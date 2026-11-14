"""The chip cross-section as reusable Blender pieces for the CHIP tab pictures.

One CMOS inverter (an NMOS and a PMOS) in the silicon, under tungsten contacts, three tiers of
copper wiring (thin M1-M4, mid M5-M9, top M10-M14) and a row of package bumps. Every node page on
the Chip tab plays this same scene: it starts on the whole chip, then the camera glides in on
the node's part (chip_hero.py is the whole-chip tour; chip_zoom.py makes the per-node ones).
Units are schematic millimetres, Y up, the cut plane at z = 0 with the camera on +z.

Lights are overlays: a slightly larger emissive copy shown for the beats where the part is active.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, empty, key, label, mat, pivot, rel, show, tube, ball  # noqa: E402
from sand_zooms import scale_keys, stream_of  # noqa: E402

HALF = 1500.0  # the chip's half-width in x
DEPTH = 700.0  # how far the slab runs behind the cut plane

# layer bands, bottom edge to top edge
SUB = (-300.0, 0.0)
CONTACT = (0.0, 360.0)
THIN = (380.0, 620.0)
MID = (640.0, 1020.0)
TOP = (1040.0, 1420.0)
BUMP_Y = 1520.0

NMOS_X, PMOS_X = -700.0, 700.0
SD = 190.0  # source and drain sit this far either side of a gate
GATE_HALF = 100.0
BUMP_PITCH = 178.0
BUMP_I = range(-3, 14)  # bump i is at x = -890 + 178 i: -890 (VSS) and 890 (VDD) are among them
VSS_X, VDD_X, IN_X, OUT_X = -890.0, 890.0, 0.0, 356.0


def bump_x(i):
    return VSS_X + BUMP_PITCH * i


# the three wiring tiers: (band, wire levels, wire height, wire depth in z)
TIERS = {
    "thin": (THIN, 4, 24.0, 40.0),
    "mid": (MID, 5, 40.0, 70.0),
    "top": (TOP, 3, 90.0, 120.0),
}


def level_y(tier, i):
    (lo, hi), n, h, _ = TIERS[tier]
    return lo + (hi - lo) * (i + 0.5) / n


def mats(m):
    m["c_sub"] = mat("chip_substrate", (0.62, 0.50, 0.30), rough=0.8)
    m["c_nplus"] = mat("chip_nplus", (0.40, 0.55, 0.90), rough=0.6)
    m["c_pplus"] = mat("chip_pplus", (0.90, 0.50, 0.50), rough=0.6)
    m["c_oxide"] = mat("chip_hik", (0.85, 0.88, 0.95), rough=0.4)
    m["c_gate"] = mat("chip_gate", (0.55, 0.58, 0.66), metal=0.8, rough=0.3)
    m["c_gate_on"] = mat("chip_gate_on", (1.0, 0.72, 0.35), emit=(1.0, 0.65, 0.25), strength=3.0)
    m["c_chan"] = mat("chip_channel", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=3.0)
    m["c_w"] = mat("chip_tungsten", (0.55, 0.57, 0.62), metal=0.9, rough=0.3)
    m["c_cu_thin"] = mat("chip_cu_thin", (0.80, 0.45, 0.30), metal=0.8, rough=0.35)
    m["c_cu_mid"] = mat("chip_cu_mid", (0.88, 0.52, 0.30), metal=0.8, rough=0.35)
    m["c_cu_top"] = mat("chip_cu_top", (0.95, 0.60, 0.30), metal=0.8, rough=0.3)
    m["c_lit_thin"] = mat("chip_lit_thin", (0.45, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.22)
    m["c_lit_mid"] = mat("chip_lit_mid", (0.75, 0.60, 1.0), emit=(0.70, 0.50, 1.0), strength=1.0, alpha=0.22)
    m["c_lit_top"] = mat("chip_lit_top", (1.0, 0.82, 0.35), emit=(1.0, 0.78, 0.30), strength=1.0, alpha=0.22)
    m["c_ild"] = mat("chip_ild", (0.55, 0.60, 0.75), rough=0.5, alpha=0.07)
    m["c_pad"] = mat("chip_pad", (0.94, 0.74, 0.38), metal=0.6, rough=0.35)
    m["c_bump"] = mat("chip_bump", (0.80, 0.82, 0.86), metal=0.7, rough=0.3)
    m["c_bump_on"] = mat("chip_bump_on", (1.0, 0.82, 0.40), emit=(1.0, 0.78, 0.30), strength=3.0)
    m["c_dot_vdd"] = mat("chip_dot_vdd", (1.0, 0.65, 0.25), emit=(1.0, 0.62, 0.22), strength=3.5)
    m["c_dot_gnd"] = mat("chip_dot_gnd", (0.45, 0.70, 1.0), emit=(0.42, 0.68, 1.0), strength=3.5)
    m["c_dot_sig"] = mat("chip_dot_sig", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=3.5)
    m["c_dot_out"] = mat("chip_dot_out", (0.75, 0.55, 1.0), emit=(0.70, 0.50, 1.0), strength=3.5)


def overlay(parent, name, lo, hi, m, intervals):
    g = empty(name + "_g", parent)
    box(name, lo, hi, m, g)
    show(g, intervals)
    return g


def route(pts):
    """A start point and the offsets from it, for stream_of."""
    s = pts[0]
    return s, [(p[0] - s[0], p[1] - s[1], p[2] - s[2]) for p in pts]


def stack_down(x, y_top, y_bot, z=-60.0):
    return [(x, y_top, z), (x, y_bot, z)]


def silicon(root, m):
    box("substrate", (-HALF, SUB[0], -DEPTH), (HALF, SUB[1], -4.0), m["c_sub"], root)


def transistor(root, m, cx, nmos, lit=()):
    """One transistor: source and drain blocks, the gate stack and its channel. `lit` shows the
    gate (and the channel under it) switched on for those intervals."""
    g = empty("nmos" if nmos else "pmos", root)
    sd = m["c_nplus"] if nmos else m["c_pplus"]
    for sgn in (-1, 1):
        x = cx + sgn * SD
        box(f"sd{sgn}", (x - 70, -90, -240), (x + 70, 6, 0), sd, g)
    box("hik", (cx - GATE_HALF - 8, 0, -240), (cx + GATE_HALF + 8, 14, 0), m["c_oxide"], g)
    box("gate", (cx - GATE_HALF, 14, -240), (cx + GATE_HALF, 120, 0), m["c_gate"], g)
    if lit:
        overlay(g, "gate_on", (cx - GATE_HALF - 6, 14, -246), (cx + GATE_HALF + 6, 126, 6), m["c_gate_on"], lit)
        overlay(g, "chan_on", (cx - SD, -30, -230), (cx + SD, 4, -6), m["c_chan"], lit)
    return g


def contacts(root, m):
    """Tungsten plugs from the source, drain and gate of each transistor up to the first metal."""
    g = empty("contacts", root)
    for cx in (NMOS_X, PMOS_X):
        for dx, y0 in ((-SD, 6), (SD, 6), (0, 120)):
            tube(f"plug{cx:.0f}_{dx:.0f}", (cx + dx, y0, -60.0), (cx + dx, level_y("thin", 0), -60.0), 28, m["c_w"], g, verts=10)
    return g


def _wires(tier, m, g, lit=()):
    """Horizontal wire runs and the vias that stack them, schematic and fixed."""
    (lo, hi), n, h, d = TIERS[tier]
    mat_ = m["c_cu_" + tier]
    runs = {
        "thin": [[(-890, -510)], [(-700, 700)], [(-510, 510)], [(-1300, -1000), (1000, 1300)]],
        "mid": [[(-1400, -300)], [(-300, 500)], [(500, 1400)], [(-900, 100)], [(100, 1100)]],
        "top": [[(-1450, 1450)], [(-1450, -100), (100, 1450)], [(-1450, 1450)]],
    }[tier]
    for i in range(n):
        y = level_y(tier, i)
        for k, (x0, x1) in enumerate(runs[i % len(runs)]):
            box(f"{tier}{i}_{k}", (x0, y - h / 2, -60 - d / 2), (x1, y + h / 2, -60 + d / 2), mat_, g)


def wiring(root, m, lit_thin=(), lit_mid=(), lit_top=()):
    """The three metal tiers, each in its own group with an optional lit overlay band."""
    out = {}
    for tier, lit in (("thin", lit_thin), ("mid", lit_mid), ("top", lit_top)):
        g = empty("metal_" + tier, root)
        _wires(tier, m, g)
        (lo, hi) = TIERS[tier][0]
        box(f"ild_{tier}", (-HALF, lo - 10, -DEPTH), (HALF, hi + 10, -8.0), m["c_ild"], g)
        if lit:
            overlay(g, f"lit_{tier}", (-HALF - 6, lo - 14, -DEPTH + 40), (HALF + 6, hi + 14, 6), m["c_lit_" + tier], lit)
        out[tier] = g
    # the stacked vias: straight columns at the power, input and output x
    v = empty("vias", root)
    for x in (VSS_X, VDD_X, IN_X, OUT_X, NMOS_X, PMOS_X, -510.0, 510.0):
        tube(f"via{x:.0f}", (x, level_y("thin", 0), -60.0), (x, TOP[1] - 40, -60.0), 20, m["c_w"], v, verts=8)
    out["vias"] = v
    return out


def bumps(root, m, lit=()):
    """Package bumps on pads over the top metal; `lit` lights the VDD and VSS bumps."""
    g = empty("bumps", root)
    for i in BUMP_I:
        x = bump_x(i)
        box(f"pad{i}", (x - 70, TOP[1] + 6, -60 - 60), (x + 70, TOP[1] + 40, -60 + 60), m["c_pad"], g)
        ball(f"bump{i}", (x, BUMP_Y, -60.0), 60, m["c_bump"], g, 14)
    if lit:
        for x in (VSS_X, VDD_X):
            b = ball(f"bump_on{x:.0f}", (x, BUMP_Y, -60.0), 70, m["c_bump_on"], g, 14)
            show(b, lit)
    return g


def chip(root, m, **lit):
    """The whole chip. `lit` keys: gate (intervals for the NMOS gate on), thin, mid, top, bumps."""
    parts = {}
    silicon(root, m)
    parts["nmos"] = transistor(root, m, NMOS_X, True, lit=lit.get("gate", ()))
    parts["pmos"] = transistor(root, m, PMOS_X, False)
    parts["contacts"] = contacts(root, m)
    parts.update(wiring(root, m, lit.get("thin", ()), lit.get("mid", ()), lit.get("top", ())))
    parts["bumps"] = bumps(root, m, lit.get("bumps", ()))
    return parts


def glide_camera(root, poses, glide=0.3):
    """One (target, distance, yaw, pitch) pose per beat. Unlike sand_zooms.camera this does not
    cut at the beat boundary: the camera eases from the last pose to the next over the first
    `glide` of the beat, then holds with a slow push-in. Beat 0 is usually WHOLE (the full chip),
    so a node's overview starts wide and zooms in. End on the same pose as the start to loop."""
    import math
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        cp, sp = math.cos(pitch), math.sin(pitch)
        a = F(i, 0) if i == 0 else F(i, glide)
        b = F(i + 1, 0) - 1
        for f, d in ((a, dist * 1.03), (b, dist * 0.98)):
            e = (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))
            key(target, f, "location", P(*t))
            key(eye, f, "location", P(*e))


WHOLE = ((0.0, 620.0, 0.0), 5800.0, 0.0, 0.10)  # the whole chip, as in chip_hero.py

__all__ = [
    "glide_camera", "WHOLE",
    "F", "P", "box", "empty", "key", "label", "pivot", "rel", "show", "tube", "ball", "scale_keys",
    "stream_of", "mats", "chip", "route", "stack_down", "level_y", "bump_x", "overlay",
    "HALF", "DEPTH", "SUB", "CONTACT", "THIN", "MID", "TOP", "BUMP_Y", "NMOS_X", "PMOS_X", "SD",
    "GATE_HALF", "VSS_X", "VDD_X", "IN_X", "OUT_X",
]
