"""HBF zoom-in c, the UCIe link, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_zoom_c.py

Writes blender/rnd_hbf_zoom_c.blend and assets/rnd_hbf_zoom_c.glb. One beat is 8 s.

The overview's package (rnd_hbf_kit.py) with the camera held on the inner HBF stack's base die,
its link strip, the interposer between it and the GPU, and the GPU's edge. The link's wires are
drawn on the interposer's cut face.

Beats (match diagrams_nodes/hbf/zooms/c.rs):
  0 base die   reads run down the TSVs and arrive at the base die
  1 the link   data leaves the link strip, crosses the interposer and climbs into the GPU
  2 grades     three lanes light in turn, thin to dense: the spec's three bandwidth grades
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, label, mat, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, GPU_X, TSV_X  # noqa: E402
from rnd_hbf_kit import HBF_TOP, HBF_XS  # noqa: E402

PAGE = "rnd_hbf"
NAME = "zoom_c"
BEATS = 3

SX = HBF_XS[0]  # the inner HBF stack
LINK_X = SX - BASE_HALF + 17.0  # middle of its link strip, on the GPU side
LANE_YS = (-28.0, -60.0, -92.0)  # the three lanes on the interposer's cut face

POSES = [
    ((760.0, 260.0, 0.0), 1250.0, 0.28, 0.12),
    ((610.0, 10.0, 0.0), 680.0, 0.22, 0.10),
    ((610.0, -10.0, 0.0), 700.0, 0.18, 0.08),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def lane(root, m, name, y, mat_key, grow=0.0):
    """A wire on the interposer's cut face from under the link strip to under the GPU's edge.
    `grow` fattens the lit copy so it covers the copper one instead of z-fighting with it."""
    return HK.gbox(name, (GPU_X - 30.0 - grow, y - 4.0 - grow, -6.0), (LINK_X + 6.0 + grow, y + 4.0 + grow, 1.5 + 2 * grow),
                   m[mat_key], root)


def link_path(y):
    return [(LINK_X, 40.0, 4.0), (LINK_X, y, 4.0), (GPU_X - 20.0, y, 4.0), (GPU_X - 20.0, 60.0, 4.0)]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    m["wire"] = mat("link_wire", (0.80, 0.55, 0.30), metal=0.8, rough=0.35)
    m["lane_lit"] = mat("lane_lit", (1.0, 0.85, 0.45), emit=(1.0, 0.8, 0.35), strength=2.2)
    HK.package(root, m)
    stacks = [K.flash_stack(root, m, x, f"hbf{int(x)}", ucie=-1) for x in HBF_XS]
    for s in stacks:
        for bd in s.bonds:
            show(bd, [])

    # the three lanes: copper always, each lit from its own moment in beat 2
    for i, y in enumerate(LANE_YS):
        lane(root, m, f"lane{i}", y, "wire")
        lit = lane(root, m, f"lane_lit{i}", y, "lane_lit", grow=1.5)
        show(lit, span(2, 0.05 + 0.3 * i, 3, 0.0))

    # beat 0: reads down the TSVs into the base die
    for i, tx in enumerate(TSV_X):
        HK.dots(root, m, f"rd{i}_", [(SX + tx, HBF_TOP - 8, 0.0), (SX + tx, 30.0, 0.0)],
                4, "page", 0, 0.08, 0.7, 60, size=12.0)
    # beat 1: data leaves the strip, crosses on the middle lane and climbs into the GPU
    HK.dots(root, m, "x_", link_path(LANE_YS[1]), 6, "data", 1, 0.1, 0.8, 70, size=11.0)
    # beat 2: one lane per grade, each denser than the last
    for i, (y, n) in enumerate(zip(LANE_YS, (2, 5, 10))):
        u0 = 0.05 + 0.3 * i
        HK.dots(root, m, f"g{i}_", link_path(y), n, "data", 2, u0, min(0.95, u0 + 0.3), 45, size=9.0)

    tags = {
        0: [("reads down the TSVs", (SX + BASE_HALF, 360.0, 0.0)), ("base die", (SX + 120.0, 35.0, 0.0)),
            ("link strip, GPU side", (LINK_X, 60.0, 0.0))],
        1: [("UCIe link (per trade press)", (LINK_X, 75.0, 0.0)), ("across the interposer", (620.0, LANE_YS[1], 0.0)),
            ("xPU-HBF host interface", (GPU_X + 20.0, -110.0, 4.0)), ("into the GPU", (GPU_X - 60.0, 90.0, 4.0))],
    }
    late = {
        2: [("grade 1: ~0.4 TB/s", (LINK_X + 30.0, LANE_YS[0], 0.0), 0.08),
            ("grade 2", (LINK_X + 30.0, LANE_YS[1], 0.0), 0.38),
            ("grade 3: up to 3.0 TB/s", (LINK_X + 30.0, LANE_YS[2], 0.0), 0.68),
            ("first-gen target: 1.6 TB/s", (GPU_X - 30.0, 120.0, 4.0), 0.7)],
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
    finish(NAME, page=PAGE)
