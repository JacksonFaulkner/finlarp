"""Dossier tab: Peers. section(t, con, F, prof) -> {"id", "title", "blocks"} | None.

Everything is read from disk, no live calls: the AI universe (ai_universe + ai_universe_category in
finlarp.duckdb, eligible names only, the same set as the `universe` view), Yahoo profiles (industry,
market cap in the profile currency) and the SEC XBRL facts for revenue, gross profit, operating income
and net income. Market caps are compared only across USD names; other currencies are shown as-is.
"""
from __future__ import annotations

import functools
import statistics
from datetime import date
from urllib.parse import quote

import duckdb

from core import db
from derive.dossier import D, _money, _pct, archive, derived, src
from sources import sec_financials as sf

ID, TITLE = "peers", "Peers"
PROFILES = D / "profiles" / "profiles.parquet"
TABLE_CAP = 25
MAX_INPUTS = 10  # rank formulas cite at most this many names that sit above the subject
EPS = 1e-9


# ---- sources ---------------------------------------------------------------

def _profile_url(t: str) -> str:
    return f"https://finance.yahoo.com/quote/{quote(t)}/profile"


def _psrc(t: str) -> dict:
    return src(f"Yahoo Finance profile · {t} · market cap, industry", _profile_url(t))


def _usrc(t: str, u: dict) -> dict:
    return src(f"AI-universe classification · {t} · reviewed {u.get('reviewed') or 'n/a'}", u["url"])


# ---- data ------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _universe() -> tuple[dict, dict, dict]:
    """(ticker -> {name, url, reviewed, primary: {bucket: w}, subs: {sub: w}}, sub labels, bucket labels).
    Eligible names only. Empty dicts when the DB is missing or cannot be opened read-only."""
    if not db.DB_PATH.exists():
        return {}, {}, {}
    try:
        con = duckdb.connect(str(db.DB_PATH), read_only=True)
    except duckdb.Error:
        return {}, {}, {}
    try:
        heads = con.execute("SELECT ticker, name, source_url, reviewed_on FROM ai_universe "
                            "WHERE eligible IS DISTINCT FROM false").fetchall()
        cats = con.execute("SELECT c.ticker, c.level, c.category, c.weight FROM ai_universe_category c "
                           "JOIN ai_universe u USING (ticker) WHERE u.eligible IS DISTINCT FROM false").fetchall()
        tax = con.execute("SELECT sub_category, coalesce(label, sub_category), primary_category, "
                          "coalesce(primary_label, primary_category) FROM ai_taxonomy").fetchall()
    except duckdb.Error:
        return {}, {}, {}
    finally:
        con.close()
    out = {t: {"name": n, "url": u or _profile_url(t), "reviewed": rv, "primary": {}, "subs": {}}
           for t, n, u, rv in heads}
    for t, level, cat, w in cats:
        if t in out:
            out[t]["primary" if level == "primary" else "subs"][cat] = w
    sub_lbl = {s: lbl for s, lbl, _, _ in tax}
    bucket_lbl = {p: plbl for _, _, p, plbl in tax}
    return out, sub_lbl, bucket_lbl


def _profiles(con) -> dict:
    if not PROFILES.exists():
        return {}
    cols = ["ticker", "long_name", "short_name", "industry", "market_cap", "currency"]
    rows = con.execute(f"SELECT {', '.join(cols)} FROM '{PROFILES}'").fetchall()
    return {r[0]: dict(zip(cols, r)) for r in rows}


def _accn_ciks(t: str) -> dict:
    path = sf.FACTS_DIR / f"{t.upper().replace('/', '_')}.parquet"
    if not path.exists():
        return {}
    with duckdb.connect() as c:
        return dict(c.execute(f"SELECT accn, any_value(cik) FROM read_parquet('{path}') GROUP BY accn").fetchall())


