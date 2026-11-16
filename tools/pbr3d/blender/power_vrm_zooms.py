"""Zoom-ins (a-e) for the VRM page: the overview's board (power_vrm_detail.scene) with its own
camera, beads and tags, three beats each (diagrams_nodes/power/vrm/zooms.rs):

  a 50 V to 12 V              the busbar, the brick cut open, 12 V across the bare plane
  b multiphase                one phase, all sixteen firing in turn, their current together
  c why over a thousand amps  the GPU's watts, its 0.8 V core, the amps that makes
  d I2R loss                  current squared, 225 W in 0.1 milliohm, a shorter path
  e vertical power            beside the GPU, moving under it, straight up

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/power_vrm_zooms.py -- a

Writes assets/power_vrm_zoom_<letter>.glb (and blender/power_vrm_zoom_<letter>.blend).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import frame, camera_path, run, rise  # noqa: E402
import power_vrm_overview as OV  # noqa: E402

PAGE = "power_vrm"
BEATS = 3


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def zoom_a(m, root, s):
    br, bp = s["brick"], s["bpaths"]
    run(root, "a_bus", bp["p50"][:2], 6, 1.6, m["v50"], 0, 0.0, 0.8, 70)
    run(root, "a_ret", list(reversed(bp["ret"])), 4, 1.2, m["v50"], 0, 0.2, 0.8, 70)
    run(root, "a_p50", bp["p50"], 6, 1.5, m["v50"], 1, 0.0, 0.5, 90)
    run(root, "a_out", bp["out12"], 6, 1.4, m["v12"], 1, 0.35, 0.85, 50)
    run(root, "a_out2", bp["out12"], 4, 1.4, m["v12"], 2, 0.0, 0.4, 50)
    for k in range(3):
        run(root, f"a_p12_{k}", D.p12_path(k), 5, 1.3, m["v12"], 2, 0.1 + 0.05 * k, 0.85, 50)
    run(root, "a_front", D.front_path(-1)[:4], 5, 1.3, m["v12"], 2, 0.1, 0.85, 60)
    tags(root, [
        [("busbar: ~50 V DC", (D.BX0 - 40.0, 10.0, D.BUS_Z[0])), ("return bar", (D.BX0 - 20.0, 10.0, D.BUS_Z[1])),
         ("into the brick", (D.BRICK[0] + 2.0, 12.0, D.BUS_Z[0]))],
        [("primary switches", br["pfet"]), ("transformer: 50 V > 12 V", br["xf"]), ("rectifiers + caps: 12 V", br["sfet"])],
        [("12 V tab", br["tab"]), ("bare 12 V plane", (-190.0, D.Y_P12[1], -40.0)), ("12 V to every stage", (-160.0, D.Y_P12[1], -40.0))],
    ])
    camera_path(root, [
        frame((D.BX0 - 10.0, 8.0, -36.0), 90.0, 0.55, 0.38),
        frame((-256.0, 9.0, -10.0), 72.0, 0.12, 0.22),
        frame((-196.0, 0.0, -32.0), 120.0, 0.25, 0.70),
    ])


def zoom_b(m, root, s):
    fp = D.front_path(-1)
    run(root, "b_in", fp[:4], 6, 0.9, m["v12"], 0, 0.0, 0.85, 50)
    run(root, "b_sw", fp[3:8], 6, 0.9, m["amp"], 0, 0.05, 0.9, 50)
    D.blink(s["ph"]["sw"][(-1, 0)], 0, range(8), 8, 0.4)
    OV.interleave(m, root, s, [1], rounds=2)
    OV.currents(m, root, [2])
    show(s["die_glow"], span(2, 0.4, 3, 0.0))
    tags(root, [
        [("power stage: chops 12 V", (D.ST_X[0] + 7.0, D.ST_H, 0.0)), ("inductor: smooths it", (-94.0, D.IN_H, 0.0)),
         ("tens of amps each", (-92.0, 8.0, 0.0))],
        [("16 phases", s["ph"]["ind"][(1, 3)]["top"]), ("fired in turn", s["ph"]["st"][(-1, 4)]["top"]), ("controller", s["ctrl"]["ctrl"])],
        [("all phases together", s["ph"]["ind"][(-1, 2)]["top"]), ("1,000+ A into the GPU", s["pkg"]["die_face"])],
    ])
    camera_path(root, [
        frame((-104.0, 4.0, -4.0), 60.0, 0.30, 0.28),
        frame((0.0, 0.0, -105.0), 330.0, 0.0, 1.0, pad=1.0),
        frame((-40.0, 2.0, -20.0), 190.0, 0.22, 0.40),
    ])


def zoom_c(m, root, s):
    pk = s["pkg"]
    show(s["die_glow"], span(0, 0.2, 3, 0.0))
    rise(root, "c_heat", (0.0, D.DIE_Y[1] + 1.0, -16.0), 8, 1.0, m["heat"], 0, 0.05, 0.85, 36.0, 70, (14.0, 10.0))
    OV.currents(m, root, [2], n_front=12, big=1.5)
    for x in (-40.0, -24.0, -8.0, 8.0, 24.0, 40.0):
        run(root, f"c_v{x}", [(x, D.P08_Y, 1.0), (x, 2.0, 2.2), (x, 13.0, 1.0), (x, 17.5, 1.0), (x * 0.6, 20.5, 1.5)], 4, 1.0, m["amp"], [1, 2], 0.05, 0.85, 40)
    tags(root, [
        [("Blackwell-class GPU", pk["top"]), ("~1,000-1,200 W", (20.0, D.DIE_Y[1], -20.0)), ("HBM", pk["hbm"])],
        [("core voltage ~0.8 V", pk["die_face"]), ("through the bumps", pk["c4"]), ("substrate", pk["sub"])],
        [("1,250-1,500 A", pk["die_face"]), ("P = V x I", (30.0, D.DIE_Y[1], -10.0)), ("from both sides", (-66.0, 1.0, 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 14.0, -24.0), 120.0, 0.20, 0.60),
        frame((-16.0, 14.0, 0.0), 64.0, 0.18, 0.15),
        frame((0.0, 4.0, 0.0), 150.0, 0.12, 0.22),
    ])


def zoom_d(m, root, s):
    OV.currents(m, root, [0, 1], n_front=8)
    show(s["ph"]["heat"], span(0, 0.3, 1, 0.0))
    show(s["plane_hot"], beat(1))
    for side in (-1, 1):
        for k in (1, 4):
            rise(root, f"d_heat{side}{k}", s["ph"]["ind"][(side, k)]["top"], 2, 0.9, m["heat"], 0, 0.3, 0.85, 30.0, 60, (4.0, 4.0))
    rise(root, "d_plane", (-60.0, 0.5, 2.0), 6, 1.0, m["heat"], 1, 0.05, 0.85, 26.0, 60, (40.0, 0.0))
    D.present(s["vert"], beat(2))
    D.present(s["ph"]["group"], span(0, 0.0, 2, 0.0))
    for x in (-38.5, -14.0, 14.0, 38.5):
        run(root, f"d_v{x}", D.vert_path(x), 4, 1.3, m["amp"], 2, 0.1, 0.85, 50)
    tags(root, [
        [("loss = current squared x R", s["ph"]["ind"][(-1, 3)]["top"]), ("2x the amps, 4x the heat", s["ph"]["ind"][(1, 3)]["top"])],
        [("0.8 V plane: hot", (-80.0, D.P08_Y, 0.0)), ("0.1 mOhm at 1,500 A = 225 W", (10.0, D.P08_Y, 0.0))],
        [("regulators under the GPU", s["vpts"]["vm"]), ("path: millimetres", (-14.0, -8.0, 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 0.0, -95.0), 330.0, 0.10, 0.60, pad=1.0),
        frame((-30.0, -6.0, 0.0), 150.0, 0.15, 0.16),
        frame((0.0, -10.0, -6.0), 140.0, 0.35, 0.10),
    ])


def zoom_e(m, root, s):
    OV.currents(m, root, [0], n_front=10)
    lift = s["vpts"]["lift"]
    D.present(s["vert"], span(1, 0.0, 3, 0.0))
    key(lift, F(1, 0.0), "location", P(0.0, -70.0, 0.0), linear=True)
    key(lift, F(1, 0.15), "location", P(0.0, -70.0, 0.0), linear=True)
    key(lift, F(1, 0.75), "location", P(0.0, 0.0, 0.0), linear=True)
    D.present(s["ph"]["group"], span(0, 0.0, 1, 0.5))
    for x in (-38.5, -14.0, 14.0, 38.5):
        run(root, f"e_v{x}", D.vert_path(x), 6, 1.3, m["amp"], 2, 0.05, 0.85, 50)
    show(s["die_glow"], beat(2))
    tags(root, [
        [("lateral: beside the GPU", (-94.0, D.IN_H, 0.0)), ("current crosses the board", (-50.0, D.P08_Y, 0.0))],
        [("modules move under", (0.0, -40.0, 0.0)), ("onto the board's back", (40.0, D.BOT, -10.0))],
        [("vertical: straight up", (-14.0, -8.0, 0.0)), ("modules under the GPU", s["vpts"]["vm"]), ("GPU die", s["pkg"]["die_face"])],
    ])
    camera_path(root, [
        frame((-60.0, 0.0, 0.0), 130.0, 0.20, 0.22),
        frame((0.0, -24.0, -6.0), 150.0, 0.35, 0.05),
        frame((0.0, -10.0, -6.0), 140.0, 0.35, 0.10),
    ])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    ZOOMS[letter](m, root, s)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python power_vrm_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
