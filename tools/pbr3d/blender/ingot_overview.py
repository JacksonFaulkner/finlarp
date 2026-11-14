"""The INGOT overview, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md). The as-pulled rod moves along six stations, one per beat: it is cropped,
tested on its cut face, ground to 300 mm, notched and wire-sawn. Pieces come from ingot_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/ingot_overview.py

It writes:
  blender/ingot_overview.blend   open it in Blender to edit by hand
  assets/ingot_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/ingot/overview.rs).

Beats (match the INGOT overview page):
  0 as-pulled  a rough rod with a cone on each end
  1 crop       blades cut the cones off at the joints; the cones fall away as scrap
  2 test       X-ray on the cut face; the spots line up and the plane is found
  3 grind OD   the wheel grinds the rod round to 300 mm
  4 notch      a V groove runs the full length, marking <110>
  5 wire saw   the ingot is fed down into the wire web and comes out as wafers
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import camera, finish  # noqa: E402
import ingot_kit as K  # noqa: E402
from ingot_kit import A, CONE, HALF, R, RAW, begin  # noqa: E402

NAMES = ["asp", "crop", "test", "grind", "notch", "saw"]

POSES = [
    ((0.0, 640.0, 0.0), 3800.0, 0.40, 0.20),
    ((1600.0, 640.0, 0.0), 3800.0, 0.40, 0.20),
    ((3000.0, 620.0, 0.0), 4600.0, 0.40, 0.20),
    ((4800.0, 660.0, 0.0), 3700.0, 0.40, 0.20),
    ((6400.0, 660.0, 0.0), 3700.0, 0.40, 0.20),
    ((8000.0, 620.0, 0.0), 4100.0, 0.55, 0.22),
]

TAGS = {
    0: [("seed cone", -HALF - CONE / 2, A + RAW + 70, 80), ("tail cone", HALF + CONE / 2, A + RAW + 70, 80),
        ("as-pulled: a little over size", 0, A + RAW + 230, 80)],
    1: [("cones cut at the joints", 0, A + RAW + 230, 80), ("cones fall away as scrap", -HALF - CONE / 2, 220, 80)],
    2: [("X-ray on the cut face", HALF + 30, A + 330, 80), ("spots line up: plane found", 420, A - 420, 80)],
    3: [("grind wheel to 300 mm", 0, A + RAW + 430, 80), ("rough skin removed", -HALF + 60, A + RAW + 40, 80)],
    4: [("V groove along the length", 0, A + R + 150, 80), ("marks <110>", HALF - 60, A + R + 80, 80)],
    5: [("mounting beam holds the ingot", 0, A + RAW + 180, 0), ("wire web cuts the kerf", 0, A - 300, 0)],
}


def build():
    m, root = begin("overview", len(NAMES))
    K.line(root, m, NAMES, tags=TAGS)
    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="ingot")
