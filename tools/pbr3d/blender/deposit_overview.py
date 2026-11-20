"""The DEPOSIT node page's overview (FRONT END, grow film), in the picture-and-panel template.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/deposit_overview.py

Writes blender/deposit_overview.blend and assets/deposit_overview.glb. One beat is 8 s.

Units are millimetres, Y up, camera on +z, cut-away at z = 0 (as sand_overview.py). The wafer is
300 mm across. Film and layer thicknesses are drawn larger than life so they read on screen.

One chamber: gas comes down the feed from the gas cabinet, through the showerhead, to a wafer on a
heated pedestal; a pump draws the by-products out at the bottom. A trench in silicon sits on its own
set for beat 4. Six beats (match the six beats in diagrams_nodes/deposit/overview.rs):
  0 grow film   the whole chamber: gas in through the showerhead, a thin film starts on the wafer
  1 CVD         close on the wafer: precursor reacts at the hot surface, the film rises, by-products drop
  2 ALD         close on the wafer: pulse A, purge, pulse B, purge; one teal layer per cycle, three cycles
  3 PVD         the metal target and argon plasma replace the showerhead; sputtered metal lands on the wafer
  4 trench      a trench in silicon: ALD coats it evenly, then PVD piles up at the top and thins below
  5 clean       by-products out the pump; a deposit flakes off the wall and lands on the wafer
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, key, label, mat, cut, show, empty, pivot, rel, box, disc, ball, rock, tube, wall, fly  # noqa: E402
from sand_zooms import start, camera, finish  # noqa: E402

PAGE = "deposit"
NAME = "overview"
BEATS = 6

CH_R = 420.0  # chamber radius
CH_TOP = 560.0  # top of the chamber wall (the lid is left off so the inside shows)
WAF_TOP = 242.0  # top of the wafer, where films start
WAF_R = 150.0  # 300 mm wafer
LAYER = 6.0  # one ALD layer, drawn thick
FILM_T = 36.0  # the full CVD film, drawn thick

# one (target, distance, yaw, pitch) per beat, as sand_zooms.camera expects
POSES = [
    ((0.0, 420.0, 0.0), 2600.0, 0.45, 0.22),  # 0 whole chamber
    ((0.0, 300.0, 0.0), 1000.0, 0.35, 0.18),  # 1 wafer, CVD
    ((0.0, 270.0, 0.0), 520.0, 0.40, 0.25),  # 2 wafer, ALD cycles
    ((0.0, 380.0, 0.0), 1500.0, 0.40, 0.15),  # 3 target and plasma
    ((0.0, 120.0, 0.0), 1000.0, 0.25, 0.20),  # 4 trench
    ((0.0, 300.0, 0.0), 1900.0, 0.60, 0.20),  # 5 chamber, pump, flake
]


def materials():
    return {
        "steel": mat("dep_steel", (0.36, 0.38, 0.43), metal=0.6, rough=0.4),
        "chamber": mat("dep_chamber", (0.30, 0.32, 0.36), metal=0.5, rough=0.45),
        "pedestal": mat("dep_pedestal", (0.22, 0.22, 0.24), rough=0.7),
        "heat": mat("dep_heat", (1.0, 0.5, 0.15), emit=(1.0, 0.45, 0.1), strength=5.0),
        "wafer": mat("dep_wafer", (0.28, 0.30, 0.34), metal=0.3, rough=0.3),
        "silicon": mat("dep_silicon", (0.32, 0.34, 0.38), metal=0.2, rough=0.35),
        "cvd": mat("dep_cvd_film", (0.78, 0.66, 0.42), rough=0.4),
        "ald": mat("dep_ald_layer", (0.35, 0.80, 0.82), rough=0.3),
        "metal": mat("dep_metal_film", (0.80, 0.82, 0.86), metal=0.9, rough=0.25),
        "target": mat("dep_target", (0.45, 0.47, 0.52), metal=0.9, rough=0.35),
        "plasma": mat("dep_plasma", (0.6, 0.4, 1.0), emit=(0.55, 0.35, 1.0), strength=1.6, alpha=0.35),
        "precursor": mat("dep_precursor", (1.0, 0.6, 0.2), emit=(1.0, 0.55, 0.15), strength=3.0),
        "reactant": mat("dep_reactant", (0.4, 0.7, 1.0), emit=(0.3, 0.6, 1.0), strength=3.0),
        "purge": mat("dep_purge", (0.85, 0.92, 1.0), emit=(0.7, 0.8, 1.0), strength=1.0, alpha=0.4),
        "argon": mat("dep_argon", (0.75, 0.55, 1.0), emit=(0.6, 0.4, 1.0), strength=4.0),
        "atom": mat("dep_metal_atom", (0.85, 0.86, 0.90), metal=0.9, rough=0.3),
        "byprod": mat("dep_byproduct", (0.92, 0.85, 0.5), emit=(0.9, 0.8, 0.4), strength=1.5),
        "deposit": mat("dep_wall_deposit", (0.50, 0.44, 0.36), rough=0.9),
        "flake": mat("dep_flake", (0.45, 0.45, 0.47), rough=0.9),
        "gas": mat("dep_gas_cabinet", (0.55, 0.58, 0.62), metal=0.5, rough=0.5),
    }


# ---- helpers ----------------------------------------------------------------------------


def bead(parent, name, pts, size, m, b, u0, life, until=None):
    """One bead that travels the absolute polyline `pts` over `life` frames, launched at fraction u0
    of beat b and kept on until `until` (default: the end of beat b)."""
    e = empty(name, parent)
    ball(name + "_ball", pts[0], size, m, e, segs=12)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    f0 = F(b, u0)
    f1 = f0 + life
    end = until if until is not None else F(b + 1, 0)
    fly(e, path, f0, f1, steps=min(60, max(4, len(pts) * 3)))
    show(e, [(f0, min(f1, end))])
    return e


def grow(m, root, name, at, radius, thick, mat_, shown, keys):
    """A disc that grows up from poly point `at`: its Y scale runs through `keys` [(frame, s)] while
    the group is switched on by `shown` intervals. Built relative to a pivot at `at`, so the scale
    holds the base still."""
    g = empty(name, root)
    show(g, shown)
    pv = pivot(name + "_grow", at, g)
    d = disc(name + "_disc", rel(at, (at[0], at[1] + thick / 2, at[2])), radius, thick, mat_)
    cut(d, 0.0)
    d.parent = pv
    for f, s in keys:
        key(pv, f, "scale", (1.0, s, 1.0), linear=True)
    return g


# ---- the parts -------------------------------------------------------------------------


def chamber(m, root):
    """The process chamber, cut open: wall, floor, heated pedestal, wafer, pump port and pump, and a
    deposit patch on the wall (the flake in beat 5 comes off it)."""
    g = empty("dep_chamber", root)
    cut(wall("dep_wall", CH_R, 0.0, CH_TOP, 22.0, m["chamber"], g), 0.0)
    cut(disc("dep_floor", (0, -10, 0), CH_R, 20, m["chamber"], g), 0.0)
    cut(disc("dep_pedestal", (0, 110, 0), 170, 220, m["pedestal"], g), 0.0)
    cut(disc("dep_heater", (0, 224, 0), 165, 6, m["heat"], g), 0.0)
    cut(disc("dep_wafer", (0, WAF_TOP - 6, 0), WAF_R, 12, m["wafer"], g), 0.0)
    cut(tube("dep_pump_port", (300, -20, 0), (300, -190, 0), 60, m["chamber"], g), 0.0)
    cut(box("dep_pump", (150, -300, -130), (450, -190, 130), m["steel"], g), 0.0)
    cut(box("dep_wall_patch", (-402, 360, -70), (-396, 470, 70), m["deposit"], g), 0.0)
    return g


def gas_top(m, root):
    """The gas side: cabinet, line, manifold, feed, and the showerhead over the wafer."""
    g = empty("dep_gas_top", root)
    cut(box("dep_gas_cabinet", (-820, 0, -150), (-640, 720, 150), m["gas"], g), 0.0)
    cut(tube("dep_gas_line", (-640, 700, 0), (-200, 805, 0), 30, m["steel"], g), 0.0)
    cut(box("dep_manifold", (-200, 780, -90), (200, 830, 90), m["steel"], g), 0.0)
    cut(tube("dep_feed", (0, 490, 0), (0, 780, 0), 35, m["steel"], g), 0.0)
    cut(disc("dep_showerhead", (0, 480, 0), 330, 20, m["steel"], g), 0.0)
    return g


def ald_layer_disc(m, root, c):
    """The c-th ALD layer (one monolayer drawn thick), sitting on the layers below it."""
    top = WAF_TOP + LAYER * c
    d = disc(f"dep_ald_layer{c}", (0, top + LAYER / 2, 0), WAF_R, LAYER, m["ald"], root)
    cut(d, 0.0)
    return d


def target_and_plasma(m, root):
    """Beat 3's source: the metal target above the wafer and the argon plasma between them."""
    g = empty("dep_pvd_source", root)
    show(g, [(F(3, 0), F(4, 0))])
    cut(box("dep_target", (-330, 392, -200), (330, 420, 200), m["target"], g), 0.0)
    cut(disc("dep_plasma", (0, 345, 0), 300, 90, m["plasma"], g), 0.0)
    return g


