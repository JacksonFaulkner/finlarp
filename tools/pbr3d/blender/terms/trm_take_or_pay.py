"""TRM_TAKE_OR_PAY: the Terms-tab overview for take-or-pay / long-term supply agreements.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_take_or_pay.py

Left: a memory fab (seller). Right: a buyer's data hall. Between them a signed contract sheet with a
minimum-volume gauge. Beat 1 a prepayment of coins crosses to the fab. Beat 2 wafer crates flow to the
buyer at the committed rate. Beat 3 the buyer's demand drops, crates pile up unused, but coins keep
flowing: take it or pay for it. Beat 4 where it shows in filings.

Beats:
  0 sign      buyer commits to a minimum volume over years
  1 prepay    cash up front helps the seller fund capacity
  2 deliver   supply flows at the committed rate
  3 pay       demand falls, the buyer still pays the minimum
  4 read      purchase obligations in filings
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, bx, empty, mat  # noqa: E402
from power_vrm_detail import frame, run, present  # noqa: E402
import kit_ledger as K  # noqa: E402
import kit_supply as S  # noqa: E402

SLUG = "TRM_TAKE_OR_PAY"
BEATS = [
    ("Take-or-pay: buy the minimum volume or pay for it anyway",
     "A take-or-pay or long-term supply agreement commits a buyer to purchase a set minimum over several years. If the "
     "buyer takes less, it still owes the money. In AI, buyers sign these to lock in scarce memory, GPUs or compute."),
    ("Prepayments give the seller cash to build capacity",
     "Some deals come with money up front. Memory makers have taken customer prepayments to help fund new fabs, and the "
     "commitment lets them add capacity knowing it is already sold."),
    ("Supply flows to the buyer at the committed rate",
     "While demand is strong, the buyer gets guaranteed supply when others are rationed. Cloud providers sign multi-year "
     "compute commitments with neoclouds on the same logic: capacity reserved, price fixed."),
    ("When demand falls, the buyer still pays",
     "If the buyer needs less, the product piles up or the reserved capacity sits idle, but the minimum payment keeps "
     "flowing. The seller is protected; the risk sits with the buyer."),
    ("Find them under purchase obligations in filings",
     "Filings list these as purchase commitments or contractual obligations, often billions over several years. Rising "
     "obligations show confidence or a scramble for supply. Related: Micron (MU), NVIDIA (NVDA), CoreWeave (CRWV), "
     "Microsoft (MSFT), Western Digital (WDC)."),
]


def mats(m):
    m["tp_floor"] = mat("tp_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["tp_wall"] = mat("tp_wall", (0.80, 0.82, 0.84), rough=0.5)
    m["tp_roof"] = mat("tp_roof", (0.30, 0.32, 0.36), metal=0.5, rough=0.4)
    m["tp_rack"] = mat("tp_rack", (0.10, 0.11, 0.13), metal=0.6, rough=0.4)
    m["tp_led"] = mat("tp_led", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=4.0)
    m["tp_min"] = mat("tp_min", (1.0, 0.75, 0.25), emit=(1.0, 0.70, 0.20), strength=3.0)
    m["tp_wafer"] = mat("tp_wafer", (0.55, 0.50, 0.70), metal=0.7, rough=0.2)


def fab(m, root):
    bx("fab", (-230.0, 0.0, -60.0), (-130.0, 40.0, 30.0), m["tp_wall"], root)
    bx("fab_roof", (-232.0, 40.0, -62.0), (-128.0, 43.0, 32.0), m["tp_roof"], root)
    for k in range(4):
        S.tank(m, root, f"gas{k}", (-215.0 + k * 22.0, 43.0, -40.0), 6.0, 14.0)
        bx(f"duct{k}", (-218.0 + k * 22.0, 43.0, 0.0), (-212.0 + k * 22.0, 52.0, 10.0), m["steel"], root)
    for k in range(5):
        bx(f"fwin{k}", (-222.0 + k * 19.0, 14.0, 30.0), (-210.0 + k * 19.0, 26.0, 30.6), m["tp_led"], root)
    # wafers stacked by the dock
    for k in range(6):
        S.drum(m, root, f"wf{k}", (-140.0 + (k % 3) * 0.0, k * 1.6, 50.0), 8.0, 1.0, mt="tp_wafer")


def hall(m, root):
    bx("hall", (130.0, 0.0, -60.0), (240.0, 2.0, 30.0), m["tp_roof"], root)
    for r in range(2):
        for k in range(6):
            x = 140.0 + k * 16.0
            z = -45.0 + r * 40.0
            bx(f"rk{r}_{k}", (x, 2.0, z), (x + 12.0, 50.0, z + 14.0), m["tp_rack"], root)
            for s in range(5):
                bx(f"rl{r}_{k}_{s}", (x + 9.0, 8.0 + s * 8.0, z + 14.0), (x + 11.0, 10.0 + s * 8.0, z + 14.5), m["tp_led"], root)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    S.materials(m)
    mats(m)
    bx("floor", (-260.0, -4.0, -180.0), (260.0, -2.0, 120.0), m["tp_floor"], root)
    fab(m, root)
    hall(m, root)

    # the contract in the middle with a minimum-volume gauge
    K.ledger_sheet(m, root, "contract", (0.0, 0.0, -40.0), 60.0, 70.0, lines=7)
    K.gauge(m, root, "minvol", 50.0, -40.0, 60.0, ticks=6)
    bx("minline", (44.0, 39.0, -46.0), (56.0, 41.0, -34.0), m["tp_min"], root)
    seal = empty("seal", root)
    S.drum(m, seal, "seal_b", (18.0, 10.0, -38.0), 6.0, 1.0, mt="ldg_red_b")
    present(seal, [(F(0, 0.4), F(5, 0))])

    # beat 1: prepayment coins from the buyer to the fab, a big stack at the fab
    run(root, "prepay", [(130.0, 30.0, 60.0), (0.0, 40.0, 70.0), (-130.0, 30.0, 60.0)], 10, 3.0,
        m["ldg_gold_b"], 1, 0.0, 0.8, 50)
    pre = empty("pre", root)
    K.coin_stack(m, pre, "prestack", (-110.0, 0.0, 70.0), 14, r=7.0, h=1.6)
    present(pre, [(F(1, 0.5), F(5, 0))])

    # beat 2-3: wafer crates flow to the buyer at the committed rate
    run(root, "supply", [(-130.0, 12.0, 40.0), (0.0, 12.0, 30.0), (130.0, 12.0, 40.0)], 8, 3.2,
        m["tp_led"], [2, 3], 0.0, 0.9, 50)
    # beat 3: unused crates pile up at the buyer, coins still flow
    pile = empty("pile", root)
    K.order_stack(m, pile, "unused", (190.0, 2.0, 60.0), 4, 3, s=8.0)
    present(pile, [(F(3, 0.3), F(5, 0))])
    run(root, "pay", [(130.0, 40.0, 80.0), (0.0, 50.0, 90.0), (-130.0, 40.0, 80.0)], 8, 2.6,
        m["ldg_gold_b"], [3, 4], 0.0, 0.9, 50)
    idle = empty("idle", root)
    for k in range(6):
        x = 140.0 + k * 16.0
        bx(f"idle{k}", (x + 1.0, 8.0, -5.0 + 14.0), (x + 11.0, 46.0, -5.0 + 14.6), m["ldg_red_b"], idle)
    present(idle, [(F(3, 0.4), F(4, 0))])

    # beat 4: the obligations ledger
    obl = empty("obl", root)
    K.ledger_sheet(m, obl, "obl_sheet", (0.0, 0.0, -150.0), 90.0, 60.0, lines=6)
    for k, h in enumerate((40.0, 32.0, 24.0, 16.0)):
        bx(f"oblbar{k}", (-40.0 + k * 22.0, 0.0, -130.0), (-28.0 + k * 22.0, h, -118.0), m["tp_wall"], obl)
    present(obl, [(F(4, 0), F(5, 0))])

    C.tags(root, {
        0: [("buyer commits to a minimum", (0.0, 80.0, -40.0)), ("seller: memory fab", (-180.0, 60.0, -10.0)),
            ("buyer: AI data hall", (185.0, 60.0, -10.0))],
        1: [("prepayment up front", (0.0, 50.0, 70.0)), ("funds new capacity", (-110.0, 30.0, 70.0))],
        2: [("supply at committed rate", (0.0, 25.0, 30.0)), ("reserved when others ration", (185.0, 60.0, -10.0))],
        3: [("demand falls: stock piles up", (190.0, 40.0, 60.0)), ("buyer still pays the minimum", (0.0, 60.0, 90.0))],
        4: [("purchase obligations", (0.0, 70.0, -150.0)), ("MU NVDA CRWV MSFT WDC", (0.0, 50.0, -120.0))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 30.0, -20.0), 470.0, 0.15, 0.45, pad=1.0),
        frame((-40.0, 25.0, 50.0), 300.0, 0.20, 0.45),
        frame((0.0, 20.0, 20.0), 380.0, -0.10, 0.50, pad=1.0),
        frame((120.0, 30.0, 50.0), 300.0, -0.25, 0.45),
        frame((0.0, 30.0, -130.0), 200.0, 0.10, 0.35),
    ], root)


if __name__ == "__main__":
    build()
