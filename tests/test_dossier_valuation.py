"""Valuation dossier tab: pure logic on synthetic inputs (no network, no local data)."""
import pytest

from derive import sentiment
from derive.dossier_tabs import valuation as V


def _sourced(item) -> bool:
    s = item.get("src")
    return bool(s and (s.get("url") or (s.get("formula") and s.get("inputs"))))


def _all_sourced(blocks) -> None:
    for b in blocks:
        for it in b.get("rows", []):
            assert _sourced(it), it
    for b in blocks:
        for it in b.get("rows", []):
            if "cells" in it:
                assert _sourced(it), it


def test_amt_uses_dollar_only_for_usd():
    assert V._amt(2.5e9, "USD") == "$2.50B"
    assert V._amt(1.2e12, "KRW") == "KRW 1.20T"
    assert V._amt(None, "KRW") == "—"


def test_px_formats_per_share_price():
    assert V._px(251.65, "USD") == "$251.65"
    assert V._px(3050000, "KRW") == "KRW 3,050,000.00"


def test_pfcf_market_cap_over_fcf_with_inputs():
    srcs = {k: {"label": k, "url": "https://x"} for k in ("price", "shares", "fcf")}
    row = V._pfcf(100.0, 1_000_000, 5_000_000.0, "USD", "USD", srcs)
    assert row["value"] == "20.0x"
    assert "100.00 × 1,000,000" in row["src"]["formula"]
    assert row["src"]["inputs"] == [srcs["price"], srcs["shares"], srcs["fcf"]]


def test_pfcf_skips_on_missing_input_and_flags_currency_mismatch():
    srcs = {k: {"label": k, "url": "https://x"} for k in ("price", "shares", "fcf")}
    assert V._pfcf(None, 1, 1, "USD", "USD", srcs) is None
    assert V._pfcf(10.0, 1, None, "USD", "USD", srcs) is None
    mismatch = V._pfcf(10.0, 1, 5.0, "USD", "TWD", srcs)
    assert mismatch["value"].startswith("n/a")
    assert "TWD" in mismatch["value"]


def test_pfcf_negative_fcf_is_not_meaningful():
    srcs = {k: {"label": k, "url": "https://x"} for k in ("price", "shares", "fcf")}
    row = V._pfcf(10.0, 1000, -5.0, "USD", "USD", srcs)
    assert row["value"] == "n/m (FCF ≤ 0)"


def test_dispersion_row_width_and_pct_of_avg():
    ys = {k: {"label": k, "url": "https://x"} for k in ("avg", "low", "high")}
    row = V._dispersion_row("Next year", "EPS", 10.0, 8.0, 13.0, lambda v: f"{v:.2f}", "{:,.2f}", ys)
    assert row["cells"] == ["EPS · Next year", "10.00", "5.00", "50.0%"]
    assert row["src"]["inputs"] == [ys["high"], ys["low"], ys["avg"]]


def test_dispersion_row_skips_missing_or_zero_avg():
    ys = {k: {"label": k, "url": "https://x"} for k in ("avg", "low", "high")}
    assert V._dispersion_row("p", "EPS", None, 1, 2, str, "{}", ys) is None
    assert V._dispersion_row("p", "EPS", 0, 1, 2, str, "{}", ys) is None


def _trend(**periods):
    return {"earningsTrend": {"trend": [
        {"period": per, "endDate": "2027-01-31", "earningsEstimate": {"avg": {"raw": 2.0}, "low": {"raw": 1.5},
                                                                     "high": {"raw": 2.5}, "growth": {"raw": 0.1}},
         "revenueEstimate": {"avg": {"raw": 1000.0}, "low": {"raw": 900.0}, "high": {"raw": 1100.0}},
         "epsTrend": {"current": {"raw": 2.0}, "7daysAgo": {"raw": 1.9}},
         "epsRevisions": {"upLast7days": {"raw": 3}, "downLast7Days": {"raw": 1},
                          "upLast30days": {"raw": 4}, "downLast30days": {}}, **extra}
        for per, extra in periods.items()]}}


def test_estimate_blocks_include_plus5y_and_revision_counts_and_are_sourced():
    res = _trend(**{"0y": {}, "+5y": {}})
    blocks = V._estimate_blocks(res, lambda p: {"label": p, "url": "https://x"}, "USD")
    titles = [b["title"] for b in blocks]
    assert any(t.startswith("EPS estimates") for t in titles)
    eps = next(b for b in blocks if b["title"].startswith("EPS estimates"))
    assert any("Next 5 years" in r["cells"][0] for r in eps["rows"])
    counts = next(b for b in blocks if b["title"].startswith("EPS estimate revisions (analysts"))
    assert counts["rows"][0]["cells"][1:] == ["3", "1", "4", "—"]
    _all_sourced(blocks)


def test_estimate_blocks_without_trend_are_empty():
    assert V._estimate_blocks({}, lambda p: {"label": p, "url": "https://x"}, "USD") == []


