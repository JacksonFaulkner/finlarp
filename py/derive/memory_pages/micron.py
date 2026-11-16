"""Micron (MU) memory page: ten tabs of sourced numbers.

Micron's fiscal year ends late Aug / early Sep, so its quarters are offset from the calendar:
FQ1 ends ~Dec (calendar Q4 of the prior year), FQ2 ~Mar (Q1), FQ3 ~Jun (Q2), FQ4 ~Sep (Q3).
memory_facts stores the CALENDAR quarter a fiscal quarter ends in; tables here show both.

Inputs: memory_facts rows (company "Micron" and "Market") plus SEC XBRL facts in
data/financials/facts/MU.parquet for gross profit / operating income and the FQ4 revenue gaps
(FQ4 = full fiscal year minus the nine-month year-to-date figure, shown as derived).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import duckdb

from core.paths import DATA_ROOT
from derive.memory_page import (Facts, src, derived, fmt, label_of, series, kv, table, bars, text,  # noqa: F401
                                qoq_table, facts_table, conflicts, qkey)

TICKER = "MU"
C = "Micron"
CIK = 723125
XBRL = DATA_ROOT / "financials" / "facts" / "MU.parquet"
REV_CONCEPT = "RevenueFromContractWithCustomerExcludingAssessedTax"


# ---- local helpers ---------------------------------------------------------------------------

def fq(p: str) -> str:
    """Calendar quarter -> Micron fiscal label (2025Q3 -> FQ4 FY25)."""
    y, q = qkey(p)
    if not y:
        return ""
    if q == 4:
        return f"FQ1 FY{(y + 1) % 100:02d}"
    return f"FQ{q + 1} FY{y % 100:02d}"


def musd(r: dict | None) -> dict | None:
    """Copy of a row with value in usd_million (memory_facts mixes $M and $B)."""
    if not r:
        return r
    if r.get("unit") == "usd_billion":
        return r | {"value": r["value"] * 1000, "unit": "usd_million"}
    return r


def money(v_musd: float) -> str:
    sign = "-" if v_musd < 0 else ""
    a = abs(v_musd)
    return f"{sign}${a:,.0f}M" if a < 1000 else f"{sign}${a / 1000:,.2f}B"


def pts(title: str, unit: str, items: list[tuple[str, float, dict]]) -> dict:
    """Series from (x, y, src) triples, so derived points can carry a derived source."""
    items = sorted(items, key=lambda t: qkey(t[0]))
    return {"type": "series", "title": title, "unit": unit,
            "points": [{"x": x, "y": round(y, 4), "src": s} for x, y, s in items]}


def only(rows: dict[str, dict], *bases: str) -> dict[str, dict]:
    return {p: r for p, r in rows.items() if r["basis"] in bases}


def strict(rows: dict[str, dict], firm: str) -> dict[str, dict]:
    firm = firm.lower()
    return {p: r for p, r in rows.items() if firm in ((r["source_name"] or "") + (r["notes"] or "")).lower()}


def short_src(r: dict) -> str:
    s = r.get("source_name") or ""
    for cut in (" earnings call prepared remarks", " earnings call prepared remark", " prepared remarks"):
        s = s.replace(cut, "")
    return s[:34]


HBM_LABEL = {"hbm_revenue": "HBM revenue, quarter", "hbm_annualized_run_rate": "HBM annualized run rate",
             "hbm4_cumulative_revenue": "HBM4 revenue, cumulative", "hbm_dimm_lpserver_revenue": "HBM + high-cap DIMM + LP server",
             "hbm_revenue_growth_qoq": "HBM revenue QoQ", "hbm_revenue_qoq_growth_floor": "HBM QoQ > company QoQ of"}


def tam_by(r: dict) -> str:
    """Who made a TAM estimate: Micron, or the research firm named in the row's notes."""
    if "Micron" in (r.get("source_name") or "") or r.get("company") == C:
        return "Micron"
    n = (r.get("notes") or r.get("source_name") or "")
    for cut in (" via", ";", " forecast", ":", ","):
        n = n.split(cut)[0]
    return n.strip()[:14]


def year_val(r: dict | None) -> str:
    return f"{r['value']:.0f}" if r else "—"


# ---- SEC XBRL (gross profit, operating income, FQ4 gaps) -------------------------------------

def _xbrl_row(concept: str, start, end, val, form, filed, accn) -> dict:
    return {"source_name": f"SEC XBRL {form} {concept}", "published": str(filed), "basis": "reported",
            "quote": f"{concept} {start}..{end} = ${val / 1e6:,.0f}M (accn {accn})",
            "source_url": f"https://www.sec.gov/Archives/edgar/data/{CIK}/{accn.replace('-', '')}/",
            "value": val / 1e6, "unit": "usd_million", "period": None, "notes": None}


