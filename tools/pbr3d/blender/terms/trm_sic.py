"""TRM_SIC on the MLCC base board: a SiC boule and wafer, then a SiC MOSFET cut open beside a
silicon one rated for the same voltage, so the thin drift region shows.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_sic.py
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, rise  # noqa: E402

SLUG = "TRM_SIC"
BEATS = [
    ("SiC switches the high-voltage side: 800 V racks, UPS, EVs",
     "Silicon carbide (SiC) power chips sit where voltages are high: in the 800 V DC power shelves coming to AI racks, "
     "in UPS and solar inverters, and above all in EV traction inverters. The GPU board's own 12 V to 0.8 V stage stays "
     "silicon (and increasingly GaN)."),
    ("It starts as a hard, slow-growing crystal",
     "SiC crystals grow by sublimation at over 2,000 C, millimetres a day, far slower than silicon. Boules are short and "
     "wafers small (150 mm moving to 200 mm) and full of defects to control, which is why SiC wafers cost many times "
     "silicon ones and why Wolfspeed, Coherent and onsemi fight over substrate supply."),
    ("Same voltage, a tenth of the drift: why SiC wins",
     "SiC's wide bandgap gives about ten times silicon's breakdown field. A SiC MOSFET can block 1,200 V with a drift "
     "region roughly a tenth as thick as a silicon device's, and that thin drift has far lower resistance."),
    ("On: less resistance, less heat, at higher temperature",
     "Electrons cross the thin SiC drift with little loss while the thick silicon one heats up. SiC also switches fast "
     "with no hole tail and survives hotter junctions, so inverters shrink and EV range rises a few percent."),
    ("A dozen SiC dies in a module drive an EV motor or an 800 V shelf",
     "Modules gang SiC dies into the six switches of a three-phase inverter. Growth tracks EV builds, plus solar, storage "
     "and data-center 800 V DC. Players: Wolfspeed (WOLF), onsemi (ON), STMicro (STM), Infineon (IFNNY), Coherent (COHR)."),
]

X0, X1, Z0 = 152.0, 246.0, -40.0
XM = 199.0  # SiC device x0..XM-3, silicon device XM+3..x1


def devices(m, root):
    g = empty("dev", root)
    sic = [(0.6, 3.0, "alum"), (3.0, 12.0, "sic"), (12.0, 16.0, "ndrift"), (16.0, 19.0, "pbody"), (19.0, 20.5, "nplus")]
    si = [(0.6, 3.0, "alum"), (3.0, 8.0, "nplus"), (8.0, 46.0, "ndrift"), (46.0, 49.0, "pbody"), (49.0, 50.5, "nplus")]
    C.xsec(m, g, "sic", X0, XM - 3.0, Z0, sic)
    C.xsec(m, g, "si", XM + 3.0, X1, Z0, si)
    for name, a, b, ytop in (("sicg", X0, XM - 3.0, 20.5), ("sig", XM + 3.0, X1, 50.5)):
        for k in range(3):
            xc = a + (b - a) * (k + 0.5) / 3
            bx(f"{name}{k}_ox", (xc - 4.0, ytop, Z0), (xc + 4.0, ytop + 0.8, 0.03), m["oxide"], g)
            bx(f"{name}{k}_p", (xc - 3.2, ytop + 0.8, Z0), (xc + 3.2, ytop + 2.8, 0.05), m["poly"], g)
        bx(f"{name}_met", (a, ytop + 3.5, Z0), (b, ytop + 6.0, 0.0), m["alum"], g)
    # drift-thickness brackets
    for name, x, y0, y1 in (("bk_sic", X0 - 3.0, 12.0, 16.0), ("bk_si", X1 + 3.0, 8.0, 46.0)):
        bx(name, (x - 0.4, y0, 0.0), (x + 0.4, y1, 0.6), m["field"], g)
    hot = empty("si_hot", root)
    bx("si_hot_b", (XM + 3.5, 8.5, Z0 + 0.5), (X1 - 0.5, 45.5, 0.1), m["die_hot"], hot)
    show(hot, [])
    paths_sic = [[(x, 26.0, 1.0), (x, 16.0, 1.0), (x, 3.0, 1.0)] for x in (X0 + 8.0, X0 + 20.0, X0 + 32.0)]
    paths_si = [[(x, 56.0, 1.0), (x, 46.0, 1.0), (x, 3.0, 1.0)] for x in (XM + 10.0, XM + 22.0, XM + 34.0)]
    return hot, paths_sic, paths_si


def boule(m, root):
    """A hexagonal SiC boule on its seed, and a sliced wafer, behind the devices."""
    g = empty("boule", root)
    c = (175.0, 0.6, -120.0)
    pts = []
    for k in range(6):
        a = math.pi / 3 * k
        pts.append((c[0] + 22.0 * math.cos(a), c[2] + 22.0 * math.sin(a)))
    D.tube("boule_body", (c[0], 0.6, c[2]), (c[0], 30.0, c[2]), 22.0, m["sic"], g, 6)
    D.tube("boule_seed", (c[0], 30.0, c[2]), (c[0], 33.0, c[2]), 18.0, m["dark"], g, 24)
    D.tube("wafer", (222.0, 0.6, -120.0), (222.0, 2.4, -120.0), 22.0, m["sic"], g, 48)
    for i in range(-3, 4):
        for j in range(-3, 4):
            if i * i + j * j <= 9:
                bx(f"wd{i}{j}", (222.0 + 5.4 * i - 2.3, 2.6, -120.0 + 5.4 * j - 2.3), (222.0 + 5.4 * i + 2.3, 2.9, -120.0 + 5.4 * j + 2.3), m["silicon"], g)
    return g, {"boule": (c[0], 33.0, c[2]), "wafer": (222.0, 3.0, -120.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root)
    hot, ps, pi = devices(m, root)
    bg, bp = boule(m, root)
    for k, p in enumerate(ps):
        run(root, f"es{k}", p, 5, 0.9, m["e_blue"], [3, 4], 0.0, 0.85, 25)
    for k, p in enumerate(pi):
        run(root, f"ei{k}", p, 3, 0.9, m["e_blue"], [3, 4], 0.0, 0.85, 70)
    show(hot, [(F(3, 0.25), F(5, 0))])
    rise(root, "sih", ((XM + X1) / 2, 57.0, -20.0), 6, 1.1, m["heat"], 3, 0.25, 0.9, 30.0, 60, (18.0, 12.0))

    C.tags(root, {
        0: [("GPU board: 12 V side, silicon", b["pk"]["top"]), ("SiC: 800 V shelves, UPS, EVs", (XM, 30.0, -20.0))],
        1: [("SiC boule: grown >2,000 C", bp["boule"]), ("150 -> 200 mm wafer", bp["wafer"])],
        2: [("SiC: 1,200 V, thin drift", (X0 - 3.0, 16.0, 0.0)), ("silicon: same volts, ~10x drift", (X1 + 3.0, 40.0, 0.0))],
        3: [("SiC: low loss", (X0 + 20.0, 26.0, 0.0)), ("silicon heats", ((XM + X1) / 2, 50.0, 0.0))],
        4: [("WOLF, ON, STM, IFNNY, COHR", (XM, 30.0, -20.0)), ("EV inverter + 800 V DC", bp["wafer"])],
    })
    cb = (XM, 28.0, -12.0)
    C.done(SLUG, BEATS, [
        frame((90.0, 10.0, -90.0), 380.0, 0.35, 0.55, pad=1.0),
        frame((198.0, 12.0, -120.0), 150.0, 0.30, 0.55),
        frame(cb, 110.0, 0.10, 0.10),
        frame(cb, 100.0, 0.18, 0.12),
        frame((200.0, 20.0, -70.0), 170.0, 0.35, 0.40),
    ], root)


if __name__ == "__main__":
    build()
