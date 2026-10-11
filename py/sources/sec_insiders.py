"""SEC Insider Transactions Data Sets — Forms 3/4/5 for the universe.

One ~11MB zip per calendar quarter (by filing date) holds every Form 3/4/5
filed in it as TSVs (SUBMISSION, REPORTINGOWNER, NONDERIV_TRANS,
DERIV_TRANS, FOOTNOTES, ...). We keep only filings whose issuer CIK is in
the universe (current + predecessor CIKs), join them into one
transactions table and write zstd Parquet per quarter; the zip is deleted.

Joint filings (fund + GP, spouse + insider) list several reporting owners
for one set of transactions. To avoid double counting we attribute each
transaction to the lowest owner CIK and keep `n_owners` / `owner_names`.

is_10b5_1: the filing-level AFF10B5ONE checkbox (Forms filed since the
2023 rule change) OR a 10b5-1 mention in any footnote the row references
or in the filing's remarks. `plan_src` says which fired.

Signal note: only code P (open-market buy) and discretionary S (not
10b5-1) carry much information; M/F/A/G/C are compensation mechanics.

https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

import duckdb

from sources import sec_http, universe

INDEX_URL = "https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets"
DATA_DIR = universe.data_dir("insiders")
TX_DIR = DATA_DIR / "transactions"
TMP_DIR = DATA_DIR / "tmp"

_TSV = "delim='\t', header=true, quote='', escape='', all_varchar=true, ignore_errors=true"
_NAMES = ("SUBMISSION.tsv", "REPORTINGOWNER.tsv", "NONDERIV_TRANS.tsv", "DERIV_TRANS.tsv", "FOOTNOTES.tsv")
# Footnote-reference columns shared by NONDERIV_TRANS and DERIV_TRANS.
_FN_COLS = (
    "SECURITY_TITLE_FN", "TRANS_DATE_FN", "DEEMED_EXECUTION_DATE_FN", "EQUITY_SWAP_TRANS_CD_FN",
    "TRANS_TIMELINESS_FN", "TRANS_SHARES_FN", "TRANS_PRICEPERSHARE_FN", "TRANS_ACQUIRED_DISP_CD_FN",
    "SHRS_OWND_FOLWNG_TRANS_FN", "DIRECT_INDIRECT_OWNERSHIP_FN", "NATURE_OF_OWNERSHIP_FN",
)
_PLAN_RE = r"10b5-?1|10b-5-?1|10b5\(1\)|10b5 1"


def _dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def available_quarters(n: int = 6) -> list[tuple[str, str]]:
    """(stem, url) for the newest n zips on SEC's index page, oldest first.
    Stems look like 2026q2_form345."""
    resp = sec_http.get(INDEX_URL)
    resp.raise_for_status()
    seen: dict[str, str] = {}
    for h in re.findall(r'href="([^"]*form345\.zip)"', resp.text):
        stem = h.rsplit("/", 1)[-1].removesuffix(".zip")
        seen.setdefault(stem, "https://www.sec.gov" + h if h.startswith("/") else h)
    return sorted(seen.items(), reverse=True)[:n][::-1]


def loaded_quarters() -> set[str]:
    return {p.stem for p in _dir(TX_DIR).glob("*.parquet")}


def _download(stem: str, url: str) -> Path:
    dest = _dir(TMP_DIR) / f"{stem}.zip"
    if dest.exists():
        return dest
    part = dest.with_suffix(".part")
    try:
        with sec_http.stream(url) as resp:
            resp.raise_for_status()
            with open(part, "wb") as f:
                for chunk in resp.iter_content(1 << 20):
                    f.write(chunk)
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    part.rename(dest)
    return dest


def _universe_map(only: set[str] | None = None) -> list[tuple[int, str]]:
    """(cik, ticker) for every CIK in the universe, predecessors included.
    `only` limits it to those tickers (backfill)."""
    out = {}
    for s in universe.stocks():
        if only and s["ticker"] not in only:
            continue
        for c in s["ciks"]:
            out.setdefault(int(c), s["ticker"])
    return sorted(out.items())


def _tx_select(table: str, kind: str) -> str:
    fns = ", ".join(f"coalesce({c}, '')" for c in _FN_COLS)
    return f"""
        SELECT ACCESSION_NUMBER acc, '{kind}' kind, SECURITY_TITLE security_title,
               try_strptime(TRANS_DATE, '%d-%b-%Y')::DATE trans_date, TRANS_CODE code,
               TRY_CAST(TRANS_SHARES AS DOUBLE) shares, TRY_CAST(TRANS_PRICEPERSHARE AS DOUBLE) price,
               TRANS_ACQUIRED_DISP_CD acquired_disposed,
               TRY_CAST(SHRS_OWND_FOLWNG_TRANS AS DOUBLE) shares_owned_after,
               DIRECT_INDIRECT_OWNERSHIP direct_indirect, NATURE_OF_OWNERSHIP nature,
               regexp_extract_all(concat_ws(',', {fns}), 'F[0-9]+') fn_ids
        FROM read_csv('{table}', {_TSV})
        WHERE ACCESSION_NUMBER IN (SELECT acc FROM sub)
    """


def ingest_quarter(stem: str, url: str, keep_zip: bool = False, only: set[str] | None = None) -> int:
    """Convert one zip to transactions/<stem>.parquet. Idempotent — returns
    rows written, 0 if already loaded. With `only`, keeps just those tickers
    and writes transactions/<stem>+<TICKERS>.parquet: the quarter's main file
    only covers tickers that were in the universe when it was loaded."""
    out_stem = stem if not only else f"{stem}+{'-'.join(sorted(only))[:80]}"
    if out_stem in loaded_quarters():
        return 0
    zip_path = _download(stem, url)
    out = _dir(TMP_DIR / stem)
    # Some zips nest files under a folder; match on basename.
    with zipfile.ZipFile(zip_path) as z:
        members = {Path(m).name: m for m in z.namelist()}
        for n in _NAMES:
            with z.open(members[n]) as src, open(out / n, "wb") as dst:
                while chunk := src.read(1 << 20):
                    dst.write(chunk)
    sub, own, nd, dv, fn = (str(out / n) for n in _NAMES)
    target = _dir(TX_DIR) / f"{out_stem}.parquet"
    part = target.with_suffix(".part")
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE uni (cik INTEGER, ticker VARCHAR)")
        con.executemany("INSERT INTO uni VALUES (?, ?)", _universe_map(only))
        con.execute(f"""
            CREATE TABLE sub AS
            SELECT s.ACCESSION_NUMBER acc, u.ticker, TRY_CAST(s.ISSUERCIK AS INTEGER) issuer_cik,
                   s.DOCUMENT_TYPE form,
                   try_strptime(s.FILING_DATE, '%d-%b-%Y')::DATE filed,
                   try_strptime(s.PERIOD_OF_REPORT, '%d-%b-%Y')::DATE period,
                   lower(s.AFF10B5ONE) IN ('1', 'true') aff10b5one,
                   coalesce(regexp_matches(s.REMARKS, '{_PLAN_RE}', 'i'), false) remarks_plan
            FROM read_csv('{sub}', {_TSV}) s
            JOIN uni u ON u.cik = TRY_CAST(s.ISSUERCIK AS INTEGER)
        """)
        con.execute(f"""
            CREATE TABLE own AS
            SELECT acc, arg_min(owner_cik, owner_cik) owner_cik,
                   arg_min(owner_name, owner_cik) owner_name,
                   arg_min(relationship, owner_cik) relationship,
                   arg_min(officer_title, owner_cik) officer_title,
                   count(*) n_owners, string_agg(owner_name, '; ' ORDER BY owner_cik) owner_names
            FROM (
                SELECT ACCESSION_NUMBER acc, TRY_CAST(RPTOWNERCIK AS BIGINT) owner_cik,
                       RPTOWNERNAME owner_name, RPTOWNER_RELATIONSHIP relationship,
                       nullif(coalesce(nullif(RPTOWNER_TITLE, ''), RPTOWNER_TXT), '') officer_title
                FROM read_csv('{own}', {_TSV})
                WHERE ACCESSION_NUMBER IN (SELECT acc FROM sub)
            ) GROUP BY acc
        """)
        con.execute(f"""
            CREATE TABLE fnp AS
            SELECT ACCESSION_NUMBER acc, list(FOOTNOTE_ID) ids
            FROM read_csv('{fn}', {_TSV})
            WHERE ACCESSION_NUMBER IN (SELECT acc FROM sub)
              AND regexp_matches(FOOTNOTE_TXT, '{_PLAN_RE}', 'i')
            GROUP BY 1
        """)
        con.execute(f"""
            COPY (
                WITH tx AS ({_tx_select(nd, 'nonderiv')} UNION ALL {_tx_select(dv, 'deriv')}),
                j AS (
                    SELECT s.ticker, s.issuer_cik, s.acc accn, s.form, s.filed, s.period,
                           o.owner_cik, o.owner_name, o.relationship, o.officer_title,
                           o.n_owners, o.owner_names,
                           t.kind, t.security_title, t.trans_date, t.code, t.shares, t.price,
                           t.shares * t.price AS value, t.acquired_disposed, t.shares_owned_after,
                           t.direct_indirect, t.nature,
                           s.aff10b5one,
                           coalesce(len(list_intersect(t.fn_ids, f.ids)) > 0, false) OR s.remarks_plan fn_plan
                    FROM tx t JOIN sub s ON s.acc = t.acc
                    LEFT JOIN own o ON o.acc = t.acc
                    LEFT JOIN fnp f ON f.acc = t.acc
                )
                SELECT * EXCLUDE (aff10b5one, fn_plan),
                       aff10b5one OR fn_plan is_10b5_1,
                       CASE WHEN aff10b5one AND fn_plan THEN 'both' WHEN aff10b5one THEN 'flag'
                            WHEN fn_plan THEN 'footnote' END plan_src
                FROM j ORDER BY ticker, trans_date, accn
            ) TO '{part}' (FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 19)
        """)
        rows = con.execute(f"SELECT count(*) FROM read_parquet('{part}')").fetchone()[0]
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    finally:
        con.close()
        for n in _NAMES:
            (out / n).unlink(missing_ok=True)
        out.rmdir()
    part.rename(target)
    if not keep_zip:
        zip_path.unlink(missing_ok=True)
    return rows


def ensure_recent(n: int = 6) -> dict[str, int]:
    """Ingest any of the newest n quarters not yet loaded."""
    return {stem: ingest_quarter(stem, url) for stem, url in available_quarters(n)}


def backfill(tickers: list[str], n: int = 6) -> dict[str, int]:
    """Insider history for tickers added after the quarters were loaded."""
    only = {t.upper() for t in tickers}
    return {stem: ingest_quarter(stem, url, only=only) for stem, url in available_quarters(n)}


def tx_sql() -> str:
    """All loaded transactions, with 4/A restatements collapsed: one row per
    (issuer, owner, date, code, shares, price, acq/disp, kind), latest filing wins."""
    return f"""(
        SELECT * FROM read_parquet('{TX_DIR}/*.parquet')
        QUALIFY row_number() OVER (
            PARTITION BY issuer_cik, owner_cik, trans_date, code, shares, price, acquired_disposed, kind,
                         security_title
            ORDER BY filed DESC, accn DESC) = 1
    )"""


def _rows(sql: str, params: dict | None = None) -> list[dict]:
    con = duckdb.connect()
    try:
        cur = con.execute(sql, params or {})
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        con.close()


def open_market(ticker: str, since: date | str | None = None) -> list[dict]:
    """Open-market buys (P) and sells (S) of non-derivative stock for a ticker."""
    since = since or (date.today() - timedelta(days=365))
    return _rows(f"""
        SELECT trans_date, filed, owner_name, relationship, officer_title, code, shares, price,
               value, shares_owned_after, direct_indirect, is_10b5_1, plan_src, form, accn
        FROM {tx_sql()}
        WHERE ticker = $t AND kind = 'nonderiv' AND code IN ('P', 'S') AND trans_date >= $since
        ORDER BY trans_date DESC, owner_name
    """, {"t": ticker.upper(), "since": str(since)})


def cluster_buys(min_insiders: int = 2, window_days: int = 30, since: date | str | None = None,
                 min_value: float = 25_000) -> list[dict]:
    """Per ticker, the best window where >= min_insiders distinct insiders each
    bought >= min_value of common stock on the open market (code P) within
    window_days. min_value drops token/ESPP-style buys (TSMC's Taiwan
    employee purchases, EPAM's $7.5k director buys); preferred stock (MSTR's
    STRC/STRK) is excluded. Ranked by insider count then dollar value."""
    since = since or (date.today() - timedelta(days=548))
    return _rows(f"""
        WITH b AS (
            SELECT ticker, owner_cik, owner_name, trans_date, coalesce(value, 0) AS value
            FROM {tx_sql()}
            WHERE kind = 'nonderiv' AND code = 'P' AND trans_date >= $since
              AND NOT regexp_matches(security_title, 'prefer|note|warrant|debenture', 'i')
        ),
        per AS (
            SELECT a.ticker, a.trans_date AS start, x.owner_cik, any_value(x.owner_name) AS owner_name,
                   max(x.trans_date) AS last, sum(x.value) AS value, count(*) AS n
            FROM (SELECT DISTINCT ticker, trans_date FROM b) a
            JOIN b x ON x.ticker = a.ticker AND x.trans_date BETWEEN a.trans_date AND a.trans_date + CAST($w AS INTEGER)
            GROUP BY 1, 2, 3
            HAVING sum(x.value) >= $v
        ),
        w AS (
            SELECT ticker, start, max(last) AS "end", count(*) AS insiders, sum(value) AS value,
                   sum(n) AS buys, string_agg(owner_name, '; ' ORDER BY value DESC) AS names
            FROM per GROUP BY 1, 2
        )
        SELECT * FROM w WHERE insiders >= $m
        QUALIFY row_number() OVER (PARTITION BY ticker ORDER BY insiders DESC, value DESC, start DESC) = 1
        ORDER BY insiders DESC, value DESC
    """, {"m": min_insiders, "w": window_days, "since": str(since), "v": min_value})


def stats() -> dict:
    con = duckdb.connect()
    try:
        g = f"read_parquet('{TX_DIR}/*.parquet')"
        return {
            "quarters": sorted(loaded_quarters()),
            "rows": con.execute(f"SELECT count(*) FROM {g}").fetchone()[0],
            "tickers": con.execute(f"SELECT count(DISTINCT ticker) FROM {g}").fetchone()[0],
            "issuer_ciks": con.execute(f"SELECT count(DISTINCT issuer_cik) FROM {g}").fetchone()[0],
            "codes": dict(con.execute(f"SELECT code, count(*) FROM {g} GROUP BY 1 ORDER BY 2 DESC").fetchall()),
            "plan_src": dict(con.execute(f"SELECT coalesce(plan_src,'none'), count(*) FROM {g} WHERE code='S' GROUP BY 1").fetchall()),
            "mb": round(sum(p.stat().st_size for p in TX_DIR.glob("*.parquet")) / 1e6, 2),
        }
    finally:
        con.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "ingest":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
        print(json.dumps(ensure_recent(n), indent=2))
    elif cmd == "show":
        for r in open_market(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None):
            print(f"{r['trans_date']} {r['code']} {r['shares'] or 0:>12,.0f} @ {r['price'] or 0:>9.2f} "
                  f"${(r['value'] or 0) / 1e6:>7.2f}M {'10b5-1' if r['is_10b5_1'] else '      '} "
                  f"{r['owner_name']} ({r['officer_title'] or r['relationship']})")
    elif cmd == "buys":
        print(json.dumps(cluster_buys(), indent=2, default=str))
    else:
        print(json.dumps(stats(), indent=2, default=str))
