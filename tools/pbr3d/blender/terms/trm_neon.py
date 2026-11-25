"""TRM_NEON: the Terms-tab overview for neon, built with the kit_supply parts.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_neon.py

Writes assets/term_TRM_NEON.glb. Captions live in specs/terms/TRM_NEON.json (same beat count).

A steel-mill air separation unit (intake, cold box columns, crude neon side-draw, cylinders) runs air
beads; the bench holds an excimer laser tube cut open (neon buffer gas, discharge electrodes) that
fires a DUV beam down through a lens stack onto a wafer.

Beats:
  0 air       neon is 18 ppm of air, drawn off big air separation plants
  1 purify    crude neon refined and filled into cylinders
  2 laser     inside an ArF/KrF excimer laser, mostly neon gas
  3 expose    the DUV pulses print patterns on wafers
  4 supply    Ukraine 2022 shock, recycling, new sources; ASML, LIN, AI.PA
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
from term_common import F, bx, empty, show  # noqa: E402
from power_vrm_detail import blink, frame, run  # noqa: E402

SLUG = "TRM_NEON"
BEATS = [
    ("Neon is a trace of air, drawn off big air separation plants",
     "Air is about 18 parts per million neon. Air separation units that make oxygen and nitrogen, often for "
     "steel mills, chill air until it liquefies and distil it in tall columns. Neon does not liquefy there, so "
     "it collects as a crude gas that only some plants bother to capture."),
    ("Crude neon is purified and filled into cylinders",
     "The crude stream is mixed with helium and nitrogen, so a separate refinery purifies it to "
     "semiconductor grade, better than 99.999%. It ships in high-pressure cylinders and tube trailers. "
     "Making a tonne of neon means processing on the order of 100,000 tonnes of air."),
    ("Excimer lasers run on a gas that is mostly neon",
     "The DUV lasers in lithography tools hold a gas mix of a little argon or krypton and fluorine in a neon "
     "buffer that is over 95% of the fill. A high-voltage discharge between electrodes makes short-lived ArF "
     "molecules that emit 193 nm light in pulses, thousands per second."),
    ("Those pulses print the patterns on every DUV-exposed wafer",
     "The beam passes through the scanner's lens stack and exposes photoresist through a mask, layer after "
     "layer. Even fabs with EUV use DUV for most layers. The laser gas is refreshed regularly, so a fab burns "
     "neon continuously while its scanners run."),
    ("The 2022 Ukraine shock pushed fabs to recycle and diversify",
     "Before 2022, plants in Ukraine purified a large share of chip-grade neon from Russian and Ukrainian steel "
     "mill gas, and prices jumped when the war shut them. Chip makers qualified new sources and added neon "
     "recycling to lasers, cutting use by up to half. Related: ASML (ASML), Linde (LIN), Air Liquide (AI.PA)."),
]

INTAKE = (-150.0, 0.0, -80.0)
COLS = [(-110.0, 0.0, -80.0), (-90.0, 0.0, -80.0)]
REF = (-55.0, 0.0, -80.0)
CYL = [(-25.0 + 8.0 * i, 0.0, -70.0 - 8.0 * j) for i in range(5) for j in range(2)]
AIR = [(-150.0, 18.0, -80.0), (-130.0, 18.0, -80.0), (-116.0, 10.0, -80.0)]
NE = [(-90.0, 56.0, -80.0), (-70.0, 50.0, -80.0), (-60.0, 26.0, -80.0)]
O2 = [(-110.0, 4.0, -70.0), (-110.0, 4.0, -45.0), (-60.0, 4.0, -45.0)]
FILL = [(-49.0, 10.0, -80.0), (-25.0, 14.0, -74.0), (10.0, 14.0, -74.0)]

LY, LZ = 30.0, -30.0  # laser tube axis height / depth on the bench


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    bx("bench", (140.0, -3.0, -60.0), (258.0, 0.0, 20.0), m["sup_steel"], root)
    bx("yard", (-175.0, -3.0, -110.0), (30.0, 0.0, -35.0), m["sup_steel"], root)

    # air separation plant
    K.drum(m, root, "intake", INTAKE, 8.0, 20.0)
    for k in range(3):
        K.ring(m, root, f"filter{k}", (INTAKE[0], 5.0 + 5.0 * k, INTAKE[2]), 8.4, 0.5, "steel")
    for k, c in enumerate(COLS):
        K.drum(m, root, f"col{k}", c, 6.0, 56.0 - 8.0 * k, "sup_gas")
        for t in range(6):
            K.ring(m, root, f"col{k}_t{t}", (c[0], 6.0 + 8.0 * t, c[2]), 6.3, 0.35, "sup_cryo")
    _, ref_pts = K.tank(m, root, "refinery", REF, 7.0, 26.0, "sup_gas")
    for k, c in enumerate(CYL):
        K.drum(m, root, f"cyl{k}", c, 2.6, 18.0, "sup_gas")
        bx(f"cyl{k}_cap", (c[0] - 1, 18.0, c[2] - 1), (c[0] + 1, 20.0, c[2] + 1), m["warn"], root)
    for nm, p in (("air", AIR), ("ne", NE), ("o2", O2), ("fill", FILL)):
        K.pipe(m, root, nm, p, 1.0)
    run(root, "airflow", AIR, 5, 1.0, m["white"], [0], 0.0, 0.8, 30)
    run(root, "o2flow", O2, 5, 1.1, m["sup_cryo"], [0], 0.1, 0.9, 40)
    run(root, "neflow", NE, 3, 0.9, m["warn"], [0, 1], 0.3, 0.9, 30)
    run(root, "fillflow", FILL, 4, 0.9, m["warn"], [1], 0.1, 0.8, 40)

    # beat 2: excimer laser tube, cut open, on the bench
    las = empty("laser", root)
    bx("las_back", (160.0, LY - 12.0, LZ - 12.0), (238.0, LY + 12.0, LZ - 10.0), m["steel"], las)
    bx("las_floor", (160.0, LY - 12.0, LZ - 12.0), (238.0, LY - 10.0, LZ + 8.0), m["steel"], las)
    bx("las_feet", (165.0, 0.0, LZ - 8.0), (233.0, LY - 12.0, LZ + 4.0), m["sup_pkg"], las)
    bx("elec_top", (168.0, LY + 3.0, LZ - 6.0), (230.0, LY + 5.0, LZ + 2.0), m["sup_coil"], las)
    bx("elec_bot", (168.0, LY - 5.0, LZ - 6.0), (230.0, LY - 3.0, LZ + 2.0), m["sup_coil"], las)
    bx("mirror_l", (158.0, LY - 6.0, LZ - 6.0), (160.0, LY + 6.0, LZ + 2.0), m["alum"], las)
    bx("window_r", (238.0, LY - 6.0, LZ - 6.0), (239.0, LY + 6.0, LZ + 2.0), m["sup_glass"], las)
    import sand_overview as O
    for k in range(40):
        u, v, w = (k * 0.618) % 1.0, (k * 0.382 + 0.3) % 1.0, (k * 0.733 + 0.6) % 1.0
        O.ball(f"ne_{k}", (166.0 + 66.0 * u, LY - 8.0 + 16.0 * v, LZ - 8.0 + 12.0 * w), 0.8, m["warn"], las, 8)
    show(las, [(F(2, 0), F(5, 0))])
    arc = bx("discharge", (170.0, LY - 2.5, LZ - 4.0), (228.0, LY + 2.5, LZ), m["rf"], root)
    blink(arc, 2, [0, 2, 4, 6], n=8, on=0.4)
    arc3 = bx("discharge3", (170.0, LY - 2.5, LZ - 4.0), (228.0, LY + 2.5, LZ), m["rf"], root)
    blink(arc3, 3, [1, 3, 5, 7], n=8, on=0.4)

    # beat 3: beam out the window, down a lens stack to a wafer
    exp = empty("expose", root)
    for k in range(4):
        K.ring(m, exp, f"lens{k}", (250.0, 26.0 - 6.0 * k, LZ - 2.0), 6.0, 0.8, "sup_glass")
    bx("wafer", (238.0, 0.0, LZ - 14.0), (262.0, 1.0, LZ + 10.0), m["si"], exp)
    for i in range(4):
        for j in range(4):
            bx(f"die{i}{j}", (240.0 + 5.5 * i, 1.0, LZ - 12.0 + 5.5 * j),
               (244.5 + 5.5 * i, 1.3, LZ - 7.5 + 5.5 * j), m["sup_ga"], exp)
    show(exp, [(F(3, 0), F(5, 0))])
    run(root, "beam", [(160.0, LY, LZ - 2.0), (250.0, LY, LZ - 2.0), (250.0, 1.5, LZ - 2.0)], 8, 0.9,
        m["rf"], [2, 3], 0.1, 0.9, 30)

    cyl0 = (CYL[0][0], 20.0, CYL[0][2])
    tags = {
        0: [("air: 18 ppm neon", (INTAKE[0], 21.0, INTAKE[2])), ("cold distillation columns", (COLS[0][0], 57.0, COLS[0][2])),
            ("O2 and N2: main products", O2[2])],
        1: [("crude neon side-draw", NE[1]), ("purified to 99.999%", ref_pts["top"]),
            ("high-pressure cylinders", cyl0)],
        2: [("neon buffer >95% of fill", (199.0, LY + 13.0, LZ - 10.0)), ("discharge electrodes", (225.0, LY + 5.0, LZ + 2.0)),
            ("193 nm ArF pulses", (239.0, LY, LZ))],
        3: [("lens stack", (250.0, 26.0, LZ - 2.0)), ("exposes the wafer", (250.0, 1.5, LZ + 10.0)),
            ("gas refreshed often", (180.0, LY + 13.0, LZ - 10.0))],
        4: [("Ukraine shut 2022", (COLS[1][0], 50.0, COLS[1][2])), ("recycling cuts use ~half", (199.0, LY + 13.0, LZ - 10.0)),
            ("ASML, LIN, AI.PA", cyl0)],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-105.0, 25.0, -75.0), 110.0, 0.30, 0.30),
        frame((-40.0, 15.0, -75.0), 100.0, 0.25, 0.35),
        frame((199.0, LY, LZ), 90.0, 0.20, 0.20),
        frame((225.0, 15.0, LZ), 90.0, 0.35, 0.35),
        frame((50.0, 20.0, -45.0), 300.0, 0.10, 0.35),
    ], root)


if __name__ == "__main__":
    build()
