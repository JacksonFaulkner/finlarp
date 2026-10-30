"""derive.dossier_tabs.positioning: pure logic on synthetic inputs, plus one section run over temp parquet and json files
(no network: the live Yahoo float is monkeypatched)."""
import json
from datetime import date, datetime

import duckdb
import pytest

from derive.dossier import validate
from derive.dossier_tabs import positioning as P
from sources import short_interest as feed


def _row(block, label):
    return next(r for r in block["rows"] if r["label"] == label)


def _kv(sec, prefix):
    return next(b for b in sec["blocks"] if b["type"] == "kv" and b["title"].startswith(prefix))


# ---- options ---------------------------------------------------------------------------------------------------------

D = date(2026, 10, 15)
LEGS = [  # (expiry, type, strike, spot, volume, open_interest, iv)
    (date(2026, 10, 16), "CALL", 100, 98.0, 1000, 10, 0.90),  # 1 day out: skipped for ATM IV
    (date(2026, 10, 16), "PUT", 100, 98.0, 0, 5, 0.95),
    (date(2026, 10, 23), "CALL", 90, 98.0, 100, 40, 0.50),
    (date(2026, 10, 23), "PUT", 90, 98.0, 50, 10, 0.60),
    (date(2026, 10, 23), "CALL", 100, 98.0, 150, 30, 0.40),
    (date(2026, 10, 23), "PUT", 100, 98.0, 100, 290, 0.42),
]


def test_put_call_and_atm_iv_use_all_expiries_and_skip_one_day_out():
    blocks = P._options_blocks("TST", datetime(2026, 10, 15, 16, 26), LEGS)
    assert len(blocks) == 1
    b = blocks[0]
    assert "thin" in b["title"] and "2026-10-15" in b["title"]
    # calls volume 1000+100+150 = 1250, puts 0+50+100 = 150 -> 0.12; OI calls 80, puts 305 -> 3.81
    assert _row(b, "put/call ratio, volume")["value"] == "0.12"
    assert _row(b, "put/call ratio, open interest")["value"] == "3.81"
    # first expiry >= 7 days out is 10-23; nearest strike to spot 98 is 100; mean of 0.40 and 0.42
    atm = _row(b, "ATM implied vol")
    assert atm["value"] == "41.0%"
    assert "call IV 40.0% and put IV 42.0% at strike 100" in atm["src"]["formula"]
    assert _row(b, "snapshot")["value"] == "2026-10-15 16:26 ET · 2 expiries"


def test_put_call_is_dash_without_call_volume_and_atm_is_dash_without_spot():
    legs = [(date(2026, 10, 23), "PUT", 90, None, 50, 10, 0.6)]
    b = P._options_blocks("TST", datetime(2026, 10, 15, 16, 26), legs)[0]
    assert _row(b, "put/call ratio, volume")["value"] == "—"
    assert _row(b, "ATM implied vol")["value"] == "—"
    assert "spot at snapshot" not in {r["label"] for r in b["rows"]}


def test_every_options_row_is_sourced():
    sec = {"id": "positioning", "blocks": P._options_blocks("TST", datetime(2026, 10, 15, 16, 26), LEGS)}
    assert validate({"sections": [sec]}) == []


# ---- short interest --------------------------------------------------------------------------------------------------

SI = [  # oldest first: (settlement_date, short_interest, days_to_cover, source)
    (date(2026, 8, 31), 100e6, 5.0, "nasdaq"),
    (date(2026, 9, 15), 110e6, 6.0, "nasdaq"),
    (date(2026, 9, 30), 121e6, 7.5, "nasdaq"),
]


def test_si_changes_are_derived_and_float_none_says_unavailable():
    b = P._si_block("TST", SI, None)
    assert _row(b, "short interest")["value"] == "121,000,000 sh · settled 2026-09-30"
    assert _row(b, "days to cover")["value"] == "7.5"
    assert _row(b, "change vs prior settlement")["value"] == "+10.0%"
    assert _row(b, "change vs prior settlement")["new"] is False
    two = _row(b, "change vs 2 settlements ago")
    assert two["value"] == "+21.0%" and two["new"] is True
    assert two["src"]["formula"] == "121,000,000 / 100,000,000 − 1 = +21.0%"
    assert _row(b, "short % of float")["value"] == "unavailable"
    assert validate({"sections": [{"id": "x", "blocks": [b]}]}) == []


