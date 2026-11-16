"""Memory R&D company pages for the diagrams Memory tab (SANDISK, SK HYNIX, ...): ten sections
of sourced numbers in the dossier JSON shape (see derive/dossier.py), cached in dossier_cache
under the key "MEM:<TICKER>" and drawn by the dossier screen in memory-page mode (ten tabs
on the left, the selected tab's tables / series / bars on the right).

Inputs: data/memory_facts/*.jsonl (web research rows, each with a verbatim quote and URL;
see data/memory_facts/README.md) and data/dart/facts.parquet (OpenDART, Korean filers).

Rule, as in the dossier: no value without a source. A point's `src.label` carries the source
name, date and the quoted sentence; derived values (QoQ %, share of revenue) carry a formula
and the sources of their inputs. When several rows give the same (period, metric), the one
with the strongest basis wins (reported > company_stated > guidance > estimate >
market_share > forecast); the others stay visible in the Sources tab as conflicts.

    uv run python derive/memory_page.py SNDK          # build + cache, print a summary
    uv run python derive/memory_page.py SNDK --json   # print the JSON
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import duckdb  # noqa: E402

from core import db  # noqa: E402
from core.paths import DATA_ROOT  # noqa: E402

FACTS_GLOB = str(DATA_ROOT / "memory_facts" / "*.jsonl")
BASIS_RANK = {"reported": 0, "company_stated": 1, "guidance": 2, "estimate": 3, "market_share": 4, "forecast": 5}
QUARTER = re.compile(r"^(\d{4})Q([1-4])$")


# ---- facts ---------------------------------------------------------------------------------

def load_facts() -> list[dict]:
    con = duckdb.connect()
    rows = con.execute(f"""
        SELECT company, ticker, period, metric, value, unit, basis, source_name, source_url,
               published, quote, notes, agent
        FROM read_json('{FACTS_GLOB}', format='newline_delimited', union_by_name=true,
             columns={{'company':'VARCHAR','ticker':'VARCHAR','period':'VARCHAR','metric':'VARCHAR',
                      'value':'DOUBLE','unit':'VARCHAR','basis':'VARCHAR','source_name':'VARCHAR',
                      'source_url':'VARCHAR','published':'VARCHAR','quote':'VARCHAR','notes':'VARCHAR',
                      'agent':'VARCHAR'}})
        QUALIFY row_number() OVER (PARTITION BY company, period, metric, source_url ORDER BY agent) = 1
    """).fetchall()
    cols = ["company", "ticker", "period", "metric", "value", "unit", "basis", "source_name", "source_url",
            "published", "quote", "notes", "agent"]
    return [dict(zip(cols, r)) for r in rows]


class Facts:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.by = defaultdict(list)  # (company, metric) -> rows
        for r in rows:
            self.by[(r["company"], r["metric"])].append(r)

    def all(self, company: str, metric: str) -> list[dict]:
        return self.by.get((company, metric), [])

    def best(self, company: str, metric: str, period: str | None = None) -> dict | None:
        rows = [r for r in self.all(company, metric) if period is None or r["period"] == period]
        if not rows:
            return None
        return min(rows, key=lambda r: (BASIS_RANK.get(r["basis"], 9), -(len(r["quote"] or ""))))

    def quarterly(self, company: str, metric: str, prefer: str | None = None, ahead: bool = False) -> dict[str, dict]:
        """period -> best row, quarterly periods only. `prefer` = substring of source_name to favour
        (e.g. "TrendForce" so one firm's series is not mixed with another's). Guidance and forecasts
        are left out unless `ahead` (they are not actuals)."""
        out: dict[str, list[dict]] = defaultdict(list)
        for r in self.all(company, metric):
            if not ahead and r["basis"] in ("guidance", "forecast"):
                continue
            if QUARTER.match(r["period"] or ""):
                out[r["period"]].append(r)

        def key(r):
            pref = 0 if prefer and prefer.lower() in ((r["source_name"] or "") + (r["notes"] or "")).lower() else 1
            return (pref, BASIS_RANK.get(r["basis"], 9), -(len(r["quote"] or "")))

        return {p: min(rs, key=key) for p, rs in sorted(out.items(), key=lambda kv: qkey(kv[0]))}

    def latest_quarter(self, metric: str, prefer: str | None = None) -> str | None:
        ps = [r["period"] for r in self.rows if r["metric"] == metric and QUARTER.match(r["period"] or "")
              and (not prefer or prefer.lower() in ((r["source_name"] or "") + (r["notes"] or "")).lower())]
        return max(ps, key=qkey) if ps else None


def qkey(p: str) -> tuple[int, int]:
    m = QUARTER.match(p or "")
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


# ---- sources and formatting -----------------------------------------------------------------

def src(r: dict) -> dict:
    quote = (r.get("quote") or "").strip()
    if len(quote) > 160:
        quote = quote[:157] + "..."
    when = f" {r['published']}" if r.get("published") else ""
    basis = f" [{r['basis']}]" if r.get("basis") and r["basis"] != "reported" else ""
    return {"label": f"{r.get('source_name') or 'source'}{when}{basis}: \"{quote}\"", "url": r.get("source_url")}


def derived(label: str, formula: str, inputs: list[dict]) -> dict:
    return {"label": label, "formula": formula, "inputs": [src(r) for r in inputs]}


UNIT_FMT = {
    "usd_million": lambda v: f"${v:,.0f}M" if abs(v) < 1000 else f"${v / 1000:,.2f}B",
    "usd_billion": lambda v: f"${v:,.2f}B",
    "krw_trillion": lambda v: f"KRW {v:,.1f}T",
    "jpy_billion": lambda v: f"JPY {v:,.1f}B",
    "cny_billion": lambda v: f"CNY {v:,.1f}B",
    "pct": lambda v: f"{v:,.1f}%",
    "layers": lambda v: f"{v:,.0f} layers",
    "gb": lambda v: f"{v:,.0f} GB",
    "tb": lambda v: f"{v:,.0f} TB",
    "kwpm": lambda v: f"{v:,.0f}k wpm",
}


def fmt(r: dict | None) -> str:
    if not r:
        return "—"
    v, unit = r["value"], r.get("unit") or ""
    f = UNIT_FMT.get(unit)
    s = f(v) if f else f"{v:,.6g} {unit}".strip()
    if r.get("basis") in ("estimate", "forecast", "guidance", "market_share"):
        s += f" ({r['basis'].replace('_', ' ')})"
    return s


def label_of(metric: str) -> str:
    return metric.replace("_", " ").replace(" qoq", " QoQ").replace(" yoy", " YoY").replace("hbf", "HBF") \
        .replace("nand", "NAND").replace("ssd", "SSD").replace("asp", "ASP").replace("jv", "JV")


# ---- block builders -------------------------------------------------------------------------

def series(title: str, unit: str, rows: dict[str, dict], scale: float = 1.0) -> dict:
    return {"type": "series", "title": title, "unit": unit,
            "points": [{"x": p, "y": round(r["value"] * scale, 4), "src": src(r)} for p, r in rows.items()]}


def kv(title: str, items: list[tuple[str, str, dict | None]]) -> dict:
    return {"type": "kv", "title": title,
            "rows": [{"label": lbl, "value": val, "src": s} for lbl, val, s in items if val not in (None, "—")]}


def table(title: str, cols: list[str], rows: list[tuple[list[str], dict | None]]) -> dict:
    return {"type": "table", "title": title, "cols": cols, "rows": [{"cells": c, "src": s} for c, s in rows]}


def bars(title: str, unit: str, items: list[tuple[str, float, dict]]) -> dict:
    return {"type": "bars", "title": title, "unit": unit,
            "items": [{"label": lbl, "value": round(v, 4), "src": s} for lbl, v, s in items]}


def text(title: str, body: str) -> dict:
    return {"type": "text", "title": title, "text": body}


def qoq_table(title: str, rows: dict[str, dict]) -> dict:
    out, prev = [], None
    for p, r in rows.items():
        if prev and prev["value"]:
            g = r["value"] / prev["value"] - 1
            s = derived(f"{p} vs {prev['period']}", f"{r['value']:,.6g} / {prev['value']:,.6g} - 1", [r, prev])
            out.append(([p, fmt(r), f"{g * 100:+.1f}%"], s))
        else:
            out.append(([p, fmt(r), "—"], src(r)))
        prev = r
    return table(title, ["quarter", "value", "QoQ"], list(reversed(out)))


def facts_table(title: str, f: Facts, company: str, metrics: list[str]) -> dict:
    """Every row of `metrics` for a company, newest first: one line per sourced number."""
    rows = []
    for m in metrics:
        for r in f.all(company, m):
            rows.append(r)
    rows.sort(key=lambda r: (r["period"] or ""), reverse=True)
    return table(title, ["metric", "period", "value"], [([label_of(r["metric"]), r["period"], fmt(r)], src(r)) for r in rows])


def conflicts(f: Facts, companies: list[str]) -> list[tuple[list[str], dict]]:
    groups = defaultdict(list)
    for r in f.rows:
        if r["company"] in companies:
            groups[(r["company"], r["period"], r["metric"])].append(r)
    out = []
    for (c, p, m), rs in sorted(groups.items(), key=lambda kv: kv[0][1] or "", reverse=True):
        vals = {round(r["value"], 3) for r in rs}
        if len(vals) > 1:
            for r in rs:
                out.append(([c, label_of(m), p, fmt(r), r.get("source_name") or ""], src(r)))
    return out


# ---- SanDisk --------------------------------------------------------------------------------

def sandisk(f: Facts) -> dict:
    C = "SanDisk"
    rev = f.quarterly(C, "revenue")
    dc, edge, cons = f.quarterly(C, "datacenter_revenue"), f.quarterly(C, "edge_revenue"), f.quarterly(C, "consumer_revenue")
    gm = f.quarterly(C, "gross_margin")
    opi = f.quarterly(C, "operating_income")
    share = f.quarterly(C, "nand_market_share", prefer="TrendForce")
    last = max(rev, key=qkey) if rev else None
    prev = sorted(rev, key=qkey)[-2] if len(rev) > 1 else None
    lr = rev.get(last) if last else None

    sections = []

    # 1. Snapshot
    snap = []
    if lr:
        snap.append((f"Revenue {last}", fmt(lr), src(lr)))
        if prev:
            pr = rev[prev]
            snap.append(("Revenue QoQ", f"{(lr['value'] / pr['value'] - 1) * 100:+.1f}%",
                         derived(f"{last} vs {prev}", f"{lr['value']:,.0f} / {pr['value']:,.0f} - 1", [lr, pr])))
    if last in gm:
        snap.append((f"Gross margin {last}", fmt(gm[last]), src(gm[last])))
    if last in dc and lr:
        d = dc[last]
        snap.append((f"Datacenter {last}", fmt(d), src(d)))
        snap.append(("Datacenter share of revenue", f"{d['value'] / lr['value'] * 100:.1f}%",
                     derived(f"{last} datacenter / total", f"{d['value']:,.0f} / {lr['value']:,.0f}", [d, lr])))
    if share:
        sp = max(share, key=qkey)
        snap.append((f"NAND market share {sp}", fmt(share[sp]), src(share[sp])))
    for m, lbl in (("jv_capacity_share", "Share of Kioxia JV capacity"), ("layer_count", "Latest BiCS layers"),
                   ("hbf_stack_capacity", "HBF stack capacity")):
        r = f.best(C, m) if m != "layer_count" else (f.best(C, m) or f.best("Kioxia", m))
        if r:
            snap.append((lbl, fmt(r), src(r)))
    sections.append({"id": "snapshot", "title": "Snapshot", "short": "Snapshot",
                     "blocks": [kv("Latest", snap),
                                text("What SanDisk is", "NAND flash and SSD maker, spun off from Western Digital in Feb 2025. "
                                     "It shares the Yokkaichi and Kitakami fabs with Kioxia and co-develops HBF (NAND stacked "
                                     "in an HBM-style package) with SK hynix. Fiscal quarters are labelled by the calendar "
                                     "quarter they mostly cover (FQ1 FY26, ended Oct 3 2025 = 2025Q3).")]})

    # 2. Revenue
    guide = {p: r for p, r in f.quarterly(C, "revenue", ahead=True).items() if r["basis"] == "guidance"}
    sections.append({"id": "revenue", "title": "Revenue", "short": "Revenue",
                     "blocks": [series("Quarterly revenue", "$M", rev), qoq_table("Revenue by quarter", rev),
                                table("Guidance", ["quarter", "guided revenue"], [([p, fmt(r)], src(r)) for p, r in guide.items()]),
                                facts_table("Fiscal years", f, C, ["revenue"]) | {"rows": [
                                    row for row in facts_table("", f, C, ["revenue"])["rows"] if row["cells"][1].startswith("FY")]}]})

    # 3. End markets
    qs = sorted(set(dc) | set(edge) | set(cons), key=qkey, reverse=True)
    mix_rows = []
    for q in qs:
        cells = [q] + [fmt(m.get(q)) for m in (dc, edge, cons)]
        first = dc.get(q) or edge.get(q) or cons.get(q)
        mix_rows.append((cells, src(first) if first else None))
    mix_blocks = [series("Datacenter revenue", "$M", dc), table("Revenue by end market", ["quarter", "Datacenter", "Edge", "Consumer"], mix_rows)]
    if last and all(last in m for m in (dc, edge, cons)):
        mix_blocks.append(bars(f"Mix {last}", "$M", [("Datacenter", dc[last]["value"], src(dc[last])),
                                                     ("Edge", edge[last]["value"], src(edge[last])),
                                                     ("Consumer", cons[last]["value"], src(cons[last]))]))
    sections.append({"id": "markets", "title": "End markets", "short": "Markets", "blocks": mix_blocks})

    # 4. Margins
    sections.append({"id": "margins", "title": "Margins", "short": "Margins",
                     "blocks": [series("Gross margin", "%", gm), series("Operating income", "$M", opi)]})

    # 5. Bits and pricing
    bit_metrics = [m for (c, m) in f.by if c == C and any(k in m for k in ("bit_growth", "asp", "per_gb", "pricing"))]
    price = f.quarterly("Market", "nand_contract_price_change_qoq", prefer="TrendForce")
    essd = f.quarterly("Market", "enterprise_ssd_price_change_qoq", prefer="TrendForce")
    sections.append({"id": "pricing", "title": "Bits & pricing", "short": "Pricing",
                     "blocks": [facts_table("SanDisk bits and price per GB", f, C, bit_metrics),
                                series("NAND contract price change QoQ (industry)", "%", price),
                                series("Enterprise SSD price change QoQ (industry)", "%", essd)]})

    # 6. NAND market share
    lq = f.latest_quarter("nand_market_share", prefer="TrendForce")
    peers = []
    for comp in ("Samsung", "SK hynix", "Kioxia", "Micron", "SanDisk", "YMTC"):
        r = f.quarterly(comp, "nand_market_share", prefer="TrendForce").get(lq) if lq else None
        if r:
            peers.append((comp, r["value"], src(r)))
    nrev = f.quarterly(C, "nand_revenue", prefer="TrendForce")
    sections.append({"id": "share", "title": "NAND share", "short": "Share",
                     "blocks": [bars(f"NAND revenue share {lq}", "%", sorted(peers, key=lambda x: -x[1])),
                                series("SanDisk NAND share", "%", share),
                                series("SanDisk NAND revenue (TrendForce)", "$B", nrev)]})

    # 7. Kioxia JV
    krev = f.quarterly("Kioxia", "revenue")
    jv = ["jv_capacity_share", "jv_investment_plan", "kitakami_fab3_cost", "yokkaichi_fab_count", "capex",
          "sandisk_jv_payment_to_kioxia", "lta_volume_coverage_target"]
    sections.append({"id": "kioxia", "title": "Kioxia JV", "short": "Kioxia",
                     "blocks": [facts_table("JV and fabs", f, "Kioxia", jv) | {"rows": facts_table("", f, "Kioxia", jv)["rows"]
                                                                                 + facts_table("", f, C, ["jv_capacity_share"])["rows"]},
                                series("Kioxia revenue", "JPY B", krev),
                                facts_table("Kioxia results", f, "Kioxia", ["operating_income", "net_income", "gross_margin",
                                                                            "operating_margin", "ssd_storage_revenue"])]})

    # 8. Technology
    tech = [m for (c, m) in f.by if c in (C, "Kioxia") and any(k in m for k in ("layer", "density", "interface", "ssd_capacity",
                                                                                   "ssd_max", "bics"))]
    sections.append({"id": "tech", "title": "Technology", "short": "Tech",
                     "blocks": [table("Process and products", ["company", "metric", "date", "value"],
                                      sorted([([r["company"], label_of(r["metric"]), r["period"], fmt(r)], src(r))
                                              for c in (C, "Kioxia") for m in tech for r in f.all(c, m)],
                                             key=lambda x: x[0][2], reverse=True))]})

    # 9. HBF
    hbf = [m for (c, m) in f.by if c in (C, "SK hynix") and m.startswith("hbf")]
    sections.append({"id": "hbf", "title": "HBF", "short": "HBF",
                     "blocks": [text("HBF", "NAND dies stacked in an HBM-style package next to the GPU, for inference that "
                                     "needs more capacity per GPU than HBM gives. Co-developed with SK hynix; OCP spec Aug 2026."),
                                table("Specs and timeline", ["company", "metric", "date", "value"],
                                      sorted([([r["company"], label_of(r["metric"]), r["period"], fmt(r)], src(r))
                                              for c in (C, "SK hynix") for m in hbf for r in f.all(c, m)],
                                             key=lambda x: x[0][2], reverse=True))]})

    # 10. Sources
    conf = conflicts(f, [C, "Kioxia"])
    n_rows = sum(1 for r in f.rows if r["company"] in (C, "Kioxia"))
    n_src = len({r["source_url"] for r in f.rows if r["company"] in (C, "Kioxia")})
    sections.append({"id": "sources", "title": "Sources", "short": "Sources",
                     "blocks": [kv("Coverage", [("Sourced numbers (SanDisk + Kioxia)", f"{n_rows}", None),
                                                ("Distinct source pages", f"{n_src}", None),
                                                ("Conflicting values", f"{len(conf)}", None)]),
                                table("Where sources disagree", ["company", "metric", "period", "value", "source"], conf)]})

    return {"ticker": "SNDK", "name": "SanDisk", "industry": "NAND flash and SSDs", "country": "US",
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "freshness": [{"source": "memory_facts", "pulled": datetime.now(timezone.utc).isoformat(timespec="seconds")}],
            "sections": sections, "unsourced": []}


def _pages() -> dict:
    """ticker -> builder: SanDisk here, the other companies one module each in derive/memory_pages/
    (each defines TICKER and build(f: Facts) -> dict, using the helpers in this file)."""
    import importlib
    import pkgutil

    pages = {"SNDK": sandisk}
    pkg = Path(__file__).with_name("memory_pages")
    for m in pkgutil.iter_modules([str(pkg)]):
        mod = importlib.import_module(f"derive.memory_pages.{m.name}")
        if getattr(mod, "TICKER", None) and getattr(mod, "build", None):
            pages[mod.TICKER] = mod.build
    return pages


# The 3D diagram each tab plays above its data (a diagrams node with a Blender overview; see
# tui/src/screens/memory_scene.rs). First keyword in the tab title wins; otherwise the company's
# default. There is no NAND-specific diagram yet, so NAND makers default to the wafer.
SCENE_RULES = [
    (("hbf",), "HBM STACK"),
    (("hbm",), "HBM STACK"),
    (("dram", "memory vs", "group"), "CELL"),
    (("bit", "pricing", "price"), "BANK"),
    (("margin", "unit", "r&d"), "ARRAY"),
    (("share",), "BANDWIDTH"),
    (("capex", "capacity", "fab", "kioxia", "wafer"), "WAFER"),
    (("tech", "node", "layer", "roadmap", "export", "sanction"), "LITHO"),
    (("customer",), "ASSEMBLY"),
    (("revenue",), "BANDWIDTH"),
]
DEFAULT_SCENE = {"SNDK": "WAFER", "YMTC": "WAFER"}


# Custom per-tab scenes (tools/pbr3d/blender/mem_<slug>.py -> tools/pbr3d/assets/mem/<slug>_<tab id>.glb)
# replace the generic diagram whenever the GLB exists.
SLUG = {"SNDK": "sandisk", "000660.KS": "sk_hynix", "005930.KS": "samsung", "MU": "micron",
        "688825.SS": "cxmt", "YMTC": "ymtc"}
MEM_ASSETS = ROOT.parent / "tools" / "pbr3d" / "assets" / "mem"


def custom_scene(ticker: str, section_id: str) -> str | None:
    name = f"{SLUG.get(ticker, ticker.lower())}_{section_id}"
    return f"mem/{name}" if (MEM_ASSETS / f"{name}.glb").exists() else None


def scene_for(ticker: str, title: str) -> str:
    t = title.lower()
    for words, scene in SCENE_RULES:
        if any(w in t for w in words):
            return scene
    return DEFAULT_SCENE.get(ticker, "HBM STACK")


def build(ticker: str) -> dict:
    pages = _pages()
    if ticker not in pages:
        raise SystemExit(f"no memory page for {ticker}; have {sorted(pages)}")
    d = pages[ticker](Facts(load_facts()))
    for s in d["sections"]:
        s["blocks"] = [b for b in s["blocks"] if b.get("points") or b.get("rows") or b.get("items") or b.get("text")]
        s.setdefault("scene", custom_scene(ticker, s["id"]) or scene_for(ticker, s["title"]))
    return d


def main(argv: list[str]) -> None:
    as_json = "--json" in argv
    tickers = [a.upper() for i, a in enumerate(argv) if not a.startswith("--") and not (i and argv[i - 1] == "--if-stale")]
    for t in tickers:
        t0 = time.time()
        d = build(t)
        db.put_cached_dossier(f"MEM:{t}", d)
        if as_json:
            print(json.dumps(d, default=str))
        else:
            n = sum(len(b.get("rows", b.get("points", b.get("items", [])))) for s in d["sections"] for b in s["blocks"])
            print(json.dumps({"ticker": t, "rebuilt": True, "sections": len(d["sections"]), "values": n,
                              "secs": round(time.time() - t0, 2)}), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
