"""Local DuckDB cache for historical price data.

Keeps a small on-disk store at ~/.local/share/nvim/security_spread.duckdb so
repeat chart opens (same symbol/range/interval within TTL) skip the network
round-trip entirely, and gives the plugin a real place to grow into (joins,
backtests, screener snapshots) instead of everything being fetch-and-discard.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path

import duckdb

DB_PATH = Path(os.path.expanduser("~/.local/share/nvim/security_spread.duckdb"))

# History doesn't change intraday for the bar we already have except the
# still-forming last bar, so a modest TTL is safe and saves a network round
# trip on every chart re-open for the same symbol/range within the window.
DEFAULT_TTL_SECONDS = 15 * 60


_SCHEMA = [
    """
        CREATE TABLE IF NOT EXISTS history_cache (
            symbol VARCHAR,
            range VARCHAR,
            interval VARCHAR,
            points_json VARCHAR,
            fetched_at DOUBLE,
            PRIMARY KEY (symbol, range, interval)
        )
    """,
    """
        CREATE TABLE IF NOT EXISTS transactions_cache (
            account VARCHAR PRIMARY KEY,
            transactions_json VARCHAR,
            fetched_at DOUBLE
        )
    """,
    """
        CREATE TABLE IF NOT EXISTS positions_cache (
            id INTEGER PRIMARY KEY,
            positions_json VARCHAR,
            fetched_at DOUBLE
        )
    """,
    """
        CREATE TABLE IF NOT EXISTS portfolio_history (
            date DATE PRIMARY KEY,
            total_value DOUBLE,
            day_change_pct DOUBLE
        )
    """,
    """
        CREATE TABLE IF NOT EXISTS canslim_cache (
            symbol VARCHAR PRIMARY KEY,
            scorecard_json VARCHAR,
            fetched_at DOUBLE
        )
    """,
    # Per-ticker research dossier (views/dossier.py) read straight out of
    # DuckDB by the portfolio_chart `dossier` screen, same as canslim_cache.
    """
        CREATE TABLE IF NOT EXISTS dossier_cache (
            symbol VARCHAR PRIMARY KEY,
            dossier_json VARCHAR,
            fetched_at DOUBLE
        )
    """,
    """
        CREATE TABLE IF NOT EXISTS edgar_facts_cache (
            symbol VARCHAR PRIMARY KEY,
            facts_json VARCHAR,
            fetched_at DOUBLE
        )
    """,
    # SEC Financial Statement Data Sets — one bulk zip per calendar quarter
    # covering every filer. Only dimensional (segment) revenue rows are kept;
    # undimensioned totals already come from companyfacts. See
    # sources/edgar_fsds.py.
    """
        CREATE TABLE IF NOT EXISTS edgar_fsds_loaded (
            quarter VARCHAR PRIMARY KEY,   -- e.g. '2026q2'
            loaded_at DOUBLE,
            row_count INTEGER
        )
    """,
    """
        CREATE TABLE IF NOT EXISTS edgar_segment_revenue (
            adsh VARCHAR,
            cik INTEGER,
            form VARCHAR,
            fy INTEGER,
            fp VARCHAR,
            filed DATE,
            tag VARCHAR,
            ddate DATE,
            qtrs INTEGER,
            axis VARCHAR,       -- 'ProductOrService', 'BusinessSegments', ... or '' for the total
            member VARCHAR,     -- 'DRAMProducts', ... or '' for the total
            value DOUBLE,
            PRIMARY KEY (adsh, tag, ddate, qtrs, axis, member)
        )
    """,
    """
        CREATE TABLE IF NOT EXISTS edgar_cik_map_cache (
            id INTEGER PRIMARY KEY,
            map_json VARCHAR,
            fetched_at DOUBLE
        )
    """,
]
_TABLES = {re.search(r"EXISTS (\w+)", s)[1] for s in _SCHEMA}


def _finite(v):
    if isinstance(v, float) and not math.isfinite(v):
        return None
    if isinstance(v, dict):
        return {k: _finite(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_finite(x) for x in v]
    return v


def _dumps(obj) -> str:
    """JSON for the caches the Rust screens parse: NaN/Infinity (from parquet
    or a 0/0 ratio) become null, since serde_json rejects the whole doc."""
    return json.dumps(_finite(obj), default=str, allow_nan=False)


def _open(read_only: bool) -> duckdb.DuckDBPyConnection:
    """DuckDB allows one read-write process *or* many readers per file, and
    nvim fires several of these scripts at once (cached + live positions,
    canslim, dossier) while the Rust screens read. Opens are short, so a
    lock conflict just means waiting a moment: retry for ~5s."""
    for attempt in range(25):
        try:
            return duckdb.connect(str(DB_PATH), read_only=read_only)
        except duckdb.IOException as e:
            if "lock" not in str(e).lower() or attempt == 24:
                raise
            time.sleep(0.05 * (attempt + 1))
    raise AssertionError("unreachable")


def _conn(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Connection with the schema in place. read_only=True for pure reads so
    they can run alongside other readers; the schema is only (re)created,
    read-write, when a table is missing (fresh DB or a new table)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        con = _open(read_only)
        have = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
        if _TABLES <= have:
            return con
        con.close()
    con = _open(False)
    for stmt in _SCHEMA:
        con.execute(stmt)
    if read_only:
        con.close()
        con = _open(True)
    return con


# Positions are read two ways: an instant local read (no TTL check — any
# age is better than blocking on the network) to paint the dashboard
# immediately, and a background live pull that overwrites this cache once
# E*TRADE responds. There's no expiry here on purpose.
def get_cached_positions() -> list[dict] | None:
    con = _conn(read_only=True)
    try:
        row = con.execute("SELECT positions_json FROM positions_cache WHERE id = 0").fetchone()
    finally:
        con.close()
    if row is None:
        return None
    return json.loads(row[0])


def put_cached_positions(positions: list[dict]) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO positions_cache VALUES (0, ?, ?) "
            "ON CONFLICT (id) DO UPDATE SET "
            "positions_json = excluded.positions_json, fetched_at = excluded.fetched_at",
            [json.dumps(positions), time.time()],
        )
    finally:
        con.close()


# Transaction history is finalized once settled — a longer TTL than price
# history is fine, and it keeps the fzf picker snappy (no network round trip
# on every open) while still refreshing periodically for newly settled trades.
TRANSACTIONS_TTL_SECONDS = 60 * 60


def get_cached_transactions(account: str, ttl_seconds: float = TRANSACTIONS_TTL_SECONDS) -> list[dict] | None:
    con = _conn(read_only=True)
    try:
        row = con.execute(
            "SELECT transactions_json, fetched_at FROM transactions_cache WHERE account = ?",
            [account],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return None
    transactions_json, fetched_at = row
    if time.time() - fetched_at > ttl_seconds:
        return None
    return json.loads(transactions_json)


def get_all_cached_transactions() -> list[dict]:
    """Local-only read across every account's cache, ignoring TTL — any
    staleness is fine here since it's only used to paint the picker
    instantly while a live refresh runs in the background."""
    con = _conn(read_only=True)
    try:
        rows = con.execute("SELECT transactions_json FROM transactions_cache").fetchall()
    finally:
        con.close()
    result = []
    for (transactions_json,) in rows:
        result.extend(json.loads(transactions_json))
    return result


def put_cached_transactions(account: str, transactions: list[dict]) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO transactions_cache VALUES (?, ?, ?) "
            "ON CONFLICT (account) DO UPDATE SET "
            "transactions_json = excluded.transactions_json, fetched_at = excluded.fetched_at",
            [account, json.dumps(transactions), time.time()],
        )
    finally:
        con.close()


# One row per calendar day — upserted every time cmd_positions runs live,
# so today's row just keeps getting overwritten with the latest numbers
# until market close, no separate cron/snapshot job needed. Also used
# (with an explicit date) by backfill_history.py to seed prior days from
# transaction history + Yahoo daily closes.
def upsert_portfolio_snapshot(total_value: float, day_change_pct: float, date: str | None = None) -> None:
    con = _conn()
    try:
        if date is None:
            con.execute(
                "INSERT INTO portfolio_history VALUES (CURRENT_DATE, ?, ?) "
                "ON CONFLICT (date) DO UPDATE SET "
                "total_value = excluded.total_value, day_change_pct = excluded.day_change_pct",
                [total_value, day_change_pct],
            )
        else:
            con.execute(
                "INSERT INTO portfolio_history VALUES (?, ?, ?) "
                "ON CONFLICT (date) DO UPDATE SET "
                "total_value = excluded.total_value, day_change_pct = excluded.day_change_pct",
                [date, total_value, day_change_pct],
            )
    finally:
        con.close()


def get_portfolio_history() -> list[dict]:
    con = _conn(read_only=True)
    try:
        rows = con.execute(
            "SELECT date, total_value, day_change_pct FROM portfolio_history ORDER BY date"
        ).fetchall()
    finally:
        con.close()
    return [
        {"date": str(d), "total_value": v, "day_change_pct": p}
        for d, v, p in rows
    ]


def get_cached_history(
    symbol: str, range_: str, interval: str, ttl_seconds: float = DEFAULT_TTL_SECONDS
) -> list[dict] | None:
    con = _conn(read_only=True)
    try:
        row = con.execute(
            "SELECT points_json, fetched_at FROM history_cache "
            "WHERE symbol = ? AND range = ? AND interval = ?",
            [symbol, range_, interval],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return None
    points_json, fetched_at = row
    if time.time() - fetched_at > ttl_seconds:
        return None
    return json.loads(points_json)


def put_cached_history(symbol: str, range_: str, interval: str, points: list[dict]) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO history_cache VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (symbol, range, interval) DO UPDATE SET "
            "points_json = excluded.points_json, fetched_at = excluded.fetched_at",
            [symbol, range_, interval, json.dumps(points), time.time()],
        )
    finally:
        con.close()


def put_cached_dossier(symbol: str, dossier: dict) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO dossier_cache VALUES (?, ?, ?) "
            "ON CONFLICT (symbol) DO UPDATE SET "
            "dossier_json = excluded.dossier_json, fetched_at = excluded.fetched_at",
            [symbol, _dumps(dossier), time.time()],
        )
    finally:
        con.close()


# CANSLIM scorecards are expensive to build (quoteSummary + two history
# pulls) but the underlying fundamentals (earnings estimates, institutional
# ownership) don't meaningfully move within a trading day, so a much longer
# TTL than price history is fine here.
CANSLIM_TTL_SECONDS = 4 * 60 * 60


def get_cached_canslim(symbol: str, ttl_seconds: float = CANSLIM_TTL_SECONDS) -> dict | None:
    con = _conn(read_only=True)
    try:
        row = con.execute(
            "SELECT scorecard_json, fetched_at FROM canslim_cache WHERE symbol = ?",
            [symbol],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return None
    scorecard_json, fetched_at = row
    if time.time() - fetched_at > ttl_seconds:
        return None
    return json.loads(scorecard_json)


def put_cached_canslim(symbol: str, scorecard: dict) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO canslim_cache VALUES (?, ?, ?) "
            "ON CONFLICT (symbol) DO UPDATE SET "
            "scorecard_json = excluded.scorecard_json, fetched_at = excluded.fetched_at",
            [symbol, _dumps(scorecard), time.time()],
        )
    finally:
        con.close()


# SEC filings land a few times a year, not intraday — a day-long TTL is
# plenty and keeps repeat scorecard builds from re-hitting data.sec.gov.
EDGAR_FACTS_TTL_SECONDS = 24 * 60 * 60
# The ticker->CIK map is a ~10MB static-ish file SEC republishes daily;
# a week-long TTL is safe (tickers rarely change CIK) and avoids
# re-downloading it on every single symbol lookup.
EDGAR_CIK_MAP_TTL_SECONDS = 7 * 24 * 60 * 60


def get_cached_edgar_facts(symbol: str, ttl_seconds: float = EDGAR_FACTS_TTL_SECONDS) -> dict | None:
    con = _conn(read_only=True)
    try:
        row = con.execute(
            "SELECT facts_json, fetched_at FROM edgar_facts_cache WHERE symbol = ?",
            [symbol],
        ).fetchone()
    finally:
        con.close()
    if row is None:
        return None
    facts_json, fetched_at = row
    if time.time() - fetched_at > ttl_seconds:
        return None
    return json.loads(facts_json)


def put_cached_edgar_facts(symbol: str, facts: dict) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO edgar_facts_cache VALUES (?, ?, ?) "
            "ON CONFLICT (symbol) DO UPDATE SET "
            "facts_json = excluded.facts_json, fetched_at = excluded.fetched_at",
            [symbol, json.dumps(facts), time.time()],
        )
    finally:
        con.close()


def get_cached_edgar_cik_map(ttl_seconds: float = EDGAR_CIK_MAP_TTL_SECONDS) -> dict | None:
    con = _conn(read_only=True)
    try:
        row = con.execute("SELECT map_json, fetched_at FROM edgar_cik_map_cache WHERE id = 0").fetchone()
    finally:
        con.close()
    if row is None:
        return None
    map_json, fetched_at = row
    if time.time() - fetched_at > ttl_seconds:
        return None
    return json.loads(map_json)


def put_cached_edgar_cik_map(cik_map: dict) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO edgar_cik_map_cache VALUES (0, ?, ?) "
            "ON CONFLICT (id) DO UPDATE SET "
            "map_json = excluded.map_json, fetched_at = excluded.fetched_at",
            [json.dumps(cik_map), time.time()],
        )
    finally:
        con.close()


# --- AI universe --------------------------------------------------------
#
# ai_stocks_reviewed.json is the backbone list of AI-exposed securities.
# The JSON carries a lot of reviewer boilerplate (disclaimers, "not a
# measure of" lists, per-field audit notes); only the signal lands here:
# identity, listing status, category weights, and the one-line rationale.
# Every per-security metric table added later (CANSLIM, EDGAR facts, ...)
# joins on `ticker`.

UNIVERSE_JSON = Path(__file__).resolve().parent / "data" / "ai_stocks_reviewed.json"


def _ensure_universe_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS ai_universe (
            ticker VARCHAR PRIMARY KEY,
            name VARCHAR,
            region VARCHAR,
            primary_category VARCHAR,
            security_status VARCHAR,
            eligible BOOLEAN,
            category_confidence VARCHAR,
            rationale VARCHAR,
            source_url VARCHAR,
            reviewed_on VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ai_universe_category (
            ticker VARCHAR,
            level VARCHAR,
            category VARCHAR,
            weight DOUBLE,
            PRIMARY KEY (ticker, level, category)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ai_taxonomy (
            sub_category VARCHAR PRIMARY KEY,
            primary_category VARCHAR,
            description VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ai_universe_meta (
            id INTEGER PRIMARY KEY,
            source_mtime DOUBLE,
            loaded_at DOUBLE,
            record_count INTEGER
        )
    """)


