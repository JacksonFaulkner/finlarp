"""The MELT + PULL overview, authored in Blender and exported for pbr3d, in the SAND template
(docs/diagram-pages.md): a Czochralski puller cut open at z = 0, the camera on +z with one pose
per beat, and `label:<text>` empties for the tags the TUI pins on. The puller's pieces are in
melt_kit.py, shared with the zooms and sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/melt_overview.py

It writes:
  blender/melt_overview.blend   open it in Blender to edit by hand
  assets/melt_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/melt/overview.rs).

Beats (match the MELT + PULL overview page):
  0 load      polysilicon chunks and dopant specks drop into the quartz crucible
  1 melt      the heater glows, the chunks melt into a pool, argon sweeps down and out
  2 neck      the seed comes down, touches the melt and a thin neck is pulled fast
  3 shoulder  the crystal flares out to full diameter under the heat shield
  4 body      the body grows up into the pull chamber; the crucible rises as the melt drops
  5 tail      the end tapers to a cone and the crystal is lifted clear of the melt
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import melt_kit as K  # noqa: E402
from melt_kit import BODY, NECK, SHOULDER, TAIL  # noqa: E402

BEATS = 6

P_KEYS = [
    (0, 700.0),
    (F(2, 0.05), 700.0),
    (F(2, 0.28), 0.0),
    (F(2, 0.38), 0.0),  # dip and settle
    (F(2, 0.95), NECK),
    (F(3, 0.05), NECK),
    (F(3, 0.92), NECK + SHOULDER),
    (F(4, 0.03), NECK + SHOULDER),
    (F(4, 0.95), NECK + SHOULDER + BODY),
    (F(5, 0.03), NECK + SHOULDER + BODY),
    (F(5, 0.55), NECK + SHOULDER + BODY + TAIL),
    (F(5, 0.65), NECK + SHOULDER + BODY + TAIL),
    (F(5, 0.92), NECK + SHOULDER + BODY + TAIL + 350.0),
    (F(6, 0), NECK + SHOULDER + BODY + TAIL + 350.0),
]
CONTACT = F(2, 0.28)

POSES = [
    # beats 0-1 look down past the heat shield's rim into the crucible, so the charge isn't
    # hidden behind the shield
    ((0.0, 1000.0, 0.0), 4300.0, 0.30, 0.40),
    ((0.0, 800.0, 0.0), 3700.0, 0.24, 0.36),
    ((0.0, 870.0, 0.0), 1250.0, 0.30, 0.10),
    ((0.0, 860.0, 0.0), 1700.0, 0.30, 0.12),
    ((0.0, 1750.0, 0.0), 6000.0, 0.28, 0.10),
    ((0.0, 2050.0, 0.0), 7800.0, 0.28, 0.18),  # crucible and tail cone stay in view
]


def build():
    m, root = start("overview", BEATS, page="melt")
    K.mats(m)
    K.furnace(root, m, heat_on=F(1, 0.08), tags={
        "pull chamber": [(F(4, 0.4), F(5, 0))],
        "heater": beat(1),
        "felt": beat(1),
        "shield": beat(3),
    })
    K.crucible(root, m, load=0, melt=1, rise=(F(4, 0.03), F(4, 0.95)), tags={
        "quartz": beat(0),
        "rise": beat(4),
        "chunks": [(F(0, 0.4), F(1, 0))],
        "dopant": [(F(0, 0.6), F(1, 0))],
        "melt": [(F(1, 0.55), F(2, 0))],
    })
    K.crystal(root, m, P_KEYS, CONTACT, tags={
        "seed": [(F(2, 0.0), F(2, 0.55))],
        "neck": [(F(2, 0.6), F(3, 0))],
        "shoulder": [(F(3, 0.5), F(4, 0))],
        "body": [(F(4, 0.45), F(5, 0))],
        "tail": [(F(5, 0.35), F(6, 0))],
        "lifted": [(F(5, 0.7), F(6, 0))],
    })
    K.argon(root, m, 1, tags={"argon": beat(1)})
    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="melt")
