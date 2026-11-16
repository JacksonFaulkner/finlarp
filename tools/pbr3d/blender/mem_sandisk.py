"""SanDisk (SNDK) memory page: one purpose-built 3D scene per tab, exported for pbr3d.

Run from the repo root (all tabs, or one):

    blender -b --factory-startup --python tools/pbr3d/blender/mem_sandisk.py [-- <tab id>]

Each tab writes tools/pbr3d/assets/mem/sandisk_<tab>.glb, which py/derive/memory_page.py's
custom_scene() picks up. Every scene is 3 beats of 8 s (frames 0..576), framed wide (about 3:1).

Every number drawn (bar heights, stack counts, tags) comes from data/memory_facts/sndk.jsonl or
mkt-share.jsonl / mkt-price.jsonl; derived values say "derived" or "est" in their tags.

  snapshot  the business in one chain: JV wafers split 60/40, BiCS die and SSD, 2026Q3 revenue by market
  revenue   a stack of $250M wafers per quarter out of the 2025Q1 trough, with guidance rings beaten
  markets   datacenter bars climb from smallest to near the top: $197M (2025Q1) to $4.80B (2026Q3)
  margins   quarterly revenue = flat grey cost + gold gross profit: 22.5% margin to 85.0%
  pricing   revenue as an area, bits sold (width) x revenue per GB (height), FY2024 -> FY2026
  share     NAND share towers; SanDisk + Kioxia (same JV fabs) merge into one 25.0% tower
  kioxia    Yokkaichi and Kitakami fabs; wafers split 3 to Kioxia, 2 to SanDisk; Fab3 and the JPY 5T plan
  tech      BiCS8 218 layers next to BiCS10 332 layers; the CMOS wafer bonded under the array
  hbf       HBM4 stacks beside a GPU; two swapped for 16-die NAND HBF stacks; capacity 64 GB -> 1.5 TB
  sources   paper stacks by publisher, re-sorted by basis, then sources that disagree as paired bars
"""

import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sand_overview as O  # noqa: E402
from sand_overview import OFF, F, P, _constant_until, box, disc, empty, fly, key, label, mat, pivot, show, tube  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402
import hbm_kit as H  # noqa: E402

SLUG = "sandisk"
PBR_DIR = os.path.normpath(os.path.join(HERE, ".."))
OUT_DIR = os.path.join(PBR_DIR, "assets", "mem")
BLEND_DIR = os.environ.get("SNDK_BLEND_DIR", "")  # .blend files only when asked (scratch dir)
END = F(3, 0)


def B(i):
    return [(F(i, 0), F(i + 1, 0))]


