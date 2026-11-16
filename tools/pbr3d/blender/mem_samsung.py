"""Samsung Electronics (005930.KS) memory page: one purpose-built 3D scene per tab.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/mem_samsung.py [-- <tab id> ...]

Each scene is 3 beats of 8 s (24 fps, frames 0..576) framed wide (about 3:1) and exported to
tools/pbr3d/assets/mem/samsung_<tab>.glb, which py/derive/memory_page.py picks up.

Every number drawn (bar heights, ring fills, wafer counts, tag text) comes from the page data:
data/memory_facts/ssg-fin.jsonl, ssg-ops.jsonl, mkt-share.jsonl and the OpenDART series in the
cached page JSON (py/derive/memory_page.py 005930.KS --json). The source of each figure is noted
next to it below. "est" in a tag marks a third-party estimate.

  snapshot     one year apart: memory revenue, DS margin, HBM share and DRAM share, then and now
  group        memory swallowing the conglomerate: revenue and profit towers, memory 14% -> 70%
  memory       15 quarters of memory revenue rising out of the 2023 trough, DS profit beside it
  dramnand     DRAM and NAND revenue towers next to price and bit moves: price did the lifting
  hbm          HBM share towers: Samsung late (15%), closing the gap to SK hynix, HBM4 60% of sales
  hbmtimeline  HBM3E 12H waits ~18 months at Nvidia's gate, then HBM4 ships Feb 2026
  share        DRAM podium: Samsung loses No.1 to SK hynix in 2025, takes it back in 2026
  capacity     capex flat then up, 1c DRAM wafer stacks ramping, P4 / P5 / Yongin / Taylor fabs
  tech         V-NAND layer columns 236 -> 286 -> 400+, V10 bonded on a separate periphery wafer
  sources      document piles per source type, OpenDART, and two places where sources disagree
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, box, disc, empty, key, label, mat, pivot, show, tube  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import hbm_kit as H  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "assets", "mem"))
SLUG = "samsung"
BEATS = 3
END = F(40, 0)
REF = 1000.0  # columns are built REF mm tall and scaled to their height


# ---- materials --------------------------------------------------------------------------


def mats(m):
    H.mats(m)
    m["mem"] = mat("ss_memory", (0.93, 0.52, 0.18), rough=0.45)
    m["mem2"] = mat("ss_memory_dark", (0.78, 0.40, 0.12), rough=0.5)
    m["rest"] = mat("ss_rest", (0.40, 0.43, 0.50), metal=0.2, rough=0.6)
    m["rest2"] = mat("ss_rest_dark", (0.30, 0.32, 0.38), metal=0.2, rough=0.6)
    m["profit"] = mat("ss_profit", (0.96, 0.66, 0.16), metal=0.4, rough=0.35, emit=(1.0, 0.62, 0.12), strength=0.25)
    m["loss"] = mat("ss_loss", (0.92, 0.20, 0.16), emit=(0.95, 0.15, 0.10), strength=2.2)
    m["samsung"] = mat("ss_samsung_blue", (0.16, 0.36, 0.95), metal=0.2, rough=0.4)
    m["samsung2"] = mat("ss_samsung_blue2", (0.10, 0.26, 0.75), metal=0.2, rough=0.45)
    m["skh"] = mat("ss_skhynix", (0.92, 0.36, 0.22), rough=0.45)
    m["skh2"] = mat("ss_skhynix2", (0.76, 0.26, 0.16), rough=0.5)
    m["mu"] = mat("ss_micron", (0.62, 0.66, 0.74), metal=0.3, rough=0.45)
    m["mu2"] = mat("ss_micron2", (0.48, 0.52, 0.60), metal=0.3, rough=0.5)
    m["cxmt"] = mat("ss_cxmt", (0.30, 0.72, 0.42), rough=0.5)
    m["nand"] = mat("ss_nand", (0.22, 0.70, 0.74), metal=0.2, rough=0.4)
    m["nand2"] = mat("ss_nand2", (0.14, 0.55, 0.60), metal=0.2, rough=0.45)
    m["hbm4"] = mat("ss_hbm4", (0.35, 0.92, 1.0), emit=(0.3, 0.85, 1.0), strength=1.6)
    m["glass"] = mat("ss_glass", (0.75, 0.82, 0.92), rough=0.1, alpha=0.16)
    m["ghost"] = mat("ss_ghost", (0.55, 0.60, 0.70), rough=0.4, alpha=0.22)
    m["guide"] = mat("ss_guidance", (0.95, 0.74, 0.30), rough=0.3, alpha=0.30)
    m["floor"] = mat("ss_floor", (0.14, 0.15, 0.18), rough=0.85)
    m["rail"] = mat("ss_rail", (0.32, 0.34, 0.40), metal=0.6, rough=0.4)
    m["green"] = mat("ss_green", (0.30, 0.90, 0.45), emit=(0.25, 0.9, 0.4), strength=2.0)
    m["fab"] = mat("ss_fab", (0.82, 0.84, 0.88), rough=0.6)
    m["fab_roof"] = mat("ss_fab_roof", (0.36, 0.40, 0.48), metal=0.4, rough=0.5)
    m["fab_us"] = mat("ss_fab_us", (0.62, 0.68, 0.80), rough=0.6)
    m["wafer"] = mat("ss_wafer", (0.62, 0.66, 0.74), metal=0.9, rough=0.18)
    m["wafer_1c"] = mat("ss_wafer_1c", (0.55, 0.75, 0.95), metal=0.8, rough=0.2, emit=(0.3, 0.6, 1.0), strength=0.4)
    m["wl_a"] = mat("ss_wordline", (0.70, 0.72, 0.78), metal=0.7, rough=0.3)
    m["wl_b"] = mat("ss_oxide", (0.24, 0.26, 0.32), rough=0.6)
    m["channel"] = mat("ss_channel", (0.95, 0.70, 0.30), emit=(1.0, 0.65, 0.2), strength=0.8)
    m["peri"] = mat("ss_peri", (0.25, 0.45, 0.95), metal=0.2, rough=0.4)
    m["paper"] = mat("ss_paper", (0.90, 0.88, 0.82), rough=0.85)
    m["paper2"] = mat("ss_paper_line", (0.70, 0.68, 0.62), rough=0.85)
    m["dart"] = mat("ss_dart", (0.55, 0.70, 0.95), rough=0.7)
    m["gpu"] = mat("ss_gpu", (0.55, 0.32, 0.90), metal=0.2, rough=0.4)
    return m


# ---- building blocks --------------------------------------------------------------------


def floor(root, m, x0, x1, z0=-700.0, z1=250.0, y=0.0):
    box("floor", (x0, y - 14, z0), (x1, y, z1), m["floor"], root)


def floor_holes(root, m, x0, x1, holes, hz=(-60.0, 60.0), z0=-700.0, z1=250.0):
    """The floor with open holes (hx0, hx1) over hz, so loss bars can hang below zero."""
    box("floor_back", (x0, -14, z0), (x1, 0, hz[0]), m["floor"], root)
    box("floor_front", (x0, -14, hz[1]), (x1, 0, z1), m["floor"], root)
    xs = [x0] + [v for h in sorted(holes) for v in h] + [x1]
    for k in range(0, len(xs), 2):
        box(f"floor_mid{k}", (xs[k], -14, hz[0]), (xs[k + 1], 0, hz[1]), m["floor"], root)


def column(parent, name, x, w, d, m_list, y0=0.0, stripes=1, z1=0.0, gap=0.0):
    """A pivot at (x, y0) holding a REF-tall column `w` wide, `d` deep (front face at z1), made of
    `stripes` bands cycling through `m_list`. Scale its third slot by h / REF to set its height."""
    pv = pivot(name, (x, y0, 0), parent)
    step = REF / stripes
    for k in range(stripes):
        b0 = k * step
        b1 = (k + 1) * step - (gap if k < stripes - 1 else 0.0)
        box(f"{name}_s{k}", (-w / 2, b0, z1 - d), (w / 2, b1, z1), m_list[k % len(m_list)], pv)
    return pv


def down_column(parent, name, x, w, d, mm, y0=0.0, z1=0.0):
    """A column hanging below y0 (losses), REF tall, scaled like `column`."""
    pv = pivot(name, (x, y0, 0), parent)
    box(f"{name}_b", (-w / 2, -REF, z1 - d), (w / 2, 0, z1), mm, pv)
    return pv


def heights(pv, keys):
    """Height keys (frame, mm) on a column pivot. 0 hides it; growing from 0 pops a flat plate on
    first so the column rises instead of swelling from a point."""
    prev = None
    for f, h in sorted(keys):
        if h <= 0:
            key(pv, f, "scale", (OFF, OFF, OFF))
        else:
            if prev is not None and prev[1] <= 0:
                key(pv, prev[0] + 1, "scale", (1, 1, OFF))
            key(pv, f, "scale", (1, 1, h / REF))
        prev = (f, h)
    # the hidden holds must not ramp
    from bpy_extras import anim_utils

    ad = pv.animation_data
    if ad and ad.action:
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        ks = sorted(keys)
        for fc in cb.fcurves:
            for kp in fc.keyframe_points:
                for (fa, ha), (fb, hb) in zip(ks, ks[1:]):
                    if ha <= 0 and fa <= kp.co[0] < fb and hb <= 0:
                        kp.interpolation = "CONSTANT"


def lift_to(pv, x, keys):
    """Location keys (frame, base y) for a pivot at x (stacked columns ride on the one below)."""
    for f, y in keys:
        key(pv, f, "location", P(x, y, 0))


def slide(pv, keys, y=0.0):
    """Location keys (frame, x) for a pivot."""
    for f, x in keys:
        key(pv, f, "location", P(x, y, 0))


def ring(parent, m, name, c, r, keys, mon, segs=100, thick=46.0, depth=70.0):
    """A share ring facing the camera: `segs` tiles round a circle at c = (x, y), clockwise from 12
    o'clock. `keys` (frame, pct) only rise; tile k turns on when the fill passes it. Unfilled tiles
    are ghosts."""
    g = empty(name, parent)
    L = 2 * math.pi * r / segs * 0.82
    p0 = keys[0][1]
    for k in range(segs):
        a = math.pi / 2 - 2 * math.pi * (k + 0.5) / segs

        def tile(nm, mm, par, zoff=0.0, t=thick, dd=depth):
            o = box(nm, (-L / 2, -t / 2, -dd), (L / 2, t / 2, 0), mm, par)
            o.location = P(c[0] + r * math.cos(a), c[1] + r * math.sin(a), -dd / 2 + zoff)
            o.rotation_euler = (0, -(a + math.pi / 2), 0)
            return o

        tile(f"{name}_g{k}", m["ghost"], g, -depth - 4, thick * 0.7, depth * 0.6)
        if k < round(p0):
            tile(f"{name}_t{k}", mon, g)
            continue
        on = None
        for (fa, pa), (fb, pb) in zip(keys, keys[1:]):
            if pb > pa and pa <= k + 0.5 < pb:
                on = round(fa + (k + 0.5 - pa) / (pb - pa) * (fb - fa))
                break
        if on is None:
            continue
        e = empty(f"{name}_e{k}", g)
        tile(f"{name}_t{k}", mon, e)
        show(e, [(on, END)])
    return g


def ring_point(c, r, pct, out=0.0):
    a = math.pi / 2 - 2 * math.pi * pct / 100.0
    return (c[0] + (r + out) * math.cos(a), c[1] + (r + out) * math.sin(a), 10.0)


def after(b, u0=0.45, u1=1.0):
    """Tags switched on once a beat's motion has settled."""
    return [(F(b, u0), F(b, u1))]


