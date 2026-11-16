"""The VRM page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/power_vrm_overview.py

Writes blender/power_vrm_overview.blend and assets/power_vrm_overview.glb. One beat is 8 s.

A GPU board cut open along its front edge (power_vrm_detail.py): the GPU package in the middle,
eight phases (power stage + inductor) down each side, the controller behind, the 50 V to 12 V
brick at the left edge with its busbar, and the 12 V plane laid bare between them.

Beats (match the seven beats in diagrams_nodes/power/vrm/overview.rs):
  0 board      the whole board: GPU, phases, brick
  1 50 V in    yellow beads ride the busbar into the brick; amber 12 V leaves into the bare plane
  2 12 V out   12 V crosses the plane; the controller's PWM pulses run to each stage in turn
  3 0.8 V      red current leaves the inductors, crosses the 0.8 V plane and climbs into the die
  4 I2R        the phases and die glow hot; heat rises
  5 vertical   the side phases go; modules under the package push current straight up
  6 grid       the whole board running: every path at once
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import frame, camera_path, run, rise, PHASE_Z  # noqa: E402

PAGE = "power_vrm"
NAME = "overview"
BEATS = 7


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def interleave(m, root, s, beats, u0=0.05, u1=0.95, rounds=2, sides=(-1, 1)):
    """PWM pulses from the controller to each stage in turn, and each stage's switch node lighting
    as its pulse lands: the phases fire one after another, never all at once. One bead per trace
    does every round in every beat."""
    order = [(side, k) for k in range(8) for side in sides]
    n = len(order)
    slot = (u1 - u0) / (rounds * n)
    for i, (side, k) in enumerate(order):
        tr = s["traces"][(side, k)]
        g = D.empty(f"pwm_{side}_{k}_g", root)
        e = D.empty(f"pwm_{side}_{k}_e", g)
        D.bead(f"pwm_{side}_{k}_s", tr[0], 1.6, m["pwm"], e)
        path = [tuple(p[j] - tr[0][j] for j in range(3)) for p in tr]
        iv, sw = [], []
        for b in beats:
            for r in range(rounds):
                u = u0 + slot * (r * n + i)
                f0 = F(b, u)
                D.fly(e, path, f0, f0 + 26, steps=6)
                iv.append((f0, f0 + 26))
                sw.append((f0 + 24, min(F(b, u + slot * 3) + 24, F(b + 1, 0))))
        show(e, iv)
        show(s["ph"]["sw"][(side, k)], sw)


def currents(m, root, beats, n_front=8, u0=0.0, u1=0.8, big=1.4):
    """0.8 V current: along both cut-face paths into the die, and across the top pours from the
    inductors toward the package."""
    for side in (-1, 1):
        run(root, f"amp_f{side}", D.front_path(side), n_front, big, m["amp"], beats, u0, u1, 110)
        for k in range(1, 8):
            run(root, f"amp_p{side}{k}", D.pour_path(side, k), 2, 1.2, m["amp"], beats, u0 + 0.02 * k, u1, 40)


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    br, bp = s["brick"], s["bpaths"]

    # beats 1 and 6: 50 V along the busbar into the brick; 12 V out onto the bare plane
    run(root, "v50", bp["p50"], 7, 1.6, m["v50"], [1, 6], 0.0, 0.55, 90)
    run(root, "v12_out", bp["out12"], 6, 1.4, m["v12"], [1, 6], 0.3, 0.85, 50)
    for k in range(3):
        run(root, f"v12_{k}", D.p12_path(k), 5, 1.3, m["v12"], [1, 2, 6], 0.15 + 0.04 * k, 0.85, 50)
    # beat 2: 12 V to every stage; the controller fires them in turn
    run(root, "v12_f", D.front_path(-1)[:4], 5, 1.3, m["v12"], [2, 6], 0.0, 0.85, 60)
    interleave(m, root, s, [2, 3, 6])
    # beats 3, 4, 6: 0.8 V current into the die
    currents(m, root, [3, 4, 6])
    show(s["die_glow"], span(3, 0.45, 5, 0.0) + span(5, 0.5, 7, 0.0))
    # beat 4: heat
    show(s["ph"]["heat"], beat(4))
    for side in (-1, 1):
        for k in (0, 3, 6):
            ip = s["ph"]["ind"][(side, k)]
            rise(root, f"heat_i{side}{k}", ip["top"], 2, 0.9, m["heat"], 4, 0.05 + 0.03 * k, 0.8, 34.0, 70, (4.0, 4.0))
    rise(root, "heat_die", (0.0, D.DIE_Y[1] + 1.0, -16.0), 5, 1.1, m["heat"], 4, 0.05, 0.85, 40.0, 70, (14.0, 10.0))
    # beat 5: vertical power
    D.present(s["ph"]["group"], span(0, 0.0, 5, 0.0) + span(6, 0.0, 7, 0.0))
    D.present(s["vert"], beat(5))
    for x in (-38.5, -14.0, 14.0, 38.5):
        run(root, f"vert{x}", D.vert_path(x), 4, 1.3, m["amp"], 5, 0.1, 0.85, 50)

    pk, ph, ctl = s["pkg"], s["ph"], s["ctrl"]
    st0, in0 = ph["st"][(-1, 0)], ph["ind"][(-1, 0)]
    tags = {
        0: [("GPU package", pk["top"]), ("VRM phases, 8 a side", ph["ind"][(-1, 3)]["top"]),
            ("50 V > 12 V brick", br["brick"]), ("controller", ctl["ctrl"])],
        1: [("busbar: ~50 V DC", br["bus"]), ("bus converter, cut open", br["xf"]), ("12 V out", br["tab"])],
        2: [("bare 12 V plane", (-190.0, D.Y_P12[1], -40.0)), ("controller fires each phase", ctl["ctrl"]),
            ("PWM traces", (-D.TR_X - 4.0, 0.4, -120.0)), ("power stage switches", ph["st"][(-1, 1)]["top"])],
        3: [("inductors: ~0.8 V out", in0["top"]), ("0.8 V plane", (-50.0, D.P08_Y, 0.0)),
            ("1,000+ A into the GPU", pk["die_face"])],
        4: [("I2R: heat in every phase", ph["ind"][(-1, 2)]["top"]), ("0.1 mOhm at 1,500 A = 225 W", (-50.0, D.P08_Y, 0.0)),
            ("GPU: ~1,000-1,200 W", pk["top"])],
        5: [("modules under the GPU", s["vpts"]["vm"]), ("straight up, millimetres", (-14.0, -8.0, 0.0)),
            ("GPU die", pk["die_face"])],
        6: [("~50 V in", br["bus"]), ("12 V", (-190.0, D.Y_P12[1], -40.0)), ("~0.8 V at the die", pk["top"])],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera_path(root, [
        frame((-40.0, 0.0, -95.0), 420.0, 0.25, 0.62, pad=1.0),
        frame((-250.0, 4.0, -30.0), 130.0, 0.35, 0.40),
        frame((-150.0, 0.0, -95.0), 230.0, 0.25, 0.75, pad=1.0),
        frame((-60.0, 0.0, 0.0), 150.0, 0.18, 0.24),
        frame((0.0, 0.0, -95.0), 330.0, 0.10, 0.55, pad=1.0),
        frame((0.0, -10.0, -6.0), 140.0, 0.35, 0.10),
        frame((-40.0, 0.0, -100.0), 470.0, 0.20, 0.55, pad=1.0),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
