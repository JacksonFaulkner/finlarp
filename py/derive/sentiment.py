"""Queries over the labelled tweets (sources/tweet_sentiment.py), shared by the MCP tools.

    ticker(t)          one stock: how many views, who holds them, net stance, trend, keywords, recent examples
    leaders(by)        tickers ranked by mentions, bullishness, bearishness, disagreement or momentum
    price_targets(t)   price targets extracted from tweets, set against the last close

A "view" is a label where the tweet is substantively about the stock (focus primary or secondary) and somebody
holds a position on it (view_holder is not none). Passing mentions and bare announcements are not views; they stay
in `mentions`. Stance is -2 bearish .. +2 bullish; `agreement` is the share of the three labelling passes whose
stance had the same sign as the final one.

Every function returns {"...": rows, "coverage": {...}}. Coverage says what the store holds and `notes` says what to
do next, in the same spirit as the `tweets` tool: read it before concluding anything.
"""
from __future__ import annotations

import duckdb

from sources import tweet_sentiment, tweets, universe

LABELS = tweet_sentiment.OUT
META = tweet_sentiment.META
TWEETS = tweets.TWEETS
TICKERS = tweets.TICKERS
BARS = universe.DATA_ROOT / "market" / "databento" / "bars_1d" / "*.parquet"

VIEW = "s.focus <> 'passing_mention' AND s.view_holder <> 'none'"
SKEW_NOTE = ("the followed accounts are overwhelmingly bullish (about 9 in 10 views), so read stance relative to other tickers "
             "or to earlier weeks, not relative to zero")


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect()


def _window(since: str | None, until: str | None) -> tuple[str, list]:
    """SQL and args limiting tweets (alias w) to [since, until), UTC dates."""
    sql, args = "", []
    if since:
        sql += " AND w.created_at >= ?::TIMESTAMP"
        args.append(since)
    if until:
        sql += " AND w.created_at < ?::TIMESTAMP"
        args.append(until)
    return sql, args


def _store(con) -> dict:
    n, tw, lo, hi, nt = con.execute(
        f"SELECT count(*), count(DISTINCT s.id), min(w.created_at), max(w.created_at), count(DISTINCT s.ticker) "
        f"FROM read_parquet('{LABELS}') s JOIN read_parquet('{TWEETS}') w ON w.id = s.id").fetchone()
    return {"labels": n, "tweets_labelled": tw, "tickers": nt, "span": [lo, hi]}


