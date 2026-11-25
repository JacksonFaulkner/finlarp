"""TRM_ROW_CYCLE_TIME: Terms-tab overview for tRC = tRAS + tRP, ACTIVATE to the next ACTIVATE in a bank.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_row_cycle_time.py

Same bank + command timeline stage as trm_cas_latency.py. Beats: hbm, ACTIVATE + tRAS bar, reads
while the row restores, PRECHARGE + tRP bar (tRC complete), next ACTIVATE and numbers.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402,F401
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from trm_cas_latency import TZ, cmd, fill, plan, stage, tx  # noqa: E402

SLUG = "TRM_ROW_CYCLE_TIME"
BEATS = [
    ("HBM stacks next to the GPU: each bank cycles rows one at a time",
     "Random access across many rows means a bank keeps opening and closing rows. The minimum time for one full "
     "open-and-close cycle in one bank is the row cycle time, tRC."),
    ("ACTIVATE opens row 2 and starts tRAS",
     "ACTIVATE raises wordline 2 and the sense amps latch the row. The row must then stay open at least tRAS, long "
     "enough for the sense amps to restore full charge into the cells they just drained."),
    ("Reads run while the cells are restored",
     "READs pick columns out of the row buffer during tRAS. Meanwhile the amplified bitlines refill each cell's "
     "capacitor, because sensing a DRAM cell destroys its stored charge."),
    ("PRECHARGE adds tRP: together they make tRC",
     "After tRAS, PRECHARGE closes the row and equalizes the bitlines for tRP. tRC = tRAS + tRP, about 45 to 50 ns on "
     "DDR5 and HBM. No new ACTIVATE can hit this bank before tRC is up."),
    ("Next ACTIVATE: tRC caps random row rate per bank",
     "At ~48 ns, one bank opens at most about 20 million rows per second. Memory gets random throughput by spreading "
     "requests across many banks and bank groups so their tRC windows overlap. "
     "Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS), Rambus (RMBS)."),
]


def build():
    n = len(BEATS)
    m, root, b, bk = stage(SLUG, n)
    pts, pk = bk["pts"], b["pk"]
    end = F(n, 0)
    cmd(m, bk, "tl_act", tx(0.03), 1, 0.05, n)
    K.row_open(bk, 2, [(F(1, 0.1), F(3, 0.3))])
    K.charge_share(m, bk, 2, 1, 0.1, 0.6)
    K.bl_show(bk, "hi", [(F(1, 0.5), F(3, 0.25))])
    fill(m, bk["g"], "tl_ras", tx(0.05), tx(0.62), 0.6, TZ, 1, 0.3, 1.0, n - 1, n=6, mt="dram_rb_on")
    fill(m, bk["g"], "tl_ras2", tx(0.05), tx(0.62), 0.6, TZ, 2, 0.0, 0.95, n - 1, n=6, mt="dram_rb_on")
    K.io_flow(m, bk, [3, 5, 7], 2, 0.05, 0.6)
    K.write_back(m, bk, 2, 2, 0.3, 0.95)
    cmd(m, bk, "tl_pre", tx(0.64), 3, 0.05, n)
    K.write_back(m, bk, 2, 3, 0.05, 0.3)
    K.bl_show(bk, "eq", [(F(3, 0.3), F(4, 0.2))])
    fill(m, bk["g"], "tl_rp", tx(0.65), tx(0.95), 0.6, TZ, 3, 0.1, 0.9, n - 1, n=5)
    cmd(m, bk, "tl_act2", tx(0.97), 4, 0.05, n)
    K.row_open(bk, 6, [(F(4, 0.15), end)])
    K.charge_share(m, bk, 6, 4, 0.15, 0.7)
    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]), ("one bank on the bench", pts["top"])],
        1: [("ACT: wordline 2 rises", pts["wl"](2)), ("tRAS bar starts", (tx(0.3), 1.5, TZ))],
        2: [("READ from row buffer", pts["io"]), ("cells restored", pts["wl"](2)), ("tRAS: min open time", (tx(0.3), 1.5, TZ))],
        3: [("PRE: bitlines to half", pts["bl"](6)), ("tRP bar", (tx(0.8), 1.5, TZ)), ("tRC = tRAS + tRP", (tx(0.5), 4.0, TZ))],
        4: [("next ACT after tRC", (tx(0.97), 4.0, TZ)), ("~48 ns: 20M rows/s/bank", pts["wl"](6))],
    })
    C.done(SLUG, BEATS, plan(n), root)


if __name__ == "__main__":
    build()
