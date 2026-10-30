"""Dossier Ownership tab: pure helpers on synthetic inputs, the 13F SQL on a tiny synthetic parquet set,
and graceful None when there is no data."""
from datetime import date

import duckdb
import pytest

from derive.dossier_tabs import ownership as own
from sources import sec_13f, sec_insiders


def test_change_kind_covers_new_added_trimmed_exited_flat():
    assert own.change_kind(None, 5) == "new"
    assert own.change_kind(5, None) == "exited"
    assert own.change_kind(5, 9) == "added"
    assert own.change_kind(9, 5) == "trimmed"
    assert own.change_kind(5, 5) == "flat"
    assert own.change_kind(None, None) is None


def test_concentration_top_shares_and_hhi():
    c = own.concentration([50, 30, 20])
    assert c["top10"] == pytest.approx(100)
    assert c["top20"] == pytest.approx(100)
    assert c["hhi"] == pytest.approx(50**2 + 30**2 + 20**2)  # 3800
    many = own.concentration([1.0] * 40)
    assert many["top10"] == pytest.approx(25)
    assert many["top20"] == pytest.approx(50)
    assert own.concentration([None, 0]) is None


def test_amend_label_from_subtype_and_amend_type():
    assert own.amend_label("13F-HR", "RESTATEMENT") == "restatement"
    assert own.amend_label("13F-HR/A", "NEW HOLDINGS") == "new-holdings amendment"
    assert own.amend_label("13F-HR/A", None) == "13F-HR/A"
    assert own.amend_label("13F-HR", None) is None


def test_sale_pct_is_share_of_pre_sale_position():
    assert own.sale_pct(50_000, 100_000) == pytest.approx(100 * 50_000 / 150_000)
    assert own.sale_pct(0, 100) is None
    assert own.sale_pct(10, None) is None


def test_role_tier_from_title_then_relationship():
    assert own.role_tier("PRESIDENT AND CEO", "Director, Officer") == "C-suite"
    assert own.role_tier("Vice President, Sales", "Officer") == "officer"
    assert own.role_tier("SVP, Chief Accounting Officer", "Officer") == "C-suite"
    assert own.role_tier(None, "Director") == "director"
    assert own.role_tier(None, "10% Owner") == "other"


def test_role_weighted_applies_weights():
    by, w = own.role_weighted([("C-suite", 100.0), ("director", 50.0), ("director", 50.0)])
    assert by["C-suite"] == 100 and by["director"] == 100
    assert w == 3 * 100 + 1 * 100


def test_planned_share_by_value_and_count():
    sells = [{"value": 300, "is_10b5_1": True}, {"value": 100, "is_10b5_1": False}]
    val, cnt = own.planned_share(sells)
    assert val == pytest.approx(75)
    assert cnt == pytest.approx(50)
    assert own.planned_share([]) == (None, None)


def test_window_flow_and_in_window():
    tx = [
        {"code": "P", "value": 40, "trans_date": date(2026, 10, 1)},
        {"code": "S", "value": 100, "trans_date": date(2026, 10, 20)},
        {"code": "S", "value": 50, "trans_date": date(2026, 8, 1)},
    ]
    assert own.window_flow(tx, date(2026, 9, 28)) == (40, 100)
    assert own.window_flow(tx, date(2026, 7, 1)) == (40, 150)
    rows = own.in_window(tx, date(2026, 10, 1), days=30)
    assert [x["value"] for x in rows] == [40, 100]


def test_filing_lag_days():
    assert own.filing_lag_days(date(2026, 10, 13), date(2026, 10, 12)) == 1
    assert own.filing_lag_days(None, date(2026, 10, 12)) is None


def test_signed_money():
    assert own._signed(-2_920_000) == "-$2.92M"
    assert own._signed(1_500) == "$1.50K"


def test_trend_formula_says_coverage_is_not_ownership_change():
    f = own._trend_formula("CRWD", date(2026, 6, 30), 2138, 6)
    assert "fixed set" in f
    assert "coverage" in f and "not real ownership change" in f


def _write_13f(root, periods, filings, holdings, cusip_map):
    """filings: (acc, cik, mgr, filed, period, subtype, amend_type); holdings: (acc, cusip, pc, sh, val)."""
    con = duckdb.connect()
    (root / "filings").mkdir(parents=True, exist_ok=True)
    (root / "holdings").mkdir(parents=True, exist_ok=True)
    con.execute("CREATE TABLE f (acc VARCHAR, cik INTEGER, mgr VARCHAR, filed DATE, period DATE, subtype VARCHAR, "
                "amend_type VARCHAR)")
    con.executemany("INSERT INTO f VALUES (?, ?, ?, ?, ?, ?, ?)", filings)
    con.execute(f"COPY f TO '{root / 'filings' / 'w.parquet'}' (FORMAT parquet)")
    con.execute("CREATE TABLE h (acc VARCHAR, cusip VARCHAR, pc VARCHAR, sh DOUBLE, val DOUBLE)")
    con.executemany("INSERT INTO h VALUES (?, ?, ?, ?, ?)", holdings)
    con.execute(f"COPY h TO '{root / 'holdings' / 'w.parquet'}' (FORMAT parquet)")
    con.execute("CREATE TABLE m (ticker VARCHAR, cusip VARCHAR)")
    con.executemany("INSERT INTO m VALUES (?, ?)", cusip_map)
    con.execute(f"COPY m TO '{root / 'cusip_map.parquet'}' (FORMAT parquet)")
    con.close()


