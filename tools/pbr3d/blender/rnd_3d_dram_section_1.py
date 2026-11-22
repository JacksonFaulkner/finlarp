"""3D DRAM section 1, "What it is: DRAM cells built upward" (heading 1 of RND_3D_DRAM.txt).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_1.py

Writes blender/rnd_3d_dram_section_1.blend and assets/rnd_3d_dram_section_1.glb. Three 8 s beats,
single cells rather than the overview's arrays:
  0 flat       one planar cell alone: transistor flat in the silicon, its 6F2 tile glowing above
  1 step one   a VCT cell rises out of the floor beside it: the transistor stands up, 4F2 tile
  2 step two   layers of sideways cells drop one by one onto a stack, the way 3D NAND is built
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, empty, label  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_1"
BEATS = 3

XP, XV, XS = -1000.0, 0.0, 950.0
N = 6  # stacked layers drawn
CAPL = 700.0  # shorter lateral capacitors so the stack sits beside the single cells

POSES = [
    ((XP, 960.0, 0.0), 6000.0, 0.40, 0.17),
    ((XP * 0.5, 960.0, 0.0), 6300.0, 0.28, 0.16),
    ((550.0, 980.0, -250.0), 6900.0, 0.22, 0.16),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)

    # ---- the planar cell, there all along ----
    pc = K.planar_cell(root, m, (XP, 0.0, 0.0), "pc")
    on(pc.charge, span(0, 0.0, 3, 0.0))
    on(pc.tile, span(0, 0.15, 3, 0.0))
    on(pc.wl_on, span(0, 0.45, 0, 0.9))
    on(pc.chan_on, span(0, 0.5, 0, 0.9))
    on(pc.bl_on, span(0, 0.6, 0, 0.95))
    K.beads(root, m, "pread", pc.read_path, 3, 0, 0.5, 0.7, life=55)

    # ---- the VCT cell rises out of the floor in beat 1 ----
    vsw = K.hidden("vct_sw", root)
    on(vsw, span(1, 0.0, 3, 0.0))
    vl = empty("vct_lift", vsw)
    K.lift(vl, [(F(1, 0.0), -2600.0), (F(1, 0.05), -2600.0), (F(1, 0.32), 0.0)])
    vc = K.vct_cell(vl, m, (XV, 0.0, 0.0), "vc")
    on(vc.charge, span(1, 0.3, 3, 0.0))
    on(vc.tile, span(1, 0.35, 3, 0.0))
    on(vc.wl_on, span(1, 0.5, 1, 0.92))
    on(vc.chan_on, span(1, 0.55, 1, 0.92))
    on(vc.bl_on, span(1, 0.62, 1, 0.95))
    K.beads(root, m, "vread", vc.read_path[:3] + [(XV - 520.0, vc.read_path[2][1], 12.0)], 3, 1, 0.55, 0.75, life=50)

    # ---- the stack builds layer by layer in beat 2 ----
    ssw = K.hidden("stack_sw", root)
    on(ssw, span(2, 0.0, 3, 0.0))
    sk = K.stacked_3d(ssw, m, (XS, 0.0, 0.0), n=N, nz=2, name="sk", mirror=False, cap_l=CAPL)
    for k, lg in enumerate(sk.layers):
        f0 = F(2, 0.04 + 0.075 * k)
        K.lift(lg, [(F(2, 0.0), 2600.0), (f0, 2600.0), (f0 + 14, 0.0)])
    ft = F(2, 0.04 + 0.075 * N)
    K.lift(sk.layers_top, [(F(2, 0.0), 2600.0), (ft, 2600.0), (ft + 14, 0.0)])
    for k in range(N):
        for ch in sk.charges[k]:
            on(ch, span(2, 0.08 + 0.075 * k, 3, 0.0))
    on(sk.bl_on[0], span(2, 0.62, 2, 0.95))
    on(sk.wl_on[4], span(2, 0.58, 2, 0.9))
    K.beads(root, m, "sread", K.stack_read_path(sk, (XS, 0.0, 0.0), 4, 1), 3, 2, 0.6, 0.78, life=45)

    # ---- tags ----
    tags = {
        0: [("transistor lies flat in the silicon", (XP - 300.0, -250.0, 0.0)),
            ("capacitor holds the bit", (XP + 170.0, 1400.0, 0.0))],
        1: [("transistor stands up: a pillar", (XV + 70.0, 400.0, 0.0)),
            ("capacitor right on top", (XV + 150.0, 1300.0, 0.0))],
        2: [("vertical bit line through the layers", (XS + 60.0, 1300.0, 0.0)),
            ("4F2 VCT cell", (XV - 150.0, 1700.0, 0.0))],
    }
    late = {
        0: [("6F2 floor space per bit", pc.pts["tile"], 0.2)],
        1: [("4F2: less floor per bit", vc.pts["tile"], 0.4),
            ("Samsung 16 Gb chip: ISSCC 2026", (XV + 200.0, -200.0, 0.0), 0.6)],
        2: [("layers stacked like 3D NAND", (XS + 1200.0, 900.0, 0.0), 0.5),
            ("Samsung roadmap: early 2030s", (XS + 600.0, K.stacked_top(N) + 20.0, -300.0), 0.7)],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))
    for i, items in late.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
