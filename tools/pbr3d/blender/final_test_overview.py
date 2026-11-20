"""The FINAL TEST node page's overview (BACK END tab), in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/final_test_overview.py

Writes blender/final_test_overview.blend and assets/final_test_overview.glb. One beat is 8 s.

One test line, left to right: a tray of packaged parts, a handler gantry that presses one part into a
socket on a load board, the ATE test head with its cable, a burn-in oven, a system-level test board,
a speed-bin row with a fmax bell over it, and a pallet of sealed trays. Parts ride an overhead rail
from the oven to the bins and the pallet.

Beats (match the seven beats in diagrams_nodes/final_test/overview.rs):
  0 line        the whole line: packaged parts in a tray, the handler above them
  1 handler     the handler lifts a part from the tray and presses it into the socket
  2 ATE         the test head runs its program over the load board cable; lights step
  3 burn-in     the oven racks glow; heat rises off the oven top; parts ride the rail in
  4 SLT         a part docks at the system test board; the monitor shows a workload
  5 bins        parts drop into the speed bins; the fmax bell lights over them
  6 ship        the sealed trays are stacked on the pallet for shipment
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, mat, box, ball, tube, empty, key, show, label, beat  # noqa: E402
from sand_zooms import start, camera, finish  # noqa: E402

PAGE = "final_test"
NAME = "overview"
BEATS = 7

# Camera poses per beat: (target, distance, yaw, pitch). The distance is a subject width over the
# left pane, as in power_grid_detail.frame().
PANE = 0.53


def pose(c, size, yaw=0.35, pitch=0.22):
    return (tuple(c), max(size / PANE, 90.0), yaw, pitch)


POSES = [
    pose((510.0, 300.0, 0.0), 3900.0, 0.35, 0.22),
    pose((-800.0, 400.0, 0.0), 1400.0, 0.50, 0.20),
    pose((-120.0, 230.0, 0.0), 1100.0, 0.35, 0.20),
    pose((600.0, 280.0, 0.0), 1100.0, 0.40, 0.20),
    pose((1190.0, 140.0, 0.0), 1100.0, 0.45, 0.20),
    pose((1750.0, 200.0, 0.0), 1000.0, 0.45, 0.20),
    pose((2150.0, 150.0, 0.0), 1000.0, 0.30, 0.20),
]

# Handler head centres (poly coordinates): over the tray, at the tray, lifted, over the socket, pressed.
HEAD_OVER_TRAY = (-1250.0, 760.0, 0.0)
HEAD_PICK = (-1250.0, 150.0, 0.0)
HEAD_OVER_SOCKET = (-520.0, 760.0, 0.0)
HEAD_PRESS = (-520.0, 160.0, 0.0)

# Overhead rail: parts ride at this height (poly Y), past the oven, the SLT board and the bins.
RAIL_Y = 120.0
SLT_X = 1010.0
PALLET_X = 2250.0
BINS = ((1600.0, "bin_a", "A top"), (1700.0, "bin_b", "B mid"), (1800.0, "bin_c", "C low"), (1900.0, "bin_x", "X scrap"))
PART_Z = (-60.0, 0.0, 60.0)


def materials():
    return {
        "floor": mat("ft_floor", (0.42, 0.43, 0.45), rough=0.85),
        "tray": mat("ft_tray", (0.14, 0.15, 0.17), rough=0.9),
        "pkg": mat("ft_pkg", (0.07, 0.07, 0.08), metal=0.2, rough=0.35),
        "lid": mat("ft_lid", (0.55, 0.56, 0.60), metal=0.8, rough=0.3),
        "steel": mat("ft_steel", (0.35, 0.37, 0.42), metal=0.6, rough=0.4),
        "steel_dark": mat("ft_steel_dark", (0.16, 0.17, 0.20), metal=0.5, rough=0.5),
        "board": mat("ft_board", (0.08, 0.32, 0.16), rough=0.6),
        "socket": mat("ft_socket", (0.12, 0.12, 0.14), rough=0.5),
        "cable": mat("ft_cable", (0.04, 0.04, 0.05), rough=0.7),
        "panel": mat("ft_panel", (0.20, 0.22, 0.26), metal=0.4, rough=0.4),
        "led_g": mat("ft_led_g", (0.3, 1.0, 0.45), emit=(0.3, 1.0, 0.45), strength=8.0),
        "glass": mat("ft_glass", (0.6, 0.8, 0.9), rough=0.1, alpha=0.3),
        "hot": mat("ft_hot", (1.0, 0.4, 0.1), emit=(1.0, 0.45, 0.12), strength=6.0),
        "heat": mat("ft_heat", (1.0, 0.5, 0.2), emit=(1.0, 0.55, 0.25), strength=3.0, alpha=0.55),
        "bead": mat("ft_bead", (1.0, 0.85, 0.3), emit=(1.0, 0.85, 0.3), strength=9.0),
        "screen": mat("ft_screen", (0.4, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=4.0),
        "bell": mat("ft_bell", (0.25, 0.55, 0.9), rough=0.5),
        "bin_a": mat("ft_bin_a", (0.30, 0.75, 0.40), rough=0.6),
        "bin_b": mat("ft_bin_b", (0.90, 0.80, 0.25), rough=0.6),
        "bin_c": mat("ft_bin_c", (0.90, 0.50, 0.20), rough=0.6),
        "bin_x": mat("ft_bin_x", (0.70, 0.20, 0.20), rough=0.6),
        "pallet": mat("ft_pallet", (0.55, 0.40, 0.25), rough=0.9),
        "sealed": mat("ft_sealed", (0.85, 0.85, 0.82), rough=0.6),
        "rail": mat("ft_rail", (0.50, 0.52, 0.55), metal=0.7, rough=0.4),
    }


def keys(obj, pts):
    """Absolute positions (poly points) at frames: linear keys on obj's location."""
    for f, pos in pts:
        key(obj, f, "location", P(*pos), linear=True)


