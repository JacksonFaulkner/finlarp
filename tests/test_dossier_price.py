"""Dossier Price tab: pure logic on synthetic bars, plus one local-data smoke test."""

from datetime import date, timedelta

import pytest

from derive.dossier import validate
from derive.dossier_tabs import price
from sources import universe, yahoo_profile

START = date(2025, 1, 1)


def make_bars(closes, spread=1.0, volume=1000, opens=None):
    """Consecutive-day bars; open defaults to close. Dates only need to be ordered."""
    out = []
    for i, c in enumerate(closes):
        o = opens[i] if opens is not None else c
        out.append(price._bar(START + timedelta(days=i), o, c + spread, c - spread, c, volume))
    return out


@pytest.fixture()
def no_live(monkeypatch):
    """Stub the live calls (SPY history, Yahoo beta) so tests never hit the network."""
    monkeypatch.setattr(price, "_spy_by_day", lambda: {})
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: None)


def test_to_bars_sorts_dedupes_and_drops_missing_close():
    rows = [
        (date(2025, 1, 3), 1, 2, 0.5, 1.5, 10),
        (date(2025, 1, 2), 1, 2, 0.5, None, 10),  # no close: dropped
        (date(2025, 1, 1), 1, 2, 0.5, 1.2, 10),
        (date(2025, 1, 3), 9, 9, 9, 9.5, 99),  # duplicate day: last one wins
    ]
    bars = price._to_bars(rows)
    assert [b["d"] for b in bars] == [date(2025, 1, 1), date(2025, 1, 3)]
    assert bars[-1]["close"] == 9.5 and bars[-1]["volume"] == 99


def test_trend_uptrend_and_downtrend():
    up = make_bars([100 + i for i in range(300)])
    down = make_bars([400 - i for i in range(300)])
    t_up = price._ma_table("X", up)
    t_down = price._ma_table("X", down)
    assert t_up["rows"][-1]["cells"][1] == "uptrend"
    assert t_down["rows"][-1]["cells"][1] == "downtrend"
    # 50-day MA of a rising line ending at 399: mean of 350..399
    assert t_up["rows"][0]["cells"][1] == f"{sum(range(350, 400)) / 50:,.2f}"


def test_ma_rows_degrade_when_short():
    bars = make_bars([100 + i for i in range(60)])
    table = price._ma_table("X", bars)
    assert table["rows"][0]["cells"][1] != "—"  # 50-day: 60 closes available
    assert table["rows"][1]["cells"][1:] == ["—", "—"]  # 200-day: not enough closes
    assert len(table["rows"]) == 2  # no trend row without both averages
    assert price._range_kv("X", bars) == []  # no 52-week block under 252 sessions


def test_range_kv_high_low_and_off_high():
    bars = make_bars([100.0] * 260)
    bars[-50] = price._bar(bars[-50]["d"], 130, 135, 129, 130, 1000)  # intraday high 135
    bars[-1] = price._bar(bars[-1]["d"], 100, 105, 90, 100, 1000)  # intraday low 90
    rows = {r["label"]: r for r in price._range_kv("X", bars)}
    assert rows["52-week high (intraday)"]["value"] == "135.00"
    assert rows["52-week low (intraday)"]["value"] == "90.00"
    # (135 - 100) / 135 * 100 = 25.9 %, shown as a negative offset
    assert rows["% off 52-week high"]["value"] == "-25.9%"


def test_returns_table_windows_and_values():
    closes = [100 + i for i in range(300)]  # close on the last bar: 399
    bars = make_bars(closes)
    table = price._returns_table("X", bars)
    names = [r["cells"][0] for r in table["rows"]]
    assert names == ["1 week", "1 month", "3 months", "6 months", "1 year"]
    one_week = table["rows"][0]
    # 5 sessions back from 399 is 394: (399 - 394) / 394 * 100 = +1.3 %
    assert one_week["cells"][2] == "394.00"
    assert one_week["cells"][3] == "+1.3%"


def test_relative_strength_uses_spy_on_same_dates(monkeypatch):
    closes = [100 + i for i in range(120)]
    bars = make_bars(closes)
    s_bar, e_bar = bars[-(price.RS_DAYS + 1)], bars[-1]
    spy_flat = {b["d"]: {"t": b["t"], "close": 100.0} for b in bars}
    monkeypatch.setattr(price, "_spy_by_day", lambda: spy_flat)
    rows = {r["label"]: r for r in price._rs_rows("X", bars)}
    sym_r = (e_bar["close"] - s_bar["close"]) / s_bar["close"] * 100
    assert rows[f"X {price.RS_DAYS}-session return"]["value"] == f"{sym_r:+.1f}%"
    assert rows[f"SPY {price.RS_DAYS}-session return"]["value"] == "+0.0%"
    rs_label = f"relative strength vs SPY ({price.RS_DAYS} sessions)"
    assert rows[rs_label]["value"] == f"{sym_r:+.1f}%"


