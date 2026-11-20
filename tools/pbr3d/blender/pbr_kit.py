"""Shared Blender helpers for the pbr3d pictures of the fab pages.

Each page script (fab_*.py, sand_*.py) builds its scenes with these: materials, primitives, keyed
motion, the start/finish/camera plumbing. Units are millimetres, Y up (see P). One beat is one
second at 24 fps, so beat i covers frames 24*i .. 24*i + 24, and pbr3d plays the file at
t = beat + local seconds. Constant switches (show) and eased keys (track, key) make things
appear, move and leave within a beat.
"""

import math
import os

import bpy
from mathutils import Vector

FPS = 24
BEAT_FRAMES = 24
OFF = 1e-5  # not zero: the glTF exporter divides by parent scale, so a zero group would zero its children

HERE = os.path.dirname(os.path.abspath(__file__))
PBR_DIR = os.path.normpath(os.path.join(HERE, ".."))

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


# ---- geometry helpers -----------------------------------------------------------------


def _name(obj, name):
    obj.name = name
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


def disc(name, centre, radius, depth, m, parent=None):
    """A solid cylinder standing on its axis (poly Y), centred at `centre`."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=radius, depth=depth, location=P(*centre))
    o = _name(bpy.context.object, name)
    o.data.materials.append(m)
    o.parent = parent
    return o


def boxg(name, lo, hi, m, parent=None):
    """A box inside its own empty: the empty can be keyed or shown without losing the box's size."""
    g = empty(name, parent)
    box(f"{name}_box", lo, hi, m, g)
    return g


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


def ball(name, c, r, m, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=24, ring_count=12, location=P(*c))
    o = _name(bpy.context.object, name)
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


def _interp(kind):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


def key(obj, frame, prop="location", value=None, linear=False):
    if value is not None:
        setattr(obj, prop, value)
    _interp("LINEAR" if linear else "BEZIER")
    obj.keyframe_insert(prop, frame=frame)


def _constant(obj):
    """Make every key on `obj`'s animation constant (a switch, not a ramp)."""
    from bpy_extras import anim_utils

    ad = obj.animation_data
    if not ad or not ad.action:
        return
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def show(group, intervals):
    """Switch a group on for each [f0, f1) interval, off (OFF scale) otherwise."""
    _interp("CONSTANT")
    group.scale = (OFF, OFF, OFF)
    group.keyframe_insert("scale", frame=0)
    for f0, f1 in intervals:
        group.scale = (1, 1, 1)
        group.keyframe_insert("scale", frame=f0)
        group.scale = (OFF, OFF, OFF)
        group.keyframe_insert("scale", frame=f1)
    _constant(group)


# ---- shared scene pieces ----------------------------------------------------------------


# ---- motion helpers ------------------------------------------------------------------------


def travel(obj, path, f0, f1, steps=4):
    """Move `obj` along the poly polyline `path` from frame f0 to f1, keyed at `steps` points."""
    for j in range(steps + 1):
        f = round(f0 + (f1 - f0) * j / steps)
        key(obj, f, "location", P(*along(path, j / steps)), linear=True)


def track(obj, pts, prop="scale", linear=False):
    """Eased keys: a list of (frame, value) pairs for one property."""
    for f, v in pts:
        key(obj, f, prop, v, linear)


def envelope(obj, spans):
    """Scale 1 inside each span (f_in, f_full, f_out, f_gone), OFF otherwise, eased on the ramps."""
    pts = []
    off = (OFF, OFF, OFF)
    for f_in, f_full, f_out, f_gone in spans:
        pts += [(f_in, off), (f_full, (1, 1, 1)), (f_out, (1, 1, 1)), (f_gone, off)]
    pts.sort(key=lambda p: p[0])
    clean = []
    for f, v in pts:
        if clean and clean[-1][0] == f:
            clean[-1] = (f, v)
        else:
            clean.append((f, v))
    track(obj, clean)


def flicker(obj, f0, f1, amps=(1.0, 1.10, 0.94, 1.05, 0.97), every=4, base=1.0):
    """A scale flicker on `obj` between f0 and f1."""
    f, k = f0, 0
    while f <= f1:
        s = base * amps[k % len(amps)]
        key(obj, f, "scale", (s, s, s))
        f += every
        k += 1


def wobble(obj, f0, f1, dy, every=6):
    """An up-and-down bob of `obj` (an empty at the origin) in poly y, keyed every `every` frames."""
    f, up = f0, True
    while f <= f1:
        key(obj, f, "location", P(0, dy if up else 0, 0))
        up = not up
        f += every


def spin(obj, f0, f1, turns=1.0, axis=2):
    """Rotate `obj` about one axis (0 = x, 1 = y, 2 = z) from f0 to f1, linearly."""
    rot = [0.0, 0.0, 0.0]
    key(obj, f0, "rotation_euler", tuple(rot))
    rot[axis] = 2 * math.pi * turns
    key(obj, f1, "rotation_euler", tuple(rot), linear=True)


def grow_bar(root, name, x0, x1, h, m, f0, f1, z0=-150, z1=150):
    """A bar standing on the floor (poly y = 0), growing from zero between frames f0 and f1."""
    grp = empty(name, root)
    box(f"{name}_bar", (x0, 0, z0), (x1, h, z1), m, grp)
    key(grp, f0, "scale", (1, 1, 0.001))
    key(grp, f1, "scale", (1, 1, 1))
    return grp


def marker(root, name, x, h, m, r=50):
    """A small sphere that rides a bar's top; move it with travel() or keys."""
    return ball(name, (x, h, 0), r, m, root)


def ring(n, r):
    """n (x, z) points on a circle of radius r about the furnace axis, for spacing things round it."""
    return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def start(name, beats):
    """A fresh Blender file: `beats` one-second beats at 24 fps, and its root empty."""
    _mats.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 0
    scene.frame_end = BEAT_FRAMES * beats
    return empty(f"fab_{name}")


def camera(root, poses, cut=False):
    """Camera keys: one (target, distance, yaw, pitch) per beat. By default the camera glides from
    each beat's pose toward the next, keyed at the middle of the beat. With `cut=True` each pose
    holds for its whole beat and the camera cuts at the beat boundary (as sand_zooms.camera does);
    gliding between poses with different yaw orbits the subject, which reads as the scene spinning."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        cp, sp = math.cos(pitch), math.sin(pitch)
        e = (t[0] + dist * cp * math.sin(yaw), t[1] + dist * sp, t[2] + dist * cp * math.cos(yaw))
        frames = (BEAT_FRAMES * i, BEAT_FRAMES * (i + 1) - 1) if cut else (BEAT_FRAMES * i + BEAT_FRAMES // 2,)
        for f in frames:
            key(target, f, "location", P(*t), linear=cut)
            key(eye, f, "location", P(*e), linear=cut)


def finish(name):
    """Save the Blender file beside this script and export the GLB pbr3d embeds."""
    os.makedirs(os.path.join(PBR_DIR, "assets"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{name}.blend"))
    glb = os.path.join(PBR_DIR, "assets", f"{name}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb,
        export_format="GLB",
        export_yup=True,
        export_animations=True,
        export_force_sampling=True,
        export_frame_step=1,
        export_cameras=False,
        export_lights=False,
        use_selection=False,
    )
    print("exported", glb)
