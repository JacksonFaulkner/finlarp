"""TRM_ROW_PRECHARGE_TIME: Terms-tab overview for tRP, the time to close a row before opening another.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_row_precharge_time.py

Same bank + command timeline stage as trm_cas_latency.py. Beats: hbm, row 3 open serving reads,
PRECHARGE with the tRP bar (write-back, bitlines equalize), ACTIVATE of row 6 after tRP, numbers.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402,F401
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from trm_cas_latency import TZ, cmd, fill, plan, stage, tx  # noqa: E402

SLUG = "TRM_ROW_PRECHARGE_TIME"
BEATS = [
    ("HBM stacks next to the GPU: one open row per bank",
     "Each bank of an HBM die can hold only one row open in its row buffer. To reach data in a different row, the "
     "bank must first close the current one."),
    ("Row 3 is open and serving reads",
     "Reads to row 3 come straight out of the row buffer. A request now arrives for row 6, which is a row conflict: "
     "row 3 has to be put away first."),
    ("PRECHARGE closes the row: the tRP bar fills",
     "PRECHARGE writes the buffer's values back into the row 3 cells, drops the wordline, and pulls every bitline "
     "back to half voltage so the next row's tiny charge can be sensed. Those cycles are tRP."),
    ("After tRP, ACTIVATE can open row 6",
     "Only when the bitlines are equalized may the controller issue ACTIVATE for row 6. Starting early would leave "
     "old voltage on the bitlines and the sense amps would misread the new row."),
    ("A row conflict costs tRP + tRCD + CL",
     "tRP is typically 13 to 16 ns. A conflict pays tRP, then tRCD, then CL, around 40 ns before data, versus about "
     "14 ns for an open-row hit. Controllers choose open- or closed-page policies to balance this. "
     "Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS), Rambus (RMBS)."),
]


def build():
    n = len(BEATS)
    m, root, b, bk = stage(SLUG, n)
    pts, pk = bk["pts"], b["pk"]
    end = F(n, 0)
    K.row_open(bk, 3, [(F(1, 0), F(2, 0.5))])
    K.bl_show(bk, "hi", [(F(1, 0), F(2, 0.4))])
    K.io_flow(m, bk, [3, 4, 5, 6], 1, 0.1, 0.9)
    cmd(m, bk, "tl_pre", tx(0.05), 2, 0.05, n)
    K.write_back(m, bk, 3, 2, 0.05, 0.45)
    K.bl_show(bk, "eq", [(F(2, 0.5), F(3, 0.2))])
    fill(m, bk["g"], "tl_rp", tx(0.07), tx(0.52), 0.6, TZ, 2, 0.1, 0.9, n - 1, n=10)
    cmd(m, bk, "tl_act", tx(0.54), 3, 0.05, n)
    K.row_open(bk, 6, [(F(3, 0.15), end)])
    K.charge_share(m, bk, 6, 3, 0.15, 0.7)
    K.bl_show(bk, "hi", [(F(3, 0.6), end)])
    fill(m, bk["g"], "tl_rcd", tx(0.56), tx(0.95), 0.6, TZ, 3, 0.15, 0.9, n - 1, n=8, mt="dram_rb_on")
    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]), ("one bank on the bench", pts["top"])],
        1: [("row 3 open", pts["wl"](3)), ("reads from row buffer", pts["io"]), ("next request: row 6", pts["wl"](6))],
        2: [("PRE: write back row 3", pts["wl"](3)), ("bitlines back to half", pts["bl"](5)),
            ("tRP bar", (tx(0.3), 1.5, TZ))],
        3: [("ACT row 6 after tRP", (tx(0.54), 4.0, TZ)), ("row 6 opens", pts["wl"](6))],
        4: [("conflict ~ tRP+tRCD+CL", (tx(0.5), 1.5, TZ)), ("one open row per bank", pts["rb"](3))],
    })
    C.done(SLUG, BEATS, plan(n), root)


if __name__ == "__main__":
    build()
