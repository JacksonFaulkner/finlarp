"""derive.sentiment and roic_news.query on tiny synthetic parquet, plus a smoke test of the MCP tools on the real data."""
import json

import duckdb
import pytest

from derive import sentiment as q
from sources import roic_news


@pytest.fixture
def store(tmp_path, monkeypatch):
    con = duckdb.connect()
    con.execute(f"""COPY (SELECT * FROM (VALUES
        ('1', 'alice', TIMESTAMP '2026-10-01 14:00:00', 'MU is a buy at 100, target 150', 5, 'u1'),
        ('2', 'bob',   TIMESTAMP '2026-10-02 14:00:00', 'selling MU',                      2, 'u2'),
        ('3', 'alice', TIMESTAMP '2026-10-09 14:00:00', 'MU again, also NVDA in passing',  9, 'u3'),
        ('4', 'carol', TIMESTAMP '2026-10-09 15:00:00', 'analyst says MU target 200',      1, 'u4'),
        ('5', 'dave',  TIMESTAMP '2026-10-10 15:00:00', 'a reply that was never labelled',  0, 'u5')
      ) AS t(id, handle, created_at, text, likes, url)) TO '{tmp_path / "tweets.parquet"}'""")
    labels = [
        # id, ticker, focus, stance, holder, claim, target, agreement
        ("1", "MU", "primary", 2, "author", "own_analysis", 150.0, 1.0),
        ("2", "MU", "primary", -1, "author", "own_analysis", None, 0.667),
        ("3", "MU", "primary", 1, "author", "own_analysis", None, 1.0),
        ("3", "NVDA", "passing_mention", 0, "none", "other", None, 1.0),
        ("4", "MU", "secondary", 1, "quoted_analyst", "price_target", 200.0, 1.0),
    ]
    rows = ", ".join(
        f"('{i}', '{t}', '{f}', {s}, '{h}', '{c}', 'days', true, {'NULL' if p is None else p}, '', 'evid {i}', 0.9, 3, {a})"
        for i, t, f, s, h, c, p, a in labels)
    con.execute(f"""COPY (SELECT * FROM (VALUES {rows}) AS t(id, ticker, focus, stance, view_holder, claim, horizon, has_numbers,
        price_target, catalyst, evidence, confidence, votes, agreement)) TO '{tmp_path / "labels.parquet"}'""")
    con.execute(f"""COPY (SELECT * FROM (VALUES
        ('1', 'analysis', ['memory_cycle'], ['hbm', 'dram'], []::VARCHAR[], false, false),
        ('2', 'analysis', ['memory_cycle'], ['hbm'],        []::VARCHAR[], false, false),
        ('3', 'analysis', ['valuation'],    ['hbm'],        []::VARCHAR[], false, false),
        ('4', 'news_recap', ['analyst_rating'], ['target'], []::VARCHAR[], false, false)
      ) AS t(id, tweet_type, themes, keywords, entities, is_repost, is_sarcastic)) TO '{tmp_path / "meta.parquet"}'""")
    con.execute(f"""COPY (SELECT * FROM (VALUES ('1','MU',true),('2','MU',true),('3','MU',true),('3','NVDA',true),('4','MU',true),
        ('5','MU',true)) AS t(tweet_id, ticker, in_universe)) TO '{tmp_path / "tickers.parquet"}'""")
    (tmp_path / "bars").mkdir()
    con.execute(f"""COPY (SELECT * FROM (VALUES ('MU', TIMESTAMP '2026-10-08 00:00:00', 90.0), ('MU', TIMESTAMP '2026-10-09 00:00:00', 100.0))
        AS t(symbol, ts_event, close)) TO '{tmp_path / "bars" / "b.parquet"}'""")
    monkeypatch.setattr(q, "LABELS", tmp_path / "labels.parquet")
    monkeypatch.setattr(q, "META", tmp_path / "meta.parquet")
    monkeypatch.setattr(q, "TWEETS", tmp_path / "tweets.parquet")
    monkeypatch.setattr(q, "TICKERS", tmp_path / "tickers.parquet")
    monkeypatch.setattr(q, "BARS", tmp_path / "bars" / "*.parquet")
    return tmp_path


def test_ticker_counts_views_not_passing_mentions(store):
    r = q.ticker("$mu")
    s = r["summary"]
    assert (r["ticker"], s["mentions"], s["views"], s["authors"]) == ("MU", 4, 4, 3)
    assert (s["bullish"], s["bearish"], s["neutral"], s["with_price_target"]) == (3, 1, 0, 2)
    assert s["avg_stance"] == 0.75
    assert {h["view_holder"]: h["views"] for h in r["by_holder"]} == {"author": 3, "quoted_analyst": 1}
    assert r["keywords"][0] == "hbm" and "memory_cycle" in r["themes"]
    assert [d["date"].isoformat() for d in r["daily"]] == ["2026-10-01", "2026-10-02", "2026-10-09"]
    assert r["recent"][0]["handle"] in ("alice", "carol") and r["recent"][0]["url"].startswith("u")
    assert r["coverage"]["store"]["labels"] == 5 and r["coverage"]["unlabelled_tweets"] == 1  # tweet 5 has a cashtag, no label


