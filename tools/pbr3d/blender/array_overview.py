"""The ARRAY overview, authored in Blender and exported for pbr3d, in the picture-and-panel template
(docs/diagram-pages.md). A 10 x 10 subarray of 1T1C cells, drawn schematically: one access walks
through it, with `label:<text>` tags pinned by the TUI while they are switched on. The kit is in
array_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/array_overview.py

It writes:
  blender/array_overview.blend   open it in Blender to edit by hand
  assets/array_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/array/overview.rs).

Beats (match the ARRAY overview page):
  0 address   an address reaches the row decoder, which picks one row
  1 activate  one word line rises; every cell in the row shares its charge with its bit line
  2 sense     the sense amps latch the row: the row buffer
  3 read      the column decoder sends a burst of four columns to the I/O
  4 row hit   a second READ to the open row skips the activate
  5 precharge the word line falls and the bit lines return to VDD/2
  6 refresh   every row is opened and closed in turn
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import array_kit as K  # noqa: E402
from array_kit import END, F, beat, cx, cy, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402

BEATS = 7
ROWS = COLS = 10
R0 = 6  # the row that opens
BITS = [1, 0, 1, 1, 0, 0, 1, 0, 1, 0]  # the row's bits, left to right
SEL_A = [1, 3, 4, 8]  # columns of the first READ
SEL_B = [0, 2, 5, 6]  # columns of the row hit

POSES = [
    ((370.0, 360.0, 0.0), 2750.0, 0.10, 0.10),
    ((370.0, 360.0, 0.0), 2650.0, 0.12, 0.10),
    ((450.0, 60.0, 0.0), 2450.0, 0.08, 0.06),
    ((450.0, 60.0, 0.0), 2450.0, 0.02, 0.06),
    ((450.0, 60.0, 0.0), 2450.0, -0.04, 0.06),
    ((370.0, 360.0, 0.0), 2650.0, 0.12, 0.10),
    ((370.0, 360.0, 0.0), 2750.0, 0.10, 0.10),
]


def build():
    m, root = start("overview", BEATS, page="array")
    K.mats(m)

    K.cells(root, m, ROWS, COLS)
    K.word_lines(root, m, ROWS, COLS)
    K.bit_lines(root, m, ROWS, COLS)
    K.sense_amps(root, m, COLS)
    K.decoders(root, m, ROWS, COLS)
    K.io_pad(root, m, COLS)

    # the row buffer: latches on the sense amps, lit once the row is sensed
    ones, zeros = K.latch_row(root, m, COLS, BITS)
    show(ones, [(F(2, 0.0), F(5, 0.0))])
    show(zeros, [(F(2, 0.0), F(5, 0.0))])

    # bit lines swing from the precharge level to full rails while the row is open
    bl_on = K.bright_bit_lines(root, m, ROWS, COLS)
    show(bl_on, [(F(1, 0.0), F(5, 0.0))])

    # cells of the open row share charge with their bit lines
    cells_on = K.bright_cells(root, m, ROWS, COLS, [R0])
    show(cells_on, beat(1))

    # the word line of the open row, a bright bar that moves for refresh
    hl, bar = K.row_bar(root, m, ROWS, COLS, R0)
    show(bar, [(F(1, 0.0), F(5, 0.25))] + beat(6))
    K.move_row(hl, [(F(6, 0.02 + 0.095 * i), i) for i in range(ROWS)], R0)

    selA = K.select(root, m, COLS, SEL_A)
    show(selA, beat(3))
    selB = K.select(root, m, COLS, SEL_B)
    show(selB, beat(4))

    # address bits flow into the row decoder
    K.flow(root, "addr", [(-430.0, cy(R0), -30.0), (-205.0, cy(R0), -30.0)], 3, 14, m["dot"], 0, 0.2, 0.5, 60)
    # ACTIVATE: each cell of the row nudges its bit line
    for j in range(COLS):
        K.flow(root, f"act{j}", [(cx(j), cy(R0), -34.0), (cx(j), K.SA_Y + 40, -18.0)], 1, 9, m["bl_on"], 1, 0.1, 0.5, 60)
    # READ: columns from the latches to the I/O pad, twice (the second is a row hit)
    io_x = K.col_span(COLS) + 225
    for j in SEL_A:
        K.flow(root, f"rdA{j}", [(cx(j), K.SA_Y + 2, -12.0), (cx(j), K.SEL_Y, -12.0), (io_x, K.SEL_Y, -12.0), (io_x, -230.0, -12.0)], 1, 10, m["green"], 3, 0.1, 0.5, 60)
    for j in SEL_B:
        K.flow(root, f"rdB{j}", [(cx(j), K.SA_Y + 2, -12.0), (cx(j), K.SEL_Y, -12.0), (io_x, K.SEL_Y, -12.0), (io_x, -230.0, -12.0)], 1, 10, m["green"], 4, 0.1, 0.5, 60)

    # tags: two to four per beat, each switched on for the beat it explains
    label("row decoder: one row", (-300, cy(R0) + 80, 0), root, beat(0))
    label("bit lines held at VDD/2", (cx(4), K.SA_Y - 60, 0), root, beat(0))
    label("word line: one row opens", (-300, cy(R0) + 70, 0), root, beat(1))
    label("cells share charge with bit lines", (cx(8) + 80, cy(R0) + 60, 0), root, beat(1))
    label("sense amps: the row buffer", (cx(9) + 120, K.SA_Y - 40, 0), root, beat(2))
    label("column decoder: 4 columns", (-20, K.SEL_Y - 50, 0), root, beat(3))
    label("I/O: a burst of 8 transfers", (io_x + 40, -360, 0), root, beat(3))
    label("row hit: no activate needed", (cx(8) + 50, K.SEL_Y - 50, 0), root, beat(4))
    label("precharge: bit lines to VDD/2", (cx(2), cy(R0) + 150, 0), root, beat(5))
    label("refresh: every row in turn", (cx(8) + 40, cy(R0) + 150, 0), root, beat(6))

    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="array")
