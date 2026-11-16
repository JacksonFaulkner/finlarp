"""Custom 3D scenes for the CXMT (688825.SS) memory R&D page, one per tab.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/mem_cxmt.py [-- <tab> ...]

Each scene is 3 beats of 8 s (frames 0..576) framed wide (about 3:1) and is exported to
tools/pbr3d/assets/mem/cxmt_<tab>.glb, which py/derive/memory_page.py picks up.

Every number drawn (bar heights, counts, tags) comes from data/memory_facts/cxmt.jsonl or the
cached page (derive/memory_page.py 688825.SS --json); see the comment on each scene.
"""

import math
import os
import random
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sand_overview as O  # noqa: E402
from sand_overview import OFF, F, P, box, empty, key, label, mat, pivot, show, tube  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402

END = F(3, 0)
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "assets", "mem"))
PRIVATE = os.environ.get("CXMT_PRIVATE", "")


# ---- kit ------------------------------------------------------------------------------


def mats(m):
    m["rev"] = mat("cx_rev", (0.30, 0.55, 0.95), metal=0.2, rough=0.4)
    m["loss"] = mat("cx_loss", (0.95, 0.22, 0.18), rough=0.5, emit=(0.95, 0.18, 0.12), strength=1.4)
    m["profit"] = mat("cx_profit", (0.30, 0.90, 0.50), rough=0.4, emit=(0.25, 0.85, 0.45), strength=1.2)
    m["gold"] = mat("cx_gold", (0.95, 0.72, 0.30), metal=0.3, rough=0.35, emit=(1.0, 0.65, 0.15), strength=0.5)
    m["ghost"] = mat("cx_ghost", (0.60, 0.75, 0.95), rough=0.2, alpha=0.22)
    m["ghost_gold"] = mat("cx_ghost_gold", (1.0, 0.8, 0.4), rough=0.2, alpha=0.3)
    m["grey"] = mat("cx_grey", (0.45, 0.48, 0.55), metal=0.2, rough=0.6)
    m["cost"] = mat("cx_cost", (0.70, 0.72, 0.78), metal=0.3, rough=0.4)
    m["floor"] = mat("cx_floor", (0.045, 0.05, 0.065), rough=0.95)
    m["fcst"] = mat("cx_fcst", (0.45, 0.62, 0.90), rough=0.3, alpha=0.35)
    m["brand"] = mat("cx_brand", (0.20, 0.85, 0.85), rough=0.35, emit=(0.15, 0.8, 0.8), strength=1.0)
    m["ssg"] = mat("cx_samsung", (0.25, 0.45, 0.95), rough=0.4)
    m["skh"] = mat("cx_skhynix", (0.95, 0.52, 0.15), rough=0.4)
    m["mu"] = mat("cx_micron", (0.62, 0.42, 0.92), rough=0.4)
    m["other"] = mat("cx_other", (0.30, 0.32, 0.36), rough=0.6)
    m["wafer"] = mat("cx_wafer", (0.55, 0.58, 0.64), metal=0.9, rough=0.2)
    m["die"] = mat("cx_die", (0.40, 0.72, 0.78), metal=0.4, rough=0.35)
    m["good"] = mat("cx_good", (0.35, 0.95, 0.55), emit=(0.3, 0.9, 0.5), strength=1.6)
    m["bad"] = mat("cx_bad", (1.0, 0.25, 0.2), emit=(1.0, 0.2, 0.15), strength=2.0)
    m["dram"] = mat("cx_dram", (0.93, 0.52, 0.18), rough=0.45)
    m["base"] = mat("cx_base", (0.25, 0.45, 0.95), metal=0.2, rough=0.4)
    m["paper"] = mat("cx_paper", (0.90, 0.88, 0.82), rough=0.85)
    m["cursor"] = mat("cx_cursor", (0.4, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=2.5, alpha=0.6)
    m["amber"] = mat("cx_amber", (1.0, 0.70, 0.20), emit=(1.0, 0.65, 0.15), strength=1.6)
    m["amber_ghost"] = mat("cx_amber_ghost", (1.0, 0.70, 0.25), rough=0.3, alpha=0.3)
    m["court"] = mat("cx_court", (0.45, 0.65, 1.0), emit=(0.4, 0.6, 1.0), strength=1.6)
    m["fab"] = mat("cx_fab", (0.78, 0.80, 0.84), metal=0.2, rough=0.5)
    m["roof"] = mat("cx_roof", (0.30, 0.33, 0.38), metal=0.5, rough=0.4)
    m["si"] = mat("cx_si", (0.35, 0.38, 0.45), metal=0.6, rough=0.3)
    for i, c in enumerate(((1.0, 0.35, 0.3), (0.35, 0.9, 0.45), (0.35, 0.6, 1.0), (1.0, 0.85, 0.3))):
        m[f"pass{i}"] = mat(f"cx_pass{i}", c, emit=c, strength=1.8)
    m["path0"] = mat("cx_path0", (0.4, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=2.5)
    m["path1"] = mat("cx_path1", (1.0, 0.75, 0.3), emit=(1.0, 0.72, 0.25), strength=2.5)
    m["path2"] = mat("cx_path2", (1.0, 0.4, 0.6), emit=(1.0, 0.35, 0.55), strength=2.5)
    return m


def tag(text, at, parent, f0, f1=END):
    assert len(text) <= 32, text
    return label(text, at, parent, [(f0, f1)])


def grp(name, parent, f0=None, f1=END):
    """A group empty; if f0 is given it is switched on for [f0, f1)."""
    g = empty(name, parent)
    if f0 is not None:
        show(g, [(f0, f1)])
    return g


def bar(parent, name, x, z, w, d, h, m, f0, f1, y0=0.0, later=()):
    """A bar standing at (x, y0, z), growing to height h (negative grows down) over [f0, f1].
    `later` = (frame, fraction of h) keys after it has grown."""
    b = pivot(name, (x, y0, z), parent)
    lo, hi = min(0.0, h), max(0.0, h)
    box(f"{name}_box", (-w / 2, lo, -d / 2), (w / 2, hi, d / 2), m, b)
    keys = [(0, (OFF,) * 3), (f0, (1, 1, OFF)), (f1, (1, 1, 1))]
    keys += [(f, (1, 1, max(v, OFF))) for f, v in later]
    if keys[-1][0] < END:
        keys.append((END, keys[-1][1]))
    scale_keys(b, keys, until=f0)
    return b


def prism(name, pts, z0, z1, m, parent=None):
    """The poly-XY polygon `pts` extruded along poly z from z0 to z1 (faces the camera)."""
    me = bpy.data.meshes.new(name)
    n = len(pts)
    verts = [tuple(P(x, y, z0)) for x, y in pts] + [tuple(P(x, y, z1)) for x, y in pts]
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


def circle_pts(cx, cy, r, n=64):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def wedge(name, c, r0, r1, u0, u1, z0, z1, m, parent=None):
    """A ring sector from fraction u0 to u1 of a full turn, clockwise from 12 o'clock."""
    steps = max(2, int(abs(u1 - u0) * 96))
    angs = [math.pi / 2 - 2 * math.pi * (u0 + (u1 - u0) * i / steps) for i in range(steps + 1)]
    outer = [(c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a)) for a in angs]
    inner = [(c[0] + r0 * math.cos(a), c[1] + r0 * math.sin(a)) for a in reversed(angs)]
    return prism(name, outer + inner, z0, z1, m, parent)


def ring_point(c, r, u):
    a = math.pi / 2 - 2 * math.pi * u
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def floor(parent, m, x0, x1, z0=-500.0, z1=500.0, y=0.0):
    box("floor", (x0, y - 30, z0), (x1, y, z1), m["floor"], parent)


def finish_mem(tab):
    os.makedirs(OUT_DIR, exist_ok=True)
    if PRIVATE:
        os.makedirs(PRIVATE, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PRIVATE, f"cxmt_{tab}.blend"))
    glb = os.path.join(OUT_DIR, f"cxmt_{tab}.glb")
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


