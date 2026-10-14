-- Godel-key UI. Same workflow as notes:
--   <leader>vn  type "> aapl q4 performance 2023" (a leading ">" routes here instead of a note)
--   ...cooking...  a notification fires when the model replies
--   <leader>vm  opens this viewer while there are unseen results (else the notes viewer);
--               ctrl-g in either viewer jumps to the other.
-- The top-ten command list comes from py/derive/godel_key.py (model, structured output); parse() is the offline fallback.
-- The RESULT section is still canned.

local M = {}

M.items = {} -- newest first: { id, query, key, args, status, ts, result, seen }
local next_id = 1

local finlarp_root = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":h:h:h:h")
local env_file = finlarp_root .. "/.env"

local CMD_NAMES = {
  DES = "Description",
  FA = "Financials",
  GR = "Ratio Analysis",
  EVT = "Company Events",
  HDS = "Holders",
  CF = "Filings",
  N = "News",
  HP = "Historical Prices",
  HMS = "Historical Multiple Security",
  EQS = "Equity Screener",
}
-- where each key lands in finlarp today
local ROUTES = {
  DES = "company() / dossier header",
  FA = "financials() / XBRL",
  GR = "derive from XBRL (formula on `i`)",
  EVT = "events screen / 8-K stream",
  HDS = "13F + Form 4 tables",
  CF = "filing index / 10-K text",
  N = "news() + tweet stance",
  HP = "bars_1d / chart screen",
  HMS = "bars_1d, multi-ticker chart",
  EQS = "sql over universe + XBRL",
}

--- Canned NL -> key. Real version: LLM structured output validated against the Command enum.
local function parse(q)
  local lower = q:lower()
  local tickers = {}
  for w in q:gmatch("%a+") do
    if #w >= 2 and #w <= 5 and w == w:upper() and not w:match("^Q%d$") then
      table.insert(tickers, w)
    end
  end
  if #tickers == 0 then
    for w in lower:gmatch("%a+") do
      if
        #w >= 3
        and #w <= 5
        and vim.tbl_contains({ "aapl", "nvda", "mrvl", "amd", "msft", "googl", "tsm", "avgo" }, w)
      then
        table.insert(tickers, w:upper())
      end
    end
  end
  local args = {}
  local qn = lower:match("q([1-4])")
  if qn then
    args.period = "Q" .. qn
  end
  local yr = lower:match("(20%d%d)")
  if yr then
    args.year = tonumber(yr)
  end
  local cmd
  if lower:match("screen") or lower:match("stocks with") then
    cmd = "EQS"
  elseif #tickers > 1 or lower:match(" vs ") then
    cmd = "HMS"
  elseif lower:match("holder") or lower:match("13f") or lower:match("bought") or lower:match("insider") then
    cmd = "HDS"
  elseif lower:match("10%-?k") or lower:match("filing") then
    cmd = "CF"
  elseif lower:match("8%-?k") or lower:match("event") or lower:match("catalyst") then
    cmd = "EVT"
  elseif lower:match("news") then
    cmd = "N"
  elseif lower:match("margin") or lower:match("ratio") then
    cmd = "GR"
  elseif
    args.period
    or lower:match("revenue")
    or lower:match("eps")
    or lower:match("income")
    or lower:match("performance")
  then
    cmd = "FA"
  elseif lower:match("price") or lower:match("stock") or lower:match("return") then
    cmd = "HP"
  else
    cmd = "DES"
  end
  return { ticker = tickers[1] or "?", tickers = tickers, country = "US", asset = "EQ", cmd = cmd, args = args }
end

