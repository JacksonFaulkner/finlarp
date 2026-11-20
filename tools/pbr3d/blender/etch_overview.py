"""The ETCH node page's overview (MELT + PULL template: picture-and-panel, docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/etch_overview.py

Writes blender/etch_overview.blend and assets/etch_overview.glb. One beat is 8 s at 24 fps.

One plasma etch chamber cut open at z = 0 (the camera sits on +z): gas comes in through the
showerhead, an RF coil round the lid lights the plasma, the wafer sits on the chuck, and a slice of
wafer stands in the middle with a hard mask, a film, an etch stop and a trench. Radicals drift in
every direction, ions fall straight down, the trench deepens until the etch stop, polymer coats the
sidewalls, and the strip step clears the mask and polymer. Parts are drawn to a schematic scale.

Beats (match the six beats in diagrams_nodes/etch/overview.rs):
  0 carve     the whole chamber: gas in, plasma lit, the wafer slice on the chuck, the pump pulls gas out
  1 ignite    RF from the coil lights the plasma; electrons, radicals and ions fill the chamber
  2 two halves radicals drift in every direction; ions fall straight down onto the trench floor
  3 deepen    the trench grows ion by ion until the etch stop, the mask barely erodes
  4 sidewall  polymer coats the trench walls; ions clear the floor, so the walls stay vertical
  5 strip     plasma off; mask and polymer are stripped, the slice goes on to clean and the next layer
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import (  # noqa: E402  (helpers, materials, beat timing)
    F,
    P,
    ball,
    beat,
    box,
    cut,
    disc,
    empty,
    fly,
    label,
    mat,
    pivot,
    rel,
    show,
    tube,
)
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402

PAGE = "etch"
BEATS = 6

# chamber (mm, Y up; the camera is on +z and the chamber is cut at z = 0)
CH_R = 1200.0  # outer radius of the chamber wall
CH_TOP = 1900.0  # underside of the lid
WAFER_Y = 150.0  # top of the chuck, where the wafer slice sits

# the wafer slice: a block through the wafer, drawn at schematic scale
SLAB_HALF = 700.0
SLAB_Z0 = -800.0
SI_TOP = 330.0  # silicon substrate
STOP_TOP = 380.0  # etch-stop layer (the trench ends here)
FILM_TOP = 1080.0  # the film being etched (oxide)
MASK_TOP = 1140.0  # the hard mask on top, open over the trench
TRENCH_HALF = 90.0  # the trench is 180 mm wide
POLY_T = 12.0  # sidewall polymer thickness

# (camera target, distance, yaw, pitch), one per beat
POSES = [
    ((0.0, 1100.0, 0.0), 6600.0, 0.22, 0.14),
    ((0.0, 1250.0, -100.0), 4000.0, 0.18, 0.12),
    ((0.0, 800.0, -300.0), 4400.0, 0.22, 0.14),
    ((0.0, 700.0, -200.0), 2900.0, 0.14, 0.08),
    ((0.0, 700.0, -200.0), 2100.0, 0.10, 0.04),
    ((0.0, 800.0, 0.0), 3200.0, 0.20, 0.22),
]


# ---- extra shapes ---------------------------------------------------------------------


def shell(name, x, z, r_out, y0, y1, thick, m, parent=None):
    """A hollow upright cylinder (a chamber wall) on axis (x, z), from y0 to y1."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=72, radius=r_out, depth=y1 - y0, end_fill_type="NOTHING", location=P(x, (y0 + y1) / 2, z)
    )
    return _solidify(bpy.context.object, name, thick, m, parent)


def _solidify(o, name, thick, m, parent):
    o.name = name
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = thick
    mod.offset = -1.0
    mod.use_rim = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(m)
    o.parent = parent
    return o


def run(parent, name, n, pts, size, m, b, u0, u1, life):
    """`n` blobs that each travel the polyline `pts` over `life` frames, launched one after another
    between fractions u0 and u1 of beat `b`."""
    g = empty(name, parent)
    path = [rel(pts[0], q) for q in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, m, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, 2 * (len(pts) - 1)))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


