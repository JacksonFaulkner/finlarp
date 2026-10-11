"""Column documentation for the SEC, patent, profile, tweet and quote views (registered in views.py)."""

from __future__ import annotations

from datetime import date, datetime
from datetime import date as _Date

from pydantic import BaseModel, Field


class FactsView(BaseModel):
    """XBRL companyfacts, one row per (ticker, taxonomy, concept, unit, start, end), latest-filed copy kept."""

    ticker: str = Field(description="Universe ticker; may include a predecessor registrant's history (e.g. MTCH=IAC)")
    cik: int = Field(description="SEC CIK of the registrant that filed the fact (can differ from universe.cik)")
    taxonomy: str = Field(description="XBRL taxonomy: us-gaap, ifrs-full, dei or srt")
    concept: str = Field(description="XBRL element name, e.g. Revenues; companies switch concepts over time (ASC 606 in 2018)")
    unit: str = Field(description="XBRL unit as filed: USD, shares, USD/shares, pure, or a foreign currency; filter on it")
    start: date | None = Field(description="Period start; NULL for instant (balance-sheet) facts")
    end: date = Field(description="Period end, or the instant date; derive periods from start/end, not fy/fp")
    val: float = Field(description="Reported value in `unit`, in full units (not thousands/millions); restated value if restated")
    fy: int | None = Field(description="Fiscal year of the FILING the kept copy came from, not of the fact's own period")
    fp: str | None = Field(description="Fiscal period of the filing the copy came from: Q1-Q3, FY (10-K has no Q4); not the fact's period")
    form: str | None = Field(description="Form type of the source filing (10-K, 10-Q, 20-F, 8-K, ...)")
    filed: date | None = Field(description="Filing date of the kept copy (the latest-filed one)")
    accn: str | None = Field(description="Accession number of the kept filing; joins to filings.accn")
    frame: str | None = Field(description="SEC calendar-period tag (e.g. CY2013Q3I, instant suffix I); set on one copy only, often NULL")


class ConceptsView(BaseModel):
    """Distinct XBRL concepts across the universe with their human label."""

    taxonomy: str = Field(description="XBRL taxonomy: us-gaap, ifrs-full, dei or srt")
    concept: str = Field(description="XBRL element name; joins to facts.concept")
    label: str | None = Field(description="Standard taxonomy label, e.g. 'Entity Common Stock, Shares Outstanding'")
    n_tickers: int = Field(description="Number of universe tickers that report this concept")


class SegmentsView(BaseModel):
    """Dimensional revenue/operating income parsed from each company's latest annual and later 10-Q XBRL."""

    ticker: str = Field(description="Universe ticker")
    cik: int = Field(description="Registrant CIK")
    accn: str = Field(description="Accession number of the filing parsed")
    form: str = Field(description="Filing form (10-K, 10-Q, 20-F, 40-F)")
    filing_date: date = Field(description="Filing date")
    period_start: date | None = Field(description="Start of the fact's reporting period")
    period_end: date | None = Field(description="End of the fact's reporting period")
    concept: str = Field(description="XBRL revenue (or operating income) concept; same company may use several")
    axis: str | None = Field(description="XBRL dimension, e.g. ProductOrServiceAxis, StatementGeographicalAxis; NULL = undimensioned total")
    member: str | None = Field(description="Member on `axis` (local name, e.g. DatacenterMember, country:TW); NULL for totals")
    value: float = Field(description="Reported amount in `unit`, full units (not thousands); multi-axis cross-tabs are not kept")
    is_custom_member: bool | None = Field(description="True when member is in the filer's own namespace (not comparable across companies); NULL for totals")
    unit: str | None = Field(description="Unit as an XBRL id; messy ('usd', 'U_CNY', 'Unit_Standard_USD_<hash>'): match with LIKE '%USD%' (unverified for non-USD)")