local function key_string(k)
  local parts = { table.concat(#k.tickers > 1 and k.tickers or { k.ticker }, ","), k.country, k.asset, k.cmd }
  if k.args.year or k.args.period then
    table.insert(parts, (k.args.year or "") .. (k.args.period or ""))
  end
  return table.concat(parts, " ")
end

local function fake_result(k)
  local t = k.ticker
  local when = (k.args.period or "FY") .. " " .. (k.args.year or "latest")
  local lines = {
    FA = {
      ("%s revenue (%s): $89.5B   +2%% YoY"):format(t, when),
      "gross margin 45.2%   op income $27.4B",
      "diluted EPS $2.18",
      "source: XBRL companyfacts, 10-K (fake numbers)",
    },
    DES = {
      t .. ": AI-universe member, sub-sector: (fake)",
      "business summary from 10-K item 1",
      "market cap / profile from Yahoo",
    },
    HP = { ("%s close 2023-12-29: 192.53   YTD +48%%"):format(t), "source: bars_1d (fake numbers)" },
    HMS = { table.concat(k.tickers, " vs ") .. " rebased to 100", "(fake) chart goes here" },
    HDS = { "top 13F adds last quarter: (fake)", "Form 4: 3 sells, 0 buys" },
    EVT = { "8-K 2023-11-02 item 2.02 earnings", "8-K 2023-08-04 item 5.02 officer change" },
    CF = { "10-K FY2023 filed 2023-11-03", "risk factors: 4 YoY-new sentences" },
    N = { "3 headlines last 7d", "tweet stance: 62% bullish (fake)" },
    GR = { "net margin 25.3%  ROIC 52%  (fake)", "formula shown on `i`" },
    EQS = { "filters parsed: (fake)", "17 matches in universe" },
  }
  return lines[k.cmd] or { "(no fake data)" }
end

--- Top 10 commands for this item: the model's ranked list (py/derive/godel_key.py) when it answered, else the local
--- parser's key first and the rest in fixed order.
local SUGGEST_ORDER = { "DES", "FA", "GR", "EVT", "HDS", "CF", "N", "HP", "HMS", "EQS" }

local function suggestions(it)
  if it.commands then
    local out = {}
    for _, c in ipairs(it.commands) do
      table.insert(out, { text = c.key, name = c.name, why = c.why })
    end
    return out
  end
  local k = it.key
  local order = { k.cmd }
  for _, c in ipairs(SUGGEST_ORDER) do
    if c ~= k.cmd then
      table.insert(order, c)
    end
  end
  local out = {}
  for _, c in ipairs(order) do
    local kk = vim.tbl_extend("force", k, { cmd = c })
    table.insert(out, { text = key_string(kk), name = CMD_NAMES[c] or "" })
  end
  return out
end

local function preview_text(it)
  local k = it.key
  local lines = { "YOU ASKED", "", it.query, "", ("%s  ·  %s"):format(it.ts, it.status), "" }
  table.insert(lines, ("── GODEL KEY %s"):format(("─"):rep(48)))
  table.insert(lines, "")
  table.insert(lines, "  " .. key_string(k))
  table.insert(lines, ("  %s: %s"):format(k.cmd, CMD_NAMES[k.cmd] or ""))
  table.insert(lines, "")
  table.insert(lines, "  ticker   " .. table.concat(k.tickers, ", "))
  table.insert(lines, "  period   " .. (k.args.period or "-"))
  table.insert(lines, "  year     " .. (k.args.year and tostring(k.args.year) or "-"))
  table.insert(lines, "  routes   " .. (ROUTES[k.cmd] or "?"))
  table.insert(lines, "")
  table.insert(lines, ("── RESULT %s"):format(("─"):rep(52)))
  table.insert(lines, "")
  if it.result then
    vim.list_extend(lines, it.result)
  else
    table.insert(lines, "(cooking…)")
  end
  local sugg, first = suggestions(it), nil
  table.insert(lines, "")
  table.insert(lines, ("── TOP 10 COMMANDS  (<Tab> focus · j/k move · y copy) %s"):format(("─"):rep(8)))
  table.insert(lines, "")
  for i, sg in ipairs(sugg) do
    table.insert(lines, ("  %2d  %-28s %s"):format(i, sg.text, sg.why or sg.name))
    first = first or #lines
  end
  return lines, first, sugg
end

local GLYPH = { done = "✓", cooking = "…" }

function M.has_unseen()
  for _, it in ipairs(M.items) do
    if it.status == "done" and not it.seen then
      return true
    end
  end
  return false
end

--- Parse locally right away (so the list shows a key), then ask the model for the ranked top-ten commands in the
--- background. On failure the local fallback list stays and the error is notified.
function M.submit(query)
  query = vim.trim((query:gsub("^>%s*", "")))
  if query == "" then
    return
  end
  local it = { id = tostring(next_id), query = query, key = parse(query), status = "cooking", ts = os.date("%H:%M:%S") }
  next_id = next_id + 1
  table.insert(M.items, 1, it)
  vim.notify("finlarp: " .. key_string(it.key) .. "  cooking…", vim.log.levels.INFO)
  local cmd = { "uv", "run", "--env-file", env_file, "py/derive/godel_key.py", query }
  vim.system(cmd, { cwd = finlarp_root, text = true }, function(res)
    vim.schedule(function()
      local ok, data = false, nil
      if res.code == 0 then
        ok, data = pcall(vim.json.decode, res.stdout, { luanil = { object = true, array = true } })
      end
      if ok and data and data.commands and #data.commands > 0 then
        it.commands = data.commands
      else
        local err = vim.trim(res.stderr or "")
        vim.notify(
          "finlarp godel: model failed, showing local guess" .. (err ~= "" and ("\n" .. err:sub(-300)) or ""),
          vim.log.levels.WARN
        )
      end
      it.status, it.result = "done", fake_result(it.key)
      vim.notify(
        ("finlarp: %s ready  (<leader>vm)"):format(it.commands and it.commands[1].key or key_string(it.key)),
        vim.log.levels.INFO
      )
    end)
  end)
end

function M.open()
  if #M.items == 0 then
    vim.notify('finlarp: no godel queries yet (<leader>vn, then start with ">")', vim.log.levels.INFO)
    return
  end
  local by_id, rows = {}, {}
  for _, it in ipairs(M.items) do
    by_id[it.id] = it
    table.insert(
      rows,
      ("%s\t%s %s  %-24s  %s"):format(
        it.id,
        GLYPH[it.status],
        it.seen and " " or "●",
        (it.commands and it.commands[1].key or key_string(it.key)),
        it.query
      )
    )
  end
  local header = "<Tab> into commands (j/k, y copy)  <CR> open screen (fake)  ^g notes  ^d delete"
  require("fzf-lua").fzf_exec(rows, {
    prompt = "Godel❯ ",
    fzf_opts = { ["--delimiter"] = "\t", ["--with-nth"] = "2", ["--header"] = header },
    winopts = {
      fullscreen = true,
      preview = { wrap = true, layout = "vertical", vertical = "down:72%", title = false },
    },
    keymap = { builtin = { ["<Tab>"] = "focus-preview" } },
    previewer = {
      _ctor = function()
        local P = require("fzf-lua.previewer.builtin").base:extend()
        function P:new(o, opts, fzf_win)
          P.super.new(self, o, opts, fzf_win)
          return self
        end
        function P:populate_preview_buf(entry_str)
          local it = by_id[vim.split(entry_str, "\t", { plain = true })[1]]
          if it and it.status == "done" then
            it.seen = true
          end
          local buf = self:get_tmp_buffer()
          local lines, first, sugg = {}, nil, {}
          if it then
            lines, first, sugg = preview_text(it)
          end
          vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
          vim.bo[buf].filetype = "text"
          if first then
            vim.keymap.set("n", "y", function()
              local i = vim.api.nvim_win_get_cursor(0)[1] - first + 1
              local sg = sugg[i]
              if not sg then
                return
              end
              vim.fn.setreg("+", sg.text)
              vim.fn.setreg('"', sg.text)
              vim.notify("finlarp: copied  " .. sg.text, vim.log.levels.INFO)
            end, { buffer = buf, nowait = true, desc = "copy godel command" })
          end
          self:set_preview_buf(buf)
          if first then
            local win = self.win and self.win.preview_winid
            if win and vim.api.nvim_win_is_valid(win) then
              pcall(vim.api.nvim_win_set_cursor, win, { first, 2 })
              vim.wo[win].cursorline = true
            end
          end
        end
        return P
      end,
    },
    actions = {
      ["default"] = function(sel)
        local it = sel and by_id[vim.split(sel[1], "\t", { plain = true })[1]]
        if it then
          vim.notify("finlarp (fake): would open " .. key_string(it.key), vim.log.levels.INFO)
        end
      end,
      ["ctrl-g"] = function()
        require("finlarp.ui.notes").open()
      end,
      ["ctrl-d"] = function(sel)
        local it = sel and by_id[vim.split(sel[1], "\t", { plain = true })[1]]
        if it then
          M.items = vim.tbl_filter(function(x)
            return x ~= it
          end, M.items)
          vim.schedule(M.open)
        end
      end,
    },
  })
end

return M
