"""Local DuckDB cache for historical price data.

Keeps a small on-disk store at ~/.local/share/nvim/security_spread.duckdb so
repeat chart opens (same symbol/range/interval within TTL) skip the network
round-trip entirely, and gives the plugin a real place to grow into (joins,
backtests, screener snapshots) instead of everything being fetch-and-discard.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import duckdb

DB_PATH = Path(os.path.expanduser("~/.local/share/nvim/security_spread.duckdb"))

# History doesn't change intraday for the bar we already have except the
# still-forming last bar, so a modest TTL is safe and saves a network round
# trip on every chart re-open for the same symbol/range within the window.
DEFAULT_TTL_SECONDS = 15 * 60


def _conn() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS history_cache (
            symbol VARCHAR,
            range VARCHAR,
            interval VARCHAR,
            points_json VARCHAR,
            fetched_at DOUBLE,
            PRIMARY KEY (symbol, range, interval)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS transactions_cache (
            account VARCHAR PRIMARY KEY,
            transactions_json VARCHAR,
            fetched_at DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS positions_cache (
            id INTEGER PRIMARY KEY,
            positions_json VARCHAR,
            fetched_at DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_history (
            date DATE PRIMARY KEY,
            total_value DOUBLE,
            day_change_pct DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS canslim_cache (
            symbol VARCHAR PRIMARY KEY,
            scorecard_json VARCHAR,
            fetched_at DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS edgar_facts_cache (
            symbol VARCHAR PRIMARY KEY,
            facts_json VARCHAR,
            fetched_at DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS edgar_cik_map_cache (
            id INTEGER PRIMARY KEY,
            map_json VARCHAR,
            fetched_at DOUBLE
        )
    """)
    return con


# Positions are read two ways: an instant local read (no TTL check — any
# age is better than blocking on the network) to paint the dashboard
# immediately, and a background live pull that overwrites this cache once
# E*TRADE responds. There's no expiry here on purpose.
def get_cached_positions() -> list[dict] | None:
    con = _conn()
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
    con = _conn()
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
    con = _conn()
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
    con = _conn()
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
    con = _conn()
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


# CANSLIM scorecards are expensive to build (quoteSummary + two history
# pulls) but the underlying fundamentals (earnings estimates, institutional
# ownership) don't meaningfully move within a trading day, so a much longer
# TTL than price history is fine here.
CANSLIM_TTL_SECONDS = 4 * 60 * 60


def get_cached_canslim(symbol: str, ttl_seconds: float = CANSLIM_TTL_SECONDS) -> dict | None:
    con = _conn()
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
            [symbol, json.dumps(scorecard), time.time()],
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
    con = _conn()
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
    con = _conn()
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
