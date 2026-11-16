"""Part builders, camera and bead helpers for the POWER tab's VRM page (power_vrm_*.py).

One GPU board, drawn about 3x life size and cut away along z = 0 (the camera sits on +z), so the
cut face shows what runs inside it. Units as everywhere (docs/diagram-pages.md): Y up, x across
the board, z toward the camera.

  board       a thick PCB built layer by layer: green solder mask, copper signal layer, a 12 V
              plane, ground, a thick 0.8 V plane, ground. A window cut through the top layers
              between the bus converter and the left phases lays the 12 V plane's copper bare.
  package     the GPU package at x = 0, cut through its middle: BGA balls, substrate with copper
              vias, C4 bumps, a silicon interposer, two GPU dies and HBM stacks.
  phases      8 phases a side (16): a power stage (DrMOS: driver, high-side and low-side FETs, a
              copper clip, in black mould) and an inductor (ferrite with a copper strap through
              it), with output capacitors next to the package. The front pair is cut open.
  controller  the multiphase controller behind the package; PWM traces wrap round to every stage.
  brick       the intermediate bus converter at the left edge, its case cut open: primary FETs, a
              planar transformer, rectifier FETs; a busbar brings 50 V to it.
  vertical    regulator modules hanging under the board, beneath the package (vertical power).

`stage` and `inductor` take a scale, so the sections can draw one phase far larger. Currents are
glowing beads riding real copper (`run`); `wire` draws a segmented wire with joints (bond wires,
traces), as on the PHOTODIODE page.
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, ball, cut, empty, fly, key, show, tube, mat  # noqa: E402

# ---- materials ------------------------------------------------------------------------------


def materials():
    return {
        "mask": mat("vrm_mask", (0.07, 0.30, 0.16), rough=0.55),
        "fr4": mat("vrm_fr4", (0.55, 0.47, 0.30), rough=0.8),
        "copper": mat("vrm_copper", (0.82, 0.48, 0.28), metal=0.9, rough=0.32),
        "plane12": mat("vrm_plane12", (0.90, 0.56, 0.26), metal=0.9, rough=0.28),
        "plane08": mat("vrm_plane08", (0.78, 0.36, 0.22), metal=0.9, rough=0.3),
        "gnd": mat("vrm_gnd", (0.55, 0.42, 0.34), metal=0.8, rough=0.4),
        "substrate": mat("vrm_substrate", (0.40, 0.26, 0.15), rough=0.75),
        "solder": mat("vrm_solder", (0.74, 0.76, 0.80), metal=0.9, rough=0.25),
        "silicon": mat("vrm_silicon", (0.42, 0.44, 0.50), metal=0.6, rough=0.3),
        "die": mat("vrm_die", (0.26, 0.20, 0.42), metal=0.4, rough=0.3),
        "hbm": mat("vrm_hbm", (0.20, 0.34, 0.62), metal=0.4, rough=0.35),
        "hbm_dram": mat("vrm_hbm_dram", (0.80, 0.52, 0.22), metal=0.3, rough=0.4),
        "mold": mat("vrm_mold", (0.07, 0.07, 0.08), rough=0.6),
        "fet": mat("vrm_fet", (0.36, 0.40, 0.52), metal=0.5, rough=0.3),
        "driver": mat("vrm_driver", (0.25, 0.48, 0.42), metal=0.4, rough=0.35),
        "gold": mat("vrm_gold", (0.88, 0.72, 0.30), metal=0.95, rough=0.25),
        "ferrite": mat("vrm_ferrite", (0.20, 0.20, 0.22), metal=0.2, rough=0.75),
        "mlcc": mat("vrm_mlcc", (0.72, 0.60, 0.42), rough=0.6),
        "mlcc_end": mat("vrm_mlcc_end", (0.80, 0.82, 0.85), metal=0.9, rough=0.25),
        "alu": mat("vrm_alu", (0.70, 0.72, 0.76), metal=0.85, rough=0.3),
        "inner_pcb": mat("vrm_inner_pcb", (0.10, 0.20, 0.14), rough=0.6),
        "ink": mat("vrm_ink", (0.85, 0.85, 0.80), rough=0.6),
        "cold": mat("vrm_cold", (0.55, 0.60, 0.66), metal=0.85, rough=0.3),
        "plastic": mat("vrm_plastic", (0.12, 0.12, 0.13), rough=0.7),
        "dark": mat("vrm_dark", (0.16, 0.17, 0.20), metal=0.5, rough=0.5),
        "screen": mat("vrm_screen", (0.03, 0.05, 0.07), rough=0.3),
        "grid": mat("vrm_grid", (0.24, 0.30, 0.36), rough=0.5),
        # glows
        "v50": mat("vrm_v50", (1.0, 0.95, 0.55), emit=(1.0, 0.92, 0.45), strength=7.0),
        "v12": mat("vrm_v12", (1.0, 0.70, 0.20), emit=(1.0, 0.62, 0.12), strength=7.0),
        "amp": mat("vrm_amp", (1.0, 0.30, 0.15), emit=(1.0, 0.24, 0.10), strength=8.0),
        "pwm": mat("vrm_pwm", (0.30, 0.90, 1.0), emit=(0.20, 0.88, 1.0), strength=8.0),
        "sw": mat("vrm_sw", (1.0, 0.95, 0.80), emit=(1.0, 0.92, 0.70), strength=9.0),
        "hot": mat("vrm_hot", (1.0, 0.45, 0.15), emit=(1.0, 0.38, 0.10), strength=3.0),
        "heat": mat("vrm_heat", (1.0, 0.55, 0.20), emit=(1.0, 0.48, 0.15), strength=5.0),
        "die_hot": mat("vrm_die_hot", (0.85, 0.30, 0.10), emit=(1.0, 0.32, 0.08), strength=1.4),
        "field": mat("vrm_field", (0.55, 0.45, 1.0), emit=(0.50, 0.40, 1.0), strength=5.0),
        "cool": mat("vrm_cool", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=4.0),
        "fail": mat("vrm_fail", (1.0, 0.1, 0.08), emit=(1.0, 0.08, 0.05), strength=4.0),
    }


# ---- shapes ---------------------------------------------------------------------------------


def bx(name, lo, hi, m, parent=None):
    """An axis-aligned box between any two opposite corners (sorted, so mirrored parts keep their
    normals)."""
    a = tuple(min(lo[i], hi[i]) for i in range(3))
    b = tuple(max(lo[i], hi[i]) for i in range(3))
    return O.box(name, a, b, m, parent)


def join(objs, name):
    """Merge meshes into one object (fewer objects in the GLB). All must share a parent."""
    objs = [o for o in objs if o is not None]
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    return o


def polyline(name, pts, r, m, parent=None):
    """A round wire through points `pts`, as one mesh."""
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = r
    cd.bevel_resolution = 2
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


def wire(name, pts, r, m, parent, verts=8):
    """A wire through `pts`: a tube per segment and a ball at each joint, so it reads as one
    segmented piece (the PHOTODIODE page's bond wires)."""
    g = empty(name, parent)
    parts = []
    for k in range(len(pts) - 1):
        parts.append(tube(f"{name}_{k}", pts[k], pts[k + 1], r, m, g, verts))
        if k:
            parts.append(ball(f"{name}_j{k}", pts[k], r, m, g, 8))
    join(parts, f"{name}_mesh")
    return g


def arc(a, b, h, n=10):
    """Points of a bond-wire arc from a to b, raised `h` in y at its middle."""
    pts = []
    for i in range(n + 1):
        t = i / n
        lift = h * math.sin(math.pi * t ** 0.8)
        pts.append(tuple(a[j] + (b[j] - a[j]) * t + (lift if j == 1 else 0.0) for j in range(3)))
    return pts


_bead_mesh = {}


def bead(name, at, size, m, parent, segs=10):
    """A glowing bead at `at`. Beads of one size and material share one mesh, so the GLB holds it
    once."""
    k = (round(size, 3), m.name, segs)
    if k not in _bead_mesh:
        o = ball(f"bead_src_{len(_bead_mesh)}", (0.0, 0.0, 0.0), size, m, None, segs)
        _bead_mesh[k] = o.data
        bpy.data.objects.remove(o)
    o = bpy.data.objects.new(name, _bead_mesh[k])
    bpy.context.collection.objects.link(o)
    o.location = P(*at)
    o.parent = parent
    return o


def run(parent, name, pts, n, size, m, beats, u0, u1, life, until=None):
    """`n` beads that each travel the absolute polyline `pts` over `life` frames, launched one
    after another between fractions u0 and u1 of each beat in `beats` (one beat or a list; the
    same beads go round again in each). A bead vanishes at the end of its beat (or at `until`)."""
    bl = [beats] if isinstance(beats, int) else list(beats)
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        bead(f"{name}{k}_s", pts[0], size, m, e)
        iv = []
        for b in bl:
            end = F(b + 1, 0) if until is None else until
            f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
            f1 = f0 + life
            fly(e, path, f0, f1, steps=max(4, len(pts) * 2))
            iv.append((f0, min(f1, end)))
        show(e, iv)
    return g


def rise(parent, name, base, n, size, m, beats, u0=0.0, u1=0.85, h=30.0, life=60, spread=(0.0, 0.0)):
    """Heat: `n` small glowing beads rising `h` from `base` (spread about it), wobbling a little."""
    bl = [beats] if isinstance(beats, int) else list(beats)
    g = empty(name, parent)
    for k in range(n):
        p0 = (base[0] + spread[0] * math.sin(1.7 * k + 0.4), base[1], base[2] + spread[1] * math.cos(2.3 * k + 0.2))
        path = [(0, 0, 0), (1.5, h * 0.4, 0), (-1.0, h * 0.75, 0), (0.5, h, 0)]
        e = empty(f"{name}{k}", g)
        bead(f"{name}{k}_s", p0, size, m, e, 8)
        iv = []
        for b in bl:
            f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
            fly(e, path, f0, f0 + life, steps=6)
            iv.append((f0, min(f0 + life, F(b + 1, 0))))
        show(e, iv)
    return g


def present(obj, intervals, away=(0.0, -6000.0, 0.0)):
    """Like `show`, but by moving the group out of sight instead of scaling it to nothing (thin
    parts under a scaled-away group can drop out of the export). Visible during each [f0, f1)."""
    O._interp("CONSTANT")
    obj.location = P(*away)
    obj.keyframe_insert("location", frame=0)
    for f0, f1 in intervals:
        obj.location = (0.0, 0.0, 0.0)
        obj.keyframe_insert("location", frame=f0)
        obj.location = P(*away)
        obj.keyframe_insert("location", frame=f1)
    O._constant(obj, "location")


def blink(obj, b, slots, n=8, on=0.5, u0=0.0, u1=1.0):
    """Switch `obj` on for the first `on` of each of its `slots` among `n` equal slots of beat b,
    repeated across [u0, u1) of the beat."""
    iv = []
    w = (u1 - u0) / n
    for s in slots:
        a = u0 + w * s
        iv.append((F(b, a), F(b, a + w * on)))
    show(obj, iv)


# ---- camera -----------------------------------------------------------------------------------

PANE = 0.53
GLIDE = 0.16


def frame(c, size, yaw=0.30, pitch=0.35, pad=1.1, min_d=58.0):
    """A pose that fits a subject `size` units across, centred on c, in the left pane."""
    return (tuple(c), max(size / PANE * pad, min_d), yaw, pitch)


def _eye(t, d, yaw, pitch):
    cp, sp = math.cos(pitch), math.sin(pitch)
    return (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))