def test_is_listing_flags_multi_ticker_posts_only():
    assert V._is_listing("AI • $IREN $39 • $NBIS $213 • $CIFR $15 • $CRWV $82", "MRVL")
    assert not V._is_listing("$MRVL will be $500 soon", "MRVL")
    assert not V._is_listing("$AMD and $MRVL both look strong", "MRVL")
    assert not V._is_listing(None, "MRVL")


def _pt(rows, close=100.0):
    return {"summary": {"targets": len(rows), "last_close": close},
            "targets": rows}


def _row(handle, price, view="author", text="$T to 120", url=None):
    return {"date": "2026-10-20", "handle": handle, "price_target": price, "view_holder": view, "text": text,
            "url": url or f"https://x.com/{handle}/status/1", "implied_upside_pct": round((price / 100 - 1) * 100, 1)}


def test_target_blocks_median_range_upside_and_tweet_sources():
    rows = [_row("a", 120.0), _row("b", 150.0), _row("c", 200.0), _row("d", 130.0, view="none"),
            _row("e", 999.0, text="$IREN $39 $NBIS $213 $CIFR $15")]
    blocks = V._target_blocks("T", _pt(rows))
    kv = blocks[0]["rows"]
    vals = {r["label"]: r["value"] for r in kv}
    assert vals["Tweet price targets"].startswith("3 targets")
    assert vals["Median target"] == "$150.00"
    assert vals["Range"] == "$120.00 – $200.00"
    assert vals["Median target vs last close"] == "+50.0%"
    tbl = blocks[1]["rows"]
    assert len(tbl) == 3
    assert all(r["src"]["url"].startswith("https://x.com/") for r in tbl)
    _all_sourced(blocks)


def test_target_blocks_empty_when_no_usable_target():
    assert V._target_blocks("T", None) == []
    assert V._target_blocks("T", _pt([_row("d", 130.0, view="none")])) == []


def test_target_blocks_without_close_omit_upside():
    blocks = V._target_blocks("T", _pt([_row("a", 120.0)], close=None))
    labels = [r["label"] for r in blocks[0]["rows"]]
    assert "Median target vs last close" not in labels
    _all_sourced(blocks)


def test_tweet_blocks_skip_non_usd(monkeypatch):
    called = []
    monkeypatch.setattr(sentiment, "price_targets", lambda *a, **k: called.append(a) or _pt([_row("a", 1.0)]))
    assert V._tweet_blocks("2308.TW", "TWD") == []
    assert called == []


def test_section_yahoo_failure_still_returns_tweet_blocks(monkeypatch):
    monkeypatch.setattr(V, "_fetch", lambda t: None)
    monkeypatch.setattr(sentiment, "price_targets", lambda *a, **k: _pt([_row("a", 120.0)]))
    out = V.section("T", None, None, {"currency": "USD"})
    assert out["id"] == "valuation" and out["title"] == "Valuation"
    assert out["blocks"][0]["title"] == "Price targets in tweets"


def test_section_returns_none_with_no_data(monkeypatch):
    monkeypatch.setattr(V, "_fetch", lambda t: None)

    def boom(*a, **k):
        raise RuntimeError("store missing")
    monkeypatch.setattr(sentiment, "price_targets", boom)
    assert V.section("T", None, None, None) is None


def test_section_survives_store_error_with_yahoo_blocks(monkeypatch):
    res = {"financialData": {"currentPrice": {"raw": 100.0}, "targetMeanPrice": {"raw": 120.0},
                             "financialCurrency": "USD", "freeCashflow": {"raw": 50.0}},
           "defaultKeyStatistics": {"sharesOutstanding": {"raw": 10.0}, "pegRatio": {"raw": 0.7}},
           "summaryDetail": {"trailingPE": {"raw": 20.0}}, "price": {"currency": "USD"}}
    monkeypatch.setattr(V, "_fetch", lambda t: res)

    def boom(*a, **k):
        raise RuntimeError("store missing")
    monkeypatch.setattr(sentiment, "price_targets", boom)
    out = V.section("T", None, None, {"currency": "USD"})
    titles = [b["title"] for b in out["blocks"]]
    assert "Consensus" in titles and "Multiples" in titles
    multiples = next(b for b in out["blocks"] if b["title"] == "Multiples")
    pfcf = next(r for r in multiples["rows"] if r["label"] == "Price / free cash flow")
    assert pfcf["value"] == "20.0x"  # 100 x 10 shares / 50 FCF
    _all_sourced(out["blocks"])


@pytest.mark.parametrize("ccy", ["KRW", "JPY", "TWD"])
def test_non_usd_consensus_targets_not_labelled_dollars(ccy):
    res = {"financialData": {"currentPrice": {"raw": 100.0}, "targetLowPrice": {"raw": 90.0},
                             "financialCurrency": ccy}, "price": {"currency": ccy}}
    blocks = V._yahoo_blocks("X", res)
    consensus = next(b for b in blocks if b["title"] == "Consensus")
    low = next(r for r in consensus["rows"] if r["label"] == "Target low")
    assert "$" not in low["value"] and low["value"].startswith(ccy)