def _dominant(weights: dict) -> str | None:
    if not weights:
        return None
    return max(weights.items(), key=lambda kv: kv[1])[0]


def load_universe(path: Path = UNIVERSE_JSON, force: bool = False) -> dict:
    """(Re)load the reviewed JSON into DuckDB. Skips when the file hasn't
    changed since the last load unless `force`."""
    mtime = path.stat().st_mtime
    con = _conn()
    try:
        _ensure_universe_tables(con)
        row = con.execute("SELECT source_mtime, record_count FROM ai_universe_meta WHERE id = 0").fetchone()
        if row is not None and not force and row[0] == mtime:
            return {"loaded": False, "record_count": row[1]}

        data = json.loads(path.read_text())
        meta = data.get("_meta", {})
        stocks = data["stocks"]

        universe_rows = []
        category_rows = []
        for s in stocks:
            sec = s.get("security", {})
            west = s.get("weight_estimation", {})
            rev = s.get("review", {})
            rationale = " ".join(west.get("rationale") or [])
            sources = s.get("sources") or []
            source_url = sources[0].get("url") if sources else None
            universe_rows.append([
                s["ticker"],
                s.get("name"),
                s.get("region"),
                _dominant(s.get("primary", {})),
                sec.get("status"),
                sec.get("eligible_as_current_security"),
                west.get("category_assignment_confidence"),
                rationale,
                source_url,
                rev.get("reviewed_on") or meta.get("reviewed_on"),
            ])
            for cat, w in (s.get("primary") or {}).items():
                category_rows.append([s["ticker"], "primary", cat, float(w)])
            for cat, w in (s.get("subs") or {}).items():
                category_rows.append([s["ticker"], "sub", cat, float(w)])

        taxonomy_rows = []
        ext_desc = meta.get("taxonomy_extensions", {})
        clar = meta.get("taxonomy_scope_clarifications", {})
        for primary, subs in meta.get("taxonomy", {}).items():
            for sub in subs:
                desc = ext_desc.get(primary, {}).get(sub) or clar.get(sub)
                taxonomy_rows.append([sub, primary, desc])

        con.execute("BEGIN")
        con.execute("DELETE FROM ai_universe")
        con.execute("DELETE FROM ai_universe_category")
        con.execute("DELETE FROM ai_taxonomy")
        con.executemany("INSERT INTO ai_universe VALUES (?,?,?,?,?,?,?,?,?,?)", universe_rows)
        con.executemany("INSERT INTO ai_universe_category VALUES (?,?,?,?)", category_rows)
        con.executemany("INSERT INTO ai_taxonomy VALUES (?,?,?)", taxonomy_rows)
        con.execute(
            "INSERT INTO ai_universe_meta VALUES (0, ?, ?, ?) "
            "ON CONFLICT (id) DO UPDATE SET source_mtime = excluded.source_mtime, "
            "loaded_at = excluded.loaded_at, record_count = excluded.record_count",
            [mtime, time.time(), len(universe_rows)],
        )
        con.execute("COMMIT")
        return {"loaded": True, "record_count": len(universe_rows)}
    finally:
        con.close()


