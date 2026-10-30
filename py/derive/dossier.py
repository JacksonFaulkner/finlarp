"""Per-ticker research dossier for the heatmap `p` screen: everything we've
pulled for one security, where every number carries a link to the document
it came from. Stored as JSON in DuckDB dossier_cache (db.py) and rendered by
the finlarp `dossier` screen, same flow as canslim.

Rule: no value without a source. Every kv row, table row, series point and
bar item has `src`:
    {"label": "10-Q Q2 FY27 · RevenueFromContract...", "url": "https://..."}
Derived numbers (YoY %, holder change, AI share) instead carry the formula
and the sources of their inputs:
    {"label": "...", "formula": "2,739.3 / 2,006.1 - 1", "inputs": [src, src]}
URLs point at the exact document: inline-XBRL viewer for financial facts,
the EX-99.1 for earnings, the 8-K / Form 4 / 13F-HR itself, Google Patents
per patent, and a text fragment (#:~:text=) that scrolls to and highlights
the quoted sentence for guidance lines and new risk factors.
`validate()` lists anything unsourced in dossier["unsourced"].

JSON shape (what tui/src/screens/dossier.rs reads):
    {ticker, name, industry, country, market_cap, employees, built_at,
     freshness: [{source, pulled}], unsourced: [...],
     sections: [{id, title, new, badge, blocks: [block]}]}
    block = {type: kv,     rows:  [{label, value, new?, src}]}
          | {type: table,  title, cols: [..], rows: [{cells: [..], new?, src}]}
          | {type: series, title, unit, points: [{x, y, src}]}
          | {type: bars,   title, unit, items: [{label, value, src}]}
          | {type: text,   text, src}

    python py/derive/dossier.py MRVL          # build + cache, print summary
    python py/derive/dossier.py MRVL --json   # print the JSON
    python py/derive/dossier.py MRVL NVDA --debug [-v]   # section health grid, no cache write
    python py/derive/dossier.py --all --debug            # health sweep over the universe
    python py/derive/dossier.py --all         # every ticker in the universe
    python py/derive/dossier.py MRVL --if-stale 12   # rebuild only if stale; JSON status (nvim)
"""
from __future__ import annotations

import json
import re
import sys
import time
import traceback
from datetime import date, datetime
from urllib.parse import quote

import duckdb


from core import db
from sources import sec_13f, universe

D = universe.DATA_ROOT
SEC = "https://www.sec.gov"
NEW_DAYS = 30
PV_URL = "https://data.uspto.gov/bulkdata/datasets/pvgpatdis"
AIPD_URL = "https://data.uspto.gov/bulkdata/datasets/ecopatai"
F13_URL = "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"
INSIDER_URL = "https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets"


# ---- links ---------------------------------------------------------------

def archive(cik, accn: str, doc: str | None = None) -> str:
    base = f"{SEC}/Archives/edgar/data/{int(cik)}/{accn.replace('-', '')}"
    return f"{base}/{doc}" if doc else f"{base}/{accn}-index.htm"


def ixbrl(cik, accn: str, doc: str) -> str:
    return f"{SEC}/ix?doc=/Archives/edgar/data/{int(cik)}/{accn.replace('-', '')}/{doc}"


def fragment(url: str | None, text: str | None, words: int = 8) -> str | None:
    """Scroll-to-text link: the browser jumps to and highlights the quote.
    First few words only, so small whitespace/markup differences still hit."""
    w = re.sub(r"^[\s•\-–·*]+", "", text or "").split()[:words]
    return f"{url}#:~:text={quote(' '.join(w), safe='')}" if (w and url) else url


def src(label: str, url: str | None = None, **kw) -> dict:
    return {"label": label, "url": url, **kw}


def derived(label: str, formula: str, inputs: list[dict], searched: dict | None = None) -> dict:
    """A computed value. With no inputs (e.g. a zero count) the dataset that
    was searched becomes the source, so "0 buys" still says where we looked."""
    if not inputs and searched:
        inputs = [searched]
    return {"label": label, "formula": formula, "inputs": inputs}


# ---- helpers ---------------------------------------------------------------

def _money(v: float | None) -> str:
    if v is None:
        return "—"
    a = abs(v)
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            return f"${v / div:,.2f}{suf}"
    return f"${v:,.0f}"


def _pct(v: float | None, signed: bool = True) -> str:
    return "—" if v is None else (f"{v:+.1f}%" if signed else f"{v:.1f}%")


