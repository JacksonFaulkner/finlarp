"""E*TRADE option chain snapshots for the US universe, one parquet per run.

    uv run --env-file ../.env python sources/etrade_options.py snapshot                 # whole universe
    uv run --env-file ../.env python sources/etrade_options.py snapshot NBIS MRVL       # just these
    uv run --env-file ../.env python sources/etrade_options.py snapshot --max-days 45 --strikes 30

Each run writes <DATA_ROOT>/options/etrade/date=YYYY-MM-DD/<HHMMSS>.parquet: one row per contract
(calls and puts side by side as separate rows) with quote, volume, open interest and greeks. The
chain endpoint has no history, so coverage starts at the first run; run it after the close to catch
the OCC open-interest update. Read-only. Needs a cached E*TRADE token (see etrade_live.REAUTH).
"""
from __future__ import annotations

import argparse
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import duckdb
import pandas as pd

from sources import etrade_live as el
from sources import pq, universe

OUT = universe.DATA_ROOT / "options" / "etrade"
PLAIN = re.compile(r"[A-Z]{1,5}")
RETRIES = 4
ET = ZoneInfo("America/New_York")


class Throttle:
    """At most `rate` requests per second across all workers."""

    def __init__(self, rate: float):
        self.gap, self.next, self.lock = 1.0 / rate, 0.0, threading.Lock()

    def wait(self) -> None:
        with self.lock:
            now = time.monotonic()
            self.next = max(self.next, now) + self.gap
            delay = self.next - self.gap - now
        if delay > 0:
            time.sleep(delay)


def tickers() -> list[str]:
    return sorted({s["ticker"] for s in universe.rows()
                   if s["region"] == "US" and s["kind"] != "foreign" and PLAIN.fullmatch(s["ticker"])})


def get(sess, th: Throttle, path: str, params: dict) -> dict:
    for i in range(RETRIES):
        th.wait()
        try:
            return el._get(sess, path, params)
        except el.NotAuthed:
            raise
        except RuntimeError as e:
            retry = any(f"HTTP {c}" in str(e) for c in (429, 500, 502, 503, 504))
            if not retry or i == RETRIES - 1:
                raise
            time.sleep(2 ** i)
    return {}


def leg(sym: str, exp: date, spot, side: dict, snap_ts: datetime) -> dict:
    g = side.get("OptionGreeks") or {}
    return {
        "snap_ts": snap_ts, "ticker": sym, "expiry": exp, "type": side.get("optionType"),
        "strike": side.get("strikePrice"), "osi": side.get("osiKey"), "spot": spot,
        "bid": side.get("bid"), "ask": side.get("ask"), "bid_size": side.get("bidSize"),
        "ask_size": side.get("askSize"), "last": side.get("lastPrice"), "net_change": side.get("netChange"),
        "volume": side.get("volume"), "open_interest": side.get("openInterest"),
        "itm": side.get("inTheMoney") == "y",
        "quote_ts": datetime.fromtimestamp(side["timeStamp"], timezone.utc) if side.get("timeStamp") else None,
        "iv": g.get("iv"), "delta": g.get("delta"), "gamma": g.get("gamma"),
        "theta": g.get("theta"), "vega": g.get("vega"), "rho": g.get("rho"),
    }


def one_ticker(sess, th: Throttle, sym: str, max_days: int, strikes: int, snap_ts: datetime) -> list[dict]:
    ex = get(sess, th, "/v1/market/optionexpiredate.json", {"symbol": sym, "expiryType": "ALL"})
    dates = (ex.get("OptionExpireDateResponse") or {}).get("ExpirationDate") or []
    today, rows = date.today(), []
    for d in dates:
        exp = date(d["year"], d["month"], d["day"])
        if not 0 <= (exp - today).days <= max_days:
            continue
        p = {"symbol": sym, "expiryYear": exp.year, "expiryMonth": exp.month, "expiryDay": exp.day,
             "chainType": "CALLPUT", "includeWeekly": "true", "skipAdjusted": "true"}
        if strikes:
            p["noOfStrikes"] = strikes
        r = get(sess, th, "/v1/market/optionchains.json", p).get("OptionChainResponse") or {}
        for pair in r.get("OptionPair") or []:
            for k in ("Call", "Put"):
                if pair.get(k):
                    rows.append(leg(sym, exp, r.get("nearPrice"), pair[k], snap_ts))
    return rows


def snapshot(syms: list[str], max_days: int, strikes: int, workers: int, rate: float) -> None:
    sess, th = el.session(), Throttle(rate)
    snap_ts = datetime.now(timezone.utc)
    rows: list[dict] = []
    failed: dict[str, str] = {}
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(one_ticker, sess, th, s, max_days, strikes, snap_ts): s for s in syms}
        for n, f in enumerate(as_completed(futs), 1):
            s = futs[f]
            try:
                rows += f.result()
            except el.NotAuthed:
                sys.exit(el.REAUTH)
            except Exception as e:  # noqa: BLE001
                failed[s] = str(e)[:120]
            if n % 25 == 0 or n == len(syms):
                print(f"  {n}/{len(syms)} tickers, {len(rows):,} contracts, {time.time() - t0:.0f}s", flush=True)
    if not rows:
        sys.exit(f"no contracts returned; {len(failed)} tickers failed")
    dest_dir = OUT / f"date={snap_ts.astimezone(ET).date()}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{snap_ts:%H%M%S}.parquet"
    con = duckdb.connect()
    con.register("chain", pd.DataFrame(rows))
    pq.copy_atomic(con, "SELECT * FROM chain ORDER BY ticker, expiry, strike, type", dest,
                   "FORMAT parquet, COMPRESSION zstd")
    print(f"wrote {len(rows):,} contracts for {len(syms) - len(failed)} tickers to {dest}")
    for s, e in sorted(failed.items())[:10]:
        print(f"  failed {s}: {e}")
    if failed:
        print(f"  {len(failed)} tickers failed in total")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("snapshot")
    sp.add_argument("tickers", nargs="*", help="default: whole US universe")
    sp.add_argument("--max-days", type=int, default=60, help="expiries within this many days")
    sp.add_argument("--strikes", type=int, default=30, help="strikes around spot per expiry; 0 = all")
    sp.add_argument("--workers", type=int, default=4)
    sp.add_argument("--rate", type=float, default=5.0, help="max requests per second, all workers")
    a = ap.parse_args()
    syms = [t.upper() for t in a.tickers] or tickers()
    snapshot(syms, a.max_days, a.strikes, a.workers, a.rate)


if __name__ == "__main__":
    main()
