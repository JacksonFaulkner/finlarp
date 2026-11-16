"""The ASSEMBLY overview (PACKAGING tab), in the SAND template (docs/diagram-pages.md).

Run from the repo root (on the worker, or locally):

    blender -b --factory-startup --python tools/pbr3d/blender/assembly_overview.py

Writes blender/assembly_overview.blend and assets/assembly_overview.glb. One beat is 8 s.

Beats (match ASSEMBLY in diagrams_pkg_nodes.rs, A_B):
  0 known-good dies arrive          bare dies and HBM stacks on a tray
  1 chip on wafer                   dies land on interposers still on the wafer
  2 HBM stacks join                 stacks appear on every interposer
  3 cut apart, then on substrate    the rest of the wafer goes; the cut-out interposer is lowered onto a substrate
  4 underfill flow                  dark underfill flows in from the front and fills the gap round the die
  5 lid goes on                     the lid drops onto the package
  6 capacity is the bottleneck      finished packages in a row
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, disc, key, label, beat, show  # noqa: E402
from sand_zooms import start, camera, finish  # noqa: E402
from pbr_kit import empty  # noqa: E402
import pkg_kit as K  # noqa: E402

PAGE = "assembly"
NAME = "overview"
BEATS = 7

POSES = [
    ((-5.0, 2.0, 0.0), 190.0, 0.50, 0.45),
    ((0.0, 0.0, 0.0), 300.0, 0.50, 0.45),
    ((0.0, 2.0, 0.0), 260.0, 0.60, 0.40),
    ((0.0, 6.0, 0.0), 150.0, 0.50, 0.25),
    ((0.0, 3.0, 0.0), 90.0, 0.40, 0.35),
    ((0.0, 5.0, 0.0), 110.0, 0.60, 0.30),
    ((0.0, 0.0, 0.0), 310.0, 0.50, 0.35),
]

WAFER_X = (-70.0, 70.0)  # the two interposers that stay on the wafer
DROP = 30.0  # mm above rest where a die or package starts its fall
LIFT = 10.0  # mm above rest the cut-out package is lifted to before it is set on the substrate
RIM_IN = 8.0  # mm in front of rest where the underfill starts, flowing in from the front edge
LID_DROP = 12.0  # mm above rest where the lid starts its fall onto the HBM stacks


def from_beat(k):
    return [(F(k, 0), F(BEATS, 0))]


def between(a, b):
    return [(F(a, 0), F(b, 0))]


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = K.materials()

    # Beat 0: bare known-good dies on a tray.
    tray = empty("tray_grp", root)
    show(tray, between(0, 1))
    box("tray", (-60.0, -1.0, -40.0), (60.0, 0.0, 40.0), m["substrate"], tray)
    for i in range(6):
        x = -40.0 + 16.0 * (i % 3)
        z = -12.0 + 24.0 * (i // 3)
        box(f"bare_die_{i}", (x - 6.0, 0.0, z - 6.0), (x + 6.0, 1.5, z + 6.0), m["die"], tray)
    # HBM stacks waiting on the same tray, clear of the dies.
    for i, (x, z) in enumerate(((14.0, -22.0), (30.0, -22.0), (14.0, 4.0), (30.0, 4.0))):
        K.hbm_stack(f"hbm_tray_{i}", (x, 0.0, z), (x + 8.0, 5.0, z + 8.0), m, tray)

    # Beats 1-3: the wafer of interposers, with two pieces that stay on it until the cut (beat 3).
    wafer = empty("wafer_grp", root)
    show(wafer, between(1, 3))  # gone once the package is cut out (beat 3)
    disc("wafer", (0.0, -1.0, 0.0), 120.0, 1.0, m["silicon"], wafer)
    side = []
    for x in WAFER_X:
        g = empty(f"wafer_tile_{x:+.0f}", root)
        g.location = P(x, 0.0, 0.0)
        show(g, between(1, 3))
        K.interposer(m, g, half=24.0)
        K.die(m, g)
        side.append(g)
    for g, x in zip(side, WAFER_X):
        key(g, F(1, 0), "location", P(x, DROP, 0.0))
        key(g, F(1, 0.6), "location", P(x, 0.0, 0.0))

    # The piece that gets cut out: its die lands on the wafer in beat 1, it stays put through
    # beat 2, is lifted clear of the wafer at the cut (beat 3) and set down on the substrate.
    # It carries its HBM (from beat 2), underfill (4) and lid (5).
    pkg = empty("pkg_grp", root)
    show(pkg, between(1, 6))
    K.interposer(m, pkg, half=26.0)
    K.die(m, pkg)
    # The package's own motion, keyed the same on the group and on its HBM (kept as a sibling
    # of the group, so the HBM's show-switch is not nested under the moving parent).
    pkg_hbm = empty("pkg_hbm", root)
    show(pkg_hbm, between(2, 6))
    for g in (pkg, pkg_hbm):
        key(g, F(1, 0), "location", P(0.0, DROP, 0.0))
        key(g, F(1, 0.6), "location", P(0.0, 0.0, 0.0))
        key(g, F(2, 0.99), "location", P(0.0, 0.0, 0.0))
        key(g, F(3, 0), "location", P(0.0, LIFT, 0.0))
        key(g, F(3, 0.45), "location", P(0.0, 0.0, 0.0))
    K.stacks(m, pkg_hbm, zs=(-9.0, 9.0))
    # The underfill and lid are animated, so they sit under the root (not under the moving pkg
    # group); the package is at rest by beat 4, where they are first seen.
    rim = empty("underfill_grp", root)
    show(rim, between(4, 6))  # off with the package at beat 6
    key(rim, F(4, 0), "location", P(0.0, 0.0, RIM_IN))
    key(rim, F(4, 0.5), "location", P(0.0, 0.0, 0.0))
    K.underfill_rim(m, rim)
    lidg = empty("lid_grp", root)
    show(lidg, between(5, 6))
    key(lidg, F(5, 0), "location", P(0.0, LID_DROP, 0.0))
    key(lidg, F(5, 0.5), "location", P(0.0, 0.0, 0.0))
    K.lid(m, lidg)

    # HBM stacks join the wafer interposers at beat 2: appear, do not fall. Gone with the wafer.
    stacks_w = empty("stacks_wafer", root)
    show(stacks_w, between(2, 3))
    for x in WAFER_X:
        K.stacks(m, stacks_w, zs=(-9.0, 9.0))
        for child in list(stacks_w.children)[-4:]:
            child.location = (child.location.x + x, child.location.y, child.location.z)

    # Beat 3: the substrate for the cut-out package, under it.
    sub = empty("substrate_grp", root)
    show(sub, between(3, 6))
    K.substrate(m, sub, half=30.0)
    c4g = empty("c4_grp", root)
    show(c4g, between(3, 6))
    K.c4(m, c4g, half=20.0)

    # Beat 6: finished packages in a row, each with substrate, interposer, die, stacks and lid.
    row = empty("finished_row", root)
    show(row, from_beat(6))
    for k, x in enumerate((-80.0, -40.0, 0.0, 40.0, 80.0)):
        f = empty(f"finished_{k}", row)
        f.location = P(x, 0.0, 0.0)
        K.substrate(m, f, half=18.0)
        K.interposer(m, f, half=14.0)
        K.die(m, f, x0=-6.0, x1=6.0, z0=-8.0, z1=8.0)
        K.stacks(m, f, zs=(-5.0, 5.0), inner=8.0, width=4.0, depth=6.0)
        K.lid(m, f, half=12.0)

    # Labels.
    labels = {
        0: [("known-good dies arrive", (-30.0, 3.0, -30.0), root)],
        1: [("chip on the interposer wafer", (6.0, 4.2, -6.0), root)],
        2: [("HBM stacks join", (18.0, 6.6, 9.0), root)],
        3: [("cut apart, then on the substrate", (25.0, 8.0, 14.0), root)],
        4: [("underfill flow", (-18.0, 2.4, 18.0), root)],
        5: [("lid goes on", (24.0, 9.0, 12.0), root)],
        6: [("capacity is the bottleneck", (0.0, -2.0, 14.0), root)],
    }
    for i, items in labels.items():
        for text, at, parent in items:
            label(text, at, parent, beat(i))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
