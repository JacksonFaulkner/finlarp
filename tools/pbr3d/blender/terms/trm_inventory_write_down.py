"""TRM_INVENTORY_WRITE_DOWN: unsold old-generation boards in a warehouse lose value when a new
platform ships, and the gap is charged to cost of revenue.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_inventory_write_down.py

Pallet racking full of boxed GPU boards (one carton cut open to show the board), a book-value bar
(what the stock cost) beside it, and a market-value bar. A truck backs in with the new generation;
the old stock dims, its market value drops below cost, and the red gap drains through a pipe into
the quarter's gross-margin bar.

Beats:
  0 stock     racks of finished boards, carried at cost
  1 new gen   a truck brings the next platform; buyers switch
  2 gap       market value falls below book value
  3 charge    the gap drains into cost of revenue; gross margin drops
  4 after     smaller book value going forward; tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, key, P, mat  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, present  # noqa: E402

SLUG = "TRM_INVENTORY_WRITE_DOWN"
BEATS = [
    ("Unsold boards sit on the balance sheet at what they cost",
     "Inventory is product a company has paid to build but not yet sold: raw parts, work in progress and finished "
     "boards. It is carried on the balance sheet at cost. For an AI hardware maker that can be billions of dollars of "
     "GPUs, memory and servers sitting in warehouses and contract factories."),
    ("A new platform ships and buyers move to it",
     "AI hardware turns over fast: a new GPU generation every year or so, faster memory, new rack designs. Once the "
     "next platform is available, customers stop ordering the old one, and parts bought for it can be left over."),
    ("When the stock can only sell below cost, its value is cut",
     "Accounting rules say inventory must be carried at the lower of cost and what it can be sold for. If old boards "
     "can now only fetch less than they cost, or nothing at all, the company must write their value down to that "
     "lower number. The gap between the two bars is the write-down."),
    ("The write-down is charged to cost of revenue and hits gross margin",
     "The charge goes through cost of revenue in the quarter it is booked, so reported gross margin drops even though "
     "no extra product was made. Companies often call out the one-time amount so investors can see the underlying "
     "margin. A large charge is a sign demand shifted faster than the supply plan."),
    ("Afterwards the stock is carried at the lower value",
     "If written-down parts later sell, there is little cost left against them, which can flatter margins for a "
     "quarter. Watch inventory growth against sales: stock rising much faster than revenue is an early warning. "
     "Related: NVIDIA (NVDA), Super Micro (SMCI), Micron (MU), Intel (INTC)."),
]

RZ = -60.0  # racks centre z
BX_, BZ = 120.0, -30.0  # value bars: book at BX_, market at BX_ + 34
H = 110.0
GX = 220.0  # gross-margin bar


def mats(m):
    m["floor"] = mat("iw_floor", (0.30, 0.31, 0.33), rough=0.85)
    m["upright"] = mat("iw_up", (0.20, 0.35, 0.65), metal=0.6, rough=0.4)
    m["beam"] = mat("iw_beam", (0.95, 0.50, 0.12), metal=0.5, rough=0.4)
    m["carton"] = mat("iw_carton", (0.62, 0.48, 0.30), rough=0.85)
    m["old"] = mat("iw_old", (0.36, 0.34, 0.32), rough=0.9)
    m["pallet"] = mat("iw_pallet", (0.55, 0.42, 0.26), rough=0.9)
    m["truck"] = mat("iw_truck", (0.85, 0.86, 0.88), metal=0.3, rough=0.5)
    m["cab"] = mat("iw_cab", (0.15, 0.35, 0.55), metal=0.5, rough=0.4)
    m["book"] = mat("iw_book", (1.0, 0.70, 0.25), emit=(1.0, 0.62, 0.18), strength=0.7)
    m["mkt"] = mat("iw_mkt", (0.35, 0.70, 1.0), emit=(0.3, 0.65, 1.0), strength=0.7)
    m["loss"] = mat("iw_loss", (1.0, 0.20, 0.12), emit=(1.0, 0.18, 0.10), strength=1.2)
    m["gp"] = mat("iw_gp", (0.35, 0.95, 0.45), emit=(0.30, 0.90, 0.40), strength=0.7)
    m["cogs"] = mat("iw_cogs", (0.60, 0.62, 0.66), emit=(0.55, 0.58, 0.62), strength=0.25)
    m["newg"] = mat("iw_newg", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=2.5)


def board(m, g, name, x, y, z, s=1.0):
    p = [bx(f"{name}_pcb", (x - 9 * s, y, z - 6 * s), (x + 9 * s, y + 0.8 * s, z + 6 * s), m["mask"], g),
         bx(f"{name}_sub", (x - 5 * s, y + 0.8 * s, z - 4 * s), (x + 5 * s, y + 1.5 * s, z + 4 * s), m["substrate"], g),
         bx(f"{name}_die", (x - 3 * s, y + 1.5 * s, z - 2.5 * s), (x + 3 * s, y + 2.2 * s, z + 2.5 * s), m["die"], g)]
    for i in (-1, 1):
        p.append(bx(f"{name}_h{i}", (x - 3 * s, y + 1.5 * s, z + i * 2.8 * s), (x + 3 * s, y + 2.6 * s, z + i * 3.8 * s), m["hbm"], g))
    return D.join(p, f"{name}_m")


def racks(m, root):
    """Three bays of pallet racking, three levels, cartons on every pallet. Returns the cut-open
    carton's centre and a dimming cover group (old stock goes grey)."""
    g = empty("racks", root)
    p = []
    lv = (0.0, 30.0, 60.0)
    for b in range(4):
        x = -200.0 + b * 80.0
        for z in (RZ - 25.0, RZ + 25.0):
            p.append(bx(f"up{b}{z:.0f}", (x - 1.5, 0.0, z - 1.5), (x + 1.5, 92.0, z + 1.5), m["upright"], g))
        for k in range(8):
            p.append(bx(f"br{b}{k}", (x - 0.5, 6.0 + 11.0 * k, RZ - 25.0), (x + 0.5, 7.0 + 11.0 * k, RZ + 25.0), m["upright"], g))
    cartons, covers = [], empty("dim", root)
    cut = None
    for b in range(3):
        x0 = -200.0 + b * 80.0
        for li, y in enumerate(lv):
            if y > 0:
                for z in (RZ - 25.0, RZ + 25.0):
                    p.append(bx(f"bm{b}{li}{z:.0f}", (x0, y - 3.0, z - 1.2), (x0 + 80.0, y, z + 1.2), m["beam"], g))
            for j in range(2):
                px = x0 + 6.0 + j * 36.0
                p.append(bx(f"pal{b}{li}{j}", (px, y, RZ - 22.0), (px + 32.0, y + 2.5, RZ + 22.0), m["pallet"], g))
                for cx in range(2):
                    for cz in range(2):
                        for cy in range(2):
                            lo = (px + 1.0 + cx * 15.5, y + 2.5 + cy * 11.0, RZ - 21.0 + cz * 21.5)
                            hi = (lo[0] + 14.5, lo[1] + 10.5, lo[2] + 20.5)
                            if b == 1 and li == 0 and j == 0 and cx == 1 and cz == 1 and cy == 0:
                                cut = (lo, hi)
                                continue
                            cartons.append(bx(f"ct{b}{li}{j}{cx}{cz}{cy}", lo, hi, m["carton"], g))
                            bx(f"cv{b}{li}{j}{cx}{cz}{cy}", (lo[0] - 0.1, lo[1] - 0.1, hi[2] - 0.1), (hi[0] + 0.1, hi[1] + 0.1, hi[2] + 0.3), m["old"], covers)
    D.join(cartons, "cartons_m")
    D.join(p, "racks_m")
    # the cut-open carton: three walls, foam, the board inside
    lo, hi = cut
    q = [bx("cut_back", lo, (hi[0], hi[1], lo[2] + 0.6), m["carton"], g),
         bx("cut_l", lo, (lo[0] + 0.6, hi[1], hi[2]), m["carton"], g),
         bx("cut_bot", lo, (hi[0], lo[1] + 0.6, hi[2]), m["carton"], g),
         bx("cut_foam", (lo[0] + 0.6, lo[1] + 0.6, lo[2] + 0.6), (hi[0], lo[1] + 2.0, hi[2]), m["white"], g)]
    D.join(q, "cut_m")
    c = ((lo[0] + hi[0]) / 2, lo[1] + 2.0, (lo[2] + hi[2]) / 2)
    board(m, g, "cut_bd", c[0], c[1], c[2], 0.7)
    return c, covers


