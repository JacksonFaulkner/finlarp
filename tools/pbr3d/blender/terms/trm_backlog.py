"""TRM_BACKLOG: the Terms-tab overview for backlog (remaining performance obligations).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_backlog.py

Left: a signed contract sheet and a shelf of order crates, one crate per undelivered order. Centre:
a backlog bar that grows as orders sign. Right: crates ship out one by one and their value turns
into recognised revenue. A cancelled order drops out of the bar.

Beats:
  0 contract  customers sign multi-year orders
  1 backlog   signed orders stack up as backlog (RPO)
  2 deliver   crates ship, revenue is recognised
  3 cancel    a cancelled order drops out of backlog
  4 quality   backlog quality: duration, cancellation, customers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402
import kit_ledger as K  # noqa: E402

SLUG = "TRM_BACKLOG"
BEATS = [
    ("Backlog is signed orders not yet delivered",
     "Backlog is what customers have contracted to buy and the company has not yet delivered or recognised. Under US "
     "GAAP the same idea is reported as remaining performance obligations (RPO). It is a measure of locked-in demand."),
    ("Signed multi-year AI compute deals swell the backlog",
     "Cloud and AI infrastructure contracts often run for several years. Oracle and CoreWeave reported RPO jumps when "
     "large multi-year AI compute contracts were signed. The number rises the day the contract is signed, not when the "
     "revenue comes in."),
    ("Delivery turns backlog into recognised revenue",
     "As the work is done or the product ships, the order moves out of backlog and into revenue. A company with a large "
     "backlog can show steady revenue growth for years, provided deliveries keep up."),
    ("Cancelled or delayed orders shrink backlog",
     "Backlog can be cancelled, delayed or re-scoped. Size alone is not enough: the quality of backlog depends on contract "
     "terms, how long it runs, and how creditworthy the customer is."),
    ("Watch duration, cancellation terms and customer quality",
     "A year of backlog from a strong buyer is worth more than a longer book from a weak one. Related: Oracle (ORCL), "
     "CoreWeave (CRWV), Microsoft (MSFT), Vertiv (VRT), GE Vernova (GEV)."),
]


def mats(m):
    m["cb_floor"] = mat("cb_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["cb_bar"] = mat("cb_bar", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=1.8)
    m["cb_red"] = mat("cb_red", (1.0, 0.30, 0.20), emit=(1.0, 0.28, 0.18), strength=3.0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    mats(m)
    bx("floor", (-260.0, -4.0, -180.0), (260.0, -2.0, 120.0), m["cb_floor"], root)

    # contract sheets stacked at the left, signed in beat 0
    sheet = K.ledger_sheet(m, root, "contract", (-160.0, 50.0, -20.0), 60.0, 80.0, lines=8)
    show(sheet, [(F(0, 0), F(5, 0))])
    # order crates: the backlog, a shelf of undelivered crates that grows with each signing
    crates = K.order_stack(m, root, "backlog_crates", (-30.0, 0.0, 0.0), 4, 3, "ldg_crate", s=10.0)
    show(crates, [(F(1, 0.3), F(4, 0.6))])
    crates2 = K.order_stack(m, root, "backlog_more", (-30.0, 0.0, 40.0), 4, 2, "ldg_crate", s=10.0)
    show(crates2, [(F(1, 0.8), F(3, 0.2)), (F(4, 0.6), F(5, 0))])
    # the backlog bar: grows at beat 1, shrinks at beat 3 on cancellation
    bar = K.ledger_bar(m, root, "bar", 60.0, -60.0, 14.0, {1: 60.0, 3: 35.0}, "cb_bar")
    show(bar, [(F(1, 0), F(5, 0))])
    # shipments: crates leave the shelf on a belt (beat 2) and arrive as revenue (right)
    run(root, "ship", [(-20.0, 10.0, 0.0), (40.0, 10.0, 0.0), (120.0, 10.0, 0.0), (170.0, 10.0, 0.0)], 6, 4.0,
        m["ldg_gold_b"], [2], 0.0, 0.8, 50)
    rev = K.coin_row(m, root, "revenue", 150.0, -30.0, 16.0, [6, 12, 18], r=6.0, h=2.2)
    show(rev, [(F(2, 0.5), F(5, 0))])
    # cancellation: a red bead strips off the bar in beat 3
    run(root, "cancel", [(60.0, 40.0, -60.0), (110.0, 60.0, -90.0)], 3, 3.5, m["cb_red"], [3], 0.0, 0.8, 40)

    C.tags(root, {
        0: [("multi-year contract signed", (-160.0, 100.0, -20.0)), ("RPO: not yet revenue", (-160.0, 70.0, -20.0))],
        1: [("backlog grows on signing", (-30.0, 40.0, 0.0)), ("ORCL CRWV RPO jumps", (60.0, 80.0, -60.0))],
        2: [("delivery: backlog to revenue", (120.0, 20.0, 0.0)), ("recognised as work is done", (150.0, 40.0, -30.0))],
        3: [("cancelled order drops out", (110.0, 60.0, -90.0)), ("bar shrinks", (60.0, 40.0, -60.0))],
        4: [("duration: how long it runs", (-30.0, 30.0, 40.0)), ("MSFT VRT GEV CRWV", (60.0, 80.0, -60.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-120.0, 40.0, -10.0), 300.0, 0.25, 0.40, pad=1.0),
        frame((-30.0, 20.0, 20.0), 220.0, -0.20, 0.45),
        frame((120.0, 20.0, -20.0), 260.0, -0.30, 0.40, pad=1.0),
        frame((60.0, 40.0, -60.0), 240.0, 0.20, 0.45),
        frame((0.0, 40.0, -20.0), 330.0, 0.10, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
