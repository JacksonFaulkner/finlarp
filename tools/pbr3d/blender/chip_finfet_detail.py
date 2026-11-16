"""Detailed FinFET parts and the FINFET page's sections 1-10 (chip_finfet.py calls sec1..sec10).

A section is a close-up of real transistor structure, not the whole chip: silicon fins standing
out of the STI oxide, the high-k / work-function metal / fill metal gate wrapping three sides,
nitride spacers and caps, merged diamond source/drain epi and tungsten trench contacts. Drawn to
a nanometre scale: NM scene units per nm (fin 7 nm wide, 50 nm tall, 30 nm pitch, as at N7/N5).

Coordinates: Y up, the channel runs along x (source at -x, drain at +x), fins sit side by side
in z. Cut-aways are made while building (no booleans): `cut_mode` sets a plane, and every
`cbox`/`cprism` clips itself to it. Modes:
  "z"     keep z <= z0 (a cut along the channel, seen from +z)
  "x"     keep x <= x0 (a cut across the gate: the classic TEM view of fins, seen from +x)
  "quad"  remove the x > x0, z > z0 quadrant (both faces at once, seen three-quarter)
  "quadl" remove the x < x0, z > z0 quadrant instead (the faces look at -x and +z, toward the light)
A cut across the gate ("x") faces +x, away from the light, so those scenes build it inside a
`turned` group, rotated a quarter turn so the cut face looks at +z (the camera, and the light).
Each part has a priority `pr`; its cut face sits pr * EPS in front of the plane, so a layer
inside another (fin inside high-k inside metal) wins on the cut face instead of z-fighting.

The GAA builders (chip_gaa_detail.py) use the same cut helpers and materials.
"""

import math
import os
import random
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, beat, box, disc, empty, fly, label, mat, pivot, rel, show, tube  # noqa: E402
from sand_zooms import finish, scale_keys, start, stream_of  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import glide_camera, route  # noqa: E402

NM = 10.0  # scene units per nanometre
EPS = 1.6  # cut-face step per priority level

CUT = {"mode": None, "x": 0.0, "z": 0.0}


def cut_mode(mode=None, x=0.0, z=0.0):
    CUT.update(mode=mode, x=x, z=z)


# ---- clipped primitives ----------------------------------------------------------------------


def _box(name, lo, hi, m, parent):
    if any(hi[i] - lo[i] < 0.5 for i in range(3)):
        return None
    return box(name, lo, hi, m, parent)


def cbox(name, lo, hi, m, parent, pr=0):
    """A box clipped to the current cut. Returns the pieces made."""
    mode = CUT["mode"]
    e = EPS * pr
    xc, zc = CUT["x"] + e, CUT["z"] + e
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    if mode is None:
        out = [_box(name, lo, hi, m, parent)]
    elif mode == "z":
        out = [_box(name, (x0, y0, z0), (x1, y1, min(z1, zc)), m, parent)]
    elif mode == "x":
        out = [_box(name, (x0, y0, z0), (min(x1, xc), y1, z1), m, parent)]
    elif mode == "quad":
        out = [
            _box(name + "_a", (x0, y0, z0), (x1, y1, min(z1, zc)), m, parent),
            _box(name + "_b", (x0, y0, max(z0, zc)), (min(x1, xc), y1, z1), m, parent),
        ]
    else:  # quadl: the x < x0, z > z0 quadrant removed; the cut faces look at -x and +z
        xl = CUT["x"] - e
        out = [
            _box(name + "_a", (x0, y0, z0), (x1, y1, min(z1, zc)), m, parent),
            _box(name + "_b", (max(x0, xl), y0, max(z0, zc)), (x1, y1, z1), m, parent),
        ]
    return [o for o in out if o is not None]


def _clip(poly, i, limit, keep_le):
    out = []
    n = len(poly)
    for k in range(n):
        p, q = poly[k], poly[(k + 1) % n]
        pin = p[i] <= limit if keep_le else p[i] >= limit
        qin = q[i] <= limit if keep_le else q[i] >= limit
        if pin:
            out.append(p)
        if pin != qin:
            t = (limit - p[i]) / (q[i] - p[i])
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def prism(name, poly, axis, r0, r1, m, parent):
    """A straight prism: `poly` is a list of (u, y) with u = z for axis "x" (extruded along x from
    r0 to r1) or u = x for axis "z" (extruded along z)."""
    if len(poly) < 3 or r1 - r0 < 0.5:
        return None
    verts = []
    for r in (r0, r1):
        for u, y in poly:
            pt = (r, y, u) if axis == "x" else (u, y, r)
            verts.append(tuple(P(*pt)))
    n = len(poly)
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


def cprism(name, poly, axis, r0, r1, m, parent, pr=0):
    """A prism clipped to the current cut."""
    mode = CUT["mode"]
    e = EPS * pr
    xc, zc = CUT["x"] + e, CUT["z"] + e
    out = []
    if mode is None:
        out.append(prism(name, poly, axis, r0, r1, m, parent))
    elif axis == "x":  # u is z
        if mode == "z":
            out.append(prism(name, _clip(poly, 0, zc, True), axis, r0, r1, m, parent))
        elif mode == "x":
            out.append(prism(name, poly, axis, r0, min(r1, xc), m, parent))
        elif mode == "quad":
            out.append(prism(name + "_a", _clip(poly, 0, zc, True), axis, r0, r1, m, parent))
            out.append(prism(name + "_b", _clip(poly, 0, zc, False), axis, r0, min(r1, xc), m, parent))
        else:
            out.append(prism(name + "_a", _clip(poly, 0, zc, True), axis, r0, r1, m, parent))
            out.append(prism(name + "_b", _clip(poly, 0, zc, False), axis, max(r0, CUT["x"] - e), r1, m, parent))
    else:  # axis z, u is x
        if mode == "z":
            out.append(prism(name, poly, axis, r0, min(r1, zc), m, parent))
        elif mode == "x":
            out.append(prism(name, _clip(poly, 0, xc, True), axis, r0, r1, m, parent))
        elif mode == "quad":
            out.append(prism(name + "_a", poly, axis, r0, min(r1, zc), m, parent))
            out.append(prism(name + "_b", _clip(poly, 0, xc, True), axis, max(r0, zc), r1, m, parent))
        else:
            out.append(prism(name + "_a", poly, axis, r0, min(r1, zc), m, parent))
            out.append(prism(name + "_b", _clip(poly, 0, CUT["x"] - e, False), axis, max(r0, zc), r1, m, parent))
    return [o for o in out if o is not None]


# ---- materials -------------------------------------------------------------------------------


