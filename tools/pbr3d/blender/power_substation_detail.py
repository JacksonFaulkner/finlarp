"""Part builders, camera and bead helpers for the SUBSTATION page (power_substation_*.py).

Units are centimetres (1 scene unit = 1 cm), Y up, camera on +z, so a 5 m transformer tank is 500
units and the whole yard (tower to switchgear house) stays well inside pbr3d's 40-40000 depth range.

  transformer   the power transformer, cut open on the plane z = ZC through its core: stepped
                laminated core (3 limbs, 2 yokes), LV and HV windings per limb with the pressboard
                barrier between them, leads, the on-load tap changer with its tap leads, oil, the
                tank, HV and LV bushings (cut open too: copper conductor, paper-and-foil condenser
                core, porcelain shell and sheds), conservator, radiator banks with fans. A `whole`
                group (front wall, full walls, whole bushings) and a `cutg` group (walls and
                bushings cut at ZC) are switched by the caller.
  yard          the substation yard around it: a lattice transmission tower and the 230 kV line,
                the dead-end gantry with strain insulator strings, surge arresters, a disconnect
                switch, a dead-tank SF6 circuit breaker, bus post insulators, the LV bus, cable
                terminations, the cable tray and the switchgear house.
  small parts   a plain transformer (for rows of units), a teaching core (one window, a 20-turn
                and a 2-turn coil), week blocks for lead times, a steel coil and grain sheet, a ship.

Power flow is drawn as glowing beads riding the real conductors (`wire` + `run`, as on the
PHOTODIODE page): yellow for high voltage, orange for low voltage, cyan for magnetic flux.
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, ball, box, cut, empty, fly, key, show, tube, mat, _smooth  # noqa: E402

PAGE = "power_substation"

# ---- the transformer (centred on x = 0, standing on its plinth) ---------------------------------
ZC = -170.0                      # the cut plane through the core and windings
TX0, TX1 = -420.0, 480.0         # tank, outside
TY0, TY1 = 50.0, 560.0
TZ0, TZ1 = -340.0, 0.0
WT = 10.0                        # wall thickness
OIL_Y = 528.0                    # oil level inside the tank
LXS = (-260.0, 0.0, 260.0)       # the three limbs (phases A, B, C)
RC = 45.0                        # limb radius (stepped)
YOKE_B = (100.0, 180.0)
YOKE_T = (420.0, 500.0)
WIND = (195.0, 405.0)            # winding height
LV_R = (52.0, 70.0)
BAR_R = (72.0, 78.0)
HV_R = (82.0, 112.0)
HV_DISCS = 14
LV_RINGS = 5
HV_COL = 97.0                    # x offset of the HV winding's right column (bead lane)
LV_COL = -61.0                   # x offset of the LV winding's left column
OLTC_X, OLTC_R = 428.0, 30.0
HVB_Z, LVB_Z = -300.0, -235.0
HVB_H, LVB_H = 390.0, 170.0
HVB_X = tuple(x + HV_COL for x in LXS)
LVB_X = tuple(x + LV_COL for x in LXS)
HV_TOP = TY1 + HVB_H + 18.0      # top of the HV terminal
LV_TOP = TY1 + LVB_H + 14.0
CONS = (-600.0, -380.0, 800.0, -300.0, 50.0)  # conservator x0, x1, y, z, r
RAD_L = (-575.0, -440.0)         # radiator banks (x ranges)
RAD_R = (500.0, 635.0)
RAD_Y = (110.0, 480.0)
RAD_Z = [-320.0 + 35.0 * k for k in range(9)]
CZ = 2.5                         # beads ride this far in front of a cut face

# ---- the yard -----------------------------------------------------------------------------------
PZ = (-110.0, -220.0, -330.0)    # phase z positions of the line and yard equipment
TWX = -3700.0                    # transmission tower
GX = -2350.0                     # dead-end gantry
AX = -2050.0                     # surge arresters
DX = -1800.0                     # disconnect switch
BX = -1350.0                     # circuit breaker
BUSX = -850.0                    # bus post insulators
LZ = (-60.0, -140.0, -220.0)     # LV bus phase z
LV_BUS_Y = (800.0, 812.0, 824.0)
TERM_X = 820.0                   # cable terminations
HOUSE = (1180.0, 1780.0, 0.0, 400.0, -560.0, 60.0)


# ---- materials ------------------------------------------------------------------------------------


def materials(m):
    """Adds the page's materials to the dict from sand_zooms.start."""
    m.update({
        "tank": mat("ps_tank", (0.40, 0.45, 0.46), metal=0.35, rough=0.5),
        "tank_edge": mat("ps_tank_edge", (0.66, 0.68, 0.66), metal=0.5, rough=0.4),
        "galv": mat("ps_galv", (0.60, 0.62, 0.64), metal=0.8, rough=0.38),
        "porcelain": mat("ps_porcelain", (0.46, 0.22, 0.12), rough=0.22),
        "polymer": mat("ps_polymer", (0.52, 0.55, 0.58), rough=0.45),
        "glass_disc": mat("ps_glass_disc", (0.30, 0.52, 0.48), metal=0.2, rough=0.15),
        "alu": mat("ps_alu", (0.82, 0.84, 0.87), metal=0.9, rough=0.28),
        "conductor": mat("ps_conductor", (0.72, 0.74, 0.76), metal=0.9, rough=0.35),
        "copper": mat("ps_copper", (0.88, 0.48, 0.24), metal=0.9, rough=0.3),
        "copper_hv": mat("ps_copper_hv", (0.78, 0.40, 0.20), metal=0.85, rough=0.35),
        "paper": mat("ps_paper", (0.80, 0.66, 0.42), rough=0.7),
        "foil": mat("ps_foil", (0.92, 0.80, 0.45), metal=1.0, rough=0.25),
        "core_a": mat("ps_core_a", (0.34, 0.38, 0.45), metal=0.75, rough=0.32),
        "core_b": mat("ps_core_b", (0.22, 0.25, 0.30), metal=0.75, rough=0.38),
        "oil": mat("ps_oil", (0.50, 0.32, 0.07), rough=0.35),
        "oil_surf": mat("ps_oil_surf", (0.72, 0.50, 0.12), metal=0.3, rough=0.12),
        "concrete": mat("ps_concrete", (0.55, 0.54, 0.51), rough=0.9),
        "gravel": mat("ps_gravel", (0.30, 0.30, 0.29), rough=0.95),
        "cabinet": mat("ps_cabinet", (0.72, 0.74, 0.72), rough=0.5),
        "sf6": mat("ps_sf6", (0.58, 0.61, 0.63), metal=0.6, rough=0.38),
        "house": mat("ps_house", (0.76, 0.77, 0.73), rough=0.6),
        "roof": mat("ps_roof", (0.30, 0.32, 0.36), metal=0.4, rough=0.5),
        "door": mat("ps_door", (0.25, 0.36, 0.48), metal=0.3, rough=0.5),
        "fan": mat("ps_fan", (0.14, 0.15, 0.17), rough=0.5),
        "hv": mat("ps_hv", (1.0, 0.86, 0.30), emit=(1.0, 0.82, 0.25), strength=4.0),
        "lv": mat("ps_lv", (1.0, 0.50, 0.16), emit=(1.0, 0.45, 0.12), strength=4.0),
        "flux": mat("ps_flux", (0.30, 0.88, 1.0), emit=(0.25, 0.85, 1.0), strength=4.0),
        "hot": mat("ps_hot", (1.0, 0.40, 0.12), emit=(1.0, 0.35, 0.08), strength=3.5),
        "cool": mat("ps_cool", (0.35, 0.62, 1.0), emit=(0.3, 0.55, 1.0), strength=3.0),
        "hot_core": mat("ps_hot_core", (0.45, 0.10, 0.05), emit=(0.9, 0.18, 0.05), strength=0.35),
        "hot_cu": mat("ps_hot_cu", (1.0, 0.55, 0.18), emit=(1.0, 0.50, 0.12), strength=2.2),
        "wisp": mat("ps_wisp", (1.0, 0.55, 0.30), emit=(1.0, 0.45, 0.2), strength=1.6),
        "week": mat("ps_week", (0.24, 0.26, 0.31), rough=0.6),
        "w21": mat("ps_w21", (0.55, 0.75, 1.0), emit=(0.45, 0.68, 1.0), strength=1.6),
        "w24": mat("ps_w24", (1.0, 0.78, 0.30), emit=(1.0, 0.72, 0.22), strength=1.8),
        "w25": mat("ps_w25", (1.0, 0.55, 0.20), emit=(1.0, 0.48, 0.15), strength=2.0),
        "wgsu": mat("ps_wgsu", (1.0, 0.25, 0.18), emit=(1.0, 0.2, 0.12), strength=2.0),
        "grain_a": mat("ps_grain_a", (0.48, 0.52, 0.58), metal=0.8, rough=0.25),
        "grain_b": mat("ps_grain_b", (0.36, 0.40, 0.47), metal=0.8, rough=0.3),
        "grain_c": mat("ps_grain_c", (0.58, 0.60, 0.64), metal=0.8, rough=0.22),
        "water": mat("ps_water", (0.07, 0.18, 0.30), metal=0.2, rough=0.15),
        "hull": mat("ps_hull", (0.55, 0.14, 0.12), metal=0.3, rough=0.5),
        "deck": mat("ps_deck", (0.30, 0.32, 0.35), metal=0.4, rough=0.5),
        "brick": mat("ps_brick", (0.52, 0.30, 0.22), rough=0.85),
        "red": mat("ps_red", (1.0, 0.15, 0.10), emit=(1.0, 0.12, 0.08), strength=3.0),
        "green": mat("ps_green", (0.25, 1.0, 0.45), emit=(0.2, 1.0, 0.4), strength=2.5),
        "white": mat("ps_white", (0.88, 0.88, 0.86), rough=0.5),
        "steel_plate": mat("ps_steel_plate", (0.50, 0.53, 0.58), metal=0.8, rough=0.3),
    })
    return m


