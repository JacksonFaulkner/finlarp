"""Column documentation for the DuckDB views the MCP `sql` tool exposes.

Each model mirrors one view; the `Field(description=...)` text is the single source for column
docs. `core.schemas.dictionary` sweeps these (and every other schema model) to annotate `schema`
output and to flag drift between a model and the view it documents. Add a model here, register it
in VIEW_MODELS, and the docs show up everywhere with no further wiring.
"""

from __future__ import annotations

import datetime as dt  # a field named `date` shadows the `date` type inside its own class body
from datetime import date, datetime

from pydantic import BaseModel, Field

from core.schemas import sec_views as sv
from core.schemas.sentiment import TweetItem, TweetLabel


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


class AccountFill(BaseModel):
    """One buy or sell fill from the user's broker (E*TRADE), built by derive/account.py."""

    fill_id: str = Field(description="Broker transaction id; a repeat id gets a #n suffix")
    acct: str = Field(description="Short hash of the broker account number")
    ts: datetime = Field(description="Fill time, UTC-aware")
    et_ts: datetime = Field(description="Naive ET timestamp of the fill")
    et_date: date = Field(description="ET calendar date; joins to bars_1d (trade date) and bars_5m.et_date")
    et_minute: int = Field(description="Minutes since midnight ET; regular session = 570..959")
    symbol: str = Field(description="Ticker, joins to bars_1d.symbol")
    side: str = Field(description="buy or sell")
    qty: float = Field(description="Shares as traded (always positive; direction is side)")
    price: float = Field(description="Price per share as traded, USD")
    amount: float = Field(description="Cash effect in USD after fees: negative for buys, positive for sells")
    split_factor: float = Field(description="New shares per old share for splits after this fill; 1.0 if none")
    qty_adj: float = Field(description="qty on today's share basis (qty * split_factor)")
    price_adj: float = Field(description="price on today's share basis (price / split_factor); compare to current prices")
    description: str | None = Field(description="Broker description, usually the company name")


class AccountRoundTrip(BaseModel):
    """One FIFO-paired lot: shares bought then sold, on a split-adjusted basis. Fees are not netted out."""

    lot_id: str = Field(description="symbol-n, in exit order")
    acct: str = Field(description="Short hash of the broker account number")
    symbol: str = Field(description="Ticker, joins to bars_1d.symbol")
    qty: float = Field(description="Shares in this lot (split-adjusted)")
    matched: bool = Field(description="False when the sell has no buy in the cache (entry/pnl columns are null)")
    entry_fill_id: str | None = Field(description="account_fills.fill_id of the buy")
    exit_fill_id: str = Field(description="account_fills.fill_id of the sell")
    entry_ts: datetime | None = Field(description="Buy time, UTC-aware")
    exit_ts: datetime = Field(description="Sell time, UTC-aware")
    entry_date: date | None = Field(description="ET date of the buy; join to bars_1d for entry context")
    exit_date: date = Field(description="ET date of the sell")
    entry_et_minute: int | None = Field(description="Minutes since midnight ET at entry; 570 = 09:30")
    exit_et_minute: int = Field(description="Minutes since midnight ET at exit")
    entry_price: float | None = Field(description="Buy price per share, split-adjusted, USD")
    exit_price: float = Field(description="Sell price per share, split-adjusted, USD")
    cost: float | None = Field(description="qty * entry_price, USD")
    proceeds: float = Field(description="qty * exit_price, USD")
    pnl: float | None = Field(description="Realized profit in USD, before fees")
    ret: float | None = Field(description="exit_price / entry_price - 1 (fraction, not percent)")
    hold_days: float | None = Field(description="Days between entry and exit fills")
    same_day: bool | None = Field(description="True when bought and sold on the same ET date")


class AccountPosition(BaseModel):
    """Open lots per symbol from the fill history, side by side with the broker's own positions."""

    symbol: str = Field(description="Ticker")
    qty: float = Field(description="Open shares from FIFO over the cached fills (split-adjusted)")
    avg_cost: float | None = Field(description="Average cost of the open FIFO lots, USD; null when qty is 0")
    cost_basis: float = Field(description="Total cost of the open FIFO lots, USD")
    n_lots: int = Field(description="Number of open FIFO lots")
    first_entry_date: date | None = Field(description="ET date of the oldest open lot")
    last_entry_date: date | None = Field(description="ET date of the newest open lot")
    broker_qty: float | None = Field(description="Shares per the broker's positions cache; 0 if the broker no longer lists it")
    broker_price_paid: float | None = Field(description="Broker's cost per share (its own cost method, not FIFO)")
    last_price: float | None = Field(description="Last price when the broker positions were cached, USD")
    market_value: float | None = Field(description="Broker market value, USD")
    unrealized_pnl: float | None = Field(description="Broker total gain in USD")
    qty_matches_broker: bool | None = Field(description="False means fills and broker disagree: missing history or a stale cache")
    as_of: datetime | None = Field(description="When the broker positions were cached, UTC-aware")


