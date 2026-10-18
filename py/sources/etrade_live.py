"""Read-only live E*TRADE queries for the MCP server. Reuses sources.etrade for OAuth and the cached
token; never places, changes or cancels orders. Nothing here returns or logs tokens or keys."""
from __future__ import annotations

import os
import time

from sources import keys

BASE = "https://api.etrade.com"
REAUTH = ("E*TRADE authorization is missing or expired. Re-authorize in a terminal: from the repo's py/ dir run "
          "`uv run --env-file ../.env python -c \"from sources import etrade; etrade.get_session()\"`, open the "
          "URL it prints, and paste the verification code. (Or use the nvim portfolio login.) Then retry.")


class NotAuthed(Exception):
    """Raised with a user-facing message when a live session can't be had."""


def _need_keys() -> None:
    for k in ("PROD_KEY", "PROD_SECRET"):
        if not os.environ.get(k):
            v = keys.get(k)
            if not v:
                raise NotAuthed(f"{k} is not set. Add PROD_KEY and PROD_SECRET (E*TRADE production consumer "
                                "key/secret) to the repo .env or the server environment.")
            os.environ[k] = v


def session():
    """Authenticated requests session via the existing cached token. Never starts a login."""
    from sources import etrade
    _need_keys()
    if etrade._load_token() is None:
        raise NotAuthed(REAUTH)
    try:
        return etrade.get_session(interactive=False)
    except etrade.AuthRequired:
        raise NotAuthed(REAUTH) from None


def _get(sess, path: str, params: dict | None = None) -> dict:
    """GET JSON. 401 -> NotAuthed; 204 -> {}; other errors raise RuntimeError without request details."""
    r = sess.get(BASE + path, params=params or {}, headers={"Accept": "application/json"})
    if r.status_code == 401:
        raise NotAuthed(REAUTH)
    if r.status_code == 204 or not r.content:
        return {}
    if r.status_code != 200:
        msg = ""
        try:
            msg = r.json().get("Error", {}).get("message", "")
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(f"E*TRADE HTTP {r.status_code} on {path.split('/')[-1]}: {msg}"[:300])
    return r.json()


def _mask(n) -> str | None:
    n = str(n or "")
    return ("****" + n[-4:]) if n else None


def accounts(sess) -> list[dict]:
    raw = _get(sess, "/v1/accounts/list.json").get("AccountListResponse", {}).get("Accounts", {}).get("Account", [])
    return [{"accountIdKey": a.get("accountIdKey"), "account": _mask(a.get("accountId")),
             "accountId": a.get("accountId"),
             "mode": a.get("accountMode"), "description": a.get("accountDesc"), "name": a.get("accountName"),
             "type": a.get("accountType"), "institution": a.get("institutionType"),
             "status": a.get("accountStatus"), "closed_date": a.get("closedDate")}
            for a in raw if a.get("accountIdKey")]


def _select(sess, account: str) -> list[dict]:
    accts = [a for a in accounts(sess) if a["status"] != "CLOSED"]
    if account:
        want = account.strip()
        accts = [a for a in accts if want in (a["accountIdKey"], a["accountId"]) or str(a["accountId"] or "").endswith(want)]
        if not accts:
            raise RuntimeError(f"no open E*TRADE account matches {account!r}; call etrade_accounts")
    return accts


def _public(a: dict) -> dict:
    return {k: v for k, v in a.items() if k != "accountId"}


def list_accounts(sess) -> list[dict]:
    return [_public(a) for a in accounts(sess)]


def balance(sess, account: str = "") -> list[dict]:
    out = []
    for a in _select(sess, account):
        b = _get(sess, f"/v1/accounts/{a['accountIdKey']}/balance.json",
                 {"instType": a["institution"] or "BROKERAGE", "realTimeNAV": "true"}).get("BalanceResponse", {})
        comp = b.get("Computed", {}) or {}
        out.append({
            "account": a["account"], "accountIdKey": a["accountIdKey"], "type": b.get("accountType") or a["type"],
            "option_level": b.get("optionLevel"),
            "total_account_value": (comp.get("RealTimeValues") or {}).get("totalAccountValue"),
            "net_market_value": (comp.get("RealTimeValues") or {}).get("netMv"),
            "cash_available_for_investment": comp.get("cashAvailableForInvestment"),
            "cash_buying_power": comp.get("cashBuyingPower"),
            "margin_buying_power": comp.get("marginBuyingPower"),
            "dt_margin_buying_power": comp.get("dtMarginBuyingPower"),
            "net_cash": comp.get("netCash"),
            "margin_balance": comp.get("marginBalance"),
            "settled_cash_for_investment": comp.get("settledCashForInvestment"),
            "cash_available_for_withdrawal": comp.get("cashAvailableForWithdrawal"),
            "margin_equity": comp.get("marginEquity"),
            "cash": b.get("Cash"), "margin": b.get("Margin"), "computed": comp,
        })
    return out


