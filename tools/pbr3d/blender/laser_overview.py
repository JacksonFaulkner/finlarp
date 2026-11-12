"""The LASER overview, authored in Blender and exported for pbr3d.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/laser_overview.py

It writes two files next to this script's folder:
  blender/laser_overview.blend   open it in Blender to edit the scene by hand
  assets/laser_overview.glb      what pbr3d embeds and plays back

Coordinates: the numbers below are the poly3d link rig's (Y up, the same units the
LASER page's keyframes use). Blender is Z up, so P(x, y, z) places a point at
Blender (x, -z, y); the glTF export then turns it back into (x, y, z) for pbr3d.

Time: one beat is one second at 24 fps, so beat i covers frames 24*i .. 24*i + 24 and
pbr3d samples the file at t = beat + local seconds.

Animation is plain transforms, so it survives the glTF export:
  - groups are empties whose scale switches a station on and off (0 or 1)
  - the camera is two empties, CamTarget and CamEye, keyed once per beat
  - pulses and the lid are moved with location keys
"""

import math
import os

import bpy
from mathutils import Vector

FPS = 24
BEAT_FRAMES = 24
BEATS = 7

HERE = os.path.dirname(os.path.abspath(__file__))
PBR_DIR = os.path.normpath(os.path.join(HERE, ".."))
BLEND_OUT = os.path.join(HERE, "laser_overview.blend")
GLB_OUT = os.path.join(PBR_DIR, "assets", "laser_overview.glb")

LASER_Z = 5000.0
EML_X = -1700.0
SIPH = (0.0, 60.0, LASER_Z)
VCSEL = (1500.0, 200.0, LASER_Z)
EML = (-1450.0, 80.0, LASER_Z)
TX = (-60.0, 40.0, 0.0)

# The seven LASER beats: (camera target, distance, yaw, pitch), as the poly3d keyframes have them.
POSES = [
    (TX, 900.0, 0.55, 0.70),
    ((150.0, 30.0, 0.0), 700.0, 0.45, 0.55),
    (EML, 1500.0, 0.50, 0.50),
    ((-1300.0, 86.0, LASER_Z), 1300.0, 0.30, 0.25),
    (SIPH, 1500.0, 0.45, 0.70),
    (VCSEL, 1500.0, 0.45, 0.30),
    (EML, 1400.0, 0.60, 0.45),
]


def P(x, y, z):
    """A poly3d point as a Blender Z-up vector."""
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
    length = d.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=length, location=(A + B) / 2)
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
    """The interpolation new keys get (Blender 5 keeps keys in slotted actions, so set it on insert)."""
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


def key(obj, frame, prop="location", value=None, linear=False):
    if value is not None:
        setattr(obj, prop, value)
    _interp("LINEAR" if linear else "BEZIER")
    obj.keyframe_insert(prop, frame=frame)


OFF = 1e-5  # not zero: the glTF exporter divides by parent scale, so a zero group would zero its children


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
    """Switch a group on (scale 1) for each [f0, f1) interval, off (OFF) otherwise."""
    group.scale = (OFF, OFF, OFF)
    group.keyframe_insert("scale", frame=0)
    for f0, f1 in intervals:
        group.scale = (1, 1, 1)
        group.keyframe_insert("scale", frame=f0)
        group.scale = (OFF, OFF, OFF)
        group.keyframe_insert("scale", frame=f1)
    _constant(group)


# ---- the scene ------------------------------------------------------------------------


