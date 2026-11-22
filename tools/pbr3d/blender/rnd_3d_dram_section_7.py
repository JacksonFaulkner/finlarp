"""3D DRAM section 7, "Stacked 3D DRAM: layers of sideways cells" (heading 7 of
tui/src/screens/diagrams_pages/RND_3D_DRAM.txt), in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_7.py

Writes blender/rnd_3d_dram_section_7.blend and assets/rnd_3d_dram_section_7.glb. One beat is 8 s.

About layer counts (zoom c opens one stack's layers up close; the overview pulls 8 apart): a
16-layer block on its bonded periphery, a 5-layer block beside it, and a bar chart of the layer
counts the page quotes. All blocks are rnd_3d_dram_kit.stacked_3d, cut at z = 0.

Beats (match diagrams_nodes/dram3d/sections/s7.rs):
  0 sixteen    the 16 layers drop onto the periphery one after another (Samsung VS-DRAM, VLSI 2026);
               the vertical bit line lights and a bit runs down it into the periphery
  1 five       beside it the 5-layer block (SK hynix, VLSI 2024): its word lines light one per layer,
               counting 1-5, and a yield bar fills to 56.1%
  2 how many   bars rise in layers: 5, 16, then the 32-192 SK hynix says wide use needs and the
               200-300 a Micron engineer estimated to beat planar on cost (2021)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, empty, key, label, mat, show  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_7"
BEATS = 3

CAPL = 700.0  # shorter lateral capacitors keep the blocks compact
W = K.S_X[3] + CAPL + 40.0  # block half width
X16, X5 = 0.0, -3300.0
BOND = 30.0  # the 16-layer block sits this far above its periphery's bond face
DROP = 1400.0

BX = (2700.0, 3250.0, 3800.0, 4350.0)  # the four bars
BW = 200.0  # bar half width
LU = 8.0  # bar height per layer
BAR_U = (0.02, 0.08, 0.16, 0.3)  # when each bar starts to rise

POSES = [
    ((X16, 2150.0, -200.0), 11500.0, 0.45, 0.12),
    ((-1600.0, 1900.0, -200.0), 11500.0, 0.08, 0.10),
    ((3500.0, 1250.0, -200.0), 5300.0, -0.05, 0.1),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def sixteen(root, m):
    """Beat 0: periphery, then 16 layers dropping in; the bit line lights; a bit goes down."""
    sk = K.stacked_3d(root, m, (X16, BOND, 0.0), n=16, nz=1, name="s16", cap_l=CAPL)
    pe = K.periphery(root, m, (X16, 0.0, 0.0), X16 - W, X16 + W, sk.zs[-1] - K.S_ZP / 2, name="s16p",
                     blocks=[("dec", 0.03, 0.22), ("sa", 0.28, 0.72), ("dec", 0.78, 0.97)])
    for k, lg in enumerate(sk.layers):
        f0 = F(0, 0.04 + 0.035 * k)
        f1 = f0 + 14
        show(lg, [(f0, F(BEATS, 0))])
        key(lg, 0, "location", P(0, DROP, 0))
        key(lg, f0, "location", P(0, DROP, 0))
        key(lg, f1, "location", P(0, 0, 0))
    show(sk.layers_top, [(F(0, 0.04 + 0.035 * 16), F(BEATS, 0))])
    bond = K.hidden("s16_bond", root)
    box("s16_bondm", (X16 - W - 10, BOND - 8, sk.zs[-1] - K.S_ZP / 2 - 10), (X16 + W + 10, BOND + 6, 6.0), m["bond"], bond)
    on(bond, span(0, 0.02, 0, 0.6))
    on(sk.bl_on[0], span(0, 0.68, 0, 0.98) + span(2, 0.0, 3, 0.0))
    on(sk.wl_on[12], span(0, 0.7, 0, 0.9))
    on(sk.charges[12][0], span(0, 0.6, 0, 0.82))
    for o in pe.sa_on:
        on(o, span(0, 0.86, 1, 0.0))
    path = K.stack_read_path(sk, (X16, BOND, 0.0), 12, 1)
    path[-1] = (X16, -K.PE_BOND - K.PE_ILD - 60.0, 12.0)
    K.beads(root, m, "s16_rd", path, 3, 0, 0.7, 0.8, life=50)
    return sk, pe


def five(root, m):
    """Beat 1: a 5-layer block on a silicon base; its word lines count the layers; yield bar."""
    sk = K.stacked_3d(root, m, (X5, 0.0, 0.0), n=5, nz=1, name="s5", cap_l=CAPL)
    zb = sk.zs[-1] - K.S_ZP / 2
    box("s5_si", (X5 - W, -400.0, zb), (X5 + W, 0.0, 0.0), m["si"], root)
    for k in range(5):
        on(sk.wl_on[k], span(1, 0.08 + 0.1 * k, 1, 0.18 + 0.1 * k) + span(1, 0.62, 1, 0.66))
    for k in range(5):
        for ch in sk.charges[k]:
            on(ch, span(1, 0.6, 2, 0.0))
    # the yield gauge: a frame and a fill on a pivot at its foot, rising to 56.1%
    gx, gh = X5 + W + 450.0, 1600.0
    g = K.hidden("y_gauge", root)
    on(g, span(1, 0.0, 2, 0.0))
    fr = [box("y_f0", (gx - 130, -10.0, -150.0), (gx + 130, 10.0, -30.0), m["axis"], g),
          box("y_f1", (gx - 130, gh - 10, -150.0), (gx + 130, gh + 10, -30.0), m["axis"], g),
          box("y_f2", (gx - 130, 0.0, -150.0), (gx - 110, gh, -30.0), m["axis"], g),
          box("y_f3", (gx + 110, 0.0, -150.0), (gx + 130, gh, -30.0), m["axis"], g),
          box("y_bk", (gx - 110, 0.0, -160.0), (gx + 110, gh, -140.0), m["tile"], g)]
    K.join(fr, "y_frame")
    pv = empty("y_pv", g, P(gx, 0.0, -90.0))
    box("y_fill", (-100.0, 0.0, -50.0), (100.0, gh, 50.0), m["dec_on"], pv)
    scale_keys(pv, [(0, (1.0, 1.0, 0.001)), (F(1, 0.6), (1.0, 1.0, 0.001)), (F(1, 0.9), (1.0, 1.0, 0.561))])
    return sk, gx, gh


def bars(root, m):
    """Beat 2: layer counts as bars, LU per layer: 5, 16, 32-192 and 200-300 (ranges float)."""
    need = mat("d3s7_need", (0.95, 0.66, 0.30), rough=0.5)
    span_ = mat("d3s7_span", (0.45, 0.47, 0.54), rough=0.6)
    g = K.hidden("bars", root)
    on(g, beat(2))
    box("bar_base", (BX[0] - 400, -60.0, -500.0), (BX[-1] + 400, 0.0, 100.0), m["sti"], g)
    specs = [(0, 5, m["bl"]), (0, 16, m["bl"]), (32, 192, need), (200, 300, need)]
    tops = []
    for i, ((lo, hi, mk), x, u) in enumerate(zip(specs, BX, BAR_U)):
        y0 = lo * LU
        vis = K.hidden(f"bar_vis{i}", g)
        on(vis, span(2, u, 3, 0.0))
        pv = empty(f"bar_pv{i}", vis, P(x, y0, -BW))
        h = (hi - lo) * LU
        objs = [box(f"bar{i}", (-BW, 0.0, -BW), (BW, h, BW), mk, pv)]
        # a dark line every 16 layers so the bar reads as a stack
        for t in range(1, int((hi - lo) // 16) + 1):
            yy = t * 16 * LU
            if yy < h - 8:
                objs.append(box(f"bar{i}_t{t}", (-BW - 4, yy - 6, -BW - 4), (BW + 4, yy + 6, BW + 4), m["tile"], pv))
        K.join(objs, f"bar{i}_m")
        scale_keys(pv, [(0, (1.0, 1.0, 0.001)), (F(2, u), (1.0, 1.0, 0.001)), (F(2, u + 0.12), 1.0)])
        if lo > 0:  # a thin grey post up to where the range starts
            ps = empty(f"post_pv{i}", g, P(x, 0.0, -BW))
            box(f"post{i}", (-30.0, 0.0, -30.0), (30.0, y0, 30.0), span_, ps)
            scale_keys(ps, [(0, (1.0, 1.0, 0.001)), (F(2, u - 0.04), (1.0, 1.0, 0.001)), (F(2, u), 1.0)])
        tops.append((x, hi * LU, 0.0))
    return tops


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    s16, pe = sixteen(root, m)
    s5, gx, gh = five(root, m)
    tops = bars(root, m)

    top16 = BOND + K.stacked_top(16)
    late = {
        0: [("periphery wafer, bonded underneath", (X16 + W, -K.PE_BOND - K.PE_ILD, 0.0), 0.0, 1.0),
            ("16 layers of sideways cells", (X16 + W, top16 - 400.0, 0.0), 0.62, 1.0),
            ("vertical bit line", (X16 + K.S_BLW, top16 + 20.0, 0.0), 0.7, 1.0),
            ("Samsung VS-DRAM, VLSI 2026", (X16 - W, top16, 0.0), 0.62, 1.0)],
        1: [("Samsung: 16 layers", (X16 + W, top16 - 200.0, 0.0), 0.0, 1.0),
            ("SK hynix, VLSI 2024: 5 layers", (X5 + W, K.stacked_top(5), 0.0), 0.05, 1.0),
            ("one word line per layer", (X5 + (K.S_X[1] + K.S_X[2]) / 2, 4 * K.S_LP + K.S_CH[1] + 45.0, 0.0), 0.1, 0.6),
            ("yield: 56.1%", (gx, gh * 0.561 + 20.0, -30.0), 0.8, 1.0)],
        2: [("5", tops[0], 0.1, 1.0), ("16", tops[1], 0.16, 1.0),
            ("32-192 for wide use: SK hynix", tops[2], 0.3, 1.0),
            ("200-300 to beat planar on cost: Micron, 2021", tops[3], 0.44, 1.0),
            ("layers", (BX[0] - 400.0, 0.0, 100.0), 0.0, 1.0)],
    }
    for i, items in late.items():
        for text, pos, u0, u1 in items:
            label(text, pos, root, span(i, u0, i if u1 < 1.0 else i + 1, u1 if u1 < 1.0 else 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
