"""Databento bars for the US universe, stored as Parquet and exposed to DuckDB as views.

    bars_1d     EQUS.SUMMARY ohlcv-1d   consolidated daily bars, true consolidated volume (from 2024-07-01)
    bars_1m     XNAS.BASIC   ohlcv-1m   1-minute bars, Nasdaq venues only (about 50-80% of consolidated volume)
    quotes_1m   XNAS.BASIC   cbbo-1m    1-minute consolidated best bid/ask

Files land in <DATA_ROOT>/market/databento/<table>/ as one Parquet per (symbol batch, window), so a
rerun skips what is already on disk. Requests are batched by symbol: one 40-symbol request is far
faster than 40 single-symbol ones. Every chunk is priced first and the run stops at --max-cost.

    uv run sources/databento_bars.py plan                        # price everything, pull nothing
    uv run sources/databento_bars.py pull bars_1d bars_1m quotes_1m --max-cost 70
    uv run sources/databento_bars.py views                       # (re)create the DuckDB views

Needs DATABENTO_API_KEY in the environment (see .env.example).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import databento as db
import duckdb
from databento.common.error import BentoServerError

from core import db as cache_db
from sources import universe

OUT_ROOT = universe.DATA_ROOT / "market" / "databento"
BATCH = 40  # symbols per request
WORKERS = 4
RETRIES = 6

TABLES = {
    "bars_1d": {"dataset": "EQUS.SUMMARY", "schema": "ohlcv-1d", "start": date(2024, 7, 1), "window_days": 3650},
    "bars_1m": {"dataset": "XNAS.BASIC", "schema": "ohlcv-1m", "years": 2, "window_days": 92},
    "quotes_1m": {"dataset": "XNAS.BASIC", "schema": "cbbo-1m", "months": 3, "window_days": 92},
}


PLAIN_TICKER = re.compile(r"[A-Z]{1,5}")  # excludes options, free text and class shares (BRK.B needs a different form)


def symbols() -> list[str]:
    """US tickers on Databento's raw_symbol scheme (class shares like BRK.B need a different form)."""
    stocks = json.loads(universe.UNIVERSE_PATH.read_text())["stocks"]  # not universe.stocks(): that hits sec.gov for CIKs
    return sorted({s["ticker"] for s in stocks if s.get("region") == "US" and "." not in s["ticker"]})


def holdings() -> list[str]:
    """Plain US tickers ever held or traded, from the append-only traded_symbols table.

    Holdings churn, so this is a superset on purpose: a sold name keeps its bars.
    """
    return [s for s in cache_db.get_traded_symbols() if PLAIN_TICKER.fullmatch(s)]


def _retry(fn):
    for i in range(RETRIES):
        try:
            return fn()
        except BentoServerError:  # the gateway 504s now and then
            if i == RETRIES - 1:
                raise
            time.sleep(2 * 2**i)
    raise AssertionError("unreachable")


def span(client: db.Historical, spec: dict) -> tuple[date, date]:
    end = date.fromisoformat(_retry(lambda: client.metadata.get_dataset_range(spec["dataset"]))["end"][:10])
    if "start" in spec:
        return spec["start"], end
    days = spec["years"] * 365 if "years" in spec else spec["months"] * 30
    return end - timedelta(days=days), end


def windows(start: date, end: date, step: int) -> list[tuple[date, date]]:
    out, cur = [], start
    while cur < end:
        nxt = min(cur + timedelta(days=step), end)
        out.append((cur, nxt))
        cur = nxt
    return out


def _manifest(path: Path) -> Path:
    return path.with_suffix(".symbols.json")


def covered(table: str, a: date, b: date) -> set[str]:
    """Symbols already requested for this window, whatever the batch layout was when they were pulled.

    Each pulled file has a manifest of the symbols asked for, so a symbol with no bars in the window
    (pre-IPO) still counts as covered. Files from before manifests existed fall back to the symbols
    inside the parquet.
    """
    out: set[str] = set()
    for f in sorted((OUT_ROOT / table).glob(f"{a}_{b}_*.parquet")):
        m = _manifest(f)
        if m.exists():
            out |= set(json.loads(m.read_text()))
        else:
            con = duckdb.connect()
            out |= {r[0] for r in con.execute("SELECT DISTINCT symbol FROM read_parquet(?)", [str(f)]).fetchall()}
            con.close()
    return out


