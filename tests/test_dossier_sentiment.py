"""Dossier Sentiment tab: pure _build on synthetic rows (population, UTC windows, views, targets, sourcing)."""

from datetime import datetime, timedelta, timezone

import duckdb

from derive.dossier_tabs import sentiment as S

NOW = datetime(2026, 10, 28, 12, 0, 0)  # naive UTC, as tweets.created_at is
T = "MU"


def raw(i, days_ago, reply=False, handle="alice"):
    return {
        "id": str(i),
        "handle": handle,
        "created_at": NOW - timedelta(days=days_ago),
        "text": f"tweet {i}",
        "likes": 1,
        "url": f"https://x.com/{handle}/status/{i}",
        "is_reply": reply,
    }


def lab(
    i,
    days_ago,
    stance=1,
    holder="author",
    focus="primary",
    agreement=1.0,
    target=None,
    handle="alice",
    tweet_type="analysis",
    is_repost=False,
    is_sarcastic=False,
    themes=("ai_capex",),
    claim="own_analysis",
):
    return {
        "id": str(i),
        "handle": handle,
        "created_at": NOW - timedelta(days=days_ago),
        "url": f"https://x.com/{handle}/status/{i}",
        "text": f"tweet {i}",
        "likes": 1,
        "focus": focus,
        "stance": stance,
        "view_holder": holder,
        "claim": claim,
        "agreement": agreement,
        "price_target": target,
        "tweet_type": tweet_type,
        "is_repost": is_repost,
        "is_sarcastic": is_sarcastic,
        "themes": list(themes),
    }


def build(raw_rows, lab_rows, counts=None, close=None, reply_labels=0):
    return S._build(T, raw_rows, lab_rows, counts or {}, close, reply_labels, NOW)


def blocks_by_title(d):
    out = {}
    for b in d["blocks"]:
        out.setdefault(b.get("title") or b["type"], []).append(b)
    return out


def kv_value(d, label):
    for b in d["blocks"]:
        for r in b.get("rows", []) if b["type"] == "kv" else []:
            if r["label"] == label:
                return r["value"]
    raise KeyError(label)


def sourced(s):
    return bool(s) and bool(
        s.get("url") or s.get("internal") or s.get("error") or (s.get("formula") and s.get("inputs"))
    )


def all_items(d):
    for b in d["blocks"]:
        if b["type"] == "text":
            yield b
            continue
        for it in b.get("rows", b.get("points", b.get("items", []))):
            yield it


def test_now_is_utc_naive():
    now = S._now()
    assert now.tzinfo is None
    utc = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs((utc - now).total_seconds()) < 5


def test_counts_use_originals_and_utc_windows():
    rows = [raw(1, 6.9), raw(2, 7.1), raw(3, 29.0), raw(4, 31.0), raw(5, 0.5, reply=True)]
    d = build(rows, [])
    assert kv_value(d, "Cashtag $MU mentions, originals (7d · 30d)") == "1 · 3"
    assert kv_value(d, "Replies with the cashtag, excluded from every count here") == "1"


def test_replies_not_counted_as_mentions_and_coverage_says_so():
    d = build([raw(1, 1), raw(2, 1, reply=True)], [lab(1, 1)], reply_labels=3)
    assert kv_value(d, "Mention volume (labelled tweets naming the cashtag)") == "1"
    assert kv_value(d, "Labels on reply tweets in the store, excluded") == "3"


def test_views_exclude_passing_mentions_and_holder_none():
    labels = [
        lab(1, 1),
        lab(2, 1, focus="passing_mention", holder="none", stance=0),
        lab(3, 2, holder="none", stance=0),
        lab(4, 2, stance=-1, holder="quoted_analyst"),
    ]
    d = build([raw(i, 1) for i in range(1, 5)], labels)
    assert kv_value(d, "Views (not a passing mention, someone holds the view)") == "2"
    assert kv_value(d, "Bullish / bearish / neutral") == "1 / 1 / 0"
    assert kv_value(d, "Avg stance (-2 bearish .. +2 bullish)") == "+0.00"


def test_contested_flag_and_share():
    labels = [lab(i, 1, agreement=0.667) for i in range(1, 4)] + [lab(9, 1, agreement=1.0)]
    d = build([raw(i, 1) for i in range(1, 10)], labels)
    assert kv_value(d, "Contested (passes disagree on the sign)") == "3 of 4 (75%)"
    assert kv_value(d, "Contested flag").startswith("yes")