def camera_path(root, plan):
    """`plan`: one entry per beat, either a pose or a list of (u, pose) moves within the beat.
    Each pose is reached by u (gliding from the last one) and held with a slow push-in."""
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


# ---- layout ---------------------------------------------------------------------------------

BX0, BX1, BZ0 = -310.0, 250.0, -215.0  # board extents (front edge at z = 0)
# layer stack (y bands), top to bottom
Y_MASK = (-0.8, 0.0)
Y_L1 = (-1.6, -0.8)
Y_D1 = (-4.0, -1.6)
Y_P12 = (-5.6, -4.0)
Y_D2 = (-8.0, -5.6)
Y_G1 = (-9.6, -8.0)
Y_D3 = (-12.0, -9.6)
Y_P08 = (-14.6, -12.0)
Y_D4 = (-17.0, -14.6)
Y_G2 = (-18.4, -17.0)
Y_D5 = (-21.0, -18.4)
Y_MASKB = (-21.8, -21.0)
BOT = -21.8
P12_Y = -4.8  # mid-height of the 12 V plane
P08_Y = -13.3  # mid-height of the 0.8 V plane
WIN = (-222.0, -160.0, -64.0, 0.0)  # x0, x1, z0, z1: window through the top layers to the 12 V plane

# package (x = 0, cut through its middle)
SUB = (-64.0, 64.0, 4.0, 12.0)  # x0, x1, y0, y1
IP = (-46.0, 46.0, 14.0, 17.0)
DIE_Y = (18.0, 23.0)
DIES = ((-30.0, -1.0), (1.0, 30.0))
DIE_Z = -34.0
HBM_X = (-45.0, -32.5)
HBM_Y = (18.0, 27.0)