@functools.lru_cache(maxsize=None)
def _fin(t: str) -> dict | None:
    """Revenue for the latest fiscal year and the one before, plus gross profit, operating income and
    net income for the same year. Each value comes with the filing it was read from; a value whose
    filing cannot be located is dropped. None when there is no revenue on disk."""
    rev = sf.annual_series(t, "revenue")
    if not rev:
        return None
    cur = rev[-1]
    prev = rev[-2] if len(rev) > 1 else None
    if prev is not None and not (330 <= (date.fromisoformat(cur["end"]) - date.fromisoformat(prev["end"])).days <= 400
                                 and prev["unit"] == cur["unit"]):
        prev = None
    ciks = _accn_ciks(t)

    def fact(r: dict | None, what: str) -> tuple[float | None, dict | None]:
        cik = ciks.get(r.get("accn")) if r else None
        if cik is None:
            return None, None
        return r["val"], src(f"{what} FY{r['fy']} · filed {r.get('filed') or 'n/a'} · {r['accn']}",
                             archive(cik, r["accn"]))

    def pick(metric: str) -> dict | None:
        return next((r for r in sf.annual_series(t, metric)
                     if r["end"] == cur["end"] and r["unit"] == cur["unit"]), None)

    rev_v, rev_s = fact(cur, "Revenue")
    if rev_v is None:
        return None
    prev_v, prev_s = fact(prev, "Revenue") if prev else (None, None)
    gross_v, gross_s = fact(pick("gross_profit"), "Gross profit")
    op_v, op_s = fact(pick("operating_income"), "Operating income")
    ni_v, ni_s = fact(pick("net_income"), "Net income")
    return {"unit": cur["unit"], "fy": cur["fy"], "prev_fy": prev["fy"] if prev else None,
            "rev": rev_v, "rev_src": rev_s, "prev_rev": prev_v, "prev_src": prev_s,
            "gross": gross_v, "gross_src": gross_s, "op": op_v, "op_src": op_s, "ni": ni_v, "ni_src": ni_s}


# ---- pure logic ------------------------------------------------------------

def _dominant(rec: dict) -> tuple[str, float] | None:
    """(bucket, weight) with the largest primary weight, ties to the alphabetically first bucket."""
    prim = rec.get("primary") or {}
    if not prim:
        return None
    cat = max(sorted(prim), key=prim.get)
    return cat, prim[cat]


def _cap(v: float | None, ccy: str | None) -> str:
    """USD as $, other currencies with their code so no local number reads as dollars."""
    if v is None:
        return "—"
    return _money(v) if ccy in (None, "USD") else f"{ccy} {_money(v).lstrip('$')}"


def _rec(x: str, p: dict, bucket: str | None, f: dict | None) -> dict:
    """One name's market cap, currency and fundamentals ratios. Valuation only for USD market caps
    over a USD revenue / net income figure, so no currency mixing."""
    cap, ccy = p.get("market_cap"), p.get("currency")
    usd = ccy == "USD"
    rec = {"t": x, "name": p.get("long_name") or p.get("short_name") or x, "cap": cap, "ccy": ccy, "usd": usd,
           "bucket": bucket, "fin": f, "growth": None, "gm": None, "om": None, "ps": None, "pe": None}
    if not f:
        return rec
    rev = f["rev"]
    if f["prev_rev"]:
        rec["growth"] = (rev / f["prev_rev"] - 1) * 100
    if rev:
        rec["gm"] = f["gross"] / rev * 100 if f["gross"] is not None else None
        rec["om"] = f["op"] / rev * 100 if f["op"] is not None else None
    if usd and f["unit"] == "USD" and cap and rev and rev > 0:
        rec["ps"] = cap / rev
    if usd and f["unit"] == "USD" and cap and f["ni"] is not None and f["ni"] > 0:
        rec["pe"] = cap / f["ni"]
    return rec


