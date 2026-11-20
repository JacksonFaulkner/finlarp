"""HBF section 2, "The parts": the glossary of diagrams_pages/RND_HBF.txt shown piece by piece on a
cut-open HBF stack beside the GPU (rnd_hbf_kit.py on hbm_kit.py).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_2.py

Writes blender/rnd_hbf_section_2.blend and assets/rnd_hbf_section_2.glb. One beat is 8 s.

Beats (match diagrams_nodes/hbf/sections/s2.rs):
  0 die     the top NAND die lifted and split: the array layer over its CMOS logic layer (CBA)
  1 stack   the 16 dies spread on their base die, TSVs and microbumps, the link to the GPU
  2 page    a big flash page beside a small DRAM-sized access, KV writes, the wear meter
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, fly, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, GPU_X, TSV_X  # noqa: E402
from rnd_hbf_kit import CMOS_T, HBF_TOP, N_DIES, nand_bottom  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_2"
BEATS = 3
SX = 850.0  # the stack's centre

POSES = [
    ((SX, 610.0, 0.0), 820.0, 0.30, 0.10),
    ((SX - 60.0, 300.0, 0.0), 1550.0, 0.28, 0.12),
    ((SX - 20.0, 330.0, 0.0), 1750.0, 0.24, 0.12),
]

TOP_LIFT = 110.0
SPLIT = 70.0
METER_X = SX + BASE_HALF + 130.0
SEGS = 6


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.package(root, m)
    s = K.flash_stack(root, m, SX, "hbf", ucie=-1)
    for k, bd in enumerate(s.bonds):
        show(bd, span(0, 0.3, 1, 0.0) if k == N_DIES - 1 else [])
    for b in s.bumps:
        show(b, beat(1))

    # beat 0: the top die is up and split; beat 1: every die spreads so the stack can be read
    for k, d in enumerate(s.dies):
        keys = [(F(1, 0.1), 0.0), (F(1, 0.35), 9.0 * (k + 1)), (F(1, 0.9), 0.0)]
        if k == N_DIES - 1:
            keys = [(F(0, 0.0), TOP_LIFT), (F(0, 0.95), TOP_LIFT), (F(1, 0.1), 0.0)] + keys[1:]
        for f, a in keys:
            HK.key(d, f, "location", P(0, a, 0))
    a15 = s.arrays[N_DIES - 1]
    for f, a in [(F(0, 0.05), 0.0), (F(0, 0.3), SPLIT), (F(0, 0.95), SPLIT), (F(1, 0.05), 0.0)]:
        HK.key(a15, f, "location", P(0, a, 0))

    # beat 1: the link from the base die's UCIe strip to the GPU
    HK.dots(root, m, "link_", K.bus_path(SX), 4, "data", 1, 0.35, 0.85, 60, size=22.0)

    # beat 2: a whole flash page leaves the top die, down the stack and over to the GPU; a small
    # DRAM-sized access rides beside it for scale
    gx = -(SX - GPU_X) + 60.0
    route = [(0.0, 0.0, 0.0), (0.0, 0.0, 120.0), (0.0, -470.0, 120.0), (gx, -470.0, 120.0), (gx, -350.0, 120.0)]
    pg = HK.gbox("page_slab", (SX - 150.0, HBF_TOP + 14.0, -90.0), (SX + 150.0, HBF_TOP + 34.0, 10.0), m["page"], root)
    small = HK.gbox("dram_bit", (SX + 170.0, HBF_TOP + 14.0, -14.0), (SX + 190.0, HBF_TOP + 34.0, 6.0), m["read"], root)
    for g in (pg, small):
        show(g, span(2, 0.05, 2, 0.78))
        fly(g, route, F(2, 0.4), F(2, 0.75), steps=10)
    # KV cache writes: small blocks go into the stack, and each costs a little wear
    for i in range(3):
        HK.dots(root, m, f"kv{i}_", [(SX - 110.0 + 110.0 * i, HBF_TOP + 160.0, 0.0), (SX - 110.0 + 110.0 * i, HBF_TOP - 6.0, 0.0)],
                2, "data", 2, 0.55 + 0.04 * i, 0.85, 34, size=16.0)
    # the wear meter: segments go out one by one as writes land
    meter = HK.empty("meter", root)
    show(meter, beat(2))
    HK.gbox("meter_frame", (METER_X - 36.0, 90.0, -60.0), (METER_X + 36.0, 100.0 + SEGS * 70.0 + 10.0, -50.0), m["plinth"], meter)
    for i in range(SEGS):
        y0 = 100.0 + i * 70.0
        g = HK.gbox(f"wear{i}", (METER_X - 28.0, y0, -48.0), (METER_X + 28.0, y0 + 60.0, -30.0), m["gold"], meter)
        gone = SEGS - 1 - i  # the top segment goes first
        show(g, [(F(2, 0.0), F(2, 0.6 + 0.07 * gone))] if gone < 3 else beat(2))

    die_y = nand_bottom(N_DIES - 1) + TOP_LIFT
    tags = {
        0: [("NAND DIE: array + its logic", (SX - 200.0, die_y + SPLIT + 10.0, 0.0), 0.0),
            ("NAND array layer", (SX + 190.0, die_y + SPLIT + 12.0, 0.0), 0.3),
            ("CMOS logic layer", (SX + 190.0, die_y + 2.0, 0.0), 0.3),
            ("CBA: logic bonded under array", (SX - 190.0, die_y + CMOS_T, 0.0), 0.4)],
        1: [("STACK: 8 or 16 NAND dies", (SX + BASE_HALF, 470.0, 0.0), 0.1),
            ("TSVs and microbumps", (SX + TSV_X[2], 250.0, 0.0), 0.3),
            ("BASE DIE: talks to the GPU", (SX + BASE_HALF, 35.0, 0.0), 0.3),
            ("UCIe / xPU-HBF link", (GPU_X + 60.0, 120.0, 0.0), 0.45)],
        2: [("PAGE: one big flash read", (SX - 150.0, HBF_TOP + 40.0, 0.0), 0.08, 0.4),
            ("DRAM access: far smaller", (SX + 190.0, HBF_TOP + 40.0, 0.0), 0.08, 0.4),
            ("KV CACHE: rewritten as it runs", (SX + 110.0, HBF_TOP + 170.0, 0.0), 0.5),
            ("ENDURANCE: cells wear out", (METER_X, 100.0 + SEGS * 70.0 + 20.0, -50.0), 0.6)],
    }
    for i, items in tags.items():
        for text, pos, u, *end in items:
            label(text, pos, root, span(i, u, i, end[0]) if end else span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
