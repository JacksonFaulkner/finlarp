"""short_interest: parsing and merging of the FINRA daily file, Nasdaq history and the Yahoo fallback (no network)."""
from datetime import date, datetime, timezone

import duckdb
import pytest

from sources import short_interest as si

FINRA = (
    "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
    "20261014|SOUN|6277000.5|100|11600000.25|B,Q,N\n"
    "20261014|QUBT|2280000|0|3800000|B,Q,N\n"
    "20261014|ZZZZ|5|0|10|B,Q,N\n"
)


class Resp:
    def __init__(self, status=200, text="", payload=None):
        self.status_code, self.text, self._p = status, text, payload

    def json(self):
        return self._p

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(si, "VOLUME", tmp_path / "short_volume.parquet")
    monkeypatch.setattr(si, "INTEREST", tmp_path / "short_interest.parquet")
    monkeypatch.setattr(si.universe, "rows", lambda: [{"ticker": t} for t in ("SOUN", "QUBT", "IONQ")])
    return tmp_path


def test_parse_volume_keeps_only_tracked_tickers_and_computes_ratio():
    rows = si.parse_volume(FINRA, {"SOUN", "QUBT"})
    assert [r["ticker"] for r in rows] == ["QUBT", "SOUN"]
    soun = rows[1]
    assert soun["date"] == date(2026, 10, 14) and soun["short_exempt_volume"] == 100
    assert soun["short_ratio"] == pytest.approx(6277000.5 / 11600000.25)


def test_parse_volume_sums_repeated_symbols():
    text = "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n20261014|SOUN|10|1|20|B\n20261014|SOUN|5|0|10|Q\n"
    (row,) = si.parse_volume(text, {"SOUN"})
    assert (row["short_volume"], row["total_volume"], row["short_ratio"]) == (15, 30, 0.5)


def test_business_days_skip_weekends():
    assert [d.day for d in si.business_days(date(2026, 10, 9), date(2026, 10, 13))] == [9, 12, 13]


def test_pull_volume_is_incremental_and_skips_missing_days(store):
    calls = []

    def get(url):
        calls.append(url)
        if "20261013" in url:
            return Resp(403)  # a holiday: FINRA's CDN answers 403, not 404
        return Resp(text=FINRA.replace("20261014", url.rsplit("shvol", 1)[1][:8]))

    out = si.pull_volume(days=3, today=date(2026, 10, 14), get=get)
    assert out["days_fetched"] == 2 and out["days_missing"] == ["2026-10-13"]
    n = len(calls)
    out = si.pull_volume(days=3, today=date(2026, 10, 15), get=lambda u: Resp(text=FINRA.replace("20261014", "20261015")))
    assert out["days_fetched"] == 1, "only the new day is requested"
    dates = duckdb.connect().execute(f"SELECT DISTINCT date FROM read_parquet('{si.VOLUME}') ORDER BY 1").fetchall()
    assert [d[0] for d in dates] == [date(2026, 10, 12), date(2026, 10, 14), date(2026, 10, 15)]
    assert n == 3  # 10-12, 10-13, 10-14


NASDAQ = {"data": {"shortInterestTable": {"rows": [
    {"settlementDate": "09/30/2026", "interest": "158,933,778", "avgDailyShareVolume": "16,508,886", "daysToCover": 9.7},
    {"settlementDate": "09/15/2026", "interest": "154,000,000", "avgDailyShareVolume": "12,993,403", "daysToCover": 8.1},
]}}}


def test_parse_nasdaq_rows_and_unsupported_tickers():
    rows = si.parse_nasdaq("SOUN", NASDAQ)
    assert [(r["settlement_date"], r["short_interest"], r["days_to_cover"]) for r in rows] == [
        (date(2026, 9, 30), 158933778.0, 9.7), (date(2026, 9, 15), 154000000.0, 8.1)]
    assert si.parse_nasdaq("IONQ", {"data": None, "message": "Short interest is only supported for Nasdaq Listed stocks"}) is None


def test_parse_yahoo_gives_latest_and_prior_month():
    dks = {"sharesShort": {"raw": 100.0}, "dateShortInterest": {"raw": 1790726400},
           "sharesShortPriorMonth": {"raw": 90.0}, "sharesShortPreviousMonthDate": {"raw": 1788134400},
           "shortRatio": {"raw": 3.2}}
    rows = si.parse_yahoo("IONQ", dks, now=datetime(2026, 10, 14, tzinfo=timezone.utc))
    assert [(r["short_interest"], r["days_to_cover"], r["source"]) for r in rows] == [(100.0, 3.2, "yahoo"), (90.0, None, "yahoo")]
    assert rows[0]["settlement_date"] > rows[1]["settlement_date"]
    assert si.parse_yahoo("IONQ", {}) == []


def test_pull_interest_falls_back_to_yahoo_and_replaces_history(store, monkeypatch):
    def get(url):
        return Resp(payload=NASDAQ) if "/SOUN/" in url else Resp(payload={"data": None})

    monkeypatch.setattr(si.yahoo, "new_session", lambda: object())
    monkeypatch.setattr(si.yahoo_profile, "fetch", lambda s, t, modules: {"defaultKeyStatistics": {
        "sharesShort": {"raw": 50.0}, "dateShortInterest": {"raw": 1790726400}}})
    out = si.pull_interest(["SOUN", "IONQ"], max_age_hours=0, get=get, pause=0)
    assert (out["nasdaq"], out["yahoo"], out["none"], out["rows_total"]) == (1, 1, 0, 3)
    # a re-fetch replaces a ticker's history instead of appending to it
    shorter = {"data": {"shortInterestTable": {"rows": NASDAQ["data"]["shortInterestTable"]["rows"][:1]}}}
    out = si.pull_interest(["SOUN"], max_age_hours=0, get=lambda u: Resp(payload=shorter), pause=0)
    assert out["rows_total"] == 2
    # recently fetched tickers are skipped
    assert si.pull_interest(["SOUN"], max_age_hours=24, get=lambda u: pytest.fail("no refetch"), pause=0)["tickers"] == 0
