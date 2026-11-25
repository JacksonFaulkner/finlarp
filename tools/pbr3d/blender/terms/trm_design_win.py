"""TRM_DESIGN_WIN: the Terms-tab overview for a design win, built with the market-ledger kit.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_design_win.py

Left: an AI board in development with an empty socket. Centre: a supplier's chip slides into the
socket: that is the design win. Right: a years-long ramp of revenue, which only starts when the
product reaches volume production. A rival chip in beat 3 takes the socket at the next generation.

Beats:
  0 socket    a board in development, an empty socket
  1 win       the supplier's chip is picked for the design
  2 ramp      one to three years later, the product goes to volume and revenue ramps
  3 lose      next generation, a rival takes the socket and the revenue stream goes
  4 read      how to read design wins: cited early, revenue later, sticky sockets
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402
import kit_ledger as K  # noqa: E402

SLUG = "TRM_DESIGN_WIN"
BEATS = [
    ("A design win is a socket picked before the product exists",
     "Chip designers choose suppliers years before a product ships. Each slot on a board is a socket, and whoever gets "
     "picked for it is the design win. Nothing is sold yet."),
    ("The supplier's chip is designed into the board",
     "Once a customer picks a part for a product still in design, the supplier has a seat at the table. The part gets "
     "qualified, the board is laid out around it, and the customer is slow to change it."),
    ("Revenue follows one to three years later",
     "The product reaches volume production after a long development cycle, and revenue ramps with it. Companies cite "
     "design wins to show future revenue long before it appears in results."),
    ("Losing the socket at the next generation drops the stream",
     "When the next product generation comes, the socket can go to a rival. The revenue stream stops in one step, so "
     "a single lost design can outweigh a year of ordinary sales."),
    ("Read design wins as a lead on future revenue",
     "A design win is a lead, not a sale. Its value depends on how many sockets a supplier holds and how sticky they "
     "are. Related: Marvell (MRVL), Broadcom (AVGO), Astera Labs (ALAB), Credo (CRDO), Lattice (LSCC)."),
]


def mats(m):
    m["dw_floor"] = mat("dw_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["dw_board"] = mat("dw_board", (0.10, 0.18, 0.40), rough=0.55)
    m["dw_chip"] = mat("dw_chip", (0.20, 0.20, 0.22), metal=0.3, rough=0.4)
    m["dw_rival"] = mat("dw_rival", (0.55, 0.55, 0.60), metal=0.5, rough=0.35)
    m["dw_ramp"] = mat("dw_ramp", (0.30, 0.85, 0.40), emit=(0.30, 0.85, 0.40), strength=1.8)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    mats(m)
    bx("floor", (-260.0, -4.0, -180.0), (260.0, -2.0, 120.0), m["dw_floor"], root)

    # the board in development (centre) with the socket
    bx("board", (-40.0, 0.0, -60.0), (120.0, 4.0, 60.0), m["dw_board"], root)
    sock = K.socket(m, root, "socket", (40.0, 4.0, 0.0), 26.0, 18.0, 6.0, pins=10)
    # the supplier's chip arrives and seats in beat 1
    chip = bx("chip", (-8.0, 0.0, -9.0), (8.0, 4.0, 9.0), m["dw_chip"], root)
    K.slide(chip, 1, (-60.0, 40.0, 0.0), (40.0, 10.0, 0.0), 0.0, 0.5)
    show(chip, [(F(1, 0), F(5, 0))])
    # the rival chip takes the socket in beat 3
    rival = bx("rival", (-8.0, 0.0, -9.0), (8.0, 4.0, 9.0), m["dw_rival"], root)
    K.slide(rival, 3, (-60.0, 40.0, 0.0), (40.0, 10.0, 0.0), 0.0, 0.5)
    show(rival, [(F(3, 0), F(5, 0))])
    show(chip, [(F(1, 0), F(3, 0))])
    # revenue ramp: green bars rising over beat 2, falling away at beat 3
    ramp = K.ledger_bar(m, root, "ramp", 180.0, -40.0, 14.0, {2: 60.0, 3: 6.0}, "dw_ramp")
    show(ramp, [(F(2, 0), F(5, 0))])
    coins = K.coin_row(m, root, "rev", 180.0, 30.0, 16.0, [6, 12, 18], r=6.0, h=2.2)
    show(coins, [(F(2, 0.5), F(4, 0))])
    # the design data flows from board to customer across beats 1 and 2
    run(root, "design", [(-60.0, 40.0, 0.0), (40.0, 12.0, 0.0)], 8, 2.6, m["ldg_blue_b"], [1, 2], 0.0, 0.8, 40)

    C.tags(root, {
        0: [("empty socket on a new board", (40.0, 30.0, 0.0)), ("no sale yet", (40.0, 40.0, 30.0))],
        1: [("supplier chip picked", (40.0, 30.0, 0.0)), ("design win", (40.0, 40.0, -30.0))],
        2: [("1-3 years later: volume", (180.0, 90.0, -40.0)), ("revenue ramps", (180.0, 60.0, 30.0))],
        3: [("next gen: rival takes socket", (40.0, 40.0, 0.0)), ("revenue stream stops", (180.0, 60.0, -40.0))],
        4: [("lead on future revenue", (40.0, 40.0, 0.0)), ("MRVL AVGO ALAB CRDO", (40.0, 30.0, -60.0))],
    })
    C.done(SLUG, BEATS, [
        frame((40.0, 20.0, 0.0), 260.0, 0.25, 0.45, pad=1.0),
        frame((40.0, 10.0, 0.0), 160.0, -0.10, 0.35),
        frame((120.0, 40.0, 0.0), 300.0, -0.30, 0.40, pad=1.0),
        frame((40.0, 20.0, 0.0), 170.0, 0.15, 0.40),
        frame((80.0, 30.0, -20.0), 320.0, 0.10, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
