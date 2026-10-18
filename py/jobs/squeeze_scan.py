"""Short-squeeze screen over the universe: crowded shorts (fuel) plus a price / volume trigger.

Reads only local parquet: short/short_interest.parquet, short/short_volume.parquet, profiles/profiles.parquet and the
databento daily bars. Nothing here is a signal on its own; it ranks names to look at.

    fuel     short % of shares, days to cover, short interest trend, short-volume ratio
    trigger  up day on volume, close above the prior 10-day high, bounce off the 20-day low

A name is "TRIGGERED" when it has fuel and at least one trigger, "SETUP" when it has fuel and no trigger yet.
Names with a pending takeover (price pinned within 3% over 20 sessions plus merger-agreement language in a recent
earnings release or an 8-K Item 1.01) are hidden: their short volume is merger-arb flow, not squeeze fuel.

    uv run python -m jobs.squeeze_scan [--top 25] [--min-si-pct 8] [--min-dtc 4] [--include-deals] [--json out.json] [TICKER ...]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb

from sources import universe

BARS = universe.DATA_ROOT / "market" / "databento" / "bars_1d" / "*.parquet"
SHORT = universe.DATA_ROOT / "short"
PROFILES = universe.DATA_ROOT / "profiles" / "profiles.parquet"
RELEASES = universe.DATA_ROOT / "earnings" / "releases" / "*.parquet"
EVENTS = universe.DATA_ROOT / "events" / "events.parquet"

# A pending cash deal pins the price to the offer: the 20-session close range is a few percent at most. A pinned name
# only counts as a pending deal with filing evidence too (merger-agreement language in an earnings release or an 8-K
# Item 1.01 in the window), so a quiet low-vol stock is not dropped and an acquirer (price not pinned) is not either.
PIN_RANGE = 0.03
DEAL_DAYS = 180

QUERY = """
WITH px AS (
  SELECT symbol, (ts_event AT TIME ZONE 'UTC')::date d, close, high, low, volume,
         max(high) OVER (PARTITION BY symbol ORDER BY ts_event ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) hi10,
         min(low)  OVER (PARTITION BY symbol ORDER BY ts_event ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) lo20,
         avg(volume) OVER (PARTITION BY symbol ORDER BY ts_event ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) v20,
         lag(close, 1) OVER (PARTITION BY symbol ORDER BY ts_event) c1,
         lag(close, 5) OVER (PARTITION BY symbol ORDER BY ts_event) c5,
         max(close) OVER (PARTITION BY symbol ORDER BY ts_event ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) hc20,
         min(close) OVER (PARTITION BY symbol ORDER BY ts_event ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) lc20,
         row_number() OVER (PARTITION BY symbol ORDER BY ts_event DESC) rn
  FROM read_parquet('{bars}')
), last_px AS (SELECT * FROM px WHERE rn = 1),
si AS (
  SELECT ticker, settlement_date, short_interest, days_to_cover,
         lag(short_interest) OVER (PARTITION BY ticker ORDER BY settlement_date) prev_si,
         row_number() OVER (PARTITION BY ticker ORDER BY settlement_date DESC) rn
  FROM read_parquet('{si}')
), last_si AS (SELECT * FROM si WHERE rn = 1),
sv AS (
  SELECT ticker,
         sum(short_volume) FILTER (WHERE rn <= 5) / nullif(sum(total_volume) FILTER (WHERE rn <= 5), 0) r5,
         sum(short_volume) FILTER (WHERE rn > 5) / nullif(sum(total_volume) FILTER (WHERE rn > 5), 0) rprev
  FROM (SELECT *, row_number() OVER (PARTITION BY ticker ORDER BY date DESC) rn
        FROM read_parquet('{sv}') WHERE total_volume > 0)
  WHERE rn <= 25 GROUP BY ticker
), deal AS (
  SELECT ticker FROM read_parquet('{rel}', union_by_name = true)
  WHERE filed >= current_date - {days} AND regexp_matches(lower(text), 'agreement and plan of merger|merger agreement')
  UNION
  SELECT ticker FROM read_parquet('{ev}') WHERE item = '1.01' AND filed >= current_date - {days}
)
SELECT s.ticker, p.d AS px_date, p.close, s.settlement_date, s.short_interest, s.days_to_cover,
       s.short_interest / s.prev_si - 1 AS si_chg,
       s.short_interest / (pr.market_cap / p.close) * 100 AS si_pct,
       v.r5 AS sv_r5, v.r5 - v.rprev AS sv_chg,
       p.close / p.c1 - 1 AS d1, p.close / p.c5 - 1 AS d5, p.volume / p.v20 AS rvol,
       p.close > p.hi10 AS breakout, p.low <= p.lo20 * 1.03 AND p.close > p.c1 AS bounce,
       p.hc20 / p.lc20 - 1 AS range20, s.ticker IN (SELECT ticker FROM deal) AS deal_evidence
