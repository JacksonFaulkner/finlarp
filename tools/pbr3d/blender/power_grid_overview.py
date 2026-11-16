"""The GRID node page's overview (POWER tab), in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/power_grid_overview.py

Writes blender/power_grid_overview.blend and assets/power_grid_overview.glb. One beat is 8 s.

One diorama, left to right (power_grid_detail.world): a power plant's turbine hall cut open
(turbine, generator), the isolated-phase bus to the step-up transformer (cut open), four
double-circuit lattice towers with insulator strings and sagging conductors, the campus substation
(gantry, bus, step-down transformer), the utility meter, the data hall (cut open: racks, busways,
cooling on the roof) and a gas turbine package beside it. Glowing beads ride the real paths.

Beats (match the seven beats in diagrams_nodes/power/grid/overview.rs):
  0 campus      the whole run; power flows from the generator to the racks
  1 lines       towers and conductors, 115-345 kV, beads along all six conductors
  2 loss        close on a tower: insulator strings, sagging conductors, few large-current beads
  3 substation  the line lands on the gantry, drops to the bus, the transformer steps it down
  4 load        the data hall cut open, power along the busways into the racks
  5 queue       projects lined up at the substation gate; one studied; months tick by
  6 PUE         power into the hall splits: most to the racks, some to cooling; heat off the roof

power_grid_zooms.py rebuilds this scene and replays its beats with its own camera and tags (it swaps
LABEL and CAMERA, and may add EXTRA animation).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start  # noqa: E402
from power_grid_detail import finish  # noqa: E402
from sand_overview import empty  # noqa: E402
import power_grid_detail as D  # noqa: E402
from power_grid_detail import frame, camera_path, run, rise, segment  # noqa: E402

PAGE = "power_grid"
NAME = "overview"
BEATS = 7

# swapped by power_grid_zooms.py
LABEL = label
CAMERA = camera_path
EXTRA = None
W = {}  # the world's points, for power_grid_zooms.py


def turbine_runs(m, root, w, b, u0=0.05):
    """The gas turbine running through beat b: flame lit, power along its cable into the hall,
    exhaust rising off its stack."""
    show(w["flame"], [(F(b, u0), F(b + 1, 0))])
    run(root, f"gt_pow{b}", w["gt_path"], 8, 5.0, m["power"], b, u0, 0.75, 70)
    rise(root, f"gt_exh{b}", w["gt"]["stack"], 7, 9.0, m["heat"], b, u0, 0.8, 60, h=150, drift=(30, 0))


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = D.materials()
    w = D.world(m, root)
    W.clear()
    W.update(w)
    h = w["hall"]
    show(w["flame"], [])

    # beat 0: the whole run, all three phases of the near circuit, big beads for the wide shot
    for k in range(3):
        run(root, f"all{k}", D.full_path(w, 1, k), 7, 10.0, m["power"], 0, 0.0 + 0.04 * k, 0.55, 150)
    # beat 1: both circuits along the line
    for s in (1, -1):
        for k, ph in enumerate("ABC"):
            run(root, f"ln{s}{ph}", w["lines"][(s, ph)], 5, 6.0, m["power"], 1, 0.02 * k, 0.6, 110)
    # beat 2: close on a tower; a slow, sparse train on each near conductor
    for k, ph in enumerate("ABC"):
        p = segment(w["lines"][(1, ph)], D.TOWERS[1] - 10, D.TOWERS[3] + 10)
        run(root, f"lo{ph}", p, 5, 3.5, m["power"], 2, 0.05 * k, 0.65, 90)
    # beat 3: down the gantry's drops into the transformer and out to the hall
    for s in (1, -1):
        for k in range(3):
            p = D.join_paths(segment(w["lines"][(s, "ABC"[k])], D.TOWERS[3], D.GX), D.sub_path(w, s, k))
            run(root, f"sb{s}{k}", p, 4, 4.0, m["power"], 3, 0.03 * k, 0.6, 110)
    # beat 4: into the hall, along the busways
    for k in range(3):
        p = D.join_paths(w["sub"]["lv"][k], h["rows"][k])
        run(root, f"dh{k}", p, 8, 4.0, m["power"], 4, 0.02 * k, 0.7, 80)
    # beat 5: the queue at the substation gate; the front project studied; months tick by
    qg = empty("pg_queue", root)
    gs, front = D.queue(m, qg)
    W["front"] = front
    show(qg, beat(5))
    ring = D.scan_ring(m, root, (front[0], 30.0, front[2]), 52.0)
    show(ring, [(F(5, 0.1), F(5, 0.35)), (F(5, 0.45), F(5, 0.7)), (F(5, 0.8), F(6, 0))])
    board = empty("pg_month_board", root)
    D.box("pg_board", (720.0, 60.0, 330.0), (875.0, 210.0, 332.0), m["tank_in"], board)
    D.box("pg_board_leg", (795.0, 0.0, 328.0), (801.0, 60.0, 332.0), m["lattice"], board)
    lit = D.months(m, board, 728.0, 192.0, 332.0, size=10.0, gap=3.0, per_row=11)
    show(board, beat(5))
    for i, g in enumerate(lit):
        show(g, [(F(5, 0.05 + 0.85 * i / len(lit)), F(6, 0))])
    # beat 6: into the hall, most to the racks, some up to the roof units; heat off the fans
    for k in range(3):
        p = D.join_paths(w["sub"]["lv"][k], h["rows"][k])
        run(root, f"it{k}", p, 7, 4.0, m["power"], 6, 0.02 * k, 0.7, 80)
    p = D.join_paths(w["sub"]["lv"][1], h["riser"])
    run(root, "cool", p, 4, 4.0, m["heat"], 6, 0.1, 0.7, 80)
    for i, f in enumerate(h["fans"][::2]):
        rise(root, f"heat{i}", f, 3, 7.0, m["heat"], 6, 0.2 + 0.05 * i, 0.9, 60, h=110, drift=(15, 10))
    if EXTRA:
        EXTRA(m, root, w)

    p, g, s, gt = w["plant"], w["gsu"], w["sub"], w["gt"]
    tags = {
        0: [("power plant", p["hall"]), ("towers, 115-345 kV", (D.TOWERS[1], 400.0, 0.0)),
            ("substation", (D.GX, 252.0, -118.0)), ("data hall", h["roof"])],
        1: [("115-345 kV conductors", w["lines"][(1, "A")][len(w["lines"][(1, "A")]) // 2]),
            ("steel lattice tower", (D.TOWERS[2] + 30, 180.0, 30.0)), ("three phases a side", (D.TOWERS[2], 350.0, 70.0))],
        2: [("insulator string", (D.TOWERS[2], 290.0, 92.0)), ("conductor sags between towers",
                                                                 w["lines"][(1, "B")][len(w["lines"][(1, "B")]) // 2 - 5]),
            ("earth wire on the peak", (D.TOWERS[2], 400.0, 34.0))],
        3: [("gantry: the line lands", (D.GX, 252.0, 118.0)), ("step-down transformer", s["sd"]["bushing"]),
            ("bus on post insulators", s["bus"]), ("utility meter", s["meter"])],
        4: [("data hall, cut open", h["roof"]), ("racks in rows", h["row"]), ("busway over each row", h["busway"])],
        5: [("projects waiting to connect", (front[0] - 300, 60.0, front[2])), ("studied before connecting", (front[0], 82.0, front[2] + 50)),
            ("55 months typical", (798.0, 210.0, 331.0))],
        6: [("IT power: the racks", h["row"]), ("overhead: cooling", h["units"]), ("heat off the roof", (h["fans"][4][0], 260.0, h["fans"][4][2]))],
    }
    for i, items in tags.items():
        for text, pos in items:
            LABEL(text, pos, root, beat(i))
    CAMERA(root, POSES)
    return root


POSES = [
    frame((150.0, 320.0, -60.0), 1750.0, 0.55, 0.36, pad=1.0),
    frame((-280.0, 260.0, 0.0), 900.0, 0.55, 0.20),
    frame((-90.0, 300.0, 40.0), 260.0, 0.62, 0.12),
    frame((740.0, 130.0, -10.0), 420.0, 0.45, 0.32),
    frame((1200.0, 70.0, -120.0), 560.0, 0.20, 0.40),
    frame((470.0, 90.0, 260.0), 640.0, 0.15, 0.36),
    frame((1230.0, 120.0, -120.0), 640.0, 0.28, 0.45),
]


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
