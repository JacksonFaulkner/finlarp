"""XBRL companyfacts — every financial-statement fact each company has
filed with the SEC, for the whole ai_stocks.json universe.

companyfacts (data.sec.gov/api/xbrl/companyfacts/CIK##########.json) is
one JSON per registrant holding every us-gaap / ifrs-full / dei / srt
value tagged in its 10-K/10-Q/20-F/40-F/8-K filings since ~2009. The raw
JSON repeats each value once per filing that re-presents it (a FY2020
revenue number shows up in the FY2020, FY2021 and FY2022 10-Ks plus the
comparative columns of later 10-Qs), so we collapse to one row per
(ticker, taxonomy, concept, unit, start, end), keeping the latest-filed
copy — which is the restated value when a company restates. `frame`
(SEC's calendar-period tag, set on only one copy) is carried over from
whichever copy had it.

A ticker may span several registrants (cik_aliases.json): MRVL's
FY2008–FY2021 history lives under the Bermuda parent. All CIKs for a
ticker are merged into one Parquet file per ticker under
financials/facts/, which is also the resume marker: a rerun skips tickers
whose file exists and whose CIK set hasn't changed (status.json).

Caveats of the source that the series helpers work around:
  * `fy`/`fp`/`form` describe the *filing* the kept copy came from, not
    the fact's own period — derive periods from start/end instead.
  * Companies tag the same line item under different concepts over time
    (Revenues -> RevenueFromContractWithCustomerExcludingAssessedTax at
    ASC 606 adoption, 2018), so series stitch a priority list per period.
  * 10-Ks carry the full year, not Q4; many cash-flow items are only
    tagged year-to-date. `quarterly_series` derives the missing quarter
    as the difference of two cumulative periods sharing a start date.

CLI: ingest [TICKER ...] [--force] | show TICKER | annual|quarterly TICKER [metric]
     | candidates [MIN_FY] | stats
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import duckdb


from sources import universe

FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
TAXONOMIES = ("us-gaap", "ifrs-full", "dei", "srt")

DIR = universe.data_dir("financials")
FACTS_DIR = DIR / "facts"
TMP_DIR = DIR / "tmp"
STATUS_PATH = DIR / "status.json"
CONCEPTS_PATH = DIR / "concepts.parquet"
FACTS_GLOB = str(FACTS_DIR / "*.parquet")

# Named metrics -> concept priority. Per period the first concept with a
# value wins, which stitches renames (SalesRevenueNet -> Revenues ->
# RevenueFromContract... across ASC 606) and us-gaap/ifrs-full filers.
METRICS: dict[str, list[str]] = {
    "revenue": [
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:Revenues",
        "us-gaap:SalesRevenueNet",
        "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax",
        "us-gaap:SalesRevenueGoodsNet",
        "us-gaap:SalesRevenueServicesNet",
        "us-gaap:RevenuesNetOfInterestExpense",
        "us-gaap:RegulatedAndUnregulatedOperatingRevenue",  # utilities
        "us-gaap:ElectricUtilityRevenue",
        "ifrs-full:Revenue",
        "ifrs-full:RevenueFromContractsWithCustomers",
    ],
    "gross_profit": ["us-gaap:GrossProfit", "ifrs-full:GrossProfit"],
    "operating_income": [
        "us-gaap:OperatingIncomeLoss",
        "ifrs-full:ProfitLossFromOperatingActivities",
    ],
    "net_income": [
        "us-gaap:NetIncomeLoss",
        "us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic",
        "us-gaap:ProfitLoss",
        "ifrs-full:ProfitLossAttributableToOwnersOfParent",
        "ifrs-full:ProfitLoss",
    ],
    "eps_diluted": [
        "us-gaap:EarningsPerShareDiluted",
        "us-gaap:EarningsPerShareBasicAndDiluted",
        "ifrs-full:DilutedEarningsLossPerShare",
        "ifrs-full:DilutedEarningsLossPerShareFromContinuingOperations",
    ],
    "eps_basic": [
        "us-gaap:EarningsPerShareBasic",
        "us-gaap:EarningsPerShareBasicAndDiluted",
        "ifrs-full:BasicEarningsLossPerShare",
    ],
    "operating_cash_flow": [
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "us-gaap:NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "ifrs-full:CashFlowsFromUsedInOperatingActivities",
    ],
    "capex": [
        "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        "us-gaap:PaymentsToAcquireProductiveAssets",
        "ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
        "ifrs-full:PurchaseOfPropertyPlantAndEquipment",
    ],
    "rnd": [
        "us-gaap:ResearchAndDevelopmentExpense",
        "us-gaap:ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        "ifrs-full:ResearchAndDevelopmentExpense",
    ],
    "total_assets": ["us-gaap:Assets", "ifrs-full:Assets"],
    "equity": [
        "us-gaap:StockholdersEquity",
        "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "ifrs-full:EquityAttributableToOwnersOfParent",
        "ifrs-full:Equity",
    ],
    "cash": [
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "ifrs-full:CashAndCashEquivalents",
    ],
    "long_term_debt": [
        "us-gaap:LongTermDebtNoncurrent",
        "us-gaap:LongTermDebt",
        "ifrs-full:NoncurrentPortionOfNoncurrentBorrowings",
    ],
    "shares_outstanding": [
        "dei:EntityCommonStockSharesOutstanding",
        "us-gaap:CommonStockSharesOutstanding",
    ],
    "diluted_shares": [
        "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
        "ifrs-full:AdjustedWeightedAverageShares",
    ],
}

_COLUMNS = {
    "ticker": "VARCHAR", "cik": "INTEGER", "taxonomy": "VARCHAR",
    "concept": "VARCHAR", "unit": "VARCHAR", "start": "DATE", "end": "DATE",
    "val": "DOUBLE", "fy": "INTEGER", "fp": "VARCHAR", "form": "VARCHAR",
    "filed": "DATE", "accn": "VARCHAR", "frame": "VARCHAR",
}


# --------------------------------------------------------------------- ingest

def _status() -> dict:
    return json.loads(STATUS_PATH.read_text()) if STATUS_PATH.exists() else {}


def _save_status(st: dict) -> None:
    tmp = STATUS_PATH.with_suffix(f".{os.getpid()}.part")
    tmp.write_text(json.dumps(st, indent=1, sort_keys=True))
    tmp.rename(STATUS_PATH)


def _fetch(cik: int) -> dict | None:
    resp = universe.sec_get(FACTS_URL.format(cik=cik), timeout=120)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def ingest_ticker(ticker: str, ciks: list[int]) -> dict:
    """Fetch, flatten and dedupe every CIK's companyfacts for one ticker
    into facts/<TICKER>.parquet. Returns a status record."""
    FACTS_DIR.mkdir(exist_ok=True)
    TMP_DIR.mkdir(exist_ok=True)
    safe = ticker.replace("/", "_")
    nd = TMP_DIR / f"{safe}.ndjson"
    raw = 0
    per_cik: dict[str, dict] = {}
    labels: dict[str, str] = {}
    with open(nd, "w") as f:
        for cik in ciks:
            doc = _fetch(cik)
            if doc is None:
                per_cik[str(cik)] = {"error": "404"}
                continue
            n = 0
            for tax, concepts in doc.get("facts", {}).items():
                if tax not in TAXONOMIES:
                    continue
                for concept, node in concepts.items():
                    labels.setdefault(f"{tax}:{concept}", node.get("label") or "")
                    for unit, entries in node.get("units", {}).items():
                        for e in entries:
                            f.write(json.dumps({
                                "ticker": ticker, "cik": cik, "taxonomy": tax,
                                "concept": concept, "unit": unit,
                                "start": e.get("start"), "end": e["end"],
                                "val": e.get("val"), "fy": e.get("fy"),
                                "fp": e.get("fp"), "form": e.get("form"),
                                "filed": e.get("filed"), "accn": e.get("accn"),
                                "frame": e.get("frame"),
                            }, separators=(",", ":")) + "\n")
                            n += 1
            per_cik[str(cik)] = {"name": doc.get("entityName"), "raw": n}
            raw += n
    out = FACTS_DIR / f"{safe}.parquet"
    rec = {"ciks": ciks, "per_cik": per_cik, "raw": raw, "at": time.strftime("%F %T")}
    if raw == 0:
        nd.unlink(missing_ok=True)
        out.unlink(missing_ok=True)
        return rec | {"rows": 0, "error": "no companyfacts"}
    part = out.with_suffix(".part")
    cols = "{" + ", ".join(f"'{k}': '{v}'" for k, v in _COLUMNS.items()) + "}"
    key = "taxonomy, concept, unit, start, \"end\""
    con = duckdb.connect()
    con.execute(f"""
        COPY (
          SELECT ticker, cik, taxonomy, concept, unit, start, "end", val, fy, fp,
                 form, filed, accn, frame
          FROM (
            SELECT * EXCLUDE (frame),
                   max(frame) OVER (PARTITION BY {key}) AS frame,
                   row_number() OVER (PARTITION BY {key}
                                      ORDER BY filed DESC NULLS LAST, accn DESC) AS rn
            FROM read_json('{nd}', format='newline_delimited', columns={cols})
            WHERE val IS NOT NULL
          ) WHERE rn = 1
          ORDER BY taxonomy, concept, unit, "end", start
        ) TO '{part}' (FORMAT parquet, COMPRESSION zstd)
    """)
    rows = con.execute(f"SELECT count(*) FROM read_parquet('{part}')").fetchone()[0]
    con.close()
    part.rename(out)
    nd.unlink(missing_ok=True)
    (TMP_DIR / f"{safe}.labels.json").write_text(json.dumps(labels))
    return rec | {"rows": rows}


def _build_concepts() -> None:
    """Merge per-ticker label sidecars into concepts.parquet
    (taxonomy, concept, label, n_tickers), then drop the sidecars."""
    counts: dict[str, list] = {}
    for p in TMP_DIR.glob("*.labels.json"):
        for k, lab in json.loads(p.read_text()).items():
            c = counts.setdefault(k, [lab, 0])
            c[1] += 1
    if not counts:
        return
    nd = TMP_DIR / "concepts.ndjson"
    with open(nd, "w") as f:
        for k, (lab, n) in counts.items():
            tax, concept = k.split(":", 1)
            f.write(json.dumps({"taxonomy": tax, "concept": concept, "label": lab, "n_tickers": n}) + "\n")
    old = CONCEPTS_PATH.exists()
    con = duckdb.connect()
    src = f"read_json('{nd}', format='newline_delimited')"
    if old:  # keep labels for tickers not re-ingested this run
        src = f"""(SELECT * FROM {src} UNION ALL BY NAME
                   SELECT * FROM '{CONCEPTS_PATH}'
                   WHERE (taxonomy, concept) NOT IN (SELECT taxonomy, concept FROM {src}))"""
    con.execute(f"""
        COPY (SELECT l.taxonomy, l.concept, l.label, coalesce(c.n, 0) AS n_tickers
              FROM {src} l LEFT JOIN (
                SELECT taxonomy, concept, count(DISTINCT ticker) AS n
                FROM '{FACTS_GLOB}' GROUP BY ALL) c USING (taxonomy, concept)
              ORDER BY taxonomy, concept)
        TO '{CONCEPTS_PATH}.part' (FORMAT parquet, COMPRESSION zstd)""")
    con.close()
    Path(f"{CONCEPTS_PATH}.part").rename(CONCEPTS_PATH)
    nd.unlink()
    for p in TMP_DIR.glob("*.labels.json"):
        p.unlink()


def ingest(tickers: list[str] | None = None, force: bool = False, workers: int = 3) -> dict:
    """Ingest the universe (or the given tickers). Skips tickers already on
    disk with the same CIK set unless force. Throttling is in sec_get, so
    the worker threads only overlap download/flatten time."""
    st = _status()
    todo = []
    for s in universe.stocks():
        t = s["ticker"]
        if tickers and t not in tickers:
            continue
        if not s["ciks"]:
            continue
        prev = st.get(t, {})
        done = (FACTS_DIR / f"{t.replace('/', '_')}.parquet").exists() or prev.get("error") == "no companyfacts"
        if not force and done and prev.get("ciks") == s["ciks"]:
            continue
        todo.append((t, s["ciks"]))
    print(f"{len(todo)} tickers to ingest", file=sys.stderr)
    t0 = time.time()
    with ThreadPoolExecutor(workers) as pool:
        futs = {pool.submit(ingest_ticker, t, c): t for t, c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            t = futs[fut]
            try:
                st[t] = fut.result()
            except Exception as e:  # keep going; rerun retries
                st[t] = {"ciks": dict(todo)[t], "error": f"{type(e).__name__}: {e}"[:300], "rows": 0}
            _save_status(st)
            print(f"[{i}/{len(todo)} {time.time() - t0:.0f}s] {t}: {st[t].get('rows')} rows"
                  + (f" ERROR {st[t]['error']}" if st[t].get("error") else ""), file=sys.stderr)
    _build_concepts()
    if TMP_DIR.exists() and not any(TMP_DIR.iterdir()):
        TMP_DIR.rmdir()
    return stats()


def stats() -> dict:
    st = _status()
    files = list(FACTS_DIR.glob("*.parquet"))
    size = sum(p.stat().st_size for p in files) + (CONCEPTS_PATH.stat().st_size if CONCEPTS_PATH.exists() else 0)
    rows = duckdb.sql(f"SELECT count(*) FROM '{FACTS_GLOB}'").fetchone()[0] if files else 0
    return {
        "tickers_with_facts": len(files),
        "rows": rows,
        "raw_rows": sum(v.get("raw", 0) for v in st.values()),
        "mb": round(size / 1e6, 1),
        "failed": {k: v.get("error") for k, v in st.items() if v.get("error")},
    }


# --------------------------------------------------------------------- series

def _parse_concepts(concepts: str | list[str]) -> list[tuple[str, str]]:
    if isinstance(concepts, str):
        concepts = METRICS.get(concepts, [concepts])
    out = []
    for c in concepts:
        tax, _, name = c.rpartition(":")
        if tax:
            out.append((tax, name))
        else:  # bare name: try both statement taxonomies
            out += [("us-gaap", name), ("ifrs-full", name)]
    return out


def _load(ticker: str, pairs: list[tuple[str, str]]) -> list[dict]:
    path = FACTS_DIR / f"{ticker.upper().replace('/', '_')}.parquet"
    if not path.exists():
        return []
    con = duckdb.connect()
    con.execute("CREATE TEMP TABLE want (taxonomy VARCHAR, concept VARCHAR, pri INTEGER)")
    con.executemany("INSERT INTO want VALUES (?, ?, ?)", [(t, c, i) for i, (t, c) in enumerate(pairs)])
    cur = con.execute(f"""
        SELECT f.*, w.pri FROM '{path}' f JOIN want w USING (taxonomy, concept)
    """)
    names = [d[0] for d in cur.description]
    rows = [dict(zip(names, r)) for r in cur.fetchall()]
    con.close()
    return rows


def _pick_unit(rows: list[dict]) -> str | None:
    """The current reporting unit: among units tagged for the latest period,
    the one with the most rows (USD for domestic filers, TWD for TSM, EUR
    for ASML, USD for JOYY/NBIS after they switched from CNY/RUB). Foreign
    filers' "convenience translation" USD columns lose on row count."""
    if not rows:
        return None
    last = max(r["end"] for r in rows)
    latest = {r["unit"] for r in rows if r["end"] == last}
    counts: dict[str, int] = {}
    for r in rows:
        if r["unit"] in latest:
            counts[r["unit"]] = counts.get(r["unit"], 0) + 1
    return max(counts, key=counts.get)


