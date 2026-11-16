"""Detailed part builders for the FIBER CPO sections (fiber_cpo_sections.py).

A co-packaged-optics switch package, drawn so the parts read: a layered organic substrate on BGA
balls, the switch ASIC (compute tiles, SerDes strips along its edges, bumps under underfill) in the
middle, and eight optical engines around it, two per side. Each engine is a silicon-photonics PIC
(waveguides, ring modulators on the transmit lanes, germanium photodetectors on the receive lanes,
a bus waveguide fed by two laser-input lanes) with the EIC (drivers and TIAs) flip-chipped on its
inner end, short copper traces back to the ASIC's SerDes edge, and a fibre array unit at its outer
edge: fibres laid in a V-groove block under a glass lid. The fibres run over the substrate edge to
a detachable passive connector (MT-style ferrule, two guide pins) seated on the board.

Units mm, Y up, camera on +z. The package is centred on the origin. Every builder takes the
material dict from `materials()`. `CLIP`, when set, trims everything to z <= CLIP (world), so a
section can show the package cut open along one lane (the cut faces are box faces, flush).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from sand_overview import P, ball, box, empty, tube  # noqa: E402
from pbr_kit import mat  # noqa: E402
import fiber_kit as K  # noqa: E402

# ---- layout ------------------------------------------------------------------------------------

SUB = 40.0                 # substrate half-width (x and z)
SUB_Y0, SUB_Y1 = 0.8, 2.8  # substrate bottom and top (BGA balls under it, board top at y = 0)
DIE = 13.0                 # ASIC die half-width
UF_Y1, DIE_Y1 = 3.2, 4.0   # underfill top (= die bottom), die top
OE_R = 24.0                # optical engine centre, distance from the package centre
OE_LAT = (-8.5, 8.5)       # the two engines per side, lateral offsets
PIC_Y0, PIC_Y1 = 3.0, 3.7  # PIC on microbumps (2.8..3.0)
EIC_Y0, EIC_Y1 = 3.85, 4.4
FIB_Y = 3.52               # fibre axis height (sits in the V-grooves, level with the PIC edge)
FIB_R = 0.3
LANES = (-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5)  # fibre / waveguide lanes across an engine
LASER = (-3.5, 3.5)        # laser-input lanes (CW light from the external laser)
TX = (-2.5, -1.5, -0.5)    # transmit lanes: a ring modulator each
RX = (0.5, 1.5, 2.5)       # receive lanes: a germanium photodetector each
# along an engine (local u, outward): PIC -7..7, EIC -6.5..-1.5, FAU 7..12, connector 28..34
CONN_U = (28.0, 34.0)
FERRULE_U = 35.5

CLIP = None  # world z: trim everything in front of it (see module doc)

SIDES = {"+x": 0.0, "-x": math.pi, "+z": -math.pi / 2, "-z": math.pi / 2}


def materials():
    m = K.materials()
    m["pic"] = mat("cpo_pic", (0.36, 0.33, 0.50), metal=0.35, rough=0.3)
    m["eic"] = mat("cpo_eic", (0.10, 0.11, 0.13), metal=0.3, rough=0.35)
    m["wg"] = mat("cpo_wg", (0.70, 0.85, 1.00), emit=(0.55, 0.80, 1.00), strength=0.8)
    m["ring"] = mat("cpo_ring", (0.90, 0.62, 0.28), metal=0.9, rough=0.25)
    m["ge"] = mat("cpo_ge", (0.55, 0.45, 0.20), metal=0.6, rough=0.4)
    m["uf"] = mat("cpo_uf", (0.13, 0.13, 0.14), rough=0.8)
    m["core"] = mat("cpo_core", (0.33, 0.38, 0.24), rough=0.8)
    m["buildup"] = mat("cpo_buildup", (0.55, 0.38, 0.20), rough=0.75)
    m["mask"] = mat("cpo_mask", (0.17, 0.15, 0.12), rough=0.55)
    m["solder"] = mat("cpo_solder", (0.78, 0.79, 0.82), metal=0.9, rough=0.25)
    m["tile"] = mat("cpo_tile", (0.24, 0.27, 0.36), metal=0.4, rough=0.3)
    m["serdes"] = mat("cpo_serdes", (0.85, 0.62, 0.30), metal=0.85, rough=0.3)
    m["vg"] = mat("cpo_vg", (0.50, 0.52, 0.58), metal=0.5, rough=0.3)
    m["lid"] = mat("cpo_lid", (0.75, 0.90, 1.00), rough=0.05, alpha=0.35)
    m["plastic"] = mat("cpo_plastic", (0.16, 0.17, 0.19), rough=0.6)
    m["ferrule"] = mat("cpo_ferrule", (0.38, 0.40, 0.43), rough=0.5)
    m["aqua"] = mat("cpo_aqua", (0.25, 0.70, 0.75), rough=0.5)
    m["cw"] = mat("cpo_cw", (1.0, 0.18, 0.12), emit=(1.0, 0.18, 0.12), strength=6.0)
    m["hl"] = mat("cpo_hl", (0.30, 0.90, 1.00), emit=(0.30, 0.90, 1.00), strength=2.0, alpha=0.18)
    m["heat"] = mat("cpo_heat", (0.95, 0.12, 0.02), emit=(1.0, 0.12, 0.02), strength=2.0, alpha=0.45)
    m["warm"] = mat("cpo_warm", (1.0, 0.30, 0.05), emit=(1.0, 0.28, 0.04), strength=1.0, alpha=0.30)
    m["ring_on"] = mat("cpo_ring_on", (1.0, 0.55, 0.20), emit=(1.0, 0.55, 0.20), strength=6.0)
    m["bad"] = mat("cpo_bad", (1.0, 0.05, 0.03), emit=(1.0, 0.05, 0.03), strength=4.0, alpha=0.7)
    m["plate"] = mat("cpo_plate", (0.70, 0.72, 0.76), metal=0.85, rough=0.3)
    m["cool"] = mat("cpo_cool", (0.25, 0.55, 1.00), emit=(0.25, 0.55, 1.00), strength=2.5, alpha=0.5)
    return m


# ---- clipped primitives ------------------------------------------------------------------------


def bx(name, lo, hi, m, parent, clip=None):
    """A box trimmed to z <= clip (world z for root parts; pass None for none). None if all cut."""
    clip = CLIP if clip == "world" else clip
    if clip is not None:
        if lo[2] >= clip:
            return None
        hi = (hi[0], hi[1], min(hi[2], clip))
    return box(name, lo, hi, m, parent)


def prism(name, profile, u0, u1, m, parent):
    """A solid with the (v, y) polygon `profile` (counter-clockwise seen from +u), run from u0 to u1
    along x. Built in its parent's local frame."""
    me = bpy.data.meshes.new(name)
    n = len(profile)
    verts = [P(u0, y, v) for v, y in profile] + [P(u1, y, v) for v, y in profile]
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    me.materials.append(m)
    o.parent = parent
    return o


