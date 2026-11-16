"""Part builders, wires, beads and camera for the SWITCHGEAR page (power_switchgear_{overview,zooms,sections}.py).

Units are centimetres, Y up, camera on +z (docs/diagram-pages.md). Every scene's root is scaled by its
own ROOT factor at the end (`scale_root`), so a 2.3 m cabinet stays far outside pbr3d's 40-unit near plane
and the whole campus stays inside its 40 m far plane. Labels, beads and the camera are children of the
root, so they scale with it.

  campus      utility yard (H-frame line, power transformers), standby generators, the switchgear house
              with two metal-clad lineups (A and B, mirror images) under an open-fronted bus duct, the
              unit substations (MV switch, cast-resin transformer, 480 V board) and the data hall
              (UPS cabinets, A and B busways over three rack rows). Returns the paths power runs along.
  cabinet     one lineup cabinet seen from the front: relay panel, an open breaker compartment with the
              withdrawable vacuum breaker (three bottles cut open), indicator flags, cable compartment.
  interrupter a vacuum bottle cut down its axis: ceramic body, fixed and moving contacts, vapour shield,
              bellows; the moving contact and its stem are one group so it can part.
  side        a metal-clad cabinet cut through its middle phase, side on: relay, breaker truck with its
              stored-energy mechanism, bottle, stabs, bus bars in section, CT, cable termination.
  acb         a 480 V air circuit breaker cut open: contacts, moving arm, arc runners, arc chute.
  transformer a dry-type unit-substation transformer cut open: core legs and yokes, LV and HV coils.
  ats         a double-throw transfer switch: utility and generator contacts, one blade, a motor operator.
  genset      a diesel generator set with its enclosure cut away.

Wires are the photodiode page's segmented wires (a tube per segment, a ball at each joint), arched with
`curve_pts`; beads (`run`, `beads`) ride them to show power moving.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, BEAT_FRAMES, ball, box, cut, empty, fly, key, show, tube  # noqa: E402
import pbr_kit  # noqa: E402
from pbr_kit import mat  # noqa: E402

# ---- materials ------------------------------------------------------------------------------


def materials():
    pbr_kit._mats.clear()
    return {
        "paint": mat("sw_paint", (0.60, 0.64, 0.66), metal=0.3, rough=0.45),
        "paint_dk": mat("sw_paint_dk", (0.30, 0.33, 0.36), metal=0.3, rough=0.5),
        "interior": mat("sw_interior", (0.78, 0.79, 0.76), rough=0.6),
        "copper": mat("sw_copper", (0.92, 0.52, 0.30), metal=0.9, rough=0.28),
        "tin": mat("sw_tin", (0.80, 0.82, 0.86), metal=0.9, rough=0.3),
        "cucr": mat("sw_cucr", (0.55, 0.36, 0.26), metal=0.8, rough=0.4),
        "ceramic": mat("sw_ceramic", (0.93, 0.91, 0.85), rough=0.45),
        "porcelain": mat("sw_porcelain", (0.50, 0.24, 0.13), rough=0.3),
        "epoxy": mat("sw_epoxy", (0.24, 0.26, 0.28), rough=0.5),
        "insul": mat("sw_insul", (0.86, 0.55, 0.20), rough=0.6),
        "cable": mat("sw_cable", (0.11, 0.11, 0.12), rough=0.7),
        "steel": mat("sw_steel", (0.62, 0.64, 0.68), metal=0.8, rough=0.35),
        "dark": mat("sw_dark", (0.13, 0.14, 0.16), metal=0.4, rough=0.5),
        "spring": mat("sw_spring", (0.74, 0.76, 0.80), metal=1.0, rough=0.25),
        "coil": mat("sw_coil", (0.85, 0.45, 0.22), metal=0.85, rough=0.35),
        "coil_lv": mat("sw_coil_lv", (0.78, 0.80, 0.84), metal=0.85, rough=0.3),
        "resin": mat("sw_resin", (0.36, 0.38, 0.42), rough=0.4),
        "core": mat("sw_core", (0.25, 0.27, 0.31), metal=0.7, rough=0.4),
        "tank": mat("sw_tank", (0.46, 0.52, 0.50), metal=0.4, rough=0.5),
        "concrete": mat("sw_concrete", (0.56, 0.56, 0.54), rough=0.9),
        "gravel": mat("sw_gravel", (0.42, 0.40, 0.37), rough=0.95),
        "ground": mat("sw_ground", (0.24, 0.28, 0.22), rough=0.95),
        "wall": mat("sw_wall", (0.74, 0.71, 0.64), rough=0.85),
        "floor": mat("sw_floor", (0.47, 0.48, 0.51), rough=0.7),
        "rack": mat("sw_rack", (0.10, 0.11, 0.12), metal=0.4, rough=0.45),
        "server": mat("sw_server", (0.28, 0.30, 0.33), metal=0.5, rough=0.4),
        "pcb": mat("sw_pcb", (0.10, 0.34, 0.20), rough=0.7),
        "gen": mat("sw_gen", (0.86, 0.70, 0.22), metal=0.3, rough=0.45),
        "engine": mat("sw_engine", (0.22, 0.30, 0.34), metal=0.5, rough=0.4),
        "relay": mat("sw_relay", (0.07, 0.07, 0.08), rough=0.4),
        "screen": mat("sw_screen", (0.15, 0.55, 0.35), emit=(0.15, 0.80, 0.42), strength=1.6),
        "screen_red": mat("sw_screen_red", (0.9, 0.15, 0.1), emit=(1.0, 0.15, 0.08), strength=3.0),
        "led_g": mat("sw_led_g", (0.2, 1.0, 0.3), emit=(0.2, 1.0, 0.3), strength=4.0),
        "led_r": mat("sw_led_r", (1.0, 0.15, 0.1), emit=(1.0, 0.12, 0.08), strength=5.0),
        "flag_closed": mat("sw_flag_closed", (0.9, 0.15, 0.12), emit=(0.9, 0.12, 0.1), strength=1.5),
        "flag_open": mat("sw_flag_open", (0.2, 0.85, 0.3), emit=(0.2, 0.85, 0.3), strength=1.5),
        "mv": mat("sw_mv", (1.0, 0.74, 0.22), emit=(1.0, 0.70, 0.18), strength=6.0),
        "lv": mat("sw_lv", (0.25, 0.85, 1.0), emit=(0.22, 0.82, 1.0), strength=6.0),
        "gen_e": mat("sw_gen_e", (0.35, 1.0, 0.35), emit=(0.3, 1.0, 0.3), strength=6.0),
        "fault": mat("sw_fault", (1.0, 0.12, 0.08), emit=(1.0, 0.10, 0.06), strength=7.0),
        "sig": mat("sw_sig", (1.0, 0.35, 0.95), emit=(1.0, 0.30, 0.95), strength=6.0),
        "arc": mat("sw_arc", (0.80, 0.88, 1.0), emit=(0.75, 0.85, 1.0), strength=14.0),
        "plasma": mat("sw_plasma", (1.0, 0.70, 0.30), emit=(1.0, 0.62, 0.22), strength=9.0),
        "molten": mat("sw_molten", (1.0, 0.55, 0.15), emit=(1.0, 0.5, 0.12), strength=6.0),
        "dead": mat("sw_dead", (0.45, 0.06, 0.05), emit=(0.55, 0.05, 0.03), strength=0.9),
        "hot": mat("sw_hot", (1.0, 0.5, 0.15), emit=(1.0, 0.45, 0.12), strength=2.5),
        "smoke": mat("sw_smoke", (0.32, 0.32, 0.34), rough=0.95),
        "vent": mat("sw_vent", (0.95, 0.80, 0.55), emit=(1.0, 0.7, 0.35), strength=3.0),
        "suit": mat("sw_suit", (0.20, 0.30, 0.55), rough=0.8),
        "visor": mat("sw_visor", (0.55, 0.62, 0.25), metal=0.5, rough=0.2),
        "skin": mat("sw_skin", (0.80, 0.62, 0.48), rough=0.7),
        "lock": mat("sw_lock", (0.85, 0.12, 0.10), rough=0.4),
        "tag": mat("sw_tag", (0.98, 0.85, 0.20), rough=0.6),
        "skid": mat("sw_skid", (0.24, 0.25, 0.28), metal=0.6, rough=0.45),
        "tyre": mat("sw_tyre", (0.06, 0.06, 0.06), rough=0.9),
        "cab": mat("sw_cab", (0.85, 0.85, 0.88), metal=0.3, rough=0.4),
        "chute": mat("sw_chute", (0.45, 0.20, 0.14), rough=0.7),
        "pathA": mat("sw_path_a", (1.0, 0.55, 0.15), emit=(1.0, 0.5, 0.12), strength=2.0),
        "pathB": mat("sw_path_b", (0.25, 0.60, 1.0), emit=(0.2, 0.55, 1.0), strength=2.0),
        "cloud": mat("sw_cloud", (0.65, 0.66, 0.70), rough=0.9),
    }


# ---- geometry ---------------------------------------------------------------------------------


def _link(name, me, m, parent):
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    O._smooth(o)
    return o


def pipe_v(name, y0, y1, ro, ri, m, parent=None, cx=0.0, cz=0.0, half=True, verts=40):
    """A hollow cylinder standing on y (axis at x = cx, z = cz). `half` keeps z <= cz and caps the cut
    faces, so the wall's section shows."""
    a0, a1 = (math.pi, 2 * math.pi) if half else (0.0, 2 * math.pi)
    n = verts // 2 if half else verts
    angles = [a0 + (a1 - a0) * i / n for i in range(n + 1 if half else n)]
    rings = [(y0, ro), (y1, ro), (y1, ri), (y0, ri)]
    vs = [tuple(P(cx + r * math.cos(t), y, cz + r * math.sin(t))) for y, r in rings for t in angles]
    k = len(angles)
    faces = []
    for a in range(4):
        b = (a + 1) % 4
        for i in (range(k - 1) if half else range(k)):
            j = (i + 1) % k
            faces.append((a * k + i, a * k + j, b * k + j, b * k + i))
    if half:
        for i in (0, k - 1):
            faces.append(tuple(a * k + i for a in range(4)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return _link(name, me, m, parent)


def rod(name, a, b, r, m, parent=None, verts=16, cz=None):
    """A solid cylinder from a to b, cut at z = `cz` when given (its axis should lie on that plane)."""
    o = tube(name, a, b, r, m, parent, verts)
    return cut(o, cz) if cz is not None else o


def ring_h(name, c, ro, ri, h, m, parent=None, half=True, verts=32):
    """A flat ring (a CT, a shed) lying level, centred at c, `h` thick."""
    return pipe_v(name, c[1] - h / 2, c[1] + h / 2, ro, ri, m, parent, c[0], c[2], half, verts)


def polyline(name, pts, r, m, parent=None):
    """A round wire through `pts` as one mesh (thin signal wires)."""
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = r
    cd.bevel_resolution = 1
    cd.use_fill_caps = True
    sp = cd.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        v = P(*p)
        sp.points[i].co = (v.x, v.y, v.z, 1.0)
    o = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(o)
    for s in bpy.context.selected_objects:
        s.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.object
    o.name = name
    o.data.materials.clear()
    o.data.materials.append(m)
    o.parent = parent
    return o


def wire(name, pts, r, m, parent=None, verts=10):
    """The photodiode page's wire: a tube per segment and a ball at each joint, so an arched run of
    points reads as one bent cable or bar."""
    g = empty(name, parent)
    for k in range(len(pts) - 1):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, m, g, verts)
        if k:
            ball(f"{name}_j{k}", pts[k], r, m, g, verts)
    return g


def curve_pts(a, b, lift, n=10):
    """Points on an arch from a to b, bowed by the offset vector `lift` at the middle."""
    out = []
    for k in range(n + 1):
        u = k / n
        w = 4 * u * (1 - u)
        out.append(tuple(a[i] + (b[i] - a[i]) * u + lift[i] * w for i in range(3)))
    return out


def sag(a, b, d, n=10):
    """A hanging conductor from a to b, sagging `d` at its middle."""
    return curve_pts(a, b, (0.0, -d, 0.0), n)


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def run(parent, name, pts, n, size, m, b, u0, u1, life, end=None):
    """`n` beads that each travel the absolute polyline `pts` over `life` frames, launched one after
    another between fractions u0 and u1 of beat `b`, each gone by frame `end` (default: the beat's end)."""
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    stop = F(b + 1, 0) if end is None else end
    for k in range(n):
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        if f0 >= stop:
            continue
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, m, e, 10)
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, min(16, len(pts) * 2)))
        show(e, [(f0, min(f1, stop))])
    return g


