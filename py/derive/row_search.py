"""Row search: one searchable table per structured dataset, for the data
sources screen (Enter on a dataset tile opens tui/src/screens/rows.rs).

Each dataset is a SQL source plus a short spec: the columns to show, which
column is the ticker and which the date, the text columns free words search,
and named field filters. Rows come back formatted (dates, $1.2B, 3.4M) so the
screen only lays them out. Rows with an accession number carry a SEC url,
the primary document when the filing index has it, the filing index if not.

Query syntax, free text and filters in any order:
    t:NVDA,AMD         ticker(s)
    since:2025         date on or after (YYYY, YYYY-MM or YYYY-MM-DD)
    until:2026-06      date before
    <field>:value      a dataset's own filters (code:P, mgr:vanguard, ...);
                       comma = any of; listed per dataset in `fields`
    "exact phrase"     must appear in one of the text columns
    -word              must not appear in any text column
    bare words         every word must appear in some text column
No query at all = the newest rows.

CLI:
    row_search.py list                         datasets as JSON
    row_search.py q DATASET QUERY... [-k N]    one query, JSON
    row_search.py --serve                      JSON-lines server for the TUI

--serve protocol: one JSON object per line on stdin, one reply per line on
stdout, echoing "id".
    {"id": 1, "ds": "insiders", "q": "t:NVDA code:S", "k": 200}
        -> {"id": 1, "title": ..., "columns": [{"name", "kind"}], "rows": [{"cells": [...],
            "url": ..., "detail": [[label, value], ...]}], "more": bool, "fields": [...], "ms": 40}
    any failure -> {"id": n, "error": "..."}
"""
from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime

import duckdb

from sources import sec_13f, sec_insiders, sec_segments, universe

D = universe.DATA_ROOT
_FILTER = re.compile(r'(\w+):("[^"]*"|\S+)')

# Form 3/4/5 transaction codes worth naming; the rest show as the bare code.
CODES = {"P": "buy", "S": "sale", "A": "award", "M": "exercise", "F": "tax", "G": "gift",
         "C": "convert", "D": "to issuer", "X": "exercise", "J": "other", "W": "will"}


@dataclass
class Col:
    expr: str
    name: str
    kind: str = "text"  # text | date | int | num | money | price | bool


@dataclass
class Dataset:
    key: str
    title: str
    src: str  # FROM clause; aliased as r
    cols: list[Col]
    date: str  # expression for since/until and the default order
    text: list[str]  # free-text search columns
    ticker: str | None = "r.ticker"
    accn: str | None = "r.accn"
    order: str = ""  # tiebreak after the date
    fields: dict[str, tuple[str, str]] = field(default_factory=dict)  # name -> (expr, "eq" | "prefix" | "contains")
    # Built once into a temp table on first use (slow joins over big parquet).
    materialize: bool = False
    hint: str = ""


def _insider_cols() -> list[Col]:
    return [
        Col("r.filed", "filed", "date"),
        Col("r.ticker", "ticker"),
        Col("r.owner_name", "insider"),
        Col("coalesce(nullif(r.officer_title, ''), r.relationship)", "role"),
        Col("r.code", "code"),
        Col("r.shares", "shares", "num"),
        Col("r.price", "price", "price"),
        Col("r.value", "value", "money"),
        Col("r.shares_owned_after", "owned after", "num"),
        Col("r.is_10b5_1", "10b5-1", "bool"),
    ]


_INSIDER_FIELDS = {
    "code": ("r.code", "eq"),
    "owner": ("r.owner_name", "contains"),
    "role": ("coalesce(r.officer_title, '') || ' ' || coalesce(r.relationship, '')", "contains"),
    "form": ("r.form", "prefix"),
    "plan": ("CASE WHEN r.is_10b5_1 THEN 'yes' ELSE 'no' END", "eq"),
}


