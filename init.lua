local M = {}

local plugin_dir = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":h")
local env_file = plugin_dir .. "/.env"

local run -- forward-declared: start_reauth retries through `run` itself

--- E*TRADE's token expired and nvim isn't a TTY sources/etrade.py can block
--- on for input() — it hands back an `auth_required` payload instead of
--- erroring, and this drives the two-step login: open the browser (you
--- look at the page yourself and copy the code), then an explicit
--- `vim.ui.input` prompt for you to paste it into. Deliberately NOT reading
--- the system clipboard here, even to auto-detect a code-shaped string —
--- that's a silent-exfiltration pattern and this only acts on what you
--- actually type/paste into the prompt yourself.
--- @param decoded table { authorize_url, request_token, request_token_secret }
--- @param retry fun() re-runs the original call once login completes
local function start_reauth(decoded, retry, fail)
  vim.notify("security_spread: E*TRADE session expired — opening browser to re-authorize", vim.log.levels.WARN)
  if vim.ui.open then
    vim.ui.open(decoded.authorize_url)
  else
    vim.fn.jobstart({ "open", decoded.authorize_url }, { detach = true })
  end

  vim.ui.input({ prompt = "E*TRADE verification code: " }, function(code)
    if not code or code == "" then
      vim.notify("security_spread: re-auth cancelled", vim.log.levels.WARN)
      fail("re-auth cancelled")
      return
    end
    run(
      "sources/etrade.py",
      { "auth_finish", decoded.request_token, decoded.request_token_secret, code },
      function(fok, fdata)
        if not fok then
          vim.notify("security_spread: re-auth failed: " .. tostring(fdata), vim.log.levels.ERROR)
          fail("re-auth failed")
          return
        end
        vim.notify("security_spread: re-authorized", vim.log.levels.INFO)
        retry()
      end
    )
  end)
end

