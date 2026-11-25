from datetime import datetime

from sources import yahoo


def _q(**fields):
    return {"symbol": "LITE", "regularMarketPrice": 840.7, "regularMarketChange": -78.83,
            "regularMarketChangePercent": -8.57, "regularMarketPreviousClose": 919.53, **fields}


def test_regular_session_repeats_the_regular_fields():
    row = yahoo.parse_quotes({"quoteResponse": {"result": [_q(marketState="REGULAR")]}})[0]
    assert row["session"] == "regular"
    assert row["session_price"] == 840.7
    assert row["session_change_pct"] == -8.57
    assert row["change_close_pct"] == -8.57


def test_pre_market_print_is_measured_against_the_last_close():
    q = _q(marketState="PRE", preMarketPrice=859.0, preMarketChangePercent=-6.58)
    row = yahoo.parse_quotes({"quoteResponse": {"result": [q]}})[0]
    assert row["session"] == "pre"
    assert (row["session_price"], row["session_change_pct"]) == (859.0, -6.58)
    # the regular fields still describe the regular session, not the pre-market print
    assert row["change_close_pct"] == -8.57


def test_post_market_and_closed_sessions():
    post = _q(marketState="POST", postMarketPrice=845.0, postMarketChangePercent=0.51)
    assert yahoo.parse_quotes({"quoteResponse": {"result": [post]}})[0]["session"] == "post"
    closed = _q(marketState="CLOSED")
    row = yahoo.parse_quotes({"quoteResponse": {"result": [closed]}})[0]
    assert row["session"] == "closed"
    assert row["session_price"] == 840.7


def test_empty_payload():
    assert yahoo.parse_quotes({"quoteResponse": {"result": None}}) == []
    assert yahoo.parse_quotes({}) == []


def _row(**fields):
    base = {"symbol": "NVDA", "last_trade": 125.53, "previous_close": 145.98,
            "regular_time": 1763672400}  # Fri 2025-11-20 16:00 ET-ish
    return {**base, **fields}


def test_since_close_pre_market_measures_from_the_last_close():
    from datetime import date
    # Monday morning: the last regular print is from Friday, so it is the base
    fri = int(datetime(2026, 11, 20, 16, 0, tzinfo=yahoo.NY).timestamp())
    mon = int(datetime(2026, 11, 23, 9, 20, tzinfo=yahoo.NY).timestamp())
    m = yahoo.since_close(_row(regular_time=fri, pre_price=164.1, pre_time=mon), date(2026, 11, 23))
    assert (m["base"], m["price"]) == (125.53, 164.1)
    assert round(m["pct"], 2) == 30.73


def test_since_close_after_todays_session_uses_the_previous_close():
    from datetime import date
    mon_close = int(datetime(2026, 11, 23, 16, 0, tzinfo=yahoo.NY).timestamp())
    mon_post = int(datetime(2026, 11, 23, 17, 0, tzinfo=yahoo.NY).timestamp())
    stale_pre = int(datetime(2026, 11, 23, 9, 0, tzinfo=yahoo.NY).timestamp())
    row = _row(last_trade=150.0, previous_close=125.53, regular_time=mon_close,
               pre_price=164.1, pre_time=stale_pre, post_price=151.0, post_time=mon_post)
    m = yahoo.since_close(row, date(2026, 11, 23))
    assert (m["base"], m["price"]) == (125.53, 151.0)


def test_since_close_needs_a_regular_print():
    from datetime import date
    assert yahoo.since_close(_row(regular_time=None), date(2026, 11, 23)) is None