def mats(m):
    m["etch_si"] = mat("etch_si", (0.50, 0.53, 0.60), metal=0.85, rough=0.25)
    m["etch_stop"] = mat("etch_stop", (0.40, 0.55, 0.70), rough=0.4)
    m["etch_oxide"] = mat("etch_oxide", (0.80, 0.74, 0.58), rough=0.5)
    m["etch_mask"] = mat("etch_mask", (0.10, 0.10, 0.11), rough=0.8)
    m["etch_void"] = mat("etch_void", (0.02, 0.02, 0.03), rough=0.9)
    m["etch_poly"] = mat("etch_poly", (0.62, 0.40, 0.90), rough=0.4, emit=(0.5, 0.3, 0.9), strength=0.6)
    m["etch_esc"] = mat("etch_esc", (0.22, 0.24, 0.26), rough=0.5)
    m["etch_cathode"] = mat("etch_cathode", (0.38, 0.30, 0.24), metal=0.5, rough=0.5)
    m["etch_coil"] = mat("etch_coil", (0.85, 0.45, 0.22), metal=0.9, rough=0.3)
    m["etch_plasma"] = mat("etch_plasma", (0.70, 0.45, 1.0), emit=(0.6, 0.35, 1.0), strength=1.2, alpha=0.12)
    m["etch_ion"] = mat("etch_ion", (0.65, 0.88, 1.0), emit=(0.6, 0.85, 1.0), strength=7.0)
    m["etch_radical"] = mat("etch_radical", (0.60, 1.0, 0.55), emit=(0.55, 1.0, 0.5), strength=3.5)
    m["etch_gas"] = mat("etch_gas", (0.80, 0.90, 1.0), emit=(0.7, 0.85, 1.0), strength=2.0, alpha=0.7)
    m["etch_byprod"] = mat("etch_byprod", (0.88, 0.88, 0.92), rough=0.7, alpha=0.7)
    m["etch_cabinet"] = mat("etch_cabinet", (0.25, 0.42, 0.30), metal=0.3, rough=0.5)
    m["etch_rf"] = mat("etch_rf", (0.20, 0.22, 0.26), metal=0.5, rough=0.4)
    return m


# ---- stations --------------------------------------------------------------------------


def build_chamber(root, m):
    """The etch chamber cut open: wall, floor, lid, showerhead, the RF coil round the lid, the
    chuck with its cathode, the pump on the right and the gas cabinet on the left."""
    g = empty("chamber", root)
    cut(shell("chamber_wall", 0.0, 0.0, CH_R, 0.0, CH_TOP, 60, m["steel"], g), 0.0)
    cut(disc("chamber_floor", (0.0, -30.0, 0.0), CH_R, 60, m["dark_steel"], g), 0.0)
    cut(disc("chamber_lid", (0.0, CH_TOP + 30.0, 0.0), CH_R, 60, m["dark_steel"], g), 0.0)
    cut(disc("showerhead", (0.0, 1815.0, 0.0), 1100.0, 30, m["electrode"], g), 0.0)
    cut(disc("gas_plenum", (0.0, 1990.0, 0.0), 1000.0, 60, m["dark_steel"], g), 0.0)

    # the RF coil: two turns of short segments round the lid, cut at the plane like the wall
    for y in (1560.0, 1640.0):
        r = 1290.0
        segs = 12
        for i in range(segs):
            a0 = 2 * math.pi * i / segs
            a1 = 2 * math.pi * (i + 1.08) / segs
            p0 = (r * math.cos(a0), y, r * math.sin(a0))
            p1 = (r * math.cos(a1), y, r * math.sin(a1))
            cut(tube(f"coil_{y:.0f}_{i}", p0, p1, 26, m["etch_coil"], g, verts=12), 0.0)
    label("RF coil lights the plasma", (1300.0, 1620.0, 0.0), g, beat(0))

    # the chuck: cathode under the electrostatic chuck, the wafer slice sits on top
    cut(disc("etch_cathode", (0.0, 30.0, 0.0), 860.0, 60, m["etch_cathode"], g), 0.0)
    cut(disc("etch_esc", (0.0, 105.0, 0.0), 850.0, 90, m["etch_esc"], g), 0.0)

    # the turbo pump on the right, its pipe from the chamber floor
    tube("pump_pipe", (1000.0, 120.0, -150.0), (1340.0, 120.0, -150.0), 45, m["steel"], g, verts=16)
    cut(disc("turbo_pump", (1600.0, 260.0, 0.0), 260.0, 400, m["dark_steel"], g), 0.0)
    label("turbo pump pulls gas out", (1600.0, 60.0, 0.0), g, beat(0))

    # the RF generator on the top right, its cable to the coil
    box("rf_generator", (1750.0, 1400.0, -350.0), (2350.0, 2000.0, 350.0), m["etch_rf"], g)
    tube("rf_cable", (1750.0, 1640.0, -150.0), (1300.0, 1640.0, -40.0), 26, m["etch_coil"], g, verts=12)

    # the gas cabinet on the left, its feed line into the plenum
    box("gas_cabinet", (-2500.0, 0.0, -350.0), (-2100.0, 1500.0, 350.0), m["etch_cabinet"], g)
    tube("gas_feed_a", (-2100.0, 1500.0, -150.0), (-1700.0, 1990.0, -150.0), 40, m["steel"], g, verts=12)
    tube("gas_feed_b", (-1700.0, 1990.0, -150.0), (-1000.0, 1990.0, -150.0), 40, m["steel"], g, verts=12)
    label("process gas in at the showerhead", (-1100.0, 1790.0, 0.0), g, beat(0))
    label("wafer on the chuck", (820.0, 300.0, 0.0), g, beat(0))
    return g