def finish(tab):
    os.makedirs(OUT_DIR, exist_ok=True)
    glb = os.path.join(OUT_DIR, f"{SLUG}_{tab}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb,
        export_format="GLB",
        export_yup=True,
        export_animations=True,
        export_force_sampling=True,
        export_frame_step=1,
        export_cameras=False,
        export_lights=False,
        use_selection=False,
    )
    print("exported", glb)


def scene(tab):
    m, root = start(tab, beats=BEATS, page=f"mem_{SLUG}")
    return mats(m), root


# ---- snapshot ---------------------------------------------------------------------------
# One year apart, four gauges. Memory revenue 2025Q3 KRW 26.7T -> 2026Q3 KRW 140.7T (IR deck);
# DS operating margin 21.2% -> 72.4% (DS OI / DS revenue, Newsroom: 7.0/33.1, 106.5/147.1);
# HBM revenue share 23% (2025Q3) -> 33% (2026Q2) and DRAM share 33% (2025Q3) -> 38% (2026Q3),
# both Counterpoint.


def build_snapshot():
    m, root = scene("snapshot")
    floor(root, m, -1700, 1700)
    s = 800.0 / 140.7
    t0, t1 = F(1, 0.08), F(1, 0.62)

    x = -1180
    bar = column(root, "mem_rev", x, 300, 300, [m["mem"], m["mem2"]], stripes=8, gap=4)
    heights(bar, [(0, 26.7 * s), (t0, 26.7 * s), (t1, 140.7 * s)])
    label("2025Q3 memory KRW 26.7T", (x + 150, 26.7 * s, 10), root, after(0, 0.15))
    label("+427% YoY", (x + 150, 0.5 * 140.7 * s, 10), root, after(1, 0.55))
    label("2026Q3 memory KRW 140.7T", (x + 150, 140.7 * s, 10), root, after(2, 0.05))

    x = -420
    gh = 800.0
    disc("margin_glass", (x, gh / 2, -160), 160, gh, m["glass"], root, verts=48)
    disc("margin_cap", (x, gh + 6, -160), 168, 12, m["rail"], root, verts=48)
    fill = pivot("margin_fill", (x, 0, 0), root)
    disc("margin_liquid", (0, REF / 2, -160), 140, REF, m["profit"], fill, verts=48)
    heights(fill, [(0, 21.15 / 100 * gh), (t0, 21.15 / 100 * gh), (t1, 72.4 / 100 * gh)])
    label("DS margin 21.2%", (x + 140, 21.15 / 100 * gh, 0), root, after(0, 0.15))
    label("DS margin 72.4%", (x + 140, 72.4 / 100 * gh, 0), root, after(2, 0.05))

    c = (400, 430)
    ring(root, m, "hbm_ring", c, 280, [(0, 23), (t0, 23), (t1, 33)], m["samsung"])
    label("HBM share 23%", ring_point(c, 280, 23, 25), root, after(0, 0.15))
    label("HBM share 33% (2026Q2)", ring_point(c, 280, 33, 25), root, after(2, 0.05))

    c2 = (1180, 430)
    ring(root, m, "dram_ring", c2, 280, [(0, 33), (t0, 33), (t1, 38)], m["mem"])
    label("DRAM share 33%", ring_point(c2, 280, 33, 25), root, after(0, 0.15))
    label("DRAM share 38%", ring_point(c2, 280, 38, 25), root, after(2, 0.05))

    pose = ((0, 400, 0), 2050, 0.0, 0.10)
    camera(root, [pose, pose, pose])
    finish("snapshot")


