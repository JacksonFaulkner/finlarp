"""The POLYSILICON overview, authored in Blender and exported for pbr3d, in the SAND template
(docs/diagram-pages.md): a Siemens-process plant cut open at z = 0, the camera on +z with one
pose per beat, and `label:<text>` empties for the tags the TUI pins on.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/poly_overview.py

It writes:
  blender/poly_overview.blend   open it in Blender to edit by hand
  assets/poly_overview.glb      what pbr3d embeds and plays back

The plant runs left to right: the fluidised-bed reactor, the condenser and distillation column
(with the STC tank and converter behind them), the Siemens bell jar, the off-gas recovery unit
behind the jar, then the crusher, the etch bath and the product bin. Parts are drawn to a
schematic scale, not to the size of a real plant.

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/polysilicon/overview.rs).

Beats (match the POLYSILICON overview page):
  0 bed       MG-Si lumps run down the chute, HCl bubbles up through the bed, TCS + H2 leave the top
  1 column    the gas condenses, vapour climbs the trays, pure TCS leaves the top, STC the bottom
  2 bell jar  TCS + H2 rise round glowing U-rods, which thicken from 20 mm to about 170 mm
  3 recycle   off-gas goes to recovery, H2 + HCl return to the bed, STC is converted back to TCS
  4 harvest   the bell lifts off, the rods cool and ride to the crusher, chunks fall into a basket
  5 finish    the basket dips in the etch bath and the chunks go into the bagged bin
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402  (helpers, materials, beat timing)
from sand_overview import (  # noqa: E402
    BEAT_FRAMES,
    OFF,
    F,
    P,
    _constant_until,
    ball,
    beat,
    box,
    cup,
    cut,
    disc,
    empty,
    fly,
    key,
    label,
    mat,
    pivot,
    rel,
    rock,
    show,
    tube,
)
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402

BEATS = 6

# x of each station's axis (mm); everything stands on y = 0
BED_X, BED_R, BED_TOP = 0.0, 700.0, 4200.0
GRAIN0, GRAIN1 = 400.0, 1900.0  # the fluidised bed of grains
HOP_X = -1800.0
INLET_X = -1900.0  # HCl (and recycled H2 + HCl) come in from here
COND_X0, COND_X1, COND_Y = 1300.0, 2300.0, 4900.0
COL_X, COL_R, COL_TOP = 3200.0, 450.0, 5600.0
FEED_Y = 3500.0
TRAYS = [700.0 * k for k in range(1, 8)]
STC_X, STC_Z = 2200.0, -900.0
JAR_X, JAR_R, JAR_WALL_TOP = 5600.0, 1150.0, 2600.0
BASE_R = 1250.0
TCS_PIPE_X = 4100.0
ROD_Y0, ROD_Y1 = 150.0, 2350.0
ROD_R0, ROD_GROW = 10.0, 8.5  # 20 mm slim rods grow to 170 mm (150-180 mm on the page)
PAIRS = [(JAR_X, -250.0, 250.0), (JAR_X - 500.0, -700.0, 200.0), (JAR_X + 500.0, -700.0, 200.0)]
REC_X0, REC_X1, REC_Z0, REC_Z1 = 6600.0, 7800.0, -2800.0, -2000.0
BACK_Z, BACK_Y = -2400.0, 800.0
LIFT = 2900.0  # how far the bell rises in beat 4
CRUSH_X = 8800.0
BASKET = (CRUSH_X, 300.0, 0.0)
TANK_X0, TANK_X1 = 9900.0, 11100.0
BIN_X0, BIN_X1 = 11800.0, 12800.0
PIPE_Z = -150.0  # pipes run just behind the cut plane

# (camera target, distance, yaw, pitch), one per beat
POSES = [
    ((-500.0, 2600.0, 0.0), 11800.0, 0.22, 0.12),
    ((2300.0, 3000.0, -300.0), 12500.0, 0.20, 0.10),
    ((JAR_X, 1500.0, -200.0), 6900.0, 0.18, 0.16),
    ((3000.0, 1900.0, -1200.0), 16000.0, 0.22, 0.34),
    ((7200.0, 2900.0, 0.0), 12500.0, 0.10, 0.14),
    ((10700.0, 1200.0, 0.0), 8200.0, 0.08, 0.30),
]


# ---- extra shapes ---------------------------------------------------------------------


def shell(name, x, z, r_out, y0, y1, thick, m, parent=None):
    """A hollow upright cylinder (a vessel wall) on axis (x, z), from y0 to y1."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=72, radius=r_out, depth=y1 - y0, end_fill_type="NOTHING", location=P(x, (y0 + y1) / 2, z)
    )
    return _solidify(bpy.context.object, name, thick, m, parent)