def beads(parent, name, pts, m, b, u0=0.0, u1=0.8, size=6.0, speed=20.0, gap=None, end=None, n=None):
    """Beads riding `pts` at `speed` cm a frame, launched through beat `b` from u0 to u1, spaced about
    `gap` cm apart along the path (or `n` of them)."""
    L = plen(pts)
    life = max(12, int(L / speed))
    if n is None:
        span = (u1 - u0) * BEAT_FRAMES * speed
        n = max(2, min(9, int(span / (gap or max(60.0, L / 3)))))
    return run(parent, name, pts, n, size, m, b, u0, u1, life, end)


def helix(name, c, r, y0, y1, turns, wr, m, parent=None, n_per=10):
    """A coil spring standing on y at (c.x, c.z)."""
    pts = []
    total = int(turns * n_per)
    for k in range(total + 1):
        t = k / total
        a = 2 * math.pi * turns * t
        pts.append((c[0] + r * math.cos(a), y0 + (y1 - y0) * t, c[2] + r * math.sin(a)))
    return polyline(name, pts, wr, m, parent)


def join(objs, name):
    """Merge meshes (same parent) into one object, for a leaner GLB."""
    objs = [o for o in objs if o is not None and o.type == "MESH"]
    if len(objs) < 2:
        return objs[0] if objs else None
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    return o


def ellipsoid(name, c, rx, ry, rz, m, parent=None, segs=16):
    o = ball(name, c, 1.0, m, parent, segs)
    o.scale = (rx, rz, ry)
    return o


def scale_root(root, s):
    root.scale = (s, s, s)


def hold_key(obj, f, prop, value):
    """A constant (stepped) key."""
    setattr(obj, prop, value)
    O._interp("CONSTANT")
    obj.keyframe_insert(prop, frame=f)


def move(obj, keys, linear=True):
    """Location keys (frame, poly offset) on a group built at the origin."""
    for f, off in keys:
        key(obj, f, "location", P(*off), linear=linear)


def turn(obj, keys):
    """Rotation keys (frame, angle in radians about poly z, counter-clockwise seen from the camera)."""
    obj.rotation_mode = "XYZ"
    for f, a in keys:
        obj.rotation_euler = (0.0, -a, 0.0)
        O._interp("LINEAR")
        obj.keyframe_insert("rotation_euler", frame=f)


def grow(obj, keys):
    """Scale keys (frame, (sx, sy, sz) in poly axes) on a pivot."""
    for f, s in keys:
        sx, sy, sz = (s, s, s) if isinstance(s, (int, float)) else s
        key(obj, f, "scale", (sx, sz, sy), linear=True)


# ---- the vacuum interrupter ---------------------------------------------------------------------


def interrupter(m, parent, c, s=1.0, name="vi", half=True):
    """A vacuum bottle standing on y, centred at c, cut at z = c.z. Base size (s = 1): ceramic body
    6 cm in radius and 18 cm long, contacts 3.6 cm in radius. Returns (points, moving group, arc group);
    the moving group holds the moving contact and its stem, at the origin, to be keyed down by `gap`."""
    cx, cy, cz = c

    def V(name_, y0, y1, ro, ri, mt, g=None):
        return pipe_v(f"{name}_{name_}", cy + s * y0, cy + s * y1, s * ro, s * ri, mt, g or parent, cx, cz, half, 40)

    def R(name_, y0, y1, r, mt, g=None, verts=24):
        return rod(f"{name}_{name_}", (cx, cy + s * y0, cz), (cx, cy + s * y1, cz), s * r, mt, g or parent, verts,
                   cz if half else None)

    V("shell_hi", 0.5, 9.0, 6.0, 5.3, m["ceramic"])
    V("shell_lo", -9.0, -0.5, 6.0, 5.3, m["ceramic"])
    V("flange", -0.5, 0.5, 6.5, 4.6, m["steel"])
    V("shield", -5.0, 5.0, 4.6, 4.3, m["tin"])
    R("cap_hi", 9.0, 9.8, 6.3, m["tin"], verts=32)
    R("cap_lo", -9.8, -9.0, 6.3, m["tin"], verts=32)
    R("fixed_stem", 0.9, 13.0, 1.4, m["copper"])
    R("fixed_contact", 0.25, 0.9, 3.6, m["copper"], verts=32)
    R("fixed_face", 0.0, 0.25, 3.6, m["cucr"], verts=32)
    for k in range(6):
        y = -8.8 + 0.55 * k
        V(f"bellows{k}", y, y + 0.3, 2.4, 1.5, m["steel"])
    R("guide", -11.0, -9.8, 2.2, m["epoxy"])
    mv = empty(f"{name}_moving", parent)
    R("moving_face", -0.25, 0.0, 3.6, m["cucr"], mv, 32)
    R("moving_contact", -0.9, -0.25, 3.6, m["copper"], mv, 32)
    R("moving_stem", -15.0, -0.9, 1.4, m["copper"], mv)
    arc = empty(f"{name}_arc", parent)
    o = ellipsoid(f"{name}_arc_glow", (cx, cy - s * 0.6, cz), s * 3.0, s * 0.9, s * 3.0, m["arc"], arc)
    if half:
        cut(o, cz + 0.02 * s)
    pts = {
        "top": (cx, cy + s * 13.0, cz),
        "bottom": (cx, cy - s * 15.0, cz),
        "gap": (cx, cy, cz),
        "shell": (cx - s * 6.0, cy + s * 4.0, cz),
        "contacts": (cx + s * 3.6, cy, cz),
        "shield": (cx + s * 4.6, cy + s * 3.0, cz),
        "bellows": (cx + s * 2.4, cy - s * 7.5, cz),
        "stem": (cx, cy - s * 12.0, cz),
        "r": s * 6.0,
    }
    return pts, mv, arc


def part(mv, arc, f, gap, s=1.0, arc_frames=6):
    """The contacts part at frame f: the moving group drops `gap` (scaled) and an arc glows for a few
    frames, then dies at the current zero."""
    move(mv, [(0, (0, 0, 0)), (f, (0, 0, 0)), (f + 3, (0, -gap * s, 0))])
    show(arc, [(f + 1, f + 1 + arc_frames)])


def close_again(mv, f, gap, s=1.0):
    move(mv, [(f, (0, -gap * s, 0)), (f + 3, (0, 0, 0))])


# ---- a lineup cabinet, seen from the front (campus scale) -----------------------------------------

CAB_W, CAB_H, CAB_D = 160.0, 236.0, 240.0
POLE_DX = 42.0
BOT_Y = 140.0          # bottle centres
BOT_S = 1.0
BUS_Y = (256.0, 272.0, 288.0)  # the three bus bars above the lineup
UP_Y = 162.0           # upper (bus) stab level
LO_Y = 127.0           # lower (cable) stab level


