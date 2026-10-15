"""Short-selling blocks for the CANSLIM S (supply / demand) section: how short interest and the daily short-volume ratio
moved next to the stock's price. Context only: nothing here changes the S score.

Reads the two parquet files written by sources/short_interest.py. Every value carries a source: the Nasdaq / Yahoo page
or the FINRA daily file it came from; ratios and changes carry their formula and the sources of their inputs.
"""
from __future__ import annotations

import bisect
from datetime import date, datetime, timezone
from typing import Callable

import duckdb

from derive.dossier import derived, src
from sources import short_interest as feed

SETTLEMENTS = 24  # ~1 year of twice-monthly settlements
SESSIONS = 30
FINRA_DAY = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{:%Y%m%d}.txt"
HOW_TO_READ = (
    "Short interest is the position: shares still short as of a settlement date, public about 7 business days later, so "
    "the newest number is already ~2 weeks old. Short volume is the flow: the share of each day's volume that was a "
    "short sale, published the evening of the trade (market-maker hedging counts, so ~45-55% is normal and ~70% is heavy "
    "new shorting). A stock that has fallen a lot with short interest flat has shorts still holding; high days-to-cover "
    "means a rise would be harder to wait out. Neither is a CANSLIM score input."
)


def _rows(path, sql: str, params: dict) -> list[tuple]:
    if not path.exists():
        return []
    return duckdb.connect().execute(sql.replace("{p}", str(path)), params).fetchall()


