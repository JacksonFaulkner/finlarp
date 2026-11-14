"""The Czochralski puller as reusable Blender pieces for the MELT + PULL pictures (overview, zooms,
sections). Each builder takes the frames it animates at, and a `tags` dict that switches its
labels on: tags[name] is a list of [f0, f1) intervals, or (text, intervals) to change the words.
A builder adds only the labels named in `tags`.

Sizes are millimetres for a 300 mm puller, schematic rather than a vendor drawing. Units, axes
and the cut-away convention are the SAND template's (docs/diagram-pages.md).

The crystal is one group that rises by p(t) (`p_keys`). Each part (neck, shoulder, body, tail)
sits in a pivot at its top and is revealed by how far the crystal has risen since the seed
touched the melt, so it appears to freeze on at the interface; if p falls again (a remelt) the
parts melt back.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, cut, disc, empty, key, label, mat, pivot, rel, rock, show, tube  # noqa: E402
from sand_zooms import scale_keys  # noqa: E402
from poly_overview import keyed_path, run, shell, _solidify  # noqa: E402

END = F(40, 0)  # "until the end" for intervals; later than any scene

SHELL_R, SHELL_TOP = 850.0, 1800.0
PULL_R, PULL_TOP = 330.0, 4300.0
FELT_R, FELT_Y0, FELT_Y1 = 720.0, 150.0, 1450.0
HEAT_R, HEAT_Y0, HEAT_Y1 = 560.0, 300.0, 1050.0
SUS_R = 440.0  # graphite susceptor round the quartz crucible
CRU_R, CRU_Y0, CRU_TOP = 410.0, 420.0, 900.0  # quartz crucible
MELT_Y = 750.0  # the melt surface, held fixed while the crystal grows
DEPTH = MELT_Y - (CRU_Y0 + 20)
SHIELD_Y0, SHIELD_Y1, SHIELD_R0, SHIELD_R1 = 820.0, 1180.0, 210.0, 470.0
RISE = 120.0  # how far the crucible rises while the body grows

XTAL_R = 150.0  # 300 mm crystal
NECK_R, NECK = 4.0, 120.0  # drawn 8 mm across (2-4 mm on the page) so it reads
SHOULDER = 170.0
BODY = 1500.0
TAIL = 260.0
SEED = 90.0
NECK_BOT = -NECK
BODY_TOP = -NECK - SHOULDER
BODY_BOT = BODY_TOP - BODY
TAIL_BOT = BODY_BOT - TAIL


def mats(m):
    m["melt_si"] = mat("melt_si", (0.95, 0.45, 0.15), metal=0.3, rough=0.15, emit=(1.0, 0.38, 0.08), strength=0.7)
    m["heater_hot"] = mat("heater_hot", (1.0, 0.45, 0.15), emit=(1.0, 0.42, 0.12), strength=2.6)
    m["graphite"] = mat("graphite", (0.10, 0.10, 0.11), rough=0.7)
    m["felt"] = mat("felt", (0.22, 0.21, 0.20), rough=1.0)
    m["poly"] = mat("poly_si", (0.62, 0.64, 0.68), metal=0.85, rough=0.28)
    m["dopant"] = mat("dopant", (0.35, 0.55, 1.0), emit=(0.3, 0.5, 1.0), strength=2.5)
    m["argon"] = mat("argon", (0.70, 0.85, 1.0), emit=(0.6, 0.8, 1.0), strength=1.4, alpha=0.6)
    m["xtal"] = mat("crystal", (0.55, 0.58, 0.64), metal=0.95, rough=0.12)
    m["seed"] = mat("seed", (0.80, 0.82, 0.88), metal=0.9, rough=0.1, emit=(0.6, 0.7, 0.9), strength=0.5)
    m["shield"] = mat("shield", (0.42, 0.44, 0.48), metal=0.7, rough=0.35)
    m["disloc"] = mat("dislocation", (1.0, 0.2, 0.15), emit=(1.0, 0.15, 0.1), strength=3.0)
    m["sio_b"] = mat("sio_bubble", (0.95, 0.95, 0.85), emit=(1.0, 0.95, 0.8), strength=1.5, alpha=0.8)
    m["co_b"] = mat("co_gas", (0.55, 0.55, 0.60), rough=0.6, alpha=0.8)
    m["oxygen"] = mat("oxygen_speck", (1.0, 0.3, 0.25), emit=(1.0, 0.25, 0.2), strength=2.0)
    m["flow_hot"] = mat("flow_hot", (1.0, 0.9, 0.5), emit=(1.0, 0.85, 0.4), strength=3.0)
    m["flow_cool"] = mat("flow_cool", (0.55, 0.15, 0.05), emit=(0.6, 0.12, 0.03), strength=1.0)
    m["field"] = mat("field_line", (0.45, 0.75, 1.0), emit=(0.4, 0.7, 1.0), strength=2.5)
    m["copper"] = mat("copper", (0.85, 0.50, 0.30), metal=0.9, rough=0.3)
    m["radiant"] = mat("radiant", (1.0, 0.8, 0.3), emit=(1.0, 0.75, 0.25), strength=3.0, alpha=0.8)
    return m


def tag(tags, name, text, at, parent):
    """The label `name` if `tags` asks for it: tags[name] is intervals or (text, intervals)."""
    if name not in tags:
        return None
    v = tags[name]
    if isinstance(v, tuple):
        text, v = v
    return label(text, at, parent, v)


def p_fn(p_keys):
    """p(f) linear between `p_keys` (frame, rise), held before the first and after the last."""

    def p_at(f):
        if f <= p_keys[0][0]:
            return p_keys[0][1]
        for (f0, p0), (f1, p1) in zip(p_keys, p_keys[1:]):
            if f0 <= f <= f1:
                return p0 if f1 == f0 else p0 + (p1 - p0) * (f - f0) / (f1 - f0)
        return p_keys[-1][1]

    return p_at


def _frames(p_keys, step):
    end = bpy.context.scene.frame_end
    return sorted({f for f, _ in p_keys if f <= end} | set(range(0, end + 1, step)))


# ---- the furnace ----------------------------------------------------------------------


def furnace(root, m, heat_on=0, tags=None, pull_chamber=True):
    """The steel chamber, pull chamber, felt, graphite heater (glowing from frame `heat_on`),
    heat shield and exhaust."""
    tags = tags or {}
    g = empty("furnace", root)
    cut(disc("floor", (0, 40, 0), SHELL_R, 80, m["steel"], g), 0.0)
    cut(shell("chamber", 0, 0, SHELL_R, 80, SHELL_TOP, 50, m["steel"], g), 0.0)
    cut(shell("lid", 0, 0, SHELL_R, SHELL_TOP, SHELL_TOP + 60, SHELL_R - PULL_R, m["steel"], g), 0.0)
    if pull_chamber:
        cut(shell("pull_chamber", 0, 0, PULL_R, SHELL_TOP + 60, PULL_TOP, 40, m["steel"], g), 0.0)
        cut(disc("pull_cap", (0, PULL_TOP + 30, 0), PULL_R, 60, m["steel"], g), 0.0)
        box("wire_drum", (-160, PULL_TOP + 60, -200), (160, PULL_TOP + 260, 120), m["dark_steel"], g)
    tag(tags, "pull chamber", "pull chamber", (PULL_R, 3300, 0), g)
    tag(tags, "chamber", "water-cooled steel chamber", (SHELL_R, 1500, 0), g)

    cut(shell("felt", 0, 0, FELT_R, FELT_Y0, FELT_Y1, 110, m["felt"], g), 3.0)
    cut(disc("felt_floor", (0, FELT_Y0 - 40, 0), FELT_R, 80, m["felt"], g), 3.0)
    phases = [("hot", m["heater_hot"], [(heat_on, END)])]
    if heat_on > 0:
        phases.append(("cold", m["graphite"], [(0, heat_on)]))
    for name, mm, iv in phases:
        w = empty(f"heater_{name}", g)
        cut(shell(f"heater_{name}_m", 0, 0, HEAT_R, HEAT_Y0, HEAT_Y1, 35, mm, w), 6.0)
        show(w, iv)
    tag(tags, "heater", "graphite heater", (HEAT_R, 500, 10), g)
    tag(tags, "felt", "felt insulation", (-FELT_R, 1300, 10), g)

    cut(funnel("heat_shield", SHIELD_Y0, SHIELD_Y1, SHIELD_R0, SHIELD_R1, 40, m["shield"], g), 9.0)
    tube("shield_strut", (SHIELD_R1, SHIELD_Y1, -100), (FELT_R - 110, SHIELD_Y1 + 60, -100), 20, m["shield"], g, verts=8)
    tag(tags, "shield", "heat shield", (-SHIELD_R1 + 60, SHIELD_Y1 - 40, 10), g)

    for s in (-1, 1):
        tube(f"exhaust{s}", (s * (SHELL_R - 100), 120, -200), (s * (SHELL_R + 300), 120, -200), 70, m["steel"], g)
    return g


def funnel(name, y0, y1, r0, r1, thick, m, parent=None):
    """A hollow cone (the heat shield): radius r0 at y0 widening to r1 at y1."""
    bpy.ops.mesh.primitive_cone_add(
        vertices=72, radius1=r0, radius2=r1, depth=y1 - y0, end_fill_type="NOTHING", location=P(0, (y0 + y1) / 2, 0)
    )
    return _solidify(bpy.context.object, name, thick, m, parent)


def cone(name, top, bottom_y, r_top, r_bot, m, parent=None):
    """A solid cone on the y axis from (0, top) down to bottom_y."""
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r_bot, radius2=r_top, depth=top - bottom_y, location=P(0, (top + bottom_y) / 2, 0))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    o.parent = parent
    return o


# ---- crucible, charge and melt ----------------------------------------------------------


def crucible(root, m, tags=None, load=None, melt=None, rise=None, spin=None):
    """The crucible group (susceptor, quartz crucible, shaft) and the melt.

    load:  beat in which chunks and dopant drop in (None: no chunks)
    melt:  beat in which the chunks melt and the pool rises (None: full melt from the start)
    rise:  (f0, f1) the crucible rises RISE while the melt gets shallower (None: it stays)
    spin:  (f0, f1, turns) the crucible group turns about its axis
    Returns (crucible group, melt top pivot)."""
    tags = tags or {}
    g = empty("crucible", root)
    cut(shell("susceptor", 0, 0, SUS_R, CRU_Y0 - 30, CRU_TOP, 30, m["graphite"], g), 12.0)
    cut(disc("susceptor_floor", (0, CRU_Y0 - 30, 0), SUS_R, 60, m["graphite"], g), 12.0)
    cut(shell("quartz", 0, 0, CRU_R, CRU_Y0, CRU_TOP, 25, m["quartz"], g), 15.0)
    cut(disc("quartz_floor", (0, CRU_Y0 + 10, 0), CRU_R, 20, m["quartz"], g), 15.0)
    tube("shaft", (0, 0, -60), (0, CRU_Y0 - 60, -60), 70, m["steel"], g, verts=24)
    tag(tags, "quartz", "quartz crucible", (CRU_R, CRU_TOP - 40, 15), g)
    tag(tags, "susceptor", "graphite susceptor", (-SUS_R, CRU_Y0 + 60, 15), g)
    tag(tags, "rise", "crucible rises as the melt drops", (SUS_R, CRU_Y0 + 40, 15), g)
    if rise:
        keyed_path(g, [(0, (0, 0, 0)), (rise[0], (0, 0, 0)), (rise[1], (0, RISE, 0)), (END, (0, RISE, 0))])
    if spin:
        # Turning the crucible itself would swing its cut-away round, so a marker block rides
        # round the rim instead.
        ring = empty("crucible_spin", g)
        box("crucible_mark", (-35, CRU_TOP - 5, SUS_R - 30), (35, CRU_TOP + 25, SUS_R + 10), m["gold"] if "gold" in m else m["steel"], ring)
        f0, f1, turns = spin
        key(ring, f0, "rotation_euler", (0, 0, 0), linear=True)
        key(ring, f1, "rotation_euler", (0, 0, 2 * math.pi * turns), linear=True)

    if load is not None:
        _charge(root, m, tags, load, melt)

    top = pivot("melt_top", (0, MELT_Y, 0), root)
    floor = (0, CRU_Y0 + 20, 0)
    bot = pivot("melt_floor", rel((0, MELT_Y, 0), floor), top)
    cut(disc("melt_m", (0, DEPTH / 2, 0), CRU_R - 26, DEPTH, m["melt_si"], bot), 18.0)
    if melt is not None:
        scale_keys(bot, [(0, (1, 1, OFF)), (F(melt, 0.15), (1, 1, OFF)), (F(melt, 0.9), 1.0), (END, 1.0)], until=F(melt, 0.15))
    if rise:
        keep = (DEPTH - RISE) / DEPTH
        scale_keys(top, [(0, 1.0), (rise[0], 1.0), (rise[1], (1, 1, keep)), (END, (1, 1, keep))])
    tag(tags, "melt", "melt near 1414 C", (-CRU_R + 120, MELT_Y - 60, 30), root)
    return g, top


def _charge(root, m, tags, load, melt):
    """Chunks and dopant dropping into the crucible in beat `load`, melting away in beat `melt`."""
    chunks = empty("chunks", root)
    gone = F(melt + 1, 0) if melt is not None else END
    show(chunks, [(0, gone)])
    k = 0
    for layer in range(4):
        n = 9 - layer
        for j in range(n):
            a = math.pi * (0.05 + 0.9 * j / max(1, n - 1))  # the back half of the crucible
            rr = (CRU_R - 70) * (0.35 + 0.6 * ((j + layer) % 3) / 2)
            x, z = rr * math.cos(a), -abs(rr * math.sin(a)) - 25
            y = CRU_Y0 + 60 + layer * 95 + (j % 2) * 20
            fall = empty(f"chunk{k}", chunks)
            sink = empty(f"chunk{k}_melt", fall, P(x, y, z))
            rock(f"chunk{k}_r", (0, 0, 0), 60 - layer * 4, m["poly"], sink)
            f0 = F(load, 0.05 + 0.025 * k)
            key(fall, f0, "location", P(0, 2200, 0))
            key(fall, f0 + 14, "location", P(0, 0, 0))
            show(fall, [(f0, gone)])
            if melt is not None:
                u = 0.15 + 0.5 * (1 - layer / 4) * 0.3 + 0.02 * j
                scale_keys(sink, [(F(melt, u), 1.0), (F(melt, min(0.92, u + 0.35)), (OFF, OFF, OFF))])
            k += 1
    tag(tags, "chunks", "polysilicon chunks", (-CRU_R + 80, CRU_Y0 + 380, -30), chunks)
    for j in range(7):
        x, z = -250 + 80 * j, -60 - 30 * (j % 3)
        e = empty(f"dopant{j}", chunks)
        ball(f"dopant{j}_s", (x, CRU_Y0 + 200 + 40 * (j % 2), z), 18, m["dopant"], e, 10)
        f0 = F(load, 0.5 + 0.04 * j)
        key(e, f0, "location", P(0, 2200, 0))
        key(e, f0 + 14, "location", P(0, 0, 0))
        show(e, [(f0, F(melt, 0.5) if melt is not None else END)])
    tag(tags, "dopant", "dopant: boron or phosphorus", (150, CRU_Y0 + 260, -60), chunks)


# ---- the crystal ------------------------------------------------------------------------


def crystal(root, m, p_keys, contact, tags=None, spin=None, wire=True, neck_r=NECK_R):
    """The seed on its wire and the crystal (neck, shoulder, body, tail). `p_keys` is the rise;
    the parts freeze on once the seed touches the melt at frame `contact`. `spin` is
    (f0, f1, turns). Returns the crystal group."""
    tags = tags or {}
    p_at = p_fn(p_keys)

    def grown(f):
        return 0.0 if f < contact else p_at(f)

    g = empty("crystal", root)
    for f in _frames(p_keys, 6):
        key(g, f, "location", P(0, p_at(f), 0), linear=True)
    if spin:
        f0, f1, turns = spin
        key(g, f0, "rotation_euler", (0, 0, 0), linear=True)
        key(g, f1, "rotation_euler", (0, 0, -2 * math.pi * turns), linear=True)

    box("seed", (-12, MELT_Y, -12), (12, MELT_Y + SEED, 12), m["seed"], g)
    box("chuck", (-30, MELT_Y + SEED, -30), (30, MELT_Y + SEED + 50, 30), m["dark_steel"], g)
    tag(tags, "seed", "oriented seed crystal", (12, MELT_Y + SEED / 2, 10), g)

    if wire:
        w = pivot("wire", (0, PULL_TOP, 0), root)
        length = PULL_TOP - (MELT_Y + SEED + 50)
        tube("wire_m", (0, 0, 0), (0, -length, 0), 3, m["steel"], w, verts=6)
        for f in _frames(p_keys, 6):
            key(w, f, "scale", (1, 1, max(OFF, (length - p_at(f)) / length)), linear=True)

    def grow(name, hi, lo, make, uniform=False):
        pv = pivot(name, (0, MELT_Y + hi, 0), g)
        make(pv)
        prev = None
        for f in _frames(p_keys, 3):
            r = max(0.0, min(1.0, (grown(f) + hi) / (hi - lo)))
            if r <= 0:
                s = (OFF, OFF, OFF)
            else:
                s = (r, r, r) if uniform else (1, 1, r)
                if not uniform and (prev is None or prev <= 0) and f > 0:
                    key(pv, f - 1, "scale", (1, 1, OFF), linear=True)
            key(pv, f, "scale", s, linear=True)
            prev = r
        return pv

    grow("neck", 0.0, NECK_BOT, lambda pv: tube("neck_m", (0, 0, 0), (0, NECK_BOT, 0), neck_r, m["xtal"], pv, verts=12))
    grow("shoulder", NECK_BOT, BODY_TOP, lambda pv: cone("shoulder_m", 0, BODY_TOP - NECK_BOT, neck_r, XTAL_R, m["xtal"], pv), uniform=True)
    grow("body", BODY_TOP, BODY_BOT, lambda pv: disc("body_m", (0, -BODY / 2, 0), XTAL_R, BODY, m["xtal"], pv, 64))
    grow("tail", BODY_BOT, TAIL_BOT, lambda pv: cone("tail_m", 0, -TAIL, XTAL_R, 25, m["xtal"], pv))
    if spin:
        # a dark stripe down the body shows the crystal turning
        stripe = grow("stripe", BODY_TOP, BODY_BOT, lambda pv: box("stripe_m", (-20, -BODY, XTAL_R - 6), (20, 0, XTAL_R + 4), m["graphite"], pv))
        stripe.name = "stripe"

    tag(tags, "neck", "dash neck 2-4 mm, pulled fast", (neck_r, MELT_Y - 30, 10), g)
    tag(tags, "shoulder", "shoulder flares to 300 mm", (XTAL_R, MELT_Y + BODY_TOP + 40, 10), g)
    tag(tags, "body", "body: 1.0-1.6 mm per min", (XTAL_R, MELT_Y + BODY_TOP - 900, 10), g)
    tag(tags, "tail", "tail cone", (XTAL_R * 0.6, MELT_Y + BODY_BOT - 120, 10), g)
    tag(tags, "lifted", "lifted clear to cool", (XTAL_R, MELT_Y + BODY_BOT + 400, 10), g)
    return g


def argon(root, m, b, tags=None, u0=0.0, u1=0.75):
    """Argon from the top of the pull chamber, down past the crystal, over the melt and out at
    the bottom, through beat `b`."""
    tags = tags or {}
    g = empty(f"argon{b}", root)
    for s in (-1, 1):
        path = [
            (s * 200, PULL_TOP - 100, 20),
            (s * 200, SHIELD_Y1, 20),
            (s * (SHIELD_R0 - 30), SHIELD_Y0, 20),
            (s * (CRU_R - 40), MELT_Y + 40, 20),
            (s * (SUS_R + 50), CRU_TOP + 40, 20),
            (s * (HEAT_R + 70), 300, 20),
            (s * (SHELL_R - 120), 140, 20),
        ]
        run(g, f"ar{b}{s:+d}_", 9, path, 35, m["argon"], b, u0, u1, 70)
    tag(tags, "argon", "argon sweeps out SiO and CO", (200, 2800, 20), g)
    return g


def static_p(p):
    """p_keys for a crystal that is already grown to rise `p` and holds there."""
    return [(0, p)]