def test_si_float_shown_as_percent():
    b = P._si_block("TST", SI, 12.34)
    assert _row(b, "short % of float")["value"] == "12.3%"


def test_si_without_rows_says_so():
    b = P._si_block("TST", [], None)
    assert _row(b, "short interest")["value"] == "no settlement rows yet"


# ---- short volume ----------------------------------------------------------------------------------------------------

def _vol(n: int, sv: float = 40.0, tv: float = 100.0):
    """n oldest-first sessions of equal ratio, one day apart."""
    return [(date(2026, 9, 1 + i), sv, tv) for i in range(n)]


def test_short_volume_windows_and_series():
    vol = _vol(20, 40.0, 100.0)
    vol[-5:] = [(d, 60.0, 100.0) for d, _, _ in vol[-5:]]  # last 5 at 60%
    blocks = P._volume_blocks("TST", vol)
    kv, series = blocks
    assert kv["type"] == "kv" and series["type"] == "series"
    assert _row(kv, "last 5 sessions")["value"] == "60%"
    # last 20: (15 * 40 + 5 * 60) / 20 = 45
    assert _row(kv, "last 20 sessions")["value"] == "45%"
    assert _row(kv, "5 vs 20 sessions")["value"] == "+15 pts"
    assert series["unit"] == "% of volume" and len(series["points"]) == 20
    assert series["points"][-1]["y"] == 60.0
    assert validate({"sections": [{"id": "x", "blocks": blocks}]}) == []


def test_short_volume_with_fewer_than_five_sessions_has_series_only():
    blocks = P._volume_blocks("TST", _vol(3))
    assert [b["type"] for b in blocks] == ["series"]


def test_short_volume_empty_gives_no_blocks():
    assert P._volume_blocks("TST", []) == []


# ---- squeeze screen --------------------------------------------------------------------------------------------------

def test_squeeze_rank_and_triggers_from_file(tmp_path, monkeypatch):
    path = tmp_path / "latest.json"
    path.write_text(json.dumps([
        {"ticker": "WOLF", "score": 8.19, "status": "TRIGGERED", "triggers": ["bounce off 20d low"], "px_date": "2026-10-26"},
        {"ticker": "TST", "score": 5.0, "status": "TRIGGERED", "triggers": ["close > 10d high", "up day on volume"],
         "px_date": "2026-10-26"},
    ]))
    monkeypatch.setattr(P, "SQUEEZE", path)
    b = P._squeeze_block("TST")
    assert b["title"].startswith("Squeeze screen · file dated ")
    assert _row(b, "rank")["value"] == "2 of 2 · score 5.0"
    assert _row(b, "status")["value"] == "TRIGGERED"
    assert _row(b, "triggers")["value"] == "close > 10d high, up day on volume"
    assert "prices through 2026-10-26" in _row(b, "rank")["src"]["inputs"][0]["label"]
    assert validate({"sections": [{"id": "x", "blocks": [b]}]}) == []


def test_squeeze_ticker_not_listed(tmp_path, monkeypatch):
    path = tmp_path / "latest.json"
    path.write_text(json.dumps([{"ticker": "WOLF", "score": 8.19, "status": "SETUP", "triggers": []}]))
    monkeypatch.setattr(P, "SQUEEZE", path)
    b = P._squeeze_block("ZZZ")
    assert "not listed among 1 names" in _row(b, "squeeze screen")["value"]


def test_squeeze_missing_file_gives_none(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "SQUEEZE", tmp_path / "nope.json")
    assert P._squeeze_block("TST") is None


# ---- section end to end ----------------------------------------------------------------------------------------------

