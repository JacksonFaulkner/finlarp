"""The INTERPOSER overview (PACKAGING tab), on the POWER-page pattern: one CoWoS package cut open
along its front face (pkg_interposer_detail.py), seven beats of 8 s
(tui/src/screens/diagrams_nodes/packaging/interposer/overview.rs):

  0 the interposer: wiring under the dies   the whole cut-away: board, substrate, C4, interposer, die, HBM
  1 data runs across it                     cyan beads leave each HBM base die, cross the BEOL, rise into the die
  2 power climbs up through TSVs            yellow beads from the board up PTHs, C4s and TSVs into the die
  3 layer by layer                          close on the stack: BEOL, silicon + TSVs, C4, substrate build-up
  4 CoWoS-L: silicon bridges                the package swaps to an organic interposer with LSI bridges, two dies
  5 growing past the reticle                top-down: 1 reticle, CoWoS-S 3.3x, 2027's 9.5x with 12 stacks
  6 the lidded package on its board         TIM and lid drop on, the die heats, heat climbs out of the lid

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_interposer_overview.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_interposer_detail as D  # noqa: E402
from pkg_interposer_detail import frame, camera_path, run, rise, present, empty  # noqa: E402

PAGE = "pkg_interposer"
NAME = "overview"
BEATS = 7
TOP = (0.0, 400.0, 0.0)  # the top-down reticle plane


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def both(m, root):
    """A silicon (S) and an organic-bridge (L) package in the same place, each in its own group."""
    gs = empty("pkg_S", root)
    s = D.scene(m, gs, "S")
    gl = empty("pkg_L", root)
    l_ = D.scene(m, gl, "L")
    return gs, s, gl, l_


def data(m, root, beats, n=5, u0=0.0, u1=0.8, bridge=False):
    for side in (-1, 1):
        for k in range(3):
            p = D.bridge_path(side, k) if bridge else D.data_path(side, k)
            run(root, f"dat_{beats}_{side}_{k}_{int(bridge)}", p, n, 0.45, m["ip_data"], beats, u0 + 0.04 * k, u1, 50)


def power(m, root, beats, xs=(-12.0, -6.0, 0.0, 6.0, 12.0), n=4, u0=0.0, u1=0.8):
    for x in xs:
        run(root, f"pwr_{beats}_{x}", D.power_path(x), n, 0.5, m["ip_power"], beats, u0, u1, 70)


def tops(m, root):
    """Three top-down packages at TOP, all to one scale: 1 reticle, CoWoS-S 3.3x, 9.5x."""
    g = empty("tops", root)
    cx, cy, cz = TOP
    D.reticle_plane(m, g, (cx - 260.0, cy, cz), 1, 1, "ret1")
    D.topdown_package(m, g, (cx - 260.0, cy + 1.2, cz), 0.1, 0.1, 1, 0, "ret1pk")
    D.reticle_plane(m, g, (cx - 140.0, cy, cz), 2, 2, "ret33", frac=3.3 / 4.0)
    D.topdown_package(m, g, (cx - 140.0, cy + 1.2, cz), 46.0, 60.0, 1, 4, "s33")
    D.reticle_plane(m, g, (cx + 90.0, cy, cz), 4, 3, "ret95", frac=9.5 / 12.0)
    D.topdown_package(m, g, (cx + 90.0, cy + 1.2, cz), 92.0, 85.0, 2, 12, "l95", organic=True)
    return g


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    gs, s, gl, l_ = both(m, root)
    present(gs, [(0, F(4, 0)), (F(6, 0), F(7, 0))])
    present(gl, span(4, 0, 5, 0))
    tg = tops(m, root)
    present(tg, beat(5))

    data(m, root, 1)
    power(m, root, 2)
    data(m, root, 4, n=4, bridge=True)
    power(m, root, 0, xs=(-6.0, 6.0), n=2, u0=0.3)
    data(m, root, 0, n=2, u0=0.3)

    # beat 6: lid drops on, die heats, heat climbs out
    lift = s["lid"]
    present(lift, beat(6))
    for gl_ in s["glow"]:
        present(gl_, span(6, 0.3, 7, 0))
    rise(root, "heat6", (0.0, D.LID[1] + 0.5, -4.0), 10, 0.5, m["ip_heat"], 6, 0.3, 0.9, 20.0, 60, (14.0, 3.0))
    power(m, root, 6, xs=(-6.0, 0.0, 6.0), n=3, u0=0.05, u1=0.6)

    p = s["pts"]
    tags(root, [
        [("silicon interposer", p["beol"]), ("GPU die", p["die"]), ("HBM stack", p["hbm"]), ("substrate", p["sub_top"]),
         ("board", p["board"])],
        [("out of the HBM base die", (D.HBM_X[0] + 2.0, D.HBM_Y[0], D.FZ)), ("across fine copper wiring", (D.DIE_X + 1.5, D.M_Y[1], D.FZ)),
         ("up into the GPU", (D.DIE_X - 2.0, D.DIE[0] + 0.4, D.FZ))],
        [("through the BGA and core", (6.0, D.CORE[1], D.FZ)), ("C4 bump", p["c4"]), ("TSV through the silicon", p["tsv"])],
        [("BEOL: 4 copper levels", p["m1"]), ("silicon + TSVs", p["si"]), ("C4 bumps", p["c4"]), ("ABF build-up", p["abf"]),
         ("glass-fibre core", p["core"])],
        [("CoWoS-L: organic interposer", (-34.0, 2.0, 0.0)), ("LSI bridge under the seam", (15.5, 1.1, 0.0)),
         ("two GPU dies", (0.0, D.DIE[1], 0.0)), ("copper TIVs", (-30.6, 0.0, 0.0))],
        [("one reticle: 26 x 33 mm", (TOP[0] - 260.0, TOP[1] + 1.0, TOP[2] - 16.5)), ("CoWoS-S: ~3.3x", (TOP[0] - 140.0, TOP[1] + 4.0, TOP[2] - 30.0)),
         ("2027: ~9.5x, 12 HBM", (TOP[0] + 90.0, TOP[1] + 4.0, TOP[2] - 42.0))],
        [("TIM", p["tim"]), ("lid", p["lid"]), ("heat out the top", (0.0, D.LID[1] + 12.0, -4.0)), ("BGA onto the board", p["bga"])],
    ])
    camera_path(root, [
        frame((0.0, -3.0, -4.0), 125.0, 0.32, 0.30),
        frame((15.0, 3.5, 0.0), 30.0, 0.10, 0.22, min_d=30.0),
        [(0.0, frame((-2.0, -6.0, 0.0), 55.0, 0.18, 0.10, min_d=40.0)), (0.5, frame((-6.0, 0.0, 0.0), 40.0, -0.10, 0.08, min_d=40.0))],
        frame((-30.0, -4.0, 0.0), 50.0, 0.22, 0.10, min_d=40.0),
        frame((0.0, 2.0, -2.0), 80.0, 0.20, 0.22),
        frame((TOP[0] - 70.0, TOP[1], TOP[2]), 420.0, 0.0, 1.2, pad=1.0),
        frame((0.0, -2.0, -6.0), 130.0, 0.38, 0.32),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
