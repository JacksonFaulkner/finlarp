"""Detailed part builders for the OPTICAL FIBER sections (fiber_fibre_sections.py).

Everything here is page-local: the fibre's layers as cut-away shells, ferrules, an MT (MPO) ferrule,
a spool, a power meter, and a camera that glides between hand-picked poses. Units mm, Y up,
camera on +z; a "half" part keeps only its z <= 0 side and caps the cut, so the camera looks into it.

Shells are built directly as closed meshes (no boolean `cut`), so concentric layers share no faces
and their cut faces never z-fight: each layer's cut face is the ring between its own two radii.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from sand_overview import F, P, _smooth, ball, box, empty, fly, key, show, tube  # noqa: E402
from pbr_kit import mat  # noqa: E402


# ---- materials -------------------------------------------------------------------------------


def materials(m):
    """Adds this page's section materials to fiber_kit's dict `m`."""
    m["core"] = mat("ff_core", (0.55, 0.88, 1.0), rough=0.1, emit=(0.35, 0.75, 1.0), strength=0.6)
    m["lit"] = mat("ff_lit", (1.0, 0.45, 0.25), emit=(1.0, 0.40, 0.18), strength=6.0)
    m["clad"] = mat("ff_clad", (0.72, 0.80, 0.88), rough=0.12)
    m["primary"] = mat("ff_primary", (0.98, 0.94, 0.80), rough=0.5)
    m["secondary"] = mat("ff_secondary", (0.12, 0.38, 0.85), rough=0.35)
    m["jacket"] = mat("ff_jacket", (0.95, 0.74, 0.10), rough=0.6)
    m["aqua"] = mat("ff_aqua", (0.15, 0.75, 0.78), rough=0.6)
    m["black"] = mat("ff_black", (0.07, 0.07, 0.08), rough=0.55)
    m["zirconia"] = mat("ff_zirconia", (0.93, 0.92, 0.88), rough=0.3)
    m["epoxy"] = mat("ff_epoxy", (0.80, 0.52, 0.12), rough=0.3)
    m["sleeve"] = mat("ff_sleeve", (0.72, 0.60, 0.40), metal=0.6, rough=0.35)
    m["housing"] = mat("ff_housing", (0.18, 0.42, 0.75), rough=0.55)
    m["mt"] = mat("ff_mt", (0.20, 0.21, 0.23), rough=0.5)
    m["ray"] = mat("ff_ray", (1.0, 0.30, 0.12), emit=(1.0, 0.28, 0.10), strength=10.0)
    m["leak"] = mat("ff_leak", (0.45, 0.75, 1.0), emit=(0.40, 0.70, 1.0), strength=8.0)
    m["normal"] = mat("ff_normal", (0.85, 0.85, 0.85), emit=(0.8, 0.8, 0.8), strength=1.5)
    m["spark"] = mat("ff_spark", (1.0, 0.75, 0.45), emit=(1.0, 0.7, 0.4), strength=8.0)
    m["screen"] = mat("ff_screen", (0.04, 0.07, 0.06), rough=0.3)
    m["bar"] = mat("ff_bar", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=4.0)
    m["bar_dim"] = mat("ff_bar_dim", (0.20, 0.35, 0.25), emit=(0.15, 0.35, 0.2), strength=1.0)
    m["half"] = mat("ff_half", (1.0, 0.55, 0.20), emit=(1.0, 0.5, 0.15), strength=3.0)
    m["heater"] = mat("ff_heater", (1.0, 0.55, 0.15), emit=(1.0, 0.45, 0.10), strength=5.0)
    m["uv"] = mat("ff_uv", (0.55, 0.35, 1.0), emit=(0.55, 0.30, 1.0), strength=5.0)
    m["foam"] = mat("ff_foam", (0.92, 0.93, 0.95), rough=0.8)
    m["foil"] = mat("ff_foil", (0.78, 0.80, 0.84), metal=0.9, rough=0.25)
    m["aramid"] = mat("ff_aramid", (0.95, 0.85, 0.45), rough=0.9)
    m["spool"] = mat("ff_spool", (0.22, 0.24, 0.28), rough=0.5)
    m["glow"] = mat("ff_glow", (1.0, 0.5, 0.25), emit=(1.0, 0.45, 0.2), strength=3.0, alpha=0.35)
    m["trail"] = mat("ff_trail", (1.0, 0.55, 0.25), emit=(1.0, 0.45, 0.15), strength=1.2)
    m["lens"] = mat("ff_lens", (0.70, 0.88, 1.0), rough=0.05, alpha=0.5)
    m["dust"] = mat("ff_dust", (0.30, 0.22, 0.14), rough=0.95)
    m["mode"] = mat("ff_mode", (1.0, 0.6, 0.3), emit=(1.0, 0.5, 0.2), strength=0.8, alpha=0.3)
    m["budget"] = mat("ff_budget", (0.35, 0.38, 0.44), rough=0.6)
    return m


# the 12 fibre colours of TIA-598, in order
RIBBON = [
    (0.10, 0.30, 0.90), (1.0, 0.45, 0.05), (0.10, 0.65, 0.20), (0.45, 0.28, 0.12),
    (0.50, 0.55, 0.60), (0.95, 0.95, 0.95), (0.90, 0.10, 0.10), (0.05, 0.05, 0.05),
    (0.95, 0.85, 0.10), (0.55, 0.20, 0.75), (0.95, 0.55, 0.65), (0.20, 0.80, 0.80),
]


# ---- geometry --------------------------------------------------------------------------------


def _v(a):
    return Vector(a)


def _mesh(name, verts, faces, m, parent):
    """A mesh object from poly-space vertices; normals made consistent (outward)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([P(*v) for v in verts], [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    _smooth(o)
    return o


def shell(name, a, b, r_in, r_out, m, parent, half=True, n=40, toward=(0, 0, 1)):
    """A tube wall from poly point `a` to `b`. Radii may be numbers or (at a, at b) pairs, so it
    can taper (a cone, a chamfer). r_in 0 makes it solid. `half` keeps only the side away from
    `toward` (the camera's side, +z) and closes the cut with flat faces."""
    A, B = _v(a), _v(b)
    d = (B - A).normalized()
    w = _v(toward)
    u = w.cross(d).normalized()
    w = d.cross(u).normalized()
    ri = r_in if isinstance(r_in, tuple) else (r_in, r_in)
    ro = r_out if isinstance(r_out, tuple) else (r_out, r_out)
    solid = ri[0] <= 0 and ri[1] <= 0
    phis = [math.pi * k / n for k in range(n + 1)] if half else [2 * math.pi * k / n for k in range(n)]
    k = len(phis)
    verts, faces = [], []

    def ring(c, r):
        base = len(verts)
        for p in phis:
            q = c + r * (math.cos(p) * u - math.sin(p) * w)
            verts.append(tuple(q))
        return base

    oa, ob = ring(A, ro[0]), ring(B, ro[1])
    if solid:
        ca = len(verts)
        verts.append(tuple(A))
        cb = len(verts)
        verts.append(tuple(B))
    else:
        ia, ib = ring(A, ri[0]), ring(B, ri[1])
    seg = range(k - 1) if half else range(k)
    for i in seg:
        j = (i + 1) % k
        faces.append((oa + i, oa + j, ob + j, ob + i))
        if solid:
            faces.append((ca, oa + j, oa + i))
            faces.append((cb, ob + i, ob + j))
        else:
            faces.append((ia + i, ib + i, ib + j, ia + j))
            faces.append((oa + i, ia + i, ia + j, oa + j))
            faces.append((ob + i, ob + j, ib + j, ib + i))
    if half:
        for i in (0, k - 1):
            if solid:
                faces.append((oa + i, ob + i, cb, ca))
            else:
                faces.append((oa + i, ob + i, ib + i, ia + i))
    return _mesh(name, verts, faces, m, parent)


def segs(name, pts, r, m, parent, verts=8):
    """A polyline of thin tubes (a ray, a wire), one group."""
    g = empty(name, parent)
    for i in range(len(pts) - 1):
        tube(f"{name}_{i}", pts[i], pts[i + 1], r, m, g, verts)
    return g


def grow_ray(name, pts, r, m, parent, f0, f1, until):
    """A ray drawn segment by segment from frame f0 to f1 (by length), held to `until`."""
    g = empty(name, parent)
    lens = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    tot, run = sum(lens), 0.0
    for i, n in enumerate(lens):
        e = empty(f"{name}_{i}", g)
        tube(f"{name}_{i}_t", pts[i], pts[i + 1], r, m, e, 8)
        show(e, [(round(f0 + (f1 - f0) * run / tot), until)])
        run += n
    head = empty(f"{name}_head", g)
    ball(f"{name}_head_s", pts[0], r * 3.0, m, head, 12)
    rel = [tuple(p[j] - pts[0][j] for j in range(3)) for p in pts]
    fly(head, rel, f0, f1, steps=max(8, 4 * len(pts)))
    show(head, [(f0, f1 + 1)])
    return g


def pulses(parent, name, n, start_pt, path, size, m, b, u0, u1, life, steps=12, end=None, scale_to=None):
    """`n` glowing blobs launched one after another between fractions u0 and u1 of beat `b`, each
    flying `path` (offsets from `start_pt`) over `life` frames. `scale_to` (sx, sy, sz) reshapes a
    blob on the way (a fading, smearing pulse)."""
    g = empty(name, parent)
    end = end if end is not None else F(b + 1, 0)
    for k in range(n):
        e = empty(f"{name}{k}", g)
        blob = ball(f"{name}{k}_s", start_pt, size, m, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=steps)
        show(e, [(f0, min(f1, end))])
        if scale_to is not None:
            key(blob, f0, "scale", (1.0, 1.0, 1.0), linear=True)
            sx, sy, sz = scale_to
            key(blob, f1, "scale", (sx, sz, sy), linear=True)  # Blender (x, y, z) = poly (x, -z, y)
    return g


def helix(name, c, axis_x0, axis_x1, r_coil, r_wire, turns, m, parent, verts=10, per_turn=32):
    """A coil of wire round the x axis through poly point `c` (a spring, a winding), one mesh."""
    pts = []
    n = int(turns * per_turn)
    for i in range(n + 1):
        t = i / n
        th = 2 * math.pi * turns * t
        x = axis_x0 + (axis_x1 - axis_x0) * t
        pts.append(P(x, c[1] + r_coil * math.cos(th), c[2] + r_coil * math.sin(th)))
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r_wire
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q.x, q.y, q.z, 1.0)
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.selected_objects:
        s.select_set(False)
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.view_layer.objects.active
    o.parent = parent
    return o, [(q.x, q.z, -q.y) for q in pts]


def rbox(name, lo, hi, m, parent, w=0.8):
    """A box with bevelled edges (reads as a moulded part)."""
    o = box(name, lo, hi, m, parent)
    if w > 0:
        mod = o.modifiers.new("bevel", "BEVEL")
        mod.width = w
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return o


# ---- camera ----------------------------------------------------------------------------------


def eye_of(t, dist, yaw, pitch):
    cp, sp = math.cos(pitch), math.sin(pitch)
    return (t[0] + dist * cp * math.sin(yaw), t[1] + dist * sp, t[2] + dist * cp * math.cos(yaw))


def glide(root, poses, glide=0.22):
    """One (target, distance, yaw, pitch) pose per beat. The camera eases from the last pose into
    the next over the first `glide` of a beat, then pushes in slowly, so each beat looks at what it
    adds and nothing jumps."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        a = F(i, 0) if i == 0 else F(i, glide)
        b = F(i + 1, 0) - 1
        for f, d in ((a, dist * 1.04), (b, dist * 0.97)):
            key(target, f, "location", P(*t))
            key(eye, f, "location", P(*eye_of(t, d, yaw, pitch)))