def build_line(root, m):
    box("floor", (-1500.0, -40.0, -700.0), (2500.0, 0.0, 700.0), m["floor"], root)

    # packaged parts in a JEDEC-style tray (the handler picks from here)
    box("tray", (-1330.0, 0.0, -200.0), (-1170.0, 50.0, 200.0), m["tray"], root)
    for i, z in enumerate((-120.0, 0.0, 120.0)):
        box(f"tray_pkg{i}", (-1300.0, 50.0, z - 45.0), (-1200.0, 70.0, z + 45.0), m["pkg"], root)

    # handler gantry, and the head that carries the part (its children are built at the origin)
    box("gantry_l", (-1320.0, 0.0, -120.0), (-1280.0, 900.0, 120.0), m["steel"], root)
    box("gantry_r", (-340.0, 0.0, -120.0), (-300.0, 900.0, 120.0), m["steel"], root)
    box("gantry_bar", (-1320.0, 880.0, -120.0), (-300.0, 920.0, 120.0), m["steel"], root)
    head = empty("handler_head", root)
    box("head_body", (-60.0, -50.0, -60.0), (60.0, 50.0, 60.0), m["steel"], head)
    tube("head_nozzle", (0.0, -50.0, 0.0), (0.0, -72.0, 0.0), 9.0, m["steel"], head)
    box("head_part", (-45.0, -100.0, -45.0), (45.0, -72.0, 45.0), m["pkg"], head)
    box("head_lid", (-30.0, -100.0, -30.0), (30.0, -96.0, 30.0), m["lid"], head)
    keys(head, [
        (0, HEAD_OVER_TRAY),
        (F(0, 0.9), HEAD_OVER_TRAY),
        (F(1, 0.0), HEAD_OVER_TRAY),
        (F(1, 0.15), HEAD_PICK),
        (F(1, 0.30), HEAD_OVER_TRAY),
        (F(1, 0.50), HEAD_OVER_SOCKET),
        (F(1, 0.70), HEAD_PRESS),
        (F(6, 1.0), HEAD_PRESS),
    ])

    # load board with its socket, and the ATE test head with its cable and lights
    box("load_board", (-640.0, 0.0, -140.0), (-400.0, 30.0, 140.0), m["board"], root)
    box("socket", (-590.0, 30.0, -70.0), (-450.0, 60.0, 70.0), m["socket"], root)
    tube("ate_cable", (-400.0, 15.0, 0.0), (-80.0, 15.0, 0.0), 14.0, m["cable"], root)
    box("test_head", (-80.0, 0.0, -200.0), (220.0, 380.0, 200.0), m["steel_dark"], root)
    box("ate_panel", (-60.0, 300.0, 200.0), (200.0, 360.0, 206.0), m["panel"], root)
    lights = empty("ate_lights", root)
    for i in range(4):
        ball(f"ate_led{i}", (-20.0 + i * 70.0, 330.0, 212.0), 12.0, m["led_g"], lights)
    show(lights, beat(2))
    for i in range(3):
        bead = ball(f"ate_bead{i}", (-400.0, 15.0, 0.0), 9.0, m["bead"], root)
        f0 = F(2, 0.05 + 0.25 * i)
        keys(bead, [(f0, (-400.0, 15.0, 0.0)), (f0 + 40, (-80.0, 15.0, 0.0))])
        show(bead, [(F(2, 0.0), F(3, 0.0))])

    # burn-in oven: the cabinet, the glass door, dark racks, and the same racks glowing in beat 3
    box("oven", (480.0, 0.0, -200.0), (760.0, 400.0, 200.0), m["steel_dark"], root)
    box("oven_door", (500.0, 20.0, 200.0), (740.0, 360.0, 212.0), m["glass"], root)
    hot = empty("oven_hot", root)
    for i in range(3):
        y0 = 60.0 + i * 110.0
        box(f"oven_rack{i}", (520.0, y0, -170.0), (720.0, y0 + 15.0, 170.0), m["steel"], root)
        box(f"oven_hot{i}", (516.0, y0 - 3.0, -174.0), (724.0, y0 + 18.0, 174.0), m["hot"], hot)
    show(hot, beat(3))
    for i in range(3):
        x = 600.0 + (i - 1) * 40.0
        hb = ball(f"oven_heat{i}", (x, 420.0, 0.0), 30.0, m["heat"], root)
        keys(hb, [(F(3, 0.1), (x, 420.0, 0.0)), (F(3, 0.9), (x, 560.0, 0.0))])
        show(hb, beat(3))

    # system-level test board, its monitor and the workload bars shown in beat 4
    box("slt_board", (980.0, 0.0, -180.0), (1220.0, 20.0, 180.0), m["board"], root)
    box("slt_chip", (1100.0, 20.0, -40.0), (1180.0, 50.0, 40.0), m["lid"], root)
    box("slt_sink", (1095.0, 50.0, -45.0), (1185.0, 120.0, 45.0), m["steel"], root)
    box("slt_monitor", (1270.0, 0.0, 40.0), (1400.0, 120.0, 70.0), m["panel"], root)
    bars = empty("slt_bars", root)
    for i, h in enumerate((40.0, 80.0, 60.0, 95.0, 70.0)):
        x0 = 1290.0 + i * 22.0
        box(f"slt_bar{i}", (x0, 20.0, 72.0), (x0 + 12.0, 20.0 + h, 76.0), m["screen"], bars)
    show(bars, beat(4))

    # overhead rail from the oven to the pallet, with pillars at its ends
    box("rail", (380.0, RAIL_Y - 5.0, -300.0), (2250.0, RAIL_Y + 5.0, 300.0), m["rail"], root)
    box("rail_pillar_l", (370.0, 0.0, -310.0), (390.0, RAIL_Y, -290.0), m["steel"], root)
    box("rail_pillar_r", (2230.0, 0.0, -310.0), (2250.0, RAIL_Y, -290.0), m["steel"], root)

    # speed bins with the fmax bell over them (beat 5)
    for bx, mat_name, _ in BINS:
        box(f"bin_{int(bx)}", (bx - 40.0, 0.0, -90.0), (bx + 40.0, 20.0, 90.0), m[mat_name], root)
    bell = empty("fmax_bell", root)
    box("bell_shelf", (1560.0, 140.0, -120.0), (1940.0, 150.0, 120.0), m["steel"], bell)
    box("bell_post_l", (1560.0, 0.0, -120.0), (1575.0, 140.0, -105.0), m["steel"], bell)
    box("bell_post_r", (1925.0, 0.0, -120.0), (1940.0, 140.0, -105.0), m["steel"], bell)
    for i in range(9):
        x0 = 1570.0 + i * 40.0
        h = 20.0 + 200.0 * math.exp(-((i - 4) ** 2) / (2 * 1.5 ** 2))
        box(f"bell{i}", (x0, 150.0, -60.0), (x0 + 30.0, 150.0 + h, 60.0), m["bell"], bell)
    show(bell, beat(5))

    # sealed trays on a pallet for shipment (beat 6)
    box("pallet_base", (2150.0, 0.0, -130.0), (2350.0, 30.0, 130.0), m["pallet"], root)
    box("pallet_trays", (2160.0, 30.0, -110.0), (2340.0, 95.0, 110.0), m["sealed"], root)


