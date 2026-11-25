"""TRM_BILL_OF_MATERIALS: the Terms-tab overview for a bill of materials (BOM).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_bill_of_materials.py

Left: an AI server board. Its parts lift off into an exploded row above it, each lined up with a
row on the BOM sheet and a coin stack for its cost. Middle: parts crates arrive from suppliers; the
memory crate is late (long lead) and the half-built boards wait. Right: a margin bar that moves when
one BOM line changes price.

Beats:
  0 list      the board and its BOM sheet: every part, quantity, supplier
  1 cost      each line carries a cost; the sum is the BOM cost
  2 lead      long-lead parts (memory, optics) gate how many boards get finished
  3 change    one line gets dearer: margin shrinks with no change to the product
  4 read      how to read BOM talk in filings and calls
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, rise, present  # noqa: E402
import kit_ledger as K  # noqa: E402

SLUG = "TRM_BILL_OF_MATERIALS"
BEATS = [
    ("A BOM lists every part that goes into a product",
     "A bill of materials names each component, how many are needed and who supplies it. For an AI server board that "
     "means the GPU, HBM memory stacks, voltage regulators, capacitors, connectors and optics. Purchasing, planning and "
     "costing all run off this list."),
    ("Add up the lines and you get the BOM cost",
     "Each line has a unit price, and quantity times price summed over the list is the BOM cost. In an AI server the "
     "GPU and memory dominate: they can be most of the bill, while hundreds of small parts add only a few percent."),
    ("One long-lead part caps how many systems get built",
     "A board cannot ship until every line is in hand. If memory or optics take months to arrive, finished boards stop "
     "at the count the scarcest part allows, and the rest sit half built on the floor."),
    ("A BOM change moves margin without changing the product",
     "If one line gets dearer, say memory prices rise, the BOM cost goes up while the selling price may not. The margin "
     "shrinks even though the product looks the same. Swapping a supplier or part can push the other way."),
    ("Read BOM cost and long-lead parts behind server margins",
     "When builders talk about component costs, memory pricing or supply-gated shipments, they are talking about the BOM. "
     "Pass-through GPU cost can raise revenue while thinning margin. Related: Jabil (JBL), Flex (FLEX), Super Micro (SMCI)."),
]

# (name, x, z, w, d, h, material, coins)
PARTS = [
    ("gpu", -150.0, -10.0, 34.0, 34.0, 4.0, "die", 12),
    ("hbm", -118.0, -10.0, 10.0, 14.0, 6.0, "hbm", 7),
    ("vrm", -186.0, -10.0, 14.0, 10.0, 7.0, "ferrite", 3),
    ("opt", -150.0, 30.0, 26.0, 10.0, 5.0, "alu", 4),
    ("cap", -186.0, 30.0, 8.0, 5.0, 3.0, "mlcc", 1),
]


def mats(m):
    m["bm_floor"] = mat("bm_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["bm_bar"] = mat("bm_bar", (0.25, 0.60, 0.40), rough=0.6)
    m["bm_bar_r"] = mat("bm_bar_r", (0.70, 0.25, 0.20), rough=0.6)
    m["bm_line"] = mat("bm_line", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=3.0)
    m["bm_late"] = mat("bm_late", (1.0, 0.30, 0.20), emit=(1.0, 0.28, 0.18), strength=4.0)


def board(m, root):
    C.pcb(m, root, "board", -210.0, -90.0, -40.0, 50.0)
    for i in range(6):
        C.trace(m, root, f"tr{i}", [(-205.0, 0.0, -32.0 + i * 13.0), (-95.0, 0.0, -32.0 + i * 13.0)], w=0.6)
    # ghost footprints left on the board once the parts lift off
    for n, x, z, w, d, h, mt, _ in PARTS:
        bx(f"pad_{n}", (x - w / 2, 0.0, z - d / 2), (x + w / 2, 0.2, z + d / 2), m["solder"], root)
    # second HBM stack and a row of extra caps for detail
    bx("hbm2", (-128.0, 0.0, -2.0), (-108.0, 6.0, 4.0), m["hbm"], root)
    for k in range(6):
        bx(f"capx{k}", (-200.0 + k * 6.0, 0.0, 42.0), (-196.0 + k * 6.0, 2.0, 45.0), m["mlcc"], root)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    mats(m)
    bx("floor", (-260.0, -4.0, -180.0), (260.0, -2.0, 120.0), m["bm_floor"], root)
    board(m, root)

    # the BOM sheet standing behind the board
    K.ledger_sheet(m, root, "sheet", (-150.0, 0.0, -120.0), 110.0, 90.0, lines=7)

    # parts lift into an exploded row, each lined up with a BOM line and its cost stack
    for k, (n, x, z, w, d, h, mt, coins) in enumerate(PARTS):
        p = bx(f"part_{n}", (-w / 2, 0.0, -d / 2), (w / 2, h, d / 2), m[mt], root)
        p.location = (x, 0.2, z)
        ex = -220.0 + k * 34.0
        K.slide(p, 0, (x, 0.2, z), (ex, 60.0, -70.0), 0.25, 0.75)
        run(root, f"lk_{n}", [(ex, 60.0, -70.0), (ex, 75.0 - k * 9.0, -118.0)], 3, 1.6, m["bm_line"], [0, 1], 0.6, 0.95, 30)
        stack = K.coin_stack(m, root, f"cost_{n}", (ex, 0.0, -70.0), coins, r=5.0, h=1.6)
        show(stack, [(F(1, 0.1), F(5, 0))])

    # the BOM total: a bar that rises in beat 1 and grows again in beat 3
    total = K.ledger_bar(m, root, "bom_total", -40.0, -70.0, 18.0, {1: 50.0, 3: 64.0}, "bm_bar_r")
    show(total, [(F(1, 0), F(5, 0))])

    # beat 2: crates from suppliers, memory crate late; half-built boards wait
    crates = []
    for k in range(4):
        c = K.order_stack(m, root, f"crate{k}", (10.0 + k * 22.0, 0.0, 20.0), 2, 2, s=7.0)
        crates.append(c)
        show(c, [(F(2, 0), F(4, 0))])
        run(root, f"in{k}", [(10.0 + k * 22.0, 30.0, 110.0), (10.0 + k * 22.0, 20.0, 20.0)], 4, 2.0,
            m["ldg_blue_b"], 2, 0.0, 0.5, 30)
    wait = empty("wait", root)
    late = empty("late", root)
    bx("late_gap", (114.0, 0.0, 14.0), (126.0, 14.0, 26.0), m["bm_late"], late)
    present(late, [(F(2, 0.1), F(2, 0.95))])
    for k in range(5):
        x = 47.0 + k * 18.0
        bx(f"half{k}", (x - 7.0, 0.0, -30.0), (x + 7.0, 2.0, -10.0), m["mask"], wait)
        C.chip(m, wait, f"hc{k}", (x, 2.0, -24.0), 6.0, 6.0, pins=3)
        bx(f"hgap{k}", (x - 4.0, 2.0, -17.0), (x + 4.0, 2.3, -13.0), m["bm_late"], wait)
    present(wait, [(F(2, 0.2), F(3, 1.0))])
    # beat 3: margin bar shrinks while price holds
    price = K.ledger_bar(m, root, "price", 190.0, -40.0, 18.0, {3: 90.0}, "ldg_paper")
    margin = K.ledger_bar(m, root, "margin", 220.0, -40.0, 18.0, {3: 30.0, 4: 16.0}, "bm_bar")
    show(price, [(F(3, 0), F(5, 0))])
    show(margin, [(F(3, 0), F(5, 0))])
    rise(root, "memheat", (-186.0, 66.0, -70.0), 6, 1.6, m["bm_late"], 3, h=24.0)

    C.tags(root, {
        0: [("every part, qty, supplier", (-150.0, 100.0, -120.0)), ("AI server board", (-150.0, 20.0, 40.0))],
        1: [("GPU + HBM = most of the bill", (-200.0, 90.0, -70.0)), ("sum = BOM cost", (-40.0, 70.0, -70.0))],
        2: [("memory late: long lead", (120.0, 30.0, 20.0)), ("boards wait half built", (80.0, 20.0, -20.0)),
            ("parts from suppliers", (40.0, 40.0, 80.0))],
        3: [("memory line gets dearer", (-186.0, 100.0, -70.0)), ("price holds", (190.0, 100.0, -40.0)),
            ("margin shrinks", (220.0, 50.0, -40.0))],
        4: [("BOM drives cost + output", (0.0, 90.0, -60.0)), ("JBL FLEX SMCI", (0.0, 70.0, 20.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-150.0, 30.0, -50.0), 200.0, 0.25, 0.45),
        frame((-150.0, 40.0, -80.0), 200.0, -0.10, 0.30),
        frame((80.0, 10.0, 0.0), 150.0, 0.10, 0.55),
        frame((40.0, 40.0, -50.0), 330.0, -0.15, 0.35, pad=1.0),
        frame((0.0, 30.0, -40.0), 460.0, 0.10, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