def _rows(con, sql: str, args: list | None = None) -> list[dict]:
    cur = con.execute(sql, args or [])
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def ticker(symbol: str, since: str | None = None, until: str | None = None, min_agreement: float = 0.0,
           holder: str = "", limit: int = 15) -> dict:
    """One stock's labelled tweets. holder narrows the views to author, quoted_analyst or quoted_person."""
    sym = symbol.upper().lstrip("$")
    con = _con()
    win, wargs = _window(since, until)
    hold = " AND s.view_holder = ?" if holder else ""
    base = (f"FROM read_parquet('{LABELS}') s JOIN read_parquet('{TWEETS}') w ON w.id = s.id "
            f"WHERE s.ticker = ? AND s.agreement >= ?{win}")
    args = [sym, min_agreement, *wargs]
    mentions = con.execute(f"SELECT count(*) {base}", args).fetchone()[0]
    view_base = f"{base} AND {VIEW}{hold}"
    vargs = args + ([holder] if holder else [])
    summary = _rows(con, f"""SELECT count(*) "views", count(DISTINCT w.handle) authors,
        count(*) FILTER (WHERE s.stance > 0) bullish, count(*) FILTER (WHERE s.stance < 0) bearish,
        count(*) FILTER (WHERE s.stance = 0) neutral, round(avg(s.stance), 2) avg_stance,
        round(avg(s.agreement), 3) avg_agreement, count(*) FILTER (WHERE s.agreement < 1) contested,
        count(*) FILTER (WHERE s.price_target IS NOT NULL) with_price_target {view_base}""", vargs)[0]
    by_holder = _rows(con, f"""SELECT s.view_holder, count(*) "views", round(avg(s.stance), 2) avg_stance {view_base}
        GROUP BY 1 ORDER BY 2 DESC""", vargs)
    by_claim = _rows(con, f"""SELECT s.claim, count(*) "views" {view_base} GROUP BY 1 ORDER BY 2 DESC LIMIT 6""", vargs)
    daily = _rows(con, f"""SELECT w.created_at::DATE AS "date", count(*) "views", round(avg(s.stance), 2) net_stance {view_base}
        GROUP BY 1 ORDER BY 1""", vargs)
    authors = _rows(con, f"""SELECT w.handle, count(*) "views", round(avg(s.stance), 2) avg_stance,
        count(*) FILTER (WHERE s.stance < 0) bearish {view_base} GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 10""", vargs)
    recent = _rows(con, f"""SELECT w.created_at::DATE AS "date", w.handle, s.stance, s.view_holder, s.claim, s.horizon,
        s.agreement, s.price_target, s.evidence, left(replace(w.text, chr(10), ' '), 220) AS "text", w.likes, w.url
        {view_base} ORDER BY w.created_at DESC LIMIT {max(1, min(limit, 100))}""", vargs)
    meta_ids = f"SELECT s.id {view_base}"
    keywords = [r[0] for r in con.execute(
        f"""SELECT kw FROM (SELECT unnest(m.keywords) kw FROM read_parquet('{META}') m
            WHERE m.id IN ({meta_ids})) GROUP BY 1 ORDER BY count(*) DESC, 1 LIMIT 10""", vargs).fetchall()]
    themes = [r[0] for r in con.execute(
        f"""SELECT th FROM (SELECT unnest(m.themes) th FROM read_parquet('{META}') m
            WHERE m.id IN ({meta_ids})) GROUP BY 1 ORDER BY count(*) DESC, 1 LIMIT 5""", vargs).fetchall()]
    unlabelled = con.execute(
        f"""SELECT count(DISTINCT t.tweet_id) FROM read_parquet('{TICKERS}') t JOIN read_parquet('{TWEETS}') w ON w.id = t.tweet_id
            WHERE t.ticker = ? AND t.tweet_id NOT IN (SELECT id FROM read_parquet('{LABELS}') WHERE ticker = ?){win}""",
        [sym, sym, *wargs]).fetchone()[0]
    notes = []
    if mentions == 0:
        notes.append(f"no labelled tweets name {sym}: check the symbol, widen since/until, or look at `tweets` for unlabelled ones")
    elif summary["views"] == 0:
        notes.append("the tweets that mention it are passing mentions or carry no view; see mentions vs views")
    elif summary["bullish"] / summary["views"] > 0.85:
        notes.append(SKEW_NOTE)
    if summary["views"] and summary["contested"] / summary["views"] > 0.3:
        notes.append("over 30% of the views are contested across passes; pass min_agreement=1 for the unanimous ones")
    if unlabelled:
        notes.append(f"{unlabelled} more tweets name {sym} but are unlabelled (replies, and tweets after the last labelling run)")
    return {"ticker": sym, "summary": {"mentions": mentions, **summary}, "by_holder": by_holder, "by_claim": by_claim,
            "daily": daily, "top_authors": authors, "keywords": keywords, "themes": themes, "recent": recent,
            "coverage": {"store": _store(con), "unlabelled_tweets": unlabelled, "notes": notes}}


LEADER_ORDER = {  # written on the aggregates themselves: `views` as an alias would clash with the column inside ORDER BY
    "mentions": "count(*) DESC, avg(s.stance) DESC",
    "bullish": "avg(s.stance) DESC, count(*) DESC",
    "bearish": "count(*) FILTER (WHERE s.stance < 0) DESC, count(*) DESC",
    "contested": "least(count(*) FILTER (WHERE s.stance > 0), count(*) FILTER (WHERE s.stance < 0)) * 1.0 / count(*) DESC, count(*) DESC",
}