def begin(tab):
    m, root = start(tab, beats=3, page="mem_cxmt")
    return mats(m), root


# ---- revenue: years of losses, then the profit turn ------------------------------------
# cxmt.jsonl: revenue 2022 8.287, 2023 9.087, 2024 24.178, 2025 61.799, 2026Q1 50.8 (CNY B);
# net income 2022 -8.328, 2023 -16.34, 2024 -7.145, 2025 1.875 (1.9), 2026Q1 24.8;
# 2026Q2 implied from 2026H1 guidance midpoints (115 - 50.8 = 64.2, 53.5 - 24.8 = 28.7), est.

K_REV = 30.0  # mm per CNY billion


def build_revenue():
    m, root = begin("revenue")
    # the zero line: a thin rail the net bars hang from or rise off
    box("zero", (-3500, -8, -30), (3400, 8, 160), m["cost"], root)
    periods = [  # x, revenue, net, beat, u, ghost
        (-3000, 8.287, -8.328, 0, 0.05, False),
        (-1900, 9.087, -16.34, 0, 0.20, False),
        (-800, 24.178, -7.145, 0, 0.40, False),
        (300, 61.799, 1.875, 1, 0.08, False),
        (1800, 50.8, 24.8, 2, 0.05, False),
        (2900, 64.2, 28.7, 2, 0.50, True),
    ]
    for i, (x, rev, net, b, u, ghost) in enumerate(periods):
        f0 = F(b, u)
        bar(root, f"rev{i}", x - 140, 0, 250, 250, rev * K_REV, m["ghost"] if ghost else m["rev"], f0, f0 + 40)
        nm = m["ghost_gold"] if ghost else (m["profit"] if net > 0 else m["loss"])
        h = max(net * K_REV, 12.0) if net > 0 else net * K_REV
        bar(root, f"net{i}", x + 140, 0, 250, 250, h, nm, f0 + 30, f0 + 70)
    # a divider between the annual bars and the single quarters
    box("divider", (1045, -300, -20), (1065, 300, 20), m["ghost"], root)

    tag("2022 net CNY -8.3B", (-2860, -250, 130), root, F(0, 0.35), F(1, 0))
    tag("2023 net CNY -16.3B", (-1760, -490, 130), root, F(0, 0.45))
    tag("2024 revenue CNY 24.2B", (-940, 725, 130), root, F(0, 0.65), F(1, 0))
    tag("2025 revenue CNY 61.8B", (160, 1854, 130), root, F(1, 0.35), F(2, 0))
    tag("2025 net +CNY 1.9B: first profit", (440, 60, 130), root, F(1, 0.45), F(2, 0))
    tag("2026Q1 alone: CNY 50.8B", (1660, 1524, 130), root, F(2, 0.30))
    tag("2026Q1 net +CNY 24.8B", (1940, 744, 130), root, F(2, 0.40))
    tag("Q2 implied CNY 64.2B est", (2760, 1926, 130), root, F(2, 0.70))

    camera(root, [((-1800, 160, 0), 3000, 0.05, 0.10), ((-1100, 700, 0), 4800, 0.05, 0.10),
                  ((0, 760, 0), 5600, 0.05, 0.10)])
    finish_mem("revenue")


# ---- margins: why the margin exists now ------------------------------------------------
# Revenue per CNY of all-in cost (cost = revenue - net income) = 1 / (1 - net margin), from the
# page's net margin series: 2022 -100.49%, 2023 -179.82%, 2024 -29.37%, 2025 +3.07%,
# 2026Q1 +48.82%. Cost is drawn as a flat line at C; the revenue column is C / (1 - NM).
# Tags: DDR price -46.61% (2023), +54.72% (2024), gross margin 2025H1 12.72% (prospectus);
# 2026Q1 ASP +57% QoQ, bits +11% QoQ (Korea Herald); server share 8.4% -> 26.5%.

C = 900.0


def build_margins():
    m, root = begin("margins")
    floor(root, m, -3000, 3000, -400, 400)
    box("cost_line", (-2900, C - 18, -40), (2900, C + 18, 260), m["cost"], root)
    nms = [(-2400, -100.49, 0, 0.05), (-1200, -179.82, 0, 0.30), (0, -29.37, 1, 0.05), (1200, 3.07, 1, 0.35),
           (2400, 48.82, 2, 0.08)]
    for i, (x, nm, b, u) in enumerate(nms):
        r = C / (1 - nm / 100)
        f0 = F(b, u)
        bar(root, f"rev{i}", x, 0, 420, 420, min(r, C - 18), m["rev"], f0, f0 + 36)
        if r < C:
            bar(root, f"gap{i}", x, 0, 380, 380, C - 18 - r, m["loss"], f0 + 36, f0 + 66, y0=r)
        else:
            bar(root, f"gap{i}", x, 0, 420, 420, r - C - 18, m["gold"], f0 + 36, f0 + 80, y0=C + 18)

    tag("all costs = revenue - net", (-2900, C + 20, 300), root, F(0, 0.15), F(1, 0))
    tag("2022 net margin -100%", (-2400, 600, 210), root, F(0, 0.30), F(1, 0))
    tag("DDR price 2023: -46.6%", (-1200, 322, 210), root, F(0, 0.45), F(1, 0))
    tag("2023 net margin -180%", (-1200, 700, 210), root, F(0, 0.55))
    tag("DDR price 2024: +54.7%", (0, 696, 210), root, F(1, 0.25), F(2, 0))
    tag("gross margin 2025H1 12.7%", (1200, 929, 210), root, F(1, 0.55), F(2, 0))
    tag("server mix 8.4% to 26.5% of rev", (1200, 500, 210), root, F(1, 0.65), F(2, 0))
    tag("DRAM price Q1 2026 +57% QoQ", (2400, 1759, 210), root, F(2, 0.30))
    tag("bits only +11% QoQ", (2400, 500, 210), root, F(2, 0.45))
    tag("2026Q1 net margin 48.8%", (2400, 1300, 210), root, F(2, 0.55))

    camera(root, [((-1500, 650, 0), 3300, 0.05, 0.12), ((-300, 750, 0), 4300, 0.05, 0.12),
                  ((150, 900, 0), 4800, 0.05, 0.12)])
    finish_mem("margins")


