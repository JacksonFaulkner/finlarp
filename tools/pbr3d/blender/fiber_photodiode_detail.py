"""Detailed part builders for the PHOTODIODE sections (fiber_photodiode_sections.py).

A receiver TO-can drawn about 16x life size (1 scene unit ~ 0.06 mm), so the sections' camera can
sit well outside pbr3d's near plane and still fill the left pane:

  cap + ball lens   steel cap at the can's -x end, a glass ball lens in its aperture
  can wall          steel cylinder, axis along x (light arrives from -x, as on the overview)
  header            the steel base at +x, gold-plated inside, four gold pins out through glass seals
  submount          white ceramic block on the header face, carrying the photodiode chip
  photodiode chip   a mesa PIN: gold ring (p contact) and blue AR coat, p-InP, i-InGaAs absorber,
                    n-InP (wider, with the gold n contact on its step), InP substrate. The chip is
                    drawn far larger than the can would hold, so its layers read.
  TIA               dark die beside the chip, gold pads, bond wires to the chip and the pin posts

Everything is cut away at z = 0 (camera on +z), so the cut faces show the layers. Units as
everywhere else: Y up, x along the can's axis. Moving carriers sit at z = +CZ, just in front of
the cut faces, so they draw over them.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, ball, box, cut, empty, fly, key, show, tube  # noqa: E402
from pbr_kit import mat  # noqa: E402

CZ = 1.6  # carriers ride this far in front of the cut plane

# ---- the can --------------------------------------------------------------------------------
CAP_X0, CAP_X1 = -47.0, -40.0     # cap end wall
WALL_X1 = 34.0                    # can wall ends at the header
HEAD_X0, HEAD_X1 = 34.0, 44.0     # header disc
CAN_R, CAN_RI, HEAD_R = 45.0, 42.0, 50.0
LENS_X, LENS_R, APER_R = -43.5, 12.0, 10.0
PIN_X1 = 130.0                    # outer pin ends
PIN_R = 1.6
# Pins (y, z) through the header. The two with posts inside are wired; the others are GND/VCC.
PINS = {"OUT": (30.0, -18.0), "VPD": (-30.0, -10.0), "GND": (0.0, -36.0), "VCC": (16.0, -32.0)}
POST_X0 = 29.0                    # posts stand inside the can from here to the header face

# ---- the chip (layers stack along x; light enters at the -x face) -----------------------------
SUB_X = (30.0, 33.5)              # ceramic submount
RING_X = (10.5, 12.5)             # gold p-contact ring on the mesa top
AR_X = (11.8, 12.5)               # anti-reflection coat inside the ring
P_X = (12.5, 15.0)                # p+ InP
I_X = (15.0, 23.0)                # intrinsic InGaAs absorber
N_X = (23.0, 25.5)                # n+ InP
S_X = (25.5, 30.0)                # InP substrate
MESA = 14.0                       # mesa half-width (p, i)
BASE = 18.0                       # n layer and substrate half-width
NC = (21.0, 23.0, -17.6, -15.0)     # n contact: x0, x1, y0, y1 on the n layer's step
RING_IN = 7.0                     # ring aperture radius
TIA_LO, TIA_HI = (27.0, 26.0, -12.0), (33.5, 38.0, 0.0)
FOCUS = (RING_X[1], 0.0, 0.0)     # where the lens focuses (the mesa top)


def materials(m):
    """Adds the photodiode's own materials to the fiber_kit dict `m`."""
    m["p_inp"] = mat("pd_p_inp", (0.80, 0.32, 0.38), rough=0.45)
    m["ingaas"] = mat("pd_ingaas", (0.78, 0.62, 0.18), metal=0.1, rough=0.4)
    m["n_inp"] = mat("pd_n_inp", (0.24, 0.40, 0.85), rough=0.45)
    m["inp_sub"] = mat("pd_inp_sub", (0.40, 0.38, 0.46), metal=0.2, rough=0.5)
    m["ar"] = mat("pd_ar", (0.35, 0.55, 1.0), rough=0.1, alpha=0.6)
    m["ceramic"] = mat("pd_ceramic", (0.86, 0.85, 0.80), rough=0.6)
    m["tia"] = mat("pd_tia", (0.13, 0.15, 0.20), metal=0.3, rough=0.35)
    m["seal"] = mat("pd_seal", (0.55, 0.75, 0.80), rough=0.15, alpha=0.5)
    m["hole"] = mat("pd_hole", (0.70, 0.35, 1.0), emit=(0.65, 0.30, 1.0), strength=8.0)
    m["volt"] = mat("pd_volt", (1.0, 0.80, 0.30), emit=(1.0, 0.80, 0.30), strength=8.0)
    m["beam"] = mat("pd_beam", (1.0, 0.40, 0.25), emit=(1.0, 0.35, 0.20), strength=1.2, alpha=0.28)
    m["flash"] = mat("pd_flash", (1.0, 0.95, 0.8), emit=(1.0, 0.95, 0.8), strength=10.0)
    m["pcb"] = mat("pd_pcb", (0.10, 0.34, 0.20), rough=0.7)
    m["ink"] = mat("pd_ink", (0.85, 0.85, 0.80), rough=0.6)
    m["si"] = mat("pd_si", (0.42, 0.45, 0.52), metal=0.6, rough=0.3)
    m["si_wg"] = mat("pd_si_wg", (0.70, 0.74, 0.80), metal=0.4, rough=0.25)
    m["oxide"] = mat("pd_oxide", (0.90, 0.92, 0.96), rough=0.3, alpha=0.55)
    m["ge"] = mat("pd_ge", (0.55, 0.45, 0.30), metal=0.5, rough=0.35)
    m["red"] = mat("pd_red", (1.0, 0.15, 0.12), emit=(1.0, 0.12, 0.10), strength=5.0)
    m["dust"] = mat("pd_dust", (0.12, 0.10, 0.08), rough=0.95)
    m["halo"] = mat("pd_halo2", (1.0, 0.85, 0.35), emit=(1.0, 0.85, 0.35), strength=1.5, alpha=0.18)
    m["guide"] = mat("pd_guide", (0.55, 0.57, 0.62), rough=0.6)
    return m


