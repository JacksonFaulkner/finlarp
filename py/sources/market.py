"""Market-direction inputs for the CANSLIM M letter.

    history(sym)          daily closes + volume (Yahoo chart API)
    distribution_days()   O'Neil distribution days on an index
    breadth(tickers)      share of a ticker list above its 50 / 200-day MA

Breadth is cached in breadth.json for 6 hours: it costs one chart request per
ticker. History here bypasses the DuckDB cache (core.db) on purpose, since
that cache stores no volume and breadth runs on a thread pool.

    uv run sources/market.py        # print the index trends and universe breadth
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor

from core import db
from sources import universe, yahoo

CACHE_TTL_SECONDS = 6 * 3600
DIST_WINDOW = 25  # sessions an O'Neil distribution day stays counted
DIST_DROP_PCT = -0.2  # a down day this deep on higher volume is distribution
WORKERS = 8
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"


def history(symbol: str, range_: str = "1y", session=None) -> list[dict]:
    """[{t, close, volume}] oldest first; sessions without a close are dropped."""
    session = session or yahoo.new_session()
    resp = session.get(CHART_URL.format(symbol), params={"range": range_, "interval": "1d"}, timeout=10)
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    closes, volumes = quote.get("close") or [], quote.get("volume") or []
    return [
        {"t": t, "close": c, "volume": volumes[i] if i < len(volumes) else None}
        for i, (t, c) in enumerate(zip(result.get("timestamp") or [], closes))
        if c is not None
    ]


def sma(points: list[dict], window: int) -> float | None:
    if len(points) < window:
        return None
    return sum(p["close"] for p in points[-window:]) / window


def distribution_days(points: list[dict], window: int = DIST_WINDOW) -> list[dict]:
    """Down days of at least DIST_DROP_PCT on volume above the prior session,
    within the last `window` sessions. Each hit carries the numbers behind it."""
    out = []
    start = max(1, len(points) - window)
    for i in range(start, len(points)):
        prev, cur = points[i - 1], points[i]
        if not (prev["close"] and prev.get("volume") and cur.get("volume")):
            continue
        pct = (cur["close"] / prev["close"] - 1) * 100
        if pct <= DIST_DROP_PCT and cur["volume"] > prev["volume"]:
            out.append({"t": cur["t"], "prev_t": prev["t"], "pct": pct, "volume": cur["volume"], "prev_volume": prev["volume"],
                        "close": cur["close"], "prev_close": prev["close"]})
    return out


def _one(symbol: str) -> dict | None:
    try:
        pts = history(symbol)
    except Exception:
        return None
    if not pts:
        return None
    ma50, ma200 = sma(pts, 50), sma(pts, 200)
    return {"ticker": symbol, "close": pts[-1]["close"], "t": pts[-1]["t"], "ma50": ma50, "ma200": ma200,
            "n": len(pts)}


def _cache_path():
    return universe.data_dir("market") / "breadth.json"


def breadth(tickers: list[str]) -> dict:
    """{as_of, n, failed, rows: [{ticker, close, t, ma50, ma200, n}]}. Rows
    hold the per-ticker numbers so each can be cited."""
    key = sorted(tickers)
    path = _cache_path()
    if path.exists():
        cached = json.loads(path.read_text())
        if cached.get("key") == key and time.time() - cached.get("fetched_at", 0) < CACHE_TTL_SECONDS:
            return cached["data"]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        rows = list(pool.map(_one, key))
    good = [r for r in rows if r]
    data = {"n": len(good), "failed": len(key) - len(good), "rows": good}
    if len(good) >= 0.8 * len(key):  # don't cache an outage
        path.write_text(json.dumps({"key": key, "fetched_at": time.time(), "data": data}))
    return data


def pct_above(rows: list[dict], field: str) -> tuple[int, int]:
    """(count above, count with data) for `field` in {"ma50", "ma200"}."""
    have = [r for r in rows if r.get(field)]
    return sum(1 for r in have if r["close"] > r[field]), len(have)


if __name__ == "__main__":
    db.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    for sym in ("SPY", "QQQ", "IWM", "RSP"):
        pts = history(sym)
        print(sym, f"{pts[-1]['close']:.2f}", f"ma50={sma(pts, 50)}", f"dist={len(distribution_days(pts))}")
    b = breadth([s["ticker"] for s in universe.rows()])
    for f in ("ma50", "ma200"):
        up, n = pct_above(b["rows"], f)
        print(f"above {f}: {up}/{n}")