def trench(m, root):
    """Beat 4: a trench 120 mm wide and 140 mm deep in silicon. ALD (first half) and PVD (second half)
    are built as separate film sets on the same silicon."""
    g = empty("dep_trench", root)
    show(g, beat_iv(4))
    for name, lo, hi in (
        ("dep_si_left", (-400, 0, -200), (-60, 200, 200)),
        ("dep_si_right", (60, 0, -200), (400, 200, 200)),
        ("dep_si_floor", (-60, 0, -200), (60, 60, 200)),
    ):
        cut(box(name, lo, hi, m["silicon"], g), 0.0)

    ald = empty("dep_trench_ald", g)
    show(ald, [(F(4, 0), F(4, 0.5))])
    for name, lo, hi in (
        ("ald_top_left", (-400, 200, -200), (-60, 204, 200)),
        ("ald_wall_left", (-60, 60, -200), (-56, 204, 200)),
        ("ald_floor", (-60, 60, -200), (60, 64, 200)),
        ("ald_wall_right", (56, 60, -200), (60, 204, 200)),
        ("ald_top_right", (60, 200, -200), (400, 204, 200)),
    ):
        cut(box(name, lo, hi, m["ald"], ald), 0.0)

    pvd = empty("dep_trench_pvd", g)
    show(pvd, [(F(4, 0.5), F(5, 0))])
    for name, lo, hi in (
        ("pvd_top_left", (-400, 200, -200), (-60, 210, 200)),
        ("pvd_lip_left", (-66, 200, -200), (-50, 210, 200)),
        ("pvd_wall_left", (-60, 60, -200), (-57, 200, 200)),
        ("pvd_floor", (-60, 60, -200), (60, 62, 200)),
        ("pvd_wall_right", (57, 60, -200), (60, 200, 200)),
        ("pvd_top_right", (60, 200, -200), (400, 210, 200)),
        ("pvd_lip_right", (50, 200, -200), (66, 210, 200)),
    ):
        cut(box(name, lo, hi, m["metal"], pvd), 0.0)
    return g