@pytest.fixture
def local(tmp_path, monkeypatch):
    """Temp short / options / squeeze files for ticker TST, and no live float call."""
    si, sv = tmp_path / "si.parquet", tmp_path / "sv.parquet"
    duckdb.connect().execute(f"""COPY (SELECT * FROM (VALUES
        ('TST', DATE '2026-08-31', 100e6, 5.0, 'nasdaq'),
        ('TST', DATE '2026-09-15', 110e6, 6.0, 'nasdaq'),
        ('TST', DATE '2026-09-30', 121e6, 7.5, 'nasdaq')
      ) t(ticker, settlement_date, short_interest, days_to_cover, source)) TO '{si}' (FORMAT parquet)""")
    vrows = ", ".join(f"('TST', DATE '2026-09-{i:02d}', {40 + i}.0, 100.0)" for i in range(1, 26))
    duckdb.connect().execute(f"""COPY (SELECT * FROM (VALUES {vrows}) t(ticker, date, short_volume, total_volume))
        TO '{sv}' (FORMAT parquet)""")
    opt_dir = tmp_path / "options" / "etrade" / "date=2026-10-15"
    opt_dir.mkdir(parents=True)
    legs = ", ".join(
        f"(TIMESTAMP '2026-10-15 16:26:00', 'TST', DATE '{e}', '{t}', {k}, 98.0, {v}, {oi}, 0.5)"
        for e, t, k, v, oi in [("2026-10-23", "CALL", 100, 150, 30), ("2026-10-23", "PUT", 100, 100, 290)])
    duckdb.connect().execute(f"""COPY (SELECT * FROM (VALUES {legs})
        t(snap_ts, ticker, expiry, type, strike, spot, volume, open_interest, iv)) TO '{opt_dir / "162600.parquet"}'
        (FORMAT parquet)""")
    sq = tmp_path / "latest.json"
    sq.write_text(json.dumps([{"ticker": "TST", "score": 4.0, "status": "SETUP", "triggers": [], "px_date": "2026-10-26"}]))
    monkeypatch.setattr(feed, "INTEREST", si)
    monkeypatch.setattr(feed, "VOLUME", sv)
    monkeypatch.setattr(P, "OPTIONS_DIR", tmp_path / "options" / "etrade")
    monkeypatch.setattr(P, "SQUEEZE", sq)
    monkeypatch.setattr(P, "_float_short_pct", lambda t: 12.34)
    return tmp_path


def test_section_end_to_end_is_sourced(local):
    sec = P.section("tst", duckdb.connect(), None, None)
    assert sec["id"] == "positioning" and sec["title"] == "Positioning"
    titles = [b["title"] for b in sec["blocks"]]
    assert titles[0].startswith("Short interest · settled 2026-09-30")
    assert any(t.startswith("Squeeze screen") for t in titles)
    assert any("thin" in t for t in titles)
    assert _row(sec["blocks"][0], "short % of float")["value"] == "12.3%"
    series = next(b for b in sec["blocks"] if b["type"] == "series")
    assert len(series["points"]) == 25
    assert validate({"sections": [sec]}) == []


def test_section_without_options_snapshot_omits_options(local, monkeypatch):
    monkeypatch.setattr(P, "OPTIONS_DIR", local / "no-such-dir")
    sec = P.section("TST", duckdb.connect(), None, None)
    assert not any("Options" in b.get("title", "") for b in sec["blocks"])


def test_section_returns_none_without_local_data_and_skips_live_call(tmp_path, monkeypatch):
    monkeypatch.setattr(feed, "INTEREST", tmp_path / "a.parquet")
    monkeypatch.setattr(feed, "VOLUME", tmp_path / "b.parquet")
    monkeypatch.setattr(P, "OPTIONS_DIR", tmp_path / "options")
    monkeypatch.setattr(P, "SQUEEZE", tmp_path / "latest.json")

    def boom(t):
        raise AssertionError("live float fetch should not run without local data")
    monkeypatch.setattr(P, "_float_short_pct", boom)
    assert P.section("ZZZZ", duckdb.connect(), None, None) is None


def test_float_fetch_fails_soft(monkeypatch):
    from sources import yahoo

    def bad_session():
        raise RuntimeError("network down")
    monkeypatch.setattr(yahoo, "new_session", bad_session)
    assert P._float_short_pct("TST") is None
