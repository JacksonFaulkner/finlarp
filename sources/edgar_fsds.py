"""SEC Financial Statement Data Sets — bulk segment (dimensional) revenue.

companyfacts (sources/edgar.py) only carries undimensioned facts, so a
product/segment revenue split (Micron DRAM vs NAND, NVDA data center vs
gaming) isn't reachable through it. The FSDS zips are the cheap way to get
that for every filer at once: one ~60MB zip per calendar quarter, num.txt
inside has a `segments` column like

    ProductOrService=DRAMProducts;
    BusinessSegments=CDBU;ConsolidationItems=OperatingSegments;

We ingest each quarter once, keep only revenue-tagged rows (with or without
segments — the plain total is needed for sum checks), and store them in
DuckDB keyed by cik. Nothing here interprets members; that's product_mix.

https://www.sec.gov/dera/data/financial-statement-data-sets
"""
from __future__ import annotations

import sys
import time
import zipfile
from datetime import date
from pathlib import Path

import requests


import db
from sources.edgar import REVENUE_CONCEPTS, UA, ticker_to_cik

ZIP_URL = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/{quarter}.zip"
CACHE_DIR = db.DB_PATH.parent / "edgar_fsds"

# Axes that are bookkeeping, not a real split. A row whose only axes are
# these is treated as the undimensioned total.
NOISE_AXES = {"ConsolidationItems"}


def _quarter_label(d: date) -> str:
    return f"{d.year}q{(d.month - 1) // 3 + 1}"


def _shift_quarter(label: str, n: int) -> str:
    y, q = int(label[:4]), int(label[5])
    idx = y * 4 + (q - 1) + n
    return f"{idx // 4}q{idx % 4 + 1}"


def available_quarters(n: int = 8, today: date | None = None) -> list[str]:
    """The last n FSDS quarters that should exist on SEC's side. A quarter's
    zip appears ~1 week after the quarter ends, so the current quarter is
    never included."""
    today = today or date.today()
    latest_closed = _shift_quarter(_quarter_label(today), -1)
    return [_shift_quarter(latest_closed, -i) for i in range(n)][::-1]


def _download(quarter: str) -> Path | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / f"{quarter}.zip"
    if dest.exists():
        return dest
    resp = requests.get(ZIP_URL.format(quarter=quarter), headers={"User-Agent": UA}, timeout=300, stream=True)
    if resp.status_code != 200:
        return None
    tmp = dest.with_suffix(".part")
    with open(tmp, "wb") as f:
        for chunk in resp.iter_content(1 << 20):
            f.write(chunk)
    tmp.rename(dest)
    return dest


def _extract(zip_path: Path) -> tuple[Path, Path]:
    """num.txt is ~600MB; extract to disk beside the zip so DuckDB can
    stream it, then the caller removes it."""
    out = zip_path.with_suffix("")
    out.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extract("num.txt", out)
        z.extract("sub.txt", out)
    return out / "num.txt", out / "sub.txt"


def ingest_quarter(quarter: str, keep_zip: bool = True) -> int:
    """Load one quarter's revenue rows into edgar_segment_revenue.
    Idempotent — returns row count, 0 if already loaded or zip missing."""
    if quarter in db.fsds_loaded_quarters():
        return 0
    zip_path = _download(quarter)
    if zip_path is None:
        return 0
    num_path, sub_path = _extract(zip_path)
    try:
        con = db._conn()
        try:
            tags = ", ".join(f"'{t}'" for t in REVENUE_CONCEPTS)
            noise = ", ".join(f"'{a}'" for a in NOISE_AXES)
            # All parsing stays in SQL — a Python executemany over ~60k rows
            # takes minutes in DuckDB, the SELECT takes under a second.
            # Single-quarter (qtrs=1) and annual (qtrs=4) durations only;
            # YTD cumulatives (2, 3) are noise for us. A row is kept when
            # it has no segments (the plain total) or exactly one non-noise
            # axis; noise-only rows (ConsolidationItems=CorporateNonSegment,
            # usually 0) and multi-axis cross-tabs are dropped.
            con.execute(
                f"""
                INSERT OR REPLACE INTO edgar_segment_revenue
                WITH raw AS (
                    SELECT n.adsh, s.cik, s.form, s.fy, s.fp, s.filed, n.tag, n.ddate, n.qtrs,
                           n.value,
                           list_filter(
                               string_split(rtrim(coalesce(n.segments, ''), ';'), ';'),
                               x -> x <> '' AND split_part(x, '=', 1) NOT IN ({noise})
                           ) AS real_axes,
                           coalesce(n.segments, '') = '' AS is_total
                    FROM read_csv(?, delim='\t', header=true, quote='', escape='',
                                  all_varchar=true, ignore_errors=true) n
                    JOIN read_csv(?, delim='\t', header=true, quote='', escape='',
                                  all_varchar=true, ignore_errors=true) s USING (adsh)
                    WHERE n.tag IN ({tags})
                      AND n.uom = 'USD'
                      AND n.qtrs IN ('1', '4')
                      AND n.value IS NOT NULL
                      AND s.form IN ('10-Q', '10-K', '10-Q/A', '10-K/A', '20-F', '40-F')
                )
                SELECT adsh,
                       CAST(cik AS INTEGER),
                       form,
                       TRY_CAST(fy AS INTEGER),
                       fp,
                       strptime(filed, '%Y%m%d')::DATE,
                       tag,
                       strptime(ddate, '%Y%m%d')::DATE,
                       CAST(qtrs AS INTEGER),
                       CASE WHEN is_total THEN '' ELSE split_part(real_axes[1], '=', 1) END,
                       CASE WHEN is_total THEN '' ELSE split_part(real_axes[1], '=', 2) END,
                       CAST(value AS DOUBLE)
                FROM raw
                WHERE is_total OR len(real_axes) = 1
                """,
                [str(num_path), str(sub_path)],
            )
            count = con.execute(
                "SELECT count(*) FROM edgar_segment_revenue WHERE adsh IN "
                "(SELECT adsh FROM read_csv(?, delim='\t', header=true, quote='', escape='', "
                "all_varchar=true, ignore_errors=true))",
                [str(sub_path)],
            ).fetchone()[0]
            con.execute(
                "INSERT INTO edgar_fsds_loaded VALUES (?, ?, ?)",
                [quarter, time.time(), count],
            )
        finally:
            con.close()
    finally:
        num_path.unlink(missing_ok=True)
        sub_path.unlink(missing_ok=True)
        num_path.parent.rmdir()
        if not keep_zip:
            zip_path.unlink(missing_ok=True)
    return count


def ensure_recent(n: int = 8) -> dict[str, int]:
    """Ingest any of the last n quarters not yet loaded. Slow on first run
    (n zips × ~60MB); a no-op afterwards except once per new quarter."""
    return {q: ingest_quarter(q) for q in available_quarters(n)}


def get_segment_revenue(symbol: str) -> list[dict]:
    cik = ticker_to_cik(symbol)
    if cik is None:
        return []
    return db.get_segment_revenue(cik)


if __name__ == "__main__":
    import json

    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        print(json.dumps(ensure_recent(n), indent=2))
    else:
        symbol = sys.argv[1] if len(sys.argv) > 1 else "MU"
        print(json.dumps(get_segment_revenue(symbol), indent=2))
