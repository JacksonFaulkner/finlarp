"""TRM_CPU: the Terms-tab overview for a CPU (the host processor in an AI server).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_cpu.py

The shared GPU board, with the host CPU drawn huge on the BENCH strip, lid off and front edge
cut: a grid of big cores (each with its own L2), a shared L3 mesh between them, DDR memory
controllers out to DIMM sticks on one side, PCIe / C2C lanes on the front feeding the GPU.

Beats:
  0 board     the CPU beside the GPU: the host that runs the show
  1 cores     the die: cores, caches, memory and I/O controllers
  2 run       cores pick up instructions; data from DIMMs through the caches
  3 feed      the CPU stages batches and ships them to the GPU over PCIe / C2C
  4 who       x86 vs Arm and the tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_CPU"
BEATS = [
    ("The CPU is the general-purpose host that runs the server",
     "A CPU runs the operating system, the drivers and most ordinary software. In an AI server one or two CPUs sit "
     "beside the accelerators: they start jobs, load data, handle networking and storage, and tell the GPUs what to do "
     "next. Outside AI, CPUs still run most cloud workloads."),
    ("Inside: a few dozen to a few hundred big, independent cores",
     "Each core is a complete processor with its own instruction decoder, branch predictor, integer and vector units "
     "and private L1/L2 cache. A large shared L3 cache and an on-die mesh connect them. Memory controllers drive many "
     "channels of DDR DRAM, and I/O blocks provide PCIe and chip-to-chip links."),
    ("Each core runs its own instruction stream, fast and out of order",
     "Cores pull instructions and data from DRAM through the cache levels, guess which way branches will go and run "
     "several instructions per clock at 3-5 GHz. That makes them good at messy, branchy, serial code, the opposite of "
     "the GPU's thousands of simple lanes doing the same maths in lockstep."),
    ("It stages the data and feeds the accelerators",
     "In training and inference the CPU loads and preprocesses batches, then ships them to the GPUs over PCIe or a "
     "coherent link such as NVIDIA's NVLink-C2C on Grace. A slow host leaves expensive GPUs idle, so AI servers pair "
     "them with high-memory-bandwidth CPUs, typically one CPU for every two to four GPUs."),
    ("Two camps: x86 from Intel and AMD, Arm designs from everyone else",
     "x86 (Intel Xeon, AMD EPYC) still holds most server sockets, and AMD has been gaining share. Arm-based chips are "
     "rising: NVIDIA Grace, AWS Graviton, Google Axion and Microsoft Cobalt license designs from Arm Holdings. Related: "
     "Intel (INTC), AMD (AMD), Arm (ARM), NVIDIA (NVDA), Amazon (AMZN)."),
]

X0, X1 = 166.0, 240.0
Z0, Z1 = -82.0, 0.0
SY0, SY1 = 0.4, 3.4
DY0, DY1 = 3.4, 7.0
NX, NZ = 4, 5  # core grid
CX0, CX1, CZ0, CZ1 = 172.0, 234.0, -72.0, -14.0


def mats(m):
    m["core"] = mat("cpu_core", (0.34, 0.30, 0.52), metal=0.5, rough=0.3)
    m["l2"] = mat("cpu_l2", (0.20, 0.40, 0.36), metal=0.5, rough=0.3)
    m["l3"] = mat("cpu_l3", (0.24, 0.30, 0.38), metal=0.5, rough=0.35)
    m["mc"] = mat("cpu_mc", (0.55, 0.42, 0.20), metal=0.6, rough=0.3)
    m["io"] = mat("cpu_io", (0.45, 0.22, 0.40), metal=0.5, rough=0.3)
    m["dimm"] = mat("cpu_dimm", (0.08, 0.22, 0.12), rough=0.6)
    m["core_on"] = mat("cpu_core_on", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=3.0)
    m["data"] = mat("cpu_data", (0.30, 0.65, 1.0), emit=(0.28, 0.62, 1.0), strength=4.0)
    m["ins"] = mat("cpu_ins", (1.0, 0.62, 0.18), emit=(1.0, 0.58, 0.15), strength=4.0)


def die(m, root):
    g = empty("cpu", root)
    bx("c_sub", (X0 - 8.0, SY0, Z0 - 6.0), (X1 + 6.0, SY1, 0.0), m["substrate"], g)
    bx("c_subcu", (X0 - 8.0, 1.8, Z0 - 6.0), (X1 + 6.0, 2.1, 0.2), m["copper"], g)
    for i in range(18):
        x = X0 - 6.0 + 4.6 * i
        D.tube(f"c_bga{i}", (x, 0.0, -1.2), (x, SY0, -1.2), 1.1, m["solder"], g, 10)
    bx("c_si", (X0, DY0, Z0), (X1, DY0 + 2.0, 0.0), m["silicon"], g)
    for k in range(6):
        y = DY0 + 2.0 + k * 0.28
        bx(f"c_m{k}", (X0, y, Z0), (X1, y + 0.14, 0.15), m["copper"], g)
        bx(f"c_d{k}", (X0, y + 0.14, Z0), (X1, y + 0.28, 0.05), m["oxide"], g)
    top = DY1 - 0.2
    bx("c_l3", (X0, DY1 - 0.4, Z0), (X1, top, 0.0), m["l3"], g)
    pw, pz = (CX1 - CX0) / NX, (CZ1 - CZ0) / NZ
    cores, on = {}, []
    for i in range(NX):
        for j in range(NZ):
            x, z = CX0 + pw * i, CZ0 + pz * j
            # core: front-end, execution, vector unit; L2 slab beside it
            bx(f"c_fe{i}{j}", (x + 1.0, top, z + 1.0), (x + pw * 0.62, top + 1.6, z + pz * 0.38), m["core"], g)
            bx(f"c_ex{i}{j}", (x + 1.0, top, z + pz * 0.42), (x + pw * 0.62, top + 1.2, z + pz - 1.0), m["core"], g)
            bx(f"c_vu{i}{j}", (x + 2.0, top + 1.2, z + pz * 0.5), (x + pw * 0.5, top + 1.8, z + pz - 2.0), m["fet"], g)
            bx(f"c_l2{i}{j}", (x + pw * 0.66, top, z + 1.0), (x + pw - 1.0, top + 1.0, z + pz - 1.0), m["l2"], g)
            for s in range(3):
                zz = z + 2.0 + s * (pz - 4.0) / 3
                bx(f"c_l2s{i}{j}{s}", (x + pw * 0.68, top + 1.0, zz), (x + pw - 1.4, top + 1.1, zz + 1.0), m["dark"], g)
            e = empty(f"c_on{i}{j}", root)
            bx(f"c_ong{i}{j}", (x + 1.4, top + 1.65, z + 1.4), (x + pw * 0.58, top + 1.85, z + pz * 0.34), m["core_on"], e)
            show(e, [])
            on.append(e)
            cores[(i, j)] = (x + pw * 0.35, top + 2.0, z + pz * 0.5)
    # memory controllers on the left edge, I/O (PCIe / C2C) along the front
    for k in range(4):
        x = CX0 + k * 15.5
        bx(f"c_mc{k}", (x, top, Z0 + 0.8), (x + 13.0, top + 1.0, CZ0 - 0.8), m["mc"], g)
    for k in range(6):
        x = CX0 + k * 10.4
        bx(f"c_io{k}", (x, top, -10.0), (x + 8.6, top + 0.9, -2.5), m["io"], g)
    # DIMM sticks left of the package (8 channels)
    dimms = empty("c_dimms", root)
    for k in range(8):
        x = X0 + 2.0 + k * 9.4
        bx(f"c_slot{k}", (x, 0.0, -124.0), (x + 2.6, 3.0, -96.0), m["plastic"], dimms)
        bx(f"c_dimm{k}", (x + 0.6, 3.0, -123.0), (x + 2.0, 30.0, -97.0), m["dimm"], dimms)
        for c in range(4):
            z = -122.0 + c * 6.4
            bx(f"c_dram{k}{c}", (x + 2.0, 8.0, z), (x + 2.6, 26.0, z + 5.0), m["mold"], dimms)
    pts = {"die": ((X0 + X1) / 2, top + 2.0, -40.0), "core": cores[(1, 2)], "l2": (CX0 + pw * 0.8, top + 1.1, CZ0 + pz * 2.5),
           "l3": (CX0 + pw * 2.0, top, CZ0 + pz * 3.0), "mc": (190.0, top + 1.0, Z0 + 5.0), "io": (205.0, top + 1.0, -5.0),
           "dimm": (200.0, 30.0, -110.0), "cut": (X0 + 6.0, DY0 + 2.8, 0.0), "top": top}
    return pts, on, cores


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk, ph, die_glow = b["pk"], b["ph"], b["die_glow"]
    cp, on, cores = die(m, root)
    top = cp["top"]
    C.magnify(m, root, (100.0, 0.0, -170.0), (X0 - 4.0, 10.0, -60.0), r=6.0)

    # beat 1: cores light one by one
    for k, e in enumerate(on):
        a = 0.2 + 0.03 * k
        iv = [(F(1, a), F(2, 0))]
        show(e, iv)
    # beat 2: each core blinks on its own rhythm; data from DIMMs through the MCs to cores
    for k, e in enumerate(on):
        blink(e, 2, [(k * 3) % 8, (k * 5 + 2) % 8, (k + 6) % 8], n=8, on=0.6)
    for k in range(6):
        i, j = k % 4, (k * 2) % 5
        c = cores[(i, j)]
        xs = X0 + 3.3 + (k + 1) * 9.4
        run(root, f"mem{k}", [(xs, 28.0, -110.0), (xs, 4.0, -94.0), (xs, top + 2.0, Z0 + 4.0), (c[0], top + 2.4, Z0 + 4.0), c],
            3, 0.7, m["data"], [2], 0.02 + 0.03 * k, 0.8, 45)
        run(root, f"ins{k}", [(c[0], top + 2.6, Z0 + 4.0), c], 3, 0.5, m["ins"], [2], 0.1 + 0.03 * k, 0.9, 25)
    # beat 3: batches out of the I/O lanes, across the board to the GPU package
    for k in range(4):
        x = 180.0 + k * 12.0
        run(root, f"feed{k}", [(x, top + 1.5, -6.0), (x, 1.0, 6.0), (x - 40.0, 1.0, 6.0), (40.0, 1.0, -10.0), (10.0, D.DIE_Y[1], -10.0)],
            5, 1.0, m["data"], [3], 0.05 + 0.05 * k, 0.8, 60)
    show(die_glow, [(F(3, 0.4), F(4, 0))])
    rise(root, "cpu_heat", ((X0 + X1) / 2, top + 2.0, -40.0), 5, 1.0, m["heat"], 3, 0.1, 0.9, 25.0, 60, (24.0, 20.0))

    C.tags(root, {
        0: [("GPU: the maths", pk["top"]), ("host CPU, lid off", cp["die"]), ("DDR memory sticks", cp["dimm"])],
        1: [("one core + its L2", cp["core"]), ("shared L3 + mesh", cp["l3"]), ("DDR controllers", cp["mc"]),
            ("PCIe / C2C I/O", cp["io"])],
        2: [("data in from DRAM", cp["dimm"]), ("3-5 GHz, out of order", cp["core"]), ("cache close to each core", cp["l2"])],
        3: [("batches out over PCIe", cp["io"]), ("into the GPU", pk["top"]), ("slow host = idle GPU", cp["die"])],
        4: [("x86: Intel Xeon, AMD EPYC", cp["die"]), ("Arm: Grace, Graviton, Axion", cp["core"]),
            ("INTC AMD ARM NVDA AMZN", cp["io"])],
    })
    cx = (X0 + X1) / 2
    C.done(SLUG, BEATS, [
        frame((60.0, 0.0, -80.0), 400.0, 0.30, 0.65, pad=1.0),
        frame((cx, top, -55.0), 125.0, 0.20, 0.70),
        frame((cx, top + 6.0, -60.0), 120.0, 0.45, 0.55),
        frame((100.0, 5.0, -30.0), 270.0, 0.15, 0.55, pad=1.0),
        frame((cx, top, -50.0), 130.0, 0.35, 0.45),
    ], root)


if __name__ == "__main__":
    build()
