"""SK hynix memory page (flagship): OpenDART totals, 424B4 DRAM/NAND split, two HBM revenue
estimates (A: DRAM revenue x HBM share of DRAM; B: HBM market size x HBM market share),
market shares, capex and fabs, HBM roadmap and customers, the July 2026 Nasdaq ADR listing."""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean

import duckdb

from core.paths import DATA_ROOT
from derive.memory_page import (Facts, src, derived, fmt, label_of, series, kv, table, bars, text,
                                qoq_table, facts_table, conflicts, qkey)

TICKER = "000660.KS"
C = "SK hynix"
DART = DATA_ROOT / "dart" / "facts.parquet"
REPORT = {"11013": "1Q report", "11012": "half-year report", "11014": "3Q report", "11011": "annual report"}

# Korea Herald Q2 2026 results article: the gain behind net income > revenue in 2026Q2. Not in
# memory_facts; read from the article itself (quote verbatim).
KH_Q2_URL = "https://www.koreaherald.com/article/10823621"
KH_GAIN = {"company": C, "period": "2026Q2", "metric": "investment_asset_gain", "value": 63.3,
           "unit": "krw_trillion", "basis": "company_stated", "source_name": "Korea Herald, Q2 2026 earnings",
           "source_url": KH_Q2_URL, "published": "2026-07-29",
           "quote": "It includes 63.3 trillion won in gains from selling and revaluing investment assets ... "
                    "most of which is from the company's stake in Japanese flash memory maker Kioxia."}


# ---- local helpers -----------------------------------------------------------------------------

def _s(r: dict) -> dict:
    """Source of a facts row or a DART row (DART rows carry their own `_src`)."""
    return r["_src"] if "_src" in r else src(r)


def _series(title: str, unit: str, rows: dict[str, dict], scale: float = 1.0) -> dict:
    return {"type": "series", "title": title, "unit": unit,
            "points": [{"x": p, "y": round(r["value"] * scale, 4), "src": _s(r)} for p, r in rows.items()]}


def _qoq(title: str, rows: dict[str, dict], col: str = "value") -> dict:
    out, prev = [], None
    for p, r in rows.items():
        if prev and prev["value"] and prev["value"] > 0:
            g = r["value"] / prev["value"] - 1
            s = {"label": f"{p} vs {prev['period']}: QoQ", "formula": f"{r['value']:,.4f} / {prev['value']:,.4f} - 1",
                 "inputs": [_s(r), _s(prev)]}
            out.append(([p, fmt(r), f"{g * 100:+.1f}%"], s))
        else:
            out.append(([p, fmt(r), "—"], _s(r)))
        prev = r
    return table(title, ["quarter", col, "QoQ"], list(reversed(out)))


def _dart() -> dict[tuple[str, str], dict]:
    """(period, account) -> pseudo facts row (krw_trillion) with its OpenDART source.
    period: '2025Q1' for quarters, 'FY2025' for full years."""
    con = duckdb.connect()
    rows = con.execute(f"""SELECT year, quarter, reprt_code, account, value_krw, basis, formula, url
                           FROM read_parquet('{DART}') WHERE ticker = ? ORDER BY year, quarter""", [TICKER]).fetchall()
    out = {}
    for year, q, code, acct, v, basis, formula, url in rows:
        period = f"FY{year}" if q == 0 else f"{year}Q{q}"
        t = v / 1e12
        rep = REPORT.get(str(code), "filing")
        if basis == "derived":
            s = {"label": f"OpenDART {year} {rep}: {period} {acct.replace('_', ' ')} = full year minus Q1-Q3",
                 "formula": f"{formula} (KRW)", "inputs": [{"label": f"OpenDART {year} {rep}", "url": url}]}
        else:
            s = {"label": f"OpenDART {year} {rep} (K-IFRS consolidated): {period} {acct.replace('_', ' ')} "
                          f"KRW {v:,.0f}", "url": url}
        out[(period, acct)] = {"company": C, "period": period, "metric": acct, "value": t, "unit": "krw_trillion",
                               "basis": "reported", "_src": s}
    return out