def _peer_row(r: dict, bucket_lbl: dict) -> dict:
    f = r["fin"]
    inputs = [_psrc(r["t"])] + ([f["rev_src"], f["op_src"]] if f else [])
    inputs = [s for s in inputs if s]
    formula = "market cap: Yahoo profile"
    if f:
        formula += f"; growth = FY{f['fy']} revenue / FY{f['prev_fy']} revenue − 1; op margin = FY{f['fy']} op income / revenue"
    return {"cells": [r["t"], r["name"], bucket_lbl.get(r["bucket"], r["bucket"]) if r["bucket"] else "—",
                      _cap(r["cap"], r["ccy"]), _pct(r["growth"]), _pct(r["om"], signed=False)],
            "src": derived(f"{r['t']} · peer row", formula, inputs)}


# ---- blocks ----------------------------------------------------------------

def _bucket_blocks(t: str, me: dict, U: dict, P: dict, sub_lbl: dict, bucket_lbl: dict) -> list[dict]:
    d = _dominant(me)
    if not d:
        return []
    cat, w = d
    usrc = _usrc(t, me)
    kv = [{"label": "Primary bucket", "value": f"{bucket_lbl.get(cat, cat)} · {cat}", "src": usrc},
          {"label": "Primary weight", "value": f"{w * 100:.0f}%", "src": usrc}]

    members = [(x, _dominant(rec)[1]) for x, rec in U.items() if _dominant(rec) and _dominant(rec)[0] == cat]
    above_w = sorted([m for m in members if m[1] > w + EPS], key=lambda m: -m[1])
    kv.append({"label": "Rank by bucket weight", "value": f"{1 + len(above_w)} of {len(members)}",
               "src": derived("rank by primary weight within bucket",
                              f"1 + #names in {cat} with primary weight > {w:.2f}; {len(members)} names in bucket",
                              [usrc] + [_usrc(x, U[x]) for x, _ in above_w[:MAX_INPUTS]])})

    me_p = P.get(t) or {}
    cap = me_p.get("market_cap")
    if cap and me_p.get("currency") == "USD":
        caps = [(x, P[x]["market_cap"]) for x, _ in members
                if x in P and P[x].get("currency") == "USD" and P[x].get("market_cap")]
        above_c = sorted([c for c in caps if c[1] > cap], key=lambda c: -c[1])
        kv.append({"label": "Rank by bucket market cap (USD)", "value": f"{1 + len(above_c)} of {len(caps)}",
                   "src": derived("rank by market cap within bucket, USD names only",
                                  f"1 + #USD names in {cat} with market cap > {_money(cap)}; {len(caps)} USD names",
                                  [_psrc(t)] + [_psrc(x) for x, _ in above_c[:MAX_INPUTS]])})

    blocks = [{"type": "kv", "rows": kv}]
    if me.get("subs"):
        items = [{"label": sub_lbl.get(s, s), "value": round(v * 100, 1), "src": usrc}
                 for s, v in sorted(me["subs"].items(), key=lambda kv_: -kv_[1])]
        blocks.append({"type": "bars", "title": "Sub-bucket exposure", "unit": "%", "items": items})
    return blocks


