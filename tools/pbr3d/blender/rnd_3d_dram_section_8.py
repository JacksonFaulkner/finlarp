"""3D DRAM section 8, "The weak spot: the floating body" (heading 8 of
tui/src/screens/diagrams_pages/RND_3D_DRAM.txt), in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_8.py

Writes blender/rnd_3d_dram_section_8.blend and assets/rnd_3d_dram_section_8.glb. One beat is 8 s.

Zoom e shows the floating body itself; this section is the comparison and the two fixes the page
names, each a cut-open cell at z = 0 (rnd_3d_dram_kit.py pieces plus two cells drawn here).

Beats (match diagrams_nodes/dram3d/sections/s8.rs):
  0 why        a planar transistor beside a VCT pillar: in the planar cell holes made in the body
               drain down into the silicon; in the pillar they have nowhere to go and pile up
  1 back gate  SK hynix's 4F2 VG idea: two pillars share a back gate between them; it lights and
               pulls the holes out of the bodies, and the Id-Vg curve slides back to where it was
  2 IGZO       a silicon pillar beside a junctionless IGZO pillar (Kioxia/Nanya, IEDM 2024): the
               silicon cell gathers holes and its charge leaks away; the IGZO cell has no body to
               charge and keeps its bit
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, ball, beat, box, label, mat  # noqa: E402
from sand_zooms import camera, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import V_BASE, V_BL, V_BODY, V_CAP0, V_DRAIN, V_GATE, V_OX, V_PAD, V_PW, V_SRC, V_WL, on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_8"
BEATS = 3

XP, XV = -900.0, 700.0  # beat 0: planar cell, VCT cell
YV = -560.0  # the VCT cell's origin: its pillar body level with the planar channel
XG = 3200.0  # beat 1: the back-gate pair
GP = 220.0  # pillar offset from the pair's centre
XS, XI = 5600.0, 6700.0  # beat 2: silicon pillar, IGZO pillar
CAP_H = 600.0
VT_X = XG - GP - V_WL - 620.0  # beat 1's Id-Vg gauge, left of the pair

POSES = [
    ((-80.0, -120.0, 0.0), 4300.0, 0.18, 0.10),
    ((XG - 330.0, 480.0, 0.0), 3800.0, 0.10, 0.10),
    ((0.5 * (XS + XI), 620.0, 0.0), 3900.0, -0.10, 0.10),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def pillar_cell(root, m, x, name, body_mk, nplus=True, wl_sides=(-1, 1), bl_x=None, bl=True):
    """A vertical cell cut at z = 0, origin (x, 0): base oxide, buried bit line, pillar (n+ / body /
    n+, or one material if not nplus: junctionless), gate oxide, word-line bars on `wl_sides`, pad
    and capacitor. Returns (static objects, capacitor pivot, charge switch)."""
    st = []
    bx0, bx1 = bl_x or (x - K.FS, x + K.FS)
    if bl:
        st.append(box(f"{name}_base", (bx0, -V_BASE, -K.FS), (bx1, V_BL[0], 0.0), m["ild"], root))
        st.append(box(f"{name}_bl", (bx0, V_BL[0], -K.V_BLW), (bx1, V_BL[1], 0.0), m["bl"], root))
    if nplus:
        st.append(box(f"{name}_dr", (x - V_PW, V_DRAIN[0], -V_PW), (x + V_PW, V_DRAIN[1], 1.5), m["nplus"], root))
        st.append(box(f"{name}_bd", (x - V_PW, V_BODY[0], -V_PW), (x + V_PW, V_BODY[1], 1.5), m[body_mk], root))
        st.append(box(f"{name}_sr", (x - V_PW, V_SRC[0], -V_PW), (x + V_PW, V_SRC[1], 1.5), m["nplus"], root))
    else:
        st.append(box(f"{name}_ch", (x - V_PW, V_DRAIN[0], -V_PW), (x + V_PW, V_SRC[1], 1.5), m[body_mk], root))
    st.append(box(f"{name}_ox", (x - V_OX, V_GATE[0] - 20, -V_OX), (x + V_OX, V_GATE[1] + 20, 0.0), m["gox"], root))
    for s in wl_sides:
        lo, hi = sorted((x + s * V_OX, x + s * V_WL))
        st.append(box(f"{name}_wl{s}", (lo, V_GATE[0], -K.FS), (hi, V_GATE[1], 0.0), m["wl"], root))
    st.append(box(f"{name}_wlb", (x - V_OX, V_GATE[0], -V_WL), (x + V_OX, V_GATE[1], -V_OX), m["wl"], root))
    st.append(box(f"{name}_pad", (x - 110, V_PAD[0], -110), (x + 110, V_PAD[1], 1.0), m["contact"], root))
    cap, ch = K.capacitor(root, m, f"{name}_cap", (x, V_CAP0, 0.0), CAP_H, K.V_CAP_R, True, cut_z=0.0)
    return st, cap, ch


def holes_in(root, m, name, x, y0, n=6, zf=20.0):
    """n hole balls in a pillar body (each its own hidden switch), two columns, bottom up."""
    hs = []
    for k in range(n):
        hx = x + (-24 if k % 2 == 0 else 24)
        hy = y0 + 55 + (k // 2) * 80
        g = K.hidden(f"{name}_h{k}", root)
        ball(f"{name}_hb{k}", (hx, hy, zf), 22, m["hole"], g, segs=10)
        hs.append(g)
    return hs


def why(root, m):
    """Beat 0: planar (holes drain to the silicon) beside VCT (holes pile up)."""
    pc = K.planar_cell(root, m, (XP, 0.0, 0.0), name="p8", tile=False, cap_h=CAP_H)
    vc = K.vct_cell(root, m, (XV, YV, 0.0), name="v8", tile=False, cap_h=CAP_H)
    on(pc.wl_on, span(0, 0.08, 0, 0.95))
    on(pc.chan_on, span(0, 0.1, 0, 0.95))
    on(vc.wl_on, span(0, 0.08, 0, 0.95))
    on(vc.chan_on, span(0, 0.1, 0, 0.95))
    for k, h in enumerate(vc.holes):
        on(h, span(0, 0.15 + 0.07 * k, 1, 0.0))
    on(vc.body, span(0, 0.6, 1, 0.0))
    # planar: holes made at the channel run down into the silicon substrate and away
    for i, dx in enumerate((-150.0, -40.0)):
        K.beads(root, m, f"p8_h{i}", [(XP + dx, -K.PL_TR - 30.0, 14.0), (XP + dx, -580.0, 14.0)], 5, 0,
                0.15 + 0.05 * i, 0.85, life=40, size=26.0, mk="hole")
    return pc, vc


def back_gate(root, m):
    """Beat 1: two pillars, word lines outside, a shared back gate between them."""
    bg = mat("d3s8_bg", (0.92, 0.62, 0.26), metal=0.4, rough=0.4)
    bg_on = mat("d3s8_bg_on", (1.0, 0.72, 0.30), emit=(1.0, 0.66, 0.22), strength=2.8)
    st = []
    xl, xr = XG - GP, XG + GP
    span_x = (XG - GP - K.FS, XG + GP + K.FS)
    for i, (x, s) in enumerate(((xl, -1), (xr, 1))):
        objs, cap, ch = pillar_cell(root, m, x, f"g8{i}", "body", wl_sides=(s,), bl_x=span_x, bl=(i == 0))
        st += objs
        on(ch, span(1, 0.0, 2, 0.0))
    # the shared back gate fills the gap between the two pillars' oxides
    st.append(box("g8_bg", (xl + V_OX, V_GATE[0], -K.FS), (xr - V_OX, V_GATE[1], 0.0), bg, root))
    K.join(st, "g8_static")
    glow = K.hidden("g8_bg_on", root)
    box("g8_bgg", (xl + V_OX - 2, V_GATE[0] - 10, -K.FS), (xr - V_OX + 2, V_GATE[1] + 10, 4.5), bg_on, glow)
    on(glow, span(1, 0.38, 2, 0.0))
    # holes sit in both bodies, then the back gate pulls them out
    for i, x in enumerate((xl, xr)):
        hs = holes_in(root, m, f"g8{i}", x, V_BODY[0])
        for k, h in enumerate(hs):
            on(h, span(1, 0.02 + 0.03 * k, 1, 0.42 + 0.04 * k))
        K.beads(root, m, f"g8_out{i}", [(x, 0.5 * (V_BODY[0] + V_BODY[1]), 20.0), (XG, 0.5 * (V_BODY[0] + V_BODY[1]), 20.0)],
                3, 1, 0.42, 0.62, life=24, size=20.0, mk="hole")
    vt = K.vt_gauge(root, m, (VT_X, 120.0, 0.0), w=440.0, h=400.0, name="vt8")
    on(vt.g, beat(1))
    K.vt_shift(vt, [(F(1, 0.0), -120.0), (F(1, 0.45), -120.0), (F(1, 0.8), 0.0)])
    return xl, xr, vt


def igzo(root, m):
    """Beat 2: a silicon pillar (holes, its charge leaks) beside a junctionless IGZO pillar."""
    m["igzo"] = mat("d3s8_igzo", (0.30, 0.78, 0.62), rough=0.45)
    st_s, cap_s, ch_s = pillar_cell(root, m, XS, "s8", "body")
    st_i, cap_i, ch_i = pillar_cell(root, m, XI, "i8", "igzo", nplus=False)
    K.join(st_s + st_i, "s8_static")
    on(ch_s, span(2, 0.0, 2, 0.62))
    on(ch_i, span(2, 0.0, 3, 0.0))
    hs = holes_in(root, m, "s8", XS, V_BODY[0])
    for k, h in enumerate(hs):
        on(h, span(2, 0.08 + 0.05 * k, 3, 0.0))
    bg = K.hidden("s8_body", root)
    box("s8_bodyg", (XS - V_PW + 14, V_BODY[0] + 6, -40.0), (XS + V_PW - 14, V_BODY[1] - 6, 4.5), m["body_glow"], bg)
    on(bg, span(2, 0.35, 3, 0.0))
    # the silicon cell's charge leaks down the pillar and away
    K.beads(root, m, "s8_leak", [(XS, V_CAP0 + 250.0, 14.0), (XS, V_DRAIN[0], 14.0), (XS - K.FS + 20.0, 60.0, 14.0)],
            4, 2, 0.3, 0.6, life=40, size=20.0)
    return ch_s, ch_i


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    pc, vc = why(root, m)
    xl, xr, vt = back_gate(root, m)
    igzo(root, m)

    vmid = YV + 0.5 * (V_BODY[0] + V_BODY[1])
    gmid = 0.5 * (V_GATE[0] + V_GATE[1])
    tags = {
        0: [("planar: body joins the silicon", (XP - 300.0, -300.0, 0.0)),
            ("pillar: body cut off below", (XV + V_PW, YV + V_DRAIN[0], 0.0))],
        1: [("shared back gate", (XG, V_GATE[1] + 20.0, 0.0)),
            ("word line", (xr + V_WL, gmid, 0.0)),
            ("SK hynix 4F2 VG, VLSI 2026", (XG - GP - V_WL, V_CAP0 + CAP_H, 0.0))],
        2: [("silicon pillar", (XS - V_WL, gmid, 0.0)),
            ("IGZO channel: junctionless", (XI + V_WL, gmid, 0.0)),
            ("Kioxia + Nanya, IEDM 2024", (XI, V_CAP0 + CAP_H, 0.0))],
    }
    late = {
        0: [("holes drain away", (XP - 100.0, -560.0, 14.0), 0.3),
            ("holes pile up in the body", (XV - V_WL, vmid - 140.0, 20.0), 0.45)],
        1: [("back gate pulls the holes out", (XG, gmid - 140.0, 20.0), 0.42),
            ("threshold back where it was", (VT_X + 220.0, 520.0, 0.0), 0.7)],
        2: [("charge leaks away", (XS - K.FS, 60.0, 14.0), 0.35),
            ("leakage < 1 aA, retention > 100 s", (XI + K.V_CAP_R, V_CAP0 + 300.0, 0.0), 0.55)],
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
    K.finish(NAME, page=PAGE)
