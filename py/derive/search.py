"""Full-text search over the pulled SEC text — for the <leader>sf picker and
for agents (same CLI, `--json` output).

Corpus: 10-K/20-F sections (sec_filing_text), YoY-new risk sentences,
earnings press releases and their extracted guidance lines (sec_earnings),
Yahoo business summaries (yahoo_profile) and granted patents since
PATENTS_SINCE, title + abstract (patents). Text is chunked into ~220-word
windows on sentence boundaries, tagged with ticker + universe
sector/sub/region + Yahoo sector/industry, and indexed with BM25 (fts).
Patents are ~3/4 of the chunks, so they only match with type:patent.

Why BM25 and not embeddings (yet): finance questions hinge on exact terms
— tickers, product names (HBM, CoWoS), line items, numbers — which BM25
matches and general-purpose embeddings blur. An agent calling this can
rephrase and re-query cheaply, which covers most of what semantic recall
would buy. If recall proves short on real questions, embeddings slot in as
a second ranker over the same chunks table (hybrid, reciprocal-rank fusion).

Query syntax — free text plus filters, any order:
    t:MRVL,NVDA        ticker(s)
    s:memory           sector: primary bucket or sub-bucket, prefix match
    i:semiconductors   Yahoo sector/industry, substring ("i:equipment", "i:software")
    r:US               region
    type:risk          10k | risk | new_risk | earnings | guidance | profile | patent (prefix ok)
    sec:mda            filing section: business, risk_factors, mda, ...
    since:2025         date lower bound (YYYY, YYYY-MM or YYYY-MM-DD)
    "exact phrase"     must appear verbatim (case-insensitive)
    -word              must not appear
No free text = browse newest chunks matching the filters.

CLI:
    search.py build                 (re)build the index from the Parquet
    search.py q QUERY... [--json] [-k N]
                                    --json adds "facets" (below) next to "results"
    search.py q QUERY... --fzf      ANSI-coloured picker lines (ui/search.lua), first
                                    line a facet summary for fzf --header-lines=1
    search.py get CHUNK_ID [--context N] [--json] [--color --terms QUERY]
    search.py --serve               JSON-lines server for the ratatui search screen

Facets: counts of every match of the query (not just the top k) per ticker,
type, section and year, top FACET_N each: {"ticker": [["MRVL", 41], ...], ...}.
Computed in the same statement as the hits, so they cost ~one GROUP BY.

--serve protocol (tui/src/screens/search): one JSON object per
line on stdin, one reply per line on stdout, in order, echoing "id". The
connection and fts extension stay loaded, so a query is ~100ms instead of
~350ms for a fresh process; the query string is parsed here (single parser).
    {"id": 1, "q": "t:MRVL guidance", "k": 50}
        -> {"id": 1, "query": parse(q), "terms": [...], "results": [...], "facets": {...}, "ms": 97}
    {"id": 2, "get": 1234, "context": 1}
        -> {"id": 2, "rows": [...]}
    any failure -> {"id": n, "error": "..."}
"""
from __future__ import annotations

import json
import re
import sys

import duckdb


from sources import universe

SRC = universe.DATA_ROOT
INDEX_PATH = universe.data_dir("search") / "search.duckdb"
CHUNK_WORDS = 220
FACET_N = 12

TYPE_ALIASES = {"10k": "filing", "filing": "filing", "risk": "filing", "new_risk": "new_risk",
                "earnings": "earnings", "guidance": "guidance", "profile": "profile", "patent": "patent"}
