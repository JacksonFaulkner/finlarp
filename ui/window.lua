local treemap = require("custom_plugins.security_spread.ui.treemap")
local colors = require("custom_plugins.security_spread.ui.colors")

local M = {}

local ns = vim.api.nvim_create_namespace("security_spread")

-- Overlay charts only stay legible up to about 4 lines at once — cap
-- selection there instead of letting it grow unbounded.
local MAX_SELECTED = 4

-- Multiple named dashboards can be open at once (e.g. one docked left, one
-- docked right). Each session owns its own tile windows/region and is
-- redrawn independently.
-- sessions[name] = { wins = {}, tiles = {}, quotes = {}, region = {}, opts = {} }
local sessions = {}
local resize_augroup = nil

local HELP_LINES = {
  " security_spread — $ dashboard ",
  "",
  " hjkl        move between tiles",
  " <Space>     select tile (up to 4, colored)",
  " r           refresh now (live E*TRADE pull)",
  " R           toggle auto-refresh (every 2s)",
  " c           CANSLIM scorecard for focused tile",
  " f           search filings for focused tile",
  " p           research dossier for focused tile",
  " <leader>sf  search filings (all)",
  " <leader>sg  chart selected/focused symbol",
  " <leader>sh  daily % change history",
  " <leader>st  search transaction history",
  " <leader>sw  AI universe: pick bucket/sub/region",
  " <leader>so  switch open dashboards",
  " q / <Esc>   close this dashboard",
  " ?           toggle this help",
}

local function close_help_win()
  local win = vim.g._security_spread_help_win
  if win and vim.api.nvim_win_is_valid(win) then
    vim.api.nvim_win_close(win, true)
  end
  vim.g._security_spread_help_win = nil
end

