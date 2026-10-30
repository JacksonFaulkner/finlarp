"""Peers dossier tab: pure logic on synthetic inputs (universe, profiles and facts are stubbed)."""
import duckdb
import pytest

from derive.dossier import validate
from derive.dossier_tabs import peers


def _src(tag):
    return {"label": f"filing {tag}", "url": f"https://example.test/{tag}"}


def _fin(rev, prev=None, gross=None, op=None, ni=None, unit="USD", fy=2026):
    return {"unit": unit, "fy": fy, "prev_fy": fy - 1 if prev is not None else None,
            "rev": rev, "rev_src": _src(f"rev{rev}"), "prev_rev": prev,
            "prev_src": _src(f"prev{prev}") if prev is not None else None,
            "gross": gross, "gross_src": _src("gross") if gross is not None else None,
            "op": op, "op_src": _src("op") if op is not None else None,
            "ni": ni, "ni_src": _src("ni") if ni is not None else None}


def _u(primary, subs=None, reviewed="2026-09-19"):
    return {"name": "x", "url": "https://example.test/co", "reviewed": reviewed,
            "primary": primary, "subs": subs or {"s1": 1.0}}


def test_dominant_picks_max_and_breaks_ties_alphabetically():
    assert peers._dominant(_u({"b": 0.5, "a": 0.5})) == ("a", 0.5)
    assert peers._dominant(_u({"x": 0.3, "y": 0.7})) == ("y", 0.7)
    assert peers._dominant(_u({})) is None


def test_cap_formats_usd_plain_and_other_currency_with_code():
    assert peers._cap(None, "USD") == "—"
    assert peers._cap(2_000_000_000_000, "USD") == "$2.00T"
    assert peers._cap(1_564_489_484_861_440, "KRW") == "KRW 1,564.49T"


def test_rec_valuation_only_for_usd_cap_and_usd_fundamentals():
    usd = peers._rec("A", {"market_cap": 10_000, "currency": "USD"}, None,
                     _fin(rev=1_000, prev=500, gross=600, op=200, ni=100))
    assert usd["growth"] == pytest.approx(100.0)
    assert usd["gm"] == pytest.approx(60.0)
    assert usd["om"] == pytest.approx(20.0)
    assert usd["ps"] == pytest.approx(10.0)
    assert usd["pe"] == pytest.approx(100.0)

    # Filer reports in TWD: growth and margins are unit-free, but P/S and P/E would mix currencies.
    twd = peers._rec("B", {"market_cap": 10_000, "currency": "USD"}, None,
                     _fin(rev=1_000, prev=500, unit="TWD", ni=100))
    assert twd["growth"] == pytest.approx(100.0)
    assert twd["ps"] is None and twd["pe"] is None

    # Non-USD listing: no valuation, no USD comparisons.
    krw = peers._rec("C", {"market_cap": 10_000, "currency": "KRW"}, None, _fin(rev=1_000, ni=100))
    assert krw["usd"] is False and krw["ps"] is None and krw["pe"] is None


def test_rec_negative_earnings_and_zero_revenue_give_no_multiples():
    neg = peers._rec("D", {"market_cap": 10_000, "currency": "USD"}, None, _fin(rev=1_000, ni=-5))
    assert neg["pe"] is None and neg["ps"] == pytest.approx(10.0)
    zero = peers._rec("E", {"market_cap": 10_000, "currency": "USD"}, None, _fin(rev=0, ni=5))
    assert zero["ps"] is None and zero["gm"] is None and zero["om"] is None


def test_rec_without_fundamentals_keeps_cap_only():
    r = peers._rec("F", {"market_cap": 5_000, "currency": "USD"}, "compute_hardware", None)
    assert r["cap"] == 5_000 and r["bucket"] == "compute_hardware"
    assert r["growth"] is None and r["ps"] is None


def _industry_fixture(monkeypatch, n_peers=30):
    """Subject S (cap 50,000 USD), n_peers USD peers P00.. with caps 1,000..n*1,000, one KRW name
    (KRW1), and one USD name with no facts (NOFIN)."""
    P = {"S": {"market_cap": 50_000, "currency": "USD", "industry": "Ind", "long_name": "Subject Co"}}
    U = {"S": _u({"bk": 0.6, "other": 0.4}, {"s1": 0.6, "s2": 0.4})}
    fins = {"S": _fin(rev=1_000, prev=800, gross=500, op=150, ni=100)}
    for i in range(n_peers):
        t = f"P{i:02d}"
        P[t] = {"market_cap": 1_000 * (i + 1), "currency": "USD", "industry": "Ind", "long_name": t}
        U[t] = _u({"bk": 1.0})
        fins[t] = _fin(rev=1_000, prev=900, gross=400, op=100, ni=50)
    P["KRW1"] = {"market_cap": 9_999_999, "currency": "KRW", "industry": "Ind", "long_name": "Korea Co"}
    U["KRW1"] = _u({"bk": 1.0})
    fins["KRW1"] = _fin(rev=1_000, prev=900, unit="KRW", ni=10)
    P["NOFIN"] = {"market_cap": 700, "currency": "USD", "industry": "Ind", "long_name": "No Facts"}
    U["NOFIN"] = _u({"bk": 1.0})
    fins["NOFIN"] = None
    monkeypatch.setattr(peers, "_fin", lambda t: fins.get(t))
    monkeypatch.setattr(peers, "_universe",
                        lambda: (U, {"s1": "Sub one", "s2": "Sub two"}, {"bk": "Bucket K", "other": "Other"}))
    return P, U


