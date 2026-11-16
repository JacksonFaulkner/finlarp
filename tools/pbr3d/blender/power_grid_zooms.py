"""Zoom-ins (a-e) for the GRID page, built from the overview's own diorama (power_grid_overview.py).

Each zoom has three beats. Zoom beat k replays one whole overview beat (its beads still riding the
conductors, cables and busways) with its own camera pose and its own tags; the keys of the old
rig's GRID zooms (diagrams_pwr_nodes.rs): a transmission, b how much power AI uses, c the
interconnection queue, d PUE, e behind the meter.

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/power_grid_zooms.py -- a

Writes assets/power_grid_zoom_<letter>.glb (and blender/power_grid_zoom_<letter>.blend).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label, beat  # noqa: E402
import power_grid_overview as ov  # noqa: E402
import power_grid_detail as D  # noqa: E402
from power_grid_detail import frame, camera_path, finish  # noqa: E402

PAGE = "power_grid"


def mid(path, f=0.5):
    return path[int(len(path) * f)]


def zooms(w):
    """letter -> three beats of (overview beat to replay, camera pose, [(tag, point)])."""
    p, g, s, h, gt = w["plant"], w["gsu"], w["sub"], w["hall"], w["gt"]
    T = D.TOWERS
    front = w["front"]
    q = lambda i: (D.GATE_X - 88.0 * (i + 1) + 40, 40.0, D.QZ)  # noqa: E731
    return {
        "a": [
            (0, frame((-1200.0, 150.0, -80.0), 620.0, 0.40, 0.28),
             [("generator, ~10-25 kV", p["gen"]), ("isolated-phase bus", mid(p["bus"][0], 0.6)),
              ("step-up transformer", g["bushing"]), ("turbine", p["turbine"])]),
            (1, frame((-280.0, 270.0, 20.0), 820.0, 0.50, 0.18),
             [("three phases, two circuits", (T[2], 350.0, -70.0)), ("115-345 kV conductors", mid(w["lines"][(1, "B")], 0.45)),
              ("lattice tower", (T[1] + 30, 160.0, 30.0))]),
            (3, frame((700.0, 140.0, 0.0), 400.0, 0.42, 0.30),
             [("the line lands on the gantry", (D.GX, 252.0, 118.0)), ("drops to the bus", mid(s["drops"][(1, "C")])),
              ("step-down transformer", s["sd"]["bushing"])]),
        ],
        "b": [
            (4, frame((1200.0, 80.0, -120.0), 540.0, 0.22, 0.38),
             [("a data hall", h["roof"]), ("racks draw the power", h["row"]), ("176 TWh in 2023: 4.4%", (1200.0, 190.0, -200.0))]),
            (0, frame((0.0, 300.0, -60.0), 1500.0, 0.55, 0.36),
             [("325-580 TWh by 2028", h["roof"]), ("6.7-12% of US power", (T[2], 400.0, 0.0))]),
            (4, frame((1100.0, 55.0, -40.0), 170.0, 0.35, 0.22),
             [("one rack: ~120 kW", h["rack"]), ("busway tap feeds it", (h["rack"][0], 100.0, D.ROWS[0])),
              ("campus: 100s of MW to 1+ GW", (1185.0, 40.0, D.ROWS[0] + 12))]),
        ],
        "c": [
            (5, frame((front[0] - 10, 40.0, front[2] - 20), 230.0, 0.30, 0.35),
             [("studied before it connects", (front[0], 82.0, front[2] + 50)), ("the gate to the grid", (D.GATE_X + 44, 60.0, 155.0))]),
            (5, frame((260.0, 60.0, 260.0), 900.0, 0.18, 0.38),
             [("~1,400 GW of plants waiting", q(5)), ("+890 GW of storage", q(1)), ("end of 2024 (LBNL)", q(3))]),
            (5, frame((800.0, 140.0, 330.0), 230.0, 0.10, 0.12),
             [("55 months, request to operation", (798.0, 210.0, 331.0)), ("one tile a month", (735.0, 192.0, 333.0))]),
        ],
        "d": [
            (6, frame((1080.0, 40.0, -80.0), 720.0, 0.30, 0.40),
             [("site power: everything drawn", s["meter"]), ("step-down transformer", s["sd"]["bushing"]), ("data hall", h["roof"])]),
            (6, frame((1150.0, 70.0, -60.0), 330.0, 0.25, 0.25),
             [("IT power: the racks", h["row"]), ("busways feed the rows", h["busway"])]),
            (6, frame((1200.0, 210.0, -160.0), 420.0, 0.25, 0.40),
             [("overhead: cooling + losses", h["units"]), ("heat off the roof", (h["fans"][4][0], 260.0, h["fans"][4][2])),
              ("PUE 1.2 = 20% extra", h["roof"])]),
        ],
        "e": [
            (1, frame((-280.0, 270.0, 20.0), 1000.0, 0.55, 0.22),
             [("new lines: years to build", (T[2], 400.0, 34.0)), ("the grid fills up", mid(w["lines"][(1, "A")], 0.5))]),
            (6, frame((1610.0, 70.0, -40.0), 300.0, 0.30, 0.25),
             [("gas turbine, on site", gt["turb"]), ("combustor", gt["comb"]), ("generator", gt["gen"]), ("compressor", gt["comp"])]),
            (6, frame((1300.0, 100.0, -60.0), 820.0, 0.35, 0.40),
             [("behind the meter", gt["stack"]), ("utility meter", s["meter"]), ("your own plant + fuel", gt["gas"])]),
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
    zoom's GLB carries only its own animation."""
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


def run(letter):
    ov.NAME = f"zoom_{letter}"
    ov.LABEL = lambda *a, **k: None
    ov.CAMERA = lambda *a, **k: None
    if letter == "e":
        ov.EXTRA = lambda m, root, w: ov.turbine_runs(m, root, w, 6)
    root = ov.build()
    plan = zooms(ov.W)[letter]
    replay([b for b, _, _ in plan])
    camera_path(root, [c for _, c, _ in plan])
    for k, (_, _, tags) in enumerate(plan):
        for text, pt in tags:
            label(text, pt, root, beat(k))
    finish(ov.NAME, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in "abcde":
        raise SystemExit("usage: blender -b --python power_grid_zooms.py -- <a|b|c|d|e>")
    run(argv[0])
