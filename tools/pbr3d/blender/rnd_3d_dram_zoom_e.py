"""R&D 3D DRAM zoom-in e, "the floating body", in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_zoom_e.py

Writes blender/rnd_3d_dram_zoom_e.blend and assets/rnd_3d_dram_zoom_e.glb. One beat is 8 s.

Two subjects, the camera cuts between them at beat boundaries:
  left   one VCT cell (rnd_3d_dram_kit.vct_cell) whose p-type body fills with holes, and an Id-Vg gauge
  right  the two fixes, drawn here as simplified VCT cells cut at z = 0: a pillar with the word line
         on one side and a back gate on the other (SK hynix VG), and a junctionless IGZO pillar
         (Kioxia / Nanya OCTRAM)

Beats (match diagrams_nodes/dram3d/zooms/e.rs):
  0 float    the body sits between two n+ layers over oxide and the bit line: no tie to silicon;
             holes pile up in it
  1 vt       the threshold curve slides left; charge leaks out of the capacitor with the word line off
  2 fixes    back gate pulls the holes out; IGZO pillar has no p-type body to fill
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, ball, box, empty, label, mat  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "zoom_e"
BEATS = 3
XB, XI = 4000.0, 4800.0  # beat 2: back-gate cell, IGZO cell
CAP_H = 700.0

POSES = [
    ((0.0, 330.0, 0.0), 1750.0, 0.30, 0.10),
    ((-480.0, 420.0, 0.0), 2750.0, 0.22, 0.10),
    ((4400.0, 430.0, 0.0), 2500.0, 0.22, 0.10),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def fix_cell(root, m, x, name, igzo):
    """A simplified VCT cell cut at z = 0. igzo=False: n+/p/n+ silicon pillar, word line on the -x
    side, back gate on the +x side. igzo=True: one junctionless IGZO block, word line both sides."""
    g = empty(name, root)
    st = K.Bin()
    hw, pw = K.FS, K.V_PW
    st.add(box(f"{name}_base", (x - hw, -K.V_BASE, -hw), (x + hw, 0.0, 0.0), m["ild"], g))
    st.add(box(f"{name}_bl", (x - hw, 0.0, -K.V_BLW), (x + hw, K.V_BL[1], 0.0), m["bl"], g))
    if igzo:
        st.add(box(f"{name}_ch", (x - pw, K.V_DRAIN[0], -pw), (x + pw, K.V_SRC[1], 1.5), m["igzo"], g))
    else:
        st.add(box(f"{name}_dr", (x - pw, K.V_DRAIN[0], -pw), (x + pw, K.V_DRAIN[1], 1.5), m["nplus"], g))
        st.add(box(f"{name}_bd", (x - pw, K.V_BODY[0], -pw), (x + pw, K.V_BODY[1], 1.5), m["body"], g))
        st.add(box(f"{name}_sr", (x - pw, K.V_SRC[0], -pw), (x + pw, K.V_SRC[1], 1.5), m["nplus"], g))
    st.add(box(f"{name}_ox", (x - K.V_OX, K.V_GATE[0] - 20, -K.V_OX), (x + K.V_OX, K.V_GATE[1] + 20, 0.0), m["gox"], g))
    y0, y1 = K.V_GATE
    st.add(box(f"{name}_wl", (x - K.V_WL, y0, -hw), (x - K.V_OX, y1, 0.0), m["wl"], g))
    if igzo:
        st.add(box(f"{name}_wl2", (x + K.V_OX, y0, -hw), (x + K.V_WL, y1, 0.0), m["wl"], g))
        st.add(box(f"{name}_wlb", (x - K.V_OX, y0, -K.V_WL), (x + K.V_OX, y1, -K.V_OX), m["wl"], g))
    else:
        st.add(box(f"{name}_bg", (x + K.V_OX, y0 - 60, -hw), (x + K.V_WL + 30, y1 + 60, 0.0), m["bg"], g))
    st.add(box(f"{name}_pad", (x - 110, K.V_PAD[0], -110), (x + 110, K.V_PAD[1], 1.0), m["contact"], g))
    st.merge(f"{name}_static")
    _, ch = K.capacitor(g, m, f"{name}_cap", (x, K.V_CAP0, 0.0), CAP_H, K.V_CAP_R, True, cut_z=0.0)
    return g, ch


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    m["bg"] = mat("d3e_bg", (0.30, 0.55, 0.40), metal=0.5, rough=0.35)
    m["bg_on"] = mat("d3e_bg_on", (0.40, 1.0, 0.60), emit=(0.35, 1.0, 0.55), strength=2.6)
    m["igzo"] = mat("d3e_igzo", (0.42, 0.74, 0.70), rough=0.45)

    # ---- beats 0-1: the floating body ----
    c = K.vct_cell(root, m, (0.0, 0.0, 0.0), "vc", cap_h=CAP_H, tile=False, holes=8)
    on(c.charge, span(0, 0.0, 2, 0.0))
    for k, hg in enumerate(c.holes):
        on(hg, span(0, 0.18 + 0.07 * k, 2, 0.0))
    on(c.body, span(0, 0.7, 2, 0.0))
    vt = K.vt_gauge(root, m, (-1180.0, 180.0, 0.0), w=520.0, h=440.0, name="vt")
    on(vt.g, span(1, 0.0, 2, 0.0))
    K.vt_shift(vt, [(F(1, 0.2), 0.0), (F(1, 0.6), -150.0)])
    on(c.bl_on, span(1, 0.72, 2, 0.0))
    K.beads(root, m, "leak", c.read_path[:3] + [(-K.FS - 150.0, K.V_BL[1] - 20.0, 12.0)], 2, 1, 0.62, 0.8,
            life=80, size=20.0)

    # ---- beat 2: the fixes ----
    gb, chb = fix_cell(root, m, XB, "fb", igzo=False)
    gi, chi = fix_cell(root, m, XI, "fi", igzo=True)
    on(chb, beat2 := span(2, 0.0, 3, 0.0))
    on(chi, beat2)
    bgo = K.hidden("bg_on", root)
    box("bg_glow", (XB + K.V_OX - 4, K.V_GATE[0] - 66, -K.FS), (XB + K.V_WL + 36, K.V_GATE[1] + 66, 4.5), m["bg_on"], bgo)
    on(bgo, span(2, 0.4, 3, 0.0))
    for k in range(4):
        hg = K.hidden(f"fbh{k}", root)
        ball(f"fbh{k}_b", (XB + (-24 if k % 2 else 24), K.V_BODY[0] + 80 + (k // 2) * 110, 18.0), 22, m["hole"], hg, segs=10)
        on(hg, span(2, 0.08 + 0.05 * k, 2, 0.42 + 0.025 * k))

    yb = (K.V_BODY[0] + K.V_BODY[1]) / 2
    tags = {
        0: [("n+ above", (K.V_PW, 640.0, 0.0), 0.05), ("p-type body", (K.V_PW, yb, 0.0), 0.1),
            ("n+ below", (K.V_PW, 160.0, 0.0), 0.15),
            ("oxide and bit line underneath: no tie to the silicon", (K.FS, -60.0, 0.0), 0.25),
            ("holes pile up in the body", (-30.0, 330.0, 20.0), 0.5)],
        1: [("threshold drops", (-1180.0 + 300.0, 180.0 + 440.0, 0.0), 0.25),
            ("charged body: turns on early", (-K.V_WL, yb, 0.0), 0.4),
            ("leaks with the word line off", (-K.FS - 80.0, 55.0, 0.0), 0.65)],
        2: [("word line", (XB - K.V_WL, 300.0, 0.0), 0.05),
            ("back gate (SK hynix VG)", (XB + K.V_WL + 30.0, 300.0, 0.0), 0.15),
            ("holes drained, threshold held", (XB, yb + 60.0, 18.0), 0.5),
            ("IGZO channel, no junctions (OCTRAM)", (XI + K.V_PW, 400.0, 0.0), 0.3),
            ("no p-type body to fill", (XI, 180.0, 4.0), 0.6)],
    }
    for i, items in tags.items():
        for text, pos, u in items:
            label(text, pos, root, span(i, u, i + 1, 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
