"""Reusable pieces for the SLICE + POLISH pictures (overview, zooms, sections), in the SAND template
(docs/diagram-pages.md): a wire saw, lapping plates, an etch bath, an edge wheel, a polish pad,
a clean station, and the wafer that rides a track between them.

Scale: millimetres, Y up. Wafers are drawn at 1 um = UM mm, so a 775 um wafer is WAFER_T mm
thick and a 125 um saw kerf is KERF_T mm; that is schematic, not a drawing. Wafers are 300 mm
(radius 150). Builders take the frames they animate at and a `tags` dict where the tags they need
are named; the scripts pass the intervals.

Parents are at the origin while a scene is built, so children are built in the parent's
coordinates (`rel` for a pivot at a point, see sand_overview.rel).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, cut, disc, empty, key, label, mat, pivot, rel, show, tube  # noqa: E402
from sand_zooms import camera, scale_keys, stream_of  # noqa: E402,F401

END = F(40, 0)  # later than any scene: "until the end"
UM = 0.1  # mm drawn per micrometre of silicon
WAFER_R = 150.0
WAFER_T = 775 * UM  # 77.5 mm
KERF_T = 125 * UM  # 12.5 mm
PITCH = WAFER_T + KERF_T  # one slice per wire pass
TRACK_Y = 40.0  # top of the track; a wafer on the carrier sits on it
STATION_X = [i * 1000.0 for i in range(7)]  # INGOT, SLICE, LAP, ETCH, EDGE, POLISH, CLEAN


def tag(tags, name, text, at, parent):
    """The label `name` if `tags` asks for it: tags[name] is intervals or (text, intervals)."""
    if name not in tags:
        return None
    v = tags[name]
    if isinstance(v, tuple):
        text, v = v
    return label(text, at, parent, v)


def mats(m):
    m["ingot"] = mat("ingot_si", (0.36, 0.40, 0.46), metal=0.8, rough=0.35)
    m["wire"] = mat("wire_steel", (0.80, 0.82, 0.86), metal=0.9, rough=0.2)
    m["grit"] = mat("diamond_grit", (0.80, 0.95, 1.0), emit=(0.6, 0.9, 1.0), strength=1.8)
    m["chip"] = mat("si_chip", (0.25, 0.27, 0.31), metal=0.5, rough=0.6)
    m["slurry"] = mat("slurry", (0.62, 0.52, 0.36), rough=0.9)
    m["plate"] = mat("iron_plate", (0.24, 0.24, 0.27), metal=0.5, rough=0.5)
    m["resin"] = mat("resin_wheel", (0.58, 0.44, 0.24), rough=0.85)
    m["bath"] = mat("etch_bath", (0.20, 0.62, 0.55), rough=0.2, emit=(0.12, 0.45, 0.40), strength=0.4, alpha=0.45)
    m["water"] = mat("coolant", (0.45, 0.72, 1.0), emit=(0.4, 0.7, 1.0), strength=1.2, alpha=0.5)
    m["damage"] = mat("damage_layer", (0.85, 0.30, 0.18), emit=(1.0, 0.28, 0.12), strength=1.2)
    m["pad"] = mat("pad_pu", (0.72, 0.58, 0.38), rough=0.9)
    m["film"] = mat("film_oxide", (0.90, 0.78, 0.50), rough=0.4)
    m["copper"] = mat("copper_film", (0.85, 0.50, 0.30), metal=0.9, rough=0.3)
    m["tung"] = mat("tungsten", (0.45, 0.46, 0.50), metal=0.9, rough=0.4)
    m["mirror"] = mat("mirror_si", (0.72, 0.76, 0.82), metal=0.95, rough=0.04)
    m["sheen"] = mat("sheen", (1.0, 1.0, 0.9), emit=(1.0, 1.0, 0.9), strength=3.0)
    m["spray"] = mat("spray", (0.75, 0.88, 1.0), emit=(0.7, 0.85, 1.0), strength=1.2, alpha=0.5)
    m["swarf"] = mat("swarf", (0.10, 0.11, 0.13), rough=0.9)
    m["gold"] = mat("gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["gold_glow"] = mat("gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["red"] = mat("red", (0.90, 0.22, 0.18), emit=(0.9, 0.15, 0.1), strength=2.5)
    m["green"] = mat("green", (0.35, 0.80, 0.45), emit=(0.3, 0.8, 0.4), strength=1.5)
    m["plinth"] = mat("plinth", (0.18, 0.19, 0.23), rough=0.8)
    m["paper"] = mat("paper", (0.90, 0.88, 0.82), rough=0.85)
    m["blue"] = mat("blue", (0.36, 0.56, 0.82), metal=0.2, rough=0.45)
    m["grey"] = mat("grey", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    return m


# ---- fixed pieces ----------------------------------------------------------------------


def floor(root, m, x0=-600.0, x1=6600.0, z=450.0):
    """The shop floor under the stations and the track the wafer rides on."""
    box("floor", (x0, -80, -z), (x1, 0, z), m["plinth"], root)
    box("track", (x0 + 200, 0, -30), (x1 - 200, TRACK_Y, 30), m["steel"], root)


def cradle(parent, x, m, w=300.0, z=160.0):
    """A low support under a slice stack or an ingot, its top at TRACK_Y."""
    box("cradle", (x - w, 0, -z), (x + w, TRACK_Y, z), m["dark_steel"], parent)


def slab(parent, name, x, y0, z, r, t, m, verts=64):
    """A wafer-like disc lying flat: bottom at poly height y0, thickness t."""
    return disc(name, (x, y0 + t / 2, z), r, t, m, parent, verts=verts)


# ---- the carrier that moves the wafer along the track -----------------------------------


class Carrier:
    """A wafer on a carrier that moves between stations. `pv` scales Y about the track, so the
    wafer can thin (lapping, etch, DSP) without moving its bottom; children are built in `pv`
    coordinates with rel(). `stops` are (frame, x) pairs; x is poly millimetres."""

    def __init__(self, root, m, stops, t=WAFER_T):
        self.g = empty("carrier", root)
        for f, x in stops:
            key(self.g, f, "location", P(x, 0, 0), linear=True)
        self.pv = pivot("wafer_pv", (0, TRACK_Y, 0), self.g)
        self.t = t
        self.m = m

    def disc(self, name, mat_key, r=WAFER_R, t=None, verts=72, grow=0.0):
        t = self.t if t is None else t
        at = (0.0, TRACK_Y + t / 2, 0.0)
        return disc(name, rel((0, TRACK_Y, 0), at), r + grow, t, self.m[mat_key], self.pv, verts=verts)


def stops_for(stations, first_beat=1, hold_until=None):
    """Carrier keys: at beat i the carrier leaves station i-1 and reaches station i a quarter of
    the way through the beat; it waits at station i until then. Starts at station `first_beat`."""
    out = [(0, stations[first_beat]), (F(first_beat, 0), stations[first_beat])]
    for i in range(first_beat + 1, len(stations)):
        out.append((F(i, 0), stations[i - 1]))
        out.append((F(i, 0.25), stations[i]))
    return out


# ---- machines ---------------------------------------------------------------------------


def wire_web(parent, m, cx, pitch_ys, half=420.0, n_gap=None, tags=None):
    """A saw frame with horizontal wires along x at heights `pitch_ys`, at z = 0 (in front of
    the cut faces behind them). Two posts stand at cx +- half."""
    g = empty("web", parent)
    top = max(pitch_ys) + 120
    for s in (-1, 1):
        box(f"post{s:+d}", (cx + s * half - 30, TRACK_Y, -30), (cx + s * half + 30, top, 30), m["dark_steel"], g)
    for k, y in enumerate(pitch_ys):
        tube(f"wire{k}", (cx - half, y, 0), (cx + half, y, 0), 5.0, m["wire"], g, verts=6)
    tag(tags or {}, "web", "diamond wire web", (cx + half - 60, top, 40), g)
    return g


def lap_plates(parent, m, cx, lower_top, upper_y, r=260.0):
    """Two plates: the lower one sits on the track, the upper one (built at upper_y) can be keyed
    down. Returns (lower, upper pivot)."""
    lower = disc("plate_lower", (cx, lower_top / 2, 0), r, lower_top, m["plate"], parent, verts=72)
    upper = pivot("plate_upper", (cx, upper_y, 0), parent)
    disc("plate_upper_m", (0, 30, 0), r, 60, m["plate"], upper, verts=72)
    return lower, upper


def bath(parent, m, cx, w=340.0, depth=160.0, z=220.0):
    """An open tank with its liquid. The liquid's scale is keyed by the scene (rises in beat)."""
    box("tank_floor", (cx - w, 0, -z), (cx + w, 14, z), m["dark_steel"], parent)
    box("tank_wall_l", (cx - w - 14, 0, -z), (cx - w, depth, z), m["dark_steel"], parent)
    box("tank_wall_r", (cx + w, 0, -z), (cx + w + 14, depth, z), m["dark_steel"], parent)
    liquid = pivot("bath_liquid", (cx, 14, 0), parent)
    box("liquid_m", (-w + 4, 0, -z + 4), (w - 4, depth - 14, z - 4), m["bath"], liquid)
    return liquid


