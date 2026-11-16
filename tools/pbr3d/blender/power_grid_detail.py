"""Part builders, bead and camera helpers for the GRID page (power_grid_{overview,zooms,sections}.py).

Units are drawn units, Y up, camera on +z, cut-away at z = 0 (docs/diagram-pages.md). The grid is
drawn as one diorama at a single scale: a lattice tower is ~400 tall, spans are 380, the whole run
from power plant to data hall is about 3,400 across, so a wide shot sits near 6,000 from the camera
(well inside pbr3d's 40 / 40,000 clip planes) and the smallest close-up (an insulator string, ~40)
still sits past the near plane.

  world()        the whole run, left to right along x:
                 power plant hall (turbine + generator cut open) -> isolated-phase bus -> step-up
                 transformer (GSU, cut open: core limbs, LV/HV windings, porcelain bushings, radiators)
                 -> four double-circuit lattice towers with insulator strings and sagging aluminium
                 conductors -> the campus substation gantry (strain strings, drops, bus on post
                 insulators) -> step-down transformer -> utility meter -> cables -> the data hall
                 (cut open: racks in rows, busways, switchboard, cooling units on the roof) and a gas
                 turbine package beside it (cut open: compressor, combustor, turbine, generator)
  queue()        projects lined up at the substation gate (solar, wind, battery, gas)
  cooling_tower  a nuclear plant's hyperbolic cooling tower
  house, crane   for the chokepoint scenes

Beads ride the real paths (generator bus, conductors with their sag, drops, cables, busways): `run`
is the photodiode page's bead train (fiber_photodiode_detail.run); `wire` its segmented wire.
Materials are all opaque (see-through ones refract like glass in pbr3d).
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, mat, cut, key, fly, show, empty, _smooth  # noqa: E402

# ---- materials ------------------------------------------------------------------------------


def materials():
    return {
        "grass": mat("pg_grass", (0.20, 0.28, 0.16), rough=0.95),
        "gravel": mat("pg_gravel", (0.46, 0.46, 0.44), rough=0.95),
        "road": mat("pg_road", (0.16, 0.16, 0.18), rough=0.9),
        "concrete": mat("pg_concrete", (0.62, 0.61, 0.58), rough=0.85),
        "lattice": mat("pg_lattice", (0.62, 0.64, 0.67), metal=0.7, rough=0.4),
        "conductor": mat("pg_conductor", (0.60, 0.61, 0.63), metal=0.8, rough=0.55),
        "insulator": mat("pg_insulator", (0.30, 0.62, 0.56), metal=0.1, rough=0.2),
        "porcelain": mat("pg_porcelain", (0.48, 0.26, 0.15), rough=0.25),
        "post_ins": mat("pg_post_ins", (0.86, 0.86, 0.84), rough=0.25),
        "tank": mat("pg_tank", (0.40, 0.46, 0.44), metal=0.3, rough=0.5),
        "tank_in": mat("pg_tank_in", (0.24, 0.27, 0.26), metal=0.2, rough=0.6),
        "core": mat("pg_core", (0.24, 0.25, 0.28), metal=0.8, rough=0.35),
        "copper": mat("pg_copper", (0.86, 0.46, 0.24), metal=0.9, rough=0.3),
        "paper": mat("pg_paper", (0.74, 0.60, 0.38), rough=0.6),
        "gen": mat("pg_gen", (0.18, 0.34, 0.56), metal=0.4, rough=0.4),
        "rotor": mat("pg_rotor", (0.30, 0.31, 0.34), metal=0.8, rough=0.3),
        "blade": mat("pg_blade", (0.74, 0.75, 0.78), metal=0.9, rough=0.25),
        "wall": mat("pg_wall", (0.78, 0.78, 0.75), rough=0.8),
        "wall_in": mat("pg_wall_in", (0.55, 0.56, 0.57), rough=0.8),
        "roof": mat("pg_roof", (0.50, 0.51, 0.53), rough=0.7),
        "floor": mat("pg_floor", (0.40, 0.41, 0.43), rough=0.7),
        "rack": mat("pg_rack", (0.07, 0.07, 0.08), metal=0.3, rough=0.5),
        "tray": mat("pg_tray", (0.30, 0.31, 0.33), metal=0.6, rough=0.4),
        "led": mat("pg_led", (0.3, 1.0, 0.5), emit=(0.3, 1.0, 0.5), strength=3.0),
        "busway": mat("pg_busway", (0.70, 0.66, 0.40), metal=0.7, rough=0.35),
        "cabinet": mat("pg_cabinet", (0.70, 0.72, 0.74), metal=0.4, rough=0.45),
        "unit": mat("pg_unit", (0.86, 0.87, 0.87), metal=0.2, rough=0.5),
        "fan": mat("pg_fan", (0.12, 0.12, 0.13), rough=0.6),
        "cable": mat("pg_cable", (0.10, 0.10, 0.11), rough=0.7),
        "gas_pipe": mat("pg_gas_pipe", (0.90, 0.75, 0.15), rough=0.5),
        "stack": mat("pg_stack", (0.58, 0.58, 0.58), metal=0.3, rough=0.6),
        "power": mat("pg_power", (1.0, 0.85, 0.30), emit=(1.0, 0.82, 0.25), strength=4.0),
        "ph_a": mat("pg_ph_a", (1.0, 0.30, 0.22), emit=(1.0, 0.28, 0.2), strength=4.0),
        "ph_b": mat("pg_ph_b", (1.0, 0.85, 0.25), emit=(1.0, 0.82, 0.2), strength=4.0),
        "ph_c": mat("pg_ph_c", (0.30, 0.58, 1.0), emit=(0.28, 0.55, 1.0), strength=4.0),
        "heat": mat("pg_heat", (1.0, 0.45, 0.15), emit=(1.0, 0.42, 0.12), strength=2.5),
        "hot": mat("pg_hot", (1.0, 0.35, 0.10), emit=(1.0, 0.32, 0.08), strength=3.5),
        "flame": mat("pg_flame", (1.0, 0.70, 0.30), emit=(1.0, 0.62, 0.25), strength=6.0),
        "scan": mat("pg_scan", (0.30, 0.90, 1.0), emit=(0.25, 0.85, 1.0), strength=3.0),
        "tile": mat("pg_tile", (0.22, 0.24, 0.28), rough=0.6),
        "tile_lit": mat("pg_tile_lit", (1.0, 0.75, 0.25), emit=(1.0, 0.7, 0.2), strength=3.0),
        "solar": mat("pg_solar", (0.08, 0.12, 0.32), metal=0.6, rough=0.2),
        "white": mat("pg_white", (0.90, 0.90, 0.90), rough=0.5),
        "battery": mat("pg_battery", (0.84, 0.86, 0.88), metal=0.2, rough=0.5),
        "pallet": mat("pg_pallet", (0.36, 0.38, 0.42), rough=0.7),
        "house": mat("pg_house", (0.80, 0.72, 0.58), rough=0.8),
        "shingle": mat("pg_shingle", (0.45, 0.20, 0.16), rough=0.8),
        "bar": mat("pg_bar", (0.35, 0.52, 0.78), metal=0.2, rough=0.5),
        "bar_old": mat("pg_bar_old", (0.40, 0.44, 0.52), rough=0.6),
        "bar_hi": mat("pg_bar_hi", (1.0, 0.75, 0.25), emit=(1.0, 0.7, 0.2), strength=1.2),
        "bar_ghost": mat("pg_bar_ghost", (0.55, 0.40, 0.25), rough=0.6),
        "price": mat("pg_price", (1.0, 0.25, 0.15), emit=(1.0, 0.2, 0.1), strength=1.5),
        "crane": mat("pg_crane", (0.95, 0.70, 0.10), metal=0.4, rough=0.45),
    }


# ---- a mesh builder: many parts, one object -------------------------------------------------


class MB:
    """Collects tubes, boxes and balls (poly coordinates) into one mesh, so a lattice tower or a row
    of racks is one object in the GLB."""

    def __init__(self):
        self.v, self.f = [], []

    def _add(self, vs, fs):
        b = len(self.v)
        self.v += [tuple(P(*p)) for p in vs]
        self.f += [tuple(b + i for i in f) for f in fs]

    def tube(self, a, b, r, n=6, caps=None):
        a, b = Vector(a), Vector(b)
        d = b - a
        if d.length < 1e-6:
            return
        d.normalize()
        up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
        u = d.cross(up).normalized()
        w = d.cross(u)
        ring = [(u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * r for k in range(n)]
        vs = [tuple(a + o) for o in ring] + [tuple(b + o) for o in ring]
        fs = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
        if caps is None:
            caps = r > 2.5
        if caps:
            fs += [tuple(reversed(range(n))), tuple(n + k for k in range(n))]
        self._add(vs, fs)

    def box(self, lo, hi):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        vs = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
        self._add(vs, fs)

    def ball(self, c, r, n=6):
        vs, fs = [], []
        rings = n // 2
        for i in range(1, rings):
            t = math.pi * i / rings
            for k in range(n):
                p = 2 * math.pi * k / n
                vs.append((c[0] + r * math.sin(t) * math.cos(p), c[1] + r * math.cos(t), c[2] + r * math.sin(t) * math.sin(p)))
        top, bot = len(vs), len(vs) + 1
        vs += [(c[0], c[1] + r, c[2]), (c[0], c[1] - r, c[2])]
        for i in range(rings - 2):
            for k in range(n):
                a, b = i * n + k, i * n + (k + 1) % n
                fs.append((a, b, b + n, a + n))
        for k in range(n):
            fs.append((top, (k + 1) % n, k))
            last = (rings - 2) * n
            fs.append((bot, last + k, last + (k + 1) % n))
        self._add(vs, fs)

    def prism(self, x0, x1, base, ridge):
        """A gable roof along x: `base` is ((z0, y0), (z1, y0)), `ridge` (zr, yr)."""
        (za, ya), (zb, yb) = base
        zr, yr = ridge
        vs = [(x0, ya, za), (x0, yb, zb), (x0, yr, zr), (x1, ya, za), (x1, yb, zb), (x1, yr, zr)]
        fs = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        self._add(vs, fs)

    def obj(self, name, m, parent=None, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(m)
        o.parent = parent
        if smooth:
            _smooth(o)
        return o


def solid(name, m, parent, build, smooth=False):
    """One object from a builder function that fills an MB."""
    mb = MB()
    build(mb)
    return mb.obj(name, m, parent, smooth)


def box(name, lo, hi, m, parent=None):
    return solid(name, m, parent, lambda mb: mb.box(lo, hi))


def tube(name, a, b, r, m, parent=None, n=16):
    return solid(name, m, parent, lambda mb: mb.tube(a, b, r, n), smooth=True)


def ball(name, c, r, m, parent=None, n=12):
    return solid(name, m, parent, lambda mb: mb.ball(c, r, n), smooth=True)


def rod_x(name, x0, x1, r, m, parent=None, cy=0.0, cz=0.0, n=40, half=True):
    """A solid cylinder along x, cut at z = 0 when `half`."""
    o = tube(name, (x0, cy, cz), (x1, cy, cz), r, m, parent, n)
    return cut(o, 0.0) if half else o


def pipe_x(name, x0, x1, ro, ri, m, parent=None, cy=0.0, half=True, verts=48):
    """A hollow cylinder along x (axis at height cy, z = 0); `half` keeps z <= 0 and caps the cut."""
    a0, a1 = (math.pi, 2 * math.pi) if half else (0.0, 2 * math.pi)
    n = verts // 2 if half else verts
    angles = [a0 + (a1 - a0) * i / n for i in range(n + 1 if half else n)]
    rings = [(x0, ro), (x1, ro), (x1, ri), (x0, ri)]
    vs = [tuple(P(x, cy + r * math.cos(t), r * math.sin(t))) for x, r in rings for t in angles]
    return _ring_mesh(name, vs, len(angles), half, m, parent)


def pipe_y(name, y0, y1, ro, ri, m, parent=None, cx=0.0, cz=0.0, half=True, verts=40):
    """A hollow cylinder standing on y (axis at x = cx, z = cz), cut at z = 0 when `half`."""
    a0, a1 = (math.pi, 2 * math.pi) if half else (0.0, 2 * math.pi)
    n = verts // 2 if half else verts
    angles = [a0 + (a1 - a0) * i / n for i in range(n + 1 if half else n)]
    rings = [(y0, ro), (y1, ro), (y1, ri), (y0, ri)]
    vs = [tuple(P(cx + r * math.cos(t), y, cz + r * math.sin(t))) for y, r in rings for t in angles]
    return _ring_mesh(name, vs, len(angles), half, m, parent)


def _ring_mesh(name, vs, k, half, m, parent):
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
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    _smooth(o)
    return o


def lathe(name, profile, m, parent=None, c=(0.0, 0.0, 0.0), n=40):
    """A solid of revolution about the vertical axis through c: profile = [(r, y), ...] bottom to top."""
    vs, fs = [], []
    for r, y in profile:
        for k in range(n):
            t = 2 * math.pi * k / n
            vs.append(tuple(P(c[0] + r * math.cos(t), c[1] + y, c[2] + r * math.sin(t))))
    for i in range(len(profile) - 1):
        for k in range(n):
            a, b = i * n + k, i * n + (k + 1) % n
            fs.append((a, b, b + n, a + n))
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    mod = o.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = 4.0
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.selected_objects:
        s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    _smooth(o)
    return o


# ---- wires and beads (the photodiode page's arched, segmented wires) -------------------------


def curve_pts(a, b, lift, n=10):
    """Points on an arc from a to b, bowed by the offset vector `lift` at the middle (a parabola:
    with lift (0, -sag, 0) it is a conductor's catenary)."""
    out = []
    for k in range(n + 1):
        u = k / n
        w = 4 * u * (1 - u)
        out.append(tuple(a[i] + (b[i] - a[i]) * u + lift[i] * w for i in range(3)))
    return out


def wire_into(mb, pts, r, n=6, joints=False):
    """A segmented wire through `pts` into an MB: a tube per segment, a ball at each joint."""
    for k in range(len(pts) - 1):
        mb.tube(pts[k], pts[k + 1], r, n, caps=False)
        if joints and k:
            mb.ball(pts[k], r * 1.15, n)


def wire(name, pts, r, m, parent=None, n=8):
    return solid(name, m, parent, lambda mb: wire_into(mb, pts, r, n), smooth=True)


def join_paths(*paths):
    out = []
    for p in paths:
        if out and math.dist(out[-1], p[0]) < 1e-6:
            out += list(p[1:])
        else:
            out += list(p)
    return out


def run(parent, name, pts, n, size, m, b, u0, u1, life, until=None):
    """`n` beads that each travel the absolute polyline `pts` over `life` frames, launched one
    after another between fractions u0 and u1 of beat `b` (fiber_photodiode_detail.run)."""
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    end = until if until is not None else F(b + 1, 0)
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, m, e, 10)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=min(120, max(4, len(pts) * 2)))
        show(e, [(f0, min(f1, end))])
    return g


