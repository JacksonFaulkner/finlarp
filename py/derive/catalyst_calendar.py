"""Events for the catalyst calendar (`fl events`, <leader>ve), generated from the local filings data. Prints one JSON list.

    uv run python py/derive/catalyst_calendar.py

The TUI runs this when the calendar opens, then groups by day in memory. Each event:

    d     ET date (YYYY-MM-DD)     t     time (HH:MM) or null     l  label
    x     detail or null           tone  bull | bear | risk | neutral
    est   true for a projected date (the TUI prefixes the label with "~")
    u     link or null

Sources (local, no network):
  - earnings releases: 8-K item 2.02 filing dates (sec_events.earnings_dates, one per release day)
  - next report, projected: last release + one quarter, per ticker, when it falls in the window
  - high-signal 8-K items (the same tier the dossier's events tab uses)

Window: PAST_DAYS back, AHEAD_DAYS forward from today.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import duckdb

from sources import sec_events, universe

PAST_DAYS = 730
AHEAD_DAYS = 365
QUARTER_DAYS = 91
DETAIL_MAX = 200


def build(today: date | None = None) -> list[dict]:
    today = today or date.today()
    since = today - timedelta(days=PAST_DAYS)
    horizon = today + timedelta(days=AHEAD_DAYS)
    names = {r["ticker"]: r["name"] for r in universe.rows()}
    con = duckdb.connect()
    ev = sec_events.EVENTS
    earn = list(sec_events.EARNINGS_ITEMS)
    out: list[dict] = []

    releases = con.execute(
        f"SELECT DISTINCT ticker, filed FROM '{ev}' WHERE item IN ? AND form = '8-K' AND filed >= ?", [earn, since]
    ).fetchall()
    for t, filed in releases:
        out.append({"d": str(filed), "t": None, "l": f"{t} earnings", "x": names.get(t), "tone": "neutral",
                    "est": False, "u": None})

    last = con.execute(
        f"SELECT ticker, max(filed) FROM '{ev}' WHERE item IN ? AND form = '8-K' GROUP BY ticker", [earn]
    ).fetchall()
    for t, filed in last:
        nxt = filed + timedelta(days=QUARTER_DAYS)
        if today <= nxt <= horizon:
            out.append({"d": str(nxt), "t": None, "l": f"{t} earnings", "x": f"projected from {filed}",
                        "tone": "neutral", "est": True, "u": None})

    items = con.execute(
        f"SELECT ticker, filed, item, label, description FROM '{ev}' "
        "WHERE signal = 'high' AND filed >= ? AND item NOT IN ?", [since, earn]
    ).fetchall()
    for t, filed, item, label, desc in items:
        detail = (desc or "").strip()[:DETAIL_MAX] or None
        out.append({"d": str(filed), "t": None, "l": f"{t} 8-K {item}: {label}", "x": detail, "tone": "risk",
                    "est": False, "u": None})

    out.sort(key=lambda e: (e["d"], e["l"]))
    return out


if __name__ == "__main__":
    print(json.dumps(build()))
