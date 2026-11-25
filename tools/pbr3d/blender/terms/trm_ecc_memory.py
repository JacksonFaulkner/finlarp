"""TRM_ECC_MEMORY: Terms-tab overview for ECC memory, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_ecc_memory.py

A DRAM bank on the bench with eight data columns and one extra check-bit column (purple). A
particle strike flips one cell; on READ the word plus check bits run to the memory controller's
ECC block, which finds the bad bit and sends the corrected word on. Two flips get flagged.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F, empty, show  # noqa: E402
from power_vrm_detail import bx, frame, present, run  # noqa: E402

SLUG = "TRM_ECC_MEMORY"
BEATS = [
    ("Server memory stores extra check bits with every word",
     "ECC memory adds check bits beside the data. A common scheme stores 8 check bits per 64 data bits, so a module "
     "carries 72 bits per word and spends 12.5 percent of its raw capacity on protection. GPU HBM and server DIMMs "
     "use it."),
    ("The check bits are computed from the data on write",
     "When the controller writes a word it computes the check bits from the data (a Hamming-style code) and stores "
     "both. In the bank they look like one more column of ordinary cells."),
    ("A stray particle or row hammer flips a bit",
     "Cosmic-ray neutrons, alpha particles and row hammer can flip a cell's charge. On large clusters with petabytes "
     "of DRAM this happens many times a day, and without ECC the wrong value would be read back silently."),
    ("On read, the controller finds and fixes the bad bit",
     "The controller recomputes the check bits from the data it read and compares them with the stored ones. The "
     "mismatch (the syndrome) points to the exact flipped bit, which is corrected before the GPU sees it. This costs "
     "a few nanoseconds."),
    ("Two flips are detected, not fixed",
     "Standard SECDED ECC corrects one bad bit and detects two, so the system can retire the page or stop the job "
     "rather than train on corrupt data. Stronger chipkill codes survive a whole failed chip. Related: Micron (MU), "
     "Samsung (005930.KS), SK hynix (000660.KS), Dell (DELL)."),
]

BX0, BX1, BZ0, BZ1 = 160.0, 214.0, -76.0, -32.0
ROWS, COLS = 6, 9
ROW = 2
CX, CZ = 234.0, -20.0  # controller ECC block


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=ROWS, cols=COLS)
    pts = bk["pts"]
    present(bk["g"], [(F(0, 0.45), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), pts["top"])
    g = empty("ecc", root)
    present(g, [(F(0, 0.0), F(5, 0))])
    m["flip"] = C.mat("t_flip", (1.0, 0.18, 0.12), emit=(1.0, 0.18, 0.12), strength=4.5)

    # check-bit column tint (always on)
    for r in range(ROWS):
        x, y, z = pts["cell"](r, COLS - 1)
        bx(f"chk{r}", (x - 0.9, y - 7.1, z - 0.9), (x + 0.9, y + 0.2, z + 0.9), m["rf"], g)
    # controller with ECC block
    top = C.chip(m, g, "ctrl", (CX, 0.0, CZ), 18.0, 18.0, h=2.4, pins=8)
    blk = bx("ecc_blk", (CX - 5.0, top[1], CZ - 5.0), (CX + 5.0, top[1] + 2.0, CZ + 5.0), m["die"], g)
    on = bx("ecc_on", (CX - 5.2, top[1], CZ - 5.2), (CX + 5.2, top[1] + 2.2, CZ + 5.2), m["sig"], g)
    show(on, [(F(3, 0.35), F(3, 0.75)), (F(4, 0.35), F(4, 0.85))])
    bad = bx("ecc_bad", (CX - 5.3, top[1], CZ - 5.3), (CX + 5.3, top[1] + 2.3, CZ + 5.3), m["warn"], g)
    show(bad, [(F(4, 0.6), F(5, 0))])
    io = pts["io"]
    bus = [io, (CX - 9.0, 1.5, io[2]), (CX - 9.0, 1.5, CZ)]
    bx("bus", (io[0] - 1.0, 0.1, io[2] - 0.6), (CX - 9.0, 0.5, io[2] + 0.6), m["copper"], g)

    # beat 1: write data + check bits into row ROW
    show(bk["wl"][ROW][1], [(F(1, 0.1), F(1, 0.8)), (F(3, 0.0), F(3, 0.3)), (F(4, 0.0), F(4, 0.3))])
    show(bk["rb_on"], [(F(1, 0.0), F(1, 0.8)), (F(3, 0.0), F(3, 0.4)), (F(4, 0.0), F(4, 0.4))])
    run(g, "wr", list(reversed(bus)), 4, 0.6, m["dram_bead_w"], [1], 0.0, 0.3, 25)
    K.write_back(m, bk, ROW, 1, 0.3, 0.7)

    # beat 2: particle strikes -> flip one cell (and a second for beat 4)
    flips = [(ROW, 3, 2), (ROW, 6, 4)]
    for k, (r, c, bt) in enumerate(flips):
        x, y, z = pts["cell"](r, c)
        run(g, f"ray{k}", [(x - 30.0, y + 60.0, z - 10.0), (x, y + 0.5, z)], 1, 0.8, m["warn"], [bt], 0.05, 0.1, 35)
        f = empty(f"flipg{k}", g)
        bx(f"flip{k}", (x - 4.5, y + 4.0, z - 4.5), (x + 4.5, y + 5.5, z + 4.5), m["flip"], f)
        end = F(3, 0.8) if k == 0 else F(5, 0)
        show(f, [(F(bt, 0.45), end)])
    # beats 3/4: read out to the controller, corrected word goes on to the GPU
    K.charge_share(m, bk, ROW, 3, 0.0, 0.2)
    run(g, "rd3", bus, 4, 0.6, m["dram_bead"], [3, 4], 0.15, 0.35, 25)
    out = [(CX, top[1] + 2.0, CZ), (CX, 8.0, CZ + 12.0), (pk["top"][0] + 30.0, 8.0, CZ + 30.0)]
    run(g, "fix", out, 4, 0.6, m["sig"], [3], 0.6, 0.85, 30)

    C.tags(root, {
        0: [("HBM: ECC on every word", pk["hbm"]), ("GPU package", pk["top"]), ("memory controller", (CX, 2.4, CZ))],
        1: [("64 data bits", pts["cell"](0, 3)), ("+ 8 check bits", pts["cell"](0, COLS - 1)), ("write data + check", pts["rb"](4))],
        2: [("particle strike", pts["cell"](ROW, 3)), ("one bit flipped", pts["sa"](3))],
        3: [("syndrome locates the bit", (CX, 4.6, CZ)), ("corrected word to GPU", out[1])],
        4: [("second flip", pts["cell"](ROW, 6)), ("two bad bits: flagged", (CX, 4.6, CZ))],
    })
    cx, cz = (BX0 + CX + 8.0) / 2, (BZ0 + CZ) / 2
    C.done(SLUG, BEATS, [
        frame((40.0, 0.0, -60.0), 360.0, 0.30, 0.60, pad=1.0),
        frame(((BX0 + BX1) / 2, 4.0, (BZ0 + BZ1) / 2), 75.0, 0.25, 0.55),
        frame(((BX0 + BX1) / 2, 4.0, (BZ0 + BZ1) / 2), 80.0, 0.35, 0.45),
        frame((cx, 4.0, cz), 105.0, 0.25, 0.50),
        frame((cx, 4.0, cz), 105.0, 0.30, 0.50),
    ], root)


if __name__ == "__main__":
    build()
