"""Shared helpers for the MATH node pages (math_pages.py): dots, bars, arrows, tiles, slides.

The pages use the SAND kit (sand_overview for geometry and keys, sand_zooms for start, camera and
finish), so the timing and units match the other picture-and-panel pages: 8 s beats at 24 fps, the
TUI samples the GLB at t = (beat + local) * 8, millimetres, Y up (see P).

Positions passed to these helpers are poly points (x, y, z) in millimetres. Groups are built at the
world origin with their children at absolute positions, so a group's location is an offset and its
scale pivots on the origin; that is what lets a bar grow from its floor and a group slide.
"""

import bpy
from mathutils import Vector
from sand_overview import OFF, P, ball, box, empty, key, label, mat, show, tube, F, beat, _name  # noqa: F401
from sand_zooms import camera, finish, start  # noqa: F401

BEAD_R = 70.0
BEAD_STEP = 190.0  # centre to centre along a row of beads
TILE = 230.0  # a matrix cell's side
TILE_T = 70.0  # a matrix cell's thickness (z)
TILE_PITCH = 300.0


def mats():
    """The math materials, on top of the SAND set that `start` made."""
    return {
        "red": mat("math_red", (0.86, 0.22, 0.18), rough=0.35),
        "blue": mat("math_blue", (0.20, 0.46, 0.92), rough=0.35),
        "grey": mat("math_grey", (0.62, 0.64, 0.70), rough=0.35),
        "gold": mat("math_gold", (0.95, 0.72, 0.25), rough=0.4),
        "lit": mat("math_lit", (1.0, 0.80, 0.30), emit=(1.0, 0.72, 0.22), strength=3.0, rough=0.3),
        "cyan": mat("math_cyan", (0.35, 0.90, 1.0), emit=(0.30, 0.85, 1.0), strength=2.5, rough=0.3),
        "green": mat("math_green", (0.30, 0.85, 0.45), emit=(0.25, 0.8, 0.4), strength=2.0, rough=0.3),
        "tile": mat("math_tile", (0.28, 0.32, 0.40), metal=0.2, rough=0.5),
        "tray": mat("math_tray", (0.20, 0.22, 0.26), metal=0.3, rough=0.6),
        "ink": mat("math_ink", (0.90, 0.90, 0.94), rough=0.5),
        "ghost": mat("math_ghost", (0.70, 0.72, 0.80), rough=0.6, alpha=0.30),
    }


# ---- primitives ------------------------------------------------------------------------


def dot(name, c, m, parent=None, r=BEAD_R):
    return ball(name, c, r, m, parent, segs=16)


def bar(name, parent, x0, x1, h, m, z=60.0):
    """A column standing on the floor (poly y = 0) from x0 to x1, h tall."""
    return box(name, (x0, 0.0, -z), (x1, h, z), m, parent)


def floor(name, parent, x0, x1, y, m, depth=260.0):
    """A flat tray or line under things: its top at poly y, `depth` deep in z."""
    return box(name, (x0, y - 40.0, -depth / 2), (x1, y, depth / 2), m, parent)


def tile(name, x, y, m, parent=None, s=TILE):
    """A matrix cell, centred at poly (x, y)."""
    h = s / 2
    return box(name, (x - h, y - h, -TILE_T / 2), (x + h, y + h, TILE_T / 2), m, parent)


def arrow(name, parent, tip, m, origin=(0.0, 0.0, 0.0), r=16.0, head=95.0, hr=52.0):
    """An arrow from poly `origin` to poly `tip`: a shaft and a cone head. Returns its group."""
    d = Vector(tip) - Vector(origin)
    L = d.length
    u = d.normalized()
    hl = min(head, 0.42 * L)
    shaft_end = Vector(tip) - u * hl
    g = empty(name, parent)
    tube(name + "_shaft", tuple(origin), tuple(shaft_end), r, m, g, verts=12)
    centre = Vector(tip) - u * (hl / 2)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=hr, radius2=0.0, depth=hl, location=P(*centre))
    c = _name(bpy.context.object, name + "_head")
    c.data.materials.append(m)
    c.parent = g
    c.rotation_mode = "QUATERNION"
    c.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(P(*u).normalized())
    return g


def axes(name, parent, x1, y1, m, r=7.0):
    """Two thin axes from the origin, to poly x1 and y1 (the plane z = 0)."""
    g = empty(name, parent)
    tube(name + "_x", (-120.0, 0.0, 0.0), (x1, 0.0, 0.0), r, m, g, verts=8)
    tube(name + "_y", (0.0, -120.0, 0.0), (0.0, y1, 0.0), r, m, g, verts=8)
    return g


def line(name, parent, a, b, m, r=7.0):
    return tube(name, a, b, r, m, parent, verts=8)


# ---- motion ----------------------------------------------------------------------------


def slide(obj, pts):
    """Keyed positions: `pts` is a list of (frame, poly point), linear between keys."""
    for f, p in pts:
        key(obj, f, "location", P(*p), linear=True)


def grow(obj, f0, f1):
    """Standing bars grow from flat to full height (poly y) between frames f0 and f1."""
    key(obj, 0, "scale", (1.0, 1.0, OFF))
    key(obj, f0, "scale", (1.0, 1.0, OFF))
    key(obj, f1, "scale", (1.0, 1.0, 1.0))


def tag(text, at, root, intervals):
    return label(text, at, root, intervals)


__all__ = [
    "BEAD_R", "BEAD_STEP", "TILE", "TILE_PITCH", "F", "beat", "P", "OFF", "start", "finish",
    "camera", "show", "label", "key", "mats", "dot", "bar", "floor", "tile", "arrow", "axes",
    "line", "slide", "grow", "tag",
]