def test_momentum_last7_against_prior7():
    labels = [lab(1, 1, stance=2), lab(2, 6, stance=2), lab(3, 8, stance=0), lab(4, 13, stance=0)]
    d = build([raw(i, 1) for i in range(1, 5)], labels)
    assert kv_value(d, "Stance, last 7 days (UTC)") == "+2.00 · 2 views"
    assert kv_value(d, "Stance, prior 7 days") == "+0.00 · 2 views"
    assert kv_value(d, "Stance momentum (last 7 minus prior 7)") == "+2.00"


def test_momentum_is_na_when_a_window_is_empty():
    d = build([raw(1, 1)], [lab(1, 1)])
    assert kv_value(d, "Stance momentum (last 7 minus prior 7)").startswith("n/a")


def test_holder_split_and_top_authors():
    labels = [
        lab(1, 1, holder="author", stance=-1, handle="a"),
        lab(2, 2, holder="author", stance=1, handle="a"),
        lab(3, 3, holder="quoted_person", stance=2, handle="b"),
    ]
    d = build([raw(i, 1) for i in range(1, 4)], labels)
    holder = next(b for b in d["blocks"] if b.get("title", "").startswith("Holder split"))
    cells = {r["cells"][0]: r["cells"] for r in holder["rows"]}
    assert cells["author"] == ["author", "2", "+0.00", "1"]
    assert cells["quoted_person"] == ["quoted_person", "1", "+2.00", "0"]
    authors = next(b for b in d["blocks"] if b.get("title", "").startswith("Top authors"))
    assert authors["rows"][0]["cells"][0] == "@a"
    assert authors["rows"][0]["src"]["url"] == "https://x.com/a/status/1"  # latest view by @a


def test_price_targets_against_last_close():
    labels = [lab(1, 1, target=150.0), lab(2, 2, target=90.0, handle="b"), lab(3, 3, target=120.0, handle="c")]
    d = build([raw(i, 1) for i in range(1, 4)], labels, close=100.0)
    assert kv_value(d, "Price targets in tweets") == "3 from 3 authors"
    assert kv_value(d, "Median target") == "$120.00"
    assert kv_value(d, "Range (low to high)") == "$90.00 to $150.00"
    assert kv_value(d, "Median implied upside vs last close") == "+20.0%"
    bars = next(b for b in d["blocks"] if b["type"] == "bars")
    assert [it["value"] for it in bars["items"]] == [50.0, -10.0, 20.0]


def test_price_targets_without_close_say_so():
    d = build([raw(1, 1)], [lab(1, 1, target=150.0)], close=None)
    assert kv_value(d, "Implied upside").startswith("n/a")
    assert not any(b["type"] == "bars" for b in d["blocks"])


def test_no_price_targets_skips_the_block():
    d = build([raw(1, 1)], [lab(1, 1)], close=100.0)
    assert not any(b.get("title") == "Price targets" for b in d["blocks"])


def test_meta_flags_drop_promo_repost_and_sarcasm_from_clean_views():
    labels = [
        lab(1, 1, stance=2),
        lab(2, 1, stance=2, tweet_type="promo"),
        lab(3, 1, stance=-2, is_repost=True),
        lab(4, 1, stance=2, is_sarcastic=True),
        lab(5, 1, stance=0, claim="promo_shill"),
    ]
    d = build([raw(i, 1) for i in range(1, 6)], labels)
    flags = next(b for b in d["blocks"] if b.get("title") == "Claim filters")["rows"]
    values = {r["label"]: r["value"] for r in flags}
    assert values["Promo views (tweet_meta type promo, or claim promo_shill)"] == "2"
    assert values["Repost views (tweet_meta is_repost)"] == "1"
    assert values["Sarcastic views (tweet_meta is_sarcastic)"] == "1"
    assert values["Views with no promo, repost or sarcasm flag"] == "+2.00 · 1 views"


def test_every_value_has_a_source():
    labels = [
        lab(
            i,
            i % 20,
            stance=(i % 5) - 2,
            holder=("author", "quoted_person")[i % 2],
            handle=f"h{i % 4}",
            target=100.0 + i,
            themes=("ai_capex", "memory_cycle"),
        )
        for i in range(1, 30)
    ]
    d = build([raw(i, i % 35) for i in range(1, 40)], labels, counts={T: 29, "NVDA": 40}, close=95.0, reply_labels=2)
    assert d["blocks"]
    bad = [it for it in all_items(d) if not sourced(it.get("src"))]
    assert bad == []


def test_empty_returns_none():
    assert build([], []) is None


def test_section_for_unknown_ticker_is_none():
    con = duckdb.connect()
    assert S.section("ZZZNOTATICKER", con, None, None) is None
