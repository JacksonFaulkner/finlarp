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