def iv(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


# ---- materials --------------------------------------------------------------------------


def mats(m):
    s = "sndk_"
    m["floor"] = mat(s + "floor", (0.05, 0.055, 0.07), rough=0.95)
    m["dc"] = mat(s + "datacenter", (0.15, 0.80, 1.0), rough=0.35, emit=(0.1, 0.7, 1.0), strength=0.6)
    m["edge"] = mat(s + "edge", (0.45, 0.45, 1.0), rough=0.4)
    m["cons"] = mat(s + "consumer", (1.0, 0.58, 0.18), rough=0.45)
    m["gold"] = mat(s + "gold", (0.95, 0.72, 0.30), metal=0.4, rough=0.35, emit=(1.0, 0.7, 0.25), strength=0.5)
    m["gold_glow"] = mat(s + "gold_glow", (1.0, 0.78, 0.35), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["cost"] = mat(s + "cost", (0.20, 0.22, 0.27), metal=0.5, rough=0.5)
    m["red"] = mat(s + "red", (0.90, 0.16, 0.18), rough=0.4)
    m["red_glow"] = mat(s + "red_glow", (1.0, 0.25, 0.2), emit=(1.0, 0.2, 0.15), strength=2.0)
    m["wafer"] = mat(s + "wafer", (0.70, 0.73, 0.80), metal=0.75, rough=0.22)
    m["wafer_red"] = mat(s + "wafer_red", (0.85, 0.30, 0.30), metal=0.5, rough=0.25)
    m["ghost"] = mat(s + "ghost", (1.0, 0.85, 0.5), rough=0.3, alpha=0.18)
    m["ghost_grey"] = mat(s + "ghost_grey", (0.7, 0.75, 0.85), rough=0.3, alpha=0.15)
    m["ring"] = mat(s + "guide_ring", (1.0, 0.85, 0.4), emit=(1.0, 0.8, 0.3), strength=2.5)
    m["kioxia"] = mat(s + "kioxia", (0.82, 0.85, 0.92), rough=0.45)
    m["samsung"] = mat(s + "samsung", (0.22, 0.42, 0.95), rough=0.4)
    m["sk"] = mat(s + "skhynix", (0.95, 0.45, 0.18), rough=0.4)
    m["micron"] = mat(s + "micron", (0.35, 0.72, 0.42), rough=0.4)
    m["nand"] = mat(s + "nand_die", (0.20, 0.72, 0.52), rough=0.4)
    m["nand2"] = mat(s + "nand_die_hi", (0.30, 0.95, 0.65), rough=0.35, emit=(0.2, 0.9, 0.55), strength=0.6)
    m["wl"] = mat(s + "wordline", (0.20, 0.22, 0.27), metal=0.7, rough=0.35)
    m["ox"] = mat(s + "oxide", (0.78, 0.80, 0.86), rough=0.5)
    m["chan"] = mat(s + "channel", (0.3, 0.9, 1.0), emit=(0.25, 0.85, 1.0), strength=1.6)
    m["cmos"] = mat(s + "cmos", (0.30, 0.55, 0.35), metal=0.3, rough=0.4)
    m["pad"] = mat(s + "bond_pad", (0.95, 0.6, 0.3), emit=(1.0, 0.55, 0.2), strength=2.0)
    m["fab"] = mat(s + "fab", (0.80, 0.82, 0.86), rough=0.6)
    m["fab_roof"] = mat(s + "fab_roof", (0.45, 0.48, 0.55), metal=0.3, rough=0.5)
    m["fab3"] = mat(s + "fab3", (0.95, 0.85, 0.55), rough=0.5)
    m["belt"] = mat(s + "belt", (0.08, 0.08, 0.10), rough=0.9)
    m["ssd"] = mat(s + "ssd", (0.12, 0.13, 0.16), metal=0.6, rough=0.3)
    m["ssd_label"] = mat(s + "ssd_label", (0.90, 0.16, 0.18), rough=0.4)
    m["paper"] = mat(s + "paper", (0.93, 0.92, 0.88), rough=0.85)
    m["paper2"] = mat(s + "paper2", (0.86, 0.83, 0.74), rough=0.85)
    m["paper_sec"] = mat(s + "paper_sec", (0.80, 0.88, 1.0), rough=0.8)
    m["green"] = mat(s + "stated_green", (0.30, 0.80, 0.45), rough=0.5)
    m["amber"] = mat(s + "guide_amber", (1.0, 0.70, 0.20), rough=0.5)
    m["blue"] = mat(s + "share_blue", (0.35, 0.55, 1.0), rough=0.5)
    m["est_red"] = mat(s + "est_red", (0.95, 0.30, 0.30), rough=0.5)
    m["srcA"] = mat(s + "src_a", (0.35, 0.65, 1.0), rough=0.4)
    m["srcB"] = mat(s + "src_b", (1.0, 0.55, 0.25), rough=0.4)
    m["axis"] = mat(s + "axis", (0.85, 0.87, 0.92), emit=(0.8, 0.85, 0.95), strength=0.8)
    m["line"] = mat(s + "line", (1.0, 1.0, 1.0), emit=(1.0, 1.0, 1.0), strength=2.0)
    return m


def begin(tab):
    m, root = start(tab, beats=3, page=SLUG)
    mats(m)
    return m, root


def fin(tab):
    os.makedirs(OUT_DIR, exist_ok=True)
    if BLEND_DIR:
        os.makedirs(BLEND_DIR, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLEND_DIR, f"{SLUG}_{tab}.blend"))
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


# ---- helpers ------------------------------------------------------------------------------


def floor(root, m, x0, x1, z0=-700.0, z1=300.0):
    box("floor", (x0, -24, z0), (x1, 0, z1), m["floor"], root)


def bar(parent, name, x, y0, w, d, h, mt, keys, z1=0.0):
    """A box of full height h standing at (x, y0), centred on x, front face at z1, inside a pivot
    at its base; `keys` are (frame, fraction of h). Hidden before the first key."""
    pv = pivot(name, (x, y0, 0), parent)
    box(name + "_m", (-w / 2, 0, z1 - d), (w / 2, h, z1), mt, pv)
    first = keys[0][0]
    ks = [(0, (OFF, OFF, OFF))] if first > 0 else []
    ks += [(f, (1, 1, max(v, OFF))) for f, v in keys]
    scale_keys(pv, ks, until=first if first > 0 else None)
    return pv


def grow(parent, name, x, y0, w, d, h, mt, f0, f1, z1=0.0, until=None):
    """A bar that grows from nothing to h over [f0, f1] and stays."""
    return bar(parent, name, x, y0, w, d, h, mt, [(f0, 0.0), (f1, 1.0)], z1)


def gshow(parent, name, intervals):
    g = empty(name, parent)
    show(g, intervals)
    return g


def join(objs, name, parent):
    """Joins meshes into one object (fewer nodes in the GLB)."""
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.parent = parent
    return o


def wafer(parent, name, c, r, mt, t=12.0):
    return disc(name, c, r, t, mt, parent, verts=40)


# ---- snapshot ------------------------------------------------------------------------------

# 2026Q3 end-market revenue, $M (Sandisk FQ1 FY27 release)
Q3_26 = {"dc": 4802, "edge": 5832, "cons": 397}


def build_snapshot():
    m, root = begin("snapshot")
    floor(root, m, -2700, 3300, -600, 250)

    # beat 0: five JV wafers standing on edge, three Kioxia, two SanDisk (60/40 of capacity)
    r = 200.0
    xs = [-2250, -1800, -1350, -900, -450]
    owner = ["k", "s", "k", "s", "k"]
    for i, (x, o) in enumerate(zip(xs, owner)):
        g = empty(f"w{i}", root)
        d = wafer(g, f"w{i}_d", (x, r + 6, -40 if o == "s" else -260), r, m["wafer_red"] if o == "s" else m["wafer"], t=16)
        d.rotation_euler = (math.pi / 2, 0, 0)
        f0 = F(0, 0.05 + 0.1 * i)
        if o == "k":
            show(g, [(f0, END)])
        else:
            # the SanDisk wafers roll right to the die in beat 1 and are used up
            show(g, [(f0, F(1, 0.42))])
            fly(g, [(0, 0, 0), (0, 120, 0), (300 - x - 120 * (i == 1), 120, 0)], F(1, 0.02), F(1, 0.4))
    label("JV wafers: Kioxia 60%", (-1400, 2 * r, -150), root, iv(0, 0.4, 1, 0))
    label("SanDisk 40%", (-1000, 2 * r, -150), root, iv(0, 0.5, 1, 0))
    label("from Yokkaichi + Kitakami", (-2200, 6, -150), root, iv(0, 0.6, 1, 0))

    # beat 1: a BiCS8 die (stacked layers with memory strings) and the SSD it goes into
    dx = 300.0
    die = pivot("die", (dx, 0, 0), root)
    plates = []
    for k in range(12):
        y = 10 + 30 * k
        plates.append(box(f"die_p{k}", (-270, y, -380), (270, y + 20, 0), m["wl"] if k % 2 else m["ox"], None))
    join(plates, "die_layers", die)
    for i in range(5):
        tube(f"die_ch{i}", (-200 + 100 * i, 10, 0), (-200 + 100 * i, 370, 0), 14, m["chan"], die, verts=10)
    scale_keys(die, [(0, (OFF, OFF, OFF)), (F(1, 0.35), (1, 1, OFF)), (F(1, 0.6), (1, 1, 1))], until=F(1, 0.35))
    label("BiCS8 die: 218 layers", (0, 370, -190), die, iv(1, 0.55, 2, 0.3))

    ssd = empty("ssd", root)
    box("ssd_body", (750, 0, -360), (1450, 110, -40), m["ssd"], ssd)
    box("ssd_tag", (880, 110, -320), (1300, 118, -80), m["ssd_label"], ssd)
    box("ssd_conn", (1450, 20, -320), (1500, 80, -80), m["gold"], ssd)
    show(ssd, [(F(1, 0.62), END)])
    label("SSD: up to 256 TB", (1100, 118, -200), root, iv(1, 0.66, 2, 0.3))

    # beat 2: 2026Q3 revenue by end market, $M -> height
    k = 0.15
    bxs = (2050, 2450, 2850)
    for j, mk in enumerate(("dc", "edge", "cons")):
        grow(root, f"mkt_{mk}", bxs[j], 0, 320, 320, Q3_26[mk] * k, m[mk], F(2, 0.1 + 0.12 * j), F(2, 0.42 + 0.12 * j))
    for i in range(6):
        g = empty(f"ssd_fly{i}", root)
        box(f"ssd_fly{i}_b", (1020, 120, -260), (1180, 160, -140), m["ssd"], g)
        f0 = F(2, 0.02 + 0.07 * i)
        tx = bxs[i % 3] - 1100
        fly(g, [(0, 0, 0), (tx * 0.5, 300, 0), (tx, 140, 0)], f0, f0 + 40)
        show(g, [(f0, f0 + 40)])
    label("2026Q3: $11.03B, 85% margin", (2450, Q3_26["edge"] * k, -160), root, iv(2, 0.6, 3, 0))
    label("Datacenter $4.80B", (bxs[0] - 160, Q3_26["dc"] * k * 0.75, 0), root, iv(2, 0.5, 3, 0))
    label("Edge $5.83B", (bxs[1] + 160, Q3_26["edge"] * k * 0.55, 0), root, iv(2, 0.62, 3, 0))
    label("Consumer $397M", (bxs[2], Q3_26["cons"] * k, -160), root, iv(2, 0.72, 3, 0))

    camera(
        root,
        [
            ((-1350.0, 250.0, -150.0), 1700.0, 0.0, 0.10),
            ((350.0, 260.0, -150.0), 2000.0, 0.0, 0.12),
            ((1750.0, 430.0, -150.0), 2400.0, 0.0, 0.10),
        ],
    )
    fin("snapshot")


# ---- revenue -------------------------------------------------------------------------------

REV = [  # quarter, revenue $M (8-K EX-99.1 / FQ1 FY27 release), guidance midpoint $M or None
    ("2024Q3", 1883, None),
    ("2024Q4", 1876, None),
    ("2025Q1", 1695, None),
    ("2025Q2", 1901, None),
    ("2025Q3", 2308, None),
    ("2025Q4", 3025, 2600),
    ("2026Q1", 5950, 4600),
    ("2026Q2", 8965, 8000),
    ("2026Q3", 11031, 10550),
]
GUIDE_Q4_26 = 12400
DISC_USD = 250.0  # one wafer disc = $250M
DISC_T, DISC_PITCH = 20.0, 25.0


def build_revenue():
    m, root = begin("revenue")
    pitch, r = 360.0, 140.0
    xs = [-1620 + pitch * i for i in range(10)]
    floor(root, m, -1900, 1900, -500, 300)
    # quarter i grows in beat i // 3, over a slice of it
    for i, (q, v, guide) in enumerate(REV):
        b, slot = divmod(i, 3)
        u0, u1 = 0.05 + 0.3 * slot, 0.3 + 0.3 * slot
        n = v / DISC_USD
        full = int(n)
        x = xs[i]
        g = empty(f"stack{i}", root)
        for k in range(full + (1 if n - full > 0.05 else 0)):
            t = DISC_T if k < full else DISC_T * (n - full)
            d = empty(f"s{i}_{k}", g)
            disc(f"s{i}_{k}_d", (x, k * DISC_PITCH + t / 2, -r), r, t, m["wafer"], d, verts=32)
            f = round(F(b, u0) + (F(b, u1) - F(b, u0)) * k / max(1, n))
            show(d, [(f, END)])
        if guide:
            gy = guide / DISC_USD * DISC_PITCH
            gr = empty(f"guide{i}", root)
            disc(f"guide{i}_ring", (x, gy, -r), r + 40, 8, m["ring"], gr, verts=32)
            show(gr, [(F(b, max(0.0, u0 - 0.04)), END)])
    # 2026Q4 guidance: a ghost stack
    gy = GUIDE_Q4_26 / DISC_USD * DISC_PITCH
    gh = empty("guide_q4", root)
    disc("guide_q4_ghost", (xs[9], gy / 2, -r), r, gy, m["ghost"], gh, verts=32)
    disc("guide_q4_ring", (xs[9], gy, -r), r + 40, 8, m["ring"], gh, verts=32)
    show(gh, [(F(2, 0.9), END)])

    top = lambda i: REV[i][1] / DISC_USD * DISC_PITCH  # noqa: E731
    label("2024Q3 $1.88B", (xs[0], top(0), -r), root, iv(0, 0.3, 1, 0))
    label("2025Q1 trough: $1.70B", (xs[2], top(2), -r), root, iv(0, 0.85, 1, 0))
    label("1 wafer = $250M of revenue", (xs[1] + r, 120, 0), root, iv(0, 0.4, 1, 0))
    label("2025Q3 $2.31B", (xs[4], top(4), -r), root, iv(1, 0.6, 2, 0))
    label("2025Q4 $3.03B vs $2.6B guide", (xs[5], top(5), -r), root, iv(1, 0.9, 2, 0))
    label("2026Q1 $5.95B vs $4.6B guide", (xs[6], top(6), -r), root, iv(2, 0.3, 3, 0))
    label("2026Q3 $11.03B, 6.5x trough", (xs[8], top(8), -r), root, iv(2, 0.85, 3, 0))
    label("2026Q4 guide $12.4B", (xs[9] + r, gy * 0.6, -r), root, iv(2, 0.92, 3, 0))

    camera(
        root,
        [
            ((-1150.0, 170.0, -150.0), 1350.0, 0.0, 0.10),
            ((-750.0, 250.0, -150.0), 1850.0, 0.0, 0.10),
            ((0.0, 620.0, -150.0), 2950.0, 0.0, 0.10),
        ],
    )
    fin("revenue")


# ---- markets -------------------------------------------------------------------------------

MKT = [  # quarter, datacenter, edge, consumer ($M, end-market tables in the 8-K releases)
    ("2024Q3", 300, 1069, 514),
    ("2024Q4", 250, 1028, 598),
    ("2025Q1", 197, 927, 571),
    ("2025Q2", 213, 1103, 585),
    ("2025Q3", 269, 1387, 652),
    ("2025Q4", 440, 1678, 907),
    ("2026Q1", 1467, 3663, 820),
    ("2026Q2", 2977, 5432, 556),
    ("2026Q3", 4802, 5832, 397),
]


def build_markets():
    m, root = begin("markets")
    k = 1000.0 / 5832.0
    pitch, w = 330.0, 92.0
    xs = [-1320 + pitch * i for i in range(9)]
    floor(root, m, -1600, 1600, -400, 300)
    sched = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)]
    per = {0: 4, 1: 3, 2: 2}
    for i, (q, dc, ed, co) in enumerate(MKT):
        b, s = sched[i]
        span = 0.8 / per[b]
        u0, u1 = 0.05 + span * s, 0.05 + span * (s + 1)
        for j, (mk, v) in enumerate((("cons", co), ("edge", ed), ("dc", dc))):
            x = xs[i] + (j - 1) * (w + 8)
            grow(root, f"b{i}_{mk}", x, 0, w, 120, v * k, m[mk], F(b, u0 + 0.03 * j), F(b, u1))

    def at(i, j, v):
        return (xs[i] + (j - 1) * (w + 8), v * k, -60)

    label("Datacenter $197M, 2025Q1", at(2, 2, 197), root, iv(0, 0.65, 1, 0))
    label("Edge $927M", at(2, 1, 927), root, iv(0, 0.7, 1, 0))
    label("Consumer $571M", at(2, 0, 571), root, iv(0, 0.75, 1, 0))
    label("2026Q1 Datacenter $1.47B", at(6, 2, 1467), root, iv(1, 0.78, 2, 0))
    label("passes Consumer $820M", at(6, 0, 820), root, iv(1, 0.8, 2, 0))
    label("Datacenter $4.80B, 18x 2025Q3", at(8, 2, 4802), root, iv(2, 0.55, 3, 0))
    label("Edge $5.83B", at(8, 1, 5832), root, iv(2, 0.6, 3, 0))
    label("Consumer $397M, shrinking", at(8, 0, 397), root, iv(2, 0.65, 3, 0))

    camera(
        root,
        [
            ((-830.0, 120.0, -60.0), 1250.0, 0.0, 0.12),
            ((-250.0, 300.0, -60.0), 2250.0, 0.0, 0.12),
            ((0.0, 480.0, -60.0), 2800.0, 0.0, 0.12),
        ],
    )
    fin("markets")


