-- <leader>vm: fzf viewer over every note you've asked (mind.duckdb), like
-- claude_history's <leader>fa but only your finlarp questions. Rows are grouped
-- by ticker (newest first within a group) and show status, age, depth and
-- title; the preview is a card with the structured answer.
--   <CR>    reopen the Claude Code chat that answered the note (--resume)
--   ctrl-f  follow-up chips: pick one of the answer's follow_ups -> new note
--   ctrl-t  filter by theme      ctrl-e  filter by linked entity
--   ctrl-o  open dossier for the note's ticker      ctrl-x  clear filter

local M = {}

local function oneline(s)
  return ((s or ""):gsub("[\t\r\n]+", " "))
end

local function rule(lines, title)
  table.insert(lines, "")
  table.insert(lines, ("── %s %s"):format(title, ("─"):rep(math.max(0, 60 - #title))))
end

local function list_section(lines, title, items, numbered)
  if items and #items > 0 then
    rule(lines, title)
    for i, item in ipairs(items) do
      table.insert(lines, (numbered and ("%d. "):format(i) or "• ") .. item)
    end
  end
end

local DEPTH = { definitional = "●○○", causal = "●●○", counterfactual = "●●●" }
local GLYPH = { answered = "✓", pending = "…", failed = "✗" }

--- Ticker a note belongs to: its anchor if that is a ticker, else the first linked ticker.
local function primary_ticker(n)
  for _, e in ipairs({ n.anchor, unpack(n.entities) }) do
    if e and e:match("^ticker:") then
      return e:sub(8)
    end
  end
end

local function preview_text(n)
  local a = n.structured
  local lines = { "YOUR NOTE  (" .. n.kind .. ")", "" }
  vim.list_extend(lines, vim.split(n.body, "\n"))
  if n.context and n.context ~= "" then
    table.insert(lines, "")
    table.insert(lines, "on: " .. oneline(n.context))
  end
  local meta = { n.ts:sub(1, 16), n.status }
  if a and a.depth then
    table.insert(meta, "depth " .. (DEPTH[a.depth] or "") .. " " .. a.depth)
  end
  if #n.entities > 0 then
    table.insert(meta, table.concat(n.entities, " "))
  end
  table.insert(lines, "")
  table.insert(lines, table.concat(meta, "  ·  "))
  if a then
    if #(a.themes or {}) > 0 then
      table.insert(lines, "themes: " .. table.concat(a.themes, ", "))
    end
    rule(lines, "ANSWER  " .. (a.title or ""))
    table.insert(lines, a.summary or "")
    list_section(lines, "EVIDENCE", a.key_points)
    if a.assumption and a.assumption ~= "" then
      rule(lines, "YOUR ASSUMPTION")
      table.insert(lines, a.assumption)
    end
    list_section(lines, "ASK NEXT  (ctrl-f)", a.follow_ups, true)
    list_section(lines, "LEARN", a.learn)
  elseif n.error then
    rule(lines, "FAILED")
    table.insert(lines, n.error)
  else
    rule(lines, "ANSWER")
    table.insert(lines, "(waiting for answer)")
  end
  return table.concat(lines, "\n")
end

-- Closing the live Claude terminal exits its job non-zero, which claudecode.nvim
-- logs as an ERROR; mute just that logger while we swap sessions on purpose.
local function close_claude_quietly()
  local ok, logger = pcall(require, "claudecode.logger")
  if not ok then
    pcall(vim.cmd, "ClaudeCodeClose")
    return
  end
  local original_error = logger.error
  logger.error = function() end
  pcall(vim.cmd, "ClaudeCodeClose")
  vim.defer_fn(function()
    logger.error = original_error
  end, 500)
end

local function open_chat(n)
  if not n.session_id then
    vim.notify("finlarp: note has no chat yet", vim.log.levels.WARN)
    return
  end
  -- claude --resume only finds sessions started from the same cwd
  if n.cwd then
    vim.cmd("tcd " .. vim.fn.fnameescape(n.cwd))
  end
  close_claude_quietly()
  -- let the old terminal job finish dying before the new one starts
  vim.defer_fn(function()
    local ok, err = pcall(vim.cmd, "ClaudeCode --resume " .. n.session_id)
    if not ok then
      vim.notify("finlarp: could not resume chat: " .. tostring(err), vim.log.levels.ERROR)
    end
  end, 150)
end

local function fzf_id(sel)
  return sel and sel[1] and vim.split(sel[1], "\t", { plain = true })[1]
end

local function pick_from(items, prompt, cb)
  if #items == 0 then
    vim.notify("finlarp: nothing to pick", vim.log.levels.INFO)
    return
  end
  vim.ui.select(items, { prompt = prompt }, function(choice)
    if choice then
      cb(choice)
    end
  end)
end

--- @param filter {theme:string|nil, entity:string|nil}|nil
function M.open(filter)
  filter = filter or {}
  require("finlarp.ui.note").mind({ "index" }, function(ok, notes)
    if not ok then
      vim.notify("finlarp: " .. tostring(notes), vim.log.levels.ERROR)
      return
    end
    if #notes == 0 then
      vim.notify("finlarp: no notes yet (<leader>vn)", vim.log.levels.INFO)
      return
    end
    local all = notes
    notes = vim.tbl_filter(function(n)
      return (not filter.theme or vim.tbl_contains(n.themes, filter.theme))
        and (not filter.entity or vim.tbl_contains(n.entities, filter.entity))
    end, all)

    -- group by ticker (A-Z, untagged last); `notes` is already newest-first
    for i, n in ipairs(notes) do
      n._i, n._tk = i, primary_ticker(n)
    end
    table.sort(notes, function(x, y)
      if x._tk ~= y._tk then
        return (x._tk or "~") < (y._tk or "~")
      end
      return x._i < y._i
    end)

    local by_id, rows = {}, {}
    for _, n in ipairs(notes) do
      by_id[n.id] = n
      local a = n.structured
      local title = a and a.title or oneline(n.body)
      -- one row per note; id is hidden (with-nth 2)
      table.insert(
        rows,
        ("%s\t%s %s  %-6s %-70s %s  %s"):format(
          n.id,
          GLYPH[n.status] or "?",
          n.ts:sub(6, 10),
          n._tk or "",
          title:sub(1, 70),
          a and DEPTH[a.depth] or "   ",
          #n.themes > 0 and table.concat(n.themes, " · ") or ""
        )
      )
    end

    local active = {}
    if filter.theme then
      table.insert(active, "theme=" .. filter.theme)
    end
    if filter.entity then
      table.insert(active, filter.entity)
    end
    local header = "<Tab> into card  <CR> chat  ^f follow-up  ^t theme  ^e entity  ^o dossier  ^x clear"
    if #active > 0 then
      header = header .. "   ⟨" .. table.concat(active, " ") .. "⟩"
    end

    local function note_of(sel)
      return by_id[fzf_id(sel)]
    end

    local fzf = require("fzf-lua")
    local current -- note shown in the preview, for <CR> from inside it
    fzf.fzf_exec(rows, {
      prompt = "Notes❯ ",
      fzf_opts = { ["--delimiter"] = "\t", ["--with-nth"] = "2", ["--nth"] = "1..", ["--header"] = header },
      winopts = {
        fullscreen = true,
        preview = { wrap = true, layout = "vertical", vertical = "down:72%", title = false },
      },
      -- <Tab> moves the cursor into the card (a real buffer: motions, visual mode, yank)
      keymap = { builtin = { ["<Tab>"] = "focus-preview" } },
      previewer = {
        _ctor = function()
          local P = require("fzf-lua.previewer.builtin").base:extend()
          function P:new(o, opts, fzf_win)
            P.super.new(self, o, opts, fzf_win)
            return self
          end
          function P:populate_preview_buf(entry_str)
            local n = by_id[vim.split(entry_str, "\t", { plain = true })[1]]
            current = n
            local buf = self:get_tmp_buffer()
            vim.api.nvim_buf_set_lines(buf, 0, -1, false, vim.split(n and preview_text(n) or "", "\n"))
            vim.bo[buf].filetype = "text"
            local win = self.win
            local function back()
              if win.fzf_winid and vim.api.nvim_win_is_valid(win.fzf_winid) then
                vim.api.nvim_set_current_win(win.fzf_winid)
                vim.cmd("startinsert")
              end
            end
            local map = function(lhs, fn)
              vim.keymap.set("n", lhs, fn, { buffer = buf, nowait = true, silent = true })
            end
            map("<Tab>", back)
            map("q", back)
            map("<Esc>", back)
            map("<CR>", function()
              if current then
                win:close()
                open_chat(current)
              end
            end)
            self:set_preview_buf(buf)
          end
          return P
        end,
      },
      actions = {
        ["default"] = function(sel)
          local n = note_of(sel)
          if n then
            open_chat(n)
          end
        end,
        -- follow-up chips: each follow_up becomes a new note anchored like its parent
        ["ctrl-f"] = function(sel)
          local n = note_of(sel)
          local ups = n and n.structured and n.structured.follow_ups or {}
          pick_from(ups, "ask next: ", function(q)
            local anchor = n.anchor or n.entities[1]
            require("finlarp.ui.note").submit(q, n.context or "", anchor)
          end)
        end,
        ["ctrl-t"] = function()
          local seen, themes = {}, {}
          for _, n in ipairs(all) do
            for _, t in ipairs(n.themes) do
              if not seen[t] then
                seen[t] = true
                table.insert(themes, t)
              end
            end
          end
          table.sort(themes)
          pick_from(themes, "theme: ", function(t)
            M.open({ theme = t, entity = filter.entity })
          end)
        end,
        ["ctrl-e"] = function()
          local seen, ents = {}, {}
          for _, n in ipairs(all) do
            for _, e in ipairs(n.entities) do
              if not seen[e] then
                seen[e] = true
                table.insert(ents, e)
              end
            end
          end
          table.sort(ents)
          pick_from(ents, "entity: ", function(e)
            M.open({ entity = e, theme = filter.theme })
          end)
        end,
        ["ctrl-o"] = function(sel)
          local n = note_of(sel)
          local tk = n and primary_ticker(n)
          if tk then
            require("finlarp").show_dossier(tk)
          else
            vim.notify("finlarp: note has no ticker", vim.log.levels.WARN)
          end
        end,
        ["ctrl-x"] = function()
          M.open()
        end,
      },
    })
  end)
end

return M