# ---- group ------------------------------------------------------------------------------
# OpenDART consolidated revenue and operating income; memory revenue from the IR deck; DS operating
# income from Samsung Newsroom. 2023Q1: group 63.75T, memory 8.92T (14.0%), group OI 0.64T, DS OI
# -4.58T. 2025Q4: group 93.84T, memory 37.1T (39.5%), group OI 20.07T, DS 16.4T. 2026Q2: group
# 171.5T, memory 120.8T (70.4%), group OI 89.49T, DS 89.2T (99.7%).

GROUP = [  # (group rev, memory rev, memory % of group, group OI, DS OI)
    (63.75, 8.92, 13.99, 0.64, -4.58),
    (93.84, 37.1, 39.54, 20.07, 16.4),
    (171.5, 120.8, 70.44, 89.49, 89.2),
]


def build_group():
    m, root = scene("group")
    floor_holes(root, m, -1700, 1700, [(-180 - 170, -180 + 170)], hz=(-320, 20))
    rs = 820.0 / 171.5  # revenue mm per KRW T
    os_ = 680.0 / 89.49  # operating income mm per KRW T
    xr, xo, c = -1080, -180, (1000, 430)
    # each state holds through its beat; the change happens early in the next beat
    times = [(0, 0)]
    for b in (1, 2):
        times.append((F(b, 0.06), b - 1))
        times.append((F(b, 0.42), b))

    mem = column(root, "g_mem", xr, 380, 380, [m["mem"], m["mem2"]], stripes=6, gap=4)
    rest = column(root, "g_rest", xr, 380, 380, [m["rest"], m["rest2"]], stripes=6, gap=4)
    heights(mem, [(f, GROUP[i][1] * rs) for f, i in times])
    heights(rest, [(f, (GROUP[i][0] - GROUP[i][1]) * rs) for f, i in times])
    lift_to(rest, xr, [(f, GROUP[i][1] * rs) for f, i in times])

    ds = column(root, "g_ds", xo, 300, 300, [m["profit"]])
    ds_loss = down_column(root, "g_ds_loss", xo, 300, 300, m["loss"])
    oth = column(root, "g_oth", xo, 300, 300, [m["rest"]])
    heights(ds, [(f, max(GROUP[i][4], 0) * os_) for f, i in times])
    heights(ds_loss, [(f, max(-GROUP[i][4], 0) * os_) for f, i in times])
    heights(oth, [(f, (GROUP[i][3] - max(GROUP[i][4], 0)) * os_) for f, i in times])
    lift_to(oth, xo, [(f, max(GROUP[i][4], 0) * os_) for f, i in times])

    ring(root, m, "g_ring", c, 300, [(0, 13.99), (F(1, 0.06), 13.99), (F(1, 0.42), 39.54),
                                     (F(2, 0.06), 39.54), (F(2, 0.42), 70.44)], m["mem"])

    # tags, one set per beat, at that beat's settled heights
    g, mm, pc, oi, d = GROUP[0]
    label("2023Q1 revenue KRW 63.7T", (xr + 190, g * rs, 10), root, after(0, 0.1))
    label("other units +5.2T, net 0.64T", (xo + 150, (oi + 4.58) * os_, 10), root, after(0, 0.1))
    label("DS loss KRW -4.58T", (xo + 150, -4.58 * os_ / 2, 10), root, after(0, 0.1))
    label("memory 14% of revenue", ring_point(c, 300, 14, 25), root, after(0, 0.1))
    g, mm, pc, oi, d = GROUP[1]
    label("2025Q4 revenue KRW 93.8T", (xr + 190, g * rs, 10), root, after(1))
    label("DS OI KRW 16.4T", (xo + 150, d * os_, 10), root, after(1))
    label("memory 40% (KRW 37.1T)", ring_point(c, 300, pc, 25), root, after(1))
    g, mm, pc, oi, d = GROUP[2]
    label("2026Q2 revenue KRW 171.5T", (xr + 190, g * rs, 10), root, after(2))
    label("memory KRW 120.8T", (xr + 190, mm * rs * 0.5, 10), root, after(2))
    label("DS 99.7% of OI (KRW 89.2T)", (xo + 150, d * os_, 10), root, after(2))
    label("memory 70% of group revenue", ring_point(c, 300, pc, 25), root, after(2))

    pose = ((-20, 410, 0), 2080, 0.0, 0.10)
    camera(root, [pose, pose, pose])
    finish("group")


# ---- memory -----------------------------------------------------------------------------
# Memory revenue by quarter (IR deck "Sales by business"), 2023Q1..2026Q3, and DS operating
# income (Newsroom). DS margin 2026Q3 = 106.5 / 147.1 = 72.4%.

MEM_Q = ["2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1", "2024Q2", "2024Q3", "2024Q4",
         "2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2", "2026Q3"]
MEM_REV = [8.92, 8.97, 10.53, 15.71, 17.49, 21.74, 22.27, 23.0, 19.1, 21.2, 26.7, 37.1, 74.8, 120.8, 140.7]
DS_OI = [-4.58, -4.36, -3.75, -2.18, 1.91, 6.45, 3.86, 2.9, 1.1, 0.4, 7.0, 16.4, 53.7, 89.2, 106.5]


