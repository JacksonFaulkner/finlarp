"""The MATH tab overviews, authored in Blender and exported for pbr3d, in the picture-and-panel
template (docs/diagram-pages.md). One scene per page of the Math tab, built on math_kit.py.

Run from the repo root, all twelve or one by name:

    blender -b --factory-startup --python tools/pbr3d/blender/math_pages.py
    blender -b --factory-startup --python tools/pbr3d/blender/math_pages.py -- dot_product

It writes, per page <slug>:
  blender/math_<slug>.blend   open it in Blender to edit by hand
  assets/math_<slug>.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/math/<slug>.rs). The beat counts here match those files.

Units: millimetres, Y up. Numbers are shown as dots, bars, arrows and grid cells; the values
themselves sit in `label:` tags the TUI pins while they are on.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import math_kit as K  # noqa: E402
from math_kit import BEAD_R, BEAD_STEP, F, OFF, arrow, axes, beat, bar, camera, dot, finish, floor, key, label  # noqa: E402
from math_kit import line, mats, show, slide, start, tile  # noqa: E402
from sand_overview import box, empty  # noqa: E402

ROW_Y = 70.0  # a dot resting on a floor at y = 0 sits at BEAD_R
TOP = BEAD_R


def add():
    m, root = start("add", 3, page="math")
    M = mats()
    floor("tray_a", root, -1300, -700, 0, M["tray"])
    floor("tray_b", root, 600, 1400, 0, M["tray"])
    floor("tray_sum", root, -700, 700, -330, M["tray"])
    red_a = [(-1200, TOP), (-1000, TOP), (-800, TOP)]
    blue_b = [(700, TOP), (900, TOP), (1100, TOP), (1300, TOP)]
    sum_y = -330 + TOP
    sum_x = [-570 + BEAD_STEP * k for k in range(7)]
    for i, (x, y) in enumerate(red_a):
        d = dot(f"red{i}", (x, y, 0), M["red"], root)
        slide(d, [(0, (x, y, 0)), (F(1, 0.15), (x, y, 0)), (F(1, 0.8), (sum_x[i], sum_y, 0))])
    for i, (x, y) in enumerate(blue_b):
        d = dot(f"blue{i}", (x, y, 0), M["blue"], root)
        slide(d, [(0, (x, y, 0)), (F(1, 0.15), (x, y, 0)), (F(1, 0.8), (sum_x[3 + i], sum_y, 0))])
    label("3 red dots", (-1000, 330, 0), root, beat(0))
    label("4 blue dots", (1000, 330, 0), root, beat(0))
    label("put them in one tray", (0, 300, 0), root, beat(1))
    label("3 + 4 = 7 dots", (0, -560, 0), root, beat(2))
    camera(root, [((50, -100, 0), 5000, 0.0, 0.12)] * 3)
    finish("add", page="math")


def subtract():
    m, root = start("subtract", 3, page="math")
    M = mats()
    floor("tray", root, -750, 750, 0, M["tray"])
    floor("tray_out", root, 790, 1560, 0, M["tray"])
    xs = [-570 + BEAD_STEP * k for k in range(7)]
    for k in range(3):
        dot(f"stay{k}", (xs[k], TOP, 0), M["grey"], root)
    taken = []
    for i in range(4):
        x = xs[3 + i]
        d = dot(f"taken{i}", (x, TOP, 0), M["red"], root)
        dest = 900 + BEAD_STEP * i
        slide(d, [(0, (x, TOP, 0)), (F(1, 0.15), (x, TOP, 0)), (F(1, 0.8), (dest, TOP, 0))])
        taken.append(d)
    label("start with 7 dots", (0, 330, 0), root, beat(0))
    label("take away 4", (1180, 330, 0), root, beat(1))
    label("3 left", (-190, 330, 0), root, beat(2))
    label("7 - 4 = 3", (0, -250, 0), root, beat(2))
    camera(root, [((550, 150, 0), 4600, 0.0, 0.10)] * 3)
    finish("subtract", page="math")


def multiply():
    m, root = start("multiply", 3, page="math")
    M = mats()
    cols = [M["red"], M["blue"], M["green"]]
    floors = [floor(f"ground{g}", root, (g - 1) * 1100 - 500, (g - 1) * 1100 + 500, 0, M["tray"]) for g in range(3)]
    for f in floors:
        show(f, beat(0))
    for g in range(3):
        cx = (g - 1) * 1100
        for j in range(4):
            x0 = cx - 285 + BEAD_STEP * j
            tgt = (-285 + BEAD_STEP * j, ROW_Y + 300 * g, 0)
            d = dot(f"g{g}_{j}", (x0, TOP, 0), cols[g], root)
            slide(d, [(0, (x0, TOP, 0)), (F(1, 0.15), (x0, TOP, 0)), (F(1, 0.75), (tgt[0], tgt[1], 0))])
    label("group 1: 4 dots", (-1100, 330, 0), root, beat(0))
    label("group 2: 4 dots", (0, 330, 0), root, beat(0))
    label("group 3: 4 dots", (1100, 330, 0), root, beat(0))
    label("3 groups of 4", (0, 600, 0), root, beat(0))
    label("stack them: 3 rows of 4", (0, 1000, 0), root, beat(1))
    label("3 x 4 = 12 dots", (0, -180, 0), root, beat(2))
    camera(root, [((0, 150, 0), 4700, 0.0, 0.08), ((0, 350, 0), 3000, 0.0, 0.08), ((0, 350, 0), 3000, 0.0, 0.08)])
    finish("multiply", page="math")


def divide():
    m, root = start("divide", 3, page="math")
    M = mats()
    gx = [-1200, -400, 400, 1200]
    for k in range(4):
        floor(f"slot{k}", root, gx[k] - 200, gx[k] + 200, 0, M["tray"], depth=160.0)
    cluster = []
    for n in range(12):
        r, j = divmod(n, 4)
        x0 = -285 + BEAD_STEP * j
        y0 = ROW_Y + 300 * r
        d = dot(f"d{n}", (x0, y0, 0), M["blue"], root)
        k, slot = n % 4, n // 4
        dest = (gx[k], TOP + 190 * slot, 0)
        t0 = 0.05 + 0.07 * n
        t1 = t0 + 0.13
        slide(d, [(0, (x0, y0, 0)), (F(1, t0), (x0, y0, 0)), (F(1, t1), dest)])
        cluster.append(d)
    label("12 dots", (0, 1050, 0), root, beat(0))
    label("deal one dot at a time", (0, 1050, 0), root, beat(1))
    label("12 / 4 = 3 in each group", (0, 1050, 0), root, beat(2))
    for k in range(4):
        label(f"group {k + 1}: 3 dots", (gx[k], -150, 0), root, beat(2))
    camera(root, [((0, 450, 0), 3600, 0.0, 0.08), ((0, 350, 0), 5200, 0.0, 0.08), ((0, 350, 0), 5200, 0.0, 0.08)])
    finish("divide", page="math")


def vector():
    m, root = start("vector", 3, page="math")
    M = mats()
    U = 200.0
    bg = empty("bars", root)
    show(bg, beat(0))
    floor("ground", bg, -900, 900, 0, M["tray"])
    for j, v in enumerate([2, 5, 1]):
        cx = -600 + 600 * j
        bar(f"slot{j + 1}", bg, cx - 100, cx + 100, v * U, M["gold"])
    # beat 1 and 2: the same list as an arrow in 3-D
    ax = empty("axes3", root)
    show(ax, beat(1) + beat(2))
    line("x_axis", ax, (-100, 0, 0), (720, 0, 0), M["ink"], r=6)
    line("y_axis", ax, (0, -100, 0), (0, 1400, 0), M["ink"], r=6)
    line("z_axis", ax, (0, 0, -100), (0, 0, 520), M["ink"], r=6)
    tip = (2 * U, 5 * U, 1 * U)
    ar = arrow("v", root, tip, M["cyan"], r=18.0, head=120.0, hr=60.0)
    show(ar, beat(1) + beat(2))
    stair = empty("steps", root)
    show(stair, beat(2))
    p0, p1, p2, p3 = (0, 0, 0), (tip[0], 0, 0), (tip[0], tip[1], 0), tip
    line("step_x", stair, p0, p1, M["ghost"], r=12)
    line("step_y", stair, p1, p2, M["ghost"], r=12)
    line("step_z", stair, p2, p3, M["ghost"], r=12)
    label("v = [2, 5, 1]", (0, 1300, 0), root, beat(0))
    label("slot 1 = 2", (-600, 480, 0), root, beat(0))
    label("slot 2 = 5", (0, 1080, 0), root, beat(0))
    label("slot 3 = 1", (600, 280, 0), root, beat(0))
    label("arrow from the origin", (-250, 200, 0), root, beat(1))
    label("2 steps along x", (620, -220, 0), root, beat(2))
    label("5 steps up, then 1 toward you", (-300, 1000, 120), root, beat(2))
    camera(root, [((0, 500, 0), 3800, 0.0, 0.05), ((300, 500, 110), 3600, 0.6, 0.3), ((300, 500, 110), 3700, 0.6, 0.3)])
    finish("vector", page="math")


def vector_add():
    m, root = start("vector_add", 3, page="math")
    M = mats()
    axes("axes", root, 1500, 2100, M["ink"])
    a = arrow("a", root, (300, 600, 0), M["gold"])
    show(a, beat(0) + beat(1) + beat(2))
    bm_outer = empty("b_show", root)
    show(bm_outer, [(F(1, 0.0), F(3, 0.0))])
    bm = empty("b_move", bm_outer)
    arrow("b", bm, (900, 1200, 0), M["blue"])
    slide(bm, [(0, (0, 0, 0)), (F(1, 0.0), (0, 0, 0)), (F(1, 0.6), (300, 600, 0))])
    c = arrow("c", root, (1200, 1800, 0), M["green"])
    show(c, beat(2))
    label("a = [1, 2]", (-250, 680, 0), root, beat(0))
    label("b = [3, 4], tail moved to the tip of a", (700, 380, 0), root, beat(1))
    label("a + b = [4, 6]", (1260, 1850, 0), root, beat(2))
    camera(root, [((450, 700, 0), 3700, 0.0, 0.0), ((600, 900, 0), 4000, 0.0, 0.0), ((600, 900, 0), 4300, 0.0, 0.0)])
    finish("vector_add", page="math")


def scale():
    m, root = start("scale", 3, page="math")
    M = mats()
    axes("axes", root, 1500, 2100, M["ink"])
    ghost = arrow("ghost", root, (300, 600, 0), M["ghost"])
    show(ghost, beat(1) + beat(2))
    sg = empty("scaled", root)
    arrow("main", sg, (300, 600, 0), M["gold"])
    key(sg, 0, "scale", (1.0, 1.0, 1.0))
    key(sg, F(1, 0.1), "scale", (1.0, 1.0, 1.0))
    key(sg, F(1, 0.7), "scale", (3.0, 3.0, 3.0))
    label("[1, 2]", (-200, 680, 0), root, beat(0))
    label("grow every slot by 3", (700, 1000, 0), root, beat(1))
    label("3 x [1, 2] = [3, 6]", (900, 1900, 0), root, beat(2))
    camera(root, [((300, 600, 0), 3300, 0.0, 0.0), ((600, 900, 0), 4000, 0.0, 0.0), ((600, 900, 0), 4400, 0.0, 0.0)])
    finish("scale", page="math")


def dot_product():
    m, root = start("dot_product", 3, page="math")
    M = mats()
    U = 60.0
    floor("ground", root, -1350, 1250, 0, M["tray"])
    a = [1, 2, 3]
    b = [4, 5, 6]
    for j in range(3):
        x0 = -1200 + 300 * j
        bar(f"a{j}", root, x0, x0 + 150, a[j] * U, M["blue"])
        x1 = -400 + 300 * j
        bar(f"b{j}", root, x1, x1 + 150, b[j] * U, M["gold"])
    # the products: one group each, grown from flat on beat 1, then slid into a column on beat 2
    stack_x = 1500.0
    stack_base = [0.0, 240.0, 840.0]  # products 4, 10, 18 stacked: 4, then 10, then 18
    for j in range(3):
        x0 = 400 + 300 * j
        pj = empty(f"product{j}", root)
        bar(f"p{j}", pj, x0, x0 + 150, a[j] * b[j] * U, M["green"])
        key(pj, 0, "scale", (1.0, 1.0, OFF))
        key(pj, F(1, 0.1), "scale", (1.0, 1.0, OFF))
        key(pj, F(1, 0.6), "scale", (1.0, 1.0, 1.0))
        dx, dy = stack_x - x0, stack_base[j]
        slide(pj, [(0, (0, 0, 0)), (F(2, 0.0), (0, 0, 0)), (F(2, 0.6), (dx, dy, 0))])
    label("a = [1, 2, 3]", (-900, 300, 0), root, beat(0))
    label("b = [4, 5, 6]", (-100, 420, 0), root, beat(0))
    label("dot product: a . b", (0, 900, 0), root, beat(0))
    label("1 x 4 = 4", (400, 300, 0), root, beat(1))
    label("2 x 5 = 10", (700, 700, 0), root, beat(1))
    label("3 x 6 = 18", (1000, 1150, 0), root, beat(1))
    label("4 + 10 + 18 = 32", (1500, 2000, 0), root, beat(2))
    camera(root, [((-300, 400, 0), 4300, 0.0, 0.08), ((700, 500, 0), 4300, 0.0, 0.08), ((800, 900, 0), 4900, 0.0, 0.08)])
    finish("dot_product", page="math")


def matrix():
    m, root = start("matrix", 3, page="math")
    M = mats()
    xs, ys = [-300.0, 0.0, 300.0], [300.0, 0.0]
    for r in range(2):
        for c in range(3):
            tile(f"a{r}{c}", xs[c], ys[r], M["tile"], root)
    lit_r1 = empty("row1_lit", root)
    for c in range(3):
        tile(f"r1_{c}", xs[c], ys[0], M["lit"], lit_r1)
    show(lit_r1, beat(1))
    lit_c2 = empty("col2_lit", root)
    for r in range(2):
        tile(f"c2_{r}", xs[1], ys[r], M["lit"], lit_c2)
    show(lit_c2, beat(2))
    label("A: 2 rows x 3 columns", (0, 560, 0), root, beat(0))
    label("shape (2 x 3): 6 numbers", (0, -260, 0), root, beat(0))
    label("row 1 = [1, 2, 3]", (0, 560, 0), root, beat(1))
    label("column 2 = [2, 5]", (0, 560, 0), root, beat(2))
    camera(root, [((0, 150, 0), 2600, 0.0, 0.0)] * 3)
    finish("matrix", page="math")


def shape_rule():
    m, root = start("shape_rule", 3, page="math")
    M = mats()
    xa, ya = [-1100.0, -800.0, -500.0], [300.0, 0.0]
    xb, yb = [-100.0, 200.0], [600.0, 300.0, 0.0]
    xc, yc = [900.0, 1200.0], [300.0, 0.0]
    for r in range(2):
        for c in range(3):
            tile(f"a{r}{c}", xa[c], ya[r], M["tile"], root)
    for r in range(3):
        for c in range(2):
            tile(f"b{r}{c}", xb[c], yb[r], M["tile"], root)
    cg = empty("answer", root)
    for r in range(2):
        for c in range(2):
            tile(f"c{r}{c}", xc[c], yc[r], M["green"], cg)
    show(cg, beat(2))
    brackets = empty("inner_brackets", root)
    box("a_cols", (xa[0] - 120, 400.0, -30.0), (xa[2] + 120, 430.0, 30.0), M["cyan"], brackets)
    box("b_rows", (xb[0] - 170, -110.0, -30.0), (xb[0] - 140, 710.0, 30.0), M["cyan"], brackets)
    show(brackets, beat(1))
    label("A is 2 x 3", (-800, 560, 0), root, beat(0))
    label("B is 3 x 2", (50, 760, 0), root, beat(0))
    label("inner 3 and 3 match", (-500, 500, 0), root, beat(1))
    label("answer: 2 x 2", (1050, 560, 0), root, beat(2))
    camera(root, [((150, 250, 0), 4500, 0.0, 0.0)] * 3)
    finish("shape_rule", page="math")


def matrix_vector():
    m, root = start("matrix_vector", 3, page="math")
    M = mats()
    xa, ya = [-700.0, -400.0], [300.0, 0.0]
    xv, xw = 0.0, 500.0
    for r in range(2):
        for c in range(2):
            tile(f"a{r}{c}", xa[c], ya[r], M["tile"], root)
        tile(f"v{r}", xv, ya[r], M["tile"], root)
        tile(f"w{r}", xw, ya[r], M["tile"], root)
    g1 = empty("row1_lit", root)
    for c in range(2):
        tile(f"ar1_{c}", xa[c], ya[0], M["lit"], g1)
    tile("v1", xv, ya[0], M["cyan"], g1)
    show(g1, beat(1))
    g2 = empty("row2_lit", root)
    for c in range(2):
        tile(f"ar2_{c}", xa[c], ya[1], M["lit"], g2)
    tile("v2", xv, ya[1], M["cyan"], g2)
    show(g2, beat(2))
    w1 = empty("slot1_lit", root)
    tile("w1", xw, ya[0], M["green"], w1)
    show(w1, beat(1) + beat(2))
    w2 = empty("slot2_lit", root)
    tile("w2", xw, ya[1], M["green"], w2)
    show(w2, beat(2))
    label("A (2 x 2)", (-550, 560, 0), root, beat(0))
    label("v (2 x 1)", (0, 560, 0), root, beat(0))
    label("answer (2 x 1)", (500, 560, 0), root, beat(0))
    label("1 x 5 + 2 x 6 = 17", (500, -260, 0), root, beat(1))
    label("3 x 5 + 4 x 6 = 39", (500, -260, 0), root, beat(2))
    camera(root, [((0, 150, 0), 2900, 0.0, 0.0)] * 3)
    finish("matrix_vector", page="math")


def matrix_matrix():
    m, root = start("matrix_matrix", 3, page="math")
    M = mats()
    xa, ya = [-700.0, -400.0], [300.0, 0.0]
    xb = [150.0, 450.0]
    xc = [800.0, 1100.0]
    for r in range(2):
        for c in range(2):
            tile(f"a{r}{c}", xa[c], ya[r], M["tile"], root)
            tile(f"b{r}{c}", xb[c], ya[r], M["tile"], root)
            tile(f"c{r}{c}", xc[c], ya[r], M["tile"], root)
    g1 = empty("cell11_lit", root)
    tile("ar1_0", xa[0], ya[0], M["lit"], g1)
    tile("ar1_1", xa[1], ya[0], M["lit"], g1)
    tile("bc1_0", xb[0], ya[0], M["cyan"], g1)
    tile("bc1_1", xb[0], ya[1], M["cyan"], g1)
    tile("c00", xc[0], ya[0], M["green"], g1)
    show(g1, beat(1))
    g2 = empty("answer_lit", root)
    for r in range(2):
        for c in range(2):
            tile(f"cl{r}{c}", xc[c], ya[r], M["green"], g2)
    show(g2, beat(2))
    label("A", (-550, 560, 0), root, beat(0))
    label("B", (300, 560, 0), root, beat(0))
    label("C = A x B", (950, 560, 0), root, beat(0))
    label("row 1 . col 1 = 19", (-300, -260, 0), root, beat(1))
    label("C = [19 22 / 43 50]", (950, -470, 0), root, beat(2))
    label("19", (800, 480, 0), root, beat(1))
    label("22", (1100, 480, 0), root, beat(2))
    label("43", (800, -150, 0), root, beat(2))
    label("50", (1100, -150, 0), root, beat(2))
    camera(root, [((250, 150, 0), 3900, 0.0, 0.0)] * 3)
    finish("matrix_matrix", page="math")


PAGES = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
    "vector": vector,
    "vector_add": vector_add,
    "scale": scale,
    "dot_product": dot_product,
    "matrix": matrix,
    "shape_rule": shape_rule,
    "matrix_vector": matrix_vector,
    "matrix_matrix": matrix_matrix,
}


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    names = argv or list(PAGES)
    for name in names:
        PAGES[name]()


if __name__ == "__main__":
    main()