def test_ticker_passing_mention_is_a_mention_only(store):
    s = q.ticker("NVDA")["summary"]
    assert (s["mentions"], s["views"]) == (1, 0)
    assert any("passing mentions" in n for n in q.ticker("NVDA")["coverage"]["notes"])


def test_ticker_filters(store):
    assert q.ticker("MU", holder="quoted_analyst")["summary"]["views"] == 1
    assert q.ticker("MU", min_agreement=1)["summary"]["views"] == 3  # bob's label was contested
    assert q.ticker("MU", since="2026-10-09")["summary"]["views"] == 2
    assert q.ticker("MU", until="2026-10-02")["summary"]["views"] == 1


def test_unknown_ticker_says_so(store):
    r = q.ticker("ZZZ")
    assert r["summary"]["mentions"] == 0 and "no labelled tweets name ZZZ" in r["coverage"]["notes"][0]


def test_leaders(store):
    r = q.leaders("mentions", min_views=1)
    assert [t["ticker"] for t in r["tickers"]] == ["MU"]  # NVDA has no views
    assert r["tickers"][0]["views"] == 4 and r["tickers"][0]["bearish"] == 1
    assert q.leaders("bearish", min_views=1)["tickers"][0]["ticker"] == "MU"
    assert q.leaders("contested", min_views=1)["tickers"][0]["ticker"] == "MU"
    assert q.leaders("mentions", min_views=10)["tickers"] == []
    assert "no ticker has 10+ views" in q.leaders("mentions", min_views=10)["coverage"]["notes"][-1]
    mom = q.leaders("momentum", min_views=1)["tickers"][0]
    assert (mom["ticker"], mom["last7"], mom["prior7"]) == ("MU", 2, 2)  # Oct 9 pair vs Oct 1-2 pair
    assert "by must be one of" in q.leaders("nope")["error"]


def test_price_targets_against_last_close(store):
    r = q.price_targets("MU")
    s = r["summary"]
    assert (s["targets"], s["authors"], s["median_target"], s["low"], s["high"]) == (2, 2, 175.0, 150.0, 200.0)
    assert s["last_close"] == 100.0 and s["median_implied_upside_pct"] == 75.0
    assert sorted(t["implied_upside_pct"] for t in r["targets"]) == [50.0, 100.0]
    assert q.price_targets("NVDA")["summary"]["targets"] == 0


def test_news_query(tmp_path, monkeypatch):
    con = duckdb.connect()
    con.execute(f"""COPY (SELECT * FROM (VALUES
        ('a', 'IREN', TIMESTAMP '2026-10-09 10:00:00', 'IREN signs Anthropic deal', 'globenewswire.com', 'u1', 'x', 1),
        ('b', 'IREN', TIMESTAMP '2026-09-01 10:00:00', 'IREN drops',                'fool.com',          'u2', 'y', 1),
        ('c', 'MU',   TIMESTAMP '2026-10-01 10:00:00', 'Micron earnings',           'zacks.com',         'u3', 'z', 1)
      ) AS t(id, ticker, published_at, title, site, url, text, text_chars)) TO '{tmp_path / "news.parquet"}'""")
    monkeypatch.setattr(roic_news, "NEWS", tmp_path / "news.parquet")
    r = roic_news.query("iren")
    assert [a["title"] for a in r["articles"]] == ["IREN signs Anthropic deal", "IREN drops"]
    assert r["coverage"]["matched"] == 2 and r["coverage"]["store"]["tickers"] == 2
    assert [a["site"] for a in roic_news.query("IREN", site="globenewswire")["articles"]] == ["globenewswire.com"]
    assert [a["ticker"] for a in roic_news.query(text="micron")["articles"]] == ["MU"]
    assert roic_news.query("IREN", since="2026-10-01")["coverage"]["matched"] == 1
    r = roic_news.query("IREN", limit=1)
    assert r["coverage"]["truncated"] and "truncated" in " ".join(r["coverage"]["notes"])
    assert "may not have been pulled" in " ".join(roic_news.query("QUBT")["coverage"]["notes"])


@pytest.mark.integration
def test_mcp_tools_on_real_data(s, has_data):
    from sources import tweet_sentiment

    if not tweet_sentiment.OUT.exists():
        pytest.skip("no tweet_sentiment parquet on disk")
    r = json.loads(s.sentiment("MU"))
    assert r["summary"]["views"] > 0 and r["coverage"]["notes"]
    assert json.loads(s.sentiment_leaders("mentions", limit=3))["tickers"]
    assert "targets" in json.loads(s.price_targets("NBIS"))
    n = json.loads(s.news("IREN", limit=3))
    assert "coverage" in n and "snippet" in n["coverage"]["notes"][0]
