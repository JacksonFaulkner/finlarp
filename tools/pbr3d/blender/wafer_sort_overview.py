"""The WAFER SORT node page's overview (BACK END row), in the picture-and-panel template
(docs/diagram-pages.md). Built on the SAND helpers (sand_overview, sand_zooms).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/wafer_sort_overview.py

Writes blender/wafer_sort_overview.blend and assets/wafer_sort_overview.glb. One beat is 8 s.

One cell, left to right: the ATE tester mainframe, the test head with its cables, the probe card
hanging under the head, the wafer on its vacuum chuck with a prober cursor stepping die to die,
and the wafer map monitor. Beads ride the cables, and the map's bins fill in one tile per die.

Beats (match the six beats in diagrams_nodes/wafer_sort/overview.rs):
  0 cell        the whole test cell: tester, head, card, wafer, map
  1 prober      the cursor steps the chuck die to die along one row
  2 contact     the card drops; needle tips land on the pads of four dies, overdrive scrubs
  3 tester      patterns go down the cables to the card; results come back up
  4 map         one tile per die fills in: green good, red bad; the map is the record
  5 hand-off    the map leaves for DICE and PICK; only good die go on

The wafer map is illustrative (a fixed pattern), not fab data.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402  (shared helpers: geometry, materials, keys, tags)
from sand_overview import F, P, box, disc, ball, tube, empty, show, label, beat, key, mat  # noqa: E402
from sand_zooms import start, camera, finish, stream_of  # noqa: E402

PAGE = "wafer_sort"
NAME = "overview"
BEATS = 6

DIE = 16.0  # die pitch on the wafer, mm
WAFER_R = 150.0
SITES = ((0, 0), (1, 0), (0, 1), (1, 1))  # the four dies probed at once (die indices)
MAP_PITCH = 30.0
MAP_X, MAP_Y, MAP_Z = 810.0, 320.0, -20.0

# (target, distance, yaw, pitch) per beat, mm; see docs/diagram-pages.md
POSES = [
    ((-80.0, 280.0, 0.0), 4000.0, 0.25, 0.12),
    ((-64.0, 60.0, 0.0), 600.0, 0.35, 0.55),
    ((8.0, 120.0, 8.0), 300.0, 0.25, 0.22),
    ((-560.0, 400.0, 0.0), 1700.0, 0.30, 0.12),
    ((810.0, 320.0, -20.0), 760.0, -0.05, 0.0),
    ((820.0, 300.0, -20.0), 1900.0, -0.10, 0.05),
]


def die_centres():
    """Die centres on the wafer: a grid of 16 mm pitch inside the round wafer."""
    out = []
    for i in range(-8, 9):
        for j in range(-8, 9):
            x, z = i * DIE, j * DIE
            if math.hypot(x, z) <= 132.0:
                out.append((i, j, x, z))
    return out


def map_tiles():
    """The illustrative bin map: tiles inside a circle of radius 4.5 tile pitches. Bad tiles follow
    a fixed pattern (not fab data); good is the rest."""
    out = []
    for tj in range(-4, 5):
        for ti in range(-4, 5):
            if ti * ti + tj * tj <= 20.5:
                bad = ti * ti + tj * tj >= 12 and (3 * ti + 5 * tj) % 6 == 0
                out.append((ti, tj, bad))
    return out


def materials(m):
    """Extra materials on top of the shared set that sand_zooms.start returns."""
    m["floor"] = mat("ws_floor", (0.24, 0.25, 0.27), rough=0.9)
    m["board"] = mat("ws_board", (0.10, 0.36, 0.22), rough=0.6)
    m["chuck"] = mat("ws_chuck", (0.30, 0.31, 0.34), metal=0.3, rough=0.7)
    m["tester"] = mat("ws_tester", (0.14, 0.15, 0.18), metal=0.5, rough=0.45)
    m["cable"] = mat("ws_cable", (0.06, 0.06, 0.07), rough=0.8)
    m["needle"] = mat("ws_needle", (0.80, 0.62, 0.30), metal=0.9, rough=0.3)
    m["pad"] = mat("ws_pad", (0.85, 0.86, 0.90), metal=0.9, rough=0.25)
    m["die"] = mat("ws_die", (0.20, 0.24, 0.30), metal=0.2, rough=0.4)
    m["untested"] = mat("ws_untested", (0.36, 0.37, 0.40), rough=0.8)
    m["good"] = mat("ws_good", (0.20, 0.90, 0.35), emit=(0.20, 0.90, 0.35), strength=2.5)
    m["bad"] = mat("ws_bad", (1.00, 0.25, 0.20), emit=(1.00, 0.20, 0.15), strength=2.5)
    m["probe"] = mat("ws_probe", (0.30, 0.90, 1.00), emit=(0.30, 0.90, 1.00), strength=4.0)
    m["bead"] = mat("ws_bead", (1.00, 0.85, 0.30), emit=(1.00, 0.80, 0.25), strength=6.0)
    m["screen"] = mat("ws_screen", (0.05, 0.06, 0.08), rough=0.4)
    return m


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    materials(m)

    box("floor", (-1400.0, -40.0, -400.0), (1400.0, 0.0, 400.0), m["floor"], root)

    # the ATE tester mainframe, and its cables up to the test head
    box("tester", (-1150.0, 0.0, -200.0), (-650.0, 620.0, 200.0), m["tester"], root)
    for k, z in enumerate((-40.0, -13.0, 13.0, 40.0)):
        tube(f"cable{k}", (-700.0, 600.0, z), (-170.0, 370.0, z), 9.0, m["cable"], root)

    # the probe card group: the test head, card and needles move together (beat 2 drops them)
    card = empty("ws_card", root)
    disc("head", (0.0, 360.0, 0.0), 180.0, 40.0, m["steel"], card)
    disc("card", (0.0, 300.0, 0.0), 165.0, 14.0, m["board"], card)
    for k in range(16):
        a = 2 * math.pi * k / 16
        x, z = 150.0 * math.cos(a), 150.0 * math.sin(a)
        tube(f"pogo{k}", (x, 340.0, z), (x, 308.0, z), 3.0, m["needle"], card)
    key(card, 0, "location", P(0.0, 0.0, 0.0))
    key(card, F(2, 0.4), "location", P(0.0, 0.0, 0.0))
    key(card, F(2, 0.7), "location", P(0.0, -22.0, 0.0))

    # the chuck and wafer, with every die (plain grey until the map fills in)
    disc("chuck", (0.0, 23.0, 0.0), 172.0, 46.0, m["chuck"], root)
    disc("wafer", (0.0, 52.0, 0.0), WAFER_R, 12.0, m["silicon"], root)
    dies = die_centres()
    for i, j, x, z in dies:
        box(f"die_{i}_{j}", (x - 7.0, 58.0, z - 7.0), (x + 7.0, 62.0, z + 7.0), m["die"], root)

    # the four probed dies: pads on top, needles from the card, a cyan glow while probing
    glow = empty("ws_site_glow", root)
    show(glow, [(F(2, 0.7), F(3, 0.9))])
    for i, j in SITES:
        cx, cz = i * DIE, j * DIE
        box(f"glow_{i}_{j}", (cx - 8.0, 63.0, cz - 8.0), (cx + 8.0, 63.5, cz + 8.0), m["probe"], glow)
        for dx in (-4.0, 4.0):
            for dz in (-4.0, 4.0):
                px, pz = cx + dx, cz + dz
                box(f"pad_{i}_{j}_{dx:+.0f}_{dz:+.0f}", (px - 2.5, 62.0, pz - 2.5), (px + 2.5, 63.0, pz + 2.5), m["pad"], root)
                tube(f"needle_{i}_{j}_{dx:+.0f}_{dz:+.0f}", (px, 293.0, pz), (px, 80.0, pz), 0.9, m["needle"], card)
                ball(f"tip_{i}_{j}_{dx:+.0f}_{dz:+.0f}", (px, 80.0, pz), 1.6, m["needle"], card, segs=8)

    # beat 1: the prober cursor steps along one row of dies
    cur = empty("ws_cursor", root)
    box("cursor_box", (-73.0, 63.0, -9.0), (-55.0, 64.0, 9.0), m["probe"], cur)
    show(cur, beat(1))
    path = [(16.0 * k, 0.0, 0.0) for k in range(9)]
    O.fly(cur, path, F(1, 0.0), F(2, 0.0), steps=8)

    # beat 3: patterns down the cables, results back up
    for k, z in enumerate((-40.0, -13.0, 13.0, 40.0)):
        stream_of(root, f"down{k}", 2, (-700.0, 600.0, z), [(0, 0, 0), (530.0, -230.0, 0)], 7.0, m["bead"], 3, 0.05, 0.5, 60)
        stream_of(root, f"up{k}", 2, (-170.0, 370.0, z), [(0, 0, 0), (-530.0, 230.0, 0)], 7.0, m["bead"], 3, 0.30, 0.75, 60)

    # the wafer map monitor: one tile per die, scanned in beat 4; bad tiles red
    box("map_stand", (MAP_X - 20.0, 0.0, -40.0), (MAP_X + 20.0, 150.0, -30.0), m["tester"], root)
    box("map_screen", (MAP_X - 170.0, 150.0, -30.0), (MAP_X + 170.0, 490.0, -26.0), m["screen"], root)
    tiles = map_tiles()
    for n, (ti, tj, bad) in enumerate(tiles):
        x = MAP_X + MAP_PITCH * ti
        y = MAP_Y + MAP_PITCH * tj
        box(f"tile_{ti}_{tj}", (x - 12.0, y - 12.0, -24.0), (x + 12.0, y + 12.0, -20.0), m["untested"], root)
        g = empty(f"res_{ti}_{tj}", root)
        box(f"res_box_{ti}_{tj}", (x - 11.0, y - 11.0, -20.0), (x + 11.0, y + 11.0, -18.0), m["bad" if bad else "good"], g)
        t0 = 0.08 + 0.80 * n / len(tiles)
        show(g, [(F(4, t0), F(6, 0))])

    # beat 5: the map leaves for DICE and PICK
    stream_of(root, "out", 3, (MAP_X + 180.0, MAP_Y, -28.0), [(0, 0, 0), (330.0, 0, 0)], 8.0, m["bead"], 5, 0.05, 0.6, 70)

    # tags, one set per beat
    label("ATE tester", (-1000.0, 620.0, 0.0), root, beat(0))
    label("probe card under the head", (0.0, 300.0, 175.0), root, beat(0))
    label("wafer on the chuck", (0.0, 58.0, 150.0), root, beat(0))
    label("wafer map: one bin per die", (MAP_X + 170.0, 320.0, -20.0), root, beat(0))
    label("prober steps die to die", (-64.0, 70.0, 60.0), root, beat(1))
    label("vacuum chuck holds the wafer", (0.0, 46.0, -150.0), root, beat(1))
    label("needle tips on the pads", (0.0, 66.0, 0.0), root, beat(2))
    label("overdrive presses the tips down", (16.0, 58.0, 20.0), root, beat(2))
    label("several dies probed at once", (8.0, 90.0, -30.0), root, beat(2))
    label("tester drives the patterns", (-900.0, 620.0, 0.0), root, beat(3))
    label("results come back as pass or fail", (-420.0, 520.0, 60.0), root, beat(3))
    label("head: pogo pins to the card", (-170.0, 395.0, 90.0), root, beat(3))
    label("one tile per die", (MAP_X - 160.0, MAP_Y + 130.0, -22.0), root, beat(4))
    label("green good, red bad", (MAP_X - 160.0, MAP_Y - 150.0, -22.0), root, beat(4))
    label("map sent to DICE and PICK", (MAP_X + 500.0, MAP_Y, -28.0), root, beat(5))
    label("only good die move on", (MAP_X - 160.0, MAP_Y - 150.0, -22.0), root, beat(5))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