# ---- geometry -------------------------------------------------------------------------------------


def _link(name, me, m, parent):
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    _smooth(o)
    return o


def ring_y(name, cx, cz, y0, y1, ri, ro, m, parent=None, half=True, segs=28):
    """A hollow cylinder standing on y, axis at (cx, cz). `half` keeps only z <= cz and caps the
    two cut faces flat on the plane z = cz, so the wall's section shows. ri may be 0 (a solid)."""
    if half:
        angles = [math.pi + math.pi * i / (segs // 2) for i in range(segs // 2 + 1)]
    else:
        angles = [2 * math.pi * i / segs for i in range(segs)]
    ri = max(ri, 0.05)
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
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return _link(name, me, m, parent)


def ring_x(name, x0, x1, cy, cz, ri, ro, m, parent=None, segs=32):
    """A whole hollow cylinder along x (axis at y = cy, z = cz)."""
    angles = [2 * math.pi * i / segs for i in range(segs)]
    ri = max(ri, 0.05)
    rings = [(x0, ro), (x1, ro), (x1, ri), (x0, ri)]
    vs = [tuple(P(x, cy + r * math.cos(t), cz + r * math.sin(t))) for x, r in rings for t in angles]
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
    return _link(name, me, m, parent)


def join(objs, name):
    """Merge meshes (all with the same parent) into one object; materials are kept per face."""
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


def wire(name, pts, r, m, parent, verts=8):
    """A conductor through `pts`: a tube per segment, a ball at each joint, merged into one mesh
    (the PHOTODIODE page's segmented wire). Beads ride the same points with `run`."""
    parts = []
    for k in range(len(pts) - 1):
        if math.dist(pts[k], pts[k + 1]) < 1e-3:
            continue
        parts.append(tube(f"{name}_{k}", pts[k], pts[k + 1], r, m, parent, verts))
        if k:
            parts.append(ball(f"{name}_j{k}", pts[k], r, m, parent, 8))
    return join(parts, name)


def sag(a, b, s, n=12):
    """Points of a conductor hung from a to b, sagging `s` at its middle."""
    return [tuple(a[i] + (b[i] - a[i]) * t - (4 * s * t * (1 - t) if i == 1 else 0.0) for i in range(3))
            for t in (k / n for k in range(n + 1))]


def arch(a, b, h, n=10):
    """Points of a jumper arched `h` up between a and b."""
    return [tuple(a[i] + (b[i] - a[i]) * t + (4 * h * t * (1 - t) if i == 1 else 0.0) for i in range(3))
            for t in (k / n for k in range(n + 1))]


_beads = {}


def bead(name, at, size, m, parent):
    """A glowing bead: one shared unit-sphere mesh per material, scaled, so the GLB stores it once."""
    me = _beads.get(m.name)
    try:
        alive = me is not None and me.name in bpy.data.meshes
    except ReferenceError:
        alive = False
    if not alive:
        o = ball(name, (0, 0, 0), 1.0, m, None, 10)
        me = o.data
        bpy.data.objects.remove(o)
        _beads[m.name] = me
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = P(*at)
    o.scale = (size, size, size)
    o.parent = parent
    return o


def finish(name):
    """sand_zooms.finish, sampling every second frame (beads and switches stay smooth at 12 fps keys)."""
    out = os.path.dirname(os.path.abspath(__file__))
    glb = os.path.join(out, "..", "assets", f"{PAGE}_{name}.glb")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{PAGE}_{name}.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.normpath(glb), export_format="GLB", export_yup=True,
                              export_animations=True, export_force_sampling=True, export_frame_step=2,
                              export_cameras=False, export_lights=False, use_selection=False)
    print("exported", os.path.normpath(glb))
    check(os.path.normpath(glb))


def check(glb):
    """Fail loudly if a switched-off node lost its scale channel in the export (it would show all
    the time): every node exported at OFF scale must be animated."""
    import json
    import struct
    d = open(glb, "rb").read()
    n = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + n])
    has = {c["target"]["node"] for a in j.get("animations", []) for c in a["channels"] if c["target"]["path"] == "scale"}
    bad = [nd["name"] for i, nd in enumerate(j["nodes"]) if nd.get("scale", [1])[0] < 1e-3 and i not in has]
    if bad:
        raise SystemExit(f"{len(bad)} switched nodes lost their animation: {bad[:8]}")


