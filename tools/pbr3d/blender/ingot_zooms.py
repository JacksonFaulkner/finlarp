"""The four INGOT zoom-ins, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md), built from the pieces in ingot_kit.py. Each zoom is four beats.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/ingot_zooms.py [-- grind notch test saw]

For each zoom it writes blender/ingot_<name>.blend and assets/ingot_<name>.glb.

  grind  the as-pulled skin is ground off by a wheel, leaving a round body at 300 mm
  notch  the V groove grows along the length, then shows as a notch on a wafer rim
  test   X-ray on the cut face: the spots scatter, then line up and the plane is found
  saw    the ingot is fed down through the wire web; the wafers part and leave a kerf
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, show, tube  # noqa: E402
from sand_zooms import camera, finish  # noqa: E402
import ingot_kit as K  # noqa: E402
from ingot_kit import A, HALF, R, RAW, SAW_LIFT, begin, move, V_PROF  # noqa: E402

END = F(40, 0)


def tag(root, text, at, f0, f1):
    label(text, at, root, [(f0, f1)])


def grind(root=None):
    m, root = begin("grind", 4)
    rp = K.rod(root, m, skin_until=F(1, 0.85), cones=False)
    K.grind(root, m, 0, F(1, 0.1), F(1, 0.85))
    tag(root, "rough skin, a little over size", (HALF * 0.3, A + RAW + 40, 60), F(0, 0.3), F(1, 0))
    tag(root, "the wheel takes the skin off", (-120, A + RAW + 330, 60), F(1, 0.3), F(2, 0))
    tag(root, "round body, 300 mm", (HALF * 0.5, A + R + 60, 60), F(2, 0.3), F(3, 0))
    tag(root, "end face: +/- 0.2 mm", (HALF, A + R + 30, 40), F(3, 0.3), END)
    camera(root, [
        ((0.0, A, 0.0), 1800.0, 0.5, 0.22),
        ((0.0, A + 140, 0.0), 1950.0, 0.6, 0.2),
        ((0.0, A + 60, 0.0), 1500.0, 0.8, 0.2),
        ((HALF - 150, A + 30, 0.0), 1500.0, math.pi / 2 - 0.4, 0.15),
    ])
    finish("grind", page="ingot")


def notch(root=None):
    m, root = begin("notch", 4)
    rp = K.rod(root, m, skin=False, cones=False)
    K.notch(root, m, rp, F(1, 0.1), F(1, 0.8))
    # beat 3: the rod drops out and a wafer is shown with its notch and the <110> direction
    show(rp["group"], [(0, F(2, 0.9))])
    wafer = K.xcyl("wafer", -11, 11, R, A, 0, m["si"], root)
    wafer_notch = K.prism_x("wafer_notch", -14, 14, V_PROF, m["notch"], root)
    show(wafer, [(F(2, 0.9), END)])
    show(wafer_notch, [(F(2, 0.9), END)])
    tube("direction", (16, A, 0), (16, A + R - 30, 0), 4, m["notch"], root, verts=8)
    tag(root, "V groove along the length", (HALF * 0.4, A + R + 140, 60), F(1, 0.3), F(2, 0))
    tag(root, "90 deg, 1.0 mm deep", (HALF * 0.5, A + R + 90, 60), F(2, 0.3), F(2, 0.9))
    tag(root, "marks <110>", (40, A + R + 40, 20), F(3, 0.3), END)
    camera(root, [
        ((0.0, A, 0.0), 1800.0, 0.5, 0.22),
        ((0.0, A, 0.0), 1700.0, 0.8, 0.2),
        ((0.0, A + R - 60, 0.0), 1400.0, math.pi / 2 - 0.4, 0.3),
        ((0.0, A + 20, 0.0), 900.0, math.pi / 2, 0.04),
    ])
    finish("notch", page="ingot")


def test(root=None):
    m, root = begin("test", 4)
    K.rod(root, m, cones=False, skin=False)
    K.test(root, m, 0, F(1, 0.1), F(2, 0.2), F(3, 0.2), END)
    tag(root, "the cut face, from the crop", (HALF - 120, A - 230, 0), F(0, 0.3), F(1, 0))
    tag(root, "X-ray beam onto the face", (HALF + 140, A + 320, 0), F(1, 0.3), F(2, 0))
    tag(root, "spots scattered: not yet", (HALF + 180, A - 330, 0), F(2, 0.3), F(3, 0))
    tag(root, "spots line up: plane found", (HALF + 200, A - 330, 0), F(3, 0.3), END)
    camera(root, [
        ((150.0, A, 0.0), 2100.0, 0.6, 0.25),
        ((300.0, A, 0.0), 2000.0, 0.6, 0.25),
        ((400.0, A - 20, 0.0), 1900.0, 0.7, 0.2),
        ((400.0, A - 20, 0.0), 1900.0, 0.7, 0.2),
    ])
    finish("test", page="ingot")


def saw(root=None):
    m, root = begin("saw", 4)
    rp = K.rod(root, m, cones=False, skin=False)
    move(rp["group"], [(0, (0, SAW_LIFT)), (F(1, 0.0), (0, SAW_LIFT)), (F(1, 0.8), (0, 0))])
    K.saw(root, m, rp, 0, F(2, 0.0), F(2, 0.3), F(3, 0.8))
    tag(root, "wire web: wires in the kerf", (0, A - 300, 0), F(0, 0.3), F(1, 0))
    tag(root, "the ingot is fed down", (0, A + RAW + 380, 0), F(1, 0.3), F(2, 0))
    tag(root, "each wire leaves a wafer", (0, A - 300, 0), F(2, 0.3), F(3, 0))
    tag(root, "kerf between wafers", (HALF * 0.4, A + RAW + 230, 0), F(3, 0.3), END)
    camera(root, [
        ((0.0, A + 80, 0.0), 2600.0, 0.6, 0.45),
        ((0.0, A + 40, 0.0), 2500.0, 0.6, 0.45),
        ((0.0, A, 0.0), 2300.0, 0.7, 0.55),
        ((0.0, A, 0.0), 2400.0, 0.7, 0.55),
    ])
    finish("saw", page="ingot")


ZOOMS = {"grind": grind, "notch": notch, "test": test, "saw": saw}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ZOOMS)
    for name in which:
        ZOOMS[name]()
