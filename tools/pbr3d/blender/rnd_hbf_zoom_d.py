"""The R&D HBF page's zoom-in d, "HBM against HBF", in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_zoom_d.py

Writes blender/rnd_hbf_zoom_d.blend and assets/rnd_hbf_zoom_d.glb. One beat is 8 s.

An 8-high HBM stack and a 16-high HBF stack side by side on a slab of interposer, the same height
(rnd_hbf_kit.py on hbm_kit.py), cut open at z = 0.

Beats (match diagrams_nodes/hbf/zooms/d.rs):
  0 capacity   one gold block over HBM, eight over HBF: 8-16x the capacity at a similar cost
  1 speed      HBM answers quickly in small pieces; HBF answers later, in bigger pages
  2 405B       weights fill the HBF stack; two bars: unlimited HBM 100, HBF within 2.2%
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, TSV_X, die_top  # noqa: E402
from rnd_hbf_kit import HBF_TOP  # noqa: E402

PAGE = "rnd_hbf"
NAME = "zoom_d"
BEATS = 3

HBM_X, HBF_X = -450.0, 450.0

POSES = [
    ((120.0, 500.0, 0.0), 3000.0, 0.20, 0.12),
    ((60.0, 330.0, 0.0), 2600.0, 0.20, 0.10),
    ((80.0, 500.0, 0.0), 2900.0, 0.18, 0.12),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def blocks(root, m):
    """Beat 0: capacity as gold blocks, one over HBM and eight (4 x 2) over HBF."""
    g = HK.gbox("cap_hbm", (HBM_X - 60, 640.0, -150.0), (HBM_X + 60, 760.0, -30.0), m["gold"], root)
    show(g, span(0, 0.1, 1, 0.0))
    for r in range(2):
        for c in range(4):
            x0 = HBF_X - 250.0 + c * 130.0
            y0 = 640.0 + r * 130.0
            cg = HK.gbox(f"cap_hbf{r}{c}", (x0, y0, -150.0), (x0 + 110.0, y0 + 110.0, -30.0), m["gold"], root)
            show(cg, span(0, 0.25 + 0.05 * (r * 4 + c), 1, 0.0))


def bars(root, m):
    """Beat 2: two bars between the stacks, unlimited HBM at 100 and HBF at 97.8 (within 2.2%)."""
    full = 420.0
    y0 = 120.0
    g1 = HK.gbox("bar_hbm", (-120.0, y0, -120.0), (-30.0, y0 + full, -30.0), m["grey"], root)
    g2 = HK.gbox("bar_hbf", (30.0, y0, -120.0), (120.0, y0 + full * 0.978, -30.0), m["array"], root)
    show(g1, span(2, 0.3, 3, 0.0))
    show(g2, span(2, 0.45, 3, 0.0))
    return y0 + full


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    HK.gbox("slab", (-900.0, -120.0, -500.0), (900.0, 0.0, 0.0), m["interposer"], root)

    HK.stack(root, m, HBM_X, 8, "hbm", phy=0)
    s = K.flash_stack(root, m, HBF_X, "hbf", ucie=0)
    for bd in s.bonds:
        show(bd, [])

    blocks(root, m)

    # beat 1: HBM's small, quick reads against HBF's later, bigger pages
    for i, tx in enumerate(TSV_X):
        HK.dots(root, m, f"q{i}_", [(HBM_X + tx, die_top(7) - 10, 0.0), (HBM_X + tx, 30.0, 0.0)],
                8, "read", 1, 0.05, 0.85, 24, size=9.0)
        HK.dots(root, m, f"pg{i}_", [(HBF_X + tx, HBF_TOP - 8, 0.0), (HBF_X + tx, 30.0, 0.0)],
                3, "page", 1, 0.4, 0.8, 70, size=24.0)

    # beat 2: weights stream into the HBF stack from above; the two bars rise
    for i, tx in enumerate(TSV_X):
        HK.dots(root, m, f"w{i}_", [(HBF_X + tx, 900.0, 0.0), (HBF_X + tx, HBF_TOP + 10, 0.0)],
                4, "page", 2, 0.02, 0.5, 50, size=18.0)
    top = bars(root, m)

    tags = {
        0: [("HBM: DRAM", (HBM_X - BASE_HALF, 300.0, 0.0), 0.0), ("HBF: NAND flash", (HBF_X + BASE_HALF, 300.0, 0.0), 0.0),
            ("8-16x the capacity", (HBF_X, 900.0, 0.0), 0.6), ("at a similar cost (SanDisk)", (HBF_X + 250.0, 680.0, 0.0), 0.7)],
        1: [("HBM: quick, small reads", (HBM_X - BASE_HALF, 420.0, 0.0), 0.05),
            ("HBF: later, bigger pages", (HBF_X + BASE_HALF, 420.0, 0.0), 0.4),
            ("higher latency", (HBF_X + BASE_HALF, 150.0, 0.0), 0.55)],
        2: [("Llama 3.1 405B: ~810 GB", (HBF_X, 880.0, 0.0), 0.05), ("unlimited HBM", (-75.0, top + 20.0, -75.0), 0.35),
            ("HBF: within 2.2%", (75.0, top - 10.0, -75.0), 0.5), ("SanDisk simulation", (HBM_X - BASE_HALF, 120.0, 0.0), 0.6)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0) if u else beat(i))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