def cabinet(m, parent, x0, zf, kind, name, relay=True):
    """A metal-clad cabinet x0..x0+CAB_W, front face at z = zf, back at zf - CAB_D. The breaker
    compartment (y 84-172) is open, showing the withdrawable vacuum breaker: three bottles cut open on
    their axes, arms back to the stabs, the mechanism box with its flags. Returns its points and groups."""
    g = empty(f"{name}", parent)
    x1 = x0 + CAB_W
    c = x0 + CAB_W / 2
    zb = zf - CAB_D
    sh = []
    sh.append(box(f"{name}_plinth", (x0, 0, zb), (x1, 16, zf), m["dark"], g))
    sh.append(box(f"{name}_back", (x0, 16, zb), (x1, CAB_H, zb + 3), m["paint"], g))
    sh.append(box(f"{name}_side_l", (x0, 16, zb), (x0 + 2, CAB_H, zf), m["paint"], g))
    sh.append(box(f"{name}_side_r", (x1 - 2, 16, zb), (x1, CAB_H, zf), m["paint"], g))
    sh.append(box(f"{name}_top", (x0, CAB_H - 3, zb), (x1, CAB_H, zf), m["paint"], g))
    sh.append(box(f"{name}_cable_door", (x0 + 2, 16, zf - 3), (x1 - 2, 84, zf), m["paint"], g))
    for k in range(4):
        y = 30 + 11 * k
        sh.append(box(f"{name}_louvre{k}", (c - 40, y, zf), (c + 40, y + 4, zf + 1.2), m["paint_dk"], g))
    sh.append(box(f"{name}_shelf_lo", (x0 + 2, 81, zb), (x1 - 2, 84, zf), m["paint"], g))
    sh.append(box(f"{name}_shelf_hi", (x0 + 2, 172, zb), (x1 - 2, 175, zf), m["paint"], g))
    sh.append(box(f"{name}_relay_door", (x0 + 2, 175, zf - 3), (x1 - 2, CAB_H - 3, zf), m["paint"], g))
    # breaker compartment: light interior, shutter wall with six stab bushings
    sh.append(box(f"{name}_shutter", (x0 + 2, 84, zf - 165), (x1 - 2, 172, zf - 162), m["interior"], g))
    sh.append(box(f"{name}_side_il", (x0 + 2, 84, zf - 162), (x0 + 4, 172, zf - 3), m["interior"], g))
    sh.append(box(f"{name}_side_ir", (x1 - 4, 84, zf - 162), (x1 - 2, 172, zf - 3), m["interior"], g))
    for k in range(3):
        x = c + (k - 1) * POLE_DX
        for yy, tag in ((UP_Y, "u"), (LO_Y, "l")):
            sh.append(tube(f"{name}_stab{tag}{k}", (x, yy, zf - 162), (x, yy, zf - 148), 5.0, m["epoxy"], g, 16))
    # the breaker: carriage, mechanism box, flags
    sh.append(box(f"{name}_carriage", (c - 66, 84, zf - 140), (c + 66, 92, zf - 8), m["dark"], g))
    sh.append(box(f"{name}_mech", (c - 66, 92, zf - 120), (c + 66, 122, zf - 8), m["paint_dk"], g))
    sh.append(tube(f"{name}_btn_o", (c - 46, 108, zf - 8), (c - 46, 108, zf - 6.5), 3.0, m["flag_open"], g, 12))
    sh.append(tube(f"{name}_btn_i", (c - 36, 108, zf - 8), (c - 36, 108, zf - 6.5), 3.0, m["flag_closed"], g, 12))
    sh.append(box(f"{name}_spring_ind", (c + 26, 100, zf - 8), (c + 34, 112, zf - 6.6), m["tag"], g))
    sh.append(box(f"{name}_handle", (c + 44, 96, zf - 8), (c + 56, 99, zf - 2), m["steel"], g))
    closed = empty(f"{name}_flag_closed", g)
    box(f"{name}_flag_c", (c - 8, 102, zf - 8), (c + 8, 114, zf - 6.2), m["flag_closed"], closed)
    opened = empty(f"{name}_flag_open", g)
    box(f"{name}_flag_o", (c - 8, 102, zf - 8), (c + 8, 114, zf - 6.2), m["flag_open"], opened)
    # three poles
    cz = zf - 70
    mvs, arcs, tops = [], [], []
    for k in range(3):
        x = c + (k - 1) * POLE_DX
        pp, mv, arc = interrupter(m, g, (x, BOT_Y, cz), BOT_S, f"{name}_vi{k}")
        mvs.append(mv)
        arcs.append(arc)
        tops.append(pp)
        sh.append(rod(f"{name}_arm_u{k}", (x, BOT_Y + 13, cz), (x, UP_Y, cz), 1.8, m["copper"], g, 12))
        sh.append(tube(f"{name}_armz_u{k}", (x, UP_Y, cz - 1), (x, UP_Y, zf - 148), 2.2, m["copper"], g, 12))
        sh.append(tube(f"{name}_tulip_u{k}", (x, UP_Y, zf - 152), (x, UP_Y, zf - 140), 3.4, m["tin"], g, 12))
        sh.append(tube(f"{name}_armz_l{k}", (x + 2.5, LO_Y, cz), (x + 2.5, LO_Y, zf - 148), 2.2, m["copper"], g, 12))
        sh.append(tube(f"{name}_tulip_l{k}", (x + 2.5, LO_Y, zf - 152), (x + 2.5, LO_Y, zf - 140), 3.4, m["tin"], g, 12))
        sh.append(tube(f"{name}_shunt{k}", (x, LO_Y, cz), (x + 2.5, LO_Y, cz), 2.0, m["copper"], g, 10))
        sh.append(tube(f"{name}_pushrod{k}", (x, 122, cz), (x, BOT_Y - 15, cz), 1.6, m["insul"], g, 10))
    # relay
    pts = {}
    if relay:
        sh.append(box(f"{name}_relay", (c - 26, 186, zf), (c + 26, 226, zf + 5), m["relay"], g))
        sh.append(box(f"{name}_screen", (c - 18, 202, zf + 5), (c + 6, 220, zf + 5.6), m["screen"], g))
        for k in range(3):
            sh.append(box(f"{name}_led{k}", (c + 12, 192 + 9 * k, zf + 5), (c + 18, 197 + 9 * k, zf + 5.8), m["led_g"], g))
        trip = empty(f"{name}_relay_trip", g)
        box(f"{name}_screen_trip", (c - 18, 202, zf + 5.6), (c + 6, 220, zf + 6.2), m["screen_red"], trip)
        box(f"{name}_led_trip", (c + 12, 210, zf + 5.8), (c + 18, 215, zf + 6.6), m["led_r"], trip)
        pts["trip"] = trip
    sh.append(box(f"{name}_plate", (c - 30, 230, zf), (c + 30, CAB_H - 4, zf + 1), m["steel"], g))
    join([o for o in sh if o.type == "MESH"], f"{name}_body")
    pts.update({
        "g": g, "closed": closed, "open": opened, "mvs": mvs, "arcs": arcs, "c": c,
        "relay": (c, 226, zf + 5), "breaker": (c - 60, 150, zf - 70), "bottle": (c + POLE_DX + 6, BOT_Y + 4, cz),
        "mech": (c, 122, zf - 8), "x0": x0, "x1": x1, "cable": (c, 40, zf), "top": (c, CAB_H, zf - 40),
    })
    return pts


def breaker_state(cab, closed_iv, open_iv):
    """Show the red (closed) or green (open) flag over frame intervals."""
    show(cab["closed"], closed_iv)
    show(cab["open"], open_iv)


def breaker(cab, events, closed=True, gap=1.4, end=None):
    """Key a cabinet's breaker through `events` [(frame, closed?)], starting `closed`: the moving
    contacts drop `gap` to open (with a short arc) and rise to close; the red/green flags follow."""
    end = end if end is not None else 10 ** 6
    state = closed
    keys = [(0, (0, 0, 0) if closed else (0, -gap, 0))]
    c_iv, o_iv = [], []
    t0 = 0
    arcs = []
    for f, want in events:
        if want == state:
            continue
        (c_iv if state else o_iv).append((t0, f))
        keys += [(f, (0, 0, 0) if state else (0, -gap, 0)), (f + 3, (0, 0, 0) if want else (0, -gap, 0))]
        if not want:
            arcs.append((f + 1, f + 7))
        state, t0 = want, f
    (c_iv if state else o_iv).append((t0, end))
    for mv in cab["mvs"]:
        move(mv, keys)
    for arc in cab["arcs"]:
        show(arc, arcs)
    show(cab["closed"], c_iv)
    show(cab["open"], o_iv)


def trip_cab(cab, f, gap=1.4, reclose=None):
    """The cabinet's breaker opens at frame f (all three poles), and closes again at `reclose`."""
    for mv, arc in zip(cab["mvs"], cab["arcs"]):
        keys = [(0, (0, 0, 0)), (f, (0, 0, 0)), (f + 3, (0, -gap, 0))]
        if reclose is not None:
            keys += [(reclose, (0, -gap, 0)), (reclose + 3, (0, 0, 0))]
        move(mv, keys)
        show(arc, [(f + 1, f + 7)])


def bottle_path(cab, k, zf, down=True):
    """Through pole k of a cabinet: bus stab, upper arm, bottle, lower arm, out to the cable compartment."""
    x = cab["c"] + (k - 1) * POLE_DX
    cz = zf - 70
    p = [(x, UP_Y, zf - 150), (x, UP_Y, cz), (x, BOT_Y + 2, cz), (x, LO_Y, cz), (x + 2.5, LO_Y, zf - 150),
         (x + 2.5, 40, zf - 150)]
    return p if down else list(reversed(p))


# ---- the switchgear house ----------------------------------------------------------------------

HOUSE_X = 1330.0
HOUSE_Z0, HOUSE_Z1 = -1320.0, -650.0
LINE_ZF = -1050.0
LINEUP_A = -1260.0      # x of lineup A's first cabinet (mirror for B)
KINDS_A = ("main", "f1", "f2", "f3", "f4", "gen")


def lineup(m, parent, side, name):
    """Six cabinets (utility main, four feeders, generator breaker) with the bus duct above them. Side A
    runs left to right from LINEUP_A; side B is its mirror image. Returns {kind: cabinet} and bus paths."""
    sgn = 1.0 if side == "A" else -1.0
    cabs = {}
    for i, kind in enumerate(KINDS_A):
        if side == "A":
            x0 = LINEUP_A + i * CAB_W
        else:
            x0 = -LINEUP_A - (i + 1) * CAB_W
        cabs[kind] = cabinet(m, parent, x0, LINE_ZF, kind, f"{name}_{kind}")
    xa = min(c["x0"] for c in cabs.values())
    xb = max(c["x1"] for c in cabs.values())
    zbus = LINE_ZF - 150
    g = empty(f"{name}_bus", parent)
    sh = [box(f"{name}_duct_back", (xa, CAB_H, zbus - 30), (xb, 304, zbus - 27), m["paint"], g),
          box(f"{name}_duct_top", (xa, 301, zbus - 30), (xb, 304, zbus + 30), m["paint"], g),
          box(f"{name}_duct_l", (xa, CAB_H, zbus - 30), (xa + 2, 304, zbus + 30), m["paint"], g),
          box(f"{name}_duct_r", (xb - 2, CAB_H, zbus - 30), (xb, 304, zbus + 30), m["paint"], g)]
    bars = []
    for k, y in enumerate(BUS_Y):
        sh.append(box(f"{name}_bar{k}", (xa + 4, y - 5, zbus - 3), (xb - 4, y + 5, zbus + 3), m["copper"], g))
        bars.append(((xa + 4, y, zbus + 3.5), (xb - 4, y, zbus + 3.5)))
    for i in range(7):
        x = xa + (xb - xa) * i / 6
        x = min(max(x, xa + 10), xb - 10)
        sh.append(box(f"{name}_standoff{i}", (x - 4, BUS_Y[0] - 5, zbus - 27), (x + 4, BUS_Y[2] + 5, zbus - 3), m["epoxy"], g))
    for kind, cab in cabs.items():
        for k in range(3):
            x = cab["c"] + (k - 1) * POLE_DX
            sh.append(box(f"{name}_{kind}_riser{k}", (x - 2.5, UP_Y - 3, zbus - 3), (x + 2.5, BUS_Y[k] + 5, zbus + 3), m["copper"], g))
    join(sh, f"{name}_bus_body")
    return cabs, {"bars": bars, "zbus": zbus, "xa": xa, "xb": xb, "sgn": sgn}


def house(m, parent):
    g = empty("house", parent)
    sh = [box("house_floor", (-HOUSE_X, -6, HOUSE_Z0), (HOUSE_X, 0, HOUSE_Z1), m["floor"], g),
          box("house_back", (-HOUSE_X, 0, HOUSE_Z0), (HOUSE_X, 320, HOUSE_Z0 + 20), m["wall"], g),
          box("house_left", (-HOUSE_X, 0, HOUSE_Z0), (-HOUSE_X + 20, 320, HOUSE_Z1), m["wall"], g),
          box("house_right", (HOUSE_X - 20, 0, HOUSE_Z0), (HOUSE_X, 320, HOUSE_Z1), m["wall"], g),
          box("house_kerb", (-HOUSE_X, 0, HOUSE_Z1 - 20), (HOUSE_X, 30, HOUSE_Z1), m["wall"], g)]
    # the ATS controller between the lineups
    sh.append(box("ats_ctrl", (-90, 0, -1290), (90, 200, -1180), m["paint"], g))
    sh.append(box("ats_ctrl_screen", (-60, 120, -1180), (60, 180, -1178), m["screen"], g))
    sh.append(box("ats_ctrl_desk", (-110, 80, -1180), (110, 92, -1120), m["paint_dk"], g))
    join(sh, "house_body")
    return {"ats": (0, 200, -1180)}


# ---- yard: an H-frame line end and a power transformer ----------------------------------------------


