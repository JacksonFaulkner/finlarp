"""Dossier tab: Positioning. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Short and options positioning, local data first: short interest and the FINRA short-volume ratio (readers from
derive.short), the squeeze screen row from squeeze/latest.json, and the latest E*TRADE option-chain snapshot when the
ticker has one. Short % of float is the only live call (Yahoo key statistics); it fails soft to "unavailable".
"""
from __future__ import annotations

import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

from derive.dossier import derived, src
from derive.short import _day_src, _pct, _rows, _si_src
from sources import short_interest as feed
from sources import universe

ET = ZoneInfo("America/New_York")
OPTIONS_DIR = universe.DATA_ROOT / "options" / "etrade"
SQUEEZE = universe.DATA_ROOT / "squeeze" / "latest.json"
NASDAQ = "https://www.nasdaq.com/market-activity/stocks/{}/short-interest"
SETTLEMENTS = 3  # latest plus two prior
SESSIONS = 30
ATM_MIN_DAYS = 7  # ATM IV uses the first expiry at least this far out, so 0-DTE and 1-DTE quotes do not decide it
SI_SQL = ("SELECT settlement_date, short_interest, days_to_cover, source FROM read_parquet('{p}') "
          "WHERE ticker = $t ORDER BY settlement_date DESC LIMIT $n")
SV_SQL = ("SELECT date, short_volume, total_volume FROM read_parquet('{p}') "
          "WHERE ticker = $t AND total_volume > 0 ORDER BY date DESC LIMIT $n")


def _internal(label: str) -> dict:
    """A local file with no public URL. dossier.validate() accepts it as sourced."""
    return src(label, None, internal=True)


def _safe(fn, default=None):
    """One broken local file or live call costs its block, not the tab."""
    try:
        return fn()
    except Exception:  # noqa: BLE001
        return default


def _float_short_pct(t: str) -> float | None:
    """Live: Yahoo defaultKeyStatistics.shortPercentOfFloat (a fraction, shown as %), through canslim's quoteSummary
    call. None on any failure."""
    def fetch():
        from derive.canslim import _quote_summary  # lazy: canslim is heavy and imports this package's helpers
        from sources import yahoo
        session = yahoo.new_session()
        crumb = yahoo.get_crumb(session)
        v = _quote_summary(session, crumb, t).get("defaultKeyStatistics", {}).get("shortPercentOfFloat")
        v = v.get("raw") if isinstance(v, dict) else v
        return float(v) * 100 if v is not None else None
    return _safe(fetch)


def _si_block(t: str, si: list[tuple], float_pct: float | None) -> dict:
    rows: list[dict] = []
    if si:
        d0, v0, dtc0, _ = si[-1]
        s0 = _si_src(t, d0, v0, si[-1][3])
        rows.append({"label": "short interest", "value": f"{v0:,.0f} sh · settled {d0}", "src": s0})
        if dtc0 is not None:
            rows.append({"label": "days to cover", "value": f"{dtc0:.1f}", "src": s0})
        for n, name in ((1, "prior settlement"), (2, "2 settlements ago")):
            if len(si) > n and si[-1 - n][1]:
                dp, vp, _, sp = si[-1 - n]
                ch = v0 / vp - 1
                rows.append({"label": f"change vs {name}", "value": _pct(ch), "new": abs(ch) >= 0.15,
                             "src": derived(f"short interest change vs {name}", f"{v0:,.0f} / {vp:,.0f} − 1 = {_pct(ch)}",
                                            [s0, _si_src(t, dp, vp, sp)])})
    else:
        rows.append({"label": "short interest", "value": "no settlement rows yet",
                     "src": src("Nasdaq short interest (sources/short_interest.py)", NASDAQ.format(t.lower()))})
    rows.append({"label": "short % of float", "value": "unavailable" if float_pct is None else f"{float_pct:.1f}%",
                 "src": src(f"Yahoo Finance key statistics {t} · defaultKeyStatistics.shortPercentOfFloat, "
                            f"fetched {date.today()}", f"https://finance.yahoo.com/quote/{t}/key-statistics/")})
    title = f"Short interest · settled {si[-1][0]}" if si else "Short interest"
    return {"type": "kv", "title": title, "rows": rows}