def chunks(table: str, client: db.Historical) -> list[dict]:
    """Only what is missing: per window, every wanted symbol that no file on disk covers yet.

    Batches are named by content, so growing the universe or the traded set never shifts or
    invalidates an existing file; it just adds chunks for the new symbols.
    """
    spec = TABLES[table]
    start, end = span(client, spec)
    wanted = sorted(set(symbols()) | set(holdings()))
    out = []
    for a, b in windows(start, end, spec["window_days"]):
        missing = [s for s in wanted if s not in covered(table, a, b)]
        for i in range(0, len(missing), BATCH):
            batch = missing[i : i + BATCH]
            tag = hashlib.sha1(",".join(batch).encode()).hexdigest()[:8]
            out.append(
                {
                    "table": table,
                    "dataset": spec["dataset"],
                    "schema": spec["schema"],
                    "symbols": batch,
                    "start": a.isoformat(),
                    "end": b.isoformat(),
                    "path": OUT_ROOT / table / f"{a}_{b}_c{tag}.parquet",
                }
            )
    return out


def cost(client: db.Historical, ch: dict) -> float:
    return _retry(
        lambda: client.metadata.get_cost(
            dataset=ch["dataset"], symbols=ch["symbols"], schema=ch["schema"], start=ch["start"], end=ch["end"], stype_in="raw_symbol"
        )
    )


def fetch(client: db.Historical, ch: dict) -> int:
    def go():
        store = client.timeseries.get_range(
            dataset=ch["dataset"], symbols=ch["symbols"], schema=ch["schema"], start=ch["start"], end=ch["end"], stype_in="raw_symbol"
        )
        return store.to_df().reset_index()

    df = _retry(go)
    if "close" in df.columns:  # Databento pads dates before a listing / after a delisting with all-zero bars
        df = df[df["close"] > 0]
    ch["path"].parent.mkdir(parents=True, exist_ok=True)
    tmp = ch["path"].with_suffix(".tmp")
    df.drop(columns=[c for c in ("rtype", "publisher_id", "instrument_id") if c in df.columns]).to_parquet(tmp)
    tmp.rename(ch["path"])  # a file on disk is always complete, so reruns can trust it
    _manifest(ch["path"]).write_text(json.dumps(ch["symbols"]))
    return len(df)


def pull(tables: list[str], max_cost: float, plan_only: bool) -> None:
    client = db.Historical()
    todo = [ch for t in tables for ch in chunks(t, client)]
    pending = [ch for ch in todo if not ch["path"].exists()]
    print(f"{len(todo)} chunks, {len(todo) - len(pending)} already on disk")
    with ThreadPoolExecutor(WORKERS) as pool:
        costs = list(pool.map(lambda ch: cost(client, ch), pending))
    per_table: dict[str, float] = {}
    for ch, c in zip(pending, costs):
        per_table[ch["table"]] = per_table.get(ch["table"], 0) + c
        ch["cost"] = c
    total = sum(costs)
    for t, c in per_table.items():
        print(f"  {t:10} ${c:8.2f}")
    print(f"  {'total':10} ${total:8.2f}   cap ${max_cost:.2f}")
    if plan_only:
        return
    if total > max_cost:
        sys.exit(f"estimate ${total:.2f} is over --max-cost ${max_cost:.2f}; nothing pulled")
    t0, rows, spent = time.time(), 0, 0.0
    with ThreadPoolExecutor(WORKERS) as pool:
        for ch, n in zip(pending, pool.map(lambda ch: fetch(client, ch), pending)):
            rows += n
            spent += ch["cost"]
            print(f"  {ch['table']:10} {ch['start']}..{ch['end']} {ch['path'].stem.rsplit('_', 1)[-1]:>9}{n:>9,} rows   ${spent:7.2f}  {time.time() - t0:5.0f}s", flush=True)
    print(f"done: {rows:,} rows, about ${spent:.2f}, {time.time() - t0:.0f}s")
    views()


def views() -> None:
    """One view per table over its Parquet files. A missing table is skipped."""
    con = duckdb.connect(str(cache_db.DB_PATH))
    for table in TABLES:
        d = OUT_ROOT / table
        if not any(d.glob("*.parquet")):
            continue
        con.execute(
            f"CREATE OR REPLACE VIEW {table} AS "
            f"SELECT * FROM read_parquet('{d}/*.parquet', union_by_name = true)"
        )
        print(f"view {table} -> {d}")
    con.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Databento bars for the universe")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "pull"):
        p = sub.add_parser(name)
        p.add_argument("tables", nargs="*", choices=list(TABLES), help="default: all")
        p.add_argument("--max-cost", type=float, default=70.0)
    sub.add_parser("views")
    args = ap.parse_args()
    if args.cmd == "views":
        views()
    else:
        pull(args.tables or list(TABLES), args.max_cost, plan_only=args.cmd == "plan")


if __name__ == "__main__":
    main()
