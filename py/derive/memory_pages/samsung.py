"""Samsung Electronics memory page (005930.KS).

Samsung is a conglomerate, so the group totals come from OpenDART (data/dart/facts.parquet) and
the page is about the memory business inside it: Memory revenue from the IR decks, the Device
Solutions (DS) division from the results releases, and memory's share of DS and of the group
(derived). Samsung gives no HBM revenue and no HBM share of DRAM revenue, so HBM revenue is
estimated with method B only (annual HBM market size x Samsung HBM revenue share); its own
stated HBM growth rates and HBM4 mix are shown beside the estimate.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import duckdb

from core.paths import DATA_ROOT
from derive.memory_page import (BASIS_RANK, QUARTER, Facts, src, derived, fmt, label_of, series, kv, table, bars, text,  # noqa: F401
                                qoq_table, facts_table, conflicts, qkey)

TICKER = "005930.KS"
C = "Samsung"
DART = DATA_ROOT / "dart" / "facts.parquet"
REPORT = {"11013": "Q1 report", "11012": "half-year report", "11014": "Q3 report", "11011": "annual report"}
GEN = {3.0: "HBM3", 3.5: "HBM3E", 4.0: "HBM4", 4.5: "HBM4E", 5.0: "HBM5"}


# ---- local helpers ----------------------------------------------------------------------------

def fv(r: dict | None) -> str:
    """fmt() plus the units memory_page does not know (Gbps, GB/s, months, HBM generation codes)."""
    if not r:
        return "—"
    v, u, m = r["value"], r.get("unit") or "", r["metric"]
    if "generation" in m or m.endswith("volume_start_target"):
        s = GEN.get(v, f"gen {v:g}")
    elif u == "year":
        s = f"{v:.0f}"
    elif u == "months":
        s = f"{v:.0f} months"
    elif u == "gbps":
        s = f"{v:g} Gbps"
    elif u == "gb_per_s":
        s = f"{v:,.0f} GB/s"
    elif u == "tb_per_s":
        s = f"{v:g} TB/s"
    elif u in ("nm", "um"):
        s = f"{v:g} {u}"
    elif u == "x":
        s = f"{v:g}x"
    elif u == "count":
        s = f"{v:,.0f}"
    elif u == "tb":
        s = f"{v:g} TB"
    else:
        return fmt(r)
    if r.get("basis") in ("estimate", "forecast", "guidance", "market_share"):
        s += f" ({r['basis'].replace('_', ' ')})"
    return s


def dsrc(label: str, formula: str, inputs: list[dict]) -> dict:
    """derived() whose inputs are already source dicts (DART points, other derived values)."""
    return {"label": label, "formula": formula, "inputs": inputs}


def dart() -> dict[str, dict[str, dict]]:
    """account -> period ('2026Q2' or 'FY2025') -> {value (KRW T), src}."""
    con = duckdb.connect()
    rows = con.execute(f"""SELECT year, quarter, account, value_krw, basis, formula, reprt_code, url
                           FROM read_parquet('{DART}') WHERE ticker = ? ORDER BY year, quarter""",
                       [TICKER]).fetchall()
    out: dict[str, dict[str, dict]] = {}
    for y, q, acct, v, basis, formula, code, url in rows:
        if v is None:
            continue
        p = f"FY{y}" if q == 0 else f"{y}Q{q}"
        t = v / 1e12
        rep = REPORT.get(str(code), "report")
        lbl = f"OpenDART {y} {rep}: {acct.replace('_', ' ')} KRW {t:,.2f}T (consolidated)"
        if basis == "derived" and formula:
            s = {"label": f"OpenDART {p} {acct.replace('_', ' ')}: full year less Q1-Q3", "url": url,
                 "formula": f"{formula} (KRW)"}
        else:
            s = {"label": lbl, "url": url}
        out.setdefault(acct, {})[p] = {"value": t, "src": s, "period": p}
    return out


def pts(title: str, unit: str, d: dict[str, dict]) -> dict:
    """Series from period -> {value, src}, quarters only, time order."""
    qs = sorted((p for p in d if not p.startswith("FY")), key=qkey)
    return {"type": "series", "title": title, "unit": unit,
            "points": [{"x": p, "y": round(d[p]["value"], 4), "src": d[p]["src"]} for p in qs]}


def strict(f: Facts, comp: str, metric: str, prefer: str) -> dict[str, dict]:
    """Quarterly rows from one research firm only (no fallback to other firms)."""
    def firm(r):  # a note "<firm> via <outlet>" names the firm; otherwise the source name must
        m = re.match(r"^\s*(\w+) via ", r["notes"] or "")
        if m:
            return m.group(1).lower() == prefer.lower()
        return prefer.lower() in (r["source_name"] or "").lower() or (r["notes"] or "").lower().startswith(prefer.lower())

    by: dict[str, list[dict]] = {}
    for r in f.all(comp, metric):
        if r["basis"] not in ("guidance", "forecast") and QUARTER.match(r["period"] or "") and firm(r):
            by.setdefault(r["period"], []).append(r)
    return {p: min(rs, key=lambda r: (BASIS_RANK.get(r["basis"], 9), -len(r["quote"] or "")))
            for p, rs in sorted(by.items(), key=lambda kv: qkey(kv[0]))}


def lab(metric: str) -> str:
    s = " " + label_of(metric) + " "
    for a, b in (("hbm3e", "HBM3E"), ("hbm4e", "HBM4E"), ("hbm", "HBM"), ("dram", "DRAM"), ("cxl", "CXL"), ("cmm d", "CMM-D"), ("cmm b", "CMM-B"), ("hbm4e", "HBM4E"), ("hpb", "HPB"), ("chbm4", "cHBM4"),
                 ("lpddr5x", "LPDDR5X"), ("pim", "PIM"), ("qlc", "QLC"), ("v10", "V10"), ("v9", "V9"), (" 12h ", " 12H "),
                 (" 2 0 ", " 2.0 "), (" 3 1 ", " 3.1 "), ("kwpm", ""), (" p4 ", " P4 "), (" p5 ", " P5 "), ("xian", "Xi'an"),
                 (" us ", " US "), ("nvidia", "Nvidia"), ("google", "Google"), ("amd mi350", "AMD MI350"), (" 1c ", " 1c "),
                 (" io ", " IO "), ("12hi", "12-high"), ("hwaseong", "Hwaseong"), ("yongin", "Yongin"), ("chips act", "CHIPS Act")):
        s = s.replace(a, b)
    s = s.strip()
    return s if s[:1] in ("z", "c") and s[1:4] == "HBM" else s[:1].upper() + s[1:]


def rows_table(title: str, f: Facts, metrics: list[str], skip_guidance: bool = False, only_guidance: bool = False,
               company: str = C) -> dict:
    """One line per sourced row of `metrics`, newest first, values through fv()."""
    rs = [r for m in metrics for r in f.all(company, m)
          if not (skip_guidance and r["basis"] in ("guidance", "forecast"))
          and not (only_guidance and r["basis"] not in ("guidance", "forecast"))]
    rs.sort(key=lambda r: (r["period"] or ""), reverse=True)
    return table(title, ["metric", "period", "value"], [([lab(r["metric"]), r["period"], fv(r)], src(r)) for r in rs])


def pct(a: float, b: float) -> str:
    return f"{a / b * 100:.1f}%"


# ---- page -------------------------------------------------------------------------------------

def build(f: Facts) -> dict:
    d = dart()
    grev, gop, gni = d.get("revenue", {}), d.get("operating_income", {}), d.get("net_income", {})
    mem = f.quarterly(C, "memory_division_revenue")
    dsr = f.quarterly(C, "ds_division_revenue", prefer="Newsroom")
    dso = f.quarterly(C, "ds_division_operating_income", prefer="Newsroom")
    last = max(mem, key=qkey) if mem else None
    qs_mem = sorted(mem, key=qkey)
    prev = qs_mem[-2] if len(qs_mem) > 1 else None
    yago = f"{int(last[:4]) - 1}{last[4:]}" if last else None
    gq = max((p for p in grev if not p.startswith("FY")), key=qkey) if grev else None

    sections = []

    # 1. Snapshot -------------------------------------------------------------------------------
    snap = []
    if last:
        m = mem[last]
        snap.append((f"Memory revenue {last}", fmt(m), src(m)))
        if prev:
            p = mem[prev]
            snap.append(("Memory revenue QoQ", f"{(m['value'] / p['value'] - 1) * 100:+.1f}%",
                         derived(f"{last} vs {prev}", f"{m['value']:,.2f} / {p['value']:,.2f} - 1", [m, p])))
        if yago in mem:
            p = mem[yago]
            snap.append(("Memory revenue YoY", f"{(m['value'] / p['value'] - 1) * 100:+.0f}%",
                         derived(f"{last} vs {yago}", f"{m['value']:,.2f} / {p['value']:,.2f} - 1", [m, p])))
        if last in dsr:
            s = dsr[last]
            snap.append((f"DS division revenue {last}", fmt(s), src(s)))
            snap.append(("Memory share of DS revenue", pct(m["value"], s["value"]),
                         derived(f"{last} memory / DS", f"{m['value']:,.2f} / {s['value']:,.2f}", [m, s])))
        if last in dso:
            o = dso[last]
            snap.append((f"DS operating income {last}", fmt(o), src(o)))
            if last in dsr:
                snap.append(("DS operating margin", pct(o["value"], dsr[last]["value"]),
                             derived(f"{last} DS OI / DS revenue", f"{o['value']:,.2f} / {dsr[last]['value']:,.2f}",
                                     [o, dsr[last]])))
    if gq:
        g = grev[gq]
        snap.append((f"Group revenue {gq} (DART)", f"KRW {g['value']:,.1f}T", g["src"]))
        if gq in mem:
            snap.append((f"Memory share of group {gq}", pct(mem[gq]["value"], g["value"]),
                         dsrc(f"{gq} memory / group revenue", f"{mem[gq]['value']:,.2f} / {g['value']:,.2f}",
                              [src(mem[gq]), g["src"]])))
        if gq in gop:
            snap.append((f"Group operating income {gq}", f"KRW {gop[gq]['value']:,.1f}T", gop[gq]["src"]))
            if gq in dso:
                snap.append((f"DS share of group OI {gq}", pct(dso[gq]["value"], gop[gq]["value"]),
                             dsrc(f"{gq} DS OI / group OI", f"{dso[gq]['value']:,.2f} / {gop[gq]['value']:,.2f}",
                                  [src(dso[gq]), gop[gq]["src"]])))
    for metric, lbl, prefer in (("dram_market_share", "DRAM share", "Counterpoint"),
                                ("hbm_market_share", "HBM share", "Counterpoint"),
                                ("nand_market_share", "NAND share", "TrendForce")):
        q = strict(f, C, metric, prefer)
        if q:
            p = max(q, key=qkey)
            snap.append((f"{lbl} {p} ({prefer})", fmt(q[p]), src(q[p])))
    r = f.best(C, "hbm4_share_of_hbm_revenue", "2026Q3")
    if r:
        snap.append(("HBM4 share of HBM revenue 2026Q3", fv(r), src(r)))
    r = f.best(C, "capex_ds_division", "2026")
    if r:
        snap.append(("DS capex 2026 (guidance)", fv(r), src(r)))
    sections.append({"id": "snapshot", "title": "Snapshot", "short": "Snapshot",
                     "blocks": [kv("Latest", snap),
                                text("What Samsung memory is",
                                     "Samsung Electronics is a conglomerate (phones, TVs, appliances, chips). Its Device "
                                     "Solutions (DS) division holds Memory, System LSI and Foundry; Memory (DRAM, HBM, "
                                     "NAND/SSD) is the largest of the three. Group totals here are OpenDART consolidated "
                                     "filings; Memory revenue is the 'Sales by business' row of the quarterly IR deck; DS "
                                     "revenue and operating income are from the results releases. Samsung does not report "
                                     "memory operating income or HBM revenue, so those appear only as estimates.")]})

    # 2. Group (OpenDART) ---------------------------------------------------------------------
    margin = {p: {"value": gop[p]["value"] / grev[p]["value"] * 100, "period": p,
                  "src": dsrc(f"{p} operating income / revenue",
                              f"{gop[p]['value']:,.3f} / {grev[p]['value']:,.3f}", [gop[p]["src"], grev[p]["src"]])}
              for p in grev if p in gop and not p.startswith("FY")}
    fy = sorted((p for p in grev if p.startswith("FY")), reverse=True)
    fy_rows = [([p, f"KRW {grev[p]['value']:,.1f}T",
                 f"KRW {gop[p]['value']:,.1f}T" if p in gop else "—",
                 f"KRW {gni[p]['value']:,.1f}T" if p in gni else "—"], grev[p]["src"]) for p in fy]
    sections.append({"id": "group", "title": "Group (DART)", "short": "Group",
                     "blocks": [pts("Group revenue (consolidated)", "KRW T", grev),
                                pts("Group operating income", "KRW T", gop),
                                pts("Group operating margin", "%", margin),
                                pts("Group net income", "KRW T", gni),
                                table("Full years (OpenDART)", ["year", "revenue", "op. income", "net income"], fy_rows),
                                text("Note", "OpenDART quarterly filings: Q4 is the annual report less Q1-Q3. The "
                                     f"latest filing in the data is {gq}; the 2026Q3 report is not yet in data/dart.")]})

    # 3. Memory vs DS -------------------------------------------------------------------------
    share_g = {}
    mix_rows = []
    for q in sorted(set(mem) | set(dsr), key=qkey, reverse=True):
        m, s, g = mem.get(q), dsr.get(q), grev.get(q)
        cells = [q, fmt(m) if m else "—", fmt(s) if s else "—",
                 pct(m["value"], s["value"]) if m and s else "—",
                 f"KRW {g['value']:,.1f}T" if g else "—",
                 pct(m["value"], g["value"]) if m and g else "—"]
        ins, parts = [], []
        if m and s:
            parts.append(f"memory/DS = {m['value']:,.2f} / {s['value']:,.2f}")
            ins += [src(m), src(s)]
        if m and g:
            parts.append(f"memory/group = {m['value']:,.2f} / {g['value']:,.3f}")
            ins += ([] if s else [src(m)]) + [g["src"]]
            share_g[q] = {"value": m["value"] / g["value"] * 100, "period": q,
                          "src": dsrc(f"{q} memory / group revenue", f"{m['value']:,.2f} / {g['value']:,.3f}",
                                      [src(m), g["src"]])}
        rs = dsrc(f"{q} memory, DS and group revenue", "; ".join(parts), ins) if parts else (src(m) if m else src(s))
        mix_rows.append((cells, rs))
    ds_margin = {q: {"value": dso[q]["value"] / dsr[q]["value"] * 100, "period": q,
                     "src": derived(f"{q} DS OI / DS revenue", f"{dso[q]['value']:,.2f} / {dsr[q]['value']:,.2f}",
                                    [dso[q], dsr[q]])}
                 for q in dsr if q in dso}
    mop = f.all(C, "memory_division_operating_income")
    sections.append({"id": "memory", "title": "Memory vs DS", "short": "Memory",
                     "blocks": [series("Memory revenue (IR deck)", "KRW T", mem),
                                qoq_table("Memory revenue by quarter", mem),
                                table("Memory in DS and in the group (KRW T)",
                                      ["quarter", "Memory", "DS", "mem/DS", "group", "mem/group"], mix_rows),
                                pts("Memory share of group revenue", "%", share_g),
                                series("DS division revenue", "KRW T", dsr),
                                series("DS operating income", "KRW T", dso),
                                pts("DS operating margin", "%", ds_margin),
                                table("Memory operating income (not disclosed; estimates only)",
                                      ["period", "value", "source"],
                                      [([r["period"], fv(r), (r["source_name"] or "")[:40]], src(r)) for r in mop])]})

    # 4. DRAM & NAND --------------------------------------------------------------------------
    dram = strict(f, C, "dram_revenue", "TrendForce")
    nand = strict(f, C, "nand_revenue", "TrendForce")
    dn_rows = []
    for q in sorted(set(dram) | set(nand), key=qkey, reverse=True):
        a, b = dram.get(q), nand.get(q)
        if a and b:
            s = derived(f"{q} DRAM / (DRAM + NAND)", f"{a['value']:,.2f} / ({a['value']:,.2f} + {b['value']:,.2f})", [a, b])
            sh = pct(a["value"], a["value"] + b["value"])
        else:
            s, sh = src(a or b), "—"
        dn_rows.append(([q, fmt(a) if a else "—", fmt(b) if b else "—", sh], s))
    bit_guid = [r for m in ("dram_bit_growth_qoq", "nand_bit_growth_qoq") for r in f.all(C, m) if r["basis"] == "guidance"]
    bit_guid.sort(key=lambda r: qkey(r["period"]), reverse=True)
    sections.append({"id": "dramnand", "title": "DRAM & NAND", "short": "DRAM/NAND",
                     "blocks": [series("DRAM revenue (TrendForce est, incl. HBM)", "$B", dram),
                                series("NAND revenue (TrendForce est)", "$B", nand),
                                table("DRAM vs NAND (TrendForce estimates)", ["quarter", "DRAM", "NAND", "DRAM share"], dn_rows),
                                series("DRAM bit growth QoQ (company stated)", "%", f.quarterly(C, "dram_bit_growth_qoq")),
                                series("DRAM ASP change QoQ (company stated)", "%", f.quarterly(C, "dram_asp_change_qoq")),
                                series("NAND bit growth QoQ (company stated)", "%", f.quarterly(C, "nand_bit_growth_qoq")),
                                series("NAND ASP change QoQ (company stated)", "%", f.quarterly(C, "nand_asp_change_qoq")),
                                table("Bit growth guidance", ["metric", "quarter", "guided"],
                                      [([lab(r["metric"]), r["period"], fv(r)], src(r)) for r in bit_guid]),
                                rows_table("Other stated bit and price moves", f,
                                           ["conventional_dram_bit_growth_qoq", "conventional_dram_asp_change_qoq",
                                            "server_dram_bit_growth_qoq", "memory_inventory_writedown"]),
                                series("DRAM contract price change QoQ (industry, TrendForce)", "%",
                                       strict(f, "Market", "dram_contract_price_change_qoq", "TrendForce")),
                                text("Note", "Samsung states bit growth and ASP moves in words ('mid-teens %'); the "
                                     "values are the midpoints of those ranges. DRAM and NAND revenue are not reported "
                                     "by Samsung; the USD figures are TrendForce estimates.")]})

    # 5. HBM -----------------------------------------------------------------------------------
    hshare = strict(f, C, "hbm_market_share", "Counterpoint")
    sizes = {y: [r for r in f.all("Market", "hbm_market_size") if r["period"] == y
                 and not ("TrendForce" in (r["notes"] or "") and r["value"] < 10)]  # stale TrendForce rows, see report
             for y in ("2023", "2024", "2025")}
    hb_rows, est25 = [], []

    def mk(r):  # "$34.0B Yole fcst"
        name = (r["notes"] or r["source_name"] or "").split()[0].rstrip(";,")
        return f"${r['value']:,.1f}B {name}" + (" fcst" if r["basis"] == "forecast" else "")

    sh23 = f.best(C, "hbm_market_share", "2023")
    for r in sizes["2023"]:
        if sh23:
            v = r["value"] * sh23["value"] / 100
            hb_rows.append((["2023", mk(r), f"{sh23['value']:.0f}% TF fcst", f"${v:,.2f}B est"],
                            derived("2023 Samsung HBM revenue est (method B)",
                                    f"{r['value']:g} x {sh23['value']:g}% = {v:,.2f} ($B); share is TrendForce's "
                                    "Apr-2023 forecast for 2023", [r, sh23])))
    sh24 = f.best(C, "hbm_bit_shipment_share", "2024Q2")
    for r in sizes["2024"]:
        if sh24:
            v = r["value"] * sh24["value"] / 100
            hb_rows.append((["2024", mk(r), f"{sh24['value']:.0f}% bit, 2Q", f"${v:,.2f}B est"],
                            derived("2024 Samsung HBM revenue est (method B, proxy share)",
                                    f"{r['value']:g} x {sh24['value']:g}% = {v:,.2f} ($B); assumption: Counterpoint's "
                                    "2024Q2 BIT share stands in for the full-year revenue share (no 2024 revenue share "
                                    "in data)", [r, sh24])))
    q25 = [hshare[q] for q in ("2025Q1", "2025Q2", "2025Q3", "2025Q4") if q in hshare]
    if q25:
        avg = sum(r["value"] for r in q25) / len(q25)
        for r in sorted(sizes["2025"], key=lambda r: r["value"]):
            v = r["value"] * avg / 100
            est25.append((v, r))
            hb_rows.append((["2025", mk(r), f"{avg:.1f}% CP avg", f"${v:,.2f}B est"],
                            derived("2025 Samsung HBM revenue est (method B)",
                                    f"{r['value']:g} x {avg:.2f}% = {v:,.2f} ($B); share = simple mean of Counterpoint "
                                    f"quarterly revenue shares {', '.join(q['period'] for q in q25)} "
                                    f"({' + '.join(f'{q['value']:g}' for q in q25)}) / {len(q25)}; quarters not "
                                    "weighted by market size; 2025Q1 not in data",
                                    [r] + q25)))
    g26 = f.best(C, "hbm_revenue_growth_yoy", "2026")
    if est25 and g26:
        lo, hi = min(est25, key=lambda x: x[0]), max(est25, key=lambda x: x[0])
        mult = 1 + g26["value"] / 100
        hb_rows.append((["2026", "—", f"x{mult:g} guided", f"${lo[0] * mult:,.1f}-{hi[0] * mult:,.1f}B est"],
                        dsrc("2026 Samsung HBM revenue est (2025 method-B est x guided growth)",
                             f"({lo[0]:,.2f} to {hi[0]:,.2f}) x {mult:g} = {lo[0] * mult:,.1f} to {hi[0] * mult:,.1f} ($B); "
                             "lower bound, since Samsung guided 'more than threefold'; inherits the 2025 assumptions",
                             [src(g26), src(lo[1]), src(hi[1])] + [src(q) for q in q25])))
    tf_bits = [r for r in f.all(C, "hbm_bit_share")]
    tf_bits.sort(key=lambda r: r["period"])
    sections.append({"id": "hbm", "title": "HBM", "short": "HBM",
                     "blocks": [text("How HBM revenue is estimated",
                                     "Samsung discloses no HBM revenue and no HBM share of DRAM revenue, so method A "
                                     "(DRAM revenue x HBM share) is not possible. Method B: annual HBM market size "
                                     "(Yole, Gartner, Micron TAM) x Samsung's HBM revenue share. Every figure below is "
                                     "an estimate; Samsung's own disclosures are growth rates and the HBM4 mix."),
                                table("HBM revenue est, method B (annual, USD)", ["year", "HBM market", "share", "Samsung"],
                                      hb_rows),
                                series("HBM revenue share (Counterpoint, quarterly)", "%", hshare),
                                bars("HBM bit share (TrendForce)", "%",
                                     [(r["period"] + (" fcst" if r["basis"] == "forecast" else ""), r["value"], src(r))
                                      for r in tf_bits]),
                                rows_table("Company-stated HBM growth and mix", f,
                                           ["hbm_revenue_growth_qoq", "hbm_revenue_growth_yoy", "hbm_bit_growth_qoq",
                                            "hbm_bit_growth_yoy", "hbm_bit_supply_growth_yoy", "hbm4_revenue_growth_qoq",
                                            "hbm4_share_of_hbm_revenue", "hbm3e_share_of_hbm_revenue",
                                            "hbm3e_share_of_hbm_volume"], skip_guidance=True),
                                rows_table("HBM guidance", f,
                                           ["hbm_revenue_growth_yoy", "hbm_revenue_growth_yoy_guidance",
                                            "hbm4_revenue_growth_qoq", "hbm4_revenue_growth_qoq_guidance",
                                            "hbm4_share_of_hbm_revenue", "hbm4_share_of_hbm_revenue_guidance",
                                            "hbm3e_share_of_hbm_revenue", "hbm_bit_supply_growth_yoy",
                                            "hbm_bit_supply_growth_yoy_guidance", "hbm_capacity_growth_yoy",
                                            "hbm_production_growth_yoy_guidance"], only_guidance=True),
                                rows_table("HBM market size (inputs)", f, ["hbm_market_size"], company="Market")]})

    # 6. HBM timeline (qualification, customers, specs) --------------------------------------
    tl_metrics = ["hbm3e_12h_stack_capacity", "hbm3e_12h_bandwidth_per_stack", "hbm_generation_volume_start",
                  "amd_mi350_hbm3e_capacity", "hbm3e_12h_nvidia_qualification_delay", "hbm4_nvidia_requested_pin_speed",
                  "hbm4_volume_start_target", "hbm4_pin_speed", "hbm_generation_sample_start", "hbm4_yield",
                  "customer_share_nvidia", "customer_share_google", "hbm_market_share_target"]
    tl = [r for m in tl_metrics for r in f.all(C, m)]

    def when(r):  # sort quarters / halves / years / dates on one axis
        p = r["period"] or ""
        if "Q" in p:
            y, q = p.split("Q")
            return f"{y}-{int(q) * 3 - 2:02d}"
        if "H" in p:
            y, h = p.split("H")
            return f"{y}-{'01' if h == '1' else '07'}"
        return p

    tl.sort(key=when)
    spec_m = ["hbm4_pin_speed", "hbm4_max_pin_speed", "hbm4_bandwidth_per_stack", "hbm4_io_pins", "hbm4_base_die_node",
              "hbm4_stack_capacity_12hi", "hbm4_stack_capacity_max", "hbm4_energy_efficiency_gain",
              "hbm4_heat_dissipation_improvement", "hbm3e_12h_chip_gap", "hbm3e_12h_vertical_density_gain"]
    specs = [(lab(m), fv(f.best(C, m, "2026Q1") or f.best(C, m)), src(f.best(C, m, "2026Q1") or f.best(C, m)))
             for m in spec_m if f.best(C, m)]
    sections.append({"id": "hbmtimeline", "title": "HBM timeline", "short": "HBM time",
                     "blocks": [table("Qualification, launches and customers", ["date", "event", "value"],
                                      [([r["period"], lab(r["metric"]), fv(r)], src(r))
                                       for r in tl]),
                                text("Nvidia qualification",
                                     "Samsung's 12-high HBM3E was announced in Feb 2024 but only cleared Nvidia's tests "
                                     "in Sep 2025, about 18 months later (Korean Economic Daily via TrendForce). HBM4 "
                                     "(1c DRAM core dies on a Samsung Foundry 4nm base die) went into mass production in "
                                     "Feb 2026; reports put Samsung at a mid-20% share of Nvidia's 2026 HBM4 allocation."),
                                kv("HBM4 / HBM3E specs (company stated)", specs)]})

    # 7. Market share --------------------------------------------------------------------------
    share_blocks = []
    for metric, firm, lbl in (("dram_market_share", "TrendForce", "DRAM"), ("hbm_market_share", "Counterpoint", "HBM"),
                              ("nand_market_share", "TrendForce", "NAND")):
        lq = max((max(q, key=qkey) for c in (C,) if (q := strict(f, c, metric, firm))), key=qkey, default=None)
        peers = []
        for comp in ("Samsung", "SK hynix", "Micron", "CXMT", "Nanya", "Kioxia", "SanDisk", "YMTC"):
            r = strict(f, comp, metric, firm).get(lq) if lq else None
            if r:
                peers.append((comp, r["value"], src(r)))
        share_blocks.append(bars(f"{lbl} revenue share {lq} ({firm})", "%", sorted(peers, key=lambda x: -x[1])))
    share_blocks += [series("Samsung DRAM share (TrendForce)", "%", strict(f, C, "dram_market_share", "TrendForce")),
                     series("Samsung DRAM share (Omdia)", "%", strict(f, C, "dram_market_share", "Omdia")),
                     series("Samsung DRAM share (Counterpoint)", "%", strict(f, C, "dram_market_share", "Counterpoint")),
                     series("Samsung NAND share (TrendForce)", "%", strict(f, C, "nand_market_share", "TrendForce")),
                     rows_table("HBM share, annual and forecasts", f, ["hbm_market_share", "hbm_bit_share",
                                                                      "hbm_market_share_target"]) | {
                         "rows": [row for row in rows_table("", f, ["hbm_market_share", "hbm_bit_share",
                                                                    "hbm_market_share_target"])["rows"]
                                  if "Q" not in row["cells"][1]]}]
    sections.append({"id": "share", "title": "Market share", "short": "Share", "blocks": share_blocks})

    # 8. Capacity & capex ----------------------------------------------------------------------
    capex = {}
    for m in ("capex_ds_division", "capex", "capex_ytd"):
        for r in f.all(C, m):
            capex.setdefault((r["period"], round(r["value"], 2), m == "capex_ytd"), r)
    cap_rows = sorted(capex.values(), key=lambda r: r["period"], reverse=True)
    sections.append({"id": "capacity", "title": "Capacity & capex", "short": "Capacity",
                     "blocks": [table("DS capex (semiconductors)", ["period", "what", "value"],
                                      [([r["period"], "Jan-Sep" if r["metric"] == "capex_ytd" else
                                         ("quarter" if "Q" in r["period"] else "full year"), fv(r)], src(r))
                                       for r in cap_rows]),
                                rows_table("Wafer capacity (k wafers/month)", f,
                                           ["wafer_capacity_kwpm", "dram_1c_capacity_kwpm", "hbm_capacity_kwpm",
                                            "p4_dram_capacity_kwpm", "p4_1c_dram_capacity_kwpm",
                                            "hwaseong_line12_capacity_kwpm", "nand_wafer_capacity_kwpm",
                                            "xian_nand_capacity_kwpm"]),
                                rows_table("Fabs and investment plans", f,
                                           ["fab_operation_start_p5", "fab_investment_p5_per_fab",
                                            "fab_investment_yongin_cluster", "hbm_packaging_line_investment",
                                            "domestic_investment_plan_5yr", "us_texas_investment_plan", "chips_act_award"]),
                                text("Sites", "Pyeongtaek P4 is being fitted with 1c DRAM lines for HBM (about a year "
                                     "from full output in early 2026 reports); P5 construction resumed with operation "
                                     "targeted for 2028; the Yongin cluster is a later, six-fab plan. Hwaseong line 12 "
                                     "is converting from 2D NAND to 1c DRAM. Xi'an (China) is Samsung's NAND fab. Taylor, "
                                     "Texas is a logic (foundry) site, not memory: its CHIPS Act award is shown for "
                                     "completeness.")]})

    # 9. Technology ----------------------------------------------------------------------------
    sections.append({"id": "tech", "title": "Technology", "short": "Tech",
                     "blocks": [rows_table("V-NAND layers and density", f,
                                           ["layer_count", "layer_count_target", "v10_nand_density_gain_vs_v9",
                                            "qlc_v9_bit_density_gain"]),
                                rows_table("1c DRAM", f, ["dram_1c_yield", "dram_1c_test_yield"]),
                                rows_table("CXL memory", f,
                                           ["cxl_cmm_d_2_0_capacity_max", "cxl_cmm_d_2_0_bandwidth",
                                            "cxl_cmm_d_3_1_capacity_max", "cxl_cmm_d_3_1_bandwidth",
                                            "cxl_cmm_b_capacity_max", "cxl_cmm_b_max_throughput",
                                            "cxl_pooling_goodput_multiple"]),
                                rows_table("Beyond HBM4 (zHBM, custom HBM, PIM)", f,
                                           ["zhbm_performance_multiple_vs_hbm5", "zhbm_density_multiple_vs_hbm5",
                                            "zhbm_energy_efficiency_multiple_vs_hbm5", "zhbm_bandwidth_gain_vs_hbm4e",
                                            "zhbm_power_efficiency_gain_vs_hbm4e", "chbm4_hpb_peak_temp_reduction",
                                            "lpddr5x_pim_effective_bandwidth_multiple"])]})

    # 10. Sources ------------------------------------------------------------------------------
    conf = conflicts(f, [C])
    mine = [r for r in f.rows if r["company"] == C]
    n_dart = sum(len(v) for v in d.values())
    sections.append({"id": "sources", "title": "Sources", "short": "Sources",
                     "blocks": [kv("Coverage", [("Sourced numbers (Samsung, memory_facts)", f"{len(mine)}", None),
                                                ("Distinct source pages", f"{len({r['source_url'] for r in mine})}", None),
                                                ("OpenDART values (revenue, OI, NI)", f"{n_dart}", None),
                                                ("Latest OpenDART quarter", gq or "—", None),
                                                ("Conflicting values", f"{len(conf)}", None)]),
                                table("Where sources disagree", ["company", "metric", "period", "value", "source"], conf)]})

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {"ticker": TICKER, "name": "Samsung Electronics", "industry": "DRAM, HBM and NAND (Memory in DS division)",
            "country": "KR", "built_at": now,
            "freshness": [{"source": "memory_facts", "pulled": now}, {"source": "OpenDART", "pulled": now}],
            "sections": sections, "unsourced": []}
