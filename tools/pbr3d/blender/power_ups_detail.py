"""Part builders, cables, beads and camera for the POWER tab's UPS page (power_ups_overview.py,
power_ups_zooms.py, power_ups_sections.py).

Units: 1 scene unit = 1 cm, Y up, camera on +z, cut-away at z = 0 (docs/diagram-pages.md). At this
scale a UPS cabinet is 2 m (200 units) tall and a 2-3 MW generator about 5.6 m long, so the camera
always sits well outside pbr3d's 40-unit near plane; the small parts a close-up needs (an IGBT
module, a lithium-ion cell, a VRLA block) are built again on a "bench" at scale `s`.

The site (plant): the utility line comes in on a pole, the diesel GENERATOR stands on its skid
with the belly fuel tank, the automatic TRANSFER SWITCH picks one of them, and the UPS lineup does
the double conversion: RECTIFIER (input inductor, IGBT bridge on a heatsink), DC LINK (capacitors cut
open to their rolled foil), INVERTER (IGBT bridge, output filter), STATIC BYPASS switch (thyristor
pucks), then the LITHIUM-ION battery cabinets on the DC bus and the racks on an overhead busway.

Cables are arched, segmented tubes; power flow is glowing beads riding them (`cable`, `flow`), the
way fiber_photodiode_detail.py draws its wires. Colours: yellow AC from the utility, cyan DC,
orange battery power, green generator power, red a dead line.
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, BEAT_FRAMES, box, tube, ball, cut, key, show, fly, empty, along, _smooth  # noqa: E402
from pbr_kit import mat  # noqa: E402

# ---- materials --------------------------------------------------------------------------------


def materials():
    return {
        "cab": mat("ups_cab", (0.56, 0.59, 0.63), metal=0.5, rough=0.45),
        "cab_back": mat("ups_cab_back", (0.30, 0.32, 0.36), metal=0.3, rough=0.6),
        "cab_dark": mat("ups_cab_dark", (0.13, 0.14, 0.16), metal=0.3, rough=0.6),
        "batt_cab": mat("ups_batt_cab", (0.22, 0.24, 0.28), metal=0.4, rough=0.5),
        "copper": mat("ups_copper", (0.86, 0.50, 0.28), metal=0.9, rough=0.3),
        "enamel": mat("ups_enamel", (0.62, 0.30, 0.16), metal=0.6, rough=0.4),
        "core": mat("ups_core", (0.34, 0.36, 0.40), metal=0.6, rough=0.4),
        "fin": mat("ups_fin", (0.76, 0.78, 0.81), metal=0.8, rough=0.3),
        "module": mat("ups_module", (0.10, 0.10, 0.12), rough=0.5),
        "dbc": mat("ups_dbc", (0.90, 0.88, 0.82), rough=0.6),
        "die": mat("ups_die", (0.28, 0.31, 0.40), metal=0.5, rough=0.3),
        "gold": mat("ups_gold", (0.86, 0.72, 0.32), metal=0.9, rough=0.3),
        "alwire": mat("ups_alwire", (0.82, 0.84, 0.88), metal=0.9, rough=0.25),
        "pcb": mat("ups_pcb", (0.10, 0.34, 0.20), rough=0.7),
        "chip": mat("ups_chip", (0.06, 0.06, 0.07), rough=0.5),
        "can": mat("ups_can", (0.72, 0.74, 0.78), metal=0.85, rough=0.3),
        "cap_top": mat("ups_cap_top", (0.12, 0.12, 0.14), rough=0.6),
        "foil": mat("ups_foil", (0.82, 0.84, 0.88), metal=0.9, rough=0.25),
        "paper": mat("ups_paper", (0.86, 0.78, 0.58), rough=0.7),
        "cell": mat("ups_cell", (0.26, 0.42, 0.70), metal=0.5, rough=0.35),
        "cell_lid": mat("ups_cell_lid", (0.75, 0.77, 0.80), metal=0.8, rough=0.3),
        "anode": mat("ups_anode", (0.10, 0.10, 0.11), rough=0.6),
        "cathode": mat("ups_cathode", (0.36, 0.38, 0.44), metal=0.3, rough=0.45),
        "sep": mat("ups_sep", (0.93, 0.93, 0.90), rough=0.7),
        "lead": mat("ups_lead", (0.50, 0.52, 0.55), metal=0.8, rough=0.35),
        "pbo2": mat("ups_pbo2", (0.42, 0.22, 0.14), rough=0.7),
        "agm": mat("ups_agm", (0.88, 0.88, 0.84), rough=0.9),
        "vrla": mat("ups_vrla", (0.18, 0.18, 0.20), rough=0.6),
        "engine": mat("ups_engine", (0.24, 0.34, 0.30), metal=0.4, rough=0.45),
        "engine_cut": mat("ups_engine_cut", (0.58, 0.60, 0.63), metal=0.6, rough=0.4),
        "bore": mat("ups_bore", (0.10, 0.10, 0.11), metal=0.4, rough=0.5),
        "piston": mat("ups_piston", (0.80, 0.82, 0.85), metal=0.9, rough=0.25),
        "rod": mat("ups_rod", (0.52, 0.54, 0.58), metal=0.8, rough=0.35),
        "alt": mat("ups_alt", (0.20, 0.30, 0.46), metal=0.4, rough=0.45),
        "radiator": mat("ups_radiator", (0.26, 0.27, 0.29), metal=0.5, rough=0.5),
        "fuel": mat("ups_fuel", (0.80, 0.52, 0.12), rough=0.35),
        "tank": mat("ups_tank", (0.17, 0.18, 0.20), metal=0.4, rough=0.55),
        "skid": mat("ups_skid", (0.10, 0.10, 0.11), metal=0.4, rough=0.6),
        "exhaust": mat("ups_exhaust", (0.44, 0.40, 0.36), metal=0.7, rough=0.5),
        "concrete": mat("ups_concrete", (0.46, 0.46, 0.44), rough=0.95),
        "floor": mat("ups_floor", (0.26, 0.27, 0.29), rough=0.8),
        "pole": mat("ups_pole", (0.40, 0.28, 0.16), rough=0.85),
        "insulator": mat("ups_insulator", (0.70, 0.78, 0.84), rough=0.3),
        "cable": mat("ups_cable", (0.09, 0.09, 0.10), rough=0.55),
        "server": mat("ups_server", (0.15, 0.16, 0.18), metal=0.4, rough=0.45),
        "rack": mat("ups_rack", (0.06, 0.06, 0.07), metal=0.4, rough=0.5),
        "busway": mat("ups_busway", (0.58, 0.60, 0.64), metal=0.7, rough=0.35),
        "led": mat("ups_led", (0.35, 1.0, 0.55), emit=(0.3, 1.0, 0.5), strength=3.5),
        "led_off": mat("ups_led_off", (0.08, 0.14, 0.10), rough=0.5),
        "led_red": mat("ups_led_red", (1.0, 0.15, 0.10), emit=(1.0, 0.12, 0.08), strength=4.0),
        "gpu_hot": mat("ups_gpu_hot", (1.0, 0.85, 0.40), emit=(1.0, 0.8, 0.35), strength=5.0),
        "truck": mat("ups_truck", (0.70, 0.18, 0.12), metal=0.4, rough=0.4),
        "tyre": mat("ups_tyre", (0.05, 0.05, 0.05), rough=0.8),
        "glass": mat("ups_glass", (0.30, 0.40, 0.48), metal=0.6, rough=0.15),
        # moving things: beads riding the cables, heat, smoke, sparks
        "ac": mat("ups_ac", (1.0, 0.86, 0.25), emit=(1.0, 0.82, 0.2), strength=6.0),
        "dc": mat("ups_dc", (0.30, 0.85, 1.0), emit=(0.25, 0.85, 1.0), strength=6.0),
        "bat": mat("ups_bat", (1.0, 0.50, 0.15), emit=(1.0, 0.45, 0.10), strength=6.0),
        "gen": mat("ups_gen", (0.45, 1.0, 0.35), emit=(0.40, 1.0, 0.30), strength=6.0),
        "fault": mat("ups_fault", (1.0, 0.12, 0.08), emit=(1.0, 0.10, 0.06), strength=4.0),
        "heat": mat("ups_heat", (1.0, 0.36, 0.10), emit=(1.0, 0.32, 0.08), strength=3.0),
        "smoke": mat("ups_smoke", (0.36, 0.36, 0.38), rough=0.9),
        "spark": mat("ups_spark", (1.0, 0.95, 0.85), emit=(1.0, 0.95, 0.85), strength=12.0),
        "signal": mat("ups_signal", (1.0, 0.40, 0.90), emit=(1.0, 0.35, 0.90), strength=6.0),
        "wave_dirty": mat("ups_wave_dirty", (1.0, 0.45, 0.15), emit=(1.0, 0.4, 0.12), strength=4.0),
        "wave_clean": mat("ups_wave_clean", (0.40, 1.0, 0.60), emit=(0.35, 1.0, 0.55), strength=4.0),
        "conduct": mat("ups_conduct", (1.0, 0.86, 0.25), emit=(1.0, 0.82, 0.2), strength=3.0),
        "ghost": mat("ups_ghost", (0.18, 0.20, 0.24), rough=0.8),
    }


# ---- shapes -------------------------------------------------------------------------------------


def _mesh(name, vs, faces, m, parent):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in vs], [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    _smooth(o)
    return o


def _ring(name, axis, c, a0, a1, ro, ri, m, parent, half, verts):
    """A hollow cylinder along `axis` ('x' or 'y') from a0 to a1, its axis through c (the other two
    coordinates). `half` keeps only the back half (z <= c's z) and closes the two cut faces."""
    t0, t1 = (math.pi, 2 * math.pi) if half else (0.0, 2 * math.pi)
    n = verts // 2 if half else verts
    ang = [t0 + (t1 - t0) * i / n for i in range(n + 1 if half else n)]
    ri = max(ri, 0.01)

    def pt(a, r, t):
        if axis == "x":
            return P(a, c[0] + r * math.cos(t), c[1] + r * math.sin(t))
        return P(c[0] + r * math.cos(t), a, c[1] + r * math.sin(t))

    rings = [(a0, ro), (a1, ro), (a1, ri), (a0, ri)]
    vs = [pt(a, r, t) for a, r in rings for t in ang]
    k = len(ang)
    faces = []
    for a in range(4):
        b = (a + 1) % 4
        for i in (range(k - 1) if half else range(k)):
            j = (i + 1) % k
            faces.append((a * k + i, a * k + j, b * k + j, b * k + i))
    if half:
        for i in (0, k - 1):
            faces.append(tuple(a * k + i for a in range(4)))
    return _mesh(name, vs, faces, m, parent)


def ring_x(name, cy, cz, x0, x1, ro, ri, m, parent=None, half=True, verts=40):
    """A hollow cylinder lying along x (axis at y = cy, z = cz); `half` cuts it at z = cz."""
    return _ring(name, "x", (cy, cz), x0, x1, ro, ri, m, parent, half, verts)


def ring_y(name, cx, cz, y0, y1, ro, ri, m, parent=None, half=True, verts=40):
    """A hollow cylinder standing on y (axis at x = cx, z = cz); `half` cuts it at z = cz."""
    return _ring(name, "y", (cx, cz), y0, y1, ro, ri, m, parent, half, verts)


def rod(name, a, b, r, m, parent=None, half=False, verts=20, zc=0.0):
    """A solid cylinder a -> b, cut at z = zc when `half`."""
    o = tube(name, a, b, r, m, parent, verts)
    return cut(o, zc) if half else o


def join(objs, name):
    """Merge meshes (same parent) into one object, for fewer objects in the GLB."""
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


def arch(a, b, lift, n=12):
    """Points on an arched cable from a to b, bowed by the vector `lift` at the middle."""
    out = []
    for k in range(n + 1):
        u = k / n
        w = 4 * u * (1 - u)
        out.append(tuple(a[i] + (b[i] - a[i]) * u + lift[i] * w for i in range(3)))
    return out


def cable(name, pts, r, m, parent=None, verts=10):
    """A cable through `pts`: a tube per segment and a ball at each joint, merged into one mesh.
    Returns the points (the path beads ride)."""
    cable_obj(name, pts, r, m, parent, verts)
    return pts


def cable_obj(name, pts, r, m, parent=None, verts=10):
    parts = []
    for k in range(len(pts) - 1):
        if math.dist(pts[k], pts[k + 1]) < 1e-3:
            continue
        parts.append(tube(f"{name}_{k}", pts[k], pts[k + 1], r, m, parent, verts))
        if k:
            parts.append(ball(f"{name}_j{k}", pts[k], r, m, parent, 8))
    return join(parts, name)


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def flow(parent, name, pts, m, runs, n=7, size=5.0, speed=9.0):
    """Beads riding the absolute polyline `pts`. `runs` is a list of (beat, u0, u1): during each, the
    n beads set off one after another between fractions u0 and u1 of that beat, each taking
    length / speed frames, and vanish at the end of their trip or the beat. The same beads are reused
    for every run, so a flow costs n objects however many beats it plays in."""
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    life = min(150, max(24, round(plen(pts) / speed)))
    steps = max(6, len(pts) * 2)
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, m, e, 10)
        vis = []
        for b, u0, u1 in runs:
            f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
            f1 = f0 + life
            fly(e, path, f0, f1, steps=steps)
            vis.append((f0, min(f1, F(b + 1, 0))))
        show(e, vis)
    return g


