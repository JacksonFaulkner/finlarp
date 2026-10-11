"""Derived (materialized) tables: stale -> live SQL fallback, background rebuild, view swap, exact parity."""

import threading
import time

import pytest

from agent import server as s

pytestmark = [pytest.mark.integration, pytest.mark.slow]


@pytest.fixture()
def isolated_derived(request, monkeypatch):
    """Point the derived machinery at an empty dir with only the cheap trading_days table.

    The dir must live under the data root: the connection's allowed_directories lock rejects views over
    files elsewhere. A few KB of parquet are left behind per test name (overwritten on the next run).
    """
    tmp_path = s.D / "market" / "derived_test" / request.node.name
    tmp_path.mkdir(parents=True, exist_ok=True)
    for old in tmp_path.glob("*.parquet"):
        old.unlink()
    con = s._db()  # build the shared connection against the real tables before patching anything
    real_src = s._derived_src("trading_days")
    monkeypatch.setattr(s, "DERIVED", tmp_path)
    monkeypatch.setattr(s, "_DERIVED", {"trading_days": s._DERIVED["trading_days"]})
    monkeypatch.setattr(s, "_derived_building", False)
    yield tmp_path
    for t in threading.enumerate():
        if t.name == "derived-build":
            t.join(timeout=60)
    con.cursor().execute(f"CREATE OR REPLACE VIEW trading_days AS SELECT * FROM {real_src}")


def test_missing_parquet_uses_live_sql(isolated_derived):
    assert not s._derived_fresh("trading_days")
    assert s._derived_src("trading_days") == s._DERIVED["trading_days"][0]


def test_background_build_swaps_view_and_matches_live(isolated_derived):
    con = s._db()
    live = con.execute(f"SELECT * FROM {s._DERIVED['trading_days'][0]} ORDER BY et_date").fetchall()
    s._refresh_derived_async()
    deadline = time.time() + 120
    while time.time() < deadline and not s._derived_fresh("trading_days"):
        time.sleep(0.5)
    assert s._derived_fresh("trading_days"), "background build did not finish"
    for t in threading.enumerate():
        if t.name == "derived-build":
            t.join(timeout=30)
    view_sql = con.execute("SELECT sql FROM duckdb_views() WHERE view_name = 'trading_days'").fetchone()[0]
    assert str(isolated_derived) in view_sql
    assert con.execute("SELECT * FROM trading_days ORDER BY et_date").fetchall() == live


def test_fresh_parquet_is_used(isolated_derived):
    s._build_derived("trading_days")
    assert s._derived_fresh("trading_days")
    assert s._derived_src("trading_days") == f"'{s._derived_path('trading_days')}'"


def test_stale_when_sources_newer(isolated_derived, monkeypatch):
    s._build_derived("trading_days")
    monkeypatch.setattr(s, "_sources_mtime", lambda: time.time() + 3600)
    assert not s._derived_fresh("trading_days")