def datasets() -> dict[str, Dataset]:
    live = sec_insiders.DATA_DIR / "live_form4.ndjson"
    ciks = ", ".join(f"({int(s['cik'])}, '{s['ticker']}')" for s in universe.stocks() if s.get("cik"))
    out = [
        Dataset(
            "insiders", "Insider Forms 3/4/5",
            sec_insiders.tx_sql() + " r", _insider_cols(), "r.filed",
            ["r.owner_name", "r.officer_title", "r.relationship", "r.security_title", "r.nature"],
            fields=_INSIDER_FIELDS, order="r.value DESC NULLS LAST",
            hint="code:P buys · code:S sales · plan:no discretionary · owner:huang",
        ),
        Dataset(
            "form4_live", "Form 4 live XML",
            f"(SELECT unnest(rows, recursive := true) FROM read_json('{live}', format='newline_delimited',"
            f" maximum_object_size=67108864)) r",
            _insider_cols(), "r.filed",
            ["r.owner_name", "r.officer_title", "r.relationship", "r.security_title"],
            fields=_INSIDER_FIELDS, order="r.value DESC NULLS LAST",
            hint="filings since the last bulk set · code:P buys · owner:name",
        ),
        Dataset(
            "13f", "13F institutional holdings",
            f"""(SELECT m.ticker, h.mgr, h.cik, h.period, h.sh, h.val, h.acc AS accn,
                        h.sh - lag(h.sh) OVER (PARTITION BY h.cik, m.ticker ORDER BY h.period) AS chg
                 FROM {sec_13f.holdings_sql()} h
                 JOIN (SELECT DISTINCT ticker, cusip FROM '{sec_13f.DATA_DIR}/cusip_map.parquet'
                       WHERE cusip IS NOT NULL) m USING (cusip)) r""",
            [Col("r.period", "period", "date"), Col("r.ticker", "ticker"), Col("r.mgr", "manager"),
             Col("r.sh", "shares", "num"), Col("r.chg", "Δ shares", "num"), Col("r.val", "value", "money")],
            "r.period", ["r.mgr"], order="r.val DESC NULLS LAST",
            fields={"mgr": ("r.mgr", "contains"), "period": ("CAST(r.period AS VARCHAR)", "prefix")},
            materialize=True, hint="universe tickers only · mgr:vanguard · t:NVDA",
        ),
        Dataset(
            "facts", "XBRL companyfacts",
            f"""(SELECT f.*, c.label FROM read_parquet('{D}/financials/facts/*.parquet', union_by_name=true) f
                 LEFT JOIN '{D}/financials/concepts.parquet' c USING (taxonomy, concept)) r""",
            [Col("r.filed", "filed", "date"), Col("r.ticker", "ticker"),
             Col("coalesce(r.label, r.concept)", "concept"), Col("r.fy || ' ' || r.fp", "period"),
             Col("r.\"end\"", "as of", "date"), Col("r.val", "value", "num"), Col("r.unit", "unit"),
             Col("r.form", "form")],
            "r.filed", ["r.concept", "r.label"],
            fields={"concept": ("r.concept", "contains"), "form": ("r.form", "prefix"),
                    "fy": ("CAST(r.fy AS VARCHAR)", "eq"), "fp": ("r.fp", "eq"), "unit": ("r.unit", "eq"),
                    "tax": ("r.taxonomy", "eq")},
            order="r.ticker, r.concept",
            hint="revenue · t:MRVL fy:2026 · concept:ResearchAndDevelopment",
        ),
        Dataset(
            "segments", "Segment and geography revenue",
            f"read_parquet('{sec_segments.facts_glob()}', union_by_name=true) r",
            [Col("r.filing_date", "filed", "date"), Col("r.ticker", "ticker"),
             Col("coalesce(r.member, 'total')", "member"), Col("r.axis", "axis"),
             Col("r.period_start", "from", "date"), Col("r.period_end", "to", "date"),
             Col("r.value", "value", "money"), Col("r.form", "form")],
            "r.filing_date", ["r.member", "r.axis", "r.concept"],
            fields={"axis": ("r.axis", "contains"), "member": ("r.member", "contains"),
                    "form": ("r.form", "prefix")},
            order="r.ticker, r.value DESC NULLS LAST",
            hint="axis:geo · member:datacenter · t:NVDA",
        ),
        Dataset(
            "fsds", "Financial Statement Data Sets",
            f"""(SELECT u.ticker, s.adsh AS accn, s.* EXCLUDE (adsh)
                 FROM fl.edgar_segment_revenue s JOIN (VALUES {ciks}) u(cik, ticker) USING (cik)) r""",
            [Col("r.filed", "filed", "date"), Col("r.ticker", "ticker"), Col("r.tag", "tag"),
             Col("r.axis", "axis"), Col("r.member", "member"), Col("r.ddate", "as of", "date"),
             Col("r.qtrs", "qtrs", "int"), Col("r.value", "value", "num"), Col("r.form", "form")],
            "r.filed", ["r.tag", "r.axis", "r.member"],
            fields={"tag": ("r.tag", "contains"), "axis": ("r.axis", "contains"),
                    "member": ("r.member", "contains"), "form": ("r.form", "prefix"),
                    "qtrs": ("CAST(r.qtrs AS VARCHAR)", "eq")},
            order="r.ticker, r.value DESC NULLS LAST",
            hint="universe tickers only · axis:geo · qtrs:4 annual",
        ),
    ]
    return {d.key: d for d in out}


