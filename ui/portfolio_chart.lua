local M = {}

local plugin_dir = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":h:h")
local crate_dir = plugin_dir .. "/portfolio_chart"
local binary_path = crate_dir .. "/target/release/portfolio_chart"

--- Rebuilds the release binary if any Rust source is newer than it, so
--- editing canslim.rs and reopening the popup picks up the change without
--- a manual `cargo build --release` — the stale-binary trap this plugin
--- kept hitting since nvim just execs whatever's on disk.
local function ensure_built()
  local bin_mtime = vim.fn.getftime(binary_path) -- -1 if missing
  local srcs = vim.fn.glob(crate_dir .. "/src/*.rs", false, true)
  table.insert(srcs, crate_dir .. "/Cargo.toml")
  local stale = bin_mtime < 0
  for _, f in ipairs(srcs) do
    if vim.fn.getftime(f) > bin_mtime then
      stale = true
      break
    end
  end
  if not stale then
    return
  end
  vim.notify("security_spread: rebuilding portfolio_chart binary...", vim.log.levels.INFO)
  local result = vim.fn.system({ "cargo", "build", "--release", "--manifest-path", crate_dir .. "/Cargo.toml" })
  if vim.v.shell_error ~= 0 then
    vim.notify("security_spread: cargo build failed:\n" .. result, vim.log.levels.ERROR)
  end
end

--- @return string "#rrggbb", or `fallback` (often "" for "no explicit
--- color, let the terminal's own default show through") when the
--- highlight group doesn't set that attribute — many colorschemes leave
--- Normal's bg unset on purpose to inherit terminal transparency, and
--- treating that as "missing, substitute a hardcoded hex" would paint an
--- opaque color that doesn't match the terminal everything else in nvim
--- renders against.
local function hl_hex(name, attr, fallback)
  local ok, hl = pcall(vim.api.nvim_get_hl, 0, { name = name, link = false })
  local val = ok and hl and hl[attr]
  if not val then
    return fallback
  end
  return string.format("#%06x", val)
end

--- Opens the ratatui portfolio-history binary inside a floating
--- :terminal — a real terminal-rendered TUI nested inside nvim, not an
--- image. Colors are pulled from the current colorscheme so it blends in.
function M.show()
  ensure_built()
  if vim.fn.executable(binary_path) ~= 1 then
    vim.notify(
      "security_spread: portfolio_chart binary not built — run `cargo build --release` in "
      .. plugin_dir .. "/portfolio_chart",
      vim.log.levels.ERROR
    )
    return
  end

  local bg = hl_hex("Normal", "bg", "")
  local fg_up = hl_hex("SecuritySpreadUp", "fg", "#4d9375")
  local fg_down = hl_hex("SecuritySpreadDown", "fg", "#c25c5c")

  local width = math.min(100, vim.o.columns - 6)
  local height = math.min(30, vim.o.lines - 6)

  local buf = vim.api.nvim_create_buf(false, true)
  vim.bo[buf].bufhidden = "wipe"

  local win = vim.api.nvim_open_win(buf, true, {
    relative = "editor",
    row = math.floor((vim.o.lines - height) / 2),
    col = math.floor((vim.o.columns - width) / 2),
    width = width,
    height = height,
    style = "minimal",
    border = "rounded",
    title = " portfolio history ",
    title_pos = "center",
    zindex = 100,
  })

  vim.api.nvim_create_autocmd("TermClose", {
    buffer = buf,
    once = true,
    callback = function()
      if vim.api.nvim_win_is_valid(win) then
        vim.api.nvim_win_close(win, true)
      end
    end,
  })

  vim.fn.termopen({ binary_path, bg, fg_up, fg_down })
  vim.cmd("startinsert")
end

--- Fallback for when nvim isn't running inside tmux: same floating
--- :terminal approach as M.show(), nested-emulator latency and all.
local function show_canslim_in_nvim_terminal(symbol, bg, fg_up, fg_down)
  -- Full editor width/height (minus the border): the scorecard lays out
  -- four+ side-by-side cards per row and the legends clip at 85%.
  local width = vim.o.columns - 2
  local height = vim.o.lines - vim.o.cmdheight - 3

  local buf = vim.api.nvim_create_buf(false, true)
  vim.bo[buf].bufhidden = "wipe"

  local win = vim.api.nvim_open_win(buf, true, {
    relative = "editor",
    row = math.floor((vim.o.lines - height) / 2),
    col = math.floor((vim.o.columns - width) / 2),
    width = width,
    height = height,
    style = "minimal",
    border = "rounded",
    title = " " .. symbol .. " canslim ",
    title_pos = "center",
    zindex = 100,
  })

  vim.api.nvim_create_autocmd("TermClose", {
    buffer = buf,
    once = true,
    callback = function()
      if vim.api.nvim_win_is_valid(win) then
        vim.api.nvim_win_close(win, true)
      end
    end,
  })

  vim.fn.termopen({ binary_path, bg, fg_up, fg_down, "canslim", symbol })
  vim.cmd("startinsert")
end

--- Opens the CANSLIM scorecard screen for one symbol. Assumes
--- `uv run services/canslim.py <symbol>` has already been run at least
--- once (cached in canslim_cache) — this just renders whatever's there.
---
--- Prefers a real `tmux display-popup` over nvim's own floating
--- :terminal: nvim's built-in terminal is a fairly naive VT100 emulator
--- (libvterm-based) and redrawing a full-screen ratatui frame — 7 gauge
--- widgets plus borders — on every keypress inside that nested emulator
--- was visibly laggy. A tmux popup is a real terminal pane (same
--- mechanism as the existing <leader>fw sessionx popup), so the rust
--- binary renders directly to it with no nvim redraw path in between.
function M.show_canslim(symbol)
  ensure_built()
  if vim.fn.executable(binary_path) ~= 1 then
    vim.notify(
      "security_spread: portfolio_chart binary not built — run `cargo build --release` in "
      .. plugin_dir .. "/portfolio_chart",
      vim.log.levels.ERROR
    )
    return
  end

  local bg = hl_hex("Normal", "bg", "")
  local fg_up = hl_hex("SecuritySpreadUp", "fg", "#4d9375")
  local fg_down = hl_hex("SecuritySpreadDown", "fg", "#c25c5c")

  if not vim.env.TMUX then
    show_canslim_in_nvim_terminal(symbol, bg, fg_up, fg_down)
    return
  end

  local run_binary = table.concat(
    vim.tbl_map(vim.fn.shellescape, { binary_path, bg, fg_up, fg_down, "canslim", symbol }),
    " "
  )

  -- The binary runs in its own tmux pane, outside nvim's process — it
  -- can't call back into the picker directly. Pressing `s` on the main
  -- scorecard screen exits it with code 90 as a signal; this wrapper
  -- watches for that and re-invokes the fzf-lua picker in the parent
  -- nvim over its RPC server (`--remote-send`) once the pane closes.
  local servername = vim.v.servername
  local back_to_picker = ""
  if servername and servername ~= "" then
    local remote_send = vim.fn.shellescape(
      "<Cmd>lua require('custom_plugins.security_spread').pick_canslim()<CR>"
    )
    back_to_picker = string.format(
      "; if [ \"$?\" = \"90\" ]; then %s --server %s --remote-send %s; fi",
      vim.fn.shellescape(vim.v.progpath), vim.fn.shellescape(servername), remote_send
    )
  end

  vim.fn.jobstart({
    "tmux", "display-popup", "-E",
    "-w", "100%", "-h", "100%",
    "-T", " " .. symbol .. " canslim ",
    run_binary .. back_to_picker,
  }, { detach = true })
end

return M
