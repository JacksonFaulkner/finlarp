"""Does a strong Korean memory session predict US stocks, and where in the US day does it show up?

Signal day: Samsung Electronics (005930.KS) and SK Hynix (000660.KS) both close up more than THRESH on
the Korean session dated the same calendar day as the US session (that session ends before the US open).
Korean closes come from Yahoo; US prices come from the Databento files (see sources/databento_bars.py).

Each US day is split into:
    gap     previous close -> open   (what the Korean move is already worth at the open)
    day     open -> close            (what you capture by buying the open)
    total   previous close -> close

    uv run jobs/korea_signal.py                        # daily table, whole universe
    uv run jobs/korea_signal.py --intraday             # plus the average path through the US session
    uv run jobs/korea_signal.py --tickers AEHR SKHY MU
    uv run jobs/korea_signal.py --thresh 0.02 --top 20

Tickers share one market factor, so the t-stats are not independent: read the spread of the whole
table (counts above and below zero), not just the top rows.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
from zoneinfo import ZoneInfo

import duckdb

from sources import universe, yahoo
from sources.databento_bars import OUT_ROOT

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
KOREA = {"samsung": "005930.KS", "hynix": "000660.KS"}
CHECKPOINTS = ["09:45", "10:00", "10:30", "11:30", "12:30", "14:00", "15:30"]
MIN_SIGNALS = 8
SEMI_BUCKET = "compute_hardware"


def korean_closes(symbol: str, range_: str) -> dict[date, float]:
    resp = yahoo.new_session().get(CHART_URL.format(symbol), params={"range": range_, "interval": "1d"}, timeout=15)
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    close, zone = result["indicators"]["quote"][0]["close"], ZoneInfo("Asia/Seoul")
    return {datetime.fromtimestamp(t, zone).date(): close[i] for i, t in enumerate(result["timestamp"]) if close[i]}


def signal_days(range_: str, thresh: float) -> set[date]:
    out: set[date] | None = None
    for sym in KOREA.values():
        closes = korean_closes(sym, range_)
        days = sorted(closes)
        up = {days[i] for i in range(1, len(days)) if closes[days[i]] / closes[days[i - 1]] - 1 > thresh}
        out = up if out is None else out & up
    return out or set()


def connect(signals: set[date], tickers: list[str] | None) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"CREATE VIEW bars_1d AS SELECT * FROM read_parquet('{OUT_ROOT}/bars_1d/*.parquet')")
    con.execute(f"CREATE VIEW bars_1m AS SELECT * FROM read_parquet('{OUT_ROOT}/bars_1m/*.parquet')")
    con.execute("CREATE TABLE signal (d DATE)")
    con.executemany("INSERT INTO signal VALUES (?)", [(d,) for d in sorted(signals)])
    con.execute("CREATE TABLE semis (symbol VARCHAR)")
    con.executemany(
        "INSERT INTO semis VALUES (?)",
        [(s["ticker"],) for s in universe.rows() if SEMI_BUCKET in s.get("primary", {})],
    )
    pick = f"WHERE symbol IN ({','.join(repr(t) for t in tickers)})" if tickers else ""
    # Databento daily bars are not split-adjusted: a day whose gap is a clean split ratio (2:1, 10:1,
    # reverse splits...) has no usable gap/total return. open->close is unaffected. Zero-price rows
    # are padding from before a listing.
    con.execute(
        f"""
        CREATE TABLE daily AS
        WITH raw AS (
            SELECT symbol, (ts_event AT TIME ZONE 'UTC')::DATE AS d, open, close,
                   lag(close) OVER (PARTITION BY symbol ORDER BY ts_event) AS prev
            FROM bars_1d WHERE open > 0 AND close > 0 {pick.replace('WHERE', 'AND')}
        ), flagged AS (
            SELECT *, abs(open / prev - 1) > 0.3 AND list_bool_or(
                [abs(prev / open / k - 1) < 0.06 OR abs(prev / open * k - 1) < 0.06
                 FOR k IN [1.5, 2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 30, 40, 50, 100]]) AS split
            FROM raw
        )
        SELECT symbol, d, open, close,
               CASE WHEN NOT coalesce(split, false) THEN open / prev - 1 END AS gap,
               close / open - 1 AS day,
               CASE WHEN NOT coalesce(split, false) THEN close / prev - 1 END AS total,
               d IN (SELECT d FROM signal) AS sig
        FROM flagged
        """
    )
    return con


def per_ticker(con: duckdb.DuckDBPyConnection, col: str):
    return con.execute(
        f"""
        SELECT symbol,
               count(*) FILTER (sig) AS n,
               avg({col}) FILTER (sig) AS sig_avg,
               avg({col}) FILTER (NOT sig) AS rest_avg,
               avg({col}) FILTER (sig) - avg({col}) FILTER (NOT sig) AS diff,
               (avg({col}) FILTER (sig) - avg({col}) FILTER (NOT sig)) /
                 sqrt(var_pop({col}) FILTER (sig) / nullif(count(*) FILTER (sig) - 1, 0)
                    + var_pop({col}) FILTER (NOT sig) / nullif(count(*) FILTER (NOT sig) - 1, 0)) AS t
        FROM daily WHERE {col} IS NOT NULL
        GROUP BY symbol HAVING count(*) FILTER (sig) >= {MIN_SIGNALS}
        """
    ).fetchdf()


def summarize(label: str, df) -> None:
    print(
        f"{label:6} tickers {len(df)}   avg diff {df['diff'].mean():+.3%}   median {df['diff'].median():+.3%}   "
        f"t>2: {(df['t'] > 2).sum()}   t<-2: {(df['t'] < -2).sum()}"
    )


def intraday(con: duckdb.DuckDBPyConnection) -> None:
    """Average return since the first regular-session bar's open at each checkpoint (equal-weighted),
    signal days vs the rest. Minute bars are Nasdaq venues only and sparse for thin names, so each
    checkpoint uses the last bar at or before it."""
    cols = [f"c_{cp.replace(':', '')}" for cp in CHECKPOINTS]
    picks = ",\n".join(f"arg_max(close, ts) FILTER (WHERE tm <= TIME '{cp}') AS {c}" for cp, c in zip(CHECKPOINTS, cols))
    con.execute(
        f"""
        CREATE TABLE path AS
        SELECT symbol, d, arg_min(open, ts) AS o, {picks}
        FROM (SELECT symbol, ts_event AS ts, open, close,
                     (ts_event AT TIME ZONE 'America/New_York')::DATE AS d,
                     (ts_event AT TIME ZONE 'America/New_York')::TIME AS tm
              FROM bars_1m)
        WHERE tm >= TIME '09:30' AND tm < TIME '16:00'
        GROUP BY symbol, d
        """
    )
    avgs = ", ".join(f"avg(p.{c} / p.o - 1) FILTER (WHERE {{cond}})" for c in cols)
    print("\nAverage return since the 09:30 open (equal-weighted); last column is the full open->close day\n")
    print(f"{'group':26}{'n':>7}" + "".join(f"{cp:>8}" for cp in CHECKPOINTS) + f"{'close':>8}")
    for name, where in (("all tickers", "TRUE"), (SEMI_BUCKET, "p.symbol IN (SELECT symbol FROM semis)")):
        for tag, cond in (("signal", "d.sig"), ("other", "NOT d.sig")):
            row = con.execute(
                f"""
                SELECT count(*) FILTER (WHERE {cond}), {avgs.format(cond=cond)}, avg(d.day) FILTER (WHERE {cond})
                FROM path p JOIN daily d ON d.symbol = p.symbol AND d.d = p.d
                WHERE {where} AND d.day IS NOT NULL
                """
            ).fetchone()
            print(f"{name + ' ' + tag:26}{row[0]:7}" + "".join(f"{v:+8.2%}" for v in row[1:]))


def main() -> None:
    ap = argparse.ArgumentParser(description="Korean memory-session signal vs US gap, day and intraday path")
    ap.add_argument("--tickers", nargs="*", help="default: whole universe")
    ap.add_argument("--thresh", type=float, default=0.01)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--intraday", action="store_true")
    args = ap.parse_args()

    con = connect(signal_days("3y", args.thresh), args.tickers)
    first, last = con.execute("SELECT min(d), max(d) FROM daily").fetchone()
    n_sig = con.execute("SELECT count(DISTINCT d) FROM daily WHERE sig").fetchone()[0]
    print(f"US days {first}..{last}   signal days in range: {n_sig}   (both Korean names > +{args.thresh:.0%})\n")

    for label in ("gap", "day", "total"):
        summarize(label, per_ticker(con, label))
    day = per_ticker(con, "day").sort_values("t")
    gap = per_ticker(con, "gap").set_index("symbol")
    print(f"\n{'sym':7}{'n':>4}{'gap diff':>10}{'day sig':>9}{'day rest':>9}{'day diff':>9}{'t':>6}   (worst, then best, open->close)")
    for r in list(day.head(args.top).itertuples()) + list(day.tail(max(args.top // 3, 3)).itertuples()):
        print(f"{r.symbol:7}{r.n:4}{gap.loc[r.symbol, 'diff']:+10.2%}{r.sig_avg:+9.2%}{r.rest_avg:+9.2%}{r.diff:+9.2%}{r.t:6.1f}")
    if args.intraday:
        intraday(con)


if __name__ == "__main__":
    main()
