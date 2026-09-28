"""SEC Form 13F data sets — institutional holdings (the CANSLIM "I").

One ~100MB zip per filing window (roughly a calendar quarter) holds every
13F-HR filed in it: ~3.8M holding rows across ~11k managers. We keep five
columns, collapse to one row per (filing, cusip, put/call), and write zstd
Parquet (~23MB/window) instead of the ~400MB TSV; the zip is deleted after.

Windows are by *filing* date, not report period — the Jun–Aug zip also
carries late filings for older periods — so nothing is resolved at ingest.
`holdings_sql()` picks the effective filing per (manager, period) at query
time: latest original-or-RESTATEMENT, plus any NEW HOLDINGS amendments
filed after it.

13F has no ticker column (FIGI is on ~12% of rows), so `build_cusip_map()`
maps the ai_stocks.json universe via OpenFIGI tickers -> FIGIs matched
against filer-reported (cusip, figi) pairs, falling back to issuer name.

https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
"""
from __future__ import annotations

import json
import re
import sys
import time
import zipfile
from pathlib import Path

import duckdb
import requests

import db
from sources import sec_http

INDEX_URL = "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"
OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"
DATA_DIR = db.DB_PATH.parent / "sec_13f"
UNIVERSE_PATH = Path(__file__).resolve().parent.parent / "data" / "ai_stocks.json"

# A single filer reporting more than this multiple of the next-largest
# holder's position is almost always a units typo (CalSTRS reported 386M
# MRVL shares for Q2 2026 — 44% of the company). Excluded from summaries.
SUSPECT_MULTIPLE = 3.0

_TSV = "delim='\t', header=true, quote='', escape='', all_varchar=true, ignore_errors=true"


def _dir(name: str) -> Path:
    d = DATA_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def available_windows(n: int = 6) -> list[tuple[str, str]]:
    """(stem, url) for the newest n zips listed on SEC's index page,
    oldest first. Stems look like 01jun2026-31aug2026_form13f."""
    resp = sec_http.get(INDEX_URL, timeout=30)
    resp.raise_for_status()
    hrefs = re.findall(r'href="([^"]*form13f\.zip)"', resp.text)
    seen: dict[str, str] = {}
    for h in hrefs:
        stem = h.rsplit("/", 1)[-1].removesuffix(".zip")
        seen.setdefault(stem, "https://www.sec.gov" + h if h.startswith("/") else h)
    return list(seen.items())[:n][::-1]


def loaded_windows() -> set[str]:
    return {p.stem for p in _dir("holdings").glob("*.parquet")}


def _download(stem: str, url: str) -> Path:
    dest = _dir("tmp") / f"{stem}.zip"
    if dest.exists():
        return dest
    resp = sec_http.stream(url)
    resp.raise_for_status()
    part = dest.with_suffix(".part")
    with open(part, "wb") as f:
        for chunk in resp.iter_content(1 << 20):
            f.write(chunk)
    part.rename(dest)
    return dest


