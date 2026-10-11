"""Column documentation for the DuckDB views the MCP `sql` tool exposes.

Each model mirrors one view; the `Field(description=...)` text is the single source for column
docs. `core.schemas.dictionary` sweeps these (and every other schema model) to annotate `schema`
output and to flag drift between a model and the view it documents. Add a model here, register it
in VIEW_MODELS, and the docs show up everywhere with no further wiring.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from core.schemas import sec_views as sv


class UniverseView(BaseModel):
    """One row per tracked ticker."""

    ticker: str = Field(description="Upper-case symbol, joins to every other table's ticker/symbol column")
    name: str = Field(description="Company name")
    region: str | None = Field(description="Listing region, e.g. US")
    cik: int | None = Field(description="SEC Central Index Key")
    primary: str = Field(description="JSON {bucket: weight} of AI-exposure buckets; prefer primary_bucket")
    subs: str = Field(description="JSON {sub-bucket: weight}, weights sum to 1")
    primary_bucket: str | None = Field(description="Dominant AI-exposure bucket (max weight in `primary`)")
    primary_weight: float | None = Field(description="Weight of primary_bucket, 0-1; <1 means a blended name")


class Bar1d(BaseModel):
    """Databento consolidated daily bar."""

    ts_event: datetime = Field(description="Midnight UTC of the trade date; use (ts_event AT TIME ZONE 'UTC')::date")
    symbol: str = Field(description="Ticker")
    open: float = Field(description="Session open, USD")
    high: float = Field(description="Session high, USD")
    low: float = Field(description="Session low, USD")
    close: float = Field(description="Session close, USD")
    volume: int = Field(description="True consolidated share volume (use this for volume rules)")


class Bar1m(BaseModel):
    """Databento 1-minute bar, Nasdaq venues only."""

    ts_event: datetime = Field(description="Bar start, UTC-aware; 04:00-20:00 ET incl. pre/post-market")
    symbol: str = Field(description="Ticker")
    open: float = Field(description="Minute open, USD")
    high: float = Field(description="Minute high, USD")
    low: float = Field(description="Minute low, USD")
    close: float = Field(description="Minute close, USD")
    volume: int = Field(description="Nasdaq-venue share volume only (~50-100% of consolidated, median ~79%)")


class Bar1mEt(Bar1m):
    """bars_1m plus ET calendar columns."""

    et_ts: datetime = Field(description="Naive ET timestamp of the bar")
    et_date: date = Field(description="ET calendar date")
    et_minute: int = Field(description="Minutes since midnight ET; regular session = 570..959")


class Bar1mSession(Bar1mEt):
    """Regular-session (09:30-16:00 ET) minutes with consolidated-scaled volume."""

    nasdaq_day_vol: int = Field(description="Sum of the symbol's Nasdaq 1m volume over the whole ET day")
    cons_day_vol: int | None = Field(description="bars_1d consolidated volume for the same day; null if no daily bar")
    vol_est: float | None = Field(description="volume * cons_day_vol / nasdaq_day_vol; approximate consolidated volume")


class BarN(BaseModel):
    """Regular-session N-minute bar (bars_5m, bars_30m)."""

    symbol: str = Field(description="Ticker")
    et_date: date = Field(description="ET calendar date")
    slot_minute: int = Field(description="Slot start in minutes since midnight ET (570 = 09:30)")
    slot_label: str = Field(description="Slot start as HH:MM ET")
    open: float = Field(description="First minute's open in the slot")
    high: float = Field(description="Highest high in the slot")
    low: float = Field(description="Lowest low in the slot")
    close: float = Field(description="Last minute's close in the slot")
    volume: int = Field(description="Nasdaq-venue share volume")
    vol_est: float | None = Field(description="Consolidated-scaled volume (see bars_1m_session.vol_est)")
    n_minutes: int = Field(description="Minutes with trades in the slot; low values mean thin trading or gaps")


class TradingDay(BaseModel):
    """One row per ET date that has regular-session bars, derived from the data itself."""

    et_date: date = Field(description="ET calendar date")
    n_symbols: int = Field(description="Symbols with at least one regular-session bar that day")
    median_close_minute: float = Field(
        description="Median across symbols of the et_minute holding the day's volume peak (the closing cross): "
                    "~960 on a normal day, ~780 on an early-close day")
    is_half_day: bool = Field(description="True when the closing cross prints before 15:00 ET (early close)")
    is_thin_day: bool = Field(description="True when n_symbols is under 80% of the median day; data-gap suspect")


# view name -> model documenting its columns
VIEW_MODELS: dict[str, type[BaseModel]] = {
    "universe": UniverseView,
    "bars_1d": Bar1d,
    "bars_1m": Bar1m,
    "bars_1m_et": Bar1mEt,
    "bars_1m_session": Bar1mSession,
    "bars_5m": BarN,
    "bars_30m": BarN,
    "trading_days": TradingDay,
    "facts": sv.FactsView,
    "concepts": sv.ConceptsView,
    "segments": sv.SegmentsView,
    "holdings_13f": sv.Holdings13F,
    "cusip_map": sv.CusipMap,
    "filings": sv.FilingsView,
    "events": sv.EventsView,
    "insider_tx": sv.InsiderTx,
    "earnings": sv.EarningsView,
    "annual_reports": sv.AnnualReports,
    "report_sections": sv.ReportSections,
    "risk_diff": sv.RiskDiff,
    "subsidiaries": sv.Subsidiaries,
    "profiles": sv.Profiles,
    "patents": sv.Patents,
    "patent_ticker": sv.PatentTicker,
    "patent_cpc": sv.PatentCpc,
    "patent_wipo": sv.PatentWipo,
    "patent_inventors": sv.PatentInventors,
    "patent_assignees": sv.PatentAssignees,
    "patent_ai": sv.PatentAi,
    "patent_ai_by_ticker_year": sv.PatentAiByTickerYear,
    "quotes_1m": sv.Quotes1m,
    "tweets": sv.TweetsView,
    "tweet_tickers": sv.TweetTickers,
}
