"""Databento bars for the US universe, stored as Parquet and exposed to DuckDB as views.

    bars_1d     EQUS.SUMMARY ohlcv-1d   consolidated daily bars, true consolidated volume (from 2024-07-01)
    bars_1m     XNAS.BASIC   ohlcv-1m   1-minute bars, Nasdaq venues only (about 50-80% of consolidated volume)
    quotes_1m   XNAS.BASIC   cbbo-1m    1-minute consolidated best bid/ask

Files land in <DATA_ROOT>/market/databento/<table>/ as one Parquet per (symbol batch, date range),
named <start>_<end>_<tag>.parquet with a .symbols.json manifest. Coverage is tracked per symbol as
date ranges across every file, so a rerun only asks for what no file holds yet: the days since the
last pull, or the whole history for a symbol new to the universe. Requests are batched by symbol:
one 40-symbol request is far faster than 40 single-symbol ones. Every chunk is priced first and the
run stops at --max-cost.

    uv run sources/databento_bars.py plan                        # price everything, pull nothing
    uv run sources/databento_bars.py pull bars_1d bars_1m quotes_1m --max-cost 70
    uv run sources/databento_bars.py dedupe [--dry-run]          # set aside files other files fully cover
    uv run sources/databento_bars.py compact [--dry-run]         # merge last month's daily delta files
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
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import databento as db
import duckdb
from databento.common.error import BentoClientError, BentoServerError

from core import db as cache_db
from sources import keys, universe

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
    return sorted({s["ticker"] for s in universe.rows() if s["region"] == "US" and s["kind"] != "foreign"})


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


def _span_of(f: Path) -> tuple[date, date]:
    a, b = f.stem.split("_")[:2]
    return date.fromisoformat(a), date.fromisoformat(b)


def file_ranges(f: Path) -> dict[str, list[tuple[date, date]]]:
    """Per symbol, the [start, end) ranges this file holds.

    A pulled file's manifest lists the symbols asked for, so a symbol with no bars in the range
    (pre-IPO) still counts as covered; its range is the one in the file name. A compacted file's
    manifest maps each symbol to its own ranges. Files from before manifests existed fall back to
    the symbols inside the parquet.
    """
    m = _manifest(f)
    if m.exists():
        got = json.loads(m.read_text())
        if isinstance(got, dict):
            return {s: [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in rs] for s, rs in got.items()}
        syms = got
    else:
        con = duckdb.connect()
        syms = [r[0] for r in con.execute("SELECT DISTINCT symbol FROM read_parquet(?)", [str(f)]).fetchall()]
        con.close()
    span = _span_of(f)
    return {s: [span] for s in syms}


def coverage(table: str, skip: Path | None = None) -> dict[str, list[tuple[date, date]]]:
    """Per symbol, every range some file on disk (other than `skip`) holds."""
    out: dict[str, list[tuple[date, date]]] = defaultdict(list)
    for f in sorted((OUT_ROOT / table).glob("*.parquet")):
        if f != skip:
            for s, rs in file_ranges(f).items():
                out[s] += rs
    return out


def gaps(have: list[tuple[date, date]], start: date, end: date) -> list[tuple[date, date]]:
    """The parts of [start, end) that no range in `have` covers."""
    out, cur = [], start
    for a, b in sorted(have):
        if b <= cur:
            continue
        if a > cur:
            out.append((cur, min(a, end)))
        cur = max(cur, b)
        if cur >= end:
            break
    if cur < end:
        out.append((cur, end))
    return [(a, b) for a, b in out if a < b]


def chunks(table: str, client: db.Historical) -> list[dict]:
    """Only what is missing: per symbol, the date ranges no file on disk covers yet, cut into
    window_days pieces and batched with every other symbol missing the same piece.

    A daily run therefore asks for one short range (last pull's end .. dataset end) for the whole
    universe, and a symbol new to the universe gets its full history. Batches are named by content,
    so growing the universe or the traded set never shifts or invalidates an existing file.
    """
    spec = TABLES[table]
    start, end = span(client, spec)
    have = coverage(table)
    by_range: dict[tuple[date, date], list[str]] = defaultdict(list)
    for s in sorted(set(symbols()) | set(holdings())):
        for ga, gb in gaps(have.get(s, []), start, end):
            for a, b in windows(ga, gb, spec["window_days"]):
                by_range[(a, b)].append(s)
    out = []
    for (a, b), missing in sorted(by_range.items()):
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


def dedupe(tables: list[str], dry_run: bool) -> list[Path]:
    """Set aside what other files already hold, in <table>/_superseded/.

    Overlapping files double rows in the views (they read every parquet). Older files go first,
    so the newest pull of a range is the one kept. A file other files cover entirely is moved; one
    they cover for only some symbols is rewritten with just the symbols it alone holds (a symbol
    that left the universe keeps its old bars). Moved, not deleted: drop the folder once happy.
    """
    moved = []
    for table in tables:
        d = OUT_ROOT / table
        for f in sorted(d.glob("*.parquet"), key=lambda p: p.stat().st_mtime):
            others = coverage(table, skip=f)
            mine = file_ranges(f)
            keep = {s: rs for s, rs in mine.items() if any(gaps(others.get(s, []), a, b) for a, b in rs)}
            if len(keep) == len(mine):
                continue
            moved.append(f)
            print(f"  {table:10} {f.name}: {len(mine) - len(keep)} of {len(mine)} symbols held elsewhere"
                  + (f", keeping {sorted(keep)}" if keep else ""))
            if dry_run:
                continue
            if keep:
                a, b = _span_of(f)
                out = d / f"{a}_{b}_r{hashlib.sha1(','.join(sorted(keep)).encode()).hexdigest()[:8]}.parquet"
                tmp = out.with_suffix(".tmp")
                con = duckdb.connect()
                con.execute(f"COPY (SELECT * FROM read_parquet('{f}') WHERE symbol IN ?) TO '{tmp}' (FORMAT parquet)",
                            [sorted(keep)])
                con.close()
                _manifest(out).write_text(json.dumps({s: [[x.isoformat(), y.isoformat()] for x, y in rs] for s, rs in keep.items()}))
                tmp.rename(out)
            (d / "_superseded").mkdir(exist_ok=True)
            for p in (f, _manifest(f)):
                if p.exists():
                    p.rename(d / "_superseded" / p.name)
    print(f"{len(moved)} files {'would be ' if dry_run else ''}set aside")
    return moved


def compact(tables: list[str], dry_run: bool, max_span_days: int = 7) -> None:
    """Merge short delta files (span <= max_span_days) from before this month into one file per
    month, so daily pulls don't leave thousands of small files for the views to open."""
    month0 = date.today().replace(day=1)
    for table in tables:
        d = OUT_ROOT / table
        groups: dict[str, list[Path]] = defaultdict(list)
        for f in sorted(d.glob("*.parquet")):
            a, b = _span_of(f)
            if (b - a).days <= max_span_days and b <= month0:
                groups[f"{a:%Y-%m}"].append(f)
        for month, files in sorted(groups.items()):
            if len(files) < 2:
                continue
            ranges: dict[str, list[tuple[date, date]]] = defaultdict(list)
            for f in files:
                for s, rs in file_ranges(f).items():
                    ranges[s] += rs
            lo = min(_span_of(f)[0] for f in files)
            hi = max(_span_of(f)[1] for f in files)
            tag = hashlib.sha1(",".join(f.name for f in files).encode()).hexdigest()[:8]
            out = d / f"{lo}_{hi}_k{tag}.parquet"
            print(f"  {table:10} {month}: {len(files)} files -> {out.name}")
            if dry_run:
                continue
            tmp = out.with_suffix(".tmp")
            con = duckdb.connect()
            con.execute(
                f"COPY (SELECT DISTINCT * FROM read_parquet({[str(f) for f in files]}, union_by_name = true) "
                f"ORDER BY symbol, ts_event) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)"
            )
            con.close()
            _manifest(out).write_text(json.dumps({s: [[a.isoformat(), b.isoformat()] for a, b in sorted(rs)] for s, rs in ranges.items()}))
            tmp.rename(out)
            for f in files:
                f.unlink()
                _manifest(f).unlink(missing_ok=True)


def cost(client: db.Historical, ch: dict) -> float | None:
    """Price of a chunk, or None when none of its symbols resolve in the range: a weekend or
    holiday with no session yet. Such a chunk is skipped, not marked covered, so the next run
    asks for it again as part of a longer range."""
    try:
        return _retry(
            lambda: client.metadata.get_cost(
                dataset=ch["dataset"], symbols=ch["symbols"], schema=ch["schema"], start=ch["start"], end=ch["end"], stype_in="raw_symbol"
            )
        )
    except BentoClientError as e:
        if "symbology_invalid_request" in str(e):
            return None
        raise


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
    client = db.Historical(keys.require("DATABENTO_API_KEY"))
    todo = [ch for t in tables for ch in chunks(t, client)]
    pending = [ch for ch in todo if not ch["path"].exists()]
    print(f"{len(todo)} chunks, {len(todo) - len(pending)} already on disk")
    with ThreadPoolExecutor(WORKERS) as pool:
        priced = list(pool.map(lambda ch: cost(client, ch), pending))
    empty = [ch for ch, c in zip(pending, priced) if c is None]
    if empty:
        print(f"  {len(empty)} chunks have no session yet (weekend/holiday), skipped")
    pending, costs = [ch for ch, c in zip(pending, priced) if c is not None], [c for c in priced if c is not None]
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
    con = cache_db._open(False)  # retries while another process holds the write lock
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
    for name in ("dedupe", "compact"):
        p = sub.add_parser(name)
        p.add_argument("tables", nargs="*", choices=list(TABLES), help="default: all")
        p.add_argument("--dry-run", action="store_true")
    sub.add_parser("views")
    args = ap.parse_args()
    if args.cmd == "views":
        views()
    elif args.cmd == "dedupe":
        dedupe(args.tables or list(TABLES), args.dry_run)
    elif args.cmd == "compact":
        compact(args.tables or list(TABLES), args.dry_run)
    else:
        pull(args.tables or list(TABLES), args.max_cost, plan_only=args.cmd == "plan")


if __name__ == "__main__":
    main()