def ring(name, c, r, m, parent, minor=0.08):
    """A ring modulator: a flat torus lying on the chip (axis = Y)."""
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=minor, major_segments=20,
                                     minor_segments=6, location=P(*c))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    o.parent = parent
    return o


# ---- the package -------------------------------------------------------------------------------


def board(m, parent, x0=-75.0, x1=75.0, z0=-75.0, z1=75.0):
    return bx("board", (x0, -3.0, z0), (x1, 0.0, z1), m["board"], parent, "world")


def substrate(m, parent, half=SUB):
    """Layered organic substrate: solder mask, build-up with copper planes, glass-epoxy core. The
    side faces show the stack. BGA balls (two rings) under it, on the board."""
    g = empty("substrate", parent)
    layers = [(0.80, 0.86, "mask"), (0.86, 1.02, "buildup"), (1.02, 1.10, "copper"),
              (1.10, 1.27, "buildup"), (1.27, 1.35, "copper"), (1.35, 2.25, "core"),
              (2.25, 2.33, "copper"), (2.33, 2.47, "buildup"), (2.47, 2.55, "copper"),
              (2.55, 2.74, "buildup"), (2.74, 2.80, "mask")]
    for i, (y0, y1, k) in enumerate(layers):
        bx(f"sub_{i}_{k}", (-half, y0, -half), (half, y1, half), m[k], g, "world")
    # plated vias half-sunk in the front face, so the cut face shows them
    for i, x in enumerate((-30.0, -18.0, -6.0, 6.0, 18.0, 30.0)):
        if CLIP is None or half <= CLIP:
            tube(f"sub_via{i}", (x, 1.05, half), (x, 2.55, half), 0.35, m["copper"], g, 8)
    balls = empty("bga", parent)
    pitch = 4.0
    k = int(half // pitch)
    for i in range(-k, k + 1):
        for j in range(-k, k + 1):
            if max(abs(i), abs(j)) < k - 1:
                continue
            x, z = i * pitch, j * pitch
            if CLIP is not None and z > CLIP:
                continue
            ball(f"bga_{i}_{j}", (x, 0.42, z), 0.45, m["solder"], balls, 8)
    return g, balls


def asic(m, parent):
    """The switch ASIC: die on C4 bumps under underfill; compute tiles on top, SerDes strips along
    each edge facing an engine row."""
    g = empty("asic", parent)
    bx("asic_uf", (-DIE - 0.6, SUB_Y1, -DIE - 0.6), (DIE + 0.6, UF_Y1, DIE + 0.6), m["uf"], g, "world")
    bx("asic_die", (-DIE, UF_Y1, -DIE), (DIE, DIE_Y1, DIE), m["die"], g, "world")
    t, n = 2.0 * (DIE - 2.0) / 5, 5
    for i in range(n):
        for j in range(n):
            x0 = -(DIE - 2.0) + i * t
            z0 = -(DIE - 2.0) + j * t
            bx(f"tile_{i}_{j}", (x0 + 0.25, DIE_Y1, z0 + 0.25), (x0 + t - 0.25, DIE_Y1 + 0.04, z0 + t - 0.25),
               m["tile"], g, "world")
    w = 1.3
    e = DIE - 0.3
    bx("serdes_px", (e - w, DIE_Y1, -DIE + 1.5), (e, DIE_Y1 + 0.05, DIE - 1.5), m["serdes"], g, "world")
    bx("serdes_nx", (-e, DIE_Y1, -DIE + 1.5), (-e + w, DIE_Y1 + 0.05, DIE - 1.5), m["serdes"], g, "world")
    bx("serdes_pz", (-DIE + 1.5, DIE_Y1, e - w), (DIE - 1.5, DIE_Y1 + 0.05, e), m["serdes"], g, "world")
    bx("serdes_nz", (-DIE + 1.5, DIE_Y1, -e), (DIE - 1.5, DIE_Y1 + 0.05, -e + w), m["serdes"], g, "world")
    return g


def oe_frame(side, lat):
    """(location, angle) of the engine on `side` at lateral offset `lat`."""
    phi = SIDES[side]
    x = OE_R * math.cos(phi) + lat * math.sin(phi)
    z = lat * math.cos(phi) - OE_R * math.sin(phi)
    return (x, 0.0, z), phi


def oe_world(side, lat, u, y, v):
    """Engine-local (u, y, v) to world (x, y, z)."""
    (cx, _, cz), phi = oe_frame(side, lat)
    return (cx + u * math.cos(phi) + v * math.sin(phi), y, cz + v * math.cos(phi) - u * math.sin(phi))


def _vrange(side, lat):
    """The local v range left by CLIP for an engine, or None if CLIP removes it."""
    if CLIP is None:
        return (-99.0, 99.0)
    (cx, _, cz), phi = oe_frame(side, lat)
    c = round(math.cos(phi))
    if c == 1:
        return (-99.0, CLIP - cz) if CLIP - cz > -5 else None
    if c == -1:
        return (cz - CLIP, 99.0) if cz - CLIP < 5 else None
    # +z / -z engines run along z: kept whole if behind the clip, dropped if not
    zmax = max(oe_world(side, lat, u, 0, v)[2] for u in (-12, 40) for v in (-5, 5))
    return (-99.0, 99.0) if zmax <= CLIP else None


def optical_engine(m, parent, side, lat, conn=True, open_conn=False):
    """One optical engine (PIC + EIC + traces + fibre array + fibres + connector), built in its own
    frame (u outward from the ASIC, v across, y up) under a group placed and turned onto `side`.
    Returns a dict: g (placed group), chips, traces, fau, fibres, conn, conn_front (the connector's
    front half, a group a section can hide to open it), or None if CLIP removes the engine."""
    vr = _vrange(side, lat)
    if vr is None:
        return None
    v0, v1 = vr

    def lb(name, lo, hi, mt, par):
        lo2, hi2 = (lo[0], lo[1], max(lo[2], v0)), (hi[0], hi[1], min(hi[2], v1))
        if lo2[2] >= hi2[2]:
            return None
        return box(name, lo2, hi2, mt, par)

    def inv(v):
        return v0 <= v <= v1

    tag = f"{side}_{lat:+.0f}"
    g = empty(f"oe_{tag}", parent)
    d = {"g": g}
    chips = d["chips"] = empty(f"oe_chips_{tag}", g)
    lb(f"pic_bump_{tag}", (-7.0, SUB_Y1, -4.5), (7.0, PIC_Y0, 4.5), m["uf"], chips)
    lb(f"pic_{tag}", (-7.0, PIC_Y0, -4.5), (7.0, PIC_Y1, 4.5), m["pic"], chips)
    lb(f"eic_bump_{tag}", (-6.5, PIC_Y1, -4.0), (-1.5, EIC_Y0, 4.0), m["uf"], chips)
    lb(f"eic_{tag}", (-6.5, EIC_Y0, -4.0), (-1.5, EIC_Y1, 4.0), m["eic"], chips)
    wy0, wy1 = PIC_Y1, PIC_Y1 + 0.03
    # waveguides: every lane from the PIC's outer edge in toward the EIC
    for v in LANES:
        if inv(v):
            lb(f"wg_{tag}_{v}", (-1.2, wy0, v - 0.07), (7.0, wy1, v + 0.07), m["wg"], chips)
    # the bus: the laser lanes feed a waveguide that runs across under the EIC's edge
    lb(f"bus_{tag}", (-1.2, wy0, -3.57), (-1.0, wy1, 3.57), m["wg"], chips)
    rings = d["rings"] = []
    for i, v in enumerate(TX):
        if inv(v):
            rings.append(ring(f"ring_{tag}_{v}", (1.2 + 1.1 * i, wy1, v + 0.45), 0.35, m["ring"], chips))
    for i, v in enumerate(RX):
        if inv(v):
            lb(f"pd_{tag}_{v}", (1.0 + 0.9 * i, wy0, v - 0.25), (1.8 + 0.9 * i, wy1 + 0.08, v + 0.25), m["ge"], chips)
    traces = d["traces"] = empty(f"oe_traces_{tag}", g)
    for v in LANES:
        if inv(v):
            lb(f"tr_{tag}_{v}", (-12.4, SUB_Y1, v - 0.18), (-5.8, SUB_Y1 + 0.04, v + 0.18), m["copper"], traces)
    # fibre array unit: V-groove block, fibres in the grooves, a glass lid
    fau = d["fau"] = empty(f"oe_fau_{tag}", g)
    lanes_in = [v for v in LANES if inv(v)]
    a, b = max(-4.5, v0), min(4.5, v1)
    prof = [(a, SUB_Y1 + 0.05), (b, SUB_Y1 + 0.05), (b, 3.55)]
    for v in sorted(lanes_in, reverse=True):
        prof += [(v + 0.45, 3.55), (v, 3.1), (v - 0.45, 3.55)]
    prof.append((a, 3.55))
    # counter-clockwise seen from +u: (v, y) with v to the right... check winding by area sign
    area = sum(prof[i][0] * prof[(i + 1) % len(prof)][1] - prof[(i + 1) % len(prof)][0] * prof[i][1]
               for i in range(len(prof)))
    if area < 0:
        prof = prof[::-1]
    prism(f"vgroove_{tag}", prof, 7.0, 12.0, m["vg"], fau)
    lb(f"fau_lid_{tag}", (7.6, 3.55, -4.3), (12.0, 4.05, 4.3), m["lid"], fau)
    fib = d["fibres"] = empty(f"oe_fibres_{tag}", g)
    u_end = FERRULE_U if conn else 20.0
    for v in lanes_in:
        tube(f"fib_{tag}_{v}", (7.0, FIB_Y, v), (u_end, FIB_Y, v), FIB_R, m["glass"], fib, 10)
    # a ribbon jacket over the free run between the array and the connector
    lb(f"ribbon_{tag}", (16.0, FIB_Y - 0.35, -4.0), (CONN_U[0], FIB_Y + 0.35, 4.0), m["cladding"], fib)
    d["conn"] = d["conn_front"] = None
    if conn:
        c = d["conn"] = empty(f"oe_conn_{tag}", g)
        u0, u1 = CONN_U
        back_v1 = 0.0 if open_conn else 4.5
        lb(f"conn_back_{tag}", (u0, 0.0, -4.8), (u1, 5.2, back_v1), m["aqua"], c)
        lb(f"ferrule_back_{tag}", (u1 - 3.0, 2.4, -3.6), (FERRULE_U, 4.6, min(back_v1, 3.6)), m["ferrule"], c)
        pins = []
        for s in (-1, 1):
            v = s * 2.9
            if inv(v):
                pins.append(tube(f"pin_{tag}_{s}", (u1 - 2.0, FIB_Y, v), (FERRULE_U + 1.6, FIB_Y, v), 0.32, m["steel"], c, 10))
        for v in lanes_in:  # the polished fibre ends on the ferrule face
            tube(f"fend_{tag}_{v}", (FERRULE_U, FIB_Y, v), (FERRULE_U + 0.05, FIB_Y, v), 0.32, m["lid"], c, 10)
        if open_conn:
            f = d["conn_front"] = empty(f"oe_conn_front_{tag}", c)
            lb(f"conn_front_{tag}", (u0, 0.0, 0.0), (u1, 5.2, 4.8), m["aqua"], f)
            lb(f"ferrule_front_{tag}", (u1 - 3.0, 2.4, 0.0), (FERRULE_U, 4.6, 3.6), m["ferrule"], f)
            for pn in pins:
                if not pn.name.endswith("_-1"):
                    pn.parent = f
    loc, phi = oe_frame(side, lat)
    g.location = P(*loc)
    g.rotation_euler = (0.0, 0.0, phi)
    d["side"], d["lat"] = side, lat
    return d


def package(m, parent, sides=("+x", "-x", "+z", "-z"), conn=True, open_conn=(), engines=True):
    """The whole package. Returns a dict: sub, bga, asic, oes {(side, lat): engine dict}."""
    out = {}
    out["sub"], out["bga"] = substrate(m, parent)
    out["asic"] = asic(m, parent)
    out["oes"] = {}
    if engines:
        for s in sides:
            for lat in OE_LAT:
                d = optical_engine(m, parent, s, lat, conn=conn, open_conn=(s, lat) in open_conn)
                if d is not None:
                    out["oes"][(s, lat)] = d
    return out


def lit_lanes(m, d, lanes, u0, u1, parent=None, mt="cw"):
    """Glowing cores along `lanes` of engine `d`, from local u0 to u1 (a group under the engine)."""
    g = empty(f"lit_{d['side']}_{d['lat']}_{u0}_{mt}", parent or d["g"])
    for v in lanes:
        tube(f"lit_{d['side']}{d['lat']}_{v}_{u0}", (u0, FIB_Y, v), (u1, FIB_Y, v), FIB_R * 0.55, m[mt], g, 8)
    return g


def mate(m, d, u_panel, panel=True):
    """The mating cable connector clipped onto engine `d`'s connector, and its ribbon cable out to a
    front-panel adapter at local u = `u_panel`. A group under the engine (fly it to plug it in)."""
    tag = f"{d['side']}_{d['lat']:+.0f}"
    g = empty(f"mate_{tag}", d["g"])
    box(f"mate_ferrule_{tag}", (FERRULE_U + 0.05, 2.4, -3.6), (FERRULE_U + 1.6, 4.6, 3.6), m["ferrule"], g)
    box(f"mate_body_{tag}", (FERRULE_U + 1.6, 0.0, -4.8), (FERRULE_U + 8.0, 5.2, 4.8), m["plastic"], g)
    box(f"mate_boot_{tag}", (FERRULE_U + 8.0, 1.8, -4.2), (FERRULE_U + 11.0, 5.0, 4.2), m["plastic"], g)
    box(f"mate_cable_{tag}", (FERRULE_U + 11.0, FIB_Y - 0.45, -4.0), (u_panel, FIB_Y + 0.45, 4.0), m["aqua"], g)
    if panel:
        box(f"mate_adapter_{tag}", (u_panel - 1.0, 0.0, -5.5), (u_panel + 3.0, 7.0, 5.5), m["dark_steel"], g)
    return g


# ---- beads on paths (the motion of fiber_photodiode_detail.wire/run, copied here) ---------------


def wire(name, pts, r, m, parent, verts=8):
    """A segmented wire or fibre through `pts`: a tube per segment, a ball at each joint."""
    from sand_overview import ball as _ball
    g = empty(name, parent)
    for k in range(len(pts) - 1):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, m, g, verts)
        if k:
            _ball(f"{name}_j{k}", pts[k], r, m, g, verts)
    return g


def arch(a, b, h, n=8):
    """Points on an arch from a to b, rising h at the middle (a sine bump in y)."""
    return [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n + h * math.sin(math.pi * k / n),
             a[2] + (b[2] - a[2]) * k / n) for k in range(n + 1)]


def ride(parent, name, pts, n, size, m, b, u0, u1, life):
    """`n` glowing beads that each ride the polyline `pts` (in the parent's frame) over `life` frames,
    launched one after another between fractions u0 and u1 of beat `b`."""
    from sand_overview import F, ball as _ball, fly, show
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        _ball(f"{name}{k}_s", pts[0], size, m, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, len(pts) * 2))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g
