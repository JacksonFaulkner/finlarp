"""The Databento spend guard: daily cap, sticky kill switch, rate limit, refunds."""

import pytest
from databento.common.error import BentoServerError

from sources import databento_guard as g


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "spend.json"
    monkeypatch.setattr(g, "LEDGER", path)
    monkeypatch.delenv("FL_DATABENTO_DAILY_CAP", raising=False)
    return path


class FakeClient:
    """Prices every request at `price`; `fail` makes the data request error out."""

    def __init__(self, price, fail=False):
        self.price, self.fail, self.served = price, fail, 0
        self.metadata = self
        self.timeseries = self

    def get_cost(self, **kw):
        return self.price

    def get_range(self, **kw):
        if self.fail:
            raise BentoServerError(http_status=504, http_body=b"", message="gateway timeout")
        self.served += 1
        return "store"


def test_books_spend_under_the_cap(ledger):
    c = FakeClient(1.25)
    assert g.get_range(c, dataset="XNAS.BASIC", schema="ohlcv-1m", symbols=["MU"]) == "store"
    s = g.status()
    assert (s["spent"], s["calls"], s["killed"]) == (1.25, 1, None)
    assert g.remaining() == pytest.approx(3.75)


def test_passing_the_cap_trips_a_sticky_kill_switch(ledger):
    c = FakeClient(2.0)
    g.get_range(c, dataset="d")
    g.get_range(c, dataset="d")
    with pytest.raises(g.DatabentoKilled, match="tripped"):
        g.get_range(c, dataset="d")  # 6.00 > 5.00
    assert c.served == 2, "the refused call never reached Databento"
    # Even a call that fits is refused now, until someone resets it.
    with pytest.raises(g.DatabentoKilled, match="is on"):
        g.get_range(FakeClient(0.01), dataset="d")
    assert g.remaining() == 0.0
    g.reset()
    assert g.status()["killed"] is None
    assert g.get_range(FakeClient(0.5), dataset="d") == "store"


def test_cap_comes_from_the_environment(ledger, monkeypatch):
    monkeypatch.setenv("FL_DATABENTO_DAILY_CAP", "0.10")
    with pytest.raises(g.DatabentoKilled):
        g.get_range(FakeClient(0.25), dataset="d")


def test_a_known_cost_skips_pricing(ledger):
    c = FakeClient(99.0)  # would trip if it were asked
    g.get_range(c, cost=0.02, dataset="d")
    assert g.status()["spent"] == 0.02


def test_an_error_answer_is_refunded(ledger):
    with pytest.raises(BentoServerError):
        g.get_range(FakeClient(1.0, fail=True), dataset="d")
    s = g.status()
    assert (s["spent"], s["calls"]) == (0.0, 0)


def test_rate_limit_waits_for_a_slot(ledger, monkeypatch):
    slept = []
    monkeypatch.setattr(g.time, "sleep", lambda s: slept.append(s))
    for i in range(g.RATE_PER_MIN):
        g.charge(0.0, "x", now=1000.0 + i * 0.1)
    # The next call is inside the same minute: it has to wait, then (time moved on) it goes.
    calls = iter([1010.0, 1061.0])
    monkeypatch.setattr(g.time, "time", lambda: next(calls))
    g.charge(0.0, "x")
    assert slept and slept[0] == pytest.approx(50.0)


def test_an_unreadable_ledger_stops_spending(ledger):
    ledger.write_text("{not json")
    with pytest.raises(g.DatabentoKilled, match="unreadable"):
        g.charge(0.01, "x")