def mats(m):
    """Chip materials plus the transistor close-up set (shared with the GAA sections)."""
    C.mats(m)
    m["d_si"] = mat("dt_si", (0.74, 0.77, 0.84), metal=0.2, rough=0.35)
    m["d_sub"] = mat("dt_sub", (0.52, 0.55, 0.63), metal=0.1, rough=0.5)
    m["d_sti"] = mat("dt_sti", (0.93, 0.86, 0.70), rough=0.8)
    m["d_hk"] = mat("dt_hk", (1.0, 0.88, 0.20), emit=(1.0, 0.85, 0.2), strength=0.6, rough=0.4)
    m["d_wfm"] = mat("dt_wfm", (0.86, 0.46, 0.20), metal=0.3, rough=0.4)
    m["d_fill"] = mat("dt_fill", (0.36, 0.38, 0.44), metal=0.5, rough=0.45)
    m["d_nit"] = mat("dt_nitride", (0.32, 0.62, 0.56), rough=0.5)
    m["d_nepi"] = mat("dt_nepi", (0.26, 0.44, 0.95), rough=0.45)
    m["d_pepi"] = mat("dt_pepi", (0.95, 0.42, 0.55), rough=0.45)
    m["d_w"] = mat("dt_w", (0.70, 0.72, 0.78), metal=0.9, rough=0.25)
    m["d_sige"] = mat("dt_sige", (0.60, 0.40, 0.80), rough=0.55)
    m["d_poly"] = mat("dt_poly", (0.66, 0.56, 0.40), rough=0.6)
    m["d_pts"] = mat("dt_pts", (0.34, 0.26, 0.52), rough=0.5)
    m["d_leak"] = mat("dt_leak", (1.0, 0.36, 0.26), emit=(1.0, 0.32, 0.22), strength=0.8)
    m["d_chan"] = mat("dt_chan", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.2)
    m["d_hot"] = mat("dt_hot", (1.0, 0.70, 0.30), emit=(1.0, 0.62, 0.22), strength=2.5)
    m["d_mask"] = mat("dt_mask", (0.86, 0.80, 0.62), rough=0.5)
    m["d_spacer"] = mat("dt_spacer", (0.40, 0.80, 0.70), rough=0.45)
    m["d_floor"] = mat("dt_floor", (0.24, 0.26, 0.31), rough=0.85)
    m["d_wafer"] = mat("dt_wafer", (0.66, 0.70, 0.78), metal=0.6, rough=0.22)
    m["d_good"] = mat("dt_good", (0.36, 0.72, 0.52), metal=0.3, rough=0.35)
    m["d_bad"] = mat("dt_bad", (0.85, 0.30, 0.26), metal=0.2, rough=0.4)
    m["d_n7"] = mat("dt_n7", (0.50, 0.56, 0.70), metal=0.5, rough=0.3)
    m["d_n5"] = mat("dt_n5", (0.38, 0.55, 0.92), metal=0.5, rough=0.3)
    m["d_n3"] = mat("dt_n3", (0.35, 0.82, 0.85), metal=0.5, rough=0.3)
    m["d_gold"] = mat("dt_gold", (0.95, 0.74, 0.32), metal=0.9, rough=0.25)
    m["d_cu"] = mat("dt_cu", (0.88, 0.52, 0.30), metal=0.85, rough=0.3)
    m["d_cell"] = mat("dt_cell", (0.30, 0.32, 0.40), rough=0.7)
    m["d_hl5"] = mat("dt_hl5", (1.0, 0.70, 0.30), emit=(1.0, 0.62, 0.22), strength=0.7)
    m["d_hlbox"] = mat("dt_hlbox", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.16)
    m["d_hl3"] = mat("dt_hl3", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=0.7)


# ---- the FinFET ------------------------------------------------------------------------------

FW, FH, FP = 70.0, 500.0, 300.0  # fin width 7 nm, height 50 nm above the oxide, pitch 30 nm
GL, GP, SP = 180.0, 510.0, 60.0  # gate length 18 nm, gate pitch 51 nm, spacer 6 nm
HK, WF = 22.0, 35.0  # high-k ~2 nm (drawn a little thick), work-function metal ~3.5 nm
GH, CAP = 260.0, 80.0  # gate metal above the fin top, nitride cap
FIN_BOT, SUB_BOT = -300.0, -520.0  # the fin's foot in the oxide, the substrate's bottom
EPI_TOP = 640.0


def fin_poly(zc, fw, fh, taper=0.0, y0=FIN_BOT):
    """A fin's cross-section in (z, y): `taper` widens the foot and narrows the top."""
    wb, wt = fw * (1 + taper), fw * (1 - 0.4 * taper)
    return [(zc - wb / 2, y0), (zc + wb / 2, y0), (zc + wt / 2, fh), (zc - wt / 2, fh)]


def _wrap_poly(zc, fw, fh, t, taper):
    """The layer `t` thick over a fin's top and both sidewalls, down to the oxide (y = 0)."""
    wb, wt = fw * (1 + taper), fw * (1 - 0.4 * taper)
    w0 = wb + (wt - wb) * (0 - FIN_BOT) / (fh - FIN_BOT)
    return [(zc - w0 / 2 - t, 0.0), (zc + w0 / 2 + t, 0.0), (zc + wt / 2 + t, fh + t), (zc - wt / 2 - t, fh + t)]


def sd_spans(gates, gl, sp, gp):
    """The source/drain gaps between gates, plus a half gap past each end gate."""
    gs = sorted(gates)
    half = (gp - gl - 2 * sp) / 2
    spans = [(gs[0] - gl / 2 - sp - half, gs[0] - gl / 2 - sp)]
    for a, b in zip(gs, gs[1:]):
        spans.append((a + gl / 2 + sp, b - gl / 2 - sp))
    spans.append((gs[-1] + gl / 2 + sp, gs[-1] + gl / 2 + sp + half))
    return spans


def finfet(parent, m, name, n=3, fp=FP, fw=FW, fh=FH, gates=(-GP, 0.0, GP), gl=GL, sp=SP, gp=GP,
           parts=("sub", "sti", "fins", "gate", "spacer", "epi", "contact"), taper=0.0, pmos=False,
           dz=0.0, gh=GH):
    """A FinFET row: `n` fins along x under the `gates`, clipped to the current cut. Returns a dict
    of group empties (sub, sti, fins, hk, wfm, fill, cap, spacer, epi, contact) and the extents."""
    g = empty(name, parent)
    zs = [dz + (k - (n - 1) / 2) * fp for k in range(n)]
    z0, z1 = zs[0] - fp / 2 - 40, zs[-1] + fp / 2 + 40
    spans = sd_spans(gates, gl, sp, gp)
    xa, xb = spans[0][0], spans[-1][1]
    grp = {}

    def group(key_):
        if key_ not in grp:
            grp[key_] = empty(f"{name}_{key_}", g)
        return grp[key_]

    if "sub" in parts:
        cbox(f"{name}_sub", (xa, SUB_BOT, z0), (xb, FIN_BOT, z1), m["d_sub"], group("sub"), 1)
    if "sti" in parts:
        cbox(f"{name}_sti", (xa, FIN_BOT, z0), (xb, 0.0, z1), m["d_sti"], group("sti"), 1)
    if "fins" in parts:
        for k, zc in enumerate(zs):
            if "epi" in parts:  # the fin is recessed in the source/drain, the epi grown on its stub
                cprism(f"{name}_fin{k}", fin_poly(zc, fw, 20.0, taper), "x", xa - 2, xb + 2, m["d_si"], group("fins"), 6)
                for i, gx in enumerate(gates):
                    cprism(f"{name}_fin{k}_{i}", fin_poly(zc, fw, fh, taper), "x", gx - gl / 2 - sp, gx + gl / 2 + sp,
                           m["d_si"], group("fins"), 6)
            else:
                cprism(f"{name}_fin{k}", fin_poly(zc, fw, fh, taper), "x", xa - 2, xb + 2, m["d_si"], group("fins"), 6)
    top = fh + gh
    if "gate" in parts:
        for i, gx in enumerate(gates):
            x0, x1 = gx - gl / 2, gx + gl / 2
            cbox(f"{name}_fill{i}", (x0, 0.0, z0), (x1, top, z1), m["d_fill"], group("fill"), 1)
            cbox(f"{name}_wfs{i}", (x0 + 2, 0.0, z0 + 2), (x1 - 2, HK + WF, z1 - 2), m["d_wfm"], group("wfm"), 2)
            cbox(f"{name}_hks{i}", (x0 + 3, 0.0, z0 + 3), (x1 - 3, HK, z1 - 3), m["d_hk"], group("hk"), 3)
            for k, zc in enumerate(zs):
                cprism(f"{name}_wf{i}_{k}", _wrap_poly(zc, fw, fh, HK + WF, taper), "x", x0, x1, m["d_wfm"],
                       group("wfm"), 2)
                cprism(f"{name}_hk{i}_{k}", _wrap_poly(zc, fw, fh, HK, taper), "x", x0, x1, m["d_hk"],
                       group("hk"), 3)
            cbox(f"{name}_cap{i}", (x0, top, z0), (x1, top + CAP, z1), m["d_nit"], group("cap"), 1)
    if "spacer" in parts:
        for i, gx in enumerate(gates):
            for s in (-1, 1):
                a, b = sorted((gx + s * gl / 2, gx + s * (gl / 2 + sp)))
                cbox(f"{name}_sp{i}{s:+d}", (a, 0.0, z0), (b, top + CAP, z1), m["d_nit"], group("spacer"), 1)
    if "epi" in parts:
        em = m["d_pepi"] if pmos else m["d_nepi"]
        for j, (a, b) in enumerate(spans):
            for k, zc in enumerate(zs):
                poly = [(zc - fw / 2 - 12, 10.0), (zc + fw / 2 + 12, 10.0), (zc + 0.62 * fp, 0.55 * EPI_TOP),
                        (zc + fw * 0.9, EPI_TOP), (zc - fw * 0.9, EPI_TOP), (zc - 0.62 * fp, 0.55 * EPI_TOP)]
                cprism(f"{name}_epi{j}_{k}", poly, "x", a, b, em, group("epi"), 4)
    if "contact" in parts:
        for j, (a, b) in enumerate(spans):
            cbox(f"{name}_ct{j}", (a + 25, EPI_TOP - 40, zs[0] - fp * 0.4), (b - 25, top + CAP, zs[-1] + fp * 0.4),
                 m["d_w"], group("contact"), 2)
    grp["_ext"] = (xa, xb, z0, z1, zs)
    grp["_g"] = g
    return grp