def _is_new(d, days: int = NEW_DAYS) -> bool:
    if d is None:
        return False
    d = d if isinstance(d, date) else date.fromisoformat(str(d)[:10])
    return (date.today() - d).days <= days


# Standard us-gaap / srt names that read badly even after splitting.
_MEMBER_ALIAS = {
    "StatementGeographical": "Geography", "ProductOrService": "Product / service",
    "StatementBusinessSegments": "Segments", "ContractWithCustomerSalesChannel": "Sales channel",
    "ContractWithCustomerBasisOfPricing": "Pricing basis", "TimingOfTransferOfGoodOrService": "Timing of transfer",
    "TimingOfTransferOfGoodsOrServices": "Timing of transfer", "ConsolidationItems": "Consolidation items",
    "SalesChannelDirectlyToConsumer": "Direct to consumer", "SalesChannelThroughIntermediary": "Through intermediary",
    "TransferredAtPointInTime": "Point in time", "TransferredOverTime": "Over time",
}
_SMALL = {"and", "or", "of", "to", "the", "in", "for", "by", "with", "from", "at", "on", "excluding", "including"}
_TAIL = {"Channel", "Segment", "Segments", "Sector", "Region", "Domain"}


def _words(s: str) -> list[str]:
    """CamelCase -> words, keeping acronyms whole: "OEMsAndIoTDevices" -> OEMs And IoT Devices."""
    s = s.replace("IoT", "\0")
    toks = re.findall(r"\0|[A-Z]{2,}s(?![a-z])|[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+|[^\sA-Za-z\d]+", s)
    return ["IoT" if t == "\0" else t for t in toks]


def _member(m: str, axis: str | None = None) -> str:
    """Readable XBRL axis / member name: strip the prefix and Axis/Member/Domain
    suffixes, split CamelCase, drop a leading run of words repeated from the
    axis ("SalesChannelOther" on ContractWithCustomerSalesChannelAxis -> "Other"),
    lowercase connectors, keep acronyms. ISO codes (CN, EUR) pass through."""
    m = re.sub(r"^[a-z\-]+:", "", m or "")
    m = re.sub(r"(Member|Domain|Axis)+$", "", m) or m
    if m in _MEMBER_ALIAS:
        return _MEMBER_ALIAS[m]
    if m.isupper():
        return m
    if not axis:  # an axis title: drop the us-gaap namespace-ish prefixes
        m = re.sub(r"^(ContractWithCustomer|Statement)(?=[A-Z])", "", m)
    w = _words(m)
    if axis:
        aw = {x.lower() for x in _words(re.sub(r"(Axis|Member|Domain)+$", "", re.sub(r"^[a-z\-]+:", "", axis)))}
        k = 0
        while k < len(w) and w[k].lower() in aw:
            k += 1
        if k >= 2 and k < len(w):  # one shared word ("Product" Revenue) is content, not a repeat
            w = w[k:]
        while len(w) > 1 and w[-1] in _TAIL:
            w = w[:-1]
    out = [x.lower() if i and x.lower() in _SMALL else x for i, x in enumerate(w)]
    out[0] = out[0][:1].upper() + out[0][1:]
    return re.sub(r" ([^\sA-Za-z\d]+) ?", r"\1 ", " ".join(out)).strip()


class Filings:
    """accn -> (cik, primary_doc, form, filed) for one ticker, incl. predecessor CIKs."""

    def __init__(self, con, ticker: str):
        self.by_accn = {r[0]: r[1:] for r in con.execute(f"""
            SELECT accn, cik, primary_doc, form, filed FROM '{D}/events/filings.parquet'
            WHERE ticker = ?""", [ticker]).fetchall()}
        cs = universe.ciks(ticker)
        self.cik = cs[0] if cs else None

    def doc_url(self, accn: str, inline_xbrl: bool = False) -> str | None:
        if not accn:
            return None
        cik, doc, _, filed = self.by_accn.get(accn, (self.cik, None, None, None))
        if cik is None:
            return None
        if doc and inline_xbrl and filed and str(filed) >= "2019-06-15":
            return ixbrl(cik, accn, doc)
        return archive(cik, accn, doc)

    def form(self, accn: str) -> str:
        return (self.by_accn.get(accn) or (None, None, "filing"))[2] or "filing"


# ---- sections --------------------------------------------------------------

