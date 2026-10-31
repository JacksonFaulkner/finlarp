"""Yahoo Finance data client: quotes + screener, JSON on stdout.

No auth needed for chart/quote lookups. The screener endpoint requires a
crumb, obtained via a throwaway cookie+crumb handshake (cached in-memory
per invocation, cheap enough to redo each run).

Usage:
    uv run sources/yahoo.py quote AAPL,MSFT
    uv run sources/yahoo.py screen --sector Technology --industry "Semiconductors" --top 25
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import requests

from core import db
from core.paths import YAHOO_CRUMB_PATH

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# The crumb+cookie handshake (fc.yahoo.com + getcrumb) is ~1s of sequential
# network RTT — redoing it on every invocation was the single biggest chunk
# of screener latency. Cache it; crumbs are long-lived (cookie expiry, not a
# short TTL), so a generous cache window is safe and a stale one just gets a
# 401 that triggers one fresh handshake.
CRUMB_CACHE_PATH = YAHOO_CRUMB_PATH
CRUMB_CACHE_TTL_SECONDS = 12 * 60 * 60


def new_session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def _fetch_crumb(session: requests.Session) -> tuple[str, dict]:
    session.get("https://fc.yahoo.com", timeout=10)
    resp = session.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10)
    resp.raise_for_status()
    return resp.text, requests.utils.dict_from_cookiejar(session.cookies)


def get_crumb(session: requests.Session, refresh: bool = False) -> str:
    """Cached crumb (+ its cookies onto session); refresh=True after a 401
    drops the cache and does the handshake again."""
    if refresh:
        CRUMB_CACHE_PATH.unlink(missing_ok=True)
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


# Yahoo marks each quote with the session it reflects; the session fields
# say which price is live and what it is measured against.
SESSIONS = {"PRE": "pre", "PREPRE": "pre", "REGULAR": "regular", "POST": "post", "POSTPOST": "post"}


def parse_quotes(payload: dict) -> list[dict]:
    """v7 quote -> one row per symbol. `last_trade`, `change_close` and `change_close_pct`
    are the regular session (last close against the close before it). `session_price` and
    `session_change_pct` are the live pre- or post-market print, measured against the last
    regular close. In the regular session they repeat the regular fields. Yahoo prints
    pre-market volume as 0 for most names, so a pre-market print can be a single trade."""
    rows = []
    for q in (payload.get("quoteResponse") or {}).get("result") or []:
        session = SESSIONS.get(q.get("marketState"), "closed")
        if session == "pre":
            price, pct = q.get("preMarketPrice"), q.get("preMarketChangePercent")
        elif session == "post":
            price, pct = q.get("postMarketPrice"), q.get("postMarketChangePercent")
        else:
            price, pct = q.get("regularMarketPrice"), q.get("regularMarketChangePercent")
        rows.append({
            "symbol": q.get("symbol"),
            "last_trade": q.get("regularMarketPrice"),
            "change_close": q.get("regularMarketChange"),
            "change_close_pct": q.get("regularMarketChangePercent"),
            "previous_close": q.get("regularMarketPreviousClose"),
            "session": session,
            "session_price": price,
            "session_change_pct": pct,
        })
    return rows


def cmd_quote(symbols: str) -> dict:
    session = new_session()
    syms = [s for s in symbols.split(",") if s]
    url = "https://query2.finance.yahoo.com/v7/finance/quote"
    rows = []
    for i in range(0, len(syms), 50):
        chunk = ",".join(syms[i:i + 50])
        resp = session.get(url, params={"symbols": chunk, "crumb": get_crumb(session)}, timeout=15)
        if resp.status_code == 401:
            resp = session.get(url, params={"symbols": chunk, "crumb": get_crumb(session, refresh=True)}, timeout=15)
        resp.raise_for_status()
        rows.extend(parse_quotes(resp.json()))
    return {"quotes": rows}


def cmd_history(symbol: str, range_: str, interval: str, max_age_hours: float | None = None) -> dict:
    ttl = db.DEFAULT_TTL_SECONDS if max_age_hours is None else max_age_hours * 3600
    cached = db.get_cached_history(symbol, range_, interval, ttl)
    if cached is not None:
        return {"symbol": symbol, "points": cached}

    session = new_session()
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


def parse_top_holdings(payload: dict, fetched_on: str) -> list[dict]:
    """quoteSummary topHoldings -> fund_holdings rows. Yahoo lists only the top 10, so these
    weights are the fund's top-10 share, not the whole fund."""
    result = (payload.get("quoteSummary") or {}).get("result") or []
    if not result:
        return []
    holdings = (result[0].get("topHoldings") or {}).get("holdings") or []
    rows = []
    for h in holdings:
        ticker = (h.get("symbol") or "").strip().upper()
        weight = (h.get("holdingPercent") or {}).get("raw")
        if not ticker or weight is None:
            continue
        rows.append({"ticker": ticker, "name": h.get("holdingName") or ticker, "weight": float(weight), "fetched_on": fetched_on})
    return rows


