"""The COAT node page's overview (FRONT END, resist coat), in the picture-and-panel template.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/coat_overview.py

Writes blender/coat_overview.blend and assets/coat_overview.glb. One beat is 8 s.

One coater-developer track, left to right: the FOUP carrier port, the adhesion-promoter (HMDS)
plate, the BARC coater cup, the resist coater cup with its nozzle, the soft-bake hot plate, the
chill plate, the interface buffer and the scanner. One wafer rides a robot arm (a glide at carry
height) from station to station; its film layers switch on as they are applied.

Beats (match the six beats in diagrams_nodes/coat/overview.rs):
  0 track     the whole track; the wafer leaves the carrier port for the primer
  1 prime     primer on the plate, then the wafer glides to the BARC cup; the BARC layer appears
  2 spin      the resist nozzle drops a bead on the centre; the wafer spins, the film spreads
  3 rim       the edge-bead nozzle trims the rim with solvent
  4 bake      the wafer glides to the soft-bake plate, which glows while the solvent drives off
  5 chill     the chill plate cools the wafer; it goes on to the interface buffer and the scanner

sand_zooms.finish() exports every frame of this short scene, so no key thinning is needed.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, ball, cup, disc, empty, fly, key, label, beat, mat, show, tube  # noqa: E402
from sand_zooms import start, camera, finish  # noqa: E402

PAGE = "coat"
NAME = "overview"
BEATS = 6
END = 6  # beat index used as "until the end"

ST_Y = 320.0  # wafer centre height when parked on a station (its underside sits on the chuck)
CARRY_Y = 620.0  # robot arm carry height, above the cups and under the rail
FOUP_X, HMDS_X, BCT_X, COT_X, HOT_X, CHILL_X, IF_X = -1000.0, -560.0, -120.0, 330.0, 760.0, 1100.0, 1400.0
PLATE_Y = 290.0  # plate centre; plate top at 300
CUP_R, CUP_H = 230.0, 150.0


def transit(a, b):
    """Robot route from station x=a to station x=b: lift, carry at CARRY_Y, lower."""
    return [(a, ST_Y, 0.0), (a, CARRY_Y, 0.0), (b, CARRY_Y, 0.0), (b, ST_Y, 0.0)]


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = {
        "steel": mat("c_steel", (0.62, 0.64, 0.67), metal=0.8, rough=0.35),
        "body": mat("c_body", (0.84, 0.86, 0.88), rough=0.5),
        "dark": mat("c_dark", (0.16, 0.18, 0.20), rough=0.6),
        "floor": mat("c_floor", (0.30, 0.32, 0.34), rough=0.9),
        "chem": mat("c_chem", (0.90, 0.75, 0.20), rough=0.6),
        "foup": mat("c_foup", (0.92, 0.93, 0.95), rough=0.3, alpha=0.5),
        "si": mat("c_si", (0.38, 0.42, 0.48), metal=0.7, rough=0.3),
        "barc": mat("c_barc", (0.10, 0.10, 0.12), rough=0.5),
        "resist": mat("c_resist", (0.95, 0.62, 0.20), rough=0.2, alpha=0.75),
        "hot": mat("c_hot", (0.90, 0.35, 0.10), emit=(1.0, 0.40, 0.10), strength=6.0, rough=0.6),
        "cool": mat("c_cool", (0.40, 0.70, 0.95), emit=(0.40, 0.80, 1.0), strength=2.0, rough=0.5),
        "drop": mat("c_drop", (1.0, 0.70, 0.25), emit=(1.0, 0.70, 0.25), strength=8.0),
    }

    # the floor, the track's base cabinet, the chemical cabinet behind the row
    box("floor", (-1250, -20, -700), (2700, 0, 700), m["floor"], root)
    box("base", (-1100, 0, -260), (1500, 60, 260), m["dark"], root)
    box("chem", (-420, 60, -460), (980, 260, -300), m["chem"], root)

    # carrier port (FOUP), interface buffer, scanner with its lens
    box("foup", (FOUP_X - 140, 60, -150), (FOUP_X + 140, 420, 150), m["foup"], root)
    box("buffer", (1300, 60, -200), (1500, 420, 200), m["body"], root)
    box("scanner", (1800, 60, -230), (2600, 420, 230), m["dark"], root)
    tube("scanner_lens", (1800, 240, 0), (1700, 240, 0), 80, m["steel"], root)
    tube("rail", (-1100, 700, 0), (2000, 700, 0), 10, m["steel"], root)

    # stations: the HMDS and hot/chill plates, and the two coater cups with their chucks
    disc("hmds_plate", (HMDS_X, PLATE_Y, 0), 160, 20, m["body"], root)
    disc("hot_plate", (HOT_X, PLATE_Y, 0), 160, 20, m["steel"], root)
    disc("chill_plate", (CHILL_X, PLATE_Y, 0), 160, 20, m["body"], root)
    for name, x in (("bct", BCT_X), ("cot", COT_X)):
        cup(f"{name}_cup", (x, 300, 0), CUP_R, CUP_H, m["steel"], root)
        disc(f"{name}_chuck", (x, 305, 0), 120, 10, m["dark"], root)
    glow_hot = disc("hot_glow", (HOT_X, 302, 0), 150, 4, m["hot"], root)
    glow_cool = disc("cool_glow", (CHILL_X, 302, 0), 150, 4, m["cool"], root)
    show(glow_hot, [(F(4, 0), F(END, 0))])
    show(glow_cool, [(F(5, 0), F(END, 0))])

    # the wafer: substrate, BARC and resist, built at the origin and moved by its location keys
    wf = empty("c_wafer", root)
    sub = disc("c_sub", (0, 0, 0), 150, 20, m["si"], parent=wf)
    barc = disc("c_barc_layer", (0, 12, 0), 150, 4, m["barc"], parent=wf)
    resist = disc("c_resist_layer", (0, 19, 0), 150, 10, m["resist"], parent=wf)
    show(barc, [(F(1, 0.6), F(END, 0))])
    show(resist, [(F(2, 0.3), F(END, 0))])

    fly(wf, transit(FOUP_X, HMDS_X), F(0, 0.10), F(0, 0.90), steps=8)  # beat 0: out of the port to the primer
    fly(wf, transit(HMDS_X, BCT_X), F(1, 0.45), F(1, 0.85), steps=8)  # beat 1: to the BARC cup
    fly(wf, transit(BCT_X, COT_X), F(2, 0.00), F(2, 0.25), steps=8)  # beat 2: to the resist cup
    # beat 2: spin the wafer after the drop lands
    wf.rotation_euler = (0, 0, 0)
    for f, a in ((F(2, 0.30), 0.0), (F(2, 0.90), 6 * math.pi)):
        key(wf, f, "rotation_euler", value=(0, 0, a), linear=True)
    fly(wf, transit(COT_X, HOT_X), F(4, 0.05), F(4, 0.40), steps=8)  # beat 4: to the soft-bake plate
    fly(wf, transit(HOT_X, CHILL_X), F(5, 0.00), F(5, 0.30), steps=8)  # beat 5: to the chill plate
    fly(wf, transit(CHILL_X, IF_X), F(5, 0.45), F(5, 0.90), steps=8)  # beat 5: to the interface buffer

    # beat 2: the resist nozzle, a drop falling onto the centre, and a few drops flung off the rim
    nozzle = tube("c_nozzle", (COT_X, 720, 0), (COT_X, 470, 0), 10, m["steel"], root)
    show(nozzle, [(F(2, 0.02), F(2, 0.30))])
    drop = ball("c_drop", (0, 0, 0), 7, m["drop"], root)
    show(drop, [(F(2, 0.08), F(2, 0.22))])
    fly(drop, [(COT_X, 470, 0.0), (COT_X, 340, 0.0)], F(2, 0.08), F(2, 0.22), steps=4)
    for i, a in enumerate((0.0, 1.6, 3.2, 4.7)):
        fling = ball(f"c_fling{i}", (0, 0, 0), 5, m["drop"], root)
        show(fling, [(F(2, 0.45), F(2, 0.75))])
        p0 = (COT_X + 160 * math.cos(a), 340.0, 160 * math.sin(a))
        p1 = (COT_X + 215 * math.cos(a), 330.0, 215 * math.sin(a))
        fly(fling, [p0, p1], F(2, 0.45), F(2, 0.75), steps=3)

    # beat 3: the edge-bead nozzle sprays solvent on the rim only
    ebr = tube("c_ebr", (COT_X + 190, 520, 0), (COT_X + 158, 345, 0), 6, m["steel"], root)
    ebr_tip = ball("c_ebr_tip", (COT_X + 155, 332, 0), 8, m["drop"], root)
    show(ebr, [(F(3, 0.05), F(3, 0.90))])
    show(ebr_tip, [(F(3, 0.05), F(3, 0.90))])

    tags = {
        0: [
            ("one track: coat, bake, chill", (400, 800, 0)),
            ("carrier port (FOUP) in", (FOUP_X, 500, 0)),
            ("robot arm carries the wafer", (-300, 680, 0)),
            ("scanner", (2200, 520, 0)),
        ],
        1: [
            ("adhesion promoter (HMDS)", (HMDS_X, 420, 0)),
            ("BARC coater", (BCT_X, 500, 0)),
            ("bottom anti-reflect layer", (BCT_X, 340, 150)),
        ],
        2: [
            ("resist nozzle", (COT_X, 520, 0)),
            ("drop onto the centre", (COT_X, 390, -60)),
            ("spin: film spreads", (COT_X, 500, 220)),
        ],
        3: [
            ("edge bead removal", (COT_X + 190, 540, 0)),
            ("solvent on the rim only", (COT_X, 340, 170)),
        ],
        4: [
            ("soft bake hot plate", (HOT_X, 380, 0)),
            ("drives off solvent", (HOT_X, 330, -120)),
        ],
        5: [
            ("chill plate", (CHILL_X, 380, 0)),
            ("interface buffer", (IF_X, 500, 0)),
            ("scanner waits for PEB", (2200, 520, 0)),
        ],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera(root, POSES)
    return root


# (target, distance, yaw, pitch) per beat, as sand_zooms.camera expects
POSES = [
    ((400, 300, 0), 3300, 0.0, 0.22),
    ((-340, 330, 0), 1100, 0.15, 0.20),
    ((COT_X - 60, 380, 0), 1000, 0.25, 0.35),
    ((COT_X, 340, 0), 480, -0.20, 0.70),
    ((HOT_X, 330, 0), 720, -0.20, 0.22),
    ((1250, 330, 0), 1000, 0.10, 0.22),
]


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