# ---- margins -------------------------------------------------------------------------------

GM = [  # quarter, revenue $M, GAAP gross margin % (8-K EX-99.1 / FQ1 FY27 release)
    ("2024Q3", 1883, 38.6),
    ("2024Q4", 1876, 32.3),
    ("2025Q1", 1695, 22.5),
    ("2025Q2", 1901, 26.2),
    ("2025Q3", 2308, 29.8),
    ("2025Q4", 3025, 50.9),
    ("2026Q1", 5950, 78.4),
    ("2026Q2", 8965, 84.6),
    ("2026Q3", 11031, 85.0),
]


def build_margins():
    m, root = begin("margins")
    k = 0.1  # mm per $M
    pitch, w = 330.0, 210.0
    xs = [-1320 + pitch * i for i in range(9)]
    floor(root, m, -1600, 1600, -400, 300)
    sched = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)]
    per = {0: 4, 1: 3, 2: 2}
    for i, (q, rev, gm) in enumerate(GM):
        b, s = sched[i]
        span = 0.8 / per[b]
        u0, u1 = 0.05 + span * s, 0.05 + span * (s + 1)
        cost = rev * (1 - gm / 100) * k
        prof = rev * gm / 100 * k
        um = (u0 + u1) / 2
        grow(root, f"cost{i}", xs[i], 0, w, 200, cost, m["cost"], F(b, u0), F(b, um))
        grow(root, f"gp{i}", xs[i], cost, w, 200, prof, m["gold"], F(b, um), F(b, u1))
    # the flat cost line across every quarter (cost ran $1.16B-$1.65B a quarter)
    line = empty("costline", root)
    box("costline_b", (-1500, 138, 5), (1500, 146, 15), m["line"], line)
    show(line, [(F(2, 0.7), END)])

    def top(i):
        return GM[i][1] * k

    def cst(i):
        return GM[i][1] * (1 - GM[i][2] / 100) * k

    label("2025Q1: 22.5% gross margin", (xs[2], top(2), -100), root, iv(0, 0.65, 1, 0))
    label("cost $1.31B of $1.70B (derived)", (xs[2] + 105, cst(2) * 0.5, 0), root, iv(0, 0.7, 1, 0))
    label("NAND contract +55-60% QoQ 1Q26", (xs[6], top(6) * 0.75, 0), root, iv(1, 0.75, 2, 0))
    label("2026Q1: 78.4% margin", (xs[6], top(6), -100), root, iv(1, 0.85, 2, 0))
    label("2026Q3: 85.0% gross margin", (xs[8], top(8), -100), root, iv(2, 0.75, 3, 0))
    label("cost $1.65B of $11.03B (derived)", (xs[8] + 105, cst(8) * 0.5, 0), root, iv(2, 0.75, 3, 0))
    label("cost per quarter ~flat", (-600, 146, 15), root, iv(2, 0.75, 3, 0))

    camera(
        root,
        [
            ((-830.0, 120.0, -100.0), 1050.0, 0.0, 0.10),
            ((-300.0, 330.0, -100.0), 2300.0, 0.0, 0.12),
            ((0.0, 560.0, -100.0), 2900.0, 0.0, 0.10),
        ],
    )
    fin("margins")