def sub_glow(parent, m, name, zs, x0, x1, mat_, fw=FW, y0=FIN_BOT + 40, y1=-20.0, taper=0.0):
    """A glowing band in each fin's foot (in the oxide, below the gate's reach), on the cut."""
    g = empty(name, parent)
    for k, zc in enumerate(zs):
        cprism(f"{name}{k}", fin_poly(zc, fw + 8, y1, taper, y0), "x", x0, x1, mat_, g, 8)
    return g


def turned(parent, name):
    """A group for an "x" cut, turned a quarter turn about y once built (see `turn`): build
    point (x, y, z) shows at (-z, y, x), so the cut face at x = 0 looks at +z."""
    return empty(name, parent)


def turn(g):
    g.rotation_euler = (0.0, 0.0, -math.pi / 2)
    return g


# ---- scene helpers ---------------------------------------------------------------------------


def scene(name, beats):
    m, root = start(name, beats, page="chip")
    mats(m)
    cut_mode(None)
    return m, root


def save(name):
    cut_mode(None)
    finish(name, page="chip")


def pose(t, dist, yaw, pitch):
    return (t, dist, yaw, pitch)


def wafer(parent, m, name, at, r, good_frac, seed, die=120.0):
    """A 300 mm wafer (drawn `r` across) with its die grid; `good_frac` of the dies green."""
    g = empty(name, parent)
    x, y, z = at
    disc(f"{name}_disc", (x, y, z), r, 24.0, m["d_wafer"], g, verts=96)
    rng = random.Random(seed)
    cells = []
    n = int(r // die) + 1
    for i in range(-n, n):
        for j in range(-n, n):
            cx, cz = x + (i + 0.5) * die, z + (j + 0.5) * die
            if math.hypot(abs(cx - x) + die / 2, abs(cz - z) + die / 2) < r - 12:
                cells.append((cx, cz))
    bad = set(rng.sample(range(len(cells)), round(len(cells) * (1 - good_frac))))
    for k, (cx, cz) in enumerate(cells):
        mt = m["d_bad"] if k in bad else m["d_good"]
        box(f"{name}_d{k}", (cx - die / 2 + 7, y + 12, cz - die / 2 + 7), (cx + die / 2 - 7, y + 20, cz + die / 2 - 7), mt, g)
    return g, len(cells), len(cells) - len(bad)


# ---- FINFET sections ---------------------------------------------------------------------------

ONE = {"gates": (0.0,), "gp": 900.0}  # one transistor: source, one gate, drain
GATE_TOP = FH + GH + CAP


def sec1():
    """1, what happens: fins out of the oxide; the gate wraps three sides; a whole transistor."""
    name = "finfet_sec1"
    m, root = scene(name, 3)
    # beat 0: bare fins standing out of the STI oxide
    b0 = empty("b0", root)
    p = finfet(b0, m, "bare", parts=("sub", "sti", "fins"), **ONE)
    zs = p["_ext"][4]
    label("silicon fin", (-250.0, FH, zs[2]), b0, beat(0))
    label("STI oxide", (-450.0, -40.0, zs[2] + 180), b0, beat(0))
    label("fin pitch ~30 nm", (-300.0, FH, zs[1]), b0, beat(0))
    show(b0, beat(0))
    # beat 1: the gate stack on, cut across the gate (x = 0), turned to face the camera
    cut_mode("x", x=0.0)
    b1 = turned(root, "b1")
    finfet(b1, m, "wrap", parts=("sub", "sti", "fins", "gate", "spacer"), **ONE)
    label("high-k (yellow)", (0.0, FH + HK / 2, zs[2]), b1, beat(1))
    label("work-function metal", (0.0, FH + HK + WF / 2, zs[0]), b1, beat(1))
    label("metal gate: top + 2 sides", (0.0, FH + GH - 80, zs[1] + 150), b1, beat(1))
    label("fin foot in the oxide", (0.0, -160.0, zs[0]), b1, beat(1))
    turn(b1)
    show(b1, beat(1))
    # beat 2: the whole transistor, cut along the middle fin and across the gate
    cut_mode("quadl", x=0.0, z=0.0)
    b2 = empty("b2", root)
    finfet(b2, m, "whole", **ONE)
    label("source epi (merged)", (-300.0, EPI_TOP - 60, 0.0), b2, beat(2))
    label("drain epi", (300.0, EPI_TOP - 60, zs[2] + 120), b2, beat(2))
    label("gate over 3 fins", (0.0, GATE_TOP, zs[0]), b2, beat(2))
    label("trench contact", (-300.0, GATE_TOP, zs[0]), b2, beat(2))
    show(b2, beat(2))
    glide_camera(root, [
        pose((0.0, 20.0, 0.0), 3200.0, -0.65, 0.45),
        pose((0.0, 170.0, 0.0), 3000.0, 0.16, 0.12),
        pose((0.0, 160.0, 0.0), 3600.0, -0.70, 0.40),
    ], glide=0.15)
    save(name)


def sec2():
    """2, the fin under the gate: dimensions, the layers of the gate, the ungated foot."""
    name = "finfet_sec2"
    m, root = scene(name, 3)
    cut_mode("x", x=0.0)
    g = turned(root, "cut")
    p = finfet(g, m, "cut", parts=("sub", "sti", "fins", "gate", "spacer"), **ONE)
    zs = p["_ext"][4]
    pts = sub_glow(g, m, "pts", zs, -450.0, 450.0, m["d_pts"], y0=FIN_BOT + 10, y1=FIN_BOT + 110)
    show(pts, beat(2))
    leak = sub_glow(g, m, "leak", zs, -450.0, 450.0, m["d_leak"], y0=FIN_BOT + 120, y1=-25.0)
    show(leak, beat(2))
    chan = empty("chan", g)
    for k, zc in enumerate(zs):
        cprism(f"ch{k}", fin_poly(zc, FW + 6, FH - 8, 0.0, 6.0), "x", -GL / 2, GL / 2, m["d_chan"], chan, 8)
    show(chan, beat(2))
    zc = zs[1]
    label("Hfin ~50 nm", (0.0, FH * 0.5, zc - FW / 2), g, beat(0))
    label("Wfin ~7 nm", (0.0, FH, zc), g, beat(0))
    label("fin pitch ~30 nm", (0.0, FH * 0.3, (zs[1] + zs[2]) / 2), g, beat(0))
    label("high-k ~1-2 nm", (0.0, FH + HK / 2, zc), g, beat(1))
    label("work-function metal", (0.0, FH + HK + WF / 2, zc + FW), g, beat(1))
    label("fill metal", (0.0, FH + GH - 70, zc - 160), g, beat(1))
    label("channel: gated 3 sides", (0.0, FH * 0.6, zs[0]), g, beat(2))
    label("sub-fin: gate can't reach", (0.0, -130.0, zc), g, beat(2))
    label("punch-through stop doping", (0.0, FIN_BOT + 60, zs[2]), g, beat(2))
    turn(g)
    glide_camera(root, [
        pose((0.0, 250.0, 0.0), 2500.0, 0.16, 0.10),
        pose((0.0, 380.0, 0.0), 1850.0, 0.14, 0.08),
        pose((0.0, 120.0, 0.0), 2700.0, 0.16, 0.10),
    ])
    save(name)


HIST = [  # node, gate pitch nm, fin pitch nm (drawn), beat
    ("N16", 90.0, 48.0, 0),
    ("N5", 51.0, 28.0, 1),
    ("N3", 45.0, 26.0, 2),
]
HS = 0.4  # sec3 draws the rows at 0.4x the close-up scale, so four N16 gates fit


def sec3():
    """3, node history: the same FinFET row at the N16, N5 and N3 gate pitches, one scale."""
    name = "finfet_sec3"
    m, root = scene(name, 3)
    cut_mode("z", z=0.0)
    for node, gp, fp, b in HIST:
        grp = empty(f"row_{node}", root)
        inner = empty(f"rowk_{node}", grp)
        gates = tuple((k - 1.5) * gp * NM for k in range(4))
        finfet(inner, m, node, n=3, fp=fp * NM, gates=gates, gl=gp * NM * 0.36, sp=gp * NM * 0.12, gp=gp * NM,
               dz=-fp * NM)
        y = GATE_TOP + 60
        box(f"pitch_{node}", (gates[1], y, -30), (gates[2], y + 30, 0), m["d_hot"], inner)
        for gx in gates[1:3]:
            box(f"tick_{node}{gx:.0f}", (gx - 15, y - 90, -30), (gx + 15, y + 90, 0), m["d_hot"], inner)
        inner.scale = (HS, HS, HS)
        show(grp, beat(b))
    y = (GATE_TOP + 90) * HS
    label("TSMC N16: gate pitch 90 nm", (-90 * NM * HS * 0.5, y, 0.0), root, beat(0))
    label("Intel 22 nm: first FinFET, 2011", (-90 * NM * HS * 1.5, FH * HS, -48 * NM * HS), root, beat(0))
    label("N5: gate pitch 51 nm", (-51 * NM * HS * 0.5, y, 0.0), root, beat(1))
    label("N7: 57 nm (est)", (-51 * NM * HS * 1.5, FH * HS, -28 * NM * HS), root, beat(1))
    label("N3: gate pitch 45 nm", (-45 * NM * HS * 0.5, y, 0.0), root, beat(2))
    label("same scale, 3 rows", (-45 * NM * HS * 1.5, FH * HS, -26 * NM * HS), root, beat(2))
    t = (0.0, 80.0, -150.0)
    glide_camera(root, [pose(t, 2700.0, 0.40, 0.55)] * 3)
    save(name)


def mini_cell(parent, m, name, cx, cz, s):
    """One logic cell seen from above, `s` across: a cell plate, two gates, two n fins and two p
    fins with their epi. Built about (cx, cz)."""
    g = empty(name, parent)
    h = s / 2
    box(f"{name}_pl", (cx - h + 3, 0, cz - h + 3), (cx + h - 3, 6, cz + h - 3), m["d_cell"], g)
    for k, fz in enumerate((-0.30, -0.16, 0.16, 0.30)):
        z = cz + fz * s
        box(f"{name}_f{k}", (cx - 0.42 * s, 6, z - 0.025 * s), (cx + 0.42 * s, 0.10 * s + 6, z + 0.025 * s), m["d_si"], g)
    for k, fz in enumerate((-0.23, 0.23)):
        mt = m["d_nepi"] if fz < 0 else m["d_pepi"]
        for j, fx in enumerate((-0.33, 0.0, 0.33)):
            x = cx + fx * s
            box(f"{name}_e{k}{j}", (x - 0.06 * s, 6, cz + fz * s - 0.12 * s), (x + 0.06 * s, 0.13 * s + 6, cz + fz * s + 0.12 * s),
                mt, g)
    for k, fx in enumerate((-0.165, 0.165)):
        x = cx + fx * s
        box(f"{name}_g{k}", (x - 0.04 * s, 6, cz - 0.42 * s), (x + 0.04 * s, 0.18 * s + 6, cz + 0.42 * s), m["d_fill"], g)
    return g


def sec4():
    """4, by the numbers: one fixed window filled with logic cells at N7, N5 and N3 density."""
    name = "finfet_sec4"
    m, root = scene(name, 3)
    w = 1800.0
    box("floor", (-w / 2 - 140, -30, -w / 2 - 140), (w / 2 + 140, 0, w / 2 + 140), m["d_floor"], root)
    for i, (x0, z0, x1, z1) in enumerate(((-w / 2 - 20, -w / 2 - 20, w / 2 + 20, -w / 2),
                                         (-w / 2 - 20, w / 2, w / 2 + 20, w / 2 + 20),
                                         (-w / 2 - 20, -w / 2, -w / 2, w / 2),
                                         (w / 2, -w / 2, w / 2 + 20, w / 2))):
        box(f"frame{i}", (x0, 0, z0), (x1, 40, z1), m["d_hot"], root)
    for b, (k, node) in enumerate(((4, "N7"), (5, "N5"), (6, "N3"))):
        grp = empty(f"cells_{node}", root)
        s = w / k
        for i in range(k):
            for j in range(k):
                mini_cell(grp, m, f"c{node}_{i}_{j}", -w / 2 + (i + 0.5) * s, -w / 2 + (j + 0.5) * s, s)
        show(grp, beat(b))
    edge = (w / 2 + 20, 40.0, -w / 2 + 120)
    label("N7: ~91 MTr/mm2 (est)", edge, root, beat(0))
    label("one logic cell", (-w / 2 + w / 8, 120.0, -w / 2 + w / 8), root, beat(0))
    label("N5: ~138 MTr/mm2 (A15 SEM)", edge, root, beat(1))
    label("N3E: ~1.6x N5 (TSMC claim)", edge, root, beat(2))
    label("same window, more cells", (-w / 2, 40.0, w / 2), root, beat(2))
    t = (0.0, 0.0, 0.0)
    glide_camera(root, [pose(t, 3600.0, 0.0, 1.05)] * 3)
    save(name)


def flex_cell(parent, m, name, x0, x1, nf):
    """A standard cell along x from x0 to x1: `nf` n fins at the bottom (z < 0) and `nf` p fins at
    the top, gates across, epi between, the cell height set by the fin count."""
    g = empty(name, parent)
    fp = 300.0
    hz = (nf + 1.4) * fp  # cell height (along z) grows with the fin count
    box(f"{name}_pl", (x0 + 4, -10, -hz), (x1 - 4, 0, hz), m["d_cell"], g)
    box(f"{name}_rail_t", (x0, 0, hz - 60), (x1, 40, hz), m["d_cu"], g)
    box(f"{name}_rail_b", (x0, 0, -hz), (x1, 40, -hz + 60), m["d_cu"], g)
    gates = [x0 + (k + 0.5) * (x1 - x0) / 3 for k in range(3)]
    for side, mt in ((-1, m["d_nepi"]), (1, m["d_pepi"])):
        zcs = [side * (0.7 * fp + (k + 0.5) * fp * 0.9) for k in range(nf)]
        for k, zc in enumerate(zcs):
            box(f"{name}_f{side}{k}", (x0 + 30, 0, zc - 35), (x1 - 30, 110, zc + 35), m["d_si"], g)
        za, zb = min(zcs) - 70, max(zcs) + 70
        for j in range(len(gates) - 1):
            xa, xb = gates[j] + 110, gates[j + 1] - 110
            box(f"{name}_e{side}{j}", (xa, 0, za), (xb, 150, zb), mt, g)
    for k, gx in enumerate(gates):
        box(f"{name}_g{k}", (gx - 55, 0, -hz + 70), (gx + 55, 190, hz - 70), m["d_fill"], g)
    return g, hz


def finflex_scene(name="finfet_sec5"):
    """5, FinFlex: a 3-2, a 2-2 and a 2-1 block, each two cells side by side (top view)."""
    m, root = scene(name, 3)
    combos = [((3, 2), "3-2"), ((2, 2), "2-2"), ((2, 1), "2-1")]
    for b, ((na, nb), tag) in enumerate(combos):
        grp = empty(f"blk{tag}", root)
        flex_cell(grp, m, f"a{tag}", -1500.0, -50.0, na)
        flex_cell(grp, m, f"b{tag}", 50.0, 1500.0, nb)
        show(grp, beat(b))
    label("3-fin cell: most drive", (-1500.0, 40.0, (3 + 1.4) * 300), root, beat(0))
    label("2-fin cell: the base", (50.0, 40.0, (2 + 1.4) * 300), root, beat(0))
    label("2-2: balanced", (-1500.0, 40.0, (2 + 1.4) * 300), root, beat(1))
    label("n fins, blue epi", (-1050.0, 150.0, -500.0), root, beat(1))
    label("p fins, pink epi", (-1050.0, 150.0, 500.0), root, beat(1))
    label("1-fin cell: low power, short", (50.0, 40.0, (1 + 1.4) * 300), root, beat(2))
    label("gate", (-1500.0 + 1450 / 6, 190.0, 0.0), root, beat(2))
    label("power rail", (900.0, 40.0, -(1 + 1.4) * 300 + 30), root, beat(2))
    t = (0.0, 0.0, 0.0)
    glide_camera(root, [pose(t, 6400.0, 0.0, 1.12)] * 3)
    save(name)


MIX = [  # quarter: (7 nm, 5 nm, 3 nm) % of TSMC wafer revenue, 2025
    ("Q1 25", 15, 36, 22),
    ("Q2 25", 14, 36, 24),
    ("Q3 25", 14, 37, 23),
    ("Q4 25", 14, 35, 28),
]


def sec6():
    """6, TSMC wafer revenue by node in 2025: four quarterly stacks of wafers, 7/5/3 nm."""
    name = "finfet_sec6"
    m, root = scene(name, 3)
    u = 13.0  # height per percentage point
    box("floor", (-1150, -30, -320), (1150, 0, 320), m["d_floor"], root)
    for i, (q, n7, n5, n3) in enumerate(MIX):
        x = -780.0 + i * 520.0
        box(f"guide{i}", (x - 12, 0, -230), (x + 12, 100 * u, -206), m["d_cell"], root)
        box(f"guide_top{i}", (x - 120, 100 * u - 8, -230), (x + 120, 100 * u, -206), m["d_cell"], root)
        y = 0.0
        for node, pct, mt in (("n7", n7, m["d_n7"]), ("n5", n5, m["d_n5"]), ("n3", n3, m["d_n3"])):
            seg = empty(f"seg{i}{node}", root)
            k = 0
            while k * 2 < pct:
                h = min(2, pct - 2 * k) * u
                disc(f"w{i}{node}{k}", (x, y + h / 2, 0.0), 170.0, h - 3.0, mt, seg, verts=32)
                y += h
                k += 1
        hi = empty(f"hi5_{i}", root)
        disc(f"glow5_{i}", (x, n7 * u + n5 * u / 2, 0.0), 176.0, n5 * u - 2, m["d_hl5"], hi, verts=32)
        show(hi, beat(1))
        hi3 = empty(f"hi3_{i}", root)
        disc(f"glow3_{i}", (x, (n7 + n5) * u + n3 * u / 2, 0.0), 176.0, n3 * u - 2, m["d_hl3"], hi3, verts=32)
        show(hi3, beat(2))
    x4 = -780.0 + 3 * 520.0
    x1 = -780.0
    label("Q4: 77% at 7 nm and below", (x4, 77 * u, 0.0), root, beat(0))
    label("7 nm: 14%", (x4 + 170, 7 * u, 0.0), root, beat(0))
    label("5 nm: 35%", (x4 + 170, (14 + 17) * u, 0.0), root, beat(0))
    label("3 nm: 28%", (x4 + 170, (49 + 14) * u, 0.0), root, beat(0))
    label("5 nm: 35-37% every quarter", (-780.0 + 520.0, (14 + 18) * u, 170.0), root, beat(1))
    label("Q1 25: 3 nm 22%", (x1, (15 + 36 + 11) * u, 170.0), root, beat(2))
    label("Q4 25: 3 nm 28%", (x4, (14 + 35 + 14) * u, 170.0), root, beat(2))
    label("100%", (x1 - 120, 100 * u, -218.0), root, beat(0) + beat(1))
    t = (0.0, 600.0, 0.0)
    glide_camera(root, [pose(t, 3500.0, 0.0, 0.18)] * 3)
    save(name)


def limits_scene(name="finfet_sec7"):
    """7, fin limits: taller thinner fins taper and vary; leakage and tight gaps; nanosheets."""
    import chip_gaa_detail as G
    m, root = scene(name, 3)
    cut_mode("x", x=0.0)
    parts = ("sub", "sti", "fins", "gate", "spacer")
    # beat 0: a normal pair of fins beside an over-stretched pair (taller, thinner, tapered)
    b0 = turned(root, "b0")
    finfet(b0, m, "norm", n=2, dz=-420.0, parts=parts, **ONE)
    finfet(b0, m, "tall", n=2, fw=50.0, fh=760.0, taper=0.55, dz=420.0, parts=parts, gh=160.0, **ONE)
    label("today's fin", (0.0, FH, -420.0 - FP / 2), b0, beat(0))
    label("taller, thinner: tapers, bends", (0.0, 760.0, 420.0 + FP / 2), b0, beat(0))
    turn(b0)
    show(b0, beat(0))
    # beat 1: a tight row: leakage at the foot, little room for the gate metal between fins
    b1 = turned(root, "b1")
    p = finfet(b1, m, "tight", n=3, fp=220.0, parts=parts, **ONE)
    sub_glow(b1, m, "leak", p["_ext"][4], -450.0, 450.0, m["d_leak"], y0=FIN_BOT + 30, y1=-25.0)
    label("sub-fin leakage", (0.0, -150.0, 0.0), b1, beat(1))
    label("gap: room for the gate?", (0.0, FH - 60, 110.0), b1, beat(1))
    turn(b1)
    show(b1, beat(1))
    # beat 2: the answer: a FinFET fin beside a stack of three nanosheets, both cut across the gate
    b2 = turned(root, "b2")
    finfet(b2, m, "one", n=1, dz=-420.0, parts=parts, **ONE)
    G.gaa(b2, m, "ns", w=300.0, dz=330.0, gates=(0.0,), gp=640.0, parts=("sub", "sti", "mesa", "sheets", "spacer", "gate"))
    label("fin: gate on 3 sides", (0.0, FH, -420.0), b2, beat(2))
    label("nanosheets: gate on 4 sides", (0.0, 450.0, 330.0), b2, beat(2))
    turn(b2)
    show(b2, beat(2))
    glide_camera(root, [
        pose((0.0, 200.0, 0.0), 3300.0, 0.16, 0.10),
        pose((0.0, 160.0, 0.0), 2600.0, 0.16, 0.10),
        pose((0.0, 160.0, 0.0), 2800.0, 0.16, 0.10),
    ], glide=0.15)
    save(name)


def saqp(parent, m, name, fp=FP, n=4):
    """Fin patterning mid-flow: spacer lines (left on the sidewalls of the mandrels, which are
    still there) over the hard mask, the fins etched into the silicon below them."""
    g = empty(name, parent)
    zs = [(k - (n - 1) / 2) * fp for k in range(n)]
    xa, xb = -450.0, 450.0
    cbox(f"{name}_sub", (xa, SUB_BOT, zs[0] - fp), (xb, FIN_BOT, zs[-1] + fp), m["d_sub"], g, 1)
    for k, zc in enumerate(zs):
        cprism(f"{name}_fin{k}", fin_poly(zc, FW, FH - 120), "x", xa, xb, m["d_si"], g, 6)
        cbox(f"{name}_hm{k}", (xa, FH - 120, zc - FW / 2), (xb, FH - 40, zc + FW / 2), m["d_nit"], g, 5)
        cbox(f"{name}_spc{k}", (xa, FH - 40, zc - FW / 2), (xb, FH + 140, zc + FW / 2), m["d_spacer"], g, 5)
    for k in range(0, n, 2):
        zc = (zs[k] + zs[k + 1]) / 2
        cbox(f"{name}_man{k}", (xa, FH - 40, zc - fp / 2 + FW / 2 + 4), (xb, FH + 110, zc + fp / 2 - FW / 2 - 4), m["d_poly"],
             g, 4)
    return g, zs


def sec8():
    """8, who makes it: a long FinFET row; Intel's tapered 22 nm-style fins; SAQP patterning."""
    name = "finfet_sec8"
    m, root = scene(name, 3)
    cut_mode("quadl", x=0.0, z=0.0)
    b0 = empty("b0", root)
    finfet(b0, m, "row", gates=(-2 * GP, -GP, 0.0, GP, 2 * GP))
    label("TSMC: N16 to N3", (-2 * GP, GATE_TOP, -FP), b0, beat(0))
    label("Samsung: 14 nm onward", (GP, GATE_TOP, FP), b0, beat(0))
    show(b0, beat(0))
    cut_mode("x", x=0.0)
    b1 = turned(root, "b1")
    finfet(b1, m, "intel", n=3, fw=90.0, fh=380.0, taper=0.9, parts=("sub", "sti", "fins", "gate", "spacer"), **ONE)
    label("Intel 22 nm: tapered fins", (0.0, 300.0, 0.0), b1, beat(1))
    label("Intel: 22 nm to Intel 3", (0.0, 380.0 + GH * 0.6, -FP), b1, beat(1))
    turn(b1)
    show(b1, beat(1))
    b2 = turned(root, "b2")
    _, zs = saqp(b2, m, "saqp")
    label("mandrel: printed by ASML", (0.0, FH + 110, (zs[0] + zs[1]) / 2), b2, beat(2))
    label("spacers: AMAT, Lam, TEL", (0.0, FH + 140, zs[3]), b2, beat(2))
    label("fin etch: Lam, TEL, AMAT", (0.0, FH * 0.4, zs[2]), b2, beat(2))
    turn(b2)
    show(b2, beat(2))
    glide_camera(root, [
        pose((0.0, 120.0, 0.0), 4900.0, -0.62, 0.42),
        pose((0.0, 140.0, 0.0), 2500.0, 0.16, 0.10),
        pose((0.0, 140.0, 0.0), 2600.0, 0.16, 0.12),
    ], glide=0.15)
    save(name)


def sec9():
    """9, chokepoints: no room between fins, the wafer cost, the estimated pitches."""
    name = "finfet_sec9"
    m, root = scene(name, 3)
    cut_mode("x", x=0.0)
    b0 = turned(root, "b0")
    p = finfet(b0, m, "tight", n=2, fp=260.0, parts=("sub", "sti", "fins", "gate", "spacer"), **ONE)
    zs = p["_ext"][4]
    label("fins: little room left", (0.0, FH, zs[0]), b0, beat(0))
    label("whole gate stack in this gap", (0.0, FH * 0.7, 0.0), b0, beat(0))
    turn(b0)
    show(b0, beat(0))
    cut_mode(None)
    b1 = empty("b1", root)
    wafer(b1, m, "waf", (0.0, 0.0, 0.0), 760.0, 0.85, 7)
    label("cost per wafer: up every node", (-760.0, 20.0, 0.0), b1, beat(1))
    label("TSMC prices: not public", (0.0, 20.0, 760.0), b1, beat(1))
    show(b1, beat(1))
    cut_mode("z", z=0.0)
    b2 = empty("b2", root)
    inner = empty("b2k", b2)
    gates = tuple((k - 1.5) * 51 * NM for k in range(4))
    finfet(inner, m, "n5", n=3, fp=28 * NM, gates=gates, gl=51 * NM * 0.36, sp=51 * NM * 0.12, gp=51 * NM, dz=-28 * NM)
    y = GATE_TOP + 60
    box("pitch_bar", (gates[1], y, -30), (gates[2], y + 30, 0), m["d_hot"], inner)
    for gx in gates[1:3]:
        box(f"tick{gx:.0f}", (gx - 15, y - 90, -30), (gx + 15, y + 90, 0), m["d_hot"], inner)
    inner.scale = (HS, HS, HS)
    label("N5: 51 nm (A15 SEM)", (0.0, (y + 30) * HS, 0.0), b2, beat(2))
    label("N7: 57 nm (WikiChip est)", (gates[0] * HS, FH * HS, -28 * NM * HS * 2), b2, beat(2))
    show(b2, beat(2))
    glide_camera(root, [
        pose((0.0, 160.0, 0.0), 2600.0, 0.16, 0.10),
        pose((0.0, 0.0, 0.0), 3100.0, 0.0, 0.95),
        pose((0.0, 120.0, -150.0), 2300.0, 0.40, 0.55),
    ], glide=0.15)
    save(name)


def sec10():
    """10, sources: the finished transistor row, the camera turning slowly round it."""
    name = "finfet_sec10"
    m, root = scene(name, 3)
    cut_mode("quadl", x=0.0, z=0.0)
    finfet(root, m, "row")
    label("Intel 22 nm tri-gate [1]", (-GP / 2, FH, 0.0), root, beat(0))
    label("TSMC 16FF+ [2]", (GP / 2, EPI_TOP, FP), root, beat(0))
    label("SAQP fins [3]", (0.0, FH, FP), root, beat(1))
    label("N7/N5 pitches [4], N3 [5]", (-GP, GATE_TOP, -FP), root, beat(1))
    label("FinFlex [6], Samsung [7]", (GP, GATE_TOP, -FP), root, beat(2))
    label("TSMC revenue mix [8]", (-GP / 2, EPI_TOP, 0.0), root, beat(2))
    t = (0.0, 100.0, 0.0)
    glide_camera(root, [pose(t, 3900.0, -0.45, 0.40), pose(t, 3800.0, -0.75, 0.34), pose(t, 3900.0, -1.05, 0.30)],
                 glide=0.6)
    save(name)


def sec5():
    finflex_scene()


def sec7():
    limits_scene()


SECTIONS = [sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9, sec10]


# ---- overview and zoom-ins -------------------------------------------------------------------


def ride(parent, name, pts, n, size, m, b, u0=0.05, u1=0.7, life=100):
    """`n` beads that each travel the polyline `pts` (in `parent`'s coordinates) over `life`
    frames, launched one after another between fractions u0 and u1 of beat `b`."""
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, m, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, len(pts) * 3))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


