"""Dossier tab: Price. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Daily closes come from the local Databento bars_1d parquet (last 2 years of
sessions). SPY is not in bars_1d, so its closes come from yahoo.cmd_history,
the cached call canslim uses. Beta is one live Yahoo summaryDetail call and is
left out if it fails. Float is not stored locally and is not shown.

Every bar-derived value cites the bar it came from (Databento label, Yahoo
history page URL for that day, the convention canslim._close_src uses).
"""
from __future__ import annotations

import glob
import math
import statistics
from datetime import datetime, timedelta, timezone

from derive.canslim import RS_DAYS, _close_src, _sma, _trend_label
from derive.dossier import _money, _pct, derived, src
from sources import universe, yahoo, yahoo_profile

BARS_GLOB = str(universe.DATA_ROOT / "market" / "databento" / "bars_1d" / "*.parquet")
SERIES_DAYS = 730
MA_DAYS = (50, 200)
WINDOWS = (("1 week", 5), ("1 month", 21), ("3 months", 63), ("6 months", 126), ("1 year", 252))
YEAR_SESSIONS = 252
VOL_SESSIONS = 30  # realized volatility window (daily log returns)
ATR_SESSIONS = 14
GAP_SESSIONS = 60
GAP_PCT = 3.0
ADV_SESSIONS = 20
AVG_SESSIONS = (20, 63)  # 20-day and ~3-month average volume


# ---- bars --------------------------------------------------------------------

def _bar(d, o, h, lo, c, v) -> dict:
    """One session. `t` is a Yahoo-style timestamp (16:00 UTC on the trade date) so the
    +/-12h day window in _day_url covers the session. `close` is the key canslim's helpers read."""
    t = int(datetime(d.year, d.month, d.day, 16, tzinfo=timezone.utc).timestamp())
    return {"d": d, "t": t, "open": o, "high": h, "low": lo, "close": c, "volume": v or 0}


def _to_bars(rows) -> list[dict]:
    """(date, open, high, low, close, volume) rows -> sorted sessions, one per date."""
    by_day = {}
    for d, o, h, lo, c, v in rows:
        if c is not None:
            by_day[d] = _bar(d, o, h, lo, c, v)
    return [by_day[d] for d in sorted(by_day)]


def _bars(con, t: str) -> list[dict]:
    if not glob.glob(BARS_GLOB):
        return []
    rows = con.execute(f"""
        SELECT (ts_event AT TIME ZONE 'UTC')::date AS d, open, high, low, close, volume
        FROM read_parquet('{BARS_GLOB}', union_by_name=true)
        WHERE symbol = ?""", [t]).fetchall()
    return _to_bars(rows)


def _day_url(t_sym: str, t: int) -> str:
    return f"https://finance.yahoo.com/quote/{t_sym}/history/?period1={t - 43200}&period2={t + 43200}"


def _bar_src(sym: str, b: dict, field: str = "close") -> dict:
    fmt = "{:,.0f}" if field == "volume" else "{:,.2f}"
    return src(f"Databento bars_1d {field} {sym} {b['d']}: {fmt.format(b[field])}", _day_url(sym, b["t"]))


def _range_src(sym: str, bars: list[dict], what: str = "closes") -> dict:
    return src(f"Databento bars_1d {what} {sym} {bars[0]['d']}..{bars[-1]['d']} ({len(bars)} sessions)",
               f"https://finance.yahoo.com/quote/{sym}/history/?period1={bars[0]['t'] - 43200}"
               f"&period2={bars[-1]['t'] + 43200}")


def _spy_by_day() -> dict:
    """SPY closes keyed by trade date. Empty if the live call fails."""
    try:
        pts = yahoo.cmd_history("SPY", "1y", "1d")["points"]
    except Exception:
        return {}
    return {datetime.fromtimestamp(p["t"], tz=timezone.utc).date(): p for p in pts}


# ---- blocks ------------------------------------------------------------------

