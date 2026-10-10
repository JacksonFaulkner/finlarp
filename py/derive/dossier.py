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
    python py/derive/dossier.py --all         # every ticker in the universe
    python py/derive/dossier.py MRVL --if-stale 12   # rebuild only if stale; JSON status (nvim)
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from urllib.parse import quote

import duckdb


from core import db
from sources import sec_13f, sec_earnings, sec_events, sec_financials, sec_insiders, sec_segments, universe, yahoo, yahoo_profile

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

def sec_events_(t: str, F: Filings) -> dict:
    rows = []
    for e in sec_events.recent_events(t, 180, "high")[:20]:
        rows.append({"cells": [str(e["filed"]), e["item"], e["label"]], "new": _is_new(e["filed"]),
                     "src": src(f"{e['form']} {e['filed']} item {e['item']}",
                                F.doc_url(e["accn"]) or archive(F.cik, e["accn"], e.get("primary_doc")))})
    return {"id": "events", "title": "Events", "blocks": [
        {"type": "table", "title": "8-K high-signal items, 180 days", "cols": ["filed", "item", "what"], "rows": rows}]}


def sec_earnings_(t: str, _F: Filings) -> dict | None:
    r = sec_earnings.latest(t)
    if not r:
        return None
    doc = archive(r["cik"], r["accn"], r.get("doc_name"))
    base = f"{r['form']} {r['filed']} {r.get('doc_name') or ''}".strip()
    new = _is_new(r["filed"])
    h = r.get("headline")
    h = json.loads(h) if isinstance(h, str) else (h or {})
    kv = []
    for key, label in (("revenue", "Revenue"), ("eps_gaap", "EPS GAAP"), ("eps_nongaap", "EPS non-GAAP")):
        x = h.get(key)
        if x and x.get("value") is not None:
            val = f"{x.get('ccy') or ''}{x['value']:,}{(' ' + x['unit']) if x.get('unit') else ''}"
            kv.append({"label": label, "value": val, "new": new,
                       "src": src(f"{base} · \"{(x.get('snippet') or '')[:70]}\"", fragment(doc, x.get("snippet")))})
    guid = [{"cells": [g.lstrip("•· ").strip()], "new": new, "src": src(base, fragment(doc, g))}
            for g in (r.get("guidance") or [])[:14]]
    blocks = [{"type": "kv", "rows": kv}] if kv else []
    if guid:
        blocks.append({"type": "table", "title": "Guidance (as written in the release)", "cols": ["line"], "rows": guid})
    return {"id": "earnings", "title": "Earnings & guidance", "blocks": blocks}


