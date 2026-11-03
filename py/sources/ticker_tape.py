"""Movers for the home screen's ticker tape: AI-universe names trading on heavy
volume with a real price move, from Yahoo quotes. JSON on stdout.

A name qualifies when today's volume is at least VOLUME_X times Yahoo's 10-day
average and its move is at least MOVE_PCT either way. Qualifiers are ranked by
volume ratio times the size of the move, and the top TOP are kept.

Outside the regular session each mover also carries its extended-hours move:
the pre-market print (PM) before the open, otherwise the last after-hours print
(AH), which Yahoo keeps through the night and the weekend. Both are measured
against the last regular close. A name whose extended-hours move is at least
EXT_MOVE_PCT qualifies on that alone (still needing its volume fields), and the
extended move adds to the size of the move when ranking.

    uv run sources/ticker_tape.py     (from py/)
"""

from __future__ import annotations

import datetime as dt
import json

from core import db as cache_db
from sources import yahoo

VOLUME_X = 1.5
MOVE_PCT = 2.0
TOP = 30
EXT_MOVE_PCT = 5.0


def extended(q: dict) -> tuple[str, float] | None:
    """The quote's extended-hours move as (label, pct), or None in the regular
    session or when Yahoo has no print newer than the regular close."""
    state = q.get("market_state")
    if state in (None, "REGULAR"):
        return None
    reg_t = q.get("regular_time") or 0

    def fresh(pct, t):
        return pct is not None and (t is None or t >= reg_t)

    pre, post = q.get("pre_change_pct"), q.get("post_change_pct")
    if state in ("PRE", "PREPRE") and fresh(pre, q.get("pre_time")):
        return "PM", pre
    if fresh(post, q.get("post_time")):
        return "AH", post
    return None


def universe_tickers() -> list[str]:
    con = cache_db._open(True)
    try:
        rows = con.execute(
            "SELECT ticker FROM ai_universe WHERE eligible IS DISTINCT FROM false ORDER BY ticker"
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def movers(quotes: list[dict]) -> list[dict]:
    """Quotes from yahoo.cmd_quote (with volume fields) -> the movers, biggest first."""
    out = []
    for q in quotes:
        vol, avg = q.get("volume"), q.get("avg_volume_10d")
        pct, price = q.get("change_close_pct"), q.get("last_trade")
        if not (vol and avg and price) or pct is None:
            continue
        ratio = vol / avg
        ext = extended(q)
        ext_pct = ext[1] if ext else 0.0
        day = ratio >= VOLUME_X and abs(pct) >= MOVE_PCT
        if not (day or abs(ext_pct) >= EXT_MOVE_PCT):
            continue
        out.append((ratio * (abs(pct) + abs(ext_pct)), {
            "ticker": q["symbol"],
            "price": round(price, 2),
            "pct": round(pct, 2),
            "ratio": round(ratio, 2),
            "volume": int(vol),
            "ext_label": ext[0] if ext else None,
            "ext_pct": round(ext_pct, 2) if ext else None,
        }))
    out.sort(key=lambda r: -r[0])
    return [row for _, row in out[:TOP]]


def main() -> None:
    tickers = universe_tickers()
    quotes = yahoo.cmd_quote(",".join(tickers))["quotes"]
    print(json.dumps({
        "asof": dt.datetime.now().isoformat(timespec="minutes"),
        "checked": len(quotes),
        "movers": movers(quotes),
    }))


if __name__ == "__main__":
    main()
