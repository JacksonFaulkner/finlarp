"""Dossier tab: Ownership. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Institutions (13F-HR): QoQ holder changes with the effective-filing and typo rules of sec_13f.summary,
the full change list, top-10 / top-20 share and HHI, a constant-panel holder trend, put/call exposure
(the holdings parquet pc column, which holdings_sql drops) and amendment flags from the filings table.

Insiders (Form 3/4/5): open-market net $ over 30/90/180 days, 2+ buyer clusters, 10b5-1 share of sells,
derivative grants/exercises, sale size vs position, role-weighted buys and filing lag.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta
from statistics import median

from derive.dossier import F13_URL, INSIDER_URL, Filings, _is_new, _money, _pct, archive, derived, src
from sources import sec_13f, sec_insiders

MIN_FILINGS = 1000  # a quarter with fewer 13F-HR filings is a partial load (the 2024 windows)
N_PANEL = 6  # quarters in the constant-panel trend
WINDOWS = (30, 90, 180)
ROLE_WEIGHT = {"C-suite": 3, "officer": 2, "director": 1, "other": 1}
CLUSTER_MIN = 25_000  # sec_insiders.cluster_buys default: drops token / ESPP-style buys
_CHIEF = re.compile(r"\b(CEO|CFO|COO|CTO|CRO|CMO|CLO|CAO|CIO|CISO|CHIEF)\b", re.I)
_PRES = re.compile(r"\bPRESIDENT\b", re.I)
_VP = re.compile(r"\b(VICE|VP|SVP|EVP)\b", re.I)


# ---- pure helpers ----------------------------------------------------------

def change_kind(a: float | None, b: float | None) -> str | None:
    """a, b = shares held in the prior / current quarter; None = no 13F line filed."""
    if a is None and b is None:
        return None
    if a is None:
        return "new"
    if b is None:
        return "exited"
    if b == a:
        return "flat"
    return "added" if b > a else "trimmed"


def concentration(shares: list[float | None]) -> dict | None:
    """Top-10 and top-20 share (%) and HHI (sum of squared % shares, 0-10,000) of holder positions."""
    s = sorted((x for x in shares if x), reverse=True)
    tot = sum(s)
    if not tot:
        return None
    return {"top10": sum(s[:10]) / tot * 100, "top20": sum(s[:20]) / tot * 100,
            "hhi": sum((x / tot * 100) ** 2 for x in s)}


def amend_label(subtype: str | None, amend_type: str | None) -> str | None:
    if amend_type == "RESTATEMENT":
        return "restatement"
    if amend_type == "NEW HOLDINGS":
        return "new-holdings amendment"
    if subtype == "13F-HR/A":
        return "13F-HR/A"
    return None


def sale_pct(shares, after) -> float | None:
    """Shares sold as % of the line's pre-sale position (shares owned after the sale + shares sold)."""
    if not shares or after is None:
        return None
    pre = after + shares
    return shares / pre * 100 if pre > 0 else None


def role_tier(title: str | None, relationship: str | None) -> str:
    t, rel = title or "", relationship or ""
    if _CHIEF.search(t) or (_PRES.search(t) and not _VP.search(t)):
        return "C-suite"
    if "Officer" in rel or (t and "Director" not in rel):
        return "officer"
    if "Director" in rel:
        return "director"
    return "other"


def role_weighted(buys: list[tuple[str, float]]) -> tuple[dict[str, float], float]:
    """($ by role tier, Σ $ x role weight)."""
    by = {k: 0.0 for k in ROLE_WEIGHT}
    for tier, v in buys:
        by[tier] += v
    return by, sum(ROLE_WEIGHT[k] * v for k, v in by.items())


def _signed(v: float) -> str:
    return ("-" if v < 0 else "") + _money(abs(v))


def filing_lag_days(filed, trans) -> int | None:
    return (filed - trans).days if filed and trans else None


def window_flow(tx: list[dict], since: date) -> tuple[float, float]:
    """(buys $, sells $) of open-market rows with trans_date >= since."""
    b = sum((x["value"] or 0) for x in tx if x["code"] == "P" and x["trans_date"] >= since)
    s = sum((x["value"] or 0) for x in tx if x["code"] == "S" and x["trans_date"] >= since)
    return b, s


def in_window(rows: list[dict], start: date, days: int = 30) -> list[dict]:
    return [x for x in rows if start <= x["trans_date"] <= start + timedelta(days=days)]


