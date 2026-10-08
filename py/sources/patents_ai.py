"""USPTO AI Patent Dataset (AIPD, ODP product ECOPATAI, release 2023_r1)
joined onto the universe's granted patents from sources/patents.py.

AIPD is USPTO's own ML classifier over every US grant (1976 - 2023-12-26)
and pre-grant publication (2001-2023): for each of 8 AI components it gives
a score in [0,1] and predict50/86/93 flags (score over the 50/86/93%
precision thresholds). We keep predict50 (USPTO's headline definition) and
the raw score, plus predict93 any-AI as `any_ai93`: predict50 is generous
(the "hardware" component flags ~65% of enterprise-software grants), so
use any_ai93 / ml for "real AI" share. Only grants are joined (utility + reissue); design, plant
and post-2023 grants have no label, so per-year shares stop at 2023.
Grant ids are the same strings as PatentsView patent_id ("10000000",
"RE49770"), so the join is exact.

Outputs in patents/:
    ai.parquet                patent_id, pub_dt, any_ai, any_ai93, <cat> (bool), <cat>_score
                              for cat in ml, evo, nlp, speech, vision, planning, kr, hardware
    ai_by_ticker_year.parquet ticker, year, n_patents (AIPD-covered grants), n_ai_any,
                              pct_ai, n_ai93, pct_ai93, n_<cat>

    python sources/patents_ai.py          # build (extracts the csv once)
    python sources/patents_ai.py top      # top tickers by AI share + a few trends
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import duckdb


from sources import universe

AIPD = universe.data_dir("bulk/aipd")
PAT = universe.data_dir("patents")
ZIP = AIPD / "2023_r1_ai_model_predictions.csv.zip"
CSV = AIPD / "ai_model_predictions.csv"
COVERED_THROUGH = "2023-12-26"
CATS = ["ml", "evo", "nlp", "speech", "vision", "planning", "kr", "hardware"]


def extract() -> Path:
    if not CSV.exists():
        if not ZIP.exists():
            raise SystemExit(f"missing {ZIP.name}: run sources/bulk_pull.py aipd")
        with zipfile.ZipFile(ZIP) as zf:
            zf.extract("ai_model_predictions.csv", AIPD)
    return CSV


def build() -> None:
    csv = extract()
    con = duckdb.connect()
    cats = ",\n".join(f"predict50_{c} = '1' AS {c}, TRY_CAST(ai_score_{c} AS DOUBLE) AS {c}_score" for c in CATS)
    con.execute(f"""
        COPY (
            SELECT a.doc_id AS patent_id, TRY_CAST(a.pub_dt AS DATE) AS pub_dt,
                   a.predict50_any_ai = '1' AS any_ai, a.predict93_any_ai = '1' AS any_ai93,
                   {cats}
            FROM read_csv('{csv}', all_varchar=true) a
            SEMI JOIN '{PAT}/patents.parquet' p ON p.patent_id = a.doc_id
            WHERE a.flag_patent = '1'
        ) TO '{PAT}/ai.parquet' (FORMAT parquet)""")
    per_cat = ",\n".join(f"count(*) FILTER (WHERE ai.{c}) AS n_{c}" for c in CATS)
    # Denominator = grants AIPD could have labelled: utility/reissue granted through its cutoff.
    con.execute(f"""
        COPY (
            SELECT t.ticker, year(p.date) AS year, count(*) AS n_patents,
                   count(*) FILTER (WHERE ai.any_ai) AS n_ai_any,
                   round(100.0 * count(*) FILTER (WHERE ai.any_ai) / count(*), 2) AS pct_ai,
                   count(*) FILTER (WHERE ai.any_ai93) AS n_ai93,
                   round(100.0 * count(*) FILTER (WHERE ai.any_ai93) / count(*), 2) AS pct_ai93,
                   {per_cat}
            FROM '{PAT}/patent_ticker.parquet' t
            JOIN '{PAT}/patents.parquet' p USING (patent_id)
            LEFT JOIN '{PAT}/ai.parquet' ai USING (patent_id)
            WHERE p.type IN ('utility', 'reissue') AND p.date <= DATE '{COVERED_THROUGH}'
            GROUP BY ALL
        ) TO '{PAT}/ai_by_ticker_year.parquet' (FORMAT parquet)""")
    covered, matched = con.execute(f"""
        SELECT count(*), count(ai.patent_id)
        FROM '{PAT}/patents.parquet' p LEFT JOIN '{PAT}/ai.parquet' ai USING (patent_id)
        WHERE p.type IN ('utility', 'reissue') AND p.date <= DATE '{COVERED_THROUGH}'""").fetchone()
    n_ai = con.execute(f"SELECT count(*) FILTER (WHERE any_ai) FROM '{PAT}/ai.parquet'").fetchone()[0]
    print(f"ai.parquet: {matched:,} of {covered:,} coverable universe grants matched "
          f"({100 * matched / covered:.2f}%); {n_ai:,} flagged any_ai")


def top(min_patents: int = 200, order: str = "p93") -> None:
    f = f"'{PAT}/ai_by_ticker_year.parquet'"
    print(f"Top 15 by AI share ({order}), grants 2021-2023, min {min_patents} patents:")
    for r in duckdb.sql(f"""
        SELECT ticker, sum(n_patents) n, sum(n_ai_any) ai, round(100.0 * sum(n_ai_any) / sum(n_patents), 1) pct,
               round(100.0 * sum(n_ml) / sum(n_patents), 1) ml, round(100.0 * sum(n_hardware) / sum(n_patents), 1) hw,
               round(100.0 * sum(n_ai93) / sum(n_patents), 1) p93
        FROM {f} WHERE year BETWEEN 2021 AND 2023 GROUP BY 1 HAVING sum(n_patents) >= {min_patents}
        ORDER BY {order} DESC LIMIT 15""").fetchall():
        print(f"  {r[0]:<10} n={r[1]:>6,}  ai50={r[2]:>6,} {r[3]:>5}%  ai93 {r[6]:>5}%  ml {r[4]}%  hw {r[5]}%")
    for t in ("MRVL", "NVDA", "GOOGL", "IBM"):
        rows = duckdb.sql(f"SELECT year, n_patents, pct_ai, pct_ai93 FROM {f} WHERE ticker = '{t}' AND year >= 2015 ORDER BY year").fetchall()
        print(f"{t} (n, ai50%, ai93%): " + "  ".join(f"{y}:{n}/{p}/{q}" for y, n, p, q in rows))


if __name__ == "__main__":
    top() if sys.argv[1:] == ["top"] else build()
