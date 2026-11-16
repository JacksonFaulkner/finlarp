"""YMTC (Yangtze Memory Technologies) memory page: ten tabs of sourced numbers.

YMTC is not listed. Its parent, CCSH (Changjiang/Changkong group holding), filed a STAR Market IPO
prospectus in Aug 2026; the IPO was reported on hold in Nov 2026. The 2023 to Q1 2026 financials
below were read from press coverage of that prospectus (Caixin, Global Times/SSE, StorageNewsletter,
Admirals), not from the prospectus itself, and they are CCSH consolidated figures.
"""
from __future__ import annotations

from datetime import datetime, timezone

from derive.memory_page import (Facts, src, derived, fmt, label_of, series, kv, table, bars, text,  # noqa: F401
                                qoq_table, facts_table, conflicts, qkey)

TICKER = "YMTC"
C = "YMTC"

PROSPECTUS_NOTE = ("Financials (2023 to Q1 2026) are CCSH consolidated figures from the Aug 2026 STAR IPO "
                   "prospectus, read from press coverage of it (Caixin, Global Times/SSE, StorageNewsletter, "
                   "Admirals), not from the prospectus itself. YMTC Co. is over 90% of CCSH revenue.")


# ---- local helpers ---------------------------------------------------------------------------

def _rows(f: Facts, metric: str, company: str = C) -> list[dict]:
    return sorted(f.all(company, metric), key=lambda r: (r["period"] or "", r["published"] or ""))


def _by_period(f: Facts, metric: str, periods: list[str] | None = None, actual: bool = True) -> dict[str, dict]:
    """period -> best row for non-quarterly metrics (years, dates), in period order."""
    out: dict[str, dict] = {}
    for p in sorted({r["period"] for r in f.all(C, metric)}):
        if periods and p not in periods:
            continue
        rs = [r for r in f.all(C, metric) if r["period"] == p and (not actual or r["basis"] not in ("guidance", "forecast"))]
        if rs:
            out[p] = f.best(C, metric, p) if not actual else min(
                rs, key=lambda r: ({"reported": 0, "company_stated": 1, "estimate": 2, "market_share": 3}.get(r["basis"], 9),
                                   -len(r["quote"] or "")))
    return out


def _one(f: Facts, metric: str, period: str | None = None, source: str | None = None) -> dict | None:
    rs = [r for r in f.all(C, metric) if (period is None or r["period"] == period)
          and (source is None or source.lower() in (r["source_name"] or "").lower())]
    return rs[0] if rs else None


def _cny(v: float) -> str:
    return f"CNY {v:,.2f}B" if abs(v) < 1 else f"CNY {v:,.1f}B"


def fmt(r):  # noqa: F811  local: 2 decimals for sub-1bn CNY, words for counts
    from derive.memory_page import fmt as _fmt
    if r and r.get("unit") == "cny_billion" and abs(r["value"]) < 1:
        s = _cny(r["value"])
        return s + (f" ({r['basis'].replace('_', ' ')})" if r.get("basis") in ("estimate", "forecast", "guidance", "market_share") else "")
    if r and r.get("unit") == "count":
        noun = {"entity_list_firms_added": " firms", "patents_asserted_vs_micron": " patents"}.get(r["metric"], "")
        return f"{r['value']:,.0f}{noun}"
    return _fmt(r)


def _src_cell(r: dict) -> str:
    return (r.get("source_name") or "").split(":")[0][:28]


def _fx(f: Facts) -> tuple[float, dict] | None:
    """CNY per USD implied by Caixin's '33 billion yuan ($4.9 billion)'."""
    r = _one(f, "ipo_raise_target", source="Caixin")
    return (33.0 / 4.9, r) if r else None


# ---- page ------------------------------------------------------------------------------------

