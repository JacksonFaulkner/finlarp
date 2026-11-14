"""The HBM STACK overview, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md): four DRAM stacks beside a GPU on a silicon interposer, cut open at z = 0,
the camera on +z with one pose per beat, and `label:<text>` empties for the tags the TUI pins on.
The stack's pieces are in hbm_kit.py, shared with the zooms and sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/hbm_overview.py

It writes:
  blender/hbm_overview.blend   open it in Blender to edit by hand
  assets/hbm_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/hbm/overview.rs).

Beats (match the HBM STACK overview page):
  0 package    a GPU and HBM stacks on one silicon interposer
  1 one stack  a base logic die under eight DRAM dies
  2 apart      the dies pull apart and microbumps show between them
  3 read       a read runs down the TSVs to the base die (the dies close again)
  4 interposer the four stacks' buses cross the interposer to the GPU
  5 taller     the stacks grow from eight dies to sixteen
  6 heat       the lower dies glow, heat leaves through the top, then the stacks settle to eight
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
from sand_overview import label, show  # noqa: E402
import hbm_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, END, GPU_X, STACK_XS, TSV_X, die_top  # noqa: E402

BEATS = 7

POSES = [
    ((0.0, 260.0, 0.0), 5200.0, 0.30, 0.16),
    ((-850.0, 330.0, 0.0), 2000.0, 0.34, 0.12),
    ((-850.0, 420.0, 0.0), 2100.0, 0.34, 0.12),
    ((-850.0, 330.0, 0.0), 2000.0, 0.34, 0.12),
    ((-300.0, 220.0, 0.0), 5400.0, 0.30, 0.14),
    ((-850.0, 520.0, 0.0), 2700.0, 0.34, 0.10),
    ((-850.0, 500.0, 0.0), 2500.0, 0.34, 0.10),
]

LOW_GLOW_DIES = 6  # the bottom dies glow in beat 6


def build():
    m, root = start("overview", BEATS, page="hbm")
    K.mats(m)
    K.package(root, m)
    label("GPU", (0.0, 420.0, 40.0), root, beat(0))
    label("HBM stacks beside the GPU", (-1500.0, 640.0, 0.0), root, beat(0))
    label("silicon interposer", (1900.0, -60.0, 0.0), root, beat(0))

    stacks = []
    for x in STACK_XS:
        phy = 1 if x < 0 else -1  # the PHY faces the GPU
        stacks.append(K.stack(root, m, x, 16, f"hbm{int(x)}", phy=phy, glow=True))

    for s in stacks:
        # Dies 9 to 16 (k = 8..15) exist only in beats 5 and 6: they drop onto the stack in beat 5
        # and go in beat 6.
        for k in range(8, 16):
            d = s.dies[k]
            key_drop(d, k)
            show(d, [(F(5, 0.1), F(6, 0.75))])
        # Every die stays closed until beat 2 pulls them apart, and comes back in beat 3.
        K.lift(s, [(F(2, 0.05), 0.0), (F(2, 0.6), 1.0), (F(3, 0.3), 0.0)])
        # Microbumps show from beat 2 on.
        for b in s.bumps:
            show(b, [(F(2, 0.3), END)])
        # Heat plates on the bottom dies in beat 6.
        for k in range(LOW_GLOW_DIES):
            show(s.glows[k], [(F(6, 0.05), F(6, 0.6))])
        for k in range(LOW_GLOW_DIES, 16):
            if s.glows[k] is not None:
                show(s.glows[k], [])

    # Beat 1: one stack. Beat 2: the pulled-apart stack. Beat 3: a read down the TSVs.
    sx = STACK_XS[1]
    label("base logic die", (sx + BASE_HALF + 10, 35.0, 0.0), root, beat(1))
    label("DRAM dies, eight shown", (sx + BASE_HALF + 10, 330.0, 0.0), root, beat(1))
    label("TSVs run through each die", (sx - BASE_HALF - 10, 300.0, 0.0), root, beat(1))
    label("microbumps join each die", (sx + BASE_HALF + 10, 150.0, 0.0), root, [(F(2, 0.4), F(3, 0))])
    label("read down the TSVs", (sx - BASE_HALF - 10, 470.0, 0.0), root, [(F(3, 0.2), F(4, 0))])

    # Beat 3: a read goes down each TSV column of every stack, after the dies have closed.
    for si, s_x in enumerate(STACK_XS):
        for i, tx in enumerate(TSV_X):
            K.dots(root, m, f"read{si}_{i}_", [(s_x + tx, die_top(7) - 10, 0.0), (s_x + tx, 30.0, 0.0)],
                   3, "read", 3, 0.4, 0.75, 60, size=12.0)

    # Beat 4: each stack's PHY sends its bus to the GPU. The outer stacks arc over the inner ones.
    for s_x in STACK_XS:
        phy = 1 if s_x < 0 else -1
        edge = s_x + phy * (BASE_HALF + 4)
        gx = -GPU_X if phy > 0 else GPU_X
        if abs(s_x) < 1000:
            pts = [(edge, 60.0, 0.0), (gx, 200.0, 0.0)]
        else:
            pts = [(edge, 60.0, 0.0), (edge, 660.0, 0.0), (gx, 660.0, 0.0), (gx, 220.0, 0.0)]
        K.dots(root, m, f"bus{int(s_x)}_", pts, 3, "data", 4, 0.1, 0.5, 70, size=30.0)
    label("PHY drives the bus", (-660.0, 60.0, 0.0), root, beat(4))
    label("to the GPU across the interposer", (-300.0, 330.0, 0.0), root, beat(4))

    # Beat 5: the top dies drop in (the drops are keyed in key_drop). Beat 6: heat leaves the top.
    for s_x in STACK_XS:
        for i, tx in enumerate(TSV_X):
            K.dots(root, m, f"heat{int(s_x)}_{i}_", [(s_x + tx, 1030.0, 0.0), (s_x + tx, 1220.0, 0.0)],
                   2, "heat", 6, 0.2, 0.6, 90, size=12.0)
    label("HBM4: 16-high, up to 64 GB", (-660.0, 900.0, 0.0), root, [(F(5, 0.5), F(6, 0.75))])
    label("lower dies run hottest", (-660.0, 200.0, 0.0), root, [(F(6, 0.05), F(6, 0.6))])
    label("heat leaves through the top", (-660.0, 1150.0, 0.0), root, [(F(6, 0.2), F(6, 0.75))])

    camera(root, POSES)


def key_drop(d, k):
    """Die k (8..15) starts 400 mm above its place at beat 5 and drops onto the stack."""
    K.key(d, F(5, 0.1), "location", P(0, 400.0, 0))
    K.key(d, F(5, 0.55), "location", P(0, 0, 0))


if __name__ == "__main__":
    build()
    finish("overview", page="hbm")