def sec_patents_(t: str, con) -> dict | None:
    P = D / "patents"
    if not (P / "patent_ticker.parquet").exists():
        return None
    con.execute(f"""CREATE OR REPLACE TEMP TABLE mine AS
        SELECT p.* FROM '{P}/patents.parquet' p SEMI JOIN
        (SELECT patent_id FROM '{P}/patent_ticker.parquet' WHERE ticker = $t) USING (patent_id)""", {"t": t})
    total = con.execute("SELECT count(*), max(date) FROM mine").fetchone()
    if not total[0]:
        return None
    match = src(f"PatentsView granted patents, assignee names matched to {t} (sources/patents.py; audit: patent_assignees view)", PV_URL)
    by_year = con.execute("SELECT year(date) y, count(*) FROM mine WHERE year(date) >= 2012 GROUP BY 1 ORDER BY 1").fetchall()
    pts = [{"x": str(y), "y": n, "src": derived(f"{t} grants in {y}", f"count(patent_id) where grant year = {y}", [match])}
           for y, n in by_year]
    blocks = [{"type": "kv", "rows": [
        {"label": "Granted US patents", "value": f"{total[0]:,} (thru {total[1]})", "src": match}]},
        {"type": "series", "title": "Grants per year", "unit": "patents", "points": pts}]
    if (P / "ai_by_ticker_year.parquet").exists():
        ai = con.execute(f"""SELECT year, n_patents, n_ai93, pct_ai93, n_ml FROM '{P}/ai_by_ticker_year.parquet'
                             WHERE ticker = ? AND year >= 2012 ORDER BY year""", [t]).fetchall()
        aipd = src("USPTO AI Patent Dataset 2023_r1 (model predictions, ≥0.93 any-AI)", AIPD_URL)
        blocks.append({"type": "series", "title": "AI share of grants (strict, thru 2023)", "unit": "%", "points": [
            {"x": str(y), "y": round(p or 0, 1),
             "src": derived(f"AI share {y}", f"{a93} AI-flagged / {n} grants", [aipd, match])} for y, n, a93, p, _ in ai]})
    wipo = con.execute(f"""SELECT w.wipo_field_title, count(*) n FROM mine m JOIN '{P}/wipo.parquet' w USING (patent_id)
                           WHERE m.date >= DATE '2023-01-01' GROUP BY 1 ORDER BY n DESC LIMIT 8""").fetchall()
    if wipo:
        blocks.append({"type": "bars", "title": "Technology mix, grants 2023+ (WIPO field)", "unit": "patents", "items": [
            {"label": f, "value": n, "src": derived(f"WIPO '{f}'", "count of 2023+ grants tagged with this field", [match])}
            for f, n in wipo]})
    recent = con.execute(f"""SELECT m.patent_id, m.date, m.title, c.cpc_subclass FROM mine m
        LEFT JOIN (SELECT patent_id, cpc_subclass FROM '{P}/cpc.parquet' WHERE cpc_sequence = 0) c USING (patent_id)
        ORDER BY m.date DESC, m.patent_id DESC LIMIT 12""").fetchall()
    blocks.append({"type": "table", "title": "Latest grants", "cols": ["granted", "title", "CPC"], "rows": [
        {"cells": [str(d), ti, c or ""], "new": _is_new(d, 90),
         "src": src(f"US{pid}", f"https://patents.google.com/patent/US{pid}")} for pid, d, ti, c in recent]})
    inv = con.execute(f"""SELECT i.name, count(*) n FROM mine m JOIN '{P}/inventors.parquet' i USING (patent_id)
        WHERE m.date >= DATE '2021-01-01' GROUP BY 1 ORDER BY n DESC LIMIT 8""").fetchall()
    if inv:
        blocks.append({"type": "bars", "title": "Most active inventors, grants 2021+", "unit": "patents", "items": [
            {"label": n or "(unnamed)", "value": k, "src": src(f"Google Patents: inventor {n}",
                                                f"https://patents.google.com/?inventor={quote(n or '')}&after=priority:20150101")}
            for n, k in inv]})
    return {"id": "patents", "title": "Patents", "blocks": blocks}


def profile_(t: str, prof: dict | None) -> dict | None:
    if not prof:
        return None
    y = src("Yahoo Finance profile", f"https://finance.yahoo.com/quote/{quote(t)}/profile")
    kv = [{"label": k, "value": v, "src": y} for k, v in (
        ("Sector / industry", f"{prof['sector']} / {prof['industry']}"), ("Country", prof["country"]),
        ("Employees", f"{prof['employees']:,}" if prof.get("employees") else None), ("Website", prof["website"])) if v]
    for o in json.loads(prof.get("officers") or "[]")[:4]:
        kv.append({"label": o.get("title") or "", "value": o.get("name") or "", "src": y})
    blocks = [{"type": "kv", "rows": kv}]
    if prof.get("summary"):
        blocks.append({"type": "text", "text": prof["summary"], "src": y})
    return {"id": "profile", "title": "Profile", "blocks": blocks}


