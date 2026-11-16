"""The ten SLICE + POLISH write-up sections, authored in Blender and exported for pbr3d in the SAND
template (docs/diagram-pages.md). The pieces are in slice_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/slice_sections.py [-- 3 5]

For each section it writes blender/slice_sec<N>.blend and assets/slice_sec<N>.glb.

  1  what happens   seven stations along the line; the wafer rides from one to the next (four beats)
  2  inside a saw   the web; the ingot fed down; coolant and swarf; a close look at one cut (four)
  3  mechanics      slicing grit, lapping, grinding, etching, polishing (five)
  4  numbers        two saw kerfs, the path to 85 um, the lapping stock and time, the end thickness (four)
  5  budget         four removal bars to scale, 1 mm per um (four)
  6  shares         CMP tools, the 2001/2002 split, slurry, pads (four)
  7  chokepoints    wire wear, thin wire, consumables by line, the two-supplier tool market (four)
  8  downstream     the flat reference, a film planarised, the same law at both ends (three)
  9  caveats        patent examples, dated shares, solar kerf numbers (three)
  10 sources        eight source cards lighting up in three groups (three)

One beat is SEC (8) seconds at 24 fps. Bars in sections 5 and 6 are drawn to a fixed scale that the
text names on the page.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, beat, box, cut, disc, empty, key, label, pivot, rel, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
import slice_kit as K  # noqa: E402
from slice_kit import END, KERF_T, PITCH, STATION_X, TRACK_Y, WAFER_R, WAFER_T  # noqa: E402

X = STATION_X
WEB_YS = [TRACK_Y + WAFER_T + KERF_T / 2 + k * PITCH for k in range(6)]


def begin(n, beats):
    m, root = start(f"sec{n}", beats, page="slice")
    K.mats(m)
    return m, root


def grow_bar(g, name, x, z, w, h, m, f0, f1, depth=None):
    """A vertical bar standing on y=0 at (x, z) that grows to height h over [f0, f1]."""
    d = depth or w
    b = pivot(name, (x, 0, z), g)
    box(f"{name}_box", (-w / 2, 0, -d / 2), (w / 2, h, d / 2), m[name_mat(name, m)], b)
    scale_keys(b, [(0, (OFF,) * 3), (f0, (1, 1, OFF)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    return b


def name_mat(name, m):
    return "gold" if name.startswith("gold") else ("blue" if name.startswith("blue") else "grey")


def grow_hbar(g, name, x, y, z, length, thick, mm, f0, f1):
    """A horizontal bar from (x, y, z) to the right that grows to `length` over [f0, f1]."""
    b = pivot(name, (x, y, z), g)
    box(f"{name}_box", (0, -thick / 2, -thick / 2), (length, thick / 2, thick / 2), mm, b)
    scale_keys(b, [(0, (OFF,) * 3), (f0, (OFF, 1, 1)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    return b


def plinth(g, m, x0, x1, z0=-600, z1=600, y=0.0):
    box("plinth", (x0, y - 80, z0), (x1, y, z1), m["plinth"], g)


def cards(root, m, specs, z_rows=(-800, 800)):
    """Paper cards in a grid; specs = [(label text, beat, lit-from u)], lit with a gold strip."""
    for n, (text, b, u) in enumerate(specs):
        x = -3900 + 2600 * (n % 4)  # wide spacing: the long tags run about 2100 mm
        z = z_rows[0] if n < 4 else z_rows[1]
        box(f"card{n}", (x - 700, 0, z - 500), (x + 700, 30, z + 500), m["paper"], root)
        lit = empty(f"lit{n}", root)
        box(f"lit{n}_m", (x - 600, 30, z - 380), (x + 300, 36, z - 340), m["gold_glow"], lit)
        show(lit, [(F(b, u), END)])
        label(text, (x - 700, 40, z + 500), root, [(F(b, u), END)])


def sec1():
    m, root = begin(1, 4)
    K.floor(root, m, x0=-600, x1=6600)
    names = ["INGOT", "SLICE", "GRIND/LAP", "ETCH", "EDGE", "POLISH", "CLEAN"]
    for i, x in enumerate(X):
        h = 260 + 60 * (i % 2)
        # behind the track (z < -170): a box over the track hid the wafer at every station
        box(f"st{i}", (x - 260, TRACK_Y, -440), (x + 260, TRACK_Y + h, -180), m["dark_steel"], root)
    stops = [(0, X[0]), (F(0, 0.8), X[1]), (F(1, 0.0), X[1]), (F(1, 0.8), X[3]),
             (F(2, 0.0), X[3]), (F(2, 0.8), X[5]), (F(3, 0.0), X[5]), (F(3, 0.8), X[6]), (END, X[6])]
    carrier = K.Carrier(root, m, stops)
    carrier.disc("wafer", "silicon")
    tags = [
        (0, [0, 1], "INGOT, then SLICE: the wire saw"),
        (1, [2, 3], "GRIND/LAP and ETCH remove the saw damage"),
        (2, [4, 5], "EDGE rounds the rim, POLISH makes the face"),
        (3, [6], "CLEAN, inspect, ship"),
    ]
    for b, idxs, text in tags:
        label(text, (X[idxs[0]] + 200, 600, 0), root, beat(b))
    camera(root, [((500.0, 250.0, 0.0), 3000.0, 0.10, 0.28), ((2500.0, 250.0, 0.0), 3000.0, 0.10, 0.28),
                  ((4500.0, 250.0, 0.0), 3000.0, 0.10, 0.28), ((6000.0, 250.0, 0.0), 3000.0, 0.10, 0.28)])
    finish("sec1", page="slice")


def sec2():
    m, root = begin(2, 4)
    K.wire_web(root, m, 0.0, WEB_YS, half=420.0)
    ing = empty("ingot_feed", root)
    key(ing, 0, "location", P(0, 420, 0))
    key(ing, F(1, 0.0), "location", P(0, 420, 0))
    key(ing, F(1, 0.6), "location", P(0, 0, 0))
    key(ing, END, "location", P(0, 0, 0))
    height = 6 * PITCH + WAFER_T
    cut(disc("ingot", (0, TRACK_Y + height / 2, 0), WAFER_R, height, m["ingot"], ing, verts=72), z=-12.0)
    show(ing, [(0, F(2, 0.0))])
    slices = empty("slices", root)
    for k in range(7):
        K.slab(slices, f"slice{k}", 0.0, TRACK_Y + k * PITCH, 0, WAFER_R, WAFER_T, m["silicon"])
    show(slices, [(F(2, 0.0), END)])
    K.spray_nozzles(root, m, 0.0, 720.0, [(F(2, 0.1), F(2, 0.9)), (F(2, 0.3), F(2, 0.95))], n=16)
    chips = [K.chip_drops(root, m, 0.0, WEB_YS[k], F(2, 0.4 + 0.05 * k), F(3, 0.0), n=6) for k in range(3)]
    label("wire web: one pass per slot", (420, WEB_YS[4], 160), root, [(0, F(1, 0.0))])
    label("ingot fed down into the web", (320, 520, 0), root, [(F(1, 0.1), F(2, 0.0))])
    label("coolant washes out the swarf", (300, 600, 0), root, [(F(2, 0.2), END)])
    # the close look: one wire and its slot
    # on the wire just past the slice edge (x > 150), not inside the slot where the slices hide it
    grit = K.grit_points(root, m, 255.0, WEB_YS[2], 0.0, F(3, 0.0), END, n=7)
    label("grit tips chip the silicon", (240, WEB_YS[2] + 14, 10), root, [(F(3, 0.1), END)])
    label("kerf: wire plus diamond layer", (175, WEB_YS[2] + 30, 0), root, [(F(3, 0.3), END)])
    camera(root, [
        ((0.0, 350.0, 0.0), 2600.0, 0.22, 0.12),
        ((0.0, 350.0, 0.0), 2600.0, 0.22, 0.12),
        ((0.0, 420.0, 0.0), 2000.0, 0.20, 0.10),
        ((240.0, WEB_YS[2], 0.0), 420.0, 0.25, 0.10),
    ])
    finish("sec2", page="slice")


def bgroup(root, name, b):
    """A group that is on only during beat b, so each beat's machine is seen alone."""
    g = empty(name, root)
    show(g, beat(b))
    return g


