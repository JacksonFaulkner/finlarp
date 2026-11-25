"""TRM_GPU on the MLCC base board: the board's own GPU package, then one GPU die drawn big on the bench
with its lid off: a grid of streaming multiprocessors (each with core lanes and a tensor core), the L2
cache down the middle, HBM stacks either side and NVLink ports on the edge.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_gpu.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_GPU"
BEATS = [
    ("The GPU is the big package in the middle of an AI board",
     "On an AI accelerator board the GPU package sits in the centre: one or two large silicon dies with stacks of "
     "high-bandwidth memory (HBM) beside them on a shared interposer. Dozens of power phases crowd round it because it "
     "draws around 1,000 W."),
    ("Inside: over a hundred copies of the same small processor",
     "Open the die and it is a grid of streaming multiprocessors (SMs), around 130 to 150 on a modern data-center GPU. "
     "Each SM holds 128 simple arithmetic lanes plus a few tensor cores, its own registers and a scratchpad. A big L2 "
     "cache runs through the middle and memory controllers line the edges next to the HBM."),
    ("One instruction, thousands of numbers at once",
     "A CPU runs a few complex threads fast. A GPU issues one instruction to groups of 32 threads (a warp) and runs tens "
     "of thousands of threads at once across all SMs, each on different data. Graphics needed this for pixels; neural "
     "networks need it because they are mostly the same multiply-add repeated billions of times."),
    ("Tensor cores do the matrix math that AI runs on",
     "Since 2017 each SM also carries tensor cores: small matrix engines that multiply whole tiles of numbers in one "
     "step, at low precision (FP16, FP8, FP4). They supply most of a GPU's AI throughput. HBM streams weights in at "
     "several TB/s to keep them fed; without that bandwidth they would sit idle."),
    ("Thousands of watts and dollars per chip, millions of chips",
     "A top GPU sells for tens of thousands of dollars, burns about a kilowatt, and is sold in racks of 72 linked by "
     "NVLink. GPU supply, price and power draw set much of AI data-center spending. TSMC (TSM) makes the dies. "
     "Related: NVIDIA (NVDA), AMD (AMD), Intel (INTC), TSM."),
]

X0, X1, Z0 = 152.0, 246.0, -82.0
DY = 6.0  # die top
NX, NZ = 6, 8  # SMs across the die (x) and deep (z), split by the L2 strip


def die(m, root):
    g = empty("gpu", root)
    bx("g_sub", (X0, 0.4, Z0), (X1, 3.0, 0.0), m["substrate"], g)
    bx("g_ip", (X0 + 3.0, 3.0, Z0 + 3.0), (X1 - 3.0, 4.2, -3.0), m["si"], g)
    dx0, dx1 = X0 + 21.0, X1 - 21.0
    dz0, dz1 = Z0 + 6.0, -6.0
    bx("g_die", (dx0, 4.2, dz0), (dx1, DY, dz1), m["die"], g)
    hbm = []
    for side, (hx0, hx1) in (("l", (X0 + 5.0, dx0 - 2.0)), ("r", (dx1 + 2.0, X1 - 5.0))):
        for k in range(3):
            z1 = -7.0 - k * 23.0
            for n in range(8):
                y = 4.2 + n * 1.3
                hbm.append(bx(f"g_hbm{side}{k}{n}", (hx0, y, z1 - 20.0), (hx1, y + 1.0, z1), m["hbm"], g))
                hbm.append(bx(f"g_hbmd{side}{k}{n}", (hx0 + 0.3, y + 1.0, z1 - 19.7), (hx1 - 0.3, y + 1.3, z1 - 0.3), m["hbm_dram"], g))
    D.join(hbm, "g_hbm")
    # L2 strip across the middle (z), SMs in two halves
    lz = (dz0 + dz1) / 2
    bx("g_l2", (dx0 + 1.0, DY, lz - 3.0), (dx1 - 1.0, DY + 1.0, lz + 3.0), m["hbm_dram"], g)
    for k in range(10):
        x = dx0 + 2.0 + k * (dx1 - dx0 - 4.0) / 10
        bx(f"g_l2b{k}", (x, DY + 1.0, lz - 2.4), (x + 3.4, DY + 1.3, lz + 2.4), m["gold"], g)
    sw = (dx1 - dx0 - 2.0) / NX
    half = (lz - 3.0 - dz0 - 1.0) / (NZ // 2)
    sm, lanes = [], []
    core_g = empty("g_cores", root)
    tens_g = empty("g_tens", root)
    centres = []
    for i in range(NX):
        for j in range(NZ):
            x0 = dx0 + 1.0 + i * sw
            z0 = dz0 + 1.0 + j * half if j < NZ // 2 else lz + 3.0 + (j - NZ // 2) * half
            x1, z1 = x0 + sw - 0.8, z0 + half - 0.8
            sm.append(bx(f"sm{i}{j}", (x0, DY, z0), (x1, DY + 0.8, z1), m["fet"], g))
            # 4 core lanes (rows of tiny ALUs) + a tensor core block + register strip
            for r in range(4):
                zz = z0 + 0.5 + r * 0.9
                lanes.append(bx(f"ln{i}{j}{r}", (x0 + 0.4, DY + 0.8, zz), (x1 - 3.4, DY + 1.2, zz + 0.5), m["silicon"], g))
                bx(f"lng{i}{j}{r}", (x0 + 0.5, DY + 1.2, zz + 0.05), (x1 - 3.5, DY + 1.35, zz + 0.45), m["sig"], core_g)
            lanes.append(bx(f"tc{i}{j}", (x1 - 3.0, DY + 0.8, z0 + 0.4), (x1 - 0.4, DY + 1.8, z1 - 0.4), m["gold"], g))
            bx(f"tcg{i}{j}", (x1 - 2.8, DY + 1.8, z0 + 0.6), (x1 - 0.6, DY + 2.0, z1 - 0.6), m["h_amber"], tens_g)
            centres.append(((x0 + x1) / 2, DY + 1.0, (z0 + z1) / 2))
    D.join(sm, "g_sms")
    D.join(lanes, "g_lanes")
    # NVLink / PCIe ports on the front edge
    for k in range(8):
        x = X0 + 8.0 + k * (X1 - X0 - 16.0) / 7
        bx(f"g_nvl{k}", (x - 2.5, 3.0, -2.0), (x + 2.5, 4.4, 0.0), m["gold"], g)
    for o in (core_g, tens_g):
        show(o, [])
    pts = {"die": ((dx0 + dx1) / 2, DY + 1.0, dz0 + 4.0), "sm": centres[NZ * 2 + 1], "l2": ((dx0 + dx1) / 2 + 10.0, DY + 1.3, lz),
           "hbm": (X0 + 10.0, 14.0, -30.0), "hbm_r": (X1 - 10.0, 14.0, -55.0), "nvl": (X0 + 30.0, 4.4, 0.0),
           "tc": centres[NZ * 4 + 6], "lanes": centres[NZ * 1 + 5]}
    return pts, core_g, tens_g, centres, (dx0, dx1, dz0, dz1, lz)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root)
    pk, ph = b["pk"], b["ph"]
    pts, core_g, tens_g, centres, (dx0, dx1, dz0, dz1, lz) = die(m, root)
    C.magnify(m, root, pk["die_r"], (X0 - 2.0, 10.0, -40.0))
    show(b["die_glow"], [(F(0, 0.3), F(1, 0)), (F(2, 0.1), F(5, 0))])

    # beat 2: every core lane flashes on the same clock; data spreads out from the L2 to every SM
    blink(core_g, 2, [1, 3, 5, 7, 9, 11, 13, 15], n=16, on=0.6)
    for k, c in enumerate(centres[::3]):
        run(root, f"sp{k}", [((dx0 + dx1) / 2, DY + 2.5, lz), (c[0], DY + 2.5, c[2])], 1, 0.5, m["sig"], 2, 0.05, 0.6, 25)
    # beat 3: tensor cores glow; HBM streams weights in
    show(tens_g, [(F(3, 0.15), F(5, 0))])
    for side, hx in (("l", X0 + 12.0), ("r", X1 - 12.0)):
        for k, z in enumerate((-17.0, -40.0, -63.0)):
            tx = dx0 + 6.0 if side == "l" else dx1 - 6.0
            run(root, f"hb{side}{k}", [(hx, 15.0, z), (tx, DY + 3.0, z), ((dx0 + dx1) / 2, DY + 3.0, lz)], 3, 0.8, m["chan"], [3, 4], 0.05 * k, 0.75, 40)
    # beat 4: full power: phases pour current in, heat leaves the die and the bench die
    for side in (-1, 1):
        run(root, f"amp{side}", D.front_path(side), 6, 1.2, m["amp"], [2, 3, 4], 0.1, 0.9, 90)
    rise(root, "gh", (0.0, D.DIE_Y[1] + 1.0, -16.0), 6, 1.0, m["heat"], 4, 0.05, 0.85, 34.0, 60, (24.0, 12.0))
    rise(root, "bh", ((dx0 + dx1) / 2, DY + 2.0, -40.0), 6, 0.9, m["heat"], [3, 4], 0.05, 0.85, 26.0, 60, (22.0, 26.0))

    C.tags(root, {
        0: [("GPU package", pk["top"]), ("HBM stacks", pk["hbm"]), ("power phases, ~1 kW", ph["ind"][(-1, 3)]["top"]),
            ("one GPU die, lid off", pts["die"])],
        1: [("SM: streaming multiprocessor", pts["sm"]), ("L2 cache down the middle", pts["l2"]), ("HBM beside the die", pts["hbm"]),
            ("NVLink / PCIe ports", pts["nvl"])],
        2: [("same instruction, every lane", pts["lanes"]), ("warps of 32 threads", pts["sm"]), ("tens of thousands in flight", pts["l2"])],
        3: [("tensor core per SM partition", pts["tc"]), ("HBM feeds weights, TB/s", pts["hbm"]), ("FP16 / FP8 / FP4 matmul", pts["l2"])],
        4: [("~1 kW per GPU", pk["top"]), ("racks of 72 over NVLink", pts["nvl"]), ("NVDA, AMD, INTC, TSM", pts["die"])],
    })
    cb = ((dx0 + dx1) / 2, DY, (dz0 + dz1) / 2)
    C.done(SLUG, BEATS, [
        frame((40.0, 0.0, -80.0), 400.0, 0.30, 0.6, pad=1.0),
        frame(cb, 100.0, 0.22, 0.75),
        frame((cb[0] - 12.0, DY, cb[2] + 10.0), 55.0, 0.15, 0.85),
        frame(cb, 95.0, 0.30, 0.6),
        frame((40.0, 10.0, -70.0), 380.0, 0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
