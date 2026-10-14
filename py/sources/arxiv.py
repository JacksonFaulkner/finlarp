"""arXiv paper metadata (title, authors, abstract, categories) harvested over OAI-PMH (`oaipmh.arxiv.org/oai`).

    raw/<set>.jsonl.gz  ->  papers.parquet     one row per arXiv id, latest version's metadata

Harvests whole top-level sets and keeps a record when any of its categories is in RELEVANT (all of CS plus
the ML, signal-processing, quantum, materials and photonics categories that map onto the stock universe).
arXiv has no affiliation field, so linking papers to tickers is a later step.

OAI pages are ~1300 records; arXiv asks for one request every few seconds and answers 503 + Retry-After when
pushed, which the harvester honours. The resumption token is saved after every page, so a killed run picks
up where it stopped; a finished set records the date it was harvested through and later runs only fetch
records changed since then. A full first harvest is ~1500 requests (a few hours).

CLI:  uv run python sources/arxiv.py pull [--sets cs,stat,...] [--since 2024-01-01]
      uv run python sources/arxiv.py ingest
      uv run python sources/arxiv.py show "speculative decoding" [LIMIT]
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import duckdb
import requests

from sources import pq, universe

DIR = universe.data_dir("arxiv")
RAW = DIR / "raw"
STATE = DIR / "state.json"
PAPERS = DIR / "papers.parquet"
BASE = "https://oaipmh.arxiv.org/oai"
SETS = ["cs", "stat", "eess", "physics:quant-ph", "physics:cond-mat", "physics:physics"]
# A record is kept when any category matches: a whole archive ("cs") or an exact category ("stat.ML").
RELEVANT = {
    "cs", "eess", "quant-ph", "stat.ML",
    "cond-mat.mtrl-sci", "cond-mat.mes-hall", "cond-mat.supr-con", "cond-mat.dis-nn",
    "physics.app-ph", "physics.optics", "physics.comp-ph", "physics.ins-det",
}
GAP = 3.0  # seconds between requests
NS = {"oai": "http://www.openarchives.org/OAI/2.0/", "a": "http://arxiv.org/OAI/arXiv/"}


def relevant(categories: list[str]) -> bool:
    return any(c in RELEVANT or c.split(".")[0] in RELEVANT for c in categories)


def _load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def _save_state(state: dict) -> None:
    tmp = STATE.with_name(STATE.name + ".part")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True))
    tmp.replace(STATE)


def _get(session: requests.Session, params: dict, retries: int = 8) -> str:
    for attempt in range(retries):
        try:
            r = session.get(BASE, params=params, timeout=180)
        except requests.RequestException as e:
            print(f"  {type(e).__name__}, retrying", file=sys.stderr)
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code == 200:
            return r.text
        if r.status_code in (429, 500, 502, 503, 504):
            wait = int(r.headers.get("Retry-After", "0") or 0) or 30 * (attempt + 1)
            print(f"  HTTP {r.status_code}, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:300]}")
    raise SystemExit("arXiv OAI kept failing; rerun later (progress is saved)")


def _text(el: ET.Element | None, path: str) -> str | None:
    if el is None or (x := el.find(path, NS)) is None or x.text is None:
        return None
    return re.sub(r"\s+", " ", x.text).strip()


def _record(rec: ET.Element) -> dict | None:
    header = rec.find("oai:header", NS)
    if header is None or header.get("status") == "deleted":
        return None
    m = rec.find("oai:metadata/a:arXiv", NS)
    if m is None:
        return None
    cats = (_text(m, "a:categories") or "").split()
    authors = []
    for a in m.findall("a:authors/a:author", NS):
        name = " ".join(p for p in (_text(a, "a:forenames"), _text(a, "a:keyname"), _text(a, "a:suffix")) if p)
        if name:
            authors.append({"name": name, "affiliations": [x.text.strip() for x in a.findall("a:affiliation", NS) if x.text]})
    return {
        "id": _text(m, "a:id"),
        "datestamp": _text(header, "oai:datestamp"),
        "created": _text(m, "a:created"),
        "updated": _text(m, "a:updated"),
        "title": _text(m, "a:title"),
        "abstract": _text(m, "a:abstract"),
        "authors": authors,
        "categories": cats,
        "comments": _text(m, "a:comments"),
        "journal_ref": _text(m, "a:journal-ref"),
        "doi": _text(m, "a:doi"),
        "license": _text(m, "a:license"),
    }


def harvest_set(session: requests.Session, state: dict, spec: str, since: date | None) -> None:
    st = state.setdefault(spec, {})
    if since:
        st.pop("token", None)
        st["from"] = since.isoformat()
    elif "token" not in st and st.get("through"):
        st["from"] = (date.fromisoformat(st["through"]) - timedelta(days=2)).isoformat()
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{spec.replace(':', '_')}.jsonl.gz"
    pages = kept = seen = 0
    started = time.monotonic()
    while True:
        if tok := st.get("token"):
            params = {"verb": "ListRecords", "resumptionToken": tok}
        else:
            params = {"verb": "ListRecords", "metadataPrefix": "arXiv", "set": spec}
            if st.get("from"):
                params["from"] = st["from"]
        t0 = time.monotonic()
        root = ET.fromstring(_get(session, params))
        responded = (_text(root, "oai:responseDate") or "")[:10]
        err = root.find("oai:error", NS)
        if err is not None:
            if err.get("code") == "noRecordsMatch":
                rows, token = [], None
            elif err.get("code") == "badResumptionToken":
                print(f"  {spec}: token expired, restarting from {st.get('from') or 'the beginning'}", file=sys.stderr)
                st.pop("token", None)
                continue
            else:
                raise SystemExit(f"{spec}: OAI error {err.get('code')}: {err.text}")
        else:
            lr = root.find("oai:ListRecords", NS)
            recs = lr.findall("oai:record", NS) if lr is not None else []
            seen += len(recs)
            rows = [r for x in recs if (r := _record(x)) and r["id"] and relevant(r["categories"])]
            t = lr.find("oai:resumptionToken", NS) if lr is not None else None
            token = t.text.strip() if t is not None and t.text and t.text.strip() else None
        if rows:
            with gzip.open(out, "at") as f:
                f.write("".join(json.dumps(r) + "\n" for r in rows))
        kept += len(rows)
        pages += 1
        if token:
            st["token"] = token
        else:
            st.pop("token", None)
            st["through"] = responded or date.today().isoformat()
        _save_state(state)
        if pages % 10 == 0 or not token:
            print(f"{spec}: {pages} pages, {seen} records, {kept} kept, {time.monotonic() - started:.0f}s", flush=True)
        if not token:
            return
        time.sleep(max(0.0, GAP - (time.monotonic() - t0)))


def pull(sets: list[str], since: date | None) -> None:
    state = _load_state()
    session = requests.Session()
    session.headers["User-Agent"] = "finlarp-arxiv-harvester/1.0"
    for spec in sets:
        harvest_set(session, state, spec, since)


def ingest() -> dict:
    files = sorted(RAW.glob("*.jsonl.gz"))
    if not files:
        raise SystemExit(f"no raw arXiv records in {RAW}")
    globs = "[" + ", ".join(f"'{f}'" for f in files) + "]"
    cols = {
        "id": "VARCHAR", "datestamp": "DATE", "created": "DATE", "updated": "DATE", "title": "VARCHAR",
        "abstract": "VARCHAR", "authors": "STRUCT(name VARCHAR, affiliations VARCHAR[])[]",
        "categories": "VARCHAR[]", "comments": "VARCHAR", "journal_ref": "VARCHAR", "doi": "VARCHAR",
        "license": "VARCHAR",
    }
    colspec = ", ".join(f"'{k}': '{v}'" for k, v in cols.items())
    con = duckdb.connect()
    # Old-style ids look like "cs/0101001"; new ones "2410.12345" start with YYMM of first submission.
    pq.copy_atomic(con, f"""
        SELECT id, title, abstract, authors, categories, categories[1] AS primary_category,
               CASE WHEN regexp_matches(id, '^\\d{{4}}\\.')
                    THEN make_date(2000 + left(id, 2)::INT, substr(id, 3, 2)::INT, 1)
                    ELSE make_date(CASE WHEN substr(split_part(id, '/', 2), 1, 2)::INT > 90 THEN 1900 ELSE 2000 END
                                   + substr(split_part(id, '/', 2), 1, 2)::INT,
                                   substr(split_part(id, '/', 2), 3, 2)::INT, 1) END AS first_month,
               created, updated, datestamp, comments, journal_ref, doi, license,
               len(authors) AS n_authors, 'https://arxiv.org/abs/' || id AS url
        FROM read_json({globs}, format='newline_delimited', columns={{{colspec}}})
        QUALIFY row_number() OVER (PARTITION BY id ORDER BY datestamp DESC, updated DESC NULLS LAST) = 1
        ORDER BY first_month DESC, id DESC""", PAPERS)
    n, lo, hi = con.execute(f"SELECT count(*), min(first_month), max(first_month) FROM read_parquet('{PAPERS}')").fetchone()
    return {"papers": n, "first_month_span": [str(lo), str(hi)], "path": str(PAPERS)}


def show(text: str, limit: int) -> None:
    for month, pid, cat, title in duckdb.connect().execute(
            f"SELECT first_month, id, primary_category, title FROM read_parquet('{PAPERS}') "
            f"WHERE title ILIKE ? OR abstract ILIKE ? ORDER BY first_month DESC LIMIT {int(limit)}",
            [f"%{text}%"] * 2).fetchall():
        print(f"{month:%Y-%m} {pid:<16} {cat:<10} {title[:110]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--sets", default=",".join(SETS), help="comma-separated OAI sets (default: %(default)s)")
    p.add_argument("--since", type=date.fromisoformat, help="only records changed on or after this date")
    sub.add_parser("ingest")
    s = sub.add_parser("show")
    s.add_argument("text")
    s.add_argument("limit", nargs="?", type=int, default=30)
    a = ap.parse_args()
    if a.cmd == "pull":
        pull([x.strip() for x in a.sets.split(",") if x.strip()], a.since)
        print(json.dumps(ingest()))
    elif a.cmd == "ingest":
        print(json.dumps(ingest()))
    else:
        show(a.text, a.limit)


if __name__ == "__main__":
    main()
