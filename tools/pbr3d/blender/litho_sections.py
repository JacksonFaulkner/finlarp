"""The ten LITHO write-up sections, each a 3D picture authored in Blender and exported for pbr3d in
the SAND template (docs/diagram-pages.md). Scanner pieces come from litho_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/litho_sections.py [-- 3 5]

For each section it writes blender/litho_sec<N>.blend and assets/litho_sec<N>.glb.

  1 what happens   light through the reticle, the lens shrinks the image, develop, etch (four beats)
  2 parts          wavelength, the EUV tin droplet, mirrors, reticle and lens, resist and stage (five)
  3 one exposure   source flash, lens, exposed resist, develop, etch (five beats, one per step)
  4 resolution     three line tiles: DUV 57 nm, EUV 16 nm, High-NA 10 nm (three beats)
  5 focus          the in-focus band long at NA 0.33, short at 0.55, and a bowed wafer (three)
  6 memory         one 6F^2 cell, F shrunk by 0.7, twice the cells (three beats)
  7 multi          lines merging, split across two masks, overlay error (three beats)
  8 makers         ASML, Nikon and Canon, one lit at a time (three beats)
  9 risks          one EUV maker, mirrors and tin, stochastic defects, export rules (four beats)
 10 sources        source cards lighting up in groups (three beats)

One beat is SEC (8) seconds at 24 fps.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, beat, box, cut, disc, empty, key, label, show, tube  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
from poly_overview import run  # noqa: E402
import litho_kit as K  # noqa: E402
from litho_kit import END, RES_TOP, RET_Y  # noqa: E402


def begin(n, beats):
    m, root = start(f"sec{n}", beats, page="litho")
    K.mats(m)
    return m, root


def on(parent, name, m_key, m, intervals, pos=None):
    """A group wrapping a box is what the caller builds; this only keeps the switch readable."""
    return empty(name, parent)


def no_tiles(tiles):
    """Hide the wafer's field tiles: unswitched, the pink and cyan tiles z-fight on the row."""
    for pink, cy in tiles.values():
        show(pink, [])
        show(cy, [])


def wrap(parent, name, intervals):
    """An empty switched on for `intervals`; build parts under it to show them only then."""
    g = empty(name, parent)
    show(g, intervals)
    return g


def card(parent, m, x, z, label_text, mat_key, intervals):
    """One source card on a plinth; it lights gold for `intervals`."""
    # a dark card body, and a lit top the size of the card: lit cards read as gold, unlit as grey
    box(f"card_{x:+.0f}_{z:+.0f}", (x - 330, 0, z - 230), (x + 330, 24, z + 230), m["grey"], parent)
    lit = empty(f"lit_{x:+.0f}_{z:+.0f}", parent)
    box(f"lit_m_{x:+.0f}_{z:+.0f}", (x - 330, 24, z - 230), (x + 330, 30, z + 230), m[mat_key], lit)
    show(lit, intervals)
    label(label_text, (x - 330, 40, z + 230), parent, intervals)


# ---- 1: what happens ----------------------------------------------------------------------


def sec1():
    m, root = begin(1, 4)
    K.frame(root, m)
    K.source(root, m, on=[(F(0, 0), END)])
    K.reticle(root, m)
    K.lens(root, m, slit_on=[])
    wg, tiles = K.wafer(root, m)
    K.rays(root, m, 0, 0.0, 0.7, K.light_path_to_reticle, n=2, life=30)
    K.rays(root, m, 1, 0.0, 0.7, K.light_path_to_wafer, n=3, life=40)
    for k, (pink, cy) in tiles.items():
        show(pink, [(F(1, 0.5), F(2, 0.0))])
        show(cy, [(F(2, 0.0), F(3, 0.0))])
    label("light through the openings only", (-150, K.RET_Y + 30, 20), root, [(F(0, 0), F(1, 0))])
    label("the lens shrinks the image on resist", (160, 380, 20), root, [(F(1, 0), F(2, 0))])
    label("develop: exposed resist goes", (0, RES_TOP + 40, 20), wg, [(F(2, 0), F(3, 0))])
    label("etch copies it into the film", (0, RES_TOP + 40, 20), wg, [(F(3, 0), END)])
    camera(root, [
        ((0.0, 440.0, 0.0), 1700.0, 0.30, 0.12),
        ((0.0, 430.0, 0.0), 1500.0, 0.30, 0.10),
        ((0.0, 80.0, 0.0), 800.0, 0.25, 0.16),
        ((0.0, 80.0, 0.0), 800.0, 0.25, 0.16),
    ])
    finish("sec1", page="litho")


