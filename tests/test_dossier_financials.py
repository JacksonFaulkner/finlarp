"""dossier_tabs.financials: pure logic on synthetic inputs, plus one end-to-end section over fake facts (no SEC data read)."""
import duckdb
import pytest

from derive.dossier import validate
from derive.dossier_tabs import financials as fin
from sources import sec_financials, sec_segments

M = 1e6
SRC_A = {"label": "10-Q filed 2026-03-01 · X · Q1 FY2026", "url": "https://sec.test/A"}
SRC_B = {"label": "10-K filed 2026-03-11 · Y · FY2026", "url": "https://sec.test/B"}


class FakeF:
    def form(self, accn):
        return "10-Q"

    def doc_url(self, accn, inline_xbrl=False):
        return f"https://sec.test/{accn}" if accn else None


def fact(end, val, concept="X", fy=None, fq=None, start=None, accn="A1", filed="2026-03-01", derived=False,
         derived_from=None):
    r = {"end": end, "start": start, "val": val, "concept": concept, "fy": fy, "fq": fq, "accn": accn,
         "filed": filed, "unit": "USD", "derived": derived}
    if derived_from is not None:
        r["derived_from"] = derived_from
    return r


def pt(v, filed="2026-03-01"):
    return {"v": v, "src": SRC_A, "filed": filed}


# ---- formatting and combinators -------------------------------------------

def test_fmt_kinds():
    assert fin._fmt(1_234_500_000) == "1,234.5"
    assert fin._fmt(0.1234, "pct") == "12.3%"
    assert fin._fmt(2.5, "eps") == "2.50"
    assert fin._fmt(3e6, "sh") == "3.0"
    assert fin._fmt(1.5, "x") == "1.50x"
    assert fin._fmt(None) == "—"


def test_bin_is_derived_with_formula_and_guards_zero_and_missing():
    out = fin._bin(pt(6e6), pt(3e6), fin._div, "/", "Ratio")
    assert out["v"] == 2.0
    assert out["src"]["formula"] == "6.0 / 3.0"
    assert out["src"]["inputs"] == [SRC_A, SRC_A]
    assert fin._bin(pt(6e6), pt(0.0), fin._div, "/", "Ratio") is None
    assert fin._bin(None, pt(3e6), fin._div, "/", "Ratio") is None


def test_sum_single_part_passes_through_and_many_parts_are_derived():
    a = pt(1e6)
    assert fin._sum([a, None], "Total") is a
    assert fin._sum([None, None], "Total") is None
    out = fin._sum([pt(1e6), pt(2e6, filed="2026-04-01")], "Total")
    assert out["v"] == 3e6
    assert out["src"]["formula"] == "1.0 + 2.0"
    assert out["filed"] == "2026-04-01"


# ---- store and derived lines ----------------------------------------------

@pytest.fixture
def fake_fin(monkeypatch):
    """Route sec_financials.quarterly_series / annual_series to dicts keyed by a metric's first concept."""
    qtr: dict[str, list] = {}
    ann: dict[str, list] = {}
    monkeypatch.setattr(sec_financials, "quarterly_series",
                        lambda t, concepts: list(qtr.get(concepts[0], [])))
    monkeypatch.setattr(sec_financials, "annual_series",
                        lambda t, concepts: list(ann.get(concepts[0], [])))
    return qtr, ann


def _seeded_view(rows_by_name: dict, cad: str = "a") -> fin._View:
    st = fin._Store("TST", FakeF())
    for name in fin.CONCEPTS:  # unseeded metrics stay empty, never read from disk
        st._rows[(name, cad)] = {}
    for name, rows in rows_by_name.items():
        st._rows[(name, cad)] = rows
    return fin._View(st, cad)


