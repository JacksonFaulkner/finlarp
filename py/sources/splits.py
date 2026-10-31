"""Stock splits from Yahoo, so the daily bars can be put on one price basis.

Databento's bars are raw: a 10:1 split shows as a 90% drop overnight, which turns
AVGO's 2024 split into a -90% year and SSO's two 2:1 splits into -40%. Each split
is stored in the `splits` table; the `bars_1d_adj` view divides pre-split prices
(and multiplies volume) by every later split's ratio.

    uv run sources/splits.py pull            # every symbol in the daily bars
    uv run sources/splits.py pull AVGO SSO   # just these
    uv run sources/splits.py check           # each split against its bar jump, and jumps with no split
"""

from __future__ import annotations

import argparse
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime

import duckdb

from core import db
from sources import databento_bars, universe, yahoo

WORKERS = 6
BARS_1D = universe.DATA_ROOT / "market" / "databento" / "bars_1d" / "*.parquet"


def fetch(symbol: str, session) -> list[dict]:
    """Split events for one symbol, oldest first. `ratio` is new shares per old share:
    2.0 for a 2:1 forward split, 0.1 for a 1:10 reverse split."""
    resp = session.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"range": "5y", "interval": "1d", "events": "split"},
        timeout=20,
    )
    if not resp.ok:
        return []
    result = (resp.json().get("chart") or {}).get("result") or []
    if not result:
        return []
    events = (result[0].get("events") or {}).get("splits") or {}
    return sorted(
        (
            {
                "symbol": symbol,
                # Yahoo stamps a split at the open (13:30 UTC), so the UTC date is the trading day
                "split_date": datetime.fromtimestamp(ev["date"], tz=UTC).date().isoformat(),
                "ratio": float(ev["numerator"]) / float(ev["denominator"]),
            }
            for ev in events.values()
        ),
        key=lambda r: r["split_date"],
    )


def bar_symbols() -> list[str]:
    con = duckdb.connect()
    try:
        rows = con.execute(f"SELECT DISTINCT symbol FROM read_parquet('{BARS_1D}', union_by_name=true) ORDER BY symbol").fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def pull(symbols: list[str]) -> dict:
    session = yahoo.new_session()
    yahoo.get_crumb(session)
    with ThreadPoolExecutor(WORKERS) as pool:
        events = list(pool.map(lambda s: fetch(s, session), symbols))
    rows = [r for ev in events for r in ev]
    db.put_splits(symbols, rows)
    databento_bars.views()  # rebuilds bars_1d_adj and market/splits.parquet from the new rows
    return {
        "symbols": len(symbols),
        "splits": len(rows),
        "with_splits": sorted({r["symbol"] for r in rows}),
    }


def check(tolerance: float = 0.15) -> dict:
    """Each stored split against the raw close-to-close jump across it, plus every large
    jump with no stored split (a real crash, or a split Yahoo doesn't list)."""
    con = duckdb.connect()
    try:
        bars = con.execute(
            f"SELECT symbol, (ts_event AT TIME ZONE 'UTC')::DATE AS d, close "
            f"FROM read_parquet('{BARS_1D}', union_by_name=true) WHERE close > 0 ORDER BY symbol, d"
        ).fetchall()
    finally:
        con.close()
    splits = db.get_splits()
    by_sym: dict[str, list[tuple[date, float]]] = {}
    for s, d, c in bars:
        by_sym.setdefault(s, []).append((d, c))

    explained, mismatched, unexplained = [], [], []
    known = set()
    for s, d, ratio in splits:
        known.add((s, d))
        series = by_sym.get(s, [])
        before = [c for bd, c in series if bd < d]
        after = [c for bd, c in series if bd >= d]
        if not before or not after:
            continue  # the split falls outside the bars
        jump = after[0] / before[-1]
        row = (s, d.isoformat(), ratio, round(jump, 4))
        (explained if abs(math.log(jump * ratio)) <= tolerance else mismatched).append(row)
    for s, series in by_sym.items():
        for (_, c0), (d1, c1) in zip(series, series[1:]):
            if abs(math.log(c1 / c0)) > math.log(1.6) and (s, d1) not in known:
                unexplained.append((s, d1.isoformat(), round(c1 / c0, 3)))
    return {"explained": explained, "mismatched": mismatched, "unexplained": unexplained}


def main() -> None:
    ap = argparse.ArgumentParser(description="Stock splits for the daily bars")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("symbols", nargs="*")
    sub.add_parser("check")
    args = ap.parse_args()
    if args.cmd == "pull":
        print(pull(args.symbols or bar_symbols()))
        return
    out = check()
    print(f"explained {len(out['explained'])}, mismatched {len(out['mismatched'])}, unexplained jumps {len(out['unexplained'])}")
    for name in ("mismatched", "unexplained"):
        for row in out[name][:40]:
            print(f"  {name}: {row}")


if __name__ == "__main__":
    main()