# ---- 2: the parts -------------------------------------------------------------------------


def sec2():
    m, root = begin(2, 5)
    K.source(root, m, on=[(F(0, 0), END)])
    # the scanner parts only appear for the beats about them, so they don't cover the droplet
    # and the mirrors
    optics = wrap(root, "optics", [(F(3, 0), END)])
    stage = wrap(root, "stage", [(F(4, 0), END)])
    label("wavelength: DUV 193 nm, EUV 13.5 nm", (0, 810, 20), root, [(F(0, 0), F(1, 0))])
    # beat 1: the EUV source, a tin droplet hit twice by a laser
    drop = empty("droplet", root)
    ball("drop_m", (0, 0, 0), 9, m["tin"], drop, 16)
    key(drop, F(1, 0.0), "location", P(0, 330, 0))
    key(drop, F(1, 0.45), "location", P(0, 60, 0), linear=True)
    show(drop, [(F(1, 0.0), F(1, 0.5))])
    flash = empty("laser", root)
    box("laser_m", (-200, 44, -10), (200, 52, -2), m["light"], flash)
    show(flash, [(F(1, 0.45), F(1, 0.8))])
    plasma = empty("plasma", root)
    ball("plasma_m", (0, 58, 0), 28, m["plasma"], plasma, 16)
    show(plasma, [(F(1, 0.5), F(2, 0.0))])
    label("tin droplet: a CO2 laser hits it twice", (40, 300, 20), root, [(F(1, 0), F(2, 0))])
    # beat 2: mirrors, each keeping about 70%
    mirrors = [(-160.0, 180.0, -40.0), (-40.0, 110.0, 30.0), (80.0, 40.0, -30.0), (190.0, -30.0, 20.0)]
    for k, (x, y, a) in enumerate(mirrors):
        mir = empty(f"mirror{k}", root)
        box(f"mirror{k}_m", (x - 40, y - 8, -30), (x + 40, y + 8, 0), m["mirror"], mir)
        mir.rotation_euler = (0, 0, math.radians(a))
        show(mir, [(F(2, 0.0), F(3, 0.0))])
    label("multilayer mirrors: about 70% each", (-190, 260, 20), root, [(F(2, 0), F(3, 0))])
    # beat 3: the reticle and the lens, 4x
    K.reticle(optics, m)
    K.lens(optics, m, slit_on=[])
    label("reticle: one per layer", (-150, K.RET_Y + 30, 20), root, [(F(3, 0), F(4, 0))])
    label("lens: 4x smaller", (160, 380, 20), root, [(F(3, 0), F(4, 0))])
    # beat 4: the photoresist on the wafer, the stage, the overlay sensor
    wg, tiles = K.wafer(stage, m)
    no_tiles(tiles)
    K.sensor(stage, m, beam_on=[(F(4, 0), END)])
    label("photoresist: where the image lands", (0, RES_TOP + 40, 20), wg, [(F(4, 0), END)])
    camera(root, [
        ((0.0, 780.0, 0.0), 900.0, 0.30, 0.14),  # the source and its light plate
        ((40.0, 170.0, 0.0), 800.0, 0.30, 0.12),
        ((0.0, 260.0, 0.0), 1100.0, 0.25, 0.10),
        ((0.0, 380.0, 0.0), 1600.0, 0.25, 0.10),
        ((120.0, 150.0, 0.0), 1000.0, 0.30, 0.12),
    ])
    finish("sec2", page="litho")