def test_relative_strength_omitted_without_spy(monkeypatch):
    bars = make_bars([100 + i for i in range(120)])
    monkeypatch.setattr(price, "_spy_by_day", lambda: {})
    assert price._rs_rows("X", bars) == []


def test_realized_vol_flat_is_zero_and_atr_on_constant_range():
    flat = make_bars([100.0] * 80, spread=1.0)  # high-low = 2, no moves
    risk = {r["label"]: r for r in price._risk_rows("X", flat)}
    assert risk["realized volatility, 30 sessions (annualized)"]["value"] == "0.0%"
    assert risk["ATR(14)"]["value"] == "2.00"


def test_gap_count_up_and_down():
    closes = [100.0] * 80
    opens = [100.0] * 80
    for i in (70, 71, 72):
        opens[i] = 104.0  # +4 % gap up vs prior close 100
    for i in (75, 76):
        opens[i] = 96.0  # -4 % gap down
    opens[77] = 102.0  # +2 %: under the 3 % threshold
    bars = make_bars(closes, opens=opens)
    gap = {r["label"]: r for r in price._risk_rows("X", bars)}[
        f"opens more than {price.GAP_PCT:g}% from prior close, {price.GAP_SESSIONS} sessions"]
    assert gap["value"] == "5 (3 up, 2 down)"


def test_volume_ratio_and_dollar_adv():
    bars = make_bars([50.0] * 70, volume=1000)
    bars[-1] = price._bar(bars[-1]["d"], 50, 51, 49, 50, 3000)  # last session 3x the rest
    rows = {r["label"]: r for r in price._volume_rows("X", bars)}
    avg20 = (19 * 1000 + 3000) / 20
    assert rows["last session volume vs 20-day average"]["value"] == f"{3000 / avg20:.2f}x"
    assert rows["dollar volume, 20-day ADV"]["value"] == price._money(
        (19 * 50 * 1000 + 50 * 3000) / 20)


def test_beta_row_and_failure(monkeypatch):
    monkeypatch.setattr(price.yahoo, "new_session", lambda: None)
    monkeypatch.setattr(yahoo_profile, "fetch", lambda *a, **k: {"summaryDetail": {"beta": {"raw": 1.5}}})
    row = price._beta_row("X")
    assert row["value"] == "1.50"
    assert row["src"]["url"] == "https://finance.yahoo.com/quote/X/"
    def down(*a, **k):
        raise RuntimeError("down")

    monkeypatch.setattr(yahoo_profile, "fetch", down)
    assert price._beta_row("X") is None


def test_section_sourced_and_degrades_without_live(monkeypatch, no_live):
    bars = make_bars([100 + i * 0.5 for i in range(300)])
    monkeypatch.setattr(price, "_bars", lambda con, t: bars)
    sec = price.section("x", None, None, None)
    assert sec["id"] == "price" and sec["title"] == "Price"
    kinds = [b["type"] for b in sec["blocks"]]
    assert kinds[0] == "series" and "table" in kinds and "kv" in kinds
    assert validate({"sections": [sec]}) == []
    assert all(r["label"] != "beta (live, Yahoo summaryDetail)" for b in sec["blocks"] if b["type"] == "kv"
               for r in b["rows"])


def test_section_none_when_no_bars_or_error(monkeypatch):
    monkeypatch.setattr(price, "_bars", lambda con, t: [])
    assert price.section("X", None, None, None) is None

    def boom(con, t):
        raise RuntimeError("parquet unreadable")

    monkeypatch.setattr(price, "_bars", boom)
    assert price.section("X", None, None, None) is None


def test_section_local_data_smoke(no_live):
    if not any(universe.DATA_ROOT.joinpath("market/databento/bars_1d").glob("*.parquet")):
        pytest.skip("no bars_1d parquet on disk")
    import duckdb

    sec = price.section("MRVL", duckdb.connect(), None, None)
    assert sec is not None
    series = sec["blocks"][0]
    assert series["type"] == "series" and len(series["points"]) > 300
    assert validate({"sections": [sec]}) == []
