"""TRM_RAS_TO_CAS_DELAY: Terms-tab overview for tRCD, the wait from ACTIVATE to the first READ.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_ras_to_cas_delay.py

Same bank + command timeline stage as trm_cas_latency.py. Beats: hbm, closed bank, ACTIVATE with
the tRCD bar filling while charge shares and the sense amps settle, READ after tRCD, numbers.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402,F401
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from trm_cas_latency import TZ, cmd, fill, plan, stage, tx  # noqa: E402

SLUG = "TRM_RAS_TO_CAS_DELAY"
BEATS = [
    ("HBM stacks next to the GPU serve every memory request",
     "The GPU's data sits in HBM stacks beside the package. A request for a row that is not open has to start "
     "with ACTIVATE, and the bank cannot answer a READ until that row is ready."),
    ("The bank starts closed: no row in the buffer",
     "Bitlines are held at half voltage and the sense amps are idle. Nothing can be read until a wordline opens a row."),
    ("ACTIVATE starts the tRCD clock",
     "ACTIVATE (the old RAS, row address strobe) raises wordline 3. Each cell's tiny charge leaks onto its bitline, "
     "and the sense amps need time to push that small swing to a full 0 or 1. The bar fills for those cycles: tRCD."),
    ("Only after tRCD may READ pick columns",
     "Once the row buffer holds the settled row, the controller may issue READ (the old CAS, column address strobe). "
     "Issue it earlier and the sense amps would hand back garbage, so the controller counts the cycles."),
    ("A row miss pays tRCD plus CL before any data",
     "Typical tRCD is around 13 to 16 ns on DDR5 and HBM. A request to a closed row waits tRCD then CL, roughly double "
     "a hit to an open row, which is why controllers reorder requests to reuse open rows. "
     "Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS), Rambus (RMBS)."),
]


def build():
    n = len(BEATS)
    m, root, b, bk = stage(SLUG, n)
    pts, pk = bk["pts"], b["pk"]
    end = F(n, 0)
    K.bl_show(bk, "eq", [(F(1, 0), F(2, 0.5))])
    cmd(m, bk, "tl_act", tx(0.05), 2, 0.05, n)
    K.row_open(bk, 3, [(F(2, 0.1), end)])
    K.charge_share(m, bk, 3, 2, 0.1, 0.7)
    K.bl_show(bk, "hi", [(F(2, 0.5), end)])
    fill(m, bk["g"], "tl_rcd", tx(0.07), tx(0.52), 0.6, TZ, 2, 0.1, 0.9, n - 1, n=10)
    cmd(m, bk, "tl_read", tx(0.54), 3, 0.05, n)
    fill(m, bk["g"], "tl_cl", tx(0.56), tx(0.95), 0.6, TZ, 3, 0.1, 0.8, n - 1, n=8, mt="dram_rb_on")
    K.io_flow(m, bk, [4, 5, 6, 7], 3, 0.6, 0.95)
    K.io_flow(m, bk, [5, 6], 4, 0.0, 0.6)
    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]), ("one bank on the bench", pts["top"])],
        1: [("bitlines held at half", pts["bl"](5)), ("sense amps idle", pts["sa"](5)), ("row buffer empty", pts["rb"](8))],
        2: [("ACT: wordline 3 rises", pts["wl"](3)), ("tRCD bar: cycles to settle", (tx(0.3), 1.5, TZ)),
            ("sense amps amplify", pts["sa"](4))],
        3: [("READ after tRCD", (tx(0.54), 4.0, TZ)), ("then CL, then data", (tx(0.8), 1.5, TZ)), ("data out", pts["io"])],
        4: [("miss = tRCD + CL ~ 28 ns", (tx(0.5), 1.5, TZ)), ("reuse open rows", pts["rb"](3))],
    })
    C.done(SLUG, BEATS, plan(n), root)


if __name__ == "__main__":
    build()
