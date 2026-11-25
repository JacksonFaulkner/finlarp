"""TRM_VENDOR_FINANCING: the Terms-tab overview for vendor financing, at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_vendor_financing.py

A money loop, so the scene is its own: on the left the chip vendor (a fab-like plant with GPU
crates on its dock and a revenue column), in the middle a neocloud's GPU hall (the neocloud
term's rack-scale racks), on the right an AI lab renting compute. Money beads go round: the
vendor invests or lends, the neocloud buys the vendor's GPUs with it, the lab pays rent, rent
repays the vendor. A glowing strap marks the vendor's backstop; at the end demand dims and the
loop breaks.

Beats:
  0 fund      the vendor lends to or invests in its customer
  1 buy       the customer spends it on the vendor's GPUs: revenue rises
  2 rent      the GPUs are rented out; rent repays the loan
  3 backstop  guarantees: the vendor promises to buy unused capacity
  4 risk      if demand falls the loop breaks and the vendor holds the risk
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import trm_neocloud as N  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_VENDOR_FINANCING"
BEATS = [
    ("A supplier lends to, or invests in, its own customer",
     "Vendor financing is when a seller funds the buyer: a loan, an equity stake, a debt guarantee or a lease. In AI "
     "infrastructure a chip maker or cloud may put money into a neocloud or AI lab that is short of capital but "
     "hungry for GPUs."),
    ("The customer spends that money on the supplier's chips",
     "The cash comes straight back as orders. The neocloud buys GPU systems, the vendor books the sale as revenue, "
     "and racks fill up. The revenue is real, but part of it was paid for with the vendor's own money, so growth can "
     "look stronger than end demand."),
    ("Rent from end users is what pays the loan back",
     "The neocloud rents the GPUs to AI labs and enterprises by the hour or under multi-year contracts. That rent "
     "services its debt and repays the vendor. The loop only closes if those end customers keep paying at prices "
     "high enough to cover depreciation and interest."),
    ("Backstops: the vendor promises to buy unused capacity",
     "Some deals go further: the vendor guarantees a customer's lease or debt, or agrees to rent back any capacity "
     "the customer cannot sell. These sit off the balance sheet and show up in the commitments and guarantees notes "
     "of the 10-K, which is where analysts look for them."),
    ("If end demand falls, the loop breaks and the vendor holds the risk",
     "When GPU rental prices drop or a customer cannot refinance, orders stop, loans may not be repaid and guarantees "
     "get called. The vendor loses future revenue and takes write-downs on the stakes. Related: NVIDIA (NVDA), "
     "CoreWeave (CRWV), Oracle (ORCL), Advanced Micro Devices (AMD)."),
]

VX = -230.0  # vendor plant x centre
HX0, HX1, HZ0, HY = -110.0, 60.0, -90.0, 70.0
ROWS = (-66.0, -32.0)
RX = [-95.0 + 16.0 * j for j in range(10)]
LX = 150.0  # AI lab x


def mats(m):
    N.mats(m)
    m["plant"] = mat("vf_plant", (0.78, 0.79, 0.80), rough=0.7)
    m["roof"] = mat("vf_roof", (0.35, 0.37, 0.40), metal=0.4, rough=0.5)
    m["crate"] = mat("vf_crate", (0.55, 0.42, 0.26), rough=0.8)
    m["strap"] = mat("vf_strap", (0.70, 0.45, 1.0), emit=(0.65, 0.40, 1.0), strength=3.0)
    m["rev"] = mat("vf_rev", (0.35, 0.95, 0.55), emit=(0.30, 0.90, 0.50), strength=2.5)
    m["road"] = mat("vf_road", (0.25, 0.26, 0.28), rough=0.8)


def plant(m, root):
    """The vendor: a long low plant with saw-tooth roof, a loading dock of GPU crates, a revenue column."""
    x0, x1, z0, z1 = VX - 50.0, VX + 50.0, -100.0, -30.0
    bx("pl_body", (x0, 0.0, z0), (x1, 34.0, z1), m["plant"], root)
    for k in range(6):
        xa = x0 + k * (x1 - x0) / 6
        bx(f"pl_saw{k}", (xa, 34.0, z0), (xa + 6.0, 44.0, z1), m["glass"], root)
        bx(f"pl_sawr{k}", (xa + 6.0, 34.0, z0), (xa + (x1 - x0) / 6, 40.0, z1), m["roof"], root)
    for k in range(5):
        bx(f"pl_win{k}", (x0 + 6.0 + k * 19.0, 14.0, z1), (x0 + 18.0 + k * 19.0, 24.0, z1 + 0.4), m["glass"], root)
    D.tube("pl_stack", (x0 + 10.0, 34.0, z0 + 10.0), (x0 + 10.0, 62.0, z0 + 10.0), 3.0, m["steel"], root, 12)
    bx("dock", (x1 - 30.0, 0.0, z1), (x1, 4.0, z1 + 22.0), m["dark"], root)
    crates = []
    for i in range(3):
        for j in range(2):
            e = empty(f"crate{i}{j}", root)
            cx, cz = x1 - 26.0 + i * 9.0, z1 + 4.0 + j * 9.0
            bx(f"crate{i}{j}_b", (cx, 4.0, cz), (cx + 7.5, 11.0, cz + 7.5), m["crate"], e)
            bx(f"crate{i}{j}_g", (cx + 1.0, 11.0, cz + 1.0), (cx + 6.5, 11.3, cz + 6.5), m["nvg"], e)
            crates.append(e)
    # revenue column in front of the plant: segments switch on one by one through beat 1
    col = []
    bx("rev_frame", (VX - 46.0, 0.0, -24.0), (VX - 34.0, 1.0, -12.0), m["dark"], root)
    for k in range(10):
        e = empty(f"rev{k}", root)
        bx(f"rev{k}_s", (VX - 45.0, 1.0 + k * 6.0, -23.0), (VX - 35.0, 6.0 + k * 6.0, -13.0), m["rev"], e)
        col.append(e)
    for k, e in enumerate(col):
        if k < 3:
            show(e, [(0, F(4, 0.4))])
        else:
            show(e, [(F(1, 0.1 + 0.08 * (k - 3)), F(4, 0.4))])
    return crates, {"top": (VX, 44.0, -65.0), "dock": (x1 - 15.0, 11.0, z1 + 10.0), "rev": (VX - 40.0, 62.0, -18.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (VX - 80.0, -3.5, -140.0), (LX + 80.0, -3.0, 60.0), m["floor"], root)
    bx("road", (VX - 60.0, -3.0, 10.0), (LX + 60.0, -2.8, 26.0), m["road"], root)
    crates, vp = plant(m, root)

    # the neocloud hall, cut open at the front
    bx("hall_floor", (HX0, -3.0, HZ0), (HX1, 0.0, 0.0), m["floor"], root)
    bx("hall_back", (HX0, 0.0, HZ0 - 4.0), (HX1, HY, HZ0), m["wall"], root)
    for x in (HX0 - 4.0, HX1):
        bx(f"hall_side{x:.0f}", (x, 0.0, HZ0 - 4.0), (x + 4.0, HY, 0.0), m["wall"], root)
    leds = empty("leds", root)
    racks = {}
    for zc in ROWS:
        for x in RX:
            g = N.gpu_rack(m, root, f"r{zc:.0f}_{x:.0f}", x, zc, leds, spine=x == RX[-1])
            racks[(zc, x)] = g
    # half the front row's racks arrive in beat 1 (bought with the loan)
    for k, x in enumerate(RX[4:-1]):
        show(racks[(ROWS[-1], x)], [(F(1, 0.4 + 0.1 * k), F(5, 0))])
    blink(leds, 2, [0, 2, 4, 6], n=8, on=0.7)
    for zc in ROWS:
        rise(root, f"heat{zc:.0f}", (-30.0, 58.0, zc), 6, 1.1, m["heat"], [1, 2], 0.3, 0.9, 14.0, 40, (60.0, 3.0))

    # the AI lab on the right
    bx("lab", (LX - 30.0, 0.0, -100.0), (LX + 30.0, 70.0, -40.0), m["glass"], root)
    for f in range(7):
        bx(f"lab_f{f}", (LX - 30.3, 8.0 + f * 9.0, -100.0), (LX + 30.3, 9.0 + f * 9.0, -39.7), m["white"], root)
    lab_glow = empty("lab_glow", root)
    for f in range(7):
        bx(f"lab_l{f}", (LX - 28.0, 3.0 + f * 9.0, -39.6), (LX + 28.0, 7.0 + f * 9.0, -39.3), m["contract"], lab_glow)
    show(lab_glow, [(0, F(4, 0.3))])

    money = m["money"]
    # beat 0: vendor -> neocloud: loan / equity beads along an arc over the road
    fund = [(VX + 20.0, 44.0, -30.0), (VX + 70.0, 70.0, -10.0), (HX0 - 10.0, 60.0, -10.0), (HX0 + 20.0, 40.0, -10.0)]
    run(root, "fund", fund, 10, 2.0, money, [0, 1], 0.05, 0.6, 50)
    # a stake certificate that drops into the neocloud hall
    stake = empty("stake", root)
    bx("stake_c", (HX0 + 10.0, 72.0, -20.0), (HX0 + 30.0, 86.0, -19.0), m["paper"] if "paper" in m else m["white"], stake)
    bx("stake_seal", (HX0 + 24.0, 74.0, -19.0), (HX0 + 28.0, 78.0, -18.6), money, stake)
    show(stake, [(F(0, 0.3), F(5, 0))])

    # beat 1: the same money goes back as orders; crates truck to the hall
    run(root, "orders", [(HX0 + 10.0, 30.0, -8.0), (VX + 70.0, 30.0, -8.0), (VX + 40.0, 20.0, -26.0)], 10, 1.6, money, 1, 0.0, 0.5, 40)
    run(root, "gpus", [vp["dock"], (VX + 60.0, 6.0, 18.0), (HX0 + 60.0, 6.0, 18.0), (HX0 + 80.0, 20.0, ROWS[-1])], 6, 3.0, m["nvg"], 1, 0.2, 0.8, 50)
    for e in crates[:3]:
        show(e, [(0, F(1, 0.5)), (F(3, 0), F(5, 0))])
    for e in crates[3:]:
        show(e, [(0, F(5, 0))])

    # beat 2: compute out to the lab, rent back, loan repaid
    for k in range(3):
        run(root, f"compute{k}", [(HX1, 30.0 + 8.0 * k, -50.0), (LX - 30.0, 30.0 + 8.0 * k, -50.0)], 6, 1.3, m["sig"], [2, 3], 0.0, 0.8, 30)
    run(root, "rent", [(LX - 30.0, 10.0, -30.0), (HX1, 10.0, -30.0), (HX0 + 30.0, 10.0, -5.0)], 8, 1.5, money, [2, 3], 0.1, 0.7, 40)
    run(root, "repay", [(HX0 + 10.0, 50.0, -5.0), (HX0 - 30.0, 80.0, 0.0), (VX + 50.0, 60.0, -20.0), (VX + 20.0, 46.0, -40.0)], 8, 1.5, money, 2, 0.4, 0.95, 50)

    # beat 3: the backstop strap from the plant round the hall, and a rent-back pipe
    strap = empty("strap", root)
    pts = [(VX + 50.0, 30.0, -60.0), (HX0 - 4.0, 30.0, -60.0), (HX0 - 4.0, 30.0, 2.0), (HX1 + 4.0, 30.0, 2.0),
           (HX1 + 4.0, 30.0, HZ0 - 6.0), (HX0 - 4.0, 30.0, HZ0 - 6.0), (HX0 - 4.0, 30.0, -60.0)]
    D.polyline("strap_l", pts, 1.0, m["strap"], strap)
    D.polyline("strap_l2", [(p[0], 36.0, p[2]) for p in pts[1:]], 1.0, m["strap"], strap)
    show(strap, [(F(3, 0.1), F(5, 0))])
    run(root, "rentback", [(HX0 + 30.0, 36.0, -60.0), (VX + 50.0, 36.0, -62.0)], 6, 1.6, m["sig"], 3, 0.3, 0.9, 40)

    # beat 4: demand falls: lab dims, loop broken, warn beads, revenue column drops
    brk = empty("break", root)
    for k in range(4):
        bx(f"brk{k}", (VX + 72.0 + k * 3.0, 54.0 + (k % 2) * 4.0, -12.0), (VX + 74.0 + k * 3.0, 60.0 + (k % 2) * 4.0, -10.0), m["warn"], brk)
    show(brk, [(F(4, 0.2), F(5, 0))])
    blink(brk, 4, [2, 3, 4, 5, 6, 7], n=8, on=0.5)
    run(root, "writedown", [(HX0 + 20.0, 80.0, -20.0), (VX + 20.0, 46.0, -40.0)], 6, 1.6, m["warn"], 4, 0.3, 0.9, 40)
    rise(root, "fall", (LX, 72.0, -70.0), 5, 1.2, m["warn"], 4, 0.3, 0.9, 16.0, 40, (20.0, 10.0))

    tags = {
        0: [("chip vendor", vp["top"]), ("loan or equity stake", (VX + 70.0, 70.0, -10.0)),
            ("neocloud customer", (-30.0, HY, HZ0))],
        1: [("orders come back", (VX + 70.0, 30.0, -8.0)), ("GPUs shipped", (HX0 + 40.0, 8.0, 18.0)),
            ("booked as revenue", vp["rev"])],
        2: [("AI lab rents compute", (LX, 70.0, -70.0)), ("rent pays the loan", (HX0 + 10.0, 50.0, -5.0))],
        3: [("guarantee / backstop", (-20.0, 36.0, 2.0)), ("vendor rents back spare", (VX + 60.0, 36.0, -62.0)),
            ("in the commitments note", vp["top"])],
        4: [("demand falls", (LX, 72.0, -70.0)), ("loop breaks", (VX + 76.0, 62.0, -10.0)),
            ("NVDA CRWV ORCL AMD", vp["rev"])],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-160.0, 30.0, -40.0), 230.0, 0.20, 0.45),
        frame((-140.0, 25.0, -30.0), 260.0, 0.10, 0.45),
        frame((-30.0, 35.0, -40.0), 330.0, -0.15, 0.45),
        frame((-100.0, 30.0, -40.0), 330.0, 0.15, 0.55),
        frame((-60.0, 35.0, -40.0), 420.0, 0.0, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