# ---- geometry ---------------------------------------------------------------------------------


def ring_x(name, x0, x1, r_in, r_out, m, parent, half=True, segs=48):
    """A ring (or, with r_in = 0, a disc) on the x axis from x0 to x1. `half` keeps only z <= 0,
    with flat faces on the cut plane, so the camera on +z looks into it."""
    if half:
        ts = [math.pi + math.pi * k / segs for k in range(segs + 1)]
    else:
        ts = [2 * math.pi * k / segs for k in range(segs)]
    n = len(ts)
    r_in = max(r_in, 0.01)
    verts = []
    for x in (x0, x1):
        for r in (r_out, r_in):
            for t in ts:
                verts.append(P(x, r * math.cos(t), r * math.sin(t)))

    def v(xi, ri, k):
        return (xi * 2 + ri) * n + k

    faces = []
    last = n - 1 if half else n
    for k in range(last):
        k2 = (k + 1) % n
        faces.append((v(0, 0, k), v(0, 0, k2), v(1, 0, k2), v(1, 0, k)))  # outer
        faces.append((v(0, 1, k), v(1, 1, k), v(1, 1, k2), v(0, 1, k2)))  # inner
        faces.append((v(0, 0, k), v(0, 1, k), v(0, 1, k2), v(0, 0, k2)))  # x0 end
        faces.append((v(1, 0, k), v(1, 0, k2), v(1, 1, k2), v(1, 1, k)))  # x1 end
    if half:
        for k in (0, n - 1):
            faces.append((v(0, 0, k), v(1, 0, k), v(1, 1, k), v(0, 1, k)))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    me.materials.append(m)
    o.parent = parent
    O._smooth(o)
    return o


def cone(name, apex, base, r, m, parent, verts=32):
    """A cone from `apex` to a disc of radius `r` at `base`, cut at z = 0."""
    A, B = P(*apex), P(*base)
    d = A - B
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=0.0, depth=d.length,
                                    location=(A + B) / 2)
    o = O._name(bpy.context.object, name)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.data.materials.append(m)
    o.parent = parent
    return cut(o, 0.0)