def parse(query: str, fields: dict | None = None) -> dict:
    """Split a query into tickers, dates, field filters, phrases, negations and words.
    Unknown `name:value` tokens stay in the text as words."""
    fields = fields or {}
    q = {"tickers": [], "since": None, "until": None, "fields": {}, "phrases": [], "exclude": [], "words": []}
    rest = query
    for key, val in _FILTER.findall(query):
        k, vals = key.lower(), [v for v in val.strip('"').split(",") if v]
        if k in ("t", "ticker"):
            q["tickers"] += [v.upper() for v in vals]
        elif k in ("since", "until") and vals:
            q[k] = vals[0] + {4: "-01-01", 7: "-01"}.get(len(vals[0]), "")
        elif k in fields:
            q["fields"].setdefault(k, []).extend(vals)
        else:
            continue
        rest = rest.replace(f"{key}:{val}", " ", 1)
    q["phrases"] = re.findall(r'"([^"]+)"', rest)
    rest = re.sub(r'"[^"]+"', " ", rest)
    q["exclude"] = [w[1:] for w in rest.split() if w.startswith("-") and len(w) > 1]
    q["words"] = [w for w in rest.split() if not w.startswith("-")]
    return q


def _where(ds: Dataset, q: dict) -> tuple[list[str], dict]:
    where, params = ["TRUE"], {}
    if q["tickers"] and ds.ticker:
        where.append(f"{ds.ticker} IN (SELECT unnest($tickers))")
        params["tickers"] = q["tickers"]
    for key, op in (("since", ">="), ("until", "<")):
        if q[key]:
            where.append(f"{ds.date} {op} TRY_CAST(${key} AS DATE)")
            params[key] = q[key]
    for i, (name, vals) in enumerate(q["fields"].items()):
        expr, how = ds.fields[name]
        params[f"f{i}"] = vals
        test = {"eq": f"upper({expr}) = upper(v)", "prefix": f"starts_with(upper({expr}), upper(v))",
                "contains": f"{expr} ILIKE '%' || v || '%'"}[how]
        where.append(f"EXISTS (SELECT 1 FROM unnest($f{i}) p(v) WHERE {test})")
    hay = " || ' ' || ".join(f"coalesce(CAST({c} AS VARCHAR), '')" for c in ds.text)
    for i, w in enumerate([*q["words"], *q["phrases"]]):
        where.append(f"({hay}) ILIKE '%' || $w{i} || '%'")
        params[f"w{i}"] = w
    for i, w in enumerate(q["exclude"]):
        where.append(f"({hay}) NOT ILIKE '%' || $x{i} || '%'")
        params[f"x{i}"] = w
    return where, params


def _compact(v: float, prefix: str = "") -> str:
    a = abs(v)
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            return f"{'-' if v < 0 else ''}{prefix}{a / div:.1f}{suf}"
    return f"{'-' if v < 0 else ''}{prefix}{a:,.0f}"


def fmt(v, kind: str) -> str:
    if v is None:
        return ""
    if kind == "date":
        return v.isoformat()[:10] if isinstance(v, (date, datetime)) else str(v)[:10]
    if kind == "bool":
        return "yes" if v else ""
    if kind == "int":
        return f"{int(v):,}"
    if kind == "price":
        return f"{v:,.2f}"
    if kind == "money":
        return _compact(float(v), "$")
    if kind == "num":
        return _compact(float(v)) if abs(v) >= 1e4 else f"{v:,.4g}" if v != int(v) else f"{int(v):,}"
    return str(v)