def rise(parent, name, base, m, runs, n=6, size=3.0, height=80.0, spread=(30.0, 10.0), seed=1):
    """Blobs (heat, smoke) rising `height` from around `base` during each (beat, u0, u1) run."""
    g = empty(name, parent)
    for k in range(n):
        dx = spread[0] * (((k * 37 + seed * 11) % 13) / 12.0 - 0.5)
        dz = spread[1] * (((k * 53 + seed * 7) % 11) / 10.0 - 0.5)
        p0 = (base[0] + dx, base[1], base[2] + dz)
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", p0, size * (0.8 + 0.4 * ((k * 7) % 5) / 4), m, e, 8)
        vis = []
        for b, u0, u1 in runs:
            f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
            f1 = f0 + 50
            fly(e, [(0, 0, 0), (dx * 0.3, height * 0.5, 0), (dx * 0.6, height, 0)], f0, f1, steps=4)
            vis.append((f0, min(f1, F(b + 1, 0))))
        show(e, vis)
    return g


def level_show(obj, frames_levels, threshold):
    """Show `obj` while a piecewise-linear level (list of (frame, level)) is above `threshold`."""
    fl = sorted(frames_levels)
    vis, on, start = [], False, 0
    f_end = fl[-1][0]
    for f in range(fl[0][0], f_end + 1, 2):
        lv = fl[0][1]
        for (fa, la), (fb, lb) in zip(fl, fl[1:]):
            if fa <= f <= fb:
                lv = la + (lb - la) * ((f - fa) / max(1, fb - fa))
                break
        if lv > threshold and not on:
            on, start = True, f
        elif lv <= threshold and on:
            on = False
            vis.append((start, f))
    if on:
        vis.append((start, f_end))
    show(obj, vis)


# ---- camera (as fiber_laser_detail.py) ------------------------------------------------------------

PANE = 0.53
GLIDE = 0.16


def frame(c, size, yaw=0.35, pitch=0.22, pad=1.08, min_d=70.0):
    """A pose that fits a subject `size` units across, centred on c, in the left pane."""
    return (tuple(c), max(size / PANE * pad, min_d), yaw, pitch)


def _eye(t, d, yaw, pitch):
    cp, sp = math.cos(pitch), math.sin(pitch)
    return (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))


def camera_path(root, plan):
    """One pose per beat (or a list of (u, pose) moves in a beat), held with a slow push-in."""
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


