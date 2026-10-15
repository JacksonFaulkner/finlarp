"""MCP server exposing the pulled SEC dataset to agents (stdio transport).

Same data the nvim UI reads — nothing here fetches from the network, so
every call is local and fast. Tools are all read-only:

    search      BM25 over filing text / new risks / earnings / guidance
    get_chunk   expand a search hit with surrounding text
    company     one-call briefing for a ticker (profile, revenue, segments,
                13F flows, events, insiders, latest guidance, filing metrics)
    financials  stitched XBRL time series (handles predecessor CIKs,
                concept renames, Q4 derivation)
    sql         read-only DuckDB SQL over views of every table (timeout, elapsed_ms, save_as)
    run_python  sandboxed pandas/numpy script over the same views (no network, scratch-only writes)
    describe_data  row counts, symbol counts and date spans per view
    tweets      posts from followed X research accounts, filter by ticker/handle/date, returns coverage
    tweet_sources  which accounts are stored and their date spans
    sentiment   labelled views on one ticker from those tweets: stance, who holds it, trend, keywords, examples
    sentiment_leaders  tickers ranked by mentions / bullish / bearish / contested / momentum
    price_targets  price targets pulled out of tweets, against the last close
    news        company news (ROIC.ai) by ticker/date/text/site, with article snippets
    schema      the views `sql` can see, with columns, bucket counts and query recipes

Register with Claude Code:
    claude mcp add finlarp -- <plugin_dir>/.venv/bin/python <plugin_dir>/mcp_server.py
"""
from __future__ import annotations

import atexit
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from datetime import date, timedelta
from pathlib import Path

import duckdb
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations


from sources import sec_13f, sec_earnings, sec_events, sec_financials, sec_insiders, sec_segments, universe
from sources import roic_news
from sources import tweets as tweets_src
from sources import yahoo_live
from derive import account
from derive import search as fts
from derive import sentiment as sentiment_q
from core.schemas import dictionary

D = universe.DATA_ROOT
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
MAX_CELL = 600

INSTRUCTIONS = """Local SEC dataset for ~428 AI-exposed stocks (universe table), pulled
from EDGAR: XBRL financials (15+ yrs), segment/geography revenue, 13F institutional
holdings (6 quarters, whole market), 8-K event stream, Form 4 insider trades,
10-K/20-F text (business, risk factors, MD&A...), YoY-new risk sentences,
earnings press releases with extracted guidance, Yahoo company profiles, tweets from followed research
accounts (`tweets` tool) with an LLM-labelled stance per ticker (`sentiment`, `sentiment_leaders`,
`price_targets` tools; views tweet_sentiment and tweet_meta), company news snippets (`news` tool), and
~1.5M granted US patents (PatentsView, thru 2025) matched to tickers.

The local snapshot ends at the last completed session. For anything about today, premarket,
after-hours, a move that just happened, or news, use the live Yahoo tools instead of guessing:
  live_quote(ticker)    price, day move, volume vs 20d avg, pre/post-market, 5d/1m trend
  live_history(ticker)  OHLCV bars from Yahoo (any range/interval, incl. 1m and pre/post-market)
  live_news(ticker)     latest headlines (explains moves the filings can't)
Use SEC data for fundamentals and these for what the market is doing right now. Say which source
each number came from.

Suggested flow: `company` for a ticker overview -> `search` for qualitative
questions (then `get_chunk` to read more of a hit) -> `financials` or `sql` for
numbers. Call `schema` before writing SQL.

search query syntax: free text plus filters, e.g.
  t:MRVL,NVDA  s:memory (sector prefix)  i:semiconductors (Yahoo industry)  r:US
  type:guid|earn|new|10k|profile|patent (patents only match with type:patent)
  sec:risk|mda|business  since:2025  "exact phrase"  -exclude
BM25 matches exact terms: if results are thin, rephrase with synonyms or
specific terms (product names, line items) rather than longer sentences.

Caveats: data is a local snapshot (check dates in results). Insider bulk data
lags 0-3 months. 20-F filers have no quarterly XBRL. Some tickers' early
XBRL history belongs to a predecessor business (MTCH=IAC, JCI=Tyco, NBIS=Yandex).
Prices (bars_1d, bars_1m, quotes_1m) are Databento pulls; column is `symbol`, time is `ts_event`
(UTC-aware: convert with AT TIME ZONE 'America/New_York'). Data ends at the last completed session.
Intraday shortcuts, already in ET: bars_1m_et (all hours, adds et_ts/et_date/et_minute), bars_1m_session
(09:30-16:00 only, adds vol_est = volume scaled to consolidated), bars_5m / bars_30m (regular-session
bars with slot_minute/slot_label). universe has primary_bucket / primary_weight columns: GROUP BY
primary_bucket instead of parsing the `primary` JSON. Prefer arg_min/arg_max(col, ts_event) for
first/last-in-window values. Call `describe_data` for coverage; `sql` takes timeout_s and
save_as (writes a parquet under the scratch dir that later queries can read_parquet);
`run_python` runs a pandas/numpy/scipy/statsmodels script when SQL alone is awkward, with an `fl` helper
(fl.bucket_slot_panel / slot_report / alpha_beta / bh / ols / tstat). `data_quality` reports doc coverage,
early-close days (trading_days.is_half_day), data gaps and survivorship: read it before trusting a result.
`schema` includes column_notes harvested from the pydantic models in core/schemas.
Patents: grants only (18mo+ lag vs filing); ticker = current owner incl. acquired
subsidiaries' pre-deal patents. Group by patent_cpc/patent_wipo for tech mix."""

mcp = MCPServer("finlarp", instructions=INSTRUCTIONS)


def _dump(obj) -> str:
    return json.dumps(obj, default=str, separators=(",", ":"))


ET = "America/New_York"
BARS_1M = f"read_parquet('{D}/market/databento/bars_1m/*.parquet', union_by_name=true)"
# Overlapping ingest files leave exact duplicate daily rows (~45%); dedupe here so joins don't fan out, and drop
# the stray pandas index column the parquet files carry.
BARS_1D = (f"(SELECT DISTINCT COLUMNS(c -> c != '__index_level_0__') FROM "
           f"read_parquet('{D}/market/databento/bars_1d/*.parquet', union_by_name=true))")
_ET_TS = f"(ts_event AT TIME ZONE '{ET}')"
BARS_1M_ET = (
    f"(SELECT symbol, ts_event, {_ET_TS} AS et_ts, CAST({_ET_TS} AS DATE) AS et_date, "
    f"CAST(extract(hour FROM {_ET_TS}) * 60 + extract(minute FROM {_ET_TS}) AS INTEGER) AS et_minute, "
    f"open, high, low, close, volume FROM {BARS_1M} "
    f"QUALIFY row_number() OVER (PARTITION BY symbol, ts_event) = 1)"  # ~0.2% exact-duplicate minutes in bars_1m
)
# Regular session only. vol_est scales each minute's Nasdaq-only volume so the day's 04:00-20:00 total
# matches the consolidated bars_1d volume (approximate: assumes bars_1d covers the same hours).
BARS_1M_SESSION = f"""(
  WITH s AS (SELECT * FROM {BARS_1M_ET} WHERE et_minute BETWEEN 570 AND 959),
       tot AS (SELECT symbol, et_date, sum(volume) nasdaq_day_vol FROM {BARS_1M_ET} GROUP BY 1, 2),
       d AS (SELECT symbol, CAST(ts_event AT TIME ZONE 'UTC' AS DATE) AS et_date, volume AS cons_day_vol FROM {BARS_1D})
  SELECT s.*, t.nasdaq_day_vol, d.cons_day_vol,
         CAST(s.volume AS DOUBLE) * d.cons_day_vol / t.nasdaq_day_vol AS vol_est
  FROM s JOIN tot t USING (symbol, et_date) LEFT JOIN d USING (symbol, et_date)
)"""