def planned_share(sells: list[dict]) -> tuple[float | None, float | None]:
    """(% of sell $ and % of sell count that carry a 10b5-1 plan flag)."""
    if not sells:
        return None, None
    tot = sum(x["value"] or 0 for x in sells)
    planned = [x for x in sells if x.get("is_10b5_1")]
    val = sum(x["value"] or 0 for x in planned) / tot * 100 if tot else None
    return val, len(planned) / len(sells) * 100


# ---- 13F -------------------------------------------------------------------

def _load(con, cusips: list[str], fdir, hdir) -> None:
    """Temp tables. own_h: effective holdings per (cik, period, cusip, pc), NULL pc = equity.
    own_eq: equity rows. own_clean: equity minus sec_13f.SUSPECT_MULTIPLE typo rows.
    Effective-filing rules are those of sec_13f.holdings_sql, which cannot keep pc."""
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE own_h AS
        WITH f AS (SELECT DISTINCT * FROM read_parquet('{fdir}/*.parquet') WHERE subtype IN ('13F-HR', '13F-HR/A')),
        base AS (SELECT * FROM f WHERE amend_type IS NULL OR amend_type = 'RESTATEMENT'
                 QUALIFY row_number() OVER (PARTITION BY cik, period ORDER BY filed DESC, acc DESC) = 1),
        adds AS (SELECT f.* FROM f JOIN base b USING (cik, period)
                 WHERE f.amend_type = 'NEW HOLDINGS' AND f.filed >= b.filed),
        eff AS (SELECT acc, cik, mgr, period FROM base UNION ALL SELECT acc, cik, mgr, period FROM adds)
        SELECT e.cik, any_value(e.mgr) mgr, e.period, h.cusip, h.pc, sum(h.sh) sh, sum(h.val) val,
               min(e.acc) acc
        FROM eff e JOIN read_parquet('{hdir}/*.parquet') h USING (acc)
        WHERE list_contains($c, h.cusip)
        GROUP BY e.cik, e.period, h.cusip, h.pc
    """, {"c": cusips})
    con.execute("CREATE OR REPLACE TEMP TABLE own_eq AS SELECT * FROM own_h WHERE pc IS NULL")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE own_clean AS
        WITH ranked AS (
            SELECT *, max(sh) FILTER (WHERE rn = 2) OVER (PARTITION BY cusip, period) runner_up
            FROM (SELECT *, row_number() OVER (PARTITION BY cusip, period ORDER BY sh DESC) rn FROM own_eq)
        )
        SELECT * EXCLUDE (rn, runner_up) FROM ranked
        WHERE NOT coalesce(rn = 1 AND sh > {sec_13f.SUSPECT_MULTIPLE} * runner_up, false)
    """)


def _panel(con, fdir, periods: list) -> list[int]:
    """CIKs that filed a 13F-HR for every period in `periods`."""
    return [r[0] for r in con.execute(f"""
        SELECT cik FROM (SELECT DISTINCT cik, period FROM read_parquet('{fdir}/*.parquet')
                         WHERE subtype IN ('13F-HR', '13F-HR/A') AND list_contains($p, period))
        GROUP BY cik HAVING count(*) = $n""", {"p": periods, "n": len(periods)}).fetchall()]


def _mover(r: tuple, cur, prev, kind: str | None = None, flag: str = "") -> dict:
    cik, mgr, a, b, acc_a, acc_b = r
    acc = acc_b or acc_a
    cells = [mgr or str(cik), "new" if a is None else f"{a / 1e6:,.2f}M",
             "exited" if b is None else f"{b / 1e6:,.2f}M", f"{((b or 0) - (a or 0)) / 1e6:+,.2f}M"]
    if kind is not None:
        cells += [kind, flag]
    return {"cells": cells, "src": src(f"13F-HR {cur if acc_b else prev} · {mgr or cik}", archive(cik, acc))}


def _trend_formula(t: str, p, n_panel: int, k: int) -> str:
    return (f"managers holding {t} equity in {p}. Panel = {n_panel} managers that filed a 13F-HR in all {k} quarters "
            "shown (a fixed set). The all-manager count also rises with 13F coverage (new filers), which is not real "
            "ownership change for this stock; only the panel columns are like-for-like.")