# ---- pricing -------------------------------------------------------------------------------

# FY2024 base; FY2025 bits +6%, ASP/GB +4% (FY2025 10-K); FY2026 bits +15% ("mid-teens", FY2026
# 10-K), revenue/GB derived = (20,248 / 7,355) / 1.15 = 2.39x
W0, H0, D0 = 560.0, 270.0, 220.0
FY = [("FY2024", 1.0, 1.0), ("FY2025", 1.06, 1.04), ("FY2026", 1.06 * 1.15, 1.04 * (20248 / 7355) / 1.15)]


def slab(root, mm, name, x0, wkeys, hkeys, mt):
    """A slab with its bottom-left front corner at (x0, 0, 0), width W0*w and height H0*h keyed."""
    pv = pivot(name, (x0, 0, 0), root)
    box(name + "_m", (0, 0, -D0), (W0, H0, 0), mt, pv)
    box(name + "_bits", (0, 0, 0), (W0, 10, 24), mm["dc_rail"], pv)  # width: bits sold
    box(name + "_price", (-24, 0, 0), (0, H0, 24), mm["gold_post"], pv)  # height: revenue per GB
    frames = sorted(set([f for f, _ in wkeys] + [f for f, _ in hkeys]))

    def val(ks, f):
        v = ks[0][1]
        for ff, vv in ks:
            if ff <= f:
                v = vv
        return v

    ks = [(0, (OFF, OFF, OFF))] + [(f, (val(wkeys, f), 1, val(hkeys, f))) for f in frames]
    scale_keys(pv, ks, until=frames[0])
    return pv


