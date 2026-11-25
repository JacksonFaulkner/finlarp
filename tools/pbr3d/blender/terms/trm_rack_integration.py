"""TRM_RACK_INTEGRATION: the Terms-tab overview for rack integration.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_rack_integration.py

Writes assets/term_TRM_RACK_INTEGRATION.glb and specs/terms/TRM_RACK_INTEGRATION.json. Units cm;
racks come from trm_rack_density's kit.

An integration line on a factory floor, left to right: pallets of parts, an empty rack frame being
filled (trays slide in), a rack being cabled and plumbed, a burn-in bay with a test cart pumping
coolant and power while the LEDs blink, and a crated rack on a truck trailer.

Beats:
  0 parts     trays, switches and power shelves arrive; an empty rack frame waits
  1 fill      trays, switch trays and power shelves slide into the frame
  2 cable     NVLink spine, network fibre, power whips and coolant hoses are connected
  3 burn-in   the rack runs flat out on a test loop for days; a failing tray is pulled
  4 ship      crated as one 1.4 t unit and trucked to the data center
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, P, empty, key, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat, present  # noqa: E402
import trm_rack_density as K  # noqa: E402

SLUG = "TRM_RACK_INTEGRATION"
BEATS = [
    ("Rack-scale AI systems are built in a factory, not in the data center",
     "Rack integration is assembling, cabling, testing and validating a whole rack of servers, switches, power and "
     "cooling before it ships. Parts arrive at an integration site run by an ODM or system maker: compute trays, "
     "NVLink switch trays, power shelves and an empty rack frame with its busbar and manifolds already fitted."),
    ("Trays, switches and power shelves slide into the frame",
     "Workers lift each tray into its slot: power shelves top and bottom, 18 compute trays and 9 NVLink switch "
     "trays for an NVL72. Each tray blind-mates to the rear busbar, the coolant manifold and the NVLink spine as "
     "it slides home, so the order and fit have to be exact."),
    ("Then it is cabled and plumbed",
     "Network fibre runs from every tray's NICs to the top-of-rack, power whips connect to the shelves, and coolant "
     "hoses are filled and pressure-tested for leaks. An NVL72's copper spine alone has about 5,000 cables, which is "
     "why this is done once, under factory conditions, rather than on site."),
    ("Burn-in: run it flat out until weak parts fail",
     "The rack is hooked to factory power and a coolant test loop and run at full load for days. Bad GPUs, optics, "
     "cables and pumps tend to fail early, so they are caught and swapped here instead of in a customer's cluster. "
     "Burn-in floor space, power and chilled water limit how many racks a site can turn out a week."),
    ("Shipped as one finished unit, ready to plug in",
     "The tested rack is crated and trucked to the data center at around 1.4 tonnes. On site it only needs "
     "power, water and network to come up, cutting deployment from weeks to days, which is why integration "
     "capacity can be a bottleneck in AI build-outs. Related: Super Micro (SMCI), Dell (DELL), Foxconn (2317.TW)."),
]

S_PARTS, S_FILL, S_CABLE, S_BURN, S_SHIP = -260.0, 0.0, 220.0, 460.0, 980.0
FILL_SLOTS = [0, 1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 31, 32, 33, 34, 35]


def loose_tray(m, parent, name, kind):
    """A tray at the origin (slot y = 0, rack front at z = RD) for sliding."""
    g = empty(name, parent)
    w, U, RD = K.RW - 3.5, K.U, K.RD
    bez = {"shelf": "bezel_p", "compute": "bezel_c", "switch": "bezel_s"}[kind]
    parts = [bx(f"{name}_ch", (-w, 0.3, -RD + 6), (w, 0.8, RD - 4), m["tray"], g),
             bx(f"{name}_bz", (-w, 0.3, RD - 4), (w, U - 0.3, RD - 2), m[bez], g)]
    if kind == "compute":
        parts.append(bx(f"{name}_pcb", (-w + 1.5, 0.8, -RD + 10), (w - 1.5, 1.1, RD - 8), m["pcb_g"], g))
        for k, (xc, zc) in enumerate(((-12, 14), (12, 14), (-12, -8), (12, -8))):
            parts.append(bx(f"{name}_cp{k}", (xc - 6, 1.1, zc - 6), (xc + 6, 3.0, zc + 6), m["coldp"], g))
    elif kind == "switch":
        parts.append(bx(f"{name}_sw", (-10, 0.8, -10), (10, 2.6, 10), m["coldp"], g))
    else:
        for k in range(6):
            xc = -22 + k * 8.8
            parts.append(bx(f"{name}_psu{k}", (xc - 3.8, 0.8, -RD + 10), (xc + 3.8, U - 0.6, RD - 4), m["alu"], g))
    D.join(parts, f"{name}_m")
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    m["wood"] = mat("ri_wood", (0.62, 0.46, 0.28), rough=0.85)
    m["epoxy"] = mat("ri_epoxy", (0.30, 0.34, 0.38), rough=0.6)
    bx("fl", (-420, -8, -220), (1250, 0, 260), m["epoxy"], root)
    for k, x in enumerate((S_FILL, S_CABLE, S_BURN)):  # yellow bay lines
        for xe in (x - 80, x + 80):
            bx(f"line{k}{xe}", (xe - 1.5, 0, -100), (xe + 1.5, 0.3, 160), m["yellow"], root)
    bx("rail", (-420, 330, -210), (1000, 338, -200), m["steel"], root)  # overhead hoist rail
    for x in (-300, 100, 500, 900):
        bx(f"col{x}", (x - 6, 0, -212), (x + 6, 338, -200), m["frame2"], root)

    # station 0: pallets of trays
    for p, (x, z) in enumerate(((S_PARTS - 50, 40), (S_PARTS + 60, 40), (S_PARTS, -90))):
        bx(f"pal{p}", (x - 50, 0, z - 40), (x + 50, 12, z + 40), m["wood"], root)
        for j in range(6 if p < 2 else 4):
            kind = "compute" if p == 0 else ("switch" if p == 1 else "shelf")
            g = loose_tray(m, root, f"pt{p}_{j}", kind)
            g.location = P(x, 12 + j * (K.U + 0.4), z - K.RD * 0.6 + 30)
            g.scale = (0.8, 0.8, 0.8)
    # station 1: empty frame (its busbar/manifolds fitted) + trays that slide in during beat 1
    K.rack_ai(m, root, "frame", (S_FILL, 0.0), 1, cut=True, liquid=True, slots=[])
    slide = empty("slide", root)
    for n, i in enumerate(FILL_SLOTS):
        kind = K.LAYOUT[i] if K.LAYOUT[i] != "net" else "switch"
        g = loose_tray(m, slide, f"st{i}", kind)
        y = K.slot_y(i)
        f0 = F(1, 0.05 + 0.75 * n / len(FILL_SLOTS))
        key(g, 0, "location", P(S_FILL, y, 140.0))
        key(g, f0, "location", P(S_FILL, y, 140.0))
        key(g, f0 + 14, "location", P(S_FILL, y, 0.0))
        show(g, [(F(1, 0), F(5, 0))])
    # station 2: a full rack, cabling appears
    _, cp_, cg = K.rack_ai(m, root, "cab", (S_CABLE, 0.0), 1, cut=True, liquid=True)
    cab = empty("cables", root)
    for k, (i, kd, y) in enumerate([t for t in cp_["trays"] if t[1] == "compute"]):
        xc = S_CABLE - 20 + (k % 6) * 6
        D.polyline(f"fib{k}", [(xc, y + 2, K.RD), (xc, y + 2, K.RD + 6), (S_CABLE + 26, y + 2, K.RD + 6), (S_CABLE + 26, K.slot_y(35), K.RD + 6)], 0.4, m["yellow"], cab)
    D.join([o for o in cab.children], "fib_m")
    present(cab, [(F(2, 0.25), F(5, 0))])
    run(root, "fib_beads", [(S_CABLE - 20, K.slot_y(8) + 2, K.RD + 6), (S_CABLE + 26, K.slot_y(8) + 2, K.RD + 6), (S_CABLE + 26, K.slot_y(35), K.RD + 6)], 6, 1.0, m["data"], [2], 0.4, 0.9, 30)
    run(root, "fill_c", [(S_CABLE - 20, K.RH + 40, -K.RD + 4), (S_CABLE - 20, K.RH, -K.RD + 4), (S_CABLE - 20, 10, -K.RD + 4)], 8, 1.5, m["cold_b"], [2], 0.2, 0.8, 50)
    D.polyline("fill_hose", [(S_CABLE - 20, K.RH, -K.RD + 4), (S_CABLE - 20, K.RH + 40, -K.RD + 4), (S_CABLE - 60, K.RH + 40, -K.RD - 40), (S_CABLE - 60, 0, -K.RD - 40)], 1.6, m["hose_b"], root)
    # station 3: burn-in rack + test cart
    _, bp, bg = K.rack_ai(m, root, "burn", (S_BURN, 0.0), 1, cut=True, liquid=True)
    cart = (S_BURN + 110, -170)
    bx("cart", (cart[0] - 25, 10, cart[1] - 40), (cart[0] + 25, 110, cart[1] + 40), m["cdu"], root)
    bx("cart_scr", (cart[0] - 18, 85, cart[1] + 40), (cart[0] + 18, 105, cart[1] + 41), m["screen"], root)
    for xc in (-18, 18):
        for zc in (-34, 34):
            bx(f"cart_w{xc}{zc}", (cart[0] + xc - 3, 0, cart[1] + zc - 3), (cart[0] + xc + 3, 10, cart[1] + zc + 3), m["rubber"], root)
    sup = [(cart[0] - 25, 60, cart[1]), (S_BURN + 50, 60, cart[1]), (S_BURN + 50, 60, -K.RD - 10), (S_BURN - 20, 60, -K.RD - 10), (S_BURN - 20, 30, -K.RD + 4)]
    ret = [(S_BURN + 20, 30, -K.RD + 4), (S_BURN + 20, 40, -K.RD - 20), (S_BURN + 60, 40, -K.RD - 20), (S_BURN + 60, 40, cart[1] - 20), (cart[0] - 25, 40, cart[1] - 20)]
    D.polyline("bt_s", sup, 1.8, m["hose_b"], root)
    D.polyline("bt_r", ret, 1.8, m["hose_r"], root)
    run(root, "bt_sb", sup, 8, 1.6, m["cold_b"], [3], 0.0, 0.7, 50)
    run(root, "bt_rb", ret, 8, 1.6, m["hot_r"], [3], 0.1, 0.8, 50)
    D.polyline("bt_pw", [(S_BURN, 330, 35), (S_BURN, K.RH + 30, 0), (S_BURN, K.RH, -40)], 1.4, m["rubber"], root)
    run(root, "bt_pwb", [(S_BURN, 330, 35), (S_BURN, K.RH + 30, 0), (S_BURN, K.RH, -40)], 6, 1.8, m["kw"], [3], 0.0, 0.8, 40)
    show(bg["gpus"], [(F(3, 0.15), F(4, 0))])
    blink(bg["leds"], 3, [0, 2, 4, 6], n=8, on=0.6)
    rise(root, "bt_heat", (S_BURN + K.RW + 8, 60, 0), 8, 1.6, m["heat"], 3, 0.1, 0.9, 50.0, 50, (4.0, 40.0))
    bad = empty("bad", root)
    yb = K.slot_y(12)
    bx("bad_f", (S_BURN - K.RW, yb, K.RD - 1.5), (S_BURN + K.RW, yb + K.U, K.RD + 0.5), m["led_r"], bad)
    blink(bad, 3, [5, 6, 7], n=8, on=0.5)
    # station 4: crate on a trailer
    tr = empty("truck", root)
    bx("trailer", (S_SHIP - 140, 30, -80), (S_SHIP + 160, 42, 120), m["frame2"], tr)
    for xw in (S_SHIP + 80, S_SHIP + 120):
        for zw in (-80, 120):
            D.tube(f"tw{xw}{zw}", (xw, 20, zw - 6), (xw, 20, zw + 6), 20.0, m["rubber"], tr, 16)
    bx("cab_t", (S_SHIP - 220, 0, -80), (S_SHIP - 145, 170, 120), m["cdu"], tr)
    bx("cab_win", (S_SHIP - 221, 110, -60), (S_SHIP - 219, 160, 100), m["screen"], tr)
    deck = empty("deck", tr, P(0, 42, 0))
    _, sp, _ = K.rack_ai(m, deck, "ship", (S_SHIP, 0.0), 1, cut=False, liquid=True)
    crate = []
    for xs in (-1, 1):
        for zs in (-1, 1):
            crate.append(bx(f"cr{xs}{zs}", (S_SHIP + xs * 40 - 4, 0, zs * 70 - 4), (S_SHIP + xs * 40 + 4, K.RH + 18, zs * 70 + 4), m["wood"], deck))
    crate.append(bx("cr_top", (S_SHIP - 44, K.RH + 10, -74), (S_SHIP + 44, K.RH + 18, 74), m["wood"], deck))
    crate.append(bx("cr_bot", (S_SHIP - 44, -10, -74), (S_SHIP + 44, 0, 74), m["wood"], deck))
    D.join(crate, "crate")
    # the rack sits on the trailer deck: lift whole truck group so the crate base sits at deck
    for f, dx in ((F(4, 0), 0.0), (F(4, 0.55), 0.0), (F(5, 0) - 1, 260.0)):
        key(tr, f, "location", P(dx, 0, 0), linear=True)

    C.tags(root, {
        0: [("compute trays", (S_PARTS - 50, 50, 40)), ("switch trays", (S_PARTS + 60, 50, 40)),
            ("power shelves", (S_PARTS, 40, -90)), ("empty frame: busbar + manifolds", (S_FILL, K.RH + 4, 0))],
        1: [("power shelves top + bottom", (S_FILL + K.RW, K.slot_y(1), 10)), ("18 compute trays", (S_FILL + K.RW, K.slot_y(8), 10)),
            ("blind-mate at the rear", (S_FILL, 100, -K.RD))],
        2: [("fibre to top-of-rack", (S_CABLE + 26, K.slot_y(30), K.RD + 6)), ("~5,000 NVLink copper cables", cp_["rear"]),
            ("coolant filled + leak-tested", (S_CABLE - 60, K.RH + 40, -K.RD - 40))],
        3: [("full load for days", bp["top"]), ("test cart: power + coolant", (cart[0], 110, cart[1])),
            ("failing tray pulled", (S_BURN + K.RW, yb, K.RD))],
        4: [("crated: ~1.4 t", (S_SHIP, K.RH + 62, 0)), ("plug in power, water, network", (S_SHIP - 180, 170, 20)),
            ("SMCI, DELL, Foxconn", (S_SHIP + 100, 60, 120))],
    })
    C.done(SLUG, BEATS, [
        frame((-130.0, 90.0, 0.0), 420.0, 0.40, 0.30),
        frame((S_FILL, 100.0, 40.0), 230.0, 0.70, 0.15),
        frame((S_CABLE, 110.0, 0.0), 240.0, -0.75, 0.15),
        frame((S_BURN + 40, 100.0, 0.0), 260.0, 0.85, 0.20),
        frame((S_SHIP + 80, 110.0, 20.0), 520.0, 0.45, 0.20),
    ], root)


if __name__ == "__main__":
    build()