OV_S = 0.4  # the detailed device drawn into the whole chip at this scale
OV_AT = (C.NMOS_X, 0.0, 0.0)


def placed(parent, name, s=OV_S, at=OV_AT):
    """A group to switch with show() and, inside it, the device's frame: moved to `at` and
    scaled by `s`, so a nanometre-scale device sits in the NMOS spot of the whole chip."""
    outer = empty(name, parent)
    inner = empty(name + "_k", outer)
    inner.location = P(*at)
    inner.scale = (s, s, s)
    return outer, inner


def chip_rest(root, m):
    """The whole chip around the NMOS spot: silicon (always on), the PMOS, wiring and bumps."""
    C.silicon(root, m)
    rest = empty("chip_rest", root)
    C.transistor(rest, m, C.PMOS_X, False)
    C.wiring(rest, m)
    C.bumps(rest, m)
    return rest


def planar(parent, m, name, gp=900.0):
    """A planar NMOS on the chip's own silicon (its top at y = 0): implanted source and drain
    flush with the surface, the high-k / metal gate lying flat on the channel, spacers, contacts."""
    g = empty(name, parent)
    z0, z1 = -490.0, 490.0
    y0 = 4.0
    top = y0 + GH + 40
    for s in (-1, 1):
        a, b = sorted((s * GL / 2, s * gp / 2))
        cbox(f"{name}_sd{s:+d}", (a, -170.0, z0), (b, y0, z1), m["d_nepi"], g, 4)
        a, b = sorted((s * GL / 2, s * (GL / 2 + SP)))
        cbox(f"{name}_sp{s:+d}", (a, y0, z0), (b, top + CAP, z1), m["d_nit"], g, 1)
        c = s * (GL / 2 + SP + (gp / 2 - GL / 2 - SP) / 2)
        cbox(f"{name}_ct{s:+d}", (c - 60, y0, z0 + 80), (c + 60, top + CAP, z1 - 80), m["d_w"], g, 2)
    cbox(f"{name}_hk", (-GL / 2, y0, z0), (GL / 2, y0 + HK, z1), m["d_hk"], g, 3)
    cbox(f"{name}_wf", (-GL / 2, y0 + HK, z0), (GL / 2, y0 + HK + WF, z1), m["d_wfm"], g, 2)
    cbox(f"{name}_fill", (-GL / 2, y0 + HK + WF, z0), (GL / 2, top, z1), m["d_fill"], g, 1)
    cbox(f"{name}_cap", (-GL / 2, top, z0), (GL / 2, top + CAP, z1), m["d_nit"], g, 1)
    cbox(f"{name}_ch", (-GL / 2, -24.0, z0), (GL / 2, y0, z1), m["d_chan"], g, 8)
    return g


