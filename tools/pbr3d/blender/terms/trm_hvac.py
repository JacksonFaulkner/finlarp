"""TRM_HVAC: the whole-building climate loop of a data center, cut open.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_hvac.py

No GPU board. Units cm (model scale, not true scale). Unlike trm_chiller (one machine), this is the
building: a two-storey shell with its front wall cut away at z = 0. Ground floor: the data hall
(rack rows) and, to the right, the chiller plant (two chillers, pumps). Upper floor: an office with
its own small air handler. Roof: a big air handler (outside-air dampers, filters, coil, fan) with
ducts down to the hall, and cooling towers taking the condenser water. At the left, a power meter
with two bars: IT load and the cooling/HVAC share of the site's power.

Beats:
  0 building   HVAC = everything that sets temperature, humidity and fresh air
  1 air side   roof AHU mixes outside air, filters, cools, fans it down to the hall
  2 water side chillers make cold water for the coils; towers dump the heat
  3 power      cooling is the biggest non-IT load: meter bars, PUE
  4 capacity   cooling capacity caps the site's megawatts; who sells it
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

SLUG = "TRM_HVAC"
BEATS = [
    ("HVAC is the building's whole climate system",
     "Heating, ventilation and air conditioning covers every machine that sets a building's temperature, humidity "
     "and fresh air: rooftop air handlers, ducts, chillers, pumps, cooling towers and their controls. In a data "
     "center it is the room- and building-level layer; chip-level liquid loops plug into it rather than replace it."),
    ("Air side: handlers mix, filter, cool and push the air",
     "An air handler draws return air and some outdoor air through dampers, filters it, passes it over a chilled-water "
     "coil and fans it through ducts to the hall. On cool days it can use outside air directly (economiser mode) and "
     "skip mechanical cooling. Offices and support rooms get their own smaller units."),
    ("Water side: chillers make the cold, towers throw it away",
     "Chillers in the plant room cool a water loop that pumps feed to every coil in the building. The heat they pull "
     "out goes into a second, condenser-water loop that runs up to cooling towers on the roof, where evaporation dumps "
     "it to the sky. Air-cooled sites swap the towers for dry coolers and use no water."),
    ("Cooling is the biggest power draw after the servers",
     "Power usage effectiveness (PUE) is total site power over IT power. A modern hall runs about 1.2 to 1.4, older "
     "ones 1.6 or more, and most of that overhead is HVAC: compressors, fans and pumps. Every 0.1 of PUE on a 100 MW "
     "campus is 10 MW that could have run GPUs."),
    ("Cooling capacity often sets a site's megawatts",
     "Each MW of IT becomes a MW of heat, so a site can only host as much compute as its plant can reject, on the "
     "hottest day, with a unit spare. Denser AI racks push more of the load onto liquid, but the building loop still "
     "carries it out. Suppliers: Trane Technologies (TT), Carrier (CARR), Johnson Controls (JCI), Lennox (LII)."),
]

# layout (cm): building x -300..400, z -220..0, ground floor y 0..160, upper 160..260, roof at 260
BX0, BX1, BZ0 = -300.0, 400.0, -220.0
G1, G2 = 230.0, 330.0
HALL1 = 160.0  # hall x < HALL1, plant room x > HALL1
MX = -400.0  # meter


def mats(m):
    K.mats(m)
    m["duct"] = mat("hv_duct", (0.74, 0.76, 0.78), metal=0.8, rough=0.35)
    m["filter"] = mat("hv_filter", (0.88, 0.86, 0.72), rough=0.95)
    m["tower"] = mat("hv_tower", (0.40, 0.48, 0.52), metal=0.3, rough=0.5)
    m["fill"] = mat("hv_fill", (0.82, 0.84, 0.80), rough=0.8)
    m["office"] = mat("hv_office", (0.55, 0.45, 0.32), rough=0.7)
    m["air_c"] = mat("hv_air_c", (0.40, 0.75, 1.0), emit=(0.30, 0.70, 1.0), strength=3.0)
    m["air_w"] = mat("hv_air_w", (1.0, 0.60, 0.25), emit=(1.0, 0.52, 0.18), strength=3.0)
    m["air_o"] = mat("hv_air_o", (0.55, 1.0, 0.70), emit=(0.45, 1.0, 0.60), strength=3.0)
    m["cond"] = mat("hv_cond", (1.0, 0.35, 0.20), emit=(1.0, 0.30, 0.15), strength=3.5)
    m["vapor"] = mat("hv_vapor", (0.85, 0.88, 0.92), emit=(0.80, 0.85, 0.92), strength=1.6)
    m["bar_it"] = mat("hv_bar_it", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=1.3)
    m["bar_cool"] = mat("hv_bar_cool", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=1.3)
    m["bar_oth"] = mat("hv_bar_oth", (1.0, 0.70, 0.25), emit=(1.0, 0.65, 0.20), strength=1.3)


def shell(m, root):
    g = empty("shell", root)
    bx("pad", (BX0 - 30.0, -6.0, BZ0 - 30.0), (BX1 + 30.0, 0.0, 20.0), m["concrete"], g)
    bx("back", (BX0, 0.0, BZ0), (BX1, G2, BZ0 + 6.0), m["wall"], g)
    bx("lw", (BX0, 0.0, BZ0), (BX0 + 6.0, G2, 0.0), m["wall"], g)
    bx("rw", (BX1 - 6.0, 0.0, BZ0), (BX1, G2, 0.0), m["wall"], g)
    bx("mid", (HALL1, 0.0, BZ0), (HALL1 + 6.0, G1, 0.0), m["wall"], g)
    bx("slab1", (BX0, G1, BZ0), (BX1, G1 + 6.0, 0.0), m["concrete"], g)
    bx("roof", (BX0, G2, BZ0), (BX1, G2 + 6.0, 0.0), m["concrete"], g)
    # office upstairs: desks
    for k in range(5):
        x = -260.0 + 60.0 * k
        bx(f"desk{k}", (x, G1 + 30.0, -120.0), (x + 40.0, G1 + 33.0, -80.0), m["office"], g)
        bx(f"mon{k}", (x + 10.0, G1 + 33.0, -112.0), (x + 30.0, G1 + 48.0, -108.0), m["screen"], g)
    bx("off_ahu", (280.0, G1 + 6.0, -200.0), (380.0, G1 + 70.0, -150.0), m["skin"], g)
    leds = empty("leds", root)
    for row, z0 in enumerate((-200.0, -100.0)):
        for k in range(6):
            K.rack(m, g, f"rk{row}{k}", -280.0 + 70.0 * k, z0, w=56.0, dep=70.0, h=210.0, leds=leds)
    return leds


def plant(m, root):
    g = empty("plant", root)
    pts = {}
    for k, z in enumerate((-170.0, -80.0)):
        x0, x1 = HALL1 + 30.0, BX1 - 40.0
        tube(f"ch_ev{k}", (x0, 30.0, z), (x1, 30.0, z), 18.0, m["shell"], g, 24)
        tube(f"ch_cd{k}", (x0, 74.0, z), (x1, 74.0, z), 16.0, m["steel"], g, 24)
        tube(f"ch_cmp{k}", (x0 + 60.0, 104.0, z), (x0 + 130.0, 104.0, z), 13.0, m["motor"], g, 20)
        bx(f"ch_box{k}", (x1 - 10.0, 96.0, z - 14.0), (x1 + 10.0, 130.0, z + 14.0), m["dark"], g)
    for k in range(3):
        x = HALL1 + 30.0 + 22.0 * k
        tube(f"pump{k}", (x, 0.0, -20.0), (x, 22.0, -20.0), 8.0, m["motor"], g, 16)
    # chilled water: plant -> up through the floors -> roof AHU coil; return down
    chw_s = [(HALL1 + 30.0, 30.0, -80.0), (HALL1 + 20.0, 30.0, -40.0), (HALL1 + 20.0, G2 + 40.0, -40.0), (60.0, G2 + 40.0, -60.0)]
    chw_r = [(40.0, G2 + 20.0, -140.0), (HALL1 + 40.0, G2 + 20.0, -140.0), (HALL1 + 40.0, 40.0, -140.0), (HALL1 + 30.0, 40.0, -170.0)]
    # condenser water: chiller condenser -> roof towers -> back
    cw_s = [(BX1 - 40.0, 74.0, -80.0), (BX1 - 20.0, 74.0, -30.0), (BX1 - 20.0, G2 + 20.0, -30.0), (330.0, G2 + 20.0, -60.0),
            (330.0, G2 + 80.0, -90.0)]
    cw_r = [(260.0, G2 + 12.0, -110.0), (BX1 - 30.0, G2 + 12.0, -190.0), (BX1 - 30.0, 74.0, -190.0), (BX1 - 40.0, 74.0, -170.0)]
    for n, p_, mt in (("chws", chw_s, "pipe_s"), ("chwr", chw_r, "pipe_r"), ("cws", cw_s, "pipe_r"), ("cwr", cw_r, "pipe_s")):
        polyline(n, p_, 3.0, m[mt], g)
        pts[n] = p_
    return pts


def roof(m, root):
    g = empty("roofkit", root)
    y0 = G2 + 6.0
    # main AHU: box x -220..120, z -170..-30, front skin cut away
    a0, a1, az0, az1, ah = -220.0, 120.0, -170.0, -30.0, 90.0
    bx("ahu_back", (a0, y0, az0), (a1, y0 + ah, az0 + 3.0), m["skin"], g)
    bx("ahu_base", (a0, y0, az0), (a1, y0 + 4.0, az1), m["frame"], g)
    # dampers on the left end (outside air + return)
    damp = []
    for k in range(8):
        y = y0 + 10.0 + 9.0 * k
        damp.append(bx(f"od{k}", (a0 - 3.0, y, az0 + 6.0), (a0 + 2.0, y + 3.0, az1 - 6.0), m["frame"], g))
    D.join(damp, "oa_damper")
    filt = []
    for k in range(5):
        x = a0 + 40.0 + 6.0 * k
        filt.append(bx(f"af{k}", (x, y0 + 8.0, az0 + 6.0), (x + 3.0, y0 + ah - 8.0, az1 - 6.0), m["filter"], g))
    D.join(filt, "ahu_filters")
    fins = []
    for k in range(18):
        x = a0 + 110.0 + 2.6 * k
        fins.append(bx(f"acf{k}", (x, y0 + 8.0, az0 + 6.0), (x + 0.8, y0 + ah - 8.0, az1 - 6.0), m["fin"], g))
    D.join(fins, "ahu_coil")
    fanhub = K.fan(m, g, "ahu_fan", (a0 + 230.0, y0 + 10.0, -100.0), r=26.0)
    # supply duct down into the hall, return duct up
    polyline("duct_s", [(80.0, y0, -100.0), (80.0, G1 + 10.0, -100.0), (80.0, G1 - 10.0, -150.0), (-280.0, G1 - 10.0, -150.0)], 9.0, m["duct"], g)
    polyline("duct_r", [(-260.0, G1 - 10.0, -30.0), (-250.0, y0 + 10.0, -30.0), (a0 - 10.0, y0 + 40.0, -60.0)], 8.0, m["duct"], g)
    # cooling towers (two cells): casing, fill pack, fan on top
    tfans = []
    for k, x in enumerate((240.0, 330.0)):
        bx(f"tw_b{k}", (x - 40.0, y0, -200.0), (x + 40.0, y0 + 100.0, -197.0), m["tower"], g)
        bx(f"tw_l{k}", (x - 40.0, y0, -200.0), (x - 37.0, y0 + 100.0, -40.0), m["tower"], g)
        bx(f"tw_r{k}", (x + 37.0, y0, -200.0), (x + 40.0, y0 + 100.0, -40.0), m["tower"], g)
        bx(f"tw_basin{k}", (x - 40.0, y0, -200.0), (x + 40.0, y0 + 10.0, -40.0), m["tower"], g)
        fl = []
        for j in range(10):
            y = y0 + 25.0 + 5.0 * j
            fl.append(bx(f"tw_f{k}{j}", (x - 36.0, y, -196.0), (x + 36.0, y + 2.4, -44.0), m["fill"], g))
        D.join(fl, f"tw_fill{k}")
        bx(f"tw_deck{k}", (x - 40.0, y0 + 97.0, -200.0), (x + 40.0, y0 + 100.0, -40.0), m["frame"], g)
        tfans.append(K.fan(m, g, f"tw_fan{k}", (x, y0 + 100.0, -120.0), r=30.0))
    return {"fan": fanhub, "tfans": tfans, "y0": y0}


def meter(m, root):
    """Power meter at the left: three stacked bars (IT, cooling, other) on a plinth."""
    g = empty("meter", root)
    bx("m_base", (MX - 40.0, 0.0, -140.0), (MX + 40.0, 6.0, -60.0), m["frame"], g)
    bx("m_panel", (MX - 40.0, 6.0, -140.0), (MX + 40.0, 260.0, -136.0), m["dark"], g)
    bars = {}
    # IT 100 units of height 150, cooling ~30% (45), other ~8% (12) -> PUE ~1.38
    for k, (name, y0, y1, mt) in enumerate((("it", 6.0, 156.0, "bar_it"), ("cool", 158.0, 203.0, "bar_cool"),
                                             ("oth", 205.0, 217.0, "bar_oth"))):
        grp = empty(f"bar_{name}", root)
        bx(f"bar_{name}_m", (MX - 25.0, y0, -130.0), (MX + 25.0, y1, -100.0), m[mt], grp)
        bars[name] = grp
    for y in range(6, 230, 15):
        bx(f"tick{y}", (MX - 35.0, y, -135.0), (MX - 28.0, y + 1.0, -133.0), m["ink"], g)
    return bars


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    leds = shell(m, root)
    p = plant(m, root)
    r = roof(m, root)
    bars = meter(m, root)
    for b in range(5):
        blink(leds, b, [0, 2, 4, 6], n=8, on=0.7)
    for f_ in [r["fan"]] + r["tfans"]:
        C.spin(f_, [0, 1, 2, 3, 4], turns=3.0)
    allb = [0, 1, 2, 3, 4]
    y0 = r["y0"]
    # air side
    oa = [(-300.0, y0 + 50.0, -100.0), (-222.0, y0 + 50.0, -100.0), (-120.0, y0 + 50.0, -100.0)]
    supply = [(-120.0, y0 + 45.0, -100.0), (0.0, y0 + 45.0, -100.0), (80.0, y0 + 20.0, -100.0), (80.0, G1 + 10.0, -100.0),
              (80.0, G1 - 10.0, -150.0), (-280.0, G1 - 10.0, -150.0), (-200.0, 40.0, -140.0)]
    ret = [(-100.0, 130.0, -60.0), (-260.0, G1 - 10.0, -30.0), (-250.0, y0 + 10.0, -30.0), (-222.0, y0 + 40.0, -60.0)]
    run(root, "a_oa", oa, 6, 3.5, m["air_o"], [1], 0.0, 0.7, 40)
    run(root, "a_sup", supply, 14, 4.0, m["air_c"], allb, 0.0, 0.8, 70)
    run(root, "a_ret", ret, 10, 4.0, m["air_w"], allb, 0.05, 0.8, 55)
    for k in range(6):
        rise(root, f"rk_heat{k}", (-252.0 + 70.0 * k, 210.0, -100.0), 3, 2.2, m["heat"], [0, 3], 0.0, 0.8, 25.0, 35, (14.0, 4.0))
    # water side
    run(root, "chws", p["chws"], 10, 3.6, m["c_supply"], [0, 2, 3, 4], 0.0, 0.75, 60)
    run(root, "chwr", p["chwr"], 10, 3.6, m["c_return"], [0, 2, 3, 4], 0.05, 0.8, 60)
    run(root, "cws", p["cws"], 10, 3.6, m["cond"], [2, 3, 4], 0.05, 0.75, 55)
    run(root, "cwr", p["cwr"], 8, 3.4, m["c_supply"], [2, 3, 4], 0.1, 0.8, 55)
    for k, x in enumerate((240.0, 330.0)):
        rise(root, f"vap{k}", (x, y0 + 110.0, -120.0), 8, 3.4, m["vapor"], [2, 4], 0.0, 0.85, 70.0, 50, (16.0, 16.0))
        drops = [(x - 20.0, y0 + 90.0, -100.0), (x - 20.0, y0 + 12.0, -100.0)]
        run(root, f"drop{k}", drops, 6, 1.4, m["c_supply"], [2], 0.0, 0.9, 20)
    # meter bars: IT always; cooling + other grow in beat 3
    show(bars["it"], [(F(0, 0), F(5, 0))])
    show(bars["cool"], [(F(3, 0.15), F(5, 0))])
    show(bars["oth"], [(F(3, 0.35), F(5, 0))])

    tags = {
        0: [("rooftop air handler", (-50.0, y0 + 100.0, -100.0)), ("cooling towers", (285.0, y0 + 110.0, -120.0)),
            ("data hall", (-120.0, 120.0, -30.0)), ("chiller plant", (280.0, 130.0, -80.0)), ("office: own small unit", (-150.0, G1 + 50.0, -100.0))],
        1: [("dampers: outside + return air", (-222.0, y0 + 85.0, -100.0)), ("filters, then cold coil", (-160.0, y0 + 95.0, -60.0)),
            ("supply fan", (10.0, y0 + 30.0, -100.0)), ("ducts down to the hall", (80.0, G1 + 40.0, -100.0))],
        2: [("chillers make cold water", (280.0, 50.0, -80.0)), ("pumps", (HALL1 + 52.0, 22.0, -20.0)),
            ("condenser water to roof", (BX1 - 20.0, 200.0, -30.0)), ("towers evaporate heat away", (285.0, y0 + 160.0, -120.0))],
        3: [("IT load", (MX + 25.0, 80.0, -100.0)), ("cooling ~20-35% on top", (MX + 25.0, 180.0, -100.0)),
            ("PUE = total / IT ~1.2-1.4", (MX, 240.0, -100.0))],
        4: [("heat rejection caps MW", (285.0, y0 + 110.0, -120.0)), ("Trane, Carrier, JCI, Lennox", (-50.0, y0 + 100.0, -100.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-20.0, 220.0, -110.0), 900.0, 0.25, 0.30, pad=1.0),
        [(0.0, frame((-90.0, y0 + 40.0, -100.0), 400.0, 0.20, 0.35)), (0.55, frame((-100.0, 260.0, -110.0), 520.0, 0.10, 0.20))],
        [(0.0, frame((280.0, 90.0, -100.0), 300.0, 0.30, 0.12)), (0.5, frame((280.0, 300.0, -110.0), 420.0, 0.20, 0.30))],
        frame((-260.0, 160.0, -100.0), 500.0, 0.15, 0.10),
        frame((-20.0, 220.0, -110.0), 960.0, -0.20, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
