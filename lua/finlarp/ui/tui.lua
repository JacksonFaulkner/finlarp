-- Launcher for the ratatui binary `fl` (tui/): one binary, several
-- screens (home | chart | portfolio | canslim | dossier | earnings | search |
-- universe | diagrams | events | menu | notes), all opened through M.open_screen. All navigation lives in the
-- binary; this file only hosts it in a popup and carries colours in. Inside tmux the binary runs in a full-size
-- `tmux display-popup` (a real terminal pane, no nested libvterm redraw
-- lag); outside tmux it falls back to a floating :terminal.
--
-- Handoff protocol: the binary can't call back into nvim, so when a screen
-- wants nvim to do something (open a document, a search chunk, another
-- screen, a picker) it writes one JSON line to $FINLARP_ACTION_FILE
-- and exits. `display-popup -E` blocks until the popup closes and passes the
-- binary's exit code through, so the jobstart on_exit here fires then and
-- M.dispatch runs the action.

local M = {}

local plugin_dir = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":h:h:h:h")
local crate_dir = plugin_dir .. "/tui"
local binary_path = crate_dir .. "/target/release/fl"
local root = "finlarp"

--- Rebuilds the release binary if any Rust source is newer than it, so
--- editing a screen and reopening the popup picks up the change without
--- a manual `cargo build --release` — the stale-binary trap this plugin
--- kept hitting since nvim just execs whatever's on disk. The build runs
--- async (a release build takes minutes and used to freeze nvim); `on_ready`
--- fires once the binary is current, and calls made mid-build wait for it.
local build_waiters = nil -- non-nil while a build is running
local function ensure_built(on_ready)
  if build_waiters then
    table.insert(build_waiters, on_ready)
    return
  end
  local bin_mtime = vim.fn.getftime(binary_path) -- -1 if missing
  local srcs = vim.fn.glob(crate_dir .. "/src/**/*.rs", false, true)
  table.insert(srcs, crate_dir .. "/Cargo.toml")
  table.insert(srcs, crate_dir .. "/Cargo.lock")
  local stale = bin_mtime < 0
  for _, f in ipairs(srcs) do
    if vim.fn.getftime(f) > bin_mtime then
      stale = true
      break
    end
  end
  if not stale then
    on_ready()
    return
  end
  vim.notify("finlarp: rebuilding TUI binary...", vim.log.levels.INFO)
  build_waiters = { on_ready }
  vim.system(
    { "cargo", "build", "--release", "--manifest-path", crate_dir .. "/Cargo.toml" },
    { text = true },
    vim.schedule_wrap(function(res)
      if res.code ~= 0 then
        vim.notify("finlarp: cargo build failed:\n" .. (res.stderr or ""), vim.log.levels.ERROR)
      end
      local waiters = build_waiters
      build_waiters = nil
      for _, fn in ipairs(waiters) do
        fn()
      end
    end)
  )
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

--- Calls require(mod)[fn](...) if it exists; notifies instead of erroring
--- when another part of the plugin hasn't grown that function yet.
local function call(mod, fn, ...)
  local ok, m = pcall(require, mod)
  if not ok or type(m) ~= "table" or type(m[fn]) ~= "function" then
    vim.notify(("finlarp: %s.%s not available"):format(mod, fn), vim.log.levels.WARN)
    return
  end
  local cok, err = pcall(m[fn], ...)
  if not cok then
    vim.notify(("finlarp: %s.%s failed: %s"):format(mod, fn, tostring(err)), vim.log.levels.ERROR)
  end
end

--- Screens that need more than open_screen(screen, arg). The binary builds
--- the canslim/dossier caches itself, so everything else opens directly.
local screens = {
  chart = function()
    M.show()
  end,
  portfolio = function(arg)
    M.show_suite(arg)
  end,
}

