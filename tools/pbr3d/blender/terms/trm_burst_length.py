"""TRM_BURST_LENGTH: the Terms-tab overview for DRAM burst length, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_burst_length.py

One bank is cut open on the bench with a row open. A single READ sends a train of data beats out
of the row buffer to the I/O edge and along the bus to the GPU; timeline blocks count the beats
(BL8 then BL16), each set filling one 64-byte cache line.

Beats:
  0 hbm    HBM stacks beside the GPU package
  1 read   one READ command on an open row
  2 bl8    eight transfers on a 64-bit channel = 64 bytes
  3 bl16   DDR5: sixteen transfers on a 32-bit subchannel = 64 bytes
  4 why    streaming vs random access, set by the standard
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from power_vrm_detail import frame, present, run  # noqa: E402

SLUG = "TRM_BURST_LENGTH"
BEATS = [
    ("HBM and DDR deliver data in bursts, not single words",
     "The GPU or CPU never asks DRAM for one byte. Each READ or WRITE command moves a fixed run of back-to-back "
     "transfers on the data pins, called a burst."),
    ("One READ on an open row starts the burst",
     "After ACTIVATE the row buffer holds the whole row. A READ picks a starting column, and the chip then streams "
     "consecutive data out of the row buffer without needing another command."),
    ("Burst length 8: eight transfers fill a 64-byte line",
     "DDR4 uses a burst of 8 on a 64-bit channel: 8 transfers x 8 bytes = 64 bytes, exactly one CPU cache line. "
     "Data moves on both clock edges, so the burst takes four clock cycles."),
    ("DDR5 doubles it to 16 on a narrower subchannel",
     "DDR5 splits each module into two 32-bit subchannels and uses a burst of 16: 16 x 4 bytes is still 64 bytes. "
     "Two independent subchannels keep more requests in flight, which raises usable bandwidth."),
    ("Long bursts suit streaming, short ones suit random reads",
     "Model weights stream in long sequential runs, so long bursts keep the pins busy and the command bus quiet. "
     "Small random reads waste part of each burst. Burst length is set by the memory standard and controller, not "
     "by the buyer. Related: Micron (MU), Samsung (005930.KS), SK hynix (000660.KS)."),
]

BX0, BX1, BZ0, BZ1 = 160.0, 236.0, -72.0, -24.0
TZ = -14.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=8, cols=12)
    pts = bk["pts"]
    present(bk["g"], [(F(1, 0), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), pts["top"])
    K.row_open(bk, 4, [(F(1, 0), F(5, 0))])
    K.bl_show(bk, "hi", [(F(1, 0), F(5, 0))])

    io = pts["io"]
    bus = [io, (io[0] - 20.0, 2.0, io[2]), (pk["hbm"][0] + 10.0, 2.0, pk["hbm"][2])]
    K.io_flow(m, bk, [2, 3, 4, 5], 1, 0.2, 0.8)
    run(root, "b8", bus, 8, 1.4, m["dram_bead"], 2, 0.1, 0.5, 40)
    run(root, "b16", bus, 16, 1.0, m["dram_bead_w"], 3, 0.1, 0.6, 40)
    run(root, "bs", bus, 16, 1.0, m["dram_bead"], 4, 0.0, 0.7, 40)

    strip = K.cmd_strip(m, root, "cmd", BX0, BX1, TZ)
    present(strip, [(F(1, 0), F(5, 0))])
    rd = K.tick(m, root, "t_rd", BX0 + 4.0, TZ)
    present(rd, [(F(1, 0.2), F(5, 0))])
    K.fill(m, root, "bl8", BX0 + 6.0, BX0 + 46.0, 0.8, TZ, 2, 0.1, 0.6, 2, n=8, mt="dram_rb_on")
    K.fill(m, root, "bl16", BX0 + 6.0, BX0 + 70.0, 0.8, TZ, 3, 0.1, 0.7, 4, n=16, mt="dram_sa_on")

    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]), ("one bank, cut open ->", (130.0, 4.0, -50.0))],
        1: [("READ command", (BX0 + 4.0, 4.0, TZ)), ("open row in the row buffer", pts["rb"](6)), ("data to the I/O edge", io)],
        2: [("BL8: 8 transfers", (BX0 + 26.0, 2.0, TZ)), ("8 x 8 bytes = 64 B line", io)],
        3: [("DDR5 BL16 on 32-bit subchannel", (BX0 + 40.0, 2.0, TZ)), ("16 x 4 bytes = 64 B", io)],
        4: [("streams keep pins busy", bus[1]), ("set by the standard", (BX0 + 40.0, 2.0, TZ))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame(((BX0 + BX1) / 2, 6.0, -42.0), 125.0, 0.25, 0.50),
        frame(((BX0 + BX1) / 2, 4.0, -30.0), 110.0, 0.20, 0.60),
        frame(((BX0 + BX1) / 2, 4.0, -30.0), 115.0, 0.30, 0.60),
        frame((90.0, 0.0, -50.0), 260.0, 0.28, 0.55, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