def test_derived_quarter_is_dropped_for_per_share_but_kept_for_flows(fake_fin):
    qtr, _ = fake_fin
    cum = [fact("2025-06-30", 1.0, fy=2026, fq=2, start="2025-01-01"),
           fact("2025-09-30", 1.5, fy=2026, fq=3, start="2025-01-01")]
    derived_row = fact("2026-01-31", 0.5, fy=2026, fq=4, start="2025-10-01", derived=True, derived_from=[
        dict(cum[1], start="2025-01-01"), dict(cum[0], start="2025-01-01")])
    qtr[fin.CONCEPTS["eps"][0]] = [derived_row]
    qtr[fin.CONCEPTS["revenue"][0]] = [dict(derived_row, val=5 * M)]
    st = fin._Store("TST", FakeF())
    assert st.pt("eps", "q", "2026-01-31") is None  # YTD minus YTD is not a quarterly EPS
    rev = st.pt("revenue", "q", "2026-01-31")
    assert rev["v"] == 5 * M
    assert rev["src"]["label"].endswith("derived: no discrete quarterly fact filed")
    assert "−" in rev["src"]["formula"]


def test_total_debt_excludes_current_portion_when_long_term_debt_is_total():
    total = _seeded_view({"ltd": {2026: fact("2026-01-31", 100 * M, concept="LongTermDebt", fy=2026)},
                          "current_ltd": {2026: fact("2026-01-31", 10 * M, concept="LongTermDebtCurrent", fy=2026)},
                          "short_borrow": {2026: fact("2026-01-31", 5 * M, concept="ShortTermBorrowings", fy=2026)}})
    assert total.total_debt(2026)["v"] == 105 * M
    noncurrent = _seeded_view({"ltd": {2026: fact("2026-01-31", 100 * M, concept="LongTermDebtNoncurrent", fy=2026)},
                               "current_ltd": {2026: fact("2026-01-31", 10 * M, concept="LongTermDebtCurrent", fy=2026)},
                               "short_borrow": {2026: fact("2026-01-31", 5 * M, concept="ShortTermBorrowings", fy=2026)}})
    assert noncurrent.total_debt(2026)["v"] == 115 * M
    assert len(noncurrent.total_debt(2026)["src"]["inputs"]) == 3


def test_roe_uses_average_equity_and_roic_spells_out_invested_capital():
    v = _seeded_view({
        "net_income": {2026: fact("2026-01-31", 200 * M, concept="NetIncomeLoss", fy=2026)},
        "equity": {2025: fact("2025-01-31", 900 * M, concept="StockholdersEquity", fy=2025),
                   2026: fact("2026-01-31", 1100 * M, concept="StockholdersEquity", fy=2026)},
        "operating_income": {2026: fact("2026-01-31", 300 * M, concept="OperatingIncomeLoss", fy=2026)},
        "pretax": {2026: fact("2026-01-31", 250 * M, concept="IncomeLossBeforeTax", fy=2026)},
        "tax": {2026: fact("2026-01-31", 50 * M, concept="IncomeTaxExpenseBenefit", fy=2026)},
        "cash": {2026: fact("2026-01-31", 100 * M, concept="CashAndCashEquivalentsAtCarryingValue", fy=2026)},
        "ltd": {2026: fact("2026-01-31", 400 * M, concept="LongTermDebtNoncurrent", fy=2026)},
    })
    roe = v.roe(2026)
    assert roe["v"] == pytest.approx(0.2)
    assert roe["src"]["formula"] == "200.0 / avg(900.0, 1,100.0) ($M)"
    roic = v.roic(2026)
    assert roic["v"] == pytest.approx(240 / 1400)
    assert "invested capital = equity + total debt − cash" in roic["src"]["formula"]
    assert "NOPAT = operating income × (1 − tax / pretax)" in roic["src"]["formula"]


