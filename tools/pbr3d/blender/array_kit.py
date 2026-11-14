"""The DRAM array as reusable Blender pieces for the ARRAY pictures (overview, zooms, sections).

A subarray is drawn as a grid of 1T1C cells in the plane z = -45, with word lines running along
rows (in front of the cells), bit lines running down columns into a row of sense amps, a column
decoder under them, a row decoder on the left and an I/O pad on the right. Everything is in
schematic millimetres (Y up, camera on +z). The subarray is 10 x 10 cells at a 100 mm pitch
unless a picture asks for another size; the page's 512 x 512 is a number to tag, not a drawing.

Static geometry is merged into one mesh per kind (`slabs`), so a scene carries a few dozen
objects rather than thousands. Animated things are groups switched with `show`, or one moving
highlight bar keyed along the rows.

Every builder takes `root` (an empty at the origin, so poly coordinates are absolute) and `m`
(the materials dict from `mats`).
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, beat, empty, key, label, mat, pivot, show  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start, stream_of  # noqa: E402

END = F(40, 0)  # "until the end" for intervals; later than any scene
PITCH = 100.0  # mm between cell centres
CELL = 44.0  # cell body size
ROW_Y = 0.0  # the first word line sits at y = 0
SA_Y = -120.0  # sense amp row (its top edge is -110, where the bit lines end)
SEL_Y = -185.0  # column decoder bar
PIN_BASE = -320.0  # I/O pad bottom


def cx(j, pitch=PITCH):
    return j * pitch


def cy(i, pitch=PITCH):
    return i * pitch


def mats(m):
    """Materials for the array, on top of the sand_overview set."""
    m["cap"] = mat("cell_cap", (0.30, 0.50, 0.60), metal=0.3, rough=0.4)
    m["cap_on"] = mat("cell_cap_on", (0.45, 0.85, 1.0), emit=(0.35, 0.8, 1.0), strength=2.2)
    m["tr"] = mat("cell_tr", (0.12, 0.12, 0.14), rough=0.5)
    m["wl"] = mat("word_line", (0.40, 0.24, 0.12), rough=0.5)
    m["wl_on"] = mat("word_line_on", (1.0, 0.52, 0.12), emit=(1.0, 0.45, 0.10), strength=3.0)
    m["bl"] = mat("bit_line", (0.36, 0.40, 0.46), metal=0.6, rough=0.4)
    m["bl_on"] = mat("bit_line_on", (0.35, 0.92, 1.0), emit=(0.30, 0.88, 1.0), strength=2.5)
    m["sa"] = mat("sense_amp", (0.50, 0.30, 0.72), metal=0.2, rough=0.4)
    m["sa_on"] = mat("sense_amp_on", (0.75, 0.50, 1.0), emit=(0.7, 0.45, 1.0), strength=2.0)
    m["latch1"] = mat("latch_one", (1.0, 0.55, 0.15), emit=(1.0, 0.50, 0.12), strength=3.0)
    m["latch0"] = mat("latch_zero", (0.11, 0.10, 0.11), rough=0.6)
    m["green"] = mat("read_green", (0.30, 1.0, 0.45), emit=(0.30, 1.0, 0.40), strength=3.0)
    m["pink"] = mat("pink_pre", (1.0, 0.35, 0.60), emit=(1.0, 0.30, 0.55), strength=3.0)
    m["decoder"] = mat("decoder", (0.42, 0.44, 0.48), metal=0.5, rough=0.5)
    m["io"] = mat("io_pad", (0.22, 0.24, 0.28), metal=0.6, rough=0.4)
    m["plate"] = mat("plate", (0.12, 0.13, 0.16), rough=0.9)
    m["probe"] = mat("probe", (1.0, 0.85, 0.20), emit=(1.0, 0.82, 0.18), strength=3.0)
    m["dot"] = mat("dot_white", (0.95, 0.95, 1.0), emit=(0.9, 0.9, 1.0), strength=2.0)
    m["fuse"] = mat("fuse", (0.95, 0.80, 0.30), metal=0.8, rough=0.3)
    m["fuse_dark"] = mat("fuse_blown", (0.15, 0.12, 0.10), rough=0.8)
    m["laser"] = mat("laser", (1.0, 0.25, 0.20), emit=(1.0, 0.2, 0.15), strength=6.0)
    m["spare"] = mat("spare_row", (0.30, 0.55, 0.36), rough=0.5)
    m["spare_on"] = mat("spare_row_on", (0.40, 1.0, 0.55), emit=(0.35, 1.0, 0.5), strength=2.5)
    m["dim"] = mat("dim_cell", (0.10, 0.14, 0.16), rough=0.7)
    m["red"] = mat("red_dead", (0.85, 0.12, 0.12), emit=(0.9, 0.1, 0.1), strength=2.0)
    m["gold"] = mat("gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["gold_glow"] = mat("gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["paper"] = mat("paper", (0.90, 0.88, 0.82), rough=0.85)
    m["grey"] = mat("grey", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    m["blue"] = mat("blue", (0.36, 0.56, 0.82), metal=0.2, rough=0.45)
    m["ghost"] = mat("ghost", (0.6, 0.75, 0.95), rough=0.2, alpha=0.18)
    return m


# ---- geometry -------------------------------------------------------------------------


def slabs(name, boxes, m, parent=None):
    """One mesh holding every box in `boxes` (each (lo, hi) in poly mm). Merged geometry: a
    single object, so the GLB stays small."""
    verts, faces = [], []
    for lo, hi in boxes:
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        base = len(verts)
        corners = [
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ]
        verts += [tuple(P(*c)) for c in corners]
        for q in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            faces.append(tuple(base + i for i in q))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    return o


def col_span(cols, pitch=PITCH):
    return (cols - 1) * pitch


def row_span(rows, pitch=PITCH):
    return (rows - 1) * pitch


def cells(root, m, rows, cols, pitch=PITCH, size=CELL, name="cells", mat_key="cap", parent=None):
    """The cell bodies, one 1T1C block each, in the plane z = -45. Returns the merged mesh."""
    h = size / 2
    boxes = []
    for i in range(rows):
        for j in range(cols):
            x, y = cx(j, pitch), cy(i, pitch)
            boxes.append(((x - h, y - h, -60.0), (x + h, y + h, -30.0)))
    return slabs(name, boxes, m[mat_key], parent or root)


def word_lines(root, m, rows, cols, pitch=PITCH, x_lo=-140.0, mat_key="wl", name="word_lines", parent=None):
    """The dim word line of every row, from the row decoder across the array."""
    boxes = []
    for i in range(rows):
        y = cy(i, pitch)
        boxes.append(((x_lo, y - 4, -14.0), (col_span(cols, pitch) + 40, y + 4, -6.0)))
    return slabs(name, boxes, m[mat_key], parent or root)


def bit_lines(root, m, rows, cols, pitch=PITCH, y_lo=SA_Y + 10, mat_key="bl", name="bit_lines", parent=None):
    """The bit line of every column, from its sense amp up past the top row."""
    boxes = []
    top = row_span(rows, pitch) + 40
    for j in range(cols):
        x = cx(j, pitch)
        boxes.append(((x - 3, y_lo, -22.0), (x + 3, top, -16.0)))
    return slabs(name, boxes, m[mat_key], parent or root)


def sense_amps(root, m, cols, pitch=PITCH, mat_key="sa", name="sense_amps", parent=None):
    """One sense amp per bit line: a purple block under each column."""
    boxes = []
    for j in range(cols):
        x = cx(j, pitch)
        boxes.append(((x - 22, SA_Y - 30, -40.0), (x + 22, SA_Y + 10, -20.0)))
    return slabs(name, boxes, m[mat_key], parent or root)


def latch_row(root, m, cols, bits, pitch=PITCH):
    """The row buffer: an orange latch for each 1 and a dark one for each 0 on the sense amp row.
    Returns (ones, zeros), two meshes to switch on and off."""
    ones, zeros = [], []
    for j in range(cols):
        x = cx(j, pitch)
        box = ((x - 26, SA_Y - 26, -20.0), (x + 26, SA_Y + 2, -8.0))
        (ones if bits[j % len(bits)] else zeros).append(box)
    a = slabs("latches_one", ones, m["latch1"], root) if ones else None
    b = slabs("latches_zero", zeros, m["latch0"], root) if zeros else None
    return a, b


def decoders(root, m, rows, cols, pitch=PITCH, name="row_decoder"):
    """The row decoder on the left (one driver per row) and the column decoder under the sense
    amps with the data line to the I/O pad on the right. Returns (row decoder, column decoder)."""
    top = row_span(rows, pitch) + 60
    rd = slabs(name, [((-200, -40, -50.0), (-130, top, -20.0))], m["decoder"], root)
    cd = slabs(
        "column_decoder",
        [((-20, SEL_Y - 16, -40.0), (col_span(cols, pitch) + 20, SEL_Y + 16, -20.0))],
        m["decoder"],
        root,
    )
    line = slabs("data_line", [((col_span(cols, pitch) + 20, SEL_Y - 6, -30.0), (col_span(cols, pitch) + 170, SEL_Y + 6, -22.0))], m["grey"], root)
    return rd, cd, line


def io_pad(root, m, cols, pitch=PITCH, name="io_pad"):
    """The I/O block at the right edge, where the burst leaves the chip."""
    x0 = col_span(cols, pitch) + 170
    return slabs(name, [((x0, PIN_BASE, -50.0), (x0 + 110, SEL_Y + 40, -20.0))], m["io"], root)


def row_bar(root, m, rows, cols, row0, pitch=PITCH, name="wl_on"):
    """A bright word line bar on row `row0`, on a mover (`hl`) that is keyed to other rows. The
    bar is built at its own row, so keying the mover by (cy(i) - cy(row0)) lands it on row i.
    Returns (mover, bar)."""
    hl = empty("row_mover", root)
    bar = slabs(
        name,
        [((-140.0, cy(row0, pitch) - 9, -16.0), (col_span(cols, pitch) + 40, cy(row0, pitch) + 9, -4.0))],
        m["wl_on"],
        hl,
    )
    return hl, bar


def move_row(hl, frames_rows, row0, pitch=PITCH):
    """Key the row mover through (frame, row) pairs, linearly."""
    for f, i in frames_rows:
        key(hl, f, "location", P(0, cy(i, pitch) - cy(row0, pitch), 0), linear=True)


def select(root, m, cols, pick, pitch=PITCH, name="col_sel"):
    """Green marks on the column decoder bar over the picked columns (switch on with `show`)."""
    boxes = [
        ((cx(j, pitch) - 15, SEL_Y - 13, -18.0), (cx(j, pitch) + 15, SEL_Y + 13, -8.0)) for j in pick
    ]
    return slabs(name, boxes, m["green"], root)


def bright_bit_lines(root, m, rows, cols, pitch=PITCH):
    """The same bit lines drawn bright (switch on while a row is sensed)."""
    return bit_lines(root, m, rows, cols, pitch, mat_key="bl_on", name="bit_lines_on", parent=root)


def bright_cells(root, m, rows, cols, pick, pitch=PITCH, name="cells_on"):
    """Bright cell bodies for the cells of row `pick` (a list of row indices), switched on together."""
    h = CELL / 2
    boxes = []
    for i in pick:
        for j in range(cols):
            x, y = cx(j, pitch), cy(i, pitch)
            boxes.append(((x - h - 2, y - h - 2, -62.0), (x + h + 2, y + h + 2, -28.0)))
    return slabs(name, boxes, m["cap_on"], root)


def flow(root, name, pts, n, size, m, b, u0, u1, life, parent=None):
    """`n` blobs that travel the polyline `pts` (absolute poly points), launched between fractions
    u0 and u1 of beat b, each taking `life` frames."""
    x0, y0, z0 = pts[0]
    offs = [(x - x0, y - y0, z - z0) for x, y, z in pts]
    return stream_of(parent or root, name, n, pts[0], offs, size, m, b, u0, u1, life)


def tags_for(root, items, at_parent=None):
    """Tags: items is a list of (text, (x, y, z), intervals)."""
    for text, at, iv in items:
        label(text, at, at_parent or root, iv)


def on(obj, intervals):
    """Switch `obj` on for `intervals`, a thin wrapper that tolerates None (an unbuilt piece)."""
    if obj is not None:
        show(obj, intervals)


def wave(root, name, x, ys, m, b, u0, life):
    """A short vertical wave of dots: one blob per y, launched in turn (used for pin bursts)."""
    g = empty(name, root)
    for k, y in enumerate(ys):
        flow(g, f"{name}_{k}", [(x, y, -10.0), (x, y - 120.0, -10.0)], 1, 9, m, b, u0 + 0.05 * k, u0 + 0.05 * k + 0.02, life)
    return g


def lane(root, m, row, x0, segs, y, b, u0, u1, label_text=None):
    """A timing lane: coloured bars laid end to end from x0, one per (mat_key, ns, text) in segs,
    each drawn at 20 mm per ns and switched on for beat b (fractions u0..u1)."""
    g = empty(f"lane{row}", root)
    x = x0
    for k, (mk, ns, text) in enumerate(segs):
        w = ns * 20.0
        bar = slabs(f"lane{row}_{k}", [((x, y - 16, -20.0), (x + w, y + 16, -10.0))], m[mk], g)
        show(bar, [(F(b, u0), F(b, u1))] if u1 is not None else [(F(b, u0), END)])
        if text:
            label(text, (x + w / 2, y + 60, -10.0), g, [(F(b, u0), END)])
        x += w
    return g


def camera_for(root, poses):
    """Thin wrapper over the sand_zooms camera."""
    camera(root, poses)


__all__ = [
    "END", "PITCH", "CELL", "SA_Y", "SEL_Y", "OFF", "F", "P", "beat", "ball", "empty", "key",
    "label", "pivot", "show", "scale_keys", "start", "finish", "camera", "stream_of",
    "mats", "slabs", "cells", "word_lines", "bit_lines", "sense_amps", "latch_row", "decoders",
    "io_pad", "row_bar", "move_row", "select", "bright_bit_lines", "bright_cells", "flow",
    "tags_for", "on", "wave", "lane", "cx", "cy", "col_span", "row_span", "math",
]