def _krw_q(f: Facts, dart: dict, metric: str) -> dict[str, dict]:
    """Quarterly KRW trillion series: DART first, then memory_facts quarters DART does not have yet."""
    q = {p: r for (p, a), r in dart.items() if a == metric and not p.startswith("FY")}
    for p, r in f.quarterly(C, metric).items():
        if p not in q and r["unit"] == "krw_trillion":
            q[p] = r
    return dict(sorted(q.items(), key=lambda kv: qkey(kv[0])))


def _usd_b(r: dict) -> float:
    return r["value"] / 1000 if r["unit"] == "usd_million" else r["value"]


ENCODED = {"hbm_generation_volume_start", "m15x_wafer_input_start", "yongin_fab1_cleanroom_open",
           "yongin_y2_cleanroom_open", "yongin_cluster_completion_year", "indiana_plant_operations_start",
           "sold_out_through_year", "hbm4_mass_production_system_ready"}
EXTRA_UNITS = {"usd": lambda v: f"${v:,.2f}", "krw": lambda v: f"KRW {v:,.0f}", "million": lambda v: f"{v:,.2f}M",
               "gbps": lambda v: f"{v:g} Gbps", "tb_per_s": lambda v: f"{v:g} TB/s", "multiple": lambda v: f"{v:g}x",
               "count": lambda v: f"{v:,.0f}"}


def fx(r: dict | None) -> str:
    """fmt() plus the units it lacks, and readable text for values that encode a year or HBM generation."""
    if not r:
        return "—"
    m = r["metric"]
    tail = f" ({r['basis'].replace('_', ' ')})" if r.get("basis") in ("estimate", "forecast", "guidance", "market_share") else ""
    if m == "hbm_generation_volume_start":
        return ("HBM4E" if r["value"] == 4.5 else f"HBM{r['value']:g}") + tail
    if m in ENCODED:
        return f"{r['period']}{tail}"
    if m in ("adr_offering_oversubscription", "hbm_demand_to_supply_ratio"):
        return f"{r['value']:g}x" + tail
    if r.get("unit") in EXTRA_UNITS:
        return EXTRA_UNITS[r["unit"]](r["value"]) + tail
    return fmt(r)


LABEL_FIX = (("hbm", "HBM"), ("adr ", "ADR "), ("ads ", "ADS "), ("lta ", "LTA "), ("p t7", "P&T7"), ("m15x", "M15X"),
             ("m17", "M17"), ("krw", "KRW"), ("kwpm", "(kwpm)"), ("ipo ", "IPO "), ("euv", "EUV"), ("chips act", "CHIPS Act"),
             ("ddr5", "DDR5"), ("essd", "eSSD"), ("ssd", "SSD"), ("io count", "I/O count"), ("gbps", "(Gbps)"),
             ("8high", "8-high"), ("dram", "DRAM"), ("us NAND", "US NAND"), ("y2", "Y2"), ("fab1", "fab 1"),
             ("fab investment ", "investment: "), ("indiana", "Indiana"), ("nvidia", "Nvidia"), ("yongin", "Yongin"), ("cheongju", "Cheongju"))


def lbl(metric: str) -> str:
    s = label_of(metric)
    for a, b in LABEL_FIX:
        s = s.replace(a, b)
    return s[:1].upper() + s[1:]


def _rows(f: Facts, company: str, metrics: list[str]) -> list[tuple[list[str], dict]]:
    rs = [r for m in metrics for r in f.all(company, m)]
    rs.sort(key=lambda r: (r["period"] or "", r["metric"]), reverse=True)
    return [([lbl(r["metric"]), r["period"], fx(r)], src(r)) for r in rs]


def _ftable(title: str, f: Facts, company: str, metrics: list[str], first: str = "metric") -> dict:
    return table(title, [first, "period", "value"], _rows(f, company, metrics))


# ---- page --------------------------------------------------------------------------------------