def edge_wheel(parent, m, cx, cy, r=110.0):
    """A resin wheel with its axis along z, spun about that axis by its pivot (rotation keys)."""
    pv = pivot("edge_wheel", (cx, cy, 0), parent)
    w = disc("wheel_m", (0, 0, 0), r, 60, m["resin"], pv, verts=48)
    w.rotation_euler = (math.radians(90), 0, 0)
    return pv


def spin(obj, f0, f1, turns=1.0, axis=2):
    """Rotate `obj` about its local Blender axis (0 x, 1 y, 2 z) from f0 to f1, linearly. Blender Z is
    poly Y (up), so a vertical spin is axis=2; a wheel whose axis is poly Z spins about axis=1."""
    r0 = [0.0, 0.0, 0.0]
    r1 = [0.0, 0.0, 0.0]
    r1[axis] = 2 * math.pi * turns
    key(obj, f0, "rotation_euler", tuple(r0), linear=True)
    key(obj, f1, "rotation_euler", tuple(r1), linear=True)


def spray_nozzles(parent, m, cx, y, f_iv, n=14, tags=None):
    """Two nozzles over a wafer and a fan of droplets falling onto it during the intervals."""
    g = empty("sprays", parent)
    for s in (-1, 1):
        tube(f"nozzle{s:+d}", (cx + s * 90, y + 140, 0), (cx + s * 90, y, 0), 8, m["steel"], g, verts=8)
    for k in range(n):
        for (f0, f1) in f_iv:
            e = empty(f"drop{k}_{f0}", g)
            x = cx + (-80 + 160 * k / max(1, n - 1))
            ball(f"drop{k}_{f0}_s", (x, y + 60, 0), 10, m["spray"], e, 8)
            key(e, f0, "location", P(0, 0, 0))
            key(e, f1, "location", P(0, -y * 0.5, 0))
            show(e, [(f0, f1)])
    return g