def xbrl_quarters(concept: str) -> dict[str, tuple[float, dict]]:
    """calendar quarter -> ($M, src). 3-month facts as filed; FQ4 = FY - 9M (derived)."""
    if not XBRL.exists():
        return {}
    con = duckdb.connect()
    rows = con.execute(f"""
        SELECT start, "end", datediff('day', start, "end") AS d, val, form, filed, accn
        FROM read_parquet('{XBRL}')
        WHERE concept = ? AND unit = 'USD' AND "end" >= DATE '2022-09-01'
        QUALIFY row_number() OVER (PARTITION BY start, "end" ORDER BY filed DESC) = 1
    """, [concept]).fetchall()

    def cq(end) -> str:
        return f"{end.year}Q{(end.month - 1) // 3 + 1}"

    out: dict[str, tuple[float, dict]] = {}
    by_start: dict = {}
    for start, end, d, val, form, filed, accn in rows:
        by_start.setdefault(start, []).append((end, d, val, form, filed, accn))
        if 80 <= d <= 100:
            r = _xbrl_row(concept, start, end, val, form, filed, accn) | {"period": cq(end)}
            out[cq(end)] = (val / 1e6, src(r))
    for start, items in by_start.items():
        fy = [i for i in items if i[1] > 350]
        nine = [i for i in items if 260 <= i[1] <= 285]
        if fy and nine:
            e, _, v, fm, fl, ac = fy[0]
            e9, _, v9, fm9, fl9, ac9 = nine[0]
            q = cq(e)
            if q not in out:
                a = _xbrl_row(concept, start, e, v, fm, fl, ac)
                b = _xbrl_row(concept, start, e9, v9, fm9, fl9, ac9)
                out[q] = ((v - v9) / 1e6, derived(f"{fq(q)} ({q}) = fiscal year minus nine months",
                                                 f"{v / 1e6:,.0f} - {v9 / 1e6:,.0f}", [a, b]))
    return out


def xbrl_fy(concept: str) -> dict[str, tuple[float, dict]]:
    """'FY2025' -> ($M, src) from 10-K full-year facts."""
    if not XBRL.exists():
        return {}
    con = duckdb.connect()
    rows = con.execute(f"""
        SELECT start, "end", val, form, filed, accn FROM read_parquet('{XBRL}')
        WHERE concept = ? AND unit = 'USD' AND datediff('day', start, "end") > 350 AND "end" >= DATE '2022-08-01'
        QUALIFY row_number() OVER (PARTITION BY start, "end" ORDER BY filed DESC) = 1
    """, [concept]).fetchall()
    return {f"FY{e.year}": (v / 1e6, src(_xbrl_row(concept, s, e, v, fm, fl, ac))) for s, e, v, fm, fl, ac in rows}


# ---- page ------------------------------------------------------------------------------------

