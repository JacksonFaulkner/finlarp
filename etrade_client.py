"""E*TRADE data client: cached OAuth1 session, JSON on stdout.

Usage:
    uv run etrade_client.py positions
    uv run etrade_client.py orders
    uv run etrade_client.py quote AAPL,MSFT

Requires PROD_KEY / PROD_SECRET in the environment (see .env at repo root).
Access token is cached at ~/.local/share/nvim/etrade_token.json and renewed
in place; falls back to an interactive browser OAuth flow only when the
cached token can no longer be renewed (after ET midnight rollover).
"""

from __future__ import annotations

import json
import os
import stat
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote

from rauth import OAuth1Service

import db

BASE_URL = "https://api.etrade.com"
TOKEN_PATH = Path(os.path.expanduser("~/.local/share/nvim/etrade_token.json"))


def _service() -> OAuth1Service:
    return OAuth1Service(
        name="etrade",
        consumer_key=os.environ["PROD_KEY"],
        consumer_secret=os.environ["PROD_SECRET"],
        request_token_url="https://api.etrade.com/oauth/request_token",
        access_token_url="https://api.etrade.com/oauth/access_token",
        authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
        base_url=BASE_URL,
    )


def _save_token(access_token: str, access_token_secret: str, renewed_at: float | None = None) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps({
        "access_token": access_token,
        "access_token_secret": access_token_secret,
        "renewed_at": renewed_at if renewed_at is not None else time.time(),
    }))
    os.chmod(TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)


def _load_token() -> dict | None:
    if not TOKEN_PATH.exists():
        return None
    return json.loads(TOKEN_PATH.read_text())


def _touch_renewed_at() -> None:
    data = _load_token()
    if data is not None:
        data["renewed_at"] = time.time()
        TOKEN_PATH.write_text(json.dumps(data))


class AuthRequired(Exception):
    """Raised instead of blocking on input() — the caller (nvim) isn't an
    interactive terminal, so login has to happen as two separate async
    steps: auth_start (get a URL) and auth_finish (submit the code the user
    pasted after actually looking at the browser page themselves)."""

    def __init__(self, authorize_url: str, request_token: str, request_token_secret: str):
        self.authorize_url = authorize_url
        self.request_token = request_token
        self.request_token_secret = request_token_secret


def _interactive_login(etrade: OAuth1Service, interactive: bool):
    request_token, request_token_secret = etrade.get_request_token(
        params={"oauth_callback": "oob", "format": "json"})
    # request_token is base64-ish (can contain +, /, =) — must be
    # percent-encoded as a query value or the URL is malformed (macOS
    # `open`/vim.ui.open reject it outright as a "bad URL").
    authorize_url = etrade.authorize_url.format(etrade.consumer_key, quote(request_token, safe=""))

    if not interactive:
        raise AuthRequired(authorize_url, request_token, request_token_secret)

    webbrowser.open(authorize_url)
    print(f"Open (if not auto-opened): {authorize_url}", file=sys.stderr)
    text_code = input("Verification code: ")
    session = etrade.get_auth_session(
        request_token, request_token_secret,
        params={"oauth_verifier": text_code})
    _save_token(session.access_token, session.access_token_secret)
    return session


def finish_login(request_token: str, request_token_secret: str, verifier: str):
    etrade = _service()
    session = etrade.get_auth_session(
        request_token, request_token_secret,
        params={"oauth_verifier": verifier})
    _save_token(session.access_token, session.access_token_secret)
    return session


# E*TRADE's idle timer is 2hr; renewing well under that (with margin for
# clock skew/slow calls) lets most invocations skip the renew round-trip
# entirely instead of paying it on every single call.
RENEW_MARGIN_SECONDS = 60 * 60


def get_session(interactive: bool = True):
    etrade = _service()
    cached = _load_token()
    if cached is None:
        return _interactive_login(etrade, interactive)

    session = etrade.get_session((cached["access_token"], cached["access_token_secret"]))

    renewed_at = cached.get("renewed_at", 0)
    if time.time() - renewed_at < RENEW_MARGIN_SECONDS:
        return session

    # Renew resets the 2hr idle timer without a browser round-trip. If the
    # token has rolled past ET midnight, E*TRADE rejects the renew and we
    # fall back to a fresh login.
    resp = session.get(BASE_URL + "/oauth/renew_access_token", params={})
    if resp.status_code != 200:
        return _interactive_login(etrade, interactive)
    _touch_renewed_at()
    return session