# ---- cabinets and their insides -------------------------------------------------------------------


def cabinet(m, parent, x0, x1, h, d, name, shell="cab"):
    """An enclosure with its front door off: back panel, sides, roof and plinth (front at z = 0)."""
    parts = [
        box(f"{name}_back", (x0, 0, -d), (x1, h, -d + 2), m["cab_back"], parent),
        box(f"{name}_sl", (x0, 0, -d), (x0 + 3, h, 0), m[shell], parent),
        box(f"{name}_sr", (x1 - 3, 0, -d), (x1, h, 0), m[shell], parent),
        box(f"{name}_roof", (x0, h - 3, -d), (x1, h, 0), m[shell], parent),
        box(f"{name}_plinth", (x0, 0, -d), (x1, 8, 0), m["cab_dark"], parent),
    ]
    return join(parts, name)


def inductor(m, parent, x0, x1, y0, y1, zc, name, depth=None):
    """A three-phase E-core inductor: laminated iron yokes and legs, a copper coil round each leg,
    cut on z = zc so the coil's turns and the iron show in section."""
    w = x1 - x0
    lw = w * 0.11
    yk = (y1 - y0) * 0.16
    depth = depth or lw * 1.6
    parts = [box(f"{name}_ytop", (x0, y1 - yk, zc - depth), (x1, y1, zc), m["core"], parent),
             box(f"{name}_ybot", (x0, y0, zc - depth), (x1, y0 + yk, zc), m["core"], parent)]
    coils = []
    for i, cx in enumerate((x0 + lw / 2 + 1, (x0 + x1) / 2, x1 - lw / 2 - 1)):
        parts.append(box(f"{name}_leg{i}", (cx - lw / 2, y0 + yk, zc - lw), (cx + lw / 2, y1 - yk, zc), m["core"], parent))
        ya, yb = y0 + yk + 1, y1 - yk - 1
        nt = 7
        for t in range(nt):
            a = ya + (yb - ya) * t / nt
            b = ya + (yb - ya) * (t + 1) / nt - 0.4
            coils.append(ring_y(f"{name}_c{i}_{t}", cx, zc - lw / 2, a, b, lw / 2 + w * 0.12, lw / 2 + 0.8,
                                m["copper" if t % 2 == 0 else "enamel"], parent, False, 28))
    # the coils' back halves sit behind the iron; cut them all on zc
    for c in coils:
        cut(c, zc + 0.3)
    join(parts, name + "_iron")
    join(coils, name + "_coils")
    return {"c": ((x0 + x1) / 2, (y0 + y1) / 2, zc)}


def heatsink(m, parent, x0, x1, y0, y1, zf, name, depth=26.0, fins=10):
    """An extruded aluminium heatsink: base plate facing +z at zf, fins running back."""
    parts = [box(f"{name}_base", (x0, y0, zf - 3), (x1, y1, zf), m["fin"], parent)]
    for i in range(fins):
        x = x0 + (x1 - x0) * (i + 0.5) / fins
        parts.append(box(f"{name}_f{i}", (x - 0.6, y0, zf - depth), (x + 0.6, y1, zf - 3), m["fin"], parent))
    return join(parts, name)


def igbt(m, parent, o, s, name, open_lid=True):
    """A power module (IGBTs and diodes) lying on its baseplate, lid off, seen from +z: copper
    baseplate, white DBC ceramic with copper islands, silicon dies, aluminium bond wires, terminals.
    Local size 14 x 6 (x, y), 1.5 deep (z), origin at its bottom-left-back corner `o`, scaled `s`."""
    ox, oy, oz = o

    def at(x, y, z):
        return (ox + s * x, oy + s * y, oz + s * z)

    parts = [box(f"{name}_base", at(0, 0, 0), at(14, 6, 0.4), m["copper"], parent),
             box(f"{name}_wl", at(0, 0, 0.4), at(0.4, 6, 1.6), m["module"], parent),
             box(f"{name}_wr", at(13.6, 0, 0.4), at(14, 6, 1.6), m["module"], parent),
             box(f"{name}_wb", at(0, 0, 0.4), at(14, 0.4, 1.6), m["module"], parent),
             box(f"{name}_wt", at(0, 5.6, 0.4), at(14, 6, 1.6), m["module"], parent)]
    if not open_lid:
        parts.append(box(f"{name}_lid", at(0, 0, 1.6), at(14, 6, 1.9), m["module"], parent))
    dies, wires = [], []
    for j in range(2):
        x0 = 0.9 + 6.5 * j
        parts.append(box(f"{name}_dbc{j}", at(x0, 0.8, 0.4), at(x0 + 5.8, 5.2, 0.6), m["dbc"], parent))
        parts.append(box(f"{name}_cu{j}", at(x0 + 0.3, 1.1, 0.6), at(x0 + 5.5, 4.9, 0.7), m["copper"], parent))
        for i in range(2):
            dx = x0 + 0.7 + 2.6 * i
            dies.append(box(f"{name}_igbt{j}{i}", at(dx, 2.9, 0.7), at(dx + 1.8, 4.5, 0.78), m["die"], parent))
            dies.append(box(f"{name}_diode{j}{i}", at(dx + 0.3, 1.4, 0.7), at(dx + 1.5, 2.5, 0.78), m["die"], parent))
            for w in range(3 if s >= 3 else 0):
                a = at(dx + 0.4 + 0.5 * w, 3.7, 0.78)
                b = at(dx + 0.4 + 0.5 * w, 5.3, 0.7)
                wires.append(cable_obj(f"{name}_w{j}{i}{w}", arch(a, b, (0, 0, 0.7 * s), 6), 0.06 * s, m["alwire"], parent, 6))
    tabs = [box(f"{name}_tab{k}", at(1.5 + 4.6 * k, 6, 0.4), at(3.5 + 4.6 * k, 7.2, 0.9), m["copper"], parent) for k in range(3)]
    join(parts + dies + tabs, name)
    if wires:
        join(wires, name + "_wires")
    return {"die": at(3.0, 3.7, 0.78), "dbc": at(4.5, 1.0, 0.6), "base": at(13, 0.2, 0.4), "tab": at(7, 7.2, 0.9),
            "wire": at(3.0, 4.6, 1.2)}


def capacitor(m, parent, cx, y0, cz, r, h, name, layers=6):
    """A can capacitor standing on y: aluminium can cut on z = cz to show the rolled foil and paper,
    a dark top with two terminals."""
    parts = [ring_y(f"{name}_can", cx, cz, y0, y0 + h, r, r - 0.8, m["can"], parent, True, 28)]
    step = (r - 0.8 - r * 0.22) / layers
    for i in range(layers):
        ro = r - 0.8 - i * step
        parts.append(ring_y(f"{name}_l{i}", cx, cz, y0 + 1, y0 + h - 1.5, ro, ro - step * 0.55, m["foil"], parent, True, 24))
        parts.append(ring_y(f"{name}_p{i}", cx, cz, y0 + 1, y0 + h - 1.5, ro - step * 0.55, ro - step, m["paper"], parent, True, 24))
    top = rod(f"{name}_top", (cx, y0 + h - 1.5, cz), (cx, y0 + h + 1.0, cz), r, m["cap_top"], parent, True, 24, cz)
    parts.append(top)
    for k, dx in enumerate((-r * 0.45, r * 0.45)):
        parts.append(tube(f"{name}_t{k}", (cx + dx, y0 + h + 1.0, cz - r * 0.4), (cx + dx, y0 + h + 3.0, cz - r * 0.4), 1.2, m["copper"], parent, 8))
    join(parts, name)
    return {"c": (cx, y0 + h * 0.5, cz), "top": (cx, y0 + h + 3.0, cz - r * 0.4)}


def pcb(m, parent, lo, hi, name, chips=4):
    parts = [box(f"{name}_b", lo, hi, m["pcb"], parent)]
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    for i in range(chips):
        y = y0 + (y1 - y0) * (i + 0.5) / chips
        parts.append(box(f"{name}_c{i}", ((x0 + x1) / 2 - 2.5, y - 1.5, z1), ((x0 + x1) / 2 + 2.5, y + 1.5, z1 + 0.6), m["chip"], parent))
    return join(parts, name)


