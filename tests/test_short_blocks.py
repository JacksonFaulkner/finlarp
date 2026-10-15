"""derive.short: the S-section blocks built from the short-interest / short-volume parquet files (no network)."""
from datetime import date, datetime, timezone

import duckdb
import pytest

from derive import short


def _write(path, sql):
    duckdb.connect().execute(f"COPY ({sql}) TO '{path}' (FORMAT parquet)")


def _ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, 14, tzinfo=timezone.utc).timestamp())


def _close(sym, p):
    return {"label": f"close {sym} {p['close']}", "url": "https://example.test/close"}


@pytest.fixture
def paths(tmp_path):
    si, sv = tmp_path / "si.parquet", tmp_path / "sv.parquet"
    _write(si, """SELECT * FROM (VALUES
        ('SOUN', DATE '2026-08-31', 150e6, 10e6, 15.0, 'nasdaq', TIMESTAMP '2026-10-14'),
        ('SOUN', DATE '2026-09-15', 155e6, 12e6, 12.9, 'nasdaq', TIMESTAMP '2026-10-14'),
        ('SOUN', DATE '2026-09-30', 159e6, 16e6, 9.9, 'nasdaq', TIMESTAMP '2026-10-14'),
        ('IONQ', DATE '2026-09-30', 10e6, NULL, 3.0, 'yahoo', TIMESTAMP '2026-10-14')
      ) t(ticker, settlement_date, short_interest, avg_daily_volume, days_to_cover, source, fetched_at)""")
    days = [date(2026, 10, d) for d in (1, 2, 5, 6, 7, 8, 9, 12, 13, 14)]
    vals = ",".join(f"('SOUN', DATE '{d}', {50 + i}, 0, 100, {0.5 + i / 100})" for i, d in enumerate(days))
    _write(sv, f"SELECT * FROM (VALUES {vals}) t(ticker, date, short_volume, short_exempt_volume, total_volume, short_ratio)")
    return si, sv


@pytest.fixture
def hist():
    out, d, px = [], date(2026, 8, 1), 8.0
    while d <= date(2026, 10, 14):
        if d.weekday() < 5:
            out.append({"t": _ts(d), "close": round(px, 2)})
            px -= 0.04
        d = date.fromordinal(d.toordinal() + 1)
    return out


def test_no_data_gives_a_pointer_not_an_empty_section(tmp_path):
    (b,) = short.short_blocks("NOPE", [], None, None, _close, si_path=tmp_path / "a", sv_path=tmp_path / "b")
    assert b["type"] == "text" and "short_interest.py" in b["text"] and b["src"]["url"]


def test_headline_rows_carry_formulas_and_sources(paths, hist):
    si, sv = paths
    blocks = short.short_blocks("SOUN", hist, 446e6, {"label": "Yahoo shares", "url": "https://y.test"}, _close, si, sv)
    kv = next(b for b in blocks if b["type"] == "kv")
    rows = {r["label"].strip(): r for r in kv["rows"]}
    assert rows["short interest"]["value"].startswith("159,000,000 sh") and "2026-09-30" in rows["short interest"]["value"]
    assert rows["% of shares outstanding"]["value"] == "35.7%"
    assert "446,000,000" in rows["% of shares outstanding"]["src"]["formula"]
    assert rows["days to cover"]["value"] == "9.9"
    assert rows["vs prior settlement"]["value"] == "+2.6%"
    assert rows["vs 2 settlements ago (~1 month)"]["value"] == "+6.0%"
    assert rows["price vs prior settlement"]["value"].startswith("-")
    assert rows["short volume ratio, last 5 sessions"]["src"]["formula"].startswith("Σ short volume")
    assert len(rows["vs prior sessions"]["src"]["inputs"]) == 5 + 5  # 10 sessions: 5 recent + the 5 before


def test_every_value_has_a_source_and_series_line_up(paths, hist):
    si, sv = paths
    blocks = short.short_blocks("SOUN", hist, None, None, _close, si, sv)
    for b in blocks:
        for r in b.get("rows", []):
            assert r["src"], (b["title"], r)
        for p in b.get("points", []):
            assert p["src"], (b["title"], p)
    series = [b for b in blocks if b["type"] == "series"]
    assert [b["title"] for b in series][:2] == ["Short interest by settlement", "Price at the same settlements"]
    assert [p["x"] for p in series[0]["points"]] == [p["x"] for p in series[1]["points"]] == ["2026-08-31", "2026-09-15", "2026-09-30"]
    assert series[0]["points"][-1]["y"] == pytest.approx(159.0)
    vol = next(b for b in series if b["title"].startswith("Short volume ratio"))
    assert len(vol["points"]) == 10 and vol["points"][0]["y"] == pytest.approx(50.0)
    table = next(b for b in blocks if b["type"] == "table")
    assert table["rows"][0]["cells"][2] == "—" and table["rows"][-1]["cells"][0] == "2026-09-30"


def test_yahoo_fallback_ticker_still_renders(paths, hist):
    si, sv = paths
    blocks = short.short_blocks("IONQ", hist, None, None, _close, si, sv)
    kv = next(b for b in blocks if b["type"] == "kv")
    first = kv["rows"][0]
    assert "Yahoo Finance key statistics" in first["src"]["label"]
    assert not any(b["type"] == "table" for b in blocks), "one settlement is not a trend"
