"""CANSLIM scorecard data models (Bill O'Neil's growth-stock framework)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class EarningsQuarter(BaseModel):
    """One reported quarter: actual vs analyst estimate."""

    quarter_end: str | None  # "YYYY-MM-DD"
    eps_actual: float | None
    eps_estimate: float | None
    surprise_pct: float | None


class RevenueQuarter(BaseModel):
    """One filed quarter's revenue (SEC EDGAR, not an estimate) plus its
    sequential (QoQ) and year-over-year growth against other filed
    quarters in the same series — real filed data, not Yahoo's summary."""

    quarter_end: str | None  # "YYYY-MM-DD"
    revenue: float | None
    qoq_growth_pct: float | None
    yoy_growth_pct: float | None
    net_income: float | None = None
    net_margin_pct: float | None = None


class CurrentEarnings(BaseModel):
    """C — Current quarterly earnings"""

    eps_estimate_current: float | None
    eps_estimate_7d_ago: float | None
    eps_estimate_30d_ago: float | None
    eps_estimate_90d_ago: float | None
    forward_qtr_eps_growth_pct: float | None
    # A growth % from 1-3 analysts (small/thinly-covered names) deserves
    # much less confidence than the same number from 20+ — surfaced so a
    # dramatic-looking figure like AEHR's 833% (near-zero base, 3 analysts)
    # reads as "thin coverage" instead of misleadingly authoritative.
    num_analysts: int | None
    history: list[EarningsQuarter] = []
    # SEC-filed quarterly revenue — the "sales must confirm earnings" half
    # of IBD's actual C rule, which pure EPS-estimate tracking above misses
    # entirely. Yahoo's earningsHistory has no revenue-surprise equivalent.
    revenue_history: list[RevenueQuarter] = []


class AnnualPeriod(BaseModel):
    """One filed fiscal year's EPS/revenue (SEC EDGAR 10-K), for a real
    multi-year growth trend instead of Yahoo's single trailing-YoY number."""

    fiscal_year_end: str | None
    eps: float | None
    revenue: float | None


class AnnualEarnings(BaseModel):
    """A — Annual earnings growth"""

    trailing_yoy_earnings_growth_pct: float | None
    trailing_yoy_revenue_growth_pct: float | None
    return_on_equity_pct: float | None
    history: list[AnnualPeriod] = []


class NewHighs(BaseModel):
    """N — New product/management/price highs"""

    price_current: float | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None
    pct_off_high: float | None


class SupplyDemand(BaseModel):
    """S — Supply and demand"""

    shares_outstanding: float | None
    short_pct_of_float: float | None
    avg_volume_10d: float | None
    avg_volume_3mo: float | None
    volume_surge_ratio: float | None


class LeaderLaggard(BaseModel):
    """L — Leader or laggard (relative strength vs benchmark)"""

    symbol_return_pct: float | None
    benchmark_return_pct: float | None
    relative_strength_score: float | None


class TopHolder(BaseModel):
    organization: str | None
    pct_held: float | None
    value: float | None


class InstitutionalSponsorship(BaseModel):
    """I — Institutional sponsorship"""

    held_pct_institutions: float | None
    top_holders: list[TopHolder]
    net_insider_shares_purchased: float | None
    recommendation_key: str | None
    target_mean_price: float | None


class MarketDirection(BaseModel):
    """M — Market direction (index-level, not per-symbol)"""

    index_symbol: str = "SPY"
    price_vs_ma50: float | None
    price_vs_ma200: float | None
    trend: str | None


class CanslimScorecard(BaseModel):
    symbol: str
    as_of: date
    c: CurrentEarnings
    a: AnnualEarnings
    n: NewHighs
    s: SupplyDemand
    l: LeaderLaggard
    i: InstitutionalSponsorship
    m: MarketDirection
    # Sourced view of the letters above (views/canslim.py): model-shaped
    # Sections, one per letter, every value with a Source. Rendered by the
    # finlarp `canslim` screen.
    overall: dict | None = None
    sections: list[dict] = []