def current_path(gl=GL, sp=SP, gp=900.0, y_ch=250.0, z=20.0, top=GATE_TOP):
    """Source contact top, down into the epi, along the channel under the gate, up to the drain
    contact: the path the electrons ride."""
    c = GL / 2 + SP + (gp / 2 - GL / 2 - SP) / 2
    return [(-c, top, z), (-c, EPI_TOP - 40, z), (-gl / 2 - sp, y_ch, z), (gl / 2 + sp, y_ch, z), (c, EPI_TOP - 40, z),
            (c, top, z)]


def overview():
    """The overview: the whole chip; in on a planar NMOS; fins rise; the gate wraps them; the
    channel on with current riding through; back out to the whole chip."""
    m, root = scene("finfet", 6)
    rest = chip_rest(root, m)
    show(rest, [(0, F(1, 0.25)), (F(5, 0), F(6, 0))])
    cut_mode("z", z=0.0)
    o, k = placed(root, "dev_whole")
    finfet(k, m, "w", parts=("fins", "gate", "spacer", "epi", "contact"), **ONE)
    hl = empty("hl", k)
    cbox("hl_box", (-480.0, -60.0, -520.0), (480.0, GATE_TOP + 40, 30.0), m["d_hlbox"], hl, 9)
    show(hl, [(0, F(1, 0))])
    show(o, [(0, F(1, 0)), (F(5, 0), F(6, 0))])
    label("FinFET (the NMOS)", (0.0, GATE_TOP + 40, 0.0), k, [(0, F(1, 0))])
    label("gate low: channel off", (0.0, GATE_TOP + 40, 0.0), k, [(F(5, 0.1), F(6, 0))])
    # beat 1: planar
    o1, k1 = placed(root, "planar")
    planar(k1, m, "pl")
    label("planar gate: one face", (0.0, GH, 0.0), k1, beat(1))
    label("flat channel (cyan)", (-GL / 2, -12.0, 0.0), k1, beat(1))
    label("source", (-320.0, -80.0, 0.0), k1, beat(1))
    label("drain", (320.0, -80.0, 0.0), k1, beat(1))
    show(o1, beat(1))
    # beat 2: the fins rise out of the silicon, then the raised source and drain grow on them
    cut_mode("quadl", x=0.0, z=0.0)
    o2, k2 = placed(root, "rise")
    pv = empty("rise_pv", k2)
    p2 = finfet(pv, m, "r", parts=("fins", "epi"), **ONE)
    scale_keys(pv, [(F(2, 0.05), (1, 1, 0.02)), (F(2, 0.5), (1, 1, 1))])
    show(p2["epi"], [(F(2, 0.55), F(3, 0))])
    label("fins stand up", (-300.0, 20.0, FP), k2, [(F(2, 0.3), F(3, 0))])
    label("raised source and drain", (-300.0, EPI_TOP - 60, 0.0), k2, [(F(2, 0.6), F(3, 0))])
    show(o2, beat(2))
    # beat 3: the gate wraps the fins (cut across the gate and along the middle fin)
    o3, k3 = placed(root, "wrap")
    finfet(k3, m, "g", parts=("fins", "gate", "spacer", "epi"), **ONE)
    label("high-k (yellow)", (0.0, FH + HK / 2, FP), k3, beat(3))
    label("gate: top and 2 sides", (0.0, FH + GH - 60, FP / 2), k3, beat(3))
    label("3 fins under 1 gate", (0.0, FH, 0.0), k3, beat(3))
    show(o3, beat(3))
    # beat 4: on: the channel glows and electrons ride from contact to contact
    cut_mode("z", z=0.0)
    o4, k4 = placed(root, "on")
    finfet(k4, m, "n", parts=("fins", "gate", "spacer", "epi", "contact"), **ONE)
    glow = empty("chan", k4)
    cbox("chan_box", (-GL / 2 - SP, 6.0, -FW / 2), (GL / 2 + SP, FH - 6, 14.0), m["d_chan"], glow, 8)
    ride(k4, "e", current_path(), 10, 18.0, m["c_dot_sig"], 4, 0.05, 0.75, 90)
    label("gate high: channel on", (0.0, FH * 0.5, 0.0), k4, beat(4))
    label("source contact", (-300.0, GATE_TOP, 0.0), k4, beat(4))
    label("drain", (300.0, EPI_TOP - 80, 0.0), k4, beat(4))
    show(o4, beat(4))
    cx = C.NMOS_X
    glide_camera(root, [
        C.WHOLE,
        pose((cx, 60.0, -40.0), 950.0, 0.18, 0.14),
        pose((cx, 70.0, -40.0), 1500.0, -0.75, 0.42),
        pose((cx, 90.0, -40.0), 1450.0, -0.75, 0.38),
        pose((cx, 150.0, 0.0), 1100.0, 0.16, 0.10),
        C.WHOLE,
    ])
    save("finfet")


