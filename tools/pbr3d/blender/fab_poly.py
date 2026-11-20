"""The POLYSILICON page as 3D pictures from Blender through pbr3d: an overview, four zoom-ins and ten sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/fab_poly.py [-- jar sec2 ...]

Writes assets/poly_<name>.glb and blender/poly_<name>.blend for each scene (the zooms and
sections; the overview below is the old stand-in, poly_overview.py writes the real one).

  overview  poly_overview  the chain: MG-Si, fluidised bed, distillation, bell jar, chunks
  zooms     a bed    the fluidised bed: Si + HCl makes TCS, bubbles and particles
            b column distillation: TCS and STC separated on trays
            c jar    the Siemens bell jar: rods grow from 20 mm to 150 mm
            d loop   recycling H2 and HCl, and the growth-rate trade-off
  sections  1 what happens  2 bell jar  3 chemistry  4 by the numbers  5 impurity limits
            6 who makes it  7 solar vs chip grade  8 chokepoints  9 listed names  10 sources
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbr_kit import *  # noqa: F401,F403  (the shared helpers, see pbr_kit.py)

BF = BEAT_FRAMES


def poly_mats():
    return dict(
        steel=mat("steel", (0.35, 0.37, 0.42), metal=0.6, rough=0.4),
        glass=mat("clear_glass", (0.9, 0.93, 0.96), rough=0.05, alpha=0.02),
        si=mat("poly_si", (0.56, 0.58, 0.63), metal=0.85, rough=0.25),
        rod=mat("rod_si", (0.62, 0.64, 0.68), metal=0.8, rough=0.3),
        graphite=mat("graphite", (0.06, 0.06, 0.07), rough=0.7),
        gas=mat("gas", (0.90, 0.90, 0.95), emit=(0.9, 0.9, 0.95), strength=0.8, alpha=0.5),
        hot=mat("hot_rod", (1.0, 0.6, 0.25), emit=(1.0, 0.6, 0.25), strength=3.0),
        arc=mat("current", (0.6, 0.85, 1.0), emit=(0.6, 0.85, 1.0), strength=3.0),
        chunk=mat("chunk", (0.72, 0.74, 0.78), metal=0.7, rough=0.3),
        mg=mat("mg_si", (0.30, 0.30, 0.32), rough=0.9),
        hcl=mat("hcl_gas", (0.6, 0.9, 0.6), emit=(0.6, 0.9, 0.6), strength=1.0, alpha=0.6),
        tcs=mat("tcs_liquid", (0.9, 0.85, 0.5), rough=0.2),
        bar=mat("bar_fill", (0.55, 0.58, 0.64), metal=0.5, rough=0.35),
        hi=mat("bar_high", (0.85, 0.45, 0.25), emit=(0.85, 0.45, 0.25), strength=0.4),
        dot=mat("marker", (1.0, 0.9, 0.6), emit=(1.0, 0.9, 0.6), strength=3.0),
        card=mat("card", (0.92, 0.92, 0.90), rough=0.8),
        frame=mat("frame", (0.5, 0.5, 0.55), alpha=0.1, rough=0.2),
        loop=mat("recycle_loop", (0.4, 0.9, 0.7), emit=(0.4, 0.9, 0.7), strength=1.6),
        bad=mat("bad_site", (1.0, 0.25, 0.2), emit=(1.0, 0.25, 0.2), strength=2.5),
    )


def column(name, base, radius, height, m, parent=None):
    """A solid vertical cylinder standing on `base` (poly point)."""
    return disc(name, (base[0], base[1] + height / 2, base[2]), radius, height, m, parent)


def rod_pair(root, m, x, grow_frames, half=120, grow=8.0, z=0.0):
    """A Siemens rod pair at x: two vertical rods `half` either side, joined by a U-bridge at the
    top. The rods grow in diameter (not length) by `grow` over `grow_frames` (f0, f1). Returns the
    two rod objects."""
    rods = []
    for side in (-1, 1):
        rx = x + side * half
        r = tube(f"rod_{x}_{side}", (rx, 40, z), (rx, 480, z), 20, m["rod"], root, verts=16)
        rods.append(r)
    tube(f"bridge_{x}", (x - half, 480, z), (x + half, 480, z), 14, m["graphite"], root, verts=10)
    f0, f1 = grow_frames
    for r in rods:
        # the tube's local z is its length (vertical here): scale x and y only
        key(r, f0, "scale", (1, 1, 1))
        key(r, f1, "scale", (grow, grow, 1))
    return rods


# ---- overview --------------------------------------------------------------------------


def overview():
    root = start("poly_overview", 4)
    m = poly_mats()
    xs = [-1500, -900, -300, 300, 900, 1500]
    # the stations, left to right: MG-Si bin, fluidised bed, column, bell jar, crusher, chunk bin
    box("mg_bin", (xs[0] - 150, 0, -150), (xs[0] + 150, 200, 150), m["steel"], root)
    column("bed", (xs[1], 0, 0), 180, 500, m["glass"], root)
    column("bed_base", (xs[1], 0, 0), 190, 40, m["steel"], root)
    column("column", (xs[2], 0, 0), 120, 900, m["steel"], root)
    column("jar_base", (xs[3], 0, 0), 240, 40, m["steel"], root)
    dome = ball("jar", (xs[3], 380, 0), 260, m["glass"], root)
    dome.scale = (1.0, 0.8, 1.0)
    rod_pair(root, m, xs[3], (BF, 4 * BF))
    box("crusher", (xs[4] - 150, 0, -150), (xs[4] + 150, 260, 150), m["steel"], root)
    box("chunk_bin", (xs[5] - 180, 0, -180), (xs[5] + 180, 220, 180), m["steel"], root)

    # beat 0: MG-Si goes into the bed; beat 1: vapour climbs the column; beat 2: rods grow;
    # beat 3: rods are crushed into chunks that fall into the bin
    for k in range(6):
        g = ball(f"mg{k}", (xs[0] + 150, 120, -90 + 36 * k), 40, m["mg"], root)
        travel(g, [(xs[0] + 150, 120, -90 + 36 * k), (xs[1] - 180, 180, 0)], 3 * k, 3 * k + 18, steps=2)
        show(g, [(0, BF)])
    for k in range(5):
        v = ball(f"vapour{k}", (xs[2], 120, 0), 60, m["gas"], root)
        travel(v, [(xs[2], 120, 0), (xs[2], 800, 0)], BF + 4 * k, BF + 4 * k + 30, steps=2)
        show(v, [(BF, 2 * BF)])
    for k in range(4):
        c = ball(f"chunk{k}", (xs[4] + 50, 300, -60 + 40 * k), 60, m["chunk"], root)
        travel(c, [(xs[4] + 50, 300, -60 + 40 * k), (xs[5], 260, -60 + 40 * k)], 3 * BF + 2 * k, 4 * BF - 4, steps=2)
        show(c, [(3 * BF, 4 * BF)])
    camera(root, cut=True, poses=[((-300, 250, 0), 4300, 0.3, 0.2), ((-300, 300, 0), 3800, 0.3, 0.2),
                  ((600, 300, 0), 4000, 0.3, 0.2), ((1100, 200, 0), 3800, 0.3, 0.2)])
    finish("poly_overview")


# ---- zoom a: the fluidised bed ---------------------------------------------------------


def zoom_bed():
    root = start("poly_zoom_bed", 4)
    m = poly_mats()
    column("vessel", (0, 0, 0), 300, 900, m["glass"], root)
    column("grid", (0, 0, 0), 300, 30, m["steel"], root)
    inlet = tube("gas_in", (0, -200, 0), (0, 30, 0), 35, m["steel"], root, verts=12)
    # particles lift and fall with the gas; bubbles of gas rise, more of them from beat 1
    for k, (x, z) in enumerate(ring(10, 150)):
        p = ball(f"particle{k}", (x, 80, z), 26, m["si"], root)
        for j in range(4):
            f0 = 6 * k + 24 * j
            travel(p, [(x, 80, z), (x * 0.4, 520 + 40 * (k % 3), z * 0.4), (x, 80, z)], f0, f0 + 22, steps=3)
    for k, (x, z) in enumerate(ring(6, 90)):
        # green HCl bubbles (the beat text says so); the emissive HCl material reads on the dark ground
        b = ball(f"bubble{k}", (x, 60, z), 40, m["hcl"], root)
        travel(b, [(x, 60, z), (x * 0.6, 700, z * 0.6)], BF + 6 * k, BF + 6 * k + 40, steps=2)
        show(b, [(BF, 4 * BF - 1)])
    # beat 2: the reaction products leave the top
    for k in range(3):
        out = ball(f"exit{k}", (0, 800, 0), 30, m["hcl"], root)
        travel(out, [(0, 800, 0), (200, 1000, 0)], 2 * BF + 6 * k, 3 * BF + 6 * k, steps=2)
        show(out, [(2 * BF, 4 * BF - 1)])
    camera(root, cut=True, poses=[((0, 300, 0), 2200, 0.5, 0.2), ((0, 300, 0), 2000, 0.8, 0.2),
                  ((0, 400, 0), 2200, 0.3, 0.25), ((0, 420, 0), 2400, 0.6, 0.25)])
    finish("poly_zoom_bed")


# ---- zoom b: the distillation column ---------------------------------------------------


def zoom_column():
    root = start("poly_zoom_column", 4)
    m = poly_mats()
    column("column", (0, 0, 0), 180, 1400, m["glass"], root)
    # trays across the column
    for k in range(7):
        y = 150 + k * 180
        disc(f"tray{k}", (0, y, 0), 170, 12, m["bar"], root)
    # vapour rises tray to tray; liquid drips back on the trays
    for k in range(6):
        v = ball(f"vap{k}", (-60, 80, 0), 50, m["gas"], root)
        travel(v, [(-60, 80, 0), (-60, 700, 0), (-60, 1280, 0)], k * 10, k * 10 + 60, steps=2)
        show(v, [(0, 4 * BF - 1)])
    for k in range(4):
        d = ball(f"drip{k}", (60, 1200 - k * 260, 0), 18, m["tcs"], root)
        travel(d, [(60, 1200 - k * 260, 0), (60, 1120 - k * 260, 0)], k * 24 + 6, k * 24 + 20, steps=2)
        show(d, [(0, 4 * BF - 1)])
    # beats 2-3: the TCS and STC take off at different heights, marked by bars
    grow_bar(root, "tcs_take", 250, 330, 500, m["hi"], 2 * BF, 3 * BF, z0=-40, z1=40)
    grow_bar(root, "stc_take", 350, 430, 200, m["bar"], 2 * BF, 3 * BF, z0=-40, z1=40)
    camera(root, cut=True, poses=[((0, 500, 0), 2600, 0.4, 0.2), ((0, 600, 0), 2600, 0.4, 0.2),
                  ((150, 400, 0), 2400, 0.4, 0.2), ((0, 500, 0), 2600, 0.6, 0.2)])
    finish("poly_zoom_column")


# ---- zoom c: the Siemens bell jar ------------------------------------------------------


def zoom_jar():
    root = start("poly_zoom_jar", 4)
    m = poly_mats()
    disc("base_plate", (0, 0, 0), 500, 40, m["steel"], root)
    # the bell (wall + dome) lifts off in beat 3 so the grown rods stand clear
    bell = empty("bell", root)
    column("jar_wall", (0, 40, 0), 450, 700, m["glass"], bell)
    dome = ball("jar_dome", (0, 740, 0), 450, m["glass"], bell)
    dome.scale = (1.0, 0.45, 1.0)
    key(bell, 3 * BF + 2, "location", P(0, 0, 0))
    key(bell, 3 * BF + 16, "location", P(0, 900, 0))
    # two U-rod pairs spaced so the rods stay apart as they grow from 20 mm to about 150 mm (3.75x
    # in this drawing): slim through beat 0, growing through beats 1-2, full in beat 3
    for x in (-200, 200):
        rod_pair(root, m, x, (BF, 3 * BF), half=110, grow=3.75)
    # beat 0: the current, as pulses running up one rod, over the bridge and down the other, in
    # front of the slim rods so they read; the bridges glow while it flows
    for x in (-200, 200):
        path = [(x - 110, 50, 30), (x - 110, 480, 30), (x + 110, 480, 30), (x + 110, 50, 30)]
        for k in range(3):
            p = ball(f"current_{x}_{k}", path[0], 16, m["arc"], root)
            f0 = 2 + 6 * k
            travel(p, path, f0, f0 + 14, steps=6)
            show(p, [(f0, f0 + 15)])
        glow = tube(f"bridge_glow_{x}", (x - 110, 480, 0), (x + 110, 480, 0), 17, m["hot"], root, verts=10)
        show(glow, [(0, BF)])
    # gas nozzles feed the base, gas circulates in the jar
    for k in range(8):
        g = ball(f"gas{k}", (-400, 100, -60 + 17 * k), 22, m["gas"], root)
        travel(g, [(-400, 100, -60 + 17 * k), (0, 300, 0), (400, 100, -60 + 17 * k)], 3 * k, 3 * k + 40, steps=2)
        show(g, [(BF, 3 * BF)])
    # whole jar in frame (about 0.53 x distance tall), slightly from above
    camera(root, cut=True, poses=[((0, 360, 0), 1700, 0.35, 0.22), ((0, 380, 0), 1800, 0.6, 0.25),
                  ((0, 380, 0), 1800, 0.3, 0.25), ((0, 500, 0), 2300, 0.5, 0.3)])
    finish("poly_zoom_jar")


# ---- zoom d: the recycle loop and the growth trade-off ---------------------------------


def zoom_loop():
    root = start("poly_zoom_loop", 4)
    m = poly_mats()
    # the recycle loop: a ring of pipe, with H2 and HCl pulses going round it
    loop_pts = [(math.cos(a) * 700, 200, math.sin(a) * 700) for a in
                [2 * math.pi * k / 16 for k in range(16)]]
    for k in range(16):
        a, b = loop_pts[k], loop_pts[(k + 1) % 16]
        tube(f"pipe{k}", a, b, 22, m["steel"], root, verts=8)
    for k in range(5):
        p = ball(f"recycle{k}", loop_pts[0], 40, m["loop"], root)
        travel(p, loop_pts[:9], 0, 4 * BF - 4, steps=8)
        show(p, [(0, 4 * BF - 1)])
    # the growth trade-off: rate against diameter, two bars on a scale
    grow_bar(root, "rate", -150, -50, 1.9 * 200, m["hi"], 2 * BF, 3 * BF, z0=-40, z1=40)
    grow_bar(root, "rod_mm", 50, 150, 180, m["bar"], BF, 3 * BF, z0=-40, z1=40)
    camera(root, cut=True, poses=[((0, 200, 0), 2600, 0.3, 0.6), ((0, 200, 0), 2600, 0.5, 0.6),
                  ((0, 250, 0), 2400, 0.3, 0.45), ((0, 250, 0), 2400, 0.3, 0.45)])
    finish("poly_zoom_loop")


# ---- sections --------------------------------------------------------------------------


def sec1_what_happens():
    root = start("poly_sec1", 3)
    m = poly_mats()
    xs = [-1200, -700, -200, 300, 800, 1300]
    for k, x in enumerate(xs):
        box(f"station{k}", (x - 120, 0, -180), (x + 120, 260, 180), m["steel"], root)
    box("track", (-1400, -40, -220), (1450, 0, 220), m["frame"], root)
    # MG-Si lumps move from the first station to the last, then chunks come out of the bin
    for k in range(5):
        g = ball(f"lump{k}", (xs[0], 300, -90 + 45 * k), 45, m["mg"], root)
        travel(g, [(xs[0], 300, -90 + 45 * k), (xs[1], 300, -90 + 45 * k), (xs[2], 300, -90 + 45 * k),
                   (xs[3], 300, -90 + 45 * k)], 6 * k, 6 * k + 36, steps=3)
        show(g, [(0, 2 * BF)])
    for k in range(4):
        c = ball(f"chunk{k}", (xs[4], 300, -60 + 40 * k), 60, m["chunk"], root)
        travel(c, [(xs[4], 300, -60 + 40 * k), (xs[5], 260, -60 + 40 * k)], 2 * BF + 4 * k, 3 * BF - 4, steps=2)
        show(c, [(2 * BF, 3 * BF)])
    camera(root, cut=True, poses=[((-600, 200, 0), 2600, 0.3, 0.3), ((0, 200, 0), 2600, 0.3, 0.3),
                  ((800, 220, 0), 2600, 0.3, 0.3)])
    finish("poly_sec1")


def sec2_bell_jar():
    root = start("poly_sec2", 3)
    m = poly_mats()
    disc("base_plate", (0, 0, 0), 500, 40, m["steel"], root)
    column("jar_wall", (0, 40, 0), 450, 700, m["glass"], root)
    dome = ball("jar_dome", (0, 740, 0), 450, m["glass"], root)
    dome.scale = (1.0, 0.45, 1.0)
    # two rod pairs, set back behind the glow, spaced so the grown rods stay apart
    for x in (-200, 200):
        rod_pair(root, m, x, (0, 3 * BF - 1), half=110, grow=3.75, z=-120)
    for k in range(3):
        box(f"nozzle{k}", (-300 + 300 * k, 40, -20), (-260 + 300 * k, 120, 20), m["steel"], root)
    # the hot rods glow through the growth: a small core low between the pairs
    hot = ball("hot_core", (0, 200, 60), 70, m["hot"], root)
    flicker(hot, 0, 3 * BF - 1, base=1.0)
    camera(root, cut=True, poses=[((0, 380, 0), 1800, 0.5, 0.25), ((0, 380, 0), 1800, 0.9, 0.25),
                  ((0, 380, 0), 1800, 0.2, 0.3)])
    finish("poly_sec2")


def sec3_chemistry():
    root = start("poly_sec3", 3)
    m = poly_mats()
    # SiHCl3 forms, then deposits on the rod, then the side reaction makes STC
    atoms = {"Si": (0.6, 0.62, 0.66), "H": (0.9, 0.9, 0.9), "Cl": (0.3, 0.8, 0.3)}
    radius = {"Si": 110, "H": 40, "Cl": 90}
    mats = {k: mat(f"atom_{k}", v, rough=0.4) for k, v in atoms.items()}
    steps = [
        [("Si", -700, 0), ("Cl", -600, 200), ("Cl", -500, -150), ("Cl", -820, -150), ("H", -700, 260)],
        [("Si", 0, 0), ("Cl", -100, 200), ("Cl", 100, 200), ("H", 0, -180), ("H", -80, -240)],
        [("Si", 700, 0), ("Cl", 600, 200), ("Cl", 800, -150), ("Cl", 690, -260), ("H", 700, 240)],
    ]
    for b, group in enumerate(steps):
        g = empty(f"step{b}", root)
        for k, (el, x, y) in enumerate(group):
            ball(f"atom{b}_{k}", (x, y + 200, 0), radius[el], mats[el], g)
        envelope(g, [(b * BF, b * BF + 2, (b + 1) * BF - 2, (b + 1) * BF + 4)])
    camera(root, cut=True, poses=[((-700, 200, 0), 1600, 0.2, 0.2), ((0, 200, 0), 1600, 0.2, 0.2),
                  ((700, 200, 0), 1600, 0.2, 0.2)])
    finish("poly_sec3")


def sec4_numbers():
    root = start("poly_sec4", 3)
    m = poly_mats()
    # beat 0: rod diameter 20 to 180 mm; beat 1: electricity 60-70 kWh/kg; beat 2: 9N purity
    grow_bar(root, "rod_in", -600, -400, 20, m["bar"], 0, BF)
    grow_bar(root, "rod_out", -300, -100, 180, m["hi"], 0, BF)
    grow_bar(root, "kwh", 0, 200, 65 * 3, m["bar"], BF, 2 * BF)
    grow_bar(root, "temp", 500, 700, 1100 / 10, m["hi"], 2 * BF, 3 * BF)
    camera(root, cut=True, poses=[((-300, 150, 0), 1800, 0.2, 0.2), ((0, 150, 0), 1800, 0.2, 0.2),
                  ((400, 150, 0), 1800, 0.2, 0.2)])
    finish("poly_sec4")


def sec5_impurities():
    root = start("poly_sec5", 3)
    m = poly_mats()
    # donor limits on a log scale: exponent 10 to 15 mapped to bar height
    data = [("Special EG", 12.2, m["bar"]), ("EG3", 12.7, m["bar"]), ("Solar", 14.4, m["hi"])]
    for k, (name, e, mm) in enumerate(data):
        x = -500 + k * 500
        grow_bar(root, name, x - 120, x + 120, (e - 10) * 150, mm, k * BF, k * BF + BF)
    camera(root, cut=True, poses=[((0, 200, 0), 1800, 0.2, 0.2), ((0, 200, 0), 1800, 0.2, 0.2),
                  ((0, 200, 0), 1800, 0.2, 0.2)])
    finish("poly_sec5")


def sec6_makers():
    root = start("poly_sec6", 3)
    m = poly_mats()
    data = [("Tongwei", 910), ("GCL", 480), ("Daqo", 350), ("Xinte", 300), ("Wacker", 80)]
    for k, (name, t) in enumerate(data):
        x = -800 + k * 400
        f0 = 0 if k < 2 else (BF if k < 4 else 2 * BF)
        grow_bar(root, name, x - 120, x + 120, t / 4, m["hi"] if k == 0 else m["bar"], f0, f0 + BF)
    camera(root, cut=True, poses=[((-400, 200, 0), 2200, 0.2, 0.2), ((0, 200, 0), 2200, 0.2, 0.2),
                  ((400, 200, 0), 2200, 0.2, 0.2)])
    finish("poly_sec6")


def sec7_grades():
    root = start("poly_sec7", 3)
    m = poly_mats()
    # solar volume is a large tower; chip-grade is a small, high-margin block
    solar = empty("solar", root)
    box("solar_tower", (-600, 0, -200), (-200, 900, 200), m["hi"], solar)
    chip = empty("chip", root)
    box("chip_block", (300, 0, -120), (500, 120, 120), m["bar"], chip)
    grow_bar(root, "solar_grow", -600, -200, 900, m["hi"], 0, BF, z0=-200, z1=200)
    envelope(chip, [(BF, BF + 2, 3 * BF - 2, 3 * BF + 4)])
    camera(root, cut=True, poses=[((-200, 300, 0), 2600, 0.3, 0.2), ((-200, 300, 0), 2600, 0.3, 0.2),
                  ((400, 150, 0), 2000, 0.3, 0.2)])
    finish("poly_sec7")


def sec8_risks():
    root = start("poly_sec8", 3)
    m = poly_mats()
    # a valve on the chunk line; overcapacity stacks up in the bins; power is a meter
    box("line", (-1000, 100, -80), (1000, 160, 80), m["steel"], root)
    valve = empty("valve", root)
    box("valve_gate", (-30, 60, -160), (30, 200, 160), m["bad"], valve)
    show(valve, [(BF, 3 * BF)])
    for k in range(4):
        g = ball(f"chunk{k}", (-800, 200, 0), 60, m["chunk"], root)
        travel(g, [(-800, 200, 0), (-80, 200, 0)], 6 * k, 6 * k + 30, steps=2)
        show(g, [(0, BF)])
    grow_bar(root, "glut", 400, 600, 800, m["hi"], 2 * BF, 3 * BF, z0=-120, z1=120)
    grow_bar(root, "power", -600, -400, 65 * 3, m["bar"], 0, 2 * BF, z0=-120, z1=120)
    camera(root, cut=True, poses=[((-300, 200, 0), 2600, 0.3, 0.25), ((0, 300, 0), 2600, 0.3, 0.25),
                  ((300, 300, 0), 2600, 0.3, 0.25)])
    finish("poly_sec8")


def sec9_names():
    root = start("poly_sec9", 3)
    m = poly_mats()
    names = ["Tongwei", "GCL", "Daqo", "Xinte", "Wacker", "OCI", "Tokuyama", "Hemlock", "REC"]
    for k in range(9):
        x = -800 + (k % 3) * 800
        z = -300 + (k // 3) * 300
        tile = empty(f"name{k}", root)
        box(f"tile{k}", (x - 200, 0, z - 100), (x + 200, 30, z + 100), m["card"], tile)
        beat = k // 3
        envelope(tile, [(beat * BF, beat * BF + 2, 3 * BF - 2, 3 * BF + 4)])
    camera(root, cut=True, poses=[((0, 60, 0), 2400, 0.3, 0.7), ((0, 60, 0), 2400, 0.3, 0.7),
                  ((0, 60, 0), 2400, 0.3, 0.7)])
    finish("poly_sec9")


def sec10_sources():
    root = start("poly_sec10", 3)
    m = poly_mats()
    cards = empty("cards", root)
    for k in range(4):
        y0 = 4 + k * 8
        card = empty(f"card{k}_grp", cards)
        box(f"card{k}", (-250, y0, -175), (250, y0 + 5, 175), m["card"], card)
        beat = 0 if k < 2 else 1
        start_x = -1200 if k % 2 == 0 else 1200
        angle = 0.9 if k % 2 == 0 else -0.9
        f0 = beat * BF + 4 * (k % 2)
        f1 = f0 + BF - 6
        key(card, f0, "location", P(start_x, 0, 0))
        key(card, f0, "rotation_euler", (0, 0, angle))
        key(card, f1, "location", P(0, 0, 0))
        key(card, f1, "rotation_euler", (0, 0, 0))
    key(cards, 2 * BF, "rotation_euler", (0, 0, 0))
    key(cards, 2 * BF + 12, "rotation_euler", (0, 0, 0.12))
    key(cards, 3 * BF - 1, "rotation_euler", (0, 0, -0.12))
    camera(root, cut=True, poses=[((0, 60, 0), 1800, 0.6, 0.7), ((0, 80, 0), 1800, 0.9, 0.7),
                  ((0, 80, 0), 1800, 0.3, 0.8)])
    finish("poly_sec10")


SCENES = {"bed": zoom_bed, "column": zoom_column, "jar": zoom_jar, "loop": zoom_loop}


def build_all():
    # overview() is the old stand-in: poly_overview.py now writes poly_overview.glb, so a full run
    # here must not overwrite it
    zoom_bed()
    zoom_column()
    zoom_jar()
    zoom_loop()
    sec1_what_happens()
    sec2_bell_jar()
    sec3_chemistry()
    sec4_numbers()
    sec5_impurities()
    sec6_makers()
    sec7_grades()
    sec8_risks()
    sec9_names()
    sec10_sources()


if __name__ == "__main__":
    # `-- jar sec2` builds only those scenes (zoom names, or secN); no args builds all but overview
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not which:
        build_all()
    for name in which:
        if name in SCENES:
            SCENES[name]()
        else:
            n = int(name.removeprefix("sec"))
            [sec1_what_happens, sec2_bell_jar, sec3_chemistry, sec4_numbers, sec5_impurities,
             sec6_makers, sec7_grades, sec8_risks, sec9_names, sec10_sources][n - 1]()