def run(parent, name, pts, n, size, m, b, u0, u1, life, steps=None):
    """`n` beads that each ride the absolute polyline `pts` over `life` frames, launched one after
    another between fractions u0 and u1 of beat `b` (fiber_photodiode_detail.run)."""
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        bead(f"{name}{k}_s", pts[0], size, m, e)
        f0 = 2 * (F(b, u0 + (u1 - u0) * k / max(1, n - 1)) // 2)
        f1 = f0 + 2 * (life // 2)
        fly(e, path, f0, f1, steps=steps or max(4, min(40, len(pts) * 2)))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


def runs(parent, name, pts, n, size, m, spans, life, steps=None):
    """`run` over several (beat, u0, u1) spans."""
    for j, (b, u0, u1) in enumerate(spans):
        run(parent, f"{name}_{j}", pts, n, size, m, b, u0, u1, life, steps)


def insulator(name, a, b, r_core, r_shed, n, m, parent, cap=None):
    """A post or string insulator from a to b: a core rod with `n` sheds (alternating sizes),
    merged into one mesh. `cap` adds metal end fittings in that material."""
    parts = [tube(f"{name}_core", a, b, r_core, m, parent, 14)]
    d = [b[i] - a[i] for i in range(3)]
    L = math.sqrt(sum(x * x for x in d))
    u = [x / L for x in d]
    t = min(L / (n + 1) * 0.35, 5.0)
    for k in range(n):
        c = (k + 1) / (n + 1)
        p = tuple(a[i] + d[i] * c for i in range(3))
        q = tuple(p[i] + u[i] * t for i in range(3))
        parts.append(tube(f"{name}_s{k}", p, q, r_shed * (1.0 if k % 2 == 0 else 0.78), m, parent, 12))
    if cap is not None:
        for j, p in enumerate((a, b)):
            q = tuple(p[i] + u[i] * (6.0 if j == 0 else -6.0) for i in range(3))
            parts.append(tube(f"{name}_cap{j}", p, q, r_core * 1.5, cap, parent, 14))
    return join(parts, name)


def lattice(name, x, z, y0, y1, w0, w1, m, parent, step=110.0, r=2.6):
    """A lattice steel column (or tower body) from y0 to y1, `w0` wide at the bottom tapering to
    `w1`, centred on (x, z): four corner legs, horizontals and X-braces, merged into one mesh."""
    n = max(1, int((y1 - y0) / step))
    parts = []

    def corner(y, sx, sz):
        t = (y - y0) / (y1 - y0)
        hw = (w0 + (w1 - w0) * t) / 2
        return (x + sx * hw, y, z + sz * hw)

    cs = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    for k, (sx, sz) in enumerate(cs):
        parts.append(tube(f"{name}_leg{k}", corner(y0, sx, sz), corner(y1, sx, sz), r * 1.5, m, parent, 6))
    for j in range(n):
        ya, yb = y0 + (y1 - y0) * j / n, y0 + (y1 - y0) * (j + 1) / n
        for k in range(4):
            c0, c1 = cs[k], cs[(k + 1) % 4]
            parts.append(tube(f"{name}_h{j}_{k}", corner(yb, *c0), corner(yb, *c1), r, m, parent, 5))
            parts.append(tube(f"{name}_d{j}_{k}", corner(ya, *c0), corner(yb, *c1), r * 0.8, m, parent, 5))
            parts.append(tube(f"{name}_e{j}_{k}", corner(ya, *c1), corner(yb, *c0), r * 0.8, m, parent, 5))
    return join(parts, name)


# ---- bushings -------------------------------------------------------------------------------------


def bushing(m, parent, x, y0, z, h, rs, n_sheds, half, name, shell="porcelain"):
    """A bushing standing on the tank lid at (x, y0, z), `h` tall, sheds of radius `rs`. With
    `half` it is cut open on the plane z (its axis): the copper conductor, the paper condenser core
    with its graded foil layers, the oil gap, the porcelain shell and sheds, the flange and the top
    cap all show in section. Returns its top terminal point."""
    parts = []

    def R(nm, ya, yb, ri, ro, mt):
        parts.append(ring_y(f"{name}_{nm}", x, z, ya, yb, ri, ro, mt, parent, half, 28 if half else 24))

    rc = 0.12 * rs           # conductor
    rp = 0.44 * rs           # condenser core outer
    r_in, r_out = 0.52 * rs, 0.64 * rs  # shell
    y_top = y0 + h
    R("flange", y0 - 4.0, y0 + 0.05 * h, r_in, 0.85 * rs, m["galv"])
    R("shell", y0 + 0.05 * h, y_top - 0.06 * h, r_in, r_out, m[shell])
    for k in range(n_sheds):
        ya = y0 + 0.08 * h + (0.84 * h) * k / n_sheds
        R(f"shed{k}", ya, ya + min(5.0, 0.3 * h / n_sheds), r_out, rs * (1.0 if k % 2 == 0 else 0.8), m[shell])
    R("cap", y_top - 0.06 * h, y_top, 0.0, 0.62 * rs, m["galv"])
    R("term", y_top, y_top + 0.05 * h, 0.0, rc * 1.4, m["alu"])
    if half:
        R("cond", y0 - 70.0, y_top, 0.0, rc, m["copper"])
        foils = 4
        edges = [rc + (rp - rc) * k / foils for k in range(foils + 1)]
        for k in range(foils):
            ya = y0 - 60.0 + 12.0 * k
            yb = y_top - 0.08 * h - 0.05 * h * k
            R(f"paper{k}", ya, yb, edges[k], edges[k + 1] - 0.9, m["paper"])
            R(f"foil{k}", ya + 4.0, yb - 4.0, edges[k + 1] - 0.9, edges[k + 1], m["foil"])
        R("oilgap", y0 - 2.0, y_top - 0.08 * h, rp, r_in, m["oil"])
    join(parts, name)
    return (x, y_top + 0.05 * h, z)


# ---- the core and windings ----------------------------------------------------------------------


def core(m, parent, name="core", lxs=LXS, rc=RC, yb=YOKE_B, yt=YOKE_T, zc=ZC, half=True, plates=6):
    """A stepped, laminated core: `plates` packets per half, each a frame of limbs and yokes whose
    width follows a circle, in two greys so the stacking shows. Only z <= zc when `half`."""
    a_parts, b_parts = [], []
    zs = [zc - rc + rc * k / plates for k in range(plates + 1)]
    layers = list(zip(zs[:-1], zs[1:]))
    if not half:
        layers += [(zc + (zc - b), zc + (zc - a)) for a, b in layers]
    x_lo, x_hi = min(lxs), max(lxs)
    for k, (za, zb) in enumerate(layers):
        zm = (za + zb) / 2
        w = math.sqrt(max(rc * rc - (zm - zc) ** 2, (0.35 * rc) ** 2))
        bucket = a_parts if k % 2 == 0 else b_parts
        mt = m["core_a"] if k % 2 == 0 else m["core_b"]
        for j, lx in enumerate(lxs):
            bucket.append(box(f"{name}_l{k}_{j}", (lx - w, yb[1], za), (lx + w, yt[0], zb), mt, parent))
        bucket.append(box(f"{name}_yb{k}", (x_lo - w, yb[0], za), (x_hi + w, yb[1], zb), mt, parent))
        bucket.append(box(f"{name}_yt{k}", (x_lo - w, yt[0], za), (x_hi + w, yt[1], zb), mt, parent))
    grooves = []
    if half:  # sheet edges drawn on the cut face, so the stack of thin sheets reads
        gm = m["core_b"]
        for j, lx in enumerate(lxs):
            for k in range(1, 9):
                x = lx - rc + 2 * rc * k / 9
                grooves.append(box(f"{name}_gl{j}_{k}", (x - 0.8, yb[1], zc), (x + 0.8, yt[0], zc + 0.6), gm, parent))
        for nm, (ya, yb_) in (("b", yb), ("t", yt)):
            for k in range(1, 8):
                y = ya + (yb_ - ya) * k / 8
                grooves.append(box(f"{name}_g{nm}{k}", (x_lo - rc, y - 0.8, zc), (x_hi + rc, y + 0.8, zc + 0.6), gm, parent))
    o = join(a_parts + b_parts + grooves, name)
    return o


def windings(m, parent, name="wd", lxs=LXS, zc=ZC, half=True):
    """Per limb: LV winding (few heavy rings) inside, pressboard barrier, HV winding (many discs
    on a recessed pressboard spacer cylinder) outside. Cut on z = zc when `half`."""
    y0, y1 = WIND
    for j, lx in enumerate(lxs):
        parts = []
        h = (y1 - y0) / LV_RINGS
        for k in range(LV_RINGS):
            parts.append(ring_y(f"{name}_lv{j}_{k}", lx, zc, y0 + h * k + 1.2, y0 + h * (k + 1) - 1.2, *LV_R, m["copper"], parent, half))
        parts.append(ring_y(f"{name}_bar{j}", lx, zc, y0 - 8.0, y1 + 8.0, *BAR_R, m["paper"], parent, half))
        h = (y1 - y0) / HV_DISCS
        for k in range(HV_DISCS):
            parts.append(ring_y(f"{name}_hv{j}_{k}", lx, zc, y0 + h * k + 1.3, y0 + h * (k + 1) - 1.3, *HV_R, m["copper_hv"], parent, half))
        sp = ring_y(f"{name}_sp{j}", lx, zc - (1.0 if half else 0.0), y0, y1, HV_R[0] + 4.0, HV_R[1] - 4.0, m["paper"], parent, half)
        parts.append(sp)
        # pressboard end rings top and bottom
        parts.append(ring_y(f"{name}_er{j}a", lx, zc, y0 - 12.0, y0 - 2.0, LV_R[0], HV_R[1], m["paper"], parent, half))
        parts.append(ring_y(f"{name}_er{j}b", lx, zc, y1 + 2.0, y1 + 12.0, LV_R[0], HV_R[1], m["paper"], parent, half))
        join(parts, f"{name}_ph{j}")


def hv_column(lx, zc=ZC, top=None):
    """The zig-zag lane down the cut face of an HV winding's right column (disc by disc)."""
    y0, y1 = WIND
    h = (y1 - y0) / HV_DISCS
    pts = [] if top is None else list(top)
    for k in range(HV_DISCS):
        y = y1 - h * (k + 0.5)
        xa, xb = (lx + HV_R[0] + 5, lx + HV_R[1] - 5) if k % 2 == 0 else (lx + HV_R[1] - 5, lx + HV_R[0] + 5)
        pts += [(xa, y, zc + CZ), (xb, y, zc + CZ)]
    return pts


def lv_column(lx, zc=ZC):
    """Up the cut face of an LV winding's left column."""
    y0, y1 = WIND
    x = lx - (LV_R[0] + LV_R[1]) / 2
    return [(x, y0 + 6.0, zc + CZ), (x, y1 - 4.0, zc + CZ)]


def flux_loops(zc=ZC, lxs=LXS, yb=YOKE_B, yt=YOKE_T, reverse=False):
    """Two loops on the core's cut face: up the middle limb, out along the top yoke, down an outer
    limb, back along the bottom yoke."""
    ym_t, ym_b = (yt[0] + yt[1]) / 2, (yb[0] + yb[1]) / 2
    loops = []
    for side in (0, 2):
        lp = [(lxs[1], ym_b, zc + CZ), (lxs[1], ym_t, zc + CZ), (lxs[side], ym_t, zc + CZ), (lxs[side], ym_b, zc + CZ),
              (lxs[1], ym_b, zc + CZ)]
        loops.append(list(reversed(lp)) if reverse else lp)
    return loops


# ---- the transformer ----------------------------------------------------------------------------


def radiator_bank(m, parent, x0, x1, name, tank_x):
    """Finned panels standing in a row along z, joined by top and bottom header pipes to the tank."""
    parts = []
    xm = (x0 + x1) / 2
    for k, z in enumerate(RAD_Z):
        parts.append(box(f"{name}_p{k}", (x0, RAD_Y[0], z - 3.0), (x1, RAD_Y[1], z + 3.0), m["tank"], parent))
        for j in range(3):  # pressed channels on each panel
            xx = x0 + (x1 - x0) * (j + 1) / 4
            parts.append(box(f"{name}_c{k}_{j}", (xx - 4.0, RAD_Y[0] + 15.0, z - 4.5), (xx + 4.0, RAD_Y[1] - 15.0, z + 4.5), m["tank"], parent))
    for y in (RAD_Y[1] - 12.0, RAD_Y[0] + 12.0):
        parts.append(tube(f"{name}_hdr{y:.0f}", (xm, y, RAD_Z[0] - 10.0), (xm, y, RAD_Z[-1] + 10.0), 8.0, m["tank"], parent, 12))
        parts.append(tube(f"{name}_pipe{y:.0f}", (tank_x, y, -180.0), (xm, y, -180.0), 9.0, m["tank"], parent, 12))
    return join(parts, name)


def fan(m, parent, x, y, z, r, name):
    """A cooling fan under a radiator bank, blowing up: shroud ring, hub and three blades. The blade
    group spins about y; returns it."""
    ring_y(f"{name}_shroud", x, z, y - 8.0, y + 8.0, r, r + 4.0, m["fan"], parent, False, 28)
    rot = empty(f"{name}_rot", parent, P(x, y, z))
    parts = [ball(f"{name}_hub", (0, 0, 0), 8.0, m["fan"], rot, 10)]
    for k in range(3):
        t = 2 * math.pi * k / 3
        parts.append(tube(f"{name}_bl{k}", (0, 0, 0), (r * 0.9 * math.cos(t), 0.0, r * 0.9 * math.sin(t)), 7.0, m["galv"], rot, 6))
    join(parts, f"{name}_blades")
    return rot


def spin(obj, f0, f1, turns):
    """Rotate `obj` about scene y (Blender z) linearly from f0 to f1."""
    obj.rotation_mode = "XYZ"
    key(obj, f0, "rotation_euler", (0.0, 0.0, 0.0), linear=True)
    key(obj, f1, "rotation_euler", (0.0, 0.0, 2 * math.pi * turns), linear=True)


def tank_walls(m, parent, z1, name, front=False):
    """Back-to-`z1` tank walls: sides, floor, lid and lid rim (and the front wall if `front`)."""
    parts = [
        box(f"{name}_l", (TX0, TY0, TZ0), (TX0 + WT, TY1, z1), m["tank"], parent),
        box(f"{name}_r", (TX1 - WT, TY0, TZ0), (TX1, TY1, z1), m["tank"], parent),
        box(f"{name}_f", (TX0, TY0, TZ0), (TX1, TY0 + WT, z1), m["tank"], parent),
        box(f"{name}_lid", (TX0, TY1 - WT, TZ0), (TX1, TY1, z1), m["tank"], parent),
        box(f"{name}_rim", (TX0 - 8.0, TY1 - 16.0, TZ0 - 8.0), (TX1 + 8.0, TY1 - 8.0, z1 + (8.0 if front else 0.0)), m["tank"], parent),
        box(f"{name}_base", (TX0 - 10.0, TY0 - 10.0, TZ0 - 10.0), (TX1 + 10.0, TY0, z1 + (10.0 if front else 0.0)), m["dark_steel"], parent),
    ]
    if front:
        parts.append(box(f"{name}_fr", (TX0, TY0, TZ1 - WT), (TX1, TY1, TZ1), m["tank"], parent))
    return join(parts, name)


def transformer(m, root, name="tx"):
    """The power transformer (see the module docstring). Returns a dict of groups and paths:
    whole, cutg, front (the front wall, stiffeners and tap-changer drive, which fly off), fans,
    hot_core / hot_cu (glow overlays, hidden), and the bead paths hv[i], lv[i], hv_top[i], lv_top[i],
    flux (two loops), oil_hot[...], oil_cool[...]."""
    g = empty(name, root)
    whole = empty(f"{name}_whole", g)
    cutg = empty(f"{name}_cutg", g)
    front = empty(f"{name}_front", g)

    box(f"{name}_plinth", (-640.0, 0.0, -420.0), (700.0, TY0 - 10.0, 60.0), m["concrete"], g)
    # common: back wall, oil on its inside face, the internals
    join([box(f"{name}_back", (TX0, TY0, TZ0), (TX1, TY1, TZ0 + WT), m["tank"], g),
          box(f"{name}_oilback", (TX0 + WT, TY0 + WT, TZ0 + WT), (TX1 - WT, OIL_Y, TZ0 + WT + 2.0), m["oil"], g)],
         f"{name}_backwall")
    core(m, g, f"{name}_core")
    windings(m, g, f"{name}_wd")
    # supports under the bottom yoke, clamps over the top yoke (behind the cut)
    join([box(f"{name}_blk{k}", (x - 30.0, TY0 + WT, ZC - 40.0), (x + 30.0, YOKE_B[0], ZC), m["paper"], g)
          for k, x in enumerate((-280.0, 0.0, 280.0))], f"{name}_blocks")
    # leads: HV from each bushing down to the top of its winding, LV from the winding up to its bushing
    hv_paths, lv_paths, hv_tops, lv_tops = [], [], [], []
    for j, lx in enumerate(LXS):
        hx, vx = HVB_X[j], LVB_X[j]
        hv_lead = [(hx, TY1 - 2.0, HVB_Z), (hx, WIND[1] + 18.0, HVB_Z), (hx, WIND[1] + 18.0, ZC - 6.0), (hx, WIND[1] - 2.0, ZC - 6.0)]
        wire(f"{name}_hvlead{j}", hv_lead, 3.5, m["copper"], g)
        lv_lead = [(vx, WIND[1] - 2.0, ZC - 6.0), (vx, WIND[1] + 22.0, ZC - 6.0), (vx, WIND[1] + 22.0, LVB_Z), (vx, TY1 - 2.0, LVB_Z)]
        wire(f"{name}_lvlead{j}", lv_lead, 5.0, m["copper"], g)
        hv_tops.append((hx, HV_TOP, HVB_Z))
        lv_tops.append((vx, LV_TOP, LVB_Z))
        down_bushing = [(hx, HV_TOP, HVB_Z + CZ), (hx, TY1, HVB_Z + CZ)]
        hv_paths.append(down_bushing + [(hx, WIND[1] + 18.0, HVB_Z + CZ), (hx, WIND[1] + 18.0, ZC + CZ)] + hv_column(lx))
        lv_paths.append(lv_column(lx) + [(vx, WIND[1] + 22.0, ZC + CZ), (vx, WIND[1] + 22.0, LVB_Z + CZ), (vx, TY1, LVB_Z + CZ),
                                          (vx, LV_TOP, LVB_Z + CZ)])
    # the on-load tap changer: an insulating cylinder beside phase C with its selector contacts,
    # the diverter switch on top, and tap leads from the HV winding
    parts = [ring_y(f"{name}_oltc", OLTC_X, ZC, 215.0, 470.0, OLTC_R - 5.0, OLTC_R, m["paper"], g, True),
             ring_y(f"{name}_oltc_shaft", OLTC_X, ZC, 215.0, 500.0, 0.0, 4.0, m["paper"], g, True),
             box(f"{name}_diverter", (OLTC_X - 24.0, 440.0, ZC - 24.0), (OLTC_X + 24.0, 500.0, ZC), m["dark_steel"], g)]
    taps = []
    for k in range(6):
        y = 235.0 + 30.0 * k
        for s in (-1, 1):
            parts.append(box(f"{name}_stud{k}{s}", (OLTC_X + s * 14.0 - 4.0, y - 4.0, ZC - 14.0), (OLTC_X + s * 14.0 + 4.0, y + 4.0, ZC), m["copper"], g))
        taps.append(y)
    join(parts, f"{name}_oltc_all")
    for k, y in enumerate(taps):
        wire(f"{name}_tap{k}", arch((LXS[2] + HV_R[1] - 2.0, y + 6.0, ZC - 3.0), (OLTC_X - 18.0, y, ZC - 3.0), 4.0, 4), 1.6, m["copper"], g, 6)
    # oil surface and the cut walls
    tank_walls(m, cutg, ZC, f"{name}_wcut")
    box(f"{name}_oiltop", (TX0 + WT, OIL_Y - 4.0, TZ0 + WT), (TX1 - WT, OIL_Y, ZC), m["oil_surf"], cutg)
    tank_walls(m, whole, TZ1, f"{name}_wwhole")
    # front wall, stiffeners and the tap changer's motor-drive cabinet: these fly off
    fparts = [box(f"{name}_front_wall", (TX0, TY0, TZ1 - WT), (TX1, TY1, TZ1), m["tank"], front)]
    for k, x in enumerate((-330.0, -170.0, -10.0, 150.0, 300.0)):
        fparts.append(box(f"{name}_stiff{k}", (x - 6.0, TY0 + 10.0, TZ1), (x + 6.0, TY1 - 16.0, TZ1 + 10.0), m["tank"], front))
    fparts.append(box(f"{name}_mdrive", (365.0, 140.0, TZ1), (455.0, 330.0, TZ1 + 38.0), m["cabinet"], front))
    fparts.append(tube(f"{name}_mshaft", (410.0, 330.0, TZ1 + 20.0), (410.0, TY1 - 10.0, TZ1 + 20.0), 3.0, m["galv"], front, 8))
    fparts.append(box(f"{name}_plate", (-60.0, 300.0, TZ1), (40.0, 360.0, TZ1 + 2.0), m["alu"], front))
    join(fparts, f"{name}_front_all")
    # bushings: cut-open ones for the cut view, whole ones otherwise
    for j in range(3):
        bushing(m, cutg, HVB_X[j], TY1, HVB_Z, HVB_H, 30.0, 12, True, f"{name}_hvbc{j}")
        bushing(m, whole, HVB_X[j], TY1, HVB_Z, HVB_H, 30.0, 12, False, f"{name}_hvbw{j}")
        bushing(m, cutg, LVB_X[j], TY1, LVB_Z, LVB_H, 24.0, 5, True, f"{name}_lvbc{j}")
        bushing(m, whole, LVB_X[j], TY1, LVB_Z, LVB_H, 24.0, 5, False, f"{name}_lvbw{j}")
    # conservator with its pipe and Buchholz relay
    cx0, cx1, cy, cz_, cr = CONS
    join([ring_x(f"{name}_cons", cx0, cx1, cy, cz_, 0.0, cr, m["tank"], g),
          ball(f"{name}_cons_e0", (cx0, cy, cz_), cr, m["tank"], g, 16),
          ball(f"{name}_cons_e1", (cx1, cy, cz_), cr, m["tank"], g, 16),
          tube(f"{name}_cons_leg0", (cx1 - 20.0, TY1, cz_), (cx1 - 20.0, cy, cz_), 6.0, m["galv"], g, 8),
          tube(f"{name}_cons_leg1", (cx0 + 30.0, RAD_Y[1], cz_), (cx0 + 30.0, cy, cz_), 6.0, m["galv"], g, 8),
          tube(f"{name}_cons_pipe", (cx1 - 50.0, cy - cr, cz_ + 20.0), (cx1 - 50.0, TY1, cz_ + 20.0), 5.0, m["tank"], g, 8),
          box(f"{name}_buchholz", (cx1 - 62.0, 640.0, cz_ + 8.0), (cx1 - 38.0, 670.0, cz_ + 32.0), m["dark_steel"], g)],
         f"{name}_conservator")
    radiator_bank(m, g, RAD_L[0], RAD_L[1], f"{name}_radl", TX0)
    radiator_bank(m, g, RAD_R[0], RAD_R[1], f"{name}_radr", TX1)
    fans = [fan(m, g, (RAD_R[0] + RAD_R[1]) / 2, RAD_Y[0] - 22.0, z, 50.0, f"{name}_fan{k}") for k, z in enumerate((-250.0, -90.0))]
    # glow overlays on the cut faces (core loss, copper loss)
    hot_core = empty(f"{name}_hot_core", g)
    w = RC
    hc = [box(f"{name}_hcl{j}", (lx - w, YOKE_B[1], ZC), (lx + w, YOKE_T[0], ZC + 1.5), m["hot_core"], hot_core) for j, lx in enumerate(LXS)]
    hc.append(box(f"{name}_hcb", (LXS[0] - w, YOKE_B[0], ZC), (LXS[2] + w, YOKE_B[1], ZC + 1.5), m["hot_core"], hot_core))
    hc.append(box(f"{name}_hct", (LXS[0] - w, YOKE_T[0], ZC), (LXS[2] + w, YOKE_T[1], ZC + 1.5), m["hot_core"], hot_core))
    join(hc, f"{name}_hot_core_m")
    hot_cu = empty(f"{name}_hot_cu", g)
    hcu = []
    for j, lx in enumerate(LXS):
        for s in (-1, 1):
            for nm, (ra, rb) in (("lv", LV_R), ("hv", HV_R)):
                xa, xb = sorted((lx + s * ra, lx + s * rb))
                hcu.append(box(f"{name}_hcu{j}{s}{nm}", (xa, WIND[0], ZC), (xb, WIND[1], ZC + 1.5), m["hot_cu"], hot_cu))
    join(hcu, f"{name}_hot_cu_m")
    # oil circulation: up the ducts, under the lid to a radiator, down its front panel, back in
    oil_hot, oil_cool = [], []
    xm_r, xm_l = (RAD_R[0] + RAD_R[1]) / 2, (RAD_L[0] + RAD_L[1]) / 2
    zf = RAD_Z[-1] + 6.0
    for j, lx in enumerate(LXS):
        side = 1 if j >= 1 else -1
        duct = lx + side * (BAR_R[1] + 2.0)
        xm, tx = (xm_r, TX1) if side > 0 else (xm_l, TX0)
        hot = [(duct, WIND[0], ZC + CZ), (duct, OIL_Y - 14.0, ZC + CZ), (tx - side * 30.0, OIL_Y - 14.0, ZC + CZ),
               (tx, RAD_Y[1] - 12.0, -180.0), (xm, RAD_Y[1] - 12.0, -180.0), (xm, RAD_Y[1] - 12.0, zf)]
        cool = [(xm, RAD_Y[1] - 12.0, zf), (xm, RAD_Y[0] + 12.0, zf), (xm, RAD_Y[0] + 12.0, -180.0), (tx, RAD_Y[0] + 12.0, -180.0),
                (tx - side * 30.0, TY0 + WT + 15.0, ZC + CZ), (duct, TY0 + WT + 15.0, ZC + CZ), (duct, WIND[0], ZC + CZ)]
        oil_hot.append(hot)
        oil_cool.append(cool)
    return {
        "g": g, "whole": whole, "cutg": cutg, "front": front, "fans": fans, "hot_core": hot_core, "hot_cu": hot_cu,
        "hv": hv_paths, "lv": lv_paths, "hv_top": hv_tops, "lv_top": lv_tops,
        "flux": flux_loops(), "flux_rev": flux_loops(reverse=True), "oil_hot": oil_hot, "oil_cool": oil_cool,
    }


def tank_mode(t, whole_iv, cut_iv):
    """Switch the transformer between its whole and cut-open states. The front group follows
    `whole` (callers that fly it off handle it themselves)."""
    show(t["whole"], whole_iv)
    show(t["cutg"], cut_iv)


def front_off(t, b, u0, u1, total_beats, back_at=None):
    """The front wall lifts forward and away between fractions u0 and u1 of beat b, then hides.
    If `back_at` (a beat), it is back in place from that beat on."""
    fr = t["front"]
    key(fr, F(b, u0), "location", P(0, 0, 0), linear=True)
    key(fr, F(b, u1), "location", P(0, 300.0, 700.0), linear=True)
    iv = [(0, F(b, u1))]
    if back_at is not None:
        key(fr, F(back_at, 0) - 1, "location", P(0, 300.0, 700.0), linear=True)
        key(fr, F(back_at, 0), "location", P(0, 0, 0), linear=True)
        iv.append((F(back_at, 0), F(total_beats, 0)))
    show(fr, iv)


# ---- the yard -------------------------------------------------------------------------------------


def yard(m, root, t, name="yd"):
    """The yard around the transformer `t` (from `transformer`). Returns the bead paths:
    hv[i] from the tower to the HV bushing top, lv[i] from the LV bushing top into the house,
    and named points for tags."""
    g = empty(name, root)
    box(f"{name}_gravel", (-4300.0, -14.0, -1500.0), (2300.0, 0.0, 700.0), m["gravel"], g)
    # the transmission tower the line arrives from
    lattice(f"{name}_tower", TWX, -220.0, 0.0, 1650.0, 380.0, 120.0, m["galv"], g, 150.0, 4.0)
    lattice(f"{name}_tower_top", TWX, -220.0, 1650.0, 2050.0, 120.0, 40.0, m["galv"], g, 130.0, 3.5)
    lattice(f"{name}_arm", TWX, -220.0, 1690.0, 1750.0, 60.0, 60.0, m["galv"], g, 60.0, 3.0)
    arm = []
    for z in (PZ[0] - 40.0, PZ[2] + 40.0):
        arm.append(box(f"{name}_armb{z:.0f}", (TWX - 25.0, 1690.0, min(z, -220.0)), (TWX + 25.0, 1750.0, max(z, -220.0)), m["galv"], g))
    join(arm, f"{name}_arms")
    line_att = []
    for i, z in enumerate(PZ):
        insulator(f"{name}_susp{i}", (TWX, 1690.0, z), (TWX, 1560.0, z), 3.0, 14.0, 9, m["glass_disc"], g, m["galv"])
        line_att.append((TWX, 1555.0, z))
    # the dead-end gantry: two lattice columns and a lattice beam
    lattice(f"{name}_gcol0", GX, 60.0, 0.0, 1500.0, 70.0, 50.0, m["galv"], g, 120.0, 3.0)
    lattice(f"{name}_gcol1", GX, -500.0, 0.0, 1500.0, 70.0, 50.0, m["galv"], g, 120.0, 3.0)
    box(f"{name}_gbeam", (GX - 22.0, 1450.0, -520.0), (GX + 22.0, 1500.0, 80.0), m["galv"], g)
    hv = []
    for i, z in enumerate(PZ):
        a_end = (GX - 140.0, 1440.0, z)
        insulator(f"{name}_strain{i}", (GX - 12.0, 1450.0, z), a_end, 3.0, 13.0, 10, m["glass_disc"], g, m["galv"])
        line = sag(line_att[i], a_end, 170.0, 16)
        wire(f"{name}_line{i}", line, 3.5, m["conductor"], g)
        # surge arrester on its stand
        box(f"{name}_ast{i}", (AX - 12.0, 0.0, z - 12.0), (AX + 12.0, 430.0, z + 12.0), m["galv"], g)
        insulator(f"{name}_arr{i}", (AX, 430.0, z), (AX, 640.0, z), 9.0, 17.0, 9, m["polymer"], g, m["galv"])
        # disconnect switch: two post insulators on a stand, an aluminium blade across
        box(f"{name}_dst{i}", (DX - 14.0, 0.0, z - 14.0), (DX + 14.0, 360.0, z + 14.0), m["galv"], g)
        box(f"{name}_dch{i}", (DX - 95.0, 360.0, z - 12.0), (DX + 95.0, 385.0, z + 12.0), m["galv"], g)
        for s in (-1, 1):
            insulator(f"{name}_dpi{i}{s}", (DX + s * 75.0, 385.0, z), (DX + s * 75.0, 585.0, z), 9.0, 18.0, 8, m["porcelain"], g, m["galv"])
            box(f"{name}_djaw{i}{s}", (DX + s * 75.0 - 10.0, 585.0, z - 8.0), (DX + s * 75.0 + 10.0, 600.0, z + 8.0), m["alu"], g)
        blade = [(DX - 75.0, 607.0, z), (DX + 75.0, 607.0, z)]
        tube(f"{name}_blade{i}", blade[0], blade[1], 4.0, m["alu"], g, 10)
        # dead-tank SF6 breaker pole: tank on legs, two bushings in a V, current transformers
        bt = [tube(f"{name}_btank{i}", (BX - 110.0, 380.0, z), (BX + 110.0, 380.0, z), 40.0, m["sf6"], g, 24),
              ball(f"{name}_bend{i}a", (BX - 110.0, 380.0, z), 40.0, m["sf6"], g, 16),
              ball(f"{name}_bend{i}b", (BX + 110.0, 380.0, z), 40.0, m["sf6"], g, 16),
              box(f"{name}_bleg{i}a", (BX - 90.0, 0.0, z - 10.0), (BX - 70.0, 345.0, z + 10.0), m["galv"], g),
              box(f"{name}_bleg{i}b", (BX + 70.0, 0.0, z - 10.0), (BX + 90.0, 345.0, z + 10.0), m["galv"], g)]
        join(bt, f"{name}_breaker{i}")
        tops = []
        for s in (-1, 1):
            base = (BX + s * 75.0, 410.0, z)
            top = (BX + s * 150.0, 690.0, z)
            insulator(f"{name}_bb{i}{s}", base, top, 10.0, 19.0, 9, m["porcelain"], g, m["galv"])
            d = [top[k] - base[k] for k in range(3)]
            L = math.sqrt(sum(x * x for x in d))
            ct_a = tuple(base[k] + d[k] * 0.02 for k in range(3))
            ct_b = tuple(base[k] + d[k] * 0.16 for k in range(3))
            tube(f"{name}_ct{i}{s}", ct_a, ct_b, 26.0, m["dark_steel"], g, 20)
            tops.append(top)
        # bus post insulator on its column
        box(f"{name}_bpc{i}", (BUSX - 14.0, 0.0, z - 14.0), (BUSX + 14.0, 820.0, z + 14.0), m["galv"], g)
        insulator(f"{name}_bpi{i}", (BUSX, 820.0, z), (BUSX, 1080.0, z), 9.0, 18.0, 10, m["porcelain"], g, m["galv"])
        bus_top = (BUSX, 1092.0, z)
        # conductors from the gantry onward, as wires the beads ride
        drop = arch((GX, 1446.0, z), (AX, 650.0, z), -120.0, 12)
        wire(f"{name}_drop{i}", drop, 3.0, m["conductor"], g)
        j1 = arch((AX, 650.0, z), (DX - 75.0, 607.0, z), 40.0, 8)
        wire(f"{name}_j1{i}", j1, 3.0, m["conductor"], g)
        j2 = arch((DX + 75.0, 607.0, z), tops[0], 50.0, 8)
        wire(f"{name}_j2{i}", j2, 3.0, m["conductor"], g)
        j3 = arch(tops[1], bus_top, 60.0, 10)
        wire(f"{name}_j3{i}", j3, 3.0, m["conductor"], g)
        j4 = sag(bus_top, t["hv_top"][i], 60.0, 14)
        wire(f"{name}_j4{i}", j4, 3.0, m["conductor"], g)
        through = [tops[0], (BX - 75.0, 410.0, z), (BX + 75.0, 410.0, z), tops[1]]
        hv.append(line + [(GX - 12.0, 1450.0, z)] + drop + j1 + blade + j2 + through + j3 + j4)
    # mechanism cabinet of the breaker, beside phase A
    box(f"{name}_bmech", (BX - 60.0, 40.0, PZ[0] + 60.0), (BX + 60.0, 300.0, PZ[0] + 110.0), m["cabinet"], g)
    box(f"{name}_bmech_ft", (BX - 60.0, 0.0, PZ[0] + 60.0), (BX + 60.0, 40.0, PZ[0] + 110.0), m["concrete"], g)
    for i, z in enumerate(PZ):
        box(f"{name}_pad{i}", (BX - 130.0, 0.0, z - 40.0), (BX + 130.0, 18.0, z + 40.0), m["concrete"], g)
    # LV side: rigid bus from the LV bushings over to the cable terminations, cables to the house
    lv = []
    box(f"{name}_tstruct", (TERM_X - 15.0, 0.0, LZ[2] - 50.0), (TERM_X + 15.0, 520.0, LZ[0] + 50.0), m["galv"], g)
    hx0, hx1, hy0, hy1, hz0, hz1 = HOUSE
    for i, z in enumerate(LZ):
        y = LV_BUS_Y[i]
        top = t["lv_top"][i]
        bus = [top, (top[0], y, top[2]), (top[0], y, z), (TERM_X - 80.0, y, z)]
        wire(f"{name}_lvbus{i}", bus, 5.0, m["alu"], g)
        term_top = (TERM_X, 770.0, z)
        bus2 = arch((TERM_X - 80.0, y, z), term_top, 12.0, 6)
        wire(f"{name}_lvbus2{i}", bus2, 5.0, m["alu"], g)
        insulator(f"{name}_term{i}", (TERM_X, 530.0, z), term_top, 10.0, 17.0, 6, m["polymer"], g, m["galv"])
        cable = [(TERM_X, 530.0, z), (TERM_X + 20.0, 500.0, z + 25.0), (TERM_X + 20.0, 70.0, z + 25.0),
                 (TERM_X + 80.0, 45.0, z + 25.0), (hx0, 45.0, z + 25.0)]
        wire(f"{name}_cable{i}", cable, 5.5, m["fan"], g)
        lv.append(bus + bus2[1:] + [(TERM_X, 530.0, z)] + cable[1:] + [(hx0 + 40.0, 45.0, z + 25.0)])
    box(f"{name}_tray", (TERM_X + 60.0, 25.0, LZ[2] - 10.0), (hx0, 32.0, LZ[0] + 55.0), m["galv"], g)
    for k in range(4):
        x = TERM_X + 100.0 + (hx0 - TERM_X - 140.0) * k / 3
        box(f"{name}_trayleg{k}", (x - 4.0, 0.0, LZ[1] - 4.0), (x + 4.0, 25.0, LZ[1] + 4.0), m["galv"], g)
    # the switchgear house
    hp = [box(f"{name}_house", (hx0, hy0, hz0), (hx1, hy1, hz1), m["house"], g),
          box(f"{name}_roof", (hx0 - 25.0, hy1, hz0 - 25.0), (hx1 + 25.0, hy1 + 22.0, hz1 + 25.0), m["roof"], g),
          box(f"{name}_door", (hx0 + 230.0, 0.0, hz1), (hx0 + 330.0, 250.0, hz1 + 3.0), m["door"], g),
          box(f"{name}_hvac", (hx1 - 200.0, hy1 + 22.0, hz0 + 100.0), (hx1 - 60.0, hy1 + 110.0, hz0 + 260.0), m["cabinet"], g),
          box(f"{name}_pad", (hx0 - 40.0, -2.0, hz0 - 40.0), (hx1 + 40.0, 6.0, hz1 + 80.0), m["concrete"], g)]
    for k in range(5):
        y = 290.0 + 14.0 * k
        hp.append(box(f"{name}_louv{k}", (hx0 + 420.0, y, hz1), (hx0 + 540.0, y + 7.0, hz1 + 4.0), m["roof"], g))
    join(hp, f"{name}_house_m")
    pts = {
        "tower": (TWX, 1750.0, -220.0), "line": line_att[0], "gantry": (GX, 1500.0, PZ[0] + 60.0),
        "arrester": (AX, 640.0, PZ[0]), "disconnect": (DX, 610.0, PZ[0]), "breaker": (BX, 420.0, PZ[0] + 40.0),
        "bus": (BUSX, 1092.0, PZ[0]), "lv_bus": (400.0, LV_BUS_Y[0], LZ[0]), "term": (TERM_X, 770.0, LZ[0]),
        "house": (hx0 + 300.0, hy1 + 20.0, hz1), "mid_line": hv[0][8],
    }
    return {"g": g, "hv": hv, "lv": lv, "pts": pts}


# ---- small parts ----------------------------------------------------------------------------------


def plain_transformer(m, parent, at, name, s=1.0, hv_h=300.0, tank="tank"):
    """A whole transformer without internals, scaled by `s` about its base at `at`: tank with
    stiffeners, three HV and three LV bushings (`hv_h` tall), radiators, conservator. Merged."""
    ox, oy, oz = at

    def A(p):
        return (ox + s * p[0], oy + s * p[1], oz + s * p[2])

    g = empty(name, parent)
    parts = [box(f"{name}_tank", A((-330, 30, -260)), A((330, 420, 0)), m[tank], g),
             box(f"{name}_lid", A((-340, 420, -270)), A((340, 432, 10)), m[tank], g),
             box(f"{name}_base", A((-345, 0, -275)), A((345, 30, 15)), m["dark_steel"], g)]
    for k in range(5):
        x = -260 + 130 * k
        parts.append(box(f"{name}_st{k}", A((x - 5, 40, 0)), A((x + 5, 410, 8)), m[tank], g))
    for side in (-1, 1):
        for k in range(7):
            z = -240 + 34 * k
            x0, x1 = (330, 430) if side > 0 else (-430, -330)
            parts.append(box(f"{name}_rad{side}{k}", A((x0, 70, z - 3)), A((x1, 380, z + 3)), m[tank], g))
    parts.append(ring_x(f"{name}_cons", ox + s * -300, ox + s * -60, oy + s * 600, oz + s * -230, 0.0, s * 38, m[tank], g, 20))
    parts.append(tube(f"{name}_consleg", A((-180, 432, -230)), A((-180, 600, -230)), s * 5, m["galv"], g, 8))
    obj = join(parts, f"{name}_body")
    for j in range(3):
        x = -150 + 150 * j
        insulator(f"{name}_hvb{j}", A((x, 432, -200)), A((x, 432 + hv_h, -200)), s * 10, s * 22, 9, m["porcelain"], g, m["galv"])
        insulator(f"{name}_lvb{j}", A((x + 60, 432, -90)), A((x + 60, 432 + 120, -90)), s * 9, s * 17, 4, m["porcelain"], g, m["galv"])
    return g, obj


def teaching_core(m, parent, name="tc", c=(0.0, 0.0, 0.0), hv_turns=20, lv_turns=2):
    """One window of laminated core (two limbs, two yokes) with a thin many-turn coil on the left
    limb and a heavy few-turn coil on the right. Returns the bead paths: hv (the coil), lv,
    flux (round the core), and points."""
    cx, cy, cz = c
    g = empty(name, parent)
    W, H, r = 260.0, 300.0, 34.0   # half window width (limb centres at cx -/+ W), half height
    lxs = (cx - W, cx + W)
    plates = 8
    parts = []
    for k in range(plates):
        za = cz - r + 2 * r * k / plates
        zb = cz - r + 2 * r * (k + 1) / plates - 0.8
        mt = m["core_a"] if k % 2 == 0 else m["core_b"]
        for j, lx in enumerate(lxs):
            parts.append(box(f"{name}_l{k}{j}", (lx - r, cy - H, za), (lx + r, cy + H, zb), mt, g))
        parts.append(box(f"{name}_yt{k}", (lxs[0] - r, cy + H - 2 * r, za), (lxs[1] + r, cy + H, zb), mt, g))
        parts.append(box(f"{name}_yb{k}", (lxs[0] - r, cy - H, za), (lxs[1] + r, cy - H + 2 * r, zb), mt, g))
    join(parts, f"{name}_core")

    def helix(x, y0, y1, rr, turns, per=24):
        n = int(turns * per)
        return [(x + rr * math.sin(2 * math.pi * k / per), y0 + (y1 - y0) * k / n, cz + rr * math.cos(2 * math.pi * k / per))
                for k in range(n + 1)]

    hv = helix(lxs[0], cy + H - 2 * r - 30.0, cy - H + 2 * r + 30.0, r + 26.0, hv_turns)
    lv = helix(lxs[1], cy - H + 2 * r + 60.0, cy + H - 2 * r - 60.0, r + 34.0, lv_turns)
    wire(f"{name}_hvcoil", hv, 4.0, m["copper"], g, 8)
    wire(f"{name}_lvcoil", lv, 13.0, m["copper"], g, 12)
    # leads out to terminals
    hv_in = [(lxs[0] - 220.0, hv[0][1] + 60.0, cz), (hv[0][0], hv[0][1] + 60.0, hv[0][2]), hv[0]]
    wire(f"{name}_hvin", hv_in, 4.0, m["copper"], g, 8)
    lv_out = [lv[-1], (lv[-1][0], lv[-1][1] + 90.0, lv[-1][2]), (lxs[1] + 240.0, lv[-1][1] + 90.0, cz)]
    wire(f"{name}_lvout", lv_out, 13.0, m["copper"], g, 12)
    zf = cz + r + 3.0
    ym_t, ym_b = cy + H - r, cy - H + r
    flux = [(lxs[0], ym_b, zf), (lxs[0], ym_t, zf), (lxs[1], ym_t, zf), (lxs[1], ym_b, zf), (lxs[0], ym_b, zf)]
    return {"g": g, "hv": hv_in + hv[1:], "lv": lv + lv_out[1:], "flux": flux, "hv_coil": hv, "lv_coil": lv,
            "lxs": lxs, "r": r, "H": H, "W": W}


def week_row(m, parent, x0, y, z, weeks, unit, mt, name, f0, f1, end, per=4, depth=36.0):
    """A row of blocks, one per `per` weeks (`unit` wide each week), popping on left to right
    between frames f0 and f1, staying until `end`. Returns the row's end point."""
    n = int(math.ceil(weeks / per))
    blocks = []
    for k in range(n):
        wk = min(per, weeks - per * k)
        xa = x0 + unit * per * k
        xb = xa + unit * wk - 2.0
        e = empty(f"{name}_{k}", parent)
        box(f"{name}_{k}_b", (xa, y, z - depth), (xb, y + 26.0, z), mt, e)
        show(e, [(round(f0 + (f1 - f0) * k / max(1, n - 1)), end)])
        blocks.append(e)
    return (x0 + unit * weeks, y + 26.0, z - depth / 2)


def week_ruler(m, parent, x0, y, z, weeks, unit, name):
    """A dark base strip with a tick every 52 weeks (one year)."""
    parts = [box(f"{name}_strip", (x0 - 10.0, y - 8.0, z - 50.0), (x0 + unit * weeks + 10.0, y, z + 8.0), m["week"], parent)]
    for k in range(int(weeks // 52) + 1):
        x = x0 + unit * 52 * k
        parts.append(box(f"{name}_tick{k}", (x - 2.0, y, z - 4.0), (x + 2.0, y + 60.0, z + 4.0), m["white"], parent))
    return join(parts, name)


def ship(m, parent, at, name, s=1.0):
    """A heavy-lift ship: hull, deck, bridge house, crane posts. Returns its group (cargo goes on
    its deck at deck height 260*s above `at`)."""
    ox, oy, oz = at
    g = empty(name, parent)

    def A(p):
        return (ox + s * p[0], oy + s * p[1], oz + s * p[2])

    parts = [box(f"{name}_hull", A((-900, 0, -260)), A((900, 220, 0)), m["hull"], g),
             box(f"{name}_bow", A((900, 40, -230)), A((1050, 220, -30)), m["hull"], g),
             box(f"{name}_deck", A((-900, 220, -260)), A((1050, 260, 0)), m["deck"], g),
             box(f"{name}_bridge", A((-880, 260, -240)), A((-650, 560, -20)), m["white"], g),
             box(f"{name}_bwin", A((-650, 480, -220)), A((-646, 520, -40)), m["door"], g)]
    for k, x in enumerate((-450, 650)):
        parts.append(tube(f"{name}_post{k}", A((x, 260, -130)), A((x, 900, -130)), s * 22, m["cabinet"], g, 12))
        parts.append(tube(f"{name}_jib{k}", A((x, 860, -130)), A((x + (300 if k == 0 else -300), 620, -130)), s * 12, m["cabinet"], g, 10))
    join(parts, f"{name}_body")
    return g


# ---- camera ---------------------------------------------------------------------------------------

PANE = 0.53
GLIDE = 0.16


def frame(c, size, yaw=0.35, pitch=0.22, pad=1.12, min_d=120.0):
    """A pose that fits a subject `size` cm across, centred on c, in the left pane."""
    return (tuple(c), max(size / PANE * pad, min_d), yaw, pitch)


def _eye(t, d, yaw, pitch):
    cp, sp = math.cos(pitch), math.sin(pitch)
    return (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))


def camera_path(root, plan):
    """`plan`: one entry per beat, either a pose or a list of (u, pose) moves within the beat.
    Each pose is reached by u (gliding from the last one) and held with a slow push-in
    (fiber_laser_detail.camera_path)."""
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
