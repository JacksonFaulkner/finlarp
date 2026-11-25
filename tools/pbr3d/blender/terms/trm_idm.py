"""TRM_IDM: an integrated device manufacturer, drawn as one walled campus that designs, fabs, tests
and sells its own chips.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_idm.py

Inside one perimeter wall: a design studio (left), a fab hall cut open with a litho scanner and a
row of process tools (middle), and a test/packaging line (right) that ends at a loading dock.
Capex arrives as gold beads, a utilization gauge shows how full the fab runs, and in the last
beats a gate in the wall opens for an outside customer (the foundry pivot).

Beats:
  0 campus    design -> fab -> test -> ship, all one company
  1 tuned     design and process teams tune each other: feedback loop
  2 capex     billions in, the fab must run full; a demand dip leaves it idle
  3 foundry   a gate opens: outside designs come in to fill the fab
  4 who       Intel, TI, Micron, ADI, Samsung, SK hynix
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_IDM"
BEATS = [
    ("An IDM designs its chips and makes them in its own fabs",
     "An integrated device manufacturer (IDM) does the whole job in-house: its engineers design the chip, its own "
     "fabs make the wafers, and its own lines test and package them. Intel, Texas Instruments, Micron, Analog "
     "Devices, Samsung and SK hynix work this way. The opposite is fabless (Nvidia, AMD), which rents a foundry."),
    ("Design and process are tuned together",
     "Because the designers and the fab sit in one company, the process can be shaped around the product and the "
     "product around the process. That matters most where the transistor is the product: memory cells (Micron, "
     "SK hynix), analog and power parts (TI, ADI) whose specs come straight from the fab recipe."),
    ("Fabs cost billions up front and only pay off when full",
     "A leading-edge fab costs $20B or more, and almost all of that is fixed: tools depreciate whether wafers flow "
     "or not. An IDM must fill its fabs with its own products; when demand dips, utilization falls and margins "
     "collapse fast. That operating leverage is why memory and IDM earnings swing so hard through the cycle."),
    ("Some IDMs now sell spare capacity as a foundry",
     "To keep fabs full and share the cost of new nodes, some IDMs open the gate to outside designs. Intel Foundry "
     "takes customer chips; Samsung has long run a foundry next to its memory business. Winning outside customers "
     "means proving yields and keeping their designs walled off from the in-house chip teams."),
    ("Mostly memory, analog and Intel",
     "Memory (Micron MU, SK hynix, Samsung) and analog/mixed-signal (TI TXN, ADI, Infineon) stay IDM because the "
     "process is the edge and older 300 mm fabs keep earning for decades. Intel (INTC) is the big logic IDM, now "
     "split into product and foundry arms. AI demand pulls hardest on memory IDMs through HBM."),
]

WALL = (-200.0, 200.0, -170.0, 10.0)
DS = (-155.0, -80.0)  # design studio centre x, z
FAB = (-90.0, 90.0, -150.0, -20.0)  # fab hall x0, x1, z0, z1
TL = (150.0, -80.0)  # test line centre x, z
GATE_Z = -80.0


def mats(m):
    m["code"] = mat("idm_code", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=2.5)
    m["wall"] = mat("idm_wall", (0.62, 0.64, 0.68), rough=0.7)
    m["tool"] = mat("idm_tool", (0.80, 0.82, 0.84), metal=0.2, rough=0.5)
    m["glass"] = mat("idm_glass", (0.35, 0.45, 0.55), rough=0.1)
    m["wafer"] = mat("idm_wafer", (0.45, 0.47, 0.60), metal=0.8, rough=0.15)
    m["cash"] = mat("idm_cash", (1.0, 0.80, 0.25), emit=(1.0, 0.75, 0.20), strength=3.0)
    m["euv"] = mat("idm_euv", (0.75, 0.45, 1.0), emit=(0.70, 0.40, 1.0), strength=3.0)
    m["low"] = mat("idm_low", (1.0, 0.30, 0.15), emit=(1.0, 0.25, 0.10), strength=2.5)
    m["ext"] = mat("idm_ext", (0.35, 0.75, 1.0), emit=(0.30, 0.70, 1.0), strength=3.0)


def walls(m, root):
    x0, x1, z0, z1 = WALL
    g = empty("wall", root)
    bx("w_back", (x0, 0.0, z0), (x1, 18.0, z0 + 3.0), m["wall"], g)
    bx("w_left", (x0, 0.0, z0), (x0 + 3.0, 18.0, z1), m["wall"], g)
    bx("w_rightA", (x1 - 3.0, 0.0, z0), (x1, 18.0, GATE_Z - 15.0), m["wall"], g)
    bx("w_rightB", (x1 - 3.0, 0.0, GATE_Z + 15.0), (x1, 18.0, z1), m["wall"], g)
    bx("w_front", (x0, 0.0, z1 - 3.0), (x1, 6.0, z1), m["wall"], g)  # low front wall keeps the view open
    gate = empty("gate", root)
    bx("w_gate", (x1 - 3.0, 0.0, GATE_Z - 15.0), (x1, 18.0, GATE_Z + 15.0), m["dark"], gate)
    show(gate, [(F(0, 0), F(3, 0.2))])
    for k in range(6):  # wall-top lamps
        x = x0 + (x1 - x0) * (k + 0.5) / 6
        bx(f"w_lamp{k}", (x - 2.0, 18.0, z0), (x + 2.0, 20.0, z0 + 3.0), m["sig"], g)


def studio(m, root):
    x, z = DS
    g = empty("ds", root)
    bx("ds_floor", (x - 35.0, 0.0, z - 60.0), (x + 35.0, 2.0, z + 60.0), m["dark"], g)
    pts = []
    for r in range(3):
        for c in range(2):
            cx, cz = x - 15.0 + 30.0 * c, z - 40.0 + 40.0 * r
            bx(f"ds_d{r}{c}", (cx - 10.0, 2.0, cz - 8.0), (cx + 10.0, 8.0, cz + 8.0), m["plastic"], g)
            bx(f"ds_s{r}{c}", (cx - 8.0, 8.0, cz - 6.0), (cx + 8.0, 20.0, cz - 5.0), m["screen"], g)
            for k in range(4):
                w = 4.0 + 2.0 * ((r + c + k) % 4)
                bx(f"ds_l{r}{c}{k}", (cx - 7.0, 17.5 - 2.5 * k, cz - 4.9), (cx - 7.0 + w, 18.3 - 2.5 * k, cz - 4.8), m["code"], g)
            pts.append((cx, 20.0, cz - 5.0))
    return pts


def fab(m, root):
    x0, x1, z0, z1 = FAB
    g = empty("fab", root)
    bx("fab_floor", (x0, 0.0, z0), (x1, 3.0, z1), m["grid"], g)
    bx("fab_back", (x0, 3.0, z0), (x1, 70.0, z0 + 3.0), m["tool"], g)
    bx("fab_roof", (x0, 70.0, z0), (x1, 73.0, z0 + 40.0), m["tool"], g)  # roof only over the back: cut away
    for xx in (x0, x1 - 3.0):
        bx(f"fab_side{xx:.0f}", (xx, 3.0, z0), (xx + 3.0, 12.0, z1), m["glass"], g)
    # scanner at the left of the hall
    sx, sz = x0 + 40.0, -85.0
    bx("sc_base", (sx - 25.0, 3.0, sz - 25.0), (sx + 25.0, 8.0, sz + 25.0), m["dark"], g)
    D.tube("sc_w", (sx, 8.0, sz), (sx, 9.0, sz), 14.0, m["wafer"], g, 48)
    for k in range(5):
        D.tube(f"sc_l{k}", (sx, 20.0 + 5.0 * k, sz), (sx, 23.0 + 5.0 * k, sz), 9.0 + (2 - abs(k - 2)) * 1.5, m["alu"], g, 32)
    bx("sc_ret", (sx - 12.0, 48.0, sz - 12.0), (sx + 12.0, 50.0, sz + 12.0), m["quartz_c"], g)
    beam = empty("sc_beam", root)
    D.tube("sc_b", (sx, 48.0, sz), (sx, 9.5, sz), 1.4, m["euv"], beam, 12)
    # process tools in a row behind
    leds = [empty(f"fab_led{k}", root) for k in range(3)]
    for k in range(5):
        tx = x0 + 85.0 + 20.0 * k
        bx(f"tool{k}", (tx - 8.0, 3.0, -135.0), (tx + 8.0, 40.0, -105.0), m["tool"], g)
        bx(f"tool{k}_win", (tx - 6.0, 12.0, -105.0), (tx + 6.0, 30.0, -104.6), m["glass"], g)
        bx(f"tool{k}_led", (tx - 2.0, 34.0, -104.6), (tx + 2.0, 36.0, -104.2), m["sig"], leds[k % 3])
    for l in leds:
        show(l, [])
    # wafer carts in front
    for k in range(4):
        cx = x0 + 90.0 + 18.0 * k
        for j in range(5):
            D.tube(f"cart{k}_{j}", (cx, 3.0 + 1.3 * j, -45.0), (cx, 3.8 + 1.3 * j, -45.0), 6.0, m["wafer"], g, 32)
    return beam, leds, {"fab": (0.0, 73.0, -130.0), "scan": (sx, 50.0, sz), "tools": (x0 + 125.0, 40.0, -105.0),
                        "in": (x0 + 10.0, 20.0, -85.0), "out": (x1 - 10.0, 20.0, -85.0), "carts": (x0 + 117.0, 10.0, -45.0)}


def testline(m, root):
    x, z = TL
    g = empty("tl", root)
    bx("tl_belt", (x - 25.0, 0.0, z - 60.0), (x - 5.0, 8.0, z + 60.0), m["dark"], g)
    for k in range(10):
        bx(f"tl_chip{k}", (x - 20.0, 8.0, z - 55.0 + 11.0 * k), (x - 10.0, 10.0, z - 47.0 + 11.0 * k), m["mold"], g)
    bx("tl_tester", (x - 2.0, 0.0, z - 30.0), (x + 25.0, 40.0, z + 10.0), m["tool"], g)
    bx("tl_head", (x - 25.0, 30.0, z - 20.0), (x - 2.0, 36.0, z), m["alu"], g)
    leds = [empty(f"tl_led{k}", root) for k in range(2)]
    for k in range(6):
        bx(f"tl_l{k}", (x + 4.0 + 3.0 * k, 34.0, z + 10.0), (x + 6.0 + 3.0 * k, 36.0, z + 10.4), m["sig"], leds[k % 2])
    for l in leds:
        show(l, [])
    # loading dock: stacked reels/boxes
    for k in range(3):
        bx(f"dock{k}", (x - 25.0 + 15.0 * k, 0.0, -5.0), (x - 13.0 + 15.0 * k, 12.0, 8.0), m["cardboard"] if "cardboard" in m else m["ceramic"], g)
    return leds, {"test": (x + 12.0, 40.0, z - 10.0), "belt": (x - 15.0, 10.0, z + 40.0), "dock": (x, 12.0, 2.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    x0, x1, z0, z1 = WALL
    bx("ground", (x0 - 60.0, -3.0, z0 - 20.0), (x1 + 90.0, 0.0, z1 + 30.0), m["grid"], root)
    walls(m, root)
    dsp = studio(m, root)
    beam, fleds, fp = fab(m, root)
    tleds, tp = testline(m, root)

    # beat 0: one flow through the campus; also beats 1 and 4
    for k, p in enumerate(dsp[:3]):
        run(root, f"d2f{k}", [p, (p[0] + 40.0, 40.0, p[2]), fp["in"]], 2, 1.2, m["code"], [0, 1, 4], 0.05 + 0.1 * k, 0.4 + 0.1 * k, 35)
    run(root, "f2t", [fp["out"], (FAB[1] + 25.0, 30.0, -85.0), (TL[0] - 15.0, 12.0, TL[1] - 50.0), (TL[0] - 15.0, 12.0, TL[1] + 60.0)],
        6, 1.3, m["v12"], [0, 4], 0.25, 0.8, 45)
    run(root, "ship", [tp["dock"], (TL[0], 20.0, 40.0), (x1 + 80.0, 10.0, 40.0)], 4, 1.4, m["v12"], [0, 4], 0.5, 0.9, 30)
    show(beam, [(F(0, 0.2), F(2, 0.5)), (F(3, 0.2), F(5, 0))])
    for l in fleds + tleds:
        for b in (0, 1, 3, 4):
            blink(l, b, [0, 2, 4, 6], n=8, on=0.6)

    # beat 1: feedback loop design <-> fab
    loop = [fp["scan"], (-100.0, 60.0, -60.0), dsp[2], (-120.0, 40.0, -110.0), fp["scan"]]
    run(root, "tune", loop, 8, 1.0, m["ext"], 1, 0.0, 0.8, 50)

    # beat 2: capex pours in; utilization gauge rises full, then a demand dip drains it
    run(root, "capex", [(0.0, 160.0, -90.0), (0.0, 110.0, -90.0), (0.0, 74.0, -90.0)], 12, 1.8, m["cash"], 2, 0.0, 0.5, 30)
    gx, gz = 40.0, -10.0
    bx("g_frame", (gx - 2.0, 0.0, gz - 4.0), (gx + 2.0, 62.0, gz + 4.0), m["dark"], root)
    for k in range(10):
        e = empty(f"g_bar{k}", root)
        bx(f"g_b{k}", (gx + 2.0, 2.0 + 6.0 * k, gz - 3.0), (gx + 12.0, 6.5 + 6.0 * k, gz + 3.0), m["sig"], e)
        off = F(2, 0.85 - 0.04 * k) if k >= 4 else F(3, 0.3)
        show(e, [(F(0, 0), F(2, 0)), (F(2, 0.1 + 0.03 * k), off), (F(3, 0.3 + 0.04 * k), F(5, 0))])
        if k < 4:
            r = empty(f"g_low{k}", root)
            bx(f"g_lb{k}", (gx + 2.0, 2.0 + 6.0 * k, gz - 3.0), (gx + 12.2, 6.5 + 6.0 * k, gz + 3.1), m["low"], r)
            show(r, [(F(2, 0.7), F(3, 0.3))])
    rise(root, "fixed", (0.0, 74.0, -120.0), 6, 1.0, m["heat"], 2, 0.1, 0.6, 25.0, 40, (40.0, 10.0))

    # beat 3: gate opens, outside customer's designs come in
    ext = empty("ext_studio", root)
    ex, ez = x1 + 55.0, GATE_Z
    bx("ex_desk", (ex - 14.0, 0.0, ez - 14.0), (ex + 14.0, 8.0, ez + 14.0), m["plastic"], ext)
    bx("ex_scr", (ex - 1.0, 8.0, ez - 11.0), (ex + 1.0, 24.0, ez + 11.0), m["screen"], ext)
    bx("ex_glow", (ex - 1.4, 10.0, ez - 9.0), (ex - 1.0, 22.0, ez + 9.0), m["ext"], ext)
    show(ext, [(F(3, 0.0), F(5, 0))])
    run(root, "outside", [(ex - 2.0, 18.0, ez), (x1 + 5.0, 12.0, GATE_Z), (FAB[1] + 10.0, 20.0, -85.0), fp["out"], fp["scan"]],
        8, 1.3, m["ext"], [3, 4], 0.2, 0.85, 55)

    C.tags(root, {
        0: [("design teams", dsp[1]), ("own fab, cut open", fp["fab"]), ("test + packaging", tp["test"]),
            ("one company, one wall", (x0 + 20.0, 20.0, z0 + 3.0))],
        1: [("process tuned to the product", fp["scan"]), ("feedback: design <-> fab", (-100.0, 60.0, -60.0)),
            ("memory, analog, power", dsp[0])],
        2: [("$20B+ per fab, mostly fixed", (0.0, 120.0, -90.0)), ("utilization must stay high", (gx + 7.0, 64.0, gz)),
            ("demand dip: idle tools", fp["tools"])],
        3: [("gate opens: foundry service", (x1, 20.0, GATE_Z)), ("outside customer design", (ex, 24.0, ez)),
            ("fills spare capacity", fp["carts"])],
        4: [("INTC: logic + Intel Foundry", fp["fab"]), ("MU, SK hynix, Samsung: memory", fp["tools"]),
            ("TXN, ADI: analog", tp["test"])],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 30.0, -80.0), 440.0, 0.20, 0.50, pad=1.0),
        frame((-90.0, 30.0, -80.0), 220.0, 0.30, 0.45),
        frame((10.0, 50.0, -80.0), 260.0, 0.10, 0.30),
        frame((150.0, 25.0, -70.0), 260.0, -0.45, 0.40),
        frame((20.0, 30.0, -80.0), 460.0, -0.15, 0.50, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