def test_roic_skipped_when_tax_rate_outside_zero_to_one():
    v = _seeded_view({
        "operating_income": {2026: fact("2026-01-31", 300 * M, concept="OperatingIncomeLoss", fy=2026)},
        "pretax": {2026: fact("2026-01-31", 100 * M, concept="IncomeLossBeforeTax", fy=2026)},
        "tax": {2026: fact("2026-01-31", -50 * M, concept="IncomeTaxExpenseBenefit", fy=2026)},
        "equity": {2026: fact("2026-01-31", 1 * M, concept="StockholdersEquity", fy=2026)},
        "cash": {2026: fact("2026-01-31", 0.0, concept="Cash", fy=2026)},
    })
    assert v.roic(2026) is None


# ---- table rows ------------------------------------------------------------

def test_table_skips_empty_rows_and_sources_each_cell():
    cols = [("q1", "Q1"), ("q2", "Q2"), ("q3", "Q3")]
    vals = {"q1": pt(1 * M), "q3": pt(3 * M, filed="2026-05-01")}
    spec = [("A ($M)", "m", lambda k: vals.get(k)), ("empty ($M)", "m", lambda k: None)]
    tbl = fin._table("T", cols, spec)
    assert tbl["cols"] == ["metric", "Q1", "Q2", "Q3"]
    assert len(tbl["rows"]) == 1
    row = tbl["rows"][0]
    assert row["cells"] == ["A ($M)", "1.0", "—", "3.0"]
    assert row["src"]["formula"] == "each cell is that period's value; see inputs"
    assert row["src"]["inputs"] == [SRC_A, SRC_A]
    assert fin._table("T", cols, [("empty", "m", lambda k: None)]) is None


def test_table_single_populated_cell_uses_the_fact_source():
    tbl = fin._table("T", [("q1", "Q1"), ("q2", "Q2")], [("A", "m", lambda k: pt(2 * M) if k == "q2" else None)])
    assert tbl["rows"][0]["src"] == SRC_A


# ---- end to end over synthetic facts ---------------------------------------

