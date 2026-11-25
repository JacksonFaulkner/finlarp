"""TRM_FREE_CASH_FLOW: operating cash pours into a cut-open cash tank; capex drains out of it to
data-center construction; what is left is free cash flow.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_free_cash_flow.py

Left: a cloud business (a hall of busy racks) whose operating cash flows in a pipe to the tank.
Centre: the tank, cut open at the front, liquid level showing cash on hand, with a level gauge.
Right: a capex pipe to a build site where new halls go up module by module. Front: a bank that lends
when the tank runs dry, and a payout spout (buybacks, dividends).

Beats:
  0 inflow    operating cash flow fills the tank
  1 capex     capex drains to new data centers being built
  2 FCF       what is left after capex is free cash flow
  3 AI surge  capex jumps, the level falls toward zero; debt tops it up
  4 uses      FCF funds buybacks, dividends, debt paydown; tickers
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_FREE_CASH_FLOW"
BEATS = [
    ("Operating cash flow is the cash the business brings in",
     "Operating cash flow is cash collected from customers minus cash paid for staff, suppliers, power and taxes, "
     "adjusted for timing of payments. It is closer to real money than net income because it skips non-cash items "
     "like depreciation and stock pay. For a big cloud company it runs at tens of billions a year."),
    ("Capital expenditure drains it to buildings, servers and chips",
     "Capex is cash spent on long-lived assets: land, data-center shells, power and cooling gear, servers and GPUs. "
     "It does not show up as an expense right away; it is depreciated over years. But the cash leaves now."),
    ("Free cash flow is what is left: operating cash flow minus capex",
     "Free cash flow (FCF) = operating cash flow - capital expenditure. It is the cash the company could hand back to "
     "shareholders, use to pay debt, or keep. Definitions vary a little: some also subtract finance leases, which "
     "matter for data-center deals."),
    ("An AI build-out can push FCF toward zero or below",
     "When capex surges for AI data centers, it can eat most of operating cash flow even while profits rise. If capex "
     "exceeds operating cash, FCF turns negative and the gap is filled with cash reserves, bonds or leases. Investors "
     "watch the gap closely: it is a bet that the new capacity earns back its cost."),
    ("FCF pays for buybacks, dividends and debt; tickers",
     "Healthy FCF funds share buybacks, dividends and debt paydown without borrowing. A falling FCF margin with rising "
     "capex is the trade-off hyperscalers are making now. Related: Microsoft (MSFT), Alphabet (GOOGL), Meta (META), "
     "Oracle (ORCL)."),
]

TX, TZ, TR, TH = 0.0, -40.0, 40.0, 110.0  # tank centre x, z, radius, height
LV = {"full": 92.0, "mid": 60.0, "fcf": 38.0, "low": 9.0}


def mats(m):
    m["ground"] = mat("fc_ground", (0.26, 0.27, 0.29), rough=0.9)
    m["tank"] = mat("fc_tank", (0.62, 0.64, 0.68), metal=0.85, rough=0.35)
    m["cash"] = mat("fc_cash", (0.30, 0.85, 0.40), emit=(0.25, 0.80, 0.35), strength=0.8)
    m["cash_b"] = mat("fc_cashb", (0.55, 1.0, 0.45), emit=(0.5, 1.0, 0.4), strength=4.0)
    m["capex_b"] = mat("fc_capex", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=4.0)
    m["debt_b"] = mat("fc_debt", (1.0, 0.25, 0.15), emit=(1.0, 0.2, 0.1), strength=4.0)
    m["pay_b"] = mat("fc_pay", (0.40, 0.80, 1.0), emit=(0.35, 0.75, 1.0), strength=4.0)
    m["concrete"] = mat("fc_conc", (0.62, 0.61, 0.58), rough=0.85)
    m["rack"] = mat("fc_rack", (0.10, 0.11, 0.13), metal=0.5, rough=0.5)
    m["led"] = mat("fc_led", (0.35, 1.0, 0.55), emit=(0.3, 1.0, 0.5), strength=3.0)
    m["crane"] = mat("fc_crane", (1.0, 0.78, 0.15), metal=0.4, rough=0.45)
    m["bank"] = mat("fc_bank", (0.80, 0.78, 0.72), rough=0.7)


def tank(m, root):
    """The cut-open tank: back half of the wall as staves with hoops, a floor, a level gauge, and
    one liquid cylinder per level (only one shown at a time)."""
    g = empty("tank", root)
    p = [D.tube("t_floor", (TX, 0.0, TZ), (TX, 3.0, TZ), TR + 2.0, m["dark"], g, 48)]
    n = 28
    for k in range(n + 1):
        a = math.pi + math.pi * k / n  # back half
        x, z = TX + TR * math.cos(a), TZ + TR * math.sin(a)
        p.append(D.tube(f"t_st{k}", (x, 3.0, z), (x, TH, z), 2.6, m["tank"], g, 8))
    for k, y in enumerate((20.0, 55.0, 90.0, TH)):
        for j in range(n):
            a0, a1 = math.pi + math.pi * j / n, math.pi + math.pi * (j + 1) / n
            p.append(D.tube(f"t_h{k}_{j}", (TX + (TR + 1.8) * math.cos(a0), y, TZ + (TR + 1.8) * math.sin(a0)),
                            (TX + (TR + 1.8) * math.cos(a1), y, TZ + (TR + 1.8) * math.sin(a1)), 1.0, m["steel"], g, 6))
    # cut edges at the sides, gauge column on the right
    for s in (-1, 1):
        p.append(bx(f"t_cut{s}", (TX + s * TR - 2.0, 3.0, TZ - 1.0), (TX + s * TR + 2.0, TH, TZ + 1.0), m["steel"], g))
    gx = TX + TR + 10.0
    p.append(bx("g_col", (gx - 2.0, 3.0, TZ - 2.0), (gx + 2.0, TH, TZ + 2.0), m["dark"], g))
    for k in range(11):
        y = 3.0 + (TH - 3.0) * k / 10
        p.append(bx(f"g_t{k}", (gx - 4.0, y - 0.4, TZ + 2.0), (gx, y + 0.4, TZ + 2.6), m["ink"], g))
    D.join(p, "tank_m")
    levels = {}
    for name, y in LV.items():
        lg = empty(f"lv_{name}", root)
        D.tube(f"liq_{name}", (TX, 3.0, TZ), (TX, y, TZ), TR - 2.5, m["cash"], lg, 40)
        bx(f"gl_{name}", (gx - 1.4, 3.0, TZ + 2.0), (gx + 1.4, y, TZ + 2.4), m["cash_b"], lg)
        levels[name] = lg
    return levels, gx


def hall(m, root, name, x0, x1, z0, z1, roof=True):
    g = empty(name, root)
    p = [bx(f"{name}_slab", (x0, 0.0, z0), (x1, 2.0, z1), m["concrete"], g),
         bx(f"{name}_back", (x0, 2.0, z0), (x1, 40.0, z0 + 2.0), m["concrete"], g),
         bx(f"{name}_side", (x0, 2.0, z0), (x0 + 2.0, 40.0, z1), m["concrete"], g)]
    rows = []
    leds = empty(f"{name}_leds", root)
    for r in range(3):
        z = z0 + 14.0 + r * (z1 - z0 - 20.0) / 3
        for k in range(int((x1 - x0 - 12.0) / 9.0)):
            x = x0 + 8.0 + k * 9.0
            rows.append(bx(f"{name}_r{r}_{k}", (x, 2.0, z), (x + 8.0, 30.0, z + 10.0), m["rack"], g))
            for j in range(4):
                bx(f"{name}_l{r}_{k}_{j}", (x + 1.0, 6.0 + j * 6.0, z + 10.0), (x + 3.0, 7.0 + j * 6.0, z + 10.4), m["led"], leds)
    D.join(rows, f"{name}_racks")
    D.join(p, f"{name}_shell")
    return g, leds


def site(m, root):
    """The build site on the right: three new halls that go up one by one, a tower crane."""
    g = empty("site", root)
    p = [bx("site_lot", (110.0, 0.0, -130.0), (300.0, 0.6, 30.0), m["ground"], g)]
    # tower crane
    p.append(bx("cr_mast", (282.0, 0.0, -120.0), (288.0, 150.0, -114.0), m["crane"], g))
    for k in range(15):
        y = 10.0 * k
        p.append(D.tube(f"cr_x{k}", (282.0, y, -114.0), (288.0, y + 10.0, -114.0), 0.5, m["crane"], g, 6))
    p.append(bx("cr_jib", (130.0, 150.0, -119.0), (300.0, 156.0, -115.0), m["crane"], g))
    p.append(bx("cr_cw", (292.0, 140.0, -121.0), (304.0, 150.0, -113.0), m["concrete"], g))
    D.join(p, "site_m")
    hook = empty("hook", root)
    D.polyline("cr_cab", [(180.0, 150.0, -117.0), (180.0, 70.0, -117.0)], 0.4, m["steel"], hook)
    bx("cr_load", (172.0, 60.0, -125.0), (188.0, 70.0, -109.0), m["rack"], hook)
    builds = []
    for k, (x0, x1) in enumerate(((120.0, 175.0), (185.0, 240.0), (250.0, 300.0))):
        hg, leds = hall(m, root, f"new{k}", x0, x1, -100.0, 10.0)
        builds.append((hg, leds, ((x0 + x1) / 2, 40.0, -45.0)))
    return builds, hook


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-320.0, -2.0, -170.0), (320.0, 0.0, 120.0), m["ground"], root)
    levels, gx = tank(m, root)
    biz, biz_leds = hall(m, root, "biz", -300.0, -110.0, -110.0, 10.0)
    blink(biz_leds, 0, [0, 2, 4, 6], n=8, on=0.7)
    show(biz_leds, [(F(0, 0), F(5, 0))])
    builds, hook = site(m, root)
    # halls go up one by one during beats 1 and 3
    for k, (hg, leds, _) in enumerate(builds):
        t0 = F(1, 0.25 + 0.25 * k) if k < 2 else F(3, 0.3)
        show(hg, [(t0, F(5, 0))])
        show(leds, [(t0 + 20, F(5, 0))])
    show(hook, [(F(1, 0), F(4, 0))])
    # levels: full by end of beat 0, mid in beat 1, FCF level beat 2, low beat 3, FCF again beat 4
    show(levels["mid"], [(F(0, 0), F(0, 0.5)), (F(1, 0.5), F(2, 0))])
    show(levels["full"], [(F(0, 0.5), F(1, 0.5))])
    show(levels["fcf"], [(F(2, 0), F(3, 0.3)), (F(4, 0), F(5, 0))])
    show(levels["low"], [(F(3, 0.3), F(4, 0))])
    # pipes: inflow from the business at top-left, capex out bottom-right, payout front
    pin = [(-110.0, 30.0, -50.0), (-60.0, 30.0, -50.0), (-60.0, TH + 10.0, -50.0), (TX - 10.0, TH + 10.0, TZ), (TX - 10.0, 60.0, TZ)]
    pout = [(TX + 20.0, 8.0, TZ + 20.0), (TX + 70.0, 8.0, TZ + 20.0), (110.0, 8.0, -45.0), (150.0, 8.0, -45.0)]
    for nm, pts in (("p_in", pin[:-1]), ("p_out", pout)):
        D.polyline(nm, pts, 3.2, m["steel"], root)
    run(root, "ocf", pin, 14, 2.6, m["cash_b"], [0, 1, 2, 3, 4], 0.0, 0.75, 70)
    run(root, "capex", pout, 10, 2.6, m["capex_b"], [1, 2], 0.1, 0.8, 55)
    run(root, "capex2", pout, 22, 3.2, m["capex_b"], [3], 0.0, 0.85, 50)
    # bank in front-left lends during the surge
    bk = [bx("bank", (-120.0, 0.0, 50.0), (-60.0, 30.0, 90.0), m["bank"], root),
          bx("bank_r", (-124.0, 30.0, 46.0), (-56.0, 36.0, 94.0), m["concrete"], root)]
    for k in range(5):
        x = -114.0 + k * 12.0
        bk.append(D.tube(f"col{k}", (x, 0.0, 92.0), (x, 30.0, 92.0), 1.6, m["white"], root, 10))
    D.join(bk, "bank_m")
    run(root, "debt", [(-60.0, 20.0, 70.0), (-20.0, 60.0, 20.0), (TX - 15.0, 30.0, TZ + 20.0)], 8, 2.4, m["debt_b"], [3], 0.35, 0.9, 45)
    # payout spout: buybacks/dividends to shareholders (front right)
    pay = [(TX + 25.0, 30.0, TZ + 25.0), (60.0, 30.0, 40.0), (90.0, 10.0, 70.0)]
    D.polyline("p_pay", pay[:2], 2.6, m["steel"], root)
    hold = []
    for k in range(6):
        x = 80.0 + (k % 3) * 12.0
        z = 62.0 + (k // 3) * 14.0
        hold.append(D.tube(f"sh{k}", (x, 0.0, z), (x, 10.0, z), 3.0, m["dark"], root, 12))
    D.join(hold, "holders")
    run(root, "payout", pay, 10, 2.4, m["pay_b"], [4], 0.1, 0.8, 45)
    rise(root, "busy", (-205.0, 32.0, -50.0), 8, 1.2, m["heat"], [0], 0.0, 0.8, 20.0, 50, (80.0, 40.0))

    C.tags(root, {
        0: [("cloud business earns cash", (-205.0, 40.0, -50.0)), ("operating cash flow in", (-60.0, TH + 10.0, -50.0)),
            ("cash on hand", (TX, LV["full"], TZ))],
        1: [("capex: halls, power, GPUs", builds[0][2]), ("cash leaves now", (TX + 70.0, 10.0, TZ + 20.0)),
            ("expensed later (depreciation)", builds[1][2])],
        2: [("FCF = OCF - capex", (TX, LV["fcf"], TZ)), ("level gauge", (gx, LV["fcf"], TZ + 2.0)),
            ("leases: some subtract too", (TX + 70.0, 10.0, TZ + 20.0))],
        3: [("AI capex surge", builds[2][2]), ("FCF near zero / negative", (TX, LV["low"], TZ)),
            ("bonds + leases fill the gap", (-90.0, 36.0, 70.0))],
        4: [("buybacks + dividends", (95.0, 12.0, 70.0)), ("MSFT GOOGL META ORCL", (-205.0, 40.0, -50.0)),
            ("what is left: FCF", (TX, LV["fcf"], TZ))],
    })
    C.done(SLUG, BEATS, [
        frame((-90.0, 50.0, -40.0), 330.0, 0.25, 0.35, pad=1.0),
        frame((120.0, 60.0, -40.0), 330.0, -0.20, 0.35, pad=1.0),
        frame((TX + 10.0, 55.0, TZ), 140.0, 0.10, 0.20),
        frame((40.0, 50.0, -20.0), 460.0, 0.0, 0.40, pad=1.0),
        frame((20.0, 40.0, 20.0), 300.0, 0.30, 0.40),
    ], root)


if __name__ == "__main__":
    build()