def yard_transformer(m, parent, x, name):
    """A utility power transformer at x (tank, radiators, conservator, three HV bushings on top, a
    cable box on its inner side) on a gravel pad, with a dead-end H-frame behind it. Returns its points."""
    g = empty(name, parent)
    z0, z1 = -2350.0, -2150.0
    sgn = 1.0 if x < 0 else -1.0      # the cable box faces the middle of the campus
    sh = [box(f"{name}_pad", (x - 330, 0, -2650), (x + 330, 4, -1980), m["gravel"], g),
          box(f"{name}_plinth", (x - 160, 4, z0 - 10), (x + 160, 30, z1 + 10), m["concrete"], g),
          box(f"{name}_tank", (x - 140, 30, z0), (x + 140, 300, z1), m["tank"], g)]
    for k in range(9):
        z = z0 + 12 + k * 22
        sh.append(box(f"{name}_fin_l{k}", (x - 200, 70, z), (x - 140, 270, z + 6), m["tank"], g))
    for k in range(9):
        z = z0 + 12 + k * 22
        sh.append(box(f"{name}_fin_r{k}", (x + 140, 70, z), (x + 200, 270, z + 6), m["tank"], g))
    sh.append(tube(f"{name}_conservator", (x - 110, 345, z0 + 20), (x + 110, 345, z0 + 20), 26, m["tank"], g, 20))
    sh.append(tube(f"{name}_leg", (x + 80, 300, z0 + 20), (x + 80, 320, z0 + 20), 6, m["tank"], g, 10))
    tops = []
    for k in range(3):
        bx = x + (k - 1) * 70
        bz = (z0 + z1) / 2 + 10
        sh.append(tube(f"{name}_bush{k}", (bx, 300, bz), (bx, 430, bz), 9, m["porcelain"], g, 14))
        for j in range(7):
            sh.append(tube(f"{name}_shed{k}_{j}", (bx, 312 + 16 * j, bz), (bx, 316 + 16 * j, bz), 16, m["porcelain"], g, 16))
        sh.append(tube(f"{name}_term{k}", (bx, 430, bz), (bx, 442, bz), 4, m["tin"], g, 10))
        tops.append((bx, 442, bz))
    cx = x + sgn * 140
    sh.append(box(f"{name}_cablebox", (min(cx, cx + sgn * 50), 170, -2290), (max(cx, cx + sgn * 50), 280, -2210), m["tank"], g))
    # H-frame dead-end behind
    hz = -2600.0
    for k, px in enumerate((x - 130, x + 130)):
        sh.append(tube(f"{name}_pole{k}", (px, 0, hz), (px, 540, hz), 9, m["dark"], g, 10))
    sh.append(box(f"{name}_xarm", (x - 160, 515, hz - 8), (x + 160, 530, hz + 8), m["dark"], g))
    ends = []
    for k in range(3):
        bx = x + (k - 1) * 70
        sh.append(tube(f"{name}_ins{k}", (bx, 515, hz), (bx, 470, hz), 4, m["porcelain"], g, 10))
        ends.append((bx, 470, hz))
    join(sh, f"{name}_body")
    lines = []
    for k in range(3):
        far = (tops[k][0], 600, -2950)
        span = sag(far, ends[k], 30, 8)
        drop = sag(ends[k], tops[k], 25, 8)
        wire(f"{name}_line{k}", span, 1.6, m["steel"], g, 8)
        wire(f"{name}_drop{k}", drop, 1.6, m["steel"], g, 8)
        lines.append(span + drop[1:])
    return {"tops": tops, "lines": lines, "cable_out": (cx + sgn * 50, 230, -2250), "tank": (x, 300, z1),
            "frame": (x, 530, hz), "g": g}


# ---- generators -----------------------------------------------------------------------------------

GEN_Z0, GEN_Z1 = -2380.0, -2080.0


def genset(m, parent, x0, x1, name, s=1.0, z0=GEN_Z0, z1=GEN_Z1, y0=0.0):
    """A diesel generator set, x0..x1, in an enclosure whose front wall is cut away: radiator and fan
    at the left end, the engine block with its rocker covers, the alternator (stator cut open round its
    rotor) at the right end with its terminal box, a fuel tank base and an exhaust stack.
    Returns points and the 'running' groups (exhaust and alternator glow)."""
    g = empty(name, parent)
    L = x1 - x0
    zc = (z0 + z1) / 2
    D = z1 - z0
    H = 0.95 * D
    sh = [box(f"{name}_tank", (x0, y0, z0), (x1, y0 + 0.12 * H, z1), m["dark"], g),
          box(f"{name}_encl_back", (x0, y0 + 0.12 * H, z0), (x1, y0 + H, z0 + 4), m["gen"], g),
          box(f"{name}_encl_l", (x0, y0 + 0.12 * H, z0), (x0 + 4, y0 + H, z1), m["gen"], g),
          box(f"{name}_encl_r", (x1 - 4, y0 + 0.12 * H, z0), (x1, y0 + H, z1), m["gen"], g),
          box(f"{name}_encl_roof", (x0, y0 + H - 4, z0), (x1, y0 + H, zc - 0.1 * D), m["gen"], g)]
    # radiator and fan
    rx0, rx1 = x0 + 0.03 * L, x0 + 0.12 * L
    sh.append(box(f"{name}_rad", (rx0, y0 + 0.16 * H, z0 + 0.1 * D), (rx1, y0 + 0.86 * H, z1 - 0.1 * D), m["paint_dk"], g))
    for k in range(10):
        y = y0 + 0.2 * H + k * 0.064 * H
        sh.append(box(f"{name}_radfin{k}", (rx1, y, z0 + 0.12 * D), (rx1 + 2, y + 0.02 * H, z1 - 0.12 * D), m["steel"], g))
    # engine block
    ex0, ex1 = x0 + 0.18 * L, x0 + 0.62 * L
    sh.append(box(f"{name}_block", (ex0, y0 + 0.14 * H, z0 + 0.22 * D), (ex1, y0 + 0.6 * H, z1 - 0.22 * D), m["engine"], g))
    for k in range(6):
        x = ex0 + (k + 0.5) * (ex1 - ex0) / 6
        sh.append(box(f"{name}_head{k}", (x - 0.03 * L, y0 + 0.6 * H, z0 + 0.3 * D), (x + 0.03 * L, y0 + 0.68 * H, z1 - 0.3 * D), m["steel"], g))
    sh.append(rod(f"{name}_turbo", (ex0 + 0.1 * L, y0 + 0.74 * H, zc), (ex0 + 0.16 * L, y0 + 0.74 * H, zc), 0.06 * H, m["steel"], g, 16))
    # alternator: stator cut open on z = zc, rotor inside
    ax0, ax1 = x0 + 0.64 * L, x0 + 0.9 * L
    ay = y0 + 0.42 * H
    R = 0.27 * H
    sh.append(rod(f"{name}_alt_end", (ax0, ay, zc), (ax0 + 0.02 * L, ay, zc), R, m["engine"], g, 32))
    sta = pipe_x(f"{name}_stator", ax0 + 0.02 * L, ax1, R, 0.68 * R, m["core"], g, y=ay, z=zc)
    sh.append(sta)
    sh.append(pipe_x(f"{name}_windings", ax0 + 0.02 * L, ax1, 0.68 * R, 0.6 * R, m["coil"], g, y=ay, z=zc))
    sh.append(rod(f"{name}_rotor", (ax0 + 0.03 * L, ay, zc), (ax1 - 0.01 * L, ay, zc), 0.5 * R, m["coil"], g, 24, zc))
    sh.append(rod(f"{name}_shaft", (ex1, ay, zc), (ax1 + 0.02 * L, ay, zc), 0.12 * R, m["steel"], g, 12, zc))
    tb = (x0 + 0.95 * L, y0 + 0.55 * H, zc)
    sh.append(box(f"{name}_tbox", (x0 + 0.91 * L, y0 + 0.4 * H, z0 + 0.25 * D), (x1 - 0.01 * L, y0 + 0.72 * H, z1 - 0.25 * D), m["paint_dk"], g))
    # exhaust stack through the roof
    sx = x0 + 0.4 * L
    sz = z0 + 0.25 * D
    sh.append(tube(f"{name}_stack", (sx, y0 + 0.68 * H, sz), (sx, y0 + 1.5 * H, sz), 0.05 * H, m["steel"], g, 14))
    sh.append(tube(f"{name}_muffler", (sx, y0 + 1.05 * H, sz), (sx, y0 + 1.3 * H, sz), 0.1 * H, m["steel"], g, 18))
    join(sh, f"{name}_body")
    glow = empty(f"{name}_alt_glow", g)
    o = rod(f"{name}_rotor_hot", (ax0 + 0.03 * L, ay, zc + 0.3), (ax1 - 0.01 * L, ay, zc + 0.3), 0.5 * R, m["hot"], glow, 24)
    cut(o, zc + 0.3)
    return {"g": g, "term": tb, "stack": (sx, y0 + 1.5 * H, sz), "alt": (ax0 + 0.15 * L, ay + 0.5 * R, zc),
            "engine": ((ex0 + ex1) / 2, y0 + 0.68 * H, zc), "rad": ((rx0 + rx1) / 2, y0 + 0.86 * H, zc),
            "glow": glow, "top": ((x0 + x1) / 2, y0 + H, z1)}