def _holder_blocks(t: str, con, F: Filings) -> list[dict]:
    cmap = sec_13f.DATA_DIR / "cusip_map.parquet"
    if not cmap.exists() or not any((sec_13f.DATA_DIR / "holdings").glob("*.parquet")):
        return []
    cusips = [r[0] for r in con.execute(f"SELECT cusip FROM '{cmap}' WHERE ticker = ? AND cusip IS NOT NULL",
                                        [t]).fetchall()]
    if not cusips:
        return []
    fdir = sec_13f.DATA_DIR / "filings"
    periods = [r[0] for r in con.execute(f"""
        SELECT period FROM read_parquet('{fdir}/*.parquet') WHERE subtype IN ('13F-HR', '13F-HR/A')
        GROUP BY period HAVING count(*) >= {MIN_FILINGS} ORDER BY period DESC LIMIT {N_PANEL}""").fetchall()]
    if len(periods) < 2:
        return []
    cur, prev = periods[0], periods[1]
    _load(con, cusips, fdir, sec_13f.DATA_DIR / "holdings")
    if not con.execute("SELECT count(*) FROM own_clean WHERE period = $p", {"p": cur}).fetchone()[0]:
        return []

    ds_cur = src(f"SEC Form 13F data sets ({cur})", F13_URL)
    ds = [src(f"SEC Form 13F data sets ({p})", F13_URL) for p in (prev, cur)]
    method = (f"13F-HR filings for periods {prev} and {cur}; only managers that filed both periods; "
              f"CUSIPs {', '.join(cusips)}; top holder dropped if >{sec_13f.SUSPECT_MULTIPLE}× runner-up (typo filter)")

    # Two-quarter panel: same managers and counts as sec_13f.summary, so the existing kv numbers hold.
    pair = _panel(con, fdir, [prev, cur]) or [-1]  # -1 is never a CIK; keeps the list parameter non-empty
    rows = con.execute("""
        SELECT cik, any_value(mgr), sum(sh) FILTER (WHERE period = $prev), sum(sh) FILTER (WHERE period = $cur),
               min(acc) FILTER (WHERE period = $prev), min(acc) FILTER (WHERE period = $cur)
        FROM own_clean WHERE period IN ($prev, $cur) AND list_contains($pair, cik) GROUP BY cik
    """, {"prev": prev, "cur": cur, "pair": pair}).fetchall()
    kinds = {r[0]: change_kind(r[2], r[3]) for r in rows}
    cnt = Counter(kinds.values())
    holders_prev = sum(r[2] is not None for r in rows)
    holders = sum(r[3] is not None for r in rows)
    sh_prev = sum(r[2] or 0 for r in rows)
    sh_cur = sum(r[3] or 0 for r in rows)

    # Amendment flags per (cik, period) from the filings table.
    flags: dict[tuple, set[str]] = {}
    for cik, p, sub, amd in con.execute(f"""
            SELECT cik, period, subtype, amend_type FROM read_parquet('{fdir}/*.parquet')
            WHERE subtype IN ('13F-HR', '13F-HR/A') AND list_contains($p, period)""", {"p": [prev, cur]}).fetchall():
        if lab := amend_label(sub, amd):
            flags.setdefault((cik, p), set()).add(lab)

    def flag_txt(cik) -> str:
        return ", ".join(sorted(flags.get((cik, cur), set()) or flags.get((cik, prev), set())))

    cur_rows = con.execute("SELECT cik, sum(sh) FROM own_clean WHERE period = $p GROUP BY cik",
                           {"p": cur}).fetchall()
    cur_holders = [c for c, _ in cur_rows]
    conc = concentration([s for _, s in cur_rows])
    amended = [c for c in cur_holders if flags.get((c, cur))]
    n_rest = sum("restatement" in flags.get((c, cur), ()) for c in cur_holders)
    n_newh = sum("new-holdings amendment" in flags.get((c, cur), ()) for c in cur_holders)

    kv = [
        {"label": "Holders", "value": f"{holders_prev:,} → {holders:,} ({_pct((holders / holders_prev - 1) * 100 if holders_prev else None)})",
         "src": derived("count of managers holding", method, ds)},
        {"label": "New / exited positions", "value": f"{cnt['new']:,} / {cnt['exited']:,}",
         "src": derived("new = held now not before", method, ds)},
        {"label": "Shares held", "value": f"{sh_prev / 1e6:,.1f}M → {sh_cur / 1e6:,.1f}M ({_pct((sh_cur / sh_prev - 1) * 100 if sh_prev else None)})",
         "src": derived("sum of reported shares", method, ds)},
        {"label": f"Holders with an amended 13F ({cur})",
         "value": f"{len(amended):,} of {len(cur_holders):,} · {n_rest} restatement · {n_newh} new holdings",
         "src": derived("holders with a 13F-HR/A in the current period", "13F-HR/A filings (restatement, new-holdings or untyped) "
                        "by holders of this stock ÷ all holders, current period", ds)},
    ]
    if conc:
        conc_formula = "share of 13F-reported shares, current period; Σ of the largest managers' shares ÷ Σ all reported (typo rows excluded)"
        kv.append({"label": "Top 10 / top 20 share", "value": f"{_pct(conc['top10'], signed=False)} / {_pct(conc['top20'], signed=False)}",
                   "src": derived("share of 13F-reported shares", conc_formula, [ds_cur])})
        kv.append({"label": "HHI (13F shares)", "value": f"{conc['hhi']:,.0f}",
                   "src": derived("Herfindahl index of 13F shares", "Σ (manager share of 13F-reported shares, in %)², 0–10,000",
                                  [ds_cur])})

    # Holder count on a constant panel, so coverage growth is separated from ownership change.
    panel = _panel(con, fdir, periods)
    trend_rows = []
    for p, n_all, n_pan, sh_pan in con.execute("""
            SELECT period, count(DISTINCT cik), count(DISTINCT cik) FILTER (WHERE list_contains($panel, cik)),
                   sum(sh) FILTER (WHERE list_contains($panel, cik))
            FROM own_clean WHERE list_contains($ps, period) GROUP BY period ORDER BY period DESC""",
            {"panel": panel or [-1], "ps": periods}).fetchall():
        trend_rows.append({"cells": [str(p), f"{n_all:,}", f"{n_pan:,}", f"{(sh_pan or 0) / 1e6:,.2f}M"],
                           "src": derived(f"SEC Form 13F data sets ({p})", _trend_formula(t, p, len(panel), len(periods)),
                                          [src(f"SEC Form 13F data sets ({p})", F13_URL)])})

    # Put / call exposure per manager (holdings parquet pc column).
    eq_cur = dict(cur_rows)
    pc_raw = con.execute("""
        SELECT cik, any_value(mgr), sum(sh) FILTER (WHERE pc = 'P'), sum(sh) FILTER (WHERE pc = 'C'), min(acc)
        FROM own_h WHERE period = $p AND pc IS NOT NULL GROUP BY cik""", {"p": cur}).fetchall()
    pc_raw.sort(key=lambda r: (r[2] or 0) + (r[3] or 0), reverse=True)
    pc_rows = []
    for cik, mgr, puts, calls, acc in pc_raw:
        puts, calls = puts or 0, calls or 0
        eq = eq_cur.get(cik)
        pc_rows.append({"cells": [mgr or str(cik), f"{puts / 1e6:,.2f}M", f"{calls / 1e6:,.2f}M",
                                  _pct((puts + calls) / eq * 100 if eq else None, signed=False)],
                        "src": src(f"13F-HR {cur} · {mgr or cik}", archive(cik, acc))})
    if pc_raw:
        tp = sum(r[2] or 0 for r in pc_raw)
        tc = sum(r[3] or 0 for r in pc_raw)
        kv.append({"label": f"Put / call shares ({cur})",
                   "value": f"puts {tp / 1e6:,.2f}M · calls {tc / 1e6:,.2f}M across {len(pc_raw)} managers",
                   "src": derived("SEC Form 13F data sets", "Σ shares where the 13F PUTCALL column is Put / Call "
                                  "(holdings parquet pc column; holdings_sql omits it)", [ds_cur])})

    moves = sorted(rows, key=lambda r: (r[3] or 0) - (r[2] or 0))
    top_in = [_mover(r, cur, prev) for r in moves[::-1][:8] if (r[3] or 0) > (r[2] or 0)]
    top_out = [_mover(r, cur, prev) for r in moves[:8] if (r[3] or 0) < (r[2] or 0)]
    full = [_mover(r, cur, prev, kind=kinds[r[0]], flag=flag_txt(r[0])) for r in moves[::-1]
            if kinds[r[0]] in ("new", "added", "trimmed", "exited")]
    cols = ["manager", str(prev), str(cur), "Δ shares"]
    out = [
        {"type": "kv", "rows": kv},
        {"type": "table", "title": "Holder count trend (constant panel vs all managers)",
         "cols": ["quarter end", "managers holding", f"panel ({len(panel)} managers, all {len(periods)} quarters)",
                  "panel shares"], "rows": trend_rows},
        {"type": "table", "title": "Biggest adds", "cols": cols, "rows": top_in},
        {"type": "table", "title": "Biggest cuts", "cols": cols, "rows": top_out},
        {"type": "table", "title": f"All QoQ changes, {len(full)} managers (new, added, trimmed, exited)",
         "cols": cols + ["change", "13F flag"], "rows": full},
    ]
    if pc_rows:
        out.append({"type": "table", "title": f"Put / call exposure per manager ({cur})",
                    "cols": ["manager", "puts", "calls", "options ÷ equity"], "rows": pc_rows})
    return out


