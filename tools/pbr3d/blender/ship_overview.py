"""The SHIP node page's overview (the BOARD-to-SHIP end of the back end), in the picture-and-panel
template (docs/diagram-pages.md). Modelled on power_grid_overview.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/ship_overview.py

Writes blender/ship_overview.blend and assets/ship_overview.glb. One beat is 8 s.

One diorama, left to right: an ODM assembly line (conveyor, board, GPU and CPU modules), a
liquid-cooled NVL72-style rack with its coolant distribution units either side, a factory loop
that beads cool through, a road past a barrier gate and a booth, a crated rack on a flatbed truck,
and a data hall at the far end. Gold beads ride the product flow; cyan beads ride the coolant.

Beats (match the six beats in diagrams_nodes/ship/overview.rs):
  0 assembly  the ODM mounts tested GPU and CPU modules on a board
  1 builders  the ODM assembles racks; the OEM designs, sells under warranty
  2 rack      one liquid-cooled rack: 72 GPUs and 36 CPUs, NVLink through the rack
  3 test      the coolant loop, leak and load tests in the factory before shipping
  4 export    the gate: US license review for advanced chips bound for China
  5 ship      the crated rack on a truck to the buyer's data hall

Static objects stay on in every beat, as in the POWER overview; only the beads and the tags are
switched per beat. The camera holds one pose per beat (power_grid_detail.camera_path).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import mat, box, tube, disc, label, beat  # noqa: E402
from sand_zooms import start  # noqa: E402
from power_grid_detail import frame, camera_path, run, finish  # noqa: E402

PAGE = "ship"
NAME = "overview"
BEATS = 6

LABEL = label  # swapped by ship_zooms.py if it is ever written
CAMERA = camera_path
EXTRA = None
W = {}  # the scene's points, for later scripts


def materials():
    return {
        "floor": mat("sh_floor", (0.40, 0.41, 0.43), rough=0.8),
        "road": mat("sh_road", (0.16, 0.16, 0.18), rough=0.9),
        "hall": mat("sh_hall", (0.78, 0.78, 0.75), rough=0.8),
        "steel": mat("sh_steel", (0.55, 0.57, 0.60), metal=0.7, rough=0.4),
        "board": mat("sh_board", (0.10, 0.36, 0.22), rough=0.5),
        "gpu": mat("sh_gpu", (0.06, 0.06, 0.07), metal=0.3, rough=0.4),
        "cpu": mat("sh_cpu", (0.55, 0.56, 0.58), metal=0.5, rough=0.35),
        "lid": mat("sh_lid", (0.80, 0.62, 0.30), metal=0.9, rough=0.3),
        "rack": mat("sh_rack", (0.07, 0.07, 0.08), metal=0.3, rough=0.5),
        "tray": mat("sh_tray", (0.30, 0.31, 0.33), metal=0.6, rough=0.4),
        "switch": mat("sh_switch", (0.20, 0.42, 0.30), metal=0.4, rough=0.45),
        "led": mat("sh_led", (0.3, 1.0, 0.5), emit=(0.3, 1.0, 0.5), strength=3.0),
        "pipe": mat("sh_pipe", (0.62, 0.64, 0.67), metal=0.8, rough=0.35),
        "cdu": mat("sh_cdu", (0.70, 0.72, 0.74), metal=0.4, rough=0.45),
        "gate": mat("sh_gate", (0.85, 0.20, 0.15), rough=0.4),
        "post": mat("sh_post", (0.86, 0.86, 0.84), rough=0.25),
        "booth": mat("sh_booth", (0.25, 0.27, 0.30), rough=0.6),
        "crate": mat("sh_crate", (0.62, 0.46, 0.28), rough=0.9),
        "truck": mat("sh_truck", (0.20, 0.30, 0.45), metal=0.3, rough=0.5),
        "tyre": mat("sh_tyre", (0.08, 0.08, 0.08), rough=0.9),
        "cool": mat("sh_cool", (0.5, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=6.0),
        "bead": mat("sh_bead", (1.0, 0.8, 0.3), emit=(1.0, 0.8, 0.3), strength=6.0),
    }


# poses: (centre, size across, yaw, pitch) per beat, through power_grid_detail.frame
POSES = [
    frame((-950.0, 200.0, 0.0), 1200.0, 0.30, 0.20, pad=1.0),
    frame((-300.0, 500.0, 0.0), 3200.0, 0.10, 0.12),
    frame((0.0, 1000.0, 0.0), 2400.0, 0.40, 0.18),
    frame((-100.0, 700.0, 0.0), 1900.0, -0.50, 0.22),
    frame((1400.0, 350.0, 0.0), 1600.0, 0.25, 0.15),
    frame((2100.0, 450.0, 0.0), 3000.0, 0.20, 0.18),
]


def build_line(m, root):
    """The ODM assembly line: a conveyor, a board, two GPU modules and a CPU between them."""
    box("sh_belt", (-1500, 110, -190), (-380, 130, 190), m["steel"], root)
    for x in (-1450, -420):
        for z in (-160, 160):
            box("sh_leg", (x - 25, 0, z - 25), (x + 25, 110, z + 25), m["steel"], root)
    box("sh_board", (-1200, 130, -210), (-600, 160, 210), m["board"], root)
    for name, x, lid in (("gpu_a", -1080, True), ("cpu", -920, False), ("gpu_b", -760, True)):
        mm = m["cpu"] if name == "cpu" else m["gpu"]
        box(f"sh_{name}", (x - 55, 160, -75), (x + 55, 185, 75), mm, root)
        if lid:
            box(f"sh_{name}_lid", (x - 40, 185, -60), (x + 40, 190, 60), m["lid"], root)


def build_rack(m, root):
    """An NVL72-style rack: 27 trays (18 compute, 9 NVLink switch) with status LEDs, and a coolant
    distribution unit (CDU) at each end of the loop."""
    box("sh_rack", (-330, 0, -520), (330, 2000, 520), m["rack"], root)
    pitch = 2000.0 / 28
    for s in range(27):
        y0 = 30 + s * pitch
        switch = 9 <= s <= 17
        box(f"sh_tray{s}", (-300, y0, 520), (300, y0 + 55, 560), m["switch" if switch else "tray"], root)
        box(f"sh_led{s}", (-280, y0 + 20, 560), (-250, y0 + 30, 566), m["led"], root)
    box("sh_cdu_r", (560, 0, -260), (900, 800, 260), m["cdu"], root)
    box("sh_cdu_l", (-900, 0, -260), (-560, 800, 260), m["cdu"], root)


def loop_path():
    """The coolant loop: out of the right CDU, up the right side, across the top, down the left."""
    return [(560, 120, 0), (400, 120, 0), (400, 1950, 0), (-400, 1950, 0), (-400, 120, 0), (-560, 120, 0)]


def build_loop(m, root):
    pts = loop_path()
    for i in range(len(pts) - 1):
        tube(f"sh_pipe{i}", pts[i], pts[i + 1], 22, m["pipe"], root)


def build_gate(m, root):
    """A barrier across the road, a booth beside it."""
    for z in (-260, 240):
        box(f"sh_post_{z}", (1390, 0, z), (1410, 600, z + 20), m["post"], root)
    box("sh_arm", (1390, 600, -240), (1410, 640, 240), m["gate"], root)
    box("sh_booth", (1300, 0, 260), (1480, 300, 420), m["booth"], root)


def build_truck(m, root):
    """A flatbed with a cab, the crate on the bed, and wheels on both sides."""
    box("sh_bed", (1750, 60, -200), (2350, 120, 200), m["truck"], root)
    box("sh_cab", (1600, 60, -200), (1720, 260, 200), m["truck"], root)
    box("sh_crate", (1900, 120, -170), (2280, 1320, 170), m["crate"], root)
    for x in (1700, 2300):
        for z in (-200, 200):
            w = disc(f"sh_wheel_{x}_{z}", (x, 70, z), 70, 60, m["tyre"], root)
            w.rotation_euler = (1.5707963, 0.0, 0.0)  # axis along the depth, so the wheel faces the camera


def build_hall(m, root):
    box("sh_hall", (2600, 0, -500), (3400, 700, 500), m["hall"], root)


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = materials()
    W.clear()
    box("sh_ground", (-2000, -12, -900), (3600, 0, 900), m["floor"], root)
    box("sh_road", (600, 0, -220), (3000, 4, 220), m["road"], root)
    build_line(m, root)
    build_rack(m, root)
    build_loop(m, root)
    build_gate(m, root)
    build_truck(m, root)
    build_hall(m, root)

    # beat 0: product flow along the belt
    run(root, "sh_prod", [(-1450, 205, 0), (-420, 205, 0)], 3, 16, m["bead"], 0, 0.0, 0.6, 90)
    # beat 2: the NVLink fabric ties the trays together; beads run up the front
    run(root, "sh_nv", [(0, 60, 600), (0, 1960, 600)], 5, 16, m["bead"], 2, 0.0, 0.6, 80)
    # beat 3: coolant around the loop
    run(root, "sh_cool", loop_path(), 6, 20, m["cool"], 3, 0.05, 0.7, 90)
    # beat 5: racks leave the gate for the data hall
    run(root, "sh_ship", [(1400, 200, 0), (2600, 200, 0)], 5, 16, m["bead"], 5, 0.05, 0.6, 110)
    if EXTRA:
        EXTRA(m, root)

    tags = {
        0: [("ODM: physical assembly", (-1000, 240, 0)), ("GPU module", (-1080, 205, 140)),
            ("board", (-900, 170, 230))],
        1: [("ODM: assembles the rack", (-1000, 420, 0)), ("OEM: designs and sells", (0, 2080, 0)),
            ("cooling and power for the rack", (700, 900, 0))],
        2: [("72 GPUs, 36 CPUs", (-420, 1700, 560)), ("one liquid-cooled rack", (0, 1000, 620)),
            ("NVLink ties the rack", (300, 1850, 620))],
        3: [("coolant loop", (420, 1000, 40)), ("connectors leaked in ramp", (-560, 200, 0)),
            ("leak and load tests", (560, 150, 300))],
        4: [("export: US license review", (1400, 700, 0)), ("China: case-by-case", (1400, 560, 300))],
        5: [("crated rack, by truck", (2080, 1340, 0)), ("buyer's data hall", (2990, 720, 0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            LABEL(text, pos, root, beat(i))
    CAMERA(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