# One row per ET date with regular-session bars. The closing cross is the day's volume peak: it prints in the
# 16:00 bar on a normal day and the 13:00 bar on an early-close day, so the median peak minute flags half days.
TRADING_DAYS = f"""(
  WITH pk AS (SELECT symbol, et_date, arg_max(et_minute, volume) AS peak FROM {BARS_1M_ET}
              WHERE et_minute BETWEEN 570 AND 1019 GROUP BY 1, 2),
       d AS (SELECT et_date, count(*) AS n_symbols, median(peak) AS median_close_minute FROM pk GROUP BY 1),
       m AS (SELECT median(n_symbols) AS med FROM d)
  SELECT d.et_date, d.n_symbols, d.median_close_minute,
         d.median_close_minute < 900 AS is_half_day, d.n_symbols < 0.8 * m.med AS is_thin_day
  FROM d, m
)"""


DERIVED = D / "market" / "derived"


def _sources_mtime() -> float:
    """Newest mtime across the parquet files the derived views are computed from."""
    files = [f for sub in ("bars_1m", "bars_1d") for f in (D / "market" / "databento" / sub).glob("*.parquet")]
    return max((f.stat().st_mtime for f in files), default=0.0)


def _bars_n(minutes: int) -> str:
    return f"""(
  SELECT symbol, et_date,
         CAST(570 + floor((et_minute - 570) / {minutes}) * {minutes} AS INTEGER) AS slot_minute,
         printf('%02d:%02d', slot_minute // 60, slot_minute % 60) AS slot_label,
         arg_min(open, ts_event) AS open, max(high) AS high, min(low) AS low, arg_max(close, ts_event) AS close,
         sum(volume) AS volume, sum(vol_est) AS vol_est, count(*) AS n_minutes
  FROM {BARS_1M_SESSION} GROUP BY symbol, et_date, slot_minute
)"""


# view name -> (live SQL, ORDER BY). Persisted as parquet under DERIVED, rebuilt when the bars change.
_DERIVED = {
    "trading_days": (TRADING_DAYS, "et_date"),
    "bars_5m": (_bars_n(5), "symbol, et_date, slot_minute"),
    "bars_30m": (_bars_n(30), "symbol, et_date, slot_minute"),
}
_derived_lock = threading.Lock()
_derived_building = False


def _derived_path(name: str) -> Path:
    return DERIVED / f"{name}.parquet"


def _derived_fresh(name: str) -> bool:
    f = _derived_path(name)
    return f.exists() and f.stat().st_mtime >= _sources_mtime()


def _build_derived(name: str) -> None:
    """Compute one derived table from the live SQL on a throwaway connection and swap it in atomically."""
    sql_, order = _DERIVED[name]
    DERIVED.mkdir(parents=True, exist_ok=True)
    out, tmp = _derived_path(name), _derived_path(name).with_suffix(".tmp.parquet")
    c = duckdb.connect()
    try:
        c.execute(f"SET temp_directory='{DERIVED}/.tmp'")
        c.execute(f"COPY (SELECT * FROM {sql_} ORDER BY {order}) TO '{tmp}' (FORMAT PARQUET)")
    finally:
        c.close()
    tmp.replace(out)


def _derived_src(name: str) -> str:
    """FROM-source for a derived view: the parquet when fresh, else the live SQL (always correct, slower)."""
    return f"'{_derived_path(name)}'" if _derived_fresh(name) else _DERIVED[name][0]


def _refresh_derived_async() -> None:
    """Rebuild any stale derived tables in a background thread, then repoint their views at the parquet."""
    global _derived_building
    with _derived_lock:
        if _derived_building or all(_derived_fresh(n) for n in _DERIVED):
            return
        _derived_building = True

    def work():
        global _derived_building
        try:
            for name in _DERIVED:
                if _derived_fresh(name):
                    continue
                try:
                    _build_derived(name)
                    cur = _con.cursor()  # DDL only; the config lock does not block CREATE VIEW
                    cur.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM '{_derived_path(name)}'")
                    cur.close()
                except Exception as e:  # noqa: BLE001 - keep serving from live SQL
                    print(f"derived {name} build failed, staying on live SQL: {e}", file=sys.stderr)
        finally:
            with _derived_lock:
                _derived_building = False

    threading.Thread(target=work, name="derived-build", daemon=True).start()


