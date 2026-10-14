"""Live Yahoo Finance reads for the MCP server: what the local snapshot can't see.

The pulled dataset ends at the last completed session; these answer "today",
"premarket", and "what's the news" straight from Yahoo's public endpoints.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sources import yahoo

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
NY = ZoneInfo("America/New_York")


def _chart(session, symbol: str, range_: str, interval: str, pre_post: bool = False) -> dict:
    resp = session.get(
        CHART_URL.format(symbol),
        params={"range": range_, "interval": interval, "includePrePost": str(pre_post).lower()},
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    bars = []
    for i, t in enumerate(result.get("timestamp") or []):
        row = {k: (quote[k][i] if i < len(quote.get(k) or []) else None) for k in ("open", "high", "low", "close", "volume")}
        if row["close"] is not None:
            row["t"] = t
            bars.append(row)
    return {"meta": result["meta"], "bars": bars}


def _pct(a: float | None, b: float | None) -> float | None:
    return round((a / b - 1) * 100, 2) if a and b else None


def _et(ts: int) -> str:
    return datetime.fromtimestamp(ts, NY).strftime("%Y-%m-%d %H:%M ET")


def live(symbol: str) -> dict:
    """Current price, today's move, volume vs 20-session average, pre/post-market move, trend."""
    s = yahoo.new_session()
    daily = _chart(s, symbol, "3mo", "1d")
    intra = _chart(s, symbol, "1d", "1m", pre_post=True)
    meta = daily["meta"]
    days = daily["bars"]
    # before the open, the last daily bar is the previous session, not today
    reg_start = meta.get("currentTradingPeriod", {}).get("regular", {}).get("start")
    has_today = bool(days) and (not reg_start or days[-1]["t"] >= reg_start)
    today = days[-1] if has_today else {}
    prior = days[:-1] if has_today else days
    # chartPreviousClose is the close before the chart's first bar (~3mo ago here), not yesterday's
    prev_close = prior[-1]["close"] if prior else meta.get("previousClose")
    avg20 = sum(b["volume"] or 0 for b in prior[-20:]) / max(len(prior[-20:]), 1) if prior else None
    ib = intra["bars"]
    last_bar = ib[-1] if ib else None
    # Yahoo marks regular hours in meta.currentTradingPeriod; everything outside is pre/post
    reg = meta.get("currentTradingPeriod", {}).get("regular", {})
    ext = [b for b in ib if reg and not (reg["start"] <= b["t"] < reg["end"])]
    pre = [b for b in ext if b["t"] < reg["start"]] if reg else []
    post = [b for b in ext if b["t"] >= reg["end"]] if reg else []
    return {
        "symbol": symbol,
        "as_of": _et(last_bar["t"] + 60) if last_bar else None,
        "last": last_bar["close"] if last_bar else meta.get("regularMarketPrice"),
        "regular_close_or_price": meta.get("regularMarketPrice"),
        "prev_close": prev_close,
        "day_change_pct": _pct(meta.get("regularMarketPrice"), prev_close),
        "day_open": today.get("open"),
        "day_high": meta.get("regularMarketDayHigh"),
        "day_low": meta.get("regularMarketDayLow"),
        "day_volume": meta.get("regularMarketVolume"),
        "avg_volume_20d": round(avg20) if avg20 else None,
        "relative_volume": round(meta["regularMarketVolume"] / avg20, 2) if avg20 and meta.get("regularMarketVolume") else None,
        "premarket": {
            "last": pre[-1]["close"], "vs_prev_close_pct": _pct(pre[-1]["close"], prev_close),
            "volume": sum(b["volume"] or 0 for b in pre),
        } if pre else None,
        "postmarket": {
            "last": post[-1]["close"], "vs_prev_close_pct": _pct(post[-1]["close"], prev_close),
            "volume": sum(b["volume"] or 0 for b in post),
        } if post else None,
        "change_5d_pct": _pct(days[-1]["close"], days[-6]["close"]) if len(days) > 5 else None,
        "change_1m_pct": _pct(days[-1]["close"], days[-22]["close"]) if len(days) > 21 else None,
        "fifty_two_week": [meta.get("fiftyTwoWeekLow"), meta.get("fiftyTwoWeekHigh")],
        "currency": meta.get("currency"),
    }


def history(symbol: str, range_: str = "1mo", interval: str = "1d", pre_post: bool = False, max_bars: int = 400) -> dict:
    data = _chart(yahoo.new_session(), symbol, range_, interval, pre_post)
    bars = data["bars"][-max_bars:]
    for b in bars:
        b["time"] = _et(b.pop("t"))
    return {"symbol": symbol, "range": range_, "interval": interval, "n": len(bars), "bars": bars}


def news(symbol: str, count: int = 8) -> list[dict]:
    resp = yahoo.new_session().get(
        SEARCH_URL, params={"q": symbol, "newsCount": count, "quotesCount": 0}, timeout=10
    )
    resp.raise_for_status()
    return [
        {
            "title": n.get("title"),
            "publisher": n.get("publisher"),
            "time": _et(n["providerPublishTime"]) if n.get("providerPublishTime") else None,
            "link": n.get("link"),
        }
        for n in resp.json().get("news", [])
    ]
