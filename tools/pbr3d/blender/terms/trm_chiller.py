"""TRM_CHILLER: an air-cooled chiller beside a data hall, cut open, at the POWER pages' detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_chiller.py

No GPU board here: a chiller is plant equipment. Units are centimetres. The hall (left, front wall
cut away at z = 0) holds two rack rows and an air handler whose coil takes chilled water. The chiller
(right, side skin cut away at z = 0) shows the shell-and-tube evaporator, the screw compressor and
motor, the expansion valve, the V-bank condenser coils and four fans on top, plus a free-cooling
coil. Water: blue = chilled supply, amber = warm return. Refrigerant: cyan = cold liquid/vapour,
red = hot compressed gas.

Beats:
  0 site      hall + chiller, chilled water out, warm water back
  1 loop      the refrigeration loop inside the chiller
  2 reject    the condenser fans spin, heat rises off the coils
  3 free      warm-water liquid cooling: compressor stops, free-cooling coil does the work
  4 market    wide view, who sells them
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat, tube  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, polyline  # noqa: E402

SLUG = "TRM_CHILLER"
BEATS = [
    ("A chiller makes the cold water the data hall runs on",
     "A chiller is a refrigeration machine the size of a shipping container. It cools a loop of water, typically to "
     "somewhere between 7 and 18 C, and pumps it into the building, where coils in air handlers or liquid-cooling "
     "units pick up the servers' heat. The water comes back warmer and the chiller cools it again."),
    ("Inside, a refrigerant loop pumps heat uphill",
     "The returning water flows through tubes in the evaporator, where low-pressure refrigerant boils and soaks up its "
     "heat. A screw or centrifugal compressor squeezes that vapour hot and dense, the condenser sheds the heat outdoors, "
     "and an expansion valve drops the pressure so the liquid can boil again. Each kW of compressor power moves about "
     "3 to 6 kW of heat."),
    ("Fans on top throw the heat into the outside air",
     "In an air-cooled chiller the condenser is a set of finned coils in a V, with large fans pulling outdoor air "
     "through them. Bigger plants use water-cooled chillers that send condenser water to cooling towers instead, "
     "trading water use for efficiency. A single large unit handles 1 to 2 MW of heat (300 to 600 tons)."),
    ("Warm-water liquid cooling lets the compressor rest",
     "Direct-to-chip liquid cooling runs facility water at 30 C or more. Outdoor air is cooler than that most of the "
     "year, so water can bypass the compressor through a free-cooling coil and the fans alone do the work. Fewer "
     "compressor hours means a lower PUE, but sites still size chillers for the hottest days."),
    ("AI campuses still buy chillers by the dozen",
     "A gigawatt-class campus can need hundreds of megawatts of heat rejection, and chillers, dry coolers and their "
     "controls are a big line in the cooling budget. Makers: Trane Technologies (TT), Carrier (CARR), Johnson Controls "
     "(JCI, York), Daikin, and Vertiv (VRT), which sells chillers alongside CDUs and power gear."),
]

# layout (cm)
HX0, HX1, HZ0 = -320.0, -60.0, -260.0  # hall
CX0, CX1, CZ0 = 30.0, 330.0, -120.0  # chiller footprint (front face cut at z = 0)
CY1 = 130.0  # chiller deck height (fans above)
EV = (60.0, 200.0, 32.0, -62.0, 20.0)  # evaporator x0, x1, y centre, z centre, radius
CMP = (225.0, 300.0, 32.0, -62.0)  # compressor x0, x1, y, z


def mats(m):
    m["skin"] = mat("ch_skin", (0.80, 0.82, 0.84), metal=0.5, rough=0.4)
    m["frame"] = mat("ch_frame", (0.18, 0.19, 0.22), metal=0.6, rough=0.45)
    m["shell"] = mat("ch_shell", (0.25, 0.42, 0.62), metal=0.4, rough=0.4)
    m["pipe_s"] = mat("ch_pipe_s", (0.20, 0.38, 0.70), metal=0.5, rough=0.35)
    m["pipe_r"] = mat("ch_pipe_r", (0.62, 0.34, 0.20), metal=0.5, rough=0.35)
    m["fin"] = mat("ch_fin", (0.72, 0.74, 0.78), metal=0.85, rough=0.3)
    m["concrete"] = mat("ch_conc", (0.48, 0.48, 0.47), rough=0.9)
    m["wall"] = mat("ch_wall", (0.62, 0.62, 0.60), rough=0.85)
    m["rack"] = mat("ch_rack", (0.08, 0.08, 0.10), metal=0.4, rough=0.5)
    m["tray"] = mat("ch_tray", (0.30, 0.31, 0.35), metal=0.6, rough=0.4)
    m["motor"] = mat("ch_motor", (0.15, 0.30, 0.22), metal=0.4, rough=0.45)
    m["c_supply"] = mat("ch_g_sup", (0.30, 0.65, 1.0), emit=(0.25, 0.62, 1.0), strength=4.0)
    m["c_return"] = mat("ch_g_ret", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=4.0)
    m["r_cold"] = mat("ch_g_rc", (0.40, 0.95, 1.0), emit=(0.35, 0.95, 1.0), strength=4.0)
    m["r_hot"] = mat("ch_g_rh", (1.0, 0.30, 0.18), emit=(1.0, 0.25, 0.12), strength=4.0)
    m["led"] = mat("ch_led", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)
    m["coil_hot"] = mat("ch_coil_hot", (0.9, 0.4, 0.2), emit=(1.0, 0.35, 0.12), strength=1.6)
    m["coil_free"] = mat("ch_coil_free", (0.3, 0.6, 1.0), emit=(0.25, 0.6, 1.0), strength=1.6)


def rack(m, parent, name, x0, z0, w=60.0, dep=110.0, h=210.0, leds=None):
    g = empty(name, parent)
    x1, z1 = x0 + w, z0 + dep
    for px in (x0, x1 - 4.0):
        for pz in (z0, z1 - 4.0):
            bx(f"{name}_p{px:.0f}{pz:.0f}", (px, 0.0, pz), (px + 4.0, h, pz + 4.0), m["rack"], g)
    bx(f"{name}_top", (x0, h - 4.0, z0), (x1, h, z1), m["rack"], g)
    trays = []
    for k in range(18):
        y = 10.0 + k * 10.8
        trays.append(bx(f"{name}_t{k}", (x0 + 4.0, y, z0 + 4.0), (x1 - 4.0, y + 8.6, z1 - 4.0), m["tray"], g))
    D.join(trays, f"{name}_trays")
    if leds is not None:
        for k in range(0, 18, 2):
            y = 14.0 + k * 10.8
            bx(f"{name}_l{k}", (x0 + 8.0, y, z1 - 3.6), (x0 + 12.0, y + 1.5, z1 - 3.4), m["led"], leds)
    return g


def hall(m, root):
    g = empty("hall", root)
    bx("h_floor", (HX0, -6.0, HZ0), (HX1, 0.0, 0.0), m["concrete"], g)
    bx("h_back", (HX0, 0.0, HZ0), (HX1, 260.0, HZ0 + 8.0), m["wall"], g)
    bx("h_left", (HX0, 0.0, HZ0), (HX0 + 8.0, 260.0, 0.0), m["wall"], g)
    bx("h_right", (HX1 - 8.0, 0.0, HZ0), (HX1, 120.0, 0.0), m["wall"], g)
    leds = empty("h_leds", root)
    for row, z0 in enumerate((-230.0, -110.0)):
        for k in range(3):
            rack(m, g, f"rk{row}{k}", -300.0 + 66.0 * k, z0, leds=leds)
    # air handler (CRAH) against the right wall: cabinet, coil, fan
    bx("ahu", (-110.0, 0.0, -230.0), (-70.0, 220.0, -40.0), m["skin"], g)
    coil = []
    for k in range(20):
        y = 30.0 + k * 8.0
        coil.append(bx(f"ahu_c{k}", (-112.0, y, -220.0), (-110.0, y + 1.0, -50.0), m["fin"], g))
    D.join(coil, "ahu_coil")
    return leds


def fan(m, root, name, c, r=24.0):
    """A condenser fan: shroud ring on the deck and a 5-blade rotor whose group sits at the hub."""
    x, y, z = c
    ring = []
    for j in range(24):
        a0, a1 = 2 * math.pi * j / 24, 2 * math.pi * (j + 1) / 24
        ring.append(tube(f"{name}_s{j}", (x + r * math.cos(a0), y + 6.0, z + r * math.sin(a0)),
                         (x + r * math.cos(a1), y + 6.0, z + r * math.sin(a1)), 2.4, m["frame"], root, 6))
    D.join(ring, f"{name}_shroud")
    hub = empty(f"{name}_rot", root, C.P(*c))
    tube(f"{name}_hub", (0.0, 0.0, 0.0), (0.0, 6.0, 0.0), 4.0, m["frame"], hub, 12)
    bl = []
    for k in range(5):
        a = 2 * math.pi * k / 5
        ca, sa = math.cos(a), math.sin(a)
        bl.append(tube(f"{name}_b{k}", (3.0 * ca, 3.0, 3.0 * sa), ((r - 3.0) * ca, 3.5, (r - 3.0) * sa), 3.0, m["skin"], hub, 4))
    D.join(bl, f"{name}_blades")
    return hub


def chiller(m, root):
    g = empty("chiller", root)
    bx("c_pad", (CX0 - 20.0, -6.0, CZ0 - 20.0), (CX1 + 20.0, 0.0, 10.0), m["concrete"], g)
    bx("c_base", (CX0, 0.0, CZ0), (CX1, 6.0, 0.0), m["frame"], g)
    bx("c_back", (CX0, 6.0, CZ0), (CX1, CY1, CZ0 + 3.0), m["skin"], g)
    bx("c_endl", (CX0, 6.0, CZ0), (CX0 + 3.0, 60.0, 0.0), m["skin"], g)
    bx("c_endr", (CX1 - 3.0, 6.0, CZ0), (CX1, 60.0, 0.0), m["skin"], g)
    for x in (CX0, CX0 + 100.0, CX0 + 200.0, CX1 - 4.0):
        bx(f"c_post{x:.0f}", (x, 6.0, -4.0), (x + 4.0, CY1, 0.0), m["frame"], g)
    bx("c_deck", (CX0, CY1 - 3.0, CZ0), (CX1, CY1, 0.0), m["frame"], g)
    # evaporator: shell with tube sheet ends, a cutaway window showing the tube bundle
    x0, x1, ey, ez, er = EV
    bx("ev_saddle0", (x0 + 10.0, 6.0, ez - 16.0), (x0 + 20.0, ey - 10.0, ez + 16.0), m["frame"], g)
    bx("ev_saddle1", (x1 - 20.0, 6.0, ez - 16.0), (x1 - 10.0, ey - 10.0, ez + 16.0), m["frame"], g)
    shell = []
    for j in range(20):  # half shell (back half), so the bundle shows from the front
        a0, a1 = math.pi * j / 20, math.pi * (j + 1) / 20
        y0, z0_ = ey + er * math.cos(a0), ez - er * math.sin(a0)
        y1, z1_ = ey + er * math.cos(a1), ez - er * math.sin(a1)
        shell.append(bx(f"ev_sh{j}", (x0, min(y0, y1), min(z0_, z1_) - 0.8), (x1, max(y0, y1) + 0.8, max(z0_, z1_)), m["shell"], g))
    D.join(shell, "ev_shell")
    for xe in (x0 - 6.0, x1):
        tube(f"ev_head{xe:.0f}", (xe, ey, ez), (xe + 6.0, ey, ez), er + 2.0, m["shell"], g, 24)
    bundle = []
    for i in range(4):
        for j in range(4):
            yy, zz = ey - 12.0 + 8.0 * i, ez - 12.0 + 8.0 * j
            bundle.append(tube(f"ev_t{i}{j}", (x0, yy, zz), (x1, yy, zz), 1.6, m["copper"], g, 8))
    D.join(bundle, "ev_bundle")
    # compressor: screw housing (cut open, two rotors with helix lobes) and motor
    cx0, cx1, cy, cz = CMP
    bx("cmp_house", (cx0, cy - 16.0, cz - 16.0), (cx0 + 45.0, cy + 16.0, cz - 2.0), m["steel"], g)
    rot = []
    for k, dz in enumerate((-8.0, 4.0)):
        rot.append(tube(f"cmp_r{k}", (cx0 + 2.0, cy, cz + dz), (cx0 + 43.0, cy, cz + dz), 5.5, m["alu"], g, 12))
        for s in range(10):
            xs = cx0 + 4.0 + 4.0 * s
            a = s * 0.8 + k * 1.5
            rot.append(tube(f"cmp_l{k}{s}", (xs, cy + 6.5 * math.cos(a), cz + dz + 6.5 * math.sin(a)),
                            (xs + 3.0, cy + 6.5 * math.cos(a + 0.6), cz + dz + 6.5 * math.sin(a + 0.6)), 1.4, m["alu"], g, 6))
    D.join(rot, "cmp_rotors")
    tube("cmp_motor", (cx0 + 45.0, cy, cz), (cx1, cy, cz), 15.0, m["motor"], g, 24)
    for s in range(8):
        xs = cx0 + 50.0 + 3.0 * s
        tube(f"cmp_rib{s}", (xs, cy, cz), (xs + 1.0, cy, cz), 16.0, m["motor"], g, 24)
    bx("cmp_feet", (cx0, 6.0, cz - 14.0), (cx1, cy - 14.0, cz + 14.0), m["frame"], g)
    # V-bank condenser coils under the deck, slanted fins drawn as stacked strips
    coils = []
    for side, zc in ((-1, -95.0), (1, -25.0)):
        for k in range(14):
            t = k / 13.0
            y = 70.0 + 55.0 * t
            z = zc + side * (-12.0 + 12.0 * t) * -1
            coils.append(bx(f"cd_{side}{k}", (CX0 + 6.0, y, z - 1.5), (CX1 - 6.0, y + 2.2, z + 1.5), m["fin"], g))
    D.join(coils, "cd_coils")
    hot = empty("cd_hot", root)
    for side, zc in ((-1, -95.0), (1, -25.0)):
        for k in range(0, 14, 3):
            t = k / 13.0
            y = 70.0 + 55.0 * t
            z = zc + side * (-12.0 + 12.0 * t) * -1
            tube(f"cdh_{side}{k}", (CX0 + 8.0, y + 1.1, z + 1.6), (CX1 - 8.0, y + 1.1, z + 1.6), 0.9, m["coil_hot"], hot, 8)
    # free-cooling coil: a slim coil on the back skin with its own glow
    free = empty("fc_glow", root)
    fc = []
    for k in range(8):
        y = 72.0 + 6.0 * k
        fc.append(bx(f"fc_{k}", (CX0 + 10.0, y, CZ0 + 4.0), (CX1 - 10.0, y + 2.0, CZ0 + 7.0), m["copper"], g))
        tube(f"fcg_{k}", (CX0 + 12.0, y + 1.0, CZ0 + 7.5), (CX1 - 12.0, y + 1.0, CZ0 + 7.5), 0.9, m["coil_free"], free, 8)
    D.join(fc, "fc_coil")
    # expansion valve and refrigerant piping
    bx("xv", (205.0, 50.0, -40.0), (215.0, 62.0, -30.0), m["brass"] if "brass" in m else m["gold"], g)
    suction = [(x1 + 6.0, ey + 6.0, ez), (215.0, ey + 6.0, ez), (215.0, cy, ez), (cx0 + 2.0, cy, cz)]
    discharge = [(cx1 - 30.0, cy + 16.0, cz), (cx1 - 30.0, 66.0, cz), (cx1 - 30.0, 70.0, -60.0), (CX0 + 20.0, 70.0, -60.0)]
    liquid = [(CX0 + 20.0, 70.0, -60.0), (CX0 + 20.0, 56.0, -35.0), (210.0, 56.0, -35.0), (210.0, 50.0, -35.0),
              (210.0, ey + er, ez + 4.0), (x1 - 10.0, ey + er - 2.0, ez + 4.0)]
    for n, pts, r in (("suc", suction, 3.0), ("dis", discharge, 2.4), ("liq", liquid, 1.6)):
        polyline(f"rp_{n}", pts, r, m["copper"], g)
    # chilled water: supply leaves the evaporator head, runs to the hall's air handler; return comes back
    sup = [(x0 - 6.0, ey + 8.0, ez), (CX0 - 10.0, ey + 8.0, ez), (CX0 - 10.0, 12.0, -150.0), (HX1 + 10.0, 12.0, -150.0),
           (-90.0, 12.0, -150.0), (-90.0, 60.0, -150.0), (-110.0, 60.0, -150.0)]
    ret = [(-110.0, 170.0, -120.0), (-90.0, 170.0, -120.0), (-90.0, 24.0, -120.0), (CX0 - 20.0, 24.0, -120.0),
           (CX0 - 20.0, ey - 8.0, ez), (x0 - 6.0, ey - 8.0, ez)]
    polyline("cw_sup", sup, 4.0, m["pipe_s"], g)
    polyline("cw_ret", ret, 4.0, m["pipe_r"], g)
    for o in (hot, free):
        show(o, [])
    return {"sup": sup, "ret": ret, "suc": suction, "dis": discharge, "liq": liquid, "hot": hot, "free": free}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    leds = hall(m, root)
    p = chiller(m, root)
    fans = [fan(m, root, f"fan{k}", (CX0 + 40.0 + 73.0 * k, CY1, -60.0)) for k in range(4)]
    for k in range(4):
        blink(leds, k, [0, 2, 4, 6], n=8, on=0.7)

    # water flows every beat; free-cooling path in beat 3
    run(root, "w_sup", p["sup"], 14, 5.5, m["c_supply"], [0, 1, 2, 3, 4], 0.0, 0.7, 70)
    run(root, "w_ret", p["ret"], 14, 5.5, m["c_return"], [0, 1, 2, 3, 4], 0.0, 0.7, 70)
    # refrigerant loop beats 1, 2 (compressor running)
    run(root, "r_suc", p["suc"], 6, 3.6, m["r_cold"], [1, 2], 0.05, 0.6, 40)
    run(root, "r_dis", p["dis"], 7, 3.4, m["r_hot"], [1, 2], 0.1, 0.65, 45)
    run(root, "r_liq", p["liq"], 7, 3.0, m["r_cold"], [1, 2], 0.15, 0.7, 50)
    show(p["hot"], [(F(1, 0.3), F(3, 0))])
    rise(root, "cmp_heat", (CMP[0] + 20.0, CMP[2] + 18.0, CMP[3] + 6.0), 5, 1.6, m["heat"], 1, 0.2, 0.8, 20.0, 40, (10.0, 4.0))
    # fans spin beats 0-4, heat plumes over them in beats 2 and 3
    for f_ in fans:
        C.spin(f_, [0, 1, 2, 3, 4], turns=3.0)
    for k in range(4):
        rise(root, f"plume{k}", (CX0 + 40.0 + 73.0 * k, CY1 + 10.0, -60.0), 8, 3.6, m["heat"], [2], 0.0, 0.85, 90.0, 50, (14.0, 14.0))
        rise(root, f"plumef{k}", (CX0 + 40.0 + 73.0 * k, CY1 + 10.0, -60.0), 4, 3.0, m["heat"], [3], 0.2, 0.85, 40.0, 50, (14.0, 14.0))
    show(p["free"], [(F(3, 0.15), F(4, 0))])
    fcp = [(CX0 - 10.0, EV[2] - 8.0, EV[3]), (CX0 + 12.0, 74.0, CZ0 + 9.0), (CX1 - 12.0, 86.0, CZ0 + 9.0),
           (CX1 - 12.0, 100.0, CZ0 + 9.0), (CX0 + 12.0, 112.0, CZ0 + 9.0)]
    run(root, "w_free", fcp, 9, 4.0, m["c_supply"], [3], 0.15, 0.8, 50)

    tags = {
        0: [("data hall: racks + air handler", (-200.0, 215.0, -110.0)), ("air-cooled chiller", (180.0, CY1 + 30.0, -60.0)),
            ("chilled water out ~7-18 C", (-20.0, 12.0, -150.0)), ("warm water back", (-20.0, 24.0, -120.0))],
        1: [("evaporator: refrigerant boils", (EV[0] + 40.0, EV[2] + EV[4], 0.0)), ("screw compressor", (CMP[0] + 20.0, CMP[2] + 18.0, -50.0)),
            ("condenser coils: hot gas", (120.0, 100.0, -25.0)), ("expansion valve", (210.0, 62.0, -35.0))],
        2: [("fans pull outside air through", (CX0 + 113.0, CY1 + 20.0, -60.0)), ("heat dumped outdoors", (CX0 + 186.0, CY1 + 60.0, -60.0)),
            ("1-2 MW per big unit", (CX1, 60.0, 0.0))],
        3: [("free-cooling coil", (CX0 + 140.0, 100.0, CZ0 + 9.0)), ("compressor off", (CMP[0] + 20.0, CMP[2] + 18.0, -50.0)),
            ("30 C+ water: fans alone", (CX0 + 113.0, CY1 + 20.0, -60.0))],
        4: [("Trane, Carrier, JCI, Daikin", (180.0, CY1 + 30.0, -60.0)), ("Vertiv: whole thermal chain", (-90.0, 225.0, -130.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 60.0, -120.0), 680.0, 0.25, 0.40, pad=1.0),
        frame((190.0, 50.0, -50.0), 260.0, 0.12, 0.18),
        [(0.0, frame((180.0, 110.0, -60.0), 340.0, 0.35, 0.55)), (0.55, frame((180.0, 140.0, -60.0), 320.0, -0.2, 0.75))],
        frame((180.0, 90.0, -80.0), 330.0, 0.45, 0.40),
        frame((0.0, 60.0, -120.0), 720.0, -0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
