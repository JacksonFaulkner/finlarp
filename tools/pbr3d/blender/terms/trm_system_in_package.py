"""TRM_SYSTEM_IN_PACKAGE: the Terms-tab overview for system in package (SiP), at POWER-page detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_system_in_package.py

Left: a board with the function built from separate packages (processor, memory, RF chip, crystal,
dozens of passives) spread over a wide area. Right: the same function as one SiP module ~12x life size,
cut open at the front: laminate substrate with copper layers and BGA balls, a flip-chip processor on bumps,
a stack of memory dies wire-bonded in steps, an RF die walled off by a shield fence, passives soldered
straight onto the substrate, all under mold compound and a metal EMI shield.

Beats:
  0 compare   discrete parts sprawl vs one small module
  1 inside    the dies and passives on one substrate
  2 wiring    signals run die to die through the substrate and bond wires
  3 shield    mold + shield, RF kept in; balls to the board
  4 who       phones, wearables, networking; related packaging methods
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, bx, empty, mat, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import frame, run, rise, present, blink  # noqa: E402

SLUG = "TRM_SYSTEM_IN_PACKAGE"
BEATS = [
    ("A system in package puts a whole circuit into one module",
     "A normal board builds a function from separate packages: a processor, memory, a radio chip, a crystal and dozens "
     "of small capacitors, each soldered on with board traces between them. A system in package (SiP) puts all of "
     "those inside one module, so the board just sees one part. The module can take a fraction of the area."),
    ("Inside: several dies and passives on one small substrate",
     "The base is a thin laminate substrate with its own copper layers. Bare dies sit on it: a processor flipped onto "
     "solder bumps, memory dies stacked and wire-bonded in steps, an RF die, plus capacitors and inductors soldered "
     "straight on. Each die can come from a different fab and process, which one big chip cannot do."),
    ("The module wires its own dies together",
     "Signals run die to die through the substrate's traces and bond wires that are only millimetres long, instead of "
     "centimetres of board. Shorter paths mean less power, less noise and faster links, and the maker tests the "
     "finished function before it ships."),
    ("Mold and a metal shield seal it; balls connect it to the board",
     "Everything is encapsulated in mold compound, and a sputtered metal shield over the top and internal fence walls "
     "keep radio noise in and out. Solder balls underneath connect the module to the main board in one reflow step, "
     "saving assembly steps for the phone or device maker."),
    ("Phones, wearables and networking use it; AI packages use cousins",
     "Watches, earbuds and phone radio front-ends are mostly SiP. Optical modules and edge devices use it too, and "
     "multi-die AI packages (chiplets on interposers) are related heterogeneous integration done at finer pitch. "
     "Related: Amkor (AMKR), ASE (ASX)."),
]

SX0, SX1, SZ0 = 60.0, 230.0, -110.0  # SiP substrate (front cut at z = 0)
SY = 6.0  # substrate top above the board


def mats(m):
    m["sp_mold"] = mat("sp_mold", (0.08, 0.08, 0.09), rough=0.6, alpha=0.35)
    m["sp_shield"] = mat("sp_shield", (0.72, 0.74, 0.78), metal=0.95, rough=0.25)
    m["sp_rf"] = mat("sp_rf", (0.45, 0.30, 0.55), metal=0.4, rough=0.3)
    m["sp_mem"] = mat("sp_mem", (0.20, 0.34, 0.62), metal=0.4, rough=0.35)
    m["sp_xtal"] = mat("sp_xtal", (0.75, 0.76, 0.78), metal=0.9, rough=0.3)
    m["sp_sig"] = mat("sp_sig", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=4.0)
    m["sp_glow"] = mat("sp_glow", (0.35, 0.8, 1.0), emit=(0.35, 0.8, 1.0), strength=1.5)


def discrete(m, root):
    """The spread-out version on a board at left."""
    g = empty("disc", root)
    C.chip(m, g, "d_cpu", (-150.0, 0.0, -60.0), 40.0, 40.0, h=4.0, pins=10)
    C.chip(m, g, "d_mem", (-80.0, 0.0, -40.0), 34.0, 18.0, h=3.5, pins=8)
    C.chip(m, g, "d_mem2", (-80.0, 0.0, -80.0), 34.0, 18.0, h=3.5, pins=8)
    C.chip(m, g, "d_rf", (-210.0, 0.0, -30.0), 22.0, 22.0, h=3.0, pins=6, body="mold")
    bx("d_xtal", (-215.0, 0.0, -100.0), (-200.0, 4.0, -92.0), m["sp_xtal"], g)
    bx("d_ant", (-250.0, 0.0, -20.0), (-240.0, 1.0, -120.0), m["copper"], g)
    for i in range(6):
        for j in range(3):
            D.mlcc(m, g, f"d_c{i}_{j}", (-200.0 + i * 24.0, 0.0, -125.0 + j * 7.0), 6.0, 3.0, 3.0)
    for k, pts in enumerate(([(-130.0, 0.02, -60.0), (-97.0, 0.02, -60.0), (-97.0, 0.02, -40.0)],
                              [(-130.0, 0.02, -70.0), (-97.0, 0.02, -80.0)],
                              [(-170.0, 0.02, -50.0), (-199.0, 0.02, -30.0)],
                              [(-221.0, 0.02, -30.0), (-240.0, 0.02, -30.0)])):
        C.trace(m, g, f"d_tr{k}", pts, 1.2)
    sig = [(-130.0, 1.0, -60.0), (-97.0, 1.0, -60.0), (-97.0, 1.0, -40.0)]
    run(root, "d_sig", sig, 6, 1.2, m["sp_sig"], 0, 0.1, 0.8, 50)
    run(root, "d_sig2", [(-170.0, 1.0, -50.0), (-199.0, 1.0, -30.0)], 5, 1.2, m["sp_sig"], 0, 0.1, 0.8, 50)
    return g


def sip(m, root):
    g = empty("sip", root)
    # BGA balls and substrate with copper layers at the cut
    for i in range(14):
        for j in range(9):
            x, z = SX0 + 6.0 + i * 11.8, SZ0 + 6.0 + j * 11.8
            if z < -2.0:
                C.O.ball(f"s_ball{i}_{j}", (x, 1.4, z), 2.4, m["solder"], g, 10)
    bx("s_sub", (SX0, 3.0, SZ0), (SX1, SY, 0.0), m["substrate"], g)
    for k in range(3):
        y = 3.6 + k * 0.8
        bx(f"s_cu{k}", (SX0, y, -0.3), (SX1, y + 0.3, 0.05), m["copper"], g)
    for x in range(int(SX0) + 10, int(SX1) - 5, 14):
        bx(f"s_via{x}", (x - 0.4, 3.0, -0.3), (x + 0.4, SY, 0.06), m["copper"], g)
    # processor: flip chip on bumps
    for i in range(10):
        C.O.ball(f"s_bump{i}", (78.0 + i * 3.6, SY + 0.7, -2.0), 0.8, m["solder"], g, 8)
    bx("s_cpu", (75.0, SY + 1.4, -55.0), (115.0, SY + 5.0, -1.0), m["die"], g)
    # memory: stepped stack, wire bonded
    for k in range(4):
        x0 = 128.0 + k * 3.0
        bx(f"s_mem{k}", (x0, SY + k * 2.6, -60.0), (170.0, SY + k * 2.6 + 2.2, -1.0), m["sp_mem"], g)
        D.wire(f"s_bw{k}", D.arc((x0 + 1.0, SY + k * 2.6 + 2.2, -3.0), (124.0, SY + 0.2, -3.0), 4.0 + k * 1.5), 0.35, m["gold"], g)
    # RF die inside a shield fence
    bx("s_rf", (190.0, SY, -40.0), (215.0, SY + 3.0, -1.0), m["sp_rf"], g)
    for s, (xa, xb) in enumerate(((182.0, 183.5), (221.5, 223.0))):
        bx(f"s_fence{s}", (xa, SY, -50.0), (xb, SY + 13.0, -0.5), m["sp_shield"], g)
    # passives straight on the substrate
    for i in range(7):
        D.mlcc(m, g, f"s_c{i}", (80.0 + i * 20.0, SY, -85.0), 6.0, 3.0, 3.0)
    bx("s_ind", (190.0, SY, -95.0), (210.0, SY + 8.0, -75.0), m["ferrite"], g)
    bx("s_xtal", (215.0, SY, -100.0), (226.0, SY + 3.0, -90.0), m["sp_xtal"], g)
    # mold (translucent so the inside reads) and top shield, back half only so the cut stays open
    mold = empty("s_moldg", root)
    bx("s_mold", (SX0, SY, SZ0), (SX1, SY + 16.0, 0.0), m["sp_mold"], mold)
    shield = empty("s_shg", root)
    bx("s_sh_top", (SX0 - 0.6, SY + 16.0, SZ0 - 0.6), (SX1 + 0.6, SY + 16.8, -30.0), m["sp_shield"], shield)
    bx("s_sh_back", (SX0 - 0.6, 3.0, SZ0 - 0.6), (SX1 + 0.6, SY + 16.8, SZ0), m["sp_shield"], shield)
    for s, x in enumerate((SX0 - 0.6, SX1)):
        bx(f"s_sh_side{s}", (x, 3.0, SZ0), (x + 0.6, SY + 16.8, -30.0), m["sp_shield"], shield)
    present(mold, [(F(3, 0.15), F(5, 0))])
    present(shield, [(F(3, 0.3), F(5, 0))])
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    C.pcb(m, root, "bd", -270.0, 250.0, -150.0, 0.0, t=3.0)
    discrete(m, root)
    # outline of the area the discrete version covers, and the SiP's footprint
    area = empty("area", root)
    for k, (a, b) in enumerate((((-262.0, 0.1, -142.0), (-258.0, 0.6, -8.0)), ((-62.0, 0.1, -142.0), (-58.0, 0.6, -8.0)),
                                ((-262.0, 0.1, -142.0), (-58.0, 0.6, -138.0)), ((-262.0, 0.1, -12.0), (-58.0, 0.6, -8.0)))):
        bx(f"area{k}", a, b, m["sp_glow"], area)
    show(area, [(F(0, 0.3), F(1, 0))])
    sip(m, root)

    # beat 1: dies light up in turn
    for k, (a, b) in enumerate((((75.0, SY + 5.0, -55.0), (115.0, SY + 5.3, -1.0)),
                                ((137.0, SY + 10.0, -60.0), (170.0, SY + 10.3, -1.0)),
                                ((190.0, SY + 3.0, -40.0), (215.0, SY + 3.3, -1.0)))):
        hl = empty(f"hl{k}", root)
        bx(f"hl{k}_b", a, b, m["sp_glow"], hl)
        show(hl, [(F(1, 0.15 + 0.25 * k), F(1, 0.4 + 0.25 * k))])

    # beat 2: signals die to die: cpu -> substrate -> memory bond wires; cpu -> rf
    y = SY - 0.6
    run(root, "w_mem", [(110.0, SY + 1.0, -2.0), (112.0, y, 0.6), (124.0, y, 0.6), (124.0, SY + 0.3, -3.0),
                         (129.0, SY + 6.0, -3.0), (137.0, SY + 9.0, -3.0)], 8, 0.9, m["sp_sig"], [2, 4], 0.0, 0.8, 40)
    run(root, "w_rf", [(114.0, SY + 1.0, -2.0), (116.0, y, 0.6), (190.0, y, 0.6), (192.0, SY + 3.0, -2.0)], 8, 0.9,
        m["pwm"], [2, 4], 0.05, 0.85, 45)
    run(root, "w_pwr", [(120.0, 1.0, 0.6), (120.0, y, 0.6), (95.0, y, 0.6), (95.0, SY + 1.0, -2.0)], 6, 0.9, m["v12"], 2, 0.1, 0.8, 40)
    rise(root, "cpu_heat", (95.0, SY + 6.0, -28.0), 6, 1.0, m["heat"], 2, 0.2, 0.8, 18.0, 50, (14.0, 12.0))

    # beat 3: RF rings stay inside the fence/shield; balls carry signals to the board
    C.rings(m, root, "rf", (202.0, SY + 5.0, -10.0), 3, n=3, r0=2.0, r1=14.0, axis="y")
    run(root, "balls", [(150.0, SY, -4.0), (150.0, 1.4, -4.0), (150.0, 0.2, -4.0), (150.0, 0.2, 20.0)], 6, 1.0,
        m["sp_sig"], 3, 0.4, 0.9, 30)

    # beat 4: modules multiply (phones, watches); blink the shield edge
    edge = empty("edge", root)
    bx("edge_b", (SX0 - 1.0, SY + 16.8, -31.0), (SX1 + 1.0, SY + 17.3, -29.0), m["sp_glow"], edge)
    blink(edge, 4, [0, 2, 4, 6], n=8, on=0.6)

    C.tags(root, {
        0: [("separate packages: wide area", (-150.0, 6.0, -60.0)), ("one SiP module", (145.0, 24.0, -60.0)),
            ("board traces, cm long", (-110.0, 1.0, -60.0))],
        1: [("flip-chip processor", (95.0, SY + 5.0, -10.0)), ("stacked memory, wire bonds", (150.0, SY + 11.0, -10.0)),
            ("RF die", (202.0, SY + 3.0, -10.0)), ("passives on substrate", (120.0, SY + 3.0, -85.0)),
            ("laminate substrate", (200.0, 4.0, 0.0))],
        2: [("die to die, mm long", (124.0, SY, 0.0)), ("bond wires", (130.0, SY + 8.0, -3.0)),
            ("tested as one function", (145.0, SY + 10.0, -60.0))],
        3: [("mold compound", (100.0, SY + 14.0, -60.0)), ("metal EMI shield", (150.0, SY + 17.0, -80.0)),
            ("shield fence round RF", (222.0, SY + 13.0, -10.0)), ("solder balls to board", (150.0, 1.0, 0.0))],
        4: [("watches, earbuds, phone RF", (-150.0, 6.0, -60.0)), ("AMKR  ASX", (80.0, SY + 18.0, -100.0)),
            ("chiplet AI packages: cousins", (200.0, SY + 18.0, -40.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-20.0, 5.0, -70.0), 520.0, 0.20, 0.55, pad=1.0),
        frame((150.0, 10.0, -30.0), 170.0, 0.25, 0.40),
        frame((150.0, 8.0, -10.0), 120.0, 0.15, 0.25),
        frame((150.0, 10.0, -50.0), 190.0, -0.25, 0.45),
        frame((20.0, 10.0, -70.0), 460.0, 0.30, 0.50, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
