"""Detailed part builders for the LASER page's numbered sections (fiber_laser_sections.py).

Units mm, Y up, camera on +z, cut-away at z = 0 (docs/diagram-pages.md). The parts are drawn far
larger than life (a section is a close-up), so each builder takes a scale `s` and an origin:

  chip       an InP EML: DFB laser section (quantum-well stripe, grating, ridge, gold pad) and an
             electro-absorption modulator section (own pad), HR coat on the back facet, AR on the front
  submount   the AlN submount under the chip, AuSn solder, the monitor photodiode behind the back facet
  can parts  header with glass-sealed pins, heat-sink post, the welded cap with its window
  wires      gold bond wires (arcs), pins with bends, copper traces
  optics     cones for beams, an aspheric lens, ferrules and fibre

and a camera that frames one subject per beat (`frame`, `camera_path`).
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, tube, ball, cut, key, _smooth  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402

# ---- materials ------------------------------------------------------------------------------


def materials():
    return {
        "inp": mat("fl_inp", (0.20, 0.22, 0.29), metal=0.25, rough=0.45),
        "inp_p": mat("fl_inp_p", (0.32, 0.29, 0.40), metal=0.2, rough=0.45),
        "mqw": mat("fl_mqw", (0.62, 0.28, 0.58), rough=0.4),
        "barrier": mat("fl_barrier", (0.35, 0.16, 0.34), rough=0.4),
        "grating": mat("fl_grating", (0.35, 0.78, 0.82), rough=0.35),
        "eam": mat("fl_eam", (0.20, 0.62, 0.52), rough=0.4),
        "bcb": mat("fl_bcb", (0.62, 0.50, 0.26), rough=0.6),
        "hr": mat("fl_hr", (0.88, 0.90, 0.94), metal=1.0, rough=0.12),
        "ar": mat("fl_ar", (0.35, 0.55, 1.0), rough=0.1, alpha=0.5),
        "aln": mat("fl_aln", (0.86, 0.84, 0.78), rough=0.65),
        "ausn": mat("fl_ausn", (0.80, 0.68, 0.38), metal=0.8, rough=0.35),
        "pd_active": mat("fl_pd_active", (0.18, 0.30, 0.75), metal=0.3, rough=0.25),
        "pd_lit": mat("fl_pd_lit", (0.35, 0.55, 1.0), emit=(0.35, 0.55, 1.0), strength=3.0),
        "stripe": mat("fl_stripe", (1.0, 0.55, 0.25), emit=(1.0, 0.5, 0.2), strength=5.0),
        "stripe_dim": mat("fl_stripe_dim", (1.0, 0.45, 0.2), emit=(1.0, 0.4, 0.18), strength=3.0),
        "beam": mat("fl_beam", (1.0, 0.42, 0.2), emit=(1.0, 0.38, 0.18), strength=2.5, alpha=0.38),
        "beam_dim": mat("fl_beam_dim", (1.0, 0.42, 0.2), emit=(1.0, 0.38, 0.18), strength=1.2, alpha=0.25),
        "seal": mat("fl_seal", (0.92, 0.94, 0.96), rough=0.25, alpha=0.85),
        "header": mat("fl_header", (0.78, 0.66, 0.36), metal=0.85, rough=0.3),
        "post": mat("fl_post", (0.72, 0.56, 0.36), metal=0.8, rough=0.35),
        "can": mat("fl_can", (0.68, 0.70, 0.74), metal=0.85, rough=0.28),
        "pcb": mat("fl_pcb", (0.10, 0.34, 0.20), rough=0.7),
        "ic": mat("fl_ic", (0.08, 0.08, 0.09), rough=0.55),
        "zirconia": mat("fl_zirconia", (0.93, 0.92, 0.88), rough=0.4),
        "coating": mat("fl_coating", (0.86, 0.80, 0.62), rough=0.7),
        "clad": mat("fl_clad", (0.62, 0.80, 0.92), rough=0.15, alpha=0.6),
        "core": mat("fl_core", (0.40, 0.70, 1.0), rough=0.15),
        "rf": mat("fl_rf", (0.95, 0.35, 0.95), emit=(0.95, 0.3, 0.95), strength=6.0),
        "screen": mat("fl_screen", (0.03, 0.05, 0.07), rough=0.3),
        "grid": mat("fl_grid", (0.24, 0.30, 0.36), rough=0.5),
        "card": mat("fl_card", (0.80, 0.80, 0.78), rough=0.8),
        "lvl0": mat("fl_lvl0", (1.0, 0.4, 0.2), emit=(1.0, 0.4, 0.2), strength=0.6),
        "lvl1": mat("fl_lvl1", (1.0, 0.4, 0.2), emit=(1.0, 0.4, 0.2), strength=2.0),
        "lvl2": mat("fl_lvl2", (1.0, 0.4, 0.2), emit=(1.0, 0.4, 0.2), strength=4.5),
        "lvl3": mat("fl_lvl3", (1.0, 0.45, 0.25), emit=(1.0, 0.45, 0.25), strength=9.0),
        "eye": mat("fl_eye", (0.30, 0.90, 1.0), emit=(0.2, 0.8, 1.0), strength=1.5, alpha=0.35),
        "gaas": mat("fl_gaas", (0.30, 0.31, 0.36), metal=0.25, rough=0.45),
        "dbr_a": mat("fl_dbr_a", (0.70, 0.62, 0.42), metal=0.3, rough=0.35),
        "dbr_b": mat("fl_dbr_b", (0.36, 0.30, 0.22), metal=0.3, rough=0.4),
        "oxide": mat("fl_oxide", (0.88, 0.88, 0.92), rough=0.3),
        "si": mat("fl_si", (0.42, 0.44, 0.50), metal=0.5, rough=0.3),
        "si_wg": mat("fl_si_wg", (0.62, 0.70, 0.86), metal=0.4, rough=0.25),
        "wafer_si": mat("fl_wafer_si", (0.50, 0.52, 0.60), metal=0.7, rough=0.2),
        "wafer_inp": mat("fl_wafer_inp", (0.24, 0.24, 0.30), metal=0.6, rough=0.25),
        "die_grid": mat("fl_die_grid", (0.55, 0.42, 0.62), metal=0.4, rough=0.3),
        "halo": mat("fl_halo", (1.0, 0.75, 0.25), emit=(1.0, 0.7, 0.2), strength=1.5, alpha=0.3),
        "hot": mat("fl_hot", (1.0, 0.75, 0.25), emit=(1.0, 0.7, 0.2), strength=4.0),
        "fail": mat("fl_fail", (1.0, 0.1, 0.08), emit=(1.0, 0.08, 0.05), strength=1.6),
        "fail_halo": mat("fl_fail_halo", (1.0, 0.1, 0.08), emit=(1.0, 0.08, 0.05), strength=0.8, alpha=0.35),
        "indium": mat("fl_indium", (0.78, 0.80, 0.84), metal=1.0, rough=0.2),
        "pie_cn": mat("fl_pie_cn", (0.95, 0.40, 0.25), rough=0.5),
        "pie_rest": mat("fl_pie_rest", (0.40, 0.45, 0.55), rough=0.5),
        "tray": mat("fl_tray", (0.12, 0.13, 0.15), rough=0.6),
        "substrate": mat("fl_substrate", (0.42, 0.27, 0.15), rough=0.8),
        "oe": mat("fl_oe", (0.20, 0.40, 0.70), metal=0.4, rough=0.35),
    }


# ---- shapes ---------------------------------------------------------------------------------


def _link(name, me, m, parent):
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    _smooth(o)
    return o


def pipe_x(name, x0, x1, ro, ri, m, parent=None, cy=0.0, half=True, verts=48):
    """A hollow cylinder along x (axis at height cy). `half` keeps only z <= 0 and caps the two cut
    faces, so the wall's section shows; otherwise a whole tube."""
    a0, a1 = (math.pi, 2 * math.pi) if half else (0.0, 2 * math.pi)
    n = verts // 2 if half else verts
    angles = [a0 + (a1 - a0) * i / n for i in range(n + 1 if half else n)]
    rings = [(x0, ro), (x1, ro), (x1, ri), (x0, ri)]
    vs = []
    for x, r in rings:
        for t in angles:
            vs.append(tuple(P(x, cy + r * math.cos(t), r * math.sin(t))))
    k = len(angles)
    faces = []
    seg = range(k - 1) if half else range(k)
    for a in range(4):
        b = (a + 1) % 4
        for i in seg:
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