def rise(parent, name, base, n, size, m, b, u0, u1, life, h=120.0, drift=(10.0, 0.0)):
    """Heat: `n` blobs rising `h` above `base` (with a little drift), launched through beat b."""
    pts = [base, (base[0] + drift[0] * 0.5, base[1] + h * 0.5, base[2] + drift[1] * 0.5),
           (base[0] + drift[0], base[1] + h, base[2] + drift[1])]
    return run(parent, name, pts, n, size, m, b, u0, u1, life)


# ---- the lattice tower ----------------------------------------------------------------------

ARMS = ((250.0, 70.0), (300.0, 92.0), (350.0, 70.0))  # (height, reach) per phase, bottom to top
STRING = 38.0  # suspension insulator string length
PHASES = ("C", "B", "A")  # bottom, middle, top arm


def tower_frame(mb, x, z0=0.0, wb=44.0, wt=13.0, top=None):
    """A four-legged lattice tower body with its cross-arms into mb (steel). `top` stops the build
    at that height (a tower under construction)."""
    levels = [0, 45, 90, 135, 180, 220, 250, 272, 300, 322, 350, 375]
    if top is not None:
        levels = [y for y in levels if y <= top]

    def hw(y):
        return wb + (wt - wb) * min(y, 220.0) / 220.0

    def corners(y):
        h = hw(y)
        return [(x - h, y, z0 - h), (x + h, y, z0 - h), (x + h, y, z0 + h), (x - h, y, z0 + h)]

    for i in range(len(levels) - 1):
        lo, hi = corners(levels[i]), corners(levels[i + 1])
        for k in range(4):
            mb.tube(lo[k], hi[k], 2.6, 6)
            j = (k + 1) % 4
            mb.tube(lo[k], hi[j], 1.0, 4)
            mb.tube(lo[j], hi[k], 1.0, 4)
    for y in levels[1:]:
        c = corners(y)
        for k in range(4):
            mb.tube(c[k], c[(k + 1) % 4], 1.2, 4)
    tips = {}
    if top is None:
        for ya, reach in ARMS:
            for s in (1, -1):
                tip = (x, ya, z0 + s * reach)
                for sx in (-1, 1):
                    mb.tube((x + sx * wt, ya, z0 + s * wt), tip, 1.8, 5)
                    mb.tube((x + sx * wt, ya + 22.0, z0 + s * wt), tip, 1.4, 5)
                for f in (0.35, 0.65):
                    zf = z0 + s * (wt + (reach - wt) * f)
                    mb.tube((x - wt * (1 - f), ya, zf), (x, ya + 22.0 * (1 - f), zf), 0.9, 4)
                    mb.tube((x + wt * (1 - f), ya, zf), (x, ya + 22.0 * (1 - f), zf), 0.9, 4)
                tips[(s, ya)] = tip
        for s in (1, -1):  # earth-wire peaks
            peak = (x, 400.0, z0 + s * 34.0)
            for sx in (-1, 1):
                mb.tube((x + sx * wt, 375.0, z0 + s * wt), peak, 1.4, 5)
                mb.tube((x + sx * wt, 375.0, z0 - s * wt), peak, 1.0, 4)
    return tips