# ---- 3: one exposure, in order ------------------------------------------------------------


def sec3():
    m, root = begin(3, 5)
    K.frame(root, m)
    K.source(root, m, on=[(F(0, 0.0), F(0, 0.6)), (F(0, 0.6), END)])
    K.reticle(root, m)
    K.lens(root, m, slit_on=[])
    wg, tiles = K.wafer(root, m)
    no_tiles(tiles)
    K.rays(root, m, 1, 0.0, 0.8, K.light_path_to_wafer, n=3, life=40)
    # the columns stand a hair proud of the resist's top and cut face, so they don't z-fight
    cols = empty("exposed_cols", root)
    for k, x in enumerate((-60.0, 0.0, 60.0)):
        box(f"col{k}", (x - 12, RES_TOP - 10, -20), (x + 12, RES_TOP + 0.8, 0.8), m["exposed"], cols)
    show(cols, [(F(2, 0.0), F(3, 0.0))])
    # develop: the same columns open (cyan: the film shows); etch: the openings reach through the film
    sink = empty("sink", root)
    for k, x in enumerate((-60.0, 0.0, 60.0)):
        box(f"dev{k}", (x - 12, RES_TOP - 10, -20), (x + 12, RES_TOP + 0.8, 0.8), m["cyan"], sink)
    show(sink, [(F(3, 0.0), F(4, 0.0))])
    etch = empty("etched", root)
    for k, x in enumerate((-60.0, 0.0, 60.0)):
        box(f"etch{k}", (x - 12, K.SUB_T, -20), (x + 12, RES_TOP + 0.8, 0.8), m["cyan"], etch)
    show(etch, [(F(4, 0.0), END)])
    label("1. the source flashes", (0, 810, 20), root, [(F(0, 0), F(1, 0))])
    label("2. the lens projects the image", (160, 380, 20), root, [(F(1, 0), F(2, 0))])
    label("3. the exposed resist changes", (0, RES_TOP + 40, 20), wg, [(F(2, 0), F(3, 0))])
    label("4. develop removes the exposed part", (0, RES_TOP + 40, 20), wg, [(F(3, 0), F(4, 0))])
    label("5. etch copies it into the film", (0, RES_TOP + 40, 20), wg, [(F(4, 0), END)])
    camera(root, [
        ((0.0, 440.0, 0.0), 1700.0, 0.30, 0.12),
        ((0.0, 430.0, 0.0), 1500.0, 0.30, 0.10),
        ((0.0, 50.0, 0.0), 560.0, 0.25, 0.16),
        ((0.0, 50.0, 0.0), 560.0, 0.25, 0.16),
        ((0.0, 50.0, 0.0), 560.0, 0.25, 0.16),
    ])
    finish("sec3", page="litho")


# ---- 4: resolution ------------------------------------------------------------------------

# half-pitch-like line widths in mm (x4 scale of 57, 16 and 10 nm), and the bar heights
TILES = [("DUV", 228.0, 228.0), ("EUV", 64.0, 64.0), ("HIGH-NA", 40.0, 40.0)]


