"""Intraday feed: Yahoo protobuf decoding and folding ticks into 1-minute bars."""
from __future__ import annotations

import struct

from sources.intraday_stream import Feed, decode_tick, minute_of


def _varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _zz(n: int) -> int:
    return (n << 1) ^ (n >> 63)


def tick_bytes(sym: str, price: float, t_ms: int, day_vol: int | None = None) -> bytes:
    s = sym.encode()
    out = b"\x0a" + _varint(len(s)) + s  # 1: id
    out += b"\x15" + struct.pack("<f", price)  # 2: price
    out += b"\x18" + _varint(_zz(t_ms))  # 3: time (sint64 ms)
    out += b"\x2a\x03NMS"  # 5: exchange, ignored
    if day_vol is not None:
        out += b"\x48" + _varint(_zz(day_vol))  # 9: dayVolume
    return out


def test_decodes_a_captured_yahoo_message():
    # first message seen from the live stream (WDC)
    raw = bytes.fromhex("0a035744431529bcb84318c093fab2a7682a034e4d533008380145baf33cc048b2ebf8026500d733c1")
    tick = decode_tick(raw)
    assert tick is not None
    assert tick["sym"] == "WDC"
    assert 360 < tick["price"] < 380
    assert tick["day_vol"] and tick["day_vol"] > 0
    assert 1.79e9 < tick["t"] < 1.80e9


def test_decode_roundtrip_and_garbage():
    t = decode_tick(tick_bytes("MKSI", 236.5, 1_791_994_412_000, 123_456))
    assert t == {"sym": "MKSI", "price": 236.5, "t": 1_791_994_412.0, "day_vol": 123_456}
    assert decode_tick(b"") is None
    assert decode_tick(b"\xff\xff\xff") is None
    assert decode_tick(tick_bytes("X", 1.0, 1)[:5]) is None  # truncated


def test_ticks_fold_into_minute_bars_with_volume_deltas():
    f = Feed()
    f.symbols = ["WDC"]
    base = 1_791_994_380  # a minute boundary
    assert minute_of(base + 59) == base
    for price, dv, dt in [(100.0, 1000, 5), (101.5, 1300, 20), (99.0, 1350, 50), (100.2, 1400, 65)]:
        f.on_tick({"sym": "WDC", "price": price, "t": base + dt, "day_vol": dv})
    first, second = f.bars["WDC"][base], f.bars["WDC"][base + 60]
    # the first tick only sets the volume baseline, later ticks add the delta
    assert first == [base, 100.0, 101.5, 99.0, 99.0, 350]
    assert second == [base + 60, 100.2, 100.2, 100.2, 100.2, 50]
    assert f.dirty == {"WDC"}


def test_ignores_symbols_that_are_not_watched_and_negative_volume_steps():
    f = Feed()
    f.symbols = ["WDC"]
    f.on_tick({"sym": "ZZZZ", "price": 1.0, "t": 1_791_994_380, "day_vol": 5})
    assert "ZZZZ" not in f.bars
    f.on_tick({"sym": "WDC", "price": 10.0, "t": 1_791_994_380, "day_vol": 500})
    f.on_tick({"sym": "WDC", "price": 10.5, "t": 1_791_994_385, "day_vol": 400})  # counter went backwards
    assert f.bars["WDC"][1_791_994_380][5] == 0


def test_seed_takes_minutes_from_databento_and_fills_the_tail_from_yahoo(monkeypatch, capsys):
    import json

    import sources.intraday_stream as mod

    now = 1_791_994_380 + 30  # a fixed clock; the Databento cutoff is DB_LAG_S before it
    session_start = now - 3600
    yahoo_minute = mod.minute_of(now - 3600)  # Databento has this minute too: it must win
    tail_minute = mod.minute_of(now - 120)  # newer than Databento's cutoff: Yahoo fills it
    fetched = []

    def fake_databento(sym, start, end):
        fetched.append((sym, start, end))
        return {yahoo_minute: [yahoo_minute, 10.0, 11.0, 9.0, 10.5, 500]}

    chart = {
        "meta": {"previousClose": 9.5, "currentTradingPeriod": {"regular": {"start": 1, "end": 2}}},
        "bars": [
            {"t": yahoo_minute, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1},
            {"t": tail_minute, "open": 20.0, "high": 21.0, "low": 19.0, "close": 20.5, "volume": 7},
        ],
    }
    monkeypatch.setattr(mod.time, "time", lambda: now)
    monkeypatch.setattr(mod, "session_start_epoch", lambda: session_start)
    monkeypatch.setattr(mod, "databento_minutes", fake_databento)
    monkeypatch.setattr(mod, "db_available_end", lambda: now + 10**9)
    monkeypatch.setattr(mod.yahoo_live, "_chart", lambda *a, **k: chart)
    monkeypatch.setattr(mod.yahoo, "new_session", lambda: None)

    f = Feed()
    f.seed("MKSI")
    seed = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    bars = {b[0]: b for b in seed["bars"]}
    assert bars[yahoo_minute][1] == 10.0  # Databento's open, not Yahoo's
    assert bars[tail_minute][1] == 20.0  # Yahoo's tail
    assert fetched == [("MKSI", session_start, mod.minute_of(now - mod.DB_LAG_S))]
    assert seed["prev_close"] == 9.5

    f.seed("MKSI")  # a resync fetches only what is new since the last cutoff: nothing here
    assert len(fetched) == 1


def test_seed_does_not_ask_databento_past_its_license_and_falls_back_to_yahoo(monkeypatch, capsys):
    import json

    import sources.intraday_stream as mod

    now = 1_791_994_380 + 30
    yahoo_minute = mod.minute_of(now - 3600)
    fetched = []
    monkeypatch.setattr(mod.time, "time", lambda: now)
    monkeypatch.setattr(mod, "session_start_epoch", lambda: now - 3600)
    monkeypatch.setattr(mod, "db_available_end", lambda: now - 7200)  # license ends before the session
    monkeypatch.setattr(mod, "databento_minutes", lambda *a: fetched.append(a) or {})
    chart = {
        "meta": {"previousClose": 9.5, "currentTradingPeriod": {"regular": {"start": 1, "end": 2}}},
        "bars": [{"t": yahoo_minute, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1}],
    }
    monkeypatch.setattr(mod.yahoo_live, "_chart", lambda *a, **k: chart)
    monkeypatch.setattr(mod.yahoo, "new_session", lambda: None)

    Feed().seed("MKSI")
    seed = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert fetched == []  # no request the license would reject
    assert {b[0]: b for b in seed["bars"]}[yahoo_minute][1] == 1.0  # Yahoo alone