class Holdings13F(BaseModel):
    """13F-HR holdings, one row per (manager, period, cusip) for the effective filing."""

    cik: int = Field(description="Filing manager's CIK")
    mgr: str | None = Field(description="Manager name")
    period: date = Field(description="Report quarter-end the holdings are as of (filing is up to 45 days later)")
    cusip: str = Field(description="9-char CUSIP; join cusip_map.cusip to get a ticker (only mapped CUSIPs are universe names)")
    sh: float | None = Field(description="Shares held; only SH-type positions (PRN bond amounts excluded), puts/calls collapsed in")
    val: float | None = Field(description="Reported market value of the position; appears to be whole USD (val/sh is near share price) - unit unverified before 2023 rule change")
    acc: str | None = Field(description="Accession number of the 13F filing")


class CusipMap(BaseModel):
    """Mapping of universe tickers to 13F CUSIPs."""

    ticker: str = Field(description="Universe ticker")
    cusip: str | None = Field(description="9-char CUSIP; NULL when unmapped (e.g. some foreign listings)")
    method: str = Field(description="How matched: figi (OpenFIGI, filer-confirmed), figi_unverified, name (issuer-name match, weakest), unmapped")
    issuer: str | None = Field(description="Issuer name as printed on the 13F")
    figi_name: str | None = Field(description="Name returned by OpenFIGI; NULL if not matched via FIGI")


class FilingsView(BaseModel):
    """Every EDGAR filing for every universe CIK (current and predecessor)."""

    ticker: str = Field(description="Universe ticker")
    cik: int = Field(description="CIK the filing was filed under")
    is_predecessor: bool = Field(description="True when cik is a predecessor registrant (e.g. Tyco for JCI), not the current one")
    form: str = Field(description="EDGAR form type, e.g. 8-K, 10-K, 4, S-8, 424B3")
    filed: date = Field(description="Filing date")
    report_date: date | None = Field(description="Period or event date the filing reports on; NULL for many forms")
    accepted_at: datetime | None = Field(description="SEC acceptance timestamp, naive; EDGAR's acceptanceDateTime is UTC (unverified in-pipeline); use for intraday timing of releases")
    accn: str = Field(description="Accession number; unique per filing")
    primary_doc: str | None = Field(description="Primary document filename within the accession")
    description: str | None = Field(description="EDGAR primary-document description text")
    items: str | None = Field(description="Comma-separated 8-K item codes as listed by EDGAR; NULL for other forms")
    size: int | None = Field(description="Filing size in bytes as reported by EDGAR")
    is_xbrl: bool | None = Field(description="True when the filing carries XBRL")


class EventsView(BaseModel):
    """8-K / 8-K/A (and 6-K) filings exploded to one row per item code."""

    ticker: str = Field(description="Universe ticker")
    cik: int = Field(description="CIK the filing was filed under")
    is_predecessor: bool = Field(description="True for a predecessor registrant's filing")
    form: str = Field(description="8-K, 8-K/A or 6-K")
    filed: date = Field(description="Filing date")
    report_date: date | None = Field(description="Date of the reported event")
    accepted_at: datetime | None = Field(description="SEC acceptance timestamp, naive (EDGAR source is UTC, unverified)")
    accn: str = Field(description="Accession number; one filing yields several rows (one per item)")
    primary_doc: str | None = Field(description="Primary document filename")
    description: str | None = Field(description="EDGAR primary-document description")
    item: str | None = Field(description="8-K item code, e.g. 2.02 earnings, 5.02 officer change; NULL for 6-K (no items)")
    label: str | None = Field(description="Human label for the item code")
    signal: str | None = Field(description="Tier of likely price relevance: high, medium or low (5.02 is noisy)")


