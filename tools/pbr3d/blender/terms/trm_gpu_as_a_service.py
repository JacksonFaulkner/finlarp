"""TRM_GPU_AS_A_SERVICE: the Terms-tab overview for renting GPU compute.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_gpu_as_a_service.py

Centre: a cut-open neocloud GPU hall, three rows of liquid-cooled racks with spine racks at the
ends. Right: the tenants (one big AI lab, small customers) with contract sheets; compute beads
flow out to them and gold rent coins flow back. Left: the lender's coin stacks funding the hall.
Front: a utilization gauge and a GPU-value bar that shrinks as the hardware ages.

Beats:
  0 rent     tenants rent GPU time instead of buying servers
  1 terms    hourly on-demand vs multi-year take-or-pay contracts
  2 debt     the hall is bought with debt; interest flows out
  3 util     returns depend on utilization and GPU life
  4 who      who sells it
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, blink, present  # noqa: E402
import kit_ledger as K  # noqa: E402
import trm_neocloud as N  # noqa: E402

SLUG = "TRM_GPU_AS_A_SERVICE"
BEATS = [
    ("Rent GPU time instead of buying servers",
     "GPU-as-a-service means a provider buys the GPUs, installs them in its own data center and rents the compute out. "
     "A lab or enterprise gets thousands of GPUs in weeks without spending billions up front or running a hall."),
    ("Hourly on demand, or multi-year contracts",
     "Small users pay by the GPU-hour, often a few dollars per H100-hour, and can leave any time. Big AI labs sign "
     "take-or-pay contracts for 2-5 years that fix the price and volume, which makes the provider's revenue bankable."),
    ("The hall is bought with borrowed money",
     "A 100 MW GPU campus can cost several billion dollars in GPUs, networking and power gear. Neoclouds fund much of it "
     "with debt secured on the GPUs and the customer contracts, so interest is a big fixed cost from day one."),
    ("Returns hinge on utilization and GPU life",
     "Idle GPUs earn nothing while their debt and depreciation keep running. Profit depends on keeping the racks busy and "
     "on the GPUs still renting at a good price before newer chips make them cheap."),
    ("Neoclouds and hyperscalers sell it",
     "CoreWeave and Nebius are pure-play GPU clouds; Oracle, Amazon, Microsoft and Google rent GPUs alongside their other cloud "
     "services. NVIDIA supplies the chips and sometimes backs the neoclouds. Related: CRWV, NBIS, ORCL, AMZN, NVDA."),
]

ROWS = (-30.0, 0.0, 30.0)
XS = [-70.0 + 16.0 * i for i in range(9)]


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    N.mats(m)
    m["slab"] = mat("gs_slab", (0.15, 0.16, 0.18), rough=0.85)
    m["lab"] = mat("gs_lab", (0.30, 0.34, 0.40), metal=0.4, rough=0.5)
    m["util"] = mat("gs_util", (0.25, 0.85, 0.45), rough=0.5)
    m["val"] = mat("gs_val", (0.30, 0.60, 0.95), rough=0.5)
    m["debt"] = mat("gs_debt", (0.85, 0.30, 0.25), rough=0.5)

    bx("floor", (-260.0, -3.0, -120.0), (260.0, -1.0, 120.0), m["slab"], root)
    # the hall: back wall and left wall, front + roof cut away
    bx("hall_back", (-90.0, 0.0, -52.0), (90.0, 70.0, -49.0), m["wall"], root)
    bx("hall_l", (-93.0, 0.0, -52.0), (-90.0, 70.0, 48.0), m["wall"], root)
    bx("hall_r", (90.0, 0.0, -52.0), (93.0, 70.0, 48.0), m["wall"], root)
    bx("hall_floor", (-90.0, 0.0, -49.0), (90.0, 0.6, 48.0), m["floor"], root)
    leds = [empty(f"leds{r}", root) for r in range(3)]
    for r, z in enumerate(ROWS):
        for i, x in enumerate(XS):
            N.gpu_rack(m, root, f"rk{r}_{i}", x, z, leds[r], spine=(i in (0, 8)))
    # cable trays above rows
    for z in ROWS:
        D.tube(f"tray{z:.0f}", (-80.0, 62.0, z), (80.0, 62.0, z), 1.2, m["cable"], root, 8)

    # tenants on the right: a big lab building and small customer boxes
    bx("lab_bld", (150.0, 0.0, -40.0), (200.0, 46.0, 0.0), m["lab"], root)
    for k in range(6):
        bx(f"lab_win{k}", (154.0 + 7.5 * k, 30.0, 0.0), (159.0 + 7.5 * k, 38.0, 0.6), m["led_g"], root)
    smalls = K.order_stack(m, root, "smalls", (175.0, 0.0, 40.0), 3, 2, "ldg_crate", s=10.0)
    present(smalls, [(F(0, 0), F(5, 0))])
    # compute out (blue), rent back (gold)
    out_pts = [(80.0, 50.0, 0.0), (120.0, 56.0, -10.0), (150.0, 30.0, -20.0)]
    run(root, "compute", out_pts, 14, 2.4, m["ldg_blue_b"], [0, 1, 3], 0.0, 0.85, 40)
    run(root, "compute_s", [(80.0, 40.0, 20.0), (120.0, 30.0, 35.0), (165.0, 14.0, 40.0)], 8, 2.0, m["ldg_blue_b"], [0, 1], 0.1, 0.85, 40)
    run(root, "rent", [(150.0, 10.0, -10.0), (120.0, 14.0, 10.0), (60.0, 6.0, 60.0)], 12, 2.6, m["ldg_gold_b"], [0, 1, 3], 0.1, 0.9, 40)
    # contracts (beat 1): a long contract sheet by the lab, a meter by the small customers
    sheet = K.ledger_sheet(m, root, "contract", (175.0, 70.0, -20.0), 30.0, 38.0, 7)
    present(sheet, [(F(1, 0), F(2, 0)), (F(4, 0), F(5, 0))])
    meter = K.ledger_sheet(m, root, "hourly", (205.0, 28.0, 40.0), 14.0, 14.0, 3)
    present(meter, [(F(1, 0), F(2, 0))])
    tick = empty("g_tick", root); bx("hour_tick", (200.0, 34.0, 40.6), (210.0, 36.0, 41.0), m["ldg_gold_b"], tick)
    blink(tick, 1, [0, 2, 4, 6], n=8)

    # lender on the left (beat 2): coin stacks, cash in, interest out
    bank = K.coin_row(m, root, "bank", -220.0, 0.0, 16.0, [20, 26, 16], r=6.0, h=2.0)
    present(bank, [(F(2, 0), F(5, 0))])
    run(root, "loan", [(-190.0, 30.0, 0.0), (-140.0, 40.0, 10.0), (-92.0, 30.0, 20.0)], 14, 3.0, m["ldg_gold_b"], [2], 0.0, 0.5, 40)
    run(root, "interest", [(-92.0, 10.0, 40.0), (-140.0, 12.0, 40.0), (-190.0, 8.0, 20.0)], 10, 2.2, m["ldg_red_b"], [2, 3], 0.4, 0.95, 40)
    debt = K.ledger_bar(m, root, "debt_bar", -200.0, 50.0, 14.0, {0: 0.0, 2: 70.0}, "debt")

    # utilization + GPU value at the front (beat 3)
    K.gauge(m, root, "ugauge", -40.0, 80.0, 60.0, ticks=4)
    K.ledger_bar(m, root, "ufill", -40.0, 80.0, 3.0, {0: 40.0, 3: 50.0}, "util")
    vb = K.ledger_bar(m, root, "value", 20.0, 80.0, 14.0, {0: 60.0, 3: 22.0}, "val")
    for r in range(3):  # racks go dark row by row when idle, back on when busy
        blink(leds[r], 3, [0, 1, 2, 3, 4, 5] if r < 2 else [0, 1, 4, 5], n=8, on=0.8)

    C.tags(root, {
        0: [("tenants rent GPU hours", (175.0, 60.0, -20.0)), ("provider owns the racks", (0.0, 80.0, 0.0))],
        1: [("multi-year take-or-pay", (175.0, 96.0, -20.0)), ("on demand: $/GPU-hour", (205.0, 44.0, 40.0))],
        2: [("GPU-backed debt", (-200.0, 80.0, 50.0)), ("interest runs every month", (-140.0, 30.0, 45.0))],
        3: [("utilization", (-40.0, 70.0, 80.0)), ("GPU resale value falls", (20.0, 70.0, 80.0)),
            ("idle racks earn nothing", (40.0, 70.0, 30.0))],
        4: [("CRWV NBIS ORCL", (0.0, 85.0, 0.0)), ("AMZN NVDA", (175.0, 60.0, -20.0))],
    })
    C.done(SLUG, BEATS, [
        frame((40.0, 30.0, 0.0), 300.0, 0.30, 0.45, pad=1.0),
        frame((150.0, 40.0, 10.0), 160.0, -0.30, 0.35),
        frame((-130.0, 30.0, 20.0), 220.0, 0.35, 0.40),
        frame((0.0, 35.0, 50.0), 200.0, 0.15, 0.35),
        frame((40.0, 40.0, 0.0), 320.0, -0.20, 0.50, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
