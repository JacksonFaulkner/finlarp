--- Live full-text search over pulled SEC text (services/search.py): 10-K/
--- 20-F sections, new-this-year risk language, earnings releases and
--- guidance. fzf re-runs the query on every keystroke (BM25 in DuckDB,
--- ~130ms), so fzf itself does no fuzzy matching.
---
--- Query syntax is the same one agents use via the CLI:
---   t:MRVL,NVDA  s:memory  r:US  type:guid  sec:risk  since:2025
---   "exact phrase"  -exclude  plus free text
---
--- <CR>    open the chunk with surrounding context in a scratch split
--- ctrl-o  open the filing's SEC index page in the browser
local M = {}

local plugin_dir = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":h:h")
-- Venv python directly: `uv run` adds ~100ms per keystroke.
local python = plugin_dir .. "/.venv/bin/python"
local script = plugin_dir .. "/services/search.py"

local function cmd(...)
  local parts = { vim.fn.shellescape(python), vim.fn.shellescape(script) }
  for _, a in ipairs({ ... }) do
    parts[#parts + 1] = a
  end
  return table.concat(parts, " ")
end

local function chunk_id(selected)
  return selected and selected[1] and selected[1]:match("^(%d+)\t")
end

local function open_chunk(id)
  vim.system({ python, script, "get", id, "--context", "2", "--json" }, { text = true }, function(res)
    vim.schedule(function()
      local ok, rows = pcall(vim.json.decode, res.stdout or "")
      if res.code ~= 0 or not ok or not rows[1] then
        vim.notify("security_spread: " .. (res.stderr or "search get failed"), vim.log.levels.ERROR)
        return
      end
      local r = rows[1]
      local lines = {
        string.format("# %s — %s / %s (%s, %s)", r.ticker, r.type, r.section or "", r.form or "", r.date or ""),
        r.url or "",
        "",
      }
      for _, row in ipairs(rows) do
        -- The hit itself is marked so it's findable among its neighbours.
        if tostring(row.id) == id then
          lines[#lines + 1] = ">>> match"
        end
        for _, l in ipairs(vim.split(row.text, "\n")) do
          lines[#lines + 1] = l
        end
        lines[#lines + 1] = ""
      end
      vim.cmd("botright vnew")
      local buf = vim.api.nvim_get_current_buf()
      vim.bo[buf].buftype = "nofile"
      vim.bo[buf].bufhidden = "wipe"
      vim.bo[buf].filetype = "markdown"
      vim.wo.wrap = true
      vim.wo.linebreak = true
      vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
      vim.bo[buf].modifiable = false
      vim.keymap.set("n", "q", "<cmd>close<cr>", { buffer = buf, silent = true })
      vim.fn.search(">>> match")
    end)
  end)
end

--- @param initial string|nil prefilled query, e.g. "t:MRVL "
function M.pick(initial)
  local ok, fzf = pcall(require, "fzf-lua")
  if not ok then
    vim.notify("security_spread: fzf-lua not installed", vim.log.levels.ERROR)
    return
  end
  if vim.fn.executable(python) ~= 1 then
    vim.notify("security_spread: " .. python .. " missing — run `uv sync`", vim.log.levels.ERROR)
    return
  end
  fzf.fzf_live(cmd("q", "<query>"), {
    prompt = "Filings> ",
    query = initial or "",
    exec_empty_query = true,
    fzf_opts = {
      ["--delimiter"] = "\t",
      ["--with-nth"] = "2..",
      ["--preview"] = cmd("get", "{1}", "--context", "1"),
      ["--preview-window"] = "down,55%,wrap",
      ["--header"] = "t:TICK s:sector r:region type:10k|risk|new|earn|guid sec:mda since:2025 \"phrase\" -word",
    },
    actions = {
      ["default"] = function(selected)
        local id = chunk_id(selected)
        if id then
          open_chunk(id)
        end
      end,
      ["ctrl-o"] = function(selected)
        local id = chunk_id(selected)
        if not id then
          return
        end
        local res = vim.system({ python, script, "get", id, "--json" }, { text = true }):wait()
        local rok, rows = pcall(vim.json.decode, res.stdout or "")
        if rok and rows[1] and rows[1].url then
          vim.ui.open(rows[1].url)
        end
      end,
    },
  })
end

return M