# phases
PITCH = 24.0
PHASE_Z = [-PITCH * k for k in range(8)]  # the first (k = 0) is cut open by the board's front edge
ST_X = (-128.0, -114.0)  # power stage (left side; the right side mirrors x)
ST_H = 3.2
ST_D = 6.0  # half depth
IN_X = (-106.0, -82.0)  # inductor
IN_H = 16.0
IN_D = 10.0
CAP_X = (-78.0, -70.0)
CTRL = (-14.0, 14.0, -209.0, -193.0)  # controller x0, x1, z0, z1
TR_X = 142.0  # PWM traces run forward along x = -+142..150
BRICK = (-286.0, -226.0, -80.0)  # x0, x1, back z
BUS_Z = (-46.0, -26.0)  # busbar blades (+50 V, return) z centres
VM_Y = (-38.0, BOT)  # vertical modules hang here


def sx(side, x):
    return x if side < 0 else -x


# ---- the board --------------------------------------------------------------------------------


def slab(name, y, mt, parent, hole=None, x0=BX0, x1=BX1, z0=BZ0):
    """One layer over the board, minus a rectangular `hole` (x0, x1, z0, z1) if given."""
    ya, yb = y
    if hole is None:
        return bx(name, (x0, ya, z0), (x1, yb, 0.0), mt, parent)
    hx0, hx1, hz0, hz1 = hole
    parts = [bx(f"{name}_l", (x0, ya, z0), (hx0, yb, 0.0), mt, parent),
             bx(f"{name}_r", (hx1, ya, z0), (x1, yb, 0.0), mt, parent),
             bx(f"{name}_b", (hx0, ya, z0), (hx1, yb, hz0), mt, parent)]
    if hz1 < 0.0:
        parts.append(bx(f"{name}_f", (hx0, ya, hz1), (hx1, yb, 0.0), mt, parent))
    return join(parts, name)


def board(m, parent, window=True):
    """The PCB, layer by layer. With `window`, the top three layers are cut away over WIN, laying
    the 12 V plane bare between the brick and the left stages."""
    g = empty("vrm_board", parent)
    hole = WIN if window else None
    slab("pcb_mask", Y_MASK, m["mask"], g, hole)
    slab("pcb_l1", Y_L1, m["copper"], g, hole)
    slab("pcb_d1", Y_D1, m["fr4"], g, hole)
    slab("pcb_p12", Y_P12, m["plane12"], g)
    slab("pcb_d2", Y_D2, m["fr4"], g)
    slab("pcb_g1", Y_G1, m["gnd"], g)
    slab("pcb_d3", Y_D3, m["fr4"], g)
    slab("pcb_p08", Y_P08, m["plane08"], g)
    slab("pcb_d4", Y_D4, m["fr4"], g)
    slab("pcb_g2", Y_G2, m["gnd"], g)
    slab("pcb_d5", Y_D5, m["fr4"], g)
    slab("pcb_maskb", Y_MASKB, m["mask"], g)
    return g


def vias(m, parent, xs, y0=P08_Y, y1=0.0, name="via", w=0.9):
    """Copper vias on the cut face: thin columns from y0 up to y1 at each x."""
    parts = [bx(f"{name}{i}", (x - w / 2, y0, -1.6), (x + w / 2, y1, 0.3), m["copper"], parent) for i, x in enumerate(xs)]
    return join(parts, name)


# ---- the GPU package -----------------------------------------------------------------------------


