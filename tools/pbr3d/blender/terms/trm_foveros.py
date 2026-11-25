"""TRM_FOVEROS: the Terms-tab overview for Intel's Foveros 3D stacking.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_foveros.py

Left/centre: a Foveros package ~20x life size, cut open at z = 0: BGA balls, laminate substrate,
C4 bumps, an active base die with TSVs, a microbump field, and three logic tiles of different
heights (compute, graphics, SoC) in mold under a lid. Right: two magnified joints side by side,
a solder microbump (~36 um pitch) and a Foveros Direct copper-to-copper hybrid bond (~9 um).

Beats:
  0 stack     the package, tiles on a base die
  1 joints    microbumps up top, TSVs through the base die, power rising
  2 talk      tile-to-tile signals run through the base die
  3 direct    microbump vs copper-to-copper bond
  4 mix       process nodes per tile, tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show, ball  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_FOVEROS"
BEATS = [
    ("Foveros stacks logic tiles on top of an active base die",
     "Instead of one big flat chip, Intel builds several smaller dies (tiles) and stacks them face-down on a base die "
     "that sits on the package substrate. The base die is a real chip too: it holds I/O, cache or power delivery, "
     "and it is the wiring hub for everything above it."),
    ("Microbumps join tiles to the base; TSVs carry power up",
     "Each tile lands on a field of tiny solder microbumps, about 36-50 microns apart in first-generation Foveros, "
     "thousands per square millimetre. Copper through-silicon vias (TSVs) punch through the base die so power and "
     "signals from the substrate can climb straight up into the tiles."),
    ("Tiles talk through the base die, not across the substrate",
     "A signal from the compute tile to the graphics tile goes down into the base die, sideways a few millimetres, and up. "
     "That path is far shorter and denser than routing across a laminate substrate, so links cost less energy per bit "
     "and the tiles behave almost like one chip."),
    ("Foveros Direct swaps solder bumps for copper-to-copper bonds",
     "Solder bumps need a gap and limit how close joints can sit. Foveros Direct polishes both dies flat and bonds copper "
     "pad to copper pad with oxide between (hybrid bonding), at about 10 microns pitch or less: roughly 10x more "
     "connections per area, lower resistance, and no gap to fill."),
    ("Each tile on its own node, one package",
     "Because tiles are separate dies, compute can use the newest node while I/O stays on a cheaper one, and small tiles "
     "yield better than one giant die. Intel uses Foveros in Meteor Lake, Ponte Vecchio and Clearwater Forest; TSMC's SoIC "
     "is the rival. Related: Intel (INTC), TSMC (TSM), Amkor (AMKR)."),
]

X0, X1 = -110.0, 110.0  # substrate
Y_SUB = (6.0, 16.0)
Y_C4 = (16.0, 20.0)
BD = (-80.0, 80.0, 20.0, 32.0)  # base die x0, x1, y0, y1
Y_UB = (32.0, 34.0)
TILES = [("compute", -76.0, -10.0, 16.0, "die"), ("gfx", -4.0, 40.0, 12.0, "hbm"), ("soc", 46.0, 76.0, 9.0, "si")]
Z0 = -60.0
J = 175.0  # joint inset centre x


def mats(m):
    m["tsv"] = mat("fv_tsv", (0.85, 0.50, 0.30), metal=0.95, rough=0.25)
    m["base"] = mat("fv_base", (0.30, 0.34, 0.44), metal=0.4, rough=0.35)
    m["oxide2"] = mat("fv_ox", (0.62, 0.70, 0.80), rough=0.25)


def package(m, root):
    g = empty("pkg", root)
    for i in range(12):
        x = X0 + 10.0 + (X1 - X0 - 20.0) * i / 11
        ball(f"bga{i}", (x, 3.0, -6.0), 3.2, m["solder"], g, 16)
    bx("sub", (X0, Y_SUB[0], Z0), (X1, Y_SUB[1], 0.0), m["substrate"], g)
    for k in range(3):
        bx(f"subcu{k}", (X0, Y_SUB[0] + 2.0 + 3.0 * k, Z0), (X1, Y_SUB[0] + 2.6 + 3.0 * k, 0.05), m["copper"], g)
    for i in range(16):
        x = BD[0] + 5.0 + (BD[1] - BD[0] - 10.0) * i / 15
        ball(f"c4_{i}", (x, 18.0, -4.0), 2.0, m["solder"], g, 12)
    bx("base", (BD[0], BD[2], Z0 + 4.0), (BD[1], BD[3], 0.0), m["base"], g)
    bx("base_metal", (BD[0], BD[3] - 2.5, Z0 + 4.0), (BD[1], BD[3], 0.05), m["copper"], g)
    tsv_x = [BD[0] + 8.0 + 9.6 * i for i in range(16)]
    for i, x in enumerate(tsv_x):
        bx(f"tsv{i}", (x - 0.8, BD[2], -4.0), (x + 0.8, BD[3] - 2.5, 0.2), m["tsv"], g)
    tops = {}
    for name, xa, xb, h, mt in TILES:
        bx(f"t_{name}", (xa, Y_UB[1], Z0 + 8.0), (xb, Y_UB[1] + h, 0.0), m[mt], g)
        bx(f"t_{name}_act", (xa, Y_UB[1], Z0 + 8.0), (xb, Y_UB[1] + 1.2, 0.06), m["copper"], g)
        n = int((xb - xa) / 3.0)
        for i in range(n):
            x = xa + 1.5 + (xb - xa - 3.0) * i / max(1, n - 1)
            ball(f"ub_{name}{i}", (x, 33.0, -2.0), 0.9, m["solder"], g, 8)
        tops[name] = ((xa + xb) / 2, Y_UB[1] + h, -20.0)
    top = Y_UB[1] + 16.0
    bx("mold_l", (BD[0] - 2.0, Y_UB[0], Z0 + 4.0), (-76.0, top, 0.0), m["mold"], g)
    bx("mold_lid", (X0 + 4.0, top + 6.0, Z0), (X1 - 4.0, top + 10.0, 0.0), m["alu"], g)
    for x in (X0 + 4.0, X1 - 8.0):
        bx(f"lidleg{x:.0f}", (x, Y_SUB[1], Z0), (x + 4.0, top + 6.0, 0.0), m["alu"], g)
    bx("tim", (BD[0], top + 4.5, Z0 + 4.0), (BD[1], top + 6.0, 0.0), m["gold"], g)
    for name, xa, xb, h, mt in TILES:
        if h < 16.0:
            bx(f"fill_{name}", (xa, Y_UB[1] + h, Z0 + 8.0), (xb, top + 4.5, -0.05), m["mold"], g)
    return tsv_x, tops


def joint(m, root, cx, direct):
    """One magnified joint between two die slabs."""
    g = empty("j_direct" if direct else "j_bump", root)
    w = 36.0
    bx(f"jb{direct}", (cx - w / 2, 10.0, -24.0), (cx + w / 2, 30.0, 0.0), m["base"], g)
    gap = 0.0 if direct else 9.0
    yt = 30.0 + gap
    bx(f"jt{direct}", (cx - w / 2, yt, -24.0), (cx + w / 2, yt + 20.0, 0.0), m["die"], g)
    if direct:
        bx("jox_b", (cx - w / 2, 28.0, -24.0), (cx + w / 2, 30.0, 0.05), m["oxide2"], g)
        bx("jox_t", (cx - w / 2, 30.0, -24.0), (cx + w / 2, 32.0, 0.05), m["oxide2"], g)
        for i in range(8):
            x = cx - w / 2 + 2.5 + (w - 5.0) * i / 7
            bx(f"jcu{i}", (x - 1.2, 27.5, -20.0), (x + 1.2, 32.5, 0.15), m["copper"], g)
    else:
        for i in range(2):
            x = cx - 8.0 + 16.0 * i
            bx(f"jpb{i}", (x - 3.0, 28.5, -16.0), (x + 3.0, 30.0, 0.1), m["copper"], g)
            bx(f"jpt{i}", (x - 3.0, yt, -16.0), (x + 3.0, yt + 1.5, 0.1), m["copper"], g)
            ball(f"jsb{i}", (x, 30.0 + gap / 2, -4.0), 4.0, m["solder"], g, 16)
        bx("jfill", (cx - w / 2, 30.0, -24.0), (cx + w / 2, yt, -8.5), m["mold"], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    C.pcb(m, root, "board", -140.0, 220.0, -110.0)
    tsv_x, tops = package(m, root)
    jb = joint(m, root, J - 22.0, False)
    jd = joint(m, root, J + 22.0, True)
    for o in (jb, jd):
        D.present(o, [(F(3, 0.0), F(5, 0))])
    C.magnify(m, root, (-30.0, 33.0, 0.5), (J - 42.0, 30.0, -10.0), 2.0)
    # power up the TSVs into the tiles
    pw = [[(x, 3.0, 4.0), (x, 18.0, 1.0), (x, 34.0, 1.0), (x, 42.0, 1.0)] for x in tsv_x[::2]]
    for k, p in enumerate(pw):
        run(root, f"pw{k}", p, 3, 1.3, m["h_amber"], [1, 4], 0.02 * k, 0.7, 36)
    # tile-to-tile signals through the base die
    for k in range(5):
        xa = -60.0 + 8.0 * k
        xb = 6.0 + 7.0 * k
        p = [(xa, 40.0, 1.0), (xa, 30.5, 1.0), (xb, 30.5, 1.0), (xb, 40.0, 1.0)]
        run(root, f"sg{k}", p, 3, 1.4, m["sig"], 2, 0.05 * k, 0.75, 34)
        run(root, f"sgb{k}", list(reversed([(x + 46.0 - 6.0 + 2 * k, y, z) for x, y, z in p])), 2, 1.4, m["e_blue"], 2, 0.3, 0.8, 34)
    # long detour path for comparison (dim): across the substrate
    run(root, "detour", [(-40.0, 34.0, 2.0), (-40.0, 12.0, 2.0), (60.0, 12.0, 2.0), (60.0, 34.0, 2.0)], 3, 0.8, m["dim_glow"], 2, 0.1, 0.6, 70)
    for k, x in enumerate((-43.0, 18.0, 61.0)):
        rise(root, f"heat{k}", (x, 72.0, -20.0), 4, 1.0, m["heat"], [0, 4], 0.1, 0.8, 25.0, 50, (14.0, 8.0))
    # direct-bond current: many thin beads vs two fat ones
    for i in range(8):
        x = J + 22.0 - 15.5 + 31.0 * i / 7
        run(root, f"dj{i}", [(x, 14.0, 1.0), (x, 46.0, 1.0)], 2, 0.6, m["sig"], 3, 0.3 + 0.03 * i, 0.9, 30)
    for i in range(2):
        x = J - 22.0 - 8.0 + 16.0 * i
        run(root, f"bj{i}", [(x, 14.0, 5.0), (x, 46.0, 5.0)], 3, 0.9, m["h_amber"], 3, 0.3, 0.9, 40)
    C.tags(root, {
        0: [("compute tile", (tops["compute"][0], tops["compute"][1], 0.0)), ("graphics tile", (tops["gfx"][0], tops["gfx"][1], 0.0)),
            ("active base die", (-70.0, 26.0, 0.0)), ("package substrate", (90.0, 11.0, 0.0))],
        1: [("microbumps ~36 um pitch", (-40.0, 33.0, 0.0)), ("TSVs through base die", (tsv_x[3], 24.0, 0.2)),
            ("C4 bumps to substrate", (60.0, 18.0, 0.0))],
        2: [("down, across, up: mm not cm", (-20.0, 30.5, 1.0)), ("vs. through the substrate", (60.0, 12.0, 0.0)),
            ("lower energy per bit", (tops["gfx"][0], tops["gfx"][1], 0.0))],
        3: [("solder microbump", (J - 22.0, 52.0, 0.0)), ("Cu-Cu hybrid bond", (J + 22.0, 52.0, 0.0)),
            ("~10x joints per mm2", (J + 22.0, 30.0, 0.2)), ("gap filled with underfill", (J - 22.0, 34.0, -8.0))],
        4: [("newest node: compute", (tops["compute"][0], tops["compute"][1], 0.0)), ("older node: I/O, SoC", (tops["soc"][0], tops["soc"][1], 0.0)),
            ("INTC, TSM, AMKR", (0.0, 70.0, 0.0))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 34.0, -25.0), 200.0, 0.30, 0.30),
        [(0.0, frame((-25.0, 28.0, -6.0), 150.0, 0.15, 0.15))],
        frame((0.0, 30.0, -6.0), 150.0, 0.05, 0.08),
        frame((J, 30.0, -8.0), 100.0, 0.15, 0.12),
        frame((30.0, 32.0, -20.0), 300.0, 0.25, 0.30),
    ], root)


if __name__ == "__main__":
    build()