def truck(m, root):
    """A box truck that backs in with new-generation boards (glowing dies)."""
    t = empty("truck", root)
    z = 50.0
    p = [bx("tr_box", (-180.0, 8.0, z - 16.0), (-100.0, 42.0, z + 16.0), m["truck"], t),
         bx("tr_cab", (-215.0, 8.0, z - 15.0), (-182.0, 34.0, z + 15.0), m["cab"], t),
         bx("tr_win", (-214.0, 24.0, z - 13.0), (-208.0, 32.0, z + 13.0), m["screen"], t),
         bx("tr_ch", (-215.0, 5.0, z - 12.0), (-100.0, 8.0, z + 12.0), m["dark"], t)]
    for x in (-200.0, -150.0, -115.0):
        for s in (-1, 1):
            p.append(D.tube(f"wh{x:.0f}{s}", (x, 5.0, z + s * 14.0), (x, 5.0, z + s * 18.0), 5.0, m["rubber"], t, 16))
    D.join(p, "truck_m")
    # new pallets sliding out the back, glowing
    ng = empty("newgen", t)
    for k in range(3):
        x = -95.0 + k * 22.0
        bx(f"np{k}", (x, 0.0, z - 10.0), (x + 18.0, 2.0, z + 10.0), m["pallet"], ng)
        board(m, ng, f"nb{k}", x + 9.0, 2.0, z, 0.9)
        bx(f"ng{k}", (x + 6.5, 4.2, z - 2.0), (x + 11.5, 4.6, z + 2.0), m["newg"], ng)
    return t, (-60.0, 10.0, z)


