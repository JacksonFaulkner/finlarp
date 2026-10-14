"""Tweets for the catalyst calendar (`fl events`, <leader>ve): every tweet that names a universe ticker, as one JSON file.

    uv run python py/derive/tweet_calendar.py            # prints the JSON; rebuilds it first when the tweet data is newer
    uv run python py/derive/tweet_calendar.py --rebuild  # force a rebuild

The TUI reads this once, then filters by ticker and groups by day in memory. Each tweet:

    d  ET date (YYYY-MM-DD)     t  ET time (HH:MM)       h  author handle         u  link to the post
    x  text, newlines flattened  l  likes   v  views      r  1 if it is a reply
    k  [[ticker, stance|null], ...]   the universe cashtags it carries; stance is the labelled view
       (-2..2, from tweet_sentiment) or null when the tweet has not been labelled

Retweets are left out. Times are America/New_York because the calendar is about the US market day.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from sources import tweet_sentiment, tweets, universe

OUT = universe.data_dir("tweet_calendar") / "tweet_calendar.json"
TEXT_MAX = 500


def _inputs() -> list:
    return [p for p in (tweets.TWEETS, tweets.TICKERS, tweet_sentiment.OUT) if p.exists()]


def is_stale() -> bool:
    return not OUT.exists() or any(p.stat().st_mtime > OUT.stat().st_mtime for p in _inputs())


def build(tweets_path=None, tickers_path=None, sentiment_path=None) -> dict:
    tweets_path, tickers_path = tweets_path or tweets.TWEETS, tickers_path or tweets.TICKERS
    sentiment_path = Path(tweet_sentiment.OUT if sentiment_path is None else sentiment_path)
    con = duckdb.connect()
    stance = {}
    if sentiment_path.exists():
        stance = {(i, t): s for i, t, s in con.execute(f"SELECT id, ticker, stance FROM read_parquet('{sentiment_path}')").fetchall()}
    rows = con.execute(
        f"""SELECT w.id, strftime(local, '%Y-%m-%d'), strftime(local, '%H:%M'), w.handle, w.text, w.likes, w.views, w.is_reply, w.url,
                   list(DISTINCT t.ticker ORDER BY t.ticker)
            FROM (SELECT *, (created_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/New_York' AS local
                  FROM read_parquet('{tweets_path}') WHERE NOT is_retweet) w
            JOIN read_parquet('{tickers_path}') t ON t.tweet_id = w.id AND t.in_universe
            GROUP BY w.id, local, w.handle, w.text, w.likes, w.views, w.is_reply, w.url
            ORDER BY local""").fetchall()
    out = []
    for tid, d, t, handle, text, likes, views, is_reply, url, tks in rows:
        out.append({"d": d, "t": t, "h": handle, "u": url or "", "l": likes or 0, "v": views or 0, "r": int(bool(is_reply)),
                    "x": " ".join((text or "").split())[:TEXT_MAX], "k": [[k, stance.get((tid, k))] for k in tks]})
    return {"asof": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tz": "America/New_York", "tweets": out}


def load(rebuild: bool = False) -> str:
    """The JSON text, from the cache unless it is stale (or `rebuild`)."""
    if rebuild or is_stale():
        tmp = OUT.with_name(OUT.name + ".part")
        tmp.write_text(json.dumps(build(), ensure_ascii=False, separators=(",", ":")))
        tmp.replace(OUT)
    return OUT.read_text()


def main() -> None:
    sys.stdout.write(load("--rebuild" in sys.argv))


if __name__ == "__main__":
    main()
