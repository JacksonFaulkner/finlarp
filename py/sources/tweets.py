"""Tweets pulled by jobs/pull_tweets.py (raw JSONL), flattened to Parquet.

    raw/<handle>.jsonl  ->  tweets.parquet        one row per tweet (deduped by id)
                            tweet_tickers.parquet one row per (tweet, cashtag)

`tweets.text` is the full text (long "note" tweets are expanded). Tickers come
from X's own cashtag entities, flagged `in_universe` when they match the stock
universe. Name/theme matching (e.g. "SK Hynix", "HBM") is not done here.

CLI:  uv run python sources/tweets.py ingest
      uv run python sources/tweets.py show TICKER [DAYS]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import duckdb

from sources import pq, universe

DIR = universe.data_dir("tweets")
RAW = DIR
TWEETS = DIR / "tweets.parquet"
TICKERS = DIR / "tweet_tickers.parquet"


def _row(r: dict) -> dict:
    note = (r.get("noteTweet") or {}).get("text")
    ents = r.get("entities") or {}
    a = r.get("author") or {}
    return {
        "id": str(r["id"]),
        "handle": (a.get("username") or "").lower(),
        "author_name": a.get("name"),
        "author_followers": a.get("followers"),
        "created_at": parsedate_to_datetime(r["createdAt"]).astimezone(timezone.utc).replace(tzinfo=None),
        "text": note or r.get("text") or "",
        "type": r.get("type"),
        "is_reply": bool(r.get("isReply")),
        "is_retweet": bool(r.get("isRetweet")),
        "is_quote": bool(r.get("isQuoteStatus")),
        "reply_to": r.get("inReplyToUsername"),
        "conversation_id": r.get("conversationId"),
        "likes": r.get("likeCount"),
        "retweets": r.get("retweetCount"),
        "replies": r.get("replyCount"),
        "quotes": r.get("quoteCount"),
        "views": r.get("viewCount"),
        "bookmarks": r.get("bookmarkCount"),
        "media_count": len(r.get("media") or []),
        "urls": json.dumps([u.get("expanded_url") or u.get("url") for u in ents.get("urls") or []]),
        "url": r.get("url"),
        "lang": r.get("lang"),
        "_cashtags": sorted({s["text"].upper() for s in ents.get("symbols") or [] if s.get("text")}),
    }


def ingest() -> dict:
    rows: dict[str, dict] = {}
    for f in sorted(RAW.glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                row = _row(json.loads(line))
                rows[row["id"]] = row
    if not rows:
        raise SystemExit(f"no raw tweets in {RAW}")
    in_u = {s["ticker"].upper() for s in universe.stocks()}
    tweets = [{k: v for k, v in r.items() if k != "_cashtags"} for r in rows.values()]
    tickers = [
        {"tweet_id": r["id"], "handle": r["handle"], "created_at": r["created_at"], "ticker": t, "in_universe": t in in_u}
        for r in rows.values() for t in r["_cashtags"]
    ]
    con = duckdb.connect()
    _write(con, tweets, TWEETS, TWEET_TYPES)
    _write(con, tickers, TICKERS, TICKER_TYPES)
    return {"tweets": len(tweets), "ticker_mentions": len(tickers), "handles": len({r["handle"] for r in tweets})}


TWEET_TYPES = {
    "id": "VARCHAR", "handle": "VARCHAR", "author_name": "VARCHAR", "author_followers": "BIGINT",
    "created_at": "TIMESTAMP", "text": "VARCHAR", "type": "VARCHAR", "is_reply": "BOOLEAN",
    "is_retweet": "BOOLEAN", "is_quote": "BOOLEAN", "reply_to": "VARCHAR", "conversation_id": "VARCHAR",
    "likes": "BIGINT", "retweets": "BIGINT", "replies": "BIGINT", "quotes": "BIGINT", "views": "BIGINT",
    "bookmarks": "BIGINT", "media_count": "INTEGER", "urls": "VARCHAR", "url": "VARCHAR", "lang": "VARCHAR",
}
TICKER_TYPES = {
    "tweet_id": "VARCHAR", "handle": "VARCHAR", "created_at": "TIMESTAMP", "ticker": "VARCHAR", "in_universe": "BOOLEAN",
}


def _write(con: duckdb.DuckDBPyConnection, rows: list[dict], dest, types: dict[str, str]) -> None:
    """rows -> parquet with explicit column types (via an ndjson temp file, no pandas needed)."""
    tmp = dest.with_name(dest.name + ".ndjson")
    tmp.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows))
    try:
        cols = ", ".join(f"'{k}': '{v}'" for k, v in types.items())
        pq.copy_atomic(con, f"SELECT * FROM read_json('{tmp}', format='newline_delimited', columns={{{cols}}}) ORDER BY created_at", dest)
    finally:
        tmp.unlink(missing_ok=True)


def query(ticker: str | None = None, handle: str | None = None, since: str | None = None, until: str | None = None,
          q: str | None = None, min_likes: int = 0, include_replies: bool = False, order: str = "recent",
          limit: int = 25) -> dict:
    """Filtered tweet search; shared by the MCP tool and (later) the TUI.

    Returns {"tweets": [...], "coverage": {...}}. Coverage lets the caller judge whether the
    query answered the question: total matches vs returned, the span and per-account split of
    the matches, replies left out, and the window the store itself covers."""
    con = duckdb.connect()
    where, args = ["NOT is_retweet"], []
    if ticker:
        where.append("id IN (SELECT tweet_id FROM read_parquet(?) WHERE ticker = ?)")
        args += [str(TICKERS), ticker.upper().lstrip("$")]
    if handle:
        where.append("handle = ?")
        args.append(handle.lower().lstrip("@"))
    if since:
        where.append("created_at >= ?::TIMESTAMP")
        args.append(since)
    if until:
        where.append("created_at < ?::TIMESTAMP")
        args.append(until)
    if q:
        where.append("text ILIKE ?")
        args.append(f"%{q}%")
    if min_likes:
        where.append("likes >= ?")
        args.append(min_likes)
    base = f"FROM read_parquet('{TWEETS}') WHERE {' AND '.join(where)}"
    limit = max(1, min(limit, 200))
    shown = base + ("" if include_replies else " AND NOT is_reply")
    order_by = "likes DESC NULLS LAST" if order == "likes" else "created_at DESC"
    cur = con.execute(
        f"SELECT id, handle, created_at, text, likes, retweets, replies, views, is_reply, is_quote, url "
        f"{shown} ORDER BY {order_by} LIMIT {limit}", args)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    total, replies_out, lo, hi = con.execute(
        f"SELECT count(*) FILTER (WHERE {'true' if include_replies else 'NOT is_reply'}), "
        f"count(*) FILTER (WHERE is_reply AND {'false' if include_replies else 'true'}), min(created_at), max(created_at) "
        f"{base}", args).fetchone()
    by_handle = dict(con.execute(
        f"SELECT handle, count(*) {shown} GROUP BY 1 ORDER BY 2 DESC LIMIT 25", args).fetchall())
    s_lo, s_hi, s_n, s_h = con.execute(
        f"SELECT min(created_at), max(created_at), count(*), count(DISTINCT handle) FROM read_parquet('{TWEETS}')").fetchone()
    notes = []
    if total > len(rows):
        notes.append(f"truncated: {len(rows)} of {total} matches returned; raise limit (max 200), narrow since/until, or filter by handle")
    if total == 0 and ticker:
        notes.append("0 cashtag matches: tweets that name the company without $TICKER are not matched; retry with `text`")
    if replies_out:
        notes.append(f"{replies_out} reply tweets also match and were excluded; set include_replies to see them")
    return {
        "tweets": rows,
        "coverage": {
            "matched": total,
            "returned": len(rows),
            "truncated": total > len(rows),
            "matched_span": [lo, hi],
            "by_handle": by_handle,
            "replies_excluded": replies_out,
            "store": {"tweets": s_n, "handles": s_h, "span": [s_lo, s_hi]},
            "notes": notes,
        },
    }


def sources() -> list[dict]:
    """Per-account coverage of the store: tweet count, first/last tweet, followers."""
    cur = duckdb.connect().execute(
        f"SELECT handle, any_value(author_name) AS name, max(author_followers) AS followers, count(*) AS tweets, "
        f"count(*) FILTER (WHERE NOT is_reply AND NOT is_retweet) AS originals, min(created_at) AS first_tweet, max(created_at) AS last_tweet "
        f"FROM read_parquet('{TWEETS}') GROUP BY 1 ORDER BY 4 DESC")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "ingest":
        print(json.dumps(ingest()))
    elif cmd == "show" and len(sys.argv) > 2:
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 14
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        for r in query(ticker=sys.argv[2], since=since, limit=30)["tweets"]:
            print(f"{r['created_at']:%m-%d %H:%M} @{r['handle']:<16} ♥{r['likes']:<5} {r['text'][:140]!r}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