FRESH = {  # source -> glob whose newest mtime is "last pulled"
    "events": "events/*.parquet", "earnings": "earnings/releases/*.parquet", "financials": "financials/facts/*.parquet",
    "segments": "segments/**/*.parquet", "insiders": "insiders/**/*.parquet", "filing_text": "filing_text/*.parquet",
    "patents": "patents/*.parquet", "profiles": "profiles/*.parquet", "tweets": "tweets/*.parquet",
}


def freshness() -> list[dict]:
    out = []
    for name, g in FRESH.items():
        files = list(D.glob(g))
        if files:
            out.append({"source": name, "pulled": datetime.fromtimestamp(max(f.stat().st_mtime for f in files)).isoformat(timespec="minutes")})
    h = list((sec_13f.DATA_DIR / "holdings").glob("*.parquet"))
    if h:
        out.append({"source": "13f", "pulled": datetime.fromtimestamp(max(f.stat().st_mtime for f in h)).isoformat(timespec="minutes")})
    return out


def _section(fn, *a, health: list | None = None, sid: str | None = None):
    """Run one section builder. Never raises; outcome goes to `health` as
    {section, status: ok|empty|error, rows, secs, error?, tb?}."""
    sid = sid or fn.__name__.strip("_")
    t0 = time.time()
    try:
        out = fn(*a)
    except Exception as e:  # one broken source shouldn't blank the screen
        if health is not None:
            health.append({"section": sid, "status": "error", "rows": 0, "secs": round(time.time() - t0, 3),
                           "error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()})
        return {"id": sid, "title": sid.replace("sec_", ""), "blocks": [
            {"type": "text", "text": f"error: {type(e).__name__}: {e}", "src": src("dossier.py", None, error=True)}]}
    if health is not None:
        rows = sum(len(b.get("rows", b.get("points", b.get("items", [])))) for b in (out or {}).get("blocks", []))
        health.append({"section": sid, "status": "ok" if out and rows else "empty", "rows": rows,
                       "secs": round(time.time() - t0, 3)})
    return out


def validate(d: dict) -> list[str]:
    """Paths of every value without a usable source (url, or formula + inputs)."""
    bad = []

    def ok(s):
        return isinstance(s, dict) and (s.get("url") or s.get("error") or s.get("internal")
                                        or (s.get("formula") and s.get("inputs")))

    for sec in d["sections"]:
        for bi, b in enumerate(sec["blocks"]):
            items = {"kv": "rows", "table": "rows", "series": "points", "bars": "items"}.get(b["type"])
            for ii, it in enumerate(b.get(items, []) if items else [b]):
                if not ok(it.get("src")):
                    bad.append(f"{sec['id']}.{bi}.{b['type']}[{ii}]")
    return bad


HEALTH_LOG = D / "debug" / "dossier_health.jsonl"


def _log_health(t: str, d: dict) -> None:
    """Append non-ok sections and unsourced paths for t (one JSON line per build)."""
    bad = [h for h in d["health"] if h["status"] != "ok"]
    if not bad and not d["unsourced"]:
        return
    HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with HEALTH_LOG.open("a") as f:
        f.write(json.dumps({"ticker": t, "built_at": d["built_at"], "health": bad, "unsourced": d["unsourced"]}) + "\n")


def debug_report(tickers: list[str], verbose: bool = False) -> None:
    """Build each ticker (no cache write) and print a ticker x section status grid."""
    ids, grid = [], {}
    for t in tickers:
        d = build(t)
        grid[t] = d
        for h in d["health"]:
            if h["section"] not in ids:
                ids.append(h["section"])
    sym = {"ok": ".", "empty": "-", "error": "E"}
    print(f"{'ticker':8}" + " ".join(i.replace("sec_", "")[:5].ljust(5) for i in ids) + "  unsrc")
    for t, d in grid.items():
        st = {h["section"]: h for h in d["health"]}
        print(f"{t:8}" + " ".join(sym[st[i]["status"]].ljust(5) if i in st else "?".ljust(5) for i in ids) + f"  {len(d['unsourced'])}")
        for h in d["health"]:
            if h["status"] == "error":
                print(f"    {h['section']}: {h['error']}")
                if verbose:
                    print("      " + h["tb"].strip().replace("\n", "\n      "))
    n = len(grid)
    print(f"\n{n} tickers   (. ok  - empty  E error)")
    for i in ids:
        c = {k: sum(1 for d in grid.values() for h in d["health"] if h["section"] == i and h["status"] == k) for k in sym}
        print(f"  {i:16} ok={c['ok']:4} empty={c['empty']:4} error={c['error']:4}")


def build(ticker: str) -> dict:
    t = ticker.upper()
    con = duckdb.connect()
    F = Filings(con, t)
    pf = D / "profiles" / "profiles.parquet"
    prof = None
    if pf.exists():
        r = con.execute(f"SELECT * FROM '{pf}' WHERE ticker = ?", [t]).fetchone()
        prof = dict(zip([c[0] for c in con.description], r)) if r else None
    name = (prof or {}).get("long_name") or next((s["name"] for s in universe.rows() if s["ticker"] == t), t)
    health: list[dict] = []
    from derive.dossier_tabs import TAB_BUILDERS  # lazy: tab modules import helpers from this file
    sections = [s for s in (
        [_section(fn, t, con, F, prof, health=health, sid=sid) for sid, fn in TAB_BUILDERS]
        + [_section(sec_patents_, t, con, health=health), _section(profile_, t, prof, health=health)]) if s]
    for s in sections:
        rows = [it for b in s["blocks"] for it in b.get("rows", [])]
        s["new"] = any(it.get("new") for it in rows)
        n_new = sum(1 for it in rows if it.get("new"))
        s["badge"] = str(n_new) if n_new else ""
    d = {"ticker": t, "name": name,
         "industry": (prof or {}).get("industry"), "country": (prof or {}).get("country"),
         "market_cap": (prof or {}).get("market_cap"), "employees": (prof or {}).get("employees"),
         "header_src": src("Yahoo Finance profile", f"https://finance.yahoo.com/quote/{quote(t)}/profile"),
         "built_at": datetime.now().isoformat(timespec="seconds"), "freshness": freshness(), "sections": sections, "health": health}
    d["unsourced"] = validate(d)
    _log_health(t, d)
    con.close()
    return d


def _is_stale(t: str, hours: float) -> bool:
    """True if t has no cached dossier, it's older than `hours`, or any
    source was pulled after it was built."""
    con = db._conn()
    try:
        r = con.execute("SELECT fetched_at FROM dossier_cache WHERE symbol = ?", [t]).fetchone()
    finally:
        con.close()
    if not r:
        return True
    built = datetime.fromtimestamp(r[0])
    if time.time() - r[0] > hours * 3600:
        return True
    return any(datetime.fromisoformat(f["pulled"]) > built for f in freshness())


def main(argv: list[str]) -> None:
    as_json = "--json" in argv
    if "--debug" in argv:
        ts = [x["ticker"] for x in universe.rows()] if "--all" in argv else [a.upper() for a in argv if not a.startswith("--")]
        return debug_report(ts, verbose="-v" in argv or "--verbose" in argv)
    # --if-stale H: rebuild only if missing / older than H hours / older than
    # the data; prints one JSON status line per ticker (for init.lua `run`).
    stale_h = next((float(argv[i + 1]) for i, a in enumerate(argv[:-1]) if a == "--if-stale"), None)
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and not (i and argv[i - 1] == "--if-stale")]
    tickers = [s["ticker"] for s in universe.rows()] if "--all" in argv else [a.upper() for a in args]
    for t in tickers:
        if stale_h is not None and not _is_stale(t, stale_h):
            print(json.dumps({"ticker": t, "rebuilt": False}), flush=True)
            continue
        t0 = time.time()
        d = build(t)
        db.put_cached_dossier(t, d)
        if as_json:
            print(json.dumps(d, default=str))
        elif stale_h is not None:
            print(json.dumps({"ticker": t, "rebuilt": True, "unsourced": len(d["unsourced"])}), flush=True)
        else:
            print(f"{t}: {len(d['sections'])} sections, {sum(len(b.get('rows', b.get('points', b.get('items', [])))) for s in d['sections'] for b in s['blocks'])} values, "
                  f"unsourced={len(d['unsourced'])} {d['unsourced'][:5]} ({time.time() - t0:.2f}s)", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
