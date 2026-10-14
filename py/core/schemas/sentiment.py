"""Structured output for the tweet labeller (sources/tweet_sentiment.py).

These models are the contract with the language model: the JSON Schema sent as the response format is generated from them,
so every `Field(description=...)` is read by the model and states the rule for that field. The same models validate the
reply and document the `tweet_sentiment` / `tweet_meta` views (core.schemas.views), so there is one source for the meaning
of each column.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Focus(StrEnum):
    primary = "primary"
    secondary = "secondary"
    passing_mention = "passing_mention"


class ViewHolder(StrEnum):
    author = "author"
    quoted_analyst = "quoted_analyst"
    quoted_person = "quoted_person"
    none = "none"


class Claim(StrEnum):
    own_analysis = "own_analysis"
    news_headline = "news_headline"
    price_target = "price_target"
    rumor = "rumor"
    earnings_or_data = "earnings_or_data"
    forecast = "forecast"
    market_recap = "market_recap"
    question = "question"
    promo_shill = "promo_shill"
    other = "other"


class Horizon(StrEnum):
    intraday = "intraday"
    days = "days"
    weeks = "weeks"
    months_plus = "months_plus"
    unspecified = "unspecified"


class TweetType(StrEnum):
    analysis = "analysis"
    news_recap = "news_recap"
    market_recap = "market_recap"
    price_target_list = "price_target_list"
    question = "question"
    promo = "promo"
    joke_meme = "joke_meme"
    other = "other"


class Theme(StrEnum):
    ai_capex = "ai_capex"
    memory_cycle = "memory_cycle"
    optics_photonics = "optics_photonics"
    neocloud = "neocloud"
    power_energy = "power_energy"
    semis_equipment = "semis_equipment"
    foundry_packaging = "foundry_packaging"
    earnings = "earnings"
    macro_rates = "macro_rates"
    valuation = "valuation"
    short_thesis = "short_thesis"
    financing_dilution = "financing_dilution"
    m_and_a = "m_and_a"
    analyst_rating = "analyst_rating"
    supply_chain = "supply_chain"
    product_launch = "product_launch"
    regulation_legal = "regulation_legal"
    customer_contract = "customer_contract"
    other = "other"


STANCE_DESC = (

        "The view of whoever view_holder names, about this stock: -2 clearly bearish (short, sell, expects a fall), -1 leaning "
        "negative, 0 neutral or no view, 1 leaning positive, 2 clearly bullish (buying, expects a rise). Judge each ticker on its "
        "own, so one tweet can be bullish on one name and bearish on another. Price action is not a view: words like laggard, "
        "leader, outperformed, fell, rallied, red, green, up, down are a recap and stay 0, as do market-cap rankings and "
        "reports that a deal was signed or a result printed, unless the author says what it means for the stock. If the author "
        "lays out a bullish and a bearish case without choosing, every ticker is 0, including the tickers listed under the Bullish heading. A ticker the author owns is +1; one they are "
        "actively buying or adding to is +2. If A is called a winner or better than B, B is negative only if the tweet says B is "
        "worse or should be sold. If a note says X threatens Y, X is not bearish for itself. Sarcasm or mockery of a crowd is 0 "
        "unless the intended position is clear. Saying that shorting or selling a stock is a mistake or dumb is bullish on it. Holding a company up as the example to follow, or saying it overtook or beat a rival, is positive for that company. Complaining that the market ignores or undervalues a stock means the author sees it as cheap, so it is not bearish. Ridiculing a company's choices or management is negative even when the tweet also describes price action"
)

VIEW_HOLDER_DESC = (

        "Whose view the stance is. author: the tweet's writer holds it (also when they clearly agree or disagree with a quoted "
        "view). quoted_analyst: a bank or analyst note the author reports. quoted_person: a named investor or executive the author "
        "reports, such as 'Burry shorts X'. none: no view at all, such as a bare announcement; if view_holder is none, stance is 0 (an author who holds a neutral view is still view_holder author). A forecast, estimate raise, upgrade, price increase or target reported from a bank, analyst or media report is quoted_analyst, with the direction it implies for the stock. A statement by an executive, analyst or media report about demand, pricing, supply, growth or margins of the company or its market is a view (quoted_person or quoted_analyst) with the direction it implies for the stock, even when the author adds no comment of their own. A claim of forecast or price_target always has a view_holder other than none"
)


class TweetLabel(BaseModel):
    """One view on one stock, taken from one tweet."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(description="Cashtag symbol, upper-case without the $. Only a ticker from the tweet's own cashtag list; never add others")
    focus: Focus = Field(description=(
        "How much the tweet is about this ticker. primary: it is the subject. secondary: discussed alongside others. "
        "passing_mention: named in a list, a run of tags, or as context for another company. A passing_mention is always "
        "stance 0 and view_holder none unless the tweet explicitly takes a side on this ticker"))
    stance: Literal[-2, -1, 0, 1, 2] = Field(description=STANCE_DESC)
    view_holder: ViewHolder = Field(description=VIEW_HOLDER_DESC)
    claim: Claim = Field(description=(
        "What kind of statement this is about the ticker. own_analysis: the author's reasoning or thesis. news_headline: reports "
        "news. price_target: gives a target price. forecast: a forward-looking estimate, estimate change, upgrade, downgrade or expected shift in demand or prices about the stock or its market, from anyone. rumor: unconfirmed. earnings_or_data: reported results, filings or company "
        "data. market_recap: only a recap of price moves or a ranking; reported company financials are earnings_or_data. question. promo_shill: touting, referral, group invite, lure, "
        "copy-paste spam. other"))
    horizon: Horizon = Field(description="Time frame of the view; unspecified when the tweet gives none")
    has_numbers: bool = Field(description="The tweet states a price, target, percent or financial figure for this ticker")
    price_target: float | None = Field(description="Target price in USD if the tweet gives one for this ticker, otherwise null")
    catalyst: str = Field(description="The event or reason behind the stance in at most 8 words; empty string if none")
    evidence: str = Field(description="The shortest verbatim phrase from the tweet (at most 12 words) that supports the stance")
    confidence: float = Field(ge=0, le=1, description="How sure you are of the stance, 0 to 1")


