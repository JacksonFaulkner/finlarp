"""Build a CanslimScorecard for a symbol from Yahoo Finance + SEC EDGAR data.

The flat letter fields (c/a/n/s/l/i/m) are kept for existing readers. Next
to them the scorecard carries `sections`: one model-shaped Section per
letter (see tui/src/model.rs and py/derive/dossier.py), where
every displayed value has a Source:
    fetched  -> {"label", "url"}  Yahoo Finance page the field is shown on,
                                  or the SEC filing (inline-XBRL viewer)
    computed -> {"label", "formula", "inputs": [...]}  growth %, surprise,
                                  volume surge, RS, % off high, margins,
                                  moving averages, letter scores
plus `overall` {score, grade, src}. The finlarp `canslim` screen
renders only `sections`.

    python py/derive/canslim.py MRVL [--force]
    python py/derive/canslim.py --all [--force]
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone

from sources import market, universe, yahoo
from core import db
import sources.edgar as edgar
from sources import sec_http
from core.schemas.canslim import (
    AnnualEarnings,
    AnnualPeriod,
    CanslimScorecard,
    CurrentEarnings,
    EarningsQuarter,
    InstitutionalSponsorship,
    LeaderLaggard,
    MarketDirection,
    NewHighs,
    RevenueQuarter,
    SupplyDemand,
    TopHolder,
)
from derive.dossier import archive, derived, ixbrl, src

MODULES = ",".join([
    "assetProfile", "summaryDetail", "defaultKeyStatistics", "financialData",
    "earningsTrend", "earningsHistory", "recommendationTrend",
    "upgradeDowngradeHistory", "institutionOwnership", "majorHoldersBreakdown",
    "insiderTransactions", "netSharePurchaseActivity", "price", "calendarEvents",
])

IBD_URL = "https://www.investors.com/ibd-university/can-slim/"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
RS_DAYS = 63  # ~3 trading months


def _quote_summary(session, crumb, symbol):
    resp = session.get(
        f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}",
        params={"modules": MODULES, "crumb": crumb},
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()["quoteSummary"]["result"]
    if not result:
        raise RuntimeError(f"no quoteSummary result for {symbol}")
    return result[0]


def _raw(field):
    if isinstance(field, dict):
        return field.get("raw")
    return field


def _raw_pct(field):
    """Some Yahoo fields (financialData.earningsGrowth/revenueGrowth,
    earningsTrend...earningsEstimate.growth) come back as a fraction where
    `fmt` confirms `raw * 100 == fmt%` (e.g. raw=9.35, fmt="934.79%") — NOT
    a plain 0-1 ratio like returnOnEquity. Every other `_pct`-suffixed
    field in this codebase is already a real percentage, so these need the
    same *100 to match that convention (and to not silently read as ~10x
    too small everywhere they're displayed)."""
    v = _raw(field)
    return v * 100 if v is not None else None


def _pct_return(points, days):
    if len(points) < days + 1:
        return None
    start = points[-(days + 1)]["close"]
    end = points[-1]["close"]
    if not start:
        return None
    return (end - start) / start * 100


def _sma(points, window):
    if len(points) < window:
        return None
    closes = [p["close"] for p in points[-window:]]
    return sum(closes) / len(closes)


# ---- sources ----------------------------------------------------------------

def _yf(symbol: str, page: str, field: str) -> dict:
    """A Yahoo quoteSummary field, linked to the Yahoo Finance page that
    displays it (the API URL needs a session crumb, so it isn't clickable)."""
    url = f"https://finance.yahoo.com/quote/{symbol}/{page + '/' if page else ''}"
    return src(f"Yahoo Finance {page or 'quote'} · {field}", url)


def _day(t: int) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).date().isoformat()


def _close_src(symbol: str, p: dict) -> dict:
    """One daily close, linked to Yahoo's history page filtered to that day."""
    t = int(p["t"])
    return src(f"Yahoo daily close {symbol} {_day(t)}: {p['close']:.2f}",
               f"https://finance.yahoo.com/quote/{symbol}/history/?period1={t - 43200}&period2={t + 43200}")


def _range_src(symbol: str, pts: list[dict]) -> dict:
    t0, t1 = int(pts[0]["t"]), int(pts[-1]["t"])
    return src(f"Yahoo daily closes {symbol} {_day(t0)}..{_day(t1)} ({len(pts)} sessions)",
               f"https://finance.yahoo.com/quote/{symbol}/history/?period1={t0 - 43200}&period2={t1 + 43200}")


class SecFacts:
    """Filed XBRL facts from companyfacts with their filing metadata (accn,
    form, fy/fp, filed), so each value links to the exact filing. The
    primary document for the inline-XBRL viewer comes from the submissions
    API; without it the link falls back to the filing index."""

    def __init__(self, symbol: str):
        self.cik = None
        self.facts = None
        self.docs: dict[str, str] = {}
        try:
            self.cik = edgar.ticker_to_cik(symbol)
            self.facts = edgar.get_company_facts(symbol)
        except Exception:
            return
        if self.cik is None:
            return
        try:
            resp = sec_http.get(SUBMISSIONS_URL.format(cik=self.cik), timeout=15)
            if resp.status_code == 200:
                recent = resp.json().get("filings", {}).get("recent", {})
                self.docs = dict(zip(recent.get("accessionNumber", []), recent.get("primaryDocument", [])))
        except Exception:
            pass

    @property
    def facts_url(self) -> str | None:
        return edgar.FACTS_URL.format(cik=self.cik) if self.cik else None

    def quarterly(self, concepts: list[str]) -> tuple[str | None, list[dict]]:
        if not self.facts:
            return None, []
        return self._freshest((c, edgar._single_quarter_series(self.facts, [c])) for c in concepts)

    def annual(self, concepts: list[str], unit: str) -> tuple[str | None, list[dict]]:
        if not self.facts:
            return None, []
        return self._freshest((c, edgar._annual_series(self.facts, [c], unit)) for c in concepts)

    @staticmethod
    def _freshest(candidates) -> tuple[str | None, list[dict]]:
        # Filers switch revenue tags over time (NVDA: ...ExcludingAssessedTax
        # until FY22, then Revenues), so the first tag with any data can be
        # years stale; take the one with the latest period end instead.
        best = (None, [])
        for c, rows in candidates:
            if rows and (not best[1] or rows[-1]["end"] > best[1][-1]["end"]):
                best = (c, rows)
        return best

    def url(self, accn: str | None) -> str | None:
        if not (self.cik and accn):
            return self.facts_url
        doc = self.docs.get(accn)
        return ixbrl(self.cik, accn, doc) if doc else archive(self.cik, accn)

    def src(self, e: dict, concept: str) -> dict:
        period = f"{e.get('start')}..{e['end']}" if e.get("start") else e["end"]
        fp = e.get("fp") or ""
        report = f"FY{e.get('fy', '?')}" if fp in ("", "FY") else f"{fp} FY{e.get('fy', '?')}"
        return src(f"{e.get('form', 'filing')} {report} filed {e.get('filed', '?')}"
                   f" · {concept} · {period}", self.url(e.get("accn")))