def pipe_x(name, x0, x1, ro, ri, m, parent=None, y=0.0, z=0.0, half=True, verts=40):
    """A hollow cylinder along x (axis at height y, depth z), cut at its axis plane when `half`."""
    a0, a1 = (math.pi, 2 * math.pi) if half else (0.0, 2 * math.pi)
    n = verts // 2 if half else verts
    angles = [a0 + (a1 - a0) * i / n for i in range(n + 1 if half else n)]
    rings = [(x0, ro), (x1, ro), (x1, ri), (x0, ri)]
    vs = [tuple(P(xx, y + r * math.cos(t), z + r * math.sin(t))) for xx, r in rings for t in angles]
    k = len(angles)
    faces = []
    for a in range(4):
        b = (a + 1) % 4
        for i in (range(k - 1) if half else range(k)):
            j = (i + 1) % k
            faces.append((a * k + i, a * k + j, b * k + j, b * k + i))
    if half:
        for i in (0, k - 1):
            faces.append(tuple(a * k + i for a in range(4)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return _link(name, me, m, parent)


def exhaust(parent, name, stack, m, b, u0=0.1, u1=0.9, n=7, rise=260.0, size=14.0):
    """Puffs of exhaust rising and drifting from a stack top through beat b."""
    pts = [stack, (stack[0] + 20, stack[1] + rise * 0.5, stack[2]), (stack[0] + 70, stack[1] + rise, stack[2] + 20)]
    return run(parent, name, pts, n, size, m, b, u0, u1, 40)


# ---- unit substation -------------------------------------------------------------------------------

USS_Z0, USS_Z1 = -470.0, -200.0


def unit_sub(m, parent, side, name):
    """A unit substation: MV switch section, a cast-resin transformer with its enclosure front cut away
    (core, three coil pairs), and a 480 V switchboard with drawout air breakers. Side A sits left of the
    hall, side B mirrors it. Returns points."""
    g = empty(name, parent)
    sgn = 1.0 if side == "A" else -1.0

    def X(a, b):
        xa, xb = -sgn * a, -sgn * b
        return (min(xa, xb), max(xa, xb))

    z0, z1 = USS_Z0, USS_Z1
    sh = [box(f"{name}_pad", (X(1720, 940)[0], 0, z0 - 30), (X(1720, 940)[1], 6, z1 + 30), m["concrete"], g)]
    # MV switch section (outer end)
    a, b = X(1700, 1560)
    sh.append(box(f"{name}_mvsw", (a, 6, z0), (b, 236, z1), m["paint"], g))
    sh.append(box(f"{name}_mvsw_win", (a + 30, 140, z1), (b - 30, 190, z1 + 1), m["dark"], g))
    # transformer enclosure: back, sides, roof strip; front open
    a, b = X(1560, 1240)
    sh.append(box(f"{name}_tx_back", (a, 6, z0), (b, 250, z0 + 4), m["paint"], g))
    sh.append(box(f"{name}_tx_roof", (a, 246, z0), (b, 250, z1), m["paint"], g))
    sh.append(box(f"{name}_tx_floor", (a, 6, z0), (b, 16, z1), m["dark"], g))
    xc = (a + b) / 2
    zc = (z0 + z1) / 2
    tx = transformer(m, g, (xc, 16, zc), 0.85, f"{name}_tx", sh)
    # LV switchboard (inner end) with four drawout breakers
    a, b = X(1240, 960)
    sh.append(box(f"{name}_lv", (a, 6, z0), (b, 236, z1), m["paint"], g))
    acbs = []
    for k in range(4):
        y = 30 + 50 * k
        sh.append(box(f"{name}_acb{k}", (a + 30, y, z1), (b - 30, y + 38, z1 + 6), m["paint_dk"], g))
        sh.append(box(f"{name}_acbw{k}", (a + 50, y + 12, z1 + 6), (a + 90, y + 26, z1 + 7), m["relay"], g))
        acbs.append(((a + b) / 2, y + 19, z1 + 6))
    join(sh, f"{name}_body")
    mv_in = (-sgn * 1630, 236, zc)
    lv_out = (-sgn * 1100, 236, zc)
    return {"g": g, "mv_in": mv_in, "lv_out": lv_out, "tx": tx, "acbs": acbs, "mvsw": (-sgn * 1630, 236, z1),
            "lv": (-sgn * 1100, 236, z1), "txc": (xc, 140, z1)}


def transformer(m, parent, base, s, name, sh=None):
    """A three-phase dry-type transformer standing at `base` (bottom centre), cut at z = base.z: core legs
    and yokes, an LV coil (silver foil) inside each HV coil (copper discs). Base size (s = 1): 300 cm wide,
    220 cm tall. Adds static meshes to `sh` when given. Returns points."""
    bx, by, bz = base
    own = sh is None
    sh = [] if own else sh

    def B(n, lo, hi, mt):
        o = box(f"{name}_{n}", (bx + s * lo[0], by + s * lo[1], bz + s * lo[2]), (bx + s * hi[0], by + s * hi[1], bz + s * hi[2]), mt, parent)
        sh.append(o)
        return o

    B("yoke_lo", (-140, 0, -40), (140, 34, 0), m["core"])
    B("yoke_hi", (-140, 196, -40), (140, 230, 0), m["core"])
    legs = (-100, 0, 100)
    for k, lx in enumerate(legs):
        B(f"leg{k}", (lx - 20, 34, -40), (lx + 20, 196, 0), m["core"])
        for j in range(4):  # lamination lines on the cut face
            B(f"lam{k}_{j}", (lx - 17 + 10 * j, 34, -0.5), (lx - 15.5 + 10 * j, 196, 0.3), m["dark"])
        sh.append(pipe_v(f"{name}_lv{k}", by + s * 40, by + s * 190, s * 31, s * 23, m["coil_lv"], parent, bx + s * lx, bz, True, 36))
        for j in range(8):
            y0 = 42 + j * 18.5
            sh.append(pipe_v(f"{name}_hv{k}_{j}", by + s * y0, by + s * (y0 + 15), s * 46, s * 36, m["coil"], parent, bx + s * lx, bz, True, 36))
        sh.append(pipe_v(f"{name}_hvres{k}", by + s * 38, by + s * 192, s * 48, s * 46, m["resin"], parent, bx + s * lx, bz, True, 36))
    # HV delta links across the coil tops, LV bars out of the top
    for k in range(2):
        sh.append(rod(f"{name}_delta{k}", (bx + s * (legs[k] + 30), by + s * 200, bz - s * 30),
                      (bx + s * (legs[k + 1] - 30), by + s * 200, bz - s * 30), s * 3, m["copper"], parent, 10))
    for k, lx in enumerate(legs):
        sh.append(box(f"{name}_lvbar{k}", (bx + s * (lx + 18), by + s * 190, bz - s * 14), (bx + s * (lx + 26), by + s * 245, bz - s * 4), m["copper"], parent))
    if own:
        join(sh, f"{name}_body")
    return {"core": (bx + s * -100, by + s * 215, bz), "leg": (bx + s * 0, by + s * 120, bz),
            "lv": (bx + s * 100, by + s * 100, bz), "hv": (bx + s * 146, by + s * 150, bz),
            "lvbar": (bx + s * 122, by + s * 245, bz - s * 9), "top": (bx, by + s * 245, bz)}


# ---- the data hall ----------------------------------------------------------------------------------

HALL_X = 900.0
HALL_Z0, HALL_Z1 = -100.0, 820.0
ROWS = (280.0, 480.0, 680.0)
RACK_X = [-390.0 + 60.0 * i for i in range(14)]


def hall(m, parent):
    """The data hall: floor, back and side walls (front open), UPS-A and UPS-B lineups in its back
    corners, three rows of racks with an A busway and a B busway over each row, and drops to every rack.
    Returns points and the busway paths."""
    g = empty("hall", parent)
    sh = [box("hall_floor", (-HALL_X, -6, HALL_Z0), (HALL_X, 0, HALL_Z1), m["floor"], g),
          box("hall_back", (-HALL_X, 0, HALL_Z0), (HALL_X, 300, HALL_Z0 + 20), m["wall"], g),
          box("hall_left", (-HALL_X, 0, HALL_Z0), (-HALL_X + 20, 300, HALL_Z1), m["wall"], g),
          box("hall_right", (HALL_X - 20, 0, HALL_Z0), (HALL_X, 300, HALL_Z1), m["wall"], g)]
    ups = {}
    for side, sgn in (("A", -1.0), ("B", 1.0)):
        xs = sorted((sgn * 860, sgn * 580))
        sh.append(box(f"ups{side}", (xs[0], 0, -60), (xs[1], 200, 60), m["cab"], g))
        for k in range(4):
            xa = xs[0] + 10 + k * 68
            sh.append(box(f"ups{side}_panel{k}", (xa, 110, 60), (xa + 50, 170, 61), m["screen"], g))
        ups[side] = {"top": (sgn * 720, 200, 0), "front": (sgn * 720, 140, 60)}
    leds = []
    for r, zr in enumerate(ROWS):
        for i, x in enumerate(RACK_X):
            sh.append(box(f"rack{r}_{i}", (x - 28, 0, zr - 55), (x + 28, 220, zr + 55), m["rack"], g))
            for j in range(6):
                y = 20 + 32 * j
                sh.append(box(f"srv{r}_{i}_{j}", (x - 24, y, zr + 55), (x + 24, y + 24, zr + 56), m["server"], g))
            leds.append(box(f"led{r}_{i}", (x + 16, 30, zr + 56), (x + 22, 200, zr + 57), m["led_g"], g))
    rows = {"A": [], "B": []}
    for r, zr in enumerate(ROWS):
        for side, sgn, dz, mt in (("A", -1.0, -30.0, "pathA"), ("B", 1.0, 30.0, "pathB")):
            y = 262.0 if side == "A" else 278.0
            sh.append(box(f"busway{side}{r}", (-430, y - 6, zr + dz - 6), (430, y + 6, zr + dz + 6), m[mt], g))
            for i, x in enumerate(RACK_X):
                sh.append(tube(f"drop{side}{r}_{i}", (x + sgn * 8, y - 6, zr + dz), (x + sgn * 8, 220, zr + dz), 2.2, m["cable"], g, 6))
            rows[side].append([(sgn * 450, y, zr + dz), (-sgn * 430, y, zr + dz)])
    # header busways from each UPS to the rows
    heads = {}
    for side, sgn, mt in (("A", -1.0, "pathA"), ("B", 1.0, "pathB")):
        y = 262.0 if side == "A" else 278.0
        sh.append(box(f"riser{side}", (sgn * 720 - 6, 200, -6), (sgn * 720 + 6, y + 6, 6), m[mt], g))
        sh.append(box(f"head_x{side}", (min(sgn * 726, sgn * 444), y - 6, -6), (max(sgn * 726, sgn * 444), y + 6, 6), m[mt], g))
        dz = -30.0 if side == "A" else 30.0
        sh.append(box(f"head_z{side}", (sgn * 450 - 6, y - 6, -6), (sgn * 450 + 6, y + 6, ROWS[-1] + dz + 6), m[mt], g))
        heads[side] = [(sgn * 720, 200, 0), (sgn * 720, y, 0), (sgn * 450, y, 0)]
    join(sh, "hall_body")
    return {"ups": ups, "rows": rows, "heads": heads, "racks": (0, 220, ROWS[1] + 55), "g": g}


# ---- the campus ------------------------------------------------------------------------------------


def campus(m, root):
    """Everything on the overview, at 1 unit = 1 cm. Returns the parts' points and the power paths
    (absolute polylines) the beads ride."""
    box("ground", (-2300, -12, -3000), (2300, -6, 1000), m["ground"], root)
    h = house(m, root)
    A, busA = lineup(m, root, "A", "linA")
    B, busB = lineup(m, root, "B", "linB")
    TA = yard_transformer(m, root, -1650.0, "txA")
    TB = yard_transformer(m, root, 1650.0, "txB")
    GA = genset(m, root, -1080.0, -260.0, "genA")
    GB = genset(m, root, 260.0, 1080.0, "genB")
    UA = unit_sub(m, root, "A", "ussA")
    UB = unit_sub(m, root, "B", "ussB")
    HL = hall(m, root)

    paths = {}
    cables = empty("cables", root)
    for side, T, L, G, U, bus in (("A", TA, A, GA, UA, busA), ("B", TB, B, GB, UB, busB)):
        sgn = bus["sgn"]
        zb = LINE_ZF - CAB_D
        # utility MV cable: yard cable box, over the back wall, down behind the main cabinet
        main = L["main"]
        mx = main["c"]
        over = (mx, 360, HOUSE_Z0 + 10)
        mv = curve_pts(T["cable_out"], over, (0, 160, 0), 12) + [(mx, 200, zb - 8), (mx, LO_Y, zb - 8)]
        wire(f"mv{side}", mv, 6.0, m["cable"], cables, 8)
        paths[f"mv{side}"] = mv
        # generator cable: terminal box over the back wall into the generator cabinet
        gen = L["gen"]
        gx = gen["c"]
        gp = curve_pts(G["term"], (gx, 360, HOUSE_Z0 + 10), (0, 140, 0), 12) + [(gx, 200, zb - 8), (gx, LO_Y, zb - 8)]
        wire(f"gencable{side}", gp, 6.0, m["cable"], cables, 8)
        paths[f"gen{side}"] = gp
        # feeder 1 to the unit substation: down to the trench, out the front, across to the MV switch
        f1 = L["f1"]
        fx = f1["c"]
        out = [(fx, 30, LINE_ZF - 30), (fx, 8, LINE_ZF + 20), (fx, 8, HOUSE_Z1 - 30)]
        fp = out + curve_pts((fx, 8, HOUSE_Z1 - 30), U["mv_in"], (0, 120, 0), 10)[1:]
        wire(f"feed{side}", fp, 5.0, m["cable"], cables, 8)
        paths[f"feed{side}"] = fp
        # other feeders: down into the floor trench, toward other halls
        for kind in ("f2", "f3", "f4"):
            c = L[kind]["c"]
            st = [(c, 30, LINE_ZF - 30), (c, 8, LINE_ZF + 20), (c, 8, HOUSE_Z1 - 90), (c, -5, HOUSE_Z1 - 60)]
            wire(f"stub{side}{kind}", st, 5.0, m["cable"], cables, 8)
            paths[f"stub{side}{kind}"] = st
        # 480 V from the switchboard to the UPS
        lv = curve_pts(U["lv_out"], HL["ups"][side]["top"], (0, 160, 0), 12)
        wire(f"lv{side}", lv, 7.0, m["cable"], cables, 8)
        paths[f"lv{side}"] = lv
        paths[f"bus{side}"] = bus
        paths[f"hv{side}"] = T["lines"]
    join_cable_meshes(cables)
    box("trench", (-HOUSE_X + 20, 0, LINE_ZF + 6), (HOUSE_X - 20, 1.5, LINE_ZF + 34), m["dark"], root)
    return {"A": A, "B": B, "TA": TA, "TB": TB, "GA": GA, "GB": GB, "UA": UA, "UB": UB, "hall": HL, "house": h,
            "busA": busA, "busB": busB, "paths": paths}


def join_cable_meshes(group):
    """Merge each wire group's segments into one mesh (the wires never move)."""
    for g in list(group.children):
        kids = [c for c in g.children if c.type == "MESH"]
        if len(kids) > 1:
            o = join(kids, f"{g.name}_mesh")


def bus_path(bus, k, x_from, x_to):
    """Along bar k of a lineup's bus, from x_from to x_to."""
    y = BUS_Y[k]
    z = bus["zbus"] + 3.5
    return [(x_from, y, z), (x_to, y, z)]


def through_cab(cab, k, inward=False):
    """From bar k down pole k of a cabinet to its cable compartment (or the reverse, for an incomer)."""
    x = cab["c"] + (k - 1) * POLE_DX
    zbus = LINE_ZF - 150
    p = [(x, BUS_Y[k], zbus + 3.5)] + bottle_path(cab, k, LINE_ZF)
    return list(reversed(p)) if inward else p


# ---- the side-on cabinet section (section scale) ------------------------------------------------------


def side(m, parent, o=(0.0, 0.0, 0.0), name="sd"):
    """A metal-clad cabinet cut through its middle phase, front at x = o.x (facing -x), height 240,
    depth 240, cut face z = o.z. Rooms: relay (front top), breaker (front), bus (rear top, three bars
    in section), cable (rear bottom). The breaker truck carries its stored-energy mechanism (closing
    and opening springs, trip coil, shaft) and the middle-phase vacuum bottle (s = 2) on the cut plane.
    Returns points and groups for the moving parts."""
    ox, oy, oz = o

    def at(x, y, z=0.0):
        return (ox + x, oy + y, oz + z)

    def B(n, lo, hi, mt, g=None):
        o_ = box(f"{name}_{n}", at(*lo), at(*hi), mt, g or parent)
        sh.append(o_)
        return o_

    sh = []
    Z = -80.0
    B("floor", (0, 0, Z), (240, 3, 0), m["paint"])
    B("roof", (0, 237, Z), (240, 240, 0), m["paint"])
    B("back", (237, 3, Z), (240, 237, 0), m["paint"])
    B("far", (0, 3, Z), (240, 237, Z + 3), m["interior"])
    B("door_lv", (0, 178, Z), (3, 237, 0), m["paint"])
    B("door_brk", (0, 3, Z), (3, 175, 0), m["paint"])
    B("handle", (-6, 120, -30), (0, 124, -10), m["steel"])
    B("bar_lv", (3, 175, Z), (115, 178, 0), m["paint"])
    B("wall_mid", (115, 3, Z), (118, 237, 0), m["paint"])
    B("bar_rear", (118, 165, Z), (237, 168, 0), m["paint"])
    # bus bars (they run along z, the lineup's length): cut faces are the copper rectangles
    for k, x in enumerate((145.0, 171.0, 197.0)):
        B(f"bus{k}", (x, 190, Z), (x + 8, 216, 0), m["copper"])
        B(f"bus_post{k}", (x + 1, 216, -60), (x + 7, 237, -50), m["epoxy"])
    # stab bushings through the middle wall
    for n, y in (("u", 152.0), ("l", 99.0)):
        sh.append(rod(f"{name}_bush_{n}", at(104, y), at(132, y), 6.0, m["epoxy"], parent, 24, oz))
        sh.append(rod(f"{name}_stab_{n}", at(100, y), at(136, y), 2.4, m["copper"], parent, 16, oz + 0.05))
    # riser to the middle bar, conductor down to the cable termination
    sh.append(rod(f"{name}_riser_h", at(136, 152), at(175, 152), 2.6, m["copper"], parent, 16, oz))
    sh.append(rod(f"{name}_riser_v", at(175, 152), at(175, 190), 2.6, m["copper"], parent, 16, oz))
    sh.append(rod(f"{name}_lo_h", at(136, 99), at(200, 99), 2.6, m["copper"], parent, 16, oz))
    sh.append(rod(f"{name}_lo_v", at(200, 99), at(200, 70), 2.6, m["copper"], parent, 16, oz))
    # cable termination with sheds, the cable down through the floor
    sh.append(rod(f"{name}_term", at(200, 20), at(200, 70), 5.0, m["insul"], parent, 20, oz))
    for j in range(3):
        sh.append(rod(f"{name}_shed{j}", at(200, 44 + 8 * j), at(200, 47 + 8 * j), 8.5, m["insul"], parent, 24, oz))
    sh.append(rod(f"{name}_cable", at(200, -70), at(200, 22), 6.0, m["cable"], parent, 20, oz))
    ct = pipe_v(f"{name}_ct", oy + 80, oy + 90, 11.0, 4.0, m["epoxy"], parent, ox + 200, oz, True, 32)
    sh.append(ct)
    # the breaker truck
    B("truck", (12, 14, -70), (108, 28, -6), m["dark"])
    for k, x in enumerate((26.0, 94.0)):
        sh.append(rod(f"{name}_wheel{k}", at(x, 9, -74), at(x, 9, -2), 6.0, m["dark"], parent, 16))
    B("mech_back", (14, 28, -70), (106, 96, -67), m["paint_dk"])
    B("mech_l", (14, 28, -70), (17, 96, -6), m["paint_dk"])
    B("mech_r", (103, 28, -70), (106, 96, -6), m["paint_dk"])
    B("mech_top", (14, 93, -70), (106, 96, -6), m["paint_dk"])
    B("mech_front_strip", (14, 28, -8), (106, 32, -6), m["paint_dk"])
    # mechanism inside: closing spring, charging motor, shaft, trip coil
    sh.append(helix(f"{name}_close_spring", at(36, 0, -30), 8.0, oy + 34, oy + 84, 9, 1.4, m["spring"], parent))
    sh.append(rod(f"{name}_motor", at(60, 44, -60), at(60, 44, -10), 8.0, m["engine"], parent, 20))
    sh.append(rod(f"{name}_gear", at(60, 44, -10), at(60, 44, -7), 10.0, m["steel"], parent, 24))
    sh.append(rod(f"{name}_shaft", at(70, 82, -64), at(70, 82, -6), 3.0, m["steel"], parent, 16))
    sh.append(rod(f"{name}_tripcoil", at(52, 62, -24), at(52, 76, -24), 5.0, m["coil"], parent, 20))
    sh.append(rod(f"{name}_latch", at(52, 76, -24), at(64, 80, -24), 1.5, m["steel"], parent, 10))
    trip_glow = empty(f"{name}_trip_glow", parent)
    rod(f"{name}_tripcoil_hot", at(52, 61.5, -24), at(52, 76.5, -24), 5.4, m["hot"], trip_glow, 20)
    # opening spring: a pivot at its base so it can stretch
    osp = empty(f"{name}_open_spring", parent, P(*at(88, 34, -30)))
    helix(f"{name}_open_spring_c", (0, 0, 0), 5.0, 0.0, 30.0, 7, 1.0, m["spring"], osp)
    # the middle-phase bottle on the cut plane, the upper arm, the shunt, the pushrod
    vi_c = at(70, 124, 0)
    vp, mv, arc = interrupter(m, parent, vi_c, 1.6, f"{name}_vi")
    sh.append(rod(f"{name}_arm_u", at(70, 124 + 1.6 * 13), at(70, 152), 2.4, m["copper"], parent, 16, oz))
    sh.append(rod(f"{name}_arm_u2", at(70, 152), at(100, 152), 2.4, m["copper"], parent, 16, oz))
    sh.append(rod(f"{name}_arm_l", at(76, 99), at(100, 99), 2.4, m["copper"], parent, 16, oz))
    sh.append(rod(f"{name}_tulip_u", at(96, 152), at(108, 152), 4.0, m["tin"], parent, 16, oz))
    sh.append(rod(f"{name}_tulip_l", at(96, 99), at(108, 99), 4.0, m["tin"], parent, 16, oz))
    sh.append(rod(f"{name}_insul_post", at(70, 96), at(70, 100), 9.0, m["epoxy"], parent, 20, oz))
    # the pushrod rides with the moving contact
    rod(f"{name}_pushrod", at(70, 82), at(70, 124 - 1.6 * 15), 2.0, m["insul"], mv, 12, oz + 0.05)
    rod(f"{name}_shunt", at(70, 101), at(77, 101), 1.6, m["copper"], mv, 10, oz + 0.05)
    # relay on the door, CT and trip wiring
    B("relay", (3, 188, -50), (28, 228, -8), m["relay"])
    B("relay_face", (-1.5, 192, -46), (0, 224, -12), m["screen"])
    rtrip = empty(f"{name}_relay_trip", parent)
    box(f"{name}_relay_face_trip", at(-2.4, 192, -46), at(-1.4, 224, -12), m["screen_red"], rtrip)
    ct_wire = [at(206, 85, -4), at(228, 85, -4), at(228, 232, -4), at(30, 232, -4), at(28, 215, -4)]
    trip_wire = [at(16, 188, -4), at(10, 178, -4), at(10, 110, -4), at(52, 110, -4), at(52, 77, -4)]
    sh.append(polyline(f"{name}_ct_wire", ct_wire, 0.8, m["dark"], parent))
    sh.append(polyline(f"{name}_trip_wire", trip_wire, 0.8, m["dark"], parent))
    join([o_ for o_ in sh if o_.type == "MESH"], f"{name}_body")
    power = [at(175, 203, 0.5), at(175, 152, 0.5), at(70, 152, 0.5), at(70, 124, 0.5), at(70, 101, 0.5),
             at(136, 99, 0.5), at(200, 99, 0.5), at(200, 20, 0.5), at(200, -60, 0.5)]
    return {
        "mv": mv, "arc": arc, "vp": vp, "trip_glow": trip_glow, "open_spring": osp, "relay_trip": rtrip,
        "ct_wire": ct_wire, "trip_wire": trip_wire, "power": power,
        "relay": at(14, 228, 0), "bus": at(171, 216, 0), "bottle": at(70 - 9.6, 140, 0), "ct": at(211, 85, 0),
        "term": at(208, 56, 0), "mech": at(36, 84, 0), "trip": at(52, 76, 0), "close_spring": at(44, 60, 0),
        "open_spring_pt": at(93, 60, 0), "cable": at(206, -20, 0), "stab": at(118, 152, 0), "truck": at(60, 28, 0),
        "door": at(0, 150, 0), "motor": at(60, 52, 0), "breaker_room": at(60, 160, 0), "cable_room": at(150, 40, 0),
        "bus_room": at(140, 228, 0), "lv_room": at(60, 228, 0),
    }


# ---- a 480 V air circuit breaker cut open ------------------------------------------------------------


def acb(m, parent, o=(0.0, 0.0, 0.0), s=1.0, name="acb"):
    """One pole of an air circuit breaker cut open, side on: front fascia at the left, rear terminals at
    the right. The moving arm pivots near the bottom and swings left to open; arc runners lead up into
    the arc chute, a stack of steel splitter plates. Base size (s = 1): 60 cm deep, 80 cm tall.
    Returns points and the arm pivot group."""
    ox, oy, oz = o

    def at(x, y, z=0.0):
        return (ox + s * x, oy + s * y, oz + s * z)

    sh = []

    def B(n, lo, hi, mt, g=None):
        o_ = box(f"{name}_{n}", at(*lo), at(*hi), mt, g or parent)
        if g is None:
            sh.append(o_)
        return o_

    B("base", (0, 0, -20), (60, 3, 0), m["epoxy"])
    B("back_wall", (0, 3, -20), (60, 72, -18), m["epoxy"])
    B("fascia", (-2, 3, -20), (2, 72, 0), m["paint_dk"])
    B("rear", (56, 3, -20), (60, 50, 0), m["epoxy"])
    # rear terminals
    B("term_hi", (56, 40, -12), (78, 46, 0), m["copper"])
    B("term_lo", (56, 10, -12), (78, 16, 0), m["copper"])
    # fixed contact on the upper terminal, arc runner up into the chute
    B("fixed", (46, 34, -12), (56, 46, 0), m["copper"])
    B("fixed_tip", (44, 34, -12), (46, 40, 0), m["cucr"])
    sh.append(polyline(f"{name}_runner_f", [at(50, 46, -2), at(52, 54, -2), at(52, 58, -2)], s * 0.8, m["steel"], parent))
    sh.append(polyline(f"{name}_runner_m", [at(36, 42, -2), at(30, 52, -2), at(30, 58, -2)], s * 0.8, m["steel"], parent))
    # the arc chute: a box of splitter plates above the contacts
    B("chute_l", (26, 56, -16), (28, 78, 0), m["chute"])
    B("chute_r", (54, 56, -16), (56, 78, 0), m["chute"])
    for k in range(9):
        x = 29.5 + 2.75 * k
        B(f"plate{k}", (x, 58, -14), (x + 0.8, 76, -1), m["steel"])
    B("chute_top", (26, 78, -16), (56, 80, 0), m["chute"])
    # the moving arm: pivot at (38, 14)
    piv = empty(f"{name}_arm", parent, P(*at(38, 14, 0)))

    def rel(x, y, z=0.0):
        return (s * (x - 38), s * (y - 14), s * z)

    box(f"{name}_arm_bar", rel(36, 14, -10), rel(41, 40, -2), m["copper"], piv)
    box(f"{name}_arm_tip", rel(41, 34, -10), rel(43.6, 40, -2), m["cucr"], piv)
    tube(f"{name}_pivot", rel(38, 14, -14), rel(38, 14, 0), s * 2.0, m["steel"], piv, 12)
    # flexible braid from the pivot to the lower terminal
    sh.append(polyline(f"{name}_braid", [at(39, 13, -6), at(46, 9, -6), at(56, 13, -6)], s * 1.6, m["copper"], parent))
    # mechanism behind the fascia: spring and toggle links
    sh.append(helix(f"{name}_spring", at(12, 0, -10), s * 4.0, oy + s * 10, oy + s * 46, 8, s * 0.7, m["spring"], parent))
    sh.append(polyline(f"{name}_link", [at(12, 48, -8), at(24, 30, -8), at(36, 22, -8)], s * 1.0, m["steel"], parent))
    sh.append(rod(f"{name}_btn", at(-4, 56, -10), at(-2, 56, -10), s * 2.5, m["flag_open"], parent, 12))
    sh.append(rod(f"{name}_btn2", at(-4, 64, -10), at(-2, 64, -10), s * 2.5, m["flag_closed"], parent, 12))
    join(sh, f"{name}_body")
    arc0 = empty(f"{name}_arc0", parent)
    ellipsoid(f"{name}_arc0_b", at(44, 38, 0.3), s * 2.0, s * 3.0, s * 0.6, m["arc"], arc0)
    arc1 = empty(f"{name}_arc1", parent)
    ellipsoid(f"{name}_arc1_b", at(41, 50, 0.3), s * 8.0, s * 2.5, s * 0.6, m["arc"], arc1)
    arc2 = empty(f"{name}_arc2", parent)
    for k in range(8):
        x = 30.8 + 2.75 * k
        ellipsoid(f"{name}_arc2_{k}", at(x, 66, 0.3), s * 0.9, s * 5.0, s * 0.5, m["plasma"], arc2)
    return {"arm": piv, "arc": (arc0, arc1, arc2), "chute": at(56, 72, 0), "plates": at(41, 76, 0),
            "fixed": at(52, 40, 0), "moving": at(38, 30, 0), "pivot": at(38, 14, 0), "mech": at(12, 40, 0),
            "term": at(72, 46, 0), "runner": at(30, 56, 0), "fascia": at(-2, 64, 0)}


# ---- a double-throw transfer switch ----------------------------------------------------------------


def ats(m, parent, o=(0.0, 0.0, 0.0), s=1.0, name="ats"):
    """A transfer switch, cut open: the utility (normal) contact at the top, the generator (emergency)
    contact at the bottom, one copper blade pivoting at the load terminal so it can only touch one at a
    time, a motor operator turning it, and the controller with its display. Base size (s = 1):
    120 cm wide, 120 cm tall. Returns points and the blade group (rotate +/-)."""
    ox, oy, oz = o

    def at(x, y, z=0.0):
        return (ox + s * x, oy + s * y, oz + s * z)

    sh = []

    def B(n, lo, hi, mt):
        o_ = box(f"{name}_{n}", at(*lo), at(*hi), mt, parent)
        sh.append(o_)
        return o_

    B("back", (0, 0, -30), (120, 120, -27), m["interior"])
    B("base", (0, 0, -30), (120, 4, 0), m["paint"])
    B("side_r", (117, 4, -30), (120, 120, 0), m["paint"])
    B("roof", (0, 117, -30), (120, 120, 0), m["paint"])
    # utility line in at the top left, generator line in at the bottom left
    B("n_bar", (0, 84, -12), (56, 90, -2), m["copper"])
    B("n_contact", (55, 78, -12), (61, 90, -2), m["cucr"])
    B("e_bar", (0, 26, -12), (56, 32, -2), m["copper"])
    B("e_contact", (55, 26, -12), (61, 38, -2), m["cucr"])
    B("n_ins", (20, 92, -14), (28, 117, -6), m["epoxy"])
    B("e_ins", (20, 4, -14), (28, 24, -6), m["epoxy"])
    # load terminal and out
    B("load_post", (92, 50, -12), (100, 66, -2), m["copper"])
    B("load_bar", (100, 54, -12), (130, 62, -2), m["copper"])
    # motor operator and link
    sh.append(rod(f"{name}_motor", at(96, 84, -26), at(96, 84, -14), s * 9.0, m["engine"], parent, 20))
    sh.append(polyline(f"{name}_link", [at(96, 84, -12), at(92, 70, -12)], s * 1.2, m["steel"], parent))
    # controller box with its display, wired to both lines
    B("ctrl", (66, 92, -24), (88, 114, -4), m["relay"])
    B("ctrl_scr", (68, 100, -4), (86, 112, -3.2), m["screen"])
    sh.append(polyline(f"{name}_sense_n", [at(40, 92, -4), at(40, 104, -4), at(66, 104, -4)], s * 0.5, m["dark"], parent))
    sh.append(polyline(f"{name}_sense_e", [at(44, 30, -4), at(44, 40, -4), at(62, 40, -4), at(62, 96, -4), at(66, 96, -4)],
                       s * 0.5, m["dark"], parent))
    join(sh, f"{name}_body")
    piv = empty(f"{name}_blade", parent, P(*at(96, 58, 0)))
    box(f"{name}_blade_bar", (s * -42, s * -3, s * -10), (s * 0, s * 3, s * -4), m["copper"], piv)
    box(f"{name}_blade_tip", (s * -44, s * -4, s * -10), (s * -40, s * 4, s * -4), m["tin"], piv)
    tube(f"{name}_blade_pin", (0, 0, s * -14), (0, 0, 0), s * 2.6, m["steel"], piv, 12)
    ang = math.atan2(28.0, 40.0)  # up to the N contact, down to the E contact
    return {"blade": piv, "ang": ang, "n": at(40, 92, 0), "e": at(40, 24, 0), "load": at(126, 62, 0),
            "ctrl": at(77, 114, 0), "motor": at(96, 93, 0), "pivot": at(96, 58, 0),
            "n_in": [at(-60, 87, -7), at(58, 87, -7)], "e_in": [at(-60, 29, -7), at(58, 29, -7)],
            "out": [at(96, 58, -7), at(130, 58, -7), at(170, 58, -7)]}


# ---- a technician ---------------------------------------------------------------------------------


def person(m, parent, base, h=180.0, name="tech", suit=True, facing=1.0):
    """A plain figure standing at `base`, `h` tall; in an arc-rated suit and hood when `suit`."""
    bx, by, bz = base
    s = h / 180.0
    body = m["suit"] if suit else m["paint_dk"]
    sh = []
    for k, dx in enumerate((-9, 9)):
        sh.append(rod(f"{name}_leg{k}", (bx + s * dx, by, bz), (bx + s * dx, by + s * 85, bz), s * 7, body, parent, 12))
    sh.append(box(f"{name}_torso", (bx - s * 20, by + s * 82, bz - s * 12), (bx + s * 20, by + s * 145, bz + s * 12), body, parent))
    for k, dx in enumerate((-25, 25)):
        sh.append(rod(f"{name}_arm{k}", (bx + s * dx, by + s * 140, bz), (bx + s * dx + facing * s * 14, by + s * 92, bz + s * 6), s * 5.5, body, parent, 10))
    sh.append(ball(f"{name}_head", (bx, by + s * 160, bz), s * 14, body if suit else m["skin"], parent, 16))
    if suit:
        sh.append(box(f"{name}_visor", (bx + facing * s * 6 - s * 9, by + s * 152, bz - s * 9),
                      (bx + facing * s * 6 + s * 9, by + s * 168, bz + s * 9), m["visor"], parent))
    join(sh, f"{name}_body")
    return {"head": (bx, by + s * 176, bz), "chest": (bx, by + s * 120, bz + s * 12), "hand": (bx + facing * s * 40, by + s * 92, bz)}


# ---- camera ----------------------------------------------------------------------------------------

PANE = 0.53
GLIDE = 0.16


def frame(c, size, yaw=0.3, pitch=0.3, pad=1.1, min_d=40.0):
    """A pose that fits a subject `size` across, centred on c, in the left pane (pre-root-scale units)."""
    return (tuple(c), max(size / PANE * pad, min_d), yaw, pitch)


def _eye(t, d, yaw, pitch):
    cp, sp = math.cos(pitch), math.sin(pitch)
    return (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))


def camera_path(root, plan):
    """One pose per beat (or a list of (u, pose) moves inside a beat), glided into and held with a slow
    push-in, as fiber_laser_detail.camera_path."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    keys = []
    for i, entry in enumerate(plan):
        moves = entry if isinstance(entry, list) else [(0.0 if i == 0 else GLIDE, entry)]
        for j, (u, pose) in enumerate(moves):
            u_end = moves[j + 1][0] - 0.14 if j + 1 < len(moves) else 1.0
            fa = F(i, u)
            fb = F(i, u_end) - (1 if j + 1 == len(moves) else 0)
            keys.append((fa, pose, 1.03))
            keys.append((fb, pose, 0.97))
    last = -1
    for f, (t, d, yaw, pitch), k in keys:
        if f <= last:
            f = last + 1
        last = f
        key(target, f, "location", P(*t), linear=True)
        key(eye, f, "location", P(*_eye(t, d * k, yaw, pitch)), linear=True)


# ---- a rack server with two power supplies --------------------------------------------------------


def server(m, parent, o=(0.0, 0.0, 0.0), name="srv"):
    """A rack seen from the side, its rear at the right, with one server pulled half out and its lid cut
    away: board, processors, fans, and two power supplies at the rear, each corded to its own PDU strip
    (PDU A orange, PDU B blue) on the rack's rear posts. Size: rack 60 wide, 200 tall, 110 deep.
    Returns points and the cord paths (absolute)."""
    ox, oy, oz = o

    def at(x, y, z=0.0):
        return (ox + x, oy + y, oz + z)

    sh = []

    def B(n, lo, hi, mt):
        o_ = box(f"{name}_{n}", at(*lo), at(*hi), mt, parent)
        sh.append(o_)
        return o_

    # rack frame: posts and rails (side on: x is depth, front at x = 0)
    for k, x in enumerate((0.0, 106.0)):
        B(f"post{k}", (x, 0, -60), (x + 4, 200, -56), m["rack"])
        B(f"postf{k}", (x, 0, -4), (x + 4, 200, 0), m["rack"])
    B("top", (0, 196, -60), (110, 200, 0), m["rack"])
    B("base", (0, 0, -60), (110, 6, 0), m["rack"])
    for j in range(9):
        y = 12 + 20 * j
        if j == 4:
            continue
        B(f"chassis{j}", (4, y, -54), (106, y + 16, -6), m["server"])
        B(f"bezel{j}", (2, y, -54), (4, y + 16, -6), m["dark"])
    # the pulled-out server, lid off: chassis floor and walls
    y0 = 92.0
    B("srv_floor", (-40, y0, -54), (100, y0 + 2, -6), m["server"])
    B("srv_back", (-40, y0, -54), (100, y0 + 16, -52), m["server"])
    B("srv_board", (-30, y0 + 2, -50), (60, y0 + 3, -10), m["pcb"])
    for k, x in enumerate((-10.0, 22.0)):
        B(f"cpu{k}", (x, y0 + 3, -40), (x + 16, y0 + 9, -20), m["steel"])
    for k in range(5):
        B(f"fan{k}", (-38, y0 + 2, -52 + 9 * k), (-32, y0 + 14, -45 + 9 * k), m["dark"])
    psu = []
    for k, z in enumerate((-50.0, -28.0)):
        B(f"psu{k}", (64, y0 + 2, z), (100, y0 + 14, z + 18), m["steel"])
        B(f"psu_led{k}", (100, y0 + 10, z + 3), (101, y0 + 13, z + 6), m["led_g"])
        psu.append(at(100, y0 + 8, z + 9))
    # PDU strips on the rear posts
    B("pdu_a", (112, 20, -58), (118, 190, -48), m["pathA"])
    B("pdu_b", (112, 20, -14), (118, 190, -4), m["pathB"])
    join(sh, f"{name}_body")
    cords = []
    for k, (p, zp) in enumerate(zip(psu, (-53.0, -9.0))):
        q = at(112, 130 + 8 * k, zp)
        pts = curve_pts(at(101, p[1] - oy, p[2] - oz), q, (10.0, 14.0, 0.0), 10)
        wire(f"{name}_cord{k}", pts, 1.4, m["cable"], parent, 8)
        feed = [at(115, 190, zp), at(115, 130 + 8 * k, zp)]
        cords.append(feed + pts[::-1][1:])
    return {"psu": psu, "cords": cords, "pdu_a": at(118, 170, -50), "pdu_b": at(118, 170, -6),
            "board": at(10, y0 + 3, -10), "rack": at(50, 200, 0), "srv": at(-20, y0 + 16, -6)}


def ups_row(m, parent, x0, n, name, w=90.0, h=200.0, d=80.0, z1=0.0):
    """`n` UPS modules side by side from x0, fronts at z = z1. Returns their front centres and the
    groups that turn a module's panel red when it fails."""
    out = []
    sh = []
    for k in range(n):
        xa = x0 + k * (w + 10)
        sh.append(box(f"{name}{k}", (xa, 0, z1 - d), (xa + w, h, z1), m["cab"], parent))
        sh.append(box(f"{name}{k}_scr", (xa + 15, 120, z1), (xa + w - 15, 160, z1 + 1), m["screen"], parent))
        sh.append(box(f"{name}{k}_vent", (xa + 15, 30, z1), (xa + w - 15, 90, z1 + 1), m["paint_dk"], parent))
        bad = empty(f"{name}{k}_bad", parent)
        box(f"{name}{k}_scr_bad", (xa + 15, 120, z1 + 1), (xa + w - 15, 160, z1 + 2), m["screen_red"], bad)
        out.append({"front": (xa + w / 2, 160, z1), "top": (xa + w / 2, h, z1 - d / 2), "bad": bad, "x": xa + w / 2})
    join(sh, f"{name}_body")
    return out


def wrench(m, parent, a, b, name="wrench"):
    """A spanner dropped across two bars, from a to b."""
    g = empty(name, parent)
    tube(f"{name}_shaft", a, b, 2.4, m["steel"], g, 10)
    for k, p in enumerate((a, b)):
        ball(f"{name}_jaw{k}", p, 4.5, m["steel"], g, 12)
    return g


def lock_tag(m, parent, at, name="lock"):
    """A red padlock with its shackle and a yellow danger tag hanging below it."""
    x, y, z = at
    sh = [box(f"{name}_body", (x - 4, y - 10, z), (x + 4, y - 2, z + 4), m["lock"], parent),
          tube(f"{name}_shackle", (x - 2.5, y - 2, z + 2), (x - 2.5, y + 4, z + 2), 0.9, m["steel"], parent, 8),
          tube(f"{name}_shackle2", (x + 2.5, y - 2, z + 2), (x + 2.5, y + 4, z + 2), 0.9, m["steel"], parent, 8),
          tube(f"{name}_shackle3", (x - 2.5, y + 4, z + 2), (x + 2.5, y + 4, z + 2), 0.9, m["steel"], parent, 8),
          box(f"{name}_tag", (x - 5, y - 30, z + 1), (x + 5, y - 12, z + 2), m["tag"], parent)]
    join(sh, f"{name}_all")
    return {"lock": (x, y - 6, z + 4), "tag": (x, y - 22, z + 2)}


def skid_truck(m, parent, x0, name="skid"):
    """A prefabricated power skid on a flatbed: steel skid frame, an enclosure with its front wall cut
    away and a short MV lineup inside, the trailer with its wheels and the tractor's cab.
    Returns points."""
    sh = []
    L = 4 * CAB_W + 60
    # trailer and tractor
    sh.append(box(f"{name}_bed", (x0 - 40, 70, -260), (x0 + L + 40, 90, 20), m["skid"], parent))
    for k, x in enumerate((x0 + 40, x0 + 120, x0 + L - 60)):
        sh.append(rod(f"{name}_wheel{k}", (x, 40, -250), (x, 40, 10), 40, m["tyre"], parent, 24))
    sh.append(box(f"{name}_cab", (x0 + L + 60, 40, -250), (x0 + L + 260, 300, 10), m["cab"], parent))
    sh.append(box(f"{name}_cab_win", (x0 + L + 200, 200, 10), (x0 + L + 250, 270, 11), m["dark"], parent))
    sh.append(rod(f"{name}_cab_wheel", (x0 + L + 180, 40, -250), (x0 + L + 180, 40, 10), 40, m["tyre"], parent, 24))
    # skid frame and enclosure
    sh.append(box(f"{name}_frame", (x0, 90, -250), (x0 + L, 110, 0), m["skid"], parent))
    sh.append(box(f"{name}_wall_back", (x0, 110, -250), (x0 + L, 400, -244), m["wall"], parent))
    sh.append(box(f"{name}_wall_l", (x0, 110, -250), (x0 + 6, 400, 0), m["wall"], parent))
    sh.append(box(f"{name}_wall_r", (x0 + L - 6, 110, -250), (x0 + L, 400, 0), m["wall"], parent))
    sh.append(box(f"{name}_roof", (x0, 394, -250), (x0 + L, 400, -120), m["wall"], parent))
    join(sh, f"{name}_body")
    cabs = []
    for k in range(4):
        g = empty(f"{name}_cabs{k}", parent, P(0, 110, 0))
        c = cabinet(m, g, x0 + 30 + k * CAB_W, -6.0, "f", f"{name}_c{k}")
        cabs.append(c)
    return {"cabs": cabs, "skid": (x0 + L / 2, 400, -120), "frame": (x0 + 30, 110, 0), "truck": (x0 + L + 160, 300, -120),
            "wheel": (x0 + 40, 80, 10)}


def pad_ghost(m, parent, c, w, d, h, name="ghost"):
    """An empty concrete pad with a thin outline of the unit that should stand on it."""
    x, y, z = c
    sh = [box(f"{name}_pad", (x - w / 2 - 30, y, z - d - 30), (x + w / 2 + 30, y + 10, z + 30), m["concrete"], parent)]
    ys = (y + 10, y + 10 + h)
    for yy in ys:
        sh.append(tube(f"{name}_e{yy}_0", (x - w / 2, yy, z - d), (x + w / 2, yy, z - d), 1.6, m["tag"], parent, 6))
        sh.append(tube(f"{name}_e{yy}_1", (x - w / 2, yy, z), (x + w / 2, yy, z), 1.6, m["tag"], parent, 6))
        sh.append(tube(f"{name}_e{yy}_2", (x - w / 2, yy, z - d), (x - w / 2, yy, z), 1.6, m["tag"], parent, 6))
        sh.append(tube(f"{name}_e{yy}_3", (x + w / 2, yy, z - d), (x + w / 2, yy, z), 1.6, m["tag"], parent, 6))
    for xx in (x - w / 2, x + w / 2):
        for zz in (z - d, z):
            sh.append(tube(f"{name}_v{xx}_{zz}", (xx, ys[0], zz), (xx, ys[1], zz), 1.6, m["tag"], parent, 6))
    join(sh, f"{name}_body")
    return {"pad": (x, y + 10, z), "top": (x, ys[1], z - d / 2)}