def build_pricing():
    m, root = begin("pricing")
    m["dc_rail"] = mat("sndk_bits_rail", (0.2, 0.9, 1.0), emit=(0.15, 0.85, 1.0), strength=2.5)
    m["gold_post"] = mat("sndk_price_post", (1.0, 0.78, 0.35), emit=(1.0, 0.75, 0.3), strength=2.5)
    floor(root, m, -1900, 1600, -500, 300)
    x0s = [-1650, -800, 150]
    # FY2024: the base slab
    slab(root, m, "fy24", x0s[0], [(F(0, 0.1), OFF), (F(0, 0.35), 1.0)], [(F(0, 0.1), 0.02), (F(0, 0.35), 0.02), (F(0, 0.6), 1.0)], m["edge"])
    # FY2025: starts as FY2024, width (bits) then height (price)
    w1, h1 = FY[1][1], FY[1][2]
    slab(root, m, "fy25", x0s[1], [(F(1, 0.05), 1.0), (F(1, 0.3), w1)], [(F(1, 0.05), 1.0), (F(1, 0.35), 1.0), (F(1, 0.6), h1)], m["edge"])
    ghost25 = gshow(root, "ghost25", [(F(1, 0.05), END)])
    box("ghost25_b", (x0s[1], 0, -D0 - 2), (x0s[1] + W0, H0, 4), m["ghost_grey"], ghost25)
    # FY2026
    w2, h2 = FY[2][1], FY[2][2]
    slab(root, m, "fy26", x0s[2], [(F(2, 0.05), w1), (F(2, 0.3), w2)], [(F(2, 0.05), h1), (F(2, 0.35), h1), (F(2, 0.7), h2)], m["dc"])
    ghost26 = gshow(root, "ghost26", [(F(2, 0.05), END)])
    box("ghost26_b", (x0s[2], 0, -D0 - 2), (x0s[2] + W0 * w1, H0 * h1, 4), m["ghost_grey"], ghost26)


    label("FY2024 revenue $6.66B", (x0s[0] + W0 / 2, H0, -D0 / 2), root, iv(0, 0.6, 1, 0))
    label("width = bits sold", (x0s[0] + W0, 4, 20), root, iv(0, 0.35, 1, 0))
    label("height = revenue per GB", (x0s[0] - 20, H0, 20), root, iv(0, 0.6, 1, 0))
    label("FY2025: bits +6%, price +4%", (x0s[1] + W0 * w1, H0 * h1 * 0.6, 0), root, iv(1, 0.6, 2, 0))
    label("FY2025 revenue $7.36B", (x0s[1] + W0 * w1 / 2, H0 * h1, -D0 / 2), root, iv(1, 0.65, 2, 0))
    label("FY2026: bits +15% (mid-teens)", (x0s[2] + W0 * w2, 4, 20), root, iv(2, 0.3, 3, 0))
    label("revenue per GB x2.4 (derived)", (x0s[2] - 20, H0 * h2 * 0.8, 20), root, iv(2, 0.7, 3, 0))
    label("FY2026 revenue $20.25B", (x0s[2] + W0 * w2 / 2, H0 * h2, -D0 / 2), root, iv(2, 0.75, 3, 0))
    label("datacenter $/GB +150%", (x0s[2] + W0 * w2, H0 * h2 * 0.55, 0), root, iv(2, 0.8, 3, 0))

    camera(
        root,
        [
            ((-1300.0, 170.0, -100.0), 1250.0, 0.12, 0.12),
            ((-850.0, 200.0, -100.0), 1750.0, 0.10, 0.12),
            ((-300.0, 360.0, -100.0), 2500.0, 0.10, 0.12),
        ],
    )
    fin("pricing")


# ---- share ---------------------------------------------------------------------------------

# TrendForce NAND revenue share: 2026Q1 (all five) and 2026Q2 (Samsung, Kioxia; SanDisk via Evertiq)
SHARE = [  # name, mat, 2026Q1 %, 2026Q2 % (None: no 2Q26 figure in the data)
    ("Samsung", "samsung", 31.6, 29.3),
    ("SK hynix", "sk", 17.6, None),
    ("Micron", "micron", 13.9, None),
    ("Kioxia", "kioxia", 13.9, 13.6),
    ("SanDisk", "red", 13.9, 11.4),
]


def build_share():
    m, root = begin("share")
    k = 30.0  # mm per percentage point
    w = 400.0
    xs = [-1600, -800, 0, 800, 1600]
    floor(root, m, -2000, 2000, -600, 300)
    top = {}
    for i, (name, mk, s1, s2) in enumerate(SHARE):
        x = xs[i]
        h1 = s1 * k
        if s2 is None:
            bar(root, f"t{i}", x, 0, w, w, h1, m[mk], [(F(0, 0.05 + 0.08 * i), 0.0), (F(0, 0.45 + 0.08 * i), 1.0), (F(1, 0.1), 1.0), (F(1, 0.2), OFF)])
            gh = gshow(root, f"ghost{i}", [(F(1, 0.2), END)])
            box(f"ghost{i}_b", (x - w / 2, 0, -w), (x + w / 2, h1, 0), m["ghost_grey"], gh)
        elif name != "SanDisk":
            h2 = s2 * k
            bar(root, f"t{i}", x, 0, w, w, h1, m[mk], [(F(0, 0.05 + 0.08 * i), 0.0), (F(0, 0.45 + 0.08 * i), 1.0), (F(1, 0.1), 1.0), (F(1, 0.45), h2 / h1)])
            top[name] = h2
    # SanDisk: grows, shrinks to 11.4, then climbs onto Kioxia's tower
    x = xs[4]
    sd = pivot("sandisk", (x, 0, 0), root)
    box("sandisk_m", (-w / 2 + 10, 0, -w + 10), (w / 2 - 10, 13.9 * k, -10), m["red"], sd)
    h1, h2 = 13.9 * k, 11.4 * k
    scale_keys(sd, [(0, (OFF, OFF, OFF)), (F(0, 0.37), (1, 1, OFF)), (F(0, 0.77), 1), (F(1, 0.1), 1), (F(1, 0.45), (1, 1, h2 / h1))], until=F(0, 0.37))
    kx, kh = xs[3], top["Kioxia"]
    for f, p in (
        (F(2, 0.1), (x, 0, 0)),
        (F(2, 0.3), (x, kh + 120, 0)),
        (F(2, 0.55), (kx, kh + 120, 0)),
        (F(2, 0.7), (kx, kh, 0)),
    ):
        key(sd, f, "location", P(*p))
    seam = gshow(root, "seam", [(F(2, 0.7), END)])
    box("seam_b", (kx - w / 2 - 6, kh - 5, -w - 6), (kx + w / 2 + 6, kh + 5, 6), m["line"], seam)

    label("Samsung 31.6%", (xs[0], 31.6 * k, -w / 2), root, iv(0, 0.6, 1, 0))
    label("SanDisk 13.9%, 2026Q1", (xs[4], 13.9 * k, -w / 2), root, iv(0, 0.75, 1, 0))
    label("tied: Kioxia, Micron 13.9%", (xs[2], 13.9 * k, -w / 2), root, iv(0, 0.8, 1, 0))
    label("SK hynix 17.6%", (xs[1], 17.6 * k, -w / 2), root, iv(0, 0.7, 1, 0))
    label("SanDisk 11.4%, 2026Q2", (xs[4], 11.4 * k, -w / 2), root, iv(1, 0.5, 2, 0))
    label("Kioxia 13.6%", (xs[3], 13.6 * k, -w / 2), root, iv(1, 0.5, 2, 0))
    label("Samsung 29.3%", (xs[0], 29.3 * k, -w / 2), root, iv(1, 0.5, 2, 0))
    label("no 2Q26 figure", (xs[1], 17.6 * k, -w / 2), root, iv(1, 0.3, 2, 0))
    label("Kioxia + SanDisk = 25.0%", (kx, kh + 11.4 * k, -w / 2), root, iv(2, 0.72, 3, 0))
    label("same JV fabs", (kx + w / 2, kh, 0), root, iv(2, 0.75, 3, 0))
    label("Samsung 29.3%", (xs[0], 29.3 * k, -w / 2), root, iv(2, 0.5, 3, 0))

    camera(
        root,
        [
            ((0.0, 430.0, -200.0), 2900.0, 0.0, 0.16),
            ((0.0, 430.0, -200.0), 2900.0, 0.0, 0.16),
            ((-300.0, 470.0, -200.0), 2800.0, 0.0, 0.14),
        ],
    )
    fin("share")


