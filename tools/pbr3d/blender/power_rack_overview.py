"""The RACK POWER page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/power_rack_overview.py

Writes blender/power_rack_overview.blend and assets/power_rack_overview.glb. One beat is 8 s.

Three areas, far apart (parts and flows from power_rack_detail.py):
  the rack    an NVL72-class rack cut lengthwise, at the origin
  the row     eight closed racks under an overhead busway (x = ROW_X)
  the sidecar a compute rack with an 800 V sidecar power rack beside it (x = SIDE_X)

Beats (match the seven beats in diagrams_nodes/power/rack/overview.rs):
  0 an AI rack          the whole rack cut open: trays, shelves top and bottom, the busbar
  1 AC into the shelves the busway tap feeds the rack PDU; whips carry AC into each shelf
  2 DC down the busbar  the shelves' PSUs push ~50 V DC out through their clips onto the bar
  3 into every tray     each tray's clip takes DC off the bar into its power board
  4 thousands of amps   the bar packed with current, glowing warm
  5 a row of racks      eight racks under the busway, about 1 MW
  6 next: 800 V DC      an 800 V feed into a sidecar beside the compute rack
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, label, beat  # noqa: E402
import power_rack_detail as D  # noqa: E402
from power_rack_detail import (  # noqa: E402
    BP, BN, BUSWAY_Y, PDU_X, RY1, SHELVES, TRAYS, U, conveyor, frame, glide_camera, loop_run, rack_closed, slot_y, span,
)

NAME = "overview"
BEATS = 7
ROW_X = -14000.0
SIDE_X = 14000.0


def B(b, u0=0.0, u1=1.0):
    return [(F(b, u0), F(b, u1))]


def row(m, root, o, b):
    """Eight closed NVL72-class racks side by side under a busway, each fed by a tap-off box."""
    xs = [o[0] + (k - 3.5) * 620.0 for k in range(8)]
    D.floor(m, root, (o[0] - 2800, -1600), (o[0] + 2800, 800), "row_floor")
    for k, x in enumerate(xs):
        rack_closed(m, root, (x, 0.0, o[2]), "nvl", f"row{k}")
    yb = BUSWAY_Y
    box("row_busway", (xs[0] - 600, yb, o[2] - 700), (xs[-1] + 600, yb + 90, o[2] - 480), m["busway"], root)
    drops = []
    for k, x in enumerate(xs):
        box(f"row_tap{k}", (x - 70, yb - 150, o[2] - 680), (x + 70, yb, o[2] - 520), m["cabinet"], root)
        box(f"row_drop{k}", (x - 12, RY1 + 30, o[2] - 612), (x + 12, yb - 150, o[2] - 588), m["cable"], root)
        drops.append(((x, yb - 160, o[2] - 470), (x, RY1 + 40, o[2] - 470)))
    conveyor(root, "row_bus_ac", [((xs[0] - 560, yb + 45, o[2] - 470), (xs[-1] + 560, yb + 45, o[2] - 470))], 110.0, 16.0, m["ac"], b, 24)
    conveyor(root, "row_drop_ac", drops, 70.0, 13.0, m["ac"], b, 24)
    return xs


def sidecar(m, root, o, b):
    """A compute rack (left) and its 800 V sidecar power rack (right): a slim violet 800 V feed
    drops into the sidecar, a short copper link carries DC across into the compute rack."""
    D.floor(m, root, (o[0] - 1600, -1600), (o[0] + 1600, 800), "side_floor")
    rack_closed(m, root, (o[0] - 310.0, 0.0, o[2]), "nvl", "side_rack")
    _, sp = rack_closed(m, root, (o[0] + 310.0, 0.0, o[2]), "sidecar", "side_car")
    y_feed = RY1 + 420.0
    box("side_tray", (o[0] - 1500, y_feed - 20, o[2] - 420), (o[0] + 1500, y_feed, o[2] - 260), m["busway"], root)
    pts_hv = [(o[0] - 1500, y_feed + 18, o[2] - 340), (o[0] + 300, y_feed + 18, o[2] - 340)]
    D.tube("side_hv_a", pts_hv[0], pts_hv[1], 14.0, m["hv_cable"], root, 12)
    D.wire("side_hv_drop", D.curve_pts((o[0] + 300, y_feed + 18, o[2] - 340), (o[0] + 360, RY1 + 30, o[2] - 340), (90.0, 0, 0), 8), 14.0, m["hv_cable"], root)
    box("side_link", (o[0] - 200, RY1 + 30, o[2] - 260), (o[0] + 200, RY1 + 70, o[2] - 200), m["copper"], root)
    conveyor(root, "side_hv", [(pts_hv[0], pts_hv[1])], 220.0, 13.0, m["hv"], b, 24)
    loop_run(root, "side_hvd", D.curve_pts((o[0] + 300, y_feed + 18, o[2] - 340), (o[0] + 360, RY1 + 30, o[2] - 340), (90.0, 0, 0), 8), 2, 13.0, m["hv"], b, 48)
    conveyor(root, "side_link_dc", [((o[0] + 200, RY1 + 90, o[2] - 230), (o[0] - 200, RY1 + 90, o[2] - 230))], 40.0, 12.0, m["dc"], b, 12)
    return sp, y_feed


def build():
    m, root = D.setup(NAME, beats=BEATS)
    R = D.Rack(m, root, name="rk")
    R.spin_fans(F(0, 0), F(5, 0))
    # flows, beat by beat
    R.ac_flow(B(0) + B(1))
    R.psu_dc(B(0) + B(2))
    R.bar_flow(B(0) + B(2) + B(3), name="bar")
    R.taps(B(0) + B(3))
    R.board_flow(B(3))
    R.bar_flow(B(4), spacing=30.0, size=7.0, period=10, name="barx")
    R.taps(B(4), spacing=16.0, size=5.0, period=10, name="tapx")
    R.bar_glow(B(4, 0.15))
    R.mark_slots(SHELVES, B(1, 0.1, 0.9), "mk_sh", x0=-600.0, x1=480.0)
    xs = row(m, root, (ROW_X, 0.0, 0.0), B(5))
    sp, y_feed = sidecar(m, root, (SIDE_X, 0.0, 0.0), B(6))

    ys = lambda i: slot_y(i) + U / 2  # noqa: E731
    xb = (BP[0] + BP[1]) / 2
    # 0 the rack
    label("power shelves: 4 at the top", (-200.0, ys(SHELVES[6]), 0.0), root, beat(0))
    label("power shelves: 4 at the bottom", (-200.0, ys(SHELVES[1]), 0.0), root, beat(0))
    label("compute trays", (-200.0, ys(27), 0.0), root, beat(0))
    label("NVLink switch trays", (-200.0, ys(17), 0.0), root, beat(0))
    label("copper busbar down the back", (xb, ys(22), 0.0), root, beat(0))
    # 1 AC in
    label("busway tap-off box", (495.0, BUSWAY_Y - 75, -190.0), root, beat(1))
    label("rack PDU: breakers, outlets", (PDU_X[0], R.breaker_y[2], -129.0), root, beat(1))
    label("AC whip into each shelf", R.whips[SHELVES[5]][4], root, beat(1))
    label("power shelf: AC inlet", (480.0, ys(SHELVES[6]), -223.0), root, beat(1))
    # 2 DC down the bar
    label("PSU makes ~50 V DC", (-200.0, slot_y(SHELVES[5]) + 34, 0.0), root, beat(2))
    label("shelf clips onto the bar", (BP[0] - 4, slot_y(SHELVES[4]) + 29, 0.0), root, beat(2))
    label("+50 V busbar", (xb, ys(27), 0.0), root, beat(2))
    label("return bar", ((BN[0] + BN[1]) / 2, ys(23), 0.0), root, beat(2))
    # 3 into the trays
    label("clip grips the bar", (BP[0] - 4, ys(18), 0.0), root, beat(3))
    label("compute tray", (230.0, ys(14) + 15, 0.0), root, beat(3))
    label("converted again on the board", (380.0, slot_y(19) + 27, 0.0), root, beat(3))
    # 4 amps
    label("~2,400 A at 120 kW", (xb, ys(27), 0.0), root, beat(4))
    label("copper bar, not a cable", ((BN[0] + BN[1]) / 2, ys(25), 0.0), root, beat(4))
    label("every clip carries its share", (BP[0] - 4, ys(26), 0.0), root, beat(4))
    # 5 a row
    label("one NVL72-class rack ~120 kW", (xs[3], slot_y(20), 6.0), root, beat(5))
    label("overhead busway", (xs[6], BUSWAY_Y + 90, -470.0), root, beat(5))
    label("8 racks: about 1 MW", (xs[1], RY1 + 30, 0.0), root, beat(5))
    # 6 800 V
    label("800 V DC feed", (SIDE_X - 900.0, y_feed + 32, -340.0), root, beat(6))
    label("sidecar power rack", sp["conv"], root, beat(6))
    label("compute rack", (SIDE_X - 310.0, slot_y(20), 6.0), root, beat(6))
    label("DC link into the rack", (SIDE_X, RY1 + 70, -230.0), root, beat(6))

    glide_camera(root, [
        frame((-640.0, 0.0, -300.0), (660.0, BUSWAY_Y + 90, 0.0), 0.22, 0.06, pad=1.0),
        frame((200.0, slot_y(SHELVES[4]) - 10, -300.0), (690.0, BUSWAY_Y + 90, 0.0), 0.55, 0.06, pad=1.04),
        frame((-420.0, slot_y(18), -100.0), (600.0, slot_y(SHELVES[6]), 0.0), 0.32, 0.04, pad=1.02),
        frame((150.0, slot_y(13), -150.0), (600.0, slot_y(21), 0.0), 0.30, 0.04, pad=1.04),
        frame((400.0, slot_y(23), -90.0), (580.0, slot_y(29), 5.0), 0.40, 0.10, pad=1.04),
        frame((ROW_X - 2800, 0.0, -1200.0), (ROW_X + 2800, BUSWAY_Y + 100, 0.0), -0.45, 0.16, pad=1.02),
        frame((SIDE_X - 1300, 0.0, -1200.0), (SIDE_X + 700, y_feed + 40, 0.0), 0.42, 0.14, pad=1.04),
    ])
    return root


if __name__ == "__main__":
    build()
    D.done(NAME)
