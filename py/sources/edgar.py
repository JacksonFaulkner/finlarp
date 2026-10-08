"""SEC EDGAR data client — raw filed XBRL financials (companyfacts API).

Free, no API key, but SEC requires a descriptive User-Agent with contact
info on every request or it 403s. Used to get real filed quarterly revenue
(Yahoo's earningsHistory has no revenue-vs-estimate equivalent) and
multi-year annual EPS/revenue — richer than Yahoo's condensed summaries
for the CANSLIM C/A letters.
"""
from __future__ import annotations

import sys
from datetime import date

from core import db
from sources import sec_http

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# XBRL concept tags to try in order — companies vary in which one they tag
# revenue under.
REVENUE_CONCEPTS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    # CRWD, NEE, AKAM, VRNS and others tag revenue only with this one.
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
]
EPS_CONCEPTS = ["EarningsPerShareDiluted", "EarningsPerShareBasic"]
NET_INCOME_CONCEPTS = ["NetIncomeLoss"]


def ticker_to_cik(symbol: str) -> int | None:
    cik_map = db.get_cached_edgar_cik_map()
    if cik_map is None:
        resp = sec_http.get(TICKERS_URL, timeout=15)
        resp.raise_for_status()
        cik_map = {v["ticker"].upper(): v["cik_str"] for v in resp.json().values()}
        db.put_cached_edgar_cik_map(cik_map)
    return cik_map.get(symbol.upper())


def get_company_facts(symbol: str, use_cache: bool = True) -> dict | None:
    if use_cache:
        cached = db.get_cached_edgar_facts(symbol)
        if cached is not None:
            return cached

    cik = ticker_to_cik(symbol)
    if cik is None:
        return None
    resp = sec_http.get(FACTS_URL.format(cik=cik), timeout=15)
    if resp.status_code != 200:
        return None
    facts = resp.json()
    db.put_cached_edgar_facts(symbol, facts)
    return facts


def _duration_days(entry: dict) -> int | None:
    try:
        return (date.fromisoformat(entry["end"]) - date.fromisoformat(entry["start"])).days
    except (KeyError, ValueError):
        return None


def _single_quarter_series(facts: dict, concepts: list[str]) -> list[dict]:
    """Last 8 single-quarter (not YTD-cumulative) filed values for the
    first matching concept tag, deduped by period end date (a later
    amended filing for the same quarter wins). Of the concepts, the one
    with the most recent period wins: filers switch tags (NVDA moved from
    Revenues to RevenueFromContractWithCustomer...), and the first tag with
    any data can be years stale.

    Q4 has no 10-Q, so it's taken from a 3-month fact in the 10-K when the
    filer tags one, else derived as FY - (Q1+Q2+Q3) and marked derived=True.
    Without it the latest quarter would stay Q3 for ~3 months after every
    10-K, and Q1's YoY/QoQ would compare against the wrong quarter."""
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    best: list[dict] = []
    for concept in concepts:
        node = us_gaap.get(concept)
        if not node:
            continue
        entries = node.get("units", {}).get("USD") or []
        quarters = [
            e for e in entries
            if e.get("form", "").startswith(("10-Q", "10-K")) and 80 <= (_duration_days(e) or 0) <= 100
        ]
        by_end: dict[str, dict] = {}
        for e in quarters:
            by_end[e["end"]] = e  # last one wins — later filings supersede
        annual = [e for e in entries if e.get("form", "").startswith("10-K") and 350 <= (_duration_days(e) or 0) <= 380]
        for fy in annual:
            if fy["end"] in by_end:
                continue
            inside = [q for q in by_end.values() if fy["start"] <= q["start"] and q["end"] < fy["end"]]
            if len(inside) == 3:
                by_end[fy["end"]] = fy | {
                    "start": max(q["end"] for q in inside),
                    "val": fy["val"] - sum(q["val"] for q in inside),
                    "derived": True,
                }
        rows = sorted(by_end.values(), key=lambda e: e["end"])
        if rows and (not best or rows[-1]["end"] > best[-1]["end"]):
            best = rows[-8:]
    return best


def _annual_series(facts: dict, concepts: list[str], unit: str) -> list[dict]:
    """Last 4 fiscal-year (10-K, ~360-370 day duration for EPS/revenue
    which are duration concepts) filed values, from the freshest concept
    (see _single_quarter_series)."""
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    best: list[dict] = []
    for concept in concepts:
        node = us_gaap.get(concept)
        if not node:
            continue
        entries = node.get("units", {}).get(unit) or []
        annual = [
            e for e in entries
            if e.get("form", "").startswith("10-K") and 350 <= (_duration_days(e) or 0) <= 380
        ]
        by_end: dict[str, dict] = {}
        for e in annual:
            by_end[e["end"]] = e
        rows = sorted(by_end.values(), key=lambda e: e["end"])
        if rows and (not best or rows[-1]["end"] > best[-1]["end"]):
            best = rows[-4:]
    return best


def get_quarterly_revenue(symbol: str) -> list[dict]:
    """[{quarter_end, revenue}, ...] oldest -> newest, up to 8 quarters."""
    facts = get_company_facts(symbol)
    if not facts:
        return []
    rows = _single_quarter_series(facts, REVENUE_CONCEPTS)
    return [{"quarter_end": r["end"], "revenue": r["val"]} for r in rows]


def get_quarterly_net_income(symbol: str) -> list[dict]:
    """[{quarter_end, net_income}, ...] oldest -> newest, up to 8 quarters —
    same NetIncomeLoss tag every filer uses, so this is a cheap add next to
    revenue rather than a new data source."""
    facts = get_company_facts(symbol)
    if not facts:
        return []
    rows = _single_quarter_series(facts, NET_INCOME_CONCEPTS)
    return [{"quarter_end": r["end"], "net_income": r["val"]} for r in rows]


def get_annual_series(symbol: str) -> list[dict]:
    """[{fiscal_year_end, eps, revenue}, ...] oldest -> newest, up to 4 years."""
    facts = get_company_facts(symbol)
    if not facts:
        return []
    eps_rows = {r["end"]: r["val"] for r in _annual_series(facts, EPS_CONCEPTS, "USD/shares")}
    rev_rows = {r["end"]: r["val"] for r in _annual_series(facts, REVENUE_CONCEPTS, "USD")}
    ends = sorted(set(eps_rows) | set(rev_rows))
    return [
        {"fiscal_year_end": end, "eps": eps_rows.get(end), "revenue": rev_rows.get(end)}
        for end in ends
    ]


if __name__ == "__main__":
    import json

    symbol = sys.argv[1] if len(sys.argv) > 1 else "MU"
    print(json.dumps({
        "quarterly_revenue": get_quarterly_revenue(symbol),
        "annual": get_annual_series(symbol),
    }, indent=2))