def _views(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    """name -> description; creates a view per dataset that exists on disk."""
    stocks = universe.stocks()
    rows = []
    for s in stocks:
        prim = s.get("primary") or {}
        bucket = max(prim, key=prim.get) if prim else None
        rows.append({"ticker": s["ticker"], "name": s["name"], "region": s.get("region"), "cik": s["cik"],
                     "primary": json.dumps(prim), "subs": json.dumps(s.get("subs", {})),
                     "primary_bucket": bucket, "primary_weight": float(prim[bucket]) if bucket else None})
    con.execute("CREATE OR REPLACE TABLE universe AS SELECT * FROM (SELECT unnest($r, recursive := true))", {"r": rows})
    specs = {
        "universe": (None, "ticker, name, region, cik, primary/subs = JSON {bucket: weight} AI-exposure buckets; "
                           "primary_bucket / primary_weight = the dominant bucket as plain columns"),
        "facts": (f"read_parquet('{D}/financials/facts/*.parquet', union_by_name=true)",
                  "XBRL facts, one row per (ticker, taxonomy, concept, unit, start, end); prefer the `financials` tool for series"),
        "concepts": (f"'{D}/financials/concepts.parquet'", "XBRL concept labels + how many tickers use each"),
        "segments": (f"read_parquet('{sec_segments.facts_glob()}', union_by_name=true)",
                     "revenue by axis/member from latest 10-K + 10-Q (axis e.g. ProductOrServiceAxis, StatementGeographicalAxis); filter unit"),
        "holdings_13f": (sec_13f.holdings_sql(), "13F long positions per (cik manager, period, cusip); join cusip_map for ticker"),
        "cusip_map": (f"'{sec_13f.DATA_DIR}/cusip_map.parquet'", "ticker -> 13F cusip"),
        "filings": (f"'{D}/events/filings.parquet'", "every EDGAR filing per ticker (form, filed, accn, items...)"),
        "events": (f"'{D}/events/events.parquet'", "8-K/6-K events, one row per item code, with label and signal tier"),
        "insider_tx": (sec_insiders.tx_sql(), "Form 3/4/5 transactions (code P=open-market buy, S=sale; is_10b5_1)"),
        "earnings": (f"read_parquet('{D}/earnings/releases/*.parquet', union_by_name=true)",
                     "earnings press releases (text, guidance VARCHAR[], headline JSON)"),
        "annual_reports": (f"'{D}/filing_text/filings.parquet'",
                           "one row per parsed 10-K/20-F: ai_per_10k_words, patent_count, risk_added/removed, subsidiary_count"),
        "report_sections": (f"'{D}/filing_text/sections.parquet'", "10-K/20-F section text (business, risk_factors, mda, ...)"),
        "risk_diff": (f"'{D}/filing_text/risk_diff.parquet'", "risk-factor sentences added/removed vs prior year (kind, novelty)"),
        "subsidiaries": (f"'{D}/filing_text/subsidiaries.parquet'", "Exhibit 21 subsidiaries + jurisdiction"),
        "profiles": (f"'{D}/profiles/profiles.parquet'",
                     "Yahoo profile per ticker: long_name, sector, industry, country, website, employees, market_cap, summary, officers JSON"),
        "patents": (f"'{D}/patents/patents.parquet'", "granted US patents: patent_id, date (grant), title, type, num_claims, filing_date"),
        "patent_ticker": (f"'{D}/patents/patent_ticker.parquet'", "patent_id -> ticker (co-assigned patents map to several)"),
        "patent_cpc": (f"'{D}/patents/cpc.parquet'", "CPC codes per patent (cpc_sequence 0 = primary; cpc_subclass e.g. H04B, G02B)"),
        "patent_wipo": (f"'{D}/patents/wipo.parquet'", "WIPO technology field per patent (35 fields, e.g. 'Optics', 'Semiconductors')"),
        "patent_inventors": (f"'{D}/patents/inventors.parquet'", "disambiguated inventor_id + name per patent (track people across tickers)"),
        "patent_assignees": (f"'{D}/patents/assignee_map.parquet'", "assignee name -> ticker match audit (kind raw|cluster, via sec_name|ex21|yahoo|manual)"),
        "patent_ai": (f"'{D}/patents/ai.parquet'",
                      "USPTO AI Patent Dataset labels per granted patent (thru 2023-12-26): any_ai (predict50, generous), "
                      "any_ai93 (strict), ml/evo/nlp/speech/vision/planning/kr/hardware bools + <cat>_score"),
        "bars_1d": (BARS_1D,
                    "Databento consolidated daily bars per symbol (open/high/low/close/volume), 2024-07-01+. Volume is the true "
                    "consolidated total. ts_event is midnight UTC of the trade date: use (ts_event AT TIME ZONE 'UTC')::date"),
        "bars_1m": (BARS_1M,
                    "Databento 1-minute bars, 2 years, Nasdaq venues only (volume is ~50-100% of consolidated, median ~79%: use "
                    "bars_1d for volume rules). Includes pre/post-market (04:00-20:00 ET); filter 09:30-16:00 for the regular session. "
                    "Only minutes with trades have a row"),
        "bars_1m_et": (BARS_1M_ET,
                       "bars_1m plus ET columns: et_ts (naive ET timestamp), et_date, et_minute (minutes since midnight ET; "
                       "regular session = 570..959). All hours"),
        "bars_1m_session": (BARS_1M_SESSION,
                            "bars_1m_et restricted to 09:30-16:00 ET, plus nasdaq_day_vol, cons_day_vol (bars_1d) and vol_est "
                            "(minute volume scaled to consolidated; approximate)"),
        "trading_days": (_derived_src("trading_days"),
                         "one row per ET date with bars: n_symbols, median_close_minute (closing-cross volume peak), is_half_day (early close), "
                         "is_thin_day (data-gap suspect). Join on et_date to drop abnormal days"),
        "bars_5m": (_derived_src("bars_5m"), "regular-session 5-minute bars: symbol, et_date, slot_minute, slot_label (HH:MM ET), OHLC, "
                                "volume (Nasdaq-only), vol_est (consolidated-scaled), n_minutes"),
        "bars_30m": (_derived_src("bars_30m"), "regular-session 30-minute bars, same columns as bars_5m"),
        "quotes_1m": (f"read_parquet('{D}/market/databento/quotes_1m/*.parquet', union_by_name=true)",
                      "Databento consolidated best bid/ask sampled per minute (bid_px_00/ask_px_00, sizes), last ~3 months; "
                      "includes pre/post-market quotes, which can be wide"),
        "tweets": (f"'{D}/tweets/tweets.parquet'",
                   "X posts from followed research accounts (handle, created_at UTC, full text, likes/retweets/replies/views, "
                   "is_reply/is_quote/is_retweet); prefer the `tweets` tool for lookups"),
        "tweet_tickers": (f"'{D}/tweets/tweet_tickers.parquet'",
                          "cashtags per tweet (tweet_id -> ticker, in_universe flag); join tweets on tweet_id = tweets.id"),
        "news": (f"'{D}/news/news.parquet'",
                 "company news per ticker (ROIC.ai; free plan covers ~2 years): published_at UTC, title, site, url and text, "
                 "which is a ~200 character snippet, not the full article; one row per (ticker, url). Includes press wires (globenewswire.com)"),
        "short_volume": (f"'{D}/short/short_volume.parquet'",
                         "FINRA Reg SHO daily short sale volume per ticker per day: short_volume, total_volume, short_ratio. "
                         "Flow (includes market-maker hedging; ~45-55% is normal), published the evening of the trade date"),
        "short_interest": (f"'{D}/short/short_interest.parquet'",
                           "short interest per ticker per settlement date (twice a month, public ~7 business days later): "
                           "short_interest, days_to_cover. source nasdaq = ~2y history, yahoo = latest two settlements only"),
        "tweet_sentiment": (f"'{D}/sentiment/tweet_sentiment.parquet'",
                            "LLM labels per (tweet, cashtag): stance -2..+2, focus, whose view (view_holder), claim type, horizon, "
                            "price_target, catalyst, evidence quote, confidence; join tweets on id. Weight by focus and view_holder"),
        "tweet_meta": (f"'{D}/sentiment/tweet_meta.parquet'",
                       "LLM metadata per labelled tweet: tweet_type, themes, keywords, entities named without a cashtag, "
                       "is_repost, is_sarcastic; join tweets on id"),
        "account_fills": (f"'{D}/account/fills.parquet'",
                          "the user's own broker fills (E*TRADE), one row per buy/sell; qty_adj/price_adj are split-adjusted. "
                          "Join to bars_1d on symbol + et_date"),
        "account_round_trips": (f"'{D}/account/round_trips.parquet'",
                                "the user's own FIFO-paired lots: entry/exit, pnl, ret, hold_days; matched=false for sells whose "
                                "buy predates the cache (no entry/pnl)"),
        "account_positions": (f"'{D}/account/positions.parquet'",
                              "the user's open FIFO lots per symbol, reconciled with the broker's positions (broker uses its own "
                              "cost method, so avg_cost can differ from broker_price_paid)"),
        "account_equity_daily": (f"'{D}/account/equity_daily.parquet'",
                                 "the user's portfolio value per calendar day with net deposits, time-weighted day_return, "
                                 "twr_index and drawdown; value history is reconstructed, weekends are carried forward (is_stale)"),
        "account_cash": (f"'{D}/account/cash.parquet'", "the user's deposits, withdrawals, dividends and interest"),
        "patent_ai_by_ticker_year": (f"'{D}/patents/ai_by_ticker_year.parquet'",
                                     "ticker x grant year (<=2023): n_patents, n_ai_any/pct_ai, n_ai93/pct_ai93, n_<cat>; prefer pct_ai93 or n_ml"),
    }
    out = {}
    for name, (src, desc) in specs.items():
        if src is not None:
            try:
                con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM {src}")
            except duckdb.Error:
                continue
        out[name] = desc
    return out


_con: duckdb.DuckDBPyConnection | None = None
_view_desc: dict[str, str] = {}
SCRATCH = D / "scratch"  # inside the allowed data dir, so saved results can be read_parquet()'d back


def _db() -> duckdb.DuckDBPyConnection:
    global _con, _view_desc
    if _con is None:
        con = duckdb.connect()
        if mem := os.environ.get("FINLARP_DUCKDB_MEMORY"):  # e.g. "8GB"
            con.execute(f"SET memory_limit='{mem}'")
        if threads := os.environ.get("FINLARP_DUCKDB_THREADS"):
            con.execute(f"SET threads={int(threads)}")
        SCRATCH.mkdir(parents=True, exist_ok=True)
        account.build_if_stale()  # broker caches -> parquet; the connection below cannot open the broker DB itself
        _view_desc = _views(con)
        # `sql` takes arbitrary SELECTs, and read_text()/read_csv() would
        # otherwise read any file (.env, the E*TRADE token) into the LLM's
        # context. Views resolve lazily, so allow just their data dirs, then
        # lock the config so a query can't turn access back on.
        con.execute(f"SET allowed_directories=['{D}/', '{sec_13f.DATA_DIR}/']")
        con.execute("SET enable_external_access=false")
        con.execute("SET lock_configuration=true")
        _con = con
        _refresh_derived_async()
    return _con


@mcp.tool(annotations=READ_ONLY)
def search(query: str, k: int = 10) -> str:
    """Full-text (BM25) search over 10-K/20-F sections, new-this-year risk
    factor sentences, earnings releases and guidance lines. Supports filters:
    t:TICKERS s:sector r:region type:10k|risk|new|earn|guid sec:section
    since:/until: dates, "exact phrase", -exclude. Returns chunk ids, metadata,
    score and ~220-word text; use get_chunk to read around a hit."""
    rows = fts.search(query, k=min(max(k, 1), 50))
    return _dump({"query": fts.parse(query), "results": rows})


@mcp.tool(annotations=READ_ONLY)
def get_chunk(chunk_id: int, context: int = 1) -> str:
    """A search hit plus `context` neighbouring chunks either side from the
    same document (max 5), with its SEC filing URL."""
    return _dump(fts.get(chunk_id, min(max(context, 0), 5)))


@mcp.tool(annotations=READ_ONLY)
def financials(ticker: str, metric: str = "revenue", period: str = "annual", n: int = 12) -> str:
    """XBRL time series for one ticker, stitched across predecessor CIKs and
    concept renames. metric: revenue, gross_profit, operating_income,
    net_income, eps_diluted, eps_basic, operating_cash_flow, capex, rnd,
    total_assets, equity, cash, long_term_debt, shares_outstanding,
    diluted_shares — or concepts like "us-gaap:InventoryNet". period: annual |
    quarterly (Q4 derived as FY minus 9M, flagged derived=true)."""
    fn = sec_financials.quarterly_series if period.startswith("q") else sec_financials.annual_series
    concepts: str | list[str] = [c.strip() for c in metric.split(",")] if ":" in metric else metric
    rows = fn(ticker.upper(), concepts)
    return _dump(rows[-max(n, 1):])


def _section(fn):
    try:
        return fn()
    except Exception as e:  # one missing dataset shouldn't sink the briefing
        return {"error": f"{type(e).__name__}: {e}"}


@mcp.tool(annotations=READ_ONLY)
def company(ticker: str) -> str:
    """One-call briefing for a ticker: universe profile (AI-exposure buckets),
    last 5 fiscal years + 4 quarters of revenue, latest segment/geography mix,
    13F holder change last quarter, high-signal 8-K events (180 days),
    open-market insider activity (365 days), latest earnings headline and
    guidance, and annual-report metrics (AI mentions, patents, new risks)."""
    t = ticker.upper()
    con = _db()
    year_ago = date.today() - timedelta(days=365)

    def profile():
        r = con.execute("SELECT * FROM universe WHERE ticker = ?", [t]).fetchone()
        if not r:
            return None
        cols = [c[0] for c in con.description]
        d = dict(zip(cols, r))
        d["primary"], d["subs"] = json.loads(d["primary"]), json.loads(d["subs"])
        return d

    def segments():
        rows = con.execute("""
            WITH latest AS (
                SELECT axis, max(period_end) pe FROM segments
                WHERE ticker = ? AND axis <> '' AND period_start IS NOT NULL
                  AND date_diff('day', period_start, period_end) > 300 GROUP BY 1
            )
            SELECT s.axis, s.member, s.period_end, s.value, s.unit FROM segments s JOIN latest l
              ON s.axis = l.axis AND s.period_end = l.pe
            WHERE s.ticker = ? AND date_diff('day', s.period_start, s.period_end) > 300
              AND s.concept NOT ILIKE '%OperatingIncome%'
            QUALIFY row_number() OVER (PARTITION BY s.axis, s.member ORDER BY s.value DESC) = 1
            ORDER BY s.axis, s.value DESC
        """, [t, t]).fetchall()
        out: dict[str, list] = {}
        for axis, member, pe, val, unit in rows:
            out.setdefault(axis, []).append({"member": member, "value": val, "unit": unit, "period_end": pe})
        return {a: m[:8] for a, m in out.items()}

    def insiders():
        tx = sec_insiders.open_market(t, year_ago)
        buys = [x for x in tx if x["code"] == "P"]
        sells = [x for x in tx if x["code"] == "S"]
        disc = [x for x in sells if not x.get("is_10b5_1")]
        return {"buys": len(buys), "buy_value": sum(x["value"] or 0 for x in buys),
                "sales": len(sells), "sale_value": sum(x["value"] or 0 for x in sells),
                "discretionary_sale_value": sum(x["value"] or 0 for x in disc),
                "recent_buys": buys[:5], "note": "bulk data lags 0-3 months"}

    def earnings():
        r = sec_earnings.latest(t)
        if not r:
            return None
        h = r.get("headline")
        return {"filed": r["filed"], "accn": r["accn"], "headline": json.loads(h) if isinstance(h, str) else h,
                "guidance": (r.get("guidance") or [])[:12]}

    def annual_report():
        r = con.execute("""
            SELECT form, filed, fiscal_period_end, ai_mentions, ai_per_10k_words, patent_count,
                   risk_factor_count, risk_added, risk_removed, subsidiary_count
            FROM annual_reports WHERE ticker = ? AND parse_ok ORDER BY filed DESC LIMIT 1
        """, [t]).fetchone()
        return dict(zip([c[0] for c in con.description], r)) if r else None

    return _dump({
        "ticker": t,
        "profile": _section(profile),
        "revenue_annual": _section(lambda: sec_financials.annual_series(t, "revenue")[-5:]),
        "revenue_quarterly": _section(lambda: sec_financials.quarterly_series(t, "revenue")[-4:]),
        "segments_latest_fy": _section(segments),
        "holders_13f": _section(lambda: (sec_13f.summary([t]) or [None])[0]),
        "events_high_180d": _section(lambda: sec_events.recent_events(t, 180, "high")[:15]),
        "insiders_365d": _section(insiders),
        "latest_earnings": _section(earnings),
        "annual_report": _section(annual_report),
    })


LIVE = ToolAnnotations(readOnlyHint=True, openWorldHint=True)


@mcp.tool(annotations=LIVE)
def live_quote(ticker: str) -> str:
    """Live Yahoo snapshot for one ticker: last price (incl. extended hours), day change vs prev
    close, day volume vs 20-session average (relative_volume is understated while the session
    is still open), pre/post-market move and volume, 5d/1m change, 52-week range. Use for any
    question about today."""
    try:
        return _dump(yahoo_live.live(ticker.upper()))
    except Exception as e:  # noqa: BLE001 - tell the model, don't crash the server
        return _dump({"error": f"yahoo live_quote failed: {e}"})


@mcp.tool(annotations=LIVE)
def live_history(ticker: str, range: str = "1mo", interval: str = "1d", pre_post: bool = False) -> str:
    """OHLCV bars from Yahoo, times in ET. range: 1d 5d 1mo 3mo 6mo 1y 2y 5y max. interval: 1m 5m 15m
    30m 60m 1d 1wk 1mo (1m only reaches back ~7 days, intraday ~60 days). pre_post=True includes
    04:00-20:00 ET extended hours. Returns at most 400 bars (the most recent)."""
    try:
        return _dump(yahoo_live.history(ticker.upper(), range, interval, pre_post))
    except Exception as e:  # noqa: BLE001
        return _dump({"error": f"yahoo live_history failed: {e}"})


@mcp.tool(annotations=LIVE)
def live_news(ticker: str, count: int = 8) -> str:
    """Latest Yahoo Finance headlines for a ticker (title, publisher, time ET, link). Use to explain
    a price move or check what the market is reacting to."""
    try:
        return _dump(yahoo_live.news(ticker.upper(), count))
    except Exception as e:  # noqa: BLE001
        return _dump({"error": f"yahoo live_news failed: {e}"})


@mcp.tool(annotations=READ_ONLY)
def tweets(ticker: str = "", handle: str = "", since: str = "", until: str = "", text: str = "",
           min_likes: int = 0, include_replies: bool = False, order: str = "recent", limit: int = 25) -> str:
    """Tweets from the ~20 followed semiconductor/AI research accounts (Sep 2026+).
    Filters: ticker (X cashtag, e.g. MU), handle, since/until (YYYY-MM-DD, UTC; until exclusive), text (substring,
    case-insensitive), min_likes. Replies are excluded unless include_replies; retweets always are.
    order: "recent" or "likes". Cashtags only: a tweet that says "Micron" without $MU won't match `ticker`,
    so also try `text`. Use `sql` over the tweets/tweet_tickers views for aggregates.

    The result's `coverage` says whether the query answered the question: matched vs returned,
    truncated, span and per-account split of the matches, replies excluded, the store's own date
    span, and `notes` with next-step hints. If coverage.truncated or matched is 0, adjust and re-query
    before concluding anything. Absence of tweets only means absence from this store (see tweet_sources)."""
    try:
        res = tweets_src.query(ticker or None, handle or None, since or None, until or None, text or None,
                               min_likes, include_replies, order, limit)
    except (duckdb.Error, OSError) as e:
        return _dump({"error": f"tweets unavailable (run sources/tweets.py ingest): {e}"})
    return _dump(res)


@mcp.tool(annotations=READ_ONLY)
def tweet_sources() -> str:
    """Which X accounts are in the tweet store, with tweet counts and first/last tweet dates.
    Check this to see whether an account is covered at all, and how fresh its data is."""
    try:
        return _dump(tweets_src.sources())
    except (duckdb.Error, OSError) as e:
        return _dump({"error": f"tweets unavailable (run sources/tweets.py ingest): {e}"})


@mcp.tool(annotations=READ_ONLY)
def sentiment(ticker: str, since: str = "", until: str = "", min_agreement: float = 0.0, holder: str = "",
              limit: int = 15) -> str:
    """What the followed X accounts say about one stock, from LLM-labelled tweets (three passes per tweet).
    A *view* is a tweet that is substantively about the stock where someone holds a position; passing mentions and
    bare announcements count as `mentions` only. stance is -2 bearish .. +2 bullish. Returns summary (mentions, views,
    bullish/bearish/neutral, avg_stance, avg_agreement, contested, price targets), by_holder (author vs quoted analyst
    vs quoted person), by_claim, a daily series, top_authors, keywords, themes and `recent` examples with the
    evidence quote and link.

    Filters: since/until (YYYY-MM-DD, UTC; until exclusive), min_agreement (1 = unanimous across passes), holder
    (author | quoted_analyst | quoted_person). The accounts are about 9-in-10 bullish, so compare a ticker with others
    or with earlier weeks, not with zero. `coverage.notes` says what to do next (uncovered ticker, unlabelled tweets,
    heavy disagreement); read it before concluding. Use `sentiment_leaders` to find tickers, `tweets` for raw posts."""
    try:
        return _dump(sentiment_q.ticker(ticker, since or None, until or None, min_agreement, holder, limit))
    except (duckdb.Error, OSError) as e:
        return _dump({"error": f"sentiment unavailable (run sources/tweet_sentiment.py run --all): {e}"})


@mcp.tool(annotations=READ_ONLY)
def sentiment_leaders(by: str = "mentions", since: str = "", until: str = "", min_views: int = 20, holder: str = "",
                      limit: int = 20) -> str:
    """Tickers ranked over the labelled tweets (see `sentiment` for what a view is).
    by: "mentions" (most views), "bullish" (highest average stance), "bearish" (most bearish views), "contested"
    (bulls and bears both present), or "momentum" (views in the last 7 days of the window against the 7 before, with
    the stance in each). min_views drops thin tickers (default 20). holder narrows to author / quoted_analyst /
    quoted_person. Returns rows plus `coverage` (store span, notes). Then call `sentiment` on a row for the detail."""
    try:
        return _dump(sentiment_q.leaders(by, since or None, until or None, min_views, holder, limit))
    except (duckdb.Error, OSError) as e:
        return _dump({"error": f"sentiment unavailable (run sources/tweet_sentiment.py run --all): {e}"})


@mcp.tool(annotations=READ_ONLY)
def price_targets(ticker: str, since: str = "", limit: int = 15) -> str:
    """Price targets that tweets state for one stock, with the median, range and implied upside against the last daily
    close, plus the individual tweets (author, date, target, stance, link). The target is whatever price the labeller found
    for that ticker in the tweet: the horizon is usually unspecified and a comparison price is sometimes picked up by
    mistake, so read the `text` before relying on one. since is YYYY-MM-DD (UTC)."""
    try:
        return _dump(sentiment_q.price_targets(ticker, since or None, limit))
    except (duckdb.Error, OSError) as e:
        return _dump({"error": f"sentiment unavailable (run sources/tweet_sentiment.py run --all): {e}"})


@mcp.tool(annotations=READ_ONLY)
def news(ticker: str = "", since: str = "", until: str = "", text: str = "", site: str = "", limit: int = 20) -> str:
    """Company news pulled from ROIC.ai (about two years back on the free plan), newest first: date, ticker, site,
    title, url and a ~200 character snippet (not the full article). Filters: ticker, since/until (YYYY-MM-DD, UTC;
    until exclusive), text (title or snippet, case-insensitive), site (publisher substring, e.g. globenewswire for
    company press releases, seekingalpha, fool). `coverage` says how much matched, the per-site split and what the store
    holds; a ticker that was never pulled returns nothing. For the latest headlines use live_news."""
    try:
        return _dump(roic_news.query(ticker or None, since or None, until or None, text or None, site or None, limit))
    except (duckdb.Error, OSError) as e:
        return _dump({"error": f"news unavailable (run sources/roic_news.py pull TICKER): {e}"})


@mcp.tool(annotations=READ_ONLY)
def schema() -> str:
    """Views available to the `sql` tool, with columns and a one-line note."""
    con = _db()
    out: dict = {}
    for name, desc in _view_desc.items():
        cols = con.execute(f"DESCRIBE {name}").fetchall()
        out[name] = {"note": desc, "columns": {c[0]: c[1] for c in cols}}
        if notes := dictionary.view_notes(name):
            out[name]["column_notes"] = notes
    out["_buckets"] = dict(con.execute(
        "SELECT primary_bucket, count(*) FROM universe GROUP BY 1 ORDER BY 2 DESC").fetchall())
    out["_recipes"] = [
        "bucket stats: ... FROM x JOIN universe u ON u.ticker = x.symbol GROUP BY u.primary_bucket",
        "intraday: use bars_30m / bars_5m (ET, regular session); slot_label is 'HH:MM' ET; return = close/open - 1",
        "first/last in a window: arg_min(open, ts_event), arg_max(close, ts_event)",
        "ET time from raw bars: ts_event AT TIME ZONE 'America/New_York' (or use bars_1m_et.et_ts)",
        "volume rules: use bars_1d.volume; for intraday shares use vol_est (consolidated-scaled) not raw Nasdaq volume",
        "big result: sql(..., save_as='name') then read_parquet('<scratch>/name.parquet'); path is in the response",
    ]
    return _dump(out)


@mcp.tool(annotations=READ_ONLY)
def data_quality(focus: str = "all") -> str:
    """Guard-rail report on the data itself. focus: all | docs | calendar | bars | universe.
    docs: how many model fields / view columns have descriptions (harvested from the pydantic models
    in core/schemas), columns with no docs, and model fields a view no longer has (drift).
    calendar: trading-day count, early-close days (is_half_day) and thin days (symbol count under 80%
    of normal; likely data gaps). bars: malformed daily/1m bars and symbols with missing days.
    universe: tickers with no price history (and the survivorship caveat). Read this before trusting
    an intraday or cross-sectional result, and drop is_half_day / is_thin_day rows when they matter."""
    con = _db()
    want = {"docs", "calendar", "bars", "universe"} if focus == "all" else {focus}
    out: dict = {}

    def docs():
        cols = {n: [c[0] for c in con.execute(f"DESCRIBE {n}").fetchall()] for n in _view_desc}
        cov = dictionary.coverage(cols)
        views = {}
        for n, c in cov.items():
            if c["model"] is None:
                views[n] = {"model": None, "n_columns": len(cols[n])}
            else:
                views[n] = {"model": c["model"], "undocumented": c["undocumented"][:12],
                            "stale_in_model": c["stale_in_model"]}
        n_doc = sum(len(c.get("documented", [])) for c in cov.values())
        n_all = sum(len(v) for v in cols.values())
        return {"views_with_a_model": sum(1 for c in cov.values() if c["model"]), "views_total": len(cov),
                "columns_documented": n_doc, "columns_total": n_all, "views": views,
                "models": dictionary.sweep_stats()}

    def calendar():
        n, lo, hi = con.execute(
            "SELECT count(*), CAST(min(et_date) AS VARCHAR), CAST(max(et_date) AS VARCHAR) FROM trading_days").fetchone()
        half = con.execute("SELECT CAST(et_date AS VARCHAR) FROM trading_days WHERE is_half_day ORDER BY 1").fetchall()
        thin = con.execute("SELECT CAST(et_date AS VARCHAR), n_symbols FROM trading_days WHERE is_thin_day ORDER BY 1").fetchall()
        return {"days": n, "first": lo, "last": hi, "half_days": [r[0] for r in half],
                "thin_days": [{"date": r[0], "n_symbols": r[1]} for r in thin]}

    def bars():
        bad_1d = con.execute("""SELECT count(*) FILTER (WHERE high < low OR open > high OR open < low OR close > high
                                  OR close < low OR open <= 0 OR close <= 0), count(*) FILTER (WHERE volume = 0), count(*)
                                FROM bars_1d""").fetchone()
        bad_1m = con.execute("""SELECT count(*) FILTER (WHERE high < low OR open > high OR open < low OR close > high
                                  OR close < low OR open <= 0 OR close <= 0), count(*) FROM bars_1m""").fetchone()
        gaps = con.execute("""
            WITH s AS (SELECT symbol, min(CAST(ts_event AT TIME ZONE 'UTC' AS DATE)) first_d,
                              count(*) n FROM bars_1d GROUP BY 1)
            SELECT s.symbol, CAST(s.first_d AS VARCHAR), s.n,
                   (SELECT count(*) FROM trading_days t WHERE t.et_date >= s.first_d) expected
            FROM s ORDER BY 1""").fetchall()
        short = sorted(((sym, f, n, e, round(n / e, 3)) for sym, f, n, e in gaps if e and n / e < 0.9), key=lambda r: r[4])
        return {"bars_1d": {"rows": bad_1d[2], "malformed": bad_1d[0], "zero_volume": bad_1d[1]},
                "bars_1m": {"rows": bad_1m[1], "malformed": bad_1m[0]},
                "symbols_with_gaps_under_90pct": [dict(zip(("symbol", "first_bar", "days", "expected", "coverage"), r))
                                                  for r in short[:20]], "n_symbols_with_gaps": len(short)}

    def uni():
        missing = con.execute("""SELECT ticker FROM universe WHERE ticker NOT IN (SELECT DISTINCT symbol FROM bars_1d)
                                 ORDER BY 1""").fetchall()
        return {"tickers_without_price_history": [r[0] for r in missing][:40], "n_without": len(missing),
                "survivorship": "the universe is today's constituents; history of delisted/removed names is absent, "
                                "so long-run returns here are biased upward"}

    for name, fn in (("docs", docs), ("calendar", calendar), ("bars", bars), ("universe", uni)):
        if name in want:
            out[name] = _section(fn)
    return _dump(out)


# (symbol-ish column, time column) per view, for describe_data
_COVERAGE = {
    "bars_1d": ("symbol", "ts_event"), "bars_1m": ("symbol", "ts_event"), "quotes_1m": ("symbol", "ts_event"),
    "tweets": ("handle", "created_at"), "events": ("ticker", "filed"), "filings": ("ticker", "filed"),
    "insider_tx": ("ticker", "filed"), "earnings": ("ticker", "filed"), "holdings_13f": ("mgr", "period"),
    "facts": ("ticker", "filed"), "annual_reports": ("ticker", "filed"),
}


@mcp.tool(annotations=READ_ONLY)
def describe_data() -> str:
    """Coverage per dataset: row count, distinct symbols/tickers/handles, and first/last date. Check
    this before analysis to see how much history exists and where the snapshot ends."""
    con = _db()
    out = {}
    for name, (who, when) in _COVERAGE.items():
        if name not in _view_desc:
            continue
        try:
            n, k, lo, hi = con.execute(
                f"SELECT count(*), count(DISTINCT {who}), CAST(min({when}) AS VARCHAR), CAST(max({when}) AS VARCHAR) "
                f"FROM {name}").fetchone()
            out[name] = {"rows": n, "distinct": k, "distinct_of": who, "first": lo, "last": hi}
        except Exception as e:  # noqa: BLE001 - one bad view shouldn't hide the rest
            out[name] = {"error": f"{type(e).__name__}: {e}"}
    out["universe"] = {"rows": con.execute("SELECT count(*) FROM universe").fetchone()[0]}
    return _dump(out)


_SQL_CACHE: dict = {}  # insertion-ordered LRU: key -> response dict
_SQL_CACHE_MAX = 64
_SQL_CACHE_MIN_MS = 500


def _data_fingerprint() -> tuple:
    """Cheap change detector: newest mtime + entry count over D, its dataset dirs, their
    subdirs (partitions), and SCRATCH. A dir's mtime moves when files are added/removed."""
    newest, count = 0, 0
    for root in (D, SCRATCH):
        try:
            with os.scandir(root) as it:
                entries = list(it)
        except OSError:
            continue
        for e in entries:
            try:
                newest = max(newest, e.stat().st_mtime_ns)
                count += 1
                if e.is_dir(follow_symlinks=False):
                    with os.scandir(e.path) as it2:
                        for e2 in it2:
                            newest = max(newest, e2.stat().st_mtime_ns)
                            count += 1
            except OSError:
                continue
    return (newest, count)


@mcp.tool(annotations=READ_ONLY)
def sql(query: str, max_rows: int = 100, timeout_s: int = 120, save_as: str = "", fresh: bool = False) -> str:
    """Run one read-only DuckDB SELECT over the dataset views (see `schema`).
    Only SELECT statements are accepted. Long text cells are truncated to
    600 chars; at most max_rows (<=1000) rows are returned. Queries are cancelled after
    timeout_s (default 120, max 900): narrow the date range / tickers or aggregate earlier.
    save_as="name" writes the FULL result to <scratch>/name.parquet and returns its path with a
    20-row preview instead of the rows, so big tables stay out of context; read it back with
    read_parquet(path) in a later query or run_python.
    Results of slow (>500 ms) queries are cached in-process and auto-invalidated when the data
    files change; a cache hit returns "cached": true (elapsed_ms near 0, original_elapsed_ms is
    the real run time). Pass fresh=True to bypass the cache. save_as calls are never cached."""
    key = None
    if not save_as:
        key = (" ".join(query.split()), min(max(max_rows, 1), 1000), _data_fingerprint())
        hit = None if fresh else _SQL_CACHE.get(key)
        if hit is not None:
            _SQL_CACHE[key] = _SQL_CACHE.pop(key)  # LRU bump
            return _dump({**hit, "cached": True, "original_elapsed_ms": hit["elapsed_ms"], "elapsed_ms": 0})
    con = _db()
    try:
        stmts = con.extract_statements(query)
    except duckdb.Error as e:
        return _dump({"error": str(e)})
    if len(stmts) != 1 or stmts[0].type != duckdb.StatementType.SELECT:
        return _dump({"error": "only a single SELECT statement is allowed"})
    if save_as and not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", save_as):
        return _dump({"error": "save_as must be 1-64 chars of letters, digits, _ or -"})
    limit = 20 if save_as else min(max(max_rows, 1), 1000)
    timeout_s = min(max(timeout_s, 1), 900)
    timed_out = threading.Event()
    timer = threading.Timer(timeout_s, lambda: (timed_out.set(), con.interrupt()))
    t0 = time.perf_counter()
    timer.start()
    try:
        cur = con.execute(query)
        cols = [c[0] for c in cur.description]
        saved = None
        if save_as:
            df = cur.fetchdf()
            saved = SCRATCH / f"{save_as}.parquet"
            tmp = duckdb.connect()
            tmp.register("df", df)
            tmp.execute(f"COPY df TO '{saved}' (FORMAT PARQUET)")
            tmp.close()
            total = len(df)
            rows = df.head(limit).itertuples(index=False, name=None)
            rows = list(rows)
        else:
            rows = cur.fetchmany(limit + 1)
            total = None
    except Exception as e:  # noqa: BLE001 - surface every failure, not just duckdb.Error
        if timed_out.is_set():
            return _dump({"error": f"timed out after {timeout_s}s; narrow the date range/tickers, aggregate earlier, "
                                   "or raise timeout_s (max 900)"})
        return _dump({"error": f"{type(e).__name__}: {e}"})
    finally:
        timer.cancel()
    truncated = total is None and len(rows) > limit
    rows = rows[:limit]
    trunc = lambda v: v[:MAX_CELL] + "…" if isinstance(v, str) and len(v) > MAX_CELL else v
    res = {"columns": cols, "rows": [[trunc(v) for v in r] for r in rows], "row_count": len(rows),
           "elapsed_ms": round((time.perf_counter() - t0) * 1000)}
    if truncated:
        res["truncated"] = True
    if saved is not None:
        res.update({"saved_to": str(saved), "total_rows": total, "preview": True})
    if key is not None and res["elapsed_ms"] > _SQL_CACHE_MIN_MS:
        _SQL_CACHE[key] = res
        while len(_SQL_CACHE) > _SQL_CACHE_MAX:
            _SQL_CACHE.pop(next(iter(_SQL_CACHE)))
    return _dump(res)


# --- run_python -------------------------------------------------------------------------------
# Arbitrary Python can read files the `sql` tool deliberately can't (.env, the E*TRADE token), so
# the child runs under macOS sandbox-exec: no network, writes only to the scratch dir, and reads
# of known secret locations denied. Environment is scrubbed. No sandbox-exec -> tool refuses unless
# FINLARP_ALLOW_UNSANDBOXED_PYTHON=1.
_REPO = Path(__file__).resolve().parents[2]
_HOME = Path.home()
_PY_OUT_MAX = 20_000
_PRELUDE = '''\
import json
import duckdb
import numpy as np
import pandas as pd
from agent import fl
con = duckdb.connect()
con.execute("SET memory_limit='{mem_gb:.1f}GB'")  # stay under the watchdog so DuckDB spills instead of being killed
con.execute("SET temp_directory='{tmp_dir}'")
for _stmt in json.load(open({defs!r})):
    con.execute(_stmt)
con.execute("SET allowed_directories=" + json.dumps({allowed!r}).replace('"', "'"))
con.execute("SET enable_external_access=false")
con.execute("SET lock_configuration=true")
SCRATCH = {scratch!r}
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 200)
'''


def _sandbox_profile(run_dir: Path) -> str:
    denied = [_REPO / ".env", _HOME / ".local/share/nvim/etrade_token.json",
              _HOME / ".ssh", _HOME / ".aws", _HOME / ".gnupg", _HOME / ".config", _HOME / ".claude"]
    lines = ["(version 1)", "(allow default)", "(deny network*)", "(deny file-write*)",
             f'(allow file-write* (subpath "{SCRATCH}") (subpath "/dev") (subpath "{run_dir}"))']
    lines += [f'(deny file-read* (subpath "{p}"))' for p in denied]
    return "\n".join(lines)


_SESSION_LOOP = '''
import io, json, os, sys, traceback
_proto = os.fdopen(os.dup(1), "w", buffering=1)
_cmds = os.fdopen(os.dup(0), "r")
os.dup2(2, 1)
sys.stdin = open(os.devnull)
_CAP = {cap}
class _Cap(io.TextIOBase):
    def __init__(self):
        self.parts, self.n = [], 0
    def write(self, s):
        self.parts.append(s); self.n += len(s)
        while self.n > 2 * _CAP and len(self.parts) > 1:
            self.n -= len(self.parts.pop(0))
        return len(s)
    def text(self):
        return "".join(self.parts)[-_CAP:]
_g = globals()
for _line in _cmds:
    _req = json.loads(_line)
    _o, _e = _Cap(), _Cap()
    _so, _se = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = _o, _e
    _rc = 0
    try:
        exec(compile(_req["code"], "<session>", "exec"), _g)
    except SystemExit:
        pass
    except BaseException:
        _rc = 1
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = _so, _se
    _proto.write(json.dumps({{"id": _req["id"], "rc": _rc, "out": _o.text(), "err": _e.text()}}) + "\\n")
'''

_AUDIT_MAX = 5_000_000
_RUN_KEEP_S = 7 * 86400
_MAX_SESSIONS = 3
_SESSION_IDLE_S = 30 * 60
_SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
_CAPTURE_MAX = 400_000  # chars kept per stream while draining a child
_sessions: dict[str, "_Session"] = {}
_sessions_lock = threading.Lock()


def _mem_limit_gb() -> float:
    try:
        return float(os.environ.get("FINLARP_PY_MEMORY_GB", "8"))
    except ValueError:
        return 8.0


def _rss_gb(pid: int) -> float:
    try:
        import psutil  # type: ignore
        return psutil.Process(pid).memory_info().rss / 2**30
    except ImportError:
        pass
    except Exception:
        return 0.0
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True, timeout=5).stdout
        return int(out.strip() or 0) / 2**20
    except Exception:
        return 0.0