HOLDERS = Literal[ViewHolder.author, ViewHolder.quoted_analyst, ViewHolder.quoted_person]
# Claims that can stand without anyone holding a view: forecasts, targets, analysis and recaps cannot.
NEUTRAL_CLAIMS = Literal[
    Claim.news_headline, Claim.earnings_or_data, Claim.market_recap, Claim.rumor, Claim.question, Claim.promo_shill, Claim.other]
OPINION_CLAIMS = Literal[
    Claim.own_analysis, Claim.news_headline, Claim.price_target, Claim.forecast, Claim.rumor, Claim.earnings_or_data,
    Claim.question, Claim.promo_shill, Claim.other]


class LabelNoView(TweetLabel):
    """No view expressed, so the stance can only be 0; a forecast, target, analysis or recap is never view-less."""

    view_holder: Literal[ViewHolder.none] = Field(description=VIEW_HOLDER_DESC)
    claim: NEUTRAL_CLAIMS = Field(description="What kind of statement this is about the ticker; see the claim values")
    stance: Literal[0] = Field(description=STANCE_DESC)


class LabelRecap(TweetLabel):
    """A recap of price moves or a ranking: a view may be attached, but the recap itself carries stance 0."""

    view_holder: HOLDERS = Field(description=VIEW_HOLDER_DESC)
    claim: Literal[Claim.market_recap] = Field(description="Always market_recap for this variant: a recap of price moves or a ranking")
    stance: Literal[0] = Field(description=STANCE_DESC)


class LabelOpinion(TweetLabel):
    """A view held or reported by someone, with the full stance scale."""

    view_holder: HOLDERS = Field(description=VIEW_HOLDER_DESC)
    claim: OPINION_CLAIMS = Field(description="What kind of statement this is about the ticker; see the claim values")
    stance: Literal[-2, -1, 0, 1, 2] = Field(description=STANCE_DESC)


class TweetItem(BaseModel):
    """Everything extracted from one tweet: metadata plus one label per cashtag."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="The tweet id, copied exactly from the input")
    tweet_type: TweetType = Field(description="What the tweet as a whole is")
    themes: list[Theme] = Field(max_length=3, description="Up to 3 themes that fit the tweet, from the allowed list")
    keywords: list[str] = Field(max_length=6, description=(
        "3 to 6 lowercase phrases of at most 3 words naming the specific topics, such as products, events or technologies "
        "('hbm4', 'optical circuit switching', 'atm offering')"))
    entities: list[str] = Field(description="Companies, funds, people and products named WITHOUT a cashtag")
    is_repost: bool = Field(description="The tweet only passes along someone else's post or an article")
    is_sarcastic: bool = Field(description="The tweet is sarcastic or mocks a position instead of holding it")
    labels: list[LabelNoView | LabelRecap | LabelOpinion] = Field(description="One label per cashtag listed for this tweet, no others")


class TweetBatch(BaseModel):
    """The reply: one item per input tweet."""

    model_config = ConfigDict(extra="forbid")

    items: list[TweetItem]


def strict_schema(model: type[BaseModel]) -> dict:
    """JSON Schema in the subset OpenAI strict structured outputs accepts: every $ref inlined (a field's own description
    wins over the referenced enum's), no $defs, and no title or default keys."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, list):
            return [walk(v) for v in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            target = defs[node["$ref"].rsplit("/", 1)[-1]]
            node = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
        return {k: walk(v) for k, v in node.items() if k not in ("title", "default")}

    return walk(schema)
