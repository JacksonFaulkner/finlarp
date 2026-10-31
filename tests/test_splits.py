import datetime as dt

import duckdb
import pytest

from core.db import adjusted_bars_sql
from sources import splits


def _adjusted(bars, split_rows):
    con = duckdb.connect()
    con.execute("CREATE TABLE bars (symbol VARCHAR, ts_event TIMESTAMPTZ, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE)")
    con.execute("CREATE TABLE splits (symbol VARCHAR, split_date DATE, ratio DOUBLE)")
    con.executemany("INSERT INTO bars VALUES (?,?,?,?,?,?,?)", bars)
    con.executemany("INSERT INTO splits VALUES (?,?,?)", split_rows)
    return con.execute(adjusted_bars_sql("bars", "splits") + " ORDER BY symbol, ts_event").fetchall()


def _bar(day, close, volume=1000.0):
    ts = dt.datetime(*day.timetuple()[:3], 0, 0, tzinfo=dt.UTC)
    return ("AVGO", ts, close, close, close, close, volume)


def test_a_forward_split_divides_earlier_prices_and_multiplies_volume():
    rows = _adjusted(
        [_bar(dt.date(2024, 7, 12), 1700.0), _bar(dt.date(2024, 7, 15), 171.0)],
        [("AVGO", dt.date(2024, 7, 15), 10.0)],
    )
    before, after = rows
    assert before[5] == pytest.approx(170.0)  # close: 1700 / 10
    assert before[6] == pytest.approx(10000.0)  # volume: 1000 * 10
    assert after[5] == pytest.approx(171.0)  # on the split day the bar is already post-split


def test_a_reverse_split_multiplies_earlier_prices():
    rows = _adjusted(
        [_bar(dt.date(2025, 3, 21), 1.56), _bar(dt.date(2025, 3, 24), 16.65)],
        [("AVGO", dt.date(2025, 3, 24), 0.1)],
    )
    assert rows[0][5] == pytest.approx(15.6)


def test_symbols_without_splits_pass_through():
    rows = _adjusted([_bar(dt.date(2025, 1, 2), 250.0)], [("OTHER", dt.date(2025, 3, 24), 10.0)])
    assert rows[0][5] == 250.0


def test_chained_splits_multiply():
    rows = _adjusted(
        [_bar(dt.date(2024, 1, 2), 100.0)],
        [("AVGO", dt.date(2024, 6, 1), 2.0), ("AVGO", dt.date(2025, 6, 1), 2.0)],
    )
    assert rows[0][5] == pytest.approx(25.0)


def test_fetch_turns_yahoo_split_events_into_rows(monkeypatch):
    payload = {"chart": {"result": [{"events": {"splits": {
        "1721050200": {"date": 1721050200, "numerator": 10.0, "denominator": 1.0},
        "1742823000": {"date": 1742823000, "numerator": 1.0, "denominator": 10.0},
    }}}]}}

    class Resp:
        ok = True

        def json(self):
            return payload

    class Session:
        def get(self, *a, **k):
            return Resp()

    rows = splits.fetch("AVGO", Session())
    assert [r["split_date"] for r in rows] == ["2024-07-15", "2025-03-24"]
    assert [r["ratio"] for r in rows] == [10.0, 0.1]