def build_memory():
    m, root = scene("memory")
    floor_holes(root, m, -1700, 1700, [(-1400 + 200 * i + 50 - 40, -1400 + 200 * i + 50 + 40) for i in range(4)],
                hz=(-60, 50))
    s = 820.0 / 140.7
    xs = [-1400 + 200 * i for i in range(15)]
    groups = [(0, range(0, 4)), (1, range(4, 12)), (2, range(12, 15))]
    for b, idx in groups:
        idx = list(idx)
        for j, i in enumerate(idx):
            f0 = F(b, 0.06 + 0.5 * j / len(idx))
            f1 = f0 + 30
            rv = column(root, f"rev{i}", xs[i] - 38, 100, 160, [m["mem"]])
            heights(rv, [(0, 0), (f0, 0), (f1, MEM_REV[i] * s)])
            o = DS_OI[i]
            if o >= 0:
                op = column(root, f"oi{i}", xs[i] + 50, 64, 90, [m["profit"]], z1=40)
            else:
                op = down_column(root, f"oi{i}", xs[i] + 50, 64, 90, m["loss"], z1=40)
            heights(op, [(0, 0), (f0 + 10, 0), (f1 + 10, abs(o) * s)])

    label("2023Q1 memory KRW 8.9T", (xs[0] - 38, MEM_REV[0] * s, 10), root, after(0, 0.4))
    label("DS loss KRW -4.58T", (xs[0] + 50, -4.58 * s, 40), root, after(0, 0.4))
    label("2023Q4 KRW 15.7T", (xs[3] - 38, MEM_REV[3] * s, 10), root, after(0, 0.6))
    label("2024Q4 KRW 23.0T", (xs[7] - 38, MEM_REV[7] * s, 10), root, after(1, 0.5))
    label("2025Q1 dip KRW 19.1T", (xs[8] - 38, MEM_REV[8] * s, 10), root, after(1, 0.55))
    label("2025Q4 KRW 37.1T", (xs[11] - 38, MEM_REV[11] * s, 10), root, after(1, 0.7))
    label("2026Q1 KRW 74.8T", (xs[12] - 38, MEM_REV[12] * s, 10), root, after(2, 0.4))
    label("2026Q3 memory KRW 140.7T", (xs[14] - 38, MEM_REV[14] * s, 10), root, after(2, 0.6))
    label("DS OI KRW 106.5T, 72.4%", (xs[14] + 50, DS_OI[14] * s, 40), root, after(2, 0.6))

    camera(root, [((-1080, 45, 0), 760, 0.0, 0.06),
                  ((-420, 140, 0), 1400, 0.0, 0.08),
                  ((150, 400, 0), 2150, 0.0, 0.10)])
    finish("memory")


# ---- dramnand ---------------------------------------------------------------------------
# Revenue: TrendForce estimates (USD, DRAM incl. HBM). Price and bits: Samsung's stated QoQ moves
# (midpoints of its ranges), ssg-ops. 2023Q1 DRAM $4.17B NAND $2.93B, DRAM ASP -13.5% bits -10.5%;
# 2024Q1 $8.05B / $5.40B, ASP +20% bits -15%; 2026Q2 $60.98B / $23.06B, ASP +45% bits +12%.

DN = [  # (label, DRAM $B, NAND $B, DRAM ASP %, DRAM bits %)
    ("2023Q1", 4.17, 2.93, -13.5, -10.5),
    ("2024Q1", 8.05, 5.40, 20.0, -15.0),
    ("2026Q2", 60.98, 23.06, 45.0, 12.0),
]


def build_dramnand():
    m, root = scene("dramnand")
    floor(root, m, -1700, 1700)
    rs = 820.0 / (60.98 + 23.06)
    ps = 7.0  # mm per percentage point
    base = 330.0
    xt, xp, xb = -820, 420, 980
    times = [(0, 0)]
    for b in (1, 2):
        times.append((F(b, 0.06), b - 1))
        times.append((F(b, 0.40), b))

    dr = column(root, "dn_dram", xt, 520, 420, [m["mem"], m["mem2"]], stripes=6, gap=4)
    nd = column(root, "dn_nand", xt, 520, 420, [m["nand"], m["nand2"]], stripes=4, gap=4)
    heights(dr, [(f, DN[i][1] * rs) for f, i in times])
    heights(nd, [(f, DN[i][2] * rs) for f, i in times])
    lift_to(nd, xt, [(f, DN[i][1] * rs) for f, i in times])

    # signed bars round a zero line at y = base
    box("zero_line", (xp - 320, base - 5, -260), (xb + 320, base + 5, 30), m["rail"], root)
    for nm, x, j, mup in (("asp", xp, 3, m["profit"]), ("bits", xb, 4, m["samsung"])):
        up = column(root, f"{nm}_up", x, 260, 260, [mup], y0=base)
        dn = down_column(root, f"{nm}_dn", x, 260, 260, m["loss"], y0=base)
        heights(up, [(f, max(DN[i][j], 0) * ps) for f, i in times])
        heights(dn, [(f, max(-DN[i][j], 0) * ps) for f, i in times])

    for b, (q, d, n, a, bt) in enumerate(DN):
        iv = after(b, 0.1 if b == 0 else 0.45)
        dt = d * rs
        label(f"{q} DRAM ${d:.2f}B est", (xt + 260, dt * 0.5, 10), root, iv)
        label(f"NAND ${n:.2f}B est", (xt + 260, dt + n * rs * 0.5, 10), root, iv)
        label(f"DRAM price {a:+.1f}% QoQ".replace(".0%", "%"), (xp + 130, base + a * ps, 10), root, iv)
        label(f"DRAM bits {bt:+.1f}% QoQ".replace(".0%", "%"), (xb + 130, base + bt * ps, 10), root, iv)

    pose = ((0, 400, 0), 2050, 0.0, 0.10)
    camera(root, [pose, pose, pose])
    finish("dramnand")


# ---- hbm --------------------------------------------------------------------------------
# HBM revenue share, Counterpoint (quarterly): 2025Q2 SK hynix 64 / Samsung 15 / Micron 21,
# 2025Q4 57 / 22 / 21, 2026Q2 50 / 33 / 18. Samsung HBM bit growth QoQ 2025Q3 ~85% (call);
# HBM4 60% of HBM sales 2026Q3 (call).

HBM_SH = [(64, 15, 21), (57, 22, 21), (50, 33, 18)]


def hbm_tower(root, m, name, x, m_a, m_b):
    return column(root, name, x, 340, 300, [m_a, m_b], stripes=12, gap=10)


