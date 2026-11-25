"""Terms the filing reader can navigate on (the diagram LSP), and where the gaps are.

    uv run python py/derive/lsp_terms.py            # scan every 10-K/10-Q/20-F section
    uv run python py/derive/lsp_terms.py --limit 300 # a quick sample

The curated list is py/derive/lsp_terms_seed.json: each term, the spellings filings use for it
(aliases), and the x-diagrams node that explains it (null when no diagram exists yet). The TUI's
filing reader (docview) underlines every alias it finds; `gd` on one opens the node, `gr` searches
every other filing for the term.

This script counts each term over the parsed filing sections (data/filing_text/sections.parquet)
and writes:

    data/lsp/terms.json   the seed plus docs / tickers / mentions / top tickers per term
    data/lsp/gaps.md      what to build next: frequent terms with no diagram, and frequent
                          acronyms that are not in the seed at all (candidates to add)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

PY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PY))
from sources import universe  # noqa: E402

SEED = PY / "derive" / "lsp_terms_seed.json"
D = Path(universe.DATA_ROOT)
OUT = D / "lsp"

# Acronyms that are filing boilerplate, not technology.
STOP = set("""
SEC US USA GAAP LLC INC CEO CFO COO CTO ITEM USD EPS IPO ESG LTD PLC NV SA AG CO CORP II III IV
VI VII VIII IX XI XII NYSE NASDAQ IRS EU UK PRC ROU RSU RSUS PSU PSUS LIBOR SOFR ASC ASU FASB
IFRS OCI AOCI EBITDA FY Q1 Q2 Q3 Q4 TSR NOL R&D SG&A COVID OEM OEMS ODM ODMS AI IT IP HR LP GP
ERISA FCPA OFAC DOJ FTC FCC EPA OSHA GDPR CCPA ISO API APIS SKU SKUS ROI ROE ROIC KPI KPIS ARR
NASA DOD DOE NIST FDA EEOC SOX PCAOB MD&A EX ADR ADS ADSS HK TW KR JP CN DE NL FR GB IN IL SG MY
TBD NA NM PP MM BN TB GB MB KB OK CA NY TX WA MA NJ FL VA CT PA OR AZ NC GA CO MN OH MI IL UT ID
OECD CISO OBBBA SOC CIO EMEA FD EEA GHG MD CPRA ERM SSP ESPP CSF ERP LLP IEC APAC CODM IRA FDIC
HIPAA DGCL CTA TCJA BEAT GILTI FDII PFIC CFC ASR DTA DTL NOLS PCI DSS SOX404 VIE VIES WFOE CSRC
SAFE CAC MOFCOM NDRC SAMR HKEX TWSE KRX JPX DPA LGPD PIPL PIPEDA CISA NYDFS FINRA CFIUS ITAR EAR
""".split())

ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,6}\b")


def load_seed() -> list[dict]:
    return json.loads(SEED.read_text())


def matcher(seed: list[dict]):
    """One regex for every spelling; returns (regex, spelling -> term index). Spellings in
    capitals (acronyms) match case-sensitively, the rest ignore case."""
    lookup: dict[str, int] = {}
    caps: list[str] = []
    words: list[str] = []
    for i, t in enumerate(seed):
        for s in [t["term"], *t["aliases"]]:
            key = s if s.isupper() or any(c.isdigit() for c in s) else s.lower()
            lookup.setdefault(key, i)
            (caps if key == s and s != s.lower() else words).append(re.escape(s))
    by_len = lambda xs: sorted(set(xs), key=len, reverse=True)  # noqa: E731
    pat = r"(?<![\w-])(?:(?P<c>" + "|".join(by_len(caps)) + r")|(?P<w>(?i:" + "|".join(by_len(words)) + r")))(?![\w-])"
    return re.compile(pat), lookup


def scan(limit: int | None) -> tuple[list[dict], Counter, dict]:
    seed = load_seed()
    rx, lookup = matcher(seed)
    con = duckdb.connect()
    q = f"SELECT ticker, accn, text FROM read_parquet('{D}/filing_text/sections.parquet') WHERE text IS NOT NULL"
    if limit:
        q += f" LIMIT {int(limit)}"
    docs: dict[int, set] = defaultdict(set)
    tickers: dict[int, Counter] = defaultdict(Counter)
    mentions: Counter = Counter()
    acr_tickers: dict[str, set] = defaultdict(set)
    seen_alias = {s.upper() for t in seed for s in [t["term"], *t["aliases"]]}
    rows = con.execute(q).fetchall()
    for n, (ticker, accn, text) in enumerate(rows):
        for m in rx.finditer(text):
            s = m.group("c") or m.group("w")
            i = lookup.get(s, lookup.get(s.lower()))
            if i is None:
                continue
            mentions[i] += 1
            docs[i].add(accn)
            tickers[i][ticker] += 1
        for m in ACRONYM.finditer(text):
            a = m.group(0)
            if a in STOP or a in seen_alias or a.isdigit() or ticker in acr_tickers[a]:
                continue
            # an acronym sits in a sentence; a word in an all-caps heading does not
            ctx = text[max(0, m.start() - 30): m.end() + 30]
            if sum(c.islower() for c in ctx) < 20:
                continue
            acr_tickers[a].add(ticker)
        if n % 500 == 0:
            print(f"  {n}/{len(rows)} sections", file=sys.stderr)
    stats = []
    for i, t in enumerate(seed):
        stats.append({
            **t,
            "docs": len(docs[i]),
            "tickers": len(tickers[i]),
            "mentions": mentions[i],
            "top": [k for k, _ in tickers[i].most_common(8)],
        })
    acr = Counter({a: len(ts) for a, ts in acr_tickers.items()})
    return stats, acr, {"sections": len(rows)}


def gaps_md(stats: list[dict], acr: Counter, meta: dict) -> str:
    lines = [
        "# Diagram LSP: coverage and gaps",
        "",
        f"Scanned {meta['sections']} filing sections. {sum(1 for s in stats if s['node'])} of "
        f"{len(stats)} seed terms have a diagram.",
        "",
        "## Frequent terms with no diagram (build these next)",
        "",
        "| term | kind | filings | tickers | top tickers |",
        "|---|---|---:|---:|---|",
    ]
    for s in sorted((s for s in stats if not s["node"]), key=lambda s: -s["tickers"]):
        lines.append(f"| {s['term']} | {s['kind']} | {s['docs']} | {s['tickers']} | {', '.join(s['top'][:5])} |")
    lines += [
        "",
        "## Terms with a diagram",
        "",
        "| term | node | filings | tickers |",
        "|---|---|---:|---:|",
    ]
    for s in sorted((s for s in stats if s["node"]), key=lambda s: -s["tickers"]):
        lines.append(f"| {s['term']} | {s['node']} | {s['docs']} | {s['tickers']} |")
    lines += [
        "",
        "## Acronyms in many companies' filings that are not in the seed",
        "",
        "Candidates to add to py/derive/lsp_terms_seed.json (some are boilerplate: skip those).",
        "",
        "| acronym | tickers |",
        "|---|---:|",
    ]
    for a, n in acr.most_common(150):
        if n < 10:
            break
        lines.append(f"| {a} | {n} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="scan only this many sections")
    a = ap.parse_args()
    stats, acr, meta = scan(a.limit)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "terms.json").write_text(json.dumps(stats, indent=1) + "\n")
    (OUT / "gaps.md").write_text(gaps_md(stats, acr, meta))
    with_node = sum(1 for s in stats if s["node"])
    print(json.dumps({"terms": len(stats), "with_diagram": with_node, "out": str(OUT)}))


if __name__ == "__main__":
    main()
