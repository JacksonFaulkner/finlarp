"""The ten ARRAY write-up sections, each a 3D picture authored in Blender and exported for pbr3d in
the picture-and-panel template (docs/diagram-pages.md). The kit is in array_kit.py; the timing
lanes come from array_zooms.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/array_sections.py [-- 3 5]

For each section it writes blender/array_sec<N>.blend and assets/array_sec<N>.glb.

  1 what happens   a grid of cells; ACTIVATE opens a row; the sense amps latch it; READ picks columns (four beats)
  2 parts          cells; the row decoder and word line; bit lines and sense amps; column decoder and I/O (four beats)
  3 one access     idle, ACTIVATE, sense, READ, PRECHARGE (five beats)
  4 hits, misses   row hit, row miss, row conflict as timing lanes (three beats)
  5 mats           a short bit line, a long one, a cut by a stripe, mats in a subarray and bank (four beats)
  6 numbers        the 512 x 512 array, one 1 KB row, 8 transfers on 8 pins, the DDR4-3200 timings (four beats)
  7 repair         a bad cell found at test, a fuse blown by laser, the spare row (three beats)
  8 makers         Micron, SK hynix, Samsung (three beats)
  9 risks          row conflicts, RowHammer, the periphery, refresh (four beats)
 10 sources        six source cards in four groups (four beats)

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/array/sections.rs).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import array_kit as K  # noqa: E402
import array_zooms as Z  # noqa: E402
from array_kit import END, F, P, beat, cx, cy, empty, flow, label, select, show, slabs  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402

ROWS = COLS = 10
R0 = 6  # the row that opens
BITS = [1, 0, 1, 1, 0, 0, 1, 0, 1, 0]
SEL_A = [1, 3, 4, 8]
SEL_B = [0, 2, 5, 6]
IO_X = K.col_span(COLS) + 225


def begin(n, beats):
    m, root = start(f"sec{n}", beats, page="array")
    K.mats(m)
    return m, root


def base(root, m, rows=ROWS, cols=COLS, r0=R0, bits=BITS):
    """The static array plus every overlay a section might switch on (unused overlays stay off)."""
    K.cells(root, m, rows, cols)
    K.word_lines(root, m, rows, cols)
    K.bit_lines(root, m, rows, cols)
    K.sense_amps(root, m, cols)
    K.decoders(root, m, rows, cols)
    K.io_pad(root, m, cols)
    d = {}
    d["ones"], d["zeros"] = K.latch_row(root, m, cols, bits)
    d["blon"] = K.bright_bit_lines(root, m, rows, cols)
    d["cells_on"] = K.bright_cells(root, m, rows, cols, [r0])
    d["hl"], d["bar"] = K.row_bar(root, m, rows, cols, r0)
    d["selA"] = select(root, m, cols, SEL_A, name="col_selA")
    d["selB"] = select(root, m, cols, SEL_B, name="col_selB")
    return d


def act_flows(root, m, b):
    for j in range(COLS):
        flow(root, f"act{b}_{j}", [(cx(j), cy(R0), -34.0), (cx(j), K.SA_Y + 40, -18.0)], 1, 9, m["bl_on"], b, 0.1, 0.5, 60)


def read_flows(root, m, b, pick, tag):
    for j in pick:
        flow(root, f"rd{tag}{j}", [(cx(j), K.SA_Y + 2, -12.0), (cx(j), K.SEL_Y, -12.0), (IO_X, K.SEL_Y, -12.0), (IO_X, -230.0, -12.0)], 1, 10, m["green"], b, 0.1, 0.5, 60)


def addr_flows(root, m, b):
    flow(root, "addr", [(-430.0, cy(R0), -30.0), (-205.0, cy(R0), -30.0)], 3, 14, m["dot"], b, 0.2, 0.5, 60)


OVERVIEW_POSES = ((370.0, 360.0, 0.0), 2750.0, 0.10, 0.10)
SENSE_POSES = ((450.0, 60.0, 0.0), 2450.0, 0.06, 0.06)


# ---- 1. what happens --------------------------------------------------------------------


def sec1():
    m, root = begin(1, 4)
    d = base(root, m)
    show(d["bar"], beat(1) + beat(2) + beat(3))
    show(d["cells_on"], beat(1))
    show(d["blon"], [(F(1, 0.0), F(3, 0.0))])
    show(d["ones"], [(F(2, 0.0), END)])
    show(d["zeros"], [(F(2, 0.0), END)])
    show(d["selA"], beat(3))
    act_flows(root, m, 1)
    read_flows(root, m, 3, SEL_A, "A")
    label("a grid of 1T1C cells", (cx(4), cy(ROWS - 1) + 120, 0), root, beat(0))
    label("ACTIVATE: one word line opens", (-300, cy(R0) + 70, 0), root, beat(1))
    label("sense amps latch the row", (cx(9) + 120, K.SA_Y - 40, 0), root, beat(2))
    label("READ picks columns to the I/O", (IO_X + 40, -360, 0), root, beat(3))
    camera(root, [OVERVIEW_POSES, OVERVIEW_POSES, SENSE_POSES, SENSE_POSES])
    finish("sec1", page="array")


# ---- 2. parts ---------------------------------------------------------------------------


def sec2():
    m, root = begin(2, 4)
    d = base(root, m)
    show(K.bright_cells(root, m, ROWS, COLS, list(range(ROWS)), name="all_cells_on"), beat(0))
    show(d["bar"], beat(1))
    show(d["blon"], beat(2))
    show(d["ones"], beat(2))
    show(d["zeros"], beat(2))
    show(d["selA"], beat(3))
    read_flows(root, m, 3, SEL_A, "A")
    label("cell: 1 transistor, 1 capacitor", (cx(COLS - 1) + 90, cy(4), 0), root, beat(0))
    label("row decoder: one word line high", (-300, cy(R0) + 70, 0), root, beat(1))
    label("bit lines and sense amps", (cx(COLS - 1) + 120, K.SA_Y - 40, 0), root, beat(2))
    label("column decoder: picks columns", (-20, K.SEL_Y - 50, 0), root, beat(3))
    label("I/O: a burst off the chip", (IO_X + 40, -360, 0), root, beat(3))
    camera(root, [OVERVIEW_POSES, OVERVIEW_POSES, SENSE_POSES, SENSE_POSES])
    finish("sec2", page="array")


# ---- 3. one access, in order -----------------------------------------------------------


def sec3():
    m, root = begin(3, 5)
    d = base(root, m)
    addr_flows(root, m, 0)
    show(d["bar"], [(F(1, 0.0), F(4, 0.0))])
    show(d["cells_on"], beat(1))
    show(d["blon"], [(F(1, 0.5), F(4, 0.0))])
    show(d["ones"], [(F(2, 0.0), F(4, 0.0))])
    show(d["zeros"], [(F(2, 0.0), F(4, 0.0))])
    show(d["selA"], beat(3))
    act_flows(root, m, 1)
    read_flows(root, m, 3, SEL_A, "A")
    label("1. idle: bit lines at VDD/2", (cx(4), K.SA_Y - 60, 0), root, beat(0))
    label("2. ACT: the word line rises", (-300, cy(R0) + 70, 0), root, beat(1))
    label("3. sense: the row is latched", (cx(COLS - 1) + 120, K.SA_Y - 40, 0), root, beat(2))
    label("4. READ: columns to the I/O", (IO_X + 40, -360, 0), root, beat(3))
    label("5. PRE: the row closes", (cx(2), cy(R0) + 150, 0), root, beat(4))
    camera(root, [OVERVIEW_POSES, OVERVIEW_POSES, SENSE_POSES, SENSE_POSES, OVERVIEW_POSES])
    finish("sec3", page="array")


# ---- 4. hits and misses -----------------------------------------------------------------


def sec4():
    m, root = begin(4, 3)
    Z.make_lane(root, m, "hit", 300.0, [("green", 13.75)], "hit: tCL = 13.75 ns", beat(0))
    Z.make_lane(root, m, "miss", 120.0, [("wl_on", 13.75), ("green", 13.75)], "miss: tRCD+tCL = 27.5 ns", beat(1))
    Z.make_lane(root, m, "conflict", -60.0, [("pink", 13.75), ("wl_on", 13.75), ("green", 13.75)], "conflict: tRP+tRCD+tCL = 41.25 ns", beat(2))
    pose = ((150.0, 120.0, 0.0), 1900.0, 0.0, 0.0)
    camera(root, [pose, pose, pose])
    finish("sec4", page="array")


# ---- 5. mats and subarrays --------------------------------------------------------------


def seg(g, m, x, y0, n, name):
    """A bit line of n cells from y0 up, with its sense amp at the foot and a swing bar beside it."""
    slabs(name + "_cells", [((x - 22, y0 + 60 * k - 22, -60.0), (x + 22, y0 + 60 * k + 22, -30.0)) for k in range(1, n + 1)], m["cap"], g)
    slabs(name + "_bl", [((x - 3, y0 - 10.0, -22.0), (x + 3, y0 + 60 * n + 30.0, -16.0))], m["bl"], g)
    slabs(name + "_sa", [((x - 22, y0 - 40.0, -40.0), (x + 22, y0 - 10.0, -20.0))], m["sa"], g)


def swing_bar(g, m, x, y0, h, name):
    slabs(name, [((x + 60, y0, -12.0), (x + 84, y0 + h, -6.0))], m["bl_on"], g)


def sec5():
    m, root = begin(5, 4)
    # beat 0: a short line (four cells) with a strong swing
    ga = empty("short", root)
    seg(ga, m, 0.0, 0.0, 4, "short")
    swing_bar(ga, m, 0.0, 0.0, 280.0, "short_swing")
    show(ga, beat(0))
    # beat 1: a line twice as long (eight cells) with half the swing
    gb = empty("long", root)
    seg(gb, m, 400.0, 0.0, 8, "long")
    swing_bar(gb, m, 400.0, 0.0, 140.0, "long_swing")
    show(gb, beat(1))
    # beat 2: the same long line cut by a sense amp stripe in the middle
    gc = empty("cut", root)
    seg(gc, m, 800.0, 0.0, 4, "cut_lo")
    seg(gc, m, 800.0, 340.0, 4, "cut_hi")
    swing_bar(gc, m, 800.0, 0.0, 280.0, "cut_swing_lo")
    swing_bar(gc, m, 800.0, 340.0, 280.0, "cut_swing_hi")
    show(gc, beat(2))
    # beat 3: mats in a subarray under a global word line, and a bank
    g3 = empty("bank", root)
    for k, ox in enumerate([0.0, 520.0, 1040.0]):
        gm = empty(f"bank_mat{k}", g3, P(ox, 0, 0))
        K.cells(gm, m, 4, 4, name=f"bank{k}_cells")
        K.word_lines(gm, m, 4, 4, name=f"bank{k}_wl")
        K.bit_lines(gm, m, 4, 4, name=f"bank{k}_bl")
        K.sense_amps(gm, m, 4, name=f"bank{k}_sa")
    gwl = slabs("bank_wl_on", [((-180.0, cy(1) - 9.0, -16.0), (1040.0 + K.col_span(4) + 60.0, cy(1) + 9.0, -4.0))], m["wl_on"], root)
    show(gwl, beat(3))
    gbl = slabs("bank_bl_on", [((-180.0, -215.0, -22.0), (1040.0 + K.col_span(4) + 60.0, -200.0, -16.0))], m["bl_on"], root)
    show(gbl, beat(3))
    show(g3, beat(3))

    label("short bit line: strong swing", (120.0, 150.0, 0.0), root, beat(0))
    label("long bit line: half the swing", (520.0, 150.0, 0.0), root, beat(1))
    label("a sense amp stripe cuts it", (900.0, 330.0, 0.0), root, beat(2))
    label("mats form a subarray and bank", (585.0, -260.0, 0.0), root, beat(3))
    camera(root, [
        ((200.0, 150.0, 0.0), 1100.0, 0.10, 0.06),
        ((400.0, 150.0, 0.0), 1400.0, 0.08, 0.06),
        ((800.0, 220.0, 0.0), 1500.0, 0.06, 0.06),
        ((585.0, 150.0, 0.0), 3400.0, 0.04, 0.08),
    ])
    finish("sec5", page="array")


# ---- 6. by the numbers ------------------------------------------------------------------


def sec6():
    m, root = begin(6, 4)
    # beat 0: the typical array
    g0 = empty("array", root)
    K.cells(g0, m, ROWS, COLS, name="array_cells")
    K.word_lines(g0, m, ROWS, COLS, name="array_wl")
    K.bit_lines(g0, m, ROWS, COLS, name="array_bl")
    K.sense_amps(g0, m, COLS, name="array_sa")
    show(g0, beat(0))
    label("512 word lines x 512 bit lines", (cx(4), cy(ROWS - 1) + 120, 0), root, beat(0))
    # beat 1: one row across 16 arrays: 1 KB, 8192 bits
    g1 = empty("row", root)
    boxes = [((110.0 * k, 0.0, -60.0), (110.0 * k + 90.0, 90.0, -30.0)) for k in range(16)]
    slabs("row_arrays", boxes, m["cap"], g1)
    slabs("row_line", [((-40.0, 40.0, -14.0), (110.0 * 15 + 130.0, 52.0, -6.0))], m["wl_on"], g1)
    show(g1, beat(1))
    label("one row: 8192 bits across 16 arrays", (110.0 * 7, 160.0, 0.0), root, beat(1))
    # beat 2: eight transfers on eight pins
    g2 = empty("pins", root)
    for k in range(8):
        px = 90.0 * k
        slabs(f"pin{k}", [((px - 4, -200.0, -20.0), (px + 4, 200.0, -12.0))], m["bl"], g2)
    show(g2, beat(2))
    for k in range(8):
        px = 90.0 * k
        flow(root, f"xfer{k}", [(px, 200.0, -12.0), (px, -200.0, -12.0)], 1, 8, m["green"], 2, 0.1 + 0.07 * k, 0.12 + 0.07 * k, 36)
    label("burst: 8 transfers on 8 pins", (360.0, -250.0, 0.0), root, beat(2))
    # beat 3: the timings, to scale
    Z.make_lane(root, m, "trcd", 300.0, [("wl_on", 13.75)], "tRCD = 13.75 ns", beat(3))
    Z.make_lane(root, m, "tcl", 120.0, [("green", 13.75)], "tCL = 13.75 ns", beat(3))
    Z.make_lane(root, m, "trp", -60.0, [("pink", 13.75)], "tRP = 13.75 ns", beat(3))
    Z.make_lane(root, m, "tras", -240.0, [("grey", 32.5)], "tRAS = 32.5 ns", beat(3))
    pose_grid = ((370.0, 360.0, 0.0), 2750.0, 0.10, 0.10)
    pose_row = ((870.0, 60.0, 0.0), 3000.0, 0.0, 0.05)
    pose_burst = ((240.0, 0.0, 0.0), 1000.0, 0.0, 0.05)
    pose_time = ((200.0, 0.0, 0.0), 1800.0, 0.0, 0.0)
    camera(root, [pose_grid, pose_row, pose_burst, pose_time])
    finish("sec6", page="array")


# ---- 7. repair --------------------------------------------------------------------------


def sec7():
    m, root = begin(7, 3)
    rows = cols = 6
    K.cells(root, m, rows, cols)
    K.word_lines(root, m, rows, cols)
    K.bit_lines(root, m, rows, cols)
    K.sense_amps(root, m, cols)
    K.decoders(root, m, rows, cols)

    spare_y = cy(rows - 1) + 100.0
    spare = slabs("spare_row", [((-40.0, spare_y - 10.0, -60.0), (K.col_span(cols) + 40.0, spare_y + 10.0, -28.0))], m["spare"], root)
    show(spare, [(F(0, 0.0), END)])
    spare_on = slabs("spare_row_on", [((-40.0, spare_y - 10.0, -62.0), (K.col_span(cols) + 40.0, spare_y + 10.0, -26.0))], m["spare_on"], root)
    show(spare_on, beat(2))

    dead = slabs("dead_cell", [((cx(3) - 26, cy(2) - 26, -64.0), (cx(3) + 26, cy(2) + 26, -26.0))], m["red"], root)
    show(dead, [(F(0, 0.0), F(2, 0.5))])

    hl = empty("probe_mover", root)
    probe = slabs("probe_bar", [((-120.0, -9.0, -16.0), (K.col_span(cols) + 40.0, 9.0, -4.0))], m["probe"], hl)
    show(probe, beat(0))
    K.move_row(hl, [(F(0, 0.05 + 0.15 * i), i) for i in range(rows)], 0)

    fx = 640.0
    fuses = [((fx + 28 * k, 760.0, -30.0), (fx + 28 * k + 14, 790.0, -20.0)) for k in range(6)]
    show(slabs("fuses_intact", fuses, m["fuse"], root), [(F(0, 0.0), F(1, 0.3))])
    show(slabs("fuses_blown", fuses, m["fuse_dark"], root), [(F(1, 0.3), END)])
    show(slabs("laser", [((fx + 52, 800.0, -34.0), (fx + 68, 960.0, -26.0))], m["laser"], root), [(F(1, 0.0), F(1, 0.45))])

    flow(root, "remap", [(-160.0, cy(2), -30.0), (-160.0, spare_y, -30.0), (cx(4), spare_y, -30.0)], 3, 12, m["dot"], 2, 0.1, 0.6, 60)

    label("wafer test finds a bad cell", (cx(3) + 90, cy(2) + 60, 0), root, beat(0))
    label("a laser blows the fuse", (fx - 120, 900.0, 0), root, beat(1))
    label("decoder sends it to a spare", (cx(1), spare_y + 60, 0), root, beat(2))
    pose = ((330.0, 330.0, 0.0), 2300.0, 0.05, 0.08)
    camera(root, [pose, pose, pose])
    finish("sec7", page="array")


# ---- 8. makers --------------------------------------------------------------------------


def card(root, m, x, y, text, b, lit_from=None):
    """A paper card at (x, y) with a gold strip that lights from beat `b` on, and its tag."""
    g = empty(f"card_{text[:6]}", root)
    slabs("paper", [((x - 650, y - 300, -40.0), (x + 650, y + 300, -30.0))], m["paper"], g)
    strip = slabs("lit", [((x - 600, y + 230, -28.0), (x + 600, y + 270, -24.0))], m["gold_glow"], g)
    show(strip, [(F(b, 0.0 if lit_from is None else lit_from), END)])
    label(text, (x - 620, y + 340, 0.0), root, [(F(b, 0.0), END)])
    return g


def sec8():
    m, root = begin(8, 3)
    names = ["Micron (MU)", "SK hynix (000660.KS)", "Samsung (005930.KS)"]
    xs = [-1500.0, 0.0, 1500.0]
    for b, (text, x) in enumerate(zip(names, xs)):
        card(root, m, x, 0.0, text, b, lit_from=0.15)
    pose = ((0.0, 0.0, 0.0), 9000.0, 0.0, 0.0)
    camera(root, [pose, pose, pose])
    finish("sec8", page="array")


# ---- 9. risks ---------------------------------------------------------------------------


def sec9():
    m, root = begin(9, 4)
    rows = cols = 6
    # beat 0: a row conflict costs three times a row hit
    Z.make_lane(root, m, "hit9", 200.0, [("green", 13.75)], "hit: 13.75 ns", beat(0))
    Z.make_lane(root, m, "conflict9", -100.0, [("pink", 13.75), ("wl_on", 13.75), ("green", 13.75)], "conflict: 41.25 ns", beat(0))
    # beats 1 to 3 use a small array
    g = empty("array9", root)
    K.cells(g, m, rows, cols, name="cells9")
    K.word_lines(g, m, rows, cols, name="wl9")
    K.bit_lines(g, m, rows, cols, name="bl9")
    K.sense_amps(g, m, cols, name="sa9")
    K.decoders(g, m, rows, cols, name="rd9")
    show(g, [(F(1, 0.0), END)])
    # beat 1: RowHammer: the neighbours of the hammered row leak
    hl, bar = K.row_bar(root, m, rows, cols, 3)
    show(bar, [(F(1, 0.0), F(1, 0.2)), (F(1, 0.4), F(1, 0.6)), (F(1, 0.8), F(2, 0.0))])
    neigh = [((cx(j) - 26, cy(i) - 26, -64.0), (cx(j) + 26, cy(i) + 26, -26.0)) for i in (2, 4) for j in range(cols)]
    show(slabs("neighbours_red", neigh, m["red"], root), beat(1))
    label("RowHammer: neighbours leak", (cx(cols - 1) + 90, cy(4), 0), root, beat(1))
    # beat 2: the periphery: decoders and sense amp stripes take area around the cells
    show(K.sense_amps(root, m, cols, mat_key="sa_on", name="sa_on9"), beat(2))
    label("periphery takes area from cells", (cx(cols - 1) + 120, K.SA_Y - 60, 0), root, beat(2))
    # beat 3: refresh walks every row, one at a time
    hl3, bar3 = K.row_bar(root, m, rows, cols, 0)
    show(bar3, beat(3))
    K.move_row(hl3, [(F(3, 0.02 + 0.095 * i), i) for i in range(rows)], 0)
    label("refresh opens rows in turn", (cx(cols - 1) + 90, cy(rows - 1), 0), root, beat(3))
    pose = ((380.0, 300.0, 0.0), 2100.0, 0.06, 0.08)
    pose_t = ((150.0, 150.0, 0.0), 1900.0, 0.0, 0.0)
    camera(root, [pose_t, pose, pose, pose])
    finish("sec9", page="array")


# ---- 10. sources ------------------------------------------------------------------------


SOURCES = [
    ("[1] UMD ENEE 359a: DRAM circuits, Jacob", 0),
    ("[2] Kim et al., SALP, arXiv 1805.01966", 0),
    ("[3] AnandTech: DDR5 sub-timings", 1),
    ("[4] geizhals: DDR4 CL22-22-22-52 listing", 1),
    ("[5] US 6,731,550; US 5,325,334 (redundancy)", 2),
    ("[6] Kim et al., RowHammer, ISCA 2014", 3),
]


def sec10():
    m, root = begin(10, 4)
    pos = [(-1500.0, 600.0), (0.0, 600.0), (1500.0, 600.0), (-1500.0, -500.0), (0.0, -500.0), (1500.0, -500.0)]
    for (text, b), (x, y) in zip(SOURCES, pos):
        card(root, m, x, y, text, b, lit_from=0.15)
    pose = ((0.0, 150.0, 0.0), 7200.0, 0.0, 0.0)
    camera(root, [pose, pose, pose, pose])
    finish("sec10", page="array")


BUILDS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9, 10: sec10}

if __name__ == "__main__":
    which = [int(n) for n in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(BUILDS)
    for n in which:
        BUILDS[n]()
