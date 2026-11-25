-- Loaded by the AI universe screen's embedded Neovim (screens/universe.rs), after the
-- user's own config, so oil and every mapping are theirs. Two hooks:
--
--   oil -> fl   the entry under oil's cursor is written to <root>/.cursor as a path
--               relative to the root (compute_semis/memory_storage/MU); fl follows it.
--   fl -> oil   fl calls FlReveal(rel, name) over --remote-send to open a directory
--               with the cursor on one entry.

local root = vim.fn.fnamemodify(vim.env.FL_UNIVERSE_ROOT or ".", ":p")
if root:sub(-1) ~= "/" then
  root = root .. "/"
end
local out = root .. ".cursor"
local last

local function report()
  if vim.bo.filetype ~= "oil" then
    return
  end
  local ok, oil = pcall(require, "oil")
  if not ok then
    return
  end
  local dir = oil.get_current_dir()
  if not dir or dir:sub(1, #root) ~= root then
    return
  end
  local rel = dir:sub(#root + 1)
  local entry = oil.get_cursor_entry()
  if entry and entry.name ~= ".." then
    rel = rel .. entry.name
  end
  rel = rel:gsub("/+$", "")
  if rel == last then
    return
  end
  last = rel
  local f = io.open(out, "w")
  if f then
    f:write(rel .. "\n")
    f:close()
  end
end

vim.api.nvim_create_autocmd({ "CursorMoved", "BufEnter" }, {
  group = vim.api.nvim_create_augroup("FlUniverse", { clear = true }),
  callback = report,
})

-- Opens <root>/rel in oil with the cursor on `name`. oil puts back its remembered cursor
-- after the open callback, so the search waits a beat or that restore would undo it.
-- Already in that directory, oil.open re-renders it and restores its cursor late, so the
-- search runs straight away instead.
function FlReveal(rel, name)
  local oil = require("oil")
  local function land()
    if name and name ~= "" then
      -- oil lines end in " <name>" (directories "<name>/"); the space keeps MU off SMU
      vim.api.nvim_win_set_cursor(0, { 1, 0 })
      vim.fn.search("\\V " .. vim.fn.escape(name, "\\") .. "/\\?\\$", "cW")
    end
    report()
  end
  local target = vim.fn.fnamemodify(root .. rel, ":p")
  if vim.bo.filetype == "oil" and oil.get_current_dir() == target then
    land()
    return
  end
  oil.open(target, nil, function()
    vim.defer_fn(land, 30)
  end)
end

vim.schedule(report)
