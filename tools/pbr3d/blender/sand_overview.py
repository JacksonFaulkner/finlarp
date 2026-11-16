"""The SAND overview, authored in Blender and exported for pbr3d.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/sand_overview.py

It writes:
  blender/sand_overview.blend   open it in Blender to edit by hand
  assets/sand_overview.glb      what pbr3d embeds and plays back

Units are millimetres, Y up in the scene (see P). The furnace is cut in half along the plane
z = 0 and the camera looks from +z, so the charge, cavities, crust and pool show in section.

One beat is SEC seconds at 24 fps: beat i covers frames BEAT_FRAMES*i .. BEAT_FRAMES*(i+1), and
the TUI samples the file at t = (beat + local) * SEC (diagrams_nodes/sand/overview.rs). Each
beat's camera holds still apart from a slow push-in, so a beat loops cleanly as a clip.

Empties named `label:<text>` are tags the TUI pins to the picture while they are switched on.

Beats (match the SAND overview page):
  0 feed      lumps of quartzite and coke run down the chutes onto the burden, which sinks
  1 cavities  an arc opens a glowing cavity under each electrode; SiO gas rises, Si drips to the pool
  2 crust     a crust grows round each cavity and the burden stalls; a stoking bar breaks the left one
  3 tap       the tap hole is lanced; silicon runs down the launder into the ladle under the fume hood
  4 off-gas   gas climbs out of the burden, along the duct into the bag filter; clean gas leaves the stack
  5 finish    the ladle pours into a casting bed; the slab is crushed and the lumps fill the bin
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

FPS = 24
SEC = 8
BEAT_FRAMES = FPS * SEC
BEATS = 6
OFF = 1e-5  # not zero: the glTF exporter divides by parent scale, so a zero group would zero its children

HERE = os.path.dirname(os.path.abspath(__file__))
PBR_DIR = os.path.normpath(os.path.join(HERE, ".."))
BLEND_OUT = os.path.join(HERE, "sand_overview.blend")
GLB_OUT = os.path.join(PBR_DIR, "assets", "sand_overview.glb")

R = 1800.0  # furnace shell radius
LINE = 150.0  # lining thickness
SHELL_TOP = 2000.0  # underside of the roof
BURDEN_TOP = 1650.0
POOL_TOP = 280.0
ELEC_R = 150.0
ELEC_TIP = 700.0
ELECS = (-650.0, 650.0)  # electrode x on the cut plane; a third stands behind at z = -650
CAV_Y, CAV_R = 560.0, 230.0
CRUST_R = 300.0
TAP_Y = 180.0
LADLE_X = R + 700.0
LADLE_TOP = 420.0
DUCT_X, DUCT_Z = 1350.0, -900.0
DUCT_Y = 2500.0
BAG_X0, BAG_X1 = 2700.0, 3800.0
BAG_Z = -1500.0  # the bag house stands behind and right of the furnace
STACK_X = 3250.0
CAST_Z = 0.0  # the product line runs on to the right of the ladle
MOULD_X = 3500.0
CRUSH_X = 4750.0
BIN_X0, BIN_X1 = 5350.0, 5950.0

# (camera target, distance, yaw, pitch), one per beat
POSES = [
    ((-300.0, 1700.0, 0.0), 7200.0, 0.35, 0.32),
    # beats 1-2: yawed off the electrode column and aimed at the cavity so the column does not
    # sit in front of it
    ((0.0, 520.0, 0.0), 4600.0, 0.75, 0.22),
    ((0.0, 620.0, 0.0), 4900.0, 0.85, 0.26),
    ((2150.0, 450.0, 0.0), 4300.0, 0.50, 0.22),
    ((1600.0, 1700.0, -600.0), 10500.0, 0.30, 0.28),
    ((4100.0, 650.0, 0.0), 6600.0, 0.12, 0.34),
]


def F(beat, u):
    """The frame a fraction `u` of the way through `beat`."""
    return round(BEAT_FRAMES * (beat + u))


def P(x, y, z):
    """A point in the scene's Y-up millimetres as a Blender Z-up vector."""
    return Vector((x, -z, y))


def along(path, u):
    """The point a fraction `u` (0..1) of the way along the polyline `path`, by length."""
    segs = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
    lens = [math.dist(a, b) for a, b in segs]
    want = max(0.0, min(1.0, u)) * sum(lens)
    for (a, b), n in zip(segs, lens):
        if want <= n or (a, b) == segs[-1]:
            f = 0.0 if n == 0 else min(1.0, want / n)
            return tuple(a[i] + (b[i] - a[i]) * f for i in range(3))
        want -= n
    return path[-1]


# ---- materials ------------------------------------------------------------------------

_mats = {}


def mat(name, base, metal=0.0, rough=0.5, emit=None, strength=0.0, alpha=1.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1.0)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    _mats[name] = m
    return m