def ingest_window(stem: str, url: str, keep_zip: bool = False) -> int:
    """Convert one zip to holdings/filings/issuers Parquet. Idempotent —
    returns holding rows written, 0 if already loaded."""
    if stem in loaded_windows():
        return 0
    zip_path = _download(stem, url)
    out = _dir("tmp") / stem
    names = ("INFOTABLE.tsv", "COVERPAGE.tsv", "SUBMISSION.tsv")
    # Older zips nest everything under a folder; match on basename.
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        members = {Path(m).name: m for m in z.namelist()}
        for n in names:
            with z.open(members[n]) as src, open(out / n, "wb") as dst:
                while chunk := src.read(1 << 20):
                    dst.write(chunk)
    info, cover, sub = (str(out / n) for n in names)
    targets = {k: _dir(k) / f"{stem}.parquet" for k in ("holdings", "filings", "issuers")}
    parts = {k: p.with_suffix(".part") for k, p in targets.items()}
    con = duckdb.connect()
    try:
        # Principal-amount rows (PRN) are bonds; only share positions matter.
        con.execute(f"""
            COPY (
                SELECT ACCESSION_NUMBER acc, CUSIP cusip,
                       CASE PUTCALL WHEN 'Put' THEN 'P' WHEN 'Call' THEN 'C' END pc,
                       sum(TRY_CAST(SSHPRNAMT AS BIGINT)) sh, sum(TRY_CAST(VALUE AS BIGINT)) val
                FROM read_csv('{info}', {_TSV})
                WHERE SSHPRNAMTTYPE = 'SH'
                GROUP BY ALL ORDER BY cusip, acc
            ) TO '{parts["holdings"]}' (FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 19)
        """)
        con.execute(f"""
            COPY (
                SELECT s.ACCESSION_NUMBER acc, CAST(s.CIK AS INTEGER) cik, c.FILINGMANAGER_NAME mgr,
                       strptime(s.FILING_DATE, '%d-%b-%Y')::DATE filed,
                       strptime(s.PERIODOFREPORT, '%d-%b-%Y')::DATE period,
                       s.SUBMISSIONTYPE subtype, c.AMENDMENTTYPE amend_type
                FROM read_csv('{sub}', {_TSV}) s JOIN read_csv('{cover}', {_TSV}) c USING (ACCESSION_NUMBER)
            ) TO '{parts["filings"]}' (FORMAT parquet, COMPRESSION zstd)
        """)
        # Issuer names + filer-reported (cusip, figi) pair counts, kept only
        # for cusip mapping. Filers mis-pair FIGIs often enough that the
        # pair count, not the cusip's popularity, has to pick the winner.
        con.execute(f"""
            COPY (
                SELECT CUSIP cusip, FIGI figi, mode(upper(NAMEOFISSUER)) issuer,
                       mode(upper(TITLEOFCLASS)) title, count(*) n
                FROM read_csv('{info}', {_TSV})
                WHERE SSHPRNAMTTYPE = 'SH'
                GROUP BY 1, 2
            ) TO '{parts["issuers"]}' (FORMAT parquet, COMPRESSION zstd)
        """)
        rows = con.execute(f"SELECT count(*) FROM read_parquet('{parts['holdings']}')").fetchone()[0]
    except Exception:
        for p in parts.values():
            p.unlink(missing_ok=True)
        raise
    finally:
        con.close()
        for n in names:
            (out / n).unlink(missing_ok=True)
        out.rmdir()
    # holdings last: its presence is the "loaded" marker.
    for k in ("filings", "issuers", "holdings"):
        parts[k].rename(targets[k])
    if not keep_zip:
        zip_path.unlink(missing_ok=True)
    return rows


def ensure_recent(n: int = 6) -> dict[str, int]:
    """Ingest any of the newest n windows not yet loaded. ~100MB download
    and ~1 min per window on first run."""
    return {stem: ingest_window(stem, url) for stem, url in available_windows(n)}


def holdings_sql() -> str:
    """Effective long-share holdings per (cik, period, cusip) as a SQL
    subquery over the Parquet files. `acc` is the base 13F-HR accession
    (a NEW HOLDINGS amendment can add rows under a later one)."""
    d = DATA_DIR
    return f"""(
        WITH f AS (
            SELECT DISTINCT * FROM read_parquet('{d}/filings/*.parquet')
            WHERE subtype IN ('13F-HR', '13F-HR/A')
        ),
        base AS (
            SELECT * FROM f WHERE amend_type IS NULL OR amend_type = 'RESTATEMENT'
            QUALIFY row_number() OVER (PARTITION BY cik, period ORDER BY filed DESC, acc DESC) = 1
        ),
        adds AS (
            SELECT f.* FROM f JOIN base b USING (cik, period)
            WHERE f.amend_type = 'NEW HOLDINGS' AND f.filed >= b.filed
        ),
        eff AS (SELECT acc, cik, mgr, period FROM base UNION ALL SELECT acc, cik, mgr, period FROM adds)
        SELECT e.cik, any_value(e.mgr) mgr, e.period, h.cusip, sum(h.sh) sh, sum(h.val) val,
               min(e.acc) acc  -- base filing's accession, for linking back to the 13F-HR
        FROM eff e JOIN read_parquet('{d}/holdings/*.parquet') h USING (acc)
        WHERE h.pc IS NULL
        GROUP BY e.cik, e.period, h.cusip
    )"""


