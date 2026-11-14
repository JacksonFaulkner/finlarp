"""The ten SAND write-up sections, each a 3D picture authored in Blender and exported for pbr3d, in
the overview's style: slow push-in cameras, `label:<text>` tags pinned by the TUI, and framing
for the left pane (the beat's text sits in a panel on the right).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/sand_sections.py

For each section it writes:
  blender/sand_sec<N>.blend   open it in Blender to edit by hand
  assets/sand_sec<N>.glb      what pbr3d embeds and plays back

  1  what happens   the plant left to right: raw piles, furnace and tap, cast, crush, bin
  2  inside a SAF   the furnace in section by zone, the three electrodes from above, the hearth
  3  the chemistry  three reactions as atoms on a temperature column: cool top, hot cavity
  4  by the numbers three gauges: temperature, energy per tonne, purity
  5  who makes it   output by country as bars, then the world total with China's share
  6  price          the US price per pound, 2021 to 2025e, as bars
  7  purity ladder  three blocks of silicon, their impurity dots thinning out 2N, 6N, 9N
  8  chokepoint     the Spruce Pine share, quartz into a crucible, the supply line broken
  9  market context US imports, the trade gate, the China #553 price
  10 sources        four source cards filing into a stack

One beat is SEC (8) seconds at 24 fps; each section is three beats. Helpers come from
sand_overview.py and sand_zooms.py.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_zooms as Z  # noqa: E402
from sand_overview import (  # noqa: E402
    OFF,
    F,
    P,
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
    wall,
)
from sand_zooms import camera, finish, scale_keys, stream_of  # noqa: E402

BEATS = 3
ALL = [(0, F(BEATS, 0))]


def start(n):
    m, root = Z.start(f"sec{n}", BEATS)
    m["si_atom"] = mat("atom_si", (0.62, 0.64, 0.70), metal=0.5, rough=0.3)
    m["o_atom"] = mat("atom_o", (0.85, 0.20, 0.16), rough=0.4)
    m["c_atom"] = mat("atom_c", (0.10, 0.10, 0.11), rough=0.5)
    m["gold"] = mat("gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["blue"] = mat("blue", (0.36, 0.56, 0.82), metal=0.2, rough=0.45)
    m["grey"] = mat("grey", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    m["red"] = mat("red", (0.90, 0.22, 0.18), emit=(0.9, 0.15, 0.1), strength=2.5)
    m["plinth"] = mat("plinth", (0.18, 0.19, 0.23), rough=0.8)
    m["paper"] = mat("paper", (0.90, 0.88, 0.82), rough=0.85)
    m["hot1"] = mat("hot1", (0.55, 0.18, 0.08), rough=0.8, emit=(1.0, 0.3, 0.05), strength=0.25)
    m["hot2"] = mat("hot2", (0.45, 0.30, 0.16), rough=0.85)
    m["fill_hot"] = mat("fill_hot", (1.0, 0.45, 0.15), emit=(1.0, 0.4, 0.1), strength=1.2)
    m["cool"] = mat("cool", (0.30, 0.24, 0.20), rough=0.9)
    return m, root


def grow_bar(g, name, x, z, w, h, m, f0, f1, y0=0.0, depth=None):
    """A bar w wide (and deep) standing at (x, y0, z) that grows from nothing to height h between
    frames f0 and f1 and then stays."""
    d = depth or w
    b = pivot(name, (x, y0, z), g)
    box(f"{name}_box", (-w / 2, 0, -d / 2), (w / 2, h, d / 2), m, b)
    scale_keys(b, [(0, (OFF,) * 3), (f0, (1, 1, OFF)), (f1, (1, 1, 1)), (F(BEATS, 0), (1, 1, 1))], until=f0)
    return b


def plinth(g, x0, x1, z0=-600, z1=600, y=0.0):
    box("plinth", (x0, y - 80, z0), (x1, y, z1), mag("plinth"), g)


_M = {}


def mag(name):
    return _M[name]


# ---- 1. what happens: rock to metallurgical-grade silicon ------------------------------


def sec1():
    m, root = start(1)
    _M.update(m)
    g = empty("sec1", root)
    plinth(g, -3600, 4600, -1200, 900)
    # raw piles: quartzite, coke, wood chips
    for k, (x, mm, name) in enumerate(((-3000, m["quartz"], "quartzite"), (-2200, m["coke"], "coke"), (-1400, mag("gold"), "wood chips"))):
        for j in range(9):
            a = j * 2.4
            r = 120 + 140 * (j % 3)
            rock(f"pile{k}_{j}", (x + r * math.cos(a), 90 + 110 * (2 - j % 3), -300 + r * math.sin(a) * 0.6), 120, mm if name != "wood chips" else mat("chips", (0.55, 0.38, 0.20), rough=0.9), g)
    label("quartzite, SiO2", (-3000, 420, -300), g, beat(0))
    label("coke and coal", (-2200, 420, -300), g, beat(0))
    label("wood chips", (-1400, 420, -300), g, beat(0))
    box("belt", (-3300, 160, 150), (-200, 220, 450), m["rubber"], g)
    label("crushed, sized, blended", (-1800, 220, 450), g, beat(0))
    for k in range(10):
        e = empty(f"lump{k}", g)
        rock(f"lump{k}_r", (-3200, 260, 300), 70, (m["quartz"], m["coke"], mat("chips", (0.55, 0.38, 0.20), rough=0.9))[k % 3], e)
        f0 = F(0, 0.05 + 0.08 * k)
        fly(e, [(0, 0, 0), (2900, 0, 0), (3000, 700, -300)], f0, f0 + 90, steps=4)
        show(e, [(f0, min(f0 + 90, F(1, 0.2)))])

    # the furnace, cut open, with its glow; the tap stream into a ladle
    cut(wall("shell", 800, 0, 1300, 90, m["lining"], g), 0.0)
    cut(disc("charge", (0, 650, 0), 710, 900, m["charge"], g), 3.0)
    cut(disc("pool", (0, 150, 0), 710, 160, m["melt"], g), 4.0)
    for i, x in enumerate((-300, 300)):
        cut(disc(f"el{i}", (x, 1250, 0), 90, 1400, m["electrode"], g, 32), 12.0)
        cut(ball(f"cav{i}", (x, 420, 0), 150, m["cavity"], g, 24), 9.0)
    disc("roof", (0, 1340, -400), 820, 80, m["steel"], g)
    label("electric arc furnace, 24/7", (800, 1100, 0), g, beat(1))
    box("launder", (800, 100, -80), (1500, 140, 80), m["refractory"], g)
    lad = empty("ladle", g)
    cup("ladle_body", (1800, 0, 0), 300, 420, m["dark_steel"], lad)
    disc("ladle_bot", (1800, 15, 0), 300, 30, m["dark_steel"], lad)
    fill = pivot("ladle_fill", (1800, 30, 0), lad)
    disc("ladle_si", (0, 180, 0), 285, 360, m["melt"], fill)
    scale_keys(fill, [(0, (1, 1, OFF)), (F(1, 0.3), (1, 1, OFF)), (F(1, 0.9), (1, 1, 1)), (F(2, 0.2), (1, 1, 1)), (F(2, 0.45), (1, 1, 0.1)), (F(3, 0), (1, 1, 0.1))])
    stm = empty("stream", g)
    tube("stream_t", (800, 160, 0), (1500, 160, 0), 30, m["melt"], stm, verts=10)
    tube("stream_f", (1500, 160, 0), (1700, 380, 0), 28, m["melt"], stm, verts=10)
    show(stm, [(F(1, 0.3), F(1, 0.9))])
    label("tap: liquid Si runs to the ladle", (1500, 200, 80), g, beat(1))
    label("ladle", (2100, 420, 0), g, beat(1))

    # cast, crushed, binned
    box("bed", (2400, 0, -350), (3300, 60, 350), m["dark_steel"], g)
    slab = pivot("slab", (2850, 60, 0), g)
    box("slab_si", (-420, 0, -300), (420, 70, 300), m["silicon"], slab)
    scale_keys(slab, [(0, OFF), (F(2, 0.25), (1, 1, OFF)), (F(2, 0.5), 1), (F(3, 0), 1)], until=F(2, 0.25))
    label("cast", (2850, 140, 350), g, beat(2))
    box("crusher", (3500, 0, -300), (3900, 600, 300), m["steel"], g)
    label("crushed and screened", (3700, 600, 300), g, beat(2))
    for i in range(12):
        e = empty(f"prod{i}", g)
        x, z = 4100 + (i % 4) * 110, -150 + (i // 4) * 140
        rock(f"prod{i}_r", (x, 80 + (i // 8) * 70, z), 60, m["silicon"], e)
        f0 = F(2, 0.55 + 0.03 * i)
        key(e, f0, "location", P(3900 - x, 500, -z))
        key(e, f0 + 14, "location", P(0, 0, 0))
        show(e, [(f0, F(3, 0))])
    label("98-99% Si, about 2N", (4300, 260, 200), g, [(F(2, 0.6), F(3, 0))])
    camera(root, [((-2000, 400, 0), 5600, 0.30, 0.30), ((700, 500, 0), 5200, 0.25, 0.22), ((3200, 300, 0), 4800, 0.30, 0.30)])
    finish("sec1")


# ---- 2. inside a submerged arc furnace --------------------------------------------------


def sec2():
    m, root = start(2)
    _M.update(m)
    g = empty("sec2", root)
    R = 1800
    cut(disc("base", (0, -60, 0), R + 40, 120, m["steel"], g), 0.0)
    cut(wall("lining", R, 0, 2200, 160, m["lining"], g), 0.0)
    # zones in the charge, coolest at the top
    cut(disc("zone_top", (0, 1750, 0), R - 160, 700, m["charge"], g), 3.0)
    cut(disc("zone_mid", (0, 1050, 0), R - 160, 700, m["cool"], g), 3.5)
    cut(disc("zone_low", (0, 480, 0), R - 160, 440, mat("sic_zone", (0.25, 0.32, 0.29), rough=0.6), g), 4.0)
    cut(disc("pool", (0, 130, 0), R - 160, 260, m["melt"], g), 4.5)
    label("upper charge: cooler, preheating", (-1100, 1900, 3), g, beat(0))
    label("SiO meets carbon: SiC forms", (-1100, 1150, 4), g, beat(0))
    label("SiC layer round the cavities", (-1200, 520, 4), g, beat(0))
    label("liquid silicon on the hearth", (900, 130, 5), g, beat(0) + beat(2))
    els = [(-780, 0), (780, 0), (0, -1100)]
    for i, (x, z) in enumerate(els):
        e = empty(f"el{i}", g)
        if z > -1:
            cut(disc(f"el{i}_rod", (x, 1900, z), 210, 2600, m["electrode"], e, 40), 12.0)
        else:
            disc(f"el{i}_rod", (x, 1900, z), 210, 2600, m["electrode"], e, 40)
        cav = pivot(f"cav{i}", (x, 520, z), g)
        if z > -1:
            cut(ball(f"cav{i}_gas", (0, 0, 0), 300, m["cavity"], cav, 32), 9.0)
        else:
            ball(f"cav{i}_gas", (0, 0, 0), 300, m["cavity"], cav, 32)
        keys, f, k = [], 0, 0
        while f < F(BEATS, 0):
            keys.append((f, (1.0, 1.05, 0.96, 1.02)[k % 4]))
            f += 6
            k += 1
        scale_keys(cav, keys)
        # electrodes are slipped down as they burn, beat 2
        key(e, F(2, 0.2), "location", P(0, 0, 0))
        key(e, F(2, 0.7), "location", P(0, -120, 0))
        key(e, F(3, 0) - 1, "location", P(0, -120, 0))
        tube(f"bus{i}", (x, 3200, z), (x * 1.2 + 2600, 3600, z * 1.2), 60, mat("copper", (0.85, 0.48, 0.30), metal=0.9, rough=0.3), g, verts=12)
    box("transformer", (2900, 3100, -900), (3900, 4100, 900), m["dark_steel"], g)
    label("three-phase transformer", (3400, 4100, 0), g, beat(1))
    label("three carbon electrodes", (els[0][0], 3100, els[0][1]), g, beat(1))
    label("one arc cavity per electrode", (els[1][0], 820, els[1][1]), g, beat(1))
    label("electrodes burn away and are slipped down", (els[0][0] + 210, 1500, 12), g, beat(2))
    box("taphole", (R - 170, 60, -120), (R + 60, 260, 120), m["coke"], g)
    label("tap hole", (R + 60, 260, 0), g, beat(2))
    camera(root, [((0, 1100, 0), 9200, 0.15, 0.12), ((800, 1800, -200), 10500, 0.45, 0.85), ((600, 700, 0), 6800, 0.35, 0.12)])
    finish("sec2")


# ---- 3. the chemistry -------------------------------------------------------------------

AR = {"Si": 190, "O": 140, "C": 130}
AS = 1.6  # spacing of the atoms in a molecule


def molecule(g, name, at, atoms, m):
    """Atoms (dx, dy, kind) round point `at`, in one group whose origin is `at`."""
    e = pivot(name, at, g)
    for k, (dx, dy, kind) in enumerate(atoms):
        ball(f"{name}_{k}", (dx * AS, dy * AS, 0), AR[kind], m[{"Si": "si_atom", "O": "o_atom", "C": "c_atom"}[kind]], e, 20)
    return e


def react(g, m, b, y, ins, outs):
    """Reactants slide in from the sides and meet at (0, y) in the first half of beat b;
    products appear there and slide apart in the second half."""
    for k, (name, x, atoms) in enumerate(ins):
        e = molecule(g, f"in{b}_{k}", (x, y, 0), atoms, m)
        key(e, F(b, 0.1), "location", P(x, y, 0))
        key(e, F(b, 0.45), "location", P(x * 0.18, y, 0))
        show(e, [(0, F(b, 0.5))] if b == 0 else [(F(b, 0), F(b, 0.5))])
        label(name, (0, 330, 0), e, [(F(b, 0), F(b, 0.45))])
    for k, (name, x, atoms) in enumerate(outs):
        e = molecule(g, f"out{b}_{k}", (x * 0.18, y, 0), atoms, m)
        key(e, F(b, 0.5), "location", P(x * 0.18, y, 0))
        key(e, F(b, 0.85), "location", P(x, y, 0))
        show(e, [(F(b, 0.5), F(b + 1, 0))])
        label(name, (0, 330, 0), e, [(F(b, 0.55), F(b + 1, 0))])


def sec3():
    m, root = start(3)
    _M.update(m)
    g = empty("sec3", root)
    # the backdrop: a column of the furnace from the cool top to the hot cavity
    box("band_top", (-1600, 1800, -400), (1600, 2700, -300), m["cool"], g)
    box("band_mid", (-1600, 900, -400), (1600, 1800, -300), m["hot2"], g)
    box("band_low", (-1600, 0, -400), (1600, 900, -300), m["hot1"], g)
    label("upper shaft, cooler", (-1600, 2500, -300), g, ALL)
    label("cavity, above 1800 C", (-1600, 300, -300), g, ALL)
    sio2 = [(0, 0, "Si"), (-170, 60, "O"), (170, 60, "O")]
    c = [(0, 0, "C")]
    sio = [(0, 0, "Si"), (170, 0, "O")]
    co = [(0, 0, "C"), (140, 0, "O")]
    sic = [(0, 0, "Si"), (170, 0, "C")]
    si = [(0, 0, "Si")]
    # beat 0, in the hot zone: SiO2 + C -> SiO + CO
    react(g, m, 0, 450, [("SiO2", -1000, sio2), ("C", 1000, c)], [("SiO gas", -900, sio), ("CO", 900, co)])
    # beat 1, higher and cooler: SiO + 2C -> SiC + CO
    react(g, m, 1, 2200, [("SiO", -1000, sio), ("2C", 1000, [(0, 0, "C"), (0, 200, "C")])], [("SiC", -900, sic), ("CO", 900, co)])
    # beat 2, back at the cavity: SiO + SiC -> 2Si + CO
    react(g, m, 2, 600, [("SiO", -1000, sio), ("SiC", 1000, sic)], [("2 Si, liquid", -900, [(0, 0, "Si"), (0, 260, "Si")]), ("CO", 900, co)])
    # arrows of the gas path: SiO rises in beat 1, falls back in beat 2
    for b, (y0, y1) in ((1, (700, 2000)), (2, (2000, 800))):
        stream_of(g, f"climb{b}", 6, (-1300, y0, 0), [(0, 0, 0), (0, y1 - y0, 0)], 40, m["sio"], b, 0.0, 0.4, 50)
    camera(root, [((0, 600, 0), 5400, 0.10, 0.06), ((0, 1900, 0), 5400, 0.10, 0.06), ((0, 900, 0), 5600, -0.10, 0.08)])
    finish("sec3")


# ---- 4. by the numbers ------------------------------------------------------------------


def gauge(g, name, x, h, fill_to, m_fill, b, marks):
    """A glass column at x, h tall, filling to `fill_to` during beat b, with tick marks."""
    tube(f"{name}_glass", (x, 0, 0), (x, h, 0), 230, mag("pipe_glass"), g, verts=32)
    disc(f"{name}_foot", (x, -40, 0), 330, 80, mag("dark_steel"), g, 32)
    f = pivot(f"{name}_fill", (x, 0, 0), g)
    tube(f"{name}_liquid", (0, 0, 0), (0, fill_to, 0), 190, m_fill, f, verts=32)
    scale_keys(f, [(0, (1, 1, 0.02)), (F(b, 0.1), (1, 1, 0.02)), (F(b, 0.7), (1, 1, 1)), (F(3, 0), (1, 1, 1))])
    for text, y in marks:
        box(f"{name}_tick{y}", (x + 230, y - 10, -20), (x + 380, y + 10, 20), mag("steel"), g)
        label(text, (x + 380, y, 0), g, [(F(b, 0.3), F(3, 0))])


def sec4():
    m, root = start(4)
    _M.update(m)
    g = empty("sec4", root)
    plinth(g, -2600, 2800, -700, 700)
    # temperature: 0-2000 C over 3000 mm
    gauge(g, "temp", -1700, 3200, 1900 * 1.5, m["fill_hot"], 0, [("Si melts, 1414 C", 1414 * 1.5), ("arc zone, above 1800 C", 1800 * 1.5)])
    # energy: 0-14 MWh/t over 3000 mm
    gauge(g, "mwh", 0, 3200, 12 * 220, m["blue"], 1, [("11 MWh per tonne", 11 * 220), ("13 MWh per tonne", 13 * 220)])
    box("mwh_band", (-260, 11 * 220, -260), (260, 13 * 220, 260), mat("band", (0.6, 0.8, 1.0), emit=(0.5, 0.75, 1.0), strength=0.6, alpha=0.25), g)
    # purity: 90-100% over 3000 mm
    gauge(g, "pure", 1700, 3200, (98.5 - 90) * 300, m["silicon"], 2, [("98%", 8 * 300), ("99%, about 2N", 9 * 300)])
    label("temperature", (-1700, -40, 330), g, ALL)
    label("power per tonne", (0, -40, 330), g, ALL)
    label("purity, 90-100% scale", (1700, -40, 330), g, ALL)
    camera(root, [((-1300, 1600, 0), 8400, 0.25, 0.12), ((0, 1600, 0), 8400, 0.15, 0.12), ((1300, 1600, 0), 8400, -0.2, 0.12)])
    finish("sec4")


# ---- 5. who makes it --------------------------------------------------------------------

KT = 0.75  # mm of bar per thousand tonnes


def sec5():
    m, root = start(5)
    _M.update(m)
    g = empty("sec5", root)
    plinth(g, -1000, 5400, -700, 700)
    grow_bar(g, "china", 0, 0, 600, 4000 * KT, mat("china", (0.86, 0.30, 0.25), rough=0.5), F(0, 0.1), F(0, 0.7))
    label("China 4,000 kt", (0, 4000 * KT, 300), g, ALL)
    others = [("Brazil 180", 180), ("Norway 130", 130), ("France 68", 68), ("rest 222", 222)]
    for k, (name, kt) in enumerate(others):
        x = 1100 + 750 * k
        grow_bar(g, f"bar{k}", x, 0, 450, kt * KT, m["blue"], F(1, 0.1 + 0.1 * k), F(1, 0.4 + 0.1 * k))
        label(name, (x, kt * KT + 20, 225), g, [(F(1, 0.3), F(3, 0))])
    # world total: a stacked bar to the right, China's share in red
    wx = 4600
    grow_bar(g, "world_china", wx, 0, 600, 4000 * KT, mat("china", (0.86, 0.30, 0.25), rough=0.5), F(2, 0.1), F(2, 0.5))
    grow_bar(g, "world_rest", wx, 0, 600, 600 * KT, m["blue"], F(2, 0.5), F(2, 0.65), y0=4000 * KT)
    label("world 4,600 kt, China about 87%", (wx, 4600 * KT, 300), g, [(F(2, 0.5), F(3, 0))])
    camera(root, [((300, 1600, 0), 8200, 0.20, 0.12), ((2300, 400, 0), 5800, 0.15, 0.15), ((2200, 1800, 0), 12000, 0.12, 0.12)])
    finish("sec5")


# ---- 6. price ---------------------------------------------------------------------------


def sec6():
    m, root = start(6)
    _M.update(m)
    g = empty("sec6", root)
    plinth(g, -600, 4600, -600, 600)
    data = [("2021", 220), ("2022", 362), ("2023", 180), ("2024", 170), ("2025e", 130)]
    when = [0, 0, 1, 1, 2]
    for k, (yr, c) in enumerate(data):
        x = 1000 * k
        b = when[k]
        u = 0.1 + 0.3 * (k - when.index(b))
        mm = mat("peak", (0.94, 0.62, 0.30), rough=0.45) if c == 362 else m["gold"]
        grow_bar(g, f"y{yr}", x, 0, 600, c * 8, mm, F(b, u), F(b, u + 0.3))
        label(f"{yr}: {c} c/lb", (x, c * 8, 300), g, [(F(b, u + 0.2), F(3, 0))])
    box("floor_line", (-500, 0, 320), (4500, 20, 340), m["steel"], g)
    camera(root, [((500, 1600, 0), 6800, 0.20, 0.12), ((1800, 1300, 0), 7400, 0.15, 0.14), ((2000, 1300, 0), 8000, -0.10, 0.14)])
    finish("sec6")


# ---- 7. purity ladder -------------------------------------------------------------------


def sec7():
    m, root = start(7)
    _M.update(m)
    g = empty("sec7", root)
    plinth(g, -2600, 2600, -800, 800)
    rng = random.Random(7)
    steps = [(-1700, 70, "metallurgical, 98-99%"), (0, 4, "solar, 99.9999% (6N)"), (1700, 0, "electronic, 99.9999999% (9N)")]
    for k, (x, dots, name) in enumerate(steps):
        blk = pivot(f"blk{k}", (x, 0, 0), g)
        box(f"blk{k}_glass", (-550, 0, -550), (550, 1100, 550), mat("si_glass", (0.70, 0.74, 0.82), metal=0.3, rough=0.15, alpha=0.35), blk)
        scale_keys(blk, [(0, (OFF,) * 3), (F(k, 0.05), (1, 1, OFF)), (F(k, 0.35), (1, 1, 1)), (F(3, 0), (1, 1, 1))], until=F(k, 0.05))
        for j in range(dots):
            dx = rng.uniform(-450, 450)
            dy = rng.uniform(100, 1000)
            dz = rng.uniform(-450, 450)
            d = empty(f"dot{k}_{j}", g)
            ball(f"dot{k}_{j}_b", (x + dx, dy, dz), 32, m["red"], d, 10)
            show(d, [(F(k, 0.35), F(3, 0))])
        label(name, (x, 1100, 550), g, [(F(k, 0.3), F(3, 0))])
    label("10,000 ppm of impurities", (-1700 + 550, 500, 550), g, beat(0))
    label("about 1 ppm", (550, 500, 550), g, beat(1))
    label("about 1 ppb: no dots at this scale", (1700 + 550, 500, 550), g, beat(2))
    camera(root, [((-1500, 600, 0), 4600, 0.30, 0.25), ((-200, 600, 0), 5600, 0.20, 0.25), ((200, 600, 0), 8800, 0.15, 0.28)])
    finish("sec7")


# ---- 8. chokepoint: high-purity quartz --------------------------------------------------


def sec8():
    m, root = start(8)
    _M.update(m)
    g = empty("sec8", root)
    # Spruce Pine: a terraced pit of white quartz, and a share ring
    for k in range(4):
        r0 = 1300 - 280 * k
        disc(f"terrace{k}", (-2200, 60 + 120 * k, 0), r0, 120, m["quartz"] if k else mat("rock_grey", (0.45, 0.43, 0.40), rough=0.95), g, 48)
    label("Spruce Pine, North Carolina", (-2200, 480, 1300), g, beat(0))
    ring = pivot("share", (-2200, 1500, 0), g)
    for k in range(20):
        a = 2 * math.pi * k / 20
        on = k < 16  # 80%: the middle of the 70-90% estimate
        e = empty(f"seg{k}", ring)
        box(f"seg{k}_b", (-60 + 600 * math.cos(a), 600 * math.sin(a) - 60, -60), (60 + 600 * math.cos(a), 600 * math.sin(a) + 60, 60), m["gold"] if on else m["grey"], e)
        show(e, [(F(0, 0.1 + 0.03 * k), F(3, 0))])
    label("an estimated 70-90% of high-purity quartz", (-2200 + 600, 1500 + 600, 60), g, [(F(0, 0.5), F(1, 0))])
    # the line to a crucible in a puller
    box("belt", (-1000, 300, -200), (900, 360, 200), m["rubber"], g)
    pull = pivot("puller", (1600, 0, 0), g)
    cut(wall("puller_shell", 700, 0, 1800, 50, m["steel"], pull), 0.0)
    cup("crucible", (0, 300, -60), 420, 380, m["quartz"], pull)
    disc("crucible_melt", (0, 500, -60), 400, 300, m["melt"], pull)
    label("quartz crucible holds the melt", (1600 + 420, 680, 0), g, beat(1))
    label("lasts hundreds of hours", (1600, 1800, 0), g, beat(1))
    for k in range(9):
        e = empty(f"q{k}", g)
        rock(f"q{k}_r", (-1000, 420, 0), 70, m["quartz"], e)
        f0 = F(1, 0.05 + 0.08 * k)
        fly(e, [(0, 0, 0), (1900, 0, 0), (2500, 300, 0)], f0, f0 + 70, steps=4)
        show(e, [(f0, f0 + 70)])
    # beat 2: the line breaks; the alarm
    gap = empty("gap", g)
    box("gap_black", (-150, 290, -210), (250, 370, 210), mat("void", (0.03, 0.03, 0.04), rough=1.0), gap)
    show(gap, [(F(2, 0.1), F(3, 0))])
    alarm = empty("alarm", g)
    ball("alarm_b", (50, 700, 0), 120, m["red"], alarm, 16)
    show(alarm, [(F(2, 0.15 + 0.1 * k), F(2, 0.2 + 0.1 * k)) for k in range(8)])
    label("Hurricane Helene, 2024", (50, 820, 0), g, [(F(2, 0.15), F(3, 0))])
    camera(root, [((-2000, 1100, 0), 6800, 0.25, 0.25), ((700, 700, 0), 6400, 0.25, 0.22), ((-300, 800, 0), 9200, 0.20, 0.25)])
    finish("sec8")


# ---- 9. market context ------------------------------------------------------------------


def sec9():
    m, root = start(9)
    _M.update(m)
    g = empty("sec9", root)
    plinth(g, -2600, 3200, -900, 900)
    grow_bar(g, "imp24", -1900, 0, 600, 117 * 12, m["blue"], F(0, 0.1), F(0, 0.4))
    grow_bar(g, "imp25", -1000, 0, 600, 180 * 12, m["blue"], F(0, 0.4), F(0, 0.7))
    label("US imports 2024: 117 kt", (-1900, 117 * 12, 300), g, [(F(0, 0.3), F(3, 0))])
    label("2025e: 180 kt", (-1000, 180 * 12, 300), g, [(F(0, 0.6), F(3, 0))])
    # the trade gate and containers passing it
    for x in (300, 1300):
        box(f"post{x}", (x - 80, 0, -500), (x + 80, 1500, -340), m["steel"], g)
    box("gate_beam", (220, 1400, -500), (1380, 1540, -340), mat("gate", (0.92, 0.70, 0.25), rough=0.5), g)
    label("tariffs and export curbs", (800, 1540, -420), g, beat(1))
    for k in range(3):
        e = empty(f"box{k}", g)
        box(f"box{k}_b", (-700, 0, -380), (-100, 450, 100), (m["blue"], mat("cont_red", (0.7, 0.25, 0.2), rough=0.6), m["grey"])[k], e)
        f0 = F(1, 0.05 + 0.25 * k)
        key(e, f0, "location", P(0, 0, 0), linear=True)
        key(e, f0 + 110, "location", P(2600, 0, 0), linear=True)
        show(e, [(f0, min(f0 + 110, F(2, 0)))])
    label("critical minerals list, Nov 2025", (1800, 500, 100), g, [(F(1, 0.4), F(2, 0))])
    grow_bar(g, "cny", 2500, 0, 600, 10600 * 0.16, mat("china", (0.86, 0.30, 0.25), rough=0.5), F(2, 0.1), F(2, 0.5))
    label("China #553: ~10,600 yuan/t, early 2025", (2500, 10600 * 0.16, 300), g, [(F(2, 0.4), F(3, 0))])
    camera(root, [((-1400, 1100, 0), 5600, 0.25, 0.15), ((800, 800, 0), 5800, 0.25, 0.18), ((900, 1000, 0), 9000, 0.20, 0.15)])
    finish("sec9")


# ---- 10. sources ------------------------------------------------------------------------


def sec10():
    m, root = start(10)
    _M.update(m)
    g = empty("sec10", root)
    plinth(g, -1600, 1600, -1100, 1100)
    cards = ["[1] USGS Mineral Commodity Summaries 2026", "[2] US patent 12157671, hrcak paper", "[3] Spruce Pine HPQ, konvoy", "[4] China #553, SMM daily review"]
    for k, text in enumerate(cards):
        e = empty(f"card{k}", g)
        box(f"card{k}_b", (-700, 0, -500), (700, 30, 500), m["paper"], e)
        box(f"card{k}_rule", (-600, 30, -380), (300, 34, -340), m["gold"], e)
        b = 0 if k < 2 else 1
        f0 = F(b, 0.1 + 0.4 * (k % 2))
        key(e, f0, "location", P(-2600 + 600 * k, 1800, 1200))
        key(e, f0 + 60, "location", P(220 * k - 330, 60 * k, 260 * k - 390))
        show(e, [(f0, F(3, 0))])
        label(text[:56], (-700, 30, 500), e, [(f0 + 50, F(3, 0))])
    camera(root, [((0, 300, 0), 5600, 0.25, 0.45), ((0, 300, 0), 5600, 0.15, 0.45), ((0, 250, 0), 5200, 0.05, 0.40)])
    finish("sec10")


def build_all():
    for f in (sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9, sec10):
        f()


if __name__ == "__main__":
    which = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []
    if which:
        for n in which:
            globals()[f"sec{n}"]()
    else:
        build_all()
