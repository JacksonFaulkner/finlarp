"""TRM_SRAM: Terms-tab overview for SRAM, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_sram.py

The GPU die's on-chip SRAM blown up on the bench: one 6T cell drawn large (two cross-coupled
inverters plus two access transistors, wordline across, BL / BLB down), a bead loop showing the
latch holding its bit, a read pulling BL down, and a tiled SRAM array next to a lone DRAM 1T1C cell
for the area comparison.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F, empty, show  # noqa: E402
from power_vrm_detail import bx, frame, present, run, wire  # noqa: E402

SLUG = "TRM_SRAM"
BEATS = [
    ("SRAM is the memory built into the GPU die itself",
     "Registers, L1 and L2 caches and shared memory on a GPU are SRAM, made in the same logic process as the cores. "
     "An H100 carries about 50 MB of L2 plus tens of MB more in registers and L1."),
    ("Each bit is six transistors: two inverters holding each other",
     "Two inverters are wired in a loop, so each one's output drives the other's input. The loop settles at 0 or 1 "
     "and stays there as long as power is on. Two access transistors connect it to the bitlines."),
    ("No refresh: the latch holds its bit by itself",
     "Unlike a DRAM capacitor, the latch is actively driven, so it never leaks away and needs no refresh. That is "
     "why SRAM answers in about a nanosecond, many times faster than HBM."),
    ("A read raises the wordline and the cell pulls one bitline down",
     "The wordline turns on both access transistors, the side holding 0 pulls its bitline slightly low, and a sense "
     "amp reads the difference between BL and BLB. Writes overpower the latch through the same two bitlines."),
    ("Fast but big: six transistors per bit versus one plus a capacitor",
     "An SRAM bit takes several times the area of a DRAM bit, and SRAM cells have barely shrunk at 3 nm, so on-chip "
     "memory is costly die area. Groq and Cerebras build inference chips around huge SRAM in place of HBM. Related: "
     "Nvidia (NVDA), TSMC (TSM), Groq (private), Cerebras (CBRS)."),
]

X0, X1, Z0, Z1 = 162.0, 214.0, -78.0, -30.0
Y = 0.6


def fet(m, g, name, x, z, kind):
    """One transistor: si body, two diffusion pads, poly gate across."""
    body = "nplus" if kind == "n" else "pplus"
    bx(f"{name}_b", (x - 4.0, Y, z - 3.0), (x + 4.0, Y + 1.2, z + 3.0), m["si"], g)
    bx(f"{name}_s", (x - 3.6, Y + 1.2, z - 2.6), (x - 1.2, Y + 1.8, z + 2.6), m[body], g)
    bx(f"{name}_d", (x + 1.2, Y + 1.2, z - 2.6), (x + 3.6, Y + 1.8, z + 2.6), m[body], g)
    bx(f"{name}_g", (x - 0.7, Y + 1.2, z - 3.6), (x + 0.7, Y + 3.0, z + 3.6), m["poly"], g)
    return (x, Y + 3.0, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    show(b["die_glow"], [(F(0, 0.2), F(0, 0.9))])
    g = empty("sram", root)
    present(g, [(F(0, 0.4), F(5, 0))])
    bx("sub", (X0 - 4.0, 0.0, Z0 - 4.0), (X1 + 4.0, Y, Z1 + 4.0), m["dram_sub"] if "dram_sub" in m else m["si"], g)
    C.magnify(m, root, pk["die"], ((X0 + X1) / 2, 6.0, (Z0 + Z1) / 2))

    xm = (X0 + X1) / 2
    zl, zr = Z0 + 14.0, Z0 + 34.0
    # inverter A (left) and B (right): pull-up p on top row, pull-down n on bottom row
    pa = fet(m, g, "pu_a", xm - 9.0, zl - 6.0, "p")
    na = fet(m, g, "pd_a", xm - 9.0, zl + 4.0, "n")
    pb = fet(m, g, "pu_b", xm + 9.0, zr - 6.0, "p")
    nb = fet(m, g, "pd_b", xm + 9.0, zr + 4.0, "n")
    axa = fet(m, g, "ax_a", X0 + 6.0, (zl + zr) / 2, "n")
    axb = fet(m, g, "ax_b", X1 - 6.0, (zl + zr) / 2, "n")
    # rails
    bx("vdd", (X0, Y, Z0 + 1.0), (X1, Y + 1.0, Z0 + 2.5), m["copper"], g)
    bx("gnd", (X0, Y, Z1 - 2.5), (X1, Y + 1.0, Z1 - 1.0), m["alum"], g)
    # wordline across both access gates, bitlines down each side
    ywl = Y + 6.0
    bx("wl", (X0 - 2.0, ywl, (zl + zr) / 2 - 0.6), (X1 + 2.0, ywl + 0.8, (zl + zr) / 2 + 0.6), m["dram_wl"], g)
    wlg = bx("wlg", (X0 - 2.0, ywl - 0.05, (zl + zr) / 2 - 0.7), (X1 + 2.0, ywl + 0.85, (zl + zr) / 2 + 0.7), m["h_amber"], g)
    show(wlg, [(F(3, 0.1), F(3, 0.85))])
    for nm, x in (("bl", X0 + 2.0), ("blb", X1 - 2.0)):
        bx(nm, (x - 0.5, Y + 8.0, Z0), (x + 0.5, Y + 8.8, Z1), m["dram_bl"], g)
    # cross-couple wires: node Q (A out) -> B gates, node QB (B out) -> A gates
    q = [(xm - 6.0, pa[1], zl - 1.0), (xm - 6.0, Y + 5.0, zl - 1.0), (xm + 9.0, Y + 5.0, zr - 1.0), (xm + 9.0, pb[1], zr - 1.0)]
    qb = [(xm + 6.0, pb[1], zr + 1.0), (xm + 6.0, Y + 4.0, zr + 1.0), (xm - 9.0, Y + 4.0, zl + 1.0), (xm - 9.0, pa[1], zl + 1.0)]
    wire("q", q, 0.35, m["copper"], g)
    wire("qb", qb, 0.35, m["copper"], g)
    loop = q + qb[1:] + [q[0]]
    run(g, "latch", loop, 6, 0.6, m["sig"], [1, 2, 3, 4], 0.0, 0.9, 50)
    hold = bx("q_hi", (xm - 7.0, Y + 1.8, zl - 2.0), (xm - 5.0, Y + 3.2, zl), m["e_blue"], g)
    show(hold, [(F(2, 0.0), F(5, 0))])
    # read: bead from access A out onto BL, BL dips
    run(g, "rd", [(axa[0], axa[1], axa[2]), (X0 + 2.0, Y + 8.8, axa[2]), (X0 + 2.0, Y + 8.8, Z1 + 6.0)], 4, 0.5,
        m["dram_bead"] if "dram_bead" in m else m["e_blue"], [3], 0.2, 0.8, 30)
    sa = bx("sense", (X0, Y, Z1 + 3.0), (X1, Y + 2.0, Z1 + 6.0), m["dim_glow"], g)
    show(sa, [(F(3, 0.4), F(3, 0.95))])

    # beat 4: tiled SRAM array vs one DRAM cell
    arr = empty("arr", g)
    for i in range(6):
        for j in range(4):
            x, z = 222.0 + 4.2 * i, Z0 + 4.0 + 4.2 * j
            bx(f"a{i}_{j}", (x, Y, z), (x + 3.6, Y + 1.2, z + 3.6), m["si"], arr)
            for t in range(3):
                bx(f"a{i}_{j}_{t}", (x + 0.4 + 1.1 * t, Y + 1.2, z + 0.4), (x + 1.2 + 1.1 * t, Y + 2.0, z + 3.2), m["poly"], arr)
    dc = empty("dcell", g)
    bx("dc_t", (230.0, Y, Z0 + 26.0), (231.4, Y + 1.2, Z0 + 27.4), m["si"], dc)
    bx("dc_c", (230.2, Y + 1.2, Z0 + 26.2), (231.2, Y + 6.0, Z0 + 27.2), m["ceramic"], dc)
    present(arr, [(F(4, 0.0), F(5, 0))])
    present(dc, [(F(4, 0.3), F(5, 0))])

    C.tags(root, {
        0: [("GPU die: caches are SRAM", pk["die"]), ("HBM: off-die DRAM", pk["hbm"]), ("one SRAM cell, enlarged", (xm, 6.0, Z0 + 24.0))],
        1: [("inverter A", (xm - 9.0, 3.6, zl - 6.0)), ("inverter B", (xm + 9.0, 3.6, zr + 4.0)), ("access transistors", (X0 + 6.0, 3.6, (zl + zr) / 2))],
        2: [("latch loop holds the bit", q[2]), ("node Q = 1, no refresh", (xm - 6.0, 3.2, zl - 1.0))],
        3: [("wordline on", (X1 + 2.0, ywl + 0.8, (zl + zr) / 2)), ("BL pulled down", (X0 + 2.0, Y + 8.8, Z1)), ("sense amp: BL vs BLB", (xm, Y + 2.0, Z1 + 4.5))],
        4: [("SRAM array: 6T per bit", (230.0, 2.0, Z0 + 6.0)), ("DRAM: 1T + 1 capacitor", (230.7, 6.6, Z0 + 26.7))],
    })
    C.done(SLUG, BEATS, [
        frame((40.0, 0.0, -60.0), 360.0, 0.30, 0.60, pad=1.0),
        frame((xm, 3.0, (Z0 + Z1) / 2), 70.0, 0.25, 0.60),
        frame((xm, 3.0, (Z0 + Z1) / 2), 60.0, 0.35, 0.65),
        frame((xm, 3.0, (Z0 + Z1) / 2 + 3.0), 70.0, 0.20, 0.55),
        frame((228.0, 2.0, Z0 + 16.0), 50.0, 0.30, 0.60),
    ], root)


if __name__ == "__main__":
    build()
