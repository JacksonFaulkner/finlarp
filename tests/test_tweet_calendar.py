"""derive.tweet_calendar: ET dates and times, universe-cashtag filter, retweets dropped, labelled stances attached."""
import duckdb
import pytest

from derive import tweet_calendar as tc


@pytest.fixture
def parquet(tmp_path):
    con = duckdb.connect()
    con.execute("""COPY (SELECT * FROM (VALUES
        ('1', 'alice', TIMESTAMP '2026-10-09 13:45:00', 'MU  looks\ngreat', 10, 1000, false, false, 'u1'),
        ('2', 'bob',   TIMESTAMP '2026-10-10 03:30:00', 'late night $NVDA',   0,  50,  true,  false, 'u2'),
        ('3', 'carol', TIMESTAMP '2026-10-09 15:00:00', 'RT $MU',             1,  10,  false, true,  'u3'),
        ('4', 'dave',  TIMESTAMP '2026-10-09 16:00:00', 'no universe ticker', 1,  10,  false, false, 'u4')
      ) AS t(id, handle, created_at, text, likes, views, is_reply, is_retweet, url)) TO '%s'""" % (tmp_path / "tweets.parquet"))
    con.execute("""COPY (SELECT * FROM (VALUES
        ('1', 'MU', true), ('1', 'NVDA', true), ('2', 'NVDA', true), ('3', 'MU', true), ('4', 'ZZZZ', false)
      ) AS t(tweet_id, ticker, in_universe)) TO '%s'""" % (tmp_path / "tickers.parquet"))
    con.execute("COPY (SELECT * FROM (VALUES ('1', 'MU', 2)) AS t(id, ticker, stance)) TO '%s'" % (tmp_path / "sent.parquet"))
    return tmp_path


def test_build_keeps_universe_originals_in_et(parquet):
    out = tc.build(parquet / "tweets.parquet", parquet / "tickers.parquet", parquet / "none.parquet")["tweets"]
    assert [x["h"] for x in out] == ["alice", "bob"]  # retweet and non-universe tweets dropped, ordered by time
    a, b = out
    assert (a["d"], a["t"]) == ("2026-10-09", "09:45")  # 13:45 UTC is 09:45 EDT
    assert (b["d"], b["t"]) == ("2026-10-09", "23:30")  # 03:30 UTC on the 10th is still the 9th in New York
    assert a["x"] == "MU looks great" and a["k"] == [["MU", None], ["NVDA", None]] and b["r"] == 1


def test_build_attaches_labelled_stance(parquet):
    out = tc.build(parquet / "tweets.parquet", parquet / "tickers.parquet", parquet / "sent.parquet")["tweets"]
    assert out[0]["k"] == [["MU", 2], ["NVDA", None]]  # labelled for MU only


def test_text_is_capped(parquet, monkeypatch):
    monkeypatch.setattr(tc, "TEXT_MAX", 5)
    out = tc.build(parquet / "tweets.parquet", parquet / "tickers.parquet", parquet / "none.parquet")["tweets"]
    assert len(out[0]["x"]) == 5