--- Runs one NvimAction table ({action = "docview"|"chunk"|"screen"|"picker", ...})
--- as written by the binary (src/app.rs NvimAction). Public so a
--- --remote-send fallback can call it too.
--- @param a table
function M.dispatch(a)
  if type(a) ~= "table" then
    return
  end
  if a.action == "docview" then
    call(root .. ".ui.docview", "open", a.url, a.quote)
  elseif a.action == "chunk" then
    call(root .. ".ui.search", "open_chunk", a.id)
  elseif a.action == "screen" then
    local open = screens[a.screen]
    if open then
      open(a.arg)
    else
      M.open_screen(a.screen, a.arg)
    end
  elseif a.action == "picker" then
    M.open_screen(a.screen) -- no argument = the screen's ticker picker
  elseif a.action == "notechat" then
    call(root .. ".ui.notes", "chat", a.id)
  elseif a.action == "noteask" then
    call(root .. ".ui.notes", "ask", a.id, a.question)
  elseif a.action == "keys" then
    -- <leader>v? menu: replay the chosen keymap so nvim's own mapping fires.
    if a.keys then
      local keys = vim.api.nvim_replace_termcodes(a.keys, true, false, true)
      vim.api.nvim_feedkeys(keys, "m", false)
    end
  elseif a.action == "claude" then
    -- <space>ac / <space>as inside the TUI: same as the nvim keys. Text is
    -- written to a file and added like any other file context.
    if a.text then
      local dir = vim.fn.stdpath("cache") .. "/finlarp/ctx"
      vim.fn.mkdir(dir, "p")
      local path = ("%s/%s.md"):format(dir, os.date("%Y%m%d-%H%M%S"))
      vim.fn.writefile(vim.split(a.text, "\n", { plain = true }), path)
      vim.cmd("ClaudeCodeAdd " .. vim.fn.fnameescape(path))
    end
    vim.cmd("ClaudeCodeFocus")
  else
    vim.notify("finlarp: unknown action " .. vim.inspect(a), vim.log.levels.WARN)
  end
end

--- Reads and deletes the action file; nil if the binary wrote none.
local function take_action(path)
  local f = io.open(path, "r")
  if not f then
    return nil
  end
  local s = f:read("*a")
  f:close()
  os.remove(path)
  if not s or s == "" then
    return nil
  end
  local ok, a = pcall(vim.json.decode, s, { luanil = { object = true, array = true } })
  if not ok then
    vim.notify("finlarp: bad action file: " .. s, vim.log.levels.ERROR)
    return nil
  end
  return a
end

--- After the binary exits: opts.on_exit(code, action) first, then the
--- default handling (dispatch the action).
local function finish(code, action_file, screen, opts)
  vim.schedule(function()
    local action = take_action(action_file)
    if opts.on_exit then
      local ok, err = pcall(opts.on_exit, code, action)
      if not ok then
        vim.notify("finlarp: on_exit failed: " .. tostring(err), vim.log.levels.ERROR)
      end
    end
    if action and action.error then
      vim.notify("finlarp: " .. screen .. ": " .. action.error, vim.log.levels.ERROR)
    elseif action then
      M.dispatch(action)
    elseif code ~= 0 then
      -- the popup closes with the process, taking any panic message with it
      vim.notify(("finlarp: %s screen exited with code %d"):format(screen, code), vim.log.levels.ERROR)
    end
  end)
end

local function open_in_float(cmd, env, title, on_exit)
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
    title = title,
    title_pos = "center",
    zindex = 100,
  })
  vim.api.nvim_create_autocmd("TermClose", {
    buffer = buf,
    once = true,
    callback = function()
      local code = vim.v.event.status
      if vim.api.nvim_win_is_valid(win) then
        vim.api.nvim_win_close(win, true)
      end
      on_exit(code)
    end,
  })
  vim.fn.jobstart(cmd, { term = true, env = env })
  vim.cmd("startinsert")
end

--- Opens a screen of the binary.
--- @param screen string "home" | "chart" | "portfolio" | "canslim" | "dossier" | "earnings" | "search" | "universe" | "diagrams" | "events" | "events"
--- @param arg string|nil screen argument (symbol, query, range)
--- @param opts table|nil { title = string, env = table<string,string>, on_exit = fun(code: integer, action: table|nil) }
function M.open_screen(screen, arg, opts)
  ensure_built(function()
    M._open_built(screen, arg, opts)
  end)
end