def package(m, parent):
    """The GPU package cut through its middle. Returns points and the die-glow group."""
    g = empty("vrm_pkg", parent)
    # BGA balls between board and substrate (the front row cut in half)
    balls = []
    for i in range(15):
        x = -56.0 + 8.0 * i
        for j in range(8):
            z = -8.0 * j
            if 0 < j < 7 and 0 < i < 14:
                continue
            b = ball(f"bga{i}_{j}", (x, 2.0, z), 2.1, m["solder"], g, 10)
            if j == 0:
                cut(b, 0.0)
            balls.append(b)
    join(balls, "bga")
    sx0, sx1, sy0, sy1 = SUB
    bx("sub_core", (sx0, sy0, -64.0), (sx1, sy1, 0.0), m["substrate"], g)
    for k, y in enumerate((5.6, 8.0, 10.4)):
        bx(f"sub_cu{k}", (sx0, y, -64.0), (sx1, y + 0.6, 0.3), m["copper"], g)
    vparts = []
    for i in range(14):
        x = -52.0 + 8.0 * i
        vparts.append(bx(f"sub_via{i}", (x - 0.8, sy0, -1.6), (x + 0.8, sy1, 0.35), m["copper"], g))
    join(vparts, "sub_vias")
    c4 = []
    for i in range(23):
        x = -44.0 + 4.0 * i
        for j in range(11):
            z = -4.0 * j
            if 0 < j < 10 and 0 < i < 22:
                continue
            b = ball(f"c4_{i}_{j}", (x, 13.0, z), 1.0, m["solder"], g, 8)
            if j == 0:
                cut(b, 0.0)
            c4.append(b)
    join(c4, "c4")
    ix0, ix1, iy0, iy1 = IP
    bx("interposer", (ix0, iy0, -46.0), (ix1, iy1, 0.0), m["silicon"], g)
    ub = []
    for i in range(29):
        x = -29.0 + 2.0 * i
        if abs(x) < 1.5:
            continue
        b = ball(f"ub{i}", (x, 17.5, 0.0), 0.5, m["solder"], g, 8)
        cut(b, 0.0)
        ub.append(b)
    join(ub, "ubumps")
    for k, (x0, x1) in enumerate(DIES):
        bx(f"die{k}", (x0, DIE_Y[0], DIE_Z), (x1, DIE_Y[1], 0.0), m["die"], g)
    for s in (-1, 1):
        for j, (z0, z1) in enumerate(((-34.0, -18.5), (-16.0, 0.0))):
            xa, xb = sorted((s * HBM_X[0], s * HBM_X[1]))
            bx(f"hbm{s}_{j}_base", (xa, HBM_Y[0], z0), (xb, HBM_Y[0] + 1.6, z1), m["hbm"], g)
            for n in range(8):
                y = HBM_Y[0] + 1.6 + n * 0.92
                bx(f"hbm{s}_{j}_d{n}", (xa, y + 0.18, z0), (xb, y + 0.92, z1), m["hbm_dram"], g)
                bx(f"hbm{s}_{j}_g{n}", (xa + 0.3, y, z0 + 0.3), (xb - 0.3, y + 0.18, z1 - (0.0 if z1 == 0.0 else 0.3)), m["mold"], g)
    hot = empty("die_glow", parent)
    for k, (x0, x1) in enumerate(DIES):
        bx(f"die_glow{k}", (x0 + 0.4, DIE_Y[1], DIE_Z + 0.4), (x1 - 0.4, DIE_Y[1] + 0.8, 0.08), m["die_hot"], hot)
        bx(f"die_glowf{k}", (x0 + 0.4, DIE_Y[0] + 0.4, 0.0), (x1 - 0.4, DIE_Y[1] - 0.4, 0.1), m["die_hot"], hot)
    pts = {"die": (-15.0, DIE_Y[1], -10.0), "die_r": (15.0, DIE_Y[1], -10.0), "die_face": (-12.0, 20.5, 0.0),
           "sub": (-56.0, 8.0, 0.0), "bga": (-36.0, 2.0, 0.0), "c4": (-38.0, 13.0, 0.0), "ip": (-38.0, 15.5, 0.0),
           "hbm": (-39.0, HBM_Y[1], -8.0), "top": (0.0, DIE_Y[1], -17.0)}
    return g, hot, pts


# ---- one phase -----------------------------------------------------------------------------------


def stage(m, parent, name, x0, x1, zc, y0=0.0, s=1.0, cut_open=False):
    """A power stage (DrMOS) from x0 to x1 (x0 at its 12 V input side; x1 > x0 or < x0 for the
    mirrored side), centred on zc, standing on y0, `s` times the board scale. Cut open, its front
    face shows the lead frame, the high-side FET, the driver, the larger low-side FET under a
    copper clip, and gold bond wires. Returns points and the switch-node glow group."""
    d = 1.0 if x1 > x0 else -1.0
    L = abs(x1 - x0)

    def X(u):  # u in 0..1 across, from the input side
        return x0 + d * L * u

    h = ST_H * s
    hz = ST_D * s
    z1 = 0.0 if cut_open else zc + hz
    g = empty(name, parent)
    bx(f"{name}_mold", (X(0), y0 + 0.5 * s, zc - hz), (X(1), y0 + h, z1), m["mold"], g)
    bx(f"{name}_frame", (X(0.02), y0, zc - hz + 0.3 * s), (X(0.98), y0 + 0.5 * s, z1), m["copper"], g)
    pts = {"in": (X(0.0), y0 + 0.3 * s, zc), "out": (X(1.0), y0 + 0.3 * s, zc), "top": (X(0.5), y0 + h, zc)}
    if cut_open:
        f = 0.25 * s
        bx(f"{name}_hs", (X(0.05), y0 + 0.5 * s, -0.7 * hz), (X(0.27), y0 + 1.3 * s, f), m["fet"], g)
        bx(f"{name}_drv", (X(0.31), y0 + 0.5 * s, -0.5 * hz), (X(0.43), y0 + 1.1 * s, f), m["driver"], g)
        bx(f"{name}_ls", (X(0.47), y0 + 0.5 * s, -0.8 * hz), (X(0.95), y0 + 1.3 * s, f), m["fet"], g)
        clip = [(X(0.48), y0 + 1.5 * s, 0.5 * f), (X(0.92), y0 + 1.5 * s, 0.5 * f), (X(0.99), y0 + 0.6 * s, 0.5 * f)]
        polyline(f"{name}_clip", clip, 0.22 * s, m["copper"], g)
        hs_clip = [(X(0.07), y0 + 1.45 * s, 0.5 * f), (X(0.25), y0 + 1.45 * s, 0.5 * f), (X(0.46), y0 + 1.5 * s, 0.5 * f)]
        polyline(f"{name}_hsclip", hs_clip, 0.16 * s, m["copper"], g)
        r = 0.05 * s
        wire(f"{name}_bw_hs", arc((X(0.33), y0 + 1.1 * s, 0.2 * f), (X(0.22), y0 + 1.3 * s, 0.2 * f), 0.7 * s), r, m["gold"], g)
        wire(f"{name}_bw_ls", arc((X(0.41), y0 + 1.1 * s, 0.2 * f), (X(0.52), y0 + 1.3 * s, 0.2 * f), 0.7 * s), r, m["gold"], g)
        pts.update({"hs": (X(0.16), y0 + 1.3 * s, 0.0), "drv": (X(0.37), y0 + 1.1 * s, 0.0), "ls": (X(0.7), y0 + 1.3 * s, 0.0),
                    "clip": (X(0.8), y0 + 1.6 * s, 0.0), "frame": (X(0.5), y0 + 0.25 * s, 0.0)})
    sw = empty(f"{name}_sw", parent)
    if cut_open:
        polyline(f"{name}_sw_l", [(X(0.48), y0 + 1.55 * s, 0.6 * s), (X(0.92), y0 + 1.55 * s, 0.6 * s), (X(0.99), y0 + 0.6 * s, 0.6 * s)],
                 0.28 * s, m["sw"], sw)
    else:
        bx(f"{name}_sw_b", (X(0.6), y0 + h, zc - 0.5 * hz), (X(0.95), y0 + h + 0.5 * s, zc + 0.5 * hz), m["sw"], sw)
    return pts, sw


