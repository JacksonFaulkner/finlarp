"""Local DuckDB cache for historical price data.

Keeps a small on-disk store at ~/.local/share/nvim/finlarp.duckdb so
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

from core.schemas.universe import Stock, infer_kind

DB_PATH = Path(os.path.expanduser("~/.local/share/nvim/finlarp.duckdb"))

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
    # Append-only: every ticker ever seen in positions or trades. The caches above are
    # overwritten (and transactions only span 2y); this is what outlives them.
    """
        CREATE TABLE IF NOT EXISTS traded_symbols (
            symbol VARCHAR PRIMARY KEY,
            first_seen DOUBLE,
            last_seen DOUBLE
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
    # Per-ticker research dossier (py/derive/dossier.py) read straight out of
    # DuckDB by the finlarp `dossier` screen, same as canslim_cache.
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


def cache_ages() -> dict:
    """Seconds since each portfolio cache was last written (None if never).
    Local-only; lets the nvim side decide what is worth re-pulling."""
    con = _conn(read_only=True)
    try:
        pos = con.execute("SELECT max(fetched_at) FROM positions_cache").fetchone()[0]
        txn = con.execute("SELECT min(fetched_at) FROM transactions_cache").fetchone()[0]
    finally:
        con.close()
    now = time.time()
    return {
        "positions_age": None if pos is None else now - pos,
        "transactions_age": None if txn is None else now - txn,
    }


def _remember_symbols(con, symbols) -> None:
    now = time.time()
    for s in {s for s in symbols if s}:
        con.execute(
            "INSERT INTO traded_symbols VALUES (?, ?, ?) ON CONFLICT (symbol) DO UPDATE SET last_seen = excluded.last_seen",
            [s, now, now],
        )


def get_traded_symbols() -> list[str]:
    """Every ticker ever held or traded. Seeds itself from the current caches, so it is
    complete the first time it is read, then only grows."""
    con = _conn()
    try:
        _remember_symbols(con, (p.get("symbol") for p in _loads("SELECT positions_json FROM positions_cache", con)))
        _remember_symbols(
            con,
            (
                t.get("symbol")
                for t in _loads("SELECT transactions_json FROM transactions_cache", con)
                if t.get("type") in TRADE_TYPES
            ),
        )
        return [r[0] for r in con.execute("SELECT symbol FROM traded_symbols ORDER BY symbol").fetchall()]
    finally:
        con.close()


TRADE_TYPES = ("Bought", "Sold", "Stock Split")


def _loads(sql: str, con) -> list[dict]:
    return [row for (blob,) in con.execute(sql).fetchall() for row in json.loads(blob)]


def put_cached_positions(positions: list[dict]) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO positions_cache VALUES (0, ?, ?) "
            "ON CONFLICT (id) DO UPDATE SET "
            "positions_json = excluded.positions_json, fetched_at = excluded.fetched_at",
            [json.dumps(positions), time.time()],
        )
        _remember_symbols(con, (p.get("symbol") for p in positions))
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
        _remember_symbols(con, (t.get("symbol") for t in transactions if t.get("type") in TRADE_TYPES))
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

UNIVERSE_JSON = Path(__file__).resolve().parents[2] / "data" / "ai_stocks_reviewed.json"


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
    con.execute("ALTER TABLE ai_universe ADD COLUMN IF NOT EXISTS kind VARCHAR")
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
    for col in ("label VARCHAR", "primary_label VARCHAR", "sort INTEGER", "primary_sort INTEGER"):
        con.execute(f"ALTER TABLE ai_taxonomy ADD COLUMN IF NOT EXISTS {col}")
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
    """One-time import of the reviewed JSON into DuckDB. The tables are the source of truth after
    that: an existing universe is never overwritten unless `force`. New stocks go through
    `upsert_stock`, not the file."""
    con = _conn()
    try:
        _ensure_universe_tables(con)
        n = con.execute("SELECT count(*) FROM ai_universe").fetchone()[0]
        if n and not force:
            return {"loaded": False, "record_count": n}

        data = json.loads(path.read_text())
        meta = data.get("_meta", {})
        taxonomy = meta.get("taxonomy", {})
        stocks, invalid = [], []
        for s in data["stocks"]:
            sec = s.get("security", {})
            west = s.get("weight_estimation", {})
            sources = s.get("sources") or []
            try:
                stock = Stock(
                    ticker=s["ticker"],
                    name=s.get("name") or s["ticker"],
                    region=s.get("region") or "US",
                    kind=infer_kind(s["ticker"]),
                    subs=s.get("subs") or {},
                    eligible=sec.get("eligible_as_current_security"),
                    status=sec.get("status"),
                    category_confidence=west.get("category_assignment_confidence"),
                    rationale=" ".join(west.get("rationale") or []) or None,
                    source_url=sources[0].get("url") if sources else None,
                    reviewed_on=(s.get("review") or {}).get("reviewed_on") or meta.get("reviewed_on"),
                )
                stock.check_taxonomy(taxonomy)
                stocks.append(stock.with_primary(taxonomy))
            except ValueError as e:
                invalid.append(str(e))

        ext_desc = meta.get("taxonomy_extensions", {})
        clar = meta.get("taxonomy_scope_clarifications", {})
        descriptions = {sub: ext_desc.get(p, {}).get(sub) or clar.get(sub) for p, subs in taxonomy.items() for sub in subs}

        con.execute("BEGIN")
        con.execute("DELETE FROM ai_universe")
        con.execute("DELETE FROM ai_universe_category")
        con.execute("DELETE FROM ai_taxonomy")
        _insert_taxonomy(con, taxonomy, meta.get("taxonomy_labels", {}), descriptions)
        for stock in stocks:
            _write_stock(con, stock)
        con.execute("COMMIT")
        return {"loaded": True, "record_count": len(stocks), "invalid": invalid}
    finally:
        con.close()