PATENTS_SINCE = "2016-01-01"
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
    src = duckdb.connect()
    prof = SRC / "profiles" / "profiles.parquet"
    yahoo = dict(src.execute(f"""
        SELECT ticker, lower(concat_ws(' / ', sector, industry)) FROM '{prof}'""").fetchall()) if prof.exists() else {}
    meta = {}
    for s in universe.rows():
        meta[s["ticker"]] = {
            "sectors": sorted(set(s.get("primary", {})) | set(s.get("subs", {}))),
            "region": s.get("region"),
            "industry": yahoo.get(s["ticker"]),
        }
    rows: list[tuple] = []

    def add(ticker, typ, section, form, date, accn, text):
        m = meta.get(ticker, {"sectors": [], "region": None, "industry": None})
        for i, c in enumerate(_chunks(text)):
            rows.append((ticker, typ, section, form, date, accn, i, c, m["sectors"], m["region"], m["industry"]))

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
    if prof.exists():
        for t, summary in src.execute(f"SELECT ticker, summary FROM '{prof}' WHERE summary IS NOT NULL").fetchall():
            add(t, "profile", "summary", "yahoo", None, None, summary)
    src.close()

    tmp = INDEX_PATH.with_suffix(".part")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    con.execute("INSTALL fts; LOAD fts")
    con.execute("""
        CREATE TABLE chunks (id INTEGER, ticker VARCHAR, type VARCHAR, section VARCHAR, form VARCHAR,
            date DATE, accn VARCHAR, seq INTEGER, text VARCHAR, sectors VARCHAR[], region VARCHAR, industry VARCHAR)
    """)
    nd = tmp.with_suffix(".ndjson")
    cols = ("ticker", "type", "section", "form", "date", "accn", "seq", "text", "sectors", "region", "industry")
    with open(nd, "w") as f:
        for i, r in enumerate(rows):
            f.write(json.dumps({"id": i, **dict(zip(cols, r))}, default=str) + "\n")
    con.execute(f"""
        INSERT INTO chunks SELECT id, ticker, type, section, form, TRY_CAST(date AS DATE), accn, seq, text, sectors, region, industry
        FROM read_json('{nd}', format = 'newline_delimited', columns = {{
            id: 'INTEGER', ticker: 'VARCHAR', type: 'VARCHAR', section: 'VARCHAR', form: 'VARCHAR', date: 'VARCHAR',
            accn: 'VARCHAR', seq: 'INTEGER', text: 'VARCHAR', sectors: 'VARCHAR[]', region: 'VARCHAR', industry: 'VARCHAR'}})
    """)
    nd.unlink()
    pat = SRC / "patents"
    if (pat / "patents.parquet").exists():
        # Title + abstract fit one chunk; loaded in SQL since there are ~700k.
        # section = primary CPC subclass (e.g. H04B), accn = "US<patent_id>" for the URL.
        con.execute("CREATE TEMP TABLE meta AS SELECT * FROM (SELECT unnest($t) AS ticker, unnest($s) AS sectors, "
                    "unnest($r) AS region, unnest($i) AS industry)",
                    {"t": list(meta), "s": [m["sectors"] for m in meta.values()],
                     "r": [m["region"] for m in meta.values()], "i": [m["industry"] for m in meta.values()]})
        con.execute(f"""
            INSERT INTO chunks
            SELECT {len(rows)} + row_number() OVER () - 1, pt.ticker, 'patent', c.cpc_subclass, 'patent', p.date,
                   'US' || p.patent_id, 0, p.title || '. ' || coalesce(a.abstract, ''), m.sectors, m.region, m.industry
            FROM '{pat}/patents.parquet' p
            JOIN '{pat}/patent_ticker.parquet' pt USING (patent_id)
            LEFT JOIN '{pat}/abstracts.parquet' a USING (patent_id)
            LEFT JOIN (SELECT patent_id, cpc_subclass FROM '{pat}/cpc.parquet' WHERE cpc_sequence = 0) c USING (patent_id)
            LEFT JOIN meta m USING (ticker)
            WHERE p.date >= DATE '{PATENTS_SINCE}'""")
    con.execute("PRAGMA create_fts_index('chunks', 'id', 'text', stemmer = 'porter', stopwords = 'english')")
    stats = dict(con.execute("SELECT type, count(*) FROM chunks GROUP BY 1").fetchall())
    stats["tickers"] = con.execute("SELECT count(DISTINCT ticker) FROM chunks").fetchone()[0]
    con.close()
    tmp.rename(INDEX_PATH)
    return stats


_FILTER = re.compile(r'(\w+):("[^"]*"|\S+)')


def parse(query: str) -> dict:
    """Split a query string into filters, phrases, negations and free text."""
    q = {"tickers": [], "sectors": [], "industries": [], "regions": [], "types": [], "sections": [], "since": None,
         "until": None, "phrases": [], "exclude": [], "text": ""}
    rest = query
    for key, val in _FILTER.findall(query):
        k = key.lower()
        vals = [v for v in val.strip('"').split(",") if v]
        if k in ("t", "ticker"):
            q["tickers"] += [v.upper() for v in vals]
        elif k in ("s", "sector"):
            q["sectors"] += [v.lower() for v in vals]
        elif k in ("i", "ind", "industry"):
            q["industries"] += [v.lower() for v in vals]
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


