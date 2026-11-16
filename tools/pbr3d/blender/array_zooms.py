"""The ARRAY zoom-ins, authored in Blender and exported for pbr3d, in the overview's style (see
array_overview.py and array_kit.py). Each zoom is four beats, one picture per zoom key:

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/array_zooms.py

For each zoom it writes:
  blender/array_<name>.blend   open it in Blender to edit by hand
  assets/array_<name>.glb      what pbr3d embeds and plays back

  a rowbuf   a whole row in the sense amps: ACTIVATE, latch, READ from the latches, precharge
  b hits     row hit, row miss and row conflict as timing lanes, then all three to scale
  c mats     one mat, a subarray under a global word line, a bank with shared bit lines,
             one subarray's row open
  d redund   a bad cell found at test, a laser blows its fuse, the decoder sends the address to a
             spare row, and the bad row is no longer used
  e burst    a column address picks 8 latches, 8 transfers on 8 pins, the next READ to the open
             row, then the whole open row serves its READs

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/array/zoom.rs).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import array_kit as K  # noqa: E402
from array_kit import END, PITCH, F, P, beat, cx, cy, empty, flow, label, mat, select, show, slabs  # noqa: E402
from sand_overview import tube  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402

BEATS = 4


def group_at(root, name, ox):
    """An empty at x = ox, for a copy of a piece built at the origin. Tags stay on the root."""
    return empty(name, root, P(ox, 0, 0))


def make_lane(root, m, name, y, segs, text, intervals, x0=-320.0):
    """A timing lane: bars laid end to end at 20 mm per ns, shown for `intervals`."""
    g = empty(name, root)
    x = x0
    for k, (mk, ns) in enumerate(segs):
        w = ns * 20.0
        slabs(f"{name}_{k}", [((x, y - 18.0, -20.0), (x + w, y + 18.0, -10.0))], m[mk], g)
        x += w
    show(g, intervals)
    label(text, (x + 30.0, y, 0.0), root, intervals)
    return g


# ---- a: the row buffer ----------------------------------------------------------------


def rowbuf():
    m, root = start("rowbuf", BEATS, page="array")
    K.mats(m)
    rows, cols, r0 = 6, 8, 3
    bits = [1, 0, 1, 1, 0, 0, 1, 0]
    K.cells(root, m, rows, cols)
    K.word_lines(root, m, rows, cols)
    K.bit_lines(root, m, rows, cols)
    K.sense_amps(root, m, cols)
    K.decoders(root, m, rows, cols)
    K.io_pad(root, m, cols)

    hl, bar = K.row_bar(root, m, rows, cols, r0)
    show(bar, [(F(0, 0.0), F(3, 0.3))])
    show(K.bright_cells(root, m, rows, cols, [r0], name="cells_on"), beat(0))
    show(K.bright_bit_lines(root, m, rows, cols), [(F(0, 0.5), F(3, 0.3))])

    ones, zeros = K.latch_row(root, m, cols, bits)
    show(ones, [(F(1, 0.0), F(3, 0.3))])
    show(zeros, [(F(1, 0.0), F(3, 0.3))])

    for j in range(cols):
        flow(root, f"act{j}", [(cx(j), cy(r0), -34.0), (cx(j), K.SA_Y + 40, -18.0)], 1, 9, m["bl_on"], 0, 0.1, 0.5, 60)

    selA = select(root, m, cols, [1, 3, 4, 6], name="col_sel")
    show(selA, beat(2))
    io_x = K.col_span(cols) + 225
    for j in [1, 3, 4, 6]:
        flow(root, f"rd{j}", [(cx(j), K.SA_Y + 2, -12.0), (cx(j), K.SEL_Y, -12.0), (io_x, K.SEL_Y, -12.0), (io_x, -230.0, -12.0)], 1, 10, m["green"], 2, 0.1, 0.5, 60)

    label("ACTIVATE raises one word line", (cx(7) + 70, cy(r0) + 70, 0), root, beat(0))
    label("sense amps latch each bit", (cx(cols - 1) + 120, K.SA_Y - 40, 0), root, beat(1))
    label("READ: latches feed the I/O", (cx(2), K.SEL_Y - 130, 0), root, beat(2))
    label("precharge empties the row buffer", (cx(2), cy(r0) + 150, 0), root, beat(3))

    camera(root, [
        ((380.0, 120.0, 0.0), 2350.0, 0.08, 0.08),
        ((380.0, 100.0, 0.0), 2300.0, 0.05, 0.07),
        ((380.0, 80.0, 0.0), 2300.0, 0.02, 0.07),
        ((380.0, 60.0, 0.0), 2350.0, 0.0, 0.07),
    ])
    finish("rowbuf", page="array")


# ---- b: row hit, row miss, row conflict -------------------------------------------------


def hits():
    m, root = start("hits", BEATS, page="array")
    K.mats(m)
    make_lane(root, m, "hit", 300.0, [("green", 13.75)], "hit: tCL = 13.75 ns", beat(0) + beat(3))
    make_lane(root, m, "miss", 120.0, [("wl_on", 13.75), ("green", 13.75)], "miss: tRCD+tCL = 27.5 ns", beat(1) + beat(3))
    make_lane(root, m, "conflict", -60.0, [("pink", 13.75), ("wl_on", 13.75), ("green", 13.75)], "conflict: tRP+tRCD+tCL = 41.25 ns", beat(2) + beat(3))
    camera(root, [
        ((150.0, 120.0, 0.0), 1900.0, 0.0, 0.0),
        ((150.0, 120.0, 0.0), 1900.0, 0.0, 0.0),
        ((150.0, 120.0, 0.0), 1900.0, 0.0, 0.0),
        ((150.0, 120.0, 0.0), 1900.0, 0.0, 0.0),
    ])
    finish("hits", page="array")


# ---- c: mats, subarrays and the bank ---------------------------------------------------


def mats_zoom():
    m, root = start("mats", BEATS, page="array")
    K.mats(m)
    rows = cols = 4
    offs = [0.0, 520.0, 1040.0]
    groups = []
    for k, ox in enumerate(offs):
        g = group_at(root, f"mat{k}", ox)
        K.cells(g, m, rows, cols, name=f"mat{k}_cells")
        K.word_lines(g, m, rows, cols, name=f"mat{k}_wl")
        K.bit_lines(g, m, rows, cols, name=f"mat{k}_bl")
        K.sense_amps(g, m, cols, name=f"mat{k}_sa")
        slabs(f"mat{k}_drv", [((-200.0, -40.0, -50.0), (-150.0, cy(rows - 1) + 60.0, -20.0))], m["decoder"], g)
        groups.append(g)
    # beat 0 shows one mat; beats 1 to 3 the subarray; beat 2 and 3 add the bank's shared lines
    show(groups[1], [(F(1, 0.0), END)])
    show(groups[2], [(F(2, 0.0), END)])
    gwl = slabs("global_wl", [((-180.0, cy(1) - 9.0, -16.0), (offs[2] + K.col_span(cols) + 60.0, cy(1) + 9.0, -4.0))], m["wl_on"], root)
    show(gwl, [(F(1, 0.0), END)])
    gbl = slabs("global_bl", [((-180.0, -215.0, -22.0), (offs[2] + K.col_span(cols) + 60.0, -200.0, -16.0))], m["bl_on"], root)
    show(gbl, [(F(2, 0.0), END)])
    show(K.bright_cells(groups[0], m, rows, cols, [1], name="open_row0"), beat(3))
    show(K.bright_cells(groups[1], m, rows, cols, [1], name="open_row1"), beat(3))

    label("one mat: local drivers, sense amp stripe", (-40.0, K.SA_Y - 150, 0), root, beat(0))
    label("a subarray: mats under one global word line", (offs[1], cy(rows - 1) + 150, 0), root, beat(1))
    label("a bank: subarrays share global bit lines", (offs[1], -260, 0), root, beat(2))
    label("one subarray's row is open", (offs[0], cy(rows - 1) + 150, 0), root, beat(3))

    camera(root, [
        ((60.0, 20.0, 0.0), 1500.0, 0.08, 0.06),
        ((570.0, 80.0, 0.0), 2900.0, 0.05, 0.06),
        ((570.0, 60.0, 0.0), 2900.0, 0.02, 0.06),
        ((570.0, 60.0, 0.0), 2900.0, -0.02, 0.06),
    ])
    finish("mats", page="array")


# ---- d: redundancy ---------------------------------------------------------------------


def redundancy():
    m, root = start("redund", BEATS, page="array")
    K.mats(m)
    rows, cols = 6, 6
    K.cells(root, m, rows, cols)
    K.word_lines(root, m, rows, cols)
    K.bit_lines(root, m, rows, cols)
    K.sense_amps(root, m, cols)
    K.decoders(root, m, rows, cols)

    # the spare row sits past the top edge of the array
    spare_y = cy(rows - 1) + 100.0
    spare = slabs("spare_row", [((-40.0, spare_y - 10.0, -60.0), (K.col_span(cols) + 40.0, spare_y + 10.0, -28.0))], m["spare"], root)
    spare_on = slabs("spare_row_on", [((-40.0, spare_y - 10.0, -62.0), (K.col_span(cols) + 40.0, spare_y + 10.0, -26.0))], m["spare_on"], root)
    show(spare_on, [(F(2, 0.0), END)])

    # a bad cell at row 2, column 3
    dead = slabs("dead_cell", [((cx(3) - 26, cy(2) - 26, -64.0), (cx(3) + 26, cy(2) + 26, -26.0))], m["red"], root)
    show(dead, [(F(0, 0.0), F(3, 0.5))])

    # wafer test: a probe bar walks the rows during beat 0
    hl = empty("probe_mover", root)
    probe = slabs("probe_bar", [((-120.0, -9.0, -16.0), (K.col_span(cols) + 40.0, 9.0, -4.0))], m["probe"], hl)
    show(probe, beat(0))
    K.move_row(hl, [(F(0, 0.05 + 0.15 * i), i) for i in range(rows)], 0)

    # the fuse bank at the top right, and the laser that blows the bad address's fuse
    fx = 640.0
    fuses = [((fx + 28 * k, 760.0, -30.0), (fx + 28 * k + 14, 790.0, -20.0)) for k in range(6)]
    show(slabs("fuses_intact", fuses, m["fuse"], root), [(F(0, 0.0), F(1, 0.3))])
    show(slabs("fuses_blown", fuses, m["fuse_dark"], root), [(F(1, 0.3), END)])
    show(slabs("laser", [((fx + 52, 800.0, -34.0), (fx + 68, 960.0, -26.0))], m["laser"], root), [(F(1, 0.0), F(1, 0.45))])

    # the decoder sends the bad row's address up and across to the spare row
    flow(root, "remap", [(-160.0, cy(2), -30.0), (-160.0, spare_y, -30.0), (cx(4), spare_y, -30.0)], 3, 12, m["dot"], 2, 0.1, 0.6, 60)

    label("wafer test finds a bad cell", (cx(3) + 90, cy(2) + 60, 0), root, beat(0))
    label("a laser blows the fuse", (fx - 120, 900.0, 0), root, beat(1))
    label("decoder sends it to a spare", (cx(1), spare_y + 60, 0), root, beat(2))
    label("the bad row is no longer used", (cx(3) + 90, cy(2) + 60, 0), root, beat(3))

    camera(root, [
        ((330.0, 330.0, 0.0), 2400.0, 0.08, 0.08),
        ((640.0, 780.0, 0.0), 1100.0, 0.05, 0.06),
        ((330.0, 330.0, 0.0), 2300.0, 0.0, 0.08),
        ((330.0, 330.0, 0.0), 2300.0, -0.04, 0.08),
    ])
    finish("redund", page="array")


# ---- e: a burst -------------------------------------------------------------------------


def burst():
    m, root = start("burst", BEATS, page="array")
    K.mats(m)
    cols = 16
    bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0]
    K.bit_lines(root, m, 1, cols)
    K.sense_amps(root, m, cols)
    K.decoders(root, m, 1, cols)
    io = K.io_pad(root, m, cols)
    ones, zeros = K.latch_row(root, m, cols, bits)
    show(ones, [(F(0, 0.0), END)])
    show(zeros, [(F(0, 0.0), END)])

    io_x = K.col_span(cols) + 225
    pin_x = K.col_span(cols) + 170 + 130
    # the first and second READ pick eight columns each
    selA = select(root, m, cols, list(range(0, 8)), name="col_selA")
    selB = select(root, m, cols, list(range(8, 16)), name="col_selB")
    show(selA, [(F(0, 0.0), F(2, 0.0))])
    show(selB, [(F(2, 0.0), END)])
    for j in range(0, 8):
        flow(root, f"a{j}", [(cx(j), K.SA_Y + 2, -12.0), (cx(j), K.SEL_Y, -12.0), (io_x, K.SEL_Y, -12.0), (io_x, -230.0, -12.0)], 1, 10, m["green"], 1, 0.1, 0.5, 40)
    for j in range(8, 16):
        flow(root, f"b{j}", [(cx(j), K.SA_Y + 2, -12.0), (cx(j), K.SEL_Y, -12.0), (io_x, K.SEL_Y, -12.0), (io_x, -230.0, -12.0)], 1, 10, m["green"], 2, 0.1, 0.5, 40)

    # eight pins, each sending one transfer of the burst
    for k in range(8):
        px = pin_x + 14 * k
        slabs(f"pin{k}", [((px - 4, -330.0, -20.0), (px + 4, -200.0, -12.0))], m["bl"], root)
        flow(root, f"pin_dot{k}", [(px, -200.0, -12.0), (px, -330.0, -12.0)], 1, 7, m["green"], 1, 0.1 + 0.08 * k, 0.12 + 0.08 * k, 36)

    label("column address picks 64 bits", (cx(3), K.SEL_Y - 70, 0), root, beat(0))
    label("8 transfers on 8 pins", (pin_x - 40, -380, 0), root, beat(1))
    label("next READ: 64 more, no ACT", (cx(11), K.SEL_Y - 70, 0), root, beat(2))
    label("one open row serves many READs", (cx(7), K.SA_Y - 70, 0), root, beat(3))

    camera(root, [
        ((930.0, -110.0, 0.0), 3500.0, 0.05, 0.06),
        ((1640.0, -200.0, 0.0), 1250.0, 0.03, 0.05),
        ((930.0, -110.0, 0.0), 3500.0, 0.0, 0.06),
        ((930.0, -110.0, 0.0), 3500.0, -0.03, 0.06),
    ])
    finish("burst", page="array")


if __name__ == "__main__":
    rowbuf()
    hits()
    mats_zoom()
    redundancy()
    burst()