def sec_revenue_(t: str, F: Filings, con) -> dict:
    def fact_src(r: dict, period: str) -> dict:
        return src(f"{F.form(r['accn'])} filed {r['filed']} · {r['concept']} · {period}",
                   F.doc_url(r["accn"], inline_xbrl=True))

    annual = sec_financials.annual_series(t, "revenue")[-6:]
    quarterly = sec_financials.quarterly_series(t, "revenue")[-9:]

    def q_label(q: dict) -> str:
        return f"Q{q['fq']} FY{q['fy']}" if q.get("fq") else f"quarter ending {q['end']}"

    def q_short(q: dict) -> str:
        return f"Q{q['fq']}'{str(q['fy'])[2:]}" if q.get("fq") else str(q["end"])[:7]

    def q_src(q: dict) -> dict:
        if not q.get("derived"):
            return fact_src(q, q_label(q))
        parts = q.get("derived_from") or []
        inputs = [fact_src(p, f"{p['start']}..{p['end']}") for p in parts]
        formula = " − ".join(f"[{p['start']}..{p['end']}] {p['val'] / 1e6:,.1f}" for p in parts) or "longer period − shorter period"
        return derived(f"{q_label(q)} derived: no discrete quarterly fact filed", formula, inputs)

    a_pts = [{"x": f"FY{a['fy']}", "y": round(a["val"] / 1e6, 1), "src": fact_src(a, f"FY{a['fy']}")} for a in annual[-5:]]
    q_pts = [{"x": q_short(q), "y": round(q["val"] / 1e6, 1), "src": q_src(q)} for q in quarterly[-8:]]
    kv = []
    if quarterly:
        q = quarterly[-1]
        kv.append({"label": f"Latest {q_label(q)}", "value": _money(q["val"]), "src": q_src(q)})
        prev = next((x for x in quarterly if q.get("fy") and x["fy"] == q["fy"] - 1 and x["fq"] == q["fq"]), None)
        if prev and prev["val"]:
            g = (q["val"] / prev["val"] - 1) * 100
            kv.append({"label": "  YoY", "value": _pct(g), "src": derived(
                "YoY growth", f"{q['val'] / 1e6:,.1f} / {prev['val'] / 1e6:,.1f} − 1", [q_src(q), q_src(prev)])})
    if len(annual) >= 2 and annual[-2]["val"]:
        a, b = annual[-1], annual[-2]
        kv.append({"label": f"FY{a['fy']}", "value": _money(a["val"]), "src": fact_src(a, f"FY{a['fy']}")})
        kv.append({"label": "  YoY", "value": _pct((a["val"] / b["val"] - 1) * 100), "src": derived(
            "YoY growth", f"{a['val'] / 1e6:,.1f} / {b['val'] / 1e6:,.1f} − 1",
            [fact_src(a, f"FY{a['fy']}"), fact_src(b, f"FY{b['fy']}")])})

    blocks = [{"type": "kv", "rows": kv},
              {"type": "series", "title": "Quarterly revenue", "unit": "$M", "points": q_pts},
              {"type": "series", "title": "Annual revenue", "unit": "$M", "points": a_pts}]
    seg = con.execute(f"""
        WITH s AS (SELECT * FROM read_parquet('{sec_segments.facts_glob()}', union_by_name=true)
                   WHERE ticker = ? AND axis <> '' AND period_start IS NOT NULL
                     AND date_diff('day', period_start, period_end) > 300
                     AND concept NOT ILIKE '%OperatingIncome%'),
             latest AS (SELECT axis, max(period_end) pe FROM s GROUP BY 1)
        SELECT s.axis, s.member, s.period_end, s.value, s.accn, s.concept FROM s JOIN latest l
          ON s.axis = l.axis AND s.period_end = l.pe
        QUALIFY row_number() OVER (PARTITION BY s.axis, s.member ORDER BY s.value DESC) = 1
        ORDER BY s.axis, s.value DESC""", [t]).fetchall()
    by_axis: dict[str, list] = {}
    for axis, member, pe, val, accn, concept in seg:
        by_axis.setdefault(axis, []).append((member, pe, val, accn, concept))
    for axis, items in by_axis.items():
        if len(items) < 2 or axis == "StatementBusinessSegmentsAxis":
            continue
        blocks.append({"type": "bars", "title": f"{_member(axis)} (FY ending {items[0][1]})",
                       "unit": "$M", "items": [
            {"label": _member(m, axis), "value": round(v / 1e6, 1),
             "src": src(f"{F.form(a)} · {c} · {axis}={m}", F.doc_url(a, inline_xbrl=True))}
            for m, _, v, a, c in items[:8]]})
    return {"id": "revenue", "title": "Revenue & segments", "blocks": blocks}


