"""The INTERPOSER overview (PACKAGING tab), in the SAND template (docs/diagram-pages.md).

Run from the repo root (on the worker, or locally if you want):

    blender -b --factory-startup --python tools/pbr3d/blender/interposer_overview.py

Writes blender/interposer_overview.blend and assets/interposer_overview.glb. One beat is 8 s.

Beats (match INTERPOSER in diagrams_pkg_nodes.rs, I_B):
  0 the interposer: wiring under the dies   a silicon interposer with copper traces, one die, four stacks
  1 data runs across it                     cyan data from each of the four stacks, across the traces, under the die
  2 power climbs up through TSVs            the interposer goes see-through: TSVs, yellow power climbing into the die
  3 CoWoS-S: one silicon slab               the full package on a substrate, all silicon, slab ~2,700 mm2
  4 CoWoS-L: silicon bridges                two dies, eight stacks, cyan bridges under the seam, organic slab
  5 growing past the reticle                the organic slab grows to ~9.5 reticles and 12 stacks
  6 the whole package on its board          the package on the board, BGA under it
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, label, beat, show, tube  # noqa: E402
from sand_zooms import start, camera, finish, stream_of, scale_keys  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402
import pkg_kit as K  # noqa: E402

PAGE = "interposer"
NAME = "overview"
BEATS = 7

# Beat 5 grows the organic slab from 52 mm to 90 mm square: 90 mm is ~9.5 reticle fields (858 mm2 each).
GROW = 45.0 / 26.0

POSES = [
    ((0.0, 2.0, 0.0), 110.0, 0.60, 0.35),
    ((0.0, 3.0, 0.0), 110.0, 0.50, 0.30),
    ((0.0, 0.0, 0.0), 100.0, 0.45, -0.25),
    ((0.0, -2.0, 0.0), 170.0, 0.60, 0.30),
    ((0.0, 0.0, 0.0), 110.0, 0.50, 0.30),
    ((0.0, 0.0, 0.0), 170.0, 0.60, 0.30),
    ((0.0, -6.0, 0.0), 200.0, 0.50, 0.25),
]


def from_beat(k):
    return [(F(k, 0), F(BEATS, 0))]


def until_beat(k):
    return [(F(0, 0), F(k, 0))]


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = K.materials()
    trace = mat("pkg_trace_copper", (0.62, 0.38, 0.24), metal=0.9, rough=0.35)
    glass = mat("pkg_si_glass", (0.30, 0.36, 0.40), rough=0.2, alpha=0.25)

    # Silicon interposer under one die and four stacks, beats 0-3. Beat 2 is see-through so the TSVs show.
    si = empty("si_small", root)
    show(si, [(F(0, 0), F(2, 0)), (F(3, 0), F(4, 0))])
    K.interposer(m, si, half=26.0, name="si_small_plate")
    si_glass = empty("si_glass", root)
    show(si_glass, [(F(2, 0), F(3, 0))])
    box("si_glass_plate", (-26.0, K.IP_BOT, -26.0), (26.0, K.IP_TOP, 26.0), glass, si_glass)

    # Fine wiring on the silicon, beats 0-3: copper traces every 2 mm each way.
    traces = empty("traces", root)
    show(traces, [(F(0, 0), F(2, 0)), (F(3, 0), F(4, 0))])
    for i in range(-12, 13):
        c = 2.0 * i
        box(f"tr_x_{i}", (-24.0, K.IP_TOP, c - 0.12), (24.0, K.IP_TOP + 0.12, c + 0.12), trace, traces)
        box(f"tr_z_{i}", (c - 0.12, K.IP_TOP, -24.0), (c + 0.12, K.IP_TOP + 0.12, 24.0), trace, traces)

    # Beat 1 swaps the die and the four stacks for see-through copies so the data under them shows.
    opaque = [(F(0, 0), F(1, 0)), (F(2, 0), F(4, 0))]
    die_glass_m = mat("pkg_die_glass", (0.42, 0.30, 0.72), rough=0.2, alpha=0.25)
    hbm_glass_m = mat("pkg_hbm_glass", (0.72, 0.74, 0.78), rough=0.2, alpha=0.25)
    die_one = empty("die_one", root)
    show(die_one, opaque)
    K.die(m, die_one)
    die_see = empty("die_see", root)
    show(die_see, [(F(1, 0), F(2, 0))])
    box("die_see_part", (-K.DIE_HALF_X, K.UB_TOP, -K.DIE_HALF_Z), (K.DIE_HALF_X, K.DIE_TOP, K.DIE_HALF_Z), die_glass_m, die_see)

    # Four stacks on the die's shoreline, beats 0-3; eight in beat 4; twelve from beat 5.
    stacks4 = empty("stacks4", root)
    show(stacks4, opaque)
    K.stacks(m, stacks4, zs=(-9.0, 9.0), inner=16.5)
    stacks4_see = empty("stacks4_see", root)
    show(stacks4_see, [(F(1, 0), F(2, 0))])
    K.stacks({"hbm": hbm_glass_m}, stacks4_see, zs=(-9.0, 9.0), inner=16.5)
    stacks8 = empty("stacks8", root)
    show(stacks8, [(F(4, 0), F(5, 0))])
    K.stacks(m, stacks8, zs=(-21.0, -9.0, 9.0, 21.0), inner=16.5)
    stacks12 = empty("stacks12", root)
    show(stacks12, from_beat(5))
    K.stacks(m, stacks12, zs=(-33.0, -21.0, -9.0, 9.0, 21.0, 33.0), inner=16.5)

    # TSVs, beat 2: twelve copper columns through the see-through silicon.
    tsvs = empty("tsvs", root)
    show(tsvs, [(F(2, 0), F(3, 0))])
    for x in (-9.0, -3.0, 3.0, 9.0):
        for z in (-9.0, 0.0, 9.0):
            tube(f"tsv_{x}_{z}", (x, K.IP_BOT, z), (x, K.IP_TOP, z), 0.5, m["copper"], tsvs, 12)

    # CoWoS-L, beats 4-6: organic slab with two dies and bridges. It grows in the first half of beat 5.
    org = empty("org_grp", root)
    show(org, from_beat(4))
    grow = empty("org_grow", org)
    scale_keys(grow, [(0, 1), (F(5, 0), 1), (F(5, 0.5), (GROW, 1, GROW))])
    K.interposer(m, grow, half=26.0, name="org_plate", mat_name="organic")
    dies2 = empty("dies_two", root)
    show(dies2, from_beat(4))
    K.die(m, dies2, x0=-13.5, x1=-2.5, name="die_left", mat_name="die")
    K.die(m, dies2, x0=2.5, x1=13.5, name="die_right", mat_name="die")
    bridges = empty("bridges", root)
    show(bridges, from_beat(4))
    for k, zc in enumerate((-12.0, -4.0, 4.0, 12.0)):
        box(f"bridge_{"abcd"[k]}", (-3.5, 1.5, zc - 2.5), (3.5, 2.4, zc + 2.5), m["bridge"], bridges)

    # Substrate, C4, board and BGA for the package: beats 3-6, the board from the same beat.
    sub = empty("substrate_grp", root)
    show(sub, from_beat(3))
    K.substrate(m, sub, half=50.0)
    c4 = empty("c4_grp", root)
    show(c4, from_beat(3))
    K.c4(m, c4, half=30.0)
    board_grp = empty("board_grp", root)
    show(board_grp, from_beat(3))
    K.board(m, board_grp)
    K.bga(m, board_grp, half=40.0)

    # Data (beat 1): from inside each of the four stacks, across the traces, under the die edge.
    data_m = m["data"]
    for side in (-1, 1):
        for zc in (-9.0, 9.0):
            name = f"data_{'l' if side < 0 else 'r'}_{'n' if zc < 0 else 'p'}"
            stream_of(root, name, 5, (side * 21.5, 2.3, zc), [(0, 0, 0), (-side * 11.0, 0, 0)],
                      1.0, data_m, 1, 0.05, 0.85, 60)

    # Power (beat 2): from below the interposer, up through each TSV into the die.
    tsv_xz = [(x, z) for x in (-9.0, -3.0, 3.0, 9.0) for z in (-9.0, 0.0, 9.0)]
    for idx, (x, z) in enumerate(tsv_xz):
        u0 = 0.1 + 0.04 * idx
        stream_of(root, f"power_{idx}", 1, (x, -1.2, z), [(0, 0, 0), (0, 4.2, 0)],
                  0.75, m["power"], 2, u0, u0, 30)

    labels = {
        0: [("silicon interposer: wires under the die", (-16.0, 1.7, 20.0), root),
            ("four HBM stacks", (18.5, 7.0, 9.0), root)],
        1: [("data across the interposer", (-16.0, 2.3, -9.0), root),
            ("into the die", (9.0, 4.0, 9.0), root)],
        2: [("power up through the TSVs", (3.0, 1.9, 0.0), root)],
        3: [("CoWoS-S: one silicon slab", (-24.0, 1.7, -22.0), root),
            ("up to ~3.3x reticle", (26.0, 1.7, -26.0), root)],
        4: [("CoWoS-L: bridges under the seam", (0.0, 2.4, -12.0), root),
            ("organic interposer", (-22.0, 1.6, 22.0), root)],
        5: [("grows to ~9.5 reticles", (45.0, 1.6, 45.0), root)],
        6: [("the package on its board", (45.0, 0.8, 0.0), root),
            ("the board under the package", (56.0, -8.0, 56.0), root)],
    }
    for i, items in labels.items():
        for text, at, parent in items:
            label(text, at, parent, beat(i))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