def fin_etch(parent, m, name, stage, n=4):
    """Fin patterning, cut across the fins: "saqp" (spacers on mandrels over the hard mask on
    unetched silicon), "etched" (fins with their hard-mask caps), "reveal" (oxide filled and
    recessed, animated in `stage[1]`'s beat when given as ("reveal", b))."""
    g = empty(name, parent)
    zs = [(k - (n - 1) / 2) * FP for k in range(n)]
    xa, xb = -450.0, 450.0
    za, zb = zs[0] - FP, zs[-1] + FP
    cbox(f"{name}_sub", (xa, SUB_BOT, za), (xb, FIN_BOT, zb), m["d_sub"], g, 1)
    kind = stage if isinstance(stage, str) else stage[0]
    if kind == "saqp":
        cbox(f"{name}_si", (xa, FIN_BOT, za), (xb, FH, zb), m["d_si"], g, 2)
        cbox(f"{name}_hm", (xa, FH, za), (xb, FH + 80, zb), m["d_nit"], g, 3)
        for k, zc in enumerate(zs):
            cbox(f"{name}_spc{k}", (xa, FH + 80, zc - FW / 2), (xb, FH + 260, zc + FW / 2), m["d_spacer"], g, 5)
        for k in range(0, n, 2):
            zc = (zs[k] + zs[k + 1]) / 2
            cbox(f"{name}_man{k}", (xa, FH + 80, zc - FP / 2 + FW / 2 + 3), (xb, FH + 230, zc + FP / 2 - FW / 2 - 3),
                 m["d_poly"], g, 4)
        return g, zs
    for k, zc in enumerate(zs):
        cprism(f"{name}_fin{k}", fin_poly(zc, FW, FH), "x", xa, xb, m["d_si"], g, 6)
        if kind == "etched":
            cbox(f"{name}_cap{k}", (xa, FH, zc - FW / 2), (xb, FH + 80, zc + FW / 2), m["d_nit"], g, 5)
    if kind == "reveal":
        b = stage[1]
        at = (0.0, FIN_BOT, 0.0)
        pv = pivot(f"{name}_sti", at, g)
        cbox(f"{name}_sti_b", rel(at, (xa, FIN_BOT, za)), rel(at, (xb, FH, zb)), m["d_sti"], pv, 1)
        r = (0.0 - FIN_BOT) / (FH - FIN_BOT)
        scale_keys(pv, [(F(b, 0.1), (1, 1, 1)), (F(b, 0.6), (1, 1, r))])
    return g, zs