def rod(name, a, b, r, m, parent=None, half=True, verts=32, front=0.0):
    """A solid cylinder from a to b, cut at z = `front` (0, or a hair in front so a lit copy's
    cut face doesn't fight the part it covers) when `half`."""
    o = tube(name, a, b, r, m, parent, verts)
    return cut(o, front) if half else o


def cone(name, a, b, ra, rb, m, parent=None, verts=32, sy=1.0, sz=1.0, half=False):
    """A cone from a (radius ra) to b (radius rb). For an axis along +x, `sy`, `sz` stretch it in
    y and z (an elliptical beam)."""
    A, B = P(*a), P(*b)
    d = B - A
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=ra, radius2=rb, depth=d.length, location=(A + B) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    from mathutils import Vector
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.scale = (sy, sz, 1.0)
    o.data.materials.append(m)
    o.parent = parent
    if half:
        cut(o, 0.0)
    return o


def ellipsoid(name, c, rx, ry, rz, m, parent=None, segs=24):
    o = ball(name, c, 1.0, m, parent, segs)
    o.scale = (rx, rz, ry)  # Blender (x, y, z) = poly (x, -z, y)
    return o


def polyline(name, pts, r, m, parent=None):
    """A round wire through poly points `pts`, as a mesh."""
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


def arc(a, b, h, n=10):
    """Points of a bond-wire arc from a to b, raised `h` in y at its middle (with a kink up off a)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        lift = h * math.sin(math.pi * t ** 0.8)
        pts.append(tuple(a[j] + (b[j] - a[j]) * t + (lift if j == 1 else 0.0) for j in range(3)))
    return pts


def wire(name, a, b, h, m, parent=None, r=0.35):
    pts = arc(a, b, h)
    polyline(name, pts, r, m, parent)
    return pts


def offsets(pts):
    """A path of absolute points as offsets from its first point (for stream_of)."""
    p0 = pts[0]
    return [tuple(p[i] - p0[i] for i in range(3)) for p in pts]


# ---- the chip -------------------------------------------------------------------------------

L, L1, W = 90.0, 58.0, 22.0  # chip length, end of the DFB section, half width (s = 1 units)


def chip(m, parent, o=(0.0, 0.0, 0.0), s=1.0, full=False, name="chip"):
    """An InP EML, back facet at x = o.x, active layer centred on y = o.y, cut face at z = o.z
    (only z <= 0 is built unless `full`). Returns (points, lit groups):
    lit["dfb"], lit["eam"] are the glowing stripe overlays, hidden until the caller shows them."""
    ox, oy, oz = o

    def B(n, lo, hi, mt, g=None, fwd=0.0, mirror=True):
        z0, z1 = lo[2], hi[2]
        if full and mirror and abs(z1) < 1e-6:
            z1 = -z0
        a = (ox + s * lo[0], oy + s * lo[1], oz + s * z0)
        b = (ox + s * hi[0], oy + s * hi[1], oz + s * z1 + (0.0 if full else fwd))
        return box(f"{name}_{n}", a, b, mt, g or parent)

    B("ncontact", (0, -20, -W), (L, -19, 0), m["ausn"])
    B("substrate", (0, -19, -W), (L, -1, 0), m["inp"])
    B("mqw", (0, -1, -W), (L1, 1, 0), m["mqw"])
    for k, y in enumerate((-0.45, 0.35)):  # barriers between the wells, on the cut face
        B(f"barrier{k}", (0, y - 0.12, -W), (L1, y + 0.12, 0), m["barrier"], fwd=0.02 * s)
    B("eam", (L1, -1, -W), (L, 1, 0), m["eam"])
    B("pclad", (0, 1, -W), (L, 5, 0), m["inp_p"])
    x = 1.5
    k = 0
    while x + 1.5 <= L1 - 1.0:
        B(f"tooth{k}", (x, 1, -W), (x + 1.5, 2.4, 0), m["grating"], fwd=0.03 * s)
        x += 3.0
        k += 1
    B("ridge", (0, 5, -4), (L, 10, 0), m["inp_p"])
    B("bcb", (0, 5, -W), (L, 10, -8), m["bcb"], mirror=False)
    if full:
        B("bcb_r", (0, 5, 8), (L, 10, W), m["bcb"], mirror=False)
    B("pad_dfb", (3, 10, -15), (L1 - 3, 11, 0), m["gold"])
    B("pad_eam", (L1 + 3, 10, -15), (L - 3, 11, 0), m["gold"])
    B("hr", (-0.8, -19, -W), (0, 10, 0), m["hr"])
    B("ar", (L, -19, -W), (L + 0.8, 10, 0), m["ar"])

    lit = {}
    g = empty(f"{name}_lit_dfb", parent)
    B("lit_dfb", (0, -0.6, -5), (L1, 0.6, 0), m["stripe"], g, fwd=0.06 * s)
    lit["dfb"] = g
    g = empty(f"{name}_lit_eam", parent)
    B("lit_eam", (L1, -0.6, -5), (L, 0.6, 0), m["stripe_dim"], g, fwd=0.06 * s)
    lit["eam"] = g

    def at(x, y, z):
        return (ox + s * x, oy + s * y, oz + s * z)

    pts = {
        "front": at(L + 0.8, 0, 0),
        "back": at(-0.8, 0, 0),
        "dfb_pad": at(L1 / 2, 11, -6),
        "eam_pad": at((L1 + L) / 2, 11, -6),
        "iso": at(L1, 10.5, -6),
        "grating": at(20.5, 1.7, 0),
        "mqw": at(14, 0, 0),
        "ridge": at(36, 8, 0),
        "trench": at(36, 10, -6),
        "cut": at(45, -10, 0),
        "top": oy + 11 * s,
        "bottom": oy - 20 * s,
    }
    return pts, lit


def submount(m, parent, o=(0.0, 0.0, 0.0), s=1.0, full=False, name="sub", pd=True):
    """The AlN submount under the chip (built with the same o and s), its AuSn solder, and the
    monitor photodiode standing behind the back facet with its blue active area facing the chip."""
    ox, oy, oz = o

    def at(x, y, z):
        return (ox + s * x, oy + s * y, oz + s * z)

    zf = 1.0 if full else 0.0
    box(f"{name}_aln", at(-20, -26, -30), at(96, -20.5, 30 * zf), m["aln"], parent)
    box(f"{name}_ausn", at(-1, -20.5, -W), at(91, -20, W * zf), m["ausn"], parent)
    pts = {"aln": at(70, -23, 0), "aln_top": at(94, -20.5, -12)}
    if pd:
        box(f"{name}_pd", at(-17, -20.5, -12), at(-9, 8, 12 * zf), m["die"], parent)
        box(f"{name}_pd_win", at(-9, -10, -10), at(-8.6, 4, 10 * zf + 0.06 * (1 - zf)), m["pd_active"], parent)
        box(f"{name}_pd_pad", at(-16, 8, -10), at(-10, 8.6, -2), m["gold"], parent)
        g = empty(f"{name}_pd_lit", parent)
        box(f"{name}_pd_glow", at(-8.62, -9, -9), at(-8.4, 3, 0.1 + 9 * zf), m["pd_lit"], g)
        pts.update({"pd": at(-13, 2, 0), "pd_face": at(-8.5, -3, 0), "pd_pad": at(-13, 8.6, -6), "pd_lit": g})
    return pts


# ---- can parts --------------------------------------------------------------------------------


def header(m, parent, x0, x1, r, half, pins, name="hdr"):
    """The header disc from x0 to x1 (radius r, axis y = 0) with a glass seal round each pin
    position (y, z) that passes through it."""
    rod(f"{name}_disc", (x0, 0, 0), (x1, 0, 0), r, m["header"], parent, half, 64)
    for k, (y, z) in enumerate(pins):
        if half and z > 0:
            continue
        tube(f"{name}_seal{k}", (x0 - 0.15, y, z), (x1 + 0.15, y, z), 3.0, m["seal"], parent, 20)


def pin(name, pts, m, parent, r=1.0):
    polyline(name, pts, r, m["gold"], parent)
    return pts


def cap(m, parent, x0, x1, r, half, win_r=9.0, name="cap"):
    """The welded cap: wall, flange, front plate with its hole, and the glass window behind it."""
    t = 1.4
    pipe_x(f"{name}_wall", x0, x1, r, r - t, m["can"], parent, half=half)
    pipe_x(f"{name}_flange", x0, x0 + 3.0, r + 3.0, r - t, m["can"], parent, half=half)
    pipe_x(f"{name}_front", x1, x1 + 2.0, r, win_r - 2.0, m["can"], parent, half=half)
    rod(f"{name}_window", (x1 - 0.8, 0, 0), (x1, 0, 0), win_r, m["glass"], parent, half, 48)


def driver_ic(m, parent, lo, hi, name="drv", leads_x=None):
    """A QFN-style driver IC: black body, gold leads round its edges, a pin-1 dot."""
    box(f"{name}_body", lo, hi, m["ic"], parent)
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    for i in range(5):
        z = z0 + (z1 - z0) * (i + 1) / 6
        box(f"{name}_lr{i}", (x1 - 0.2, y0, z - 0.8), (x1 + 1.2, y0 + 1.2, z + 0.8), m["gold"], parent)
        box(f"{name}_ll{i}", (x0 - 1.2, y0, z - 0.8), (x0 + 0.2, y0 + 1.2, z + 0.8), m["gold"], parent)
    for i in range(5):
        x = x0 + (x1 - x0) * (i + 1) / 6
        box(f"{name}_lf{i}", (x - 0.8, y0, z1 - 0.2), (x + 0.8, y0 + 1.2, z1 + 1.2), m["gold"], parent)
    tube(f"{name}_dot", (x0 + 3, y1, z1 - 3), (x0 + 3, y1 + 0.15, z1 - 3), 1.0, m["steel"], parent, 12)


# ---- camera -----------------------------------------------------------------------------------

PANE = 0.53
GLIDE = 0.16


def frame(c, size, yaw=0.35, pitch=0.22, pad=1.12, min_d=58.0):
    """A pose that fits a subject `size` mm across, centred on c, in the left pane."""
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


def pipe_y(name, y0, y1, ro, ri, m, parent=None, cx=0.0, half=True, verts=48):
    """A hollow cylinder standing on y (axis at x = cx, z = 0), cut at z = 0 when `half`."""
    a0, a1 = (math.pi, 2 * math.pi) if half else (0.0, 2 * math.pi)
    n = verts // 2 if half else verts
    angles = [a0 + (a1 - a0) * i / n for i in range(n + 1 if half else n)]
    rings = [(y0, ro), (y1, ro), (y1, ri), (y0, ri)]
    vs = [tuple(P(cx + r * math.cos(t), y, r * math.sin(t))) for y, r in rings for t in angles]
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


def join(objs, name):
    """Merge meshes into one object (fewer objects in the GLB). All must share a parent."""
    objs = [o for o in objs if o is not None]
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    return o


def wedge(name, c, r, h, a0, a1, m, parent=None, n=32):
    """A pie slice lying flat (thickness h along y) at c, from angle a0 to a1 (radians, in x-z)."""
    cx, cy, cz = c
    vs = [tuple(P(cx, cy, cz)), tuple(P(cx, cy + h, cz))]
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        x, z = cx + r * math.cos(t), cz - r * math.sin(t)
        vs.append(tuple(P(x, cy, z)))
        vs.append(tuple(P(x, cy + h, z)))
    faces = []
    for i in range(n):
        b0, t0, b1, t1 = 2 + 2 * i, 3 + 2 * i, 4 + 2 * i, 5 + 2 * i
        faces += [(0, b1, b0), (1, t0, t1), (b0, b1, t1, t0)]
    faces += [(0, 2, 3, 1), (0, 1, 3 + 2 * n, 2 + 2 * n)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return _link(name, me, m, parent)


# ---- a VCSEL ----------------------------------------------------------------------------------


def vcsel(m, parent, o=(0.0, 0.0, 0.0), s=1.0, name="vc", half=True):
    """A VCSEL cut down its middle: GaAs substrate, bottom mirror stack (DBR), the mesa with its
    quantum wells, oxide aperture and top DBR, and a gold ring contact; light leaves the top.
    Returns (points, lit group, beam group)."""
    ox, oy, oz = o

    def at(x, y, z=0.0):
        return (ox + s * x, oy + s * y, oz + s * z)

    zf = 0.0 if half else 1.0
    box(f"{name}_sub", at(-22, -14, -22), at(22, -6, 22 * zf), m["gaas"], parent)
    layers = []
    for k in range(16):
        y = -6 + 0.6 * k
        layers.append(box(f"{name}_dbrb{k}", at(-22, y, -22), at(22, y + 0.6, 22 * zf), m["dbr_a" if k % 2 else "dbr_b"], parent))
    rr = 9.0 * s
    rod(f"{name}_mqw", at(0, 3.6), at(0, 4.8), rr, m["mqw"], parent, half, 48)
    rod(f"{name}_ox", at(0, 4.8), at(0, 5.3), rr, m["oxide"], parent, half, 48)
    rod(f"{name}_ap", at(0, 4.75), at(0, 5.35), 3.5 * s, m["mqw"], parent, half, 32, front=0.05 * s)
    for k in range(12):
        y = 5.3 + 0.6 * k
        rod(f"{name}_dbrt{k}", at(0, y), at(0, y + 0.6), rr, m["dbr_a" if k % 2 else "dbr_b"], parent, half, 48)
    pipe_y(f"{name}_ring", oy + s * 12.5, oy + s * 13.3, rr, 4.0 * s, m["gold"], parent, cx=ox, half=half)
    box(f"{name}_pad", at(11, 3.6, -16), at(21, 4.3, -4 if half else 4), m["gold"], parent)
    box(f"{name}_bridge", at(8.2, 3.6, -7), at(11, 13.3, -4 if half else -1), m["gold"], parent)
    lit = empty(f"{name}_lit", parent)
    rod(f"{name}_lit_a", at(0, 3.6), at(0, 5.35), 3.4 * s, m["stripe"], lit, half, 32, front=0.1 * s)
    beam = empty(f"{name}_beam", parent)
    cone(f"{name}_beam_c", at(0, 13.3), at(0, 40), 3.2 * s, 9.0 * s, m["beam"], beam, 32, half=half)
    pts = {"top": at(0, 13.3, 0), "ring": at(6.5, 13.3, 0), "aperture": at(2.5, 5.05, 0), "mqw": at(6, 4.2, 0),
           "dbr_top": at(-6, 9, 0), "dbr_bot": at(-15, -1, 0), "sub": at(-12, -10, 0), "beam": at(0, 30, 0),
           "pad": at(16, 4.3, -10)}
    return pts, lit, beam


# ---- a silicon-photonics chip with a Mach-Zehnder modulator --------------------------------------


def siph(m, parent, o=(0.0, 0.0, 0.0), s=1.0, name="sp", laser=True, fibre=True):
    """A silicon-photonics chip: silicon substrate, buried oxide, silicon waveguides (a splitter,
    two Mach-Zehnder arms with gold electrodes, a combiner), a grating coupler with a fibre above it,
    and an InP CW laser die butted to its left edge. The chip's front face is at z = o.z.
    Returns (points, paths) where paths hold the waveguide polylines for light."""
    ox, oy, oz = o

    def at(x, y, z):
        return (ox + s * x, oy + s * y, oz + s * z)

    box(f"{name}_sub", at(-50, -8, -40), at(50, -1.5, 0), m["si"], parent)
    box(f"{name}_box", at(-50, -1.5, -40), at(50, 0, 0), m["oxide"], parent)
    wy, zc, za, zb = 0.5, -20.0, -12.0, -28.0
    p_in = [at(-50, wy, zc), at(-30, wy, zc)]
    p_a = [at(-30, wy, zc), at(-26, wy, zc + 2), at(-22, wy, za), at(18, wy, za), at(22, wy, zc + 6), at(26, wy, zc)]
    p_b = [at(-30, wy, zc), at(-26, wy, zc - 2), at(-22, wy, zb), at(18, wy, zb), at(22, wy, zc - 6), at(26, wy, zc)]
    p_out = [at(26, wy, zc), at(34, wy, zc)]
    for n_, pp in (("in", p_in), ("a", p_a), ("b", p_b), ("out", p_out)):
        polyline(f"{name}_wg_{n_}", pp, 0.55 * s, m["si_wg"], parent)
    for k in range(7):
        x = 34.5 + 1.2 * k
        box(f"{name}_gc{k}", at(x, 0, -24), at(x + 0.6, 1.0, -16), m["si_wg"], parent)
    elec = {}
    for n_, (z0, z1) in (("g1", (-9.5, -7.5)), ("sig", (-21.0, -19.0)), ("g2", (-32.5, -30.5))):
        elec[n_] = box(f"{name}_el_{n_}", at(-18, 0, z0), at(14, 1.4, z1), m["gold"], parent)
        box(f"{name}_elpad_{n_}", at(-18, 0, z0 - 1.5), at(-12, 1.5, z1 + 1.5), m["gold"], parent)
    pts = {"in": at(-40, wy, zc), "arm_a": at(0, wy, za), "arm_b": at(0, wy, zb), "split": at(-27, wy, zc),
           "join": at(23, wy, zc), "gc": at(37, 1.0, -20), "el_sig": at(0, 1.4, -20), "el_g": at(0, 1.4, -8.5),
           "chip": at(0, -4, 0), "box": at(30, -0.8, 0), "out": at(30, wy, zc)}
    if laser:
        box(f"{name}_laser", at(-62, -8, -26), at(-50.3, 4, -14), m["inp"], parent)
        box(f"{name}_laser_pad", at(-60, 4, -24), at(-52, 4.5, -16), m["gold"], parent)
        box(f"{name}_laser_stripe", at(-62, 0.2, -20.6), at(-50.3, 0.8, -19.4), m["mqw"], parent)
        pts.update({"laser": at(-56, 4.5, -20), "laser_facet": at(-50.3, wy, zc)})
    if fibre:
        a, b = at(38.5, 3.0, -20), at(38.5 + 8.0, 50.0, -20)
        tube(f"{name}_fib", a, b, 3.0 * s, m["clad"], parent, 24)
        tube(f"{name}_fibcore", a, b, 0.7 * s, m["core"], parent, 12)
        pts.update({"fibre": at(42, 26, -17), "fibre_top": b})
    return pts, {"in": p_in, "a": p_a, "b": p_b, "out": p_out}


# ---- wafers, CPO package --------------------------------------------------------------------------


def wafer(m, parent, c, r, mt, die, name, pad=None, gap=0.6, t=1.2):
    """A wafer lying flat at c (radius r, thickness t) covered in a grid of dies (die = (dx, dz)),
    merged into one mesh. Returns the list of die centres."""
    cx, cy, cz = c
    tube(f"{name}_disc", (cx, cy - t, cz), (cx, cy, cz), r, mt, parent, 96)
    dx, dz = die
    dies, centres = [], []
    nx, nz = int(2 * r / dx) + 1, int(2 * r / dz) + 1
    for i in range(nx):
        for j in range(nz):
            x = cx - r + (i + 0.5) * dx
            z = cz - r + (j + 0.5) * dz
            corner = max(math.hypot(x - cx + sx * dx / 2, z - cz + sz * dz / 2) for sx in (-1, 1) for sz in (-1, 1))
            if corner > r * 0.96:
                continue
            dies.append(box(f"{name}_d{i}_{j}", (x - dx / 2 + gap / 2, cy, z - dz / 2 + gap / 2),
                            (x + dx / 2 - gap / 2, cy + 0.3, z + dz / 2 - gap / 2), pad or m["die_grid"], parent))
            centres.append((x, cy + 0.3, z))
    if dies:
        join(dies, f"{name}_dies")
    return centres