def bar(m, root, name, x, y0, h, mt, iv, w=12.0):
    g = empty(name, root)
    bx(f"{name}_b", (x - w, y0, BZ - w), (x + w, y0 + h, BZ + w), m[mt], g)
    show(g, iv)
    return g


def plinth(m, root, name, x, w=14.0, hh=H):
    p = [bx(f"{name}_pl", (x - w - 3.0, 0.0, BZ - w - 3.0), (x + w + 3.0, 0.6, BZ + w + 3.0), m["dark"], root)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            p.append(bx(f"{name}_p{sx}{sz}", (x + sx * w - 0.6, 0.6, BZ + sz * w - 0.6), (x + sx * w + 0.6, hh + 2.0, BZ + sz * w + 0.6), m["steel"], root))
    p.append(bx(f"{name}_cap", (x - w - 1.0, hh + 2.0, BZ - w - 1.0), (x + w + 1.0, hh + 3.0, BZ + w + 1.0), m["steel"], root))
    D.join(p, f"{name}_fr")


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-260.0, -2.0, -120.0), (270.0, 0.0, 90.0), m["floor"], root)
    for k in range(6):  # floor lane stripes
        x = -240.0 + k * 40.0
        bx(f"lane{k}", (x, 0.0, 18.0), (x + 22.0, 0.2, 21.0), m["beam"], root)
    cut, covers = racks(m, root)
    show(covers, [(F(1, 0.25), F(5, 0))])
    t, dock = truck(m, root)
    # the truck drives in during beat 1 and stays
    key(t, 0, "location", P(-140.0, 0, 0), linear=True)
    key(t, F(1, 0.05), "location", P(-140.0, 0, 0), linear=True)
    key(t, F(1, 0.45), "location", P(0, 0, 0), linear=True)
    show(t, [(F(1, 0), F(5, 0))])

    plinth(m, root, "bk", BX_)
    plinth(m, root, "mk", BX_ + 34.0)
    plinth(m, root, "gm", GX, 12.0, 90.0)
    # book value: full height all page until written down
    bar(m, root, "book", BX_, 0.6, H, "book", [(F(0, 0.2), F(2, 0.45))])
    bar(m, root, "book1", BX_, 0.6, H * 0.45, "book", [(F(2, 0.45), F(4, 0))])
    bar(m, root, "book2", BX_, 0.6, H * 0.45, "book", [(F(4, 0), F(5, 0))])
    # market value: equal to cost, then falls
    bar(m, root, "mkt1", BX_ + 34.0, 0.6, H, "mkt", [(F(0, 0.4), F(2, 0.25))])
    bar(m, root, "mkt2", BX_ + 34.0, 0.6, H * 0.45, "mkt", [(F(2, 0.25), F(5, 0))])
    gap = bar(m, root, "gap", BX_, 0.6 + H * 0.45, H * 0.55, "loss", [(F(2, 0.45), F(3, 0.6))], w=12.4)
    # the pipe from the top of the book bar to the gross-margin bar
    pipe = [(BX_, H + 6.0, BZ), (BX_, H + 18.0, BZ), (GX, H + 18.0, BZ), (GX, 96.0, BZ)]
    D.polyline("pipe", pipe, 2.4, m["steel"], root)
    run(root, "drain", pipe + [(GX, 70.0, BZ)], 14, 2.2, m["loss"], [3], 0.05, 0.7, 50)
    # gross-margin bar: cost grey under green; the charge pushes cost up
    bar(m, root, "gm_c", GX, 0.6, 30.0, "cogs", [(F(0, 0), F(3, 0.4))], w=10.0)
    bar(m, root, "gm_g", GX, 30.6, 58.0, "gp", [(F(0, 0), F(3, 0.4))], w=10.0)
    bar(m, root, "gm_c2", GX, 0.6, 30.0, "cogs", [(F(3, 0.4), F(5, 0))], w=10.0)
    bar(m, root, "gm_w", GX, 30.6, 14.0, "loss", [(F(3, 0.4), F(5, 0))], w=10.2)
    bar(m, root, "gm_g2", GX, 44.6, 44.0, "gp", [(F(3, 0.4), F(5, 0))], w=10.0)
    # beat 0: value beads from the racks to the book bar
    run(root, "carry", [(-80.0, 70.0, RZ), (40.0, 110.0, BZ), (BX_, H - 6.0, BZ)], 8, 2.0, m["book"], [0], 0.1, 0.7, 50)
    # beat 1: orders flow to the new pallets instead
    run(root, "orders", [(60.0, 60.0, 60.0), (0.0, 40.0, 60.0), (dock[0], 8.0, dock[2])], 8, 2.0, m["newg"], [1], 0.45, 0.95, 40)
    rise(root, "dust", (cut[0], cut[1] + 4.0, cut[2]), 5, 0.8, m["dim_glow"], [2, 3], 0.0, 0.8, 18.0, 50, (6.0, 4.0))

    C.tags(root, {
        0: [("finished boards, at cost", (-80.0, 70.0, RZ)), ("one carton opened", cut),
            ("book value", (BX_, H + 3.0, BZ)), ("market value", (BX_ + 34.0, H + 3.0, BZ))],
        1: [("next-gen platform arrives", dock), ("orders switch to new", (20.0, 50.0, 60.0)),
            ("old stock goes stale", (-120.0, 92.0, RZ))],
        2: [("market value drops", (BX_ + 34.0, H * 0.45, BZ + 12.0)), ("cost stays on the books", (BX_, H, BZ + 12.0)),
            ("gap = write-down", (BX_, H * 0.72, BZ + 12.0))],
        3: [("charged to cost of revenue", ((BX_ + GX) / 2, H + 20.0, BZ)), ("one-time hit", (GX, 38.0, BZ + 10.0)),
            ("gross margin drops", (GX, 88.0, BZ))],
        4: [("carried at the lower value", (BX_, H * 0.45, BZ + 12.0)), ("watch stock vs sales", (-80.0, 70.0, RZ)),
            ("NVDA SMCI MU INTC", (GX, 92.0, BZ))],
    })
    C.done(SLUG, BEATS, [
        frame((-10.0, 40.0, -30.0), 380.0, 0.30, 0.40, pad=1.0),
        frame((-110.0, 30.0, 10.0), 230.0, 0.45, 0.35),
        frame((BX_ + 17.0, 55.0, BZ), 140.0, 0.10, 0.15),
        frame(((BX_ + GX) / 2, 60.0, BZ), 190.0, 0.05, 0.15),
        frame((40.0, 50.0, -30.0), 330.0, -0.25, 0.30, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
