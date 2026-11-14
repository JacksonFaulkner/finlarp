"""The ten CELL write-up sections, each a 3D picture authored in Blender and exported for pbr3d in
the MELT + PULL template (docs/diagram-pages.md). Cell pieces come from cell_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/cell_sections.py [-- 3 5]

For each section it writes blender/cell_sec<N>.blend and assets/cell_sec<N>.glb.

  1 what happens   a full capacitor reads as 1; an empty one as 0; an array of cells, each its own bit (3 beats)
  2 the parts      word line, storage capacitor, bit line, sense amp, precharge (5 beats)
  3 one read       precharge, word line, charge sharing, sense amp, restore (5 beats)
  4 refresh        the pointer walks the rows, each rewritten within the window (3 beats)
  5 leakage        charge drains at each cell's own rate; the weakest sets the deadline (3 beats)
  6 numbers        6F^2 and 8F^2 cell areas; a 512 x 512 array (3 beats)
  7 shrinking      a smaller footprint; taller plates keep the charge (3 beats)
  8 makers         three wafer makers, one ticker per beat (3 beats)
  9 risks          refresh time, blocked access, RowHammer (3 beats)
 10 sources        four source cards lit in turn (4 beats)

One beat is SEC (8) seconds at 24 fps.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, box, disc, empty, key, label, pivot, rel, show, tube, cup  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start, stream_of  # noqa: E402
import cell_kit as K  # noqa: E402
from cell_kit import ZC, SRC_X, DRN_X, BL_Y, CAP_Y0, CAP_Y1, WL_Y, END  # noqa: E402


def begin(n, beats):
    m, root = start(f"sec{n}", beats, page="cell")
    K.mats(m)
    return m, root


def wrap(root, name, intervals):
    """A group switched on for `intervals` (its children keep their own keys)."""
    g = empty(name, root)
    show(g, intervals)
    return g


def cap_label(root, text, b, u0=0.0, u1=1.0):
    label(text, (SRC_X + 40, CAP_Y1 + 70, ZC), root, [(F(b, u0), F(b, u1))])


# ---- 1. what happens ----------------------------------------------------------------------


def sec1():
    m, root = begin(1, 3)
    single = wrap(root, "single", [(F(0, 0), F(2, 0))])
    parts = K.cell(single, m)
    scale_keys(parts["fill"], [(0, (1, 1, 1.0)), (F(1, 0), (1, 1, 1.0)), (F(1, 0.5), (1, 1, 0.02))])
    array = wrap(root, "array", [(F(2, 0), END)])
    cells = K.rows_of_cells(array, m, 3, 3, 520.0)
    for k, (g, pv) in enumerate(cells):
        scale_keys(pv, [(0, (1, 1.0 if k % 2 == 0 else 0.02, 1))])
    cap_label(root, "a full capacitor reads as 1", 0)
    cap_label(root, "an empty capacitor reads as 0", 1)
    label("every cell holds its own bit", (0, 900, 0), root, [(F(2, 0), END)])
    camera(root, [
        ((0.0, 500.0, ZC), 4600.0, 0.45, 0.16),
        ((0.0, 500.0, ZC), 4600.0, 0.45, 0.16),
        ((0.0, 300.0, 0.0), 4200.0, 0.50, 0.35),
    ])
    finish("sec1", page="cell")


# ---- 2. the parts -------------------------------------------------------------------------


def sec2():
    m, root = begin(2, 5)
    K.cell(root, m,
           lit_wl=[(F(0, 0), F(1, 0))],
           lit_bl=[(F(2, 0), F(3, 0))],
           lit_sa=[(F(3, 0), F(4, 0))],
           lit_pre=[(F(4, 0), F(5, 0))])
    label("word line: row select", (0, WL_Y + 190, ZC + 170), root, [(F(0, 0), F(1, 0))])
    label("access transistor", (-120, 60, ZC + 150), root, [(F(0, 0), F(1, 0))])
    cap_label(root, "storage capacitor: the bit", 1)
    label("bit line: the column wire", (DRN_X, BL_Y + 130, ZC), root, [(F(2, 0), F(3, 0))])
    label("sense amp: the latch", (-1340, BL_Y + 210, ZC), root, [(F(3, 0), F(4, 0))])
    label("precharge: back to the middle", (1150, BL_Y + 210, ZC), root, [(F(4, 0), F(5, 0))])
    camera(root, [
        ((-200.0, 300.0, -300.0), 3600.0, 0.60, 0.18),
        ((SRC_X, 500.0, ZC), 3400.0, 0.45, 0.16),
        ((DRN_X, 900.0, ZC), 4200.0, 0.30, 0.14),
        ((-1100.0, 900.0, ZC), 3600.0, 0.30, 0.14),
        ((1000.0, 900.0, ZC), 3600.0, 0.30, 0.14),
    ])
    finish("sec2", page="cell")


# ---- 3. one read, in order ----------------------------------------------------------------


def sec3():
    m, root = begin(3, 5)
    parts = K.cell(root, m,
                   lit_wl=[(F(1, 0), F(4, 0.7))],
                   lit_bl=[(F(2, 0), F(4, 0.9))],
                   lit_sa=[(F(3, 0), F(4, 0.9))],
                   lit_pre=[(F(0, 0), F(1, 0))])
    scale_keys(parts["bar"], [
        (0, (1, 1, 0.5)),
        (F(2, 0.60), (1, 1, 0.6)),
        (F(3, 0.60), (1, 1, 1.0)),
        (F(4, 0.90), (1, 1, 0.5)),
    ])
    scale_keys(parts["fill"], [
        (0, (1, 1, 1.0)),
        (F(2, 0.60), (1, 1, 0.85)),
        (F(4, 0.60), (1, 1, 1.0)),
    ])
    stream_of(root, "share", 6, (SRC_X, 600.0, ZC), K.PATH_CAP_TO_BL, 28, m["cyan_dot"], 2, 0.20, 0.60, 60)
    stream_of(root, "restore", 6, (DRN_X, BL_Y, ZC), K.PATH_BL_TO_CAP, 28, m["violet_dot"], 4, 0.10, 0.60, 60)
    label("precharge: the line sits at VDD/2", (1150, BL_Y + 210, ZC), root, [(F(0, 0), F(1, 0))])
    label("word line high: transistor on", (0, WL_Y + 190, ZC + 170), root, [(F(1, 0), F(2, 0))])
    label("charge sharing: a small move", (DRN_X, BL_Y + 130, ZC), root, [(F(2, 0), F(3, 0))])
    label("sense amp latches to a rail", (-1340, BL_Y + 210, ZC), root, [(F(3, 0), F(4, 0))])
    cap_label(root, "restore: the cell is full again", 4)
    camera(root, [
        ((0.0, 800.0, ZC), 5000.0, 0.45, 0.16),
        ((-200.0, 300.0, -300.0), 4000.0, 0.60, 0.18),
        ((0.0, 700.0, ZC), 4800.0, 0.45, 0.16),
        ((-900.0, 800.0, ZC), 4800.0, 0.45, 0.16),
        ((SRC_X, 600.0, ZC), 4200.0, 0.45, 0.16),
    ])
    finish("sec3", page="cell")


# ---- 4. refresh -----------------------------------------------------------------------------

ROWS = 8
PITCH = 420.0
Z_LO, Z_HI = -1470.0, 1470.0


def sweep_rows(root, m, t0, t1):
    """A row of cells with a pointer walking along z from t0 to t1, each row rewritten as it passes."""
    cells = K.rows_of_cells(root, m, 1, ROWS, PITCH)
    ptr = empty("pointer", root)
    box("pointer_m", (-330, 820, -22), (330, 850, 22), m["pointer"], ptr)
    key(ptr, t0, "location", P(0, 0, Z_LO), linear=True)
    key(ptr, t1, "location", P(0, 0, Z_HI), linear=True)
    for j, (g, pv) in enumerate(cells):
        z = (j - (ROWS - 1) / 2) * PITCH
        t_at = t0 + round((z - Z_LO) / (Z_HI - Z_LO) * (t1 - t0))
        scale_keys(pv, [(0, (1, 1, 0.85)), (t_at, (1, 1, 0.85)), (t_at + 34, (1, 1, 1.0)), (F(3, 0.95), (1, 1, 1.0))])
    return cells


def sec4():
    m, root = begin(4, 3)
    sweep_rows(root, m, F(0, 0), F(2, 0.9))
    label("a REF command every 7.8 us", (0, 900, -300), root, [(F(0, 0), F(1, 0))])
    label("each slice is read, rewritten", (0, 900, 150), root, [(F(1, 0), F(2, 0))])
    label("window closes, all rows done", (0, 900, 300), root, [(F(2, 0), F(3, 0))])
    camera(root, [
        ((0.0, 400.0, -900.0), 4200.0, 0.55, 0.22),
        ((0.0, 400.0, 0.0), 4400.0, 0.55, 0.22),
        ((0.0, 400.0, 700.0), 4200.0, 0.55, 0.22),
    ])
    finish("sec4", page="cell")


# ---- 5. leakage -----------------------------------------------------------------------------


def sec5():
    m, root = begin(5, 3)
    cells = K.rows_of_cells(root, m, 1, 3, 520.0)
    # rates: index 0 strong, 1 middle, 2 weakest; all refreshed to full at the start of beat 2
    levels = [
        [(0, 1.0), (F(1, 0.9), 0.90), (F(2, 0.5), 0.90), (F(2, 0.8), 1.0)],
        [(0, 1.0), (F(1, 0.9), 0.72), (F(2, 0.5), 0.72), (F(2, 0.8), 1.0)],
        [(0, 1.0), (F(1, 0.9), 0.50), (F(2, 0.5), 0.50), (F(2, 0.8), 1.0)],
    ]
    for (g, pv), keys in zip(cells, levels):
        scale_keys(pv, [(f, (1, 1, v)) for f, v in keys])
    label("charge drains from every cell", (0, 900, 0), root, [(F(0, 0), F(1, 0))])
    label("each cell drains at its own rate", (0, 900, 0), root, [(F(1, 0), F(2, 0))])
    label("refresh arrives just in time", (0, 900, 0), root, [(F(2, 0), F(3, 0))])
    camera(root, [
        ((0.0, 400.0, 0.0), 3400.0, 0.50, 0.14),
        ((0.0, 400.0, 0.0), 3400.0, 0.50, 0.14),
        ((0.0, 400.0, 0.0), 3400.0, 0.50, 0.14),
    ])
    finish("sec5", page="cell")


# ---- 6. numbers -----------------------------------------------------------------------------


def tiles(root, m, nx, nz, size, gap, mat_):
    """nx by nz tiles on the floor, centred on the origin."""
    g = empty("tiles", root)
    for i in range(nx):
        for j in range(nz):
            x = (i - (nx - 1) / 2) * (size + gap)
            z = (j - (nz - 1) / 2) * (size + gap)
            box(f"tile_{i}_{j}", (x - size / 2, 0, z - size / 2), (x + size / 2, 60, z + size / 2), mat_, g)
    return g


def sec6():
    m, root = begin(6, 3)
    t6 = tiles(wrap(root, "six", [(F(0, 0), F(1, 0))]), m, 3, 2, 260.0, 30.0, m["charge"])
    t8 = tiles(wrap(root, "eight", [(F(1, 0), F(2, 0))]), m, 4, 2, 260.0, 30.0, m["cyan_dot"])
    grid = wrap(root, "grid", [(F(2, 0), END)])
    tiles(grid, m, 16, 16, 30.0, 10.0, m["cap_out"])
    label("6F^2 with an open bit line", (0, 300, 300), root, [(F(0, 0), F(1, 0))])
    label("8F^2 with a folded bit line", (0, 300, 300), root, [(F(1, 0), F(2, 0))])
    label("512 x 512 cells in one array", (0, 300, 300), root, [(F(2, 0), END)])
    camera(root, [
        ((0.0, 0.0, 0.0), 2600.0, 0.25, 0.55),
        ((0.0, 0.0, 0.0), 2800.0, 0.25, 0.55),
        ((0.0, 0.0, 0.0), 6200.0, 0.25, 0.55),
    ])
    finish("sec6", page="cell")


# ---- 7. shrinking ---------------------------------------------------------------------------


def sec7():
    m, root = begin(7, 3)
    H = CAP_Y1 - CAP_Y0
    box("source_n", (-150, -60, -150), (150, 20, 150), m["n_plus"], root)
    tube("storage_node", (0, 0, 0), (0, CAP_Y0 + 10, 0), 60, m["plug"], root, verts=12)
    stack, _ = K.cap_stack(root, m, (0, CAP_Y0, 0), H, outer=True)
    scale_keys(stack, [
        (0, (1, 1, 1)),
        (F(1, 0.10), (1, 1, 1)),
        (F(1, 0.70), (0.5, 1, 0.5)),
        (F(2, 0.10), (0.5, 1, 0.5)),
        (F(2, 0.80), (0.5, 1.6, 0.5)),
    ])
    label("a wide cell: a big capacitor", (0, CAP_Y1 + 90, 260), root, [(F(0, 0), F(1, 0))])
    label("smaller F: less signal", (0, CAP_Y1 + 90, 260), root, [(F(1, 0), F(2, 0))])
    label("taller plates keep Cc up", (0, CAP_Y1 + 90, 260), root, [(F(2, 0), F(3, 0))])
    camera(root, [
        ((0.0, 600.0, 0.0), 3000.0, 0.40, 0.12),
        ((0.0, 600.0, 0.0), 3000.0, 0.40, 0.12),
        ((0.0, 700.0, 0.0), 3200.0, 0.40, 0.12),
    ])
    finish("sec7", page="cell")


# ---- 8. makers ------------------------------------------------------------------------------


def sec8():
    m, root = begin(8, 3)
    box("plinth_e", (-1500, 0, -600), (1500, 30, 600), m["plinth"], root)
    names = ["Micron (MU)", "SK hynix (000660.KS)", "Samsung (005930.KS)"]
    xs = [-950.0, 0.0, 950.0]
    for i, (x, name) in enumerate(zip(xs, names)):
        disc(f"wafer_{i}", (x, 60, 0), 400, 40, m["paper"], root, verts=72)
        glow = disc(f"wafer_glow_{i}", (x, 85, 0), 410, 10, m["gold_glow"], root, verts=72)
        show(glow, [(F(i, 0), END)])
        label(name, (x, 260, 380), root, [(F(i, 0), F(i + 1, 0))])
    camera(root, [
        ((-950.0, 60.0, 0.0), 3600.0, 0.05, 0.85),
        ((0.0, 60.0, 0.0), 3600.0, 0.05, 0.85),
        ((950.0, 60.0, 0.0), 3600.0, 0.05, 0.85),
    ])
    finish("sec8", page="cell")


# ---- 9. risks -------------------------------------------------------------------------------


def sec9():
    m, root = begin(9, 3)
    # beat 0: the refresh sweep on a meter of its time
    meter, bar = K.gauge(root, m)
    scale_keys(bar, [(0, (1, 1, 0.05)), (F(0, 0.9), (1, 1, 1.0)), (F(2, 0.9), (1, 1, 1.0))])
    rows_grp = wrap(root, "rows_s0", [(F(0, 0), F(1, 0))])
    sweep_rows(rows_grp, m, F(0, 0), F(0, 0.9))
    label("covering the weakest cells costs time", (0, 900, 0), root, [(F(0, 0), F(1, 0))])
    # beat 1: a gate closes the bank while a refresh runs; requests queue behind it
    gate = wrap(root, "gate", [(F(1, 0), F(2, 0))])
    box("gate_m", (-200, 0, -500), (200, 900, -460), m["red"], gate)
    stream_of(root, "requests", 6, (500.0, 300.0, -300.0), [(0, 0, 0), (-800, 0, 0)], 40, m["cyan_dot"], 1, 0.10, 0.80, 80)
    label("refresh blocks access while it runs", (-200, 1000, -480), root, [(F(1, 0), F(2, 0))])
    # beat 2: RowHammer: the row in the middle flickers, the neighbours lose charge
    hammer = K.rows_of_cells(wrap(root, "hammer", [(F(2, 0), END)]), m, 1, 3, 420.0)
    levels = [(1.0, 0.82), (1.0, 1.0), (1.0, 0.82)]
    for (g, pv), (a, b) in zip(hammer, levels):
        scale_keys(pv, [(F(2, 0), (1, 1, a)), (F(2, 0.9), (1, 1, b))])
    label("RowHammer: one row leaks into its neighbours", (0, 900, 0), root, [(F(2, 0), END)])
    camera(root, [
        ((0.0, 500.0, 0.0), 4800.0, 0.40, 0.20),
        ((0.0, 500.0, 0.0), 4400.0, 0.40, 0.20),
        ((0.0, 500.0, 0.0), 3600.0, 0.40, 0.20),
    ])
    finish("sec9", page="cell")


# ---- 10. sources ----------------------------------------------------------------------------


def sec10():
    m, root = begin(10, 4)
    box("plinth_s", (-1800, 0, -900), (1800, 30, 900), m["plinth"], root)
    cards = [
        ((-800.0, 0.0, -400.0), "Jacob, UMD ENEE 359a (slides)"),
        ((800.0, 0.0, -400.0), "Mutlu, arXiv 2306.16037"),
        ((-800.0, 0.0, 400.0), "HiRA, arXiv 2209.10198"),
        ((800.0, 0.0, 400.0), "PROTEAS, arXiv 2404.16256"),
    ]
    for i, (c, text) in enumerate(cards):
        x, _, z = c
        box(f"card{i}", (x - 600, 30, z - 380), (x + 600, 50, z + 380), m["paper"], root)
        lit = box(f"card{i}_lit", (x - 620, 50, z - 400), (x + 620, 60, z + 400), m["gold_glow"], root)
        show(lit, [(F(i, 0.1), END)])
        label(text, (x - 600, 70, z + 400), root, [(F(i, 0.1), F(i + 1, 0))])
    camera(root, [
        ((-800.0, 0.0, -400.0), 3200.0, 0.0, 0.95),
        ((800.0, 0.0, -400.0), 3200.0, 0.0, 0.95),
        ((-800.0, 0.0, 400.0), 3200.0, 0.0, 0.95),
        ((800.0, 0.0, 400.0), 3200.0, 0.0, 0.95),
    ])
    finish("sec10", page="cell")


SECTIONS = [sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9, sec10]

if __name__ == "__main__":
    which = [int(a) for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(range(1, 11))
    for n in which:
        SECTIONS[n - 1]()
