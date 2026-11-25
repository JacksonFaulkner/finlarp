"""The LOGIC DIE page's overview (PACKAGING tab), in the picture-and-panel template.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_logic_die_overview.py

Writes blender/pkg_logic_die_overview.blend and assets/pkg_logic_die_overview.glb. One beat is 8 s.

A CoWoS-style GPU package cut open along its front edge (pkg_logic_die_detail.py): two flip-chip
logic dies on a silicon interposer with a bridge between them, HBM stacks on the long edges,
microbumps, C4 bumps, an ABF substrate, BGA balls and the board; TIM and a lid on top.

Beats (match diagrams_nodes/packaging/logic_die/overview.rs):
  0 package       the whole package, cut open, lid on
  1 inside a die  close on the cut face: bulk silicon, transistors, metal stack facing down
  2 reticle       lid off; a pink 26 x 33 mm field fits round one die
  3 HBM shoreline cyan data from each die's edge through the RDL into the HBM
  4 two dies      green die-to-die traffic across the bridge
  5 power         yellow current from the board up through the whole stack into the dies
  6 heat          the dies glow; heat climbs through the TIM and the lid
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_logic_die_detail as D  # noqa: E402
from pkg_logic_die_detail import frame, camera_path, run, rise, bx, empty, present  # noqa: E402

PAGE = "pkg_logic_die"
NAME = "overview"
BEATS = 7

V_ALL = frame((0.0, 0.0, -16.0), 105.0, 0.35, 0.34, pad=1.0)
V_CUT = frame((-20.0, 3.5, 0.0), 34.0, 0.18, 0.10, min_d=20.0)
V_TOP = frame((0.0, 8.0, -16.0), 82.0, 0.10, 1.05)
V_HBM = frame((-26.0, 4.0, -2.0), 34.0, 0.30, 0.22, min_d=20.0)
V_BRIDGE = frame((0.0, 3.5, 0.0), 22.0, 0.10, 0.18, min_d=16.0)
V_STACK = frame((-4.0, -1.0, 0.0), 52.0, 0.12, 0.08)
V_HEAT = frame((0.0, 8.0, -12.0), 75.0, 0.25, 0.28)


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def reticle(m, root, intervals):
    g = empty("reticle", root)
    x0, x1 = 0.6, 26.6
    z0, z1 = -33.0, 0.0
    y = D.DIE[1] + 0.1
    for n, lo, hi in (("l", (x0 - 0.4, y, z0), (x0, y + 0.4, z1)), ("r", (x1, y, z0), (x1 + 0.4, y + 0.4, z1)),
                      ("b", (x0, y, z0 - 0.4), (x1, y + 0.4, z0)), ("f", (x0, y, z1 - 0.4), (x1, y + 0.4, z1))):
        bx(f"ret_{n}", lo, hi, m["reticle"], g)
    show(g, intervals)
    return g


def data(m, root, beats, n=5):
    for side in (-1, 1):
        run(root, f"data{side}", D.data_path(side), n, 0.5, m["data"], beats, 0.0, 0.8, 60)
        run(root, f"datab{side}", list(reversed(D.data_path(side))), n - 2, 0.5, m["data"], beats, 0.1, 0.85, 60)


def d2d(m, root, beats, n=6):
    run(root, "d2d_r", D.d2d_path(1), n, 0.5, m["d2d"], beats, 0.0, 0.85, 50)
    run(root, "d2d_l", D.d2d_path(-1), n, 0.5, m["d2d"], beats, 0.05, 0.9, 50)


def power(m, root, beats, xs=(-18.0, -8.0, 9.0, 19.0), n=4):
    for x in xs:
        run(root, f"pw{x}", D.power_path(x), n, 0.7, m["power"], beats, 0.0, 0.8, 70)


def heat(m, root, beats, n=6):
    for i in range(2):
        rise(root, f"heat{i}", D.heat_base(i), n, 1.3, m["heat"], beats, 0.05, 0.85, 22.0, 60, (9.0, 7.0))


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.package(m, root, floorplan=True)
    present(s["lid"], beat(0) + beat(1) + beat(6))

    reticle(m, root, beat(2))
    data(m, root, [3])
    d2d(m, root, [4])
    power(m, root, [5])
    for g in s["hot"]:
        show(g, span(6, 0.1, 7, 0.0))
    heat(m, root, [6])

    tags = {
        0: [("logic dies (2)", (-14.0, D.LID[1], -6.0)), ("HBM stacks", (-32.0, D.HBM_Y[1], -1.0)),
            ("interposer", (-40.0, D.IP[1], 0.0)), ("ABF substrate", (-50.0, D.SUB[1] - 1.0, 0.0)), ("board", (-70.0, D.BOARD[1], 0.0))],
        1: [("bulk silicon", (-20.0, 6.8, 0.0)), ("transistors", (-10.0, D.DEV[0] + 0.15, 0.0)),
            ("metal stack, face down", (-24.0, 4.2, 0.0)), ("microbumps", (-16.0, D.UB[0] + 0.3, -0.4))],
        2: [("26 x 33 mm field", (26.6, D.DIE[1] + 0.4, -16.0)), ("858 mm2 limit", (14.0, D.DIE[1] + 0.4, -33.0)),
            ("SM tiles + L2", (-14.0, D.DIE[1], -10.0))],
        3: [("HBM PHY at the edge", (-25.0, D.DEV[0], 0.0)), ("RDL wires", (-28.0, D.IP[1] - 0.3, 0.0)),
            ("HBM stack", (-33.0, D.HBM_Y[1], -2.0))],
        4: [("bridge in the interposer", (0.0, D.IP_SI[0] + 0.6, 0.0)), ("die-to-die link", (0.0, D.UB[1], 0.0)),
            ("~10 TB/s (B200)", (6.0, D.DIE[1], -2.0))],
        5: [("BGA", (-18.0, D.BGA_Y, 0.4)), ("core through-hole", (-8.0, -2.7, -1.0)), ("C4 + TSV", (9.0, 1.4, 0.0)),
            ("into the die", (19.0, D.DEV[1], 0.0))],
        6: [("~1,000 W per package", (-13.0, D.DIE[1], -6.0)), ("TIM", (13.0, D.TIM[1], 0.0)), ("lid: heat out the top", (0.0, D.LID[1], -8.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera_path(root, [V_ALL, V_CUT, V_TOP, V_HBM, V_BRIDGE, V_STACK, V_HEAT])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
