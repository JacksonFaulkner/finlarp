"""Build a CanslimScorecard for a symbol from Yahoo Finance data."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import db
import services.edgar as edgar
from models.canslim import (
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

MODULES = ",".join([
    "assetProfile", "summaryDetail", "defaultKeyStatistics", "financialData",
    "earningsTrend", "earningsHistory", "recommendationTrend",
    "upgradeDowngradeHistory", "institutionOwnership", "majorHoldersBreakdown",
    "insiderTransactions", "netSharePurchaseActivity", "price", "calendarEvents",
])


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


def build_scorecard(symbol: str, use_cache: bool = True) -> CanslimScorecard:
    if use_cache:
        cached = db.get_cached_canslim(symbol)
        if cached is not None:
            return CanslimScorecard.model_validate(cached)

    card = _fetch_scorecard(symbol)
    db.put_cached_canslim(symbol, card.model_dump(mode="json"))
    return card


def _fetch_scorecard(symbol: str) -> CanslimScorecard:
    session = config._session()
    crumb = config._crumb(session)
    qs = _quote_summary(session, crumb, symbol)
    hist = config.cmd_history(symbol, "1y", "1d")["points"]
    spy_hist = config.cmd_history("SPY", "1y", "1d")["points"]

    et = qs.get("earningsTrend", {}).get("trend", [])
    current_trend = et[0] if et else {}
    eps_trend = current_trend.get("epsTrend", {})
    eps_estimate = current_trend.get("earningsEstimate", {})

    fd = qs.get("financialData", {})
    dks = qs.get("defaultKeyStatistics", {})
    sd = qs.get("summaryDetail", {})
    price_mod = qs.get("price", {})
    io = qs.get("institutionOwnership", {}).get("ownershipList", [])
    nspa = qs.get("netSharePurchaseActivity", {})
    eh = qs.get("earningsHistory", {}).get("history", [])

    # SEC EDGAR failures (rate limit, unmapped ticker, no filings yet for a
    # recent IPO) shouldn't break the whole scorecard — Yahoo-only fields
    # still work fine without them.
    try:
        edgar_quarterly_revenue = edgar.get_quarterly_revenue(symbol)
    except Exception:
        edgar_quarterly_revenue = []
    try:
        edgar_annual = edgar.get_annual_series(symbol)
    except Exception:
        edgar_annual = []

    current_price = _raw(price_mod.get("regularMarketPrice"))
    fifty_high = _raw(sd.get("fiftyTwoWeekHigh"))
    fifty_low = _raw(sd.get("fiftyTwoWeekLow"))
    pct_off_high = None
    if current_price and fifty_high:
        pct_off_high = (fifty_high - current_price) / fifty_high * 100

    vol_10d = _raw(sd.get("averageVolume10days") or dks.get("averageDailyVolume10Day"))
    vol_3mo = _raw(sd.get("averageVolume") or dks.get("averageDailyVolume3Month"))
    vol_surge = None
    if vol_10d and vol_3mo:
        vol_surge = vol_10d / vol_3mo

    sym_ret = _pct_return(hist, 63)
    spy_ret = _pct_return(spy_hist, 63)
    rs_score = None
    if sym_ret is not None and spy_ret is not None:
        rs_score = sym_ret - spy_ret

    ma50 = _sma(spy_hist, 50)
    ma200 = _sma(spy_hist, 200)
    spy_price = spy_hist[-1]["close"] if spy_hist else None
    trend = None
    if spy_price and ma50 and ma200:
        if spy_price > ma50 > ma200:
            trend = "uptrend"
        elif spy_price < ma50 < ma200:
            trend = "downtrend"
        else:
            trend = "correction"

    top_holders = [
        TopHolder(
            organization=h.get("organization"),
            pct_held=_raw(h.get("pctHeld")),
            value=_raw(h.get("value")),
        )
        for h in io[:5]
    ]

    earnings_history = [
        EarningsQuarter(
            quarter_end=(q.get("quarter") or {}).get("fmt"),
            eps_actual=_raw(q.get("epsActual")),
            eps_estimate=_raw(q.get("epsEstimate")),
            surprise_pct=_raw(q.get("surprisePercent")),
        )
        for q in eh
    ]

    # edgar_quarterly_revenue is oldest -> newest; QoQ compares each
    # quarter to the one immediately before it, YoY to 4 quarters back
    # (same set skips a quarter if EDGAR's filed series has a gap).
    revenue_history = []
    for idx, q in enumerate(edgar_quarterly_revenue):
        qoq = None
        if idx > 0 and edgar_quarterly_revenue[idx - 1]["revenue"]:
            prev = edgar_quarterly_revenue[idx - 1]["revenue"]
            qoq = (q["revenue"] - prev) / prev * 100
        yoy = None
        if idx >= 4 and edgar_quarterly_revenue[idx - 4]["revenue"]:
            prev_year = edgar_quarterly_revenue[idx - 4]["revenue"]
            yoy = (q["revenue"] - prev_year) / prev_year * 100
        revenue_history.append(RevenueQuarter(
            quarter_end=q["quarter_end"],
            revenue=q["revenue"],
            qoq_growth_pct=qoq,
            yoy_growth_pct=yoy,
        ))

    annual_history = [
        AnnualPeriod(fiscal_year_end=y["fiscal_year_end"], eps=y["eps"], revenue=y["revenue"])
        for y in edgar_annual
    ]

    return CanslimScorecard(
        symbol=symbol,
        as_of=date.today(),
        c=CurrentEarnings(
            eps_estimate_current=_raw(eps_estimate.get("avg")),
            eps_estimate_7d_ago=_raw(eps_trend.get("7daysAgo")),
            eps_estimate_30d_ago=_raw(eps_trend.get("30daysAgo")),
            eps_estimate_90d_ago=_raw(eps_trend.get("90daysAgo")),
            forward_qtr_eps_growth_pct=_raw(eps_estimate.get("growth")),
            history=earnings_history,
            revenue_history=revenue_history,
        ),
        a=AnnualEarnings(
            trailing_yoy_earnings_growth_pct=_raw(fd.get("earningsGrowth")),
            trailing_yoy_revenue_growth_pct=_raw(fd.get("revenueGrowth")),
            return_on_equity_pct=_raw(fd.get("returnOnEquity")),
            history=annual_history,
        ),
        n=NewHighs(
            price_current=current_price,
            fifty_two_week_high=fifty_high,
            fifty_two_week_low=fifty_low,
            pct_off_high=pct_off_high,
        ),
        s=SupplyDemand(
            shares_outstanding=_raw(dks.get("sharesOutstanding")),
            short_pct_of_float=_raw(dks.get("shortPercentOfFloat")),
            avg_volume_10d=vol_10d,
            avg_volume_3mo=vol_3mo,
            volume_surge_ratio=vol_surge,
        ),
        l=LeaderLaggard(
            symbol_return_pct=sym_ret,
            benchmark_return_pct=spy_ret,
            relative_strength_score=rs_score,
        ),
        i=InstitutionalSponsorship(
            held_pct_institutions=_raw(dks.get("heldPercentInstitutions")),
            top_holders=top_holders,
            net_insider_shares_purchased=_raw(
                nspa.get("netShares") or nspa.get("netInfoShares")
            ),
            recommendation_key=fd.get("recommendationKey"),
            target_mean_price=_raw(fd.get("targetMeanPrice")),
        ),
        m=MarketDirection(
            index_symbol="SPY",
            price_vs_ma50=(spy_price - ma50) if (spy_price and ma50) else None,
            price_vs_ma200=(spy_price - ma200) if (spy_price and ma200) else None,
            trend=trend,
        ),
    )


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
