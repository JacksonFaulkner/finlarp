"""MCP server exposing the pulled SEC dataset to agents (stdio transport).

Same data the nvim UI reads — nothing here fetches from the network, so
every call is local and fast. Tools are all read-only:

    search      BM25 over filing text / new risks / earnings / guidance
    get_chunk   expand a search hit with surrounding text
    company     one-call briefing for a ticker (profile, revenue, segments,
                13F flows, events, insiders, latest guidance, filing metrics)
    financials  stitched XBRL time series (handles predecessor CIKs,
                concept renames, Q4 derivation)
    sql         read-only DuckDB SQL over views of every table
    schema      the views `sql` can see, with columns

Register with Claude Code:
    claude mcp add security-spread -- <plugin_dir>/.venv/bin/python <plugin_dir>/mcp_server.py
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import duckdb
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations


from sources import sec_13f, sec_earnings, sec_events, sec_financials, sec_insiders, sec_segments, universe
from views import search as fts

D = universe.DATA_ROOT
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
MAX_CELL = 600

INSTRUCTIONS = """Local SEC dataset for ~428 AI-exposed stocks (ai_stocks.json universe), pulled
from EDGAR: XBRL financials (15+ yrs), segment/geography revenue, 13F institutional
holdings (6 quarters, whole market), 8-K event stream, Form 4 insider trades,
10-K/20-F text (business, risk factors, MD&A...), YoY-new risk sentences,
earnings press releases with extracted guidance, Yahoo company profiles, and
~1.5M granted US patents (PatentsView, thru 2025) matched to tickers.

Suggested flow: `company` for a ticker overview -> `search` for qualitative
questions (then `get_chunk` to read more of a hit) -> `financials` or `sql` for
numbers. Call `schema` before writing SQL.

search query syntax: free text plus filters, e.g.
  t:MRVL,NVDA  s:memory (sector prefix)  i:semiconductors (Yahoo industry)  r:US
  type:guid|earn|new|10k|profile|patent (patents only match with type:patent)
  sec:risk|mda|business  since:2025  "exact phrase"  -exclude
BM25 matches exact terms: if results are thin, rephrase with synonyms or
specific terms (product names, line items) rather than longer sentences.

Caveats: data is a local snapshot (check dates in results). Insider bulk data
lags 0-3 months. 20-F filers have no quarterly XBRL. Some tickers' early
XBRL history belongs to a predecessor business (MTCH=IAC, JCI=Tyco, NBIS=Yandex).
Patents: grants only (18mo+ lag vs filing); ticker = current owner incl. acquired
subsidiaries' pre-deal patents. Group by patent_cpc/patent_wipo for tech mix."""

mcp = MCPServer("security-spread", instructions=INSTRUCTIONS)


def _dump(obj) -> str:
    return json.dumps(obj, default=str, separators=(",", ":"))


