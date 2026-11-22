"""R&D 3D DRAM zoom-in b, "periphery bonded under the array", in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_zoom_b.py

Writes blender/rnd_3d_dram_zoom_b.blend and assets/rnd_3d_dram_zoom_b.glb. One beat is 8 s.

Two subjects, the camera cuts between them at beat boundaries:
  left   two wafers (rnd_3d_dram_kit.wafer): the cell wafer turns face down onto the periphery wafer
  right  one cell-on-periphery die (bonded_die), cut open at z = 0

Beats (match diagrams_nodes/dram3d/zooms/b.rs):
  0 wafers    the cell wafer flips over and comes down onto the periphery wafer; the seam glows
  1 pads      close on the bond face: copper pads in oxide meet pad to pad, the bond line lights
  2 signal    whole die: a cell's charge runs down its bit line, through a via and the bond into the sense amps
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, disc, empty, key, label, P as BP  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "zoom_b"
BEATS = 3

WX = -7000.0  # the wafers
PERI_Y = 500.0  # periphery wafer centre
CELL_Y0 = 1500.0  # cell wafer starts here, face up
CELL_Y1 = PERI_Y + 40.0  # and lands here, face down
LIFT = 520.0  # the die's array hangs this far up at the start of beat 1

POSES = [
    ((WX, 820.0, -150.0), 3900.0, 0.25, 0.30),
    ((-250.0, 230.0, 0.0), 1500.0, 0.28, 0.10),
    ((0.0, 560.0, -300.0), 6300.0, 0.35, 0.15),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)

    # ---- beat 0: wafer to wafer ----
    K.wafer(root, m, (WX, PERI_Y, 0.0), kind="peri", name="wp")
    pv = empty("cell_pivot", root, BP(WX, CELL_Y0, 0.0))
    K.wafer(pv, m, (0.0, 0.0, 0.0), kind="cell", name="wc")
    pv.rotation_mode = "XYZ"
    for f, ang, y in [(0, 0.0, CELL_Y0), (F(0, 0.15), 0.0, CELL_Y0), (F(0, 0.45), math.pi, CELL_Y0),
                      (F(0, 0.5), math.pi, CELL_Y0), (F(0, 0.8), math.pi, CELL_Y1)]:
        key(pv, f, "rotation_euler", (ang, 0.0, 0.0))
        key(pv, f, "location", BP(WX, y, 0.0))
    seam = K.hidden("seam", root)
    disc("seam_d", (WX, PERI_Y + 20.0, 0.0), 915.0, 10.0, m["bond"], seam, verts=64)
    on(seam, span(0, 0.8, 1, 0.0))

    # ---- beats 1-2: one die, cut open ----
    bd = K.bonded_die(root, m, (0.0, 0.0, 0.0), nx=4, nz=3, name="bd")
    arr, pe = bd.arr, bd.peri
    K.lift(bd.top, [(0, LIFT), (F(1, 0.12), LIFT), (F(1, 0.55), 0.0)])
    on(bd.line, span(1, 0.55, 3, 0.0))
    for i in range(4):
        on(arr.cells[(i, 0)].charge, span(1, 0.0, 3, 0.0))
    on(arr.wl_on[1], span(2, 0.15, 2, 0.6))
    on(arr.bl_on[0], span(2, 0.25, 2, 0.75))
    for o in pe.sa_on:
        on(o, span(2, 0.55, 3, 0.0))
    x = arr.xs[1]
    ay = K.V_BASE
    y_dev = -K.PE_BOND - K.PE_ILD
    path = [(x, ay + K.V_CAP0 + 450.0, 14.0), (x, ay + K.V_BL[1] - 20.0, 14.0), (x - 100.0, ay + K.V_BL[1] - 20.0, 14.0),
            (x - 100.0, 0.0, 14.0), (x - 100.0, y_dev + 60.0, 14.0), (x - 100.0, y_dev - 80.0, 14.0)]
    K.beads(root, m, "sig", path, 4, 2, 0.18, 0.5, life=60, size=26.0)

    xp = x - 100.0
    tags = {
        0: [("cell wafer: 4F2 arrays", (WX - 700.0, CELL_Y0 + 30.0, 0.0), 0.05, 0.5),
            ("periphery wafer: logic process", (WX + 650.0, PERI_Y - 20.0, 650.0), 0.1, 1.0),
            ("turned face down", (WX + 900.0, CELL_Y0, 0.0), 0.3, 0.6),
            ("wafer-to-wafer hybrid bond", (WX - 900.0, PERI_Y + 30.0, 0.0), 0.82, 1.0)],
        1: [("Cu pad, array side", (xp - 50.0, 40.0, 0.0), 0.58, 1.0),
            ("Cu pad, periphery side", (xp - 50.0, -35.0, 0.0), 0.1, 1.0),
            ("oxide meets oxide", (x + 200.0, -25.0, 0.0), 0.3, 1.0),
            ("bonded: copper to copper", (arr.xs[0] + 100.0, 0.0, 0.0), 0.6, 1.0)],
        2: [("cell array", (arr.x1, 700.0, 0.0), 0.05, 1.0), ("bond", bd.pts["bond"], 0.1, 1.0),
            ("sense amps right under the cells", pe.pts["sa"], 0.55, 1.0),
            ("decoders", (pe.blocks[0][1] + 60.0, y_dev - 80.0, 0.0), 0.65, 1.0)],
    }
    for i, items in tags.items():
        for text, pos, u0, u1 in items:
            label(text, pos, root, span(i, u0, i, u1) if u1 < 1.0 else span(i, u0, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
