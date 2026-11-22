"""3D DRAM section 4, "Why DRAM has to go vertical" (heading 4 of RND_3D_DRAM.txt).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_4.py

Writes blender/rnd_3d_dram_section_4.blend and assets/rnd_3d_dram_section_4.glb. Three 8 s beats:
  0 narrower   four capacitors, one per shrink, grow up one after another: each narrower, so each
               must be taller to hold the same charge (radius x height kept constant)
  1 yield      the tallest, thinnest one leans over into its neighbour and shorts (one way tall
               capacitors fail): close, from above
  2 floor      the way out is floor area: two equal floor plates seen from above, 12F x 4F each;
               eight 6F2 tiles fill one, twelve 4F2 tiles fill the other (50% more cells)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, ball, box, disc, label  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import FS, on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_4"
BEATS = 3

CAP_XS = [-900.0, -300.0, 300.0, 900.0]
CAP_R = [165.0, 128.0, 98.0, 74.0]
RH = 165.0 * 1150.0  # radius x height, the same for every capacitor
PAD_Y = 0.0
LEAN = math.radians(12.0)

XC = 4800.0  # the two floor plates' x centre
ZA, ZB = -650.0, 650.0  # 6F2 plate behind, 4F2 plate in front
PW, PD = 12 * FS, 4 * FS  # plate size: 12F x 4F

POSES = [
    ((0.0, 1100.0, 0.0), 6400.0, 0.30, 0.14),
    ((450.0, 1350.0, 0.0), 4900.0, -0.20, 0.30),
    ((XC, 0.0, 0.0), 5000.0, 0.0, 1.10),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    m["short"] = K.mat("d3s4_short", (1.0, 0.25, 0.2), emit=(1.0, 0.25, 0.15), strength=5.0)

    # ---- beats 0-1: four generations of capacitor on one oxide strip ----
    st = K.Bin()
    st.add(box("strip_si", (-1250.0, -420.0, -260.0), (1250.0, -160.0, 0.0), m["si"], root))
    st.add(box("strip_ild", (-1250.0, -160.0, -260.0), (1250.0, PAD_Y - 30.0, 0.0), m["ild"], root))
    for i, (x, r) in enumerate(zip(CAP_XS, CAP_R)):
        st.add(box(f"pad{i}", (x - r - 20, PAD_Y - 30.0, -r - 20), (x + r + 20, PAD_Y, 1.0), m["contact"], root))
    st.merge("strip_static")

    caps = []
    for i, (x, r) in enumerate(zip(CAP_XS, CAP_R)):
        h = RH / r
        pv, ch = K.capacitor(root, m, f"cap{i}", (x, PAD_Y, 0.0), h, r, True, cut_z=0.0)
        u = 0.08 + 0.17 * i
        scale_keys(pv, [(F(0, 0.0), (1.0, 1.0, 0.02)), (F(0, u), (1.0, 1.0, 0.02)), (F(0, u + 0.14), 1.0)])
        on(ch, span(0, u + 0.12, 3, 0.0))
        caps.append((pv, h, r))

    # beat 1: the tallest leans into its neighbour; a short flashes at the contact
    pv3, h3, r3 = caps[3]
    K.key(pv3, F(1, 0.0), "rotation_euler", (0.0, 0.0, 0.0))
    K.key(pv3, F(1, 0.2), "rotation_euler", (0.0, 0.0, 0.0))
    K.key(pv3, F(1, 0.5), "rotation_euler", (0.0, -LEAN, 0.0))
    _, h2, r2 = caps[2]
    # where the leaning capacitor's left wall meets the neighbour's right wall
    yc = (CAP_XS[3] - CAP_XS[2] - r2 - r3 / math.cos(LEAN)) / math.tan(LEAN)
    yc = min(yc, h2 - 40.0)
    spark = K.hidden("short", root)
    ball("short_b", (CAP_XS[2] + r2, PAD_Y + yc, 30.0), 70.0, m["short"], spark, segs=14)
    on(spark, span(1, 0.5, 1, 0.58) + span(1, 0.64, 1, 0.72) + span(1, 0.78, 2, 0.0))

    # ---- beat 2: equal floor plates, 6F2 vs 4F2 ----
    for cz, nx, nz, tx, edge, nm in ((ZA, 3, 2, 4, "tile_edge", "a"), (ZB, 2, 2, 6, "tile_edge2", "b")):
        cx = XC
        box(f"plate_{nm}", (cx - PW / 2 - 40, -60.0, cz - PD / 2 - 40), (cx + PW / 2 + 40, 0.0, cz + PD / 2 + 40), m["ild"], root)
        k = 0
        for j in range(2):
            for i in range(tx):
                x = cx - PW / 2 + (i + 0.5) * nx * FS
                z = cz - PD / 2 + (j + 0.5) * nz * FS
                sw = K.hidden(f"t{nm}{k}", root)
                on(sw, span(2, 0.1 + (0.05 if nm == "a" else 0.035) * k, 3, 0.0))
                K.footprint(sw, m, (x, 0.0, z), nx, nz, 0.0, name=f"ft{nm}{k}", edge=edge)
                disc(f"stub{nm}{k}", (x, 70.0, z), 0.62 * FS, 120.0, m["plate"], sw, verts=20)
                k += 1

    # ---- tags ----
    label("same charge each time", (CAP_XS[0] + CAP_R[0], RH / CAP_R[0] * 0.6, 0.0), root, span(0, 0.2, 1, 0.0))
    label("narrower capacitor must grow taller", (CAP_XS[3] + CAP_R[3], RH / CAP_R[3] * 0.8, 0.0), root, span(0, 0.7, 1, 0.0))
    label("shrink: 6F2 cell, ever thinner", (0.0, -420.0, 0.0), root, span(0, 0.0, 1, 0.0))
    label("tall, thin: hard to make with good yield", (CAP_XS[3] - 40.0, 700.0, 0.0), root, span(1, 0.0, 2, 0.0))
    label("one failure: it leans and shorts", (CAP_XS[2] + r2, PAD_Y + yc, 30.0), root, span(1, 0.55, 2, 0.0))
    label("6F2 (2F x 3F): 8 cells", (XC + PW / 2, 0.0, ZA - PD / 2), root, span(2, 0.1, 3, 0.0))
    label("4F2 (2F x 2F): 12 cells, +50%", (XC + PW / 2, 0.0, ZB + PD / 2), root, span(2, 0.35, 3, 0.0))
    label("same floor: 12F x 4F each", (XC - PW / 2, 0.0, 0.0), root, span(2, 0.0, 3, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
