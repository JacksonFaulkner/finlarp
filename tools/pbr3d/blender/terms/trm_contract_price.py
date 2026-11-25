"""TRM_CONTRACT_PRICE: the Terms-tab overview for memory contract prices (own scene, no board).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_contract_price.py

A fab-side warehouse of DRAM chip trays ships pallets to a big buyer on a quarterly contract
while small lots trade daily on the spot market. Two price walls behind: spot bars jump around
daily, contract bars step once a quarter and follow spot with a lag.

Beats:
  0 supply   memory maker's trays and pallets
  1 contract big buyers' pallets at a negotiated price
  2 spot     small lots trade daily
  3 lag      spot moves first, contract follows
  4 margins  contract trend drives revenue and margins
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F  # noqa: E402
from power_vrm_detail import bx, frame, present, run  # noqa: E402
from sand_overview import empty, show  # noqa: E402

SLUG = "TRM_CONTRACT_PRICE"
BEATS = [
    ("Memory makers sell chips by the pallet and by the lot",
     "DRAM and NAND come off the fab as trays of packaged chips. A few makers supply nearly all of it, and they sell "
     "through two channels with two different prices."),
    ("Contract price: what big buyers negotiate",
     "Hyperscalers, PC and phone makers buy huge volumes on agreements that reset monthly or quarterly. That "
     "negotiated per-chip price is the contract price, and it covers most of the industry's revenue."),
    ("Spot price: small lots that trade every day",
     "Brokers and smaller buyers trade leftover chips daily. The spot price reacts quickly to shortages or "
     "gluts, so it is noisy."),
    ("Spot moves first; contract follows in steps",
     "When spot runs above contract, buyers expect the next negotiation to rise, and vice versa. Contract prices "
     "move in quarterly steps that trail the spot trend, which makes spot a leading indicator."),
    ("Contract trends drive memory makers' earnings",
     "A 10-20% quarterly move in contract price flows almost straight into gross margin, since fab costs are "
     "mostly fixed. That is why analysts track it on every earnings call. Related: Micron (MU), Samsung "
     "(005930.KS), SK hynix (000660.KS), Sandisk (SNDK)."),
]

SPOT = [1.0, 1.1, 0.95, 1.2, 1.35, 1.3, 1.55, 1.7, 1.6, 1.85, 2.0, 1.9, 2.2, 2.1, 2.35, 2.5]
CONTRACT = [1.0] * 4 + [1.1] * 4 + [1.4] * 4 + [1.8] * 4


def tray(m, parent, name, x, z, y=0.0):
    g = empty(name, parent)
    bx(name + "_t", (x - 9, y, z - 6), (x + 9, y + 1.2, z + 6), m["pcb_blue"], g)
    for i in range(4):
        for j in range(3):
            cx, cz = x - 6.5 + i * 4.3, z - 3.6 + j * 3.6
            bx(f"{name}_c{i}{j}", (cx - 1.6, y + 1.2, cz - 1.3), (cx + 1.6, y + 2.2, cz + 1.3), m["mold"], g)
    return g


def pallet(m, parent, name, x, z, layers=4):
    g = empty(name, parent)
    bx(name + "_p", (x - 11, 0, z - 8), (x + 11, 2.0, z + 8), m["ceramic"], g)
    for k in range(layers):
        tray(m, g, f"{name}_l{k}", x, z, 2.0 + k * 2.4)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    bx("floor", (-120, -1.0, -120), (120, 0.0, 60), m["steel"], root)
    # fab warehouse: rack of trays
    for r in range(3):
        bx(f"shelf{r}", (-100, r * 14.0 + 6, -60), (-40, r * 14.0 + 7, -40), m["alum"], root)
        for c in range(3):
            tray(m, root, f"st{r}{c}", -90 + c * 20, -50, r * 14.0 + 7)
    for x in (-100, -40):
        bx(f"post{x}", (x - 1, 0, -61), (x + 1, 44, -59), m["alum"], root)
    # contract pallets moving to buyer dock
    pals = [pallet(m, root, f"pal{i}", -20 + i * 26, -10) for i in range(3)]
    for i, p in enumerate(pals):
        present(p, [(F(1, 0.1 * i), F(5, 0))])
    bx("dock", (60, 0, -30), (110, 20, 10), m["car"], root)
    run(root, "ship", [(-70, 10, -30), (0, 10, -10), (80, 22, -10)], 6, 2.0, m["e_blue"], [1, 4], 0.0, 0.7, 50)
    # spot lots: small trays hopping to broker desk
    bx("desk", (60, 0, 25), (90, 8, 45), m["mold"], root)
    run(root, "spot", [(-40, 10, 20), (0, 16, 30), (70, 10, 35)], 10, 1.2, m["h_amber"], [2, 3], 0.0, 0.9, 25)
    # price walls
    gs, gc = empty("spotbars", root), empty("conbars", root)
    for i, (s, c) in enumerate(zip(SPOT, CONTRACT)):
        x = -100 + i * 12.0
        bx(f"sb{i}", (x, 0, -95), (x + 4.5, s * 30.0, -91), m["copper"], gs)
        bx(f"cb{i}", (x + 5.0, 0, -95), (x + 9.5, c * 30.0, -91), m["nplus"], gc)
    present(gc, [(F(1, 0.3), F(5, 0))])
    present(gs, [(F(2, 0.2), F(5, 0))])
    up = bx("margin", (60, 20, -20), (66, 21, -14), m["sig"], root)
    show(up, [(F(4, 0.2), F(5, 0))])
    C.wiggle(up, [4], amp=(0.0, 3.0, 0.0), period=10)

    C.tags(root, {
        0: [("fab output: trays of chips", (-70, 40, -50)), ("pallets for big buyers", (0, 12, -10))],
        1: [("contract: negotiated, quarterly", (-40, 50, -93)), ("hyperscalers, OEMs", (85, 20, -10))],
        2: [("spot: small lots, daily", (70, 10, 35)), ("spot bars: noisy", (-20, 60, -93))],
        3: [("spot leads", (80, 75, -93)), ("contract steps after", (60, 55, -93))],
        4: [("contract up -> margin up", (63, 22, -17)), ("most revenue is contract", (0, 12, -10))],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 15.0, -30.0), 180.0, 0.35, 0.45, pad=1.0),
        frame((10.0, 20.0, -40.0), 230.0, 0.25, 0.35, pad=1.0),
        frame((10.0, 20.0, -20.0), 230.0, 0.40, 0.40, pad=1.0),
        frame((-5.0, 35.0, -93.0), 210.0, 0.05, 0.15, pad=1.0),
        frame((0.0, 25.0, -40.0), 250.0, 0.20, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
