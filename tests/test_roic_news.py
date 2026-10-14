"""roic_news: offline checks of normalisation, dedupe and the history-limit handling (no network)."""
import json
from datetime import date

import duckdb
import pytest

from sources import roic_news


def _art(url, ts="2026-10-09T11:52:00.000Z", title="t", text="body", site="fool.com"):
    return {"symbol": "IREN", "title": title, "article_url": url, "article_text": text, "published_date": ts, "site": site}


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    monkeypatch.setattr(roic_news, "DIR", tmp_path)
    monkeypatch.setattr(roic_news, "RAW", tmp_path / "raw")
    monkeypatch.setattr(roic_news, "STATE", tmp_path / "state.json")
    monkeypatch.setattr(roic_news, "NEWS", tmp_path / "news.parquet")
    (tmp_path / "raw").mkdir()
    return tmp_path


def test_row_normalises_time_and_site():
    row = roic_news._row("IREN", _art("https://x.test/a", ts="2026-10-09T23:30:00-04:00", site=None))
    assert row["published_at"] == "2026-10-10 03:30:00"  # converted to naive UTC
    assert row["site"] == "x.test"  # falls back to the url host
    assert row["text_chars"] == 4 and len(row["id"]) == 16


def test_row_skips_items_without_url_or_date():
    assert roic_news._row("IREN", _art("")) is None
    assert roic_news._row("IREN", {**_art("https://x.test/a"), "published_date": None}) is None


def test_ingest_dedupes_by_ticker_and_url(tmp_store):
    lines = [_art("https://x.test/a"), _art("https://x.test/a", title="dup"), _art("https://x.test/b")]
    (tmp_store / "raw" / "IREN.jsonl").write_text("".join(json.dumps(a) + "\n" for a in lines))
    (tmp_store / "raw" / "SERV.jsonl").write_text(json.dumps(_art("https://x.test/a")) + "\n")
    assert roic_news.ingest() == {"articles": 3, "tickers": 2}  # same url under two tickers stays two rows
    rows = duckdb.connect().execute(
        f"SELECT ticker, count(*), count(DISTINCT id) FROM read_parquet('{roic_news.NEWS}') GROUP BY 1 ORDER BY 1").fetchall()
    assert rows == [("IREN", 2, 2), ("SERV", 1, 1)]


def test_ingest_requires_raw(tmp_store):
    with pytest.raises(SystemExit):
        roic_news.ingest()


class _Resp:
    def __init__(self, status, body):
        self.status_code, self._body, self.text = status, body, json.dumps(body)

    def json(self):
        return self._body


class _Session:
    def __init__(self, *resps):
        self.resps = list(resps)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append(params)
        return self.resps.pop(0)


@pytest.fixture
def fast(monkeypatch):
    monkeypatch.setattr(roic_news.keys, "require", lambda name: "k")
    monkeypatch.setattr(roic_news.time, "sleep", lambda s: None)
    return roic_news._Throttle(rpm=1e9)


def test_history_limit_raises(fast):
    msg = "Your Free plan includes 2 years of history. This request reaches back ~3 years."
    s = _Session(_Resp(403, {"error": msg}))
    with pytest.raises(roic_news.HistoryLimit):
        roic_news._get(s, fast, "IREN", {})


def test_paywall_stops_the_run(fast):
    s = _Session(_Resp(402, {"error": {"message": "upgrade"}}))
    with pytest.raises(SystemExit):
        roic_news._get(s, fast, "IREN", {})


def test_pull_ticker_pages_until_short_page_and_merges(tmp_store, fast):
    page0 = [_art(f"https://x.test/{i}") for i in range(roic_news.PAGE)]
    page1 = [_art("https://x.test/last")]
    s = _Session(_Resp(200, page0), _Resp(200, page1))
    fetched, new = roic_news.pull_ticker(s, fast, "IREN", date(2026, 1, 1), date(2026, 10, 12), max_pages=10)
    assert (fetched, new) == (roic_news.PAGE + 1, roic_news.PAGE + 1)
    assert [c["page"] for c in s.calls] == [0, 1]
    # a second run that sees one old and one new article only adds the new one
    s2 = _Session(_Resp(200, [_art("https://x.test/0"), _art("https://x.test/fresh")]))
    assert roic_news.pull_ticker(s2, fast, "IREN", date(2026, 1, 1), date(2026, 10, 12), max_pages=10) == (2, 1)
