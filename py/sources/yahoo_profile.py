"""Yahoo Finance company profiles for the universe (quoteSummary
assetProfile + quoteType + price). Gives every ticker, SEC filer or not,
a legal long name, sector/industry, country, website and business summary.

    profiles/profiles.parquet  ticker, long_name, short_name, sector, industry,
                               country, website, domain, employees, market_cap,
                               currency, summary, officers (JSON [{name, title}])

    python sources/yahoo_profile.py
"""
from __future__ import annotations

import json
import time
from urllib.parse import urlparse

import duckdb


from sources import yahoo
from sources import universe
from sources import pq

OUT = universe.data_dir("profiles")
URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"
MODULES = "assetProfile,quoteType,price"


def fetch(session, sym: str) -> dict | None:
    crumb = yahoo.get_crumb(session)
    for attempt in range(3):
        r = session.get(URL.format(sym), params={"modules": MODULES, "crumb": crumb}, timeout=15)
        if r.status_code == 404:
            return None
        if r.status_code == 401:  # crumb went stale mid-run: new handshake, not the same dead crumb
            crumb = yahoo.get_crumb(session, refresh=True)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt * 3)
            continue
        r.raise_for_status()
        res = (r.json().get("quoteSummary") or {}).get("result") or []
        return res[0] if res else None
    return None


def row(ticker: str, res: dict) -> dict:
    ap, qt, pr = res.get("assetProfile", {}), res.get("quoteType", {}), res.get("price", {})
    site = ap.get("website") or ""
    return {
        "ticker": ticker,
        "long_name": qt.get("longName"),
        "short_name": qt.get("shortName"),
        "sector": ap.get("sector"),
        "industry": ap.get("industry"),
        "country": ap.get("country"),
        "website": site or None,
        "domain": urlparse(site).netloc.removeprefix("www.") or None,
        "employees": ap.get("fullTimeEmployees"),
        "market_cap": (pr.get("marketCap") or {}).get("raw"),
        "currency": pr.get("currency"),
        "summary": ap.get("longBusinessSummary"),
        "officers": json.dumps([{"name": o.get("name"), "title": o.get("title")}
                                for o in ap.get("companyOfficers") or []]),
    }


def main() -> None:
    session = yahoo.new_session()
    rows, missing = [], []
    for s in universe.stocks():
        res = fetch(session, s["ticker"])
        if res:
            rows.append(row(s["ticker"], res))
        else:
            missing.append(s["ticker"])
        time.sleep(0.4)
    prev = OUT / "profiles.parquet"
    had = duckdb.sql(f"SELECT count(*) FROM '{prev}'").fetchone()[0] if prev.exists() else 0
    if len(rows) < 0.9 * had:
        # a dead crumb or a Yahoo outage fails most tickers; keep the good file
        raise SystemExit(f"only {len(rows)} profiles fetched vs {had} stored; not overwriting")
    con = duckdb.connect()
    con.execute("CREATE TABLE p AS SELECT * FROM (SELECT unnest($r, recursive := true))", {"r": rows})
    pq.copy_atomic(con, "SELECT * FROM p", prev)
    print(f"{len(rows)} profiles, {len(missing)} missing: {' '.join(missing)}")


if __name__ == "__main__":
    main()
