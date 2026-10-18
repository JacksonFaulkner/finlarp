"""jobs.squeeze_scan: fuel filter + trigger tags over small synthetic parquet files (no network)."""
import duckdb

from jobs import squeeze_scan


def _write(path, sql):
    duckdb.connect().execute(f"COPY ({sql}) TO '{path}' (FORMAT parquet)")


def test_scan_tags_triggered_and_setup(tmp_path):
    bars = tmp_path / "bars.parquet"
    rows = []
    for sym, last in (("AAA", 13.0), ("BBB", 10.0)):  # AAA gaps up on volume at the end, BBB is flat
        for i in range(25):
            close, vol = (10.0, 1_000_000) if i < 24 else (last, 5_000_000 if sym == "AAA" else 1_000_000)
            rows.append(f"('{sym}', TIMESTAMPTZ '2026-09-{i + 1:02d} 00:00:00+00' , {close}, {close}, {close}, {close}, {vol})"
                        if i < 24 else
                        f"('{sym}', TIMESTAMPTZ '2026-10-01 00:00:00+00', {close}, {close}, {close}, {close}, {vol})")
    _write(bars, f"SELECT * FROM (VALUES {','.join(rows)}) t(symbol, ts_event, open, high, low, close, volume)")
    si, sv, pr = tmp_path / "si.parquet", tmp_path / "sv.parquet", tmp_path / "pr.parquet"
    _write(si, """SELECT * FROM (VALUES
        ('AAA', DATE '2026-09-15', 18e6, 1e6, 18.0), ('AAA', DATE '2026-09-30', 20e6, 1e6, 20.0),
        ('BBB', DATE '2026-09-15', 18e6, 1e6, 18.0), ('BBB', DATE '2026-09-30', 20e6, 1e6, 20.0),
        ('CCC', DATE '2026-09-30', 1e6, 1e6, 1.0)) t(ticker, settlement_date, short_interest, avg_daily_volume, days_to_cover)""")
    _write(sv, "SELECT * FROM (VALUES ('AAA', DATE '2026-09-30', 60, 100), ('BBB', DATE '2026-09-30', 50, 100)) t(ticker, date, short_volume, total_volume)")
    _write(pr, "SELECT * FROM (VALUES ('AAA', 1.0e9, 'USD'), ('BBB', 1.0e9, 'USD'), ('CCC', 1.0e9, 'USD')) t(ticker, market_cap, currency)")
    rel, ev = tmp_path / "rel.parquet", tmp_path / "ev.parquet"
    _write(rel, "SELECT 'ZZZ' ticker, current_date filed, 'nothing' AS text WHERE false")
    _write(ev, "SELECT 'ZZZ' ticker, current_date filed, '1.01' item WHERE false")
    kw = dict(bars=bars, si_path=si, sv_path=sv, profiles=pr, releases=rel, events=ev)
    out = {r["ticker"]: r for r in squeeze_scan.scan(**kw)}
    assert set(out) == {"AAA", "BBB"}  # CCC fails the short % / days-to-cover filter
    assert out["AAA"]["status"] == "TRIGGERED" and "up day on volume" in out["AAA"]["triggers"]
    assert out["BBB"]["status"] == "SETUP"
    assert out["AAA"]["score"] > out["BBB"]["score"]


def test_pending_deal_is_hidden_only_when_pinned_and_filed(tmp_path):
    bars = tmp_path / "bars.parquet"
    rows = []
    for sym, closes in (("PIN", [10.00 + 0.01 * (i % 3) for i in range(25)]),  # pinned and has a merger release
                        ("ACQ", [10.0 + i for i in range(25)]),  # moving, has a merger release (the acquirer)
                        ("QUIET", [10.00 + 0.01 * (i % 3) for i in range(25)])):  # pinned, no filing evidence
        for i, c in enumerate(closes):
            rows.append(f"('{sym}', TIMESTAMPTZ '2026-09-{i + 1:02d} 00:00:00+00', {c}, {c}, {c}, {c}, 1000000)")
    _write(bars, f"SELECT * FROM (VALUES {','.join(rows)}) t(symbol, ts_event, open, high, low, close, volume)")
    si, sv, pr = tmp_path / "si.parquet", tmp_path / "sv.parquet", tmp_path / "pr.parquet"
    vals = ",".join(f"('{t}', DATE '2026-09-30', 20e6, 1e6, 20.0)" for t in ("PIN", "ACQ", "QUIET"))
    _write(si, f"SELECT * FROM (VALUES {vals}) t(ticker, settlement_date, short_interest, avg_daily_volume, days_to_cover)")
    _write(sv, "SELECT * FROM (VALUES ('PIN', DATE '2026-09-30', 60, 100)) t(ticker, date, short_volume, total_volume)")
    _write(pr, "SELECT * FROM (VALUES ('PIN', 1.0e9, 'USD'), ('ACQ', 1.0e9, 'USD'), ('QUIET', 1.0e9, 'USD')) t(ticker, market_cap, currency)")
    rel, ev = tmp_path / "rel.parquet", tmp_path / "ev.parquet"
    _write(rel, """SELECT * FROM (VALUES ('PIN', current_date, 'entered into an Agreement and Plan of Merger'),
                                          ('ACQ', current_date, 'entered into an Agreement and Plan of Merger'))
                   t(ticker, filed, text)""")
    _write(ev, "SELECT 'ZZZ' ticker, current_date filed, '1.01' item WHERE false")
    kw = dict(bars=bars, si_path=si, sv_path=sv, profiles=pr, releases=rel, events=ev, min_si_pct=0, min_dtc=0)
    assert {r["ticker"] for r in squeeze_scan.scan(**kw)} == {"ACQ", "QUIET"}
    kept = {r["ticker"]: r for r in squeeze_scan.scan(**kw, include_deals=True)}
    assert kept["PIN"]["pending_deal"] and not kept["ACQ"]["pending_deal"] and not kept["QUIET"]["pending_deal"]