# ---- formatting ---------------------------------------------------------------

def _f(v, fmt: str = "{:.2f}", none: str = "—") -> str:
    return none if v is None else fmt.format(v)


def _big(v) -> str:
    if v is None:
        return "—"
    a = abs(v)
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            return f"{v / div:,.2f}{suf}"
    return f"{v:,.0f}"


def _sp(v) -> str:
    return _f(v, "{:+.1f}%")


def _kv(label: str, value: str, source: dict | None) -> dict:
    return {"label": label, "value": value, "src": source}


def _clamp(v, lo, hi) -> int:
    return round(max(0.0, min(1.0, (v - lo) / (hi - lo))) * 100)


def _grade(score: int | None) -> str:
    if score is None:
        return "—"
    for cut, g in ((80, "A"), (60, "B"), (40, "C"), (20, "D")):
        if score >= cut:
            return g
    return "F"


def _score(letter: str, parts: list[tuple[float | None, float, float, dict | None]]) -> tuple[int | None, dict]:
    """Rough 0-100 "how good does this look" per letter (the gauge, not a
    stored rating): mean of clamp((v - lo) / (hi - lo)) over available inputs.
    Bounds were calibrated against MU, NVDA, GOOGL, WEN, GME filed/estimate data."""
    have = [(v, lo, hi, s) for v, lo, hi, s in parts if v is not None]
    if not have:
        return None, derived(f"{letter} score: no inputs available", "n/a", [])
    vals = [_clamp(v, lo, hi) for v, lo, hi, _ in have]
    score = sum(vals) // len(vals)
    terms = " + ".join(f"clamp(({v:.2f} − {lo:g}) / ({hi:g} − {lo:g}))" for v, lo, hi, _ in have)
    formula = f"({terms}) / {len(have)} × 100 = {score}" if len(have) > 1 else f"{terms} × 100 = {score}"
    return score, derived(f"{letter} score (gauge; A≥80 B≥60 C≥40 D≥20)", formula, [s for *_, s in have if s])


def _trend_label(price, ma50, ma200) -> str | None:
    if not (price and ma50 and ma200):
        return None
    if price > ma50 > ma200:
        return "uptrend"
    if price < ma50 < ma200:
        return "downtrend"
    return "correction"


def _stock_ma_rows(sym: str, pts: list[dict]):
    """N-section moving-average rows for the stock: close, MA50/MA200 with % distance, trend label."""
    if not pts:
        s_empty = src(f"Yahoo {sym} history: empty", f"https://finance.yahoo.com/quote/{sym}/history/")
        return [], None, s_empty, None, s_empty
    price = pts[-1]["close"]
    s_close = _close_src(sym, pts[-1])
    ma50, ma200 = _sma(pts, 50), _sma(pts, 200)
    rows, pct200, s_pct200 = [_kv(f"{sym} close", _f(price), s_close)], None, derived(f"{sym} vs MA200: < 200 closes", "n/a", [s_close])
    for n, ma in ((50, ma50), (200, ma200)):
        if ma is None:
            s_ma = derived(f"{sym} {n}-day MA: < {n} closes", "n/a", [s_close])
            rows += [_kv(f"{n}-day MA", "—", s_ma)]
            continue
        s_ma = derived(f"{sym} {n}-day simple moving average", f"sum of last {n} closes / {n} = {ma:.2f}", [_range_src(sym, pts[-n:])])
        pct = (price - ma) / ma * 100
        s_pct = derived(f"{sym} vs MA{n}", f"({price:.2f} − {ma:.2f}) / {ma:.2f} × 100 = {pct:+.1f}%", [s_close, s_ma])
        rows += [_kv(f"{n}-day MA", _f(ma), s_ma), _kv(f"vs {n}-day", _f(pct, "{:+.1f}%"), s_pct)]
        if n == 200:
            pct200, s_pct200 = pct, s_pct
    trend = _trend_label(price, ma50, ma200)
    s_trend = derived(f"{sym} trend", f"price {_f(price)} vs MA50 {_f(ma50)} vs MA200 {_f(ma200)}: "
                      "price > MA50 > MA200 = uptrend; price < MA50 < MA200 = downtrend; else correction", [s_close])
    return rows, pct200, s_pct200, trend, s_trend


def _index_row(sym: str, pts: list[dict]) -> tuple[dict, str | None]:
    """One index-table row: close, 50/200-day MA, trend; each cell's source is
    the same derived trend (price vs both MAs), citing the closes behind it."""
    if not pts:
        return {"cells": [sym, "—", "—", "—", "—"],
                "src": src(f"Yahoo {sym} history: empty", f"https://finance.yahoo.com/quote/{sym}/history/")}, None
    price, ma50, ma200 = pts[-1]["close"], _sma(pts, 50), _sma(pts, 200)
    trend = _trend_label(price, ma50, ma200)
    inputs = [_close_src(sym, pts[-1])]
    for n in (50, 200):
        if len(pts) >= n:
            inputs.append(_range_src(sym, pts[-n:]))
    s_row = derived(f"{sym} trend", f"price {_f(price)} vs MA50 {_f(ma50)} vs MA200 {_f(ma200)}: "
                    "price > MA50 > MA200 = uptrend; price < MA50 < MA200 = downtrend; else correction", inputs)
    return {"cells": [sym, _f(price), _f(ma50), _f(ma200), trend or "—"], "src": s_row}, trend


