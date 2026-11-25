"""Diagrams for ticker dossiers, built from templates instead of per-ticker Blender code.

Two kinds of picture land above a dossier tab (the tab's `scene`, played by
tui/src/screens/memory_scene.rs):

1. Data diagrams. COMPOSITIONS chains template panels (tools/pbr3d/blender/tpl_kit.py: bars,
   donut, towers) into one 3-beat scene per (ticker, tab). Each panel is fed from a sourced block
   the dossier tab already builds (e.g. the Financials tab's "Quarterly revenue" series), so the
   picture never shows a number the tab below it does not source. Output:
   tools/pbr3d/assets/tpl/<TICKER>_<tab>.glb, with the spec next to it in tpl/specs/ (a spec that
   has not changed is not rebuilt).

2. Stack diagrams. STACK maps a ticker to the existing hand-built diagrams pages that show where
   it sits in the AI hardware stack (LASER for COHR, HBM STACK for MU, ...). These are reused, not
   rebuilt: the Profile tab plays the first one.

    uv run python derive/dossier_diagrams.py MRVL NVDA      # specs + GLBs for these tickers
    uv run python derive/dossier_diagrams.py --all          # every universe ticker
    uv run python derive/dossier_diagrams.py MRVL --spec    # print the specs, build nothing
    uv run python derive/dossier_diagrams.py --all --jobs 3 # Blender processes in parallel
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPO = ROOT.parent
TPL = REPO / "tools" / "pbr3d" / "assets" / "tpl"
SPECS = TPL / "specs"
RUNNER = REPO / "tools" / "pbr3d" / "blender" / "tpl_run.py"
BATCH = 12  # specs per Blender process (start-up is ~2 s; a scene is well under that)

# ---- 1. data diagrams ----------------------------------------------------------------------
# tab id -> beats; each beat is a list of (panel, block title prefix) alternatives, first found
# wins. A beat with no match is dropped; a composition with no beats is skipped.
COMPOSITIONS: dict[str, list[list[tuple[str, str]]]] = {
    "financials": [
        [("bars", "Quarterly revenue"), ("bars", "Annual revenue")],
        [("bars", "Operating margin, quarterly"), ("bars", "Operating margin, annual"),
         ("bars", "Gross margin, quarterly")],
        [("donut", "Product / service"), ("donut", "Geography"), ("bars", "Free cash flow, quarterly")],
    ],
}

# Short titles for the picture's title tag (block titles carry dates in parentheses).
SHORT = {"Operating margin, quarterly": "Operating margin", "Operating margin, annual": "Operating margin, annual",
         "Gross margin, quarterly": "Gross margin", "Free cash flow, quarterly": "Free cash flow"}


def _title(block_title: str) -> str:
    t = re.sub(r"\s*\(.*\)\s*$", "", block_title or "").strip()
    return SHORT.get(t, t)


def partition(items: list[list], totals: list[float], tol: float = 0.015) -> list[list]:
    """XBRL member lists overlap: a parent next to its children (ASML "Product" with NXE, ArF...;
    NVDA "Data Center" with Compute, Networking) or two partitions side by side (VRT product /
    service and product-ex-spares / services-and-spares). Keep the subset that adds up to a filed
    total (latest first) within `tol`, with the most members (the finest split). With no total,
    drop members that equal a sum of smaller ones. Returns items in the given order."""
    items = sorted(items, key=lambda kv: -kv[1])[:14]
    n = len(items)
    for t in totals:
        best = None
        for mask in range(1, 1 << n):
            tot = sum(items[i][1] for i in range(n) if mask >> i & 1)
            if abs(tot - t) <= tol * t:
                rank = (bin(mask).count("1"), -abs(tot - t))  # most members, then closest
                if best is None or rank > best[0]:
                    best = (rank, mask)
        if best:
            return [items[i] for i in range(n) if best[1] >> i & 1]
    keep = []
    for i, (name, v) in enumerate(items):
        rest = [w for _, w in items[i + 1:]]
        parent = any(abs(sum(rest[j] for j in range(len(rest)) if m >> j & 1) - v) <= tol * v
                     for m in range(3, 1 << len(rest)) if bin(m).count("1") >= 2)
        if not parent:
            keep.append([name, v])
    return keep


def _panel(panel: str, b: dict, totals: list[float] | None = None) -> dict | None:
    unit = b.get("unit", "")
    if panel == "bars":
        pts = [[p["x"], p["y"]] for p in b.get("points") or [] if p.get("y") is not None]
        return {"panel": "bars", "title": _title(b["title"]), "unit": unit, "points": pts} if len(pts) >= 3 else None
    if panel == "donut":
        items = [[i["label"], i["value"]] for i in b.get("items") or [] if (i.get("value") or 0) > 0]
        items = partition(items, totals or [])
        return {"panel": "donut", "title": _title(b["title"]), "unit": unit, "items": items} if len(items) >= 2 else None
    raise ValueError(panel)


def compose(ticker: str, section: dict) -> dict | None:
    """The spec for one dossier section, or None when it has no composition or no data."""
    beats_spec = COMPOSITIONS.get(section.get("id", ""))
    if not beats_spec:
        return None
    blocks = section.get("blocks") or []
    annual = next((b for b in blocks if b.get("title") == "Annual revenue"), None)
    totals = [p["y"] for p in reversed((annual or {}).get("points") or []) if p.get("y")]
    beats = []
    for options in beats_spec:
        for panel, prefix in options:
            b = next((b for b in blocks if (b.get("title") or "").startswith(prefix)), None)
            p = _panel(panel, b, totals) if b else None
            if p:
                beats.append(p)
                break
    if not beats:
        return None
    return {"name": scene_name(ticker, section["id"]), "beats": beats}


def scene_name(ticker: str, tab: str) -> str:
    return f"{ticker.upper().replace('/', '_')}_{tab}"


def scene_for(ticker: str, tab: str) -> str | None:
    """The `scene` of a dossier tab: a built template GLB ("tpl/<name>"), else for the Profile tab
    the ticker's first stack diagram, else None."""
    name = scene_name(ticker, tab)
    if (TPL / f"{name}.glb").exists():
        return f"tpl/{name}"
    if tab == "profile" and STACK.get(ticker.upper()):
        return STACK[ticker.upper()][0]
    return None