def _where(q: dict) -> tuple[list[str], dict, str, str]:
    """WHERE clauses + params + score expression + ORDER BY for a parsed query."""
    where, params = ["TRUE"], {}
    if q["tickers"]:
        where.append("c.ticker IN (SELECT unnest($tickers))")
        params["tickers"] = q["tickers"]
    if q["sectors"]:
        where.append("EXISTS (SELECT 1 FROM unnest(c.sectors) a(x), unnest($sectors) b(p) WHERE starts_with(x, p))")
        params["sectors"] = q["sectors"]
    if q["industries"]:
        where.append("EXISTS (SELECT 1 FROM unnest($industries) b(p) WHERE contains(c.industry, p))")
        params["industries"] = q["industries"]
    if q["regions"]:
        where.append("c.region IN (SELECT unnest($regions))")
        params["regions"] = q["regions"]
    if q["types"]:
        where.append("c.type IN (SELECT unnest($types))")
        params["types"] = q["types"]
    else:
        where.append("c.type <> 'patent'")
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
        params["terms"] = terms
        where.append("score IS NOT NULL")
        return where, params, "fts_main_chunks.match_bm25(c.id, $terms)", "score DESC"
    return where, params, "NULL::DOUBLE", "c.date DESC NULLS LAST, c.ticker, c.seq"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(INDEX_PATH), read_only=True)
    con.execute("LOAD fts")
    return con


_COLS = ["id", "ticker", "type", "section", "form", "date", "accn", "seq", "text", "score"]


def search_full(query: str, k: int = 30, con: duckdb.DuckDBPyConnection | None = None,
                facets: bool = True) -> dict:
    """Top-k hits plus facet counts over every match, in one statement.
    Pass `con` (from connect()) to reuse a loaded connection (--serve)."""
    q = parse(query)
    where, params, score, order = _where(q)
    own = con is None
    con = con or connect()
    # One BM25 pass: the matching set is materialized with narrow columns
    # only (no text), ranked ids and facet counts are aggregated from it in
    # the same statement, then the top-k texts are fetched by id.
    fac_sql = f"""
        (SELECT list([dim, n, CAST(c AS VARCHAR)] ORDER BY dim, rk) FROM (
            SELECT dim, n, c, row_number() OVER (PARTITION BY dim ORDER BY c DESC, n) AS rk FROM (
                SELECT 'ticker' AS dim, ticker AS n, count(*) AS c FROM h GROUP BY ALL
                UNION ALL SELECT 'type', type, count(*) FROM h GROUP BY ALL
                UNION ALL SELECT 'section', section, count(*) FROM h WHERE section IS NOT NULL GROUP BY ALL
                UNION ALL SELECT 'year', CAST(year(date) AS VARCHAR), count(*) FROM h WHERE date IS NOT NULL GROUP BY ALL))
         WHERE rk <= {FACET_N})""" if facets else "NULL"
    try:
        top, flat = con.execute(f"""
            WITH h AS MATERIALIZED (
                SELECT id, ticker, type, section, date, seq, score FROM (
                    SELECT c.id, c.ticker, c.type, c.section, c.date, c.seq, c.text, c.sectors, c.region, c.industry,
                           {score} AS score FROM chunks c) c
                WHERE {' AND '.join(where)})
            SELECT (SELECT list([id, score]) FROM (SELECT id, score FROM h c ORDER BY {order} LIMIT {int(k)})), {fac_sql}
        """, params).fetchone()
        top = top or []
        ids, scores = [int(t[0]) for t in top], [t[1] for t in top]
        by_id = {}
        if ids:
            for r in con.execute("""
                SELECT c.id, c.ticker, c.type, c.section, c.form, c.date, c.accn, c.seq, c.text, s.score
                FROM chunks c JOIN (SELECT unnest($ids) AS id, unnest($scores) AS score) s USING (id)""",
                                 {"ids": ids, "scores": scores}).fetchall():
                by_id[r[0]] = r
    finally:
        if own:
            con.close()
    fac: dict[str, list] = {}
    for dim, n, c in flat or []:
        fac.setdefault(dim, []).append([n, int(c)])
    if "year" in fac:
        fac["year"].sort(key=lambda x: x[0], reverse=True)
    return {"query": q, "terms": highlight_terms(q),
            "results": [dict(zip(_COLS, by_id[i])) | {"url": _url(by_id[i][6])} for i in ids if i in by_id],
            "facets": fac}