class _Watchdog(threading.Thread):
    """Polls child RSS; kills it above the limit and sets .tripped."""

    def __init__(self, proc: subprocess.Popen):
        super().__init__(daemon=True)
        self.proc, self.limit, self.tripped, self.peak = proc, _mem_limit_gb(), False, 0.0
        self._halt = threading.Event()

    def run(self):
        while not self._halt.wait(0.25):
            if self.proc.poll() is not None:
                return
            rss = _rss_gb(self.proc.pid)
            self.peak = max(self.peak, rss)
            if rss > self.limit:
                self.tripped = True
                self.proc.kill()
                return

    def stop(self):
        self._halt.set()


class _Tail(threading.Thread):
    """Drains a stream, keeping only the last _CAPTURE_MAX chars (never unbounded memory)."""

    def __init__(self, stream):
        super().__init__(daemon=True)
        self.stream, self.buf, self.total = stream, "", 0

    def run(self):
        try:
            for chunk in iter(lambda: self.stream.read(8192), ""):
                self.total += len(chunk)
                self.buf = (self.buf + chunk)[-_CAPTURE_MAX:]
        except Exception:
            pass


def _preexec(cpu_s: int):
    def fn():
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s + 2))
        os.setsid()
    return fn


def _spawn(cmd, run_dir: Path, env: dict, cpu_s: int, stdin: bool = False) -> subprocess.Popen:
    return subprocess.Popen(cmd, cwd=run_dir, env=env, text=True, errors="replace", bufsize=1,
                            stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=_preexec(cpu_s))


