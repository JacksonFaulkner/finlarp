"""HBF zoom-in b, CBA bonding, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_hbf_zoom_b.py

Writes blender/rnd_hbf_zoom_b.blend and assets/rnd_hbf_zoom_b.glb. One beat is 8 s.

One NAND die drawn large, cut open at z = 0: SanDisk's CBA (CMOS directly bonded to array) builds
the logic and the array on separate wafers and bonds them face to face.

Beats (match diagrams_nodes/hbf/zooms/b.rs):
  0 apart   the CMOS logic wafer below, the NAND array wafer above, face to face
  1 bond    the array comes down onto the logic; the bond line glows
  2 stack   the die drops onto its stack; logic blocks under every array block light up
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, empty, key, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import rnd_hbf_kit as K  # noqa: E402

PAGE = "rnd_hbf"
NAME = "zoom_b"
BEATS = 3

HALF = 400.0  # half the width of the die drawn here
DEPTH = 200.0  # the die's depth behind the cut face
CMOS_T, ARRAY_T = 40.0, 60.0
GAP = 180.0  # how far apart the wafers start
BLOCKS = 4  # array blocks across the die, each with its logic beneath
STRINGS = 6  # NAND strings per block on the cut face
DROP = 90.0  # how far the bonded die drops to land on the stack

POSES = [
    ((0.0, 130.0, 0.0), 1400.0, 0.30, 0.16),
    ((0.0, 70.0, 0.0), 1500.0, 0.30, 0.14),
    ((0.0, -170.0, 0.0), 1500.0, 0.30, 0.16),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def block_x(i):
    w = 2 * HALF / BLOCKS
    return -HALF + w * i + 16.0, -HALF + w * (i + 1) - 16.0


def die(root, m):
    """The die: CMOS layer, array layer (its own group, keyed), bond line and logic highlights."""
    d = empty("die", root)
    box("cmos", (-HALF, 0.0, -DEPTH), (HALF, CMOS_T, 0.0), m["cmos"], d)
    # logic circuits on the CMOS cut face, one patch under each array block
    for i in range(BLOCKS):
        x0, x1 = block_x(i)
        for j in range(3):
            cx = x0 + (x1 - x0) * (j + 0.5) / 3
            box(f"logic{i}_{j}", (cx - 22.0, 8.0, -2.0), (cx + 22.0, CMOS_T - 8.0, 1.5), m["ucie"], d)
    arr = empty("array", d)
    box("array_m", (-HALF, CMOS_T, -DEPTH), (HALF, CMOS_T + ARRAY_T, 0.0), m["array"], arr)
    for i in range(BLOCKS):
        x0, x1 = block_x(i)
        for s in range(STRINGS):
            sx = x0 + (x1 - x0) * (s + 0.5) / STRINGS
            box(f"str{i}_{s}", (sx - 5.0, CMOS_T + 6.0, -2.0), (sx + 5.0, CMOS_T + ARRAY_T - 6.0, 1.5), m["string"], arr)
    bond = empty("bond", d)
    box("bond_m", (-HALF - 6.0, CMOS_T - 2.0, -DEPTH - 6.0), (HALF + 6.0, CMOS_T + 2.0, 4.0), m["bond"], bond)
    lit = empty("lit", d)
    for i in range(BLOCKS):
        x0, x1 = block_x(i)
        box(f"lit{i}", (x0, 4.0, -1.0), (x1, 7.0, 3.0), m["page"], lit)
    return d, arr, bond, lit


def stack(root, m):
    """Three dies already on a base die, below where the bonded die lands."""
    g = empty("stack", root)
    box("st_base", (-HALF - 30.0, -480.0, -DEPTH - 30.0), (HALF + 30.0, -420.0, 0.0), m["base"], g)
    for k in range(3):
        y0 = -410.0 + k * 110.0
        box(f"st_cmos{k}", (-HALF, y0, -DEPTH), (HALF, y0 + CMOS_T, 0.0), m["cmos"], g)
        box(f"st_arr{k}", (-HALF, y0 + CMOS_T, -DEPTH), (HALF, y0 + CMOS_T + ARRAY_T, 0.0), m["array"], g)
    return g


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    d, arr, bond, lit = die(root, m)

    # beat 0: the array wafer hangs above the logic; beat 1: it comes down and bonds
    for f, y in [(F(0, 0.0), GAP), (F(1, 0.1), GAP), (F(1, 0.55), 0.0)]:
        key(arr, f, "location", P(0, y, 0))
    show(bond, span(1, 0.55, 2, 0.35))
    show(lit, span(2, 0.1, 3, 0.0))
    # beat 2: the bonded die drops onto the stack
    for f, y in [(F(2, 0.0), 0.0), (F(2, 0.25), 0.0), (F(2, 0.5), -DROP)]:
        key(d, f, "location", P(0, y, 0))
    show(stack(root, m), beat(2))

    tags = {
        0: [("CMOS logic wafer", (HALF, 20.0, 0.0)), ("NAND array wafer", (HALF, GAP + 70.0, 0.0)),
            ("built apart, face to face", (-HALF, GAP + 50.0, 0.0))],
    }
    late = {
        1: [("bonded: CMOS directly to array", (HALF - 60.0, CMOS_T, 0.0), 0.55),
            ("CBA: two wafers, one die", (-HALF + 60.0, CMOS_T + ARRAY_T, 0.0), 0.65)],
        2: [("logic under every array block", (-HALF + 100.0, 20.0 - DROP, 0.0), 0.5),
            ("the array keeps its area for bits", (HALF - 100.0, 90.0 - DROP, 0.0), 0.5),
            ("onto the stack, 16 dies high", (-HALF, -250.0, 0.0), 0.6)],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))
    for i, items in late.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