# ---- capacity: wafer stacks, then forecasts that diverge -------------------------------
# kwpm (cxmt.jsonl): 2020 40 est, 2022 70 est, 2023 120 est, end-2025 265 (SemiAnalysis) with
# output 240 (Omdia), Sep 2026 320 (Commercial Times), end-2026 350 / 2027 420 (SemiAnalysis),
# 2028: 500 SemiAnalysis, 550 Nomura, 600 lower bound (Reuters via TrendForce).

WPITCH = 30.0  # mm per 10k wafers/month


def wafer_stack(parent, m, name, x, kwpm, mat_key, f0, f1, r=190.0, solid=False):
    g = pivot(name, (x, 0, 0), parent)
    n = 0 if solid else kwpm / 10.0
    if solid:  # a forecast: one translucent column, no wafers in it yet
        bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=r, depth=top(kwpm), location=P(0, top(kwpm) / 2, 0))
        o = bpy.context.object
        o.name = f"{name}_col"
        o.data.materials.append(m[mat_key])
        o.parent = g
    k = 0
    while n > 0:
        t = 22.0 * min(1.0, n)
        y = k * WPITCH
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=t, location=P(0, y + t / 2, 0))
        o = bpy.context.object
        o.name = f"{name}_w{k}"
        o.data.materials.append(m[mat_key])
        o.parent = g
        n -= 1
        k += 1
    scale_keys(g, [(0, (OFF,) * 3), (f0, (1, 1, OFF)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    return g


def top(kwpm):
    return (math.ceil(kwpm / 10.0) - 1) * WPITCH + 22.0 * min(1.0, kwpm / 10.0 - math.ceil(kwpm / 10.0) + 1)


def build_capacity():
    m, root = begin("capacity")
    floor(root, m, -3400, 3100, -400, 400)
    hist = [(-3000, 40, 0, 0.05), (-2350, 70, 0, 0.25), (-1700, 120, 0, 0.45), (-900, 265, 1, 0.05), (-150, 320, 1, 0.40)]
    for i, (x, v, b, u) in enumerate(hist):
        wafer_stack(root, m, f"hist{i}", x, v, "wafer", F(b, u), F(b, u) + 60)
    # Omdia's output at end-2025: a red ring round the 2025 stack at 240k
    ring = pivot("out_ring", (-900, 0, 0), root)
    bpy.ops.mesh.primitive_torus_add(major_radius=230, minor_radius=14, location=P(0, top(240), 0))
    o = bpy.context.object
    o.name = "out_ring_m"
    o.data.materials.append(m["bad"])
    o.parent = ring
    show(ring, [(F(1, 0.30), END)])

    fc = [(650, 350, 0.05), (1450, 420, 0.20)]
    for i, (x, v, u) in enumerate(fc):
        wafer_stack(root, m, f"fc{i}", x, v, "fcst", F(2, u), F(2, u) + 50, solid=True)
    X28 = 2350.0
    wafer_stack(root, m, "end", X28, 600, "fcst", F(2, 0.38), F(2, 0.38) + 50, solid=True)
    for i, (v, pk) in enumerate(((500, "path0"), (550, "path1"), (600, "path2"))):
        f0 = F(2, 0.45 + 0.08 * i)
        p = pivot(f"path{i}", (1450 + 190, top(420), 0), root)
        tube(f"path{i}_t", (0, 0, 0), (X28 - 215 - 1640, top(v) - top(420), 0), 13, m[pk], p, verts=10)
        rg = pivot(f"ring{i}", (X28, top(v), 0), root)
        bpy.ops.mesh.primitive_torus_add(major_radius=215, minor_radius=16, location=P(0, 0, 0))
        o = bpy.context.object
        o.name = f"ring{i}_m"
        o.data.materials.append(m[pk])
        o.parent = rg
        show(p, [(f0, END)])
        show(rg, [(f0 + 8, END)])

    X28_TAG = X28 + 215
    tag("2020: ~40k wpm est", (-3000, top(40) + 30, 190), root, F(0, 0.25), F(1, 0))
    tag("2022: ~70k wpm est", (-2350, top(70) + 30, 190), root, F(0, 0.45), F(1, 0))
    tag("2023: ~120k wpm est", (-1700, top(120) + 30, 190), root, F(0, 0.65), F(2, 0))
    tag("end-2025: 265k capacity est", (-900, top(265) + 30, 190), root, F(1, 0.25), F(2, 0))
    tag("only ~240k came out (Omdia)", (-900, top(240), 230), root, F(1, 0.40), F(2, 0))
    tag("Sep 2026: 320k wpm", (-150, top(320) + 30, 190), root, F(1, 0.60), F(2, 0))
    tag("2027: 420k fcst", (1450, top(420) + 30, 190), root, F(2, 0.30))
    tag("2028: 500k (SemiAnalysis)", (X28_TAG, top(500), 0), root, F(2, 0.50))
    tag("2028: 550k (Nomura)", (X28_TAG, top(550), 0), root, F(2, 0.58))
    tag("2028: 600k+ (Reuters)", (X28_TAG, top(600), 0), root, F(2, 0.66))

    camera(root, [((-2300, 250, 0), 2300, 0.0, 0.16), ((-1300, 550, 0), 3500, 0.0, 0.16),
                  ((-80, 850, 0), 4700, 0.0, 0.14)])
    finish_mem("capacity")


# ---- share: CXMT's slice of the DRAM market, 3% to 10% ---------------------------------
# Counterpoint revenue share (page series): 2025Q1 3, Q2 4, Q3 5, Q4 8, 2026Q1 8, Q2 10, Q3 9.
# 2026Q3 split (Counterpoint): Samsung 38, SK hynix 29, Micron 21, CXMT 9.

def build_share():
    m, root = begin("share")
    rc = (-1900.0, 820.0)
    R0, R1 = 430.0, 800.0
    floor(root, m, -2900, 3000, -400, 400)
    base = grp("ring_rest", root, 0, F(2, 0.45))
    wedge("ring_rest_m", rc, R0, R1, 0, 1, -160, 0, m["other"], base)

    q = [(3, 0, 0.08), (4, 0, 0.50), (5, 1, 0.08), (8, 1, 0.38), (8, 1, 0.68), (10, 2, 0.08), (9, 2, 0.30)]
    for i, (v, b, u) in enumerate(q):
        f0 = F(b, u)
        f1 = F(q[i + 1][1], q[i + 1][2]) if i + 1 < len(q) else F(2, 0.45)
        g = grp(f"cx_wedge{i}", root, f0, f1)
        wedge(f"cx_wedge{i}_m", rc, R0 - 20, R1 + 40, 0, v / 100, -170, 60, m["brand"], g)
        bar(root, f"q{i}", 150 + i * 420, 0, 260, 260, v * 140, m["brand"], f0, f0 + 30)
    # 2026Q3 split by maker
    split = [(38, "ssg"), (29, "skh"), (21, "mu"), (9, "brand"), (3, "other")]
    u = 0.0
    for name, (v, mk) in zip(("ssg", "skh", "mu", "cxmt", "rest"), split):
        g = grp(f"split_{name}", root, F(2, 0.45))
        lift = 60 if name == "cxmt" else 0
        wedge(f"split_{name}_m", rc, R0, R1 + (60 if name == "cxmt" else 0), u + 0.004, u + v / 100 - 0.004, -160,
              lift, m[mk], g)
        u += v / 100

    tag("2025Q1: CXMT 3% of DRAM sales", ring_point(rc, R1 + 40, 0.015) + (60,), root, F(0, 0.15), F(0, 0.5))
    tag("2025Q1: 3%", (150, 420, 130), root, F(0, 0.20), F(1, 0))
    tag("2025Q2: 4%", (570, 560, 130), root, F(0, 0.60), F(1, 0))
    tag("2025Q4: 8%", (1410, 1120, 130), root, F(1, 0.45), F(2, 0))
    tag("2026Q1: 8% (TrendForce 7.6%)", (1830, 1120, 130), root, F(1, 0.75), F(2, 0))
    tag("2026Q2: 10% peak", (2250, 1400, 130), root, F(2, 0.15))
    tag("2026Q3: Samsung 38%", ring_point(rc, R1, 0.19) + (20,), root, F(2, 0.50))
    tag("SK hynix 29%, Micron 21%", ring_point(rc, R1, 0.60) + (20,), root, F(2, 0.55))
    tag("CXMT 9%: #4 in DRAM", ring_point(rc, R1 + 60, 0.925) + (80,), root, F(2, 0.60))

    camera(root, [((0, 860, 0), 4500, 0.0, 0.10)] * 3)
    finish_mem("share")


# ---- products: G4 yield, quadruple patterning, G5 dies per wafer ------------------------
# ddr5_yield 80% (2025-04, Digitimes) -> 90% est (2026-08, TrendForce); G5 half pitch 11.95 nm,
# quadruple patterning, no EUV; dies per wafer +50% (TechNode, 2026-09-20); 24Gb LPDDR5X die;
# LPDDR5X 10,667 MT/s (Wccftech).

def die_grid(parent, m, name, cx, cy, R, pitch, mat_key, z1=14.0, draw=True):
    cells = []
    n = int(R / pitch) + 1
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = cx + i * pitch, cy + j * pitch
            h = pitch * 0.42
            corners = [(x + sx * h, y + sy * h) for sx in (-1, 1) for sy in (-1, 1)]
            if all(math.hypot(a - cx, b - cy) < R - 20 for a, b in corners):
                cells.append((x, y))
    if draw:
        for k, (x, y) in enumerate(cells):
            h = pitch * 0.42
            box(f"{name}{k}", (x - h, y - h, 0), (x + h, y + h, z1), m[mat_key], parent)
    return cells


def wafer_disc(parent, m, name, cx, cy, R):
    prism(name, circle_pts(cx, cy, R), -40, 0, m["wafer"], parent)


def build_products():
    m, root = begin("products")
    g4c, g5c, R = (-1400.0, 850.0), (1400.0, 850.0), 820.0
    rng = random.Random(7)
    w4 = grp("g4", root)
    show(w4, [(0, F(1, 0)), (F(2, 0), END)])
    wafer_disc(w4, m, "g4_wafer", *g4c, R)
    cells = die_grid(w4, m, "g4_die", *g4c, R, 130, "die")
    rng.shuffle(cells)
    n10 = round(len(cells) * 0.10)
    for name, sub, iv in (("bad_a", cells[:n10], [(F(0, 0.08), F(1, 0)), (F(2, 0), END)]),
                          ("bad_b", cells[n10:2 * n10], [(F(0, 0.08), F(0, 0.55))])):
        g = grp(name, root)
        for k, (x, y) in enumerate(sub):
            box(f"{name}{k}", (x - 52, y - 52, 14), (x + 52, y + 52, 24), m["bad"], g)
        show(g, iv)
    # beat 0: the good-die meter, 80% then 90% of a 100% track
    meter = grp("meter", root, 0, F(1, 0))
    L, my = 1700.0, 850.0
    box("meter_track", (-350, my - 70, -60), (-350 + L, my + 70, 0), m["fcst"], meter)
    fill = pivot("meter_fill", (-350, my, 0), meter)
    box("meter_fill_m", (0, -60, -50), (L, 60, 10), m["good"], fill)
    scale_keys(fill, [(0, (OFF,) * 3), (F(0, 0.08), (OFF, 1, 1)), (F(0, 0.30), (0.80, 1, 1)), (F(0, 0.58), (0.80, 1, 1)),
                      (F(0, 0.75), (0.90, 1, 1)), (END, (0.90, 1, 1))], until=F(0, 0.08))

    # beat 1: quadruple patterning, four passes of lines each a quarter pitch over
    qp = grp("qp", root, F(1, 0), F(2, 0))
    box("qp_si", (-1700, 420, -60), (1700, 1300, 0), m["si"], qp)
    for p in range(4):
        g = grp(f"qp_pass{p}", qp, F(1, 0.08 + 0.15 * p))
        for k in range(9):
            x = -1600 + (k * 4 + p) * 92
            box(f"qp{p}_{k}", (x, 470, 0), (x + 50, 1250, 30 + 8 * p), m[f"pass{p}"], g)

    w5 = grp("g5", root, F(2, 0.05))
    wafer_disc(w5, m, "g5_wafer", *g5c, R)
    die_grid(w5, m, "g5_die", *g5c, R, 130 / math.sqrt(1.5), "die")

    tag("G4 DDR5 yield ~80% (Apr 2025)", (-350 + 0.8 * L, my + 60, 10), root, F(0, 0.30), F(0, 0.58))
    tag("~90% by Aug 2026 est", (-350 + 0.9 * L, my + 60, 10), root, F(0, 0.75), F(1, 0))
    tag("G4: 17 nm class est", (-1400, 1670, 0), root, F(0, 0.15), F(1, 0))
    tag("red dies = failed", (cells[0][0], cells[0][1], 24), root, F(0, 0.15), F(0, 0.55))
    tag("litho pass 1 of 4", (-1600, 1250, 30), root, F(1, 0.12), F(1, 0.55))
    tag("4 passes, no EUV", (-1600 + 3 * 92, 1250, 54), root, F(1, 0.60), F(2, 0))
    tag("G5: 11.95 nm half pitch", (1500, 470, 40), root, F(1, 0.70), F(2, 0))
    tag("G5: +50% dies per wafer", (1400, 1670, 0), root, F(2, 0.30))
    tag("24Gb LPDDR5X die (G5)", (2150, 600, 14), root, F(2, 0.45))
    tag("G4 DDR5 ~90% yield est", (-1400, 1670, 0), root, F(2, 0.55))

    camera(root, [((-100, 850, 0), 3700, 0.0, 0.04), ((0, 860, 0), 2600, 0.0, 0.04), ((0, 850, 0), 3900, 0.0, 0.04)])
    finish_mem("products")


# ---- hbm: why the yields are the problem ----------------------------------------------
# HBM3 8-high ~25% in 2026Q2: front-end ~35% x back-end ~70% (SemiAnalysis); HBM3E 20-30%
# (Reuters), vs ~70% at SK hynix on the same tech (source notes); small volume from Aug 2026,
# full mass production 2027 est.

def mini_stack(parent, name, x, z, m, dies=8, w=140.0, t=22.0, gap=7.0, base_mat="base"):
    g = empty(name, parent)
    box(f"{name}_b", (x - w / 2 - 8, 0, z - w / 2 - 8), (x + w / 2 + 8, 26, z + w / 2 + 8), m[base_mat], g)
    for k in range(dies):
        y = 26 + gap + k * (t + gap)
        box(f"{name}_d{k}", (x - w / 2, y, z - w / 2), (x + w / 2, y + t, z + w / 2), m["dram"], g)
    return g, 26 + dies * (t + gap)


def build_hbm():
    m, root = begin("hbm")
    rng = random.Random(3)
    # beat 0: front-end, the wafer at x = -6000; bad dies leave for the scrap bin
    b0 = grp("b0", root, F(0, 0), F(1, 0))
    wc = (-6000.0, 850.0)
    wafer_disc(b0, m, "fe_wafer", *wc, 800)
    cells = die_grid(b0, m, "fe_die", *wc, 800, 150, "die", draw=False)
    rng.shuffle(cells)
    ngood = round(len(cells) * 0.35)
    good, bad = cells[:ngood], cells[ngood:]
    gg = grp("fe_good", b0)
    for k, (x, y) in enumerate(good):
        box(f"fe_g{k}", (x - 60, y - 60, 0), (x + 60, y + 60, 24), m["good"], gg)
    gb = grp("fe_bad", b0)
    gm = pivot("fe_bad_move", (wc[0], wc[1], 0), gb)
    for k, (x, y) in enumerate(bad):
        box(f"fe_b{k}", (x - 60 - wc[0], y - 60 - wc[1], 0), (x + 60 - wc[0], y + 60 - wc[1], 24), m["bad"], gm)
    key(gm, F(0, 0.45), "location", P(wc[0], wc[1], 0))
    key(gm, F(0, 0.75), "location", P(-3700, 330, 0))
    key(gm, F(0, 0.45), "scale", (1, 1, 1))
    key(gm, F(0, 0.75), "scale", (0.3, 0.3, 0.3))
    binm = grp("bin", b0)
    box("bin_m", (-4050, 0, -150), (-3350, 120, 150), m["grey"], binm)
    floor(b0, m, -7200, -3000, -300, 300)

    # beat 1: stacking known-good dies into 10 eight-high stacks; 3 fail bonding
    b1 = grp("b1", root, F(1, 0), F(2, 0))
    floor(b1, m, -2300, 2300, -300, 300)
    W, T, G = 260.0, 40.0, 12.0
    failed = {2, 5, 8}
    for s in range(10):
        x = -2000 + s * 444
        box(f"st{s}_base", (x - W / 2 - 14, 0, -W / 2 - 14), (x + W / 2 + 14, 50, W / 2 + 14), m["base"], b1)
        for k in range(8):
            d = grp(f"st{s}_d{k}", b1)
            y = 50 + G + k * (T + G)
            box(f"st{s}_dm{k}", (x - W / 2, y, -W / 2), (x + W / 2, y + T, W / 2), m["dram"], d)
            f0 = F(1, 0.04 + 0.05 * k + 0.004 * s)
            key(d, 0, "location", P(0, 900, 0))
            key(d, f0, "location", P(0, 900, 0))
            key(d, f0 + 10, "location", P(0, 0, 0))
            show(d, [(f0, END)])
        if s in failed:
            fg = grp(f"st{s}_fail", b1, F(1, 0.62))
            box(f"st{s}_failm", (x - W / 2 - 18, 40, -W / 2 - 18), (x + W / 2 + 18, 50 + 8 * (T + G) + 14, W / 2 + 18), m["bad"], fg)
    stack_top = 50 + 8 * (T + G)

    # beat 2: HBM3E, 20 stacks each: CXMT ~25% good (5), SK hynix ~70% (14)
    b2 = grp("b2", root, F(2, 0))
    floor(b2, m, 4000, 8100, -500, 200)
    for side, (x0, ngood_s, base) in enumerate(((4200.0, 5, "brand"), (6300.0, 14, "skh"))):
        order = list(range(20))
        random.Random(11 + side).shuffle(order)
        good_set = set(order[:ngood_s])
        for i in range(20):
            col, rowi = i % 10, i // 10
            x, z = x0 + col * 165, -rowi * 230
            mini_stack(b2, f"h{side}_{i}", x, z, m, base_mat=base)
            flag = grp(f"h{side}_{i}_flag", b2, F(2, 0.20 + 0.03 * col))
            box(f"h{side}_{i}_fm", (x - 72, 262, z - 72), (x + 72, 330, z + 72), m["good" if i in good_set else "bad"], flag)

    tag("HBM3 front-end yield ~35% est", (-6000, 1650, 0), root, F(0, 0.15), F(1, 0))
    tag("~65% of dies scrapped", (-3700, 120, 150), root, F(0, 0.70), F(1, 0))
    tag("8-high HBM3 stacks", (-2000, stack_top, 130), root, F(1, 0.45), F(2, 0))
    tag("bonding ~70% est: 3 of 10 fail", (-1112, stack_top + 14, 150), root, F(1, 0.66), F(2, 0))
    tag("overall ~25% (35% x 70%) est", (1996, stack_top, 130), root, F(1, 0.75), F(2, 0))
    tag("CXMT HBM3E yield ~20-30% est", (4200, 330, 0), root, F(2, 0.50))
    tag("SK hynix ~70% on same tech", (7785, 330, 0), root, F(2, 0.55))
    tag("small volume since Aug 2026", (4400, 0, 120), root, F(2, 0.65))
    tag("full volume 2027 est", (5600, 0, 120), root, F(2, 0.70))

    camera(root, [((-5200, 820, 0), 3500, 0.0, 0.05), ((0, 330, 0), 3300, 0.0, 0.12),
                  ((6050, 120, -110), 2900, 0.0, 0.45)])
    finish_mem("hbm")


# ---- ipo: money in, day one, the valuation tower ---------------------------------------
# planned raise CNY 29.5B (2026-05-28), raised 57.919B at CNY 8.66/share (6.688B shares);
# debut close CNY 49 (+465.8%); debut cap CNY 3.28T est (TrendForce); 2024 pre-money 140B.

def build_ipo():
    m, root = begin("ipo")
    # beat 0: proceeds vs plan as horizontal bars (50 mm per CNY B), around x = -6000
    b0 = grp("b0", root, 0, F(1, 0))
    kb, X0 = 50.0, -7500.0
    floor(b0, m, X0 - 200, X0 + 3200, -400, 300)
    pl = grp("plan", b0, F(0, 0.05))
    box("plan_m", (X0, 420, -200), (X0 + 29.5 * kb, 720, 0), m["ghost"], pl)
    n = 12
    wdt = 57.919 * kb / n
    for i in range(n):
        g = grp(f"brick{i}", b0)
        box(f"brick{i}_m", (X0 + i * wdt + 5, 40, -200), (X0 + (i + 1) * wdt - 5, 340, 0), m["gold"], g)
        f0 = F(0, 0.12 + 0.045 * i)
        key(g, 0, "location", P(-900, 500, 0))
        key(g, f0, "location", P(-900, 500, 0))
        key(g, f0 + 14, "location", P(0, 0, 0))
        show(g, [(f0, F(1, 0))])
    tag("planned raise CNY 29.5B", (X0 + 29.5 * kb, 720, 0), b0, F(0, 0.08), F(1, 0))
    tag("6.688B shares at CNY 8.66", (X0 + 600, 340, 0), b0, F(0, 0.40), F(1, 0))
    tag("raised CNY 57.9B: 1.96x plan", (X0 + 57.919 * kb, 340, 0), b0, F(0, 0.75), F(1, 0))

    # beat 1: listing day, offer at the open vs the close (30 mm per CNY), around x = 0
    b1 = grp("b1", root, F(1, 0), F(2, 0))
    floor(b1, m, -1900, 1900, -400, 300)
    kp = 30.0
    box("offer_m", (-1600, 0, -300), (-1000, 8.66 * kp, 0), m["grey"], b1)
    box("offer_line", (-1600, 8.66 * kp - 8, -20), (1600, 8.66 * kp + 8, 30), m["cost"], b1)
    bar(b1, "close", 1300, -150, 600, 300, 49 * kp, m["profit"], F(1, 0.35), F(1, 0.65))
    arrow = pivot("arrow", (-1000, 8.66 * kp, 0), b1)
    tube("arrow_t", (0, 0, 20), (2000, 49 * kp - 8.66 * kp, 20), 16, m["gold"], arrow, verts=10)
    scale_keys(arrow, [(0, (OFF,) * 3), (F(1, 0.35), (OFF, OFF, OFF)), (F(1, 0.65), (1, 1, 1)), (END, (1, 1, 1))], until=F(1, 0.35))
    tag("offer CNY 8.66 (2026-07-27)", (-1600, 8.66 * kp, 0), b1, F(1, 0.08), F(2, 0))
    tag("debut close CNY 49", (1000, 49 * kp, 0), b1, F(1, 0.66), F(2, 0))
    tag("+465.8% on day one", (0, 8.66 * kp + 0.5 * (49 - 8.66) * kp, 20), b1, F(1, 0.72), F(2, 0))

    # beat 2: valuation towers (0.45 mm per CNY B), around x = 6000
    b2 = grp("b2", root, F(2, 0))
    floor(b2, m, 4300, 7700, -500, 300)
    kv = 0.45
    box("pre_m", (4600, 0, -400), (5300, 140 * kv, 0), m["grey"], b2)
    bar(b2, "cap", 6900, -200, 700, 400, 3280 * kv, m["brand"], F(2, 0.15), F(2, 0.65))
    tag("2024 pre-money CNY 140B", (4600, 140 * kv, 0), b2, F(2, 0.05))
    tag("debut cap CNY 3.28T est", (6550, 3280 * kv, 0), b2, F(2, 0.66))
    tag("23.4x the 2024 valuation", (7250, 900, 0), b2, F(2, 0.75))

    camera(root, [((X0 + 1500, 380, 0), 2400, 0.05, 0.10), ((0, 740, 0), 3200, 0.05, 0.08),
                  ((6000, 760, 0), 3300, 0.05, 0.06)])
    finish_mem("ipo")


# ---- controls: the US list actions on a timeline ---------------------------------------
# page controls table: 2024-03 Entity List under consideration; 2025-01-06 DoD 1260H;
# 2026-02-13 reported removed; 2026-06 kept/reinstated; 2026-06-16 Entity List approved,
# publication delayed; 2026-08 CXMT sues DoD; 2026-09-20 G5 with quadruple patterning, no EUV.

T0, MM = -3000.0, 175.0  # x of 2024-01-01 and mm per month


def tx(y, mo, d=1):
    return T0 + ((y - 2024) * 12 + (mo - 1) + (d - 1) / 30) * MM


def build_controls():
    m, root = begin("controls")
    x_end = tx(2026, 11)
    floor(root, m, T0 - 200, x_end + 200, -300, 300)
    box("rail", (T0 - 150, 0, -40), (x_end + 150, 30, 40), m["cost"], root)
    for yr in (2024, 2025, 2026):
        box(f"tick{yr}", (tx(yr, 1) - 8, 0, -60), (tx(yr, 1) + 8, 80, 60), m["paper"], root)
    # lanes: DoD 1260H at y 900, Commerce Entity List at y 520
    box("lane_dod", (T0, 870, -170), (x_end, 880, -150), m["floor"], root)
    box("lane_bis", (T0, 490, -170), (x_end, 500, -150), m["floor"], root)

    # the cursor sweeps 2024-01 -> 2026-11 over the three beats
    cur = grp("cursor", root)
    box("cursor_m", (T0 - 5, 0, -10), (T0 + 5, 1150, 10), m["cursor"], cur)
    sweep = [(0, tx(2024, 1)), (F(1, 0) - 1, tx(2025, 6)), (F(2, 0) - 1, tx(2026, 7)), (END, x_end)]
    for f, x in sweep:
        key(cur, f, "location", P(x - T0, 0, 0), linear=True)

    def when(x):
        for (fa, xa), (fb, xb) in zip(sweep, sweep[1:]):
            if xa <= x <= xb:
                return round(fa + (fb - fa) * (x - xa) / (xb - xa))
        return END

    def ribbon(name, xa, xb, y, mk, thick=90):
        g = pivot(name, (xa, y, 0), root)
        box(f"{name}_m", (0, -thick / 2, -110), (xb - xa, thick / 2, 0), m[mk], g)
        fa, fb = when(xa), when(xb)
        scale_keys(g, [(0, (OFF,) * 3), (fa, (OFF, 1, 1)), (fb, (1, 1, 1)), (END, (1, 1, 1))], until=fa)

    def event(name, x, h, mk, y0=30):
        f = when(x)
        g = grp(name, root, f)
        box(f"{name}_pole", (x - 10, y0, -20), (x + 10, h, 20), m[mk], g)
        box(f"{name}_cap", (x - 45, h, -45), (x + 45, h + 60, 45), m[mk], g)
        return f

    # DoD 1260H: listed 2025-01-06 .. 2026-02-13, again from 2026-06
    ribbon("dod1", tx(2025, 1, 6), tx(2026, 2, 13), 900, "loss")
    ribbon("dod2", tx(2026, 6, 1), x_end, 900, "loss")
    # Commerce: considered from 2024-03 (ghost), approved but unpublished from 2026-06-16
    ribbon("bis1", tx(2024, 3), tx(2026, 6, 16), 520, "amber_ghost", 60)
    ribbon("bis2", tx(2026, 6, 16), x_end, 520, "amber", 60)

    e1 = event("e_bis_consider", tx(2024, 3), 520, "amber")
    e2 = event("e_dod_add", tx(2025, 1, 6), 900, "loss")
    e3 = event("e_dod_off", tx(2026, 2, 13), 1000, "grey")
    e4 = event("e_dod_back", tx(2026, 6, 1), 900, "loss")
    e5 = event("e_bis_ok", tx(2026, 6, 16), 520, "amber")
    e6 = event("e_court", tx(2026, 8), 300, "court")
    e7 = event("e_g5", tx(2026, 9, 20), 200, "good")

    tag("2024-03 Entity List mulled", (tx(2024, 3), 580, 45), root, e1 + 6, F(1, 0.2))
    tag("2025-01-06 on DoD 1260H list", (tx(2025, 1, 6), 960, 45), root, e2 + 6, F(1, 0.70))
    tag("red = on DoD 1260H list", (T0 + 60, 900, 0), root, F(0, 0.05), F(0, 0.75))
    tag("amber = Commerce Entity List", (T0 + 60, 520, 0), root, F(0, 0.05), F(0, 0.75))
    tag("2026-02 off 1260H (reported)", (tx(2026, 2, 13), 1060, 45), root, e3 + 6, F(2, 0))
    tag("2026-06 back on 1260H", (tx(2026, 6, 1), 960, 45), root, e4 + 6, F(2, 0.5))
    tag("Entity List approved, held", (tx(2026, 6, 16), 520, 45), root, e5 + 6)
    tag("2026-08 CXMT sues DoD", (tx(2026, 8), 360, 45), root, e6 + 4)
    tag("2026-09 G5 at 11.95nm, no EUV", (tx(2026, 9, 20), 260, 45), root, e7 + 4)

    camera(root, [((-1300, 560, 0), 3300, 0.0, 0.12), ((800, 560, 0), 3300, 0.0, 0.12),
                  ((1900, 560, 0), 2600, 0.0, 0.12)])
    finish_mem("controls")


# ---- sources: stacks of documents, and numbers that disagree ---------------------------
# page sources tab: 121 sourced numbers, 36 source pages, 26 conflicting values; rows per
# source (top 8); 2025Q4 DRAM share: Omdia 4.7, prospectus-cited 7.67, Counterpoint 8,
# TrendForce projection 12; 2024 revenue 24.178 (prospectus) vs 15.44 in press (= 2025H1).

def build_sources():
    m, root = begin("sources")
    floor(root, m, -2700, 2700, -400, 400)
    # beat 0: paper stacks, one sheet per sourced row
    b0 = grp("b0", root, 0, F(1, 0))
    rows = [18, 7, 7, 7, 6, 6, 4, 4]
    for s, n in enumerate(rows):
        x = -2200 + s * 620
        g = pivot(f"pile{s}", (x, 0, 0), b0)
        for k in range(n):
            jx = ((k * 37) % 9 - 4) * 4
            box(f"pile{s}_{k}", (jx - 210, k * 52, -150), (jx + 210, k * 52 + 40, 150), m["paper"], g)
        f0 = F(0, 0.05 + 0.05 * s)
        scale_keys(g, [(0, (OFF,) * 3), (f0, (1, 1, OFF)), (f0 + 40, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    tag("prospectus (unofficial): 18", (-2200, 18 * 52, 150), b0, F(0, 0.30), F(1, 0))
    tag("Counterpoint, TechNode: 7 each", (-1580, 7 * 52, 150), b0, F(0, 0.45), F(1, 0))
    tag("121 numbers, 36 sources", (1600, 260, 150), b0, F(0, 0.60), F(1, 0))

    # beat 1: four answers to one question (CXMT share, 2025Q4)
    b1 = grp("b1", root, F(1, 0), F(2, 0))
    k = 130.0
    ans = [(4.7, "rev"), (7.67, "mu"), (8.0, "brand"), (12.0, "ghost_gold")]
    for i, (v, mk) in enumerate(ans):
        bar(b1, f"ans{i}", -1500 + i * 1000, 0, 520, 400, v * k, m[mk], F(1, 0.08 + 0.08 * i), F(1, 0.08 + 0.08 * i) + 36)
    tag("2025Q4 share: Omdia 4.7%", (-1760, 4.7 * k, 200), b1, F(1, 0.30), F(2, 0))
    tag("prospectus cite 7.67%", (-760, 7.67 * k, 200), b1, F(1, 0.40), F(2, 0))
    tag("Counterpoint 8%", (240, 8 * k, 200), b1, F(1, 0.50), F(2, 0))
    tag("TrendForce 12% (projection)", (1240, 12 * k, 200), b1, F(1, 0.60), F(2, 0))

    # beat 2: a press error traced back: 2024 revenue 24.2B vs 15.44B (really 2025H1)
    b2 = grp("b2", root, F(2, 0))
    kr = 55.0
    bar(b2, "r2024", -900, 0, 700, 400, 24.178 * kr, m["rev"], F(2, 0.05), F(2, 0.20))
    bar(b2, "press", 900, 0, 700, 400, 15.438 * kr, m["loss"], F(2, 0.20), F(2, 0.35))
    fix = grp("fix", b2, F(2, 0.55))
    box("fix_m", (520, 15.438 * kr + 10, -220), (1280, 15.438 * kr + 50, 220), m["good"], fix)
    tag("2024 revenue CNY 24.2B (filing)", (-1250, 24.178 * kr, 200), b2, F(2, 0.25))
    tag("press: CNY 15.44B for 2024", (550, 15.438 * kr, 200), b2, F(2, 0.40))
    tag("that is 2025H1 revenue", (1250, 15.438 * kr + 50, 220), b2, F(2, 0.58))
    tag("26 values conflict on this page", (0, 120, 220), b2, F(2, 0.70))

    camera(root, [((0, 560, 0), 3900, 0.10, 0.14), ((0, 700, 0), 3900, 0.08, 0.12), ((0, 650, 0), 3500, 0.08, 0.12)])
    finish_mem("sources")


# ---- snapshot: three fabs, the profit turn, fourth place -------------------------------
# 300k wpm in three 12-inch fabs, 2 Hefei + 1 Beijing (Reuters, 2026-08-03); 2025 revenue 61.799,
# 2026Q1 revenue 50.8 / net 24.8 (CNY B); Counterpoint 2026Q3 share 38 / 29 / 21 / 9.

def fab(parent, m, name, x, w=520.0, d=420.0, h=330.0):
    box(f"{name}_body", (x - w / 2, 0, -d), (x + w / 2, h, 0), m["fab"], parent)
    box(f"{name}_roof", (x - w / 2 - 20, h, -d - 20), (x + w / 2 + 20, h + 40, 20), m["roof"], parent)
    for i in range(3):
        bx = x - w / 2 + 70 + i * 120
        box(f"{name}_vent{i}", (bx, h + 40, -d / 2 - 40), (bx + 60, h + 120, -d / 2 + 40), m["roof"], parent)


def build_snapshot():
    m, root = begin("snapshot")
    floor(root, m, -3500, 3500, -600, 400)
    # beat 0: three fabs, wafers flowing out
    for i, x in enumerate((-3000, -2350, -1700)):
        g = grp(f"fab{i}", root, F(0, 0.05 + 0.12 * i))
        fab(g, m, f"fab{i}", x)
    for i in range(14):
        e = grp(f"wf{i}", root)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=110, depth=14, location=P(-2350, 60, 120))
        o = bpy.context.object
        o.name = f"wf{i}_m"
        o.data.materials.append(m["wafer"])
        o.parent = e
        f0 = F(0, 0.35) + i * 22
        key(e, f0, "location", P(0, 0, 0), linear=True)
        key(e, f0 + 70, "location", P(1950, 0, 0), linear=True)
        show(e, [(f0, f0 + 70)])
    tag("2 fabs in Hefei, 1 in Beijing", (-2350, 500, 0), root, F(0, 0.35), F(1, 0))
    tag("~300k wafers/month est", (-1200, 60, 60), root, F(0, 0.55), F(1, 0))

    # beat 1: 2025 full-year revenue vs one quarter of 2026 (25 mm per CNY B)
    k = 25.0
    bar(root, "rev25", -400, 0, 380, 380, 61.799 * k, m["rev"], F(1, 0.05), F(1, 0.25))
    bar(root, "rev26", 150, 0, 380, 380, 50.8 * k, m["rev"], F(1, 0.30), F(1, 0.50))
    bar(root, "net26", 600, 0, 380, 380, 24.8 * k, m["profit"], F(1, 0.50), F(1, 0.70))
    tag("all of 2025: CNY 61.8B", (-590, 61.799 * k, 190), root, F(1, 0.25), F(2, 0))
    tag("2026Q1 alone: CNY 50.8B", (-40, 50.8 * k, 190), root, F(1, 0.50), F(2, 0))
    tag("2026Q1 profit CNY 24.8B", (790, 24.8 * k, 190), root, F(1, 0.72), F(2, 0))

    # beat 2: the DRAM revenue ring, Counterpoint 2026Q3
    rc, R0, R1 = (2300.0, 800.0), 380.0, 720.0
    u = 0.0
    for name, v, mk in (("ssg", 38, "ssg"), ("skh", 29, "skh"), ("mu", 21, "mu"), ("cxmt", 9, "brand"), ("rest", 3, "other")):
        g = grp(f"ring_{name}", root, F(2, 0.05))
        big = name == "cxmt"
        wedge(f"ring_{name}_m", rc, R0, R1 + (70 if big else 0), u + 0.004, u + v / 100 - 0.004, -150, 70 if big else 0, m[mk], g)
        u += v / 100
    tag("Samsung 38%", ring_point(rc, R1, 0.19) + (20,), root, F(2, 0.15))
    tag("CXMT 9%: #4 in DRAM (Q3 2026)", ring_point(rc, R1 + 70, 0.925) + (90,), root, F(2, 0.25))
    tag("SK hynix 29%, Micron 21%", ring_point(rc, R1, 0.60) + (20,), root, F(2, 0.30))

    camera(root, [((-1600, 330, 0), 2400, 0.04, 0.18), ((-1000, 750, 0), 3900, 0.06, 0.12),
                  ((300, 800, 0), 5300, 0.06, 0.12)])
    finish_mem("snapshot")


BUILDERS = {
    "snapshot": build_snapshot,
    "revenue": build_revenue,
    "margins": build_margins,
    "capacity": build_capacity,
    "share": build_share,
    "products": build_products,
    "hbm": build_hbm,
    "ipo": build_ipo,
    "controls": build_controls,
    "sources": build_sources,
}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(BUILDERS)
    for t in which:
        BUILDERS[t]()
