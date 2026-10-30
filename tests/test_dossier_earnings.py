"""derive.dossier_tabs.earnings: the Earnings & guidance tab on synthetic inputs (no network)."""
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import duckdb
import pytest

from derive.dossier_tabs import earnings
from sources import sec_earnings, sec_events, yahoo_profile

ET = ZoneInfo("America/New_York")
CIK = 1835632


class FakeF:
    """Stands in for dossier.Filings: only cik and doc_url are used by the tab."""
    cik = CIK

    def doc_url(self, accn, inline_xbrl=False):
        return f"https://www.sec.gov/Archives/edgar/data/{CIK}/{accn.replace('-', '')}/{accn}-index.htm"


def _release_text(consensus: str | None = None) -> str:
    lines = ["Marvell reports results.", "Net revenue for the quarter was $2.7 billion."]
    if consensus:
        lines.append(consensus)
    lines += ["Outlook for the Third Quarter", "Net revenue is expected to be $3.150 billion +/- 5%.",
              "Forward-looking statements: we undertake no obligation to update these statements."]
    return "\n".join(lines)


@pytest.fixture
def paths(tmp_path, monkeypatch):
    rel_dir = tmp_path / "releases"
    rel_dir.mkdir()
    rel = rel_dir / "MRVL.parquet"
    events = tmp_path / "events.parquet"
    heads = {
        "new": json.dumps({"revenue": {"value": 2.739, "unit": "billion", "ccy": "$", "conf": "high",
                                       "snippet": "Q2 Net Revenue: $2.739 billion"},
                           "eps_nongaap": {"value": 0.94, "ccy": "$", "conf": "high",
                                           "snippet": "Q2 non-GAAP EPS: $0.94"}}),
        "old": json.dumps({"revenue": {"value": 2.418, "unit": "billion", "ccy": "$", "conf": "high",
                                       "snippet": "Q1 Net Revenue: $2.418 billion"}}),
    }
    rows = [
        ("MRVL", CIK, "0001835632-26-000022", "8-K", date(2026, 8, 27), "q227.htm", "ex99.1",
         _release_text("Analysts expected earnings of $0.85 per share, consensus of $0.80 per share."),
         ["•Net revenue is expected to be $3.150 billion +/- 5%.", "GAAP gross margin is expected to be 52.9%."],
         heads["new"]),
        ("MRVL", CIK, "0001835632-26-000014", "8-K", date(2026, 5, 27), "q127.htm", "ex99.1",
         _release_text(), [], heads["old"]),
    ]
    con = duckdb.connect()
    con.execute("CREATE TABLE r (ticker VARCHAR, cik BIGINT, accn VARCHAR, form VARCHAR, filed DATE, "
                "doc_name VARCHAR, method VARCHAR, text VARCHAR, guidance VARCHAR[], headline VARCHAR)")
    for ticker, cik, accn, form, filed, doc, method, text, guid, head in rows:
        con.execute("INSERT INTO r VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [ticker, cik, accn, form, filed, doc, method, text, guid, head])
    con.execute(f"COPY r TO '{rel}' (FORMAT parquet)")
    con.execute("CREATE TABLE e (ticker VARCHAR, filed DATE, form VARCHAR, item VARCHAR, accn VARCHAR, "
                "primary_doc VARCHAR)")
    for filed, accn, item in [(date(2026, 8, 27), "0001835632-26-000022", "2.02"),
                              (date(2026, 5, 27), "0001835632-26-000014", "2.02"),
                              (date(2026, 8, 27), "0001835632-26-000023", "7.01")]:  # 7.01 is not a report date
        con.execute("INSERT INTO e VALUES ('MRVL', ?, '8-K', ?, ?, 'doc.htm')", [filed, item, accn])
    con.execute(f"COPY e TO '{events}' (FORMAT parquet)")
    monkeypatch.setattr(sec_earnings, "REL_DIR", rel_dir)
    monkeypatch.setattr(sec_events, "EVENTS", events)
    return con


def _sourced(v) -> bool:
    s = v.get("src") if isinstance(v, dict) else None
    return isinstance(s, dict) and bool(s.get("url") or (s.get("formula") and s.get("inputs")))


def _values(sec):
    for b in sec["blocks"]:
        for it in b.get("rows", b.get("points", b.get("items", []))):
            yield b, it


def test_consensus_eps_takes_amount_after_consensus_wording():
    text = "Results beat.\nEPS of $0.85 per share, above consensus of $0.80 per share.\nNothing else."
    got = earnings._consensus_eps(text)
    assert got is not None and got[0] == "0.80"


def test_consensus_eps_ignores_boilerplate_and_bare_mentions():
    boiler = "We do not intend to review or confirm analysts' expectations of $1.00 per share."
    assert earnings._consensus_eps(boiler) is None
    assert earnings._consensus_eps("We finished ahead of consensus estimates.") is None
    assert earnings._consensus_eps("") is None


def test_hl_formats_units_and_per_share_decimals():
    assert earnings._hl({"value": 2.739, "unit": "billion", "ccy": "$"}) == "$2.739 billion"
    assert earnings._hl({"value": 0.8, "ccy": "$"}, eps=True) == "$0.80"
    assert earnings._hl({"value": 2.2, "unit": "table", "ccy": "$"}) == "$2.2"
    assert earnings._hl(None) == "—"


def test_next_report_unavailable_when_live_call_raises(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("offline")
    monkeypatch.setattr(yahoo_profile, "fetch", boom)
    (row,) = earnings._next_report("MRVL")
    assert row["value"] == "unavailable"
    assert row["src"]["url"] == "https://finance.yahoo.com/quote/MRVL/"
    assert "ConnectionError" in row["src"]["label"]


def test_next_report_unavailable_when_no_result(monkeypatch):
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: None)
    (row,) = earnings._next_report("MRVL")
    assert row["value"] == "unavailable"


def test_next_report_date_time_and_consensus(monkeypatch):
    ts = int(datetime(2026, 12, 1, 15, 0, tzinfo=ET).timestamp())
    res = {"calendarEvents": {"earnings": {
        "earningsDate": [{"raw": ts, "fmt": "2026-12-01"}], "isEarningsDateEstimate": True,
        "earningsAverage": {"raw": 1.10094}, "earningsLow": {"raw": 1.07628}, "earningsHigh": {"raw": 1.14},
        "revenueAverage": {"raw": 3151995970}}}}
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: res)
    rows = earnings._next_report("MRVL")
    assert [r["label"] for r in rows] == ["Next earnings", "Consensus EPS, next report", "Consensus revenue, next report"]
    assert rows[0]["value"] == "2026-12-01, 15:00 ET (estimate)"
    assert rows[1]["value"] == "$1.10 (range $1.08 to $1.14)"
    assert rows[2]["value"] == "$3.15B"
    assert all(r["src"]["url"] == "https://finance.yahoo.com/quote/MRVL/" for r in rows)