def universe_groups() -> list[dict]:
    """Every pickable group: primary buckets, sub buckets, and regions,
    with member counts (eligible securities only)."""
    load_universe()
    con = _conn()
    try:
        rows = con.execute("""
            SELECT 'primary' AS level, c.category, NULL AS parent, count(*) AS n,
                   list(u.ticker ORDER BY c.weight DESC, u.ticker) AS tickers
            FROM ai_universe_category c JOIN ai_universe u USING (ticker)
            WHERE c.level = 'primary' AND u.eligible IS DISTINCT FROM false
            GROUP BY c.category
            UNION ALL
            SELECT 'sub', c.category, t.primary_category, count(*),
                   list(u.ticker ORDER BY c.weight DESC, u.ticker)
            FROM ai_universe_category c
            JOIN ai_universe u USING (ticker)
            LEFT JOIN ai_taxonomy t ON t.sub_category = c.category
            WHERE c.level = 'sub' AND u.eligible IS DISTINCT FROM false
            GROUP BY c.category, t.primary_category
            UNION ALL
            SELECT 'region', region, NULL, count(*), list(ticker ORDER BY ticker)
            FROM ai_universe WHERE eligible IS DISTINCT FROM false
            GROUP BY region
            ORDER BY 1, 3 NULLS FIRST, 4 DESC
        """).fetchall()
    finally:
        con.close()
    return [
        {"level": lv, "category": cat, "parent": parent, "count": n, "tickers": tickers}
        for lv, cat, parent, n, tickers in rows
    ]