# ---- the UPS lineup -------------------------------------------------------------------------------

H = 200.0   # cabinet height
D = 70.0    # cabinet depth
ZB = -22.0  # internal busbars (beads ride them) sit this far back, in front of the parts


def converter(m, parent, x0, x1, name, kind):
    """A RECTIFIER (kind 'rect': input inductor above an IGBT bridge) or an INVERTER ('inv': IGBT
    bridge below an output filter inductor and AC capacitors). Returns its points and bus path."""
    g = parent
    cabinet(m, g, x0, x1, H, D, name)
    w = x1 - x0
    heatsink(m, g, x0 + 8, x1 - 8, 22, 100, -40.0, f"{name}_hs", depth=26.0, fins=12)
    mods = []
    for r_ in range(2):
        for c_ in range(3):
            mx = x0 + 10 + c_ * (w - 20) / 3
            my = 28 + r_ * 36
            mods.append(igbt(m, g, (mx, my, -40.0), (w - 26) / 3 / 14.0, f"{name}_m{r_}{c_}"))
    pcb(m, g, (x0 + 6, 106, -50), (x1 - 6, 116, -48), f"{name}_ctl", 6)
    if kind == "rect":
        ind = inductor(m, g, x0 + 14, x1 - 14, 124, 182, -34.0, f"{name}_ind")
        brk = box(f"{name}_brk", (x0 + 8, 186, -40), (x0 + 30, 194, -10), m["cab_dark"], g)
        path = [(x0 + 20, H - 2, ZB), (x0 + 20, 186, ZB), (x0 + 20, 160, ZB), (x0 + 20, 100, ZB), (x1 - 20, 100, ZB),
                (x1 - 20, 160, ZB), (x1 - 20, H - 2, ZB)]
    else:
        ind = inductor(m, g, x0 + 14, x1 - 46, 124, 182, -34.0, f"{name}_ind")
        for k in range(2):
            capacitor(m, g, x1 - 26, 126 + 30 * k, -30.0, 8.0, 22.0, f"{name}_fc{k}", 4)
        path = [(x0 + 20, H - 2, ZB), (x0 + 20, 100, ZB), (x1 - 20, 100, ZB), (x1 - 20, 120, ZB), (x1 - 34, 160, ZB),
                (x1 - 20, H - 2, ZB)]
    cable(f"{name}_bus", path, 2.2, m["copper"], g, 8)
    pts = {"mod": (x0 + 10 + (w - 20) / 3 + 3, 64 + 4, -38.0), "hs": (x1 - 10, 60, -40.0), "ind": ind["c"],
           "top": ((x0 + x1) / 2, H, -30.0), "in": (x0 + 20, H, ZB), "out": (x1 - 20, H, ZB), "path": path,
           "heat": [((x0 + x1) / 2, 100, -55.0), ((x0 + x1) / 2, 182, -35.0)], "ctl": (x0 + 10, 111, -48), "mods": mods}
    return pts


def dc_link(m, parent, x0, x1, name):
    """The DC LINK: a cabinet of can capacitors, cut open, on a pair of copper DC busbars."""
    cabinet(m, parent, x0, x1, H, D, name)
    xs = [x0 + 16, x1 - 16]
    caps = []
    for i, cx in enumerate(xs):
        for j in range(4):
            caps.append(capacitor(m, parent, cx, 16 + 40 * j, -32.0, 11.0, 30.0, f"{name}_cap{i}{j}"))
    for k, y in enumerate((172.0, 178.0)):
        box(f"{name}_dcbus{k}", (x0 + 4, y, -26), (x1 - 4, y + 3, -22), m["copper"], parent)
    path = [(x0 + 12, H - 2, ZB), (x0 + 12, 186, ZB), (x1 - 12, 186, ZB), (x1 - 12, H - 2, ZB)]
    return {"cap": caps[2]["c"], "caps": caps, "bus": ((x0 + x1) / 2, 178, -22), "in": path[0], "out": path[-1], "path": path,
            "batt": ((x0 + x1) / 2, H, -50.0), "top": ((x0 + x1) / 2, H, -30.0)}


def puck(m, parent, cx, cy, cz, r, name):
    """A press-pack thyristor ('hockey puck') standing on y, cut on z = cz: ceramic ring, copper
    pole pieces and the silicon wafer between them."""
    parts = [ring_y(f"{name}_cer", cx, cz, cy - 3, cy + 3, r, r - 1.5, m["dbc"], parent, True, 28),
             rod(f"{name}_pl", (cx, cy - 4.5, cz), (cx, cy - 0.4, cz), r - 1.6, m["copper"], parent, True, 24, cz),
             rod(f"{name}_si", (cx, cy - 0.4, cz), (cx, cy + 0.4, cz), r - 2.4, m["die"], parent, True, 24, cz),
             rod(f"{name}_pu", (cx, cy + 0.4, cz), (cx, cy + 4.5, cz), r - 1.6, m["copper"], parent, True, 24, cz)]
    return join(parts, name)


def static_switch(m, parent, x0, x1, name):
    """The STATIC BYPASS switch: two anti-parallel thyristor pucks clamped between heatsinks, and
    the conducting glow (a group, hidden until shown)."""
    cabinet(m, parent, x0, x1, H, D, name)
    cx = (x0 + x1) / 2
    for k, cy in enumerate((80.0, 130.0)):
        heatsink(m, parent, x0 + 6, x1 - 6, cy - 16, cy - 5, -20.0, f"{name}_hs{k}a", 30.0, 6)
        puck(m, parent, cx, cy, -32.0, 12.0, f"{name}_scr{k}")
        heatsink(m, parent, x0 + 6, x1 - 6, cy + 5, cy + 16, -20.0, f"{name}_hs{k}b", 30.0, 6)
    pcb(m, parent, (x0 + 6, 160, -60), (x1 - 6, 176, -58), f"{name}_ctl", 3)
    glow = empty(f"{name}_on", parent)
    for k, cy in enumerate((80.0, 130.0)):
        rod(f"{name}_on{k}", (cx, cy - 0.5, -32.0), (cx, cy + 0.5, -32.0), 9.8, m["conduct"], glow, True, 24, -31.6)
    path = [(cx - 12, H - 2, ZB), (cx - 12, 40, ZB), (cx + 12, 40, ZB), (cx + 12, H - 2, ZB)]
    cable(f"{name}_bus", path, 2.0, m["copper"], parent, 8)
    return {"scr": (cx, 130.0, -32.0), "glow": glow, "in": path[0], "out": path[-1], "path": path, "top": (cx, H, -30.0)}