def inductor(m, parent, name, x0, x1, zc, y0=0.0, s=1.0, cut_open=False, field=False):
    """A power inductor from x0 (its input end) to x1: a ferrite block with a flat copper strap
    through it, the strap's ends folded down to pads. Cut open, the front shows the strap inside
    the ferrite. Returns points (the strap path for beads) and a field-glow group (if asked)."""
    d = 1.0 if x1 > x0 else -1.0
    L = abs(x1 - x0)

    def X(u):
        return x0 + d * L * u

    h = IN_H * s
    hz = IN_D * s
    z1 = 0.0 if cut_open else zc + hz
    g = empty(name, parent)
    bx(f"{name}_core", (X(0.06), y0 + 0.4 * s, zc - hz), (X(0.94), y0 + h, z1), m["ferrite"], g)
    ys = y0 + 0.45 * h
    t = 1.6 * s
    sz = 0.62 * hz
    zf = 0.0 if cut_open else zc + sz
    if cut_open:
        f = 0.3 * s
        bx(f"{name}_strap", (X(0.04), ys, zc - sz), (X(0.96), ys + t, f), m["copper"], g)
    for u0, u1 in ((0.0, 0.06), (0.94, 1.0)):
        bx(f"{name}_end{u0}", (X(u0), y0, zc - sz), (X(u1), ys + t, zf + (0.04 * s if cut_open else 0.0)), m["copper"], g)
    pts = {"path": [(X(0.03), y0 + 0.6 * s, 0.0), (X(0.03), ys + t / 2, 0.0), (X(0.97), ys + t / 2, 0.0), (X(0.97), y0 + 0.6 * s, 0.0)],
           "in": (X(0.0), y0 + 0.3 * s, zc), "out": (X(1.0), y0 + 0.3 * s, zc), "top": (X(0.5), y0 + h, zc),
           "core": (X(0.25), y0 + 0.8 * h, 0.0), "strap": (X(0.5), ys + t, 0.0)}
    fg = None
    if field:
        fg = empty(f"{name}_field", parent)
        lo, hi = ys - 2.2 * s, ys + t + 2.2 * s
        fz = 0.5 * s
        loop = [(X(0.14), lo, fz), (X(0.86), lo, fz), (X(0.86), hi, fz), (X(0.14), hi, fz), (X(0.14), lo, fz)]
        polyline(f"{name}_field_l", loop, 0.32 * s, m["field"], fg)
        lo2, hi2 = ys - 4.6 * s, ys + t + 4.6 * s
        loop2 = [(X(0.1), lo2, fz), (X(0.9), lo2, fz), (X(0.9), hi2, fz), (X(0.1), hi2, fz), (X(0.1), lo2, fz)]
        polyline(f"{name}_field_l2", loop2, 0.26 * s, m["field"], fg)
    return pts, fg


def mlcc(m, parent, name, c, w=6.0, d=3.0, h=3.0, along="x"):
    """A ceramic capacitor: tan body, silver ends."""
    x, y, z = c
    if along == "x":
        bx(f"{name}_b", (x - w / 2 + 1.0, y, z - d / 2), (x + w / 2 - 1.0, y + h, z + d / 2), m["mlcc"], parent)
        bx(f"{name}_e0", (x - w / 2, y, z - d / 2), (x - w / 2 + 1.0, y + h, z + d / 2), m["mlcc_end"], parent)
        bx(f"{name}_e1", (x + w / 2 - 1.0, y, z - d / 2), (x + w / 2, y + h, z + d / 2), m["mlcc_end"], parent)
    else:
        bx(f"{name}_b", (x - d / 2, y, z - w / 2 + 1.0), (x + d / 2, y + h, z + w / 2 - 1.0), m["mlcc"], parent)
        bx(f"{name}_e0", (x - d / 2, y, z - w / 2), (x + d / 2, y + h, z - w / 2 + 1.0), m["mlcc_end"], parent)
        bx(f"{name}_e1", (x - d / 2, y, z + w / 2 - 1.0), (x + d / 2, y + h, z + w / 2), m["mlcc_end"], parent)


def phases(m, parent, sides=(-1, 1), heat=True):
    """All 16 phases. Returns a dict: groups (all, heat), per-phase points and switch-node groups
    keyed (side, k)."""
    g = empty("vrm_phases", parent)
    hg = empty("vrm_heat", parent) if heat else None
    out = {"group": g, "heat": hg, "st": {}, "ind": {}, "sw": {}}
    for side in sides:
        for k, zc in enumerate(PHASE_Z):
            c = k == 0
            n = f"p{'l' if side < 0 else 'r'}{k}"
            sp, sw = stage(m, g, f"{n}_st", sx(side, ST_X[0]), sx(side, ST_X[1]), zc, cut_open=c)
            ip, _ = inductor(m, g, f"{n}_in", sx(side, IN_X[0]), sx(side, IN_X[1]), zc, cut_open=c)
            # pads and the switch-node trace between stage and inductor
            bx(f"{n}_swpad", (sx(side, ST_X[1] - 0.5), 0.0, zc - 3.0), (sx(side, IN_X[0] + 1.5), 0.35, min(0.02, zc + 3.0)), m["copper"], g)
            for j, dz in enumerate((-5.0, 5.0)):
                if c and dz > 0:
                    continue
                mlcc(m, g, f"{n}_oc{j}", (sx(side, (CAP_X[0] + CAP_X[1]) / 2), 0.0, zc + dz), 7.0, 3.6, 3.0)
            mlcc(m, g, f"{n}_ic", (sx(side, ST_X[0] - 5.0), 0.0, zc - (4.5 if c else 3.5)), 5.0, 2.4, 2.4, along="z")
            out["st"][(side, k)] = sp
            out["ind"][(side, k)] = ip
            out["sw"][(side, k)] = sw
            if hg is not None:
                bx(f"{n}_hot_s", (sx(side, ST_X[0] + 0.5), ST_H, zc - ST_D + 0.5), (sx(side, ST_X[1] - 0.5), ST_H + 1.0, min(zc + ST_D - 0.5, 0.02)),
                   m["hot"], hg)
                bx(f"{n}_hot_i", (sx(side, IN_X[0] + 2.0), IN_H, zc - IN_D + 0.8), (sx(side, IN_X[1] - 2.0), IN_H + 1.0, min(zc + IN_D - 0.8, 0.02)),
                   m["hot"], hg)
    # the 0.8 V copper pour the inductors feed, between them and the package
    for side in sides:
        bx(f"pour08_{side}", (sx(side, IN_X[1] - 3.0), 0.0, BZ0 + 8.0), (sx(side, -60.0), 0.3, 0.02), m["copper"], g)
    return out


