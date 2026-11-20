"""R&D HBF page, section 6 "The spec": heading 6 of diagrams_pages/RND_HBF.txt, in the
picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_6.py

Writes blender/rnd_hbf_section_6.blend and assets/rnd_hbf_section_6.glb. One beat is 8 s.

An 8-high and a 16-high HBF stack on an interposer beside a GPU, cut open at z = 0
(rnd_hbf_kit.py pieces).

Beats (match diagrams_nodes/hbf/sections/s6.rs):
  0 two sizes  the spec's two stack configurations, 8-high and 16-high, up to 512 GB
  1 grades     three bandwidth grades as bars, about 0.4 to 3.0 TB/s; reads run down the stack
  2 interface  the base die's link strip lights and data crosses to the GPU: the xPU-HBF interface
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, box, empty, label, show, tube  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, BASE_T, DIE_HALF, TSV_X, TSV_R, BUMP_R  # noqa: E402
from rnd_hbf_kit import CMOS_T, ARRAY_T, NB_T, STRINGS, nand_bottom, nand_top  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_6"
BEATS = 3

X8, X16 = -350.0, 300.0  # the 8-high and the 16-high stack
GPU_X0, GPU_X1, GPU_Y1, GPU_Z = 680.0, 1120.0, 380.0, 400.0
BAR_XS = (-1250.0, -1100.0, -950.0)  # the three grade bars, low to high
BAR_HS = (70.0, 260.0, 525.0)  # ~0.4, a middle grade, ~3.0 TB/s (only the ends are labelled)

POSES = [
    ((0.0, 290.0, 0.0), 2700.0, 0.28, 0.14),
    ((-430.0, 300.0, 0.0), 3600.0, 0.22, 0.14),
    ((330.0, 260.0, 0.0), 3100.0, 0.24, 0.16),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def stack(root, m, x, n, name, ucie=1):
    """An n-high HBF stack (rnd_hbf_kit.flash_stack's dies, any count), cut at z = 0."""
    g = empty(name, root)
    box(f"{name}_base_die", (x - BASE_HALF, 0, -BASE_HALF), (x + BASE_HALF, BASE_T, 0), m["base"], g)
    lo, hi = HK.span(x + ucie * (BASE_HALF - 36), x + ucie * (BASE_HALF + 2))
    box(f"{name}_ucie", (lo, 10, -BASE_HALF + 40), (hi, BASE_T - 10, -40), m["ucie"], g)
    for k in range(n):
        bot = nand_bottom(k)
        mid, top = bot + CMOS_T, bot + CMOS_T + ARRAY_T
        box(f"{name}_cmos{k}", (x - DIE_HALF, bot, -DIE_HALF), (x + DIE_HALF, mid, 0), m["cmos"], g)
        box(f"{name}_array{k}", (x - DIE_HALF, mid, -DIE_HALF), (x + DIE_HALF, top, 0), m["array"], g)
        for s in range(STRINGS):
            sx = x - DIE_HALF + 2 * DIE_HALF * (s + 0.5) / STRINGS
            box(f"{name}_str{k}_{s}", (sx - 3, mid + 2, -2), (sx + 3, top - 2, 1.5), m["string"], g)
        for i, tx in enumerate(TSV_X):
            tube(f"{name}_tsv{k}_{i}", (x + tx, bot - NB_T, 0), (x + tx, top, 0), TSV_R * 0.8, m["copper"], g, verts=10)
            tube(f"{name}_mb{k}_{i}", (x + tx, bot - NB_T, 0), (x + tx, bot, 0), BUMP_R * 0.8, m["bump"], g, verts=10)
    return g


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.gbox("interposer", (-1450.0, -120.0, -600.0), (1300.0, 0.0, 0.0), m["interposer"], root)
    HK.gbox("substrate", (-1600.0, -320.0, -700.0), (1450.0, -120.0, 0.0), m["substrate"], root)
    HK.gbox("gpu", (GPU_X0, 0.0, -GPU_Z), (GPU_X1, GPU_Y1, 0.0), m["gpu"], root)

    stack(root, m, X8, 8, "hbf8")
    stack(root, m, X16, 16, "hbf16")

    # beat 1: the three grade bars appear low to high; reads run down the 16-high stack
    for i, (bx, h) in enumerate(zip(BAR_XS, BAR_HS)):
        g = HK.gbox(f"grade{i}", (bx - 55.0, 0.0, -110.0), (bx + 55.0, h, -20.0), m["gold"], root)
        show(g, span(1, 0.1 + 0.15 * i, 2, 0.0))
    for i, tx in enumerate(TSV_X):
        HK.dots(root, m, f"rd{i}_", [(X16 + tx, nand_top(15) - 8, 0.0), (X16 + tx, 30.0, 0.0)],
                4, "page", 1, 0.1, 0.8, 60, size=12.0)

    # beat 2: the link strips light and data crosses the interposer to the GPU
    for x in (X8, X16):
        g = HK.gbox(f"link_glow{int(x)}", (x + BASE_HALF - 30, 8, -BASE_HALF + 30), (x + BASE_HALF + 8, BASE_T - 8, 4),
                    m["bond"], root)
        show(g, beat(2))
    HK.dots(root, m, "bus16_", [(X16 + BASE_HALF + 4, 50.0, 0.0), (GPU_X0, 180.0, 0.0)], 4, "data", 2, 0.15, 0.8, 60, size=24.0)
    HK.dots(root, m, "bus8_", [(X8 + BASE_HALF + 4, 50.0, 0.0), (X8 + BASE_HALF + 4, 660.0, 0.0),
                               (GPU_X0 + 60.0, 660.0, 0.0), (GPU_X0 + 60.0, 400.0, 0.0)],
            4, "data", 2, 0.25, 0.85, 80, size=24.0)

    tags = {
        0: [("8-high stack", (X8 - BASE_HALF, 250.0, 0.0)), ("16-high stack", (X16 + BASE_HALF, 470.0, 0.0)),
            ("up to 512 GB a stack", (X16, nand_top(15) + 60.0, 0.0)), ("first OCP spec: Aug 3 2026", (-800.0, -10.0, 0.0))],
        1: [("three bandwidth grades", (BAR_XS[1], 620.0, 0.0)), ("about 0.4 TB/s", (BAR_XS[0], BAR_HS[0] + 10.0, 0.0)),
            ("about 3.0 TB/s: a ceiling", (BAR_XS[2], BAR_HS[2] + 10.0, 0.0))],
        2: [("xPU-HBF host interface", (X16 + BASE_HALF, 40.0, 0.0)), ("UCIe link (trade press)", (GPU_X0 - 60.0, 200.0, 0.0)),
            ("reliability and packaging", (X8 - BASE_HALF, 200.0, 0.0)), ("Google, Tenstorrent joined", (GPU_X1, 450.0, 0.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