def _kill(p: subprocess.Popen):
    try:
        os.killpg(p.pid, 9)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass
    try:
        p.wait(timeout=5)
    except Exception:
        pass


def _housekeeping(run_root: Path):
    cutoff = time.time() - _RUN_KEEP_S
    live = {s.run_dir for s in _sessions.values()}
    try:
        for d in run_root.iterdir():
            if d.is_dir() and not d.is_symlink() and d not in live and d.stat().st_mtime < cutoff:
                shutil.rmtree(d, ignore_errors=True)
    except OSError:
        pass


def _audit(code: str, session: str, rc, elapsed_ms: int):
    import hashlib
    path = SCRATCH / "run_audit.log"
    try:
        if path.exists() and path.stat().st_size > _AUDIT_MAX:
            path.replace(path.with_suffix(".log.1"))
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "sha256": hashlib.sha256(code.encode()).hexdigest(),
               "session": session, "returncode": rc, "elapsed_ms": elapsed_ms}
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        pass


class _Session:
    def __init__(self, name: str, cmd, run_dir: Path, env: dict):
        self.name, self.run_dir = name, run_dir
        self.proc = _spawn(cmd, run_dir, env, 4 * 3600, stdin=True)
        self.wd = _Watchdog(self.proc)
        self.wd.start()
        self.err = _Tail(self.proc.stderr)
        self.err.start()
        self.lines: "queue.Queue[str]" = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()
        self.lock = threading.Lock()
        self.last = time.time()
        self.seq = 0

    def _pump(self):
        try:
            for ln in self.proc.stdout:
                self.lines.put(ln)
        finally:
            self.lines.put("")  # EOF sentinel

    def call(self, code: str, timeout_s: int):
        """Returns (rc, text, error)."""
        self.seq += 1
        self.last = time.time()
        mark = self.err.total
        try:
            self.proc.stdin.write(json.dumps({"id": self.seq, "code": code}) + "\n")
            self.proc.stdin.flush()
        except OSError:
            return -1, "", "session process died"
        deadline = time.time() + timeout_s
        while True:
            try:
                ln = self.lines.get(timeout=max(0.05, min(0.5, deadline - time.time())))
            except queue.Empty:
                if time.time() >= deadline:
                    return -1, "", f"timed out after {timeout_s}s; session killed and discarded"
                continue
            self.last = time.time()
            if ln == "":
                if self.wd.tripped:
                    return -1, "", f"memory limit {self.wd.limit:g} GB exceeded (peak {self.wd.peak:.1f} GB); session killed"
                return -1, "", f"session process died (rc={self.proc.poll()}); " + self.err.buf[-2000:]
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("id") != self.seq:
                continue
            text = r["out"] + (("\n--- stderr ---\n" + r["err"]) if r["err"].strip() else "")
            if self.err.total > mark and self.err.buf.strip():
                text += "\n--- process stderr ---\n" + self.err.buf[-2000:]
            return r["rc"], text, None

    def close(self):
        self.wd.stop()
        _kill(self.proc)