def build(f: Facts) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Revenue: memory_facts (quoted) first, XBRL fills the FQ4 gaps.
    rev: dict[str, tuple[float, dict]] = {}
    for p, r in f.quarterly(C, "revenue").items():
        r = musd(r)
        rev[p] = (r["value"], src(r))
    xrev = xbrl_quarters(REV_CONCEPT)
    for p, v in xrev.items():
        rev.setdefault(p, v)
    rev = dict(sorted(rev.items(), key=lambda kv_: qkey(kv_[0])))
    gp, opi = xbrl_quarters("GrossProfit"), xbrl_quarters("OperatingIncomeLoss")
    gm = {}
    for p, (g, gs) in gp.items():
        if p in xrev and xrev[p][0]:
            rv, rs = xrev[p]
            gm[p] = (g / rv * 100, {"label": f"{fq(p)} gross margin", "formula": f"{g:,.0f} / {rv:,.0f}",
                                    "inputs": [gs, rs]})
    qs = list(rev)
    last = qs[-1] if qs else None
    prev = qs[-2] if len(qs) > 1 else None

    dram = {p: musd(r) for p, r in only(f.quarterly(C, "dram_revenue"), "reported", "company_stated").items()}
    nand = {p: musd(r) for p, r in only(f.quarterly(C, "nand_revenue"), "reported", "company_stated").items()}
    dshare, nshare = f.quarterly(C, "dram_share_of_revenue"), f.quarterly(C, "nand_share_of_revenue")
    rev_guide = {r["period"]: r for r in f.all(C, "revenue_guidance")}
    fy_rev = {p: (musd(r)["value"], src(r)) for p, r in ((r["period"], r) for r in f.all(C, "revenue"))
              if p.startswith("FY")}
    for p, v in xbrl_fy(REV_CONCEPT).items():
        fy_rev.setdefault(p, v)

    dshare_cp = strict(f.quarterly(C, "dram_market_share", prefer="Counterpoint"), "Counterpoint")
    dshare_tf = strict(f.quarterly(C, "dram_market_share", prefer="TrendForce"), "TrendForce")
    dshare_om = strict(f.quarterly(C, "dram_market_share", prefer="Omdia"), "Omdia")
    hshare = strict(f.quarterly(C, "hbm_market_share", prefer="Counterpoint"), "Counterpoint")
    nshare_tf = strict(f.quarterly(C, "nand_market_share", prefer="TrendForce"), "TrendForce")
    nshare_cp = strict(f.quarterly(C, "nand_market_share", prefer="Counterpoint"), "Counterpoint")

    sections = []

    # 1. Snapshot ------------------------------------------------------------------------------
    snap = []
    if last:
        v, s = rev[last]
        snap.append((f"Revenue {fq(last)} ({last})", money(v), s))
        if prev:
            pv, ps = rev[prev]
            snap.append(("Revenue QoQ", f"{(v / pv - 1) * 100:+.1f}%",
                         {"label": f"{fq(last)} vs {fq(prev)}", "formula": f"{v:,.0f} / {pv:,.0f} - 1", "inputs": [s, ps]}))
        if last in gm:
            snap.append((f"Gross margin {fq(last)}", f"{gm[last][0]:.1f}%", gm[last][1]))
        if last in dshare:
            snap.append((f"DRAM share of revenue {fq(last)}", fmt(dshare[last]), src(dshare[last])))
    fy_last = max((p for p in fy_rev), default=None)
    if fy_last:
        snap.append((f"Revenue {fy_last} (fiscal)", money(fy_rev[fy_last][0]), fy_rev[fy_last][1]))
    g = max(rev_guide.items(), key=lambda kv_: qkey(kv_[0]), default=None)
    if g:
        snap.append((f"Guidance {fq(g[0])} revenue", fmt(g[1]), src(g[1])))
    hb = f.best(C, "hbm_revenue", "2025Q3")
    if hb:
        snap.append(("HBM revenue FQ4 FY25 (last stated)", "~$2.0B (stated)", src(hb)))
    if dshare_tf:
        p = max(dshare_tf, key=qkey)
        snap.append((f"DRAM share {p} (TrendForce)", f"{dshare_tf[p]['value']:.1f}%", src(dshare_tf[p])))
    if hshare:
        p = max(hshare, key=qkey)
        snap.append((f"HBM share {p} (Counterpoint)", f"{hshare[p]['value']:.0f}%", src(hshare[p])))
    cx = f.best(C, "capex", "FY2026")
    if cx:
        snap.append(("Net capex FY2026", fmt(cx), src(cx)))
    rpo = f.best(C, "remaining_performance_obligations")
    if rpo:
        snap.append(("Remaining performance obligations", fmt(rpo) + " (stated)", src(rpo)))
    sections.append({"id": "snapshot", "title": "Snapshot", "short": "Snapshot", "blocks": [
        kv("Latest", snap),
        text("What Micron is", "US maker of DRAM (incl. HBM) and NAND, the third of the three big DRAM makers. "
             "Fiscal years end late Aug / early Sep: FQ1 ends ~Dec, FQ2 ~Mar, FQ3 ~Jun, FQ4 ~Sep. Tabs label "
             "quarters by the calendar quarter they end in, with the fiscal label beside it "
             "(2026Q3 = FQ4 FY26, a 14-week quarter). Gross margin comes from SEC XBRL; FQ4 values not "
             "filed as 3-month facts are derived as full year minus nine months."),
    ]})

    # 2. Revenue -------------------------------------------------------------------------------
    rows_rev = []
    for p in reversed(qs):
        v, s = rev[p]
        i = qs.index(p)
        qoq = "—"
        if i:
            pv = rev[qs[i - 1]][0]
            qoq = f"{(v / pv - 1) * 100:+.1f}%"
        rows_rev.append(([p, fq(p), money(v), qoq, f"{gm[p][0]:.1f}%" if p in gm else "—",
                          money(opi[p][0]) if p in opi else "—"], s))
    guide_rows = []
    for p, r in sorted(rev_guide.items(), key=lambda kv_: qkey(kv_[0]), reverse=True):
        act = rev.get(p)
        if act:
            gv = musd(r)["value"]
            guide_rows.append(([p, fq(p), fmt(r).replace(" (guidance)", ""), money(act[0]),
                                f"{(act[0] / gv - 1) * 100:+.1f}%"],
                               {"label": f"{fq(p)} actual vs guidance midpoint", "formula": f"{act[0]:,.0f} / {gv:,.0f} - 1",
                                "inputs": [src(r), act[1]]}))
        else:
            guide_rows.append(([p, fq(p), fmt(r).replace(" (guidance)", ""), "pending", "—"], src(r)))
    fy_rows = [([p, money(v)], s) for p, (v, s) in sorted(fy_rev.items(), reverse=True)]
    demand = []
    for m, lbl in (("remaining_performance_obligations", "RPO (strategic customer agreements)"),
                   ("sca_customer_commitments", "SCA customer commitments"),
                   ("data_center_revenue", "Data center revenue FQ3 FY26"),
                   ("data_center_ssd_revenue", "Data center SSD revenue FQ4 FY26")):
        r = f.best(C, m)
        if r:
            demand.append((lbl, fmt(r), src(r)))
    sections.append({"id": "revenue", "title": "Revenue", "short": "Revenue", "blocks": [
        pts("Quarterly revenue (calendar quarter of fiscal end)", "$B", [(p, v / 1000, s) for p, (v, s) in rev.items()]),
        table("Revenue, gross margin, operating income", ["quarter", "fiscal", "revenue", "QoQ", "GM", "op income"], rows_rev),
        pts("Gross margin (SEC XBRL)", "%", [(p, v, s) for p, (v, s) in gm.items()]),
        table("Revenue guidance vs actual (midpoint)", ["quarter", "fiscal", "guided", "actual", "vs guide"], guide_rows),
        table("Fiscal years", ["fiscal year", "revenue"], fy_rows),
        kv("Demand signals (company stated)", demand),
    ]})

    # 3. DRAM vs NAND --------------------------------------------------------------------------
    mix_q = sorted(set(dram) | set(nand), key=qkey, reverse=True)
    mix_rows = []
    for p in mix_q:
        d, n = dram.get(p), nand.get(p)
        mix_rows.append(([p, fq(p), money(d["value"]) if d else "—", money(n["value"]) if n else "—",
                          fmt(dshare.get(p)), fmt(nshare.get(p))], src(d or n)))
    fy_mix = []
    for p in sorted({r["period"] for m in ("dram_revenue", "nand_revenue") for r in f.all(C, m) if r["period"].startswith("FY")},
                    reverse=True):
        d = f.best(C, "dram_revenue", p)
        n = f.best(C, "nand_revenue", p)
        fy_mix.append(([p, money(musd(d)["value"]) if d else "—", money(musd(n)["value"]) if n else "—"], src(d or n)))
    mix_blocks = [
        pts("DRAM revenue", "$B", [(p, r["value"] / 1000, src(r)) for p, r in dram.items()]),
        pts("NAND revenue", "$B", [(p, r["value"] / 1000, src(r)) for p, r in nand.items()]),
        series("DRAM share of revenue (company stated)", "%", dshare),
        table("DRAM and NAND by quarter", ["quarter", "fiscal", "DRAM", "NAND", "DRAM %", "NAND %"], mix_rows),
        table("Fiscal years (10-K)", ["fiscal year", "DRAM", "NAND"], fy_mix),
    ]
    if last in dram and last in nand:
        mix_blocks.insert(3, bars(f"Mix {fq(last)} ({last})", "$B", [("DRAM", dram[last]["value"] / 1000, src(dram[last])),
                                                                     ("NAND", nand[last]["value"] / 1000, src(nand[last]))]))
    sections.append({"id": "dram_nand", "title": "DRAM vs NAND", "short": "DRAM/NAND", "blocks": mix_blocks})

    # 4. Business units: old (CNBU/MBU/SBU/EBU) and new (CMBU/CDBU/MCBU/AEBU), never mixed ------
    def bu_table(title: str, units: list[tuple[str, str]]) -> tuple[dict, dict]:
        data = {lbl: f.quarterly(C, m) for m, lbl in units}
        qq = sorted({p for d in data.values() for p in d}, key=qkey, reverse=True)
        rows = []
        for p in qq:
            first = next((d[p] for d in data.values() if p in d), None)
            rows.append(([p, fq(p)] + [fmt(d.get(p)) for d in data.values()], src(first) if first else None))
        fys = sorted({r["period"] for m, _ in units for r in f.all(C, m) if r["period"].startswith("FY")}, reverse=True)
        fy_rows_ = []
        for p in fys:
            cells = [fmt(f.best(C, m, p)) for m, _ in units]
            first = next((f.best(C, m, p) for m, _ in units if f.best(C, m, p)), None)
            fy_rows_.append(([p] + cells, src(first)))
        return (table(title, ["quarter", "fiscal"] + [lbl for _, lbl in units], rows),
                table(title.split(" (")[0] + ", fiscal years", ["fiscal year"] + [lbl for _, lbl in units], fy_rows_))

    new_units = [("cmbu_revenue", "CMBU"), ("cdbu_revenue", "CDBU"), ("mcbu_revenue", "MCBU"), ("aebu_revenue", "AEBU")]
    old_units = [("cnbu_revenue", "CNBU"), ("mbu_revenue", "MBU"), ("sbu_revenue", "SBU"), ("ebu_revenue", "EBU")]
    new_q, new_fy = bu_table("New structure (from FQ4 FY25)", new_units)
    old_q, old_fy = bu_table("Old structure (to FQ3 FY25)", old_units)
    bu_text = text("Two structures", "Micron reorganised its business units in 2025. New: CMBU = Cloud Memory (hyperscale "
                      "DRAM incl. HBM), CDBU = Core Data Center, MCBU = Mobile and Client, AEBU = Automotive and Embedded. "
                      "Old: CNBU = Compute and Networking, MBU = Mobile, SBU = Storage, EBU = Embedded. The 10-K recast "
                      "earlier fiscal years to the new units; quarters are shown only as filed, so the two blocks below "
                      "never mix structures.")
    bu_blocks = [new_q]
    cm = f.quarterly(C, "cmbu_revenue")
    newest = max(f.quarterly(C, "aebu_revenue"), key=qkey, default=None)
    if newest:
        items = [(lbl, f.quarterly(C, m)[newest]["value"] / 1000, src(f.quarterly(C, m)[newest]))
                 for m, lbl in new_units if newest in f.quarterly(C, m)]
        bu_blocks.append(bars(f"New units {fq(newest)} ({newest})", "$B", items))
    bu_blocks += [series("CMBU revenue (new structure)", "$M", cm),
                  series("CMBU gross margin (company stated)", "%", f.quarterly(C, "cmbu_gross_margin")),
                  new_fy, old_q, series("CNBU revenue (old structure)", "$M", f.quarterly(C, "cnbu_revenue")), old_fy, bu_text]
    sections.append({"id": "bus", "title": "Business units", "short": "BUs", "blocks": bu_blocks})

    # 5. HBM -----------------------------------------------------------------------------------
    stated = []
    for m in ("hbm_revenue", "hbm_annualized_run_rate", "hbm4_cumulative_revenue", "hbm_dimm_lpserver_revenue",
              "hbm_revenue_growth_qoq", "hbm_revenue_qoq_growth_floor"):
        for r in f.all(C, m):
            note = (r.get("notes") or "")
            bound = " (lower bound)" if "lower bound" in note else " (upper bound)" if "upper bound" in note else ""
            per = r["period"] + (f" {fq(r['period'])}" if qkey(r["period"])[0] else "")
            stated.append(([per, HBM_LABEL[m],
                            fmt(musd(r) if r["unit"] == "usd_billion" and m == "hbm_revenue" else r) + bound], src(r)))
    ms = f.best(C, "hbm_revenue_fy_milestone_flag")
    if ms:
        stated.append((["FY2024", "HBM revenue, fiscal year", "several hundred $M (stated)"], src(ms)))
    stated.sort(key=lambda x: x[0][0], reverse=True)

    # Method A (inverse): HBM share of DRAM revenue implied by the stated HBM quarters.
    impl = []
    for r in f.all(C, "hbm_revenue"):
        p = r["period"]
        d = dram.get(p)
        if d:
            h = musd(r)["value"]
            note = r.get("notes") or ""
            bound = ">" if "lower bound" in note else "~"
            impl.append(([p, fq(p), f"{bound}{money(h)}", money(d["value"]), f"{bound}{h / d['value'] * 100:.1f}% est"],
                         derived(f"{fq(p)} implied HBM share of DRAM revenue (est)",
                                 f"stated HBM {h:,.0f} / DRAM revenue {d['value']:,.0f}", [r, d])))
    impl.sort(key=lambda x: qkey(x[0][0]), reverse=True)

    # Method B: annual HBM TAM x Micron HBM revenue share.
    _seen = set()
    tam_rows = [r for r in f.all(C, "hbm_market_size") + f.all("Market", "hbm_market_size")
                if not ((tam_by(r), r["period"], r["value"], r["published"]) in _seen
                        or _seen.add((tam_by(r), r["period"], r["value"], r["published"])))]
    tam_rows = sorted(tam_rows,
                      key=lambda r: (r["period"], r["published"] or ""), reverse=True)
    tam_tab = table("HBM market size (TAM) estimates", ["year", "value", "by", "said"],
                    [([r["period"], fmt(r), tam_by(r),
                       r["published"] or ""], src(r)) for r in tam_rows])
    mB = []
    share23 = f.best(C, "hbm_market_share", "2023")
    cp25 = [r for p, r in hshare.items() if p.startswith("2025")]
    for year, share_v, share_srcs, share_note in (
            ("2023", share23["value"] if share23 else None, [share23] if share23 else [],
             "TrendForce 2023 share forecast (Apr 2023)"),
            ("2025", (sum(r["value"] for r in cp25) / len(cp25)) if cp25 else None, cp25,
             f"mean of Counterpoint quarterly shares {', '.join(sorted(r['period'] for r in cp25))} "
             "(Q1 2025 not available; assumes the year averages the quarters shown)")):
        if share_v is None:
            continue
        sizes, seen = [], set()
        for r in f.all(C, "hbm_market_size") + f.all("Market", "hbm_market_size"):
            k = (tam_by(r), r["value"], r["published"])
            if r["period"] == year and r["basis"] in ("company_stated", "estimate") and k not in seen:
                seen.add(k)
                sizes.append(r)
        for sz in sorted(sizes, key=lambda r: -r["value"]):
            est = sz["value"] * share_v / 100
            who = tam_by(sz) + (" TAM" if tam_by(sz) == "Micron" else "")
            mB.append(([year, f"{who} {fmt(sz).split(' (')[0]}", f"{share_v:.0f}%", f"${est:,.2f}B est"],
                       derived(f"Method B {year} Micron HBM revenue (est)",
                               f"{sz['value']:g} x {share_v:.1f}%; share = {share_note}", [sz] + share_srcs)))
    hb_fq4 = f.best(C, "hbm_revenue", "2025Q3")
    run = f.best(C, "hbm_annualized_run_rate")
    cmp_rows = []
    if run:
        cmp_rows.append(("Stated run rate, FQ4 FY25 (annualized)", "~$8B (stated)", src(run)))
    if hb_fq4:
        cmp_rows.append(("Stated HBM revenue FQ4 FY25 (2025Q3)", "~$2.0B (stated)", src(hb_fq4)))
    b25 = [x for x in mB if x[0][0] == "2025"]
    if b25:
        cmp_rows.append(("Method B CY2025 range (est)", f"{b25[-1][0][3].split(' ')[0]} to {b25[0][0][3]}", b25[0][1]))

    # Share parity: HBM share vs DRAM share (Counterpoint, same table).
    par_rows = []
    for p in sorted(set(hshare) & set(dshare_cp), key=qkey, reverse=True):
        h, d = hshare[p], dshare_cp[p]
        par_rows.append(([p, fq(p), f"{h['value']:.0f}%", f"{d['value']:.0f}%", f"{h['value'] - d['value']:+.0f} pts"],
                         derived(f"{p} HBM share minus DRAM share", f"{h['value']:g} - {d['value']:g}", [h, d])))
    parity = []
    for m, lbl in (("hbm_share_target_vs_dram_share", "Target"), ("hbm_share_vs_dram_share_reached_flag", "Reached")):
        for r in sorted(f.all(C, m), key=lambda r: r["published"] or ""):
            parity.append((f"{lbl} ({r['published'] or r['period']})",
                           {"2025": "HBM share = DRAM bit share in CY2025", "2025Q4": "= DRAM supply share, run rate CQ4 25",
                            "2025Q3": "HBM share in line with DRAM share CQ3 25"}.get(r["period"], r["period"]), src(r)))
    sold = []
    for m in ("hbm_sold_out_flag", "hbm_supply_contracted_flag"):
        for r in sorted(f.all(C, m), key=lambda r: r["published"] or ""):
            sold.append((f"CY{r['period']} supply ({r['published'] or ''})",
                         "sold out" if m == "hbm_sold_out_flag" else "contracted / sold out", src(r)))
    tech = []
    for m, lbl, v in (("hbm3e_12h_capacity", "HBM3E 12-high", None), ("hbm4_16h_capacity", "HBM4 16-high", None),
                      ("hbm4_bandwidth_tbps", "HBM4 bandwidth", lambda r: f">{r['value']:g} TB/s per stack"),
                      ("hbm4_volume_ramp_quarter", "HBM4 volume ramp", lambda r: "CQ2 2026"),
                      ("hbm4e_volume_ramp_year", "HBM4E volume ramp", lambda r: f"CY{r['value']:.0f}"),
                      ("hbm_large_customers_shipping", "Large HBM customers shipping (FQ2 FY25)", lambda r: f"{r['value']:.0f}")):
        r = f.best(C, m)
        if r:
            tech.append((lbl, v(r) if v else fmt(r) + " per cube", src(r)))
    sections.append({"id": "hbm", "title": "HBM", "short": "HBM", "blocks": [
        table("Company-stated HBM figures", ["period", "metric", "value"], stated),
        table("Method A (inverse): implied HBM share of DRAM revenue", ["quarter", "fiscal", "HBM", "DRAM", "share"], impl),
        table("Method B: annual TAM x Micron HBM revenue share", ["year", "TAM used", "share", "Micron HBM"], mB),
        kv("Cross-check", cmp_rows),
        series("Micron HBM revenue share (Counterpoint)", "%", hshare),
        table("Share parity: HBM vs DRAM revenue share (Counterpoint)", ["quarter", "fiscal", "HBM", "DRAM", "gap"], par_rows),
        kv("Share parity milestones (company stated)", parity),
        tam_tab,
        kv("HBM supply", sold),
        kv("Products", tech),
        text("How to read the estimates", "Micron states HBM dollars only occasionally (>$100M FQ3 FY24, >$1B FQ2 FY25, "
             "~$2B FQ4 FY25), so there is no quarterly HBM series. Method A needs an HBM share of DRAM revenue; "
             "Micron gives none, so the table runs it backwards from the stated figures. Method B multiplies an annual "
             "TAM by a research-firm share and gives ANNUAL revenue; it is not split into quarters. Every 'est' value "
             "is derived and its formula and inputs are in the source bar."),
    ]})

    # 6. Bits & pricing ------------------------------------------------------------------------
    bp = {m: f.quarterly(C, m) for m in ("dram_bit_growth_qoq", "dram_asp_change_qoq", "nand_bit_growth_qoq", "nand_asp_change_qoq")}
    bq = sorted({p for d in bp.values() for p in d}, key=qkey, reverse=True)
    bp_rows = []
    for p in bq:
        first = next((d[p] for d in bp.values() if p in d), None)
        bp_rows.append(([p, fq(p)] + [f"{d[p]['value']:+.0f}%" if p in d else "—" for d in bp.values()], src(first)))
    ind = []
    for m in ("industry_dram_bit_growth_yoy", "industry_nand_bit_growth_yoy"):
        for r in sorted(f.all(C, m), key=lambda r: (r["period"], r["published"] or "")):
            ind.append((f"{'DRAM' if 'dram' in m else 'NAND'} CY{r['period']} (said {r['published'] or '?'})", fmt(r), src(r)))
    tfd = strict(f.quarterly("Market", "dram_contract_price_change_qoq", prefer="TrendForce"), "TrendForce")
    sections.append({"id": "pricing", "title": "Bits & pricing", "short": "Pricing", "blocks": [
        series("DRAM ASP change QoQ (company stated)", "%", bp["dram_asp_change_qoq"]),
        series("DRAM bit shipments QoQ (company stated)", "%", bp["dram_bit_growth_qoq"]),
        series("NAND ASP change QoQ (company stated)", "%", bp["nand_asp_change_qoq"]),
        series("NAND bit shipments QoQ (company stated)", "%", bp["nand_bit_growth_qoq"]),
        table("Bits and ASP by fiscal quarter", ["quarter", "fiscal", "DRAM bits", "DRAM ASP", "NAND bits", "NAND ASP"], bp_rows),
        kv("Industry bit growth (Micron view)", ind),
        series("DRAM contract price change QoQ (TrendForce, industry)", "%", tfd),
        text("Note", "Micron describes bits and prices in words ('mid-teens', 'low-60s'); memory_facts maps each phrase to a "
             "number (mid-teens -> 15, high-teens -> 17, low-20s -> 22) and keeps the phrase in the quote."),
    ]})

    # 7. Capex ---------------------------------------------------------------------------------
    cap_q = {p: r for p, r in f.quarterly(C, "capex").items()}
    cap_fy = {r["period"]: r for r in f.all(C, "capex") if r["period"].startswith("FY")}
    gross = {r["period"]: r for r in f.all(C, "capex_gross_ppe")}
    xppe = xbrl_fy("PaymentsToAcquirePropertyPlantAndEquipment")
    fy_cap_rows = []
    for p in sorted(set(cap_fy) | set(gross) | set(xppe), reverse=True):
        net = cap_fy.get(p)
        gr = gross.get(p)
        g_s = fmt(gr) if gr else (f"${xppe[p][0] / 1000:,.2f}B" if p in xppe else "—")
        inten = "—"
        s = src(net) if net else (src(gr) if gr else xppe[p][1])
        if net and p in fy_rev:
            inten = f"{net['value'] * 1000 / fy_rev[p][0] * 100:.0f}%"
        fy_cap_rows.append(([p, fmt(net), g_s, inten], s))
    gh = sorted(f.all(C, "capex_guidance") + f.all(C, "capex_guidance_first_half") + f.all(C, "capex_guidance_pct_of_revenue")
                + f.all(C, "construction_capex_increase_guidance"), key=lambda r: (r["published"] or "", r["period"]))
    gh_rows = []
    for r in gh:
        mm = re.search(r"FQ\d FY\d\d", r.get("source_name") or "")
        said = (mm.group(0) if mm else "") + (f" {r['published'][:7]}" if r.get("published") else "")
        tgt = r["period"]
        if qkey(tgt)[0]:
            tgt = f"{fq(tgt)} ({tgt})"
        what = {"capex_guidance": "net capex", "capex_guidance_first_half": "1H net capex",
                "capex_guidance_pct_of_revenue": "% of revenue", "construction_capex_increase_guidance": "construction, YoY +"}[r["metric"]]
        bound = " (low bound)" if "lower bound" in (r.get("notes") or "") else ""
        actual = cap_fy.get(r["period"]) if r["metric"] == "capex_guidance" else None
        if r["metric"] == "capex_guidance" and qkey(r["period"])[0]:
            actual = cap_q.get(r["period"])
        gh_rows.append(([tgt, what, said, fmt(r).replace(" (guidance)", "") + bound, fmt(actual)], src(r)))
    sections.append({"id": "capex", "title": "Capex", "short": "Capex", "blocks": [
        table("Fiscal-year capex", ["fiscal year", "net capex", "gross PP&E", "net / revenue"], fy_cap_rows),
        table("Quarterly net capex", ["quarter", "fiscal", "net capex"],
              [([p, fq(p), fmt(r)], src(r)) for p, r in sorted(cap_q.items(), key=lambda kv_: qkey(kv_[0]), reverse=True)]),
        table("Capex guidance history (by date said)", ["for", "what", "said at", "guide", "actual net"], gh_rows),
    ]})

    # 8. Fabs ----------------------------------------------------------------------------------
    def row(m, lbl, val=None):
        r = f.best(C, m)
        return (lbl, val(r) if (r and val) else fmt(r), src(r)) if r else (lbl, None, None)

    ny_out = sorted(f.all(C, "new_york_fab_first_output_year"), key=lambda r: r["published"] or "")
    ny = [row("new_york_fab_investment", "Investment (up to 4 fabs, 20+ yrs)"),
          row("new_york_state_incentives", "NY State incentives")]
    if ny_out:
        ny.append(("First wafer output", f"CY{ny_out[-1]['value']:.0f}", src(ny_out[-1])))
    idaho = [row("chips_act_direct_funding", "CHIPS Act direct funding (ID + NY)")]
    if ny_out and "ID1" in (ny_out[-1]["quote"] or ""):
        idaho.append(("ID1 wafer output", "mid-calendar 2027", src(ny_out[-1])))
    for r in sorted(f.all(C, "us_investment_plan"), key=lambda r: r["published"] or ""):
        idaho.append((f"US investment plan ({r['published']})", fmt(r) + (" +" if "lower bound" in (r["notes"] or "") else ""), src(r)))
    idaho.append(row("us_investment_plan_increment", "Added Jun 2025 (incl. 2nd Idaho fab)"))
    idaho.append(row("micron_research_labs_investment", "Micron research labs"))
    sg = [row("singapore_hbm_packaging_investment", "HBM packaging plant"),
          row("singapore_hbm_packaging_first_output_year", "Initial output", lambda r: f"early CY{r['value']:.0f}")]
    jp = [row("hiroshima_fab_investment", "Hiroshima fab investment", lambda r: f"JPY {r['value']:,.0f}B (estimate)"),
          row("hiroshima_fab_subsidy", "METI subsidy (up to)", lambda r: f"JPY {r['value']:,.0f}B (estimate)")]
    india = [row("india_atmp_investment", "Sanand ATMP (assembly/test), total"),
             row("india_government_incentive", "Government incentives")]
    sections.append({"id": "fabs", "title": "Fabs", "short": "Fabs", "blocks": [
        kv("New York (Clay)", ny), kv("Idaho (Boise) and US plan", idaho), kv("Singapore", sg),
        kv("Japan (Hiroshima)", jp), kv("India (Sanand, Gujarat)", india),
        text("Footprint", "DRAM front end: Taiwan and Hiroshima today, Boise ID1/ID2 and New York next. NAND: Singapore. "
             "HBM packaging: Taiwan now, Singapore plant next. India (Sanand) is assembly and test, not a wafer fab."),
    ]})

    # 9. Market share --------------------------------------------------------------------------
    def peers_bar(metric: str, firm: str, title: str, companies: list[str], q: str | None = None) -> dict:
        q = q or max(strict(f.quarterly(C, metric, prefer=firm), firm), key=qkey, default=None)
        items = []
        for comp in companies:
            r = strict(f.quarterly(comp, metric, prefer=firm), firm).get(q) if q else None
            if r:
                items.append((comp, r["value"], src(r)))
        return bars(f"{title} {q} ({firm})", "%", sorted(items, key=lambda x: -x[1]))

    dram_peers = ["Samsung", "SK hynix", "Micron", "CXMT", "Nanya"]
    share_q = sorted(set(dshare_tf) | set(dshare_cp) | set(dshare_om), key=qkey, reverse=True)
    share_rows = []
    for p in share_q:
        first = dshare_tf.get(p) or dshare_cp.get(p) or dshare_om.get(p)
        share_rows.append(([p, fmt(dshare_tf.get(p)).replace(" (market share)", ""),
                            fmt(dshare_om.get(p)).replace(" (market share)", ""),
                            fmt(dshare_cp.get(p)).replace(" (market share)", ""), fmt(hshare.get(p)).replace(" (market share)", "")],
                           src(first)))
    tf_rev = strict(f.quarterly(C, "dram_revenue", prefer="TrendForce"), "TrendForce")
    tf_cmp = []
    for p in sorted(tf_rev, key=qkey, reverse=True):
        own = dram.get(p)
        tf_cmp.append(([p, fq(p), fmt(tf_rev[p]).replace(" (estimate)", ""), money(own["value"]) if own else "—"], src(tf_rev[p])))
    sections.append({"id": "share", "title": "Market share", "short": "Share", "blocks": [
        peers_bar("dram_market_share", "TrendForce", "DRAM revenue share", dram_peers),
        series("Micron DRAM share (TrendForce)", "%", dshare_tf),
        series("Micron DRAM share (Counterpoint)", "%", dshare_cp),
        peers_bar("hbm_market_share", "Counterpoint", "HBM revenue share", ["SK hynix", "Samsung", "Micron"]),
        table("Micron share by source (calendar quarters)", ["quarter", "DRAM TF", "DRAM Omdia", "DRAM CP", "HBM CP"], share_rows),
        peers_bar("nand_market_share", "TrendForce", "NAND revenue share",
                  ["Samsung", "SK hynix", "Kioxia", "Micron", "SanDisk", "YMTC"]),
        table("Micron NAND share", ["quarter", "TrendForce", "Counterpoint"],
              [([p, fmt(nshare_tf.get(p)).replace(" (market share)", ""), fmt(nshare_cp.get(p)).replace(" (market share)", "")], src(nshare_tf.get(p) or nshare_cp.get(p)))
               for p in sorted(set(nshare_tf) | set(nshare_cp), key=qkey, reverse=True)]),
        table("TrendForce DRAM revenue est. (calendar) vs Micron reported (fiscal)", ["quarter", "fiscal", "TrendForce", "Micron"],
              tf_cmp),
        facts_table("Older HBM share points", f, C, ["hbm_bit_shipment_share"]) | {
            "rows": [r_ for r_ in facts_table("", f, C, ["hbm_bit_shipment_share", "hbm_market_share"])["rows"]
                     if not qkey(r_["cells"][1])[0] or "bit" in r_["cells"][0]]},
    ]})

    # 10. Sources ------------------------------------------------------------------------------
    conf = conflicts(f, [C])
    n_rows = sum(1 for r in f.rows if r["company"] == C)
    n_src = len({r["source_url"] for r in f.rows if r["company"] == C})
    bases = {}
    for r in f.rows:
        if r["company"] == C:
            bases[r["basis"]] = bases.get(r["basis"], 0) + 1
    sections.append({"id": "sources", "title": "Sources", "short": "Sources", "blocks": [
        kv("Coverage", [("Sourced numbers (Micron)", f"{n_rows}", None), ("Distinct source pages", f"{n_src}", None),
                        ("Conflicting values", f"{len(conf)}", None),
                        ("SEC XBRL quarters (revenue / GP / op income)", f"{len(xrev)} / {len(gp)} / {len(opi)}", None)]
           + [(f"Rows with basis {b}", f"{n}", None) for b, n in sorted(bases.items(), key=lambda kv_: -kv_[1])]),
        table("Where sources disagree", ["company", "metric", "period", "value", "source"], conf),
    ]})

    return {"ticker": TICKER, "name": "Micron", "industry": "DRAM, HBM and NAND", "country": "US",
            "built_at": now,
            "freshness": [{"source": "memory_facts", "pulled": now}, {"source": "SEC XBRL (data/financials)", "pulled": now}],
            "sections": sections, "unsourced": []}