def build_hbm():
    m, root = scene("hbm")
    floor(root, m, -1700, 1700)
    s = 720.0 / 64.0
    xk, xs, xm = -760, 60, 880
    times = [(0, 0)]
    for b in (1, 2):
        times.append((F(b, 0.06), b - 1))
        times.append((F(b, 0.40), b))

    skh = hbm_tower(root, m, "t_skh", xk, m["skh"], m["skh2"])
    mu = hbm_tower(root, m, "t_mu", xm, m["mu"], m["mu2"])
    heights(skh, [(f, HBM_SH[i][0] * s) for f, i in times])
    heights(mu, [(f, HBM_SH[i][2] * s) for f, i in times])
    # Samsung: HBM3E-era dies below; in beat 2 the top 60% turns HBM4
    ss = hbm_tower(root, m, "t_ss", xs, m["samsung"], m["samsung2"])
    h4f0, h4f1 = F(2, 0.45), F(2, 0.65)
    ss_keys = [(f, HBM_SH[i][1] * s) for f, i in times]
    top = HBM_SH[2][1] * s
    ss_keys += [(h4f0, top), (h4f1, top * 0.4), (END, top * 0.4)]
    heights(ss, ss_keys)
    h4 = hbm_tower(root, m, "t_ss_hbm4", xs, m["hbm4"], m["samsung"])
    heights(h4, [(0, 0), (h4f0, 0), (h4f1, top * 0.6), (END, top * 0.6)])
    lift_to(h4, xs, [(h4f0, top), (h4f1, top * 0.4)])

    # the gap between SK hynix and Samsung: a red bar from Samsung's top to SK hynix's top
    gx = (xk + xs) / 2
    gap = pivot("gap", (gx, 0, 0), root)
    box("gap_bar", (-22, 0, -60), (22, REF, 0), m["loss"], gap)
    for f, i in times:
        k, ssv, _ = HBM_SH[i]
        key(gap, f, "location", P(gx, ssv * s, 0))
        key(gap, f, "scale", (1, 1, (k - ssv) * s / REF))
    names = ("2025Q2", "2025Q4", "2026Q2")
    for b, (k, ssv, mu_) in enumerate(HBM_SH):
        iv = after(b, 0.1 if b == 0 else 0.42)
        label(f"{names[b]} Samsung {ssv}%", (xs + 170, ssv * s, 10), root, iv)
        label(f"SK hynix {k}%", (xk - 170, k * s, 10), root, iv)
        label(f"gap {k - ssv} pts", (gx + 22, (ssv + (k - ssv) / 2) * s, 10), root, iv)
        if b == 0:
            label(f"Micron {mu_}%", (xm + 170, mu_ * s, 10), root, iv)
        if b == 1:
            label("HBM bits +85% QoQ (3Q25)", (xs + 170, ssv * s * 0.5, 10), root, iv)
    label("HBM4 = 60% of HBM sales 3Q26", (xs + 170, top * 0.75, 10), root, [(h4f1, F(3, 0))])

    pose = ((40, 370, 0), 2000, 0.0, 0.10)
    camera(root, [pose, pose, pose])
    finish("hbm")


# ---- hbmtimeline ------------------------------------------------------------------------
# HBM3E 12H announced 2024-02-27 (36 GB, 1,280 GB/s; Samsung release). Nvidia qualification only
# in Sep 2025, ~18 months (Korean Economic Daily via TrendForce, est). Meanwhile AMD MI350 used it
# (288 GB per GPU, est) and Samsung supplied 60%+ of Google TPU HBM in 2025 (est). HBM4 mass
# production Feb 2026, 11.7 Gbps pins, 4 nm foundry base die (company); Samsung mid-20% share of
# Nvidia HBM4 (Hankyung, est).

T0 = -1450.0  # x of 2024-01


def mx(year, month):
    return T0 + ((year - 2024) * 12 + (month - 1)) * 92.0


def build_hbmtimeline():
    m, root = scene("hbmtimeline")
    floor(root, m, -1700, 1700)
    box("rail", (mx(2024, 1) - 80, 0, 60), (mx(2026, 8), 22, 140), m["rail"], root)
    for y in (2024, 2025, 2026):
        for q in range(4):
            mo = 1 + 3 * q
            if y == 2026 and mo > 7:
                continue
            hgt = 70 if q == 0 else 34
            box(f"tick{y}{q}", (mx(y, mo) - 6, 22, 80), (mx(y, mo) + 6, 22 + hgt, 120), m["rail"], root)

    sc = 0.46
    x3, x4 = mx(2024, 2), mx(2026, 2)
    xq = mx(2025, 9)
    # HBM3E 12H: dies drop in during beat 0, the stack waits, then rolls to Sep 2025 in beat 2
    mv3 = empty("hbm3e", root)
    mv3.scale = (sc, sc, sc)
    st3 = H.stack(mv3, m, 0, 12, "s3", tsv=True)
    for k, d in enumerate(st3.dies):
        f0 = F(0, 0.05 + 0.03 * k)
        key(d, 0, "location", P(0, 900, 0))
        key(d, f0, "location", P(0, 900, 0))
        key(d, f0 + 12, "location", P(0, 0, 0))
    key(mv3, 0, "location", P(x3, 30, 0))
    key(mv3, F(2, 0.05), "location", P(x3, 30, 0))
    key(mv3, F(2, 0.32), "location", P(xq - 120, 30, 0))
    # the gate in front of it: down in beats 0-1, lifts at the start of beat 2
    gate = empty("gate", root)
    box("gate_bar", (x3 + 120, 40, -260), (x3 + 150, 470, 40), m["loss"], gate)
    key(gate, 0, "location", P(0, 0, 0))
    key(gate, F(2, 0.0), "location", P(0, 0, 0))
    key(gate, F(2, 0.06), "location", P(0, 700, 0))
    gs = empty("gate_s", root)
    show(gs, [(0, F(2, 0.07))])
    gate.parent = gs
    # 18 months of waiting along the rail
    wait = pivot("wait", (x3, 34, 100), root)
    box("wait_bar", (0, -12, -40), (REF, 12, 40), m["loss"], wait)
    key(wait, 0, "scale", (OFF, OFF, OFF))
    key(wait, F(1, 0.05), "scale", (OFF, OFF, OFF))
    key(wait, F(1, 0.06), "scale", (OFF, 1, 1))
    key(wait, F(1, 0.70), "scale", ((xq - x3) / REF, 1, 1))
    from sand_overview import _constant_until

    _constant_until(wait, F(1, 0.06))
    # Nvidia's GPU, which both stacks end up beside
    xg = (xq + x4) / 2
    gpu = empty("gpu", root)
    box("gpu_die", (xg - 120, 30, -230), (xg + 120, 250, 0), m["gpu"], gpu)
    show(gpu, [(F(2, 0.0), END)])
    # HBM4: rises at Feb 2026, with its 4 nm logic base die lit
    mv4 = empty("hbm4", root)
    st4 = H.stack(mv4, m, 0, 12, "s4", tsv=True)
    mv4.location = P(x4 + 40, 30, 0)
    key(mv4, 0, "scale", (OFF, OFF, OFF))
    key(mv4, F(2, 0.38), "scale", (OFF, OFF, OFF))
    key(mv4, F(2, 0.39), "scale", (sc, OFF, sc))
    key(mv4, F(2, 0.55), "scale", (sc, sc, sc))
    _constant_until(mv4, F(2, 0.39))
    glow = empty("hbm4_glow", root)
    box("hbm4_base_glow", (x4 + 40 - 92, 30, -90), (x4 + 40 + 92, 30 + 35, 4), m["hbm4"], glow)
    show(glow, [(F(2, 0.55), END)])

    label("Feb 2024: HBM3E 12H, 36 GB", (x3, 450, 10), root, after(0, 0.3))
    label("1,280 GB/s per stack", (x3 + 80, 220, 10), root, after(0, 0.45))
    label("Nvidia gate: closed", (x3 + 150, 470, 40), root, after(0, 0.55))
    label("Nvidia qual wait ~18 mo est", ((x3 + xq) / 2, 46, 100), root, after(1, 0.55))
    label("AMD MI350: 288 GB HBM3E est", (mx(2025, 6), 46, 100), root, after(1, 0.3, 0.55))
    label("Google TPU 2025: 60%+ est", (mx(2025, 1), 46, 100), root, after(1, 0.75))
    label("Sep 2025: Nvidia passes 12H", (xq - 120, 440, 10), root, after(2, 0.32))
    label("Feb 2026: HBM4 in volume", (x4 + 40, 440, 10), root, after(2, 0.55))
    label("11.7 Gbps, 4nm base die", (x4 + 132, 50, 10), root, after(2, 0.6))
    label("Nvidia HBM4 share ~25% est", (xg, 250, 0), root, after(2, 0.7))

    camera(root, [((-1000, 300, 0), 1350, 0.0, 0.12),
                  ((-150, 300, 0), 2000, 0.0, 0.12),
                  ((0, 300, 0), 2000, 0.0, 0.12)])
    finish("hbmtimeline")


