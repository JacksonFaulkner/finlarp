"""Broker account tables for the MCP `sql` tool, built from the E*TRADE caches in finlarp.duckdb.

    account_fills         one row per buy/sell fill, with split-adjusted qty/price
    account_round_trips   FIFO-paired lots: entry, exit, pnl, hold time (unmatched sells flagged)
    account_positions     open FIFO lots per symbol, reconciled against the broker's own positions
    account_equity_daily  portfolio value, deposit/withdrawal flow, time-weighted daily return, drawdown
    account_cash          deposits, withdrawals, dividends, interest

Written as parquet under <data root>/account/ so the MCP connection (which cannot open the broker DB or
the OAuth token) reads them like any other dataset. The broker account number is replaced by a short hash.

    python py/derive/account.py          # rebuild now
"""
from __future__ import annotations

import hashlib
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
import pandas as pd

from core import db
from sources import universe

ET = ZoneInfo("America/New_York")
OUT = universe.DATA_ROOT / "account"
TABLES = ("fills", "round_trips", "positions", "equity_daily", "cash")

_SPLIT = re.compile(r"SPLIT RATIO\s+(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", re.I)
_TRADE = {"Bought": "buy", "Sold": "sell"}
_CASH_KIND = {"Dividend": "dividend", "Qualified Dividend": "dividend", "Interest Income": "interest"}
_EPS = 1e-9


def _acct(account) -> str:
    return hashlib.sha1(str(account).encode()).hexdigest()[:8]


def _utc(ms: float) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def _et(ts: datetime) -> datetime:
    return ts.astimezone(ET).replace(tzinfo=None)


def _splits(txs: list[dict]) -> dict[str, list[tuple[datetime, float]]]:
    """symbol -> [(ts, new shares per old share)]. E*TRADE lists each split twice under one transaction id."""
    seen, out = set(), defaultdict(list)
    for t in txs:
        if t.get("type") != "Stock Split" or not t.get("symbol"):
            continue
        m = _SPLIT.search(t.get("description") or "")
        key = (t.get("transaction_id"), t["symbol"])
        if not m or key in seen:
            continue
        seen.add(key)
        old, new = float(m.group(1)), float(m.group(2))
        out[t["symbol"]].append((_utc(t["date"]), old / new))
    return out


def build_fills(txs: list[dict]) -> pd.DataFrame:
    splits = _splits(txs)
    rows, seen = [], defaultdict(int)
    for t in txs:
        if t.get("type") not in _TRADE or not t.get("symbol"):
            continue
        ts = _utc(t["date"])
        factor = 1.0
        for sts, f in splits.get(t["symbol"], []):
            if sts > ts:
                factor *= f
        tid = str(t.get("transaction_id"))
        seen[tid] += 1
        qty, price = abs(float(t["quantity"])), float(t["price"])
        rows.append({
            "fill_id": tid if seen[tid] == 1 else f"{tid}#{seen[tid]}",
            "acct": _acct(t.get("account")), "ts": ts, "et_ts": _et(ts), "et_date": _et(ts).date(),
            "et_minute": _et(ts).hour * 60 + _et(ts).minute, "symbol": t["symbol"], "side": _TRADE[t["type"]],
            "qty": qty, "price": price, "amount": float(t["amount"]), "split_factor": factor,
            "qty_adj": qty * factor, "price_adj": price / factor, "description": t.get("description"),
        })
    cols = ["fill_id", "acct", "ts", "et_ts", "et_date", "et_minute", "symbol", "side", "qty", "price",
            "amount", "split_factor", "qty_adj", "price_adj", "description"]
    return pd.DataFrame(rows, columns=cols).sort_values(["ts", "side"], ascending=[True, True], kind="stable",
                                                        ignore_index=True)


