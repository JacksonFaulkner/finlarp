"""TRM_WET_CHEMICALS: the Terms-tab overview for electronic-grade wet chemicals, built with kit_supply parts.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_wet_chemicals.py

Writes assets/term_TRM_WET_CHEMICALS.glb. Captions live in specs/terms/TRM_WET_CHEMICALS.json.

Bulk tanks and a purification column feed filtered lines to a wet bench of open baths; a wafer
cassette dips bath to bath, and a single-wafer spin cleaner sprays chemistry across a turning wafer.

Beats:
  0 bulk      HF, sulfuric acid, ammonia cleans arrive in bulk and are purified
  1 purity    filters strip metals and particles to parts per trillion
  2 bath      a cassette of wafers dips through etch, rinse, clean baths
  3 spin      a single-wafer tool sprays chemistry on a spinning wafer
  4 demand    every step uses it; ENTG, MRK.DE, BAS.DE
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
import sand_overview as O  # noqa: E402
from term_common import F, bx, empty, show, spin  # noqa: E402
from power_vrm_detail import frame, run, rise, mat  # noqa: E402

SLUG = "TRM_WET_CHEMICALS"
BEATS = [
    ("Wet chemicals are ultra-pure acids, bases and solvents",
     "Fabs use hydrofluoric acid to etch oxide, sulfuric acid and peroxide to strip resist, and ammonia-peroxide "
     "mixes to lift particles. They arrive by tanker or tote, sit in bulk tanks, and are pumped through a "
     "distribution system to every wet tool in the fab."),
    ("Electronic grade means impurities at parts per trillion",
     "A single iron or sodium atom in the wrong place can leak current in a transistor, so metals and particles "
     "are held to parts per trillion. Suppliers distill and filter the chemicals, and the fab filters again at "
     "the point of use. Filters, liners and sensors in this loop are a business of their own."),
    ("Wafer batches dip through etch, rinse and clean baths",
     "In a wet bench, a cassette of wafers is lowered into one bath after another: an acid etch, an ultra-pure "
     "water rinse, a clean, another rinse, then a dryer. Baths are heated and recirculated through filters, and "
     "used chemistry goes to waste treatment."),
    ("Single-wafer tools spray chemistry on a spinning wafer",
     "Advanced nodes moved many cleans to single-wafer tools: the wafer spins and nozzles spray chemistry across "
     "it, then water, then it spins dry. This gives tighter control and fewer defects than batch baths, at the "
     "cost of more tools."),
    ("Cleans run between most steps, so volume rises with complexity",
     "A modern chip sees hundreds of cleaning and etch steps, so a big fab uses thousands of tonnes of chemistry a "
     "month. More layers in 3D NAND and gate-all-around logic mean more cleans per wafer. Related: Entegris "
     "(ENTG), Merck KGaA (MRK.DE), BASF (BAS.DE)."),
]

TANKS = [(-150.0, 0.0, -60.0), (-125.0, 0.0, -60.0), (-100.0, 0.0, -60.0)]
COL = (-70.0, 0.0, -50.0)
FIL = (-40.0, 0.0, -40.0)
BATHS = [0.0, 22.0, 44.0, 66.0]
BZ = -40.0
SPIN = (130.0, 0.0, -40.0)
CHEMS = ["sup_flow", "wc_green", "sup_he"]


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    m["wc_green"] = mat("wc_green", (0.5, 1.0, 0.5), emit=(0.4, 1.0, 0.45), strength=2.5)
    m["wc_liq"] = mat("wc_liq", (0.35, 0.75, 0.95), emit=(0.3, 0.7, 1.0), strength=0.6)
    m["wc_acid"] = mat("wc_acid", (0.95, 0.75, 0.35), emit=(1.0, 0.7, 0.3), strength=0.6)
    m["wc_wafer"] = mat("wc_wafer", (0.35, 0.38, 0.48), metal=0.8, rough=0.15)
    m["wc_pfa"] = mat("wc_pfa", (0.92, 0.92, 0.90), metal=0.0, rough=0.4)

    bx("floor", (-175.0, -3.0, -95.0), (170.0, 0.0, 0.0), m["sup_steel"], root)

    # bulk tanks with coloured bands, then the column and the filters
    tank_pts = []
    for k, c in enumerate(TANKS):
        O.disc(f"bulk{k}", (c[0], 20.0, c[2]), 10.0, 40.0, m["wc_pfa"], root)
        O.disc(f"bulk{k}_band", (c[0], 32.0, c[2]), 10.2, 3.0, m[CHEMS[k]], root)
        tank_pts.append((c[0], 40.0, c[2]))
    O.disc("column", (COL[0], 30.0, COL[2]), 6.0, 60.0, m["sup_steel"], root)
    for j in range(5):
        O.disc(f"col_tray{j}", (COL[0], 8.0 + j * 11.0, COL[2]), 6.4, 1.0, m["sup_coil"], root)
    feeds = []
    for k, c in enumerate(TANKS):
        p = [(c[0], 4.0, c[2] + 10.0), (c[0], 4.0, -42.0 - k * 3), (COL[0] - 6, 8.0, -42.0 - k * 3)]
        K.pipe(m, root, f"feed{k}", p, 0.9)
        feeds.append(p)
    # cut-away filter housings: pleated element inside
    fil_out = []
    for k in range(3):
        x = FIL[0] + k * 9
        O.disc(f"fil{k}_base", (x, 1.0, FIL[2]), 3.5, 2.0, m["wc_pfa"], root)
        O.disc(f"fil{k}_cap", (x, 23.0, FIL[2]), 3.5, 2.0, m["wc_pfa"], root)
        bx(f"fil{k}_back", (x - 3.5, 0.0, FIL[2] - 3.5), (x + 3.5, 22.0, FIL[2] - 3.0), m["wc_pfa"], root)
        for j in range(8):
            bx(f"fil{k}_pleat{j}", (x - 2.2, 2.0 + j * 2.4, FIL[2] - 2.2), (x + 2.2, 3.0 + j * 2.4, FIL[2] + 2.2),
               m["sup_pkg"], root)
    to_fil = [(COL[0], 58.0, COL[2]), (COL[0], 62.0, COL[2]), (FIL[0] - 6, 62.0, FIL[2]), (FIL[0] - 6, 24.0, FIL[2])]
    K.pipe(m, root, "to_fil", to_fil, 0.9)
    out = [(FIL[0] + 22, 20.0, FIL[2]), (BATHS[0] - 10, 30.0, BZ)]
    K.pipe(m, root, "to_bench", out, 0.9)
    fil_out.append(out)

    # beat 1: dirt beads get caught in the filters, clean beads pass
    for k in range(3):
        x = FIL[0] + k * 9
        run(root, f"dirt{k}", [(x, 24.0, FIL[2]), (x, 12.0, FIL[2])], 4, 0.9, m["sup_hot"], [1], 0.05, 0.8, 20)
        run(root, f"clean{k}", [(x, 24.0, FIL[2] + 4), (x, 1.0, FIL[2] + 4)], 4, 0.7, m["sup_he"], [1], 0.1, 0.9, 25)

    # wet bench: four baths
    bx("bench", (BATHS[0] - 12, 0.0, BZ - 14), (BATHS[-1] + 12, 14.0, BZ + 14), m["wc_pfa"], root)
    bath_mats = ["wc_acid", "wc_liq", "wc_acid", "wc_liq"]
    for k, x in enumerate(BATHS):
        bx(f"bath{k}", (x - 9, 14.0, BZ - 10), (x + 9, 16.0, BZ + 10), m["sup_pkg"], root)
        bx(f"bath{k}_liq", (x - 8, 14.0, BZ - 9), (x + 8, 16.4, BZ + 9), m[bath_mats[k]], root)
    bx("bench_hood", (BATHS[0] - 12, 40.0, BZ - 14), (BATHS[-1] + 12, 42.0, BZ + 14), m["sup_steel"], root)
    bx("bench_post", (BATHS[0] - 12, 14.0, BZ - 14), (BATHS[0] - 10, 40.0, BZ - 12), m["sup_steel"], root)
    bx("bench_post2", (BATHS[-1] + 10, 14.0, BZ - 14), (BATHS[-1] + 12, 40.0, BZ - 12), m["sup_steel"], root)
    # the cassette of wafers: a pivot at the origin, moved by keyframes
    cas = empty("cassette", root)
    for j in range(6):
        O.disc(f"cw{j}", (BATHS[0], 22.0, BZ - 6 + j * 2.4), 6.0, 0.4, m["wc_wafer"], cas).rotation_euler = (0, 0, 0)
    bx("cas_frame", (BATHS[0] - 7, 15.5, BZ - 8), (BATHS[0] + 7, 16.5, BZ + 8), m["wc_pfa"], cas)
    bx("cas_arm", (BATHS[0] - 0.8, 16.5, BZ - 0.8), (BATHS[0] + 0.8, 38.0, BZ + 0.8), m["sup_steel"], cas)
    O._interp("LINEAR")
    keys = [(0, 0.0, 10.0)]
    for k, x in enumerate(BATHS):
        u = 0.05 + k * 0.22
        keys += [(F(2, u), x, 10.0), (F(2, u + 0.06), x, 0.0), (F(2, u + 0.14), x, 0.0), (F(2, u + 0.2), x, 10.0)]
    keys.append((F(5, 0) - 1, BATHS[-1], 10.0))
    for f, x, y in keys:
        cas.location = (x - BATHS[0], 0.0, y)  # blender z is scene up
        cas.keyframe_insert("location", frame=f)
    for k, x in enumerate(BATHS):
        rise(root, f"bath{k}_steam", (x, 16.0, BZ), 4, 0.6, m["wc_liq"] if k % 2 else m["sup_hot"], [2],
             h=14.0, spread=(14.0, 14.0))
    run(root, "bench_feed", out, 5, 1.0, m["sup_flow"], [0, 2, 4], 0.1, 0.9, 25)

    # single-wafer spin cleaner, front cut away
    sx, sz = SPIN[0], SPIN[2]
    bx("spin_back", (sx - 22, 0, sz - 18), (sx + 22, 40, sz - 16), m["white"], root)
    bx("spin_l", (sx - 22, 0, sz - 18), (sx - 20, 40, sz + 16), m["white"], root)
    bx("spin_r", (sx + 20, 0, sz - 18), (sx + 22, 40, sz + 16), m["white"], root)
    bx("spin_top", (sx - 22, 40, sz - 18), (sx + 22, 42, sz + 16), m["white"], root)
    O.cup("spin_bowl", (sx, 6.0, sz), 15.0, 8.0, m["sup_pkg"], root)
    rot = O.pivot("spin_rot", (sx, 13.0, sz), root)
    O.disc("spin_wafer", (0.0, 0.0, 0.0), 12.0, 0.5, m["wc_wafer"], rot)
    for j in range(3):
        bx(f"spin_pin{j}", (-0.5 + (j - 1) * 7, 0.2, 9.5), (0.5 + (j - 1) * 7, 1.2, 10.5), m["sup_coil"], rot)
    spin(rot, [3], turns=6.0)
    bx("nozzle_arm", (sx - 18, 26.0, sz - 0.8), (sx + 1, 27.5, sz + 0.8), m["sup_steel"], root)
    bx("nozzle", (sx - 0.5, 22.0, sz - 1.0), (sx + 1.5, 26.0, sz + 1.0), m["sup_steel"], root)
    run(root, "spray", [(sx + 0.5, 22.0, sz), (sx + 0.5, 13.5, sz)], 6, 0.8, m["wc_green"], [3], 0.05, 0.9, 10)
    for k in range(6):
        import math
        a = 2 * math.pi * k / 6
        run(root, f"fling{k}", [(sx, 13.6, sz), (sx + 14 * math.cos(a), 11.0, sz + 14 * math.sin(a))], 2, 0.6,
            m["wc_green"], [3], 0.15 + 0.04 * k, 0.9, 12)

    for k in range(3):
        run(root, f"feed_flow{k}", feeds[k], 3, 1.1, m[CHEMS[k]], [0, 4], 0.05 * k, 0.7, 30)
    run(root, "col_up", to_fil, 4, 1.0, m["sup_he"], [0, 1], 0.2, 0.9, 30)

    tags = {
        0: [("HF, sulfuric, ammonia", tank_pts[1]), ("purification column", (COL[0], 62.0, COL[2])),
            ("pumped to every tool", (BATHS[0] - 10, 30.0, BZ))],
        1: [("filters at point of use", (FIL[0] + 9, 24.0, FIL[2])), ("metals caught: ppt", (FIL[0], 12.0, FIL[2])),
            ("clean chemistry passes", (FIL[0] + 18, 2.0, FIL[2] + 4))],
        2: [("cassette of wafers", (BATHS[1], 38.0, BZ)), ("acid etch bath", (BATHS[0], 16.0, BZ + 10)),
            ("ultra-pure water rinse", (BATHS[3], 16.0, BZ + 10))],
        3: [("wafer spins", (sx + 10, 13.5, sz + 8)), ("nozzle sprays chemistry", (sx, 26.0, sz)),
            ("flung off, spun dry", (sx - 14, 12.0, sz))],
        4: [("hundreds of cleans/chip", (BATHS[2], 42.0, BZ)), ("ENTG, MRK.DE, BAS.DE", tank_pts[0]),
            ("more layers, more cleans", (sx, 42.0, sz))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-100.0, 25.0, -50.0), 120.0, 0.30, 0.25),
        frame((FIL[0] + 9, 12.0, FIL[2]), 55.0, 0.20, 0.20),
        frame((BATHS[1] + 11, 22.0, BZ), 110.0, 0.20, 0.30),
        frame((sx, 18.0, sz), 60.0, 0.25, 0.40),
        frame((-10.0, 25.0, -45.0), 330.0, 0.25, 0.35),
    ], root)


if __name__ == "__main__":
    build()
