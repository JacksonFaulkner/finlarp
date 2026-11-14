"""The SLICE + POLISH overview, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md): the seven stations of the wafer line (INGOT, SLICE, LAP, ETCH, EDGE,
POLISH, CLEAN) along a track, one station per beat, the wafer carried from one to the next, and
`label:<text>` empties for the tags the TUI pins on. The pieces are in slice_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/slice_overview.py

It writes:
  blender/slice_overview.blend   open it in Blender to edit by hand
  assets/slice_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8.

Beats (match the SLICE + POLISH overview page):
  0 ingot    a ground 300 mm ingot on its cradle
  1 slice    the ingot rides to the wire web and comes out as slices, one kerf apart
  2 lap      the wafer is carried to the plates; they close and the wafer thins, damage on its faces
  3 etch     the wafer goes into the bath; the liquid rises and the damage layer comes off
  4 edge     the wafer reaches the edge wheel, which rounds the rim
  5 polish   the pad comes down on the wafer; a sheen moves across; the face turns to a mirror
  6 clean    spray over the mirror wafer; it is inspected and shipped
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, cut, disc, empty, key, label, pivot, show  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
import slice_kit as K  # noqa: E402
from slice_kit import END, KERF_T, PITCH, STATION_X, TRACK_Y, WAFER_R, WAFER_T  # noqa: E402

BEATS = 7
X = STATION_X
INGOT_H = 6 * PITCH + WAFER_T  # seven slices with six kerfs between

# camera: one pose per beat, on the station of that beat
POSES = [((x, 260.0, 0.0), 3600.0, 0.18, 0.12) for x in X]


def build():
    m, root = start("overview", BEATS, page="slice")
    K.mats(m)
    K.floor(root, m)

    # 0-1: the ingot, carried from the grinder to the wire web and sliced there
    ingot_g = empty("ingot_carry", root)
    for f, x in [(0, X[0]), (F(1, 0.0), X[0]), (F(1, 0.2), X[1]), (END, X[1])]:
        key(ingot_g, f, "location", P(x, 0, 0), linear=True)
    cut(disc("ingot", (0, TRACK_Y + INGOT_H / 2, 0), WAFER_R, INGOT_H, m["ingot"], ingot_g, verts=72), z=-12.0)
    show(ingot_g, [(0, F(1, 0.85))])
    K.cradle(root, X[0], m)
    K.cradle(root, X[1], m)
    shelf = empty("slices", root)
    for k in range(7):
        K.slab(shelf, f"slice{k}", X[1], TRACK_Y + k * PITCH, 0, WAFER_R, WAFER_T, m["silicon"])
    show(shelf, [(F(1, 0.85), F(2, 0.0))])
    K.wire_web(root, m, X[1], [TRACK_Y + WAFER_T + KERF_T / 2 + k * PITCH for k in range(6)])

    # 2-6: the wafer rides the track; the carrier steps from station to station
    carrier = K.Carrier(root, m, K.stops_for(X, first_beat=1))
    rough = carrier.disc("wafer_rough", "silicon")
    show(rough, [(F(2, 0.0), F(5, 0.0))])
    mirror = carrier.disc("wafer_mirror", "mirror", grow=0.4)
    show(mirror, [(F(5, 0.0), END)])
    # thinning: lapping (80 um), then the etch (20 um), then DSP (15 um)
    scale_keys(carrier.pv, [
        (0, (1, 1, 1)),
        (F(2, 0.3), (1, 1, 1)),
        (F(2, 0.9), (1, 1, 0.897)),
        (F(3, 0.85), (1, 1, 0.87)),
        (F(5, 0.7), (1, 1, 0.84)),
        (END, (1, 1, 0.84)),
    ])
    # damage on both faces after lapping; the etch takes it off
    disc("damage_top", (0, WAFER_T - 1.5, 0), WAFER_R + 1, 3.0, m["damage"], carrier.pv)
    disc("damage_bot", (0, 1.5, 0), WAFER_R + 1, 3.0, m["damage"], carrier.pv)
    for name in ("damage_top", "damage_bot"):
        show(carrier.pv.children[[c.name for c in carrier.pv.children].index(name)], [(F(2, 0.3), F(3, 0.6))])

    # 2: the lapping plates close on the wafer
    disc("plate_lower", (X[2], TRACK_Y / 2, 0), 260.0, TRACK_Y, m["plate"], root, verts=72)
    upper = pivot("plate_upper", (X[2], 0, 0), root)
    disc("plate_upper_m", (0, 0, 0), 260.0, 60.0, m["plate"], upper, verts=72)
    key(upper, F(2, 0.25), "location", P(X[2], 187.5, 0), linear=True)
    key(upper, F(2, 0.85), "location", P(X[2], 140.5, 0), linear=True)
    key(upper, END, "location", P(X[2], 140.5, 0), linear=True)

    # 3: the etch bath; the liquid rises over the wafer
    liquid = K.bath(root, m, X[3])
    scale_keys(liquid, [(0, (1, 1, 0.0001)), (F(3, 0.05), (1, 1, 0.0001)), (F(3, 0.45), (1, 1, 1)), (END, (1, 1, 1))])

    # 4: the edge wheel grinds the rim; it turns while the wafer is at the station
    wheel_pv = K.edge_wheel(root, m, X[4] + WAFER_R + 90, TRACK_Y + WAFER_T / 2, r=110.0)
    show(wheel_pv.children[0], [(F(4, 0.0), F(5, 0.0))])
    K.spin(wheel_pv, F(4, 0.0), F(5, 0.0), turns=3.0, axis=1)

    # 5: the polishing pad, turning over the wafer; a sheen crosses the top face
    pad = empty("pad", root)
    key(pad, 0, "location", P(X[5], 170, 0))
    pad_disc = disc("pad_m", (0, 0, 0), 200.0, 25.0, m["pad"], pad, verts=72)
    show(pad_disc, [(F(5, 0.0), F(6, 0.0))])
    K.spin(pad, F(5, 0.0), F(6, 0.0), turns=2.0, axis=2)
    top = TRACK_Y + WAFER_T * 0.84
    sheen_g = empty("sheen_move", root)
    for f, x in [(F(5, 0.1), X[5] - 120), (F(5, 0.9), X[5] + 120)]:
        key(sheen_g, f, "location", P(x, 0, 0), linear=True)
    sheen = box("sheen", (-30, top + 0.5, -110), (30, top + 1.5, 110), m["sheen"], sheen_g)
    show(sheen, [(F(5, 0.1), F(5, 0.95))])

    # 6: spray over the mirror wafer
    K.spray_nozzles(root, m, X[6], 240.0, [(F(6, 0.1), F(6, 0.6)), (F(6, 0.3), F(6, 0.8))], n=12)

    # tags, each on the beat it explains
    label("ground 300 mm ingot", (X[0], 520, 0), root, beat(0))
    label("kerf about 125 um", (X[1] - 330, 150, 150), root, beat(1))
    label("wire web: one pass per slice", (X[1] + 300, 430, 160), root, beat(1))
    label("lapping: both faces at once", (X[2], 330, 160), root, beat(2))
    label("80 to 200 um removed", (X[2] - 300, 170, 200), root, beat(2))
    label("wet etch strips the damage", (X[3], 340, 200), root, beat(3))
    label("15-25 um removed", (X[3] - 330, 240, 0), root, beat(3))
    label("edge wheel rounds the rim", (X[4] + 260, 300, 0), root, beat(4))
    label("pad and slurry: mirror face", (X[5], 360, 0), root, beat(5))
    label("10-20 um removed (DSP)", (X[5] - 330, 200, 0), root, beat(5))
    label("clean, inspect, ship", (X[6], 330, 0), root, beat(6))
    label("775 um +/- 25, TTV 5 um", (X[6] - 260, 180, 0), root, beat(6))

    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="slice")