def search(query: str, k: int = 30) -> list[dict]:
    return search_full(query, k, facets=False)["results"]


def highlight_terms(q: dict) -> list[str]:
    """Words to highlight for a parsed query: free text (minus stopword-ish
    short words) and phrases. Porter stemming means "guidance" also hits
    "guided", so highlighters match a stem prefix (see _hl_re)."""
    return [w for w in q["text"].split() if len(w) > 2] + q["phrases"]


def _hl_re(terms: list[str]) -> re.Pattern | None:
    pats = []
    for t in sorted(terms, key=len, reverse=True):
        stem = t if " " in t or len(t) <= 4 else t[:max(4, len(t) - 2)]
        pats.append(re.escape(stem) + (r"\w*" if stem != t or len(t) <= 4 else ""))
    return re.compile(r"\b(" + "|".join(pats) + ")", re.I) if pats else None


def get(chunk_id: int, context: int = 0, con: duckdb.DuckDBPyConnection | None = None) -> list[dict]:
    """A chunk plus `context` neighbours either side from the same document."""
    own = con is None
    con = con or duckdb.connect(str(INDEX_PATH), read_only=True)
    try:
        rows = con.execute("""
            SELECT n.id, n.ticker, n.type, n.section, n.form, n.date, n.accn, n.seq, n.text
            -- IS NOT DISTINCT FROM: profiles have no accn and patents no
            -- section, and a plain = (or USING) never matches NULL to NULL.
            FROM chunks c JOIN chunks n
              ON n.ticker IS NOT DISTINCT FROM c.ticker AND n.type IS NOT DISTINCT FROM c.type
             AND n.accn IS NOT DISTINCT FROM c.accn AND n.section IS NOT DISTINCT FROM c.section
            WHERE c.id = ? AND n.seq BETWEEN c.seq - ? AND c.seq + ? ORDER BY n.seq
        """, [chunk_id, context, context]).fetchall()
    finally:
        if own:
            con.close()
    cols = ["id", "ticker", "type", "section", "form", "date", "accn", "seq", "text"]
    return [dict(zip(cols, r)) | {"url": _url(r[6])} for r in rows]


def _url(accn: str | None) -> str | None:
    if not accn:
        return None
    if accn.startswith("US"):
        return f"https://patents.google.com/patent/{accn}"
    cik = accn.split("-")[0].lstrip("0")
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn.replace('-', '')}/{accn}-index.htm"


