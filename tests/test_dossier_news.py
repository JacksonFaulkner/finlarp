"""derive.dossier_tabs.news: pure logic on synthetic inputs (no network, no real data)."""
import json
from datetime import date, datetime, timedelta

import duckdb

from derive.dossier_tabs import news
from sources import roic_news, sec_events


class FakeF:
    """Stands in for dossier.Filings: accn -> url, plus the CIK used for the archive fallback."""

    def __init__(self, urls=None, cik=1835632):
        self.urls = urls or {}
        self.cik = cik

    def doc_url(self, accn, inline_xbrl=False):
        return self.urls.get(accn)


def _d(days_ago: int) -> str:
    return (date.today() - timedelta(days=days_ago)).isoformat()


def test_event_rows_drop_earnings_dates_and_keep_every_tier():
    events = [
        {"filed": _d(5), "form": "8-K", "item": "2.02", "signal": "high", "label": "Results", "accn": "A1", "primary_doc": "x.htm"},
        {"filed": _d(10), "form": "8-K", "item": "1.01", "signal": "high", "label": "Agreement", "accn": "A2", "primary_doc": "y.htm"},
        {"filed": _d(40), "form": "8-K", "item": "8.01", "signal": "low", "label": "Other", "accn": "A3", "primary_doc": "z.htm"},
        {"filed": _d(60), "form": "6-K", "item": None, "signal": "medium", "label": "Foreign report", "accn": "A4", "primary_doc": None},
    ]
    rows = news._event_rows(events, FakeF(urls={"A2": "https://sec.test/a2", "A3": "https://sec.test/a3"}))
    assert [r["cells"][1] for r in rows] == ["1.01", "8.01", "-"]  # 2.02 left to the earnings tab
    assert [r["cells"][2] for r in rows] == ["high", "low", "medium"]
    assert rows[0]["new"] is True and rows[1]["new"] is False  # 10 days is new, 40 is not
    assert rows[0]["src"]["url"] == "https://sec.test/a2"
    assert rows[2]["src"]["url"].startswith("https://www.sec.gov/Archives/edgar/data/1835632/")  # archive index fallback


def test_filing_src_falls_back_to_archive_then_internal():
    e = {"form": "8-K", "filed": "2026-10-01", "item": "1.01", "accn": "0001-26-000001", "primary_doc": "d.htm"}
    s = news._filing_src(e, FakeF(cik=1835632))
    assert s["url"] == "https://www.sec.gov/Archives/edgar/data/1835632/000126000001/d.htm"
    s = news._filing_src(e, FakeF(cik=None))
    assert s["url"] is None and s["internal"] is True


def test_fetch_news_window_ticker_and_order(tmp_path, monkeypatch):
    path = tmp_path / "news.parquet"
    today = date(2026, 10, 28)
    rows = [
        ("MRVL", datetime(2026, 10, 20, 9), "a.com", "new one", "https://a.test/1", "snip 1"),
        ("MRVL", datetime(2025, 3, 1, 9), "b.com", "older one", "https://b.test/2", "snip 2"),
        ("MRVL", datetime(2023, 1, 1, 9), "c.com", "too old", "https://c.test/3", "snip 3"),
        ("NVDA", datetime(2026, 10, 21, 9), "d.com", "other ticker", "https://d.test/4", "snip 4"),
    ]
    con = duckdb.connect()
    con.execute("CREATE TABLE n (ticker VARCHAR, published_at TIMESTAMP, site VARCHAR, title VARCHAR, url VARCHAR, text VARCHAR)")
    con.executemany("INSERT INTO n VALUES (?, ?, ?, ?, ?, ?)", rows)
    con.execute(f"COPY n TO '{path}' (FORMAT parquet)")
    monkeypatch.setattr(roic_news, "NEWS", path)
    arts, total = news._fetch_news("MRVL", today)
    assert total == 2  # the 2023 row is outside the two-year window
    assert [a["title"] for a in arts] == ["new one", "older one"]  # newest first, other tickers excluded
    rows_out = news._news_rows(arts)
    assert rows_out[0]["src"]["url"] == "https://a.test/1" and rows_out[0]["cells"][0] == "2026-10-20"


def test_fetch_news_missing_store_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(roic_news, "NEWS", tmp_path / "none.parquet")
    assert news._fetch_news("MRVL", date(2026, 10, 28)) == ([], 0)