def build_wafer(root, m):
    """The wafer slice on the chuck: silicon, etch stop, the oxide film, the hard mask over it.
    The trench is a void that grows downward from the mask opening, the sidewall polymer appears
    on its walls, and the mask is stripped in beat 5."""
    w = empty("wafer", root)
    box("etch_si", (-SLAB_HALF, WAFER_Y, SLAB_Z0), (SLAB_HALF, SI_TOP, 0.0), m["etch_si"], w)
    box("etch_stop", (-SLAB_HALF, SI_TOP, SLAB_Z0), (SLAB_HALF, STOP_TOP, 0.0), m["etch_stop"], w)
    box("film_left", (-SLAB_HALF, STOP_TOP, SLAB_Z0), (-TRENCH_HALF, FILM_TOP, 0.0), m["etch_oxide"], w)
    box("film_right", (TRENCH_HALF, STOP_TOP, SLAB_Z0), (SLAB_HALF, FILM_TOP, 0.0), m["etch_oxide"], w)
    label("etch stop: the trench ends here", (0.0, STOP_TOP + 40.0, 0.0), w, beat(3))
    label("film: the layer being carved", (-520.0, 800.0, 0.0), w, beat(3))

    # the hard mask, open over the trench; it erodes only slowly while the etch runs
    g_mask = empty("hard_mask", root)
    box("mask_left", (-SLAB_HALF, FILM_TOP, SLAB_Z0), (-TRENCH_HALF, MASK_TOP, 0.0), m["etch_mask"], g_mask)
    box("mask_right", (TRENCH_HALF, FILM_TOP, SLAB_Z0), (SLAB_HALF, MASK_TOP, 0.0), m["etch_mask"], g_mask)
    show(g_mask, [(F(0, 0), F(5, 0.25))])
    label("hard mask: erodes slowly", (-640.0, 1160.0, 0.0), root, beat(1))

    # the trench: a dark void hung from the mask opening, scaled in height about its top edge
    trench = pivot("trench", (0.0, MASK_TOP, 0.0), root)
    box(
        "trench_void",
        rel((0.0, MASK_TOP, 0.0), (-TRENCH_HALF, STOP_TOP, SLAB_Z0)),
        rel((0.0, MASK_TOP, 0.0), (TRENCH_HALF, MASK_TOP, -5.0)),
        m["etch_void"],
        trench,
    )
    scale_keys(
        trench,
        [
            (0, (1, 0.02, 1)),
            (F(2, 0.9), (1, 0.02, 1)),
            (F(3, 0.8), (1, 1, 1)),
            (F(6, 0), (1, 1, 1)),
        ],
    )

    # the sidewall polymer: thin violet films on both trench walls, present in beat 4
    g_poly = empty("sidewall_polymer", root)
    box(
        "poly_left",
        (-TRENCH_HALF, STOP_TOP + 5.0, SLAB_Z0),
        (-TRENCH_HALF + POLY_T, MASK_TOP - 40.0, -5.0),
        m["etch_poly"],
        g_poly,
    )
    box(
        "poly_right",
        (TRENCH_HALF - POLY_T, STOP_TOP + 5.0, SLAB_Z0),
        (TRENCH_HALF, MASK_TOP - 40.0, -5.0),
        m["etch_poly"],
        g_poly,
    )
    show(g_poly, [(F(4, 0), F(5, 0.45))])
    label("sidewall polymer blocks sideways attack", (120.0, 900.0, 0.0), root, beat(4))
    label("ions clear the floor only", (0.0, 420.0, 0.0), root, beat(4))
    return w


