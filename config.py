"""Yahoo Finance data client: quotes + screener, JSON on stdout.

No auth needed for chart/quote lookups. The screener endpoint requires a
crumb, obtained via a throwaway cookie+crumb handshake (cached in-memory
per invocation, cheap enough to redo each run).

Usage:
    uv run config.py quote AAPL,MSFT
    uv run config.py screen --sector Technology --industry "Semiconductors" --top 25
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

import db

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# The crumb+cookie handshake (fc.yahoo.com + getcrumb) is ~1s of sequential
# network RTT — redoing it on every invocation was the single biggest chunk
# of screener latency. Cache it; crumbs are long-lived (cookie expiry, not a
# short TTL), so a generous cache window is safe and a stale one just gets a
# 401 that triggers one fresh handshake.
CRUMB_CACHE_PATH = Path(os.path.expanduser("~/.local/share/nvim/yahoo_crumb.json"))
CRUMB_CACHE_TTL_SECONDS = 12 * 60 * 60


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def _fetch_crumb(session: requests.Session) -> tuple[str, dict]:
    session.get("https://fc.yahoo.com", timeout=10)
    resp = session.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10)
    resp.raise_for_status()
    return resp.text, requests.utils.dict_from_cookiejar(session.cookies)


def _crumb(session: requests.Session) -> str:
    if CRUMB_CACHE_PATH.exists():
        cached = json.loads(CRUMB_CACHE_PATH.read_text())
        if time.time() - cached.get("fetched_at", 0) < CRUMB_CACHE_TTL_SECONDS:
            session.cookies.update(cached["cookies"])
            return cached["crumb"]

    crumb, cookies = _fetch_crumb(session)
    CRUMB_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CRUMB_CACHE_PATH.write_text(json.dumps({
        "crumb": crumb,
        "cookies": cookies,
        "fetched_at": time.time(),
    }))
    return crumb


def cmd_quote(symbols: str) -> dict:
    session = _session()
    # /v7/finance/spark batches all symbols into one request (no auth needed),
    # unlike /v8/finance/chart which is one request per symbol — that serial
    # loop was the main source of dashboard-open latency (~400ms/symbol).
    resp = session.get(
        "https://query1.finance.yahoo.com/v7/finance/spark",
        params={"symbols": symbols, "range": "1d", "interval": "1d"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()["spark"]["result"]

    result = []
    for entry in data:
        response = entry.get("response") or [{}]
        meta = response[0].get("meta", {})
        result.append({
            "symbol": meta.get("symbol") or entry.get("symbol"),
            "last_trade": meta.get("regularMarketPrice"),
            "change_close": meta.get("fulldayChange"),
            "change_close_pct": meta.get("fulldayChangePercent"),
            "previous_close": meta.get("chartPreviousClose"),
        })
    return {"quotes": result}


def cmd_history(symbol: str, range_: str, interval: str) -> dict:
    cached = db.get_cached_history(symbol, range_, interval)
    if cached is not None:
        return {"symbol": symbol, "points": cached}

    session = _session()
    resp = session.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"range": range_, "interval": interval},
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    closes = result["indicators"]["quote"][0].get("close") or []
    points = [
        {"t": t, "close": c}
        for t, c in zip(timestamps, closes)
        if c is not None
    ]
    db.put_cached_history(symbol, range_, interval, points)
    return {"symbol": symbol, "points": points}


def _screen_request(session: requests.Session, crumb: str, body: dict) -> dict:
    resp = session.post(
        "https://query2.finance.yahoo.com/v1/finance/screener",
        params={"crumb": crumb},
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def cmd_screen(sector: str | None, industry: str | None, top: int) -> dict:
    session = _session()
    crumb = _crumb(session)

    operands = [{"operator": "eq", "operands": ["region", "us"]}]
    if sector:
        operands.append({"operator": "eq", "operands": ["sector", sector]})
    if industry:
        operands.append({"operator": "eq", "operands": ["industry", industry]})

    body = {
        "size": top,
        "offset": 0,
        "sortField": "intradaymarketcap",
        "sortType": "desc",
        "quoteType": "EQUITY",
        "query": {"operator": "and", "operands": operands},
    }
    data = _screen_request(session, crumb, body)
    if data["finance"].get("error"):
        # Cached crumb/cookies went stale early — refetch once and retry
        # before giving up, instead of failing the whole call.
        CRUMB_CACHE_PATH.unlink(missing_ok=True)
        crumb, cookies = _fetch_crumb(session)
        session.cookies.update(cookies)
        data = _screen_request(session, crumb, body)
        if data["finance"].get("error"):
            raise RuntimeError(data["finance"]["error"])

    quotes = data["finance"]["result"][0]["quotes"]
    result = []
    for q in quotes:
        result.append({
            "symbol": q.get("symbol"),
            "last_trade": q.get("regularMarketPrice"),
            "change_close": q.get("regularMarketChange"),
            "change_close_pct": q.get("regularMarketChangePercent"),
            "market_cap": q.get("marketCap"),
        })
    return {"quotes": result}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    quote_p = sub.add_parser("quote")
    quote_p.add_argument("symbols")

    screen_p = sub.add_parser("screen")
    screen_p.add_argument("--sector")
    screen_p.add_argument("--industry")
    screen_p.add_argument("--top", type=int, default=25)

    history_p = sub.add_parser("history")
    history_p.add_argument("symbol")
    history_p.add_argument("--range", dest="range_", default="6mo")
    history_p.add_argument("--interval", default="1d")

    args = parser.parse_args()

    if args.cmd == "quote":
        output = cmd_quote(args.symbols)
    elif args.cmd == "screen":
        output = cmd_screen(args.sector, args.industry, args.top)
    elif args.cmd == "history":
        output = cmd_history(args.symbol, args.range_, args.interval)
    else:
        print(f"unknown command: {args.cmd}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(output))


if __name__ == "__main__":
    main()
