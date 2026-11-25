"""kit_plant: shared parts for the power-plant term scenes (TRM_GAS_TURBINE, TRM_FUEL_CELL, TRM_BESS).

Coordinates are the term scenes' poly space: x right, y up (mm), z toward the camera. Every builder
takes the materials dict m and a parent, builds its own group empty at `c` (children are in local
coordinates, relative to c) and returns that group, or a dict of groups and points.

API (name(args) -> returns):
  materials(m) -> m
      adds the plant_* materials and glows to m (call after C.setup).
  ground(m, parent, x0, x1, z0, z1, y=0.0) -> group
      a concrete pad, top at y.
  pipe(m, parent, name, pts, r, mt) -> group
      a round pipe through poly points pts (absolute, relative to parent origin).
  cyl(m, parent, name, c, r, h, mt, axis="y", verts=48) -> object
      a solid cylinder centred at c; axis "y" (default), "x" or "z".
  shell(m, parent, name, x0, x1, r0, r1, mt, a0=0.0, a1=2pi, n=48) -> object
      a tube along poly x from x0 to x1, outer radius r0, inner r1, over the angle arc a0..a1
      (a0=-pi, a1=0 keeps the z<0 half: a cut-away the camera on +z can see into).
  blades(m, parent, name, x, r_hub, r_tip, n, mt, w, phase=0.0) -> group
      a rotor ring of n radial blades at poly x, from r_hub to r_tip, tube radius w.
  gas_turbine(m, parent, name, c, L, r, cut=True) -> dict(group, rotor, flame, casing, pts)
      an axial gas turbine along x: inlet, 4 compressor stages, 10 combustor cans, 3 turbine stages,
      exhaust. cut=True leaves the back half of each casing open. rotor is the spinning group
      (its origin on the shaft), flame is the glow in the combustor (show/hide it per beat).
  generator(m, parent, name, c, L, r) -> group
      a generator on a shared shaft (along x) with a terminal box.
  hrsg(m, parent, name, c, w, h, d) -> group
      heat-recovery steam generator: finned casing box with an inlet on its base.
  stack(m, parent, name, c, h, r) -> group
      an exhaust stack standing on its base (y up).
  fc_cell(m, parent, name, c, w, d) -> dict(group, layers, top)
      one solid-oxide cell cut open at z = 0: interconnect, anode, electrolyte, cathode, interconnect
      (thicknesses exaggerated for reading).
  fc_stack(m, parent, name, c, w, d, n) -> dict(group, top)
      n cells stacked in y, each a steel-framed plate, with a gas manifold on the side.
  container(m, parent, name, c, L, W, H) -> group
      a 20 ft battery container standing on the pad, with a door on its +x end.
  cell_prism(m, parent, name, c, w, h, d) -> dict(group, layers, top)
      a prismatic LFP cell: casing cut open at its front, copper and aluminium foils with separators.
  rack(m, parent, name, c, cols, rows, cw, ch, cd) -> group
      a battery rack: cols x rows of cell trays on a steel frame.
  pcs(m, parent, name, c, w, h, d) -> group
      a power-conversion (inverter) cabinet with a vent grille.
  transformer(m, parent, name, c, w, h, d) -> group
      a pad-mount transformer: tank with three bushings on top.
"""

import math
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sand_overview as O  # noqa: E402
from sand_overview import P, empty, mat, tube  # noqa: E402

PI = math.pi
TWO_PI = 2 * math.pi


