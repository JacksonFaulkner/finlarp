"""TRM_NEOCLOUD: the Terms-tab overview for neoclouds, at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_neocloud.py

A neocloud is a business, not a board part, so the scene is its own: a GPU hall cut open at the
front, rows of liquid-cooled rack-scale GPU systems with network spine racks at the row ends. One
compute tray stands huge on a plinth in front, cut open (GPUs, HBM, cold plates, NICs). Outside
on the left is the developer's substation that leases the power; on the right the customers (one
big AI lab, smaller tenants) and a lender whose debt buys the GPUs against those contracts.

Beats:
  0 hall      rows of GPU racks and nothing else: a GPU-only cloud
  1 tray      one compute tray, giant and cut open: GPUs, HBM, cold plates, NICs
  2 fabric    a training job: traffic beads between racks and the spine
  3 power     megawatts leased from a data center developer's substation
  4 money     debt buys GPUs, contracts pay it back; one customer dominates
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_NEOCLOUD"
BEATS = [
    ("A neocloud is a cloud built only to rent out GPUs",
     "Neoclouds are newer cloud providers that sell one thing: time on large clusters of Nvidia GPUs for AI training "
     "and inference. Unlike AWS, Azure or Google Cloud they skip the long menu of databases, storage and software "
     "services. Their halls are rows of rack-scale GPU systems, each rack drawing well over 100 kW."),
    ("What they rent: trays of GPUs, HBM and fast NICs",
     "Each rack holds compute trays like this one: GPU packages with stacked HBM memory beside the die, cold plates "
     "carrying liquid over them, and high-speed network cards. A single rack-scale system costs a few million "
     "dollars, and a cluster has thousands of GPUs, so the hardware bill runs into the billions."),
    ("Training jobs need every GPU wired to every other",
     "A big model trains across thousands of GPUs at once, swapping gradients every step. So neoclouds build "
     "non-blocking InfiniBand or Ethernet fabrics with spine switches at the end of the rows, and sell whole "
     "clusters that behave like one machine. Getting this right at scale is a large part of their pitch."),
    ("Power is leased from data center developers",
     "Most neoclouds do not build their own power plants or grid connections. They lease powered shells from "
     "developers and ex-bitcoin miners who already hold substations and utility contracts. Power availability, "
     "measured in megawatts that can be energised by a given date, is often the real limit on growth."),
    ("Debt buys the GPUs; a few big customers pay it back",
     "GPUs are bought in bulk with debt, often secured by the GPUs and backed by multi-year take-or-pay contracts "
     "from AI labs and hyperscalers that need overflow capacity. That makes revenue lumpy and concentrated in a "
     "handful of customers, and GPUs depreciate within a few years. Related: CoreWeave (CRWV), Nebius (NBIS), IREN "
     "(IREN), Applied Digital (APLD), and supplier Nvidia (NVDA)."),
]

HX0, HX1, HZ0, HY = -150.0, 130.0, -125.0, 75.0
ROWS = (-100.0, -66.0, -32.0)
RX = [-130.0 + 16.0 * j for j in range(14)]  # rack centres x (last two are spine racks)
SPINE = RX[-2:]
TRAY = (-90.0, 70.0, -2.6, 14.0, 12.0, 52.0)  # giant tray x0, x1, y0, y1, z0, z1 (in front of the hall)
SUBX = -240.0
CUST = 190.0


def mats(m):
    m["floor"] = mat("nc_floor", (0.50, 0.52, 0.55), rough=0.7)
    m["wall"] = mat("nc_wall", (0.72, 0.73, 0.72), rough=0.85)
    m["rackm"] = mat("nc_rack", (0.06, 0.06, 0.07), metal=0.6, rough=0.45)
    m["trayc"] = mat("nc_tray", (0.30, 0.31, 0.34), metal=0.8, rough=0.35)
    m["nvg"] = mat("nc_green", (0.45, 0.85, 0.20), emit=(0.40, 0.85, 0.15), strength=3.0)
    m["led_g"] = mat("nc_led", (0.3, 1.0, 0.5), emit=(0.3, 1.0, 0.5), strength=4.0)
    m["cable"] = mat("nc_cable", (0.10, 0.10, 0.12), rough=0.6)
    m["glass"] = mat("nc_glass", (0.35, 0.50, 0.65), metal=0.3, rough=0.15)
    m["bank"] = mat("nc_bank", (0.85, 0.82, 0.74), rough=0.7)
    m["money"] = mat("nc_money", (1.0, 0.85, 0.30), emit=(1.0, 0.80, 0.25), strength=3.5)
    m["contract"] = mat("nc_contract", (0.95, 0.95, 1.0), emit=(0.90, 0.92, 1.0), strength=2.0)


def gpu_rack(m, parent, name, x, z, leds, spine=False):
    g = empty(name, parent)
    w, d, h = 12.0, 18.0, 56.0
    x0, x1, z0, z1 = x - w / 2, x + w / 2, z - d / 2, z + d / 2
    bx(f"{name}_shell", (x0, 0.0, z0), (x1, h, z0 + 1.0), m["rackm"], g)
    for a in (x0, x1 - 1.0):
        bx(f"{name}_side{a:.0f}", (a, 0.0, z0), (a + 1.0, h, z1), m["rackm"], g)
    bx(f"{name}_top", (x0, h - 1.5, z0), (x1, h, z1), m["rackm"], g)
    n = 18
    for u in range(n):
        y = 2.0 + u * (h - 5.0) / n
        hh = (h - 5.0) / n
        if spine or u in (8, 9):  # switch trays (centre of compute racks, all of spine racks)
            bx(f"{name}_sw{u}", (x0 + 1.0, y + 0.2, z0 + 1.0), (x1 - 1.0, y + hh - 0.3, z1 - 0.6), m["dark"], g)
            for p in range(5):
                bx(f"{name}_port{u}{p}", (x0 + 1.6 + p * 1.8, y + hh * 0.3, z1 - 0.6), (x0 + 2.6 + p * 1.8, y + hh * 0.7, z1 - 0.3), m["sig"], leds)
        else:
            bx(f"{name}_t{u}", (x0 + 1.0, y + 0.2, z0 + 1.0), (x1 - 1.0, y + hh - 0.3, z1 - 0.6), m["trayc"], g)
            bx(f"{name}_g{u}", (x0 + 1.6, y + hh * 0.35, z1 - 0.6), (x1 - 3.5, y + hh * 0.6, z1 - 0.4), m["nvg"], g)
            bx(f"{name}_l{u}", (x1 - 2.8, y + hh * 0.35, z1 - 0.6), (x1 - 1.8, y + hh * 0.6, z1 - 0.3), m["led_g"], leds)
    if not spine:  # liquid manifolds on the back
        for k, mt in enumerate(("cool", "hot")):
            D.tube(f"{name}_mf{k}", (x - 2.0 + 4.0 * k, 2.0, z0 - 0.8), (x - 2.0 + 4.0 * k, h - 3.0, z0 - 0.8), 0.7, m[mt], g, 8)
    return g


def tray(m, root):
    """The giant cut-open compute tray on its plinth. Returns key points and the GPU-hot group."""
    x0, x1, y0, y1, z0, z1 = TRAY
    g = empty("tray", root)
    bx("plinth", (x0 - 4.0, -6.0, z0 - 4.0), (x1 + 4.0, y0, z1 + 4.0), m["dark"], g)
    bx("tray_floor", (x0, y0, z0), (x1, y0 + 1.0, z1), m["trayc"], g)
    bx("tray_back", (x0, y0, z0), (x1, y1, z0 + 1.0), m["trayc"], g)
    bx("tray_side", (x0, y0, z0), (x0 + 1.0, y1, z1), m["trayc"], g)
    C.pcb(m, g, "tray_pcb", x0 + 3.0, x1 - 22.0, z0 + 3.0, z1 - 3.0)
    # the pcb helper builds at y 0; lift visually by the plinth floor (y0 + 1 ~ 3) is close enough
    hot = empty("gpu_hot", root)
    gpus = []
    for k in range(4):
        cx = x0 + 18.0 + k * 28.0
        cz = (z0 + z1) / 2
        bx(f"gsub{k}", (cx - 11.0, 0.0, cz - 13.0), (cx + 11.0, 1.6, cz + 13.0), m["substrate"], g)
        bx(f"gdie{k}", (cx - 5.0, 1.6, cz - 6.0), (cx + 5.0, 3.0, cz + 6.0), m["die"], g)
        bx(f"ghot{k}", (cx - 4.8, 3.0, cz - 5.8), (cx + 4.8, 3.15, cz + 5.8), m["die_hot"], hot)
        for s in (-1, 1):
            for j in range(4):
                bx(f"ghbm{k}{s}{j}", (cx + s * 6.0 - 1.8, 1.6, cz - 9.0 + j * 4.6), (cx + s * 6.0 + 1.8, 4.2, cz - 5.6 + j * 4.6), m["hbm"], g)
        # cold plate hovering, cut in half so the die shows on the front half
        bx(f"gcp{k}", (cx - 11.0, 6.0, cz - 13.0), (cx + 11.0, 9.0, cz - 1.0), m["cold"], g)
        gpus.append((cx, cz))
    # liquid loop: inlet manifold along the back, hoses into each cold plate
    D.tube("tray_in", (x0 + 4.0, 11.0, z0 + 4.0), (x1 - 24.0, 11.0, z0 + 4.0), 1.0, m["cool"], g, 10)
    D.tube("tray_out", (x0 + 4.0, 13.0, z0 + 6.5), (x1 - 24.0, 13.0, z0 + 6.5), 1.0, m["hot"], g, 10)
    for k, (cx, cz) in enumerate(gpus):
        D.tube(f"hose_in{k}", (cx - 4.0, 11.0, z0 + 4.0), (cx - 4.0, 9.0, cz - 6.0), 0.6, m["cool"], g, 8)
        D.tube(f"hose_out{k}", (cx + 4.0, 13.0, z0 + 6.5), (cx + 4.0, 9.0, cz - 6.0), 0.6, m["hot"], g, 8)
        run(root, f"lq{k}", [(x0 + 4.0, 11.0, z0 + 4.0), (cx - 4.0, 11.0, z0 + 4.0), (cx - 4.0, 9.0, cz - 6.0),
                              (cx + 4.0, 9.0, cz - 6.0), (cx + 4.0, 13.0, z0 + 6.5), (x1 - 24.0, 13.0, z0 + 6.5)],
            4, 0.8, m["cool"], 1, 0.05 + 0.08 * k, 0.6 + 0.08 * k, 50)
    # NICs at the front-right of the tray, with cage ports at the tray's front face
    for k in range(4):
        z = z0 + 6.0 + k * 9.0
        bx(f"nic{k}", (x1 - 20.0, 0.0, z), (x1 - 4.0, 1.4, z + 6.0), m["pcb_blue"], g)
        bx(f"nicchip{k}", (x1 - 15.0, 1.4, z + 1.5), (x1 - 10.0, 2.4, z + 4.5), m["mold"], g)
        bx(f"port{k}", (x1 - 1.0, 1.0, z + 1.0), (x1 + 1.0, 4.0, z + 5.0), m["alu"], g)
    show(hot, [(F(1, 0.3), F(3, 0))])
    pts = {"gpu": (gpus[1][0], 4.0, gpus[1][1]), "hbm": (gpus[2][0] + 6.0, 4.2, gpus[2][1] + 4.0),
           "cp": (gpus[0][0], 9.0, gpus[0][1] - 6.0), "nic": (x1 - 12.0, 2.4, z0 + 30.0), "c": ((x0 + x1) / 2, 6.0, (z0 + z1) / 2)}
    return pts


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (SUBX - 60.0, -3.5, HZ0 - 30.0), (CUST + 90.0, -3.0, 70.0), m["floor"], root)
    bx("hall_floor", (HX0, -3.0, HZ0), (HX1, 0.0, 0.0), m["floor"], root)
    bx("wall_back", (HX0, 0.0, HZ0 - 4.0), (HX1, HY, HZ0), m["wall"], root)
    bx("wall_l", (HX0 - 4.0, 0.0, HZ0 - 4.0), (HX0, HY, 0.0), m["wall"], root)
    bx("wall_r", (HX1, 0.0, HZ0 - 4.0), (HX1 + 4.0, HY, 0.0), m["wall"], root)
    leds = empty("leds", root)
    for zc in ROWS:
        for x in RX:
            gpu_rack(m, root, f"r{zc:.0f}_{x:.0f}", x, zc, leds, spine=x in SPINE)
        bx(f"cool_hdr{zc:.0f}", (HX0 + 4.0, 1.0, zc - 11.5), (SPINE[0] - 8.0, 3.0, zc - 10.0), m["cool"], root)
        rise(root, f"heat{zc:.0f}", (-40.0, 58.0, zc), 7, 1.1, m["heat"], [0, 1], 0.0, 0.85, 14.0, 40, (80.0, 3.0))
    # overhead cable trays from each row to the spine racks
    for zc in ROWS:
        bx(f"ctray{zc:.0f}", (HX0 + 6.0, 62.0, zc - 2.0), (SPINE[1] + 6.0, 63.0, zc + 2.0), m["yellow"] if "yellow" in m else m["gold"], root)
    bx("ctray_x", (SPINE[0] - 2.0, 66.0, ROWS[0]), (SPINE[0] + 2.0, 67.0, ROWS[-1]), m["gold"], root)
    blink(leds, 2, [0, 2, 4, 6], n=8, on=0.7)

    tp = tray(m, root)
    C.magnify(m, root, (RX[3], 30.0, ROWS[-1] + 9.0), (TRAY[0] + 20.0, 20.0, TRAY[4]), r=5.0, name="mag")

    # fabric: each compute rack row sends beads up the tray to the spine and back
    for zc in ROWS:
        for x in RX[1:-2:3]:
            run(root, f"fab{zc:.0f}{x:.0f}", [(x, 56.0, zc), (x, 64.0, zc), (SPINE[0], 64.0, zc), (SPINE[0], 50.0, zc)],
                3, 1.1, m["sig"], 2, 0.0, 0.5, 40)
            run(root, f"fbk{zc:.0f}{x:.0f}", [(SPINE[1], 50.0, zc), (SPINE[1], 65.0, zc + 1.0), (x + 4.0, 65.0, zc + 1.0), (x + 4.0, 56.0, zc + 1.0)],
                3, 1.1, m["bit"], 2, 0.35, 0.85, 40)
    run(root, "fab_x", [(SPINE[0], 68.0, ROWS[0]), (SPINE[0], 68.0, ROWS[-1])], 6, 1.2, m["sig"], 2, 0.0, 0.8, 40)

    # power: the developer's substation on the left, its own fenced lot
    sx0 = SUBX
    for k in range(3):
        D.tube(f"tower{k}", (sx0 - 30.0, 0.0, -110.0 + 45.0 * k), (sx0 - 30.0, 95.0, -110.0 + 45.0 * k), 1.5, m["steel"], root, 8)
        bx(f"tower_arm{k}", (sx0 - 40.0, 90.0, -111.0 + 45.0 * k), (sx0 - 20.0, 92.0, -109.0 + 45.0 * k), m["steel"], root)
    for k in range(2):
        z = -105.0 + 50.0 * k
        bx(f"xf{k}", (sx0, 0.0, z), (sx0 + 26.0, 30.0, z + 30.0), m["ups"] if "ups" in m else m["dark"], root)
        for f in range(6):
            bx(f"xf{k}_fin{f}", (sx0 + 26.0, 3.0, z + 2.0 + f * 4.8), (sx0 + 29.0, 26.0, z + 3.5 + f * 4.8), m["dark"], root)
        for b in range(3):
            D.tube(f"xf{k}_bush{b}", (sx0 + 6.0 + b * 7.0, 30.0, z + 15.0), (sx0 + 6.0 + b * 7.0, 40.0, z + 15.0), 1.0, m["white"], root, 10)
    for k in range(12):  # fence
        x = sx0 - 15.0 + k * 6.0
        D.tube(f"fence{k}", (x, 0.0, -5.0), (x, 14.0, -5.0), 0.3, m["steel"], root, 6)
    D.tube("fence_rail", (sx0 - 15.0, 14.0, -5.0), (sx0 + 51.0, 14.0, -5.0), 0.3, m["steel"], root, 6)
    bx("busduct", (sx0 + 29.0, 34.0, -62.0), (HX0, 38.0, -54.0), m["copper"], root)
    for zc in ROWS:
        bx(f"rowbus{zc:.0f}", (HX0, 58.0, zc + 6.0), (SPINE[0] - 8.0, 60.0, zc + 9.0), m["copper"], root)
    run(root, "grid", [(sx0 - 30.0, 92.0, -65.0), (sx0 + 13.0, 40.0, -90.0), (sx0 + 29.0, 36.0, -58.0), (HX0, 36.0, -58.0)],
        10, 2.0, m["v12"], 3, 0.0, 0.6, 50)
    for zc in ROWS:
        run(root, f"rowpw{zc:.0f}", [(HX0, 36.0, -58.0), (HX0 + 3.0, 59.0, zc + 7.5), (SPINE[0] - 10.0, 59.0, zc + 7.5)],
            6, 1.4, m["v12"], 3, 0.3, 0.8, 50)

    # customers on the right: one big AI lab and two small tenants; a lender in front
    cx = CUST
    bx("lab", (cx, 0.0, -120.0), (cx + 60.0, 70.0, -60.0), m["glass"], root)
    for f in range(7):
        bx(f"lab_floor{f}", (cx - 0.3, 8.0 + f * 9.0, -120.0), (cx + 60.3, 9.0 + f * 9.0, -59.7), m["white"], root)
    bx("t1", (cx, 0.0, -45.0), (cx + 22.0, 28.0, -25.0), m["glass"], root)
    bx("t2", (cx + 32.0, 0.0, -45.0), (cx + 52.0, 22.0, -25.0), m["glass"], root)
    bx("bank", (cx, 0.0, 10.0), (cx + 50.0, 22.0, 40.0), m["bank"], root)
    for k in range(6):
        D.tube(f"col{k}", (cx + 4.0 + k * 8.4, 0.0, 41.5), (cx + 4.0 + k * 8.4, 20.0, 41.5), 1.2, m["white"], root, 12)
    bx("bank_roof", (cx - 2.0, 22.0, 8.0), (cx + 52.0, 26.0, 44.0), m["bank"], root)
    # compute flows out: most to the lab
    for k in range(3):
        run(root, f"out_lab{k}", [(HX1, 40.0 + 6.0 * k, -90.0), (cx, 40.0 + 6.0 * k, -90.0)], 8, 1.4, m["sig"], 4, 0.0, 0.8, 30)
    run(root, "out_t1", [(HX1, 20.0, -35.0), (cx, 20.0, -35.0)], 3, 1.0, m["sig"], 4, 0.1, 0.8, 30)
    run(root, "out_t2", [(HX1, 14.0, -30.0), (cx + 32.0, 14.0, -30.0)], 2, 1.0, m["sig"], 4, 0.2, 0.8, 30)
    # contracts from the lab to the bank; debt from the bank into the hall (buying GPUs)
    run(root, "contract", [(cx + 30.0, 2.0, -60.0), (cx + 30.0, 2.0, 10.0)], 4, 1.6, m["contract"], 4, 0.0, 0.5, 40)
    run(root, "debt", [(cx, 12.0, 25.0), (HX1 + 10.0, 12.0, 25.0), (TRAY[1] + 6.0, 10.0, 30.0)], 8, 1.6, m["money"], 4, 0.3, 0.9, 40)
    run(root, "repay", [(cx + 20.0, 3.0, -60.0), (cx + 20.0, 3.0, 8.0)], 5, 1.2, m["money"], 4, 0.4, 0.95, 40)

    tags = {
        0: [("rows of rack-scale GPU systems", (-60.0, 56.0, ROWS[1])), ("100+ kW per rack", (RX[2], 56.0, ROWS[-1])),
            ("no databases, no app menu", (RX[8], 70.0, HZ0))],
        1: [("GPU die", tp["gpu"]), ("HBM stacks", tp["hbm"]), ("liquid cold plate", tp["cp"]), ("high-speed NICs", tp["nic"])],
        2: [("training job on all GPUs", (-60.0, 64.0, ROWS[0])), ("spine switches", (SPINE[1], 56.0, ROWS[1])),
            ("non-blocking fabric", (SPINE[0], 68.0, ROWS[-1]))],
        3: [("developer's substation", (sx0 + 13.0, 40.0, -55.0)), ("leased megawatts", (sx0 + 60.0, 38.0, -58.0)),
            ("power gates growth", (HX0 + 20.0, 60.0, ROWS[1]))],
        4: [("one AI lab: most of revenue", (cx + 30.0, 70.0, -90.0)), ("contracts back the debt", (cx + 30.0, 4.0, -20.0)),
            ("lender funds GPUs", (cx + 25.0, 26.0, 25.0)), ("CRWV, NBIS, IREN, APLD", (HX1, 60.0, -60.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-10.0, 25.0, -60.0), 300.0, 0.20, 0.50, pad=1.0),
        frame(((TRAY[0] + TRAY[1]) / 2, 6.0, (TRAY[4] + TRAY[5]) / 2), 160.0, 0.15, 0.75),
        frame((0.0, 40.0, -66.0), 280.0, -0.25, 0.55, pad=1.0),
        frame((-170.0, 30.0, -60.0), 230.0, 0.40, 0.40),
        frame((150.0, 25.0, -40.0), 270.0, -0.30, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
