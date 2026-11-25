"""TRM_GAS_TURBINE: a combined-cycle gas plant yard, and one gas turbine cut open on the bench.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_gas_turbine.py

Writes assets/term_TRM_GAS_TURBINE.glb. Captions live in specs/terms/TRM_GAS_TURBINE.json.

Beats:
  0 yard      the plant: gas turbine, generator, HRSG, stack, steam turbine
  1 cut open  one turbine cut open on the bench: compressor, combustor, turbine on one shaft
  2 burn      air through the compressor, fuel lit in the cans, hot gas through the turbine blades
  3 power     the generator turns the shaft; current runs out to the grid
  4 steam     exhaust heat makes steam: the second turbine
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_plant as K  # noqa: E402
from sand_overview import F  # noqa: E402
from power_vrm_detail import frame, run, rise, present  # noqa: E402

SLUG = "TRM_GAS_TURBINE"
BEATS = [
    ("A gas turbine burns gas to spin a generator",
     "A gas turbine burns natural gas to spin a generator. Add a steam turbine fed by its exhaust heat and the plant "
     "becomes a combined cycle, which gets more power out of the same fuel. It is the fastest firm power a data "
     "center can add, whether from the grid or built on site behind the meter."),
    ("Cut open: compressor, combustor and turbine on one shaft",
     "Air is squeezed through the compressor's blade rings and then goes into the combustor. The turbine's blades "
     "sit on the same shaft downstream, so part of the turbine's work drives the compressor and the rest turns the "
     "generator."),
    ("Air in, fuel lit, hot gas spins the blades",
     "Fuel is injected into the compressed air in the combustor cans and lit. The hot gas expands fast through the "
     "turbine blades, which are nickel superalloys and are cooled with air bled off the compressor, since the flame "
     "is far hotter than the metal can take."),
    ("The generator turns the shaft into grid power",
     "The generator sits on the same shaft. Its spinning rotor induces current in the stator windings, which runs out "
     "through a transformer to the grid or straight to a data center on site."),
    ("Exhaust heat makes steam for a second turbine",
     "The exhaust still carries a lot of heat. A heat recovery steam generator (HRSG) turns it into steam for a steam "
     "turbine, adding a second generator and lifting the plant's efficiency. Turbine order books now run years out "
     "on AI load. Related: GE Vernova (GEV), Siemens Energy (ENR), Mitsubishi Heavy (MHVYF), Caterpillar (CAT)."),
]

# yard
PAD = (-300.0, 250.0, -140.0, 60.0)
YT = (-60.0, 40.0, -20.0)  # yard turbine centre
YL, YR = 170.0, 30.0
YG = (-205.0, 40.0, -20.0)  # generator
HR = (70.0, 0.0, -20.0)  # HRSG base
ST = (120.0, 0.0, -20.0)  # stack base
SP = (62.0, 52.0, 60.0)  # steam turbine
# bench (x 150..248): the cut-open turbine
BT = (200.0, 22.0, -30.0)
BL, BR = 88.0, 14.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    K.ground(m, root, *PAD)

    yt = K.gas_turbine(m, root, "yard_gt", YT, YL, YR, cut=False)
    gen = K.generator(m, root, "gen", YG, 60.0, 26.0)
    hrsg = K.hrsg(m, root, "hrsg", HR, 52.0, 70.0, 40.0)
    stk = K.stack(m, root, "stack", ST, 120.0, 8.0)
    steam = K.cyl(m, root, "steam_t", SP, 14.0, 50.0, m["plant_steel"], axis="x")
    K.pipe(m, root, "pole", [(-262.0, 0.0, -20.0), (-262.0, 92.0, -20.0)], 2.2, m["plant_steel"])
    K.pipe(m, root, "gas_line", [(-330.0, 8.0, 80.0), (-120.0, 8.0, 80.0), (-70.0, 16.0, 58.0)], 3.5, m["plant_steel"])
    steam_pts = [(HR[0], 72.0, -20.0), (HR[0], 74.0, 28.0), (SP[0], SP[1] + 10.0, SP[2])]
    K.pipe(m, root, "steam_line", steam_pts, 3.0, m["plant_steam"])

    # bench: the cut-open turbine
    bt = K.gas_turbine(m, root, "bench_gt", BT, BL, BR, cut=True)
    flame = bt["flame"]
    rotor_b = bt["rotor"]
    pts = bt["pts"]
    magn_at = (YT[0] + 10.0, 0.5, 70.0)
    C.magnify(m, root, magn_at, (BT[0] - BL / 2 - 10.0, BT[1] + 20.0, BT[2]))

    # beat 2: fuel lit, air and gas run through
    flame_show = [(F(2, 0.1), F(4, 0.0))]
    present(flame, flame_show)
    cx, cy, cz = BT
    air = [(cx - BL / 2 - 14.0, cy + 0.2 * BR, cz + 6.0), (cx - 26.0, cy + 0.4 * BR, cz + 6.0),
           (cx - 6.0, cy + 0.6 * BR, cz + 5.0), (cx + 8.0, cy + 0.8 * BR, cz + 5.0)]
    run(root, "air", air, 7, 0.9, m["plant_air"], [2, 3], 0.0, 0.8, 40)
    hot = [(cx + 6.0, cy + 0.7 * BR, cz + 4.0), (cx + 24.0, cy + 0.6 * BR, cz + 4.0),
           (cx + 40.0, cy + 0.6 * BR, cz + 4.0), (cx + BL / 2 + 6.0, cy + 0.7 * BR, cz + 4.0)]
    run(root, "hot", hot, 8, 1.1, m["plant_hotgas"], [2, 3, 4], 0.1, 0.9, 40)
    C.spin(rotor_b, [2, 3, 4], turns=2.0, axis=0)
    C.spin(yt["rotor"], [2, 3, 4], turns=2.0, axis=0)
    C.spin(gen, [3, 4], turns=2.0, axis=0)

    # beat 3: electrical current out to the grid
    cable = [(YG[0] - 30.0, YG[1], YG[2]), (-262.0, YG[1], YG[2]), (-262.0, 90.0, YG[2])]
    run(root, "grid", cable, 7, 1.0, m["plant_elec"], [3], 0.0, 0.8, 40)

    # beat 4: heat up the stack, steam runs up to the steam turbine
    rise(root, "stack_heat", (ST[0], 120.0, ST[2]), 6, 1.4, m["plant_hotgas"], 4, 0.0, 0.8, 30.0, 60, (4.0, 4.0))
    run(root, "steam", steam_pts, 6, 1.2, m["plant_steam"], [4], 0.0, 0.7, 50)

    C.tags(root, {
        0: [("gas turbine", (YT[0], YT[1] + 34.0, YT[2])), ("generator", (YG[0], YG[1] + 26.0, YG[2])),
            ("HRSG: exhaust heat", (HR[0], 70.0, HR[2])), ("stack", (ST[0], 120.0, ST[2]))],
        1: [("compressor", (BT[0] - 26.0, BT[1] + BR + 4.0, BT[2])), ("combustor cans", (BT[0] + 2.0, BT[1] + BR + 6.0, BT[2])),
            ("turbine blades", (BT[0] + 30.0, BT[1] + BR + 4.0, BT[2])), ("one shaft", (BT[0], BT[1], BT[2] + 10.0))],
        2: [("air in", pts["inlet"]), ("fuel lit", pts["comb"]), ("hot gas drives the blades", pts["turb"])],
        3: [("shaft spins the rotor", pts["shaft"]), ("current to the grid", (-262.0, 90.0, -20.0)), ("GEV, ENR", (YG[0], YG[1] + 26.0, YG[2]))],
        4: [("exhaust heat -> steam", (ST[0] - 4.0, 120.0, ST[2])), ("steam turbine", (SP[0], SP[1] + 14.0, SP[2])),
            ("MHVYF, CAT", (SP[0] - 12.0, SP[1] - 12.0, SP[2]))],
    })
    C.done(SLUG, BEATS, [
        frame((-90.0, 40.0, -10.0), 420.0, 0.30, 0.30, pad=1.0),
        frame((BT[0], BT[1] + 6.0, BT[2]), 120.0, 0.25, 0.22),
        frame((BT[0], BT[1] + 4.0, BT[2] + 8.0), 80.0, 0.12, 0.10),
        frame((-180.0, 60.0, -20.0), 260.0, 0.30, 0.28),
        frame((90.0, 40.0, 0.0), 320.0, 0.30, 0.30, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