def materials(m):
    m["plant_casing"] = mat("plant_casing", (0.30, 0.33, 0.37), metal=0.6, rough=0.4)
    m["plant_rotor"] = mat("plant_rotor", (0.45, 0.47, 0.52), metal=0.9, rough=0.3)
    m["plant_blade"] = mat("plant_blade", (0.66, 0.68, 0.72), metal=0.95, rough=0.22)
    m["plant_hot"] = mat("plant_hot", (0.52, 0.34, 0.30), metal=0.8, rough=0.3)
    m["plant_steel"] = mat("plant_steel", (0.50, 0.52, 0.56), metal=0.9, rough=0.35)
    m["plant_concrete"] = mat("plant_concrete", (0.50, 0.50, 0.48), rough=0.95)
    m["plant_box"] = mat("plant_box", (0.86, 0.87, 0.85), rough=0.5)
    m["plant_door"] = mat("plant_door", (0.20, 0.36, 0.52), rough=0.5)
    m["plant_grid"] = mat("plant_grid", (0.14, 0.15, 0.17), rough=0.8)
    m["plant_anode"] = mat("plant_anode", (0.22, 0.22, 0.26), rough=0.6)
    m["plant_cathode"] = mat("plant_cathode", (0.45, 0.56, 0.36), rough=0.6)
    m["plant_ysz"] = mat("plant_ysz", (0.92, 0.90, 0.82), rough=0.5)
    m["plant_ic"] = mat("plant_ic", (0.60, 0.62, 0.66), metal=0.8, rough=0.35)
    m["plant_cu"] = mat("plant_cu", (0.85, 0.55, 0.30), metal=0.9, rough=0.3)
    m["plant_al"] = mat("plant_al", (0.80, 0.82, 0.86), metal=0.9, rough=0.3)
    m["plant_sep"] = mat("plant_sep", (0.92, 0.92, 0.90), rough=0.6)
    m["plant_flame"] = mat("plant_flame", (1.0, 0.62, 0.22), emit=(1.0, 0.55, 0.18), strength=3.0)
    m["plant_hotgas"] = mat("plant_hotgas", (1.0, 0.42, 0.16), emit=(1.0, 0.38, 0.12), strength=2.0)
    m["plant_steam"] = mat("plant_steam", (0.85, 0.92, 1.0), emit=(0.80, 0.90, 1.0), strength=1.5, alpha=0.8)
    m["plant_fuel"] = mat("plant_fuel", (0.35, 0.90, 1.0), emit=(0.30, 0.85, 1.0), strength=2.5)
    m["plant_air"] = mat("plant_air", (0.60, 0.80, 1.0), emit=(0.55, 0.78, 1.0), strength=2.0)
    m["plant_elec"] = mat("plant_elec", (1.0, 0.86, 0.30), emit=(1.0, 0.84, 0.28), strength=2.5)
    m["plant_ion"] = mat("plant_ion", (0.90, 0.50, 1.0), emit=(0.85, 0.45, 1.0), strength=2.5)
    m["plant_cool"] = mat("plant_cool", (0.40, 0.80, 1.0), emit=(0.35, 0.75, 1.0), strength=2.0)
    return m


# ---- shapes -----------------------------------------------------------------------------------


def _bx(name, lo, hi, mt, parent):
    a = tuple(min(lo[i], hi[i]) for i in range(3))
    b = tuple(max(lo[i], hi[i]) for i in range(3))
    return O.box(name, a, b, mt, parent)


def _mesh(name, verts, faces, mt, parent):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(P(*v)) for v in verts], [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mt)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    return o


def cyl(m, parent, name, c, r, h, mt, axis="y", verts=48):
    o = O.disc(name, c, r, h, mt, parent, verts)
    if axis == "x":
        o.rotation_euler = (0.0, PI / 2, 0.0)
    elif axis == "z":
        o.rotation_euler = (PI / 2, 0.0, 0.0)
    return o


def shell(m, parent, name, x0, x1, r0, r1, mt, a0=0.0, a1=TWO_PI, n=48):
    """A tube along poly x (see the module doc)."""
    full = a1 - a0 >= TWO_PI - 1e-6
    angs = [a0 + (a1 - a0) * i / n for i in range(n if full else n + 1)]
    k = len(angs)
    verts, idx = [], {}

    def vid(kind, xi, ai):
        key = (kind, xi, ai % k)
        if key not in idx:
            a = angs[ai % k]
            r = r0 if kind == 0 else r1
            x = x0 if xi == 0 else x1
            idx[key] = len(verts)
            verts.append((x, r * math.cos(a), r * math.sin(a)))
        return idx[key]

    faces = []
    steps = range(k) if full else range(k - 1)
    for i in steps:
        j = i + 1
        faces.append([vid(0, 0, i), vid(0, 0, j), vid(0, 1, j), vid(0, 1, i)])
        faces.append([vid(1, 0, i), vid(1, 1, i), vid(1, 1, j), vid(1, 0, j)])
        for xi in (0, 1):
            faces.append([vid(0, xi, i), vid(0, xi, j), vid(1, xi, j), vid(1, xi, i)])
    if not full:
        for ai in (0, k - 1):
            faces.append([vid(0, 0, ai), vid(0, 1, ai), vid(1, 1, ai), vid(1, 0, ai)])
    g = empty(name, parent, (0, 0, 0))
    return _mesh(name, verts, faces, mt, g)


