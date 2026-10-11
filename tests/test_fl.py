import numpy as np
import pandas as pd
from pytest import approx as pytest_approx

from agent import fl


def test_tstat_known():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    expected = 3 / (np.std(x, ddof=1) / np.sqrt(5))
    assert fl.tstat(x) == pytest_approx(expected)


def test_tstat_nan_small_or_constant():
    assert np.isnan(fl.tstat([1.0, 2.0]))
    assert np.isnan(fl.tstat([]))
    assert np.isnan(fl.tstat([2.0, 2.0, 2.0]))
    assert np.isnan(fl.tstat([1.0, np.nan, 2.0]))  # NaN dropped -> n=2


def test_p_from_t():
    p = fl.p_from_t([0.0, 1.96, -1.96])
    assert p[0] == pytest_approx(1.0)
    assert p[1] == pytest_approx(0.05, abs=1e-3) and p[2] == p[1]


def test_bh_hand_example():
    p = np.array([0.04, 0.001, 0.03, 0.2])
    # sorted: .001,.03,.04,.2 -> *4/rank: .004,.06,.0533,.2 -> cummin from end: .004,.0533,.0533,.2
    q = fl.bh(p)
    assert q == pytest_approx(np.array([0.05333333, 0.004, 0.05333333, 0.2]))


def test_bh_monotone_clipped_order():
    rng = np.random.default_rng(0)
    p = rng.uniform(size=50)
    q = fl.bh(p)
    assert q.max() <= 1.0 and (q >= p - 1e-12).all()
    o = np.argsort(p)
    assert (np.diff(q[o]) >= -1e-12).all()
    assert fl.bh(np.array([0.9, 0.95])).max() <= 1.0


def test_ols_recovers():
    rng = np.random.default_rng(1)
    x = rng.normal(size=500)
    y = 2 + 3 * x + rng.normal(scale=0.5, size=500)
    r = fl.ols(y, pd.DataFrame({"x": x}))
    assert abs(r.loc["const", "coef"] - 2) < 0.1
    assert abs(r.loc["x", "coef"] - 3) < 0.1
    assert r.loc["x", "t"] > 50


def test_alpha_beta_planted():
    rng = np.random.default_rng(2)
    rows = []
    for b in "ABCD":
        mkt = rng.normal(0, 0.01, 400)
        alpha = 0.002 if b == "A" else 0.0
        ret = alpha + 1.2 * mkt + rng.normal(0, 0.003, 400)
        rows.append(pd.DataFrame({"bucket": b, "slot": 570, "ret": ret, "mkt": mkt}))
    out = fl.alpha_beta(pd.concat(rows)).set_index("bucket")
    assert abs(out.loc["A", "alpha_bps"] - 20) < 5
    assert out.loc["A", "q_bh"] < 0.01
    assert (out.drop("A")["q_bh"] > 0.05).all()
    assert abs(out.loc["A", "beta"] - 1.2) < 0.1