def _volume_blocks(t: str, vol: list[tuple]) -> list[dict]:
    """vol: (date, short_volume, total_volume), oldest first. Ratios are sums, not averages of daily ratios."""
    if not vol:
        return []
    rows: list[dict] = []
    ratios: dict[int, float] = {}
    srcs: dict[int, list[dict]] = {}
    for n in (5, 20):
        if len(vol) < n:
            continue
        ws = vol[-n:]
        sv, tv = sum(v[1] for v in ws), sum(v[2] for v in ws)
        ratios[n] = sv / tv
        srcs[n] = [_day_src(t, d, s, tot) for d, s, tot in ws]
        rows.append({"label": f"last {n} sessions", "value": f"{ratios[n] * 100:.0f}%",
                     "src": derived(f"short volume ratio, last {n} sessions",
                                    f"Σ short volume / Σ total volume = {sv:,.0f} / {tv:,.0f}", srcs[n])})
    if 5 in ratios and 20 in ratios:
        rows.append({"label": "5 vs 20 sessions", "value": f"{(ratios[5] - ratios[20]) * 100:+.0f} pts",
                     "src": derived("short volume ratio, last 5 vs last 20 sessions (the 20 include the 5)",
                                    f"{ratios[5] * 100:.1f}% − {ratios[20] * 100:.1f}%", srcs[20])})
    out: list[dict] = [{"type": "series", "title": f"Short-sale volume ratio, last {len(vol)} sessions",
                        "unit": "% of volume",
                        "points": [{"x": str(d), "y": round(sv / tv * 100, 1), "src": _day_src(t, d, sv, tv)}
                                   for d, sv, tv in vol]}]
    if rows:
        out.insert(0, {"type": "kv", "title": "Short-sale volume (FINRA daily, flow)", "rows": rows})
    return out


def _squeeze_block(t: str) -> dict | None:
    if not SQUEEZE.exists():
        return None
    data = json.loads(SQUEEZE.read_text())
    file_date = datetime.fromtimestamp(SQUEEZE.stat().st_mtime).date()
    px = max((r.get("px_date") or "" for r in data), default="")
    fsrc = _internal(f"squeeze/latest.json · squeeze_scan file dated {file_date}, prices through {px or 'n/a'}")
    ranked = sorted(data, key=lambda r: r.get("score") or 0, reverse=True)
    hit = next((i for i, r in enumerate(ranked) if r.get("ticker") == t), None)
    if hit is None:
        rows = [{"label": "squeeze screen",
                 "value": f"not listed among {len(ranked)} names (fails the fuel filter or hidden as a pending deal)",
                 "src": fsrc}]
    else:
        r = ranked[hit]
        rows = [
            {"label": "rank", "value": f"{hit + 1} of {len(ranked)} · score {r.get('score') or 0:.1f}",
             "src": derived("squeeze rank: position by score in squeeze/latest.json",
                            f"{t} at {hit + 1} of {len(ranked)}, sorted by score", [fsrc])},
            {"label": "status", "value": r.get("status") or "—", "src": fsrc},
            {"label": "triggers", "value": ", ".join(r.get("triggers") or []) or "none", "src": fsrc},
        ]
    return {"type": "kv", "title": f"Squeeze screen · file dated {file_date}", "rows": rows}


def _latest_chain(con, t: str) -> tuple[datetime, list[tuple]] | None:
    """The newest E*TRADE snapshot holding this ticker: (snap_ts, legs). Legs are
    (expiry, type, strike, spot, volume, open_interest, iv)."""
    if not any(OPTIONS_DIR.glob("date=*/*.parquet")):
        return None
    glob = f"{OPTIONS_DIR}/date=*/*.parquet"
    rows = con.execute(
        f"SELECT snap_ts, expiry, type, strike, spot, volume, open_interest, iv FROM read_parquet('{glob}') "
        f"WHERE ticker = ? AND snap_ts = (SELECT max(snap_ts) FROM read_parquet('{glob}') WHERE ticker = ?)",
        [t, t]).fetchall()
    return (rows[0][0], [r[1:] for r in rows]) if rows else None