def string_into(mb_ins, mb_steel, top, length=STRING, axis=(0.0, -1.0, 0.0), discs=10, r=4.6):
    """An insulator string from `top` along `axis`: a steel rod, `discs` glass discs, a clamp.
    Returns the conductor's attachment point."""
    ax = Vector(axis).normalized()
    t = Vector(top)
    end = t + ax * length
    mb_steel.tube(tuple(t), tuple(end), 0.7, 5)
    for k in range(discs):
        c = t + ax * (4.0 + (length - 7.0) * k / max(1, discs - 1))
        mb_ins.tube(tuple(c - ax * 0.7), tuple(c + ax * 0.7), r, 8)
    mb_steel.tube(tuple(end - ax * 1.5), tuple(end + ax * 1.5), 2.0, 6)
    return tuple(end)


def tower(m, parent, x, name, z0=0.0, top=None):
    """A double-circuit lattice tower at x: body and arms (galvanised steel), concrete footings,
    and a suspension string at each arm tip. Returns {(side, phase): clamp point} and peaks."""
    st, ins, conc = MB(), MB(), MB()
    tips = tower_frame(st, x, z0, top=top)
    for sx in (-1, 1):
        for sz in (-1, 1):
            conc.box((x + sx * 44 - 7, -2, z0 + sz * 44 - 7), (x + sx * 44 + 7, 6, z0 + sz * 44 + 7))
    clamps = {}
    for (s, ya), tip in tips.items():
        ph = PHASES[[a[0] for a in ARMS].index(ya)]
        clamps[(s, ph)] = string_into(ins, st, tip)
    st.obj(f"{name}_steel", m["lattice"], parent, smooth=True)
    if ins.v:
        ins.obj(f"{name}_ins", m["insulator"], parent, smooth=True)
    conc.obj(f"{name}_feet", m["concrete"], parent)
    peaks = {s: (x, 400.0, z0 + s * 34.0) for s in (1, -1)}
    return clamps, peaks


# ---- layout --------------------------------------------------------------------------------

HALL0, HALL1 = -1520.0, -1180.0  # turbine hall x
AXIS_Y = 70.0  # turbine-generator axis height
TURB = (-1490.0, -1370.0)
GEN = (-1350.0, -1230.0)
GSU = (-1110.0, -980.0)  # step-up transformer tank x
GSU_LIMBS = (-1080.0, -1045.0, -1010.0)
TOWERS = (-850.0, -470.0, -90.0, 290.0)
GX = 620.0  # gantry
SUB_T = (700.0, 790.0)  # step-down transformer tank x
SUB_LIMBS = (722.0, 745.0, 768.0)
BUS_Y = 185.0
BUS_Z = {"A": -25.0, "B": -45.0, "C": -65.0}
GANTRY_Z = {"A": 30.0, "B": 60.0, "C": 90.0}
METER = (870.0, 0.0, 10.0)
DH = (950.0, 1450.0)  # data hall x
DH_Z = -260.0
DH_TOP = 150.0
ROWS = (-45.0, -115.0, -185.0)
RACK_W, RACK_H, RACK_D = 22.0, 70.0, 24.0
GT = (1500.0, 1720.0)  # gas turbine package x
SAG = 34.0
LV_Z = (-20.0, -35.0, -50.0)


def ground(m, root, x0=-3200.0, x1=3400.0, z0=-2500.0, z1=2600.0):
    box("pg_ground", (x0, -8.0, z0), (x1, 0.0, z1), m["grass"], root)