def _series(sym: str, bars: list[dict]) -> dict:
    cut = bars[-1]["d"] - timedelta(days=SERIES_DAYS)
    return {"type": "series", "title": f"{sym} daily close, last 2 years", "unit": "USD",
            "points": [{"x": b["d"].isoformat(), "y": b["close"], "src": _bar_src(sym, b)}
                       for b in bars if b["d"] > cut]}


def _ma_table(sym: str, bars: list[dict]) -> dict | None:
    c = bars[-1]["close"]
    rows, inputs = [], {}
    for n in MA_DAYS:
        ma = _sma(bars, n)
        if ma is None:
            rows.append({"cells": [f"{n}-day MA", "—", "—"],
                         "src": derived(f"{sym} {n}-day MA: < {n} closes", "n/a", [], searched=_range_src(sym, bars))})
            continue
        win = bars[-n:]
        pct = (c - ma) / ma * 100
        inputs[n] = _range_src(sym, win)
        rows.append({"cells": [f"{n}-day MA", f"{ma:,.2f}", _pct(pct)], "src": derived(
            f"{sym} close vs {n}-day MA",
            f"sum of last {n} closes / {n} = {ma:,.2f}; ({c:,.2f} − {ma:,.2f}) / {ma:,.2f} × 100 = {pct:+.1f}%",
            [_bar_src(sym, bars[-1]), inputs[n]])})
    trend = _trend_label(c, _sma(bars, 50), _sma(bars, 200))
    if trend:
        rows.append({"cells": ["trend", trend, ""], "src": derived(
            f"{sym} trend",
            "price > MA50 > MA200 = uptrend; price < MA50 < MA200 = downtrend; else correction",
            [_bar_src(sym, bars[-1])] + [inputs[n] for n in MA_DAYS if n in inputs])})
    if not rows:
        return None
    return {"type": "table", "title": "Moving averages", "cols": ["average", "level", "close vs level"], "rows": rows}


def _range_kv(sym: str, bars: list[dict]) -> list[dict]:
    win = bars[-YEAR_SESSIONS:]
    if len(win) < YEAR_SESSIONS:
        return []
    hi = max(win, key=lambda b: b["high"])
    lo = min(win, key=lambda b: b["low"])
    c = bars[-1]["close"]
    off = (hi["high"] - c) / hi["high"] * 100
    return [
        {"label": "52-week high (intraday)", "value": f"{hi['high']:,.2f}", "src": _bar_src(sym, hi, "high")},
        {"label": "52-week low (intraday)", "value": f"{lo['low']:,.2f}", "src": _bar_src(sym, lo, "low")},
        {"label": "% off 52-week high", "value": _pct(-off), "src": derived(
            "% off 52-week high", f"({hi['high']:,.2f} − {c:,.2f}) / {hi['high']:,.2f} × 100 = {off:.1f}%",
            [_bar_src(sym, hi, "high"), _bar_src(sym, bars[-1])])},
    ]


def _returns_table(sym: str, bars: list[dict]) -> dict | None:
    last = bars[-1]
    rows = []
    for name, n in WINDOWS:
        if len(bars) <= n:
            continue
        s = bars[-(n + 1)]
        r = (last["close"] - s["close"]) / s["close"] * 100
        rows.append({"cells": [name, s["d"].isoformat(), f"{s['close']:,.2f}", _pct(r)], "src": derived(
            f"{sym} {name} return ({n} sessions)",
            f"({last['close']:,.2f} − {s['close']:,.2f}) / {s['close']:,.2f} × 100 = {r:+.1f}%",
            [_bar_src(sym, s), _bar_src(sym, last)])})
    if not rows:
        return None
    return {"type": "table", "title": "Returns", "cols": ["window", "from", "start close", "return"], "rows": rows}


