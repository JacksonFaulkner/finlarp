"""Dossier tab: Earnings & guidance. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Four parts, each sourced:
  - next report date and time, consensus EPS / revenue for it (Yahoo calendarEvents, live)
  - the last N_RELEASES earnings releases (EX-99.1 via sec_earnings): headline revenue and
    EPS, an EPS consensus figure only where the release text states one, and the guidance
    lines extracted from each release
  - report-date history: 8-K item 2.02 filing dates (sec_events.earnings_dates), with the
    gap between reports as a derived value

Guidance vs consensus is not built: guidance is free text whose period and units vary, and
Yahoo gives consensus only for the next report, so there is no reliable join.
Medium/low 8-K items are not shown here (the news tab owns them).
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

from derive.dossier import Filings, _is_new, _money, archive, derived, fragment, src
from sources import sec_earnings, sec_events, yahoo, yahoo_profile

N_RELEASES = 4
N_REPORT_DATES = 12
GUIDANCE_LINES = 14
ET = ZoneInfo("America/New_York")

_BOILER = re.compile(r"undertake no obligation|forward[- ]looking|review or confirm", re.I)
_CONS = re.compile(r"consensus|analysts?['’]? (?:average |mean )?(?:estimates?|expectations?)|"
                   r"street (?:estimates?|expectations?)", re.I)
_AFTER_AMOUNT = re.compile(r"\$\s?(\d+\.\d+)")


def _url(t: str) -> str:
    return f"https://finance.yahoo.com/quote/{quote(t)}/"


def _hl(x: dict | None, eps: bool = False) -> str:
    """{"value": 2.739, "unit": "billion", "ccy": "$"} -> "$2.739 billion"; per-share values
    keep two decimals ("$0.80"); "—" when absent."""
    if not x or x.get("value") is None:
        return "—"
    unit = x.get("unit")
    unit = "" if not unit or unit == "table" else f" {unit}"
    num = f"{x['value']:.2f}" if eps else f"{x['value']:,}"
    return f"{x.get('ccy') or ''}{num}{unit}"


def _headline(r: dict) -> dict:
    h = r.get("headline")
    if isinstance(h, str):
        return json.loads(h) if h else {}
    return h or {}


def _consensus_eps(text: str) -> tuple[str, str] | None:
    """(amount, line) for an EPS consensus figure the release states, e.g.
    "...above consensus of $0.80 per share". Such sentences are rare; the
    amount must follow the consensus wording within the same line."""
    for line in (text or "").split("\n"):
        if not line or _BOILER.search(line):
            continue
        for m in _CONS.finditer(line):
            win = line[max(0, m.start() - 90): m.end() + 90]
            if not re.search(r"per share|\bEPS\b|earnings", win, re.I):
                continue
            amt = _AFTER_AMOUNT.search(line[m.end(): m.end() + 60])
            if amt:
                return amt.group(1), line[:400]
    return None


def _releases(t: str, con) -> list[dict]:
    path = sec_earnings.REL_DIR / f"{t}.parquet"
    if not path.exists():
        return []
    cur = con.execute(f"SELECT * FROM read_parquet('{path}') ORDER BY filed DESC LIMIT {N_RELEASES}")
    names = [d[0] for d in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def _release_blocks(t: str, con, F: Filings) -> list[dict]:
    rels = []
    for r in _releases(t, con):
        cik = r.get("cik") or F.cik
        if not cik or not r.get("accn"):
            continue
        hl = _headline(r)
        rels.append({
            "r": r, "hl": hl, "new": _is_new(r["filed"]), "cons": _consensus_eps(r.get("text") or ""),
            "doc": archive(cik, r["accn"], r.get("doc_name")),
            "base": f"{r['form']} {r['filed']} {r.get('doc_name') or ''}".strip(),
        })
    if not rels:
        return []

    has_cons = any(x["cons"] for x in rels)
    cols = ["filed", "revenue", "EPS non-GAAP", "EPS GAAP"] + (["EPS consensus"] if has_cons else [])
    rows = []
    for x in rels:
        hl = x["hl"]
        anchor = next((hl[k]["snippet"] for k in ("revenue", "eps_nongaap", "eps_gaap") if (hl.get(k) or {}).get("snippet")), None)
        if x["cons"]:
            anchor = anchor or x["cons"][1]
        cells = [str(x["r"]["filed"]), _hl(hl.get("revenue")), _hl(hl.get("eps_nongaap"), True),
                 _hl(hl.get("eps_gaap"), True)]
        if has_cons:
            cells.append(f"${x['cons'][0]} (release text)" if x["cons"] else "—")
        label = f"{x['base']} · headline figures" + (f" \"{anchor[:70]}\"" if anchor else "")
        rows.append({"cells": cells, "new": x["new"], "src": src(label, fragment(x["doc"], anchor))})
    blocks = [{"type": "table", "title": "Last releases (headline figures)", "cols": cols, "rows": rows}]

    for x in rels:
        g = x["r"].get("guidance") or []
        if not g:
            continue
        blocks.append({"type": "table", "title": f"Guidance as written in release · filed {x['r']['filed']}",
                       "cols": ["line"], "rows": [
            {"cells": [s.lstrip("•· ").strip()], "new": x["new"], "src": src(x["base"], fragment(x["doc"], s))}
            for s in g[:GUIDANCE_LINES]]})
    return blocks


def _report_blocks(t: str, con, F: Filings) -> list[dict]:
    dates = sec_events.earnings_dates(t)  # distinct 8-K item 2.02 filing dates, oldest first
    if not dates:
        return []
    accn_on = {}
    for filed, accn in con.execute(
            f"SELECT filed, accn FROM '{sec_events.EVENTS}' WHERE ticker = ? AND item IN ? AND form = '8-K' "
            "ORDER BY filed, accn", [t, list(sec_events.EARNINGS_ITEMS)]).fetchall():
        accn_on.setdefault(filed, accn)

    def filing(d) -> dict | None:
        url = F.doc_url(accn_on[d]) if d in accn_on else None
        return src(f"8-K {d} · item 2.02", url) if url else None

    rows = []
    pairs = list(zip(dates, [None] + dates[:-1]))[-N_REPORT_DATES:][::-1]
    for d, prior in pairs:
        here = filing(d)
        if not here:
            continue
        cell, row_src = "—", here
        prior_src = filing(prior) if prior else None
        if prior_src:
            gap = (d - prior).days
            cell = str(gap)
            row_src = derived(f"days between 8-K item 2.02 filings {prior} and {d}",
                              f"{d} − {prior} = {gap} days", [here, prior_src])
        rows.append({"cells": [str(d), cell], "new": _is_new(d), "src": row_src})
    if not rows:
        return []
    return [{"type": "table", "title": "Report dates (8-K item 2.02)", "cols": ["filed", "days since prior report"],
             "rows": rows}]


def _next_report(t: str) -> list[dict]:
    """kv rows for the next report from Yahoo calendarEvents. Live call: a failure
    returns an 'unavailable' row rather than raising."""
    url = _url(t)
    try:
        res = yahoo_profile.fetch(yahoo.new_session(), t, "calendarEvents")
    except Exception as e:  # network, throttling, or a changed response: the tab still renders
        return [{"label": "Next earnings", "value": "unavailable",
                 "src": src(f"Yahoo Finance calendarEvents · request failed ({type(e).__name__})", url)}]
    if not res:
        return [{"label": "Next earnings", "value": "unavailable",
                 "src": src("Yahoo Finance calendarEvents · no result", url)}]
    earn = (res.get("calendarEvents") or {}).get("earnings") or {}
    entries = [x for x in (earn.get("earningsDate") or []) if x.get("raw") is not None]
    if not entries:
        return [{"label": "Next earnings", "value": "not listed by Yahoo",
                 "src": src("Yahoo Finance calendarEvents · earnings", url)}]

    first = datetime.fromtimestamp(entries[0]["raw"], ET)
    day = entries[0].get("fmt") or first.date().isoformat()
    if len(entries) > 1:
        day = f"{day} to {entries[-1].get('fmt') or '?'}"
    when = "time not listed" if first.hour == 0 else first.strftime("%H:%M ET")
    est = " (estimate)" if earn.get("isEarningsDateEstimate") else ""
    rows = [{"label": "Next earnings", "value": f"{day}, {when}{est}",
             "src": src("Yahoo Finance calendarEvents · earningsDate", url)}]

    avg, low, high = (earn.get(k) or {} for k in ("earningsAverage", "earningsLow", "earningsHigh"))
    if avg.get("raw") is not None:
        rng = f" (range ${low['raw']:.2f} to ${high['raw']:.2f})" if low.get("raw") is not None and high.get("raw") is not None else ""
        rows.append({"label": "Consensus EPS, next report", "value": f"${avg['raw']:.2f}{rng}",
                     "src": src("Yahoo Finance calendarEvents · earningsAverage", url)})
    rev = earn.get("revenueAverage") or {}
    if rev.get("raw") is not None:
        rows.append({"label": "Consensus revenue, next report", "value": _money(rev["raw"]),
                     "src": src("Yahoo Finance calendarEvents · revenueAverage", url)})
    return rows


def _safe(fn, *a) -> list:
    """A part that fails (missing parquet, bad row) drops out; the others still render."""
    try:
        return fn(*a) or []
    except Exception:
        return []


def section(t: str, con, F: Filings, prof: dict | None) -> dict | None:
    blocks = []
    nxt = _safe(_next_report, t)
    if nxt:
        blocks.append({"type": "kv", "rows": nxt})
    blocks += _safe(_release_blocks, t, con, F)
    blocks += _safe(_report_blocks, t, con, F)
    if not blocks:
        return None
    return {"id": "earnings", "title": "Earnings & guidance", "blocks": blocks}