def front_path(side):
    """The cut-face path of phase (side, 0): 12 V plane up into the stage, the switch node, the
    inductor's strap, the copper pour, down to the 0.8 V plane, along it under the package, then up
    through a BGA ball, the substrate's via, a C4 bump, the interposer and into the die."""
    zf = 1.0
    xs = lambda x: sx(side, x)  # noqa: E731
    ip_in, ip_out = xs(IN_X[0]), xs(IN_X[1])
    xa = -40.0 if side < 0 else 40.0
    return [
        (xs(ST_X[0] - 30.0), P12_Y, zf), (xs(ST_X[0] - 2.0), P12_Y, zf), (xs(ST_X[0] - 2.0), 0.6, zf), (xs(ST_X[1]), 0.9, zf),
        (xs(IN_X[0] + 0.7), 0.9, zf), (xs(IN_X[0] + 0.7), 7.9, zf), (xs(IN_X[1] - 0.7), 7.9, zf), (xs(IN_X[1] - 0.7), 0.9, zf),
        (xs(-68.0), 0.9, zf), (xs(-68.0), P08_Y, zf), (xa, P08_Y, zf),
        (xa, 2.0, zf + 1.4), (xa, 13.0, zf), (xa, 17.5, zf), (xa * 0.5, 20.5, zf + 0.6),
    ]


def p12_path(k):
    """12 V across the bare plane in the window, from the brick's output tab toward stage (left, k);
    past the window's edge it runs on under the top layers to vias beneath the stage."""
    zc = PHASE_Z[k] if k else -3.0
    y = Y_P12[1] + 0.9
    return [(-215.0, y, -20.0), (-195.0, y, -20.0 + 0.4 * (zc + 20.0)), (-163.0, y, zc)]


def pour_path(side, k):
    """0.8 V from inductor (side, k) across the top copper pour to the package edge."""
    zc = PHASE_Z[k]
    z = min(zc, -1.5)
    return [(sx(side, IN_X[1]), 1.0, z), (sx(side, -62.0), 1.0, z)]


# ---- controller and PWM traces --------------------------------------------------------------------


def controller(m, parent):
    """The multiphase controller (QFN) behind the package, PWM traces wrapping round to every
    stage. Returns its points and, per (side, k), the trace polyline."""
    g = empty("vrm_ctrl", parent)
    x0, x1, z0, z1 = CTRL
    bx("ctrl_body", (x0, 0.0, z0), (x1, 3.0, z1), m["mold"], g)
    for i in range(6):
        u = (i + 0.5) / 6
        bx(f"ctrl_lz{i}", (x0 + (x1 - x0) * u - 0.8, 0.0, z1 - 0.3), (x0 + (x1 - x0) * u + 0.8, 0.6, z1 + 1.2), m["copper"], g)
        bx(f"ctrl_lb{i}", (x0 + (x1 - x0) * u - 0.8, 0.0, z0 - 1.2), (x0 + (x1 - x0) * u + 0.8, 0.6, z0 + 0.3), m["copper"], g)
    tube("ctrl_dot", (x0 + 3.0, 3.0, z1 - 3.0), (x0 + 3.0, 3.15, z1 - 3.0), 1.0, m["ink"], g, 12)
    traces = {}
    y = 0.35
    for side in (-1, 1):
        xe = x0 if side < 0 else x1
        for k, zc in enumerate(PHASE_Z):
            zk = z0 + 2.0 + 1.6 * k
            lane = sx(side, TR_X + 1.2 * (7 - k))
            zt = zc + 2.5 if k else -1.0
            pts = [(xe, y, zk), (lane, y, zk), (lane, y, zt), (sx(side, ST_X[0]), y, zt)]
            wire(f"pwm_{side}_{k}", pts, 0.32, m["copper"], g, verts=6)
            traces[(side, k)] = [(p[0], p[1] + 0.5, p[2]) for p in pts]
    return {"ctrl": ((x0 + x1) / 2, 3.0, (z0 + z1) / 2)}, traces


# ---- the bus converter brick and busbar ----------------------------------------------------------