def build(f: Facts) -> dict:
    dart = _dart()
    rev = _krw_q(f, dart, "revenue")
    opi = _krw_q(f, dart, "operating_income")
    ni = _krw_q(f, dart, "net_income")
    last = max(rev, key=qkey)
    prev = sorted(rev, key=qkey)[-2]
    fy = sorted({p for (p, a) in dart if p.startswith("FY")})
    sections = []

    # 1. Snapshot ---------------------------------------------------------------------------------
    lr, pr = rev[last], rev[prev]
    snap = [(f"Revenue {last}", fmt(lr), _s(lr)),
            ("Revenue QoQ", f"{(lr['value'] / pr['value'] - 1) * 100:+.1f}%",
             {"label": f"{last} vs {prev}", "formula": f"{lr['value']:,.4f} / {pr['value']:,.4f} - 1",
              "inputs": [_s(lr), _s(pr)]})]
    if last in opi:
        o = opi[last]
        snap += [(f"Operating income {last}", fmt(o), _s(o)),
                 ("Operating margin", f"{o['value'] / lr['value'] * 100:.1f}%",
                  {"label": f"{last} operating income / revenue", "formula": f"{o['value']:,.4f} / {lr['value']:,.4f}",
                   "inputs": [_s(o), _s(lr)]})]
    if fy:
        r = dart[(fy[-1], "revenue")]
        snap.append((f"Revenue {fy[-1]} (DART)", fmt(r), _s(r)))
    ds = f.best(C, "dram_share_of_revenue", "2026Q1")
    if ds:
        snap.append(("DRAM share of revenue 2026Q1", fmt(ds), src(ds)))
    hs = f.quarterly(C, "hbm_market_share", prefer="Counterpoint")
    if hs:
        p = max(hs, key=qkey)
        snap.append((f"HBM share {p} (Counterpoint)", fmt(hs[p]), src(hs[p])))
    dsh = f.quarterly(C, "dram_market_share", prefer="TrendForce")
    if dsh:
        p = max(dsh, key=qkey)
        snap.append((f"DRAM share {p}", fmt(dsh[p]), src(dsh[p])))
    for m, lbl in (("customer_share_nvidia", "Share of Nvidia HBM4 orders"), ("capex", None),
                   ("employees", "Employees"), ("adr_offering_net_proceeds", "ADR net proceeds (Jul 2026)")):
        if m == "capex":
            r = f.best(C, "capex", "FY2025")
            lbl = "Capex FY2025"
        else:
            r = f.best(C, m)
        if r:
            snap.append((lbl, fx(r), src(r)))
    sections.append({"id": "snapshot", "title": "Snapshot", "short": "Snapshot", "blocks": [
        kv("Latest", snap),
        text("What SK hynix is", "Korea's second memory maker and the HBM leader: DRAM (incl. HBM) is ~77% of revenue, "
             "NAND (incl. Solidigm, the former Intel NAND unit) most of the rest. Main supplier of HBM to Nvidia. "
             "Fabs in Icheon and Cheongju (M15X for HBM DRAM), Yongin cluster under construction, Wuxi and Dalian "
             "in China, an HBM packaging plant planned in Indiana. Listed in Seoul (000660) and, since July 2026, "
             "on Nasdaq as ADSs (SKHY). Totals here are OpenDART K-IFRS consolidated figures; the latest quarter "
             "not yet in DART comes from the earnings release.")]})

    # 2. Revenue ----------------------------------------------------------------------------------
    rq = {p: r for p, r in rev.items() if p >= "2022Q1"}
    fy_rows = []
    for p in reversed(fy):
        r = dart[(p, "revenue")]
        o = dart.get((p, "operating_income"))
        fy_rows.append(([p, fmt(r), fmt(o), f"{o['value'] / r['value'] * 100:.1f}%" if o else "—"], _s(r)))
    sections.append({"id": "revenue", "title": "Revenue", "short": "Revenue", "blocks": [
        _series("Quarterly revenue (OpenDART; latest from earnings release)", "KRW T", rq),
        _qoq("Revenue by quarter", rq, "revenue"),
        table("Full years (OpenDART annual reports)", ["year", "revenue", "op. income", "op. margin"], fy_rows),
        table("Company-stated growth", ["metric", "period", "value"],
              _rows(f, C, ["revenue_growth_qoq", "dram_revenue_growth_yoy", "nand_revenue_growth_yoy"]))]})

    # 3. DRAM vs NAND -----------------------------------------------------------------------------
    split_periods = sorted({r["period"] for m in ("dram_revenue", "nand_revenue") for r in f.all(C, m)
                            if r["unit"] == "krw_trillion"}, key=lambda p: (p.replace("FY", ""), p), reverse=True)
    split = []
    for p in split_periods:
        d = next((r for r in f.all(C, "dram_revenue") if r["period"] == p and r["unit"] == "krw_trillion"), None)
        n = next((r for r in f.all(C, "nand_revenue") if r["period"] == p and r["unit"] == "krw_trillion"), None)
        o = next((r for r in f.all(C, "other_revenue") if r["period"] == p and r["unit"] == "krw_trillion"), None)
        tot = dart.get((p, "revenue"))
        share = f"{d['value'] / tot['value'] * 100:.1f}%" if d and tot else "—"
        first = d or n
        split.append(([p, fx(d), fx(n), fx(o), share], src(first)))
    dram_tf = {p: r for p, r in f.quarterly(C, "dram_revenue", prefer="TrendForce").items() if r["unit"] == "usd_billion"}
    nand_tf = {p: r for p, r in f.quarterly(C, "nand_revenue", prefer="TrendForce").items() if r["unit"] == "usd_billion"}
    mix_blocks = [table("DRAM / NAND split (KRW; 424B4 'reported', 4Q25 via Futurum)",
                        ["period", "DRAM", "NAND", "other", "DRAM % (DART)"], split)]
    d26, n26, o26 = (f.best(C, m, "2026Q1") for m in ("dram_revenue", "nand_revenue", "other_revenue"))
    if d26 and n26 and o26:
        mix_blocks.append(bars("Revenue mix 2026Q1 (424B4)", "KRW T", [
            ("DRAM", d26["value"], src(d26)), ("NAND", n26["value"], src(n26)), ("Other", o26["value"], src(o26))]))
    mix_blocks += [_series("DRAM revenue, TrendForce estimate", "$B", dram_tf),
                   _series("NAND revenue (SK Group incl. Solidigm), TrendForce estimate", "$B", nand_tf)]
    sections.append({"id": "mix", "title": "DRAM vs NAND", "short": "Mix", "blocks": mix_blocks})

    # 4. HBM --------------------------------------------------------------------------------------
    sections.append({"id": "hbm", "title": "HBM", "short": "HBM", "blocks": _hbm(f)})

    # 5. Margins ----------------------------------------------------------------------------------
    om = {}
    for p, o in opi.items():
        r = rev.get(p)
        if r and p >= "2022Q1":
            om[p] = {"period": p, "value": o["value"] / r["value"] * 100,
                     "_src": {"label": f"{p} operating income / revenue",
                              "formula": f"{o['value']:,.4f} / {r['value']:,.4f}", "inputs": [_s(o), _s(r)]}}
    ni_rows = []
    for p in sorted(ni, key=qkey, reverse=True):
        if p < "2023Q1":
            continue
        n, r, o = ni[p], rev.get(p), opi.get(p)
        flag = "NI > revenue: one-off investment gain (Kioxia)" if r and n["value"] > r["value"] else ""
        ni_rows.append(([p, fmt(r), fmt(o), fmt(n), flag], _s(n)))
    main = [table("Quarterly P&L (OpenDART)", ["quarter", "revenue", "op. income", "net income", "note"], ni_rows),
            _series("Operating margin", "%", om),
            _series("Operating income", "KRW T", {p: r for p, r in opi.items() if p >= "2022Q1"})]
    m_blocks = []
    if ("2026Q2", "net_income") in dart:
        n, r, o = dart[("2026Q2", "net_income")], dart[("2026Q2", "revenue")], dart[("2026Q2", "operating_income")]
        m_blocks.append({"type": "text", "title": "2026Q2: net income exceeds revenue (one-off gain)",
                         "text": f"2026Q2 net income ({fmt(n)}) is larger than revenue ({fmt(r)}) because of a one-off, "
                                 f"non-operating gain of {fmt(KH_GAIN).split(' (')[0]} on selling and revaluing investment "
                                 "assets, mostly the stake in Kioxia. It is not operating profit: use operating income "
                                 f"({fmt(o)}) for run-rate earnings.",
                         "src": src(KH_GAIN)})
        m_blocks.append(kv("2026Q2 bridge", [
            ("Revenue", fmt(r), _s(r)), ("Operating income", fmt(o), _s(o)), ("Net income", fmt(n), _s(n)),
            ("Net income - operating income", f"KRW {n['value'] - o['value']:,.1f}T",
             {"label": "2026Q2 net income minus operating income", "formula": f"{n['value']:,.4f} - {o['value']:,.4f}",
              "inputs": [_s(n), _s(o)]}),
            ("Gain on selling / revaluing investments (pre-tax)", fmt(KH_GAIN).split(" (")[0], src(KH_GAIN))]))
    m_blocks += main
    rd = _rows(f, C, ["rd_expense"])
    if rd:
        m_blocks.append(table("R&D expense (424B4)", ["metric", "period", "value"], rd))
    sections.append({"id": "margins", "title": "Margins", "short": "Margins", "blocks": m_blocks})

    # 6. Bits & pricing ---------------------------------------------------------------------------
    sections.append({"id": "pricing", "title": "Bits & pricing", "short": "Pricing", "blocks": [
        series("DRAM bit shipments QoQ (company)", "%", f.quarterly(C, "dram_bit_growth_qoq")),
        series("DRAM ASP QoQ (company)", "%", f.quarterly(C, "dram_asp_change_qoq")),
        series("NAND bit shipments QoQ (company)", "%", f.quarterly(C, "nand_bit_growth_qoq")),
        series("NAND ASP QoQ (company)", "%", f.quarterly(C, "nand_asp_change_qoq")),
        series("DRAM contract price QoQ (industry, TrendForce)", "%",
               f.quarterly("Market", "dram_contract_price_change_qoq", prefer="TrendForce press release")),
        table("Demand guidance", ["metric", "period", "value"],
              _rows(f, C, ["dram_demand_growth_yoy", "hbm_demand_growth_yoy", "server_ssd_shipment_growth_yoy",
                           "server_ddr5_shipment_growth_qoq", "essd_revenue_growth_qoq", "essd_revenue_growth_yoy"]))]})

    # 7. Market share -----------------------------------------------------------------------------
    sections.append({"id": "share", "title": "Market share", "short": "Share", "blocks": _share(f)})

    # 8. Capex & fabs -----------------------------------------------------------------------------
    cap_fy = [r for r in f.all(C, "capex") if r["period"].startswith("FY")]
    cap_fy.sort(key=lambda r: r["period"])
    fab_metrics = sorted(m for (c, m) in f.by if c == C and (m.startswith(("fab_investment", "yongin", "m15x", "indiana"))
                                                            or m in ("long_term_investment_plan_total", "euv_scanner_purchase_cost",
                                                                     "solidigm_us_nand_fab_reported_investment")))
    sections.append({"id": "fabs", "title": "Capex & fabs", "short": "Fabs", "blocks": [
        bars("Capex, cash paid for PP&E (424B4)", "KRW T", [(r["period"], r["value"], src(r)) for r in cap_fy]),
        _ftable("Capex: quarters and guidance", f, C, ["capex", "capex_to_revenue_ratio"]),
        _ftable("Fabs and investment plans", f, C, fab_metrics, "item"),
        _ftable("Capacity (estimates)", f, C, ["wafer_capacity_kwpm", "dram_wafer_input_kwpm", "hbm_capacity_kwpm",
                                               "dram_1b_capacity_target_kwpm"])]})

    # 9. Tech & customers -------------------------------------------------------------------------
    tech = ["hbm_generation_volume_start", "hbm4_mass_production_system_ready", "hbm_io_count", "hbm_pin_speed_gbps",
            "hbm_power_efficiency_improvement", "hbm_stack_capacity", "hbm_stack_capacity_8high", "hbm_stack_height",
            "hbm_stack_bandwidth", "hbm_die_thinning", "hbm_heat_dissipation_improvement", "layer_count"]
    cust = ["customer_share_nvidia", "largest_customer_share_of_revenue", "long_term_supply_agreement_customers",
            "lta_share_of_capacity", "sold_out_through_year", "hbm_demand_to_supply_ratio"]
    sections.append({"id": "tech", "title": "Tech & customers", "short": "Tech", "blocks": [
        _ftable("HBM generations and specs (NAND: layer count)", f, C, tech, "item"),
        _ftable("Customers and demand", f, C, cust, "item"),
        text("Customers", "The 424B4 does not name customers: the largest took 23.9% of FY2025 revenue and 14.8% of "
             "2026Q1. Press reports put SK hynix at roughly two thirds of Nvidia's HBM4 (Vera Rubin) orders. "
             "HBM4 shipped in volume from 2026Q2, HBM4E targeted for 2027.")]})

    # 10. Listing & sources -----------------------------------------------------------------------
    adr = sorted(m for (c, m) in f.by if c == C and (m.startswith("adr_") or m in (
        "shares_outstanding_post_offering", "ipo_proceeds_use_capex_korea", "market_cap", "share_price_krw",
        "treasury_share_buyback", "shareholder_returns_plan")))
    conf = conflicts(f, [C])
    n_rows = sum(1 for r in f.rows if r["company"] == C)
    n_src = len({r["source_url"] for r in f.rows if r["company"] == C})
    sections.append({"id": "listing", "title": "ADR & sources", "short": "Listing", "blocks": [
        _ftable("Nasdaq ADR listing (SKHY, July 2026) and capital returns", f, C, adr, "item"),
        text("ADR listing", "SK hynix sold 177.9M ADSs at $149 on Nasdaq (ticker SKHY) in July 2026; 10 ADSs = 1 "
             "common share. Net proceeds about $26.2B, earmarked for Yongin Fab 1 and the P&T7 packaging fab in Korea."),
        kv("Coverage", [("Sourced numbers (SK hynix)", f"{n_rows}", None),
                        ("Distinct source pages", f"{n_src}", None),
                        ("OpenDART rows used", f"{len(dart)}", None),
                        ("Conflicting values", f"{len(conf)}", None)]),
        table("Where sources disagree", ["company", "metric", "period", "value", "source"], conf)]})

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {"ticker": TICKER, "name": "SK hynix", "industry": "DRAM, HBM and NAND flash", "country": "South Korea",
            "built_at": now,
            "freshness": [{"source": "memory_facts", "pulled": now}, {"source": "OpenDART", "pulled": now}],
            "sections": sections, "unsourced": []}