def zoom_a():
    """a, making fins: SAQP spacers; the fins etched; the oxide filled and recessed."""
    name = "finfet_zoom_a"
    m, root = scene(name, 3)
    cut_mode("x", x=0.0)
    gs = [turned(root, f"b{i}") for i in range(3)]
    _, zs = fin_etch(gs[0], m, "saqp", "saqp")
    fin_etch(gs[1], m, "etch", "etched")
    fin_etch(gs[2], m, "rev", ("reveal", 2))
    label("mandrel (printed)", (0.0, FH + 230, (zs[0] + zs[1]) / 2), gs[0], beat(0))
    label("spacer: becomes a fin", (0.0, FH + 260, zs[3]), gs[0], beat(0))
    label("hard mask", (0.0, FH + 40, zs[2] + 100), gs[0], beat(0))
    label("fin etched in the silicon", (0.0, FH * 0.3, zs[1]), gs[1], beat(1))
    label("hard-mask cap", (0.0, FH + 80, zs[2]), gs[1], beat(1))
    label("trench", (0.0, 0.0, (zs[2] + zs[3]) / 2), gs[1], beat(1))
    label("STI oxide, recessed", (0.0, -40.0, (zs[1] + zs[2]) / 2), gs[2], [(F(2, 0.4), F(3, 0))])
    label("fin top revealed", (0.0, FH, zs[3]), gs[2], [(F(2, 0.5), F(3, 0))])
    for i, g in enumerate(gs):
        turn(g)
        show(g, beat(i))
    t = (0.0, 150.0, 0.0)
    glide_camera(root, [pose(t, 2950.0, 0.16, 0.12)] * 3)
    save(name)