def _views(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    """name -> description; creates a view per dataset that exists on disk."""
    stocks = universe.stocks()
    rows = [{"ticker": s["ticker"], "name": s["name"], "region": s.get("region"), "cik": s["cik"],
             "primary": json.dumps(s.get("primary", {})), "subs": json.dumps(s.get("subs", {}))} for s in stocks]
    con.execute("CREATE OR REPLACE TABLE universe AS SELECT * FROM (SELECT unnest($r, recursive := true))", {"r": rows})
    specs = {
        "universe": (None, "ticker, name, region, cik, primary/subs = JSON {bucket: weight} AI-exposure buckets"),
        "facts": (f"read_parquet('{D}/financials/facts/*.parquet', union_by_name=true)",
                  "XBRL facts, one row per (ticker, taxonomy, concept, unit, start, end); prefer the `financials` tool for series"),
        "concepts": (f"'{D}/financials/concepts.parquet'", "XBRL concept labels + how many tickers use each"),
        "segments": (f"read_parquet('{sec_segments.facts_glob()}', union_by_name=true)",
                     "revenue by axis/member from latest 10-K + 10-Q (axis e.g. ProductOrServiceAxis, StatementGeographicalAxis); filter unit"),
        "holdings_13f": (sec_13f.holdings_sql(), "13F long positions per (cik manager, period, cusip); join cusip_map for ticker"),
        "cusip_map": (f"'{sec_13f.DATA_DIR}/cusip_map.parquet'", "ticker -> 13F cusip"),
        "filings": (f"'{D}/events/filings.parquet'", "every EDGAR filing per ticker (form, filed, accn, items...)"),
        "events": (f"'{D}/events/events.parquet'", "8-K/6-K events, one row per item code, with label and signal tier"),
        "insider_tx": (sec_insiders.tx_sql(), "Form 3/4/5 transactions (code P=open-market buy, S=sale; is_10b5_1)"),
        "earnings": (f"read_parquet('{D}/earnings/releases/*.parquet', union_by_name=true)",
                     "earnings press releases (text, guidance VARCHAR[], headline JSON)"),
        "annual_reports": (f"'{D}/filing_text/filings.parquet'",
                           "one row per parsed 10-K/20-F: ai_per_10k_words, patent_count, risk_added/removed, subsidiary_count"),
        "report_sections": (f"'{D}/filing_text/sections.parquet'", "10-K/20-F section text (business, risk_factors, mda, ...)"),
        "risk_diff": (f"'{D}/filing_text/risk_diff.parquet'", "risk-factor sentences added/removed vs prior year (kind, novelty)"),
        "subsidiaries": (f"'{D}/filing_text/subsidiaries.parquet'", "Exhibit 21 subsidiaries + jurisdiction"),
        "profiles": (f"'{D}/profiles/profiles.parquet'",
                     "Yahoo profile per ticker: long_name, sector, industry, country, website, employees, market_cap, summary, officers JSON"),
        "patents": (f"'{D}/patents/patents.parquet'", "granted US patents: patent_id, date (grant), title, type, num_claims, filing_date"),
        "patent_ticker": (f"'{D}/patents/patent_ticker.parquet'", "patent_id -> ticker (co-assigned patents map to several)"),
        "patent_cpc": (f"'{D}/patents/cpc.parquet'", "CPC codes per patent (cpc_sequence 0 = primary; cpc_subclass e.g. H04B, G02B)"),
        "patent_wipo": (f"'{D}/patents/wipo.parquet'", "WIPO technology field per patent (35 fields, e.g. 'Optics', 'Semiconductors')"),
        "patent_inventors": (f"'{D}/patents/inventors.parquet'", "disambiguated inventor_id + name per patent (track people across tickers)"),
        "patent_assignees": (f"'{D}/patents/assignee_map.parquet'", "assignee name -> ticker match audit (kind raw|cluster, via sec_name|ex21|yahoo|manual)"),
        "patent_ai": (f"'{D}/patents/ai.parquet'",
                      "USPTO AI Patent Dataset labels per granted patent (thru 2023-12-26): any_ai (predict50, generous), "
                      "any_ai93 (strict), ml/evo/nlp/speech/vision/planning/kr/hardware bools + <cat>_score"),
        "patent_ai_by_ticker_year": (f"'{D}/patents/ai_by_ticker_year.parquet'",
                                     "ticker x grant year (<=2023): n_patents, n_ai_any/pct_ai, n_ai93/pct_ai93, n_<cat>; prefer pct_ai93 or n_ml"),
    }
    out = {}
    for name, (src, desc) in specs.items():
        if src is not None:
            try:
                con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM {src}")
            except duckdb.Error:
                continue
        out[name] = desc
    return out


_con: duckdb.DuckDBPyConnection | None = None
_view_desc: dict[str, str] = {}


def _db() -> duckdb.DuckDBPyConnection:
    global _con, _view_desc
    if _con is None:
        con = duckdb.connect()
        _view_desc = _views(con)
        # `sql` takes arbitrary SELECTs, and read_text()/read_csv() would
        # otherwise read any file (.env, the E*TRADE token) into the LLM's
        # context. Views resolve lazily, so allow just their data dirs, then
        # lock the config so a query can't turn access back on.
        con.execute(f"SET allowed_directories=['{D}/', '{sec_13f.DATA_DIR}/']")
        con.execute("SET enable_external_access=false")
        con.execute("SET lock_configuration=true")
        _con = con
    return _con


@mcp.tool(annotations=READ_ONLY)
def search(query: str, k: int = 10) -> str:
    """Full-text (BM25) search over 10-K/20-F sections, new-this-year risk
    factor sentences, earnings releases and guidance lines. Supports filters:
    t:TICKERS s:sector r:region type:10k|risk|new|earn|guid sec:section
    since:/until: dates, "exact phrase", -exclude. Returns chunk ids, metadata,
    score and ~220-word text; use get_chunk to read around a hit."""
    rows = fts.search(query, k=min(max(k, 1), 50))
    return _dump({"query": fts.parse(query), "results": rows})


@mcp.tool(annotations=READ_ONLY)
def get_chunk(chunk_id: int, context: int = 1) -> str:
    """A search hit plus `context` neighbouring chunks either side from the
    same document (max 5), with its SEC filing URL."""
    return _dump(fts.get(chunk_id, min(max(context, 0), 5)))


@mcp.tool(annotations=READ_ONLY)
def financials(ticker: str, metric: str = "revenue", period: str = "annual", n: int = 12) -> str:
    """XBRL time series for one ticker, stitched across predecessor CIKs and
    concept renames. metric: revenue, gross_profit, operating_income,
    net_income, eps_diluted, eps_basic, operating_cash_flow, capex, rnd,
    total_assets, equity, cash, long_term_debt, shares_outstanding,
    diluted_shares — or concepts like "us-gaap:InventoryNet". period: annual |
    quarterly (Q4 derived as FY minus 9M, flagged derived=true)."""
    fn = sec_financials.quarterly_series if period.startswith("q") else sec_financials.annual_series
    concepts: str | list[str] = [c.strip() for c in metric.split(",")] if ":" in metric else metric
    rows = fn(ticker.upper(), concepts)
    return _dump(rows[-max(n, 1):])


def _section(fn):
    try:
        return fn()
    except Exception as e:  # one missing dataset shouldn't sink the briefing
        return {"error": f"{type(e).__name__}: {e}"}


@mcp.tool(annotations=READ_ONLY)
def company(ticker: str) -> str:
    """One-call briefing for a ticker: universe profile (AI-exposure buckets),
    last 5 fiscal years + 4 quarters of revenue, latest segment/geography mix,
    13F holder change last quarter, high-signal 8-K events (180 days),
    open-market insider activity (365 days), latest earnings headline and
    guidance, and annual-report metrics (AI mentions, patents, new risks)."""
    t = ticker.upper()
    con = _db()
    year_ago = date.today() - timedelta(days=365)

    def profile():
        r = con.execute("SELECT * FROM universe WHERE ticker = ?", [t]).fetchone()
        if not r:
            return None
        cols = [c[0] for c in con.description]
        d = dict(zip(cols, r))
        d["primary"], d["subs"] = json.loads(d["primary"]), json.loads(d["subs"])
        return d

    def segments():
        rows = con.execute("""
            WITH latest AS (
                SELECT axis, max(period_end) pe FROM segments
                WHERE ticker = ? AND axis <> '' AND period_start IS NOT NULL
                  AND date_diff('day', period_start, period_end) > 300 GROUP BY 1
            )
            SELECT s.axis, s.member, s.period_end, s.value, s.unit FROM segments s JOIN latest l
              ON s.axis = l.axis AND s.period_end = l.pe
            WHERE s.ticker = ? AND date_diff('day', s.period_start, s.period_end) > 300
              AND s.concept NOT ILIKE '%OperatingIncome%'
            QUALIFY row_number() OVER (PARTITION BY s.axis, s.member ORDER BY s.value DESC) = 1
            ORDER BY s.axis, s.value DESC
        """, [t, t]).fetchall()
        out: dict[str, list] = {}
        for axis, member, pe, val, unit in rows:
            out.setdefault(axis, []).append({"member": member, "value": val, "unit": unit, "period_end": pe})
        return {a: m[:8] for a, m in out.items()}

    def insiders():
        tx = sec_insiders.open_market(t, year_ago)
        buys = [x for x in tx if x["code"] == "P"]
        sells = [x for x in tx if x["code"] == "S"]
        disc = [x for x in sells if not x.get("is_10b5_1")]
        return {"buys": len(buys), "buy_value": sum(x["value"] or 0 for x in buys),
                "sales": len(sells), "sale_value": sum(x["value"] or 0 for x in sells),
                "discretionary_sale_value": sum(x["value"] or 0 for x in disc),
                "recent_buys": buys[:5], "note": "bulk data lags 0-3 months"}

    def earnings():
        r = sec_earnings.latest(t)
        if not r:
            return None
        h = r.get("headline")
        return {"filed": r["filed"], "accn": r["accn"], "headline": json.loads(h) if isinstance(h, str) else h,
                "guidance": (r.get("guidance") or [])[:12]}

    def annual_report():
        r = con.execute("""
            SELECT form, filed, fiscal_period_end, ai_mentions, ai_per_10k_words, patent_count,
                   risk_factor_count, risk_added, risk_removed, subsidiary_count
            FROM annual_reports WHERE ticker = ? AND parse_ok ORDER BY filed DESC LIMIT 1
        """, [t]).fetchone()
        return dict(zip([c[0] for c in con.description], r)) if r else None

    return _dump({
        "ticker": t,
        "profile": _section(profile),
        "revenue_annual": _section(lambda: sec_financials.annual_series(t, "revenue")[-5:]),
        "revenue_quarterly": _section(lambda: sec_financials.quarterly_series(t, "revenue")[-4:]),
        "segments_latest_fy": _section(segments),
        "holders_13f": _section(lambda: (sec_13f.summary([t]) or [None])[0]),
        "events_high_180d": _section(lambda: sec_events.recent_events(t, 180, "high")[:15]),
        "insiders_365d": _section(insiders),
        "latest_earnings": _section(earnings),
        "annual_report": _section(annual_report),
    })


@mcp.tool(annotations=READ_ONLY)
def schema() -> str:
    """Views available to the `sql` tool, with columns and a one-line note."""
    con = _db()
    out = {}
    for name, desc in _view_desc.items():
        cols = con.execute(f"DESCRIBE {name}").fetchall()
        out[name] = {"note": desc, "columns": {c[0]: c[1] for c in cols}}
    return _dump(out)


@mcp.tool(annotations=READ_ONLY)
def sql(query: str, max_rows: int = 100) -> str:
    """Run one read-only DuckDB SELECT over the dataset views (see `schema`).
    Only SELECT statements are accepted. Long text cells are truncated to
    600 chars; at most max_rows (<=1000) rows are returned."""
    con = _db()
    stmts = con.extract_statements(query)
    if len(stmts) != 1 or stmts[0].type != duckdb.StatementType.SELECT:
        return _dump({"error": "only a single SELECT statement is allowed"})
    try:
        cur = con.execute(query)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchmany(min(max(max_rows, 1), 1000))
    except duckdb.Error as e:
        return _dump({"error": str(e)})
    trunc = lambda v: v[:MAX_CELL] + "…" if isinstance(v, str) and len(v) > MAX_CELL else v
    return _dump({"columns": cols, "rows": [[trunc(v) for v in r] for r in rows], "row_count": len(rows)})


if __name__ == "__main__":
    mcp.run("stdio")
