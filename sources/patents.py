"""Granted US patents for the universe, from the PatentsView bulk tables
that sources/bulk_pull.py drops in bulk/pv/.

Ticker <- assignee matching is exact on a normalized name (case, punctuation
and legal suffixes stripped) against, per ticker:
    SEC registrant name + formerNames (cached submissions JSON)
    Yahoo long name (profiles/profiles.parquet; the only legal name for non-SEC filers)
    Exhibit 21 subsidiaries (filing_text/subsidiaries.parquet)
    patent_aliases.json (acquisitions not yet in a 10-K, spin-off names...)
Suffix stripping can merge a small foreign sub with an unrelated big
assignee ("Westinghouse Electric Pvt. Limited" -> Westinghouse Electric
Company LLC); patent_aliases.json `_exclude` drops those (ticker, org) pairs.
PatentsView's disambiguated assignee_id already folds typos ("MARVELL AISA")
into one org, so exact matching on its canonical name is enough. A name
that normalizes to more than one ticker is dropped and reported.

Outputs in patents/ (all filtered to matched patents):
    assignee_map.parquet  kind (raw|cluster), org, ticker, via, n_patents
    patent_ticker.parquet patent_id, ticker, matched_on (a patent can have co-assignees)
    patents.parquet       patent_id, date, title, type, num_claims, filing_date, application_id
    cpc.parquet           patent_id, cpc_sequence, cpc_group, cpc_subclass, cpc_type
    wipo.parquet          patent_id, wipo_sector_title, wipo_field_title
    abstracts.parquet     patent_id, abstract
    inventors.parquet     patent_id, inventor_id, name

    python sources/patents.py          # build
    python sources/patents.py review   # top matched orgs per ticker + conflicts
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

import duckdb


from sources import universe
from sources import pq

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "data" / "patent_aliases.json"
PV = universe.data_dir("bulk/pv")
OUT = universe.data_dir("patents")
TABLES = ["assignee_disambiguated", "assignee_not_disambiguated", "patent", "application", "cpc_current",
          "wipo_technology", "patent_abstract", "inventor_disambiguated"]

_SUFFIX = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "LTD", "LIMITED", "LLC", "LLP",
    "LP", "PLC", "PTE", "PTY", "AG", "SA", "SAS", "SARL", "SPA", "NV", "BV", "GMBH", "KG", "KK",
    "KABUSHIKI", "KAISHA", "OY", "OYJ", "AB", "ASA", "AS", "SE", "HOLDINGS", "HOLDING", "GROUP",
    "THE", "DE", "DEL", "ULC", "SRL", "BHD", "SDN", "PVT", "PRIVATE",
}
# Normalized names too generic to trust as a match key.
_GENERIC = {"", "TECHNOLOGIES", "TECHNOLOGY", "SYSTEMS", "SOLUTIONS", "INTERNATIONAL", "SERVICES",
            "HOLDINGS", "ENTERPRISES", "INDUSTRIES", "SOFTWARE", "NETWORKS", "LABS", "DIGITAL"}


# Exhibit 21 parser leaks headers/footnotes and bare jurisdictions as "subsidiaries".
_EX21_JUNK = re.compile(
    r"^(as of|at )|december \d|subsidiar|variable interest|wholly.owned|^vies?$|"
    r"^(united states|united kingdom|australia|belgium|brazil|canada|cayman islands|china|denmark|france|"
    r"germany|hong kong|india|ireland|israel|italy|japan|korea|mexico|netherlands|poland|singapore|spain|"
    r"sweden|switzerland|taiwan)$", re.I)


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"&", " AND ", s)
    toks = re.sub(r"[^A-Z0-9 ]+", " ", s).split()
    while toks and toks[-1] in _SUFFIX:
        toks.pop()
    while toks and toks[0] == "THE":
        toks.pop(0)
    out = " ".join(toks)
    return "" if out in _GENERIC or len(out) < 3 else out


def candidates() -> dict[str, set[tuple[str, str]]]:
    """normalized name -> {(ticker, via)}. Tickers sharing a CIK (GOOG/GOOGL) keep the first."""
    names: dict[str, set[tuple[str, str]]] = defaultdict(set)
    seen_cik: set[int] = set()
    keep: set[str] = set()
    for s in universe.stocks():
        t = s["ticker"]
        if s["cik"] and s["cik"] in seen_cik:
            continue
        keep.add(t)
        if not s["cik"]:
            names[norm(s["name"])].add((t, "universe"))
            continue
        seen_cik.add(s["cik"])
        for cik in s["ciks"]:
            p = universe.data_dir("submissions") / f"{cik}.json"
            if not p.exists():
                continue
            sub = json.loads(p.read_text())
            names[norm(sub.get("name", ""))].add((t, "sec_name"))
            for f in sub.get("formerNames") or []:
                names[norm(f.get("name", ""))].add((t, "sec_former"))
    prof = universe.DATA_ROOT / "profiles" / "profiles.parquet"
    if prof.exists():
        for t, long_name in duckdb.sql(f"SELECT ticker, long_name FROM '{prof}' WHERE long_name IS NOT NULL").fetchall():
            if t in keep:
                names[norm(long_name)].add((t, "yahoo"))
    subs = universe.DATA_ROOT / "filing_text" / "subsidiaries.parquet"
    if subs.exists():
        for t, sub in duckdb.sql(f"SELECT DISTINCT ticker, subsidiary FROM '{subs}'").fetchall():
            if t in keep and sub and not _EX21_JUNK.search(sub):
                names[norm(sub)].add((t, "ex21"))
    if MANUAL.exists():
        for t, extra in json.loads(MANUAL.read_text()).items():
            if not t.startswith("_"):
                for n in extra:
                    names[norm(n)].add((t, "manual"))
    names.pop("", None)
    return names


VIA_RANK = ["sec_name", "sec_former", "yahoo", "manual", "ex21", "universe"]


def exclusions() -> set[tuple[str, str]]:
    if not MANUAL.exists():
        return set()
    ex = json.loads(MANUAL.read_text()).get("_exclude", {})
    return {(t, org) for t, orgs in ex.items() if not t.startswith("_") for org in orgs}


def extract() -> dict[str, Path]:
    """Unzip the needed TSVs next to their zips once (DuckDB can't read .zip)."""
    out = {}
    for t in TABLES:
        z = PV / f"g_{t}.tsv.zip"
        tsv = PV / f"g_{t}.tsv"
        if not tsv.exists():
            if not z.exists():
                raise SystemExit(f"missing {z.name}: run sources/bulk_pull.py pv")
            with zipfile.ZipFile(z) as zf:
                member = zf.namelist()[0]
                with zf.open(member) as src, open(tsv.with_suffix(".tsv.part"), "wb") as dst:
                    while chunk := src.read(1 << 24):
                        dst.write(chunk)
            tsv.with_suffix(".tsv.part").rename(tsv)
        out[t] = tsv
    return out


def _csv(path: Path) -> str:
    return (f"read_csv('{path}', delim='\\t', quote='\"', escape='\"', header=true, "
            f"all_varchar=true, strict_mode=false, ignore_errors=true)")


def build() -> None:
    tsv = extract()
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    names = candidates()
    conflicts = {n for n, v in names.items() if len({t for t, _ in v}) > 1}
    excluded = {(t, norm(o)) for t, o in exclusions()}

    def match(org: str) -> tuple[str, str] | None:
        n = norm(org)
        hit = names.get(n)
        if not hit or n in conflicts:
            return None
        t, via = min(hit, key=lambda x: VIA_RANK.index(x[1]))
        return None if (t, n) in excluded else (t, via)

    # Two keys per patent-assignee row: the raw name as printed on the patent,
    # and PatentsView's cluster label. Raw wins (the Samsung Electronics
    # cluster is labelled "SAMSUNG DISPLAY"); the label catches raw typos.
    maps = {}
    for kind, table, col in (("raw", "assignee_not_disambiguated", "raw_assignee_organization"),
                             ("cluster", "assignee_disambiguated", "disambig_assignee_organization")):
        orgs = con.execute(f"""
            SELECT {col}, count(*) FROM {_csv(tsv[table])} WHERE {col} <> '' GROUP BY 1""").fetchall()
        rows = [(o, *m, n) for o, n in orgs if (m := match(o))]
        con.execute(f"""CREATE TABLE {kind}_map AS SELECT * FROM (SELECT
            unnest($o) AS org, unnest($t) AS ticker, unnest($v) AS via, unnest($n) AS n_patents)""",
                    {"o": [r[0] for r in rows], "t": [r[1] for r in rows],
                     "v": [r[2] for r in rows], "n": [r[3] for r in rows]})
        maps[kind] = len(rows)
    pq.copy_atomic(con, "SELECT 'raw' AS kind, * FROM raw_map UNION ALL SELECT 'cluster', * FROM cluster_map",
                   f"{OUT}/assignee_map.parquet")

    con.execute(f"""
        CREATE TABLE pt AS
        SELECT DISTINCT r.patent_id, coalesce(rm.ticker, cm.ticker) AS ticker,
               CASE WHEN rm.ticker IS NOT NULL THEN 'raw' ELSE 'cluster' END AS matched_on
        FROM {_csv(tsv['assignee_not_disambiguated'])} r
        LEFT JOIN {_csv(tsv['assignee_disambiguated'])} d USING (patent_id, assignee_sequence)
        LEFT JOIN raw_map rm ON rm.org = r.raw_assignee_organization
        LEFT JOIN cluster_map cm ON cm.org = d.disambig_assignee_organization
        WHERE coalesce(rm.ticker, cm.ticker) IS NOT NULL""")
    pq.copy_atomic(con, "SELECT * FROM pt", f"{OUT}/patent_ticker.parquet")
    con.execute("CREATE TABLE ids AS SELECT DISTINCT patent_id FROM pt")

    queries = {
        "patents": f"""
            SELECT p.patent_id, TRY_CAST(p.patent_date AS DATE) AS date, p.patent_title AS title,
                   p.patent_type AS type, TRY_CAST(p.num_claims AS INT) AS num_claims,
                   TRY_CAST(a.filing_date AS DATE) AS filing_date, a.application_id
            FROM {_csv(tsv['patent'])} p SEMI JOIN ids USING (patent_id)
            LEFT JOIN {_csv(tsv['application'])} a USING (patent_id)""",
        "cpc": f"""
            SELECT patent_id, TRY_CAST(cpc_sequence AS INT) AS cpc_sequence, cpc_group, cpc_subclass, cpc_type
            FROM {_csv(tsv['cpc_current'])} SEMI JOIN ids USING (patent_id)""",
        "wipo": f"""
            SELECT patent_id, wipo_sector_title, wipo_field_title
            FROM {_csv(tsv['wipo_technology'])} SEMI JOIN ids USING (patent_id)""",
        "abstracts": f"""
            SELECT patent_id, patent_abstract AS abstract
            FROM {_csv(tsv['patent_abstract'])} SEMI JOIN ids USING (patent_id)""",
        "inventors": f"""
            SELECT patent_id, inventor_id,
                   trim(disambig_inventor_name_first || ' ' || disambig_inventor_name_last) AS name
            FROM {_csv(tsv['inventor_disambiguated'])} SEMI JOIN ids USING (patent_id)""",
    }
    for name, q in queries.items():
        pq.copy_atomic(con, q, f"{OUT}/{name}.parquet")
        print(f"{name}: {con.execute(f'SELECT count(*) FROM read_parquet(\'{OUT}/{name}.parquet\')').fetchone()[0]:,}", flush=True)

    n_t, n_p = con.execute("SELECT count(DISTINCT ticker), count(DISTINCT patent_id) FROM pt").fetchone()
    print(f"matched {maps['raw']:,} raw + {maps['cluster']:,} cluster names -> {n_t} tickers, "
          f"{n_p:,} patents; {len(conflicts)} ambiguous names dropped")


def review(top: int = 5) -> None:
    m = f"'{OUT}/assignee_map.parquet'"
    pt = f"'{OUT}/patent_ticker.parquet'"
    for t, n, k, orgs in duckdb.sql(f"""
        WITH top AS (
            SELECT ticker, count(*) AS names,
                   string_agg(org || ' (' || n_patents || ', ' || via || ')', '; ' ORDER BY n_patents DESC)
                     FILTER (WHERE rn <= {top}) AS top_orgs
            FROM (SELECT *, row_number() OVER (PARTITION BY ticker ORDER BY n_patents DESC) rn
                  FROM {m} WHERE kind = 'raw')
            GROUP BY ticker)
        SELECT ticker, count(DISTINCT patent_id) AS patents, any_value(names), any_value(top_orgs)
        FROM {pt} LEFT JOIN top USING (ticker)
        GROUP BY ticker ORDER BY patents DESC""").fetchall():
        print(f"{t:6} {n:>8,} {k or 0:>5}  {orgs}")
    names = candidates()
    conflicts = sorted((n, sorted({t for t, _ in v})) for n, v in names.items() if len({t for t, _ in v}) > 1)
    print(f"\n{len(conflicts)} ambiguous names (dropped):")
    for n, ts in conflicts[:60]:
        print(f"  {n}: {ts}")


if __name__ == "__main__":
    review() if sys.argv[1:] == ["review"] else build()