def _fy_label(end: date) -> int:
    """Fiscal year named for the calendar year it ends in, except 52/53-week
    years ending in the first week of January (belong to the prior year)."""
    return end.year - 1 if end.month == 1 and end.day <= 7 else end.year


def _days(r: dict) -> int | None:
    return (r["end"] - r["start"]).days + 1 if r["start"] else None


def _out(r: dict, **extra) -> dict:
    return {"end": r["end"].isoformat(), "start": r["start"].isoformat() if r["start"] else None,
            "val": r["val"], "concept": r["concept"], "unit": r["unit"],
            "filed": r["filed"].isoformat() if r["filed"] else None, "accn": r["accn"], **extra}


def _stitch(cands: dict[date, list[tuple[int, dict]]]) -> dict[date, dict]:
    """Per period end, the value from the highest-priority concept. Zeros
    lose to any nonzero candidate: some filers tag a placeholder 0 under a
    higher-priority concept (ETN: Revenues=0 next to SalesRevenueNet)."""
    return {end: min(lst, key=lambda x: (x[1]["val"] == 0, x[0]))[1] for end, lst in cands.items()}


def annual_series(ticker: str, concepts: str | list[str] = "revenue", unit: str | None = None) -> list[dict]:
    """[{fy, start, end, val, concept, unit, ...}] oldest -> newest, one per
    fiscal year, stitched across CIKs and concept renames. `concepts` is a
    METRICS name or a priority list of "taxonomy:Concept" (bare names try
    us-gaap then ifrs-full). Duration concepts use ~1-year periods; instant
    concepts (balance sheet) use the value at each fiscal year end."""
    rows = _load(ticker, _parse_concepts(concepts))
    unit = unit or _pick_unit(rows)
    rows = [r for r in rows if r["unit"] == unit]
    durations = [r for r in rows if r["start"] is not None]
    cands: dict[date, list] = {}
    if durations:
        for r in durations:
            if 350 <= _days(r) <= 380:
                cands.setdefault(r["end"], []).append((r["pri"], r))
    else:
        fy_ends = _fiscal_year_ends(ticker)
        for r in rows:
            if r["end"] in fy_ends:
                cands.setdefault(r["end"], []).append((r["pri"], r))
    picked = _stitch(cands)
    return [_out(picked[e], fy=_fy_label(e)) for e in sorted(picked)]


