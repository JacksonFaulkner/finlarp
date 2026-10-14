"""Company news (title, link and a ~200 character snippet) from ROIC.ai (`/v2/company/news/{ticker}`).

    raw/<ticker>.jsonl  ->  news.parquet     one row per (ticker, article url), deduped

The free plan allows 5 requests/minute and 2 years of history (Individual 5, Professional 40); a request
reaching further back is refused with a 403 naming the limit, so the puller clamps its window to
`--years` and stops cleanly if the API disagrees. Re-running only fetches what is newer than the last
pull of that ticker.

CLI:  uv run python sources/roic_news.py pull IREN SERV [--since 2025-01-01] [--until 2026-10-12] [--years 2]
      uv run python sources/roic_news.py pull --universe [--max-pages 30]
      uv run python sources/roic_news.py ingest
      uv run python sources/roic_news.py show TICKER [DAYS]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone

import duckdb
import requests

from sources import keys, pq, universe

DIR = universe.data_dir("news")
RAW = DIR / "raw"
STATE = DIR / "state.json"
NEWS = DIR / "news.parquet"
BASE = "https://api.roic.ai/v2/company/news"
PAGE = 20  # limit=100 came back empty in testing; 20 is reliable
TYPES = {
    "id": "VARCHAR", "ticker": "VARCHAR", "published_at": "TIMESTAMP", "title": "VARCHAR",
    "site": "VARCHAR", "url": "VARCHAR", "text": "VARCHAR", "text_chars": "INTEGER",
}


class HistoryLimit(Exception):
    """The plan does not reach back as far as the requested window."""


class _Throttle:
    def __init__(self, rpm: float):
        self.gap = 60.0 / rpm
        self.last = 0.0

    def wait(self) -> None:
        if (d := self.last + self.gap - time.monotonic()) > 0:
            time.sleep(d)
        self.last = time.monotonic()


def _get(session: requests.Session, throttle: _Throttle, ticker: str, params: dict, retries: int = 4) -> list[dict]:
    """One page of articles. Never prints the URL: it carries the API key."""
    for attempt in range(retries):
        throttle.wait()
        try:
            r = session.get(f"{BASE}/{ticker}", params={**params, "apikey": keys.require("ROIC_TOKEN")}, timeout=40)
        except requests.RequestException as e:
            print(f"  {ticker}: {type(e).__name__}, retrying", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 200:
            try:
                data = r.json()
            except ValueError:  # empty body: seen under rate limiting
                time.sleep(15)
                continue
            return data if isinstance(data, list) else []
        if r.status_code == 429:
            time.sleep(30 * (attempt + 1))
            continue
        msg = _error_message(r)
        if r.status_code == 403 and "history" in msg.lower():
            raise HistoryLimit(msg)
        if r.status_code in (402, 401):
            raise SystemExit(f"{r.status_code}: {msg}")
        if r.status_code == 404:
            return []
        print(f"  {ticker}: HTTP {r.status_code} {msg[:120]}", file=sys.stderr)
        return []
    return []


def _error_message(r: requests.Response) -> str:
    try:
        body = r.json()
    except ValueError:
        return r.text[:200]
    err = body.get("error", body) if isinstance(body, dict) else body
    return err.get("message", str(err)) if isinstance(err, dict) else str(err)


def _load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def _save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True))


def _read_raw(ticker: str) -> dict[str, dict]:
    f = RAW / f"{ticker}.jsonl"
    out: dict[str, dict] = {}
    if f.exists():
        for line in f.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                out[row["article_url"]] = row
    return out


def pull_ticker(session: requests.Session, throttle: _Throttle, ticker: str, since: date, until: date,
                max_pages: int) -> tuple[int, int]:
    """Fetch [since, until] newest-first, page by page, until a page comes back short or empty.
    Returns (fetched, new)."""
    seen = _read_raw(ticker)
    before = len(seen)
    fetched = 0
    for page in range(max_pages):
        rows = _get(session, throttle, ticker, {
            "limit": PAGE, "page": page, "date_start": since.isoformat(), "date_end": until.isoformat()})
        fetched += len(rows)
        for row in rows:
            if row.get("article_url"):
                seen[row["article_url"]] = row
        if len(rows) < PAGE:
            break
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{ticker}.jsonl"
    tmp = out.with_name(out.name + ".part")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in seen.values()))
    tmp.replace(out)
    return fetched, len(seen) - before


def pull(tickers: list[str], since: date | None, until: date, years: int, max_pages: int, rpm: float) -> None:
    state = _load_state()
    floor = until - timedelta(days=365 * years - 3)
    session, throttle = requests.Session(), _Throttle(rpm)
    for t in tickers:
        t = t.upper()
        start = since or (date.fromisoformat(state[t]) - timedelta(days=2) if t in state else floor)
        start = max(start, floor)
        try:
            fetched, new = pull_ticker(session, throttle, t, start, until, max_pages)
        except HistoryLimit as e:
            print(f"{t}: {e}")
            raise SystemExit("stopping: lower --years to match the plan") from e
        state[t] = until.isoformat()
        _save_state(state)
        print(f"{t}: {start}..{until} {fetched} fetched, {new} new")


def _row(ticker: str, r: dict) -> dict | None:
    url, ts = r.get("article_url"), r.get("published_date")
    if not url or not ts:
        return None
    published = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if published.tzinfo:
        published = published.astimezone(timezone.utc).replace(tzinfo=None)
    text = r.get("article_text") or ""
    return {
        "id": hashlib.sha1(f"{ticker}|{url}".encode()).hexdigest()[:16],
        "ticker": ticker,
        "published_at": published.isoformat(sep=" "),
        "title": r.get("title"),
        "site": r.get("site") or (re.sub(r"^www\.", "", m.group(1)) if (m := re.match(r"https?://([^/]+)", url)) else None),
        "url": url,
        "text": text,
        "text_chars": len(text),
    }


def ingest() -> dict:
    rows: dict[str, dict] = {}
    for f in sorted(RAW.glob("*.jsonl")):
        ticker = f.stem.upper()
        for line in f.read_text().splitlines():
            if line.strip() and (row := _row(ticker, json.loads(line))):
                rows[row["id"]] = row
    if not rows:
        raise SystemExit(f"no raw news in {RAW}")
    tmp = NEWS.with_name(NEWS.name + ".ndjson")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows.values()))
    try:
        cols = ", ".join(f"'{k}': '{v}'" for k, v in TYPES.items())
        pq.copy_atomic(duckdb.connect(),
                       f"SELECT * FROM read_json('{tmp}', format='newline_delimited', columns={{{cols}}}) "
                       f"ORDER BY ticker, published_at DESC", NEWS)
    finally:
        tmp.unlink(missing_ok=True)
    return {"articles": len(rows), "tickers": len({r["ticker"] for r in rows.values()})}


def query(ticker: str | None = None, since: str | None = None, until: str | None = None, text: str | None = None,
          site: str | None = None, limit: int = 20) -> dict:
    """Filtered article search for the MCP `news` tool. `text` matches the title or the snippet, case-insensitively.
    Returns {"articles": [...], "coverage": {...}}; coverage says what the store holds and what to do next."""
    con = duckdb.connect()
    where, args = ["true"], []
    if ticker:
        where.append("ticker = ?")
        args.append(ticker.upper().lstrip("$"))
    if since:
        where.append("published_at >= ?::TIMESTAMP")
        args.append(since)
    if until:
        where.append("published_at < ?::TIMESTAMP")
        args.append(until)
    if text:
        where.append("(title ILIKE ? OR text ILIKE ?)")
        args += [f"%{text}%"] * 2
    if site:
        where.append("site ILIKE ?")
        args.append(f"%{site}%")
    base = f"FROM read_parquet('{NEWS}') WHERE {' AND '.join(where)}"
    limit = max(1, min(limit, 100))
    cur = con.execute(f"SELECT published_at, ticker, site, title, url, left(text, 300) snippet {base} "
                      f"ORDER BY published_at DESC LIMIT {limit}", args)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    matched, lo, hi = con.execute(f"SELECT count(*), min(published_at), max(published_at) {base}", args).fetchone()
    sites = dict(con.execute(f"SELECT site, count(*) {base} GROUP BY 1 ORDER BY 2 DESC LIMIT 8", args).fetchall())
    n, tk, s_lo, s_hi = con.execute(
        f"SELECT count(*), count(DISTINCT ticker), min(published_at), max(published_at) FROM read_parquet('{NEWS}')").fetchone()
    notes = ["article text here is a snippet of about 200 characters (ROIC's field), not the full article: use the url for the rest"]
    if matched > len(rows):
        notes.append(f"truncated: {len(rows)} of {matched} matches returned; narrow since/until, site or text, or raise limit (max 100)")
    if matched == 0:
        covered = ticker and con.execute(f"SELECT count(*) FROM read_parquet('{NEWS}') WHERE ticker = ?", [ticker.upper().lstrip("$")]).fetchone()[0]
        notes.append(f"{ticker.upper()} has no stored news: it may not have been pulled (sources/roic_news.py pull)" if ticker and not covered
                     else "no article matches: widen the dates or try different words")
    notes.append("the store is a pull, not a live feed (free plan reaches back about 2 years); use live_news for the latest headlines")
    return {"articles": rows, "coverage": {"matched": matched, "returned": len(rows), "truncated": matched > len(rows),
                                            "matched_span": [lo, hi], "by_site": sites,
                                            "store": {"articles": n, "tickers": tk, "span": [s_lo, s_hi]}, "notes": notes}}


def show(ticker: str, days: int) -> None:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    for pub, site, title in duckdb.connect().execute(
            f"SELECT published_at, site, title FROM read_parquet('{NEWS}') WHERE ticker = ? AND published_at >= ?::TIMESTAMP "
            f"ORDER BY published_at DESC LIMIT 40", [ticker.upper(), since]).fetchall():
        print(f"{pub:%Y-%m-%d} {str(site)[:22]:<22} {str(title)[:110]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("tickers", nargs="*")
    p.add_argument("--universe", action="store_true", help="every ticker in the stock universe")
    p.add_argument("--since", type=date.fromisoformat)
    p.add_argument("--until", type=date.fromisoformat, default=date.today() + timedelta(days=1))
    p.add_argument("--years", type=int, default=2, help="history the plan allows (free 2, Individual 5)")
    p.add_argument("--max-pages", type=int, default=25, help="pages of %d articles per ticker per run" % PAGE)
    p.add_argument("--rpm", type=float, default=5, help="requests per minute (free plan 5)")
    sub.add_parser("ingest")
    s = sub.add_parser("show")
    s.add_argument("ticker")
    s.add_argument("days", nargs="?", type=int, default=30)
    a = ap.parse_args()
    if a.cmd == "pull":
        tickers = [x["ticker"] for x in universe.stocks()] if a.universe else a.tickers
        if not tickers:
            raise SystemExit("give tickers or --universe")
        pull(tickers, a.since, a.until, a.years, a.max_pages, a.rpm)
        print(json.dumps(ingest()))
    elif a.cmd == "ingest":
        print(json.dumps(ingest()))
    else:
        show(a.ticker, a.days)


if __name__ == "__main__":
    main()
