"""SK hynix memory page: one purpose-built scene per tab, authored in Blender for pbr3d.

Run from the repo root (all tabs, or one):

    blender -b --factory-startup --python tools/pbr3d/blender/mem_sk_hynix.py [-- <tab id>]

Each tab writes tools/pbr3d/assets/mem/sk_hynix_<tab>.glb, which py/derive/memory_page.py picks
up as the tab's picture. Every scene is 3 beats of 8 s (frames 0..576) framed for a wide ~3:1
slot. Tags are `label:<text>` empties; at most 4 show at once.

Every number drawn (bar heights, stack counts, tags) comes from data/memory_facts/*.jsonl, the
OpenDART rows in data/dart/facts.parquet, or the cached page (memory_page.py 000660.KS --json):

  snapshot  FY2025 revenue (four quarters) vs 2026Q1-Q3 quarters; 2026Q3 alone tops FY2025, and
            83.3T of its 104.6T is operating income
  revenue   19 quarters of OpenDART revenue: the fall to the 2023Q1 trough, the climb, the jump
  mix       DRAM / NAND split FY2023-FY2025 and 1Q25 / 1Q26 (424B4), HBM slice 1Q25 (est)
  hbm       stacks by generation on a timeline (HBM2E, HBM3, HBM3E 8/12/16-high, HBM4 12-high)
            with SK hynix's HBM share ring
  margins   2023 losses (costs above revenue), wafers diverted to HBM, then revenue far above
            costs: 79.7% operating margin in 2026Q3
  pricing   DRAM ASP QoQ vs DRAM bit growth QoQ: the 2026 spike is price, not volume
  share     HBM share towers for SK hynix, Samsung, Micron trading places 2022 / 2Q25 / 2Q26
  fabs      a world map with each SK hynix fab and packaging site pinned; Enter flies to it (fab_map.py)
  tech      TSVs, 40% thinner dies + MR-MUF for 12-high, HBM4's 2,048 I/O bus
  listing   the July 2026 Nasdaq ADR: $149 x 177.9M ADS -> $26.2B -> Yongin Fab 1 + P&T7
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
import fab_map  # noqa: E402
from sand_overview import OFF, F, P, _constant_until, ball, box, disc, empty, fly, key, label, mat, pivot, rel, show, tube  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import hbm_kit as H  # noqa: E402

SLUG = "sk_hynix"
TABS = ("snapshot", "revenue", "mix", "hbm", "margins", "pricing", "share", "fabs", "tech", "listing")
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets", "mem"))
PRIVATE = "/private/tmp/claude-501/-Users-jacksonfaulkner-code-github-repos-finlarp/1f3cac96-b488-4686-95c8-8cd0f983bf75/scratchpad/sk_hynix_private"
END = F(3, 0)


def beat(i, u0=0.0, u1=1.0):
    return [(F(i, u0), F(i, u1) if u1 < 1.0 else F(i + 1, 0))]


# ---- data (all from the sources above) ------------------------------------------------------

# OpenDART quarterly revenue / operating income, KRW trillion; 2026Q3 from the earnings release
# (Kyunghyang Shinmun 2026-10-28), as on the cached page.
QUARTERS = ["2022Q1", "2022Q2", "2022Q3", "2022Q4", "2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1",
            "2024Q2", "2024Q3", "2024Q4", "2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2", "2026Q3"]
REV = [12.1557, 13.811, 10.9829, 7.672, 5.0881, 7.3059, 9.0662, 11.3055, 12.4296,
       16.4233, 17.5731, 19.767, 17.6391, 22.232, 24.4489, 32.8267, 52.5763, 79.3187, 104.6155]
OI = [2.8596, 4.1926, 1.6556, -1.8984, -3.4023, -2.8821, -1.792, 0.346, 2.886,
      5.4685, 7.03, 8.0828, 7.4405, 9.2129, 11.3834, 19.1696, 37.6103, 60.5426, 83.3338]
Q = {q: (r, o) for q, r, o in zip(QUARTERS, REV, OI)}

# SK hynix DRAM ASP and bit shipments QoQ, % (424B4 table / earnings calls)
PRICE_Q = ["2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1", "2024Q2", "2024Q3", "2024Q4",
           "2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2", "2026Q3"]
ASP = [-18, 8, 10, 18, 20, 15, 15, 10, 0, 2, 5, 25, 65, 30, 28]
BITS = [-20, 35, 20, 2, -15, 22, -1, 5, -8, 25, 8, 2, 0, 8, 10]


# ---- materials ---------------------------------------------------------------------------------


def mats(m):
    m = H.mats(m)
    m["rev"] = mat("skh_rev", (0.25, 0.55, 0.95), metal=0.2, rough=0.4)
    m["rev_dim"] = mat("skh_rev_dim", (0.30, 0.38, 0.52), metal=0.2, rough=0.6)
    m["cost"] = mat("skh_cost", (0.42, 0.44, 0.50), metal=0.1, rough=0.7)
    m["loss"] = mat("skh_loss", (0.95, 0.18, 0.15), emit=(0.95, 0.15, 0.10), strength=0.6, rough=0.5)
    m["profit"] = mat("skh_profit", (1.0, 0.68, 0.12), emit=(1.0, 0.62, 0.10), strength=0.45, metal=0.3, rough=0.35)
    m["trough"] = mat("skh_trough", (0.85, 0.25, 0.22), rough=0.5)
    m["climb"] = mat("skh_climb", (0.20, 0.70, 0.75), metal=0.2, rough=0.45)
    m["jump"] = mat("skh_jump", (1.0, 0.66, 0.15), emit=(1.0, 0.6, 0.12), strength=0.4, metal=0.3, rough=0.35)
    m["era22"] = mat("skh_era22", (0.40, 0.48, 0.62), metal=0.2, rough=0.55)
    m["dram_rev"] = mat("skh_dram", (0.25, 0.55, 0.95), metal=0.2, rough=0.4)
    m["nand_rev"] = mat("skh_nand", (0.30, 0.78, 0.45), metal=0.1, rough=0.5)
    m["other_rev"] = mat("skh_other", (0.55, 0.55, 0.60), rough=0.7)
    m["hbm_slice"] = mat("skh_hbm_slice", (1.0, 0.55, 0.15), emit=(1.0, 0.5, 0.12), strength=0.6, rough=0.4)
    m["floor"] = mat("skh_floor", (0.13, 0.14, 0.17), rough=0.9)
    m["rail"] = mat("skh_rail", (0.55, 0.60, 0.70), metal=0.5, rough=0.4)
    m["line"] = mat("skh_line", (1.0, 0.85, 0.40), emit=(1.0, 0.82, 0.35), strength=0.9)
    m["ghost"] = mat("skh_ghost", (0.60, 0.72, 0.95), rough=0.3, alpha=0.22)
    m["ghost_gold"] = mat("skh_ghost_gold", (1.0, 0.8, 0.4), rough=0.3, alpha=0.25)
    m["skh"] = mat("skh_brand", (0.98, 0.42, 0.14), emit=(0.98, 0.38, 0.10), strength=0.8, rough=0.4)
    m["ssg"] = mat("skh_ssg", (0.22, 0.42, 0.95), metal=0.2, rough=0.4)
    m["mu"] = mat("skh_mu", (0.55, 0.62, 0.70), metal=0.4, rough=0.45)
    m["ring_bg"] = mat("skh_ring_bg", (0.22, 0.24, 0.30), rough=0.8)
    m["price"] = mat("skh_price", (1.0, 0.66, 0.15), emit=(1.0, 0.6, 0.12), strength=0.45, metal=0.3, rough=0.35)
    m["price_dn"] = mat("skh_price_dn", (0.95, 0.22, 0.18), emit=(0.95, 0.2, 0.15), strength=0.5, rough=0.5)
    m["bits"] = mat("skh_bits", (0.30, 0.65, 1.0), metal=0.2, rough=0.4)
    m["fab"] = mat("skh_fab", (0.78, 0.80, 0.84), metal=0.3, rough=0.5)
    m["fab_roof"] = mat("skh_fab_roof", (0.35, 0.38, 0.45), metal=0.4, rough=0.5)
    m["coin"] = mat("skh_coin", (1.0, 0.78, 0.30), metal=0.9, rough=0.25, emit=(1.0, 0.7, 0.25), strength=0.6)
    m["nasdaq"] = mat("skh_nasdaq", (0.15, 0.55, 0.85), metal=0.3, rough=0.4)
    m["mold"] = mat("skh_mold", (0.95, 0.65, 0.20), emit=(0.95, 0.6, 0.15), strength=0.9, rough=0.4, alpha=0.8)
    m["chip"] = mat("skh_chip", (0.20, 0.22, 0.26), metal=0.4, rough=0.4)
    m["wafer"] = mat("skh_wafer", (0.50, 0.55, 0.85), metal=0.85, rough=0.18)
    return m


# ---- helpers -----------------------------------------------------------------------------------


def grow(obj, f0, f1, full=(1.0, 1.0, 1.0)):
    """Hidden until f0, then pops to a flat plate and grows in height to `full` by f1."""
    f0 = max(1, f0)
    key(obj, 0, "scale", (OFF, OFF, OFF))
    key(obj, f0, "scale", (full[0], full[1], OFF))
    key(obj, f1, "scale", full)
    _constant_until(obj, f0)  # only the hidden key pops; f0 -> f1 ramps


def bar(name, parent, x, w, y0, y1, m, d=None, z0=0.0):
    """A vertical bar from y0 to y1 at x, in a pivot at its base (scale the pivot's 3rd slot)."""
    d = d or w
    at = (x, y0, 0)
    pv = pivot(name, at, parent)
    box(f"{name}_m", rel(at, (x - w / 2, y0, z0 - d)), rel(at, (x + w / 2, y1, z0)), m, pv)
    return pv


def stacked(name, parent, x, w, parts, d=None):
    """A bar of stacked segments [(height, mat), ...] in one pivot at its base."""
    at = (x, 0, 0)
    pv = pivot(name, at, parent)
    y = 0.0
    d = d or w
    for i, (h, m) in enumerate(parts):
        if h > 0:
            box(f"{name}_s{i}", rel(at, (x - w / 2, y, -d)), rel(at, (x + w / 2, y + h, 0)), m, pv)
        y += abs(h)
    return pv


def floor(parent, m, x0, x1, z0=-700.0, z1=250.0, y=-12.0):
    box("floor", (x0, y - 20, z0), (x1, y, z1), m["floor"], parent)


def wedge_mesh(name, c, r0, r1, depth, a0, a1, m, parent, segs=6):
    """A ring sector facing the camera (+z): centre c, radii r0..r1, angles a0..a1 (radians,
    clockwise from 12 o'clock), from z = c.z - depth to c.z."""
    bm = bmesh.new()
    ring = []
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs
        sx, sy = math.sin(a), math.cos(a)
        layer = []
        for r in (r0, r1):
            for z in (0.0, -depth):
                layer.append(bm.verts.new(P(c[0] + r * sx, c[1] + r * sy, c[2] + z)))
        ring.append(layer)  # [in-front, in-back, out-front, out-back]
    for i in range(segs):
        a, b = ring[i], ring[i + 1]
        bm.faces.new((a[0], b[0], b[2], a[2]))  # front
        bm.faces.new((a[1], a[3], b[3], b[1]))  # back
        bm.faces.new((a[2], b[2], b[3], a[3]))  # outer
        bm.faces.new((a[0], a[1], b[1], b[0]))  # inner
    s, e = ring[0], ring[-1]
    bm.faces.new((s[0], s[2], s[3], s[1]))
    bm.faces.new((e[0], e[1], e[3], e[2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


def ring_fill(name, parent, c, r0, r1, depth, m, schedule, n=50):
    """A donut chart: n sectors, sector i on while the percentage (linear between the
    (frame, pct) keys of `schedule`) covers it."""
    g = empty(name, parent)

    def pct(f):
        if f <= schedule[0][0]:
            return schedule[0][1]
        for (fa, pa), (fb, pb) in zip(schedule, schedule[1:]):
            if fa <= f <= fb:
                return pa + (pb - pa) * (f - fa) / max(1, fb - fa)
        return schedule[-1][1]

    step = 2 * math.pi / n
    for i in range(n):
        e = empty(f"{name}{i}", g)
        wedge_mesh(f"{name}{i}_m", c, r0, r1, depth, i * step + 0.01, (i + 1) * step - 0.01, m, e, 3)
        thr = (i + 0.5) * 100.0 / n
        on, iv = None, []
        for f in range(0, END + 1, 2):
            vis = pct(f) >= thr and f < END
            if vis and on is None:
                on = f
            if not vis and on is not None:
                iv.append((on, f))
                on = None
        if on is not None:
            iv.append((on, END))
        show(e, iv)
    return g


def wafer_disc(name, c, parent, m, r=70.0, t=10.0):
    """A wafer standing face-on to the camera (a thin disc in the x-y plane)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=t, location=P(*c))
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (math.pi / 2 - 0.55, 0, 0.35)
    o.data.materials.append(m)
    o.parent = parent
    return o


def flyer(name, parent, maker, path, f0, f1, steps=6, hide_after=True):
    """An object built at path[0] that flies along the absolute polyline `path` from f0 to f1."""
    e = empty(name, parent)
    maker(e, path[0])
    rp = [rel(path[0], p) for p in path]
    fly(e, rp, f0, f1, steps)
    show(e, [(f0, f1 if hide_after else END)])
    return e


def finish(tab):
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(PRIVATE, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PRIVATE, f"{SLUG}_{tab}.blend"))
    glb = os.path.join(ASSETS, f"{SLUG}_{tab}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb, export_format="GLB", export_yup=True, export_animations=True,
        export_force_sampling=True, export_frame_step=1, export_cameras=False,
        export_lights=False, use_selection=False,
    )
    print("exported", glb)
    if tab == "fabs":
        fab_map.sidecar(os.path.join(ASSETS, f"{SLUG}_{tab}.sites.json"))


def kt(v):
    return f"KRW {v:.1f}T"


# ---- snapshot: one quarter now out-earns all of 2025 ---------------------------------------------


def build_snapshot(root, m):
    S = 8.5  # mm per KRW trillion
    W = 420.0
    floor(root, m, -2000, 2000)
    # FY2025: four quarters stacked (OpenDART); sums to 97.1T
    fy = ["2025Q1", "2025Q2", "2025Q3", "2025Q4"]
    fy_rev = sum(Q[q][0] for q in fy)
    fy_oi = sum(Q[q][1] for q in fy)
    xs = -1250.0
    y = 0.0
    for i, q in enumerate(fy):
        h = Q[q][0] * S
        pv = bar(f"fy25_{q}", root, xs, W, y, y + h - 6, m["rev"] if i % 2 == 0 else m["rev_dim"])
        grow(pv, F(0, 0.08 + 0.18 * i), F(0, 0.24 + 0.18 * i))
        y += h
    label(f"FY2025 revenue {kt(fy_rev)}", (xs, fy_rev * S + 10, 0), root, beat(0, 0.75) + beat(1))
    # the FY2025 level, drawn across the chart
    lv = pivot("fy_level", (xs - W / 2, fy_rev * S, 0), root)
    box("fy_level_m", rel((xs - W / 2, fy_rev * S, 0), (xs - W / 2, fy_rev * S - 5, -W)),
        rel((xs - W / 2, fy_rev * S, 0), (1450, fy_rev * S + 5, 30)), m["line"], lv)
    key(lv, 0, "scale", (OFF, OFF, OFF))
    key(lv, F(0, 0.85), "scale", (OFF, 1, 1))
    key(lv, F(1, 0.1), "scale", (1, 1, 1))
    _constant_until(lv, F(0, 0.85) + 1)

    # 2026 quarters
    qs = ["2026Q1", "2026Q2", "2026Q3"]
    for i, q in enumerate(qs):
        x = -200.0 + 650.0 * i
        h = Q[q][0] * S
        pv = bar(f"q_{q}", root, x, W, 0, h, m["rev"])
        grow(pv, F(1, 0.05 + 0.25 * i), F(1, 0.3 + 0.25 * i))
    label(f"2026Q3 alone {kt(Q['2026Q3'][0])}", (1100, Q["2026Q3"][0] * S + 10, 0), root, beat(1, 0.8))
    label(f"2026Q1 {kt(Q['2026Q1'][0])}", (-200, Q["2026Q1"][0] * S + 10, 0), root, beat(1, 0.3))

    # beat 2: operating income fills gold from the floor inside each bar
    for name, x, oi in [("fy", xs, fy_oi)] + [(q, -200.0 + 650.0 * i, Q[q][1]) for i, q in enumerate(qs)]:
        pv = bar(f"oi_{name}", root, x, W + 16, 0, oi * S, m["profit"], d=W + 16, z0=8)
        grow(pv, F(2, 0.05), F(2, 0.45))
    label(f"Op income {kt(Q['2026Q3'][1])}", (1100, Q["2026Q3"][1] * S * 0.55, 30), root, beat(2, 0.45))
    label("79.7% operating margin", (1100, Q["2026Q3"][0] * S + 10, 0), root, beat(2, 0.5))
    label(f"FY2025 op income {kt(fy_oi)}", (xs, fy_oi * S * 0.6, 30), root, beat(2, 0.5))
    pose = ((100.0, 470.0, 0.0), 2750.0, 0.12, 0.08)
    camera(root, [pose, pose, pose])


# ---- revenue: down to the trough, the climb, the jump --------------------------------------------


def build_revenue(root, m):
    S = 10.0
    DX, W = 165.0, 115.0
    n = len(QUARTERS)
    x0 = -DX * (n - 1) / 2
    floor(root, m, x0 - 300, -x0 + 300)
    groups = [(0, 5, 0), (5, 15, 1), (15, 19, 2)]
    for i, q in enumerate(QUARTERS):
        r = Q[q][0]
        if i < 4:
            mk = "era22"
        elif i < 8:
            mk = "trough"
        elif i < 15:
            mk = "climb"
        else:
            mk = "jump"
        b, k, cnt = next((g[2], i - g[0], g[1] - g[0]) for g in groups if g[0] <= i < g[1])
        u0 = 0.05 + 0.6 * k / cnt
        pv = bar(f"rev_{q}", root, x0 + DX * i, W, 0, r * S, m[mk])
        grow(pv, F(b, u0), F(b, u0 + 0.12))
    X = lambda q: x0 + DX * QUARTERS.index(q)  # noqa: E731
    T = lambda q: (X(q), Q[q][0] * S + 8, 0)  # noqa: E731
    label(f"2022Q2 {kt(Q['2022Q2'][0])}", T("2022Q2"), root, beat(0, 0.3))
    label(f"2023Q1 trough {kt(Q['2023Q1'][0])}", T("2023Q1"), root, beat(0, 0.7) + beat(1, 0.0, 0.5))
    label(f"2024Q4 {kt(Q['2024Q4'][0])}", T("2024Q4"), root, beat(1, 0.58))
    label(f"2025Q3 {kt(Q['2025Q3'][0])}", T("2025Q3"), root, beat(1, 0.75))
    label(f"2026Q3 {kt(Q['2026Q3'][0])}", T("2026Q3"), root, beat(2, 0.65))
    label("+31.9% QoQ", (X("2026Q3") - 30, Q["2026Q3"][0] * S * 0.6, 20), root, beat(2, 0.75))
    label(f"2025Q4 {kt(Q['2025Q4'][0])}", T("2025Q4"), root, beat(2, 0.2))
    label("20.6x the 2023Q1 trough", (X("2023Q1"), Q["2023Q1"][0] * S + 8, 0), root, beat(2, 0.8))
    camera(root, [
        ((x0 + DX * 3, 130.0, 0.0), 1050.0, 0.10, 0.10),
        ((x0 + DX * 9, 230.0, 0.0), 1600.0, 0.10, 0.10),
        ((150.0, 560.0, 0.0), 2550.0, 0.08, 0.07),
    ])


# ---- mix: DRAM pulls away -----------------------------------------------------------------------


def build_mix(root, m):
    S = 9.0
    W = 380.0
    floor(root, m, -2100, 2100)
    years = [  # (name, x, DRAM, NAND, other) KRW trillion, 424B4 / Futurum
        ("FY2023", -1500.0, 20.769, 9.653, 2.3),
        ("FY2024", -950.0, 44.732, 19.274, 2.2),
        ("FY2025", -400.0, 74.904, 20.69, 0.0),
        ("1Q25", 450.0, 14.037, 3.229, 0.4),
        ("1Q26", 1000.0, 40.659, 11.574, 0.343),
    ]
    when = {"FY2023": (0, 0.05), "FY2024": (0, 0.35), "FY2025": (1, 0.05), "1Q25": (2, 0.05), "1Q26": (2, 0.4)}
    for name, x, d, n, o in years:
        hbm = d * 0.44 if name == "1Q25" else 0.0  # HBM ~44% of 1Q25 DRAM revenue (Counterpoint est)
        pv = stacked(f"mix_{name}", root, x, W, [(hbm * S, m["hbm_slice"]), ((d - hbm) * S, m["dram_rev"]),
                                                 (n * S, m["nand_rev"]), (o * S, m["other_rev"])])
        b, u = when[name]
        grow(pv, F(b, u), F(b, u + 0.25))
    label("FY2023 DRAM 63.4%", (-1500, (20.769 + 9.653 + 2.3) * S + 8, 0), root, beat(0, 0.3))
    label("FY2024 DRAM 67.6%", (-950, (44.732 + 19.274 + 2.2) * S + 8, 0), root, beat(0, 0.6) + beat(1))
    label("NAND KRW 19.3T", (-950, (44.732 + 9.6) * S, 20), root, beat(0, 0.7))
    label("FY2025 DRAM KRW 74.9T, 77.1%", (-400, (74.904 + 20.69) * S + 8, 0), root, beat(1, 0.35))
    label("NAND KRW 20.7T", (-400, (74.904 + 10.3) * S, 20), root, beat(1, 0.5))
    label("1Q25 HBM ~44% of DRAM est", (450, 14.037 * 0.22 * S, 30), root, beat(2, 0.45))
    label("1Q26 DRAM KRW 40.7T, 77.3%", (1000, (40.659 + 11.574) * S + 8, 0), root, beat(2, 0.65))
    label("FY2025 DRAM 77.1%", (-400, (74.904 + 20.69) * S + 8, 0), root, beat(2))
    camera(root, [
        ((-1050.0, 380.0, 0.0), 1650.0, 0.12, 0.08),
        ((-700.0, 470.0, 0.0), 2150.0, 0.12, 0.08),
        ((200.0, 420.0, 0.0), 2250.0, 0.12, 0.08),
    ])


# ---- hbm: how SK hynix built HBM, generation by generation ----------------------------------------


def build_hbm(root, m):
    floor(root, m, -2000, 2700, z0=-500, z1=300)
    box("rail", (-1800, -10, 20), (1500, 6, 60), m["rail"], root)
    gens = [  # (name, x, dies, beat, u)
        ("hbm2e", -1500.0, 8, 0, 0.05),
        ("hbm3", -1020.0, 8, 0, 0.45),
        ("hbm3e8", -540.0, 8, 1, 0.02),
        ("hbm3e12", -60.0, 12, 1, 0.30),
        ("hbm3e16", 420.0, 16, 1, 0.58),
        ("hbm4", 960.0, 12, 2, 0.02),
    ]
    tops = {}
    for name, x, n, b, u in gens:
        s = H.stack(root, m, x, n, name, tsv=(name == "hbm4"))
        f_base = F(b, u)
        show(s.base, [(f_base, END)])  # the base die pops in, then the dies drop onto it
        per = round(0.22 * 192 / n)
        for k, d in enumerate(s.dies):
            fa = f_base + 6 + per * k
            fb = fa + per
            key(d, 0, "location", P(0, 700, 0))
            key(d, fa, "location", P(0, 700, 0))
            key(d, fb, "location", P(0, 0, 0))
            _constant_until(d, fa + 1)
            show(d, [(fa, END)])  # scale switch; location is a separate channel
        box(f"{name}_tick", (x - 8, 6, 20), (x + 8, 40, 60), m["line"], root)
        tops[name] = H.die_top(n - 1)
    # HBM4 feeds a GPU over a wide bus
    g = empty("gpu_g", root)
    box("gpu_m", (1250, 0, -170), (1560, 240, 0), m["gpu"], g)
    show(g, [(F(2, 0.25), END)])
    for j in range(5):
        y = 22 + 9 * j
        tb = empty(f"bus{j}", root)
        tube(f"bus{j}_m", (1150, y, 4 + 3 * j), (1250, y, 4 + 3 * j), 3.5, m["data"], tb, verts=6)
        show(tb, [(F(2, 0.3), END)])
    # SK hynix HBM share ring (TrendForce 2022 50%, Counterpoint 1Q25 70%, 2Q26 50%)
    rc = (2150.0, 560.0, -60.0)
    wedge_mesh("ring_bg", rc, 230, 330, 40, 0.0, 2 * math.pi - 0.001, m["ring_bg"], root, 48)
    sched = [(0, 0), (F(0, 0.6), 0), (F(0, 0.85), 50), (F(1, 0.75), 50), (F(1, 0.95), 70),
             (F(2, 0.45), 70), (F(2, 0.7), 50), (END, 50)]
    ring_fill("share", root, (rc[0], rc[1], rc[2] + 6), 232, 328, 40, m["skh"], sched)

    T = lambda name, x: (x, tops[name] + 15, 0)  # noqa: E731
    RT = (2150 - 330, 560, 0)
    label("HBM2E 8-high", T("hbm2e", -1500), root, beat(0, 0.3))
    label("HBM3: only maker in 2023", T("hbm3", -1020), root, beat(0, 0.65))
    label("SK hynix HBM share 50% (2022)", RT, root, beat(0, 0.85) + beat(1, 0.0, 0.7))
    label("HBM3E 8-high Mar 2024 1.18TB/s", T("hbm3e8", -540), root, beat(1, 0.2))
    label("12-high Sep 2024, 36 GB", T("hbm3e12", -60), root, beat(1, 0.48))
    label("16-high Nov 2024, 48 GB", T("hbm3e16", 420), root, beat(1, 0.78))
    label("70% share 1Q25 (Counterpoint)", RT, root, beat(1, 0.95) + beat(2, 0.0, 0.5))
    label("HBM4 12-high, 2Q26 volume", T("hbm4", 960), root, beat(2, 0.25))
    label("2,048 I/O, 10 Gbps", (1400, 240 + 10, 0), root, beat(2, 0.4))
    label("50% share 2Q26 (Counterpoint)", RT, root, beat(2, 0.72))
    pose = ((420.0, 520.0, 0.0), 2900.0, 0.10, 0.08)
    camera(root, [pose, pose, pose])


# ---- margins: why the margins exist now --------------------------------------------------------


def quarter_bar(name, parent, x, w, rev, oi, S, mm):
    """Revenue vs operating cost for one quarter (cost = revenue - operating income): grey up to
    the lower of the two, red above revenue when costs exceed it (loss), gold above costs when
    revenue exceeds them (profit)."""
    cost = rev - oi
    lo = min(rev, cost)
    parts = [(lo * S, mm["cost"])]
    if oi < 0:
        parts.append((-oi * S, mm["loss"]))
    else:
        parts.append((oi * S, mm["profit"]))
    return stacked(name, parent, x, w, parts)


def build_margins(root, m):
    # beat 0: the 2023 glut, close up (70 mm per KRW trillion)
    g0 = empty("glut", root)
    show(g0, beat(0))
    S0, DX0, W0 = 62.0, 290.0, 200.0
    qs0 = QUARTERS[:9]  # 2022Q1 .. 2024Q1
    base0 = -5200.0
    box("floor0", (base0 - 1500, -32, -700), (base0 + 1500, -12, 250), m["floor"], g0)
    for i, q in enumerate(qs0):
        x = base0 + DX0 * (i - 4)
        pv = quarter_bar(f"g_{q}", g0, x, W0, Q[q][0], Q[q][1], S0, m)
        grow(pv, F(0, 0.04 + 0.065 * i), F(0, 0.13 + 0.065 * i))
    xq = base0
    r, o = Q["2023Q1"]
    label("2023Q1 revenue KRW 5.1T", (xq - 60, r * S0 * 0.5, 30), g0, beat(0, 0.45))
    label("costs KRW 8.5T: loss KRW 3.4T", (xq, (r - o) * S0 + 10, 0), g0, beat(0, 0.55))
    label("-66.9% operating margin", (xq + 60, r * S0 * 0.2, 30), g0, beat(0, 0.7))

    # beat 1: 50 wafers = all DRAM wafer starts. 18% (2025 est) then 30% (2027 est) of them slide
    # over to the HBM stack, the commodity block left behind shrinks, then the contract price rises.
    g1 = empty("divert", root)
    show(g1, beat(1))
    box("floor1", (-1800, -32, -700), (1700, -12, 250), m["floor"], g1)
    COLS, ROWS, SP, R = 10, 5, 130.0, 54.0
    gx0, gy0 = -1450.0, 90.0
    order = sorted(((c, r) for c in range(COLS) for r in range(ROWS)), key=lambda cr: (-cr[0], cr[1]))
    hx = 450.0
    hb = H.stack(g1, m, hx, 8, "div_hbm", tsv=False)
    htop = H.die_top(7)
    n18, n30 = 9, 15  # 18% and 30% of 50
    for idx, (c, r) in enumerate(order):
        pos = (gx0 + SP * c, gy0 + SP * r, 40.0)
        e = empty(f"w{c}_{r}", g1)
        wafer_disc(f"w{c}_{r}_m", pos, e, m["wafer"], r=R, t=8)
        pop = F(1, 0.02 + 0.002 * idx)
        if idx < n30:
            batch = 0 if idx < n18 else 1
            k = idx if batch == 0 else idx - n18
            fs = F(1, (0.18 if batch == 0 else 0.42) + 0.012 * k)
            fe = fs + 26
            path = [(0, 0, 0), rel(pos, (hx - 150, htop + 160, 60)), rel(pos, (hx, htop + 40, 60))]
            fly(e, path, fs, fe, 4)
            show(e, [(pop, fe)])
        else:
            show(e, [(pop, END)])
    # HBM dies appear as the wafers land: 4 dies after the 2025 batch, all 8 after the 2027 one
    f_a = F(1, 0.18 + 0.012 * (n18 - 1)) + 26
    f_b = F(1, 0.42 + 0.012 * (n30 - n18 - 1)) + 26
    for j, d in enumerate(hb.dies):
        show(d, [((f_a if j < 4 else f_b), END)])
    show(hb.base, [(F(1, 0.02), END)])
    # DRAM contract price index: 100 before, 195.5 after +95.5% (TrendForce 1Q26)
    S1, PX = 3.0, 1150.0
    pa = bar("price_base", g1, PX, 220, 0, 100 * S1, m["cost"])
    grow(pa, F(1, 0.03), F(1, 0.12))
    pb = bar("price_rise", g1, PX, 230, 100 * S1, 195.5 * S1, m["price"], d=230, z0=4)
    grow(pb, F(1, 0.66), F(1, 0.86))
    label("50 wafers = all DRAM starts", (gx0 + SP * 4.5, gy0 + SP * 4 + R + 10, 0), g1, beat(1, 0.04, 0.3))
    label("2025: 18% to HBM (est)", (hx, htop * 0.5, 30), g1, beat(1, 0.3))
    label("2027: 30% to HBM (est)", (hx, htop + 15, 0), g1, beat(1, 0.55))
    label("commodity DRAM: 35 of 50 left", (gx0 + SP * 3, gy0 + SP * 4 + R + 10, 0), g1, beat(1, 0.62))
    label("DRAM contract +95.5% 1Q26", (PX, 195.5 * S1 + 12, 0), g1, beat(1, 0.86))

    # beat 2: revenue climbs far above costs; the gap is gold
    g2 = empty("gap", root)
    show(g2, beat(2))
    S2, DX2, W2 = 13.0, 200.0, 140.0
    qs2 = QUARTERS[4:]
    base2 = 5200.0
    x0 = base2 - DX2 * (len(qs2) - 1) / 2
    box("floor2", (x0 - 400, -32, -700), (x0 + DX2 * len(qs2) + 200, -12, 250), m["floor"], g2)
    for i, q in enumerate(qs2):
        pv = quarter_bar(f"p_{q}", g2, x0 + DX2 * i, W2, Q[q][0], Q[q][1], S2, m)
        if i < 12:  # 2023Q1 .. 2025Q4
            grow(pv, F(2, 0.03 + 0.035 * i), F(2, 0.09 + 0.035 * i))
        else:  # 2026Q1 .. Q3 grow while the camera pulls back
            grow(pv, F(2, 0.50 + 0.09 * (i - 12)), F(2, 0.60 + 0.09 * (i - 12)))
    xl = x0 + DX2 * (len(qs2) - 1)
    r, o = Q["2023Q1"]
    label("2023Q1 loss KRW 3.4T", (x0, (r - o) * S2 + 8, 0), g2, beat(2, 0.08, 0.5))
    label(f"2025Q4 margin 58.4%", (x0 + DX2 * 11, Q["2025Q4"][0] * S2 + 8, 0), g2, beat(2, 0.45, 0.75))
    r, o = Q["2026Q3"]
    label("2026Q3 revenue KRW 104.6T", (xl, r * S2 + 10, 0), g2, beat(2, 0.8))
    label("Op income KRW 83.3T", (xl - 40, ((r - o) + o * 0.5) * S2, 30), g2, beat(2, 0.82))
    label("costs KRW 21.3T", (xl - 40, (r - o) * S2 * 0.5, 30), g2, beat(2, 0.84))
    label("79.7% operating margin", (x0 + DX2 * 9, Q["2026Q1"][0] * S2 + 120, 0), g2, beat(2, 0.88))
    close = ((x0 + DX2 * 5.5, 230.0, 0.0), 1650.0, 0.10, 0.08)
    wide = ((base2 + 100.0, 720.0, 0.0), 3000.0, 0.10, 0.07)
    camera(root, [
        ((base0, 440.0, 0.0), 2500.0, 0.10, 0.07),
        ((-100.0, 340.0, 0.0), 2050.0, 0.08, 0.06),
        close,
    ])
    # beat 2: hold close on 2023-2025, then pull back as the 2026 bars grow
    tgt, eye = bpy.data.objects["CamTarget"], bpy.data.objects["CamEye"]
    for f, (t, dist, yaw, pitch) in ((F(2, 0.47), close), (F(2, 0.85), wide), (F(3, 0) - 1, wide)):
        cp, sp = math.cos(pitch), math.sin(pitch)
        e = (t[0] + dist * cp * math.sin(yaw), t[1] + dist * sp, t[2] + dist * cp * math.cos(yaw))
        key(tgt, f, "location", P(*t))
        key(eye, f, "location", P(*e))


# ---- pricing: the 2026 spike is price, not volume -------------------------------------------------


def build_pricing(root, m):
    S = 10.0
    DX, W = 220.0, 80.0
    n = len(PRICE_Q)
    x0 = -DX * (n - 1) / 2
    floor(root, m, x0 - 300, -x0 + 300, y=-260)
    box("zero", (x0 - 200, -3, -150), (-x0 + 200, 3, 20), m["rail"], root)
    groups = [(0, 4, 0), (4, 11, 1), (11, 15, 2)]
    for i, q in enumerate(PRICE_Q):
        b, k, cnt = next((g[2], i - g[0], g[1] - g[0]) for g in groups if g[0] <= i < g[1])
        u = 0.05 + 0.55 * k / cnt
        x = x0 + DX * i
        for kind, v, dx, mk in (("p", ASP[i], -45, "price" if ASP[i] >= 0 else "price_dn"), ("b", BITS[i], 45, "bits")):
            if v == 0:
                v = 0.6  # a sliver so 0% still shows
            y0, y1 = (0, v * S) if v > 0 else (v * S, 0)
            at = (x + dx, 0, 0)
            pv = pivot(f"{kind}_{q}", at, root)
            box(f"{kind}_{q}_m", rel(at, (x + dx - W / 2, y0, -W)), rel(at, (x + dx + W / 2, y1, 0)), m[mk], pv)
            grow(pv, F(b, u), F(b, u + 0.12))
    X = lambda q: x0 + DX * PRICE_Q.index(q)  # noqa: E731
    label("1Q23 DRAM price -18%", (X("2023Q1") - 45, -18 * S - 10, 0), root, beat(0, 0.2))
    label("1Q23 bits -20%", (X("2023Q1") + 45, -20 * S - 30, 30), root, beat(0, 0.3))
    label("4Q23 price +18%", (X("2023Q4") - 45, 18 * S + 10, 0), root, beat(0, 0.7))
    label("1Q24 price +20%", (X("2024Q1") - 45, 20 * S + 10, 0), root, beat(1, 0.15))
    label("2Q25 bits +25%, price +2%", (X("2025Q2"), 25 * S + 10, 0), root, beat(1, 0.6))
    label("1Q26 DRAM price +65%", (X("2026Q1") - 45, 65 * S + 10, 0), root, beat(2, 0.3))
    label("1Q26 bits 0%", (X("2026Q1") + 45, 15, 30), root, beat(2, 0.4))
    label("3Q26 price +28%, bits +10%", (X("2026Q3"), 28 * S + 10, 0), root, beat(2, 0.65))
    camera(root, [
        ((X("2023Q2") + 100, 90.0, 0.0), 1550.0, 0.10, 0.07),
        ((X("2024Q3") + 100, 90.0, 0.0), 1900.0, 0.10, 0.07),
        ((150.0, 230.0, 0.0), 2450.0, 0.08, 0.07),
    ])


# ---- share: HBM share towers trading places ------------------------------------------------------


def build_share(root, m):
    S = 14.0
    W = 520.0
    SLOT = [-1050.0, 0.0, 1050.0]
    floor(root, m, -2000, 2000)
    # (company -> share) per beat; ranks decide the slot (TrendForce 2022; Counterpoint 2Q25, 2Q26)
    shares = [
        {"skh": 50, "ssg": 40, "mu": 10},
        {"skh": 64, "ssg": 15, "mu": 21},
        {"skh": 50, "ssg": 33, "mu": 18},
    ]
    names = {"skh": "SK hynix", "ssg": "Samsung", "mu": "Micron"}
    for c in ("skh", "ssg", "mu"):
        g = empty(f"tw_{c}", root)  # moves between slots
        pv = pivot(f"tw_{c}_p", (0, 0, 0), g)
        box(f"tw_{c}_m", (-W / 2, 0, -W), (W / 2, 1000.0, 0), m[c], pv)  # 1000 mm = 100%
        for b, sh in enumerate(shares):
            rank = sorted(sh, key=lambda k: -sh[k]).index(c)
            x = SLOT[rank]
            h = sh[c] / 100.0
            fa, fb = F(b, 0.02), F(b, 0.25)
            if b == 0:
                key(g, 0, "location", P(x, 0, 0))
                key(pv, 0, "scale", (OFF, OFF, OFF))
                key(pv, fa, "scale", (1, 1, OFF))
                key(pv, fb, "scale", (1, 1, h * S / 10.0))
            else:
                key(g, fa, "location", P(*prev_x))
                key(g, fb, "location", P(x, 0, 0))
                key(pv, fa, "scale", (1, 1, prev_h * S / 10.0))
                key(pv, fb, "scale", (1, 1, h * S / 10.0))
            prev_x, prev_h = (x, 0, 0), h
            tag = f"{names[c]} {sh[c]}%"
            if c == "skh":
                tag = ["2022: SK hynix 50% of HBM", "2Q25: SK hynix 64%", "2Q26: SK hynix 50%"][b]
            label(tag, (x, sh[c] * S + 15, 0), root, beat(b, 0.3))
        _constant_until(pv, F(0, 0.02) + 1)
    pose = ((0.0, 430.0, 0.0), 2200.0, 0.14, 0.10)
    camera(root, [pose, pose, pose])


# ---- fabs: capex, the new fabs rising, the 600T plan ----------------------------------------------


def fab(name, parent, x, z, w, h, d, m):
    g = empty(name, parent)
    pv = pivot(f"{name}_p", (x, 0, 0), g)
    box(f"{name}_m", rel((x, 0, 0), (x - w / 2, 0, z - d)), rel((x, 0, 0), (x + w / 2, h, z)), m["fab"], pv)
    box(f"{name}_r", rel((x, 0, 0), (x - w / 2 - 15, h, z - d - 15)), rel((x, 0, 0), (x + w / 2 + 15, h + 25, z + 15)), m["fab_roof"], pv)
    return g, pv


def build_fabs(root, m):
    """Capex & fabs: a world map with each SK hynix site pinned on it. The TUI flies the camera to
    a site on Enter (fab_map.py; sites in geo/sk_hynix_sites.json). The capex bars and fab tables
    stay in the section's data below the picture."""
    fab_map.build(root, m)


# ---- tech: TSVs, thin dies + MR-MUF, HBM4's wide bus ---------------------------------------------


def custom_stack(parent, m, x, n, die_t, gap, name):
    """A stack of n dies of thickness die_t with `gap` between them, on a base die; returns the
    group and the list of gap y ranges."""
    g = empty(name, parent)
    box(f"{name}_base", (x - 190, 0, -190), (x + 190, 70, 0), m["base"], g)
    gaps = []
    y = 70.0
    for k in range(n):
        gaps.append((y, y + gap))
        y += gap
        box(f"{name}_d{k}", (x - 170, y, -170), (x + 170, y + die_t, 0), m["dram"], g)
        for tx in (-110, 0, 110):
            tube(f"{name}_t{k}_{tx}", (x + tx, y - gap, 2), (x + tx, y + die_t, 2), 8, m["copper"], g, verts=8)
        y += die_t
    return g, gaps, y


def build_tech(root, m):
    # beat 0: TSVs carry data straight up through every die
    g0 = empty("tsv", root)
    show(g0, beat(0))
    X0 = -5200.0
    box("floor0", (X0 - 1500, -32, -600), (X0 + 1500, -12, 250), m["floor"], g0)
    s, gaps, top = custom_stack(g0, m, X0, 8, 40.0, 20.0, "t8")
    for k in range(12):
        tx = (-110, 0, 110)[k % 3]
        f0 = F(0, 0.15 + 0.06 * k)
        path = [(X0 + tx, 30, 14), (X0 + tx, top - 10, 14)]
        flyer(f"pulse{k}", g0, lambda e, c, k=k: ball(f"pulse{k}_m", c, 16, m["data"], e, 10), path, f0, f0 + 40)
    label("TSV: copper through every die", (X0 + 110, top * 0.55, 20), g0, beat(0, 0.1))
    label("base logic die + 8 DRAM dies", (X0 - 150, 35, 0), g0, beat(0, 0.3))
    label("HBM3E 8-high: 1.18 TB/s", (X0, top + 20, 0), g0, beat(0, 0.6))

    # beat 1: 12-high in the height of 8-high: 40% thinner dies, gaps filled with MR-MUF
    g1 = empty("thin", root)
    show(g1, beat(1))
    box("floor1", (-1500, -32, -600), (1500, -12, 250), m["floor"], g1)
    s8, gaps8, top8 = custom_stack(g1, m, -550, 8, 40.0, 20.0, "a8")
    s12, gaps12, top12 = custom_stack(g1, m, 550, 12, 24.0, 16.0, "a12")
    # height line across both
    box("hline", (-800, top8 - 3, -10), (800, top8 + 3, 20), m["line"], g1)
    for k, (y0, y1) in enumerate(gaps12):
        pv = pivot(f"muf{k}", (550, y0, 0), g1)
        box(f"muf{k}_m", rel((550, y0, 0), (550 - 175, y0, -175)), rel((550, y0, 0), (550 + 175, y1, 6)), m["mold"], pv)
        f0 = F(1, 0.35 + 0.035 * k)
        key(pv, 0, "scale", (OFF, OFF, OFF))
        key(pv, f0, "scale", (OFF, 1, 1))
        key(pv, f0 + 14, "scale", (1, 1, 1))
        _constant_until(pv, f0 + 1)
    label("8-high: 24 GB", (-550, top8 + 20, 0), g1, beat(1, 0.1))
    label("12-high: dies 40% thinner", (550, top12 + 20, 0), g1, beat(1, 0.2))
    label("36 GB at 8-high's height", (0, top8 + 12, 20), g1, beat(1, 0.3))
    label("MR-MUF fill: +10% heat out", (725, 200, 20), g1, beat(1, 0.6))

    # beat 2: HBM4 doubles the bus: 2,048 I/O from the base die to the GPU
    g2 = empty("bus", root)
    show(g2, beat(2))
    X2 = 5200.0
    box("floor2", (X2 - 1600, -32, -600), (X2 + 1600, -12, 250), m["floor"], g2)
    box("interposer2", (X2 - 1300, -60, -400), (X2 + 1300, 0, 0), m["interposer"], g2)
    s4, _, top4 = custom_stack(g2, m, X2 - 700, 12, 24.0, 16.0, "h4")
    box("gpu2", (X2 + 150, 0, -360), (X2 + 700, 200, 0), m["gpu"], g2)
    for j in range(16):
        y = 8.0
        z = -20 - 21 * j
        tube(f"wire{j}", (X2 - 510, y, z), (X2 + 150, y, z), 4, m["copper"], g2, verts=6)
    for k in range(28):
        j = (k * 7) % 16
        f0 = F(2, 0.1 + 0.025 * k)
        z = -20 - 21 * j
        path = [(X2 - 500, 18, z), (X2 + 150, 18, z)]
        flyer(f"bit{k}", g2, lambda e, c, k=k: ball(f"bit{k}_m", c, 12, m["data"], e, 8), path, f0, f0 + 30)
    label("HBM4 12-high", (X2 - 700, top4 + 20, 0), g2, beat(2, 0.1))
    label("2,048 I/O (data pins)", (X2 - 180, 12, -10), g2, beat(2, 0.25))
    label("10 Gbps per pin", (X2 + 425, 215, -100), g2, beat(2, 0.45))
    label("40%+ better power efficiency", (X2 - 700, top4 * 0.5, 20), g2, beat(2, 0.65))
    camera(root, [
        ((X0, 290.0, 0.0), 1350.0, 0.25, 0.12),
        ((0.0, 290.0, 0.0), 1500.0, 0.15, 0.10),
        ((X2 - 150, 220.0, -100.0), 1900.0, 0.15, 0.30),
    ])


# ---- listing: the 2026 Nasdaq ADR ---------------------------------------------------------------


def coin(e, c, m, r=70.0, t=16.0):
    disc(f"{e.name}_c", c, r, t, m["coin"], e, 24)


def build_listing(root, m):
    floor(root, m, -2400, 2600)
    # left: Nasdaq desk; centre: SK hynix vault; right (beat 1): the two fabs
    box("nasdaq", (-2000, 0, -300), (-1500, 380, 0), m["nasdaq"], root)
    box("vault", (-450, 0, -300), (50, 260, 0), m["skh"], root)
    # beat 0: 26 coins (one per US$1B of the $26.2B net) stack up on the vault
    CT = 22.0
    A = (-1500.0, 300.0, 80.0)
    for k in range(26):
        f0 = F(0, 0.05 + 0.028 * k)
        f1 = f0 + 24
        ys = 260 + 8 + CT * k
        e = empty(f"coin{k}", root)
        coin(e, A, m)
        pts = [A, (-850.0, 760.0, 80.0), (-200.0, ys + 60, 80.0), (-200.0, ys, 80.0)]
        fx = 600.0 if k < 15 else 1600.0  # Yongin Fab 1 26.6T / P&T7 18.9T of 45.5T -> 15 / 11 coins
        g0 = F(1, 0.2 + 0.024 * (25 - k))  # the top coin leaves first
        pts2 = [(fx, 700.0, 120.0), (fx, 120.0, 120.0)]
        for j, q in enumerate(pts):
            key(e, round(f0 + (f1 - f0) * j / 3), "location", P(*rel(A, q)), linear=True)
        key(e, g0, "location", P(*rel(A, pts[-1])), linear=True)
        key(e, g0 + 20, "location", P(*rel(A, pts2[0])), linear=True)
        key(e, g0 + 32, "location", P(*rel(A, pts2[1])), linear=True)
        show(e, [(f0, g0 + 32)])
    label("177.9M ADS at $149", (-1750, 380 + 15, 0), root, beat(0, 0.1))
    label("7x oversubscribed est", (-1750, 200, 30), root, beat(0, 0.3))
    label("Net proceeds $26.2B", (-200, 260 + CT * 26 + 30, 0), root, beat(0, 0.75) + beat(1, 0.0, 0.25))
    # beat 1: fabs rise (KRW trillion of the 45.5T use of proceeds)
    S = 14.0
    for nm, x, v, tag in (("yf1", 600.0, 26.6, "Yongin Fab 1 KRW 26.6T"), ("pt7", 1600.0, 18.9, "P&T7 HBM pkg KRW 18.9T")):
        g, pv = fab(nm, root, x, 0, 560, v * S, 400, m)
        grow(pv, F(1, 0.05), F(1, 0.3))
        show(g, [(F(1, 0.05), F(2, 0))])
        label(tag, (x, v * S + 50, 0), root, beat(1, 0.3))
    label("KRW 45.5T of capex in Korea", (1100, 150, 30), root, beat(1, 0.7))
    # beat 2: the first day: offer $149, open $170, close $168.49 (5 mm per $)
    g2 = empty("day1", root)
    show(g2, beat(2))
    for i, (nm, v, mk) in enumerate((("offer", 149.0, "cost"), ("open", 170.0, "price"), ("close", 168.49, "price"))):
        x = 300 + 600 * i
        pv = bar(f"px_{nm}", g2, x, 360, 0, v * 4.5, m[mk])
        grow(pv, F(2, 0.05 + 0.2 * i), F(2, 0.2 + 0.2 * i))
    label("Offer $149", (300, 149 * 4.5 + 15, 0), g2, beat(2, 0.15))
    label("Opened $170 (+14%)", (900, 170 * 4.5 + 15, 0), g2, beat(2, 0.35))
    label("Closed $168.49 est", (1500, 168.49 * 4.5 + 15, 0), g2, beat(2, 0.55))
    label("Mkt cap ~$1.2T est", (-200, 330, 0), g2, beat(2, 0.75))
    camera(root, [
        ((-900.0, 470.0, 0.0), 2450.0, 0.10, 0.07),
        ((150.0, 450.0, 0.0), 2750.0, 0.10, 0.07),
        ((300.0, 400.0, 0.0), 2600.0, 0.10, 0.07),
    ])


BUILDERS = {
    "snapshot": build_snapshot, "revenue": build_revenue, "mix": build_mix, "hbm": build_hbm,
    "margins": build_margins, "pricing": build_pricing, "share": build_share, "fabs": build_fabs,
    "tech": build_tech, "listing": build_listing,
}


def run(tab):
    m, root = start(f"{SLUG}_{tab}", beats=3, page="mem")
    m = mats(m)
    BUILDERS[tab](root, m)
    finish(tab)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for t in (argv or TABS):
        run(t)