def sec_holders_(t: str, con) -> dict | None:
    cmap = D.parent / "sec_13f" / "cusip_map.parquet"
    cusips = [r[0] for r in con.execute(f"SELECT cusip FROM '{cmap}' WHERE ticker = ?", [t]).fetchall()]
    if not cusips:
        return None
    con.execute(f"CREATE OR REPLACE TEMP TABLE h AS SELECT * FROM {sec_13f.holdings_sql()} WHERE list_contains($c, cusip)",
                {"c": cusips})
    periods = [r[0] for r in con.execute("SELECT DISTINCT period FROM h ORDER BY 1 DESC LIMIT 2").fetchall()]
    if len(periods) < 2:
        return None
    cur, prev = periods
    fdir = sec_13f.DATA_DIR / "filings"
    rows = con.execute(f"""
        WITH f AS (SELECT cik, period FROM read_parquet('{fdir}/*.parquet')
                   WHERE subtype IN ('13F-HR', '13F-HR/A') AND period IN ($prev, $cur)),
        panel AS (SELECT cik FROM f WHERE period = $prev INTERSECT SELECT cik FROM f WHERE period = $cur),
        ranked AS (SELECT *, max(sh) FILTER (WHERE rn = 2) OVER (PARTITION BY cusip, period) runner_up
                   FROM (SELECT *, row_number() OVER (PARTITION BY cusip, period ORDER BY sh DESC) rn FROM h)),
        clean AS (SELECT * FROM ranked WHERE NOT coalesce(rn = 1 AND sh > {sec_13f.SUSPECT_MULTIPLE} * runner_up, false)
                  AND period IN ($prev, $cur) AND cik IN (SELECT cik FROM panel))
        SELECT cik, any_value(mgr), sum(sh) FILTER (WHERE period = $prev), sum(sh) FILTER (WHERE period = $cur),
               min(acc) FILTER (WHERE period = $prev), min(acc) FILTER (WHERE period = $cur)
        FROM clean GROUP BY cik""", {"prev": prev, "cur": cur}).fetchall()
    # `is not None`, not truthiness: a reported 0-share line still counts as a holder (matches sec_13f.summary).
    holders_prev = sum(1 for r in rows if r[2] is not None); holders = sum(1 for r in rows if r[3] is not None)
    new_pos = sum(1 for r in rows if r[3] is not None and r[2] is None)
    exited = sum(1 for r in rows if r[2] is not None and r[3] is None)
    sh_prev = sum(r[2] or 0 for r in rows); sh_cur = sum(r[3] or 0 for r in rows)
    method = (f"13F-HR filings for periods {prev} and {cur}; only managers that filed both periods; "
              f"CUSIPs {', '.join(cusips)}; top holder dropped if >{sec_13f.SUSPECT_MULTIPLE}× runner-up (typo filter)")
    ds = [src(f"SEC Form 13F data sets ({p})", F13_URL) for p in (prev, cur)]
    kv = [
        {"label": "Holders", "value": f"{holders_prev:,} → {holders:,} ({_pct((holders / holders_prev - 1) * 100 if holders_prev else None)})",
         "src": derived("count of managers holding", method, ds)},
        {"label": "New / exited positions", "value": f"{new_pos:,} / {exited:,}", "src": derived("new = held now not before", method, ds)},
        {"label": "Shares held", "value": f"{sh_prev / 1e6:,.1f}M → {sh_cur / 1e6:,.1f}M ({_pct((sh_cur / sh_prev - 1) * 100 if sh_prev else None)})",
         "src": derived("sum of reported shares", method, ds)},
    ]

    def mover(r):
        cik, mgr, a, b, acc_a, acc_b = r
        acc = acc_b or acc_a
        return {"cells": [mgr or str(cik), "new" if a is None else f"{a / 1e6:,.2f}M", "exited" if b is None else f"{b / 1e6:,.2f}M", f"{((b or 0) - (a or 0)) / 1e6:+,.2f}M"],
                "src": src(f"13F-HR {cur if acc_b else prev} · {mgr}", archive(cik, acc),
                           **({"inputs": [src(f"13F-HR {prev}", archive(cik, acc_a))]} if acc_a and acc_b else {}))}
    moves = sorted(rows, key=lambda r: (r[3] or 0) - (r[2] or 0))
    top_in = [mover(r) for r in moves[::-1][:8] if (r[3] or 0) > (r[2] or 0)]
    top_out = [mover(r) for r in moves[:8] if (r[3] or 0) < (r[2] or 0)]
    cols = ["manager", str(prev), str(cur), "Δ shares"]
    return {"id": "holders", "title": "Institutions (13F)", "blocks": [
        {"type": "kv", "rows": kv},
        {"type": "table", "title": "Biggest adds", "cols": cols, "rows": top_in},
        {"type": "table", "title": "Biggest cuts", "cols": cols, "rows": top_out}]}


