"""The MICROBUMP overview, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md). A finished package on its board, pulled apart to show its bumps at every
level, the microbumps under the die, the C4 bumps under the interposer, power climbing through the
joints, underfill filling the gap, and hybrid bonds that leave no bumps at all.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/microbump_overview.py

It writes:
  blender/microbump_overview.blend   open it in Blender to edit by hand
  assets/microbump_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8.
Stylised: the scene is in mm but the bumps are drawn larger than life. Pitch ratios are kept:
microbump pitch 2.0, C4 pitch 7.5 (the real 40 um and 150 um are 1:3.75, here 1:3.75).

Beats (match the MICROBUMP overview in diagrams_pkg_nodes.rs, U_B):
  0 finished package   a die on an interposer on a substrate, on its board
  1 pulled apart       the levels lift apart; bumps at every level
  2 microbumps         the die drops onto the 7x7 microbump grid; camera on the joint
  3 C4 bumps           the substrate closes onto the C4 balls under the interposer
  4 power climbs       the levels part a little; yellow power climbs up the joints
  5 underfill          dark underfill fills the gap round the die
  6 hybrid bonds       the bumps vanish; the die sits flat on the interposer over a copper pad
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, tube, box, label, beat, show, key  # noqa: E402
from sand_zooms import start, camera, finish, stream_of  # noqa: E402
from pbr_kit import mat, empty  # noqa: E402

PAGE = "microbump"
NAME = "overview"
BEATS = 7

# Poses: (target, distance, yaw, pitch) per beat.
POSES = [
    ((0.0, -3.0, 0.0), 95.0, 0.60, 0.30),
    ((0.0, -6.0, 0.0), 135.0, 0.60, 0.07),
    ((0.0, 2.6, 0.0), 60.0, 0.60, 0.26),
    ((0.0, -1.5, 0.0), 65.0, 0.50, 0.02),
    ((0.0, 0.0, 0.0), 80.0, 0.90, 0.05),
    ((0.0, 3.0, 0.0), 55.0, 0.70, 0.45),
    ((0.0, 3.0, 0.0), 55.0, 0.30, 0.50),
]

# Levels (Y up). The assembled stack, bottom to top: board, BGA balls, substrate, C4 balls,
# interposer, microbumps, die. Each slot is the gap the joints span when the levels are closed.
BOARD_TOP, BOARD_BOT = -9.0, -15.0
BGA_Y, BGA_R = -8.0, 1.0  # spans -9..-7: the slot between board and substrate
SUB_TOP, SUB_BOT = -3.0, -7.0
C4_Y, C4_R = -1.5, 1.5  # spans -3..0: the slot between substrate and interposer
IP_BOT, IP_TOP = 0.0, 1.6
UB_TOP, DIE_TOP = 3.2, 4.6  # microbump slot 1.6 tall; the die is 1.4 thick
UB_PITCH, C4_PITCH, BGA_PITCH = 2.0, 7.5, 5.0
UB_R, UB_CAP_R = 0.45, 0.6  # copper pillar, solder cap
DIE_HALF = 7.0
UF_OUT = 1.4  # underfill fillet beyond the die edge
PAD_T = 0.2  # hybrid copper pad on the interposer

# Vertical offsets (mm) per beat for the die group and the substrate group: each (beat, dy) ramps
# to dy over the first half of its beat and holds until the next step.
DIE_STEPS = [(0, 0.0), (1, 8.0), (2, 0.0), (4, 2.5), (5, 0.0), (6, -1.4)]
SUB_STEPS = [(0, 0.0), (1, -6.0), (3, 0.0), (4, -2.5), (5, 0.0)]
# The board follows the substrate but drops a further 6 mm in beat 1 so the BGA slot opens too.
BOARD_STEPS = [(0, 0.0), (1, -12.0), (3, 0.0), (4, -2.5), (5, 0.0)]


def levels(grp, steps):
    """Keys `grp`'s vertical offset through `steps` (see above)."""
    prev = None
    for b, dy in steps:
        if prev is None:
            key(grp, F(b, 0), "location", P(0.0, dy, 0.0))
        else:
            key(grp, F(b, 0), "location", P(0.0, prev, 0.0))
            key(grp, F(b, 0.5), "location", P(0.0, dy, 0.0))
        prev = dy