--- Small floating help overlay listing the `$` dashboard's keybinds.
--- Any key (or calling again) closes it — it's read-only, not modal.
local function toggle_help()
  local existing = vim.g._security_spread_help_win
  if existing and vim.api.nvim_win_is_valid(existing) then
    close_help_win()
    return
  end

  local width = 0
  for _, line in ipairs(HELP_LINES) do
    width = math.max(width, #line)
  end
  width = width + 2

  local buf = vim.api.nvim_create_buf(false, true)
  vim.bo[buf].bufhidden = "wipe"
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, HELP_LINES)
  vim.bo[buf].modifiable = false

  local win = vim.api.nvim_open_win(buf, false, {
    relative = "editor",
    row = math.floor((vim.o.lines - #HELP_LINES - 2) / 2),
    col = math.floor((vim.o.columns - width) / 2),
    width = width,
    height = #HELP_LINES,
    style = "minimal",
    border = "rounded",
    zindex = 200, -- above tile floats
    focusable = false,
  })
  vim.wo[win].winhighlight = "NormalFloat:SecuritySpreadSymbol"
  vim.g._security_spread_help_win = win

  vim.api.nvim_create_autocmd("WinClosed", {
    once = true,
    callback = function()
      if vim.g._security_spread_help_win == win then
        vim.g._security_spread_help_win = nil
      end
    end,
  })
end

--- Find the session that owns `win`, if any.
local function session_for_win(win)
  for name, s in pairs(sessions) do
    for _, w in ipairs(s.wins) do
      if w == win then
        return name, s
      end
    end
  end
  return nil, nil
end

--- Directional nav between tile floats, scoped to the current session only
--- (so left/right docked dashboards don't bleed into each other). Native
--- <C-w>hjkl walks the split tree and lands on whatever real window sits
--- behind the floats, so we pick the nearest tile by screen position
--- instead.
--- @param dir "h"|"j"|"k"|"l"
local function navigate(dir)
  local cur = vim.api.nvim_get_current_win()
  local _, s = session_for_win(cur)
  if not s then
    return
  end

  local from
  for _, t in ipairs(s.tiles) do
    if t.win == cur then
      from = t
      break
    end
  end
  if not from then
    return
  end

  local best, best_score
  for _, t in ipairs(s.tiles) do
    if t.win ~= cur and vim.api.nvim_win_is_valid(t.win) then
      local dx, dy = t.cx - from.cx, t.cy - from.cy
      local along, ortho
      local matches
      if dir == "h" then
        matches, along, ortho = dx < 0, -dx, dy
      elseif dir == "l" then
        matches, along, ortho = dx > 0, dx, dy
      elseif dir == "k" then
        matches, along, ortho = dy < 0, -dy, dx
      elseif dir == "j" then
        matches, along, ortho = dy > 0, dy, dx
      end
      if matches then
        local score = along + math.abs(ortho) * 3
        if not best_score or score < best_score then
          best, best_score = t, score
        end
      end
    end
  end

  if best then
    s.focus_symbol = best.symbol
    vim.api.nvim_set_current_win(best.win)
  end
end

--- Best ticker to act on when a dashboard key is pressed outside a tile.
local function focused_symbol(name)
  local s = sessions[name]
  if not s then
    return nil
  end
  local cur = vim.api.nvim_get_current_win()
  for _, t in ipairs(s.tiles) do
    if t.win == cur then
      s.focus_symbol = t.symbol
      return t.symbol
    end
  end
  if s.focus_symbol then
    return s.focus_symbol
  end
  if s.selected and s.selected[1] then
    return s.selected[1].symbol
  end
  return s.tiles[1] and s.tiles[1].symbol or nil
end

local function open_focused_dossier(name)
  local symbol = focused_symbol(name)
  if symbol then
    require("custom_plugins.security_spread").show_dossier(symbol)
  end
end

local function ensure_highlights()
  vim.api.nvim_set_hl(0, "SecuritySpreadUp", { fg = "#4d9375", bold = false, default = true })
  vim.api.nvim_set_hl(0, "SecuritySpreadDown", { fg = "#c25c5c", bold = false, default = true })
  vim.api.nvim_set_hl(0, "SecuritySpreadSymbol", { fg = "#e6e6e6", bold = true, default = true })
  colors.ensure_highlights()
end

--- Toggles tile-selection under `win`, within its session's ordered list
--- (up to MAX_SELECTED). Each slot gets a stable color from `colors.SERIES`
--- so a tile's border color matches its line color in the overlay chart.
--- <leader>sg reads `s.selected` to know which symbols to chart together.
--- @param win integer
local function toggle_select(win)
  local _, s = session_for_win(win)
  if not s then
    return
  end
  s.selected = s.selected or {}

  for i, sel in ipairs(s.selected) do
    if sel.win == win then
      vim.wo[win].winhighlight = "FloatBorder:FloatBorder"
      table.remove(s.selected, i)
      -- Re-color the remaining selections down to fill the freed slot so
      -- colors always match selection order 1..N.
      for j, remaining in ipairs(s.selected) do
        if vim.api.nvim_win_is_valid(remaining.win) then
          vim.wo[remaining.win].winhighlight = "FloatBorder:" .. colors.SERIES[j].hl
        end
      end
      return
    end
  end

  if #s.selected >= MAX_SELECTED then
    vim.notify("security_spread: max " .. MAX_SELECTED .. " symbols selected", vim.log.levels.WARN)
    return
  end

  local symbol
  for _, t in ipairs(s.tiles) do
    if t.win == win then
      symbol = t.symbol
      break
    end
  end

  s.selected[#s.selected + 1] = { win = win, symbol = symbol }
  vim.wo[win].winhighlight = "FloatBorder:" .. colors.SERIES[#s.selected].hl
end

--- @param text string
--- @param width integer
local function center(text, width)
  text = text or ""
  if #text >= width then
    return text:sub(1, width)
  end
  local total_pad = width - #text
  local left = math.floor(total_pad / 2)
  return string.rep(" ", left) .. text .. string.rep(" ", total_pad - left)
end

--- @param q table merged position+quote entry
--- @return table[] { text, hl }
local function tile_text_lines(q)
  local sign = (q.change_close or 0) >= 0
  local hl = sign and "SecuritySpreadUp" or "SecuritySpreadDown"
  local sign_str = sign and "+" or ""

  local price = q.last_price and string.format("$%.2f", q.last_price) or "n/a"
  local pct = q.change_close_pct and string.format("%s%.2f%%", sign_str, q.change_close_pct) or ""
  local abs = q.change_close and string.format("%s%.2f", sign_str, q.change_close) or ""

  return {
    { text = q.symbol, hl = "SecuritySpreadSymbol" },
    { text = price, hl = hl },
    { text = pct, hl = hl },
    { text = abs, hl = hl },
  }
end

--- Closes just one session's tile windows (used before a redraw too).
--- @param name string
local function close_session(name)
  local s = sessions[name]
  if not s then
    return
  end
  for _, win in ipairs(s.wins) do
    if vim.api.nvim_win_is_valid(win) then
      pcall(vim.api.nvim_win_close, win, true)
    end
  end
  s.wins = {}
  s.tiles = {}
  -- Clear win refs but keep the symbols so a redraw can re-find each tile
  -- by symbol and re-apply its slot color.
  if s.selected then
    for _, sel in ipairs(s.selected) do
      sel.win = nil
    end
  end
end

local function close_all_sessions()
  for name in pairs(sessions) do
    close_session(name)
  end
  sessions = {}
  close_help_win()
  if resize_augroup then
    pcall(vim.api.nvim_del_augroup_by_id, resize_augroup)
    resize_augroup = nil
  end
end

--- Picks which of the 4 text lines fit in `height`, centered vertically.
local function visible_lines(lines, height)
  if height >= 4 then
    return { lines[1], { text = "", hl = nil }, lines[2], lines[3] }
  elseif height >= 3 then
    return { lines[1], lines[2], lines[3] }
  elseif height >= 2 then
    return { lines[1], lines[3] }
  elseif height >= 1 then
    return { lines[1] }
  end
  return {}
end

local function open_tile(tile, region, name)
  local w, h = tile.w, tile.h
  if w < 3 or h < 3 then
    return nil -- too small to hold a bordered tile with any content
  end

  local buf = vim.api.nvim_create_buf(false, true)
  vim.bo[buf].bufhidden = "wipe"

  local content_h = h - 2
  local content_w = w - 2
  local lines = tile_text_lines(tile.item)
  local show = visible_lines(lines, content_h)

  local buf_lines = {}
  local pad_top = math.floor((content_h - #show) / 2)
  for _ = 1, pad_top do
    buf_lines[#buf_lines + 1] = string.rep(" ", content_w)
  end
  for _, entry in ipairs(show) do
    buf_lines[#buf_lines + 1] = center(entry.text, content_w)
  end
  while #buf_lines < content_h do
    buf_lines[#buf_lines + 1] = string.rep(" ", content_w)
  end

  vim.api.nvim_buf_set_lines(buf, 0, -1, false, buf_lines)

  for i, entry in ipairs(show) do
    if entry.hl then
      vim.api.nvim_buf_add_highlight(buf, ns, entry.hl, pad_top + i - 1, 0, -1)
    end
  end

  vim.bo[buf].modifiable = false

  local win_opts
  if region.win then
    -- Floats anchored to a real host window (a normal split) so the
    -- dashboard behaves like a real pane: native resize, <C-w> layout,
    -- moves/resizes when the split does.
    win_opts = {
      relative = "win",
      win = region.win,
      row = tile.y,
      col = tile.x,
      width = content_w,
      height = content_h,
      style = "minimal",
      border = "single",
      focusable = true,
      zindex = 50,
    }
  else
    -- No host window: anchor to the whole editor (fullscreen dashboard).
    win_opts = {
      relative = "editor",
      row = region.row + tile.y,
      col = region.col + tile.x,
      width = content_w,
      height = content_h,
      style = "minimal",
      border = "single",
      focusable = true,
      zindex = 50,
    }
  end

  local win = vim.api.nvim_open_win(buf, false, win_opts)

  vim.keymap.set("n", "q", function()
    M.close(name)
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "<Esc>", function()
    M.close(name)
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "h", function()
    navigate("h")
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "j", function()
    navigate("j")
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "k", function()
    navigate("k")
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "l", function()
    navigate("l")
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "<Space>", function()
    toggle_select(win)
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "?", toggle_help, { buffer = buf, silent = true })
  -- Lazily required (not at module load) — init.lua requires window.lua,
  -- so requiring init.lua back at the top level here would be circular.
  vim.keymap.set("n", "r", function()
    local s = sessions[name]
    if s and s.opts and s.opts.on_refresh then
      s.opts.on_refresh()
    end
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "R", function()
    require("custom_plugins.security_spread").toggle_auto_refresh(name)
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "c", function()
    require("custom_plugins.security_spread").show_canslim(tile.item.symbol)
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "f", function()
    require("custom_plugins.security_spread").pick_search("t:" .. tile.item.symbol .. " ")
  end, { buffer = buf, silent = true })
  vim.keymap.set("n", "p", function()
    local s = sessions[name]
    if s then
      s.focus_symbol = tile.item.symbol
    end
    require("custom_plugins.security_spread").show_dossier(tile.item.symbol)
  end, { buffer = buf, silent = true })

  vim.api.nvim_create_autocmd("WinEnter", {
    buffer = buf,
    callback = function()
      local s = sessions[name]
      if s then
        s.focus_symbol = tile.item.symbol
      end
    end,
  })

  return win
end

--- Rewrites an already-open tile window's content in place (new price/
--- change text, same window/position) — no close/reopen, so no flicker and
--- no focus disturbance. Mirrors open_tile's content layout exactly.
--- @param win integer
--- @param item table merged position+quote entry
local function render_tile_content(win, item)
  if not vim.api.nvim_win_is_valid(win) then
    return
  end
  local buf = vim.api.nvim_win_get_buf(win)
  local content_w = vim.api.nvim_win_get_width(win)
  local content_h = vim.api.nvim_win_get_height(win)

  local lines = tile_text_lines(item)
  local show = visible_lines(lines, content_h)

  local buf_lines = {}
  local pad_top = math.floor((content_h - #show) / 2)
  for _ = 1, pad_top do
    buf_lines[#buf_lines + 1] = string.rep(" ", content_w)
  end
  for _, entry in ipairs(show) do
    buf_lines[#buf_lines + 1] = center(entry.text, content_w)
  end
  while #buf_lines < content_h do
    buf_lines[#buf_lines + 1] = string.rep(" ", content_w)
  end

  vim.bo[buf].modifiable = true
  vim.api.nvim_buf_clear_namespace(buf, ns, 0, -1)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, buf_lines)
  for i, entry in ipairs(show) do
    if entry.hl then
      vim.api.nvim_buf_add_highlight(buf, ns, entry.hl, pad_top + i - 1, 0, -1)
    end
  end
  vim.bo[buf].modifiable = false
end

--- Data-only refresh (e.g. the background live pull in show_portfolio):
--- if the same tile windows are already up for the same set of symbols,
--- just rewrite their text/colors in place instead of the full
--- close/relayout/reopen `draw()` does — that's what caused the visible
--- flash and cursor snap-back on every background update. Only handles
--- the common case (same symbol set, no resize needed); anything else
--- (first open, symbol set changed, layout stale) returns false so the
--- caller falls back to a real M.open.
--- @param name string
--- @param quotes table[]
--- @return boolean handled
function M.update_quotes(name, quotes)
  local s = sessions[name]
  if not s or #s.tiles == 0 then
    return false
  end

  local by_symbol = {}
  for _, q in ipairs(quotes) do
    by_symbol[q.symbol] = q
  end

  for _, t in ipairs(s.tiles) do
    if not by_symbol[t.symbol] then
      return false -- symbol set shrank — needs a real relayout
    end
  end
  local seen = {}
  for _, t in ipairs(s.tiles) do
    seen[t.symbol] = true
  end
  for symbol in pairs(by_symbol) do
    if not seen[symbol] then
      return false -- symbol set grew — needs a real relayout
    end
  end

  for _, t in ipairs(s.tiles) do
    local item = by_symbol[t.symbol]
    render_tile_content(t.win, item)
  end
  s.quotes = quotes
  return true
end

local function draw(name)
  local s = sessions[name]
  if not s then
    return
  end

  -- Redraws (background data refresh, resize) used to always steal focus
  -- to the first tile, so mid-refresh the cursor visibly snapped back to
  -- the top-left square. Only remember/restore focus if the cursor was
  -- actually inside this session already — otherwise a background refresh
  -- must never touch focus at all, wherever the user currently is.
  local cur_win = vim.api.nvim_get_current_win()
  local focus_symbol = nil
  local was_focused_here = false
  for _, t in ipairs(s.tiles) do
    if t.win == cur_win then
      focus_symbol = t.symbol
      was_focused_here = true
      break
    end
  end
  focus_symbol = focus_symbol or s.focus_symbol
  local is_initial_open = #s.tiles == 0

  close_session(name)
  ensure_highlights()

  local region = s.region
  local width, height
  if region.win and vim.api.nvim_win_is_valid(region.win) then
    width = vim.api.nvim_win_get_width(region.win)
    height = vim.api.nvim_win_get_height(region.win)
  else
    width = region.width
    height = region.height
  end

  -- Raw $ value (market cap or position value) is wildly skewed — a few
  -- names would eat the whole screen and bury everything else. Compress
  -- with sqrt so relative rank still shows but small names stay readable.
  local tiles = treemap.layout_items(s.quotes, function(q)
    return math.sqrt(math.max(q.value or 1, 1))
  end, 0, 0, width, height)

  for _, tile in ipairs(tiles) do
    local win = open_tile(tile, region, name)
    if win then
      s.wins[#s.wins + 1] = win
      s.tiles[#s.tiles + 1] = {
        win = win,
        cx = tile.x + tile.w / 2,
        cy = tile.y + tile.h / 2,
        symbol = tile.item.symbol,
      }
    end
  end

  -- Re-apply each selection's color after a redraw (tile windows are
  -- fresh, so find whichever one still matches each selected symbol).
  if s.selected then
    for i, sel in ipairs(s.selected) do
      for _, t in ipairs(s.tiles) do
        if t.symbol == sel.symbol then
          vim.wo[t.win].winhighlight = "FloatBorder:" .. colors.SERIES[i].hl
          sel.win = t.win
          break
        end
      end
    end
  end

  if was_focused_here then
    -- Prefer landing back on the same symbol's tile (layout/sort order can
    -- shift between redraws); fall back to the first tile if that symbol
    -- dropped out.
    local target = s.wins[1]
    for _, t in ipairs(s.tiles) do
      if t.symbol == focus_symbol then
        target = t.win
        break
      end
    end
    if target and vim.api.nvim_win_is_valid(target) then
      vim.api.nvim_set_current_win(target)
      for _, t in ipairs(s.tiles) do
        if t.win == target then
          s.focus_symbol = t.symbol
          break
        end
      end
    end
  elseif is_initial_open or not vim.api.nvim_win_is_valid(cur_win) then
    -- Either the very first draw (floats just opened on top of whatever
    -- real window was active — without this, focus/keys stay on that
    -- underlying buffer and the dashboard is mouse-only until you click
    -- into a tile) or the window the cursor was in got closed by this
    -- redraw. Either way something needs focus, so fall back to the first
    -- tile.
    if s.wins[1] and vim.api.nvim_win_is_valid(s.wins[1]) then
      vim.api.nvim_set_current_win(s.wins[1])
      for _, t in ipairs(s.tiles) do
        if t.win == s.wins[1] then
          s.focus_symbol = t.symbol
          break
        end
      end
    end
  end
end

--- @param name string unique key for this dashboard (e.g. watchlist name) —
---   opening the same name again replaces that session in place, leaving
---   other open sessions untouched.
--- @param quotes table[] each with symbol, last_price, change_close,
---   change_close_pct, and `value` (used for tile sizing)
--- @param opts table|nil { win } to host the tiles inside a real split
---   window (native resize/<C-w> layout, closes with the split) — pass the
---   host window id from a real `vsplit`/`split`. Omit for a fullscreen
---   dashboard covering the whole editor.
function M.open(name, quotes, opts)
  opts = opts or {}
  local region = {
    win = opts.win,
    row = 0,
    col = 0,
    width = vim.o.columns,
    height = vim.o.lines - 2,
  }

  -- Reusing the existing session table (rather than replacing it outright)
  -- is what lets draw() see the pre-redraw tiles/selection/background_buf
  -- and carry focus and selection across a same-name reopen — e.g. the
  -- background live-data refresh in show_portfolio calling this again
  -- with fresher quotes.
  local existing = sessions[name]
  sessions[name] = {
    wins = existing and existing.wins or {},
    tiles = existing and existing.tiles or {},
    selected = existing and existing.selected or nil,
    background_buf = existing and existing.background_buf or nil,
    quotes = quotes,
    region = region,
    opts = opts,
  }
  -- Captured before draw(), which focuses the first tile: after it the
  -- current buffer is a tile's scratch buffer, not what shows in the gaps.
  local prev_buf = vim.api.nvim_get_current_buf()
  draw(name)

  -- Tile floats have q/<Esc> bound, but whatever's showing in the gaps
  -- between tiles didn't — the host split's own buffer for a docked
  -- dashboard, or the buffer that was current when a fullscreen one opened.
  -- Clicking there and hitting q did nothing. q should always close the
  -- dashboard, no matter where focus lands.
  -- Keep the original background_buf on a reopen (e.g. a background data
  -- refresh) instead of recomputing from whatever buffer happens to be
  -- current at that moment — for a fullscreen dashboard that could be a
  -- tile's own scratch buffer if the user is focused inside it.
  local background_buf = existing
      and existing.background_buf
      and vim.api.nvim_buf_is_valid(existing.background_buf)
      and existing.background_buf
    or (opts.win and vim.api.nvim_win_is_valid(opts.win) and vim.api.nvim_win_get_buf(opts.win))
    or prev_buf
  sessions[name].background_buf = background_buf
  vim.keymap.set("n", "q", function()
    M.close(name)
  end, { buffer = background_buf, silent = true })
  vim.keymap.set("n", "<Esc>", function()
    M.close(name)
  end, { buffer = background_buf, silent = true })
  vim.keymap.set("n", "?", toggle_help, { buffer = background_buf, silent = true })
  vim.keymap.set("n", "r", function()
    local s = sessions[name]
    if s and s.opts and s.opts.on_refresh then
      s.opts.on_refresh()
    end
  end, { buffer = background_buf, silent = true })
  vim.keymap.set("n", "R", function()
    require("custom_plugins.security_spread").toggle_auto_refresh(name)
  end, { buffer = background_buf, silent = true })
  vim.keymap.set("n", "p", function()
    open_focused_dossier(name)
  end, { buffer = background_buf, silent = true })

  if not resize_augroup then
    resize_augroup = vim.api.nvim_create_augroup("SecuritySpreadResize", { clear = true })

    vim.api.nvim_create_autocmd("VimResized", {
      group = resize_augroup,
      callback = function()
        for n, s in pairs(sessions) do
          -- Host-window sessions redraw off the window's own size; only
          -- fullscreen (no host) sessions need to follow the editor here.
          if not s.region.win then
            s.region.width = vim.o.columns
            s.region.height = vim.o.lines - 2
            draw(n)
          end
        end
      end,
    })

    vim.api.nvim_create_autocmd("WinResized", {
      group = resize_augroup,
      callback = function()
        local resized = vim.v.event.windows or {}
        for n, s in pairs(sessions) do
          if s.region.win then
            for _, w in ipairs(resized) do
              if w == s.region.win then
                draw(n)
                break
              end
            end
          end
        end
      end,
    })

    vim.api.nvim_create_autocmd("WinClosed", {
      group = resize_augroup,
      callback = function(args)
        local closed = tonumber(args.match)
        for n, s in pairs(sessions) do
          if s.region.win == closed then
            M.close(n)
          end
        end
      end,
    })
  end
end

--- Closes one named session, or every open session if `name` is omitted.
--- @param name string|nil
function M.close(name)
  if name == nil then
    close_all_sessions()
    return
  end
  local s = sessions[name]
  close_session(name)
  -- Undo the background-buffer q/<Esc> hijack from M.open — for a
  -- fullscreen dashboard that buffer is the user's real, pre-existing
  -- buffer, so leaving the mapping in place would hijack q there forever.
  if s and s.background_buf and vim.api.nvim_buf_is_valid(s.background_buf) then
    pcall(vim.keymap.del, "n", "q", { buffer = s.background_buf })
    pcall(vim.keymap.del, "n", "<Esc>", { buffer = s.background_buf })
    pcall(vim.keymap.del, "n", "?", { buffer = s.background_buf })
    pcall(vim.keymap.del, "n", "r", { buffer = s.background_buf })
    pcall(vim.keymap.del, "n", "R", { buffer = s.background_buf })
    pcall(vim.keymap.del, "n", "p", { buffer = s.background_buf })
  end
  sessions[name] = nil
  close_help_win()
  -- A docked dashboard's host split (picker.host_win_for_slot) exists only
  -- for it; close it too. After sessions[name] = nil so the WinClosed
  -- autocmd this fires doesn't re-enter M.close. pcall: it may be the last window.
  if s and s.region.win and vim.api.nvim_win_is_valid(s.region.win) then
    pcall(vim.api.nvim_win_close, s.region.win, true)
  end
end

--- @return string[] names of currently open sessions
--- Read-only lookup of a session by name — lets init.lua's auto-refresh
--- timer check the dashboard is still open and reach its opts.on_refresh
--- without window.lua needing to know anything about refresh/timers itself.
--- @param name string
--- @return table|nil
function M.get_session(name)
  return sessions[name]
end

function M.list_open()
  local names = {}
  for name in pairs(sessions) do
    names[#names + 1] = name
  end
  table.sort(names)
  return names
end

--- Focuses the first tile window of an already-open session by name.
--- @param name string
function M.focus(name)
  local s = sessions[name]
  if s and s.wins[1] and vim.api.nvim_win_is_valid(s.wins[1]) then
    vim.api.nvim_set_current_win(s.wins[1])
  end
end

--- Symbols to chart for the dashboard containing the current window: every
--- <Space>-selected symbol (in selection order, so color slots line up with
--- the overlay chart), or just whichever tile is currently focused if
--- nothing's selected.
--- @return string[]
function M.selected_symbols()
  local cur = vim.api.nvim_get_current_win()
  local _, s = session_for_win(cur)
  if not s then
    return {}
  end
  if s.selected and #s.selected > 0 then
    local out = {}
    for _, sel in ipairs(s.selected) do
      out[#out + 1] = sel.symbol
    end
    return out
  end
  for _, t in ipairs(s.tiles) do
    if t.win == cur then
      return { t.symbol }
    end
  end
  return {}
end

return M
