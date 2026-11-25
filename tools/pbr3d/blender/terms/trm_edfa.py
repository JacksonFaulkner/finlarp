"""TRM_EDFA: the Terms-tab overview for the erbium-doped fibre amplifier.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_edfa.py

Writes assets/term_TRM_EDFA.glb. Captions live in specs/terms/TRM_EDFA.json.

Beats:
  0 route     a long-haul fibre route: terminals, 80 km spans, amplifier huts
  1 fade      eight DWDM colours enter the amplifier faint after a span
  2 pump      a 980 nm pump laser joins through a WDM coupler and lights the erbium coil
  3 gain      the excited erbium copies the passing photons: all eight colours leave bright
  4 chain     gain-flattening filter, isolators, and an amp every 60-100 km; tickers
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, mat, show  # noqa: E402
from power_vrm_detail import bx, frame, polyline, rise, run  # noqa: E402

import term_common as C  # noqa: E402
import kit_photonics as K  # noqa: E402

SLUG = "TRM_EDFA"
BEATS = [
    ("Long fibre routes need a boost every 60-100 km",
     "Light in glass fibre loses about 0.2 dB per km, so after an 80 km span only about a fiftieth of the power is "
     "left. A long-haul route is a chain of spans with an amplifier hut at each joint. The erbium-doped fibre "
     "amplifier (EDFA) is the box in those huts, and it amplifies without ever turning the light into electricity."),
    ("Dozens of faint colours arrive together",
     "A DWDM fibre carries many wavelengths in the C-band, around 1530-1565 nm, each one a separate channel. After a "
     "span every channel is weak. Converting each one to electrical form, regenerating it and re-transmitting it would "
     "need a full transceiver per colour; the EDFA avoids all of that."),
    ("A pump laser energises erbium ions in a coil of special fibre",
     "Inside the box sits 5-30 m of fibre whose core is doped with erbium. A 980 nm (or 1480 nm) pump laser is "
     "merged into that fibre by a WDM coupler. The pump light lifts the erbium ions into an excited state, storing "
     "energy along the coil."),
    ("Signal photons trigger the ions to add identical photons",
     "When a signal photon passes an excited ion, the ion drops back and emits a second photon with the same "
     "wavelength, phase and direction (stimulated emission). Every colour in the C-band is copied this way at once, "
     "for 20-30 dB of gain. One amplifier serves all the channels, which is what made DWDM long-haul affordable."),
    ("Filters and isolators tidy the output; amps repeat down the route",
     "Erbium gain is uneven across colours, so a gain-flattening filter evens the channels out, and optical isolators "
     "stop reflections from turning the coil into a laser. Each amp adds a little noise, which limits how many can be "
     "chained before a full regeneration. Lumentum (LITE), Coherent (COHR) and Ciena (CIEN) build them; ROADM nodes "
     "contain them too."),
]

LINE_Y = 8.0
X_IN, X_CPL, X_C0, X_C1, X_GFF, X_OUT = -70.0, -40.0, -22.0, 22.0, 42.0, 70.0
COIL_C = (0.0, LINE_Y, 6.0)
ROUTE_Z = -90.0


def coil_pts(turns=5, r0=7.0, r1=15.0, n=220):
    """A flat spiral of erbium fibre in the x-z plane, entering at the left and leaving at the right."""
    pts = []
    for i in range(n + 1):
        u = i / n
        a = math.pi + 2 * math.pi * turns * u
        r = r0 + (r1 - r0) * u
        pts.append((COIL_C[0] + r * math.cos(a), LINE_Y + 0.2 * math.sin(9 * a), COIL_C[2] + r * math.sin(a)))
    return pts


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    m["er"] = mat("edfa_er", (0.85, 0.45, 0.55), rough=0.2)
    m["er_glow"] = mat("edfa_erg", (1.0, 0.45, 0.65), emit=(1.0, 0.35, 0.6), strength=1.1)
    m["pump"] = mat("edfa_pump", (1.0, 0.2, 0.2), emit=(1.0, 0.15, 0.12), strength=4.0)
    m["hut"] = mat("edfa_hut", (0.62, 0.60, 0.55), rough=0.7)
    m["ground"] = mat("edfa_ground", (0.24, 0.27, 0.22), rough=0.9)
    chans = K.chan_mats()

    # ---- beat 0 context: the route behind the box -------------------------------------------
    route = empty("route", root)
    bx("ground", (-180.0, -2.0, ROUTE_Z - 18.0), (180.0, 0.0, ROUTE_Z + 18.0), m["ground"], route)
    K.switch_panel(m, route, "termA", -175.0, -150.0, 0.0, 26.0, ROUTE_Z + 4.0, cols=3, rows=4)
    K.switch_panel(m, route, "termB", 150.0, 175.0, 0.0, 26.0, ROUTE_Z + 4.0, cols=3, rows=4)
    huts = [-90.0, -30.0, 30.0, 90.0]
    for k, hx in enumerate(huts):
        bx(f"hut{k}", (hx - 7.0, 0.0, ROUTE_Z - 6.0), (hx + 7.0, 10.0, ROUTE_Z + 6.0), m["hut"], route)
        bx(f"hutr{k}", (hx - 8.0, 10.0, ROUTE_Z - 7.0), (hx + 8.0, 11.2, ROUTE_Z + 7.0), m["ph_case"], route)
        bx(f"hutl{k}", (hx - 2.0, 4.0, ROUTE_Z + 6.0), (hx + 2.0, 6.0, ROUTE_Z + 6.4), m["ph_green"], route)
    stops = [-150.0] + huts + [150.0]
    for k in range(len(stops) - 1):
        a, b = stops[k] + (0 if k == 0 else 7.0), stops[k + 1] - (0 if k == len(stops) - 2 else 7.0)
        sag = [(a + (b - a) * i / 10, 3.0 - 2.0 * math.sin(math.pi * i / 10), ROUTE_Z + 7.0) for i in range(11)]
        K.fiber(m, route, f"span{k}", sag, r=0.6)
    route_path = [(-150.0, 3.0, ROUTE_Z + 7.0), (150.0, 3.0, ROUTE_Z + 7.0)]
    run(route, "rbeads", route_path, 8, 1.4, m["ph_c4"], [0], 0.0, 0.6, 70)
    show(route, [(F(0, 0), F(1, 0)), (F(4, 0), F(5, 0))])

    # ---- the amplifier box, lid off ---------------------------------------------------------
    box = empty("box", root)
    bx("tray", (-82.0, 0.0, -26.0), (82.0, 1.2, 30.0), m["ph_case"], box)
    for k, (xa, xb, za, zb) in enumerate(((-82, -80.8, -26, 30), (80.8, 82, -26, 30), (-82, 82, -26, -24.8))):
        bx(f"wall{k}", (xa, 0.0, za), (xb, 10.0, zb), m["ph_case"], box)
    bx("pcb", (-60.0, 1.2, -22.0), (60.0, 2.4, -8.0), m["ph_pcb"], box)
    for k in range(5):
        C.chip(m, box, f"ic{k}", (-45.0 + 22.0 * k, 2.4, -15.0), 7.0, 5.0, h=1.4, pins=6)
    # connectors at each end
    for k, cx in enumerate((-82.0, 82.0)):
        bx(f"conn{k}", (cx - 3.0, LINE_Y - 2.5, -2.5), (cx + 3.0, LINE_Y + 2.5, 2.5), m["steel"], box)
    # isolators: small cylinders-as-boxes on the line
    for k, ix in enumerate((X_IN + 12.0, X_OUT - 8.0)):
        bx(f"iso{k}", (ix - 4.0, LINE_Y - 1.8, -1.8), (ix + 4.0, LINE_Y + 1.8, 1.8), m["ph_gold"], box)
        bx(f"isoA{k}", (ix + 1.0, LINE_Y + 1.8, -0.4), (ix + 3.0, LINE_Y + 2.4, 0.4), m["white"], box)
    # WDM coupler (pump + signal combiner)
    bx("cpl", (X_CPL - 5.0, LINE_Y - 2.2, -2.2), (X_CPL + 5.0, LINE_Y + 2.2, 2.2), m["ph_si"], box)
    # gain-flattening filter
    bx("gff", (X_GFF - 4.0, LINE_Y - 2.4, -2.4), (X_GFF + 4.0, LINE_Y + 2.4, 2.4), m["ph_oxide"], box)
    bx("gffs", (X_GFF - 0.3, LINE_Y - 2.6, -2.6), (X_GFF + 0.3, LINE_Y + 2.6, 2.6), m["ph_violet"], box)
    # spool hub for the erbium coil
    bx("hub", (COIL_C[0] - 5.0, 1.2, COIL_C[2] - 5.0), (COIL_C[0] + 5.0, LINE_Y - 0.6, COIL_C[2] + 5.0), m["white"], box)
    cp = coil_pts()
    polyline("coil", cp, 0.55, m["er"], box)
    # pump laser on its cooler, fibre pigtail into the coupler
    bx("tec", (X_CPL - 8.0, 1.2, -24.0), (X_CPL + 8.0, 3.0, -16.0), m["ceramic"], box)
    K.laser(m, box, "pumpL", (X_CPL, 3.0, -20.0), "ph_red", size=3.0)
    pump_path = [(X_CPL + 3.2, 4.4, -20.0), (X_CPL + 6.0, LINE_Y, -12.0), (X_CPL + 2.0, LINE_Y, -2.0)]
    K.fiber(m, box, "pumpf", pump_path, r=0.4)
    # the signal line
    seg_in = [(-82.0, LINE_Y, 0.0), (X_CPL - 5.0, LINE_Y, 0.0)]
    seg_mid = [(X_CPL + 5.0, LINE_Y, 0.0), (cp[0][0], LINE_Y, 0.0), cp[0]]
    seg_out = [cp[-1], (X_GFF - 4.0, LINE_Y, cp[-1][2]), (X_GFF - 4.0, LINE_Y, 0.0)]
    seg_end = [(X_GFF + 4.0, LINE_Y, 0.0), (82.0, LINE_Y, 0.0)]
    for k, s in enumerate((seg_in, seg_mid, seg_out, seg_end)):
        K.fiber(m, box, f"line{k}", s, r=0.45)
    show(box, [(F(1, 0), F(5, 0))])

    # coil glow once pumped
    glow = empty("glow", root)
    polyline("coilg", cp, 0.6, m["er_glow"], glow)
    show(glow, [(F(2, 0.25), F(5, 0))])

    # ---- beads ------------------------------------------------------------------------------
    # beat 1: faint channels arrive (small beads), stop at the coupler
    for k, c in enumerate(chans):
        zk = -2.8 + 0.8 * k
        run(root, f"faint{k}", [(-82.0, LINE_Y + 0.0, zk * 0.25), (X_CPL - 5.0, LINE_Y, zk * 0.25)], 3, 0.45, m[c],
            [1, 2], 0.0 + 0.03 * k, 0.6, 40)
    # beat 2: pump light flows into the coil
    run(root, "pumpb", pump_path + list(cp[::6]), 10, 0.8, m["pump"], [2, 3], 0.05, 0.8, 90)
    # beat 2-3: excited-ion sparkle along the coil
    for k in range(6):
        p = cp[30 + 30 * k]
        rise(root, f"ion{k}", p, 3, 0.4, m["er_glow"], [2, 3], 0.2, 0.9, h=4.0, life=30)
    # beat 3-4: the full path, faint in, bright out
    full_in = seg_in + seg_mid[:-1] + cp[::4]
    full_out = cp[-1:] + seg_out[1:] + seg_end
    for k, c in enumerate(chans):
        run(root, f"in{k}", full_in, 2, 0.45, m[c], [3, 4], 0.02 * k, 0.5, 80)
        run(root, f"out{k}", full_out, 3, 1.2, m[c], [3, 4], 0.3 + 0.02 * k, 0.75, 30)

    # beat 4: gain spectrum before/after the flattening filter
    spec = empty("spec", root)
    bx("specb", (30.0, 14.0, -20.0), (80.0, 15.0, -10.0), m["ph_front"], spec)
    raw = [0.5, 0.8, 1.0, 0.9, 0.7, 0.75, 0.85, 0.6]
    for k, c in enumerate(chans):
        x = 33.0 + 6.0 * k
        bx(f"sr{k}", (x - 1.2, 15.0, -18.0), (x + 1.2, 15.0 + 10.0 * raw[k], -16.5), m[c], spec)
        bx(f"sf{k}", (x - 1.2, 15.0, -13.5), (x + 1.2, 15.0 + 6.0, -12.0), m[c], spec)
    show(spec, [(F(4, 0.1), F(5, 0))])

    tags = {
        0: [("terminal: DWDM transponders", (-162.0, 30.0, ROUTE_Z)), ("amp hut every 60-100 km", (-30.0, 14.0, ROUTE_Z)),
            ("span loses ~0.2 dB/km", (60.0, 6.0, ROUTE_Z + 7.0))],
        1: [("faint C-band channels in", (-65.0, LINE_Y + 4.0, 0.0)), ("lid off: the amp's tray", (0.0, 12.0, -24.0)),
            ("input isolator", (X_IN + 12.0, LINE_Y + 4.0, 0.0))],
        2: [("980 nm pump laser", (X_CPL, 8.0, -20.0)), ("WDM coupler merges pump", (X_CPL, LINE_Y + 4.0, 0.0)),
            ("erbium-doped coil, 5-30 m", (0.0, LINE_Y + 3.0, COIL_C[2] + 15.0))],
        3: [("stimulated emission", (0.0, LINE_Y + 4.0, COIL_C[2])), ("all colours amplified", (62.0, LINE_Y + 4.0, 0.0)),
            ("+20-30 dB gain", (X_GFF, LINE_Y + 5.0, 0.0))],
        4: [("raw gain: uneven", (36.0, 25.0, -18.0)), ("after flattening filter", (75.0, 21.0, -12.0)),
            ("isolator blocks reflections", (X_OUT - 8.0, LINE_Y + 2.0, 2.0)), ("chain of amps", (-90.0, 12.0, ROUTE_Z))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 10.0, ROUTE_Z), 350.0, 0.0, 0.32, pad=1.0),
        frame((-45.0, LINE_Y, -4.0), 90.0, 0.25, 0.55),
        [(0.0, frame((-30.0, LINE_Y, -10.0), 100.0, 0.30, 0.65)), (0.55, frame((-18.0, LINE_Y, -6.0), 85.0, 0.20, 0.70))],
        frame((10.0, LINE_Y, 0.0), 170.0, -0.15, 0.55),
        [(0.0, frame((50.0, 14.0, -10.0), 70.0, -0.25, 0.35)), (0.55, frame((0.0, 10.0, -40.0), 260.0, 0.0, 0.40))],
    ], root)


if __name__ == "__main__":
    build()