def build_plasma(root, m):
    """The glowing plasma between the chuck and the showerhead, lit from the end of beat 0 to the
    strip step in beat 5."""
    g = empty("plasma_glow", root)
    cut(disc("plasma_volume", (0.0, 1025.0, 0.0), 1150.0, 1350, m["etch_plasma"], g), 0.0)
    show(g, [(F(0, 0.6), F(5, 0.5))])
    label("plasma: electrons, radicals, ions", (0.0, 1320.0, 0.0), root, beat(1))
    label("5-100 mTorr", (-1150.0, 1480.0, 0.0), root, beat(1))
    return g


def build_flows(root, m):
    """The moving parts: gas jets from the showerhead (beats 0-1), ions falling onto the trench
    and the mask (beats 2-4), radicals drifting sideways (beats 2-3), and the byproducts pumped out."""
    # gas jets from the showerhead
    for k, x in enumerate((-800.0, -400.0, 0.0, 400.0, 800.0)):
        run(root, f"gas{k}", 3, [(x, 1790.0, -300.0), (x * 0.9, 1450.0, -300.0)], 18, m["etch_gas"], 0, 0.1 + 0.05 * k, 0.6, 60)

    # ions: a few land in the trench, more land on the mask; they fall straight down
    for k, x in enumerate((-60.0, -20.0, 20.0, 60.0)):
        run(root, f"ion_trench{k}", 3, [(x, 1500.0, -200.0), (x, MASK_TOP + 20.0, -200.0), (x, STOP_TOP + 10.0, -200.0)], 18, m["etch_ion"], 2, 0.05 + 0.1 * k, 0.5, 70)
    for k, x in enumerate((-620.0, -420.0, 420.0, 620.0)):
        run(root, f"ion_mask{k}", 3, [(x, 1500.0, -200.0), (x, MASK_TOP + 30.0, -200.0)], 18, m["etch_ion"], 2, 0.1 + 0.08 * k, 0.6, 50)
    for k, x in enumerate((-60.0, 0.0, 60.0)):
        run(root, f"ion_late{k}", 3, [(x, 1500.0, -200.0), (x, STOP_TOP + 10.0, -200.0)], 18, m["etch_ion"], 3, 0.1 + 0.2 * k, 0.6, 60)

    # radicals: neutral, so they come from every direction and reach the trench walls too
    radical_paths = [
        [(-900.0, 1420.0, -700.0), (-500.0, 1100.0, -150.0), (-300.0, 1190.0, -600.0)],
        [(800.0, 1420.0, -300.0), (300.0, 1000.0, -800.0), (100.0, 1200.0, -500.0)],
        [(-200.0, 1450.0, -850.0), (150.0, 1080.0, -400.0), (120.0, 1300.0, -200.0)],
        [(600.0, 1420.0, -800.0), (-120.0, 1000.0, -500.0), (-60.0, 1200.0, -200.0)],
    ]
    for k, pts in enumerate(radical_paths):
        run(root, f"radical{k}", 3, pts, 18, m["etch_radical"], 2, 0.2 + 0.1 * k, 0.7, 60)

    # byproducts (SiF4 and friends) leave the wafer and go down to the pump
    run(
        root,
        "byproduct",
        4,
        [(0.0, 1150.0, -400.0), (600.0, 1000.0, -400.0), (900.0, 500.0, -300.0), (1000.0, 120.0, -150.0)],
        20,
        m["etch_byprod"],
        3,
        0.2,
        0.7,
        80,
    )
    label("radicals: sideways too", (-600.0, 1300.0, -300.0), root, beat(2))
    label("ions: straight down", (330.0, 1260.0, -200.0), root, beat(2))
    label("pump: byproducts out", (1100.0, 600.0, -150.0), root, beat(3))
    label("strip: mask and polymer off", (-420.0, 1180.0, 0.0), root, beat(5))
    label("then clean, next layer", (820.0, 620.0, 0.0), root, beat(5))


def build():
    m, root = start("overview", BEATS, page=PAGE)
    mats(m)
    build_chamber(root, m)
    build_wafer(root, m)
    build_plasma(root, m)
    build_flows(root, m)
    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish("overview", page=PAGE)