def brick(m, parent):
    """The intermediate bus converter, case cut open at z = 0, and the busbar bringing 50 V.
    Returns points and the paths for 50 V in and 12 V out."""
    g = empty("vrm_brick", parent)
    x0, x1, zb = BRICK
    # case: base PCB, walls, lid (open at the front)
    bx("brick_pcb", (x0, 0.0, zb), (x1, 2.0, 0.0), m["inner_pcb"], g)
    bx("brick_wl", (x0, 2.0, zb), (x0 + 2.0, 20.0, 0.0), m["alu"], g)
    bx("brick_wr", (x1 - 2.0, 2.0, zb), (x1, 20.0, 0.0), m["alu"], g)
    bx("brick_wb", (x0, 2.0, zb), (x1, 20.0, zb + 2.0), m["alu"], g)
    bx("brick_lid", (x0, 20.0, zb), (x1, 22.0, -16.0), m["alu"], g)
    # primary FETs, the planar transformer (E-core with windings), rectifier FETs, output caps
    f = 0.3
    for i, x in enumerate((x0 + 4.0, x0 + 11.0)):
        bx(f"brick_pfet{i}", (x, 2.0, -14.0), (x + 5.0, 4.5, f), m["mold"], g)
    cx = (x0 + x1) / 2
    bx("xf_yb", (cx - 15.0, 3.0, -50.0), (cx + 15.0, 5.0, f), m["ferrite"], g)
    bx("xf_yt", (cx - 15.0, 15.0, -50.0), (cx + 15.0, 17.0, f), m["ferrite"], g)
    for i, (a, b) in enumerate(((-15.0, -11.0), (-3.0, 3.0), (11.0, 15.0))):
        bx(f"xf_leg{i}", (cx + a, 5.0, -50.0), (cx + b, 15.0, f), m["ferrite"], g)
    for i in range(4):
        y = 5.8 + 2.3 * i
        mt = m["copper"] if i % 2 == 0 else m["gold"]
        for j, (a, b) in enumerate(((-10.4, -3.6), (3.6, 10.4))):
            bx(f"xf_w{i}_{j}", (cx + a, y, -46.0), (cx + b, y + 1.4, f * 2), mt, g)
    for i, x in enumerate((x1 - 17.0, x1 - 10.0)):
        bx(f"brick_sfet{i}", (x, 2.0, -14.0), (x + 5.0, 4.5, f), m["mold"], g)
    for i in range(3):
        mlcc(m, g, f"brick_oc{i}", (x1 - 8.0, 2.0, -30.0 - 8.0 * i), 6.0, 3.0, 3.0)
    # input pins and the busbar (two copper bars from the left)
    bus = {}
    for i, zc in enumerate(BUS_Z):
        bx(f"busbar{i}", (BX0 - 60.0, 6.0, zc - 3.0), (x0, 10.0, zc + 3.0), m["copper"], g)
        bx(f"bus_post{i}", (BX0 + 4.0, 0.0, zc - 3.0), (BX0 + 10.0, 10.0, zc + 3.0), m["copper"], g)
        bus[i] = [(BX0 - 58.0, 10.6, zc), (x0 + 1.0, 10.6, zc)]
    # 12 V output tab into the bare plane
    bx("brick_tab", (x1 - 2.0, 1.0, -26.0), (x1 + 12.0, 3.0, -14.0), m["copper"], g)
    bx("brick_tab_dn", (x1 + 10.0, Y_P12[1], -26.0), (x1 + 12.0, 3.0, -14.0), m["copper"], g)
    p50 = bus[0] + [(x0 + 6.5, 4.8, -8.0), (cx - 8.0, 6.0, 0.6)]
    out12 = [(cx + 7.0, 6.0, 0.6), (x1 - 12.0, 4.8, -8.0), (x1 + 5.0, 3.6, -20.0), (x1 + 11.0, 3.6, -20.0), (x1 + 11.0, Y_P12[1] + 0.9, -20.0)]
    pts = {"brick": (cx, 22.0, -40.0), "xf": (cx, 16.0, 0.0), "pfet": (x0 + 9.0, 4.5, 0.0), "sfet": (x1 - 10.0, 4.5, 0.0),
           "bus": (BX0 - 30.0, 10.0, BUS_Z[0]), "tab": (x1 + 6.0, 3.0, -20.0), "winding": (cx - 7.0, 9.0, 0.0)}
    return pts, {"p50": p50, "ret": bus[1], "out12": out12}


# ---- vertical power -------------------------------------------------------------------------------

VM_XS = ((-50.0, -27.0), (-25.0, -2.0), (2.0, 25.0), (27.0, 50.0))
VM_ZS = ((-52.0, -27.0), (-25.0, 0.0))


def vertical(m, parent):
    """Regulator modules on the board's back, beneath the package: each a power stage over a
    ferrite block with its copper strap, the front row cut open. Returns the group and points.
    The group sits inside a `lift` empty (returned as pts["lift"]) that can slide it up into place."""
    lift = empty("vrm_vlift", parent)
    g = empty("vrm_vertical", lift)
    y0, y1 = VM_Y
    for i, (x0, x1) in enumerate(VM_XS):
        for j, (z0, z1) in enumerate(VM_ZS):
            n = f"vm{i}_{j}"
            front = z1 == 0.0
            bx(f"{n}_st", (x0, y1 - 3.0, z0), (x1, y1, z1), m["mold"], g)
            bx(f"{n}_core", (x0, y0, z0), (x1, y1 - 3.0, z1), m["ferrite"], g)
            if front:
                bx(f"{n}_strap", (x0 + 2.0, y0 + 4.0, z0 + 3.0), (x1 - 2.0, y0 + 6.0, 0.3), m["copper"], g)
                for xa in (x0 + 2.0, x1 - 4.0):
                    bx(f"{n}_leg{xa}", (xa, y0 + 4.0, z0 + 3.0), (xa + 2.0, y1 - 3.0, 0.3), m["copper"], g)
                bx(f"{n}_fets", (x0 + 4.0, y1 - 2.6, z0 + 2.0), (x1 - 4.0, y1 - 1.4, 0.3), m["fet"], g)
    pts = {"vm": (-38.0, (y0 + y1) / 2, 0.0), "vm_top": (0.0, y1, -25.0), "strap": (-14.0, y0 + 6.0, 0.0), "lift": lift}
    return g, pts


def vert_path(x):
    """Straight up from a module's strap, through the board's via, a BGA ball and the substrate
    into the die above."""
    zf = 1.0
    return [(x, VM_Y[0] + 5.0, zf), (x, BOT, zf), (x, 2.0, zf + 1.2), (x, 13.0, zf), (x, 17.5, zf), (x * 0.6, 20.5, zf + 0.5)]


# ---- a scope screen (sections) -----------------------------------------------------------------


