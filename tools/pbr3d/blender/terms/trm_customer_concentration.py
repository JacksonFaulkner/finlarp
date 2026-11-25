"""TRM_CUSTOMER_CONCENTRATION: the Terms-tab overview for customer concentration.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_customer_concentration.py

A business term, so the scene is its own: a chip/server supplier's plant on the left, feeding a
street of customers on the right through order pipes: four thick glowing pipes to hyperscaler
campuses and a fan of thin lines to small buyers. Behind them stands a revenue-share bar wall
with a glowing 10% disclosure line. One hyperscaler cuts its order and the plant dims.

Beats:
  0 many      the plant ships to a crowd of customers
  1 few       four thick pipes: a few hyperscalers take most of the output
  2 ten pct   revenue-share bars; anyone past the 10% line must be disclosed
  3 cut       one big buyer cuts orders: its pipe goes dark, revenue drops
  4 why       leverage runs both ways; related tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_CUSTOMER_CONCENTRATION"
BEATS = [
    ("Customer concentration: how much revenue a few buyers make up",
     "A supplier's revenue is the sum of what every customer buys. If thousands of customers each buy a little, "
     "losing one hardly matters. If a handful buy most of the output, the company's results depend on those few "
     "purchase decisions."),
    ("In AI hardware a few hyperscalers buy most of the output",
     "Microsoft, Amazon, Google, Meta and Oracle build most of the world's AI data centers, so chip, network and "
     "server suppliers sell a large share of their output to them. A supplier can have two or three customers "
     "making up half its revenue. Big orders arrive as large, lumpy purchase commitments."),
    ("Filers must disclose any customer at 10% or more",
     "US rules require a company to say when a single customer accounts for 10% or more of revenue, usually as "
     "'Customer A, B, C' in the 10-K notes with the percentage. Risk factors often describe the largest buyers "
     "and what would happen if they cut back. Adding up these disclosures shows how concentrated a supplier is."),
    ("One buyer pulling back can move the whole company",
     "When a large customer pauses, switches to a rival, or designs its own chip in house, the supplier's revenue "
     "can fall by a double-digit percentage in a quarter. Fixed costs stay, so margins fall faster than revenue. "
     "Big buyers also use their weight to push prices down."),
    ("Concentration cuts both ways",
     "Selling to the biggest spenders means fast growth while their capex rises, and long design-in relationships "
     "are hard to displace. But the same few budgets drive the stock up and down, and in-house silicon programs are "
     "a standing threat. Related: NVIDIA (NVDA), Broadcom (AVGO), Marvell (MRVL), Super Micro Computer (SMCI)."),
]

PX, PZ = -150.0, -40.0  # plant centre
BIG_X = 120.0
BIG_Z = [-130.0, -85.0, -40.0, 5.0]
SHARES = [0.22, 0.17, 0.13, 0.11]  # the four big customers' revenue shares
SMALL = [(70.0 + 22.0 * (k % 5), 50.0 + 16.0 * (k // 5)) for k in range(15)]  # small buyers x, z
WALLX0, WALLZ = -80.0, -175.0


def mats(m):
    m["ground"] = mat("cc_ground", (0.40, 0.43, 0.45), rough=0.85)
    m["plantw"] = mat("cc_plant", (0.70, 0.72, 0.74), metal=0.3, rough=0.6)
    m["roof"] = mat("cc_roof", (0.30, 0.32, 0.36), metal=0.6, rough=0.4)
    m["glass"] = mat("cc_glass", (0.28, 0.42, 0.58), metal=0.4, rough=0.15)
    m["pipe"] = mat("cc_pipe", (0.25, 0.27, 0.30), metal=0.7, rough=0.35)
    m["order"] = mat("cc_order", (0.35, 0.85, 1.0), emit=(0.30, 0.80, 1.0), strength=3.5)
    m["thin"] = mat("cc_thin", (0.40, 0.90, 0.55), emit=(0.35, 0.85, 0.50), strength=2.5)
    m["bar"] = mat("cc_bar", (0.30, 0.55, 0.95), metal=0.3, rough=0.4)
    m["bar_hi"] = mat("cc_bar_hi", (1.0, 0.65, 0.25), emit=(1.0, 0.60, 0.20), strength=0.5)
    m["gate"] = mat("cc_gate", (1.0, 0.30, 0.20), emit=(1.0, 0.25, 0.15), strength=3.5)
    m["wallbk"] = mat("cc_wall", (0.05, 0.06, 0.08), rough=0.5)
    m["lit"] = mat("cc_lit", (1.0, 0.85, 0.50), emit=(1.0, 0.80, 0.45), strength=3.0)


def plant(m, root):
    x, z = PX, PZ
    g = empty("plant", root)
    bx("pl_body", (x - 45.0, 0.0, z - 60.0), (x + 45.0, 36.0, z + 60.0), m["plantw"], g)
    for k in range(6):  # saw-tooth roof
        zz = z - 60.0 + k * 20.0
        bx(f"pl_roof{k}", (x - 45.0, 36.0, zz), (x + 45.0, 42.0, zz + 12.0), m["roof"], g)
        bx(f"pl_sky{k}", (x - 44.0, 36.0, zz + 12.0), (x + 44.0, 42.0, zz + 13.0), m["glass"], g)
    for k in range(2):
        D.tube(f"pl_stack{k}", (x - 25.0 + 20.0 * k, 36.0, z - 45.0), (x - 25.0 + 20.0 * k, 75.0, z - 45.0), 4.0, m["steel"], g, 16)
    bx("pl_dock", (x + 45.0, 0.0, z - 40.0), (x + 52.0, 14.0, z + 40.0), m["dark"], g)
    for k in range(6):
        bx(f"pl_door{k}", (x + 52.0, 1.0, z - 36.0 + k * 13.0), (x + 52.4, 11.0, z - 27.0 + k * 13.0), m["alu"], g)
    # cut-away front: the line inside (boards on a conveyor) visible through an open front at z+60
    bx("pl_belt", (x - 40.0, 6.0, z + 48.0), (x + 40.0, 8.0, z + 56.0), m["rubber"], g)
    for k in range(9):
        xx = x - 36.0 + k * 9.0
        bx(f"pl_brd{k}", (xx, 8.0, z + 49.0), (xx + 6.0, 9.2, z + 55.0), m["pcb_blue"], g)
        bx(f"pl_chip{k}", (xx + 2.0, 9.2, z + 51.0), (xx + 4.0, 10.2, z + 53.0), m["die"], g)
    lit_full = empty("pl_lit", root)
    lit_dim = empty("pl_dim", root)
    for k in range(10):
        xx = x - 40.0 + k * 8.5
        bx(f"pl_win{k}", (xx, 20.0, z + 60.0), (xx + 5.0, 28.0, z + 60.6), m["lit"], lit_full)
        if k % 3 == 0:
            bx(f"pl_wind{k}", (xx, 20.0, z + 60.0), (xx + 5.0, 28.0, z + 60.6), m["lit"], lit_dim)
    show(lit_full, [(0, F(3, 0.45))])
    show(lit_dim, [(F(3, 0.45), F(5, 0))])
    rise(root, "pl_smoke", (x - 15.0, 76.0, z - 45.0), 8, 1.4, m["heat"], [0, 1, 2], 0.0, 0.9, 25.0, 50, (10.0, 1.0))
    return {"dock": (x + 52.0, 10.0, z), "line": (x, 10.0, z + 56.0), "c": (x, 30.0, z), "win": (x, 28.0, z + 60.0)}


def campus(m, root, k, z):
    """A hyperscaler data center campus: two long halls, cooling units on the roof."""
    g = empty(f"hs{k}", root)
    for j in range(2):
        x0 = BIG_X + j * 34.0
        bx(f"hs{k}_hall{j}", (x0, 0.0, z - 15.0), (x0 + 30.0, 20.0, z + 15.0), m["concrete"] if "concrete" in m else m["plantw"], g)
        for c in range(3):
            bx(f"hs{k}_ac{j}{c}", (x0 + 3.0 + c * 9.0, 20.0, z - 10.0), (x0 + 9.0 + c * 9.0, 24.0, z + 10.0), m["dark"], g)
            D.tube(f"hs{k}_fan{j}{c}", (x0 + 6.0 + c * 9.0, 24.0, z), (x0 + 6.0 + c * 9.0, 24.3, z), 2.5, m["alu"], g, 16)
    return (BIG_X + 32.0, 26.0, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-220.0, -2.0, -200.0), (230.0, 0.0, 110.0), m["ground"], root)
    pl = plant(m, root)
    dock = pl["dock"]

    # the thin lines to small buyers: always there, beads all beats
    for k, (x, z) in enumerate(SMALL):
        bx(f"sm{k}", (x - 5.0, 0.0, z - 5.0), (x + 5.0, 8.0 + 3.0 * (k % 3), z + 5.0), m["glass"], root)
        bx(f"sm_roof{k}", (x - 5.5, 8.0 + 3.0 * (k % 3), z - 5.5), (x + 5.5, 9.0 + 3.0 * (k % 3), z + 5.5), m["roof"], root)
        path = [(dock[0], 2.0, dock[2] + 30.0), (20.0, 2.0, z), (x - 5.0, 2.0, z)]
        D.polyline(f"thin{k}", path, 0.25, m["pipe"], root)
        run(root, f"tb{k}", path, 2, 0.7, m["thin"], [0, 1, 2, 3, 4], 0.05 * (k % 5), 0.6 + 0.05 * (k % 5), 50)

    # the four thick pipes to hyperscalers
    hs = []
    for k, z in enumerate(BIG_Z):
        hs.append(campus(m, root, k, z))
        r = 1.0 + 6.0 * SHARES[k]
        y = 6.0 + 2.0 * k
        path = [(dock[0], y, dock[2] - 30.0 + 12.0 * k), (40.0, y, z), (BIG_X, y, z)]
        D.polyline(f"thick{k}", path, r, m["pipe"], root)
        beats = [1, 2, 3, 4] if k != 0 else [1, 2]
        run(root, f"ob{k}", [(p[0], p[1] + r + 0.8, p[2]) for p in path], 7, 1.0 + r * 0.35, m["order"], beats, 0.0, 0.8, 45)
        if k == 0:  # the first big buyer's pipe glows red once it cuts
            cut = empty("cut", root)
            D.polyline("cut_pipe", [(p[0], p[1] + r + 0.3, p[2]) for p in path], 0.6, m["gate"], cut)
            show(cut, [(F(3, 0.2), F(5, 0))])
            # a valve closing on it
            vx = 60.0
            bx("valve", (vx - 3.0, y - r - 2.0, z - r - 2.0), (vx + 3.0, y + r + 6.0, z + r + 2.0), m["steel"], root)
            D.tube("valve_wheel", (vx, y + r + 7.0, z), (vx, y + r + 7.5, z), 5.0, m["gate"], root, 24)
    # beat 0 also sends a little on the big pipes so they don't look idle
    for k, z in enumerate(BIG_Z):
        run(root, f"ob0_{k}", [(dock[0], 12.0, dock[2]), (BIG_X, 12.0, z)], 2, 0.8, m["thin"], 0, 0.1 * k, 0.8, 50)

    # revenue-share wall behind: 4 big bars, then a crowd of short ones, 10% gate line
    bx("wall_bk", (WALLX0 - 8.0, 0.0, WALLZ - 3.0), (WALLX0 + 190.0, 110.0, WALLZ), m["wallbk"], root)
    scale = 300.0  # bar height per unit share
    bars = empty("bars", root)
    pts = {}
    for k, s in enumerate(SHARES):
        x0 = WALLX0 + 6.0 + k * 18.0
        h = s * scale
        if k == 0:
            b0 = empty("bar0g", root)
            bx("bar0", (x0, 4.0, WALLZ), (x0 + 12.0, 4.0 + h, WALLZ + 6.0), m["bar"], b0)
            show(b0, [(F(2, 0.0), F(3, 0.4))])
        else:
            bx(f"bar{k}", (x0, 4.0, WALLZ), (x0 + 12.0, 4.0 + h, WALLZ + 6.0), m["bar"], bars)
        hi = empty(f"bar_hi{k}", root)
        bx(f"barh{k}", (x0 - 0.3, 4.0 + 0.1 * scale, WALLZ - 0.3), (x0 + 12.3, 4.0 + h + 0.3, WALLZ + 6.3), m["bar_hi"], hi)
        show(hi, [(F(2, 0.25 + 0.1 * k), F(3, 0.4) if k == 0 else F(5, 0))])
        pts[k] = (x0 + 6.0, 4.0 + h, WALLZ + 6.0)
    # customer A's bar after the cut
    dropped = empty("bar_drop", root)
    bx("bar0_low", (WALLX0 + 5.8, 4.0, WALLZ - 0.4), (WALLX0 + 18.2, 4.0 + 0.04 * scale, WALLZ + 6.4), m["gate"], dropped)
    show(dropped, [(F(3, 0.4), F(5, 0))])
    for k in range(20):
        x0 = WALLX0 + 84.0 + k * 5.0
        h = (0.035 - 0.0012 * k) * scale
        bx(f"sbar{k}", (x0, 4.0, WALLZ), (x0 + 3.5, 4.0 + h, WALLZ + 4.0), m["bar"], bars)
    show(bars, [(F(2, 0.0), F(5, 0))])
    gate = empty("gate", root)
    bx("gate_line", (WALLX0 - 6.0, 4.0 + 0.1 * scale - 0.6, WALLZ + 6.5), (WALLX0 + 188.0, 4.0 + 0.1 * scale + 0.6, WALLZ + 7.5), m["gate"], gate)
    show(gate, [(F(2, 0.1), F(5, 0))])
    # the total revenue meter beside the plant (drops after the cut)
    mx = PX + 20.0
    bx("meter_bk", (mx - 8.0, 0.0, PZ + 76.0), (mx + 8.0, 95.0, PZ + 80.0), m["wallbk"], root)
    for lvl, iv in ((85.0, (0, F(3, 0.5))), (66.0, (F(3, 0.5), F(5, 0)))):
        e = empty(f"meter{lvl:.0f}", root)
        bx(f"meterb{lvl:.0f}", (mx - 5.0, 3.0, PZ + 80.0), (mx + 5.0, 3.0 + lvl, PZ + 83.0), m["order"], e)
        show(e, [iv])

    C.magnify(m, root, (PX, 10.0, PZ + 56.0), (PX + 10.0, 30.0, PZ + 90.0), r=3.0, name="mag")

    tags = {
        0: [("supplier's plant", pl["win"]), ("many small buyers", (SMALL[7][0], 12.0, SMALL[7][1])),
            ("revenue = sum of orders", (mx, 88.0, PZ + 83.0))],
        1: [("hyperscaler campuses", hs[1]), ("thick pipe = big share", (40.0, 14.0, BIG_Z[0])),
            ("boards for few buyers", pl["line"])],
        2: [("10% disclosure line", (WALLX0 + 120.0, 4.0 + 0.1 * scale, WALLZ + 7.0)), ("Customer A: 22%", pts[0]),
            ("Customers B, C, D", pts[2]), ("long tail under 4%", (WALLX0 + 120.0, 14.0, WALLZ + 4.0))],
        3: [("Customer A cuts orders", (60.0, 16.0, BIG_Z[0])), ("plant runs below capacity", pl["win"]),
            ("revenue drops ~20%", (mx, 69.0, PZ + 83.0)), ("A's bar falls", (WALLX0 + 12.0, 16.0, WALLZ + 6.0))],
        4: [("rides hyperscaler capex", hs[2]), ("in-house chips: a threat", hs[0]),
            ("NVDA, AVGO, MRVL, SMCI", (PX, 80.0, PZ))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-10.0, 20.0, -20.0), 330.0, 0.20, 0.55, pad=1.0),
        frame((10.0, 15.0, -60.0), 300.0, 0.30, 0.50, pad=1.0),
        frame((WALLX0 + 90.0, 50.0, WALLZ), 200.0, 0.0, 0.15),
        [(0.0, frame((-20.0, 20.0, -70.0), 300.0, 0.25, 0.45, pad=1.0)), (0.6, frame((-40.0, 40.0, -110.0), 300.0, 0.10, 0.35, pad=1.0))],
        frame((-10.0, 25.0, -60.0), 340.0, -0.25, 0.50, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