def _kv(blocks):
    return {r["label"]: r["value"] for b in blocks if b["type"] == "kv" for r in b["rows"]}


def test_industry_blocks_rank_averages_and_capped_table(monkeypatch):
    P, U = _industry_fixture(monkeypatch, n_peers=30)
    blocks = peers._industry_blocks("S", "Ind", U, P, {"bk": "Bucket K"})
    kv = _kv(blocks)

    assert kv["Names in industry"] == "33 · 32 with a USD market cap"  # S, 30 peers, KRW1, NOFIN
    assert kv["Rank by market cap (USD)"] == "1 of 32"  # S is the largest USD name
    assert kv["Average market cap (USD peers)"].endswith("n=31")  # 30 peers + NOFIN, subject excluded
    assert kv["Median revenue growth"].endswith("n=31")  # 30 peers + KRW1 (growth is unit-free); NOFIN has none

    table = next(b for b in blocks if b["type"] == "table")
    tickers = [r["cells"][0] for r in table["rows"]]
    assert len(tickers) == peers.TABLE_CAP
    assert tickers[:3] == ["P29", "P28", "P27"]  # sorted by market cap, largest first
    assert "KRW1" not in tickers  # outside the top 25 by cap; non-USD rows sort after USD ones
    assert validate({"sections": [{"id": "peers", "blocks": blocks}]}) == []


def test_industry_table_puts_non_usd_after_usd(monkeypatch):
    P, U = _industry_fixture(monkeypatch, n_peers=3)
    blocks = peers._industry_blocks("S", "Ind", U, P, {"bk": "Bucket K"})
    table = next(b for b in blocks if b["type"] == "table")
    tickers = [r["cells"][0] for r in table["rows"]]
    assert tickers == ["P02", "P01", "P00", "NOFIN", "KRW1"]
    krw_row = next(r for r in table["rows"] if r["cells"][0] == "KRW1")
    assert krw_row["cells"][3].startswith("KRW ")
    assert validate({"sections": [{"id": "peers", "blocks": blocks}]}) == []


def test_bucket_rank_by_weight_and_market_cap():
    U = {
        "S": _u({"bk": 0.6, "other": 0.4}),
        "A": _u({"bk": 1.0}),
        "B": _u({"bk": 0.7, "other": 0.3}),
        "C": _u({"bk": 0.5, "other": 0.5}),  # exact tie: alphabetically first bucket wins, so C is in "bk"
        "D": _u({"other": 1.0}),
    }
    P = {"S": {"market_cap": 100, "currency": "USD"}, "A": {"market_cap": 300, "currency": "USD"},
         "B": {"market_cap": 200, "currency": "USD"}, "C": {"market_cap": 50, "currency": "KRW"},
         "D": {"market_cap": 900, "currency": "USD"}}
    blocks = peers._bucket_blocks("S", U["S"], U, P, {"s1": "Sub one"},
                                  {"bk": "Bucket K", "other": "Other"})
    kv = _kv(blocks)
    assert kv["Primary bucket"] == "Bucket K · bk"
    assert kv["Primary weight"] == "60%"
    # "bk" members: A (1.0), B (0.7), S (0.6), C (0.5). Above S by weight: A and B, so 3 of 4.
    assert kv["Rank by bucket weight"] == "3 of 4"
    # USD caps in "bk": A 300, B 200, S 100 (C is KRW, excluded). Above S: A and B, so 3 of 3.
    assert kv["Rank by bucket market cap (USD)"] == "3 of 3"
    bars = next(b for b in blocks if b["type"] == "bars")
    assert [(i["label"], i["value"]) for i in bars["items"]] == [("Sub one", 100.0)]
    assert validate({"sections": [{"id": "peers", "blocks": blocks}]}) == []


def test_section_returns_none_without_data(monkeypatch, tmp_path):
    monkeypatch.setattr(peers, "_universe", lambda: ({}, {}, {}))
    monkeypatch.setattr(peers, "PROFILES", tmp_path / "missing.parquet")
    assert peers.section("NOPE", duckdb.connect(), None, None) is None


def test_section_with_profile_only_still_builds_industry(monkeypatch, tmp_path):
    monkeypatch.setattr(peers, "_universe", lambda: ({}, {}, {}))
    monkeypatch.setattr(peers, "PROFILES", tmp_path / "missing.parquet")
    monkeypatch.setattr(peers, "_fin", lambda t: None)
    prof = {"ticker": "Q", "industry": "Ind", "market_cap": 1_000, "currency": "USD", "long_name": "Q Co"}
    s = peers.section("Q", duckdb.connect(), None, prof)
    assert s is not None and s["id"] == "peers" and s["title"] == "Peers"
    assert _kv(s["blocks"])["Names in industry"] == "1 · 1 with a USD market cap"
    assert validate({"sections": [s]}) == []
