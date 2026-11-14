"""The four SAND zoom-ins, authored in Blender and exported for pbr3d, in the overview's style:
parts cut open at z = 0 so the inside shows, the camera on +z with a slow push-in per beat, and
`label:<text>` empties for the tags the TUI pins on. The TUI draws the scene in the left part of
the frame and the beat's text in a panel on the right, so the cameras frame a squarish picture.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/sand_zooms.py

For each zoom it writes:
  blender/sand_<name>.blend   open it in Blender to edit by hand
  assets/sand_<name>.glb      what pbr3d embeds and plays back

  a cavity  one electrode tip: the arc opens the cavity, quartz melts at its wall into SiO gas,
            SiO meets the SiC shell and silicon drips to the pool, escaped SiO turns coke to SiC
  b crust   the charge sinks steadily, SiO condenses into crust, the charge hangs on it and the
            cavity swells, the stoking bar breaks it and the charge falls in
  c tap     full pool behind a clay plug, the lance burns it open, metal runs under the hood into
            the ladle, the mud gun packs a fresh plug
  d bag     dusty gas enters under the bags, a cake builds on the cloth, a pulse of air knocks it
            off, microsilica is bagged and clean gas leaves the stack

One beat is SEC (8) seconds at 24 fps, as in sand_overview.py; the TUI samples the file at
t = (beat + local) * 8 (diagrams_nodes/sand/mod.rs). Every zoom is four beats.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402  (helpers, materials, beat timing)
from sand_overview import (  # noqa: E402
    BEAT_FRAMES,
    FPS,
    OFF,
    F,
    P,
    _constant_until,
    ball,
    beat,
    box,
    cup,
    cut,
    disc,
    empty,
    fly,
    key,
    label,
    mat,
    pivot,
    rel,
    rock,
    show,
    tube,
)

HERE = os.path.dirname(os.path.abspath(__file__))
PBR_DIR = os.path.normpath(os.path.join(HERE, ".."))
BEATS = 4


# ---- shared scene pieces ----------------------------------------------------------------


def start(name, beats=BEATS, page="sand"):
    """A fresh Blender file: `beats` beats of SEC seconds, its materials, and its root empty."""
    O._mats.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 0
    scene.frame_end = BEAT_FRAMES * beats
    m = O.M()
    m["sic"] = mat("sic", (0.22, 0.30, 0.27), metal=0.2, rough=0.55)
    m["clay"] = mat("clay", (0.45, 0.33, 0.22), rough=0.95)
    m["flame"] = mat("flame", (1.0, 0.85, 0.55), emit=(1.0, 0.8, 0.45), strength=9.0)
    m["jet"] = mat("jet", (0.75, 0.88, 1.0), emit=(0.7, 0.85, 1.0), strength=5.0, alpha=0.7)
    m["cake"] = mat("cake", (0.20, 0.20, 0.22), rough=0.95)
    m["crust_lite"] = mat("crust_lite", (0.52, 0.47, 0.40), rough=0.9)
    m["bag_sack"] = mat("bag_sack", (0.88, 0.88, 0.84), rough=0.9)
    m["hood"] = mat("hood", (0.28, 0.30, 0.34), metal=0.6, rough=0.45)
    return m, empty(f"{page}_{name}")


def camera(root, poses):
    """One (target, distance, yaw, pitch) pose per beat, held with a slow push-in, cutting at the
    beat boundary, as in the overview."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        cp, sp = math.cos(pitch), math.sin(pitch)
        for f, d in ((F(i, 0), dist * 1.04), (F(i + 1, 0) - 1, dist * 0.97)):
            e = (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))
            key(target, f, "location", P(*t), linear=True)
            key(eye, f, "location", P(*e), linear=True)