def cmd_positions(session) -> dict:
    accounts_resp = session.get(BASE_URL + "/v1/accounts/list.json", params={})
    accounts_resp.raise_for_status()
    accounts = (
        accounts_resp.json()
        .get("AccountListResponse", {})
        .get("Accounts", {})
        .get("Account", [])
    )

    result = []
    for account in accounts:
        account_id_key = account.get("accountIdKey")
        if not account_id_key:
            continue
        port_resp = session.get(
            BASE_URL + f"/v1/accounts/{account_id_key}/portfolio.json",
            params={},
        )
        if port_resp.status_code != 200:
            continue
        positions = (
            port_resp.json()
            .get("PortfolioResponse", {})
            .get("AccountPortfolio", [{}])[0]
            .get("Position", [])
        )
        for p in positions:
            # Product.symbol is the real ticker; symbolDescription is
            # free-text (can contain spaces) for some position types and
            # breaks the comma-joined quote URL if it's used as the symbol.
            symbol = p.get("Product", {}).get("symbol") or p.get("symbolDescription")
            quick = p.get("Quick", {})
            result.append({
                "account": account.get("accountId"),
                "symbol": symbol,
                "quantity": p.get("quantity"),
                "last_price": quick.get("lastTrade"),
                "price_paid": p.get("pricePaid"),
                "total_gain": p.get("totalGain"),
                "market_value": p.get("marketValue"),
                # portfolio.json already includes today's change per
                # position — no separate quote.json round trip needed.
                "change_close": p.get("daysGain"),
                "change_close_pct": p.get("daysGainPct"),
            })
    db.put_cached_positions(result)

    # Stock-only market value understates true account equity (ignores
    # cash) and, worse, makes buying new stock with freshly deposited cash
    # look like a huge same-day "gain" — the jump is capital deployment,
    # not return. totalAccountValue from balance.json is cash + positions,
    # matching how backfill_history.py computes historical days (cash
    # tracked via transaction amounts), so the two methods agree.
    total_value = 0.0
    for account in accounts:
        account_id_key = account.get("accountIdKey")
        if not account_id_key:
            continue
        bal_resp = session.get(
            BASE_URL + f"/v1/accounts/{account_id_key}/balance.json",
            params={"instType": "BROKERAGE", "realTimeNAV": "true"},
        )
        if bal_resp.status_code != 200:
            continue
        total_value += (
            bal_resp.json()
            .get("BalanceResponse", {})
            .get("Computed", {})
            .get("RealTimeValues", {})
            .get("totalAccountValue") or 0
        )

    if total_value:
        today = time.strftime("%Y-%m-%d")
        # Exclude today's deposits/withdrawals from the return calc — an
        # Online Transfer changes account value without being a gain/loss.
        transfers_today = sum(
            t.get("amount") or 0
            for t in db.get_all_cached_transactions()
            if t.get("type") == "Online Transfer" and t.get("date")
            and time.strftime("%Y-%m-%d", time.localtime(t["date"] / 1000)) == today
        )
        prior = db.get_portfolio_history()
        prior_value = prior[-1]["total_value"] if prior and prior[-1]["date"] != today else (
            prior[-2]["total_value"] if len(prior) >= 2 else None
        )
        if prior_value:
            day_change_pct = (total_value - prior_value - transfers_today) / prior_value * 100
            db.upsert_portfolio_snapshot(total_value, day_change_pct)
        else:
            db.upsert_portfolio_snapshot(total_value, 0.0)

    return {"positions": result}


def cmd_positions_cached() -> dict:
    """Local-only read, no OAuth session/network — for painting the
    dashboard instantly while a live `positions` pull runs in the
    background. Returns positions: null if nothing's cached yet."""
    return {"positions": db.get_cached_positions()}


def cmd_orders(session) -> dict:
    accounts_resp = session.get(BASE_URL + "/v1/accounts/list.json", params={})
    accounts_resp.raise_for_status()
    accounts = (
        accounts_resp.json()
        .get("AccountListResponse", {})
        .get("Accounts", {})
        .get("Account", [])
    )

    result = []
    for account in accounts:
        account_id_key = account.get("accountIdKey")
        if not account_id_key:
            continue
        resp = session.get(
            BASE_URL + f"/v1/accounts/{account_id_key}/orders.json",
            params={},
        )
        if resp.status_code != 200:
            continue
        orders = resp.json().get("OrdersResponse", {}).get("Order", [])
        for o in orders:
            result.append(o)
    return {"orders": result}


def cmd_quote(session, symbols: str) -> dict:
    url = BASE_URL + "/v1/market/quote/" + symbols + ".json"
    resp = session.get(url, params={})
    resp.raise_for_status()
    quotes = resp.json().get("QuoteResponse", {}).get("QuoteData", [])
    result = []
    for q in quotes:
        all_data = q.get("All", {})
        result.append({
            "symbol": q.get("Product", {}).get("symbol"),
            "last_trade": all_data.get("lastTrade"),
            "change_close": all_data.get("changeClose"),
            "change_close_pct": all_data.get("changeClosePercentage"),
            "previous_close": all_data.get("previousClose"),
        })
    return {"quotes": result}


