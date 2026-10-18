"""Read-only live E*TRADE tools with a fake session (no network, no real token)."""
import json

import pytest

from sources import etrade_live as el


class Resp:
    def __init__(self, status=200, body=None):
        self.status_code, self._b = status, body
        self.content = b"x" if body is not None else b""

    def json(self):
        return self._b


class Sess:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, params=None, headers=None):
        self.calls.append((url, params))
        for frag, r in self.routes.items():
            if frag in url:
                return r.pop(0) if isinstance(r, list) else r
        return Resp(404, {})


ACCTS = Resp(200, {"AccountListResponse": {"Accounts": {"Account": [
    {"accountIdKey": "K1", "accountId": "12345678", "accountType": "MARGIN", "institutionType": "BROKERAGE", "accountStatus": "ACTIVE"},
    {"accountIdKey": "K2", "accountId": "999", "accountStatus": "CLOSED"}]}}})


def sess(**extra):
    return Sess({"accounts/list": ACCTS, **extra})


def test_accounts_masks_number():
    out = el.list_accounts(sess())
    assert out[0]["account"] == "****5678" and "accountId" not in out[0]


def test_balance_fields():
    s = sess(**{"K1/balance": Resp(200, {"BalanceResponse": {"accountType": "MARGIN", "Computed": {
        "cashBuyingPower": 10.0, "marginBuyingPower": 40.0, "RealTimeValues": {"totalAccountValue": 500.0}}}})})
    b = el.balance(s)
    assert len(b) == 1  # closed account skipped
    assert (b[0]["cash_buying_power"], b[0]["margin_buying_power"], b[0]["total_account_value"]) == (10.0, 40.0, 500.0)


def test_positions_pages_and_totals():
    pos = lambda sym, mv, g: {"Product": {"symbol": sym}, "quantity": 1, "marketValue": mv, "totalGain": g, "daysGain": 1,
                              "Quick": {"lastTrade": mv}}
    s = sess(**{"K1/portfolio": [
        Resp(200, {"PortfolioResponse": {"AccountPortfolio": [{"totalPages": 2, "Position": [pos("AAA", 100, 10)]}]}}),
        Resp(200, {"PortfolioResponse": {"AccountPortfolio": [{"totalPages": 2, "Position": [pos("BBB", 50, -5)]}]}})]})
    r = el.positions(s)
    assert [p["symbol"] for p in r["positions"]] == ["AAA", "BBB"]
    assert r["totals"] == {"market_value": 150, "unrealized_pnl": 5, "day_pnl": 2}


def test_orders_empty_204_and_parse():
    assert el.orders(sess(**{"K1/orders": Resp(204)})) == []
    body = {"OrdersResponse": {"Order": [{"orderId": 7, "orderType": "EQ", "OrderDetail": [{
        "status": "OPEN", "priceType": "LIMIT", "limitPrice": 5, "Instrument": [{
            "Product": {"symbol": "MU"}, "orderAction": "BUY", "orderedQuantity": 3}]}]}]}}
    o = el.orders(sess(**{"K1/orders": Resp(200, body)}))
    assert (o[0]["symbol"], o[0]["action"], o[0]["qty"], o[0]["limit_price"]) == ("MU", "BUY", 3, 5)
    with pytest.raises(RuntimeError):
        el.orders(sess(), status="bogus")


def test_transactions_dates_and_account_filter():
    s = sess(**{"K1/transactions": Resp(200, {"TransactionListResponse": {"Transaction": [
        {"transactionId": 1, "transactionType": "Bought", "amount": -9, "brokerage": {"product": {"symbol": "X"}, "quantity": 1, "price": 9}}]}})})
    t = el.transactions(s, account="5678", since="2026-09-01", until="2026-09-30")
    assert t[0]["symbol"] == "X"
    assert s.calls[-1][1]["startDate"] == "09012026"
    with pytest.raises(RuntimeError):
        el.transactions(sess(), account="0000")


def test_401_is_reauth_not_crash():
    with pytest.raises(el.NotAuthed):
        el.balance(Sess({"accounts/list": Resp(401, {})}))


@pytest.fixture()
def server(monkeypatch):
    from agent import server
    return server


def test_tools_return_auth_message_when_no_token(server, monkeypatch):
    from sources import etrade
    monkeypatch.setenv("PROD_KEY", "k"); monkeypatch.setenv("PROD_SECRET", "s")
    monkeypatch.setattr(etrade, "_load_token", lambda: None)
    r = json.loads(server.etrade_accounts())
    assert r["auth_required"] and "Re-authorize" in r["error"]


def test_tools_return_auth_message_when_keys_missing(server, monkeypatch):
    monkeypatch.delenv("PROD_KEY", raising=False)
    monkeypatch.setattr(el.keys, "get", lambda n: None)
    assert "PROD_KEY" in json.loads(server.etrade_balance())["error"]


def test_tool_wraps_unexpected_error_without_secrets(server, monkeypatch):
    class Boom:
        def get(self, *a, **k):
            raise ConnectionError("down")
    monkeypatch.setattr(el, "session", lambda: Boom())
    r = json.loads(server.etrade_positions())
    assert "ConnectionError" in r["error"]


def test_no_write_tools_exposed(server):
    names = [n for n in dir(server) if n.startswith("etrade_") and n != "etrade_live"]
    assert sorted(names) == ["etrade_accounts", "etrade_balance", "etrade_orders", "etrade_positions", "etrade_transactions"]
