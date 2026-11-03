from sources import ticker_tape


def _q(sym, *, vol, avg, pct, price=10.0):
    return {"symbol": sym, "volume": vol, "avg_volume_10d": avg,
            "change_close_pct": pct, "last_trade": price}


def test_needs_both_heavy_volume_and_a_real_move():
    quotes = [
        _q("HOT", vol=3_000_000, avg=1_000_000, pct=-4.0),   # both: qualifies
        _q("QUIET", vol=3_000_000, avg=1_000_000, pct=0.5),  # volume only
        _q("MOVE", vol=900_000, avg=1_000_000, pct=6.0),     # move only
    ]
    assert [m["ticker"] for m in ticker_tape.movers(quotes)] == ["HOT"]


def test_ranks_by_volume_ratio_times_move_size():
    quotes = [
        _q("A", vol=2_000_000, avg=1_000_000, pct=3.0),   # 2.0 * 3 = 6
        _q("B", vol=4_000_000, avg=1_000_000, pct=-2.5),  # 4.0 * 2.5 = 10
    ]
    assert [m["ticker"] for m in ticker_tape.movers(quotes)] == ["B", "A"]


def test_missing_fields_are_skipped_not_fatal():
    quotes = [
        _q("NOVOL", vol=None, avg=1_000_000, pct=5.0),
        _q("NOAVG", vol=3_000_000, avg=None, pct=5.0),
        _q("NOPCT", vol=3_000_000, avg=1_000_000, pct=None),
    ]
    assert ticker_tape.movers(quotes) == []


def test_output_is_trimmed_to_top():
    quotes = [_q(f"T{i}", vol=3_000_000, avg=1_000_000, pct=2.0 + i) for i in range(40)]
    assert len(ticker_tape.movers(quotes)) == ticker_tape.TOP


def _ext(sym, state, *, pct=4.0, vol=3_000_000, avg=1_000_000, **fields):
    q = _q(sym, vol=vol, avg=avg, pct=pct)
    q.update({"market_state": state, "regular_time": 100, **fields})
    return q


def test_regular_session_has_no_extended_move():
    q = _ext("A", "REGULAR", post_change_pct=3.0, post_time=200)
    [m] = ticker_tape.movers([q])
    assert (m["ext_label"], m["ext_pct"]) == (None, None)


def test_after_hours_and_overnight_show_the_post_print():
    for state in ("POST", "POSTPOST", "CLOSED"):
        q = _ext("A", state, post_change_pct=3.14, post_time=200)
        [m] = ticker_tape.movers([q])
        assert (m["ext_label"], m["ext_pct"]) == ("AH", 3.14), state


def test_pre_market_shows_the_pre_print_else_last_after_hours():
    q = _ext("A", "PRE", pre_change_pct=-1.5, pre_time=200, post_change_pct=3.0, post_time=150)
    assert ticker_tape.extended(q) == ("PM", -1.5)
    q = _ext("A", "PRE", post_change_pct=3.0, post_time=150)
    assert ticker_tape.extended(q) == ("AH", 3.0)


def test_a_print_older_than_the_regular_close_is_ignored():
    q = _ext("A", "POST", post_change_pct=3.0, post_time=50)
    assert ticker_tape.extended(q) is None
    assert ticker_tape.extended(_ext("A", "POST")) is None  # no fields at all


def test_big_extended_move_alone_qualifies_and_ranks_higher():
    quiet_day = _ext("EARN", "POST", pct=0.5, vol=1_200_000, post_change_pct=-12.0, post_time=200)
    small_ah = _ext("SMALL", "POST", pct=0.5, vol=1_200_000, post_change_pct=3.0, post_time=200)
    day_only = _ext("DAY", "POST", pct=2.5, vol=2_000_000)
    got = ticker_tape.movers([quiet_day, small_ah, day_only])
    assert [m["ticker"] for m in got] == ["EARN", "DAY"]
    assert got[0]["ext_label"] == "AH"
