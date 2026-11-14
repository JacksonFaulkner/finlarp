"""The INGOT pieces as Blender parts for the overview, zooms and sections: the as-pulled rod and its
cones, the crop blades, the grinder, the V notch, the X-ray cut-face test, the wire web and the
wafers. Built on sand_overview.py and sand_zooms.py (docs/diagram-pages.md).

Units are millimetres, Y up (see P). The rod lies along poly X on the axis y = A, z = 0. A rod is
built at the origin of its own group and moved by location keys, so its parts use local x (the
body spans -HALF..HALF). Station equipment is built at absolute positions X.

Schematic, not to scale: the body is short, the cones, notch, kerf and skin are drawn larger than
life, and the wafers are drawn thick so the kerf shows.
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, empty, key, label, mat, show, tube  # noqa: E402
from sand_overview import _smooth  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402

END = F(40, 0)  # "until the end" for intervals; later than any scene

A = 620.0  # rod axis height
R = 150.0  # the finished 300 mm body
RAW = 170.0  # the as-pulled skin, a little over size before grinding
HALF = 500.0  # half the body length
CONE = 140.0  # each cone's length (drawn)
CONE_R = 35.0  # the cone tip
STAGE_W = 1600.0  # spacing of the stations along X
STA_Y = 450.0  # top of the cradles
PITCH = 66.0  # wafer pitch (wafer thickness plus kerf, drawn)
N_WAFERS = 14
WAFER_T = 22.0
SAW_LIFT = 420.0  # the ingot starts this far above the wire web
WHEEL_R = 230.0
GAP = 16.0  # how far the wafers spread apart after the cut

# the V groove on the top of the body, a convex triangle (y, z) in poly coordinates
V_PROF = [(A + R + 16, -46.0), (A + R + 16, 46.0), (A + R - 46, 0.0)]
V_PROF_REL = [(y - A, z) for y, z in V_PROF]


def add_mats(m):
    m["si"] = mat("ingot_si", (0.62, 0.65, 0.70), metal=0.85, rough=0.22)
    m["raw"] = mat("ingot_raw", (0.50, 0.46, 0.42), metal=0.5, rough=0.6)
    m["scrap"] = mat("ingot_scrap", (0.30, 0.29, 0.28), rough=0.8)
    m["wire"] = mat("ingot_wire", (0.85, 0.86, 0.90), metal=1.0, rough=0.2)
    m["xray"] = mat("ingot_xray", (0.5, 0.95, 1.0), emit=(0.5, 0.95, 1.0), strength=3.0)
    m["spot"] = mat("ingot_spot", (1.0, 0.95, 0.6), emit=(1.0, 0.95, 0.6), strength=3.5)
    m["spark"] = mat("ingot_spark", (1.0, 0.8, 0.4), emit=(1.0, 0.8, 0.4), strength=4.0)
    m["notch"] = mat("ingot_notch", (1.0, 0.5, 0.2), emit=(1.0, 0.5, 0.2), strength=2.0)
    m["wheel"] = mat("ingot_wheel", (0.20, 0.22, 0.26), rough=0.9)
    m["blade"] = mat("ingot_blade", (0.70, 0.72, 0.76), metal=0.9, rough=0.3)
    m["gold"] = mat("ingot_gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["gold_glow"] = mat("ingot_gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["blue"] = mat("ingot_blue", (0.36, 0.56, 0.82), metal=0.2, rough=0.45)
    m["bar"] = mat("ingot_bar", (0.55, 0.58, 0.64), metal=0.5, rough=0.35)
    m["bar_hi"] = mat("ingot_bar_hi", (0.85, 0.45, 0.25), emit=(0.85, 0.45, 0.25), strength=0.4)
    m["card"] = mat("ingot_card", (0.90, 0.88, 0.82), rough=0.85)
    m["plinth"] = mat("ingot_plinth", (0.18, 0.19, 0.23), rough=0.8)
    m["grey"] = mat("ingot_grey", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    m["red"] = mat("ingot_red", (0.90, 0.22, 0.18), emit=(0.9, 0.15, 0.1), strength=2.5)
    m["ghost"] = mat("ingot_ghost", (0.6, 0.75, 0.95), rough=0.2, alpha=0.25)
    m["atom"] = mat("ingot_atom", (0.62, 0.64, 0.70), metal=0.5, rough=0.3)
    return m


def begin(name, beats):
    """A fresh file for the INGOT scene `name`: the shared materials and the root empty."""
    m, root = start(name, beats, page="ingot")
    add_mats(m)
    return m, root


# ---- shapes ---------------------------------------------------------------------------------


def xcyl(name, x0, x1, r, y, z, m, parent=None, verts=48):
    """A solid cylinder lying along poly X from x0 to x1 on the axis (y, z)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=x1 - x0, location=P((x0 + x1) / 2, y, z))
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (0, math.pi / 2, 0)
    _smooth(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


def xcone(name, x0, x1, r0, r1, y, z, m, parent=None, verts=48):
    """A cone along poly X: radius r0 at x0, r1 at x1."""
    bpy.ops.mesh.primitive_cone_add(
        vertices=verts, radius1=r0, radius2=r1, depth=x1 - x0, location=P((x0 + x1) / 2, y, z)
    )
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (0, math.pi / 2, 0)
    _smooth(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


def zcyl(name, x, y, z, r, t, m, parent=None, verts=48):
    """A disc of radius r and thickness t whose face points at the camera (axis along poly Z)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=t, location=P(x, y, z))
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (math.pi / 2, 0, 0)
    _smooth(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


def prism_x(name, x0, x1, prof, m, parent=None):
    """A convex prism along poly X from x0 to x1; `prof` is its (y, z) outline."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    a = [bm.verts.new(tuple(P(x0, y, z))) for y, z in prof]
    b = [bm.verts.new(tuple(P(x1, y, z))) for y, z in prof]
    n = len(prof)
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


def move(obj, keys):
    """Location keys (frame, (x, y)) of a group, linear between them; poly X and Y offsets."""
    for f, (x, y) in keys:
        key(obj, f, "location", P(x, y, 0), linear=True)


def station(root, m, X, cradle=True):
    """A cradle under each end of the rod at station X, on the plinth."""
    if not cradle:
        return
    for s in (-1, 1):
        box(f"cradle{s:+d}_{int(X)}", (X + s * 380 - 50, 0, -130), (X + s * 380 + 50, A - RAW + 6, 130), m["steel"], root)


def plinth(root, m, x0, x1):
    box("plinth", (x0, 0, -300), (x1, 40, 300), m["plinth"], root)


# ---- the rod --------------------------------------------------------------------------------


def rod(root, m, skin_until=None, cones=True, skin=True):
    """The as-pulled rod, built at the origin of its own group. The skin (a little over size) is
    ground away at `skin_until` (None: it stays). Returns a dict of its parts."""
    g = empty("rod", root)
    body = xcyl("body", -HALF, HALF, R, A, 0, m["si"], g)
    parts = {"group": g, "body": body, "skin": None, "cones": None}
    if skin:
        sk = xcyl("skin", -HALF, HALF, RAW, A, 0, m["raw"], g)
        if skin_until is not None:
            show(sk, [(0, skin_until)])
        parts["skin"] = sk
    cg = empty("cones", g)
    parts["cones"] = cg
    if cones:
        xcone("seed_cone", -HALF - CONE, -HALF, CONE_R, RAW, A, 0, m["scrap"], cg)
        xcone("tail_cone", HALF, HALF + CONE, RAW, CONE_R, A, 0, m["scrap"], cg)
    return parts


def crop_lines(root, m, X, f0, f1):
    """Thin orange rings where the cones meet the body (the crop lines)."""
    for s in (-1, 1):
        c = xcyl(f"crop_line{s:+d}", X + s * HALF - 5, X + s * HALF + 5, RAW + 24, A, 0, m["notch"], root)
        show(c, [(f0, f1)])


def crop(root, m, rod_parts, X, f_blade, f_fall, f_gone):
    """Blades at both joints from f_blade to f_gone; the cones drop away as scrap from f_fall."""
    for s in (-1, 1):
        b = xcyl(f"blade{s:+d}", X + s * HALF - 6, X + s * HALF + 6, 250, A, 0, m["blade"], root)
        show(b, [(f_blade, f_gone)])
    move(rod_parts["cones"], [(f_fall, (0, 0)), (f_gone, (0, -700))])
    show(rod_parts["cones"], [(0, f_gone)])


def grind(root, m, X, f0, f1):
    """A grinding wheel (axis towards the camera) traverses the top of the rod from f0 to f1, with
    sparks at the contact. The skin comes off at the rod's skin_until frame."""
    wg = empty("wheel", root)
    zcyl("wheel_m", X, A + RAW + 190, 0, WHEEL_R, 90, m["wheel"], wg)
    for k in range(6):
        ball(f"spark{k}", (X + 40 * k - 100, A + RAW + 6, 70), 10, m["spark"], wg, segs=8)
    move(wg, [(f0, (-350, 0)), (f1, (350, 0))])
    show(wg, [(max(0, f0 - 12), f1 + 12)])
    return wg


def notch(root, m, rod_parts, f0, f1):
    """A V groove cut along the full length of the body, growing from f0 to f1 (the pivot sits at
    the left end and the groove scales along X)."""
    pv = empty("notch_pv", rod_parts["group"], P(-HALF, A, 0))
    prism_x("v_notch", 0.0, 2 * HALF, V_PROF_REL, m["notch"], pv)
    scale_keys(pv, [(0, (OFF, 1, 1)), (f0, (OFF, 1, 1)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    return pv


def test(root, m, X, f_beam, f_scatter, f_align, f_end):
    """X-ray on the cut face at the rod's +X end: the beam in, the diffracted beam out, and four
    spots on the face. The spots start scattered at f_scatter and line up at f_align."""
    box("xray_src", (X + 780, A + 210, -70), (X + 880, A + 310, 70), m["steel"], root)
    box("xray_det", (X + 700, A - 310, -110), (X + 820, A - 190, 110), m["steel"], root)
    bin_ = tube("xray_in", (X + 800, A + 260, 0), (X + HALF + 8, A + 40, 0), 7, m["xray"], root, verts=8)
    bout = tube("xray_out", (X + HALF + 8, A + 40, 0), (X + 760, A - 250, 0), 7, m["xray"], root, verts=8)
    show(bin_, [(f_beam, f_end)])
    show(bout, [(f_beam, f_end)])
    aligned = [(70, 0), (-70, 0), (0, 70), (0, -70)]
    scatter = [(-40, 95), (100, -30), (30, -100), (-100, 25)]
    for k, ((dy, dz), (sy, sz)) in enumerate(zip(aligned, scatter)):
        xs = X + HALF + 16
        s = ball(f"spot{k}", (xs, A + dy, dz), 26, m["spot"], root, segs=10)
        key(s, f_scatter, "location", P(xs, A + sy, sz), linear=True)
        key(s, f_align, "location", P(xs, A + dy, dz), linear=True)
        show(s, [(f_scatter, f_end)])


def saw(root, m, rod_parts, X, f_cut, f_spread, f_end):
    """The wire web (wires in the kerf between wafer positions, two rollers) and the ingot, which
    is cut at f_cut into wafers that spread apart from f_spread to f_end. The caller moves the rod
    group through the web."""
    for k in range(N_WAFERS - 1):
        x = X + (k - (N_WAFERS - 2) / 2) * PITCH  # the kerf between wafers k and k+1
        tube(f"wire{k}", (x, A, -430), (x, A, 430), 4, m["wire"], root, verts=8)
    for s in (-1, 1):
        xcyl(f"roller{s:+d}", X - 580, X + 580, 70, A, s * 440, m["steel"], root)
    beam = empty("mount_beam", rod_parts["group"])
    box("mount_beam_m", (-HALF - 70, A + RAW, -80), (HALF + 70, A + RAW + 70, 80), m["steel"], beam)
    show(beam, [(0, f_end)])
    show(rod_parts["body"], [(0, f_cut)])
    if rod_parts["skin"] is not None:
        show(rod_parts["skin"], [(0, f_cut)])
    for i in range(N_WAFERS):
        x = (i - (N_WAFERS - 1) / 2) * PITCH
        wg = empty(f"wafer{i}", rod_parts["group"])
        xcyl(f"wafer_m{i}", x - WAFER_T / 2, x + WAFER_T / 2, R, A, 0, m["si"], wg)
        show(wg, [(f_cut, END)])
        spread = (i - (N_WAFERS - 1) / 2) * GAP
        move(wg, [(f_cut, (0, 0)), (f_spread, (0, 0)), (f_end, (spread, 0))])
    return beam


# ---- the overview line ---------------------------------------------------------------------


def line(root, m, names, tags=None, marks=False, skin_grind=None):
    """The rod moved through the stations named in `names`, one station per beat: 'asp', 'crop',
    'test', 'grind', 'notch' or 'saw'. Station i is at X = i * STAGE_W during beat i, and the rod
    arrives in its first 15%. `tags` maps a beat to (text, dx, dy, dz) labels for its station."""
    tags = tags or {}
    n = len(names)
    rod_skin_until = F(names.index("grind"), 0.85) if "grind" in names else None
    rp = rod(root, m, skin_until=rod_skin_until, cones=True)
    plinth(root, m, -700, STAGE_W * (n - 1) + 700)
    for i in range(n):
        station(root, m, i * STAGE_W)
    keys = [(0, (0, 0))]
    for i, nm in enumerate(names):
        X = i * STAGE_W
        if i > 0:
            if nm == "saw":
                keys += [(F(i, 0), ((i - 1) * STAGE_W, 0)), (F(i, 0.15), (X, SAW_LIFT)), (F(i, 0.42), (X, 0))]
            else:
                keys += [(F(i, 0), ((i - 1) * STAGE_W, 0)), (F(i, 0.15), (X, 0))]
        if nm == "asp" and marks:
            crop_lines(root, m, X, F(i, 0.25), F(i + 1, 0))
        if nm == "crop":
            if marks:
                crop_lines(root, m, X, F(i, 0.0), F(i, 0.4))
            crop(root, m, rp, X, F(i, 0.1), F(i, 0.35), F(i, 0.85))
        if nm == "test":
            test(root, m, X, F(i, 0.25), F(i, 0.3), F(i, 0.6), F(i + 1, 0))
        if nm == "grind":
            grind(root, m, X, F(i, 0.2), F(i, 0.85))
        if nm == "notch":
            notch(root, m, rp, F(i, 0.2), F(i, 0.9))
        if nm == "saw":
            saw(root, m, rp, X, F(i, 0.42), F(i, 0.6), F(i + 1, 0))
        for text, dx, dy, dz in tags.get(i, []):
            label(text, (X + dx, dy, dz), root, [(F(i, 0.3), F(i + 1, 0))])
    # the rod's keys: station moves, the saw lift, and the hold at each station
    keys = sorted({f: v for f, v in keys}.items())
    move(rp["group"], keys)
    return rp