def _fiscal_year_ends(ticker: str) -> set[date]:
    path = FACTS_DIR / f"{ticker.upper().replace('/', '_')}.parquet"
    if not path.exists():
        return set()
    return {r[0] for r in duckdb.sql(f"""
        SELECT DISTINCT "end" FROM '{path}'
        WHERE start IS NOT NULL AND date_diff('day', start, "end") BETWEEN 349 AND 379
          AND taxonomy IN ('us-gaap', 'ifrs-full')
          AND (form LIKE '10-K%' OR form LIKE '20-F%' OR form LIKE '40-F%')
    """).fetchall()}


def quarterly_series(ticker: str, concepts: str | list[str] = "revenue", unit: str | None = None) -> list[dict]:
    """[{fy, fq, start, end, val, concept, derived, ...}] oldest -> newest,
    one per fiscal quarter. Discrete ~3-month facts are used as filed;
    quarters that are only implied (Q4 = FY - 9M, cash-flow YTD tagging)
    are derived from two cumulative periods sharing a start date, flagged
    derived=True, with both facts in `derived_from` [longer, shorter]. Instant concepts return every period-end value.
    20-F filers generally have no quarters (only annual/semiannual)."""
    rows = _load(ticker, _parse_concepts(concepts))
    unit = unit or _pick_unit(rows)
    rows = [r for r in rows if r["unit"] == unit]
    durations = [r for r in rows if r["start"] is not None]
    annual = {r["end"]: r["start"] for r in durations if 350 <= _days(r) <= 380}
    cands: dict[date, list] = {}
    if not durations:
        for r in rows:
            cands.setdefault(r["end"], []).append((r["pri"], r))
        picked = _stitch(cands)
        return [_out(picked[e]) for e in sorted(picked)]

    by_concept: dict[int, list[dict]] = {}
    for r in durations:
        by_concept.setdefault(r["pri"], []).append(r)
    for pri, rs in by_concept.items():
        have = {}
        for r in rs:
            if 80 <= _days(r) <= 100:
                have[r["end"]] = r | {"derived": False}
        by_start: dict[date, list[dict]] = {}
        for r in rs:
            if 80 <= _days(r) <= 380:
                by_start.setdefault(r["start"], []).append(r)
        for group in by_start.values():
            group.sort(key=lambda r: r["end"])
            for a, b in zip(group, group[1:]):
                gap = (b["end"] - a["end"]).days
                if 80 <= gap <= 100 and b["end"] not in have:
                    have[b["end"]] = b | {"start": a["end"] + timedelta(days=1),
                                          "val": b["val"] - a["val"], "derived": True, "parts": (b, a)}
        for end, r in have.items():
            cands.setdefault(end, []).append((pri, r))
    picked = _stitch(cands)
    out = []
    for e in sorted(picked):
        r = picked[e]
        fy = fq = None
        for a_end, a_start in annual.items():
            if a_start <= e <= a_end:
                fy = _fy_label(a_end)
                fq = min(4, max(1, round(((e - a_start).days + 1) / 91.3)))
                break
        if fy is None and annual and e > max(annual):  # current, unfinished FY
            last = max(annual)
            k = (e - last).days
            fy = _fy_label(last) + 1 + (k - 1) // 371
            fq = min(4, max(1, round((((k - 1) % 371) + 1) / 91.3)))
        extra = {}
        if r["derived"]:  # the two cumulative facts subtracted, so callers can cite both filings
            extra["derived_from"] = [
                {"start": x["start"].isoformat(), "end": x["end"].isoformat(), "val": x["val"],
                 "concept": x["concept"], "filed": x["filed"].isoformat() if x["filed"] else None, "accn": x["accn"]}
                for x in r["parts"]]
        out.append(_out(r, fy=fy, fq=fq, derived=r["derived"], **extra))
    return out