def dome(name, c, r_out, thick, m, parent=None):
    """A hollow hemisphere (the top of the bell), open at the bottom, centred at poly point `c`."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r_out, segments=72, ring_count=36, location=P(*c))
    o = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 0, -1), clear_outer=True)
    bm.to_mesh(o.data)
    bm.free()
    return _solidify(o, name, thick, m, parent)


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


def pipe(name, pts, r, m, parent, verts=16):
    """A pipe run through poly points `pts`, with a ball at each bend."""
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        tube(f"{name}{i}", a, b, r, m, parent, verts=verts)
        if i:
            ball(f"{name}{i}_elbow", a, r * 1.05, m, parent, segs=12)


def run(parent, name, n, pts, size, m, b, u0, u1, life):
    """`n` blobs that each travel the poly polyline `pts` over `life` frames, launched one after
    another between fractions u0 and u1 of beat `b`."""
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


def keyed_path(obj, keys):
    """Location keys (frame, poly offset); holds between keys are linear."""
    for f, off in keys:
        key(obj, f, "location", P(*off), linear=True)


def mats(m):
    m["hcl"] = mat("hcl_gas", (0.55, 0.90, 0.55), emit=(0.5, 0.9, 0.5), strength=1.6, alpha=0.75)
    m["tcs_gas"] = mat("tcs_gas", (1.0, 0.88, 0.45), emit=(1.0, 0.85, 0.4), strength=1.8, alpha=0.75)
    m["tcs_liq"] = mat("tcs_liquid", (0.95, 0.80, 0.35), rough=0.2, emit=(0.9, 0.7, 0.3), strength=0.6)
    m["h2"] = mat("h2_gas", (0.65, 0.85, 1.0), emit=(0.6, 0.8, 1.0), strength=1.8, alpha=0.75)
    m["stc"] = mat("stc", (0.75, 0.55, 0.95), emit=(0.7, 0.5, 0.95), strength=1.6, alpha=0.8)
    m["rod_hot"] = mat("rod_hot", (1.0, 0.55, 0.2), emit=(1.0, 0.5, 0.15), strength=4.0)
    m["poly"] = mat("poly_si", (0.62, 0.64, 0.68), metal=0.85, rough=0.28)
    m["mg"] = mat("mg_si", (0.32, 0.32, 0.34), metal=0.4, rough=0.8)
    m["grains"] = mat("grain_bed", (0.36, 0.36, 0.39), metal=0.3, rough=0.8)
    m["acid"] = mat("acid", (0.55, 0.85, 0.65), rough=0.1, alpha=0.45)
    m["bag"] = mat("bag_poly", (0.90, 0.92, 0.95), rough=0.4, alpha=0.65)
    m["water"] = mat("cooling", (0.35, 0.55, 0.85), metal=0.4, rough=0.3)
    return m


# ---- stations --------------------------------------------------------------------------


def build_bed(root, m):
    """The fluidised-bed reactor and its feed. Beat 0: MG-Si lumps run down the chute, HCl comes
    in under the distributor and bubbles up through the grains, TCS + H2 leave the top."""
    g = empty("bed", root)
    cut(disc("bed_floor", (BED_X, 30, 0), BED_R, 60, m["steel"], g), 0.0)
    cut(shell("bed_wall", BED_X, 0, BED_R, 60, BED_TOP, 60, m["steel"], g), 0.0)
    cut(disc("bed_roof", (BED_X, BED_TOP + 30, 0), BED_R, 60, m["steel"], g), 0.0)
    cut(disc("distributor", (BED_X, 340, 0), BED_R - 60, 30, m["dark_steel"], g), 3.0)
    cut(disc("grains", (BED_X, (GRAIN0 + GRAIN1) / 2, 0), BED_R - 60, GRAIN1 - GRAIN0, m["grains"], g), 3.0)
    label("fluidised bed, about 300 C", (BED_X + 350, 1300, 40), g, beat(0))

    # the grains churn: lumps on the cut face bob up and down through beat 0
    for k in range(10):
        x = BED_X - 520 + (k % 5) * 260
        y = 650 + (k // 5) * 650 + (k % 2) * 180
        e = empty(f"grain{k}", g)
        rock(f"grain{k}_r", (x, y, 25), 55, m["mg"], e)
        for j in range(13):
            dy = (90 if (j + k) % 2 else -60) if j % 12 else 0
            key(e, F(0, j / 12), "location", P(0, dy, 0))
        key(e, F(1, 0), "location", P(0, 0, 0))

    # feed hopper and chute
    box("hopper", (HOP_X - 350, 3200, -450), (HOP_X + 350, 4000, 150), m["steel"], g)
    chute = [(HOP_X, 3200, PIPE_Z), (BED_X - BED_R - 20, GRAIN1 - 100, PIPE_Z)]
    tube("chute", *chute, 110, m["pipe_glass"], g, verts=24)
    label("MG-Si lumps, 98-99% Si", (HOP_X - 350, 3700, 150), g, beat(0))
    lumps = empty("lumps", g)
    for k in range(10):
        e = empty(f"lump{k}", lumps)
        rock(f"lump{k}_r", chute[0], 70, m["mg"], e)
        f0 = F(0, 0.04 + 0.085 * k)
        f1 = f0 + 30
        fly(e, [(0, 0, 0), rel(chute[0], chute[1]), rel(chute[0], (BED_X - 300, GRAIN1 - 150, PIPE_Z))], f0, f1, steps=4)
        show(e, [(f0, min(f1, F(1, 0)))])

    # HCl inlet under the distributor; it also carries the recycled H2 + HCl (beat 3)
    pipe("inlet", [(INLET_X, 250, PIPE_Z), (BED_X - BED_R + 30, 250, PIPE_Z)], 90, m["steel"], g)
    label("HCl gas in", (INLET_X + 200, 250, 0), g, beat(0))
    for k, x in enumerate((-420, -140, 140, 420)):
        run(g, f"hcl{k}_", 4, [(BED_X + x, 300, 50), (BED_X + x * 1.1, GRAIN1, 50)], 55, m["hcl"], 0, 0.06 + 0.04 * k, 0.8, 54)
    run(g, "hcl_in", 6, [(INLET_X, 250, PIPE_Z), (BED_X - BED_R, 250, PIPE_Z)], 70, m["hcl"], 0, 0.0, 0.7, 30)

    # product gas off the top, along to the condenser
    up = [(BED_X, BED_TOP + 60, PIPE_Z), (BED_X, COND_Y, PIPE_Z), (COND_X0, COND_Y, PIPE_Z)]
    pipe("bed_out", up, 110, m["steel"], g)
    run(g, "tcs_free", 6, [(BED_X - 200, GRAIN1 + 50, 60), (BED_X, BED_TOP - 100, 60)], 80, m["tcs_gas"], 0, 0.15, 0.8, 50)
    label("TCS + H2 out the top", (BED_X, COND_Y + 150, PIPE_Z), g, beat(0))
    return g


def build_column(root, m):
    """The condenser, the distillation column, the STC tank and the STC converter. Beat 1: gas
    condenses, vapour climbs the trays, pure TCS leaves the top and STC the bottom. Beat 3: STC is
    converted back to TCS and fed to the column."""
    g = empty("column", root)
    tube("condenser", (COND_X0, COND_Y, PIPE_Z), (COND_X1, COND_Y, PIPE_Z), 280, m["water"], g, verts=32)
    for x in (COND_X0 + 150, COND_X1 - 150):
        tube(f"cond_band{x:.0f}", (x, COND_Y, PIPE_Z), (x + 40, COND_Y, PIPE_Z), 300, m["steel"], g, verts=32)
    label("condenser: gas to liquid", (COND_X0 + 500, COND_Y + 280, PIPE_Z), g, beat(1))
    feed = [(COND_X1, COND_Y, PIPE_Z), (COND_X1 + 100, COND_Y, PIPE_Z), (COND_X1 + 100, FEED_Y, PIPE_Z), (COL_X - COL_R + 20, FEED_Y, PIPE_Z)]
    pipe("col_feed", feed, 70, m["steel"], g)
    run(g, "gas_in", 5, [(BED_X, COND_Y, PIPE_Z), (COND_X0 + 300, COND_Y, PIPE_Z)], 90, m["tcs_gas"], 1, 0.0, 0.5, 30)
    run(g, "liq_in", 6, [(COND_X1 - 100, COND_Y, PIPE_Z)] + feed[1:], 55, m["tcs_liq"], 1, 0.1, 0.75, 40)

    cut(disc("col_floor", (COL_X, 30, 0), COL_R, 60, m["steel"], g), 0.0)
    cut(shell("col_wall", COL_X, 0, COL_R, 60, COL_TOP, 50, m["steel"], g), 0.0)
    cut(disc("col_roof", (COL_X, COL_TOP + 30, 0), COL_R, 60, m["steel"], g), 0.0)
    for k, y in enumerate(TRAYS):
        dx = 60 if k % 2 else -60
        cut(disc(f"tray{k}", (COL_X + dx, y, 0), COL_R - 110, 30, m["dark_steel"], g), 3.0)
    label("distillation trays, 30-60 C", (COL_X + COL_R, 2800, 0), g, beat(1))
    # vapour climbs from tray to tray, liquid drips back down the other side
    run(g, "vapour", 9, [(COL_X - 150, 450, 40), (COL_X - 150, COL_TOP - 200, 40)], 70, m["tcs_gas"], 1, 0.08, 0.85, 60)
    run(g, "reflux", 8, [(COL_X + 200, COL_TOP - 300, 40), (COL_X + 200, 300, 40)], 40, m["stc"], 1, 0.1, 0.85, 60)
    pool = disc("col_sump", (COL_X, 200, -10), COL_R - 60, 220, m["stc"], g)
    cut(pool, 2.0)

    top = [(COL_X, COL_TOP + 60, PIPE_Z), (COL_X, 5900, PIPE_Z), (TCS_PIPE_X, 5900, PIPE_Z), (TCS_PIPE_X, 90, PIPE_Z), (JAR_X - BASE_R, 90, PIPE_Z)]
    pipe("tcs_line", top, 70, m["steel"], g)
    run(g, "tcs_top", 6, top[:3], 70, m["tcs_gas"], 1, 0.25, 0.85, 36)
    label("pure TCS off the top", (COL_X + 500, 5900, PIPE_Z), g, beat(1))

    # STC tank and converter, behind and left of the column
    bottom = [(COL_X - COL_R + 20, 300, PIPE_Z), (STC_X, 300, PIPE_Z), (STC_X, 300, STC_Z + 400)]
    pipe("stc_line", bottom, 60, m["steel"], g)
    disc("stc_tank", (STC_X, 600, STC_Z), 400, 1200, m["dark_steel"], g, 48)
    run(g, "stc_out", 5, bottom, 55, m["stc"], 1, 0.3, 0.85, 30)
    label("STC out the bottom", (STC_X - 400, 1000, STC_Z + 400), g, beat(1))
    box("converter", (STC_X - 400, 1500, STC_Z - 400), (STC_X + 400, 2300, STC_Z + 400), m["steel"], g)
    tube("conv_riser", (STC_X, 1200, STC_Z), (STC_X, 1500, STC_Z), 60, m["steel"], g)
    back = [(STC_X + 400, 1900, STC_Z), (COL_X, 1900, STC_Z), (COL_X, 1900, -COL_R + 20)]
    pipe("conv_out", back, 60, m["steel"], g)
    label("STC converted back to TCS", (STC_X, 2300, STC_Z + 400), g, beat(3))
    run(g, "stc_loop", 6, bottom + [(STC_X, 1200, STC_Z), (STC_X, 1900, STC_Z)], 70, m["stc"], 3, 0.05, 0.55, 60)
    run(g, "tcs_back", 5, back, 70, m["tcs_gas"], 3, 0.3, 0.85, 30)
    return g


def rod_pair(parent, m, k, x, z, half):
    """A U-shaped rod pair at (x, z): two upright rods `half` mm either side of x, bridged at the
    top. Each part sits in a pivot that thickens it in beat 2 (ROD_GROW times); a hot copy shows
    while the rods are powered and a cool copy after."""
    hot = [(F(2, 0), F(4, 0.15))]
    cool = [(0, F(2, 0)), (F(4, 0.15), F(6, 0))]
    grow = [(0, 1.0), (F(2, 0.05), 1.0), (F(2, 0.95), ROD_GROW), (F(6, 0), ROD_GROW)]
    for side in (-1, 1):
        rx = x + side * half
        pv = pivot(f"rod{k}{side:+d}", (rx, ROD_Y0, z), parent)
        for tag, mm, iv in (("hot", m["rod_hot"], hot), ("cool", m["poly"], cool)):
            w = empty(f"rod{k}{side:+d}_{tag}", pv)
            tube(f"rod{k}{side:+d}_{tag}_m", (0, 0, 0), (0, ROD_Y1 - ROD_Y0, 0), ROD_R0, mm, w, verts=12)
            show(w, iv)
        scale_keys(pv, [(f, (s, s, 1)) for f, s in grow])
    pv = pivot(f"bridge{k}", (x, ROD_Y1, z), parent)
    for tag, mm, iv in (("hot", m["rod_hot"], hot), ("cool", m["poly"], cool)):
        w = empty(f"bridge{k}_{tag}", pv)
        tube(f"bridge{k}_{tag}_m", (-half - ROD_R0, 0, 0), (half + ROD_R0, 0, 0), ROD_R0, mm, w, verts=12)
        show(w, iv)
    scale_keys(pv, [(f, (1, s, s)) for f, s in grow])


def build_jar(root, m):
    """The Siemens bell jar: base plate, three U-rod pairs and the water-cooled bell. Beat 2: TCS
    + H2 rise round the glowing rods, which thicken. Beat 3: the off-gas leaves for recovery.
    Beat 4: the bell lifts, the rods cool and ride to the crusher."""
    g = empty("jar", root)
    cut(disc("jar_base", (JAR_X, 75, 0), BASE_R, 150, m["dark_steel"], g), 0.0)
    for k, dx in enumerate((-800, -350, 350, 800)):
        cut(disc(f"nozzle{k}", (JAR_X + dx, 175, -100), 45, 50, m["steel"], g, 16), 2.0)

    bell = empty("bell", g)
    cut(shell("bell_wall", JAR_X, 0, JAR_R, 150, JAR_WALL_TOP, 60, m["water"], bell), 6.0)
    cut(dome("bell_dome", (JAR_X, JAR_WALL_TOP, 0), JAR_R, 60, m["water"], bell), 6.0)
    label("water-cooled steel bell", (JAR_X + JAR_R, 1900, 0), bell, beat(2))
    label("bell lifted off", (JAR_X + JAR_R, JAR_WALL_TOP, 0), bell, beat(4))
    keyed_path(bell, [(F(4, 0.03), (0, 0, 0)), (F(4, 0.22), (0, LIFT, 0)), (F(6, 0), (0, LIFT, 0))])

    # the rods: carry (moves in beat 4) > show (gone once crushed) > pivots (thicken in beat 2)
    carry = empty("rods_carry", g)
    vis = empty("rods_vis", carry)
    show(vis, [(0, F(4, 0.62))])
    for k, (x, z, half) in enumerate(PAIRS):
        rod_pair(vis, m, k, x, z, half)
    label("U-rods at about 1100 C", (JAR_X - 250, 1700, -250), carry, beat(2))
    label("rods: 20 mm to 150-180 mm", (JAR_X + 250, 900, -250), carry, beat(2))
    label("rods 150-180 mm thick", (JAR_X + 250, 1400, -250), carry, [(F(4, 0.25), F(4, 0.55))])
    over = CRUSH_X - JAR_X
    keyed_path(carry, [
        (F(4, 0.25), (0, 0, 0)),
        (F(4, 0.36), (0, LIFT - 300, 250)),
        (F(4, 0.50), (over, LIFT - 300, 250)),
        (F(4, 0.62), (over, 1400, 250)),
        (F(6, 0), (over, 1400, 250)),
    ])

    # TCS + H2 rise from the nozzles round the rods (beat 2)
    for k, dx in enumerate((-800, -350, 350, 800)):
        run(g, f"jar_gas{k}_", 5, [(JAR_X + dx, 200, -60), (JAR_X + dx * 0.6, 2400, -60), (JAR_X, 3000, -60)], 60, m["tcs_gas"], 2, 0.03 + 0.05 * k, 0.8, 70)
    run(g, "jar_feed", 6, [(TCS_PIPE_X, 1500, PIPE_Z), (TCS_PIPE_X, 90, PIPE_Z), (JAR_X - BASE_R, 90, PIPE_Z)], 70, m["tcs_gas"], 2, 0.0, 0.7, 30)
    label("TCS + H2 in at the base", (JAR_X - 800, 200, 0), g, beat(2))
    return g


def build_recycle(root, m):
    """The off-gas line from the jar to the recovery unit and the long return pipe to the bed's
    inlet. Beat 3: off-gas goes to recovery and H2 + HCl ride back to the bed."""
    g = empty("recycle", root)
    out = [(JAR_X + BASE_R, 90, PIPE_Z), (7300, 90, PIPE_Z), (7300, 90, REC_Z1)]
    pipe("offgas", out, 80, m["steel"], g)
    box("recovery", (REC_X0, 0, REC_Z0), (REC_X1, 1700, REC_Z1), m["steel"], g)
    for k in range(3):
        disc(f"rec_drum{k}", (REC_X0 + 200 + 400 * k, 2100, (REC_Z0 + REC_Z1) / 2), 160, 800, m["dark_steel"], g, 24)
    label("off-gas recovery", (REC_X1, 1700, REC_Z1), g, beat(3))
    ret = [(REC_X0, BACK_Y, BACK_Z), (INLET_X, BACK_Y, BACK_Z), (INLET_X, BACK_Y, PIPE_Z), (INLET_X, 250, PIPE_Z)]
    pipe("return", ret, 90, m["pipe_glass"], g, verts=20)
    label("H2 + HCl back to the bed", (1500, BACK_Y + 150, BACK_Z), g, beat(3))
    run(g, "offgas_p", 6, [(JAR_X, 400, -100), (JAR_X + 900, 150, PIPE_Z)] + out[1:], 80, m["tcs_gas"], 3, 0.0, 0.45, 40)
    half = len(ret) // 2
    run(g, "ret_h2", 8, ret + [(BED_X - BED_R, 250, PIPE_Z)], 100, m["h2"], 3, 0.15, 0.6, 72)
    run(g, "ret_hcl", 7, ret + [(BED_X - BED_R, 250, PIPE_Z)], 80, m["hcl"], 3, 0.2, 0.65, 72)
    return g


def build_finish(root, m):
    """The crusher, the etch bath and the product bin. Beat 4: crushed chunks fall into the
    basket under the crusher. Beat 5: the basket dips in the bath and tips into the bin."""
    g = empty("finish", root)
    box("crusher", (CRUSH_X - 600, 1000, -500), (CRUSH_X + 600, 2200, 400), m["steel"], g)
    box("crusher_mouth", (CRUSH_X - 700, 2200, -500), (CRUSH_X + 700, 2350, 400), m["dark_steel"], g)
    for dx in (-500, 500):
        box(f"crusher_leg{dx}", (CRUSH_X + dx - 60, 0, -400), (CRUSH_X + dx + 60, 1000, 300), m["dark_steel"], g)
    tube("crusher_spout", (CRUSH_X, 1000, -50), (CRUSH_X, 800, -50), 150, m["dark_steel"], g, verts=20)
    label("crusher", (CRUSH_X + 600, 2000, 400), g, beat(4))

    # the basket and its chunks ride a hoist through beat 5
    hoist = empty("hoist", g)
    cup("basket", BASKET, 330, 170, m["dark_steel"], hoist)
    disc("basket_floor", (BASKET[0], BASKET[1] + 10, 0), 330, 20, m["dark_steel"], hoist, 32)
    tube("hoist_cable", (BASKET[0], BASKET[1] + 170, 0), (BASKET[0], BASKET[1] + 2400, 0), 12, m["steel"], hoist, verts=8)
    show_hoist = empty("chunks_vis", hoist)
    show(show_hoist, [(0, F(5, 0.84))])
    for k in range(14):
        cx = BASKET[0] - 200 + (k % 4) * 130
        cz = -150 + ((k // 4) % 3) * 130
        cy = BASKET[1] + 80 + (k // 12) * 110
        e = empty(f"chunk{k}", show_hoist)
        rock(f"chunk{k}_r", (cx, cy, cz), 75, m["poly"], e)
        f0 = F(4, 0.64 + 0.022 * k)
        key(e, f0, "location", P(CRUSH_X - cx, 850 - cy, -50 - cz))
        key(e, f0 + 9, "location", P(0, 0, 0))
        show(e, [(f0, F(6, 0))])
    label("chunks fall into the basket", (BASKET[0] + 330, BASKET[1] + 250, 0), g, [(F(4, 0.68), F(5, 0))])
    tank_c = (TANK_X0 + TANK_X1) / 2
    bin_c = (BIN_X0 + BIN_X1) / 2
    dip = BASKET[1] - 200
    keyed_path(hoist, [
        (F(5, 0.04), (0, 0, 0)),
        (F(5, 0.12), (0, 1300, 0)),
        (F(5, 0.22), (tank_c - CRUSH_X, 1300, 0)),
        (F(5, 0.30), (tank_c - CRUSH_X, dip - BASKET[1] + 150, 0)),
        (F(5, 0.50), (tank_c - CRUSH_X, dip - BASKET[1] + 150, 0)),
        (F(5, 0.58), (tank_c - CRUSH_X, 1300, 0)),
        (F(5, 0.70), (bin_c - CRUSH_X, 1300, 0)),
        (F(5, 0.80), (bin_c - CRUSH_X, 900, 0)),
        (F(6, 0) - 1, (bin_c - CRUSH_X, 900, 0)),
    ])

    # the etch bath: an open tank, cut so the acid shows
    box("tank_floor", (TANK_X0, 0, -600), (TANK_X1, 60, 0), m["steel"], g)
    box("tank_back", (TANK_X0, 0, -660), (TANK_X1, 1100, -600), m["steel"], g)
    for x0 in (TANK_X0 - 60, TANK_X1):
        box(f"tank_side{x0:.0f}", (x0, 0, -660), (x0 + 60, 1100, 0), m["steel"], g)
    box("acid", (TANK_X0, 60, -600), (TANK_X1, 850, -2), m["acid"], g)
    label("acid etch bath", (TANK_X1, 1000, 0), g, beat(5))
    run(g, "etch_fizz", 8, [(tank_c - 150, 400, -100), (tank_c, 900, -100)], 30, m["clean"], 5, 0.3, 0.48, 24)

    # the product bin, lined with a bag that fills
    box("bin_floor", (BIN_X0, 0, -500), (BIN_X1, 60, 0), m["steel"], g)
    box("bin_back", (BIN_X0, 0, -560), (BIN_X1, 1000, -500), m["steel"], g)
    for x0 in (BIN_X0 - 60, BIN_X1):
        box(f"bin_side{x0:.0f}", (x0, 0, -560), (x0 + 60, 1000, 0), m["steel"], g)
    box("bin_front", (BIN_X0, 0, -60), (BIN_X1, 450, 0), m["steel"], g)
    fill = pivot("bin_fill", (bin_c, 60, -250), g)
    box("bin_chunks", rel((bin_c, 60, -250), (BIN_X0 + 40, 60, -460)), rel((bin_c, 60, -250), (BIN_X1 - 40, 760, -70)), m["poly"], fill)
    scale_keys(fill, [(0, (1, 1, 0.12)), (F(5, 0.82), (1, 1, 0.12)), (F(5, 0.95), (1, 1, 1)), (F(6, 0), (1, 1, 1))], until=None)
    box("bin_bag", (BIN_X0 + 20, 60, -480), (BIN_X1 - 20, 980, -50), m["bag"], g)
    label("9N+ chunks, bagged", (BIN_X1, 800, 0), g, [(F(5, 0.7), F(6, 0))])
    return g


def build():
    m, root = start("overview", BEATS, page="poly")
    mats(m)
    build_bed(root, m)
    build_column(root, m)
    build_jar(root, m)
    build_recycle(root, m)
    build_finish(root, m)
    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="poly")
