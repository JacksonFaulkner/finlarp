"""The WAFER overview, authored in Blender and exported for pbr3d.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/wafer_overview.py

It writes:
  blender/wafer_overview.blend   open it in Blender to edit by hand
  assets/wafer_overview.glb      what pbr3d embeds and plays back

Units are millimetres, Y up in the scene. Blender is Z up, so P(x, y, z) places a point at
Blender (x, -z, y); the glTF export turns it back into (x, y, z).

The wafer is a 300 mm disc, 775 um thick on the datasheet. It is drawn 6 mm thick, about
8x exaggerated, so the epi layer and the bevel read at overview distance.

Time: one beat is one second at 24 fps, so beat i covers frames 24*i .. 24*i + 24, and
pbr3d samples the file at t = beat + local seconds.

Beats (match the WAFER overview page):
  0 polished   the blank disc, mirror top face
  1 epi or SOI a device layer appears on top
  2 inspect    a scan bar crosses the disc
  3 pack       the disc slides into a FOUP
"""

import math
import os

import bpy
from mathutils import Vector

FPS = 24
BEAT_FRAMES = 24
BEATS = 4
OFF = 1e-5  # not zero: the glTF exporter divides by parent scale, so a zero group would zero its children

HERE = os.path.dirname(os.path.abspath(__file__))
PBR_DIR = os.path.normpath(os.path.join(HERE, ".."))
BLEND_OUT = os.path.join(HERE, "wafer_overview.blend")
GLB_OUT = os.path.join(PBR_DIR, "assets", "wafer_overview.glb")

RADIUS = 150.0
THICK = 6.0
FOUP_X = 480.0
FOUP_HALF = 170.0
FOUP_H = 330.0

# (camera target, distance, yaw, pitch), one per beat, as the poly3d overviews key them
POSES = [
    ((0.0, 30.0, 0.0), 600.0, 0.60, 0.45),
    ((60.0, 6.0, 0.0), 520.0, 0.80, 0.35),
    ((0.0, 10.0, 0.0), 520.0, 0.30, 1.05),
    ((300.0, 60.0, 0.0), 1200.0, 0.50, 0.35),
]

def P(x, y, z):
    """A point in the scene's Y-up millimetres as a Blender Z-up vector."""
    return Vector((x, -z, y))


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


# ---- helpers --------------------------------------------------------------------------


def _name(obj, name):
    obj.name = name
    return obj


def box(name, lo, hi, m, parent=None):
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    dx, dy, dz = (hi[i] - lo[i] for i in range(3))
    bpy.ops.mesh.primitive_cube_add(size=1, location=P(*c))
    o = _name(bpy.context.object, name)
    o.scale = Vector((dx, abs(dz), abs(dy)))
    o.data.materials.append(m)
    o.parent = parent
    return o


def disc(name, centre, radius, depth, m, parent=None, bevel=0.0):
    """A disc lying flat (axis = poly Y). `bevel` rounds the rim, applied to the mesh."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=radius, depth=depth, location=P(*centre))
    o = _name(bpy.context.object, name)
    o.data.materials.append(m)
    if bevel > 0:
        bev = o.modifiers.new("Rim", "BEVEL")
        bev.width = bevel
        bev.segments = 3
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=bev.name)
    o.parent = parent
    return o


def empty(name, parent=None, loc=(0, 0, 0)):
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=loc)
    o = _name(bpy.context.object, name)
    o.parent = parent
    return o


def key(obj, frame, prop="location", value=None, linear=False):
    if value is not None:
        setattr(obj, prop, value)
    _interp("LINEAR" if linear else "BEZIER")
    obj.keyframe_insert(prop, frame=frame)


def _interp(kind):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


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


# ---- the scene ------------------------------------------------------------------------


def build_wafer(root):
    """The disc, notch and epi layer ride one holder, so the whole wafer can move (beat 3)."""
    holder = empty("wafer", root)
    silicon = mat("silicon_mirror", (0.50, 0.53, 0.58), metal=0.9, rough=0.16)
    notch = mat("notch", (0.03, 0.03, 0.04), rough=0.8)
    epi = mat("epi_layer", (0.62, 0.58, 0.52), metal=0.3, rough=0.4)

    disc("disc", (0, THICK / 2, 0), RADIUS, THICK, silicon, holder, bevel=1.5)
    # the flat-less notch: a small dark cut on the rim, as the datasheet orients it
    box("notch", (-6, THICK / 2 - 1, -RADIUS - 1), (6, THICK / 2 + 1, -RADIUS + 9), notch, holder)

    # epi (or SOI) layer on the top face, beat 1 on
    layer = empty("epi", holder)
    disc("epi_disc", (0, THICK + 0.75, 0), RADIUS - 1, 1.5, epi, layer)
    show(layer, [(BEAT_FRAMES, 4 * BEAT_FRAMES)])

    # the wafer slides into the FOUP during beat 3
    key(holder, 3 * BEAT_FRAMES, "location", (0, 0, 0))
    key(holder, 4 * BEAT_FRAMES - 1, "location", P(FOUP_X, 60, 0), linear=True)
    return holder


def build_scan(root):
    """A scan bar crosses the disc during beat 2 (the page's 'scan bar')."""
    grp = empty("scan", root)
    cyan = mat("scan_bar", (0.4, 0.9, 1.0), rough=0.3, emit=(0.4, 0.9, 1.0), strength=2.0)
    bar = box("scan_bar", (-2, 12, -RADIUS - 5), (2, 16, RADIUS + 5), cyan, grp)
    key(bar, 2 * BEAT_FRAMES, "location", P(-RADIUS - 20, 0, 0))
    key(bar, 3 * BEAT_FRAMES - 1, "location", P(RADIUS + 20, 0, 0), linear=True)
    show(grp, [(2 * BEAT_FRAMES, 3 * BEAT_FRAMES)])
    return grp


def build_foup(root):
    """A FOUP: a base plate and four glass walls, shown during beat 3."""
    grp = empty("foup", root)
    steel = mat("foup_base", (0.30, 0.32, 0.36), metal=0.6, rough=0.4)
    glass = mat("foup_glass", (0.85, 0.92, 1.0), rough=0.05, alpha=0.22)
    cx = FOUP_X
    h = FOUP_HALF
    box("foup_floor", (cx - h, 0, -h), (cx + h, 6, h), steel, grp)
    box("foup_wall_a", (cx - h, 6, -h), (cx + h, FOUP_H, -h + 5), glass, grp)
    box("foup_wall_b", (cx - h, 6, h - 5), (cx + h, FOUP_H, h), glass, grp)
    box("foup_wall_c", (cx - h, 6, -h), (cx - h + 5, FOUP_H, h), glass, grp)
    box("foup_wall_d", (cx + h - 5, 6, -h), (cx + h, FOUP_H, h), glass, grp)
    show(grp, [(3 * BEAT_FRAMES, 4 * BEAT_FRAMES)])
    return grp


def build_camera(root):
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(POSES):
        f = BEAT_FRAMES * i + BEAT_FRAMES // 2
        cp, sp = math.cos(pitch), math.sin(pitch)
        e = (t[0] + dist * cp * math.sin(yaw), t[1] + dist * sp, t[2] + dist * cp * math.cos(yaw))
        key(target, f, "location", P(*t))
        key(eye, f, "location", P(*e))


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 0
    scene.frame_end = BEAT_FRAMES * BEATS
    root = empty("wafer_overview")
    build_wafer(root)
    build_scan(root)
    build_foup(root)
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