def _openfigi(tickers: list[str]) -> dict[str, dict]:
    """ticker -> {"ids": [figi, compositeFIGI, shareClassFIGI...], "name": str}
    for US listings, cached in openfigi.json. Keyless limit: 10 jobs/request,
    25 requests/minute."""
    cache_path = DATA_DIR / "openfigi.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    todo = [t for t in tickers if t not in cache]
    for i in range(0, len(todo), 10):
        batch = todo[i:i + 10]
        jobs = [{"idType": "TICKER", "idValue": t.replace(".", "/"), "exchCode": "US"} for t in batch]
        resp = requests.post(OPENFIGI_URL, json=jobs, timeout=30)
        if resp.status_code == 429:
            time.sleep(60)
            resp = requests.post(OPENFIGI_URL, json=jobs, timeout=30)
        resp.raise_for_status()
        for t, res in zip(batch, resp.json()):
            data = res.get("data", [])
            ids = sorted({x[k] for x in data for k in ("figi", "compositeFIGI", "shareClassFIGI") if x.get(k)})
            cache[t] = {"ids": ids, "name": data[0]["name"] if data else None}
        cache_path.write_text(json.dumps(cache))
        time.sleep(2.5)
    return {t: cache[t] for t in tickers}


_NAME_NOISE = re.compile(
    r"\b(INC|CORP|CORPORATION|CO|LTD|LIMITED|PLC|HOLDINGS?|GROUP|NV|N V|SA|AG|SE|ADR|ADS|SPONSORED|SPON|"
    r"COM|CL [A-Z]|CLASS [A-Z]|NEW|THE|TECHNOLOGIES|TECHNOLOGY|TECH)\b"
)


def _norm(name: str) -> str:
    s = re.sub(r"[^A-Z0-9 ]", " ", (name or "").upper().replace("'", ""))
    return " ".join(_NAME_NOISE.sub(" ", s).split())


def _names_agree(a: str, b: str) -> bool:
    return bool(set(_norm(a).split()) & set(_norm(b).split()))


def build_cusip_map() -> dict[str, int]:
    """Map every universe ticker to a 13F cusip. Writes cusip_map.parquet
    (ticker, cusip, method, issuer, figi_name). Returns method counts.

    figi: OpenFIGI ids -> the cusip filers pair them with most often, kept
    only if the issuer name shares a word with OpenFIGI's name.
    name: exact normalized issuer-name match (OpenFIGI name, then the
    universe's own name); catches foreign listings via their US ADRs."""
    stocks = json.loads(UNIVERSE_PATH.read_text())["stocks"]
    con = duckdb.connect()
    # Window start date from the file stem (01jun2026-31aug2026_form13f)
    # so a FIGI whose cusip changed (spin-off, redomicile) follows the new one.
    pairs = con.execute(f"""
        SELECT cusip, figi, strptime(split_part(parse_filename(filename, true), '-', 1), '%d%b%Y') win, sum(n) n
        FROM read_parquet('{DATA_DIR}/issuers/*.parquet', filename = true)
        WHERE figi IS NOT NULL GROUP BY 1, 2, 3
    """).fetchall()
    issuers = con.execute(f"""
        SELECT cusip, mode(issuer) issuer, sum(n) n FROM read_parquet('{DATA_DIR}/issuers/*.parquet') GROUP BY 1
    """).fetchall()
    con.close()

    best: dict[str, tuple] = {}
    for cusip, figi, win, n in pairs:
        if figi not in best or (win, n) > best[figi][1:]:
            best[figi] = (cusip, win, n)
    by_figi = {f: (c, n) for f, (c, _, n) in best.items()}
    by_name: dict[str, tuple[str, int]] = {}
    for cusip, issuer, n in issuers:
        k = _norm(issuer)
        if k and n >= 20 and (k not in by_name or n > by_name[k][1]):
            by_name[k] = (cusip, n)
    names = {c: nm for c, nm, _ in issuers}

    figi = _openfigi([s["ticker"] for s in stocks if "." not in s["ticker"]])
    rows, counts = [], {"figi": 0, "figi_unverified": 0, "name": 0, "unmapped": 0}
    for s in stocks:
        t = s["ticker"]
        f = figi.get(t) or {"ids": [], "name": None}
        hits = [by_figi[i] for i in f["ids"] if i in by_figi]
        agreed = [h for h in hits if not f["name"] or _names_agree(f["name"], names.get(h[0]))]
        if agreed or hits:
            cusip = max(agreed or hits, key=lambda h: h[1])[0]
            method = "figi" if agreed else "figi_unverified"
        else:
            match = by_name.get(_norm(f["name"] or "")) or by_name.get(_norm(s["name"]))
            cusip, method = (match[0], "name") if match else (None, "unmapped")
        rows.append((t, cusip, method, names.get(cusip), f["name"]))
        counts[method] += 1

    con = duckdb.connect()
    con.execute("CREATE TABLE m (ticker VARCHAR, cusip VARCHAR, method VARCHAR, issuer VARCHAR, figi_name VARCHAR)")
    con.executemany("INSERT INTO m VALUES (?, ?, ?, ?, ?)", rows)
    con.execute(f"COPY m TO '{DATA_DIR}/cusip_map.parquet' (FORMAT parquet)")
    con.close()
    return counts