def _who(r: dict) -> str:
    t = (r.get("notes") or "") + " " + (r.get("source_name") or "")
    for k, v in (("Gartner", "Gartner"), ("Micron", "Micron TAM"), ("Yole", "Yole"), ("TrendForce", "TrendForce"),
                 ("Counterpoint", "Counterpoint"), ("IDC", "IDC")):
        if k in t:
            return v
    return (r.get("source_name") or "")[:20]


# ---- HBM tab -----------------------------------------------------------------------------------

def _hbm(f: Facts) -> list[dict]:
    blocks = []
    share = {p: r for p, r in f.quarterly(C, "hbm_share_of_dram_revenue").items()}
    dram_usd = {p: r for p, r in f.quarterly(C, "dram_revenue", prefer="TrendForce").items() if r["unit"] == "usd_billion"}
    dram_krw = {r["period"]: r for r in f.all(C, "dram_revenue") if r["unit"] == "krw_trillion" and r["basis"] == "reported"}

    # A: DRAM revenue x HBM share of DRAM revenue
    a_rows, a_pts = [], []
    for p, s in share.items():
        lb = " (lower bound)" if "lower bound" in (s["notes"] or "") else ""
        who = "company" if s["basis"] == "company_stated" else "Counterpoint est"
        for d, cur in ((dram_krw.get(p), "KRW"), (dram_usd.get(p), "USD")):
            if not d:
                continue
            v = d["value"] * s["value"] / 100
            vs = f"KRW {v:,.2f}T est{lb}" if cur == "KRW" else f"${v:,.2f}B est{lb}"
            dsrc = "424B4" if cur == "KRW" else "TrendForce"
            sx = derived(f"Method A {p}: SK hynix DRAM revenue ({dsrc}) x HBM share of DRAM revenue ({who})",
                         f"{d['value']:g} x {s['value']:g}% = {vs}", [d, s])
            draw = f"KRW {d['value']:,.2f}T" if cur == "KRW" else f"${d['value']:,.2f}B"
            a_rows.append(([p, f"{draw} ({dsrc}{' est' if d['basis'] == 'estimate' else ''})",
                            f"{s['value']:g}% ({who}{', >=' if lb else ''})", vs], sx))
            if cur == "USD":
                a_pts.append({"x": p, "y": round(v, 3), "src": sx})
    blocks.append(table("A. DRAM revenue x HBM share of DRAM revenue (estimate)",
                        ["quarter", "DRAM revenue", "HBM % of DRAM", "HBM revenue"], a_rows))

    # B: annual HBM market size x SK hynix annual HBM share
    cp = {p: r for p, r in f.quarterly(C, "hbm_market_share", prefer="Counterpoint").items()}
    sizes = sorted(f.all("Market", "hbm_market_size"), key=lambda r: r["period"])
    b_rows, b_bars = [], []
    for year in sorted({r["period"] for r in sizes}):
        mkt = [r for r in sizes if r["period"] == year and r["basis"] in ("estimate", "company_stated", "market_share")]
        if not mkt:
            continue
        shares = []
        qs = [cp[f"{year}Q{i}"] for i in range(1, 5) if f"{year}Q{i}" in cp]
        if len(qs) == 4:
            avg = mean(r["value"] for r in qs)
            shares.append((avg, f"{avg:.2f}% (mean of Counterpoint/press 1Q-4Q{year[2:]})", qs,
                           f"simple mean of the four quarterly revenue shares "
                           f"({' + '.join(f'{r['value']:g}' for r in qs)}) / 4; assumes equal quarterly HBM market size"))
        for r in f.all(C, "hbm_market_share"):
            if r["period"] == year:
                caveat = "Yole, likely 2024 basis" if "2024 basis" in (r["notes"] or "") else _who(r)
                shares.append((r["value"], f"{r['value']:g}% ({caveat})", [r],
                               f"annual share as published ({r['notes'] or r['basis']})"))
        for m in mkt:
            for sv, sl, sin, note in shares:
                v = _usd_b(m) * sv / 100
                vs = f"${v:,.1f}B est"
                if "lower bound" in (m["notes"] or "") or "surpassing" in (m["quote"] or ""):
                    vs += " (lower bound)"
                who = _who(m)
                sx = derived(f"Method B {year}: HBM market size ({who}) x SK hynix HBM share",
                             f"{_usd_b(m):g}B x {sv:.2f}% = {v:,.2f}B; share: {note}", [m] + sin)
                b_rows.append(([year, f"${_usd_b(m):g}B ({who})", sl, vs], sx))
                b_bars.append((f"{year} {who} x {sv:.0f}%", round(v, 2), sx))
    blocks.append(table("B. HBM market size x SK hynix HBM share (annual estimate)",
                        ["year", "HBM market", "SK hynix share", "HBM revenue"], b_rows))

    # side by side
    side = []
    a_note = "; ".join(f"{pt['x']} ${pt['y']:.2f}B" for pt in a_pts)
    if a_pts and b_bars:
        side = [("Method A, quarterly (USD, TrendForce DRAM)", a_note + " est",
                 {"label": "Method A quarterly estimates", "formula": "DRAM revenue x HBM share of DRAM revenue",
                  "inputs": [pt["src"] for pt in a_pts]}),
                ("Method A annualised 1Q25 x 4", f"${a_pts[-1]['y'] * 4:,.1f}B est (run-rate, not a forecast)",
                 {"label": "Method A run-rate", "formula": f"{a_pts[-1]['y']:.3f}B x 4 (assumes flat quarters)",
                  "inputs": [a_pts[-1]["src"]]}) if a_pts[-1]["x"] == "2025Q1" else None]
        b25 = [b for b in b_bars if b[0].startswith("2025")]
        if b25:
            lo, hi = min(b25, key=lambda b: b[1]), max(b25, key=lambda b: b[1])
            side.append(("Method B, 2025 range", f"${lo[1]:,.1f}B to ${hi[1]:,.1f}B est",
                         {"label": "Method B 2025 low / high", "formula": f"min {lo[0]} = {lo[1]}B; max {hi[0]} = {hi[1]}B",
                          "inputs": [lo[2], hi[2]]}))
        side = [x for x in side if x]
    if side:
        blocks.append(kv("A vs B (estimates, not reported)", side))
    if b_bars:
        blocks.append(bars("Method B estimates by input pair", "$B est", b_bars))
    blocks.append(series("SK hynix HBM revenue share, Counterpoint (quarterly)", "%", cp))
    blocks.append(series("HBM share of SK hynix DRAM revenue (company; 1Q25 Counterpoint)", "%", share))
    blocks.append(_ftable("Company-stated HBM growth (no KRW/USD HBM revenue is reported)", f, C,
                          ["hbm_revenue_growth_qoq", "hbm_revenue_growth_yoy", "hbm3_revenue_growth_yoy",
                           "hbm3e_12high_share_of_hbm3e_revenue", "hbm_share_of_dram_bits",
                           "hbm_share_of_dram_operating_profit", "hbm_bit_shipment_share"]))
    g = [r for r in f.all(C, "hbm_share_of_dram_revenue") if r["basis"] == "guidance"]
    if g:
        blocks.append(table("Guidance", ["metric", "period", "value"],
                            [([label_of(r["metric"]), r["period"], fx(r)], src(r)) for r in g]))
    blocks.append(text("How the estimates work",
                       "SK hynix does not report HBM revenue in won or dollars. A: DRAM revenue times the HBM share of "
                       "DRAM revenue, for quarters where the company (3Q24 30%, 4Q24 'over 40%') or Counterpoint "
                       "(1Q25 44%) gave a share. B: annual HBM market size (Gartner, Yole, Micron TAM) times SK hynix's "
                       "HBM share (Counterpoint quarterly shares averaged, or an annual figure). Every value marked est "
                       "is a derived estimate; the source bar shows the formula and inputs."))
    return blocks


