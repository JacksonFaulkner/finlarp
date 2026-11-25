"""TRM_TAM: the Terms-tab overview for total addressable market, at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_tam.py

A sizing idea, so the scene is its own: a giant 300 mm wafer on a tilted stand stands for one
year's spending in a category, every die a slice of dollars. A wedge of it lights as the SAM (the
part a company's products can reach), a smaller patch lifts out as the SOM (what it can win).
Then the dies take vendor colours, and a ring of new dies grows round the edge as the market
expands, with a forecast bar chart beside it.

Beats:
  0 tam       the whole wafer: all annual spending in the category
  1 sam       the wedge the company's products can serve
  2 som       the share it can realistically win lifts out
  3 vendors   the dies split by vendor; the market is shared
  4 growth    a new ring grows; forecasts climb, methods are rarely disclosed
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, P, empty, key, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_TAM"
BEATS = [
    ("TAM: everything buyers spend on a category in a year",
     "Total addressable market is the yearly spending on a product category if one company won every sale. Picture "
     "the whole wafer as that market and each die as a slice of dollars. For AI accelerators, managements have quoted "
     "numbers in the hundreds of billions to a trillion dollars a year by the end of the decade."),
    ("SAM: the part its products can actually serve",
     "No company sells into the whole category. The serviceable addressable market is the wedge its products, "
     "regions and customers can reach: a networking firm's SAM in AI is switches and optics, not GPUs. SAM is the "
     "honest ceiling for a single company."),
    ("SOM: the share it can realistically win",
     "Within the SAM, competitors, capacity and customer habits limit what can be won. The serviceable obtainable "
     "market is that realistic share. Revenue forecasts are built from the SOM, so a huge TAM with a tiny SOM means "
     "little for the next few years."),
    ("The same market is split among many vendors",
     "Every die in the wafer goes to somebody: Nvidia GPUs, custom ASICs from Broadcom and Marvell, AMD, memory from "
     "Micron and SK hynix, switches from Arista. Each vendor tends to cite the whole TAM, so adding up their "
     "claims usually gives more than the market can hold."),
    ("TAMs grow and get revised; the method is rarely shown",
     "TAM figures come from earnings calls, investor days and analyst models, and they move as capex plans move. The "
     "filings seldom show how they were built, so check what spending is counted and over what years. Related: "
     "NVIDIA (NVDA), Broadcom (AVGO), Micron (MU), Arista Networks (ANET)."),
]

R = 100.0  # wafer radius
CY = 108.0  # wafer centre height on its stand
TILT = 0.0
PITCH = 9.0
SAM = (math.radians(20.0), math.radians(95.0))  # wedge angles (in the wafer plane, from +x)
SOM = (math.radians(45.0), math.radians(70.0), 45.0, 85.0)  # angle range + radius range
VENDORS = [("v_nv", 0.42), ("v_asic", 0.18), ("v_amd", 0.10), ("v_mem", 0.18), ("v_net", 0.12)]


def mats(m):
    m["wafer"] = mat("tam_wafer", (0.30, 0.32, 0.40), metal=0.85, rough=0.15)
    m["die_t"] = mat("tam_die", (0.42, 0.40, 0.55), metal=0.6, rough=0.25)
    m["sam_g"] = mat("tam_sam", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=2.5)
    m["som_g"] = mat("tam_som", (1.0, 0.75, 0.25), emit=(1.0, 0.70, 0.20), strength=3.5)
    m["v_nv"] = mat("tam_nv", (0.45, 0.85, 0.20), emit=(0.40, 0.85, 0.15), strength=2.0)
    m["v_asic"] = mat("tam_asic", (0.90, 0.30, 0.30), emit=(0.90, 0.25, 0.25), strength=2.0)
    m["v_amd"] = mat("tam_amd", (0.95, 0.55, 0.20), emit=(0.95, 0.50, 0.15), strength=2.0)
    m["v_mem"] = mat("tam_mem", (0.55, 0.45, 1.0), emit=(0.50, 0.40, 1.0), strength=2.0)
    m["v_net"] = mat("tam_net", (0.30, 0.85, 0.90), emit=(0.25, 0.85, 0.90), strength=2.0)
    m["new"] = mat("tam_new", (0.95, 0.95, 1.0), emit=(0.90, 0.92, 1.0), strength=1.4)
    m["floor"] = mat("tam_floor", (0.42, 0.44, 0.48), rough=0.7)
    m["money"] = mat("tam_money", (1.0, 0.85, 0.30), emit=(1.0, 0.80, 0.25), strength=3.5)


def wp(u, v, d=0.0):
    """Wafer-plane point (u right, v up) standing at z = d in front of the wafer face (z = 0)."""
    return (u, CY + v, d)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-200.0, -4.0, -140.0), (230.0, -3.0, 80.0), m["floor"], root)
    # stand: a base plate, two posts, a cradle
    bx("stand_base", (-60.0, -3.0, -40.0), (60.0, 2.0, 20.0), m["dark"], root)
    for s in (-1, 1):
        bx(f"stand_post{s}", (s * 50.0 - 3.0, 2.0, -12.0), (s * 50.0 + 3.0, CY - 60.0, -6.0), m["steel"], root)
    D.tube("cradle", (-55.0, CY - 60.0, -9.0), (55.0, CY - 60.0, -9.0), 2.0, m["steel"], root, 12)
    # the wafer disc, facing the camera (+z)
    D.tube("wafer_disc", (0.0, CY, -3.0), (0.0, CY, 0.0), R, m["wafer"], root, 96)
    bx("notch", (-3.0, CY - R - 0.2, -3.2), (3.0, CY - R + 3.0, 0.2), m["dark"], root)
    # dies
    base, sam, som_lift, vend = [], [], [], {k: [] for k, _ in VENDORS}
    sam_g, som_g = empty("sam_glow", root), empty("som", root)
    vg = {k: empty(f"vend_{k}", root) for k, _ in VENDORS}
    n = int(R // PITCH) + 1
    idx = 0
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            u, v = i * PITCH, j * PITCH
            rr = math.hypot(u, v) + PITCH * 0.72
            if rr > R - 2.0:
                continue
            a = math.atan2(v, u) % (2 * math.pi)
            r0 = math.hypot(u, v)
            h = PITCH * 0.42
            lo, hi = wp(u - h, v - h, 0.0), wp(u + h, v + h, 0.8)
            in_som = SOM[0] <= a <= SOM[1] and SOM[2] <= r0 <= SOM[3]
            if in_som:
                bx(f"som_d{idx}", (lo[0], lo[1], 0.2), (hi[0], hi[1], 1.2), m["som_g"], som_g)
                base.append(bx(f"d{idx}", lo, (hi[0], hi[1], 0.6), m["die_t"], root))
            else:
                base.append(bx(f"d{idx}", lo, hi, m["die_t"], root))
            if SAM[0] <= a <= SAM[1] and not in_som:
                sam.append(bx(f"sam_d{idx}", (lo[0], lo[1], 0.8), (hi[0], hi[1], 1.1), m["sam_g"], sam_g))
            # vendor colour by angle share (pie)
            acc = 0.0
            for k, share in VENDORS:
                acc += share
                if a / (2 * math.pi) <= acc + 1e-6:
                    vend[k].append(bx(f"{k}_d{idx}", (lo[0], lo[1], 0.8), (hi[0], hi[1], 1.15), m[k], vg[k]))
                    break
            idx += 1
    D.join(base, "dies")
    D.join(sam, "sam_m")
    for k in vend:
        D.join(vend[k], f"{k}_m")
    show(sam_g, [(F(1, 0.15), F(3, 0))])
    for k in vg:
        show(vg[k], [(F(3, 0.15), F(5, 0))])
    # SAM wedge outline: two glowing spokes
    for k, a in enumerate(SAM):
        e = empty(f"spoke{k}", root)
        D.polyline(f"spoke{k}_l", [wp(0, 0, 1.4), wp(R * math.cos(a), R * math.sin(a), 1.4)], 0.5, m["sam_g"], e)
        show(e, [(F(1, 0.1), F(3, 0))])
    # SOM patch lifts out toward the camera in beat 2 and stays there
    show(som_g, [(F(1, 0.6), F(5, 0))])
    key(som_g, 0, "location", P(0, 0, 0))
    key(som_g, F(2, 0.1), "location", P(0, 0, 0))
    key(som_g, F(2, 0.4), "location", P(0, 0, 22.0))
    key(som_g, F(3, 0.1), "location", P(0, 0, 22.0))
    key(som_g, F(3, 0.3), "location", P(0, 0, 0))
    cx = (SOM[2] + SOM[3]) / 2 * math.cos((SOM[0] + SOM[1]) / 2)
    cyv = (SOM[2] + SOM[3]) / 2 * math.sin((SOM[0] + SOM[1]) / 2)
    run(root, "som_cash", [wp(cx, cyv, 24.0), wp(cx + 40.0, cyv - 30.0, 30.0), (150.0, 40.0, 10.0)], 8, 1.4, m["money"], 2, 0.4, 0.95, 40)

    # beat 4: an outer ring grows round the wafer: the market expands
    ring = empty("ring_new", root)
    D.tube("ring_disc", (0.0, CY, -3.4), (0.0, CY, -0.4), R + 16.0, m["wafer"], ring, 96)
    newd = []
    for k in range(72):
        a = 2 * math.pi * k / 72
        rr = R + 8.0
        u, v = rr * math.cos(a), rr * math.sin(a)
        newd.append(bx(f"nd{k}", wp(u - 3.0, v - 3.0, -0.4), wp(u + 3.0, v + 3.0, 0.6), m["new"], ring))
    D.join(newd, "nd_m")
    show(ring, [(F(4, 0.1), F(5, 0))])

    # forecast bars on the right: one per year, appearing one after another in beat 4
    bars = []
    for k, h in enumerate((18.0, 28.0, 40.0, 55.0, 72.0, 92.0)):
        x = 130.0 + k * 14.0
        e = empty(f"yr{k}", root)
        bx(f"yr{k}_b", (x, 0.0, -10.0), (x + 10.0, h, 0.0), m["v_nv"] if k < 3 else m["sam_g"], e)
        bx(f"yr{k}_cap", (x - 0.5, h, -10.5), (x + 10.5, h + 1.0, 0.5), m["alu"], e)
        bars.append(e)
        show(e, [(0, F(4, 0))] if k < 3 else [(F(4, 0.15 + 0.15 * (k - 3)), F(5, 0))])
    bx("chart_base", (126.0, -3.0, -14.0), (216.0, 0.0, 4.0), m["dark"], root)
    rise(root, "hype", (195.0, 92.0, -5.0), 6, 1.0, m["money"], 4, 0.6, 0.95, 18.0, 30, (8.0, 3.0))

    # beat 3: purchase beads from each vendor sector out to a buyer stack on the left
    for k, (key_, share) in enumerate(VENDORS):
        a0 = sum(s for _, s in VENDORS[:k]) * 2 * math.pi
        a = a0 + share * math.pi
        p0 = wp(60.0 * math.cos(a), 60.0 * math.sin(a), 2.0)
        run(root, f"buy{k}", [p0, wp(60.0 * math.cos(a) * 1.6, 60.0 * math.sin(a) * 1.6, 12.0)], 4, 1.2, m[key_], 3, 0.2 + 0.05 * k, 0.8, 30)

    sx, sy = 70.0 * math.cos(math.radians(60)), 70.0 * math.sin(math.radians(60))
    tags = {
        0: [("one year of category spend", wp(-60.0, 70.0, 1.0)), ("every die = slice of $", wp(-30.0, -30.0, 1.0)),
            ("TAM", wp(-80.0, -40.0, 1.0))],
        1: [("SAM: what it can serve", wp(sx, sy, 2.0)), ("rest: other products", wp(-50.0, -40.0, 1.0))],
        2: [("SOM: what it can win", wp(cx, cyv, 24.0)), ("feeds the revenue model", (150.0, 30.0, 10.0))],
        3: [("Nvidia GPUs", wp(40.0, 50.0, 1.5)), ("custom ASICs", wp(-55.0, -5.0, 1.5)),
            ("memory", wp(15.0, -60.0, 1.5)), ("networking", wp(60.0, -20.0, 1.5))],
        4: [("market grows outward", wp(-80.0, 80.0, 1.0)), ("forecasts climb", (195.0, 93.0, -5.0)),
            ("NVDA AVGO MU ANET", (150.0, 40.0, -5.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, CY, 0.0), 230.0, 0.15, 0.10),
        frame((0.0, CY, 0.0), 220.0, -0.10, 0.10),
        frame((25.0, CY + 30.0, 10.0), 140.0, 0.45, 0.15),
        frame((0.0, CY, 0.0), 220.0, 0.05, 0.05),
        frame((50.0, CY - 10.0, 0.0), 330.0, -0.15, 0.12, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
