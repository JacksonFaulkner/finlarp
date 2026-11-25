"""TRM_CRAH: a computer room air handler, cut open, at the POWER pages' detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_crah.py

No GPU board: a CRAH is room equipment. Units are centimetres. Unlike trm_hot_aisle (which is
about the aisles), the subject here is the unit itself: a tall downflow cabinet with its front
skin cut away at z = 0 showing the return filter bank, the A-frame chilled-water coil, the
three-way valve and headers, the condensate pan, the controller and the EC fans that sit in the
raised floor and push cold air into the plenum. A row of racks with perforated tiles in front
stands to the right; a second (standby) CRAH stands to the left.

Beats:
  0 room      warm air in at the top, cold air out under the floor, up through the tiles
  1 coil      chilled water through the A-frame coil; the valve sets how much
  2 fans      EC fans pressurise the plenum
  3 control   supply-air sensor, valve, condensate; standby unit for N+1
  4 limits    ~15-20 kW/rack ceiling for room air; AI racks go liquid; who makes them
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat, tube  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, polyline  # noqa: E402
import trm_chiller as K  # noqa: E402  (rack + fan builders)

SLUG = "TRM_CRAH"
BEATS = [
    ("A CRAH cools the room air, not the chips",
     "A computer room air handler is a fridge-sized cabinet on the data hall floor. It pulls in the warm air the "
     "servers exhaust, cools it across a water coil and blows it back out, usually down into a raised floor so it "
     "rises through perforated tiles in front of the racks. A hall has a row of them along the walls."),
    ("Chilled water does the cooling; the coil is the heart",
     "Inside is a big finned coil, often folded into an A shape for more area. Chilled water from the building plant "
     "runs through its tubes at roughly 10 to 18 C, and a motorised valve opens or closes to match the heat load. "
     "No compressor sits inside: that is the difference from a CRAC, which carries its own refrigerant circuit."),
    ("EC fans push the cold air under the floor",
     "Variable-speed EC fans at the bottom blow the cooled air into the floor plenum, holding a small positive "
     "pressure (a few hundredths of an inch of water) so air comes up wherever a tile is perforated. Fan power goes "
     "with the cube of speed, so running more units at half speed beats a few at full speed."),
    ("Sensors steer it, and a spare stands by",
     "A controller reads supply and return air temperature and humidity, then trims the valve and fan speed. Water "
     "that condenses on the coil drips into a pan and is pumped away. Halls carry at least one extra unit (N+1) so "
     "a failure or service does not warm the room. A large unit moves 100-250 kW of heat."),
    ("Air runs out of road above ~20 kW a rack",
     "Room air handles about 15 to 20 kW per rack before the airflow gets impractical. AI racks run 40 to 130 kW, so "
     "GPUs move to direct liquid cooling and CRAHs shrink to the leftover heat from networking, storage and power "
     "gear. Makers: Vertiv (VRT, Liebert), Schneider, Stulz, Trane (TT), Johnson Controls (JCI), Munters."),
]

# layout (cm). Floor top at y = 0, plenum below to y = -60, ceiling at y = 300.
UX0, UX1, UZ0 = 0.0, 140.0, -90.0  # CRAH cabinet footprint (front cut at z = 0)
UH = 210.0
PL = -60.0
RX0 = 230.0  # rack row start (x)
COIL = (12.0, 128.0, 70.0, 160.0)  # coil x0, x1, y bottom, y apex


def mats(m):
    K.mats(m)
    m["tile"] = mat("cr_tile", (0.70, 0.71, 0.72), metal=0.2, rough=0.6)
    m["perf"] = mat("cr_perf", (0.30, 0.32, 0.36), metal=0.4, rough=0.5)
    m["filter"] = mat("cr_filter", (0.88, 0.86, 0.72), rough=0.95)
    m["pan"] = mat("cr_pan", (0.55, 0.57, 0.60), metal=0.9, rough=0.3)
    m["air_c"] = mat("cr_air_c", (0.40, 0.75, 1.0), emit=(0.30, 0.70, 1.0), strength=3.0)
    m["air_w"] = mat("cr_air_w", (1.0, 0.60, 0.25), emit=(1.0, 0.52, 0.18), strength=3.0)
    m["drip"] = mat("cr_drip", (0.60, 0.85, 1.0), emit=(0.55, 0.85, 1.0), strength=2.5)
    m["coil_c"] = mat("cr_coil_c", (0.3, 0.6, 1.0), emit=(0.25, 0.6, 1.0), strength=1.4)


def room(m, root):
    g = empty("room", root)
    bx("slab", (-200.0, PL - 6.0, -260.0), (560.0, PL, 0.0), m["concrete"], g)
    bx("backwall", (-200.0, PL, -260.0), (560.0, 300.0, -252.0), m["wall"], g)
    # raised floor: pedestals + stringers + tiles (60 cm grid); perforated tiles before the racks
    peds = []
    for i in range(13):
        for j in range(5):
            x, z = -200.0 + 60.0 * i, -240.0 + 60.0 * j
            peds.append(tube(f"ped{i}_{j}", (x, PL, z), (x, -4.0, z), 1.6, m["steel"], g, 8))
    D.join(peds, "pedestals")
    tiles, perf = [], []
    for i in range(12):
        for j in range(4):
            x, z = -200.0 + 60.0 * i, -240.0 + 60.0 * j
            if UX0 - 10 < x < UX1 and z > UZ0 - 20:
                continue  # the unit stands in a floor cut-out
            is_perf = j == 3 and x >= RX0 - 10 and x < 520.0
            (perf if is_perf else tiles).append(bx(f"tl{i}_{j}", (x + 0.5, -4.0, z + 0.5), (x + 59.5, 0.0, z + 59.5), m["perf" if is_perf else "tile"], g))
    D.join(tiles, "tiles")
    D.join(perf, "perf_tiles")
    holes = []
    for i in range(12):
        x = -200.0 + 60.0 * i
        if not (x >= RX0 - 10 and x < 520.0):
            continue
        for a in range(6):
            for b in range(6):
                hx, hz = x + 7.0 + 9.0 * a, -60.0 + 7.0 + 9.0 * b
                holes.append(bx(f"ph{i}_{a}{b}", (hx, 0.0, hz), (hx + 4.0, 0.15, hz + 4.0), m["frame"], g))
    D.join(holes, "perf_holes")
    leds = empty("leds", root)
    for k in range(4):
        K.rack(m, g, f"rk{k}", RX0 + 70.0 * k, -230.0, w=64.0, dep=110.0, h=210.0, leds=leds)
    return leds


def crah(m, root, name, x0, standby=False):
    """The cabinet at x0 (width 140). Returns a dict of glow groups, fans and paths."""
    g = empty(name, root)
    x1 = x0 + 140.0
    bx(f"{name}_back", (x0, 0.0, UZ0), (x1, UH, UZ0 + 3.0), m["skin"], g)
    bx(f"{name}_l", (x0, 0.0, UZ0), (x0 + 3.0, UH, 0.0), m["skin"], g)
    bx(f"{name}_r", (x1 - 3.0, 0.0, UZ0), (x1, UH, 0.0), m["skin"], g)
    for x in (x0, x1 - 4.0):
        bx(f"{name}_post{x:.0f}", (x, 0.0, -4.0), (x + 4.0, UH, 0.0), m["frame"], g)
    if standby:  # closed unit: full front skin
        bx(f"{name}_front", (x0 + 4.0, 0.0, -3.0), (x1 - 4.0, UH, 0.0), m["skin"], g)
        bx(f"{name}_grille", (x0 + 10.0, UH - 30.0, -0.5), (x1 - 10.0, UH - 6.0, 0.4), m["grid"], g)
        bx(f"{name}_hmi", (x0 + 50.0, 140.0, 0.0), (x0 + 90.0, 165.0, 1.0), m["screen"], g)
        return {"g": g}
    # top: return-air grille + V filter bank
    grille = []
    for k in range(14):
        xs = x0 + 6.0 + 9.4 * k
        grille.append(bx(f"{name}_gr{k}", (xs, UH, UZ0 + 4.0), (xs + 3.0, UH + 2.0, -4.0), m["frame"], g))
    D.join(grille, f"{name}_grille")
    filt = []
    for k in range(6):
        xa = x0 + 8.0 + 21.0 * k
        filt.append(bx(f"{name}_f{k}a", (xa, 178.0, UZ0 + 6.0), (xa + 10.0, 200.0, -8.0), m["filter"], g))
        filt.append(bx(f"{name}_f{k}b", (xa + 10.0, 182.0, UZ0 + 6.0), (xa + 19.0, 198.0, -8.0), m["frame"], g))
    D.join(filt, f"{name}_filters")
    # A-frame coil: two slanted fin banks meeting at the apex, copper return bends at the ends
    cx0, cx1, yb, ya = x0 + 12.0, x1 - 12.0, COIL[2], COIL[3]
    xm = (cx0 + cx1) / 2
    fins, bends, glow = [], [], empty(f"{name}_coilglow", root)
    for side in (-1, 1):
        for k in range(16):
            t = k / 15.0
            y = yb + (ya - yb) * t
            x = xm + side * (cx1 - xm) * (1.0 - t)
            fins.append(bx(f"{name}_fin{side}{k}", (x - 4.0, y, UZ0 + 8.0), (x + 4.0, y + 1.8, -8.0), m["fin"], g))
            if k % 2 == 0:
                tube(f"{name}_ct{side}{k}", (x, y + 0.9, UZ0 + 6.0), (x, y + 0.9, -6.0), 0.9, m["copper"], g, 8)
                bends.append(tube(f"{name}_cb{side}{k}", (x, y + 0.9, -6.0), (x, y + 6.0, -6.0), 1.0, m["copper"], g, 8))
                tube(f"{name}_cg{side}{k}", (x, y + 0.9, -5.0), (x, y + 0.9, UZ0 + 10.0), 0.5, m["coil_c"], glow, 6)
    D.join(fins, f"{name}_fins")
    D.join(bends, f"{name}_bends")
    show(glow, [])
    # condensate pan + pump + drain
    bx(f"{name}_pan", (cx0 - 2.0, yb - 8.0, UZ0 + 6.0), (cx1 + 2.0, yb - 4.0, -6.0), m["pan"], g)
    bx(f"{name}_pump", (x1 - 30.0, 30.0, UZ0 + 10.0), (x1 - 14.0, 44.0, UZ0 + 30.0), m["motor"], g)
    polyline(f"{name}_drain", [(x1 - 22.0, yb - 8.0, UZ0 + 20.0), (x1 - 22.0, 44.0, UZ0 + 20.0)], 1.0, m["plastic"], g)
    # chilled water headers + 3-way valve on the right side
    hx = x1 - 8.0
    sup = [(hx + 60.0, PL + 10.0, -40.0), (hx, PL + 10.0, -40.0), (hx, 60.0, -40.0), (hx, 60.0, -30.0), (hx, ya - 10.0, -30.0)]
    ret = [(hx - 2.0, ya - 6.0, -60.0), (hx - 2.0, 50.0, -60.0), (hx, 50.0, -60.0), (hx, PL + 22.0, -60.0), (hx + 60.0, PL + 22.0, -60.0)]
    polyline(f"{name}_sup", sup, 2.6, m["pipe_s"], g)
    polyline(f"{name}_ret", ret, 2.6, m["pipe_r"], g)
    valve = empty(f"{name}_valve", g)
    bx(f"{name}_vb", (hx - 5.0, 52.0, -46.0), (hx + 5.0, 64.0, -34.0), m["gold"], valve)
    bx(f"{name}_va", (hx - 4.0, 64.0, -44.0), (hx + 4.0, 76.0, -36.0), m["dark"], valve)
    # controller + display, supply/return sensors
    bx(f"{name}_ctl", (x0 + 6.0, 20.0, UZ0 + 6.0), (x0 + 36.0, 58.0, UZ0 + 14.0), m["dark"], g)
    scr = empty(f"{name}_scr", root)
    bx(f"{name}_ctls", (x0 + 9.0, 40.0, UZ0 + 14.0), (x0 + 33.0, 54.0, UZ0 + 14.6), m["led"], scr)
    sens = empty(f"{name}_sens", root)
    for k, (sx, sy) in enumerate(((xm, 205.0), (xm, -40.0))):
        bx(f"{name}_sn{k}", (sx - 2.0, sy - 2.0, -24.0), (sx + 2.0, sy + 2.0, -20.0), m["sig"], sens)
    # floor box + EC fans (rotors about scene y) blowing down into the plenum
    bx(f"{name}_plinth", (x0, PL, UZ0), (x0 + 3.0, 0.0, 0.0), m["frame"], g)
    bx(f"{name}_plinr", (x1 - 3.0, PL, UZ0), (x1, 0.0, 0.0), m["frame"], g)
    fans = [K.fan(m, g, f"{name}_fan{k}", (x0 + 28.0 + 42.0 * k, -32.0, -45.0), r=18.0) for k in range(3)]
    for k in range(3):
        tube(f"{name}_mot{k}", (x0 + 28.0 + 42.0 * k, -14.0, -45.0), (x0 + 28.0 + 42.0 * k, 0.0, -45.0), 6.0, m["motor"], g, 16)
    bx(f"{name}_deck", (x0, 0.0, UZ0), (x1, 4.0, 0.0), m["grid"], g)
    return {"g": g, "glow": glow, "fans": fans, "sup": sup, "ret": ret, "scr": scr, "sens": sens, "valve": valve,
            "xm": xm, "hx": hx}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    leds = room(m, root)
    u = crah(m, root, "crah", UX0)
    sb = crah(m, root, "crah_sb", -180.0, standby=True)
    for k in range(4):
        blink(leds, k, [0, 2, 4, 6], n=8, on=0.7)
    for b in range(5):
        blink(u["scr"], b, [0, 1, 2, 3, 4, 5, 6, 7], n=8, on=0.8)
    blink(u["sens"], 3, [0, 2, 4, 6], n=8, on=0.5)
    show(u["glow"], [(F(1, 0.1), F(5, 0))])
    for f_ in u["fans"]:
        C.spin(f_, [0, 1, 2, 3, 4], turns=4.0)
    xm = u["xm"]
    # air: warm return from rack backs along the ceiling into the top; cold down the coil, out the fans,
    # along the plenum and up through the perforated tiles into the rack fronts
    warm = [(RX0 + 140.0, 215.0, -200.0), (RX0 + 140.0, 270.0, -150.0), (xm + 20.0, 270.0, -50.0), (xm, UH + 4.0, -45.0),
            (xm, 185.0, -45.0)]
    inside = [(xm - 30.0, 175.0, -40.0), (xm - 50.0, 110.0, -40.0), (xm - 30.0, 30.0, -40.0), (xm - 30.0, -40.0, -45.0)]
    inside2 = [(xm + 30.0, 175.0, -50.0), (xm + 50.0, 110.0, -50.0), (xm + 30.0, 30.0, -50.0), (xm + 30.0, -40.0, -45.0)]
    plen = [(xm, -48.0, -45.0), (RX0 - 40.0, -40.0, -30.0), (RX0 + 60.0, -40.0, -30.0), (RX0 + 60.0, 10.0, -30.0),
            (RX0 + 60.0, 80.0, -110.0)]
    plen2 = [(xm + 40.0, -48.0, -45.0), (RX0 + 80.0, -40.0, -30.0), (RX0 + 200.0, -40.0, -30.0), (RX0 + 200.0, 10.0, -30.0),
             (RX0 + 200.0, 120.0, -110.0)]
    allb = [0, 1, 2, 3, 4]
    run(root, "a_warm", warm, 12, 4.5, m["air_w"], allb, 0.0, 0.75, 60)
    run(root, "a_in1", inside, 6, 3.6, m["air_c"], allb, 0.1, 0.8, 40)
    run(root, "a_in2", inside2, 6, 3.6, m["air_c"], allb, 0.15, 0.85, 40)
    run(root, "a_pl1", plen, 10, 4.0, m["air_c"], allb, 0.1, 0.8, 55)
    run(root, "a_pl2", plen2, 10, 4.0, m["air_c"], allb, 0.15, 0.85, 60)
    for k in range(4):
        rise(root, f"rk_heat{k}", (RX0 + 32.0 + 70.0 * k, 200.0, -228.0), 4, 2.2, m["heat"], [0, 4], 0.0, 0.8, 40.0, 40, (16.0, 4.0))
    # chilled water through the coil in beats 1-4
    run(root, "w_sup", u["sup"], 8, 3.4, m["c_supply"], [1, 2, 3, 4], 0.0, 0.7, 45)
    run(root, "w_ret", u["ret"], 8, 3.4, m["c_return"], [1, 2, 3, 4], 0.05, 0.75, 45)
    # condensate drips beat 3
    drip = [(xm - 20.0, COIL[2] + 5.0, -30.0), (xm - 20.0, COIL[2] - 6.0, -30.0)]
    run(root, "drip", drip, 6, 1.2, m["drip"], [3], 0.0, 0.85, 20)
    C.wiggle(u["valve"], [1, 3], amp=(0.0, 0.6, 0.0), period=10)

    hx = u["hx"]
    tags = {
        0: [("warm exhaust back to the CRAH", (RX0 + 60.0, 270.0, -120.0)), ("CRAH: cools the room air", (70.0, UH + 20.0, -45.0)),
            ("raised-floor plenum", (RX0 - 50.0, -40.0, -20.0)), ("perforated tiles feed racks", (RX0 + 130.0, 6.0, -30.0))],
        1: [("A-frame chilled-water coil", (xm, COIL[3] + 6.0, -20.0)), ("3-way valve sets the flow", (hx, 70.0, -40.0)),
            ("10-18 C water in", (hx + 50.0, PL + 10.0, -40.0)), ("no compressor (vs CRAC)", (40.0, 40.0, -10.0))],
        2: [("EC fans, variable speed", (xm, -30.0, -10.0)), ("plenum under slight pressure", (RX0 + 20.0, -40.0, -10.0)),
            ("fan power ~ speed cubed", (xm, 20.0, -10.0))],
        3: [("supply/return air sensors", (xm, 205.0, -20.0)), ("condensate pan + pump", (UX1 - 22.0, 50.0, -10.0)),
            ("standby unit: N+1", (-110.0, UH + 15.0, -45.0)), ("100-250 kW per unit", (70.0, 120.0, 0.0))],
        4: [("room air tops out ~20 kW/rack", (RX0 + 140.0, 230.0, -170.0)), ("AI racks 40-130 kW: liquid", (RX0 + 140.0, 110.0, -100.0)),
            ("Vertiv, Stulz, Trane, JCI", (70.0, UH + 20.0, -45.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((150.0, 110.0, -120.0), 640.0, 0.30, 0.25, pad=1.0),
        [(0.0, frame((70.0, 115.0, -45.0), 220.0, 0.20, 0.10)), (0.6, frame((80.0, 100.0, -45.0), 200.0, 0.45, 0.15))],
        [(0.0, frame((110.0, -20.0, -45.0), 300.0, 0.25, 0.30)), (0.55, frame((230.0, -10.0, -60.0), 360.0, -0.15, 0.40))],
        frame((10.0, 110.0, -60.0), 380.0, 0.25, 0.15),
        frame((170.0, 120.0, -120.0), 700.0, -0.25, 0.30, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
