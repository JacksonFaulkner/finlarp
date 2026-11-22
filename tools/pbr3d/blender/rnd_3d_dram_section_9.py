"""3D DRAM section 9, "Who is building it, timing and risks" (heading 9 of
tui/src/screens/diagrams_pages/RND_3D_DRAM.txt), in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_9.py

Writes blender/rnd_3d_dram_section_9.blend and assets/rnd_3d_dram_section_9.glb. One beat is 8 s.

Two rows of plinths, each carrying a small cut-open structure from rnd_3d_dram_kit.py: Samsung's
reported node road (10a, 10b, 10c with 4F2 VCT cells, 10d with stacked layers), and one plinth per
company with the structure it is building.

Beats (match diagrams_nodes/dram3d/sections/s9.rs):
  0 the road   Samsung's reported plan: plinths 10a to 10d light in turn as a bead runs the road;
               4F2 VCT on 10a-10c, stacked 3D DRAM from 10d; dates are press targets
  1 who        five plinths: Samsung (VCT), SK hynix (VCT on bonded periphery), Micron (stays
               planar), CXMT (VCT), NEO Semiconductor (stacked IGZO layers, a claim)
  2 risks      a red "not on sale" line runs along the plinths, process-step slabs pile up beside
               the VCT cell (extra steps eat the density gain) and ghost layers keep climbing over
               the stacked block (it needs dozens to hundreds of layers to pay)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, empty, key, label, mat  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_9"
BEATS = 3

CAP_H = 500.0
RX = (0.0, 1500.0, 3000.0, 4700.0)  # beat 0: nodes 10a, 10b, 10c, 10d
RU = (0.08, 0.28, 0.48, 0.68)  # when each node lights
CX = (7600.0, 9200.0, 10800.0, 12400.0, 14200.0)  # beat 1: Samsung, SK hynix, Micron, CXMT, NEO
PL_Y = -260.0  # plinth top (structures stand on it)
SK_CAPL = 420.0
SK_W = K.S_X[3] + SK_CAPL + 40.0

POSES = [
    ((2650.0, 450.0, -300.0), 11500.0, 0.55, 0.16),
    ((11150.0, 550.0, -300.0), 14500.0, 0.45, 0.14),
    ((11150.0, 800.0, -300.0), 14500.0, -0.42, 0.20),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def plinth(root, m, x, half, name, rim_ivs=None):
    """A plinth under a structure, its top at PL_Y; a glowing rim switched on for rim_ivs."""
    box(f"{name}_pl", (x - half, PL_Y - 160.0, -520.0), (x + half, PL_Y, 120.0), m["d9_plinth"], root)
    if rim_ivs:
        g = K.hidden(f"{name}_rim", root)
        box(f"{name}_rimf", (x - half - 10, PL_Y - 40.0, 112.0), (x + half + 10, PL_Y + 6.0, 132.0), m["tile_edge2"], g)
        on(g, rim_ivs)


def vct_on(root, m, x, name, charge_ivs=None):
    """A small VCT cell standing on a plinth (origin raised so its base sits on PL_Y)."""
    c = K.vct_cell(root, m, (x, PL_Y + K.V_BASE, 0.0), name=name, tile=False, cap_h=CAP_H)
    if charge_ivs:
        on(c.charge, charge_ivs)
    return c


def road(root, m):
    """Beat 0: Samsung's reported node road."""
    g = K.hidden("road", root)
    on(g, beat(0))
    cells = []
    for i, (x, u) in enumerate(zip(RX[:3], RU)):
        plinth(g, m, x, 520.0, f"r{i}", span(0, u, 1, 0.0))
        cells.append(vct_on(g, m, x, f"r{i}c", span(0, u, 1, 0.0)))
    plinth(g, m, RX[3], SK_W + 140.0, "r3", span(0, RU[3], 1, 0.0))
    sk = K.stacked_3d(g, m, (RX[3], PL_Y, 0.0), n=4, nz=1, name="r3s", cap_l=SK_CAPL)
    for k in range(4):
        for ch in sk.charges[k]:
            on(ch, span(0, RU[3] + 0.03 * k, 1, 0.0))
    # the road: a strip along the plinths' front, a bead running it node to node
    box("road_strip", (RX[0] - 600.0, PL_Y - 180.0, 140.0), (RX[3] + SK_W + 200.0, PL_Y - 150.0, 300.0), m["sti"], g)
    K.beads(root, m, "road_b", [(RX[0] - 500.0, PL_Y - 140.0, 220.0), (RX[3] + 200.0, PL_Y - 140.0, 220.0)],
            1, 0, 0.04, 0.04, life=int(F(0, 0.66) - F(0, 0.04)), size=40.0)
    return cells, sk