def ats(m, parent, x0, x1, name):
    """The automatic TRANSFER SWITCH: a utility contact (top), a generator contact (bottom), the
    moving blade on its pivot to the load terminal, a motor operator and the controller. Returns
    blade groups 'blade_u' and 'blade_g' (switch them with show) and the bus paths."""
    cabinet(m, parent, x0, x1, H, D, name)
    cu = (x0 + 16, 150.0, ZB)
    cg = (x0 + 16, 70.0, ZB)
    pv = (x1 - 22, 110.0, ZB)
    for k, c in enumerate((cu, cg)):
        box(f"{name}_ct{k}", (c[0] - 7, c[1] - 6, -36), (c[0] + 5, c[1] + 6, -18), m["copper"], parent)
        box(f"{name}_arc{k}", (c[0] - 9, c[1] - 9, -40), (c[0] - 7, c[1] + 9, -14), m["cab_dark"], parent)
    rod(f"{name}_pivot", (pv[0], pv[1], -40), (pv[0], pv[1], -14), 5.0, m["cab_dark"], parent, False, 16)
    box(f"{name}_motor", (x1 - 34, 26, -50), (x1 - 8, 50, -20), m["cab_dark"], parent)
    rod(f"{name}_motor_ax", (x1 - 21, 50, -35), (x1 - 21, 105, -35), 2.0, m["rod"], parent, False, 10)
    ctl = box(f"{name}_ctl", (x0 + 6, 172, -40), (x1 - 6, 190, -30), m["cab_dark"], parent)
    leds = {}
    for k, (nm, mt) in enumerate((("u", "led"), ("g", "led"))):
        g = empty(f"{name}_led_{nm}", parent)
        ball(f"{name}_led_{nm}_b", (x0 + 16 + 14 * k, 181, -29), 2.2, m[mt], g, 10)
        leds[nm] = g
    blades = {}
    for nm, c in (("u", cu), ("g", cg)):
        g = empty(f"{name}_blade_{nm}", parent)
        tube(f"{name}_blade_{nm}_t", (c[0] + 4, c[1], -20), (pv[0], pv[1], -20), 2.6, m["copper"], g, 10)
        blades[nm] = g
    # entries: utility from the top-left, generator into the left side low; load out the top-right
    bus_u = [(x0 + 16, H - 2, ZB), (x0 + 16, cu[1] + 6, ZB)]
    bus_g = [(x0 + 3, cg[1], ZB), (cg[0] - 7, cg[1], ZB)]
    bus_o = [(pv[0], pv[1], ZB), (pv[0], H - 2, ZB)]
    cable(f"{name}_bu", bus_u, 2.2, m["copper"], parent, 8)
    cable(f"{name}_bo", bus_o, 2.2, m["copper"], parent, 8)
    path_u = bus_u + [(cu[0], cu[1], ZB), (pv[0], pv[1], ZB)] + bus_o[1:]
    path_g = bus_g + [(cg[0], cg[1], ZB), (pv[0], pv[1], ZB)] + bus_o[1:]
    return {"cu": cu, "cg": cg, "pv": pv, "blade_u": blades["u"], "blade_g": blades["g"], "path_u": path_u,
            "path_g": path_g, "in_u": bus_u[0], "in_g": bus_g[0], "out": bus_o[-1], "ctl": (x0 + 20, 190, -35),
            "led_u": leds["u"], "led_g": leds["g"], "motor": (x1 - 21, 50, -20), "top": ((x0 + x1) / 2, H, -30.0)}


# ---- batteries --------------------------------------------------------------------------------------

MODS = 8


def li_cabinet(m, parent, x0, x1, name, cells=10):
    """A LITHIUM-ION cabinet: eight module trays of prismatic cells (cut on z = 0), each with its BMS
    board, and a state-of-charge LED per module. Returns the LEDs (index 0 = bottom)."""
    cabinet(m, parent, x0, x1, H, D, name, shell="batt_cab")
    leds = []
    w = x1 - x0 - 10
    for i in range(MODS):
        y = 12 + 22 * i
        parts = [box(f"{name}_tray{i}", (x0 + 5, y, -D + 4), (x1 - 5, y + 2, 0), m["cab_dark"], parent)]
        cw = (w - 12) / cells
        for c in range(cells):
            cx = x0 + 11 + c * cw
            parts.append(box(f"{name}_c{i}_{c}", (cx + 0.3, y + 2, -D + 8), (cx + cw - 0.3, y + 16, -4), m["cell"], parent))
            parts.append(box(f"{name}_cl{i}_{c}", (cx + 0.3, y + 16, -D + 8), (cx + cw - 0.3, y + 17, -4), m["cell_lid"], parent))
        parts.append(box(f"{name}_bms{i}", (x0 + 6, y + 2, -4), (x0 + 10, y + 18, -1), m["pcb"], parent))
        parts.append(box(f"{name}_bar{i}", (x0 + 11, y + 17, -12), (x1 - 6, y + 18, -8), m["copper"], parent))
        join(parts, f"{name}_mod{i}")
        box(f"{name}_ledoff{i}", (x0 + 6.5, y + 13, -1), (x0 + 9.5, y + 16, 0.2), m["led_off"], parent)
        g = empty(f"{name}_led{i}", parent)
        box(f"{name}_led{i}_b", (x0 + 6.3, y + 12.8, -1), (x0 + 9.7, y + 16.2, 0.6), m["led"], g)
        leds.append(g)
    box(f"{name}_dcbar", (x0 + 4, 192, -40), (x1 - 4, 195, -30), m["copper"], parent)
    return {"leds": leds, "top": ((x0 + x1) / 2, H, -35.0), "cells": ((x0 + x1) / 2, 100, 0.0), "mod": (x0 + 30, 12 + 22 * 5 + 10, 0.0)}


def soc(cabs, frames_levels):
    """Drive every cabinet's module LEDs from one charge level (0..1) over time."""
    for c in cabs:
        for i, g in enumerate(c["leds"]):
            level_show(g, frames_levels, (i + 0.5) / MODS)


def li_cell(m, parent, o, s, name):
    """A prismatic lithium-ion cell, cut open on z = o.z: aluminium can, the wound electrode stack
    (copper foil + graphite anode, separator, aluminium foil + oxide cathode), lid, terminals, vent.
    Local size 2.7 x 9 (x, y), 14.8 deep; origin at the bottom-left of the cut face."""
    ox, oy, oz = o

    def at(x, y, z):
        return (ox + s * x, oy + s * y, oz + s * z)

    parts = [box(f"{name}_wl", at(0, 0, -14.8), at(0.1, 8.4, 0), m["can"], parent),
             box(f"{name}_wr", at(2.6, 0, -14.8), at(2.7, 8.4, 0), m["can"], parent),
             box(f"{name}_wb", at(0, 0, -14.8), at(2.7, 0.1, 0), m["can"], parent),
             box(f"{name}_back", at(0, 0, -14.8), at(2.7, 8.4, -14.7), m["can"], parent),
             box(f"{name}_lid", at(0, 8.4, -14.8), at(2.7, 9.0, 0), m["cell_lid"], parent)]
    seq = ["copper", "anode", "sep", "cathode", "foil", "cathode", "sep", "anode"]
    x = 0.2
    t = 0.09
    k = 0
    layers = []
    while x + t <= 2.5:
        mt = seq[k % len(seq)]
        th = t * (0.5 if mt in ("copper", "foil", "sep") else 1.0)
        layers.append(box(f"{name}_L{k}", at(x, 0.4, -14.4), at(x + th, 7.6, 0), m[mt], parent))
        x += th
        k += 1
    for k, (xx, mt) in enumerate(((0.7, "foil"), (2.0, "copper"))):
        parts.append(box(f"{name}_term{k}", at(xx - 0.35, 9.0, -11.0), at(xx + 0.35, 9.6, -4.0), m[mt], parent))
    parts.append(rod(f"{name}_vent", at(1.35, 9.0, -7.5), at(1.35, 9.15, -7.5), 0.45 * s, m["cab_dark"], parent))
    join(parts, name)
    join(layers, name + "_stack")
    return {"stack": at(1.3, 4.0, 0), "anode": at(0.5, 2.0, 0), "sep": at(1.1, 6.0, 0), "cathode": at(1.8, 3.0, 0),
            "lid": at(1.35, 9.0, -7.5), "pos": at(0.7, 9.6, -7.5), "neg": at(2.0, 9.6, -7.5), "can": at(2.7, 1.0, 0)}


