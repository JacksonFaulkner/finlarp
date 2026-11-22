"""R&D 3D DRAM zoom-in d, "6F2 against 4F2", in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_zoom_d.py

Writes blender/rnd_3d_dram_zoom_d.blend and assets/rnd_3d_dram_zoom_d.glb. One beat is 8 s.

Three subjects, the camera cuts between them at beat boundaries:
  cells   a planar 6F2 cell and a 4F2 VCT cell side by side, each with its F-grid tile overhead
  area    the same 6F x 6F patch tiled both ways: 6 planar cells against 9 VCT cells
  wafers  two wafers, the right one's dies smaller (drawn about 29% more; Samsung says >20%)

Beats (match diagrams_nodes/dram3d/zooms/d.rs):
  0 cells    the two cells and their tiles: 2F x 3F against 2F x 2F
  1 area     cells fill a 6F x 6F patch one by one: 6 against 9, about 50% more
  2 wafers   more dies per wafer
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, disc, label  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "zoom_d"
BEATS = 3
FS = K.FS

XP, XV = -650.0, 650.0  # beat 0 cells
PL_CAP = 1200.0
TILE_Y = K.PL_CAP0 + PL_CAP + 160.0  # both tiles at the same height
V_CAP = TILE_Y - 160.0 - K.V_CAP0
AX = 7000.0  # beat 1 patches centre
AL, AR = AX - 800.0, AX + 800.0
WX = 14000.0  # beat 2 wafers centre

POSES = [
    ((0.0, 700.0, -100.0), 5300.0, 0.30, 0.55),
    ((AX, 0.0, 60.0), 5000.0, 0.0, 0.95),
    ((WX, -200.0, 0.0), 6500.0, 0.0, 0.80),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)

    # ---- beat 0: one cell of each ----
    pc = K.planar_cell(root, m, (XP, 0.0, 0.0), "pc", cap_h=PL_CAP)
    vc = K.vct_cell(root, m, (XV, 0.0, 0.0), "vc", cap_h=V_CAP, holes=0)
    for h in (pc, vc):
        on(h.charge, span(0, 0.0, 1, 0.0))
        on(h.tile, span(0, 0.0, 1, 0.0))

    # ---- beat 1: a 6F x 6F patch tiled both ways ----
    K.footprint(root, m, (AL, 0, 0), 6, 6, 0.0, name="patchL", edge="tile_edge")
    K.footprint(root, m, (AR, 0, 0), 6, 6, 0.0, name="patchR", edge="tile_edge2")
    k = 0
    for a in range(2):  # 6F2: 3F along x, 2F along z
        for b in range(3):
            cx, cz = AL - 600 + 300 + a * 600, -600 + 200 + b * 400
            g = K.footprint(root, m, (cx, 0, cz), 3, 2, 22.0, name=f"t6_{k}", edge="tile_edge")
            disc(f"c6_{k}", (cx, 70.0, cz), 120.0, 90.0, m["diel"], g, verts=20)
            on(g, span(1, 0.08 + 0.07 * k, 2, 0.0))
            k += 1
    k = 0
    for a in range(3):
        for b in range(3):
            cx, cz = AR - 600 + 200 + a * 400, -600 + 200 + b * 400
            g = K.footprint(root, m, (cx, 0, cz), 2, 2, 22.0, name=f"t4_{k}", edge="tile_edge2")
            disc(f"c4_{k}", (cx, 70.0, cz), 120.0, 90.0, m["diel"], g, verts=20)
            on(g, span(1, 0.08 + 0.047 * k, 2, 0.0))
            k += 1

    # ---- beat 2: dies per wafer ----
    K.wafer(root, m, (WX - 1050.0, 0.0, 0.0), r=900.0, die=170.0, kind="cell", name="w6")
    K.wafer(root, m, (WX + 1050.0, 0.0, 0.0), r=900.0, die=150.0, kind="cell", name="w4")

    tags = {
        0: [("planar: 6F2 = 2F x 3F", pc.pts["tile"], 0.05), ("vertical: 4F2 = 2F x 2F", vc.pts["tile"], 0.2),
            ("transistor lies flat beside the capacitor", (XP - 300.0, -300.0, 0.0), 0.4),
            ("transistor under the capacitor", (XV + K.V_WL, 400.0, 0.0), 0.55)],
        1: [("same 6F x 6F patch", (AL - 600.0, 30.0, 600.0), 0.05),
            ("6 cells of 6F2", (AL, 30.0, -620.0), 0.55),
            ("9 cells of 4F2: 50% more", (AR, 30.0, -620.0), 0.6)],
        2: [("6F2 dies", (WX - 1050.0, 30.0, -900.0), 0.05),
            ("4F2 + periphery under: smaller die", (WX + 1050.0, 30.0, -900.0), 0.2),
            (">20% more dies per wafer (Samsung)", (WX + 1050.0, 30.0, 900.0), 0.45)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