def _si_src(symbol: str, d: date, si: float, source: str) -> dict:
    if source == "nasdaq":
        return src(f"Nasdaq short interest {symbol} · settled {d}: {si:,.0f} shares (FINRA)",
                   f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/short-interest")
    return src(f"Yahoo Finance key statistics {symbol} · short interest as of {d}: {si:,.0f} shares",
               f"https://finance.yahoo.com/quote/{symbol}/key-statistics/")


def _day_src(symbol: str, d: date, sv: float, tv: float) -> dict:
    return src(f"FINRA Reg SHO daily short sale volume {symbol} {d}: {sv:,.0f} short of {tv:,.0f} shares", FINRA_DAY.format(d))


def _pct(v: float | None, digits: int = 1) -> str:
    return "—" if v is None else f"{v * 100:+.{digits}f}%"


def _price_on(points: list[dict], keys: list[str], d: date) -> dict | None:
    """The last daily bar on or before `d`."""
    i = bisect.bisect_right(keys, d.isoformat()) - 1
    return points[i] if i >= 0 else None


def short_blocks(symbol: str, hist: list[dict], shares_out: float | None, shares_src: dict | None,
                 close_src: Callable[[str, dict], dict], si_path=None, sv_path=None) -> list[dict]:
    """Blocks for the S section, or a single note when the ticker has no short data yet."""
    si_path, sv_path = si_path or feed.INTEREST, sv_path or feed.VOLUME
    si = _rows(si_path, "SELECT settlement_date, short_interest, days_to_cover, source FROM read_parquet('{p}') "
               "WHERE ticker = $t ORDER BY settlement_date DESC LIMIT $n", {"t": symbol, "n": SETTLEMENTS})[::-1]
    vol = _rows(sv_path, "SELECT date, short_volume, total_volume FROM read_parquet('{p}') "
                "WHERE ticker = $t AND total_volume > 0 ORDER BY date DESC LIMIT $n", {"t": symbol, "n": SESSIONS})[::-1]
    if not si and not vol:
        return [{"type": "text", "title": "Short selling",
                 "text": "No short-interest or short-volume data for this ticker yet. "
                         "Run: python py/sources/short_interest.py all",
                 "src": src("sources/short_interest.py (FINRA + Nasdaq)", "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data")}]

    day_keys = [datetime.fromtimestamp(int(p["t"]), tz=timezone.utc).date().isoformat() for p in hist]
    blocks: list[dict] = []

    # ---- headline
    rows: list[dict] = []
    si_srcs = [_si_src(symbol, d, v, s) for d, v, _, s in si]
    prices = [_price_on(hist, day_keys, d) for d, *_ in si]
    price_srcs = [close_src(symbol, p) if p else None for p in prices]
    if si:
        d0, v0, dtc0, _ = si[-1]
        rows.append({"label": "short interest", "value": f"{v0:,.0f} sh · settled {d0}", "src": si_srcs[-1]})
        if shares_out and shares_src:
            rows.append({"label": "  % of shares outstanding", "value": f"{v0 / shares_out * 100:.1f}%",
                         "src": derived("short % of shares outstanding", f"{v0:,.0f} / {shares_out:,.0f} = {v0 / shares_out * 100:.1f}% "
                                        "(shares outstanding, not float: the float % is higher)", [si_srcs[-1], shares_src])})
        if dtc0 is not None:
            rows.append({"label": "  days to cover", "value": f"{dtc0:.1f}", "src": si_srcs[-1]})
        for n, name in ((1, "prior settlement"), (2, "2 settlements ago (~1 month)")):
            if len(si) > n and si[-1 - n][1]:
                ch = v0 / si[-1 - n][1] - 1
                rows.append({"label": f"  vs {name}", "value": _pct(ch), "new": abs(ch) >= 0.15,
                             "src": derived(f"short interest change vs {name}", f"{v0:,.0f} / {si[-1 - n][1]:,.0f} − 1 = {_pct(ch)}",
                                            [si_srcs[-1], si_srcs[-1 - n]])})
        if len(si) > 1 and prices[-1] and prices[-2] and price_srcs[-1] and price_srcs[-2]:
            c1, c0 = prices[-1]["close"], prices[-2]["close"]
            rows.append({"label": "  price vs prior settlement", "value": _pct(c1 / c0 - 1),
                         "src": derived("price change since the prior settlement", f"{c1:.2f} / {c0:.2f} − 1 = {_pct(c1 / c0 - 1)}",
                                        [price_srcs[-1], price_srcs[-2]])})
    if len(vol) >= 5:
        last5, prev = vol[-5:], vol[-25:-5]
        r5 = sum(v[1] for v in last5) / sum(v[2] for v in last5)
        s5 = [_day_src(symbol, d, sv, tv) for d, sv, tv in last5]
        rows.append({"label": "short volume ratio, last 5 sessions", "value": f"{r5 * 100:.0f}%",
                     "src": derived("short volume ratio over the last 5 sessions",
                                    f"Σ short volume / Σ total volume = {sum(v[1] for v in last5):,.0f} / {sum(v[2] for v in last5):,.0f}", s5)})
        if prev:
            rp = sum(v[1] for v in prev) / sum(v[2] for v in prev)
            rows.append({"label": "  vs prior sessions", "value": f"{(r5 - rp) * 100:+.0f} pts",
                         "src": derived("short volume ratio, last 5 vs the 20 before",
                                        f"{r5 * 100:.1f}% − {rp * 100:.1f}% (prior {len(prev)} sessions)",
                                        s5 + [_day_src(symbol, d, sv, tv) for d, sv, tv in prev])})
    blocks.append({"type": "kv", "title": "Short selling (context, not scored)", "rows": rows})

    # ---- short interest vs price, by settlement
    if len(si) >= 2:
        table = []
        for i, (d, v, dtc, _) in enumerate(si):
            c = prices[i]["close"] if prices[i] else None
            d_si = v / si[i - 1][1] - 1 if i and si[i - 1][1] else None
            d_px = c / prices[i - 1]["close"] - 1 if i and c and prices[i - 1] else None
            cells = [str(d), f"{v / 1e6:,.2f}M", _pct(d_si), f"{dtc:.1f}" if dtc is not None else "—",
                     f"{c:.2f}" if c else "—", _pct(d_px)]
            inputs = [si_srcs[i]] + ([price_srcs[i]] if price_srcs[i] else []) + ([si_srcs[i - 1]] if d_si is not None else [])
            table.append({"cells": cells, "src": derived(f"{symbol} settlement {d}", "ΔSI = SI / prior SI − 1; Δprice = close / prior close − 1", inputs)
                          if len(inputs) > 1 else si_srcs[i]})
        blocks.append({"type": "table", "title": f"Short interest vs price at each settlement (oldest first, last {len(si)})",
                       "cols": ["settled", "short int.", "Δ SI", "days to cover", "close", "Δ price"], "rows": table})
        blocks.append({"type": "series", "title": "Short interest by settlement", "unit": "M shares",
                       "points": [{"x": str(d), "y": v / 1e6, "src": si_srcs[i]} for i, (d, v, *_) in enumerate(si)]})
        blocks.append({"type": "series", "title": "Price at the same settlements", "unit": "$",
                       "points": [{"x": str(d), "y": prices[i]["close"] if prices[i] else None,
                                   "src": price_srcs[i] or si_srcs[i]} for i, (d, *_) in enumerate(si)]})

    # ---- daily short-volume ratio vs price
    if vol:
        dp = [_price_on(hist, day_keys, d) for d, *_ in vol]
        blocks.append({"type": "series", "title": f"Short volume ratio, last {len(vol)} sessions", "unit": "% of volume",
                       "points": [{"x": str(d), "y": sv / tv * 100, "src": _day_src(symbol, d, sv, tv)} for d, sv, tv in vol]})
        blocks.append({"type": "series", "title": "Daily close, same sessions", "unit": "$",
                       "points": [{"x": str(d), "y": p["close"] if p else None,
                                   "src": close_src(symbol, p) if p else _day_src(symbol, d, sv, tv)}
                                  for (d, sv, tv), p in zip(vol, dp)]})
    blocks.append({"type": "text", "title": "How to read this", "text": HOW_TO_READ,
                   "src": src("FINRA short interest and Reg SHO short sale volume", "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data")})
    return blocks
