"""HBF section 4: why inference wants capacity (heading 4 of diagrams_pages/RND_HBF.txt).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_4.py

Writes blender/rnd_hbf_section_4.blend and assets/rnd_hbf_section_4.glb. One beat is 8 s.

Beats (match diagrams_nodes/hbf/sections/s4.rs):
  0 near the GPU  a GPU and two HBM stacks; gold weight blocks sit in the stacks and stream in
  1 810 GB        Llama 3.1 405B at 16 bits: a wide plinth fills with HBM stacks, two rows,
                  each taking its gold share of the weights
  2 fewer stacks  the HBM row goes; two HBF stacks (8-16x the capacity) hold the same gold
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, empty, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, DIE_HALF, GPU_X, GPU_Y1, GPU_Z, die_top  # noqa: E402
from rnd_hbf_kit import HBF_TOP  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_4"
BEATS = 3

FRONT_XS = (-2150.0, -1500.0, -850.0, 850.0, 1500.0, 2150.0)
BACK_XS = (-2100.0, -1400.0, -700.0, 0.0, 700.0, 1400.0, 2100.0)
BACK_Z = -650.0
TOP8 = die_top(7)

POSES = [
    ((-450.0, 300.0, 0.0), 4300.0, 0.30, 0.16),
    ((0.0, 250.0, -420.0), 8800.0, 0.12, 0.55),
    ((450.0, 380.0, 0.0), 4900.0, 0.18, 0.18),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def plinth(root, m):
    """A wide interposer and substrate, room for two rows of stacks, and the GPU."""
    HK.gbox("s4_interposer", (-2500.0, -120.0, -1000.0), (2500.0, 0.0, 0.0), m["interposer"], root)
    HK.gbox("s4_substrate", (-2750.0, -320.0, -1100.0), (2750.0, -120.0, 0.0), m["substrate"], root)
    HK.gbox("s4_gpu", (-GPU_X, 0.0, -GPU_Z), (GPU_X, GPU_Y1, 0.0), m["gpu"], root)


def weight(root, m, name, x, y0, z1, size, intervals):
    """A gold block of weights sitting on a stack top (front face at z1)."""
    h = size / 2
    g = HK.gbox(name, (x - h, y0, z1 - size), (x + h, y0 + size, z1 - 5.0), m["gold"], root)
    show(g, intervals)
    return g


def hbm_at(root, m, x, z0, name, intervals):
    """An 8-high HBM stack whose front face is at z0 (hbm_kit builds at z0 = 0; an offset empty
    moves it back)."""
    off = empty(f"{name}_off", root, P(0.0, 0.0, z0))
    s = HK.stack(off, m, x, 8, name, phy=0, tsv=z0 == 0.0)
    show(s.g, intervals)
    return s


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    plinth(root, m)

    # beat 0 and 2: the two HBM stacks at the GPU's left; beat 1: all thirteen
    near = (-1500.0, -850.0)
    for x in FRONT_XS:
        iv = beat(0) + beat(1) + beat(2) if x in near else beat(1)
        hbm_at(root, m, x, 0.0, f"hbm_f{int(x)}", iv)
    for x in BACK_XS:
        hbm_at(root, m, x, BACK_Z, f"hbm_b{int(x)}", beat(1))

    # beat 0: weight blocks in the two stacks, streaming to the GPU
    for x in near:
        weight(root, m, f"w0_{int(x)}", x, TOP8 + 10.0, -DIE_HALF + 165.0, 150.0, beat(0))
        HK.dots(root, m, f"w0b{int(x)}_", K.bus_path(x), 4, "data", 0, 0.2, 0.8, 70, size=26.0)

    # beat 1: every stack takes its share of the weights, one after another
    order = [(x, 0.0) for x in FRONT_XS] + [(x, BACK_Z) for x in BACK_XS]
    order.sort(key=lambda p: (p[0], -p[1]))
    for i, (x, z) in enumerate(order):
        u = 0.12 + 0.05 * i
        weight(root, m, f"w1_{i}", x, TOP8 + 10.0, z - DIE_HALF + 165.0, 150.0, span(1, u, 2, 0.0))

    # beat 2: two HBF stacks hold the same weights in two big blocks
    for x in (850.0, 1500.0):
        s = K.flash_stack(root, m, x, f"hbf{int(x)}", ucie=-1)
        show(s.g, beat(2))
        for bd in s.bonds:
            show(bd, [])
        for b in s.bumps:
            show(b, [])
        weight(root, m, f"w2_{int(x)}", x, HBF_TOP + 10.0, 0.0, 300.0, span(2, 0.25, 3, 0.0))
        HK.dots(root, m, f"w2b{int(x)}_", K.bus_path(x), 4, "data", 2, 0.4, 0.85, 70, size=26.0)

    tags = {
        0: [("model weights", (-1500.0, TOP8 + 170.0, -10.0), 0.0), ("held in memory beside the GPU", (-850.0 + BASE_HALF, 300.0, 0.0), 0.15),
            ("GPU", (0.0, GPU_Y1 + 20.0, 0.0), 0.0)],
        1: [("Llama 3.1 405B", (-2150.0, 900.0, 0.0), 0.05), ("16-bit weights: ~810 GB", (0.0, 900.0, BACK_Z), 0.2),
            ("many HBM stacks to hold it", (1500.0, 760.0, 0.0), 0.5)],
        2: [("HBF: 8-16x the capacity", (850.0 - BASE_HALF, 380.0, 0.0), 0.1), ("512 GB a stack: two hold it", (850.0, HBF_TOP + 330.0, 0.0), 0.35),
            ("similar cost (SanDisk)", (1500.0 + BASE_HALF, 200.0, 0.0), 0.55)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