def vrla_block(m, parent, o, s, name, cells=6):
    """A VRLA lead-acid block cut open on z = o.z: plastic case, six cells, each a stack of lead
    grids (grey, negative) and lead dioxide plates (brown, positive) with glass-mat separators."""
    ox, oy, oz = o

    def at(x, y, z):
        return (ox + s * x, oy + s * y, oz + s * z)

    W, Hh, Dd = 30.0, 22.0, 17.0
    parts = [box(f"{name}_bot", at(0, 0, -Dd), at(W, 0.6, 0), m["vrla"], parent),
             box(f"{name}_back", at(0, 0, -Dd), at(W, Hh, -Dd + 0.6), m["vrla"], parent),
             box(f"{name}_lid", at(-0.3, Hh, -Dd), at(W + 0.3, Hh + 1.5, 0), m["vrla"], parent)]
    cw = W / cells
    plates = []
    for c in range(cells + 1):
        parts.append(box(f"{name}_wall{c}", at(c * cw - 0.3, 0, -Dd), at(c * cw + 0.3, Hh, 0), m["vrla"], parent))
    for c in range(cells):
        x = c * cw + 0.6
        k = 0
        while x + 0.55 < (c + 1) * cw - 0.4:
            mt = ("lead", "agm", "pbo2", "agm")[k % 4]
            th = 0.25 if mt == "agm" else 0.35
            plates.append(box(f"{name}_p{c}_{k}", at(x, 1.0, -Dd + 1), at(x + th, Hh - 2.5, 0), m[mt], parent))
            x += th
            k += 1
        parts.append(box(f"{name}_strap{c}", at(c * cw + 0.6, Hh - 2.5, -Dd + 1), at((c + 1) * cw - 0.6, Hh - 1.5, -2), m["lead"], parent))
    for k, xx in enumerate((3.0, W - 3.0)):
        parts.append(rod(f"{name}_post{k}", at(xx, Hh + 1.5, -Dd / 2), at(xx, Hh + 3.5, -Dd / 2), 1.0 * s, m["lead"], parent))
    join(parts, name)
    join(plates, name + "_plates")
    return {"plates": at(cw * 1.5, Hh * 0.5, 0), "case": at(W, Hh * 0.8, 0), "lid": at(W * 0.5, Hh + 1.5, -Dd / 2), "w": W * s, "h": Hh * s}


def vrla_cabinet(m, parent, x0, x1, name, rows=5):
    """A lead-acid battery cabinet: shelves of VRLA blocks, cut on z = 0."""
    cabinet(m, parent, x0, x1, H, D + 20, name, shell="batt_cab")
    parts = []
    for r_ in range(rows):
        y = 10 + r_ * 37
        parts.append(box(f"{name}_sh{r_}", (x0 + 3, y, -D - 16), (x1 - 3, y + 2, 0), m["cab_dark"], parent))
        n = 3
        bw = (x1 - x0 - 12) / n
        for k in range(n):
            bx = x0 + 6 + k * bw
            parts.append(box(f"{name}_b{r_}{k}", (bx + 0.6, y + 2, -D - 12), (bx + bw - 0.6, y + 30, -3), m["vrla"], parent))
            parts.append(box(f"{name}_bt{r_}{k}", (bx + 2, y + 30, -40), (bx + 5, y + 32, -30), m["lead"], parent))
            parts.append(box(f"{name}_bt2{r_}{k}", (bx + bw - 5, y + 30, -40), (bx + bw - 2, y + 32, -30), m["lead"], parent))
    join(parts, name + "_blocks")
    return {"top": ((x0 + x1) / 2, H, -35.0), "c": ((x0 + x1) / 2, 100, 0.0)}


# ---- the generator ----------------------------------------------------------------------------------

GEN_L = 560.0
GEN_W = 90.0   # half width (z)
AXIS_Y = 145.0


