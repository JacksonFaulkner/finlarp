"""TRM_COLOCATION: the Terms-tab overview for colocation, at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_colocation.py

Colocation does not live on a GPU board, so the scene is its own: a data hall cut open at the
front. Two retail cages of customer racks sit inside the provider's building; the provider brings
utility power through switchgear and UPS to overhead busway, cold air from CRAH units along the
wall, and fiber from the meet-me room to every cage. On the right, behind a partition, a whole
wholesale hall is leased to one tenant and filled with dense liquid-cooled AI racks.

Beats:
  0 building  the hall cut open: cages, MMR, power yard, CRAHs, the wholesale hall
  1 cage      inside one cage: the customer's own servers, locked mesh, its cabinets
  2 utilities power beads down the busway into each rack, cold air in, hot air out
  3 interconnect cross-connects from every cage through the meet-me room to carriers and clouds
  4 wholesale the leased hall: denser racks, more kW, priced per kW
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_COLOCATION"
BEATS = [
    ("Colocation: rent the building, bring your own servers",
     "A colocation (colo) provider owns the data center building and everything that keeps it running: the grid "
     "connection, backup power, cooling, security and fiber. Customers rent space inside it and install servers they "
     "own and operate themselves. The provider never touches the customer's computers; it sells a safe, powered, "
     "cooled, connected place to put them."),
    ("Retail colo: a locked cage of the customer's own cabinets",
     "Retail customers rent a few cabinets or a fenced cage on a shared floor. Inside, the racks, servers, switches "
     "and storage belong to the tenant, and only its staff hold the badge to the cage door. Contracts typically run "
     "three to five years and renew, which makes the revenue recurring and sticky: moving racks out is costly and "
     "risky."),
    ("The provider supplies power and cooling, billed mostly per kW",
     "Utility power comes in through switchgear and UPS batteries with generators behind them, then runs along "
     "overhead busway and drops into each rack. CRAH units push cold air into the rack fronts and pull the hot "
     "exhaust back. Because power and cooling are the scarce, expensive parts, pricing is quoted largely per "
     "kilowatt of committed power rather than per square foot."),
    ("Interconnection: cross-connects through the meet-me room",
     "Every cage runs fiber to the meet-me room, where a cross-connect patches it to any other tenant: carriers, "
     "cloud on-ramps, exchanges, partners. Each cross-connect is a small monthly fee with almost no cost to "
     "provide. The more networks in one building, the more valuable it is to the next tenant, which is the moat of "
     "interconnection-heavy retail sites."),
    ("Wholesale colo: whole halls leased to one tenant, now for AI",
     "Wholesale colo leases an entire hall or building, often to a hyperscaler, on 10-15 year terms at lower "
     "margins per kW. AI shows up here as bigger, denser leases: racks that drew 8-15 kW now draw 40-130 kW and need "
     "liquid cooling. Related: Equinix (EQIX) leans retail and interconnection, Digital Realty (DLR) wholesale plus "
     "retail, Iron Mountain (IRM) and Applied Digital (APLD) build for AI tenants."),
]

# hall: floor x -170..170, z -130..0 (front cut), y 0; ceiling 70
HX0, HX1, HZ0, HY = -170.0, 170.0, -130.0, 70.0
CAGES = [(-145.0, -65.0), (-50.0, 30.0)]  # x spans of the two retail cages
CZ = (-95.0, -20.0)  # cage z span
PART = 45.0  # partition wall x for the wholesale hall
MMR = (-150.0, 30.0, -128.0, -112.0)  # meet-me room x0, x1, z0, z1
BUS_Y = 58.0


def mats(m):
    m["floor"] = mat("co_floor", (0.55, 0.57, 0.60), rough=0.7)
    m["tile"] = mat("co_tile", (0.42, 0.44, 0.48), rough=0.6)
    m["wall"] = mat("co_wall", (0.78, 0.78, 0.76), rough=0.85)
    m["rackm"] = mat("co_rack", (0.08, 0.08, 0.09), metal=0.6, rough=0.45)
    m["srv"] = mat("co_srv", (0.22, 0.23, 0.26), metal=0.7, rough=0.4)
    m["mesh"] = mat("co_mesh", (0.70, 0.72, 0.74), metal=0.9, rough=0.35)
    m["yellow"] = mat("co_tray", (0.90, 0.72, 0.12), rough=0.5)
    m["busw"] = mat("co_bus", (0.75, 0.62, 0.30), metal=0.8, rough=0.35)
    m["ups"] = mat("co_ups", (0.30, 0.34, 0.40), metal=0.4, rough=0.5)
    m["led_g"] = mat("co_led_g", (0.3, 1.0, 0.5), emit=(0.3, 1.0, 0.5), strength=4.0)
    m["led_b"] = mat("co_led_b", (0.3, 0.6, 1.0), emit=(0.3, 0.6, 1.0), strength=4.0)
    m["tag_a"] = mat("co_tag_a", (0.95, 0.55, 0.2), emit=(0.95, 0.5, 0.15), strength=2.0)
    m["tag_b"] = mat("co_tag_b", (0.4, 0.7, 1.0), emit=(0.35, 0.65, 1.0), strength=2.0)
    m["tag_w"] = mat("co_tag_w", (0.75, 0.4, 1.0), emit=(0.7, 0.35, 1.0), strength=2.0)


def rack(m, parent, name, x, z, w=9.0, d=14.0, h=44.0, units=10, leds=None, liquid=False):
    """A cabinet centred (x, z), front facing +z: frame, server slabs with bezel lines, LEDs
    (added to the `leds` group), optional manifold pipes on the back."""
    g = empty(name, parent)
    x0, x1, z0, z1 = x - w / 2, x + w / 2, z - d / 2, z + d / 2
    for (a, b) in ((x0, x0 + 0.8), (x1 - 0.8, x1)):
        for (c, e) in ((z0, z0 + 0.8), (z1 - 0.8, z1)):
            bx(f"{name}_post{a:.0f}{c:.0f}", (a, 0.0, c), (b, h, e), m["rackm"], g)
    bx(f"{name}_top", (x0, h - 1.0, z0), (x1, h, z1), m["rackm"], g)
    bx(f"{name}_base", (x0, 0.0, z0), (x1, 1.5, z1), m["rackm"], g)
    bx(f"{name}_side", (x0, 1.5, z0 + 0.8), (x0 + 0.3, h - 1.0, z1 - 0.8), m["rackm"], g)
    uh = (h - 4.0) / units
    for u in range(units):
        y0 = 2.0 + u * uh
        bx(f"{name}_s{u}", (x0 + 0.9, y0 + 0.15, z0 + 1.2), (x1 - 0.9, y0 + uh - 0.25, z1 - 0.9), m["srv"], g)
        bx(f"{name}_bz{u}", (x0 + 1.4, y0 + uh * 0.45, z1 - 0.9), (x1 - 2.6, y0 + uh * 0.55, z1 - 0.7), m["dark"], g)
        if leds is not None:
            bx(f"{name}_l{u}", (x1 - 2.2, y0 + uh * 0.4, z1 - 0.9), (x1 - 1.4, y0 + uh * 0.6, z1 - 0.6), m["led_g" if u % 3 else "led_b"], leds)
    if liquid:
        for k, mt in enumerate(("cool", "hot")):
            xp = x - 1.5 + 3.0 * k
            D.tube(f"{name}_mf{k}", (xp, 2.0, z0 - 0.6), (xp, h - 2.0, z0 - 0.6), 0.6, m[mt], g, 8)
    return g


def cage(m, parent, name, x0, x1, z0, z1, h=50.0):
    """A wire-mesh cage: posts, horizontal rails, vertical wires; the front run left out so the
    camera sees in; a door on the right side."""
    g = empty(name, parent)
    sides = [((x0, z0), (x1, z0)), ((x0, z0), (x0, z1)), ((x1, z0), (x1, z1 - 14.0))]
    for k, ((ax, az), (bx_, bz)) in enumerate(sides):
        L = math.hypot(bx_ - ax, bz - az)
        n = max(2, int(L / 2.5))
        for i in range(n + 1):
            u = i / n
            px, pz = ax + (bx_ - ax) * u, az + (bz - az) * u
            r = 0.45 if i in (0, n) or i % 8 == 0 else 0.1
            D.tube(f"{name}_w{k}_{i}", (px, 0.0, pz), (px, h, pz), r, m["mesh"], g, 6)
        for yy in (0.4, 12.0, 25.0, 38.0, h):
            D.tube(f"{name}_r{k}_{yy:.0f}", (ax, yy, az), (bx_, yy, bz), 0.3, m["mesh"], g, 6)
    # door frame on the right side, front end
    for zz in (z1 - 14.0, z1):
        D.tube(f"{name}_dp{zz:.0f}", (x1, 0.0, zz), (x1, h - 6.0, zz), 0.5, m["mesh"], g, 8)
    D.tube(f"{name}_dt", (x1, h - 6.0, z1 - 14.0), (x1, h - 6.0, z1), 0.5, m["mesh"], g, 8)
    bx(f"{name}_lock", (x1 - 0.4, 22.0, z1 - 12.5), (x1 + 0.6, 26.0, z1 - 11.0), m["gold"], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    # ---- the building shell
    bx("floor", (HX0 - 70.0, -3.0, HZ0 - 6.0), (HX1 + 6.0, 0.0, 0.0), m["floor"], root)
    for i in range(int((HX1 - HX0) / 20)):
        x = HX0 + 20.0 * i
        bx(f"tile{i}", (x + 0.3, 0.0, HZ0), (x + 0.6, 0.08, 0.0), m["tile"], root)
    bx("wall_back", (HX0, 0.0, HZ0 - 4.0), (HX1, HY, HZ0), m["wall"], root)
    bx("wall_left", (HX0 - 4.0, 0.0, HZ0 - 4.0), (HX0, HY, 0.0), m["wall"], root)
    bx("wall_right", (HX1, 0.0, HZ0 - 4.0), (HX1 + 4.0, HY, 0.0), m["wall"], root)
    bx("partition", (PART, 0.0, HZ0), (PART + 2.5, HY, -8.0), m["wall"], root)
    bx("ceil_beam", (HX0, HY, HZ0 - 4.0), (HX1 + 4.0, HY + 3.0, HZ0 + 10.0), m["wall"], root)

    leds = empty("leds", root)
    # ---- retail cages
    racks = []
    cgroups = []
    for ci, (x0, x1) in enumerate(CAGES):
        cg = cage(m, root, f"cage{ci}", x0, x1, CZ[0], CZ[1])
        cgroups.append(cg)
        for row, zc in enumerate((-78.0, -42.0)):
            for j in range(6):
                x = x0 + 9.0 + j * 12.0
                rack(m, root, f"r{ci}_{row}_{j}", x, zc, leds=leds)
                racks.append((x, zc, ci))
        # a tenant name plate (colour per tenant)
        bx(f"plate{ci}", (x0 + 4.0, 44.0, CZ[0] - 0.5), (x0 + 30.0, 49.0, CZ[0] + 0.2), m["tag_a" if ci == 0 else "tag_b"], root)

    # ---- meet-me room at the back: a glass-fronted room with patch frames
    mx0, mx1, mz0, mz1 = MMR
    bx("mmr_wall", (mx0, 0.0, mz1 - 1.0), (mx1, 3.0, mz1), m["wall"], root)
    for k in range(10):
        x = mx0 + 8.0 + k * 17.5
        bx(f"mmr_frame{k}", (x - 3.0, 0.0, mz0 + 2.0), (x + 3.0, 40.0, mz0 + 8.0), m["rackm"], root)
        for p in range(8):
            bx(f"mmr_p{k}_{p}", (x - 2.5, 4.0 + p * 4.4, mz0 + 8.0), (x + 2.5, 6.4 + p * 4.4, mz0 + 8.4), m["yellow"], root)
    carriers = empty("carriers", root)
    for k in range(10):
        x = mx0 + 8.0 + k * 17.5
        bx(f"mmr_lit{k}", (x - 2.4, 36.0, mz0 + 8.4), (x + 2.4, 37.0, mz0 + 8.8), m["sig"], carriers)
    show(carriers, [(F(3, 0.2), F(4, 0))])
    # fiber tray overhead from the MMR along each cage
    tray_y = 63.0
    bx("tray_main", (mx0, tray_y, -120.0), (mx1, tray_y + 1.2, -114.0), m["yellow"], root)
    for ci, (x0, x1) in enumerate(CAGES):
        xc = (x0 + x1) / 2
        bx(f"tray{ci}", (xc - 3.0, tray_y, -114.0), (xc + 3.0, tray_y + 1.2, -30.0), m["yellow"], root)
        bx(f"tray_drop{ci}", (xc - 1.0, 50.0, -60.5), (xc + 1.0, tray_y, -59.5), m["yellow"], root)

    # ---- power: utility yard outside the left wall, switchgear, UPS, busway over every row
    yx = HX0 - 60.0
    for k in range(3):  # utility poles and lines
        D.tube(f"pole{k}", (yx - 5.0, 0.0, -110.0 + 40.0 * k), (yx - 5.0, 80.0, -110.0 + 40.0 * k), 1.2, m["plastic"], root, 8)
    bx("xfmr", (yx, 0.0, -115.0), (yx + 22.0, 26.0, -90.0), m["ups"], root)
    for k in range(5):
        bx(f"xfmr_fin{k}", (yx + 2.0 + 4.0 * k, 2.0, -90.0), (yx + 3.0 + 4.0 * k, 22.0, -87.0), m["ups"], root)
    bx("gen", (yx, 0.0, -75.0), (yx + 30.0, 22.0, -45.0), m["driver"], root)
    bx("gen_ex", (yx + 22.0, 22.0, -66.0), (yx + 26.0, 34.0, -62.0), m["dark"], root)
    for k in range(4):  # switchgear lineup + UPS cabinets inside, left wall
        bx(f"swg{k}", (HX0 + 2.0, 0.0, -20.0 - 9.0 * k - 8.0), (HX0 + 14.0, 46.0, -20.0 - 9.0 * k), m["ups"], root)
        bx(f"swg_w{k}", (HX0 + 14.0, 30.0, -26.0 - 9.0 * k), (HX0 + 14.3, 40.0, -22.0 - 9.0 * k), m["screen"], root)
    batt = empty("batt", root)
    for k in range(4):
        bx(f"ups_led{k}", (HX0 + 14.0, 10.0, -26.0 - 9.0 * k), (HX0 + 14.4, 14.0, -22.0 - 9.0 * k), m["led_g"], batt)
    # busway: runs along x over each rack row, plus a feeder along the left wall
    bx("feeder", (HX0 + 4.0, BUS_Y, -60.0), (HX0 + 10.0, BUS_Y + 3.0, -20.0), m["busw"], root)
    for zc in (-78.0, -42.0):
        bx(f"bus{zc:.0f}", (HX0 + 4.0, BUS_Y, zc - 2.0), (PART - 2.0, BUS_Y + 3.0, zc + 2.0), m["busw"], root)
        for (x, z, ci) in racks:
            if z == zc:
                bx(f"tap{x:.0f}{zc:.0f}", (x - 1.5, BUS_Y - 3.5, zc - 1.5), (x + 1.5, BUS_Y, zc + 1.5), m["ups"], root)
                D.tube(f"whip{x:.0f}{zc:.0f}", (x, BUS_Y - 3.5, zc), (x, 44.0, zc), 0.4, m["plastic"], root, 6)
    # power beads: yard -> switchgear -> busway -> rack drops
    run(root, "pw_in", [(yx - 5.0, 78.0, -70.0), (yx + 11.0, 26.0, -100.0), (HX0 - 4.0, 30.0, -40.0), (HX0 + 8.0, BUS_Y + 1.5, -40.0)],
        8, 1.6, m["v12"], [0, 2], 0.0, 0.7, 50)
    for zc in (-78.0, -42.0):
        for (x, z, ci) in racks[::2]:
            if z == zc:
                run(root, f"pw{x:.0f}{zc:.0f}", [(HX0 + 8.0, BUS_Y + 1.5, zc), (x, BUS_Y + 1.5, zc), (x, 44.0, zc)],
                    2, 1.1, m["v12"], 2, 0.1 + 0.0015 * (x - HX0), 0.6 + 0.0015 * (x - HX0), 40)

    # ---- cooling: CRAH units along the back of each cage zone (between cage and MMR)
    for k in range(5):
        x = -150.0 + 36.0 * k
        bx(f"crah{k}", (x, 0.0, -110.0), (x + 22.0, 34.0, -100.0), m["white"], root)
        C.D.tube(f"crah_fan{k}", (x + 11.0, 34.0, -105.0), (x + 11.0, 35.5, -105.0), 4.0, m["grid"], root, 16)
        bx(f"crah_grille{k}", (x + 2.0, 2.0, -100.0), (x + 20.0, 14.0, -99.6), m["grid"], root)
    for ci, (x0, x1) in enumerate(CAGES):
        for j in range(0, 6, 2):
            x = x0 + 9.0 + j * 12.0
            # cold air low along the floor into the cold aisle, up into rack fronts
            run(root, f"cold{ci}{j}", [(x, 4.0, -99.0), (x, 3.0, -60.0), (x, 14.0, -34.0), (x, 20.0, -42.0)],
                4, 1.0, m["cool"], 2, 0.05, 0.6, 46)
            rise(root, f"hot{ci}{j}", (x, 44.0, -86.0), 4, 0.9, m["heat"], 2, 0.1, 0.8, 14.0, 40, (3.0, 2.0))

    # ---- cross-connects: each rack row up the tray to the MMR, and MMR out to carriers
    for ci, (x0, x1) in enumerate(CAGES):
        xc = (x0 + x1) / 2
        for k, zc in enumerate((-78.0, -42.0)):
            run(root, f"xc{ci}{k}", [(xc, 45.0, zc), (xc, tray_y + 2.0, zc), (xc, tray_y + 2.0, -117.0),
                                       (mx0 + 8.0 + 17.5 * (3 + ci * 3 + k), tray_y + 2.0, -117.0), (mx0 + 8.0 + 17.5 * (3 + ci * 3 + k), 36.0, -118.0)],
                5, 1.0, m["sig"], 3, 0.0, 0.7, 50)
    # cage 0 talks to cage 1 through the MMR patch
    x0c, x1c = (CAGES[0][0] + CAGES[0][1]) / 2, (CAGES[1][0] + CAGES[1][1]) / 2
    run(root, "xc_ab", [(x0c, tray_y + 3.5, -60.0), (x0c, tray_y + 3.5, -117.0), (x1c, tray_y + 3.5, -117.0), (x1c, tray_y + 3.5, -60.0)],
        6, 1.2, m["bit"], 3, 0.15, 0.85, 50)
    # carrier fibers leaving through the back wall
    for k in range(3):
        x = -120.0 + 50.0 * k
        D.tube(f"conduit{k}", (x, 2.0, HZ0 - 4.0), (x, 2.0, HZ0 - 40.0), 1.5, m["dark"], root, 10)
        run(root, f"carrier{k}", [(x, 36.0, -124.0), (x, 3.0, -126.0), (x, 3.0, HZ0 - 40.0)], 4, 1.0, m["sig"], 3, 0.1, 0.8, 40)

    # ---- the wholesale hall: dense liquid-cooled racks, CDUs, one tenant
    wleds = empty("wleds", root)
    for row, zc in enumerate((-100.0, -70.0, -40.0)):
        for j in range(8):
            x = PART + 12.0 + j * 13.5
            rack(m, root, f"w{row}_{j}", x, zc, w=10.0, d=16.0, h=50.0, units=14, leds=wleds, liquid=True)
    for k in range(3):
        bx(f"cdu{k}", (HX1 - 14.0, 0.0, -112.0 + 32.0 * k), (HX1 - 2.0, 40.0, -96.0 + 32.0 * k), m["ups"], root)
    for zc in (-100.0, -70.0, -40.0):
        bx(f"wbus{zc:.0f}", (PART + 4.0, BUS_Y + 4.0, zc - 2.5), (HX1 - 16.0, BUS_Y + 8.0, zc + 2.5), m["busw"], root)
        for mt, dz in (("cool", -9.6), ("hot", -11.2)):
            D.tube(f"wpipe{zc:.0f}{mt}", (PART + 6.0, 2.5, zc + dz), (HX1 - 14.0, 2.5, zc + dz), 0.8, m[mt], root, 8)
        run(root, f"wpw{zc:.0f}", [(PART + 6.0, BUS_Y + 6.0, zc), (HX1 - 18.0, BUS_Y + 6.0, zc)], 8, 1.6, m["amp"], 4, 0.0, 0.7, 50)
        run(root, f"wcool{zc:.0f}", [(HX1 - 14.0, 2.5, zc - 9.6), (PART + 6.0, 2.5, zc - 9.6)], 6, 1.0, m["cool"], 4, 0.05, 0.75, 50)
        rise(root, f"wheat{zc:.0f}", (PART + 60.0, 52.0, zc), 6, 1.2, m["heat"], 4, 0.1, 0.8, 16.0, 40, (45.0, 3.0))
    bx("wplate", (PART + 20.0, 55.0, HZ0 + 0.1), (PART + 90.0, 62.0, HZ0 + 0.6), m["tag_w"], root)
    show(wleds, [(F(0, 0), F(1, 0)), (F(4, 0), F(5, 0))])

    # LEDs blink on the retail racks during beat 1; steady otherwise
    blink(leds, 1, [0, 1, 3, 4, 6, 7], n=8, on=0.8)
    show(batt, [(F(2, 0), F(3, 0))])

    ca = CAGES[0]
    tags = {
        0: [("provider's building and plant", (HX0 + 10.0, HY, -60.0)), ("retail cages", (CAGES[1][0] + 20.0, 50.0, CZ[0])),
            ("meet-me room", (mx0 + 90.0, 40.0, mz0 + 6.0)), ("wholesale hall, one tenant", (PART + 60.0, 52.0, -70.0))],
        1: [("tenant's own servers", (ca[0] + 30.0, 40.0, -42.0)), ("locked mesh cage", (ca[1], 25.0, CZ[1] - 12.0)),
            ("rent: cabinets or a cage", (ca[0] + 40.0, 50.0, CZ[0]))],
        2: [("utility + generator + UPS", (HX0 - 30.0, 26.0, -90.0)), ("busway drops to racks", (-60.0, BUS_Y + 3.0, -42.0)),
            ("CRAH cold air in", (-100.0, 34.0, -105.0)), ("billed per kW", (-10.0, 45.0, -78.0))],
        3: [("cross-connect fiber", (-105.0, tray_y + 2.0, -90.0)), ("MMR patches tenant to tenant", (mx0 + 60.0, 36.0, mz0 + 8.0)),
            ("carriers and cloud on-ramps", (-70.0, 3.0, HZ0 - 30.0))],
        4: [("40-130 kW AI racks", (PART + 40.0, 50.0, -40.0)), ("liquid cooling, CDUs", (HX1 - 8.0, 40.0, -80.0)),
            ("10-15 yr hall lease", (PART + 55.0, 62.0, HZ0)), ("EQIX, DLR, IRM, APLD", (PART + 100.0, 58.0, -100.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-20.0, 20.0, -70.0), 340.0, 0.25, 0.55, pad=1.0),
        frame((ca[0] + 40.0, 22.0, -55.0), 95.0, 0.30, 0.30),
        frame((-110.0, 30.0, -60.0), 190.0, 0.55, 0.45),
        frame((-60.0, 35.0, -90.0), 210.0, 0.05, 0.60),
        frame((PART + 60.0, 25.0, -65.0), 140.0, -0.35, 0.45),
    ], root)


if __name__ == "__main__":
    build()