def chip_drops(parent, m, cx, y, f0, f1, n=10):
    """Small silicon chips and swarf falling away from a point during [f0, f1)."""
    g = empty("chips", parent)
    for k in range(n):
        x = cx + 30 * math.cos(k * 2.4)
        z = 30 * math.sin(k * 2.4)
        e = empty(f"chip{k}", g)
        ball(f"chip{k}_s", (x, y, z), 6, m["chip"], e, 6)
        key(e, f0, "location", P(0, 0, 0))
        key(e, f1, "location", P(0, -120, 0))
        show(e, [(f0, f1)])
    return g


def grit_points(parent, m, cx, y, z, f0, f1, n=6, r=5.0):
    """Diamond grit tips on a wire, lit during [f0, f1)."""
    g = empty("grit", parent)
    for k in range(n):
        e = empty(f"grit{k}", g)
        ball(f"grit{k}_s", (cx - 40 + 16 * k, y + 6, z), r, m["grit"], e, 6)
        show(e, [(f0, f1)])
    return g


def wafer_shelf(root, m, x, y, z, n, t, gap, r, mat_key):
    """A stack of n wafer-like slices standing with `gap` between, bottom at y."""
    g = empty("shelf", root)
    for k in range(n):
        slab(g, f"slice{k}", x, y + k * (t + gap), z, r, t, m[mat_key])
    return g