def _snippet(text: str, terms: list[str], width: int = 160) -> str:
    low = text.lower()
    pos = min((p for t in terms if (p := low.find(t.lower())) >= 0), default=0)
    start = max(0, pos - width // 4)
    return ("…" if start else "") + text[start:start + width].replace("\t", " ")


# ANSI for the fzf picker (fzf --ansi); colours stay terminal-palette so
# they follow the user's theme.
_B, _DIM, _RST, _HL = "\033[1m", "\033[2m", "\033[0m", "\033[1;33m"
_TYPE_COL = {"filing": "34", "new_risk": "31", "earnings": "32", "guidance": "36", "profile": "35", "patent": "33"}
TYPE_BADGE = {"filing": "10K", "new_risk": "NEW", "earnings": "ERN", "guidance": "GUI", "profile": "PRF",
              "patent": "PAT"}


def _hl(text: str, rx: re.Pattern | None, on: str = _HL, off: str = _RST) -> str:
    return rx.sub(lambda m: on + m.group(0) + off, text) if rx else text


def _fzf_line(r: dict, terms: list[str], color: bool = False) -> str:
    # id is field 1 (hidden by the picker), the rest is what fzf shows.
    if not color:
        head = f"{r['ticker']:<6} {r['type']:<8} {(r['section'] or '')[:12]:<12} {str(r['date'] or '')[:10]:<10}"
        return f"{r['id']}\t{head} │ {_snippet(r['text'], terms)}"
    badge = TYPE_BADGE.get(r["type"], r["type"][:3].upper())
    col = _TYPE_COL.get(r["type"], "37")
    head = (f"{_B}\033[36m{r['ticker']:<6}{_RST} \033[{col}m{badge}{_RST} "
            f"{_DIM}{str(r['date'] or '')[:10]:<10}{_RST} {(r['section'] or '')[:12]:<12}")
    return f"{r['id']}\t{head} │ {_hl(_snippet(r['text'], terms), _hl_re(terms))}"


def facet_summary(fac: dict, n: int = 5) -> str:
    """One-line facet header: "MRVL 41 · NVDA 12 │ 10K 30 · ERN 9 │ 2025 20 · 2024 18"."""
    parts = []
    for dim in ("ticker", "type", "year"):
        items = fac.get(dim, [])[:n]
        if items:
            parts.append(" · ".join(f"{TYPE_BADGE.get(k, k) if dim == 'type' else k} {c}" for k, c in items))
    return " │ ".join(parts)


def serve() -> None:
    """JSON-lines loop (see module docstring). Replies are flushed per line;
    the client drops replies whose id is stale, so we never skip requests."""
    con = connect()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        rid = None
        try:
            req = json.loads(line)
            rid = req.get("id")
            if "get" in req:
                out = {"id": rid, "rows": get(int(req["get"]), int(req.get("context", 0)), con)}
            else:
                import time
                t = time.perf_counter()
                out = {"id": rid, **search_full(req.get("q", ""), int(req.get("k", 50)), con)}
                out["ms"] = round((time.perf_counter() - t) * 1000)
        except Exception as e:  # noqa: BLE001 — every failure becomes a reply, never a dead server
            out = {"id": rid, "error": f"{type(e).__name__}: {e}"}
        sys.stdout.write(json.dumps(out, default=str) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    args = sys.argv[1:]
    as_json = "--json" in args
    color = "--color" in args
    fzf = "--fzf" in args
    args = [a for a in args if a not in ("--json", "--color", "--fzf")]
    k = 30
    if "-k" in args:
        i = args.index("-k")
        k = int(args[i + 1])
        del args[i:i + 2]
    cmd = args[0] if args else "q"
    if cmd == "--serve":
        serve()
    elif cmd == "build":
        print(json.dumps(build()))
    elif cmd == "get":
        ctx, terms = 0, []
        if "--context" in args:
            ctx = int(args[args.index("--context") + 1])
        if "--terms" in args:
            terms = highlight_terms(parse(args[args.index("--terms") + 1]))
        rows = get(int(args[1]), ctx)
        if as_json:
            print(json.dumps(rows, default=str))
        else:
            rx = _hl_re(terms) if color else None
            hit_seq = next((r["seq"] for r in rows if str(r["id"]) == args[1]), None)
            for r in rows:
                head = f"{r['ticker']}  {r['type']}  {r['section']}  {r['form']}  {r['date']}"
                hit = str(r["id"]) == args[1]
                if color:
                    head = f"{_B}{head}{_RST}" + (f"  {_HL}◀ match{_RST}" if hit and ctx else "")
                    print(f"{head}\n{_DIM}{r['url']}{_RST}\n")
                else:
                    print(f"{head}\n{r['url']}\n")
                body = re.sub(r"(.{1,100})(\s|$)", r"\1\n", r["text"])
                if color and not hit and hit_seq is not None:
                    # neighbours are context: keep the lines next to the match
                    # so a preview window opens with the match near the top
                    ls = body.rstrip("\n").split("\n")
                    body = "\n".join(["…", *ls[-3:]] if r["seq"] < hit_seq else [*ls[:6], "…"]) + "\n"
                if color and not hit:
                    body = _DIM + body.replace("\n", _RST + "\n" + _DIM) + _RST
                print(_hl(body, rx, _HL, _RST + (_DIM if color and not hit else "")) if rx else body)
    else:
        query = " ".join(args[1:] if args and args[0] == "q" else args)
        if as_json:
            print(json.dumps(search_full(query, k), default=str))
        elif fzf:
            res = search_full(query, k)
            total = sum(c for _, c in res["facets"].get("type", []))  # type has < FACET_N values: complete
            # leading tab: the picker shows fields 2.. (field 1 is the chunk id)
            print(f"\t\033[2m{total} matches  {facet_summary(res['facets'])}\033[0m")
            for r in res["results"]:
                print(_fzf_line(r, res["terms"], color=True))
        else:
            terms = parse(query)["text"].split() + parse(query)["phrases"]
            for r in search(query, k):
                print(_fzf_line(r, terms))