def build_round_trips(fills: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[dict]]]:
    """FIFO lots on the split-adjusted basis. Returns (round trips, open lots by symbol)."""
    lots: dict[str, deque] = defaultdict(deque)
    rows, n = [], defaultdict(int)
    for f in fills.sort_values(["ts", "side"], kind="stable").itertuples():
        if f.side == "buy":
            lots[f.symbol].append({"qty": f.qty_adj, "price": f.price_adj, "fill": f})
            continue
        rem = f.qty_adj
        while rem > _EPS and lots[f.symbol]:
            lot = lots[f.symbol][0]
            take = min(rem, lot["qty"])
            n[f.symbol] += 1
            rows.append(_trip(f"{f.symbol}-{n[f.symbol]}", take, lot["fill"], lot["price"], f, f.price_adj))
            lot["qty"] -= take
            rem -= take
            if lot["qty"] <= _EPS:
                lots[f.symbol].popleft()
        if rem > _EPS:  # sold shares the cache never saw bought (older than its window, or transferred in)
            n[f.symbol] += 1
            rows.append(_trip(f"{f.symbol}-{n[f.symbol]}", rem, None, None, f, f.price_adj))
    cols = ["lot_id", "acct", "symbol", "qty", "matched", "entry_fill_id", "exit_fill_id", "entry_ts", "exit_ts",
            "entry_date", "exit_date", "entry_et_minute", "exit_et_minute", "entry_price", "exit_price", "cost",
            "proceeds", "pnl", "ret", "hold_days", "same_day"]
    open_lots = {s: [{"qty": lt["qty"], "price": lt["price"], "date": lt["fill"].et_date} for lt in q] for s, q in
                 lots.items() if q}
    return pd.DataFrame(rows, columns=cols), open_lots


def _trip(lot_id, qty, entry, entry_price, exit_, exit_price) -> dict:
    row = {"lot_id": lot_id, "acct": exit_.acct, "symbol": exit_.symbol, "qty": qty, "matched": entry is not None,
           "entry_fill_id": None, "exit_fill_id": exit_.fill_id, "entry_ts": None, "exit_ts": exit_.ts,
           "entry_date": None, "exit_date": exit_.et_date, "entry_et_minute": None, "exit_et_minute": exit_.et_minute,
           "entry_price": None, "exit_price": exit_price, "cost": None, "proceeds": qty * exit_price, "pnl": None,
           "ret": None, "hold_days": None, "same_day": None}
    if entry is not None:
        row.update(entry_fill_id=entry.fill_id, entry_ts=entry.ts, entry_date=entry.et_date,
                   entry_et_minute=entry.et_minute, entry_price=entry_price, cost=qty * entry_price,
                   pnl=qty * (exit_price - entry_price), ret=exit_price / entry_price - 1,
                   hold_days=(exit_.ts - entry.ts).total_seconds() / 86400, same_day=entry.et_date == exit_.et_date)
    return row


def build_positions(open_lots: dict[str, list[dict]], broker: list[dict], as_of: datetime | None) -> pd.DataFrame:
    by_sym = {b["symbol"]: b for b in broker or [] if b.get("symbol")}
    rows = []
    for sym in sorted(set(open_lots) | set(by_sym)):
        lots, b = open_lots.get(sym, []), by_sym.get(sym, {})
        qty = sum(lt["qty"] for lt in lots)
        cost = sum(lt["qty"] * lt["price"] for lt in lots)
        bq = b.get("quantity", 0.0 if by_sym else None)  # a symbol the broker no longer lists holds 0
        rows.append({
            "symbol": sym, "qty": qty, "avg_cost": cost / qty if qty > _EPS else None, "cost_basis": cost,
            "n_lots": len(lots), "first_entry_date": min((lt["date"] for lt in lots), default=None),
            "last_entry_date": max((lt["date"] for lt in lots), default=None), "broker_qty": bq,
            "broker_price_paid": b.get("price_paid"), "last_price": b.get("last_price"),
            "market_value": b.get("market_value"), "unrealized_pnl": b.get("total_gain"),
            "qty_matches_broker": None if bq is None else abs(qty - bq) < 1e-6, "as_of": as_of,
        })
    cols = ["symbol", "qty", "avg_cost", "cost_basis", "n_lots", "first_entry_date", "last_entry_date", "broker_qty",
            "broker_price_paid", "last_price", "market_value", "unrealized_pnl", "qty_matches_broker", "as_of"]
    return pd.DataFrame(rows, columns=cols)