def sec3():
    m, root = begin(3, 5)
    # 0 slicing: fixed diamond grit on a wire, chips leaving the silicon
    g = bgroup(root, "m_slice", 0)
    tube("slice_wire", (-300, 200, 0), (300, 200, 0), 5.0, m["wire"], g, verts=6)
    box("slice_block", (-260, TRACK_Y, -120), (260, 150, 120), m["silicon"], g)
    K.grit_points(g, m, 0.0, 200.0, 0.0, 0, F(1, 0.0), n=8)
    K.chip_drops(g, m, 0.0, 150.0, F(0, 0.3), F(1, 0.0), n=8)
    label("fixed diamond grit cuts by fracture", (260, 260, 0), root, beat(0))
    # 1 lapping: loose slurry between two plates
    g = bgroup(root, "m_lap", 1)
    disc("lap_lower", (0, TRACK_Y / 2, 0), 260.0, TRACK_Y, m["plate"], g, verts=72)
    K.slab(g, "lap_wafer", 0.0, TRACK_Y, 0.0, WAFER_R, WAFER_T, m["silicon"])
    upper = pivot("lap_upper", (0, 0, 0), g)
    cut(disc("lap_upper_m", (0, 0, 0), 260.0, 60.0, m["plate"], upper, verts=72), z=-40.0)
    key(upper, F(1, 0.0), "location", P(0, 187.5, 0), linear=True)
    key(upper, F(1, 0.8), "location", P(0, 140.5, 0), linear=True)
    key(upper, END, "location", P(0, 140.5, 0), linear=True)
    grains = empty("slurry", g)
    for k in range(14):
        a = 2.0 * math.pi * k / 14
        ball(f"g{k}", (170 * math.cos(a), 150, 170 * math.sin(a)), 5.0, m["slurry"], grains, 6)
    label("two plates, slurry: flat and parallel", (300, 260, 0), root, beat(1))
    # 2 grinding: a resin-bond wheel turning over the wafer
    g = bgroup(root, "m_grind", 2)
    K.slab(g, "grind_wafer", 0.0, TRACK_Y, 0.0, WAFER_R, WAFER_T, m["silicon"])
    wheel = empty("grind_wheel", g)
    key(wheel, F(2, 0.0), "location", P(0, 260, 0), linear=True)
    key(wheel, F(2, 0.7), "location", P(0, 200, 0), linear=True)
    key(wheel, END, "location", P(0, 200, 0), linear=True)
    disc("wheel_m", (0, 0, 0), 240.0, 40.0, m["resin"], wheel, verts=72)
    K.spin(wheel, F(2, 0.0), END, turns=2.0, axis=2)
    label("resin wheel: 10-20 um off one side", (300, 300, 0), root, beat(2))
    # 3 etching: the bath, the damage layer goes
    g = bgroup(root, "m_etch", 3)
    liquid = K.bath(g, m, 0.0, w=340.0, depth=160.0, z=220.0)
    scale_keys(liquid, [(0, (1, 1, 0.0001)), (F(3, 0.0), (1, 1, 0.0001)), (F(3, 0.3), (1, 1, 1)), (END, (1, 1, 1))])
    K.slab(g, "etch_wafer", 0.0, TRACK_Y, 0.0, WAFER_R, WAFER_T, m["silicon"])
    for nm, yy in (("etch_dtop", TRACK_Y + WAFER_T - 1.5), ("etch_dbot", TRACK_Y + 1.5)):
        d = disc(nm, (0, yy, 0), WAFER_R + 1, 3.0, m["damage"], g)
        show(d, [(F(3, 0.0), F(3, 0.6))])
    label("wet bath strips the damage layer", (330, 240, 0), root, beat(3))
    # 4 polishing: the pad, and the softened band wiped off
    g = bgroup(root, "m_pol", 4)
    K.slab(g, "pol_wafer", 0.0, TRACK_Y, 0.0, WAFER_R, WAFER_T, m["silicon"])
    band = K.pbox("pol_band", (-150, TRACK_Y + WAFER_T - 1, -150), (150, TRACK_Y + WAFER_T + 2, 150), m["film"], g,
                  at=(150, TRACK_Y + WAFER_T, 0))
    scale_keys(band, [(0, (1, 1, 1)), (F(4, 0.2), (1, 1, 1)), (F(4, 0.85), (0.0001, 1, 1)), (END, (0.0001, 1, 1))], until=F(4, 0.2))
    pad = empty("pol_pad", g)
    key(pad, 0, "location", P(0, 200, 0))
    key(pad, F(4, 0.4), "location", P(0, 160, 0), linear=True)
    key(pad, END, "location", P(0, 160, 0), linear=True)
    cut(disc("pol_pad_m", (0, 0, 0), 230.0, 30.0, m["pad"], pad, verts=72), z=-40.0)
    label("pad and slurry: chemistry softens, abrasive wipes", (330, 260, 0), root, beat(4))
    camera(root, [
        ((0.0, 200.0, 0.0), 1500.0, 0.25, 0.14),
        ((0.0, 200.0, 0.0), 1500.0, 0.25, 0.14),
        ((0.0, 200.0, 0.0), 1500.0, 0.25, 0.14),
        ((0.0, 200.0, 0.0), 1500.0, 0.25, 0.14),
        ((0.0, 200.0, 0.0), 1500.0, 0.25, 0.14),
    ])
    finish("sec3", page="slice")