def beat_iv(i):
    return [(F(i, 0), F(i + 1, 0))]


# ---- the beats -------------------------------------------------------------------------


def beat0(m, root):
    """Gas down the feed, spread over the wafer. The film starts thin (grow runs in beat 1)."""
    for k in range(6):
        x = -240.0 + 96.0 * k
        bead(root, f"dep_g0_{k}", [(0.0, 770.0, 0.0), (0.0, 500.0, 0.0), (x, 262.0, 0.0)], 6.0,
             m["precursor"], 0, 0.05 + 0.06 * k, 40)


def beat1(m, root):
    """CVD: precursor from the showerhead reacts at the hot surface; the by-products go to the pump."""
    for k in range(9):
        x = -240.0 + 60.0 * k
        bead(root, f"dep_cv{k}", [(x * 0.7, 455.0, 0.0), (x * 0.4, 340.0, 0.0), (x * 0.1, 252.0, 0.0)],
             7.0, m["precursor"], 1, 0.04 + 0.03 * k, 36)
    for k in range(5):
        x = -120.0 + 60.0 * k
        bead(root, f"dep_rx{k}", [(x, WAF_TOP + 4, 0.0), (x + 8, WAF_TOP + 34, 0.0), (x + 14, WAF_TOP + 64, 0.0)],
             6.0, m["heat"], 1, 0.36 + 0.04 * k, 30)
    for k in range(5):
        x = -100.0 + 50.0 * k
        bead(root, f"dep_bp{k}", [(x, 252.0, 0.0), (230.0, 250.0, 0.0), (240.0, 40.0, 0.0), (300.0, -170.0, 0.0)],
             6.0, m["byprod"], 1, 0.5 + 0.03 * k, 48)


