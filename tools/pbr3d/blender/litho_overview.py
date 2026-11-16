"""The LITHO overview, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md): one layer through the exposure scanner, cut open at z = 0, the camera on
+z with one pose per beat, and `label:<text>` empties for the tags the TUI pins on. The scanner's
pieces are in litho_kit.py, shared with the zooms and sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/litho_overview.py

It writes:
  blender/litho_overview.blend   open it in Blender to edit by hand
  assets/litho_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/litho/overview.rs).

Beats (match the LITHO overview page):
  0 align     the sensor's green beam reads the marks on the wafer
  1 source    the source lights the reticle; light passes the chrome-free openings
  2 lens      the lens prints the image 4x smaller on the resist
  3 scan      one field: the wafer slides one field width, the reticle 4x as far, the other way
  4 step      the stage steps field to field; the exposed fields fill in pink
  5 develop   the exposed resist washes away (cyan: the film shows through)
  6 etch      the exposed resist is gone; fresh purple resist for the next layer
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, key, label  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import litho_kit as K  # noqa: E402
from litho_kit import END, FIELDS, RES_TOP  # noqa: E402

BEATS = 7

# the stage moves the wafer under the lens for the scan (its alignment happens in beat 0)
STAGE_IN = (F(2, 0.85), F(3, 0.0))

POSES = [
    ((120.0, 150.0, 0.0), 1100.0, 0.35, 0.12),
    ((0.0, 440.0, 0.0), 1700.0, 0.30, 0.12),
    ((0.0, 430.0, 0.0), 1500.0, 0.30, 0.10),
    ((40.0, 360.0, 0.0), 1550.0, 0.28, 0.12),  # wafer and reticle both in frame: the 4x scan
    ((0.0, 90.0, 0.0), 1200.0, 0.28, 0.14),
    ((-135.0, 60.0, 0.0), 800.0, 0.22, 0.16),
    ((-135.0, 60.0, 0.0), 800.0, 0.22, 0.16),
]


def build():
    m, root = start("overview", BEATS, page="litho")
    K.mats(m)
    K.frame(root, m)
    K.source(root, m, on=[(F(1, 0), END)])
    ret = K.reticle(root, m)

    # the scan: field 0 and 1 in beat 3, fields 2..8 in beat 4
    first = K.plan(F(3, 0.05), 0.40 * 192, 2)
    rest = K.plan(F(4, 0.0), 0.95 * 192 / (FIELDS - 2), FIELDS - 2)
    windows = first + rest
    scans = [(f0, f1) for f0, f1, _, _ in windows]
    slit_on = [(f0, f1) for f0, f1 in scans]
    lens = K.lens(root, m, slit_on=slit_on)  # noqa: F841

    wg, tiles = K.wafer(root, m)
    key(wg, 0, "location", (0, 0, 0))
    key(wg, STAGE_IN[0], "location", (0, 0, 0))
    key(wg, STAGE_IN[1], "location", (K.X_START, 0, 0), linear=True)
    K.scan_keys(wg, ret, windows, k0=0)
    for k, (pink, cyan) in tiles.items():
        f1 = windows[k][1]
        show_pink = [(f1, F(5, 0.05))]
        show_cyan = [(F(5, 0.05), F(6, 0.10))]
        K.show(pink, show_pink)
        K.show(cyan, show_cyan)

    K.sensor(root, m, beam_on=[(F(0, 0), F(1, 0))])
    K.rays(root, m, 1, 0.0, 0.8, K.light_path_to_reticle, n=2, life=30)
    K.rays(root, m, 2, 0.0, 0.8, K.light_path_to_wafer, n=3, life=40)

    # tags: two to four per beat, each for the beat it explains
    label("alignment sensor reads the marks", (K.SENSOR_X + 4, 262, 20), root, [(F(0, 0), F(1, 0))])
    label("marks from the layer below", (K.MARK_X, RES_TOP + 40, 20), wg, [(F(0, 0), F(1, 0))])
    label("source: 193 nm DUV, 13.5 nm EUV", (0, 810, 20), root, [(F(1, 0), F(2, 0))])
    label("reticle: chrome on quartz", (-150, K.RET_Y + 30, 20), root, [(F(1, 0), F(2, 0))])
    label("lens: prints 4x smaller", (160, 380, 20), root, [(F(2, 0), F(3, 0))])
    label("reticle moves 4x the wafer", (-160, K.RET_Y + 40, 20), root, [(F(3, 0), F(4, 0))])
    label("one field exposed at a time", (0, RES_TOP + 40, 20), wg, [(F(3, 0), F(4, 0))])
    label("step: next field", (0, RES_TOP + 40, 20), wg, [(F(4, 0), F(5, 0))])
    label("exposed resist washes away", (0, RES_TOP + 40, 20), wg, [(F(5, 0), F(6, 0))])
    label("fresh resist for the next layer", (0, RES_TOP + 40, 20), wg, [(F(6, 0), END)])

    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="litho")