def sec4():
    m, root = begin(4, 3)
    tiles = []
    for k, (name, w, h) in enumerate(TILES):
        x0 = -330 + 330 * k
        g = empty(f"tile{k}", root)
        box(f"tile{k}_bg", (x0 - 150, -10, -200), (x0 + 150, 230, -185), m["plinth"], g)
        pitch = w / 4  # one line (w/8) and one space (w/8)
        n = int(260 / pitch)
        for j in range(n):
            xl = x0 - 130 + j * pitch
            box(f"tile{k}_l{j}", (xl, 0, -180), (xl + w / 8, 60, 0), m["exposed"], g)
        bar = empty(f"bar{k}", root)
        box(f"bar{k}_m", (x0 + 90, 0, -40), (x0 + 130, h * 1.6, 0), m["alarm"] if k == 0 else m["exposed"], bar)
        show(g, [(F(k, 0.0), END)])
        show(bar, [(F(k, 0.2), END)])
        label(f"{name}: {['57', '16', '10'][k]} nm", (x0 - 140, 260, 20), root, [(F(k, 0.2), F(k + 1, 0.0))])
        tiles.append(g)
    camera(root, [
        ((-330.0, 60.0, -90.0), 680.0, 0.12, 0.55),
        ((0.0, 60.0, -90.0), 680.0, 0.12, 0.55),
        ((330.0, 60.0, -90.0), 680.0, 0.12, 0.55),
    ])
    finish("sec4", page="litho")


# ---- 5: depth of focus --------------------------------------------------------------------


def sec5():
    m, root = begin(5, 3)
    K.frame(root, m)
    wg, tiles = K.wafer(root, m)
    no_tiles(tiles)
    long_b = empty("band_long", root)
    tube("band_long_m", (0, RES_TOP - 150, 14), (0, RES_TOP + 150, 14), 10, m["band"], long_b, verts=12)
    show(long_b, [(F(0, 0.0), F(1, 0.0))])
    half = 150.0 * (0.33 / 0.55) ** 2
    short_b = empty("band_short", root)
    tube("band_short_m", (0, RES_TOP - half, 14), (0, RES_TOP + half, 14), 10, m["band"], short_b, verts=12)
    show(short_b, [(F(1, 0.0), F(2, 0.0))])
    # beat 2: a wafer that is not flat; the parts outside the band turn orange
    bump = empty("bump", root)
    for k in range(-3, 4):
        x = 40.0 * k
        h = 14.0 * (1 - abs(k) / 4.0)
        box(f"bump{k}", (x - 18, RES_TOP, -70), (x + 18, RES_TOP + h, 0), m["alarm"], bump)
    show(bump, [(F(2, 0.0), END)])
    label("NA 0.33: long in-focus band", (60, RES_TOP + 150, 20), root, [(F(0, 0), F(1, 0))])
    label("NA 0.55: band 2.8x shorter", (60, RES_TOP + 60, 20), root, [(F(1, 0), F(2, 0))])
    label("a bowed wafer leaves the band", (60, RES_TOP + 40, 20), root, [(F(2, 0), END)])
    camera(root, [
        ((0.0, 80.0, 0.0), 900.0, 0.25, 0.10),
        ((0.0, 80.0, 0.0), 900.0, 0.25, 0.10),
        ((0.0, 80.0, 0.0), 900.0, 0.25, 0.10),
    ])
    finish("sec5", page="litho")


# ---- 6: memory ----------------------------------------------------------------------------


def sec6():
    m, root = begin(6, 3)
    grid = empty("grid", root)
    cell = 60.0
    for i in range(6):
        for j in range(4):
            x, z = -180 + i * cell, -120 + j * cell
            box(f"cell_{i}_{j}", (x, 0, z), (x + cell - 6, 8, z + cell - 6), m["grey"], grid)
    # the cell (orange) is 3F by 2F; beat 0 shows one, beat 1 shrinks F, beat 2 doubles the count
    one = empty("one_cell", root)
    box("one_cell_m", (-180, 8, -120), (-180 + 3 * 30, 16, -120 + 2 * 30), m["cell"], one)
    show(one, [(F(0, 0.0), F(1, 0.0)), (F(2, 0.0), END)])
    key(grid, F(1, 0.0), "scale", (1, 1, 1))
    key(grid, F(1, 0.8), "scale", (0.7, 1, 0.7), linear=True)
    key(grid, END, "scale", (0.7, 1, 0.7))
    more = empty("more_cells", root)
    for i in range(3):
        box(f"more{i}", (-180 + 3 * 60 * i / 3 * 0.9 + 30, 8, 60), (-180 + 3 * 60 * i / 3 * 0.9 + 60, 16, 90), m["cell"], more)
    show(more, [(F(2, 0.0), END)])
    label("one 1T1C cell is 6F^2", (60, 120, 20), root, [(F(0, 0), F(1, 0))])
    label("F x 0.7: area x 0.49", (60, 120, 20), root, [(F(1, 0), F(2, 0))])
    label("about twice the cells", (60, 120, 20), root, [(F(2, 0), END)])
    camera(root, [
        ((0.0, 8.0, 0.0), 800.0, 0.30, 0.45),
        ((0.0, 8.0, 0.0), 800.0, 0.30, 0.45),
        ((0.0, 8.0, 0.0), 800.0, 0.30, 0.45),
    ])
    finish("sec6", page="litho")


