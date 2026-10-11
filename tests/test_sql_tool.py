import json

import pytest

pytestmark = pytest.mark.integration


def q(s, *a, **k):
    return json.loads(s.sql(*a, **k))


def test_rejects_non_select(s, con):
    assert "error" in q(s, "CREATE TABLE x AS SELECT 1")
    assert "error" in q(s, "SELECT 1; SELECT 2")


def test_bad_column(s, con):
    r = q(s, "SELECT nope FROM universe")
    assert r["error"].startswith("BinderException")


def test_basic(s, con):
    r = q(s, "SELECT ticker FROM universe", max_rows=5)
    assert r["row_count"] == 5 and r["truncated"]


@pytest.mark.slow
def test_timeout_and_recovery(s, con):
    r = q(s, "SELECT count(*) FROM bars_1m a JOIN bars_1m b ON a.symbol = b.symbol AND a.close < b.close",
          timeout_s=1, fresh=True)
    assert "timed out" in r["error"]
    assert q(s, "SELECT 1 AS x")["rows"] == [[1]]


def test_save_as(s, con):
    r = q(s, "SELECT ticker FROM universe", save_as="pytest_tmp")
    assert r["row_count"] <= 20 and r["preview"]
    back = q(s, f"SELECT count(*) FROM read_parquet('{r['saved_to']}')")
    assert back["rows"][0][0] == r["total_rows"]


def test_bad_save_as(s, con):
    assert "save_as" in q(s, "SELECT 1", save_as="../evil")["error"]


@pytest.mark.slow
def test_cache(s, con):
    s._SQL_CACHE.clear()
    sqlq = "SELECT count(*) FROM bars_1m a JOIN bars_1m b ON a.symbol = b.symbol AND a.ts_event = b.ts_event"
    r1 = q(s, sqlq)
    if r1["elapsed_ms"] <= s._SQL_CACHE_MIN_MS:
        pytest.skip("query too fast to be cached on this machine")
    assert not r1.get("cached")
    r2 = q(s, sqlq)
    assert r2["cached"] is True and r2["elapsed_ms"] == 0
    assert not q(s, sqlq, fresh=True).get("cached")


def test_errors_not_cached(s, con):
    s._SQL_CACHE.clear()
    q(s, "SELECT nope FROM universe")
    q(s, "SELECT nope FROM universe")
    assert not s._SQL_CACHE
