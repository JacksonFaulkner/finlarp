"""R&D 3D DRAM zoom-in c, "the stacked layers cut open", in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_zoom_c.py

Writes blender/rnd_3d_dram_zoom_c.blend and assets/rnd_3d_dram_zoom_c.glb. One beat is 8 s.

An eight-layer stacked 3D DRAM block (rnd_3d_dram_kit.stacked_3d, staircase on), cut open at z = 0.

Beats (match diagrams_nodes/dram3d/zooms/c.rs):
  0 layer     close on the top layer: bit line, drain, body under a gate-all-around word line,
              source, a capacitor lying on its side
  1 read      the layers pull apart and settle; one layer's word line lights and its charge runs
              into the vertical bit line and down
  2 stair     from behind: every layer's word line runs out to its own step with a contact
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, label, tube  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "zoom_c"
BEATS = 3
N = 8
TOPK = N - 1
RK = 4  # the layer read in beat 1 and lit on the stair in beat 2
STEP = 90.0
LP = K.S_LP
CM = (K.S_CH[0] + K.S_CH[1]) / 2

POSES = [
    ((480.0, TOPK * LP + 150.0, 0.0), 1750.0, 0.20, 0.08),
    ((0.0, 1350.0, -300.0), 7400.0, 0.30, 0.15),
    ((0.0, 1250.0, -1500.0), 6600.0, 2.55, 0.32),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    o = (0.0, 0.0, 0.0)
    s = K.stacked_3d(root, m, o, n=N, nz=3, name="sk", stair=True)
    zb = s.pts["back"]

    for k in range(N):
        for ch in s.charges[k]:
            on(ch, span(0, 0.0, 3, 0.0))

    # beat 0: the top layer's word line lights at the end
    on(s.wl_on[TOPK], span(0, 0.62, 1, 0.0))

    # beat 1: pull apart, settle, then read layer RK into the bit line
    K.lift_layers(s, [(F(1, 0.04), 0.0), (F(1, 0.22), 1.0), (F(1, 0.42), 1.0), (F(1, 0.56), 0.0)], STEP)
    on(s.wl_on[RK], span(1, 0.6, 1, 1.0) + span(2, 0.25, 3, 0.0))
    on(s.bl_on[0], span(1, 0.68, 2, 0.0))
    K.beads(root, m, "read", K.stack_read_path(s, o, RK, 1), 4, 1, 0.62, 0.82, life=50, size=24.0)

    # beat 2: the stair seen from behind; layer RK's step and contact light with its word line
    sg = K.hidden("stair_on", s.layers[RK])
    c0, c1 = RK * LP + K.S_CH[0], RK * LP + K.S_CH[1]
    ext = (N - RK) * 140.0
    for sd in (1, -1):
        lo, hi = sorted((sd * (K.S_X[1] + 14), sd * (K.S_X[2] - 14)))
        box(f"stg{sd}", (lo, c0 - 52, zb - ext - 6), (hi, c1 + 52, zb + 4), m["wl_on"], sg)
        cx = (lo + hi) / 2
        tube(f"stc{sd}", (cx, c1 + 45, zb - ext + 70), (cx, N * LP + 125, zb - ext + 70), 28, m["wl_on"], sg, verts=10)
    on(sg, span(2, 0.35, 3, 0.0))

    xc = (K.S_X[1] + K.S_X[2]) / 2
    yt = TOPK * LP
    tags = {
        0: [("vertical bit line", (K.S_BLW, yt + 60.0, 0.0), 0.05),
            ("n+ drain on the bit line", (115.0, yt + K.S_CH[0], 0.0), 0.15),
            ("silicon channel", (xc, yt + CM, 2.0), 0.25),
            ("word line all round it", (xc, yt + K.S_CH[1] + 40.0, 0.0), 0.35),
            ("n+ source", (405.0, yt + K.S_CH[1], 0.0), 0.45),
            ("capacitor lies on its side", (K.S_X[3] + 380.0, yt + CM + 40.0, 0.0), 0.55)],
        1: [("layers pull apart", (s.pts["right"], 7 * (LP + STEP), 0.0), 0.05),
            ("oxide between layers", (s.pts["right"], RK * LP + 12.0, 0.0), 0.58),
            ("one word line per layer", (xc, RK * LP + K.S_CH[1] + 40.0, 0.0), 0.6),
            ("shared vertical bit line", (0.0, 2 * LP, 0.0), 0.7)],
        2: [("word lines step out at the back", (-K.S_X[2], 3 * LP + 160.0, zb - (N - 3) * 140.0), 0.05),
            ("one contact per layer", (xc, N * LP + 125.0, zb - 140.0 + 70.0), 0.2),
            ("lit: one layer's word line", (xc, c1 + 45.0, zb - ext + 30.0), 0.4)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            end = (i, 0.5) if text == "layers pull apart" else (i + 1, 0.0)
            label(text, pos, root, span(i, u, *end))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