def _drop_session(name: str):
    with _sessions_lock:
        s = _sessions.pop(name, None)
    if s:
        s.close()


def _close_all_sessions():
    for n in list(_sessions):
        _drop_session(n)


atexit.register(_close_all_sessions)


def _prepare_run(run_dir: Path, code: str | None) -> Path:
    # The child can't import this package (it loads .env, which the sandbox hides), so hand it the
    # view definitions and a copy of the universe table instead.
    defs = [r[0] for r in _db().execute("SELECT sql FROM duckdb_views() WHERE NOT internal").fetchall()]
    defs_file = run_dir / "views.json"
    defs_file.write_text(json.dumps(["CREATE VIEW universe AS SELECT * FROM read_parquet('%s/universe.parquet')" % run_dir]
                                    + [d for d in defs if not d.startswith("CREATE VIEW universe ")]))
    tmp = duckdb.connect()
    tmp.register("u", _db().execute("SELECT * FROM universe").fetchdf())
    tmp.execute(f"COPY u TO '{run_dir}/universe.parquet' (FORMAT PARQUET)")
    tmp.close()
    script = run_dir / "script.py"
    pre = _PRELUDE.format(defs=str(defs_file), scratch=str(SCRATCH),
                          allowed=[f"{D}/", f"{sec_13f.DATA_DIR}/", f"{run_dir}/"],
                          mem_gb=max(0.5, _mem_limit_gb() * 0.7), tmp_dir=f"{run_dir}/duck_tmp")
    if code is None:
        script.write_text(pre + "\n" + _SESSION_LOOP.format(cap=_PY_OUT_MAX) + "\n")
    else:
        script.write_text(pre + "\n" + code + "\n")
    return script


