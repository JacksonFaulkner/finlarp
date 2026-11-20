"""The CLEAN node page's overview (FRONT END, strip and rinse), in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/clean_overview.py

Writes blender/clean_overview.blend and assets/clean_overview.glb. One beat is 8 s.

One wet bench, cut open along z = 0 and seen from +z: five open-front chemistry tanks (SPM, DHF,
SC-1, SC-2, ultrapure-water rinse) on a steel bench, a wafer carrier that rides from tank to tank,
and a hooded spin dryer at the right end. Bubbles rise in the hot tanks; a rinse stream falls into
the last tank.

Beats (match the six beats in diagrams_nodes/clean/overview.rs):
  0 bench     the whole bench; the carrier hangs over the first tank
  1 SPM       the carrier is lowered into the hot sulfuric / peroxide tank; bubbles rise
  2 DHF       lifted out, carried across, dipped in the dilute HF tank
  3 SC-1      across to the ammonia / peroxide tank; bubbles rise
  4 SC-2      across to the hydrochloric / peroxide tank
  5 rinse     rinsed in ultrapure water, then raised into the dryer hood

Units are millimetres, Y up, camera on +z (see sand_overview.P).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, mat, box, empty, key, label, beat, tube  # noqa: E402
from sand_zooms import start  # noqa: E402
from power_grid_detail import finish, frame, camera_path, run, rise  # noqa: E402

PAGE = "clean"
NAME = "overview"
BEATS = 6

# tank centres (x) and the carrier's rest x (over the first tank)
X_SPM, X_DHF, X_SC1, X_SC2, X_RIN = -1100.0, -600.0, -100.0, 400.0, 900.0
X_DRY = 1450.0
TANK_HALF = 200.0
HOVER_Y = 500.0  # the carrier rides this far above a tank when it travels

W = {}  # the scene's parts, for any later page script


def materials():
    return {
        "steel": mat("cl_steel", (0.45, 0.47, 0.50), metal=0.6, rough=0.4),
        "bench": mat("cl_bench", (0.18, 0.19, 0.21), metal=0.5, rough=0.5),
        "floor": mat("cl_floor", (0.40, 0.41, 0.43), rough=0.8),
        "wall": mat("cl_wall", (0.78, 0.78, 0.75), rough=0.8),
        "hood": mat("cl_hood", (0.70, 0.72, 0.74), metal=0.4, rough=0.45),
        "wafer": mat("cl_wafer", (0.55, 0.58, 0.64), metal=0.9, rough=0.22),
        "cassette": mat("cl_cassette", (0.20, 0.22, 0.25), rough=0.6),
        "spm": mat("cl_spm", (0.55, 0.22, 0.10), emit=(0.9, 0.35, 0.12), strength=0.6),
        "dhf": mat("cl_dhf", (0.80, 0.90, 0.95), rough=0.1),
        "sc1": mat("cl_sc1", (0.50, 0.75, 0.95), rough=0.1),
        "sc2": mat("cl_sc2", (0.60, 0.92, 0.80), rough=0.1),
        "uw": mat("cl_uw", (0.55, 0.82, 1.0), rough=0.1),
        "bub": mat("cl_bub", (0.92, 0.96, 1.0), emit=(0.85, 0.92, 1.0), strength=1.5),
        "water": mat("cl_water", (0.55, 0.80, 1.0), emit=(0.45, 0.75, 1.0), strength=2.0),
    }


def tank(name, x, liquid, m, root):
    """An open-front chemistry tank: floor, two side walls and a back wall, with the liquid
    inside. The front is open (z = 0) so the cut-away shows the bath."""
    lo, hi = x - TANK_HALF, x + TANK_HALF
    box(f"{name}_floor", (lo, 300.0, -340.0), (hi, 320.0, 0.0), m["steel"], root)
    box(f"{name}_wall_l", (lo, 300.0, -340.0), (lo + 20.0, 820.0, 0.0), m["steel"], root)
    box(f"{name}_wall_r", (hi - 20.0, 300.0, -340.0), (hi, 820.0, 0.0), m["steel"], root)
    box(f"{name}_back", (lo, 300.0, -360.0), (hi, 820.0, -340.0), m["steel"], root)
    box(f"{name}_liquid", (x - 180.0, 320.0, -330.0), (x + 180.0, 700.0, -20.0), liquid, root)


def carrier(m, root):
    """A wafer carrier with five wafers, built over the first tank. Its group starts at rest
    (in the tank) and is moved by route()."""
    cas = empty("clean_carrier", root)
    x = X_SPM
    for k in range(5):
        z = -280.0 + 14.0 * k
        box(f"clean_wafer{k}", (x - 150.0, 440.0, z - 2.0), (x + 150.0, 740.0, z + 2.0), m["wafer"], cas)
    box("clean_rail_l", (x - 166.0, 420.0, -300.0), (x - 158.0, 770.0, -205.0), m["cassette"], cas)
    box("clean_rail_r", (x + 158.0, 420.0, -300.0), (x + 166.0, 770.0, -205.0), m["cassette"], cas)
    box("clean_base", (x - 166.0, 420.0, -300.0), (x + 166.0, 432.0, -205.0), m["cassette"], cas)
    box("clean_handle", (x - 40.0, 770.0, -300.0), (x + 40.0, 800.0, -205.0), m["cassette"], cas)
    return cas


def D(x):
    """Offset of the carrier over tank x, when it is dipped."""
    return (x - X_SPM, 0.0, 0.0)


def H(x):
    """Offset of the carrier held above tank x."""
    return (x - X_SPM, HOVER_Y, 0.0)


def route(cas):
    """The carrier's path, one linear key per stop: beat, fraction, offset from rest."""
    stops = [(0, 0.00, H(X_SPM)), (0, 1.00, H(X_SPM))]
    # beat 1: lowered into the SPM tank
    stops += [(1, 0.00, H(X_SPM)), (1, 0.30, D(X_SPM)), (1, 1.00, D(X_SPM))]
    # beats 2-4: lift, carry across, lower into the next tank
    for b, prev, cur in ((2, X_SPM, X_DHF), (3, X_DHF, X_SC1), (4, X_SC1, X_SC2)):
        stops += [
            (b, 0.00, D(prev)),
            (b, 0.10, H(prev)),
            (b, 0.22, H(cur)),
            (b, 0.34, D(cur)),
            (b, 1.00, D(cur)),
        ]
    # beat 5: into the rinse, then up and over into the dryer hood
    stops += [
        (5, 0.00, D(X_SC2)),
        (5, 0.10, H(X_SC2)),
        (5, 0.22, H(X_RIN)),
        (5, 0.34, D(X_RIN)),
        (5, 0.62, D(X_RIN)),
        (5, 0.74, H(X_RIN)),
        (5, 0.84, H(X_DRY)),
        (5, 0.94, D(X_DRY)),
        (5, 1.00, D(X_DRY)),
    ]
    for b, u, off in stops:
        key(cas, F(b, u), "location", P(*off), linear=True)


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = materials()

    # the room: floor, backdrop, steel bench under the tanks
    box("clean_floor", (-1700.0, -8.0, -900.0), (1900.0, 0.0, 0.0), m["floor"], root)
    box("clean_backdrop", (-1700.0, 0.0, -900.0), (1900.0, 1300.0, -870.0), m["wall"], root)
    box("clean_bench", (-1500.0, 180.0, -420.0), (1750.0, 300.0, 0.0), m["bench"], root)

    tank("spm", X_SPM, m["spm"], m, root)
    tank("dhf", X_DHF, m["dhf"], m, root)
    tank("sc1", X_SC1, m["sc1"], m, root)
    tank("sc2", X_SC2, m["sc2"], m, root)
    tank("rinse", X_RIN, m["uw"], m, root)

    # spin dryer hood at the right end, open at the front
    box("clean_hood_top", (1300.0, 1000.0, -360.0), (1600.0, 1040.0, 0.0), m["hood"], root)
    box("clean_hood_l", (1300.0, 300.0, -360.0), (1320.0, 1040.0, 0.0), m["hood"], root)
    box("clean_hood_r", (1580.0, 300.0, -360.0), (1600.0, 1040.0, 0.0), m["hood"], root)
    box("clean_hood_back", (1300.0, 300.0, -380.0), (1600.0, 1040.0, -360.0), m["hood"], root)

    cas = carrier(m, root)
    W["carrier"] = cas
    route(cas)

    # bubbles in the two hot tanks, a rinse stream into the last tank
    rise(root, "spm_bub", (X_SPM - 100.0, 330.0, -150.0), 6, 14.0, m["bub"], 1, 0.40, 0.95, 80, h=300.0, drift=(20.0, 0.0))
    rise(root, "sc1_bub", (X_SC1 - 60.0, 330.0, -150.0), 6, 14.0, m["bub"], 3, 0.40, 0.95, 80, h=300.0, drift=(20.0, 0.0))
    tube("clean_nozzle", (X_RIN, 960.0, -150.0), (X_RIN, 830.0, -150.0), 14.0, m["steel"], root)
    run(root, "rinse_stream", [(X_RIN, 950.0, -150.0), (X_RIN, 600.0, -150.0)], 5, 10.0, m["water"], 5, 0.35, 0.6, 40)

    # tags: a few per beat, pinned to the part each one names
    tags = {
        0: [("wafer carrier", (X_SPM + 160.0, 1000.0, -240.0)),
            ("five chemistry tanks", (X_SC1, 760.0, -20.0)),
            ("rinse, then dry", (X_DRY, 1060.0, -20.0))],
        1: [("SPM: hot sulfuric + peroxide", (X_SPM, 850.0, -20.0)),
            ("strips photoresist and organics", (X_SPM + 120.0, 560.0, -10.0))],
        2: [("DHF: dilute hydrofluoric acid", (X_DHF, 850.0, -20.0)),
            ("strips the thin oxide", (X_DHF, 560.0, -10.0))],
        3: [("SC-1: ammonia + peroxide", (X_SC1, 850.0, -20.0)),
            ("removes particles and organics", (X_SC1, 560.0, -10.0))],
        4: [("SC-2: hydrochloric acid + peroxide", (X_SC2, 850.0, -20.0)),
            ("removes metal ions", (X_SC2, 560.0, -10.0))],
        5: [("ultrapure water rinse", (X_RIN, 850.0, -20.0)),
            ("spin dry in the hood", (X_DRY, 1060.0, -20.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera_path(root, POSES)
    return root


POSES = [
    frame((-300.0, 600.0, -150.0), 3900.0, yaw=0.35, pitch=0.22),  # 0: the whole bench
    frame((X_SPM + 80.0, 560.0, -150.0), 1000.0, yaw=0.45, pitch=0.18),  # 1: SPM
    frame((-850.0, 600.0, -150.0), 1500.0, yaw=0.45, pitch=0.18),  # 2: DHF, carried from SPM
    frame((X_SC1, 560.0, -150.0), 1000.0, yaw=0.45, pitch=0.18),  # 3: SC-1
    frame((X_SC2, 560.0, -150.0), 1000.0, yaw=0.45, pitch=0.18),  # 4: SC-2
    frame((1000.0, 600.0, -150.0), 1900.0, yaw=0.40, pitch=0.20),  # 5: rinse and dryer
]


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
