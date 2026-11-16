"""Zoom-ins (a-e) for the RACK POWER page, built from the overview's own scene (power_rack_overview.py).

Each zoom has three beats. Zoom beat k replays one overview beat (its beads still riding the busbar,
cables and busway) with its own camera pose and its own tags. The keys and titles are the old rig's
RACK POWER zooms (diagrams_pwr_nodes.rs): a AC in, DC down the back; b power shelves; c kilowatts per
rack; d 800 V DC and the sidecar; e why so many amps.

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/power_rack_zooms.py -- a

Writes assets/power_rack_zoom_<letter>.glb (and blender/power_rack_zoom_<letter>.blend).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label, beat  # noqa: E402
import power_rack_overview as ov  # noqa: E402
import power_rack_detail as D  # noqa: E402
from power_rack_detail import (  # noqa: E402
    BP, BN, BUSWAY_Y, RY1, SHELVES, U, frame, glide_camera, slot_y,
)

PAGE = "power_rack"
ROW_X = ov.ROW_X
SIDE_X = ov.SIDE_X
Y_FEED = RY1 + 420.0
XB = (BP[0] + BP[1]) / 2
XN = (BN[0] + BN[1]) / 2


def ys(i):
    return slot_y(i) + U / 2


def zooms():
    """letter -> three beats of (overview beat to replay, (lo, hi, yaw, pitch) or pose, [(tag, point)])."""
    return {
        "a": [
            (1, frame((300.0, slot_y(SHELVES[6]) - 120.0, -330.0), (560.0, BUSWAY_Y + 100.0, -60.0), 0.50, 0.10),
             [("busway tap-off box", (495.0, BUSWAY_Y - 75, -190.0)), ("power shelf: AC inlet", (480.0, ys(SHELVES[6]), -223.0))]),
            (2, frame((-260.0, slot_y(SHELVES[4]) - 60.0, -200.0), (600.0, slot_y(SHELVES[6]) + 80.0, 0.0), 0.30, 0.05),
             [("PSU makes ~50 V DC", (-200.0, slot_y(SHELVES[5]) + 34, 0.0)), ("+50 V busbar", (XB, ys(27), 0.0))]),
            (2, frame((BP[0] - 40.0, ys(18) - 40.0, -120.0), (BN[1] + 40.0, ys(26) + 40.0, 0.0), 0.20, 0.05),
             [("shelf clips onto the bar", (BP[0] - 4, slot_y(SHELVES[4]) + 29, 0.0)), ("return bar", (XN, ys(23), 0.0))]),
        ],
        "b": [
            (1, frame((-600.0, slot_y(SHELVES[6]) - 30.0, -560.0), (480.0, slot_y(SHELVES[6]) + 60.0, 0.0), 0.40, 0.12),
             [("power shelves: 4 at the top", (-200.0, ys(SHELVES[6]), 0.0))]),
            (1, frame((-600.0, slot_y(SHELVES[1]) - 30.0, -560.0), (480.0, slot_y(SHELVES[1]) + 60.0, 0.0), 0.40, 0.12),
             [("power shelves: 4 at the bottom", (-200.0, ys(SHELVES[1]), 0.0))]),
            (1, frame((-300.0, slot_y(SHELVES[5]) - 60.0, -400.0), (300.0, slot_y(SHELVES[5]) + 60.0, 0.0), 0.30, 0.10),
             [("6 PSUs x 5.5 kW = 33 kW", (-200.0, ys(SHELVES[5]), 0.0))]),
        ],
        "c": [
            (0, frame((-420.0, -40.0, -300.0), (420.0, slot_y(37) + 120.0, 0.0), 0.30, 0.06),
             [("~120 kW", (-200.0, ys(27), 0.0))]),
            (5, frame((ROW_X - 2800.0, 0.0, -1200.0), (ROW_X + 2800.0, BUSWAY_Y + 100.0, 0.0), -0.45, 0.16, 1.02),
             [("8 racks: about 1 MW", (ROW_X - 620.0, RY1 + 30.0, 0.0))]),
            (5, frame((ROW_X - 330.0, -40.0, -330.0), (ROW_X + 330.0, slot_y(37) + 120.0, 0.0), 0.30, 0.04),
             [("one NVL72-class rack ~120 kW", (ROW_X, slot_y(20), 6.0))]),
        ],
        "d": [
            (6, frame((SIDE_X - 1300.0, 0.0, -1200.0), (SIDE_X + 700.0, Y_FEED + 40.0, 0.0), 0.42, 0.14, 1.04),
             [("800 V DC feed", (SIDE_X - 900.0, Y_FEED + 32.0, -340.0)), ("sidecar power rack", (SIDE_X + 310.0, slot_y(20), 6.0))]),
            (6, frame((SIDE_X - 260.0, RY1 - 40.0, -330.0), (SIDE_X + 260.0, RY1 + 120.0, -160.0), 0.30, 0.10),
             [("DC link into the rack", (SIDE_X, RY1 + 70.0, -230.0))]),
            (6, frame((SIDE_X - 200.0, slot_y(4), -300.0), (SIDE_X + 500.0, slot_y(12), 0.0), 0.40, 0.08),
             [("compute rack", (SIDE_X - 310.0, slot_y(20), 6.0))]),
        ],
        "e": [
            (4, frame((BP[0] - 60.0, ys(14), -160.0), (BN[1] + 60.0, ys(27), 0.0), 0.30, 0.08),
             [("~2,400 A at 120 kW", (XB, ys(27), 0.0)), ("copper bar, not a cable", (XN, ys(25), 0.0))]),
            (4, frame((BP[0] - 60.0, ys(24), -120.0), (BN[1] + 60.0, ys(30), 0.0), 0.20, 0.06),
             [("every clip carries its share", (BP[0] - 4, ys(26), 0.0))]),
            (4, frame((-420.0, 0.0, -300.0), (600.0, slot_y(29), 0.0), 0.32, 0.06),
             [("thousands of amps", (XB, ys(27), 0.0))]),
        ],
    }


def replay(beats):
    """Zoom beat k plays overview beat beats[k]: every animated channel is resampled, frame by
    frame, from that overview beat into this one."""
    n = BEAT_FRAMES
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in list(cb.fcurves):
            vals = []
            for k, b in enumerate(beats):
                for j in range(n):
                    vals.append((k * n + j, fc.evaluate(F(b, 0) + j)))
            vals.append((len(beats) * n, vals[-1][1]))
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(vals))
            fc.keyframe_points.foreach_set("co", [c for f, v in vals for c in (f, v)])
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.update()
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = n * len(beats)
    bpy.context.scene.frame_set(0)
    prune()


def prune():
    """Delete what never shows in the replayed beats, so the zoom's GLB carries only its own animation."""
    gone = []
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        sc = [fc for fc in cb.fcurves if fc.data_path == "scale"]
        if sc and all(max(abs(k.co[1]) for k in fc.keyframe_points) < 1e-3 for fc in sc[:1]):
            gone.append(obj)
    doomed = set()
    for o in gone:
        doomed.add(o)
        doomed.update(o.children_recursive)
    for o in doomed:
        bpy.data.objects.remove(o, do_unlink=True)


def play(name, plan, page=PAGE):
    """Rebuilds the overview scene, replays the overview beats in `plan` under the plan's cameras and
    tags, and exports blender/<page>_<name>.blend and assets/<page>_<name>.glb. Shared with the sections."""
    ov.NAME = name
    ov.label = lambda *a, **k: None  # the overview's own tags are not wanted in a zoom
    ov.glide_camera = lambda *a, **k: None
    root = ov.build()
    replay([b for b, _, _ in plan])
    glide_camera(root, [pose for _, pose, _ in plan])
    for k, (_, _, tags) in enumerate(plan):
        for text, pt in tags:
            label(text, pt, root, beat(k))
    D.done(name)


def run(letter):
    play(f"zoom_{letter}", zooms()[letter])


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in "abcde":
        raise SystemExit("usage: blender -b --python power_rack_zooms.py -- <a|b|c|d|e>")
    run(argv[0])
