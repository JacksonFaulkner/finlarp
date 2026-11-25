"""TRM_SYSTOLIC_ARRAY on the MLCC base board: the accelerator die's matrix unit drawn as an 8x8 grid
of multiply-accumulate cells standing on the bench. Weights load into every cell, activations march
in from the left one column per clock, partial sums march down, and the diagonal wavefront sweeps
across. The last beat shows the payoff: one fetch from SRAM is reused by a whole row.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_systolic_array.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_SYSTOLIC_ARRAY"
BEATS = [
    ("The matrix engine inside an AI chip is a grid of tiny calculators",
     "Inside a TPU, and inside the tensor cores of many other accelerators, sits a systolic array: a square grid of "
     "multiply-accumulate (MAC) cells wired only to their neighbours. Google's TPUs use grids of 128x128 or 256x256 "
     "cells, tens of thousands of multipliers in one block. Here it is drawn 8x8, standing beside the board."),
    ("Each cell: one multiplier, one adder, one stored weight",
     "Every cell holds one number from the weight matrix in a small register. Each clock it takes an input value from "
     "its left neighbour, multiplies it by its weight, adds the partial sum coming from the cell above, and passes both "
     "on: the input to the right, the new sum downward. No cell ever talks to main memory."),
    ("Weights load once and stay put",
     "Before a matrix multiply starts, a tile of weights is shifted into the grid so every cell has its own value. "
     "That tile is then reused for every row of input that flows through, often thousands of rows, before the next "
     "tile is loaded. This weight-stationary design is what the original TPU used."),
    ("Data pulses through like a heartbeat, one step per clock",
     "Inputs enter the left edge staggered by one clock per row, so a diagonal wavefront sweeps across the grid. Each "
     "clock every busy cell does one multiply-add, and finished dot products drop out of the bottom row. The name comes "
     "from systole, the heart's pumping beat: data is pumped through in lockstep."),
    ("One memory fetch feeds a whole row: high throughput per watt",
     "Reading a number from SRAM or HBM costs far more energy than multiplying it. In a systolic array each fetched "
     "value is used by every cell in its row, N times for an N-wide grid, so the chip spends its power on math instead "
     "of data movement. The catch is flexibility: it only shines on big, dense matrix multiplies. Related: Alphabet "
     "(GOOGL), Broadcom (AVGO), Amazon (AMZN), NVIDIA (NVDA)."),
]

N = 8
PIT = 10.0
GX0 = 168.0  # left edge of the grid; the SRAM feeder stands left of it
GY0 = 14.0  # bottom of the grid; the accumulators sit below
GZ = -14.0  # cell back faces; fronts at z = 0


def cell_c(i, j):
    """Centre (front face) of the cell at row i (0 = top) and column j."""
    return (GX0 + PIT * (j + 0.5), GY0 + PIT * (N - i - 0.5), 0.0)


def grid(m, root):
    g = empty("sa", root)
    # the plinth the array stands on: a slab of die silicon with metal stack bands
    bx("sa_si", (GX0 - 22.0, 0.4, GZ - 6.0), (GX0 + N * PIT + 6.0, 4.0, 2.0), m["si"], g)
    for k in range(3):
        bx(f"sa_m{k}", (GX0 - 22.0, 4.0 + k * 1.2, GZ - 6.0), (GX0 + N * PIT + 6.0, 4.6 + k * 1.2, 2.0), m["copper" if k % 2 else "oxide"], g)
    bx("sa_back", (GX0 - 2.0, 7.6, GZ - 2.0), (GX0 + N * PIT + 2.0, GY0 + N * PIT + 2.0, GZ), m["dark"], g)
    wgt = empty("sa_wgt", root)
    diag = [empty(f"sa_d{k}", root) for k in range(2 * N - 1)]
    parts, wires = [], []
    for i in range(N):
        for j in range(N):
            x, y, _ = cell_c(i, j)
            h = PIT * 0.42
            parts.append(bx(f"c{i}_{j}_f", (x - h, y - h, GZ), (x + h, y + h, -0.6), m["mold"], g))
            # multiplier (left), adder (right), weight register (top strip)
            parts.append(bx(f"c{i}_{j}_mul", (x - h + 0.6, y - h + 0.6, -0.6), (x - 0.3, y + 0.8, 0.0), m["fet"], g))
            parts.append(bx(f"c{i}_{j}_add", (x + 0.3, y - h + 0.6, -0.6), (x + h - 0.6, y + 0.8, 0.0), m["driver"], g))
            parts.append(bx(f"c{i}_{j}_reg", (x - h + 0.6, y + 1.4, -0.6), (x + h - 0.6, y + h - 0.6, 0.0), m["gold"], g))
            bx(f"c{i}_{j}_w", (x - h + 0.9, y + 1.7, -0.5), (x + h - 0.9, y + h - 0.9, 0.12), m["h_amber"], wgt)
            bx(f"c{i}_{j}_g", (x - h + 0.8, y - h + 0.8, -0.5), (x + h - 0.8, y + 0.6, 0.15), m["sig"], diag[i + j])
            # neighbour links: right (activations) and down (sums)
            if j < N - 1:
                wires.append(bx(f"c{i}_{j}_lr", (x + h, y - 0.4, -4.0), (x + PIT - h, y + 0.4, -3.0), m["copper"], g))
            if i < N - 1:
                wires.append(bx(f"c{i}_{j}_ud", (x - 0.4, y - PIT + h, -4.0), (x + 0.4, y - h, -3.0), m["alum"], g))
    D.join(parts, "sa_cells")
    D.join(wires, "sa_links")
    # SRAM feeder on the left: a tall bank of cells, one output per row
    sx0, sx1 = GX0 - 20.0, GX0 - 6.0
    bx("sram", (sx0, 7.6, GZ - 2.0), (sx1, GY0 + N * PIT, 0.0), m["hbm"], g)
    for k in range(16):
        y = 9.0 + k * (GY0 + N * PIT - 10.0) / 16
        bx(f"sram_r{k}", (sx0 + 0.6, y, -0.1), (sx1 - 0.6, y + 0.6, 0.1), m["hbm_dram"], g)
    for i in range(N):
        y = cell_c(i, 0)[1]
        bx(f"feed{i}", (sx1, y - 0.4, -4.0), (GX0 + PIT * 0.08, y + 0.4, -3.0), m["copper"], g)
    # accumulators under the bottom row
    accs = []
    for j in range(N):
        x = cell_c(N - 1, j)[0]
        accs.append(bx(f"acc{j}", (x - 3.6, 8.4, GZ), (x + 3.6, GY0 - 1.2, 0.0), m["silicon"], g))
    D.join(accs, "sa_acc")
    acc_g = empty("sa_accg", root)
    for j in range(N):
        x = cell_c(N - 1, j)[0]
        bx(f"accg{j}", (x - 3.0, 9.0, -0.4), (x + 3.0, GY0 - 1.8, 0.15), m["e_blue"], acc_g)
    for o in [wgt, acc_g] + diag:
        show(o, [])
    top = GY0 + N * PIT
    pts = {"grid": (GX0 + N * PIT / 2, top, GZ / 2), "cell": cell_c(1, 2), "mul": (cell_c(4, 6)[0] - 2.0, cell_c(4, 6)[1] - 1.0, 0.0),
           "reg": (cell_c(2, 6)[0], cell_c(2, 6)[1] + 3.0, 0.0), "sram": ((sx0 + sx1) / 2, top - 6.0, 0.0),
           "acc": (cell_c(N - 1, 4)[0], 10.0, 0.0), "diag": cell_c(3, 3), "plinth": (GX0 + 30.0, 4.0, 2.0)}
    return pts, wgt, diag, acc_g, (sx1, top)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root)
    pk = b["pk"]
    pts, wgt, diag, acc_g, (sx1, top) = grid(m, root)
    C.magnify(m, root, pk["die_r"], (GX0 - 22.0, 40.0, -10.0))
    show(b["die_glow"], [(F(3, 0.0), F(5, 0))])

    # beat 1: one cell lit to show its parts; beat 2: weights slide in from the top and stay
    show(diag[3], [(F(1, 0.2), F(2, 0))])
    show(wgt, [(F(2, 0.35), F(5, 0))])
    for j in range(N):
        x = cell_c(0, j)[0]
        run(root, f"wl{j}", [(x, top + 14.0, 1.0), (x, top - 2.0, 1.0), (x, GY0 + 6.0, 1.0)], 3, 0.8, m["h_amber"], 2, 0.0, 0.25, 22)

    # beat 3: activations in from the left, staggered per row; sums down; the wavefront sweeps
    for i in range(N):
        y = cell_c(i, 0)[1]
        run(root, f"act{i}", [(sx1, y, 1.0), (GX0 + N * PIT, y, 1.0)], 3, 0.8, m["chan"], [3, 4], 0.03 + 0.05 * i, 0.35 + 0.05 * i, 45)
    for j in range(N):
        x = cell_c(0, j)[0] + 2.5
        run(root, f"ps{j}", [(x, top, 1.2), (x, GY0 - 3.0, 1.2)], 2, 0.7, m["sig"], 3, 0.08 + 0.05 * j, 0.45 + 0.05 * j, 45)
    for k, g_ in enumerate(diag):
        blink(g_, 3, [k, k + 2 * N - 1 if k + 2 * N - 1 < 32 else k], n=32, on=1.6)
    blink(acc_g, 3, [16, 18, 20, 22, 24, 26, 28, 30], n=32, on=0.9)

    # beat 4: one fetch from SRAM reused across a whole row (bright bead runs along row 3), cool chip
    y3 = cell_c(3, 0)[1]
    run(root, "fetch", [(sx1 - 7.0, y3, 1.0), (sx1, y3, 1.0), (GX0 + N * PIT, y3, 1.0)], 4, 1.2, m["v12"], 4, 0.05, 0.6, 50)
    for k, g_ in enumerate(diag):
        blink(g_, 4, [k % 16], n=16, on=1.0)
    rise(root, "sh", (GX0 + N * PIT / 2, top + 2.0, GZ / 2), 3, 0.7, m["heat"], 4, 0.1, 0.8, 14.0, 60, (30.0, 4.0))

    C.tags(root, {
        0: [("GPU / TPU package", pk["top"]), ("matrix unit, 8x8 shown", pts["grid"]), ("real: 128x128 to 256x256", pts["plinth"])],
        1: [("one MAC cell", pts["cell"]), ("multiplier + adder", pts["mul"]), ("weight register", pts["reg"]),
            ("SRAM feeds each row", pts["sram"])],
        2: [("weights shift in from top", pts["grid"]), ("then stay put", pts["reg"]), ("reused for every input row", pts["diag"])],
        3: [("inputs flow right", pts["sram"]), ("partial sums flow down", pts["grid"]), ("diagonal wavefront", pts["diag"]),
            ("results drop out here", pts["acc"])],
        4: [("one fetch, used 8 times", pts["sram"]), ("math, not data movement", pts["diag"]), ("GOOGL, AVGO, AMZN, NVDA", pts["acc"])],
    })
    cg = (GX0 + N * PIT / 2 - 8.0, GY0 + N * PIT / 2, -6.0)
    C.done(SLUG, BEATS, [
        frame((40.0, 10.0, -80.0), 380.0, 0.32, 0.55, pad=1.0),
        frame(cell_c(2, 3), 72.0, 0.12, 0.12),
        frame(cg, 105.0, 0.12, 0.25),
        frame(cg, 100.0, 0.05, 0.08),
        frame((GX0 + 20.0, GY0 + N * PIT / 2, -6.0), 110.0, 0.28, 0.20),
    ], root)


if __name__ == "__main__":
    build()
