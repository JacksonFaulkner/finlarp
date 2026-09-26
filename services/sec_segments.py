"""Dimensional revenue (segment / product / geography) from XBRL instances.

companyfacts carries only undimensioned facts, and the FSDS zips
(services/edgar_fsds.py) lag a quarter. This goes to each filing directly:
per company, the latest annual report (10-K / 20-F / 40-F) and the latest
10-Q filed after it. SEC publishes a plain XBRL instance next to every
inline filing (`<primary>_htm.xml`, ~2-3MB); we stream-parse it, keep the
revenue facts, and drop the XML.

Kept per fact: undimensioned totals and single-axis contexts
(ProductOrServiceAxis=DataCenterMember, StatementGeographicalAxis=country:TW,
...). ConsolidationItemsAxis=OperatingSegmentsMember is bookkeeping and is
stripped before counting axes. Contexts with 2+ real axes are cross-tabs
(segment x geography); they're skipped but counted per filing in the
manifest. Operating income is kept only undimensioned and by business
segment.

Members are local names; `is_custom_member` is true when the member lives
in the filer's own namespace (mrvl:DataCenterMember) rather than us-gaap /
srt / ifrs-full / country — i.e. not comparable across companies.

Layout under universe.data_dir("segments"):
    facts/<accn>.parquet   one zstd file per parsed filing
    manifest.json          accn -> status/rows/multi_axis (resume key)

CLI:
    SEC_RPS=1.4 uv run python services/sec_segments.py ingest [TICKER ...]
    uv run python services/sec_segments.py show TICKER
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import universe
from services.edgar import REVENUE_CONCEPTS

ANNUAL_FORMS = {"10-K", "10-KT", "20-F", "40-F"}
QUARTERLY_FORMS = {"10-Q"}

# edgar.py lacks the IncludingAssessedTax variant (CRWD, AAON, NEE, DUK... use it)
REVENUE = set(REVENUE_CONCEPTS) | {"RevenueFromContractWithCustomerIncludingAssessedTax",
                                   "Revenue", "RevenueFromContractsWithCustomers"}
OPINC = {"OperatingIncomeLoss", "ProfitLossFromOperatingActivities"}
SEGMENT_AXES = {"StatementBusinessSegmentsAxis", "SegmentsAxis"}

# Namespaces whose members are shared vocabulary (comparable across filers).
STANDARD_NS = ("fasb.org/us-gaap", "fasb.org/srt", "xbrl.ifrs.org", "xbrl.sec.gov/country",
               "xbrl.sec.gov/currency", "xbrl.sec.gov/exch", "xbrl.sec.gov/stpr", "xbrl.sec.gov/dei")
CONCEPT_NS = ("fasb.org/us-gaap", "xbrl.ifrs.org")

XBRLI = "{http://www.xbrl.org/2003/instance}"
XBRLDI = "{http://xbrl.org/2006/xbrldi}"

_manifest_lock = threading.Lock()


def _dir() -> Path:
    return universe.data_dir("segments")


def _facts_dir() -> Path:
    d = _dir() / "facts"
    d.mkdir(exist_ok=True)
    return d


def _manifest_path() -> Path:
    return _dir() / "manifest.json"


def load_manifest() -> dict[str, dict]:
    p = _manifest_path()
    return json.loads(p.read_text()) if p.exists() else {}


def _save_manifest_entry(accn: str, entry: dict) -> None:
    with _manifest_lock:
        m = load_manifest()
        m[accn] = entry
        tmp = _manifest_path().with_suffix(f".{os.getpid()}.part")
        tmp.write_text(json.dumps(m, indent=1, sort_keys=True))
        tmp.rename(_manifest_path())


# --------------------------------------------------------------- selection

def pick_filings(cik: int) -> list[dict]:
    """Latest annual report, plus the latest 10-Q filed after it."""
    r = universe.submissions(cik)["filings"]["recent"]
    rows = [{k: r[k][i] for k in ("accessionNumber", "form", "filingDate", "reportDate",
                                  "primaryDocument", "isXBRL", "isInlineXBRL")}
            for i in range(len(r["accessionNumber"]))]
    rows.sort(key=lambda x: x["filingDate"], reverse=True)
    annual = next((x for x in rows if x["form"] in ANNUAL_FORMS), None)
    out = [annual] if annual else []
    after = annual["filingDate"] if annual else ""
    q = next((x for x in rows if x["form"] in QUARTERLY_FORMS and x["filingDate"] > after), None)
    if q:
        out.append(q)
    return out


def _instance_url(cik: int, f: dict) -> str | None:
    """URL of the XBRL instance. Inline filings get SEC's extracted
    `<primary>_htm.xml`; anything else is found via the folder index."""
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{f['accessionNumber'].replace('-', '')}"
    prim = f.get("primaryDocument") or ""
    if f.get("isInlineXBRL") and prim.endswith((".htm", ".html")):
        guess = f"{base}/{prim.rsplit('.', 1)[0]}_htm.xml"
        return guess  # verified by caller; falls back to index on 404
    return _instance_from_index(base)


def _instance_from_index(base: str) -> str | None:
    resp = universe.sec_get(f"{base}/index.json")
    if resp.status_code != 200:
        return None
    items = resp.json()["directory"]["item"]
    xmls = [i for i in items if i["name"].lower().endswith(".xml")]
    htm = [i for i in xmls if i["name"].lower().endswith("_htm.xml")]
    if htm:
        return f"{base}/{max(htm, key=lambda i: int(i.get('size') or 0))['name']}"
    skip = ("_cal.xml", "_def.xml", "_lab.xml", "_pre.xml")
    cands = [i for i in xmls if not i["name"].lower().endswith(skip)
             and i["name"] != "FilingSummary.xml"]
    if not cands:
        return None
    return f"{base}/{max(cands, key=lambda i: int(i.get('size') or 0))['name']}"


# ----------------------------------------------------------------- parsing

def _local(qname: str) -> str:
    return qname.split("}", 1)[-1].split(":", 1)[-1]


def parse_instance(data: bytes) -> tuple[list[dict], dict]:
    """(rows, stats). Rows lack ticker/cik/accn/form — the caller adds them."""
    ns_map: dict[str, str] = {}          # prefix -> uri (last wins; instances declare once)
    contexts: dict[str, dict] = {}
    facts: list[tuple] = []              # (concept, ctx, unit, value)
    for event, item in ET.iterparse(io.BytesIO(data), events=("start-ns", "end")):
        if event == "start-ns":
            ns_map[item[0]] = item[1]
            continue
        el = item
        tag = el.tag
        if tag == XBRLI + "context":
            start = el.findtext(f"{XBRLI}period/{XBRLI}startDate")
            end = el.findtext(f"{XBRLI}period/{XBRLI}endDate")
            dims = []
            for m in el.iter(XBRLDI + "explicitMember"):
                txt = (m.text or "").strip()
                prefix = txt.split(":", 1)[0] if ":" in txt else ""
                dims.append((_local(m.get("dimension", "")), _local(txt), ns_map.get(prefix, "")))
            for m in el.iter(XBRLDI + "typedMember"):
                val = "".join(m.itertext()).strip()
                dims.append((_local(m.get("dimension", "")), val, "typed"))
            contexts[el.get("id")] = {"start": start, "end": end, "dims": dims}
            el.clear()
        elif tag.startswith("{") and el.get("contextRef"):
            uri, name = tag[1:].split("}", 1)
            if (name in REVENUE or name in OPINC) and any(s in uri for s in CONCEPT_NS):
                txt = (el.text or "").strip()
                if txt:
                    try:
                        facts.append((name, el.get("contextRef"), el.get("unitRef"), float(txt)))
                    except ValueError:
                        pass
            el.clear()

    rows, seen = [], set()
    multi, multi_ctx = 0, set()
    for concept, ctx_id, unit, val in facts:
        ctx = contexts.get(ctx_id)
        if not ctx or not ctx["start"] or not ctx["end"]:
            continue  # instants aren't revenue
        dims = [d for d in ctx["dims"]
                if not (d[0] == "ConsolidationItemsAxis" and d[1] == "OperatingSegmentsMember")]
        if len(dims) > 1:
            if concept in REVENUE and ctx_id not in multi_ctx:
                multi += 1
                multi_ctx.add(ctx_id)
            continue
        axis, member, is_custom = None, None, None
        if dims:
            axis, member, uri = dims[0]
            is_custom = not any(s in uri for s in STANDARD_NS)
            if concept in OPINC and axis not in SEGMENT_AXES:
                continue
        key = (concept, ctx["start"], ctx["end"], axis, member, unit)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"period_start": ctx["start"], "period_end": ctx["end"], "concept": concept,
                     "axis": axis, "member": member, "value": val,
                     "is_custom_member": is_custom, "unit": unit})
    return rows, {"multi_axis_contexts": multi, "contexts": len(contexts)}


def _write_parquet(rows: list[dict], dest: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".ndjson", delete=False) as tmp:
        for r in rows:
            tmp.write(json.dumps(r) + "\n")
    try:
        part = dest.with_suffix(".part")
        con = duckdb.connect()
        con.execute(f"""
            COPY (SELECT ticker::VARCHAR AS ticker, cik::BIGINT AS cik, accn::VARCHAR AS accn,
                         form::VARCHAR AS form, filing_date::DATE AS filing_date,
                         period_start::DATE AS period_start, period_end::DATE AS period_end,
                         concept::VARCHAR AS concept, axis::VARCHAR AS axis, member::VARCHAR AS member,
                         value::DOUBLE AS value, is_custom_member::BOOLEAN AS is_custom_member,
                         unit::VARCHAR AS unit
                  FROM read_json('{tmp.name}', format='newline_delimited', columns={{
                      ticker:'VARCHAR', cik:'BIGINT', accn:'VARCHAR', form:'VARCHAR',
                      filing_date:'VARCHAR', period_start:'VARCHAR', period_end:'VARCHAR',
                      concept:'VARCHAR', axis:'VARCHAR', member:'VARCHAR', value:'DOUBLE',
                      is_custom_member:'BOOLEAN', unit:'VARCHAR'}}))
            TO '{part}' (FORMAT parquet, COMPRESSION zstd)""")
        con.close()
        part.rename(dest)
    finally:
        os.unlink(tmp.name)


# ------------------------------------------------------------------ ingest

def ingest_filing(ticker: str, cik: int, f: dict) -> dict:
    accn = f["accessionNumber"]
    entry = {"ticker": ticker, "cik": cik, "form": f["form"], "filing_date": f["filingDate"],
             "report_date": f["reportDate"], "status": "ok", "ts": int(time.time())}
    if not f.get("isXBRL"):
        return entry | {"status": "no_xbrl", "reason": "filing has no XBRL"}
    url = _instance_url(cik, f)
    resp = universe.sec_get(url) if url else None
    if resp is not None and resp.status_code == 404 and url.endswith("_htm.xml"):
        base = url.rsplit("/", 1)[0]
        url = _instance_from_index(base)
        resp = universe.sec_get(url) if url else None
    if resp is None or resp.status_code != 200:
        code = None if resp is None else resp.status_code
        return entry | {"status": "failed", "reason": f"instance not found ({code})", "url": url}
    try:
        rows, stats = parse_instance(resp.content)
    except ET.ParseError as e:
        return entry | {"status": "failed", "reason": f"parse error: {e}", "url": url}
    meta = {"ticker": ticker, "cik": cik, "accn": accn, "form": f["form"],
            "filing_date": f["filingDate"]}
    rows = [meta | r for r in rows]
    if rows:
        _write_parquet(rows, _facts_dir() / f"{accn}.parquet")
    rev = [r for r in rows if r["concept"] in REVENUE]
    axes = sorted({r["axis"] for r in rev if r["axis"]})
    return entry | stats | {
        "url": url, "rows": len(rows), "bytes": len(resp.content),
        "revenue_axes": axes,
        "status": "ok" if rev else "no_revenue",
        **({"reason": "no revenue concept facts"} if not rev else {}),
    }


def _work(ticker: str, cik: int) -> list[str]:
    done = load_manifest()
    msgs = []
    try:
        filings = pick_filings(cik)
    except Exception as e:  # noqa: BLE001 — record and move on
        _save_manifest_entry(f"cik:{cik}", {"ticker": ticker, "cik": cik, "status": "failed",
                                            "reason": f"submissions: {e}"})
        return [f"{ticker}: submissions failed: {e}"]
    if not filings:
        _save_manifest_entry(f"cik:{cik}", {"ticker": ticker, "cik": cik, "status": "no_filings",
                                            "reason": "no 10-K/20-F/40-F/10-Q"})
        return [f"{ticker}: no periodic filings"]
    for f in filings:
        prev = done.get(f["accessionNumber"])
        if prev and prev["status"] in ("ok", "no_xbrl", "no_revenue"):
            continue
        try:
            e = ingest_filing(ticker, cik, f)
        except Exception as ex:  # noqa: BLE001
            e = {"ticker": ticker, "cik": cik, "form": f["form"], "status": "failed",
                 "reason": f"{type(ex).__name__}: {ex}"}
        _save_manifest_entry(f["accessionNumber"], e)
        msgs.append(f"{ticker} {f['form']} {f['accessionNumber']}: {e['status']} "
                    f"rows={e.get('rows', 0)} axes={','.join(e.get('revenue_axes', []))}")
    return msgs


def ingest(tickers: list[str] | None = None, workers: int = 3) -> None:
    stocks = [s for s in universe.stocks() if s["cik"]]
    if tickers:
        want = {t.upper() for t in tickers}
        stocks = [s for s in stocks if s["ticker"].upper() in want]
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for i, msgs in enumerate(ex.map(lambda s: _work(s["ticker"], s["cik"]), stocks), 1):
            for m in msgs:
                print(f"[{i}/{len(stocks)} {time.time() - t0:.0f}s] {m}", flush=True)
    print(f"done in {time.time() - t0:.0f}s")


# -------------------------------------------------------------------- query

def facts_glob() -> str:
    return str(_facts_dir() / "*.parquet")


def _mix(con, ticker: str, where: str) -> None:
    per = con.execute(f"""
        SELECT period_start, period_end, accn, form FROM read_parquet('{facts_glob()}')
        WHERE ticker = ? AND concept IN (SELECT unnest(?)) AND {where}
        ORDER BY period_end DESC, period_end - period_start ASC LIMIT 1""",
                      [ticker, sorted(REVENUE)]).fetchone()
    if not per:
        return
    ps, pe, accn, form = per
    rows = con.execute(f"""
        SELECT concept, axis, member, value, is_custom_member, unit
        FROM read_parquet('{facts_glob()}')
        WHERE ticker = ? AND period_start = ? AND period_end = ? AND accn = ?
          AND concept IN (SELECT unnest(?))""", [ticker, ps, pe, accn, sorted(REVENUE)]).fetchall()
    # 20-F filers may add a convenience translation (TSM: TWD + USD);
    # keep the unit most facts are reported in.
    units: dict[str, int] = {}
    for *_, u in rows:
        units[u] = units.get(u, 0) + 1
    unit = max(units, key=units.get)
    rows = [r for r in rows if r[5] == unit]
    totals = {c: v for c, a, _, v, _, _ in rows if a is None}
    total = max(totals.values()) if totals else None
    print(f"\n{ticker} {form} {accn}  {ps} -> {pe} ({(pe - ps).days + 1}d)  "
          f"total revenue {total / 1e9 if total else float('nan'):,.3f}B {unit}")
    by_axis: dict[str, dict[str, list]] = {}
    for c, a, m, v, cust, _ in rows:
        if a:
            by_axis.setdefault(a, {}).setdefault(c, []).append((m, v, cust))
    for axis, concepts in sorted(by_axis.items()):
        # the concept with the most members on this axis is the "real" split
        c, members = max(concepts.items(), key=lambda kv: len(kv[1]))
        denom = totals.get(c) or total
        print(f"  {axis}  [{c}]")
        for m, v, cust in sorted(members, key=lambda x: -x[1]):
            share = f"{v / denom:6.1%}" if denom else "   n/a"
            print(f"    {share}  {v / 1e9:10,.3f}B  {m}{'' if cust else '  (std)'}")
    opi = con.execute(f"""
        SELECT member, value FROM read_parquet('{facts_glob()}')
        WHERE ticker = ? AND period_start = ? AND period_end = ? AND accn = ?
          AND concept IN (SELECT unnest(?)) AND axis IS NOT NULL ORDER BY value DESC""",
                      [ticker, ps, pe, accn, sorted(OPINC)]).fetchall()
    if opi:
        print("  operating income by segment")
        for m, v in opi:
            print(f"               {v / 1e9:10,.3f}B  {m}")


def show(ticker: str) -> None:
    ticker = ticker.upper()
    con = duckdb.connect()
    _mix(con, ticker, "period_end - period_start < 120")   # latest quarter
    _mix(con, ticker, "period_end - period_start > 300")   # latest fiscal year


def summary() -> None:
    m = load_manifest()
    by_status: dict[str, int] = {}
    for e in m.values():
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
    print(json.dumps(by_status))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if cmd == "ingest":
        ingest(sys.argv[2:] or None)
    elif cmd == "show":
        for t in sys.argv[2:]:
            show(t)
    else:
        summary()