class AccountEquityDaily(BaseModel):
    """Portfolio value per calendar day, reconstructed from fills and Yahoo closes (not broker balances)."""

    date: dt.date = Field(description="Calendar date")
    total_value: float = Field(description="Portfolio market value at the end of the day, USD")
    net_flow: float = Field(description="Deposits minus withdrawals dated this day, USD")
    day_return: float | None = Field(description="Time-weighted: value / (prior value + net_flow) - 1, flow counted at the start of the day")
    twr_index: float = Field(description="Cumulative time-weighted index, 1.0 at the first date")
    drawdown: float = Field(description="twr_index / running max - 1 (fraction, <= 0)")
    is_stale: bool = Field(description="Value and flow unchanged from the prior day: a weekend/holiday carry-forward")


class AccountCash(BaseModel):
    """Non-trade cash events on the account."""

    acct: str = Field(description="Short hash of the broker account number")
    ts: datetime = Field(description="Event time, UTC-aware")
    et_date: date = Field(description="ET calendar date")
    kind: str = Field(description="deposit, withdrawal, dividend, interest or other")
    symbol: str | None = Field(description="Ticker for dividends; null otherwise")
    amount: float = Field(description="USD; positive is cash in")
    description: str | None = Field(description="Broker description")


class NewsView(BaseModel):
    """One company news article (title, link and a ~200 character snippet), pulled from ROIC.ai by sources/roic_news.py."""

    id: str = Field(description="Stable article id: sha1 of ticker|url, first 16 hex chars")
    ticker: str = Field(description="Universe ticker the article was pulled for; one row per (ticker, url)")
    published_at: datetime = Field(description="Publication time, naive UTC")
    title: str | None = Field(description="Headline")
    site: str | None = Field(description="Publisher domain as ROIC reports it, e.g. fool.com, globenewswire.com, seekingalpha.com")
    url: str = Field(description="Link to the original article")
    text: str = Field(description="Article snippet as ROIC returns it, about 200 characters (never the full article); use url for the rest")
    text_chars: int = Field(description="Length of text in characters; filter on it to drop stubs")


class ShortVolumeView(BaseModel):
    """FINRA Reg SHO daily short sale volume per ticker per day, from sources/short_interest.py (published the evening of the trade date)."""

    ticker: str = Field(description="Universe ticker")
    date: dt.date = Field(description="Trade date")
    short_volume: float = Field(description="Shares sold short that day across FINRA-reported venues; includes market-maker hedging, so it is flow, not a position")
    short_exempt_volume: float = Field(description="Part of short_volume that was short-exempt")
    total_volume: float = Field(description="Total shares traded that day across the same venues (not the consolidated tape total)")
    short_ratio: float | None = Field(description="short_volume / total_volume, 0-1; roughly 0.45-0.55 is normal, near 0.7 means heavy new shorting")


class ShortInterestView(BaseModel):
    """Short interest per ticker per FINRA settlement date (twice a month, published ~7 business days later), from sources/short_interest.py."""

    ticker: str = Field(description="Universe ticker")
    settlement_date: dt.date = Field(description="Settlement date the short position is as of; the data is public about 7 business days later")
    short_interest: float = Field(description="Shares sold short and not yet covered at settlement")
    avg_daily_volume: float | None = Field(description="Average daily share volume used for days_to_cover; null for the Yahoo fallback")
    days_to_cover: float | None = Field(description="short_interest / avg_daily_volume: how many days of normal volume it takes shorts to cover")
    source: str = Field(description="nasdaq = ~2 years of history for Nasdaq-listed names; yahoo = fallback, only the latest two settlements")
    fetched_at: datetime = Field(description="When this ticker's history was last pulled, UTC")


class TweetSentimentView(TweetLabel):
    """One labelled view on one ticker in one tweet, from sources/tweet_sentiment.py. Column docs are the labeller's own
    field descriptions (core.schemas.sentiment), so the rules the model followed are the rules documented here."""

    id: str = Field(description="Tweet id; joins to tweets.id and tweet_meta.id. One row per (id, ticker)")
    votes: int = Field(description="How many independent labelling passes named this ticker for the tweet. Stance is the median across them")
    agreement: float = Field(description="Share of those passes whose stance has the same sign as the final stance, 0 to 1; low means a contested label")


class TweetMetaView(BaseModel):
    """Tweet-level metadata from the same labelling pass, one row per labelled tweet."""

    id: str = Field(description="Tweet id; joins to tweets.id")
    tweet_type: str = TweetItem.model_fields["tweet_type"]
    themes: list[str] = TweetItem.model_fields["themes"]
    keywords: list[str] = TweetItem.model_fields["keywords"]
    entities: list[str] = TweetItem.model_fields["entities"]
    is_repost: bool = TweetItem.model_fields["is_repost"]
    is_sarcastic: bool = TweetItem.model_fields["is_sarcastic"]


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
    "news": NewsView,
    "short_volume": ShortVolumeView,
    "short_interest": ShortInterestView,
    "tweet_sentiment": TweetSentimentView,
    "tweet_meta": TweetMetaView,
    "account_fills": AccountFill,
    "account_round_trips": AccountRoundTrip,
    "account_positions": AccountPosition,
    "account_equity_daily": AccountEquityDaily,
    "account_cash": AccountCash,
}