def build_cash(txs: list[dict]) -> pd.DataFrame:
    rows = []
    for t in txs:
        ty = t.get("type")
        if ty in _TRADE or ty == "Stock Split":
            continue
        amount = float(t.get("amount") or 0)
        kind = _CASH_KIND.get(ty or "") or (("deposit" if amount >= 0 else "withdrawal") if ty == "Online Transfer" else "other")
        ts = _utc(t["date"])
        rows.append({"acct": _acct(t.get("account")), "ts": ts, "et_date": _et(ts).date(), "kind": kind,
                     "symbol": t.get("symbol"), "amount": amount, "description": t.get("description")})
    cols = ["acct", "ts", "et_date", "kind", "symbol", "amount", "description"]
    return pd.DataFrame(rows, columns=cols).sort_values("ts", ignore_index=True)


def build_equity_daily(history: list[dict], cash: pd.DataFrame) -> pd.DataFrame:
    """Daily return is time-weighted with each day's net deposit counted at the start of the day:
    r = value / (prev_value + flow) - 1. Weekends and holidays are carried forward (is_stale)."""
    cols = ["date", "total_value", "net_flow", "day_return", "twr_index", "drawdown", "is_stale"]
    if not history:
        return pd.DataFrame(columns=cols)
    h = pd.DataFrame(history)[["date", "total_value"]]
    h["date"] = pd.to_datetime(h["date"]).dt.date
    flows = cash[cash["kind"].isin(["deposit", "withdrawal"])].groupby("et_date")["amount"].sum()
    h["net_flow"] = h["date"].map(flows).fillna(0.0)
    prev = h["total_value"].shift(1)
    base = prev + h["net_flow"]
    h["day_return"] = (h["total_value"] / base - 1).where(base > 0)
    h["twr_index"] = (1 + h["day_return"].fillna(0)).cumprod()
    h["drawdown"] = h["twr_index"] / h["twr_index"].cummax() - 1
    h["is_stale"] = (h["total_value"] == prev) & (h["net_flow"] == 0)
    return h[cols]


def _write(df: pd.DataFrame, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    final = OUT / f"{name}.parquet"
    tmp = final.with_suffix(".tmp.parquet")
    con = duckdb.connect()
    try:
        con.register("df", df)
        con.execute(f"COPY df TO '{tmp}' (FORMAT PARQUET)")
    finally:
        con.close()
    tmp.replace(final)


def build() -> dict[str, int]:
    """Rebuild every table from the broker caches. Returns row counts."""
    txs = db.get_all_cached_transactions()
    fills = build_fills(txs)
    trips, open_lots = build_round_trips(fills)
    cash = build_cash(txs)
    age = db.cache_ages().get("positions_age")
    as_of = None if age is None else datetime.now(timezone.utc).replace(microsecond=0) - pd.Timedelta(seconds=age)
    out = {
        "fills": fills,
        "round_trips": trips,
        "positions": build_positions(open_lots, db.get_cached_positions() or [], as_of),
        "equity_daily": build_equity_daily(db.get_portfolio_history(), cash),
        "cash": cash,
    }
    for name, df in out.items():
        _write(df, name)
    return {name: len(df) for name, df in out.items()}


def build_if_stale() -> bool:
    """Rebuild when a table is missing or finlarp.duckdb is newer. Never raises: the broker DB may be locked
    by the TUI, in which case the existing parquet is kept."""
    try:
        files = [OUT / f"{t}.parquet" for t in TABLES]
        if all(f.exists() for f in files) and min(f.stat().st_mtime for f in files) >= Path(db.DB_PATH).stat().st_mtime:
            return False
        build()
        return True
    except Exception as e:  # noqa: BLE001
        print(f"account tables not rebuilt: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    for name, n in build().items():
        print(f"{name}: {n} rows -> {OUT / (name + '.parquet')}")