def _list_files(started: float) -> list[str]:
    skip = {"script.py", "views.json", "universe.parquet", "run_audit.log", "run_audit.log.1"}
    return sorted(str(f) for f in SCRATCH.rglob("*") if f.is_file() and f.name not in skip and f.stat().st_mtime >= started)[:50]


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def run_python(code: str, timeout_s: int = 300, session: str = "", reset_session: bool = False) -> str:
    """Run a Python script (pandas as pd, numpy as np, `con` = the same DuckDB connection and views `sql`
    uses, `fl` helpers, `SCRATCH` = writable dir path) for analysis that is awkward in pure SQL: statistics,
    t-tests, reshaping, multi-step pipelines. Print what you want back (stdout+stderr returned, last 20k chars).
    Sandboxed: no network, writes only under SCRATCH, no access to .env or broker tokens. Files written
    under SCRATCH are listed in the result (parquet there can be queried with read_parquet).
    timeout_s default 300, max 1800 (per call; CPU limit is a few seconds above it).
    Caps: child killed if RSS exceeds 8 GB (env FINLARP_PY_MEMORY_GB); output beyond the last 20k chars dropped.
    session: a name ([A-Za-z0-9_-]{1,32}) keeps one long-lived process so variables/dataframes persist
    between calls (max 3 sessions, LRU evicted, 30 min idle expiry; a timeout or kill discards the session).
    reset_session=true drops that session first (code may be empty to just drop it).
    Each call is logged (time, sha256 of code, session, returncode, ms) to SCRATCH/run_audit.log."""
    _db()  # make sure scratch exists and the views build
    sandbox = shutil.which("sandbox-exec")
    if not sandbox and os.environ.get("FINLARP_ALLOW_UNSANDBOXED_PYTHON") != "1":
        return _dump({"error": "run_python needs macOS sandbox-exec (not found); set "
                               "FINLARP_ALLOW_UNSANDBOXED_PYTHON=1 to run unsandboxed"})
    if session and not _SESSION_RE.match(session):
        return _dump({"error": "session must match [A-Za-z0-9_-]{1,32}"})
    if reset_session and session:
        _drop_session(session)
        if not code.strip():
            return _dump({"returncode": 0, "output": f"session {session!r} dropped", "files": []})
    timeout_s = min(max(timeout_s, 1), 1800)
    run_root = SCRATCH / "run"
    run_root.mkdir(parents=True, exist_ok=True)
    _housekeeping(run_root)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}
    started = time.time()
    t0 = time.perf_counter()

    def done(rc, text, **extra):
        ms = round((time.perf_counter() - t0) * 1000)
        _audit(code, session, rc, ms)
        return _dump({"returncode": rc, "output": text[-_PY_OUT_MAX:], "files": _list_files(started),
                      "elapsed_ms": ms, **extra})

    if session:
        now = time.time()
        with _sessions_lock:
            for n, s in list(_sessions.items()):
                if now - s.last > _SESSION_IDLE_S or s.proc.poll() is not None:
                    _sessions.pop(n)
                    threading.Thread(target=s.close, daemon=True).start()
            s = _sessions.get(session)
            if s is None:
                while len(_sessions) >= _MAX_SESSIONS:
                    lru = min(_sessions, key=lambda k: _sessions[k].last)
                    threading.Thread(target=_sessions.pop(lru).close, daemon=True).start()
                run_dir = run_root / uuid.uuid4().hex[:12]
                run_dir.mkdir(parents=True)
                script = _prepare_run(run_dir, None)
                cmd = [sys.executable, "-I", str(script)]
                if sandbox:
                    cmd = [sandbox, "-p", _sandbox_profile(run_dir)] + cmd
                s = _sessions[session] = _Session(session, cmd, run_dir, {**env, "HOME": str(run_dir), "TMPDIR": str(run_dir)})
        with s.lock:
            rc, text, err = s.call(code, timeout_s)
        if err:
            if _sessions.get(session) is s:
                _drop_session(session)
            return done(rc, err + ("\n" + text if text else ""), session=session)
        return done(rc, text, session=session)

    run_dir = run_root / uuid.uuid4().hex[:12]
    run_dir.mkdir(parents=True)
    script = _prepare_run(run_dir, code)
    cmd = [sys.executable, "-I", str(script)]
    if sandbox:
        cmd = [sandbox, "-p", _sandbox_profile(run_dir)] + cmd
    cpu_s = timeout_s + 5
    p = _spawn(cmd, run_dir, {**env, "HOME": str(run_dir), "TMPDIR": str(run_dir)}, cpu_s)
    wd, so, se = _Watchdog(p), _Tail(p.stdout), _Tail(p.stderr)
    wd.start(); so.start(); se.start()
    timed_out = False
    try:
        p.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill(p)
    wd.stop()
    so.join(5); se.join(5)
    rc = p.returncode
    text = so.buf + (("\n--- stderr ---\n" + se.buf) if se.buf.strip() else "")
    if wd.tripped:
        text = f"killed: memory limit {wd.limit:g} GB exceeded (peak {wd.peak:.1f} GB)\n" + text[-_PY_OUT_MAX:]
    elif timed_out:
        text = f"timed out after {timeout_s}s\n" + text[-_PY_OUT_MAX:]
    elif rc == -24:
        text = f"killed: CPU time limit ({cpu_s}s) exceeded\n" + text[-_PY_OUT_MAX:]
    if so.total + se.total > _PY_OUT_MAX:
        return done(rc, text, truncated=f"{so.total + se.total} chars produced, last {_PY_OUT_MAX} kept")
    return done(rc, text)


if __name__ == "__main__":
    if "--build-derived" in sys.argv:  # prebuild trading_days / bars_5m / bars_30m so the first start is fast
        for _name in _DERIVED:
            if "--force" in sys.argv or not _derived_fresh(_name):
                _t0 = time.perf_counter()
                _build_derived(_name)
                print(f"built {_name} in {time.perf_counter() - _t0:.1f}s -> {_derived_path(_name)}", file=sys.stderr)
    else:
        mcp.run("stdio")