# ---- Market share tab --------------------------------------------------------------------------

def _share(f: Facts) -> list[dict]:
    out = []
    lq = max(f.quarterly(C, "hbm_market_share", prefer="Counterpoint Research"), key=qkey, default=None)
    hbm_peers = []
    for comp in ("SK hynix", "Samsung", "Micron"):
        r = f.quarterly(comp, "hbm_market_share", prefer="Counterpoint").get(lq) if lq else None
        if r:
            hbm_peers.append((comp, r["value"], src(r)))
    out.append(bars(f"HBM revenue share {lq} (Counterpoint)", "%", sorted(hbm_peers, key=lambda x: -x[1])))
    dq = f.latest_quarter("dram_market_share", prefer="TrendForce")
    dram_peers = []
    for comp in ("Samsung", "SK hynix", "Micron", "CXMT", "Nanya"):
        r = f.quarterly(comp, "dram_market_share", prefer="TrendForce").get(dq) if dq else None
        if r:
            dram_peers.append((comp, r["value"], src(r)))
    out.append(bars(f"DRAM revenue share {dq} (TrendForce)", "%", sorted(dram_peers, key=lambda x: -x[1])))
    out.append(series("SK hynix DRAM share (TrendForce first)", "%", f.quarterly(C, "dram_market_share", prefer="TrendForce")))
    out.append(series("SK hynix HBM share (Counterpoint first)", "%", f.quarterly(C, "hbm_market_share", prefer="Counterpoint")))
    out.append(series("SK Group NAND share (TrendForce first)", "%", f.quarterly(C, "nand_market_share", prefer="TrendForce")))
    other = _rows(f, C, ["hbm3_market_share", "hbm4_market_share"]) + [
        r for r in _rows(f, C, ["hbm_market_share", "dram_market_share", "nand_market_share"])
        if "IDC" in r[1]["label"] or "Q" not in r[0][1]]
    out.append(table("Annual, IDC and other shares", ["metric", "period", "value"], other))
    return out
