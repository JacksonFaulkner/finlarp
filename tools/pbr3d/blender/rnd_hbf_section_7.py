"""HBF section 7, "What the papers found": three simulation results on the overview's package.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_section_7.py

Writes blender/rnd_hbf_section_7.blend and assets/rnd_hbf_section_7.glb. One beat is 8 s.

Beats (match diagrams_nodes/hbf/sections/s7.rs):
  0 FlashAccel  six HBF stacks beside HBM; a throughput bar grows 2.49x over the HBM-only one
  1 Son et al.  a wide pipe of capacity carries slow reads; the GPU needs a fast one, near HBM's
  2 tiers       HBM, HBF and host memory feed the GPU; completion time drops 46-60%
All three are simulations, and the tags say so.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, label, show, tube  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as HK  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402
from rnd_hbf_kit import BACK_XS, BACK_Z, HBF_XS, HBM_XS  # noqa: E402
from rnd_hbf_overview import bus, hbf_reads, hbm_reads  # noqa: E402

PAGE = "rnd_hbf"
NAME = "section_7"
BEATS = 3

POSES = [
    ((0.0, 330.0, -350.0), 6600.0, 0.35, 0.50),
    ((800.0, 480.0, 0.0), 3500.0, 0.15, 0.12),
    ((650.0, 420.0, 0.0), 8600.0, 0.18, 0.14),
]

HOST_X = 2800.0  # host memory, off the package on the board


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def bar(root, m, name, lo, hi, mat_key, intervals):
    g = HK.gbox(name, lo, hi, m[mat_key], root)
    show(g, intervals)
    return g


def lane(root, m, name, pts, r, mat_key, intervals):
    """A pipe along the polyline `pts`, shown during `intervals`."""
    g = HK.empty(name, root)
    for i in range(len(pts) - 1):
        tube(f"{name}_{i}", pts[i], pts[i + 1], r, m[mat_key], g, verts=14)
    show(g, intervals)
    return g


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    m["board"] = HK.mat("host_board", (0.16, 0.36, 0.22), rough=0.8)
    m["dimm"] = HK.mat("host_dimm", (0.30, 0.55, 0.85), metal=0.2, rough=0.5)
    HK.package(root, m)
    for x in HBM_XS:
        HK.stack(root, m, x, 8, f"hbm{int(x)}", phy=1)
    front = [K.flash_stack(root, m, x, f"hbf{int(x)}", ucie=-1) for x in HBF_XS]
    for s in front:
        for bd in s.bonds:
            show(bd, [])
        for b in s.bumps:
            show(b, [])
    show(K.gpu_glow(root, m), span(0, 0.4, 1, 0.0) + span(2, 0.45, 3, 0.0))

    # beat 0: FlashAccel. A back row of four more HBF stacks, six in all, and two throughput bars
    # over the GPU: HBM only, and with six HBF stacks (2.49x).
    back = [K.flash_stack(root, m, x, f"hbfb{int(x)}", z0=BACK_Z, detail=False, ucie=0) for x in BACK_XS]
    for s in back:
        show(s.g, beat(0))
        for bd in s.bonds:
            show(bd, [])
        for b in s.bumps:
            show(b, [])
    base_h = 240.0
    bar(root, m, "tp_hbm", (-330.0, 420.0, -420.0), (-130.0, 420.0 + base_h, -300.0), "grey", span(0, 0.1, 1, 0.0))
    bar(root, m, "tp_hbf", (130.0, 420.0, -420.0), (330.0, 420.0 + 2.49 * base_h, -300.0), "gold", span(0, 0.35, 1, 0.0))
    for x in HBF_XS:
        hbf_reads(root, m, 0, x, u0=0.05, u1=0.5, tag="fa")
        bus(root, m, 0, x, 0.3, 0.8, tag="fab")

    # beat 1: Son et al. A wide pipe of capacity with slow reads, and the fast pipe a GPU needs.
    slow = [(1500.0, 620.0, 0.0), (1500.0, 760.0, 0.0), (150.0, 760.0, 0.0), (150.0, 400.0, 0.0)]
    lane(root, m, "slow_pipe", slow, 48.0, "ghost", beat(1))
    HK.dots(root, m, "slow_", slow, 3, "page", 1, 0.05, 0.6, 150, size=34.0)
    quick = [(850.0, 600.0, 0.0), (850.0, 640.0, 0.0), (-150.0, 640.0, 0.0), (-150.0, 400.0, 0.0)]
    lane(root, m, "fast_pipe", quick, 14.0, "copper", span(1, 0.35, 2, 0.0))
    HK.dots(root, m, "fast_", quick, 10, "read", 1, 0.4, 0.9, 40, size=14.0)
    cap = HK.gbox("cap_pile", (1360.0, 860.0, -150.0), (1640.0, 1000.0, -30.0), m["gold"], root)
    show(cap, beat(1))

    # beat 2: three tiers. Host memory off the package feeds HBF, HBF and HBM feed the GPU, and
    # the completion-time bar shrinks by about half (46-60%).
    board = HK.gbox("host_board", (2450.0, -360.0, -500.0), (3150.0, -320.0, 0.0), m["board"], root)
    show(board, beat(2))
    for i in range(3):
        x0 = HOST_X - 230.0 + i * 170.0
        d = HK.gbox(f"dimm{i}", (x0, -320.0, -420.0), (x0 + 60.0, 380.0, -60.0), m["dimm"], root)
        show(d, beat(2))
    feed = [(HOST_X, 420.0, 0.0), (HOST_X, 700.0, 0.0), (1500.0, 700.0, 0.0), (1500.0, 580.0, 0.0)]
    HK.dots(root, m, "host_", feed, 4, "data", 2, 0.05, 0.5, 90, size=26.0)
    for x in HBM_XS:
        hbm_reads(root, m, 2, x, u0=0.1, u1=0.6, tag="th")
        bus(root, m, 2, x, 0.3, 0.8, tag="thb")
    for x in HBF_XS:
        hbf_reads(root, m, 2, x, u0=0.15, u1=0.6, tag="tf")
        bus(root, m, 2, x, 0.35, 0.85, tag="tfb")
    bar(root, m, "ct_hbm", (-1800.0, 1250.0, -60.0), (1400.0, 1360.0, 0.0), "grey", span(2, 0.1, 3, 0.0))
    bar(root, m, "ct_tier", (-1800.0, 1080.0, -60.0), (-1800.0 + 3200.0 * 0.47, 1190.0, 0.0), "gold", span(2, 0.5, 3, 0.0))

    tags = {
        0: [("HBM only", (-230.0, 420.0 + base_h + 20.0, -300.0), 0.1),
            ("6 HBF stacks: ~2.49x throughput", (230.0, 420.0 + 2.49 * base_h + 20.0, -300.0), 0.35),
            ("1.93x energy efficiency", (1500.0, 600.0, BACK_Z), 0.5),
            ("FlashAccel, simulated", (-1500.0, 600.0, 0.0), 0.6)],
        1: [("more capacity, slow reads", (800.0, 780.0, 0.0), 0.1),
            ("needs reads near HBM speed", (350.0, 640.0, 0.0), 0.45),
            ("Son et al., simulated", (1500.0, 1000.0, 0.0), 0.6)],
        2: [("host memory", (HOST_X, 400.0, -60.0), 0.05), ("HBM + HBF + host: 3 tiers", (1500.0, 720.0, 0.0), 0.2),
            ("HBM alone", (-1800.0, 1360.0, 0.0), 0.1), ("46-60% less time (simulated)", (-1800.0 + 1504.0, 1190.0, 0.0), 0.5)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
