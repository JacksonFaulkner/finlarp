"""R&D 3D DRAM zoom-in a, "the vertical transistor cut open", in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_zoom_a.py

Writes blender/rnd_3d_dram_zoom_a.blend and assets/rnd_3d_dram_zoom_a.glb. One beat is 8 s.

Three 4F2 VCT cells (rnd_3d_dram_kit.vct_cell) on one buried bit line, cut open at z = 0; the
middle one is the subject. Each cell sits on its own word line (word lines run along z), so one
word line picks one cell on the shared bit line.

Beats (match diagrams_nodes/dram3d/zooms/a.rs):
  0 cell      the whole cell: buried bit line, pillar, wrapped word line, capacitor on top, 2F x 2F tile
  1 pillar    close on the pillar: n+ / p body / n+, gate oxide; the word line lights, the channel forms
  2 read      charge runs from the capacitor down the pillar into the bit line, which lights
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, label  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "zoom_a"
BEATS = 3
P = K.V_PITCH  # neighbour cells along the bit line

POSES = [
    ((0.0, 1000.0, 0.0), 4300.0, 0.42, 0.17),
    ((0.0, 420.0, 0.0), 1350.0, 0.30, 0.10),
    ((-150.0, 850.0, 0.0), 4100.0, 0.36, 0.13),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)

    c = K.vct_cell(root, m, (0.0, 0.0, 0.0), "vc", holes=0)
    nb = [K.vct_cell(root, m, (s * P, 0.0, 0.0), f"vn{i}", tile=False, holes=0) for i, s in enumerate((-1, 1))]

    # charge: stored through beats 0-1, drains into the bit line in beat 2
    on(c.charge, span(0, 0.0, 2, 0.75))
    q = bpy.data.objects["vc_cap_q"]
    scale_keys(q, [(F(2, 0.25), 1.0), (F(2, 0.62), (1.0, 1.0, 0.3))])
    for n in nb:
        on(n.charge, span(0, 0.0, 3, 0.0))
    on(c.tile, beat(0))

    # beat 1: the word line comes on, the channel forms on the pillar faces
    on(c.wl_on, span(1, 0.4, 3, 0.0))
    on(c.chan_on, span(1, 0.55, 3, 0.0))
    # beat 2: charge runs down to the bit line, which lights along the whole row
    for h in [c] + nb:
        on(h.bl_on, span(2, 0.42, 3, 0.0))
    path = c.read_path[:3] + [(-P - 150.0, K.V_BL[1] - 20.0, 12.0)]
    K.beads(root, m, "read", path, 5, 2, 0.22, 0.6, life=55)

    pp = c.pts
    xr = P + K.FS + 40.0  # right edge of the row
    tags = {
        0: [("capacitor on top", (K.V_CAP_R, 1450.0, 0.0), 0.05),
            ("word line wraps the pillar", (K.V_WL, 400.0, 0.0), 0.2),
            ("buried bit line", (xr, 55.0, 0.0), 0.35),
            ("4F2 cell: 2F x 2F", pp["tile"], 0.5)],
        1: [("n+ under the capacitor", pp["source"], 0.05), ("p-type pillar body", pp["pillar"], 0.12),
            ("n+ on the bit line", pp["drain"], 0.19), ("gate oxide", (-K.V_OX, 520.0, 0.0), 0.26),
            ("word line on", (-K.V_WL, 300.0, 0.0), 0.42), ("channel forms on the pillar faces", (K.V_PW, 300.0, 6.0), 0.58)],
        2: [("charge leaves the capacitor", (0.0, 1250.0, 12.0), 0.2),
            ("down the pillar", (0.0, 450.0, 12.0), 0.35),
            ("bit line carries it to the sense amp", (-P - 100.0, 55.0, 0.0), 0.5)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
