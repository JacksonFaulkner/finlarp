"""Search the EDGAR filing index and the 8-K / 6-K event stream.

Rows are filings from sources/sec_events.py (filings.parquet, every filing per
company), joined to the item-level events (events.parquet: one row per 8-K item
with its label and signal tier). The default scope is the 8-K and 6-K families,
the dataset's own name; `form:` widens or narrows it.

Query syntax, free text and filters in any order:
    t:INTC,MU          ticker(s)
    form:10-Q,DEF      form prefixes (default 8-K, 6-K and their amendments)
    item:5.02          8-K item code, prefix ok (item:5.0 is 5.01 to 5.08)
    signal:high        some item on the filing at this tier or above (high | medium | low)
    since:2025         filed on or after (YYYY, YYYY-MM or YYYY-MM-DD)
    until:2026-06      filed before
    "exact phrase"     in the description or an item label
    -word              must not appear in the description or an item label
    bare words         every word must appear in the description or an item label
No query at all = the newest filings in scope.

CLI:
    filing_search.py q QUERY... [--json] [-k N]
"""

from __future__ import annotations

import argparse
import json
import re

import duckdb

from sources import sec_events

DEFAULT_FORMS = ["8-K", "6-K"]  # prefixes: also matches 8-K/A and 6-K/A
TIER = {"high": 3, "medium": 2, "low": 1}
_FILTER = re.compile(r'(\w+):("[^"]*"|\S+)')


def parse(query: str) -> dict:
    q = {"tickers": [], "forms": [], "items": [], "signal": None, "since": None, "until": None,
         "phrases": [], "exclude": [], "words": []}
    rest = query
    for key, val in _FILTER.findall(query):
        k, vals = key.lower(), [v for v in val.strip('"').split(",") if v]
        if k in ("t", "ticker"):
            q["tickers"] += [v.upper() for v in vals]
        elif k == "form":
            q["forms"] += [v.upper() for v in vals]
        elif k == "item":
            q["items"] += vals
        elif k == "signal":
            if vals and vals[0].lower() in TIER:
                q["signal"] = vals[0].lower()
        elif k in ("since", "until") and vals:
            q[k] = vals[0] + {4: "-01-01", 7: "-01"}.get(len(vals[0]), "")
        else:
            continue
        rest = rest.replace(f"{key}:{val}", " ", 1)
    q["phrases"] = re.findall(r'"([^"]+)"', rest)
    rest = re.sub(r'"[^"]+"', " ", rest)
    q["exclude"] = [w[1:] for w in rest.split() if w.startswith("-") and len(w) > 1]
    q["words"] = [w for w in rest.split() if not w.startswith("-")]
    return q


def sec_url(cik: int, accn: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn.replace('-', '')}/{accn}-index.htm"


def search(query: str, k: int = 200) -> list[dict]:
    q = parse(query)
    where, params = ["TRUE"], {}
    forms = q["forms"] or DEFAULT_FORMS
    where.append("EXISTS (SELECT 1 FROM unnest($forms) p(x) WHERE starts_with(f.form, x))")
    params["forms"] = forms
    if q["tickers"]:
        where.append("f.ticker IN (SELECT unnest($tickers))")
        params["tickers"] = q["tickers"]
    if q["items"]:
        where.append("EXISTS (SELECT 1 FROM unnest($items) p(x) WHERE EXISTS "
                     "(SELECT 1 FROM unnest(string_split(coalesce(f.items, ''), ',')) i(v) WHERE starts_with(v, x)))")
        params["items"] = q["items"]
    if q["signal"]:
        where.append("coalesce(ev.tier, 0) >= $tier")
        params["tier"] = TIER[q["signal"]]
    for key, op in (("since", ">="), ("until", "<")):
        if q[key]:
            where.append(f"f.filed {op} TRY_CAST(${key} AS DATE)")
            params[key] = q[key]
    text = "coalesce(f.description, '') || ' ' || coalesce(ev.labels, '')"
    for i, w in enumerate([*q["phrases"], *q["words"]]):
        where.append(f"{text} ILIKE '%' || $w{i} || '%'")
        params[f"w{i}"] = w
    for i, w in enumerate(q["exclude"]):
        where.append(f"{text} NOT ILIKE '%' || $x{i} || '%'")
        params[f"x{i}"] = w
    sql = f"""
        WITH ev AS (
            SELECT accn, string_agg(item || ' ' || label, '; ' ORDER BY item) AS labels,
                   max(CASE signal WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END) AS tier
            FROM read_parquet('{sec_events.EVENTS}') WHERE item IS NOT NULL GROUP BY accn
        )
        SELECT f.ticker, f.cik, f.form, CAST(f.filed AS VARCHAR), f.accn, f.primary_doc,
               coalesce(f.items, '') AS items, coalesce(f.description, '') AS description,
               coalesce(ev.labels, '') AS labels, coalesce(ev.tier, 0) AS tier, f.is_predecessor
        FROM read_parquet('{sec_events.FILINGS}') f LEFT JOIN ev USING (accn)
        WHERE {' AND '.join(where)}
        ORDER BY f.filed DESC, f.ticker
        LIMIT {int(k)}"""
    con = duckdb.connect()
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    cols = ["ticker", "cik", "form", "filed", "accn", "primary_doc", "items", "description", "labels", "tier", "is_predecessor"]
    out = []
    for r in rows:
        d = dict(zip(cols, r))
        d["url"] = sec_url(d["cik"], d["accn"])
        out.append(d)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Search EDGAR filings and 8-K / 6-K events")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("q")
    p.add_argument("query", nargs="*")
    p.add_argument("--json", action="store_true")
    p.add_argument("-k", type=int, default=200)
    args = ap.parse_args()
    rows = search(" ".join(args.query), args.k)
    if args.json:
        print(json.dumps(rows, default=str))
        return
    for r in rows:
        print(f"{r['filed']} {r['ticker']:6} {r['form']:7} {r['items']:14} {r['labels'] or r['description']}")
    print(f"{len(rows)} filings")


if __name__ == "__main__":
    main()