def plant(m, root):
    """The turbine hall cut open: a turbine (blade rows) and generator (stator, windings, rotor) on
    one shaft, a stack outside. Returns points."""
    g = empty("pg_plant", root)
    w = MB()
    w.box((HALL0, 0, DH_Z + 40), (HALL1, 4, 0))  # floor
    w.box((HALL0, 4, -224), (HALL1, 200, -216))  # back wall
    w.box((HALL0, 4, -224), (HALL0 + 8, 200, 0))
    w.box((HALL1 - 8, 4, -224), (HALL1, 200, 0))
    w.box((HALL0 - 4, 200, -228), (HALL1 + 4, 210, -40))  # roof, cut short so the hall reads open
    w.obj("pg_hall_walls", m["wall"], g)
    box("pg_hall_gravel", (HALL0 - 20, 0, -260), (GSU[1] + 60, 1.5, 120), m["gravel"], g)
    # turbine: casing, blade rows growing toward the generator, the shaft
    pipe_x("pg_turb_case", TURB[0], TURB[1], 56, 48, m["stack"], g, AXIS_Y)
    blades = MB()
    for k in range(9):
        x = TURB[0] + 10 + k * 12.0
        r = 20.0 + 3.0 * k
        blades.tube((x - 1.6, AXIS_Y, 0.0), (x + 1.6, AXIS_Y, 0.0), r, 28)
    o = blades.obj("pg_turb_blades", m["blade"], g)
    cut(o, 0.5)
    rod_x("pg_shaft", TURB[0] - 20, GEN[1] + 30, 8.0, m["rotor"], g, AXIS_Y)
    # generator: blue frame, laminated stator core, copper bars in its slots, the rotor
    pipe_x("pg_gen_frame", GEN[0], GEN[1], 64, 52, m["gen"], g, AXIS_Y)
    pipe_x("pg_gen_stator", GEN[0] + 6, GEN[1] - 6, 52, 40, m["core"], g, AXIS_Y)
    bars = MB()
    for k in range(1, 12):
        t = math.pi + math.pi * k / 12
        y, z = AXIS_Y + 44 * math.cos(t), 44 * math.sin(t)
        bars.box((GEN[0] + 2, y - 2.5, z - 2.5), (GEN[1] - 2, y + 2.5, min(0.0, z + 2.5)))
    bars.obj("pg_gen_bars", m["copper"], g)
    rod_x("pg_gen_rotor", GEN[0] + 10, GEN[1] - 10, 32, m["rotor"], g, AXIS_Y)
    bands = MB()
    for k in range(5):
        x = GEN[0] + 18 + k * 20
        bands.tube((x - 4, AXIS_Y, 0.0), (x + 4, AXIS_Y, 0.0), 33.5, 32)
    o = bands.obj("pg_gen_field", m["copper"], g)
    cut(o, 0.3)
    ped = MB()
    for x in (TURB[0] - 12, GEN[0] - 10, GEN[1] + 16):
        ped.box((x - 6, 4, -30), (x + 6, AXIS_Y - 6, 0))
    ped.obj("pg_pedestals", m["dark"] if "dark" in m else m["rotor"], g)
    # stack and its base outside
    tube("pg_stack", (HALL0 + 40, 0, -300), (HALL0 + 40, 430, -300), 26, m["stack"], g, 24)
    # isolated-phase bus: three ducts up off the generator and across to the GSU's LV bushings
    gx = GEN[0] + 70
    lv_tops = [(GSU[0] + 18, 190.0, z) for z in LV_Z]
    bus = []
    for k, z in enumerate(LV_Z):
        p = [(gx, AXIS_Y + 50, z), (gx, 214.0, z), (GSU[0] + 18, 214.0, z), lv_tops[k]]
        bus.append(p)
    duct = MB()
    for p in bus:
        for a, b in zip(p, p[1:]):
            duct.tube(a, b, 5.5, 12)
        duct.ball(p[1], 5.5, 10)
        duct.ball(p[2], 5.5, 10)
    duct.obj("pg_ipb", m["blade"], g, smooth=True)
    return {"gen": (GEN[0] + 60, AXIS_Y + 64, 0.0), "rotor": (GEN[0] + 40, AXIS_Y + 20, 0.0),
            "bars": (GEN[0] + 60, AXIS_Y - 44, 0.0), "turbine": (TURB[0] + 60, AXIS_Y + 50, 0.0),
            "blades": (TURB[0] + 70, AXIS_Y + 40, 0.0), "stack": (HALL0 + 40, 430.0, -300.0),
            "bus": bus, "hall": (HALL0 + 170, 200.0, -100.0)}


def transformer(m, root, x0, x1, limbs, name, y0=15.0, y1=160.0, zb=-90.0, hv_h=80.0, lv_side="left"):
    """A power transformer tank cut open at z = 0: three core limbs with yokes, LV (inner) and HV
    (outer, paper-wrapped) windings, radiators on the right, porcelain bushings and a conservator on
    top. Returns points (HV bushing tops, LV bushing tops, winding centres)."""
    g = empty(name, root)
    t = MB()
    t.box((x0, y0, zb), (x1, y0 + 4, 0))
    t.box((x0, y0, zb - 4), (x1, y1, zb))
    t.box((x0 - 4, y0, zb - 4), (x0, y1, 0))
    t.box((x1, y0, zb - 4), (x1 + 4, y1, 0))
    t.box((x0 - 4, y1, zb - 4), (x1 + 4, y1 + 5, 0))
    t.obj(f"{name}_tank", m["tank"], g)
    box(f"{name}_inside", (x0, y0 + 4, zb), (x1, y1, zb + 2), m["tank_in"], g)
    box(f"{name}_pad", (x0 - 20, -2, zb - 30), (x1 + 50, y0, 30), m["concrete"], g)
    hl = 6.0
    c = MB()
    for x in limbs:
        c.box((x - hl, y0 + 14, -hl), (x + hl, y1 - 14, 0))
    c.box((limbs[0] - hl - 8, y0 + 8, -hl), (limbs[-1] + hl + 8, y0 + 22, 0))
    c.box((limbs[0] - hl - 8, y1 - 22, -hl), (limbs[-1] + hl + 8, y1 - 8, 0))
    c.obj(f"{name}_core", m["core"], g)
    pitch = limbs[1] - limbs[0]
    for k, x in enumerate(limbs):
        pipe_y(f"{name}_lv{k}", y0 + 26, y1 - 26, hl + 5.5, hl + 1.5, m["copper"], g, cx=x)
        pipe_y(f"{name}_hv{k}", y0 + 24, y1 - 24, pitch / 2 - 1.0, hl + 7.5, m["paper"], g, cx=x)
    rad = MB()
    for k in range(8):
        z = zb + 8 + k * (-zb - 18) / 7
        rad.box((x1 + 4, y0 + 10, z - 1.8), (x1 + 34, y1 - 14, z + 1.8))
    rad.tube((x1 + 4, y1 - 20, zb + 8), (x1 + 34, y1 - 20, zb + 8), 3, 8)
    rad.obj(f"{name}_radiators", m["tank"], g)
    hv_tops = []
    sheds = MB()
    cores = MB()
    for x in limbs:
        base = (x, y1 + 5, zb / 2)
        top = (x, y1 + 5 + hv_h, zb / 2)
        cores.tube(base, top, 3.5, 10)
        nsh = int(hv_h / 8)
        for k in range(nsh):
            y = y1 + 10 + k * (hv_h - 12) / max(1, nsh - 1)
            sheds.tube((x, y - 1.3, zb / 2), (x, y + 1.3, zb / 2), 8.0, 16)
        cores.tube((x, top[1] - 2, zb / 2), (x, top[1] + 4, zb / 2), 5.0, 10)
        hv_tops.append((x, top[1] + 4, zb / 2))
    lv_tops = []
    lx = x0 + 18 if lv_side == "left" else x1 - 18
    for k, z in enumerate((-20.0, -35.0, -50.0)):
        base = (lx, y1 + 5, z)
        top = (lx, y1 + 25, z)
        cores.tube(base, top, 3.0, 10)
        sheds.tube((lx, y1 + 12, z), (lx, y1 + 14, z), 5.5, 12)
        sheds.tube((lx, y1 + 19, z), (lx, y1 + 21, z), 5.5, 12)
        lv_tops.append(top)
    sheds.obj(f"{name}_sheds", m["porcelain"], g, smooth=True)
    cores.obj(f"{name}_bushing_cores", m["porcelain"], g, smooth=True)
    tube(f"{name}_conservator", (x0 + 10, y1 + hv_h * 0.55, zb - 6), (x1 - 30, y1 + hv_h * 0.55, zb - 6),
         13, m["tank"], g, 20)
    tube(f"{name}_cons_pipe", (x1 - 40, y1 + 5, zb - 6), (x1 - 40, y1 + hv_h * 0.55, zb - 6), 2.5, m["tank"], g, 8)
    mid = (y0 + y1) / 2
    return {"hv": hv_tops, "lv": lv_tops, "core": (limbs[1], y1 - 15, 0.0), "lv_w": (limbs[0] + hl + 3.5, mid, 0.0),
            "hv_w": (limbs[0] + pitch / 2 - 3, mid + 20, 0.0), "tank": (x0, y1 - 20, 0.0),
            "radiator": (x1 + 30, mid, zb + 8), "bushing": (limbs[1], y1 + hv_h * 0.6, zb / 2),
            "limbs": limbs, "mid": mid}


