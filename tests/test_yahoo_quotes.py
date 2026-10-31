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
