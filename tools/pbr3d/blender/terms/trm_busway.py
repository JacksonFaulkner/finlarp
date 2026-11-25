"""TRM_BUSWAY: overhead busway feeding rack rows from switchgear, with one run cut open.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_busway.py

No GPU board: busway is building power distribution. Units are centimetres. Left: a switchgear
lineup (front cut, breakers visible). A busway trunk leaves its top and runs overhead along x above
a row of racks; plug-in tap-off boxes hang from it and drop short cords to each rack's PDU. Right:
a section of busway ~4x size, cut open: steel housing, four insulated copper bars (L1 L2 L3 N) and a
plug-in opening with a tap's stabs gripping the bars.

Beats:
  0 room     switchgear, overhead busway, taps and racks
  1 inside   the cut-open section: bars in a steel housing
  2 feed     current flows along the bars and down each tap to the racks
  3 add      a new rack arrives; a tap clips on live, no cable pulled
  4 market   wide view, who sells it
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat, tube, key  # noqa: E402
from power_vrm_detail import frame, run, blink, polyline, present  # noqa: E402
import trm_chiller as CH  # noqa: E402

SLUG = "TRM_BUSWAY"
BEATS = [
    ("Busway carries power overhead from switchgear to the racks",
     "Instead of pulling separate cables from the switchgear to every rack, many data halls hang a busway above each row: "
     "a factory-built run of copper or aluminium bars inside a steel housing. Sections bolt together into one long "
     "trunk, rated from a few hundred to several thousand amps."),
    ("Inside: flat copper bars, insulated and packed tight",
     "Cut a section open and there are flat bars for the three phases (L1, L2, L3) and neutral, each wrapped in "
     "insulation and stacked close together. Tight spacing keeps impedance and voltage drop low and the housing doubles "
     "as the ground path. A 400 V, 800 A run can feed a row of racks over 500 kW."),
    ("Tap-off boxes plug into the run and feed each rack",
     "Openings along the housing accept plug-in tap-off units. Spring stabs inside the tap grip the bars, a breaker or "
     "fuses in the box protect the drop, and a short cord runs to the rack's PDU. Many taps include metering, so "
     "operators see each rack's draw."),
    ("Add or move a rack: clip on a tap, no new cable",
     "When a new rack arrives, an electrician plugs a tap into the next free opening, often while the busway stays "
     "energised. No conduit, no cable pull back to the switchgear, minutes instead of days. That flexibility matters "
     "as AI racks jump from 15 kW to 100 kW+ and layouts change every hardware generation."),
    ("Higher rack power pushes busway into more halls",
     "Dense AI rows need hundreds of amps per row, which is bulky to do with cable. Busway suppliers include Eaton (ETN), "
     "Schneider Electric (SU.PA), Siemens (SIE.DE), nVent (NVT), plus Legrand (Starline) and Vertiv. It is sold with "
     "the switchgear and PDUs on either end."),
]

BY = 290.0  # busway centre height
BZ = -60.0  # busway z (above the rack fronts)
RX = [-150.0, -84.0, -18.0, 48.0, 114.0]  # rack x0s (the last one is the new rack)
SX0, SX1 = 330.0, 520.0  # giant section x range
GY, GZ = 150.0, -40.0  # giant section centre (y, z)
GS = 4.0  # scale of the giant section


def mats(m):
    CH.mats(m)
    m["house"] = mat("bw_house", (0.55, 0.58, 0.62), metal=0.7, rough=0.35)
    m["ins"] = mat("bw_ins", (0.25, 0.25, 0.28), rough=0.6)
    m["tapbox"] = mat("bw_tap", (0.80, 0.80, 0.78), metal=0.3, rough=0.45)
    m["gear"] = mat("bw_gear", (0.70, 0.72, 0.74), metal=0.4, rough=0.45)
    m["cord"] = mat("bw_cord", (0.08, 0.08, 0.09), rough=0.7)
    m["l1"] = mat("bw_l1", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=3.5)
    m["l2"] = mat("bw_l2", (0.30, 0.65, 1.0), emit=(0.25, 0.62, 1.0), strength=3.5)
    m["l3"] = mat("bw_l3", (0.85, 0.45, 1.0), emit=(0.85, 0.45, 1.0), strength=3.5)


def switchgear(m, root):
    g = empty("sg", root)
    x0, x1 = -340.0, -200.0
    bx("sg_back", (x0, 0.0, -110.0), (x1, 230.0, -100.0), m["gear"], g)
    for k in range(4):
        xa = x0 + 35.0 * k
        bx(f"sg_side{k}", (xa, 0.0, -100.0), (xa + 2.0, 230.0, -10.0), m["gear"], g)
        for j in range(3):
            y = 20.0 + 65.0 * j
            bx(f"sg_br{k}{j}", (xa + 6.0, y, -60.0), (xa + 30.0, y + 45.0, -20.0), m["frame"], g)
            bx(f"sg_h{k}{j}", (xa + 14.0, y + 18.0, -20.0), (xa + 22.0, y + 26.0, -16.0), m["white"], g)
    bx("sg_top", (x0, 230.0, -110.0), (x1, 236.0, -10.0), m["gear"], g)
    # vertical bus bars at the back of the lineup
    for k, mt in enumerate(("copper", "copper", "copper")):
        bx(f"sg_vb{k}", (x0 + 4.0, 10.0, -96.0 + 8.0 * k), (x1 - 4.0, 14.0, -92.0 + 8.0 * k), m[mt], g)
    leds = empty("sg_leds", root)
    for k in range(4):
        bx(f"sg_led{k}", (x0 + 10.0 + 35.0 * k, 215.0, -10.0), (x0 + 16.0 + 35.0 * k, 219.0, -9.0), m["led"], leds)
    return leds


def trunk(m, root):
    g = empty("trunk", root)
    xa, xb = -270.0, 200.0
    polyline("bw_riser", [(-270.0, 236.0, BZ), (-270.0, BY, BZ), (xa, BY, BZ)], 1.0, m["house"], g)
    bx("bw_riser_box", (-282.0, 236.0, BZ - 10.0), (-258.0, BY + 8.0, BZ + 10.0), m["house"], g)
    bx("bw_run", (xa, BY - 8.0, BZ - 10.0), (xb, BY + 8.0, BZ + 10.0), m["house"], g)
    for k in range(9):  # section joints and hangers
        x = xa + 15.0 + 55.0 * k
        bx(f"bw_j{k}", (x - 2.0, BY - 9.0, BZ - 11.0), (x + 2.0, BY + 9.0, BZ + 11.0), m["frame"], g)
        tube(f"bw_hang{k}", (x, BY + 8.0, BZ), (x, 360.0, BZ), 0.8, m["steel"], g, 6)
    for k in range(5):  # plug-in openings
        x = RX[k] + 30.0
        bx(f"bw_open{k}", (x - 6.0, BY - 9.0, BZ + 6.0), (x + 6.0, BY - 8.6, BZ + 10.6), m["dark"], g)
    bx("bw_ceiling", (-360.0, 360.0, -200.0), (220.0, 364.0, 0.0), m["wall"], g)
    return g


def tap(m, root, name, x):
    g = empty(name, root)
    bx(f"{name}_box", (x - 10.0, BY - 34.0, BZ - 8.0), (x + 10.0, BY - 9.0, BZ + 12.0), m["tapbox"], g)
    bx(f"{name}_hdl", (x - 3.0, BY - 30.0, BZ + 12.0), (x + 3.0, BY - 22.0, BZ + 15.0), m["warn"], g)
    polyline(f"{name}_cord", [(x, BY - 34.0, BZ + 2.0), (x, 222.0, BZ + 2.0), (x - 26.0, 214.0, BZ + 20.0)], 1.4, m["cord"], g)
    return g


def giant(m, root):
    """The cut-open section, axis along x, scaled GS."""
    g = empty("giant", root)
    h, w = 8.0 * GS, 10.0 * GS
    y0, y1, z0, z1 = GY - h, GY + h, GZ - w, GZ + w
    bx("g_back", (SX0, y0, z0), (SX1, y1, z0 + 2.0), m["house"], g)
    bx("g_top", (SX0, y1 - 2.0, z0), (SX1, y1, z1), m["house"], g)
    bx("g_bot", (SX0, y0, z0), (SX1, y0 + 2.0, z1), m["house"], g)
    for k in range(6):  # housing ribs
        x = SX0 + 10.0 + 34.0 * k
        bx(f"g_rib{k}", (x, y1, z0), (x + 3.0, y1 + 3.0, z1), m["frame"], g)
    names = ("l1", "l2", "l3", "n")
    glow = {}
    ys = []
    for k, nm in enumerate(names):
        yc = y0 + 10.0 + (h * 2 - 20.0) * (k + 0.5) / 4
        ys.append(yc)
        bx(f"g_ins{k}", (SX0, yc - 4.6, z0 + 6.0), (SX1, yc + 4.6, z1 - 2.0), m["ins"], g)
        bx(f"g_bar{k}", (SX0 - 6.0, yc - 3.0, z0 + 7.0), (SX1 + 6.0, yc + 3.0, z1 - 0.5), m["copper"], g)
        if nm != "n":
            gl = empty(f"g_glow{nm}", root)
            bx(f"g_gl{k}", (SX0 + 4.0, yc - 1.0, z1 - 0.5), (SX1 - 4.0, yc + 1.0, z1 + 0.2), m[nm], gl)
            show(gl, [])
            glow[nm] = gl
    # a tap at the middle with stabs reaching the bars
    xm = (SX0 + SX1) / 2
    tg = empty("g_tap", root)
    bx("g_tapbox", (xm - 30.0, y0 - 70.0, z0 + 6.0), (xm + 30.0, y0 - 4.0, z1 - 10.0), m["tapbox"], tg)
    bx("g_brk", (xm - 12.0, y0 - 55.0, z1 - 10.0), (xm + 12.0, y0 - 25.0, z1 - 6.0), m["frame"], tg)
    for k, yc in enumerate(ys):
        bx(f"g_stab{k}", (xm - 10.0 + 6.0 * k, y0 - 4.0, z1 - 14.0), (xm - 7.0 + 6.0 * k, yc - 3.0, z1 - 11.0), m["tin"], tg)
        bx(f"g_jaw{k}", (xm - 12.0 + 6.0 * k, yc - 5.0, z1 - 16.0), (xm - 5.0 + 6.0 * k, yc - 3.0, z1 - 9.0), m["tin"], tg)
    return glow, ys, (xm, y0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-360.0, -6.0, -200.0), (240.0, 0.0, 20.0), m["concrete"], root)
    sg_leds = switchgear(m, root)
    trunk(m, root)
    rleds = []
    for k, x0 in enumerate(RX):
        le = empty(f"rleds{k}", root)
        rk = CH.rack(m, root, f"rk{k}", x0, -170.0, leds=le)
        rleds.append(le)
        if k == 4:
            present(rk, [(F(3, 0.15), F(9, 0))])
    taps = [tap(m, root, f"tap{k}", RX[k] + 30.0) for k in range(5)]
    # the new rack's tap clips up onto the busway in beat 3
    present(taps[4], [(F(3, 0.3), F(9, 0))])
    key(taps[4], F(3, 0.3), "location", C.P(0.0, -40.0, 0.0))
    key(taps[4], F(3, 0.55), "location", C.P(0.0, 0.0, 0.0))
    present(rleds[4], [(F(3, 0.6), F(9, 0))])
    for k in range(4):
        for b in range(5):
            blink(rleds[k], b, [0, 2, 4, 6], n=8, on=0.7)
        blink(sg_leds, k, [1, 3, 5, 7], n=8, on=0.6)
    for b in (3, 4):
        blink(rleds[4], b, [5, 7] if b == 3 else [0, 2, 4, 6], n=8, on=0.7)
    D.polyline("mag_l", [(150.0, BY, BZ), (SX0 - 8.0, GY + 30.0, GZ)], 0.4, m["field"], root)
    glow, ys, (xm, gy0) = giant(m, root)

    for nm in ("l1", "l2", "l3"):
        show(glow[nm], [(F(1, 0.3), F(5, 0))])
    for k, nm in enumerate(("l1", "l2", "l3")):
        run(root, f"g_i{nm}", [(SX0 - 4.0, ys[k], GZ + 42.0), (SX1 + 4.0, ys[k], GZ + 42.0)], 6, 2.2, m[nm], [2], 0.0, 0.7, 50)
        run(root, f"g_s{nm}", [(xm - 8.5 + 6.0 * k, ys[k], GZ + 30.0), (xm - 8.5 + 6.0 * k, gy0 - 30.0, GZ + 30.0)], 3, 1.8, m[nm], [2, 3], 0.2, 0.8, 30)
    # current along the trunk and down taps
    main = [(-270.0, 236.0, BZ + 12.0), (-270.0, BY, BZ + 12.0), (190.0, BY, BZ + 12.0)]
    run(root, "i_main", main, 14, 3.0, m["l1"], [0, 2, 3, 4], 0.0, 0.7, 70)
    for k in range(5):
        x = RX[k] + 30.0
        drop = [(x, BY - 12.0, BZ + 14.0), (x, 222.0, BZ + 4.0), (x - 26.0, 214.0, BZ + 22.0)]
        run(root, f"i_drop{k}", drop, 4, 2.4, m["l2"], [2] if k < 4 else [3, 4], 0.3 if k < 4 else 0.6, 0.9, 25)
        if k < 4:
            run(root, f"i_dropb{k}", drop, 4, 2.4, m["l2"], [4], 0.0, 0.8, 25)

    tags = {
        0: [("switchgear lineup", (-270.0, 240.0, -10.0)), ("overhead busway trunk", (0.0, BY + 10.0, BZ)),
            ("plug-in tap boxes", (RX[1] + 30.0, BY - 34.0, BZ + 12.0)), ("rack row", (RX[2] + 30.0, 210.0, -60.0))],
        1: [("steel housing = ground", (xm, GY + 34.0, GZ)), ("L1 L2 L3 + N copper bars", (SX1, ys[1], GZ + 40.0)),
            ("insulation between bars", (SX0 + 20.0, ys[2], GZ + 38.0))],
        2: [("stabs grip each bar", (xm, gy0 - 4.0, GZ + 30.0)), ("breaker in the tap", (xm, gy0 - 40.0, GZ + 34.0)),
            ("cord down to rack PDU", (RX[3] + 10.0, 220.0, BZ + 10.0))],
        3: [("new rack arrives", (RX[4] + 30.0, 212.0, -60.0)), ("tap clips on, live bus", (RX[4] + 30.0, BY - 20.0, BZ + 12.0)),
            ("no cable pull", (RX[4] - 20.0, BY + 20.0, BZ))],
        4: [("Eaton, Schneider, Siemens", (0.0, BY + 10.0, BZ)), ("nVent, Legrand, Vertiv", (xm, GY + 34.0, GZ))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-80.0, 160.0, -90.0), 520.0, 0.25, 0.22, pad=1.0),
        frame((xm, GY - 10.0, GZ), 200.0, 0.30, 0.20),
        [(0.0, frame((xm, GY - 30.0, GZ), 220.0, 0.15, 0.10)), (0.5, frame((0.0, 220.0, -80.0), 360.0, 0.20, 0.25))],
        frame((RX[4] + 10.0, 200.0, -80.0), 220.0, 0.35, 0.20),
        frame((60.0, 160.0, -80.0), 760.0, -0.20, 0.25, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
