"""TRM_ATM_OFFERING: the Terms-tab overview for an at-the-market offering.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_atm_offering.py

A company tower on the left holds a filed shelf registration and an ATM cap meter. A broker desk
in the middle drips share tokens onto a market belt to a trading floor on the right; cash beads
come back to the company's vault and fill the meter. Behind, the share-count stack grows and an
ownership bar shows existing holders' slice shrinking.

Beats:
  0 setup     company, shelf, sales agreement, cap meter
  1 dribble   the broker sells a few shares a day into normal trading
  2 cash      cash flows back; the cap meter fills
  3 dilution  the share stack grows; old holders' slice shrinks
  4 who       price pressure and the companies that use it
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, P, bx, empty, show, mat, key  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402
from sand_overview import disc, pivot, rel  # noqa: E402
from trm_yield import bar  # noqa: E402

SLUG = "TRM_ATM_OFFERING"
BEATS = [
    ("An ATM program lets a company sell new shares bit by bit into the market",
     "Instead of one big marketed deal, the company files a shelf registration with the SEC and signs a sales "
     "agreement with one or more brokers. The board sets a dollar cap, say $1-2 billion, and nothing has to be "
     "sold on any given day."),
    ("The broker drips shares into normal trading at the market price",
     "On days the company chooses, the broker sells newly issued shares into ordinary trading, often a small slice "
     "of daily volume so the price is not knocked down. There is no roadshow and no fixed discount; the broker "
     "takes a commission of around 1-3%."),
    ("Cash comes back over weeks or months until the cap is used",
     "Proceeds land in the company's account as trades settle. The company reports how much it sold, and at what "
     "average price, in its quarterly filings or a prospectus supplement. It can pause when the stock is weak and "
     "sell faster when it is strong."),
    ("Every share sold grows the share count and dilutes existing holders",
     "New shares are new claims on the same business. If a company with 500 million shares sells 25 million, "
     "each old holder owns about 5% less of it. The trade is worth it only if the cash earns more than the "
     "ownership given up."),
    ("Cash-hungry growth companies lean on it; traders watch it as steady supply",
     "AI infrastructure builders that need capital fast use ATMs alongside debt. A large open program is a steady "
     "seller in the market, which can cap rallies, so traders watch filings for new or upsized ATMs. Related: "
     "CoreWeave (CRWV), Nebius (NBIS), Super Micro Computer (SMCI), Applied Digital (APLD)."),
]

CO = (-170.0, -60.0)  # company tower x, z
BR = (0.0, -40.0)  # broker desk
MK = (170.0, -60.0)  # trading floor
BELT_Y = 14.0


def mats(m):
    m["glass"] = mat("a_glass", (0.25, 0.35, 0.48), metal=0.6, rough=0.15)
    m["floor"] = mat("a_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["paper"] = mat("a_paper", (0.92, 0.92, 0.88), rough=0.7)
    m["share"] = mat("a_share", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=3.0)
    m["cash"] = mat("a_cash", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=3.0)
    m["old"] = mat("a_old", (0.55, 0.58, 0.66), rough=0.4)
    m["new"] = mat("a_new", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=2.0)
    m["meter"] = mat("a_meter", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=2.5)
    m["red"] = mat("a_red", (1.0, 0.25, 0.15), emit=(1.0, 0.20, 0.10), strength=3.0)


def tower(m, root):
    x, z = CO
    g = empty("tower", root)
    bx("tw_core", (x - 30, 0, z - 30), (x + 30, 120, z + 30), m["glass"], g)
    for k in range(12):  # floor slabs and mullions
        bx(f"tw_fl{k}", (x - 31, 8 + 9.5 * k, z - 31), (x + 31, 9 + 9.5 * k, z + 31), m["steel"], g)
    for k in range(7):
        bx(f"tw_mu{k}", (x - 30 + 10 * k - 0.5, 0, z + 30), (x - 30 + 10 * k + 0.5, 120, z + 31.5), m["steel"], g)
    bx("tw_roof", (x - 22, 120, z - 22), (x + 22, 128, z + 22), m["car"], g)
    # vault at the tower's foot, front
    bx("vault", (x - 22, 0, z + 34), (x + 22, 34, z + 58), m["steel"], g)
    disc("vault_door", (x, 17, z + 58.5), 12, 1.5, m["chuck"] if "chuck" in m else m["steel"], g)
    # shelf registration: a stack of filing pages on a plinth with text lines
    sx, sz = x + 55, z + 40
    bx("shelf_plinth", (sx - 14, 0, sz - 12), (sx + 14, 10, sz + 12), m["car"], g)
    for k in range(5):
        bx(f"shelf_pg{k}", (sx - 10 + k * 0.4, 10 + k * 0.6, sz - 8), (sx + 10 + k * 0.4, 10.5 + k * 0.6, sz + 8), m["paper"], g)
    for k in range(6):
        bx(f"shelf_ln{k}", (sx - 8, 13.05, sz - 6 + 2.2 * k), (sx + 8 - 3 * (k % 2), 13.15, sz - 5.4 + 2.2 * k), m["ink"] if "ink" in m else m["mold"], g)
    # cap meter: glass tube beside the tower, fill bar grows
    mx = x - 50
    bx("meter_frame_l", (mx - 7, 0, z + 20), (mx - 5, 100, z + 24), m["steel"], g)
    bx("meter_frame_r", (mx + 5, 0, z + 20), (mx + 7, 100, z + 24), m["steel"], g)
    bx("meter_cap", (mx - 9, 100, z + 18), (mx + 9, 103, z + 26), m["red"], g)
    return (x, 120, z), (sx, 13, sz), (mx, 100, z + 22), (x, 34, z + 46)


def broker(m, root):
    x, z = BR
    g = empty("broker", root)
    bx("desk", (x - 30, 0, z - 14), (x + 30, 16, z + 14), m["car"], g)
    for k, dx in enumerate((-18, 0, 18)):  # screens
        bx(f"scr{k}", (x + dx - 8, 16, z - 10), (x + dx + 8, 28, z - 9), m["mold"], g)
        bx(f"scrg{k}", (x + dx - 7, 17, z - 8.9), (x + dx + 7, 27, z - 8.8), m["dim_glow"], g)
    # hopper of fresh share tokens above the desk
    for k in range(30):
        a = k * 2.4
        D.bead(f"tok{k}", (x + 8 * math.cos(a) * (k % 3 + 1) / 3, 34 + 2 * (k // 10), z + 8 * math.sin(a) * (k % 3 + 1) / 3), 1.6, m["share"], g)
    bx("hopper", (x - 12, 26, z - 12), (x + 12, 30, z + 12), m["steel"], g)
    return (x, 40, z)


def market(m, root):
    x, z = MK
    g = empty("market", root)
    bx("pit", (x - 50, 0, z - 40), (x + 50, 4, z + 40), m["steel"], g)
    bx("board", (x - 50, 20, z - 48), (x + 50, 90, z - 44), m["mold"], g)
    # price line on the ticker board (dips a little as supply comes in during beat 4)
    pts = [(x - 45 + 90 * i / 40, 55 + 12 * math.sin(i * 0.5) * 0.5 + 0.6 * i * (1 if i < 25 else -1.2), z - 43.5) for i in range(41)]
    D.polyline("price", pts, 0.6, m["sig"], g)
    for i in range(4):  # trader desks
        for j in range(2):
            bx(f"td{i}{j}", (x - 40 + 22 * i, 4, z - 10 + 26 * j), (x - 26 + 22 * i, 12, z + 2 + 26 * j), m["car"], g)
            bx(f"tdg{i}{j}", (x - 38 + 22 * i, 12, z - 8 + 26 * j), (x - 28 + 22 * i, 18, z - 7 + 26 * j), m["dim_glow"], g)
    return (x, 90, z - 46), (x, 12, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-270, -4, -220), (260, 0, 80), m["floor"], root)
    top, shelf, meter, vault = tower(m, root)
    hop = broker(m, root)
    board, floor_ = market(m, root)
    # belt from broker to market
    bx("belt", (BR[0] + 30, BELT_Y - 2, BR[1] - 4), (MK[0] - 50, BELT_Y, BR[1] + 4), m["rubber"], root)
    for k in range(8):
        D.tube(f"roll{k}", (BR[0] + 34 + 12 * k, BELT_Y - 2, BR[1] - 5), (BR[0] + 34 + 12 * k, BELT_Y - 2, BR[1] + 5), 1.6, m["steel"], root, 10)
    # agreement contract linking tower and broker
    D.polyline("agree", [(shelf[0] + 14, 6, shelf[2]), (BR[0] - 30, 6, BR[1])], 0.5, m["field"], root)

    sp = [(hop[0], hop[1] - 6, hop[2]), (BR[0] + 30, BELT_Y + 1.6, BR[1]), (MK[0] - 50, BELT_Y + 1.6, BR[1]), (MK[0], 14, MK[1])]
    run(root, "shares", sp, 10, 1.6, m["share"], [1, 2, 3, 4], 0.0, 0.8, 60)
    cp = [(MK[0], 14, MK[1] + 20), (MK[0] - 60, 10, 40.0), (BR[0], 10, 40.0), (vault[0], 20, vault[2] + 14)]
    run(root, "cash", cp, 12, 1.4, m["cash"], [2, 3, 4], 0.0, 0.8, 60)

    # cap meter fill
    pv = pivot("meter_fill", (meter[0], 0.0, meter[2]), root)
    bx("meter_f", rel((meter[0], 0, meter[2]), (meter[0] - 4.5, 0, meter[2] - 1.5)), rel((meter[0], 0, meter[2]), (meter[0] + 4.5, 1, meter[2] + 1.5)), m["meter"], pv)
    for f, h in ((0, 1e-3), (F(2, 0.05), 1e-3), (F(2, 0.95), 45.0), (F(3, 0.0), 45.0), (F(4, 0.9), 85.0)):
        key(pv, f, "scale", (1, 1, h), linear=True)

    # share stack (count) behind, grows in beat 3
    bar(m, root, "stack_old", 30.0, -190.0, 30.0, {0: 80.0}, "old")
    pv2 = pivot("stack_new", (30.0, 80.0, -190.0), root)
    bx("stack_new_b", rel((30, 80, -190), (15, 80, -205)), rel((30, 80, -190), (45, 81, -175)), m["new"], pv2)
    for f, h in ((0, 1e-3), (F(3, 0.05), 1e-3), (F(3, 0.8), 8.0)):
        key(pv2, f, "scale", (1, 1, h), linear=True)
    for k in range(8):
        bx(f"stack_ln{k}", (14.5, 10 * k, -205.5), (45.5, 10 * k + 0.6, -174.5), m["steel"], root)
    # ownership bar: old holders 100 -> ~91 of fixed width, new slice appears at the right
    ox0, ow = -150.0, 90.0
    po = pivot("own_old", (ox0, 40.0, -190.0), root)
    bx("own_old_b", rel((ox0, 40, -190), (ox0, 30, -198)), rel((ox0, 40, -190), (ox0 + 1, 50, -182)), m["old"], po)
    pn = pivot("own_new", (ox0 + ow, 40.0, -190.0), root)
    bx("own_new_b", rel((ox0 + ow, 40, -190), (ox0 + ow - 1, 30, -198)), rel((ox0 + ow, 40, -190), (ox0 + ow, 50, -182)), m["new"], pn)
    for f, a, b in ((0, ow, 1e-3), (F(3, 0.05), ow, 1e-3), (F(3, 0.8), ow * 0.91, ow * 0.09)):
        key(po, f, "scale", (a, 1, 1), linear=True)
        key(pn, f, "scale", (b, 1, 1), linear=True)
    bx("own_frame", (ox0 - 1, 29, -199), (ox0 + ow + 1, 30, -181), m["steel"], root)

    # beat 4: selling pressure on the board
    red = empty("press", root)
    for k in range(5):
        D.bead(f"press{k}", (board[0] + 10 + 6 * k, 58 - 3 * k, board[2] + 3), 1.4, m["red"], red)
    show(red, [(F(4, 0.3), F(5, 0))])

    T = {
        0: [("company files a shelf (S-3)", shelf), ("sales agreement with a broker", hop),
            ("board-set cap, e.g. $1.5B", meter), ("company", top)],
        1: [("broker sells new shares", hop), ("small slice of daily volume", (MK[0] - 60, BELT_Y + 2, BR[1])),
            ("at the market price", board)],
        2: [("cash settles back to the company", vault), ("cap meter fills", meter), ("~1-3% broker commission", hop)],
        3: [("share count grows", (30.0, 90.0, -190.0)), ("old holders: ~91%", (ox0 + 40, 50.0, -190.0)),
            ("new shares: ~9%", (ox0 + ow - 5, 50.0, -190.0))],
        4: [("steady seller can cap rallies", board), ("CRWV NBIS SMCI APLD", top), ("pause when price is weak", hop)],
    }
    C.tags(root, T)
    C.done(SLUG, BEATS, [
        frame((-60.0, 40.0, -60.0), 330.0, 0.25, 0.40),
        frame((80.0, 30.0, -50.0), 240.0, -0.15, 0.40),
        frame((-80.0, 40.0, -20.0), 260.0, 0.30, 0.35),
        frame((-50.0, 50.0, -180.0), 260.0, 0.10, 0.30),
        frame((0.0, 50.0, -80.0), 420.0, -0.20, 0.40),
    ], root)


if __name__ == "__main__":
    build()
