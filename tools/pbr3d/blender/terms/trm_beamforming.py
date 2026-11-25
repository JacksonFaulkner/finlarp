"""TRM_BEAMFORMING: the Terms-tab overview for beamforming, on the telecom-radio kit.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_beamforming.py

Writes assets/term_TRM_BEAMFORMING.glb. Captions live in specs/terms/TRM_BEAMFORMING.json.

An array panel on a mast faces a phone down the street. A beamformer chip on the bench is cut
open to show its phase-shifter blocks. Each element's phase is set so the waves add up in one
direction; the beam then follows the phone as it moves.

Beats:
  0 array     the panel, the phone down the street
  1 chip      the beamformer chip cut open: one phase shifter per element
  2 phase     each element's wave is shifted; the wavefronts tilt toward the phone
  3 lock      the waves add up on the phone and cancel elsewhere
  4 follow    the phone moves; the beam re-steers, the old direction goes quiet
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402
import kit_radio as K  # noqa: E402

SLUG = "TRM_BEAMFORMING"
BEATS = [
    ("A panel of elements, one phone down the street",
     "A phased-array panel is a grid of small antennas that all transmit the same signal. The base station's "
     "beamformer decides what each element sends, so one panel can point its energy at a chosen phone."),
    ("Inside the beamformer: a phase shifter and amplitude control per element",
     "The beamformer chip splits the signal across channels. Each channel has a phase shifter and a gain stage, so each "
     "element's copy of the signal can be delayed and scaled independently. Phone handsets use a small version of the same idea."),
    ("Shift each element's phase and the waves tilt toward the phone",
     "Waves from neighbouring elements are offset by a small phase step. The steps tilt the wavefront, and the energy "
     "piles up in the direction the phase steps point, like a flashlight beam made of many small sources."),
    ("The waves add up on the phone and cancel in other directions",
     "In the chosen direction the copies arrive in step and add up, which gives more signal strength and less interference "
     "for everyone else. Mmwave phones and small cells rely on this to reach a handset without wasting power on empty space."),
    ("The phone moves and the beam follows it",
     "When the phone moves the beamformer recomputes the phase steps and re-aims the beam, dropping the old direction. "
     "Beamforming chips from Qualcomm (QCOM), Skyworks (SWKS), Qorvo (QRVO) and Ericsson (ERIC) sit in this path."),
]

PANEL = (0.0, 40.0, 0.0)
PHONE_A = (-40.0, 1.0, 140.0)
PHONE_B = (60.0, 1.0, 170.0)
BX = 200.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.radio_materials(m)
    K.ground(m, root, "street", -160.0, 160.0, -180.0, 200.0)
    K.phone(m, root, "phoneA", PHONE_A, s=1.6)
    K.phone(m, root, "phoneB", PHONE_B, s=1.6)
    panel = K.antenna_panel(m, root, "panel", (0.0, 44.0, 2.6), nx=8, ny=6, pitch=3.0, size=2.0)

    # the bench: a beamformer chip, cut open, with its phase shifters in a row
    bf = K.beamformer(m, root, "bf", (BX, 4.0, 0.0), n=8, s=3.0)
    show(bf["group"], [(F(1, 0.0), F(2, 0))])

    # beat 2: the phase steps, drawn as rays fanned toward phone A, each element a little later
    rays = K.steer_paths((0.0, 44.0, 2.6), [-35.0, -20.0, -8.0, 4.0, 16.0], length=170.0)
    for k, r in enumerate(rays):
        run(root, f"ray{k}", r, 4, 1.6, m["radio_beam"], [2, 3], 0.05 * k, 0.6, 40)
    # beat 3: the lock; lobe toward A, the other direction quiet
    lb = K.lobe(m, root, "lobeA", (0.0, 44.0, 2.6), PHONE_A, width=10.0, n=4)
    show(lb, [(F(3, 0.1), F(5, 0))])
    for k, r in enumerate(K.beam_paths((0.0, 44.0, 2.6), PHONE_A, n=3, spread=6.0)):
        run(root, f"lock{k}", r, 3, 1.8, m["radio_beam"], [3], 0.1, 0.8, 40)
    # beat 4: phone B now; beam re-steers, the old lobe goes out
    for k, r in enumerate(K.beam_paths((0.0, 44.0, 2.6), PHONE_B, n=3, spread=6.0)):
        run(root, f"follow{k}", r, 3, 1.8, m["radio_beam2"], [4], 0.1, 0.8, 40)

    C.tags(root, {
        0: [("one panel, many elements", panel["top"]), ("phone down the street", PHONE_A)],
        1: [("phase shifter per element", bf["pads"][3]), ("gain per channel", bf["top"])],
        2: [("phase step tilts the wavefront", rays[2][2]), ("same signal, shifted", rays[0][2])],
        3: [("waves add up on the phone", PHONE_A), ("less energy elsewhere", rays[0][2])],
        4: [("phone moves, beam follows", PHONE_B), ("old direction goes quiet", PHONE_A)],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 40.0, 60.0), 300.0, 0.20, 0.20, pad=1.0),
        frame((BX, 6.0, 0.0), 120.0, 0.25, 0.22, pad=1.0),
        frame((0.0, 40.0, 60.0), 300.0, 0.10, 0.25, pad=1.0),
        frame((0.0, 40.0, 60.0), 300.0, -0.10, 0.25, pad=1.0),
        frame((20.0, 30.0, 80.0), 320.0, 0.15, 0.22, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