@pytest.fixture
def synthetic_13f(tmp_path, monkeypatch):
    monkeypatch.setattr(sec_13f, "DATA_DIR", tmp_path)
    monkeypatch.setattr(own, "MIN_FILINGS", 1)
    p1, p2 = date(2026, 3, 31), date(2026, 6, 30)
    filings = [
        ("1-A", 1, "Alpha", date(2026, 4, 10), p1, "13F-HR", None),
        ("1-B", 1, "Alpha", date(2026, 8, 1), p2, "13F-HR", None),
        ("1-C", 1, "Alpha", date(2026, 8, 10), p2, "13F-HR/A", "RESTATEMENT"),
        ("2-A", 2, "Beta", date(2026, 4, 11), p1, "13F-HR", None),
        ("2-B", 2, "Beta", date(2026, 8, 2), p2, "13F-HR", None),
        ("3-A", 3, "Gamma", date(2026, 4, 12), p1, "13F-HR", None),
        ("3-B", 3, "Gamma", date(2026, 8, 3), p2, "13F-HR", None),
        ("4-B", 4, "Delta", date(2026, 8, 4), p2, "13F-HR", None),
    ]
    holdings = [
        ("1-A", "CUSIP1", None, 100, 1.0),
        ("1-B", "CUSIP1", None, 100, 1.0),   # superseded by the restatement 1-C
        ("1-C", "CUSIP1", None, 150, 1.0),
        ("2-A", "CUSIP1", None, 50, 1.0),
        ("2-B", "CUSIP1", None, 10, 1.0),
        ("2-B", "CUSIP1", "P", 30, 1.0),     # put row: keep in pc table, not in equity
        ("3-A", "CUSIP1", None, 100, 1.0),
        ("3-B", "CUSIP1", None, 5000, 1.0),  # typo: > 3x the runner-up (150), dropped
        ("4-B", "CUSIP1", None, 20, 1.0),
    ]
    holdings = [(a, c, pc, sh * 1_000_000, v) for a, c, pc, sh, v in holdings]  # millions of shares
    _write_13f(tmp_path, [p1, p2], filings, holdings, [("TST", "CUSIP1")])
    return tmp_path


def test_holder_blocks_on_synthetic_13f(synthetic_13f):
    con = duckdb.connect()
    blocks = own._holder_blocks("TST", con, None)
    kv = {r["label"]: r for r in blocks[0]["rows"]}
    # Pair panel is Alpha, Beta, Gamma (filed both quarters). Gamma's cur row is a typo and is dropped.
    assert kv["Holders"]["value"].startswith("3 → 2")
    assert kv["New / exited positions"]["value"] == "0 / 1"
    assert kv["Holders with an amended 13F (2026-06-30)"]["value"].startswith("1 of 3 ")
    assert kv["Top 10 / top 20 share"]["value"] == "100.0% / 100.0%"
    # Full QoQ list: Alpha added (restatement flag), Beta trimmed, Gamma exited.
    full = next(b for b in blocks if b.get("title", "").startswith("All QoQ"))
    kinds = {r["cells"][0]: (r["cells"][4], r["cells"][5]) for r in full["rows"]}
    assert kinds["Alpha"] == ("added", "restatement")
    assert kinds["Beta"][0] == "trimmed"
    assert kinds["Gamma"][0] == "exited"
    # Trend: Delta (new filer, not in the panel) counts in all managers, not in the panel.
    trend = next(b for b in blocks if b.get("title", "").startswith("Holder count trend"))
    cur_row = trend["rows"][0]["cells"]
    assert cur_row[0] == "2026-06-30" and cur_row[1] == "3" and cur_row[2] == "2"
    # Put/call: Beta's 30 puts sit beside 10 equity shares.
    pc = next(b for b in blocks if b.get("title", "").startswith("Put / call"))
    assert pc["rows"][0]["cells"][:3] == ["Beta", "30.00M", "0.00M"]  # 30M puts
    assert pc["rows"][0]["cells"][3] == "300.0%"
    for b in blocks:
        for r in b.get("rows", []):
            assert r.get("src") is not None


def test_no_data_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(sec_13f, "DATA_DIR", tmp_path)
    monkeypatch.setattr(sec_insiders, "loaded_quarters", lambda: set())
    con = duckdb.connect()
    from derive.dossier import Filings
    F = Filings.__new__(Filings)
    F.by_accn, F.cik = {}, None
    assert own.section("NONE", con, F, None) is None
