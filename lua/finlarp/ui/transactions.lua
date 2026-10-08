local M = {}

--- @param t table one transaction from py/sources/etrade.py's cmd_transactions
--- @return string fzf-lua row: fixed-width columns so alignment stays fuzzy-searchable
local function format_row(t)
  local date = t.date and os.date("%Y-%m-%d %H:%M:%S", math.floor(t.date / 1000)) or "?"
  local symbol = t.symbol or ""
  local ttype = t.type or ""
  local qty = t.quantity and string.format("%.4g", t.quantity) or ""
  local price = t.price and string.format("$%.2f", t.price) or ""
  local amount = t.amount and string.format("%+.2f", t.amount) or ""
  local desc = t.description or ""

  return string.format("%-19s %-6s %-14s %-8s %-10s %-10s  %s", date, symbol, ttype, qty, price, amount, desc)
end

local function open_picker(fzf, transactions)
  table.sort(transactions, function(a, b)
    return (a.date or 0) > (b.date or 0)
  end)

  local rows = {}
  local by_row = {}
  for _, t in ipairs(transactions) do
    local row = format_row(t)
    rows[#rows + 1] = row
    by_row[row] = t
  end

  fzf.fzf_exec(rows, {
    prompt = "Transactions> ",
    fzf_opts = {
      ["--header"] = "date                sym    type           qty      price      amount      description",
    },
    actions = {
      ["default"] = function(selected)
        local t = by_row[selected[1]]
        if not t then
          return
        end
        local lines = {}
        for k, v in pairs(t) do
          lines[#lines + 1] = string.format("%s: %s", k, tostring(v))
        end
        table.sort(lines)
        vim.notify(table.concat(lines, "\n"), vim.log.levels.INFO, { title = "Transaction detail" })
      end,
    },
  })
end

--- Opens an fzf-lua picker over transaction history. Paints instantly from
--- whatever's cached in DuckDB (see py/core/db.py) — same instant-then-refresh
--- pattern as `$`. If nothing's cached yet (first run), falls back to
--- blocking on the live E*TRADE pull once. Either way, a live pull always
--- runs in the background afterward to keep the cache warm for next time;
--- fzf-lua has no live-reload hook for an already-open custom picker, so
--- that refresh lands silently and shows up on the *next* `<leader>st`.
--- Fuzzy-search any column: date, symbol, type, or description. <CR>
--- shows the full raw record.
function M.pick()
  local ok, fzf = pcall(require, "fzf-lua")
  if not ok then
    vim.notify("finlarp: fzf-lua not installed", vim.log.levels.ERROR)
    return
  end

  local ss = require("finlarp")

  ss.transactions_cached(function(cok, cached)
    local opened_from_cache = cok and cached and #cached > 0
    if opened_from_cache then
      open_picker(fzf, cached)
    else
      vim.notify("finlarp: loading transaction history...", vim.log.levels.INFO)
    end

    ss.transactions(function(tok, transactions)
      if not tok then
        if not opened_from_cache then
          vim.notify("finlarp: " .. tostring(transactions), vim.log.levels.ERROR)
        end
        return
      end
      if #transactions == 0 then
        if not opened_from_cache then
          vim.notify("finlarp: no transactions found", vim.log.levels.WARN)
        end
        return
      end
      if not opened_from_cache then
        open_picker(fzf, transactions)
      end
    end)
  end)
end

return M