# ---- 2. stack diagrams ---------------------------------------------------------------------
# dossier_stack.json: ticker -> diagrams pages showing what the company makes or does in the stack.
STACK: dict[str, list[str]] = {k: v for k, v in json.loads((Path(__file__).parent / "dossier_stack.json").read_text()).items()
                               if not k.startswith("_")}


# ---- build ---------------------------------------------------------------------------------

def specs_for_sections(ticker: str, sections: list[dict], con, F) -> list[dict]:
    """Every scene spec for a dossier: the ticker's custom story (derive/dossier_custom/) for the
    tabs it covers, the generic composition for the rest."""
    from derive import dossier_custom

    fin = next((s for s in sections if s.get("id") == "financials"), None)
    out = dossier_custom.specs(ticker, con, F, fin)
    have = {s["name"] for s in out}
    for s in sections:
        spec = compose(ticker, s)
        if spec and spec["name"] not in have:
            out.append(spec)
    return out


def specs_for(ticker: str) -> list[dict]:
    import duckdb

    from derive.dossier import Filings
    from derive.dossier_tabs import financials

    con = duckdb.connect()
    try:
        F = Filings(con, ticker)
        sec = financials.section(ticker, con, F, None)
        return specs_for_sections(ticker, [{**sec, "id": "financials"}] if sec else [], con, F)
    finally:
        con.close()


KIT = REPO / "tools" / "pbr3d" / "blender" / "tpl_kit.py"


def _stamp(spec: dict) -> str:
    """What a GLB was built from: the spec and the kit's source (a kit change rebuilds all)."""
    kit = hashlib.sha1(KIT.read_bytes()).hexdigest()[:12]
    return json.dumps({"kit": kit, **spec}, sort_keys=True)


def _changed(spec: dict) -> bool:
    p = SPECS / f"{spec['name']}.json"
    glb = TPL / f"{spec['name']}.glb"
    new = _stamp(spec)
    return not (glb.exists() and p.exists() and p.read_text() == new)


def render(specs: list[dict], jobs: int = 1, force: bool = False) -> tuple[int, int]:
    """Runs Blender on the specs that changed; returns (built, failed)."""
    todo = [s for s in specs if force or _changed(s)]
    if not todo:
        return 0, 0
    SPECS.mkdir(parents=True, exist_ok=True)
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]

    def run(batch: list[dict]) -> tuple[int, int]:
        tmp = SPECS / f".batch-{batch[0]['name']}.json"
        tmp.write_text(json.dumps(batch))
        try:
            r = subprocess.run(["blender", "-b", "--factory-startup", "--python", str(RUNNER), "--", str(tmp)],
                               capture_output=True, text=True)
        finally:
            tmp.unlink(missing_ok=True)
        ok = 0
        for s in batch:
            if f"exported {TPL / s['name']}.glb" in r.stdout:
                (SPECS / f"{s['name']}.json").write_text(_stamp(s))
                ok += 1
            else:
                print(f"  {s['name']}: failed\n{r.stderr[-1500:]}", file=sys.stderr)
        return ok, len(batch) - ok

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        res = list(ex.map(run, batches))
    return sum(r[0] for r in res), sum(r[1] for r in res)


def main(argv: list[str]) -> None:
    show = "--spec" in argv
    force = "--force" in argv
    jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 1
    tickers = [a.upper() for a in argv if not a.startswith("--") and not a.isdigit()]
    if "--all" in argv:
        from sources import universe
        tickers = [r["ticker"] for r in universe.rows()]
    if not tickers:
        raise SystemExit(__doc__)
    specs = []
    for t in tickers:
        try:
            got = specs_for(t)
        except Exception as e:  # one ticker's data problem must not stop a batch
            print(f"{t}: spec failed: {e}", file=sys.stderr)
            continue
        specs += got
        if not got:
            print(f"{t}: no diagram data")
    if show:
        print(json.dumps(specs, indent=1))
        return
    built, failed = render(specs, jobs=jobs, force=force)
    print(f"{len(specs)} specs, {built} built, {len(specs) - built - failed} unchanged, {failed} failed")


if __name__ == "__main__":
    main(sys.argv[1:])
