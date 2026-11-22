"""3D DRAM section 6, "Wafer-to-wafer bonding: periphery under the array" (heading 6 of
tui/src/screens/diagrams_pages/RND_3D_DRAM.txt), in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/rnd_3d_dram_section_6.py

Writes blender/rnd_3d_dram_section_6.blend and assets/rnd_3d_dram_section_6.glb. One beat is 8 s.

Zoom b flips and bonds the wafers and opens the bond face; this section shows the two processes,
the die shrink and the dies-per-wafer gain instead.

Beats (match diagrams_nodes/dram3d/sections/s6.rs):
  0 two wafers  side by side, two processes: a chunk grows out of each, the 4F2 VCT array on its
                Cu pads (cell wafer) and logic transistors and wiring under Cu pads (periphery)
  1 one die     a die with its periphery strip beside the array: the strip drops, spreads under
                the array, the array settles onto it and the die outline shrinks
  2 dies/wafer  a wafer of side-by-side dies and a bonded wafer of smaller dies; a scan bar counts
                each: over 20% more dies per wafer (Samsung's ISSCC 2026 claim)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, disc, empty, key, label  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402

PAGE = "rnd_3d_dram"
NAME = "section_6"
BEATS = 3

WR, WT = 800.0, 40.0  # beat 0's wafers
WX0 = 1000.0  # their centres: cell wafer at -WX0, periphery wafer at +WX0
CH_Y = 450.0  # each wafer's chunk grows up from this height
CS = 0.7  # the chunks' final scale

DX = 4200.0  # beat 1's die
A0, A1, AZ = DX - 500.0, DX + 500.0, (-1000.0, 0.0)  # the array block's footprint
AH = 260.0  # array block height
SW = 200.0  # periphery strip width beside the array (die area 1.2x)
PH = 260.0  # periphery strip height

WX = (8000.0, 9900.0)  # beat 2's two wafers
WR2 = 820.0
DIE_OLD, DIE_NEW = 160.0, 144.0  # (160/144)^2 = 1.23 die area; 60 -> 76 whole dies (+27%)

POSES = [
    ((0.0, 820.0, -250.0), 5900.0, 0.22, 0.2),
    ((DX + 80.0, 120.0, -500.0), 3300.0, 0.55, 0.42),
    ((sum(WX) / 2, 0.0, -60.0), 6300.0, 0.0, 0.95),
]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def die_count(r, die):
    """As rnd_3d_dram_kit.wafer lays its grid: whole dies inside r - 20."""
    n, c = int(r // die), 0
    for i in range(-n, n):
        for j in range(-n, n):
            x0, z0 = i * die + 8, j * die + 8
            if math.hypot(max(abs(x0), abs(x0 + die - 16)), max(abs(z0), abs(z0 + die - 16))) <= r - 20:
                c += 1
    return c


def wafers(root, m):
    """Beat 0: two wafers side by side, two processes. A chunk of each grows up out of its wafer:
    the cell wafer's 4F2 VCT array (DRAM process) over its Cu pads, the periphery wafer's logic
    transistors and wiring (logic process) under its Cu pads."""
    g = K.hidden("w0", root)
    on(g, beat(0))
    K.wafer(g, m, (-WX0, 0.0, 0.0), r=WR, t=WT, kind="cell", die=150.0, name="w_cell")
    K.wafer(g, m, (WX0, 0.0, 0.0), r=WR, t=WT, kind="peri", die=150.0, name="w_peri")
    # the cell chunk: a 3 x 2 VCT array, built about its own pivot (cut at local z = 0)
    pl = empty("w_cpv", g, P(-WX0, CH_Y, 0.0))
    arr = K.vct_array(pl, m, (0.0, K.V_BASE + 60.0, 0.0), nx=3, nz=2, name="w_va", cap_h=700.0)
    pads = [box("w_cbox", (arr.x0, 0.0, arr.zb), (arr.x1, 60.0 + K.V_BASE - 118.0, 0.0), m["sti"], pl)]
    for i, x in enumerate(arr.xs):
        pads.append(box(f"w_cpad{i}", (x - 150, 0.0, -50), (x - 50, 62.0, 1.6), m["cu"], pl))
    K.join(pads, "w_cpads")
    # the periphery chunk: logic transistors, wiring, its Cu pads on top
    pr = empty("w_ppv", g, P(WX0, CH_Y, 0.0))
    pe = K.periphery(pr, m, (0.0, K.PE_T, 0.0), -620.0, 620.0, -700.0, name="w_pe",
                     blocks=[("dec", 0.03, 0.3), ("sa", 0.36, 0.97)])
    for pv in (pl, pr):
        scale_keys(pv, [(0, 0.02), (F(0, 0.06), 0.02), (F(0, 0.38), CS)])
    stem = [box(f"w_stem{i}", (x - 8, WT / 2, -8), (x + 8, CH_Y, 8), m["axis"], g) for i, x in enumerate((-WX0, WX0))]
    K.join(stem, "w_stems")
    on(arr.wl_on[1], span(0, 0.5, 0, 0.8))
    on(arr.bl_on[0], span(0, 0.58, 0, 0.9))
    for i in range(3):
        on(arr.cells[(i, 0)].charge, span(0, 0.38, 1, 0.0))
    for o in pe.sa_on:
        on(o, span(0, 0.62, 1, 0.0))
    for o in pe.dec_on:
        on(o, span(0, 0.66, 1, 0.0))
    rp = [(x * CS - WX0, y * CS + CH_Y, z) for x, y, z in arr.cells[(1, 0)].read_path]
    K.beads(root, m, "w_rd", rp[:3], 3, 0, 0.55, 0.75, life=45)


def die_morph(root, m):
    """Beat 1: periphery strip beside the array -> under it; the die outline shrinks to 1/1.2."""
    g = K.hidden("d1", root)
    on(g, beat(1))
    z0, z1 = AZ
    st = K.Bin()
    # the array block: a cell slab with 4 x 4 raised mats and sense-amp stripes between
    top = empty("d_arr_mv", g)
    st.add(box("d_arr", (A0, 0.0, z0), (A1, AH, z1), m["die_cell"], top))
    mw = (A1 - A0) / 4
    for i in range(4):
        for j in range(4):
            x, z = A0 + i * mw, z0 + j * mw
            st.add(box(f"d_mat{i}{j}", (x + 22, AH, z + 22), (x + mw - 22, AH + 14, z + mw - 22), m["bl"], top))
    for i in range(1, 4):
        x = A0 + i * mw
        st.add(box(f"d_sa{i}", (x - 10, AH, z0 + 10), (x + 10, AH + 8, z1 - 10), m["sa"], top))
    st.merge("d_arr_static")
    K.lift(top, [(F(1, 0.0), 0.0), (F(1, 0.12), 0.0), (F(1, 0.3), PH * 0.75), (F(1, 0.62), PH * 0.75),
                 (F(1, 0.78), 0.0)])
    # the periphery strip beside the array: decoders and sense-amp blocks on logic silicon
    cx, cy, cz = A1 + SW / 2, PH / 2, (z0 + z1) / 2
    mv = empty("d_strip_mv", g)
    pv = empty("d_strip_pv", mv, P(cx, cy, cz))
    sb = K.Bin()
    sb.add(box("d_strip", (-SW / 2, -PH / 2, z0 - cz), (SW / 2, PH / 2, z1 - cz), m["peri_si"], pv))
    for k in range(5):
        zz = z0 - cz + 30 + k * (z1 - z0 - 60) / 5
        kind = "dec" if k % 2 else "sa"
        sb.add(box(f"d_blk{k}", (-SW / 2 + 25, PH / 2, zz), (SW / 2 - 25, PH / 2 + 18, zz + (z1 - z0 - 60) / 5 - 30),
                   m[kind], pv))
    sb.merge("d_strip_static")
    # drop below the array's level, then spread under it (volume kept: x 5, height 0.6)
    tx, ty = (A0 + A1) / 2, -PH * 0.3
    K.lift(mv, [(F(1, 0.12), 0.0), (F(1, 0.3), -PH)])
    key(mv, F(1, 0.62), "location", P(tx - cx, ty - cy, 0.0))
    scale_keys(pv, [(F(1, 0.3), 1.0), (F(1, 0.62), (5.0, 1.0, 0.6))])
    # bond plane, lit once the array is down on its periphery
    bl = K.hidden("d_bond", g)
    box("d_bond_m", (A0 - 8, -5.0, z0 - 8), (A1 + 8, 5.0, z1 + 8), m["bond"], bl)
    on(bl, span(1, 0.78, 2, 0.0))
    # die outline: a glowing rim on the floor, pivot at the left edge; shrinks 1.2 -> 1.0
    rim = empty("d_rim_pv", g, P(A0, 0.0, 0.0))
    y0 = -PH * 0.6 - 30.0
    e = 16.0
    x1 = A1 + SW - A0
    rb = [box("d_r0", (-e, y0, z0 - 40 - e), (x1 + e, y0 + 14, z0 - 40 + e), m["tile_edge"], rim),
          box("d_r1", (-e, y0, z1 + 40 - e), (x1 + e, y0 + 14, z1 + 40 + e), m["tile_edge"], rim),
          box("d_r2", (-e - 40, y0, z0 - 40), (-40 + e, y0 + 14, z1 + 40), m["tile_edge"], rim),
          box("d_r3", (x1 + 40 - e, y0, z0 - 40), (x1 + 40 + e, y0 + 14, z1 + 40), m["tile_edge"], rim)]
    K.join(rb, "d_rim")
    sx = (A1 - A0 + 80) / (x1 + 80)
    scale_keys(rim, [(F(1, 0.62), 1.0), (F(1, 0.9), (sx, 1.0, 1.0))])
    # signals: once bonded, reads drop from the array straight down into its periphery
    for i, x in enumerate((A0 + 250.0, A0 + 750.0)):
        K.beads(root, m, f"d_rd{i}", [(x, AH + 30.0, 14.0), (x, -PH * 0.5, 14.0)], 2, 1, 0.8 + 0.05 * i, 0.95,
                life=26, size=24.0)


def counts(root, m):
    """Beat 2: a wafer of side-by-side dies, and a bonded pair of the smaller dies; scan bars."""
    g = K.hidden("w2", root)
    on(g, beat(2))
    K.wafer(g, m, (WX[0], 0.0, 0.0), r=WR2, t=WT, kind="cell", die=DIE_OLD, name="w_old")
    # each old die keeps its periphery strip beside the array: a purple band on its right sixth
    strips, n = [], int(WR2 // DIE_OLD)
    for i in range(-n, n):
        for j in range(-n, n):
            x0, z0 = i * DIE_OLD + 8, j * DIE_OLD + 8
            if math.hypot(max(abs(x0), abs(x0 + DIE_OLD - 16)), max(abs(z0), abs(z0 + DIE_OLD - 16))) > WR2 - 20:
                continue
            xs = WX[0] + x0 + (DIE_OLD - 16) * 0.8
            strips.append(box(f"w_os{i}_{j}", (xs, WT / 2 + 3, z0), (WX[0] + x0 + DIE_OLD - 16, WT / 2 + 7, z0 + DIE_OLD - 16),
                              m["die_peri"], g))
    K.join(strips, "w_old_strips")
    K.wafer(g, m, (WX[1], -WT, 0.0), r=WR2, t=WT, kind="peri", die=150.0, name="w_new_peri")
    K.wafer(g, m, (WX[1], 0.0, 0.0), r=WR2, t=WT, kind="cell", die=DIE_NEW, name="w_new")
    box("w_new_bond", (WX[1] - 3, -WT / 2 - 4, -3), (WX[1] + 3, -WT / 2 + 4, 3), m["bond"], g)
    disc("w_new_bondm", (WX[1], -WT / 2, 0.0), WR2 + 5.0, 8.0, m["bond"], g, verts=64)
    for i, x in enumerate(WX):
        bar = K.hidden(f"w_scan{i}", root)
        mv = empty(f"w_scan_mv{i}", bar)
        box(f"w_scan_m{i}", (x - WR2 * 0.6, 26.0, -14.0), (x + WR2 * 0.6, 40.0, 14.0), m["tile_edge2"], mv)
        key(mv, F(2, 0.12), "location", P(0, 0, WR2 * 0.85))
        key(mv, F(2, 0.6), "location", P(0, 0, -WR2 * 0.85))
        on(bar, span(2, 0.12, 2, 0.6))


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    K.mats(m)
    wafers(root, m)
    die_morph(root, m)
    counts(root, m)
    n_old, n_new = die_count(WR2, DIE_OLD), die_count(WR2, DIE_NEW)
    print("section_6 die counts", n_old, n_new, f"{100.0 * (n_new / n_old - 1):.0f}%")

    tags = {
        0: [("cell wafer: DRAM cells", (-WX0 - WR * 0.6, 20.0, WR * 0.5)),
            ("periphery wafer: logic process", (WX0 + WR * 0.6, 20.0, WR * 0.5))],
        1: [],
        2: [("bonded: cell on periphery", (WX[1] + WR2 * 0.75, -40.0, WR2 * 0.6))],
    }
    late = {
        0: [("Samsung 16 Gb test chip, 10 nm class", (-WX0, CH_Y + 1700.0 * CS, 0.0), 0.4, 1.0),
            ("Cu pads: the bond face", (-WX0 + 620.0 * CS, CH_Y + 30.0 * CS, 0.0), 0.5, 1.0),
            ("sense amps, decoders", (WX0 + 620.0 * CS, CH_Y + (K.PE_SI - 80.0) * CS, 0.0), 0.62, 1.0)],
        1: [("periphery beside the array", (A1 + SW, PH, -200.0), 0.0, 0.3),
            ("cell array", (A0, AH + 20.0, -100.0), 0.0, 0.62),
            ("periphery slides under", (A1, -PH * 0.6, -100.0), 0.35, 0.78),
            ("same rules, smaller die", (A1 + 40.0, -PH * 0.6 - 30.0, -100.0), 0.82, 1.0)],
        2: [("periphery beside: fewer dies", (WX[0] - WR2 * 0.7, 20.0, WR2 * 0.7), 0.0, 1.0),
            ("over 20% more dies per wafer", (WX[1], 30.0, -WR2), 0.62, 1.0),
            ("Samsung, ISSCC 2026", (WX[1] - WR2 * 0.4, 30.0, -WR2 * 0.9), 0.7, 1.0)],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))
    for i, items in late.items():
        for text, pos, u0, u1 in items:
            label(text, pos, root, span(i, u0, i if u1 < 1.0 else i + 1, u1 if u1 < 1.0 else 0.0))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    K.finish(NAME, page=PAGE)