# ---- share ------------------------------------------------------------------------------
# DRAM revenue share, TrendForce: 2024Q1 Samsung 43.9 / SK hynix 31.1 / Micron 21.5; 2025Q2
# SK hynix 38.7 / Samsung 32.7 / Micron 22.0; 2026Q2 Samsung 39.4 / SK hynix 24.9 / Micron 23.3,
# CXMT 9.5 (Herald Business, TrendForce data).

SHARE = {  # company: [(share, rank) per beat]; rank 0 = hidden
    "Samsung": [(43.9, 1), (32.7, 2), (39.4, 1)],
    "SK hynix": [(31.1, 2), (38.7, 1), (24.9, 2)],
    "Micron": [(21.5, 3), (22.0, 3), (23.3, 3)],
    "CXMT": [(0, 0), (0, 0), (9.5, 4)],
}
SLOT_X = {1: 0.0, 2: -700.0, 3: 700.0, 4: 1300.0}
SLOT_Y = {1: 90.0, 2: 55.0, 3: 30.0, 4: 0.0}


def build_share():
    m, root = scene("share")
    floor(root, m, -1700, 1700)
    s = 15.0
    for r, x in SLOT_X.items():
        if r < 4:
            box(f"podium{r}", (x - 250, 0, -330), (x + 250, SLOT_Y[r], 40), m["plinth"], root)
    mats_ = {"Samsung": (m["samsung"], m["samsung2"]), "SK hynix": (m["skh"], m["skh2"]),
             "Micron": (m["mu"], m["mu2"]), "CXMT": (m["cxmt"], m["cxmt"])}
    times = [(0, 0)]
    for b in (1, 2):
        times.append((F(b, 0.06), b - 1))
        times.append((F(b, 0.45), b))
    qs = ("2024Q1", "2025Q2", "2026Q2")
    for name, st in SHARE.items():
        ma, mb = mats_[name]
        col = column(root, f"c_{name}", 0, 300, 260, [ma, mb], stripes=8, gap=5)
        hk, lk = [], []
        for f, i in times:
            v, r = st[i]
            hk.append((f, v * s))
            # hidden towers wait in their first visible slot
            rr = r or next(rk for _, rk in st if rk)
            lk.append((f, rr))
        heights(col, hk)
        for f, rr in lk:
            key(col, f, "location", P(SLOT_X[rr], SLOT_Y[rr], -20))
        for b in range(3):
            v, r = st[b]
            if not r:
                continue
            txt = f"{name} {v:.1f}%"
            if r == 1 and name != "Samsung":
                txt += " (No.1)"
            if name == "Samsung":
                txt = f"{qs[b]} {txt}"
            label(txt, (SLOT_X[r] + 150, SLOT_Y[r] + v * s, 0), root, after(b, 0.1 if b == 0 else 0.48))

    pose = ((250, 360, 0), 2000, 0.0, 0.10)
    camera(root, [pose, pose, pose])
    finish("share")


# ---- capacity ---------------------------------------------------------------------------
# DS capex (Newsroom / Korea Times): 2023 48.4T, 2024 46.3T, 2025 47.5T, 2026 guidance 76.8T
# (Jan-Sep actual 52.8T). 1c DRAM capacity (ETNews / Hankyung via TrendForce, est): 60k wpm end
# 2025, 70k Feb 2026, 200k target end 2026; 1c yield 80% (ETNews, est). Fabs: P4 190k wpm by
# 2027Q1 (Hankyung, est); P5 from 2028, KRW 60T+ per fab (est); Yongin six fabs KRW 360T (est);
# Taylor TX $37B plan (US government release; logic fabs).

CAPEX = [("2023", 48.4), ("2024", 46.3), ("2025", 47.5)]
XA, XC = -3200.0, 3200.0  # beat 0 and beat 2 sit left and right of the wafer stacks


def fab(root, m, name, x, z, w, d, h, f0, f1, wall="fab"):
    pv = pivot(name, (x, 0, z), root)
    box(f"{name}_body", (-w / 2, 0, -d / 2), (w / 2, h, d / 2), m[wall], pv)
    box(f"{name}_roof", (-w / 2 - 12, h, -d / 2 - 12), (w / 2 + 12, h + 24, d / 2 + 12), m["fab_roof"], pv)
    for k in range(3):
        y = h * (0.25 + 0.25 * k)
        box(f"{name}_band{k}", (-w / 2 - 3, y - 10, d / 2 - 2), (w / 2 + 3, y + 10, d / 2 + 4), m["fab_roof"], pv)
    from sand_overview import _constant_until

    key(pv, 0, "scale", (OFF, OFF, OFF))
    key(pv, f0, "scale", (OFF, OFF, OFF))
    key(pv, f0 + 1, "scale", (1, 1, OFF))
    key(pv, f1, "scale", (1, 1, 1))
    _constant_until(pv, f0 + 1)
    return pv