def _insert_taxonomy(con: duckdb.DuckDBPyConnection, taxonomy: dict, labels: dict, descriptions: dict) -> None:
    """Rows carry display labels and stack order (dict order of `taxonomy`)."""
    rows, n = [], 0
    for ps, (primary, subs) in enumerate(taxonomy.items()):
        for sub in subs:
            rows.append([sub, primary, descriptions.get(sub), labels.get(sub, sub), labels.get(primary, primary), n, ps])
            n += 1
    con.executemany("INSERT INTO ai_taxonomy VALUES (?,?,?,?,?,?,?)", rows)


def _write_stock(con: duckdb.DuckDBPyConnection, s: Stock) -> None:
    con.execute("DELETE FROM ai_universe WHERE ticker = ?", [s.ticker])
    con.execute("DELETE FROM ai_universe_category WHERE ticker = ?", [s.ticker])
    con.execute(
        "INSERT INTO ai_universe (ticker, name, region, primary_category, security_status, eligible, "
        "category_confidence, rationale, source_url, reviewed_on, kind) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [s.ticker, s.name, s.region, _dominant(s.primary), s.status, s.eligible, s.category_confidence,
         s.rationale, s.source_url, s.reviewed_on, s.kind],
    )
    rows = [[s.ticker, "primary", c, w] for c, w in s.primary.items()]
    rows += [[s.ticker, "sub", c, w] for c, w in s.subs.items()]
    con.executemany("INSERT INTO ai_universe_category VALUES (?,?,?,?)", rows)


def taxonomy() -> dict[str, list[str]]:
    con = _conn()
    try:
        _ensure_universe_tables(con)
        out: dict[str, list[str]] = {}
        for sub, primary in con.execute("SELECT sub_category, primary_category FROM ai_taxonomy ORDER BY sort").fetchall():
            out.setdefault(primary, []).append(sub)
        return out
    finally:
        con.close()


def upsert_stock(stock: Stock) -> Stock:
    """Add or replace one stock. Buckets are checked against the taxonomy and primary is recomputed."""
    tax = taxonomy()
    stock.check_taxonomy(tax)
    stock = stock.with_primary(tax)
    con = _conn()
    try:
        _ensure_universe_tables(con)
        con.execute("BEGIN")
        _write_stock(con, stock)
        con.execute("COMMIT")
    finally:
        con.close()
    return stock


def get_stocks(include_ineligible: bool = False) -> list[Stock]:
    """The universe. Ineligible names (acquired, delisted) are kept in the table but hidden by default."""
    load_universe()
    con = _conn()
    try:
        where = "" if include_ineligible else "WHERE u.eligible IS DISTINCT FROM false"
        heads = con.execute(
            f"SELECT ticker, name, region, kind, eligible, security_status, category_confidence, rationale, "
            f"source_url, reviewed_on FROM ai_universe u {where} ORDER BY ticker"
        ).fetchall()
        weights: dict[str, dict[str, dict[str, float]]] = {}
        for t, level, cat, w in con.execute("SELECT ticker, level, category, weight FROM ai_universe_category").fetchall():
            weights.setdefault(t, {"primary": {}, "sub": {}})[level][cat] = w
    finally:
        con.close()
    out = []
    for t, name, region, kind, elig, status, conf, why, url, rev in heads:
        w = weights.get(t, {"primary": {}, "sub": {}})
        subs = dict(sorted(w["sub"].items(), key=lambda kv: -kv[1]))
        out.append(
            Stock.model_construct(
                ticker=t, name=name, region=region, kind=kind or "stock", subs=subs,
                primary=dict(sorted(w["primary"].items(), key=lambda kv: -kv[1])), eligible=elig, status=status,
                category_confidence=conf, rationale=why, source_url=url, reviewed_on=rev,
            )
        )
    return out


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