class InsiderTx(BaseModel):
    """Form 3/4/5 insider transaction lines, one per owner-deduplicated transaction row."""

    ticker: str = Field(description="Universe ticker of the issuer")
    issuer_cik: int | None = Field(description="Issuer CIK")
    accn: str = Field(description="Accession number of the Form 4/5")
    form: str = Field(description="4, 4/A, 5 or 5/A")
    filed: date = Field(description="Filing date (Form 4 is due 2 business days after trans_date)")
    period: date | None = Field(description="Period of report (transaction date of the event)")
    owner_cik: int | None = Field(description="Reporting owner CIK; lowest CIK when a filing has several owners")
    owner_name: str | None = Field(description="Reporting owner name (lowest-CIK owner when joint filing)")
    relationship: str | None = Field(description="Comma list of Director, Officer, TenPercentOwner, Other")
    officer_title: str | None = Field(description="Officer title if an officer, e.g. 'Chair, President & CEO'")
    n_owners: int | None = Field(description="Number of joint reporting owners on the filing; the row keeps only the lowest CIK")
    owner_names: str | None = Field(description="All owner names joined by '; '")
    kind: str = Field(description="nonderiv = common stock table, deriv = options/RSUs table")
    security_title: str | None = Field(description="Security, e.g. Common Stock, RSU Award")
    trans_date: date | None = Field(description="Transaction date (not the filing date)")
    code: str | None = Field(description="Form 4 transaction code: P open-market buy, S open-market sale, A grant, M option exercise, F tax withholding, G gift, C conversion, D to issuer. Only P/S are discretionary signal")
    shares: float | None = Field(description="Shares in the transaction (unsigned; direction is acquired_disposed)")
    price: float | None = Field(description="Price per share in USD; 0 for grants, exercises and many deriv rows")
    value: float | None = Field(description="shares * price in USD (derived, not reported); 0 when price is 0")
    acquired_disposed: str | None = Field(description="A = acquired, D = disposed")
    shares_owned_after: float | None = Field(description="Shares owned after this transaction")
    direct_indirect: str | None = Field(description="D = direct ownership, I = indirect (see nature)")
    nature: str | None = Field(description="Nature of indirect ownership (trust, spouse, ...); NULL if direct")
    is_10b5_1: bool | None = Field(description="Under a 10b5-1 plan: filing checkbox (post-2023 forms) OR footnote/remarks mention")
    plan_src: str | None = Field(description="Which signal set is_10b5_1: flag, footnote or both; NULL when not flagged")


class EarningsView(BaseModel):
    """Earnings press releases (EX-99.1 of item 2.02 8-Ks, or guessed 6-K) with extracted guidance."""

    ticker: str = Field(description="Universe ticker")
    cik: int = Field(description="CIK of the filer")
    accn: str = Field(description="Accession number of the 8-K/6-K")
    form: str = Field(description="8-K or 6-K")
    filed: date = Field(description="Filing date")
    doc_name: str | None = Field(description="Exhibit filename")
    method: str | None = Field(description="How the release was found: ex99.1, largest_ex99, guess_6k_text or guess_6k_desc (guess_* are heuristic)")
    text: str | None = Field(description="Release text converted from HTML; table rows are ' | ' joined")
    words: int | None = Field(description="Word count of text")
    guidance: list[str] | None = Field(description="Verbatim forward-guidance sentences/rows picked by regex rules; empty list when none found (~80% of rows have some)")
    headline: str | None = Field(description="JSON {revenue|eps_gaap|eps_nongaap: {value, unit, ccy, conf, snippet}}; conf high/med/low, rule-extracted so verify against snippet; eps GAAP vs non-GAAP can be mislabelled")


