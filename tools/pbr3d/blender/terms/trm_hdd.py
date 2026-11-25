"""TRM_HDD: a hard drive with its cover cut away: a stack of spinning platters on a spindle, an
actuator arm swinging its heads across them, and on the bench a close-up of a head flying over
magnetic bits.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_hdd.py
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, P, show  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink  # noqa: E402
from sand_overview import empty, tube  # noqa: E402
import sand_overview as O  # noqa: E402

SLUG = "TRM_HDD"
BEATS = [
    ("An HDD stores bits magnetically on spinning platters",
     "Open the sealed case and there are 8 to 10 glass or aluminium platters on one spindle, an arm with a head for "
     "every surface, and a controller board underneath. Data-center drives are filled with helium to cut drag."),
    ("Platters spin at 7,200 rpm under flying heads",
     "The stack turns 120 times a second. Each head rides on an air (helium) cushion a few nanometres above the "
     "surface, reading concentric tracks of bits as they pass beneath."),
    ("The actuator arm seeks: milliseconds, not microseconds",
     "A voice-coil motor swings all heads together to the right track, then the drive waits for the sector to come "
     "round. Seek plus rotation costs 5 to 10 ms, about 50 times slower than an SSD read."),
    ("Close up: the head flips tiny magnetic grains",
     "The write pole's field sets the magnetization of each bit, up or down, and a magnetoresistive sensor reads "
     "it back. HAMR and similar tricks heat the spot with a laser to pack bits tighter: 30+ TB per drive."),
    ("Cheapest storage per TB, so it holds the bulk",
     "An HDD costs several times less per terabyte than an SSD, so most cloud data still lives on disks. AI piles "
     "up training sets, logs and generated media in these capacity tiers. "
     "Related: Seagate (STX), Western Digital (WDC), Toshiba (6502.T)."),
]

SC = (-70.0, 0.0, -110.0)   # spindle centre
R = 82.0
PIV = (70.0, 0.0, -200.0)   # actuator pivot
PLY = [8.0, 18.0, 28.0]
BX0, BX1 = 152.0, 246.0
BCX = (BX0 + BX1) / 2


def case(m, root):
    g = empty("case", root)
    bx("base", (-170.0, -6.0, -225.0), (110.0, 0.0, 0.0), m["alu"], g)
    for name, lo, hi in (("wl", (-170.0, 0.0, -225.0), (-162.0, 40.0, 0.0)),
                         ("wb", (-170.0, 0.0, -225.0), (110.0, 40.0, -217.0)),
                         ("wr", (102.0, 0.0, -225.0), (110.0, 40.0, 0.0))):
        bx("case_" + name, lo, hi, m["alu"], g)
    bx("cover", (-170.0, 40.0, -225.0), (110.0, 41.0, -150.0), m["steel"], g)
    bx("pcb", (-160.0, -9.0, -215.0), (100.0, -6.0, -10.0), m["mask"], g)
    C.chip(m, g, "soc", (20.0, -9.0, -60.0), 20.0, 20.0, h=-1.5, pins=0, body="dark")
    return g


def platters(m, root):
    outer = empty("spin_o", root, P(*SC))
    for k, y in enumerate(PLY):
        tube(f"pl{k}", (0.0, y, 0.0), (0.0, y + 1.6, 0.0), R, m["alu"], outer, 64)
        # tracks of bits on top so the spin reads
        for j in range(36):
            a = 2 * math.pi * j / 36
            r = 40.0 + 10.0 * (j % 4)
            x, z = r * math.cos(a), r * math.sin(a)
            bx(f"bit{k}_{j}", (x - 1.5, y + 1.6, z - 1.5), (x + 1.5, y + 1.75, z + 1.5),
               m["pplus" if j % 2 else "nplus"], outer)
    tube("spindle", (0.0, 0.0, 0.0), (0.0, 34.0, 0.0), 12.0, m["steel"], outer, 32)
    C.spin(outer, [1, 2, 3, 4], turns=3.0)
    return outer


def arm(m, root):
    g = empty("arm", root, P(*PIV))
    tube("pivot", (0.0, 0.0, 0.0), (0.0, 34.0, 0.0), 9.0, m["steel"], g, 24)
    bx("vcm", (8.0, 2.0, -18.0), (40.0, 30.0, 18.0), m["ferrite"], g)
    tip = (-115.0, 0.0, 85.0)
    heads = []
    for k, y in enumerate(PLY):
        for dy in (-1.4, 3.0):
            yy = y + dy
            tube(f"arm{k}{dy}", (0.0, yy, 0.0), (tip[0], yy, tip[2]), 1.4, m["steel"], g, 8)
            bx(f"sl{k}{dy}", (tip[0] - 3.0, yy - 0.6, tip[2] - 2.0), (tip[0] + 3.0, yy + 0.6, tip[2] + 2.0), m["ceramic"], g)
    O._interp("BEZIER")
    for b, angs in ((2, (0.0, 0.25, -0.15, 0.3, 0.0)),):
        for j, a in enumerate(angs):
            g.rotation_euler = (0.0, 0.0, a)
            g.keyframe_insert("rotation_euler", frame=F(b, j / (len(angs) - 1) * 0.95))
    head = (PIV[0] + tip[0], PLY[2] + 3.0, PIV[2] + tip[2])
    return head


def bench(m, root):
    g = empty("closeup", root)
    bx("glass", (BX0, 0.0, -30.0), (BX1, 6.0, 0.0), m["quartz_c"], g)
    bx("soft", (BX0, 6.0, -30.0), (BX1, 7.0, 0.0), m["moly"], g)
    for i in range(16):
        x = BX0 + i * (BX1 - BX0) / 16
        bx(f"mb{i}", (x + 0.3, 7.0, -30.0), (x + (BX1 - BX0) / 16 - 0.3, 9.0, 0.0),
           m["pplus" if (i * 7 % 3) else "nplus"], g)
    bx("coat", (BX0, 9.0, -30.0), (BX1, 9.4, 0.0), m["car"], g)
    sl = (BCX - 16.0, 14.0, -24.0), (BCX + 16.0, 26.0, -2.0)
    bx("slider", *sl, m["ceramic"], g)
    bx("pole", (BCX + 6.0, 11.5, -16.0), (BCX + 9.0, 14.0, -6.0), m["nickel"], g)
    bx("reader", (BCX - 6.0, 11.5, -14.0), (BCX - 5.0, 14.0, -8.0), m["gold"], g)
    field = empty("field", root)
    bx("fld", (BCX + 5.0, 9.4, -15.0), (BCX + 10.0, 11.5, -7.0), m["rf"], field)
    show(field, [])
    blink(field, 3, [0, 2, 4, 6], n=8, on=0.5)
    return {"pole": (BCX + 7.5, 12.0, -6.0), "reader": (BCX - 5.5, 12.0, -8.0), "bits": (BX0 + 15.0, 9.0, -4.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    case(m, root)
    platters(m, root)
    head = arm(m, root)
    b = bench(m, root)
    C.magnify(m, root, head, (BX0 - 2.0, 16.0, -14.0), r=3.0)
    # bits stream under the head on the bench (beats 1 and 3)
    run(root, "track", [(BX1 - 2.0, 10.0, -11.0), (BX0 + 2.0, 10.0, -11.0)], 6, 0.8, m["bit"], [1, 3], 0.0, 0.9, 30)
    run(root, "read", [b["reader"], (BCX - 5.5, 30.0, -11.0)], 4, 0.7, m["sig"], 3, 0.1, 0.9, 20)
    rise(root, "motor", (SC[0], 34.0, SC[2]), 4, 0.8, m["h_amber"], [1], 0.0, 0.8, 16.0, 45, (6.0, 6.0))

    pl = (SC[0], PLY[2] + 1.8, SC[2] + 60.0)
    C.tags(root, {
        0: [("platter stack on one spindle", pl), ("actuator arm + heads", (PIV[0] - 40.0, 34.0, PIV[2] + 30.0)),
            ("controller board below", (40.0, -8.0, -12.0)), ("sealed, helium-filled case", (100.0, 40.0, -180.0))],
        1: [("7,200 rpm: 120 turns/s", (SC[0], 34.0, SC[2])), ("bits on concentric tracks", pl),
            ("head flies nm above", head)],
        2: [("voice-coil swings the arm", (PIV[0] + 24.0, 30.0, PIV[2])), ("seek + spin wait: 5-10 ms", head),
            ("~50x slower than an SSD", pl)],
        3: [("write pole flips the grains", b["pole"]), ("MR sensor reads them back", b["reader"]),
            ("magnetic bits, up or down", b["bits"]), ("HAMR: laser heat, 30+ TB", (BCX, 26.0, -12.0))],
        4: [("several x cheaper per TB", pl), ("bulk cloud and AI data", (SC[0], 34.0, SC[2])),
            ("STX, WDC, 6502.T", (PIV[0], 34.0, PIV[2]))],
    })
    C.done(SLUG, BEATS, [
        frame((-10.0, 10.0, -110.0), 300.0, 0.25, 0.60, pad=1.0),
        frame((SC[0], 20.0, SC[2]), 200.0, 0.20, 0.55),
        frame((0.0, 20.0, -130.0), 240.0, 0.35, 0.70),
        frame((BCX, 14.0, -14.0), 110.0, 0.25, 0.22),
        frame((20.0, 10.0, -110.0), 420.0, 0.20, 0.50, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
