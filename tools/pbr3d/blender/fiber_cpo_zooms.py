"""Zoom-ins (a-e) for the FIBER CPO node, generated from the overview's own scene (fiber_cpo_overview.py).

A zoom is the overview's geometry and timeline frozen at one overview state per caption beat (the
same pattern as pkg_zooms.py), with its own camera pose and tags for each of its three beats:

  a the switch chip       overview states 1, 2, 5: the chip, data leaving its SerDes edge, its heat
  b the optical engine    overview states 1, 3, 2: the engine, rings imprinting light, data in from the chip
  c the fibre ports       overview states 1, 3, 4: the V-groove array, light into it, light along the ribbon
  d the passive connector overview states 1, 4, 6: the connector, light through it, on along the cable
  e the substrate         overview states 1, 5, 2: the layered base, the heat across it, the copper on it

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_cpo_zooms.py -- a

Writes assets/fiber_cpo_zoom_<letter>.glb. The beats are in diagrams_nodes/fiber/cpo/zooms.rs.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label  # noqa: E402
from sand_zooms import camera as zoom_camera, finish  # noqa: E402
import fiber_cpo_overview as mod  # noqa: E402
import fiber_cpo_detail as D  # noqa: E402

W = mod.W
pose = mod.pose
FY = D.FIB_Y

# Overview (beat, fraction) each caption beat shows, per zoom. The beads ride continuously through
# their beats, so a mid-beat sample always catches some in flight.
STATES = {
    "a": [(1, 0.5), (2, 0.5), (5, 0.5)],
    "b": [(1, 0.5), (3, 0.5), (2, 0.5)],
    "c": [(1, 0.5), (3, 0.5), (4, 0.5)],
    "d": [(1, 0.5), (4, 0.5), (6, 0.5)],
    "e": [(1, 0.5), (5, 0.5), (2, 0.5)],
}

# letter -> one (camera pose, [(tag, pinned at)]) per caption beat; mm, Y up, in the overview's scene.
ZOOMS = {
    "a": [
        (pose((0.0, 3.8, 2.0), 34.0, 0.35, 0.80),
         [("SWITCH CHIP", (-4.5, 4.05, 3.5)), ("SERDES ALONG THE EDGE", (11.8, 4.05, 6.0)),
          ("BUMPS UNDER UNDERFILL", (2.0, 3.0, 13.6))]),
        (pose((10.0, 3.4, 8.5), 22.0, 0.15, 1.00),
         [("DATA LEAVES THE SERDES EDGE", (12.0, 4.05, 5.0)), ("COPPER TO THE ENGINE", W(-9.5, 2.95, -1.5))]),
        (pose((2.0, 4.0, 2.0), 42.0, 0.35, 0.80),
         [("CHIP HEAT", (0.0, 8.0, 0.0)), ("ENGINES SIT IN IT", W(0.0, 5.6, 0.0))]),
    ],
    "b": [
        (pose(W(3.0, 3.6, 0.0), 24.0, 0.45, 0.70),
         [("PHOTONIC CHIP (PIC)", W(4.5, 3.73, -3.5)), ("ELECTRONIC CHIP (EIC)", W(-4.0, 4.4, 1.5)),
          ("FIBRE ARRAY", W(10.0, 4.05, 2.0))]),
        (pose(W(6.0, 3.6, 0.0), 24.0, 0.30, 0.85),
         [("RINGS IMPRINT THE DATA", W(2.3, D.PIC_Y1 + 0.05, -1.05)), ("LIGHT INTO THE FIBRES", W(12.0, FY, -1.5))]),
        (pose(W(-7.0, 3.2, 0.0), 20.0, 0.10, 1.05),
         [("DATA IN FROM THE CHIP", W(-9.5, 2.95, -1.5)), ("ELECTRONIC CHIP", W(-4.0, 4.4, 1.0))]),
    ],
    "c": [
        (pose(W(11.0, 3.5, 0.0), 14.0, 1.00, 0.50),
         [("V-GROOVE BLOCK", W(12.0, 3.3, -3.0)), ("GLASS LID", W(10.0, 4.05, 2.5)),
          ("ONE FIBRE PER GROOVE", W(15.0, FY + 0.3, 1.5))]),
        (pose(W(12.0, 3.5, 0.0), 20.0, 0.60, 0.60),
         [("LIGHT INTO THE FIBRES", W(16.0, FY, -1.5)), ("LASER LANE IN", W(19.0, FY, -3.5))]),
        (pose(W(20.0, 3.5, 0.0), 30.0, 0.50, 0.55),
         [("ALONG THE RIBBON", W(22.0, FY + 0.5, 0.0)), ("TO THE CONNECTOR", W(30.0, 5.2, -1.0))]),
    ],
    "d": [
        (pose(W(34.0, 3.0, 0.0), 20.0, 0.75, 0.45),
         [("PASSIVE CONNECTOR", W(30.0, 5.2, -1.0)), ("CABLE CONNECTOR", W(40.0, 5.2, 0.0)),
          ("FIBRE CABLE", W(48.0, FY + 0.45, 0.0))]),
        (pose(W(36.0, 4.0, 0.0), 30.0, 0.45, 0.55),
         [("LIGHT PASSES STRAIGHT THROUGH", W(42.0, FY + 0.6, 0.0)), ("NO ELECTRONICS INSIDE", W(32.0, 2.0, -4.8))]),
        (pose((110.0, 4.0, 8.5), 80.0, 0.35, 0.55),
         [("ON ALONG THE CABLE", (140.0, FY + 1.6, 8.5)), ("FRONT PANEL", (77.0, 14.0, -2.0))]),
    ],
    "e": [
        (pose((30.0, 1.8, 32.0), 22.0, 0.55, 0.40),
         [("ORGANIC SUBSTRATE", (24.0, 2.8, 28.0)), ("COPPER PLANES AND CORE", (31.0, 1.8, 40.0)),
          ("BGA BALLS TO THE BOARD", (36.0, 0.42, 40.0))]),
        (pose((4.0, 3.5, 4.0), 90.0, 0.40, 0.75),
         [("HEAT SPREADS THROUGH IT", (-24.0, 2.8, 39.0)), ("CHIP HEAT", (0.0, 8.0, 0.0))]),
        (pose(W(-7.0, 3.2, 0.0), 20.0, 0.10, 1.05),
         [("COPPER ON THE SUBSTRATE", W(-9.5, 2.95, -1.5)), ("SERDES EDGE", (12.0, 4.05, 4.0))]),
    ],
}


def hold(states):
    """Zoom beat k shows the overview at `states[k]` = (beat, fraction), switched at each zoom beat
    boundary. Every animated channel is held constant, so the camera and the tag hold with the
    rest: one picture per caption beat."""
    frames = [k * BEAT_FRAMES for k in range(len(states))]
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in list(cb.fcurves):
            values = [fc.evaluate(F(b, u)) for b, u in states]
            while len(fc.keyframe_points):
                fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
            for f, value in zip(frames, values):
                kp = fc.keyframe_points.insert(f, value)
                kp.interpolation = "CONSTANT"
            fc.update()
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = BEAT_FRAMES * len(states)
    bpy.context.scene.frame_set(0)


def run(letter):
    if letter not in ZOOMS:
        raise SystemExit(f"unknown zoom {letter}; one of {sorted(ZOOMS)}")
    mod.NAME = f"zoom_{letter}"
    states = STATES[letter]
    poses = list(mod.POSES)
    for (b, _), (p, _) in zip(states, ZOOMS[letter]):
        poses[b] = p  # the overview beat each caption beat freezes gets that beat's pose
    root = mod.build(tags=False, poses=poses, cam=zoom_camera)
    for (b, _), (_, tags) in zip(states, ZOOMS[letter]):
        for text, at in tags:
            label(text, at, root, [(F(b, 0), F(b + 1, 0))])
    hold(states)
    finish(mod.NAME, page=mod.PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1:
        raise SystemExit("usage: blender -b --python fiber_cpo_zooms.py -- <a|b|c|d|e>")
    run(argv[0])