def positions(sess, account: str = "") -> dict:
    rows = []
    for a in _select(sess, account):
        page = 1
        while True:
            port = _get(sess, f"/v1/accounts/{a['accountIdKey']}/portfolio.json",
                        {"count": 100, "pageNumber": page, "totalsRequired": "true", "view": "QUICK"})
            ap = (port.get("PortfolioResponse", {}).get("AccountPortfolio") or [{}])[0]
            for p in ap.get("Position", []):
                prod = p.get("Product", {}) or {}
                rows.append({
                    "account": a["account"], "symbol": prod.get("symbol") or p.get("symbolDescription"),
                    "security_type": prod.get("securityType"), "position_type": p.get("positionType"),
                    "quantity": p.get("quantity"), "last": (p.get("Quick") or {}).get("lastTrade"),
                    "price_paid": p.get("pricePaid"), "cost_basis": p.get("totalCost"),
                    "market_value": p.get("marketValue"),
                    "unrealized_pnl": p.get("totalGain"), "unrealized_pnl_pct": p.get("totalGainPct"),
                    "day_pnl": p.get("daysGain"), "day_pnl_pct": p.get("daysGainPct"),
                    "pct_of_portfolio": p.get("pctOfPortfolio"),
                })
            total = int(ap.get("totalPages") or 1)
            if page >= total or page >= 20:
                break
            page += 1
    tot = lambda k: round(sum(r[k] or 0 for r in rows), 2)  # noqa: E731
    return {"positions": rows, "totals": {"market_value": tot("market_value"), "unrealized_pnl": tot("unrealized_pnl"),
                                          "day_pnl": tot("day_pnl")}}


def _mmddyyyy(s: str) -> str:
    return time.strftime("%m%d%Y", time.strptime(s, "%Y-%m-%d"))


def orders(sess, account: str = "", status: str = "OPEN", since: str = "", until: str = "", limit: int = 50) -> list[dict]:
    status = status.upper()
    if status not in {"OPEN", "EXECUTED", "CANCELLED", "INDIVIDUAL_FILLS", "CANCEL_REQUESTED", "EXPIRED", "REJECTED"}:
        raise RuntimeError("status must be one of OPEN, EXECUTED, CANCELLED, INDIVIDUAL_FILLS, CANCEL_REQUESTED, EXPIRED, REJECTED")
    out = []
    for a in _select(sess, account):
        params = {"status": status, "count": min(max(limit, 1), 100)}
        if since:
            params["fromDate"] = _mmddyyyy(since)
        if until:
            params["toDate"] = _mmddyyyy(until)
        while len(out) < limit:
            payload = _get(sess, f"/v1/accounts/{a['accountIdKey']}/orders.json", params).get("OrdersResponse", {})
            for o in payload.get("Order", []):
                for d in o.get("OrderDetail", [{}]):
                    for inst in d.get("Instrument", [{}]):
                        out.append({
                            "account": a["account"], "order_id": o.get("orderId"), "type": o.get("orderType"),
                            "status": d.get("status"), "placed_ms": d.get("placedTime"),
                            "executed_ms": d.get("executedTime"),
                            "symbol": (inst.get("Product") or {}).get("symbol"), "action": inst.get("orderAction"),
                            "qty": inst.get("orderedQuantity"), "filled_qty": inst.get("filledQuantity"),
                            "avg_exec_price": inst.get("averageExecutionPrice"),
                            "price_type": d.get("priceType"), "limit_price": d.get("limitPrice"),
                            "stop_price": d.get("stopPrice"), "duration": d.get("orderTerm"),
                            "estimated_commission": d.get("estimatedCommission"),
                        })
            marker = payload.get("marker")
            if not marker:
                break
            params = {**params, "marker": marker}
    return out[:limit]


def transactions(sess, account: str = "", since: str = "", until: str = "", limit: int = 50) -> list[dict]:
    now = time.time()
    since = since or time.strftime("%Y-%m-%d", time.localtime(now - 30 * 86400))
    until = until or time.strftime("%Y-%m-%d", time.localtime(now))
    out = []
    for a in _select(sess, account):
        params = {"startDate": _mmddyyyy(since), "endDate": _mmddyyyy(until), "count": 50, "sortOrder": "DESC"}
        n = 0
        while n < limit:
            payload = _get(sess, f"/v1/accounts/{a['accountIdKey']}/transactions.json", params).get("TransactionListResponse", {})
            for t in payload.get("Transaction", []):
                br = t.get("brokerage") or {}
                out.append({"account": a["account"], "transaction_id": t.get("transactionId"),
                            "date_ms": t.get("transactionDate"), "type": t.get("transactionType"),
                            "description": t.get("description"), "symbol": (br.get("product") or {}).get("symbol"),
                            "quantity": br.get("quantity"), "price": br.get("price"), "amount": t.get("amount")})
                n += 1
            if not payload.get("marker"):
                break
            params = {**params, "marker": payload["marker"]}
    return out[:limit]
