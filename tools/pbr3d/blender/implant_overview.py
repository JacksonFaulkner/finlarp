"""The IMPLANT node page's overview (FAB tab), in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/implant_overview.py

Writes blender/implant_overview.blend and assets/implant_overview.glb. One beat is 8 s.

One beamline, left to right, cut open along the beam (units are millimetres, Y up): a gas cabinet
feeds the arc source (BF3, PH3 or AsH3), the extraction electrodes pull ions out, the analyzer
magnet bends them by mass and charge, the mass slit passes one species, the accelerator column
sets the energy, the scanner spreads the beam, and the wafer sits tilted in the end station next to
a Faraday cup. Dopant ions ride the beam; wrong masses stop at the slit.

Beats (match the six beats in diagrams_nodes/implant/overview.rs):
  0 source      gas is ionized in the arc chamber; extraction pulls dopant ions into the beam
  1 analyzer    the magnet bends by mass; the right species passes the slit, the rest stop there
  2 accelerate  the column sets the energy, which sets how deep the ions will go
  3 scan        the scanner spreads the beam; the wafer is tilted and the Faraday cup counts the dose
  4 damage      the ions break the crystal; anneal heats the wafer to repair it and activate the dopant
  5 market      the end station and the makers: Applied Materials (Varian) and Axcelis

implant_zooms.py is not written; this page has no zoom-ins or numbered sections.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, empty, label, mat, pivot, rel, show, ball, box, disc, tube, fly, key  # noqa: E402
from sand_zooms import start, camera, finish  # noqa: E402

PAGE = "implant"
NAME = "overview"
BEATS = 6

# beam axis: y = 700 (poly), z = 0; the source is at x ~ 250, the wafer at x ~ 3700
BEAM_Y = 700.0
X_SRC, X_EXT, X_MAG, X_SLIT = 250.0, 700.0, 1100.0, 1550.0
X_COL0, X_COL1 = 1650.0, 3050.0
X_SCAN = 3150.0
X_WAFER = 3700.0
PATH_GOOD = [(650.0, BEAM_Y, 0.0), (1545.0, BEAM_Y, 0.0), (3650.0, BEAM_Y, 0.0)]
PATH_WRONG = [(1200.0, BEAM_Y, 0.0), (1540.0, 560.0, 0.0)]

# (camera target, distance, yaw, pitch), one per beat
POSES = [
    ((2000.0, 700.0, 0.0), 6600.0, 0.30, 0.18),
    ((1250.0, 700.0, 0.0), 2800.0, 0.50, 0.15),
    ((2400.0, 700.0, 0.0), 3000.0, 0.45, 0.15),
    ((3400.0, 700.0, 0.0), 2800.0, 0.35, 0.20),
    ((3700.0, 700.0, 0.0), 1400.0, 0.50, 0.25),
    ((3300.0, 700.0, 0.0), 4600.0, 0.20, 0.25),
]


def axis_x(obj, degrees=90.0):
    """Turn a disc or tube built on the poly-Y axis so its axis runs along poly X (the beam)."""
    obj.rotation_euler = (0.0, math.radians(degrees), 0.0)
    return obj


def build_beamline(root, m):
    """The implanter: gas cabinet, arc source, extraction, analyzer, slit, column, scanner, end station."""
    g = empty("beamline", root)

    # gas cabinet and feed line
    box("gas_cabinet", (-400.0, 0.0, -350.0), (-50.0, 1200.0, 350.0), m["dark_steel"], g)
    tube("gas_line", (-50.0, 700.0, 0.0), (250.0, 700.0, 0.0), 30.0, m["steel"], g)
    label("gas: BF3, PH3, AsH3", (-225.0, 1350.0, 0.0), g, beat(0))

    # arc source: a horizontal chamber with its plasma glowing inside
    tube("source", (250.0, BEAM_Y, 0.0), (650.0, BEAM_Y, 0.0), 230.0, m["steel"], g, verts=48)
    tube("plasma", (300.0, BEAM_Y, 0.0), (600.0, BEAM_Y, 0.0), 120.0, m["flame"], g, verts=32)
    label("ion source: arc chamber", (450.0, 1050.0, 0.0), g, beat(0))

    # extraction electrodes pull ions out of the source
    box("extract_a", (X_EXT - 20.0, 380.0, -220.0), (X_EXT + 20.0, 1020.0, 220.0), m["electrode"], g)
    label("extraction electrodes", (X_EXT, 1200.0, 0.0), g, beat(0))

    # analyzer magnet: a box across the beam, lit during beat 1
    mag = pivot("analyzer", (X_MAG, BEAM_Y, 0.0), g)
    box("analyzer_magnet", rel((X_MAG, BEAM_Y, 0.0), (X_MAG - 260.0, 300.0, -300.0)),
        rel((X_MAG, BEAM_Y, 0.0), (X_MAG + 260.0, 1100.0, 300.0)), m["dark_steel"], mag)
    label("analyzer magnet bends by mass", (X_MAG, 1250.0, 0.0), g, beat(1))

    # mass-resolving slit: two plates with the gap the right species passes through
    box("slit_top", (X_SLIT - 15.0, 720.0, -300.0), (X_SLIT + 15.0, 900.0, 300.0), m["steel"], g)
    box("slit_bottom", (X_SLIT - 15.0, 500.0, -300.0), (X_SLIT + 15.0, 680.0, 300.0), m["steel"], g)
    label("slit: wrong masses stop here", (X_SLIT, 300.0, 0.0), g, beat(1))

    # accelerator column: a clear tube with a ring per stage
    tube("column", (X_COL0, BEAM_Y, 0.0), (X_COL1, BEAM_Y, 0.0), 190.0, m["pipe_glass"], g, verts=32)
    for k in range(7):
        x = X_COL0 + 40.0 + k * 200.0
        axis_x(disc(f"stage{k}", (x, BEAM_Y, 0.0), 200.0, 30.0, m["steel"], g, verts=48))
    label("accelerator or decel column", (2350.0, 1100.0, 0.0), g, beat(2))

    # scanner: a pair of plates that sweep the beam across the wafer
    box("scan_top", (X_SCAN - 12.0, 830.0, -240.0), (X_SCAN + 12.0, 960.0, 240.0), m["steel"], g)
    box("scan_bottom", (X_SCAN - 12.0, 440.0, -240.0), (X_SCAN + 12.0, 570.0, 240.0), m["steel"], g)
    label("scanner spreads the beam", (X_SCAN, 1150.0, 0.0), g, beat(3))
    return g


def build_end_station(root, m):
    """The wafer, tilted and spun, beside a Faraday cup; the damage skin and anneal ring for beat 4."""
    g = empty("end_station", root)
    holder = pivot("wafer_tilt", (X_WAFER, BEAM_Y, 0.0), g)
    axis_x(disc("wafer", rel((X_WAFER, BEAM_Y, 0.0), (X_WAFER, BEAM_Y, 0.0)), 150.0, 12.0, m["silicon"], holder, verts=96))
    # amorphous skin left by the ions: a thin shell over the wafer face, lit during beat 4
    skin = pivot("damage_skin", (X_WAFER + 14.0, BEAM_Y, 0.0), g)
    axis_x(disc("skin", rel((X_WAFER + 14.0, BEAM_Y, 0.0), (X_WAFER + 14.0, BEAM_Y, 0.0)), 146.0, 6.0, m["damage"], skin, verts=96))
    show(skin, [(F(4, 0.0), F(5, 0.0))])
    # anneal ring: a heat source around the wafer, on during the second half of beat 4
    ring = pivot("anneal_ring", (X_WAFER, BEAM_Y, 0.0), g)
    axis_x(disc("heat", rel((X_WAFER, BEAM_Y, 0.0), (X_WAFER, BEAM_Y, 0.0)), 178.0, 14.0, m["flame"], ring, verts=96))
    show(ring, [(F(4, 0.5), F(5, 0.0))])
    # the wafer holder: a block behind the wafer
    box("holder", (X_WAFER + 20.0, 560.0, -220.0), (X_WAFER + 120.0, 840.0, 220.0), m["dark_steel"], g)
    # Faraday cup, counts the beam current
    box("faraday_cup", (3500.0, 330.0, 220.0), (3880.0, 520.0, 330.0), m["steel"], g)
    label("wafer, tilted and spun", (X_WAFER, 1050.0, 0.0), g, beat(3))
    label("Faraday cup counts current", (3700.0, 300.0, 280.0), g, beat(3))
    label("damage: amorphous skin", (X_WAFER, 1050.0, 280.0), g, beat(4))
    label("anneal: heal, activate", (X_WAFER, 1200.0, 0.0), g, [(F(4, 0.5), F(5, 0.0))])
    label("Applied (Varian), Axcelis", (X_WAFER, 1300.0, 0.0), g, beat(5))
    label("dopant gases are toxic", (-225.0, 400.0, 0.0), g, beat(5))
    return g, holder


def build(root=None):
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m["damage"] = mat("damage", (0.30, 0.12, 0.12), rough=0.9, alpha=0.5)
    m["reject"] = mat("reject", (0.55, 0.55, 0.60), rough=0.6)
    build_beamline(root, m)
    g, holder = build_end_station(root, m)

    # the beam: a glowing tube on for beats 0-3
    beam = tube("beam", (650.0, BEAM_Y, 0.0), (3650.0, BEAM_Y, 0.0), 20.0, m["jet"], root, verts=16)
    show(beam, [(F(0, 0.0), F(4, 0.0))])

    # dopant ions: two per beat in beats 0-3, flying source to wafer
    for b in range(4):
        for k in range(2):
            bead = ball(f"ion_{b}_{k}", (0.0, 0.0, 0.0), 22.0, m["melt"], root)
            fly(bead, PATH_GOOD, F(b, 0.05 + 0.4 * k), F(b, 0.45 + 0.4 * k))

    # wrong masses: grey beads that stop at the slit, during beat 1
    for k in range(3):
        bead = ball(f"reject_{k}", (0.0, 0.0, 0.0), 20.0, m["reject"], root)
        fly(bead, PATH_WRONG, F(1, 0.1 + 0.2 * k), F(1, 0.2 + 0.2 * k))

    # the wafer tilts for beat 3 (channeling is avoided by tilt and spin)
    key(holder, F(3, 0.0), "rotation_euler", (0.0, 0.0, math.radians(0.0)))
    key(holder, F(3, 0.5), "rotation_euler", (0.0, 0.0, math.radians(7.0)))
    key(holder, F(4, 0.0), "rotation_euler", (0.0, 0.0, math.radians(7.0)))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