def _atm_iv(legs: list[tuple], spot: float | None, snap_date: date):
    """Mean call and put IV at the strike nearest spot, in the first expiry at least ATM_MIN_DAYS out."""
    if not spot:
        return None
    expiries = sorted({lg[0] for lg in legs if lg[0]})
    if not expiries:
        return None
    exp = next((e for e in expiries if (e - snap_date).days >= ATM_MIN_DAYS), expiries[0])
    cand = [lg for lg in legs if lg[0] == exp and lg[2] is not None and lg[6] is not None]
    if not cand:
        return None
    k = min({lg[2] for lg in cand}, key=lambda s: abs(s - spot))
    ivs = {lg[1]: lg[6] for lg in cand if lg[2] == k}
    if not ivs:
        return None
    return sum(ivs.values()) / len(ivs), k, exp, (exp - snap_date).days, ivs


def _options_blocks(t: str, snap_ts: datetime, legs: list[tuple]) -> list[dict]:
    """One thin snapshot: put/call ratios (volume, open interest) and ATM IV, all expiries in the snapshot."""
    snap_et = snap_ts.astimezone(ET) if snap_ts.tzinfo else snap_ts
    snap_date = snap_et.date()
    snap = _internal(f"E*TRADE option chain snapshot {snap_et:%Y-%m-%d %H:%M} ET · {len(legs)} contracts · "
                     "sources/etrade_options.py")
    calls = [lg for lg in legs if lg[1] == "CALL"]
    puts = [lg for lg in legs if lg[1] == "PUT"]
    spot = next((lg[3] for lg in legs if lg[3]), None)
    n_exp = len({lg[0] for lg in legs})
    rows: list[dict] = [{"label": "snapshot", "value": f"{snap_date} {snap_et:%H:%M} ET · {n_exp} expiries", "src": snap}]
    if spot:
        rows.append({"label": "spot at snapshot", "value": f"{spot:,.2f}", "src": snap})
    for label, idx, nm in (("put/call ratio, volume", 4, "volume"), ("put/call ratio, open interest", 5, "open interest")):
        num = sum(lg[idx] or 0 for lg in puts)
        den = sum(lg[idx] or 0 for lg in calls)
        if den:
            rows.append({"label": label, "value": f"{num / den:.2f}",
                         "src": derived(f"{label} (all expiries in the snapshot)",
                                        f"Σ put {nm} / Σ call {nm} = {num:,.0f} / {den:,.0f}", [snap])})
        else:
            rows.append({"label": label, "value": "—", "src": snap})
    atm = _atm_iv(legs, spot, snap_date)
    if atm:
        iv, k, exp, dte, ivs = atm
        parts = " and ".join(f"{side.lower()} IV {v * 100:.1f}%" for side, v in sorted(ivs.items()))
        rows.append({"label": "ATM implied vol", "value": f"{iv * 100:.1f}%",
                     "src": derived("ATM implied vol: mean of call and put IV at the strike nearest spot",
                                    f"mean of {parts} at strike {k:g}, expiry {exp} ({dte} days out), spot {spot:,.2f}",
                                    [snap])})
    else:
        rows.append({"label": "ATM implied vol", "value": "—", "src": snap})
    return [{"type": "kv", "title": f"Options · thin: one E*TRADE snapshot, {snap_date}", "rows": rows}]


def section(t: str, con, F, prof: dict | None) -> dict | None:
    t = t.upper()
    si = _safe(lambda: _rows(feed.INTEREST, SI_SQL, {"t": t, "n": SETTLEMENTS})[::-1], [])
    vol = _safe(lambda: _rows(feed.VOLUME, SV_SQL, {"t": t, "n": SESSIONS})[::-1], [])
    sq = _safe(lambda: _squeeze_block(t))
    chain = _safe(lambda: _latest_chain(con, t))
    if not (si or vol or sq or chain):
        return None  # nothing local for this ticker: no live call either
    blocks: list[dict] = [_si_block(t, si, _float_short_pct(t))]
    blocks += _volume_blocks(t, vol)
    if sq:
        blocks.append(sq)
    if chain:
        blocks += _options_blocks(t, *chain)
    return {"id": "positioning", "title": "Positioning", "blocks": blocks}
