"""The R&D HBF page's section 3, "From flash cell to GPU, in order", in the picture-and-panel
template (docs/diagram-pages.md). Built on rnd_hbf_kit.py and hbm_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_3.py

Writes blender/rnd_hbf_section_3.blend and assets/rnd_hbf_section_3.glb. One beat is 8 s.

Beats (match diagrams_nodes/hbf/sections/s3.rs):
  0 read a page   one die's array lights a page; its CMOS layer reads it out to the TSV
  1 down the TSVs the data runs down the TSV columns to the base die
  2 into the GPU  the base die sends it over the UCIe link across the interposer; HBM reads arrive too
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, box, empty, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, DIE_HALF, TSV_X, die_top  # noqa: E402
from rnd_hbf_kit import CMOS_T, HBF_TOP, HBF_XS, HBM_XS, nand_bottom  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_3"
BEATS = 3

DIE = 12  # the die whose page is read
SX = HBF_XS[0]
PAGE_X = (SX - 95.0, SX - 25.0)  # the page, on the array layer between two TSV columns

POSES = [
    ((SX - 40.0, nand_bottom(DIE) + 10.0, 0.0), 520.0, 0.28, 0.10),
    ((SX, 300.0, 0.0), 1500.0, 0.30, 0.12),
    ((250.0, 260.0, 0.0), 5300.0, 0.22, 0.14),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.package(root, m)
    for x in HBM_XS:
        HK.stack(root, m, x, 8, f"hbm{int(x)}", phy=1)
    front = [K.flash_stack(root, m, x, f"hbf{int(x)}", ucie=-1) for x in HBF_XS]
    for s in front:
        for bd in s.bonds:
            show(bd, [])

    # beat 0: a page lights on one die's array, the CMOS layer under it reads it to the TSV
    bot = nand_bottom(DIE)
    mid = bot + CMOS_T
    pg = empty("page_g", front[0].arrays[DIE])
    box("page_m", (PAGE_X[0], mid + 2.0, -DIE_HALF * 0.6), (PAGE_X[1], mid + 11.0, 2.5), m["page"], pg)
    show(pg, span(0, 0.15, 1, 0.3))
    cx = (PAGE_X[0] + PAGE_X[1]) / 2
    for j in range(2):
        HK.dots(root, m, f"rd{j}_", [(cx - 15 + 30 * j, mid + 6.0, 3.0), (cx - 15 + 30 * j, bot + 3.5, 3.0),
                                     (SX + TSV_X[0], bot + 3.5, 3.0)], 3, "page", 0, 0.35 + 0.05 * j, 0.8, 60, size=4.0)

    # beat 1: the data runs down the TSV columns to the base die, in both stacks
    for x in HBF_XS:
        for i, tx in enumerate(TSV_X):
            top = nand_bottom(DIE) + 10.0 if x == SX else HBF_TOP - 8.0
            HK.dots(root, m, f"tsv{int(x)}_{i}_", [(x + tx, top, 3.0), (x + tx, 30.0, 3.0)], 4, "page", 1,
                    0.1, 0.7, 60, size=11.0)

    # beat 2: over the UCIe link into the GPU; HBM's reads arrive from the other side
    for x in HBF_XS:
        HK.dots(root, m, f"bus{int(x)}_", K.bus_path(x), 4, "data", 2, 0.05, 0.7, 70, size=24.0)
    for x in HBM_XS:
        for i, tx in enumerate(TSV_X):
            HK.dots(root, m, f"hr{int(x)}_{i}_", [(x + tx, die_top(7) - 10, 0.0), (x + tx, 30.0, 0.0)], 2,
                    "read", 2, 0.05, 0.35, 50, size=11.0)
        HK.dots(root, m, f"hbus{int(x)}_", K.bus_path(x), 3, "data", 2, 0.35, 0.75, 70, size=24.0)
    show(K.gpu_glow(root, m), span(2, 0.55, 3, 0.0))

    label("weights sit in the NAND array", (cx, mid + 13.0, 0.0), root, span(0, 0.15, 1, 0.0))
    label("CMOS layer reads one page", (SX + 20.0, bot + 3.0, 0.0), root, span(0, 0.35, 1, 0.0))
    label("a page: far bigger than DRAM's", (PAGE_X[0] - 40.0, mid + 8.0, 0.0), root, span(0, 0.55, 1, 0.0))
    label("down the TSVs", (SX + BASE_HALF, 360.0, 0.0), root, beat(1))
    label("microbumps join each die", (SX - DIE_HALF + 8.0, nand_bottom(4) - 4.0, 0.0), root, beat(1))
    label("to the base die", (SX - BASE_HALF - 10, 35.0, 0.0), root, span(1, 0.4, 2, 0.0))
    label("UCIe link across the interposer", (700.0, 120.0, 0.0), root, beat(2))
    label("into the GPU", (0.0, 400.0, 30.0), root, span(2, 0.4, 3, 0.0))
    label("HBM reads arrive too", (-850.0, 620.0, 0.0), root, span(2, 0.3, 3, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