# ---- ground and pipes -------------------------------------------------------------------------


def ground(m, parent, x0, x1, z0, z1, y=0.0):
    g = empty("pad", parent)
    _bx("pad_slab", (x0, y - 8.0, z0), (x1, y, z1), m["plant_concrete"], g)
    return g


def pipe(m, parent, name, pts, r, mt):
    g = empty(name, parent)
    for k in range(len(pts) - 1):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, mt, g, 12)
        if k:
            O.ball(f"{name}_j{k}", pts[k], r, mt, g, 8)
    return g


# ---- gas turbine ------------------------------------------------------------------------------


def blades(m, parent, name, x, r_hub, r_tip, n, mt, w, phase=0.0):
    g = empty(name, parent)
    for j in range(n):
        a = phase + TWO_PI * j / n
        hub = (x, r_hub * math.cos(a), r_hub * math.sin(a))
        tip = (x, r_tip * math.cos(a), r_tip * math.sin(a))
        tube(f"{name}_b{j}", hub, tip, w, mt, g, 6)
    return g


def gas_turbine(m, parent, name, c, L, r, cut=True):
    g = empty(name, parent, P(*c))
    a0, a1 = (-PI, 0.0) if cut else (0.0, TWO_PI)
    casing = [
        shell(m, g, f"{name}_inlet", -L / 2, -0.40 * L, 1.06 * r, 0.96 * r, m["plant_casing"], a0, a1),
        shell(m, g, f"{name}_comp", -0.40 * L, -0.05 * L, 0.94 * r, 0.86 * r, m["plant_casing"], a0, a1),
        shell(m, g, f"{name}_comb", -0.05 * L, 0.20 * L, 1.14 * r, 1.04 * r, m["plant_casing"], a0, a1),
        shell(m, g, f"{name}_tcase", 0.20 * L, 0.42 * L, 1.00 * r, 0.90 * r, m["plant_casing"], a0, a1),
        shell(m, g, f"{name}_exh", 0.42 * L, L / 2, 1.10 * r, 1.00 * r, m["plant_casing"], a0, a1),
    ]
    rotor = empty(f"{name}_rotor", g)
    cyl(m, rotor, f"{name}_drum", (0.0, 0.0, 0.0), 0.30 * r, 0.9 * L, m["plant_rotor"], axis="x")
    for s in range(4):
        x = -0.38 * L + s * 0.10 * L
        tip = 0.80 * r * (1.0 - 0.05 * s)
        blades(m, rotor, f"{name}_c{s}", x, 0.36 * r, tip, 26, m["plant_blade"], 0.07 * r, phase=0.1 * s)
    for s in range(3):
        x = 0.24 * L + s * 0.09 * L
        tip = 0.86 * r * (1.0 - 0.04 * s)
        blades(m, rotor, f"{name}_t{s}", x, 0.42 * r, tip, 22, m["plant_hot"], 0.08 * r, phase=0.2 * s)
    cans = empty(f"{name}_cans", g)
    for j in range(10):
        a = TWO_PI * j / 10
        tube(f"{name}_can{j}", (-0.04 * L, 0.70 * r * math.cos(a), 0.70 * r * math.sin(a)),
             (0.16 * L, 0.70 * r * math.cos(a), 0.70 * r * math.sin(a)), 0.13 * r, m["plant_steel"], cans, 10)
    flame = cyl(m, g, f"{name}_flame", (0.06 * L, 0.0, 0.0), 0.42 * r, 0.20 * L, m["plant_flame"], axis="x", verts=24)
    pts = {"inlet": (-0.40 * L, 1.10 * r, 0.0), "comp": (-0.20 * L, 0.90 * r, 0.0),
           "comb": (0.04 * L, 1.18 * r, 0.0), "turb": (0.30 * L, 1.04 * r, 0.0),
           "shaft": (0.0, 0.0, 0.0), "exh": (0.46 * L, 1.14 * r, 0.0)}
    return {"group": g, "rotor": rotor, "flame": flame, "casing": casing, "pts": pts, "cans": cans}