def M():
    """The scene's materials, made once."""
    return {
        "steel": mat("steel", (0.35, 0.37, 0.42), metal=0.6, rough=0.4),
        "dark_steel": mat("dark_steel", (0.16, 0.17, 0.20), metal=0.5, rough=0.5),
        "lining": mat("lining", (0.42, 0.30, 0.25), rough=0.85),
        "charge": mat("charge", (0.20, 0.17, 0.14), rough=0.95),
        "quartz": mat("quartz", (0.85, 0.83, 0.78), rough=0.6),
        "coke": mat("coke", (0.07, 0.07, 0.08), rough=0.8),
        "silicon": mat("silicon", (0.55, 0.58, 0.64), metal=0.9, rough=0.22),
        "electrode": mat("electrode", (0.06, 0.06, 0.07), rough=0.5),
        "cavity": mat("cavity", (1.0, 0.45, 0.12), rough=0.3, emit=(1.0, 0.38, 0.08), strength=2.2),
        "arc": mat("arc", (1.0, 0.95, 0.85), emit=(1.0, 0.92, 0.8), strength=14.0),
        "crust": mat("crust", (0.13, 0.11, 0.10), rough=0.9),
        "melt": mat("melt", (1.0, 0.6, 0.25), rough=0.3, emit=(1.0, 0.5, 0.15), strength=4.0),
        "sio": mat("sio_gas", (0.95, 0.85, 0.55), emit=(1.0, 0.8, 0.45), strength=1.5, alpha=0.6),
        "fume": mat("fume", (0.85, 0.86, 0.90), rough=0.7, alpha=0.55),
        "clean": mat("clean_gas", (0.95, 0.97, 1.0), rough=0.6, alpha=0.18),
        "dust": mat("microsilica", (0.62, 0.63, 0.66), rough=0.9),
        "cloth": mat("cloth", (0.85, 0.80, 0.70), rough=0.9),
        "glass": mat("clear_glass", (0.9, 0.93, 0.96), rough=0.05, alpha=0.02),
        "refractory": mat("refractory", (0.30, 0.26, 0.23), rough=0.8),
        "rubber": mat("belt", (0.08, 0.08, 0.09), rough=0.9),
        "pipe_glass": mat("pipe_glass", (0.55, 0.62, 0.72), rough=0.2, alpha=0.22),
        "hot_gas": mat("hot_gas", (1.0, 0.75, 0.45), emit=(1.0, 0.65, 0.35), strength=2.0, alpha=0.75),
    }


# ---- geometry helpers -----------------------------------------------------------------


def _name(obj, name):
    obj.name = name
    return obj


def _smooth(obj):
    """Smooth shading, with edges sharper than 40 degrees kept hard (cut faces stay flat)."""
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    except Exception:
        bpy.ops.object.shade_flat()


def cut(obj, z=0.0):
    """Remove the part of `obj` in front of the plane poly z = `z` and cap the opening, so the
    camera (on +z) sees inside. The object's transform is baked into its mesh first; parents are
    at the origin while the scene is built, so the plane is in world space."""
    me = obj.data
    me.transform(obj.matrix_basis)
    obj.matrix_basis = Matrix.Identity(4)
    bm = bmesh.new()
    bm.from_mesh(me)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    # poly z is -Blender y; the normal points to the side that is removed (poly z > z)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, -z, 0), plane_no=(0, -1, 0), clear_outer=True)
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    _smooth(obj)
    return obj


def box(name, lo, hi, m, parent=None):
    """An axis-aligned box from poly corner `lo` to `hi`."""
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    dx, dy, dz = (hi[i] - lo[i] for i in range(3))
    bpy.ops.mesh.primitive_cube_add(size=1, location=P(*c))
    o = _name(bpy.context.object, name)
    o.scale = Vector((dx, abs(dz), abs(dy)))  # Blender Y is poly -Z, Blender Z is poly Y
    o.data.materials.append(m)
    o.parent = parent
    return o


def disc(name, centre, radius, depth, m, parent=None, verts=96):
    """A solid cylinder standing on its axis (poly Y), centred at `centre`."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=P(*centre))
    o = _name(bpy.context.object, name)
    o.data.materials.append(m)
    o.parent = parent
    return o


def cup(name, base, radius, height, m, parent=None):
    """An open-topped cylinder (a ladle body): its wall only, from poly point `base` upward."""
    centre = (base[0], base[1] + height / 2, base[2])
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, radius=radius, depth=height, end_fill_type="NOTHING", location=P(*centre)
    )
    o = _name(bpy.context.object, name)
    o.data.materials.append(m)
    o.parent = parent
    return o


def wall(name, r_out, y0, y1, thick, m, parent=None):
    """A hollow cylinder wall (the furnace lining), `thick` mm, from poly y0 to y1."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=96, radius=r_out, depth=y1 - y0, end_fill_type="NOTHING", location=P(0, (y0 + y1) / 2, 0)
    )
    o = _name(bpy.context.object, name)
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = thick
    mod.offset = -1.0
    mod.use_rim = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(m)
    o.parent = parent
    return o


