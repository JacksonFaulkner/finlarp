"""Part kit for the PACKAGING tab's SUBSTRATE page (pkg_substrate_*.py).

One organic FC-BGA package substrate, drawn hugely thickened (its ~1.5 mm stack is 62 units tall,
its width 300) and cut open along z = 0, the camera on +z, so the cut face shows the anatomy:

  board        green PCB under it all (mask, FR-4, a copper plane on the cut face)
  BGA          solder balls at coarse board pitch (24) on pads, front row cut in half
  land caps    capacitors on the substrate's underside between the balls (land-side caps)
  bottom stack 6 build-up layers (ABF film + copper), green solder resist under them
  core         glass-fibre/epoxy core with copper foils and plated through-holes (PTH), each a
               copper barrel cut open, plugged with dark resin, with lands on both faces
  top stack    6 more build-up layers; layers 1 and 3 (from the core) are GND / power planes,
               the rest signal layers whose traces run into the board (copper dots on the face)
  microvias    laser vias, tapered cones through each ABF film, stacked on copper capture pads
  C4           fine-pitch (8) solder bumps on pads in solder-resist openings, under a see-through
               underfill, then the interposer, the GPU die and HBM stacks
  stiffener    a metal ring round the substrate's edge (back and sides)

Routes (ROUTES) build the fan-out geometry and give bead paths from the same numbers: each goes
from a C4 bump down microvias to a signal layer, across it, down through a PTH and out to a BGA
ball. Power columns (POWER_X) run straight up from centre balls through the planes.

Close-ups for sections (built at an offset, scaled): c4_joint, bga_joint, via_stack, core_pair,
abf_roll, share_bars, size_squares. A warp chain (warp) bends for the warpage beats.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, ball, cut, empty, key, show, tube, mat  # noqa: E402
import pkg_kit as K  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, join, run, rise, present, frame, camera_path, bead  # noqa: E402,F401

# ---- materials ------------------------------------------------------------------------------


def materials():
    m = {}
    m.update(K.materials())
    m.update(D.materials())
    m.update({
        "abf": mat("sub2_abf", (0.86, 0.74, 0.50), rough=0.6),
        "core": mat("sub2_core", (0.46, 0.36, 0.20), rough=0.75),
        "weave": mat("sub2_weave", (0.58, 0.50, 0.32), rough=0.7),
        "cu": mat("sub2_cu", (0.90, 0.50, 0.25), metal=0.9, rough=0.3),
        "plane": mat("sub2_plane", (0.80, 0.42, 0.20), metal=0.9, rough=0.35),
        "pth": mat("sub2_pth", (1.0, 0.62, 0.32), metal=0.6, rough=0.25, emit=(1.0, 0.55, 0.25), strength=0.6),
        "resin": mat("sub2_resin", (0.10, 0.09, 0.08), rough=0.85),
        "sr": mat("sub2_resist", (0.10, 0.42, 0.24), rough=0.45),
        "uf": mat("sub2_underfill", (0.12, 0.10, 0.10), rough=0.8, alpha=0.35),
        "stiff": mat("sub2_stiffener", (0.62, 0.64, 0.68), metal=0.8, rough=0.35),
        "glass": mat("sub2_glass", (0.55, 0.78, 0.90), metal=0.1, rough=0.08, alpha=0.55),
        "pet": mat("sub2_pet", (0.85, 0.90, 0.95), rough=0.2, alpha=0.5),
        "ip": mat("sub2_interposer", (0.34, 0.38, 0.44), metal=0.5, rough=0.4),
        "pwr": mat("sub2_pwr", (1.0, 0.78, 0.18), emit=(1.0, 0.72, 0.12), strength=5.0),
        "sig": mat("sub2_sig", (0.30, 0.90, 1.0), emit=(0.20, 0.88, 1.0), strength=5.0),
        "plane_lit": mat("sub2_plane_lit", (1.0, 0.70, 0.20), emit=(1.0, 0.62, 0.15), strength=2.0),
        "trace_lit": mat("sub2_trace_lit", (0.30, 0.90, 1.0), emit=(0.20, 0.85, 1.0), strength=2.0),
        "stress": mat("sub2_stress", (1.0, 0.15, 0.10), emit=(1.0, 0.10, 0.06), strength=3.0),
        "bar_a": mat("sub2_bar_a", (0.95, 0.60, 0.25), metal=0.3, rough=0.4),
        "bar_b": mat("sub2_bar_b", (0.45, 0.62, 0.90), metal=0.3, rough=0.4),
    })
    return m


# ---- layout ---------------------------------------------------------------------------------

SX0, SX1, SZ0 = -150.0, 150.0, -150.0  # substrate extents (front cut at z = 0)
UNIT, ABF_T = 3.0, 2.0  # one build-up layer: ABF film then copper
NL = 6  # build-up layers per side
SR_T = 1.2
CORE0 = SR_T + NL * UNIT  # 19.2
CORE1 = CORE0 + 24.0  # 43.2
TOP = CORE1 + NL * UNIT + SR_T  # 62.4
FOIL = 1.0
PLANES = (1, 3)  # build-up layer k (from the core) that are solid planes
C4_R, C4_PITCH, C4_HALF = 2.4, 8.0, 56.0
C4_Y = TOP + C4_R - 0.3
IP_Y = (C4_Y + C4_R - 0.3, C4_Y + C4_R + 7.7)
DIE_Y = (IP_Y[1] + 1.0, IP_Y[1] + 10.0)
BGA_R, BGA_PITCH, BGA_HALF = 5.0, 24.0, 144.0
BOARD_TOP = -2 * BGA_R + 0.6
BGA_Y = BOARD_TOP + BGA_R - 0.3
PTH_R = 4.0

# Fan-out routes: (C4 x, signal layer k from the core, PTH / BGA x). Mirrored at -x.
# Inner bumps take the deeper layers so no trace crosses another route's via.
ROUTES = [(32.0, 0, 72.0), (40.0, 2, 96.0), (48.0, 4, 120.0), (56.0, 5, 144.0)]
POWER_X = (0.0, 16.0)  # power columns (and -x): PTH, planes, vias, C4 (fed from balls at 0 / 24)


def cu_y(side, k):
    """(y0, y1) of copper layer k (0 next to the core) on side +1 (top) or -1 (bottom)."""
    if side > 0:
        b = CORE1 + UNIT * k
        return (b + ABF_T, b + UNIT)
    t = CORE0 - UNIT * k
    return (t - UNIT, t - ABF_T)


def abf_y(side, k):
    if side > 0:
        b = CORE1 + UNIT * k
        return (b, b + ABF_T)
    t = CORE0 - UNIT * k
    return (t - ABF_T, t)


def mid(r):
    return (r[0] + r[1]) / 2


def all_routes():
    return [(s * xc, k, s * xb) for s in (1, -1) for (xc, k, xb) in ROUTES]


def pth_xs():
    xs = {xb for _, _, xb in all_routes()}
    xs |= {s * x for s in (1, -1) for x in POWER_X}
    return sorted(xs)


def cone(name, a, b, ra, rb, m, parent=None, verts=16):
    A, B = P(*a), P(*b)
    d = B - A
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=ra, radius2=rb, depth=d.length, location=(A + B) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    from mathutils import Vector
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.data.materials.append(m)
    o.parent = parent
    return o


def halfcut(o):
    return cut(o, 0.0)


# ---- the cross-section ------------------------------------------------------------------------


def _skip(x, xs, w):
    return any(abs(x - v) < w for v in xs)


def core(m, parent, x0=SX0, x1=SX1, z0=SZ0, name="core"):
    g = empty(name, parent)
    parts = [bx(f"{name}_body", (x0, CORE0 + FOIL, z0), (x1, CORE1 - FOIL, 0.0), m["core"], g)]
    # glass-cloth bundles in the cut face: rows of flat ellipses (here thin bars) and long fibres
    weave = []
    for r, y in enumerate((CORE0 + 7.0, CORE0 + 17.0)):
        weave.append(bx(f"{name}_fib{r}", (x0, y - 0.3, z0), (x1, y + 0.3, -1.7), m["weave"], g))
        off = 3.0 if r % 2 else 0.0
        x = x0 + off
        while x < x1 - 3:
            if not _skip(x + 1.7, pth_xs(), PTH_R + 3.0):
                weave.append(bx(f"{name}_bun{r}_{int(x)}", (x, y - 0.9, -1.6), (x + 3.4, y + 0.9, 0.05), m["weave"], g))
            x += 7.0
    join(weave, f"{name}_weave")
    join(parts, f"{name}_mesh")
    foils = []
    for i, (ya, yb) in enumerate(((CORE0, CORE0 + FOIL), (CORE1 - FOIL, CORE1))):
        foils.append(bx(f"{name}_foil{i}", (x0, ya, z0), (x1, yb, 0.0), m["plane"], g))
    join(foils, f"{name}_foils")
    return g


def pths(m, parent, xs=None, name="pth"):
    """Plated through-holes, each cut in half by the front face: copper barrel, resin plug, lands."""
    g = empty(name, parent)
    cu_parts, plug = [], []
    for i, x in enumerate(xs if xs is not None else pth_xs()):
        cu_parts.append(halfcut(tube(f"{name}_bar{i}", (x, CORE0 - 0.6, 0.0), (x, CORE1 + 0.6, 0.0), PTH_R, m["pth"], g, 24)))
        plug.append(halfcut(tube(f"{name}_plug{i}", (x, CORE0 - 0.05, 0.0), (x, CORE1 + 0.05, 0.0), PTH_R - 1.8, m["resin"], g, 24)))
        for j, y in enumerate((CORE0 - 0.6, CORE1)):
            cu_parts.append(bx(f"{name}_land{i}_{j}", (x - PTH_R - 2.5, y, -6.0), (x + PTH_R + 2.5, y + 0.6, 0.0), m["pth"], g))
    join(cu_parts, f"{name}_cu")
    join(plug, f"{name}_plug")
    return g


def via_stack(m, parent, x, side, k0, k1, name, mt=None, z=0.0, r0=1.0, r1=1.7):
    """Stacked microvias at x from layer k0 to k1 (k0 <= k1) on one side, with capture pads,
    half cut by the front face. Layer -1 means the core land."""
    mt = mt or m["cu"]
    parts = []
    for k in range(max(k0, 0), k1 + 1):
        a = abf_y(side, k)
        inner, outer = (a[0], a[1]) if side > 0 else (a[1], a[0])
        parts.append(halfcut(cone(f"{name}_v{k}", (x, inner, z), (x, outer, z), r0, r1, mt, parent)))
        c = cu_y(side, k)
        parts.append(bx(f"{name}_p{k}", (x - 3.0, c[0], z - 3.0), (x + 3.0, c[1], z), mt, parent))
    return join(parts, f"{name}_mesh")


def buildup(m, parent, side, name, x0=SX0, x1=SX1, z0=SZ0, keep=None):
    """One side's 6 build-up layers: ABF films, copper planes (with antipads), signal traces
    (strips running into the board, copper dots on the cut face). Returns per-layer groups."""
    g = empty(name, parent)
    layers = []
    sig_x = [xc for xc, _, _ in all_routes()] + [xb for _, _, xb in all_routes()]
    for k in range(NL):
        lg = empty(f"{name}_L{k}", g)
        a = abf_y(side, k)
        bx(f"{name}_abf{k}", (x0, a[0], z0), (x1, a[1], 0.0), m["abf"], lg)
        c = cu_y(side, k)
        parts = []
        if k in PLANES:
            # a plane with gaps where signal vias pass
            holes = sorted(v for v in sig_x if x0 < v < x1)
            xa = x0
            for h in holes:
                if h - 4.0 > xa:
                    parts.append(bx(f"{name}_pl{k}_{int(xa)}", (xa, c[0], z0), (h - 4.0, c[1], 0.0), m["plane"], lg))
                xa = max(xa, h + 4.0)
            if xa < x1:
                parts.append(bx(f"{name}_pl{k}_end", (xa, c[0], z0), (x1, c[1], 0.0), m["plane"], lg))
        else:
            x = x0 + 2.0 + (k % 2) * 2.5
            while x < x1 - 2.0:
                if not _skip(x, sig_x + list(pth_xs()), 5.0):
                    parts.append(bx(f"{name}_tr{k}_{int(x * 10)}", (x - 0.8, c[0], z0), (x + 0.8, c[1], 0.0), m["cu"], lg))
                x += 5.0
        if parts:
            join(parts, f"{name}_cu{k}")
        layers.append(lg)
    # solder resist on the outside
    ys = (TOP - SR_T, TOP) if side > 0 else (0.0, SR_T)
    sr = bx(f"{name}_sr", (x0, ys[0], z0), (x1, ys[1], 0.0), m["sr"], g)
    return g, layers, sr


def routes(m, parent, name="rt"):
    """The fan-out geometry: per route, a microvia stack from the outer top layer down to its
    signal layer, a trace across that layer on the cut face, a stack down to the core, a PTH (built
    by pths), the bottom stack and the BGA pad. Returns (group, {route index: bead path})."""
    g = empty(name, parent)
    paths = {}
    lit = empty(f"{name}_lit", g)  # glowing copies of the traces, shown in the signal beats
    for i, (xc, k, xb) in enumerate(all_routes()):
        via_stack(m, g, xc, 1, k, NL - 1, f"{name}{i}_up")
        c = cu_y(1, k)
        xa, xz = sorted((xc, xb))
        bx(f"{name}{i}_tr", (xa - 3.0, c[0], -3.0), (xz + 3.0, c[1], 0.0), m["cu"], g)
        bx(f"{name}{i}_trl", (xa - 3.0, c[0] - 0.05, -3.05), (xz + 3.0, c[1] + 0.05, 0.05), m["trace_lit"], lit)
        via_stack(m, g, xb, 1, 0, k, f"{name}{i}_dn")
        via_stack(m, g, xb, -1, 0, NL - 1, f"{name}{i}_bt")
        zf = 1.2
        paths[i] = [(xc, C4_Y + C4_R, zf), (xc, mid(cu_y(1, k)), zf), (xb, mid(cu_y(1, k)), zf),
                    (xb, CORE1, zf), (xb, CORE0, zf), (xb, SR_T, zf), (xb, BGA_Y, zf)]
    for i, x in enumerate(s * v for s in (1, -1) for v in POWER_X):
        via_stack(m, g, x, 1, 0, NL - 1, f"{name}_pw{i}")
        via_stack(m, g, x, -1, 0, NL - 1, f"{name}_pb{i}")
    return g, paths, lit


def power_path(x, to_c4=None, zf=1.2):
    """A power bead's path: up from the BGA ball nearest column x, along the bottom power plane to
    the column, up its PTH to the top power plane, along it to a C4 bump at to_c4, into the
    interposer."""
    xb = BGA_PITCH * round(x / BGA_PITCH)
    pb = mid(cu_y(-1, PLANES[1]))
    pl = mid(cu_y(1, PLANES[1]))
    xc = x if to_c4 is None else to_c4
    return [(xb, BOARD_TOP - 6.0, zf), (xb, BGA_Y, zf), (xb, pb, zf), (x, pb, zf), (x, CORE0, zf),
            (x, CORE1, zf), (x, pl, zf), (xc, pl, zf), (xc, TOP, zf), (xc, IP_Y[0] + 2.0, zf)]


def c4s(m, parent, half=C4_HALF, pitch=C4_PITCH, rows=13, name="c4"):
    g = empty(name, parent)
    balls, pads = [], []
    n = int(half // pitch)
    for i in range(-n, n + 1):
        x = i * pitch
        for j in range(rows):
            z = -j * pitch
            b = ball(f"{name}_{i}_{j}", (x, C4_Y, z), C4_R, m["solder"], g, 12)
            pads.append(bx(f"{name}_pad{i}_{j}", (x - 2.2, TOP - SR_T, z - 2.2), (x + 2.2, TOP + 0.15, min(z + 2.2, 0.0)), m["cu"], g))
            balls.append(halfcut(b) if j == 0 else b)
    join(balls, f"{name}_balls")
    join(pads, f"{name}_pads")
    return g


def bgas(m, parent, half=BGA_HALF, pitch=BGA_PITCH, rows=7, name="bga"):
    g = empty(name, parent)
    balls, pads = [], []
    n = int(half // pitch)
    for i in range(-n, n + 1):
        x = i * pitch
        for j in range(rows):
            z = -j * pitch
            b = ball(f"{name}_{i}_{j}", (x, BGA_Y, z), BGA_R, m["solder"], g, 14)
            balls.append(halfcut(b) if j == 0 else b)
            for y0, y1 in ((-0.2, 0.6), (BOARD_TOP - 0.6, BOARD_TOP + 0.2)):
                pads.append(bx(f"{name}_pd{i}_{j}_{y0}", (x - 4.5, y0, z - 4.5), (x + 4.5, y1, min(z + 4.5, 0.0)), m["cu"], g))
    join(balls, f"{name}_balls")
    join(pads, f"{name}_pads")
    return g


def land_caps(m, parent, name="lsc"):
    g = empty(name, parent)
    for i, x in enumerate((-36.0, -12.0, 12.0, 36.0)):
        for j, z in enumerate((-12.0, -36.0, -60.0)):
            D.mlcc(m, g, f"{name}{i}{j}", (x, -3.2, z), w=8.0, d=4.0, h=3.2)
    return g


def board(m, parent, name="pcb"):
    g = empty(name, parent)
    bx(f"{name}_mask", (-220.0, BOARD_TOP - 1.0, -220.0), (220.0, BOARD_TOP, 0.0), m["mask"], g)
    bx(f"{name}_fr4", (-220.0, BOARD_TOP - 22.0, -220.0), (220.0, BOARD_TOP - 1.0, 0.0), m["fr4"], g)
    for i, y in enumerate((BOARD_TOP - 5.0, BOARD_TOP - 12.0, BOARD_TOP - 18.0)):
        bx(f"{name}_cu{i}", (-220.0, y - 0.8, -220.0), (220.0, y, 0.0), m["plane"], g)
    return g


def top_parts(m, parent, name="pkg"):
    """Underfill, interposer, GPU die, HBM stacks, stiffener ring."""
    g = empty(name, parent)
    out = {"group": g}
    out["uf"] = bx(f"{name}_uf", (-66.0, TOP, -100.0), (66.0, IP_Y[0], 0.0), m["uf"], g)
    out["ip"] = bx(f"{name}_ip", (-64.0, IP_Y[0], -100.0), (64.0, IP_Y[1], 0.0), m["ip"], g)
    out["die"] = bx(f"{name}_die", (-30.0, DIE_Y[0], -80.0), (30.0, DIE_Y[1], 0.0), m["die"], g)
    for side in (-1, 1):
        lo = (side * 34.0, DIE_Y[0], -40.0)
        hi = (side * 58.0, DIE_Y[1] + 4.0, 0.0)
        K.hbm_stack(f"{name}_hbm{side}", tuple(min(a, b) for a, b in zip(lo, hi)), tuple(max(a, b) for a, b in zip(lo, hi)), m, g)
    ring = []
    for xa, xb in ((SX0, SX0 + 14.0), (SX1 - 14.0, SX1)):
        ring.append(bx(f"{name}_st{xa}", (xa, TOP, SZ0), (xb, TOP + 8.0, 0.0), m["stiff"], g))
    ring.append(bx(f"{name}_stb", (SX0, TOP, SZ0), (SX1, TOP + 8.0, SZ0 + 14.0), m["stiff"], g))
    join(ring, f"{name}_stiff")
    return out


def substrate(m, parent, name="sub"):
    """The substrate alone (no board, balls or top): core, PTHs, build-up both sides, routes."""
    g = empty(name, parent)
    core(m, g, name=f"{name}_core")
    pths(m, g, name=f"{name}_pth")
    top, tl, tsr = buildup(m, g, 1, f"{name}_top")
    bot, bl, bsr = buildup(m, g, -1, f"{name}_bot")
    rg, paths, lit = routes(m, g, f"{name}_rt")
    return {"group": g, "top": top, "top_layers": tl, "bot": bot, "bot_layers": bl,
            "top_sr": tsr, "bot_sr": bsr, "routes": rg, "paths": paths, "lit": lit}


def scene(m, root, top=True, caps=True):
    """The whole cut-open stack. Returns a dict of groups and anchor points."""
    s = {}
    s["board"] = board(m, root)
    s["bga"] = bgas(m, root)
    if caps:
        s["caps"] = land_caps(m, root)
    s["sub"] = substrate(m, root)
    s["c4"] = c4s(m, root)
    if top:
        s["pkg"] = top_parts(m, root)
    s["lit_planes"] = lit_planes(m, root)
    show(s["sub"]["lit"], [])
    show(s["lit_planes"], [])
    return s


def lit_planes(m, parent, name="lp"):
    """Glowing overlays on the two top planes and the core foils, for the power beats."""
    g = empty(name, parent)
    for k in PLANES:
        c = cu_y(1, k)
        bx(f"{name}{k}", (SX0, c[0] - 0.05, -2.0), (SX1, c[1] + 0.05, 0.06), m["plane_lit"], g)
        c = cu_y(-1, k)
        bx(f"{name}b{k}", (SX0, c[0] - 0.05, -2.0), (SX1, c[1] + 0.05, 0.06), m["plane_lit"], g)
    return g


# anchors for tags
A_CORE = (-100.0, mid((CORE0, CORE1)), 0.0)
A_PTH = (-120.0, CORE1 - 4.0, 0.0)
A_TOPBU = (-128.0, mid((CORE1, TOP)), 0.0)
A_BOTBU = (-128.0, mid((0.0, CORE0)), 0.0)
A_C4 = (16.0, C4_Y, 0.0)
A_BGA = (-96.0, BGA_Y, 0.0)
A_IP = (-50.0, IP_Y[1], 0.0)
A_DIE = (0.0, DIE_Y[1], -20.0)
A_SR = (-140.0, TOP, 0.0)
A_CAP = (-12.0, -1.5, -12.0)
A_PLANE = (-84.0, mid(cu_y(1, 3)), 0.0)
A_VIA = (40.0, mid((CORE1, TOP)), 0.0)

# ---- views --------------------------------------------------------------------------------------

V_ALL = frame((0.0, 30.0, -60.0), 340.0, 0.35, 0.40, pad=1.0)
V_FACE = frame((-60.0, 32.0, 0.0), 150.0, 0.12, 0.10)
V_FACE_R = frame((60.0, 32.0, 0.0), 150.0, -0.12, 0.10)
V_C4 = frame((24.0, 64.0, -6.0), 80.0, 0.30, 0.28)
V_BGA = frame((-40.0, 0.0, 0.0), 120.0, 0.25, -0.05)
V_CORE = frame((-100.0, 31.0, 0.0), 80.0, 0.10, 0.06)
V_TOPBU = frame((48.0, 52.0, 0.0), 80.0, -0.10, 0.10)


# ---- warp ---------------------------------------------------------------------------------------

N_BEND = 20
STRAIN = {}  # warp group name -> its two strain-ball empties


def show_strain(g, intervals):
    for e in STRAIN[g.name]:
        show(e, intervals)


def warp(m, parent, name="warp", half=150.0, c4=True):
    """The substrate as N_BEND hinged segments (resist, build-up, core, build-up, resist) with C4
    on top and BGA below, sitting at y = 0..TOP. bend(...) keys a bow. Returns (group, pivots)."""
    g = empty(name, parent)
    w = 2 * half / N_BEND
    pivots, prev = [], g
    for k in range(N_BEND):
        loc = P(-half, 0.0, 0.0) if k == 0 else P(w, 0.0, 0.0)
        piv = empty(f"{name}_h{k}", prev, loc)
        for tag, (ya, yb), mt in (("srb", (0.0, SR_T), "sr"), ("bub", (SR_T, CORE0), "abf"),
                                   ("core", (CORE0, CORE1), "core"), ("but", (CORE1, TOP - SR_T), "abf"),
                                   ("srt", (TOP - SR_T, TOP), "sr")):
            bx(f"{name}_{tag}{k}", (0.0, ya, -120.0), (w, yb, 0.0), m[mt], piv)
        for j, y in enumerate((mid((SR_T, CORE0)), mid((CORE1, TOP)))):
            bx(f"{name}_cu{k}_{j}", (0.0, y - 0.6, -120.0), (w, y + 0.6, 0.05), m["plane"], piv)
        if c4 and abs(-half + (k + 0.5) * w) < 60.0:
            ball(f"{name}_c4_{k}", (w / 2, C4_Y, -0.1), C4_R, m["solder"], piv, 10)
        ball(f"{name}_bga_{k}", (w / 2, -BGA_R + 0.3, -0.1), BGA_R, m["solder"], piv, 10)
        pivots.append(piv)
        prev = piv
    # red strained-joint balls on the end links, hidden until show_strain(); built here, before any
    # group is presented or keyed, so their parent inverse is clean and they ride the links
    strain = []
    for j, k in enumerate((0, N_BEND - 1)):
        e = ball(f"{name}_strain{j}_b", (w / 2, -BGA_R + 0.3, 0.5), BGA_R + 0.8, m["stress"], pivots[k], 14)
        show(e, [])  # a ball scales about its own centre, so show() on it directly is safe
        strain.append(e)
    STRAIN[g.name] = strain
    return g, pivots


def bend(pivots, keys):
    """keys: list of (frame, a) where a is the end slope in radians (+ smile: ends up)."""
    n = len(pivots)
    for f, a in keys:
        for k, piv in enumerate(pivots):
            th = a if k == 0 else -2 * a / (n - 1)
            key(piv, f, "rotation_euler", (0.0, th, 0.0))


# ---- close-ups (for sections) ---------------------------------------------------------------------


def c4_joint(m, parent, o, s=1.0, name="cj"):
    """One C4 joint cut in half, large: substrate build-up (ABF, copper, microvia), resist opening,
    copper pad, solder bump, interposer pad and UBM above, underfill around. o = bottom centre."""
    g = empty(name, parent)
    x0, y0, z0 = o

    def B(n, lo, hi, mt):
        return bx(f"{name}_{n}", (x0 + s * lo[0], y0 + s * lo[1], z0 + s * lo[2]), (x0 + s * hi[0], y0 + s * hi[1], z0 + s * hi[2]), m[mt], g)

    B("abf0", (-60, 0, -40), (60, 10, 0), "abf")
    B("cu0", (-60, 10, -40), (60, 14, 0), "plane")
    B("abf1", (-60, 14, -40), (60, 24, 0), "abf")
    B("pad", (-16, 24, -16), (16, 28, 0), "cu")
    B("sr_l", (-60, 24, -40), (-20, 32, 0), "sr")
    B("sr_r", (20, 24, -40), (60, 32, 0), "sr")
    B("sr_b", (-20, 24, -40), (20, 32, -20), "sr")
    halfcut(cone(f"{name}_mv", (x0, y0 + 14 * s, z0), (x0, y0 + 24 * s, z0), 4 * s, 8 * s, m["cu"], g))
    halfcut(ball(f"{name}_bump", (x0, y0 + 42 * s, z0), 18 * s, m["solder"], g, 28))
    B("ubm", (-14, 58, -14), (14, 62, 0), "gold")
    B("ippad", (-16, 62, -16), (16, 66, 0), "cu")
    B("ip", (-60, 66, -40), (60, 84, 0), "ip")
    B("uf_l", (-60, 32, -40), (-22, 66, -1), "uf")
    B("uf_r", (22, 32, -40), (60, 66, -1), "uf")
    return g


def bga_joint(m, parent, o, s=1.0, name="bj"):
    g = empty(name, parent)
    x0, y0, z0 = o

    def B(n, lo, hi, mt):
        return bx(f"{name}_{n}", (x0 + s * lo[0], y0 + s * lo[1], z0 + s * lo[2]), (x0 + s * hi[0], y0 + s * hi[1], z0 + s * hi[2]), m[mt], g)

    B("fr4", (-70, -30, -40), (70, -4, 0), "fr4")
    B("bpad", (-22, -4, -22), (22, 0, 0), "cu")
    B("bmask_l", (-70, -4, -40), (-26, 2, 0), "mask")
    B("bmask_r", (26, -4, -40), (70, 2, 0), "mask")
    halfcut(ball(f"{name}_ball", (x0, y0 + 22 * s, z0), 26 * s, m["solder"], g, 32))
    B("spad", (-22, 44, -22), (22, 48, 0), "cu")
    B("ssr_l", (-70, 44, -40), (-26, 50, 0), "sr")
    B("ssr_r", (26, 44, -40), (70, 50, 0), "sr")
    B("sabf", (-70, 50, -40), (70, 62, 0), "abf")
    B("score", (-70, 62, -40), (70, 80, 0), "core")
    return g


def via_column(m, parent, o, s=1.0, staggered=False, name="vc", n=4):
    """Four build-up layers with microvias stacked on one another, or staggered step by step."""
    g = empty(name, parent)
    x0, y0, z0 = o
    for k in range(n):
        ya = y0 + s * 14 * k
        bx(f"{name}_abf{k}", (x0 - 40 * s, ya, z0 - 30 * s), (x0 + 40 * s, ya + 10 * s, z0), m["abf"], g)
        bx(f"{name}_cu{k}", (x0 - 40 * s, ya + 10 * s, z0 - 30 * s), (x0 - 16 * s, ya + 14 * s, z0), m["plane"], g)
        bx(f"{name}_cr{k}", (x0 + 22 * s, ya + 10 * s, z0 - 30 * s), (x0 + 40 * s, ya + 14 * s, z0), m["plane"], g)
        dx = (k * 8 * s - 12 * s) if staggered else 0.0
        halfcut(cone(f"{name}_v{k}", (x0 + dx, ya, z0), (x0 + dx, ya + 10 * s, z0), 3 * s, 6 * s, m["cu"], g, 20))
        bx(f"{name}_p{k}", (x0 + dx - 9 * s, ya + 10 * s, z0 - 9 * s), (x0 + dx + 9 * s, ya + 14 * s, z0), m["cu"], g)
    return g


def core_pair(m, parent, o, s=1.0, name="cp"):
    """An organic core (left, fibres, wide drilled PTH) beside a glass core (right, thin
    through-glass vias at fine pitch)."""
    g = empty(name, parent)
    x0, y0, z0 = o
    org = empty(f"{name}_org", g)
    bx(f"{name}_ob", (x0 - 110 * s, y0, z0 - 40 * s), (x0 - 10 * s, y0 + 30 * s, z0), m["core"], org)
    for r in range(3):
        bx(f"{name}_of{r}", (x0 - 110 * s, y0 + (7 + 8 * r) * s, z0 - 40 * s), (x0 - 10 * s, y0 + (8 + 8 * r) * s, z0 + 0.05), m["weave"], org)
    for i, x in enumerate((-85, -35)):
        halfcut(tube(f"{name}_op{i}", (x0 + x * s, y0, z0), (x0 + x * s, y0 + 30 * s, z0), 9 * s, m["cu"], org, 20))
        halfcut(tube(f"{name}_oq{i}", (x0 + x * s, y0 - 0.1, z0), (x0 + x * s, y0 + 30 * s + 0.1, z0), 6 * s, m["resin"], org, 20))
    gl = empty(f"{name}_gl", g)
    bx(f"{name}_gb", (x0 + 10 * s, y0, z0 - 40 * s), (x0 + 110 * s, y0 + 30 * s, z0), m["glass"], gl)
    for i in range(7):
        x = 22 + 14 * i
        halfcut(tube(f"{name}_tgv{i}", (x0 + x * s, y0, z0), (x0 + x * s, y0 + 30 * s, z0), 2.5 * s, m["cu"], gl, 16))
    return g, org, gl


def abf_roll(m, parent, o, s=1.0, name="roll"):
    """A roll of ABF on its PET carrier, the film unrolling flat toward the camera: PET base,
    ABF resin, cover film."""
    g = empty(name, parent)
    x0, y0, z0 = o
    r = 20 * s
    rl = tube(f"{name}_core", (x0 - 60 * s, y0 + r, z0 - 60 * s), (x0 + 60 * s, y0 + r, z0 - 60 * s), r, m["abf"], g, 32)
    rl.name = f"{name}_roll"
    tube(f"{name}_spool", (x0 - 66 * s, y0 + r, z0 - 60 * s), (x0 + 66 * s, y0 + r, z0 - 60 * s), 5 * s, m["plastic"], g, 16)
    bx(f"{name}_pet", (x0 - 60 * s, y0, z0 - 60 * s), (x0 + 60 * s, y0 + 1.5 * s, z0), m["pet"], g)
    bx(f"{name}_abf", (x0 - 60 * s, y0 + 1.5 * s, z0 - 60 * s), (x0 + 60 * s, y0 + 5 * s, z0 - 6 * s), m["abf"], g)
    bx(f"{name}_cover", (x0 - 60 * s, y0 + 5 * s, z0 - 60 * s), (x0 + 60 * s, y0 + 6 * s, z0 - 14 * s), m["pet"], g)
    return g


def share_bars(m, parent, o, s=1.0, name="bars"):
    """FC-BGA share estimate bars: Ibiden 35, Shinko 18, Unimicron 14, AT&S 10, Nan Ya 5."""
    g = empty(name, parent)
    x0, y0, z0 = o
    out = {}
    for i, (who, pct) in enumerate((("Ibiden", 35), ("Shinko", 18), ("Unimicron", 14), ("AT&S", 10), ("Nan Ya", 5))):
        x = x0 + (i - 2) * 34 * s
        h = pct * 3.0 * s
        bx(f"{name}_{i}", (x - 12 * s, y0, z0 - 24 * s), (x + 12 * s, y0 + h, z0), m["bar_a" if i == 0 else "bar_b"], g)
        out[who] = (x, y0 + h, -12 * s + z0)
    bx(f"{name}_base", (x0 - 90 * s, y0 - 3 * s, z0 - 34 * s), (x0 + 90 * s, y0, z0 + 6 * s), m["dark"], g)
    return g, out


def size_squares(m, parent, o, s=1.0, name="sq"):
    """Substrate footprints to scale (mm), largest at the bottom, stepped up like a pyramid:
    120, 100, 77.5, 55 mm square. Returns {mm: corner anchor}."""
    g = empty(name, parent)
    x0, y0, z0 = o
    out = {}
    for i, mm in enumerate((120, 100, 77.5, 55)):
        h = mm * s / 2
        y = y0 + i * 3.0 * s
        bx(f"{name}_{i}", (x0 - h, y, z0 - 2 * h), (x0 + h, y + 3.0 * s, z0), m["core" if i % 2 else "sr"], g)
        out[mm] = (x0 + h - 4 * s, y + 3.0 * s, z0 - 4 * s)
    return g, out