def generator(m, parent, x0, name, cut_open=True, fuel_y=48.0, zc=0.0):
    """A standby diesel GENERATOR set on its skid, cut open on z = 0: belly fuel tank, radiator and fan,
    an inline engine block with pistons, rods and crankshaft, the turbo and exhaust stack, the
    coupling, and the ALTERNATOR (stator with its windings, a salient-pole rotor). With cut_open False
    it is a closed enclosure (for rows of gensets). Returns moving groups and points."""
    x1 = x0 + GEN_L
    gp = {}
    if not cut_open:
        z = zc
        parts = [box(f"{name}_skid", (x0, 0, z - GEN_W), (x1, 12, z + GEN_W), m["skid"], parent),
                 box(f"{name}_tank", (x0, 12, z - GEN_W), (x1, 60, z + GEN_W), m["tank"], parent),
                 box(f"{name}_encl", (x0 + 4, 60, z - GEN_W + 4), (x1 - 4, 270, z + GEN_W - 4), m["engine"], parent)]
        for k in range(6):
            x = x0 + 60 + k * 70
            parts.append(box(f"{name}_louvre{k}", (x, 150, z + GEN_W - 4), (x + 40, 230, z + GEN_W - 2), m["radiator"], parent))
        parts.append(box(f"{name}_door", (x1 - 90, 70, z + GEN_W - 4), (x1 - 30, 230, z + GEN_W - 2.5), m["radiator"], parent))
        parts.append(rod(f"{name}_stack", (x0 + 330, 270, z), (x0 + 330, 340, z), 10.0, m["exhaust"], parent))
        join(parts, name)
        return {"top": ((x0 + x1) / 2, 270, z), "stack": (x0 + 330, 340, z), "c": ((x0 + x1) / 2, 140, z + GEN_W),
                "tank": ((x0 + x1) / 2, 36, z + GEN_W)}
    # skid and belly fuel tank (shell, with the fuel showing on the cut)
    tank = [box(f"{name}_skid", (x0, 0, -GEN_W), (x1, 12, 0), m["skid"], parent),
            box(f"{name}_tb", (x0 + 2, 12, -GEN_W), (x1 - 2, 15, 0), m["tank"], parent),
            box(f"{name}_tt", (x0 + 2, 57, -GEN_W), (x1 - 2, 60, 0), m["tank"], parent),
            box(f"{name}_tk", (x0 + 2, 12, -GEN_W), (x1 - 2, 60, -GEN_W + 3), m["tank"], parent),
            box(f"{name}_te0", (x0 + 2, 12, -GEN_W), (x0 + 5, 60, 0), m["tank"], parent),
            box(f"{name}_te1", (x1 - 5, 12, -GEN_W), (x1 - 2, 60, 0), m["tank"], parent)]
    join(tank, f"{name}_tank")
    fuel = empty(f"{name}_fuel", parent)
    box(f"{name}_fuel_b", (x0 + 5, 15, -GEN_W + 3), (x1 - 5, fuel_y, -0.5), m["fuel"], fuel)
    # radiator and fan
    rad = [box(f"{name}_rad", (x0 + 6, 60, -80), (x0 + 30, 250, 0), m["radiator"], parent)]
    for k in range(14):
        y = 68 + k * 13
        rad.append(box(f"{name}_radf{k}", (x0 + 6, y, -0.4), (x0 + 30, y + 3, 0.4), m["cab_dark"], parent))
    join(rad, f"{name}_radiator")
    fan = empty(f"{name}_fan", parent, P(x0 + 44, 155, -40))
    box(f"{name}_blade0", (-3, -60, -7), (3, 60, 7), m["skid"], fan)
    box(f"{name}_blade1", (-3, -7, -60), (3, 7, 60), m["skid"], fan)
    # engine block: crankcase, cylinder block with six bores, head, rocker cover
    ex0, ex1 = x0 + 70, x0 + 340
    blk = [box(f"{name}_case", (ex0, 60, -70), (ex1, 105, -58), m["engine_cut"], parent),
           box(f"{name}_case_l", (ex0, 60, -70), (ex0 + 6, 105, 0), m["engine_cut"], parent),
           box(f"{name}_case_t", (ex0, 100, -70), (ex1, 105, 0), m["engine_cut"], parent),
           box(f"{name}_head", (ex0, 182, -70), (ex1, 204, 0), m["engine_cut"], parent),
           box(f"{name}_cover", (ex0 + 6, 204, -60), (ex1 - 6, 216, -6), m["engine"], parent),
           box(f"{name}_sump", (ex0 + 10, 60, -70), (ex1 - 10, 66, 0), m["engine"], parent)]
    bores = 6
    bw = (ex1 - ex0) / bores
    pistons = []
    for k in range(bores):
        bx = ex0 + k * bw
        blk.append(box(f"{name}_web{k}", (bx, 105, -70), (bx + 6, 182, 0), m["engine_cut"], parent))
        blk.append(box(f"{name}_bore{k}", (bx + 6, 105, -70), (bx + bw, 182, -50), m["bore"], parent))
        pg = empty(f"{name}_pist{k}", parent)
        box(f"{name}_pist{k}_p", (bx + 8, 150, -48), (bx + bw - 2, 172, -6), m["piston"], pg)
        for r in range(3):
            box(f"{name}_pist{k}_r{r}", (bx + 8, 165 - r * 4, -6), (bx + bw - 2, 166 - r * 4, -5.6), m["bore"], pg)
        box(f"{name}_pist{k}_rod", (bx + bw / 2 - 2, 98, -30), (bx + bw / 2 + 4, 152, -24), m["rod"], pg)
        pistons.append(pg)
        # valves in the head over each bore
        for v in range(2):
            vx = bx + 12 + v * (bw - 20)
            blk.append(box(f"{name}_valve{k}{v}", (vx, 178, -20), (vx + 4, 200, -16), m["rod"], parent))
    blk.append(box(f"{name}_blkend", (ex1 - 6, 105, -70), (ex1, 182, 0), m["engine_cut"], parent))
    join(blk, f"{name}_block")
    crank = empty(f"{name}_crank", parent, P(ex0, 82, -30))
    tube(f"{name}_crank_s", (0, 0, 0), (ex1 - ex0 + 30, 0, 0), 5.0, m["rod"], crank, 16)
    for k in range(bores):
        cx = k * bw + bw / 2
        if k % 2 == 0:
            box(f"{name}_cw{k}", (cx - 7, 0, -9), (cx + 7, 15, 9), m["piston"], crank)
        else:
            box(f"{name}_cw{k}", (cx - 7, -15, -9), (cx + 7, 0, 9), m["piston"], crank)
    # turbo, manifold, exhaust stack with muffler
    rod(f"{name}_manifold", (ex0 + 20, 196, -50), (ex1 - 10, 196, -50), 7.0, m["exhaust"], parent, False, 16)
    ball(f"{name}_turbo", (ex1 - 30, 228, -45), 18.0, m["exhaust"], parent, 16)
    stack_x = ex1 - 30
    rod(f"{name}_riser", (stack_x, 240, -45), (stack_x, 270, -45), 8.0, m["exhaust"], parent, False, 16)
    rod(f"{name}_muffler", (stack_x, 270, -45), (stack_x, 320, -45), 18.0, m["exhaust"], parent, False, 20)
    rod(f"{name}_stack", (stack_x, 320, -45), (stack_x, 350, -45), 8.0, m["exhaust"], parent, False, 16)
    # coupling and alternator
    ax0, ax1 = x0 + 350, x1 - 8
    ring_x(f"{name}_flywheel", AXIS_Y, -30.0, x0 + 340, ax0 + 6, 60.0, 8.0, m["engine"], parent, True, 40)
    ring_x(f"{name}_altframe", AXIS_Y, 0.0, ax0 + 6, ax1, 82.0, 74.0, m["alt"], parent, True, 48)
    ring_x(f"{name}_stator", AXIS_Y, 0.0, ax0 + 14, ax1 - 10, 74.0, 50.0, m["core"], parent, True, 48)
    wind = []
    for k in range(9):
        t = math.pi + math.pi * (k + 0.5) / 9
        y, z = AXIS_Y + 51 * math.cos(t), 51 * math.sin(t)
        wind.append(tube(f"{name}_slot{k}", (ax0 + 10, y, z), (ax1 - 6, y, z), 4.0, m["copper"], parent, 10))
    for k, xx in enumerate((ax0 + 10, ax1 - 10)):
        wind.append(ring_x(f"{name}_endturn{k}", AXIS_Y, 0.0, xx - 4, xx + 4, 60.0, 46.0, m["copper"], parent, True, 40))
    join(wind, f"{name}_windings")
    box(f"{name}_altfoot", (ax0 + 10, 60, -70), (ax1 - 10, 66, 0), m["alt"], parent)
    rotor = empty(f"{name}_rotor", parent, P(ax0, AXIS_Y, 0))
    tube(f"{name}_shaft", (-20, 0, 0), (ax1 - ax0 + 8, 0, 0), 8.0, m["rod"], rotor, 16)
    tube(f"{name}_hub", (20, 0, 0), (ax1 - ax0 - 20, 0, 0), 22.0, m["core"], rotor, 24)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        cy, cz = 34 * math.cos(a), 34 * math.sin(a)
        pole = box(f"{name}_pole{k}", (24, -10, -10), (ax1 - ax0 - 24, 10, 10), m["copper" if k % 2 else "enamel"], rotor)
        pole.location = P((ax1 - ax0) / 2, cy, cz)
        pole.rotation_euler = (a, 0, 0)
    tb = (ax1 - 70, 205.0, -35.0)
    box(f"{name}_tbox", (ax1 - 100, 226, -60), (ax1 - 40, 258, -10), m["alt"], parent)
    # control panel
    box(f"{name}_panel", (x0 + 40, 230, -30), (x0 + 70, 290, -10), m["cab_dark"], parent)
    gp.update({
        "pistons": pistons, "crank": crank, "rotor": rotor, "fan": fan, "fuel": fuel, "bw": bw,
        "stack": (stack_x, 350, -45), "engine": (ex0 + bw * 1.5, 140, 0.0), "piston": (ex0 + bw * 2.5, 172, 0.0),
        "crank_pt": (ex0 + 40, 82, 0.0), "alt": (ax0 + 60, AXIS_Y + 60, 0.0), "rotor_pt": (ax0 + 60, AXIS_Y + 34, 10.0),
        "radiator": (x0 + 18, 230, 0.0), "tank": (x0 + 200, 40, 0.0), "tb": (tb[0], 258, -35.0), "turbo": (ex1 - 30, 228, -27),
        "panel": (x0 + 55, 290, -20), "x1": x1, "c": ((x0 + x1) / 2, 160, 0.0),
    })
    return gp


def engine_run(gp, f0, f1, period=8):
    """Pistons up and down (firing order staggered), crank, fan and rotor turning, from f0 to f1."""
    for k, pg in enumerate(gp["pistons"]):
        phase = (0, 4, 2, 5, 1, 3)[k] / 6.0
        key(pg, f0 - 1, "location", P(0, 0, 0), linear=True)
        for f in range(f0, f1 + 1, 2):
            y = -16 * (0.5 - 0.5 * math.cos(2 * math.pi * ((f - f0) / period + phase)))
            key(pg, f, "location", P(0, y, 0), linear=True)
        key(pg, f1 + 2, "location", P(0, 0, 0), linear=True)
    turns = (f1 - f0) / period
    for obj in (gp["crank"], gp["rotor"], gp["fan"]):
        key(obj, f0, "rotation_euler", (0, 0, 0), linear=True)
        key(obj, f1, "rotation_euler", (-2 * math.pi * turns * (0.5 if obj is gp["fan"] else 1.0), 0, 0), linear=True)


# ---- racks, the utility pole -------------------------------------------------------------------------

RACK_W = 60.0