def curve_pts(a, b, lift, n=10):
    """Points on a bond-wire arc from a to b, bowed by the offset vector `lift` at the middle."""
    out = []
    for k in range(n + 1):
        u = k / n
        w = 4 * u * (1 - u)
        out.append(tuple(a[i] + (b[i] - a[i]) * u + lift[i] * w for i in range(3)))
    return out


def wire(name, pts, r, m, parent):
    """A wire through `pts`: a tube per segment, a ball at each joint so it reads as one piece."""
    g = empty(name, parent)
    for k in range(len(pts) - 1):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, m, g, 8)
        if k:
            ball(f"{name}_j{k}", pts[k], r, m, g, 8)
    return g


def run(parent, name, pts, n, size, m, b, u0, u1, life):
    """`n` beads that each travel the absolute polyline `pts` over `life` frames, launched one
    after another between fractions u0 and u1 of beat `b`."""
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, m, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, len(pts) * 2))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


def front(p):
    """`p` moved onto the carriers' plane, just in front of the cut faces."""
    return (p[0], p[1], CZ)


# ---- the parts --------------------------------------------------------------------------------


def can(m, parent, cut_open=True):
    """Cap with its ball lens, the can wall and the header. Cut at z = 0 when `cut_open`."""
    g = empty("pd_can_cut" if cut_open else "pd_can_whole", parent)
    h = cut_open
    ring_x("can_wall", CAP_X1, WALL_X1, CAN_RI, CAN_R, m["steel"], g, h)
    ring_x("can_cap", CAP_X0, CAP_X1, APER_R, CAN_R, m["steel"], g, h)
    ring_x("can_lip", WALL_X1 - 3.0, WALL_X1, CAN_R, CAN_R + 3.0, m["steel"], g, h)  # weld flange
    ring_x("header", HEAD_X0, HEAD_X1, 0.0, HEAD_R, m["dark_steel"], g, h)
    lens = ball("ball_lens", (LENS_X, 0.0, 0.0), LENS_R, m["glass"], g, 32)
    if h:
        cut(lens, 0.0)
        ring_x("header_gold", HEAD_X0 - 0.5, HEAD_X0, 0.0, CAN_RI, m["gold"], g, True)
    return g


def pins(m, parent):
    """Four gold pins out of the header's back, each through a glass seal bead."""
    g = empty("pd_pins", parent)
    for nm, (py, pz) in PINS.items():
        tube(f"pin_{nm}", (HEAD_X1 - 1.0, py, pz), (PIN_X1, py, pz), PIN_R, m["gold"], g, 12)
        tube(f"seal_{nm}", (HEAD_X1, py, pz), (HEAD_X1 + 1.5, py, pz), 3.6, m["seal"], g, 16)
    return g


def chip(m, parent):
    """The submount and the PIN chip on it, cut at z = 0 so the layer stack shows."""
    g = empty("pd_chip", parent)
    box("submount", (SUB_X[0], -22.0, -22.0), (SUB_X[1], 22.0, 0.0), m["ceramic"], g)
    box("solder", (S_X[1] - 0.4, -BASE, -BASE), (S_X[1] + 0.2, BASE, 0.0), m["gold"], g)
    box("substrate", (S_X[0], -BASE, -BASE), (S_X[1] - 0.4, BASE, 0.0), m["inp_sub"], g)
    box("n_inp", (N_X[0], -BASE, -BASE), (N_X[1], BASE, 0.0), m["n_inp"], g)
    box("ingaas", (I_X[0], -MESA, -MESA), (I_X[1], MESA, 0.0), m["ingaas"], g)
    box("p_inp", (P_X[0], -MESA, -MESA), (P_X[1], MESA, 0.0), m["p_inp"], g)
    # The p contact: a gold ring on the mesa top, the light entering through its middle.
    ring_x("p_ring", RING_X[0], RING_X[1], RING_IN, MESA - 1.0, m["gold"], g, True, 40)
    ring_x("ar_coat", AR_X[0], AR_X[1], 0.0, RING_IN, m["ar"], g, True, 40)
    # The n contact: a gold pad on the n layer's step beside the mesa.
    box("n_contact", (NC[0], NC[2], -6.0), (NC[1], NC[3], 0.0), m["gold"], g)
    return g