def scope(m, parent, c, w, h, name="sc"):
    cx, cy, cz = c
    bx(f"{name}_bezel", (cx - w / 2 - 6, cy - h / 2 - 6, cz - 8.0), (cx + w / 2 + 6, cy + h / 2 + 6, cz - 1.0), m["dark"], parent)
    bx(f"{name}_screen", (cx - w / 2, cy - h / 2, cz - 1.0), (cx + w / 2, cy + h / 2, cz), m["screen"], parent)
    gl = []
    for i in range(-4, 5):
        gl.append(tube(f"{name}_gv{i}", (cx + w / 9 * i, cy - h / 2, cz + 0.1), (cx + w / 9 * i, cy + h / 2, cz + 0.1), 0.18, m["grid"], parent, 6))
    for i in range(-2, 3):
        gl.append(tube(f"{name}_gh{i}", (cx - w / 2, cy + h / 4.5 * i, cz + 0.1), (cx + w / 2, cy + h / 4.5 * i, cz + 0.1), 0.18, m["grid"], parent, 6))
    join(gl, f"{name}_grid")


def offsets(pts):
    p0 = pts[0]
    return [tuple(p[i] - p0[i] for i in range(3)) for p in pts]


def scene(m, root, window=True, vert=True, heat=True, ctrl=True):
    """The whole board: PCB, package, phases, controller, brick, vertical modules (hidden until
    shown). Returns a dict of groups, points and paths."""
    board(m, root, window)
    pg, die_glow, pkp = package(m, root)
    ph = phases(m, root, heat=heat)
    show(die_glow, [])
    if heat and ph["heat"] is not None:
        show(ph["heat"], [])
    cp, traces = controller(m, root) if ctrl else ({}, {})
    bp, bpaths = brick(m, root)
    # vias on the cut face: under the package (0.8 V plane up to the balls) and at the pour
    vias(m, root, [-40.0, -24.0, -8.0, 8.0, 24.0, 40.0], P08_Y, 0.0, "pkg_vias")
    vias(m, root, [-68.0, 68.0], P08_Y, 0.3, "pour_vias", 1.4)
    vias(m, root, [ST_X[0] - 2.0, -ST_X[0] + 2.0], P12_Y, 0.3, "in_vias", 1.2)
    plane_hot = empty("plane_hot", root)
    bx("plane_hot_l", (-120.0, Y_P08[0] + 0.2, 0.0), (120.0, Y_P08[1] - 0.2, 0.15), m["hot"], plane_hot)
    show(plane_hot, [])
    vg = vpts = None
    if vert:
        vg, vpts = vertical(m, root)
        vias(m, root, [-38.5, -14.0, 14.0, 38.5], BOT, 0.0, "vm_vias", 1.4)
        present(vg, [])
    return {"pkg": pkp, "die_glow": die_glow, "ph": ph, "ctrl": cp, "traces": traces, "brick": bp, "bpaths": bpaths,
            "vert": vg, "vpts": vpts, "plane_hot": plane_hot}


# ---- one phase on its own, large (sections) ------------------------------------------------------


def bench_phase(m, parent, o, s=3.0, name="bp"):
    """One phase drawn `s` times the board scale on a strip of board, all cut open at z = 0: the
    12 V plane feeding a via up into the power stage, the stage (FETs, driver, clip), the switch
    node pad, the inductor (ferrite, copper strap, a field glow, hidden until shown), output
    capacitors and the via down to the 0.8 V plane. `o` is the stage's input corner on the board
    top. Returns points, paths (12 V in, switch node + strap, 0.8 V out) and groups."""
    ox, oy, _ = o
    g = empty(name, parent)

    def at(x, y, z=0.0):
        return (ox + s * x, oy + s * y, s * z)

    for n_, (ya, yb), mt in (("mask", Y_MASK, "mask"), ("l1", Y_L1, "copper"), ("d1", Y_D1, "fr4"), ("p12", Y_P12, "plane12"),
                             ("d2", Y_D2, "fr4"), ("g1", Y_G1, "gnd"), ("d3", Y_D3, "fr4"), ("p08", Y_P08, "plane08"),
                             ("d4", Y_D4, "fr4")):
        bx(f"{name}_{n_}", at(-18, ya, -16), at(70, yb, 0), m[mt], g)
    sp, sw = stage(m, g, f"{name}_st", ox, ox + 14 * s, 0.0, oy, s, cut_open=True)
    ip, fg = inductor(m, g, f"{name}_in", ox + 22 * s, ox + 46 * s, 0.0, oy, s, cut_open=True, field=True)
    show(fg, [])
    bx(f"{name}_swpad", at(13.5, 0, -3), at(23.5, 0.35, 0.01), m["copper"], g)
    bx(f"{name}_pour", at(45, 0, -10), at(70, 0.3, 0.01), m["copper"], g)
    for j, z in enumerate((-2.2, -7.0)):
        mlcc(m, g, f"{name}_oc{j}", at(53, 0.3, z), 7.0 * s, 3.4 * s, 3.0 * s)
    mlcc(m, g, f"{name}_ic", at(-7, 0.0, -3.0), 6.0 * s, 3.0 * s, 3.0 * s)
    w = 1.0 * s
    for n_, x, ya, yb in (("vin", -2.0, P12_Y, 0.0), ("vout", 62.0, P08_Y, 0.3)):
        bx(f"{name}_{n_}", (ox + s * x - w / 2, oy + s * ya, -1.6 * s), (ox + s * x + w / 2, oy + s * yb, 0.3 * s), m["copper"], g)
    zf = 0.8 * s
    strap = [(p[0], p[1], zf) for p in ip["path"]]
    paths = {
        "p12": [at(-18, P12_Y, 0), at(-2, P12_Y, 0), at(-2, 0.6, 0), at(1, 0.9, 0)],
        "sw": [at(1, 1.0, 0), at(12, 1.0, 0), at(14, 0.6, 0), at(22.5, 0.6, 0)] + strap,
        "out": [strap[-1], at(62, 0.6, 0), at(62, P08_Y, 0), at(70, P08_Y, 0)],
    }
    for k in paths:
        paths[k] = [(p[0], p[1], zf) for p in paths[k]]
    pts = {"st": sp, "ind": ip, "sw": sw, "field": fg, "caps": at(53, 3.3, -2.2), "p12": at(-12, Y_P12[1], 0), "p08": at(66, Y_P08[1], 0),
           "vin": at(-2, -2.0, 0), "vout": at(62, -6.0, 0), "centre": at(26, 4, 0)}
    return pts, paths
