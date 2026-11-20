"""R&D HBF zoom-in a, "the stack cut open", in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_zoom_a.py

Writes blender/rnd_hbf_zoom_a.blend and assets/rnd_hbf_zoom_a.glb. One beat is 8 s.

One 16-high HBF stack (rnd_hbf_kit.py) on a slab of interposer, cut open at z = 0.

Beats (match diagrams_nodes/hbf/zooms/a.rs):
  0 whole      the stack: 16 NAND dies, TSVs, the base die and its UCIe strip
  1 spread     the dies pull apart: microbumps between them, 16 x 256 Gb = 512 GB
  2 beside HBM an 8-high HBM stack beside it: about the same height
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF  # noqa: E402
from rnd_hbf_kit import HBF_TOP  # noqa: E402

PAGE = "rnd_hbf"
NAME = "zoom_a"
BEATS = 3

SX = 850.0  # the HBF stack
HX = 350.0  # the HBM stack that joins it in beat 2
STEP = 12.0  # how far die k rises per step in beat 1

POSES = [
    ((SX, 290.0, 0.0), 1450.0, 0.30, 0.12),
    ((SX, 380.0, 0.0), 1650.0, 0.30, 0.12),
    ((600.0, 310.0, 0.0), 2000.0, 0.20, 0.12),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.gbox("slab", (50.0, -90.0, -400.0), (1300.0, 0.0, 0.0), m["interposer"], root)

    s = K.flash_stack(root, m, SX, "hbf", ucie=-1)
    for bd in s.bonds:
        show(bd, [])
    for b in s.bumps:
        show(b, span(1, 0.15, 2, 0.0))
    for k, d in enumerate(s.dies):
        for f, a in [(F(1, 0.1), 0.0), (F(1, 0.45), STEP * (k + 1)), (F(1, 0.92), 0.0)]:
            HK.key(d, f, "location", P(0, a, 0))

    hbm = HK.stack(root, m, HX, 8, "hbm", phy=0)
    show(hbm.g, span(2, 0.1, 3, 0.0))
    HK.limit_plane(root, m, HX - BASE_HALF - 30, SX + BASE_HALF + 30, HBF_TOP + 8, z0=-200.0,
                   name="same_height", intervals=span(2, 0.4, 3, 0.0))

    left = SX - BASE_HALF - 10
    right = SX + BASE_HALF + 10
    tags = {
        0: [("16 NAND dies", (right, 400.0, 0.0), 0.05), ("TSVs through every die", (SX - 110.0, 470.0, 0.0), 0.2),
            ("base die", (right, 35.0, 0.0), 0.35), ("UCIe link strip", (left, 35.0, 0.0), 0.5)],
        1: [("microbumps between dies", (left, 300.0, 0.0), 0.3), ("256 Gb a die", (right, 420.0, 0.0), 0.4),
            ("16 x 256 Gb = 512 GB", (right, 200.0, 0.0), 0.55)],
        2: [("HBM: 8 DRAM dies", (HX - BASE_HALF - 10, 300.0, 0.0), 0.15), ("HBF: 16 NAND dies", (right, 300.0, 0.0), 0.15),
            ("about the same height", (600.0, HBF_TOP + 40.0, 0.0), 0.45)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