def _industry_blocks(t: str, ind: str, U: dict, P: dict, bucket_lbl: dict) -> list[dict]:
    names = [x for x, p in P.items() if p.get("industry") == ind and (x in U or x == t)]
    recs = {x: _rec(x, P[x], _dominant(U[x])[0] if x in U and _dominant(U[x]) else None, _fin(x)) for x in names}
    me = recs[t]
    peers = [r for x, r in recs.items() if x != t]
    usd_caps = sorted([r for r in recs.values() if r["usd"] and r["cap"]], key=lambda r: -r["cap"])
    n_usd = len(usd_caps)

    kv = [{"label": "Industry (Yahoo)", "value": ind, "src": _psrc(t)},
          {"label": "Names in industry", "value": f"{len(recs)} · {n_usd} with a USD market cap",
           "src": derived("count of eligible names with this industry", f"count(ticker) where industry = '{ind}'",
                          [_psrc(t)])}]
    if me["usd"] and me["cap"]:
        above = [r for r in usd_caps if r["cap"] > me["cap"]]
        kv.append({"label": "Rank by market cap (USD)", "value": f"{1 + len(above)} of {n_usd}",
                   "src": derived("rank by market cap, USD names", f"1 + #USD names in industry with market cap > "
                                  f"{_money(me['cap'])}; {n_usd} USD names", [_psrc(t)] +
                                  [_psrc(r["t"]) for r in above[:MAX_INPUTS]])})
    blocks = [{"type": "kv", "rows": kv}]

    order = sorted(peers, key=lambda r: (0 if r["usd"] and r["cap"] else 1 if r["cap"] else 2, -(r["cap"] or 0)))
    if order:
        blocks.append({"type": "table",
                       "title": f"Same-industry peers · top {TABLE_CAP} by market cap (non-USD after, in local currency)",
                       "cols": ["ticker", "name", "bucket", "market cap", "revenue growth", "op margin"],
                       "rows": [_peer_row(r, bucket_lbl) for r in order[:TABLE_CAP]]})

    def inputs(rs: list[dict], pick) -> list[dict]:
        return [s for r in rs for s in pick(r) if s]

    avg_rs = [r for r in peers if r["usd"] and r["cap"]]
    agg = []
    if avg_rs:
        agg.append({"label": "Average market cap (USD peers)",
                    "value": f"{_money(statistics.mean(r['cap'] for r in avg_rs))} · n={len(avg_rs)}",
                    "src": derived("mean market cap, USD peers", f"mean of {len(avg_rs)} USD peer market caps, excl. {t}",
                                   inputs(avg_rs, lambda r: [_psrc(r["t"])]))})
    for key, label, fmt_signed, srcs in (
        ("growth", "Median revenue growth", True, lambda r: [r["fin"]["rev_src"], r["fin"]["prev_src"]]),
        ("gm", "Median gross margin", False, lambda r: [r["fin"]["gross_src"]]),
        ("om", "Median operating margin", False, lambda r: [r["fin"]["op_src"]]),
    ):
        rs = [r for r in peers if r[key] is not None]
        if rs:
            agg.append({"label": label, "value": f"{_pct(statistics.median(r[key] for r in rs), fmt_signed)} · n={len(rs)}",
                        "src": derived(label.lower(), f"median over {len(rs)} peers of {key} (latest FY, excl. {t})",
                                       inputs(rs, srcs))})
    if agg:
        blocks.append({"type": "kv", "rows": agg})

    val = []
    for key, label, srcs in (
        ("ps", "Median P/S (market cap / FY revenue)", lambda r: [_psrc(r["t"]), r["fin"]["rev_src"]]),
        ("pe", "Median P/E (market cap / FY net income, positive only)", lambda r: [_psrc(r["t"]), r["fin"]["ni_src"]]),
    ):
        rs = [r for r in peers if r[key] is not None]
        if rs:
            med = statistics.median(r[key] for r in rs)
            val.append({"label": label, "value": f"{med:.1f}x · n={len(rs)}",
                        "src": derived(label.lower(), f"median of {len(rs)} USD peers' {key.upper()}", inputs(rs, srcs))})
            if me[key] is not None:
                val.append({"label": f"  this name {key.upper()}", "value": f"{me[key]:.1f}x vs median {med:.1f}x",
                            "src": derived(f"{key.upper()} of {t}", f"market cap / FY {'revenue' if key == 'ps' else 'net income'}",
                                           [_psrc(t), me["fin"]["rev_src" if key == "ps" else "ni_src"]])})
    if val:
        blocks.append({"type": "kv", "rows": val})
    return blocks


def section(t: str, con, F, prof: dict | None) -> dict | None:
    U, sub_lbl, bucket_lbl = _universe()
    P = _profiles(con)
    if prof and t not in P:
        P[t] = prof
    blocks = []
    if t in U:
        blocks += _bucket_blocks(t, U[t], U, P, sub_lbl, bucket_lbl)
    ind = (P.get(t) or {}).get("industry")
    if ind:
        blocks += _industry_blocks(t, ind, U, P, bucket_lbl)
    return {"id": ID, "title": TITLE, "blocks": blocks} if blocks else None