def universe_members(level: str, category: str) -> list[dict]:
    """Securities in a group, heaviest exposure first. Region groups have
    no weight so they come back weight=1."""
    load_universe()
    con = _conn()
    try:
        if level == "region":
            rows = con.execute(
                "SELECT ticker, name, 1.0::DOUBLE FROM ai_universe "
                "WHERE region = ? AND eligible IS DISTINCT FROM false ORDER BY ticker",
                [category],
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT u.ticker, u.name, c.weight FROM ai_universe_category c "
                "JOIN ai_universe u USING (ticker) "
                "WHERE c.level = ? AND c.category = ? AND u.eligible IS DISTINCT FROM false "
                "ORDER BY c.weight DESC, u.ticker",
                [level, category],
            ).fetchall()
    finally:
        con.close()
    return [{"ticker": t, "name": n, "weight": w} for t, n, w in rows]


# --- FSDS segment revenue -------------------------------------------------

def fsds_loaded_quarters() -> set[str]:
    con = _conn(read_only=True)
    try:
        return {r[0] for r in con.execute("SELECT quarter FROM edgar_fsds_loaded").fetchall()}
    finally:
        con.close()


def get_segment_revenue(cik: int) -> list[dict]:
    """All kept revenue rows for a filer, oldest -> newest. Includes the
    undimensioned total (axis='') so callers can sum-check members."""
    con = _conn(read_only=True)
    try:
        rows = con.execute(
            """
            SELECT adsh, form, fy, fp, filed, tag, ddate, qtrs, axis, member, value
            FROM edgar_segment_revenue
            WHERE cik = ?
            ORDER BY ddate, filed, axis, member
            """,
            [cik],
        ).fetchall()
    finally:
        con.close()
    keys = ["adsh", "form", "fy", "fp", "filed", "tag", "ddate", "qtrs", "axis", "member", "value"]
    out = []
    for r in rows:
        d = dict(zip(keys, r))
        d["filed"] = d["filed"].isoformat()
        d["ddate"] = d["ddate"].isoformat()
        out.append(d)
    return out

