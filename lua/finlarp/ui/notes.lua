-- <leader>vm: ratatui browser (tui/src/screens/notes.rs) over every note you've
-- asked (mind.duckdb). Lua only fetches the notes and runs what the screen
-- hands back:
--   <CR>    reopen the Claude Code chat that answered the note (--resume)
--   ctrl-f  follow-up chip -> new note anchored like the parent
--   ctrl-o  dossier for the note's ticker      ctrl-g  godel

local M = {}

local by_id = {} -- notes from the last open(), for the actions the screen hands back

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

--- Reopen the Claude chat that answered note `id`.
function M.chat(id)
  local n = by_id[id]
  if n then
    open_chat(n)
  end
end

--- Save follow-up `question` as a new note anchored like note `id`.
function M.ask(id, question)
  local n = by_id[id]
  if n then
    local anchor = n.anchor or (n.entities and n.entities[1])
    require("finlarp.ui.note").submit(question, n.context or "", anchor)
  end
end

function M.open()
  require("finlarp.ui.note").mind({ "index" }, function(ok, notes)
    if not ok then
      vim.notify("finlarp: " .. tostring(notes), vim.log.levels.ERROR)
      return
    end
    if #notes == 0 then
      vim.notify("finlarp: no notes yet (<leader>vn)", vim.log.levels.INFO)
      return
    end
    by_id = {}
    for _, n in ipairs(notes) do
      by_id[n.id] = n
    end
    require("finlarp.ui.tui").show_notes(notes)
  end)
end

return M
