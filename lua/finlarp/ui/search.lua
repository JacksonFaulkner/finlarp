--- Live full-text search over pulled SEC text (views/search.py): 10-K/
--- 20-F sections, new-this-year risk language, earnings releases and
--- guidance, Yahoo profiles and (with type:patent) granted patents. BM25 in
--- DuckDB; neither front end does fuzzy matching.
---
--- Two front ends over the same engine and query syntax:
---
---   M.pick(initial)      fzf-lua live picker. Re-runs `search.py q --fzf`
---                        per (debounced) keystroke: a process per query,
---                        ~130-450ms. ANSI columns (ticker, type badge, dim
---                        date, section, snippet with terms highlighted), a
---                        facet summary header line (top tickers / types /
---                        years over all matches) and a preview of the chunk
---                        ± 1 neighbour with terms highlighted.
---   M.pick_tui(initial)  ratatui screen (tui/src/screens/search)
---                        in the popup, via ui/tui.lua
---                        open_screen. Talks to one long-lived
---                        `search.py --serve` (~40-130ms warm), with a facet
---                        sidebar that rewrites t:/type:/sec:/since: tokens,
---                        a scrollable context preview and query history.
---                        Its enter / alt-v come back here as open_chunk /
---                        docview actions.
---   M.open_chunk(id)     chunk + 2 neighbours in a scratch split (both
---                        front ends' <CR>).
---
--- Query syntax is the same one agents use via the CLI:
---   t:MRVL,NVDA  s:memory  r:US  i:software  type:10k|risk|new|earn|guid|patent|profile
---   sec:risk  since:2025  "exact phrase"  -exclude  plus free text
---
--- fzf keys:  <CR> open the chunk with surrounding context in a scratch split
---            alt-v open the source document inside nvim at this passage (ui/docview.lua)
---            ctrl-o open the filing's SEC index page in the browser
--- TUI keys:  same three, plus tab (focus), ^j/^k, y copy, ? help (see search/mod.rs KEYS)
local M = {}

local plugin_dir = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":h:h:h:h")
-- Venv python directly: `uv run` adds ~100ms per keystroke.
local python = plugin_dir .. "/.venv/bin/python"
local script = plugin_dir .. "/views/search.py"
local DEBOUNCE_S = "0.2"

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

--- Opens chunk `id` (string or number) with 2 neighbouring chunks either
--- side in a scratch vsplit, cursor on the hit.
function M.open_chunk(id)
  id = tostring(id)
  vim.system({ python, script, "get", id, "--context", "2", "--json" }, { text = true }, function(res)
    vim.schedule(function()
      local ok, rows = pcall(vim.json.decode, res.stdout or "", { luanil = { object = true, array = true } })
      if res.code ~= 0 or not ok or not rows[1] then
        vim.notify("finlarp: " .. (res.stderr or "search get failed"), vim.log.levels.ERROR)
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
    vim.notify("finlarp: fzf-lua not installed", vim.log.levels.ERROR)
    return
  end
  if vim.fn.executable(python) ~= 1 then
    vim.notify("finlarp: " .. python .. " missing — run `uv sync`", vim.log.levels.ERROR)
    return
  end
  -- Debounce: fzf kills an in-flight reload when the query changes, so a
  -- short sleep ahead of the query means only a typing pause actually
  -- hits DuckDB (~450ms on the full index) instead of every keystroke.
  fzf.fzf_live("sleep " .. DEBOUNCE_S .. " && " .. cmd("q", "--fzf", "<query>"), {
    prompt = "Filings> ",
    query = initial or "",
    exec_empty_query = true,
    fzf_opts = {
      ["--ansi"] = true,
      ["--delimiter"] = "\t",
      ["--with-nth"] = "2..",
      -- first output line is the facet summary for the current query
      ["--header-lines"] = "1",
      ["--preview"] = cmd("get", "{1}", "--context", "1", "--color", "--terms", "{q}"),
      ["--preview-window"] = "down,55%,wrap",
      ["--header"] = 't:TICK s:sector r:region type:10k|risk|new|earn|guid|patent sec:mda since:2025 "phrase" -word',
    },
    actions = {
      ["default"] = function(selected)
        local id = chunk_id(selected)
        if id then
          M.open_chunk(id)
        end
      end,
      ["alt-v"] = function(selected)
        -- the source document inside nvim, jumped to the chunk's opening words
        local id = chunk_id(selected)
        if not id then
          return
        end
        local res = vim.system({ python, script, "get", id, "--json" }, { text = true }):wait()
        local rok, rows = pcall(vim.json.decode, res.stdout or "", { luanil = { object = true, array = true } })
        if rok and rows[1] and rows[1].url then
          local words = {}
          for w in rows[1].text:gmatch("%S+") do
            words[#words + 1] = w
            if #words == 10 then
              break
            end
          end
          require("finlarp.ui.docview").open(rows[1].url, table.concat(words, " "))
        end
      end,
      ["ctrl-o"] = function(selected)
        local id = chunk_id(selected)
        if not id then
          return
        end
        local res = vim.system({ python, script, "get", id, "--json" }, { text = true }):wait()
        local rok, rows = pcall(vim.json.decode, res.stdout or "", { luanil = { object = true, array = true } })
        if rok and rows[1] and rows[1].url then
          vim.ui.open(rows[1].url)
        end
      end,
    },
  })
end

--- The ratatui search screen in the popup (see header). Falls back to the
--- fzf picker if the popup launcher isn't available.
--- @param initial string|nil prefilled query
function M.pick_tui(initial)
  local ok, pc = pcall(require, "finlarp.ui.tui")
  if not ok or type(pc.open_screen) ~= "function" then
    vim.notify("finlarp: tui.open_screen unavailable, using fzf", vim.log.levels.WARN)
    return M.pick(initial)
  end
  pc.open_screen("search", initial or "", { title = " search " })
end

return M