# ---- kioxia --------------------------------------------------------------------------------


def fab(root, m, name, x, w, h, d, mt, f0, f1, z1=-80.0):
    pv = pivot(name, (x, 0, 0), root)
    box(name + "_body", (-w / 2, 0, z1 - d), (w / 2, h, z1), mt, pv)
    box(name + "_roof", (-w / 2 + 30, h, z1 - d + 40), (w / 2 - 30, h + 40, z1 - 40), m["fab_roof"], pv)
    scale_keys(pv, [(0, (OFF, OFF, OFF)), (f0, (1, 1, OFF)), (f1, 1)], until=f0)
    return pv


def build_kioxia():
    m, root = begin("kioxia")
    floor(root, m, -2500, 1800, -700, 400)
    # Yokkaichi: six fabs (Fab2..Fab7); Kitakami: Fab1, Fab2, and Fab3 under construction
    yx = [-2250 + 260 * i for i in range(6)]
    for i, x in enumerate(yx):
        fab(root, m, f"yok{i}", x, 220, 260 + 20 * (i % 2), 360, m["fab"], F(0, 0.05 + 0.06 * i), F(0, 0.3 + 0.06 * i))
    kx = [-500, -230]
    for i, x in enumerate(kx):
        fab(root, m, f"kit{i}", x, 230, 300, 380, m["fab"], F(0, 0.45 + 0.08 * i), F(0, 0.7 + 0.08 * i))
    fab(root, m, "kit3", 110, 320, 400, 440, m["fab3"], F(2, 0.1), F(2, 0.6))
    # Fab3's footprint, waiting for it
    pad = gshow(root, "fab3_pad", [(F(0, 0.8), F(2, 0.1))])
    box("fab3_pad_b", (-50, 0, -560), (270, 8, -80), m["ghost"], pad)

    # the belt along the front and the two piles at the right
    box("belt", (-2400, 0, 60), (700, 14, 200), m["belt"], root)
    box("belt_k", (700, 0, -120), (1000, 14, 200), m["belt"], root)
    bxK, bxS = 1050.0, 1450.0
    box("pile_k_base", (bxK - 130, 0, -20), (bxK + 130, 14, 240), m["fab_roof"], root)
    box("pile_s_base", (bxS - 130, 0, -20), (bxS + 130, 14, 240), m["red"], root)
    pattern = "KSKSK"
    nK = nS = 0
    for j in range(25):
        who = pattern[j % 5]
        start_x = -900.0 if j % 2 == 0 else -100.0
        g = empty(f"wf{j}", root)
        wafer(g, f"wf{j}_d", (start_x, 22, 130), 105, m["wafer_red"] if who == "S" else m["wafer"], t=14)
        if who == "K":
            tx, ty = bxK, 22 + 18 * nK
            nK += 1
        else:
            tx, ty = bxS, 22 + 18 * nS
            nS += 1
        f0 = F(1, 0.03 + 0.032 * j)
        path = [(0, 0, 0), (650 - start_x, 0, 0), (tx - start_x, 0, 0), (tx - start_x, ty - 22 + 4, 0)]
        fly(g, path, f0, f0 + 50, steps=6)
        show(g, [(f0, END)])

    label("Yokkaichi: 6 fabs (Fab2-7)", (yx[2] + 130, 300, -260), root, iv(0, 0.4, 1, 0))
    label("Kitakami: Fab1 + Fab2", (kx[1], 320, -260), root, iv(0, 0.75, 1, 0))
    label("shared JV fabs in Japan", (-900, 14, 130), root, iv(0, 0.5, 1, 0))
    label("Kioxia: 60% of capacity", (bxK, 22 + 18 * 15, 130), root, iv(1, 0.6, 2, 0))
    label("SanDisk: 40%", (bxS, 22 + 18 * 10, 130), root, iv(1, 0.6, 2, 0))
    label("same BiCS wafers, split 3:2", (650, 14, 130), root, iv(1, 0.2, 2, 0))
    label("Kitakami Fab3 ~JPY 1.8T est", (110, 440, -300), root, iv(2, 0.5, 3, 0))
    label("JV plan: JPY 5T through 2032", (-1600, 280, -260), root, iv(2, 0.3, 3, 0))
    label("JV extended to Dec 2034", (-500, 300, -260), root, iv(2, 0.4, 3, 0))
    label("SanDisk pays Kioxia $1.17B", (bxS, 22 + 18 * 10, 130), root, iv(2, 0.6, 3, 0))

    camera(
        root,
        [
            ((-1050.0, 240.0, -200.0), 2400.0, 0.0, 0.30),
            ((150.0, 200.0, -50.0), 2550.0, 0.0, 0.28),
            ((-350.0, 240.0, -150.0), 2900.0, 0.0, 0.28),
        ],
    )
    fin("kioxia")


# ---- tech ----------------------------------------------------------------------------------

LAYER_MM = 2.5
PLATE_LAYERS = 8  # one plate drawn per eight layers
STACK_W, STACK_D = 820.0, 420.0


