
import pytest

from core.schemas.views import VIEW_MODELS

pytestmark = pytest.mark.integration

BUCKETS_N = 6


def test_no_drift(s, con):
    for view in VIEW_MODELS:
        cols = [c[0] for c in con.execute(f"DESCRIBE {view}").fetchall()]
        assert set(cols) == set(VIEW_MODELS[view].model_fields), (view, set(cols) ^ set(VIEW_MODELS[view].model_fields))


def test_primary_bucket(con):
    rows = con.execute("SELECT primary_bucket, count(*), count(*) FILTER (WHERE primary_bucket IS NULL) "
                       "FROM universe GROUP BY 1").fetchall()
    named = [r for r in rows if r[0] is not None]
    assert len(named) <= BUCKETS_N
    nulls = sum(r[1] for r in rows if r[0] is None)
    total = sum(r[1] for r in rows)
    assert nulls < 0.1 * total
    assert con.execute("SELECT count(*) FROM universe WHERE primary_weight >= 0.999 AND primary_bucket IS NULL"
                       ).fetchone()[0] == 0


@pytest.mark.slow
def test_bars_30m(con):
    mn, mx, bad, nm = con.execute("""SELECT min(slot_minute), max(slot_minute),
        count(*) FILTER (WHERE (slot_minute - 570) % 30 != 0), max(n_minutes)
        FROM bars_30m WHERE et_date >= (SELECT max(et_date) - 30 FROM trading_days)""").fetchone()
    assert mn >= 570 and mx <= 930 and bad == 0 and nm <= 30


def test_trading_days_half(con):
    got = {r[0] for r in con.execute("SELECT CAST(et_date AS VARCHAR) FROM trading_days WHERE is_half_day").fetchall()}
    expected = {"2024-11-29", "2024-12-24", "2025-07-03", "2025-11-28", "2025-12-24"}
    lo = con.execute("SELECT CAST(min(et_date) AS VARCHAR) FROM trading_days").fetchone()[0]
    assert {d for d in expected if d >= lo} <= got
    assert got <= expected, got - expected


@pytest.mark.slow
def test_session_volume_ratio(con):
    r = con.execute("""WITH m AS (SELECT max(et_date) mx FROM trading_days)
        SELECT median(nasdaq_day_vol * 1.0 / cons_day_vol) FROM bars_1m_session, m
        WHERE et_date > mx - 30 AND et_minute = 600 AND cons_day_vol > 0""").fetchone()[0]
    assert 0.6 <= r <= 0.95