def ball(name, c, r, m, parent=None, segs=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=segs, ring_count=segs // 2, location=P(*c))
    o = _name(bpy.context.object, name)
    o.data.materials.append(m)
    o.parent = parent
    _smooth(o)
    return o


def rock(name, c, r, m, parent=None):
    """A lump: a low-poly ball, faceted like broken stone."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=P(*c))
    o = _name(bpy.context.object, name)
    o.scale = Vector((1.0, 0.8, 0.7))
    o.data.materials.append(m)
    o.parent = parent
    return o


def tube(name, a, b, r, m, parent=None, verts=16):
    """A cylinder of radius `r` from poly point `a` to `b`."""
    A, B = P(*a), P(*b)
    d = B - A
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(A + B) / 2)
    o = _name(bpy.context.object, name)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.data.materials.append(m)
    o.parent = parent
    return o


def empty(name, parent=None, loc=(0, 0, 0)):
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=loc)
    o = _name(bpy.context.object, name)
    o.parent = parent
    return o


def pivot(name, at, parent=None):
    """An empty at poly point `at`, for groups that scale about that point. Children must be
    built relative to it (see `rel`)."""
    return empty(name, parent, P(*at))


def rel(at, p):
    """Poly point `p` expressed relative to a pivot at poly point `at`."""
    return (p[0] - at[0], p[1] - at[1], p[2] - at[2])


def _interp(kind):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


def key(obj, frame, prop="location", value=None, linear=False):
    if value is not None:
        setattr(obj, prop, value)
    _interp("LINEAR" if linear else "BEZIER")
    obj.keyframe_insert(prop, frame=frame)


def _constant(obj, prop=None):
    """Make the keys on `obj`'s animation constant (switches, not ramps); only `prop` if given."""
    from bpy_extras import anim_utils

    ad = obj.animation_data
    if not ad or not ad.action:
        return
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        if prop is not None and fc.data_path != prop:
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def show(obj, intervals):
    """Switch `obj` on for each [f0, f1) interval, off (OFF scale) otherwise."""
    _interp("CONSTANT")
    obj.scale = (OFF, OFF, OFF)
    obj.keyframe_insert("scale", frame=0)
    for f0, f1 in intervals:
        obj.scale = (1, 1, 1)
        obj.keyframe_insert("scale", frame=f0)
        obj.scale = (OFF, OFF, OFF)
        obj.keyframe_insert("scale", frame=f1)
    _constant(obj, "scale")


def label(text, at, parent, intervals):
    """A tag the TUI pins at poly point `at`, shown during `intervals`."""
    e = empty("label:" + text.replace(" ", "_"), parent, P(*at))
    show(e, intervals)
    return e


def beat(i):
    """The whole of beat i as one interval."""
    return [(F(i, 0), F(i + 1, 0))]


def fly(obj, path, f0, f1, steps=6):
    """Move `obj` (a group whose children were built at the origin's frame) along `path`,
    linearly, from frame f0 to f1. Positions are offsets from where it was built."""
    for j in range(steps + 1):
        f = round(f0 + (f1 - f0) * j / steps)
        key(obj, f, "location", P(*along(path, j / steps)), linear=True)


# ---- the scene ------------------------------------------------------------------------


def build_furnace(root, m):
    """The submerged-arc furnace in section: lining, roof, charge, the liquid pool, three
    electrodes (two on the cut plane), a cavity and a crust under each front electrode."""
    g = empty("furnace", root)

    # Coplanar cut faces z-fight, so each part is cut a few mm further forward than the one behind.
    cut(disc("base", (0, 60, 0), R + 40, 120, m["steel"], g), 0.0)
    cut(wall("lining", R, 120, SHELL_TOP, LINE, m["lining"], g), 0.0)
    cut(disc("roof", (0, SHELL_TOP + 40, 0), R + 40, 80, m["steel"], g), 0.0)
    cut(disc("charge", (0, (POOL_TOP + BURDEN_TOP) / 2, 0), R - LINE, BURDEN_TOP - POOL_TOP, m["charge"], g), 3.0)
    label("burden: quartzite + coke", (-1150, 1500, 10), g, beat(0))

    # The pool grows while the cavities drip (beat 1) and drains during the tap (beat 3).
    pool = pivot("pool", (0, 120, 0), g)
    cut(disc("pool_si", rel((0, 120, 0), (0, (120 + POOL_TOP) / 2, 0)), R - LINE, POOL_TOP - 120, m["silicon"], pool), 4.0)
    key(pool, 0, "scale", (1, 1, 1))
    key(pool, F(1, 0.1), "scale", (1, 1, 1))
    key(pool, F(1, 0.95), "scale", (1, 1, 1.25))
    key(pool, F(3, 0.25), "scale", (1, 1, 1.25))
    key(pool, F(3, 0.95), "scale", (1, 1, 0.55))
    key(pool, F(6, 0), "scale", (1, 1, 0.55))
    label("liquid silicon pool", (-1250, 200, 10), g, beat(1))

    for i, x in enumerate(ELECS):
        cut(disc(f"electrode{i}", (x, (ELEC_TIP + 3100) / 2, 0), ELEC_R, 3100 - ELEC_TIP, m["electrode"], g, 48), 12.0)
    disc("electrode_back", (0, (ELEC_TIP + 3100) / 2, -650), ELEC_R, 3100 - ELEC_TIP, m["electrode"], g, 48)
    label("carbon electrode", (650, 1500, 20), g, beat(1))

    # Cavities open in beat 1 and stay open; each flickers with its arc.
    for i, x in enumerate(ELECS):
        cav = pivot(f"cavity{i}", (x, CAV_Y, 0), g)
        cut(ball(f"cavity{i}_gas", (0, 0, 0), CAV_R, m["cavity"], cav, 32), 9.0)
        arc = pivot(f"arc{i}", (x, ELEC_TIP, 0), g)
        tube(f"arc{i}_core", (0, 0, 14), (0, POOL_TOP + 20 - ELEC_TIP, 14), 22, m["arc"], arc, verts=8)
        key(cav, 0, "scale", (OFF, OFF, OFF))
        key(cav, F(1, 0.0), "scale", (0.3, 0.3, 0.3))
        key(cav, F(1, 0.3), "scale", (1, 1, 1))
        f, k = F(1, 0.3), 0
        while f < F(6, 0):
            s = (1.0, 1.04, 0.97, 1.02)[k % 4]
            key(cav, f, "scale", (s, s, s))
            f += 6
            k += 1
        _constant_until(cav, F(1, 0))
        show(arc, [(F(1, 0.05), F(6, 0))])
    label("gas cavity, above 1800 C", (-650, CAV_Y - 120, 20), g, beat(1))

    # Crust: a thin skin at first, swelling through beat 2; the left one is broken by the bar.
    for i, x in enumerate(ELECS):
        cr = pivot(f"crust{i}", (x, CAV_Y + 40, 0), g)
        cut(ball(f"crust{i}_shell", (0, 0, 0), CRUST_R, m["crust"], cr, 32), 6.0)
        key(cr, 0, "scale", (OFF, OFF, OFF))
        key(cr, F(1, 0.0), "scale", (0.82, 0.82, 0.82))
        key(cr, F(2, 0.0), "scale", (0.85, 0.85, 0.85))
        key(cr, F(2, 0.55), "scale", (1.45, 1.45, 1.45))
        if i == 0:
            key(cr, F(2, 0.74), "scale", (1.45, 1.45, 1.45))
            key(cr, F(2, 0.80), "scale", (0.9, 0.9, 0.9))
        key(cr, F(3, 0.0), "scale", (1.45 if i else 0.9,) * 3)
        key(cr, F(6, 0), "scale", (1.45 if i else 0.9,) * 3)
        _constant_until(cr, F(1, 0))
    label("crust: SiO2 + SiC + Si", (650 + 330, CAV_Y + 260, 20), g, beat(2))

    # Debris: chunks of the broken crust fall into the cavity.
    deb = empty("debris", g)
    for k in range(7):
        a = -0.9 + k * 0.3
        x0, y0 = ELECS[0] + 380 * math.sin(a), CAV_Y + 40 + 380 * math.cos(a)
        ch = empty(f"debris{k}", deb)
        rock(f"debris{k}_rock", (x0, y0, 30), 55, m["crust"], ch)
        key(ch, F(2, 0.76), "location", P(0, 0, 0))
        key(ch, F(2, 0.95), "location", P((ELECS[0] - x0) * 0.6, -(y0 - CAV_Y) * 0.9, 0), linear=True)
        show(ch, [(F(2, 0.76), F(2, 0.95))])

    # SiO gas rising out of the cavities in beat 1, and Si droplets falling to the pool.
    gas = empty("sio", g)
    for i, x in enumerate(ELECS):
        for k in range(8):
            b = empty(f"sio{i}_{k}", gas)
            dx = (-1) ** k * (60 + 25 * (k % 3))
            ball(f"sio{i}_{k}_ball", (x + dx, CAV_Y + CAV_R, 40), 38, m["sio"], b, 12)
            f0 = F(1, 0.25 + 0.085 * k)
            f1 = f0 + round(BEAT_FRAMES * 0.3)
            key(b, f0, "location", P(0, 0, 0))
            key(b, f1, "location", P(dx * 1.5, 700, 0), linear=True)
            show(b, [(f0, min(f1, F(2, 0)))])
        for k in range(6):
            d = empty(f"drop{i}_{k}", gas)
            ball(f"drop{i}_{k}_ball", (x + (k % 3 - 1) * 70, CAV_Y - CAV_R + 20, 40), 26, m["silicon"], d, 12)
            f0 = F(1, 0.3 + 0.11 * k)
            f1 = f0 + 22
            key(d, f0, "location", P(0, 0, 0))
            key(d, f1, "location", P(0, -(CAV_Y - CAV_R + 20 - POOL_TOP - 20), 0), linear=True)
            show(d, [(f0, min(f1, F(2, 0)))])
    label("SiO gas climbs into the charge", (-650 + 120, CAV_Y + CAV_R + 450, 40), g, [(F(1, 0.3), F(2, 0))])

    # Tracer lumps on the cut face: the burden sinks in beats 0-1, stalls under the crust in beat
    # 2 until the bar breaks it, then drops.
    tr = empty("tracers", g)
    spots = [(-1300, 1450), (-900, 1150), (-300, 1350), (200, 1480), (900, 1200), (1300, 1420), (-200, 1000), (300, 1080)]
    for k, (x, y) in enumerate(spots):
        t = empty(f"tracer{k}", tr)
        rock(f"tracer{k}_rock", (x, y, 20), 50, m["quartz"] if k % 2 else m["coke"], t)
        key(t, 0, "location", P(0, 0, 0))
        key(t, F(2, 0.0), "location", P(0, -220, 0), linear=True)
        key(t, F(2, 0.78), "location", P(0, -230, 0))
        key(t, F(2, 0.92), "location", P(0, -420, 0))
        key(t, F(6, 0), "location", P(0, -420, 0))

    # Stoking car: rolls along the roof to the left electrode, drives its bar into the crust.
    stoker = empty("stoker", g)
    bar_x = ELECS[0] - 300
    box("stoker_car", (bar_x - 160, SHELL_TOP + 80, -140), (bar_x + 160, SHELL_TOP + 190, 140), m["dark_steel"], stoker)
    for wx in (-110, 110):
        disc(f"stoker_wheel{wx}", (bar_x + wx, SHELL_TOP + 110, 150), 40, 30, m["steel"], stoker, 16)
    bar = empty("stoker_bar", stoker)
    tube("stoker_rod", (bar_x, SHELL_TOP + 190, 60), (bar_x, SHELL_TOP - 200, 60), 34, m["steel"], bar)
    label("stoking bar", (bar_x, SHELL_TOP - 200, 60), bar, [(F(2, 0.6), F(2, 0.9))])
    label("stoking car", (bar_x, SHELL_TOP + 190, 0), stoker, [(F(2, 0.35), F(2, 0.6))])
    key(stoker, F(2, 0.35), "location", P(-900, 0, 0))
    key(stoker, F(2, 0.55), "location", P(0, 0, 0))
    key(stoker, F(2, 0.95), "location", P(0, 0, 0))
    key(bar, F(2, 0.58), "location", P(0, 0, 0))
    key(bar, F(2, 0.72), "location", P(0, -(SHELL_TOP - 200 - (CAV_Y + 40 + CRUST_R * 1.45) + 60), 0))
    key(bar, F(2, 0.82), "location", P(0, -(SHELL_TOP - 200 - (CAV_Y + 40 + CRUST_R * 1.45) + 160), 0))
    key(bar, F(2, 0.95), "location", P(0, 0, 0))
    show(stoker, [(F(2, 0.35), F(3, 0))])
    return g


def build_feed(root, m):
    """Two hoppers on the roof. In beat 0 a stream of quartzite and coke lumps runs down each
    chute, through the roof and onto the burden."""
    g = empty("feed", root)
    falls = empty("falls", g)
    for side, (x, z) in enumerate(((-1250.0, -120.0), (1150.0, -160.0))):
        hx = x - 450 if side == 0 else x + 250
        box(f"hopper{side}", (hx - 220, 2500, z - 220), (hx + 220, 3150, z + 220), m["steel"], g)
        top = (hx, 2500, z)
        mouth = (x, SHELL_TOP + 80, z)
        tube(f"chute{side}", top, mouth, 120, m["pipe_glass"], g, verts=24)
        # what has landed: a heap under the chute, growing through the beat
        heap = pivot(f"heap{side}", (x, BURDEN_TOP, z + 60), g)
        cut(ball(f"heap{side}_pile", (0, 0, 0), 260, m["quartz"] if side else m["coke"], heap, 16), -z - 60 + 2.0)
        key(heap, 0, "scale", (1, 1, 0.25))
        key(heap, F(1, 0), "scale", (1, 1, 0.6))
        key(heap, F(6, 0), "scale", (1, 1, 0.6))
        path = [top, mouth, (x, BURDEN_TOP + 40, z)]
        for k in range(12):
            lump = empty(f"lump{side}_{k}", falls)
            rock(f"lump{side}_{k}_rock", top, 85, m["quartz"] if (k + side) % 3 else m["coke"], lump)
            f0 = F(0, 0.03 + 0.075 * k)
            f1 = f0 + 30
            rel_path = [rel(top, p) for p in path]
            fly(lump, rel_path, f0, f1, steps=4)
            show(lump, [(f0, min(f1, F(1, 0)))])
    label("hopper", (-1700, 3150, 0), g, beat(0))
    label("lumps drop onto the burden", (-1250, BURDEN_TOP + 120, -120), g, beat(0))
    return g


def build_tap(root, m):
    """The tap hole, launder, fume hood and ladle. Beat 3 lances the hole and the silicon runs;
    beat 5 carries the ladle to the casting bed."""
    g = empty("tap", root)
    box("launder", (R - 40, TAP_Y - 50, -80), (R + 600, TAP_Y, 80), m["refractory"], g)
    for zz in (-90, 80):
        box(f"launder_side{zz}", (R - 40, TAP_Y - 50, zz), (R + 600, TAP_Y + 40, zz + 10), m["refractory"], g)
    plug = empty("tap_plug", g)
    box("tap_plug_clay", (R - 30, TAP_Y, -45), (R + 40, TAP_Y + 70, 45), m["coke"], plug)
    show(plug, [(0, F(3, 0.2)), (F(4, 0), F(6, 0))])
    lance = empty("lance", g)
    tube("lance_rod", (R + 60, TAP_Y + 35, 0), (R + 900, TAP_Y + 200, 0), 18, m["steel"], lance)
    key(lance, F(3, 0.05), "location", P(500, 100, 0))
    key(lance, F(3, 0.17), "location", P(0, 0, 0))
    key(lance, F(3, 0.24), "location", P(500, 100, 0))
    show(lance, [(F(3, 0.05), F(3, 0.25))])
    label("tap hole", (R, TAP_Y + 40, 0), g, [(F(3, 0.0), F(3, 0.3))])

    # The doghouse hood over the spout, ducted up into the off-gas line.
    hx = R + 330
    box("hood_roof", (hx - 380, 1050, -320), (hx + 380, 1090, 320), m["steel"], g)
    for zz in (-320, 300):
        box(f"hood_side{zz}", (hx - 380, 700, zz), (hx + 380, 1090, zz + 20), m["steel"], g)
    tube("hood_duct", (hx, 1090, 0), (hx, 2000, -700), 110, m["steel"], g)
    label("fume hood", (hx + 380, 1090, 0), g, beat(3))

    stream = pivot("stream", (R + 10, TAP_Y + 10, 0), g)
    tube("stream_run", (0, 0, 0), (560, -20, 0), 32, m["melt"], stream, verts=12)
    tube("stream_fall", (560, -20, 0), (LADLE_X - 140 - R - 10, LADLE_TOP - 60 - TAP_Y - 10, 0), 30, m["melt"], stream, verts=12)
    key(stream, 0, "scale", (OFF, OFF, OFF))
    key(stream, F(3, 0.2), "scale", (OFF, 1, 1))
    key(stream, F(3, 0.3), "scale", (1, 1, 1))
    key(stream, F(3, 0.92), "scale", (1, 1, 1))
    key(stream, F(3, 0.98), "scale", (OFF, OFF, OFF))
    _constant_until(stream, F(3, 0.2))

    fume = empty("tap_fume", g)
    for k in range(7):
        f = empty(f"tap_fume{k}", fume)
        ball(f"tap_fume{k}_ball", (R + 200 + 40 * (k % 3), TAP_Y + 60, 0), 70, m["fume"], f, 12)
        f0 = F(3, 0.28 + 0.09 * k)
        f1 = f0 + round(BEAT_FRAMES * 0.22)
        key(f, f0, "location", P(0, 0, 0))
        key(f, f1, "location", P(120, 800, 0), linear=True)
        show(f, [(f0, min(f1, F(4, 0)))])

    # The ladle fills in beat 3; in beat 5 a crane lifts it to the casting bed and it pours.
    ladle = empty("ladle", g)
    cup("ladle_body", (LADLE_X, 0, 0), 380, LADLE_TOP, m["dark_steel"], ladle)
    disc("ladle_base", (LADLE_X, 15, 0), 380, 30, m["dark_steel"], ladle)
    fill = pivot("ladle_fill", (LADLE_X, 30, 0), ladle)
    disc("ladle_si", (0, (LADLE_TOP - 50) / 2, 0), 365, LADLE_TOP - 80, m["melt"], fill)
    key(fill, 0, "scale", (1, 1, OFF))
    key(fill, F(3, 0.25), "scale", (1, 1, OFF))
    key(fill, F(3, 0.95), "scale", (1, 1, 1))
    key(fill, F(5, 0.32), "scale", (1, 1, 1))
    key(fill, F(5, 0.55), "scale", (1, 1, 0.08))
    key(fill, F(6, 0), "scale", (1, 1, 0.08))
    label("ladle", (LADLE_X + 380, LADLE_TOP, 0), ladle, beat(3))
    lift = [(0, 0, 0), (0, 900, 0), (MOULD_X - 500 - LADLE_X, 900, 0), (MOULD_X - 500 - LADLE_X, 650, 0)]
    key(ladle, F(5, 0.0), "location", P(0, 0, 0))
    fly(ladle, lift, F(5, 0.04), F(5, 0.3), steps=3)
    key(ladle, F(6, 0) - 1, "location", P(*lift[-1]))
    show(ladle, [(F(3, 0.0), F(6, 0))])
    pour = pivot("pour", (MOULD_X - 500 + 370, 650 + LADLE_TOP, 0), g)
    tube("pour_fall", (0, 0, 0), (80, -(650 + LADLE_TOP - 110), 0), 30, m["melt"], pour, verts=12)
    show(pour, [(F(5, 0.32), F(5, 0.55))])
    return g


def _constant_until(obj, frame):
    """Make the keys of `obj` before `frame` constant (it pops on, then animates)."""
    from bpy_extras import anim_utils

    ad = obj.animation_data
    if not ad or not ad.action:
        return
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            if kp.co[0] < frame:
                kp.interpolation = "CONSTANT"


def build_offgas(root, m):
    """The off-gas duct from the roof to the bag house, the bags, the microsilica hopper and the
    stack. In beat 4 gas climbs out of the burden into the duct; the bags catch the fume and
    clean gas leaves the stack."""
    g = empty("offgas", root)
    path = [
        (DUCT_X, SHELL_TOP + 80, DUCT_Z),
        (DUCT_X, DUCT_Y, DUCT_Z),
        (DUCT_X, DUCT_Y, BAG_Z),
        (BAG_X0 + 200, DUCT_Y, BAG_Z),
    ]
    # glass duct with steel bands, so the gas inside shows
    for a, b in zip(path, path[1:]):
        tube(f"duct_{a[0]:.0f}_{a[2]:.0f}", a, b, 140, m["pipe_glass"], g, verts=24)
        for k in range(1, 4):
            u = k / 4
            c = tuple(a[i] + (b[i] - a[i]) * u for i in range(3))
            d = [b[i] - a[i] for i in range(3)]
            n = math.sqrt(sum(v * v for v in d)) or 1.0
            e = tuple(c[i] + d[i] / n * 25 for i in range(3))
            tube(f"band_{c[0]:.0f}_{c[1]:.0f}_{c[2]:.0f}", c, e, 155, m["steel"], g, verts=24)
    for c in path[1:3]:
        ball(f"duct_elbow_{c[2]:.0f}", c, 150, m["steel"], g)
    label("off-gas duct", (DUCT_X, DUCT_Y + 150, (DUCT_Z + BAG_Z) / 2), g, beat(4))

    box("bag_house", (BAG_X0, 500, BAG_Z - 600), (BAG_X1, 2700, BAG_Z + 600), m["glass"], g)
    for r in (BAG_Z - 300.0, BAG_Z, BAG_Z + 300.0):
        for c in range(6):
            x = BAG_X0 + 175 + c * 150
            tube(f"bag_{r:+.0f}_{c}", (x, 800, r), (x, 2500, r), 45, m["cloth"], g, verts=12)
    label("bag filters", (BAG_X1, 1900, BAG_Z + 600), g, beat(4))
    # the hopper under the bags fills with microsilica
    box("bag_hopper", (BAG_X0 + 100, 300, BAG_Z - 500), (BAG_X1 - 100, 500, BAG_Z + 500), m["dark_steel"], g)
    for lx in (BAG_X0 + 150, BAG_X1 - 150):
        for lz in (BAG_Z - 450, BAG_Z + 450):
            box(f"bag_leg{lx}_{lz}", (lx - 40, 0, lz - 40), (lx + 40, 300, lz + 40), m["steel"], g)
    dust = pivot("dust", (BAG_X0, 500, BAG_Z), g)
    box("dust_pile", rel((BAG_X0, 500, BAG_Z), (BAG_X0 + 60, 500, BAG_Z - 560)), rel((BAG_X0, 500, BAG_Z), (BAG_X1 - 60, 800, BAG_Z + 560)), m["dust"], dust)
    key(dust, 0, "scale", (1, 1, 0.15))
    key(dust, F(4, 0.2), "scale", (1, 1, 0.15))
    key(dust, F(4, 0.95), "scale", (1, 1, 1))
    key(dust, F(6, 0), "scale", (1, 1, 1))
    label("microsilica, sold", (BAG_X1 - 200, 700, BAG_Z + 600), g, beat(4))
    tube("stack", (STACK_X, 2700, BAG_Z), (STACK_X, 3900, BAG_Z), 120, m["steel"], g)
    label("stack: clean gas", (STACK_X, 3900, BAG_Z), g, beat(4))

    # gas leaving the burden (inside the roof, visible through the cut) into the duct
    puffs = empty("puffs", g)
    full = [(DUCT_X - 400, BURDEN_TOP + 40, -60), (DUCT_X, SHELL_TOP - 40, DUCT_Z)] + path
    for i in range(12):
        p = empty(f"puff{i}", puffs)
        ball(f"puff{i}_ball", full[0], 110, m["hot_gas"], p, 12)
        f0 = F(4, 0.02 + 0.07 * i)
        f1 = f0 + round(BEAT_FRAMES * 0.32)
        fly(p, [rel(full[0], q) for q in full], f0, f1, steps=6)
        show(p, [(f0, min(f1, F(5, 0)))])
    clean = empty("clean", g)
    for i in range(6):
        p = empty(f"clean{i}", clean)
        ball(f"clean{i}_ball", (STACK_X, 3900, BAG_Z), 110, m["clean"], p, 12)
        f0 = F(4, 0.3 + 0.1 * i)
        f1 = f0 + round(BEAT_FRAMES * 0.25)
        key(p, f0, "location", P(0, 0, 0))
        key(p, f1, "location", P(250, 900, 0), linear=True)
        show(p, [(f0, min(f1, F(5, 0)))])
    return g


def build_product(root, m):
    """The casting bed, the crusher and the product bin, in front of the furnace. In beat 5 the
    slab sets in the bed, rides the belt into the crusher and comes out as lumps."""
    g = empty("product", root)
    mx, mz = MOULD_X, CAST_Z
    box("mould", (mx - 500, 0, mz - 350), (mx + 500, 60, mz + 350), m["dark_steel"], g)
    for zz in (mz - 350, mz + 330):
        box(f"mould_wall{zz}", (mx - 500, 60, zz), (mx + 500, 140, zz + 20), m["dark_steel"], g)
    label("casting bed", (mx - 500, 140, mz + 350), g, beat(5))

    slab = pivot("slab", (mx, 60, mz), g)
    box("slab_si", (-460, 0, -310), (460, 70, 310), m["silicon"], slab)
    key(slab, 0, "scale", (OFF, OFF, OFF))
    key(slab, F(5, 0.33), "scale", (1, 1, OFF))
    key(slab, F(5, 0.55), "scale", (1, 1, 1))
    key(slab, F(5, 0.58), "location", P(mx, 60, mz))
    key(slab, F(5, 0.74), "location", P(CRUSH_X - 300, 260, mz), linear=True)
    key(slab, F(5, 0.75), "scale", (1, 1, 1))
    key(slab, F(5, 0.76), "scale", (OFF, OFF, OFF))
    _constant_until(slab, F(5, 0.33))

    box("belt", (mx + 500, 220, mz - 300), (CRUSH_X - 250, 260, mz + 300), m["rubber"], g)
    box("crusher_body", (CRUSH_X - 250, 0, mz - 380), (CRUSH_X + 250, 700, mz + 380), m["steel"], g)
    for k, dx in enumerate((-90, 90)):
        roll = empty(f"roll{k}", g, P(CRUSH_X + dx, 760, mz))
        tube(f"roll{k}_drum", (0, 0, -300), (0, 0, 300), 85, m["dark_steel"], roll, verts=24)
        key(roll, F(5, 0.5), "rotation_euler", (0, 0, 0))
        key(roll, F(5, 1.0), "rotation_euler", (0, (-1) ** k * 6 * math.pi, 0), linear=True)
    label("crusher", (CRUSH_X, 800, mz + 300), g, beat(5))

    box("bin_floor", (BIN_X0, 0, mz - 300), (BIN_X1, 40, mz + 300), m["steel"], g)
    box("bin_back", (BIN_X0, 40, mz - 300), (BIN_X1, 500, mz - 260), m["steel"], g)
    box("bin_left", (BIN_X0, 40, mz - 300), (BIN_X0 + 40, 500, mz + 300), m["steel"], g)
    box("bin_right", (BIN_X1 - 40, 40, mz - 300), (BIN_X1, 500, mz + 300), m["steel"], g)
    box("bin_front", (BIN_X0, 40, mz + 260), (BIN_X1, 260, mz + 300), m["steel"], g)
    tube("chute_out", (CRUSH_X + 250, 300, mz), (BIN_X0 + 80, 500, mz), 70, m["dark_steel"], g)
    label("product bin", (BIN_X1, 500, mz + 300), g, beat(5))

    lumps = empty("lumps", g)
    for i in range(14):
        lx = BIN_X0 + 110 + (i % 4) * 125
        lz = mz - 180 + ((i // 4) % 3) * 160
        ly = 90 + (i // 12) * 90
        l = empty(f"lump{i}", lumps)
        rock(f"product{i}_rock", (lx, ly, lz), 60, m["silicon"], l)
        f0 = F(5, 0.76 + 0.016 * i)
        key(l, f0, "location", P(CRUSH_X + 250 - lx, 650 - ly, mz - lz))
        key(l, f0 + 10, "location", P(0, 0, 0))
        show(l, [(f0, F(6, 0))])
    return g


def build_camera(root):
    """One pose per beat, held for the beat with a slow push-in, cutting at the beat boundary."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(POSES):
        cp, sp = math.cos(pitch), math.sin(pitch)
        for f, d in ((F(i, 0), dist * 1.04), (F(i + 1, 0) - 1, dist * 0.97)):
            e = (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))
            key(target, f, "location", P(*t), linear=True)
            key(eye, f, "location", P(*e), linear=True)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 0
    scene.frame_end = BEAT_FRAMES * BEATS
    _mats.clear()
    m = M()
    root = empty("sand_overview")
    build_furnace(root, m)
    build_feed(root, m)
    build_tap(root, m)
    build_offgas(root, m)
    build_product(root, m)
    build_camera(root)


def export():
    os.makedirs(os.path.dirname(GLB_OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    bpy.ops.export_scene.gltf(
        filepath=GLB_OUT,
        export_format="GLB",
        export_yup=True,
        export_animations=True,
        export_force_sampling=True,
        export_frame_step=1,
        export_cameras=False,
        export_lights=False,
        use_selection=False,
    )
    print("exported", GLB_OUT)


if __name__ == "__main__":
    build()
    export()
