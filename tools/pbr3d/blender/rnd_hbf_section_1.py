"""HBF section 1, "What it is: NAND flash in an HBM package" (heading 1 of RND_HBF.txt).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_1.py

Writes blender/rnd_hbf_section_1.blend and assets/rnd_hbf_section_1.glb. Three 8 s beats:
  0 HBM        four HBM stacks of DRAM dies around the GPU on the interposer
  1 HBF        the two right-hand HBM stacks give way to HBF stacks of NAND, dropped in the same way
  2 capacity   gold capacity blocks rise: one per HBM stack, eight per HBF stack; reads flow slower
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import TSV_X, die_top  # noqa: E402
from rnd_hbf_kit import HBF_TOP, HBF_XS, HBM_XS  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_1"
BEATS = 3

POSES = [
    ((280.0, 260.0, 0.0), 6100.0, 0.25, 0.16),
    ((720.0, 320.0, 0.0), 4700.0, 0.25, 0.14),
    ((280.0, 500.0, 0.0), 6400.0, 0.18, 0.14),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def cubes(root, m, x, n, name):
    """`n` gold capacity blocks over the stack at x, in rows of four, popping in through beat 2."""
    for i in range(n):
        r, c = divmod(i, 4)
        cols = min(n, 4)
        x0 = x - cols * 65.0 + c * 130.0 + 10.0
        y0 = 660.0 + r * 130.0
        g = HK.gbox(f"{name}{i}", (x0, y0, -150.0), (x0 + 110.0, y0 + 110.0, -30.0), m["gold"], root)
        show(g, span(2, 0.1 + 0.04 * i, 3, 0.0))


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.package(root, m)

    # HBM on the left the whole time
    for x in HBM_XS:
        HK.stack(root, m, x, 8, f"hbm{int(x)}", phy=1)
    # HBM on the right only in beat 0
    for x in HBF_XS:
        s = HK.stack(root, m, x, 8, f"hbmr{int(x)}", phy=-1)
        show(s.g, beat(0))
    # HBF on the right from beat 1: the dies drop onto the base die one after another
    for x in HBF_XS:
        s = K.flash_stack(root, m, x, f"hbf{int(x)}", ucie=-1)
        show(s.g, span(1, 0.0, 3, 0.0))
        for bd in s.bonds:
            show(bd, [])
        for k, d in enumerate(s.dies):
            f0 = F(1, 0.05 + 0.025 * k)
            HK.key(d, f0, "location", P(0, 500.0, 0))
            HK.key(d, f0 + 20, "location", P(0, 0, 0))

    # beat 2: reads: HBM small and quick, HBF bigger and later; capacity blocks
    for x in HBM_XS:
        for i, tx in enumerate(TSV_X):
            HK.dots(root, m, f"q{int(x)}_{i}_", [(x + tx, die_top(7) - 10, 0.0), (x + tx, 30.0, 0.0)],
                    6, "read", 2, 0.1, 0.85, 26, size=9.0)
    for x in HBF_XS:
        for i, tx in enumerate(TSV_X):
            HK.dots(root, m, f"pg{int(x)}_{i}_", [(x + tx, HBF_TOP - 8, 0.0), (x + tx, 30.0, 0.0)],
                    2, "page", 2, 0.4, 0.8, 70, size=22.0)
    for x in HBM_XS:
        cubes(root, m, x, 1, f"cap_m{int(x)}_")
    for x in HBF_XS:
        cubes(root, m, x, 8, f"cap_f{int(x)}_")

    label("GPU", (0.0, 420.0, 40.0), root, beat(0) + beat(1))
    label("HBM: stacked DRAM dies", (-1500.0, 600.0, 0.0), root, beat(0))
    label("beside the GPU", (850.0, 600.0, 0.0), root, beat(0))
    label("silicon interposer", (1150.0, -60.0, 0.0), root, beat(0))
    label("HBF: stacked NAND dies", (1500.0, 600.0, 0.0), root, span(1, 0.45, 2, 0.0))
    label("same package, same interposer", (850.0, -60.0, 0.0), root, span(1, 0.2, 2, 0.0))
    label("HBM: one block a stack", (-1500.0, 820.0, 0.0), root, span(2, 0.15, 3, 0.0))
    label("HBF: 8-16x the capacity", (1500.0, 1000.0, 0.0), root, span(2, 0.4, 3, 0.0))
    label("bandwidth below HBM", (850.0, 300.0, 0.0), root, span(2, 0.5, 3, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
