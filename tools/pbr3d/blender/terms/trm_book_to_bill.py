"""TRM_BOOK_TO_BILL: the Terms-tab overview for the book-to-bill ratio.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_book_to_bill.py

An equipment maker's plant in the middle: orders (blue beads) arrive from customer fabs on the
left, finished tools ship out in crates on a belt to the right (amber beads). Between them sits
the backlog: a stack of order cards that grows or drains. Above, a dial reads bookings/billings,
and behind, a chart shows the ratio leading revenue.

Beats:
  0 flows     orders in, shipments out
  1 above 1   more orders than shipments: backlog grows, dial 1.2
  2 below 1   orders slow: backlog drains, dial 0.8
  3 leading   the ratio turns before revenue does
  4 who       equipment and chip makers that report it
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, P, bx, empty, show, mat, key  # noqa: E402
from power_vrm_detail import frame, run, rise  # noqa: E402
from sand_overview import disc, pivot, rel, _interp  # noqa: E402

SLUG = "TRM_BOOK_TO_BILL"
BEATS = [
    ("Book-to-bill compares new orders to what was shipped and billed",
     "Bookings are new orders signed in a period; billings are products shipped and invoiced in the same period. "
     "Book-to-bill is bookings divided by billings. A chip-tool maker that booked $12B and billed $10B in a "
     "quarter has a ratio of 1.2."),
    ("Above 1.0, orders outrun shipments and the backlog grows",
     "When customers order faster than the factory can build and ship, unfilled orders pile up as backlog. A ratio "
     "above 1 means future revenue is already being locked in, and lead times usually stretch."),
    ("Below 1.0, shipments outrun orders and the backlog drains",
     "When orders slow, the plant keeps shipping out of its backlog, so revenue can look fine for a while even as "
     "new business dries up. A ratio stuck below 1 warns that revenue will fall once the backlog runs down."),
    ("It turns before revenue, which is why investors watch it",
     "Because orders come months before shipments, the ratio tends to turn ahead of reported sales. Equipment and "
     "chip makers have long published it as a read on demand; a single quarter can be lumpy when one big customer "
     "places a large order."),
    ("Chip-equipment makers are where the number matters most",
     "Fabs order lithography, etch and test tools a year or more ahead, so tool makers' orders and backlog lead the "
     "whole cycle. Some now report backlog instead of a strict ratio, but the idea is the same. Related: Applied "
     "Materials (AMAT), ASML (ASML), Lam Research (LRCX), Teradyne (TER)."),
]

PL = (0.0, -80.0)  # plant x, z
BK = (0.0, 20.0)  # backlog stack x, z


def mats(m):
    m["floor"] = mat("b_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["wall"] = mat("b_wall", (0.55, 0.58, 0.62), rough=0.5)
    m["order"] = mat("b_order", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=3.0)
    m["ship"] = mat("b_ship", (1.0, 0.62, 0.18), emit=(1.0, 0.62, 0.18), strength=3.0)
    m["card"] = mat("b_card", (0.30, 0.55, 0.85), emit=(0.30, 0.55, 0.85), strength=0.8)
    m["crate"] = mat("b_crate", (0.62, 0.48, 0.30), rough=0.8)
    m["red"] = mat("b_red", (1.0, 0.25, 0.15), emit=(1.0, 0.20, 0.10), strength=3.0)


def fab(m, root, name, x, z):
    """A customer fab: low clean-room block with stacks and a roof of air handlers."""
    g = empty(name, root)
    bx(f"{name}_b", (x - 30, 0, z - 22), (x + 30, 26, z + 22), m["wall"], g)
    for k in range(4):
        bx(f"{name}_ah{k}", (x - 26 + 14 * k, 26, z - 10), (x - 16 + 14 * k, 32, z + 4), m["steel"], g)
    for k in (-1, 1):
        D.tube(f"{name}_st{k}", (x + 20 * k, 26, z - 16), (x + 20 * k, 50, z - 16), 2.2, m["steel"], g, 12)
    bx(f"{name}_dock", (x + 30, 0, z - 8), (x + 34, 12, z + 8), m["car"], g)
    return (x + 30, 10, z)


def plant(m, root):
    x, z = PL
    g = empty("plant", root)
    # cut-open hall: back wall, side walls, floor; tools inside on an assembly line
    bx("pl_floor", (x - 70, 0, z - 40), (x + 70, 1, z + 40), m["steel"], g)
    bx("pl_back", (x - 70, 0, z - 42), (x + 70, 50, z - 40), m["wall"], g)
    for s in (-1, 1):
        bx(f"pl_side{s}", (x + 70 * s, 0, z - 40), (x + 72 * s, 50, z + 10), m["wall"], g)
    bx("pl_roof", (x - 72, 50, z - 42), (x + 72, 53, z - 10), m["wall"], g)
    tools = []
    for k in range(4):  # semiconductor tools being built: body, chamber ring, EFEM
        tx = x - 48 + 32 * k
        bx(f"tool{k}", (tx - 10, 1, z - 26), (tx + 10, 22, z - 6), m["white"], g)
        bx(f"tool{k}_efem", (tx - 8, 1, z - 6), (tx + 8, 12, z + 2), m["steel"], g)
        disc(f"tool{k}_ch", (tx, 24, z - 16), 6, 4, m["steel"], g)
        tools.append(bx(f"tool{k}_lt", (tx - 7, 18, z - 5.9), (tx + 7, 19, z - 5.7), m["sig"], g))
    return (x, 50, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-300, -4, -260), (300, 0, 100), m["floor"], root)
    docks = [fab(m, root, f"fab{k}", -230.0, -120.0 + 70 * k) for k in range(3)]
    pt = plant(m, root)
    # shipping belt + crates out to the right
    bx("belt", (PL[0] + 70, 8, -6), (260, 10, 6), m["rubber"], root)
    for k in range(10):
        D.tube(f"roll{k}", (PL[0] + 76 + 18 * k, 8, -7), (PL[0] + 76 + 18 * k, 8, 7), 1.8, m["steel"], root, 10)
    crates = empty("crates", root)
    for k in range(4):
        cx = 110 + 40 * k
        bx(f"crate{k}", (cx - 10, 10, -8), (cx + 10, 28, 8), m["crate"], crates)
        for j in range(3):
            bx(f"crate{k}_sl{j}", (cx - 10.3, 13 + 5 * j, -8.3), (cx + 10.3, 14 + 5 * j, 8.3), m["car"], crates)
    # order paths from each fab dock to the plant's order desk (backlog)
    shipping = [(PL[0], 12, PL[1] + 10), (PL[0] + 70, 12, 0), (270, 12, 0)]
    for k, d in enumerate(docks):
        path = [d, (d[0] + 60, 30, d[2]), (BK[0] - 20, 30, BK[1]), (BK[0], 20, BK[1])]
        run(root, f"ord{k}", path, 6, 1.6, m["order"], [0, 1, 3, 4], 0.0, 0.8, 60)
        run(root, f"ord_slow{k}", path, 2, 1.6, m["order"], 2, 0.0, 0.8, 60)
    run(root, "ship", shipping, 8, 1.8, m["ship"], [0, 1, 2, 3, 4], 0.0, 0.85, 70)

    # backlog: a stack of order cards, height keyed per beat
    pv = pivot("backlog", (BK[0], 0.0, BK[1]), root)
    for k in range(1):
        bx("bl_box", rel((BK[0], 0, BK[1]), (BK[0] - 16, 0, BK[1] - 12)), rel((BK[0], 0, BK[1]), (BK[0] + 16, 1, BK[1] + 12)), m["card"], pv)
    bx("bl_tray", (BK[0] - 20, 0, BK[1] - 16), (BK[0] + 20, 2, BK[1] + 16), m["steel"], root)
    for f, h in ((0, 20.0), (F(1, 0.1), 20.0), (F(1, 0.9), 55.0), (F(2, 0.1), 55.0), (F(2, 0.9), 22.0),
                 (F(3, 0.1), 22.0), (F(3, 0.9), 40.0)):
        key(pv, f, "scale", (1, 1, h), linear=True)

    # dial on a mast: 0.5..1.5 arc, red mark at 1.0, needle rotates
    dx, dy, dz = 0.0, 110.0, 30.0
    D.tube("mast", (dx, 0, dz - 6), (dx, dy - 34, dz - 6), 2.0, m["steel"], root, 12)
    disc_g = empty("dial", root)
    bx("dial_face", (dx - 36, dy - 34, dz - 6), (dx + 36, dy + 6, dz - 4), m["car"], disc_g)
    ticks = []
    for i in range(11):
        a = math.pi * (0.9 - 0.8 * i / 10)  # 0.5 at left .. 1.5 at right
        r0, r1 = 24, 30 if i % 5 == 0 else 27
        mt = m["red"] if i == 5 else m["ink"]
        D.polyline(f"tick{i}", [(dx + r0 * math.cos(a), dy - 30 + r0 * math.sin(a), dz - 3.6), (dx + r1 * math.cos(a), dy - 30 + r1 * math.sin(a), dz - 3.6)], 0.5, mt, disc_g)
    nd = empty("needle", root, P(dx, dy - 30, dz - 3))
    D.polyline("needle_m", [(0, 0, 0), (0, 26, 0)], 0.8, m["v12"], nd)
    _interp("LINEAR")

    def needle(f, ratio):
        a = -(ratio - 1.0) / 0.5 * (0.4 * math.pi)  # positive ratio-1 swings right (clockwise)
        nd.rotation_euler = (0.0, -a, 0.0)
        nd.keyframe_insert("rotation_euler", frame=f)

    for f, r in ((0, 1.0), (F(1, 0.1), 1.0), (F(1, 0.6), 1.2), (F(2, 0.1), 1.2), (F(2, 0.6), 0.8),
                 (F(3, 0.1), 0.8), (F(3, 0.6), 1.1)):
        needle(f, r)

    # chart behind the plant: ratio line leads revenue line
    cg = empty("chart", root)
    cx0, cx1, cy, cz = -120.0, 120.0, 165.0, -160.0
    bx("chart_bd", (cx0 - 8, cy - 40, cz - 3), (cx1 + 8, cy + 40, cz - 1), m["mold"], cg)
    D.tube("chart_post_l", (cx0, 0, cz - 2), (cx0, cy - 40, cz - 2), 2.0, m["steel"], cg, 10)
    D.tube("chart_post_r", (cx1, 0, cz - 2), (cx1, cy - 40, cz - 2), 2.0, m["steel"], cg, 10)
    D.polyline("c_ratio", C.wave_pts(cx0, cx1, cy + 8, cz, 22.0, 1.5), 0.9, m["order"], cg)
    D.polyline("c_rev", C.wave_pts(cx0, cx1, cy - 12, cz + 0.3, 18.0, 1.5, phase=-1.4), 0.9, m["ship"], cg)
    D.polyline("c_one", [(cx0, cy + 8, cz - 0.5), (cx1, cy + 8, cz - 0.5)], 0.3, m["ink"], cg)
    show(cg, [(F(3, 0.0), F(5, 0))])

    T = {
        0: [("customer fabs place orders", docks[1]), ("tool maker builds", pt), ("shipped + billed", (200.0, 28.0, 0.0)),
            ("backlog of open orders", (BK[0], 20.0, BK[1]))],
        1: [("orders > shipments", docks[0]), ("backlog grows", (BK[0], 55.0, BK[1])), ("ratio 1.2", (dx, dy, dz))],
        2: [("orders slow", docks[2]), ("backlog drains", (BK[0], 22.0, BK[1])), ("ratio 0.8", (dx, dy, dz)),
            ("revenue holds, for now", (200.0, 28.0, 0.0))],
        3: [("ratio turns first", (cx0 + 40, cy + 30, cz)), ("revenue follows months later", (cx1 - 40, cy - 30, cz)),
            ("1.0 line", (cx1, cy + 8, cz))],
        4: [("AMAT ASML LRCX TER", pt), ("orders lead the chip cycle", (dx, dy, dz))],
    }
    C.tags(root, T)
    C.done(SLUG, BEATS, [
        frame((-20.0, 30.0, -40.0), 400.0, 0.20, 0.45),
        frame((-60.0, 50.0, -20.0), 300.0, 0.30, 0.30),
        frame((40.0, 50.0, -10.0), 300.0, -0.25, 0.30),
        frame((0.0, 130.0, -120.0), 300.0, 0.05, 0.15),
        frame((0.0, 40.0, -60.0), 520.0, -0.15, 0.40),
    ], root)


if __name__ == "__main__":
    build()