def summary(tickers: list[str] | None = None) -> list[dict]:
    """Per ticker, latest two periods: holder count, shares held, new and
    exited positions — restricted to managers who filed in both periods so
    filer churn doesn't read as buying. Suspect typo positions excluded."""
    con = duckdb.connect()
    try:
        con.execute(f"CREATE TEMP TABLE h AS SELECT * FROM {holdings_sql()}")
        cur, prev = [r[0] for r in con.execute("SELECT DISTINCT period FROM h ORDER BY 1 DESC LIMIT 2").fetchall()]
        rows = con.execute(f"""
            WITH panel AS (
                SELECT cik FROM h WHERE period = $prev INTERSECT SELECT cik FROM h WHERE period = $cur
            ),
            ranked AS (
                SELECT *, max(sh) FILTER (WHERE rn = 2) OVER (PARTITION BY cusip, period) runner_up
                FROM (SELECT *, row_number() OVER (PARTITION BY cusip, period ORDER BY sh DESC) rn FROM h)
            ),
            clean AS (
                SELECT * FROM ranked
                WHERE NOT (rn = 1 AND sh > {SUSPECT_MULTIPLE} * runner_up)
                  AND period IN ($prev, $cur) AND cik IN (SELECT cik FROM panel)
            ),
            w AS (
                SELECT cusip, cik,
                       sum(sh) FILTER (WHERE period = $prev) a, sum(sh) FILTER (WHERE period = $cur) b
                FROM clean GROUP BY 1, 2
            )
            SELECT m.ticker, m.method,
                   count(a) holders_prev, count(b) holders, sum(a) shares_prev, sum(b) shares,
                   count(*) FILTER (WHERE a IS NULL AND cik IS NOT NULL) new_pos,
                   count(*) FILTER (WHERE b IS NULL AND cik IS NOT NULL) exited
            FROM read_parquet('{DATA_DIR}/cusip_map.parquet') m LEFT JOIN w USING (cusip)
            WHERE len($tickers) = 0 OR list_contains($tickers, m.ticker)
            GROUP BY 1, 2 ORDER BY holders DESC NULLS LAST
        """, {"prev": prev, "cur": cur, "tickers": [t.upper() for t in tickers or []]}).fetchall()
        cols = ["ticker", "method", "holders_prev", "holders", "shares_prev", "shares", "new_pos", "exited"]
        return [dict(zip(cols, r)) | {"period": str(cur), "period_prev": str(prev)} for r in rows]
    finally:
        con.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if cmd == "ingest":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
        print(json.dumps(ensure_recent(n), indent=2))
    elif cmd == "map":
        print(json.dumps(build_cusip_map(), indent=2))
    else:
        print(json.dumps(summary(sys.argv[2:] or None), indent=2, default=str))
