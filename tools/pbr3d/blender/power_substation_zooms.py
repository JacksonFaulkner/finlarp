"""Zoom-ins (a-e) for the SUBSTATION page, built from the overview's own scene (power_substation_overview.py).

A zoom replays the overview: each of its three caption beats (diagrams_nodes/power/substation/zooms.rs)
plays one window (beat, u0, u1) of the overview stretched over 8 s, so the beads keep moving, with its
own camera pose and its own tags pinned to the parts. The subjects: a the core and windings, b how the
turns ratio works, c losses and cooling, d lead times, e electrical steel.

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/power_substation_zooms.py -- a

Writes assets/power_substation_zoom_<letter>.glb (and blender/power_substation_zoom_<letter>.blend).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label, beat  # noqa: E402
import power_substation_overview as ov  # noqa: E402
import power_substation_detail as D  # noqa: E402
from power_substation_detail import frame, camera_path, finish, ZC, LXS, HVB_X, LVB_X, HV_TOP, LV_TOP  # noqa: E402

B = LXS[1]
ROWS = [(ov.WK_X0 + ov.WK_UNIT * w, 34.0, z - 18.0) for w, z in zip((50, 120, 128, 144), ov.WK_Z)]
LEAD = frame((-60.0, 60.0, 300.0), 1150.0, 0.15, 0.78)

# letter -> three beats of (overview window (beat, u0, u1), camera pose, [(tag, point)])
ZOOMS = {
    "a": [
        ((2, 0.4, 1.0), frame((0.0, 300.0, ZC), 760.0, 0.14, 0.08),
         [("laminated electrical steel", (B, 460.0, ZC)), ("3 limbs", (LXS[0], 330.0, ZC)), ("2 yokes", (LXS[2] + 20.0, 140.0, ZC))]),
        ((2, 0.4, 1.0), frame((B - 20.0, 300.0, ZC), 300.0, 0.18, 0.08),
         [("LV winding: few heavy turns", (B - 61.0, 330.0, ZC)), ("steel limb inside", (B, 260.0, ZC)),
          ("pressboard barrier", (B - 75.0, 410.0, ZC))]),
        ((2, 0.4, 1.0), frame((B + 50.0, 300.0, ZC), 320.0, 0.22, 0.08),
         [("HV winding: many disc coils", (B + 97.0, 330.0, ZC)), ("pressboard between the discs", (B + 97.0, 250.0, ZC)),
          ("lead from the HV bushing", (B + 97.0, 425.0, ZC - 6.0))]),
    ],
    "b": [
        ((3, 0.0, 0.5), frame((0.0, 300.0, ZC), 820.0, 0.12, 0.08),
         [("current in the HV winding", (LXS[0] + 97.0, 300.0, ZC)), ("makes flux in the core", (B, 300.0, ZC))]),
        ((3, 0.5, 1.0), frame((B + 20.0, 300.0, ZC), 360.0, 0.16, 0.08),
         [("one flux through both coils", (B, 320.0, ZC)), ("same volts in every turn", (B + 97.0, 280.0, ZC)),
          ("LV: fewer turns, fewer volts", (B - 61.0, 260.0, ZC))]),
        ((4, 0.0, 1.0), frame((40.0, 560.0, -190.0), 1250.0, 0.22, 0.14),
         [("230 kV in", (HVB_X[0], HV_TOP, D.HVB_Z)), ("34.5 kV out", (LVB_X[2], LV_TOP, D.LVB_Z)),
          ("~6.7x more turns on the HV side", (B + 97.0, 330.0, ZC))]),
    ],
    "c": [
        ((5, 0.0, 0.3), frame((0.0, 300.0, ZC), 820.0, 0.14, 0.08),
         [("core loss: heat in the steel", (B, 460.0, ZC)), ("there even at no load", (LXS[2], 300.0, ZC))]),
        ((5, 0.33, 0.66), frame((0.0, 300.0, ZC), 820.0, 0.14, 0.08),
         [("copper loss: resistance", (LXS[0] + 97.0, 300.0, ZC)), ("grows with the load", (LXS[2] - 61.0, 260.0, ZC))]),
        ((5, 0.55, 1.0), frame((300.0, 330.0, -170.0), 900.0, 0.42, 0.14),
         [("hot oil rises", (LXS[2] + 77.0, 380.0, ZC)), ("cooled in the radiators", (D.RAD_R[0] + 60.0, 300.0, -40.0)),
          ("fans", (D.RAD_R[0] + 60.0, D.RAD_Y[0] - 22.0, -90.0))]),
    ],
    "d": [
        ((6, 0.0, 0.25), LEAD, [("2021: ~50 weeks", ROWS[0]), ("one tick = one year", (ov.WK_X0 + ov.WK_UNIT * 52, 68.0, ov.WK_Z[0]))]),
        ((6, 0.25, 0.55), LEAD, [("2021: ~50 weeks", ROWS[0]), ("2024: ~120 weeks", ROWS[1])]),
        ((6, 0.55, 1.0), LEAD, [("2025: ~128 weeks", ROWS[2]), ("step-up units: ~144 weeks", ROWS[3])]),
    ],
    "e": [
        ((2, 0.4, 1.0), frame((LXS[2], 300.0, ZC), 420.0, 0.2, 0.1),
         [("grain-oriented electrical steel", (LXS[2], 330.0, ZC)), ("thin insulated sheets", (LXS[2] + 30.0, 460.0, ZC))]),
        ((2, 0.4, 1.0), frame((B, 450.0, ZC), 520.0, 0.3, 0.3),
         [("few mills make it", (B, 500.0, ZC - 20.0)), ("sheets stacked in packets", (B + 100.0, 500.0, ZC - 30.0))]),
        ((0, 0.0, 1.0), ov.POSES[0], [("each unit built for its site", (0.0, D.TY1, -40.0)), ("little spare stock", (D.TX1, 300.0, 0.0))]),
    ],
}


def replay(windows):
    """Zoom beat k plays overview frames F(b, u0)..F(b, u1) stretched over one beat: every animated
    channel is resampled to a key every second frame (scale keys stay constant, so switches stay sharp)."""
    nb = len(windows)
    frames = list(range(0, BEAT_FRAMES * nb + 1, 2))

    def src(f):
        k = min(f // BEAT_FRAMES, nb - 1)
        local = (f - k * BEAT_FRAMES) / BEAT_FRAMES
        b, u0, u1 = windows[k]
        return BEAT_FRAMES * (b + u0 + (u1 - u0) * local)

    dead = []
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in list(cb.fcurves):
            values = [fc.evaluate(src(f)) for f in frames]
            if fc.data_path == "scale" and max(values) < 1e-3:
                dead.append(obj)
                break
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(frames))
            co = []
            for f, v in zip(frames, values):
                co += [f, v]
            fc.keyframe_points.foreach_set("co", co)
            interp = "CONSTANT" if fc.data_path == "scale" else "LINEAR"
            for kp in fc.keyframe_points:
                kp.interpolation = interp
            fc.update()
    prune(dead)
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = BEAT_FRAMES * nb
    bpy.context.scene.frame_set(0)


def prune(objs):
    """Delete objects (and everything under them): switched off all through the zoom, or not needed."""
    gone = set()

    def walk(o):
        for c in o.children:
            walk(c)
        gone.add(o.name)

    for o in objs:
        walk(o)
    for nm in gone:
        o = bpy.data.objects.get(nm)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)


# zooms that never look at the yard drop its equipment (the gravel stays)
NO_YARD = "acd"


def run(letter):
    beats = ZOOMS[letter]
    ov.NAME = f"zoom_{letter}"
    ov.LABEL = lambda *a, **k: None
    ov.CAMERA = lambda *a, **k: None
    root = ov.build()
    if letter in NO_YARD:
        yard = bpy.data.objects["yd"]
        prune([c for c in yard.children if c.name != "yd_gravel"])
    replay([b[0] for b in beats])
    camera_path(root, [b[1] for b in beats])
    for k, (_, _, tags) in enumerate(beats):
        for text, p in tags:
            label(text, p, root, beat(k))
    finish(ov.NAME)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python power_substation_zooms.py -- <a|b|c|d|e>")
    run(argv[0])