# one ALD cycle spans CYCLE of beat 2; its steps, as fractions of the beat from the cycle's start
CYCLE = 0.3
STEP = {"A": (0.01, 0.06), "P1": (0.06, 0.10), "B": (0.10, 0.16), "P2": (0.16, 0.20), "LAYER": 0.21}


def ald_cycles(m, root):
    """Three ALD cycles in beat 2, each CYCLE long so all three layers land inside the beat. Each:
    pulse A (precursor dots settle), purge, pulse B (reactant), purge, then its layer is in place."""
    for c in range(3):
        cs = c * CYCLE
        top = WAF_TOP + LAYER * c
        a0, a1 = STEP["A"]
        dots = empty(f"dep_dots{c}", root)
        show(dots, [(F(2, cs + a0), F(2, cs + a1))])
        for i, x in enumerate((-120.0, -80.0, -40.0, 0.0, 40.0, 80.0, 120.0)):
            for z in (-50.0, 0.0, 50.0):
                ball(f"dep_site{c}_{i}_{int(z)}", (x, top + 5.0, z), 5.0, m["precursor"], dots, segs=12)
        for i, x in enumerate((-120.0, -40.0, 40.0, 120.0)):
            bead(root, f"dep_pa{c}_{i}", [(x, 420.0, 0.0), (x, top + 5.0, 0.0)], 6.0, m["precursor"],
                 2, cs + a0 + 0.001 * i, 8, until=F(2, cs + a1))
        p0, p1 = STEP["P1"]
        for k, z in enumerate((-45.0, -15.0, 15.0, 45.0)):
            bead(root, f"dep_pu{c}_{k}", [(-300.0, top + 30.0, z), (300.0, top + 30.0, z)], 5.0, m["purge"],
                 2, cs + p0 + 0.003 * k, 10, until=F(2, cs + p1))
        b0, b1 = STEP["B"]
        for i, x in enumerate((-100.0, -30.0, 40.0, 110.0)):
            bead(root, f"dep_pb{c}_{i}", [(x, 420.0, 0.0), (x, top + 5.0, 0.0)], 6.0, m["reactant"],
                 2, cs + b0 + 0.001 * i, 8, until=F(2, cs + b1))
        q0, q1 = STEP["P2"]
        for k, z in enumerate((-45.0, -15.0, 15.0, 45.0)):
            bead(root, f"dep_pv{c}_{k}", [(-300.0, top + 30.0, z), (300.0, top + 30.0, z)], 5.0, m["purge"],
                 2, cs + q0 + 0.003 * k, 10, until=F(2, cs + q1))
        show(ald_layer_disc(m, root, c), [(F(2, cs + STEP["LAYER"]), F(3, 0))])


def beat3_argon_and_atoms(m, root):
    """PVD: argon ions climb into the target; sputtered metal atoms fly down in straight lines."""
    for k in range(8):
        x = -240.0 + 480.0 * k / 7.0
        bead(root, f"dep_ar{k}", [(x, 280.0, 0.0), (x * 0.9, 385.0, 0.0)], 6.0, m["argon"], 3, 0.04 + 0.03 * k, 24)
    for k in range(9):
        x = -240.0 + 480.0 * k / 8.0
        bead(root, f"dep_at{k}", [(x, 390.0, 0.0), (x * 0.6, 320.0, 0.0), (x * 0.5, 250.0, 0.0)], 5.0,
             m["atom"], 3, 0.30 + 0.04 * k, 32)