def gantry(m, root):
    """The substation's dead-end gantry: two lattice columns and a box-truss beam, a strain string
    per phase reaching back toward the line. Returns the strain ends (where the line lands)."""
    st, ins = MB(), MB()
    for zc in (-118.0, 118.0):
        for i, (ya, yb) in enumerate(((0, 60), (60, 120), (120, 180), (180, 252))):
            for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                st.tube((GX + sx * 9, ya, zc + sz * 9), (GX + sx * 9, yb, zc + sz * 9), 2.0, 6)
            st.tube((GX - 9, ya, zc - 9), (GX + 9, yb, zc - 9), 0.9, 4)
            st.tube((GX - 9, ya, zc + 9), (GX + 9, yb, zc + 9), 0.9, 4)
            st.tube((GX - 9, ya, zc - 9), (GX - 9, yb, zc + 9), 0.9, 4)
            st.tube((GX + 9, ya, zc - 9), (GX + 9, yb, zc + 9), 0.9, 4)
    for y in (236.0, 252.0):
        for sx in (-1, 1):
            st.tube((GX + sx * 7, y, -127), (GX + sx * 7, y, 127), 1.8, 6)
    for k in range(-12, 13):
        z = k * 10.0
        st.tube((GX - 7, 236, z), (GX + 7, 252, z + 10), 0.8, 4)
        st.tube((GX - 7, 236, z), (GX - 7, 252, z + 5), 0.8, 4)
    ends = {}
    for ph, zg in GANTRY_Z.items():
        for s in (1, -1):
            ends[(s, ph)] = string_into(ins, st, (GX - 8, 238.0, s * zg), 30.0, (-1.0, 0.0, 0.0), 8, 4.2)
    for zc in (-118.0, 118.0):
        box(f"pg_gantry_foot{int(zc)}", (GX - 14, -2, zc - 14), (GX + 14, 6, zc + 14), m["concrete"], root)
    st.obj("pg_gantry_steel", m["lattice"], root, smooth=True)
    ins.obj("pg_gantry_ins", m["insulator"], root, smooth=True)
    return ends


def substation(m, root, ends):
    """Drops from the gantry, rigid bus on post insulators, the step-down transformer, the fence and
    gravel, the utility meter and the cables to the hall. Returns points and paths."""
    box("pg_sub_gravel", (GX - 70, 0, -160), (920.0, 1.5, 150), m["gravel"], root)
    sd = transformer(m, root, SUB_T[0], SUB_T[1], SUB_LIMBS, "pg_sdt", y0=10.0, y1=118.0, zb=-80.0, hv_h=56.0,
                     lv_side="right")
    drops, buses = {}, {}
    cond = MB()
    stands, posts = MB(), MB()
    for k, ph in enumerate(("A", "B", "C")):
        zb = BUS_Z[ph]
        hv = sd["hv"][k]
        bus = [(GX + 18, BUS_Y, zb), (hv[0], BUS_Y, zb)]
        jumper = curve_pts(bus[1], hv, (0, 4, 0), 4)
        buses[ph] = bus + jumper[1:]
        wire_into(cond, bus, 2.4)
        wire_into(cond, jumper, 1.6)
        for xp in (GX + 30, GX + 64):
            stands.tube((xp, 0, zb), (xp, BUS_Y - 44, zb), 3.0, 8)
            for j in range(7):
                y = BUS_Y - 40 + j * 5.5
                posts.tube((xp, y - 1, zb), (xp, y + 1, zb), 5.0, 12)
            posts.tube((xp, BUS_Y - 42, zb), (xp, BUS_Y - 2, zb), 2.4, 8)
        for s in (1, -1):
            e = ends[(s, ph)]
            d = curve_pts(e, (GX + 18, BUS_Y, zb), (6, -8, 0), 8)
            wire_into(cond, d, 1.6)
            drops[(s, ph)] = d
    cond.obj("pg_sub_conductors", m["conductor"], root, smooth=True)
    stands.obj("pg_sub_stands", m["lattice"], root)
    posts.obj("pg_sub_posts", m["post_ins"], root, smooth=True)
    fence = MB()
    for x in range(int(GX - 60), 921, 40):
        fence.tube((x, 0, -155), (x, 46, -155), 1.6, 5)
    for y in (16.0, 30.0, 44.0):
        fence.tube((GX - 60, y, -155), (920, y, -155), 0.7, 4)
    fence.obj("pg_fence", m["lattice"], root)
    # the utility meter at the property line, and the cables to the hall's switchboard
    mx, _, mz = METER
    box("pg_meter", (mx - 14, 0, mz - 10), (mx + 14, 52, mz + 10), m["cabinet"], root)
    box("pg_meter_face", (mx - 7, 30, mz + 10), (mx + 7, 44, mz + 11), m["fan"], root)
    lv, cables = [], MB()
    for k, top in enumerate(sd["lv"]):
        z = LV_Z[k]
        p = [top, (top[0] + 22, top[1] + 4, z), (SUB_T[1] + 40, 60, z), (SUB_T[1] + 52, 3, z),
             (mx, 3, z), (DH[0] + 20, 3, z), (DH[0] + 26, 60, z), (DH[0] + 26, 88, z)]
        lv.append(p)
        wire_into(cables, p, 3.0, 8)
    cables.obj("pg_lv_cables", m["cable"], root, smooth=True)
    return {"sd": sd, "drops": drops, "buses": buses, "lv": lv, "meter": (mx, 52.0, mz),
            "bus": (GX + 46, BUS_Y, BUS_Z["B"]), "posts": (GX + 30, BUS_Y - 25, BUS_Z["C"]),
            "fence": (GX - 30, 46.0, -155.0)}


