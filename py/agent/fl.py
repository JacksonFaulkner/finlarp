"""Analysis helpers preloaded into `run_python` as `fl`.

Deliberately standalone (numpy/pandas/scipy/statsmodels only, no finlarp imports): the sandboxed
child can't import modules that read `.env`. The defaults encode the lessons from the time-of-day
study: test against a beta-adjusted benchmark, not a raw one; correct for the many cells you test;
drop early-close days; report how many days/symbols a number rests on.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

def slot_label(minute: int) -> str:
    return f"{minute // 60}:{minute % 60:02d}"


def tstat(x) -> float:
    """Mean over standard error; NaN for fewer than 3 observations."""
    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    if len(x) < 3 or x.std(ddof=1) == 0:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))


def p_from_t(t) -> np.ndarray:
    """Two-sided p-value under the normal approximation (fine for n in the hundreds)."""
    return 2 * stats.norm.sf(np.abs(np.asarray(t, dtype=float)))


def bh(p) -> np.ndarray:
    """Benjamini-Hochberg q-values, in the input order. Use when you test many cells."""
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    q = np.empty_like(p)
    ranked = p[order] * len(p) / (np.arange(len(p)) + 1)
    q[order] = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1.0)
    return q


def ols(y, X, robust: bool = True) -> pd.DataFrame:
    """OLS with an intercept. Returns coef/se/t/p per term (HC1-robust errors by default)."""
    import statsmodels.api as sm

    Xd = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
    res = sm.OLS(np.asarray(y, dtype=float), sm.add_constant(Xd, has_constant="add")).fit(
        cov_type="HC1" if robust else "nonrobust")
    names = ["const"] + [str(c) for c in Xd.columns]
    return pd.DataFrame({"coef": res.params, "se": res.bse, "t": res.tvalues, "p": res.pvalues}, index=names)


def alpha_beta(df: pd.DataFrame, y: str = "ret", mkt: str = "mkt", by=("bucket", "slot")) -> pd.DataFrame:
    """Per group, regress y on mkt: alpha (in bps), beta, their t-stats, BH q-value across groups."""
    rows = []
    for key, g in df.groupby(list(by)):
        if len(g) < 30:
            continue
        r = ols(g[y].values, g[[mkt]])
        rows.append((*(key if isinstance(key, tuple) else (key,)), len(g),
                     r.loc["const", "coef"] * 1e4, r.loc["const", "t"], r.loc[mkt, "coef"], r.loc["const", "p"]))
    out = pd.DataFrame(rows, columns=[*by, "n", "alpha_bps", "t_alpha", "beta", "p"])
    out["q_bh"] = bh(out["p"].values) if len(out) else []
    return out.sort_values("p").reset_index(drop=True)


def bucket_slot_panel(con, bars: str = "bars_30m", exclude_half_days: bool = True) -> pd.DataFrame:
    """Equal-weight bucket return per (date, slot) with the all-universe return as `mkt`.

    Columns: bucket, d, slot, ret, aret (mean |ret|), vshare (share of day's consolidated-scaled
    volume), mkt, maret, ex (ret - mkt), rel_vol (aret / maret). Early-close days are dropped
    (trading_days.is_half_day) so a 13:00 close does not pollute the late slots; pass False to keep.
    """
    half = "AND NOT t.is_half_day" if exclude_half_days else ""
    r = con.execute(f"""
        WITH s AS (
          SELECT b.symbol, b.et_date, b.slot_minute, b.close / b.open - 1 AS ret,
                 b.vol_est / sum(b.vol_est) OVER (PARTITION BY b.symbol, b.et_date) AS vshare
          FROM {bars} b JOIN trading_days t USING (et_date)
          WHERE b.open > 0 {half}
        )
        SELECT u.primary_bucket AS bucket, s.et_date AS d, s.slot_minute AS slot,
               avg(ret) AS ret, avg(abs(ret)) AS aret, avg(vshare) AS vshare, count(*) AS n_syms
        FROM s JOIN universe u ON u.ticker = s.symbol WHERE u.primary_bucket IS NOT NULL
        GROUP BY 1, 2, 3
    """).df()
    mk = r.groupby(["d", "slot"]).agg(mkt=("ret", "mean"), maret=("aret", "mean")).reset_index()
    r = r.merge(mk, on=["d", "slot"])
    r["ex"] = r["ret"] - r["mkt"]
    r["rel_vol"] = r["aret"] / r["maret"]
    r.attrs.update(n_days=int(r["d"].nunique()), exclude_half_days=exclude_half_days)
    return r


def slot_report(panel: pd.DataFrame) -> pd.DataFrame:
    """One table per (bucket, slot): raw and excess bps, beta-adjusted alpha with BH q, rel. volatility, volume share."""
    ab = alpha_beta(panel, "ret", "mkt", ("bucket", "slot"))
    g = panel.groupby(["bucket", "slot"])
    base = pd.DataFrame({
        "raw_bps": g["ret"].mean() * 1e4, "t_raw": g["ret"].apply(tstat),
        "excess_bps": g["ex"].mean() * 1e4, "t_excess": g["ex"].apply(tstat),
        "rel_vol": g["rel_vol"].mean(), "vol_pct": g["vshare"].mean() * 100,
    }).reset_index()
    out = base.merge(ab.drop(columns=["p"]), on=["bucket", "slot"], how="left")
    out["time"] = out["slot"].map(slot_label)
    return out.sort_values(["bucket", "slot"]).reset_index(drop=True)


def describe_panel(panel: pd.DataFrame) -> str:
    """One line stating what the numbers rest on; print it above any table you report."""
    a = panel.attrs
    return (f"{a.get('n_days', panel['d'].nunique())} days, {panel['bucket'].nunique()} buckets, "
            f"avg {panel['n_syms'].mean():.0f} symbols per cell, half-days "
            f"{'excluded' if a.get('exclude_half_days') else 'INCLUDED'}")
