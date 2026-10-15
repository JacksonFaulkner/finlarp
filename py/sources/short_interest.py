"""Short-selling data for the universe: two free public feeds that answer different questions.

    short/short_volume.parquet    FINRA Reg SHO daily short sale volume, one row per ticker per day:
                                  ticker, date, short_volume, short_exempt_volume, total_volume, short_ratio.
                                  Published the evening of the trade date. It is FLOW: how much of the day's volume
                                  was a short sale (market-maker hedging included, so ~45-55% is normal).
    short/short_interest.parquet  Short interest by settlement date (twice a month, published ~7 business days
                                  later): ticker, settlement_date, short_interest, avg_daily_volume, days_to_cover,
                                  source, fetched_at. It is the POSITION: shares still short.
                                  Nasdaq's API serves ~2 years of history for Nasdaq-listed names; NYSE and other
                                  names fall back to Yahoo, which only has the latest two settlements.

    python sources/short_interest.py volume [--days 300] [TICKER ...]
    python sources/short_interest.py interest [--max-age-hours 20] [TICKER ...]
    python sources/short_interest.py all
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import time
from datetime import date, datetime, timedelta, timezone

import duckdb
import requests

from sources import pq, universe, yahoo, yahoo_profile

OUT = universe.data_dir("short")
VOLUME = OUT / "short_volume.parquet"
INTEREST = OUT / "short_interest.parquet"

FINRA_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{:%Y%m%d}.txt"
NASDAQ_URL = "https://api.nasdaq.com/api/quote/{}/short-interest?assetClass=stocks"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
PAUSE_S = 0.35


def _get(url: str, **kw) -> requests.Response:
    return requests.get(url, headers={"User-Agent": UA, "Accept": "application/json, text/plain"}, timeout=25, **kw)


def _tickers(only: list[str] | None) -> list[str]:
    have = [r["ticker"] for r in universe.rows()]
    return [t.upper() for t in only] if only else have


def business_days(start: date, end: date) -> list[date]:
    days, d = [], start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def _merge(path, rows: list[dict], key: list[str], replace_tickers: set[str] | None = None) -> int:
    """Upsert `rows` into the parquet at `path`. With `replace_tickers`, every stored row of those tickers is dropped first
    (a full history re-fetch must not leave stale settlements behind). Returns the row count after the merge."""
    if not rows:
        return 0
    con = duckdb.connect()
    con.execute("CREATE TABLE new AS SELECT * FROM (SELECT unnest($r, recursive := true))", {"r": rows})
    if path.exists():
        con.execute(f"CREATE TABLE old AS SELECT * FROM read_parquet('{path}')")
        if replace_tickers:
            con.execute("DELETE FROM old WHERE ticker IN (SELECT unnest($t))", {"t": sorted(replace_tickers)})
        keys = " AND ".join(f"old.{k} = new.{k}" for k in key)
        con.execute(f"DELETE FROM old WHERE EXISTS (SELECT 1 FROM new WHERE {keys})")
        con.execute("CREATE TABLE merged AS SELECT * FROM old UNION ALL BY NAME SELECT * FROM new")
    else:
        con.execute("CREATE TABLE merged AS SELECT * FROM new")
    pq.copy_atomic(con, f"SELECT * FROM merged ORDER BY {', '.join(key)}", path)
    return con.execute("SELECT count(*) FROM merged").fetchone()[0]


# ---- FINRA daily short sale volume -----------------------------------------------------------------------------

def parse_volume(text: str, wanted: set[str]) -> list[dict]:
    """One FINRA CNMS file -> rows for the tickers we track. A symbol can appear on several lines when its markets are
    reported separately; they are summed."""
    acc: dict[tuple[str, date], list[float]] = {}
    for r in csv.DictReader(io.StringIO(text), delimiter="|"):
        sym = (r.get("Symbol") or "").strip().upper()
        if sym not in wanted or not r.get("Date"):
            continue
        d = datetime.strptime(r["Date"], "%Y%m%d").date()
        cur = acc.setdefault((sym, d), [0.0, 0.0, 0.0])
        cur[0] += float(r["ShortVolume"] or 0)
        cur[1] += float(r["ShortExemptVolume"] or 0)
        cur[2] += float(r["TotalVolume"] or 0)
    return [{"ticker": t, "date": d, "short_volume": sv, "short_exempt_volume": se, "total_volume": tv,
             "short_ratio": (sv / tv) if tv else None}
            for (t, d), (sv, se, tv) in sorted(acc.items())]


def pull_volume(tickers: list[str] | None = None, days: int = 300, today: date | None = None, get=_get) -> dict:
    """Fetch every missing business day since the last stored one (first run: `days` back) and merge it in."""
    today = today or date.today()
    wanted = set(_tickers(tickers))
    start = today - timedelta(days=days)
    if VOLUME.exists():
        last = duckdb.connect().execute(f"SELECT max(date) FROM read_parquet('{VOLUME}')").fetchone()[0]
        if last:
            start = max(start, last + timedelta(days=1))
    fetched, missing, rows = 0, [], []
    for d in business_days(start, today):
        resp = get(FINRA_URL.format(d))
        if resp.status_code in (403, 404):  # FINRA's CDN answers 403 for a file that does not exist: holiday, or not up yet
            missing.append(d.isoformat())
            continue
        resp.raise_for_status()
        day_rows = parse_volume(resp.text, wanted)
        rows += day_rows
        fetched += 1
        if len(rows) > 20000:  # keep memory and the merge small on a long backfill
            _merge(VOLUME, rows, ["ticker", "date"])
            rows = []
    total = _merge(VOLUME, rows, ["ticker", "date"])
    return {"days_fetched": fetched, "days_missing": missing, "rows_total": total}


# ---- short interest ---------------------------------------------------------------------------------------------

def _num(s) -> float | None:
    if s in (None, "", "N/A", "--"):
        return None
    try:
        return float(str(s).replace(",", "").replace("$", ""))
    except ValueError:
        return None


def parse_nasdaq(ticker: str, payload: dict, now: datetime | None = None) -> list[dict] | None:
    """Nasdaq short-interest JSON -> rows, or None when Nasdaq does not carry the ticker (it only supports Nasdaq-listed names)."""
    table = ((payload or {}).get("data") or {}).get("shortInterestTable")
    if not table or not table.get("rows"):
        return None
    now = now or datetime.now(timezone.utc)
    out = []
    for r in table["rows"]:
        try:
            d = datetime.strptime(r["settlementDate"], "%m/%d/%Y").date()
        except (KeyError, ValueError):
            continue
        si = _num(r.get("interest"))
        if si is None:
            continue
        out.append({"ticker": ticker, "settlement_date": d, "short_interest": si,
                    "avg_daily_volume": _num(r.get("avgDailyShareVolume")), "days_to_cover": _num(r.get("daysToCover")),
                    "source": "nasdaq", "fetched_at": now})
    return out or None


def parse_yahoo(ticker: str, dks: dict, now: datetime | None = None) -> list[dict]:
    """Yahoo defaultKeyStatistics -> up to two settlements (latest and the one a month earlier)."""
    now = now or datetime.now(timezone.utc)

    def raw(k):
        v = dks.get(k)
        return v.get("raw") if isinstance(v, dict) else v

    out = []
    for si_key, date_key, dtc in (("sharesShort", "dateShortInterest", raw("shortRatio")),
                                  ("sharesShortPriorMonth", "sharesShortPreviousMonthDate", None)):
        si, ts = raw(si_key), raw(date_key)
        if si is None or ts is None:
            continue
        d = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
        out.append({"ticker": ticker, "settlement_date": d, "short_interest": float(si), "avg_daily_volume": None,
                    "days_to_cover": dtc, "source": "yahoo", "fetched_at": now})
    return out


def _recently_fetched(max_age_hours: float) -> set[str]:
    if not INTEREST.exists() or max_age_hours <= 0:
        return set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    rows = duckdb.connect().execute(
        f"SELECT ticker FROM read_parquet('{INTEREST}') GROUP BY ticker HAVING max(fetched_at) > $c", {"c": cutoff}).fetchall()
    return {r[0] for r in rows}


def pull_interest(tickers: list[str] | None = None, max_age_hours: float = 20, get=_get, pause: float = PAUSE_S) -> dict:
    todo = [t for t in _tickers(tickers) if t not in _recently_fetched(max_age_hours)]
    session = None
    rows, replaced, counts = [], set(), {"nasdaq": 0, "yahoo": 0, "none": 0}
    for t in todo:
        got = None
        try:
            resp = get(NASDAQ_URL.format(t))
            if resp.status_code == 200:
                got = parse_nasdaq(t, resp.json())
        except (requests.RequestException, ValueError):
            got = None
        if got is None:
            try:
                if session is None:
                    session = yahoo.new_session()
                res = yahoo_profile.fetch(session, t, modules="defaultKeyStatistics") or {}
                got = parse_yahoo(t, res.get("defaultKeyStatistics") or {}) or None
            except Exception:  # noqa: BLE001 - one bad ticker must not stop the batch
                got = None
        if got:
            rows += got
            replaced.add(t)
            counts[got[0]["source"]] += 1
        else:
            counts["none"] += 1
        time.sleep(pause)
    total = _merge(INTEREST, rows, ["ticker", "settlement_date"], replace_tickers=replaced)
    return {"tickers": len(todo), **counts, "rows_total": total}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["volume", "interest", "all"])
    ap.add_argument("tickers", nargs="*")
    ap.add_argument("--days", type=int, default=300, help="volume: how far back the first run goes")
    ap.add_argument("--max-age-hours", type=float, default=20, help="interest: skip tickers fetched more recently")
    a = ap.parse_args()
    if a.what in ("volume", "all"):
        print("short volume:", pull_volume(a.tickers or None, a.days))
    if a.what in ("interest", "all"):
        print("short interest:", pull_interest(a.tickers or None, a.max_age_hours))
    return 0


if __name__ == "__main__":
    sys.exit(main())
