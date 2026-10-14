"""Live intraday feed for the TUI grid (screens/intraday): one process, JSON lines both ways.

Why not poll: the chart REST endpoint is called once per ticker to seed the day, then every trade
arrives over Yahoo's websocket (one connection carries every symbol) and is folded into 1-minute
bars here. A slow REST resync (RESYNC_S) heals anything the socket missed. The Rust side
aggregates 1m into 5m/15m, so switching interval never touches the network.

    uv run python -m sources.intraday_stream --serve

stdin (one JSON object per line):
    {"cmd": "set", "symbols": ["MKSI", "WDC"]}     replace the watched symbols
    {"cmd": "resync"}                               re-seed every symbol from REST now
    {"cmd": "quit"}

stdout (one JSON object per line), bars are [t, open, high, low, close, volume], t = epoch seconds:
    {"ev": "seed",   "sym", "prev_close", "reg": [open_t, close_t], "bars": [...]}   whole day, pre/post included
    {"ev": "bar",    "sym", "bar": [...]}                                            the forming minute, <= 4/s
    {"ev": "status", "state": "live" | "down" | "seeding", "msg": "..."}
    {"ev": "error",  "sym", "msg": "..."}
"""
from __future__ import annotations

import base64
import json
import struct
import sys
import threading
import time
from typing import Any

import certifi
import websocket

from sources import yahoo, yahoo_live

WS_URL = "wss://streamer.finance.yahoo.com/?version=2"
EMIT_S = 0.25
RESYNC_S = 60
PING_S = 20


def _varint(b: bytes, i: int) -> tuple[int, int]:
    n = shift = 0
    while True:
        c = b[i]
        i += 1
        n |= (c & 0x7F) << shift
        shift += 7
        if not c & 0x80:
            return n, i


def _zigzag(n: int) -> int:
    return (n >> 1) ^ -(n & 1)


def decode_tick(raw: bytes) -> dict | None:
    """Yahoo's PricingData protobuf, only the fields the bars need.

    1 id (str)  2 price (f32)  3 time (sint64 ms)  7 marketHours  9 dayVolume (sint64).
    """
    f: dict[int, Any] = {}
    i = 0
    try:
        while i < len(raw):
            tag, i = _varint(raw, i)
            field, wire = tag >> 3, tag & 7
            if wire == 0:
                v, i = _varint(raw, i)
            elif wire == 5:
                v = struct.unpack("<f", raw[i : i + 4])[0]
                i += 4
            elif wire == 1:
                v = struct.unpack("<d", raw[i : i + 8])[0]
                i += 8
            elif wire == 2:
                n, i = _varint(raw, i)
                v = raw[i : i + n]
                i += n
            else:
                return None
            if field in (1, 2, 3, 7, 9):
                f[field] = v
    except (IndexError, struct.error):
        return None
    if 1 not in f or 2 not in f or 3 not in f:
        return None
    return {
        "sym": f[1].decode(),
        "price": float(f[2]),
        "t": _zigzag(int(f[3])) / 1000.0,
        "day_vol": _zigzag(int(f[9])) if 9 in f else None,
    }


def minute_of(t: float) -> int:
    return int(t) // 60 * 60