def build_capacity():
    m, root = scene("capacity")
    floor(root, m, XA - 900, XC + 1700, -900, 300)

    # beat 0: capex staircase, 2026 a guidance ghost with the Jan-Sep actual inside
    s = 640.0 / 76.8
    xs = [XA - 690 + 460 * i for i in range(4)]
    for i, (yr, v) in enumerate(CAPEX):
        c = column(root, f"capex{yr}", xs[i], 300, 300, [m["mem"], m["mem2"]], stripes=5, gap=4)
        f0 = F(0, 0.05 + 0.12 * i)
        heights(c, [(0, 0), (f0, 0), (f0 + 24, v * s)])
    ytd = column(root, "capex2026", xs[3], 300, 300, [m["profit"]])
    gd = column(root, "capex2026g", xs[3], 330, 330, [m["guide"]], z1=15)
    f0 = F(0, 0.42)
    heights(ytd, [(0, 0), (f0, 0), (f0 + 30, 52.8 * s)])
    heights(gd, [(0, 0), (f0 + 30, 0), (f0 + 60, 76.8 * s)])
    label("2023 DS capex KRW 48.4T", (xs[0] + 150, 48.4 * s, 10), root, after(0, 0.2))
    label("2025 KRW 47.5T", (xs[2] + 150, 47.5 * s, 10), root, after(0, 0.4))
    label("Jan-Sep 2026 KRW 52.8T", (xs[3] + 150, 52.8 * s * 0.6, 15), root, after(0, 0.55))
    label("2026 guided KRW 76.8T", (xs[3] + 150, 76.8 * s, 15), root, after(0, 0.68))

    # beat 1: 1c DRAM wafers, one disc per 10k wafers a month
    piles = [(-760, 6, "1c DRAM 60k wpm end-2025 est"), (0, 7, "70k wpm Feb 2026 est"),
             (760, 20, "200k wpm end-2026 target est")]
    for pi, (x, n, txt) in enumerate(piles):
        box(f"pad{pi}", (x - 200, 0, -360), (x + 200, 20, 40), m["plinth"], root)
        for k in range(n):
            e = empty(f"w{pi}_{k}", root)
            disc(f"w{pi}_{k}_d", (x, 20 + 14 + 32 * k, -160), 150, 22, m["wafer_1c"], e, verts=48)
            f0 = F(1, 0.05 + 0.25 * pi + 0.25 * k / max(n, 1))
            key(e, 0, "location", P(0, 500, 0))
            key(e, f0, "location", P(0, 500, 0))
            key(e, f0 + 10, "location", P(0, 0, 0))
            show(e, [(f0, END)])
        label(txt, (x + 150, 20 + 32 * n, 0), root, [(F(1, 0.1 + 0.25 * pi + 0.25), F(2, 0))])
    label("1c yield 80% est (Aug 2026)", (760 - 150, 20 + 32 * 10, 0), root, after(1, 0.85))

    # beat 2: the fabs, in date order
    box("plinth_kr", (XC - 1450, 0, -700), (XC + 650, 18, 200), m["plinth"], root)
    box("plinth_us", (XC + 850, 0, -700), (XC + 1450, 18, 200), m["plinth"], root)
    fab(root, m, "p4", XC - 1180, -250, 380, 420, 330, F(2, 0.04), F(2, 0.16))
    fab(root, m, "p5", XC - 640, -250, 380, 420, 330, F(2, 0.16), F(2, 0.28))
    for k in range(6):
        fx = XC - 110 + 260 * (k % 3)
        fz = -120 - 300 * (k // 3)
        fab(root, m, f"yongin{k}", fx, fz, 220, 240, 280, F(2, 0.28 + 0.03 * k), F(2, 0.36 + 0.03 * k))
    fab(root, m, "taylor", XC + 1150, -250, 380, 420, 300, F(2, 0.52), F(2, 0.64), wall="fab_us")
    label("P4: 190k wpm by 2027Q1 est", (XC - 1180, 360, -40), root, after(2, 0.2))
    label("P5: 2028, KRW 60T+/fab est", (XC - 640, 360, -40), root, after(2, 0.32))
    label("Yongin: 6 fabs, KRW 360T est", (XC + 150, 310, 0), root, after(2, 0.5))
    label("Taylor TX: $37B, logic fabs", (XC + 1150, 330, -40), root, after(2, 0.68))

    camera(root, [((XA, 360, 0), 1850, 0.0, 0.10),
                  ((0, 330, 0), 1800, 0.0, 0.12),
                  ((XC, 260, 0), 2000, 0.0, 0.16)])
    finish("capacity")


# ---- tech -------------------------------------------------------------------------------
# V-NAND layer counts (Samsung via KED Global / HPCwire): V8 236 (2023), V9 286 (2024; QLC V9
# +86% bit density), V10 BV-NAND 400+ (Aug 2026; +58% density vs V9, bonding vertical).

NAND_GENS = [("V8", 236, -950.0), ("V9", 286, -50.0), ("V10", 400, 900.0)]


def nand_column(root, m, name, x, layers, y0):
    pv = pivot(name, (x, y0, 0), root)
    n = layers // 10  # one band per 10 layers
    step = REF / n
    for k in range(n):
        box(f"{name}_l{k}", (-230, k * step, -300), (230, k * step + step * 0.55, 0), m["wl_a"], pv)
        box(f"{name}_o{k}", (-230, k * step + step * 0.55, -300), (230, (k + 1) * step, 0), m["wl_b"], pv)
    for j, cx in enumerate((-150, -50, 50, 150)):
        tube(f"{name}_ch{j}", (cx, 0, 0), (cx, REF, 0), 16, m["channel"], pv, verts=12)
    return pv


def build_tech():
    m, root = scene("tech")
    floor(root, m, -1700, 1700)
    s = 2.0  # mm per layer
    cols = []
    for b, (gen, layers, x) in enumerate(NAND_GENS):
        y0 = 90.0 if gen == "V10" else 20.0
        box(f"sub_{gen}", (x - 260, 0, -320), (x + 260, 20, 20), m["plinth"], root)
        c = nand_column(root, m, f"col_{gen}", x, layers, y0)
        f0 = F(b, 0.06)
        heights(c, [(0, 0), (f0, 0), (F(b, 0.5), layers * s)])
        cols.append(c)
    # V10: the periphery logic is made on its own wafer and bonded under the cell stack
    xv = NAND_GENS[2][2]
    per = empty("peri", root)
    box("peri_wafer", (xv - 240, 20, -310), (xv + 240, 86, -10), m["peri"], per)
    for k in range(5):
        box(f"peri_bump{k}", (xv - 180 + 90 * k, 86, -170), (xv - 150 + 90 * k, 90, -140), m["bump"], per)
    key(per, 0, "location", P(700, 260, 0))
    key(per, F(2, 0.5), "location", P(700, 260, 0))
    key(per, F(2, 0.68), "location", P(0, 260, 0))
    key(per, F(2, 0.8), "location", P(0, 0, 0))
    show(per, [(F(2, 0.5), END)])

    label("V8: 236 layers (2023)", (NAND_GENS[0][2] + 230, 20 + 236 * s, 0), root, [(F(0, 0.5), F(2, 0.55))])
    label("word-line layers", (NAND_GENS[0][2] - 230, 20 + 236 * s * 0.4, 0), root, after(0, 0.55))
    label("channel holes", (NAND_GENS[0][2] - 150, 20 + 236 * s * 0.7, 0), root, after(0, 0.6))
    label("V9: 286 layers (2024)", (NAND_GENS[1][2] + 230, 20 + 286 * s, 0), root, [(F(1, 0.5), F(3, 0))])
    label("QLC V9: +86% bit density", (NAND_GENS[1][2] + 230, 20 + 286 * s * 0.5, 0), root, after(1, 0.55))
    label("V10 BV: 400+ layers (2026)", (xv + 230, 90 + 400 * s, 0), root, after(2, 0.5))
    label("+58% density vs V9", (xv + 230, 90 + 400 * s * 0.55, 0), root, after(2, 0.6))
    label("periphery wafer bonded under", (xv + 240, 55, -10), root, after(2, 0.82))

    camera(root, [((-500, 320, 0), 1500, 0.0, 0.10),
                  ((-300, 360, 0), 1750, 0.0, 0.10),
                  ((80, 430, 0), 2050, 0.0, 0.10)])
    finish("tech")


# ---- sources ----------------------------------------------------------------------------
# Counts for Samsung in memory_facts (the page's Sources tab: 325 numbers, 129 pages, 57 conflicts):
# company stated 172, third-party estimates 71, research-firm shares 49, guidance 30 + forecasts 3;
# OpenDART values 111. Disagreements: DRAM share 2026Q2 TrendForce 39.4% vs Counterpoint 38%;
# DS operating income 2025Q3 reported KRW 7.0T vs pre-results estimate KRW 6.1T.

PILES = [("company stated: 172", 172, "paper"), ("estimates: 71", 71, "paper"),
         ("research-firm shares: 49", 49, "paper"), ("guidance + forecast: 33", 33, "paper")]


def pile(root, m, name, x, mm, mline):
    return column(root, name, x, 300, 220, [mm, mline], stripes=20, gap=0)


def build_sources():
    m, root = scene("sources")
    floor(root, m, -1800, 4700)
    s = 3.6  # mm per sourced number
    xs = [-1300, -700, -100, 500]
    for i, (txt, n, _) in enumerate(PILES):
        p = pile(root, m, f"pile{i}", xs[i], m["paper"], m["paper2"])
        f0 = F(0, 0.05 + 0.1 * i)
        heights(p, [(0, 0), (f0, 0), (f0 + 40, n * s)])
        label(txt, (xs[i] + 150, n * s, 0), root, after(0, 0.4 + 0.08 * i))
    dart = pile(root, m, "dart", 1150, m["dart"], m["peri"])
    heights(dart, [(0, 0), (F(1, 0.05), 0), (F(1, 0.35), 111 * s)])
    label("OpenDART filings: 111 values", (1300, 111 * s, 0), root, after(1, 0.3))
    # 57 conflicting values pulled out to a red pile (one sheet flies per 5)
    xr = 1650
    red = column(root, "conflicts", xr, 300, 220, [m["loss"], m["skh2"]], stripes=10)
    heights(red, [(0, 0), (F(1, 0.4), 0), (F(1, 0.85), 57 * s)])
    for k in range(11):
        src = xs[k % 4]
        e = empty(f"fly{k}", root)
        box(f"fly{k}_b", (src - 130, 0, -200), (src + 130, 10, -20), m["loss"], e)
        f0 = F(1, 0.4 + 0.04 * k)
        key(e, f0, "location", P(0, PILES[k % 4][1] * s, 0), linear=True)
        key(e, f0 + 10, "location", P((xr - src) * 0.5, 600, 0), linear=True)
        key(e, f0 + 20, "location", P(xr - src, 57 * s * k / 11, 0), linear=True)
        show(e, [(f0, f0 + 20)])
    label("57 values conflict", (xr + 150, 57 * s, 0), root, after(1, 0.8))
    label("129 distinct source pages", (xs[0] + 150, 172 * s, 0), root, after(1, 0.3))

    # beat 2: two disagreements as side-by-side bars
    X2 = 3100.0
    ps = 15.0
    a1 = column(root, "tf", X2 - 640, 220, 220, [m["samsung"]])
    a2 = column(root, "cp", X2 - 380, 220, 220, [m["samsung2"]])
    b1 = column(root, "rep", X2 + 380, 220, 220, [m["profit"]])
    b2 = column(root, "est", X2 + 640, 220, 220, [m["rest"]])
    for c, v, k in ((a1, 39.4 * ps, 0), (a2, 38.0 * ps, 1), (b1, 7.0 * 80, 2), (b2, 6.1 * 80, 3)):
        f0 = F(2, 0.08 + 0.08 * k)
        heights(c, [(0, 0), (f0, 0), (f0 + 30, v)])
    label("DRAM 2Q26: TrendForce 39.4%", (X2 - 640, 39.4 * ps, 0), root, after(2, 0.3))
    label("Counterpoint 38.0%", (X2 - 380 + 110, 38.0 * ps * 0.8, 0), root, after(2, 0.35))
    label("DS OI 3Q25 reported KRW 7.0T", (X2 + 380, 7.0 * 80, 0), root, after(2, 0.45))
    label("pre-results est KRW 6.1T", (X2 + 640 + 110, 6.1 * 80 * 0.8, 0), root, after(2, 0.5))

    camera(root, [((-400, 330, 0), 1950, 0.0, 0.10),
                  ((260, 340, 0), 2250, 0.0, 0.10),
                  ((X2, 320, 0), 1750, 0.0, 0.10)])
    finish("sources")


BUILDERS = {
    "snapshot": build_snapshot,
    "group": build_group,
    "memory": build_memory,
    "dramnand": build_dramnand,
    "hbm": build_hbm,
    "hbmtimeline": build_hbmtimeline,
    "share": build_share,
    "capacity": build_capacity,
    "tech": build_tech,
    "sources": build_sources,
}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for tab in argv or list(BUILDERS):
        BUILDERS[tab]()