def finish(name, page="sand"):
    """Saves blender/<page>_<name>.blend and exports assets/<page>_<name>.glb."""
    os.makedirs(os.path.join(PBR_DIR, "assets"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{page}_{name}.blend"))
    glb = os.path.join(PBR_DIR, "assets", f"{page}_{name}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb,
        export_format="GLB",
        export_yup=True,
        export_animations=True,
        export_force_sampling=True,
        export_frame_step=1,
        export_cameras=False,
        export_lights=False,
        use_selection=False,
    )
    print("exported", glb)


def stream_of(parent, name, n, start_pt, path, size, m, b, u0, u1, life):
    """`n` blobs that each travel `path` (offsets from `start_pt`) over `life` frames, launched
    one after another between fractions u0 and u1 of beat `b`."""
    g = empty(name, parent)
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", start_pt, size, m, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=4)
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


def scale_keys(obj, keys, until=None):
    """Scale keys (frame, uniform or (x, y, z)) on `obj`; keys before `until` pop rather than ramp."""
    for f, s in keys:
        key(obj, f, "scale", (s, s, s) if isinstance(s, (int, float)) else s)
    if until is not None:
        _constant_until(obj, until)


# ---- a: the gas cavity ----------------------------------------------------------------

TIP_Y = 1000.0  # electrode tip
CAV_C = (0.0, 760.0)  # cavity centre (x, y)
CAV_R = 380.0
SHELL_R = 520.0
POOL_Y = 260.0


def build_cavity():
    m, root = start("cavity")
    g = empty("cavity_zoom", root)

    # the charge as a block whose front face is the cut plane; the hearth and pool below it
    box("hearth", (-1300, -120, -1300), (1300, 0, 0), m["refractory"], g)
    box("charge", (-1300, POOL_Y, -1300), (1300, 2100, 0), m["charge"], g)
    pool = pivot("pool", (0, 0, 0), g)
    box("pool_si", (-1300, 0, -1300), (1300, POOL_Y, 3), m["silicon"], pool)
    scale_keys(pool, [(0, 1), (F(2, 0.2), 1), (F(3, 1) - 1, (1, 1, 1.35))])
    label("liquid silicon pool", (-900, POOL_Y, 3), g, beat(2) + beat(3))

    cut(disc("electrode", (0, (TIP_Y + 2400) / 2, 0), 230, 2400 - TIP_Y, m["electrode"], g, 48), 14.0)
    label("carbon electrode", (230, 1700, 14), g, beat(0))

    # the SiC shell round the cavity: present from the start, it is what the cavity is lined with
    cut(ball("sic_shell", (CAV_C[0], CAV_C[1], 0), SHELL_R, m["sic"], g, 40), 5.0)
    label("SiC shell", (-SHELL_R * 0.8, CAV_C[1] - SHELL_R * 0.55, 5), g, beat(2))

    # the cavity opens in beat 0 and flickers with the arc after
    cav = pivot("cavity", (CAV_C[0], CAV_C[1], 0), g)
    cut(ball("cavity_gas", (0, 0, 0), CAV_R, m["cavity"], cav, 40), 9.0)
    keys = [(0, 0.25), (F(0, 0.15), 0.25), (F(0, 0.55), 1.0)]
    f, k = F(0, 0.55), 0
    while f < F(BEATS, 0):
        keys.append((f, (1.0, 1.03, 0.98, 1.02)[k % 4]))
        f += 6
        k += 1
    scale_keys(cav, keys)
    label("gas cavity, above 1800 C", (CAV_R * 0.55, CAV_C[1] - CAV_R * 0.5, 9), g, beat(0))

    arc = pivot("arc", (0, TIP_Y, 0), g)
    tube("arc_core", (0, 0, 20), (0, CAV_C[1] - CAV_R - TIP_Y + 30, 20), 30, m["arc"], arc, verts=8)
    show(arc, [(F(0, 0.1), F(BEATS, 0))])
    label("arc", (0, (TIP_Y + CAV_C[1] - CAV_R) / 2, 20), g, [(F(0, 0.25), F(1, 0))])

    # beat 1: quartz lumps at the upper cavity wall melt away; SiO and CO bubble off them
    for k in range(5):
        a = -1.0 + k * 0.5
        x, y = CAV_C[0] + (CAV_R + 40) * math.sin(a), CAV_C[1] + (CAV_R + 40) * math.cos(a) * 0.9
        q = pivot(f"quartz{k}", (x, y, 0), g)
        rock(f"quartz{k}_rock", (0, 0, 24), 70, m["quartz"], q)
        scale_keys(q, [(0, 1), (F(1, 0.1 + 0.1 * k), 1), (F(1, 0.45 + 0.1 * k), OFF), (F(BEATS, 0), OFF)])
        stream_of(
            g, f"sio_a{k}", 3, (x, y, 30), [(0, 0, 0), ((CAV_C[0] - x) * 0.6, (CAV_C[1] - y) * 0.6, 0)],
            34, m["sio"], 1, 0.15 + 0.1 * k, 0.4 + 0.1 * k, 60,
        )
    label("quartz melts at the hot wall", (CAV_R * 0.7, CAV_C[1] + CAV_R * 0.8, 24), g, beat(1))
    label("SiO + CO gas", (-90, CAV_C[1] + 60, 30), g, [(F(1, 0.3), F(2, 0))])

    # beat 2: silicon beads on the lower shell and drips to the pool
    for k in range(7):
        a = math.pi + (k - 3) * 0.28
        x = CAV_C[0] + (CAV_R - 20) * math.sin(a)
        y = CAV_C[1] + (CAV_R - 20) * math.cos(a)
        d = empty(f"drip{k}", g)
        ball(f"drip{k}_bead", (x, y, 30), 34, m["melt"], d, 14)
        for rep in range(2):
            f0 = F(2, 0.1 + 0.11 * k + 0.4 * rep)
            if f0 >= F(3, 0):
                continue
            key(d, f0, "location", P(0, 0, 0), linear=True)
            key(d, f0 + 18, "location", P(0, 0, 0), linear=True)
            key(d, f0 + 36, "location", P(0, POOL_Y - y + 10, 0), linear=True)
        show(d, [(F(2, 0.1 + 0.11 * k), F(3, 0))])
    label("Si drips to the pool", (260, (CAV_C[1] - CAV_R + POOL_Y) / 2, 30), g, [(F(2, 0.3), F(3, 0))])

    # beat 3: SiO slipping out the top of the shell; coke above turns to SiC where it meets it
    for k, x in enumerate((-430, -150, 150, 430)):
        y0 = CAV_C[1] + SHELL_R * 0.8
        stream_of(g, f"sio_up{k}", 4, (x * 0.6, y0, 30), [(0, 0, 0), (x * 0.5, 700, 0)], 36, m["sio"], 3, 0.02, 0.6, 70)
    for k, (x, y) in enumerate(((-520, 1640), (-160, 1760), (220, 1620), (560, 1720), (-760, 1400), (760, 1450))):
        c = pivot(f"coke{k}", (x, y, 0), g)
        rock(f"coke{k}_rock", (0, 0, 22), 80, m["coke"], c)
        s = pivot(f"sicr{k}", (x, y, 0), g)
        rock(f"sicr{k}_rock", (0, 0, 22), 82, m["sic"], s)
        flip = F(3, 0.35 + 0.08 * k)
        show(c, [(0, flip)])
        show(s, [(flip, F(BEATS, 0))])
    label("SiO escapes upward", (500, 1250, 30), g, beat(3))
    label("SiO + 2C turns coke to SiC", (-520, 1720, 22), g, [(F(3, 0.4), F(4, 0))])

    camera(
        root,
        [
            ((0, 1050, 0), 4300, 0.18, 0.10),
            ((0, 950, 0), 3000, 0.12, 0.08),
            ((0, 620, 0), 3100, -0.15, 0.12),
            ((0, 1150, 0), 4200, 0.25, 0.14),
        ],
    )
    finish("cavity")


# ---- b: crust and stoking -------------------------------------------------------------

ROOF_Y = 2500.0
CR_C = (0.0, 820.0)


def build_crust():
    m, root = start("crust")
    g = empty("crust_zoom", root)
    box("hearth", (-1700, -120, -1500), (1700, 0, 0), m["refractory"], g)
    box("pool_si", (-1700, 0, -1500), (1700, 280, 3), m["silicon"], g)
    box("charge", (-1700, 280, -1500), (1700, 2150, 0), m["charge"], g)
    box("lining_l", (-1900, -120, -1500), (-1700, ROOF_Y, 0), m["lining"], g)
    box("lining_r", (1700, -120, -1500), (1900, ROOF_Y, 0), m["lining"], g)
    box("roof", (-1950, ROOF_Y, -1500), (1950, ROOF_Y + 90, 0), m["steel"], g)
    cut(disc("electrode", (0, (1080 + 3300) / 2, 0), 230, 3300 - 1080, m["electrode"], g, 48), 14.0)
    label("electrode", (230, 1900, 14), g, beat(0))

    cav = pivot("cavity", (CR_C[0], CR_C[1], 0), g)
    cut(ball("cavity_gas", (0, 0, 0), 300, m["cavity"], cav, 40), 9.0)
    scale_keys(cav, [(0, 1), (F(2, 0.05), 1), (F(2, 0.7), 1.45), (F(3, 0.62), 1.45), (F(3, 0.85), 1.0), (F(4, 0), 1.0)])
    label("cavity", (300, CR_C[1] - 200, 9), g, beat(0))
    label("cavity swells", (420, CR_C[1] - 260, 9), g, [(F(2, 0.5), F(3, 0))])

    # crust: a thin ring at first, thickening as SiO condenses (beat 1), broken at beat 3
    cr = pivot("crust", (CR_C[0], CR_C[1] + 60, 0), g)
    cut(ball("crust_shell", (0, 0, 0), 420, m["crust_lite"], cr, 40), 5.0)
    scale_keys(cr, [(0, 0.85), (F(1, 0.1), 0.85), (F(1, 0.95), 1.55), (F(3, 0.6), 1.55), (F(3, 0.68), 0.9), (F(4, 0), 0.9)])
    label("thin SiC shell", (-420 * 0.75, CR_C[1] + 60 + 420 * 0.65, 5), g, beat(0))
    label("crust: SiO2 + Si", (-420 * 1.3, CR_C[1] + 60 + 420 * 1.0, 5), g, [(F(1, 0.5), F(3, 0.6))])

    # SiO rising out of the cavity and freezing onto the outside of the crust (beat 1)
    for k in range(6):
        a = -1.2 + 0.48 * k
        x0, y0 = CR_C[0] + 300 * math.sin(a), CR_C[1] + 300 * math.cos(a)
        x1, y1 = CR_C[0] + 620 * math.sin(a), CR_C[1] + 60 + 620 * math.cos(a)
        stream_of(g, f"sio{k}", 3, (x0, y0, 30), [(0, 0, 0), (x1 - x0, y1 - y0, 0)], 34, m["sio"], 1, 0.05 + 0.05 * k, 0.55 + 0.05 * k, 56)
    label("2SiO -> SiO2 + Si freezes out", (650, 1600, 30), g, [(F(1, 0.25), F(2, 0))])

    # tracer lumps on the cut face: sinking (beat 0), hung up over the crust (beat 2), falling (beat 3)
    spots = [(-1300, 1950), (-800, 1700), (-450, 2000), (450, 1950), (850, 1750), (1300, 1980), (-1250, 1350), (1250, 1400), (-600, 1450), (600, 1500)]
    for k, (x, y) in enumerate(spots):
        t = empty(f"tracer{k}", g)
        rock(f"tracer{k}_rock", (x, y, 22), 70, m["quartz"] if k % 2 else m["coke"], t)
        near = abs(x) < 900
        key(t, 0, "location", P(0, 0, 0), linear=True)
        key(t, F(1, 0.5), "location", P(0, -260, 0), linear=True)
        key(t, F(2, 0.2), "location", P(0, -300 if near else -380, 0))
        key(t, F(3, 0.62), "location", P(0, -300 if near else -560, 0))
        key(t, F(3, 0.9), "location", P(0, -650 if near else -620, 0))
        key(t, F(4, 0), "location", P(0, -680 if near else -640, 0))
    label("charge sinks steadily", (-1300, 1900, 22), g, beat(0))
    label("charge hangs on the crust", (-600, 1250, 22), g, beat(2))

    # the stoking car rolls in on the roof and drives its bar down into the crust (beat 3)
    st = empty("stoker", g)
    bx = -420.0
    box("stoker_car", (bx - 220, ROOF_Y + 100, -180), (bx + 220, ROOF_Y + 260, 180), m["dark_steel"], st)
    for wx in (-150, 150):
        disc(f"stoker_wheel{wx}", (bx + wx, ROOF_Y + 130, 190), 50, 30, m["steel"], st, 16)
    bar = empty("stoker_bar", st)
    tube("stoker_rod", (bx, ROOF_Y + 260, 40), (bx, ROOF_Y - 300, 40), 40, m["steel"], bar)
    reach = ROOF_Y - 300 - (CR_C[1] + 60 + 420 * 1.4)
    key(st, F(3, 0.0), "location", P(-1200, 0, 0))
    key(st, F(3, 0.25), "location", P(0, 0, 0))
    key(st, F(4, 0) - 1, "location", P(0, 0, 0))
    key(bar, F(3, 0.3), "location", P(0, 0, 0))
    key(bar, F(3, 0.58), "location", P(0, -reach, 0))
    key(bar, F(3, 0.68), "location", P(0, -reach - 150, 0))
    key(bar, F(3, 0.95), "location", P(0, 0, 0))
    show(st, [(F(3, 0), F(4, 0))])
    label("stoking car", (bx, ROOF_Y + 260, 0), st, [(F(3, 0.05), F(3, 0.35))])
    label("stoking bar", (bx, ROOF_Y - 300, 40), bar, [(F(3, 0.35), F(3, 0.7))])

    deb = empty("debris", g)
    for k in range(8):
        a = -1.1 + k * 0.3
        x0, y0 = CR_C[0] + 600 * math.sin(a), CR_C[1] + 60 + 600 * math.cos(a)
        ch = empty(f"debris{k}", deb)
        rock(f"debris{k}_rock", (x0, y0, 30), 70, m["crust_lite"], ch)
        key(ch, F(3, 0.62), "location", P(0, 0, 0))
        key(ch, F(3, 0.85), "location", P(-(x0 - CR_C[0]) * 0.5, -(y0 - CR_C[1]) * 0.9, 0), linear=True)
        show(ch, [(F(3, 0.62), F(3, 0.86))])
    label("charge falls in again", (650, 1350, 22), g, [(F(3, 0.7), F(4, 0))])

    camera(
        root,
        [
            ((0, 1350, 0), 5600, 0.15, 0.10),
            ((0, 1150, 0), 4200, 0.10, 0.08),
            ((0, 1250, 0), 4900, -0.12, 0.10),
            ((0, 1500, 0), 6000, 0.20, 0.14),
        ],
    )
    finish("crust")


# ---- c: tapping -----------------------------------------------------------------------

WALL_X0, WALL_X1 = -350.0, 0.0  # the furnace wall, inside face at x0
HOLE_Y = 300.0
LAD_X = 1700.0
LAD_TOP = 800.0
LAD_BASE = -700.0


def build_tap():
    m, root = start("tap")
    g = empty("tap_zoom", root)
    box("floor", (-1600, -150, -1200), (LAD_X - 300, 0, 800), m["refractory"], g)
    box("pit", (LAD_X - 300, LAD_BASE - 120, -1200), (2700, LAD_BASE, 800), m["refractory"], g)
    box("hearth", (-1600, 0, -1200), (WALL_X0, 120, 0), m["refractory"], g)
    box("charge", (-1600, 760, -1200), (WALL_X0, 1700, 0), m["charge"], g)
    # the wall with a tap hole through it: built round the hole
    box("wall_low", (WALL_X0, 0, -1200), (WALL_X1, HOLE_Y - 70, 0), m["lining"], g)
    box("wall_high", (WALL_X0, HOLE_Y + 70, -1200), (WALL_X1, 1700, 0), m["lining"], g)
    box("wall_back", (WALL_X0, HOLE_Y - 70, -1200), (WALL_X1, HOLE_Y + 70, -70), m["lining"], g)
    box("shell", (WALL_X1, 0, -1200), (WALL_X1 + 40, 1700, 0), m["dark_steel"], g)
    label("furnace wall", (WALL_X0 / 2, 1300, 0), g, beat(0))

    pool = pivot("pool", (0, 120, 0), g)
    box("pool_si", rel((0, 120, 0), (-1600, 120, -1200)), rel((0, 120, 0), (WALL_X0, 700, 3)), m["melt"], pool)
    scale_keys(pool, [(0, 1), (F(2, 0.15), 1), (F(2, 0.95), (1, 1, 0.45)), (F(4, 0), (1, 1, 0.45))])
    label("liquid silicon, 1414 C+", (-1100, 650, 3), g, beat(0) + beat(2))

    plug = empty("plug", g)
    box("plug_clay", (WALL_X0 - 10, HOLE_Y - 70, -70), (WALL_X1 + 60, HOLE_Y + 70, 4), m["clay"], plug)
    show(plug, [(0, F(1, 0.55))])
    plug2 = pivot("plug2", (WALL_X1 + 60, HOLE_Y, 0), g)
    box("plug2_clay", rel((WALL_X1 + 60, HOLE_Y, 0), (WALL_X0 - 10, HOLE_Y - 70, -70)), rel((WALL_X1 + 60, HOLE_Y, 0), (WALL_X1 + 60, HOLE_Y + 70, 4)), m["clay"], plug2)
    scale_keys(plug2, [(0, OFF), (F(3, 0.4), (0.05, 1, 1)), (F(3, 0.7), 1), (F(4, 0), 1)], until=F(3, 0.4))
    label("clay plug", (WALL_X1 + 60, HOLE_Y + 70, 4), g, beat(0) + [(F(3, 0.6), F(4, 0))])

    # the launder from the hole down to the ladle, and the ladle
    box("launder", (WALL_X1, HOLE_Y - 120, -130), (LAD_X - 300, HOLE_Y - 70, 130), m["refractory"], g)
    for zz in (-140, 120):
        box(f"launder_side{zz}", (WALL_X1, HOLE_Y - 120, zz), (LAD_X - 300, HOLE_Y, zz + 20), m["refractory"], g)
    label("launder", (900, HOLE_Y, 130), g, beat(2))
    lad = empty("ladle", g)
    cup("ladle_body", (LAD_X + 200, LAD_BASE, -200), 480, LAD_TOP, m["dark_steel"], lad)
    disc("ladle_base", (LAD_X + 200, LAD_BASE + 20, -200), 480, 40, m["dark_steel"], lad)
    fill = pivot("ladle_fill", (LAD_X + 200, LAD_BASE + 40, -200), lad)
    disc("ladle_si", (0, (LAD_TOP - 120) / 2, 0), 465, LAD_TOP - 140, m["melt"], fill)
    scale_keys(fill, [(0, (1, 1, OFF)), (F(2, 0.2), (1, 1, OFF)), (F(2, 0.95), (1, 1, 1)), (F(4, 0), (1, 1, 1))])
    label("ladle", (LAD_X + 680, 0, -200), g, beat(2) + beat(3))

    # beat 1: the oxygen lance slides in and burns the plug out
    lance = empty("lance", g)
    tube("lance_pipe", (WALL_X1 + 70, HOLE_Y, 0), (WALL_X1 + 1700, HOLE_Y + 260, 0), 24, m["steel"], lance)
    ball("lance_flame", (WALL_X1 + 60, HOLE_Y, 10), 85, m["flame"], lance, 16)
    key(lance, F(1, 0.0), "location", P(900, 140, 0))
    key(lance, F(1, 0.3), "location", P(0, 0, 0))
    key(lance, F(1, 0.55), "location", P(-330, 0, 0))
    key(lance, F(1, 0.8), "location", P(900, 140, 0))
    show(lance, [(F(1, 0), F(1, 0.85))])
    label("oxygen lance", (WALL_X1 + 900, HOLE_Y + 140, 0), lance, [(F(1, 0.05), F(1, 0.6))])
    label("tap hole opens", (WALL_X0 / 2, HOLE_Y - 70, 4), g, [(F(1, 0.55), F(2, 0))])

    # beat 2: the metal runs; fume boils off the stream into the hood
    st = pivot("stream", (WALL_X1, HOLE_Y - 60, 0), g)
    tube("stream_run", (0, 0, 0), (LAD_X - 300 - WALL_X1, 0, 0), 45, m["melt"], st, verts=14)
    tube("stream_fall", (LAD_X - 300 - WALL_X1, 0, 0), (LAD_X + 50 - WALL_X1, -300, -100), 42, m["melt"], st, verts=14)
    scale_keys(st, [(0, OFF), (F(1, 0.6), (0.05, 1, 1)), (F(1, 0.8), 1), (F(3, 0.3), 1), (F(3, 0.4), OFF), (F(4, 0), OFF)], until=F(1, 0.6))

    hx = 950.0
    box("hood_roof", (hx - 700, 1250, -500), (hx + 700, 1300, 300), m["hood"], g)
    box("hood_back", (hx - 700, 650, -520), (hx + 700, 1300, -500), m["hood"], g)
    tube("hood_duct", (hx, 1300, -100), (hx, 2300, -100), 160, m["hood"], g, verts=24)
    label("fume hood", (hx + 700, 1300, 300), g, beat(2))
    for k in range(10):
        f = empty(f"fume{k}", g)
        x = WALL_X1 + 150 + 120 * (k % 5)
        ball(f"fume{k}_ball", (x, HOLE_Y + 20, 40), 80, m["fume"], f, 12)
        f0 = F(2, 0.05 + 0.085 * k)
        fly(f, [(0, 0, 0), (0, 700, -60), (hx - x, 1700, -100)], f0, f0 + 60, steps=4)
        show(f, [(f0, min(f0 + 60, F(3, 0.3)))])
    label("SiO2 fume off the stream", (WALL_X1 + 450, HOLE_Y + 520, 40), g, [(F(2, 0.25), F(3, 0))])

    # beat 3: the mud gun swings in and packs the hole
    gun = empty("mud_gun", g)
    tube("gun_barrel", (WALL_X1 + 70, HOLE_Y, 0), (WALL_X1 + 1300, HOLE_Y + 420, 0), 90, m["steel"], gun, verts=20)
    box("gun_body", (WALL_X1 + 1200, HOLE_Y + 300, -200), (WALL_X1 + 1700, HOLE_Y + 650, 200), m["dark_steel"], gun)
    key(gun, F(3, 0.0), "location", P(800, 250, 0))
    key(gun, F(3, 0.3), "location", P(0, 0, 0))
    key(gun, F(3, 0.75), "location", P(0, 0, 0))
    key(gun, F(4, 0) - 1, "location", P(800, 250, 0))
    show(gun, [(F(3, 0), F(4, 0))])
    label("mud gun", (WALL_X1 + 1450, HOLE_Y + 650, 0), gun, [(F(3, 0.05), F(3, 0.6))])

    camera(
        root,
        [
            ((-200, 600, 0), 5800, 0.35, 0.15),
            ((200, 450, 0), 4600, 0.40, 0.12),
            ((750, 350, 0), 7600, 0.45, 0.22),
            ((500, 450, 0), 6000, 0.40, 0.15),
        ],
    )
    finish("tap")


# ---- d: the bag filter ----------------------------------------------------------------

HX0, HX1 = -1400.0, 1400.0  # housing
SHEET_Y = 2600.0  # the tube sheet the bags hang from
HOP_Y = 600.0


def build_bag():
    m, root = start("bag")
    g = empty("bag_zoom", root)
    # the housing cut open: back wall, sides, the tube sheet, the clean plenum and the hopper
    box("back", (HX0, HOP_Y, -1300), (HX1, SHEET_Y + 500, -1250), m["dark_steel"], g)
    box("side_l", (HX0 - 50, HOP_Y, -1300), (HX0, SHEET_Y + 500, 0), m["dark_steel"], g)
    box("side_r", (HX1, HOP_Y, -1300), (HX1 + 50, SHEET_Y + 500, 0), m["dark_steel"], g)
    box("sheet", (HX0, SHEET_Y, -1300), (HX1, SHEET_Y + 40, 0), m["steel"], g)
    box("roof", (HX0 - 50, SHEET_Y + 500, -1300), (HX1 + 50, SHEET_Y + 550, 0), m["steel"], g)
    label("clean-gas plenum", (HX0 + 200, SHEET_Y + 300, 0), g, beat(0))
    for k, (x0, x1) in enumerate(((HX0, -150), (150, HX1))):
        box(f"hopper{k}", (x0, HOP_Y - 450, -1300), (x1, HOP_Y, 0), m["pipe_glass"], g)
    box("hopper_throat", (-150, -150, -800), (150, HOP_Y - 450, -500), m["steel"], g)
    for lx in (HX0 + 60, HX1 - 60):
        box(f"leg{lx}", (lx - 50, -400, -700), (lx + 50, HOP_Y - 450, -600), m["steel"], g)

    # the inlet duct into the dirty side, the outlet and fan to the stack
    tube("inlet", (HX0 - 1500, 1100, -600), (HX0, 1100, -600), 230, m["pipe_glass"], g, verts=24)
    tube("outlet", (HX1, SHEET_Y + 270, -600), (HX1 + 900, SHEET_Y + 270, -600), 200, m["steel"], g, verts=24)
    disc("fan", (HX1 + 1000, SHEET_Y + 270, -600), 330, 260, m["dark_steel"], g, 32)
    tube("stack", (HX1 + 1000, SHEET_Y + 270, -600), (HX1 + 1000, SHEET_Y + 1400, -600), 200, m["steel"], g, verts=24)
    label("from the furnace", (HX0 - 1300, 1330, -600), g, beat(0))
    label("fan and stack", (HX1 + 1000, SHEET_Y + 1000, -400), g, beat(3))

    bags = [(x, z) for x in (-1050, -630, -210, 210, 630, 1050) for z in (-950, -450)]
    for i, (x, z) in enumerate(bags):
        tube(f"bag{i}", (x, SHEET_Y, z), (x, 1000, z), 110, m["cloth"], g, verts=16)
        disc(f"bag{i}_cap", (x, 1000, z), 110, 20, m["cloth"], g, 16)
    label("filter bags", (630 + 110, 1900, -450), g, beat(0))

    # beat 0: dusty gas in under the bags and up between them
    for k in range(14):
        d = empty(f"dirty{k}", g)
        ball(f"dirty{k}_ball", (HX0 - 1400, 1100, -600), 75, m["hot_gas"], d, 12)
        tx = -1050 + 210 * (k % 11)
        f0 = F(0, 0.03 + 0.06 * k)
        fly(d, [(0, 0, 0), (1400, 0, 0), (1400 + tx - HX0, 300, 0), (1400 + tx - HX0, 900, 0)], f0, f0 + 70, steps=4)
        show(d, [(f0, min(f0 + 70, F(1, 0)))])
    label("dusty gas", (HX0 + 300, 1150, -600), g, beat(0))

    # beat 1: a cake grows on each bag; clean gas rises inside the bags into the plenum
    cakes = []
    for i, (x, z) in enumerate(bags):
        c = pivot(f"cake{i}", (x, 0, z), g)
        tube(f"cake{i}_skin", (0, SHEET_Y - 20, 0), (0, 1020, 0), 112, m["cake"], c, verts=16)
        cakes.append(c)
    for c in cakes:
        scale_keys(c, [(0, (OFF,) * 3), (F(1, 0.05), (1.0, 1, 1)), (F(1, 0.9), (1.45, 1.45, 1)), (F(2, 0.3), (1.45, 1.45, 1)), (F(2, 0.42), (OFF,) * 3), (F(4, 0), (OFF,) * 3)], until=F(1, 0.05))
    label("dust cake on the cloth", (-210 - 160, 1600, -450), g, [(F(1, 0.3), F(2, 0.4))])
    for k in range(8):
        x, z = bags[(k * 5) % len(bags)]
        e = empty(f"inbag{k}", g)
        ball(f"inbag{k}_ball", (x, 1100, z), 60, m["clean"], e, 12)
        f0 = F(1, 0.2 + 0.08 * k)
        fly(e, [(0, 0, 0), (0, SHEET_Y - 1100 + 200, 0), (HX1 - x, SHEET_Y - 1100 + 200, 0)], f0, f0 + 70, steps=4)
        show(e, [(f0, min(f0 + 70, F(2, 0)))])
    label("clean gas up through the cloth", (HX1 - 300, SHEET_Y + 200, -450), g, [(F(1, 0.3), F(2, 0))])

    # beat 2: a pulse of air down each row; the cake drops into the hopper
    for row, z in enumerate((-950, -450)):
        j = empty(f"jet{row}", g)
        tube(f"jet{row}_pipe", (HX0 + 100, SHEET_Y + 380, z), (HX1 - 100, SHEET_Y + 380, z), 40, m["steel"], g, verts=12)
        for x in (-1050, -630, -210, 210, 630, 1050):
            tube(f"jet{row}_{x}", (x, SHEET_Y + 360, z), (x, SHEET_Y - 500, z), 55, m["jet"], j, verts=10)
        f0 = F(2, 0.25 + 0.08 * row)
        show(j, [(f0, f0 + 14)])
    label("pulse of compressed air", (-630, SHEET_Y + 380, -450), g, [(F(2, 0.15), F(2, 0.55))])
    for k in range(18):
        x, z = bags[k % len(bags)]
        ch = empty(f"flake{k}", g)
        rock(f"flake{k}_rock", (x + 150 * (-1) ** k, 1300 + 90 * (k % 7), z), 60, m["cake"], ch)
        f0 = F(2, 0.4 + 0.012 * k)
        key(ch, f0, "location", P(0, 0, 0))
        key(ch, f0 + 40, "location", P(-x * 0.6, -(1300 + 90 * (k % 7)) + HOP_Y - 200, 0), linear=True)
        show(ch, [(f0, f0 + 41)])
    label("cake drops to the hopper", (500, HOP_Y + 100, 0), g, [(F(2, 0.45), F(3, 0))])

    # beat 3: the hopper empties into a bulk bag of microsilica; clean gas leaves the stack
    dust = pivot("dust", (0, HOP_Y - 450, 0), g)
    box("dust_pile", (HX0 + 60, 0, -1250), (HX1 - 60, 260, -20), m["dust"], dust)
    scale_keys(dust, [(0, (1, 1, 0.2)), (F(2, 0.45), (1, 1, 0.2)), (F(2, 0.9), (1, 1, 1)), (F(3, 0.2), (1, 1, 1)), (F(3, 0.8), (1, 1, 0.25)), (F(4, 0), (1, 1, 0.25))])
    sack = pivot("sack", (0, -400, -650), g)
    box("sack_body", (-330, 0, -330), (330, 650, 330), m["bag_sack"], sack)
    scale_keys(sack, [(0, (1, 1, 0.1)), (F(3, 0.15), (1, 1, 0.1)), (F(3, 0.8), (1, 1, 1)), (F(4, 0), (1, 1, 1))])
    label("microsilica, sold", (330, -100, -320), g, beat(3))
    for k in range(7):
        e = empty(f"clean{k}", g)
        ball(f"clean{k}_ball", (HX1 + 1000, SHEET_Y + 1400, -600), 150, m["clean"], e, 12)
        f0 = F(3, 0.05 + 0.12 * k)
        key(e, f0, "location", P(0, 0, 0))
        key(e, f0 + 60, "location", P(300, 1000, 0), linear=True)
        show(e, [(f0, min(f0 + 60, F(4, 0)))])

    camera(
        root,
        [
            ((-700, 1500, 0), 8600, 0.25, 0.10),
            ((0, 1800, 0), 6400, 0.30, 0.10),
            ((0, 2000, 0), 6400, 0.15, 0.14),
            ((700, 1500, 0), 9800, 0.35, 0.16),
        ],
    )
    finish("bag")


def build_all():
    build_cavity()
    build_crust()
    build_tap()
    build_bag()


if __name__ == "__main__":
    build_all()