class AnnualReports(BaseModel):
    """One row per 10-K/10-KT/20-F/40-F with text-mining counts."""

    ticker: str = Field(description="Universe ticker")
    cik: int = Field(description="Filer CIK")
    accn: str = Field(description="Accession number; joins to report_sections/risk_diff/subsidiaries")
    form: str = Field(description="10-K, 10-KT, 20-F or 40-F")
    filed: date = Field(description="Filing date")
    fiscal_period_end: date | None = Field(description="Fiscal year end of the report")
    primary_doc: str | None = Field(description="Primary document filename")
    parse_ok: bool | None = Field(description="Sections were parsed; if false, counts are unreliable")
    parse_method: str | None = Field(description="items, items+fallback, fallback or 40f_exhibits")
    parse_error: str | None = Field(description="Parse error text; NULL when ok")
    doc_words: int | None = Field(description="Word count of the whole document")
    ai_mentions: int | None = Field(description="Total AI-term mentions in the document")
    ai_per_10k_words: float | None = Field(description="ai_mentions per 10,000 words (comparable across filings)")
    ai_term: int | None = Field(description="Count of the bare 'AI' term")
    artificial_intelligence: int | None = Field(description="Count of 'artificial intelligence'")
    machine_learning: int | None = Field(description="Count of 'machine learning'")
    generative: int | None = Field(description="Count of 'generative' mentions (generative AI)")
    patent_count: int | None = Field(description="Patent count; appears to be the largest patent figure parsed from text, e.g. 7,200 (unverified); see patent_sentences")
    patent_sentences: list[str] | None = Field(description="Sentences the patent count came from")
    risk_factor_count: int | None = Field(description="Number of risk-factor items detected")
    risk_sentences: int | None = Field(description="Number of sentences in the risk-factors section")
    prior_accn: str | None = Field(description="Previous year's annual-report accession used for risk_diff; NULL if none")
    risk_added: int | None = Field(description="Count of risk sentences new vs prior year (see risk_diff)")
    risk_removed: int | None = Field(description="Count of prior-year risk sentences dropped")
    ex21_doc: str | None = Field(description="Exhibit 21 (subsidiaries) filename; NULL if absent")
    subsidiary_count: int | None = Field(description="Number of subsidiaries parsed from Exhibit 21")


class ReportSections(BaseModel):
    """Extracted text sections of annual reports."""

    ticker: str = Field(description="Universe ticker")
    cik: int = Field(description="Filer CIK")
    accn: str = Field(description="Accession number; joins to annual_reports.accn")
    form: str = Field(description="10-K, 10-KT, 20-F or 40-F")
    fiscal_period_end: date | None = Field(description="Fiscal year end")
    section: str = Field(description="business, risk_factors, mda, market_risk or cybersecurity")
    text: str | None = Field(description="Section text")
    words: int | None = Field(description="Word count of text")
    parse_ok: bool | None = Field(description="Section extraction succeeded")


class RiskDiff(BaseModel):
    """Risk-factor sentences added or removed vs the prior annual report."""

    ticker: str = Field(description="Universe ticker")
    accn: str = Field(description="Current annual report accession")
    prior_accn: str = Field(description="Prior annual report accession compared against")
    kind: str = Field(description="added = new this year, removed = in prior year only")
    sentence: str = Field(description="The risk sentence (may start with a bullet char)")
    novelty: float = Field(description="Share of the sentence's shingles not in the other filing, 0.5-1.0 (threshold 0.5); 1.0 = fully new wording")


class Subsidiaries(BaseModel):
    """Exhibit 21 subsidiary list per annual report."""

    ticker: str = Field(description="Universe ticker")
    accn: str = Field(description="Annual report accession; joins to annual_reports.accn")
    subsidiary: str = Field(description="Subsidiary name as printed (may keep footnote markers like '(1)')")
    jurisdiction: str | None = Field(description="State/country of organisation")


class Profiles(BaseModel):
    """Yahoo company profile snapshot, one row per ticker."""

    ticker: str = Field(description="Universe ticker (foreign listings carry suffixes, e.g. 005930.KS)")
    long_name: str | None = Field(description="Full company name")
    short_name: str | None = Field(description="Yahoo short name")
    sector: str | None = Field(description="Yahoo sector")
    industry: str | None = Field(description="Yahoo industry")
    country: str | None = Field(description="HQ country")
    website: str | None = Field(description="Company website URL")
    domain: str | None = Field(description="Website domain")
    employees: int | None = Field(description="Full-time employees")
    market_cap: int | None = Field(description="Market cap in `currency` units at snapshot time (not USD for KRW/JPY/TWD names)")
    currency: str | None = Field(description="Currency of market_cap: USD, KRW, JPY, TWD")
    summary: str | None = Field(description="Business summary text")
    officers: str | None = Field(description="JSON list of officers with name and title")


class Patents(BaseModel):
    """USPTO granted patents (PatentsView), all assignees, through 2025."""

    patent_id: str = Field(description="Patent number as string (design/plant types have prefixes)")
    date: _Date | None = Field(description="Grant date")
    title: str | None = Field(description="Patent title")
    type: str | None = Field(description="utility, design, reissue, plant, defensive publication or statutory invention registration")
    num_claims: int | None = Field(description="Number of claims")
    filing_date: _Date | None = Field(description="Application filing date (grants lag filing by 18+ months)")
    application_id: str | None = Field(description="USPTO application number")


