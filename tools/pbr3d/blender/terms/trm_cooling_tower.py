"""TRM_COOLING_TOWER: a wet (evaporative) cooling tower beside a chiller plant, cut open.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_cooling_tower.py

No GPU board: a cooling tower is site plant. Units are centimetres. Left: a water-cooled chiller's
condenser barrel and pump on a pad. Right: a counterflow tower, front skin cut away at z = 0: cold
water basin, side air-inlet louvers, corrugated fill pack, spray header with nozzles, drift
eliminators, fan deck with a fan stack and a 6-blade fan. Amber = warm condenser water, blue = cooled
water, white = air / vapour plume, green = make-up water.

Beats:
  0 site      chiller condenser sends warm water to the tower, cool water comes back
  1 inside    spray over the fill, air enters the louvers and rises through
  2 evaporate the fan spins, a vapour plume leaves the top
  3 water     make-up meter tops up evaporation and blowdown
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
import trm_chiller as CH  # noqa: E402

SLUG = "TRM_COOLING_TOWER"
BEATS = [
    ("A cooling tower dumps the plant's heat into the air by evaporating water",
     "Water-cooled chillers reject the heat they pull out of a data hall into a condenser water loop. That loop runs "
     "out to a cooling tower at roughly 35 C and comes back around 29 C. The tower is the last step in the chain: "
     "from chip, to coolant, to chiller, to outside air."),
    ("Warm water is sprayed over fill while fans pull air up through it",
     "Inside, a header of nozzles sprays the warm water over fill: stacks of corrugated plastic sheets that spread it "
     "into thin films with a huge surface area. Air enters through louvers at the bottom and rises against the falling "
     "water. Drift eliminators above the spray catch droplets before the air leaves, and the cooled water collects "
     "in a basin."),
    ("Evaporating about 1% of the flow cools the rest by ~6 C",
     "Each kilogram of water that evaporates carries away about 2,400 kJ, so a small fraction turning to vapour chills "
     "everything that falls past it. That is why towers can cool water below the outdoor dry-bulb temperature and run "
     "with a lower energy bill than air-cooled chillers. The white plume on a cold day is that vapour condensing."),
    ("The catch: water use, refilled through a make-up meter",
     "Evaporated water has to be replaced, and some basin water is bled off (blowdown) so dissolved minerals do not "
     "build up. Rejecting 100 MW of heat this way evaporates on the order of 3 million litres a day. In dry or "
     "water-stressed regions that can decide where a campus is built, or push it toward dry coolers instead."),
    ("Big AI campuses mix towers, dry coolers and chillers",
     "Warm-water liquid cooling lets many new sites skip evaporation for most of the year, but towers remain the cheapest "
     "way to reject heat where water is plentiful. Makers and suppliers: SPX Technologies (SPXC, Marley), Modine (MOD), "
     "Johnson Controls (JCI), Trane Technologies (TT), plus EVAPCO and Baltimore Aircoil (private)."),
]

TX0, TX1, TZ0 = 60.0, 300.0, -200.0  # tower footprint, front cut at z = 0
BASIN = 40.0
LOUV = (45.0, 110.0)
FILL = (120.0, 190.0)
SPRAY = 205.0
DRIFT = (218.0, 230.0)
DECK = 250.0
FANC = ((TX0 + TX1) / 2, DECK, TZ0 / 2)


def mats(m):
    CH.mats(m)
    m["frp"] = mat("ct_frp", (0.70, 0.74, 0.72), metal=0.1, rough=0.55)
    m["fillm"] = mat("ct_fill", (0.30, 0.44, 0.50), metal=0.0, rough=0.6)
    m["water"] = mat("ct_water", (0.10, 0.30, 0.45), metal=0.2, rough=0.1)
    m["pvc"] = mat("ct_pvc", (0.86, 0.86, 0.84), rough=0.5)
    m["vapour"] = mat("ct_vap", (0.85, 0.90, 0.95), emit=(0.80, 0.88, 0.95), strength=2.0)
    m["makeup"] = mat("ct_mk", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.5)
    m["air"] = mat("ct_air", (0.75, 0.85, 0.95), emit=(0.7, 0.82, 0.95), strength=2.5)
    m["film"] = mat("ct_film", (0.3, 0.6, 1.0), emit=(0.25, 0.6, 1.0), strength=1.4)


def tower(m, root):
    g = empty("tower", root)
    bx("t_pad", (TX0 - 20.0, -6.0, TZ0 - 20.0), (TX1 + 20.0, 0.0, 15.0), m["concrete"], g)
    # basin: concrete tub with water surface
    bx("t_basin_floor", (TX0, 0.0, TZ0), (TX1, 4.0, 0.0), m["concrete"], g)
    bx("t_basin_back", (TX0, 4.0, TZ0), (TX1, BASIN, TZ0 + 6.0), m["concrete"], g)
    bx("t_basin_l", (TX0, 4.0, TZ0), (TX0 + 6.0, BASIN, 0.0), m["concrete"], g)
    bx("t_basin_r", (TX1 - 6.0, 4.0, TZ0), (TX1, BASIN, 0.0), m["concrete"], g)
    bx("t_basin_front", (TX0, 4.0, -4.0), (TX1, 18.0, 0.0), m["concrete"], g)
    bx("t_water", (TX0 + 6.0, 4.0, TZ0 + 6.0), (TX1 - 6.0, 30.0, -4.0), m["water"], g)
    # casing: back wall, side walls above louvers, corner posts
    bx("t_back", (TX0, LOUV[1], TZ0), (TX1, DECK, TZ0 + 3.0), m["frp"], g)
    for x0, x1 in ((TX0, TX0 + 3.0), (TX1 - 3.0, TX1)):
        bx(f"t_side{x0:.0f}", (x0, LOUV[1], TZ0), (x1, DECK, 0.0), m["frp"], g)
    for x in (TX0, TX1 - 5.0):
        for z in (TZ0, -5.0):
            bx(f"t_post{x:.0f}{z:.0f}", (x, BASIN, z), (x + 5.0, DECK, z + 5.0), m["frame"], g)
    # louvers on both ends and the back: slanted slats
    lv = []
    for k in range(9):
        y = LOUV[0] + 7.0 * k
        for x0, x1 in ((TX0 - 4.0, TX0 + 2.0), (TX1 - 2.0, TX1 + 4.0)):
            lv.append(bx(f"t_lv{x0:.0f}_{k}", (x0, y, TZ0), (x1, y + 2.0, 0.0), m["frp"], g))
        lv.append(bx(f"t_lvb{k}", (TX0, y, TZ0 - 4.0), (TX1, y + 2.0, TZ0 + 2.0), m["frp"], g))
    D.join(lv, "t_louvers")
    # fill pack: corrugated sheets (zig-zag strips) seen edge-on through the cut
    fill = []
    n_sheet = 22
    for i in range(n_sheet):
        x = TX0 + 10.0 + (TX1 - TX0 - 20.0) * i / (n_sheet - 1)
        for j in range(7):
            y0 = FILL[0] + 10.0 * j
            dx = 2.5 if j % 2 == 0 else -2.5
            fill.append(tube(f"t_f{i}_{j}", (x, y0, -2.0), (x + dx, y0 + 10.0, -2.0), 0.6, m["fillm"], g, 4))
        fill.append(bx(f"t_fs{i}", (x - 0.3, FILL[0], TZ0 + 6.0), (x + 0.3, FILL[1], -4.0), m["fillm"], g))
    D.join(fill, "t_fill")
    bx("t_fill_sup", (TX0 + 3.0, FILL[0] - 4.0, TZ0), (TX1 - 3.0, FILL[0] - 1.0, 0.0), m["frame"], g)
    # spray header: main pipe along x with branch arms and nozzles
    tube("t_hdr", (TX0 - 30.0, SPRAY, -100.0), (TX1 - 10.0, SPRAY, -100.0), 5.0, m["pvc"], g, 16)
    noz = []
    for i in range(7):
        x = TX0 + 22.0 + 30.0 * i
        noz.append(tube(f"t_arm{i}", (x, SPRAY, TZ0 + 10.0), (x, SPRAY, -8.0), 2.2, m["pvc"], g, 10))
        for z in (-170.0, -130.0, -70.0, -30.0):
            noz.append(tube(f"t_nz{i}_{z:.0f}", (x, SPRAY, z), (x, SPRAY - 6.0, z), 1.6, m["frame"], g, 8))
    D.join(noz, "t_arms")
    # drift eliminators: tight chevron blades
    de = []
    for i in range(40):
        x = TX0 + 6.0 + (TX1 - TX0 - 12.0) * i / 39
        de.append(tube(f"t_de{i}a", (x, DRIFT[0], -3.0), (x + 2.0, (DRIFT[0] + DRIFT[1]) / 2, -3.0), 0.5, m["frp"], g, 4))
        de.append(tube(f"t_de{i}b", (x + 2.0, (DRIFT[0] + DRIFT[1]) / 2, -3.0), (x, DRIFT[1], -3.0), 0.5, m["frp"], g, 4))
    D.join(de, "t_drift")
    bx("t_drift_back", (TX0 + 3.0, DRIFT[0], TZ0 + 3.0), (TX1 - 3.0, DRIFT[1], -6.0), m["frp"], g)
    # fan deck with an opening, a fan stack (velocity recovery cylinder)
    bx("t_deck_l", (TX0, DECK, TZ0), (FANC[0] - 70.0, DECK + 4.0, 0.0), m["frame"], g)
    bx("t_deck_r", (FANC[0] + 70.0, DECK, TZ0), (TX1, DECK + 4.0, 0.0), m["frame"], g)
    bx("t_deck_b", (FANC[0] - 70.0, DECK, TZ0), (FANC[0] + 70.0, DECK + 4.0, FANC[2] - 70.0), m["frame"], g)
    bx("t_deck_f", (FANC[0] - 70.0, DECK, FANC[2] + 70.0), (FANC[0] + 70.0, DECK + 4.0, 0.0), m["frame"], g)
    stack = []
    for j in range(16):  # back half only so the fan shows through the cut
        a0, a1 = math.pi + math.pi * j / 16, math.pi + math.pi * (j + 1) / 16
        r0, r1 = 66.0, 72.0
        for k in range(6):
            y0 = DECK + 4.0 + 9.0 * k
            ra, rb = r0 + (r1 - r0) * k / 6, r0 + (r1 - r0) * (k + 1) / 6
            stack.append(tube(f"t_st{j}_{k}", (FANC[0] + ra * math.cos(a0), y0 + 4.5, FANC[2] + ra * math.sin(a0)),
                              (FANC[0] + ra * math.cos(a1), y0 + 4.5, FANC[2] + ra * math.sin(a1)), 4.6, m["frp"], g, 6))
    D.join(stack, "t_stack")
    # motor + gearbox under the fan on a bridge
    bx("t_bridge", (FANC[0] - 70.0, DECK - 6.0, FANC[2] - 4.0), (FANC[0] + 70.0, DECK, FANC[2] + 4.0), m["frame"], g)
    bx("t_gear", (FANC[0] - 8.0, DECK, FANC[2] - 8.0), (FANC[0] + 8.0, DECK + 12.0, FANC[2] + 8.0), m["motor"], g)
    tube("t_motor", (FANC[0] + 14.0, DECK + 6.0, FANC[2]), (FANC[0] + 40.0, DECK + 6.0, FANC[2]), 7.0, m["motor"], g, 16)
    tube("t_shaft", (FANC[0] + 8.0, DECK + 6.0, FANC[2]), (FANC[0] + 14.0, DECK + 6.0, FANC[2]), 2.0, m["steel"], g, 8)
    return g


def fan(m, root):
    hub = empty("ct_fan", root, C.P(FANC[0], DECK + 14.0, FANC[2]))
    tube("ctf_hub", (0.0, 0.0, 0.0), (0.0, 6.0, 0.0), 9.0, m["frame"], hub, 16)
    bl = []
    for k in range(6):
        a = 2 * math.pi * k / 6
        ca, sa = math.cos(a), math.sin(a)
        bl.append(tube(f"ctf_b{k}", (8.0 * ca, 3.0, 8.0 * sa), (62.0 * ca, 4.0, 62.0 * sa), 3.4, m["skin"], hub, 4))
    D.join(bl, "ctf_blades")
    return hub


def plant(m, root):
    """The chiller's condenser barrel and the condenser-water pump, left of the tower."""
    g = empty("plant", root)
    bx("p_pad", (-260.0, -6.0, -170.0), (-20.0, 0.0, 15.0), m["concrete"], g)
    bx("p_skid", (-240.0, 0.0, -150.0), (-80.0, 8.0, -30.0), m["frame"], g)
    tube("p_cond", (-235.0, 50.0, -90.0), (-95.0, 50.0, -90.0), 30.0, m["shell"], g, 28)
    tube("p_evap", (-235.0, 22.0, -130.0), (-95.0, 22.0, -130.0), 1.0, m["shell"], g, 8)
    for x in (-240.0, -95.0):
        tube(f"p_head{x:.0f}", (x, 50.0, -90.0), (x + 5.0, 50.0, -90.0), 32.0, m["shell"], g, 28)
    for x in (-215.0, -115.0):
        bx(f"p_sad{x:.0f}", (x - 6.0, 8.0, -110.0), (x + 6.0, 24.0, -70.0), m["frame"], g)
    tube("p_comp", (-200.0, 92.0, -90.0), (-130.0, 92.0, -90.0), 14.0, m["steel"], g, 20)
    tube("p_cmotor", (-130.0, 92.0, -90.0), (-95.0, 92.0, -90.0), 12.0, m["motor"], g, 20)
    # pump on the return line
    tube("p_pump", (-40.0, 18.0, -40.0), (-40.0, 40.0, -40.0), 10.0, m["shell"], g, 20)
    tube("p_pmotor", (-40.0, 40.0, -40.0), (-40.0, 62.0, -40.0), 8.0, m["motor"], g, 20)
    leds = empty("p_leds", root)
    bx("p_panel", (-250.0, 8.0, -160.0), (-215.0, 70.0, -150.0), m["skin"], g)
    for k in range(4):
        bx(f"p_led{k}", (-244.0 + 7.0 * k, 60.0, -150.0), (-240.0 + 7.0 * k, 63.0, -149.5), m["led"], leds)
    return leds


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    leds = plant(m, root)
    tower(m, root)
    fh = fan(m, root)
    # condenser water: warm out of the condenser, up to the spray header; cool from the basin back
    warm = [(-95.0, 62.0, -90.0), (-10.0, 62.0, -90.0), (-10.0, SPRAY, -90.0), (TX0 - 30.0, SPRAY, -100.0),
            (TX1 - 12.0, SPRAY, -100.0)]
    cool = [(TX0 + 20.0, 12.0, -40.0), (-20.0, 12.0, -40.0), (-40.0, 20.0, -40.0), (-40.0, 30.0, -40.0),
            (-60.0, 30.0, -40.0), (-60.0, 38.0, -90.0), (-95.0, 38.0, -90.0)]
    polyline("cw_warm", warm[:4], 5.0, m["pipe_r"], root)
    polyline("cw_cool", cool, 5.0, m["pipe_s"], root)
    # make-up water line with a meter + float valve, blowdown drain
    mk = [(TX1 + 80.0, 6.0, -40.0), (TX1 + 40.0, 6.0, -40.0), (TX1 + 40.0, 36.0, -40.0), (TX1 - 10.0, 36.0, -40.0)]
    polyline("mk_line", mk, 2.6, m["copper"], root)
    meter = empty("mk_meter", root)
    bx("mk_body", (TX1 + 52.0, 0.0, -50.0), (TX1 + 70.0, 16.0, -30.0), m["brass"] if "brass" in m else m["gold"], meter)
    bx("mk_face", (TX1 + 54.0, 16.0, -48.0), (TX1 + 68.0, 17.0, -32.0), m["white"], meter)
    dial = empty("mk_dial", root, C.P(TX1 + 61.0, 17.2, -40.0))
    bx("mk_needle", (-0.4, 0.0, 0.0), (0.4, 0.4, -6.0), m["warn"], dial)
    bd = [(TX0 + 10.0, 6.0, -20.0), (TX0 - 10.0, 6.0, -20.0), (TX0 - 10.0, 2.0, 20.0)]
    polyline("bd_line", bd, 2.0, m["copper"], root)

    films = empty("films", root)
    for i in range(7):
        x = TX0 + 22.0 + 30.0 * i
        for z in (-30.0,):
            tube(f"film{i}", (x, SPRAY - 8.0, z + 26.0), (x, FILL[0], z + 26.0), 0.8, m["film"], films, 6)
    show(films, [(F(1, 0.2), F(4, 0))])
    for k in range(4):
        blink(leds, k, [0, 2, 4, 6], n=8, on=0.7)

    all_b = [0, 1, 2, 3, 4]
    run(root, "w_warm", warm, 12, 5.5, m["c_return"], all_b, 0.0, 0.7, 70)
    run(root, "w_cool", cool, 12, 5.5, m["c_supply"], all_b, 0.0, 0.7, 70)
    # water falling: warm drops at the spray turn blue as they fall through the fill
    for i in range(7):
        x = TX0 + 22.0 + 30.0 * i
        run(root, f"drop_w{i}", [(x, SPRAY - 6.0, -4.0), (x, FILL[1], -4.0)], 2, 2.2, m["c_return"], [1, 2, 3], 0.0, 0.8, 14)
        run(root, f"drop_c{i}", [(x + 3.0, FILL[0], -4.0), (x + 3.0, 32.0, -4.0)], 2, 2.2, m["c_supply"], [1, 2, 3], 0.1, 0.9, 18)
    # air: in through both louver banks, up through the fill, out the fan
    for s, x0 in ((-1, TX0 - 40.0), (1, TX1 + 40.0)):
        xm = TX0 + 50.0 if s < 0 else TX1 - 50.0
        run(root, f"air{s}", [(x0, 70.0, -4.0), (xm, 80.0, -4.0), (xm, FILL[1], -4.0), (FANC[0] + s * 30.0, DECK, -60.0),
                              (FANC[0] + s * 30.0, DECK + 90.0, -60.0)], 8, 3.0, m["air"], [1, 2], 0.0, 0.75, 70)
    C.spin(fh, all_b, turns=4.0)
    rise(root, "plume", (FANC[0], DECK + 60.0, FANC[2]), 18, 6.0, m["vapour"], [2, 3, 4], 0.0, 0.85, 140.0, 70, (45.0, 45.0))
    run(root, "mk_flow", mk, 8, 2.6, m["makeup"], [3], 0.0, 0.75, 45)
    run(root, "bd_flow", bd, 4, 2.2, m["c_supply"], [3], 0.2, 0.8, 30)
    C.spin(dial, [3], turns=2.0)

    tags = {
        0: [("chiller condenser", (-165.0, 90.0, -60.0)), ("warm water out ~35 C", (-10.0, 150.0, -90.0)),
            ("cooled water back ~29 C", (0.0, 14.0, -40.0)), ("wet cooling tower", (TX1, DECK + 70.0, -60.0))],
        1: [("spray header + nozzles", (TX0 + 40.0, SPRAY, -8.0)), ("fill: thin water films", (FANC[0], FILL[1] - 10.0, -2.0)),
            ("air in through louvers", (TX0 - 4.0, 80.0, -4.0)), ("drift eliminators", (TX1 - 40.0, DRIFT[1], -3.0))],
        2: [("fan pulls air up", (FANC[0], DECK + 20.0, FANC[2])), ("~1% evaporates", (FANC[0], DECK + 140.0, FANC[2])),
            ("cools the rest ~6 C", (FANC[0] + 60.0, 40.0, -4.0))],
        3: [("make-up water meter", (TX1 + 61.0, 20.0, -40.0)), ("blowdown sheds minerals", (TX0 - 10.0, 6.0, 0.0)),
            ("~3M L/day per 100 MW", (FANC[0], DECK + 140.0, FANC[2]))],
        4: [("SPX Marley, EVAPCO, BAC", (TX1, DECK + 70.0, -60.0)), ("Modine, JCI, Trane", (-165.0, 90.0, -60.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((40.0, 130.0, -90.0), 600.0, 0.28, 0.30, pad=1.0),
        frame((FANC[0], 140.0, -60.0), 300.0, 0.10, 0.12),
        [(0.0, frame((FANC[0], 230.0, -80.0), 330.0, 0.25, 0.30)), (0.55, frame((FANC[0], 260.0, -90.0), 340.0, -0.15, 0.55))],
        frame((TX1 - 20.0, 60.0, -60.0), 330.0, 0.30, 0.30),
        frame((40.0, 150.0, -90.0), 640.0, -0.25, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