function M._open_built(screen, arg, opts)
  opts = opts or {}
  screen = screen or "chart"
  if vim.fn.executable(binary_path) ~= 1 then
    vim.notify("finlarp: TUI binary not built — run `cargo build --release` in " .. crate_dir, vim.log.levels.ERROR)
    return
  end

  local cmd = {
    binary_path,
    "--bg",
    hl_hex("Normal", "bg", ""),
    "--up",
    hl_hex("SecuritySpreadUp", "fg", "#4d9375"),
    "--down",
    hl_hex("SecuritySpreadDown", "fg", "#c25c5c"),
    screen,
  }
  if arg and arg ~= "" then
    cmd[#cmd + 1] = arg
  end
  local title = opts.title or (" " .. (arg and (arg .. " ") or "") .. screen .. " ")
  local action_file = vim.fn.tempname()
  local env = { FINLARP_ACTION_FILE = action_file }
  -- cursor highlight follows the colorscheme (faint, like nvim's own cursorline)
  local cursor_bg = hl_hex("CursorLine", "bg", "")
  if cursor_bg == "" then
    cursor_bg = hl_hex("Visual", "bg", "")
  end
  if cursor_bg ~= "" then
    env.FINLARP_CURSOR_BG = cursor_bg
  end
  if vim.env.FINLARP_DB then
    env.FINLARP_DB = vim.env.FINLARP_DB
  end
  for k, v in pairs(opts.env or {}) do
    env[k] = v
  end
  local function on_exit(code)
    finish(code, action_file, screen, opts)
  end

  if not vim.env.TMUX then
    open_in_float(cmd, env, title, on_exit)
    return
  end

  -- The popup's shell gets the tmux server's environment, not this job's,
  -- so the env vars go on the command line.
  local parts = { "env" }
  for k, v in pairs(env) do
    parts[#parts + 1] = vim.fn.shellescape(k .. "=" .. v)
  end
  for _, c in ipairs(cmd) do
    parts[#parts + 1] = vim.fn.shellescape(c)
  end
  -- No detach: display-popup -E blocks until the popup closes and exits
  -- with the binary's code, so on_exit fires exactly then.
  vim.fn.jobstart({
    "tmux",
    "display-popup",
    "-E",
    "-w",
    "100%",
    "-h",
    "100%",
    "-T",
    title,
    table.concat(parts, " "),
  }, {
    on_exit = function(_, code)
      on_exit(code)
    end,
  })
end

--- Portfolio history line chart (reads DuckDB portfolio_history directly).
--- @param range string|nil "1M" | "3M" | "6M" | "1Y" | "ALL"
function M.show(range)
  M.open_screen("chart", range, { title = " portfolio history " })
end

--- Portfolio suite: six tabs (overview, positions, exposure, risk, activity,
--- signals). Reads DuckDB directly, like the history chart.
--- @param range string|nil starting range for the overview: "1M" | "3M" | "6M" | "1Y" | "ALL"
function M.show_suite(range)
  -- The binary only reads DuckDB, so the background refresh (init.lua
  -- refresh_portfolio) reports through a small JSON status file it polls:
  -- {seq, state = refreshing|done|error, msg, pulled}.
  local status_file = vim.fn.tempname()
  local seq = 0
  local function report(state, msg, pulled)
    seq = seq + 1
    pcall(vim.fn.writefile, { vim.json.encode({ seq = seq, state = state, msg = msg, pulled = pulled }) }, status_file)
  end
  M.open_screen("portfolio", range, {
    title = " portfolio ",
    env = { FINLARP_STATUS_FILE = status_file },
  })
  call(root, "refresh_portfolio", report)
end

--- The `<leader>vm` notes browser. `notes` are the mind CLI's index rows.
function M.show_notes(notes)
  local file = vim.fn.tempname()
  vim.fn.writefile({ vim.json.encode(notes) }, file)
  M.open_screen("notes", nil, { title = " notes ", env = { FINLARP_NOTES_FILE = file } })
end

--- The `<leader>v?` menu: a ratatui list of keymaps. nvim owns the list.
--- @param items { lhs: string, name: string, desc: string, mode: string? }[]
function M.show_menu(items)
  local file = vim.fn.tempname()
  vim.fn.writefile({ vim.json.encode(items) }, file)
  M.open_screen("menu", nil, { title = " finlarp ", env = { FINLARP_MENU_FILE = file } })
end

--- The home menu (`fl` / `fl .`).
function M.show_home()
  M.open_screen("home", nil, { title = " finlarp " })
end

return M