class PatentTicker(BaseModel):
    """Patent to ticker link (a patent can have several co-assignee tickers)."""

    patent_id: str = Field(description="Joins to patents.patent_id")
    ticker: str = Field(description="Universe ticker that currently owns the assignee (incl. acquired subsidiaries)")
    matched_on: str = Field(description="raw = assignee name as printed on the patent; cluster = PatentsView disambiguated label (fallback)")


class PatentCpc(BaseModel):
    """CPC classifications per patent."""

    patent_id: str = Field(description="Joins to patents.patent_id")
    cpc_sequence: int | None = Field(description="Order of the CPC code on the patent (0-based)")
    cpc_group: str | None = Field(description="Full CPC group, e.g. H01L2924/12036")
    cpc_subclass: str | None = Field(description="CPC subclass (4 chars), e.g. H01L; use for technology mix")
    cpc_type: str | None = Field(description="inventional (core) or additional (indexing) code")


class PatentWipo(BaseModel):
    """WIPO technology field per patent."""

    patent_id: str = Field(description="Joins to patents.patent_id")
    wipo_sector_title: str | None = Field(description="WIPO technology sector")
    wipo_field_title: str | None = Field(description="WIPO technology field")


class PatentInventors(BaseModel):
    """Inventors per patent."""

    patent_id: str = Field(description="Joins to patents.patent_id")
    inventor_id: str | None = Field(description="PatentsView disambiguated inventor id")
    name: str | None = Field(description="Inventor name")


class PatentAssignees(BaseModel):
    """Assignee-name to ticker matching table with provenance."""

    kind: str = Field(description="raw = name as printed on patents; cluster = PatentsView disambiguated organisation")
    org: str = Field(description="Assignee organisation name")
    ticker: str = Field(description="Ticker the org was matched to")
    via: str = Field(description="Match source: sec_name, sec_former, ex21 (subsidiary list), yahoo (profile name) or manual")
    n_patents: int | None = Field(description="Patents assigned to this org name (a patent counted under raw and cluster rows separately)")


class PatentAi(BaseModel):
    """AI classification of each granted utility/reissue patent (USPTO AIPD)."""

    patent_id: str = Field(description="Joins to patents.patent_id")
    pub_dt: date | None = Field(description="Publication (grant) date")
    any_ai: bool | None = Field(description="Any AI category at the generous predict50 threshold; over-counts, prefer any_ai93")
    any_ai93: bool | None = Field(description="Any AI category at the strict predict93 threshold; use for 'real AI' share")
    ml: bool | None = Field(description="Machine-learning category flag (threshold per patents_ai.py, unverified)")
    ml_score: float | None = Field(description="Model probability 0-1 for machine learning")
    evo: bool | None = Field(description="Evolutionary computation flag")
    evo_score: float | None = Field(description="Model probability 0-1 for evolutionary computation")
    nlp: bool | None = Field(description="Natural-language-processing flag")
    nlp_score: float | None = Field(description="Model probability 0-1 for NLP")
    speech: bool | None = Field(description="Speech flag")
    speech_score: float | None = Field(description="Model probability 0-1 for speech")
    vision: bool | None = Field(description="Computer-vision flag")
    vision_score: float | None = Field(description="Model probability 0-1 for vision")
    planning: bool | None = Field(description="AI planning/control flag")
    planning_score: float | None = Field(description="Model probability 0-1 for planning")
    kr: bool | None = Field(description="Knowledge-representation/reasoning flag")
    kr_score: float | None = Field(description="Model probability 0-1 for knowledge representation")
    hardware: bool | None = Field(description="AI hardware flag")
    hardware_score: float | None = Field(description="Model probability 0-1 for AI hardware")


