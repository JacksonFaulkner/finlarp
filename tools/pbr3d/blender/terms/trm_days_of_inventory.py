"""TRM_DAYS_OF_INVENTORY: the Terms-tab overview for days inventory outstanding (DIO).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_days_of_inventory.py

An accounting term, so the scene is its own: an AI server builder's warehouse cut open at the
front. Parts trucks unload onto an inbound belt on the left, pallets of GPU server boards stack
up on racks inside, finished servers leave on an outbound belt to trucks on the right. A tall
day-counter gauge by the door shows days of inventory; it climbs on a ramp and turns red when
sales stall.

Beats:
  0 formula   inventory / (cost of revenue / 365) = days of inventory
  1 balanced  in = out, stacks steady, ~60 days
  2 ramp      building ahead of a new platform: stacks grow on purpose
  3 stall     shipments slow, stacks pile up, the gauge goes red
  4 risk      write-downs, cash tied up; related tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_DAYS_OF_INVENTORY"
BEATS = [
    ("Days of inventory: how long stock sits before it sells",
     "Days inventory outstanding (DIO) = ending inventory / (cost of revenue / 365). If a company holds $3B of "
     "inventory and its yearly cost of revenue is $18B, that is about $49M a day, so roughly 61 days of inventory. "
     "It turns a balance-sheet number into time."),
    ("In balance: parts come in as fast as servers go out",
     "When purchases, production and shipments move together, inventory stays roughly flat and DIO stays steady. "
     "Every business has a normal level: a server builder with long build cycles holds more days than a retailer. "
     "The change over time matters more than the level."),
    ("A platform ramp builds stock on purpose",
     "Before a new GPU generation ships in volume, server makers buy chips, memory and chassis early and build "
     "systems ahead of customer acceptance. Inventory and DIO jump. That is healthy if those systems ship and get "
     "paid for in the next quarter or two."),
    ("If sales stall, the stacks keep growing",
     "When orders slip, a customer delays a data center, or a part shortage holds up final assembly, product "
     "keeps arriving but stops leaving. DIO climbs past its normal range. Rising DIO with flat or falling revenue "
     "is the warning sign analysts look for."),
    ("Old stock ties up cash and risks write-downs",
     "Inventory is cash already spent. If it sits too long, the next GPU generation makes it worth less and the "
     "company takes an inventory write-down that hits gross margin. Hardware makers with long build cycles watch "
     "DIO closely around ramps. Related: Super Micro Computer (SMCI), Dell (DELL), Micron (MU), NVIDIA (NVDA)."),
]

WX0, WX1, WZ0, WH = -110.0, 110.0, -110.0, 60.0  # warehouse shell, open front at z = 0
RACK_X = [-70.0, -35.0, 0.0, 35.0, 70.0]
RACK_Z = (-90.0, -50.0)
# pallet levels visible per beat (out of 5): balanced, ramp, stall, risk
LEVELS = {0: 2, 1: 2, 2: 3, 3: 5, 4: 5}
DAYS = {0: 0.42, 1: 0.42, 2: 0.62, 3: 0.95, 4: 0.95}  # gauge height fraction


def mats(m):
    m["ground"] = mat("di_ground", (0.40, 0.42, 0.44), rough=0.85)
    m["floor"] = mat("di_floor", (0.58, 0.60, 0.62), rough=0.6)
    m["wall"] = mat("di_wall", (0.74, 0.75, 0.74), rough=0.85)
    m["rackm"] = mat("di_rack", (0.15, 0.30, 0.60), metal=0.6, rough=0.4)
    m["beam"] = mat("di_beam", (0.95, 0.50, 0.10), metal=0.4, rough=0.45)
    m["pallet"] = mat("di_pallet", (0.60, 0.45, 0.28), rough=0.8)
    m["box"] = mat("di_box", (0.70, 0.55, 0.36), rough=0.75)
    m["truck"] = mat("di_truck", (0.88, 0.88, 0.86), metal=0.3, rough=0.5)
    m["cab"] = mat("di_cab", (0.20, 0.30, 0.50), metal=0.5, rough=0.4)
    m["inb"] = mat("di_in", (0.35, 0.85, 1.0), emit=(0.30, 0.80, 1.0), strength=3.5)
    m["outb"] = mat("di_out", (0.40, 1.0, 0.55), emit=(0.35, 0.95, 0.50), strength=3.5)
    m["gauge_ok"] = mat("di_gok", (0.35, 0.85, 1.0), emit=(0.30, 0.80, 1.0), strength=1.0)
    m["gauge_hi"] = mat("di_ghi", (1.0, 0.65, 0.20), emit=(1.0, 0.60, 0.15), strength=1.0)
    m["gauge_red"] = mat("di_gred", (1.0, 0.25, 0.15), emit=(1.0, 0.20, 0.10), strength=1.2)
    m["wallbk"] = mat("di_bk", (0.05, 0.06, 0.08), rough=0.5)
    m["cash"] = mat("di_cash", (0.35, 0.95, 0.45), emit=(0.30, 0.90, 0.40), strength=3.0)


def server_pallet(m, g, name, x, y, z):
    """A pallet with a stack of three server sleds (open-top so the boards show)."""
    bx(f"{name}_p", (x - 7.0, y, z - 6.0), (x + 7.0, y + 1.2, z + 6.0), m["pallet"], g)
    for k in range(3):
        yy = y + 1.2 + k * 2.2
        bx(f"{name}_s{k}", (x - 6.5, yy, z - 5.5), (x + 6.5, yy + 0.4, z + 5.5), m["alu"], g)
        bx(f"{name}_b{k}", (x - 6.0, yy + 0.4, z - 5.0), (x + 6.0, yy + 0.8, z + 5.0), m["mask"], g)
        for j in range(2):
            bx(f"{name}_g{k}{j}", (x - 4.0 + j * 5.0, yy + 0.8, z - 2.0), (x - 1.0 + j * 5.0, yy + 1.6, z + 2.0), m["cold"], g)


def rack(m, root, name, x, z):
    """A pallet rack: uprights, orange beams on five levels. Returns the level heights."""
    g = empty(name, root)
    for dx in (-9.0, 9.0):
        for dz in (-7.0, 7.0):
            bx(f"{name}_up{dx:.0f}{dz:.0f}", (x + dx - 0.6, 0.0, z + dz - 0.6), (x + dx + 0.6, 52.0, z + dz + 0.6), m["rackm"], g)
    ys = [1.0 + 10.0 * k for k in range(5)]
    for k, y in enumerate(ys):
        for dz in (-7.0, 7.0):
            bx(f"{name}_bm{k}{dz:.0f}", (x - 9.0, y - 0.8, z + dz - 0.5), (x + 9.0, y, z + dz + 0.5), m["beam"], g)
    return ys


def truck(m, root, name, x, z, facing=1):
    g = empty(name, root)
    bx(f"{name}_box", (x - 18.0, 3.0, z - 7.0), (x + 18.0, 20.0, z + 7.0), m["truck"], g)
    cx = x + facing * 24.0
    bx(f"{name}_cab", (cx - 6.0, 3.0, z - 7.0), (cx + 6.0, 15.0, z + 7.0), m["cab"], g)
    for wx in (x - 12.0, x + 10.0, cx):
        for s in (-1, 1):
            D.tube(f"{name}_w{wx:.0f}{s}", (wx, 3.0, z + s * 7.0), (wx, 3.0, z + s * 8.5), 3.0, m["rubber"], g, 16)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-230.0, -2.0, -160.0), (240.0, 0.0, 70.0), m["ground"], root)
    bx("wh_floor", (WX0, -0.5, WZ0), (WX1, 0.0, 0.0), m["floor"], root)
    bx("wh_back", (WX0, 0.0, WZ0 - 3.0), (WX1, WH, WZ0), m["wall"], root)
    for s, x in ((-1, WX0), (1, WX1)):
        bx(f"wh_side{s}", (x - 1.5, 0.0, WZ0), (x + 1.5, WH, 0.0), m["wall"], root)
        bx(f"wh_door{s}", (x - 1.6, 0.0, -38.0), (x + 1.6, 18.0, -12.0), m["dark"], root)
    for k in range(6):  # roof trusses (roof itself cut away)
        z = WZ0 + 4.0 + k * 20.0
        bx(f"wh_truss{k}", (WX0, WH - 2.0, z - 0.8), (WX1, WH, z + 0.8), m["steel"], root)

    # racks and the pallets that fill them beat by beat
    lvl_groups = [empty(f"lvl{k}", root) for k in range(5)]
    for zc in RACK_Z:
        for x in RACK_X:
            ys = rack(m, root, f"rk{x:.0f}_{zc:.0f}", x, zc)
            for k, y in enumerate(ys):
                server_pallet(m, lvl_groups[k], f"pl{x:.0f}{zc:.0f}{k}", x, y, zc)
    for k, g in enumerate(lvl_groups):
        iv = [(F(b, 0.0 if LEVELS.get(b - 1, LEVELS[b]) > k else 0.5), F(b + 1, 0)) for b in range(5) if LEVELS[b] > k]
        show(g, iv)
    # aisle overstock on the floor in the stall beats
    over = empty("over", root)
    for k in range(8):
        server_pallet(m, over, f"ov{k}", -80.0 + k * 22.0, 0.0, -22.0)
    show(over, [(F(3, 0.55), F(5, 0))])
    # dust on the old stock in the last beat
    dust = rise(root, "dust", (0.0, 50.0, -70.0), 10, 0.8, m["dim_glow"], 4, 0.0, 0.9, 10.0, 60, (70.0, 20.0))

    # inbound: trucks on the left, belt through the left door; outbound belt and trucks on the right
    truck(m, root, "tin", -175.0, -25.0, facing=-1)
    truck(m, root, "tout", 175.0, -25.0, facing=1)
    bx("belt_in", (-155.0, 4.0, -29.0), (WX0 + 20.0, 6.0, -21.0), m["rubber"], root)
    bx("belt_out", (WX1 - 20.0, 4.0, -29.0), (155.0, 6.0, -21.0), m["rubber"], root)
    for x in range(-150, int(WX0 + 20), 10):
        bx(f"leg_in{x}", (x - 0.5, 0.0, -28.0), (x + 0.5, 4.0, -22.0), m["steel"], root)
    for x in range(int(WX1 - 15), 155, 10):
        bx(f"leg_out{x}", (x - 0.5, 0.0, -28.0), (x + 0.5, 4.0, -22.0), m["steel"], root)
    pin = [(-155.0, 8.0, -25.0), (WX0 + 20.0, 8.0, -25.0), (-70.0, 10.0, -50.0)]
    pout = [(70.0, 10.0, -50.0), (WX1 - 20.0, 8.0, -25.0), (155.0, 8.0, -25.0)]
    run(root, "in_b", pin, 6, 2.0, m["inb"], [0, 1], 0.0, 0.8, 45)
    run(root, "out_b", pout, 6, 2.0, m["outb"], [0, 1], 0.1, 0.85, 45)
    run(root, "in_ramp", pin, 10, 2.0, m["inb"], [2, 3], 0.0, 0.85, 45)
    run(root, "out_ramp", pout, 4, 2.0, m["outb"], 2, 0.3, 0.85, 45)
    run(root, "out_stall", pout, 1, 2.0, m["outb"], [3, 4], 0.5, 0.5, 45)
    # beat 4: cash tied up: cash beads flow *into* the stacks and stay
    run(root, "cash_in", [(-155.0, 30.0, -25.0), (-60.0, 45.0, -70.0), (40.0, 45.0, -70.0)], 8, 1.4, m["cash"], 4, 0.0, 0.7, 50)

    # the day-counter gauge by the front corner
    gx, gz = 135.0, 20.0
    bx("g_bk", (gx - 10.0, 0.0, gz - 3.0), (gx + 10.0, 110.0, gz), m["wallbk"], root)
    for k in range(1, 7):
        y = 4.0 + k * 15.0
        bx(f"g_tick{k}", (gx - 10.0, y - 0.4, gz), (gx - 6.0, y + 0.4, gz + 0.5), m["ink"], root)
    bx("g_norm", (gx - 10.0, 4.0 + 0.5 * 100.0 - 0.5, gz), (gx + 10.0, 4.0 + 0.5 * 100.0 + 0.5, gz + 0.8), m["ink"], root)
    for b in range(5):
        e = empty(f"g{b}", root)
        mt = "gauge_ok" if DAYS[b] < 0.5 else "gauge_hi" if DAYS[b] < 0.8 else "gauge_red"
        bx(f"g_bar{b}", (gx - 5.0, 4.0, gz), (gx + 5.0, 4.0 + 100.0 * DAYS[b], gz + 2.0), m[mt], e)
        show(e, [(F(b, 0.0), F(b + 1, 0))])
    # formula plaque in beat 0: inventory pile / daily cost bar
    fx, fz = gx - 40.0, 30.0
    fg = empty("formula", root)
    bx("f_inv", (fx - 8.0, 20.0, fz), (fx + 8.0, 36.0, fz + 2.0), m["box"], fg)
    bx("f_div", (fx - 10.0, 17.5, fz), (fx + 10.0, 18.5, fz + 2.0), m["ink"], fg)
    bx("f_day", (fx - 1.0, 10.0, fz), (fx + 1.0, 16.0, fz + 2.0), m["inb"], fg)
    bx("f_post", (fx - 1.0, 0.0, fz - 1.0), (fx + 1.0, 10.0, fz), m["steel"], fg)
    show(fg, [(0, F(1, 0))])

    gtop = lambda b: (gx, 4.0 + 100.0 * DAYS[b], gz + 2.0)  # noqa: E731
    tags = {
        0: [("ending inventory", (fx, 36.0, fz + 2.0)), ("/ daily cost of revenue", (fx, 13.0, fz + 2.0)),
            ("= days of inventory", gtop(0)), ("$3B / $49M a day = 61 days", (0.0, 22.0, -50.0))],
        1: [("parts in", pin[1]), ("servers out", pout[1]), ("steady ~60 days", gtop(1))],
        2: [("building ahead of a ramp", (0.0, 32.0, -50.0)), ("purchases surge", pin[1]), ("DIO rising: planned", gtop(2))],
        3: [("shipments stall", pout[1]), ("overflow in the aisle", (-40.0, 8.0, -22.0)),
            ("DIO past normal", gtop(3)), ("stacks keep growing", (35.0, 52.0, -50.0))],
        4: [("cash tied up in stock", (-60.0, 45.0, -70.0)), ("next GPU gen: write-down", (0.0, 52.0, -50.0)),
            ("SMCI, DELL, MU, NVDA", (gx, 112.0, gz))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((60.0, 35.0, -10.0), 190.0, 0.25, 0.25),
        frame((0.0, 25.0, -40.0), 300.0, 0.10, 0.40, pad=1.0),
        frame((10.0, 30.0, -45.0), 300.0, 0.15, 0.40, pad=1.0),
        [(0.0, frame((10.0, 30.0, -45.0), 300.0, -0.15, 0.40, pad=1.0)), (0.6, frame((40.0, 35.0, -30.0), 260.0, -0.30, 0.30, pad=1.0))],
        frame((20.0, 35.0, -40.0), 320.0, 0.20, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
