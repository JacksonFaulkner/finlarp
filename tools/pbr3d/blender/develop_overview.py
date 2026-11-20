"""The DEVELOP node page's overview (FAB flow, develop step), in the picture-and-panel template.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/develop_overview.py

Writes blender/develop_overview.blend and assets/develop_overview.glb. One beat is 8 s.

One picture: a slice across the wafer (silicon, film, resist lines, cut-open so the profile shows),
on a vacuum chuck inside a cut-away develop cup on the coater/developer track, with a hot plate and
a cool plate behind it. Glowing beads ride the real paths: developer and dissolved resist down the
drain, rinse water, etch ions into the trenches.

Beats (match the six beats in diagrams_nodes/develop/overview.rs):
  0 latent    the pattern is still invisible: exposed spaces hold a latent image, nothing removed yet
  1 puddle    a nozzle lays a TMAH puddle; exposed resist dissolves and the dissolved part drains off
  2 trenches  the exposed resist is gone to the film; the unexposed resist stands as a stencil
  3 rinse     DI water rinses the developer away and the wafer dries; one thin line leans
  4 bridge    redeposited resist bridges two neighbouring lines (magenta)
  5 stencil   the developed resist is the stencil; etch ions cut the film through the trenches

Units are drawn units (Y up, camera on +z, the slice is cut at z = 0 by the cup). The scene is built
at the same scale as the GRID page; labels are tags pinned on while their beat plays.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show, empty, mat, pivot, key, fly, cut, OFF  # noqa: E402
from sand_zooms import start  # noqa: E402
from power_grid_detail import MB, box, tube, ball, lathe, run, frame, camera_path, finish  # noqa: E402

PAGE = "develop"
NAME = "overview"
BEATS = 6

# swapped or extended by a later zoom script, as the GRID page does
LABEL = label
CAMERA = camera_path
EXTRA = None

SUB_TOP = 20.0  # top of the silicon
FILM_TOP = 30.0  # top of the film (SiO2-like) the resist sits on
RES_H = 60.0  # resist height above the film
RES_TOP = FILM_TOP + RES_H
LINE_HALF = 7.0  # resist line half width (14 wide)
X_LINES = [-136.0 + 34.0 * k for k in range(9)]  # 34 pitch, nine lines
X_GAPS = [x + 17.0 for x in X_LINES[:-1]]  # the exposed spaces between them
C_LINE = 4  # the centre line: the one that leans in beat 3 and is hidden then
LEAN = -0.2  # radians, toward the line on its left (rotation about the z axis, poly)
DRAIN = (150.0, -30.0, -80.0)  # cup drain, behind the cut


def arm(root, name, side, m):
    """A nozzle arm built at the origin: a bar reaching `side` (+1 right, -1 left), a drop, a tip.
    fly() moves the group in from off to the side, over the wafer centre."""
    grp = empty(name, root)
    mb = MB()
    mb.tube((0.0, 200.0, 0.0), (300.0 * side, 200.0, 0.0), 3.0, 8)
    mb.tube((0.0, 200.0, 0.0), (0.0, 112.0, 0.0), 2.2, 8)
    mb.ball((0.0, 108.0, 0.0), 6.0, 10)
    mb.obj(f"{name}_arm", m["nozzle"], grp, smooth=True)
    return grp


def build_track(root, m):
    """The floor, a hot plate and a cool plate on the track behind the develop cup."""
    box("dev_floor", (-620.0, -140.0, -320.0), (620.0, -130.0, 60.0), m["floor"], root)
    box("dev_hotplate", (-520.0, -130.0, -240.0), (-380.0, -96.0, -150.0), m["track"], root)
    box("dev_hotplate_top", (-515.0, -100.0, -235.0), (-385.0, -96.0, -155.0), m["hot"], root)
    box("dev_coolplate", (380.0, -130.0, -240.0), (520.0, -96.0, -150.0), m["track"], root)
    box("dev_coolplate_top", (385.0, -100.0, -235.0), (515.0, -96.0, -155.0), m["cool"], root)


def build_wafer(root, m):
    """The slice: chuck, silicon, film, and resist lines with the exposed spaces between them."""
    box("dev_spindle", (-14.0, -120.0, -14.0), (14.0, -20.0, 14.0), m["chuck"], root)
    box("dev_chuck", (-165.0, -20.0, -60.0), (165.0, 0.0, 60.0), m["chuck"], root)
    box("dev_si", (-150.0, 0.0, -50.0), (150.0, SUB_TOP, 50.0), m["si"], root)
    box("dev_film", (-150.0, SUB_TOP, -50.0), (150.0, FILM_TOP, 50.0), m["film"], root)

    mb = MB()
    for k, x in enumerate(X_LINES):
        if k != C_LINE:
            mb.box((x - LINE_HALF, FILM_TOP, -50.0), (x + LINE_HALF, RES_TOP, 50.0))
    mb.obj("dev_lines", m["resist"], root)

    # the centre line stands on its own so it can lean in beat 3
    c_line = box("dev_line_c", (X_LINES[C_LINE] - LINE_HALF, FILM_TOP, -50.0),
                 (X_LINES[C_LINE] + LINE_HALF, RES_TOP, 50.0), m["resist"], root)
    show(c_line, [(F(0, 0), F(3, 0)), (F(4, 0), F(6, 0))])

    # the exposed spaces: latent in beat 0, dissolved in beat 1 (each pivots on its base)
    for i, gx in enumerate(X_GAPS):
        pv = pivot(f"dev_gap{i}", (gx, FILM_TOP, 0.0), root)
        g = MB()
        g.box((-10.0, 0.0, -50.0), (10.0, RES_H, 50.0))
        g.obj(f"dev_gap{i}_latent", m["latent"], pv)
        key(pv, F(1, 0.35), "scale", (1.0, 1.0, 1.0))
        key(pv, F(1, 0.8), "scale", (1.0, OFF, 1.0))

    # the lean: the centre line on its own pivot, tilting toward its left neighbour in beat 3
    lean = pivot("dev_lean", (X_LINES[C_LINE], FILM_TOP, 0.0), root)
    lm = MB()
    lm.box((-LINE_HALF, 0.0, -50.0), (LINE_HALF, RES_H, 50.0))
    lm.obj("dev_lean_line", m["resist"], lean)
    show(lean, [(F(3, 0), F(4, 0))])
    key(lean, F(3, 0.1), "rotation_euler", (0.0, 0.0, 0.0))
    key(lean, F(3, 0.75), "rotation_euler", (0.0, LEAN, 0.0))


def build_cup(root, m):
    """The develop cup, cut open so the wafer shows, with its drain behind the cut."""
    wall = lathe("dev_cup_wall", [(196.0, -30.0), (196.0, 46.0)], m["cup"], root, n=48)
    cut(wall, z=0.0)
    floor = lathe("dev_cup_floor", [(170.0, -30.0), (196.0, -30.0)], m["cup"], root, n=48)
    cut(floor, z=0.0)
    tube("dev_drain", (DRAIN[0], -30.0, DRAIN[2]), (DRAIN[0], -110.0, DRAIN[2]), 10.0, m["drain"], root)


def build_beads(root, m):
    """Beads on the real paths: dissolved resist drains from each space (beat 1); rinse water runs
    across and off (beat 3); etch ions drop into each trench (beat 5)."""
    for i, gx in enumerate(X_GAPS):
        path = [(gx, 70.0, 0.0), (gx, 35.0, 0.0), (110.0, 20.0, -40.0), DRAIN, (DRAIN[0], -100.0, DRAIN[2])]
        run(root, f"dev_dis{i}", path, 2, 3.5, m["dissolved"], 1, 0.42, 0.9, 44)
    run(root, "dev_water", [(0.0, 104.0, 0.0), (130.0, 96.0, 0.0), (150.0, 60.0, -40.0), DRAIN,
                            (DRAIN[0], -100.0, DRAIN[2])], 10, 4.0, m["water"], 3, 0.3, 0.8, 56)
    for i, gx in enumerate(X_GAPS):
        run(root, f"dev_ion{i}", [(gx, 160.0, 0.0), (gx, 30.0, 0.0)], 2, 3.2, m["ion"], 5, 0.0, 0.8, 36)


def build_puddle_and_defect(root, m):
    """The developer puddle over the wafer (beat 1 to 2) and the magenta bridge (beat 4)."""
    puddle = box("dev_puddle", (-152.0, RES_TOP, -54.0), (152.0, RES_TOP + 10.0, 54.0), m["tmah"], root)
    show(puddle, [(F(1, 0.3), F(2, 0.4))])
    bridge = box("dev_bridge", (-26.0, 76.0, -12.0), (-8.0, 84.0, 12.0), m["bridge"], root)
    show(bridge, [(F(4, 0.15), F(6, 0))])


def build_arms(root, m):
    """The develop nozzle (beat 1) and the rinse nozzle (beat 3), each swept in over the centre."""
    dev = arm(root, "dev_develop", +1, m)
    show(dev, [(F(1, 0.0), F(2, 0.0))])
    fly(dev, [(300.0, 0.0, 0.0), (0.0, 0.0, 0.0)], F(1, 0.0), F(1, 0.3))
    rinse = arm(root, "dev_rinse", -1, m)
    show(rinse, [(F(3, 0.0), F(4, 0.0))])
    fly(rinse, [(-300.0, 0.0, 0.0), (0.0, 0.0, 0.0)], F(3, 0.0), F(3, 0.25))


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update({
        "si": mat("dev_si", (0.16, 0.18, 0.22), metal=0.3, rough=0.4),
        "film": mat("dev_film", (0.42, 0.50, 0.58), rough=0.5),
        "resist": mat("dev_resist", (0.62, 0.42, 0.20), rough=0.6),
        "latent": mat("dev_latent", (1.0, 0.85, 0.45), emit=(1.0, 0.8, 0.4), strength=1.2, alpha=0.7),
        "tmah": mat("dev_tmah", (0.55, 0.80, 1.0), rough=0.1, alpha=0.4),
        "water": mat("dev_water", (0.35, 0.90, 1.0), emit=(0.3, 0.85, 1.0), strength=2.5),
        "dissolved": mat("dev_dissolved", (1.0, 0.55, 0.15), emit=(1.0, 0.5, 0.12), strength=3.0),
        "bridge": mat("dev_bridge", (1.0, 0.25, 0.7), emit=(1.0, 0.2, 0.6), strength=3.5),
        "ion": mat("dev_ion", (0.75, 0.55, 1.0), emit=(0.7, 0.5, 1.0), strength=3.0),
        "nozzle": mat("dev_nozzle", (0.75, 0.77, 0.80), metal=0.8, rough=0.3),
        "chuck": mat("dev_chuck", (0.22, 0.23, 0.25), metal=0.6, rough=0.4),
        "cup": mat("dev_cup", (0.86, 0.87, 0.87), rough=0.5),
        "track": mat("dev_track", (0.30, 0.32, 0.36), metal=0.4, rough=0.5),
        "floor": mat("dev_floor", (0.40, 0.41, 0.43), rough=0.7),
        "hot": mat("dev_hot", (0.85, 0.35, 0.15), emit=(1.0, 0.35, 0.1), strength=1.0),
        "cool": mat("dev_cool", (0.25, 0.45, 0.70), metal=0.2, rough=0.4),
        "drain": mat("dev_drain", (0.30, 0.31, 0.33), metal=0.5, rough=0.5),
    })
    build_track(root, m)
    build_wafer(root, m)
    build_cup(root, m)
    build_puddle_and_defect(root, m)
    build_arms(root, m)
    build_beads(root, m)
    if EXTRA:
        EXTRA(m, root)

    tags = {
        0: [("latent image: exposed, not yet removed", (-17.0, 100.0, 0.0)),
            ("hot and cool plates on the track", (-450.0, -60.0, -200.0))],
        1: [("develop nozzle", (0.0, 200.0, 0.0)), ("TMAH puddle", (-120.0, 106.0, 0.0)),
            ("exposed resist dissolves", (17.0, 62.0, 0.0))],
        2: [("trench: exposed resist gone", (17.0, 70.0, 0.0)), ("line: unexposed resist", (0.0, 100.0, 0.0))],
        3: [("DI water rinse", (0.0, 130.0, 0.0)), ("thin line leans", (-14.0, 96.0, 0.0))],
        4: [("bridge: redeposited resist", (-17.0, 92.0, 0.0))],
        5: [("ions carve the film", (17.0, 150.0, 0.0)), ("resist stencil", (0.0, 100.0, 0.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            LABEL(text, pos, root, beat(i))
    CAMERA(root, POSES)
    return root


# one pose per beat (target, distance, yaw, pitch), from camera.frame
POSES = [
    frame((0.0, 120.0, 0.0), 700.0, 0.30, 0.20),
    frame((30.0, 100.0, 0.0), 420.0, 0.25, 0.15),
    frame((0.0, 60.0, 0.0), 300.0, 0.10, 0.05),
    frame((0.0, 100.0, 0.0), 420.0, -0.25, 0.20),
    frame((-30.0, 70.0, 0.0), 220.0, 0.05, 0.08),
    frame((0.0, 100.0, 0.0), 520.0, 0.40, 0.25),
]


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
