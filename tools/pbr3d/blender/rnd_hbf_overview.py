"""The R&D HBF page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_overview.py

Writes blender/rnd_hbf_overview.blend and assets/rnd_hbf_overview.glb. One beat is 8 s.

A GPU package cut open along its front edge (rnd_hbf_kit.py, on top of hbm_kit.py): the GPU on a
silicon interposer, two 8-high HBM stacks on its left and two 16-high HBF stacks on its right,
both stacks the same height.

Beats (match the seven beats in diagrams_nodes/hbf/overview.rs):
  0 package    the GPU with HBM on one side and HBF on the other
  1 16 dies    the HBF dies pull slightly apart: 16 NAND dies on a base die
  2 CBA        the top die rises and splits into its array and CMOS layers, then bonds back
  3 weights    reads run down the HBF stacks and across the interposer into the GPU
  4 trade-off  HBM: small and quick; HBF: 8-16x the capacity, later and in bigger pages
  5 six stacks a back row of four more HBF stacks: six in all; the GPU glows (FlashAccel)
  6 timeline   every path running; the spec-to-samples dates step in
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, TSV_X, die_top  # noqa: E402
from rnd_hbf_kit import BACK_XS, BACK_Z, HBF_TOP, HBF_XS, HBM_XS, N_DIES, nand_bottom  # noqa: E402

PAGE = "rnd_hbf"
NAME = "overview"
BEATS = 7

POSES = [
    ((250.0, 260.0, 0.0), 5700.0, 0.30, 0.16),
    ((850.0, 300.0, 0.0), 1500.0, 0.30, 0.12),
    ((850.0, 580.0, 0.0), 820.0, 0.30, 0.10),
    ((1000.0, 300.0, 0.0), 3000.0, 0.22, 0.14),
    ((0.0, 480.0, 0.0), 4700.0, 0.10, 0.12),
    ((0.0, 150.0, -350.0), 6200.0, 0.35, 0.62),
    ((250.0, 440.0, 0.0), 6200.0, 0.25, 0.16),
]

TOP_LIFT = 110.0  # how far the top HBF die rises in beat 2
SPLIT = 70.0  # how far its array layer lifts off its CMOS layer


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def hbm_reads(root, m, b, x, n=3, life=60, u0=0.35, u1=0.75, size=12.0, tag="hr"):
    for i, tx in enumerate(TSV_X):
        HK.dots(root, m, f"{tag}{int(x)}_{i}_", [(x + tx, die_top(7) - 10, 0.0), (x + tx, 30.0, 0.0)],
                n, "read", b, u0, u1, life, size=size)


def hbf_reads(root, m, b, x, n=3, life=70, u0=0.1, u1=0.5, size=12.0, mat_key="page", tag="fr"):
    for i, tx in enumerate(TSV_X):
        pts = [(x + tx, HBF_TOP - 8, 0.0), (x + tx, 30.0, 0.0)]
        HK.dots(root, m, f"{tag}{int(x)}_{i}_", pts, n, mat_key, b, u0, u1, life, size=size)


def bus(root, m, b, x, u0, u1, n=3, life=70, size=26.0, tag="bus"):
    HK.dots(root, m, f"{tag}{int(x)}_", K.bus_path(x), n, "data", b, u0, u1, life, size=size)


def capacity_cubes(root, m):
    """Beat 4: one block of capacity over an HBM stack, eight over an HBF stack (8-16x)."""
    g = HK.gbox("cap_hbm", (-850.0 - 60, 640.0, -150.0), (-850.0 + 60, 760.0, -30.0), m["gold"], root)
    show(g, span(4, 0.15, 5, 0.0))
    for r in range(2):
        for c in range(4):
            x0 = 850.0 - 250.0 + c * 130.0
            y0 = 640.0 + r * 130.0
            cg = HK.gbox(f"cap_hbf{r}{c}", (x0, y0, -150.0), (x0 + 110.0, y0 + 110.0, -30.0), m["gold"], root)
            show(cg, span(4, 0.15 + 0.04 * (r * 4 + c), 5, 0.0))


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.package(root, m)

    for x in HBM_XS:
        HK.stack(root, m, x, 8, f"hbm{int(x)}", phy=1)
    front = [K.flash_stack(root, m, x, f"hbf{int(x)}", ucie=-1) for x in HBF_XS]
    for s in front:
        for bd in s.bonds:
            show(bd, [])  # bond lines stay off except die 15's in beat 2 (below)
        for b in s.bumps:
            show(b, span(1, 0.2, 2, 0.0))

    # beat 1: the dies spread so all 16 can be counted. beat 2: the top die of the inner stack
    # rises, its array layer lifts off the CMOS layer and bonds back, then it settles.
    for si, s in enumerate(front):
        for k, d in enumerate(s.dies):
            keys = [(F(1, 0.1), 0.0), (F(1, 0.45), 9.0 * (k + 1)), (F(1, 0.9), 0.0)]
            if si == 0 and k == N_DIES - 1:
                keys += [(F(2, 0.05), 0.0), (F(2, 0.25), TOP_LIFT), (F(2, 0.85), TOP_LIFT), (F(2, 0.98), 0.0)]
            for f, a in keys:
                HK.key(d, f, "location", P(0, a, 0))
    top = front[0]
    a15 = top.arrays[N_DIES - 1]
    for f, a in [(F(2, 0.25), 0.0), (F(2, 0.4), SPLIT), (F(2, 0.55), SPLIT), (F(2, 0.68), 0.0)]:
        HK.key(a15, f, "location", P(0, a, 0))
    show(top.bonds[N_DIES - 1], span(2, 0.68, 2, 0.85))

    # beat 5: a back row of four more HBF stacks, six in all
    back = [K.flash_stack(root, m, x, f"hbfb{int(x)}", z0=BACK_Z, detail=False, ucie=0) for x in BACK_XS]
    for s in back:
        show(s.g, beat(5))
        for bd in s.bonds:
            show(bd, [])
        for b in s.bumps:
            show(b, [])
    show(K.gpu_glow(root, m), span(3, 0.6, 4, 0.0) + span(5, 0.3, 6, 0.0) + span(6, 0.5, 7, 0.0))

    # beat 3: weights read down the HBF stacks, then across the interposer into the GPU
    for x in HBF_XS:
        hbf_reads(root, m, 3, x, tag="w")
        bus(root, m, 3, x, 0.45, 0.8, tag="wb")
    # beat 4: HBM answers quickly in small pieces; HBF answers later in big pages
    hbm_reads(root, m, 4, -850.0, n=8, life=26, u0=0.1, u1=0.85, size=9.0, tag="q")
    hbf_reads(root, m, 4, 850.0, n=3, life=70, u0=0.4, u1=0.8, size=26.0, tag="pg")
    capacity_cubes(root, m)
    # beat 5: all six HBF stacks feed the GPU (front row shown moving)
    for x in HBF_XS:
        hbf_reads(root, m, 5, x, tag="s")
        bus(root, m, 5, x, 0.35, 0.75, tag="sb")
    # beat 6: everything at once
    for x in HBM_XS:
        hbm_reads(root, m, 6, x, u0=0.05, u1=0.6, tag="ah")
        bus(root, m, 6, x, 0.3, 0.8, tag="ahb")
    for x in HBF_XS:
        hbf_reads(root, m, 6, x, u0=0.05, u1=0.6, tag="af")
        bus(root, m, 6, x, 0.3, 0.8, tag="afb")

    sx = HBF_XS[0]
    tags = {
        0: [("GPU", (0.0, 420.0, 40.0)), ("HBM: DRAM stacks", (-1500.0, 600.0, 0.0)),
            ("HBF: NAND flash stacks", (1500.0, 600.0, 0.0)), ("silicon interposer", (1150.0, -60.0, 0.0))],
        1: [("16 NAND dies", (sx + BASE_HALF, 420.0, 0.0)), ("256 Gb a die, 512 GB a stack", (sx + BASE_HALF, 230.0, 0.0)),
            ("base die", (sx - BASE_HALF - 10, 35.0, 0.0)), ("about as tall as HBM", (sx - BASE_HALF - 10, 520.0, 0.0))],
        5: [("6 HBF stacks beside HBM", (1500.0, 650.0, BACK_Z)), ("2.49x throughput per GPU (sim)", (0.0, 450.0, 0.0)),
            ("1.93x energy efficiency (sim)", (-1200.0, 650.0, 0.0))],
    }
    top_y = nand_bottom(N_DIES - 1) + TOP_LIFT
    late = {
        2: [("CMOS logic layer", (sx + 190.0, top_y + 3.0, 0.0), 0.3), ("NAND array layer", (sx + 190.0, top_y + 70.0, 0.0), 0.3),
            ("bonded face to face: CBA", (sx - 190.0, top_y + 10.0, 0.0), 0.62)],
        3: [("read: NAND to the base die", (1500.0 + 190.0, 300.0, 0.0), 0.1), ("UCIe link to the GPU", (660.0, 60.0, 0.0), 0.4),
            ("spec: 0.4-3.0 TB/s grades", (1100.0, 760.0, 0.0), 0.5), ("first-gen target 1.6 TB/s", (1100.0, 680.0, 0.0), 0.6)],
        4: [("HBM: quick, small", (-850.0, 840.0, 0.0), 0.1), ("HBF: 8-16x the capacity", (850.0, 960.0, 0.0), 0.3),
            ("slower, in bigger pages", (850.0 + 220.0, 300.0, 0.0), 0.45)],
        6: [("Feb 2026: SanDisk-SK hynix MOU", (-1700.0, 950.0, 0.0), 0.08), ("Aug 2026: first OCP spec", (-800.0, 1100.0, 0.0), 0.3),
            ("H2 2026: HBF samples", (100.0, 950.0, 0.0), 0.5), ("early 2027: inference devices", (900.0, 1100.0, 0.0), 0.7)],
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
