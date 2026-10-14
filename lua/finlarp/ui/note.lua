-- <leader>vn note capture: a small floating box anchored to whatever is
-- under the cursor (word or visual selection). <CR> saves the note to
-- mind.duckdb, then a background job asks headless Claude (finlarp MCP
-- tools) and notifies when the answer is stored. Answers are read back
-- with :FinlarpNotes.

local M = {}

local finlarp_root = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":h:h:h:h")
local env_file = finlarp_root .. "/.env"

function M.mind(args, cb)
  local cmd = { "uv", "run", "--env-file", env_file, "py/mind/cli.py" }
  vim.list_extend(cmd, args)
  vim.system(cmd, { cwd = finlarp_root, text = true }, function(res)
    vim.schedule(function()
      if res.code ~= 0 then
        cb(false, res.stderr ~= "" and res.stderr or "mind cli exited " .. res.code)
        return
      end
      local ok, data = pcall(vim.json.decode, res.stdout, { luanil = { object = true, array = true } })
      cb(ok, ok and data or res.stdout)
    end)
  end)
end

--- Text to anchor the note on: visual selection if there is one, else the word under the cursor.
local function grab_context(visual)
  if visual then
    local s, e = vim.fn.getpos("'<"), vim.fn.getpos("'>")
    local lines = vim.api.nvim_buf_get_text(0, s[2] - 1, s[3] - 1, e[2] - 1, e[3], {})
    return table.concat(lines, " ")
  end
  return vim.fn.expand("<cWORD>")
end

--- Save a note and ask Claude in the background. `anchor` (e.g. "ticker:MRVL") links it to an entity.
function M.submit(body, context, anchor)
  body = vim.trim(body)
  if body == "" then
    return
  end
  local screen = vim.bo.filetype ~= "" and vim.bo.filetype or vim.fn.expand("%:t")
  local args = { "add", "--body", body, "--screen", screen, "--context", context }
  if anchor then
    vim.list_extend(args, { "--anchor", anchor })
  end
  M.mind(args, function(ok, saved)
    if not ok then
      vim.notify("finlarp note: " .. tostring(saved), vim.log.levels.ERROR)
      return
    end
    vim.notify("finlarp: note saved, asking…", vim.log.levels.INFO)
    M.mind({ "answer", saved.id }, function(aok, ans)
      if not aok then
        vim.notify("finlarp: answer failed: " .. tostring(ans), vim.log.levels.ERROR)
        return
      end
      M.last = { answer = ans.answer.summary }
      local themes = table.concat(ans.answer.themes or {}, ", ")
      vim.notify(
        "finlarp: answer ready for “" .. body:sub(1, 40) .. "” [" .. themes .. "]  (<leader>vm)",
        vim.log.levels.INFO
      )
    end)
  end)
end

--- @param visual boolean|nil capture the visual selection as context
function M.open(visual)
  local context = grab_context(visual)
  local buf = vim.api.nvim_create_buf(false, true)
  local width = math.min(80, vim.o.columns - 8)
  local win = vim.api.nvim_open_win(buf, true, {
    relative = "cursor",
    row = 1,
    col = 0,
    width = width,
    height = 6,
    style = "minimal",
    border = "rounded",
    title = " note · " .. (context ~= "" and context:sub(1, 40) or "no context") .. " ",
  })
  vim.wo[win].wrap = true
  vim.bo[buf].bufhidden = "wipe"
  vim.cmd("startinsert")

  local function close()
    if vim.api.nvim_win_is_valid(win) then
      vim.api.nvim_win_close(win, true)
    end
  end
  local function send()
    local text = table.concat(vim.api.nvim_buf_get_lines(buf, 0, -1, false), "\n")
    close()
    vim.cmd("stopinsert")
    if vim.trim(text):sub(1, 1) == ">" then
      require("finlarp.ui.godel").submit(text)
    else
      M.submit(text, context)
    end
  end
  vim.keymap.set({ "n", "i" }, "<CR>", send, { buffer = buf, silent = true })
  vim.keymap.set("i", "<S-CR>", "<CR>", { buffer = buf, silent = true })
  vim.keymap.set("n", "q", close, { buffer = buf, silent = true })
  vim.keymap.set("n", "<Esc>", close, { buffer = buf, silent = true })
end

--- Show the most recent answer in a scratch split.
function M.show_last()
  if not (M.last and M.last.answer) then
    vim.notify("finlarp: no answer yet", vim.log.levels.WARN)
    return
  end
  vim.cmd("botright new")
  local buf = vim.api.nvim_get_current_buf()
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, vim.split(M.last.answer, "\n"))
  vim.bo[buf].buftype = "nofile"
  vim.bo[buf].filetype = "markdown"
  vim.keymap.set("n", "q", "<cmd>close<cr>", { buffer = buf, silent = true })
end

--- List notes linked to an entity (e.g. "ticker:MRVL") in a scratch split.
function M.list(entity)
  M.mind({ "notes", entity }, function(ok, notes)
    if not ok then
      vim.notify("finlarp: " .. tostring(notes), vim.log.levels.ERROR)
      return
    end
    local lines = { "# " .. entity .. "  (" .. #notes .. " notes)", "" }
    for _, n in ipairs(notes) do
      table.insert(lines, ("## %s [%s/%s]"):format(n.ts:sub(1, 16), n.kind, n.status))
      vim.list_extend(lines, vim.split(n.body, "\n"))
      if n.answer then
        vim.list_extend(lines, { "", "> " .. n.answer:gsub("\n", "\n> ") })
      end
      table.insert(lines, "")
    end
    vim.cmd("botright new")
    local buf = vim.api.nvim_get_current_buf()
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
    vim.bo[buf].buftype = "nofile"
    vim.bo[buf].filetype = "markdown"
    vim.keymap.set("n", "q", "<cmd>close<cr>", { buffer = buf, silent = true })
  end)
end

function M.setup()
  vim.api.nvim_create_user_command("FinlarpNote", function(o)
    M.open(o.range > 0)
  end, { range = true })
  vim.api.nvim_create_user_command("FinlarpAnswer", M.show_last, {})
  vim.api.nvim_create_user_command("FinlarpNotes", function(o)
    local e = o.args:find(":") and o.args or ("ticker:" .. o.args:upper())
    M.list(e)
  end, { nargs = 1 })
end

return M
