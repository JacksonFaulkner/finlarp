"""One-off backfill of portfolio_history from transaction history + Yahoo
daily closes, so the ratatui chart has more than "today" to plot on first
use.

Reconstructs, for each trading day since your earliest transaction, both
your stock holdings (from Bought/Sold quantities, split-adjusted) and your
cash balance (every transaction's `amount` is E*TRADE's own signed cash
effect — buys negative, sells/dividends/interest/transfers positive —
so summing it chronologically IS the cash balance). Total account value
is cash + stock value, matching what sources/etrade.py's live cmd_positions
pulls from balance.json for "today". Online Transfer amounts (deposits/
withdrawals) are excluded from the day-over-day % change — adding money
isn't a gain.

Usage:
    uv run jobs/backfill_history.py
"""

from __future__ import annotations

import re
import sys
import time
from collections import defaultdict


from core import db
from sources import yahoo

SHARE_AFFECTING_TYPES = {"Bought", "Sold"}
SPLIT_RATIO_RE = re.compile(r"SPLIT RATIO\s+(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)", re.I)


def _epoch_ms_to_date(ms: int) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ms / 1000))


def main() -> None:
    transactions = db.get_all_cached_transactions()
    if not transactions:
        print("no cached transactions — run `uv run sources/etrade.py transactions` first", file=sys.stderr)
        sys.exit(1)
    transactions = [t for t in transactions if t.get("date")]
    transactions.sort(key=lambda t: t["date"])

    share_txns = [t for t in transactions if t.get("type") in SHARE_AFFECTING_TYPES and t.get("symbol")]
    if not share_txns:
        print("no Bought/Sold transactions found — nothing to backfill", file=sys.stderr)
        return

    # Yahoo closes are split-adjusted, so every trade quantity is converted to
    # current-split terms (qty * ratios of splits after the trade) or a
    # position is undervalued until the split date, then "recovers" as a fake
    # gain. Stock Split rows themselves are not counted as share changes:
    # E*TRADE emits them duplicated. Ratio comes from the description
    # ("SPLIT RATIO 2:1"); one split per (symbol, date).
    splits: dict[str, dict[str, float]] = defaultdict(dict)
    for t in transactions:
        if t.get("type") != "Stock Split" or not t.get("symbol"):
            continue
        m = SPLIT_RATIO_RE.search(t.get("description") or "")
        if m and float(m.group(2)):
            splits[t["symbol"]][_epoch_ms_to_date(t["date"])] = float(m.group(1)) / float(m.group(2))

    # Running share count checkpoints per symbol, in chronological order —
    # holdings on any given day = the last checkpoint at or before that day.
    checkpoints: dict[str, list[tuple[str, float]]] = defaultdict(list)
    running_shares: dict[str, float] = defaultdict(float)
    for t in share_txns:
        symbol = t["symbol"]
        trade_date = _epoch_ms_to_date(t["date"])
        qty = t.get("quantity") or 0
        for split_date, ratio in splits.get(symbol, {}).items():
            if split_date > trade_date:
                qty *= ratio
        running_shares[symbol] += qty
        checkpoints[symbol].append((_epoch_ms_to_date(t["date"]), running_shares[symbol]))

    # Cash balance checkpoints from every transaction's signed amount —
    # same idea, held-until-superseded lookup by date.
    cash_checkpoints: list[tuple[str, float]] = []
    running_cash = 0.0
    for t in transactions:
        running_cash += t.get("amount") or 0
        cash_checkpoints.append((_epoch_ms_to_date(t["date"]), running_cash))

    # Net external cash flow (deposits/withdrawals only) per day — excluded
    # from the return calc so funding the account isn't counted as a gain.
    transfers_by_date: dict[str, float] = defaultdict(float)
    for t in transactions:
        if t.get("type") == "Online Transfer":
            transfers_by_date[_epoch_ms_to_date(t["date"])] += t.get("amount") or 0

    symbols = sorted(checkpoints.keys())
    earliest_date = _epoch_ms_to_date(transactions[0]["date"])
    print(f"backfilling {len(symbols)} symbols from {earliest_date}: {', '.join(symbols)}", file=sys.stderr)

    # 2y covers any realistic transaction history; Yahoo ignores the extra
    # range on symbols with a shorter trading history.
    closes_by_symbol: dict[str, dict[str, float]] = {}
    for symbol in symbols:
        try:
            result = yahoo.cmd_history(symbol, "2y", "1d")
        except Exception as e:
            print(f"  skipping {symbol}: {e}", file=sys.stderr)
            continue
        closes_by_symbol[symbol] = {
            _epoch_ms_to_date(p["t"] * 1000): p["close"] for p in result["points"]
        }

    # Trading calendar = union of every date any symbol actually has a
    # close for — avoids inventing weekend/holiday rows.
    all_dates = sorted({d for closes in closes_by_symbol.values() for d in closes})
    today = time.strftime("%Y-%m-%d")
    all_dates = [d for d in all_dates if d >= earliest_date and d < today]

    def last_at_or_before(checkpoints_list, date):
        val = None
        for d, v in checkpoints_list:
            if d <= date:
                val = v
            else:
                break
        return val

    prev_value = None
    written = 0
    for date in all_dates:
        stock_value = 0.0
        for symbol, closes in closes_by_symbol.items():
            shares = last_at_or_before(checkpoints[symbol], date) or 0
            if shares <= 0:
                continue
            close = closes.get(date)
            if close is None:
                continue
            stock_value += shares * close

        cash = last_at_or_before(cash_checkpoints, date) or 0.0
        total_value = stock_value + cash

        # Before the account has any meaningful money in it, a tiny swing
        # in an odd cent of stray cash reads as a mathematically valid but
        # meaningless six-figure % change (dividing by ~$0). Skip the
        # bootstrap noise rather than let it wreck the chart's y-axis.
        if total_value < 100:
            continue

        if prev_value:
            transfers_today = transfers_by_date.get(date, 0.0)
            day_change_pct = (total_value - prev_value - transfers_today) / prev_value * 100
        else:
            day_change_pct = 0.0

        db.upsert_portfolio_snapshot(total_value, day_change_pct, date=date)
        prev_value = total_value
        written += 1

    print(f"backfilled {written} days into portfolio_history", file=sys.stderr)


if __name__ == "__main__":
    main()