def sec4():
    m, root = begin(4, 4)
    # 0: two kerfs side by side (150 um slurry, 125 um diamond), each as three cut slices
    g = bgroup(root, "k0", 0)
    for nm, x, kerf in (("slurry", -450.0, 15.0), ("diamond", 350.0, KERF_T)):
        sub = empty(f"kerf_{nm}", g)
        for k in range(3):
            K.slab(sub, f"{nm}_s{k}", x, TRACK_Y + k * (WAFER_T + kerf), 0, WAFER_R, WAFER_T, m["silicon"])
    label("slurry saw: about 150 um", (-450, 380, 180), root, beat(0))
    label("diamond wire: about 125 um", (350, 380, 180), root, beat(0))
    # 1: the path to about 85 um, a third stack with the narrower slot
    g = bgroup(root, "k1", 1)
    for k in range(3):
        K.slab(g, f"path_s{k}", 350.0, TRACK_Y + k * (WAFER_T + 8.5), 0, WAFER_R, WAFER_T, m["silicon"])
    label("path to about 85 um", (350, 380, 180), root, beat(1))
    label("fine wire under 35 um: research", (-450, 380, 180), root, beat(1))
    # 2: lapping stock 80 um (8 mm) and its time, 40 minutes
    g = bgroup(root, "k2", 2)
    K.slab(g, "lap_w", -300.0, TRACK_Y, 0, WAFER_R, WAFER_T, m["silicon"])
    box("lap_stock", (-300 - WAFER_R - 30, TRACK_Y + WAFER_T - 8, -160), (-300 - WAFER_R - 10, TRACK_Y + WAFER_T, 160), m["red"], g)
    grow_hbar(g, "time40", -300.0 - WAFER_R, 0.0, -200.0, 340.0, 20.0, m["gold"], F(2, 0.1), F(2, 0.8))
    label("80 um, 40 min: 200-300 mm example", (-300, 330, 180), root, beat(2))
    label("80 to 200 um in total", (300, 220, 0), root, beat(2))
    # 3: the end result: 775 um with a 25 um tolerance either side
    g = bgroup(root, "k3", 3)
    K.slab(g, "end_w", 0.0, TRACK_Y, 0.0, WAFER_R, WAFER_T, m["silicon"])
    for nm, yy in (("tol_top", TRACK_Y + WAFER_T + 2.5), ("tol_bot", TRACK_Y - 2.5)):
        box(nm, (-200, yy - 1, -170), (200, yy + 1, 170), m["gold"], g)
    label("775 um +/- 25 um", (210, 200, 0), root, beat(3))
    label("TTV 5 um or less", (210, 140, 0), root, beat(3))
    camera(root, [
        ((-50.0, 230.0, 0.0), 2400.0, 0.12, 0.14),
        ((350.0, 230.0, 0.0), 1900.0, 0.12, 0.14),
        ((-300.0, 230.0, 0.0), 1900.0, 0.12, 0.14),
        ((0.0, 230.0, 0.0), 1900.0, 0.12, 0.14),
    ])
    finish("sec4", page="slice")


