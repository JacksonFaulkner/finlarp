"""HBF section 8, "The weak spot: writes" (heading 8 of diagrams_pages/RND_HBF.txt), in the
picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_8.py

Writes blender/rnd_hbf_section_8.blend and assets/rnd_hbf_section_8.glb. One beat is 8 s.

A small cut-open package: a GPU between an 8-high HBM stack (left) and a 16-high HBF stack
(right), with a wear meter beside the flash.

Beats (match diagrams_nodes/hbf/sections/s8.rs):
  0 reads      weights stream out of the flash; almost nothing is written back
  1 KV writes  the KV cache is written into the flash over and over; the wear meter climbs
  2 scheduler  writes are steered off the flash; the meter falls and the lifetime bars grow
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, label, mat, pivot, rel, show  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, die_top  # noqa: E402
from rnd_hbf_kit import HBF_TOP  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_8"
BEATS = 3

HBM_X, HBF_X = -650.0, 650.0
GPU_HX, GPU_H, GPU_HZ = 250.0, 300.0, 250.0
METER_X, METER_H = 1060.0, 500.0
LIFE_XS = (1250.0, 1380.0)  # the 1.2-year and 14.8-year lifetime bars
LIFE_H = 500.0  # 14.8 years
COL_R, COL_W = 110.0, -110.0  # read and write TSV columns (offsets from the stack's centre)

POSES = [
    ((300.0, 300.0, 0.0), 3600.0, 0.18, 0.12),
    ((750.0, 300.0, 0.0), 2300.0, 0.22, 0.12),
    ((330.0, 300.0, 0.0), 4100.0, 0.16, 0.12),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def bar(root, name, x, h, m_fill, keys, until, half=40.0):
    """A bar of full height `h` standing on y = 0 at x, scaled in y by `keys` [(frame, fraction)]."""
    at = (x, 0.0, -20.0)
    pv = pivot(name, at, root)
    box(f"{name}_m", rel(at, (x - half, 0.0, -40.0)), rel(at, (x + half, h, 0.0)), m_fill, pv)
    scale_keys(pv, [(f, (1.0, 1.0, max(s, 1e-4))) for f, s in keys], until=until)
    return pv


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    m["write"] = mat("kv_write", (1.0, 0.30, 0.22), emit=(1.0, 0.28, 0.18), strength=3.0)
    m["wear"] = mat("wear_fill", (0.95, 0.30, 0.22), emit=(0.95, 0.28, 0.2), strength=1.2, rough=0.5)
    m["frame"] = mat("meter_frame", (0.22, 0.23, 0.27), rough=0.7)

    HK.gbox("s8_interposer", (-1000.0, -90.0, -500.0), (1460.0, 0.0, 0.0), m["interposer"], root)
    HK.gbox("s8_substrate", (-1100.0, -220.0, -560.0), (1560.0, -90.0, 0.0), m["substrate"], root)
    HK.gbox("s8_gpu", (-GPU_HX, 0.0, -GPU_HZ), (GPU_HX, GPU_H, 0.0), m["gpu"], root)
    HK.stack(root, m, HBM_X, 8, "s8_hbm", phy=1)
    fs = K.flash_stack(root, m, HBF_X, "s8_hbf", ucie=-1)
    for bd in fs.bonds:
        show(bd, [])

    # the wear meter: a dark frame, a red fill that climbs in beat 1 and falls in beat 2
    HK.gbox("s8_meter_frame", (METER_X - 52, -8.0, -60.0), (METER_X + 52, METER_H + 12, -42.0), m["frame"], root)
    bar(root, "s8_wear", METER_X, METER_H, m["wear"],
        [(0, 0.12), (F(1, 0.1), 0.12), (F(1, 0.9), 0.9), (F(2, 0.1), 0.9), (F(2, 0.55), 0.18)], until=1)
    # beat 2: estimated write lifetime, before and after the scheduler (1.2 and 14.8 years)
    for x, frac, u in ((LIFE_XS[0], 1.2 / 14.8, 0.45), (LIFE_XS[1], 1.0, 0.55)):
        bar(root, f"s8_life{int(x)}", x, LIFE_H, m["gold"],
            [(0, 0.0), (F(2, u), 0.0), (F(2, u + 0.3), frac)], until=F(2, u))

    # paths: reads leave the flash on one TSV column; writes go into it on another
    hbf_edge = HBF_X - BASE_HALF - 4
    hbm_edge = HBM_X + BASE_HALF + 4
    read_pts = [(HBF_X + COL_R, HBF_TOP - 8, 0.0), (HBF_X + COL_R, 35.0, 0.0), (hbf_edge, 40.0, 0.0), (GPU_HX, 150.0, 0.0)]
    write_pts = [(GPU_HX, 210.0, 0.0), (hbf_edge, 40.0, 0.0), (HBF_X + COL_W, 35.0, 0.0), (HBF_X + COL_W, HBF_TOP - 8, 0.0)]
    hbm_write = [(-GPU_HX, 210.0, 0.0), (hbm_edge, 40.0, 0.0), (HBM_X - 110.0, 35.0, 0.0), (HBM_X - 110.0, die_top(7) - 10, 0.0)]

    # beat 0: many reads, one lonely write
    HK.dots(root, m, "s8_r0_", read_pts, 8, "page", 0, 0.05, 0.85, 70, size=16.0)
    HK.dots(root, m, "s8_w0_", write_pts, 1, "write", 0, 0.5, 0.5, 70, size=16.0)
    # beat 1: the KV cache is written into the flash again and again
    HK.dots(root, m, "s8_r1_", read_pts, 3, "page", 1, 0.05, 0.8, 70, size=14.0)
    HK.dots(root, m, "s8_w1_", write_pts, 12, "write", 1, 0.02, 0.88, 60, size=16.0)
    # beat 2: the scheduler steers writes to HBM; hardly any reach the flash
    HK.dots(root, m, "s8_w2h_", hbm_write, 10, "write", 2, 0.02, 0.85, 60, size=16.0)
    HK.dots(root, m, "s8_w2f_", write_pts, 1, "write", 2, 0.4, 0.4, 60, size=16.0)
    HK.dots(root, m, "s8_r2_", read_pts, 5, "page", 2, 0.05, 0.85, 70, size=14.0)

    tags = {
        0: [("weights: read, rarely written", (HBF_X + COL_R, 300.0, 0.0), 0.05),
            ("flash wears out as it is rewritten", (HBF_X, HBF_TOP + 60.0, 0.0), 0.2),
            ("writes are slow", (HBF_X + COL_W, 120.0, 0.0), 0.5)],
        1: [("KV cache: rewritten constantly", (HBF_X + COL_W, 420.0, 0.0), 0.05),
            ("wear rising", (METER_X, METER_H, -40.0), 0.35),
            ("KV writes: 5-13.9% of run time", (GPU_HX, 330.0, 0.0), 0.5)],
        2: [("scheduler: 94% fewer HBF writes", (0.0, GPU_H + 10.0, 0.0), 0.05),
            ("1.2 years", (LIFE_XS[0], 60.0, -20.0), 0.6),
            ("14.8 years (est.)", (LIFE_XS[1], LIFE_H, -20.0), 0.75)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
