"""3D DRAM section 2, "The parts" (heading 2 of RND_3D_DRAM.txt).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_2.py

Writes blender/rnd_3d_dram_section_2.blend and assets/rnd_3d_dram_section_2.glb. Three 8 s beats
walking the parts table, one exhibit each:
  0 the cell   one 4F2 VCT cell pulls apart into its parts (capacitor and pad up, word-line bars out to
               the sides, bit line down, the pillar left standing), then goes back together: 1T1C, 4F2
  1 the chip   a small array lifts a hand's width off its periphery to show the Cu pads face to face,
               drops back, the bond line glows and the sense amps and decoders light (COP / PUC)
  2 stacked    a four-layer VS-DRAM block seen low from the side: a write sweeps up the layers, each
               layer's word line lighting as its sideways capacitor charges off the vertical bit line
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, empty, label  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_2"
BEATS = 3

XV, XB, XS = 0.0, 2800.0, 6400.0
NS = 4  # stacked layers

POSES = [
    ((XV, 1020.0, 0.0), 5800.0, 0.50, 0.12),
    ((XB, 250.0, 0.0), 3700.0, 0.55, 0.10),
    ((XS - 250.0, 560.0, -250.0), 5300.0, -0.42, 0.12),
]

# explode offsets (dx, dy, dz) for the cell's parts
OUT = {"cap": (0.0, 420.0, 0.0), "wl_l": (-300.0, 0.0, 0.0), "wl_r": (300.0, 0.0, 0.0), "wl_b": (0.0, 0.0, -260.0),
       "bl": (0.0, -300.0, 0.0)}
T_OUT = (0.12, 0.32)  # beat 0: pull apart
T_IN = (0.78, 0.94)  # beat 0: back together


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def explode_group(parent, name, off, objs):
    """Reparent `objs` (built at the origin frame) under a new empty that moves out by `off` and back."""
    e = empty(name, parent)
    for o in objs:
        o.parent = e
    for f, a in ((F(0, 0.0), 0.0), (F(0, T_OUT[0]), 0.0), (F(0, T_OUT[1]), 1.0), (F(0, T_IN[0]), 1.0), (F(0, T_IN[1]), 0.0)):
        K.key(e, f, "location", K.P(off[0] * a, off[1] * a, off[2] * a))
    return e


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    ob = bpy.data.objects

    # ---- beat 0: the cell, pulled apart ----
    vc = K.vct_cell(root, m, (XV, 0.0, 0.0), "vc", merge=False)
    explode_group(vc.g, "x_cap", OUT["cap"], [vc.cap, ob["vc_pad"], vc.tile])
    explode_group(vc.g, "x_wll", OUT["wl_l"], [ob["vc_wl-1"]])
    explode_group(vc.g, "x_wlr", OUT["wl_r"], [ob["vc_wl1"]])
    explode_group(vc.g, "x_wlb", OUT["wl_b"], [ob["vc_wlb"]])
    explode_group(vc.g, "x_bl", OUT["bl"], [ob["vc_base"], ob["vc_bl"], vc.bl_on])
    on(vc.charge, span(0, 0.0, 1, 0.0))
    on(vc.tile, span(0, 0.0, 1, 0.0))
    on(vc.chan_on, span(0, 0.4, 0, 0.7))
    # wl_on stays put (it would float off the moved bars): light it only once the cell is whole
    on(vc.wl_on, span(0, 0.95, 1, 0.0))
    on(vc.bl_on, span(0, 0.95, 1, 0.0))

    # ---- beat 1: the chip, cell array over its periphery ----
    bd = K.bonded_die(root, m, (XB, 0.0, 0.0), nx=3, nz=2, name="bd")
    K.lift(bd.top, [(F(1, 0.0), 0.0), (F(1, 0.08), 0.0), (F(1, 0.25), 380.0), (F(1, 0.52), 380.0), (F(1, 0.66), 0.0)])
    on(bd.line, span(1, 0.66, 2, 0.0))
    for p in bd.peri.sa_on:
        on(p, span(1, 0.74, 2, 0.0))
    for p in bd.peri.dec_on:
        on(p, span(1, 0.8, 2, 0.0))
    for i in range(3):
        on(bd.arr.cells[(i, 0)].charge, span(1, 0.0, 2, 0.0))
    on(bd.arr.bl_on[0], span(1, 0.68, 1, 0.95))
    for i, x in enumerate(bd.arr.xs[:2]):
        K.beads(root, m, f"drop{i}", [(x - 100, K.V_BASE + 30, 14.0), (x - 100, -K.PE_BOND - 60, 14.0),
                                      (x - 100, -K.PE_BOND - K.PE_ILD + 60, 14.0)], 2, 1, 0.7, 0.85, life=34, size=20.0)

    # ---- beat 2: stacked layers, a write sweeping up ----
    o = (XS, 0.0, 0.0)
    sk = K.stacked_3d(root, m, o, n=NS, nz=2, name="sk")
    on(sk.bl_on[0], span(2, 0.1, 2, 0.95))
    for k in range(NS):
        u = 0.18 + 0.17 * k
        on(sk.wl_on[k], span(2, u, 2, u + 0.15))
        for ch in sk.charges[k]:
            on(ch, span(2, u + 0.1, 3, 0.0))
    for k in (1, 3):
        path = list(reversed(K.stack_read_path(sk, o, k, -1)))
        K.beads(root, m, f"wr{k}", path, 2, 2, 0.12 + 0.17 * k, 0.17 + 0.17 * k, life=30)

    # ---- tags ----
    held = span(0, T_OUT[1], 0, T_IN[0])
    cx = XV
    for text, pos in [
        ("capacitor: holds the bit as charge", (cx + 150.0, K.V_CAP0 + 420.0 + 700.0, 0.0)),
        ("VCT pillar: source, channel, drain", (cx + 70.0, 650.0, 0.0)),
        ("word line: the gate round the pillar", (cx + 300.0 + 160.0, 480.0, 0.0)),
        ("bit line underneath", (cx + 200.0, -300.0 + 55.0, 0.0)),
    ]:
        label(text, pos, root, held)
    label("1T1C: one transistor, one capacitor", (cx - 160.0, 400.0, 0.0), root, span(0, 0.0, 0, T_OUT[0]) + span(0, T_IN[1], 1, 0.0))
    label("4F2 cell: 2F x 2F", vc.pts["tile"], root, span(0, T_IN[1], 1, 0.0))

    a = bd.arr
    label("cell array on top", (a.x1, K.V_BASE + 650.0, 0.0), root, beat(1))
    label("Cu pads in oxide: hybrid bond", (bd.pts["bond"][0], 30.0, 0.0), root, span(1, 0.2, 2, 0.0))
    label("periphery: sense amps, decoders", (bd.peri.pts["sa"][0], bd.peri.pts["sa"][1], 0.0), root, span(1, 0.72, 2, 0.0))
    label("COP: cell on periphery", (XB - 900.0, -500.0, 0.0), root, span(1, 0.5, 2, 0.0))

    W = K.S_X[3] + K.S_CAPL + 40.0
    label("VS-DRAM: cells lying on their sides", (XS - W, NS * K.S_LP + 25.0, -400.0), root, beat(2))
    label("vertical bit line", (XS - 60.0, NS * K.S_LP - 80.0, 0.0), root, beat(2))
    label("capacitor lies flat", (XS - K.S_X[3] - 600.0, 2 * K.S_LP + 130.0 + K.S_CAP_R, 0.0), root, span(2, 0.15, 3, 0.0))
    label("word line all round the channel", (XS - 260.0, 1 * K.S_LP + K.S_CH[0] - 45.0, 0.0), root, span(2, 0.3, 3, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