def _rs_rows(sym: str, bars: list[dict]) -> list[dict]:
    """63-session return minus SPY's over the same two trade dates (canslim rs_score logic)."""
    if len(bars) <= RS_DAYS:
        return []
    spy = _spy_by_day()
    s_bar, e_bar = bars[-(RS_DAYS + 1)], bars[-1]
    s_spy, e_spy = spy.get(s_bar["d"]), spy.get(e_bar["d"])
    if not (s_spy and e_spy):
        return []
    sym_r = (e_bar["close"] - s_bar["close"]) / s_bar["close"] * 100
    spy_r = (e_spy["close"] - s_spy["close"]) / s_spy["close"] * 100
    rs = sym_r - spy_r
    s_sym = derived(f"{sym} {RS_DAYS}-session return",
                    f"({e_bar['close']:,.2f} − {s_bar['close']:,.2f}) / {s_bar['close']:,.2f} × 100 = {sym_r:+.1f}%",
                    [_bar_src(sym, s_bar), _bar_src(sym, e_bar)])
    s_spy_r = derived(f"SPY {RS_DAYS}-session return",
                      f"({e_spy['close']:,.2f} − {s_spy['close']:,.2f}) / {s_spy['close']:,.2f} × 100 = {spy_r:+.1f}%",
                      [_close_src("SPY", s_spy), _close_src("SPY", e_spy)])
    return [
        {"label": f"{sym} {RS_DAYS}-session return", "value": _pct(sym_r), "src": s_sym},
        {"label": f"SPY {RS_DAYS}-session return", "value": _pct(spy_r), "src": s_spy_r},
        {"label": f"relative strength vs SPY ({RS_DAYS} sessions)", "value": _pct(rs), "src": derived(
            f"relative strength ({sym} return − SPY return, {RS_DAYS} sessions)",
            f"{sym_r:+.1f} − {spy_r:+.1f} = {rs:+.1f}", [s_sym, s_spy_r])},
    ]


def _volume_rows(sym: str, bars: list[dict]) -> list[dict]:
    last = bars[-1]
    rows = [{"label": "last session volume (shares)", "value": f"{last['volume']:,.0f}",
             "src": _bar_src(sym, last, "volume")}]
    for n in AVG_SESSIONS:
        if len(bars) < n:
            continue
        win = bars[-n:]
        avg = sum(b["volume"] for b in win) / n
        s_avg = derived(f"{sym} average volume, {n} sessions", f"sum of {n} daily volumes / {n} = {avg:,.0f}",
                        [_range_src(sym, win, "volumes")])
        name = "20-day" if n == ADV_SESSIONS else "3-month"
        ratio = last["volume"] / avg if avg else None
        rows.append({"label": f"{name} average volume ({n} sessions)", "value": f"{avg:,.0f}", "src": s_avg})
        if ratio is not None:
            rows.append({"label": f"last session volume vs {name} average", "value": f"{ratio:.2f}x", "src": derived(
                f"volume vs {name} average", f"{last['volume']:,.0f} / {avg:,.0f} = {ratio:.2f}x",
                [_bar_src(sym, last, "volume"), s_avg])})
    win = bars[-ADV_SESSIONS:]
    if len(win) == ADV_SESSIONS:
        adv = sum(b["close"] * b["volume"] for b in win) / ADV_SESSIONS
        rows.append({"label": f"dollar volume, {ADV_SESSIONS}-day ADV", "value": _money(adv), "src": derived(
            f"dollar volume, {ADV_SESSIONS}-day ADV",
            f"mean of (close × volume) over {ADV_SESSIONS} sessions = {_money(adv)}",
            [_range_src(sym, win, "closes and volumes")])})
    return rows