def hall(m, root):
    """The data hall cut open: racks in three rows with green status lights, a busway over each row
    with taps down to the racks, the switchboard, cooling units and fans on the roof."""
    g = empty("pg_dh", root)
    x0, x1 = DH
    w = MB()
    w.box((x0, 0, DH_Z), (x1, 4, 0))
    w.box((x0, 4, DH_Z), (x1, DH_TOP, DH_Z + 8))
    w.box((x0, 4, DH_Z), (x0 + 8, DH_TOP, 0))
    w.box((x1 - 8, 4, DH_Z), (x1, DH_TOP, 0))
    w.obj("pg_dh_walls", m["wall"], g)
    box("pg_dh_roof", (x0 - 4, DH_TOP, DH_Z - 4), (x1 + 4, DH_TOP + 8, -70), m["roof"], g)
    racks, leds, bus, taps = MB(), MB(), MB(), MB()
    centres = []
    for z in ROWS:
        n = int((x1 - x0 - 90) // (RACK_W + 4))
        for i in range(n):
            xa = x0 + 60 + i * (RACK_W + 4)
            racks.box((xa, 4, z - RACK_D / 2), (xa + RACK_W, 4 + RACK_H, z + RACK_D / 2))
            leds.box((xa + 4, 12, z + RACK_D / 2), (xa + 7, 62, z + RACK_D / 2 + 1.2))
            taps.tube((xa + RACK_W / 2, 4 + RACK_H, z), (xa + RACK_W / 2, 100, z), 1.2, 6)
            centres.append((xa + RACK_W / 2, 4 + RACK_H, z))
        bus.box((x0 + 30, 98, z - 4), (x1 - 20, 106, z + 4))
    racks.obj("pg_racks", m["rack"], g)
    leds.obj("pg_rack_leds", m["led"], g)
    bus.obj("pg_busways", m["busway"], g)
    taps.obj("pg_taps", m["busway"], g)
    box("pg_switchboard", (x0 + 10, 4, -80), (x0 + 42, 96, -8), m["cabinet"], g)
    units, fans = MB(), MB()
    unit_tops = []
    for k in range(4):
        xa = x0 + 30 + k * 115
        units.box((xa, DH_TOP + 8, -230), (xa + 90, DH_TOP + 34, -100))
        for zf in (-200.0, -130.0):
            for xf in (xa + 24, xa + 66):
                fans.tube((xf, DH_TOP + 34, zf), (xf, DH_TOP + 37, zf), 17, 16)
                unit_tops.append((xf, DH_TOP + 38, zf))
    units.obj("pg_cool_units", m["unit"], g)
    fans.obj("pg_fans", m["fan"], g, smooth=True)
    # power paths: switchboard up and along each busway
    rows = []
    for z in ROWS:
        rows.append([(x0 + 26, 88, -44.0), (x0 + 30, 102, z), (x1 - 20, 102, z)])
    riser = [(x0 + 26, 88, -44.0), (x0 + 26, 96, -60), (x0 + 16, 140, -150), (x0 + 16, DH_TOP + 12, -170),
             (x0 + 75, DH_TOP + 22, -170), (x1 - 60, DH_TOP + 22, -170)]
    tube("pg_riser", riser[2], riser[3], 2.5, m["cable"], g, 8)
    return {"rows": rows, "riser": riser, "racks": centres, "fans": unit_tops,
            "hall": (x0 + 250, DH_TOP, -150.0), "rack": (x0 + 60 + 6 * 26 + 11, 4 + RACK_H, ROWS[0]),
            "row": (x0 + 220, 50.0, ROWS[0] + RACK_D / 2), "busway": (x0 + 300, 106.0, ROWS[0]),
            "switchboard": (x0 + 26, 96.0, -8.0), "units": (x0 + 260, DH_TOP + 34, -100.0),
            "roof": (x0 + 400, DH_TOP + 8, -80.0)}


def gas_turbine(m, root):
    """A gas turbine package cut open: inlet filter house, compressor (shrinking blade rows),
    combustor (glowing), turbine (growing rows), generator, exhaust stack. Returns points, the flame
    group (shown while it runs) and the cable path to the hall."""
    g = empty("pg_gt", root)
    x0, x1 = GT
    ay = 46.0
    w = MB()
    w.box((x0, 0, -120), (x1, 4, 0))
    w.box((x0, 4, -120), (x1, 96, -114))
    w.box((x0, 4, -120), (x0 + 6, 96, 0))
    w.box((x1 - 6, 4, -120), (x1, 96, 0))
    w.box((x0 - 3, 96, -123), (x1 + 3, 101, -50))
    w.obj("pg_gt_enclosure", m["unit"], g)
    box("pg_gt_filter", (x0 + 6, 101, -110), (x0 + 60, 140, -60), m["cabinet"], g)
    pipe_x("pg_gt_case_c", x0 + 18, x0 + 82, 30, 27, m["stack"], g, ay)
    pipe_x("pg_gt_comb", x0 + 82, x0 + 108, 34, 30, m["stack"], g, ay)
    pipe_x("pg_gt_case_t", x0 + 108, x0 + 140, 32, 29, m["stack"], g, ay)
    bl = MB()
    for k in range(7):
        x = x0 + 24 + k * 8.5
        bl.tube((x - 1.4, ay, 0), (x + 1.4, ay, 0), 25 - 1.4 * k, 24)
    for k in range(3):
        x = x0 + 114 + k * 9
        bl.tube((x - 1.6, ay, 0), (x + 1.6, ay, 0), 20 + 3 * k, 24)
    o = bl.obj("pg_gt_blades", m["blade"], g)
    cut(o, 0.5)
    rod_x("pg_gt_shaft", x0 + 14, x1 - 10, 5, m["rotor"], g, ay)
    flame = empty("pg_gt_flame", g)
    fl = MB()
    for k in range(6):
        t = math.pi + math.pi * (k + 0.5) / 6
        y, z = ay + 18 * math.cos(t), 18 * math.sin(t)
        fl.tube((x0 + 86, y, z), (x0 + 106, y, z), 4.5, 10)
    o = fl.obj("pg_gt_flames", m["flame"], flame)
    cut(o, 0.6)
    pipe_x("pg_gt_gen", x1 - 70, x1 - 14, 30, 22, m["gen"], g, ay)
    rod_x("pg_gt_gen_rotor", x1 - 64, x1 - 20, 18, m["rotor"], g, ay)
    tube("pg_gt_stack", (x0 + 150, 96, -70), (x0 + 150, 230, -70), 18, m["stack"], g, 20)
    tube("pg_gas_pipe", (x0 + 95, 4, -60), (x1 + 160, 4, -60), 4, m["gas_pipe"], g, 10)
    cab = [(x1 - 40, ay + 30, -20.0), (x1 - 40, 90, -20.0), (x1 - 40, 90, -30.0), (x1 - 8, 3, -30.0)]
    cable = [(x1 - 8, 3, -30.0), (DH[1] + 20, 3, -30.0), (DH[1] - 10, 60, -30.0), (DH[1] - 30, 102, ROWS[1])]
    path = cab + cable[1:] + [(DH[0] + 30, 102, ROWS[1])]
    wire("pg_gt_cable", cable[:3], 3.0, m["cable"], g)
    return {"gt": (x0 + 60, ay + 30, 0.0), "comb": (x0 + 95, ay + 18, 0.0), "comp": (x0 + 40, ay + 26, 0.0),
            "turb": (x0 + 124, ay + 26, 0.0), "gen": (x1 - 42, ay + 30, 0.0), "stack": (x0 + 150, 230.0, -70.0),
            "gas": (x1 + 100, 8.0, -60.0), "filter": (x0 + 33, 140.0, -85.0)}, flame, path


def lines(m, root, gsu, ends, towers=TOWERS):
    """The towers and both circuits' conductors, from the GSU's HV bushings, sagging tower to tower,
    to the gantry's strain strings. Returns {(side, phase): path} and per-tower points."""
    clamps, peaks = [], []
    for i, x in enumerate(towers):
        c, p = tower(m, root, x, f"pg_t{i}")
        clamps.append(c)
        peaks.append(p)
    cond, earth = MB(), MB()
    paths = {}
    for s in (1, -1):
        for k, ph in enumerate(("A", "B", "C")):
            pts = curve_pts(gsu["hv"][k], clamps[0][(s, ph)], (0, -10, 0), 6) if gsu else [clamps[0][(s, ph)]]
            for i in range(len(towers) - 1):
                pts += curve_pts(clamps[i][(s, ph)], clamps[i + 1][(s, ph)], (0, -SAG, 0), 10)[1:]
            pts += curve_pts(clamps[-1][(s, ph)], ends[(s, ph)], (0, -SAG * 0.6, 0), 10)[1:]
            wire_into(cond, pts, 1.7, 5)
            paths[(s, ph)] = pts
        for i in range(len(towers) - 1):
            wire_into(earth, curve_pts(peaks[i][s], peaks[i + 1][s], (0, -SAG * 0.8, 0), 8), 0.9, 4, False)
    cond.obj("pg_conductors", m["conductor"], root, smooth=True)
    earth.obj("pg_earth_wires", m["conductor"], root)
    return paths, clamps


def world(m, root, parts=("ground", "plant", "gsu", "lines", "sub", "hall", "gt"), towers=TOWERS):
    """The whole run (or the named parts of it; without the GSU the line starts at the first of
    `towers`). Returns a dict of points and paths."""
    w = {}
    if "ground" in parts:
        ground(m, root)
    if "plant" in parts:
        w["plant"] = plant(m, root)
    if "gsu" in parts:
        box("pg_gsu_gravel", (GSU[0] - 30, 0, -150), (TOWERS[0] + 70, 1.5, 120), m["gravel"], root)
        w["gsu"] = transformer(m, root, GSU[0], GSU[1], GSU_LIMBS, "pg_gsu")
    if "lines" in parts or "sub" in parts:
        w["ends"] = gantry(m, root)
    if "lines" in parts:
        w["lines"], w["clamps"] = lines(m, root, w.get("gsu"), w["ends"], towers)
    if "sub" in parts:
        w["sub"] = substation(m, root, w["ends"])
    if "hall" in parts:
        w["hall"] = hall(m, root)
    if "gt" in parts:
        w["gt"], w["flame"], w["gt_path"] = gas_turbine(m, root)
    return w


def gsu_path(w, k):
    """Generator terminal -> isolated-phase bus -> LV bushing -> through the windings -> HV bushing."""
    g = w["gsu"]
    lim = g["limbs"][k]
    return join_paths(w["plant"]["bus"][k], [g["lv"][k], (lim + 6, g["mid"] + 10, -3.0), (lim, g["mid"] + 30, -3.0),
                                             (lim, 150.0, -40.0), g["hv"][k]])


def full_path(w, s, k, rows=True):
    """One phase all the way: generator, GSU, the line, the gantry drop, the bus, the step-down
    transformer, the LV cable, and along a busway in the hall."""
    ph = "ABC"[k]
    sd = w["sub"]["sd"]
    lim = sd["limbs"][k]
    through = [sd["hv"][k], (lim, sd["mid"] + 20, -3.0), (lim + 8, sd["mid"], -3.0), sd["lv"][k]]
    p = join_paths(gsu_path(w, k), w["lines"][(s, ph)], w["sub"]["drops"][(s, ph)], w["sub"]["buses"][ph], through,
                   w["sub"]["lv"][k])
    if rows:
        p = join_paths(p, w["hall"]["rows"][k])
    return p


def sub_path(w, s, k):
    """From the gantry's strain string down into the step-down transformer and out to the hall."""
    ph = "ABC"[k]
    sd = w["sub"]["sd"]
    lim = sd["limbs"][k]
    through = [sd["hv"][k], (lim, sd["mid"] + 20, -3.0), (lim + 8, sd["mid"], -3.0), sd["lv"][k]]
    return join_paths(w["sub"]["drops"][(s, ph)], w["sub"]["buses"][ph], through, w["sub"]["lv"][k],
                      w["hall"]["rows"][k])


def segment(path, x0, x1):
    """The part of a path whose x lies in [x0, x1] (paths here run left to right)."""
    return [p for p in path if x0 <= p[0] <= x1]


# ---- the interconnection queue ------------------------------------------------------------------

QZ = 260.0  # the queue's road, in front of the substation
GATE_X = 700.0
Q_KINDS = ("solar", "battery", "gas", "wind", "solar", "battery", "wind", "gas", "battery", "solar", "wind")


def project(m, parent, kind, x, z, name):
    """One project waiting to connect, on its grey pallet: a solar array, battery containers, a gas
    plant or a wind turbine."""
    g = empty(name, parent)
    box(f"{name}_pallet", (x - 36, 0, z - 30), (x + 36, 6, z + 30), m["pallet"], g)
    if kind == "solar":
        pv, legs = MB(), MB()
        for r in range(3):
            zc = z - 20 + r * 20
            for c in range(2):
                xa = x - 32 + c * 33
                y0, y1 = 12.0, 24.0
                pv.box((xa, y0, zc - 6), (xa + 31, y0 + 2.5, zc + 2))
                pv.box((xa, y0 + 2.5, zc - 6), (xa + 31, y1 - 6, zc - 4))
                legs.tube((xa + 15, 6, zc), (xa + 15, y0, zc), 1.0, 4)
        pv.obj(f"{name}_pv", m["solar"], g)
        legs.obj(f"{name}_legs", m["lattice"], g)
    elif kind == "battery":
        b = MB()
        for zc in (z - 14, z + 14):
            b.box((x - 32, 6, zc - 11), (x + 32, 34, zc + 11))
        b.obj(f"{name}_boxes", m["battery"], g)
        d = MB()
        for zc in (z - 14, z + 14):
            for xa in (-28, -12, 4, 20):
                d.box((x + xa, 10, zc + 11), (x + xa + 10, 30, zc + 12.5))
        d.obj(f"{name}_doors", m["cabinet"], g)
    elif kind == "gas":
        box(f"{name}_house", (x - 30, 6, z - 22), (x + 18, 40, z + 22), m["unit"], g)
        tube(f"{name}_stack", (x + 26, 6, z - 6), (x + 26, 76, z - 6), 6, m["stack"], g, 12)
    else:
        tube(f"{name}_mast", (x, 6, z), (x, 120, z), 3.2, m["white"], g, 12)
        box(f"{name}_nacelle", (x - 6, 116, z - 4), (x + 12, 126, z + 4), m["white"], g)
        hub = (x - 8, 121, z + 2)
        bl = MB()
        for k in range(3):
            t = math.pi / 2 + 2 * math.pi * k / 3
            bl.tube(hub, (hub[0], hub[1] + 44 * math.sin(t), hub[2] + 44 * math.cos(t)), 1.6, 5)
        bl.ball(hub, 3.0, 8)
        bl.obj(f"{name}_blades", m["white"], g)
    return g


def queue(m, root, n=11, spacing=88.0):
    """The road to the substation's gate and the projects lined up on it, front of the line first.
    Returns the groups (front first) and the front slot."""
    box("pg_q_road", (GATE_X - spacing * n - 40, 0, QZ - 42), (GATE_X + 40, 1.2, QZ + 42), m["road"], root)
    box("pg_q_spur", (GATE_X - 40, 0, 150), (GATE_X + 40, 1.2, QZ - 42), m["road"], root)
    gate = MB()
    gate.tube((GATE_X - 44, 0, 155), (GATE_X - 44, 60, 155), 3, 8)
    gate.tube((GATE_X + 44, 0, 155), (GATE_X + 44, 60, 155), 3, 8)
    gate.tube((GATE_X - 44, 60, 155), (GATE_X + 44, 60, 155), 2.2, 8)
    gate.obj("pg_q_gate", m["lattice"], root, smooth=True)
    gs = []
    for i in range(n):
        x = GATE_X - spacing * (i + 1) + 40
        gs.append(project(m, root, Q_KINDS[i % len(Q_KINDS)], x, QZ, f"pg_q{i}"))
    return gs, (GATE_X - spacing + 40, 0.0, QZ)


def scan_ring(m, parent, c, r=50.0, name="pg_scan"):
    """A glowing ring round a project being studied."""
    g = empty(name, parent)
    mb = MB()
    n = 32
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        mb.tube((c[0] + r * math.cos(a0), c[1], c[2] + r * math.sin(a0)),
                (c[0] + r * math.cos(a1), c[1], c[2] + r * math.sin(a1)), 1.6, 6)
    mb.obj(f"{name}_ring", m["scan"], g, smooth=True)
    return g


def months(m, parent, x0, y, z, n=55, size=10.0, gap=3.0, per_row=11, name="pg_month", step=3):
    """`n` tiles (one per month) in rows; returns lit overlays to show in turn, each lighting the
    next `step` tiles (fewer animated objects than one per tile)."""
    dim = MB()
    lit = []
    for k in range(n):
        r, c = divmod(k, per_row)
        xa = x0 + c * (size + gap)
        ya = y - r * (size + gap)
        dim.box((xa, ya, z), (xa + size, ya + size, z + 2))
        if k % step == 0:
            g = empty(f"{name}{k}", parent)
            mb = MB()
            for j in range(k, min(n, k + step)):
                rr, cc = divmod(j, per_row)
                xb, yb = x0 + cc * (size + gap), y - rr * (size + gap)
                mb.box((xb, yb, z + 2), (xb + size, yb + size, z + 4))
            mb.obj(f"{name}{k}_lit", m["tile_lit"], g)
            lit.append(g)
    dim.obj(f"{name}_dim", m["tile"], parent)
    return lit


# ---- other parts -----------------------------------------------------------------------------


def cooling_tower(m, parent, c, h=360.0, r0=130.0, rw=80.0, rt=92.0, name="pg_ct"):
    prof = []
    for k in range(13):
        u = k / 12
        yw = 0.72
        r = r0 + (rw - r0) * (u / yw) ** 0.8 if u <= yw else rw + (rt - rw) * ((u - yw) / (1 - yw)) ** 1.5
        prof.append((r, h * u))
    o = lathe(name, prof, m["concrete"], parent, c)
    legs = MB()
    for k in range(16):
        t = 2 * math.pi * k / 16
        legs.tube((c[0] + r0 * math.cos(t), c[1] - 20, c[2] + r0 * math.sin(t)),
                  (c[0] + r0 * math.cos(t + 0.2), c[1] + 2, c[2] + r0 * math.sin(t + 0.2)), 3.0, 5)
    legs.obj(f"{name}_legs", m["concrete"], parent)
    return o


def house(mb_wall, mb_roof, x, z, w=50.0, d=40.0, h=32.0):
    mb_wall.box((x - w / 2, 0, z - d / 2), (x + w / 2, h, z + d / 2))
    mb_roof.prism(x - w / 2 - 3, x + w / 2 + 3, ((z - d / 2 - 4, h), (z + d / 2 + 4, h)), (z, h + 20))


def crane(m, parent, x, z, h=480.0, jib=220.0, name="pg_crane"):
    """A tower crane: a lattice mast, a jib and counter-jib, a hook line."""
    mb = MB()
    a = 8.0
    levels = [i * 40.0 for i in range(int(h / 40) + 1)]
    for i in range(len(levels) - 1):
        for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            mb.tube((x + sx * a, levels[i], z + sz * a), (x + sx * a, levels[i + 1], z + sz * a), 1.6, 5)
        mb.tube((x - a, levels[i], z + a), (x + a, levels[i + 1], z + a), 0.8, 4)
        mb.tube((x - a, levels[i], z - a), (x + a, levels[i + 1], z - a), 0.8, 4)
    top = levels[-1]
    for zz in (-a, a):
        mb.tube((x - 80, top, z + zz), (x + jib, top, z + zz), 1.6, 5)
        mb.tube((x - 80, top + 14, z + zz * 0.3), (x + jib, top + 4, z + zz * 0.3), 1.2, 5)
    mb.tube((x, top, z), (x, top + 40, z), 2.0, 5)
    mb.box((x - 80, top - 18, z - 9), (x - 55, top, z + 9))
    mb.obj(name, m["crane"], parent)
    tube(f"{name}_hook", (x + jib * 0.7, top, z), (x + jib * 0.7, top - 160, z), 0.8, m["cable"], parent, 6)
    return (x + jib * 0.7, top - 160, z)


# ---- camera -----------------------------------------------------------------------------------

PANE = 0.53
GLIDE = 0.16


def frame(c, size, yaw=0.35, pitch=0.22, pad=1.12, min_d=90.0):
    """A pose that fits a subject `size` across, centred on c, in the left pane."""
    return (tuple(c), max(size / PANE * pad, min_d), yaw, pitch)


def _eye(t, d, yaw, pitch):
    cp, sp = math.cos(pitch), math.sin(pitch)
    return (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))


