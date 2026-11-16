"""Zoom-ins (a-e) for the LASER page, built from the overview's own detailed close-up (fiber_laser_overview.py).

A zoom is the overview's scene held still: each of its three caption beats (diagrams_nodes/fiber/laser/
zooms.rs) shows one frozen state of the overview, sampled at the (beat, fraction) in SAMPLES, with its own
camera pose and its own tags pinned to the parts. The subjects: a the TO-can, b the chip and facet,
c the monitor photodiode, d the window and pigtail, e the fibre core.

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_laser_zooms.py -- a

Writes assets/fiber_laser_zoom_<letter>.glb (and blender/fiber_laser_zoom_<letter>.blend).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label, beat  # noqa: E402
from sand_zooms import finish  # noqa: E402
import fiber_laser_overview as ov  # noqa: E402
from fiber_laser_overview import at, pose, C, S, PIN_BIAS, PIN_DATA, PIN_MON, DRV_X, LENS_X, FER_X  # noqa: E402
from fiber_laser_detail import camera_path  # noqa: E402

PAGE = "fiber_laser"

# chip points (bench coordinates), as fiber_laser_detail.chip lays them out at scale S
CHIP_TOP = 11 * S
FRONT = C[0] + S * 90.8
BACK = C[0] - S * 0.8
PD = (C[0] - S * 13, S * 2, 0.0)
PD_FACE = (C[0] - S * 8.5, -S * 3, 0.0)

# letter -> three beats of (overview sample (beat, fraction), camera pose, [(tag, bench point)])
ZOOMS = {
    "a": [
        ((1, 0.6), pose((14.0, -4.0, 0.0), 74.0, 0.45, 0.28),
         [("cap, cut open", (24.0, 25.0, 0.0)), ("gold header", (-2.0, 26.0, 0.0)), ("heat-sink post", (20.0, -14.0, 0.0)),
          ("glass-sealed pins", (-3.0, PIN_BIAS[0], PIN_BIAS[1]))]),
        ((2, 0.3), pose((14.0, 0.0, 0.0), 44.0, 0.35, 0.28),
         [("laser chip on its submount", (C[0] + S * 30, CHIP_TOP, 0.0)), ("bond wires from the pins", (4.0, PIN_BIAS[0], PIN_BIAS[1])),
          ("facet glow: one of 4 levels", (FRONT, 1.6, 0.0))]),
        ((3, 0.4), pose((40.0, 0.0, 0.0), 54.0, 0.35, 0.22),
         [("glass window", (39.6, 7.0, 0.0)), ("beam out through the window", (44.0, 3.0, 0.0)), ("lens ahead", (LENS_X, 9.0, 0.0))]),
    ],
    "b": [
        ((1, 0.6), pose((17.0, -1.0, 0.0), 30.0, 0.30, 0.25),
         [("InP laser chip, cut open", (C[0] + S * 45, -S * 10, 0.0)), ("AlN submount", (C[0] + S * 70, -S * 23, 0.0)),
          ("gold pads: laser, modulator", (C[0] + S * 74, CHIP_TOP, -S * 6))]),
        ((2, 0.06), pose((22.0, 0.0, 0.0), 26.0, 0.40, 0.22),
         [("top level: widest glow", (FRONT, 2.2, 0.0)), ("DFB stripe lit", (C[0] + S * 20, 0.0, 0.0))]),
        ((2, 0.19), pose((22.0, 0.0, 0.0), 26.0, 0.40, 0.22),
         [("bottom level: smallest glow", (FRONT, 0.8, 0.0)), ("modulator section absorbs", (C[0] + S * 74, CHIP_TOP, -S * 6))]),
    ],
    "c": [
        ((1, 0.6), pose((7.0, -2.0, 0.0), 30.0, 0.35, 0.28),
         [("monitor photodiode", PD), ("blue active face", PD_FACE), ("chip's back facet", (BACK, 1.5, 0.0))]),
        ((4, 0.3), pose((0.0, 4.0, -4.0), 36.0, 0.35, 0.30),
         [("back light lands on it", PD_FACE), ("photocurrent up its wire", (2.0, 8.0, -5.0)), ("monitor pin", (4.0, PIN_MON[0], PIN_MON[1]))]),
        ((4, 0.6), pose((-24.0, 4.0, -8.0), 80.0, 0.30, 0.30),
         [("back to the driver IC", (DRV_X - 13.0, 26.0, -13.0)), ("monitor pin", (-24.0, PIN_MON[0], PIN_MON[1])),
          ("bias pin back to the chip", (-24.0, PIN_BIAS[0], PIN_BIAS[1]))]),
    ],
    "d": [
        ((1, 0.6), pose((40.0, 0.0, 0.0), 48.0, 0.40, 0.22),
         [("glass window", (39.6, 7.0, 0.0)), ("cap welded shut", (1.5, 28.0, 0.0)), ("lens", (LENS_X, 9.0, 0.0))]),
        ((3, 0.35), pose((56.0, 0.0, 0.0), 64.0, 0.32, 0.22),
         [("beam crosses the window", (40.5, 3.5, 0.0)), ("lens focuses it", (LENS_X, 9.0, 0.0)), ("into the ferrule", (FER_X, 1.5, 0.0))]),
        ((3, 0.8), pose((104.0, 0.0, 0.0), 70.0, 0.35, 0.22),
         [("gold sleeve", (FER_X + 12.0, 7.5, 0.0)), ("ceramic ferrule", (FER_X + 18.0, -5.0, 0.0)), ("pigtail fibre, lit core", (130.0, 0.5, 0.0))]),
    ],
    "e": [
        ((5, 0.3), pose((FER_X - 2.0, 0.0, 0.0), 26.0, 0.45, 0.22),
         [("rays converge on the core", (FER_X - 6.0, 2.0, 0.0)), ("fibre end in the ferrule", (FER_X, 1.4, 0.0))]),
        ((5, 0.6), pose((FER_X + 10.0, 0.0, 0.0), 36.0, 0.35, 0.22),
         [("light enters the ~9 um core", (FER_X + 2.0, 0.5, 0.0)), ("glass cladding round it", (FER_X + 14.0, 1.4, 0.0))]),
        ((5, 0.85), pose((FER_X + 40.0, 0.0, 0.0), 60.0, 0.35, 0.22),
         [("light runs down the core", (FER_X + 50.0, 0.5, 0.0)), ("coating outside", (FER_X + 44.0, 4.0, 0.0))]),
    ],
}


def hold(samples):
    """Zoom beat k shows the overview's state at samples[k]: every animated channel is resampled to
    one constant key per caption beat."""
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
    beats = ZOOMS[letter]
    ov.NAME = f"zoom_{letter}"
    ov.LABEL = lambda *a, **k: None
    ov.CAMERA = lambda *a, **k: None
    root = ov.build()
    hold([b[0] for b in beats])
    camera_path(root, [b[1] for b in beats])
    for k, (_, _, tags) in enumerate(beats):
        for text, p in tags:
            label(text, at(p), root, beat(k))
    finish(ov.NAME, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python fiber_laser_zooms.py -- <a|b|c|d|e>")
    run(argv[0])
