"""Korean filers from OpenDART (Financial Supervisory Service): SK hynix and Samsung Electronics.

They file with DART, not the SEC, so EDGAR has nothing for them. OpenDART's
fnlttSinglAcntAll returns the full consolidated statements (XBRL-based) of one periodic
report. We pull every quarterly / half / annual report from START_YEAR on and keep the
income-statement lines that matter for the memory pages (revenue, operating income, net
income), one row per (ticker, report, account).

Quarter values: quarterly and half reports carry the 3-month figure in thstrm_amount; the
annual report carries the full year, so Q4 = annual - (Q1 + Q2 + Q3) and is stored with
that formula. Every row keeps rcept_no, the DART filing it came from:
    https://dart.fss.or.kr/dsaf001/main.do?rcpNo=<rcept_no>

Layout under data/dart/:
    facts.parquet   ticker, corp_code, year, quarter, reprt_code, account, value_krw,
                    basis ('reported' | 'derived'), formula, rcept_no, url, pulled_at

Needs OPENDART_API_KEY (.env).

CLI:
    uv run python sources/dart.py ingest          # both companies, all years
    uv run python sources/dart.py show 000660.KS  # quarterly revenue / op income
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.paths import DATA_ROOT  # noqa: E402
from sources import keys  # noqa: E402

API = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
OUT_DIR = DATA_ROOT / "dart"
FACTS = OUT_DIR / "facts.parquet"
START_YEAR = 2019

# DART corp codes (8 digits, from corpCode.xml)
CORPS = {
    "000660.KS": ("00164779", "SK hynix"),
    "005930.KS": ("00126380", "Samsung Electronics"),
}

# report codes, in calendar order; quarter they end
REPORTS = [("11013", 1), ("11012", 2), ("11014", 3), ("11011", 4)]

# income-statement accounts we keep: our name -> DART account_id / Korean names seen in filings
ACCOUNTS = {
    "revenue": ({"ifrs-full_Revenue", "ifrs_Revenue"}, {"매출액", "수익(매출액)", "영업수익"}),
    "operating_income": ({"dart_OperatingIncomeLoss"}, {"영업이익", "영업이익(손실)"}),
    "net_income": ({"ifrs-full_ProfitLoss", "ifrs_ProfitLoss"}, {"당기순이익", "당기순이익(손실)", "분기순이익", "반기순이익"}),
}


def _get(params: dict) -> dict:
    q = {"crtfc_key": keys.require("OPENDART_API_KEY"), **params}
    last = None
    for attempt in range(4):
        try:
            r = requests.get(API, params=q, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:  # network blips: retry with backoff
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"OpenDART unreachable {params}: {last}")


def _match(row: dict) -> str | None:
    if row.get("sj_div") not in ("IS", "CIS"):
        return None
    for name, (ids, kor) in ACCOUNTS.items():
        if row.get("account_id") in ids or row.get("account_nm", "").strip() in kor:
            return name
    return None


def _num(s: str | None) -> float | None:
    if not s or s.strip() in ("", "-"):
        return None
    return float(s.replace(",", ""))


def pull_report(corp: str, year: int, reprt: str) -> tuple[str | None, dict[str, float]]:
    """(rcept_no, {account: 3-month value, or full year for the annual report})."""
    d = _get({"corp_code": corp, "bsns_year": str(year), "reprt_code": reprt, "fs_div": "CFS"})
    if d.get("status") != "000":
        return None, {}
    vals: dict[str, float] = {}
    rcept = None
    for row in d.get("list", []):
        name = _match(row)
        if name and name not in vals and (v := _num(row.get("thstrm_amount"))) is not None:
            vals[name] = v
            rcept = row.get("rcept_no") or rcept
    return rcept, vals


def ingest(tickers: list[str] | None = None) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    this_year = datetime.now().year
    for ticker in tickers or list(CORPS):
        corp, _name = CORPS[ticker]
        for year in range(START_YEAR, this_year + 1):
            got: dict[int, tuple[str, dict[str, float]]] = {}
            for reprt, q in REPORTS:
                rcept, vals = pull_report(corp, year, reprt)
                if rcept and vals:
                    got[q] = (rcept, vals)
                time.sleep(0.15)
            for q, (rcept, vals) in got.items():
                url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}"
                for acct, v in vals.items():
                    if q < 4:
                        rows.append((ticker, corp, year, q, REPORTS[q - 1][0], acct, v, "reported", None, rcept, url, now))
                        continue
                    # annual report: derive Q4 when all three quarters are present
                    got_parts = [got.get(i, (None, {}))[1].get(acct) for i in (1, 2, 3)]
                    parts = [p for p in got_parts if p is not None]
                    if len(parts) == 3:
                        q4 = v - sum(parts)
                        f = f"FY {v:,.0f} - Q1 {parts[0]:,.0f} - Q2 {parts[1]:,.0f} - Q3 {parts[2]:,.0f}"
                        rows.append((ticker, corp, year, 4, "11011", acct, q4, "derived", f, rcept, url, now))
                    rows.append((ticker, corp, year, 0, "11011", acct, v, "reported", "full year", rcept, url, now))
            print(f"{ticker} {year}: quarters {sorted(got)}", file=sys.stderr)
    con = duckdb.connect()
    con.execute("""create table f (ticker varchar, corp_code varchar, year int, quarter int,
        reprt_code varchar, account varchar, value_krw double, basis varchar, formula varchar,
        rcept_no varchar, url varchar, pulled_at varchar)""")
    con.executemany("insert into f values (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.execute(f"copy f to '{FACTS}' (format parquet, compression zstd)")
    print(f"{len(rows)} rows -> {FACTS}", file=sys.stderr)
    return FACTS


def show(ticker: str) -> None:
    con = duckdb.connect()
    print(con.execute(f"""
        select year, quarter, account, round(value_krw / 1e12, 2) as trillion_krw, basis
        from read_parquet('{FACTS}') where ticker = ? and quarter > 0
        order by year, quarter, account""", [ticker]).fetchdf().to_string(index=False))


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["ingest"]
    if cmd == "ingest":
        ingest(args or None)
    elif cmd == "show":
        show(args[0])
    else:
        raise SystemExit(__doc__)
