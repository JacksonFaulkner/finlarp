"""The BANK overview, authored in Blender and exported for pbr3d in the MELT template
(docs/diagram-pages.md): one DRAM die, face-on, with its bank groups, command bus, data lane and
I/O pad. The die's pieces are in bank_kit.py, shared with the zooms and sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/bank_overview.py

It writes:
  blender/bank_overview.blend   open it in Blender to edit by hand
  assets/bank_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/bank/overview.rs).

Beats (match the BANK overview page):
  0 many banks   the die: four bank groups, one command bus, one data bus to the I/O pad
  1 ACT A        a command opens a row in bank A; its row buffer stands up
  2 ACT B        bank B, in another group, opens while A is still open
  3 READ         bursts from A and B alternate onto the data bus, one burst at a time
  4 window       C and D open too: four ACTIVATEs in one tFAW window, a fifth (E) waits
  5 conflict     A needs another row: it precharges (pink) while B keeps reading
  6 refresh      all-bank REFRESH: every bank closes, then all sixteen turn cyan
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import bank_kit as K  # noqa: E402
from bank_kit import END, IO_X, CMD_Y  # noqa: E402

BEATS = 7

# (camera target, distance, yaw, pitch), one per beat
POSES = [
    ((160.0, 100.0, 0.0), 6100.0, 0.12, 0.16),
    ((-700.0, 330.0, 0.0), 3300.0, 0.10, 0.12),
    ((700.0, 330.0, 0.0), 3300.0, -0.06, 0.12),
    ((320.0, 120.0, 0.0), 4700.0, 0.0, 0.10),
    ((-100.0, -100.0, 0.0), 5000.0, 0.10, 0.14),
    ((0.0, 220.0, 0.0), 4000.0, 0.04, 0.12),
    ((160.0, 100.0, 0.0), 6100.0, 0.10, 0.16),
]


def build():
    m, root = start("overview", BEATS, page="bank")
    K.mats(m)
    d = K.die(root, m)
    g = d["banks"]
    A, B, C, D, E = g[0][0], g[1][0], g[2][0], g[3][0], g[0][3]

    # beat 0: the die and its three named parts
    K.tag(root, "16 banks in 4 bank groups", (-1080.0, 620.0, 40.0), beat(0))
    K.tag(root, "command bus", (0.0, CMD_Y + 70.0, 40.0), beat(0))
    K.tag(root, "data bus: one burst at a time", (420.0, 70.0, 40.0), beat(0))
    K.tag(root, "I/O: the chip's data pins", (IO_X + 60.0, -230.0, 40.0), beat(0))

    # beat 1: ACTIVATE bank A
    K.activate(root, A, F(1, 0.05), F(1, 0.40), m)
    K.set_state(A, "row", [(F(1, 0.40), F(5, 0.10)), (F(5, 0.60), F(6, 0.25))])
    K.tag(root, "ACTIVATE bank A: row opens", K.above(A), beat(1))

    # beat 2: ACTIVATE bank B while A is still open
    K.activate(root, B, F(2, 0.05), F(2, 0.40), m)
    K.set_state(B, "row", [(F(2, 0.40), F(6, 0.25))])
    K.tag(root, "bank B: another group, same time", K.above(B), beat(2))

    # beat 3: READs alternate between A and B
    for k in range(6):
        bk = A if k % 2 == 0 else B
        u0 = 0.10 + 0.12 * k
        K.send(root, "rd_alt", K.data_path(bk), F(3, u0), F(3, u0 + 0.11), m["data_dot"])
    K.tag(root, "READs alternate: groups overlap", (-420.0, 90.0, 40.0), beat(3))

    # beat 4: C and D open; the fifth bank, E, waits for the window
    K.activate(root, C, F(4, 0.05), F(4, 0.30), m)
    K.activate(root, D, F(4, 0.15), F(4, 0.40), m)
    K.set_state(C, "row", [(F(4, 0.30), F(6, 0.25))])
    K.set_state(D, "row", [(F(4, 0.40), F(6, 0.25))])
    K.set_state(E, "pink", [(F(4, 0.25), F(4, 0.90))])
    K.tag(root, "fifth ACT waits: tFAW", K.above(E), beat(4))

    # beat 5: a row conflict in A; B keeps reading
    K.set_state(A, "pink", [(F(5, 0.05), F(5, 0.60))])
    K.reads(root, B, F(5, 0.10), F(5, 0.95), 4, m)
    K.tag(root, "bank A: row conflict", K.above(A), beat(5))
    K.tag(root, "bank B keeps reading", K.above(B), beat(5))

    # beat 6: all-bank refresh; every bank turns cyan together
    for bk in d["all"]:
        K.set_state(bk, "cyan", [(F(6, 0.30), END)])
    K.tag(root, "REFRESH: all banks at once", (0.0, 640.0, 40.0), beat(6))

    K.commit(d)
    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="bank")
