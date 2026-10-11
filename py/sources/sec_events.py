"""Full EDGAR filing index per company, plus the 8-K event stream.

`filings.parquet` holds every filing listed in data.sec.gov submissions for
every CIK of every universe stock (predecessor CIKs flagged
`is_predecessor`). `events` explodes 8-K / 8-K/A filings to one row per
item code with a label and a signal tier; 6-K (foreign private issuers)
has no item codes, so each 6-K is one row with item NULL.

Signal tiers (how likely an item is to move or re-rate the stock):
  high   Discrete, price-relevant corporate facts: material agreements
         entered/terminated (1.01, 1.02), bankruptcy (1.03), acquisitions or
         disposals completed (2.01), earnings (2.02), restructuring/exit
         costs (2.05) and impairments (2.06), delisting notices (3.01),
         auditor changes (4.01), non-reliance / restatements (4.02), change
         of control (5.01), officer/director departures & appointments
         (5.02). 5.02 is noisy (routine board refreshes, comp plan tweaks
         filed under it) but CEO/CFO exits are among the most informative
         8-Ks, so it stays high and callers can filter by description.
  medium Capital-structure or governance changes that matter sometimes:
         new debt / off-balance-sheet obligations (2.03, 2.04), unregistered
         equity sales (3.02), security-holder rights changes (3.03), mine
         safety (1.04), cybersecurity incidents (1.05), charter/bylaw
         amendments or fiscal-year change (5.03), ABS items (6.xx),
         and 6-K (foreign-filer catch-all: sometimes earnings, often not).
  low    Routine or wrapper items: Reg FD (7.01, usually a slide deck),
         other events (8.01, a grab bag), exhibits (9.01, rides along with
         nearly every 8-K), shareholder votes (5.07), ethics code changes
         (5.05), trading blackouts (5.04), shell status (5.06), shareholder
         nominations (5.08).
Pre-Aug-2004 8-Ks use whole-number items (1-12); they are labelled
"[legacy]" and tiered the same way (12 = earnings, 6 = director exits).

Resumable: each ticker's rows go to raw/<TICKER>.ndjson (skipped if
present unless --refresh); Parquet is rebuilt from all raw files at the end.

CLI:  uv run python sources/sec_events.py ingest [--refresh]
      uv run python sources/sec_events.py show TICKER [DAYS]
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta

import duckdb


from sources import universe
from sources import pq

DIR = universe.data_dir("events")
RAW = DIR / "raw"
FILINGS = DIR / "filings.parquet"
EVENTS = DIR / "events.parquet"

ITEMS: dict[str, tuple[str, str]] = {
    "1.01": ("Entry into a Material Definitive Agreement", "high"),
    "1.02": ("Termination of a Material Definitive Agreement", "high"),
    "1.03": ("Bankruptcy or Receivership", "high"),
    "1.04": ("Mine Safety - Reporting of Shutdowns and Patterns of Violations", "medium"),
    "1.05": ("Material Cybersecurity Incidents", "medium"),
    "2.01": ("Completion of Acquisition or Disposition of Assets", "high"),
    "2.02": ("Results of Operations and Financial Condition", "high"),
    "2.03": ("Creation of a Direct Financial Obligation", "medium"),
    "2.04": ("Triggering Events That Accelerate a Financial Obligation", "medium"),
    "2.05": ("Costs Associated with Exit or Disposal Activities", "high"),
    "2.06": ("Material Impairments", "high"),
    "3.01": ("Notice of Delisting or Failure to Satisfy a Listing Rule", "high"),
    "3.02": ("Unregistered Sales of Equity Securities", "medium"),
    "3.03": ("Material Modification to Rights of Security Holders", "medium"),
    "4.01": ("Changes in Registrant's Certifying Accountant", "high"),
    "4.02": ("Non-Reliance on Previously Issued Financial Statements", "high"),
    "5.01": ("Changes in Control of Registrant", "high"),
    "5.02": ("Departure/Election of Directors or Officers; Compensatory Arrangements", "high"),
    "5.03": ("Amendments to Articles or Bylaws; Change in Fiscal Year", "medium"),
    "5.04": ("Temporary Suspension of Trading Under Employee Benefit Plans", "low"),
    "5.05": ("Amendments to Code of Ethics or Waiver", "low"),
    "5.06": ("Change in Shell Company Status", "low"),
    "5.07": ("Submission of Matters to a Vote of Security Holders", "low"),
    "5.08": ("Shareholder Director Nominations", "low"),
    "6.01": ("ABS Informational and Computational Material", "medium"),
    "6.02": ("Change of Servicer or Trustee", "medium"),
    "6.03": ("Change in Credit Enhancement or Other External Support", "medium"),
    "6.04": ("Failure to Make a Required Distribution", "medium"),
    "6.05": ("Securities Act Updating Disclosure", "medium"),
    "7.01": ("Regulation FD Disclosure", "low"),
    "8.01": ("Other Events", "low"),
    "9.01": ("Financial Statements and Exhibits", "low"),
    # Pre-Aug-2004 8-K numbering (whole-number items; 12 existed 2003-2004).
    "1": ("[legacy] Changes in Control of Registrant", "high"),
    "2": ("[legacy] Acquisition or Disposition of Assets", "high"),
    "3": ("[legacy] Bankruptcy or Receivership", "high"),
    "4": ("[legacy] Changes in Registrant's Certifying Accountant", "high"),
    "5": ("[legacy] Other Events", "low"),
    "6": ("[legacy] Resignations of Registrant's Directors", "high"),
    "7": ("[legacy] Financial Statements and Exhibits", "low"),
    "8": ("[legacy] Change in Fiscal Year", "medium"),
    "9": ("[legacy] Regulation FD Disclosure", "low"),
    "10": ("[legacy] Amendments to Code of Ethics or Waiver", "low"),
    "11": ("[legacy] Temporary Suspension of Trading Under Employee Benefit Plans", "low"),
    "12": ("[legacy] Results of Operations and Financial Condition", "high"),
}
EARNINGS_ITEMS = ("2.02", "12")

_COLS = ("form", "filingDate", "reportDate", "acceptanceDateTime", "accessionNumber",
         "primaryDocument", "primaryDocDescription", "items", "size", "isXBRL")


def _rows(ticker: str, cik: int, pred: bool) -> list[dict]:
    rec = universe.submissions(cik)["filings"]["recent"]
    n = len(rec["accessionNumber"])
    col = {k: rec.get(k) or [None] * n for k in _COLS}
    return [{
        "ticker": ticker, "cik": cik, "is_predecessor": pred,
        "form": col["form"][i], "filed": col["filingDate"][i] or None,
        "report_date": col["reportDate"][i] or None,
        "accepted_at": col["acceptanceDateTime"][i] or None,
        "accn": col["accessionNumber"][i], "primary_doc": col["primaryDocument"][i] or None,
        "description": col["primaryDocDescription"][i] or None,
        "items": col["items"][i] or None, "size": col["size"][i],
        "is_xbrl": bool(col["isXBRL"][i]),
    } for i in range(n)]


def ingest(refresh: bool = False, tickers: list[str] | None = None) -> None:
    RAW.mkdir(exist_ok=True)
    t0 = time.time()
    fails: list[str] = []
    ss = [s for s in universe.stocks() if s["ciks"] and (not tickers or s["ticker"] in tickers)]
    for k, s in enumerate(ss, 1):
        out = RAW / f"{s['ticker']}.ndjson"
        if out.exists() and not refresh:
            continue
        try:
            rows = [r for j, c in enumerate(s["ciks"]) for r in _rows(s["ticker"], c, j > 0)]
        except Exception as e:  # noqa: BLE001 — keep going, report at end
            fails.append(f"{s['ticker']}: {e}")
            print(f"[{k}/{len(ss)}] {s['ticker']} FAILED {e}", flush=True)
            continue
        tmp = out.with_suffix(".part")
        tmp.write_text("".join(json.dumps(r) + "\n" for r in rows))
        tmp.rename(out)
        print(f"[{k}/{len(ss)}] {s['ticker']} {len(rows)} filings", flush=True)
    build()
    print(f"done in {time.time() - t0:.0f}s; {len(fails)} failures")
    for f in fails:
        print("  ", f)


def build() -> None:
    """Rebuild filings.parquet and events.parquet from raw/*.ndjson."""
    con = duckdb.connect()
    pq.copy_atomic(con, f"""
          SELECT ticker, cik::BIGINT AS cik, is_predecessor, form,
                 filed::DATE AS filed, TRY_CAST(report_date AS DATE) AS report_date,
                 TRY_CAST(accepted_at AS TIMESTAMP) AS accepted_at, accn, primary_doc,
                 description, items, size::BIGINT AS size, is_xbrl
          FROM read_json('{RAW}/*.ndjson', format='newline_delimited', columns={{
            ticker:'VARCHAR', cik:'BIGINT', is_predecessor:'BOOLEAN', form:'VARCHAR',
            filed:'VARCHAR', report_date:'VARCHAR', accepted_at:'VARCHAR', accn:'VARCHAR',
            primary_doc:'VARCHAR', description:'VARCHAR', items:'VARCHAR', size:'BIGINT',
            is_xbrl:'BOOLEAN'}})
          ORDER BY ticker, filed, accn
    """, FILINGS, "FORMAT parquet, COMPRESSION zstd")
    labels = ", ".join(f"('{k}', '{v[0].replace(chr(39), chr(39) * 2)}', '{v[1]}')"
                       for k, v in ITEMS.items())
    pq.copy_atomic(con, f"""
          WITH f AS (
            SELECT * FROM '{FILINGS}' WHERE form IN ('8-K', '8-K/A', '6-K', '6-K/A')),
          x AS (
            SELECT f.*, trim(unnest(string_split(items, ','))) AS item
            FROM f WHERE items IS NOT NULL
            UNION ALL
            SELECT f.*, NULL AS item FROM f WHERE items IS NULL),
          lab(item, label, signal) AS (VALUES {labels})
          SELECT x.ticker, x.cik, x.is_predecessor, x.form, x.filed, x.report_date,
                 x.accepted_at, x.accn, x.primary_doc, x.description, x.item,
                 CASE WHEN x.item IS NULL AND x.form LIKE '6-K%' THEN 'Foreign issuer report (6-K)'
                      ELSE lab.label END AS label,
                 CASE WHEN x.item IS NULL AND x.form LIKE '6-K%' THEN 'medium'
                      ELSE coalesce(lab.signal, 'low') END AS signal
          FROM x LEFT JOIN lab USING (item)
          ORDER BY x.ticker, x.filed, x.accn, x.item
    """, EVENTS, "FORMAT parquet, COMPRESSION zstd")


def _q(sql: str, params: list | None = None) -> list[tuple]:
    return duckdb.connect().execute(sql, params or []).fetchall()


def earnings_dates(ticker: str) -> list[date]:
    """Distinct filing dates of 8-K item 2.02 (legacy item 12 pre-2004),
    oldest first. Excludes 8-K/A so restated releases don't add dates."""
    return [r[0] for r in _q(
        f"SELECT DISTINCT filed FROM '{EVENTS}' WHERE ticker = ? AND item IN ? "
        "AND form = '8-K' ORDER BY filed", [ticker.upper(), list(EARNINGS_ITEMS)])]


def recent_events(ticker: str, days: int = 365, min_signal: str = "low") -> list[dict]:
    """Events for a ticker in the last `days`, newest first. min_signal in
    low|medium|high filters by tier."""
    tiers = {"low": ("low", "medium", "high"), "medium": ("medium", "high"), "high": ("high",)}
    since = date.today() - timedelta(days=days)
    cur = duckdb.connect().execute(
        f"SELECT filed, form, item, label, signal, accn, primary_doc, description "
        f"FROM '{EVENTS}' WHERE ticker = ? AND filed >= ? AND signal IN ? "
        "ORDER BY filed DESC, accn, item", [ticker.upper(), since, list(tiers[min_signal])])
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def event_counts(since: date | str) -> list[tuple]:
    """Universe-wide (item, label, signal, events, tickers) since a date."""
    return _q(
        f"SELECT item, any_value(label), any_value(signal), count(*) AS n, "
        f"count(DISTINCT ticker) AS tickers FROM '{EVENTS}' WHERE filed >= ? "
        "GROUP BY item ORDER BY n DESC", [str(since)])


def _show(ticker: str, days: int) -> None:
    t = ticker.upper()
    print(f"{t} filings by form:")
    for f, n in _q(f"SELECT form, count(*) FROM '{FILINGS}' WHERE ticker = ? "
                   "GROUP BY 1 ORDER BY 2 DESC LIMIT 15", [t]):
        print(f"  {f:<12} {n}")
    print("8-K items (all time):")
    for i, lab, n in _q(f"SELECT item, any_value(label), count(*) FROM '{EVENTS}' "
                        "WHERE ticker = ? GROUP BY 1 ORDER BY 3 DESC", [t]):
        print(f"  {i or '-':<5} {n:>4}  {lab}")
    ed = earnings_dates(t)
    print(f"earnings (2.02) dates, last 8 of {len(ed)}: {', '.join(map(str, ed[-8:]))}")
    print(f"events last {days}d:")
    for e in recent_events(t, days):
        print(f"  {e['filed']} {e['form']:<6} {e['item'] or '-':<5} {e['signal']:<6} {e['label']}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "ingest":
        ingest(refresh="--refresh" in sys.argv)
    elif cmd == "build":
        build()
    elif cmd == "show" and len(sys.argv) > 2:
        _show(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 365)
    else:
        print(__doc__)