def racks(m, parent, x0, n, name, depth=110.0):
    """A row of server racks, front open: server trays with GPU lights (one group per rack, so they
    can pulse), an overhead busway with a tap box and drop to each rack."""
    leds = []
    for r in range(n):
        rx = x0 + r * (RACK_W + 2)
        parts = [box(f"{name}{r}_l", (rx, 0, -depth), (rx + 3, 210, 0), m["rack"], parent),
                 box(f"{name}{r}_r", (rx + RACK_W - 3, 0, -depth), (rx + RACK_W, 210, 0), m["rack"], parent),
                 box(f"{name}{r}_t", (rx, 207, -depth), (rx + RACK_W, 210, 0), m["rack"], parent),
                 box(f"{name}{r}_b", (rx, 0, -depth), (rx + RACK_W, 210, -depth + 2), m["rack"], parent)]
        g = empty(f"{name}{r}_gpu", parent)
        for t in range(10):
            y = 10 + t * 19.5
            parts.append(box(f"{name}{r}_s{t}", (rx + 3, y, -depth + 6), (rx + RACK_W - 3, y + 16, -3), m["server"], parent))
            for k in range(4):
                x = rx + 8 + k * 11
                box(f"{name}{r}_g{t}{k}", (x, y + 6, -3), (x + 7, y + 10, -2.2), m["led"], g)
        join(parts, f"{name}{r}")
        leds.append(g)
    x1 = x0 + n * (RACK_W + 2)
    box(f"{name}_busway", (x0 - 10, 236, -70), (x1, 248, -50), m["busway"], parent)
    drops = []
    for r in range(n):
        cx = x0 + r * (RACK_W + 2) + RACK_W / 2
        box(f"{name}_tap{r}", (cx - 6, 226, -66), (cx + 6, 236, -54), m["cab_dark"], parent)
        drops.append(cable(f"{name}_drop{r}", [(cx, 226, -60), (cx, 210, -60)], 2.0, m["cable"], parent, 8))
    return {"leds": leds, "bus": [(x0 - 10, 242, -45), (x1, 242, -45)], "drops": drops, "top": ((x0 + x1) / 2, 210, -30.0),
            "c": ((x0 + x1) / 2, 110, 0.0), "x1": x1, "in": (x0 - 10, 242, -60)}


def pole(m, parent, x, z, name, h=430.0):
    """A utility pole with a crossarm and three insulators; returns the line's attachment points."""
    tube(f"{name}_pole", (x, 0, z), (x, h + 20, z), 9.0, m["pole"], parent, 14)
    box(f"{name}_arm", (x - 70, h, z - 6), (x + 70, h + 10, z + 6), m["pole"], parent)
    pts = []
    for k, dx in enumerate((-55.0, 0.0, 55.0)):
        for j in range(3):
            tube(f"{name}_ins{k}{j}", (x + dx, h + 10 + j * 6, z), (x + dx, h + 14 + j * 6, z), 6.0, m["insulator"], parent, 12)
        pts.append((x + dx, h + 30, z))
    return pts


# ---- the whole site --------------------------------------------------------------------------------

GX0 = -1640.0                       # generator skid's left end
POLE_X, POLE_Z = -985.0, -110.0
ATS_X = (-900.0, -820.0)
RECT_X = (-780.0, -660.0)
DCL_X = (-650.0, -590.0)
INV_X = (-580.0, -460.0)
SS_X = (-450.0, -400.0)
BATT_X = [(-360.0, -284.0), (-280.0, -204.0), (-200.0, -124.0)]
RACK_X0 = -40.0
NRACK = 4


def plant(m, root, gen_cut=True):
    """The whole site. Returns its parts' points, groups and the cable paths the beads ride."""
    g = root
    box("site_floor", (-1700.0, -6.0, -400.0), (300.0, 0.0, 30.0), m["floor"], g)
    box("site_pad", (GX0 - 30, 0.0, -120.0), (GX0 + GEN_L + 30, 2.0, 20.0), m["concrete"], g)
    gp = generator(m, g, GX0, "gen") if gen_cut else generator(m, g, GX0, "gen", cut_open=False)
    ins = pole(m, g, POLE_X, POLE_Z, "pole")
    at = ats(m, g, *ATS_X, "ats")
    rc = converter(m, g, *RECT_X, "rect", "rect")
    dl = dc_link(m, g, *DCL_X, "dcl")
    iv = converter(m, g, *INV_X, "inv", "inv")
    ss = static_switch(m, g, *SS_X, "ss")
    bats = [li_cabinet(m, g, a, b, f"batt{i}") for i, (a, b) in enumerate(BATT_X)]
    rk = racks(m, g, RACK_X0, NRACK, "rack")

    C = {}
    # utility: the line from far behind to the pole, then the drop into the ATS's top
    far = (ins[1][0], ins[1][1] + 10, -800.0)
    C["util_in"] = cable("c_util_in", arch(far, ins[1], (0, -25, 0), 14), 3.0, m["cable"], g)
    C["util_drop"] = cable("c_util_drop", arch(ins[1], (at["in_u"][0], H + 4, ZB), (60, 40, 30), 14), 3.0, m["cable"], g)
    # generator: alternator terminal box to the ATS's left side
    C["gen_out"] = cable("c_gen_out", arch(gp["tb"] if gen_cut else (GX0 + GEN_L - 60, 270, 0), (at["in_g"][0], at["in_g"][1], ZB),
                                           (0, 90, 10), 14), 3.5, m["cable"], g)
    # the UPS chain
    C["ats_rect"] = cable("c_ats_rect", arch((at["out"][0], H + 2, ZB), (rc["in"][0], H + 2, ZB), (0, 40, 0), 10), 3.5, m["cable"], g)
    C["rect_dcl"] = cable("c_rect_dcl", arch((rc["out"][0], H + 2, ZB), (dl["in"][0], H + 2, ZB), (0, 26, 0), 8), 3.5, m["cable"], g)
    C["dcl_inv"] = cable("c_dcl_inv", arch((dl["out"][0], H + 2, ZB), (iv["in"][0], H + 2, ZB), (0, 26, 0), 8), 3.5, m["cable"], g)
    C["inv_out"] = cable("c_inv_out", arch((iv["out"][0], H + 2, ZB), rk["in"], (0, 120, 0), 18), 3.5, m["cable"], g)
    C["bypass"] = cable("c_bypass", arch((at["out"][0] + 4, H + 2, -40.0), (ss["in"][0], H + 2, -40.0), (0, 150, 0), 18), 3.0, m["cable"], g)
    C["ss_out"] = cable("c_ss_out", arch((ss["out"][0], H + 2, -40.0), (rk["in"][0], rk["in"][1], -66.0), (0, 70, 0), 14), 3.0, m["cable"], g)
    bt = [b["top"] for b in bats]
    C["dc_batt"] = cable("c_dc_batt", arch((dl["batt"][0], H + 2, -50.0), (bt[0][0], H + 2, -45.0), (0, 70, 0), 14), 3.5, m["cable"], g)
    C["batt_bus"] = cable("c_batt_bus", [(bt[0][0], H + 2, -45.0), (bt[1][0], H + 2, -45.0), (bt[2][0], H + 2, -45.0)], 3.0, m["cable"], g)

    # the lit fault overlay on the utility cables (shown while the utility is dead)
    dead = empty("util_dead", g)
    cable("c_util_dead_a", [(p[0], p[1], p[2] + 0.4) for p in C["util_in"]], 3.4, m["fault"], dead)
    cable("c_util_dead_b", [(p[0], p[1], p[2] + 0.4) for p in C["util_drop"]], 3.4, m["fault"], dead)

    racks_bus = rk["bus"]
    paths = {
        "util": C["util_in"] + C["util_drop"][1:] + at["path_u"] + C["ats_rect"][1:],
        "gen": C["gen_out"] + at["path_g"] + C["ats_rect"][1:],
        "rect": rc["path"] + C["rect_dcl"][1:] + dl["path"][1:],
        "inv": C["dcl_inv"] + iv["path"][1:] + C["inv_out"][1:] + racks_bus[1:],
        "charge": C["dc_batt"] + C["batt_bus"][1:],
        "discharge": list(reversed(C["batt_bus"])) + list(reversed(C["dc_batt"]))[1:],
        "bypass": C["bypass"] + ss["path"] + C["ss_out"][1:] + [(rk["bus"][1][0], rk["bus"][1][1], -66.0)],
        "util_bypass": C["util_in"] + C["util_drop"][1:] + at["path_u"],
    }
    return {"gen": gp, "ats": at, "rect": rc, "dcl": dl, "inv": iv, "ss": ss, "bats": bats, "racks": rk, "ins": ins,
            "dead": dead, "C": C, "paths": paths}


def drops_flow(root, S, m, runs, name="drop"):
    """Short bead runs down each rack's drop from the busway."""
    for r, d in enumerate(S["racks"]["drops"]):
        flow(root, f"{name}{r}", d, m, runs, n=2, size=3.5, speed=3.0)
