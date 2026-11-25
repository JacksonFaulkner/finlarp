"""TRM_GALLIUM: the Terms-tab overview for gallium, built with the kit_supply parts.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_gallium.py

Writes assets/term_TRM_GALLIUM.glb. Captions live in specs/terms/TRM_GALLIUM.json (same beat count).

An alumina refinery yard (bauxite heap, digester tanks, gallium recovery column, ingot drums) runs
beads of caustic liquor; the bench holds a gallium ingot melting, then a GaN crystal slice, then a
board of GaN power and GaAs RF chips.

Beats:
  0 refinery  bauxite to Bayer liquor; gallium skimmed off the alumina stream
  1 metal     a 99.99999% ingot that melts near body temperature
  2 crystal   Ga and N (or As) atoms stacked into a compound semiconductor
  3 devices   GaN power switches and GaAs RF amplifiers on a board
  4 supply    China refines ~98%; export licences since 2023
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
from term_common import F, bx, empty, show  # noqa: E402
from power_vrm_detail import blink, frame, rise, run  # noqa: E402

SLUG = "TRM_GALLIUM"
BEATS = [
    ("Gallium is skimmed off alumina refining as a byproduct",
     "There are no gallium mines. Bauxite ore holds about 50 parts per million of gallium, and when a refinery "
     "dissolves bauxite in hot caustic soda to make alumina, the gallium goes into the liquor with it. A recovery "
     "column pulls a little of it out of that stream, so gallium output follows alumina plants, not demand."),
    ("Refined to seven nines, it is a metal that melts in your hand",
     "Crude gallium is refined to 99.99999% purity for chips. It melts at 29.8 C, so a bar turns liquid on a warm "
     "day, and it is shipped in plastic-lined bottles. World output is only several hundred tonnes a year."),
    ("Bonded to nitrogen or arsenic it becomes a compound semiconductor",
     "Gallium paired with nitrogen (GaN) or arsenic (GaAs) forms crystals whose electrons move faster and stand "
     "higher voltage than silicon's. GaN has a wide bandgap of 3.4 eV versus silicon's 1.1 eV. Wafers and "
     "epitaxial layers of these crystals are what chip makers buy."),
    ("GaN switches power and GaAs amplifies radio in AI and phone hardware",
     "GaN transistors switch power supplies at high frequency with low loss, shrinking server and charger "
     "power stages. GaAs chips are the power amplifiers in phones and many RF links, and GaN also makes "
     "blue lasers and LEDs. A shortage of gallium shows up as longer lead times for these parts."),
    ("China refines nearly all of it and licenses exports",
     "China produces roughly 98% of primary gallium because it runs most of the world's alumina capacity. It "
     "required export licences in 2023 and later banned shipments to the US, which pushed prices outside China "
     "sharply higher. Related: AXT Inc (AXTI), Navitas Semiconductor (NVTS), Coherent (COHR)."),
]

# refinery yard, behind the bench
ORE = (-140.0, 0.0, -50.0)
DIG = [(-100.0, 0.0, -50.0), (-70.0, 0.0, -50.0)]
COL = (-38.0, 0.0, -50.0)
DRUMS = [(-5.0, 0.0, -40.0), (12.0, 0.0, -40.0), (29.0, 0.0, -40.0)]
POT = [(-100.0, 0.0, -95.0), (-60.0, 0.0, -95.0)]  # alumina product silos (main stream)
LIQ = [
    [(-128.0, 6.0, -50.0), (-112.0, 18.0, -50.0)],
    [(-90.0, 20.0, -50.0), (-80.0, 20.0, -50.0)],
    [(-60.0, 20.0, -50.0), (-46.0, 30.0, -50.0)],
]
GA = [(-30.0, 10.0, -50.0), (-15.0, 10.0, -45.0), (-5.0, 14.0, -40.0)]
AL = [(-70.0, 4.0, -60.0), (-70.0, 4.0, -80.0), (-60.0, 6.0, -90.0)]

BC = (199.0, 0.0, -20.0)  # bench centre


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    bx("bench", (140.0, -3.0, -60.0), (258.0, 0.0, 20.0), m["sup_steel"], root)
    bx("yard", (-170.0, -3.0, -120.0), (60.0, 0.0, -20.0), m["sup_steel"], root)

    # beat 0 + 4: refinery
    K.rock_pile(m, root, "bauxite", ORE, 14.0)
    dig_pts = []
    for k, c in enumerate(DIG):
        _, pts = K.tank(m, root, f"dig{k}", c, 10.0, 22.0)
        dig_pts.append(pts)
        bx(f"dig{k}_liq", (c[0] - 7, 1.0, c[2] - 7), (c[0] + 7, 15.0, c[2] + 7), m["sup_hot"], root)
    col = K.drum(m, root, "column", COL, 6.0, 34.0, "sup_gas")
    for k in range(5):
        K.ring(m, col, f"col_tray{k}", (COL[0], 6.0 + k * 6.0, COL[2]), 6.3, 0.4, "sup_steel")
    for k, c in enumerate(POT):
        K.drum(m, root, f"silo{k}", c, 9.0, 30.0, "sup_gas")
    for k, c in enumerate(DRUMS):
        K.drum(m, root, f"gadrum{k}", c, 5.0, 10.0, "sup_ga")
    for k, p in enumerate(LIQ):
        K.pipe(m, root, f"liq{k}", p, 1.4)
    K.pipe(m, root, "gapipe", GA, 0.9)
    K.pipe(m, root, "alpipe", AL, 1.6)
    for k, p in enumerate(LIQ):
        run(root, f"liqflow{k}", p, 4, 1.1, m["sup_flow"], [0], 0.0, 0.7, 40)
    run(root, "alflow", AL, 5, 1.2, m["white"], [0], 0.05, 0.75, 40)
    run(root, "gaflow", GA, 2, 0.8, m["e_blue"], [0, 4], 0.3, 0.8, 40)
    rise(root, "steam", (-85.0, 22.0, -50.0), 6, 0.7, m["sup_hot"], [0], spread=(14.0, 4.0), h=20.0)

    # beat 1: melting ingot on the bench
    ing = empty("ingot_g", root)
    bx("ingot", (175.0, 0.0, -30.0), (215.0, 8.0, -12.0), m["sup_ga"], ing)
    pool = bx("pool", (215.0, 0.0, -34.0), (232.0, 0.6, -8.0), m["sup_ga"], ing)
    show(pool, [(F(1, 0.15), F(2, 0))])
    hand = bx("warm_pad", (170.0, -0.5, -40.0), (238.0, 0.0, -2.0), m["sup_hot"], ing)
    show(hand, [(F(1, 0.1), F(2, 0))])
    rise(root, "warm", (200.0, 8.0, -21.0), 6, 0.6, m["h_amber"], [1], 0.2, 0.9, h=14.0, spread=(14.0, 6.0))
    show(ing, [(F(1, 0), F(2, 0))])

    # beat 2: GaN lattice, two layers
    xt = empty("xtal", root)
    bx("xtal_base", (165.0, 0.0, -45.0), (233.0, 2.0, 5.0), m["gan"], xt)
    for lay in range(3):
        K.lattice(m, xt, f"lat{lay}", (199.0, 6.0 + lay * 7.0, -20.0), 7, 5, 9.0, 2.0,
                  "sup_ga_atom", "sup_n_atom")
    show(xt, [(F(2, 0), F(3, 0))])
    ebeads = run(root, "elec", [(166.0, 13.0, -20.0), (232.0, 13.0, -20.0)], 6, 0.9, m["e_blue"], [2],
                 0.2, 0.9, 30)

    # beat 3: chips on a board
    dv = empty("dev", root)
    gan_g, gan_glow, gan_pts = K.die(m, dv, "gan_fet", (180.0, 1.6, -20.0), 14.0, 12.0, "sup_hot")
    gaas_g, gaas_glow, gaas_pts = K.die(m, dv, "gaas_pa", (220.0, 1.6, -20.0), 14.0, 12.0, "sup_hot")
    for k in range(4):
        bx(f"ind{k}", (172.0 + k * 5, 1.6, -4.0), (175.0 + k * 5, 6.0, 0.0), m["sup_coil"], dv)
    show(dv, [(F(3, 0), F(4, 0))])
    blink(gan_glow, 3, [0, 2, 4, 6], n=8)
    run(root, "pwr", [(160.0, 4.0, -20.0), (180.0, 4.0, -20.0), (200.0, 4.0, -8.0)], 5, 0.9, m["h_amber"], [3],
        0.1, 0.8, 30)
    C.rings(m, root, "rfw", (220.0, 8.0, -20.0), [3], n=4, r0=3.0, r1=30.0)

    tags = {
        0: [("bauxite: ~50 ppm gallium", (ORE[0], 14.0, ORE[2])), ("hot caustic liquor", dig_pts[0]["top"]),
            ("recovery column", (COL[0], 36.0, COL[2])), ("alumina: the main product", (POT[1][0], 32.0, POT[1][2]))],
        1: [("99.99999% pure", (195.0, 9.0, -21.0)), ("melts at 29.8 C", (224.0, 1.0, -21.0)),
            ("a few hundred t/year", (180.0, 1.0, -40.0))],
        2: [("Ga atoms (grey)", (172.0, 20.0, -38.0)), ("N atoms (blue)", (226.0, 20.0, -2.0)),
            ("bandgap 3.4 eV vs Si 1.1", (199.0, 26.0, -20.0))],
        3: [("GaN power switch", gan_pts["top"]), ("GaAs RF amplifier", gaas_pts["top"]),
            ("fast, low-loss switching", (168.0, 4.0, 2.0))],
        4: [("China: ~98% of supply", (COL[0], 36.0, COL[2])), ("export licences 2023", DRUMS[1]),
            ("AXTI, NVTS, COHR", (DRUMS[2][0], 11.0, DRUMS[2][2]))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-55.0, 15.0, -60.0), 150.0, 0.30, 0.35),
        frame((203.0, 4.0, -21.0), 75.0, 0.25, 0.40),
        frame((199.0, 12.0, -20.0), 85.0, 0.20, 0.45),
        frame((200.0, 4.0, -18.0), 80.0, 0.30, 0.50),
        frame((-40.0, 12.0, -50.0), 150.0, 0.45, 0.35),
    ], root)


if __name__ == "__main__":
    build()