def cmd_portfolio_history() -> dict:
    """Local-only read, no OAuth session/network — the ratatui portfolio
    chart binary reads DuckDB directly instead, but this exists so the
    history is inspectable/debuggable from the CLI too."""
    return {"history": db.get_portfolio_history()}


def cmd_transactions_cached() -> dict:
    """Local-only read, no OAuth session/network — pairs with the same
    instant-then-refresh pattern as positions_cached."""
    return {"transactions": db.get_all_cached_transactions()}


def cmd_transactions(session) -> dict:
    accounts_resp = session.get(BASE_URL + "/v1/accounts/list.json", params={})
    accounts_resp.raise_for_status()
    accounts = (
        accounts_resp.json()
        .get("AccountListResponse", {})
        .get("Accounts", {})
        .get("Account", [])
    )

    result = []
    for account in accounts:
        account_id_key = account.get("accountIdKey")
        account_id = account.get("accountId")
        if not account_id_key or not account_id:
            continue

        cached = db.get_cached_transactions(account_id)
        if cached is not None:
            result.extend(cached)
            continue

        # E*TRADE defaults to a narrow recent window and paginates via a
        # `marker` cursor (not an offset) — walk it until the response stops
        # supplying one. startDate on its own 500s — E*TRADE requires
        # endDate alongside it. 2 years covers realistic transaction-search
        # needs.
        # count > 50 500s — E*TRADE's max page size for this endpoint is 50
        # even though other endpoints allow more.
        two_years_ago = time.strftime("%m%d%Y", time.localtime(time.time() - 2 * 365 * 86400))
        today = time.strftime("%m%d%Y")
        params = {"startDate": two_years_ago, "endDate": today, "count": 50}
        raw_txns = []
        while True:
            resp = session.get(
                BASE_URL + f"/v1/accounts/{account_id_key}/transactions.json",
                params=params,
            )
            if resp.status_code != 200:
                break
            payload = resp.json().get("TransactionListResponse", {})
            raw_txns.extend(payload.get("Transaction", []))
            marker = payload.get("marker")
            if not marker:
                break
            params = {**params, "marker": marker}

        account_txns = []
        for t in raw_txns:
            brokerage = t.get("brokerage", {})
            product = brokerage.get("product", {})
            account_txns.append({
                "account": account_id,
                "transaction_id": t.get("transactionId"),
                # transactionDate is epoch millis from E*TRADE
                "date": t.get("transactionDate"),
                "type": t.get("transactionType"),
                "description": t.get("description"),
                "symbol": product.get("symbol"),
                "quantity": brokerage.get("quantity"),
                "price": brokerage.get("price"),
                "amount": t.get("amount"),
            })
        db.put_cached_transactions(account_id, account_txns)
        result.extend(account_txns)
    return {"transactions": result}


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: etrade_client.py <positions|orders|transactions|quote SYMBOLS|auth_finish TOKEN SECRET CODE>", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "auth_finish":
        if len(sys.argv) < 5:
            print("usage: etrade_client.py auth_finish REQUEST_TOKEN REQUEST_TOKEN_SECRET CODE", file=sys.stderr)
            sys.exit(1)
        finish_login(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps({"ok": True}))
        return

    if cmd == "positions_cached":
        print(json.dumps(cmd_positions_cached()))
        return

    if cmd == "transactions_cached":
        print(json.dumps(cmd_transactions_cached()))
        return

    if cmd == "portfolio_history":
        print(json.dumps(cmd_portfolio_history()))
        return

    try:
        # nvim isn't a TTY input() can block on — get_session never falls
        # back to the blocking browser/input() flow here. A stale token
        # comes back as a normal auth_required payload instead of an error,
        # so the caller can drive the two-step login itself.
        session = get_session(interactive=False)
    except AuthRequired as e:
        print(json.dumps({
            "auth_required": True,
            "authorize_url": e.authorize_url,
            "request_token": e.request_token,
            "request_token_secret": e.request_token_secret,
        }))
        return

    if cmd == "positions":
        output = cmd_positions(session)
    elif cmd == "orders":
        output = cmd_orders(session)
    elif cmd == "quote":
        if len(sys.argv) < 3:
            print("usage: etrade_client.py quote SYMBOL1,SYMBOL2", file=sys.stderr)
            sys.exit(1)
        output = cmd_quote(session, sys.argv[2])
    elif cmd == "transactions":
        output = cmd_transactions(session)
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(output))


if __name__ == "__main__":
    main()