def tia(m, parent):
    """The TIA die beside the chip, its pads facing the lens, on the header face."""
    g = empty("pd_tia", parent)
    box("tia_die", TIA_LO, TIA_HI, m["tia"], g)
    for k in range(4):
        y = TIA_LO[1] + 1.5 + k * 3.0
        box(f"tia_pad{k}", (TIA_LO[0] - 0.4, y, -9.0), (TIA_LO[0], y + 1.8, -3.0), m["gold"], g)
    return g


# Bond wire routes (absolute points). Each starts on a pad and lands on a pad or post.
def routes():
    pring = (RING_X[0], 11.0, -4.0)
    tia_in = (TIA_LO[0] - 0.4, TIA_LO[1] + 2.4, -6.0)
    tia_out = (TIA_LO[0] - 0.4, TIA_LO[1] + 11.4, -6.0)
    vpd_y, vpd_z = PINS["VPD"]
    out_y, out_z = PINS["OUT"]
    ncon = ((NC[0] + NC[1]) / 2, (NC[2] + NC[3]) / 2, -3.0)
    return {
        "p_to_tia": curve_pts(pring, tia_in, (-7.0, 2.0, 0.0)),
        "n_to_vpd": curve_pts((NC[0], ncon[1], ncon[2]), (POST_X0, vpd_y, vpd_z), (-6.0, -4.0, 0.0)),
        "tia_to_out": curve_pts(tia_out, (POST_X0, out_y, out_z), (-5.0, 3.0, 0.0)),
    }


def bonds(m, parent):
    g = empty("pd_bonds", parent)
    for nm, pts in routes().items():
        wire(f"bond_{nm}", pts, 0.45, m["gold"], g)
    for nm in ("VPD", "OUT"):
        py, pz = PINS[nm]
        tube(f"post_{nm}", (POST_X0, py, pz), (HEAD_X0, py, pz), 2.0, m["gold"], g, 12)
    return g


def photodiode(m, parent, cut_open=True):
    """The whole receiver: can (cut or sealed), and, when cut, the chip, TIA and bonds inside."""
    g = empty("pd_all_cut" if cut_open else "pd_all_whole", parent)
    can(m, g, cut_open)
    if cut_open:
        chip(m, g)
        tia(m, g)
        bonds(m, g)
    return g


FIBRE_TIP = -95.0


def fibre(m, parent):
    """The fibre's end: jacket, ceramic-gold ferrule, the lit core at its tip."""
    g = empty("pd_fibre", parent)
    tube("fibre_jacket", (-300.0, 0.0, 0.0), (-150.0, 0.0, 0.0), 5.0, m["dark_steel"], g, 24)
    tube("ferrule", (-150.0, 0.0, 0.0), (FIBRE_TIP, 0.0, 0.0), 10.0, m["gold"], g, 32)
    tube("fibre_core", (FIBRE_TIP - 2.0, 0.0, 0.0), (FIBRE_TIP + 0.3, 0.0, 0.0), 1.2, m["light"], g, 12)
    return g


def beam(m, parent):
    """The light: a cone spreading from the fibre tip to the lens, a cone narrowing to the chip."""
    g = empty("pd_beam", parent)
    cone("beam_in", (FIBRE_TIP + 0.5, 0.0, 0.0), (LENS_X, 0.0, 0.0), 8.0, m["beam"], g)
    cone("beam_out", FOCUS, (LENS_X, 0.0, 0.0), 8.0, m["beam"], g)
    return g