def test_catalyst_blocks_match_ticker_tokens_and_keep_setup():
    pages = [
        {"date": "2026-10-15", "label": "TSM Q3", "tickers": "TSM  2330.TW", "when": "Thu", "status": "confirmed",
         "tabs": [{"name": "Watch", "text": "w"}, {"name": "Setup", "text": "Orders lead capex."}]},
        {"date": "2026-10-14", "label": "ASML Q3", "tickers": "ASML", "when": "Wed", "status": "estimated", "tabs": []},
        {"date": "2026-10-16", "label": "MUX", "tickers": "MUX", "when": "Fri", "status": "estimated", "tabs": []},
    ]
    blocks = news._catalyst_blocks("TSM", pages)
    table, text = blocks
    assert table["type"] == "table" and [r["cells"][1] for r in table["rows"]] == ["TSM Q3"]
    assert table["rows"][0]["src"] == {"label": "tui/src/screens/fixtures/catalyst_pages.json · TSM Q3", "url": None,
                                       "internal": True}
    assert text["text"] == "TSM Q3: Orders lead capex." and text["src"]["internal"] is True
    assert news._catalyst_blocks("MU", pages) == []  # substring "MUX" does not match "MU"


def test_tweet_rows_filter_window_stance_and_order():
    tweets = [
        {"d": _d(3), "t": "09:45", "h": "alice", "u": "https://x.test/1", "x": "MU looks great", "k": [["MU", 2], ["NVDA", None]]},
        {"d": _d(1), "t": "23:30", "h": "bob", "u": "", "x": "late $MU", "k": [["MU", None]]},
        {"d": _d(400), "t": "10:00", "h": "old", "u": "https://x.test/old", "x": "old", "k": [["MU", 1]]},
        {"d": _d(2), "t": "11:00", "h": "nvda", "u": "https://x.test/n", "x": "nvda only", "k": [["NVDA", 0]]},
    ]
    rows, total = news._tweet_rows(tweets, "MU", date.today())
    assert total == 2 and [r["cells"][2] for r in rows] == ["@bob", "@alice"]  # newest first, old and NVDA-only dropped
    assert rows[1]["cells"][3] == "+2" and rows[0]["cells"][3] == "—"
    assert rows[1]["src"]["url"] == "https://x.test/1"
    assert rows[0]["src"].get("internal") is True and rows[0]["src"]["url"] is None


def test_live_block_fails_soft(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("no route")

    monkeypatch.setattr(news.yahoo_live, "news", boom)
    now = datetime(2026, 10, 28, 20, 8, tzinfo=news.NY)
    b = news._live_block("MRVL", now)
    assert b["type"] == "text" and "2026-10-28 20:08 ET" in b["text"] and "ConnectionError" in b["text"]
    assert b["src"]["error"] is True


def test_live_block_rows_link_or_quote_fallback(monkeypatch):
    items = [
        {"time": "2026-10-28 14:15 ET", "publisher": "Motley Fool", "title": "Headline", "link": "https://y.test/a"},
        {"time": None, "publisher": None, "title": "No link", "link": None},
    ]
    monkeypatch.setattr(news.yahoo_live, "news", lambda sym, count=8: items)
    b = news._live_block("MRVL", datetime(2026, 10, 28, 20, 8, tzinfo=news.NY))
    assert b["type"] == "table" and b["title"] == "Live headlines from Yahoo, pulled 2026-10-28 20:08 ET"
    assert b["rows"][0]["src"]["url"] == "https://y.test/a"
    assert b["rows"][1]["src"]["url"] == "https://finance.yahoo.com/quote/MRVL/news"


def test_section_with_no_local_data_keeps_only_live_block(tmp_path, monkeypatch):
    monkeypatch.setattr(sec_events, "EVENTS", tmp_path / "none.parquet")
    monkeypatch.setattr(roic_news, "NEWS", tmp_path / "none.parquet")
    monkeypatch.setattr(news, "CATALYST_PAGES", tmp_path / "none.json")

    def gone():
        raise OSError("no tweet calendar")

    monkeypatch.setattr(news.tweet_calendar, "load", gone)
    monkeypatch.setattr(news.yahoo_live, "news", lambda sym, count=8: [])
    s = news.section("ZZZZ", None, FakeF(), None)
    assert s["id"] == "news" and s["title"] == "News & catalysts"
    assert [b["type"] for b in s["blocks"]] == ["table"] and s["blocks"][0]["rows"] == []


def test_section_builds_tweets_from_calendar(tmp_path, monkeypatch):
    cal = {"tweets": [{"d": _d(1), "t": "10:00", "h": "alice", "u": "https://x.test/1", "x": "MU up", "k": [["MU", 1]]}]}
    monkeypatch.setattr(sec_events, "EVENTS", tmp_path / "none.parquet")
    monkeypatch.setattr(roic_news, "NEWS", tmp_path / "none.parquet")
    monkeypatch.setattr(news, "CATALYST_PAGES", tmp_path / "none.json")
    monkeypatch.setattr(news.tweet_calendar, "load", lambda: json.dumps(cal))
    monkeypatch.setattr(news.yahoo_live, "news", lambda sym, count=8: [])
    s = news.section("MU", None, FakeF(), None)
    tweets = [b for b in s["blocks"] if b["type"] == "table" and "Tweet calendar" in b["title"]]
    assert len(tweets) == 1 and tweets[0]["rows"][0]["src"]["url"] == "https://x.test/1"