# ---- 7: multi-patterning ------------------------------------------------------------------


def sec7():
    m, root = begin(7, 3)
    # beat 0: lines too close for one exposure merge into one smear
    smear = empty("smear", root)
    box("smear_m", (-150, 0, -40), (150, 40, 0), m["alarm"], smear)
    show(smear, [(F(0, 0.0), F(1, 0.0))])
    # beat 1: split: pink lines from mask A, cyan from mask B between them
    pink = empty("maskA", root)
    cyan = empty("maskB", root)
    for k in range(6):
        x = -125 + 50 * k
        box(f"a{k}", (x - 10, 0, -40), (x + 10, 40, 0), m["exposed"], pink)
        box(f"b{k}", (x + 25 - 10, 0, -40), (x + 25 + 10, 40, 0), m["cyan"], cyan)
    show(pink, [(F(1, 0.0), END)])
    show(cyan, [(F(1, 0.0), END)])
    # beat 2: overlay error slides mask B toward its neighbours, so the spacing goes uneven
    key(cyan, F(2, 0.0), "location", P(0, 0, 0))
    key(cyan, F(2, 0.8), "location", P(-14, 0, 0), linear=True)
    label("one exposure: lines merge", (0, 80, 20), root, [(F(0, 0), F(1, 0))])
    label("split: mask A, then mask B", (0, 80, 20), root, [(F(1, 0), F(2, 0))])
    label("overlay error between passes", (0, 80, 20), root, [(F(2, 0), END)])
    camera(root, [
        ((0.0, 30.0, 0.0), 760.0, 0.20, 0.12),
        ((0.0, 30.0, 0.0), 760.0, 0.20, 0.12),
        ((0.0, 30.0, 0.0), 760.0, 0.20, 0.12),
    ])
    finish("sec7", page="litho")


# ---- 8: who makes it ----------------------------------------------------------------------


def sec8():
    m, root = begin(8, 3)
    makers = [(-300.0, "ASML: EUV and DUV scanners"), (0.0, "Nikon: DUV scanners"), (300.0, "Canon: DUV scanners")]
    for k, (x, text) in enumerate(makers):
        g = empty(f"maker{k}", root)
        box(f"body{k}", (x - 110, 0, -120), (x + 110, 220, 0), m["steel"], g)
        glow = empty(f"glow{k}", g)
        box(f"glow{k}_m", (x - 90, 220, -100), (x + 90, 232, -20), m["gold_glow"], glow)
        show(glow, [(F(k, 0.0), F(k + 1, 0.0))])
        label(text, (x - 110, 260, 20), root, [(F(k, 0.0), F(k + 1, 0.0))])
    camera(root, [
        ((-300.0, 120.0, 0.0), 1000.0, 0.22, 0.10),
        ((0.0, 120.0, 0.0), 1000.0, 0.22, 0.10),
        ((300.0, 120.0, 0.0), 1000.0, 0.22, 0.10),
    ])
    finish("sec8", page="litho")