def build(f: Facts) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rev = _by_period(f, "revenue", ["2023", "2024", "2025"])
    ni = {p: r for p, r in _by_period(f, "net_income", ["2023", "2024", "2025"]).items()}
    ni["2023"] = _one(f, "net_income", "2023", "Global Times") or ni.get("2023")  # prospectus, not Changkong
    rev_q1, ni_q1 = _one(f, "revenue", "2026Q1"), _one(f, "net_income", "2026Q1")
    gm_q1 = _one(f, "gross_margin", "2026Q1")
    cp = {r["period"]: r for r in _rows(f, "nand_market_share") if (r["source_name"] or "") == "Counterpoint Research"}
    gfm = {r["period"]: r for r in _rows(f, "nand_market_share") if (r["source_name"] or "").startswith("GetFlashMemory")}
    cp = dict(sorted(cp.items(), key=lambda kv_: qkey(kv_[0])))
    gfm = dict(sorted(gfm.items(), key=lambda kv_: qkey(kv_[0])))
    ipo_val = _one(f, "ipo_valuation", "2026-08-27")
    raise_t = _one(f, "ipo_raise_target")
    admirals_url = next((r["source_url"] for r in f.all(C, "revenue") if "Admirals" in (r["source_name"] or "")), None)
    hold_src = {"label": "Reuters 2026-11-04 via Admirals (2026-11-11) [press report; recorded in research notes, "
                         "no verbatim quote stored]: CCSH STAR IPO put on hold", "url": admirals_url}
    sections = []

    # 1. Snapshot ---------------------------------------------------------------------------
    snap = []
    if "2025" in rev:
        snap.append(("Revenue 2025 (CCSH)", fmt(rev["2025"]), src(rev["2025"])))
    if "2025" in ni:
        snap.append(("Net profit 2025", fmt(ni["2025"]), src(ni["2025"])))
    if rev_q1:
        snap.append(("Revenue Q1 2026", fmt(rev_q1), src(rev_q1)))
    if ni_q1:
        snap.append(("Net profit Q1 2026", fmt(ni_q1), src(ni_q1)))
    if gm_q1:
        snap.append(("Gross margin Q1 2026", fmt(gm_q1), src(gm_q1)))
    if cp:
        lp = max(cp, key=qkey)
        snap.append((f"NAND revenue share {lp}", f"{cp[lp]['value']:.0f}% (Counterpoint)", src(cp[lp])))
    ship = _one(f, "nand_shipment_share", "2026Q2")
    if ship:
        snap.append(("NAND bit shipment share 2026Q2", fmt(ship), src(ship)))
    cap = _one(f, "wafer_capacity_kwpm", "2026-08-24")
    if cap:
        snap.append(("Wafer capacity (Caixin, Aug 2026)", f"~{cap['value']:.0f}k wpm (est; sources 130-200k)", src(cap)))
    lay = _one(f, "layer_count", "2026-08-28")
    if lay:
        snap.append(("Layers in mass production", fmt(lay) + " (Xtacking 4.0)", src(lay)))
    if ipo_val:
        snap.append(("IPO valuation range", "CNY 275-330B (prospectus)", src(ipo_val)))
    snap.append(("IPO status", "filed Aug 2026; reported on hold Nov 2026", hold_src))
    sections.append({"id": "snapshot", "title": "Snapshot", "short": "Snapshot",
                     "blocks": [kv("Latest", snap),
                                text("What YMTC is", "Yangtze Memory Technologies, Wuhan: China's 3D NAND maker, state-backed "
                                     "(Big Fund, Hubei investors). Its Xtacking design builds the CMOS logic and the NAND "
                                     "array on separate wafers and bonds them. On the US Entity List since Dec 2022. Not "
                                     "listed: parent CCSH filed for a Shanghai STAR Market IPO in Aug 2026, which was "
                                     "reported on hold in Nov 2026. " + PROSPECTUS_NOTE)]})

    # 2. Revenue & profit -------------------------------------------------------------------
    pl_rows = []
    for p in ("2023", "2024", "2025"):
        r, n = rev.get(p), ni.get(p)
        if r:
            pl_rows.append(([p, fmt(r), fmt(n) if n else "—", _src_cell(r)], src(r)))
    if rev_q1:
        pl_rows.append((["2026Q1", fmt(rev_q1), fmt(ni_q1), _src_cell(rev_q1)], src(rev_q1)))
    growth = []
    ps = [p for p in ("2023", "2024", "2025") if p in rev]
    for a, b in zip(ps, ps[1:]):
        ra, rb = rev[a], rev[b]
        growth.append((f"Revenue {b} vs {a}", f"{(rb['value'] / ra['value'] - 1) * 100:+.1f}%",
                       derived(f"{b} vs {a}", f"{rb['value']:,.1f} / {ra['value']:,.1f} - 1", [rb, ra])))
    yoy = _one(f, "revenue_growth_yoy", "2026Q1")
    if yoy and rev_q1:
        growth.append(("Revenue Q1 2026 YoY (stated)", f"+{yoy['value']:.0f}%", src(yoy)))
        q1_25 = rev_q1["value"] / (1 + yoy["value"] / 100)
        growth.append(("Implied Q1 2025 revenue (est)", f"{_cny(q1_25)} est",
                       derived("Q1 2025 implied from Q1 2026 and stated YoY",
                               f"{rev_q1['value']:,.1f} / (1 + {yoy['value']:.0f}%) = {q1_25:,.2f}; YoY is rounded",
                               [rev_q1, yoy])))
    if ni_q1 and "2025" in ni:
        growth.append(("Q1 2026 profit vs all of 2025", f"{ni_q1['value'] / ni['2025']['value']:.2f}x",
                       derived("Q1 2026 / FY2025 net profit", f"{ni_q1['value']:,.1f} / {ni['2025']['value']:,.1f}",
                               [ni_q1, ni["2025"]])))
    dnp = _one(f, "daily_net_profit", "2026Q1")
    if dnp:
        growth.append(("Daily net profit Q1 2026", f">CNY {dnp['value']:.2f}B", src(dnp)))
        if ni_q1:
            growth.append(("Check: daily x 90 days (est)", f"{_cny(dnp['value'] * 90)} est",
                           derived("cross-check of Q1 profit", f"{dnp['value']} x 90 days = {dnp['value'] * 90:,.1f} "
                                   f"vs stated {ni_q1['value']:,.1f}", [dnp, ni_q1])))
    ent = _one(f, "ymtc_entity_revenue", "2025")
    if ent:
        growth.append(("YMTC Co. (subsidiary) revenue 2025", fmt(ent), src(ent)))
        if "2025" in rev:
            growth.append(("YMTC Co. share of CCSH 2025", f"{ent['value'] / rev['2025']['value'] * 100:.1f}%",
                           derived("subsidiary / consolidated", f"{ent['value']:,.2f} / {rev['2025']['value']:,.1f}",
                                   [ent, rev["2025"]])))
    other_rev = [r for r in f.all(C, "revenue") if r["basis"] == "estimate"] + f.all(C, "nand_revenue")
    other_ni = [r for r in f.all(C, "net_income") if r is not ni.get("2023") and r["period"] in ("2022", "2023")]
    sections.append({"id": "revenue", "title": "Revenue & profit", "short": "Revenue",
                     "blocks": [series("Annual revenue (CCSH consolidated)", "CNY B", rev),
                                series("Annual net profit", "CNY B", ni),
                                table("Income by period", ["period", "revenue", "net profit", "source"], pl_rows),
                                kv("Growth and checks", growth),
                                table("Third-party estimates and older figures (not prospectus)",
                                      ["metric", "period", "value", "source"],
                                      [([label_of(r["metric"]), r["period"], fmt(r), _src_cell(r)], src(r))
                                       for r in sorted(other_rev + other_ni, key=lambda r: r["period"])]),
                                text("Read with care", PROSPECTUS_NOTE + " The 2023 loss of CNY 19.2B (memory downturn) "
                                     "conflicts with a CNY 0.531B profit that Caixin dates to 2022 and TMTPost attributes "
                                     "to Changkong Group for 2023: different years or entities.")]})

    # 3. Margins, capex, R&D ---------------------------------------------------------------
    marg = []
    nm_pts = []
    for p in ("2023", "2024", "2025"):
        if p in rev and p in ni:
            v = ni[p]["value"] / rev[p]["value"] * 100
            d = derived(f"{p} net margin", f"{ni[p]['value']:,.2f} / {rev[p]['value']:,.1f}", [ni[p], rev[p]])
            marg.append((f"Net margin {p}", f"{v:.1f}%", d))
            nm_pts.append({"x": p, "y": round(v, 2), "src": d})
    if rev_q1 and ni_q1:
        v = ni_q1["value"] / rev_q1["value"] * 100
        d = derived("Q1 2026 net margin", f"{ni_q1['value']:,.1f} / {rev_q1['value']:,.1f}", [ni_q1, rev_q1])
        marg.append(("Net margin Q1 2026", f"{v:.1f}%", d))
        nm_pts.append({"x": "2026Q1", "y": round(v, 2), "src": d})
    if gm_q1:
        marg.append(("Gross margin Q1 2026", fmt(gm_q1), src(gm_q1)))
    asp = _one(f, "nand_asp_change_vs_2025_avg", "2026Q1")
    if asp:
        marg.append(("NAND price Q1 2026 vs 2025 avg", f"+{asp['value']:.0f}% (estimate)", src(asp)))
    capx, rnd = _one(f, "capex_cumulative"), _one(f, "rnd_cumulative")
    cum_in = [rev[p] for p in ("2023", "2024", "2025") if p in rev] + ([rev_q1] if rev_q1 else [])
    cum = sum(r["value"] for r in cum_in)
    inv = []
    if cum_in:
        inv.append(("Cumulative revenue 2023-Q1 2026", _cny(cum),
                    derived("sum of period revenue", " + ".join(f"{r['value']:,.1f}" for r in cum_in), cum_in)))
    for r, nm in ((capx, "capex"), (rnd, "R&D")):
        if r:
            inv.append((f"Cumulative {nm} 2023-Q1 2026", f"~{fmt(r)}", src(r)))
            if cum:
                inv.append((f"{nm} / revenue, 2023-Q1 2026", f"{r['value'] / cum * 100:.0f}%",
                            derived(f"cumulative {nm} / cumulative revenue", f"{r['value']:,.0f} / {cum:,.1f}",
                                    [r] + cum_in)))
    for m, lbl in (("ipo_proceeds_capex", "IPO proceeds earmarked: capex"), ("ipo_proceeds_rnd", "IPO proceeds earmarked: R&D")):
        r = _one(f, m)
        if r:
            inv.append((lbl, fmt(r), src(r)))
    pat = _one(f, "patents_granted")
    if pat:
        inv.append(("Invention patents (Mar 2026)", f"{pat['value']:,.0f}", src(pat)))
    sections.append({"id": "margins", "title": "Margins, capex, R&D", "short": "Margins",
                     "blocks": [{"type": "series", "title": "Net margin (derived)", "unit": "%", "points": nm_pts},
                                kv("Margins", marg), kv("Capex and R&D", inv),
                                text("Note", "The prospectus coverage gives capex and R&D only as cumulative totals for "
                                     "the reporting period (2023 to Q1 2026, ~CNY 96B and ~CNY 16B); no per-year split "
                                     "was found. Gross margin was found for Q1 2026 only.")]})

    # 4. Wafer capacity ---------------------------------------------------------------------
    wc = _rows(f, "wafer_capacity_kwpm")
    cap_rows = [([r["period"], fmt(r), r["basis"], _src_cell(r), (r["notes"] or "")[:40]], src(r)) for r in wc]
    cap_bars = [(f"{r['period'][:7]} {_src_cell(r)[:14]}", r["value"], src(r)) for r in wc if r["basis"] != "forecast"]
    wp = _rows(f, "wafers_processed")
    wp_rows = []
    for r in wp:
        k = r["value"] / 12 / 1000
        wp_rows.append(([r["period"], f"{r['value'] / 1e6:.2f}M wafers", f"~{k:.0f}k wpm avg" + (" est" if r["basis"] != "forecast" else " fcst"),
                         _src_cell(r)],
                        derived(f"{r['period']} wafers / 12 months", f"{r['value']:,.0f} / 12 / 1000 = {k:,.1f}k per month", [r])))
    plan = []
    for m in ("planned_wafer_capacity_kwpm", "new_fab_design_capacity_kwpm", "wafer_capacity_added_kwpm",
              "fab3_design_capacity_kwpm", "fab3_wafer_capacity_kwpm", "fab3_investment_progress",
              "fab3_registered_capital", "fab3_ymtc_stake", "fab3_domestic_tool_share"):
        for r in _rows(f, m):
            plan.append(([label_of(m).replace(" kwpm", ""), r["period"], fmt(r), _src_cell(r)], src(r)))
    sections.append({"id": "capacity", "title": "Wafer capacity", "short": "Capacity",
                     "blocks": [bars("Installed capacity estimates (k wafers/month)", "k wpm", cap_bars),
                                table("Capacity: sources side by side", ["as of", "value", "basis", "source", "note"], cap_rows),
                                table("Wafers processed per year -> monthly average", ["year", "wafers", "per month", "source"], wp_rows),
                                table("Expansion: Fab 3 and plans", ["metric", "date", "value", "source"], plan),
                                text("Why 130k, 160k and 200k all appear", "No figure comes from YMTC. ~130k wafer starts/month "
                                     "(Notebookcheck, eefocus via TrendForce) and 160k at end-2024 (analyst reports via Reuters) "
                                     "describe the same two Wuhan fabs at about the same time, so they are a genuine conflict. "
                                     "Reuters' sources put it at ~200k in Apr 2026 while Caixin said ~160k in Aug 2026. Wafer "
                                     "starts (what is running) and installed capacity (what could run) are often mixed. The "
                                     "Korea Herald annual wafer counts work out to ~108k/month in 2024 and ~148k in 2025, "
                                     "nearer the low end.")]})

    # 5. NAND market share ------------------------------------------------------------------
    qs = sorted(set(cp) | set(gfm), key=qkey)
    side = [([q, fmt(cp.get(q)).replace(" (market share)", ""), fmt(gfm.get(q)).replace(" (market share)", "")],
             src(cp.get(q) or gfm.get(q))) for q in qs]
    lq = "2026Q1"
    peers = []
    for comp in ("Samsung", "SK hynix", "Kioxia", "Micron", "SanDisk", "YMTC"):
        r = next((x for x in f.all(comp, "nand_market_share") if x["period"] == lq
                  and (x["source_name"] or "").startswith("GetFlashMemory")), None)
        if r:
            peers.append((comp, r["value"], src(r)))
    others = [r for r in _rows(f, "nand_market_share") if r not in cp.values() and r not in gfm.values()]
    ship_rows = _rows(f, "nand_shipment_share")
    have = {r["period"] for r in ship_rows}  # same Counterpoint figures appear under both metric names
    ship_rows += [r for r in _rows(f, "nand_bit_shipment_share") if r["period"] not in have]
    ship_rows += _rows(f, "nand_bit_growth_qoq") + _rows(f, "nand_bit_growth_yoy")
    checks = []
    size = next((r for r in f.all("Market", "nand_market_size") if r["period"] == "2026Q1"
                 and (r["source_name"] or "").startswith("GetFlashMemory")), None)
    nrev = _one(f, "nand_revenue", "2026Q1")
    if size and gfm.get("2026Q1"):
        s = gfm["2026Q1"]
        v = size["value"] * s["value"] / 100
        checks.append(("Q1 2026 NAND revenue, share x market (est)", f"${v:.2f}B est",
                       derived("Counterpoint share x Counterpoint market size", f"{s['value']}% x ${size['value']}B", [s, size])))
    fx = _fx(f)
    if fx and rev_q1:
        rate, fr = fx
        checks.append(("Q1 2026 CCSH revenue in USD (est)", f"${rev_q1['value'] / rate:.2f}B est",
                       derived("CNY revenue / CNY-USD rate implied by Caixin (33bn yuan = $4.9bn)",
                               f"{rev_q1['value']:,.1f} / ({33.0} / {4.9}) = {rev_q1['value'] / rate:,.2f}", [rev_q1, fr])))
    if nrev:
        checks.append(("TechNode Q1 2026 NAND revenue", fmt(nrev) + " - conflicts", src(nrev)))
    sections.append({"id": "share", "title": "NAND market share", "short": "Share",
                     "blocks": [bars(f"NAND revenue share {lq} (Counterpoint table via GetFlashMemory)", "%",
                                     sorted(peers, key=lambda x: -x[1])),
                                series("YMTC NAND revenue share (Counterpoint page)", "%", cp),
                                table("Counterpoint series side by side", ["quarter", "Counterpoint page", "via GetFlashMemory"], side),
                                table("Other sources (annual, point-in-time, forecasts)", ["period", "value", "source", "note"],
                                      [([r["period"], fmt(r), _src_cell(r), (r["notes"] or "")[:34]], src(r)) for r in others]),
                                table("Bit shipments (Counterpoint unless noted)", ["metric", "period", "value", "source"],
                                      [([label_of(r["metric"]), r["period"], fmt(r), _src_cell(r)], src(r)) for r in ship_rows]),
                                kv("Revenue cross-checks", checks)]})

    # 6. Layer-count roadmap ----------------------------------------------------------------
    lc = _rows(f, "layer_count")
    gate = _one(f, "layer_count", "2025-02-07")
    road = [([r["period"], fmt(r), r["basis"].replace("_", " "), _src_cell(r), (r["notes"] or "")[:40]], src(r)) for r in lc]
    dens = [([r["period"], f"{r['value']:.1f} Gb/mm2", _src_cell(r), (r["notes"] or "")[:40]], src(r))
            for r in _rows(f, "bit_density_gb_per_mm2")]
    gt = text("Gates vs active layers",
              "Layer counts are not one measure. TechInsights counted 294 gates in the Xtacking 4.0 die (150 on the lower "
              "deck, 144 on the upper): every gate line in the stack, including dummy and select gates. Active word-line "
              "layers that store data are fewer, which is why the same generation is reported as 267 (IPO filing "
              "coverage, 'in mass production') and 270 (TrendForce). 232 is the 2022 Xtacking 3.0 part. Korea Herald "
              "reports 300+ layers planned for 2026; peers' figures (SK hynix 321, Samsung 286) are also active-layer counts.")
    if gate:
        gt["src"] = src(gate)
    sections.append({"id": "layers", "title": "Layer roadmap", "short": "Layers",
                     "blocks": [{"type": "series", "title": "Reported layer count by date", "unit": "layers",
                                 "points": [{"x": r["period"][:7], "y": r["value"], "src": src(r)} for r in lc if r["basis"] != "forecast"]},
                                table("Layer counts", ["date", "value", "basis", "source", "note"], road), gt,
                                table("Bit density", ["date", "density", "source", "note"], dens)]})

    # 7. Funding & valuation ----------------------------------------------------------------
    fund = []
    for m in ("government_investment", "big_fund_investment", "registered_capital", "fab2_investment",
              "funding_round_size", "investor_contribution", "valuation", "subsidiary_share_of_group_revenue"):
        for r in _rows(f, m):
            fund.append(([label_of(m), r["period"], fmt(r), _src_cell(r), (r["notes"] or "")[:30]], src(r)))
    fund.sort(key=lambda x: x[0][1])
    vals = [(f"{r['period'][:7]} {_src_cell(r)[:12]}", r["value"], src(r)) for r in _rows(f, "valuation")]
    if ipo_val:
        vals.append(("2026-08 IPO midpoint", ipo_val["value"], src(ipo_val)))
    imp = []
    ic = _one(f, "investor_contribution")
    if ic:
        imp.append(("Implied post-money from Quan Hong stake", f"{_cny(ic['value'] / 0.0099)} est",
                    derived("1.6bn yuan for a 0.99% stake", f"{ic['value']} / 0.99% = {ic['value'] / 0.0099:,.1f}", [ic])))
    sections.append({"id": "funding", "title": "Funding & valuation", "short": "Funding",
                     "blocks": [bars("Valuation marks (CNY B)", "CNY B", vals), kv("Checks", imp),
                                table("State funding, capital and rounds", ["item", "date", "value", "source", "note"], fund),
                                text("Note", "Registered capital moves are registry data seen through press: over CNY 105B "
                                     "after the 2023 state injection (eeNews, Bloomberg/Tianyancha), then YMTC Holding cut "
                                     "to CNY 17.8B (Caixin; dated Sept 2025 in one place and Sept 2023 in another). The "
                                     "Big Fund and Hubei Changsheng withdrew from the Phase II fab in 2023.")]})

    # 8. IPO --------------------------------------------------------------------------------
    ipo = []
    if raise_t:
        ipo.append(("Raise target (STAR Market)", fmt(raise_t) + " ($4.9B)", src(raise_t)))
    pc, pr = _one(f, "ipo_proceeds_capex"), _one(f, "ipo_proceeds_rnd")
    if pc and pr:
        ipo.append(("Use of proceeds: capex", fmt(pc), src(pc)))
        ipo.append(("Use of proceeds: R&D", fmt(pr), src(pr)))
        ipo.append(("Capex + R&D", _cny(pc["value"] + pr["value"]),
                    derived("sum of uses vs 33bn target", f"{pc['value']} + {pr['value']}", [pc, pr] + ([raise_t] if raise_t else []))))
    if ipo_val:
        ipo.append(("Post-listing valuation", "CNY 275-330B (mid 302.5)", src(ipo_val)))
    kh = _one(f, "ipo_valuation", "2026-04-07")
    if kh:
        ipo.append(("Pre-filing expectation (Apr 2026)", ">$40B (forecast)", src(kh)))
    ipo.append(("Status", "reported on hold (Reuters, 2026-11-04)", hold_src))
    mult = []
    if ipo_val:
        v = ipo_val["value"]
        if fx:
            mult.append(("Midpoint in USD (est)", f"${v / fx[0]:.1f}B est",
                         derived("CNY midpoint / Caixin-implied rate", f"{v} / (33 / 4.9) = {v / fx[0]:,.1f}", [ipo_val, fx[1]])))
        if "2025" in ni:
            mult.append(("P/E on 2025 profit (est)", f"{v / ni['2025']['value']:.1f}x est",
                         derived("midpoint / 2025 net profit", f"{v} / {ni['2025']['value']}", [ipo_val, ni["2025"]])))
        if "2025" in rev:
            mult.append(("P/S on 2025 revenue (est)", f"{v / rev['2025']['value']:.1f}x est",
                         derived("midpoint / 2025 revenue", f"{v} / {rev['2025']['value']}", [ipo_val, rev["2025"]])))
        if ni_q1:
            mult.append(("P/E on Q1 2026 x 4 (est)", f"{v / (ni_q1['value'] * 4):.1f}x est",
                         derived("midpoint / (Q1 2026 profit x 4); assumes Q1 run-rate holds all year",
                                 f"{v} / ({ni_q1['value']} x 4)", [ipo_val, ni_q1])))
    sections.append({"id": "ipo", "title": "IPO", "short": "IPO",
                     "blocks": [kv("CCSH STAR Market IPO", ipo), kv("Implied multiples at the midpoint", mult),
                                text("Who lists", "The issuer is CCSH, the holding company above YMTC; YMTC Co. produces "
                                     "over 90% of group revenue (Admirals). The ~CNY 300B valuation is set against Q1 2026 "
                                     "earnings at the peak of a NAND price spike, so the run-rate multiple is far lower "
                                     "than the 2025 one.")]})

    # 9. Sanctions & lawsuits ---------------------------------------------------------------
    ev = [
        ("entity_list_firms_added", "US adds YMTC (and its Japan unit) to the Entity List"),
        ("equipment_order_cut", "YMTC cuts orders with Naura after Oct 2022 export controls"),
        ("nand_market_share", "Analyst: share to fall due to US sanctions"),
        ("fab2_investment", "Big Fund, Hubei Changsheng pull out of Phase II fab"),
        ("government_investment", "State investors inject capital after sanctions"),
        ("patents_asserted_vs_micron", "YMTC sues Micron in N.D. Cal. over 8 patents"),
        ("fab3_domestic_tool_share", "Fab 3 to use domestic tools for at least half"),
    ]
    tl = []
    for m, desc in ev:
        for r in _rows(f, m):
            if m == "nand_market_share" and r["period"] != "2023":
                continue
            if m == "government_investment" and r["period"][:4] != "2023":
                continue
            tl.append(([r["period"], desc, fmt(r), _src_cell(r)], src(r)))
    loss = ni.get("2023")
    if loss:
        tl.append((["2023", "Net loss in first year under controls (memory downturn)", fmt(loss), _src_cell(loss)], src(loss)))
    def _tk(p: str) -> str:
        if len(p) == 6 and p[4] == "Q":
            return f"{p[:4]}-{(int(p[5]) - 1) * 3 + 1:02d}"
        return p if len(p) > 4 else p + "-99"
    tl.sort(key=lambda x: _tk(x[0][0]))
    sections.append({"id": "sanctions", "title": "Sanctions & lawsuits", "short": "Sanctions",
                     "blocks": [table("Timeline", ["date", "event", "value", "source"], tl),
                                text("Gaps", "The research rows cover the Dec 2022 Entity List listing, the 2023 fallout "
                                     "and the Nov 2023 patent suit against Micron. No sourced rows were collected for later "
                                     "steps (Micron's countersuits, US defense lists, the outcome of the patent cases), so "
                                     "they are left out rather than stated without a source.")]})

    # 10. Sources ---------------------------------------------------------------------------
    mine = [r for r in f.rows if r["company"] == C]
    conf = conflicts(f, [C])
    cnt = {"label": "count of data/memory_facts rows with company = YMTC (conflicts: same period and metric, different values)", "url": None}
    per = {}
    for r in mine:
        k = (r["source_name"] or "").split(":")[0]
        per.setdefault(k, [0, r["source_url"]])[0] += 1
    srcs = sorted(per.items(), key=lambda kv_: -kv_[1][0])
    sections.append({"id": "sources", "title": "Sources", "short": "Sources",
                     "blocks": [kv("Coverage", [("Sourced numbers (YMTC)", f"{len(mine)}", cnt),
                                                ("Distinct source pages", f"{len({r['source_url'] for r in mine})}", cnt),
                                                ("Conflicting values", f"{len(conf)}", cnt)]),
                                text("Financials", PROSPECTUS_NOTE),
                                table("Where sources disagree", ["company", "metric", "period", "value", "source"], conf),
                                table("Sources by row count", ["source", "rows"],
                                      [([k[:48], str(n)], {"label": k, "url": u}) for k, (n, u) in srcs])]})

    return {"ticker": TICKER, "name": "YMTC", "industry": "3D NAND flash (unlisted; parent CCSH STAR IPO filed)",
            "country": "CN", "built_at": now,
            "freshness": [{"source": "memory_facts", "pulled": now}],
            "sections": sections, "unsourced": []}