class Feed:
    """Per-symbol 1m bars + the state to fold ticks into them."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.bars: dict[str, dict[int, list]] = {}  # sym -> minute -> [t, o, h, l, c, v]
        self.meta: dict[str, dict] = {}  # sym -> {prev_close, reg}
        self.day_vol: dict[str, int | None] = {}
        self.dirty: set[str] = set()
        self.symbols: list[str] = []
        self.ws: websocket.WebSocketApp | None = None
        self.out_lock = threading.Lock()

    # ---- output -------------------------------------------------------------
    def emit(self, obj: dict) -> None:
        with self.out_lock:
            sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")
            sys.stdout.flush()

    # ---- REST seed / resync --------------------------------------------------
    def seed(self, sym: str) -> None:
        try:
            res = yahoo_live._chart(yahoo.new_session(), sym, "1d", "1m", pre_post=True)
        except Exception as e:  # network / unknown symbol
            self.emit({"ev": "error", "sym": sym, "msg": f"seed failed: {e}"})
            return
        meta = res["meta"]
        reg = meta.get("currentTradingPeriod", {}).get("regular", {})
        now_min = minute_of(time.time())
        with self.lock:
            cur = self.bars.setdefault(sym, {})
            for b in res["bars"]:
                # Yahoo stamps the still-forming bar with the request time, not the minute start
                t = minute_of(b["t"])
                row = [t, b["open"], b["high"], b["low"], b["close"], b["volume"] or 0]
                if None in row[:5]:
                    continue
                old = cur.get(t)
                if old is not None and t >= now_min:
                    # forming minute: REST lags the socket, so keep the wider range and latest close
                    row = [t, row[1], max(row[2], old[2]), min(row[3], old[3]), old[4], max(row[5], old[5])]
                cur[t] = row
            self.meta[sym] = {
                "prev_close": meta.get("previousClose") or meta.get("chartPreviousClose"),
                "reg": [reg.get("start"), reg.get("end")],
            }
            payload = {"ev": "seed", "sym": sym, **self.meta[sym], "bars": [cur[k] for k in sorted(cur)]}
        self.emit(payload)

    # ---- websocket -----------------------------------------------------------
    def on_tick(self, tick: dict) -> None:
        sym, price, m = tick["sym"], tick["price"], minute_of(tick["t"])
        with self.lock:
            if sym not in self.symbols:
                return
            dv = tick["day_vol"]
            last = self.day_vol.get(sym)
            vol = max(dv - last, 0) if dv is not None and last is not None else 0
            if dv is not None:
                self.day_vol[sym] = dv
            cur = self.bars.setdefault(sym, {})
            bar = cur.get(m)
            if bar is None:
                cur[m] = [m, price, price, price, price, vol]
            else:
                bar[2] = max(bar[2], price)
                bar[3] = min(bar[3], price)
                bar[4] = price
                bar[5] += vol
            self.dirty.add(sym)

    def _on_message(self, _ws, msg: str) -> None:
        try:
            data = json.loads(msg)
            tick = decode_tick(base64.b64decode(data["message"]))
        except (ValueError, KeyError):
            return
        if tick:
            self.on_tick(tick)

    def _on_open(self, ws) -> None:
        with self.lock:
            syms = list(self.symbols)
        ws.send(json.dumps({"subscribe": syms}))
        self.emit({"ev": "status", "state": "live", "msg": f"streaming {len(syms)} symbols"})

    def ws_loop(self) -> None:
        backoff = 1.0
        while True:
            self.ws = websocket.WebSocketApp(
                WS_URL,
                header=["User-Agent: " + yahoo.UA, "Origin: https://finance.yahoo.com"],
                on_open=self._on_open,
                on_message=self._on_message,
            )
            started = time.time()
            self.ws.run_forever(sslopt={"ca_certs": certifi.where()}, ping_interval=PING_S, ping_timeout=10)
            self.emit({"ev": "status", "state": "down", "msg": f"socket closed, retry in {backoff:.0f}s"})
            # a connection that lived a while resets the backoff
            backoff = 1.0 if time.time() - started > 30 else min(backoff * 2, 30.0)
            time.sleep(backoff)

    # ---- commands ------------------------------------------------------------
    def set_symbols(self, symbols: list[str]) -> None:
        symbols = list(dict.fromkeys(s.upper() for s in symbols if s.strip()))
        with self.lock:
            old = self.symbols
            self.symbols = symbols
            for s in set(old) - set(symbols):
                self.bars.pop(s, None)
                self.meta.pop(s, None)
                self.day_vol.pop(s, None)
        added = [s for s in symbols if s not in old]
        removed = [s for s in old if s not in symbols]
        ws = self.ws
        if ws is not None and ws.sock and ws.sock.connected:
            try:
                if added:
                    ws.send(json.dumps({"subscribe": added}))
                if removed:
                    ws.send(json.dumps({"unsubscribe": removed}))
            except Exception:
                pass  # the reconnect loop resubscribes from self.symbols
        for s in added:
            threading.Thread(target=self.seed, args=(s,), daemon=True).start()

    def stdin_loop(self) -> None:
        for line in sys.stdin:
            try:
                cmd = json.loads(line)
            except ValueError:
                continue
            if cmd.get("cmd") == "set":
                self.set_symbols(cmd.get("symbols") or [])
            elif cmd.get("cmd") == "resync":
                with self.lock:
                    syms = list(self.symbols)
                for s in syms:
                    threading.Thread(target=self.seed, args=(s,), daemon=True).start()
            elif cmd.get("cmd") == "quit":
                break
        sys.stdout.flush()
        import os

        os._exit(0)  # stdin closed: the screen is gone

    def run(self) -> None:
        threading.Thread(target=self.stdin_loop, daemon=True).start()
        threading.Thread(target=self.ws_loop, daemon=True).start()
        last_resync = time.time()
        while True:
            time.sleep(EMIT_S)
            with self.lock:
                dirty, self.dirty = self.dirty, set()
                out = [
                    {"ev": "bar", "sym": s, "bar": self.bars[s][max(self.bars[s])]}
                    for s in dirty
                    if self.bars.get(s)
                ]
                syms = list(self.symbols)
            for o in out:
                self.emit(o)
            if time.time() - last_resync > RESYNC_S:
                last_resync = time.time()
                for s in syms:
                    threading.Thread(target=self.seed, args=(s,), daemon=True).start()


def main() -> None:
    if "--serve" not in sys.argv:
        print(__doc__)
        return
    Feed().run()


if __name__ == "__main__":
    main()
