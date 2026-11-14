"""The INGOT page as 3D pictures from Blender through pbr3d: an overview, four zoom-ins, ten sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/fab_ingot.py

Writes assets/ingot_<name>.glb and blender/ingot_<name>.blend for each scene.

  overview  ingot_overview  as-pulled rod, crop, test, grind, notch, wire saw
  zooms     a grind   the grinder brings the ingot to 300 mm
            b notch   the V notch on the rim, on the <110> direction
            c xray    X-ray on the cut face sets the orientation
            d wire    the wire web slices the ingot into wafers
  sections  1 what happens   2 the rod and where it is cut   3 the crystal physics
            4 by the numbers   5 wafer size ladder   6 mass and dies per wafer
            7 who makes it   8 market structure and risks   9 listed names   10 sources
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbr_kit import *  # noqa: F401,F403  (the shared helpers, see pbr_kit.py)

BF = BEAT_FRAMES
R = 150.0  # 300 mm
RAW = 170.0  # the as-pulled body, a little over size before grinding


def ingot_mats():
    return dict(
        steel=mat("steel", (0.35, 0.37, 0.42), metal=0.6, rough=0.4),
        si=mat("ingot_si", (0.50, 0.53, 0.58), metal=0.85, rough=0.22),
        raw=mat("raw_rod", (0.42, 0.44, 0.48), metal=0.7, rough=0.5),
        wafer=mat("wafer_si", (0.56, 0.58, 0.63), metal=0.9, rough=0.16),
        wire=mat("wire", (0.75, 0.78, 0.82), metal=1.0, rough=0.25),
        xray=mat("xray", (0.5, 0.95, 1.0), emit=(0.5, 0.95, 1.0), strength=3.0),
        spark=mat("spark", (1.0, 0.8, 0.4), emit=(1.0, 0.8, 0.4), strength=4.0),
        cone=mat("cone_scrap", (0.3, 0.3, 0.33), rough=0.8),
        notch=mat("notch_cut", (1.0, 0.5, 0.2), emit=(1.0, 0.5, 0.2), strength=2.0),
        bar=mat("bar_fill", (0.55, 0.58, 0.64), metal=0.5, rough=0.35),
        hi=mat("bar_high", (0.85, 0.45, 0.25), emit=(0.85, 0.45, 0.25), strength=0.4),
        dot=mat("marker", (1.0, 0.9, 0.6), emit=(1.0, 0.9, 0.6), strength=3.0),
        card=mat("card", (0.92, 0.92, 0.90), rough=0.8),
        frame=mat("frame", (0.5, 0.5, 0.55), alpha=0.1, rough=0.2),
        lump=mat("lump", (0.30, 0.30, 0.32), rough=0.9),
        spot=mat("xray_spot", (1.0, 0.95, 0.6), emit=(1.0, 0.95, 0.6), strength=3.5),
        grind=mat("grind_wheel", (0.2, 0.22, 0.26), rough=0.9),
    )


def rod(root, m, x, z=0.0, radius=RAW, length=800.0, name="rod", material=None):
    """A vertical rod standing on the floor at (x, z); its axis is poly Y."""
    return disc(name, (x, length / 2, z), radius, length, material or m["raw"], root)


# ---- overview --------------------------------------------------------------------------


def overview():
    root = start("ingot_overview", 4)
    m = ingot_mats()
    xs = [-1500, -1000, -500, 0, 500, 1000]
    box("track", (-1700, -60, -220), (1300, 0, 220), m["frame"], root)
    for k, x in enumerate(xs):
        box(f"station{k}", (x - 130, 0, -200), (x + 130, 260, 200), m["steel"], root)
    # beat 0: the as-pulled rod moves to the crop station, and its cones fall away
    body = rod(root, m, xs[0], 0, radius=RAW, length=800, name="rod")
    travel(body, [(xs[0], 400, 0), (xs[1], 400, 0)], 0, BF - 2, steps=2)
    cone = rod(root, m, xs[1], 0, radius=RAW, length=120, name="cone", material=m["cone"])
    show(cone, [(BF, 2 * BF)])
    # beat 1: the test station reads the orientation with an X-ray beam
    travel(body, [(xs[1], 400, 0), (xs[2], 400, 0)], BF, 2 * BF, steps=2)
    beam = tube("xray_beam", (xs[2], 1100, 0), (xs[2], 420, 0), 8, m["xray"], root, verts=8)
    show(beam, [(BF, 2 * BF)])
    # beat 2: the grind station turns the body down to 300 mm
    travel(body, [(xs[2], 400, 0), (xs[3], 400, 0)], 2 * BF, 2 * BF + 12, steps=2)
    track(body, [(2 * BF + 12, (1, 1, 1)), (3 * BF, (R / RAW, 1, R / RAW))])
    spin(body, 2 * BF + 12, 3 * BF)
    # beat 3: the wire saw slices the ingot into wafers, one after another
    travel(body, [(xs[3], 400, 0), (xs[4], 400, 0)], 3 * BF, 4 * BF - 2, steps=2)
    for k in range(4):
        w = disc(f"wafer{k}", (xs[5] - 240, 3 + 40 * k, 0), R, 4, m["wafer"], root)
        show(w, [(3 * BF + 4 * k, 4 * BF)])
    camera(root, [((-800, 300, 0), 3600, 0.3, 0.25), ((-200, 300, 0), 3400, 0.3, 0.25),
                  ((400, 350, 0), 3400, 0.3, 0.25), ((800, 300, 0), 3600, 0.3, 0.25)])
    finish("ingot_overview")


# ---- zoom a: the grind -----------------------------------------------------------------


def zoom_grind():
    root = start("ingot_zoom_grind", 4)
    m = ingot_mats()
    body = rod(root, m, 0, 0, radius=RAW, length=600, name="body")
    # the body turns about its axis through the whole grind
    spin(body, 0, 4 * BF, turns=2.0)
    track(body, [(0, (1, 1, 1)), (BF, (1, 1, 1)), (3 * BF, (R / RAW, 1, R / RAW)), (4 * BF - 1, (R / RAW, 1, R / RAW))])
    wheel = empty("wheel", root)
    box("wheel_block", (230, 0, -90), (330, 600, 90), m["grind"], wheel)
    travel(wheel, [(0, 0, 0), (-70, 0, 0)], BF, 3 * BF, steps=2)
    for k in range(10):
        s = ball(f"spark{k}", (200, 300 + 20 * k, 0), 12, m["spark"], root)
        travel(s, [(190, 300, 0), (120, 360 + 20 * (k % 4), 0)], BF + 4 * k, BF + 4 * k + 18, steps=2)
        show(s, [(BF, 3 * BF)])
    camera(root, [((0, 300, 0), 1600, 0.6, 0.2), ((0, 300, 0), 1500, 0.9, 0.2),
                  ((0, 300, 0), 1500, 0.6, 0.2), ((0, 300, 0), 1700, 0.4, 0.3)])
    finish("ingot_zoom_grind")


# ---- zoom b: the V notch ---------------------------------------------------------------


def zoom_notch():
    root = start("ingot_zoom_notch", 4)
    m = ingot_mats()
    wafer = disc("wafer", (0, 6, 0), R, 6, m["wafer"], root)
    spin(wafer, 0, 4 * BF, turns=0.25)
    # the notch: a V cut at the rim, in orange, shown from beat 1
    notch = boxg("notch", (R - 30, 0, -22), (R + 4, 14, 22), m["notch"])
    notch.rotation_euler = (0, math.radians(45), 0)
    show(notch, [(BF, 4 * BF)])
    # beat 2: the depth and the angle, marked by a measuring bar
    depth = boxg("depth_bar", (R - 30, 14, 26), (R + 4, 16, 30), m["dot"])
    show(depth, [(2 * BF, 3 * BF)])
    # beat 3: the <110> direction, an arrow from the centre through the notch
    arrow = tube("direction", (0, 14, 0), (R - 6, 14, 0), 2.5, m["dot"], root, verts=8)
    show(arrow, [(3 * BF, 4 * BF)])
    camera(root, [((0, 6, 0), 520, 0.5, 0.55), ((R - 10, 6, 0), 300, 0.9, 0.5),
                  ((R - 10, 6, 0), 300, 0.9, 0.5), ((0, 6, 0), 560, 0.2, 0.55)])
    finish("ingot_zoom_notch")


# ---- zoom c: X-ray orientation ---------------------------------------------------------


def zoom_xray():
    root = start("ingot_zoom_xray", 4)
    m = ingot_mats()
    block = box_block = boxg("crystal", (-150, 0, -150), (150, 300, 150), m["si"])
    spin(block, 2 * BF, 4 * BF, turns=0.125)
    # the X-ray beam comes down onto the cut face from beat 1
    beam = tube("beam", (0, 700, 0), (0, 310, 0), 10, m["xray"], root, verts=8)
    show(beam, [(BF, 4 * BF)])
    # beat 2: diffraction spots on the cut face, a symmetric pattern for the right orientation
    for k, (x, z) in enumerate(ring(6, 110)):
        s = ball(f"spot{k}", (x, 305, z), 12, m["spot"], root)
        show(s, [(2 * BF, 4 * BF)])
    camera(root, [((0, 200, 0), 1100, 0.6, 0.5), ((0, 200, 0), 1000, 0.9, 0.5),
                  ((0, 200, 0), 1000, 0.6, 0.6), ((0, 200, 0), 1100, 0.3, 0.45)])
    finish("ingot_zoom_xray")


# ---- zoom d: the wire web --------------------------------------------------------------


def zoom_wire():
    root = start("ingot_zoom_wire", 4)
    m = ingot_mats()
    # the wire web: parallel wire runs, one wire looped round two guide rollers
    for k in range(9):
        x = -280 + 70 * k
        wr = tube(f"wire{k}", (x, 40, -350), (x, 40, 350), 4, m["wire"], root, verts=8)
    for k, z in enumerate((-350, 350)):
        roller = disc(f"roller{k}", (0, 40, z), 60, 40, m["steel"], root)
    # the ingot rises through the web in beats 0-2
    ingot = rod(root, m, 0, 0, radius=R, length=400, name="ingot")
    travel(ingot, [(0, -220, 0), (0, 150, 0)], 0, 3 * BF, steps=3)
    # wafers drop off below the web in beats 2 and 3
    for k in range(5):
        w = disc(f"slice{k}", (0, -120 - 40 * k, 420 + 90 * k), R, 3, m["wafer"], root)
        show(w, [(2 * BF + 4 * k, 4 * BF)])
    camera(root, [((0, 0, 0), 1600, 0.5, 0.35), ((0, 0, 0), 1500, 0.9, 0.35),
                  ((0, 0, 0), 1500, 0.9, 0.35), ((0, 0, 0), 1700, 0.5, 0.45)])
    finish("ingot_zoom_wire")


# ---- sections --------------------------------------------------------------------------


def sec1_what_happens():
    root = start("ingot_sec1", 3)
    m = ingot_mats()
    xs = [-1200, -700, -200, 300, 800, 1300]
    for k, x in enumerate(xs):
        box(f"station{k}", (x - 120, 0, -180), (x + 120, 260, 180), m["steel"], root)
    box("track", (-1400, -40, -220), (1450, 0, 220), m["frame"], root)
    body = rod(root, m, xs[0], 0, radius=RAW, length=500, name="rod")
    travel(body, [(xs[0], 250, 0), (xs[1], 250, 0), (xs[2], 250, 0), (xs[3], 250, 0)], 0, 3 * BF - 2, steps=3)
    for k in range(4):
        w = disc(f"wafer{k}", (xs[5], 60 + 30 * k, 0), R, 4, m["wafer"], root)
        show(w, [(2 * BF + 6 * k, 3 * BF)])
    camera(root, [((-600, 200, 0), 2800, 0.3, 0.3), ((200, 200, 0), 2800, 0.3, 0.3),
                  ((900, 200, 0), 2800, 0.3, 0.3)])
    finish("ingot_sec1")


def sec2_rod():
    root = start("ingot_sec2", 3)
    m = ingot_mats()
    body = rod(root, m, 0, 0, radius=R, length=900, name="body")
    # the seed and tail cones, cropped off in beat 1
    seed = empty("seed_cone", root)
    tube("seed", (0, 900, 0), (0, 1000, 0), R * 0.7, m["cone"], seed, verts=24)
    tail = empty("tail_cone", root)
    tube("tail", (0, -100, 0), (0, 0, 0), R * 0.7, m["cone"], tail, verts=24)
    envelope(seed, [(0, 1, BF, BF + 6)])
    envelope(tail, [(0, 1, BF, BF + 6)])
    # the crop lines: flat lines across the body where the cut is made
    for k, y in enumerate((-30, 900)):
        box(f"crop_line{k}", (-R - 40, y, -4), (R + 40, y + 4, 4), m["notch"], root)
    # the cut: a wire saw line that moves down the body in beat 2
    cutl = boxg("cut_line", (-R - 30, -10, -4), (R + 30, -6, 4), m["xray"])
    travel(cutl, [(0, 900, 0), (0, 0, 0)], 2 * BF, 3 * BF - 2, steps=2)
    camera(root, [((0, 450, 0), 2600, 0.4, 0.2), ((0, 450, 0), 2400, 0.8, 0.2),
                  ((0, 450, 0), 2600, 0.4, 0.2)])
    finish("ingot_sec2")


def sec3_physics():
    root = start("ingot_sec3", 3)
    m = ingot_mats()
    cube = boxg("crystal_cube", (-200, 0, -200), (200, 400, 200), m["si"])
    spin(cube, 0, BF, turns=0.125, axis=1)
    spin(cube, BF, 2 * BF, turns=0.125, axis=0)
    # beat 2: the {111} plane, a diagonal slab through the cube, shown against the {100} face
    diag = boxg("plane111", (-230, 180, -6), (230, 196, 6), m["hi"])
    diag.rotation_euler = (math.radians(45), 0, math.radians(35))
    show(diag, [(2 * BF, 3 * BF)])
    camera(root, [((0, 200, 0), 1600, 0.5, 0.35), ((0, 200, 0), 1500, 0.5, 0.35),
                  ((0, 200, 0), 1500, 0.5, 0.35)])
    finish("ingot_sec3")


def sec4_numbers():
    root = start("ingot_sec4", 3)
    m = ingot_mats()
    # diameter 300, thickness 775 um, mass 125 g, notch depth 1.0 mm
    grow_bar(root, "diameter", -600, -420, 300 / 2, m["bar"], 0, BF)
    grow_bar(root, "thickness", -100, 80, 775 / 10, m["hi"], BF, 2 * BF)
    grow_bar(root, "mass", 420, 600, 125 * 2, m["bar"], 2 * BF, 3 * BF)
    camera(root, [((-300, 200, 0), 2000, 0.2, 0.2), ((0, 200, 0), 2000, 0.2, 0.2),
                  ((400, 200, 0), 2000, 0.2, 0.2)])
    finish("ingot_sec4")


def sec5_ladder():
    root = start("ingot_sec5", 3)
    m = ingot_mats()
    data = [("100 mm", 525), ("150 mm", 675), ("200 mm", 725), ("300 mm", 775), ("450 mm", 925)]
    for k, (name, um) in enumerate(data):
        x = -800 + k * 400
        f0 = 0 if k < 2 else (BF if k < 4 else 2 * BF)
        grow_bar(root, name, x - 110, x + 110, um / 2, m["hi"] if name == "300 mm" else m["bar"], f0, f0 + BF)
    camera(root, [((-400, 200, 0), 2200, 0.2, 0.2), ((0, 200, 0), 2200, 0.2, 0.2),
                  ((400, 200, 0), 2200, 0.2, 0.2)])
    finish("ingot_sec5")


def sec6_mass():
    root = start("ingot_sec6", 3)
    m = ingot_mats()
    data = [("100 mm", 10, 56), ("200 mm", 53, 269), ("300 mm", 125, 640), ("450 mm", 342, 1490)]
    for k, (name, g, dies) in enumerate(data):
        x = -900 + k * 600
        f0 = k * BF // 2
        grow_bar(root, f"mass_{name}", x - 110, x + 110, g, m["hi"] if name == "300 mm" else m["bar"], f0, f0 + BF)
    camera(root, [((-300, 200, 0), 2600, 0.2, 0.2), ((300, 200, 0), 2600, 0.2, 0.2),
                  ((300, 200, 0), 2600, 0.2, 0.2)])
    finish("ingot_sec6")


def sec7_share():
    root = start("ingot_sec7", 3)
    m = ingot_mats()
    data = [("Shin-Etsu", 19.9), ("SUMCO", 17.2), ("GlobalWafers", 12.9), ("Siltronic", 9.9), ("SK Siltron", 8.6)]
    for k, (name, pct) in enumerate(data):
        x = -700 + k * 350
        f0 = 0 if k < 2 else (BF if k < 4 else 2 * BF)
        grow_bar(root, name, x - 120, x + 120, pct * 12, m["hi"] if k < 2 else m["bar"], f0, f0 + BF)
    camera(root, [((-300, 150, 0), 2600, 0.2, 0.2), ((0, 150, 0), 2600, 0.2, 0.2),
                  ((300, 150, 0), 2600, 0.2, 0.2)])
    finish("ingot_sec7")


def sec8_structure():
    root = start("ingot_sec8", 3)
    m = ingot_mats()
    # five firms close together, the top two in beat 0; a chokepoint marker; long-term agreements
    for k in range(5):
        x = -700 + k * 350
        grow_bar(root, f"firm{k}", x - 110, x + 110, (90 - 4 * k) * 2, m["hi"] if k < 2 else m["bar"], 0, BF)
    chok = marker(root, "choke", -700, 0, m["dot"], r=60)
    travel(chok, [(-700, 0, 0), (-700, 220, 0)], BF, 2 * BF, steps=2)
    lta = boxg("lta_band", (-900, 100, -20), (900, 120, 20), m["notch"])
    show(lta, [(2 * BF, 3 * BF)])
    camera(root, [((0, 150, 0), 2600, 0.2, 0.2), ((0, 150, 0), 2600, 0.2, 0.2),
                  ((0, 150, 0), 2600, 0.2, 0.2)])
    finish("ingot_sec8")


def sec9_names():
    root = start("ingot_sec9", 3)
    m = ingot_mats()
    names = ["Shin-Etsu", "SUMCO", "GlobalWafers", "Siltronic", "SK Siltron"]
    for k in range(5):
        x = -800 + (k % 3) * 800
        z = -250 + (k // 3) * 500
        tile = empty(f"name{k}", root)
        box(f"tile{k}", (x - 200, 0, z - 100), (x + 200, 30, z + 100), m["card"], tile)
        beat = k // 2
        envelope(tile, [(beat * BF, beat * BF + 2, 3 * BF - 2, 3 * BF + 4)])
    camera(root, [((0, 60, 0), 2400, 0.3, 0.7), ((0, 60, 0), 2400, 0.3, 0.7),
                  ((0, 60, 0), 2400, 0.3, 0.7)])
    finish("ingot_sec9")


def sec10_sources():
    root = start("ingot_sec10", 3)
    m = ingot_mats()
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
    camera(root, [((0, 60, 0), 1800, 0.6, 0.7), ((0, 80, 0), 1800, 0.9, 0.7),
                  ((0, 80, 0), 1800, 0.3, 0.8)])
    finish("ingot_sec10")


def build_all():
    overview()
    zoom_grind()
    zoom_notch()
    zoom_xray()
    zoom_wire()
    sec1_what_happens()
    sec2_rod()
    sec3_physics()
    sec4_numbers()
    sec5_ladder()
    sec6_mass()
    sec7_share()
    sec8_structure()
    sec9_names()
    sec10_sources()


if __name__ == "__main__":
    build_all()
