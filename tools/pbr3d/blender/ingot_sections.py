"""The ten INGOT write-up sections, each a 3D picture authored in Blender and exported for pbr3d in
the SAND template (docs/diagram-pages.md). Pieces come from ingot_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/ingot_sections.py [-- 3 5]

For each section it writes blender/ingot_sec<N>.blend and assets/ingot_sec<N>.glb.

  1  what happens   crop, test, grind, notch, wire saw in five beats (the rod moves along)
  2  the rod        side view: the cones and crop lines, the cones off, the V groove, the saw
  3  the physics    {100} and {111} planes, the <110> notch, dopant atoms in the lattice
  4  the wafer      300 mm across, 775 um thick, the notch, about 125 g and 640 dies
  5  size ladder    thickness per diameter: 100, 150, 200, 300 and 450 mm (never built)
  6  mass and dies  grams and dies per wafer for 100, 200, 300 and 450 mm
  7  who makes it   the five makers' 2024 shares as bars, then the five-firm total
  8  structure      five firms at 82-94%, the 2023 downturn, the supply chain
  9  listed names   the wafer makers and their exchange lines
 10  sources        eight source cards lit in four groups
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, empty, key, label, show  # noqa: E402
from sand_zooms import camera, finish, scale_keys  # noqa: E402
import ingot_kit as K  # noqa: E402
from ingot_kit import A, HALF, PITCH, R, RAW, STAGE_W, begin  # noqa: E402

END = F(40, 0)


def tag(root, text, at, f0, f1):
    label(text, at, root, [(f0, f1)])


def gbox(root, name, lo, hi, m, f0, f1=END):
    """A box switched on from f0 to f1, held in its own group: show() writes the group's scale, so
    the box keeps its size."""
    g = empty(name, root)
    box(name + "_m", lo, hi, m, g)
    show(g, [(f0, f1)])
    return g


def bar(root, name, x, w, h, m, f0, f1=END, depth=120.0, y0=0.0):
    """A standing bar at x, width w and height h, switched on from f0."""
    return gbox(root, name, (x - w / 2, y0, -depth / 2), (x + w / 2, y0 + h, depth / 2), m, f0, f1)


def hbar(root, name, x0, y, length, thick, m, f0, f1=END):
    """A horizontal bar from x0 to x0 + length, switched on from f0."""
    return gbox(root, name, (x0, y - thick / 2, -60), (x0 + length, y + thick / 2, 60), m, f0, f1)


# ---- 1. what happens --------------------------------------------------------------------------


def sec1():
    names = ["crop", "test", "grind", "notch", "saw"]
    m, root = begin("sec1", len(names))
    K.line(root, m, names, tags={
        0: [("cones cut at the joints", 0, A + RAW + 230, 80)],
        1: [("X-ray on the cut face", HALF + 30, A + 330, 80)],
        2: [("grind wheel to 300 mm", 0, A + RAW + 430, 80)],
        3: [("V groove, marks <110>", 0, A + R + 150, 80)],
        4: [("wire web cuts the kerf", 0, A - 300, 0)],
    })
    camera(root, [((i * K.STAGE_W, 640.0, 0.0), 3800.0, 0.40, 0.20) for i in range(len(names))])
    finish("sec1", page="ingot")


# ---- 2. the rod, side view --------------------------------------------------------------------


def sec2():
    names = ["asp", "crop", "notch", "saw"]
    m, root = begin("sec2", len(names))
    K.line(root, m, names, marks=True, tags={
        0: [("seed cone", -HALF - 70, A + RAW + 70, 80), ("crop lines at the joints", HALF, A + RAW + 170, 80)],
        1: [("cones fall away as scrap", -HALF - 70, 220, 80)],
        2: [("V groove runs the full length", 0, A + R + 150, 80)],
        3: [("wire web: the ingot is cut", 0, A - 300, 0)],
    })
    camera(root, [((i * K.STAGE_W, 620.0, 0.0), 3600.0, 0.25, 0.14) for i in range(len(names))])
    finish("sec2", page="ingot")


# ---- 3. the physics ---------------------------------------------------------------------------

CUBE = 5  # atoms per edge
SP = 70.0  # atom spacing, drawn


def atoms(root, m, origin, mat=None, skip=None):
    """A CUBE^3 lattice of atoms; `skip(i, j, k)` leaves a site out."""
    out = []
    for i in range(CUBE):
        for j in range(CUBE):
            for k in range(CUBE):
                if skip and skip(i, j, k):
                    continue
                c = (origin[0] + i * SP, origin[1] + j * SP, origin[2] + k * SP)
                out.append(ball(f"atom{i}{j}{k}", c, 22, mat or m["atom"], root, segs=6))
    return out


def sec3():
    m, root = begin("sec3", 4)
    ox = -2 * SP
    oy = A - 2 * SP
    oz = -2 * SP
    lat = empty("lattice", root)
    atoms(lat, m, (ox, oy, oz))
    show(lat, [(0, F(2, 0)), (F(3, 0), END)])
    # beat 0: the top face, {100}, a square grid; gold atoms on that layer
    top = empty("top_layer", root)
    for i in range(CUBE):
        for k in range(CUBE):
            ball(f"top{i}{k}", (ox + i * SP, oy + (CUBE - 1) * SP, oz + k * SP), 26, m["gold_glow"], top, segs=6)
    show(top, [(0, F(1, 0))])
    tag(root, "{100}: square grid, CMOS", (ox + 4 * SP + 80, oy + 4 * SP + 60, oz + 4 * SP), 0, F(1, 0))
    # beat 1: the {111} plane, a slanted slab through the cube, triangular grid
    slab_g = empty("plane111", root)
    slab = box("plane111_m", (-260, A - 10, -280), (260, A + 14, 280), m["bar_hi"], slab_g)
    slab.rotation_euler = (math.radians(45), 0, math.radians(35))
    show(slab_g, [(F(1, 0), F(2, 0))])
    tag(root, "{111}: triangular grid, bipolar, power", (300, A + 200, 0), F(1, 0.2), F(2, 0))
    # beat 2: the notch on a wafer rim marks <110>
    wf = K.zcyl("wafer_face", 0, A, 0, R, 22, m["si"], root)
    wf_g = empty("notch_group", root)
    wf_notch = box("rim_notch", (-30, A + R - 26, -20), (30, A + R + 16, 20), m["notch"], wf_g)
    wf_notch.rotation_euler = (0, 0, math.radians(45))
    show(wf, [(F(2, 0), F(3, 0))])
    show(wf_g, [(F(2, 0), F(3, 0))])
    tag(root, "notch marks <110>", (150, A + R + 120, 60), F(2, 0.3), F(3, 0))
    # beat 3: dopant atoms in the lattice, 1e13 to 1e16 per cm3
    dop = empty("dopant", root)
    for n, (i, j, k) in enumerate([(1, 2, 1), (3, 1, 3), (2, 3, 0), (0, 0, 4)]):
        ball(f"dop{n}", (ox + i * SP, oy + j * SP, oz + k * SP), 30, m["blue"], dop, segs=8)
    show(dop, [(F(3, 0.2), END)])
    tag(root, "dopant atoms: 1e13 to 1e16 per cm3", (-260, A + 260, 200), F(3, 0.3), END)
    camera(root, [
        ((0.0, A, 0.0), 1100.0, 0.5, 0.35),
        ((0.0, A, 0.0), 1200.0, 0.6, 0.45),
        ((0.0, A + 50, 0.0), 900.0, 0.2, 0.15),
        ((0.0, A, 0.0), 1100.0, 0.5, 0.25),
    ])
    finish("sec3", page="ingot")


# ---- 4. the wafer in numbers ------------------------------------------------------------------


def sec4():
    m, root = begin("sec4", 4)
    wf = K.zcyl("wafer", 0, A, 0, R, 22, m["si"], root)
    show(wf, [(0, END)])
    # beat 0: diameter 300 mm, a bar across the wafer
    d = hbar(root, "diameter", -R, A + R + 60, 2 * R, 10, m["bar_hi"], F(0, 0.1), F(1, 0))
    tag(root, "300 mm, +/- 0.2 mm", (0, A + R + 130, 60), F(0, 0.3), F(1, 0))
    # beat 1: thickness 775 um, seen from the edge
    edge = K.xcyl("edge", -40, 40, R, A, 0, m["si"], root)
    show(edge, [(F(1, 0), F(2, 0))])
    show(wf, [(0, F(1, 0))])
    tag(root, "775 um, +/- 25 um", (60, A + R + 70, 0), F(1, 0.3), F(2, 0))
    # beat 2: the 1.0 mm V notch on the rim
    n2_g = empty("notch_lip", root)
    n2 = box("notch_lip_m", (-30, A + R - 22, -18), (30, A + R + 16, 18), m["notch"], n2_g)
    n2.rotation_euler = (0, 0, math.radians(45))
    show(n2_g, [(F(2, 0), F(3, 0))])
    tag(root, "notch 1.0 mm deep, 90 deg", (120, A + R + 110, 60), F(2, 0.3), F(3, 0))
    # beat 3: a die grid inside the circle, about 640 dies of 100 mm2
    dies = empty("dies", root)
    for i in range(-6, 7):
        for j in range(-6, 7):
            x, y = i * 24.0, j * 24.0
            if math.hypot(x, y) < R - 14:
                box(f"die{i}_{j}", (x - 9, A + y - 9, 30), (x + 9, A + y + 9, 46), m["bar_hi"], dies)
    show(dies, [(F(3, 0.1), END)])
    tag(root, "about 125 g, about 640 dies", (0, A + R + 100, 60), F(3, 0.3), END)
    camera(root, [
        ((0.0, A, 0.0), 1000.0, 0.02, 0.05),
        ((0.0, A, 0.0), 1000.0, math.pi / 2 - 0.15, 0.05),
        ((0.0, A, 0.0), 800.0, 0.02, 0.05),
        ((0.0, A, 0.0), 800.0, 0.02, 0.05),
    ])
    finish("sec4", page="ingot")


# ---- 5. size ladder ---------------------------------------------------------------------------

LADDER = [("100 mm", 525), ("150 mm", 675), ("200 mm", 725), ("300 mm", 775), ("450 mm", 925)]


def sec5():
    m, root = begin("sec5", 3)
    for k, (name, um) in enumerate(LADDER):
        x = (k - 2) * 420.0
        f0 = [0, 0, 0, F(1, 0), F(2, 0)][k]
        mat = m["bar_hi"] if name == "300 mm" else m["bar"]
        if name == "450 mm":
            mat = m["ghost"]
        bar(root, f"um_{k}", x, 240, um / 2.0, mat, f0)
        tag(root, f"{name}: {um} um", (x, um / 2.0 + 90, 0), f0 + 40, END)
    camera(root, [((0, 260, 0), 3900.0, 0.2, 0.15), ((0, 260, 0), 3900.0, 0.2, 0.15),
                  ((0, 260, 0), 3900.0, 0.2, 0.15)])
    finish("sec5", page="ingot")


# ---- 6. mass and dies -------------------------------------------------------------------------

MASS = [("100 mm", 10, 56), ("200 mm", 53, 269), ("300 mm", 125, 640), ("450 mm", 342, 1490)]


def sec6():
    m, root = begin("sec6", 3)
    for k, (name, g, dies) in enumerate(MASS):
        x = (k - 1.5) * 380.0
        mat = m["bar_hi"] if name == "300 mm" else (m["ghost"] if name == "450 mm" else m["bar"])
        bar(root, f"mass_{k}", x, 200, g / 2.0, mat, 0)
        bar(root, f"dies_{k}", x, 200, dies / 6.0, mat, F(1, 0))
        tag(root, f"{name}: {g} g", (x, g / 2.0 + 50, 0), 40, F(1, 0))
        tag(root, f"{dies} dies", (x, dies / 6.0 + 50, 0), F(1, 0) + 40, END)
    camera(root, [((0, 240, 0), 3400.0, 0.2, 0.15), ((0, 240, 0), 3400.0, 0.2, 0.15),
                  ((0, 240, 0), 3400.0, 0.2, 0.15)])
    finish("sec6", page="ingot")


# ---- 7. who makes it --------------------------------------------------------------------------

SHARES = [("Shin-Etsu", 19.9), ("SUMCO", 17.2), ("GlobalWafers", 12.9), ("Siltronic", 9.9), ("SK Siltron", 8.6)]


def sec7():
    m, root = begin("sec7", 4)
    for k, (name, pct) in enumerate(SHARES):
        y = 560.0 - k * 220.0
        f0 = [0, 0, F(1, 0), F(1, 0), F(2, 0)][k]
        mat = m["bar_hi"] if k < 2 else m["bar"]
        hbar(root, f"share{k}", 0, y, pct * 40.0, 120, mat, f0)
        tag(root, f"{name}: {pct}%", (pct * 40.0 + 80, y, 60), f0 + 40, F(3, 0) if k < 4 else END)
    # beat 3: the five firms stacked against the rest of the market
    hbar(root, "rest", 0, 140, 1300.0, 120, m["ghost"], F(3, 0))
    tag(root, "five firms 68.5%, rest 31.5%", (0, 120, 60), F(3, 0.3), END)
    camera(root, [((350, 350, 0), 3600.0, 0.0, 0.0), ((350, 350, 0), 3600.0, 0.0, 0.0),
                  ((350, 350, 0), 3600.0, 0.0, 0.0), ((350, 300, 0), 3600.0, 0.0, 0.0)])
    finish("sec7", page="ingot")


# ---- 8. structure and risks -------------------------------------------------------------------


def sec8():
    m, root = begin("sec8", 3)
    # beat 0: five firms at 82-94% of the market
    hbar(root, "firms_solid", -1000, 360, 820 * 2, 160, m["bar_hi"], 0, F(1, 0))
    hbar(root, "firms_band", -1000 + 1640, 360, 120, 160, m["grey"], 0, F(1, 0))
    tag(root, "five firms: 82-94% of wafers", (0, 620, 60), 40, F(1, 0))
    # beat 1: the 2023 downturn, bars shrinking from 2022
    rows = [("wafer revenue -10.9%", 10.9), ("area shipped -14.3%", 14.3), ("polished 300 mm -13%", 13.0), ("epi 300 mm -5%", 5.0)]
    for k, (name, pct) in enumerate(rows):
        y = 300.0 - k * 180.0
        hbar(root, f"base{k}", 0, y, 1000, 90, m["ghost"], F(1, 0))
        hbar(root, f"drop{k}", 0, y, 1000 * (1 - pct / 100.0), 90, m["bar_hi"], F(1, 0))
        tag(root, name, (1050, y, 60), F(1, 0.3), F(2, 0))
    # beat 2: the supply chain, with the quartz link flagged
    steps = ["Spruce Pine quartz", "crucible", "polysilicon", "CZ pull", "wafer"]
    for k, s in enumerate(steps):
        x = (k - 2) * 900.0
        box(f"chain{k}", (x - 300, 0, -120), (x + 300, 220, 120), m["bar"] if k else m["bar_hi"], root)
        tag(root, s, (x, 300, 140), F(2, 0.2), END)
    camera(root, [((300, 420, 0), 4800.0, 0.0, 0.0), ((700, 300, 0), 4800.0, 0.0, 0.0),
                  ((0, 260, 0), 6400.0, 0.1, 0.1)])
    finish("sec8", page="ingot")


# ---- 9. listed names --------------------------------------------------------------------------

NAMES = [("Shin-Etsu 4063.T", 0), ("SUMCO 3436.T", 0), ("GlobalWafers 6488.TWO", 1),
         ("Siltronic SSG.DE", 1), ("SK Siltron (SK Inc 034730.KS)", 2)]


def sec9():
    m, root = begin("sec9", 3)
    for k, (name, beat) in enumerate(NAMES):
        x = (k - 2) * 700.0
        gbox(root, f"card{k}", (x - 300, 0, -40), (x + 300, 200, 40), m["card"], 0)
        gbox(root, f"lit{k}", (x - 300, 200, -40), (x + 300, 224, 40), m["gold_glow"], F(beat, 0.2))
        tag(root, name, (x, 260, 0), F(beat, 0.3), END)
    gbox(root, "stamp", (-900, -180, -40), (900, -60, 40), m["red"], F(2, 0.5))
    tag(root, "tickers: general knowledge, not fetched", (0, -250, 0), F(2, 0.6), END)
    camera(root, [((0, 200, 0), 6400.0, 0.0, 0.0), ((0, 200, 0), 6400.0, 0.0, 0.0),
                  ((0, 150, 0), 6400.0, 0.0, 0.0)])
    finish("sec9", page="ingot")


# ---- 10. sources ------------------------------------------------------------------------------

SOURCES = ["[1] Wikipedia: Wafer (electronics)", "[2] Wikipedia: Czochralski method",
           "[3] University Wafer 300 mm sheet", "[4] USPTO 12617032, 12605863",
           "[5] Report Prime wafer shares", "[6] Omdia 2020, via KED Global",
           "[7] SEMI 2023, via substack", "[8] SEMI M1 listing"]


def sec10():
    m, root = begin("sec10", 4)
    for k, text in enumerate(SOURCES):
        x = (k % 4 - 1.5) * 760.0
        z = 0.0
        y = 300.0 - (k // 4) * 320.0
        beat = k // 2
        box(f"src{k}", (x - 330, y, -30), (x + 330, y + 200, 30), m["card"], root)
        gbox(root, f"lit{k}", (x - 330, y + 200, -30), (x + 330, y + 226, 30), m["gold_glow"], F(beat, 0.2))
        tag(root, text, (x, y + 250, 0), F(beat, 0.3), F(beat + 1, 0))
    camera(root, [((0, 80, 0), 5200.0, 0.0, 0.0)] * 4)
    finish("sec10", page="ingot")


BUILDS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9, 10: sec10}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [str(n) for n in BUILDS]
    for n in which:
        BUILDS[int(n)]()
