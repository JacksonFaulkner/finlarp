"""Full-text search over the pulled SEC text — for the <leader>sf picker and
for agents (same CLI, `--json` output).

Corpus: 10-K/20-F sections (sec_filing_text), YoY-new risk sentences,
earnings press releases and their extracted guidance lines (sec_earnings).
Text is chunked into ~220-word windows on sentence boundaries, tagged with
ticker + universe sector/sub/region, and indexed with DuckDB's BM25 (fts).

Why BM25 and not embeddings (yet): finance questions hinge on exact terms
— tickers, product names (HBM, CoWoS), line items, numbers — which BM25
matches and general-purpose embeddings blur. An agent calling this can
rephrase and re-query cheaply, which covers most of what semantic recall
would buy. If recall proves short on real questions, embeddings slot in as
a second ranker over the same chunks table (hybrid, reciprocal-rank fusion).

Query syntax — free text plus filters, any order:
    t:MRVL,NVDA        ticker(s)
    s:memory           sector: primary bucket or sub-bucket, prefix match
    r:US               region
    type:risk          10k | risk | new_risk | earnings | guidance (prefix ok)
    sec:mda            filing section: business, risk_factors, mda, ...
    since:2025         date lower bound (YYYY, YYYY-MM or YYYY-MM-DD)
    "exact phrase"     must appear verbatim (case-insensitive)
    -word              must not appear
No free text = browse newest chunks matching the filters.

CLI:
    search.py build                 (re)build the index from the Parquet
    search.py q QUERY... [--json] [-k N]
    search.py get CHUNK_ID [--context N] [--json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import universe

SRC = universe.DATA_ROOT
INDEX_PATH = universe.data_dir("search") / "search.duckdb"
CHUNK_WORDS = 220

TYPE_ALIASES = {"10k": "filing", "filing": "filing", "risk": "filing", "new_risk": "new_risk",
                "earnings": "earnings", "guidance": "guidance"}
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"(])")


def _chunks(text: str) -> list[str]:
    """Sentence-packed windows of ~CHUNK_WORDS words. Source text is hard-
    wrapped HTML, so whitespace is collapsed first."""
    sents = _SENT.split(re.sub(r"\s+", " ", text or "").strip())
    out, cur, n = [], [], 0
    for s in sents:
        w = len(s.split())
        if cur and n + w > CHUNK_WORDS:
            out.append(" ".join(cur))
            cur, n = [], 0
        cur.append(s)
        n += w
    if cur:
        out.append(" ".join(cur))
    return out


def build() -> dict:
    """Rebuild search.duckdb from whatever the pullers have written so far."""
    meta = {}
    for s in universe.stocks():
        meta[s["ticker"]] = {
            "sectors": sorted(set(s.get("primary", {})) | set(s.get("subs", {}))),
            "region": s.get("region"),
        }
    src = duckdb.connect()
    rows: list[tuple] = []

    def add(ticker, typ, section, form, date, accn, text):
        m = meta.get(ticker, {"sectors": [], "region": None})
        for i, c in enumerate(_chunks(text)):
            rows.append((ticker, typ, section, form, date, accn, i, c, m["sectors"], m["region"]))

    ft = SRC / "filing_text"
    if (ft / "sections.parquet").exists():
        for r in src.execute(f"""
            SELECT s.ticker, s.section, s.form, coalesce(f.filed, s.fiscal_period_end), s.accn, s.text
            FROM '{ft}/sections.parquet' s LEFT JOIN '{ft}/filings.parquet' f USING (accn, ticker)
            WHERE s.text IS NOT NULL
        """).fetchall():
            add(r[0], "filing", r[1], r[2], r[3], r[4], r[5])
    if (ft / "risk_diff.parquet").exists():
        # One chunk per filing's added risk text, so a hit reads as "new this year".
        for r in src.execute(f"""
            SELECT d.ticker, f.form, f.filed, d.accn, string_agg(d.sentence, ' ')
            FROM '{ft}/risk_diff.parquet' d LEFT JOIN '{ft}/filings.parquet' f USING (accn, ticker)
            WHERE d.kind = 'added' GROUP BY ALL
        """).fetchall():
            add(r[0], "new_risk", "risk_factors", r[1], r[2], r[3], r[4])
    er = SRC / "earnings" / "releases"
    if er.exists() and any(er.glob("*.parquet")):
        for r in src.execute(f"""
            SELECT ticker, form, filed, accn, text, guidance FROM read_parquet('{er}/*.parquet', union_by_name = true)
        """).fetchall():
            add(r[0], "earnings", "release", r[1], r[2], r[3], r[4])
            if r[5]:
                add(r[0], "guidance", "guidance", r[1], r[2], r[3], " ".join(r[5]))
    src.close()

    tmp = INDEX_PATH.with_suffix(".part")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    con.execute("INSTALL fts; LOAD fts")
    con.execute("""
        CREATE TABLE chunks (id INTEGER, ticker VARCHAR, type VARCHAR, section VARCHAR, form VARCHAR,
            date DATE, accn VARCHAR, seq INTEGER, text VARCHAR, sectors VARCHAR[], region VARCHAR)
    """)
    nd = tmp.with_suffix(".ndjson")
    cols = ("ticker", "type", "section", "form", "date", "accn", "seq", "text", "sectors", "region")
    with open(nd, "w") as f:
        for i, r in enumerate(rows):
            f.write(json.dumps({"id": i, **dict(zip(cols, r))}, default=str) + "\n")
    con.execute(f"""
        INSERT INTO chunks SELECT id, ticker, type, section, form, TRY_CAST(date AS DATE), accn, seq, text, sectors, region
        FROM read_json('{nd}', format = 'newline_delimited', columns = {{
            id: 'INTEGER', ticker: 'VARCHAR', type: 'VARCHAR', section: 'VARCHAR', form: 'VARCHAR', date: 'VARCHAR',
            accn: 'VARCHAR', seq: 'INTEGER', text: 'VARCHAR', sectors: 'VARCHAR[]', region: 'VARCHAR'}})
    """)
    nd.unlink()
    con.execute("PRAGMA create_fts_index('chunks', 'id', 'text', stemmer = 'porter', stopwords = 'english')")
    stats = dict(con.execute("SELECT type, count(*) FROM chunks GROUP BY 1").fetchall())
    stats["tickers"] = con.execute("SELECT count(DISTINCT ticker) FROM chunks").fetchone()[0]
    con.close()
    tmp.rename(INDEX_PATH)
    return stats


_FILTER = re.compile(r'(\w+):("[^"]*"|\S+)')


def parse(query: str) -> dict:
    """Split a query string into filters, phrases, negations and free text."""
    q = {"tickers": [], "sectors": [], "regions": [], "types": [], "sections": [], "since": None,
         "until": None, "phrases": [], "exclude": [], "text": ""}
    rest = query
    for key, val in _FILTER.findall(query):
        k = key.lower()
        vals = [v for v in val.strip('"').split(",") if v]
        if k in ("t", "ticker"):
            q["tickers"] += [v.upper() for v in vals]
        elif k in ("s", "sector"):
            q["sectors"] += [v.lower() for v in vals]
        elif k in ("r", "region"):
            q["regions"] += [v.upper() for v in vals]
        elif k == "type":
            q["types"] += [next((t for a, t in TYPE_ALIASES.items() if a.startswith(v.lower())), v.lower()) for v in vals]
        elif k in ("sec", "section"):
            q["sections"] += [v.lower() for v in vals]
        elif k in ("since", "until"):
            q[k] = vals[0] + {4: "-01-01", 7: "-01"}.get(len(vals[0]), "")
        else:
            continue
        rest = rest.replace(f"{key}:{val}", " ", 1)
    q["phrases"] = re.findall(r'"([^"]+)"', rest)
    rest = re.sub(r'"[^"]+"', " ", rest)
    q["exclude"] = [w[1:] for w in rest.split() if w.startswith("-") and len(w) > 1]
    q["text"] = " ".join(w for w in rest.split() if not w.startswith("-"))
    return q


def search(query: str, k: int = 30) -> list[dict]:
    q = parse(query)
    where, params = ["TRUE"], {}
    if q["tickers"]:
        where.append("c.ticker IN (SELECT unnest($tickers))")
        params["tickers"] = q["tickers"]
    if q["sectors"]:
        where.append("EXISTS (SELECT 1 FROM unnest(c.sectors) a(x), unnest($sectors) b(p) WHERE starts_with(x, p))")
        params["sectors"] = q["sectors"]
    if q["regions"]:
        where.append("c.region IN (SELECT unnest($regions))")
        params["regions"] = q["regions"]
    if q["types"]:
        where.append("c.type IN (SELECT unnest($types))")
        params["types"] = q["types"]
    if q["sections"]:
        where.append("EXISTS (SELECT 1 FROM unnest($sections) b(p) WHERE starts_with(c.section, p))")
        params["sections"] = q["sections"]
    for key, op in (("since", ">="), ("until", "<")):
        if q[key]:
            where.append(f"c.date {op} TRY_CAST(${key} AS DATE)")
            params[key] = q[key]
    for i, p in enumerate(q["phrases"]):
        where.append(f"c.text ILIKE '%' || $ph{i} || '%'")
        params[f"ph{i}"] = p
    for i, w in enumerate(q["exclude"]):
        where.append(f"c.text NOT ILIKE '%' || $ex{i} || '%'")
        params[f"ex{i}"] = w
    # Phrases also feed BM25 so a phrase-only query still ranks.
    terms = " ".join([q["text"], *q["phrases"]]).strip()
    if terms:
        score = "fts_main_chunks.match_bm25(c.id, $terms)"
        params["terms"] = terms
        order = "score DESC"
        where.append("score IS NOT NULL")
    else:
        score, order = "NULL::DOUBLE", "c.date DESC NULLS LAST, c.ticker, c.seq"
    con = duckdb.connect(str(INDEX_PATH), read_only=True)
    try:
        con.execute("LOAD fts")
        rows = con.execute(f"""
            SELECT id, ticker, type, section, form, date, accn, seq, text, score FROM (SELECT c.id, c.ticker, c.type, c.section, c.form, c.date, c.accn, c.seq, c.text, c.sectors, c.region,
                                  {score} AS score FROM chunks c) c
            WHERE {' AND '.join(where)} ORDER BY {order} LIMIT {int(k)}
        """, params).fetchall()
    finally:
        con.close()
    cols = ["id", "ticker", "type", "section", "form", "date", "accn", "seq", "text", "score"]
    return [dict(zip(cols, r)) | {"url": _url(r[6])} for r in rows]


def get(chunk_id: int, context: int = 0) -> list[dict]:
    """A chunk plus `context` neighbours either side from the same document."""
    con = duckdb.connect(str(INDEX_PATH), read_only=True)
    try:
        rows = con.execute("""
            SELECT n.id, n.ticker, n.type, n.section, n.form, n.date, n.accn, n.seq, n.text
            FROM chunks c JOIN chunks n USING (accn, type, section)
            WHERE c.id = ? AND n.seq BETWEEN c.seq - ? AND c.seq + ? ORDER BY n.seq
        """, [chunk_id, context, context]).fetchall()
    finally:
        con.close()
    cols = ["id", "ticker", "type", "section", "form", "date", "accn", "seq", "text"]
    return [dict(zip(cols, r)) | {"url": _url(r[6])} for r in rows]


def _url(accn: str | None) -> str | None:
    if not accn:
        return None
    cik = accn.split("-")[0].lstrip("0")
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn.replace('-', '')}/{accn}-index.htm"


def _snippet(text: str, terms: list[str], width: int = 160) -> str:
    low = text.lower()
    pos = min((p for t in terms if (p := low.find(t.lower())) >= 0), default=0)
    start = max(0, pos - width // 4)
    return ("…" if start else "") + text[start:start + width].replace("\t", " ")


def _fzf_line(r: dict, terms: list[str]) -> str:
    # id is field 1 (hidden by the picker), the rest is what fzf shows.
    head = f"{r['ticker']:<6} {r['type']:<8} {(r['section'] or '')[:12]:<12} {str(r['date'] or '')[:10]:<10}"
    return f"{r['id']}\t{head} │ {_snippet(r['text'], terms)}"


if __name__ == "__main__":
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    k = 30
    if "-k" in args:
        i = args.index("-k")
        k = int(args[i + 1])
        del args[i:i + 2]
    cmd = args[0] if args else "q"
    if cmd == "build":
        print(json.dumps(build()))
    elif cmd == "get":
        ctx = 0
        if "--context" in args:
            ctx = int(args[args.index("--context") + 1])
        rows = get(int(args[1]), ctx)
        if as_json:
            print(json.dumps(rows, default=str))
        else:
            for r in rows:
                print(f"{r['ticker']}  {r['type']}  {r['section']}  {r['form']}  {r['date']}\n{r['url']}\n")
                print(re.sub(r"(.{1,100})(\s|$)", r"\1\n", r["text"]))
    else:
        query = " ".join(args[1:] if args and args[0] == "q" else args)
        rows = search(query, k)
        if as_json:
            print(json.dumps({"query": parse(query), "results": rows}, default=str))
        else:
            terms = parse(query)["text"].split() + parse(query)["phrases"]
            for r in rows:
                print(_fzf_line(r, terms))