def test_next_report_midnight_et_means_time_not_listed(monkeypatch):
    ts = int(datetime(2026, 12, 1, 0, 0, tzinfo=ET).timestamp())
    res = {"calendarEvents": {"earnings": {"earningsDate": [{"raw": ts, "fmt": "2026-12-01"}]}}}
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: res)
    assert earnings._next_report("MRVL")[0]["value"] == "2026-12-01, time not listed"


def test_next_report_range_and_missing_dates(monkeypatch):
    t1 = int(datetime(2026, 12, 1, 15, tzinfo=ET).timestamp())
    t2 = int(datetime(2026, 12, 3, 15, tzinfo=ET).timestamp())
    res = {"calendarEvents": {"earnings": {"earningsDate": [{"raw": t1, "fmt": "2026-12-01"},
                                                            {"raw": t2, "fmt": "2026-12-03"}]}}}
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: res)
    assert earnings._next_report("MRVL")[0]["value"] == "2026-12-01 to 2026-12-03, 15:00 ET"
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: {"calendarEvents": {"earnings": {}}})
    assert earnings._next_report("MRVL")[0]["value"] == "not listed by Yahoo"


def test_section_builds_releases_guidance_and_report_dates(paths, monkeypatch):
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: None)
    sec = earnings.section("MRVL", paths, FakeF(), None)
    assert sec["id"] == "earnings" and sec["title"] == "Earnings & guidance"
    titles = [b.get("title") for b in sec["blocks"]]
    assert sec["blocks"][0]["type"] == "kv"
    assert "Last releases (headline figures)" in titles
    assert "Report dates (8-K item 2.02)" in titles
    assert any(t and t.startswith("Guidance as written in release") for t in titles)

    rel = next(b for b in sec["blocks"] if b.get("title") == "Last releases (headline figures)")
    # the newest release states an EPS consensus, so the consensus column appears
    assert rel["cols"] == ["filed", "revenue", "EPS non-GAAP", "EPS GAAP", "EPS consensus"]
    assert rel["rows"][0]["cells"] == ["2026-08-27", "$2.739 billion", "$0.94", "—", "$0.80 (release text)"]
    assert rel["rows"][1]["cells"][1] == "$2.418 billion"
    assert rel["rows"][1]["cells"][-1] == "—"

    dates = next(b for b in sec["blocks"] if b.get("title") == "Report dates (8-K item 2.02)")
    assert [r["cells"][0] for r in dates["rows"]] == ["2026-08-27", "2026-05-27"]  # newest first, 7.01 excluded
    assert dates["rows"][0]["cells"][1] == "92"
    assert dates["rows"][0]["src"]["formula"] == "2026-08-27 − 2026-05-27 = 92 days"
    assert dates["rows"][1]["cells"][1] == "—"


def test_section_every_value_is_sourced(paths, monkeypatch):
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: None)
    sec = earnings.section("MRVL", paths, FakeF(), None)
    n = 0
    for _, it in _values(sec):
        n += 1
        assert _sourced(it), it
    assert n > 5


def test_section_survives_missing_parquet_and_dead_yahoo(tmp_path, monkeypatch):
    monkeypatch.setattr(sec_earnings, "REL_DIR", tmp_path / "none")
    monkeypatch.setattr(sec_events, "EVENTS", tmp_path / "missing_events.parquet")

    def boom(*a, **k):
        raise TimeoutError("slow")
    monkeypatch.setattr(yahoo_profile, "fetch", boom)
    sec = earnings.section("ZZZZ", duckdb.connect(), FakeF(), None)
    assert sec is not None
    assert [b["type"] for b in sec["blocks"]] == ["kv"]
    assert sec["blocks"][0]["rows"][0]["value"] == "unavailable"
