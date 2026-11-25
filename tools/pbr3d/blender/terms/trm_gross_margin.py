"""TRM_GROSS_MARGIN: revenue minus cost of revenue, shown as stacked cost bars beside a GPU-board
assembly line.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_gross_margin.py

A conveyor carries finished accelerator boards (package, die, HBM stacks) toward the dock. Behind
it stand the input bins (HBM stacks, CoWoS substrates, PCB + assembly). Each sold board pours green
revenue beads into a tall bar; cost beads from the bins fill its lower segments, and what is left on
top is gross profit. A second bar shows a server assembler's thin margin; a third pair shows mix and
memory costs eating into the green; the green then splits into R&D, SG&A and operating profit.

Beats:
  0 sale      boards roll off the line, revenue fills the bar
  1 costs     HBM, package and board costs fill the bottom, gross profit on top
  2 pricing   chip designer (~75%) next to server assembler (~10%)
  3 mix       HBM gets pricier, mix shifts: cost grows, green shrinks
  4 uses      gross profit pays R&D and SG&A first; tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, key, P, mat  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_GROSS_MARGIN"
BEATS = [
    ("Every board sold brings in revenue",
     "Gross margin starts with revenue: the price customers pay for each GPU board, server or chip that ships. "
     "Here boards roll off the line and each sale pours into the revenue bar. On its own, revenue says nothing about "
     "how much of that money the company keeps."),
    ("Cost of revenue fills the bottom; gross profit is what is left",
     "Cost of revenue is what it took to make what was sold: purchased memory (HBM), advanced packaging (CoWoS), the "
     "board, components, assembly, test and yield losses. Subtract it from revenue and the remainder is gross profit. "
     "Gross margin is gross profit divided by revenue, so a $100 sale with $25 of cost is a 75% gross margin."),
    ("Pricing power shows up as a fat margin; assemblers run thin",
     "A chip designer that owns the product sells a board for several times its input cost and runs gross margins in "
     "the 70s. A server assembler buys those same GPUs and resells them inside a box, so most of its revenue passes "
     "straight through to cost and margins sit near 10%. Same hardware, very different share of each dollar kept."),
    ("Input costs and product mix move the margin",
     "When HBM prices rise, a new product ramps with low early yields, or sales shift toward cheaper parts, cost per "
     "dollar of revenue goes up and the green shrinks. A few points of gross margin on a large revenue base can swing "
     "operating profit by billions, which is why guidance on margin moves stocks."),
    ("Gross profit pays for R&D and SG&A; the rest is operating profit",
     "Operating expenses come out of gross profit, not revenue: engineering (R&D), sales and admin (SG&A). A high, "
     "stable gross margin leaves room to outspend rivals on R&D and still earn a lot. "
     "Related: NVIDIA (NVDA), Broadcom (AVGO), Super Micro (SMCI), Dell (DELL)."),
]

BZ = -40.0  # bars and conveyor z centre
BAR_W = 13.0  # half width
H = 120.0  # bar height for 100% of revenue
XA, XB = 60.0, 130.0  # main bar, comparison bar


def mats(m):
    m["ground"] = mat("gm_ground", (0.22, 0.23, 0.25), rough=0.9)
    m["belt"] = mat("gm_belt", (0.08, 0.08, 0.09), rough=0.8)
    m["frame"] = mat("gm_frame", (0.35, 0.37, 0.40), metal=0.8, rough=0.4)
    m["bin"] = mat("gm_bin", (0.20, 0.30, 0.45), metal=0.3, rough=0.5)
    m["rev"] = mat("gm_rev", (0.55, 1.0, 0.45), emit=(0.5, 1.0, 0.4), strength=0.7)
    m["gp"] = mat("gm_gp", (0.35, 0.95, 0.45), emit=(0.30, 0.90, 0.40), strength=0.7)
    m["c_hbm"] = mat("gm_chbm", (0.25, 0.50, 1.0), emit=(0.25, 0.50, 1.0), strength=0.7)
    m["c_pkg"] = mat("gm_cpkg", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.15), strength=0.7)
    m["c_brd"] = mat("gm_cbrd", (0.60, 0.62, 0.66), emit=(0.55, 0.58, 0.62), strength=0.3)
    m["c_gpu"] = mat("gm_cgpu", (0.70, 0.40, 1.0), emit=(0.65, 0.35, 1.0), strength=0.7)
    m["rd"] = mat("gm_rd", (0.40, 0.85, 1.0), emit=(0.35, 0.80, 1.0), strength=0.7)
    m["sga"] = mat("gm_sga", (1.0, 0.85, 0.35), emit=(1.0, 0.80, 0.30), strength=0.7)


def gpu_board(m, g, name, x, y, z):
    """A small accelerator board: green PCB, substrate, two dies, four HBM stacks, power stages."""
    p = [bx(f"{name}_pcb", (x - 16.0, y, z - 11.0), (x + 16.0, y + 1.2, z + 11.0), m["mask"], g),
         bx(f"{name}_sub", (x - 8.0, y + 1.2, z - 7.0), (x + 8.0, y + 2.2, z + 7.0), m["substrate"], g),
         bx(f"{name}_d0", (x - 5.0, y + 2.2, z - 4.0), (x - 0.4, y + 3.2, z + 4.0), m["die"], g),
         bx(f"{name}_d1", (x + 0.4, y + 2.2, z - 4.0), (x + 5.0, y + 3.2, z + 4.0), m["die"], g)]
    for j, zz in enumerate((-5.6, 4.0)):
        for i, xx in enumerate((-5.0, 1.0)):
            p.append(bx(f"{name}_h{i}{j}", (x + xx, y + 2.2, z + zz), (x + xx + 4.0, y + 4.0, z + zz + 1.6), m["hbm"], g))
    for i in range(5):
        p.append(bx(f"{name}_st{i}", (x - 14.0 + i * 2.6, y + 1.2, z - 9.5), (x - 12.4 + i * 2.6, y + 2.0, z - 7.5), m["fet"], g))
        p.append(bx(f"{name}_in{i}", (x - 14.0 + i * 2.6, y + 1.2, z + 7.0), (x - 12.0 + i * 2.6, y + 3.0, z + 9.5), m["ferrite"], g))
    p.append(bx(f"{name}_edge", (x + 16.0, y, z - 8.0), (x + 17.5, y + 1.0, z + 8.0), m["gold"], g))
    return D.join(p, f"{name}_m")


def conveyor(m, root):
    g = empty("line", root)
    p = [bx("belt", (-250.0, 10.0, BZ - 15.0), (0.0, 12.0, BZ + 15.0), m["belt"], g)]
    for side in (-1, 1):
        p.append(bx(f"rail{side}", (-252.0, 8.0, BZ + side * 15.0), (2.0, 14.0, BZ + side * 17.0), m["frame"], g))
    for k in range(9):
        x = -245.0 + k * 30.0
        for side in (-1, 1):
            p.append(bx(f"leg{k}{side}", (x - 1.2, 0.0, BZ + side * 15.0 - 1.2), (x + 1.2, 8.0, BZ + side * 15.0 + 1.2), m["frame"], g))
    for k in range(26):
        x = -248.0 + k * 9.6
        p.append(D.tube(f"rol{k}", (x, 9.0, BZ - 15.0), (x, 9.0, BZ + 15.0), 1.2, m["steel"], g, 8))
    D.join(p, "line_m")
    # a test/inspection gantry over the belt
    q = [bx("gan_l", (-130.0, 0.0, BZ - 22.0), (-126.0, 40.0, BZ - 18.0), m["frame"], g),
         bx("gan_r", (-130.0, 0.0, BZ + 18.0), (-126.0, 40.0, BZ + 22.0), m["frame"], g),
         bx("gan_t", (-134.0, 40.0, BZ - 22.0), (-122.0, 46.0, BZ + 22.0), m["dark"], g),
         bx("gan_h", (-131.0, 30.0, BZ - 6.0), (-125.0, 40.0, BZ + 6.0), m["alu"], g)]
    D.join(q, "gantry_m")
    scan = empty("scan", root)
    bx("scan_b", (-129.0, 13.0, BZ - 14.0), (-127.0, 30.0, BZ + 14.0), m["pwm"], scan)
    # boards that slide along the belt, beat after beat
    mv = empty("boards", root)
    for k in range(6):
        gpu_board(m, mv, f"bd{k}", -230.0 + k * 40.0, 12.0, BZ)
    return mv, scan


def bins(m, root):
    """Input bins behind the line: HBM stacks, CoWoS substrates, PCBs. Returns tag points + outlets."""
    g = empty("bins", root)
    p = []
    out = {}
    for k, (key_, x) in enumerate((("hbm", -200.0), ("pkg", -140.0), ("brd", -80.0))):
        z = -110.0
        p.append(bx(f"bin{k}", (x - 22.0, 0.0, z - 18.0), (x + 22.0, 18.0, z + 18.0), m["bin"], g))
        p.append(bx(f"bin{k}_lip", (x - 23.0, 18.0, z - 19.0), (x + 23.0, 19.5, z + 19.0), m["frame"], g))
        for i in range(4):
            for j in range(3):
                cx, cz = x - 15.0 + i * 10.0, z - 10.0 + j * 10.0
                if key_ == "hbm":  # stacks of DRAM dies
                    for s in range(4):
                        p.append(bx(f"hb{i}{j}{s}", (cx - 2.5, 19.5 + s * 1.4, cz - 3.5), (cx + 2.5, 20.6 + s * 1.4, cz + 3.5),
                                    m["hbm_dram"] if s % 2 else m["hbm"], g))
                elif key_ == "pkg":
                    p.append(bx(f"pk{i}{j}", (cx - 4.0, 19.5, cz - 4.0), (cx + 4.0, 20.8, cz + 4.0), m["substrate"], g))
                    p.append(bx(f"pi{i}{j}", (cx - 2.6, 20.8, cz - 2.6), (cx + 2.6, 21.4, cz + 2.6), m["silicon"], g))
                else:
                    p.append(bx(f"pb{i}{j}", (cx - 4.5, 19.5, cz - 4.5), (cx + 4.5, 20.5 + j * 0.8, cz + 4.5), m["mask"], g))
        out[key_] = (x, 26.0, z)
    D.join(p, "bins_m")
    return out


def bar(m, root, name, x, segs, lit_iv):
    """A stacked bar at x: segs = [(fraction, mat), ...] bottom up, shown during lit_iv. Returns
    the y of each segment's centre."""
    g = empty(name, root)
    y = 0.6
    mids = []
    for k, (f, mt) in enumerate(segs):
        h = H * f
        bx(f"{name}_{k}", (x - BAR_W + 1.0, y, BZ - BAR_W + 1.0), (x + BAR_W - 1.0, y + h - 0.4, BZ + BAR_W - 1.0), m[mt], g)
        mids.append(y + h / 2)
        y += h
    show(g, lit_iv)
    return mids