def sec_insiders_(t: str, F: Filings) -> dict:
    tx = sec_insiders.open_market(t, date.today() - timedelta(days=365))
    rows, srcs = [], []
    for x in tx[:25]:
        s = src(f"Form {x['form']} filed {x['filed']} · {x['owner_name']}", archive(F.cik, x["accn"]))
        srcs.append(s)
        rows.append({"cells": [str(x["trans_date"]), x["owner_name"], x.get("officer_title") or x.get("relationship") or "",
                               "BUY" if x["code"] == "P" else "sell", f"{x['shares'] or 0:,.0f}",
                               f"${x['price']:,.2f}" if x.get("price") is not None else "—",
                               _money(x["value"]), "10b5-1" if x.get("is_10b5_1") else ""],
                     "new": _is_new(x["filed"]), "src": s})
    buys = [x for x in tx if x["code"] == "P"]; sells = [x for x in tx if x["code"] == "S"]
    disc = [x for x in sells if not x.get("is_10b5_1")]
    all_src = [src(f"Form {x['form']} {x['filed']} · {x['owner_name']}", archive(F.cik, x["accn"])) for x in tx]
    ins_ds = src(f"SEC insider transactions data sets, {t}, last 365 days", INSIDER_URL)
    kv = [
        {"label": "Open-market buys (365d)", "value": f"{len(buys)} · {_money(sum(x['value'] or 0 for x in buys))}",
         "src": derived("sum of Form 4 code P", "Σ value of non-derivative code-P transactions", [s for s, x in zip(all_src, tx) if x["code"] == "P"], ins_ds)},
        {"label": "Sales (365d)", "value": f"{len(sells)} · {_money(sum(x['value'] or 0 for x in sells))}",
         "src": derived("sum of Form 4 code S", "Σ value of non-derivative code-S transactions", [s for s, x in zip(all_src, tx) if x["code"] == "S"], ins_ds)},
        {"label": "  discretionary (not 10b5-1)", "value": _money(sum(x["value"] or 0 for x in disc)),
         "src": derived("code S without a 10b5-1 plan flag", "Σ value where is_10b5_1 = false",
                        [s for s, x in zip(all_src, tx) if x["code"] == "S" and not x.get("is_10b5_1")], ins_ds)},
    ]
    return {"id": "insiders", "title": "Insiders", "blocks": [
        {"type": "kv", "rows": kv},
        {"type": "table", "title": "Open-market transactions (bulk data lags 0–3 months)",
         "cols": ["date", "who", "role", "", "shares", "price", "value", "plan"], "rows": rows}]}


def sec_risks_(t: str, F: Filings, con) -> dict | None:
    ar = con.execute(f"""
        SELECT accn, form, filed, risk_added, risk_removed, risk_factor_count, ai_mentions
        FROM '{D}/filing_text/filings.parquet' WHERE ticker = ? AND parse_ok ORDER BY filed DESC LIMIT 1""", [t]).fetchone()
    if not ar:
        return None
    accn, form, filed, added, removed, _, ai = ar
    doc = F.doc_url(accn)
    s10k = src(f"{form} filed {filed}", doc)
    kv = [{"label": "Risk sentences added / removed vs prior year", "value": f"{added} / {removed}",
           "new": _is_new(filed, 60), "src": derived("sentence diff of Item 1A", "sentences in this 1A not in prior-year 1A",
                                                       [s10k])},
          {"label": "AI mentions in annual report", "value": f"{ai}", "src": s10k}]
    sents = con.execute(f"""
        SELECT sentence, novelty FROM '{D}/filing_text/risk_diff.parquet'
        WHERE ticker = ? AND accn = ? AND kind = 'added' ORDER BY novelty DESC NULLS LAST LIMIT 12""", [t, accn]).fetchall()
    rows = [{"cells": [s], "new": _is_new(filed, 60), "src": src(f"{form} {filed} · Item 1A", fragment(doc, s))} for s, _ in sents]
    return {"id": "risks", "title": "New risk factors", "blocks": [
        {"type": "kv", "rows": kv},
        {"type": "table", "title": f"Most novel added sentences ({form} {filed})", "cols": ["sentence"], "rows": rows}]}


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