def photons(parent, name, m, b, u0, u1, n=6, life=60, to=None, spread=6.0):
    """Photons from the fibre tip through the lens to the focus (or `to`), alternating above and
    below the axis so the beam's shape shows."""
    g = empty(name, parent)
    end = to or FOCUS
    for k in range(n):
        y = spread * (1 if k % 2 else -1) * (0.5 + 0.5 * ((k // 2) % 2))
        pts = [front((FIBRE_TIP, 0.0, 0.0)), front((LENS_X, y, 0.0)), front(end)]
        run(g, f"{name}_{k}", pts, 1, 1.1, m["light"], b, u0 + (u1 - u0) * k / max(1, n - 1),
            u0 + (u1 - u0) * k / max(1, n - 1), life)
    return g


def pair(parent, name, m, hit_y, hit_x, f0, life=50):
    """One absorbed photon at (hit_x, hit_y) in the absorber: a flash, then an electron drifting to
    the n layer and out to the n contact, and a hole drifting back to the p ring."""
    g = empty(name, parent)
    hit = front((hit_x, hit_y, 0.0))
    fl = ball(f"{name}_flash", hit, 1.8, m["flash"], g, 12)
    show(fl, [(f0, f0 + 8)])
    e_pts = [hit, front((N_X[0] + 1.2, hit_y, 0.0)), front((N_X[0] + 1.2, (NC[2] + NC[3]) / 2, 0.0)),
             front((NC[0], (NC[2] + NC[3]) / 2, 0.0))]
    ring_y = -10.0 if hit_y < 0 else 10.0
    h_pts = [hit, front((P_X[0] + 0.8, hit_y, 0.0)), front((P_X[0] + 0.8, ring_y, 0.0)),
             front((RING_X[0] + 1.0, ring_y, 0.0))]
    for tag, pts, mm, lf in (("e", e_pts, m["elec"], life), ("h", h_pts, m["hole"], int(life * 1.4))):
        e = empty(f"{name}_{tag}", g)
        ball(f"{name}_{tag}_s", pts[0], 1.0, mm, e, 12)
        path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
        fly(e, path, f0 + 4, f0 + 4 + lf, steps=9)
        show(e, [(f0 + 4, f0 + 4 + lf)])
    return g


def pairs(parent, name, m, b, u0, u1, n, life=50, photon_life=24):
    """`n` photons, each landing in the absorber and freeing a pair, spread between u0 and u1 of
    beat `b`. The photon comes in from the lens's exit through the ring's aperture."""
    g = empty(name, parent)
    for k in range(n):
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        y = [-4.0, 3.0, -1.0, 5.0, -5.5, 1.5, -2.5, 4.0, 0.5, -3.5][k % 10]
        x = [17.5, 19.5, 16.5, 21.0, 18.5, 20.0, 17.0, 19.0, 21.5, 18.0][k % 10]
        ph_pts = [front((LENS_X + LENS_R, y * 0.4, 0.0)), front((RING_X[0], y, 0.0)), front((x, y, 0.0))]
        run(g, f"{name}_ph{k}", ph_pts, 1, 1.0, m["light"], b,
            (f0 - photon_life) / F(1, 0) - b, (f0 - photon_life) / F(1, 0) - b, photon_life)
        pair(g, f"{name}_p{k}", m, y, x, f0, life)
    return g


def glide_camera(root, poses, glide=0.28):
    """One (target, distance, yaw, pitch) pose per beat. The camera eases from the last pose to
    the next over the first `glide` of each beat, then holds with a slow push-in (as
    chip_kit.glide_camera)."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        cp, sp = math.cos(pitch), math.sin(pitch)
        a = F(i, 0) if i == 0 else F(i, glide)
        b = F(i + 1, 0) - 1
        for f, d in ((a, dist * 1.04), (b, dist * 0.97)):
            e = (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))
            key(target, f, "location", P(*t))
            key(eye, f, "location", P(*e))


def frame(lo, hi, yaw=0.0, pitch=0.2, pad=1.15):
    """A pose that fits the box lo..hi (x, y, z) into the left pane (about 1.14 wide per 1 high,
    vertical field 0.52 rad) seen from (yaw, pitch): every corner is projected through the real
    perspective, the distance found by bisection, and the target shifted so the box sits centred."""
    tv = math.tan(0.26) / pad
    th = tv * 1.137
    cp, sp = math.cos(pitch), math.sin(pitch)
    fwd = (cp * math.sin(yaw), sp, cp * math.cos(yaw))  # from target toward the eye
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
        a, b = 1.0, 20000.0
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
    return (tuple(c), max(d, 70.0), yaw, pitch)


# ---- extras for the write-up's sections ----------------------------------------------------------


def blip(parent, name, pts, size, mt, f0, life):
    """One bead along the absolute polyline `pts` from frame f0 for `life` frames."""
    e = empty(name, parent)
    ball(f"{name}_s", pts[0], size, mt, e, 12)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    fly(e, path, f0, f0 + life, steps=max(4, len(pts) * 2))
    show(e, [(f0, f0 + life)])
    return e


def flash(parent, name, at, mt, f0, r=1.8, life=8):
    o = ball(name, at, r, mt, parent, 12)
    show(o, [(f0, f0 + life)])
    return o


def halo(m, parent, name, lo, hi, intervals, pad=3.0, r=0.6):
    """A glowing wire frame round a part, to single it out: its 12 edges as emissive tubes, each
    switched on for `intervals` (tubes, not a translucent box, so it reads on any background)."""
    (x0, y0, z0), (x1, y1, z1) = [tuple(v - pad for v in lo), tuple(v + pad for v in hi)]
    if hi[2] <= 0.0:
        z1 = min(z1, CZ)
    xs, ys, zs = (x0, x1), (y0, y1), (z0, z1)
    edges = []
    for y in ys:
        for z in zs:
            edges.append(((x0, y, z), (x1, y, z)))
    for x in xs:
        for z in zs:
            edges.append(((x, y0, z), (x, y1, z)))
    for x in xs:
        for y in ys:
            edges.append(((x, y, z0), (x, y, z1)))
    for k, (a, b) in enumerate(edges):
        o = tube(f"{name}_{k}", a, b, r, m["volt"], parent, 8)
        show(o, intervals)


GX = 320.0  # the germanium photodiode's centre x (it sits off to the side of the can)


def ge_pd(m, parent, gx=GX):
    """A germanium-on-silicon waveguide photodiode, cut at z = 0: silicon substrate, buried oxide,
    the silicon slab and rib waveguide carrying the light in, a germanium block grown on its end,
    an n+ cap and gold vias to the top and to the p-doped slab."""
    g = empty("ge_pd", parent)
    box("ge_sub", (gx - 90, -44.0, -50.0), (gx + 80, -28.0, 0.0), m["si"], g)
    box("ge_box", (gx - 90, -28.0, -50.0), (gx + 80, -24.0, 0.0), m["oxide"], g)
    box("ge_slab", (gx - 90, -24.0, -50.0), (gx + 80, -20.0, 0.0), m["si_wg"], g)
    box("ge_pslab", (gx + 5, -24.1, -34.0), (gx + 62, -19.9, 0.0), m["p_inp"], g)
    box("ge_rib", (gx - 90, -20.0, -6.0), (gx + 12, -14.0, 0.0), m["si_wg"], g)
    box("ge_block", (gx + 10, -20.0, -14.0), (gx + 55, -5.0, 0.0), m["ge"], g)
    box("ge_ncap", (gx + 10, -5.0, -14.0), (gx + 55, -3.5, 0.0), m["n_inp"], g)
    tube("ge_nvia", (gx + 24, -3.5, -7.0), (gx + 24, 12.0, -7.0), 2.4, m["gold"], g, 12)
    box("ge_npad", (gx + 16, 12.0, -15.0), (gx + 32, 15.0, 0.0), m["gold"], g)
    tube("ge_pvia", (gx + 48, -20.0, -26.0), (gx + 48, 12.0, -26.0), 2.4, m["gold"], g, 12)
    box("ge_ppad", (gx + 40, 12.0, -34.0), (gx + 56, 15.0, -18.0), m["gold"], g)
    return g


def ge_light(parent, name, m, b, u0, u1, n, gx=GX):
    """Photons guided along the rib into the germanium; each is absorbed (a flash) and frees a
    pair: the electron up to the n via, the hole down into the p slab and its via."""
    g = empty(name, parent)
    for k in range(n):
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        x = gx + 16 + 30 * ((k * 7) % 5) / 4
        blip(g, f"{name}_ph{k}", [front((gx - 90, -17.0, 0)), front((x, -17.0, 0))], 1.1, m["light"],
             f0 - 30, 30)
        flash(g, f"{name}_f{k}", front((x, -14.0, 0)), m["flash"], f0)
        blip(g, f"{name}_e{k}", [front((x, -14.0, 0)), front((x, -6.0, 0)), front((gx + 24, -6.0, 0)),
                                 front((gx + 24, 10.0, 0))], 1.0, m["elec"], f0 + 4, 40)
        blip(g, f"{name}_h{k}", [front((x, -14.0, 0)), front((x, -22.0, 0)), front((gx + 48, -22.0, 0)),
                                 front((gx + 48, 10.0, 0))], 1.0, m["hole"], f0 + 4, 55)
    return g
