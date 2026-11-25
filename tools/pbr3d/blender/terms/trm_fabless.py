"""TRM_FABLESS: the Terms-tab overview for the fabless model.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_fabless.py

Three sites on one floor, left to right: the chip designer (an office of workstations and a
small compute rack, no tools), the foundry (a fab hall with process tools and a stack of capex
coins), the packaging house (bond/mold lines) and, at the far right, a customer's GPU rack. Data
flows right (tapeout), chips flow right, money flows back left and most of it stays with the
designer.

Beats:
  0 chain     designer -> foundry -> packaging -> customer
  1 design    engineers design; the layout ships as a tapeout
  2 make      foundry prints wafers, packager builds chips, chips go to racks
  3 money     customer pays the designer; the designer pays wafer prices; margin stays
  4 risk      a queue at the foundry; one supplier; who is fabless
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_FABLESS"
BEATS = [
    ("A fabless company designs chips and pays others to make them",
     "A fabless chip company owns the design, the software and the customer, but no factory. Its layouts go to a "
     "foundry that prints the wafers and to packaging and test houses (OSATs) that turn dies into finished chips. "
     "NVIDIA, AMD, Broadcom, Qualcomm and Marvell all work this way."),
    ("The designer's product is a layout file, not silicon",
     "Thousands of engineers write the chip in code, verify it on compute farms and lay it out with EDA software. "
     "The finished design is sent to the foundry as a tapeout. The designer's spending is mostly people, software "
     "licences and mask sets, not buildings."),
    ("The foundry and packaging houses carry the factories",
     "The foundry (mostly TSMC at the leading edge) spends tens of billions a year on fabs and tools and prints the "
     "wafers; packagers like ASE and Amkor, or TSMC's own CoWoS lines, mount the dies with memory into the finished "
     "part. The designer ships those chips to server makers and clouds."),
    ("Low capex, high margins: the designer keeps the value of the design",
     "The customer pays the designer; the designer pays the foundry a wafer price and the packager a fee. Because the "
     "design and software carry the value, a leader like NVIDIA keeps ~70%+ gross margin while spending little on "
     "capex. The foundry earns its own margin on wafers but carries all the plant risk."),
    ("The catch: you queue for someone else's capacity",
     "Fabless companies depend on foundry capacity and pricing: in tight markets everyone lines up for the same "
     "leading-edge and CoWoS slots, and filings name TSMC as a sole or key supplier risk (Taiwan included). Related: "
     "NVIDIA (NVDA), AMD (AMD), Broadcom (AVGO), Marvell (MRVL), Qualcomm (QCOM)."),
]

DES = (-200.0, -110.0)  # designer x span
FAB = (-80.0, 50.0)  # foundry
OSAT = (75.0, 140.0)  # packager
CUST = (165.0, 215.0)  # customer rack
ZB, ZF = -90.0, -10.0


def mats(m):
    m["wall"] = mat("fl_wall", (0.82, 0.84, 0.86), metal=0.2, rough=0.45)
    m["tool2"] = mat("fl_tool", (0.30, 0.45, 0.62), metal=0.4, rough=0.35)
    m["floor"] = mat("fl_floor", (0.50, 0.53, 0.56), metal=0.2, rough=0.5)
    m["code"] = mat("fl_code", (0.40, 1.0, 0.50), emit=(0.40, 1.0, 0.50), strength=2.5)
    m["win"] = mat("fl_win", (0.45, 0.80, 1.0), emit=(0.40, 0.75, 1.0), strength=3.0)
    m["coin"] = mat("fl_coin", (0.95, 0.78, 0.30), metal=0.95, rough=0.25)
    m["cash"] = mat("fl_cash", (1.0, 0.85, 0.30), emit=(1.0, 0.80, 0.25), strength=4.0)
    m["wfr"] = mat("fl_wfr", (0.45, 0.47, 0.60), metal=0.8, rough=0.15)
    m["que"] = mat("fl_que", (1.0, 0.55, 0.25), emit=(1.0, 0.5, 0.2), strength=2.5)


def pad(m, root, name, x0, x1):
    bx(f"{name}_pad", (x0, 0.0, ZB), (x1, 1.0, ZF), m["floor"], root)
    bx(f"{name}_back", (x0, 1.0, ZB - 3.0), (x1, 50.0, ZB), m["wall"], root)


def designer(m, root):
    pad(m, root, "des", *DES)
    x0, x1 = DES
    screens = []
    for r in range(2):
        for c in range(3):
            x = x0 + 14.0 + 28.0 * c
            z = ZF - 20.0 - 32.0 * r
            bx(f"desk{r}{c}", (x - 11.0, 8.0, z - 6.0), (x + 11.0, 9.0, z + 6.0), m["alu"], root)
            for lg in (-1, 1):
                bx(f"leg{r}{c}{lg}", (x + lg * 10.0 - 0.5, 1.0, z - 5.0), (x + lg * 10.0 + 0.5, 8.0, z + 5.0), m["dark"], root)
            bx(f"mon{r}{c}", (x - 8.0, 10.0, z - 5.0), (x + 8.0, 20.0, z - 4.0), m["plastic"], root)
            bx(f"stand{r}{c}", (x - 1.0, 9.0, z - 5.0), (x + 1.0, 10.0, z - 4.5), m["alu"], root)
            s = empty(f"scr{r}{c}", root)
            for k in range(4):
                bx(f"scr{r}{c}_{k}", (x - 7.0, 11.5 + 2.0 * k, z - 3.9), (x - 7.0 + 5.0 + 2.5 * ((k + c) % 4), 12.3 + 2.0 * k, z - 3.7), m["code"], s)
            screens.append(s)
            D.tube(f"chair{r}{c}", (x, 1.0, z + 10.0), (x, 6.0, z + 10.0), 3.0, m["dark"], root, 12)
    # a small compute rack in the corner
    leds = [empty(f"rk{k}", root) for k in range(3)]
    bx("rack", (x1 - 16.0, 1.0, ZB + 2.0), (x1 - 2.0, 46.0, ZB + 16.0), m["dark"], root)
    for s in range(10):
        y = 4.0 + 4.2 * s
        for j in range(3):
            bx(f"rkl{s}{j}", (x1 - 14.0 + 3.5 * j, y, ZB + 16.0), (x1 - 12.5 + 3.5 * j, y + 1.2, ZB + 16.4), m["sig"], leds[(s + j) % 3])
    # the margin pile: coins that grow in beat 3
    pile = empty("pile", root)
    for st, (dx, n) in enumerate(((0.0, 26), (-11.0, 20), (11.0, 16))):
        for k in range(n):
            D.tube(f"coin{st}_{k}", (x0 + 70.0 + dx, 1.0 + 1.4 * k, ZF - 6.0), (x0 + 70.0 + dx, 2.2 + 1.4 * k, ZF - 6.0), 5.0, m["coin"], pile, 24)
    return screens, leds, pile, {"des": ((x0 + x1) / 2, 50.0, ZB), "pile": (x0 + 70.0, 38.0, ZF - 6.0),
                                 "rack": (x1 - 9.0, 46.0, ZB + 9.0), "desk": (x0 + 14.0, 20.0, ZF - 24.0)}


def foundry(m, root):
    pad(m, root, "fab", *FAB)
    x0, x1 = FAB
    bx("fab_roof", (x0, 50.0, ZB - 3.0), (x1, 53.0, ZB + 20.0), m["wall"], root)
    lit = empty("fab_lit", root)
    for c in range(4):
        for r in range(2):
            x = x0 + 18.0 + 32.0 * c
            z = ZF - 18.0 - 36.0 * r
            bx(f"ft{c}{r}", (x - 12.0, 1.0, z - 10.0), (x + 12.0, 30.0, z + 6.0), m["tool2"], root)
            bx(f"ftt{c}{r}", (x - 9.0, 30.0, z - 8.0), (x + 9.0, 34.0, z + 2.0), m["alu"], root)
            D.tube(f"ftw{c}{r}", (x - 3.0, 18.0, z + 6.0), (x - 3.0, 18.0, z + 6.3), 4.5, m["win"], lit, 20)
            for p in range(2):
                bx(f"ftf{c}{r}{p}", (x - 9.0 + 9.0 * p, 10.0, z + 6.0), (x - 3.0 + 9.0 * p, 14.0, z + 9.0), m["foup"] if "foup" in m else m["v12"], root)
    # capex: a tall stack of coins behind the fab
    cap = empty("capex", root)
    for k in range(30):
        D.tube(f"cx{k}", (x1 - 8.0, 53.0 + 1.4 * k, ZB + 8.0), (x1 - 8.0, 54.2 + 1.4 * k, ZB + 8.0), 6.0, m["coin"], cap, 24)
    return lit, cap, {"fab": ((x0 + x1) / 2, 53.0, ZB + 10.0), "capex": (x1 - 8.0, 95.0, ZB + 8.0),
                      "tool": (x0 + 18.0, 34.0, ZF - 18.0)}


def osat(m, root):
    pad(m, root, "os", *OSAT)
    x0, x1 = OSAT
    for r in range(2):
        z = ZF - 22.0 - 34.0 * r
        bx(f"line{r}", (x0 + 4.0, 1.0, z - 6.0), (x1 - 4.0, 8.0, z + 6.0), m["dark"], root)
        for k in range(3):
            x = x0 + 12.0 + 20.0 * k
            bx(f"mach{r}{k}", (x - 7.0, 8.0, z - 8.0), (x + 7.0, 24.0, z + 4.0), m["wall"], root)
            bx(f"machw{r}{k}", (x - 4.0, 14.0, z + 4.0), (x + 4.0, 20.0, z + 4.3), m["screen"], root)
    return {"osat": ((x0 + x1) / 2, 50.0, ZB)}


def customer(m, root):
    pad(m, root, "cu", *CUST)
    x0, x1 = CUST
    leds = [empty(f"cl{k}", root) for k in range(3)]
    for k in range(2):
        xa = x0 + 4.0 + 24.0 * k
        bx(f"crk{k}", (xa, 1.0, ZB + 10.0), (xa + 20.0, 70.0, ZB + 50.0), m["dark"], root)
        for s in range(14):
            y = 4.0 + 4.6 * s
            bx(f"csv{k}{s}", (xa + 1.0, y, ZB + 50.0), (xa + 19.0, y + 3.8, ZB + 50.4), m["grid"], root)
            for j in range(4):
                bx(f"cl{k}{s}{j}", (xa + 3.0 + 4.0 * j, y + 1.4, ZB + 50.4), (xa + 5.0 + 4.0 * j, y + 2.4, ZB + 50.7), m["sig"], leds[(s + j) % 3])
    return leds, {"rack": ((x0 + x1) / 2, 70.0, ZB + 30.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-215.0, -3.0, -110.0), (230.0, 0.0, 20.0), m["grid"], root)
    screens, dleds, pile, dp = designer(m, root)
    flit, capex, fp = foundry(m, root)
    op = osat(m, root)
    cleds, cp = customer(m, root)
    for s in screens:
        show(s, [(F(0, 0), F(5, 0))])
    show(flit, [(F(0, 0), F(5, 0))])
    for k, l in enumerate(dleds):
        blink(l, 1, [k, k + 3], n=6, on=0.6)
    for k, l in enumerate(cleds):
        blink(l, 2, [k, k + 3], n=6, on=0.6)
    show(pile, [(F(3, 0.4), F(5, 0))])
    show(capex, [(F(2, 0), F(5, 0))])

    yb = 60.0
    zf = ZF + 4.0
    # beat 0: one tour of the chain
    run(root, "tour", [(DES[1], 20.0, zf), (FAB[0] + 10.0, 20.0, zf), (OSAT[0] + 10.0, 20.0, zf), (CUST[0] + 10.0, 30.0, zf)], 5, 1.6, m["code"], 0, 0.1, 0.8, 80)
    # beat 1: tapeout beads from the desks to the fab
    run(root, "tape", [(DES[0] + 40.0, 22.0, ZF - 30.0), (DES[1], yb, ZF - 30.0), (FAB[0] + 20.0, yb, ZF - 30.0), (FAB[0] + 20.0, 36.0, ZF - 30.0)], 8, 1.3, m["code"], 1, 0.3, 0.9, 50)
    # beat 2: wafers to the packager, chips to the rack
    run(root, "wafers", [(FAB[1] - 10.0, 10.0, zf), (OSAT[0] + 10.0, 10.0, zf)], 6, 2.4, m["wfr"], 2, 0.0, 0.6, 50)
    run(root, "chips", [(OSAT[1] - 10.0, 10.0, zf), (CUST[0] + 20.0, 10.0, zf), (CUST[0] + 20.0, 40.0, ZB + 52.0)], 6, 1.4, m["v12"], 2, 0.3, 0.9, 50)
    rise(root, "fabheat", ((FAB[0] + FAB[1]) / 2, 53.0, ZB + 20.0), 8, 1.0, m["heat"], 2, 0.0, 0.9, 20.0, 50, (50.0, 10.0))
    # beat 3: money: customer -> designer (big), designer -> foundry (smaller)
    run(root, "pay", [(CUST[0] + 20.0, 74.0, ZB + 30.0), (0.0, 85.0, ZB + 30.0), (DES[0] + 70.0, 40.0, ZF - 6.0)], 14, 1.6, m["cash"], [3, 4], 0.0, 0.7, 60)
    run(root, "wfee", [(DES[0] + 70.0, 30.0, ZF - 6.0), (DES[1], 45.0, zf), (FAB[0] + 20.0, 45.0, zf), (FAB[1] - 8.0, 56.0, ZB + 8.0)], 5, 1.3, m["cash"], 3, 0.3, 0.9, 50)
    # beat 4: a queue of other designers' tapeouts at the fab door
    q = empty("queue", root)
    for k in range(6):
        bx(f"q{k}", (FAB[0] - 4.0 - 4.5 * k, 1.0, ZF - 4.0), (FAB[0] - 1.0 - 4.5 * k, 8.0, ZF - 1.0), m["que"], q)
    show(q, [(F(4, 0.1), F(5, 0))])

    C.tags(root, {
        0: [("chip designer (fabless)", dp["des"]), ("foundry", fp["fab"]), ("packaging + test", op["osat"]),
            ("customer racks", cp["rack"])],
        1: [("engineers + EDA software", dp["desk"]), ("compute farm for verification", dp["rack"]),
            ("tapeout to the foundry", (FAB[0] + 20.0, 40.0, ZF - 30.0))],
        2: [("foundry prints the wafers", fp["tool"]), ("fab capex: $10Bs a year", fp["capex"]),
            ("chips ship to customers", cp["rack"])],
        3: [("customer pays the designer", (0.0, 85.0, ZB + 30.0)), ("wafer price to foundry", (FAB[0] + 20.0, 45.0, zf)),
            ("margin stays: ~70%+ GM", dp["pile"])],
        4: [("queue for TSMC slots", (FAB[0] - 15.0, 8.0, ZF - 2.0)), ("NVDA AMD AVGO MRVL QCOM", dp["des"]),
            ("single-supplier risk", fp["fab"])],
    })
    C.done(SLUG, BEATS, [
        frame((5.0, 20.0, -50.0), 430.0, 0.15, 0.45, pad=1.0),
        frame((-110.0, 25.0, -50.0), 190.0, 0.30, 0.40),
        frame((80.0, 30.0, -50.0), 300.0, -0.15, 0.40, pad=1.0),
        frame((-60.0, 40.0, -50.0), 330.0, 0.10, 0.35, pad=1.0),
        frame((-60.0, 20.0, -50.0), 300.0, 0.25, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
