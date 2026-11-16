"""YMTC memory page: one purpose-built scene per tab, 3 beats of 8 s, wide (~3:1) framing.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/mem_ymtc.py [-- <tab id> ...]

Writes tools/pbr3d/assets/mem/ymtc_<tab>.glb, which py/derive/memory_page.py picks up.
Every figure in a tag or a bar height comes from data/memory_facts/ymtc.jsonl, as shown on the
cached page (`cd py && uv run python derive/memory_page.py YMTC --json`). Estimates say "est".
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, _constant_until, ball, box, disc, empty, fly, key, label, mat, pivot, show, tube  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
from poly_overview import run  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PBR_DIR = os.path.normpath(os.path.join(HERE, ".."))
END = F(4, 0)


def B(i, u0=0.0, u1=1.0):
    """[F(i,u0), F(i,u1)) as an interval list."""
    return [(F(i, u0), F(i, u1))]


def mats(m):
    m["floor"] = mat("ymtc_floor", (0.13, 0.13, 0.17), rough=0.9)
    m["plate"] = mat("ymtc_plate", (0.19, 0.20, 0.25), rough=0.8)
    m["rev"] = mat("ymtc_rev", (0.12, 0.55, 0.85), rough=0.45, emit=(0.25, 0.6, 0.85), strength=0.15)
    m["rev2"] = mat("ymtc_rev2", (0.18, 0.42, 0.58), rough=0.5)
    m["gold"] = mat("ymtc_gold", (1.0, 0.62, 0.08), metal=0.3, rough=0.35, emit=(1.0, 0.6, 0.1), strength=0.45)
    m["red"] = mat("ymtc_red", (0.90, 0.10, 0.10), rough=0.5, emit=(0.95, 0.12, 0.12), strength=0.45)
    m["grey"] = mat("ymtc_grey", (0.45, 0.47, 0.53), rough=0.6)
    m["grey2"] = mat("ymtc_grey2", (0.30, 0.31, 0.36), rough=0.6)
    m["purple"] = mat("ymtc_purple", (0.45, 0.25, 0.95), rough=0.45, emit=(0.55, 0.35, 0.95), strength=0.25)
    m["purple2"] = mat("ymtc_purple2", (0.28, 0.20, 0.48), rough=0.5)
    m["green"] = mat("ymtc_green", (0.30, 0.85, 0.45), rough=0.5, emit=(0.2, 0.7, 0.35), strength=0.5)
    m["copper"] = mat("ymtc_copper", (0.90, 0.52, 0.30), metal=0.8, rough=0.3)
    m["si"] = mat("ymtc_si", (0.50, 0.53, 0.60), metal=0.85, rough=0.25)
    m["white"] = mat("ymtc_white", (0.90, 0.90, 0.93), rough=0.5, emit=(0.9, 0.9, 0.95), strength=0.6)
    m["glass"] = mat("ymtc_glass", (0.85, 0.90, 1.0), rough=0.1, alpha=0.22)
    m["redglass"] = mat("ymtc_redglass", (1.0, 0.3, 0.3), emit=(1.0, 0.2, 0.2), strength=0.8, alpha=0.35)
    m["goldglass"] = mat("ymtc_goldglass", (1.0, 0.75, 0.3), emit=(1.0, 0.7, 0.2), strength=0.5, alpha=0.3)
    m["dim"] = mat("ymtc_dim", (0.26, 0.27, 0.33), rough=0.7)
    m["paper"] = mat("ymtc_paper", (0.88, 0.86, 0.80), rough=0.9)
    m["tool"] = mat("ymtc_tool", (0.40, 0.60, 0.80), metal=0.4, rough=0.4)
    m["bond"] = mat("ymtc_bond", (1.0, 0.7, 0.4), emit=(1.0, 0.6, 0.3), strength=4.0)
    return m


def begin(tab):
    m, root = start(tab, beats=3, page="ymtc")
    return mats(m), root


def export(tab):
    out = os.path.join(PBR_DIR, "assets", "mem", f"ymtc_{tab}.glb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out, export_format="GLB", export_yup=True, export_animations=True,
        export_force_sampling=True, export_frame_step=1, export_cameras=False,
        export_lights=False, use_selection=False,
    )
    print("exported", out)


def grp(parent, name, intervals=None):
    g = empty(name, parent)
    if intervals is not None:
        show(g, intervals)
    return g


def bar(parent, name, x, z, w, d, m, keys, y0=0.0, down=False, vis=None):
    """A vertical bar standing at (x, y0, z) (hanging down if `down`), height keyed by
    [(frame, mm)]; it pops on at the first key. `vis` optionally limits when it shows."""
    holder = grp(parent, name + "_v", vis)
    pv = pivot(name, (x, y0, z), holder)
    lo, hi = (-1000.0, 0.0) if down else (0.0, 1000.0)
    box(name + "_m", (-w / 2, lo, -d / 2), (w / 2, hi, d / 2), m, pv)
    key(pv, 0, "scale", (OFF, OFF, OFF))
    for f, h in keys:
        key(pv, f, "scale", (1, 1, max(h / 1000.0, OFF)))
    _constant_until(pv, keys[0][0])
    return pv


def gbox(parent, name, lo, hi, m, intervals=None):
    g = grp(parent, name, intervals)
    box(name + "_m", lo, hi, m, g)
    return g


def stripes(parent, name, x, z, w, d, total, y0, f0, f1, ma, mb, step=40.0, until=END):
    """A column of `total` mm built from `step`-mm stripes that appear bottom to top."""
    n = math.ceil(total / step - 1e-6)
    for k in range(n):
        lo = y0 + k * step
        hi = min(y0 + total, lo + step)
        fk = round(f0 + (f1 - f0) * k / max(1, n - 1))
        gbox(parent, f"{name}{k}", (x - w / 2, lo, z - d / 2), (x + w / 2, hi - 3, z + d / 2),
             ma if k % 2 == 0 else mb, [(fk, until)])


def flat_cam(root, poses):
    camera(root, poses)


# ---- snapshot ----------------------------------------------------------------------------


def s_snapshot():
    m, root = begin("snapshot")
    g = empty("snap", root)
    for x in (-2600, 0, 2600):
        box(f"ped{x}", (x - 900, -150, -600), (x + 900, 0, 600), m["plate"], g)
    # make: a 300 mm wafer and a 267-layer stack (3 mm per layer)
    disc("wafer", (-2600, 15, 0), 720, 30, m["si"], g)
    stripes(g, "nand", -2600, 0, 520, 520, 267 * 3, 30, F(0, 0.05), F(0, 0.45), m["purple"], m["purple2"])
    label("267-layer NAND, Xtacking 4.0", (-2860, 840, 0), root, B(0, 0.45))
    label("~160k wafers/month est", (-3300, 40, 300), root, B(0, 0.5))
    # sell: a ring of 50 segments (2% each), YMTC 7 of them = 14% (Counterpoint, 2026Q2)
    cx, cy, r = 0.0, 650.0, 480.0
    for k in range(50):
        a0 = math.pi / 2 - 2 * math.pi * k / 50 - 0.02
        a1 = math.pi / 2 - 2 * math.pi * (k + 1) / 50 + 0.02
        pa = (cx + r * math.cos(a0), cy + r * math.sin(a0), 0)
        pb = (cx + r * math.cos(a1), cy + r * math.sin(a1), 0)
        ymtc = k < 7
        e = grp(g, f"seg{k}", [(F(1, 0.05 + 0.35 * k / 49) if not ymtc else F(1, 0.5), END)])
        tube(f"seg{k}_t", pa, pb, 70 if ymtc else 50, m["purple"] if ymtc else m["grey2"], e, verts=8)
    label("14% of NAND revenue, 2026Q2", (300, 1100, 0), root, B(1, 0.55))
    label("Counterpoint", (-480, 300, 0), root, B(1, 0.6))
    # earn: Q1 2026 revenue 47.0 = cost 13.6 + profit 33.4 (CNY B), 20 mm per B
    bar(g, "cost", 2600, 0, 700, 600, m["grey"], [(F(2, 0.05), 1), (F(2, 0.3), 272)])
    bar(g, "profit", 2600, 0, 700, 600, m["gold"], [(F(2, 0.32), 1), (F(2, 0.6), 668)], y0=272)
    label("Q1 2026 revenue CNY 47.0B", (2250, 950, 0), root, B(2, 0.62))
    label("net profit CNY 33.4B", (2950, 600, 0), root, B(2, 0.62))
    label("gross margin 76.8%", (2950, 300, 0), root, B(2, 0.7))
    flat_cam(root, [((-1900, 480, 0), 3900, 0.0, 0.16), ((0, 520, 0), 3900, 0.0, 0.12), ((1900, 480, 0), 3900, 0.0, 0.14)])
    export("snapshot")


# ---- revenue -----------------------------------------------------------------------------


def s_revenue():
    m, root = begin("revenue")
    g = empty("rev", root)
    S = 24.0  # mm per CNY B
    box("zero", (-3200, -8, -260), (3200, 8, 260), m["white"], g)
    rows = [  # x, revenue, profit, beat, rev u0-u1, profit u0-u1
        (-2400, 18.7, -19.2, 0, (0.06, 0.32), (0.40, 0.70)),
        (-800, 45.2, 6.77, 1, (0.04, 0.25), (0.25, 0.38)),
        (800, 63.2, 14.2, 1, (0.45, 0.68), (0.68, 0.80)),
        (2400, 47.0, 33.4, 2, (0.04, 0.28), (0.32, 0.60)),
    ]
    for i, (x, rv, pf, b, ur, up) in enumerate(rows):
        bar(g, f"r{i}", x - 190, 0, 340, 340, m["rev"], [(F(b, ur[0]), 1), (F(b, ur[1]), rv * S)])
        bar(g, f"p{i}", x + 190, 0, 340, 340, m["red"] if pf < 0 else m["gold"],
            [(F(b, up[0]), 1), (F(b, up[1]), abs(pf) * S)], down=pf < 0)
    label("2023 revenue CNY 18.7B", (-2600, 18.7 * S + 20, 0), root, B(0, 0.33))
    label("2023 net loss CNY 19.2B", (-2050, -19.2 * S, 0), root, B(0, 0.7))
    label("2024: CNY 45.2B, profit 6.8B", (-1000, 45.2 * S + 20, 0), root, B(1, 0.3))
    label("2025: CNY 63.2B, profit 14.2B", (600, 63.2 * S + 20, 0), root, B(1, 0.72))
    label("Q1 2026 alone: CNY 47.0B", (2200, 47.0 * S + 20, 0), root, B(2, 0.3))
    label("Q1 profit 33.4B = 2.35x 2025", (2560, 33.4 * S, 0), root, B(2, 0.62))
    flat_cam(root, [((-700, 480, 0), 4700, 0.0, 0.10), ((0, 560, 0), 4700, 0.0, 0.10), ((200, 560, 0), 4700, 0.0, 0.10)])
    export("revenue")


# ---- margins -----------------------------------------------------------------------------


def s_margins():
    m, root = begin("margins")
    g = empty("mar", root)
    H = 900.0  # one column = each yuan of revenue
    box("floor", (-3000, -60, -400), (3000, 0, 400), m["floor"], g)
    gbox(g, "line", (-3000, H - 6, -330), (3000, H + 6, 330), m["glass"])
    # 2023: costs = revenue + 19.2B loss = 2.03x revenue (net margin -102.7%)
    bar(g, "c23", -2100, 0, 600, 500, m["grey"], [(F(0, 0.06), 1), (F(0, 0.3), H)])
    bar(g, "l23", -2100, 0, 600, 500, m["red"], [(F(0, 0.34), 1), (F(0, 0.7), H * 1.027)], y0=H)
    label("2023: costs 2x revenue", (-2400, H * 2.027, 0), root, B(0, 0.7))
    label("net margin -102.7%", (-1800, H * 1.5, 0), root, B(0, 0.75))
    label("revenue = 100%", (-2950, H, 0), root, B(0, 0.3, 0.68))
    for x, net, nm, u in ((-700, 0.15, "2024 net margin 15.0%", 0.05), (700, 0.225, "2025 net margin 22.5%", 0.45)):
        bar(g, f"c{x}", x, 0, 600, 500, m["grey"], [(F(1, u), 1), (F(1, u + 0.2), H * (1 - net))])
        bar(g, f"g{x}", x, 0, 600, 500, m["gold"], [(F(1, u + 0.22), 1), (F(1, u + 0.35), H * net)], y0=H * (1 - net))
        label(nm, (x - 300, H + 20, 0), root, B(1, u + 0.35))
    # Q1 2026: starts at the 2025 split, then prices rise and the cost share shrinks to 28.9%
    c = bar(g, "cq", 2100, 0, 600, 500, m["grey"], [(F(2, 0.04), 1), (F(2, 0.2), H * 0.775), (F(2, 0.35), H * 0.775), (F(2, 0.7), H * 0.289)])
    holder = grp(g, "gq_v")
    pv = pivot("gq", (2100, H, 0), holder)  # gold hangs from the 100% line and grows down
    box("gq_m", (-300, -1000, -250), (300, 0, 250), m["gold"], pv)
    key(pv, 0, "scale", (OFF, OFF, OFF))
    for f, h in ((F(2, 0.22), 1), (F(2, 0.32), H * 0.225), (F(2, 0.35), H * 0.225), (F(2, 0.7), H * 0.711)):
        key(pv, f, "scale", (1, 1, h / 1000))
    _constant_until(pv, F(2, 0.22))
    label("Q1 2026 net margin 71.1%", (1800, H + 20, 0), root, B(2, 0.7))
    label("gross margin 76.8%", (2400, H * 0.6, 0), root, B(2, 0.75))
    label("NAND price +173% vs 2025 est", (2400, H * 0.15, 0), root, B(2, 0.38))
    flat_cam(root, [((-600, 900, 0), 5300, 0.0, 0.10), ((0, 800, 0), 5000, 0.0, 0.10), ((300, 800, 0), 5000, 0.0, 0.10)])
    export("margins")


# ---- capacity: three gauges --------------------------------------------------------------


def gauge(g, m, name, cx, cy, r, value, f0, f1, vmax=250.0):
    gbox(g, f"{name}_face", (cx - r - 260, cy - 260, -120), (cx + r + 260, cy + r + 260, -60), m["plate"])
    box(f"{name}_ped", (cx - 500, cy - 600, -300), (cx + 500, cy - 260, 300), m["floor"], g)
    n = 25
    for k in range(n):
        a0 = math.pi * (1 - k / n) - 0.015
        a1 = math.pi * (1 - (k + 1) / n) + 0.015
        pa = (cx + r * math.cos(a0), cy + r * math.sin(a0), 0)
        pb = (cx + r * math.cos(a1), cy + r * math.sin(a1), 0)
        tube(f"{name}_d{k}", pa, pb, 55, m["dim"], g, verts=8)
        if (k + 1) * 10 <= value + 1e-6:
            fk = round(f0 + (f1 - f0) * (k + 1) * 10 / value)
            e = grp(g, f"{name}_l{k}", [(fk, END)])
            tube(f"{name}_lt{k}", (pa[0], pa[1], 20), (pb[0], pb[1], 20), 70, m["rev"], e, verts=8)
    for v in range(0, 251, 50):
        a = math.pi * (1 - v / vmax)
        tube(f"{name}_t{v}", (cx + (r + 110) * math.cos(a), cy + (r + 110) * math.sin(a), 0),
             (cx + (r + 230) * math.cos(a), cy + (r + 230) * math.sin(a), 0), 18, m["white"], g, verts=6)
    ball(f"{name}_hub", (cx, cy, 60), 95, m["white"], g, 16)
    pv = empty(f"{name}_needle", g, P(cx, cy, 80))
    tube(f"{name}_n", (0, 0, 0), (0, r * 0.95, 0), 30, m["gold"], pv, verts=8)
    key(pv, 0, "rotation_euler", (0, -math.pi / 2, 0))
    key(pv, f0, "rotation_euler", (0, -math.pi / 2, 0), linear=True)
    key(pv, f1, "rotation_euler", (0, value / vmax * math.pi - math.pi / 2, 0), linear=True)
    # 2025 average output, 1.77M wafers / 12 = ~148k/month (Korea Herald via Tribune)
    a = math.pi * (1 - 147.5 / vmax)
    e = grp(g, f"{name}_avg", [(F(2, 0.6), END)])
    tube(f"{name}_avgt", (cx + (r - 140) * math.cos(a), cy + (r - 140) * math.sin(a), 40),
         (cx + (r + 260) * math.cos(a), cy + (r + 260) * math.sin(a), 40), 26, m["red"], e, verts=8)
    return (cx + (r + 230) * math.cos(a), cy + (r + 230) * math.sin(a), 40)


def s_capacity():
    m, root = begin("capacity")
    g = empty("cap", root)
    r = 760.0
    gauge(g, m, "g1", -2500, 0, r, 130, F(0, 0.08), F(0, 0.5))
    gauge(g, m, "g2", 0, 0, r, 160, F(1, 0.08), F(1, 0.5))
    tip = gauge(g, m, "g3", 2500, 0, r, 200, F(2, 0.08), F(2, 0.5))
    pt = lambda cx, v: (cx + 0.95 * r * math.cos(math.pi * (1 - v / 250)), 0.95 * r * math.sin(math.pi * (1 - v / 250)), 80)
    label("130k wpm est (Notebookcheck)", pt(-2500, 130), root, B(0, 0.5))
    label("same fabs, end-2024: 130k", (-3200, -350, 300), root, B(0, 0.6))
    label("130k", pt(-2500, 130), root, B(1) + B(2))
    label("160k est (TrendForce, Caixin)", pt(0, 160), root, B(1, 0.5))
    label("160k", pt(0, 160), root, B(2))
    label("200k est (Reuters, Apr 2026)", pt(2500, 200), root, B(2, 0.5))
    label("2025 output ~148k/mo avg est", tip, root, B(2, 0.65))
    flat_cam(root, [((0, 250, 0), 5300, 0.0, 0.08), ((0, 250, 0), 5300, 0.0, 0.08), ((0, 250, 0), 5300, 0.0, 0.08)])
    export("capacity")


# ---- share -------------------------------------------------------------------------------


def s_share():
    m, root = begin("share")
    g = empty("share", root)
    S = 60.0  # mm per percentage point
    box("floor", (-4100, -60, -400), (4100, 0, 400), m["floor"], g)
    q = [("2025Q2", 11, 0, 0.05), ("2025Q3", 10, 0, 0.45), ("2025Q4", 12, 1, 0.05), ("2026Q1", 14, 1, 0.35), ("2026Q2", 14, 1, 0.65)]
    for i, (name, v, b, u) in enumerate(q):
        x = -3600 + 650 * i
        bar(g, f"q{i}", x, 0, 460, 460, m["purple"], [(F(b, u), 1), (F(b, u + 0.22), v * S)])
        label(f"{name}: {v}%" + (" (Counterpoint)" if i == 4 else ""), (x - 200, v * S + 10, 0), root, B(b, u + 0.22) if b == 0 else B(1, u + 0.22))
    peers = [("Samsung", 29), ("SK hynix", 18), ("Kioxia", 14), ("Micron", 13), ("SanDisk", 13), ("YMTC", 13)]
    for i, (name, v) in enumerate(peers):
        x = 600 + 620 * i
        u = 0.05 + 0.06 * i if name != "YMTC" else 0.5
        bar(g, f"c{i}", x, 0, 460, 460, m["purple"] if name == "YMTC" else m["grey"], [(F(2, u), 1), (F(2, u + 0.2), v * S)])
    label("Samsung 29%", (400, 29 * S + 10, 0), root, B(2, 0.25))
    label("SK hynix 18%", (1020, 18 * S + 10, 0), root, B(2, 0.3))
    label("Micron, SanDisk 13% each", (2460, 13 * S, 0), root, B(2, 0.5))
    label("YMTC 13% (other table: 14%)", (3700, 13 * S + 10, 0), root, B(2, 0.72))
    flat_cam(root, [((-200, 800, 0), 5900, 0.0, 0.10), ((-200, 800, 0), 5900, 0.0, 0.10), ((700, 900, 0), 5900, 0.0, 0.10)])
    export("share")


# ---- layers: Xtacking, layer counts, gates vs data layers --------------------------------


def s_layers():
    m, root = begin("layers")
    g = empty("lay", root)
    v0 = grp(g, "b0", B(0))
    # the array wafer: silicon, the word-line stack with channel holes, copper pads on top
    box("arr_si", (600, 0, -400), (2600, 120, 400), m["si"], v0)
    for k in range(10):
        box(f"arr_st{k}", (600, 120 + 40 * k, -400), (2600, 157 + 40 * k, 400), m["purple"] if k % 2 else m["purple2"], v0)
    for i, x in enumerate(range(750, 2500, 200)):
        tube(f"arr_ch{i}", (x, 120, 400), (x, 520, 400), 28, m["white"], v0, verts=8)
        box(f"arr_pad{i}", (x + 50, 520, -300), (x + 140, 550, 400), m["copper"], v0)
    # the CMOS wafer, built about its centre so it can flip face down
    cm = pivot("cmos", (-1600, 160, 0), v0)
    box("cm_si", (-1000, -160, -400), (1000, 40, 400), m["si"], cm)
    box("cm_logic", (-1000, 40, -400), (1000, 130, 400), m["green"], cm)
    for i, x in enumerate(range(-850, 900, 200)):
        box(f"cm_pad{i}", (x + 50, 130, -300), (x + 140, 160, 400), m["copper"], cm)
    for f, loc in ((F(0, 0.05), (-1600, 160, 0)), (F(0, 0.26), (-1600, 1250, 0)), (F(0, 0.48), (-1600, 1250, 0)),
                   (F(0, 0.68), (1600, 1250, 0)), (F(0, 0.84), (1600, 710, 0))):
        key(cm, f, "location", P(*loc))
    key(cm, 0, "rotation_euler", (0, 0, 0))
    key(cm, F(0, 0.27), "rotation_euler", (0, 0, 0))
    key(cm, F(0, 0.47), "rotation_euler", (math.pi, 0, 0))
    gbox(v0, "bondglow", (600, 543, -405), (2600, 562, 405), m["bond"], [(F(0, 0.84), F(1, 0))])
    label("CMOS logic wafer", (0, 0, 410), cm, B(0, 0.02, 0.26))
    label("CMOS flips face down", (0, 1400, 0), root, B(0, 0.3, 0.68))
    label("NAND array wafer", (1000, 330, 410), root, B(0, 0.02))
    label("Cu-Cu bond, face to face", (2600, 555, 0), root, B(0, 0.85))
    label("logic on top, built apart", (1100, 860, 0), root, B(0, 0.88))
    # beat 1: reported layer counts, 4 mm per layer
    cols = [(-2100, 232, m["purple"], m["purple2"], 0.03, 0.28, "232 layers, 2022 (Xtacking 3)"),
            (-700, 267, m["purple"], m["purple2"], 0.30, 0.56, "267 layers, 2026 (Xtacking 4)"),
            (700, 286, m["grey"], m["grey2"], 0.60, 0.78, "Samsung 286 (TrendForce)"),
            (2100, 321, m["grey"], m["grey2"], 0.60, 0.78, "SK hynix 321 (TrendForce)")]
    for i, (x, n, ma, mb, u0, u1, text) in enumerate(cols):
        stripes(g, f"lc{i}", x, 0, 800, 600, n * 4, 0, F(1, u0), F(1, u1), ma, mb, until=F(2, 0))
        label(text, (x - 380, n * 4, 0), root, B(1, u1))
    # beat 2: TechInsights counted 294 gates (150 lower deck + 144 upper); 267 store data
    lo = grp(g, "lowdeck", B(2))
    stripes(lo, "ld", -1000, 0, 900, 600, 600, 0, F(2, 0.03), F(2, 0.16), m["purple"], m["purple2"])
    for y in (0, 568):
        gbox(lo, f"ldr{y}", (-1460, y, -310), (-540, y + 32, 310), m["red"], [(F(2, 0.18), END)])
    up = grp(g, "updeck", B(2))
    stripes(up, "ud", -1000, 0, 900, 600, 576, 600, F(2, 0.17), F(2, 0.3), m["purple"], m["purple2"])
    for y in (600, 1144):
        gbox(up, f"udr{y}", (-1460, y, -310), (-540, y + 32, 310), m["red"], [(F(2, 0.32), END)])
    key(up, F(2, 0.36), "location", P(0, 0, 0))
    key(up, F(2, 0.48), "location", P(0, 160, 0))
    stripes(g, "active", 1000, 0, 900, 600, 267 * 4, 0, F(2, 0.55), F(2, 0.75), m["purple"], m["purple2"])
    label("lower deck: 150 gates", (-1450, 300, 0), root, B(2, 0.18))
    label("upper deck: 144 gates", (-1450, 1050, 0), root, B(2, 0.48))
    label("294 gates counted (TechInsights)", (-1400, 1336, 0), root, B(2, 0.5))
    label("267 store data (270 per TF)", (600, 1068, 0), root, B(2, 0.75))
    flat_cam(root, [((0, 800, 0), 4300, 0.0, 0.16), ((0, 660, 0), 4100, 0.0, 0.14), ((0, 700, 0), 3900, 0.0, 0.12)])
    export("layers")


# ---- funding -----------------------------------------------------------------------------


def s_funding():
    m, root = begin("funding")
    g = empty("fund", root)
    S = 6.0  # mm per CNY B
    box("floor", (-4400, -60, -500), (2600, 0, 500), m["floor"], g)
    for i, x in enumerate((-3700, -2900, -2100)):
        box(f"src{i}", (x - 260, 1200, -260), (x + 260, 1540, 260), m["red"], g)
        run(g, f"flow{i}", 9, [(x, 1180, 0), (x, 900, 0), (-1000, 470, 0), (-1000, 300, 0)], 45, m["gold"], 0, 0.05, 0.6, 60)
    gbox(g, "tank", (-1800, 0, -420), (-200, 450, 420), m["glass"])
    fill = bar(g, "fill", -1000, 0, 1500, 760, m["gold"], [(F(0, 0.15), 1), (F(0, 0.75), 49 * S), (F(1, 0.15), 49 * S), (F(1, 0.6), (49 + 9.44) * S)])
    label("Big Fund II ~CNY 13.0B est", (-3900, 1540, 0), root, B(0, 0.1))
    label("Mar 2023: CNY 49.0B, state est", (-1700, 49 * S, 0), root, B(0, 0.7))
    label("reg. capital >CNY 105B est", (-300, 450, 0), root, B(0, 0.78))
    inv = grp(g, "investors", [(F(1, 0.0), END)])
    for k in range(15):
        x = -3950 + 160 * k
        box(f"inv{k}", (x - 55, 1650, -55), (x + 55, 1760, 55), m["rev"], inv)
        if k % 3 == 1:
            run(g, f"drop{k}", 3, [(x, 1630, 0), (x, 1300, 0), (-1000, 470, 0), (-1000, 340, 0)], 32, m["gold"], 1, 0.05 + 0.02 * k, 0.45, 55)
    label("15-16 investors", (-3950, 1760, 0), root, B(1, 0.05))
    label("Apr 2025 round CNY 9.4B est", (-1700, 58.4 * S, 0), root, B(1, 0.6))
    bar(g, "tower", 1500, 0, 800, 700, m["rev"], [(F(1, 0.5), 1), (F(1, 0.85), 161.6 * S), (F(2, 0.12), 161.6 * S), (F(2, 0.5), 302.5 * S)])
    label("post-money CNY 161.6B est", (1100, 161.6 * S, 0), root, B(1, 0.85))
    gbox(g, "mark160", (1000, 160 * S - 8, -380), (2000, 160 * S + 8, 380), m["white"], [(F(2, 0.05), END)])
    gbox(g, "band", (950, 275 * S, -400), (2050, 330 * S, 400), m["goldglass"], [(F(2, 0.5), END)])
    label("2025 marks CNY 160-162B est", (2000, 160 * S, 0), root, B(2, 0.1))
    label("IPO range CNY 275-330B", (1000, 330 * S, 0), root, B(2, 0.52))
    flat_cam(root, [((-1000, 900, 0), 4900, 0.0, 0.10), ((-900, 950, 0), 4900, 0.0, 0.10), ((-700, 1000, 0), 4900, 0.0, 0.10)])
    export("funding")


# ---- ipo ---------------------------------------------------------------------------------


def s_ipo():
    m, root = begin("ipo")
    g = empty("ipo", root)
    box("floor", (-3600, -60, -500), (3600, 0, 500), m["floor"], g)
    box("market", (-2500, 1650, -300), (-1500, 1900, 300), m["rev"], g)
    S = 28.0  # mm per CNY B in the bins
    for name, x, v, n in (("lines", -2750, 20.8, 12), ("rd", -1250, 12.2, 7)):
        gbox(g, f"bin_{name}", (x - 450, 0, -350), (x + 450, 680, 350), m["glass"])
        run(g, f"f_{name}", n, [(-2000, 1630, 0), (-2000, 1300, 0), (x, 800, 0), (x, 200, 0)], 50, m["gold"], 0, 0.05, 0.6, 50)
        bar(g, f"fill_{name}", x, 0, 820, 640, m["gold"], [(F(0, 0.15), 1), (F(0, 0.75), v * S)])
    label("raise target CNY 33.0B", (-2500, 1900, 0), root, B(0, 0.05))
    label("production lines CNY 20.8B", (-3150, 20.8 * S, 0), root, B(0, 0.72))
    label("R&D CNY 12.2B", (-1650, 12.2 * S, 0), root, B(0, 0.72))
    # valuation tower built of 2025-profit blocks (14.2B each, 5 mm per B): 21.3 of them
    V = 5.0
    stripes(g, "tower", 1200, 0, 700, 600, 302.5 * V, 0, F(1, 0.12), F(1, 0.5), m["rev"], m["rev2"], step=14.2 * V)
    gbox(g, "band", (750, 275 * V, -380), (1650, 330 * V, 380), m["goldglass"], [(F(1, 0.5), END)])
    bar(g, "p25", 2200, 0, 500, 500, m["gold"], [(F(1, 0.04), 1), (F(1, 0.1), 14.2 * V)])
    bar(g, "q1x4", 3000, 0, 500, 500, m["gold"], [(F(1, 0.55), 1), (F(1, 0.75), 33.4 * 4 * V)])
    label("valuation CNY 275-330B", (850, 330 * V, 0), root, B(1, 0.5))
    label("21.3x 2025 profit est", (2000, 14.2 * V + 10, 0), root, B(1, 0.15))
    label("2.3x Q1 2026 profit x4 est", (2800, 133.6 * V, 0), root, B(1, 0.76))
    # beat 2: the listing is put on hold; a red gate drops under the market
    gate = pivot("gate", (0, 0, 0), g)
    box("gate_m", (-3300, 1180, -380), (-700, 1260, 380), m["red"], gate)
    key(gate, 0, "location", P(0, 2500, 0))
    key(gate, F(2, 0.1), "location", P(0, 2500, 0))
    key(gate, F(2, 0.24), "location", P(0, 0, 0))
    _constant_until(gate, F(2, 0.1))
    run(g, "stuck", 10, [(-2000, 1630, 0), (-2000, 1290, 0)], 50, m["gold"], 2, 0.26, 0.9, 20)
    label("on hold: Reuters, 2026-11-04", (-2000, 1260, 380), root, B(2, 0.25))
    label("valuation CNY 275-330B", (850, 330 * V, 0), root, B(2, 0.3))
    flat_cam(root, [((-900, 950, 0), 5300, 0.0, 0.10), ((300, 850, 0), 5200, 0.0, 0.10), ((100, 900, 0), 5400, 0.0, 0.10)])
    export("ipo")


# ---- sanctions ---------------------------------------------------------------------------


def tool(parent, name, x, m, w=440, h=620):
    e = empty(name, parent)
    box(name + "_b", (x - w / 2, 0, -260), (x + w / 2, h, 260), m, e)
    box(name + "_c", (x - w / 2 + 40, h, -200), (x + w / 2 - 40, h + 90, 200), m, e)
    return e


def s_sanctions():
    m, root = begin("sanctions")
    g = empty("sanc", root)
    box("ground", (-5200, -60, -700), (8600, 0, 700), m["floor"], g)
    box("borderline", (-2030, 0, -700), (-1970, 6, 700), m["white"], g)
    # Fab 1-2: floor, back wall, roof; 4 bays
    box("fab_back", (-1200, 0, -700), (1900, 1250, -600), m["plate"], g)
    box("fab_roof", (-1250, 1250, -700), (1950, 1330, 600), m["grey2"], g)
    box("fab_right", (1900, 0, -700), (1960, 1250, 600), m["plate"], g)
    bays = [-800, -100, 600, 1300]
    for i in range(3):
        t = tool(g, f"ft{i}", -4400, m["tool"])
        f0 = F(0, 0.04 + 0.13 * i)
        key(t, 0, "location", P(0, 0, 0))
        fly(t, [(0, 0, 0), (bays[i] + 4400, 0, 0)], f0, f0 + 60, steps=2)
    t4 = tool(g, "ft3", -4400, m["tool"])
    key(t4, F(0, 0.45), "location", P(0, 0, 0))
    key(t4, F(0, 0.7), "location", P(4400 - 2330, 0, 0), linear=True)
    wall = pivot("wall", (-2000, 0, 0), g)
    box("wall_m", (-60, 0, -700), (60, 1400, 700), m["red"], wall)
    key(wall, 0, "scale", (OFF, OFF, OFF))
    key(wall, F(0, 0.55), "scale", (1, 1, OFF))
    key(wall, F(0, 0.64), "scale", (1, 1, 1))
    _constant_until(wall, F(0, 0.55))
    gbox(g, "emptybay", (1300 - 300, 0, -500), (1300 + 300, 900, 400), m["redglass"], [(F(0, 0.7), F(2, 0))])
    label("US Entity List, 2022-12-15", (-2000, 1400, 0), root, B(0, 0.64))
    label("36 Chinese firms added", (-2000, 700, 700), root, B(0, 0.7))
    label("foreign tools", (-4400, 700, 0), root, B(0, 0.0, 0.4))
    # beat 1: expansion stalls: domestic tool orders cut, the year ends in a loss
    for k in range(10):
        x = 2500 + (k % 5) * 300
        z = -200 if k < 5 else 250
        e = grp(g, f"naura{k}", [(F(1, 0.0), F(1, 0.3 + 0.04 * k) if k >= 3 else F(2, 0))])
        box(f"naura{k}_m", (x - 110, 0, z - 110), (x + 110, 260, z + 110), m["gold"], e)
    bar(g, "loss", 600, 950, 700, 300, m["red"], [(F(1, 0.55), 1), (F(1, 0.8), 19.2 * 30)], down=True, vis=B(1))
    label("Naura orders cut 70% est", (2500, 300, 0), root, B(1, 0.7))
    label("2023 net loss CNY 19.2B", (950, -576, 950), root, B(1, 0.8))
    label("bay left empty", (1300, 900, 0), root, B(1, 0.05))
    # beat 2: Fab 3, more than half its tools from Chinese makers
    f3 = grp(g, "fab3", [(F(2, 0.0), END)])
    box("f3_back", (3200, 0, -700), (7400, 1250, -600), m["plate"], f3)
    box("f3_roof", (3150, 1250, -700), (7450, 1330, 600), m["grey2"], f3)
    box("f3_half", (3200, 2, -600), (5300, 10, 600), m["goldglass"], f3)
    box("f3_mid", (5280, 2, -600), (5320, 14, 600), m["white"], f3)
    bays3 = [3550, 4250, 4950, 5650, 6350, 7050]
    for i, x in enumerate(bays3):
        if i < 4:
            t = tool(f3, f"dt{i}", 9200, m["gold"])
            f0 = F(2, 0.05 + 0.1 * (3 - i))
            key(t, f0, "location", P(0, 0, 0))
            key(t, f0 + 50, "location", P(x - 9200, 0, 0))
            _constant_until(t, f0)
        else:
            tool(f3, f"ot{i}", x, m["tool"])
    label("Fab 3: >50% domestic tools est", (3600, 1330, 0), root, B(2, 0.5))
    label("design capacity 100k wpm est", (6800, 1330, 0), root, B(2, 0.6))
    label("Phase III capital CNY 20.7B est", (4200, 0, 600), root, B(2, 0.65))
    flat_cam(root, [((-1500, 650, 0), 4900, 0.0, 0.12), ((800, 250, 0), 5200, 0.0, 0.12), ((5200, 650, 0), 4300, 0.0, 0.12)])
    export("sanctions")


# ---- sources -----------------------------------------------------------------------------


def s_sources():
    m, root = begin("sources")
    g = empty("src", root)
    stacks = [("TrendForce", 11), ("Caixin", 9), ("Tribune", 7), ("Admirals", 7), ("StorageNL", 7), ("Global Times", 5), ("Counterpoint", 5), ("GetFlashMemory", 5)]
    v0 = grp(g, "stacks", B(0))
    k = 0
    for i, (name, n) in enumerate(stacks):
        x = -2800 + 800 * i
        for j in range(n):
            e = empty(f"sh{i}_{j}", v0)
            box(f"sh{i}_{j}_m", (x - 280, 85 * j, -380), (x + 280, 85 * j + 70, 380), m["paper"], e)
            f = F(0, 0.03 + 0.6 * k / 55)
            key(e, 0, "location", P(0, 3000, 0))
            key(e, f, "location", P(0, 400, 0))
            key(e, f + 6, "location", P(0, 0, 0))
            _constant_until(e, f)
            k += 1
    label("TrendForce: 11 numbers", (-3060, 935, 0), root, B(0, 0.2))
    label("Caixin Global: 9", (-2260, 765, 0), root, B(0, 0.3))
    label("94 numbers, 24 source pages", (2500, 425, 0), root, B(0, 0.7))
    # beat 1: the same year, opposite signs (2023 net income)
    S = 45.0
    box("zero1", (-1600, -8, -300), (1600, 8, 300), m["white"], grp(g, "z1", B(1)))
    bar(g, "tmt", -500, 0, 600, 500, m["gold"], [(F(1, 0.08), 1), (F(1, 0.2), 0.531 * S)], vis=B(1))
    bar(g, "gt", 500, 0, 600, 500, m["red"], [(F(1, 0.25), 1), (F(1, 0.6), 19.2 * S)], down=True, vis=B(1))
    label("2023: +CNY 0.5B (TMTPost)", (-750, 30, 0), root, B(1, 0.2))
    label("2023: -CNY 19.2B (prospectus)", (750, -19.2 * S, 0), root, B(1, 0.6))
    label("14 conflicting values", (-1600, 0, 300), root, B(1, 0.65))
    # beat 2: two more disagreements, the gap glowing red
    pairs = [(-2000, 130, 160, 6.0, "130k wpm (Notebookcheck)", "160k wpm (TrendForce)"),
             (1400, 11, 9, 70.0, "2025Q2 11% (Counterpoint)", "9% (GetFlashMemory table)")]
    for i, (x, a, b, s, ta, tb) in enumerate(pairs):
        bar(g, f"pa{i}", x - 350, 0, 560, 500, m["rev"], [(F(2, 0.05 + 0.3 * i), 1), (F(2, 0.25 + 0.3 * i), a * s)], vis=B(2))
        bar(g, f"pb{i}", x + 350, 0, 560, 500, m["purple"], [(F(2, 0.05 + 0.3 * i), 1), (F(2, 0.25 + 0.3 * i), b * s)], vis=B(2))
        lo, hi = sorted((a * s, b * s))
        gbox(g, f"gap{i}", (x - 700, lo, -300), (x + 700, hi, 300), m["redglass"], [(F(2, 0.3 + 0.3 * i), F(3, 0))])
        label(ta, (x - 600, a * s, 0), root, B(2, 0.25 + 0.3 * i))
        label(tb, (x + 600, b * s, 0), root, B(2, 0.25 + 0.3 * i))
    flat_cam(root, [((0, 450, 0), 4600, 0.0, 0.12), ((0, -330, 0), 3600, 0.0, 0.10), ((-300, 500, 0), 4600, 0.0, 0.10)])
    export("sources")


SCENES = {
    "snapshot": s_snapshot, "revenue": s_revenue, "margins": s_margins, "capacity": s_capacity,
    "share": s_share, "layers": s_layers, "funding": s_funding, "ipo": s_ipo,
    "sanctions": s_sanctions, "sources": s_sources,
}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(SCENES)
    for t in which:
        SCENES[t]()
