"""TRM_MASSIVE_MIMO: the Terms-tab overview for Massive MIMO, on the telecom-radio kit.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_massive_mimo.py

Writes assets/term_TRM_MASSIVE_MIMO.glb. Captions live in specs/terms/TRM_MASSIVE_MIMO.json.

A macro tower carries an active antenna unit: a grid of array elements on its front face, each
with its own transceiver chain. Users stand on the street below. Beams go out to several phones
at once, so one site serves many users on the same spectrum.

Beats:
  0 site      tower, antenna unit on top, users on the street
  1 inside    the unit cut open: one transceiver chain per array element
  2 beams     several beams leave the array at once, each to its own phone
  3 streams   more beams and streams for more users in the same slot
  4 scale     more elements, more streams, same spectrum
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402
import kit_radio as K  # noqa: E402

SLUG = "TRM_MASSIVE_MIMO"
BEATS = [
    ("One tower, one antenna unit, many users below",
     "A 5G mid-band macro site hangs an active antenna unit at the top of its mast. The unit's face is a grid of dozens "
     "to hundreds of antenna elements, and the same panel serves every phone in the sector at once."),
    ("Inside: one transceiver chain per array element",
     "Behind each element sits its own radio chain: a transceiver chip, filters and amplifiers. Because every element has "
     "its own chain, the base station can control the phase and amplitude of each one separately, and that is what makes "
     "the beams possible."),
    ("Beams to several phones in the same slot",
     "The unit sends a separate beam to each phone on the same frequency and time. Each beam is aimed by weighting the "
     "elements, so each user receives mostly its own signal and the others see little of it."),
    ("More streams: more users served in the same spectrum",
     "Every extra antenna adds degrees of freedom, so the site can carry more spatial streams. Capacity grows with the "
     "number of elements and the number of users served, without buying more spectrum."),
    ("Scale: more elements, more streams, same spectrum",
     "The gain is in the array, so it lands in the radio content: more antenna elements, transceiver chains and "
     "baseband processing per site. Suppliers include Ericsson (ERIC), Nokia (NOK), Qualcomm (QCOM) and Skyworks (SWKS)."),
]

TOWER = (0.0, 0.0, 0.0)
TOWER_H = 120.0
AAU_C = (0.0, TOWER_H + 6.0, 0.0)
# users on the street, in front of the array
USERS = [(-70.0, 1.0, 70.0), (-20.0, 1.0, 95.0), (30.0, 1.0, 80.0), (75.0, 1.0, 110.0), (-55.0, 1.0, 130.0),
         (10.0, 1.0, 150.0), (60.0, 1.0, 170.0), (-95.0, 1.0, 165.0)]
# bench: the unit cut open, with its chains lined up beneath
BX = 200.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.radio_materials(m)
    K.ground(m, root, "street", -160.0, 160.0, -180.0, 200.0)
    for i, (x0, x1, h, z0, z1) in enumerate(((-140, -90, 90, 40, 80), (90, 140, 70, 60, 100), (-150, -110, 60, 120, 170),
                                             (110, 160, 110, 130, 180))):
        K.building(m, root, f"bld{i}", x0, x1, h, z0, z1)
    K.tower(m, root, "tower", TOWER, h=TOWER_H, w=14.0)
    aau = K.aau(m, root, "aau", AAU_C, w=34.0, h=22.0, d=10.0, nx=8, ny=6)
    for i, u in enumerate(USERS):
        K.phone(m, root, f"ph{i}", u, s=1.0)

    # the bench copy of the unit, cut open: panel on the left, the chains lined up along the front
    bench = K.aau(m, root, "bench_aau", (BX, 30.0, 0.0), w=50.0, h=30.0, d=12.0, nx=8, ny=6)
    chains = []
    for i in range(8):
        x = BX - 35.0 + i * 10.0
        chains.append(K.transceiver(m, root, f"chain{i}", (x, 0.0, -22.0), s=2.2))
    # one bead run per beam: each user gets its own path from the array
    beams = {i: K.beam_paths(AAU_C, (u[0], 1.0, u[2]), n=1)[0] for i, u in enumerate(USERS)}

    # beat 1: the bench unit and its chains come on
    show(bench["group"], [(F(1, 0.0), F(2, 0))])
    for c in chains:
        show(c["group"], [(F(1, 0.1), F(2, 0))])
    # beat 2: beams to the first three phones, in turn, through the same slot
    for i in (0, 2, 5):
        run(root, f"b{i}", beams[i], 4, 2.4, m["radio_beam"], [2, 3], 0.05 * i, 0.45, 40)
    # beat 3: more users, second stream colour
    for i in (1, 3, 4, 6, 7):
        run(root, f"s{i}", beams[i], 3, 2.4, m["radio_beam2"], [3, 4], 0.05 * i, 0.5, 40)
    # beat 4: the whole array lights up; lobes fan from the panel to every user
    for i in range(len(USERS)):
        lb = K.lobe(m, root, f"lobe{i}", AAU_C, (USERS[i][0], 1.0, USERS[i][2]), width=4.0, n=2)
        show(lb, [(F(4, 0.1), F(5, 0))])

    C.tags(root, {
        0: [("macro tower, one unit on top", aau["top"]), ("dozens to hundreds of elements", aau["front"]),
            ("users on the street below", USERS[3])],
        1: [("one transceiver chain per element", chains[3]["top"]), ("phase and amplitude per element", chains[0]["top"])],
        2: [("beams to several phones at once", USERS[2]), ("same frequency, same slot", USERS[0])],
        3: [("more spatial streams", USERS[4]), ("no extra spectrum", USERS[6])],
        4: [("more elements: more streams", aau["front"]), ("capacity grows, spectrum fixed", USERS[7])],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 90.0, 60.0), 260.0, 0.20, 0.20, pad=1.0),
        frame((BX, 14.0, 0.0), 120.0, 0.25, 0.20, pad=1.0),
        frame((0.0, 90.0, 60.0), 240.0, -0.15, 0.25, pad=1.0),
        frame((0.0, 90.0, 60.0), 240.0, 0.30, 0.30, pad=1.0),
        frame((0.0, 100.0, 60.0), 280.0, 0.10, 0.22, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
