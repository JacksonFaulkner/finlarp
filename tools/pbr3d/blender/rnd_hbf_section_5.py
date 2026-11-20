"""HBF section 5, "Inside the stack" (heading 5 of tui/src/screens/diagrams_pages/RND_HBF.txt), in
the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_5.py

Writes blender/rnd_hbf_section_5.blend and assets/rnd_hbf_section_5.glb. One beat is 8 s.

Beats (match diagrams_nodes/hbf/sections/s5.rs):
  0 16 dies   one HBF stack, its dies spreading so all 16 can be counted: 256 Gb each, 512 GB
  1 CBA       the top die rises; its array layer lifts off its CMOS layer, then bonds back
  2 vs HBM    an 8-high HBM stack appears beside it at the same height; reads run down the stack
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, TSV_X  # noqa: E402
from rnd_hbf_kit import HBF_TOP, N_DIES, nand_bottom  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_5"
BEATS = 3

FX = 250.0  # the HBF stack
HX = -250.0  # the HBM stack beside it in beat 2

POSES = [
    ((FX, 300.0, 0.0), 1500.0, 0.30, 0.12),
    ((FX, 580.0, 0.0), 820.0, 0.30, 0.10),
    ((0.0, 320.0, 0.0), 1800.0, 0.20, 0.12),
]

TOP_LIFT = 110.0
SPLIT = 70.0


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.gbox("interposer", (-700.0, -120.0, -400.0), (700.0, 0.0, 0.0), m["interposer"], root)

    s = K.flash_stack(root, m, FX, "hbf", ucie=0)
    for bd in s.bonds:
        show(bd, [])
    for b in s.bumps:
        show(b, span(0, 0.2, 1, 0.0))
    for k, d in enumerate(s.dies):
        keys = [(F(0, 0.1), 0.0), (F(0, 0.45), 9.0 * (k + 1)), (F(0, 0.9), 0.0)]
        if k == N_DIES - 1:
            keys += [(F(1, 0.05), 0.0), (F(1, 0.25), TOP_LIFT), (F(1, 0.85), TOP_LIFT), (F(1, 0.98), 0.0)]
        for f, a in keys:
            HK.key(d, f, "location", P(0, a, 0))
    a15 = s.arrays[N_DIES - 1]
    for f, a in [(F(1, 0.25), 0.0), (F(1, 0.4), SPLIT), (F(1, 0.55), SPLIT), (F(1, 0.68), 0.0)]:
        HK.key(a15, f, "location", P(0, a, 0))
    show(s.bonds[N_DIES - 1], span(1, 0.68, 1, 0.85))

    # beat 2: an 8-high HBM stack beside it, the same height, and a height line across both
    h = HK.stack(root, m, HX, 8, "hbm", phy=0)
    show(h.g, beat(2))
    line = HK.gbox("height", (HX - 230.0, HBF_TOP + 2.0, -60.0), (FX + 230.0, HBF_TOP + 8.0, -20.0), m["limit"], root)
    show(line, span(2, 0.2, 3, 0.0))
    for i, tx in enumerate(TSV_X):
        HK.dots(root, m, f"rd{i}_", [(FX + tx, HBF_TOP - 8, 0.0), (FX + tx, 30.0, 0.0)], 3, "page", 2, 0.35, 0.8, 70, size=12.0)

    top_y = nand_bottom(N_DIES - 1) + TOP_LIFT
    tags = {
        0: [("16 NAND dies", (FX + BASE_HALF, 420.0, 0.0)), ("256 Gb a die", (FX + BASE_HALF, 250.0, 0.0)),
            ("512 GB a stack", (FX - BASE_HALF + 20, 520.0, 0.0)), ("base die", (FX - BASE_HALF - 10, 35.0, 0.0))],
        2: [("HBM: 8 DRAM dies", (HX - BASE_HALF - 10, 420.0, 0.0)), ("HBF: 16 NAND dies", (FX + BASE_HALF, 420.0, 0.0))],
    }
    late = {
        1: [("CBA: logic bonded under array", (FX - 190.0, top_y + 10.0, 0.0), 0.62)],
        2: [("height close to HBM4", (0.0, HBF_TOP + 20.0, -40.0), 0.25), ("1.6 TB/s read target", (FX + BASE_HALF, 150.0, 0.0), 0.4)],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))
    for i, items in late.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))
    # the two layer tags only while the layers are apart
    label("CMOS logic layer", (FX + 190.0, top_y + 3.0, 0.0), root, span(1, 0.3, 1, 0.66))
    label("NAND array layer", (FX + 190.0, top_y + 70.0, 0.0), root, span(1, 0.3, 1, 0.66))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