def build_module(root):
    """The transceiver module at the origin: board, tray, lid, driver, eight lasers and lenses."""
    g = empty("module", root)
    board = mat("board", (0.10, 0.22, 0.14), rough=0.6)
    steel = mat("shell", (0.35, 0.37, 0.42), metal=0.6, rough=0.4)
    gold = mat("gold", (0.85, 0.70, 0.30), metal=1.0, rough=0.3)
    copper = mat("copper", (0.80, 0.45, 0.25), metal=1.0, rough=0.35)
    chip = mat("chip", (0.12, 0.12, 0.14), rough=0.4, emit=(0.3, 0.6, 1.0), strength=0.25)
    laser_m = mat("laser", (0.8, 0.3, 0.2), rough=0.3, emit=(1.0, 0.25, 0.1), strength=1.2)
    glass = mat("glass", (0.9, 0.95, 1.0), rough=0.05, alpha=0.25)
    smf = mat("fibre", (0.95, 0.85, 0.40), rough=0.4)

    box("board", (-1100, -24, -360), (0, 0, 360), board, g)
    box("substrate", (-950, 0, -200), (-550, 10, 200), mat("substrate", (0.55, 0.55, 0.6), rough=0.5), g)
    box("asic", (-900, 10, -150), (-600, 40, 150), chip, g)
    for i in range(8):
        z = -56 + i * 16
        box(f"trace{i}", (-550, 0, z - 3), (-300, 1.5, z + 3), copper, g)
    box("panel_low", (0, 0, -360), (14, 170, -70), steel, g)
    box("panel_high", (0, 110, -70), (14, 170, 70), steel, g)
    box("tray_floor", (-300, 6, -65), (300, 10, 65), steel, g)
    box("tray_back", (-300, 6, -65), (300, 40, -61), steel, g)
    box("tray_end", (290, 6, -65), (300, 86, 65), steel, g)
    box("pcb", (-295, 10, -58), (240, 14, 58), board, g)
    for i in range(6):
        z = -45 + i * 18
        box(f"pad{i}", (-300, 9, z - 5), (-272, 15, z + 5), gold, g)

    # the lid slides off during beat 0
    lid_holder = empty("lid", g)
    box("lid", (-300, 82, -65), (300, 86, 65), steel, lid_holder)
    key(lid_holder, 0, "location", (0, 0, 0))
    key(lid_holder, 20, "location", P(0, 110, 0))

    box("driver", (-40, 14, 10), (0, 22, 50), chip, g)
    box("tia", (-40, 14, -50), (0, 22, -10), chip, g)
    for i in range(8):
        z = 10 + i * 5.7
        box(f"laser{i}", (80, 14, z - 2.5), (110, 24, z + 2.5), laser_m, g)
        ball(f"lens{i}", (140, 22, z), 5.0, glass, g)
    box("ribbon", (150, 20, -56), (250, 24, 56), smf, g)
    box("mpo", (250, 26, -40), (290, 66, 40), mat("mpo", (0.2, 0.2, 0.22), rough=0.4, emit=(0.4, 0.3, 0.1), strength=0.3), g)
    tube("cable", (290, 46, 0), (900, 46, 0), 14, mat("coating", (0.95, 0.80, 0.20), rough=0.4), g)

    # the beam from each laser through its lens to the connector, beat 1
    beams = empty("beams", g)
    beam_m = mat("beam", (1.0, 0.2, 0.1), emit=(1.0, 0.2, 0.1), strength=2.5)
    for i in range(8):
        z = 10 + i * 5.7
        tube(f"beam{i}", (110, 22, z), (250, 30, 0), 1.5, beam_m, beams, verts=8)
    show(beams, [(BEAT_FRAMES, 2 * BEAT_FRAMES)])
    show(g, [(0, 2 * BEAT_FRAMES)])
    return g


