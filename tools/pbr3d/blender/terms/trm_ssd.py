"""TRM_SSD: an NVMe SSD stick laid out big: gold fingers, controller, DRAM cache and four NAND
packages, with a NAND package cut open on the bench to show its stacked dies and 3D NAND layers.
Commands flow in over PCIe, fan out over flash channels, and data comes back.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_ssd.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, wire, arc  # noqa: E402
from sand_overview import empty  # noqa: E402

SLUG = "TRM_SSD"
BEATS = [
    ("An SSD is NAND flash plus a controller on one board",
     "An SSD has no moving parts. A controller chip, a small DRAM cache and several NAND flash packages share one "
     "board, and gold fingers plug it into the server. A 30 TB data-center drive is mostly NAND packages."),
    ("The host talks NVMe over four PCIe lanes",
     "Reads and writes arrive as NVMe commands over PCIe, typically four lanes at Gen5 for about 14 GB/s. NVMe "
     "keeps thousands of command queues open at once, so many GPUs and threads can hit one drive in parallel."),
    ("The controller fans each command out over flash channels",
     "The controller splits work across 8 to 16 independent channels, each wired to several NAND dies. Spreading "
     "one large read over all of them is where the bandwidth comes from; one die alone manages only a few hundred MB/s."),
    ("Inside a package: stacked dies of 3D NAND",
     "Each package stacks 8 to 16 thin dies, bonded by wires to the substrate. Each die is a 3D NAND array: "
     "200+ word-line layers pierced by vertical channel holes, every crossing one cell holding 3 or 4 bits."),
    ("Random reads in ~100 us, so SSDs feed the GPUs",
     "A random read takes about 100 microseconds, against several milliseconds for a hard disk. GPU servers carry "
     "local SSDs as scratch and checkpoint space, and flash arrays feed training data. "
     "Related: Samsung (005930.KS), SK hynix (000660.KS), MU, SNDK, PSTG."),
]

BX0, BX1 = 152.0, 246.0
BCX, BCZ = (BX0 + BX1) / 2, -18.0
NAND_X = [-60.0, -5.0, 50.0, 105.0]
CTRL = (-170.0, 0.0, -45.0)
DRAM = (-112.0, 0.0, -68.0)


def drive(m, root):
    """The SSD stick: board, gold fingers, controller, DRAM, PMIC, four NAND packages, traces."""
    pcb = C.pcb(m, root, "ssd_pcb", -240.0, 132.0, -92.0, 0.0)
    fing = empty("ssd_fingers", root)
    for k in range(12):
        z = -86.0 + k * 7.2
        bx(f"ssd_f{k}", (-252.0, -1.0, z), (-238.0, -0.6, z + 5.0), m["gold"], fing)
    bx("ssd_tab", (-252.0, -1.6, -90.0), (-240.0, -1.0, -2.0), m["fr4"], fing)
    ctrl = C.chip(m, root, "ssd_ctrl", CTRL, 40.0, 40.0, h=2.4, pins=0, body="dark")
    bx("ssd_ctrl_lid", (CTRL[0] - 14.0, 2.4, CTRL[2] - 14.0), (CTRL[0] + 14.0, 3.0, CTRL[2] + 14.0), m["alu"], root)
    dram = C.chip(m, root, "ssd_dram", DRAM, 22.0, 30.0, h=1.6, pins=0, body="mold")
    C.chip(m, root, "ssd_pmic", (-215.0, 0.0, -20.0), 12.0, 12.0, h=1.2, pins=4, body="mold")
    for k in range(6):
        C.chip(m, root, f"ssd_cap{k}", (-226.0 + 6.0 * k, 0.0, -78.0), 3.0, 1.8, h=1.4, pins=0, body="mlcc")
    tops = []
    for k, x in enumerate(NAND_X):
        tops.append(C.chip(m, root, f"ssd_nand{k}", (x, 0.0, -48.0), 44.0, 60.0, h=2.0, pins=0, body="mold"))
        bx(f"ssd_nlogo{k}", (x - 12.0, 2.0, -40.0), (x + 12.0, 2.05, -36.0), m["ink"], root)
    # PCIe lanes: connector to controller
    lanes = []
    for k in range(4):
        z = -62.0 + 9.0 * k
        pts = [(-238.0, 0.0, z), (-205.0, 0.0, z), (-192.0, 0.0, CTRL[2] - 12.0 + 8.0 * k)]
        C.trace(m, pcb, f"ssd_lane{k}", pts, w=1.0)
        lanes.append([(p[0], 3.5, p[2]) for p in pts] + [(CTRL[0], 3.5, CTRL[2])])
    # flash channels: controller to each NAND package
    chans = []
    for k, x in enumerate(NAND_X):
        z = -14.0 + 2.5 * k
        pts = [(CTRL[0] + 20.0, 0.0, CTRL[2] + 8.0 + 2.0 * k), (-140.0, 0.0, z), (x, 0.0, z), (x, 0.0, -18.0)]
        C.trace(m, pcb, f"ssd_ch{k}", pts, w=1.2)
        chans.append([(CTRL[0], 3.5, CTRL[2])] + [(p[0], 3.5, p[2]) for p in pts] + [(x, 3.5, -48.0)])
    C.trace(m, pcb, "ssd_dq", [(CTRL[0] + 20.0, 0.0, -60.0), (DRAM[0], 0.0, -60.0)], w=1.4)
    return {"ctrl": ctrl, "dram": dram, "nand": tops, "lanes": lanes, "chans": chans}


def stack(m, root, x0, x1, z0, y0, layers, pitch):
    """3D NAND block cut open at z = 0: alternating word-line / oxide plates with three
    channel holes sliced in half so the cell strings show."""
    g = empty("nand3d", root)
    for k in range(layers):
        y = y0 + k * pitch
        bx(f"n3_ox{k}", (x0, y, z0), (x1, y + pitch * 0.45, 0.0), m["nand_ox"], g)
        bx(f"n3_wl{k}", (x0, y + pitch * 0.45, z0), (x1, y + pitch, 0.0), m["nand_cg"], g)
    top = y0 + layers * pitch
    holes = []
    for j, xc in enumerate((x0 + 8.0, (x0 + x1) / 2, x1 - 8.0)):
        C.D.tube(f"n3_h{j}", (xc, y0 - 1.0, -1.6), (xc, top + 3.0, -1.6), 2.2, m["nand_chan"], g, 12)
        holes.append(xc)
    xc = holes[1]
    return {"grp": g, "top": (xc, top + 3.0, -1.6), "hole": [(xc, y0 + k * pitch, -1.6) for k in range(layers)]}


def bench(m, root):
    """A NAND package sawn open: substrate, balls, 8 staggered dies with bond wires, mold behind,
    and a 3D NAND block lifted above the top die."""
    z0 = -36.0
    g = empty("pkg_open", root)
    for i in range(10):
        C.D.tube(f"ball{i}", (BX0 + 6.0 + 9.4 * i, -2.0, -6.0), (BX0 + 6.0 + 9.4 * i, 0.0, -6.0), 1.6, m["solder"], g, 10)
    bx("sub", (BX0, 0.0, z0), (BX1, 3.0, 0.0), m["substrate"], g)
    bx("sub_cu", (BX0, 3.0, z0), (BX1, 3.3, 0.0), m["copper"], g)
    bx("mold_back", (BX0, 3.3, z0), (BX1, 26.0, z0 + 6.0), m["mold"], g)
    dies = empty("dies", g)
    pads = []
    for k in range(8):
        y = 3.3 + k * 2.6
        xs = BX0 + 12.0 + k * 3.0
        bx(f"daf{k}", (xs, y, z0 + 6.0), (BX1 - 6.0, y + 0.5, -4.0), m["plastic"], dies)
        bx(f"die{k}", (xs, y + 0.5, z0 + 6.0), (BX1 - 6.0, y + 2.2, -4.0), m["silicon"], dies)
        bx(f"cell{k}", (xs + 4.0, y + 2.2, -16.0), (BX1 - 10.0, y + 2.3, -4.2), m["nand_cg"], dies)
        pads.append((xs + 1.0, y + 2.2, -10.0))
        wire(f"bw{k}", arc((xs + 1.0, y + 2.2, -10.0), (BX0 + 4.0 + 0.8 * k, 3.3, -10.0), 3.0 + 0.6 * k, 8),
             0.22, m["gold"], g)
    stk = stack(m, root, BX0 + 30.0, BX1 - 24.0, -26.0, 36.0, 10, 3.2)
    C.magnify(m, root, (BCX + 18.0, 24.0, -10.0), (BCX + 3.0, 40.0, -16.0), r=2.0, name="mag3d")
    return {"pads": pads, "stk": stk, "top": (BCX + 10.0, 24.0, -10.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    d = drive(m, root)
    b = bench(m, root)
    C.magnify(m, root, d["nand"][3], (BX0 - 2.0, 14.0, BCZ))

    # beat 1: commands stream in over the PCIe lanes; beat 4 again (reads)
    for k, pts in enumerate(d["lanes"]):
        run(root, f"cmd{k}", pts, 4, 1.4, m["sig"], [1, 4], 0.05 + 0.03 * k, 0.75, 40)
    # beat 2: controller fans out over the channels; beat 4 data back
    for k, pts in enumerate(d["chans"]):
        run(root, f"chan{k}", pts, 4, 1.4, m["e_blue"], 2, 0.05 + 0.04 * k, 0.75, 50)
        run(root, f"back{k}", list(reversed(pts)), 3, 1.2, m["bit"], 4, 0.1 + 0.04 * k, 0.7, 50)
    # NAND busy lights on each package top, staggered, during beat 2
    for k, t in enumerate(d["nand"]):
        led = empty(f"busy{k}", root)
        bx(f"busy{k}_b", (t[0] + 14.0, t[1], -26.0), (t[0] + 18.0, t[1] + 0.4, -22.0), m["sig"], led)
        show(led, [])
        blink(led, 2, [k, k + 4], n=8, on=0.6)
    # controller works hard: heat over it in beats 2 and 4
    rise(root, "ctrl_heat", (CTRL[0], 3.2, CTRL[2]), 6, 0.9, m["h_amber"], [2], 0.0, 0.85, 22.0, 45, (12.0, 12.0))
    # beat 3: a read runs down the channel hole and out to the die pads
    hole = b["stk"]["hole"]
    run(root, "hole_e", [b["stk"]["top"]] + list(reversed(hole)), 4, 0.9, m["nand_e"], 3, 0.1, 0.7, 36)
    run(root, "wire_e", [b["pads"][7], (BX0 + 10.0, 22.0, -10.0), (BX0 + 4.0, 3.3, -10.0)], 3, 0.8, m["sig"], 3, 0.2, 0.8, 30)

    C.tags(root, {
        0: [("controller: the drive's brain", (CTRL[0], 3.0, CTRL[2])), ("DRAM cache", (DRAM[0], 1.6, DRAM[2])),
            ("NAND flash packages", d["nand"][1]), ("gold fingers into the server", (-246.0, 0.0, -45.0))],
        1: [("NVMe commands over PCIe x4", (-215.0, 3.0, -50.0)), ("Gen5 x4: about 14 GB/s", (-200.0, 3.0, -30.0)),
            ("thousands of queues at once", (CTRL[0], 3.0, CTRL[2]))],
        2: [("one channel per package here", (-60.0, 3.0, -14.0)), ("all dies work in parallel", d["nand"][2]),
            ("controller schedules the work", (CTRL[0], 3.0, CTRL[2]))],
        3: [("8 dies stacked, wire-bonded", (BX0 + 30.0, 14.0, -6.0)), ("200+ word-line layers", b["stk"]["top"]),
            ("channel hole = a cell string", (BCX - 8.0, 50.0, -16.0)), ("substrate and solder balls", (BCX, 1.0, -6.0))],
        4: [("random read ~100 us", (CTRL[0], 3.0, CTRL[2])), ("HDD seek: several ms", (-60.0, 3.0, -48.0)),
            ("005930.KS, 000660.KS, MU", d["nand"][2]), ("SNDK, PSTG", d["nand"][3])],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 10.0, -46.0), 330.0, 0.20, 0.45, pad=1.0),
        frame((-205.0, 0.0, -45.0), 110.0, 0.30, 0.55),
        frame((-80.0, 0.0, -40.0), 260.0, 0.15, 0.60),
        frame((BCX, 22.0, BCZ), 120.0, 0.30, 0.22),
        frame((-10.0, 15.0, -40.0), 360.0, 0.25, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
