"""TRM_HELIUM: the Terms-tab overview for helium, built with the kit_supply parts.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_helium.py

Writes assets/term_TRM_HELIUM.glb. Captions live in specs/terms/TRM_HELIUM.json (same beat count).

A gas field (well heads, separation plant, liquefier, ISO dewars) runs natural gas beads; helium
atoms split off. The bench shows an MRI magnet in a liquid helium bath, then a fab etch chamber
with helium cooling a wafer from behind.

Beats:
  0 wells     helium rides out of the ground in natural gas
  1 liquefy   cooled to 4.2 K and shipped as liquid in dewars
  2 mri       liquid helium keeps superconducting magnet coils cold; boil-off
  3 fab       backside cooling, carrier and leak-check gas in chip tools
  4 supply    a few countries, no way to make more; LIN, APD, AI.PA
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
from term_common import F, bx, empty, show  # noqa: E402
from power_vrm_detail import blink, frame, rise, run  # noqa: E402

SLUG = "TRM_HELIUM"
BEATS = [
    ("Helium comes out of the ground mixed into natural gas",
     "Helium forms over hundreds of millions of years from radioactive decay in rock and collects in some "
     "natural gas fields, at a fraction of a percent up to a few percent. It is pulled out only where a gas "
     "plant bothers to separate it. Once vented into the air, it escapes to space, so nobody can manufacture it."),
    ("Chilled to 4.2 K, it ships as a liquid in vacuum dewars",
     "The plant cools the gas until everything else condenses, then liquefies the helium at 4.2 kelvin, the "
     "coldest boiling point of any element. It travels in insulated ISO containers that slowly boil off, so "
     "a shipment has a clock on it of about a month."),
    ("Liquid helium keeps superconducting magnets cold",
     "MRI scanners and research magnets wind niobium-titanium wire that only superconducts near 4 K. The coil "
     "sits in a bath of liquid helium, and the bath slowly boils away and must be topped up. Magnets are the "
     "largest single use of helium."),
    ("Fabs use it to cool wafers and check for leaks",
     "In etch and deposition tools, helium flows behind the wafer to carry heat to the chuck, because it "
     "conducts heat well and reacts with nothing. It is also a carrier gas and the tracer for leak checks. A "
     "large fab needs a steady high-purity supply, so a shortage slows tools and raises running costs."),
    ("A handful of countries supply it, and supply can't be ramped",
     "The US, Qatar, Algeria and Russia produce most of the world's helium, and an outage at one plant can "
     "tighten the market for months. For AI data centers it is a tiny cost, but for new fabs it is a real input "
     "constraint. Related: Linde (LIN), Air Products (APD), Air Liquide (AI.PA)."),
]

WELLS = [(-150.0, 0.0, -80.0), (-125.0, 0.0, -100.0), (-150.0, 0.0, -110.0)]
PLANT = (-95.0, 0.0, -80.0)
LIQF = (-60.0, 0.0, -80.0)
ISO = [(-25.0, 0.0, -70.0), (0.0, 0.0, -70.0), (25.0, 0.0, -70.0)]
GAS = [[(w[0], 18.0, w[2]), (w[0] + 10.0, 6.0, (w[2] - 80.0) / 2 - 40.0), (PLANT[0] - 10.0, 10.0, PLANT[2])]
       for w in WELLS]
HE = [(PLANT[0] + 8.0, 26.0, PLANT[2]), (LIQF[0], 34.0, LIQF[2])]
CH4 = [(PLANT[0], 10.0, PLANT[2] + 12.0), (PLANT[0], 4.0, -40.0), (-140.0, 4.0, -40.0)]
SHIP = [(LIQF[0] + 8.0, 8.0, LIQF[2]), (-35.0, 8.0, -70.0), (25.0, 8.0, -70.0)]


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    bx("bench", (140.0, -3.0, -60.0), (258.0, 0.0, 20.0), m["sup_steel"], root)
    bx("yard", (-175.0, -3.0, -125.0), (45.0, 0.0, -30.0), m["sup_steel"], root)

    # gas field
    for k, w in enumerate(WELLS):
        K.drum(m, root, f"well{k}", w, 2.0, 18.0)
        bx(f"well{k}_valve", (w[0] - 4, 12.0, w[2] - 1.5), (w[0] + 4, 15.0, w[2] + 1.5), m["warn"], root)
        K.pipe(m, root, f"gas{k}", GAS[k], 1.0)
        run(root, f"gasflow{k}", GAS[k], 4, 1.0, m["sup_flow"], [0], 0.0, 0.7, 40)
    _, plant_pts = K.tank(m, root, "plant", PLANT, 9.0, 26.0, "sup_gas")
    K.drum(m, root, "liquefier", LIQF, 7.0, 34.0, "sup_gas")
    for k in range(4):
        K.ring(m, root, f"liqf_fin{k}", (LIQF[0], 6.0 + 7.0 * k, LIQF[2]), 7.4, 0.5, "sup_cryo")
    K.pipe(m, root, "hepipe", HE, 0.8)
    K.pipe(m, root, "ch4pipe", CH4, 1.4)
    run(root, "heflow", HE, 4, 0.9, m["sup_he"], [0, 1], 0.2, 0.9, 30)
    run(root, "ch4flow", CH4, 4, 1.1, m["sup_flow"], [0], 0.2, 0.9, 40)
    iso_pts = []
    for k, c in enumerate(ISO):
        bx(f"iso{k}_frame", (c[0] - 10, 0.0, c[2] - 6), (c[0] + 10, 1.5, c[2] + 6), m["steel"], root)
        _, liq, pts = K.dewar(m, root, f"iso{k}", (c[0], 1.5, c[2]), 6.0, 14.0)
        iso_pts.append(pts)
    K.pipe(m, root, "ship", SHIP, 0.8)
    run(root, "shipflow", SHIP, 5, 0.9, m["sup_cryo"], [1], 0.1, 0.9, 40)
    K.cloud(m, root, "he_atoms", (PLANT[0], 34.0, PLANT[2]), 10, 6.0, 0.9)

    # beat 2: MRI on the bench, cut-open dewar around the coil
    mri = empty("mri", root)
    _, gpts = K.gantry(m, mri, "gantry", (199.0, 26.0, -30.0), 24.0, 30.0)
    _, bath, dpts = K.dewar(m, mri, "bath", (199.0, 0.0, 10.0), 14.0, 22.0)
    K.ring(m, mri, "nbti", (199.0, 26.0, -14.0), 18.0, 1.2, "sup_coil", "z", 32)
    bx("table", (190.0, 12.0, -60.0), (208.0, 14.0, -16.0), m["white"], mri)
    show(mri, [(F(2, 0), F(3, 0))])
    rise(root, "boil", (199.0, 14.0, 10.0), 8, 0.7, m["sup_he"], [2], h=24.0, spread=(8.0, 6.0))
    run(root, "current", [(181.0, 26.0, -14.0), (199.0, 44.0, -14.0), (217.0, 26.0, -14.0),
                          (199.0, 8.0, -14.0), (181.0, 26.0, -14.0)], 6, 1.0, m["e_blue"], [2], 0.0, 0.9, 40)

    # beat 3: fab etch chamber, wafer on chuck, helium behind it
    fab = empty("fab", root)
    bx("etch_back", (164.0, 0.0, -47.0), (234.0, 40.0, -45.0), m["steel"], fab)
    bx("etch_floor", (164.0, 0.0, -47.0), (234.0, 8.0, -5.0), m["steel"], fab)
    bx("etch_lid", (164.0, 38.0, -47.0), (234.0, 40.0, -30.0), m["steel"], fab)
    bx("showerhead", (176.0, 32.0, -38.0), (222.0, 34.0, -12.0), m["alum"], fab)
    bx("chuck", (174.0, 10.0, -40.0), (224.0, 16.0, -10.0), m["steel"], fab)
    wafer = bx("wafer", (176.0, 16.5, -38.0), (222.0, 17.5, -12.0), m["si"], fab)
    plasma = bx("plasma", (178.0, 22.0, -36.0), (220.0, 26.0, -14.0), m["rf"], fab)
    show(fab, [(F(3, 0), F(4, 0))])
    blink(plasma, 3, [0, 1, 2, 3, 4, 5, 6, 7], n=8, on=0.6)
    run(root, "bkside", [(160.0, 16.0, -25.0), (176.0, 16.2, -25.0), (222.0, 16.2, -25.0)], 6, 0.8,
        m["sup_he"], [3], 0.0, 0.85, 30)
    rise(root, "chuckheat", (199.0, 17.5, -25.0), 5, 0.6, m["h_amber"], [3], h=-6.0, spread=(18.0, 8.0))
    _ = wafer

    tags = {
        0: [("gas wells: up to a few % He", (WELLS[0][0], 20.0, WELLS[0][2])),
            ("separation plant", plant_pts["top"]), ("methane back to pipeline", CH4[2])],
        1: [("liquefied at 4.2 K", (LIQF[0], 36.0, LIQF[2])), ("ISO dewar: boils off", iso_pts[1]["liquid"]),
            ("about a month to use it", iso_pts[2]["liquid"])],
        2: [("NbTi coil: superconducts ~4 K", (217.0, 40.0, -14.0)), ("liquid He bath", dpts["liquid"]),
            ("boil-off must be topped up", (199.0, 40.0, 10.0))],
        3: [("He behind the wafer", (165.0, 16.0, -25.0)), ("plasma etch on top", (199.0, 27.0, -25.0)),
            ("heat into the chuck", (222.0, 12.0, -10.0))],
        4: [("US, Qatar, Algeria, Russia", (WELLS[1][0], 20.0, WELLS[1][2])),
            ("can't be manufactured", plant_pts["top"]), ("LIN, APD, AI.PA", iso_pts[0]["liquid"])],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-110.0, 12.0, -85.0), 110.0, 0.30, 0.40),
        frame((-30.0, 12.0, -75.0), 110.0, 0.25, 0.35),
        frame((199.0, 22.0, -15.0), 90.0, 0.35, 0.30),
        frame((199.0, 18.0, -25.0), 85.0, 0.25, 0.35),
        frame((-65.0, 12.0, -80.0), 200.0, 0.35, 0.40),
    ], root)


if __name__ == "__main__":
    build()
