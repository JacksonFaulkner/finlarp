"""The SUBSTRATE page's overview (PACKAGING tab), in the picture-and-panel template.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_substrate_overview.py

Writes blender/pkg_substrate_overview.blend and assets/pkg_substrate_overview.glb. One beat is 8 s.
The scene is pkg_substrate_detail.scene: an FC-BGA substrate cut open along its front edge.

Beats (match diagrams_nodes/packaging/substrate/overview.rs):
  0 the substrate      the whole cut-open stack: board, BGA, substrate, C4, interposer, die, HBM
  1 C4 on top          the fine-pitch bump field in its resist openings, under the interposer
  2 inside the laminate core with PTH barrels, ABF films, copper planes, signal traces, microvias
  3 BGA below          coarse balls to the board; capacitors between them on the underside
  4 power              yellow beads up from the balls, through PTHs, across the lit planes, into C4
  5 signals fan out    cyan beads from C4 down microvias, across a layer, down a PTH, to a ball
  6 warpage            the laminate alone, bowing as it heats in reflow and cools
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_substrate_detail as D  # noqa: E402
from pkg_substrate_detail import frame, camera_path, run, rise, present  # noqa: E402

PAGE = "pkg_substrate"
NAME = "overview"
BEATS = 7


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat, offset=0):
    for i, items in per_beat.items() if isinstance(per_beat, dict) else enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i + offset))


def power_beads(m, root, beats, n=5, u0=0.0, u1=0.8, size=1.3, tag="pw"):
    for s in (1, -1):
        run(root, f"{tag}{s}a", D.power_path(0.0, s * 8.0), n, size, m["pwr"], beats, u0, u1, 90)
        run(root, f"{tag}{s}b", D.power_path(s * 16.0, s * 24.0), n, size, m["pwr"], beats, u0 + 0.05, u1, 90)


def signal_beads(m, root, s, beats, n=4, u0=0.0, u1=0.8, size=1.1, tag="sg", reverse=False):
    for i, p in s["sub"]["paths"].items():
        pts = list(reversed(p)) if reverse else p
        run(root, f"{tag}{i}", pts, n, size, m["sig"], beats, u0 + 0.02 * (i % 4), u1, 80)


def warp_scene(m, root, beats_on, keys, name="warp"):
    g, piv = D.warp(m, root, name)
    present(g, [iv for b in beats_on for iv in beat(b)])
    D.bend(piv, keys)
    return g, piv


def hide_main(s, intervals):
    """Present the main stack (everything but the board) only during `intervals`."""
    for k in ("bga", "caps", "c4", "lit_planes"):
        present(s[k], intervals)
    present(s["sub"]["group"], intervals)
    if "pkg" in s:
        present(s["pkg"]["group"], intervals)


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    hide_main(s, span(0, 0.0, 6, 0.0))
    show(s["lit_planes"], beat(4))
    show(s["sub"]["lit"], beat(5))

    power_beads(m, root, [4])
    signal_beads(m, root, s, [5])
    rise(root, "heat_die", (0.0, D.DIE_Y[1] + 1.0, -30.0), 5, 1.4, m["heat"], 4, 0.3, 0.9, 40.0, 70, (24.0, 20.0))

    # beat 6: the laminate alone, heated (ends down, cry) then cooled past flat (ends up, smile)
    _, piv = warp_scene(m, root, [6], [(F(6, 0.0), 0.0), (F(6, 0.1), 0.0), (F(6, 0.45), -0.18),
                                       (F(6, 0.55), -0.18), (F(6, 0.9), 0.14), (F(6, 1.0) - 1, 0.14)])
    rise(root, "reflow", (0.0, D.TOP + 2.0, -30.0), 8, 1.3, m["heat"], 6, 0.05, 0.45, 40.0, 60, (110.0, 20.0))

    tags(root, {
        0: [("package substrate", D.A_TOPBU), ("interposer + GPU die", D.A_DIE), ("server board", (-180.0, D.BOARD_TOP, 0.0))],
        1: [("C4 bumps: ~150 um pitch", D.A_C4), ("solder resist", D.A_SR), ("underfill", (-60.0, D.TOP + 3.0, 0.0))],
        2: [("CORE + plated through-holes", D.A_PTH), ("BUILD-UP: ABF film + copper", D.A_TOPBU),
            ("microvias", (-56.0, D.mid((D.CORE1, D.TOP)), 0.0)), ("ground / power planes", D.A_PLANE)],
        3: [("BGA balls: ~1 mm pitch", D.A_BGA), ("land-side capacitors", D.A_CAP), ("board pads", (-48.0, D.BOARD_TOP, 0.0))],
        4: [("power up through the core", (16.0, D.CORE0 + 6.0, 0.0)), ("planes spread it", D.A_PLANE), ("into the die", D.A_DIE)],
        5: [("FAN-OUT: fine bumps", (48.0, D.C4_Y, 0.0)), ("across a signal layer", (96.0, D.mid(D.cu_y(1, 4)), 0.0)),
            ("out to the board pitch", (120.0, D.BGA_Y, 0.0))],
        6: [("WARPAGE in reflow", (0.0, D.TOP + 4.0, 0.0)), ("ends bend, bumps strain", (130.0, D.TOP, 0.0))],
    })

    camera_path(root, [
        D.V_ALL,
        D.V_C4,
        D.V_FACE,
        D.V_BGA,
        frame((0.0, 30.0, 0.0), 160.0, 0.10, 0.18),
        D.V_FACE_R,
        frame((0.0, 20.0, -40.0), 330.0, 0.15, 0.12, pad=1.0),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