def _market_internals(session, spy_hist: list[dict]) -> dict:
    """Everything M adds beyond SPY's trend: the other indices, distribution
    days on SPY and QQQ, and breadth across the finlarp universe. Any piece
    that fails to fetch comes back empty rather than sinking the scorecard."""
    from concurrent.futures import ThreadPoolExecutor

    def _hist(sym):
        try:
            return market.history(sym)  # own session: requests sessions aren't thread-safe
        except Exception:
            return []

    def _breadth():
        try:
            return market.breadth([x["ticker"] for x in universe.rows()])
        except Exception:
            return None

    # Independent network pulls run side by side instead of one after another.
    with ThreadPoolExecutor(max_workers=4) as pool:
        f_hists = {sym: pool.submit(_hist, sym) for sym in ("QQQ", "IWM", "RSP")}
        f_breadth = pool.submit(_breadth)
        hists = {"SPY": spy_hist} | {sym: f.result() for sym, f in f_hists.items()}
        breadth_data = f_breadth.result()
    index_rows, trends = [], {}
    for sym, pts in hists.items():
        row, trends[sym] = _index_row(sym, pts)
        index_rows.append(row)

    dist = {}
    for sym in ("SPY", "QQQ"):
        pts = hists[sym]
        dist[sym] = (pts, market.distribution_days(pts) if pts and pts[-1].get("volume") else None)

    return {"index_rows": index_rows, "trends": trends, "dist": dist, "breadth": breadth_data}


def _dist_blocks(internals: dict) -> tuple[list[dict], int | None, dict]:
    """(table rows, SPY count or None, SPY count's source)."""
    rows, counts, s_spy_dist = [], {}, derived("SPY distribution days: no volume data", "n/a", [])
    for sym, (pts, days) in internals["dist"].items():
        if days is None:
            continue
        counts[sym] = len(days)
        window = pts[-(market.DIST_WINDOW + 1):]
        s_count = derived(
            f"{sym} distribution days, last {market.DIST_WINDOW} sessions",
            f"count of sessions down ≥{abs(market.DIST_DROP_PCT)}% on volume above the prior session = {len(days)}",
            [_range_src(sym, window)])
        if sym == "SPY":
            s_spy_dist = s_count
        rows.append({"cells": [sym, "count", str(len(days)), "", ""], "src": s_count})
        for d in days:
            a = {"t": d["prev_t"], "close": d["prev_close"]}
            b = {"t": d["t"], "close": d["close"]}
            rows.append({"cells": [sym, _day(d["t"]), f"{d['pct']:+.2f}%", f"{d['volume']:,.0f}", f"{d['prev_volume']:,.0f}"],
                         "src": derived(f"{sym} {_day(d['t'])} distribution day",
                                        f"({d['close']:.2f} − {d['prev_close']:.2f}) / {d['prev_close']:.2f} × 100 = {d['pct']:+.2f}%; "
                                        f"volume {d['volume']:,.0f} > prior {d['prev_volume']:,.0f}",
                                        [_close_src(sym, a), _close_src(sym, b)])})
    return rows, counts.get("SPY"), s_spy_dist


def _breadth_rows(b: dict | None) -> tuple[list[dict], float | None, dict | None]:
    """(kv rows, % above 50-day MA, that percentage's source)."""
    if not b or not b["rows"]:
        return [], None, None
    kv, pct50, s50 = [], None, None
    for field, n in (("ma50", 50), ("ma200", 200)):
        up, have = market.pct_above(b["rows"], field)
        if not have:
            continue
        pct = up / have * 100
        inputs = [src(f"{r['ticker']} close {r['close']:.2f} vs {n}-day MA {r[field]:.2f}",
                      f"https://finance.yahoo.com/quote/{r['ticker']}/history/") for r in b["rows"] if r.get(field)]
        s = derived(f"universe breadth: above {n}-day MA",
                    f"{up} of {have} universe tickers close above their {n}-day average = {pct:.0f}%", inputs)
        kv.append(_kv(f"universe above {n}-day MA", f"{pct:.0f}%  ({up}/{have})", s))
        if n == 50:
            pct50, s50 = pct, s
    if b["failed"]:
        kv.append(_kv("tickers without data", str(b["failed"]), src(
            "market.breadth: chart request failed or too few closes", "https://finance.yahoo.com/")))
    return kv, pct50, s50


# Tab labels for narrow screens (the Rust tab strip falls back to these).
SHORT = {"C": "Earnings", "A": "Annual", "N": "New high", "S": "Supply", "L": "Leader", "I": "Institutions", "M": "Market"}


def _section(key: str, title: str, score: int | None, score_src: dict, blocks: list[dict], rule: str) -> dict:
    blocks = [b for b in blocks if b.get("rows") or b.get("points") or b.get("items") or b.get("text")]
    blocks.append({"type": "text", "title": "Rule", "text": rule,
                   "src": src("IBD University · CAN SLIM (William O'Neil)", IBD_URL)})
    return {"id": key.lower(), "title": f"{key} {title}", "short": f"{key} {SHORT.get(key, title)}", "new": False,
            "badge": f"{_grade(score)} {score}" if score is not None else "—", "blocks": blocks, "score": score, "score_src": score_src}


# ---- build --------------------------------------------------------------------

def build_scorecard(symbol: str, use_cache: bool = True) -> CanslimScorecard:
    if use_cache:
        cached = db.get_cached_canslim(symbol)
        # Entries written before sections existed are refetched.
        if cached is not None and cached.get("sections"):
            return CanslimScorecard.model_validate(cached)

    card = _fetch_scorecard(symbol)
    db.put_cached_canslim(symbol, card.model_dump(mode="json"))
    return card


def _nearest_prior(quarters, idx, target_days, tolerance_days):
    """Find the filed quarter closest to `target_days` before
    quarters[idx], within tolerance. Small/irregular filers (odd fiscal
    year-ends, a skipped 10-Q) don't file exactly every 90 days — AEHR's
    filed quarters have real multi-month gaps — so a fixed "4 quarters
    back = idx-4" offset silently compares against the wrong quarter
    once there's a gap. Matching by actual elapsed days is correct
    regardless of gaps; it just returns None if nothing's close enough."""
    target_end = date.fromisoformat(quarters[idx]["end"])
    best = None
    best_diff = None
    for j in range(idx):
        days = (target_end - date.fromisoformat(quarters[j]["end"])).days
        diff = abs(days - target_days)
        if diff <= tolerance_days and (best_diff is None or diff < best_diff):
            best, best_diff = quarters[j], diff
    return best


