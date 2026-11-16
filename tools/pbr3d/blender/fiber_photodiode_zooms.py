"""Zoom-ins (a-e) for the FIBER PHOTODIODE page, generated from the overview's own scene.

A zoom is the overview's geometry and timeline with the camera held on one subject and a single tag.
Each zoom beat replays one whole overview beat (`states`), so the picture under each of its three
captions is the overview's own animation for that moment, seen up close.

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_photodiode_zooms.py -- a

Writes assets/fiber_photodiode_zoom_<letter>.glb. The captions and text live in
tui/src/screens/diagrams_nodes/fiber/photodiode/zooms.rs (three beats each).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
import fiber_photodiode_overview as OV  # noqa: E402
import fiber_photodiode_detail as D  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label  # noqa: E402
from sand_zooms import finish  # noqa: E402

PAGE = OV.PAGE
ZOOM_BEATS = 3  # the zoom's caption beats (zooms.rs: three per zoom)
OUT_TAG = (100.0, *D.PINS["OUT"])

# letter -> (box lo, box hi, yaw, pitch, tag text, tag position, overview beat per zoom beat).
ZOOMS = {
    # the window: the ball lens in the sealed can's cap, light from the fibre; a burst; pulses
    "a": ((-125.0, -30.0, -12.0), (-25.0, 30.0, 40.0), -0.55, 0.2, "WINDOW", (D.LENS_X, D.LENS_R, 0.0),
          [1, 4, 5]),
    # the chip: cut open, its layers; pairs freed; current leaving up the bond wire
    "b": ((8.0, -24.0, -20.0), (36.0, 40.0, 0.0), -0.45, 0.14, "CHIP", (20.0, D.MESA, 0.0), [2, 2, 3]),
    # the pins: the header's back and the four pins; current out; a bright burst; on to the board
    "c": ((30.0, -50.0, -50.0), (140.0, 50.0, 50.0), 0.8, 0.25, "PINS", OUT_TAG, [3, 4, 6]),
    # the current path: OUT pin, flex, board trace toward the cage
    "d": ((40.0, -55.0, -60.0), (OV.CAGE_X0 + 40.0, 50.0, 10.0), 0.2, 0.45, "CURRENT PATH",
          ((OV.FLEX_X + OV.CAGE_X0) / 2, OV.TRACE_Y, OV.TRACE_Z), [4, 4, 6]),
    # the module cage: the transceiver in its cage, the trace running in
    "e": ((OV.CAGE_X0 - 60.0, -55.0, -130.0), (OV.CAGE_X0 + 530.0, 160.0, 130.0), 0.25, 0.4, "MODULE CAGE",
          OV.kit(OV.K.MOD_X, 13.0, 0.0), [6, 6, 6]),
}


def retime(states):
    """Zoom beat k replays overview beat states[k] frame by frame: every animated channel is
    resampled at each frame and keyed constant, so switches stay switches."""
    n = BEAT_FRAMES * len(states)
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in list(cb.fcurves):
            vals = [fc.evaluate(b * BEAT_FRAMES + f) for b in states for f in range(BEAT_FRAMES)]
            vals.append(vals[-1])
            kps = fc.keyframe_points
            while len(kps):
                kps.remove(kps[0], fast=True)
            # Drop keys that repeat the one before; constant keys hold until the next change.
            keep = [(0, vals[0])] + [(i, v) for i, v in enumerate(vals) if i and v != vals[i - 1]]
            if keep[-1][0] != n:
                keep.append((n, vals[-1]))
            kps.add(len(keep))
            co = []
            for i, v in keep:
                co += [float(i), float(v)]
            kps.foreach_set("co", co)
            for kp in kps:
                kp.interpolation = "CONSTANT"
            fc.update()
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = n
    bpy.context.scene.frame_set(0)


def run(letter):
    if letter not in ZOOMS:
        raise SystemExit(f"unknown zoom {letter}; one of {sorted(ZOOMS)}")
    lo, hi, yaw, pitch, text, at, states = ZOOMS[letter]
    assert len(states) == ZOOM_BEATS
    pose = D.frame(lo, hi, yaw=yaw, pitch=pitch)
    OV.NAME = f"zoom_{letter}"
    OV.label = lambda *a, **k: None
    # One held pose for every overview beat, so the camera is the same in each replayed beat.
    root = OV.build(camera=lambda root, poses: D.glide_camera(root, [pose] * OV.BEATS))
    label(text, at, root, [(F(0, 0), F(OV.BEATS, 0))])
    retime(states)
    finish(f"zoom_{letter}", page=PAGE)


if __name__ == "__main__":
    letter = sys.argv[sys.argv.index("--") + 1]
    run(letter)
