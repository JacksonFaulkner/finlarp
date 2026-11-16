"""The four SLICE + POLISH zoom-ins, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md), built from the pieces in slice_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/slice_zooms.py [-- web lap preston budget]

For each zoom it writes blender/slice_zoom_<name>.blend and assets/slice_zoom_<name>.glb.

  web      the wire web: the ingot fed down through it, slices one kerf apart, a worn wire bowing
           under the load, and the last wafers still attached like teeth
  lap      two plates and slurry: the upper plate presses, the wafers come out flat but cracked
           under the surface, and the plate lifts away
  preston  a pad on the wafer, a softened band wiped off under pressure, the pH scale with its two
           markers, and pits at pH 13
  budget   the thickness budget as slabs peeled off a wafer: kerf, lapping, etch, polish

One beat is SEC (8) seconds at 24 fps; every zoom is four beats. The budget draws 1 um as 0.1 mm,
as the other scenes do.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, box, cut, disc, empty, key, label, pivot, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
import slice_kit as K  # noqa: E402
from slice_kit import END, KERF_T, PITCH, TRACK_Y, WAFER_R, WAFER_T  # noqa: E402

BEATS = 4


def begin(name):
    m, root = start(name, BEATS, page="slice")
    K.mats(m)
    return m, root


# ---- a: the wire web ---------------------------------------------------------------------

WEB_YS = [TRACK_Y + WAFER_T + KERF_T / 2 + k * PITCH for k in range(6)]


def web():
    m, root = begin("web")
    K.wire_web(root, m, 0.0, WEB_YS, half=420.0)
    straight = [c for c in root.children if c.name.startswith("wire") and c.name[4:].isdigit()]
    # the ingot comes down through the web in beat 0, then it is cut in place
    ing = empty("ingot_feed", root)
    key(ing, 0, "location", P(0, 420, 0))
    key(ing, F(0, 0.75), "location", P(0, 0, 0))
    key(ing, END, "location", P(0, 0, 0))
    height = 6 * PITCH + WAFER_T
    cut(disc("ingot", (0, TRACK_Y + height / 2, 0), WAFER_R, height, m["ingot"], ing, verts=72), z=-12.0)
    show(ing, [(0, F(1, 0.0))])
    # the slices, with a kerf gap where each wire passes
    slices = empty("slices", root)
    for k in range(7):
        K.slab(slices, f"slice{k}", 0.0, TRACK_Y + k * PITCH, 0, WAFER_R, WAFER_T, m["silicon"])
    show(slices, [(F(1, 0.0), END)])
    # beat 2: the worn wire bows under the load, deepest at the middle
    worn = empty("worn_wire", root)
    y = WEB_YS[2]
    dz = 34.0
    tube("worn_a", (-420, y, 0), (0, y - dz, 0), 5.0, m["wire"], worn, verts=6)
    tube("worn_b", (0, y - dz, 0), (420, y, 0), 5.0, m["wire"], worn, verts=6)
    show(worn, [(F(2, 0.0), F(3, 0.0))])
    for c in straight:
        if c.name == "wire2":
            show(c, [(0, F(2, 0.0)), (F(3, 0.0), END)])
    box("dzmax_bar", (-400, y - dz, -26), (-392, y, -22), m["red"], root)
    # beat 3: the last wafers are still held by an uncut base
    base = K.pbox("uncut_base", (-150, 0, -150), (150, TRACK_Y, 150), m["ingot"], root)
    show(base, [(F(3, 0.0), END)])

    label("ingot fed down through the wire web", (300, 520, 0), root, [(F(0, 0.1), F(1, 0.0))])
    label("kerf about 125 um per slot", (300, TRACK_Y + WAFER_T + KERF_T / 2, 160), root, [(F(1, 0.1), END)])
    label("one wire pass cuts one slot", (300, 360, 160), root, [(F(1, 0.1), F(2, 0.0))])
    label("worn wire: deeper bow (dzmax)", (300, WEB_YS[2] - dz, 160), root, [(F(2, 0.1), F(3, 0.0))])
    label("last wafers still attached", (210, TRACK_Y + 40, 180), root, [(F(3, 0.1), END)])
    camera(root, [((0.0, 360.0, 0.0), 2400.0, 0.20, 0.10)] * BEATS)
    finish("zoom_web", page="slice")


# ---- b: lapping -----------------------------------------------------------------------------


def lap():
    m, root = begin("lap")
    carrier = K.Carrier(root, m, [(0, 0.0)])
    rough = carrier.disc("wafer", "silicon")
    scale_keys(carrier.pv, [(0, (1, 1, 1)), (F(1, 0.25), (1, 1, 1)), (F(2, 0.8), (1, 1, 0.897)), (END, (1, 1, 0.897))])
    dtop = disc("damage_top", (0, WAFER_T - 1.0, 0), WAFER_R + 1, 3.0, m["damage"], carrier.pv)
    dbot = disc("damage_bot", (0, 1.5, 0), WAFER_R + 1, 3.0, m["damage"], carrier.pv)
    show(dtop, [(F(2, 0.1), END)])
    show(dbot, [(F(2, 0.1), END)])
    disc("plate_lower", (0, TRACK_Y / 2, 0), 260.0, TRACK_Y, m["plate"], root, verts=72)
    upper = pivot("plate_upper", (0, 0, 0), root)
    # front half cut away, so the gap, the slurry and the wafer's top face show under it
    cut(disc("plate_upper_m", (0, 0, 0), 260.0, 60.0, m["plate"], upper, verts=72), z=-40.0)
    key(upper, 0, "location", P(0, 187.5, 0), linear=True)
    key(upper, F(1, 0.05), "location", P(0, 187.5, 0), linear=True)
    key(upper, F(2, 0.7), "location", P(0, 140.5, 0), linear=True)
    key(upper, F(3, 0.1), "location", P(0, 140.5, 0), linear=True)
    key(upper, F(3, 0.6), "location", P(0, 300.0, 0), linear=True)
    key(upper, END, "location", P(0, 300.0, 0), linear=True)
    # slurry grains in the gap, while the plates are apart and closing
    slurry = empty("slurry", root)
    for k in range(18):
        a = 2.0 * math.pi * k / 18
        r = 150.0 + 90.0 * ((k * 37) % 5) / 4
        ball(f"grain{k}", (r * math.cos(a), TRACK_Y + WAFER_T + 20 + 12 * (k % 4), r * math.sin(a)), 5.0, m["slurry"], slurry, 6)
    show(slurry, [(0, F(2, 0.5))])
    # pressure arrows on the upper plate while it presses
    arrows = empty("pressure", root)
    for s in (-150, 0, 150):
        tube(f"shaft{s}", (s, 300, -130), (s, 240, -130), 6.0, m["red"], arrows, verts=6)
        ball(f"head{s}", (s, 236, -130), 14.0, m["red"], arrows, 8)
    show(arrows, [(F(1, 0.1), F(2, 0.8))])

    label("wafers sit between two plates, slurry in the gap", (330, 240, 0), root, [(0, F(1, 0.0))])
    label("upper plate presses: both faces wear", (330, 260, 0), root, [(F(1, 0.1), F(2, 0.0))])
    label("flat and parallel, cracked underneath", (330, 180, 0), root, [(F(2, 0.1), F(3, 0.5))])
    label("80 to 200 um removed in total", (330, 120, 0), root, [(F(3, 0.2), END)])
    camera(root, [((0.0, 150.0, 0.0), 1500.0, 0.25, 0.14)] * BEATS)
    finish("zoom_lap", page="slice")


# ---- c: Preston -----------------------------------------------------------------------------


def preston():
    m, root = begin("preston")
    carrier = K.Carrier(root, m, [(0, 0.0)])
    carrier.disc("wafer", "silicon")
    # the softened band on the top face, wiped off from left to right during beat 1
    band = K.pbox("softened_band", (-150, TRACK_Y + WAFER_T - 1, -150), (150, TRACK_Y + WAFER_T + 2, 150), m["film"], root,
                  at=(150, TRACK_Y + WAFER_T, 0))
    scale_keys(band, [(0, (1, 1, 1)), (F(1, 0.2), (1, 1, 1)), (F(1, 0.85), (0.0001, 1, 1)), (END, (0.0001, 1, 1))], until=F(1, 0.2))
    # the pad, lowered onto the wafer in beat 1
    pad = empty("pad", root)
    key(pad, 0, "location", P(0, 230, 0))
    key(pad, F(1, 0.0), "location", P(0, 230, 0), linear=True)
    key(pad, F(1, 0.6), "location", P(0, 170, 0), linear=True)
    key(pad, END, "location", P(0, 170, 0), linear=True)
    disc("pad_m", (0, 0, 0), 230.0, 30.0, m["pad"], pad, verts=72)
    # grains flowing between pad and wafer in beats 0-1
    grains = empty("grains", root)
    for k in range(14):
        a = 2.0 * math.pi * k / 14
        ball(f"pgrain{k}", (120 * math.cos(a), TRACK_Y + WAFER_T + 18, 120 * math.sin(a)), 5.0, m["slurry"], grains, 6)
    show(grains, [(0, F(2, 0.0))])
    # the removal-rate marker: a bar that climbs with pressure in beat 1
    bar = pivot("rr_bar", (300, TRACK_Y, 0), root)
    box("rr_box", (-30, 0, -30), (30, 240, 30), m["gold"], bar)
    scale_keys(bar, [(0, (1, 1, 0.02)), (F(1, 0.2), (1, 1, 0.02)), (F(1, 0.9), (1, 1, 1)), (END, (1, 1, 1))], until=F(1, 0.2))
    # pH scale in beat 2: 0 to 14 along x, with markers at 8.5 and 13
    ph_y = TRACK_Y + 20
    box("ph_scale", (-320, 0, 230), (320, 20, 250), m["grey"], root)
    for pH in (8.5, 13.0):
        x = -320 + 640 * pH / 14.0
        show(K.pbox(f"ph_mark{pH}", (x - 8, 20, 225), (x + 8, 90, 255), m["red"], root), [(F(2, 0.0), END)])
    # pits at pH 13 in beat 3
    pits = empty("pits", root)
    for k in range(12):
        x = -100 + 17 * (k % 6)
        z = -60 + 40 * (k // 6)
        ball(f"pit{k}", (x, TRACK_Y + WAFER_T + 1, z), 12.0, m["damage"], pits, 6)
    show(pits, [(F(3, 0.0), END)])
    show(pad, [(0, F(2, 0.5))])

    label("pad and slurry on the wafer", (300, 250, 0), root, [(0, F(1, 0.0))])
    label("pressure sets the rate: RR = K*P + C", (300, 280, 0), root, [(F(1, 0.1), F(2, 0.0))])
    label("silica rises with pH; ceria peaks pH 8-9", (0, 220, -190), root, [(F(2, 0.1), F(3, 0.0))])
    label("pitting seen at pH 13", (300, 140, 60), root, [(F(3, 0.1), END)])
    camera(root, [((0.0, 150.0, 0.0), 1600.0, 0.30, 0.16)] * BEATS)
    finish("zoom_preston", page="slice")


# ---- d: the thickness budget ----------------------------------------------------------------


LAYER_MAT = {"kerf": "grey", "lapping": "damage", "etch": "blue", "polish": "gold"}


def budget():
    m, root = begin("budget")
    # from the bottom: the finished wafer, then polish, etch, lapping and the kerf on top
    wafer_top = TRACK_Y + WAFER_T
    layers = [
        ("polish", 1.5, "silicon"),
        ("etch", 2.0, "silicon"),
        ("lapping", 8.0, "silicon"),
        ("kerf", 12.5, "silicon"),
    ]
    K.slab(root, "wafer", 0.0, TRACK_Y, 0, WAFER_R, WAFER_T, m["silicon"])
    home = {}
    y = wafer_top
    for name, t, mk in layers:
        obj = K.slab(root, name, 0.0, y, 0, WAFER_R, t, m[LAYER_MAT[name]])  # one colour each, or they read as one slab
        home[name] = (y, t)
        y += t
    # each layer is peeled off to the side in its own beat, in the order the process takes them
    peel = [("kerf", 0), ("lapping", 1), ("etch", 2), ("polish", 3)]
    for name, b in peel:
        obj = root.children[[c.name for c in root.children].index(name)]
        key(obj, 0, "location", P(0, 0, 0))
        key(obj, F(b, 0.2), "location", P(0, 0, 0), linear=True)
        key(obj, F(b, 0.85), "location", P(-300, 90, 0), linear=True)
        key(obj, END, "location", P(-300, 90, 0), linear=True)
    label("kerf about 125 um: lost at the saw", (-300, 220, 0), root, [(F(0, 0.3), F(1, 0.0))])
    label("lapping: 80 um example (80-200)", (-300, 220, 0), root, [(F(1, 0.3), F(2, 0.0))])
    label("etch: 15-25 um", (-300, 220, 0), root, [(F(2, 0.3), F(3, 0.0))])
    label("DSP polish: 10-20 um; 775 um left", (100, 160, 60), root, [(F(3, 0.3), END)])
    camera(root, [((-120.0, 110.0, 0.0), 1300.0, 0.35, 0.22)] * BEATS)
    finish("zoom_budget", page="slice")


BUILDERS = {"web": web, "lap": lap, "preston": preston, "budget": budget}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(BUILDERS)
    for n in which:
        BUILDERS[n]()