def cmd_holdings(fund: str) -> dict:
    """Top holdings of one fund, stored in fund_holdings (replacing the last pull)."""
    from datetime import date

    session = new_session()
    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{fund}"
    resp = session.get(url, params={"modules": "topHoldings", "crumb": get_crumb(session)}, timeout=15)
    if resp.status_code == 401:
        resp = session.get(url, params={"modules": "topHoldings", "crumb": get_crumb(session, refresh=True)}, timeout=15)
    resp.raise_for_status()
    rows = parse_top_holdings(resp.json(), date.today().isoformat())
    stored = db.put_fund_holdings(fund, rows)
    return {"fund": fund, "holdings": stored, "weight": round(sum(r["weight"] for r in rows), 4)}


def _screen_request(session: requests.Session, crumb: str, body: dict) -> dict:
    resp = session.post(
        "https://query2.finance.yahoo.com/v1/finance/screener",
        params={"crumb": crumb},
        json=body,
        timeout=15,
    )
    if resp.status_code == 401:  # stale crumb: let cmd_screen refresh + retry
        return {"finance": {"error": "401 Unauthorized"}}
    resp.raise_for_status()
    return resp.json()


def cmd_screen(sector: str | None, industry: str | None, top: int) -> dict:
    session = new_session()
    crumb = get_crumb(session)

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
        crumb = get_crumb(session, refresh=True)
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
    history_p.add_argument("--max-age", type=float, default=None, help="reuse the cache if younger than this many hours")

    universe_p = sub.add_parser("universe")
    universe_sub = universe_p.add_subparsers(dest="universe_cmd", required=True)
    universe_sub.add_parser("groups")
    members_p = universe_sub.add_parser("members")
    members_p.add_argument("level", choices=["primary", "sub", "region"])
    members_p.add_argument("category")
    universe_sub.add_parser("reload")
    holdings_p = universe_sub.add_parser("holdings", help="top holdings of each fund (default: every etf in the universe)")
    holdings_p.add_argument("tickers", nargs="*")

    args = parser.parse_args()

    if args.cmd == "quote":
        output = cmd_quote(args.symbols)
    elif args.cmd == "screen":
        output = cmd_screen(args.sector, args.industry, args.top)
    elif args.cmd == "history":
        output = cmd_history(args.symbol, args.range_, args.interval, args.max_age)
    elif args.cmd == "universe":
        from core import db

        if args.universe_cmd == "groups":
            output = {"groups": db.universe_groups()}
        elif args.universe_cmd == "members":
            output = {"members": db.universe_members(args.level, args.category)}
        elif args.universe_cmd == "holdings":
            funds = args.tickers or db.etf_tickers()
            output = {"funds": [cmd_holdings(f) for f in funds]}
        else:
            output = db.load_universe(force=True)
    else:
        print(f"unknown command: {args.cmd}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(output))


if __name__ == "__main__":
    main()