# ---- 9: chokepoints and risks -------------------------------------------------------------


def sec9():
    m, root = begin(9, 4)
    # beat 0: one EUV maker, two empty plinths
    tower = wrap(root, "tower", [(F(0, 0), F(1, 0))])
    box("tower_m", (-80, 0, -80), (80, 320, 0), m["steel"], tower)
    for k, x in enumerate((-300.0, 300.0)):
        box(f"plinth{k}", (x - 80, 0, -80), (x + 80, 60, 0), m["plinth"], tower)
    label("one EUV scanner maker: ASML", (100, 340, 20), root, [(F(0, 0), F(1, 0))])
    # beat 1: mirrors and the tin source are single points
    mir = empty("mirrors", root)
    for k, x in enumerate((-160.0, -60.0, 40.0, 140.0)):
        box(f"mirror{k}", (x - 40, 0, -40), (x + 40, 12, 0), m["mirror"], mir)
    show(mir, [(F(1, 0), END)])
    label("a dozen mirrors leave about 1%", (-60, 60, 20), root, [(F(1, 0), F(2, 0))])
    # beat 2: stochastic defects: few photons, random breaks along fine lines
    ph = empty("photons", root)
    for k in range(8):
        ball(f"ph{k}", (-180 + 50 * k, 260 - 25 * (k % 3), -20), 6, m["light"], ph, 8)
    show(ph, [(F(2, 0), F(3, 0))])
    defects = empty("defects", root)
    for k in range(6):
        box(f"d{k}", (-170 + 60 * k, 0, -20), (-160 + 60 * k, 20, -10), m["alarm"], defects)
    show(defects, [(F(2, 0.4), END)])
    label("stochastic: too few photons", (-60, 120, 20), root, [(F(2, 0), F(3, 0))])
    # beat 3: export rules fence off advanced scanners
    fence = empty("fence", root)
    for k in range(7):
        box(f"post{k}", (-200 + 60 * k, 0, -10), (-190 + 60 * k, 200, 0), m["alarm"], fence)
    show(fence, [(F(3, 0), END)])
    label("export controls: check current rules", (-120, 240, 20), root, [(F(3, 0), END)])
    camera(root, [
        ((0.0, 160.0, 0.0), 1100.0, 0.22, 0.10),
        ((-10.0, 30.0, -20.0), 700.0, 0.22, 0.45),
        ((0.0, 120.0, -20.0), 800.0, 0.22, 0.30),
        ((0.0, 120.0, 0.0), 900.0, 0.22, 0.12),
    ])
    finish("sec9", page="litho")


# ---- 10: sources --------------------------------------------------------------------------


def sec10():
    m, root = begin(10, 3)
    # cards: ASML product pages (beat 0), SEC filings (beat 1), patent and open notes (beat 2)
    card(root, m, -380, -560, "ASML EXE:5000, High-NA", "gold_glow", [(F(0, 0), F(1, 0))])
    card(root, m, 380, -560, "ASML: 5 things, High-NA", "gold_glow", [(F(0, 0), F(1, 0))])
    card(root, m, -380, 0, "ASML annual report 2024", "gold_glow", [(F(1, 0), F(2, 0))])
    card(root, m, 380, 0, "ASML 20-F FY2025", "gold_glow", [(F(1, 0), F(2, 0))])
    card(root, m, 0, 560, "US 6,839,125: formulas", "gold_glow", [(F(2, 0), END)])
    camera(root, [
        ((0.0, 0.0, -560.0), 3000.0, 0.0, 0.85),
        ((0.0, 0.0, 0.0), 3000.0, 0.0, 0.85),
        ((0.0, 0.0, 560.0), 3000.0, 0.0, 0.85),
    ])
    finish("sec10", page="litho")


BUILDS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9, 10: sec10}

if __name__ == "__main__":
    which = [int(a) for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(BUILDS)
    for n in which:
        BUILDS[n]()