def predecessor_candidates(min_fy: int = 2015) -> list[dict]:
    """Tickers whose earliest annual us-gaap/ifrs fact is FY >= min_fy, with
    the current registrant's former names and first filing date — the
    starting list for finding a predecessor CIK to add to cik_aliases.json.
    Most hits are genuine recent IPOs/spin-offs; verify by hand."""
    first = duckdb.sql(f"""
        SELECT ticker, min("end") AS first_end, list(DISTINCT cik) AS ciks
        FROM '{FACTS_GLOB}'
        WHERE start IS NOT NULL AND taxonomy IN ('us-gaap', 'ifrs-full')
          AND date_diff('day', start, "end") BETWEEN 349 AND 379
        GROUP BY ticker
    """).fetchall()
    out = []
    for t, first_end, cks in sorted(first):
        if _fy_label(first_end) < min_fy:
            continue
        sub = universe.submissions(universe.ciks(t)[0])
        fil = sub["filings"]["recent"]
        out.append({
            "ticker": t, "first_fy": _fy_label(first_end), "ciks": cks, "name": sub.get("name"),
            "former": [f.get("name") for f in sub.get("formerNames", [])],
            "first_filing": min(fil["filingDate"]) if fil["filingDate"] else None,
        })
    return out


# --------------------------------------------------------------------- CLI