def grid(half, pitch):
    n = int(round(half / pitch))
    return [(pitch * i, pitch * j) for i in range(-n, n + 1) for j in range(-n, n + 1)]


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)

    board = mat("pkg_board", (0.10, 0.34, 0.20), rough=0.7)
    substrate = mat("substrate_abf", (0.42, 0.27, 0.15), rough=0.8)
    silicon = mat("interposer_si", (0.30, 0.36, 0.40), metal=0.4, rough=0.5)
    die = mat("die_purple", (0.42, 0.30, 0.72), metal=0.2, rough=0.35)
    solder = mat("c4_solder", (0.85, 0.82, 0.75), metal=0.8, rough=0.35)
    copper = mat("cu_pillar", (0.85, 0.55, 0.35), metal=0.9, rough=0.3)
    underfill = mat("underfill_dark", (0.10, 0.09, 0.09), rough=0.9)
    power = mat("power_yellow", (1.0, 0.85, 0.20), emit=(1.0, 0.80, 0.20), strength=10.0)

    sub_grp = empty("substrate_grp", root)
    ip_grp = empty("interposer_grp", root)
    die_grp = empty("die_grp", root)
    levels(die_grp, DIE_STEPS)
    levels(sub_grp, SUB_STEPS)
    board_grp = empty("board_grp", root)
    levels(board_grp, BOARD_STEPS)

    # Board and BGA balls (board_grp) follow the substrate (sub_grp); the C4 balls hang from the
    # interposer (ip_grp); the interposer stays put.
    # Beat 4 swaps board, substrate and interposer for see-through copies so the power column shows.
    solid_iv = [(F(0, 0), F(4, 0)), (F(5, 0), F(7, 0))]
    see_iv = [(F(4, 0), F(5, 0))]

    def slab(name, lo, hi, m_solid, m_see, parent):
        a = empty(f"{name}_solid", parent)
        show(a, solid_iv)
        box(name, lo, hi, m_solid, a)
        b = empty(f"{name}_see", parent)
        show(b, see_iv)
        box(f"{name}_glass", lo, hi, m_see, b)

    board_see = mat("pkg_board_glass", (0.10, 0.34, 0.20), rough=0.3, alpha=0.2)
    substrate_see = mat("substrate_abf_glass", (0.42, 0.27, 0.15), rough=0.3, alpha=0.2)
    silicon_see = mat("interposer_si_glass", (0.30, 0.36, 0.40), rough=0.3, alpha=0.2)
    slab("board", (-40.0, BOARD_BOT, -40.0), (40.0, BOARD_TOP, 40.0), board, board_see, board_grp)
    bga = empty("bga_balls", board_grp)
    for i, (x, z) in enumerate(grid(20.0, BGA_PITCH)):
        ball(f"bga_{i}", (x, BGA_Y, z), BGA_R, solder, bga, 12)
    slab("substrate", (-30.0, SUB_BOT, -30.0), (30.0, SUB_TOP, 30.0), substrate, substrate_see, sub_grp)
    slab("interposer", (-26.0, IP_BOT, -26.0), (26.0, IP_TOP, 26.0), silicon, silicon_see, ip_grp)
    c4 = empty("c4_bumps", ip_grp)
    for i, (x, z) in enumerate(grid(22.5, C4_PITCH)):
        ball(f"c4_{i}", (x, C4_Y, z), C4_R, solder, c4, 12)

    # Hybrid copper pad on the interposer, shown only in beat 6 (the bonds there are copper to copper).
    pad = empty("hybrid_pad", ip_grp)
    show(pad, [(F(6, 0), F(7, 0))])
    box("pad", (-DIE_HALF - 0.2, IP_TOP, -DIE_HALF - 0.2), (DIE_HALF + 0.2, IP_TOP + PAD_T, DIE_HALF + 0.2), copper, pad)

    # Die with its microbump grid: a 7x7 array of copper pillars with solder caps. The grid is
    # hidden from beat 6, when the bonds are hybrid. Underfill fills the gap in beat 5 only.
    ub = empty("microbumps", die_grp)
    show(ub, [(F(0, 0), F(6, 0))])
    for i, (x, z) in enumerate(grid(6.0, UB_PITCH)):
        tube(f"ub_{i}", (x, 2.2, z), (x, UB_TOP, z), UB_R, copper, ub, 12)
        ball(f"ubcap_{i}", (x, 1.9, z), UB_CAP_R, solder, ub, 12)
    box("die", (-DIE_HALF, UB_TOP, -DIE_HALF), (DIE_HALF, DIE_TOP, DIE_HALF), die, die_grp)
    fill = empty("underfill", die_grp)
    show(fill, [(F(5, 0), F(6, 0))])
    e = DIE_HALF + UF_OUT
    box("underfill_fill", (-e, IP_TOP, -e), (e, UB_TOP, e), underfill, fill)

    # Power: yellow climbs straight up a column on the camera side, under the die's corner, through
    # the BGA slot, the C4 slot, the interposer's TSVs and the microbump slot, into the die.
    stream_of(
        root,
        "power",
        6,
        (5.0, -12.0, 5.0),
        [(0.0, 0.0, 0.0), (0.0, 20.0, 0.0)],
        1.2,
        power,
        4,
        0.1,
        0.85,
        56,
    )

    # Tags: two per beat, pinned to their parts (parented so they move with the part).
    label("finished package: die on interposer", (-6.0, 5.0, 0.0), die_grp, beat(0))
    label("substrate", (20.0, -5.0, 22.0), sub_grp, beat(0))
    label("bumps at every level", (-6.0, 5.0, -4.0), die_grp, beat(1))
    label("BGA balls below", (20.0, BGA_Y, 20.0), board_grp, beat(1))
    label("microbumps ~40 um", (4.0, 2.4, 8.5), die_grp, beat(2))
    label("20-25 um bumps", (-8.5, 2.4, -2.0), die_grp, beat(2))
    label("C4 ~150 um", (14.0, C4_Y, 14.0), ip_grp, beat(3))
    label("interposer to substrate", (-14.0, C4_Y, -14.0), ip_grp, beat(3))
    label("power climbs the joints", (10.0, -4.0, -10.0), root, beat(4))
    label("every amp passes the bumps", (-9.0, 3.0, 9.0), die_grp, beat(4))
    label("underfill shares stress", (-3.0, 2.4, e), die_grp, beat(5))
    label(">10x C4 thermal-cycle life", (e, 2.4, -4.0), die_grp, beat(5))
    label("hybrid bond <= 10 um", (5.0, 5.0, 5.0), die_grp, beat(6))
    label("no bumps: copper to copper", (-5.0, 5.0, -5.0), die_grp, beat(6))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
