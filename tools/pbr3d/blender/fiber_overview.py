"""The FIBER tab overview: the whole optical link on one board, in the SAND template (docs/diagram-pages.md).

Run from the repo root (on the worker, or locally):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_overview.py

Writes blender/fiber_overview.blend and assets/fiber_overview.glb. One beat is 8 s.
Stations come from fiber_kit.py; this file only sets the beats, streams, camera and tags.

Beats (match the seven beats in diagrams_nodes/fiber/mod.rs):
  0 the whole link on its board
  1 PAM4 DSP: clean symbols           electrical data streams into the DSP
  2 LASER: bits to light              red beam from the laser into the fibre
  3 OPTICAL FIBER: glass, 0.3 dB      light runs down the core
  4 PHOTODIODE: light to amps         light lands; current leaves
  5 TRANSCEIVER: the module           the module is the focus
  6 CPO: optics on chip               the package with optics beside the ASIC
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, camera, finish, stream_of  # noqa: E402
import fiber_kit as K  # noqa: E402

PAGE = "fiber"
NAME = "overview"
BEATS = 7

POSES = [
    ((130.0, 0.0, 0.0), 450.0, 0.45, 0.35),
    ((0.0, -2.0, 0.0), 90.0, 0.60, 0.30),
    ((42.0, -2.0, 0.0), 80.0, 0.60, 0.30),
    ((84.0, -4.0, 0.0), 120.0, 0.50, 0.30),
    ((122.0, -2.0, 0.0), 85.0, 0.60, 0.30),
    ((172.0, 4.0, 0.0), 110.0, 0.50, 0.30),
    ((236.0, -2.0, 0.0), 95.0, 0.60, 0.30),
]


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = K.materials()
    K.link_stations(m, root)

    # Beat 1: electrical data streams into the DSP.
    elec = empty_group(root, "elec_in", (F(1, 0), F(2, 0)))
    stream_of(elec, "elec_in_s", 4, (K.DSP_X - 50.0, -5.0, 0.0), [(0, 0, 0), (34.0, 0, 0)],
              1.2, m["elec"], 1, 0.05, 0.6, 40)

    # Beat 2: red beam from the laser into the fibre.
    beam = empty_group(root, "beam", (F(2, 0), F(5, 0)))
    stream_of(beam, "beam_s", 3, (K.LASER_X + 8.0, -5.0, 0.0), [(0, 0, 0), (60.0, 0, 0)],
              1.0, m["light"], 2, 0.1, 0.8, 30)

    # Beat 3: light down the fibre.
    fib_light = empty_group(root, "fibre_light", (F(3, 0), F(4, 0)))
    stream_of(fib_light, "fibre_s", 4, (K.LASER_X + 14.0, -5.0, 0.0), [(0, 0, 0), (66.0, 0, 0)],
              1.2, m["light"], 3, 0.05, 0.6, 40)

    # Beat 4: light into the photodiode, electrical current out toward the module.
    pd_in = empty_group(root, "pd_in", (F(4, 0), F(5, 0)))
    stream_of(pd_in, "pd_in_s", 3, (K.PD_X - 14.0, -5.0, 0.0), [(0, 0, 0), (12.0, 0, 0)],
              1.0, m["light"], 4, 0.1, 0.6, 24)
    pd_out = empty_group(root, "pd_out", (F(4, 0.4), F(5, 0)))
    stream_of(pd_out, "pd_out_s", 3, (K.PD_X + 6.0, -5.0, 0.0), [(0, 0, 0), (14.0, 0, 0)],
              1.0, m["elec"], 4, 0.5, 0.9, 24)

    labels = {
        0: [("PAM4 DSP", (K.DSP_X, 5.0, 12.0), root),
            ("LASER", (K.LASER_X, 5.0, 12.0), root),
            ("OPTICAL FIBER", (80.0, 5.0, 12.0), root),
            ("PHOTODIODE", (K.PD_X, 5.0, 12.0), root),
            ("TRANSCEIVER", (K.MOD_X, 16.0, 12.0), root),
            ("CPO", (K.CPO_X, 5.0, 12.0), root)],
        1: [("PAM4 DSP: clean symbols", (K.DSP_X, 5.0, -12.0), root)],
        2: [("LASER: bits to light", (K.LASER_X, 5.0, -12.0), root)],
        3: [("OPTICAL FIBER: glass, 0.3 dB", (80.0, 5.0, -12.0), root)],
        4: [("PHOTODIODE: light to amps", (K.PD_X, 5.0, -12.0), root)],
        5: [("TRANSCEIVER: the module", (K.MOD_X, 16.0, -12.0), root)],
        6: [("CPO: optics on chip", (K.CPO_X, 5.0, -12.0), root)],
    }
    for i, items in labels.items():
        for text, at, parent in items:
            label(text, at, parent, beat(i))

    camera(root, POSES)
    return root


def empty_group(parent, name, interval):
    """An empty shown during one interval (a stream's on/off switch)."""
    from pbr_kit import empty
    g = empty(name, parent)
    show(g, [interval])
    return g


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
