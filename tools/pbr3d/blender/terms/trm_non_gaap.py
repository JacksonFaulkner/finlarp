"""TRM_NON_GAAP: the Terms-tab overview for non-GAAP earnings, at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_non_gaap.py

An accounting idea, so the scene is its own: a quarter's income statement built as a 3D waterfall
on a plinth. Revenue is a tall tower filled with cash; cost blocks step it down (cost of revenue,
R&D and SG&A, then stock-based compensation as a stack of share coins, amortization of acquired
intangibles, restructuring) to a short GAAP profit bar. Then the three add-back blocks lift off and
re-stack on top of GAAP profit to build the taller non-GAAP bar. Behind, a share pile grows with
every grant and a lit reconciliation table stands on the back wall.

Beats:
  0 gaap      revenue minus every cost: the GAAP profit bar
  1 addbacks  the items the company calls non-recurring or non-cash light up
  2 bridge    the add-back blocks fly onto GAAP profit: the non-GAAP bar
  3 sbc       stock pay is still a cost: the share count grows, buybacks spend cash
  4 recon     the SEC requires a reconciliation table next to every non-GAAP number
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, P, empty, key, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_NON_GAAP"
BEATS = [
    ("GAAP profit is revenue minus every cost, by the rulebook",
     "US companies report results under GAAP, the standard accounting rules. Start from revenue, take away the cost "
     "of the products sold, research and development, sales and admin, stock paid to staff, amortization of bought "
     "companies and one-off charges, and what is left is GAAP operating profit. Every company follows the same rules, "
     "so GAAP numbers compare cleanly across firms."),
    ("Management flags some costs as non-cash or one-off",
     "Companies argue a few lines do not reflect how the business runs day to day. The usual three: stock-based "
     "compensation (staff paid in shares, no cash leaves), amortization of intangibles bought in acquisitions "
     "(an accounting write-down of a past deal), and restructuring such as layoffs or plant closures. Each company "
     "picks its own list."),
    ("Add them back and you get the bigger non-GAAP number",
     "Non-GAAP profit is GAAP profit with those items added back. For a chip firm that bought big companies the gap "
     "is large: Broadcom's non-GAAP operating margin runs far above its GAAP margin because of VMware and earlier "
     "deal amortization plus billions in stock pay. Analyst estimates and 'beats' are usually quoted on the non-GAAP "
     "figure."),
    ("Stock pay is still a real cost to shareholders",
     "Paying staff in shares spends no cash, but every grant adds shares and dilutes existing owners. Many firms "
     "then spend cash on buybacks just to hold the share count flat, so the cost shows up anyway. For AI hardware and "
     "neocloud names stock comp is often the single largest add-back, which is why some investors stick to GAAP or "
     "subtract it themselves."),
    ("The SEC requires a reconciliation beside every non-GAAP figure",
     "Under Regulation G and Item 10(e), a company that publishes a non-GAAP measure must show the closest GAAP "
     "measure with equal prominence and a line-by-line table bridging the two. Read the table: if the add-backs grow "
     "every year, they are not one-off. Related: NVIDIA (NVDA), Broadcom (AVGO), Marvell (MRVL), CoreWeave (CRWV)."),
]

W = 20.0  # bar width (x) and depth (z)
Z0, Z1 = -W, 0.0
REV = 120.0
# the waterfall steps: (name, x centre, y top, y bottom, material, add-back?)
STEPS = [
    ("cogs", -90.0, 120.0, 70.0, "cost", False),
    ("opex", -64.0, 70.0, 46.0, "cost2", False),
    ("sbc", -38.0, 46.0, 32.0, "sbcm", True),
    ("amort", -12.0, 32.0, 24.0, "amortm", True),
    ("restr", 14.0, 24.0, 20.0, "restrm", True),
]
GAAP_X, GAAP_TOP = 40.0, 20.0
NG_X = 118.0
BRIDGE_X = {"sbc": 66.0, "amort": 84.0, "restr": 100.0}


def mats(m):
    m["plinth"] = mat("ng_plinth", (0.16, 0.17, 0.20), metal=0.3, rough=0.5)
    m["floor"] = mat("ng_floor", (0.42, 0.44, 0.48), rough=0.7)
    m["glassbar"] = mat("ng_glass", (0.55, 0.75, 0.70), metal=0.2, rough=0.12)
    m["cash"] = mat("ng_cash", (0.35, 0.95, 0.55), emit=(0.30, 0.90, 0.50), strength=2.5)
    m["cost"] = mat("ng_cost", (0.55, 0.32, 0.30), rough=0.55)
    m["cost2"] = mat("ng_cost2", (0.62, 0.42, 0.32), rough=0.55)
    m["sbcm"] = mat("ng_sbc", (0.85, 0.68, 0.25), metal=0.85, rough=0.3)
    m["amortm"] = mat("ng_amort", (0.45, 0.38, 0.70), rough=0.45)
    m["restrm"] = mat("ng_restr", (0.75, 0.28, 0.32), rough=0.5)
    m["gaap"] = mat("ng_gaap", (0.25, 0.55, 0.85), rough=0.4)
    m["ngm"] = mat("ng_ng", (0.30, 0.80, 0.60), rough=0.4)
    m["flag"] = mat("ng_flag", (1.0, 0.80, 0.30), emit=(1.0, 0.75, 0.25), strength=3.0)
    m["money"] = mat("ng_money", (1.0, 0.85, 0.30), emit=(1.0, 0.80, 0.25), strength=3.5)
    m["row"] = mat("ng_row", (0.85, 0.90, 1.0), emit=(0.80, 0.88, 1.0), strength=2.0)
    m["share"] = mat("ng_share", (0.92, 0.92, 0.88), rough=0.5)
    m["paper"] = mat("ng_paper", (0.93, 0.92, 0.86), rough=0.8)


def coin_stack(m, parent, name, x, y0, y1, z, r=3.6, step=1.2):
    parts = []
    k = 0
    y = y0
    while y + step <= y1 + 0.01:
        parts.append(D.tube(f"{name}{k}", (x, y, z), (x, y + step * 0.82, z), r, m["sbcm"], parent, 16))
        y += step
        k += 1
    return D.join(parts, name)


def block(m, root, name, xc, yb, yt, mt):
    """One cost block: a frame of edges round a solid, with the item's own detail."""
    g = empty(name, root)
    x0, x1 = xc - W / 2, xc + W / 2
    if name == "sbc":  # a 3x2 grid of share-coin stacks with a certificate face
        for i in range(3):
            for j in range(2):
                coin_stack(m, g, f"sbc_c{i}{j}", x0 + 3.6 + i * 6.4, yb, yt, Z0 + 5.0 + j * 9.0)
        bx("sbc_cert", (x0 + 1.0, yb + 1.0, -0.6), (x1 - 1.0, yt - 1.0, 0.0), m["paper"], g)
        bx("sbc_seal", (x1 - 6.0, yb + 2.0, 0.0), (x1 - 2.0, yb + 6.0, 0.3), m["sbcm"], g)
    elif name == "amort":  # a little acquired company: a building being written down
        bx("am_slab", (x0, yb, Z0), (x1, yt, Z1), m[mt], g)
        for k in range(4):
            bx(f"am_win{k}", (x0 + 2.0 + k * 4.5, yb + 2.0, 0.0), (x0 + 5.0 + k * 4.5, yt - 2.0, 0.3), m["glassbar"], g)
    else:
        bx(f"{name}_slab", (x0, yb, Z0), (x1, yt, Z1), m[mt], g)
        for k in range(int((yt - yb) // 6)):  # stacked invoice sheets on the face
            y = yb + 1.5 + k * 6.0
            bx(f"{name}_sh{k}", (x0 + 2.0, y, 0.0), (x1 - 2.0, y + 3.5, 0.25), m["paper"], g)
    for sx in (x0, x1 - 0.6):  # edge posts
        for sz in (Z0, Z1 - 0.6):
            bx(f"{name}_e{sx:.0f}{sz:.0f}", (sx, yb, sz), (sx + 0.6, yt, sz + 0.6), m["dark"], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-190.0, -4.0, -120.0), (190.0, -3.0, 50.0), m["floor"], root)
    bx("plinth", (-112.0, -3.0, Z0 - 6.0), (132.0, 0.0, 8.0), m["plinth"], root)
    # back wall with the reconciliation table
    bx("wall", (-140.0, -3.0, -84.0), (150.0, 150.0, -80.0), m["dark"], root)

    # revenue: a glass tower filled with stacked cash
    rx = -116.0
    bx("rev_glass_back", (rx - W / 2, 0.0, Z0), (rx + W / 2, REV, Z0 + 0.6), m["glassbar"], root)
    for k in range(int(REV // 4)):
        bx(f"rev_bill{k}", (rx - W / 2 + 1.0, k * 4.0 + 0.3, Z0 + 1.0), (rx + W / 2 - 1.0, k * 4.0 + 3.4, Z1 - 1.0), m["cash"] if k % 5 == 0 else m["gaap"], root)
    for sx in (rx - W / 2, rx + W / 2 - 0.6):
        for sz in (Z0, Z1 - 0.6):
            bx(f"rev_e{sx:.0f}{sz:.0f}", (sx, 0.0, sz), (sx + 0.6, REV, sz + 0.6), m["alu"], root)
    bx("rev_cap", (rx - W / 2, REV, Z0), (rx + W / 2, REV + 1.0, Z1), m["alu"], root)

    groups = {}
    prev_top = REV
    for name, xc, yt, yb, mt, _ in STEPS:
        groups[name] = block(m, root, name, xc, yb, yt, mt)
        # connector line from the previous bar's level
        D.polyline(f"lvl_{name}", [(xc - W / 2 - 6.0, prev_top, 1.0), (xc - W / 2, prev_top, 1.0)], 0.3, m["ink"], root)
        prev_top = yb
    D.polyline("lvl_gaap", [(GAAP_X - W / 2 - 6.0, GAAP_TOP, 1.0), (GAAP_X - W / 2, GAAP_TOP, 1.0)], 0.3, m["ink"], root)
    bx("gaap_bar", (GAAP_X - W / 2, 0.0, Z0), (GAAP_X + W / 2, GAAP_TOP, Z1), m["gaap"], root)
    for k in range(5):
        bx(f"gaap_cash{k}", (GAAP_X - W / 2 + 1.0, k * 4.0 + 0.3, 0.0), (GAAP_X + W / 2 - 1.0, k * 4.0 + 3.0, 0.3), m["cash"], root)

    # beat 0: cash leaks from the revenue tower down each step
    lvl = REV
    for name, xc, yt, yb, mt, _ in STEPS:
        run(root, f"leak_{name}", [(rx + W / 2, lvl - 2.0, 2.0), (xc, lvl - 2.0, 2.0), (xc, yb + 2.0, 2.0)], 4, 1.2, m["cash"], 0, 0.05, 0.6, 40)
        lvl = yb
    run(root, "leak_gaap", [(rx + W / 2, 6.0, 4.0), (GAAP_X, 6.0, 4.0), (GAAP_X, GAAP_TOP, 4.0)], 6, 1.4, m["cash"], 0, 0.2, 0.8, 50)

    # beat 1: flags hover over the three add-backs
    flags = empty("flags", root)
    for name, xc, yt, yb, mt, ab in STEPS:
        if ab:
            D.tube(f"flag_pole_{name}", (xc, yt, -2.0), (xc, yt + 14.0, -2.0), 0.35, m["alu"], flags, 8)
            bx(f"flag_{name}", (xc, yt + 9.0, -2.2), (xc + 8.0, yt + 14.0, -1.8), m["flag"], flags)
            bx(f"halo_{name}", (xc - W / 2 - 0.8, yb - 0.8, 0.3), (xc + W / 2 + 0.8, yb, 0.8), m["flag"], flags)
            bx(f"halo2_{name}", (xc - W / 2 - 0.8, yt, 0.3), (xc + W / 2 + 0.8, yt + 0.8, 0.8), m["flag"], flags)
    show(flags, [(F(1, 0.15), F(2, 0.3))])

    # beat 2: the add-backs lift and re-stack on GAAP profit
    top = GAAP_TOP
    dest = {}
    for name, xc, yt, yb, mt, ab in STEPS:
        if not ab:
            continue
        h = yt - yb
        g = groups[name]
        dx, dy = BRIDGE_X[name] - xc, top - yb
        dest[name] = (BRIDGE_X[name], top + h, 0.0)
        key(g, 0, "location", P(0, 0, 0))
        key(g, F(2, 0.1), "location", P(0, 0, 0))
        key(g, F(2, 0.18), "location", P(0, 30.0, 18.0))
        key(g, F(2, 0.3), "location", P(dx, dy + 20.0, 18.0))
        key(g, F(2, 0.4), "location", P(dx, dy, 0))
        D.polyline(f"lvl_b_{name}", [(BRIDGE_X[name] - W / 2 - 6.0 + (2.0 if name == "sbc" else 0.0), top, 1.0), (BRIDGE_X[name] - W / 2, top, 1.0)], 0.3, m["ink"], root)
        top += h
    ng_top = top
    ng = empty("ng_bar", root)
    bx("ng_slab", (NG_X - W / 2, 0.0, Z0), (NG_X + W / 2, ng_top, Z1), m["ngm"], ng)
    for k in range(int(ng_top // 4)):
        bx(f"ng_cash{k}", (NG_X - W / 2 + 1.0, k * 4.0 + 0.3, 0.0), (NG_X + W / 2 - 1.0, k * 4.0 + 3.0, 0.3), m["cash"], ng)
    D.polyline("lvl_ng", [(BRIDGE_X["restr"] + W / 2, ng_top, 1.0), (NG_X - W / 2, ng_top, 1.0)], 0.3, m["ink"], root)
    show(ng, [(F(2, 0.42), F(5, 0))])
    run(root, "ng_fill", [(BRIDGE_X["restr"], ng_top + 2.0, 3.0), (NG_X, ng_top + 2.0, 3.0), (NG_X, 2.0, 3.0)], 6, 1.4, m["cash"], 2, 0.42, 0.9, 30)

    # beat 3: the share pile behind grows with every grant; buybacks spend cash to shrink it
    pile = []
    for k in range(40):
        i, j, lay = k % 8, (k // 8) % 2, k // 16
        e = empty(f"share{k}", root)
        x = -60.0 + i * 7.0
        bx(f"share{k}_s", (x, lay * 6.0, -62.0 + j * 7.0), (x + 6.0, lay * 6.0 + 5.4, -56.0 + j * 7.0), m["share"], e)
        bx(f"share{k}_t", (x + 1.0, lay * 6.0 + 5.4, -61.0 + j * 7.0), (x + 5.0, lay * 6.0 + 5.6, -57.0 + j * 7.0), m["sbcm"], e)
        pile.append(e)
    for k, e in enumerate(pile):
        if k < 24:
            show(e, [(0, F(5, 0))])
        else:  # new grants appear one by one in beat 3
            show(e, [(F(3, 0.05 + 0.5 * (k - 24) / 16), F(5, 0))])
    run(root, "grant", [(-38.0, 46.0, -10.0), (-38.0, 40.0, -40.0), (-20.0, 20.0, -58.0)], 8, 1.4, m["flag"], 3, 0.0, 0.6, 40)
    # cash vault on the right of the pile, buyback beads out of it
    bx("vault", (10.0, 0.0, -70.0), (40.0, 26.0, -46.0), m["steel"], root)
    D.tube("vault_door", (25.0, 13.0, -45.8), (25.0, 13.0, -45.0), 9.0, m["dark"], root, 24)
    D.tube("vault_hub", (25.0, 13.0, -45.0), (25.0, 13.0, -44.0), 2.0, m["alu"], root, 12)
    for k in range(4):
        D.tube(f"vault_spoke{k}", (25.0, 13.0, -44.5), (25.0 + 7.0 * (1 if k % 2 == 0 else 0) * (1 if k < 2 else -1), 13.0 + 7.0 * (0 if k % 2 == 0 else 1) * (1 if k < 2 else -1), -44.5), 0.5, m["alu"], root, 6)
    run(root, "buyback", [(10.0, 20.0, -58.0), (0.0, 30.0, -58.0), (-20.0, 18.0, -58.0)], 8, 1.6, m["money"], 3, 0.45, 0.95, 40)

    # beat 4: reconciliation table on the back wall: GAAP row, three add-back rows, non-GAAP row
    table = empty("table", root)
    bx("tbl_panel", (-40.0, 70.0, -80.0), (90.0, 140.0, -79.0), m["screen"], root)
    rows = [("gaap", 130.0), ("sbcm", 120.0), ("amortm", 110.0), ("restrm", 100.0), ("ngm", 86.0)]
    for k, (mt, y) in enumerate(rows):
        bx(f"tbl_lbl{k}", (-34.0, y, -79.0), (10.0, y + 4.0, -78.5), m["row"], table)
        bx(f"tbl_chip{k}", (-38.0, y, -79.0), (-35.5, y + 4.0, -78.4), m[mt], table)
        bx(f"tbl_num{k}", (60.0, y, -79.0), (84.0, y + 4.0, -78.5), m["row"], table)
        for d in range(5):
            bx(f"tbl_dot{k}{d}", (14.0 + d * 8.0, y + 1.6, -79.0), (16.0 + d * 8.0, y + 2.4, -78.6), m["ink"], table)
    bx("tbl_rule", (-34.0, 94.0, -79.0), (84.0, 94.6, -78.5), m["row"], table)
    show(table, [(F(4, 0.1), F(5, 0))])
    # tracer from each bar to its row
    run(root, "tr_gaap", [(GAAP_X, GAAP_TOP + 2.0, Z0), (GAAP_X, 132.0, -78.0), (60.0, 132.0, -78.0)], 3, 1.0, m["row"], 4, 0.15, 0.4, 30)
    run(root, "tr_ng", [(NG_X, ng_top + 2.0, Z0), (NG_X, 88.0, -78.0), (84.0, 88.0, -78.0)], 3, 1.0, m["row"], 4, 0.35, 0.6, 30)
    rise(root, "glow_ng", (NG_X, ng_top + 1.0, -10.0), 5, 0.9, m["cash"], [2, 4], 0.75, 0.95, 16.0, 30, (6.0, 6.0))

    xg, xn = GAAP_X, NG_X
    tags = {
        0: [("revenue", (rx, REV + 1.0, -10.0)), ("cost of revenue", (-90.0, 120.0, -10.0)),
            ("R&D + SG&A", (-64.0, 70.0, -10.0)), ("GAAP operating profit", (xg, GAAP_TOP, -10.0))],
        1: [("stock-based comp", (-38.0, 60.0, -2.0)), ("acquired intangibles", (-12.0, 46.0, -2.0)),
            ("restructuring", (14.0, 38.0, -2.0))],
        2: [("add-backs re-stacked", (BRIDGE_X["amort"], dest["amort"][1], -10.0)), ("GAAP profit", (xg, GAAP_TOP, -10.0)),
            ("non-GAAP profit", (xn, ng_top, -10.0))],
        3: [("new shares from grants", (-30.0, 18.0, -55.0)), ("buybacks spend cash", (25.0, 26.0, -58.0)),
            ("dilution is the cost", (-60.0, 12.0, -62.0))],
        4: [("reconciliation table", (25.0, 140.0, -79.0)), ("GAAP shown equally", (xg, GAAP_TOP, -10.0)),
            ("NVDA AVGO MRVL CRWV", (xn, ng_top, -10.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-40.0, 55.0, -20.0), 200.0, 0.10, 0.25),
        frame((-10.0, 38.0, -10.0), 150.0, -0.10, 0.20),
        frame((80.0, 30.0, -10.0), 170.0, 0.0, 0.18),
        frame((-10.0, 25.0, -50.0), 130.0, 0.55, 0.45),
        frame((40.0, 75.0, -50.0), 210.0, 0.05, 0.18),
    ], root)


if __name__ == "__main__":
    build()
