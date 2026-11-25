"""TRM_TARGET_ROW_REFRESH: Terms-tab overview for target row refresh (TRR), on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_target_row_refresh.py

An HBM bank on the bench with a row-activation counter beside it (one bar per row). Row 4 is
hammered, its counter climbs past the threshold, the chip refreshes rows 3 and 5 early, and an
extra refresh slot shows up on the command timeline.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F, empty, show  # noqa: E402
from power_vrm_detail import blink, bx, frame, present  # noqa: E402

SLUG = "TRM_TARGET_ROW_REFRESH"
BEATS = [
    ("TRR lives inside the DRAM dies of every HBM stack",
     "Target row refresh is logic built into the DRAM itself, including the HBM stacks beside a GPU. It exists "
     "because of row hammer: opening one row over and over leaks charge out of the rows next to it."),
    ("The chip counts how often each row is opened",
     "A small tracker next to each bank counts ACTIVATE commands per row, or samples them, since a full counter for "
     "every row would cost too much area. Most rows stay cold; a hammered row climbs fast."),
    ("A hot row crosses the threshold",
     "When one row's count passes a set threshold inside the refresh window, the chip marks it as an aggressor. "
     "The rows on either side are the ones at risk, not the hot row itself."),
    ("Its neighbours get refreshed early",
     "At the next refresh command the chip spends some of the time rewriting the victim rows next to the aggressor, "
     "restoring their full charge before any bit can flip. The counter then resets."),
    ("The extra refreshes cost bandwidth, and TRR can be fooled",
     "Every early refresh ties up the bank, so less time is left for reads, which hurts when memory bandwidth limits "
     "AI work. Attacks that hammer many rows at once have beaten simple trackers, so DDR5 and HBM3 add refresh "
     "management commands from the controller. Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS), "
     "Rambus (RMBS)."),
]

BX0, BX1, BZ0, BZ1 = 160.0, 224.0, -76.0, -28.0
ROWS, COLS = 8, 10
AGG = 4
TX = 232.0  # counter column x


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=ROWS, cols=COLS)
    pts = bk["pts"]
    present(bk["g"], [(F(0, 0.45), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), pts["top"])
    g = empty("trr", root)
    present(g, [(F(1, 0), F(5, 0))])

    # counter: one track per row, blocks grow along +x
    bx("ctr_base", (TX - 1.0, 0.0, BZ0 - 2.0), (TX + 15.0, 0.8, BZ1 + 2.0), m["dram_sub"], g)
    bx("ctr_thr", (TX + 10.6, 0.8, BZ0 - 2.0), (TX + 11.0, 4.0, BZ1 + 2.0), m["warn"], g)
    cold = [2, 1, 3, 2, 0, 1, 2, 1]
    for r in range(ROWS):
        z = pts["row_z"](r)
        n = 7 if r == AGG else cold[r]
        for k in range(n):
            mt = "warn" if (r == AGG and k >= 5) else ("h_amber" if r == AGG else "dram_timer")
            blk = bx(f"c{r}_{k}", (TX + 1.5 * k, 0.8, z - 1.6), (TX + 1.5 * k + 1.2, 2.2, z + 1.6), m[mt], g)
            if r == AGG:
                f0 = F(1, 0.2 + 0.1 * k) if k < 5 else F(2, 0.1 + 0.2 * (k - 5))
            else:
                f0 = F(1, 0.2 + 0.15 * k)
            end = F(4, 0) if r == AGG else F(5, 0)
            show(blk, [(f0, end)])

    _, wl = bk["wl"][AGG]
    blink(wl, 1, range(12), n=12, on=0.5)
    blink(wl, 2, range(10), n=10, on=0.5, u1=0.6)
    show(bk["sa_on"], [(F(3, 0.05), F(3, 0.8))])
    for k, v in enumerate((3, 5)):
        show(bk["wl"][v][1], [(F(3, 0.05 + 0.35 * k), F(3, 0.4 + 0.35 * k))])
        K.write_back(m, bk, v, 3, 0.05 + 0.35 * k, 0.3 + 0.35 * k)
        flag = bx(f"vflag{v}", (BX0 - 6.0, 0.6, pts["row_z"](v) - 1.5), (BX0 - 3.0, 6.0, pts["row_z"](v) + 1.5),
                  m["warn"], g)
        show(flag, [(F(2, 0.6), F(3, 0.4 + 0.35 * k))])

    # command timeline: reads with an extra refresh slot
    zt = BZ0 - 9.0
    K.cmd_strip(m, g, "cmd", BX0, BX1, zt)
    for k in range(12):
        x = BX0 + 2.0 + 5.0 * k
        mt = "h_amber" if k in (5, 6, 7) else "dram_bl_eq"
        blk = bx(f"cmd{k}", (x, 0.6, zt - 1.2), (x + 4.0, 2.0, zt + 1.2), m[mt], g)
        show(blk, [(F(4, 0.05 + 0.06 * k), F(5, 0))])

    C.tags(root, {
        0: [("HBM stacks: DRAM dies", pk["hbm"]), ("GPU package", pk["top"]), ("one bank, cut open", pts["top"])],
        1: [("activation counter per row", (TX + 6.0, 2.0, BZ0)), ("row 4 opened again and again", pts["wl"](AGG))],
        2: [("row 4 passes threshold", (TX + 11.0, 4.0, pts["row_z"](AGG))), ("victims: rows 3 and 5", (BX0 - 4.5, 6.0, pts["row_z"](3)))],
        3: [("refresh row 3, then row 5", pts["wl"](5)), ("charge restored", pts["cell"](3, 4)), ("counter resets", (TX + 3.0, 2.0, pts["row_z"](AGG)))],
        4: [("refresh slots steal read time", (BX0 + 32.0, 2.0, zt)), ("reads", (BX0 + 6.0, 2.0, zt))],
    })
    cx, cz = (BX0 + TX + 14.0) / 2, (BZ0 + BZ1) / 2
    C.done(SLUG, BEATS, [
        frame((40.0, 0.0, -70.0), 360.0, 0.30, 0.60, pad=1.0),
        frame((cx, 4.0, cz), 95.0, 0.25, 0.55),
        frame((cx + 10.0, 4.0, cz), 80.0, 0.25, 0.55),
        frame((cx - 5.0, 4.0, cz), 85.0, 0.30, 0.50),
        frame(((BX0 + BX1) / 2, 2.0, BZ0 - 9.0), 80.0, 0.20, 0.75),
    ], root)


if __name__ == "__main__":
    build()