def frame_bar(m, root, name, x):
    """The rack each bar stands in: plinth, four posts, a 100% cap and tick marks."""
    p = [bx(f"{name}_pl", (x - BAR_W - 4.0, 0.0, BZ - BAR_W - 4.0), (x + BAR_W + 4.0, 0.6, BZ + BAR_W + 4.0), m["dark"], root)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            p.append(bx(f"{name}_p{sx}{sz}", (x + sx * BAR_W - 0.7, 0.6, BZ + sz * BAR_W - 0.7),
                        (x + sx * BAR_W + 0.7, H + 2.0, BZ + sz * BAR_W + 0.7), m["frame"], root))
    p.append(bx(f"{name}_cap", (x - BAR_W - 1.0, H + 2.0, BZ - BAR_W - 1.0), (x + BAR_W + 1.0, H + 3.0, BZ + BAR_W + 1.0), m["frame"], root))
    for k in range(1, 10):
        y = H * k / 10
        p.append(bx(f"{name}_t{k}", (x - BAR_W - 3.0, y - 0.3, BZ + BAR_W), (x - BAR_W, y + 0.3, BZ + BAR_W + 0.6), m["ink"], root))
    D.join(p, f"{name}_frame")


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-280.0, -2.0, -160.0), (250.0, 0.0, 40.0), m["ground"], root)
    boards, scan = conveyor(m, root)
    # boards advance one slot per half beat across the whole page
    for b in range(len(BEATS)):
        key(boards, F(b, 0), "location", P(0, 0, 0), linear=True)
        key(boards, F(b + 1, 0) - 1, "location", P(40.0, 0, 0), linear=True)
    blink(scan, 0, range(8), n=8, on=0.4)
    blink(scan, 1, range(8), n=8, on=0.4)
    bo = bins(m, root)
    frame_bar(m, root, "fa", XA)
    frame_bar(m, root, "fb", XB)

    # beat 0: the whole bar is revenue
    bar(m, root, "rev", XA, [(1.0, "rev")], [(F(0, 0.35), F(1, 0.2))])
    run(root, "sale", [(0.0, 16.0, BZ), (25.0, 60.0, BZ), (XA, H - 10.0, BZ)], 10, 2.2, m["rev"], [0], 0.0, 0.6, 50)
    # beats 1, 2 and 4: costs at the bottom, gross profit on top (~75%)
    A1 = [(0.11, "c_hbm"), (0.08, "c_pkg"), (0.06, "c_brd"), (0.75, "gp")]
    ma = bar(m, root, "a1", XA, A1, [(F(1, 0.2), F(3, 0.1)), (F(4, 0), F(5, 0))])
    for k, (key_, seg) in enumerate((("hbm", 0), ("pkg", 1), ("brd", 2))):
        sx, sy, sz = bo[key_]
        run(root, f"cost{k}", [(sx, sy, sz), (sx + 40.0, 70.0, (sz + BZ) / 2), (XA - BAR_W - 2.0, ma[seg], BZ)],
            6, 2.0, m[A1[seg][1]], [1], 0.0 + 0.1 * k, 0.55 + 0.1 * k, 55)
    # beat 2: the assembler's bar, mostly purchased GPUs
    B = [(0.70, "c_gpu"), (0.08, "c_hbm"), (0.12, "c_brd"), (0.10, "gp")]
    mb = bar(m, root, "b", XB, B, [(F(2, 0.15), F(5, 0))])
    run(root, "passthru", [(XA, ma[3], BZ + 14.0), ((XA + XB) / 2, 30.0, BZ + 24.0), (XB, mb[0], BZ + 14.0)],
        8, 2.0, m["c_gpu"], [2], 0.25, 0.85, 45)
    # beat 3: pricier HBM, low-yield ramp: the green shrinks
    A2 = [(0.19, "c_hbm"), (0.12, "c_pkg"), (0.07, "c_brd"), (0.62, "gp")]
    m2 = bar(m, root, "a2", XA, A2, [(F(3, 0.1), F(4, 0))])
    shrink = empty("shrink", root)
    bx("shr", (XA - BAR_W - 1.0, H * 0.75 - 0.5, BZ + BAR_W + 0.5), (XA + BAR_W + 1.0, H * 0.75 + 0.5, BZ + BAR_W + 1.5), m["fail"], shrink)
    blink(shrink, 3, range(8), n=8, on=0.5, u0=0.2)
    run(root, "hbm_up", [(bo["hbm"][0], 26.0, bo["hbm"][2]), (-60.0, 90.0, -80.0), (XA - BAR_W - 2.0, m2[0], BZ)],
        8, 2.6, m["c_hbm"], [3], 0.1, 0.7, 50)
    # beat 4: gross profit splits into R&D, SG&A and operating profit
    split = [(0.25, "rd"), (0.10, "sga"), (0.40, "gp")]
    yb = H * 0.25 + 0.6
    sg = empty("split", root)
    for k, (f, mt) in enumerate(split):
        h = H * f
        bx(f"sp{k}", (XA + BAR_W + 3.0, yb, BZ - 6.0), (XA + BAR_W + 9.0, yb + h - 0.6, BZ + 6.0), m[mt], sg)
        yb += h
    show(sg, [(F(4, 0.15), F(5, 0))])
    for k, (x, mt, y) in enumerate(((190.0, "rd", 30.0), (215.0, "sga", 20.0))):
        p = [bx(f"op{k}", (x - 10.0, 0.0, BZ - 10.0), (x + 10.0, y, BZ + 10.0), m["dark"], root)]
        D.join(p, f"op{k}_m")
        run(root, f"opx{k}", [(XA + BAR_W, H * (0.38 if k == 0 else 0.55), BZ), (x, y + 30.0, BZ), (x, y + 2.0, BZ)],
            8, 2.0, m[mt], [4], 0.2 + 0.1 * k, 0.8, 45)
    rise(root, "opprofit", (XA, H + 4.0, BZ), 8, 1.4, m["gp"], 4, 0.3, 0.9, 24.0, 50, (8.0, 6.0))

    top = (XA, H + 3.0, BZ)
    C.tags(root, {
        0: [("boards roll off the line", (-150.0, 16.0, BZ)), ("each sale = revenue", (25.0, 60.0, BZ)),
            ("revenue: 100%", top)],
        1: [("HBM memory", (XA - BAR_W, ma[0], BZ + BAR_W)), ("CoWoS packaging", (XA - BAR_W, ma[1], BZ + BAR_W)),
            ("board, assembly, test", (XA - BAR_W, ma[2], BZ + BAR_W)), ("gross profit ~75%", (XA, ma[3], BZ + BAR_W)),
            ("input bins", bo["pkg"])],
        2: [("chip designer: ~75%", (XA, H + 3.0, BZ)), ("server assembler: ~10%", (XB, H + 3.0, BZ)),
            ("GPUs pass straight through", (XB, mb[0], BZ + BAR_W))],
        3: [("HBM price up", (XA - BAR_W, m2[0], BZ + BAR_W)), ("margin 75% -> 62%", (XA, H * 0.75, BZ + BAR_W)),
            ("new ramp, low yield", (XA - BAR_W, m2[1], BZ + BAR_W))],
        4: [("R&D", (190.0, 32.0, BZ)), ("SG&A", (215.0, 22.0, BZ)), ("operating profit", (XA, H + 6.0, BZ)),
            ("NVDA AVGO SMCI DELL", (-150.0, 16.0, BZ))],
    })
    C.done(SLUG, BEATS, [
        frame((-60.0, 40.0, -60.0), 340.0, 0.35, 0.40, pad=1.0),
        frame((0.0, 50.0, -60.0), 230.0, 0.25, 0.28),
        frame(((XA + XB) / 2, 60.0, BZ), 150.0, 0.15, 0.15),
        frame((XA + 20.0, 60.0, BZ), 170.0, -0.20, 0.18),
        frame((120.0, 55.0, BZ), 210.0, 0.20, 0.22),
    ], root)


if __name__ == "__main__":
    build()
