"""Dossier tab: Sentiment. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Population: original tweets (no retweets, no replies) that cashtag the ticker. The raw cashtag counts and the labelled
views both use it, so the two numbers agree. The labeller reads originals by default (sources/tweet_sentiment.pending),
but the labelled store also holds labels on reply tweets from earlier runs; those are dropped here and counted in a
coverage row. Windows are UTC: tweets.created_at is UTC-naive.

Aggregates come from one query over the labelled store (tweet_sentiment) joined to tweets and tweet_meta, not from the
derive/sentiment.py helpers, which count reply labels in their views.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from urllib.parse import quote

import duckdb

from derive.dossier import derived, src
from sources import tweet_sentiment, tweets, universe

LABELS = tweet_sentiment.OUT
META = tweet_sentiment.META
TWEETS = tweets.TWEETS
TICKERS = tweets.TICKERS
BARS = universe.DATA_ROOT / "market" / "databento" / "bars_1d" / "*.parquet"
TAB_SRC = "dossier_tabs/sentiment.py"
NEW_DAYS = 7
CONTESTED_SHARE = 0.3  # matches the note in derive/sentiment.py ticker()


def _now() -> datetime:
    """One UTC clock for every window. tweets.created_at is UTC-naive, so the clock is too."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_view(r: dict) -> bool:
    return r["focus"] != "passing_mention" and r["view_holder"] != "none"


def _is_promo(r: dict) -> bool:
    return r.get("tweet_type") == "promo" or r.get("claim") == "promo_shill"


def _avg(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 2) if xs else None


def _stance(rows: list[dict]) -> str:
    return f"{_avg([r['stance'] for r in rows]):+.2f} · {len(rows)} views" if rows else "no views"


# ---- queries ---------------------------------------------------------------


def _raw(con, t: str) -> list[dict]:
    """Every tweet with the cashtag, replies included (the caller filters)."""
    cur = con.execute(
        f"""
        SELECT w.id, w.handle, w.created_at, w.text, w.likes, w.url, w.is_reply
        FROM read_parquet('{TWEETS}') w JOIN read_parquet('{TICKERS}') k ON k.tweet_id = w.id
        WHERE k.ticker = ? AND NOT w.is_retweet ORDER BY w.created_at DESC""",
        [t],
    )
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _labelled(con, t: str) -> list[dict]:
    """Labelled original tweets naming t, one row per (tweet, ticker), with the meta flags."""
    cur = con.execute(
        f"""
        SELECT w.id, w.handle, w.created_at, w.url, w.text, w.likes, s.focus, s.stance, s.view_holder, s.claim,
               s.agreement, s.price_target, m.tweet_type, m.is_repost, m.is_sarcastic, m.themes
        FROM read_parquet('{LABELS}') s
        JOIN read_parquet('{TWEETS}') w ON w.id = s.id
        LEFT JOIN read_parquet('{META}') m ON m.id = s.id
        WHERE s.ticker = ? AND NOT w.is_retweet AND NOT w.is_reply""",
        [t],
    )
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _reply_labels(con, t: str) -> int:
    return con.execute(
        f"""
        SELECT count(*) FROM read_parquet('{LABELS}') s JOIN read_parquet('{TWEETS}') w ON w.id = s.id
        WHERE s.ticker = ? AND w.is_reply""",
        [t],
    ).fetchone()[0]


def _view_counts(con) -> dict[str, int]:
    """Views per ticker over originals, for the rank row."""
    return dict(
        con.execute(f"""
        SELECT s.ticker, count(*) FROM read_parquet('{LABELS}') s JOIN read_parquet('{TWEETS}') w ON w.id = s.id
        WHERE NOT w.is_retweet AND NOT w.is_reply AND s.focus <> 'passing_mention' AND s.view_holder <> 'none'
        GROUP BY 1""").fetchall()
    )


def _last_close(con, t: str) -> float | None:
    try:
        v = con.execute(
            f"SELECT arg_max(close, ts_event) FROM read_parquet('{BARS}', union_by_name=true) WHERE symbol = ?", [t]
        ).fetchone()[0]
    except duckdb.Error:
        return None
    return float(v) if v else None


# ---- section ---------------------------------------------------------------