def build_parts(root, m):
    """Four parts ride the rail: docked at the SLT board in beat 4, dropped into the bins in beat 5,
    and set on the pallet in beat 6. Each part is a group built at the origin and keyed absolutely."""
    for i, z in enumerate(PART_Z):
        pk = empty(f"ride_part{i}", root)
        box(f"ride_body{i}", (-25.0, -10.0, -25.0), (25.0, 10.0, 25.0), m["pkg"], pk)
        box(f"ride_lid{i}", (-18.0, 10.0, -18.0), (18.0, 13.0, 18.0), m["lid"], pk)
        bx = BINS[i][0]
        keys(pk, [
            (0, (380.0, RAIL_Y, z)),
            (F(3, 0.0), (380.0, RAIL_Y, z)),
            (F(4, 0.4), (SLT_X, RAIL_Y, z)),
            (F(5, 0.2), (SLT_X, RAIL_Y, z)),
            (F(5, 0.5), (bx, RAIL_Y, z)),
            (F(5, 0.85), (bx, 30.0, z)),
            (F(6, 0.1), (bx, RAIL_Y, z)),
            (F(6, 0.5), (PALLET_X, RAIL_Y, z)),
            (F(6, 0.8), (PALLET_X, 105.0, z)),
        ])


def build_labels(root):
    tags = {
        0: [("packaged parts in trays", (-1250.0, 90.0, 0.0)), ("handler", (-1250.0, 960.0, 0.0))],
        1: [("handler presses the part", (-520.0, 300.0, 0.0)), ("socket: pins touch the balls", (-520.0, 70.0, 150.0))],
        2: [("test head: patterns, speed, power", (60.0, 420.0, 0.0)), ("load board routes channels", (-520.0, 25.0, -170.0))],
        3: [("burn-in oven: heat and voltage", (620.0, 440.0, 0.0))],
        4: [("system test: real board, real software", (1100.0, 260.0, 0.0))],
        5: [("speed bins by fmax", (1750.0, 470.0, 0.0))],
        6: [("sealed trays ship", (2250.0, 250.0, 0.0))],
    }
    for i, items in tags.items():
        for text, at in items:
            label(text, at, root, beat(i))


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = materials()
    build_line(root, m)
    build_parts(root, m)
    build_labels(root)
    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
