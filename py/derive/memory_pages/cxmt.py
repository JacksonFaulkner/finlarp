"""CXMT (ChangXin Memory Technologies, 688825.SS) memory page: ten tabs built from the CXMT rows
of data/memory_facts. Prospectus financials (2022-2025H1) come from an unofficial English
translation of the SSE STAR prospectus; 2023-2025 annual totals and 2026Q1 come from TrendForce
DataTrack / Yicai coverage of the updated prospectus. All values are CNY unless a unit says
otherwise. CXMT reports no HBM revenue and no research firm here estimates one, so this page has
no HBM revenue model.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from derive.memory_page import (Facts, src, derived, fmt, label_of, series, kv, table, bars, text,  # noqa: F401
                                qoq_table, facts_table, conflicts, qkey)

TICKER = "688825.SS"
C = "CXMT"
FIRMS = ("Counterpoint", "TrendForce", "Omdia")
PROSPECTUS_URL = "saranormous.github.io/filing-websites/cxmt"


# ---- local helpers ---------------------------------------------------------------------------

def fx(r: dict | None) -> str:
    """fmt() plus the units this page uses that memory_page.fmt does not know."""
    if not r:
        return "—"
    v, u = r["value"], r.get("unit") or ""
    tail = f" ({r['basis'].replace('_', ' ')})" if r.get("basis") in ("estimate", "forecast", "guidance") else ""
    if u == "cny_billion" and abs(v) >= 1000:
        return f"CNY {v / 1000:,.2f}T{tail}"
    if u == "cny_per_share":
        return f"CNY {v:,.2f}/sh{tail}"
    if u == "mt_per_s":
        return f"{v:,.0f} MT/s{tail}"
    if u == "nm":
        return f"{v:,.2f} nm{tail}".replace(".00 nm", " nm")
    if u == "count":
        return f"{v:,.0f}{tail}"
    if u == "year":
        return f"{v:.0f}{tail}"
    if u == "thousand_wafers":
        return f"{v:,.0f}k wafers{tail}"
    if u == "gb" and r.get("metric", "").endswith("die_density"):
        return f"{v:,.0f} Gb (die){tail}"
    if u == "pct" and r.get("basis") == "market_share":
        return f"{v:g}%"
    return fmt(r)


def pkey(p: str) -> str:
    """Sortable date for '2025Q1', '2025-12-31', '2026-08', '2023' (a bare year sorts as year-end)."""
    m = re.match(r"^(\d{4})Q([1-4])$", p or "")
    if m:
        return f"{m.group(1)}-{int(m.group(2)) * 3:02d}-31"
    if re.match(r"^\d{4}$", p or ""):
        return f"{p}-12-31"
    return p or ""


def nums(quote: str) -> list[float]:
    """Numbers in a verbatim quote, in order ('1,543,792.46' -> 1543792.46, '-3.67%' -> -3.67)."""
    return [float(x.replace(",", "")) for x in re.findall(r"-?\d[\d,]*\.?\d*", quote or "")]


def qsrc(r: dict, what: str) -> dict:
    """Source for a number read from another column of the same verbatim quote."""
    s = src(r)
    s["label"] = f"{what} (column of the quoted prospectus table) -- " + s["label"]
    return s


def firm(r: dict) -> str:
    """Research firm behind a share row: the source name first, then the head of the notes
    (later note clauses often mention the other firms' figures, so they are not used)."""
    name = r.get("source_name") or ""
    for k in FIRMS:
        if k in name:
            return k
    if "prospectus" in name.lower():
        return "Prospectus"
    head = (r.get("notes") or "").split(";")[0]
    for k in FIRMS:
        if k in head:
            return k
    return "Other"


def by_firm(rows: list[dict]) -> dict[str, dict[str, dict]]:
    """firm -> quarter -> one row (the firm's own page if present, else the longest quote)."""
    out: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["basis"] in ("forecast", "guidance") or not re.match(r"^\d{4}Q[1-4]$", r["period"] or ""):
            continue
        out[firm(r)][r["period"]].append(r)
    res = {}
    for k, qs in out.items():
        res[k] = {p: min(rs, key=lambda r: (0 if (r["source_name"] or "").startswith(k) else 1, -len(r["quote"] or "")))
                  for p, rs in sorted(qs.items(), key=lambda kv: qkey(kv[0]))}
    return res


def pick(f: Facts, metric: str, period: str, contains: str | None = None) -> dict | None:
    rs = [r for r in f.all(C, metric) if r["period"] == period
          and (not contains or contains.lower() in ((r["source_name"] or "") + (r["source_url"] or "")).lower())]
    return min(rs, key=lambda r: -len(r["quote"] or "")) if rs else None


def pct_change(a: dict, b: dict, label: str) -> tuple[str, dict]:
    g = a["value"] / b["value"] - 1
    return f"{g * 100:+.0f}%", derived(label, f"{a['value']:,.4g} / {b['value']:,.4g} - 1", [a, b])


def tsrc(body: str, s: dict | None) -> dict:
    t = text("", body)
    t["src"] = s
    return t


def titled(title: str, body: str, s: dict | None) -> dict:
    t = text(title, body)
    t["src"] = s
    return t


def ftable(title: str, rows: list[dict], cols=("metric", "date", "value", "source")) -> dict:
    rows = sorted(rows, key=lambda r: r["period"] or "", reverse=True)
    return table(title, list(cols), [([label_of(r["metric"]), r["period"], fx(r), short_src(r)], src(r)) for r in rows])


def short_src(r: dict) -> str:
    s = (r.get("source_name") or "").split(":")[0]
    return s if len(s) <= 34 else s[:33] + "…"


# ---- page -----------------------------------------------------------------------------------

def build(f: Facts) -> dict:
    A = lambda m: f.all(C, m)  # noqa: E731
    rev = {r["period"]: r for r in A("revenue") if r["basis"] == "reported"}
    ni = {r["period"]: r for r in A("net_income") if r["basis"] == "reported"}
    rev_g = next((r for r in A("revenue") if r["basis"] == "guidance"), None)
    ni_g = next((r for r in A("net_income") if r["basis"] == "guidance"), None)
    rev9 = pick(f, "revenue_ytd", "2025Q3")
    ni9 = pick(f, "net_income_ytd", "2025Q3")
    years = [y for y in ("2022", "2023", "2024", "2025") if y in rev]

    # prospectus table rows (unofficial translation), other columns read from the same quote
    gm_row = pick(f, "gross_margin", "2025H1", PROSPECTUS_URL)
    rd_row = pick(f, "rd_expense", "2025H1", PROSPECTUS_URL)
    rde_row = pick(f, "rd_employees", "2025-06-30", PROSPECTUS_URL)
    gm = {}  # period -> (value, src)
    if gm_row:
        n = nums(gm_row["quote"])
        for p, v in zip(("2022", "2023", "2024", "2025H1"), n[-4:]):
            gm[p] = (v, qsrc(gm_row, f"main-business gross margin {p} = {v}%"))
    rd, rd_pct = {}, {}
    if rd_row:
        n = nums(rd_row["quote"])  # 2025H1, 2024, 2023, 2022: amount (RMB 10k), % of revenue
        for i, p in enumerate(("2025H1", "2024", "2023", "2022")):
            amt, pc = n[2 * i], n[2 * i + 1]
            rd[p] = (amt / 1e5, qsrc(rd_row, f"R&D {p} = RMB {amt:,.2f} x 10k"))
            rd_pct[p] = (pc, qsrc(rd_row, f"R&D / revenue {p} = {pc}%"))
    rd_emp = {}
    if rde_row:
        for p, v in zip(("2025-06-30", "2024-12-31", "2023-12-31", "2022-12-31"), nums(rde_row["quote"])[:4]):
            rd_emp[p] = (v, qsrc(rde_row, f"R&D personnel {p} = {v:,.0f}"))
    emp = {r["period"]: r for r in A("employees") if r["basis"] == "reported"}

    share_rows = A("dram_market_share")
    sf = by_firm(share_rows)
    cap = A("wafer_capacity_kwpm")

    sections = []

    # 1. Snapshot ---------------------------------------------------------------------------
    snap = []
    if "2025" in rev:
        snap.append(("Revenue 2025", fx(rev["2025"]), src(rev["2025"])))
        if "2024" in rev:
            v, s = pct_change(rev["2025"], rev["2024"], "2025 vs 2024 revenue")
            snap.append(("Revenue growth 2025", v, s))
    if "2025" in ni:
        snap.append(("Net income 2025", fx(ni["2025"]), src(ni["2025"])))
    if "2026Q1" in rev:
        snap.append(("Revenue 2026Q1", fx(rev["2026Q1"]), src(rev["2026Q1"])))
    if "2026Q1" in ni:
        snap.append(("Net income 2026Q1 (attrib.)", fx(ni["2026Q1"]), src(ni["2026Q1"])))
        if "2026Q1" in rev:
            a, b = ni["2026Q1"], rev["2026Q1"]
            snap.append(("Net margin 2026Q1", f"{a['value'] / b['value'] * 100:.1f}%",
                         derived("2026Q1 net income / revenue", f"{a['value']} / {b['value']}", [a, b])))
    if rev_g:
        snap.append(("2026H1 revenue guidance", "CNY 110-120B (guidance)", src(rev_g)))
    for k in ("Counterpoint", "TrendForce"):
        if sf.get(k):
            p = max(sf[k], key=qkey)
            snap.append((f"DRAM share {p} ({k})", fx(sf[k][p]), src(sf[k][p])))
    cur = max((r for r in cap if r["basis"] == "estimate"), key=lambda r: r["period"], default=None)
    if cur:
        snap.append((f"Wafer capacity {cur['period'][:7]}", fx(cur), src(cur)))
    for m, lbl in (("hbm3e_yield", "HBM3E yield"), ("ipo_proceeds", "IPO proceeds")):
        r = pick(f, m, "2026-10-28") if m == "hbm3e_yield" else next(
            (x for x in A(m) if x["unit"] == "cny_billion"), None)
        if r:
            snap.append((lbl, fx(r), src(r)))
    mc = pick(f, "market_cap", "2026-07-27", "trendforce")
    if mc:
        snap.append(("Market cap at debut close", fx(mc), src(mc)))
    pros = gm_row or rd_row
    sections.append({"id": "snapshot", "title": "Snapshot", "short": "Snapshot", "blocks": [
        kv("Latest", snap),
        titled("What CXMT is",
               "ChangXin Memory Technologies, Hefei: China's largest DRAM maker (DDR4/DDR5, LPDDR4X/5X), "
               "fourth in global DRAM revenue behind Samsung, SK hynix and Micron. Listed on the Shanghai STAR "
               "Market on 2026-07-27 as 688825 at a CNY 8.66 offer price. Money figures are CNY.", src(pick(f, "dram_market_share", "2025Q4", "substack") or pick(f, "ipo_price", "2026-07-27"))),
        titled("About the prospectus numbers",
               "2022-2025H1 financials (revenue, gross margin, R&D, staff) are read from an UNOFFICIAL English "
               "translation of the SSE STAR prospectus, not the Chinese filing. 2023-2025 totals and 2026Q1 "
               "come from TrendForce DataTrack and Yicai coverage of the updated prospectus. Cursor a number "
               "to see which.", src(pros) if pros else None)]})

    # 2. Revenue & profit -------------------------------------------------------------------
    annual = []
    for y in years:
        r, n_ = rev[y], ni.get(y)
        cells = [y, fx(r), fx(n_) if n_ else "—"]
        if n_:
            cells.append(f"{n_['value'] / r['value'] * 100:+.0f}%")
        else:
            cells.append("—")
        prev = rev.get(str(int(y) - 1))
        cells.append(pct_change(r, prev, "")[0] if prev else "—")
        s = derived(f"{y} revenue, net income, net margin, YoY",
                    f"net margin = {n_['value'] if n_ else 'n/a'} / {r['value']}"
                    + (f"; YoY = {r['value']} / {prev['value']} - 1" if prev else ""),
                    [x for x in (r, n_, prev) if x])
        annual.append((cells, s))
    annual.reverse()
    half = []
    for p in ("2026Q1", "2025H1"):
        if p in rev:
            n_ = ni.get(p)
            half.append(([p, fx(rev[p]), fx(n_) if n_ else "—",
                          f"{n_['value'] / rev[p]['value'] * 100:+.0f}%" if n_ else "—"],
                         derived(f"{p} revenue and net income", "net margin = net income / revenue",
                                 [x for x in (rev[p], n_) if x])))
    # derived quarters from year-to-date totals (different sources: prospectus vs Caixin)
    qpts, qtab = [], []
    if rev9 and "2025H1" in rev:
        v = rev9["value"] - rev["2025H1"]["value"]
        s = derived("2025Q3 revenue (est): 9M (Caixin) - H1 (prospectus)",
                    f"{rev9['value']} - {rev['2025H1']['value']}", [rev9, rev["2025H1"]])
        qpts.append({"x": "2025Q3 est", "y": round(v, 3), "src": s})
        qtab.append((["2025Q3", f"CNY {v:,.1f}B est", "9M - H1"], s))
    if rev9 and "2025" in rev:
        v = rev["2025"]["value"] - rev9["value"]
        s = derived("2025Q4 revenue (est): FY (prospectus) - 9M (Caixin)",
                    f"{rev['2025']['value']} - {rev9['value']}", [rev["2025"], rev9])
        qpts.append({"x": "2025Q4 est", "y": round(v, 3), "src": s})
        qtab.append((["2025Q4", f"CNY {v:,.1f}B est", "FY - 9M"], s))
    if "2026Q1" in rev:
        qpts.append({"x": "2026Q1", "y": rev["2026Q1"]["value"], "src": src(rev["2026Q1"])})
        qtab.append((["2026Q1", fx(rev["2026Q1"]), "reported"], src(rev["2026Q1"])))
    if ni9 and "2025H1" in ni:
        v = ni9["value"] - ni["2025H1"]["value"]
        qtab.append((["2025Q3 net", f"CNY {v:,.1f}B est", "9M - H1"],
                     derived("2025Q3 net income (est): 9M (Caixin) - H1 (prospectus); Caixin's basis "
                             "(attributable or total) is not stated", f"{ni9['value']} - {ni['2025H1']['value']}",
                             [ni9, ni["2025H1"]])))
    if "2025" in rev and "2025H1" in rev:
        v = rev["2025"]["value"] - rev["2025H1"]["value"]
        qtab.append((["2025H2", f"CNY {v:,.1f}B est", "FY - H1"],
                     derived("2025H2 revenue (est)", f"{rev['2025']['value']} - {rev['2025H1']['value']}",
                             [rev["2025"], rev["2025H1"]])))
    guide = []
    if rev_g:
        guide.append((["2026H1 revenue", "CNY 110-120B", fx(rev_g)], src(rev_g)))
        if "2026Q1" in rev:
            v = rev_g["value"] - rev["2026Q1"]["value"]
            guide.append((["2026Q2 revenue implied", "", f"CNY {v:,.1f}B est"],
                          derived("2026Q2 implied by guidance (est): H1 guidance midpoint - Q1 actual",
                                  f"{rev_g['value']} - {rev['2026Q1']['value']}", [rev_g, rev["2026Q1"]])))
    if ni_g:
        guide.append((["2026H1 net income", "CNY 50-57B", fx(ni_g)], src(ni_g)))
        if "2026Q1" in ni:
            v = ni_g["value"] - ni["2026Q1"]["value"]
            guide.append((["2026Q2 net implied", "", f"CNY {v:,.1f}B est"],
                          derived("2026Q2 net income implied by guidance (est): H1 midpoint - Q1 actual",
                                  f"{ni_g['value']} - {ni['2026Q1']['value']}", [ni_g, ni["2026Q1"]])))
    sections.append({"id": "revenue", "title": "Revenue & profit", "short": "Revenue", "blocks": [
        series("Annual revenue", "CNY B", {y: rev[y] for y in years}),
        table("Annual results (CNY)", ["year", "revenue", "net income", "net margin", "rev YoY"], annual),
        table("Half / quarter reported", ["period", "revenue", "net income", "net margin"], half),
        {"type": "series", "title": "Quarterly revenue path (est = from YTD totals)", "unit": "CNY B", "points": qpts},
        table("Derived periods (est)", ["period", "value", "method"], qtab),
        table("Guidance (company, prospectus)", ["item", "range", "midpoint"], guide)]})

    # 3. Margins & R&D ----------------------------------------------------------------------
    gm_items = [(p, v, s) for p, (v, s) in gm.items()]
    q3gm = pick(f, "gross_margin", "2025Q3")
    rd_rows = []
    for p in ("2025H1", "2024", "2023", "2022"):
        if p in rd:
            rd_rows.append(([p, f"CNY {rd[p][0]:,.2f}B", f"{rd_pct[p][0]:.1f}%"], rd[p][1]))
    staff = []
    for p in ("2025-06-30", "2024-12-31", "2023-12-31", "2022-12-31"):
        e = emp.get(p)
        r_ = rd_emp.get(p)
        if e or r_:
            cells = [p, fx(e) if e else "—", f"{r_[0]:,.0f}" if r_ else "—",
                     f"{r_[0] / e['value'] * 100:.0f}%" if (e and r_) else "—"]
            staff.append((cells, derived(f"staff {p}", "R&D share = R&D personnel / total employees",
                                         [x for x in (e, rde_row) if x])))
    ni_m = []
    for y in years:
        if y in ni:
            a, b = ni[y], rev[y]
            ni_m.append({"x": y, "y": round(a["value"] / b["value"] * 100, 2),
                         "src": derived(f"{y} net margin", f"{a['value']} / {b['value']}", [a, b])})
    if "2026Q1" in ni:
        a, b = ni["2026Q1"], rev["2026Q1"]
        ni_m.append({"x": "2026Q1", "y": round(a["value"] / b["value"] * 100, 2),
                     "src": derived("2026Q1 net margin", f"{a['value']} / {b['value']}", [a, b])})
    blocks3 = [bars("Main-business gross margin (prospectus)", "%", gm_items),
               {"type": "series", "title": "Net margin (attributable)", "unit": "%", "points": ni_m},
               table("R&D expense (prospectus)", ["period", "R&D", "% of revenue"], rd_rows)]
    cum = pick(f, "rd_expense_cumulative", "2025H1")
    kvs = []
    if q3gm:
        kvs.append(("Gross margin ~2025Q3 (Caixin)", fx(q3gm), src(q3gm)))
    if cum:
        kvs.append(("R&D 2022-2025H1 cumulative", fx(cum), src(cum)))
    blocks3 += [kv("Other margin facts", kvs),
                table("Headcount (prospectus)", ["as of", "employees", "R&D staff", "R&D %"], staff)]
    wiki = [r for r in A("employees") if r["basis"] != "reported"]
    if wiki:
        blocks3.append(ftable("Other headcount figures", wiki))
    sections.append({"id": "margins", "title": "Margins & R&D", "short": "Margins", "blocks": blocks3})

    # 4. Wafer capacity ---------------------------------------------------------------------
    hist = [r for r in cap + A("wafer_output_kwpm") if r["basis"] == "estimate"]
    fc = [r for r in cap if r["basis"] == "forecast"]
    hist = sorted(hist, key=lambda r: pkey(r["period"]))
    hist_pts = [{"x": f"{r['period'][:7]} {'out' if 'output' in r['metric'] else 'cap'}", "y": r["value"], "src": src(r)}
                for i, r in enumerate(hist) if not (i and hist[i - 1]["period"][:7] == r["period"][:7]
                                                    and hist[i - 1]["value"] == r["value"])]
    side = []
    for yr in ("2024", "2026", "2027", "2028"):
        for r in sorted([r for r in fc if r["period"].startswith(yr)], key=lambda r: r["value"]):
            side.append(([yr, f"{r['value']:,.0f}k", short_src(r), (r["notes"] or "").split(";")[0][:40]], src(r)))
    e25o = next((r for r in A("wafer_output_kwpm") if r["period"] == "2025-12-31"), None)
    e25 = [r for r in cap + A("wafer_output_kwpm") if r["period"] == "2025-12-31"]
    e28 = sorted([r for r in fc if r["period"].startswith("2028")], key=lambda r: r["value"])
    add = A("wafer_capacity_added_kwpm")
    annual_out = A("dram_wafer_output_annual") + A("wafer_output_per_quarter")
    sections.append({"id": "capacity", "title": "Wafer capacity", "short": "Capacity", "blocks": [
        {"type": "series", "title": "Capacity / output history, wafers/month (mixed sources, estimates)",
         "unit": "k wpm", "points": hist_pts},
        bars("End-2025: sources disagree", "k wpm",
             [(f"{'capacity' if r['metric'] == 'wafer_capacity_kwpm' else 'output'} · {short_src(r)[:22]}",
               r["value"], src(r)) for r in e25]),
        bars("End-2028 forecasts", "k wpm", [(short_src(r)[:30], r["value"], src(r)) for r in e28]),
        table("Forecasts side by side", ["year", "k wpm", "source", "note"], side),
        ftable("Capacity additions", add),
        ftable("Wafer output", annual_out),
        tsrc("Capacity = wafer starts the fabs can run; output = wafers actually produced. Omdia's 240k "
             "output at end-2025 vs SemiAnalysis' 265k capacity is partly that difference; Omdia ties the "
             "output ceiling to equipment export controls and yields.",
             src(e25o) if e25o else None)]})

    # 5. DRAM share -------------------------------------------------------------------------
    quarters = sorted({p for k in sf for p in sf[k]}, key=qkey, reverse=True)
    cols = [k for k in ("Counterpoint", "TrendForce", "Omdia", "Prospectus") if k in sf]
    side_rows = []
    for q in quarters:
        cells = [q] + [fx(sf[k].get(q)) if sf[k].get(q) else "—" for k in cols]
        ins = [sf[k][q] for k in cols if sf[k].get(q)]
        side_rows.append((cells, derived(f"{q} CXMT DRAM revenue share by firm", "one row per firm", ins)
                          if len(ins) > 1 else src(ins[0])))
    other = [r for r in share_rows if firm(r) == "Other" or r["basis"] == "forecast"
             or not re.match(r"^\d{4}Q[1-4]$", r["period"] or "")] + A("dram_production_share")
    peer_q = max(sf.get("Counterpoint", {}) or {"": 0}, key=qkey)
    peers = []
    for comp in ("Samsung", "SK hynix", "Micron", "CXMT", "Nanya"):
        r = by_firm(f.all(comp, "dram_market_share")).get("Counterpoint", {}).get(peer_q)
        if r:
            peers.append((comp, r["value"], src(r)))
    tq = max(sf.get("TrendForce", {}) or {"": 0}, key=qkey)
    tpeers = []
    for comp in ("Samsung", "SK hynix", "Micron", "CXMT"):
        r = by_firm(f.all(comp, "dram_market_share")).get("TrendForce", {}).get(tq)
        if r:
            tpeers.append((comp, r["value"], src(r)))
    blocks5 = [series(f"CXMT DRAM revenue share: {k}", "%", sf[k]) for k in ("Counterpoint", "TrendForce", "Omdia") if sf.get(k)]
    blocks5.insert(0, table("CXMT DRAM share by research firm", ["quarter"] + cols, side_rows))
    blocks5 += [bars(f"Counterpoint DRAM revenue share {peer_q}", "%", sorted(peers, key=lambda x: -x[1])),
                bars(f"TrendForce DRAM revenue share {tq}", "%", sorted(tpeers, key=lambda x: -x[1])),
                series("CXMT DRAM revenue, Omdia estimate", "$B", f.quarterly(C, "dram_revenue")),
                ftable("Annual, projected and other-basis shares", other)]
    sections.append({"id": "share", "title": "DRAM share", "short": "Share", "blocks": blocks5})

    # 6. Products & nodes -------------------------------------------------------------------
    node_m = ["ddr5_node", "g5_active_area_half_pitch", "g5_dies_per_wafer_increase", "ddr5_yield"]
    prod_m = ["ddr5_max_speed", "lpddr5x_max_speed", "lpddr5x_die_density"]
    mix_m = ["server_share_of_revenue", "customer_contract_value", "dram_asp_change_yoy", "dram_asp_change_qoq",
             "dram_bit_growth_qoq", "lpddr_sales_volume_growth_yoy", "dram_asp_discount_vs_peers"]
    g5 = pick(f, "g5_active_area_half_pitch", "2026-09-20")
    sections.append({"id": "products", "title": "Products & nodes", "short": "Products", "blocks": [
        ftable("Process nodes and yields", [r for m in node_m for r in A(m)]),
        ftable("Products", [r for m in prod_m for r in A(m)]),
        ftable("Pricing, bits and mix", [r for m in mix_m for r in A(m)]),
        titled("Node generations",
               "G4: 17nm-class DDR5 per TrendForce (TechInsights measured ~16nm on G4 16Gb DDR5). G5: 11.95nm "
               "active-area half pitch made with quadruple patterning, no EUV; mass "
               "production announced 2026-09-20 with 24Gb LPDDR5X first.", src(g5) if g5 else None)]})

    # 7. HBM --------------------------------------------------------------------------------
    hbm_m = [m for (c, m) in f.by if c == C and m.startswith("hbm")]
    hbm_rows = [r for m in hbm_m for r in A(m)]
    yields = [(f"{label_of(r['metric']).replace(' yield', '').upper()} · {short_src(r)[:18]}", r["value"], src(r))
              for r in hbm_rows if r["metric"].endswith("_yield")]
    hcap = sorted([r for r in hbm_rows if r["metric"] == "hbm_capacity_kwpm"], key=lambda r: r["period"])
    timing = [r for r in hbm_rows if "production" in r["metric"] or "volume_start" in r["metric"]]
    no_hbm = next(iter(A("ipo_proceeds_to_existing_lines")), None)
    sections.append({"id": "hbm", "title": "HBM", "short": "HBM", "blocks": [
        titled("No HBM revenue model",
               "CXMT does not report HBM revenue or HBM's share of DRAM sales, and no research firm in the "
               "data gives a CXMT HBM market share or HBM revenue estimate, so this tab shows no HBM revenue "
               "(estimated or otherwise). The IPO use-of-proceeds list has no HBM project.",
               src(no_hbm) if no_hbm else None),
        bars("Reported HBM yields (estimates)", "%", yields),
        table("Timing", ["metric", "date", "value", "source"],
              [([label_of(r["metric"]), r["period"], fx(r), short_src(r)], src(r))
               for r in sorted(timing, key=lambda r: r["period"])]),
        table("HBM wafer capacity: sources disagree", ["as of", "k wpm", "basis", "source"],
              [([r["period"], f"{r['value']:,.0f}k", r["basis"], short_src(r)], src(r)) for r in hcap]),
        titled("Where CXMT is",
               "HBM3 8-high yield ~25% in 2026Q2 (front-end ~35% x back-end ~70%, SemiAnalysis). HBM3E small-"
               "scale production started around Aug 2026, with Reuters putting yield at 20-30% (source notes: ~70% "
               "at SK hynix). Full HBM3E mass production: end-2026 (Reuters) or 2027 (Korean industry analysis).",
               src(pick(f, "hbm3_yield", "2026Q2")) if pick(f, "hbm3_yield", "2026Q2") else None)]})

    # 8. IPO & funding ----------------------------------------------------------------------
    ipo_m = ["ipo_price", "ipo_proceeds", "ipo_planned_raise", "ipo_proceeds_to_existing_lines", "market_cap",
             "hefei_govt_ownership"]
    fund_m = ["funding_round_size", "pre_money_valuation"]
    fa = {r["period"]: r for r in A("fixed_assets")}
    fa_chg = []
    for y in sorted(fa):
        p = fa.get(str(int(y) - 1))
        if p:
            fa_chg.append({"x": y, "y": round(fa[y]["value"] - p["value"], 3),
                           "src": derived(f"{y} change in fixed assets (proxy for net capex, est)",
                                          f"{fa[y]['value']} - {p['value']}", [fa[y], p])})
    ipo_kv = []
    price = pick(f, "ipo_price", "2026-07-27")
    procs = next((r for r in A("ipo_proceeds") if r["unit"] == "cny_billion"), None)
    if price and procs:
        ipo_kv.append(("Shares sold (implied)", f"{procs['value'] / price['value']:,.3f}B shares",
                       derived("proceeds / offer price", f"{procs['value']} / {price['value']}", [procs, price])))
    pm = pick(f, "pre_money_valuation", "2024-03")
    if mc and pm:
        ipo_kv.append(("Debut market cap / 2024 pre-money", f"{mc['value'] / pm['value']:.1f}x",
                       derived("debut close market cap / March 2024 pre-money valuation",
                               f"{mc['value']} / {pm['value']}", [mc, pm])))
    if procs and pick(f, "ipo_planned_raise", "2026-05-28"):
        pr = pick(f, "ipo_planned_raise", "2026-05-28")
        ipo_kv.append(("Raised vs planned", f"{procs['value'] / pr['value']:.2f}x",
                       derived("actual proceeds / planned raise", f"{procs['value']} / {pr['value']}", [procs, pr])))
    sections.append({"id": "ipo", "title": "IPO & funding", "short": "IPO", "blocks": [
        ftable("STAR Market IPO (2026-07-27, 688825)", [r for m in ipo_m for r in A(m)]),
        kv("Derived", ipo_kv),
        ftable("Pre-IPO funding", [r for m in fund_m for r in A(m)]),
        series("Fixed assets (prospectus via Substack)", "CNY B", fa),
        {"type": "series", "title": "Fixed-asset growth, capex proxy (est)", "unit": "CNY B", "points": fa_chg}]})

    # 9. Export controls --------------------------------------------------------------------
    dod = next(iter(A("dod_1260h_listing")), None)
    ent = next(iter(A("entity_list_delayed_firms")), None)
    wo = next((r for r in A("wafer_output_kwpm") if r["period"] == "2025-12-31"), None)
    note = lambda r: {**src(r), "label": "per research notes on this row, not in the quote -- " + src(r)["label"]}  # noqa: E731
    tl = []
    if ent:
        tl.append((["2024-03", "Entity List listing under consideration (Bloomberg)", "Commerce"], note(ent)))
    if dod:
        tl.append((["2025-01-06", "Added to DoD Section 1260H 'Chinese military companies' list", "DoD"], src(dod)))
        tl.append((["2026-02-13", "Reported removed from the 1260H list", "DoD"], note(dod)))
        tl.append((["2026-06", "Kept / reinstated after June 2026 review", "DoD"], note(dod)))
    if ent:
        tl.append((["2026-06-16", "Entity List addition approved by interagency panel; Commerce delays "
                                  "publishing it along with 100+ other firms", "Commerce"], src(ent)))
    if dod:
        tl.append((["2026-08", "CXMT sues DoD over the 1260H listing", "Court"], note(dod)))
    if g5:
        tl.append((["2026-09-20", "G5 node in production with quadruple patterning, no EUV", "Tools"], src(g5)))
    sections.append({"id": "controls", "title": "Export controls", "short": "Controls", "blocks": [
        table("US lists and controls timeline", ["date", "event", "who"], tl),
        kv("Status (latest in data)", [
            ("DoD 1260H list", "on the list (reinstated mid-2026; lawsuit filed Aug 2026)", note(dod) if dod else None),
            ("Commerce Entity List", "not published as of 2026-06 (approved, delayed)", src(ent) if ent else None),
            ("Effect on output", "Omdia ties the ~240k wpm end-2025 output ceiling to equipment controls and yields",
             note(wo) if wo else None)]),
        tsrc("The data has no rows on BIS equipment rules (Oct 2022 / Dec 2024) or HBM export rules naming "
             "CXMT, so they are not shown; only listings with a quoted source are on this tab.", None)]})

    # 10. Sources ---------------------------------------------------------------------------
    mine = [r for r in f.rows if r["company"] == C]
    conf = conflicts(f, [C])
    by_src = Counter(short_src(r) for r in mine)
    first = {}
    for r in mine:
        first.setdefault(short_src(r), r)
    sections.append({"id": "sources", "title": "Sources", "short": "Sources", "blocks": [
        kv("Coverage", [("Sourced CXMT numbers", f"{len(mine)}", None),
                        ("Distinct source pages", f"{len({r['source_url'] for r in mine})}", None),
                        ("Conflicting values", f"{len(conf)}", None)]),
        titled("Prospectus translation",
               "Rows named 'CXMT STAR prospectus (unofficial English translation)' come from a community "
               "translation of the Chinese SSE filing (saranormous.github.io), not from CXMT or the exchange. "
               "Several of its figures match TrendForce and Yicai reports of the official filing (2023-2024 "
               "revenue and net income); the rest are unverified against the Chinese text.", src(pros) if pros else None),
        table("Rows per source", ["source", "rows"],
              [([k, str(n)], src(first[k])) for k, n in by_src.most_common()]),
        table("Where sources disagree", ["company", "metric", "period", "value", "source"], conf)]})

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {"ticker": TICKER, "name": "CXMT", "industry": "DRAM", "country": "China",
            "built_at": now, "freshness": [{"source": "memory_facts", "pulled": now}],
            "sections": sections, "unsourced": []}