def leaders(by: str = "mentions", since: str | None = None, until: str | None = None, min_views: int = 20,
           holder: str = "", limit: int = 20) -> dict:
    """Tickers ranked by `by`: mentions, bullish, bearish, contested (bulls and bears both present) or momentum
    (views in the last 7 days of the window against the 7 before)."""
    if by not in (*LEADER_ORDER, "momentum"):
        return {"error": f"by must be one of {[*LEADER_ORDER, 'momentum']}"}
    con = _con()
    win, wargs = _window(since, until)
    hold = " AND s.view_holder = ?" if holder else ""
    args = [*wargs, *([holder] if holder else [])]
    base = (f"FROM read_parquet('{LABELS}') s JOIN read_parquet('{TWEETS}') w ON w.id = s.id WHERE {VIEW}{win}{hold}")
    limit = max(1, min(limit, 100))
    if by == "momentum":
        rows = _rows(con, f"""WITH x AS (SELECT s.ticker, w.created_at::DATE d, s.stance {base}), m AS (SELECT max(d) mx FROM x)
            SELECT ticker, count(*) FILTER (WHERE d > mx - 7) last7, count(*) FILTER (WHERE d <= mx - 7 AND d > mx - 14) prior7,
              round(avg(stance) FILTER (WHERE d > mx - 7), 2) stance_last7,
              round(avg(stance) FILTER (WHERE d <= mx - 7 AND d > mx - 14), 2) stance_prior7
            FROM x, m GROUP BY 1 HAVING count(*) FILTER (WHERE d > mx - 14) >= {min_views}
            ORDER BY count(*) FILTER (WHERE d > mx - 7) * 1.0 / greatest(count(*) FILTER (WHERE d <= mx - 7 AND d > mx - 14), 1) DESC,
              2 DESC LIMIT {limit}""", args)
    else:
        rows = _rows(con, f"""SELECT s.ticker, count(*) "views", count(DISTINCT w.handle) authors,
            count(*) FILTER (WHERE s.stance > 0) bullish, count(*) FILTER (WHERE s.stance < 0) bearish,
            round(avg(s.stance), 2) avg_stance, round(avg(s.agreement), 3) avg_agreement {base}
            GROUP BY 1 HAVING count(*) >= {min_views} ORDER BY {LEADER_ORDER[by]} LIMIT {limit}""", args)
    notes = [SKEW_NOTE] if by in ("mentions", "bullish") else []
    if not rows:
        notes.append(f"no ticker has {min_views}+ views in this window: lower min_views or widen since/until")
    if by == "momentum":
        notes.append("momentum compares the last 7 days of the data in the window with the 7 before; small counts swing a lot")
    return {"by": by, "tickers": rows, "coverage": {"store": _store(con), "notes": notes}}


def price_targets(symbol: str, since: str | None = None, limit: int = 15) -> dict:
    """Price targets extracted from tweets about one stock, against its last daily close."""
    sym = symbol.upper().lstrip("$")
    con = _con()
    win, wargs = _window(since, None)
    base = (f"FROM read_parquet('{LABELS}') s JOIN read_parquet('{TWEETS}') w ON w.id = s.id "
            f"WHERE s.ticker = ? AND s.price_target IS NOT NULL AND s.price_target > 0{win}")
    args = [sym, *wargs]
    close = None
    try:
        close = con.execute(f"SELECT arg_max(close, ts_event) FROM read_parquet('{BARS}', union_by_name=true) WHERE symbol = ?",
                            [sym]).fetchone()[0]
    except duckdb.Error:
        pass
    summary = _rows(con, f"""SELECT count(*) targets, count(DISTINCT w.handle) authors, round(median(s.price_target), 2) median_target,
        min(s.price_target) low, max(s.price_target) high {base}""", args)[0]
    if close and summary["median_target"]:
        summary["last_close"] = round(close, 2)
        summary["median_implied_upside_pct"] = round(100 * (summary["median_target"] / close - 1), 1)
    rows = _rows(con, f"""SELECT w.created_at::DATE AS "date", w.handle, s.price_target, s.view_holder, s.stance, s.horizon, s.agreement,
        left(replace(w.text, chr(10), ' '), 220) AS "text", w.url {base} ORDER BY w.created_at DESC LIMIT {max(1, min(limit, 100))}""", args)
    if close:
        for r in rows:
            r["implied_upside_pct"] = round(100 * (r["price_target"] / close - 1), 1)
    notes = ["targets are whatever price the labeller found for this ticker in the tweet; horizon is usually unspecified and a "
             "price quoted for comparison can be picked up by mistake, so read `text` before relying on one"]
    if close is None:
        notes.append("no daily bars for this symbol: implied upside is unavailable")
    if not summary["targets"]:
        notes.append(f"no tweet in the window gives a price target for {sym}")
    return {"ticker": sym, "summary": summary, "targets": rows, "coverage": {"store": _store(con), "notes": notes}}