@pytest.fixture
def synthetic_segments(tmp_path, monkeypatch):
    path = tmp_path / "seg.parquet"
    rows = [
        ("TST", 1, "A1", "10-K", "2026-03-11", "2025-02-01", "2026-01-31", "OperatingIncomeLoss",
         "StatementBusinessSegmentsAxis", "ChipMember", 300.0 * M, False, "USD"),
        ("TST", 1, "A1", "10-K", "2026-03-11", "2025-02-01", "2026-01-31",
         "RevenueFromContractWithCustomerExcludingAssessedTax", "StatementBusinessSegmentsAxis", "ChipMember",
         1000.0 * M, False, "USD"),
        ("TST", 1, "A1", "10-K", "2026-03-11", "2025-02-01", "2026-01-31", "OperatingIncomeLoss",
         "StatementBusinessSegmentsAxis", "SoftwareMember", 50.0 * M, False, "USD"),
        ("TST", 1, "A1", "10-K", "2026-03-11", "2025-02-01", "2026-01-31",
         "RevenueFromContractWithCustomerExcludingAssessedTax", "StatementBusinessSegmentsAxis", "SoftwareMember",
         500.0 * M, False, "USD"),
    ]
    con = duckdb.connect()
    con.execute("""CREATE TABLE seg (ticker VARCHAR, cik BIGINT, accn VARCHAR, form VARCHAR, filing_date DATE,
                   period_start DATE, period_end DATE, concept VARCHAR, axis VARCHAR, member VARCHAR,
                   value DOUBLE, is_custom_member BOOLEAN, unit VARCHAR)""")
    con.executemany("INSERT INTO seg VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.execute(f"COPY seg TO '{path}' (FORMAT parquet)")
    monkeypatch.setattr(sec_segments, "facts_glob", lambda: str(path))
    return con


def test_section_builds_tables_with_sources_and_segment_margin(fake_fin, synthetic_segments):
    qtr, ann = fake_fin
    qends = [("2025-04-30", 2026, 1), ("2025-07-31", 2026, 2), ("2025-10-31", 2026, 3), ("2026-01-31", 2026, 4)]
    rev = [fact(e, v * M, concept="RevenueFromContractWithCustomerExcludingAssessedTax", fy=fy, fq=fq,
                start="2025-01-01", accn=f"R{fq}")
           for (e, fy, fq), v in zip(qends, [250, 260, 270, 280])]
    rev[3] = fact("2026-01-31", 280 * M, concept="RevenueFromContractWithCustomerExcludingAssessedTax", fy=2026,
                  fq=4, start="2025-10-01", accn="R4", derived=True, derived_from=[
                      dict(end="2026-01-31", start="2025-02-01", val=1060 * M, concept="Rev", accn="K1",
                           filed="2026-03-11"),
                      dict(end="2025-10-31", start="2025-02-01", val=780 * M, concept="Rev", accn="R3",
                           filed="2025-12-01")])
    qtr[fin.CONCEPTS["revenue"][0]] = rev
    ann[fin.CONCEPTS["revenue"][0]] = [fact("2025-01-31", 900 * M, fy=2025, accn="K0", filed="2025-03-01"),
                                       fact("2026-01-31", 1060 * M, fy=2026, accn="K1", filed="2026-03-11")]
    gp = [fact(e, v * M, concept="GrossProfit", fy=fy, fq=fq, start="2025-01-01") for (e, fy, fq), v in
          zip(qends, [100, 110, 120, 130])]
    qtr[fin.CONCEPTS["gross_profit"][0]] = gp
    qtr[fin.CONCEPTS["ocf"][0]] = [fact(e, v * M, concept="OCF", fy=fy, fq=fq, start="2025-01-01")
                                   for (e, fy, fq), v in zip(qends, [50, 60, 70, 80])]
    qtr[fin.CONCEPTS["capex"][0]] = [fact(e, 10 * M, concept="Capex", fy=fy, fq=fq, start="2025-01-01")
                                     for (e, fy, fq) in qends]
    qtr[fin.CONCEPTS["eps"][0]] = [fact(e, 0.5, concept="EPS", fy=fy, fq=fq, start="2025-01-01")
                                   for (e, fy, fq) in qends[:3]]
    qtr[fin.CONCEPTS["cash"][0]] = [fact(e, v * M, concept="Cash", accn="B") for e, v in
                                    zip([q[0] for q in qends], [500, 520, 540, 560])]

    con = synthetic_segments
    out = fin.section("TST", con, FakeF(), None)

    assert out["id"] == "financials" and out["title"] == "Financials"
    titles = [b["title"] for b in out["blocks"] if b["type"] == "table"]
    assert titles[:4] == ["Segment operating income and margin (FY ending 2026-01-31)",
                          "Quarterly P&L and cash flow", "Annual P&L and cash flow",
                          "Quarter-end balance sheet, per-share and capital return"]
    assert validate({"sections": [out]}) == []

    qtable = next(b for b in out["blocks"] if b.get("title") == "Quarterly P&L and cash flow")
    cells = {r["cells"][0]: r["cells"][1:] for r in qtable["rows"]}
    assert cells["Gross margin (%)"][-1] == "46.4%"  # 130 / 280, Q4 revenue is a derived quarter
    assert cells["Free cash flow ($M)"][-1] == "70.0"
    assert cells["EPS diluted ($)"][-1] == "—"  # derived quarter never used for per-share values
    assert cells["EPS diluted ($)"][0] == "0.50"

    seg = next(b for b in out["blocks"] if b.get("type") == "table" and "Segment" in b["title"])
    chip = next(r for r in seg["rows"] if r["cells"][1] == "300.0")
    assert chip["cells"][2] == "1,000.0" and chip["cells"][3] == "30.0%"
    assert chip["src"]["formula"] == "300.0 / 1,000.0"


def test_section_is_none_without_revenue(fake_fin, synthetic_segments):
    assert fin.section("TST", synthetic_segments, FakeF(), None) is None
