"""Part builders, flows and camera for the RACK POWER page (power_rack_{overview,zooms,sections}.py).

Units mm, Y up, true scale (a rack is ~1.9 m here, so even a PSU's parts stay far outside pbr3d's
40-unit near plane). Each "area" is one subject built at its own origin, far apart so cameras on one
never see another:

  Rack     an NVL72-class rack cut lengthwise down its middle (camera on +z looks at the cut). Depth
           runs along x (front at -x, rear at +x). Bottom to top: four power shelves, a battery backup
           shelf, eight compute trays, nine NVLink switch trays, ten compute trays, four power shelves,
           two network switches. Each power shelf shows one PSU cut open (fan, bulk capacitors,
           transformer, heat sinks, output bus). Down the rear: the +50 V and return copper busbars
           with every tray's and shelf's clip gripping them, a rack PDU with its breakers and outlets,
           AC whips from the PDU into each shelf, and an overhead busway with its tap-off box.
  Shelf    one power shelf, lid off, seen from above: six PSU modules side by side (one with its own
           cover off showing EMI filter, PFC inductor, bulk capacitors, MOSFETs on heat sinks, the
           transformer, output capacitors and fan), the backplane with three AC inlets and the DC
           output bus that runs to two clips on a stub of the rack busbar.
  closed   whole racks seen from the front (NVL72-class, a cloud server rack, a 1 MW-class rack,
           an 800 V sidecar), for rows and comparisons.

Flows are glowing beads riding the real conductors: amber = AC, pink = ~400 V DC inside a PSU,
blue = ~50 V DC, violet = 800 V DC. Straight runs use `conveyor` (all beads of one direction in a
group that slides one bead spacing per period: one animated node for many beads); arched cables use
`loop_run` (a few beads that ride the arc again and again), after fiber_photodiode_detail.wire/run.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, ball, box, cut, empty, key, show, tube, label, beat, _smooth  # noqa: E402

PAGE = "power_rack"
BEATS = 3

# ---- materials ------------------------------------------------------------------------------------


def materials():
    m = {}

    def M_(k, *a, **kw):
        m[k] = O.mat("pr_" + k, *a, **kw)

    M_("frame", (0.10, 0.11, 0.13), metal=0.6, rough=0.45)
    M_("panel", (0.20, 0.21, 0.24), metal=0.3, rough=0.7)
    M_("chassis", (0.46, 0.48, 0.52), metal=0.7, rough=0.4)
    M_("shelf", (0.66, 0.68, 0.71), metal=0.6, rough=0.35)
    M_("psu", (0.74, 0.76, 0.79), metal=0.6, rough=0.35)
    M_("compute", (0.45, 0.28, 0.66), rough=0.5)
    M_("switch", (0.14, 0.55, 0.55), rough=0.5)
    M_("net", (0.22, 0.23, 0.26), rough=0.5)
    M_("copper", (0.88, 0.50, 0.28), metal=0.9, rough=0.28)
    M_("tin", (0.82, 0.83, 0.86), metal=0.9, rough=0.25)
    M_("insul", (0.88, 0.82, 0.62), rough=0.6)
    M_("pcb", (0.08, 0.34, 0.18), rough=0.7)
    M_("ic", (0.07, 0.07, 0.08), rough=0.5)
    M_("cold", (0.72, 0.74, 0.78), metal=0.8, rough=0.3)
    M_("pipe_b", (0.15, 0.35, 0.85), rough=0.4)
    M_("pipe_r", (0.80, 0.20, 0.16), rough=0.4)
    M_("cable", (0.06, 0.06, 0.07), rough=0.7)
    M_("plug", (0.13, 0.13, 0.14), rough=0.6)
    M_("cap", (0.12, 0.22, 0.52), rough=0.4)
    M_("cap_top", (0.78, 0.79, 0.81), metal=0.8, rough=0.3)
    M_("xcap", (0.85, 0.70, 0.20), rough=0.5)
    M_("ferrite", (0.22, 0.22, 0.24), rough=0.6)
    M_("heatsink", (0.80, 0.82, 0.85), metal=0.8, rough=0.3)
    M_("fan", (0.10, 0.10, 0.11), rough=0.6)
    M_("breaker", (0.90, 0.90, 0.88), rough=0.5)
    M_("handle", (0.85, 0.16, 0.12), rough=0.5)
    M_("pdu", (0.13, 0.13, 0.15), metal=0.4, rough=0.5)
    M_("busway", (0.58, 0.60, 0.63), metal=0.7, rough=0.35)
    M_("cell", (0.20, 0.50, 0.34), rough=0.5)
    M_("floor", (0.23, 0.24, 0.26), rough=0.85)
    M_("sidecar", (0.28, 0.24, 0.36), metal=0.5, rough=0.45)
    M_("server", (0.36, 0.38, 0.42), metal=0.5, rough=0.45)
    M_("hv_cable", (0.90, 0.48, 0.12), rough=0.5)
    M_("cabinet", (0.70, 0.72, 0.70), metal=0.4, rough=0.5)
    M_("concrete", (0.48, 0.47, 0.45), rough=0.9)
    # glowing things
    M_("ac", (1.0, 0.62, 0.12), emit=(1.0, 0.58, 0.10), strength=5.0)
    M_("bulk", (1.0, 0.36, 0.58), emit=(1.0, 0.30, 0.55), strength=5.0)
    M_("dc", (0.25, 0.72, 1.0), emit=(0.20, 0.68, 1.0), strength=6.0)
    M_("hv", (0.82, 0.38, 1.0), emit=(0.78, 0.32, 1.0), strength=6.0)
    M_("hot", (1.0, 0.36, 0.08), emit=(1.0, 0.30, 0.05), strength=3.0)
    M_("warm", (0.95, 0.42, 0.16), emit=(1.0, 0.36, 0.08), strength=0.7)
    M_("mark", (1.0, 0.82, 0.30), emit=(1.0, 0.78, 0.25), strength=3.0)
    M_("fail", (1.0, 0.12, 0.08), emit=(1.0, 0.08, 0.05), strength=3.0)
    M_("led", (0.30, 1.0, 0.45), emit=(0.25, 1.0, 0.40), strength=4.0)
    M_("arc", (0.85, 0.90, 1.0), emit=(0.8, 0.88, 1.0), strength=12.0)
    M_("col_lo", (0.35, 0.62, 0.95), emit=(0.30, 0.58, 0.95), strength=1.2)
    M_("col_mid", (1.0, 0.62, 0.15), emit=(1.0, 0.58, 0.12), strength=1.2)
    M_("col_hi", (1.0, 0.25, 0.20), emit=(1.0, 0.22, 0.18), strength=1.2)
    return m


def setup(name, beats=BEATS):
    from sand_zooms import start
    _, root = start(name, beats=beats, page=PAGE)
    return materials(), root


def done(name):
    from sand_zooms import finish
    finish(name, page=PAGE)


# ---- small shapes ---------------------------------------------------------------------------------


def add(o, p):
    return (o[0] + p[0], o[1] + p[1], o[2] + p[2])


def _link(name, me, mt, parent):
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mt)
    o.parent = parent
    _smooth(o)
    return o


def pipe_y(name, c, y0, y1, ro, ri, mt, parent=None, half=False, verts=32):
    """A ring standing on y (axis through c's x and z), from y0 to y1. `half` keeps z <= c.z."""
    cx, cz = c[0], c[2]
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
    return _link(name, me, mt, parent)


def pipe_z(name, c, z0, z1, ro, ri, mt, parent=None, verts=32):
    """A ring whose axis runs along z through c's x and y, from z0 to z1 (a fan shroud)."""
    cx, cy = c[0], c[1]
    angles = [2 * math.pi * i / verts for i in range(verts)]
    rings = [(z0, ro), (z1, ro), (z1, ri), (z0, ri)]
    vs = [tuple(P(cx + r * math.cos(t), cy + r * math.sin(t), z)) for z, r in rings for t in angles]
    k = len(angles)
    faces = []
    for a in range(4):
        b = (a + 1) % 4
        for i in range(k):
            j = (i + 1) % k
            faces.append((a * k + i, a * k + j, b * k + j, b * k + i))
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return _link(name, me, mt, parent)


def rod(name, a, b, r, mt, parent=None, half=False, verts=24, front=0.0):
    o = tube(name, a, b, r, mt, parent, verts)
    return cut(o, front) if half else o


def join(objs, name):
    """Merge meshes (same parent) into one object, keeping each material."""
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
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


class Kit:
    """Collects static boxes/rods under one parent and merges them by material on `seal()`."""

    def __init__(self, name, parent, o=(0.0, 0.0, 0.0)):
        self.name, self.g, self.o, self.objs, self.n = name, empty(name, parent), o, [], 0

    def _nm(self, n):
        self.n += 1
        return f"{self.name}_{n}_{self.n}"

    def B(self, n, lo, hi, mt):
        o = box(self._nm(n), add(self.o, lo), add(self.o, hi), mt, self.g)
        self.objs.append(o)
        return o

    def T(self, n, a, b, r, mt, verts=16, half=False):
        o = rod(self._nm(n), add(self.o, a), add(self.o, b), r, mt, self.g, half, verts)
        self.objs.append(o)
        return o

    def Y(self, n, c, y0, y1, ro, ri, mt, half=False, verts=24):
        cc = add(self.o, c)
        o = pipe_y(self._nm(n), cc, cc[1] - c[1] + y0, cc[1] - c[1] + y1, ro, ri, mt, self.g, half, verts)
        self.objs.append(o)
        return o

    def keep(self, o):
        self.objs.append(o)
        return o

    def seal(self):
        by = {}
        for o in self.objs:
            by.setdefault(o.data.materials[0].name if o.data.materials else "", []).append(o)
        for k, objs in by.items():
            join(objs, f"{self.name}_{k}")
        self.objs = []
        return self.g


# ---- cables, beads, highlights --------------------------------------------------------------------


_BEAD = {}


def bead(name, c, r, mt, parent=None):
    """A light, smooth-shaded sphere (8 x 5) for beads: far fewer vertices than `ball`."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=r)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = P(*c)
    o.data.materials.append(mt)
    o.parent = parent
    return o


def curve_pts(a, b, lift, n=10):
    """Points on an arc from a to b, bowed by the vector `lift` at the middle."""
    out = []
    for k in range(n + 1):
        u = k / n
        w = 4 * u * (1 - u)
        out.append(tuple(a[i] + (b[i] - a[i]) * u + lift[i] * w for i in range(3)))
    return out


def wire(name, pts, r, mt, parent, verts=10):
    """A cable through `pts`: a tube per segment, a ball at each joint so it reads as one piece."""
    g = empty(name, parent)
    objs = []
    for k in range(len(pts) - 1):
        objs.append(tube(f"{name}_{k}", pts[k], pts[k + 1], r, mt, g, verts))
        if k:
            objs.append(bead(f"{name}_j{k}", pts[k], r, mt, g))
    join(objs, f"{name}_mesh")
    return g


def _cum(pts):
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + math.dist(pts[i - 1], pts[i]))
    return c


def loop_run(parent, name, pts, n, size, mt, iv, period=48):
    """`n` beads riding the polyline `pts` over and over (one trip per `period` frames, evenly
    phased), visible during the intervals `iv`."""
    g = empty(name, parent)
    show(g, iv)
    f_lo, f_hi = min(a for a, _ in iv), max(b for _, b in iv)
    cum = _cum(pts)
    tot = cum[-1] or 1.0
    for k in range(n):
        e = empty(f"{name}{k}", g)
        bead(f"{name}{k}_b", pts[0], size, mt, e)
        ph = int(period * k / n)
        c = f_lo - ph
        while c < f_hi:
            for j, p in enumerate(pts):
                f = c + round((period - 1) * cum[j] / tot)
                if f < f_lo - period or f > f_hi + 1:
                    continue
                key(e, max(f, 0), "location", P(p[0] - pts[0][0], p[1] - pts[0][1], p[2] - pts[0][2]), linear=True)
            c += period
    return g


def conveyor(parent, name, segs, spacing, size, mt, iv, period=24, sign=1.0):
    """Beads every `spacing` along each segment (a, b) in `segs` (all pointing the same way). The
    whole group slides one spacing along a->b every `period` frames, so the beads stream.
    Visible during `iv`."""
    g = empty(name, parent)
    show(g, iv)
    mv = empty(f"{name}_mv", g)
    d = None
    objs = []
    for i, (a, b) in enumerate(segs):
        L = math.dist(a, b)
        if L < 1e-6:
            continue
        u = tuple((b[j] - a[j]) / L for j in range(3))
        d = d or u
        k = 0
        while k * spacing <= L - spacing * 0.6:
            p = tuple(a[j] + u[j] * spacing * k for j in range(3))
            objs.append(bead(f"{name}_{i}_{k}", p, size, mt, mv))
            k += 1
    join(objs, f"{name}_beads")
    f_lo, f_hi = min(a for a, _ in iv), max(b for _, b in iv)
    c = f_lo
    while c < f_hi:
        key(mv, c, "location", P(0, 0, 0), linear=True)
        s = spacing * (period - 1) / period
        key(mv, c + period - 1, "location", P(d[0] * s, d[1] * s, d[2] * s), linear=True)
        c += period
    return g


def bracket(name, lo, hi, mt, parent, r=3.0, plane="z"):
    """A glowing rectangle round lo..hi, drawn in the plane z = hi.z (or y = hi.y for `plane` 'y')."""
    g = empty(name, parent)
    objs = []
    if plane == "z":
        z = hi[2]
        cs = [(lo[0], lo[1], z), (hi[0], lo[1], z), (hi[0], hi[1], z), (lo[0], hi[1], z)]
    else:
        y = hi[1]
        cs = [(lo[0], y, lo[2]), (hi[0], y, lo[2]), (hi[0], y, hi[2]), (lo[0], y, hi[2])]
    for i in range(4):
        objs.append(tube(f"{name}_{i}", cs[i], cs[(i + 1) % 4], r, mt, g, 8))
        objs.append(bead(f"{name}_c{i}", cs[i], r, mt, g))
    join(objs, f"{name}_m")
    return g


def spin(obj, axis, f0, f1, turns):
    """Spin `obj` about its own Blender axis (0 x, 1 y, 2 z) linearly from f0 to f1."""
    r = [0.0, 0.0, 0.0]
    key(obj, f0, "rotation_euler", tuple(r), linear=True)
    r[axis] = 2 * math.pi * turns
    key(obj, f1, "rotation_euler", tuple(r), linear=True)


def fan(m, parent, c, r, axis, name, f0, f1, turns=40.0, depth=12.0):
    """A fan: dark shroud ring, hub and five blades, spinning from f0 to f1. `axis` 'x' or 'z'."""
    piv = empty(name, parent, P(*c))
    blades = []
    hub_a = (-depth / 2, 0, 0) if axis == "x" else (0, 0, -depth / 2)
    hub_b = (depth / 2, 0, 0) if axis == "x" else (0, 0, depth / 2)
    blades.append(tube(f"{name}_hub", hub_a, hub_b, r * 0.32, m["fan"], piv, 12))
    from mathutils import Matrix
    for k in range(5):
        t = 2 * math.pi * k / 5
        if axis == "x":
            o = box(f"{name}_bl{k}", (-1.5, r * 0.3, -r * 0.16), (1.5, r * 0.92, r * 0.16), m["fan"], piv)
            o.matrix_basis = Matrix.Rotation(t, 4, "X") @ o.matrix_basis
        else:
            o = box(f"{name}_bl{k}", (-r * 0.16, r * 0.3, -1.5), (r * 0.16, r * 0.92, 1.5), m["fan"], piv)
            o.matrix_basis = Matrix.Rotation(t, 4, "Y") @ o.matrix_basis
        blades.append(o)
    join(blades, f"{name}_rotor")
    spin(piv, 0 if axis == "x" else 1, f0, f1, turns if axis == "x" else -turns)
    return piv


# ---- the rack, cut lengthwise ---------------------------------------------------------------------

U = 44.45
RX0, RX1 = -600.0, 640.0          # rack front, rear
RZ = 300.0                        # half width (the cut keeps z <= 0)
Y0 = 70.0                         # first slot's floor
TX0, TX1 = -570.0, 470.0          # trays and shelves: front, rear wall
PSU_X1 = 30.0                     # PSU modules run TX0..PSU_X1; the shelf backplane behind
BP = (492.0, 508.0)               # +50 V busbar (x)
BN = (532.0, 548.0)               # return busbar
BZ = -60.0                        # busbars run from z = BZ to the cut face
PDU_X, PDU_Z = (652.0, 680.0), (-150.0, -108.0)
INLET_X, INLET_Z = (470.0, 490.0), (-250.0, -196.0)
LAYOUT = ["shelf"] * 4 + ["bbu"] + ["compute"] * 8 + ["switch"] * 9 + ["compute"] * 10 + ["shelf"] * 4 + ["net"] * 2
RY1 = Y0 + len(LAYOUT) * U + 40.0  # roof
BUSWAY_Y = RY1 + 230.0
CZ = 4.0                          # beads ride this far in front of the cut faces


def slot_y(i):
    return Y0 + i * U


SHELVES = [i for i, k in enumerate(LAYOUT) if k == "shelf"]
TRAYS = [i for i, k in enumerate(LAYOUT) if k in ("compute", "switch")]
BAR_Y0, BAR_Y1 = slot_y(0) + 6.0, slot_y(SHELVES[-1] + 1) - 6.0
MID_Y = (slot_y(SHELVES[3] + 1) + slot_y(SHELVES[4])) / 2


class Rack:
    """The NVL72-class rack cut lengthwise at z = 0, origin `o` (the floor below the front post).
    Methods add flows and overlays; every interval list is [(f0, f1), ...]."""

    def __init__(self, m, root, o=(0.0, 0.0, 0.0), name="rk", f_spin=(0, 1)):
        self.m, self.root, self.o, self.name = m, root, o, name
        k = Kit(name, root, o)
        self.k = k
        B = k.B
        B("plinth", (RX0, 0, -RZ), (RX1, Y0 - 6, 0), m["frame"])
        B("roof", (RX0, RY1, -RZ), (560.0, RY1 + 30, 0), m["frame"])
        B("side", (RX0, 0, -RZ - 12), (RX1, RY1 + 30, -RZ), m["panel"])
        B("post_f", (RX0, Y0 - 6, -RZ), (RX0 + 24, RY1, -RZ + 40), m["frame"])
        B("post_r", (RX1 - 14, Y0 - 6, -RZ), (RX1, RY1, -RZ + 40), m["frame"])
        B("rail_f", (RX0 + 24, Y0 - 6, -RZ), (RX0 + 30, RY1, -RZ + 60), m["frame"])
        self.f_spin = f_spin
        self.fans = []
        for i, kind in enumerate(LAYOUT):
            y = slot_y(i)
            if kind == "shelf":
                self._shelf(y)
            elif kind == "bbu":
                self._bbu(y)
            elif kind in ("compute", "switch"):
                self._tray(y, kind)
            else:
                self._net(y)
        # busbars, insulated standoffs to the rear post
        B("bar_p", (BP[0], BAR_Y0, BZ), (BP[1], BAR_Y1, 0), m["copper"])
        B("bar_n", (BN[0], BAR_Y0, BZ), (BN[1], BAR_Y1, 0), m["copper"])
        B("bar_rail", (RX1 - 30, BAR_Y0, -60), (RX1 - 14, BAR_Y1, -30), m["frame"])
        y = BAR_Y0 + 120
        while y < BAR_Y1 - 60:
            B("stand_a", (BP[1], y - 10, -54), (BN[0], y + 10, -36), m["insul"])
            B("stand_b", (BN[1], y - 10, -54), (RX1 - 30, y + 10, -36), m["insul"])
            y += 330
        # rack PDU down the rear: body, an outlet per shelf, breakers at the top
        B("pdu", (PDU_X[0], Y0, PDU_Z[0]), (PDU_X[1], RY1 - 10, PDU_Z[1]), m["pdu"])
        self.outlets = {}
        for i in SHELVES:
            yc = slot_y(i) + U / 2
            B("outlet", (PDU_X[0] - 6, yc - 14, PDU_Z[0] + 6), (PDU_X[0], yc + 14, PDU_Z[1] - 6), m["plug"])
            self.outlets[i] = (PDU_X[0] - 6, yc, (PDU_Z[0] + PDU_Z[1]) / 2)
        self.breaker_y = []
        for j in range(4):
            yb = slot_y(SHELVES[3] + 2) + j * 120.0
            B("brk", (PDU_X[0] - 8, yb, PDU_Z[0] + 4), (PDU_X[0], yb + 70, PDU_Z[1] - 4), m["breaker"])
            B("brk_h", (PDU_X[0] - 16, yb + 26, -134), (PDU_X[0] - 8, yb + 44, -124), m["handle"])
            self.breaker_y.append(yb + 35)
        # overhead busway (runs across the row, along z) and its tap-off box
        B("busway", (380.0, BUSWAY_Y, -1600), (600.0, BUSWAY_Y + 90, 0), m["busway"])
        B("busway_rib", (370.0, BUSWAY_Y + 30, -1600), (610.0, BUSWAY_Y + 60, -4), m["busway"])
        B("tap", (430.0, BUSWAY_Y - 150, -300), (560.0, BUSWAY_Y, -190), m["cabinet"])
        B("tap_brk", (500.0, BUSWAY_Y - 120, -190), (540.0, BUSWAY_Y - 50, -182), m["breaker"])
        B("tap_h", (510.0, BUSWAY_Y - 96, -182), (530.0, BUSWAY_Y - 78, -176), m["handle"])
        k.seal()
        # cables: tap box down to the PDU; whips from the PDU's outlets to each shelf's AC inlet
        ox = lambda p: add(o, p)  # noqa: E731
        self.feed_pts = [ox(p) for p in curve_pts((495.0, BUSWAY_Y - 150, -245.0), (666.0, RY1 - 10, -129.0), (60.0, -30.0, 0.0), 8)]
        wire(f"{name}_feed", self.feed_pts, 11.0, m["cable"], root)
        self.whips = {}
        for i in SHELVES:
            a = self.outlets[i]
            yc = slot_y(i) + U / 2
            b = (INLET_X[1], yc, (INLET_Z[0] + INLET_Z[1]) / 2)
            lift = (-20.0, 34.0 if i in SHELVES[4:] else -34.0, 40.0)
            pts = [ox(p) for p in curve_pts(a, b, lift, 8)]
            wire(f"{name}_whip{i}", pts, 7.0, m["cable"], root)
            self.whips[i] = pts

    # -- the slots ---------------------------------------------------------------------------------

    def _clip(self, yc, cable_side=False):
        """A tray's or shelf's clips: a stub from its rear wall and jaws either side of each bar."""
        B, m = self.k.B, self.m
        B("stub_p", (TX1, yc - 6, -46), (BP[0] - 4, yc + 6, -14), m["copper"])
        B("jaw_pf", (BP[0] - 8, yc - 9, -56), (BP[0], yc + 9, -4), m["tin"])
        B("jaw_pb", (BP[1], yc - 9, -56), (BP[1] + 6, yc + 9, -4), m["tin"])
        B("stub_n", (TX1, yc - 5, -86), (BN[0] - 6, yc + 5, -68), m["copper"])
        B("jaw_nf", (BN[0] - 8, yc - 9, -64), (BN[0], yc + 9, -4), m["tin"])
        B("jaw_nb", (BN[1], yc - 9, -56), (BN[1] + 6, yc + 9, -4), m["tin"])
        B("jaw_nr", (BN[1], yc - 9, -86), (BN[1] + 6, yc + 9, -56), m["tin"])

    def _box_shell(self, y, front_mt, bezel=22.0):
        B, m = self.k.B, self.m
        B("floor", (TX0, y + 1.5, -RZ + 30), (TX1, y + 3.5, 0), m["chassis"])
        B("cover", (TX0, y + U - 3.5, -RZ + 30), (TX1, y + U - 1.5, -150), m["chassis"])
        B("bezel", (TX0 - bezel, y + 1.5, -RZ + 30), (TX0, y + U - 1.5, 0), front_mt)
        B("rear", (TX1 - 3, y + 3.5, -RZ + 30), (TX1, y + U - 3.5, 0), m["chassis"])

    def _tray(self, y, kind):
        B, T, m = self.k.B, self.k.T, self.m
        self._box_shell(y, m[kind])
        B("board", (TX0 + 30, y + 3.5, -RZ + 40), (TX1 - 40, y + 6.5, 0), m["pcb"])
        chips = [(-480.0, -330.0), (-290.0, -140.0), (-80.0, 60.0)] if kind == "compute" else [(-420.0, -270.0), (-200.0, -50.0)]
        for x0, x1 in chips:
            B("pkg", (x0, y + 6.5, -200), (x1, y + 10, 0), m["ic"])
            B("plate", (x0 + 8, y + 10, -190), (x1 - 8, y + 24, 0), m["cold"])
        T("pipe_s", (-470.0, y + 31, -40), (380.0, y + 31, -40), 4.0, m["pipe_b"], 8)
        T("pipe_r", (-470.0, y + 31, -120), (380.0, y + 31, -120), 4.0, m["pipe_r"], 8)
        B("pwr_board", (300.0, y + 6.5, -220), (TX1 - 6, y + 9, 0), m["pcb"])
        B("brick", (340.0, y + 9, -140), (420.0, y + 27, 0), m["ic"])
        B("brick_pins", (420.0, y + 10, -60), (430.0, y + 14, -10), m["copper"])
        self._clip(y + U / 2)

    def _shelf(self, y):
        """A power shelf: one PSU module cut open lengthwise (fan at the front, then the output
        capacitors, transformer, MOSFET heat sink, bulk capacitors, PFC inductor, EMI filter, rear
        connector), then the shelf backplane, the AC inlet and the output bus to the clips."""
        B, T, Y, m = self.k.B, self.k.T, self.k.Y, self.m
        self._box_shell(y, m["shelf"], bezel=16.0)
        B("psu_floor", (TX0, y + 3.5, -110), (PSU_X1, y + 5.5, 0), m["pcb"])
        B("psu_wall", (TX0, y + 3.5, -112), (PSU_X1, y + U - 3.5, -108), m["psu"])
        B("grille", (TX0 - 16, y + 4, -100), (TX0 - 10, y + U - 4, 0), m["fan"])
        self.fans.append((TX0 + 14, y + U / 2, -50.0))
        for x in (-500.0, -470.0, -440.0):
            T("ocap", (x, y + 5.5, -30), (x, y + 22, -30), 7.0, m["cap"], 12, half=True)
        B("xfmr_core", (-400.0, y + 5.5, -80), (-330.0, y + 36, 0), m["ferrite"])
        B("xfmr_wind", (-392.0, y + 12, -86), (-338.0, y + 30, 2), m["copper"])
        for j in range(5):
            x = -290.0 + j * 12
            B("fin", (x, y + 8, -90), (x + 4, y + 38, 0), m["heatsink"])
        B("fets", (-296.0, y + 5.5, -60), (-226.0, y + 9, 0), m["ic"])
        for x in (-190.0, -150.0):
            T("bulk", (x, y + 5.5, -40), (x, y + 38, -40), 16.0, m["cap"], 20, half=True)
            T("bulk_t", (x, y + 38, -40), (x, y + 39.5, -40), 16.0, m["cap_top"], 20, half=True)
        Y("pfc_l", (-90.0, 0, -40.0), y + 5.5, y + 26, 22.0, 9.0, m["copper"], half=True)
        for j in range(4):
            x = -52.0 + j * 12
            B("fin2", (x, y + 8, -90), (x + 4, y + 36, 0), m["heatsink"])
        Y("emi_l", (8.0, 0, -40.0), y + 5.5, y + 22, 11.0, 4.0, m["ferrite"], half=True)
        B("psu_conn", (PSU_X1 - 6, y + 6, -100), (PSU_X1 + 6, y + U - 6, 0), m["plug"])
        B("out_strip", (-470.0, y + 33, -60), (PSU_X1 - 6, y + 36, 0), m["copper"])
        B("backplane", (PSU_X1 + 6, y + 3.5, -RZ + 40), (TX1 - 6, y + 6.5, 0), m["pcb"])
        B("out_bus", (PSU_X1 + 6, y + 26, -40), (TX1, y + 32, 0), m["copper"])
        B("ac_trace", (PSU_X1 + 6, y + 6.5, -40), (TX1 - 6, y + 9, 0), m["copper"])
        B("inlet", (INLET_X[0], y + 7, INLET_Z[0]), (INLET_X[1], y + U - 7, INLET_Z[1]), m["plug"])
        B("led", (TX0 - 18, y + U - 12, -20), (TX0 - 16, y + U - 7, -10), m["led"])
        self._clip(y + 29)

    def _bbu(self, y):
        B, T, m = self.k.B, self.k.T, self.m
        self._box_shell(y, m["net"], bezel=16.0)
        B("bms", (TX0 + 10, y + 3.5, -RZ + 40), (TX1 - 20, y + 6, 0), m["pcb"])
        x = TX0 + 30
        while x < 360:
            T("cell", (x, y + 6, -30), (x, y + 38, -30), 9.0, m["cell"], 12, half=True)
            x += 24.0
        B("bbu_conv", (380.0, y + 6, -120), (450.0, y + 30, 0), m["ic"])
        self._clip(y + U / 2)

    def _net(self, y):
        m = self.m
        self._box_shell(y, m["net"])
        self.k.B("asic", (-300.0, y + 3.5, -150), (-100.0, y + 18, 0), m["cold"])

    # -- overlays and flows -------------------------------------------------------------------------

    def at(self, p):
        return add(self.o, p)

    def tray_y(self, i):
        return self.o[1] + slot_y(i) + U / 2

    def bar_front(self, x_bar, y):
        return self.at(((x_bar[0] + x_bar[1]) / 2, y, CZ))

    def spin_fans(self, f0, f1, name="fans"):
        for j, c in enumerate(self.fans):
            fan(self.m, self.root, self.at(c), 15.0, "x", f"{self.name}_{name}{j}", f0, f1, turns=(f1 - f0) / 8.0, depth=10.0)

    def ac_flow(self, iv, shelves=None, feed=True, inside=True, period=40):
        """Amber beads: busway tap down the feed to the PDU, along each whip into a shelf, through the
        backplane trace into the PSU's connector, then forward through the PSU to its transformer."""
        m, r = self.m, self.root
        if feed:
            loop_run(r, f"{self.name}_acf", self.feed_pts, 4, 9.0, m["ac"], iv, 48)
            pdu_c = self.at(((PDU_X[0] + PDU_X[1]) / 2, 0, PDU_Z[1] + 4))
            conveyor(r, f"{self.name}_acpdu", [((pdu_c[0], self.o[1] + RY1 - 30, pdu_c[2]), (pdu_c[0], self.o[1] + Y0 + 10, pdu_c[2]))], 70.0, 6.0, m["ac"], iv, 24)
        for i in (shelves or SHELVES):
            loop_run(r, f"{self.name}_acw{i}", self.whips[i], 3, 7.5, m["ac"], iv, 40)
        if inside:
            segs = [(self.at((TX1 - 8, slot_y(i) + 11, CZ)), self.at((-170.0, slot_y(i) + 11, CZ))) for i in (shelves or SHELVES)]
            conveyor(r, f"{self.name}_acin", segs, 56.0, 4.5, m["ac"], iv, period)
            segs = [(self.at((-170.0, slot_y(i) + 11, CZ)), self.at((-370.0, slot_y(i) + 11, CZ))) for i in (shelves or SHELVES)]
            conveyor(r, f"{self.name}_bulk", segs, 56.0, 4.5, m["bulk"], iv, period)

    def psu_dc(self, iv, shelves=None, period=24):
        """Blue beads: out of each PSU's transformer, back along its output strip and bus to the clips."""
        m, r = self.m, self.root
        sh = shelves or SHELVES
        segs = [(self.at((-380.0, slot_y(i) + 34.5, CZ)), self.at((BP[0] - 6, slot_y(i) + 29, CZ))) for i in sh]
        # all point +x (the small y slope is the same for every shelf)
        conveyor(r, f"{self.name}_psudc", segs, 50.0, 4.5, m["dc"], iv, period)

    def bar_flow(self, iv, spacing=46.0, size=6.0, period=20, name="bar"):
        """Blue beads down the +50 V bar from the top shelves and up it from the bottom ones, meeting
        in the middle of the rack; return beads go the other way on the return bar."""
        m, r = self.m, self.root
        xp = (BP[0] + BP[1]) / 2
        xn = (BN[0] + BN[1]) / 2
        top0, bot0 = slot_y(SHELVES[4]) + 29, slot_y(SHELVES[3]) + 29
        conveyor(r, f"{self.name}_{name}_dn", [(self.at((xp, top0, CZ)), self.at((xp, MID_Y, CZ))),
                                                (self.at((xn, MID_Y, CZ)), self.at((xn, bot0, CZ)))], spacing, size, m["dc"], iv, period)
        conveyor(r, f"{self.name}_{name}_up", [(self.at((xp, bot0, CZ)), self.at((xp, MID_Y, CZ))),
                                                (self.at((xn, MID_Y, CZ)), self.at((xn, top0, CZ)))], spacing, size, m["dc"], iv, period)

    def taps(self, iv, trays=None, spacing=28.0, size=4.5, period=20, name="tap"):
        """Blue beads off the bar through each tray's clip into its power board's converter brick."""
        segs = [(self.at((BP[0] + 4, slot_y(i) + U / 2, CZ)), self.at((410.0, slot_y(i) + U / 2, CZ))) for i in (trays or TRAYS)]
        conveyor(self.root, f"{self.name}_{name}", segs, spacing, size, self.m["dc"], iv, period)

    def board_flow(self, iv, trays=None, period=24):
        """From the brick on along the board toward the GPUs (the VRMs take it from there)."""
        segs = [(self.at((340.0, slot_y(i) + 12, CZ)), self.at((-300.0, slot_y(i) + 12, CZ))) for i in (trays or TRAYS)]
        conveyor(self.root, f"{self.name}_brd", segs, 60.0, 3.5, self.m["dc"], iv, period)

    def bar_glow(self, iv, mt="warm", name="glow"):
        g = empty(f"{self.name}_{name}", self.root)
        box(f"{self.name}_{name}_p", self.at((BP[0] - 0.5, BAR_Y0, -2)), self.at((BP[1] + 0.5, BAR_Y1, 1.0)), self.m[mt], g)
        box(f"{self.name}_{name}_n", self.at((BN[0] - 0.5, BAR_Y0, -2)), self.at((BN[1] + 0.5, BAR_Y1, 1.0)), self.m[mt], g)
        show(g, iv)
        return g

    def mark_slots(self, idx, iv, name, mt="mark", x0=None, x1=None):
        g = empty(f"{self.name}_{name}", self.root)
        for i in idx:
            y = slot_y(i)
            bracket(f"{self.name}_{name}{i}", self.at((x0 if x0 is not None else TX0 - 24, y + 1, 0)),
                    self.at((x1 if x1 is not None else TX1 + 4, y + U - 1, CZ + 2)), self.m[mt], g, 2.5)
        show(g, iv)
        return g


# ---- one power shelf from above (lid off) --------------------------------------------------------

PSU_W = 86.0           # module width (x)
PSU_L = 560.0          # module length (z, front at 0)
SHELF_D = 800.0        # shelf depth (z)
SH_W = 6 * PSU_W + 7 * 4.0


def psu_x(j):
    """Centre x of PSU j (0..5)."""
    return -SH_W / 2 + 4.0 + PSU_W / 2 + j * (PSU_W + 4.0)


class Shelf:
    """A power shelf seen from above, lid off, front toward +z. Origin `o` = centre of its front
    edge at floor level. PSU `open_j` has its own cover off to show its insides; the others are
    closed. Behind them: the backplane, three AC inlets on the left, the DC output bus to two clips on
    a stub of the rack's busbars at the rear centre."""

    def __init__(self, m, root, o=(0.0, 0.0, 0.0), name="sh", open_j=2, f_spin=(0, 1), swap_j=None):
        self.m, self.root, self.o, self.name, self.open_j = m, root, o, name, open_j
        k = Kit(name, root, o)
        B, T, Y = k.B, k.T, k.Y
        h = 44.0
        B("floor", (-SH_W / 2 - 6, 0, -SHELF_D), (SH_W / 2 + 6, 3, 0), m["shelf"])
        B("wall_l", (-SH_W / 2 - 6, 3, -SHELF_D), (-SH_W / 2, h, 0), m["shelf"])
        B("wall_r", (SH_W / 2, 3, -SHELF_D), (SH_W / 2 + 6, h, 0), m["shelf"])
        B("rear", (-SH_W / 2 - 6, 3, -SHELF_D - 6), (SH_W / 2 + 6, h, -SHELF_D), m["shelf"])
        B("ear_l", (-SH_W / 2 - 26, 0, -6), (-SH_W / 2 - 6, h, 0), m["shelf"])
        B("ear_r", (SH_W / 2 + 6, 0, -6), (SH_W / 2 + 26, h, 0), m["shelf"])
        B("bp", (-SH_W / 2, 3, -SHELF_D), (SH_W / 2, 6, -PSU_L - 8), m["pcb"])
        for j in range(6):
            if j == swap_j:
                continue
            self._module(k, j, open_=(j == open_j))
        # backplane: PSU sockets, the DC output bus (two copper bars) and the AC trace
        for j in range(6):
            x = psu_x(j)
            B("sock", (x - 30, 6, -PSU_L - 22), (x + 30, 34, -PSU_L - 8), m["plug"])
        self.bus_z = -PSU_L - 70
        B("bus_p", (-SH_W / 2 + 20, 20, self.bus_z - 10), (SH_W / 2 - 20, 30, self.bus_z + 10), m["copper"])
        B("bus_n", (-SH_W / 2 + 20, 20, self.bus_z - 40), (SH_W / 2 - 20, 30, self.bus_z - 20), m["copper"])
        for j in range(6):
            x = psu_x(j)
            B("leg_p", (x - 8, 20, -PSU_L - 22), (x + 2, 30, self.bus_z), m["copper"])
            B("leg_n", (x + 6, 12, -PSU_L - 22), (x + 16, 20, self.bus_z - 30), m["copper"])
        B("out_p", (-10, 20, -SHELF_D - 40), (10, 30, self.bus_z), m["copper"])
        B("out_n", (24, 12, -SHELF_D - 40), (44, 20, self.bus_z - 30), m["copper"])
        self.ac_z = -PSU_L - 130
        B("ac_tr", (-SH_W / 2 + 20, 6, self.ac_z - 6), (SH_W / 2 - 20, 8, self.ac_z + 6), m["copper"])
        for j in range(6):
            x = psu_x(j)
            B("ac_leg", (x - 26, 6, self.ac_z), (x - 16, 8, -PSU_L - 22), m["copper"])
        self.inlets = []
        for q in range(3):
            x = -SH_W / 2 + 40 + q * 70
            B("inlet", (x - 26, 6, -SHELF_D - 30), (x + 26, 40, -SHELF_D + 6), m["plug"])
            B("inlet_tr", (x - 4, 6, -SHELF_D), (x + 4, 8, self.ac_z), m["copper"])
            self.inlets.append((x, 40.0, -SHELF_D - 30))
        # the rack's busbar stub behind, with the shelf's clips gripping it
        bz = -SHELF_D - 70
        B("rbar_p", (-12, -260, bz - 16), (12, 300, bz), m["copper"])
        B("rbar_n", (22, -260, bz - 16), (46, 300, bz), m["copper"])
        for xx in (-12, 22):
            B("jaw_f", (xx - 4, 10, bz), (xx + 28, 34, bz + 8), m["tin"])
            B("jaw_b", (xx - 4, 10, bz - 24), (xx + 28, 34, bz - 16), m["tin"])
        B("clip_p", (-10, 20, -SHELF_D - 40), (10, 30, bz + 8), m["copper"])
        B("clip_n", (24, 12, -SHELF_D - 40), (44, 20, bz + 8), m["copper"])
        self.bar = (17.0, bz)
        k.seal()
        self.k = k
        for j in range(6):
            if j == swap_j:
                continue
            fan(m, root, add(o, (psu_x(j), 22.0, -22.0)), 17.0, "z", f"{name}_fan{j}", f_spin[0], f_spin[1], turns=(f_spin[1] - f_spin[0]) / 8.0, depth=10.0)

    def _module(self, k, j, open_=False, parent_kit=None):
        B, T, Y, m = k.B, k.T, k.Y, self.m
        x = psu_x(j)
        w = PSU_W / 2
        B("m_floor", (x - w, 3, -PSU_L), (x + w, 5, 0), m["psu"])
        B("m_wl", (x - w, 5, -PSU_L), (x - w + 2, 40, 0), m["psu"])
        B("m_wr", (x + w - 2, 5, -PSU_L), (x + w, 40, 0), m["psu"])
        B("m_face_t", (x - w, 36, -3), (x + w, 40, 0), m["psu"])
        B("m_face_b", (x - w, 5, -3), (x + w, 8, 0), m["psu"])
        B("m_handle", (x + w - 16, 10, 0), (x + w - 8, 34, 14), m["fan"])
        B("m_led", (x - w + 6, 30, 0), (x - w + 12, 34, 2), m["led"])
        Kz = pipe_z(f"{self.name}_shroud{j}_{k.n}", add(self.o, (x, 22.0, 0)), -40.0 + self.o[2], -3.0 + self.o[2], 20.0, 18.0, m["fan"], k.g, 20)
        k.keep(Kz)
        if not open_:
            B("m_cover", (x - w, 40, -PSU_L), (x + w, 42, -3), m["psu"])
            return
        B("m_pcb", (x - w + 3, 5, -PSU_L + 10), (x + w - 3, 7, -46), m["pcb"])
        # from the front (fan) back: output caps, sync rectifiers, transformer, LLC FETs, bulk caps,
        # PFC inductor, PFC FETs, EMI filter, rear connector
        for q in range(3):
            for r_ in range(2):
                T("ocap", (x - 24 + q * 16, 7, -70 - r_ * 22), (x - 24 + q * 16, 24, -70 - r_ * 22), 6.0, m["cap"], 12)
                T("ocap_t", (x - 24 + q * 16, 24, -70 - r_ * 22), (x - 24 + q * 16, 25, -70 - r_ * 22), 6.0, m["cap_top"], 12)
        for q in range(4):
            B("sr", (x - 30 + q * 15, 7, -134), (x - 20 + q * 15, 10, -122), m["ic"])
        B("xf_core", (x - 30, 7, -205), (x + 12, 34, -150), m["ferrite"])
        B("xf_wind", (x - 26, 13, -211), (x + 8, 28, -144), m["copper"])
        B("hs_base", (x - 34, 7, -275), (x + 34, 12, -236), m["heatsink"])
        for q in range(6):
            B("hs_fin", (x - 34 + q * 13, 12, -272), (x - 30 + q * 13, 34, -239), m["heatsink"])
        for q in (-18, 18):
            T("bulk", (x + q, 7, -318), (x + q, 38, -318), 15.0, m["cap"], 20)
            T("bulk_t", (x + q, 38, -318), (x + q, 39.5, -318), 15.0, m["cap_top"], 20)
        Y("pfc", (x, 0, -385), 7, 24, 25.0, 9.0, m["copper"], verts=28)
        B("pfc_hs", (x - 34, 7, -440), (x + 34, 12, -418), m["heatsink"])
        for q in range(6):
            B("pfc_fin", (x - 34 + q * 13, 12, -438), (x - 30 + q * 13, 30, -420), m["heatsink"])
        Y("emi_a", (x - 16, 0, -490), 7, 22, 12.0, 4.5, m["ferrite"], verts=20)
        Y("emi_b", (x + 16, 0, -490), 7, 22, 12.0, 4.5, m["ferrite"], verts=20)
        B("xcap", (x - 30, 7, -530), (x + 30, 22, -514), m["xcap"])
        B("conn", (x - 30, 7, -PSU_L + 8), (x + 30, 30, -PSU_L), m["plug"])
        B("strip", (x + w - 9, 7, -PSU_L + 8), (x + w - 4, 30, -60), m["copper"])
        self.pts = {
            "fan": (x, 36.0, -22.0), "ocap": (x - 10, 25.0, -80.0), "xfmr": (x - 8, 34.0, -178.0),
            "fets": (x, 34.0, -255.0), "bulk": (x + 18, 39.5, -318.0), "pfc": (x, 24.0, -385.0),
            "emi": (x - 16, 22.0, -490.0), "conn": (x, 30.0, -PSU_L + 4), "strip": (x + w - 6, 30.0, -300.0),
        }

    def at(self, p):
        return add(self.o, p)

    def psu_flow(self, iv, period=24):
        """Inside the open PSU: amber AC from the connector to the bulk caps, pink ~400 V DC on to
        the transformer, blue DC out to the output caps, then back along the copper strip."""
        x = psu_x(self.open_j)
        m, r, n = self.m, self.root, self.name
        y = 44.0
        conveyor(r, f"{n}_pac", [(self.at((x - 4, y, -PSU_L + 6)), self.at((x - 4, y, -330.0)))], 30.0, 5.0, m["ac"], iv, period)
        conveyor(r, f"{n}_pbulk", [(self.at((x - 4, y, -330.0)), self.at((x - 4, y, -190.0)))], 30.0, 5.0, m["bulk"], iv, period)
        conveyor(r, f"{n}_pdc", [(self.at((x - 4, y, -190.0)), self.at((x - 4, y, -66.0)))], 30.0, 5.0, m["dc"], iv, period)
        conveyor(r, f"{n}_pret", [(self.at((x + PSU_W / 2 - 6, 33.0, -64.0)), self.at((x + PSU_W / 2 - 6, 33.0, -PSU_L + 10)))], 34.0, 4.5, m["dc"], iv, period)

    def ac_in(self, iv, period=24):
        """Amber from the three inlets along the backplane trace to every PSU's socket."""
        m, r, n = self.m, self.root, self.name
        segs = [(self.at((ix, 12.0, -SHELF_D)), self.at((ix, 12.0, self.ac_z))) for ix, _, _ in self.inlets]
        conveyor(r, f"{n}_acin", segs, 34.0, 5.0, m["ac"], iv, period)
        x0 = self.inlets[0][0]
        conveyor(r, f"{n}_actr", [(self.at((x0, 12.0, self.ac_z)), self.at((SH_W / 2 - 24, 12.0, self.ac_z)))], 34.0, 5.0, m["ac"], iv, period)
        segs = [(self.at((psu_x(j) - 21, 12.0, self.ac_z)), self.at((psu_x(j) - 21, 12.0, -PSU_L - 20))) for j in range(6)]
        conveyor(r, f"{n}_acleg", segs, 30.0, 5.0, m["ac"], iv, period)

    def dc_out(self, iv, period=24, js=range(6)):
        """Blue from every PSU's socket down its leg to the output bus, along it to the centre and out
        through the clip onto the rack's busbar."""
        m, r, n = self.m, self.root, self.name
        segs = [(self.at((psu_x(j) - 3, 34.0, -PSU_L - 22)), self.at((psu_x(j) - 3, 34.0, self.bus_z))) for j in js]
        conveyor(r, f"{n}_dcleg", segs, 30.0, 5.0, m["dc"], iv, period)
        conveyor(r, f"{n}_dcl", [(self.at((-SH_W / 2 + 24, 34.0, self.bus_z)), self.at((0, 34.0, self.bus_z)))], 34.0, 5.0, m["dc"], iv, period)
        conveyor(r, f"{n}_dcr", [(self.at((SH_W / 2 - 24, 34.0, self.bus_z)), self.at((0, 34.0, self.bus_z)))], 34.0, 5.0, m["dc"], iv, period)
        conveyor(r, f"{n}_dcout", [(self.at((0, 34.0, self.bus_z)), self.at((0, 34.0, self.bar[1] + 4)))], 30.0, 5.0, m["dc"], iv, period)
        bx, bz = self.bar
        conveyor(r, f"{n}_dcbar", [(self.at((0, 34.0, bz + 4)), self.at((0, -240.0, bz + 4)))], 36.0, 5.0, m["dc"], iv, period)

    def module(self, j, name, open_=False):
        """A loose PSU module (for the hot-swap), as its own group at the shelf position j."""
        k = Kit(f"{self.name}_{name}", self.root, self.o)
        self._module(k, j, open_)
        g = k.seal()
        fan(self.m, g, add(self.o, (psu_x(j), 22.0, -22.0)), 17.0, "z", f"{self.name}_{name}_fan", 0, 1, 0.0, 10.0)
        return g


# ---- closed racks from the front ------------------------------------------------------------------


def rack_closed(m, root, o, kind="nvl", name="rc", h=None):
    """A whole rack seen from the front (front face at z = o.z, facing +z), 600 wide, 1200 deep.
    kind: 'nvl' (an NVL72-class AI rack), 'cloud' (air-cooled 2U servers), 'mw' (a 1 MW-class rack
    of vertical blades), 'sidecar' (an 800 V power rack: converter shelves and storage)."""
    k = Kit(name, root, o)
    B, T = k.B, k.T
    H = h or RY1
    B("body", (-300, 0, -1200), (300, H + 30, -6), m["frame"])
    B("post_l", (-300, 0, -6), (-276, H + 30, 0), m["frame"])
    B("post_r", (276, 0, -6), (300, H + 30, 0), m["frame"])
    B("top", (-300, H, -6), (300, H + 30, 0), m["frame"])
    pts = {}
    if kind == "nvl":
        for i, kd in enumerate(LAYOUT):
            y = slot_y(i)
            mt = {"shelf": m["shelf"], "bbu": m["net"], "compute": m["compute"], "switch": m["switch"], "net": m["net"]}[kd]
            B("bez", (-272, y + 1.5, -6), (272, y + U - 1.5, 4), mt)
            if kd == "shelf":
                for j in range(6):
                    x = -230 + j * 92
                    B("psu_fan", (x - 13, y + 6, 4), (x + 13, y + U - 6, 6), m["fan"])
            elif kd in ("compute", "switch"):
                B("led", (230, y + 16, 4), (240, y + 26, 6), m["led"])
        pts["shelf_top"] = add(o, (0, slot_y(SHELVES[5]) + U / 2, 6))
        pts["shelf_bot"] = add(o, (0, slot_y(SHELVES[1]) + U / 2, 6))
        pts["trays"] = add(o, (0, slot_y(17), 6))
    elif kind == "cloud":
        y = Y0
        n = 0
        while y + 2 * U < H - 200:
            if n % 4 == 3:
                B("blank", (-272, y + 1.5, -10), (272, y + 2 * U - 1.5, 0), m["panel"])
            else:
                B("srv", (-272, y + 1.5, -6), (272, y + 2 * U - 1.5, 4), m["server"])
                for j in range(8):
                    x = -230 + j * 62
                    B("srv_fan", (x - 18, y + U - 18, 4), (x + 18, y + U + 18, 6), m["fan"])
                B("led", (240, y + 20, 4), (252, y + 30, 6), m["led"])
            y += 2 * U
            n += 1
        B("tor", (-272, H - 140, -6), (272, H - 100, 4), m["net"])
        pts["servers"] = add(o, (0, H / 2, 6))
    elif kind == "mw":
        B("shelf_t", (-272, H - 220, -6), (272, H - 40, 4), m["shelf"])
        B("shelf_b", (-272, Y0, -6), (272, Y0 + 180, 4), m["shelf"])
        x = -262.0
        while x < 262:
            B("blade", (x, Y0 + 196, -6), (x + 14, H - 236, 6), m["compute"])
            x += 18.0
        pts["blades"] = add(o, (0, H / 2, 6))
    elif kind == "sidecar":
        for j in range(6):
            y = Y0 + 40 + j * 190
            B("conv", (-272, y, -6), (272, y + 150, 4), m["sidecar"])
            for q in range(4):
                B("vent", (-240 + q * 130, y + 30, 4), (-150 + q * 130, y + 120, 6), m["fan"])
            B("led", (230, y + 60, 4), (244, y + 90, 7), m["hv"])
        yb = Y0 + 40 + 6 * 190
        B("store", (-272, yb, -6), (272, H - 40, 4), m["net"])
        for q in range(8):
            T("store_c", (-230 + q * 66, yb + 30, 10), (-230 + q * 66, H - 70, 10), 22.0, m["cell"], 12)
        pts["conv"] = add(o, (0, Y0 + 400, 6))
        pts["store"] = add(o, (0, (yb + H) / 2, 6))
    k.seal()
    return k.g, pts


# ---- camera ---------------------------------------------------------------------------------------


def glide_camera(root, poses, glide=0.24):
    """One (target, distance, yaw, pitch) pose per beat: the camera eases from the last pose to the
    next over the first `glide` of each beat, then holds with a slow push-in."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        cp, sp = math.cos(pitch), math.sin(pitch)
        jump = i > 0 and math.dist(t, poses[i - 1][0]) > 4000.0
        a = F(i, 0) if (i == 0 or jump) else F(i, glide)
        b = F(i + 1, 0) - 1
        for f, d in ((a, dist * 1.03), (b, dist * 0.97)):
            e = (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))
            key(target, f, "location", P(*t))
            key(eye, f, "location", P(*e))


def frame(lo, hi, yaw=0.0, pitch=0.2, pad=1.1):
    """A pose that fits the box lo..hi into the left pane (about 1.14 wide per 1 high, vertical
    field 0.52 rad) seen from (yaw, pitch): every corner is projected through the real perspective,
    the distance found by bisection, and the target shifted so the box sits centred."""
    tv = math.tan(0.26) / pad
    th = tv * 1.137
    cp, sp = math.cos(pitch), math.sin(pitch)
    fwd = (cp * math.sin(yaw), sp, cp * math.cos(yaw))
    right = (math.cos(yaw), 0.0, -math.sin(yaw))
    up = (-sp * math.sin(yaw), cp, -sp * math.cos(yaw))
    corners = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]

    def dot(a, b):
        return sum(a[i] * b[i] for i in range(3))

    def spans(c, d):
        xs, ys = [], []
        for q in corners:
            v = [q[i] - c[i] for i in range(3)]
            depth = d - dot(v, fwd)
            xs.append(dot(v, right) / depth)
            ys.append(dot(v, up) / depth)
        return min(xs), max(xs), min(ys), max(ys)

    d = 100.0
    for _ in range(3):
        a, b = 1.0, 60000.0
        for _ in range(60):
            mid = (a + b) / 2
            x0, x1, y0, y1 = spans(c, mid)
            if max(-x0, x1) <= th and max(-y0, y1) <= tv:
                b = mid
            else:
                a = mid
        d = b
        x0, x1, y0, y1 = spans(c, d)
        sx, sy = (x0 + x1) / 2 * d, (y0 + y1) / 2 * d
        c = [c[i] + right[i] * sx + up[i] * sy for i in range(3)]
    return (tuple(c), max(d, 90.0), yaw, pitch)


def after(b, u, beats=BEATS):
    return [(F(b, u), F(beats, 0))]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def floor(m, root, lo, hi, name="floor"):
    """A raised-floor slab under an area (its top at y = 0)."""
    return box(name, (lo[0], -40.0, lo[1]), (hi[0], 0.0, hi[1]), m["floor"], root)
