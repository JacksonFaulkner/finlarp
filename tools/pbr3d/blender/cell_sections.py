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
    label(text, K.CAP_TAG, root, [(F(b, u0), F(b, u1))])


# ---- 1. what happens ----------------------------------------------------------------------


def sec1():
    m, root = begin(1, 3)
    single = wrap(root, "single", [(F(0, 0), F(2, 0))])
    parts = K.cell(single, m)
    scale_keys(parts["fill"], [(0, (1, 1, 1.0)), (F(1, 0), (1, 1, 1.0)), (F(1, 0.5), (1, 1, 0.02))])
    array = wrap(root, "array", [(F(2, 0), END)])
    cells = K.rows_of_cells(array, m, 3, 3, 520.0)
    for k, (g, pv) in enumerate(cells):
        scale_keys(pv, [(0, (1, 1, 1.0 if k % 2 == 0 else 0.02))])
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
    stream_of(root, "share", 6, K.SHARE_START, K.PATH_CAP_TO_BL, 28, m["cyan_dot"], 2, 0.20, 0.60, 60)
    stream_of(root, "restore", 6, K.RESTORE_START, K.PATH_BL_TO_CAP, 28, m["violet_dot"], 4, 0.10, 0.60, 60)
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
    box("pointer_m", (-200, 820, -110), (200, 850, 110), m["pointer"], ptr)
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
        ((0.0, 420.0, 0.0), 5200.0, 1.25, 0.24),
        ((0.0, 420.0, 0.0), 5000.0, 1.25, 0.24),
        ((0.0, 420.0, 0.0), 5200.0, 1.25, 0.24),
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
        ((0.0, 400.0, 0.0), 2900.0, 1.20, 0.16),
        ((0.0, 400.0, 0.0), 2900.0, 1.20, 0.16),
        ((0.0, 400.0, 0.0), 2900.0, 1.20, 0.16),
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
    tiles(grid, m, 16, 16, 30.0, 10.0, m["n_plus"])
    label("6F^2 with an open bit line", (0, 300, 300), root, [(F(0, 0), F(1, 0))])
    label("8F^2 with a folded bit line", (0, 300, 300), root, [(F(1, 0), F(2, 0))])
    label("512 x 512 cells in one array", (0, 70, 330), root, [(F(2, 0), END)])
    camera(root, [
        ((0.0, 0.0, 0.0), 2600.0, 0.25, 0.55),
        ((0.0, 0.0, 0.0), 2800.0, 0.25, 0.55),
        ((0.0, 0.0, 0.0), 1700.0, 0.25, 0.55),
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
    meter, bar = K.gauge(wrap(root, "meter_s0", [(F(0, 0), F(1, 0))]), m)
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
        ((0.0, 420.0, 0.0), 2700.0, 1.20, 0.18),
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
        box(f"card{i}", (x - 600, 30, z - 380), (x + 600, 50, z + 380), m["grey"], root)
        lit = box(f"card{i}_lit", (x - 620, 50, z - 400), (x + 620, 60, z + 400), m["gold_glow"], root)
        K.switch(lit, [(F(i, 0.1), END)])
        label(text, (x - 600, 70, z + 400), root, [(F(i, 0.1), F(i + 1, 0))])
    camera(root, [
        ((-800.0, 0.0, -400.0), 3200.0, 0.0, 0.95),
        ((800.0, 0.0, -400.0), 3200.0, 0.0, 0.95),
        ((-800.0, 0.0, 400.0), 3200.0, 0.0, 0.95),
        ((800.0, 0.0, 400.0), 3200.0, 0.0, 0.95),
    ])
    finish("sec10", page="cell")


# ==== detailed rebuild (cell_detail.py on rnd_3d_dram_kit.planar_cell) =========================

import rnd_3d_dram_kit as R  # noqa: E402
import cell_detail as D  # noqa: E402
from rnd_3d_dram_kit import on  # noqa: E402


def dbegin(n, beats):
    m, root = start(f"sec{n}", beats, page="cell")
    R.mats(m)
    D.mats(m)
    return m, root


def dfinish(n):
    R.finish(f"sec{n}", page="cell")


def b(i, u0=0.0, u1=1.0):
    return [(F(i, u0), F(i, u1))]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


# The rig's camera targets: the cell at the origin, the sense amp at SA_X.
CELL_T = (-60.0, 300.0, 0.0)
CAP_T = (45.0, 1250.0, 0.0)
SA_T = (D.SA_X, 700.0, 0.0)
WIDE_T = (-600.0, 800.0, 0.0)


def sec2_d():
    """The parts: one beat per row of the parts table."""
    m, root = dbegin(2, 6)
    r = D.read_rig(root, m)
    c = r.cell
    on(c.wl_on, b(0) + b(1))
    on(c.chan_on, b(1))
    on(r.charge, span(2, 0.0, 6, 0.0))
    on(c.bl_on, b(3))
    on(r.bl_bar_on, b(5))
    on(r.sa_on, b(4))
    on(r.eq_on, b(5))
    label("word line: buried in a trench, runs into the page", c.pts["wl"], root, b(0))
    label("nitride cap insulates it from above", (c.pts["wl"][0], -40.0, 0.0), root, b(0))
    label("gate oxide: the thin insulator", (-170.0, -300.0, 0.0), root, b(1))
    label("channel: a U round the trench bottom", c.pts["chan"], root, b(1))
    label("drain n+: to the bit line", c.pts["drain"], root, b(1))
    label("source n+: to the capacitor", c.pts["source"], root, b(1))
    label("TiN / high-k / TiN cylinder: the bit", c.pts["cap"], root, b(2))
    label("storage-node contact + landing pad", c.pts["snc"], root, b(2))
    label("bit line: the column wire, behind", r.pts["bl_mid"], root, b(3))
    label("bit-line contact down to the drain", c.pts["blc"], root, b(3))
    label("sense amp: two cross-coupled inverters", r.pts["sa"], root, b(4))
    label("BL on one side", r.pts["g_bl"], root, b(4))
    label("BL-bar: the twin line, the reference", r.pts["blb"], root, b(5))
    label("equaliser holds both at VDD/2", r.pts["eq"], root, b(5))
    camera(root, [
        (CELL_T, 2300.0, 0.35, 0.10),
        ((-100.0, -150.0, 0.0), 1500.0, 0.20, 0.06),
        (CAP_T, 4000.0, 0.40, 0.10),
        ((-700.0, 500.0, 0.0), 3600.0, 0.45, 0.25),
        (SA_T, 2400.0, 0.30, 0.10),
        ((-1500.0, 600.0, 0.0), 3400.0, 0.35, 0.15),
    ])
    dfinish(2)


def sec3_d():
    """One read: precharge, word line, charge sharing, sense, restore."""
    m, root = dbegin(3, 5)
    r = D.read_rig(root, m)
    c = r.cell
    on(r.eq_on, b(0) + b(4, 0.75))
    on(c.wl_on, span(1, 0.0, 4, 0.7))
    on(c.chan_on, span(1, 0.3, 4, 0.7))
    on(c.bl_on, span(2, 0.2, 4, 0.75))
    on(r.sa_on, span(3, 0.15, 4, 0.75))
    on(r.charge, span(0, 0.0, 2, 0.45) + span(4, 0.55, 5, 0.0))
    D.gauge_keys(r.g_bl, [(0, 0.5), (F(2, 0.2), 0.5), (F(2, 0.6), 0.56), (F(3, 0.15), 0.56), (F(3, 0.5), 1.0),
                          (F(4, 0.75), 1.0), (F(4, 0.95), 0.5)])
    D.gauge_keys(r.g_blb, [(0, 0.5), (F(3, 0.15), 0.5), (F(3, 0.5), 0.0), (F(4, 0.75), 0.0), (F(4, 0.95), 0.5)])
    R.beads(root, m, "share", r.share, 8, 2, 0.15, 0.45, life=60, size=30.0)
    R.beads(root, m, "restore", r.restore, 8, 4, 0.10, 0.40, life=60, size=30.0, mk="lk_sub")
    label("precharge: BL and BL-bar both at VDD/2", r.pts["eq"], root, b(0))
    label("both gauges on the VDD/2 line", r.pts["half"], root, b(0))
    label("word line high: the U channel opens", c.pts["chan"], root, b(1))
    label("cell charge spills onto the bit line", c.pts["cap"], root, b(2))
    label("BL rises a little: about +60 mV", r.pts["g_bl"], root, b(2))
    label("sense amp compares BL with BL-bar", r.pts["sa"], root, b(3))
    label("and slams them apart: BL to VDD, BL-bar to 0", r.pts["g_blb"], root, b(3))
    label("restore: full VDD flows back into the cell", c.pts["cap"], root, b(4))
    camera(root, [
        (SA_T, 2600.0, 0.30, 0.10),
        ((-100.0, -150.0, 0.0), 1500.0, 0.20, 0.06),
        (WIDE_T, 3600.0, 0.25, 0.10),
        (SA_T, 2400.0, 0.25, 0.08),
        (WIDE_T, 3600.0, 0.25, 0.10),
    ])
    dfinish(3)


def sec1_d():
    """A bit is charge: full reads 1, empty reads 0, then a field of cells, each its own bit."""
    m, root = dbegin(1, 3)
    one = wrap(root, "one", span(0, 0.0, 2, 0.0))
    c = R.planar_cell(one, m, (0.0, 0.0, 0.0), "c1", cutp=True, tile=False)
    sw, lv = D.q_strips(one, m, (0.0, 0.0, 0.0), "q1")
    on(sw, span(0, 0.0, 2, 0.0))
    D.level_keys(lv, [(0, 1.0), (F(1, 0.0), 1.0), (F(1, 0.4), 0.02)])
    fld = wrap(root, "fld", span(2, 0.0, 3, 0.0))
    a = D.field(fld, m, (0.0, 0.0, 0.0), 4, 3, name="f1")
    for i in range(4):
        o = (a.cells[(i, 0)].pts["cap_top"][0] - R.PL_SN_X, 0.0, 0.0)
        qs, ql = D.q_strips(fld, m, o, f"fq{i}")
        if i % 2 == 0:
            on(qs, b(2))
    label("full capacitor: a 1", c.pts["cap"], root, b(0))
    label("one transistor + one capacitor = 1T1C", c.pts["wl"], root, b(0))
    label("charge drains out: now it reads 0", c.pts["cap"], root, b(1))
    label("a field of cells: 1 0 1 0", a.cells[(0, 0)].pts["cap"], root, b(2))
    label("nitride lattice props the tall caps", (a.cells[(3, 0)].pts["cap_top"][0] + 150, R.PL_CAP0 + R.PL_CAP_H * 0.9, 0.0), root, b(2))
    camera(root, [
        ((0.0, 900.0, 0.0), 4400.0, 0.45, 0.12),
        ((0.0, 900.0, 0.0), 4400.0, 0.45, 0.12),
        ((0.0, 1100.0, -200.0), 4600.0, 0.50, 0.22),
    ])
    dfinish(1)


def sec5_d():
    """Leakage: the four exits from the storage node, then cells draining at their own rates."""
    m, root = dbegin(5, 5)
    one = wrap(root, "one", span(0, 0.0, 4, 0.0))
    c = R.planar_cell(one, m, (0.0, 0.0, 0.0), "c5", cutp=True, tile=False)
    sw, lv = D.q_strips(one, m, (0.0, 0.0, 0.0), "q5")
    on(sw, span(0, 0.0, 4, 0.0))
    D.level_keys(lv, [(0, 1.0), (F(3, 0.95), 0.55)])
    lp = D.leak_paths(c)
    for kind in ("sub", "jn", "gidl", "diel"):
        D.leak(root, m, lp, kind, 4, 0, 0.1, 0.8)
    D.leak(root, m, lp, "sub", 10, 1, 0.05, 0.85, size=20.0)
    D.leak(root, m, lp, "jn", 8, 2, 0.05, 0.85, size=20.0)
    D.leak(root, m, lp, "gidl", 8, 2, 0.05, 0.85, size=20.0)
    D.leak(root, m, lp, "diel", 8, 3, 0.05, 0.85, size=20.0)
    label("charge leaks out four ways", c.pts["cap"], root, b(0))
    label("subthreshold: the off transistor still trickles", c.pts["chan"], root, b(1))
    label("out the drain to the bit line", c.pts["drain"], root, b(1))
    label("junction: n+ source into the p substrate", (30.0, -330.0, 0.0), root, b(2))
    label("GIDL: strong field at the gate edge", (-200.0, -150.0, 0.0), root, b(2))
    label("hotter chip, faster leaks", c.pts["si"], root, b(2))
    label("through the thin high-k dielectric", lp["diel"][-1], root, b(3))
    rows = wrap(root, "rows", b(4))
    a = R.planar_array(rows, m, (0.0, 0.0, 0.0), 3, 1, name="r5", tile_at=None)
    rates = [0.85, 0.62, 0.30]
    for i, v in enumerate(rates):
        o = (a.cells[(i, 0)].pts["cap_top"][0] - R.PL_SN_X, 0.0, 0.0)
        qs, ql = D.q_strips(rows, m, o, f"rq{i}")
        on(qs, b(4))
        D.level_keys(ql, [(F(4, 0.0), 1.0), (F(4, 0.7), v), (F(4, 0.8), v), (F(4, 0.95), 1.0)])
    label("every cell leaks at its own rate", a.cells[(0, 0)].pts["cap"], root, b(4, 0.0, 0.5))
    label("the weakest sets the 64 ms refresh", a.cells[(2, 0)].pts["cap"], root, b(4, 0.3, 0.8))
    label("refresh: all back to full", a.cells[(1, 0)].pts["cap_top"], root, b(4, 0.8, 1.0))
    camera(root, [
        ((0.0, 500.0, 0.0), 3600.0, 0.30, 0.10),
        ((-100.0, -150.0, 0.0), 1500.0, 0.20, 0.06),
        ((-60.0, -250.0, 0.0), 1600.0, 0.20, 0.06),
        ((100.0, 1300.0, 0.0), 1800.0, 0.30, 0.08),
        ((0.0, 900.0, 0.0), 4200.0, 0.20, 0.10),
    ])
    dfinish(5)


X6, XV, XS = 0.0, 2600.0, 6000.0


def sec7_d():
    """Shrinking: 6F2 today, a thinner cap must grow taller, 4F2 vertical transistor, 3D DRAM."""
    m, root = dbegin(7, 4)
    g6 = wrap(root, "g6", span(0, 0.0, 2, 0.0))
    c = R.planar_cell(g6, m, (X6, 0.0, 0.0), "c7", cutp=True, tile=True)
    show(c.tile, b(0))
    scale_keys(c.cap, [(0, (1, 1, 1)), (F(1, 0.15), (1, 1, 1)), (F(1, 0.7), (0.6, 0.6, 1.45))])
    gv = wrap(root, "gv", b(2))
    v = R.vct_cell(gv, m, (XV, 0.0, 0.0), "v7", cutp=True, tile=True)
    on(v.wl_on, b(2, 0.3, 1.0))
    on(v.chan_on, b(2, 0.3, 1.0))
    gs = wrap(root, "gs", b(3))
    st = R.stacked_3d(gs, m, (XS, 0.0, 0.0), n=5, nz=2, name="s7")
    for k, lg in enumerate(st.wl_on):
        on(lg, b(3, 0.2 + 0.12 * k, 1.0))
    label("6F2 today: 3F x 2F footprint", c.pts["tile"], root, b(0))
    label("cap must hold ~10 fF, so it stands tall", c.pts["cap"], root, b(0))
    label("thinner cap, same charge: grow taller", c.pts["cap"], root, b(1))
    label("real ratio ~40:1; they lean and touch", c.pts["cap_top"], root, b(1))
    label("4F2: the transistor stands up", v.pts["tile"], root, b(2))
    label("vertical channel pillar", v.pts["pillar"], root, b(2))
    label("gate wraps the pillar", v.pts["gate"], root, b(2))
    label("buried bit line underneath", v.pts["bl"], root, b(2))
    label("3D DRAM: caps lie sideways, layers stack", st.pts["cap"], root, b(3))
    label("bit line runs up through the layers", st.pts["bl"], root, b(3))
    label("one word line per layer", st.pts["wl"], root, b(3))
    camera(root, [
        ((X6, 1100.0, 0.0), 4000.0, 0.40, 0.14),
        ((X6, 1300.0, 0.0), 4600.0, 0.40, 0.14),
        ((XV, 1000.0, 0.0), 4000.0, 0.45, 0.16),
        ((XS, 700.0, -200.0), 4400.0, 0.45, 0.18),
    ])
    dfinish(7)


SECTIONS = [sec1_d, sec2_d, sec3_d, sec4, sec5_d, sec6, sec7_d, sec8, sec9, sec10]

if __name__ == "__main__":
    which = [int(a) for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(range(1, 11))
    for n in which:
        SECTIONS[n - 1]()
