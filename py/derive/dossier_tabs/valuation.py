"""Dossier tab: Valuation. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Replaces the old `estimates` section (derive/dossier.py estimates_), which is kept there until the lead removes it.
Live Yahoo quoteSummary for the consensus, multiples, cash flow, estimate tables, dispersion, revisions and the
surprise history; tweet-extracted price targets from derive/sentiment.py (local store). Every value has a src: a
Yahoo page (url) or a derived(formula, inputs). Missing data drops the row or block, never the tab.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from urllib.parse import quote

from derive.dossier import _is_new, _money, _pct, derived, src
from sources import yahoo, yahoo_profile

MODULES = ("earningsTrend,earningsHistory,recommendationTrend,upgradeDowngradeHistory,financialData,"
           "defaultKeyStatistics,summaryDetail,price")
EST_PERIODS = {"0q": "Current quarter", "+1q": "Next quarter", "0y": "Current year", "+1y": "Next year",
               "+5y": "Next 5 years (p.a.)"}
PAGES = {"analysis": "Yahoo Finance analysis", "key-statistics": "Yahoo Finance key statistics",
         "financials": "Yahoo Finance financials", "balance-sheet": "Yahoo Finance balance sheet",
         "cash-flow": "Yahoo Finance cash flow"}
MULTIPLES = [  # label, [(module, field) candidates, first present wins], Yahoo page, format
    ("Trailing P/E", [("summaryDetail", "trailingPE")], "key-statistics", "{:.1f}x"),
    ("Forward P/E", [("summaryDetail", "forwardPE"), ("defaultKeyStatistics", "forwardPE")], "key-statistics", "{:.1f}x"),
    ("PEG", [("defaultKeyStatistics", "pegRatio")], "key-statistics", "{:.2f}"),
    ("P/S (TTM)", [("summaryDetail", "priceToSalesTrailing12Months")], "key-statistics", "{:.1f}x"),
    ("P/B", [("defaultKeyStatistics", "priceToBook")], "key-statistics", "{:.1f}x"),
    ("EV / sales", [("defaultKeyStatistics", "enterpriseToRevenue")], "key-statistics", "{:.1f}x"),
    ("EV / EBITDA", [("defaultKeyStatistics", "enterpriseToEbitda")], "key-statistics", "{:.1f}x"),
]
AMOUNTS = [  # label, (module, field), Yahoo page, currency basis: "px" = quote currency, "fin" = reporting currency
    ("Enterprise value", ("defaultKeyStatistics", "enterpriseValue"), "key-statistics", "px"),
    ("EBITDA (TTM)", ("financialData", "ebitda"), "financials", "fin"),
    ("Free cash flow (TTM)", ("financialData", "freeCashflow"), "cash-flow", "fin"),
    ("Total cash", ("financialData", "totalCash"), "balance-sheet", "fin"),
    ("Total debt", ("financialData", "totalDebt"), "balance-sheet", "fin"),
]
TARGET_DAYS = 180
TARGET_LIMIT = 100
LISTING_CASHTAGS = 3  # a post naming this many other $tickers is a list or a comparison: its price is not this stock's


# ---- small helpers -----------------------------------------------------------

def _raw(f):
    return f.get("raw") if isinstance(f, dict) else f


def _n(v, fmt: str = "{:,.2f}") -> str:
    return "—" if v is None else fmt.format(v)


def _amt(v, ccy: str | None) -> str:
    """Money in the given currency: $ for USD, the ISO code otherwise (never a bare $ on a KRW number)."""
    s = _money(v)
    if v is None or not ccy or ccy == "USD":
        return s
    return s.replace("$", f"{ccy} ", 1)


def _px(v: float, ccy: str | None) -> str:
    """A per-share price: $ for USD, the ISO code otherwise."""
    return f"${v:,.2f}" if not ccy or ccy == "USD" else f"{ccy} {v:,.2f}"


def _page(t: str, page: str) -> str:
    return f"https://finance.yahoo.com/quote/{quote(t)}/{page}/"


def _first(res: dict, cands: list[tuple[str, str]]) -> tuple:
    """(value, module, field) of the first candidate with a value, else (None, None, None)."""
    for mod, field in cands:
        v = _raw((res.get(mod) or {}).get(field))
        if v is not None:
            return v, mod, field
    return None, None, None


def _fetch(t: str) -> dict | None:
    """One quoteSummary call for every module the tab reads. Fail-soft: any error means no Yahoo blocks."""
    try:
        return yahoo_profile.fetch(yahoo.new_session(), t, MODULES)
    except Exception:
        return None


# ---- Yahoo blocks -------------------------------------------------------------

def _pfcf(price, shares, fcf, px_ccy, fin_ccy, srcs: dict) -> dict | None:
    """Price / free cash flow = market cap / FCF, with market cap = currentPrice x sharesOutstanding (the same
    currentPrice the consensus upside uses). Not computed when a value is missing; when the quote and the cash flow
    are in different currencies (ADRs reporting in local currency) the row says so instead of mixing units."""
    if price is None or shares is None or fcf is None:
        return None
    inputs = [srcs["price"], srcs["shares"], srcs["fcf"]]
    if px_ccy != fin_ccy:
        return {"label": "Price / free cash flow", "value": f"n/a: quote in {px_ccy}, cash flow in {fin_ccy}",
                "src": derived("P/FCF not computed: currencies differ", f"quote {px_ccy} vs cash flow {fin_ccy}", inputs)}
    mcap = price * shares
    if fcf <= 0:
        return {"label": "Price / free cash flow", "value": "n/m (FCF ≤ 0)",
                "src": derived("Price / free cash flow", f"FCF {fcf:,.0f} ≤ 0, ratio not meaningful", inputs)}
    ratio = mcap / fcf
    return {"label": "Price / free cash flow", "value": f"{ratio:.1f}x", "src": derived(
        "Price / free cash flow",
        f"market cap ({price:,.2f} × {shares:,.0f}) = {mcap:,.0f}; {mcap:,.0f} / {fcf:,.0f} = {ratio:.1f}x", inputs)}


def _dispersion_row(name: str, metric: str, avg, low, high, fmt, nf: str, ys: dict) -> dict | None:
    """(high - low) and (high - low) / |avg| for one period. fmt renders a value for the cells, nf is the number
    format of the formula; ys holds the Yahoo src of avg, low and high."""
    if avg is None or low is None or high is None or not avg:
        return None
    w = high - low
    pct = w / abs(avg) * 100
    return {"cells": [f"{metric} · {name}", fmt(avg), fmt(w), f"{pct:.1f}%"], "src": derived(
        f"{metric} dispersion, {name}",
        f"({nf.format(high)} − {nf.format(low)}) = {nf.format(w)}; {nf.format(w)} / |{nf.format(avg)}| × 100 = {pct:.1f}%",
        [ys["high"], ys["low"], ys["avg"]])}


def _estimate_blocks(res: dict, y, fin_ccy: str | None) -> list[dict]:
    blocks = []
    trend = {p["period"]: p for p in (res.get("earningsTrend") or {}).get("trend", []) if p.get("period") in EST_PERIODS}
    eps_rows, rev_rows, rev_trend_rows, disp_rows, rev_count_rows = [], [], [], [], []
    money = lambda v: _amt(v, fin_ccy)  # noqa: E731
    for per, label in EST_PERIODS.items():
        p = trend.get(per)
        if not p:
            continue
        e, r, tr = p.get("earningsEstimate") or {}, p.get("revenueEstimate") or {}, p.get("epsTrend") or {}
        rv = p.get("epsRevisions") or {}
        name = f"{label} (ends {p['endDate']})" if p.get("endDate") else label
        if _raw(e.get("avg")) is not None:
            eps_rows.append({"cells": [name, _n(_raw(e.get("avg"))), _n(_raw(e.get("low"))), _n(_raw(e.get("high"))),
                                       _n(_raw(e.get("yearAgoEps"))), _pct(_raw(e.get("growth")) * 100 if _raw(e.get("growth")) is not None else None),
                                       _n(_raw(e.get("numberOfAnalysts")), "{:.0f}")],
                             "src": y(f"earningsTrend[{per}].earningsEstimate")})
            d = _dispersion_row(name, "EPS", _raw(e.get("avg")), _raw(e.get("low")), _raw(e.get("high")), _n, "{:,.2f}", {
                "avg": y(f"earningsTrend[{per}].earningsEstimate.avg"), "low": y(f"earningsTrend[{per}].earningsEstimate.low"),
                "high": y(f"earningsTrend[{per}].earningsEstimate.high")})
            if d:
                disp_rows.append(d)
        if _raw(r.get("avg")) is not None:
            rev_rows.append({"cells": [name, money(_raw(r.get("avg"))), money(_raw(r.get("low"))), money(_raw(r.get("high"))),
                                       money(_raw(r.get("yearAgoRevenue"))), _pct(_raw(r.get("growth")) * 100 if _raw(r.get("growth")) is not None else None),
                                       _n(_raw(r.get("numberOfAnalysts")), "{:.0f}")],
                             "src": y(f"earningsTrend[{per}].revenueEstimate")})
            d = _dispersion_row(name, "Revenue", _raw(r.get("avg")), _raw(r.get("low")), _raw(r.get("high")), money, "{:,.0f}", {
                "avg": y(f"earningsTrend[{per}].revenueEstimate.avg"), "low": y(f"earningsTrend[{per}].revenueEstimate.low"),
                "high": y(f"earningsTrend[{per}].revenueEstimate.high")})
            if d:
                disp_rows.append(d)
        cur = _raw(tr.get("current"))
        if cur is not None:
            cells, ago_srcs = [name, _n(cur)], []
            for k, days in (("7daysAgo", 7), ("30daysAgo", 30), ("90daysAgo", 90)):
                ago = _raw(tr.get(k))
                if ago:
                    ch = (cur - ago) / abs(ago) * 100
                    cells.append(f"{_n(ago)} ({ch:+.1f}%)")
                    ago_srcs.append(derived(f"{label} EPS estimate revision, {days}d",
                                            f"({cur:,.2f} − {ago:,.2f}) / |{ago:,.2f}| × 100 = {ch:+.1f}%",
                                            [y(f"earningsTrend[{per}].epsTrend.current"), y(f"earningsTrend[{per}].epsTrend.{k}")]))
                else:
                    cells.append("—")
            rev_trend_rows.append({"cells": cells, "src": ago_srcs[0] if ago_srcs else y(f"earningsTrend[{per}].epsTrend")})
        # analyst counts of EPS estimates raised / cut over the last 7 and 30 days
        counts = [_raw(rv.get("upLast7days")), _raw(rv.get("downLast7Days", rv.get("downLast7days"))),
                  _raw(rv.get("upLast30days")), _raw(rv.get("downLast30days"))]
        if any(c is not None for c in counts):
            rev_count_rows.append({"cells": [name, *("—" if c is None else f"{c:.0f}" for c in counts)],
                                   "src": y(f"earningsTrend[{per}].epsRevisions")})

    if eps_rows:
        blocks.append({"type": "table", "title": f"EPS estimates ({fin_ccy or 'per share'})", "cols": ["period", "avg", "low", "high", "year ago", "growth", "analysts"], "rows": eps_rows})
    if rev_rows:
        blocks.append({"type": "table", "title": "Revenue estimates", "cols": ["period", "avg", "low", "high", "year ago", "growth", "analysts"], "rows": rev_rows})
    if disp_rows:
        blocks.append({"type": "table", "title": "Estimate dispersion (high − low, and as % of avg)",
                       "cols": ["period", "avg", "high − low", "(high − low) / |avg|"], "rows": disp_rows})
    if rev_count_rows:
        blocks.append({"type": "table", "title": "EPS estimate revisions (analysts raising / cutting)",
                       "cols": ["period", "up 7d", "down 7d", "up 30d", "down 30d"], "rows": rev_count_rows})
    if rev_trend_rows:
        blocks.append({"type": "table", "title": "EPS estimate revisions (change since)",
                       "cols": ["period", "now", "7d ago", "30d ago", "90d ago"], "rows": rev_trend_rows})
    return blocks


def _yahoo_blocks(t: str, res: dict) -> list[dict]:
    y = lambda path, page="analysis": src(f"{PAGES[page]} · {path}", _page(t, page))  # noqa: E731
    fd, dks, sd = res.get("financialData") or {}, res.get("defaultKeyStatistics") or {}, res.get("summaryDetail") or {}
    px_ccy = (res.get("price") or {}).get("currency") or sd.get("currency")
    fin_ccy = _raw(fd.get("financialCurrency")) or px_ccy
    blocks = []

    # consensus (kept from the old section)
    price, mean_t = _raw(fd.get("currentPrice")), _raw(fd.get("targetMeanPrice"))
    kv = []
    if fd.get("recommendationKey"):
        kv.append({"label": "Consensus rating", "value": f"{fd['recommendationKey']} "
                   f"(mean {_n(_raw(fd.get('recommendationMean')), '{:.2f}')} of 5, "
                   f"{_n(_raw(fd.get('numberOfAnalystOpinions')), '{:.0f}')} analysts)",
                   "src": y("financialData.recommendationKey")})
    for key, label in (("targetLowPrice", "Target low"), ("targetMeanPrice", "Target mean"),
                       ("targetMedianPrice", "Target median"), ("targetHighPrice", "Target high")):
        if _raw(fd.get(key)) is not None:
            kv.append({"label": label, "value": _px(_raw(fd[key]), px_ccy), "src": y(f"financialData.{key}")})
    if price and mean_t:
        up = (mean_t / price - 1) * 100
        kv.append({"label": "Upside to mean target", "value": _pct(up), "src": derived(
            "Upside to mean analyst target", f"({mean_t:,.2f} / {price:,.2f} − 1) × 100 = {up:+.1f}%",
            [y("financialData.targetMeanPrice"), y("financialData.currentPrice")])})
    if kv:
        blocks.append({"type": "kv", "title": "Consensus", "rows": kv})

    # multiples
    rows = []
    for label, cands, page, fmt in MULTIPLES:
        v, mod, field = _first(res, cands)
        if v is not None:
            rows.append({"label": label, "value": fmt.format(v), "src": y(f"{mod}.{field}", page)})
    pf = _pfcf(price, _raw(dks.get("sharesOutstanding")), _raw(fd.get("freeCashflow")), px_ccy, fin_ccy, {
        "price": y("financialData.currentPrice"), "shares": y("defaultKeyStatistics.sharesOutstanding", "key-statistics"),
        "fcf": y("financialData.freeCashflow", "cash-flow")})
    if pf:
        rows.append(pf)
    if rows:
        blocks.append({"type": "kv", "title": "Multiples", "rows": rows})

    # enterprise value, EBITDA, cash flow, balance sheet
    rows = []
    for label, (mod, field), page, basis in AMOUNTS:
        v = _raw((res.get(mod) or {}).get(field))
        if v is not None:
            rows.append({"label": label, "value": _amt(v, px_ccy if basis == "px" else fin_ccy), "src": y(f"{mod}.{field}", page)})
    if rows:
        blocks.append({"type": "kv", "title": "Enterprise value and cash", "rows": rows})

    blocks += _estimate_blocks(res, y, fin_ccy)

    # earnings surprises
    hist = [h for h in (res.get("earningsHistory") or {}).get("history", []) if _raw(h.get("epsActual")) is not None]
    if hist:
        blocks.append({"type": "table", "title": "EPS vs estimate, last quarters", "cols": ["quarter", "actual", "estimate", "surprise"],
                       "rows": [{"cells": [(h.get("quarter") or {}).get("fmt") or "?", _n(_raw(h.get("epsActual"))), _n(_raw(h.get("epsEstimate"))),
                                           _pct(_raw(h.get("surprisePercent")) * 100 if _raw(h.get("surprisePercent")) is not None else None)],
                                 "src": y("earningsHistory")} for h in hist]})

    # rating mix and recent rating changes
    rt = (res.get("recommendationTrend") or {}).get("trend", [])
    if rt:
        blocks.append({"type": "table", "title": "Rating mix by month", "cols": ["month", "strong buy", "buy", "hold", "sell", "strong sell"],
                       "rows": [{"cells": [{"0m": "This month", "-1m": "Last month", "-2m": "2 months ago", "-3m": "3 months ago"}.get(r.get("period"), r.get("period") or "?"),
                                           *(str(r.get(k, 0)) for k in ("strongBuy", "buy", "hold", "sell", "strongSell"))],
                                 "src": y(f"recommendationTrend[{r.get('period')}]")} for r in rt]})

    ud = sorted((res.get("upgradeDowngradeHistory") or {}).get("history", []), key=lambda h: h.get("epochGradeDate") or 0, reverse=True)[:12]
    if ud:
        blocks.append({"type": "table", "title": "Recent rating changes", "cols": ["date", "firm", "action", "from", "to"],
                       "rows": [{"cells": [datetime.fromtimestamp(h["epochGradeDate"]).date().isoformat() if h.get("epochGradeDate") else "?",
                                           h.get("firm") or "?", h.get("action") or "?", h.get("fromGrade") or "—", h.get("toGrade") or "—"],
                                 "new": _is_new(datetime.fromtimestamp(h["epochGradeDate"]).date()) if h.get("epochGradeDate") else False,
                                 "src": y("upgradeDowngradeHistory")} for h in ud]})
    return blocks


# ---- tweet price targets --------------------------------------------------------

def _is_listing(text: str | None, t: str) -> bool:
    """True for posts that name several other tickers (fib-level lists, comparisons): a price there belongs to
    one of the other names, not to t."""
    other = {c.upper() for c in re.findall(r"\$[A-Za-z]{1,6}\b", text or "")} - {f"${t.upper()}"}
    return len(other) >= LISTING_CASHTAGS


def _target_blocks(t: str, pt: dict | None) -> list[dict]:
    """Price targets from tweets (derive/sentiment.price_targets), kept to rows where the author holds a view on
    this stock (view_holder not none): a price in a tweet listing several tickers is often another ticker's."""
    if not pt:
        return []
    close = (pt.get("summary") or {}).get("last_close")
    rows = [r for r in pt.get("targets") or [] if r.get("url") and r.get("price_target") and r.get("view_holder") != "none"
            and not _is_listing(r.get("text"), t)]
    if not rows:
        return []
    prices = sorted(float(r["price_target"]) for r in rows)
    n = len(prices)
    median = prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) / 2
    low, high = prices[0], prices[-1]
    authors = len({r.get("handle") for r in rows})
    tsrc = lambda r: src(f"tweet by {r.get('handle')} · {str(r.get('date'))[:10]}", r["url"])  # noqa: E731
    srcs = [tsrc(r) for r in rows]
    med_src = derived("Median tweet price target", f"median of {n} targets = {median:,.2f}", srcs)
    kv = [
        {"label": "Tweet price targets", "value": f"{n} targets · {authors} authors (last {TARGET_DAYS} days)",
         "src": derived("Tweet price targets, count", f"{n} tweets, last {TARGET_DAYS} days, author holds a view, with a price target",
                        srcs)},
        {"label": "Median target", "value": f"${median:,.2f}", "src": med_src},
        {"label": "Range", "value": f"${low:,.2f} – ${high:,.2f}", "src": derived(
            "Tweet target range", f"min {low:,.2f} to max {high:,.2f} over {n} targets", srcs)},
    ]
    if close:
        up = (median / close - 1) * 100
        close_src = src("last daily close, bars_1d (Databento, local snapshot)", _page(t, "history"))
        kv.append({"label": "Last close", "value": f"${close:,.2f}", "src": close_src})
        kv.append({"label": "Median target vs last close", "value": _pct(up), "src": derived(
            "Median tweet target vs last close", f"({median:,.2f} / {close:,.2f} − 1) × 100 = {up:+.1f}%", [med_src, close_src])})
    rows_tbl = []
    for r in rows:
        cells = [str(r.get("date"))[:10], f"@{r.get('handle')}", f"${float(r['price_target']):,.2f}",
                 _pct(r["implied_upside_pct"]) if r.get("implied_upside_pct") is not None else "—",
                 (r.get("text") or "").replace("\n", " ")[:140]]
        rows_tbl.append({"cells": cells, "new": _is_new(str(r.get("date"))[:10]), "src": tsrc(r)})
    return [
        {"type": "kv", "title": "Price targets in tweets", "rows": kv},
        {"type": "table", "title": "Tweet price targets, listed", "cols": ["date", "author", "target", "vs last close", "tweet"],
         "rows": rows_tbl},
    ]


def _tweet_blocks(t: str, px_ccy: str | None) -> list[dict]:
    if px_ccy != "USD":  # the targets are written in the listing's currency: skip non-USD names rather than mix units
        return []
    try:
        from derive import sentiment  # lazy: the store is only read here
        since = (date.today() - timedelta(days=TARGET_DAYS)).isoformat()
        return _target_blocks(t, sentiment.price_targets(t, since=since, limit=TARGET_LIMIT))
    except Exception:
        return []


# ---- entry point ------------------------------------------------------------------

def section(t: str, con, F, prof: dict | None) -> dict | None:
    res = _fetch(t)
    px_ccy = ((res or {}).get("price") or {}).get("currency") or (prof or {}).get("currency")
    blocks = (_yahoo_blocks(t, res) if res else []) + _tweet_blocks(t, px_ccy)
    return {"id": "valuation", "title": "Valuation", "blocks": blocks} if blocks else None
