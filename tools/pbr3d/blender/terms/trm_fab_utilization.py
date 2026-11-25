"""TRM_FAB_UTILIZATION: the Terms-tab overview for fab utilization.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_fab_utilization.py

A fab hall cut open at the front: four rows of process tools (load ports, chamber, lit window),
an overhead track carrying FOUPs, an outbound conveyor of finished wafers, and on the right a cost
board: the fixed-cost tank on the roof that drains depreciation onto every wafer, a cost-per-wafer
bar and a gross-margin bar.

Beats:
  0 fab       the hall running full, wafers rolling out
  1 fixed     depreciation drips from the tank, spread over many wafers; cost bar short
  2 downturn  half the bays go dark, fewer wafers carry the same cost; cost bar tall, margin thin
  3 split     AI leading-edge bays full, mature-node bays idle
  4 who       TSMC, Micron, TI, GlobalFoundries
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_FAB_UTILIZATION"
BEATS = [
    ("Utilization is the share of a fab's capacity that is running",
     "A fab is a hall of process tools (lithography, etch, deposition, clean, metrology) that wafers visit hundreds "
     "of times. Utilization is how many wafer starts it is actually running against what it could run, usually "
     "quoted as a percentage. Full fabs run near 90-100%; in a slump they can drop to 60-70% or lower."),
    ("A fab's costs are mostly fixed, so they are spread over every wafer",
     "A leading-edge fab costs $20B+ to build and is written off over about five years whether it runs or not. "
     "Depreciation, staff and upkeep are fixed; only materials and power scale with output. When the hall is full "
     "those fixed costs spread across many wafers and each one is cheap to make."),
    ("When tools sit idle, each wafer carries more of the fixed cost",
     "If orders fall and half the tools go quiet, the same depreciation lands on half as many wafers, so cost per "
     "wafer jumps and gross margin falls fast. Companies often book the idle part as an underutilization charge. "
     "Memory makers and integrated chip makers call these out in downturns; it is why their margins swing so hard."),
    ("AI keeps leading-edge lines full while mature nodes sit underused",
     "Demand for AI accelerators keeps leading-edge logic, HBM and advanced packaging (CoWoS) lines running flat out, "
     "with pricing power. Older, mature-node fabs that make analog, auto and industrial chips can sit well below "
     "capacity at the same time, so utilization is a per-node story, not one number for the industry."),
    ("Watch utilization to read the margin swing before it reports",
     "Management comments on utilization and loadings are an early read on gross margin. Related: TSMC (TSM), Micron "
     "(MU), Texas Instruments (TXN), GlobalFoundries (GFS). Fabless designers don't carry this cost directly, but feel "
     "it as foundry price changes."),
]

COLS = 6
ROWS = 4
TX = [-125.0 + 50.0 * i for i in range(COLS)]  # tool x centres
TZ = [-30.0 - 40.0 * j for j in range(ROWS)]  # tool z centres
TW, TD, TH = 30.0, 22.0, 36.0
LEAD = {0, 1, 2}  # columns that are leading-edge / AI (stay full in beat 3)
CB = 190.0  # cost board x


def mats(m):
    m["tool"] = mat("fu_tool", (0.82, 0.84, 0.86), metal=0.3, rough=0.4)
    m["tool2"] = mat("fu_tool2", (0.30, 0.45, 0.62), metal=0.4, rough=0.35)
    m["floor"] = mat("fu_floor", (0.52, 0.55, 0.58), metal=0.2, rough=0.5)
    m["win"] = mat("fu_win", (0.45, 0.80, 1.0), emit=(0.40, 0.75, 1.0), strength=3.0)
    m["idle"] = mat("fu_idle", (0.10, 0.11, 0.13), rough=0.4)
    m["foup"] = mat("fu_foup", (0.95, 0.60, 0.20), rough=0.5)
    m["cost"] = mat("fu_cost", (1.0, 0.30, 0.20), emit=(1.0, 0.25, 0.15), strength=3.0)
    m["margin"] = mat("fu_margin", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=2.5)
    m["wfr"] = mat("fu_wfr", (0.45, 0.47, 0.60), metal=0.8, rough=0.15)


def tool(m, root, name, x, z, mt):
    g = empty(name, root)
    x0, x1, z0, z1 = x - TW / 2, x + TW / 2, z - TD / 2, z + TD / 2
    bx(f"{name}_b", (x0, 0.0, z0), (x1, TH, z1 - 4.0), m[mt], g)
    bx(f"{name}_top", (x0 + 3.0, TH, z0 + 3.0), (x1 - 3.0, TH + 5.0, z1 - 8.0), m["alu"], g)
    for p in range(3):  # load ports with FOUPs
        px = x0 + 4.0 + 8.0 * p
        bx(f"{name}_lp{p}", (px, 0.0, z1 - 4.0), (px + 6.0, 12.0, z1), m["dark"], g)
        bx(f"{name}_fp{p}", (px + 0.5, 12.0, z1 - 3.5), (px + 5.5, 17.0, z1 - 0.5), m["foup"], g)
    bx(f"{name}_scr", (x1 - 9.0, 20.0, z1 - 4.0), (x1 - 2.0, 28.0, z1 - 3.8), m["screen"], g)
    D.tube(f"{name}_ch", (x - 4.0, TH - 14.0, z1 - 4.0), (x - 4.0, TH - 14.0, z1 - 3.6), 7.0, m["dark"], g, 24)
    lit = empty(f"{name}_lit", root)
    D.tube(f"{name}_w", (x - 4.0, TH - 14.0, z1 - 3.6), (x - 4.0, TH - 14.0, z1 - 3.3), 5.0, m["win"], lit, 24)
    bx(f"{name}_led", (x1 - 8.0, 30.0, z1 - 3.9), (x1 - 3.0, 32.0, z1 - 3.6), m["sig"], lit)
    dark = empty(f"{name}_dark", root)
    D.tube(f"{name}_wd", (x - 4.0, TH - 14.0, z1 - 3.6), (x - 4.0, TH - 14.0, z1 - 3.3), 5.0, m["idle"], dark, 24)
    bx(f"{name}_ledd", (x1 - 8.0, 30.0, z1 - 3.9), (x1 - 3.0, 32.0, z1 - 3.6), m["warn"], dark)
    return lit, dark


def bar(m, root, name, x, z, h, mt):
    g = empty(name, root)
    bx(f"{name}_f", (x - 5.0, 0.0, z - 3.0), (x + 5.0, h, z + 3.0), m[mt], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-160.0, -3.0, -190.0), (225.0, 0.0, 20.0), m["floor"], root)
    raised = []
    for i in range(38):
        raised.append(bx(f"fl_l{i}", (-160.0 + 10.0 * i, 0.0, -190.0), (-159.6 + 10.0 * i, 0.08, 20.0), m["grid"], root))
    D.join(raised, "floor_grid")
    bx("wall", (-160.0, 0.0, -195.0), (160.0, 80.0, -190.0), m["tool"], root)
    lits, darks = {}, {}
    for i, x in enumerate(TX):
        for j, z in enumerate(TZ):
            lits[(i, j)], darks[(i, j)] = tool(m, root, f"t{i}{j}", x, z, "tool2" if i in LEAD else "tool")
    # overhead hoist track over each row
    for j, z in enumerate(TZ):
        D.tube(f"ohs{j}", (-150.0, 58.0, z + TD / 2 - 2.0), (150.0, 58.0, z + TD / 2 - 2.0), 1.0, m["alu"], root, 8)
        for i in range(7):
            D.tube(f"ohs_h{j}{i}", (-150.0 + 50.0 * i, 58.0, z + TD / 2 - 2.0), (-150.0 + 50.0 * i, 80.0, z + TD / 2 - 2.0), 0.4, m["alu"], root, 6)
    # outbound conveyor at the front
    bx("conv", (-150.0, 6.0, 4.0), (175.0, 8.0, 14.0), m["dark"], root)
    for i in range(30):
        D.tube(f"roll{i}", (-148.0 + 11.0 * i, 8.0, 4.0), (-148.0 + 11.0 * i, 8.0, 14.0), 0.8, m["alu"], root, 8)
    # fixed-cost tank on the roof, cost board on the right
    D.tube("tank", (CB, 70.0, -60.0), (CB, 100.0, -60.0), 16.0, m["steel"], root, 32)
    D.tube("tank_lid", (CB, 100.0, -60.0), (CB, 101.0, -60.0), 17.0, m["dark"], root, 32)
    D.polyline("tank_pipe", [(CB, 70.0, -60.0), (CB, 50.0, -60.0), (CB - 30.0, 30.0, 9.0)], 1.2, m["steel"], root)
    bx("board", (CB - 22.0, 0.0, -10.0), (CB + 22.0, 60.0, -8.0), m["gauge"] if "gauge" in m else m["dark"], root)
    for k in range(6):
        bx(f"board_t{k}", (CB - 22.0, 8.0 * k + 4.0, -8.0), (CB + 22.0, 8.0 * k + 4.3, -7.7), m["ink"], root)
    c_lo = bar(m, root, "c_lo", CB - 10.0, -4.0, 12.0, "cost")
    c_hi = bar(m, root, "c_hi", CB - 10.0, -4.0, 40.0, "cost")
    m_hi = bar(m, root, "m_hi", CB + 10.0, -4.0, 44.0, "margin")
    m_lo = bar(m, root, "m_lo", CB + 10.0, -4.0, 14.0, "margin")
    m_mid = bar(m, root, "m_mid", CB + 10.0, -4.0, 30.0, "margin")

    full = [(F(0, 0), F(2, 0.3)), (F(4, 0), F(5, 0))]
    for (i, j), g in lits.items():
        if i in LEAD:
            show(g, full + [(F(2, 0.3), F(4, 0))]) if (i + j) % 2 == 0 else show(g, full + [(F(3, 0), F(4, 0))])
            show(darks[(i, j)], [] if (i + j) % 2 == 0 else [(F(2, 0.3), F(3, 0))])
        else:
            show(g, full + ([(F(2, 0.3), F(3, 0))] if (i + j) % 2 == 0 else []))
            show(darks[(i, j)], ([] if (i + j) % 2 == 0 else [(F(2, 0.3), F(3, 0))]) + [(F(3, 0), F(4, 0))])
    show(c_lo, [(F(1, 0.2), F(2, 0.4)), (F(4, 0), F(5, 0))])
    show(c_hi, [(F(2, 0.4), F(3, 0))])
    show(m_hi, [(F(1, 0.2), F(2, 0.4))])
    show(m_lo, [(F(2, 0.4), F(3, 0))])
    show(m_mid, [(F(3, 0), F(5, 0))])

    # FOUPs hop between tools along the hoist tracks
    for j, z in enumerate(TZ):
        zz = z + TD / 2 - 2.0
        run(root, f"foup{j}", [(-150.0, 56.0, zz), (150.0, 56.0, zz)], 8, 2.2, m["v12"], [0, 1, 4], 0.0, 0.8, 90)
        run(root, f"foupd{j}", [(-150.0, 56.0, zz), (150.0, 56.0, zz)], 3, 2.2, m["v12"], [2, 3], 0.0, 0.8, 90)
    # wafers out on the conveyor: many when full, few when not
    run(root, "out_full", [(-150.0, 10.0, 9.0), (170.0, 10.0, 9.0)], 12, 2.4, m["wfr"], [0, 1, 4], 0.0, 0.85, 80)
    run(root, "out_few", [(-150.0, 10.0, 9.0), (170.0, 10.0, 9.0)], 4, 2.4, m["wfr"], [2, 3], 0.0, 0.85, 80)
    # depreciation drips from the tank onto the passing wafers
    run(root, "dep", [(CB, 70.0, -60.0), (CB, 50.0, -60.0), (CB - 30.0, 30.0, 9.0), (CB - 30.0, 12.0, 9.0)], 10, 1.2, m["cost"], [1, 2], 0.05, 0.9, 40)
    rise(root, "heat", (-60.0, TH + 5.0, -80.0), 10, 1.0, m["heat"], [0, 3], 0.0, 0.9, 20.0, 50, (60.0, 50.0))

    C.tags(root, {
        0: [("process tools, row on row", (TX[1], TH + 5.0, TZ[0])), ("overhead FOUP track", (TX[4], 58.0, TZ[1])),
            ("finished wafers out", (120.0, 10.0, 9.0))],
        1: [("fixed cost: depreciation", (CB, 101.0, -60.0)), ("cost per wafer: low", (CB - 10.0, 12.0, -4.0)),
            ("gross margin: high", (CB + 10.0, 44.0, -4.0))],
        2: [("half the tools idle", (TX[3], TH, TZ[0])), ("cost per wafer: jumps", (CB - 10.0, 40.0, -4.0)),
            ("margin: thin", (CB + 10.0, 14.0, -4.0))],
        3: [("leading edge / AI: full", (TX[1], TH + 5.0, TZ[0])), ("mature nodes: idle", (TX[4], TH + 5.0, TZ[0]))],
        4: [("TSMC, Micron", (TX[1], TH + 5.0, TZ[0])), ("TI, GlobalFoundries", (TX[4], TH + 5.0, TZ[0])),
            ("loadings lead margins", (CB, 60.0, -8.0))],
    })
    C.done(SLUG, BEATS, [
        frame((30.0, 20.0, -80.0), 360.0, 0.30, 0.50, pad=1.0),
        frame((CB - 40.0, 40.0, -30.0), 140.0, -0.35, 0.25),
        frame((40.0, 20.0, -60.0), 320.0, 0.15, 0.40, pad=1.0),
        frame((0.0, 20.0, -60.0), 300.0, 0.0, 0.45, pad=1.0),
        frame((30.0, 20.0, -80.0), 360.0, -0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
