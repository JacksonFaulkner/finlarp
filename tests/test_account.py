"""Account tables: split-adjusted fills, FIFO round trips, positions reconciliation, time-weighted equity."""

from datetime import datetime, timezone

import pytest

from core.schemas.views import VIEW_MODELS
from derive import account


def _ms(y, m, d, h=15, mi=0):
    return int(datetime(y, m, d, h, mi, tzinfo=timezone.utc).timestamp() * 1000)


def _tx(tid, when, ty, sym, qty, price, desc=""):
    return {"account": "123", "transaction_id": tid, "date": when, "type": ty, "symbol": sym, "quantity": qty,
            "price": price, "amount": -qty * price if ty == "Bought" else abs(qty) * price, "description": desc}


@pytest.fixture()
def txs():
    return [
        _tx("1", _ms(2025, 1, 6), "Bought", "AAA", 10, 100.0),
        _tx("2", _ms(2025, 1, 7), "Bought", "AAA", 10, 110.0),
        _tx("3", _ms(2025, 1, 8), "Sold", "AAA", -15, 120.0),
        _tx("4", _ms(2025, 1, 6), "Bought", "SPL", 40, 88.0),
        _tx("5", _ms(2025, 2, 3, 8), "Stock Split", "SPL", 40, 0.0, "X SPLIT RATIO 2:1"),
        _tx("5", _ms(2025, 2, 3, 8), "Stock Split", "SPL", 40, 0.0, "X SPLIT RATIO 2:1"),  # listed twice by the broker
        _tx("6", _ms(2025, 3, 3), "Sold", "SPL", -80, 66.0),
        _tx("7", _ms(2025, 3, 4), "Sold", "OLD", -8, 27.0),
        {"account": "123", "transaction_id": "8", "date": _ms(2025, 1, 6, 8), "type": "Online Transfer",
         "symbol": None, "quantity": 0, "price": 0, "amount": 1000.0, "description": "ACH DEPOSIT"},
        {"account": "123", "transaction_id": "9", "date": _ms(2025, 1, 8, 8), "type": "Qualified Dividend",
         "symbol": "AAA", "quantity": 0, "price": 0, "amount": 5.0, "description": "AAA REC"},
    ]


def test_fills_split_adjusted(txs):
    f = account.build_fills(txs).set_index("fill_id")
    assert f.loc["4", "split_factor"] == 2.0  # one split counted once despite two rows
    assert f.loc["4", "qty_adj"] == 80 and f.loc["4", "price_adj"] == 44.0
    assert f.loc["6", "split_factor"] == 1.0
    assert set(f["side"]) == {"buy", "sell"} and (f["qty"] > 0).all()
    assert len(f) == 6  # transfers, dividends and splits are not fills


def test_round_trips_fifo_and_split(txs):
    trips, open_lots = account.build_round_trips(account.build_fills(txs))
    aaa = trips[trips.symbol == "AAA"].sort_values("lot_id")
    assert list(aaa["qty"]) == [10, 5]  # the sell consumes the first lot fully, then half of the second
    assert list(aaa["entry_price"]) == [100.0, 110.0]
    assert aaa["pnl"].sum() == pytest.approx(10 * 20 + 5 * 10)
    assert open_lots["AAA"][0]["qty"] == 5
    spl = trips[trips.symbol == "SPL"].iloc[0]
    assert spl.qty == 80 and spl.entry_price == 44.0 and spl.pnl == pytest.approx(80 * 22.0)  # not a phantom loss
    old = trips[trips.symbol == "OLD"].iloc[0]
    assert not old.matched and old.pnl != old.pnl  # sell with no buy in the cache: pnl is NaN


def test_positions_reconcile(txs):
    fills = account.build_fills(txs)
    _, open_lots = account.build_round_trips(fills)
    broker = [{"symbol": "AAA", "quantity": 5, "price_paid": 109.0, "last_price": 121.0, "market_value": 605.0,
               "total_gain": 60.0}, {"symbol": "ZZZ", "quantity": 1, "price_paid": 1.0}]
    p = account.build_positions(open_lots, broker, None).set_index("symbol")
    assert p.loc["AAA", "qty"] == 5 and p.loc["AAA", "avg_cost"] == 110.0 and bool(p.loc["AAA", "qty_matches_broker"])
    assert not bool(p.loc["ZZZ", "qty_matches_broker"])  # broker holds it, fills do not
    # FIFO lots that the broker no longer lists are a mismatch, not unknown
    p2 = account.build_positions({"GONE": [{"qty": 3.0, "price": 2.0, "date": None}]}, broker, None).set_index("symbol")
    assert p2.loc["GONE", "broker_qty"] == 0 and not bool(p2.loc["GONE", "qty_matches_broker"])


def test_cash_kinds(txs):
    c = account.build_cash(txs)
    assert sorted(c["kind"]) == ["deposit", "dividend"]
    assert c.loc[c.kind == "deposit", "amount"].iloc[0] == 1000.0
    assert not c["kind"].isin(["other"]).any()


def test_equity_twr_excludes_deposits(txs):
    cash = account.build_cash(txs)
    hist = [{"date": "2025-01-06", "total_value": 1000.0, "day_change_pct": 0},
            {"date": "2025-01-07", "total_value": 1100.0, "day_change_pct": 0},
            {"date": "2025-01-08", "total_value": 1100.0, "day_change_pct": 0},
            {"date": "2025-01-09", "total_value": 990.0, "day_change_pct": 0}]
    e = account.build_equity_daily(hist, cash).set_index("date")
    d = lambda s: datetime.fromisoformat(s).date()  # noqa: E731
    assert e.loc[d("2025-01-06"), "net_flow"] == 1000.0 and e.loc[d("2025-01-06"), "day_return"] != e.loc[d("2025-01-06"), "day_return"]
    assert e.loc[d("2025-01-07"), "day_return"] == pytest.approx(0.10)
    assert bool(e.loc[d("2025-01-08"), "is_stale"])
    assert e.loc[d("2025-01-09"), "drawdown"] == pytest.approx(-0.10)
    # a later deposit must not show up as return
    cash2 = account.build_cash(txs + [{"account": "123", "transaction_id": "10", "date": _ms(2025, 1, 9, 8),
                                       "type": "Online Transfer", "symbol": None, "quantity": 0, "price": 0,
                                       "amount": 500.0, "description": "ACH"}])
    hist2 = hist[:3] + [{"date": "2025-01-09", "total_value": 1650.0, "day_change_pct": 0}]
    assert account.build_equity_daily(hist2, cash2).set_index("date").loc[d("2025-01-09"), "day_return"] == pytest.approx(0.03125)


def test_models_match_tables(txs):
    fills = account.build_fills(txs)
    trips, open_lots = account.build_round_trips(fills)
    cash = account.build_cash(txs)
    frames = {"account_fills": fills, "account_round_trips": trips, "account_cash": cash,
              "account_positions": account.build_positions(open_lots, [], None),
              "account_equity_daily": account.build_equity_daily(
                  [{"date": "2025-01-06", "total_value": 1.0, "day_change_pct": 0}], cash)}
    for view, df in frames.items():
        assert set(df.columns) == set(VIEW_MODELS[view].model_fields), view
