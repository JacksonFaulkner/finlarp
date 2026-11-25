"""TRM_LNG: the Terms-tab overview for liquefied natural gas, built with the kit_supply parts.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_lng.py

Writes assets/term_TRM_LNG.glb. Captions live in specs/terms/TRM_LNG.json (same beat count).

A strip of coast: wellheads and a liquefaction train on the left, a Moss-sphere carrier crossing the
sea, then a regas terminal feeding a gas turbine and a data center hall on the right. The bench in
front shows the 600x shrink: a cloud of gas molecules beside the one small liquid block they become.

Beats:
  0 liquefy   field gas runs through compressors and a cold box, cooled to -162 C
  1 shrink    gas cloud vs the liquid it becomes: about 600 times smaller
  2 ship      a carrier with insulated spheres crosses the sea
  3 regas     the terminal warms it back to gas; a turbine powers the data hall
  4 price     long chain, few terminals: LNG prices pass through to power
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
import sand_overview as O  # noqa: E402
from term_common import F, bx, empty, show, spin  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_LNG"
BEATS = [
    ("LNG is natural gas chilled to -162 C until it turns liquid",
     "Gas from the field is cleaned of water, CO2 and heavy parts, then compressed and run through a cold box "
     "where refrigerant loops pull it down to about -162 C. At that temperature methane condenses into a clear "
     "liquid. A big liquefaction train burns roughly a tenth of its gas just running the compressors."),
    ("As a liquid it takes about 600 times less space",
     "The same molecules that fill 600 cubic meters as gas fit in one cubic meter as liquid. That shrink is the "
     "whole point: a pipeline cannot cross an ocean, but a tank of liquid can. The liquid must stay cold, so tanks "
     "are heavily insulated and a little boils off every day."),
    ("Carriers with insulated tanks ship it across oceans",
     "An LNG carrier holds about 170,000 cubic meters, in spherical Moss tanks or membrane tanks inside the hull. "
     "Boil-off gas often fuels the ship's own engines. A trip from the US Gulf to Europe takes around two weeks, "
     "to Asia about a month."),
    ("Terminals warm it back to gas for turbines and the grid",
     "At the import terminal, seawater or burners warm the liquid back into gas in vaporizers, and it enters the "
     "pipeline grid. Gas turbines turn it into electricity, and many new AI data centers are planned around "
     "gas-fired power, either from the grid or from turbines on site."),
    ("A long chain with few plants, so LNG prices reach power bills",
     "Liquefaction trains cost billions and take years to build, so supply is lumpy and a few export plants set "
     "the market. When LNG prices jump, power prices in importing regions follow, and that reaches the cost of "
     "running data centers. Related: Cheniere Energy (LNG), Venture Global (VG), Sempra (SRE)."),
]

SEA_Z0, SEA_Z1 = -110.0, 0.0
WELLS = [(-200.0, 0.0, -70.0), (-185.0, 0.0, -45.0)]
COMP = (-150.0, 0.0, -55.0)
COLD = (-118.0, 0.0, -55.0)
STORE = (-82.0, 0.0, -55.0)
REGAS = (95.0, 0.0, -55.0)
TURB = (135.0, 0.0, -55.0)
HALL = (190.0, 0.0, -55.0)
SHIP_Y = 1.0
SHIP_Z = -55.0
BENCH_Z = 30.0


def ship(m, root):
    """Hull, bridge and four Moss spheres. Returns the group (a pivot at the origin) and tag points."""
    g = empty("carrier", root)
    x0, x1 = -45.0, 45.0
    bx("hull", (x0, SHIP_Y, SHIP_Z - 9.0), (x1, SHIP_Y + 8.0, SHIP_Z + 9.0), m["lng_hull"], g)
    bx("hull_red", (x0, SHIP_Y - 1.0, SHIP_Z - 9.2), (x1, SHIP_Y + 1.5, SHIP_Z + 9.2), m["lng_red"], g)
    bx("bow", (x1, SHIP_Y + 1.0, SHIP_Z - 6.0), (x1 + 8.0, SHIP_Y + 8.0, SHIP_Z + 6.0), m["lng_hull"], g)
    bx("deck", (x0, SHIP_Y + 8.0, SHIP_Z - 8.5), (x1, SHIP_Y + 8.6, SHIP_Z + 8.5), m["sup_steel"], g)
    bx("bridge", (x0 + 1.0, SHIP_Y + 8.6, SHIP_Z - 6.0), (x0 + 8.0, SHIP_Y + 18.0, SHIP_Z + 6.0), m["white"], g)
    bx("funnel", (x0 + 2.0, SHIP_Y + 18.0, SHIP_Z - 1.5), (x0 + 5.0, SHIP_Y + 22.0, SHIP_Z + 1.5), m["lng_red"], g)
    tops = []
    for k in range(4):
        cx = x0 + 18.0 + k * 19.0
        O.ball(f"moss{k}", (cx, SHIP_Y + 13.0, SHIP_Z), 8.0, m["lng_moss"], g)
        bx(f"skirt{k}", (cx - 7.0, SHIP_Y + 8.6, SHIP_Z - 7.0), (cx + 7.0, SHIP_Y + 11.0, SHIP_Z + 7.0),
           m["sup_steel"], g)
        tops.append((cx, SHIP_Y + 21.0, SHIP_Z))
    # one sphere cut open: the cold liquid inside
    cut = empty("moss_cut", g)
    O.disc("moss_liquid", (x0 + 37.0, SHIP_Y + 22.5, SHIP_Z), 6.5, 0.6, m["sup_cryo"], cut)
    return g, tops


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    m["lng_sea"] = mat("lng_sea", (0.05, 0.16, 0.26), metal=0.0, rough=0.15)
    m["lng_hull"] = mat("lng_hull", (0.12, 0.13, 0.16), metal=0.3, rough=0.5)
    m["lng_red"] = mat("lng_red", (0.55, 0.10, 0.08), metal=0.0, rough=0.6)
    m["lng_moss"] = mat("lng_moss", (0.82, 0.80, 0.74), metal=0.2, rough=0.45)
    m["lng_win"] = mat("lng_win", (0.9, 0.8, 0.5), emit=(1.0, 0.8, 0.4), strength=3.0)

    # ground and sea
    bx("land_l", (-230.0, -3.0, -110.0), (-55.0, 0.0, 0.0), m["sup_steel"], root)
    bx("land_r", (65.0, -3.0, -110.0), (240.0, 0.0, 0.0), m["sup_steel"], root)
    bx("sea", (-55.0, -4.0, SEA_Z0), (65.0, -1.0, SEA_Z1), m["lng_sea"], root)
    bx("bench", (140.0, -3.0, 5.0), (250.0, 0.0, 60.0), m["sup_steel"], root)

    # export side: wells, compressors, cold box, storage
    for k, w in enumerate(WELLS):
        bx(f"well{k}", (w[0] - 2, 0, w[2] - 2), (w[0] + 2, 10, w[2] + 2), m["warn"], root)
        bx(f"well{k}_cap", (w[0] - 3.5, 10, w[2] - 3.5), (w[0] + 3.5, 12, w[2] + 3.5), m["sup_steel"], root)
    comps = []
    for k in range(3):
        cz = COMP[2] - 12 + k * 12
        O.tube(f"comp{k}", (COMP[0] - 9, 6, cz), (COMP[0] + 9, 6, cz), 4.5, m["sup_gas"], root, 24)
        fan = O.pivot(f"comp{k}_rot", (COMP[0] - 10.0, 6.0, cz), root)
        bx(f"comp{k}_blade", (-0.5, -4.0, -0.6), (0.5, 4.0, 0.6), m["sup_coil"], fan)
        spin(fan, [0], turns=4.0, axis=0)
        comps.append(fan)
    # cold box with its front cut away: refrigerant coils inside
    bx("coldbox_back", (COLD[0] - 10, 0, COLD[2] - 10), (COLD[0] + 10, 40, COLD[2] - 8), m["sup_steel"], root)
    bx("coldbox_l", (COLD[0] - 10, 0, COLD[2] - 10), (COLD[0] - 8, 40, COLD[2] + 10), m["sup_steel"], root)
    bx("coldbox_r", (COLD[0] + 8, 0, COLD[2] - 10), (COLD[0] + 10, 40, COLD[2] + 10), m["sup_steel"], root)
    bx("coldbox_top", (COLD[0] - 10, 40, COLD[2] - 10), (COLD[0] + 10, 42, COLD[2] + 10), m["sup_steel"], root)
    bx("coldbox_in", (COLD[0] - 8, 0, COLD[2] - 8), (COLD[0] + 8, 1, COLD[2] + 10), m["sup_pkg"], root)
    for j in range(6):
        K.ring(m, root, f"mcr{j}", (COLD[0], 6 + j * 5.5, COLD[2]), 6.0, 0.9,
               "sup_cryo" if j < 3 else "sup_coil", "z", 18)
    store_g, _, store_pts = K.dewar(m, root, "store", STORE, 16.0, 36.0)
    feed = [(WELLS[0][0], 6, WELLS[0][2]), (-200, 6, -55), (COMP[0] - 12, 6, -55)]
    feed2 = [(WELLS[1][0], 6, WELLS[1][2]), (-185, 6, -55)]
    to_cold = [(COMP[0] + 10, 6, -55), (COLD[0] - 10, 6, -55)]
    down = [(COLD[0], 37, COLD[2] + 7), (COLD[0], 4, COLD[2] + 7)]
    to_store = [(COLD[0] + 10, 6, -55), (STORE[0] - 16, 6, -55)]
    jetty = [(STORE[0] + 16, 6, -55), (-50, 6, -55), (-50, 8, -66)]
    for k, p in enumerate([feed, feed2, to_cold, to_store, jetty]):
        K.pipe(m, root, f"exp_pipe{k}", p, 1.4)
    run(root, "gas_in", feed, 4, 1.4, m["sup_flow"], [0], 0.0, 0.6, 30)
    run(root, "gas_in2", feed2, 3, 1.4, m["sup_flow"], [0], 0.05, 0.6, 25)
    run(root, "gas_comp", to_cold, 4, 1.4, m["sup_flow"], [0], 0.15, 0.8, 25)
    run(root, "chill", down, 6, 1.4, m["sup_he"], [0], 0.2, 0.9, 30)
    run(root, "liq_out", to_store, 4, 1.2, m["sup_cryo"], [0, 4], 0.3, 0.9, 25)
    rise(root, "comp_heat", (COMP[0], 12.0, COMP[2]), 8, 0.9, m["sup_hot"], [0], h=22.0, spread=(10.0, 12.0))

    # beat 1: the bench, gas cloud vs liquid block
    shrink = empty("shrink", root)
    K.cloud(m, shrink, "gas_cloud", (172.0, 22.0, BENCH_Z), 90, 18.0, 1.0, "sup_flow")
    bx("gas_box", (152.0, 2.0, BENCH_Z - 20.0), (192.0, 2.6, BENCH_Z + 20.0), m["sup_pkg"], shrink)
    bx("liq_block", (220.0, 0.0, BENCH_Z - 2.5), (225.0, 5.0, BENCH_Z + 2.5), m["sup_cryo"], shrink)
    bx("liq_pad", (214.0, 0.0, BENCH_Z - 8.0), (231.0, 0.4, BENCH_Z + 8.0), m["sup_pkg"], shrink)
    arrow = [(195.0, 12.0, BENCH_Z), (215.0, 6.0, BENCH_Z)]
    K.pipe(m, shrink, "shrink_arrow", arrow, 0.6, "sup_arrow_dn")
    show(shrink, [(F(1, 0), F(2, 0))])
    run(root, "condense", arrow, 6, 1.0, m["sup_cryo"], [1], 0.1, 0.9, 25)

    # beat 2: the carrier crosses the sea
    car, moss_tops = ship(m, root)
    O._interp("LINEAR")
    for f, x in [(0, -10.0), (F(2, 0), -10.0), (F(2, 0.95), 18.0), (F(5, 0) - 1, 18.0)]:
        car.location = (x, 0.0, 0.0)
        car.keyframe_insert("location", frame=f)
    wake = [(-55.0, 0.5, SHIP_Z + 3), (60.0, 0.5, SHIP_Z + 3)]
    run(root, "wake", wake, 6, 0.9, m["sup_he"], [2], 0.0, 0.9, 35)
    boil = rise(root, "boiloff", (moss_tops[1][0] + 14.0, moss_tops[1][1], SHIP_Z), 6, 0.8, m["sup_cryo"], [2],
                h=14.0, spread=(30.0, 4.0))

    # import side: regas vaporizers, turbine, hall
    for k in range(4):
        x = REGAS[0] - 12 + k * 8
        bx(f"vap{k}", (x - 2.5, 0, REGAS[2] - 8), (x + 2.5, 24, REGAS[2] + 8), m["sup_gas"], root)
        for j in range(5):
            bx(f"vap{k}_fin{j}", (x - 3.2, 3 + j * 4.5, REGAS[2] - 8.2), (x + 3.2, 4 + j * 4.5, REGAS[2] + 8.2),
               m["sup_steel"], root)
    ig, ipts = K.tank(m, root, "imp_tank", (REGAS[0] - 22, 0, REGAS[2] - 28), 12.0, 26.0)
    bx("turb_hall", (TURB[0] - 12, 0, TURB[2] - 10), (TURB[0] + 12, 18, TURB[2] + 10), m["white"], root)
    O.tube("turb_body", (TURB[0] - 10, 9, TURB[2] + 11), (TURB[0] + 10, 9, TURB[2] + 11), 5.0, m["sup_gas"], root, 24)
    bx("stack", (TURB[0] + 6, 18, TURB[2] - 4), (TURB[0] + 11, 34, TURB[2] + 1), m["sup_steel"], root)
    bx("hall", (HALL[0] - 30, 0, HALL[2] - 20), (HALL[0] + 30, 16, HALL[2] + 20), m["lng_hull"], root)
    wins = empty("hall_wins", root)
    for k in range(8):
        x = HALL[0] - 26 + k * 7.2
        bx(f"win{k}", (x, 5, HALL[2] + 20), (x + 5, 11, HALL[2] + 20.5), m["lng_win"], wins)
    for k in range(3):
        bx(f"chiller{k}", (HALL[0] - 24 + k * 18, 16, HALL[2] - 12), (HALL[0] - 12 + k * 18, 20, HALL[2] + 4),
           m["sup_steel"], root)
    unload = [(68, 8, -66), (REGAS[0] - 16, 6, -55)]
    gas_out = [(REGAS[0] + 16, 6, -55), (TURB[0] - 12, 6, -55)]
    wire = [(TURB[0] + 12, 14, -55), (HALL[0] - 30, 14, -55)]
    K.pipe(m, root, "imp_pipe0", unload, 1.4)
    K.pipe(m, root, "imp_pipe1", gas_out, 1.4)
    K.pipe(m, root, "hv_line", wire, 0.5, "sup_coil")
    run(root, "unload", unload, 4, 1.2, m["sup_cryo"], [3], 0.0, 0.6, 20)
    run(root, "regas_out", gas_out, 5, 1.3, m["sup_flow"], [3, 4], 0.15, 0.85, 22)
    run(root, "power", wire, 6, 1.0, m["sup_he"], [3, 4], 0.3, 0.95, 18)
    rise(root, "exhaust", (TURB[0] + 8.5, 34.0, TURB[2] - 1.5), 6, 1.0, m["sup_hot"], [3, 4], h=18.0)
    for b in (3, 4):
        blink(wins, b, [0, 1, 2, 3, 4, 5, 6], n=8, on=0.6)

    tags = {
        0: [("field gas in", (-200.0, 12.0, -70.0)), ("compressors", (COMP[0], 12.0, COMP[2])),
            ("cold box: -162 C", (COLD[0], 40.0, COLD[2])), ("liquid to storage", store_pts["liquid"])],
        1: [("gas: 600 m3", (172.0, 42.0, BENCH_Z)), ("liquid: 1 m3", (222.5, 6.0, BENCH_Z)),
            ("same molecules", (205.0, 12.0, BENCH_Z))],
        2: [("~170,000 m3 carrier", moss_tops[0]), ("Moss sphere: insulated", moss_tops[2]),
            ("boil-off fuels engines", moss_tops[3])],
        3: [("vaporizers warm it", (REGAS[0], 24.0, REGAS[2])), ("gas turbine", (TURB[0], 34.0, TURB[2])),
            ("AI data hall", (HALL[0], 20.0, HALL[2]))],
        4: [("trains: years, billions", (COLD[0], 40.0, COLD[2])), ("LNG, VG, SRE", moss_tops[1]),
            ("price passes to power", (HALL[0], 20.0, HALL[2]))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-140.0, 15.0, -55.0), 130.0, 0.35, 0.35),
        frame((195.0, 15.0, BENCH_Z), 100.0, 0.20, 0.25),
        frame((10.0, 12.0, -55.0), 130.0, 0.30, 0.30),
        frame((150.0, 12.0, -55.0), 140.0, 0.30, 0.35),
        frame((0.0, 15.0, -55.0), 330.0, 0.20, 0.40),
    ], root)


if __name__ == "__main__":
    build()