def _sec_doc(cik, accn: str, primary: str | None) -> str:
    cik = str(int(cik)) if cik else accn.split("-")[0].lstrip("0")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn.replace('-', '')}"
    return f"{base}/{primary}" if primary else f"{base}/{accn}-index.htm"


class Searcher:
    def __init__(self, con: duckdb.DuckDBPyConnection | None = None):
        self.con = con or duckdb.connect()
        self.sets = datasets()
        self._built: set[str] = set()
        self._attached = False

    def _src(self, ds: Dataset) -> str:
        if "fl." in ds.src and not self._attached:
            self.con.execute(f"ATTACH '{D}/finlarp.duckdb' AS fl (READ_ONLY)")
            self._attached = True
        if not ds.materialize:
            return ds.src
        name = f"rows_{ds.key}"
        if ds.key not in self._built:
            self.con.execute(f'CREATE OR REPLACE TEMP TABLE "{name}" AS SELECT r.* FROM {ds.src}')
            self._built.add(ds.key)
        return f'"{name}" r'

    def _urls(self, accns: list[str]) -> dict[str, str]:
        if not accns:
            return {}
        rows = self.con.execute(
            f"SELECT accn, cik, primary_doc FROM '{D}/events/filings.parquet' WHERE accn IN (SELECT unnest($a))",
            {"a": accns}).fetchall()
        found = {a: _sec_doc(c, a, p) for a, c, p in rows}
        return {a: found.get(a) or _sec_doc(None, a, None) for a in accns}

    def query(self, key: str, query: str = "", k: int = 200) -> dict:
        ds = self.sets.get(key)
        if ds is None:
            raise KeyError(f"unknown dataset {key!r}; one of {', '.join(self.sets)}")
        q = parse(query, ds.fields)
        where, params = _where(ds, q)
        src = self._src(ds)
        shown = [f"{c.expr} AS c{i}" for i, c in enumerate(ds.cols)]
        accn = f", {ds.accn} AS _accn" if ds.accn else ", NULL AS _accn"
        order = ", ".join(x for x in (f"{ds.date} DESC NULLS LAST", ds.order) if x)
        sql = (f"SELECT {', '.join(shown)}{accn}, to_json(r) AS _raw FROM {src} "
               f"WHERE {' AND '.join(where)} ORDER BY {order} LIMIT {int(k) + 1}")
        cur = self.con.execute(sql, params)
        raw = cur.fetchall()
        more = len(raw) > k
        raw = raw[:k]
        n = len(ds.cols)
        urls = self._urls(sorted({r[n] for r in raw if r[n]}))
        rows = []
        for r in raw:
            cells = [fmt(v, c.kind) for v, c in zip(r[:n], ds.cols)]
            if ds.key in ("insiders", "form4_live") and r[4] in CODES:
                cells[4] = f"{r[4]} {CODES[r[4]]}"
            detail = [[k2, "" if v is None else str(v)] for k2, v in json.loads(r[n + 1]).items()]
            rows.append({"cells": cells, "url": urls.get(r[n]), "detail": detail})
        return {"title": ds.title, "columns": [{"name": c.name, "kind": c.kind} for c in ds.cols],
                "rows": rows, "more": more, "fields": sorted(ds.fields), "hint": ds.hint, "query": q}


def serve() -> None:
    s = Searcher()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        rid = None
        try:
            req = json.loads(line)
            rid = req.get("id")
            t = time.perf_counter()
            out = {"id": rid, **s.query(req["ds"], req.get("q", ""), int(req.get("k", 200)))}
            out["ms"] = round((time.perf_counter() - t) * 1000)
        except Exception as e:  # noqa: BLE001 - every failure becomes a reply, never a dead server
            out = {"id": rid, "error": f"{type(e).__name__}: {e}"}
        sys.stdout.write(json.dumps(out, default=str) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    args = sys.argv[1:]
    k = 200
    if "-k" in args:
        i = args.index("-k")
        k = int(args[i + 1])
        del args[i:i + 2]
    cmd = args[0] if args else "list"
    if cmd == "--serve":
        serve()
    elif cmd == "list":
        print(json.dumps({d.key: d.title for d in datasets().values()}))
    elif cmd == "q":
        print(json.dumps(Searcher().query(args[1], " ".join(args[2:]), k), default=str, indent=1))