def sec5():
    m, root = begin(5, 4)
    g = empty("budget", root)
    plinth(g, m, -40, 260, -400, 400, y=-60)
    rows = [
        ("saw kerf 125 um", 125.0, 600, m["grey"], 0, 0.1, 0.6),
        ("lapping 80 um (80-200)", 80.0, 450, m["blue"], 1, 0.1, 0.5),
        ("etch 20 um (15-25)", 20.0, 300, m["gold"], 2, 0.1, 0.5),
        ("DSP polish 15 um (10-20)", 15.0, 150, m["gold"], 3, 0.1, 0.5),
    ]
    box("zero_line", (-3, -60, -60), (0, 680, 60), m["steel"], g)
    for k, (text, um, y, mm, b, u0, u1) in enumerate(rows):
        grow_hbar(g, f"bar{k}", 0, y, 0, um * 4.0, 70.0, mm, F(b, u0), F(b, u1))
        label(text, (um * 4.0 + 20, y + 50, 0), g, [(F(b, u1 - 0.05), END)])
    camera(root, [((300.0, 380.0, 0.0), 1500.0, 0.10, 0.12)] * 4)
    finish("sec5", page="slice")


def sec6():
    m, root = begin(6, 4)
    plinth(root, m, -300, 1400, -400, 400)
    # 0: AMAT and Ebara together about 80 percent (market-research claim)
    g = bgroup(root, "s0", 0)
    grow_bar(g, "gold_tools", 0, 0, 220, 80 * 2.0, m, F(0, 0.1), F(0, 0.7))
    label("AMAT + Ebara: about 80% (rough claim)", (-170, 200, 0), root, beat(0))
    # 1: Dataquest 2001 and 2002, Applied and Ebara
    g = bgroup(root, "s1", 1)
    for k, (x, h, txt) in enumerate([(0, 62.1, "Applied 2001 62.1%"), (330, 23.0, "Ebara 2001 23%"),
                                      (660, 61.3, "Applied 2002 61.3%"), (990, 22.0, "Ebara 2002 22%")]):
        grow_bar(g, f"ded{k}", x, 0, 220, h * 2.0, m, F(1, 0.1 + 0.1 * k), F(1, 0.5 + 0.1 * k))
        label(txt, (x - 80, h * 2.0 + 60, 0), root, [(F(1, 0.55), F(2, 0.0))])
    # 2: slurry: Fujifilm about 31 percent, top six over 70 percent
    g = bgroup(root, "s2", 2)
    grow_bar(g, "gold_fuji", 0, 0, 220, 31 * 2.0, m, F(2, 0.1), F(2, 0.5))
    grow_bar(g, "blue_top6", 330, 0, 220, 70 * 2.0, m, F(2, 0.2), F(2, 0.6))
    label("Fujifilm (4901.T): about 31%", (-170, 150, 0), root, beat(2))
    label("top six slurry: over 70% (summary)", (150, 200, 0), root, beat(2))
    # 3: pads: DuPont over 50 percent, a rough number
    g = bgroup(root, "s3", 3)
    grow_bar(g, "gold_pad", 0, 0, 220, 50 * 2.0, m, F(3, 0.1), F(3, 0.5))
    label("DuPont (DD): over 50% of pads (undated)", (-170, 160, 0), root, beat(3))
    camera(root, [((60.0, 120.0, 0.0), 1500.0, 0.10, 0.15), ((500.0, 120.0, 0.0), 2200.0, 0.10, 0.15),
                  ((200.0, 120.0, 0.0), 1600.0, 0.10, 0.15), ((60.0, 120.0, 0.0), 1500.0, 0.10, 0.15)])
    finish("sec6", page="slice")


