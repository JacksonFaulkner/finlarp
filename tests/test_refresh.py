"""Scheduled refresh: lane layout, key gating, market-hours gate, and the incremental-pull helpers it relies on."""
import json
from datetime import date, datetime

import pytest

from jobs import refresh
from sources import databento_bars as bars
from sources import keys, sec_financials


def test_daily_lanes_keep_sec_serial_and_build_last():
    steps = refresh.daily_steps()
    lanes = {s["name"]: s["lane"] for s in steps}
    assert all(lanes[n] == "sec" for n in ("events", "financials", "earnings", "filing_text", "13f", "13f_map"))
    assert [s["name"] for s in steps if s["lane"] == "final"] == ["search", "dossier", "squeeze"]
    tw = [s["name"] for s in steps if s["lane"] == "tweets"]
    assert tw == ["tweets_pull", "tweets_ingest", "sentiment"]
    fin = next(s for s in steps if s["name"] == "financials")
    assert "--new-filings" in fin["cmd"] and "--force" not in fin["cmd"]


def test_intraday_targets_the_watchlist(monkeypatch):
    monkeypatch.setattr(refresh, "watchlist", lambda: ["MU", "NVDA"])
    by = {s["name"]: s for s in refresh.intraday_steps()}
    assert {"tweets_pull", "sentiment", "news", "events"} <= set(by)
    assert {"MU", "NVDA"} <= set(by["events"]["cmd"]) and {"MU", "NVDA"} <= set(by["news"]["cmd"])
    monkeypatch.setattr(refresh, "watchlist", lambda: [])
    assert {s["name"] for s in refresh.intraday_steps()} == {"tweets_pull", "tweets_ingest", "sentiment"}


def test_step_without_its_key_is_skipped(monkeypatch, tmp_path):
    monkeypatch.setattr(keys, "get", lambda name: None)
    r = refresh.run_step(refresh.step("x", "news", "sources/roic_news.py", needs="ROIC_TOKEN"), tmp_path)
    assert r["status"] == "skipped" and "ROIC_TOKEN" in r["detail"]


@pytest.mark.parametrize("ts,want", [
    ("2026-10-12 09:00", True), ("2026-10-12 16:59", True), ("2026-10-12 17:00", False),
    ("2026-10-12 07:59", False), ("2026-10-10 12:00", False),  # Saturday
])
def test_market_hours(ts, want):
    assert refresh.market_hours(datetime.fromisoformat(ts).replace(tzinfo=refresh.ET)) is want


def d(s):
    return date.fromisoformat(s)


def test_gaps_returns_only_the_uncovered_tail_and_holes():
    have = [(d("2024-07-01"), d("2026-10-10")), (d("2024-07-01"), d("2026-10-08"))]
    assert bars.gaps(have, d("2024-07-01"), d("2026-10-14")) == [(d("2026-10-10"), d("2026-10-14"))]
    assert bars.gaps([], d("2026-01-01"), d("2026-02-01")) == [(d("2026-01-01"), d("2026-02-01"))]
    holed = [(d("2026-01-01"), d("2026-01-10")), (d("2026-01-20"), d("2026-02-01"))]
    assert bars.gaps(holed, d("2026-01-01"), d("2026-02-01")) == [(d("2026-01-10"), d("2026-01-20"))]
    assert bars.gaps([(d("2026-01-01"), d("2026-03-01"))], d("2026-01-15"), d("2026-02-01")) == []


def test_file_ranges_reads_both_manifest_shapes(tmp_path):
    a = tmp_path / "2026-01-01_2026-02-01_cabc.parquet"
    a.with_suffix(".symbols.json").write_text(json.dumps(["MU", "NVDA"]))
    assert bars.file_ranges(a) == {"MU": [(d("2026-01-01"), d("2026-02-01"))], "NVDA": [(d("2026-01-01"), d("2026-02-01"))]}
    b = tmp_path / "2026-01-01_2026-01-09_kdef.parquet"
    b.with_suffix(".symbols.json").write_text(json.dumps({"MU": [["2026-01-01", "2026-01-05"]]}))
    assert bars.file_ranges(b) == {"MU": [(d("2026-01-01"), d("2026-01-05"))]}


def test_filed_since_spots_new_periodic_reports(monkeypatch):
    rec = {"form": ["8-K", "10-Q", "4"], "filingDate": ["2026-10-11", "2026-10-02", "2026-10-11"]}
    monkeypatch.setattr(sec_financials.universe, "submissions", lambda cik: {"filings": {"recent": rec}})
    assert sec_financials.filed_since([1], "2026-09-26 16:00:00") is True
    assert sec_financials.filed_since([1], "2026-10-02 09:00:00") is True  # same day: companyfacts may lag
    assert sec_financials.filed_since([1], "2026-10-03 09:00:00") is False  # only an 8-K and a Form 4 since
    assert sec_financials.filed_since([1], None) is True
