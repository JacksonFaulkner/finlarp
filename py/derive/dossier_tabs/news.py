"""Dossier tab: News & catalysts. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Blocks, in order:
  live headlines   Yahoo news search, pulled now (fails soft: a text block says why)
  8-K items        every signal tier, last EVENT_DAYS; the 2.02 earnings dates are left to the earnings tab
  company news    ROIC articles (roic_news.NEWS), last NEWS_DAYS, newest NEWS_MAX
  catalyst pages   tui fixtures catalyst_pages.json entries whose `tickers` contain t (internal, curated)
  tweets           tweet calendar posts naming t, last TWEET_DAYS, linked to the post

catalysts.json has no ticker field (its labels are free text, e.g. "MRVL FQ3"), so it is not matched.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

from derive import tweet_calendar
from derive.dossier import Filings, _is_new, archive, src
from sources import roic_news, sec_events, yahoo_live

NY = ZoneInfo("America/New_York")
EVENT_DAYS = 365
NEWS_DAYS = 730
NEWS_MAX = 100
TWEET_DAYS = 365
TWEET_MAX = 50
LIVE_MAX = 10
CATALYST_PAGES = Path(__file__).resolve().parents[3] / "tui" / "src" / "screens" / "fixtures" / "catalyst_pages.json"
CATALYST_PAGES_LABEL = "tui/src/screens/fixtures/catalyst_pages.json"


def _clip(s: str | None, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _filing_src(e: dict, F: Filings) -> dict:
    """The filing itself: the index/primary doc from the filings table; internal only if no CIK is known."""
    url = F.doc_url(e["accn"]) or (archive(F.cik, e["accn"], e.get("primary_doc")) if F.cik else None)
    label = f"{e['form']} {e['filed']} item {e['item'] or '-'}"
    return src(label, url, **({} if url else {"internal": True}))


# ---- 8-K items -------------------------------------------------------------

def _event_rows(events: list[dict], F: Filings) -> list[dict]:
    rows = []
    for e in events:
        if e.get("item") in sec_events.EARNINGS_ITEMS:  # earnings dates are owned by the earnings tab
            continue
        rows.append({"cells": [str(e["filed"]), e.get("item") or "-", e.get("signal") or "",
                               e.get("label") or e.get("form") or ""],
                     "new": _is_new(e["filed"]), "src": _filing_src(e, F)})
    return rows


def _event_block(t: str, F: Filings) -> dict | None:
    if not sec_events.EVENTS.exists():
        return None
    rows = _event_rows(sec_events.recent_events(t, EVENT_DAYS, "low"), F)
    if not rows:
        return None
    return {"type": "table", "title": f"8-K items, last {EVENT_DAYS} days (all signal tiers; 2.02 dates on the earnings tab)",
            "cols": ["filed", "item", "signal", "what"], "rows": rows}


# ---- company news (ROIC) -----------------------------------------------------

def _news_rows(articles: list[dict]) -> list[dict]:
    rows = []
    for a in articles:
        d = str(a["published_at"])[:10]
        title = a.get("title") or ""
        url = a.get("url")
        rows.append({"cells": [d, a.get("site") or "", _clip(title, 120), _clip(a.get("snippet"), 160)],
                     "new": _is_new(d),
                     "src": src(f"{a.get('site') or 'news'} · {d}", url, **({} if url else {"internal": True}))})
    return rows


def _fetch_news(t: str, today: date) -> tuple[list[dict], int]:
    """(newest articles within NEWS_DAYS, total matching). Empty when the store has no file."""
    if not roic_news.NEWS.exists():
        return [], 0
    since = (today - timedelta(days=NEWS_DAYS)).isoformat()
    con = duckdb.connect()
    try:
        where = f"FROM read_parquet('{roic_news.NEWS}') WHERE ticker = ? AND published_at >= ?::TIMESTAMP"
        total = con.execute(f"SELECT count(*) {where}", [t, since]).fetchone()[0]
        cur = con.execute(f"SELECT published_at, site, title, url, left(text, 200) AS snippet {where} "
                          f"ORDER BY published_at DESC LIMIT {NEWS_MAX}", [t, since])
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()], total
    finally:
        con.close()


def _news_block(t: str, today: date) -> dict | None:
    articles, total = _fetch_news(t, today)
    if not articles:
        return None
    return {"type": "table", "title": f"Company news, last {NEWS_DAYS // 365} years (newest {len(articles)} of {total})",
            "cols": ["date", "source", "headline", "snippet"], "rows": _news_rows(articles)}


# ---- catalyst pages (curated fixtures) ----------------------------------------

def _catalyst_blocks(t: str, pages: list[dict]) -> list[dict]:
    mine = [p for p in pages if t in (p.get("tickers") or "").split()]
    if not mine:
        return []
    rows, texts = [], []
    for p in sorted(mine, key=lambda p: p.get("date") or ""):
        s = src(f"{CATALYST_PAGES_LABEL} · {p.get('label')}", None, internal=True)
        rows.append({"cells": [p.get("date") or "?", p.get("label") or "", p.get("when") or "", p.get("status") or ""],
                     "src": s})
        setup = next((tab.get("text") for tab in p.get("tabs") or [] if tab.get("name") == "Setup"), None)
        if setup:
            texts.append({"type": "text", "text": f"{p.get('label')}: {setup}", "src": s})
    return [{"type": "table", "title": f"Catalyst pages naming {t}", "cols": ["date", "event", "when", "status"],
             "rows": rows}, *texts]


def _load_pages() -> list[dict]:
    try:
        return json.loads(CATALYST_PAGES.read_text())
    except (OSError, ValueError):
        return []


# ---- tweet calendar ------------------------------------------------------------

def _tweet_rows(tweets: list[dict], t: str, today: date) -> tuple[list[dict], int]:
    """(newest TWEET_MAX rows, total posts naming t in the window)."""
    since = (today - timedelta(days=TWEET_DAYS)).isoformat()
    hits = []
    for w in tweets:
        if (w.get("d") or "") < since:
            continue
        k = next((k for k in w.get("k") or [] if k and k[0] == t), None)
        if k is None:
            continue
        hits.append((w, k[1] if len(k) > 1 else None))
    hits.sort(key=lambda h: (h[0].get("d") or "", h[0].get("t") or ""), reverse=True)
    rows = []
    for w, stance in hits[:TWEET_MAX]:
        d, hh, url = w.get("d") or "", w.get("h") or "?", w.get("u") or None
        rows.append({"cells": [d, f"{w.get('t') or ''} ET", f"@{hh}",
                               f"{stance:+g}" if isinstance(stance, (int, float)) else "—",
                               _clip(w.get("x"), 200)],
                     "new": _is_new(d),
                     "src": src(f"@{hh} · {d} {w.get('t') or ''} ET", url, **({} if url else {"internal": True}))})
    return rows, len(hits)


def _tweet_block(t: str, today: date) -> dict | None:
    try:
        cal = json.loads(tweet_calendar.load())
    except (OSError, ValueError):
        return None
    rows, total = _tweet_rows(cal.get("tweets") or [], t, today)
    if not rows:
        return None
    return {"type": "table", "title": f"Tweet calendar posts naming ${t}, last {TWEET_DAYS} days ({total} posts, newest {len(rows)} shown)",
            "cols": ["date", "time", "who", "stance", "tweet"], "rows": rows}


# ---- live headlines ----------------------------------------------------------------

def _live_block(t: str, now: datetime) -> dict:
    stamp = now.strftime("%Y-%m-%d %H:%M ET")
    try:
        items = yahoo_live.news(t, count=LIVE_MAX)
    except Exception as e:  # network or Yahoo schema change: say so, keep the rest of the tab
        return {"type": "text", "text": f"Live Yahoo headlines unavailable at {stamp}: {type(e).__name__}: {e}",
                "src": src("Yahoo Finance news search (live)", None, error=True)}
    rows = [{"cells": [i.get("time") or "", i.get("publisher") or "", _clip(i.get("title"), 160)],
             "src": src(f"Yahoo Finance · {i.get('publisher') or 'news'}",
                        i.get("link") or f"https://finance.yahoo.com/quote/{t}/news")}
            for i in items]
    return {"type": "table", "title": f"Live headlines from Yahoo, pulled {stamp}",
            "cols": ["time", "publisher", "headline"], "rows": rows}


# ---- section --------------------------------------------------------------------------

def section(t: str, con, F, prof: dict | None) -> dict | None:
    now = datetime.now(NY)
    today = now.date()
    blocks = [_live_block(t, now)]
    for block in (_event_block(t, F), _news_block(t, today)):
        if block:
            blocks.append(block)
    blocks += _catalyst_blocks(t, _load_pages())
    tweets = _tweet_block(t, today)
    if tweets:
        blocks.append(tweets)
    return {"id": "news", "title": "News & catalysts", "blocks": blocks}