def sec7():
    m, root = begin(7, 4)
    # 0: a worn wire bows under the load, against a new one
    y = WEB_YS[2]
    dz = 34.0
    g = bgroup(root, "c0", 0)
    tube("wire_new", (-420, y, 0), (420, y, 0), 5.0, m["wire"], g, verts=6)
    worn = empty("worn", g)
    tube("worn_a", (-420, y, 0), (0, y - dz, 0), 5.0, m["wire"], worn, verts=6)
    tube("worn_b", (0, y - dz, 0), (420, y, 0), 5.0, m["wire"], worn, verts=6)
    label("worn wire deflects more: TTV and kerf rise", (300, y - dz - 60, 0), root, beat(0))
    # 1: thick wire holds, thin wire is weaker and can break
    g = bgroup(root, "c1", 1)
    tube("thick_wire", (-300, 300, 0), (300, 300, 0), 9.0, m["wire"], g, verts=8)
    tube("thin_a", (-300, 120, 0), (-40, 120, 0), 2.5, m["wire"], g, verts=6)
    tube("thin_b", (40, 120, 0), (300, 120, 0), 2.5, m["wire"], g, verts=6)
    label("thick wire: more kerf, holds", (320, 330, 0), root, beat(1))
    label("thin wire: less kerf, can break", (320, 110, 0), root, beat(1))
    # 2: consumables bought forever: drums of slurry and pads, qualified per line
    g = bgroup(root, "c2", 2)
    for k in range(4):
        disc(f"drum{k}", (-500 + 330 * k, 0, 0), 120.0, 260.0, m["blue"] if k % 2 else m["grey"], g, verts=48)
    label("slurry and pads: a few vendors", (-300, 330, 0), root, beat(2))
    label("qualified per fab line: slow to switch", (-300, 380, 0), root, [(F(2, 0.5), F(3, 0.0))])
    # 3: tool market: two big suppliers, a challenger at the edge
    g = bgroup(root, "c3", 3)
    box("tool_a", (-300, 0, -200), (-60, 380, 200), m["gold"], g)
    box("tool_b", (120, 0, -200), (360, 300, 200), m["blue"], g)
    box("tool_c", (520, 0, -200), (640, 110, 200), m["red"], g)
    label("Applied and Ebara: two suppliers", (-300, 420, 0), root, beat(3))
    label("Chinese toolmakers pushing in", (460, 180, 0), root, [(F(3, 0.1), END)])
    camera(root, [((150.0, y - 30, 0.0), 1500.0, 0.08, 0.12), ((50.0, 210.0, 0.0), 1600.0, 0.08, 0.12),
                  ((0.0, 180.0, 0.0), 2600.0, 0.08, 0.12), ((180.0, 200.0, 0.0), 2600.0, 0.08, 0.12)])
    finish("sec7", page="slice")