EST_MODULES = "earningsTrend,earningsHistory,recommendationTrend,upgradeDowngradeHistory,financialData"
EST_PERIODS = {"0q": "Current quarter", "+1q": "Next quarter", "0y": "Current year", "+1y": "Next year"}


def _raw(f):
    return f.get("raw") if isinstance(f, dict) else f


def _n(v, fmt: str = "{:,.2f}") -> str:
    return "—" if v is None else fmt.format(v)


def estimates_(t: str) -> dict | None:
    """Analyst consensus from Yahoo Finance (the Analysis page): EPS and
    revenue estimates by period, how they have been revised, price targets,
    the rating mix, and recent upgrades / downgrades."""
    session = yahoo.new_session()
    res = yahoo_profile.fetch(session, t, EST_MODULES)
    if not res:
        return None
    url = f"https://finance.yahoo.com/quote/{quote(t)}/analysis/"
    y = lambda what: src(f"Yahoo Finance analysis · {what}", url)  # noqa: E731
    blocks = []

    fd = res.get("financialData") or {}
    price, mean_t = _raw(fd.get("currentPrice")), _raw(fd.get("targetMeanPrice"))
    kv = []
    if fd.get("recommendationKey"):
        kv.append({"label": "Consensus rating", "value": f"{fd['recommendationKey']} "
                   f"(mean {_n(_raw(fd.get('recommendationMean')), '{:.2f}')} of 5, "
                   f"{_n(_raw(fd.get('numberOfAnalystOpinions')), '{:.0f}')} analysts)", "src": y("financialData.recommendationKey")})
    for key, label in (("targetLowPrice", "Target low"), ("targetMeanPrice", "Target mean"),
                       ("targetMedianPrice", "Target median"), ("targetHighPrice", "Target high")):
        if _raw(fd.get(key)) is not None:
            kv.append({"label": label, "value": f"${_raw(fd[key]):,.2f}", "src": y(f"financialData.{key}")})
    if price and mean_t:
        up = (mean_t / price - 1) * 100
        kv.append({"label": "Upside to mean target", "value": _pct(up), "src": derived(
            "Upside to mean analyst target", f"({mean_t:,.2f} / {price:,.2f} − 1) × 100 = {up:+.1f}%",
            [y("financialData.targetMeanPrice"), y("financialData.currentPrice")])})
    if kv:
        blocks.append({"type": "kv", "title": "Consensus", "rows": kv})

    trend = {p["period"]: p for p in (res.get("earningsTrend") or {}).get("trend", []) if p.get("period") in EST_PERIODS}
    eps_rows, rev_rows, rev_trend_rows = [], [], []
    for per, label in EST_PERIODS.items():
        p = trend.get(per)
        if not p:
            continue
        e, r, tr = p.get("earningsEstimate") or {}, p.get("revenueEstimate") or {}, p.get("epsTrend") or {}
        name = f"{label} (ends {p.get('endDate') or '?'})"
        if _raw(e.get("avg")) is not None:
            eps_rows.append({"cells": [name, _n(_raw(e.get("avg"))), _n(_raw(e.get("low"))), _n(_raw(e.get("high"))),
                                       _n(_raw(e.get("yearAgoEps"))), _pct(_raw(e.get("growth")) * 100 if _raw(e.get("growth")) is not None else None),
                                       _n(_raw(e.get("numberOfAnalysts")), "{:.0f}")],
                             "src": y(f"earningsTrend[{per}].earningsEstimate")})
        if _raw(r.get("avg")) is not None:
            rev_rows.append({"cells": [name, _money(_raw(r.get("avg"))), _money(_raw(r.get("low"))), _money(_raw(r.get("high"))),
                                       _money(_raw(r.get("yearAgoRevenue"))), _pct(_raw(r.get("growth")) * 100 if _raw(r.get("growth")) is not None else None),
                                       _n(_raw(r.get("numberOfAnalysts")), "{:.0f}")],
                             "src": y(f"earningsTrend[{per}].revenueEstimate")})
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
    if eps_rows:
        blocks.append({"type": "table", "title": "EPS estimates", "cols": ["period", "avg", "low", "high", "year ago", "growth", "analysts"], "rows": eps_rows})
    if rev_rows:
        blocks.append({"type": "table", "title": "Revenue estimates", "cols": ["period", "avg", "low", "high", "year ago", "growth", "analysts"], "rows": rev_rows})
    if rev_trend_rows:
        blocks.append({"type": "table", "title": "EPS estimate revisions (change since)",
                       "cols": ["period", "now", "7d ago", "30d ago", "90d ago"], "rows": rev_trend_rows})

    hist = [h for h in (res.get("earningsHistory") or {}).get("history", []) if _raw(h.get("epsActual")) is not None]
    if hist:
        blocks.append({"type": "table", "title": "EPS vs estimate, last quarters", "cols": ["quarter", "actual", "estimate", "surprise"],
                       "rows": [{"cells": [(h.get("quarter") or {}).get("fmt") or "?", _n(_raw(h.get("epsActual"))), _n(_raw(h.get("epsEstimate"))),
                                           _pct(_raw(h.get("surprisePercent")) * 100 if _raw(h.get("surprisePercent")) is not None else None)],
                                 "src": y("earningsHistory")} for h in hist]})

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
    return {"id": "estimates", "title": "Analyst estimates", "blocks": blocks} if blocks else None


