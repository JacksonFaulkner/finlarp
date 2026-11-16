"""The RACK POWER node's nine numbered sections (POWER tab), in the picture-and-panel template
(docs/diagram-pages.md). Section N illustrates heading N of tui/src/screens/diagrams_pages/PWR_RACK.txt,
so the menu title, the text panel and the picture agree; heading 10 (Sources) is text only. Three
beats each, one beat is 8 s.

Each section replays overview beats (power_rack_overview.py: the same rack, row and sidecar, with their
beads on the busbar, whips and busway) under a camera and tags chosen for its heading, as the zoom-ins
do (power_rack_zooms.py, which owns the replay and the export).

Run from the repo root, one section per run (or several in one process):

    blender -b --factory-startup --python tools/pbr3d/blender/power_rack_sections.py -- <n>

Writes blender/power_rack_section_<n>.blend and assets/power_rack_section_<n>.glb.

  1 what happens       AC in at the top, DC down the back
  2 the parts          PDU, POWER SHELF, PSU, BUSBAR; KILOWATTS PER RACK, 800 VDC, SIDECAR
  3 power, in order    PDU, shelves, PSUs make DC, busbar, tray clips
  4 why so many amps   ~2,400 A on a copper bar
  5 shelves and redundancy  six 5.5 kW PSUs per 33 kW shelf, swapped while running
  6 kilowatts per rack keeps rising  one rack, then a row of racks
  7 800 V DC           the sidecar and the DC link
  8 who makes it       the shelves, busways and reference designs
  9 chokepoints        thousands of amps, new DC safety practice
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from power_rack_detail import BP, BN, BUSWAY_Y, PDU_X, RY1, SHELVES, frame, slot_y  # noqa: E402
from power_rack_zooms import play, ROW_X, SIDE_X, Y_FEED, XB, XN, ys  # noqa: E402

PAGE = "power_rack"


def sections():
    """section number -> three beats of (overview beat to replay, camera pose, [(tag, point)])."""
    top, bottom = SHELVES[6], SHELVES[1]
    return {
        1: [
            (0, frame((-640.0, 0.0, -300.0), (660.0, BUSWAY_Y + 90.0, 0.0), 0.22, 0.06, 1.0),
             [("power shelves at the top", (-200.0, ys(top), 0.0)), ("copper busbar down the back", (XB, ys(22), 0.0))]),
            (1, frame((-200.0, slot_y(SHELVES[5]) - 120.0, -420.0), (600.0, BUSWAY_Y + 100.0, -60.0), 0.40, 0.10),
             [("AC whip into each shelf", (480.0, ys(top), -223.0))]),
            (2, frame((-260.0, slot_y(SHELVES[4]) - 60.0, -200.0), (600.0, slot_y(top) + 80.0, 0.0), 0.30, 0.05),
             [("PSU makes ~50 V DC", (-200.0, slot_y(SHELVES[5]) + 34, 0.0)), ("+50 V busbar", (XB, ys(27), 0.0))]),
        ],
        2: [
            (0, frame((-420.0, -40.0, -300.0), (420.0, slot_y(37) + 120.0, 0.0), 0.30, 0.06),
             [("compute trays", (-200.0, ys(27), 0.0)), ("NVLink switch trays", (-200.0, ys(17), 0.0))]),
            (1, frame((PDU_X[0] - 300.0, BUSWAY_Y - 200.0, -420.0), (PDU_X[0] + 300.0, BUSWAY_Y + 100.0, 0.0), 0.50, 0.10),
             [("busway tap-off box", (495.0, BUSWAY_Y - 75, -190.0)), ("rack PDU: breakers, outlets", (PDU_X[0], BUSWAY_Y - 150.0, -129.0))]),
            (6, frame((SIDE_X - 1300.0, 0.0, -1200.0), (SIDE_X + 700.0, Y_FEED + 40.0, 0.0), 0.42, 0.14, 1.04),
             [("800 V DC feed", (SIDE_X - 900.0, Y_FEED + 32.0, -340.0)), ("sidecar power rack", (SIDE_X + 310.0, slot_y(20), 6.0))]),
        ],
        3: [
            (1, frame((300.0, slot_y(top) - 120.0, -330.0), (560.0, BUSWAY_Y + 100.0, -60.0), 0.50, 0.10),
             [("1 AC from the PDU", (495.0, BUSWAY_Y - 75, -190.0)), ("2 shelf splits it", (480.0, ys(top), -223.0))]),
            (2, frame((-260.0, slot_y(SHELVES[4]) - 60.0, -200.0), (600.0, slot_y(top) + 80.0, 0.0), 0.30, 0.05),
             [("3 PSUs make ~50 V DC", (-200.0, slot_y(SHELVES[5]) + 34, 0.0)), ("4 busbar carries it", (XB, ys(27), 0.0))]),
            (3, frame((BP[0] - 40.0, ys(18) - 40.0, -120.0), (BN[1] + 40.0, ys(26) + 40.0, 0.0), 0.20, 0.05),
             [("5 tray clip takes DC", (BP[0] - 4, ys(18), 0.0)), ("converted again on the board", (380.0, slot_y(19) + 27, 0.0))]),
        ],
        4: [
            (4, frame((BP[0] - 60.0, ys(14), -160.0), (BN[1] + 60.0, ys(27), 0.0), 0.30, 0.08),
             [("~2,400 A at 120 kW", (XB, ys(27), 0.0)), ("copper bar, not a cable", (XN, ys(25), 0.0))]),
            (4, frame((BP[0] - 60.0, ys(24), -120.0), (BN[1] + 60.0, ys(30), 0.0), 0.20, 0.06),
             [("every clip carries its share", (BP[0] - 4, ys(26), 0.0))]),
            (4, frame((-420.0, 0.0, -300.0), (600.0, slot_y(29), 0.0), 0.32, 0.06),
             [("thousands of amps", (XB, ys(27), 0.0))]),
        ],
        5: [
            (1, frame((-600.0, slot_y(top) - 30.0, -560.0), (480.0, slot_y(top) + 60.0, 0.0), 0.40, 0.12),
             [("power shelves: 4 at the top", (-200.0, ys(top), 0.0))]),
            (1, frame((-600.0, slot_y(bottom) - 30.0, -560.0), (480.0, slot_y(bottom) + 60.0, 0.0), 0.40, 0.12),
             [("power shelves: 4 at the bottom", (-200.0, ys(bottom), 0.0))]),
            (1, frame((-300.0, slot_y(SHELVES[5]) - 60.0, -400.0), (300.0, slot_y(SHELVES[5]) + 60.0, 0.0), 0.30, 0.10),
             [("6 PSUs x 5.5 kW = 33 kW", (-200.0, ys(SHELVES[5]), 0.0))]),
        ],
        6: [
            (0, frame((-420.0, -40.0, -300.0), (420.0, slot_y(37) + 120.0, 0.0), 0.30, 0.06),
             [("~120 kW", (-200.0, ys(27), 0.0))]),
            (5, frame((ROW_X - 2800.0, 0.0, -1200.0), (ROW_X + 2800.0, BUSWAY_Y + 100.0, 0.0), -0.45, 0.16, 1.02),
             [("8 racks: about 1 MW", (ROW_X - 620.0, RY1 + 30.0, 0.0)), ("overhead busway", (ROW_X, BUSWAY_Y + 90, -470.0))]),
            (5, frame((ROW_X - 330.0, -40.0, -330.0), (ROW_X + 330.0, slot_y(37) + 120.0, 0.0), 0.30, 0.04),
             [("one NVL72-class rack ~120 kW", (ROW_X, slot_y(20), 6.0))]),
        ],
        7: [
            (6, frame((SIDE_X - 1300.0, 0.0, -1200.0), (SIDE_X + 700.0, Y_FEED + 40.0, 0.0), 0.42, 0.14, 1.04),
             [("800 V DC feed", (SIDE_X - 900.0, Y_FEED + 32.0, -340.0)), ("sidecar power rack", (SIDE_X + 310.0, slot_y(20), 6.0))]),
            (6, frame((SIDE_X - 260.0, RY1 - 40.0, -330.0), (SIDE_X + 260.0, RY1 + 120.0, -160.0), 0.30, 0.10),
             [("DC link into the rack", (SIDE_X, RY1 + 70.0, -230.0))]),
            (6, frame((SIDE_X - 200.0, slot_y(4), -300.0), (SIDE_X + 500.0, slot_y(12), 0.0), 0.40, 0.08),
             [("compute rack", (SIDE_X - 310.0, slot_y(20), 6.0))]),
        ],
        8: [
            (0, frame((-640.0, 0.0, -300.0), (660.0, BUSWAY_Y + 90.0, 0.0), 0.22, 0.06, 1.0),
             [("power shelves", (-200.0, ys(top), 0.0)), ("compute trays", (-200.0, ys(27), 0.0))]),
            (5, frame((ROW_X - 2800.0, 0.0, -1200.0), (ROW_X + 2800.0, BUSWAY_Y + 100.0, 0.0), -0.45, 0.16, 1.02),
             [("overhead busway", (ROW_X, BUSWAY_Y + 90, -470.0))]),
            (6, frame((SIDE_X - 1300.0, 0.0, -1200.0), (SIDE_X + 700.0, Y_FEED + 40.0, 0.0), 0.42, 0.14, 1.04),
             [("sidecar power rack", (SIDE_X + 310.0, slot_y(20), 6.0))]),
        ],
        9: [
            (4, frame((BP[0] - 60.0, ys(14), -160.0), (BN[1] + 60.0, ys(27), 0.0), 0.30, 0.08),
             [("thousands of amps", (XB, ys(27), 0.0))]),
            (3, frame((BP[0] - 40.0, ys(18) - 40.0, -120.0), (BN[1] + 40.0, ys(26) + 40.0, 0.0), 0.20, 0.05),
             [("clips must grip the bar", (BP[0] - 4, ys(18), 0.0))]),
            (6, frame((SIDE_X - 260.0, RY1 - 40.0, -330.0), (SIDE_X + 260.0, RY1 + 120.0, -160.0), 0.30, 0.10),
             [("new DC safety practice", (SIDE_X, RY1 + 70.0, -230.0))]),
        ],
    }


def build(n):
    play(f"section_{n}", sections()[n], page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ns = [int(a) for a in argv] or list(range(1, 10))
    for n in ns:
        if n not in range(1, 10):
            raise SystemExit("usage: ... -- <1..9>")
        build(n)
