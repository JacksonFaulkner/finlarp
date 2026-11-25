"""TRM_SERVER_USEFUL_LIFE: the Terms-tab overview for server useful life (depreciation schedule).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_server_useful_life.py

Left: a GPU rack on a plinth, its purchase price as a coin stack. Centre: a year-by-year floor
of depreciation bars, one per year. Beat 1 compares a 3-year schedule (three tall bars) with a
6-year one (six short bars). Right: an earnings bar that grows when the life is stretched.
Back: a new-generation rack slides in and the old rack's lights dim (fast GPU obsolescence).

Beats:
  0 cost     a server's cost is spread over its useful life
  1 stretch  3 years -> 6 years: smaller yearly charge
  2 profit   lower depreciation lifts reported earnings
  3 risk     GPUs age fast; the economic life may be shorter
  4 who      disclosed as an estimate change
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, bx, empty, mat  # noqa: E402
from power_vrm_detail import frame, run, blink, present  # noqa: E402
import kit_ledger as K  # noqa: E402
import trm_neocloud as N  # noqa: E402

SLUG = "TRM_SERVER_USEFUL_LIFE"
BEATS = [
    ("Server cost is spread over its useful life",
     "A company does not expense a $3 million GPU rack in the year it buys it. It picks an estimated useful life and "
     "books an equal slice of the cost as depreciation each year until the asset is written down."),
    ("Hyperscalers stretched lives from 3 to 6 years",
     "Between 2020 and 2023 Microsoft, Alphabet, Meta and Amazon raised server lives from about 3-4 years to 5-6 years. "
     "The same rack now costs one sixth of its price a year instead of one third."),
    ("A longer life lifts reported earnings",
     "Smaller yearly depreciation means higher operating income, with no change in cash spent. Each extension added "
     "billions of dollars a year to big tech profits."),
    ("AI GPUs may age faster than the books say",
     "NVIDIA ships a faster GPU generation roughly every year, so older chips rent for less and less. Critics argue the "
     "real economic life of an AI GPU may be 3-4 years; Amazon cut some server lives back to 5 years in 2025."),
    ("Changes are disclosed with the dollar effect",
     "A change in useful life is an accounting estimate change, applied going forward, and the 10-K or 10-Q states its "
     "effect on operating income. Watch it at MSFT, GOOGL, AMZN, META and GPU clouds like CRWV."),
]

YX0 = -40.0  # first year bar x
STEP = 22.0
COST = 120.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    N.mats(m)
    m["slab"] = mat("ul_slab", (0.15, 0.16, 0.18), rough=0.85)
    m["dep3"] = mat("ul_dep3", (0.90, 0.45, 0.25), rough=0.5)
    m["dep6"] = mat("ul_dep6", (0.30, 0.60, 0.95), rough=0.5)
    m["earn"] = mat("ul_earn", (0.30, 0.85, 0.45), rough=0.5)
    m["grid"] = mat("ul_grid", (0.30, 0.32, 0.36), rough=0.7)

    bx("floor", (-200.0, -3.0, -120.0), (240.0, -1.0, 120.0), m["slab"], root)
    # the old rack on a plinth with its price
    bx("plinth", (-130.0, 0.0, -20.0), (-90.0, 6.0, 20.0), m["grid"], root)
    old_leds = empty("old_leds", root)
    rk = empty("old_rack", root)
    rk.location = C.P(0.0, 6.0, 0.0)
    N.gpu_rack(m, rk, "old", -110.0, 0.0, old_leds, spine=False)
    blink(old_leds, 3, [0, 1, 2, 3], n=8, on=0.6, u0=0.0, u1=0.5)
    price = K.coin_stack(m, root, "price", (-75.0, 0.0, 15.0), 24, 5.0, 2.0)
    # year axis: tick slabs for 6 years
    for y in range(6):
        bx(f"yr{y}", (YX0 + STEP * y - 9.0, 0.0, 30.0), (YX0 + STEP * y + 9.0, 0.6, 34.0), m["grid"], root)
    # 3-year schedule (front row) and 6-year (back row)
    for y in range(6):
        x = YX0 + STEP * y
        h3 = COST / 3 if y < 3 else 0.0
        K.ledger_bar(m, root, f"d3_{y}", x, 15.0, 12.0, {0: h3, 1: h3, 2: 0.0}, "dep3")
        K.ledger_bar(m, root, f"d6_{y}", x, -10.0, 12.0, {0: 0.0, 1: COST / 6, 3: COST / 6, 4: COST / 6}, "dep6")
    # cost flowing from coins into the year bars
    run(root, "slices", [(-75.0, 50.0, 15.0), (-50.0, 60.0, 15.0), (YX0 + STEP * 2, 45.0, 15.0)], 10, 2.4, m["ldg_gold_b"],
        [0], 0.0, 0.85, 40)
    run(root, "slices6", [(-75.0, 50.0, 15.0), (-40.0, 40.0, -10.0), (YX0 + STEP * 5, 25.0, -10.0)], 10, 2.4, m["ldg_gold_b"],
        [1], 0.1, 0.85, 50)
    # earnings bar on the right: grows when depreciation shrinks
    K.gauge(m, root, "egauge", 140.0, 0.0, 90.0, ticks=5)
    K.ledger_bar(m, root, "earn", 160.0, 0.0, 14.0, {0: 40.0, 2: 70.0, 3: 70.0, 4: 58.0}, "earn")
    K.ledger_bar(m, root, "deprec", 180.0, 0.0, 14.0, {0: 40.0, 2: 20.0, 3: 20.0, 4: 24.0}, "dep6")
    run(root, "lift", [(180.0, 30.0, 0.0), (170.0, 70.0, 0.0), (160.0, 60.0, 0.0)], 8, 2.0, m["ldg_gold_b"], [2], 0.1, 0.85, 40)
    # new generation rack slides in (beat 3)
    new_leds = empty("new_leds", root)
    nr = empty("new_rack", root)
    N.gpu_rack(m, nr, "new", -110.0, -50.0, new_leds, spine=False)
    present(nr, [(F(3, 0.2), F(5, 0))])
    blink(new_leds, 3, [0, 1, 2, 3, 4, 5, 6, 7], n=8, on=0.7, u0=0.2)
    K.ledger_sheet(m, root, "note", (60.0, 40.0, -60.0), 40.0, 30.0, 6)

    C.tags(root, {
        0: [("$ price spread over years", (-75.0, 60.0, 15.0)), ("3-yr life: 1/3 a year", (YX0 + STEP, 55.0, 15.0))],
        1: [("6-yr life: 1/6 a year", (YX0 + STEP * 3, 35.0, -10.0)), ("same rack, same cash", (-110.0, 75.0, 0.0))],
        2: [("operating income up", (160.0, 85.0, 0.0)), ("depreciation down", (180.0, 35.0, 0.0))],
        3: [("new GPU every ~year", (-110.0, 70.0, -50.0)), ("old rack rents for less", (-110.0, 50.0, 10.0))],
        4: [("estimate change, disclosed", (60.0, 62.0, -60.0)), ("MSFT GOOGL AMZN META CRWV", (60.0, 90.0, -20.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-50.0, 30.0, 10.0), 220.0, 0.30, 0.40),
        frame((10.0, 25.0, 0.0), 200.0, 0.10, 0.40),
        frame((160.0, 45.0, 0.0), 120.0, -0.30, 0.25),
        frame((-100.0, 35.0, -20.0), 140.0, 0.45, 0.30),
        frame((30.0, 40.0, -10.0), 340.0, -0.15, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