def _risk_rows(sym: str, bars: list[dict]) -> list[dict]:
    rows = []
    if len(bars) >= VOL_SESSIONS + 1:
        win = bars[-(VOL_SESSIONS + 1):]
        rets = [math.log(b["close"] / a["close"]) for a, b in zip(win, win[1:])]
        sd = statistics.stdev(rets)
        rv = sd * math.sqrt(252) * 100
        rows.append({"label": f"realized volatility, {VOL_SESSIONS} sessions (annualized)", "value": f"{rv:.1f}%",
                     "src": derived(f"realized volatility, {VOL_SESSIONS} sessions",
                                    f"stdev of {VOL_SESSIONS} daily log returns = {sd:.4f}; × √252 × 100 = {rv:.1f}%",
                                    [_range_src(sym, win)])})
    if len(bars) >= ATR_SESSIONS + 1:
        win = bars[-(ATR_SESSIONS + 1):]
        trs = [max(b["high"] - b["low"], abs(b["high"] - a["close"]), abs(b["low"] - a["close"]))
               for a, b in zip(win, win[1:])]
        atr = sum(trs) / ATR_SESSIONS
        s_atr = derived(f"ATR({ATR_SESSIONS})", f"mean of true range over {ATR_SESSIONS} sessions = {atr:,.2f}",
                        [_range_src(sym, win)])
        c = bars[-1]["close"]
        rows.append({"label": f"ATR({ATR_SESSIONS})", "value": f"{atr:,.2f}", "src": s_atr})
        rows.append({"label": f"ATR({ATR_SESSIONS}) as % of close", "value": f"{atr / c * 100:.1f}%",
                     "src": derived(f"ATR({ATR_SESSIONS}) / close",
                                    f"{atr:,.2f} / {c:,.2f} × 100 = {atr / c * 100:.1f}%",
                                    [s_atr, _bar_src(sym, bars[-1])])})
    if len(bars) >= GAP_SESSIONS + 1:
        win = bars[-(GAP_SESSIONS + 1):]
        gaps = [(b["open"] / a["close"] - 1) * 100 for a, b in zip(win, win[1:])]
        up = sum(g > GAP_PCT for g in gaps)
        down = sum(g < -GAP_PCT for g in gaps)
        rows.append({"label": f"opens more than {GAP_PCT:g}% from prior close, {GAP_SESSIONS} sessions",
                     "value": f"{up + down} ({up} up, {down} down)", "src": derived(
                         f"opens more than {GAP_PCT:g}% from prior close, {GAP_SESSIONS} sessions",
                         f"count of |open / prior close − 1| > {GAP_PCT:g}% = {up + down} (up {up}, down {down})",
                         [_range_src(sym, win, "opens and closes")])})
    return rows


def _beta_row(sym: str) -> dict | None:
    try:
        res = yahoo_profile.fetch(yahoo.new_session(), sym, "summaryDetail")
    except Exception:
        return None
    beta = ((res or {}).get("summaryDetail") or {}).get("beta")
    beta = beta.get("raw") if isinstance(beta, dict) else beta
    if beta is None:
        return None
    return {"label": "beta (live, Yahoo summaryDetail)", "value": f"{beta:.2f}",
            "src": src("Yahoo Finance quote · summaryDetail.beta", f"https://finance.yahoo.com/quote/{sym}/")}


# ---- section -----------------------------------------------------------------

def _kv(rows: list[dict]) -> dict | None:
    return {"type": "kv", "rows": rows} if rows else None


def section(t: str, con, F, prof: dict | None) -> dict | None:
    sym = t.upper()
    try:
        bars = _bars(con, sym)
    except Exception:
        return None
    if not bars:
        return None
    blocks = [
        _series(sym, bars),
        _ma_table(sym, bars),
        _kv(_range_kv(sym, bars)),
        _returns_table(sym, bars),
        _kv(_rs_rows(sym, bars)),
        _kv(_volume_rows(sym, bars)),
        _kv(_risk_rows(sym, bars) + [r for r in [_beta_row(sym)] if r]),
    ]
    blocks = [b for b in blocks if b and (b.get("rows") or b.get("points"))]
    return {"id": "price", "title": "Price", "blocks": blocks} if blocks else None