def show(ticker: str) -> None:
    ticker = ticker.upper()
    path = FACTS_DIR / f"{ticker}.parquet"
    if not path.exists():
        print(f"{ticker}: no facts on disk ({_status().get(ticker, {}).get('error', 'not ingested')})")
        return
    n, nc, ciks = duckdb.sql(f"SELECT count(*), count(DISTINCT concept), list(DISTINCT cik) FROM '{path}'").fetchone()
    print(f"{ticker}: {n} facts, {nc} concepts, CIKs {ciks}\n")
    metrics = ["revenue", "gross_profit", "operating_income", "net_income", "eps_diluted", "operating_cash_flow"]
    series = {m: {r["fy"]: r for r in annual_series(ticker, m)} for m in metrics}
    fys = sorted(set().union(*[s.keys() for s in series.values()]))
    unit = next((r["unit"] for s in series.values() for r in s.values()), "")
    print(f"Annual ({unit}, millions except EPS)")
    print(f"{'FY':>6} {'end':>10} " + " ".join(f"{m[:12]:>12}" for m in metrics) + "  revenue concept")
    for fy in fys:
        end = next(s[fy]["end"] for s in series.values() if fy in s)
        cells = []
        for m in metrics:
            r = series[m].get(fy)
            cells.append("" if r is None else f"{r['val']:.2f}" if m.startswith("eps") else f"{r['val'] / 1e6:,.0f}")
        rc = series["revenue"].get(fy, {}).get("concept", "")
        print(f"{fy:>6} {end:>10} " + " ".join(f"{c:>12}" for c in cells) + f"  {rc}")
    q = quarterly_series(ticker, "revenue")[-12:]
    if q:
        print("\nQuarterly revenue (last 12; * = derived)")
        for r in q:
            print(f"  FY{r['fy']} Q{r['fq']} {r['end']}  {r['val'] / 1e6:>12,.1f}{' *' if r['derived'] else ''}  {r['concept']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    cmd = args[0] if args else "stats"
    if cmd == "ingest":
        rest = [a for a in args[1:] if not a.startswith("--")]
        print(json.dumps(ingest([t.upper() for t in rest] or None, force="--force" in args), indent=2))
    elif cmd == "show" and len(args) > 1:
        show(args[1])
    elif cmd == "candidates":
        for c in predecessor_candidates(int(args[1]) if len(args) > 1 else 2015):
            print(json.dumps(c))
    elif cmd == "annual" and len(args) > 1:
        print(json.dumps(annual_series(args[1].upper(), args[2] if len(args) > 2 else "revenue"), indent=1))
    elif cmd == "quarterly" and len(args) > 1:
        print(json.dumps(quarterly_series(args[1].upper(), args[2] if len(args) > 2 else "revenue"), indent=1))
    else:
        print(json.dumps(stats(), indent=2))
