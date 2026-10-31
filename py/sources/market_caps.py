"""Market cap per universe name in USD, for the size weights in the TUI.

profiles.parquet holds Yahoo's market cap in each listing's own currency, so
KRW and JPY names are on a different scale from the rest. Each non-USD name is
divided by the spot rate from Yahoo (`KRW=X` is KRW per USD), and the result is
written to the `ai_market_cap` table the universe screen reads.

    uv run sources/market_caps.py     (from py/)
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from core import db as cache_db
from sources import universe, yahoo


def fx_per_usd(currencies: set[str]) -> dict[str, float]:
    """Units of each currency per US dollar. Raises if a rate is missing."""
    rates = {"USD": 1.0}
    foreign = sorted(c for c in currencies if c != "USD")
    if foreign:
        quotes = yahoo.cmd_quote(",".join(f"{c}=X" for c in foreign))["quotes"]
        for q in quotes:
            px = q.get("last_trade")
            if px:
                rates[q["symbol"][:-2]] = float(px)
    missing = set(foreign) - rates.keys()
    if missing:
        raise RuntimeError(f"no FX rate from Yahoo for {sorted(missing)}")
    return rates


def build() -> list[tuple]:
    """Rows for ai_market_cap: ticker, currency, cap in listing currency, rate, cap in USD."""
    path = universe.data_dir("profiles") / "profiles.parquet"
    con = cache_db._open(True)
    try:
        raw = con.execute(
            "SELECT ticker, market_cap, currency FROM read_parquet(?) "
            "WHERE market_cap IS NOT NULL AND currency IS NOT NULL",
            [str(path)],
        ).fetchall()
    finally:
        con.close()
    rates = fx_per_usd({ccy for _, _, ccy in raw})
    return [
        (t, ccy, float(cap), rates[ccy], float(cap) / rates[ccy])
        for t, cap, ccy in raw
    ]


def write(rows: list[tuple]) -> None:
    asof = dt.date.today()
    con = cache_db._open(False)  # retries while another process holds the write lock
    try:
        con.execute(
            "CREATE OR REPLACE TABLE ai_market_cap ("
            " ticker VARCHAR PRIMARY KEY, currency VARCHAR, market_cap_local DOUBLE,"
            " fx_per_usd DOUBLE, market_cap_usd DOUBLE, as_of DATE)"
        )
        con.executemany(
            "INSERT INTO ai_market_cap VALUES (?, ?, ?, ?, ?, ?)",
            [(*r, asof) for r in rows],
        )
    finally:
        con.close()


def main() -> None:
    argparse.ArgumentParser(description="Market cap per universe name in USD.").parse_args()
    rows = build()
    write(rows)
    top = sorted(rows, key=lambda r: -r[4])[:5]
    print(f"ai_market_cap: {len(rows)} names")
    for t, ccy, _, rate, usd in top:
        print(f"  {t:12} {ccy}  rate {rate:>10.2f}  ${usd / 1e9:8.1f}bn")
    sys.exit(0)


if __name__ == "__main__":
    main()
