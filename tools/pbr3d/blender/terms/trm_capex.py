"""TRM_CAPEX: the Terms-tab overview for capital expenditures, built with the market-ledger kit.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_capex.py

Left: cash in gold coin stacks, the operating money a hyperscaler has. Centre: the bench, where a
bank of GPU boxes (the new asset) takes the cash as coins flow in. Its asset bar shrinks as it is
depreciated. Back: four hyperscaler capex bars that surge in beat 3, and their spend flows out to
the chip, memory and power suppliers in beat 4.

Beats:
  0 cash     operating cash in coin stacks
  1 spend    cash becomes long-lived assets: racks, halls, power
  2 expense  the asset depreciates; cost is spread over years
  3 surge    hyperscaler capex bars surge
  4 suppliers capex flows out to suppliers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat, P  # noqa: E402
from power_vrm_detail import frame, run, blink  # noqa: E402
import kit_ledger as K  # noqa: E402

SLUG = "TRM_CAPEX"
BEATS = [
    ("Capex is cash spent on long-lived assets",
     "Capital expenditure is money spent on things that last years: data centers, servers, power gear and fabs. "
     "It leaves the bank now, but it is not an expense in the year it is paid. It goes on the balance sheet as an asset."),
    ("Cash becomes racks, halls and power",
     "An AI buildout turns operating cash into GPU racks, halls, cooling and grid connections. Each dollar here is "
     "a dollar a company can no longer return to shareholders or spend on other things."),
    ("Depreciation spreads the cost over years",
     "The asset loses value on the books each year, and that depreciation runs through the income statement. "
     "So heavy capex shows up as cash out today and as lower profit for years after."),
    ("Hyperscaler capex surges in the AI build",
     "Microsoft, Alphabet, Amazon and Meta are each spending tens of billions a year on AI capacity. Guidance for next "
     "year is watched closely because it sets the demand for chips, memory and power gear."),
    ("One company's capex is another's revenue",
     "The spend flows out to chip, memory, networking and power suppliers. Their backlog and revenue are "
     "this cash in another company's books. Related: NVIDIA (NVDA), Vertiv (VRT), GE Vernova (GEV), Broadcom (AVGO)."),
]

BX = (200.0, 0.0, 0.0)  # bench centre
BARS = {  # hyperscaler: (x, height by beat); heights in scene units, est. shape only
    "MSFT": (-60.0, {0: 30.0, 3: 110.0}),
    "GOOGL": (-20.0, {0: 26.0, 3: 96.0}),
    "AMZN": (20.0, {0: 34.0, 3: 120.0}),
    "META": (60.0, {0: 20.0, 3: 84.0}),
}


def mats(m):
    m["floor"] = mat("cx_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["bench"] = mat("cx_bench", (0.22, 0.24, 0.27), metal=0.6, rough=0.4)
    m["bar_a"] = mat("cx_bar_a", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=1.8)
    m["bar_b"] = mat("cx_bar_b", (1.0, 0.62, 0.18), emit=(1.0, 0.62, 0.18), strength=1.8)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    mats(m)
    bx("floor", (-260.0, -4.0, -180.0), (260.0, -2.0, 120.0), m["floor"], root)

    # cash on the floor (left): operating cash in coin stacks
    cash = K.coin_row(m, root, "cash", -220.0, -40.0, 18.0, [14, 22, 10, 18], r=7.0, h=2.2)
    show(cash, [(F(0, 0), F(2, 0))])
    coins_out = [(-150.0, 6.0, -40.0), (-110.0, 40.0, -40.0), (BX[0] - 40.0, 40.0, 0.0), (BX[0] - 10.0, 22.0, 0.0)]
    show(K.pipe(m, root, "pipe_in", coins_out[:3], "steel", 2.2), [(F(1, 0), F(3, 0))])
    run(root, "coins_in", coins_out, 18, 3.0, m["ldg_gold_b"], [1, 2], 0.0, 0.8, 50)

    # the bench: a bank of GPU boxes, shown from beat 1
    bench = empty("bench", root)
    bx("bench_top", (BX[0] - 70.0, 0.0, -50.0), (BX[0] + 70.0, 6.0, 50.0), m["bench"], bench)
    asset = K.order_stack(m, root, "assets", (BX[0], 6.0, 0.0), 4, 3, "ldg_crate", s=12.0)
    show(asset, [(F(1, 0.5), F(5, 0))])
    # the asset's value bar on the bench, shrinking as it depreciates (beats 2 and 3)
    val = K.ledger_bar(m, root, "value", BX[0] + 60.0, 45.0, 6.0, {1: 60.0, 2: 40.0, 3: 30.0}, "bar_a")
    show(val, [(F(1, 0), F(5, 0))])

    # hyperscaler capex bars at the back, surging in beat 3
    for name, (x, hs) in BARS.items():
        K.ledger_bar(m, root, f"capex_{name}", x, -120.0, 22.0, hs, "bar_b")
        K.gauge(m, root, f"gauge_{name}", x, -140.0, 120.0, ticks=4)
        K.ledger_bar(m, root, f"fill_{name}", x, -140.0, 3.0, hs, "bar_a")

    # capex outflow to suppliers (beat 4): beads from the bars to the racks
    for k, (name, (x, _)) in enumerate(BARS.items()):
        run(root, f"out_{name}", [(x, 8.0, -90.0), (x, 30.0, -60.0), (BX[0] - 20.0, 20.0, -20.0 + 10.0 * k)], 8, 3.0, m["ldg_blue_b"],
            [4], 0.1 + 0.1 * k, 0.8, 40)
        show(D.polyline(f"out_pipe_{name}", [(x, 8.0, -90.0), (x, 30.0, -60.0), (BX[0] - 20.0, 12.0, -20.0 + 10.0 * k)], 1.4,
                        m["steel"], root), [(F(4, 0), F(5, 0))])

    C.tags(root, {
        0: [("operating cash", (-200.0, 40.0, -40.0)), ("cash on hand", (-220.0, 30.0, -40.0))],
        1: [("halls, racks, power", (BX[0], 40.0, 0.0)), ("capitalised: on the balance sheet", (BX[0], 46.0, 45.0))],
        2: [("depreciation: cost spread over years", (BX[0] + 60.0, 50.0, 45.0)), ("P&L hit after cash out", (BX[0], 30.0, -20.0))],
        3: [("MSFT GOOGL AMZN META", (-120.0, 150.0, -120.0)), ("capex surges", (-120.0, 130.0, -120.0))],
        4: [("spend becomes supplier revenue", (-120.0, 30.0, 60.0)), ("NVDA VRT GEV AVGO", (BX[0] + 40.0, 30.0, -60.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 40.0, -30.0), 380.0, 0.25, 0.50, pad=1.0),
        frame((BX[0] - 20.0, 20.0, 0.0), 220.0, -0.20, 0.45),
        frame((BX[0] + 60.0, 40.0, 40.0), 180.0, -0.40, 0.45),
        frame((0.0, 70.0, -120.0), 330.0, 0.15, 0.30, pad=1.0),
        frame((60.0, 30.0, -60.0), 340.0, -0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
