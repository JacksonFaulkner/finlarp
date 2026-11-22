"""3D DRAM section 5, "The 4F2 cell: a vertical channel transistor" (heading 5 of RND_3D_DRAM.txt).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_5.py

Writes blender/rnd_3d_dram_section_5.blend and assets/rnd_3d_dram_section_5.glb. Two VCT cells: one
cut open at z = 0, one whole beside it (its word line visibly closes round the pillar). Three 8 s
beats:
  0 pillar     close on the cut pillar from the left: n+ / channel / n+ stacked in one upright
               pillar, gate oxide round it, capacitor straight on top
  1 gate       from high on the right: the whole cell's word line lights as a ring round its pillar;
               in the cut cell the channel turns on and charge climbs from the bit line into the
               capacitor (a write)
  2 materials  charge leaks back out of the silicon pillar (red beads); the channel turns to IGZO
               and the leak stops; the word line's TiN turns to molybdenum (both reported, not final)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, box, label  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import FS, V_BL, V_BODY, V_CAP0, V_DRAIN, V_GATE, V_OX, V_PAD, V_PW, V_SRC, V_WL, on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_5"
BEATS = 3

XC = 0.0  # cut cell
XW, ZW = -700.0, -750.0  # whole cell, behind and to the left

POSES = [
    ((XC, 520.0, 0.0), 2600.0, 0.45, 0.08),
    ((-350.0, 560.0, -380.0), 3500.0, -0.28, 0.42),
    ((XC, 620.0, 0.0), 3000.0, -0.12, 0.10),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    m["leak"] = K.mat("d3s5_leak", (1.0, 0.3, 0.25), emit=(1.0, 0.25, 0.2), strength=3.5)
    m["igzo"] = K.mat("d3s5_igzo", (0.30, 0.78, 0.62), emit=(0.25, 0.70, 0.55), strength=0.9)
    m["mo"] = K.mat("d3s5_mo", (0.80, 0.82, 0.88), metal=1.0, rough=0.2)

    vc = K.vct_cell(root, m, (XC, 0.0, 0.0), "vc", tile=False)
    vw = K.vct_cell(root, m, (XW, 0.0, ZW), "vw", cutp=False, tile=False)

    # beat 0: the cut cell holds a bit; the pillar's parts lit in turn by the tags only
    on(vc.charge, span(0, 0.0, 1, 0.3) + span(1, 0.72, 3, 0.0))
    on(vw.charge, span(0, 0.0, 3, 0.0))

    # beat 1: the gate ring lights on the whole cell, the cut cell's channel opens and it is written
    on(vw.wl_on, span(1, 0.2, 1, 0.9))
    on(vc.wl_on, span(1, 0.3, 1, 0.9))
    on(vc.chan_on, span(1, 0.36, 1, 0.9))
    on(vc.bl_on, span(1, 0.4, 1, 0.9))
    zt = 12.0
    write = [(XC + FS + 250.0, V_BL[1] - 20.0, zt), (XC, V_BL[1] - 20.0, zt), (XC, V_PAD[0], zt), (XC, V_CAP0 + 450.0, zt)]
    K.beads(root, m, "write", write, 4, 1, 0.42, 0.62, life=45)

    # beat 2: leakage through the silicon channel, then IGZO and Mo
    leak = [(XC - 30.0, V_CAP0 + 300.0, zt), (XC - 30.0, V_PAD[0], zt), (XC - 30.0, V_BL[1] - 20.0, zt),
            (XC - FS - 250.0, V_BL[1] - 20.0, zt)]
    K.beads(root, m, "leak", leak, 3, 2, 0.05, 0.3, life=70, size=18.0, mk="leak")
    ig = K.hidden("igzo", root)
    box("igzo_m", (XC - V_PW - 1, V_BODY[0] - 2, -V_PW - 1), (XC + V_PW + 1, V_BODY[1] + 2, 2.6), m["igzo"], ig)
    on(ig, span(2, 0.45, 3, 0.0))
    mo = K.hidden("mo", root)
    for s in (-1, 1):
        lo, hi = sorted((XC + s * (V_OX + 1), XC + s * (V_WL + 2)))
        box(f"mo_m{s}", (lo, V_GATE[0] - 2, -FS - 1), (hi, V_GATE[1] + 2, 2.6), m["mo"], mo)
    on(mo, span(2, 0.68, 3, 0.0))

    # ---- tags ----
    tags0 = [
        ("n+ under the capacitor", (XC + V_PW, (V_SRC[0] + V_SRC[1]) / 2, 0.0), 0.05),
        ("channel: upright silicon pillar", (XC + V_PW, (V_BODY[0] + V_BODY[1]) / 2, 0.0), 0.2),
        ("n+ on the bit line", (XC + V_PW, (V_DRAIN[0] + V_DRAIN[1]) / 2, 0.0), 0.35),
        ("gate oxide round the pillar", (XC + V_OX, V_GATE[1] + 10.0, 0.0), 0.5),
        ("capacitor straight on top: 4F2", (XC + 150.0, V_CAP0 + 300.0, 0.0), 0.62),
    ]
    for text, pos, u in tags0:
        label(text, pos, root, span(0, u, 1, 0.0))
    label("word line wraps the pillar: the gate", (XW + V_WL, (V_GATE[0] + V_GATE[1]) / 2, ZW + FS), root, span(1, 0.15, 2, 0.0))
    label("bit line underneath", (XC + FS, (V_BL[0] + V_BL[1]) / 2, 0.0), root, span(1, 0.4, 2, 0.0))
    label("charge written into the capacitor", (XC + 150.0, V_CAP0 + 600.0, 0.0), root, span(1, 0.55, 2, 0.0))
    label("silicon channel leaks charge", (XC - V_PW, 400.0, 0.0), root, span(2, 0.05, 2, 0.45))
    label("IGZO channel: far less leakage", (XC - V_PW, 400.0, 0.0), root, span(2, 0.45, 3, 0.0))
    label("Mo in place of TiN word line", (XC + V_WL, V_GATE[0] + 60.0, 0.0), root, span(2, 0.68, 3, 0.0))
    label("Samsung, reported", (XC + 150.0, V_CAP0 + 500.0, 0.0), root, span(2, 0.5, 3, 0.0))
    _ = beat

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