def layer_stack(root, m, name, xc, layers, y0, f0, f1, group=10):
    """`layers` drawn as plates (one per PLATE_LAYERS), revealed bottom-up in groups over [f0, f1].
    Returns the group empty and the stack's top height."""
    g = empty(name, root)
    n = layers // PLATE_LAYERS
    t = LAYER_MM * PLATE_LAYERS
    ngroups = math.ceil(n / group)
    for gi in range(ngroups):
        objs = []
        for k in range(gi * group, min(n, (gi + 1) * group)):
            y = y0 + k * t
            objs.append(box(f"{name}_p{k}", (xc - STACK_W / 2, y, -STACK_D), (xc + STACK_W / 2, y + t * 0.62, 0), m["wl"], None))
            objs.append(box(f"{name}_o{k}", (xc - STACK_W / 2, y + t * 0.62, -STACK_D), (xc + STACK_W / 2, y + t, 0), m["ox"], None))
        e = empty(f"{name}_g{gi}", g)
        join(objs, f"{name}_g{gi}_m", e)
        f = round(f0 + (f1 - f0) * gi / max(1, ngroups - 1))
        show(e, [(f, END)])
    top = y0 + n * t
    # channel holes through every layer: glowing pillars on the cut face, grown after the stack
    ch = pivot(name + "_ch", (xc, y0, 0), g)
    for i in range(7):
        cx = -STACK_W / 2 + 110 + i * (STACK_W - 220) / 6
        tube(f"{name}_ch{i}", (cx, 0, 0), (cx, top - y0 + 6, 0), 13, m["chan"], ch, verts=10)
    scale_keys(ch, [(0, (OFF, OFF, OFF)), (f1, (1, 1, OFF)), (f1 + 40, 1)], until=f1)
    return g, top


def build_tech():
    m, root = begin("tech")
    floor(root, m, -1800, 1900, -700, 300)
    x8, x10 = -650.0, 450.0
    base = 50.0
    box("sub8", (x8 - STACK_W / 2 - 20, 0, -STACK_D - 20), (x8 + STACK_W / 2 + 20, base, 0), m["cmos"], root)
    _, top8 = layer_stack(root, m, "bics8", x8, 218, base, F(0, 0.05), F(0, 0.55))

    # BiCS10: built on its own wafer in beat 1, then lifted in beat 2 for the CMOS wafer to go under
    lift = empty("lift10", root)
    _, top10 = layer_stack(lift, m, "bics10", x10, 332, base + 40, F(1, 0.05), F(1, 0.6))
    arr_g = gshow(lift, "arr_sub_g", [(F(1, 0.0), END)])
    arr_sub = box("arr_sub", (x10 - STACK_W / 2 - 20, base, -STACK_D - 20), (x10 + STACK_W / 2 + 20, base + 40, 0), m["ox"], arr_g)
    sub_g = empty("sub10_g", root)
    box("sub10", (x10 - STACK_W / 2 - 20, 0, -STACK_D - 20), (x10 + STACK_W / 2 + 20, base, 0), m["wafer"], sub_g)
    show(sub_g, [(F(1, 0.0), F(2, 0.25))])
    _ = arr_sub
    key(lift, 0, "location", P(0, 0, 0))
    key(lift, F(2, 0.05), "location", P(0, 0, 0))
    key(lift, F(2, 0.25), "location", P(0, 120, 0))
    key(lift, F(2, 0.6), "location", P(0, 120, 0))
    key(lift, F(2, 0.75), "location", P(0, 30, 0))
    # the CMOS wafer slides in from the right under the lifted array, with copper bond pads
    cm = empty("cmos10", root)
    box("cmos10_b", (x10 - STACK_W / 2 - 20, 0, -STACK_D - 20), (x10 + STACK_W / 2 + 20, 70, 0), m["cmos"], cm)
    for i in range(9):
        px = x10 - STACK_W / 2 + 40 + i * (STACK_W - 80) / 8
        box(f"pad{i}", (px - 22, 70, -60), (px + 22, 76, 0), m["pad"], cm)
    for f, dx in ((F(2, 0.25), 1500), (F(2, 0.55), 0)):
        key(cm, f, "location", P(dx, 0, 0))
    show(cm, [(F(2, 0.25), END)])

    label("BiCS8: 218 layers", (x8, top8, -STACK_D / 2), root, iv(0, 0.55, 1, 0))
    label("in volume; 15% of bits 2025Q3", (x8 + STACK_W / 2, top8 * 0.5, 0), root, iv(0, 0.65, 1, 0))
    label("BiCS10: 332 layers, +52%", (x10, top10, -STACK_D / 2), lift, iv(1, 0.6, 2, 0))
    label("TLC >29 Gb/mm2, +59%", (x10 + STACK_W / 2, top10 * 0.55, 0), lift, iv(1, 0.7, 2, 0))
    label("samples Jul 2026", (x10 + STACK_W / 2, top10 * 0.25, 0), lift, iv(1, 0.75, 2, 0))
    label("CMOS wafer bonded under array", (x10 + STACK_W / 2 + 20, 70, 0), cm, iv(2, 0.55, 3, 0))
    label("4.8 Gb/s per pin, +33%", (x10, top10, -STACK_D / 2), lift, iv(2, 0.75, 3, 0))
    label("QLC >37 Gb/mm2", (x10 - STACK_W / 2, top10 * 0.6, 0), lift, iv(2, 0.8, 3, 0))
    label("volume 2027 at Kitakami", (x10 + STACK_W / 2, top10 * 0.5, 0), lift, iv(2, 0.8, 3, 0))

    camera(
        root,
        [
            ((-650.0, 380.0, -200.0), 1700.0, 0.12, 0.16),
            ((-100.0, 520.0, -200.0), 2250.0, 0.10, 0.14),
            ((-50.0, 520.0, -200.0), 2550.0, 0.10, 0.12),
        ],
    )
    fin("tech")


# ---- hbf -----------------------------------------------------------------------------------