def companies(root, m):
    """Beats 1-2: one plinth per company with what it is building."""
    g = K.hidden("who", root)
    on(g, span(1, 0.0, 3, 0.0))
    for i, x in enumerate(CX):
        half = SK_W + 120.0 if i == 4 else 540.0
        plinth(g, m, x, half, f"c{i}", span(1, 0.08 + 0.12 * i, 3, 0.0))
    ss = vct_on(g, m, CX[0], "c0c", span(1, 0.08, 3, 0.0))
    # SK hynix: the VCT cell on a bonded periphery slab (purple), bond line lit
    box("c1_peri", (CX[1] - 300.0, PL_Y, -300.0), (CX[1] + 300.0, PL_Y + 160.0, 0.0), m["die_peri"], g)
    box("c1_bond", (CX[1] - 304.0, PL_Y + 156.0, -304.0), (CX[1] + 304.0, PL_Y + 168.0, 4.0), m["bond"], g)
    c1 = K.vct_cell(g, m, (CX[1], PL_Y + 168.0 + K.V_BASE, 0.0), name="c1c", tile=False, cap_h=CAP_H)
    on(c1.charge, span(1, 0.2, 3, 0.0))
    # Micron: today's planar cell
    pc = K.planar_cell(g, m, (CX[2], PL_Y + K.PL_SI, 0.0), name="c2p", tile=False, cap_h=900.0)
    on(pc.charge, span(1, 0.32, 3, 0.0))
    cx_ = vct_on(g, m, CX[3], "c3c", span(1, 0.44, 3, 0.0))
    # NEO: a stacked block (its cells are IGZO in the claim; drawn with the kit's stacked cell)
    neo = K.stacked_3d(g, m, (CX[4], PL_Y, 0.0), n=6, nz=1, name="c4s", cap_l=SK_CAPL)
    for k in range(6):
        for ch in neo.charges[k]:
            on(ch, span(1, 0.56 + 0.02 * k, 3, 0.0))
    return ss, c1, pc, cx_, neo


def risks(root, m, neo):
    """Beat 2: not on sale; extra process steps; layers still to climb."""
    line = K.hidden("rk_line", root)
    box("rk_line_m", (CX[0] - 700.0, PL_Y - 120.0, 136.0), (CX[4] + SK_W + 200.0, PL_Y - 80.0, 170.0), m["wall"], line)
    on(line, span(2, 0.05, 3, 0.0))
    # extra steps: slabs drop one by one onto a pile between Samsung's and SK hynix's plinths
    px = 0.5 * (CX[0] + CX[1])
    steps = mat("d9_step", (0.80, 0.42, 0.36), rough=0.5)
    for k in range(7):
        sg = K.hidden(f"rk_step{k}", root)
        mv = empty(f"rk_step_mv{k}", sg)
        y = PL_Y + k * 90.0
        box(f"rk_step_m{k}", (px - 220.0 + 8 * (k % 2), y, -360.0), (px + 220.0 - 8 * (k % 2), y + 80.0, -60.0), steps, mv)
        u = 0.25 + 0.05 * k
        key(mv, F(2, u), "location", P(0, 500.0, 0))
        key(mv, F(2, u + 0.04), "location", P(0, 0.0, 0))
        on(sg, span(2, u, 3, 0.0))
    box("rk_floor", (px - 260.0, PL_Y - 160.0, -400.0), (px + 260.0, PL_Y, -20.0), m["d9_plinth"], root)
    # layers still to climb: ghost plates keep appearing above the NEO block
    ghost = mat("d9_ghost", (0.55, 0.58, 0.66), rough=0.6)
    top = PL_Y + K.stacked_top(6)
    for k in range(8):
        gg = K.hidden(f"rk_ghost{k}", root)
        y = top + 40.0 + k * 130.0
        box(f"rk_ghost_m{k}", (CX[4] - SK_W, y, -K.S_ZP / 2), (CX[4] + SK_W, y + 30.0, 0.0), ghost, gg)
        on(gg, span(2, 0.45 + 0.05 * k, 3, 0.0))
    return px, top + 40.0 + 8 * 130.0


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    m["d9_plinth"] = mat("d9_plinth", (0.26, 0.28, 0.34), rough=0.7)
    cells, sk = road(root, m)
    ss, c1, pc, cx_, neo = companies(root, m)
    px, gtop = risks(root, m, neo)

    ctop = PL_Y + K.V_BASE + K.V_CAP0 + CAP_H
    stop4 = PL_Y + K.stacked_top(4)
    late = {
        0: [("10a: first node below 10 nm class", (RX[0], ctop + 40.0, 0.0), 0.08),
            ("4F2 VCT across 10a, 10b, 10c", (RX[2], ctop + 40.0, 0.0), 0.48),
            ("3D DRAM from 10d", (RX[3] + SK_W, stop4, 0.0), 0.68),
            ("10a: mass production 2028 (target)", (RX[0] - 520.0, PL_Y - 80.0, 120.0), 0.2)],
        1: [("Samsung (005930.KS): VCT", (CX[0], ctop + 40.0, 0.0), 0.08),
            ("SK hynix (000660.KS): 4F2 at 10b (press)", (CX[1] + 300.0, PL_Y + 120.0, 0.0), 0.2),
            ("Micron (MU): skips 4F2", (CX[2], PL_Y + K.PL_SI + K.PL_CAP0 + 900.0, 0.0), 0.32),
            ("CXMT: 4F2 DDR5, end-2026 plan", (CX[3], ctop + 40.0, 0.0), 0.44),
            ("NEO: IGZO, 128 layers (claim)", (CX[4] + SK_W, PL_Y + K.stacked_top(6), 0.0), 0.56)],
        2: [("none on sale: dates are targets", (CX[2] + 800.0, PL_Y - 100.0, 150.0), 0.08),
            ("extra steps can eat the gain", (px, PL_Y + 7 * 90.0, -60.0), 0.6),
            ("needs dozens to hundreds of layers", (CX[4] - SK_W, gtop, 0.0), 0.8)],
    }
    for i, items in late.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