def generator(m, parent, name, c, L, r):
    g = empty(name, parent, P(*c))
    cyl(m, g, f"{name}_body", (0.0, 0.0, 0.0), r, L, m["plant_casing"], axis="x", verts=64)
    cyl(m, g, f"{name}_cap", (L / 2, 0.0, 0.0), r * 0.96, 0.02 * L, m["plant_steel"], axis="x", verts=64)
    _bx(f"{name}_term", (-L * 0.1, -r - 0.5 * r, -r * 0.6), (L * 0.2, -r * 0.05, r * 0.6), m["plant_steel"], g)
    return g


def hrsg(m, parent, name, c, w, h, d):
    g = empty(name, parent, P(*c))
    _bx(f"{name}_box", (-w / 2, 0.0, -d / 2), (w / 2, h, d / 2), m["plant_casing"], g)
    for i in range(int(h // 6)):
        y = 4.0 + 6.0 * i
        _bx(f"{name}_fin{i}", (-w / 2 - 2.0, y, -d / 2), (w / 2 + 2.0, y + 1.6, d / 2), m["plant_steel"], g)
    _bx(f"{name}_inlet", (-w * 0.35, -6.0, -d / 2 - 4.0), (w * 0.35, 2.0, -d / 2 + 2.0), m["plant_steel"], g)
    return g


def stack(m, parent, name, c, h, r):
    g = empty(name, parent, P(*c))
    g.rotation_euler = (0.0, -PI / 2, 0.0)  # poly x -> poly y, so the shell below stands upright
    shell(m, g, f"{name}_shell", 0.0, h, r, r * 0.9, m["plant_casing"])
    return g


# ---- fuel cell --------------------------------------------------------------------------------


def fc_cell(m, parent, name, c, w, d):
    g = empty(name, parent, P(*c))
    bands = [("ic_lo", 0.0, 2.0, "plant_ic"), ("anode", 2.0, 5.0, "plant_anode"), ("ysz", 5.0, 5.6, "plant_ysz"),
             ("cathode", 5.6, 8.0, "plant_cathode"), ("ic_hi", 8.0, 10.0, "plant_ic")]
    layers = {}
    for nm, y0, y1, mk in bands:
        layers[nm] = _bx(f"{name}_{nm}", (-w / 2, y0, -d), (w / 2, y1, 0.0), m[mk], g)
    # gas channels cut into the top interconnect: fuel one way, air the other
    for k in range(5):
        x = -w / 2 + w * (k + 0.5) / 5
        _bx(f"{name}_chan{k}", (x - 1.2, 10.0, -d + 2.0), (x + 1.2, 10.6, -2.0), m["plant_ic"], g)
    top = (0.0, 10.6, -d / 2)
    return {"group": g, "layers": layers, "top": top}


def fc_stack(m, parent, name, c, w, d, n):
    g = empty(name, parent, P(*c))
    pitch = 5.0
    for i in range(n):
        y = i * pitch
        _bx(f"{name}_plate{i}", (-w / 2, y, -d / 2), (w / 2, y + 1.6, d / 2), m["plant_ic"], g)
        _bx(f"{name}_cell{i}", (-w / 2 + 3.0, y + 1.6, -d / 2 + 3.0), (w / 2 - 3.0, y + 2.6, d / 2 - 3.0),
            m["plant_anode"], g)
    top_y = n * pitch
    _bx(f"{name}_cap", (-w / 2 - 2.0, top_y, -d / 2 - 2.0), (w / 2 + 2.0, top_y + 2.0, d / 2 + 2.0), m["plant_steel"], g)
    _bx(f"{name}_manifold", (w / 2 + 2.0, 0.0, -d * 0.25), (w / 2 + 8.0, top_y, -d * 0.05), m["plant_steel"], g)
    return {"group": g, "top": (0.0, top_y + 2.0, 0.0)}


# ---- battery ----------------------------------------------------------------------------------


def container(m, parent, name, c, L, W, H):
    g = empty(name, parent, P(*c))
    _bx(f"{name}_body", (-L / 2, 0.0, -W / 2), (L / 2, H, W / 2), m["plant_box"], g)
    _bx(f"{name}_door", (L / 2, 0.8, -W * 0.46), (L / 2 + 1.0, H - 0.8, W * 0.46), m["plant_door"], g)
    for i in range(6):
        z = -W * 0.4 + W * 0.8 * i / 5
        _bx(f"{name}_louv{i}", (-L / 2 - 1.0, H * 0.6, z - 0.8), (-L / 2, H * 0.72, z + 0.8), m["plant_grid"], g)
    return g


def cell_prism(m, parent, name, c, w, h, d):
    g = empty(name, parent, P(*c))
    t = 1.2
    _bx(f"{name}_back", (-w / 2, 0.0, -d / 2), (w / 2, h, -d / 2 + t), m["plant_steel"], g)
    _bx(f"{name}_top", (-w / 2, h - t, -d / 2), (w / 2, h, d / 2), m["plant_steel"], g)
    _bx(f"{name}_bot", (-w / 2, 0.0, -d / 2), (w / 2, t, d / 2), m["plant_steel"], g)
    for side in (-1, 1):
        _bx(f"{name}_side{side}", (side * w / 2 - t * side, 0.0, -d / 2), (side * w / 2, h, d / 2), m["plant_steel"], g)
    layers = []
    n = 9
    for i in range(n):
        z = -d / 2 + t + (d - 2 * t) * (i + 0.5) / n
        layers.append(_bx(f"{name}_cu{i}", (-w / 2 + 2.5, 2.5, z - 0.3), (w / 2 - 6.0, h - 3.0, z + 0.3), m["plant_cu"], g))
        layers.append(_bx(f"{name}_sep{i}", (-w / 2 + 2.0, 2.0, z + 0.9), (w / 2 - 5.5, h - 2.0, z + 1.2), m["plant_sep"], g))
        layers.append(_bx(f"{name}_al{i}", (-w / 2 + 6.0, 3.5, z + 1.8), (w / 2 - 2.5, h - 3.5, z + 2.4), m["plant_al"], g))
    cyl(m, g, f"{name}_post_l", (-w * 0.25, h + 0.5, 0.0), 1.4, 1.0, m["plant_cu"])
    cyl(m, g, f"{name}_post_r", (w * 0.25, h + 0.5, 0.0), 1.4, 1.0, m["plant_al"])
    return {"group": g, "layers": layers, "top": (0.0, h + 1.0, 0.0)}


def rack(m, parent, name, c, cols, rows, cw, ch, cd):
    g = empty(name, parent, P(*c))
    W, H = cols * cw, rows * ch
    for i in range(2):
        for j in range(2):
            x = -W / 2 + (W - 1.6) * i
            z = -cd / 2 + (cd - 1.6) * j
            _bx(f"{name}_post{i}{j}", (x, 0.0, z), (x + 1.6, H + 1.0, z + 1.6), m["plant_steel"], g)
    for r_ in range(rows):
        for k in range(cols):
            x0 = -W / 2 + k * cw + 1.0
            y0 = r_ * ch + 1.0
            _bx(f"{name}_cell{r_}_{k}", (x0, y0, -cd * 0.4), (x0 + cw - 2.0, y0 + ch - 2.0, cd * 0.4), m["plant_cathode"] if (r_ + k) % 2 else m["plant_steel"], g)
    return g


def pcs(m, parent, name, c, w, h, d):
    g = empty(name, parent, P(*c))
    _bx(f"{name}_box", (-w / 2, 0.0, -d / 2), (w / 2, h, d / 2), m["plant_box"], g)
    for i in range(6):
        y = h * 0.2 + h * 0.6 * i / 5
        _bx(f"{name}_grille{i}", (-w * 0.38, y, d / 2), (w * 0.38, y + 1.2, d / 2 + 0.8), m["plant_grid"], g)
    return g


def transformer(m, parent, name, c, w, h, d):
    g = empty(name, parent, P(*c))
    _bx(f"{name}_tank", (-w / 2, 0.0, -d / 2), (w / 2, h, d / 2), m["plant_steel"], g)
    for i in (-1, 0, 1):
        cyl(m, g, f"{name}_bush{i}", (i * w * 0.28, h + 3.0, 0.0), 1.6, 6.0, m["plant_grid"], verts=20)
    return g
