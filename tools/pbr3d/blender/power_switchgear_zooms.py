"""Zoom-ins (a-e) for the SWITCHGEAR page, built from the overview's own campus (power_switchgear_overview.py).

Each zoom has three beats. Zoom beat k replays one overview beat (its beads still riding the cables,
bus bars and breakers) with its own camera pose and its own tags. The keys and titles are the old rig's
SWITCHGEAR zooms (diagrams_pwr_nodes.rs): a feed: MV to 480 V; b breaking a fault; c redundancy: 2N;
d generators and the ATS; e arc flash.

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/power_switchgear_zooms.py -- a

Writes assets/power_switchgear_zoom_<letter>.glb (and blender/power_switchgear_zoom_<letter>.blend).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label, beat  # noqa: E402
from sand_zooms import finish  # noqa: E402
import power_switchgear_overview as ov  # noqa: E402
from power_switchgear_detail import frame, camera_path  # noqa: E402

PAGE = "power_switchgear"


def zooms(w):
    """letter -> three beats of (overview beat to replay, camera pose, [(tag, point)])."""
    A, UA, P, hall = w["A"], w["UA"], w["paths"], w["hall"]
    f1, fault = A["f1"], w["fault"]
    return {
        "a": [
            (1, frame(A["f2"]["relay"], 900, 0.30, 0.20),
             [("feeder breakers", A["f2"]["relay"]), ("feeds to the substations", A["f3"]["relay"])]),
            (1, frame(UA["txc"], 600, 0.25, 0.20),
             [("unit substation: to 480 V", UA["txc"])]),
            (1, frame(P["lvB"][6], 900, 0.30, 0.20),
             [("480 V to the hall", P["lvB"][6])]),
        ],
        "b": [
            (2, frame(f1["relay"], 420, 0.25, 0.20),
             [("its relay sees the fault", f1["relay"])]),
            (2, frame(f1["bottle"], 260, 0.30, 0.15),
             [("vacuum breaker opens", f1["bottle"])]),
            (2, frame(fault, 900, 0.25, 0.20),
             [("fault current", fault), ("other feeders stay on", A["f3"]["relay"])]),
        ],
        "c": [
            (3, frame(P["feedA"][5], 1000, 0.30, 0.20),
             [("path A", P["feedA"][5])]),
            (3, frame(P["feedB"][5], 1000, -0.30, 0.20),
             [("path B", P["feedB"][5])]),
            (3, frame(hall["racks"], 1500, 0.20, 0.30),
             [("each rack fed from A and B", hall["racks"])]),
        ],
        "d": [
            (4, frame(w["GA"]["top"], 1200, 0.30, 0.20),
             [("standby generators", w["GA"]["top"]), ("ATS controller", w["house"]["ats"])]),
            (5, frame(w["house"]["ats"], 700, 0.20, 0.20),
             [("utility lost", P["mvA"][6]), ("ATS: generator breakers close", w["house"]["ats"])]),
            (6, frame(w["GB"]["top"], 1000, -0.20, 0.20),
             [("utility back", P["mvA"][6]), ("generators cool down", w["GB"]["top"])]),
        ],
        "e": [
            (2, frame(fault, 340, 0.20, 0.15),
             [("arc flash: thousands of degrees", fault)]),
            (2, frame(fault, 220, -0.30, 0.10),
             [("molten metal", fault), ("the cabinet is built to vent it", f1["relay"])]),
            (2, frame(f1["relay"], 300, 0.15, 0.15),
             [("enclosed gear", f1["relay"])]),
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
    """Delete what never shows in the replayed beats (beads and switches of other beats), so the
    scene's GLB carries only its own animation."""
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


def play(name, pick, page=PAGE):
    """Rebuilds the overview's campus, replays the overview beats that `pick(campus points)` names,
    under that plan's cameras and tags, and exports blender/<page>_<name>.blend and
    assets/<page>_<name>.glb. Shared with power_switchgear_sections.py."""
    ov.NAME = name
    ov.LABEL = lambda *a, **k: None
    ov.CAMERA = lambda *a, **k: None
    root = ov.build()
    plan = pick(ov.W)
    replay([b for b, _, _ in plan])
    camera_path(root, [c for _, c, _ in plan])
    for k, (_, _, tags) in enumerate(plan):
        for text, pt in tags:
            label(text, pt, root, beat(k))
    finish(name, page=page)


def run(letter):
    play(f"zoom_{letter}", lambda w: zooms(w)[letter])


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in "abcde":
        raise SystemExit("usage: blender -b --python power_switchgear_zooms.py -- <a|b|c|d|e>")
    run(argv[0])
