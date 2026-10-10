"""Intraday volume / price snapshot from Yahoo 1-minute bars.

    bars(sym)                       [{t, open, high, low, close, volume}] oldest first, completed bars only
    snapshot(sym, window=39)        volume, pace vs the day, VWAP, hi/lo for the last `window` minutes

The bar still forming is dropped: Yahoo reports it with partial (often zero)
volume, which skews both the window total and the day pace.

    uv run sources/intraday.py NBIS AEHR            # last 39 minutes
    uv run sources/intraday.py NBIS --window 15 --json
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime

from sources import yahoo

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
BAR_SECONDS = 60
BAR_META_TOLERANCE_PCT = 2.0  # forming bar + feed lag stay well under this


def fetch(symbol: str, interval: str = "1m", range_: str = "1d", session=None) -> dict:
    session = session or yahoo.new_session()
    resp = session.get(CHART_URL.format(symbol), params={"range": range_, "interval": interval}, timeout=10)
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(result.get("timestamp") or []):
        row = {k: (quote[k][i] if i < len(quote.get(k) or []) else None) for k in ("open", "high", "low", "close", "volume")}
        if row["close"] is None:
            continue
        row["t"] = t
        out.append(row)
    return {"meta": result["meta"], "bars": out}


def bars(symbol: str, session=None, now: float | None = None) -> tuple[list[dict], dict]:
    """Completed 1-minute bars plus Yahoo's meta block."""
    data = fetch(symbol, session=session)
    now = time.time() if now is None else now
    done = [b for b in data["bars"] if b["t"] + BAR_SECONDS <= now]
    return done, data["meta"]


def snapshot(symbol: str, window: int = 39, session=None, now: float | None = None) -> dict:
    done, meta = bars(symbol, session=session, now=now)
    if not done:
        return {"symbol": symbol, "error": "no completed bars"}
    # by clock, not bar count: Yahoo omits minutes with no trades, so thin names have gaps
    end = done[-1]["t"] + BAR_SECONDS
    win = [b for b in done if b["t"] >= end - window * 60]
    vol = lambda rows: sum(b["volume"] or 0 for b in rows)
    day_vol, win_vol = vol(done), vol(win)
    # pace per clock minute; day denominator is the elapsed session, gaps included
    day_pace = day_vol / ((end - done[0]["t"]) / BAR_SECONDS)
    win_pace = win_vol / window
    vwap = sum(b["close"] * (b["volume"] or 0) for b in done) / day_vol if day_vol else None
    prev = meta.get("chartPreviousClose")
    last = win[-1]["close"]
    return {
        "symbol": symbol,
        "window_start": end - window * 60,
        "window_end": end,
        "bars": len(win),
        "window_volume": win_vol,
        "window_per_min": round(win_pace),
        "day_volume": day_vol,
        "day_per_min": round(day_pace),
        "pace_vs_day": round(win_pace / day_pace, 2) if day_pace else None,
        "window_open": win[0]["open"] if win[0]["open"] is not None else win[0]["close"],
        "last": last,
        "window_high": max(b["high"] for b in win if b["high"] is not None),
        "window_low": min(b["low"] for b in win if b["low"] is not None),
        "day_high": max(b["high"] for b in done if b["high"] is not None),
        "day_low": min(b["low"] for b in done if b["low"] is not None),
        "vwap": round(vwap, 4) if vwap else None,
        "prev_close": prev,
        "chg_vs_prev_pct": round((last / prev - 1) * 100, 2) if prev else None,
        "meta_volume": meta.get("regularMarketVolume"),
        "bars_vs_meta_pct": _pct_diff(day_vol, meta.get("regularMarketVolume")),
        "top_bars": [(b["t"], b["volume"]) for b in sorted(done, key=lambda b: -(b["volume"] or 0))[:3]],
    }


def _pct_diff(bar_sum: int, meta_vol: int | None) -> float | None:
    return round((bar_sum / meta_vol - 1) * 100, 2) if meta_vol else None


def _hm(ts: int) -> str:
    return datetime.fromtimestamp(ts).astimezone().strftime("%H:%M")


def _warn(s: dict) -> list[str]:
    """Bars summing above Yahoo's own day volume means bad prints in the 1m feed.
    Bars below it is normal after the close (the closing auction is not in 1m bars)."""
    diff = s["bars_vs_meta_pct"]
    if diff is None or diff <= BAR_META_TOLERANCE_PCT:
        return []
    spikes = ", ".join(f"{_hm(t)}={v:,}" for t, v in s["top_bars"])
    return [f"  WARN     1m bars sum {diff:+.1f}% vs Yahoo day volume ({s['meta_volume']:,}); biggest bars: {spikes}"]


def render(s: dict) -> str:
    if "error" in s:
        return f"{s['symbol']}: {s['error']}"
    above = "above" if s["vwap"] and s["last"] >= s["vwap"] else "below"
    return "\n".join(
        [
            f"{s['symbol']}  {_hm(s['window_start'])}-{_hm(s['window_end'])} ({s['bars']} bars with trades)",
            f"  volume   {s['window_volume']:,}  ({s['window_per_min']:,}/min; day {s['day_per_min']:,}/min; pace {s['pace_vs_day']}x)",
            f"  price    {s['window_open']:.2f} -> {s['last']:.2f}  window {s['window_low']:.2f}-{s['window_high']:.2f}"
            f"  day {s['day_low']:.2f}-{s['day_high']:.2f}",
            f"  vwap     {s['vwap']}  (last is {above})   vs prev close {s['chg_vs_prev_pct']}%",
            f"  day vol  {s['day_volume']:,}",
        ]
        + _warn(s)
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Intraday volume / price snapshot from Yahoo 1-minute bars")
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--window", type=int, default=39, help="minutes of clock time")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    session = yahoo.new_session()
    snaps = [snapshot(s.upper(), args.window, session=session) for s in args.symbols]
    print(json.dumps(snaps, indent=2) if args.json else "\n\n".join(render(s) for s in snaps))


if __name__ == "__main__":
    main()
