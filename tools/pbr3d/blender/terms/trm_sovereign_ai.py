"""TRM_SOVEREIGN_AI: the Terms-tab overview for national (sovereign) AI compute.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_sovereign_ai.py

A country on the floor, ringed by a low border wall with one customs gate. Inside: a national
GPU hall (racks), a government building whose budget coins fund it, a telecom tower, and local
data (blue beads) that loops between citizens' towns and the hall without leaving the border.
Outside: a supplier dock with crates of GPUs that wait at the gate for an export license
(red lamp) and then roll in (green lamp).

Beats:
  0 nation   compute built inside the country's borders
  1 data     data stays at home: residency and language
  2 budget   the state (or national telecom) pays
  3 license  lumpy deals gated by export licenses
  4 who      suppliers
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat  # noqa: E402
from power_vrm_detail import frame, run, blink, present  # noqa: E402
import kit_ledger as K  # noqa: E402
import trm_neocloud as N  # noqa: E402

SLUG = "TRM_SOVEREIGN_AI"
BEATS = [
    ("A nation builds AI compute on its own soil",
     "Sovereign AI is a government, or a national champion it backs, building GPU data centers and AI models inside "
     "its own borders under local control. Examples include national clouds in Saudi Arabia, the UAE, France, Japan and India."),
    ("Data and models stay inside the border",
     "Countries want citizens' and government data processed at home, under their own laws. They also want models trained "
     "on their own languages and culture rather than relying on a few US companies for a strategic technology."),
    ("The state budget is the customer",
     "The money often comes from state budgets, sovereign wealth funds or national telecoms. For suppliers this is a new "
     "customer class beyond the US hyperscalers, sometimes worth billions per country."),
    ("Deals are lumpy and wait on export licenses",
     "Orders arrive as a few very large projects, so supplier revenue jumps around by quarter. Advanced US GPUs need export "
     "licenses for many countries, and a deal can sit at the border until approval comes."),
    ("Chip, cloud and network suppliers benefit",
     "NVIDIA sells the GPUs and full systems, Oracle and others run sovereign cloud regions, and Dell, HPE, Cisco build "
     "and network the halls. Related: NVDA, ORCL, CSCO, DELL."),
]

R = 130.0  # border radius
GATE_A = 0.0  # gate angle (towards +x)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    N.mats(m)
    m["land"] = mat("sv_land", (0.20, 0.27, 0.20), rough=0.9)
    m["sea"] = mat("sv_sea", (0.10, 0.16, 0.24), metal=0.2, rough=0.3)
    m["wall2"] = mat("sv_wall", (0.55, 0.52, 0.46), rough=0.7)
    m["gov"] = mat("sv_gov", (0.78, 0.76, 0.70), rough=0.6)
    m["town"] = mat("sv_town", (0.45, 0.42, 0.40), rough=0.7)
    m["flag"] = mat("sv_flag", (0.85, 0.25, 0.20), rough=0.6)
    m["red_l"] = mat("sv_red", (1.0, 0.15, 0.1), emit=(1.0, 0.15, 0.1), strength=4.0)
    m["grn_l"] = mat("sv_grn", (0.2, 1.0, 0.3), emit=(0.2, 1.0, 0.3), strength=4.0)

    bx("sea", (-300.0, -4.0, -220.0), (320.0, -2.0, 200.0), m["sea"], root)
    D.tube("land", (0.0, -2.0, 0.0), (0.0, 0.0, 0.0), R + 6.0, m["land"], root, 48)
    # border wall: segments round the circle, gap at the gate
    n = 40
    for k in range(n):
        a = 2 * math.pi * k / n
        if abs(math.atan2(math.sin(a - GATE_A), math.cos(a - GATE_A))) < 0.12:
            continue
        x, z = R * math.cos(a), R * math.sin(a)
        D.tube(f"wall{k}", (x, 0.0, z), (x, 9.0, z), 6.5, m["wall2"], root, 8)
    # gate posts and lamps
    gx = R
    for s in (-1, 1):
        bx(f"gate_post{s}", (gx - 3.0, 0.0, s * 15.0 - 3.0), (gx + 3.0, 22.0, s * 15.0 + 3.0), m["wall2"], root)
    red = empty("g_red", root); bx("lamp_red", (gx - 2.0, 22.0, -17.0), (gx + 2.0, 26.0, -13.0), m["red_l"], red)
    grn = empty("g_grn", root); bx("lamp_grn", (gx - 2.0, 22.0, 13.0), (gx + 2.0, 26.0, 17.0), m["grn_l"], grn)
    present(red, [(F(3, 0), F(3, 0.55))])
    present(grn, [(F(3, 0.55), F(5, 0))])
    barrier = empty("g_bar", root); bx("barrier", (gx - 1.0, 12.0, -13.0), (gx + 1.0, 14.0, 13.0), m["flag"], barrier)
    present(barrier, [(F(0, 0), F(3, 0.55))])

    # national GPU hall
    bx("hall_floor", (-50.0, 0.0, -40.0), (50.0, 1.0, 10.0), m["floor"], root)
    bx("hall_back", (-50.0, 0.0, -42.0), (50.0, 64.0, -40.0), m["wall"], root)
    leds = empty("leds", root)
    for r, z in enumerate((-26.0, -2.0)):
        for i in range(7):
            N.gpu_rack(m, root, f"rk{r}_{i}", -42.0 + 14.0 * i, z, leds, spine=(i == 0))
    blink(leds, 0, [0, 2, 4, 6], n=8, on=0.9)
    # government building + flag
    bx("gov", (-100.0, 0.0, 30.0), (-60.0, 30.0, 60.0), m["gov"], root)
    for k in range(6):
        D.tube(f"col{k}", (-97.0 + 7.0 * k, 0.0, 62.0), (-97.0 + 7.0 * k, 28.0, 62.0), 1.4, m["gov"], root, 8)
    D.tube("dome", (-80.0, 30.0, 45.0), (-80.0, 40.0, 45.0), 10.0, m["gov"], root, 24)
    D.tube("pole", (-80.0, 40.0, 45.0), (-80.0, 70.0, 45.0), 0.6, m["steel"], root, 6)
    flag = empty("g_flag", root); bx("flag", (-80.0, 60.0, 45.0), (-64.0, 69.0, 45.6), m["flag"], flag)
    C.wiggle(flag, [0, 1, 2, 3, 4], amp=(0.0, 0.0, 0.8), period=8)
    # telecom tower
    D.tube("tower", (70.0, 0.0, -70.0), (70.0, 80.0, -70.0), 1.6, m["steel"], root, 6)
    for k in range(3):
        bx(f"ant{k}", (68.0, 66.0 + 5 * k, -72.0), (72.0, 69.0 + 5 * k, -68.0), m["steel"], root)
    # towns
    towns = [(-40.0, 90.0), (40.0, 80.0), (-100.0, -50.0), (20.0, -95.0)]
    for t, (x, z) in enumerate(towns):
        for k in range(5):
            h = 6.0 + 4.0 * ((k * 7 + t) % 4)
            bx(f"town{t}_{k}", (x + (k % 3) * 7.0, 0.0, z + (k // 3) * 7.0), (x + (k % 3) * 7.0 + 5.0, h, z + (k // 3) * 7.0 + 5.0),
               m["town"], root)
    # data residency: beads loop towns <-> hall, inside the wall
    for t, (x, z) in enumerate(towns):
        run(root, f"data{t}", [(x, 10.0, z), (x * 0.5, 30.0, z * 0.5 - 10.0), (0.0, 50.0, -15.0)], 8, 2.2, m["ldg_blue_b"],
            [0, 1, 4], 0.05 * t, 0.85, 40)
    # budget coins (beat 2)
    gc = K.coin_row(m, root, "budget", -120.0, 15.0, 10.0, [14, 18, 12], r=4.5, h=1.6)
    present(gc, [(F(2, 0), F(5, 0))])
    run(root, "funds", [(-100.0, 30.0, 20.0), (-60.0, 50.0, 0.0), (-20.0, 40.0, -10.0)], 14, 2.6, m["ldg_gold_b"], [2], 0.0, 0.85, 40)
    run(root, "telco", [(70.0, 60.0, -70.0), (40.0, 50.0, -40.0), (20.0, 40.0, -15.0)], 8, 2.2, m["ldg_gold_b"], [2], 0.2, 0.85, 40)

    # supplier dock outside, crates wait then roll in (beat 3)
    bx("dock", (190.0, -2.0, -40.0), (260.0, 4.0, 40.0), m["wall"], root)
    crates = K.order_stack(m, root, "crates", (0.0, 4.0, 0.0), 2, 2, "ldg_crate", s=10.0)
    dock_p, gate_p, hall_p = (220.0, 4.0, 0.0), (gx + 22.0, 0.0, 0.0), (60.0, 0.0, 0.0)
    C.key(crates, F(0, 0), "location", C.P(*dock_p))
    C.key(crates, F(3, 0.1), "location", C.P(*gate_p))
    C.key(crates, F(3, 0.55), "location", C.P(*gate_p))
    C.key(crates, F(3, 0.85), "location", C.P(*hall_p))
    C.key(crates, F(4, 0.99), "location", C.P(*hall_p))
    sheet = K.ledger_sheet(m, root, "license", (gx + 30.0, 30.0, 25.0), 16.0, 20.0, 4)
    present(sheet, [(F(3, 0), F(4, 0))])

    C.tags(root, {
        0: [("national GPU hall", (0.0, 75.0, -20.0)), ("inside the border", (60.0, 20.0, 100.0))],
        1: [("data stays at home", (-40.0, 40.0, 90.0)), ("local-language models", (0.0, 70.0, -20.0))],
        2: [("state budget pays", (-80.0, 78.0, 45.0)), ("national telecom", (70.0, 90.0, -70.0))],
        3: [("export license needed", (gx + 30.0, 46.0, 25.0)), ("lumpy, big deals", (220.0, 30.0, 0.0))],
        4: [("NVDA ORCL", (0.0, 80.0, -20.0)), ("CSCO DELL", (gx + 20.0, 40.0, 0.0))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 20.0, 0.0), 340.0, 0.30, 0.65, pad=1.0),
        frame((-20.0, 25.0, 20.0), 240.0, -0.20, 0.55),
        frame((-60.0, 30.0, 10.0), 200.0, 0.40, 0.40),
        frame((170.0, 20.0, 0.0), 180.0, -0.35, 0.35),
        frame((40.0, 30.0, 0.0), 340.0, -0.25, 0.55, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