FROM last_si s
JOIN last_px p ON p.symbol = s.ticker
LEFT JOIN read_parquet('{pr}') pr ON pr.ticker = s.ticker AND pr.currency = 'USD'
LEFT JOIN sv v ON v.ticker = s.ticker
"""


def scan(min_si_pct: float = 8.0, min_dtc: float = 4.0, tickers: list[str] | None = None,
         bars=BARS, si_path=SHORT / "short_interest.parquet", sv_path=SHORT / "short_volume.parquet",
         profiles=PROFILES, releases=RELEASES, events=EVENTS, include_deals: bool = False) -> list[dict]:
    """Ranked fuel + trigger rows. Pending-deal names (pinned price plus deal filings) are dropped unless
    include_deals; with it they are kept and carry pending_deal=True."""
    q = QUERY.format(bars=bars, si=si_path, sv=sv_path, pr=profiles, rel=releases, ev=events, days=DEAL_DAYS)
    cur = duckdb.connect().execute(q)
    cols = [c[0] for c in cur.description]
    out = []
    for row in cur.fetchall():
        r = dict(zip(cols, row))
        if tickers and r["ticker"] not in tickers:
            continue
        if r["si_pct"] is None or r["si_pct"] < min_si_pct or (r["days_to_cover"] or 0) < min_dtc:
            continue
        r["pending_deal"] = bool(r["deal_evidence"] and r["range20"] is not None and r["range20"] <= PIN_RANGE)
        if r["pending_deal"] and not include_deals:
            continue
        triggers = []
        if r["d1"] is not None and r["d1"] > 0.03 and (r["rvol"] or 0) >= 1.5:
            triggers.append("up day on volume")
        if r["breakout"]:
            triggers.append("close > 10d high")
        if r["bounce"]:
            triggers.append("bounce off 20d low")
        r["triggers"] = triggers
        r["status"] = "TRIGGERED" if triggers else "SETUP"
        r["score"] = score(r)
        out.append(r)
    return sorted(out, key=lambda r: r["score"], reverse=True)


def score(r: dict) -> float:
    """Rough rank: fuel (short %, days to cover, shorts adding, heavy new shorting) plus 2 points per trigger."""
    s = min(r["si_pct"] / 10, 3) + min((r["days_to_cover"] or 0) / 5, 3)
    s += 1 if (r["si_chg"] or 0) > 0.05 else 0
    s += 1 if (r["sv_r5"] or 0) > 0.6 else 0
    return round(s + 2 * len(r["triggers"]), 2)


def _f(v, fmt: str) -> str:
    return "—" if v is None else format(v, fmt)


def render(rows: list[dict], top: int) -> str:
    head = f"{'ticker':<7}{'status':<10}{'score':>6}{'SI%':>6}{'DTC':>6}{'ΔSI':>8}{'SV5':>6}{'1d':>8}{'5d':>8}{'rvol':>6}  triggers"
    lines = [head, "-" * len(head)]
    for r in rows[:top]:
        lines.append(f"{r['ticker']:<7}{r['status']:<10}{r['score']:>6.1f}{_f(r['si_pct'], '.1f'):>6}"
                     f"{_f(r['days_to_cover'], '.1f'):>6}{_f(r['si_chg'] and r['si_chg'] * 100, '+.0f'):>7}%"
                     f"{_f(r['sv_r5'] and r['sv_r5'] * 100, '.0f'):>5}%{_f(r['d1'] and r['d1'] * 100, '+.1f'):>7}%"
                     f"{_f(r['d5'] and r['d5'] * 100, '+.1f'):>7}%{_f(r['rvol'], '.1f'):>6}  {', '.join(r['triggers']) or '—'}")
    asof = max((str(r["px_date"]) for r in rows), default="n/a")
    lines.append(f"\nprices through {asof}; {len(rows)} names pass the filter (SI% is short interest / (market cap / close), a shares-outstanding proxy).")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("tickers", nargs="*")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--min-si-pct", type=float, default=8.0)
    ap.add_argument("--min-dtc", type=float, default=4.0)
    ap.add_argument("--include-deals", action="store_true", help="keep pending-deal names (hidden by default)")
    ap.add_argument("--json", help="also write the full ranked list to this path")
    a = ap.parse_args()
    allrows = scan(a.min_si_pct, a.min_dtc, [t.upper() for t in a.tickers] or None, include_deals=True)
    hidden = [r for r in allrows if r["pending_deal"]]
    rows = allrows if a.include_deals else [r for r in allrows if not r["pending_deal"]]
    print(render(rows, a.top))
    if hidden and not a.include_deals:
        print("hidden as pending deals (pinned price + merger filing): " + ", ".join(r["ticker"] for r in hidden))
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        with open(a.json, "w") as f:
            json.dump(rows, f, default=str, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