# ---- insiders --------------------------------------------------------------

def _f4(F: Filings, accn: str) -> str | None:
    return archive(F.cik, accn) if F.cik else None


def _insider_blocks(t: str, con, F: Filings, today: date) -> list[dict]:
    if not sec_insiders.loaded_quarters():
        return []
    since = today - timedelta(days=365)
    tx = sec_insiders.open_market(t, since)  # non-derivative P and S
    ins_ds = src(f"SEC insider transactions data sets, {t}, last 365 days", INSIDER_URL)

    def fsrc(x: dict) -> dict:
        return src(f"Form {x['form']} filed {x['filed']} · {x['owner_name']}", _f4(F, x["accn"]))

    def uniq(rows: list[dict]) -> list[dict]:
        seen: set = set()
        out = []
        for x in rows:
            if x["accn"] not in seen:
                seen.add(x["accn"])
                out.append(fsrc(x))
        return out

    buys = [x for x in tx if x["code"] == "P"]
    sells = [x for x in tx if x["code"] == "S"]
    disc = [x for x in sells if not x.get("is_10b5_1")]
    kv = [
        {"label": "Open-market buys (365d)", "value": f"{len(buys)} · {_money(sum(x['value'] or 0 for x in buys))}",
         "src": derived("sum of Form 4 code P", "Σ value of non-derivative code-P transactions", uniq(buys), ins_ds)},
        {"label": "Sales (365d)", "value": f"{len(sells)} · {_money(sum(x['value'] or 0 for x in sells))}",
         "src": derived("sum of Form 4 code S", "Σ value of non-derivative code-S transactions", uniq(sells), ins_ds)},
        {"label": "  discretionary (not 10b5-1)", "value": _money(sum(x["value"] or 0 for x in disc)),
         "src": derived("code S without a 10b5-1 plan flag", "Σ value where is_10b5_1 = false", uniq(disc), ins_ds)},
    ]
    for n in WINDOWS:
        since_n = today - timedelta(days=n)
        b, s = window_flow(tx, since_n)
        kv.append({"label": f"Net open-market {n}d", "value": f"{_signed(b - s)} (buys {_money(b)} · sells {_money(s)})",
                   "src": derived(f"buys − sells, last {n} days",
                                  f"Σ value code P − Σ value code S, trans_date ≥ {since_n}",
                                  uniq([x for x in tx if x["trans_date"] >= since_n]), ins_ds)})
    val_pct, cnt_pct = planned_share(sells)
    kv.append({"label": "10b5-1 share of sells (365d)",
               "value": f"{_pct(val_pct, signed=False)} by value · {_pct(cnt_pct, signed=False)} by count",
               "src": derived("sells flagged 10b5-1 ÷ all sells", "Σ value (and count) where is_10b5_1 ÷ all code-S",
                              uniq(sells), ins_ds)})
    pcts = [(p, x) for x in sells if (p := sale_pct(x["shares"], x["shares_owned_after"])) is not None]
    big = max(pcts, key=lambda px: px[0], default=None)
    if big:
        kv.append({"label": "Largest sale as % of position (365d)",
                   "value": f"{big[0]:.2f}% · {big[1]['owner_name']} {big[1]['trans_date']}", "src": fsrc(big[1])})
    else:
        kv.append({"label": "Largest sale as % of position (365d)", "value": "—",
                   "src": derived("no sale with a position", "shares ÷ (shares owned after + shares)", [], ins_ds)})
    by_tier, weighted = role_weighted([(role_tier(x.get("officer_title"), x.get("relationship")), x["value"] or 0)
                                       for x in buys])
    kv.append({"label": "Buys by role (365d)",
               "value": " · ".join(f"{k} {_money(v)}" for k, v in by_tier.items() if v) or "—",
               "src": derived("open-market buys grouped by role", "role from officer_title, else relationship",
                              uniq(buys), ins_ds)})
    kv.append({"label": "Role-weighted buys (365d)", "value": _money(weighted),
               "src": derived("Σ buy value × role weight",
                              f"weights {ROLE_WEIGHT} (judgment, not a standard); C-suite from title", uniq(buys), ins_ds)})
    lags = [g for x in tx if (g := filing_lag_days(x["filed"], x["trans_date"])) is not None]
    kv.append({"label": "Filing lag, median / max (365d)",
               "value": f"{median(lags):.0f} / {max(lags)} days" if lags else "—",
               "src": derived("filed − transaction date", "calendar days, median and max over open-market rows",
                              uniq(tx), ins_ds)})
    cl = next((r for r in sec_insiders.cluster_buys(since=since) if r["ticker"] == t), None)
    if cl:
        kv.append({"label": "Insider cluster (2+ buyers, 30d)",
                   "value": f"{cl['insiders']} insiders · {_money(cl['value'])} · {cl['start']} to {cl['end']}: {cl['names']}",
                   "src": derived("distinct insiders each buying ≥ $25k of common stock (code P) within 30 days",
                                  "best window (most insiders, then $); Σ value of buys inside it",
                                  uniq(in_window(buys, cl["start"])), ins_ds)})
    else:
        kv.append({"label": "Insider cluster (2+ buyers, 30d)", "value": "none in 365d",
                   "src": derived("no 30-day window with 2+ insiders buying", f"min buy ${CLUSTER_MIN:,} per insider",
                                  [], ins_ds)})

    rows = [{"cells": [str(x["trans_date"]), x["owner_name"], x.get("officer_title") or x.get("relationship") or "",
                       "BUY" if x["code"] == "P" else "sell", f"{x['shares'] or 0:,.0f}",
                       f"${x['price']:,.2f}" if x.get("price") is not None else "—",
                       _money(x["value"]), "10b5-1" if x.get("is_10b5_1") else "",
                       (f"{p:.2f}%" if x["code"] == "S" and (p := sale_pct(x["shares"], x["shares_owned_after"])) is not None else "")],
             "new": _is_new(x["filed"]), "src": fsrc(x)} for x in tx[:25]]

    cur = con.execute(f"""
        SELECT * FROM {sec_insiders.tx_sql()}
        WHERE ticker = ? AND kind = 'deriv' AND code IN ('A', 'M') AND trans_date >= ?
        ORDER BY trans_date DESC, owner_name""", [t, since])
    cols = [d[0] for d in cur.description]
    drv = [dict(zip(cols, r)) for r in cur.fetchall()]
    drows = [{"cells": [str(x["trans_date"]), x["owner_name"], x.get("officer_title") or x.get("relationship") or "",
                        "grant" if x["code"] == "A" else "exercise", x.get("security_title") or "",
                        f"{x['shares'] or 0:,.0f}", f"${x['price']:,.2f}" if x.get("price") else "—",
                        "10b5-1" if x.get("is_10b5_1") else ""],
              "new": _is_new(x["filed"]), "src": fsrc(x)} for x in drv[:50]]
    return [
        {"type": "kv", "rows": kv},
        {"type": "table", "title": "Open-market transactions (bulk data lags 0–3 months)",
         "cols": ["date", "who", "role", "", "shares", "price", "value", "plan", "% of pos"], "rows": rows},
        {"type": "table", "title": "Derivative grants (A) and exercises (M), 365d, not open market",
         "cols": ["date", "who", "role", "", "security", "shares", "price", "plan"], "rows": drows},
    ]


def section(t: str, con, F: Filings, prof: dict | None) -> dict | None:
    today = date.today()
    blocks = _holder_blocks(t, con, F) + _insider_blocks(t, con, F, today)
    if not blocks:
        return None
    return {"id": "ownership", "title": "Ownership", "blocks": blocks}