def build_eml(root):
    g = empty("eml", root)
    x, y, z = EML_X, 0.0, LASER_Z
    inp = mat("inp", (0.60, 0.45, 0.35), rough=0.4)
    box("eml_chip", (x - 250, 0, z - 90), (x + 150, 80, z + 90), inp, g)
    box("eml_dfb", (x - 250, 80, z - 10), (x - 10, 92, z + 10), mat("dfb", (0.85, 0.45, 0.35), rough=0.3, emit=(1.0, 0.4, 0.2), strength=0.4), g)
    box("eml_eam", (x + 10, 80, z - 10), (x + 150, 92, z + 10), mat("eam", (0.45, 0.25, 0.75), rough=0.3, emit=(0.6, 0.3, 1.0), strength=0.3), g)
    gold = mat("gold", (0.85, 0.70, 0.30), metal=1.0, rough=0.3)
    box("eml_pad_a", (x - 200, 80, z + 18), (x - 60, 84, z + 70), gold, g)
    box("eml_pad_b", (x + 40, 80, z + 18), (x + 130, 84, z + 70), gold, g)
    ball("eml_lens", (x + 300, 86, z), 40, mat("glass", (0.9, 0.95, 1.0), rough=0.05, alpha=0.25), g)
    tube("eml_fibre", (x + 420, 86, z), (x + 900, 86, z), 30, mat("coating", (0.85, 0.90, 0.95), rough=0.4), g)

    # four PAM4 levels leaving the modulator, beat 3: four pulses along the fibre
    pulses = empty("pulses", g)
    pulse_m = mat("pulse", (0.4, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=2.0)
    for k in range(4):
        off = 40.0 * k
        p = ball(f"pulse{k}", (x + 420 + off, 86, z), 10 + 3 * k, pulse_m, pulses)
        key(p, 3 * BEAT_FRAMES, "location", P(x + 420 + off, 86, z))
        key(p, 4 * BEAT_FRAMES - 1, "location", P(x + 900 + off - 100, 86, z), linear=True)
    show(pulses, [(3 * BEAT_FRAMES, 4 * BEAT_FRAMES)])
    show(g, [(2 * BEAT_FRAMES, 4 * BEAT_FRAMES), (6 * BEAT_FRAMES, 7 * BEAT_FRAMES)])
    return g


def build_siph(root):
    g = empty("siph", root)
    x, y, z = SIPH
    box("si_slab", (x - 400, 0, z - 200), (x + 400, 40, z + 200), mat("silicon", (0.25, 0.30, 0.35), rough=0.3), g)
    box("cw_die", (x - 520, 10, z - 40), (x - 410, 50, z + 40), mat("cw", (0.6, 0.45, 0.35), rough=0.3, emit=(1.0, 0.4, 0.2), strength=0.5), g)
    wg = mat("waveguide", (0.8, 0.85, 0.95), rough=0.2)
    arm = mat("arm", (0.8, 0.85, 0.95), rough=0.2, emit=(0.4, 0.9, 1.0), strength=0.8)
    gold = mat("gold", (0.85, 0.70, 0.30), metal=1.0, rough=0.3)
    tube("wg_in", (x - 410, 42, z), (x - 250, 42, z), 4, wg, g)
    for sz in (-1.0, 1.0):
        tube(f"arm_in{sz:+.0f}", (x - 250, 42, z), (x - 160, 42, z + 60 * sz), 4, wg, g)
        tube(f"arm{sz:+.0f}", (x - 160, 42, z + 60 * sz), (x + 160, 42, z + 60 * sz), 4, arm, g)
        tube(f"arm_out{sz:+.0f}", (x + 160, 42, z + 60 * sz), (x + 250, 42, z), 4, wg, g)
        box(f"electrode{sz:+.0f}", (x - 130, 40, z + 60 * sz + 10 * sz - 8), (x + 130, 46, z + 60 * sz + 10 * sz + 8), gold, g)
    tube("wg_out", (x + 250, 42, z), (x + 330, 42, z), 4, wg, g)
    for i in range(6):
        gx = x + 335 + i * 9
        box(f"grating{i}", (gx, 40, z - 20), (gx + 4, 44, z + 20), wg, g)
    tube("siph_fibre", (x + 360, 60, z), (x + 440, 560, z), 20, mat("coating", (0.85, 0.90, 0.95), rough=0.4), g)
    show(g, [(4 * BEAT_FRAMES, 5 * BEAT_FRAMES)])
    return g


def build_vcsel(root):
    g = empty("vcsel", root)
    x, y, z = VCSEL
    box("vc_base", (x - 250, 0, z - 250), (x + 250, 40, z + 250), mat("vc_base", (0.40, 0.42, 0.48), rough=0.5), g)
    for i in range(18):
        y0 = 40 + i * 5
        if i == 9:
            c, m = (0.9, 0.4, 0.4), mat("active", (0.9, 0.4, 0.4), rough=0.3, emit=(1.0, 0.3, 0.2), strength=0.8)
        else:
            c = (0.70, 0.66, 0.60) if i % 2 == 0 else (0.45, 0.45, 0.55)
            m = mat(f"mirror{i % 2}", c, rough=0.3)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=50, depth=5, location=P(x, y0 + 2.5, z))
        o = _name(bpy.context.object, f"mesa{i}")
        o.data.materials.append(m)
        o.parent = g
    tube("vc_fibre", (x, 520, z), (x, 1000, z), 60, mat("om4", (0.30, 0.60, 0.90), rough=0.4), g)
    show(g, [(5 * BEAT_FRAMES, 6 * BEAT_FRAMES)])
    return g


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
    root = empty("laser_overview")
    build_module(root)
    build_eml(root)
    build_siph(root)
    build_vcsel(root)
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