def build_hbf():
    m, root = begin("hbf")
    H.mats(m)
    H.package(root, m)
    pkg = H.SUB_X
    _ = pkg
    xs = H.STACK_XS  # (-1500, -850, 850, 1500)
    n = 16
    # left pair: HBM4 DRAM stacks, stay; right pair: HBM4 that leaves in beat 1
    for i, x in enumerate(xs[:2]):
        H.stack(root, m, x, n, f"hbm{i}", phy=1, tsv=False)
    out = empty("hbm_out", root)
    for i, x in enumerate(xs[2:]):
        H.stack(out, m, x, n, f"hbmR{i}", phy=-1, tsv=False)
    key(out, 0, "location", P(0, 0, 0))
    key(out, F(1, 0.1), "location", P(0, 0, 0))
    key(out, F(1, 0.4), "location", P(0, 1600, 0))
    show(out, [(0, F(1, 0.4))])
    # HBF: the same 16-high footprint, NAND dies
    dram = m["dram"]
    m["dram"] = m["nand"]
    inn = empty("hbf_in", root)
    for i, x in enumerate(xs[2:]):
        H.stack(inn, m, x, n, f"hbf{i}", phy=-1, tsv=False)
    m["dram"] = dram
    key(inn, 0, "location", P(0, 1600, 0))
    key(inn, F(1, 0.4), "location", P(0, 1600, 0))
    key(inn, F(1, 0.7), "location", P(0, 0, 0))
    show(inn, [(F(1, 0.4), END)])

    # beat 2: capacity per stack, 64 GB : 512 GB : 1536 GB as bars to the right
    k = 0.62
    bx = [2750.0, 3200.0, 3650.0]
    for j, (gb, mk) in enumerate(((64, "dram"), (512, "nand"), (1536, "nand2"))):
        grow(root, f"cap{j}", bx[j], 0, 300, 300, gb * k, m[mk], F(2, 0.1 + 0.12 * j), F(2, 0.45 + 0.12 * j))
    cf = gshow(root, "cap_floor_g", [(F(2, 0.0), END)])
    box("cap_floor", (2450, H.SUB_Y0, -500), (3900, 0, 100), m["floor"], cf)

    top = H.DIE_TOP_16
    label("GPU", (0, H.GPU_Y1, -H.GPU_Z / 2), root, iv(0, 0.2, 1, 0.4))
    label("HBM4: 64 GB per stack", (xs[0], top, -H.DIE_HALF), root, iv(0, 0.3, 1, 1))
    label("DRAM dies", (xs[1] + H.DIE_HALF, top * 0.6, 0), root, iv(0, 0.4, 1, 0))
    label("silicon interposer", (1200, 0, -100), root, iv(0, 0.5, 1, 0))
    label("HBF: 16 NAND dies x 256Gb", (xs[2] - H.DIE_HALF, top * 0.6, 0), root, iv(1, 0.72, 2, 0))
    label("512 GB per stack = 8x HBM4", (xs[3], top, -H.DIE_HALF), root, iv(1, 0.75, 2, 0))
    label("8-16x HBM capacity (SanDisk)", (xs[3] + H.DIE_HALF, top * 0.3, 0), root, iv(1, 0.85, 2, 0))
    label("HBM4 64 GB", (bx[0], 64 * k, -150), root, iv(2, 0.45, 3, 0))
    label("HBF gen1 512 GB, 1.6 TB/s", (bx[1], 512 * k, -150), root, iv(2, 0.6, 3, 0))
    label("gen3 1.5 TB, >3.2 TB/s", (bx[2], 1536 * k, -150), root, iv(2, 0.75, 3, 0))
    label("product samples 2027", (xs[3], top, -H.DIE_HALF), root, iv(2, 0.8, 3, 0))

    camera(
        root,
        [
            ((0.0, 380.0, -300.0), 3500.0, 0.0, 0.20),
            ((450.0, 380.0, -300.0), 3300.0, 0.0, 0.20),
            ((2250.0, 470.0, -300.0), 3000.0, 0.0, 0.12),
        ],
    )
    fin("hbf")


# ---- sources -------------------------------------------------------------------------------

# rows in data/memory_facts/sndk.jsonl (168), by publisher and by basis
PUBS = [("SEC 8-K / 10-K: 73 rows", 73, "paper_sec"), ("TrendForce: 28", 28, "paper"), ("Blocks & Files: 26", 26, "paper2"),
        ("StorageReview: 11", 11, "paper"), ("8 other sites: 30", 30, "paper2")]
BASIS = [("company-stated: 129 rows", 129, "green"), ("guidance: 18", 18, "amber"), ("share trackers: 14", 14, "blue"),
         ("estimates: 7", 7, "est_red")]
SHEET = 8.0  # mm per row


def paper_stack(root, m, name, x, rows, mt, f0, f1, hide=None, group=6):
    g = empty(name, root)
    ng = math.ceil(rows / group)
    for gi in range(ng):
        objs = []
        for r in range(gi * group, min(rows, (gi + 1) * group)):
            dx = 14 * math.sin(r * 2.3)
            dz = 10 * math.cos(r * 1.7)
            objs.append(box(f"{name}_s{r}", (x - 150 + dx, r * SHEET, -380 + dz), (x + 150 + dx, r * SHEET + SHEET * 0.8, -20 + dz), mt, None))
        e = empty(f"{name}_g{gi}", g)
        join(objs, f"{name}_g{gi}_m", e)
        f = round(f0 + (f1 - f0) * gi / max(1, ng - 1))
        show(e, [(f, hide if hide else END)])
    return rows * SHEET


def build_sources():
    m, root = begin("sources")
    floor(root, m, -2000, 3400, -600, 300)
    px = [-1600 + 420 * i for i in range(5)]
    tops = []
    for i, (txt, n, mk) in enumerate(PUBS):
        tops.append(paper_stack(root, m, f"pub{i}", px[i], n, m[mk], F(0, 0.05 + 0.08 * i), F(0, 0.4 + 0.08 * i), hide=F(1, 0.15)))
        label(txt, (px[i], tops[-1], -200), root, iv(0, 0.5, 1, 0.15) if i < 4 else [])
    bx = [-1500 + 520 * i for i in range(4)]
    for i, (txt, n, mk) in enumerate(BASIS):
        t = paper_stack(root, m, f"bas{i}", bx[i], n, m[mk], F(1, 0.15 + 0.08 * i), F(1, 0.55 + 0.08 * i), hide=F(2, 0.05))
        label(txt, (bx[i], t, -200), root, iv(1, 0.6, 2, 0))

    # beat 2: the same number from two sources, as paired bars (scaled to the larger = 700 mm)
    pairs = [
        ("Kioxia FY25 op profit 870 v 876", 870.0, 876.2),
        ("SanDisk 2026Q1 share 13.0 v 13.9", 13.0, 13.9),
        ("Kioxia FY26 capex 450B v 470B", 450.0, 470.0),
        ("Kioxia 1Q26 guide 890 v 1003", 890.0, 1002.9),
    ]
    cx = [900 + 620 * i for i in range(4)]
    for i, (txt, a, b) in enumerate(pairs):
        mx = max(a, b)
        f0 = F(2, 0.08 + 0.1 * i)
        grow(root, f"pa{i}", cx[i] - 95, 0, 170, 200, 700 * a / mx, m["srcA"], f0, f0 + 50)
        grow(root, f"pb{i}", cx[i] + 95, 0, 170, 200, 700 * b / mx, m["srcB"], f0 + 10, f0 + 60)
        label(txt, (cx[i], 700 + 10, -100), root, iv(2, 0.25 + 0.1 * i, 3, 0))

    camera(
        root,
        [
            ((-800.0, 330.0, -200.0), 2400.0, 0.0, 0.20),
            ((-650.0, 520.0, -200.0), 2500.0, 0.0, 0.18),
            ((1850.0, 380.0, -200.0), 2400.0, 0.0, 0.16),
        ],
    )
    fin("sources")


BUILDERS = {
    "snapshot": build_snapshot,
    "revenue": build_revenue,
    "markets": build_markets,
    "margins": build_margins,
    "pricing": build_pricing,
    "share": build_share,
    "kioxia": build_kioxia,
    "tech": build_tech,
    "hbf": build_hbf,
    "sources": build_sources,
}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for tab in argv or list(BUILDERS):
        BUILDERS[tab]()