def camera_path(root, plan):
    """`plan`: one pose per beat (fiber_laser_detail.camera_path): reached by GLIDE into the beat
    (gliding from the last one), then held with a slow push-in."""
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


def _land_last_keys(step):
    """The exporter samples each action from its first to its last key in `step`s, so a last key
    off the step grid is dropped (a bar left half-grown, a bead left showing). Repeat each
    channel's last key on the next frame of the grid."""
    from bpy_extras import anim_utils

    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in cb.fcurves:
            if not len(fc.keyframe_points):
                continue
            last = fc.keyframe_points[-1]
            f = int(round(last.co[0]))
            if f % step:
                kp = fc.keyframe_points.insert(f + step - f % step, last.co[1])
                kp.interpolation = "CONSTANT"


def finish(name, page="power_grid", step=2):
    """Saves blender/<page>_<name>.blend and exports assets/<page>_<name>.glb, as sand_zooms.finish
    but sampling every `step` frames (12 a second; pbr3d interpolates between them), which halves
    the animation data of a scene with hundreds of beads."""
    _land_last_keys(step)
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, "..", "assets"))
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, f"{page}_{name}.blend"))
    glb = os.path.join(out, f"{page}_{name}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb,
        export_format="GLB",
        export_yup=True,
        export_animations=True,
        export_force_sampling=True,
        export_frame_step=step,
        export_cameras=False,
        export_lights=False,
        use_selection=False,
    )
    print("exported", glb)
