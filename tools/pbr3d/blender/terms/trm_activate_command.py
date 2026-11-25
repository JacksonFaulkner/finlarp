"""TRM_ACTIVATE_COMMAND: the Terms-tab overview for DRAM ACTIVATE, on the MLCC base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_activate_command.py

Writes assets/term_TRM_ACTIVATE_COMMAND.glb. Captions live in specs/terms/TRM_ACTIVATE_COMMAND.json.

The GPU board's HBM stacks feed the GPU; one bank of an HBM die is drawn large on the bench, cut
open: a grid of 1T1C cells, wordlines across the rows, bitlines down the columns, sense amps and a
row buffer at the edge. ACTIVATE raises one wordline, the row's cells share charge onto their
bitlines, the sense amps read each 0 or 1, and the row buffer holds the whole row.

Beats:
  0 hbm      HBM stacks beside the GPU package
  1 bank     the bank, row closed: sense amps idle
  2 activate wordline 3 rises, charge shares to the bitlines, sense amps amplify, row buffer loads
  3 read     READ commands pick columns from the open row out to the I/O edge
  4 tRCD     the wait between ACTIVATE and the first read, and why controllers keep rows open
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from power_vrm_detail import frame, present  # noqa: E402

SLUG = "TRM_ACTIVATE_COMMAND"
BEATS = [
    ("HBM stacks sit beside the GPU and feed it",
     "AI accelerators pull their data from HBM, stacks of DRAM dies next to the GPU package. Each die is split into "
     "many banks, and each bank is a grid of tiny cells: one capacitor and one transistor per bit."),
    ("A bank is a grid: wordlines run along rows, bitlines down columns",
     "Each cell holds its bit as charge on a tiny capacitor. A wordline (one per row) switches the access transistors in "
     "that row, and a bitline (one per column) carries the charge out. Before ACTIVATE the row is closed: the sense amps "
     "are idle and no cell can be read."),
    ("ACTIVATE opens one whole row onto the sense amps",
     "The controller sends ACTIVATE with a row address. That wordline rises, every cell in the row shares its small "
     "charge onto its bitline, and the sense amps push each bitline to a full 0 or 1. The row buffer now holds the "
     "whole row."),
    ("Reads and writes then hit columns of the open row",
     "While the row stays open, READ and WRITE commands pick columns from the row buffer and stream them to the I/O "
     "pins. A column outside the open row cannot be reached without another ACTIVATE."),
    ("The wait from ACTIVATE to the first read costs time",
     "The delay from ACTIVATE to a READ (tRCD) sets how fast a bank answers random requests, and so does the time a "
     "row must stay open. For AI workloads these gaps limit effective memory bandwidth, so controllers batch accesses "
     "to rows that are already open. Related: Micron (MU), SK hynix (000660.KS), Rambus (RMBS)."),
]

BX0, BX1, BZ0, BZ1 = 160.0, 236.0, -72.0, -24.0
ROWS, COLS = 8, 12


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    b = C.base(m, root)
    pk, ph = b["pk"], b["ph"]
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=ROWS, cols=COLS)
    pts = bk["pts"]
    present(bk["g"], [(F(1, 0), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), pts["top"])

    # beat 2: ACTIVATE on row 3
    K.row_open(bk, 3, [(F(2, 0.05), F(5, 0))])
    K.charge_share(m, bk, 3, 2, 0.05, 0.6)
    K.bl_show(bk, "hi", [(F(2, 0.5), F(5, 0))])

    # beat 3 and 4: READ columns out of the open row
    K.io_flow(m, bk, [2, 3, 4, 5, 6, 7], 3, 0.0, 0.9)
    K.io_flow(m, bk, [8, 9], 4, 0.0, 0.5)

    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]), ("each stack: many banks", (-70.0, 2.0, -70.0))],
        1: [("bank: rows x columns of cells", pts["top"]), ("wordline: one per row", pts["wl"](3)),
            ("bitline: one per column", pts["bl"](5)), ("sense amps idle, row closed", pts["sa"](5))],
        2: [("ACT: wordline 3 rises", pts["wl"](3)), ("cells share charge to bitlines", pts["bl"](4)),
            ("sense amps read 0 or 1", pts["sa"](4)), ("row buffer holds the row", pts["rb"](4))],
        3: [("READ: columns from the open row", pts["io"]), ("row buffer to I/O pins", pts["rb"](7))],
        4: [("ACT to READ: the tRCD gap", pts["sa"](6)), ("row stays open for reuse", pts["rb"](2))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame(((BX0 + BX1) / 2, 6.0, (BZ0 + BZ1) / 2), 130.0, 0.25, 0.45),
        frame(((BX0 + BX1) / 2, 6.0, -48.0), 90.0, 0.20, 0.40),
        frame((BX1 - 10.0, 6.0, -30.0), 100.0, 0.25, 0.40),
        frame((60.0, 0.0, -70.0), 330.0, 0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