def sec8():
    m, root = begin(8, 3)
    # 0: a mirror wafer is the flat reference under the lithography stepper
    g = bgroup(root, "d0", 0)
    K.slab(g, "ref_w", 0.0, TRACK_Y, 0.0, WAFER_R, WAFER_T, m["mirror"])
    box("litho_beam", (-400, 420, -20), (400, 440, 20), m["steel"], g)
    label("polished face: the flat reference for lithography", (260, 330, 0), root, beat(0))
    # 1: a film with a bump on the wafer, planarised by a pad
    g = bgroup(root, "d1", 1)
    box("film_base", (-260, TRACK_Y, -200), (260, TRACK_Y + 60, 200), m["silicon"], g)
    bump = K.pbox("film_bump", (-40, TRACK_Y + 60, -120), (40, TRACK_Y + 180, 120), m["film"], g, at=(0, TRACK_Y + 60, 0))
    scale_keys(bump, [(0, (1, 1, 1)), (F(1, 0.1), (1, 1, 1)), (F(1, 0.8), (1, 1, 0.4)), (END, (1, 1, 0.4))], until=F(1, 0.1))
    pad = empty("fl_pad", g)
    key(pad, 0, "location", P(0, 330, 0))
    key(pad, F(1, 0.2), "location", P(0, 330, 0), linear=True)
    key(pad, F(1, 0.9), "location", P(0, 260, 0), linear=True)
    key(pad, END, "location", P(0, 260, 0), linear=True)
    cut(disc("fl_pad_m", (0, 0, 0), 230.0, 30.0, m["pad"], pad, verts=72), z=-40.0)  # the bump shows
    label("films: STI, copper, tungsten", (260, 260, 0), root, beat(1))
    # 2: the same law at both ends: wafer polish and fab CMP
    g = bgroup(root, "d2", 2)
    K.slab(g, "left_w", -500.0, TRACK_Y, 0.0, 150.0, WAFER_T, m["mirror"])
    K.slab(g, "right_w", 500.0, TRACK_Y, 0.0, 150.0, 40.0, m["film"])
    label("wafer maker: bare silicon", (-500, 300, 0), root, beat(2))
    label("fab CMP: deposited films, RR = K*P + C", (500, 300, 0), root, beat(2))
    camera(root, [
        ((0.0, 200.0, 0.0), 1500.0, 0.10, 0.14),
        ((0.0, 200.0, 0.0), 1700.0, 0.10, 0.14),
        ((0.0, 160.0, 0.0), 2700.0, 0.06, 0.14),
    ])
    finish("sec8", page="slice")