def _growth(cur: float, prior: float, label: str, s_cur: dict, s_prior: dict) -> tuple[float, dict]:
    g = (cur - prior) / prior * 100
    return g, derived(label, f"({cur / 1e6:,.1f} − {prior / 1e6:,.1f}) / {prior / 1e6:,.1f} × 100 = {g:+.1f}%",
                      [s_cur, s_prior])


def _fetch_scorecard(symbol: str) -> CanslimScorecard:
    S = symbol
    session = yahoo.new_session()
    crumb = yahoo.get_crumb(session)
    qs = _quote_summary(session, crumb, symbol)
    hist = yahoo.cmd_history(symbol, "1y", "1d")["points"]
    spy_hist = yahoo.cmd_history("SPY", "1y", "1d")["points"]

    et = qs.get("earningsTrend", {}).get("trend", [])
    current_trend = et[0] if et else {}
    eps_trend = current_trend.get("epsTrend", {})
    eps_estimate = current_trend.get("earningsEstimate", {})
    trend_period = f"{current_trend.get('period', '0q')} ending {current_trend.get('endDate', '?')}"

    fd = qs.get("financialData", {})
    dks = qs.get("defaultKeyStatistics", {})
    sd = qs.get("summaryDetail", {})
    price_mod = qs.get("price", {})
    io = qs.get("institutionOwnership", {}).get("ownershipList", [])
    nspa = qs.get("netSharePurchaseActivity", {})
    eh = qs.get("earningsHistory", {}).get("history", [])

    # SEC EDGAR failures (rate limit, unmapped ticker, no filings yet for a
    # recent IPO, 20-F filers with no 10-Q facts) shouldn't break the whole
    # scorecard — Yahoo-only fields still work fine without them.
    sec = SecFacts(symbol)
    try:
        rev_concept, rev_rows = sec.quarterly(edgar.REVENUE_CONCEPTS)
        ni_concept, ni_rows = sec.quarterly(edgar.NET_INCOME_CONCEPTS)
        eps_a_concept, eps_a_rows = sec.annual(edgar.EPS_CONCEPTS, "USD/shares")
        rev_a_concept, rev_a_rows = sec.annual(edgar.REVENUE_CONCEPTS, "USD")
    except Exception:
        rev_concept, rev_rows, ni_concept, ni_rows = None, [], None, []
        eps_a_concept, eps_a_rows, rev_a_concept, rev_a_rows = None, [], None, []

    # ---- N: price vs 52-week range
    current_price = _raw(price_mod.get("regularMarketPrice"))
    fifty_high = _raw(sd.get("fiftyTwoWeekHigh"))
    fifty_low = _raw(sd.get("fiftyTwoWeekLow"))
    s_price = _yf(S, "", "price.regularMarketPrice")
    s_high = _yf(S, "", "summaryDetail.fiftyTwoWeekHigh")
    s_low = _yf(S, "", "summaryDetail.fiftyTwoWeekLow")
    pct_off_high = None
    s_off_high = derived("% off 52-week high: inputs missing", "n/a", [s_price, s_high])
    if current_price and fifty_high:
        pct_off_high = (fifty_high - current_price) / fifty_high * 100
        s_off_high = derived("% off 52-week high",
                             f"({fifty_high:.2f} − {current_price:.2f}) / {fifty_high:.2f} × 100 = {pct_off_high:.1f}%",
                             [s_high, s_price])

    # ---- S: volume
    vol_10d_f = "summaryDetail.averageVolume10days" if _raw(sd.get("averageVolume10days")) else "defaultKeyStatistics.averageDailyVolume10Day"
    vol_3mo_f = "summaryDetail.averageVolume" if _raw(sd.get("averageVolume")) else "defaultKeyStatistics.averageDailyVolume3Month"
    vol_10d = _raw(sd.get("averageVolume10days") or dks.get("averageDailyVolume10Day"))
    vol_3mo = _raw(sd.get("averageVolume") or dks.get("averageDailyVolume3Month"))
    s_v10 = _yf(S, "key-statistics", vol_10d_f)
    s_v3 = _yf(S, "key-statistics", vol_3mo_f)
    vol_surge = None
    s_surge = derived("volume surge: inputs missing", "n/a", [s_v10, s_v3])
    if vol_10d and vol_3mo:
        vol_surge = vol_10d / vol_3mo
        s_surge = derived("volume surge (10-day avg / 3-month avg)",
                          f"{vol_10d:,.0f} / {vol_3mo:,.0f} = {vol_surge:.2f}x", [s_v10, s_v3])

    # ---- L: 3-month return vs SPY
    def ret_src(sym, pts, ret):
        if ret is None:
            return derived(f"{sym} {RS_DAYS}-session return: < {RS_DAYS + 1} closes", "n/a",
                           [_range_src(sym, pts)] if pts else [])
        a, b = pts[-(RS_DAYS + 1)], pts[-1]
        return derived(f"{sym} {RS_DAYS}-session return",
                       f"({b['close']:.2f} − {a['close']:.2f}) / {a['close']:.2f} × 100 = {ret:+.1f}%",
                       [_close_src(sym, a), _close_src(sym, b)])

    sym_ret = _pct_return(hist, RS_DAYS)
    spy_ret = _pct_return(spy_hist, RS_DAYS)
    s_sym_ret = ret_src(S, hist, sym_ret)
    s_spy_ret = ret_src("SPY", spy_hist, spy_ret)
    rs_score = None
    s_rs = derived("relative strength: inputs missing", "n/a", [s_sym_ret, s_spy_ret])
    if sym_ret is not None and spy_ret is not None:
        rs_score = sym_ret - spy_ret
        s_rs = derived(f"relative strength ({S} return − SPY return, {RS_DAYS} sessions)",
                       f"{sym_ret:+.1f} − {spy_ret:+.1f} = {rs_score:+.1f}", [s_sym_ret, s_spy_ret])

    # ---- M: SPY trend
    ma50 = _sma(spy_hist, 50)
    ma200 = _sma(spy_hist, 200)
    spy_price = spy_hist[-1]["close"] if spy_hist else None
    s_spy = _close_src("SPY", spy_hist[-1]) if spy_hist else src("Yahoo SPY history: empty", "https://finance.yahoo.com/quote/SPY/history/")

    def ma_src(n, ma):
        if ma is None:
            return derived(f"SPY {n}-day MA: < {n} closes", "n/a", [s_spy])
        return derived(f"SPY {n}-day simple moving average", f"sum of last {n} closes / {n} = {ma:.2f}",
                       [_range_src("SPY", spy_hist[-n:])])

    s_ma50, s_ma200 = ma_src(50, ma50), ma_src(200, ma200)
    trend = None
    if spy_price and ma50 and ma200:
        if spy_price > ma50 > ma200:
            trend = "uptrend"
        elif spy_price < ma50 < ma200:
            trend = "downtrend"
        else:
            trend = "correction"
    vs50 = (spy_price - ma50) if (spy_price and ma50) else None
    vs200 = (spy_price - ma200) if (spy_price and ma200) else None
    s_vs50 = derived("SPY − MA50", f"{spy_price:.2f} − {ma50:.2f} = {vs50:+.2f}" if vs50 is not None else "n/a", [s_spy, s_ma50])
    s_vs200 = derived("SPY − MA200", f"{spy_price:.2f} − {ma200:.2f} = {vs200:+.2f}" if vs200 is not None else "n/a", [s_spy, s_ma200])
    s_trend = derived("market trend",
                      f"price {_f(spy_price)} vs MA50 {_f(ma50)} vs MA200 {_f(ma200)}: "
                      "price > MA50 > MA200 = uptrend; price < MA50 < MA200 = downtrend; else correction",
                      [s_spy, s_ma50, s_ma200])

    # ---- I
    top_holders = [
        TopHolder(organization=h.get("organization"), pct_held=_raw(h.get("pctHeld")), value=_raw(h.get("value")))
        for h in io[:5]
    ]
    holder_dates = [(h.get("reportDate") or {}).get("fmt") for h in io[:5]]

    # ---- C: EPS history (Yahoo) + filed revenue (SEC)
    earnings_history = [
        EarningsQuarter(
            quarter_end=(q.get("quarter") or {}).get("fmt"),
            eps_actual=_raw(q.get("epsActual")),
            eps_estimate=_raw(q.get("epsEstimate")),
            surprise_pct=_raw(q.get("surprisePercent")),
        )
        for q in eh
    ]

    rev_src = {r["end"]: sec.src(r, rev_concept) for r in rev_rows}
    ni_by_end = {r["end"]: r for r in ni_rows}
    revenue_history, rev_meta = [], []
    for idx, q in enumerate(rev_rows):
        s_rev = rev_src[q["end"]]
        qoq = yoy = None
        s_qoq = s_yoy = None
        prior_q = _nearest_prior(rev_rows, idx, target_days=90, tolerance_days=20)
        if prior_q and prior_q["val"]:
            qoq, s_qoq = _growth(q["val"], prior_q["val"], f"QoQ revenue growth, quarter ending {q['end']}",
                                 s_rev, rev_src[prior_q["end"]])
        prior_y = _nearest_prior(rev_rows, idx, target_days=365, tolerance_days=30)
        if prior_y and prior_y["val"]:
            yoy, s_yoy = _growth(q["val"], prior_y["val"], f"YoY revenue growth, quarter ending {q['end']}",
                                 s_rev, rev_src[prior_y["end"]])
        ni = ni_by_end.get(q["end"])
        net_income = ni["val"] if ni else None
        margin, s_margin = None, None
        if net_income is not None and q["val"]:
            margin = net_income / q["val"] * 100
            s_margin = derived(f"net margin, quarter ending {q['end']}",
                               f"{net_income / 1e6:,.1f} / {q['val'] / 1e6:,.1f} × 100 = {margin:.1f}%",
                               [sec.src(ni, ni_concept), s_rev])
        revenue_history.append(RevenueQuarter(quarter_end=q["end"], revenue=q["val"], qoq_growth_pct=qoq,
                                              yoy_growth_pct=yoy, net_income=net_income, net_margin_pct=margin))
        rev_meta.append((s_rev, s_qoq, s_yoy, s_margin))

    eps_a = {r["end"]: r for r in eps_a_rows}
    rev_a = {r["end"]: r for r in rev_a_rows}
    annual_ends = sorted(set(eps_a) | set(rev_a))
    annual_history = [
        AnnualPeriod(fiscal_year_end=e, eps=(eps_a.get(e) or {}).get("val"), revenue=(rev_a.get(e) or {}).get("val"))
        for e in annual_ends
    ]

    c = CurrentEarnings(
        eps_estimate_current=_raw(eps_estimate.get("avg")),
        eps_estimate_7d_ago=_raw(eps_trend.get("7daysAgo")),
        eps_estimate_30d_ago=_raw(eps_trend.get("30daysAgo")),
        eps_estimate_90d_ago=_raw(eps_trend.get("90daysAgo")),
        forward_qtr_eps_growth_pct=_raw_pct(eps_estimate.get("growth")),
        num_analysts=_raw(eps_estimate.get("numberOfAnalysts")),
        history=earnings_history,
        revenue_history=revenue_history,
    )
    a = AnnualEarnings(
        trailing_yoy_earnings_growth_pct=_raw_pct(fd.get("earningsGrowth")),
        trailing_yoy_revenue_growth_pct=_raw_pct(fd.get("revenueGrowth")),
        return_on_equity_pct=_raw(fd.get("returnOnEquity")),
        history=annual_history,
    )
    n = NewHighs(price_current=current_price, fifty_two_week_high=fifty_high, fifty_two_week_low=fifty_low,
                 pct_off_high=pct_off_high)
    s = SupplyDemand(
        shares_outstanding=_raw(dks.get("sharesOutstanding")),
        short_pct_of_float=_raw(dks.get("shortPercentOfFloat")),
        avg_volume_10d=vol_10d, avg_volume_3mo=vol_3mo, volume_surge_ratio=vol_surge,
    )
    lead = LeaderLaggard(symbol_return_pct=sym_ret, benchmark_return_pct=spy_ret, relative_strength_score=rs_score)
    i = InstitutionalSponsorship(
        held_pct_institutions=_raw(dks.get("heldPercentInstitutions")),
        top_holders=top_holders,
        net_insider_shares_purchased=_raw(nspa.get("netShares") or nspa.get("netInfoShares")),
        recommendation_key=fd.get("recommendationKey"),
        target_mean_price=_raw(fd.get("targetMeanPrice")),
    )
    m = MarketDirection(index_symbol="SPY", price_vs_ma50=vs50, price_vs_ma200=vs200, trend=trend)

    # ================= sections (what the screen renders) =================
    AN = "analysis"
    s_eps_now = _yf(S, AN, f"earningsTrend[{trend_period}].earningsEstimate.avg")
    s_eps_7 = _yf(S, AN, f"earningsTrend[{trend_period}].epsTrend.7daysAgo")
    s_eps_30 = _yf(S, AN, f"earningsTrend[{trend_period}].epsTrend.30daysAgo")
    s_eps_90 = _yf(S, AN, f"earningsTrend[{trend_period}].epsTrend.90daysAgo")
    s_growth = _yf(S, AN, f"earningsTrend[{trend_period}].earningsEstimate.growth (fraction × 100)")
    s_analysts = _yf(S, AN, f"earningsTrend[{trend_period}].earningsEstimate.numberOfAnalysts")

    # Growth off a negative or zero base is not meaningful (-650% "growth"
    # for a name going from -0.01 to -0.06): drop it from line and score.
    negative_base = c.eps_estimate_current is not None and c.eps_estimate_current <= 0
    fwd_growth = None if negative_base else c.forward_qtr_eps_growth_pct
    na = c.num_analysts
    # Thin coverage: a dramatic % from 1-3 analysts is one guess, not a consensus.
    cov = "" if na is None else (f"  ({na} analysts — thin coverage)" if na <= 3 else f"  ({na} analysts)")
    latest_rev_yoy = revenue_history[-1].yoy_growth_pct if revenue_history else None
    s_latest_yoy = (rev_meta[-1][2] if rev_meta and rev_meta[-1][2]
                    else derived("filed revenue YoY: no filed 10-Q quarter with a year-ago comparison", "n/a", [], {"label": "SEC companyfacts", "url": sec.facts_url}))

    c_score, c_ssrc = _score("C", [(fwd_growth, 0, 100, s_growth), (latest_rev_yoy, 0, 50, s_latest_yoy)])

    rev_trend = [("90d ago", c.eps_estimate_90d_ago, s_eps_90), ("30d ago", c.eps_estimate_30d_ago, s_eps_30),
                 ("7d ago", c.eps_estimate_7d_ago, s_eps_7), ("now", c.eps_estimate_current, s_eps_now)]
    rev_rows, prev = [], None
    for label, v, sv in rev_trend:
        delta, sd_ = "", sv
        if prev is not None and prev[0] is not None and v is not None:
            d = v - prev[0]
            arrow = "▲" if d > 1e-9 else "▼" if d < -1e-9 else " "
            delta = f"{d:+.2f} {arrow}"
            sd_ = src(sv["label"], sv["url"], formula=f"{v:.2f} − {prev[0]:.2f} = {d:+.2f} vs {prev[1]}",
                      inputs=[sv, prev[2]])
        rev_rows.append({"cells": [label, _f(v), delta], "bar": v, "src": sd_})
        prev = (v, label, sv)

    eh_src = lambda q: _yf(S, AN, f"earningsHistory {q.quarter_end}: actual {_f(q.eps_actual)}, "
                                  f"estimate {_f(q.eps_estimate)}, surprisePercent {_f(q.surprise_pct, '{:+.1%}')}")
    latest_q = earnings_history[-1].quarter_end if earnings_history else "—"
    latest_rev_q = revenue_history[-1].quarter_end if revenue_history else "—"

    c_blocks = [
        {"type": "kv", "title": "Headline", "rows": [
            _kv("fwd qtr EPS growth", ("n/m (negative EPS)" if negative_base else _sp(fwd_growth)) + cov,
                derived("n/m: growth off a ≤0 EPS base is not meaningful", f"eps estimate {_f(c.eps_estimate_current)} ≤ 0",
                        [s_eps_now, s_growth]) if negative_base else s_growth),
            _kv("analysts", _f(na, "{}"), s_analysts),
            _kv("filed revenue YoY (SEC)", _sp(latest_rev_yoy), s_latest_yoy),
        ]},
        {"type": "table", "title": "EPS estimate revision (▲ raised / ▼ cut vs prior)",
         "cols": ["next-qtr est", "EPS", "Δ"], "rows": rev_rows},
        {"type": "bars", "title": f"EPS actual vs estimate by quarter (compare = estimate) · latest {latest_q}",
         "unit": "$/sh", "items": [
             {"label": q.quarter_end or "?", "value": q.eps_actual, "compare": q.eps_estimate,
              "note": " ".join(x for x in (
                  _f(q.surprise_pct, "{:+.1%}") if q.surprise_pct is not None else "",
                  "" if q.eps_estimate is None else ("beat" if q.eps_actual >= q.eps_estimate else "missed")) if x),
              "src": eh_src(q)}
             for q in earnings_history if q.eps_actual is not None]},
        {"type": "table", "title": f"Revenue by quarter (SEC filed) · latest {latest_rev_q}",
         "cols": ["quarter", "revenue", "QoQ", "YoY", "net margin"],
         "rows": [{"cells": [r.quarter_end, _big(r.revenue), _sp(r.qoq_growth_pct), _sp(r.yoy_growth_pct), _f(r.net_margin_pct, "{:.1f}%")],
                   "bar": r.revenue,
                   # Row links to the revenue filing; formula/inputs cover the computed cells.
                   "src": src(meta[0]["label"], meta[0]["url"],
                              formula="QoQ = rev / prior qtr − 1; YoY = rev / year-ago qtr − 1; margin = net income / rev",
                              inputs=[x for x in meta[1:] if x] or [meta[0]])}
                  for r, meta in zip(revenue_history, rev_meta)]},
    ]
    if not rev_rows:
        c_blocks.append({"type": "text", "title": "SEC filed revenue", "text":
                         "No single-quarter 10-Q revenue facts in SEC companyfacts (20-F/40-F filer, unmapped ticker, or no filings yet).",
                         "src": src("SEC companyfacts (searched)", sec.facts_url or "https://www.sec.gov/edgar/search/")})
    sections = [_section("C", "Current earnings", c_score, c_ssrc, c_blocks,
                         "Current quarterly EPS up ≥25% YoY, ideally accelerating, with sales confirming (≥25% or accelerating). "
                         "Gauge: next-quarter consensus EPS growth over 0..100% and latest filed revenue YoY over 0..50%, averaged. "
                         "Growth off a ≤0 EPS base is excluded. Thin analyst coverage (≤3) is flagged.")]

    # ---- A
    s_eg = _yf(S, "key-statistics", "financialData.earningsGrowth (fraction × 100)")
    s_rg = _yf(S, "key-statistics", "financialData.revenueGrowth (fraction × 100)")
    s_roe = _yf(S, "key-statistics", "financialData.returnOnEquity (fraction × 100)")
    a_score, a_ssrc = _score("A", [(a.trailing_yoy_earnings_growth_pct, 0, 50, s_eg)])
    ann_rows, prev_eps = [], None
    for e in annual_ends:
        er, rr = eps_a.get(e), rev_a.get(e)
        s_e = sec.src(er, eps_a_concept) if er else None
        s_r = sec.src(rr, rev_a_concept) if rr else None
        inputs = [x for x in (s_e, s_r) if x]
        g_txt = "—"
        if er and prev_eps and prev_eps[0]["val"] and prev_eps[0]["val"] > 0:
            g = (er["val"] - prev_eps[0]["val"]) / abs(prev_eps[0]["val"]) * 100
            g_txt = f"{g:+.1f}%"
            inputs.append(derived("EPS YoY", f"({er['val']:.2f} − {prev_eps[0]['val']:.2f}) / {prev_eps[0]['val']:.2f} × 100 = {g_txt}",
                                  [s_e, prev_eps[1]]))
        main = s_e or s_r
        ann_rows.append({"cells": [f"FY{e[2:4]} ({e})", _f(er and er["val"], "${:.2f}"), _big(rr and rr["val"]), g_txt],
                         "src": src(main["label"], main["url"], formula="EPS YoY = EPS / prior-year EPS − 1 (n/m off ≤0 base)",
                                    inputs=inputs) if len(inputs) > 1 else main})
        if er:
            prev_eps = (er, s_e)
    a_blocks = [
        {"type": "kv", "title": "Headline", "rows": [
            _kv("earnings growth YoY (Yahoo, latest qtr)", _sp(a.trailing_yoy_earnings_growth_pct), s_eg),
            _kv("revenue growth YoY (Yahoo, latest qtr)", _sp(a.trailing_yoy_revenue_growth_pct), s_rg),
            _kv("return on equity", _f(a.return_on_equity_pct and a.return_on_equity_pct * 100, "{:.1f}%"), s_roe),
        ]},
        {"type": "series", "title": f"SEC filed annual EPS ({eps_a_concept or 'n/a'})", "unit": "$/sh",
         "points": [{"x": f"FY{e[2:4]}", "y": (eps_a.get(e) or {}).get("val"),
                     "src": sec.src(eps_a[e], eps_a_concept) if e in eps_a else
                     derived(f"no 10-K EPS fact for FY ending {e}", "n/a", [], {"label": "SEC companyfacts", "url": sec.facts_url})}
                    for e in annual_ends]},
        {"type": "table", "title": "SEC filed annual (10-K)", "cols": ["fiscal year", "EPS", "revenue", "EPS YoY"], "rows": ann_rows},
    ]
    if not annual_ends:
        a_blocks.append({"type": "text", "title": "SEC filed history", "text": "No 10-K annual EPS/revenue facts in SEC companyfacts.",
                         "src": src("SEC companyfacts (searched)", sec.facts_url or "https://www.sec.gov/edgar/search/")})
    sections.append(_section("A", "Annual growth", a_score, a_ssrc, a_blocks,
                             "Annual EPS up ≥25% in each of the last 3 years, ROE ≥17%. "
                             "Gauge: Yahoo earnings growth YoY over 0..50%. The 10-K series shows the real multi-year trend."))

    # ---- N
    ma_rows, pct_vs200, s_vs200_stock, stock_trend, s_stock_trend = _stock_ma_rows(S, hist)
    n_score, n_ssrc = _score("N", [
        (None if pct_off_high is None else 30 - pct_off_high, 0, 30, s_off_high),
        (pct_vs200, -10, 20, s_vs200_stock),
    ])
    sections.append(_section("N", "New high", n_score, n_ssrc, [
        {"type": "kv", "title": "Headline", "rows": [
            _kv("price", _f(current_price), s_price),
            _kv("52-week high", _f(fifty_high), s_high),
            _kv("52-week low", _f(fifty_low), s_low),
            _kv("off high", _f(pct_off_high and -pct_off_high, "{:.1f}%"), s_off_high),
        ]},
        {"type": "kv", "title": "Moving averages", "rows": ma_rows + [_kv("trend", stock_trend or "—", s_stock_trend)]}],
        "New products, management or price highs: buy as the stock emerges from a sound base toward new highs, not near lows. "
        "Leaders hold above the 200-day average; a close below it is a warning. "
        "Trend: price > MA50 > MA200 = uptrend, price < MA50 < MA200 = downtrend, otherwise correction. "
        "Gauge: mean of 30 − % off the 52-week high over 0..30 (at the high = 100, ≥30% off = 0) "
        "and % above the 200-day over -10..20."))

    # ---- S
    s_score, s_ssrc = _score("S", [(vol_surge, 0.5, 2.0, s_surge)])
    sections.append(_section("S", "Supply / demand", s_score, s_ssrc, [
        {"type": "kv", "title": "Headline", "rows": [
            _kv("shares outstanding", _big(s.shares_outstanding), _yf(S, "key-statistics", "defaultKeyStatistics.sharesOutstanding")),
            _kv("short % of float", _f(s.short_pct_of_float and s.short_pct_of_float * 100, "{:.1f}%"),
                _yf(S, "key-statistics", "defaultKeyStatistics.shortPercentOfFloat (fraction × 100)")),
            _kv("avg volume 10d", _big(vol_10d), s_v10),
            _kv("avg volume 3mo", _big(vol_3mo), s_v3),
            _kv("volume surge (10d / 3mo)", _f(vol_surge, "{:.2f}x"), s_surge),
        ]}],
        "Demand shows up as volume: big-volume up days on breakouts, light volume on pullbacks. "
        "Gauge: 10-day / 3-month average volume over 0.5..2.0x."))

    # ---- L
    l_score, l_ssrc = _score("L", [(rs_score, -20, 20, s_rs)])
    sections.append(_section("L", "Leader / laggard", l_score, l_ssrc, [
        {"type": "kv", "title": f"Headline ({RS_DAYS} sessions ≈ 3 months)", "rows": [
            _kv(f"{S} 3mo return", _sp(sym_ret), s_sym_ret),
            _kv("SPY 3mo return", _sp(spy_ret), s_spy_ret),
            _kv("relative strength", _f(rs_score, "{:+.1f}"), s_rs),
        ]}],
        "Buy leaders (IBD RS rating ≥80), avoid laggards. This is a simplified RS: 3-month return minus SPY's, "
        "not IBD's 12-month weighted percentile. Gauge: RS over −20..+20."))

    # ---- I
    s_inst = _yf(S, "holders", "defaultKeyStatistics.heldPercentInstitutions (fraction × 100)")
    i_score, i_ssrc = _score("I", [(i.held_pct_institutions and i.held_pct_institutions * 100, 0, 100, s_inst)])
    sections.append(_section("I", "Institutional", i_score, i_ssrc, [
        {"type": "kv", "title": "Headline", "rows": [
            _kv("held by institutions", _f(i.held_pct_institutions and i.held_pct_institutions * 100, "{:.1f}%"), s_inst),
            _kv("analyst recommendation", i.recommendation_key or "—", _yf(S, AN, "financialData.recommendationKey")),
            _kv("target mean price", _f(i.target_mean_price), _yf(S, AN, "financialData.targetMeanPrice")),
            _kv("net insider shares purchased (6mo)", _big(i.net_insider_shares_purchased),
                _yf(S, "insider-transactions", "netSharePurchaseActivity.netShares")),
        ]},
        {"type": "table", "title": "Top institutional holders", "cols": ["holder", "% held", "value", "reported"],
         "rows": [{"cells": [h.organization or "?", _f(h.pct_held and h.pct_held * 100, "{:.2f}%"), _f(h.value, "${:,.0f}") if h.value is None else "$" + _big(h.value), d or "—"],
                   "src": _yf(S, "holders", f"institutionOwnership.ownershipList[{k}] {h.organization} (13F as of {d or '?'})")}
                  for k, (h, d) in enumerate(zip(top_holders, holder_dates))]},
    ], "Look for increasing sponsorship by quality institutions, but not over-owned. "
       "Gauge: % held by institutions over 0..100."))

    # ---- M
    internals = _market_internals(session, spy_hist)
    dist_rows, spy_dist, s_spy_dist = _dist_blocks(internals)
    breadth_kv, pct50, s_pct50 = _breadth_rows(internals["breadth"])
    m_val = {"uptrend": 100, "correction": 50, "downtrend": 0}.get(trend or "")
    s_m_trend = derived("SPY trend gauge", f"trend {trend or 'n/a'}: uptrend = 100, correction = 50, downtrend = 0", [s_trend])
    m_score, m_ssrc = _score("M", [
        (m_val, 0, 100, s_m_trend),
        (None if spy_dist is None else -spy_dist, -7, 0, s_spy_dist),
        (pct50, 20, 80, s_pct50),
    ])
    sections.append(_section("M", "Market direction", m_score, m_ssrc, [
        {"type": "kv", "title": "SPY", "rows": [
            _kv("SPY close", _f(spy_price), s_spy),
            _kv("50-day MA", _f(ma50), s_ma50),
            _kv("200-day MA", _f(ma200), s_ma200),
            _kv("SPY vs MA50", _f(vs50, "{:+.2f}"), s_vs50),
            _kv("SPY vs MA200", _f(vs200, "{:+.2f}"), s_vs200),
            _kv("trend", trend or "—", s_trend),
        ]},
        {"type": "table", "title": "Indices (RSP = equal-weight S&P: lagging SPY means narrow leadership)",
         "cols": ["index", "close", "MA50", "MA200", "trend"], "rows": internals["index_rows"]},
        {"type": "table", "title": f"Distribution days, last {market.DIST_WINDOW} sessions",
         "cols": ["index", "date", "change", "volume", "prior volume"], "rows": dist_rows},
        {"type": "kv", "title": "Breadth (finlarp universe)", "rows": breadth_kv}],
        "Three of four stocks follow the market: buy in a confirmed uptrend, raise cash in corrections. "
        "Trend: SPY > MA50 > MA200 = uptrend, SPY < MA50 < MA200 = downtrend, otherwise correction. "
        "Distribution days: a down day of 0.2%+ on volume above the prior session; 5+ in 25 sessions means "
        "institutions are selling. Breadth: the share of the universe above its 50-day average; a rising "
        "index on falling breadth is a warning. Gauge: mean of trend (0..100), SPY distribution days "
        "(7 → 0), and breadth above 50-day (20%..80%)."))

    scored = [(sec_["id"].upper(), sec_["score"]) for sec_ in sections if sec_["score"] is not None]
    overall = None
    if scored:
        o = sum(v for _, v in scored) // len(scored)
        overall = {"score": o, "grade": _grade(o), "src": derived(
            "overall (mean of letter gauges)", " + ".join(f"{k} {v}" for k, v in scored) + f" / {len(scored)} = {o}",
            [sec_["score_src"] for sec_ in sections if sec_["score"] is not None])}
    for sec_ in sections:
        sec_.pop("score")
        sec_.pop("score_src")

    return CanslimScorecard(symbol=symbol, as_of=date.today(), c=c, a=a, n=n, s=s, l=lead, i=i, m=m,
                            overall=overall, sections=sections)


def _held_symbols() -> list[str]:
    txns = db.get_all_cached_transactions()
    share_affecting = {"Bought", "Sold", "Stock Split"}
    return sorted({t["symbol"] for t in txns if t.get("type") in share_affecting and t.get("symbol")})


if __name__ == "__main__":
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if "--all" in sys.argv:
        symbols = _held_symbols()
        print(f"scoring {len(symbols)} symbols: {', '.join(symbols)}", file=sys.stderr)
        cards = []
        for symbol in symbols:
            try:
                cards.append(build_scorecard(symbol, use_cache=not force).model_dump(mode="json"))
            except Exception as e:
                print(f"  skipping {symbol}: {e}", file=sys.stderr)
        print(json.dumps(cards, indent=2))
    else:
        symbol = args[0] if args else "MU"
        card = build_scorecard(symbol, use_cache=not force)
        print(card.model_dump_json(indent=2))