# ---- assembly --------------------------------------------------------------

FRESH = {  # source -> glob whose newest mtime is "last pulled"
    "events": "events/*.parquet", "earnings": "earnings/releases/*.parquet", "financials": "financials/facts/*.parquet",
    "segments": "segments/**/*.parquet", "insiders": "insiders/**/*.parquet", "filing_text": "filing_text/*.parquet",
    "patents": "patents/*.parquet", "profiles": "profiles/*.parquet",
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


def _section(fn, *a):
    try:
        return fn(*a)
    except Exception as e:  # one broken source shouldn't blank the screen
        return {"id": fn.__name__.strip("_"), "title": fn.__name__.strip("_").replace("sec_", ""), "blocks": [
            {"type": "text", "text": f"error: {type(e).__name__}: {e}", "src": src("dossier.py", None, error=True)}]}


def validate(d: dict) -> list[str]:
    """Paths of every value without a usable source (url, or formula + inputs)."""
    bad = []

    def ok(s):
        return isinstance(s, dict) and (s.get("url") or s.get("error") or (s.get("formula") and s.get("inputs")))

    for sec in d["sections"]:
        for bi, b in enumerate(sec["blocks"]):
            items = {"kv": "rows", "table": "rows", "series": "points", "bars": "items"}.get(b["type"])
            for ii, it in enumerate(b.get(items, []) if items else [b]):
                if not ok(it.get("src")):
                    bad.append(f"{sec['id']}.{bi}.{b['type']}[{ii}]")
    return bad


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
    sections = [s for s in (
        _section(sec_events_, t, F), _section(sec_earnings_, t, F), _section(sec_revenue_, t, F, con),
        _section(sec_holders_, t, con), _section(sec_insiders_, t, F), _section(sec_risks_, t, F, con),
        _section(sec_patents_, t, con), _section(estimates_, t), _section(profile_, t, prof)) if s]
    for s in sections:
        rows = [it for b in s["blocks"] for it in b.get("rows", [])]
        s["new"] = any(it.get("new") for it in rows)
        n_new = sum(1 for it in rows if it.get("new"))
        s["badge"] = str(n_new) if n_new else ""
    d = {"ticker": t, "name": name,
         "industry": (prof or {}).get("industry"), "country": (prof or {}).get("country"),
         "market_cap": (prof or {}).get("market_cap"), "employees": (prof or {}).get("employees"),
         "header_src": src("Yahoo Finance profile", f"https://finance.yahoo.com/quote/{quote(t)}/profile"),
         "built_at": datetime.now().isoformat(timespec="seconds"), "freshness": freshness(), "sections": sections}
    d["unsourced"] = validate(d)
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