def sec9():
    m, root = begin(9, 3)
    plinth(root, m, -4400, 4400, -1700, 1700)
    cards(root, m, [
        ("removal amounts: patent examples, not a standard", 0, 0.2),
        ("market shares: old or market-research, verify", 1, 0.2),
        ("kerf: solar-grade roadmap numbers", 2, 0.2),
    ])
    camera(root, [((-1800.0, 0.0, -800.0), 20000.0, 0.06, 0.85)] * 3)  # the labels run to about x -5000 and +3300
    finish("sec9", page="slice")


def sec10():
    m, root = begin(10, 3)
    plinth(root, m, -4400, 4400, -1700, 1700)
    srcs = [
        ("[1] TaiyangNews, diamond wire", 0), ("[2] Ge et al., fine wire", 0), ("[3] Springer 2026, wear and kerf", 0),
        ("[4] Lapping, etch, polish patents", 1), ("[5] Preston law and pH (patent, doi)", 1),
        ("[6] Slurry and tool shares, semiconductor-digest", 2),
        ("[7] CMP competition, Applied FY2025 10-K", 2), ("[8] CMP equipment share, Dataquest", 2),
    ]
    specs, seen = [], {}
    for t, b in srcs:
        j = seen.get(b, 0)
        seen[b] = j + 1
        specs.append((t, b, 0.15 + 0.3 * j))
    cards(root, m, specs)
    camera(root, [((900.0, 0.0, 0.0), 24000.0, 0.06, 0.85)] * 3)  # the right-hand column's tags reach x 6000
    finish("sec10", page="slice")


BUILDERS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9, 10: sec10}

if __name__ == "__main__":
    which = [int(a) for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(BUILDERS)
    for n in which:
        BUILDERS[n]()
