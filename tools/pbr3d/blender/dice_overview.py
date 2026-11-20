"""The DICE node page's overview (BACK END tab), in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/dice_overview.py

Writes blender/dice_overview.blend and assets/dice_overview.glb. One beat is 8 s.

One wafer on its ring frame, drawn large and not to scale (the thickness and the streets are
exaggerated so they read): a wafer lies on blue dicing tape stretched across a steel ring frame,
its die drawn as a grid with the scribe streets as the silicon gaps between them. A diamond blade
travels one street and cuts into the tape; a stealth laser focuses inside the silicon (a translucent
wafer shows the modified layer); low-k streets are grooved by a laser before the blade finishes;
the tape is stretched so the die part, the good ones lift off and the bad ones stay on the tape.

Beats (match the six beats in diagrams_nodes/dice/overview.rs):
  0 frame     the thinned wafer on dicing tape, held in a steel ring frame
  1 streets   the scribe streets between die; the dies are drawn large
  2 blade     a diamond blade cuts one street, into the tape but not through it
  3 stealth   a laser focuses inside the silicon; a see-through wafer shows the modified layer
  4 low-k     laser grooves the low-k street first, then the blade finishes
  5 pick      the tape is stretched; good die lift off, bad die stay on the tape
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, ball, disc, empty, key, label, mat, show, fly, wall  # noqa: E402
from sand_zooms import start  # noqa: E402
from power_grid_detail import finish, frame, camera_path  # noqa: E402

PAGE = "dice"
NAME = "overview"
BEATS = 6

LABEL = label
CAMERA = camera_path

WAFER_R = 150.0  # the silicon wafer's radius, mm (drawn at this size, not to scale)
WAFER_Y0, WAFER_Y1 = 0.0, 6.0  # thickness drawn thick so it reads (not to scale)
TOP = WAFER_Y1  # the silicon's top face
DIE = 26.0  # die side
PITCH = 30.0  # die pitch: a 4 mm street between die (drawn wide)
DIE_H = 1.2  # die stand-up height above the silicon
TAPE_Y = -1.0  # tape centre height
TAPE_R = 185.0
BLADE_R = 18.0
BLADE_Y = 12.0  # blade centre: its bottom reaches into the tape
CUT_Z0, CUT_Z1 = -150.0, 150.0
STREET_X = 0.0  # the street the blade and the stealth laser travel along

# (camera target, distance, yaw, pitch) per beat, from power_grid_detail.frame
POSES = [
    frame((0.0, 0.0, 0.0), 420.0, 0.55, 0.40, pad=1.0),
    frame((0.0, TOP, -40.0), 110.0, 0.45, 0.28),
    frame((0.0, 10.0, 0.0), 110.0, 0.90, 0.22),
    frame((0.0, 3.0, -60.0), 150.0, 0.60, 0.12),
    frame((0.0, TOP, -20.0), 90.0, 0.70, 0.30),
    frame((0.0, 0.0, 0.0), 420.0, 0.35, 0.50, pad=1.0),
]

# the bad die (inked at wafer sort) and the good ones the picker lifts, as (column, row) indexes
BAD = {(-1, 2), (1, -2), (-3, -2)}
LIFT = {(2, -1), (0, -2), (-2, 0)}


def die_grid():
    """Die centres: half-pitch offsets so a street (x = 0 and z = 0) runs through the middle."""
    out = []
    for i in range(-6, 6):
        for j in range(-6, 6):
            cx, cz = (i + 0.5) * PITCH, (j + 0.5) * PITCH
            if math.hypot(cx, cz) + DIE * 0.71 <= WAFER_R - 4.0:
                out.append((i, j, cx, cz))
    return out


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)

    steel = mat("dice_steel", (0.35, 0.37, 0.42), metal=0.6, rough=0.4)
    silicon = mat("dice_silicon", (0.55, 0.58, 0.64), metal=0.9, rough=0.22)
    ghost = mat("dice_wafer_ghost", (0.55, 0.58, 0.64), metal=0.2, rough=0.3, alpha=0.3)
    tape = mat("dice_tape", (0.20, 0.35, 0.70), rough=0.8)
    die_m = mat("dice_die", (0.10, 0.14, 0.28), metal=0.3, rough=0.35)
    bad_m = mat("dice_bad_die", (0.75, 0.15, 0.12), rough=0.5)
    bench = mat("dice_bench", (0.12, 0.13, 0.15), rough=0.9)
    blade_m = mat("dice_blade", (0.55, 0.55, 0.60), metal=0.8, rough=0.3)
    laser_m = mat("dice_laser", (1.0, 0.45, 0.20), emit=(1.0, 0.4, 0.15), strength=10.0)
    groove_m = mat("dice_groove", (0.03, 0.03, 0.04), rough=0.9)
    crack_m = mat("dice_crack", (1.0, 0.85, 0.55), emit=(1.0, 0.8, 0.45), strength=2.0, alpha=0.7)

    box("dice_bench", (-420.0, -30.0, -420.0), (420.0, -3.0, 420.0), bench, root)
    disc("dice_tape", (0.0, TAPE_Y, 0.0), TAPE_R, 1.0, tape, root, verts=128)
    wall("dice_frame", TAPE_R + 6.0, -3.0, 6.0, 8.0, steel, root)

    wafer = disc("dice_wafer", (0.0, (WAFER_Y0 + WAFER_Y1) / 2, 0.0), WAFER_R, WAFER_Y1 - WAFER_Y0, silicon, root, verts=128)
    ghost_w = disc("dice_wafer_ghost", (0.0, (WAFER_Y0 + WAFER_Y1) / 2, 0.0), WAFER_R, WAFER_Y1 - WAFER_Y0, ghost, root, verts=128)

    # the die, one object each so they can drop, spread and lift
    for i, j, cx, cz in die_grid():
        rest = (cx, TOP + DIE_H / 2, cz)
        bad = (i, j) in BAD
        o = box(f"dice_die_{i}_{j}", (cx - DIE / 2, TOP, cz - DIE / 2), (cx + DIE / 2, TOP + DIE_H, cz + DIE / 2),
                bad_m if bad else die_m, root)
        key(o, 0, "location", P(*rest))
        key(o, F(5, 0.2), "location", P(*rest))
        spread = (cx * 1.15, TAPE_Y + 0.5 + DIE_H / 2, cz * 1.15)
        key(o, F(5, 0.65), "location", P(*spread), linear=True)
        if (i, j) in LIFT:
            key(o, F(5, 0.80), "location", P(spread[0], spread[1] + 40.0, spread[2]), linear=True)

    # the blade: a pivot that rides the street (mounted so its spin axis lies along x), and a
    # child disc that spins about that axis
    blade = empty("dice_blade_pivot", root)
    blade.rotation_euler = (0.0, math.pi / 2, 0.0)
    disc_b = disc("dice_blade", (0.0, 0.0, 0.0), BLADE_R, 1.6, blade_m, blade, verts=64)
    key(disc_b, 0, "rotation_euler", (0.0, 0.0, 0.0), linear=True)
    key(disc_b, F(6, 0), "rotation_euler", (0.0, 0.0, math.tau * 40.0), linear=True)
    # each show() starts on the frame its first position key lands, so nothing shows at the origin
    cut_path = [(STREET_X, BLADE_Y, CUT_Z0), (STREET_X, BLADE_Y, CUT_Z1)]
    fly(blade, cut_path, F(2, 0.10), F(2, 0.90))
    fly(blade, cut_path, F(4, 0.60), F(4, 0.95))
    show(blade, [(F(2, 0.10), F(2, 0.95)), (F(4, 0.60), F(4, 0.97))])

    # the stealth laser: inside the silicon in beat 3, then along the two low-k grooves in beat 4
    las = empty("dice_laser_pivot", root)
    ball("dice_laser", (0.0, 0.0, 0.0), 4.0, laser_m, las)
    fly(las, [(STREET_X, 3.0, CUT_Z0), (STREET_X, 3.0, CUT_Z1)], F(3, 0.10), F(3, 0.90))
    fly(las, [(-1.2, TOP + 2.0, CUT_Z0), (-1.2, TOP + 2.0, CUT_Z1)], F(4, 0.10), F(4, 0.32))
    fly(las, [(1.2, TOP + 2.0, CUT_Z1), (1.2, TOP + 2.0, CUT_Z0)], F(4, 0.32), F(4, 0.54))
    show(las, [(F(3, 0.10), F(3, 0.90)), (F(4, 0.10), F(4, 0.56))])

    # the modified layer (beat 3), and the two low-k grooves once the laser has passed
    crack = box("dice_crack", (-0.5, 0.5, CUT_Z0), (0.5, WAFER_Y1 - 0.5, CUT_Z1), crack_m, root)
    show(crack, [(F(3, 0.10), F(4, 0.0))])
    for side, x, t0 in (("a", -1.8, F(4, 0.12)), ("b", 1.8, F(4, 0.34))):
        g = box(f"dice_groove_{side}", (x - 0.6, TOP - 1.5, CUT_Z0), (x + 0.6, TOP + 0.4, CUT_Z1), groove_m, root)
        show(g, [(t0, F(6, 0))])

    # the wafer is see-through in beat 3 (its ghost shows the modified layer), and gone once the tape stretches
    show(wafer, [(F(0, 0), F(3, 0)), (F(4, 0), F(5, 0.2))])
    show(ghost_w, [(F(3, 0), F(4, 0))])

    # labels, per beat
    tags = {
        0: [("thinned wafer", (0.0, 30.0, 60.0)), ("dicing tape", (120.0, TAPE_Y, 130.0)),
            ("steel ring frame", (TAPE_R + 6.0, 14.0, 0.0))],
        1: [("scribe street", (STREET_X, TOP + 14.0, -60.0)), ("die", (45.0, TOP + 14.0, 45.0))],
        2: [("diamond blade", (30.0, 40.0, 0.0)), ("cut into the tape, not through it", (0.0, 4.0, -120.0))],
        3: [("laser focused inside", (0.0, 3.0, -40.0)), ("modified layer, no kerf", (0.0, 14.0, -100.0))],
        4: [("low-k: laser grooves first", (-1.8, TOP + 8.0, 60.0)), ("blade finishes the cut", (30.0, 40.0, -30.0))],
        5: [("tape stretched: gaps grow", (100.0, 20.0, 100.0)), ("good die lifted", (45.0, 60.0, -15.0)),
            ("bad die stays on the tape", (-15.0, 8.0, 45.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            LABEL(text, pos, root, beat(i))

    CAMERA(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
