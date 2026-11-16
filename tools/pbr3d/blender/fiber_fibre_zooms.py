"""Zoom-ins (a-e) for the OPTICAL FIBER overview (fiber_fibre_overview.py), in the SAND template.

A zoom is the overview's scene with the camera held on one subject for the whole run, and a single
tag: the tag is the zoom's short menu name (fibre/zooms.rs). Each zoom shows three beats; each zoom
beat freezes one overview state, sampled at a fraction `u` of overview beat `b`. The subject must be
on screen in that state.

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_fibre_zooms.py -- a

Writes assets/fiber_fibre_zoom_<letter>.glb. The letters:
  a laser end       laser can, lens and the ferrule tip: light focused onto the core's end
  b glass core      the magnified cut segment: rays turning back at the core wall
  c the run         the magnified segment: packets dimming, light scattering out
  d photodiode end  the far ferrule tip, the lens, the photodiode can and its wire to the amplifier
  e whole reach     the whole link from above: light the full length, the run drawn short

Each zoom beat has its own camera pose (ZOOMS), keyed after the hold.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label  # noqa: E402
from sand_zooms import camera as zoom_camera, finish  # noqa: E402
import fiber_fibre_overview as ov  # noqa: E402

PAGE = "fiber_fibre"
ZOOM_BEATS = 3  # the zoom's caption beats (fibre/zooms.rs: three per zoom)

# letter -> (poses, tag text, tag position, samples). One (target, distance, yaw, pitch) pose per zoom
# beat (mm, Y up, in the overview's scene; keep distance >= ~60, pbr3d clips nearer than 40 mm).
# Each sample is (overview beat, fraction through that beat): the state that zoom beat freezes.
ZOOMS = {
    "a": ([((-205, 0, 0), 115.0, 0.45, 0.22), ((-150, 0, 0), 230.0, 0.60, 0.30), ((-188, 0, 0), 95.0, -0.70, 0.18)],
          "laser end", (-225, 12, 0), [(1, 0.15), (1, 0.45), (1, 0.75)]),
    "b": ([((25, 110, 0), 220.0, 0.25, 0.22), ((-10, 112, 0), 110.0, 0.30, 0.20), ((25, 60, 0), 300.0, 0.30, 0.20)],
          "glass core", (-30, 135, -1), [(2, 0.30), (2, 0.55), (2, 0.85)]),
    "c": ([((25, 108, 0), 200.0, 0.30, 0.25), ((40, 108, 0), 160.0, 0.35, 0.22), ((25, 60, 0), 300.0, 0.30, 0.22)],
          "the run", (60, 135, -1), [(3, 0.25), (3, 0.55), (3, 0.85)]),
    "d": ([((245, 0, 0), 110.0, 0.45, 0.22), ((268, 0, 0), 95.0, 0.55, 0.22), ((300, 0, 0), 130.0, 0.40, 0.25)],
          "photodiode end", (235, 26, -1), [(5, 0.20), (5, 0.55), (6, 0.55)]),
    "e": ([((25, 0, 0), 620.0, 0.20, 0.55), ((25, 0, 0), 520.0, 0.35, 0.35), ((25, 0, 0), 780.0, 0.0, 0.25)],
          "whole reach", (25, 6, -1), [(4, 0.30), (4, 0.50), (4, 0.70)]),
}


def hold(samples):
    """Zoom beat k shows the overview state at samples[k] = (beat, u), switched at each zoom beat
    boundary. Every animated channel is held constant, so the camera and the tag hold with the rest."""
    frames = [k * BEAT_FRAMES for k in range(len(samples))]
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in list(cb.fcurves):
            values = [fc.evaluate(F(b, u)) for b, u in samples]
            while len(fc.keyframe_points):
                fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
            for f, value in zip(frames, values):
                kp = fc.keyframe_points.insert(f, value)
                kp.interpolation = "CONSTANT"
            fc.update()
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = BEAT_FRAMES * len(samples)
    bpy.context.scene.frame_set(0)


def run(letter):
    poses, text, at, samples = ZOOMS[letter]
    name = f"zoom_{letter}"
    # The overview's tags are replaced by this zoom's one tag, and its camera by this zoom's poses,
    # keyed after the hold (one pose per zoom beat, a slow push-in within it).
    ov.NAME = name
    ov.label = lambda *a, **k: None
    ov.camera = lambda root, poses: None
    root = ov.build()
    # The tag is on for the whole overview, so it shows in every sampled state.
    label(text, at, root, [(F(0, 0), F(ov.BEATS, 0))])
    hold(samples)
    zoom_camera(root, poses)
    bpy.context.scene.frame_set(0)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit(f"usage: blender -b --python fiber_fibre_zooms.py -- <{'|'.join(ZOOMS)}>")
    run(argv[0])