def zoom_b():
    """b, the gate wraps three sides: high-k alone; the full gate; on, with current riding the fin."""
    name = "finfet_zoom_b"
    m, root = scene(name, 3)
    cut_mode("x", x=0.0)
    b0, b1 = turned(root, "b0"), turned(root, "b1")
    p0 = finfet(b0, m, "hk", parts=("sub", "sti", "fins", "gate"), **ONE)
    for key_ in ("wfm", "fill", "cap"):
        show(p0[key_], [])
    finfet(b1, m, "gt", parts=("sub", "sti", "fins", "gate", "spacer"), **ONE)
    zs = p0["_ext"][4]
    label("high-k ~1-2 nm", (0.0, FH + HK / 2, zs[1]), b0, beat(0))
    label("on top and both sidewalls", (0.0, FH * 0.6, zs[2] + FW / 2 + HK / 2), b0, beat(0))
    label("work-function metal", (0.0, FH + HK + WF / 2, zs[1] + FW), b1, beat(1))
    label("fill metal", (0.0, FH + GH - 80, zs[0] - 100), b1, beat(1))
    label("no gate under the fin", (0.0, -150.0, zs[1]), b1, beat(1))
    for i, g in enumerate((b0, b1)):
        turn(g)
        show(g, beat(i))
    cut_mode("z", z=0.0)
    b2 = empty("b2", root)
    finfet(b2, m, "on", parts=("sub", "sti", "fins", "gate", "spacer", "epi", "contact"), **ONE)
    glow = empty("chan", b2)
    cbox("chan_box", (-GL / 2 - SP, 6.0, -FW / 2), (GL / 2 + SP, FH - 6, 14.0), m["d_chan"], glow, 8)
    ride(b2, "e", current_path(), 10, 18.0, m["c_dot_sig"], 2, 0.05, 0.75, 90)
    ride(b2, "lk", [(-GL / 2 - SP - 60, -120.0, 20.0), (GL / 2 + SP + 60, -120.0, 20.0)], 4, 12.0, m["d_leak"], 2, 0.2,
         0.8, 70)
    label("on: channel glows", (0.0, FH * 0.55, 0.0), b2, beat(2))
    label("electrons, contact to contact", (-300.0, GATE_TOP - 60, 0.0), b2, beat(2))
    label("sub-fin leak path", (0.0, -120.0, 0.0), b2, beat(2))
    show(b2, beat(2))
    glide_camera(root, [
        pose((0.0, 300.0, 0.0), 2100.0, 0.16, 0.10),
        pose((0.0, 250.0, 0.0), 2500.0, 0.16, 0.10),
        pose((0.0, 180.0, 0.0), 2700.0, 0.18, 0.12),
    ])
    save(name)


def zoom_c():
    """c, fin count: the same transistor one, two and three fins wide."""
    name = "finfet_zoom_c"
    m, root = scene(name, 3)
    texts = ("1 fin: smallest, least drive", "2 fins: 2x the drive", "3 fins: the fastest cells")
    for i, n in enumerate((1, 2, 3)):
        zc = -(n - 1) / 2 * FP  # cut along the back fin, so the cut across the gate shows every fin
        cut_mode("quadl", x=0.0, z=zc)
        g = empty(f"n{n}", root)
        finfet(g, m, f"f{n}", n=n, **ONE)
        ride(g, f"e{n}", current_path(z=zc + 20), 8, 16.0, m["c_dot_sig"], i, 0.1, 0.75, 90)
        label(texts[i], (0.0, GATE_TOP, zc), g, beat(i))
        if n == 3:
            label("drive ~ fin count", (-300.0, EPI_TOP - 60, zc), g, beat(i))
        show(g, beat(i))
    t = (0.0, 150.0, 0.0)
    glide_camera(root, [pose(t, 3400.0, -0.75, 0.42)] * 3)
    save(name)


def zoom_d():
    finflex_scene("finfet_zoom_d")


def zoom_e():
    limits_scene("finfet_zoom_e")


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}