def beat5_flakes(m, root):
    """A flake breaks off the wall deposit and falls to the wafer, three of them over beat 5."""
    for k in range(3):
        start_pt = (-392.0, 430.0 - 40.0 * k, 0.0)
        pts = [start_pt, (-300.0, 340.0 - 20.0 * k, 0.0), (-150.0 + 40.0 * k, 262.0, 0.0),
               (-120.0 + 60.0 * k, WAF_TOP + 8.0, 0.0)]
        e = empty(f"dep_flake{k}", root)
        rock(f"dep_flake{k}_rock", start_pt, 9.0, m["flake"], e)
        path = [tuple(p[i] - start_pt[i] for i in range(3)) for p in pts]
        f0, f1 = F(5, 0.45 + 0.06 * k), F(5, 0.72 + 0.06 * k)
        fly(e, path, f0, f1, steps=6)
        show(e, [(f0, F(6, 0))])
    for k in range(6):
        x = -100.0 + 40.0 * k
        bead(root, f"dep_bq{k}", [(x, 252.0, 0.0), (230.0, 250.0, 0.0), (240.0, 40.0, 0.0), (300.0, -170.0, 0.0)],
             6.0, m["byprod"], 5, 0.05 + 0.03 * k, 48, until=F(5, 0.5))


# ---- labels -----------------------------------------------------------------------------


def labels(root):
    # beat 0
    label("precursor gas in", (60.0, 880.0, 0.0), root, beat_iv(0))
    label("showerhead", (370.0, 480.0, 0.0), root, beat_iv(0))
    label("heated pedestal", (-220.0, 130.0, 0.0), root, beat_iv(0))
    label("gas cabinet", (-730.0, 790.0, 0.0), root, beat_iv(0))
    label("pump", (300.0, -250.0, 0.0), root, [(F(0, 0), F(2, 0)), (F(5, 0), F(6, 0))])
    # beat 1
    label("reacts on the hot surface", (-200.0, 320.0, 0.0), root, beat_iv(1))
    label("solid film grows", (210.0, 300.0, 0.0), root, beat_iv(1))
    label("by-products to the pump", (300.0, -230.0, 0.0), root, beat_iv(1))
    # beat 2, cycle 1
    tag = (-200.0, 300.0, 0.0)
    label("1 pulse A, precursor sticks", tag, root, [(F(2, STEP["A"][0]), F(2, STEP["A"][1]))])
    label("2 purge, excess removed", tag, root, [(F(2, STEP["P1"][0]), F(2, STEP["P1"][1]))])
    label("3 pulse B, reactant", tag, root, [(F(2, STEP["B"][0]), F(2, STEP["B"][1]))])
    label("4 purge", tag, root, [(F(2, STEP["P2"][0]), F(2, STEP["P2"][1]))])
    label("one layer per cycle", tag, root, [(F(2, STEP["LAYER"]), F(3, 0))])
    # beat 3
    label("argon plasma", (-280.0, 335.0, 0.0), root, beat_iv(3))
    label("metal target", (300.0, 425.0, 0.0), root, beat_iv(3))
    label("atoms fly straight to the wafer", (250.0, 300.0, 0.0), root, [(F(3, 0.3), F(4, 0))])
    # beat 4
    label("ALD coats walls and floor evenly", (0.0, 300.0, 0.0), root, [(F(4, 0), F(4, 0.5))])
    label("PVD thick on top, thin in trench", (0.0, 300.0, 0.0), root, [(F(4, 0.5), F(5, 0))])
    # beat 5
    label("deposit on the wall", (-410.0, 430.0, 0.0), root, [(F(5, 0), F(6, 0))])
    label("flake lands on the wafer", (-100.0, 280.0, 0.0), root, [(F(5, 0.72), F(6, 0))])


# ---- the scene -------------------------------------------------------------------------


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = materials()
    show(chamber(m, root), [(F(0, 0), F(4, 0)), (F(5, 0), F(6, 0))])
    show(gas_top(m, root), [(F(0, 0), F(3, 0)), (F(5, 0), F(6, 0))])
    grow(m, root, "dep_cvd", (0.0, WAF_TOP, 0.0), WAF_R, FILM_T, m["cvd"],
         [(F(0, 0), F(2, 0))], [(F(0, 0.25), 0.04), (F(1, 0.95), 1.0)])
    target_and_plasma(m, root)
    grow(m, root, "dep_metal", (0.0, WAF_TOP, 0.0), WAF_R, 14.0, m["metal"],
         [(F(3, 0.55), F(4, 0))], [(F(3, 0.55), 0.04), (F(3, 0.95), 1.0)])
    trench(m, root)
    beat0(m, root)
    beat1(m, root)
    ald_cycles(m, root)
    beat3_argon_and_atoms(m, root)
    beat5_flakes(m, root)
    labels(root)
    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
