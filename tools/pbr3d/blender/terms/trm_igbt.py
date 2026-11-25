"""TRM_IGBT on the MLCC base board. The board itself has no IGBTs: they sit upstream, in the UPS,
chiller and fan drives. The bench shows an IGBT cell cut open, then a module, then turn-off.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_igbt.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, rise  # noqa: E402

SLUG = "TRM_IGBT"
BEATS = [
    ("IGBTs live upstream of the GPU board, where volts are high",
     "The GPU board runs on 12 V and below, switched by MOSFETs. IGBTs (insulated gate bipolar transistors) work further "
     "up the chain: in UPS inverters, chiller and pump motor drives, wind and solar inverters, trains and older EV "
     "drives, switching hundreds to thousands of volts."),
    ("A MOSFET on top, a bipolar transistor underneath",
     "The top looks like a power MOSFET: emitter metal, trench gates in oxide, n+ source and p-body. The difference is at "
     "the bottom: a p+ collector layer under a thick n- drift region. That extra layer turns the device into a MOSFET "
     "driving a bipolar transistor."),
    ("Gate on: electrons go down, holes come up, the drift floods",
     "With the gate on, electrons flow down the channel as in a MOSFET. They reach the p+ collector, which injects holes "
     "back up into the drift region. Flooded with both carriers, the thick drift conducts far better than it could alone "
     "(conductivity modulation), so one chip carries large currents at high voltage."),
    ("A module: many chips on ceramic, wired in parallel",
     "Real IGBTs ship as modules: several chips and their diodes soldered onto a ceramic DBC substrate, joined by rows of "
     "aluminium bond wires, on a copper baseplate that bolts to a heatsink, with big screw terminals on top."),
    ("Turn-off is slow: holes linger, a tail current wastes energy",
     "Switch the gate off and the stored holes must drain away before current stops, leaving a tail that wastes energy "
     "each cycle. That caps IGBTs at ~tens of kHz, and is why SiC MOSFETs take the high end. IGBTs stay cheaper per amp "
     "for much industrial work. Makers: Infineon (IFNNY), Mitsubishi Electric, onsemi (ON), STMicro (STM), Fuji Electric."),
]

X0, X1, Z0 = 152.0, 246.0, -40.0
Y_COL = (0.6, 4.0)
Y_PP = (4.0, 9.0)
Y_FS = (9.0, 12.0)
Y_DRIFT = (12.0, 34.0)
Y_BODY = (34.0, 40.0)
Y_SRC = (40.0, 43.0)
Y_MET = (44.5, 50.0)


def cell(m, root):
    g = empty("igbt", root)
    C.xsec(m, g, "ig", X0, X1, Z0, [(*Y_COL, "alum"), (*Y_PP, "pplus"), (*Y_FS, "nplus"), (*Y_DRIFT, "ndrift"),
                                     (*Y_BODY, "pbody"), (*Y_SRC, "nplus")])
    bx("ig_met", (X0, Y_MET[0], Z0), (X1, Y_MET[1], 0.0), m["alum"], g)
    n = 4
    pitch = (X1 - X0) / n
    chan = empty("ig_chan", root)
    down, up = [], []
    for k in range(n):
        xc = X0 + pitch * (k + 0.5)
        bx(f"igt{k}_ox", (xc - 3.0, 30.0, Z0), (xc + 3.0, Y_SRC[1], 0.02), m["oxide"], g)
        bx(f"igt{k}_p", (xc - 2.2, 31.0, Z0), (xc + 2.2, Y_SRC[1] - 0.3, 0.05), m["poly"], g)
        bx(f"igt{k}_c", (xc - 3.6, Y_SRC[1], Z0), (xc + 3.6, Y_MET[0], 0.05), m["oxide"], g)
        if k < n - 1:
            cx = xc + pitch / 2
            bx(f"igc{k}", (cx - 2.0, Y_BODY[1] - 2.0, Z0), (cx + 2.0, Y_MET[0], 0.05), m["alum"], g)
        for s in (-1, 1):
            xe = xc + s * 3.35
            bx(f"igch{k}{s}", (xe - 0.35, Y_BODY[0], Z0), (xe + 0.35, Y_BODY[1], 0.12), m["chan"], chan)
            down.append([(xe, Y_MET[0] - 0.5, 1.0), (xe, Y_BODY[0], 1.0), (xe + s * 4.0, 20.0, 1.0), (xe + s * 5.0, Y_FS[0], 1.0)])
            up.append([(xe + s * 8.0, Y_PP[1], 1.2), (xe + s * 7.0, 22.0, 1.2), (xe + s * 9.0, Y_BODY[0] + 1.0, 1.2), (xe + s * 10.0, Y_BODY[1], 1.2)])
    flood = empty("ig_flood", root)
    bx("ig_flood_b", (X0 + 0.5, Y_DRIFT[0] + 0.5, Z0 + 0.5), (X1 - 0.5, Y_DRIFT[1] - 0.5, 0.08), m["flood"], flood)
    show(chan, [])
    show(flood, [])
    pts = {"met": ((X0 + X1) / 2, Y_MET[1], -20.0), "gate": (X0 + pitch / 2, 36.0, 0.0), "drift": (X0 + 12.0, 22.0, 0.0),
           "pp": (X1 - 14.0, 6.0, 0.0), "fs": (X0 + 50.0, 10.5, 0.0), "body": (X1 - 30.0, 37.0, 0.0)}
    return pts, chan, flood, down, up


def module(m, root):
    """An IGBT module behind the cell: copper baseplate, DBC ceramic, chips, bond wires, terminals."""
    g = empty("mod", root)
    x0, x1, z0, z1 = 158.0, 240.0, -190.0, -70.0
    bx("mod_base", (x0, 0.6, z0), (x1, 6.0, z1), m["copper"], g)
    for i, (a, b) in enumerate(((x0 + 4.0, (x0 + x1) / 2 - 2.0), ((x0 + x1) / 2 + 2.0, x1 - 4.0))):
        bx(f"dbc_cu_b{i}", (a, 6.0, z0 + 6.0), (b, 7.0, z1 - 6.0), m["copper"], g)
        bx(f"dbc_cer{i}", (a, 7.0, z0 + 6.0), (b, 9.5, z1 - 6.0), m["aln"], g)
        bx(f"dbc_cu_t{i}", (a + 2.0, 9.5, z0 + 10.0), (b - 2.0, 10.5, z1 - 10.0), m["copper"], g)
        for j in range(3):
            zc = z0 + 25.0 + 35.0 * j
            cx = a + 12.0
            bx(f"chip{i}{j}", (cx - 7.0, 10.5, zc - 7.0), (cx + 7.0, 11.5, zc + 7.0), m["si"], g)
            bx(f"diode{i}{j}", (cx + 12.0, 10.5, zc - 5.0), (cx + 20.0, 11.5, zc + 5.0), m["si"], g)
            for w in range(5):
                z = zc - 5.0 + 2.5 * w
                D.wire(f"bw{i}{j}{w}", D.arc((cx - 3.0, 11.5, z), (cx + 26.0, 10.5, z), 6.0, 8), 0.35, m["alum"], g, 6)
    for i, x in enumerate((x0 + 14.0, (x0 + x1) / 2, x1 - 14.0)):
        bx(f"term{i}", (x - 5.0, 10.5, z1 - 14.0), (x + 5.0, 40.0, z1 - 4.0), m["copper"], g)
        bx(f"nut{i}", (x - 4.0, 40.0, z1 - 13.0), (x + 4.0, 42.0, z1 - 5.0), m["steel"], g)
    return {"mod": ((x0 + x1) / 2, 12.0, (z0 + z1) / 2), "dbc": (x0 + 6.0, 8.5, z1 - 6.0), "term": (x0 + 14.0, 41.0, z1 - 9.0),
            "base": (x1, 3.0, z1 - 20.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m["flood"] = C.mat("t_flood", (0.50, 0.45, 0.85), emit=(0.55, 0.45, 1.0), strength=0.5)
    b = C.base(m, root)
    pts, chan, flood, down, up = cell(m, root)
    mp = module(m, root)

    show(chan, [(F(2, 0.1), F(3, 0)), (F(4, 0), F(4, 0.3))])
    show(flood, [(F(2, 0.35), F(3, 0)), (F(4, 0), F(4, 0.75))])
    for k, p in enumerate(down):
        run(root, f"e{k}", p, 3, 0.8, m["e_blue"], 2, 0.05 + 0.02 * (k % 3), 0.85, 40)
        run(root, f"e4{k}", p, 2, 0.8, m["e_blue"], 4, 0.0, 0.2, 40)
    for k, p in enumerate(up):
        run(root, f"h{k}", p, 3, 0.8, m["h_amber"], 2, 0.25 + 0.02 * (k % 3), 0.9, 45)
        run(root, f"t{k}", p, 3, 0.8, m["h_amber"], 4, 0.25, 0.75, 110)  # tail: slow, after the gate is off
    rise(root, "tailheat", ((X0 + X1) / 2, Y_MET[1] + 1.0, -20.0), 6, 1.1, m["heat"], 4, 0.3, 0.9, 30.0, 60, (40.0, 12.0))

    C.tags(root, {
        0: [("GPU board: 12 V and below", b["pk"]["top"]), ("IGBT: UPS, chillers, drives", pts["met"]),
            ("hundreds to 1000s of volts", (X1, 25.0, 0.0))],
        1: [("emitter metal", pts["met"]), ("trench gate", pts["gate"]), ("thick n- drift", pts["drift"]),
            ("p+ collector: the extra layer", pts["pp"]), ("n field stop", pts["fs"])],
        2: [("electrons down the channel", pts["gate"]), ("holes injected up", pts["pp"]), ("drift floods: low loss on", pts["drift"])],
        3: [("module: chips on DBC ceramic", mp["dbc"]), ("rows of Al bond wires", mp["mod"]), ("screw terminals", mp["term"]),
            ("copper baseplate to heatsink", mp["base"])],
        4: [("gate off: holes linger", pts["drift"]), ("tail current = lost energy", pts["met"]), ("IFNNY, ON, STM, Mitsubishi", pts["pp"])],
    })
    cb = ((X0 + X1) / 2, 25.0, -12.0)
    C.done(SLUG, BEATS, [
        frame((90.0, 10.0, -90.0), 380.0, 0.35, 0.55, pad=1.0),
        frame(cb, 115.0, 0.25, 0.20),
        frame(cb, 95.0, 0.08, 0.08),
        frame(mp["mod"], 120.0, 0.45, 0.70),
        frame(cb, 100.0, 0.15, 0.12),
    ], root)


if __name__ == "__main__":
    build()
