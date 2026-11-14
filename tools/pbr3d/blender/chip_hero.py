"""The CHIP hero: the whole chip cross-section in the MELT + PULL template (docs/diagram-pages.md),
cut at its centre plane with the camera on +z. Every Chip-tab node plays this same scene zoomed in
on its part (chip_zoom.py); this is the tour of all of it.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/chip_hero.py

Writes blender/chip_hero.blend and assets/chip_hero.glb. One beat is 8 s; the TUI samples at
t = (beat + local) * 8.

Beats:
  0 whole     the cross-section: silicon at the bottom, wiring on top, bumps over everything
  1 power     VDD comes in through a bump and down the thick top metal, the stacked vias and the
              contacts to the PMOS; the return runs up from the NMOS to the VSS bump
  2 switch    a 1 on the gates turns the NMOS on and the PMOS off: the output is pulled low
  3 local     the output climbs the contact into thin metal, the dense local wiring
  4 global    it moves on through mid metal (block to block) and top metal (chip wide) to a bump
  5 whole     all of it again: three tiers, one rule, the signal always climbs to wider wire
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import camera, finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, label, route, stream_of  # noqa: E402

BEATS = 6
LIFE = 60

GATE_ON = [(F(2, 0.10), F(4, 0.0))]
THIN_ON = [(F(3, 0.05), F(4, 0.0))]
MID_ON = [(F(4, 0.05), F(4, 0.55))]
TOP_ON = [(F(4, 0.45), F(5, 0.0))]
BUMPS_ON = [(F(1, 0.05), F(2, 0.0)), (F(4, 0.50), F(5, 0.0))]

WHOLE = ((0.0, 620.0, 0.0), 5800.0, 0.0, 0.10)
POSES = [
    WHOLE,
    ((0.0, 700.0, 0.0), 5200.0, 0.0, 0.10),
    ((0.0, 260.0, 0.0), 3800.0, 0.0, 0.10),
    ((-100.0, 520.0, 0.0), 4200.0, 0.0, 0.10),
    ((200.0, 900.0, 0.0), 5200.0, 0.0, 0.10),
    WHOLE,
]


def build(name="hero", poses=POSES):
    m, root = start(name, BEATS, page="chip")
    C.mats(m)
    C.chip(root, m, gate=GATE_ON, thin=THIN_ON, mid=MID_ON, top=TOP_ON, bumps=BUMPS_ON)

    # power: VDD down to the PMOS source, the return up from the NMOS source to the VSS bump
    y_in = C.BUMP_Y
    s, p = route([(C.VDD_X, y_in, -60), (C.VDD_X, 6, -60)])
    stream_of(root, "vdd", 9, s, p, 46, m["c_dot_vdd"], 1, 0.10, 0.60, 90)
    s, p = route([(C.VSS_X, 6, -60), (C.VSS_X, y_in, -60)])
    stream_of(root, "vss", 9, s, p, 46, m["c_dot_gnd"], 1, 0.10, 0.60, 90)

    # switch: the input arrives from a bump, down to thin metal, across, down to the gate
    y_thin = C.level_y("thin", 3)
    s, p = route([(C.IN_X, y_in, -60), (C.IN_X, y_thin, -60), (C.NMOS_X, y_thin, -60), (C.NMOS_X, 120, -60)])
    stream_of(root, "input", 9, s, p, 46, m["c_dot_sig"], 2, 0.05, 0.50, 100)

    # the output: up the NMOS drain contact into thin metal, across to the middle
    y1 = C.level_y("thin", 0)
    s, p = route([(-510, 6, -60), (-510, y1, -60), (C.OUT_X, y1, -60)])
    stream_of(root, "out_thin", 9, s, p, 46, m["c_dot_out"], 3, 0.05, 0.55, 90)
    # then up through mid and top metal to a bump
    s, p = route([(C.OUT_X, y1, -60), (C.OUT_X, C.level_y("mid", 2), -60), (C.OUT_X, y_in, -60)])
    stream_of(root, "out_up", 9, s, p, 46, m["c_dot_out"], 4, 0.05, 0.55, 110)

    label("package bumps", (-890.0, y_in + 100, -60), root, [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))])
    label("top metal M10-M14", (1000.0, C.TOP[1] - 60, 0), root, [(F(0, 0), F(1, 0)), (F(4, 0.45), F(6, 0))])
    label("mid metal M5-M9", (1000.0, C.MID[1] - 60, 0), root, [(F(0, 0), F(1, 0)), (F(4, 0.05), F(4, 0.55)), (F(5, 0), F(6, 0))])
    label("thin metal M1-M4", (1000.0, C.THIN[1] - 60, 0), root, [(F(0, 0), F(1, 0)), (F(3, 0), F(4, 0)), (F(5, 0), F(6, 0))])
    label("contacts", (1150.0, 200.0, 0), root, [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))])
    label("NMOS", (C.NMOS_X, -150.0, 0), root, [(F(0, 0), F(1, 0)), (F(2, 0), F(4, 0)), (F(5, 0), F(6, 0))])
    label("PMOS", (C.PMOS_X, -150.0, 0), root, [(F(0, 0), F(1, 0)), (F(2, 0), F(4, 0)), (F(5, 0), F(6, 0))])
    label("silicon substrate", (0.0, -200.0, 0), root, [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))])
    label("VDD in", (C.VDD_X, y_in + 110, -60), root, [(F(1, 0), F(2, 0))])
    label("VSS return", (C.VSS_X, y_in + 110, -60), root, [(F(1, 0), F(2, 0))])
    label("input: gates high", (C.NMOS_X, 260.0, 0), root, [(F(2, 0), F(3, 0))])
    label("NMOS on, PMOS off", (0.0, -150.0, 0), root, [(F(2, 0.3), F(4, 0))])
    label("local hop", (C.OUT_X, 700.0, 0), root, [(F(3, 0), F(4, 0))])
    label("to the next block", (-1000.0, 830.0, 0), root, [(F(4, 0), F(4, 0.5))])
    label("across the chip", (-1000.0, 1230.0, 0), root, [(F(4, 0.45), F(5, 0))])

    camera(root, poses)


if __name__ == "__main__":
    build()
    finish("hero", page="chip")