def section(t: str, con, F, prof: dict | None) -> dict | None:
    t = t.upper()
    if not all(p.exists() for p in (LABELS, META, TWEETS, TICKERS)):
        return None
    raw, lab = _raw(con, t), _labelled(con, t)
    if not raw and not lab:
        return None
    return _build(t, raw, lab, _view_counts(con), _last_close(con, t), _reply_labels(con, t), _now())


def _build(
    t: str,
    raw: list[dict],
    lab: list[dict],
    counts: dict[str, int],
    close: float | None,
    reply_labels: int,
    now: datetime,
) -> dict | None:
    """Pure: the tab from already-read rows. `now` is the UTC clock for every window."""
    ds_url = "https://x.com/search?q=" + quote(f"${t}")
    ds = src(f"labelled tweets and cashtag ${t}, original tweets only (tweet_sentiment, tweets)", ds_url)
    orig = [r for r in raw if not r["is_reply"]]
    replies = [r for r in raw if r["is_reply"]]
    views = [r for r in lab if _is_view(r)]
    if not orig and not lab:
        return None

    def tsrc(r: dict) -> dict:
        return src(f"@{r['handle']} · {r['created_at']:%Y-%m-%d}", r["url"] or ds_url)

    def d(label: str, formula: str, rows: list[dict] | None = None, cap: int = 25) -> dict:
        """Derived value. With rows, the tweets behind it are the inputs (first `cap`, noted in the formula)."""
        if not rows:
            return derived(label, formula, [], ds)
        f = formula if len(rows) <= cap else f"{formula}; first {cap} of {len(rows)} tweets listed"
        return derived(label, f, [tsrc(r) for r in rows[:cap]])

    def within(rows: list[dict], days: int) -> list[dict]:
        cut = now - timedelta(days=days)
        return [r for r in rows if r["created_at"] >= cut]

    blocks = []

    # 1. Labelled views summary and rank
    kv = [
        {
            "label": "Mention volume (labelled tweets naming the cashtag)",
            "value": str(len(lab)),
            "src": d(
                "labelled original tweets naming the cashtag", f"count of labelled original tweets with ${t}", lab
            ),
        }
    ]
    if views:
        s = _stats(views)
        kv += [
            {
                "label": "Views (not a passing mention, someone holds the view)",
                "value": str(s["n"]),
                "src": d("views", f"count where focus <> passing_mention and view_holder <> none, ${t}", views),
            },
            {
                "label": "Bullish / bearish / neutral",
                "value": f"{s['bull']} / {s['bear']} / {s['neu']}",
                "src": d("stance signs of views", f"count of stance >0 / <0 / =0 over {s['n']} views", views),
            },
            {
                "label": "Avg stance (-2 bearish .. +2 bullish)",
                "value": f"{s['avg']:+.2f}",
                "src": d("avg stance", f"mean(stance) over {s['n']} views", views),
            },
            {
                "label": "Avg agreement across the three passes",
                "value": f"{_avg([r['agreement'] for r in views]):.2f}",
                "src": d("avg agreement", f"mean(agreement) over {s['n']} views", views),
            },
        ]
        contested = [r for r in views if r["agreement"] is not None and r["agreement"] < 1]
        share = len(contested) / len(views)
        kv += [
            {
                "label": "Contested (passes disagree on the sign)",
                "value": f"{len(contested)} of {len(views)} ({share:.0%})",
                "src": d("contested views", "count of views with agreement < 1", contested),
            },
            {
                "label": "Contested flag",
                "value": f"yes, over {CONTESTED_SHARE:.0%} of views disagree"
                if share > CONTESTED_SHARE
                else f"no, at most {CONTESTED_SHARE:.0%} of views disagree",
                "src": derived("contested share", f"{len(contested)} / {len(views)}", [], ds),
            },
        ]
    if t in counts:
        rank = 1 + sum(1 for n in counts.values() if n > counts[t])
        kv.append(
            {
                "label": "Rank by views among labelled tickers",
                "value": f"#{rank} of {len(counts)} ({counts[t]} views)",
                "src": derived(
                    "rank by count of views", f"rank of ${t} by views among {len(counts)} tickers with views", [], ds
                ),
            }
        )
    blocks.append({"type": "kv", "rows": kv})

    # 2. Coverage: what the counts leave out
    cov = []
    if lab:
        first, last = min(r["created_at"] for r in lab), max(r["created_at"] for r in lab)
        cov.append(
            {
                "label": "Span of labelled tweets (UTC)",
                "value": f"{first:%Y-%m-%d} to {last:%Y-%m-%d}",
                "src": d("labelled span", "min and max created_at of the labelled original tweets", lab),
            }
        )
    labelled_ids = {r["id"] for r in lab}
    unlabelled = [r for r in orig if r["id"] not in labelled_ids]
    if unlabelled:
        cov.append(
            {
                "label": "Original tweets with the cashtag, not yet labelled",
                "value": str(len(unlabelled)),
                "src": d("unlabelled originals", "originals with the cashtag minus labelled originals", unlabelled),
            }
        )
    if replies or reply_labels:
        cov.append(
            {
                "label": "Replies with the cashtag, excluded from every count here",
                "value": str(len(replies)),
                "src": derived("reply tweets", f"tweets with ${t} where is_reply is true", [], ds),
            }
        )
        cov.append(
            {
                "label": "Labels on reply tweets in the store, excluded",
                "value": str(reply_labels),
                "src": derived("reply labels", f"labelled rows on reply tweets naming ${t}", [], ds),
            }
        )
    if cov:
        blocks.append({"type": "kv", "title": "Coverage", "rows": cov})

    if not views:
        blocks.append(
            {
                "type": "text",
                "text": f"No labelled views on ${t} yet: stance, holders and targets need labels.",
                "src": src(TAB_SRC, None, internal=True),
            }
        )

    # 3. Stance momentum: last 7 days against the 7 before, UTC
    if views:
        last7, prior7 = (
            within(views, 7),
            [r for r in views if now - timedelta(days=14) <= r["created_at"] < now - timedelta(days=7)],
        )
        both = bool(last7) and bool(prior7)
        mom = [
            {
                "label": "Stance, last 7 days (UTC)",
                "value": _stance(last7),
                "src": d("stance last 7d", f"mean(stance) of views since {(now - timedelta(days=7)):%Y-%m-%d}", last7),
            },
            {
                "label": "Stance, prior 7 days",
                "value": _stance(prior7),
                "src": d("stance prior 7d", "mean(stance) of views from 14 to 7 days before the clock", prior7),
            },
            {
                "label": "Stance momentum (last 7 minus prior 7)",
                "value": (
                    f"{_avg([r['stance'] for r in last7]) - _avg([r['stance'] for r in prior7]):+.2f}"
                    if both
                    else "n/a: one of the 7-day windows has no views"
                ),
                "src": d("stance momentum", "mean(stance) last 7d minus mean(stance) prior 7d", last7 + prior7),
            },
        ]
        blocks.append({"type": "kv", "title": "Momentum", "rows": mom})

        # 4. Daily stance trend
        by_day = defaultdict(list)
        for r in views:
            by_day[r["created_at"].date()].append(r)
        pts = [
            {
                "x": day.isoformat(),
                "y": _avg([r["stance"] for r in rows]),
                "src": d(
                    f"{len(rows)} views on {day.isoformat()}",
                    f"mean(stance) of views dated {day.isoformat()} (UTC)",
                    rows,
                ),
            }
            for day, rows in sorted(by_day.items())
        ]
        blocks.append(
            {"type": "series", "title": "Stance by day (views, UTC)", "unit": "stance (-2..+2)", "points": pts}
        )

        # 5. Holder split
        hrows = []
        for h in ("author", "quoted_analyst", "quoted_person"):
            rows = [r for r in views if r["view_holder"] == h]
            if rows:
                hrows.append(
                    {
                        "cells": [
                            h,
                            str(len(rows)),
                            f"{_avg([r['stance'] for r in rows]):+.2f}",
                            str(sum(r["stance"] < 0 for r in rows)),
                        ],
                        "src": d(f"{h} views", f"count of views with view_holder={h}", rows),
                    }
                )
        if hrows:
            blocks.append(
                {
                    "type": "table",
                    "title": "Holder split (who holds the view)",
                    "cols": ["holder", "views", "avg stance", "bearish"],
                    "rows": hrows,
                }
            )

        # 6. Top authors, each row sourced to that author's latest view
        by_author = defaultdict(list)
        for r in views:
            by_author[r["handle"]].append(r)
        arows = []
        for h, rows in sorted(by_author.items(), key=lambda kv_: (-len(kv_[1]), kv_[0]))[:10]:
            latest = max(rows, key=lambda r: r["created_at"])
            arows.append(
                {
                    "cells": [
                        f"@{h}",
                        str(len(rows)),
                        f"{_avg([r['stance'] for r in rows]):+.2f}",
                        str(sum(r["stance"] < 0 for r in rows)),
                    ],
                    "src": src(f"@{h} · latest view {latest['created_at']:%Y-%m-%d}", latest["url"] or ds_url),
                }
            )
        if arows:
            blocks.append(
                {
                    "type": "table",
                    "title": "Top authors (views, avg stance, bearish count)",
                    "cols": ["who", "views", "avg stance", "bearish"],
                    "rows": arows,
                }
            )

    # 7. Price targets
    pts = sorted([r for r in lab if (r["price_target"] or 0) > 0], key=lambda r: r["created_at"], reverse=True)
    if pts:
        vals = [r["price_target"] for r in pts]
        med = median(vals)
        pt_kv = [
            {
                "label": "Price targets in tweets",
                "value": f"{len(pts)} from {len({r['handle'] for r in pts})} authors",
                "src": d("price targets", f"count of labelled tweets with price_target > 0 for ${t}", pts),
            },
            {
                "label": "Median target",
                "value": f"${med:,.2f}",
                "src": d("median target", f"median(price_target) over {len(pts)} tweets", pts),
            },
            {
                "label": "Range (low to high)",
                "value": f"${min(vals):,.2f} to ${max(vals):,.2f}",
                "src": d("target range", f"min and max of price_target over {len(pts)} tweets", pts),
            },
        ]
        bars = []
        if close:
            pt_kv.append(
                {
                    "label": "Last daily close",
                    "value": f"${close:,.2f}",
                    "src": derived(
                        "last close",
                        f"arg_max(close, ts_event) over bars_1d for ${t}",
                        [src("Databento daily bars (market/databento/bars_1d)", None)],
                    ),
                }
            )
            pt_kv.append(
                {
                    "label": "Median implied upside vs last close",
                    "value": f"{(med / close - 1) * 100:+.1f}%",
                    "src": derived(
                        "implied upside", f"median target / last close - 1 = {med:,.2f} / {close:,.2f} - 1", [], ds
                    ),
                }
            )
            bars = [
                {
                    "label": f"@{r['handle']} {r['created_at']:%Y-%m-%d} · ${r['price_target']:,.2f}",
                    "value": round((r["price_target"] / close - 1) * 100, 1),
                    "src": tsrc(r),
                }
                for r in pts[:15]
            ]
        else:
            pt_kv.append(
                {
                    "label": "Implied upside",
                    "value": "n/a: no daily bars for this symbol",
                    "src": src(TAB_SRC, None, internal=True),
                }
            )
        blocks.append({"type": "kv", "title": "Price targets", "rows": pt_kv})
        if bars:
            blocks.append(
                {"type": "bars", "title": "Implied upside per tweeted target vs last close", "unit": "%", "items": bars}
            )
        blocks.append(
            {
                "type": "text",
                "text": "Targets are whatever price the labeller found in the tweet; horizon is usually "
                "unstated and a price quoted for comparison can be picked up by mistake. "
                "Read the tweet before relying on one.",
                "src": src(TAB_SRC, None, internal=True),
            }
        )

    if views:
        # 8. Themes (tweet_meta)
        by_theme = defaultdict(list)
        for r in views:
            for th in r.get("themes") or []:
                by_theme[th].append(r)
        trows = [
            {
                "cells": [
                    th,
                    str(len(rows)),
                    f"{_avg([r['stance'] for r in rows]):+.2f}",
                    str(sum(r["stance"] < 0 for r in rows)),
                ],
                "src": d(f"views tagged {th}", f"count of views whose tweet_meta themes include {th}", rows),
            }
            for th, rows in sorted(by_theme.items(), key=lambda kv_: (-len(kv_[1]), kv_[0]))[:8]
        ]
        if trows:
            blocks.append(
                {
                    "type": "table",
                    "title": "Themes (tweet_meta, views)",
                    "cols": ["theme", "views", "avg stance", "bearish"],
                    "rows": trows,
                }
            )

        # 9. Claims (labelled) and the meta flags
        by_claim = defaultdict(list)
        for r in views:
            by_claim[r["claim"]].append(r)
        crows = [
            {
                "cells": [
                    c,
                    str(len(rows)),
                    f"{_avg([r['stance'] for r in rows]):+.2f}",
                    str(sum(r["stance"] < 0 for r in rows)),
                ],
                "src": d(f"views with claim {c}", f"count of views with claim={c}", rows),
            }
            for c, rows in sorted(by_claim.items(), key=lambda kv_: (-len(kv_[1]), kv_[0]))[:6]
        ]
        blocks.append(
            {
                "type": "table",
                "title": "Claims (views)",
                "cols": ["claim", "views", "avg stance", "bearish"],
                "rows": crows,
            }
        )

        promo = [r for r in views if _is_promo(r)]
        repost = [r for r in views if r.get("is_repost")]
        sarc = [r for r in views if r.get("is_sarcastic")]
        clean = [r for r in views if not (_is_promo(r) or r.get("is_repost") or r.get("is_sarcastic"))]
        flags = [
            {
                "label": "Promo views (tweet_meta type promo, or claim promo_shill)",
                "value": str(len(promo)),
                "src": d("promo views", "count of views with tweet_type=promo or claim=promo_shill", promo),
            },
            {
                "label": "Repost views (tweet_meta is_repost)",
                "value": str(len(repost)),
                "src": d("repost views", "count of views with is_repost", repost),
            },
            {
                "label": "Sarcastic views (tweet_meta is_sarcastic)",
                "value": str(len(sarc)),
                "src": d("sarcastic views", "count of views with is_sarcastic", sarc),
            },
            {
                "label": "Views with no promo, repost or sarcasm flag",
                "value": _stance(clean),
                "src": d("clean views", "views with no promo, repost or sarcasm flag; mean(stance)", clean),
            },
        ]
        blocks.append({"type": "kv", "title": "Claim filters", "rows": flags})

    # 10. Raw cashtag mentions: originals, 7d and 30d
    if orig:
        n7, n30 = within(orig, 7), within(orig, 30)
        blocks.append(
            {
                "type": "kv",
                "rows": [
                    {
                        "label": f"Cashtag ${t} mentions, originals (7d · 30d)",
                        "value": f"{len(n7)} · {len(n30)}",
                        "src": d(
                            f"original tweets with ${t}",
                            f"count of original tweets with ${t} in the last 7 and 30 days (UTC)",
                            n30,
                        ),
                    },
                    {
                        "label": "Accounts, 30 days",
                        "value": str(len({r["handle"] for r in n30})),
                        "src": d("accounts", "distinct handles in the last 30 days", n30),
                    },
                    {
                        "label": "Latest original",
                        "value": f"{orig[0]['created_at']:%Y-%m-%d %H:%M} UTC · @{orig[0]['handle']}",
                        "src": tsrc(orig[0]),
                    },
                ],
            }
        )
        table = [
            {
                "cells": [
                    f"{r['created_at']:%Y-%m-%d}",
                    f"@{r['handle']}",
                    f"♥{r['likes'] or 0}",
                    " ".join((r["text"] or "").split()),
                ],
                "new": (now.date() - r["created_at"].date()).days <= NEW_DAYS,
                "src": tsrc(r),
            }
            for r in orig[:40]
        ]
        blocks.append(
            {
                "type": "table",
                "title": "Raw cashtag tweets, originals only (retweets and replies excluded)",
                "cols": ["date", "who", "likes", "tweet"],
                "rows": table,
            }
        )

    blocks.append(
        {
            "type": "text",
            "text": "Followed-account track record: not built. It needs a forward-return join (price "
            "after each view), which this tab does not do.",
            "src": src(TAB_SRC, None, internal=True),
        }
    )
    return {"id": "sentiment", "title": "Sentiment", "blocks": blocks}


def _stats(rows: list[dict]) -> dict:
    s = [r["stance"] for r in rows]
    return {
        "n": len(rows),
        "avg": _avg(s),
        "bull": sum(x > 0 for x in s),
        "bear": sum(x < 0 for x in s),
        "neu": sum(x == 0 for x in s),
    }
