"""TRM_MEMORY_LATENCY: the Terms-tab overview for memory latency, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_memory_latency.py

A request bead leaves the GPU die for an HBM stack and the data comes back. On the bench a
timeline adds up the pieces: controller queue, ACTIVATE (tRCD), column read (CL) and the trip
back, against a steady stream that shows bandwidth is a different number.

Beats:
  0 miss     the GPU misses in cache and sends a read
  1 queue    the controller queue
  2 array    tRCD + CL inside the DRAM
  3 return   the trip back; total ~100+ ns
  4 vs bw    bandwidth vs latency, CXL trade-off
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from power_vrm_detail import bx, mat, frame, present, run  # noqa: E402
from sand_overview import empty, show  # noqa: E402

SLUG = "TRM_MEMORY_LATENCY"
BEATS = [
    ("A cache miss sends a read out to memory",
     "When data is not in the GPU's caches, a read request leaves the die for an HBM stack. Every thread that needs "
     "that data waits until it comes back. Memory latency is that round-trip time."),
    ("First the request waits in the memory controller",
     "The controller holds a queue of requests and reorders them to reuse open rows and avoid bank conflicts. Under "
     "heavy load this queueing can be the largest piece of the delay."),
    ("Inside the DRAM: open the row, then read the column",
     "If the row is closed the chip needs ACTIVATE (tRCD, about 14 ns) and then a column read (CAS latency, about "
     "14 ns more). A row that another request left open costs a PRECHARGE on top."),
    ("Then the data rides back; the total is around 100 ns",
     "Add the bus or link trip both ways and the result is typically 80-120 ns for local DRAM, hundreds of GPU "
     "clock cycles. GPUs hide it by keeping thousands of threads in flight."),
    ("Bandwidth is not latency",
     "A system can move terabytes per second and still stall on each miss: bandwidth is how wide the pipe is, "
     "latency is how long it is. CXL memory adds capacity but also adds a link hop, often 100+ ns more. Related: "
     "Micron (MU), Astera Labs (ALAB), Intel (INTC)."),
]

TX0, TX1 = 155.0, 245.0
LANES = {"q": -38.0, "arr": -27.0, "ret": -16.0, "bw": -5.0}
QX0, QX1, QZ0, QZ1 = 155.0, 178.0, -72.0, -52.0
BX0, BX1, BZ0, BZ1 = 188.0, 244.0, -74.0, -48.0


def bigfill(m, parent, name, x0, x1, y, z, beat, u0, u1, until_beat, n=10, mt="dram_timer", hw=3.6, h=3.0):
    """kit_dram.fill, about 3x thicker: blocks appear left to right over beat/u0..u1."""
    g = empty(name, parent)
    w = (x1 - x0) / n
    for k in range(n):
        a = x0 + w * k
        blk = empty(f"{name}_e{k}", g)
        bx(f"{name}_{k}", (a + 0.3, y, z - hw), (a + w - 0.3, y + h, z + hw), m[mt], blk)
        show(blk, [(F(beat, u0 + (u1 - u0) * k / n), F(until_beat + 1, 0))])
    return g


def lane(m, parent, name, x0, x1, z, mt="dram_sub"):
    g = empty(name + "_e", parent)
    bx(name, (x0, 0.2, z - 4.2), (x1, 0.8, z + 4.2), m[mt], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    for k, c in {"lq": (1.0, 0.85, 0.35), "lr": (1.0, 0.45, 0.10), "lc": (1.0, 0.20, 0.25),
                 "lb": (0.15, 0.85, 1.0), "le": (0.25, 0.45, 1.0)}.items():
        m[k] = mat(f"lat_{k}", tuple(v * 0.6 for v in c), emit=c, strength=1.4)
    b = C.base(m, root)
    pk = b["pk"]
    top, hbm = pk["top"], pk["hbm"]
    go = [(top[0], top[1] + 2.0, top[2]), (hbm[0], top[1] + 2.0, hbm[2]), (hbm[0], hbm[1] + 2.0, hbm[2])]
    back = list(reversed(go))
    run(root, "req0", go, 1, 2.2, m["warn"], 0, 0.2, 0.2, 50)
    run(root, "req", go, 3, 1.6, m["warn"], [1, 2], 0.0, 0.3, 50)
    run(root, "dat", back, 3, 1.6, m["dram_bead"], 3, 0.0, 0.3, 50)
    run(root, "bw", go, 24, 1.0, m["dram_bead"], 4, 0.0, 0.9, 30)
    run(root, "bwb", back, 24, 1.0, m["dram_bead_w"], 4, 0.0, 0.9, 30)

    # controller queue: a box of request slots on the bench
    qg = empty("queue", root)
    bx("q_box", (QX0, 0.0, QZ0), (QX1, 3.0, QZ1), m["dram_sub"], qg)
    slots = []
    for i in range(6):
        z = QZ0 + 2.0 + i * 3.0
        bx(f"q_slot{i}", (QX0 + 2.0, 3.0, z), (QX1 - 2.0, 3.6, z + 2.0), m["dram_rb"], qg)
        s_on = empty(f"q_on_e{i}", qg)
        bx(f"q_on{i}", (QX0 + 2.5, 3.6, z + 0.2), (QX1 - 2.5, 4.6, z + 1.8), m["warn"], s_on)
        show(s_on, [(F(1, 0.1 * i), F(2, 0.1 + 0.1 * i))])
        slots.append((QX1, 4.0, z + 1.0))
    present(qg, [(F(1, 0), F(5, 0))])
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=6, cols=8)
    pts = bk["pts"]
    present(bk["g"], [(F(1, 0), F(5, 0))])
    C.magnify(m, root, (hbm[0], 0.0, hbm[2]), pts["top"])
    run(root, "q2b", [slots[2], ((QX1 + BX0) / 2, 6.0, slots[2][2]), pts["wl"](2)], 3, 1.4, m["warn"], 1, 0.6, 0.9, 25)
    K.row_open(bk, 2, [(F(2, 0.05), F(5, 0))])
    K.charge_share(m, bk, 2, 2, 0.05, 0.45)
    K.bl_show(bk, "hi", [(F(2, 0.45), F(5, 0))])
    K.io_flow(m, bk, [2, 3, 4, 5], 2, 0.5, 0.9)
    K.io_flow(m, bk, [3, 4, 5, 6], 3, 0.0, 0.5)

    for k, z in LANES.items():
        show(lane(m, root, f"lane_{k}", TX0, TX1, z), [(F(1, 0), F(5, 0))])
    bigfill(m, root, "f_q", TX0, TX0 + 30.0, 0.8, LANES["q"], 1, 0.1, 0.8, 4, n=6, mt="lq")
    bigfill(m, root, "f_rcd", TX0 + 30.0, TX0 + 50.0, 0.8, LANES["arr"], 2, 0.05, 0.45, 4, n=4, mt="lr")
    bigfill(m, root, "f_cl", TX0 + 50.0, TX0 + 70.0, 0.8, LANES["arr"], 2, 0.5, 0.9, 4, n=4, mt="lc")
    bigfill(m, root, "f_ret", TX0 + 70.0, TX1, 0.8, LANES["ret"], 3, 0.05, 0.6, 4, n=5, mt="lb")
    bigfill(m, root, "f_bw", TX0, TX1, 0.8, LANES["bw"], 4, 0.0, 0.5, 4, n=18, mt="le")
    mid = (TX0 + TX1) / 2

    C.tags(root, {
        0: [("GPU: cache miss", top), ("read heads to HBM", hbm)],
        1: [("controller queue", (QX0 + 10.0, 5.0, QZ0 + 8.0)), ("queue time", (TX0 + 15.0, 4.0, LANES["q"])),
            ("reorders for open rows", (QX1, 5.0, QZ1 - 3.0))],
        2: [("tRCD ~14 ns: ACTIVATE", (TX0 + 40.0, 4.0, LANES["arr"])), ("CL ~14 ns: column read", (TX0 + 60.0, 4.0, LANES["arr"])),
            ("row opens in the bank", pts["wl"](2))],
        3: [("data leaves the bank", pts["io"]), ("trip back over the bus", (TX0 + 80.0, 4.0, LANES["ret"])), ("total ~80-120 ns", (TX1, 4.0, LANES["ret"]))],
        4: [("bandwidth: width of the pipe", hbm), ("latency: length of the pipe", (mid, 2.0, LANES["bw"])),
            ("CXL: +capacity, +latency", top)],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 300.0, 0.30, 0.65, pad=1.0),
        frame((mid, 3.0, -40.0), 105.0, 0.25, 0.65),
        frame((mid, 3.0, -40.0), 100.0, 0.30, 0.65),
        frame((mid, 3.0, -38.0), 105.0, 0.35, 0.65),
        frame((80.0, 0.0, -60.0), 360.0, 0.30, 0.60, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
