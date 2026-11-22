"""The LOGIC DIE overview, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md). The compute die alone, then the reticle field, yield, HBM along the
edges, the chiplet split, data and power, and heat.

Run from the repo root (on the worker, not locally):

    blender -b --factory-startup --python tools/pbr3d/blender/logic_die_overview.py

It writes:
  blender/logic_die_overview.blend   open it in Blender to edit by hand
  assets/logic_die_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8.

Beats (match the LOGIC DIE overview in diagrams_pkg_nodes.rs, L_B):
  0 the logic die     one large purple die, alone
  1 reticle           a pink outline marks the 26 x 33 mm field over the die
  2 yield             the die glows under test; random defects land on it
  3 HBM               four HBM stacks beside the die on an interposer
  4 chiplets          the die splits in two, joined by a bridge; eight stacks
  5 data and power    cyan data in from the HBM, yellow power up from the board
  6 heat              the split dies glow hot; heat rises through the lid
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, ball, label, beat, show  # noqa: E402
from sand_zooms import start, camera, finish, stream_of  # noqa: E402
from pbr_kit import mat, empty  # noqa: E402
import pkg_kit as K  # noqa: E402

PAGE = "logic_die"
NAME = "overview"
BEATS = 7

# Poses: (target, distance, yaw, pitch) per beat, as in ingot_overview.py.
POSES = [
    ((0.0, 0.6, 0.0), 85.0, 0.50, 0.35),
    ((0.0, 0.8, 0.0), 95.0, 0.50, 0.35),
    ((0.0, 0.6, 0.0), 85.0, 0.40, 0.30),
    ((0.0, 2.0, 0.0), 105.0, 0.60, 0.40),
    ((0.0, 2.0, 0.0), 105.0, 0.50, 0.45),
    ((0.0, -2.0, 12.0), 120.0, 0.45, 0.55),
    ((0.0, 4.0, 0.0), 105.0, 0.50, 0.70),
]

# Die: 25.5 x 32 mm (about H100's 814 mm2), inside a 26 x 33 mm reticle field.
HALF_X, HALF_Z, DIE_TOP = 12.75, 16.0, 1.2
GAP = 1.2  # half-width of the bridge gap at the split


def solid(m, name, lo, hi, intervals, parent):
    """One box in its own group, switched on for `intervals`."""
    g = empty(name, parent)
    box(f"{name}_part", lo, hi, m, g)
    show(g, intervals)
    return g


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)

    die = mat("logic_die", (0.42, 0.30, 0.72), metal=0.2, rough=0.35)
    die_test = mat("logic_test", (0.36, 0.26, 0.78), emit=(0.55, 0.40, 1.0), strength=1.6)
    die_hot = mat("logic_hot", (0.90, 0.35, 0.15), emit=(1.0, 0.40, 0.10), strength=2.5)
    lid = mat("logic_lid", (0.80, 0.82, 0.86), metal=0.5, rough=0.25, alpha=0.5)
    reticle = mat("reticle_field", (1.0, 0.40, 0.70), emit=(1.0, 0.35, 0.65), strength=3.0)
    defect = mat("defect", (1.0, 0.10, 0.10), emit=(1.0, 0.05, 0.05), strength=4.0)
    interposer = mat("interposer_si", (0.30, 0.36, 0.40), metal=0.4, rough=0.5)
    hbm = K.hbm_materials()
    bridge = mat("bridge_link", (0.25, 0.85, 0.85), metal=0.3, rough=0.4)
    data = mat("data_cyan", (0.30, 0.90, 1.0), emit=(0.20, 0.90, 1.0), strength=10.0)
    power = mat("power_yellow", (1.0, 0.85, 0.20), emit=(1.0, 0.80, 0.20), strength=10.0)
    heat = mat("heat_wisp", (1.0, 0.50, 0.20), emit=(1.0, 0.45, 0.15), strength=4.0, alpha=0.8)

    # Beat intervals.
    solid_intervals = [(F(0, 0), F(2, 0)), (F(3, 0), F(4, 0))]  # purple die, beats 0-1 and 3
    test_intervals = [(F(2, 0), F(3, 0))]  # glowing die under test
    split_intervals = [(F(4, 0), F(6, 0))]  # chiplets, beats 4-5
    split_hot = [(F(6, 0), F(7, 0))]  # chiplets glowing, beat 6
    from_3 = [(F(3, 0), F(7, 0))]
    from_5 = [(F(5, 0), F(6, 0))]  # power rail and data, beat 5
    from_6 = [(F(6, 0), F(7, 0))]  # lid, beat 6
    from_4 = [(F(4, 0), F(7, 0))]

    # 0-3: one die.
    solid(die, "die_solid", (-HALF_X, 0.0, -HALF_Z), (HALF_X, DIE_TOP, HALF_Z), solid_intervals, root)
    solid(die_test, "die_test", (-HALF_X, 0.0, -HALF_Z), (HALF_X, DIE_TOP, HALF_Z), test_intervals, root)

    # 1: reticle field, four bars around the die at 26 x 33 mm.
    ret = empty("reticle", root)
    show(ret, [(F(1, 0), F(2, 0))])
    box("ret_left", (-13.3, DIE_TOP, -16.6), (-12.9, DIE_TOP + 0.3, 16.6), reticle, ret)
    box("ret_right", (12.9, DIE_TOP, -16.6), (13.3, DIE_TOP + 0.3, 16.6), reticle, ret)
    box("ret_front", (-13.3, DIE_TOP, 16.2), (13.3, DIE_TOP + 0.3, 16.6), reticle, ret)
    box("ret_back", (-13.3, DIE_TOP, -16.6), (13.3, DIE_TOP + 0.3, -16.2), reticle, ret)

    # 2: random defects on the die under test.
    dfx = empty("defects", root)
    show(dfx, test_intervals)
    for i, (x, z) in enumerate([(-6.0, -9.0), (3.0, -3.0), (7.0, 8.0), (-2.0, 11.0), (-9.0, 2.0)]):
        ball(f"defect_{i}", (x, DIE_TOP + 0.1, z), 1.0, defect, dfx, 12)

    # 3-4: interposer and HBM stacks on its edges. Four stacks from beat 3, eight from beat 4.
    ip = empty("interposer", root)
    show(ip, from_3)
    box("interposer_plate", (-45.0, -2.0, -40.0), (45.0, 0.0, 40.0), interposer, ip)
    # The stack under the interposer, from beat 3 with it: substrate (its top meets the
    # interposer's underside at y = -2), BGA balls, and the green board the power rail rises from.
    mk = K.materials()
    sub = empty("substrate_grp", root)
    show(sub, from_3)
    K.substrate(mk, sub, half=50.0)
    bd = empty("board_grp", root)
    show(bd, from_3)
    # Wider than the kit's 120 mm board: this substrate is 100 mm, so the kit board showed only a rim.
    box("board", (-80.0, -14.0, -80.0), (80.0, K.BOARD_TOP, 80.0), mk["board"], bd)
    K.bga(mk, bd, half=20.0)

    for side in (-1, 1):
        inner, outer = side * 14.5, side * 22.25
        x0, x1 = min(inner, outer), max(inner, outer)
        for zc, intervals in ((-9.0, from_3), (9.0, from_3), (-21.0, from_4), (21.0, from_4)):
            g = empty(f"hbm_{side}_{zc}", root)
            show(g, intervals)
            K.hbm_stack(f"hbm_{side}_{zc}_stack", (x0, 0.0, zc - 4.0), (x1, 5.0, zc + 4.0), hbm, g)

    # 4-6: the die splits in two, joined by a bridge.
    split_parts = [
        ((-HALF_X, 0.0, -HALF_Z), (-GAP, DIE_TOP, HALF_Z)),
        ((GAP, 0.0, -HALF_Z), (HALF_X, DIE_TOP, HALF_Z)),
    ]
    for i, (lo, hi) in enumerate(split_parts):
        solid(die, f"split_{i}", lo, hi, split_intervals, root)
        solid(die_hot, f"split_hot_{i}", lo, hi, split_hot, root)
    solid(bridge, "bridge", (-GAP, 0.0, -10.0), (GAP, 0.6, 10.0), from_4, root)

    # 5: data in from the HBM. Power comes up from the board on a rail outside the interposer
    # edge (the plate would hide it underneath), then runs along the top into the die's front edge.
    rail = empty("power_rail", root)
    show(rail, from_5)
    box("power_rail_part", (-0.9, -14.0, 40.5), (0.9, 0.0, 42.0), power, rail)
    stream_of(root, "data_left", 4, (-22.0, 2.5, 9.0), [(0, 0, 0), (9, 0, -9)], 1.1, data, 5, 0.1, 0.7, 40)
    stream_of(root, "data_right", 4, (22.0, 2.5, -9.0), [(0, 0, 0), (-9, 0, 9)], 1.1, data, 5, 0.1, 0.7, 40)
    stream_of(root, "power", 5, (0.0, -14.0, 41.0), [(0, 0, 0), (0, 14.5, 0), (0, 14.5, -23.5)], 1.3, power, 5, 0.1, 0.7, 40)

    # 6: a lid over the dies (translucent, so the glow shows through); heat rises off its top.
    lid_g = empty("lid_grp", root)
    show(lid_g, from_6)
    box("lid", (-HALF_X - 0.4, DIE_TOP, -HALF_Z - 0.4), (HALF_X + 0.4, DIE_TOP + 1.4, HALF_Z + 0.4), lid, lid_g)
    for k, (x, z) in enumerate([(-7.0, -8.0), (7.0, 8.0), (0.0, 0.0)]):
        stream_of(root, f"heat{k}", 4, (x, DIE_TOP + 1.4, z), [(0, 0, 0), (0, 12, 0)], 2.0, heat, 6, 0.1, 0.7, 40)

    # Tags: 2 per beat, shown only during their beat.
    tags = {
        0: [("logic die", (-10.0, DIE_TOP + 0.1, -12.0)), ("N4/N3-class node", (9.0, DIE_TOP + 0.1, 11.0))],
        1: [("26 x 33 mm field", (13.3, DIE_TOP + 0.3, 0.0)), ("858 mm2 limit", (-13.3, DIE_TOP + 0.3, -16.6))],
        2: [("one defect = one die", (-6.0, DIE_TOP + 0.1, -9.0)), ("~45% yield at 800 mm2", (9.0, DIE_TOP + 0.1, 9.0))],
        3: [("HBM along the edges", (-18.5, 5.0, 9.0)), ("edge length sets the count", (18.5, 5.0, -9.0))],
        4: [("two dies", (-7.0, DIE_TOP + 0.1, 14.0)), ("bridge ~10 TB/s", (0.0, 0.6, -12.0))],
        5: [("data ~8 TB/s", (-17.0, 3.0, 4.0)), ("power up from the board", (2.0, -7.0, 42.0))],
        6: [("heat leaves the top", (2.0, 14.5, 2.0)), ("cooling on BOARD", (-7.0, 5.5, 9.0))],
    }
    for i, items in tags.items():
        for text, at in items:
            label(text, at, root, beat(i))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
