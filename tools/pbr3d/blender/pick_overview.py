"""The PICK node page's overview (BACK END tab), in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/pick_overview.py

Writes blender/pick_overview.blend and assets/pick_overview.glb. One beat is 8 s.

A sawn wafer on blue dicing tape in a steel frame, cut into a grid of die. A map panel at left shows
one square per die: green is good, red is bad. A vacuum chuck holds the tape. A collet lowers onto the
good die at the centre, needles push up through the tape, the collet lifts the die clear and swings it
to a carrier tray at right. A stack at the far right shows why one bad die matters. Sketch, not to scale.

Beats (match the six beats in diagrams_nodes/pick/overview.rs):
  0 good die only   the whole diorama: wafer on tape, map, collet hovering, carrier tray
  1 the map         the map panel: green good die, red bad die
  2 vacuum          the chuck holds the tape; the collet comes down and grips the centre die
  3 needles         needles push up through the tape; the die lifts; the collet holds it
  4 carrier         the collet swings the die to the tray; its neighbours stay on the tape
  5 known good die  the HBM stack: one red die scraps the whole stack
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, beat, box, disc, fly, label, show, tube, wall  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402

PAGE = "pick"
NAME = "overview"
BEATS = 6

PITCH = 24.0  # die pitch, mm (sketch scale)
DIE = 19.0  # die width, mm
DIE_T = 0.6  # die thickness, mm
RING = 130.0  # die whose centre lies inside this radius are on the wafer
BAD = {(2, 1), (3, 1), (2, 2), (-3, -2), (4, -3), (0, 4), (-4, 3), (-1, -4)}  # the map's bad die

# (camera target, distance, yaw, pitch), one per beat
POSES = [
    ((20.0, 70.0, 0.0), 1850.0, 0.25, 0.42),
    ((-150.0, 90.0, 60.0), 1050.0, 0.25, 0.25),
    ((0.0, 60.0, 0.0), 430.0, 0.35, 0.22),
    ((0.0, 40.0, 0.0), 330.0, 0.60, 0.12),
    ((200.0, 60.0, 0.0), 720.0, 0.30, 0.28),
    ((480.0, 50.0, 0.0), 430.0, 0.40, 0.18),
]


def shifted(path, dy):
    """The same path, raised by dy (mm)."""
    return [(x, y + dy, z) for x, y, z in path]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m["tape"] = O.mat("pick_tape", (0.30, 0.46, 0.72), rough=0.7)
    m["die"] = O.mat("pick_die", (0.32, 0.36, 0.42), metal=0.5, rough=0.3)
    m["ink"] = O.mat("pick_ink", (0.62, 0.08, 0.08), rough=0.5)
    m["ok"] = O.mat("pick_ok", (0.20, 0.65, 0.30), emit=(0.20, 0.65, 0.30), strength=1.0, rough=0.5)
    m["tray"] = O.mat("pick_tray", (0.85, 0.86, 0.90), rough=0.6)

    # the wafer on tape, in its frame, on the vacuum chuck
    disc("pick_tape", (0.0, -3.0, 0.0), 220.0, 6.0, m["tape"])
    wall("pick_frame", 232.0, -8.0, 4.0, 8.0, m["steel"])
    disc("pick_chuck", (0.0, -12.0, 0.0), 200.0, 12.0, m["dark_steel"])

    # the die grid; the centre die (0, 0) is the one picked
    dies = {}
    for i in range(-5, 6):
        for j in range(-5, 6):
            x, z = PITCH * i, PITCH * j
            if x * x + z * z > RING * RING:
                continue
            bad = (i, j) in BAD
            dies[(i, j)] = box(
                f"die_{i}_{j}",
                (x - DIE / 2, 0.0, z - DIE / 2),
                (x + DIE / 2, DIE_T, z + DIE / 2),
                m["ink"] if bad else m["die"],
            )

    # the map panel at left, one square per die (green good, red bad)
    box("pick_map_panel", (-420.0, 40.0, 170.0), (-300.0, 200.0, 180.0), m["dark_steel"])
    for i, j in dies:
        cx, cy = -360.0 + 10.0 * i, 120.0 + 10.0 * j
        box(
            f"map_{i}_{j}",
            (cx - 4.0, cy - 4.0, 180.0),
            (cx + 4.0, cy + 4.0, 183.0),
            m["ink"] if (i, j) in BAD else m["ok"],
        )

    # the carrier tray at right
    box("pick_tray", (300.0, 0.0, -60.0), (360.0, 14.0, 60.0), m["tray"])

    # the HBM stack at the far right: a base die, twelve DRAM dies, one of them bad
    box("pick_stack_base", (470.0, 0.0, -40.0), (530.0, 14.0, 40.0), m["dark_steel"])
    for k in range(12):
        y0 = 14.0 + 5.0 * k
        box(
            f"pick_stack_{k}",
            (470.0, y0, -40.0),
            (530.0, y0 + 4.0, 40.0),
            m["ink"] if k == 6 else m["die"],
        )

    # the pick: collet and hose, needles, and the die they lift
    collet = disc("pick_collet", (0.0, 150.0, 0.0), 14.0, 10.0, m["rubber"])
    hose = tube("pick_hose", (0.0, 155.0, 0.0), (0.0, 220.0, 0.0), 2.5, m["rubber"], verts=8)
    die = dies[(0, 0)]

    for sx in (-5.0, 5.0):
        for sz in (-5.0, 5.0):
            n = tube(f"pick_needle_{sx}_{sz}", (sx, -16.0, sz), (sx, 0.0, sz), 1.0, m["steel"], verts=8)
            show(n, [(F(3, 0.05), F(3, 0.8))])
            fly(n, [(sx, -8.0, sz), (sx, 0.0, sz)], F(3, 0.10), F(3, 0.50))

    # collet path: down onto the die (beat 2), up with the die (beat 3), across to the tray (beat 4).
    # The die rides 5.3 mm under the collet, and the hose 37.5 mm above it, so all three share one path.
    A = [(0.0, 150.0, 0.0), (0.0, 5.6, 0.0)]
    B = [(0.0, 5.6, 0.0), (0.0, 13.6, 0.0)]
    C = [(0.0, 13.6, 0.0), (0.0, 60.0, 0.0)]
    D = [(0.0, 60.0, 0.0), (330.0, 60.0, 0.0), (330.0, 19.6, 0.0)]
    fly(collet, A, F(2, 0.10), F(2, 0.50))
    fly(collet, B, F(3, 0.10), F(3, 0.50))
    fly(collet, C, F(3, 0.55), F(3, 0.90))
    fly(collet, D, F(4, 0.10), F(4, 0.60))
    fly(hose, shifted(A, 37.5), F(2, 0.10), F(2, 0.50))
    fly(hose, shifted(B, 37.5), F(3, 0.10), F(3, 0.50))
    fly(hose, shifted(C, 37.5), F(3, 0.55), F(3, 0.90))
    fly(hose, shifted(D, 37.5), F(4, 0.10), F(4, 0.60))
    fly(die, shifted(B, -5.3), F(3, 0.10), F(3, 0.50))
    fly(die, shifted(C, -5.3), F(3, 0.55), F(3, 0.90))
    fly(die, shifted(D, -5.3), F(4, 0.10), F(4, 0.60))

    tags = {
        0: [("wafer on blue tape", (-200.0, 22.0, 0.0)), ("pick-up collet", (40.0, 150.0, 0.0)),
            ("carrier tray", (330.0, 34.0, 0.0))],
        1: [("map: one bin per die", (-360.0, 205.0, 185.0)), ("green: good, picked", (-300.0, 150.0, 185.0)),
            ("red: bad, skipped", (48.0, 8.0, 24.0))],
        2: [("vacuum holds the die", (40.0, 40.0, 0.0)), ("chuck holds the tape", (-200.0, -12.0, 0.0))],
        3: [("needles push up", (-30.0, 8.0, 0.0)), ("die lifts off the tape", (-40.0, 40.0, 0.0))],
        4: [("neighbours stay on tape", (-48.0, 8.0, -48.0)), ("tray or Gel-Pak", (330.0, 40.0, 0.0))],
        5: [("one bad die", (560.0, 46.0, 0.0)), ("scraps the whole stack", (560.0, 88.0, 0.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))
    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