--- Runs `uv run <script> <args>` async and decodes the JSON stdout. If the
--- script is sources/etrade.py and the cached token expired, transparently
--- drives the re-auth flow and retries the original call once it succeeds
--- — callers never see an auth failure, just a slower first response.
--- @param script string e.g. "sources/etrade.py" or "sources/yahoo.py"
--- @param args string[] extra CLI args, e.g. { "quote", "AAPL,MSFT" }
--- @param callback fun(ok: boolean, data_or_err: any)
run = function(script, args, callback)
  local cmd = vim.list_extend({
    "uv",
    "run",
    "--env-file",
    env_file,
    script,
  }, args)

  vim.system(cmd, { cwd = plugin_dir, text = true }, function(result)
    vim.schedule(function()
      if result.code ~= 0 then
        callback(false, result.stderr ~= "" and result.stderr or script .. " exited " .. result.code)
        return
      end
      local ok, decoded = pcall(vim.json.decode, result.stdout, { luanil = { object = true, array = true } })
      if not ok then
        callback(false, "failed to decode JSON: " .. result.stdout)
        return
      end
      if type(decoded) == "table" and decoded.auth_required then
        start_reauth(decoded, function()
          run(script, args, callback)
        end, function(err)
          callback(false, err) -- settle the caller (auto-refresh's in_flight)
        end)
        return
      end
      callback(true, decoded)
    end)
  end)
end

--- @param callback fun(ok: boolean, positions_or_err: any)
function M.positions(callback)
  run("sources/etrade.py", { "positions" }, function(ok, data)
    if ok then
      callback(true, data.positions)
    else
      callback(false, data)
    end
  end)
end

--- Local-only read (no network/OAuth) from the DuckDB cache written by the
--- last live `positions` pull. `callback` gets nil if nothing's cached yet.
--- @param callback fun(ok: boolean, positions_or_err: any)
function M.positions_cached(callback)
  run("sources/etrade.py", { "positions_cached" }, function(ok, data)
    if ok then
      callback(true, data.positions)
    else
      callback(false, data)
    end
  end)
end

--- @param callback fun(ok: boolean, orders_or_err: any)
function M.orders(callback)
  run("sources/etrade.py", { "orders" }, function(ok, data)
    if ok then
      callback(true, data.orders)
    else
      callback(false, data)
    end
  end)
end

--- @param callback fun(ok: boolean, transactions_or_err: any)
function M.transactions(callback)
  run("sources/etrade.py", { "transactions" }, function(ok, data)
    if ok then
      callback(true, data.transactions)
    else
      callback(false, data)
    end
  end)
end

--- Local-only read (no network/OAuth) from the DuckDB cache — instant.
--- @param callback fun(ok: boolean, transactions_or_err: any)
function M.transactions_cached(callback)
  run("sources/etrade.py", { "transactions_cached" }, function(ok, data)
    if ok then
      callback(true, data.transactions)
    else
      callback(false, data)
    end
  end)
end

--- @param symbols string[] e.g. { "AAPL", "MSFT" }
--- @param callback fun(ok: boolean, quotes_or_err: any)
function M.quote(symbols, callback)
  run("sources/etrade.py", { "quote", table.concat(symbols, ",") }, function(ok, data)
    if ok then
      callback(true, data.quotes)
    else
      callback(false, data)
    end
  end)
end

--- @param symbols string[] e.g. { "NVDA", "AMD" }
--- @param callback fun(ok: boolean, quotes_or_err: any)
function M.quote_yahoo(symbols, callback)
  run("sources/yahoo.py", { "quote", table.concat(symbols, ",") }, function(ok, data)
    if ok then
      callback(true, data.quotes)
    else
      callback(false, data)
    end
  end)
end

--- @param filters table|nil { sector, industry, top } — no real position, just
---   a market screen (top N by market cap matching the filters).
--- @param callback fun(ok: boolean, quotes_or_err: any)
function M.screen_yahoo(filters, callback)
  filters = filters or {}
  local args = { "screen" }
  if filters.sector then
    vim.list_extend(args, { "--sector", filters.sector })
  end
  if filters.industry then
    vim.list_extend(args, { "--industry", filters.industry })
  end
  if filters.top then
    vim.list_extend(args, { "--top", tostring(filters.top) })
  end
  run("sources/yahoo.py", args, function(ok, data)
    if ok then
      callback(true, data.quotes)
    else
      callback(false, data)
    end
  end)
end

--- @param callback fun(ok: boolean, groups_or_err: any) groups: { { level, category, parent, count } }
function M.universe_groups(callback)
  run("sources/yahoo.py", { "universe", "groups" }, function(ok, data)
    if ok then
      callback(true, data.groups)
    else
      callback(false, data)
    end
  end)
end

--- @param level "primary"|"sub"|"region"
--- @param category string
--- @param callback fun(ok: boolean, members_or_err: any) members: { { ticker, name, weight } }
function M.universe_members(level, category, callback)
  run("sources/yahoo.py", { "universe", "members", level, category }, function(ok, data)
    if ok then
      callback(true, data.members)
    else
      callback(false, data)
    end
  end)
end

--- @param symbol string e.g. "NVDA"
--- @param callback fun(ok: boolean, points_or_err: any) points: { { t, close }, ... }
function M.history_yahoo(symbol, callback)
  run("sources/yahoo.py", { "history", symbol }, function(ok, data)
    if ok then
      callback(true, data.points)
    else
      callback(false, data)
    end
  end)
end

--- Renders a matplotlib PNG overlay chart for `series` ({ { symbol, closes } })
--- at the given pixel size, writing it to a temp file.
--- @param series table[]
--- @param width_px integer
--- @param height_px integer
--- @param callback fun(ok: boolean, path_or_err: any)
function M.render_chart(series, width_px, height_px, callback)
  local cmd = { "uv", "run", "--env-file", env_file, "views/chart_render.py" }
  local payload = vim.json.encode({ series = series, width_px = width_px, height_px = height_px })
  vim.system(cmd, { cwd = plugin_dir, text = true, stdin = payload }, function(result)
    vim.schedule(function()
      if result.code ~= 0 then
        callback(false, result.stderr ~= "" and result.stderr or "views/chart_render.py exited " .. result.code)
        return
      end
      local ok, decoded = pcall(vim.json.decode, result.stdout, { luanil = { object = true, array = true } })
      if not ok then
        callback(false, "failed to decode JSON: " .. result.stdout)
        return
      end
      callback(true, decoded.path)
    end)
  end)
end

--- Opens a historical price overlay chart for one or more symbols in a
--- floating window (normalized to % change so different price scales
--- compare on one chart).
--- @param symbols string[]
function M.show_chart(symbols)
  require("custom_plugins.security_spread.ui.chart").show(symbols)
end

--- Charts the <Space>-selected symbols (up to 4) in the dashboard under the
--- cursor — falls back to whichever tile is currently focused if none
--- selected.
function M.show_chart_current()
  local symbols = require("custom_plugins.security_spread.ui.window").selected_symbols()
  if #symbols == 0 then
    vim.notify("security_spread: no tile focused/selected", vim.log.levels.WARN)
    return
  end
  M.show_chart(symbols)
end

--- Opens (or replaces in place) a named treemap session for a plain list of
--- quotes already in tile-ready shape ({ symbol, value, last_price,
--- change_close, change_close_pct }).
--- @param name string session key — reuse a watchlist's name to let multiple
---   dashboards coexist (e.g. one docked left, one docked right).
--- @param merged table[]
--- @param opts table|nil { row, col, width, height } — sub-region to dock into
function M.show_quotes(name, merged, opts)
  local window = require("custom_plugins.security_spread.ui.window")
  -- If this session's tiles are already up for the same set of symbols
  -- (the common case for a background data refresh), update their text in
  -- place instead of the full close/relayout/reopen M.open does — avoids
  -- the visible flash and cursor snap-back on every refresh. Falls back to
  -- a real open for the first draw or when the symbol set changed.
  if not window.update_quotes(name, merged) then
    window.open(name, merged, opts)
  end
end

--- Opens a market-cap-sized treemap for a Yahoo screener watchlist (no real
--- position — value is market cap).
--- @param name string
--- @param filters table|nil { sector, industry, top }
--- @param opts table|nil region to dock into
function M.show_screen(name, filters, opts)
  M.screen_yahoo(filters, function(ok, quotes)
    if not ok then
      vim.notify("security_spread: " .. tostring(quotes), vim.log.levels.ERROR)
      return
    end
    local merged = {}
    for _, q in ipairs(quotes) do
      merged[#merged + 1] = {
        symbol = q.symbol,
        value = q.market_cap or 1,
        last_price = q.last_trade,
        change_close = q.change_close,
        change_close_pct = q.change_close_pct,
      }
    end
    M.show_quotes(name, merged, opts)
  end)
end

--- Opens an equal-weighted treemap for a fixed symbol list (Yahoo quotes,
--- no real position behind them).
--- @param name string
--- @param symbols string[]
--- @param opts table|nil region to dock into
function M.show_symbols(name, symbols, opts)
  M.quote_yahoo(symbols, function(ok, quotes)
    if not ok then
      vim.notify("security_spread: " .. tostring(quotes), vim.log.levels.ERROR)
      return
    end
    local merged = {}
    for _, q in ipairs(quotes) do
      merged[#merged + 1] = {
        symbol = q.symbol,
        value = 1,
        last_price = q.last_trade,
        change_close = q.change_close,
        change_close_pct = q.change_close_pct,
      }
    end
    M.show_quotes(name, merged, opts)
  end)
end

--- Treemap of one AI-universe group, tiles sized by each member's weight
--- to that bucket (region groups are equal-sized).
--- @param group table { level, category }
--- @param opts table|nil region to dock into
function M.show_universe_group(group, opts)
  M.universe_members(group.level, group.category, function(ok, members)
    if not ok then
      vim.notify("security_spread: " .. tostring(members), vim.log.levels.ERROR)
      return
    end
    local weight_of, symbols = {}, {}
    for _, m in ipairs(members) do
      weight_of[m.ticker] = m.weight
      symbols[#symbols + 1] = m.ticker
    end
    local name = "AI: " .. group.category
    M.quote_yahoo(symbols, function(qok, quotes)
      if not qok then
        vim.notify("security_spread: " .. tostring(quotes), vim.log.levels.ERROR)
        return
      end
      local merged = {}
      for _, q in ipairs(quotes) do
        merged[#merged + 1] = {
          symbol = q.symbol,
          value = weight_of[q.symbol] or 1,
          last_price = q.last_trade,
          change_close = q.change_close,
          change_close_pct = q.change_close_pct,
        }
      end
      M.show_quotes(name, merged, opts)
    end)
  end)
end

--- Aggregates positions by symbol (summing quantity/market_value across
--- accounts). portfolio.json already carries today's change per position
--- (daysGain/daysGainPct), so no separate quote() round trip is needed.
--- @param positions table[]
--- @return table[] merged in first-seen symbol order
local function merge_positions(positions)
  local by_symbol = {}
  local order = {}
  for _, p in ipairs(positions) do
    if p.symbol then
      if not by_symbol[p.symbol] then
        by_symbol[p.symbol] = {
          symbol = p.symbol,
          value = 0,
          quantity = 0,
          last_price = p.last_price,
          change_close = 0,
          change_close_pct = p.change_close_pct,
        }
        order[#order + 1] = p.symbol
      end
      local agg = by_symbol[p.symbol]
      agg.value = agg.value + (p.market_value or 0)
      agg.quantity = agg.quantity + (p.quantity or 0)
      agg.change_close = agg.change_close + (p.change_close or 0)
      agg.last_price = p.last_price or agg.last_price
    end
  end

  local merged = {}
  for _, symbol in ipairs(order) do
    merged[#merged + 1] = by_symbol[symbol]
  end
  return merged
end

--- name -> { timer, in_flight } for M.toggle_auto_refresh. Module-level so
--- a timer survives across calls and can be found again to stop it.
local auto_refresh = {}

--- Opens the treemap dashboard from whatever's cached in DuckDB (instant,
--- no network), then kicks off a live E*TRADE pull in the background and
--- redraws the same session in place once it lands — so `$` never blocks
--- on the network, it just shows stale-then-fresh. The same live pull is
--- wired up as `r` (manual refresh) and `R` (toggle auto-refresh) inside
--- the dashboard — see window.lua's session opts.on_refresh.
--- @param name string
--- @param opts table|nil region to dock into
function M.show_portfolio(name, opts)
  name = name or "My Portfolio"
  opts = opts or {}
  local window = require("custom_plugins.security_spread.ui.window")
  local opened = false
  --- Draw unless the user already closed this dashboard (or its docked
  --- split): cached, live and auto-refresh results all land async, and a
  --- late one would otherwise reopen it or draw into a dead window.
  local function show(quotes)
    if opened and not window.get_session(name) then
      return
    end
    if opts.win and not vim.api.nvim_win_is_valid(opts.win) then
      return
    end
    opened = true
    M.show_quotes(name, quotes, opts)
  end

  --- @param done fun()|nil called once the pull settles, ok or not — lets
  ---   the auto-refresh timer know it's safe to fire the next tick instead
  ---   of piling up requests behind a slow one.
  local function live_refresh(done)
    M.positions(function(ok, positions)
      if not ok then
        vim.notify("security_spread: " .. tostring(positions), vim.log.levels.ERROR)
      elseif #positions == 0 then
        vim.notify("security_spread: no positions found", vim.log.levels.WARN)
      else
        show(merge_positions(positions))
      end
      if done then
        done()
      end
    end)
  end
  opts.on_refresh = live_refresh

  M.positions_cached(function(cok, cached)
    if cok and cached and #cached > 0 then
      show(merge_positions(cached))
    end
  end)

  live_refresh()
end

M.show = M.show_portfolio

--- Toggles a periodic live refresh for an open `$`-style dashboard (bound
--- to `R` inside it). Skips a tick rather than queueing one if the
--- previous pull hasn't finished yet — a live pull is a real E*TRADE round
--- trip (~1-2s: positions + a balance.json call per account), so a short
--- interval must never let requests stack up.
--- @param name string
--- @param interval_ms integer|nil default 2000
function M.toggle_auto_refresh(name, interval_ms)
  local existing = auto_refresh[name]
  if existing then
    existing.timer:stop()
    existing.timer:close()
    auto_refresh[name] = nil
    vim.notify("security_spread: auto-refresh off", vim.log.levels.INFO)
    return
  end

  local window = require("custom_plugins.security_spread.ui.window")
  local session = window.get_session and window.get_session(name)
  if not session or not session.opts or not session.opts.on_refresh then
    vim.notify("security_spread: nothing to auto-refresh here", vim.log.levels.WARN)
    return
  end

  interval_ms = interval_ms or 2000
  local state = { in_flight = false }
  local timer = vim.uv.new_timer()
  timer:start(
    interval_ms,
    interval_ms,
    vim.schedule_wrap(function()
      if state.in_flight then
        return -- previous pull still in flight — skip this tick, don't stack
      end
      local s = window.get_session(name)
      if not s then
        timer:stop()
        timer:close()
        auto_refresh[name] = nil
        return
      end
      state.in_flight = true
      s.opts.on_refresh(function()
        state.in_flight = false
      end)
    end)
  )
  auto_refresh[name] = { timer = timer }
  vim.notify("security_spread: auto-refresh on every " .. interval_ms .. "ms", vim.log.levels.INFO)
end

--- Dispatches a watchlist entry (from watchlists.lua) into a named,
--- optionally region-docked session.
--- @param entry table one entry from watchlists.lua
--- @param opts table|nil region to dock into ({ row, col, width, height })
function M.show_entry(entry, opts)
  if entry.kind == "portfolio" then
    M.show_portfolio(entry.name, opts)
  elseif entry.kind == "screen" then
    M.show_screen(entry.name, { sector = entry.sector, industry = entry.industry, top = entry.top }, opts)
  elseif entry.kind == "symbols" then
    M.show_symbols(entry.name, entry.symbols, opts)
  else
    vim.notify("security_spread: unknown watchlist kind " .. tostring(entry.kind), vim.log.levels.ERROR)
  end
end

--- Opens the fzf-lua transaction history picker.
function M.pick_transactions()
  require("custom_plugins.security_spread.ui.transactions").pick()
end

--- Opens the fzf-lua watchlist picker.
--- @param slot "left"|"right"|nil dock the chosen watchlist into a half, or fullscreen if nil
function M.pick(slot)
  require("custom_plugins.security_spread.ui.picker").pick(slot)
end

--- Opens the fzf-lua AI-universe group picker (primary/sub buckets, regions).
function M.pick_universe(slot)
  require("custom_plugins.security_spread.ui.universe").pick(slot)
end

--- Lists currently open dashboard session names.
function M.list_open()
  return require("custom_plugins.security_spread.ui.window").list_open()
end

--- fzf-lua picker over currently open sessions — focuses the chosen one.
function M.switch()
  local ok, fzf = pcall(require, "fzf-lua")
  if not ok then
    vim.notify("security_spread: fzf-lua not installed", vim.log.levels.ERROR)
    return
  end
  local window = require("custom_plugins.security_spread.ui.window")
  local open = window.list_open()
  if #open == 0 then
    vim.notify("security_spread: no dashboards open", vim.log.levels.WARN)
    return
  end
  fzf.fzf_exec(open, {
    prompt = "Switch dashboard> ",
    actions = {
      ["default"] = function(selected)
        window.focus(selected[1])
      end,
    },
  })
end

--- Closes one named session, or every open session if `name` is omitted.
function M.close(name)
  require("custom_plugins.security_spread.ui.window").close(name)
end

--- Opens the daily-% portfolio history line chart — a real ratatui TUI
--- binary (portfolio_chart/), run inside a floating :terminal so it's
--- genuinely rendered by the terminal, not an image. It reads DuckDB
--- directly (no JSON handoff) for the day_change_pct/total_value series
--- that sources/etrade.py's cmd_positions upserts on every live `$` refresh.
function M.show_portfolio_history()
  require("custom_plugins.security_spread.ui.portfolio_chart").show()
end

-- Portfolio suite freshness: what is worth re-pulling on open.
local POSITIONS_FRESH_S = 5 * 60
local TRANSACTIONS_FRESH_S = 60 * 60
local CLOSES_FRESH_H = 6
local CLOSES_RANGE = "2y"
local CLOSES_WORKERS = 4
-- Keep in step with Bench::ALL in portfolio_chart/src/screens/portfolio/data.rs.
local BENCH_SYMBOLS = { "SPY", "QQQ", "SOXX" }

local suite_refresh = { running = false, report = nil }

--- Brings everything the portfolio suite reads up to date, in the background:
--- positions + equity snapshot (E*TRADE, if older than 5 min), transactions
--- (if older than 1h), then daily closes for the benchmarks and held symbols
--- (Yahoo, if older than 6h). Each step is skipped while its cache is fresh,
--- so opening the suite repeatedly costs nothing. The TUI only reads DuckDB,
--- so `report` is how it hears about progress.
--- @param report fun(state: "refreshing"|"done"|"error", msg: string, pulled: boolean)
--- @param force boolean|nil ignore the freshness windows
function M.refresh_portfolio(report, force)
  if suite_refresh.running then
    suite_refresh.report = report -- a newly opened suite takes over reporting
    report("refreshing", "refresh in progress", true)
    return
  end
  suite_refresh.running = true
  suite_refresh.report = report
  local function say(state, msg, pulled)
    suite_refresh.report(state, msg, pulled)
  end

  run("sources/etrade.py", { "status" }, function(ok, age)
    age = ok and age or {}
    local need_pos = force or not age.positions_age or age.positions_age > POSITIONS_FRESH_S
    local need_txn = force or not age.transactions_age or age.transactions_age > TRANSACTIONS_FRESH_S
    local pulled = need_pos or need_txn
    local errors = {}

    local function finish()
      suite_refresh.running = false
      if #errors > 0 then
        say("error", "refresh failed: " .. errors[1], pulled)
      else
        say("done", "portfolio updated", pulled)
      end
    end

    local function pull_closes()
      M.positions_cached(function(_, cached)
        local symbols, seen = {}, {}
        for _, s in ipairs(BENCH_SYMBOLS) do
          seen[s] = true
          symbols[#symbols + 1] = s
        end
        for _, p in ipairs(cached or {}) do
          if p.symbol and not seen[p.symbol] and not p.symbol:find("[%s,]") then
            seen[p.symbol] = true
            symbols[#symbols + 1] = p.symbol
          end
        end
        -- A few at a time: every call is a `uv run` that takes the DuckDB
        -- write lock, so a full fan-out just queues on the lock.
        local next_i, active = 1, 0
        local function spawn()
          while active < CLOSES_WORKERS and next_i <= #symbols do
            local sym = symbols[next_i]
            next_i = next_i + 1
            active = active + 1
            run("sources/yahoo.py", {
              "history", sym, "--range", CLOSES_RANGE, "--interval", "1d",
              "--max-age", tostring(CLOSES_FRESH_H),
            }, function(hok, herr)
              active = active - 1
              if not hok then
                errors[#errors + 1] = ("%s closes: %s"):format(sym, vim.trim(tostring(herr)):sub(1, 80))
              end
              if next_i > #symbols and active == 0 then
                finish()
              else
                spawn()
              end
            end)
          end
        end
        if #symbols == 0 then
          finish()
        else
          spawn()
        end
      end)
    end

    local function pull_txns()
      if not need_txn then
        pull_closes()
        return
      end
      say("refreshing", "refreshing transactions…", true)
      M.transactions(function(tok, terr)
        if not tok then
          errors[#errors + 1] = "transactions: " .. vim.trim(tostring(terr)):sub(1, 80)
        end
        pull_closes()
      end)
    end

    if not need_pos then
      pull_txns()
      return
    end
    say("refreshing", "refreshing positions…", true)
    M.positions(function(pok, perr)
      if not pok then
        errors[#errors + 1] = "positions: " .. vim.trim(tostring(perr)):sub(1, 80)
        pull_closes() -- E*TRADE is down or unauthorised: still refresh what we can
        return
      end
      pull_txns()
    end)
  end)
end

--- Opens the portfolio suite TUI (portfolio_chart `portfolio` screen). It
--- paints from DuckDB at once while M.refresh_portfolio updates the cache
--- behind it; progress and completion reach the TUI through a status file
--- (see ui/portfolio_chart.lua show_suite), so it reloads in place.
--- @param range string|nil starting range for the overview
function M.show_portfolio_suite(range)
  require("custom_plugins.security_spread.ui.portfolio_chart").show_suite(range)
end

--- Opens the CANSLIM scorecard TUI for a symbol. Fetches (--force, so a
--- manual open always gets current data and picks up schema changes)
--- and only then opens the TUI, so the screen is populated on first paint
--- — no "press r to reload" round trip. Prompts for a symbol if none given.
--- @param symbol string|nil
function M.show_canslim(symbol)
  local function open(sym)
    vim.notify("security_spread: fetching " .. sym .. " canslim...", vim.log.levels.INFO)
    run("views/canslim.py", { sym, "--force" }, function(ok, data)
      if not ok then
        vim.notify("security_spread: canslim fetch failed: " .. tostring(data), vim.log.levels.ERROR)
        return
      end
      require("custom_plugins.security_spread.ui.portfolio_chart").show_canslim(sym)
    end)
  end

  if symbol and symbol ~= "" then
    open(symbol)
  else
    vim.ui.input({ prompt = "CANSLIM symbol: " }, function(input)
      if input and input ~= "" then
        open(input:upper())
      end
    end)
  end
end

--- Live full-text search over pulled SEC filings / earnings text.
--- @param initial string|nil prefilled query, e.g. "t:MRVL "
function M.pick_search(initial)
  require("custom_plugins.security_spread.ui.search").pick(initial)
end

--- Opens the per-ticker research dossier TUI (portfolio_chart `dossier`
--- screen). Rebuilds views/dossier.py's cache first if it's missing,
--- older than 12h, or older than the data it's built from; otherwise opens
--- instantly. Prompts for a symbol if none given.
--- @param symbol string|nil
function M.show_dossier(symbol)
  local function open(sym)
    sym = sym:upper()
    local chart = require("custom_plugins.security_spread.ui.portfolio_chart")
    run("views/dossier.py", { sym, "--if-stale", "12" }, function(ok, data)
      if not ok then
        -- still open: the screen explains a missing cache itself
        vim.notify("security_spread: dossier build failed: " .. tostring(data), vim.log.levels.ERROR)
      elseif type(data) == "table" and (data.unsourced or 0) > 0 then
        vim.notify(
          ("security_spread: %s dossier has %d unsourced values"):format(sym, data.unsourced),
          vim.log.levels.WARN
        )
      end
      chart.open_screen("dossier", sym, { title = " " .. sym .. " dossier " })
    end)
  end

  if symbol and symbol ~= "" then
    open(symbol)
  else
    vim.ui.input({ prompt = "Dossier symbol: " }, function(input)
      if input and input ~= "" then
        open(input)
      end
    end)
  end
end

--- fzf-lua picker over held symbols (from cached transaction history).
--- Same instant-paint pattern as pick_transactions: uses whatever's
--- cached, no live E*TRADE pull.
--- @param prompt string
--- @param on_pick fun(symbol: string)
local function pick_held(prompt, on_pick)
  local ok, fzf = pcall(require, "fzf-lua")
  if not ok then
    vim.notify("security_spread: fzf-lua not installed", vim.log.levels.ERROR)
    return
  end

  local share_affecting = { Bought = true, Sold = true, ["Stock Split"] = true }

  M.transactions_cached(function(cok, transactions)
    if not cok or not transactions then
      vim.notify("security_spread: no cached transactions — run <leader>st first", vim.log.levels.WARN)
      return
    end
    local seen, symbols = {}, {}
    for _, t in ipairs(transactions) do
      if t.symbol and share_affecting[t.type] and not seen[t.symbol] then
        seen[t.symbol] = true
        symbols[#symbols + 1] = t.symbol
      end
    end
    table.sort(symbols)
    if #symbols == 0 then
      vim.notify("security_spread: no symbols found in cached transactions", vim.log.levels.WARN)
      return
    end

    fzf.fzf_exec(symbols, {
      prompt = prompt,
      actions = {
        ["default"] = function(selected)
          if selected[1] then
            on_pick(selected[1])
          end
        end,
      },
    })
  end)
end

--- Held-symbol picker -> CANSLIM scorecard.
function M.pick_canslim()
  pick_held("CANSLIM> ", M.show_canslim)
end

--- Held-symbol picker -> research dossier.
function M.pick_dossier()
  pick_held("Dossier> ", M.show_dossier)
end

return M
