"""Zoom-ins (a-e) for the UPS page, built from the overview's own scene (power_ups_overview.py).

A zoom replays beats of the overview under its own camera: zoom beat k plays overview beat
REPLAY[k] in full (beads keep riding the cables, pistons keep moving), with its own pose and its own
tags. Overview beat 7 is the hidden ECO-mode beat. Subjects (keys and labels as the old rig's UPS
zooms in diagrams_pwr_nodes.rs):

  a inside a UPS                  rectifier, DC link and batteries, inverter
  b a power cut, second by second 0 s utility lost, ~10 s generator up, the transfer
  c batteries and runtime         Li-ion cabinets, minutes of runtime, recharge
  d generators                    a diesel and an alternator, start in ten seconds, fuel on site
  e efficiency                    two conversions, 3-5% lost as heat, eco mode (static bypass)

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/power_ups_zooms.py -- a

Writes assets/power_ups_zoom_<letter>.glb (and blender/power_ups_zoom_<letter>.blend).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, label, beat  # noqa: E402
from sand_zooms import finish  # noqa: E402
import power_ups_overview as ov  # noqa: E402
import power_ups_detail as D  # noqa: E402
from power_ups_detail import frame, camera_path  # noqa: E402

PAGE = "power_ups"
G = D.GX0

# letter -> three beats of (overview beat to replay, camera pose, [(tag, point)]); points are
# looked up in the built scene by the functions below, so they follow the plant's layout.
def plan(S):
    at, gp, rc, dl, iv, ss, bt, rk, C = S["ats"], S["gen"], S["rect"], S["dcl"], S["inv"], S["ss"], S["bats"], S["racks"], S["C"]
    return {
        "a": [
            (0, frame((-720.0, 110.0, -30.0), 210.0, 0.30, 0.16),
             [("input inductor", rc["ind"]), ("IGBT bridge on its heatsink", rc["mod"]), ("AC in from the switch", rc["in"]),
              ("DC out", rc["out"])]),
            (1, frame((-470.0, 140.0, -30.0), 420.0, 0.30, 0.20),
             [("DC link capacitors", dl["cap"]), ("DC to the batteries", C["dc_batt"][7]), ("Li-ion cabinets charging", bt[0]["mod"])]),
            (0, frame((-520.0, 110.0, -30.0), 210.0, 0.30, 0.16),
             [("IGBT bridge: DC to AC", iv["mod"]), ("output filter", iv["ind"]), ("clean AC to the racks", iv["out"])]),
        ],
        "b": [
            (2, frame((-640.0, 230.0, -60.0), 760.0, 0.28, 0.26),
             [("0 s: utility lost", C["util_drop"][5]), ("batteries take over", C["dc_batt"][7]), ("inverter never stops", iv["top"])]),
            (4, frame((G + 290.0, 180.0, 0.0), 620.0, 0.26, 0.20),
             [("engine cranks and fires", gp["piston"]), ("~10 s: at voltage and speed", gp["alt"]), ("exhaust", gp["stack"])]),
            (5, frame((-1160.0, 200.0, -20.0), 1080.0, 0.26, 0.24, pad=0.95),
             [("transfer: blade to generator", at["top"]), ("generator carries the load", C["gen_out"][7]),
              ("UPS input back", rc["top"])]),
        ],
        "c": [
            (1, frame((-242.0, 120.0, -20.0), 330.0, 0.32, 0.18),
             [("Li-ion cabinets", bt[1]["top"]), ("modules of prismatic cells", bt[0]["mod"]), ("charge LEDs", bt[2]["mod"])]),
            (3, frame((-242.0, 120.0, -20.0), 330.0, 0.32, 0.18),
             [("draining: minutes, not hours", bt[1]["mod"]), ("battery DC out", C["dc_batt"][8])]),
            (5, frame((-400.0, 150.0, -30.0), 480.0, 0.30, 0.20),
             [("recharging on generator power", bt[1]["mod"]), ("DC from the rectifier", C["dc_batt"][7]),
              ("DC link", dl["top"])]),
        ],
        "d": [
            (0, frame((G + 290.0, 170.0, 0.0), 600.0, 0.24, 0.16),
             [("diesel engine", gp["engine"]), ("alternator", gp["alt"]), ("radiator", gp["radiator"]),
              ("about 2-3 MW per set", gp["panel"])]),
            (4, frame((G + 200.0, 140.0, 0.0), 360.0, 0.26, 0.18),
             [("pistons and crankshaft", gp["piston"]), ("crank turning", gp["crank_pt"]), ("turbo and exhaust", gp["turbo"])]),
            (5, frame((G + 280.0, 90.0, 0.0), 600.0, 0.22, 0.14),
             [("belly fuel tank, cut open", gp["tank"]), ("diesel fuel", (gp["tank"][0] + 140, 30.0, 0.0)),
              ("running", gp["alt"])]),
        ],
        "e": [
            (0, frame((-620.0, 115.0, -30.0), 380.0, 0.26, 0.16),
             [("conversion 1: rectifier", rc["top"]), ("conversion 2: inverter", iv["top"]), ("every watt, twice", dl["top"])]),
            (6, frame((-620.0, 125.0, -30.0), 380.0, 0.26, 0.16),
             [("3-5% lost as heat", rc["heat"][1]), ("heatsinks", iv["hs"]), ("that heat must be cooled", iv["heat"][1])]),
            (7, frame((-620.0, 220.0, -60.0), 560.0, 0.24, 0.24),
             [("eco: static bypass closed", ss["scr"]), ("utility straight to the racks", C["bypass"][9]),
              ("rectifier and inverter idle", rc["top"])]),
        ],
    }


def replay(sources):
    """Zoom beat k plays overview beat sources[k]: every animated channel is resampled frame by frame."""
    n = len(sources)
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in list(cb.fcurves):
            const = any(kp.interpolation == "CONSTANT" for kp in fc.keyframe_points)
            co = []
            for k, b in enumerate(sources):
                for f in range(BEAT_FRAMES):
                    co += [k * BEAT_FRAMES + f, fc.evaluate(F(b, 0) + f)]
            co += [n * BEAT_FRAMES, fc.evaluate(F(sources[-1], 0) + BEAT_FRAMES - 1)]
            kps = fc.keyframe_points
            while len(kps):
                kps.remove(kps[0], fast=True)
            kps.add(len(co) // 2)
            kps.foreach_set("co", co)
            for kp in kps:
                kp.interpolation = "CONSTANT" if const else "LINEAR"
            fc.update()
    sc = bpy.context.scene
    sc.frame_start = 0
    sc.frame_end = BEAT_FRAMES * n
    sc.frame_set(0)


def run(letter):
    ov.NAME = f"zoom_{letter}"
    ov.LABEL = lambda *a, **k: None
    ov.CAMERA = lambda *a, **k: None
    root, S = ov.build()
    beats = plan(S)[letter]
    replay([b[0] for b in beats])
    camera_path(root, [b[1] for b in beats])
    for k, (_, _, tags) in enumerate(beats):
        for text, p in tags:
            label(text, p, root, beat(k))
    finish(ov.NAME, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in "abcde":
        raise SystemExit("usage: blender -b --python power_ups_zooms.py -- <a|b|c|d|e>")
    run(argv[0])