class PatentAiByTickerYear(BaseModel):
    """AI patent counts per ticker and grant year."""

    ticker: str = Field(description="Universe ticker")
    year: int = Field(description="Grant year")
    n_patents: int = Field(description="Grants with AIPD coverage (utility+reissue) matched to the ticker; the pct denominators")
    n_ai_any: int = Field(description="Patents with any_ai (predict50, generous)")
    pct_ai: float = Field(description="100 * n_ai_any / n_patents (percent, not fraction)")
    n_ai93: int = Field(description="Patents with any_ai93 (strict)")
    pct_ai93: float = Field(description="100 * n_ai93 / n_patents (percent)")
    n_ml: int = Field(description="Patents flagged machine learning")
    n_evo: int = Field(description="Patents flagged evolutionary computation")
    n_nlp: int = Field(description="Patents flagged NLP")
    n_speech: int = Field(description="Patents flagged speech")
    n_vision: int = Field(description="Patents flagged vision")
    n_planning: int = Field(description="Patents flagged planning")
    n_kr: int = Field(description="Patents flagged knowledge representation")
    n_hardware: int = Field(description="Patents flagged AI hardware; categories overlap, do not sum")


class Quotes1m(BaseModel):
    """Databento XNAS.BASIC cbbo-1m: consolidated best bid/ask sampled each minute."""

    ts_recv: datetime = Field(description="Databento receive time, UTC-aware")
    ts_event: datetime = Field(description="Minute-bar timestamp (end of the 1-minute interval), UTC-aware; convert to ET")
    side: str | None = Field(description="Side of the last trade in the interval; only 'N' (none) seen")
    price: float | None = Field(description="Last trade price in the interval, USD")
    size: int | None = Field(description="Last trade size, shares")
    flags: int | None = Field(description="Databento record flags bitfield")
    bid_px_00: float | None = Field(description="Best bid price at interval end, USD; NULL if no bid")
    ask_px_00: float | None = Field(description="Best ask price at interval end, USD")
    bid_sz_00: int | None = Field(description="Size at best bid (shares; often round lots, unit unverified)")
    ask_sz_00: int | None = Field(description="Size at best ask")
    bid_pb_00: int | None = Field(description="Publisher id of the venue posting the best bid")
    ask_pb_00: int | None = Field(description="Publisher id of the venue posting the best ask")
    symbol: str = Field(description="Ticker")


class TweetsView(BaseModel):
    """Tweets from followed research accounts."""

    id: str = Field(description="Tweet id (string; exceeds float precision)")
    handle: str = Field(description="Author handle without @")
    author_name: str | None = Field(description="Author display name")
    author_followers: int | None = Field(description="Author follower count at pull time")
    created_at: datetime = Field(description="Post time, naive UTC (converted from the API's timestamp)")
    text: str | None = Field(description="Tweet text")
    type: str | None = Field(description="tweet or reply")
    is_reply: bool | None = Field(description="Reply to another tweet")
    is_retweet: bool | None = Field(description="Retweet")
    is_quote: bool | None = Field(description="Quote tweet")
    reply_to: str | None = Field(description="Tweet id or handle replied to; NULL if not a reply (unverified which)")
    conversation_id: str | None = Field(description="Id of the thread's root tweet")
    likes: int | None = Field(description="Likes at pull time")
    retweets: int | None = Field(description="Retweets at pull time")
    replies: int | None = Field(description="Replies at pull time")
    quotes: int | None = Field(description="Quote tweets at pull time")
    views: int | None = Field(description="View count at pull time")
    bookmarks: int | None = Field(description="Bookmarks at pull time")
    media_count: int | None = Field(description="Attached media items")
    urls: str | None = Field(description="JSON list of URLs in the tweet")
    url: str | None = Field(description="Permalink on x.com")
    lang: str | None = Field(description="Language code")


class TweetTickers(BaseModel):
    """Cashtag mentions: one row per (tweet, ticker)."""

    tweet_id: str = Field(description="Joins to tweets.id")
    handle: str = Field(description="Author handle")
    created_at: datetime = Field(description="Tweet time, naive UTC")
    ticker: str = Field(description="Ticker from a $cashtag, upper-case")
    in_universe: bool = Field(description="True when ticker is in universe; false rows are other symbols")
