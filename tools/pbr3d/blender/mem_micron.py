"""Custom 3D scenes for the Micron (MU) memory R&D page: one scene per tab, each explaining why
that tab matters, exported to assets/mem/micron_<tab>.glb (py/derive/memory_page.py picks them up).

Run from the repo root (all tabs, or the tab ids after `--`):

    blender -b --factory-startup --python tools/pbr3d/blender/mem_micron.py [-- hbm capex]

Every scene is 3 beats of 8 s (frames 0..576), framed for the wide (~3:1) slot. Units are mm, Y up,
the camera on +z (docs/diagram-pages.md). Every figure drawn (bar heights, tags) comes from
data/memory_facts/mu.jsonl, mkt-share.jsonl or the cached page (`derive/memory_page.py MU --json`);
the source sits next to each number below. Micron fiscal quarters are named by the calendar
quarter they end in (FQ4 FY26 = 2026Q3), as on the page.
"""

import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sand_overview as O  # noqa: E402
from sand_overview import OFF, F, P, ball, box, disc, empty, fly, key, label, mat, pivot, show  # noqa: E402
from sand_zooms import camera, scale_keys, start  # noqa: E402

SLUG = "micron"
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "assets", "mem"))
BEATS = 3
END = F(BEATS, 0)

ROOT = None
TAGS = []  # (text, intervals) of the scene being built, checked before export


# ---- kit --------------------------------------------------------------------------------


def mats(m):
    """Scene colours, named with the slug so the material cache never hands back another page's."""
    def mk(name, c, **kw):
        m[name] = mat(f"mu_{name}", c, **kw)

    mk("dram", (0.12, 0.32, 0.85), rough=0.4)
    mk("nand", (0.12, 0.62, 0.30), rough=0.45)
    mk("other", (0.55, 0.57, 0.62), rough=0.6)
    mk("gold", (0.78, 0.40, 0.03), metal=0.25, rough=0.4, emit=(1.0, 0.55, 0.1), strength=0.15)
    mk("gold_hot", (0.96, 0.72, 0.28), emit=(1.0, 0.72, 0.3), strength=1.6)
    mk("red", (0.80, 0.12, 0.12), rough=0.45, emit=(0.9, 0.15, 0.12), strength=0.25)
    mk("cost", (0.22, 0.23, 0.27), rough=0.7)
    mk("ghost", (0.65, 0.78, 1.0), rough=0.2, alpha=0.3)
    mk("ghost_gold", (1.0, 0.8, 0.4), rough=0.2, alpha=0.3)
    mk("floor", (0.06, 0.065, 0.08), rough=0.85)
    mk("line", (0.75, 0.77, 0.82), rough=0.5)
    mk("steel", (0.50, 0.53, 0.58), metal=0.7, rough=0.35)
    mk("cyan", (0.05, 0.55, 0.85), rough=0.35, emit=(0.1, 0.6, 1.0), strength=0.3)
    mk("purple", (0.62, 0.38, 0.92), rough=0.4)
    mk("orange", (0.95, 0.50, 0.18), rough=0.45)
    mk("slate", (0.40, 0.48, 0.62), rough=0.5)
    mk("muted1", (0.48, 0.42, 0.36), rough=0.7)
    mk("muted2", (0.36, 0.44, 0.40), rough=0.7)
    mk("muted3", (0.42, 0.40, 0.50), rough=0.7)
    mk("muted4", (0.50, 0.46, 0.34), rough=0.7)
    mk("paper", (0.90, 0.88, 0.82), rough=0.85)
    mk("paper2", (0.80, 0.84, 0.92), rough=0.85)
    mk("land", (0.09, 0.12, 0.12), rough=0.9)
    mk("sea", (0.04, 0.05, 0.08), rough=0.6)
    mk("glow", (0.4, 0.95, 1.0), emit=(0.35, 0.9, 1.0), strength=3.0)
    mk("wafer", (0.72, 0.74, 0.80), metal=0.8, rough=0.25)
    return m


def tag(text, at, intervals, parent=None):
    assert len(text) <= 32, text
    TAGS.append((text, intervals))
    return label(text, at, parent or ROOT, intervals)


def bar(parent, name, x, w, d, h, m, y0=0.0, z0=0.0):
    """A pivot at (x, y0, z0) holding a box x +- w/2, y0..y0+h (h may be negative), z0-d..z0. Key the
    pivot's scale (1, 1, v) to grow it."""
    pv = pivot(name, (x, y0, z0), parent or ROOT)
    box(f"{name}_m", (-w / 2, min(0.0, h), -d), (w / 2, max(0.0, h), 0.0), m, pv)
    return pv


def cyl(parent, name, x, r, h, m, y0=0.0, z=0.0, verts=48):
    """A standing cylinder of height h on (x, y0, z), in a pivot at its foot."""
    pv = pivot(name, (x, y0, z), parent or ROOT)
    disc(f"{name}_m", (0, h / 2, 0), r, h, m, pv, verts)
    return pv


def heights(pv, keys, pop=True):
    """Height keys [(frame, fraction of the built height)]. With `pop`, hidden before the first key."""
    ks = []
    f0 = keys[0][0]
    if pop and f0 > 0:
        ks.append((0, (OFF, OFF, OFF)))
    for f, v in keys:
        ks.append((f, (1, 1, max(v, OFF))))
    scale_keys(pv, ks, until=f0 if pop and f0 > 0 else None)


def group(name, intervals=None, parent=None):
    g = empty(name, parent or ROOT)
    if intervals is not None:
        show(g, intervals)
    return g


def floor(x0, x1, z0=-700.0, z1=60.0, y=0.0, m="floor"):
    box("floor", (x0, y - 30, z0), (x1, y, z1), M[m], ROOT)


def move(obj, keys):
    """Location keys [(frame, (x, y, z) offset)], linear between keys."""
    for f, off in keys:
        key(obj, f, "location", P(*off), linear=True)


M = {}


# ---- snapshot: a year that multiplied revenue while cost stood still ---------------------
# Revenue FQ4 FY25 $11.315B, gross profit $5.054B (44.7%); FQ4 FY26 $54.229B, gross profit
# $47.047B (86.8%) (SEC XBRL / 8-K via page revenue tab). FQ1 FY27 guide $61.5B and RPO $150B
# (FQ4 FY26 release and prepared remarks).


def snapshot():
    k = 16.0  # mm per $B
    floor(-2300, 2300)
    W, D = 620.0, 360.0
    xs = (-1350.0, 0.0, 1350.0)
    rev = (11.315, 54.229)
    gp = (5.054, 47.047)
    for i, (r, g) in enumerate(zip(rev, gp)):
        x = xs[i]
        # beat 0: the plain revenue tower (blue); the right one climbs from last year's height
        v = group(f"rev{i}_vis", [(F(0, 0.04), F(1, 0.0))])
        pv = bar(v, f"rev{i}", x, W, D, r * k, M["dram"])
        if i == 0:
            heights(pv, [(F(0, 0.05), 1.0)])
        else:
            heights(pv, [(F(0, 0.05), rev[0] / r), (F(0, 0.20), rev[0] / r), (F(0, 0.70), 1.0)])
        # beats 1-2: the same tower as glass, with cost (grey) at the foot and margin (gold) filling it
        gv = group(f"glass{i}_vis", [(F(1, 0.0), END)])
        bar(group(f"glass{i}_on", [(F(1, 0.0), F(1, 0.78))], gv), f"glass{i}", x, W + 16, D + 16, r * k + 8, M["ghost"], z0=8)
        cost = bar(gv, f"cost{i}", x, W, D, (r - g) * k, M["cost"])
        heights(cost, [(F(1, 0.02), 0.02), (F(1, 0.2), 1.0)])
        mg = bar(gv, f"margin{i}", x, W - 4, D - 4, g * k, M["gold"], y0=(r - g) * k)
        heights(mg, [(F(1, 0.2), 0.01), (F(1, 0.75), 1.0)])
    # beat 2: next quarter's guide as a glass tower
    gd = bar(None, "guide", xs[2], W, D, 61.5 * k, M["ghost_gold"])
    heights(gd, [(F(2, 0.05), 0.02), (F(2, 0.6), 1.0)])

    h0, h1 = rev[0] * k, rev[1] * k
    tag("FQ4 FY25 $11.32B", (xs[0], h0 + 20, -D / 2), [(F(0, 0.1), F(1, 0))])
    tag("FQ4 FY26 $54.23B", (xs[1], h1 + 20, -D / 2), [(F(0, 0.72), F(1, 0))])
    tag("4.8x in a year", (xs[1] + W / 2, h1 * 0.5, 0), [(F(0, 0.75), F(1, 0))])
    tag("44.7% margin, cost $6.26B", (xs[0], h0 + 20, -D / 2), [(F(1, 0.3), F(2, 0))])
    tag("cost $7.18B", (xs[1] + W / 2, (rev[1] - gp[1]) * k * 0.5, 0), [(F(1, 0.25), END)])
    tag("86.8% gross margin", (xs[1], h1 * 0.6, 0), [(F(1, 0.75), END)])
    tag("FQ1 FY27 guide $61.5B", (xs[2], 61.5 * k + 20, -D / 2), [(F(2, 0.6), END)])
    tag("RPO $150B (stated)", (xs[0], h0 + 20, -D / 2), [(F(2, 0.3), END)])
    camera(ROOT, [((0.0, 470.0, 0.0), 3000.0, 0.10, 0.13)] * 3)


# ---- revenue: a staircase out of the 2023 trough ------------------------------------------
# Quarterly revenue, DRAM and NAND (10-Q Revenue by Technology / prepared remarks; page revenue
# and dram_nand tabs); operating income for the loss quarters (page revenue table).

QTRS = ["2022Q4", "2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1", "2024Q2", "2024Q3",
        "2024Q4", "2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2", "2026Q3"]
REV = [4.085, 3.693, 3.752, 4.010, 4.726, 5.824, 6.811, 7.750,
       8.709, 8.053, 9.301, 11.32, 13.643, 23.86, 41.456, 54.23]
DRAM = [2.829, 2.722, 2.672, 2.8, 3.427, 4.158, 4.692, 5.3,
        6.4, 6.123, 7.071, 9.0, 10.812, 18.768, 31.328, 39.8]
NAND = [1.103, 0.885, 1.013, 1.2, 1.230, 1.567, 2.065, 2.4,
        2.241, 1.855, 2.155, 2.3, 2.743, 4.997, 9.943, 14.1]
OPLOSS = [-0.209, -2.30, -1.76, -1.47, -1.13]


def revenue():
    k = 25.0
    sp, W, D = 262.0, 200.0, 220.0
    x0 = -sp * 7.5
    floor(x0 - 300, -x0 + 300, z0=-700, z1=-D - 10)
    box("zero", (x0 - 300, -4, -D - 10), (-x0 + 300, 0, 4), M["line"], ROOT)
    groups = [range(0, 5), range(5, 12), range(12, 16)]
    for b, idx in enumerate(groups):
        n = len(idx)
        for j, i in enumerate(idx):
            x = x0 + sp * i
            f0 = F(b, 0.05 + 0.6 * j / max(1, n - 1)) if n > 1 else F(b, 0.1)
            f1 = f0 + 30
            y = 0.0
            pv = pivot(f"q{i}", (x, 0, 0), ROOT)
            for part, val, mm in (("d", DRAM[i], "dram"), ("n", NAND[i], "nand"), ("o", REV[i] - DRAM[i] - NAND[i], "other")):
                if val <= 0.005:
                    continue
                box(f"q{i}{part}", (-W / 2, y, -D), (W / 2, y + val * k, 0), M[mm], pv)
                y += val * k
            heights(pv, [(f0, 0.02), (f1, 1.0)])
            if i < len(OPLOSS):
                pv = bar(None, f"loss{i}", x, W * 0.7, D * 0.7, OPLOSS[i] * k, M["red"], z0=-D * 0.15)
                heights(pv, [(f1, 0.02), (f1 + 20, 1.0)])
    xi = lambda i: x0 + sp * i  # noqa: E731
    tag("2023 trough $3.69B", (xi(1), REV[1] * k + 10, -D / 2), [(F(0, 0.3), F(1, 0))])
    tag("op loss -$2.30B", (xi(1) + W / 2, OPLOSS[1] * k * 0.6, 0), [(F(0, 0.4), F(1, 0))])
    tag("DRAM blue, NAND green", (xi(4) + W / 2, DRAM[4] * k * 0.5, 0), [(F(0, 0.75), F(1, 0))])
    tag("FQ4 FY25 $11.32B", (xi(11), REV[11] * k + 10, -D / 2), [(F(1, 0.7), F(2, 0))])
    tag("FQ3 FY24 $6.81B", (xi(6), REV[6] * k + 10, -D / 2), [(F(1, 0.3), F(2, 0))])
    tag("FQ4 FY26 $54.23B", (xi(15), REV[15] * k + 10, -D / 2), [(F(2, 0.7), END)])
    tag("DRAM $39.8B", (xi(15) + W / 2, DRAM[15] * k * 0.5, 0), [(F(2, 0.75), END)])
    tag("NAND $14.1B", (xi(15) + W / 2, (DRAM[15] + NAND[15] * 0.5) * k, 0), [(F(2, 0.75), END)])
    tag("FQ2 FY26 $23.86B", (xi(13), REV[13] * k + 10, -D / 2), [(F(2, 0.4), END)])
    camera(ROOT, [
        ((xi(2.4), 25.0, 0.0), 1200.0, 0.06, 0.12),
        ((xi(6.6), 110.0, 0.0), 2100.0, 0.06, 0.14),
        ((350.0, 620.0, 0.0), 3200.0, 0.06, 0.12),
    ])


# ---- dram_nand: two engines, and the DRAM one is three times bigger ------------------------
# Fiscal-year DRAM / NAND revenue (10-K Revenue by Technology): FY23 10.98 / 4.21, FY24 17.60 /
# 7.23, FY25 28.58 / 8.50, FY26 100.68 / 31.79 $B. DRAM 79% of revenue FQ4 FY25 and NAND ASP
# +85% QoQ FQ3 FY26 (prepared remarks).

FY_DN = [("FY23", 10.978, 4.206), ("FY24", 17.603, 7.227), ("FY25", 28.578, 8.503), ("FY26", 100.679, 31.785)]


def dram_nand():
    k = 13.0
    xs = (-1950.0, -700.0, 550.0, 1800.0)
    floor(-2600, 2500)
    r = 170.0
    when = [(0, 0.05), (0, 0.45), (1, 0.1), (2, 0.08)]
    for i, (fy, d, n) in enumerate(FY_DN):
        b, u = when[i]
        f0 = F(b, u)
        pv = cyl(None, f"{fy}_dram", xs[i] - r - 15, r, d * k, M["dram"], z=-r)
        heights(pv, [(f0, 0.02), (f0 + (90 if i < 3 else 130), 1.0)])
        pn = cyl(None, f"{fy}_nand", xs[i] + r + 15, r, n * k, M["nand"], z=-r)
        heights(pn, [(f0 + 20, 0.02), (f0 + (110 if i < 3 else 150), 1.0)])
    t = lambda i, side, v: (xs[i] + side * (r + 15), v * k + 15, -r)  # noqa: E731
    tag("FY23 DRAM $10.98B", t(0, -1, FY_DN[0][1]), [(F(0, 0.3), F(1, 0))])
    tag("FY23 NAND $4.21B", t(0, 1, FY_DN[0][2]), [(F(0, 0.35), F(1, 0))])
    tag("FY24 DRAM $17.60B", t(1, -1, FY_DN[1][1]), [(F(0, 0.75), F(1, 0))])
    tag("FY24 NAND $7.23B", t(1, 1, FY_DN[1][2]), [(F(0, 0.8), F(1, 0))])
    tag("FY25 DRAM $28.58B", t(2, -1, FY_DN[2][1]), [(F(1, 0.5), END)])
    tag("FY25 NAND $8.50B", t(2, 1, FY_DN[2][2]), [(F(1, 0.55), F(2, 0))])
    tag("DRAM 79% of sales, FQ4 FY25", (xs[2] - 2 * r - 15, FY_DN[2][1] * k * 0.25, -r), [(F(1, 0.6), F(2, 0))])
    tag("FY26 DRAM $100.68B", t(3, -1, FY_DN[3][1]), [(F(2, 0.7), END)])
    tag("FY26 NAND $31.79B", t(3, 1, FY_DN[3][2]), [(F(2, 0.75), END)])
    tag("NAND price +85% QoQ (FQ3)", (xs[3] + r + 15, FY_DN[3][2] * k * 0.5, 0), [(F(2, 0.8), END)])
    camera(ROOT, [
        ((-1200.0, 170.0, 0.0), 1850.0, 0.06, 0.14),
        ((-500.0, 230.0, 0.0), 2500.0, 0.06, 0.14),
        ((400.0, 640.0, 0.0), 3400.0, 0.06, 0.12),
    ])


# ---- bus: the old units recut into the new, and cloud memory takes off --------------------
# FY2024 old structure CNBU 9.513 / MBU 6.354 / SBU 4.592 / EBU 4.614 $B; the same year recast
# to CMBU 3.792 / CDBU 4.984 / MCBU 11.667 / AEBU 4.631; FY2026 CMBU 43.085 / CDBU 37.592 /
# MCBU 36.601 / AEBU 15.886 (10-K / 10-Q segment tables). CMBU gross margin 83% FQ4 FY26 (stated).


def bus():
    k = 30.0
    xs = (-1200.0, -400.0, 400.0, 1200.0)
    W, D = 560.0, 380.0
    floor(-2200, 2200)
    old = [("CNBU", 9.513, "muted1"), ("MBU", 6.354, "muted2"), ("SBU", 4.592, "muted3"), ("EBU", 4.614, "muted4")]
    new = [("CMBU", 3.792, 43.085, "cyan"), ("CDBU", 4.984, 37.592, "dram"), ("MCBU", 11.667, 36.601, "purple"), ("AEBU", 4.631, 15.886, "nand")]
    for i, (n, v, mm) in enumerate(old):
        mv = group(f"old{i}_mv", parent=group(f"old{i}_vis", [(F(0, 0.04), F(1, 0.42))]))
        pv = bar(mv, f"old{i}", xs[i], W, D, v * k, M[mm])
        heights(pv, [(F(0, 0.05 + 0.08 * i), 0.02), (F(0, 0.25 + 0.08 * i), 1.0), (F(1, 0.2), 1.0), (F(1, 0.41), 0.05)])
        move(mv, [(F(1, 0.05), (0, 0, 0)), (F(1, 0.38), (-xs[i], 0, 0))])
    for i, (n, v24, v26, mm) in enumerate(new):
        mv = group(f"new{i}_mv")
        pv = bar(mv, f"new{i}", xs[i], W, D, v26 * k, M[mm])
        heights(pv, [(F(1, 0.42), 0.15 * v24 / v26), (F(1, 0.75), v24 / v26), (F(2, 0.08), v24 / v26), (F(2, 0.7), 1.0)])
        move(mv, [(F(1, 0.42), (-xs[i], 0, 0)), (F(1, 0.75), (0, 0, 0))])
    # a glass block of the whole FY24 ($25.07B) at the centre while the units are recut
    pool = bar(group("pool_vis", [(F(1, 0.3), F(1, 0.55))]), "pool", 0, W + 40, D + 40, 25.07 * k * 0.25, M["ghost"], z0=20)
    heights(pool, [(F(1, 0.3), 1.0)], pop=False)
    top = lambda i, v: (xs[i], v * k + 15, -D / 2)  # noqa: E731
    for i, (n, v, _) in enumerate(old):
        tag(f"{n} ${v:.2f}B FY24" if i == 0 else f"{n} ${v:.2f}B", top(i, v), [(F(0, 0.3 + 0.08 * i), F(1, 0.15))])
    tag("same FY24 $25.07B, recut", (0, 25.07 * k * 0.25 + 20, -D / 2), [(F(1, 0.3), F(1, 0.55))])
    tag("CMBU (cloud) $3.79B FY24", top(0, new[0][1]), [(F(1, 0.78), F(2, 0.05))])
    tag("MCBU $11.67B", top(2, new[2][1]), [(F(1, 0.78), F(2, 0.05))])
    tag("CMBU $43.09B FY26", top(0, new[0][2]), [(F(2, 0.72), END)])
    tag("CDBU $37.59B", top(1, new[1][2]), [(F(2, 0.72), END)])
    tag("MCBU $36.60B", top(2, new[2][2]), [(F(2, 0.72), END)])
    tag("CMBU gross margin 83%", (xs[0] + W / 2, new[0][2] * k * 0.5, 0), [(F(2, 0.78), END)])
    camera(ROOT, [
        ((150.0, 160.0, 0.0), 2150.0, 0.06, 0.15),
        ((150.0, 160.0, 0.0), 2150.0, 0.06, 0.15),
        ((150.0, 620.0, 0.0), 3050.0, 0.06, 0.12),
    ])


# ---- hbm: taller stacks, then the money, then share parity --------------------------------
# HBM3E 12-high 36 GB (FQ2 FY24), HBM4 16-high 48 GB (FQ2 FY26), HBM4 > 2.8 TB/s (FQ4 FY25),
# HBM4 volume ramp CQ2 2026 (FQ1 FY26). HBM revenue > $100M FQ3 FY24, > $1B FQ2 FY25, ~ $2B FQ4
# FY25 (prepared remarks). HBM share 21% vs DRAM share 22%, 2025Q2 (Counterpoint, page share
# parity table); parity reached CQ3 25 (FQ4 FY25 remarks).


def hbm():
    import hbm_kit as H

    mine = {k: M[k] for k in ("gold", "steel", "wafer")}
    H.mats(M)
    M.update(mine)
    floor(-3000, 2800, z0=-900)
    sx = (-2350.0, -1750.0, -1150.0)
    gens = [8, 12, 16]
    for s, (x, n) in enumerate(zip(sx, gens)):
        st = H.stack(ROOT, M, x, n, f"stk{s}", tsv=True)
        f0 = F(0, 0.04 + 0.1 * s)
        show(st.base, [(f0, END)])
        for kk, d in enumerate(st.dies):
            show(d, [(f0 + 4 + kk * 5, END)])
    tag("HBM3E 8-high", (sx[0], H.die_top(7) + 20, -170), [(F(0, 0.3), F(1, 0))])
    tag("HBM3E 12-high 36GB", (sx[1], H.die_top(11) + 20, -170), [(F(0, 0.45), F(1, 0))])
    tag("HBM4 16-high 48GB", (sx[2], H.die_top(15) + 20, -170), [(F(0, 0.6), F(1, 0)), (F(2, 0.1), END)])
    tag("HBM4 >2.8 TB/s, ramp CQ2 26", (sx[2] + 190, 400, 0), [(F(0, 0.7), F(1, 0))])

    k = 450.0  # mm per $B of quarterly HBM revenue
    rx = (-350.0, 100.0, 550.0)
    revs = [(0.1, ">$100M FQ3 FY24"), (1.0, ">$1B FQ2 FY25"), (2.0, "~$2B FQ4 FY25")]
    for i, (v, t) in enumerate(revs):
        pv = bar(None, f"hrev{i}", rx[i], 300, 300, v * k, M["gold"])
        f0 = F(1, 0.05 + 0.22 * i)
        heights(pv, [(f0, 0.02), (f0 + 40, 1.0)])
        tag(t, (rx[i], v * k + 15, -150), [(f0 + 40, END if i == 2 else F(2, 0))])
    tag("HBM sold out CY24 to CY27", (rx[0], 700, -150), [(F(1, 0.8), F(2, 0))])

    kk = 30.0  # mm per share point
    gx = (1450.0, 1850.0)
    for i, (v, mm) in enumerate(((21.0, "gold"), (22.0, "dram"))):
        pv = bar(None, f"share{i}", gx[i], 340, 340, v * kk, M[mm])
        heights(pv, [(F(2, 0.08), 0.02), (F(2, 0.55), 1.0)])
    tag("HBM share 21% (2025Q2)", (gx[0], 21 * kk + 15, -170), [(F(2, 0.55), END)])
    tag("DRAM share 22%", (gx[1] + 170, 22 * kk * 0.6, 0), [(F(2, 0.6), END)])
    camera(ROOT, [
        ((-1250.0, 480.0, 0.0), 2400.0, 0.06, 0.14),
        ((-650.0, 470.0, 0.0), 2800.0, 0.06, 0.13),
        ((0.0, 470.0, 0.0), 3500.0, 0.06, 0.12),
    ])


# ---- pricing: price did the work, bits barely moved --------------------------------------
# DRAM ASP change and DRAM bit shipment change QoQ, company stated (page pricing tab); gross
# margin -32.7% FQ2 FY23 and 84.6% FQ3 FY26 (SEC XBRL, page revenue tab).

ASP = [-22, -20, -10, -8, 2, 17, 20, 15, 8, 5, -2, 11, 20, 65, 62, 17]
BITS = [-25, 15, 10, 15, 22, 2, -5, 0, 11, -8, 20, 12, None, 5, 2, 5]


def pricing():
    k = 12.0
    sp = 280.0
    x0 = -sp * 7.5
    floor(x0 - 300, -x0 + 300, z0=-700, z1=-170)
    box("zero", (x0 - 300, -4, -170), (-x0 + 300, 0, 4), M["line"], ROOT)
    groups = [range(0, 4), range(4, 12), range(12, 16)]
    for b, idx in enumerate(groups):
        n = len(idx)
        for j, i in enumerate(idx):
            x = x0 + sp * i
            f0 = F(b, 0.05 + 0.55 * j / max(1, n - 1))
            a = ASP[i]
            pv = bar(None, f"asp{i}", x - 55, 120, 150, a * k if a else 6, M["red" if a < 0 else "gold"])
            heights(pv, [(f0, 0.02), (f0 + 30, 1.0)])
            if BITS[i] is not None:
                bv = BITS[i]
                pb = bar(None, f"bits{i}", x + 60, 80, 110, bv * k if bv else 6, M["dram"], z0=-20)
                heights(pb, [(f0 + 10, 0.02), (f0 + 40, 1.0)])
    xi = lambda i: x0 + sp * i  # noqa: E731
    tag("DRAM price -20% (FQ2 FY23)", (xi(1) - 55, ASP[1] * k - 10, 0), [(F(0, 0.4), F(1, 0))])
    tag("bits +15% (blue)", (xi(1) + 60, BITS[1] * k + 10, -60), [(F(0, 0.45), F(1, 0))])
    tag("gross margin -32.7%", (xi(2) - 55, ASP[2] * k * 0.5, 0), [(F(0, 0.6), F(1, 0))])
    tag("price +20% (FQ3 FY24)", (xi(6) - 55, ASP[6] * k + 10, -75), [(F(1, 0.35), F(2, 0))])
    tag("bits +20% (FQ3 FY25)", (xi(10) + 60, BITS[10] * k + 10, -60), [(F(1, 0.7), F(2, 0))])
    tag("price +65% (FQ2 FY26)", (xi(13) - 55, ASP[13] * k + 10, -75), [(F(2, 0.4), END)])
    tag("bits +2% (FQ3 FY26)", (xi(14) + 60, BITS[14] * k + 10, -60), [(F(2, 0.55), END)])
    tag("gross margin 84.6%", (xi(14) - 55, ASP[14] * k * 0.6, 0), [(F(2, 0.65), END)])
    camera(ROOT, [
        ((xi(1.6), 10.0, 0.0), 1600.0, 0.06, 0.12),
        ((xi(6.2), 90.0, 0.0), 2300.0, 0.06, 0.12),
        ((350.0, 250.0, 0.0), 3150.0, 0.06, 0.11),
    ])


# ---- capex: FY26 guidance raised three times, and 1H FY27 alone nearly matches it ----------
# Net capex FY24 $8.1B, FY25 $13.8B, FY26 $27.37B actual; FY26 guide $20B (Dec 2025), $25B+
# (Mar 2026), $27B (Jun 2026); 1H FY27 guide $25B (Sep 2026). All Micron remarks / 8-K.


def capex():
    k = 45.0
    W, D = 560.0, 380.0
    xs = (-1650.0, -900.0, 300.0, 1500.0)
    floor(-2400, 2400)
    for i, (v, b, u) in enumerate(((8.1, 0, 0.05), (13.8, 0, 0.35))):
        pv = bar(None, f"fy{i}", xs[i], W, D, v * k, M["steel"])
        heights(pv, [(F(b, u), 0.02), (F(b, u + 0.25), 1.0)])
    # FY26: climbs guide by guide, then lands on the actual
    full = 27.37
    pv = bar(None, "fy26", xs[2], W, D, full * k, M["steel"])
    heights(pv, [(F(1, 0.04), 0.02),
                 (F(1, 0.20), 20 / full), (F(1, 0.34), 20 / full),
                 (F(1, 0.50), 25 / full), (F(1, 0.64), 25 / full),
                 (F(1, 0.80), 27 / full), (F(2, 0.05), 27 / full),
                 (F(2, 0.25), 1.0)])
    for j, (g, u) in enumerate(((20, 0.20), (25, 0.50), (27, 0.80))):
        rg = group(f"guide{j}", [(F(1, u), END)])
        box(f"guide{j}_m", (xs[2] - W / 2 - 60, g * k - 6, -D - 40), (xs[2] + W / 2 + 60, g * k + 6, 40), M["gold_hot"], rg)
    cap = group("actual_cap", [(F(2, 0.25), END)])
    box("actual_cap_m", (xs[2] - W / 2 - 8, full * k, -D - 8), (xs[2] + W / 2 + 8, full * k + 14, 8), M["cyan"], cap)
    gh = bar(None, "fy27h1", xs[3], W, D, 25 * k, M["ghost_gold"])
    heights(gh, [(F(2, 0.35), 0.02), (F(2, 0.8), 1.0)])
    tag("FY24 net capex $8.1B", (xs[0], 8.1 * k + 15, -D / 2), [(F(0, 0.3), F(1, 0))])
    tag("FY25 $13.8B", (xs[1], 13.8 * k + 15, -D / 2), [(F(0, 0.6), END)])
    tag("Dec 25: FY26 guide $20B", (xs[2] - W / 2 - 60, 20 * k, 0), [(F(1, 0.2), F(2, 0))])
    tag("Mar 26: $25B+", (xs[2] + W / 2 + 60, 25 * k, 0), [(F(1, 0.5), F(2, 0))])
    tag("Jun 26: $27B", (xs[2] - W / 2 - 60, 27 * k, 0), [(F(1, 0.8), F(2, 0))])
    tag("FY26 actual $27.37B", (xs[2], full * k + 30, -D / 2), [(F(2, 0.28), END)])
    tag("1H FY27 guide $25B", (xs[3], 25 * k + 15, -D / 2), [(F(2, 0.8), END)])
    tag("FY26 guide raised 3 times", (xs[2] + W / 2, 8 * k, 0), [(F(2, 0.4), END)])
    camera(ROOT, [
        ((-500.0, 400.0, 0.0), 2400.0, 0.06, 0.13),
        ((-50.0, 600.0, 0.0), 2750.0, 0.06, 0.12),
        ((200.0, 600.0, 0.0), 3050.0, 0.06, 0.12),
    ])


# ---- fabs: where the money lands, west to east, and when wafers come out ------------------
# New York $100B, up to 4 fabs, first wafers CY2030; Boise ID1 wafers mid-2027; CHIPS $6.1B
# (ID + NY); Singapore HBM packaging $7B, output early 2027; Hiroshima JPY 1,500B (estimate,
# TrendForce); Sanand ATMP $2.75B, opened 2026-02-28. Footprint area ~ investment; Idaho's
# own figure is not disclosed, so it is drawn as glass.


def fabs():
    S = 95.0  # footprint side = S * sqrt($B)
    floor(-3200, 3100, z0=-1500, z1=120, m="sea")
    box("us_land", (-3100, 0, -1400), (-900, 8, 60), M["land"], ROOT)
    box("asia_land", (200, 0, -1400), (3000, 8, 60), M["land"], ROOT)
    sites = [  # name, x, z, $B (None = not disclosed), beat, lit order (frame)
        ("boise", -2550.0, -500.0, None, 0),
        ("ny", -1550.0, -650.0, 100.0, 0),
        ("sanand", 650.0, -500.0, 2.75, 1),
        ("singapore", 1550.0, -400.0, 7.0, 1),
        ("hiroshima", 2450.0, -600.0, 9.3, 1),
    ]
    tops = {}
    for j, (nm, x, z, v, b) in enumerate(sites):
        side = S * math.sqrt(v) if v else 420.0
        h = 240.0  # flat fabs: the footprint carries the money
        f0 = F(b, 0.05 + 0.18 * (j % 3 if b else j))
        pv = pivot(f"fab_{nm}", (x, 8, z), ROOT)
        box(f"fab_{nm}_m", (-side / 2, 0, -side / 2), (side / 2, h, side / 2), M["ghost" if v is None else "steel"], pv)
        box(f"fab_{nm}_roof", (-side / 2 - 10, h, -side / 2 - 10), (side / 2 + 10, h + 18, side / 2 + 10), M["cost"], pv)
        heights(pv, [(f0, 0.02), (f0 + 50, 1.0)])
        tops[nm] = (x, 8 + h + 18, z, side)
    tag("Boise ID1: wafers mid-2027", (tops["boise"][0], tops["boise"][1] + 10, tops["boise"][2]), [(F(0, 0.3), F(1, 0))])
    tag("New York $100B, up to 4 fabs", (tops["ny"][0], tops["ny"][1] + 10, tops["ny"][2]), [(F(0, 0.5), F(1, 0))])
    tag("CHIPS Act $6.1B (ID + NY)", (-2050, 30, 60), [(F(0, 0.65), F(1, 0))])
    tag("Sanand ATMP $2.75B", (tops["sanand"][0], tops["sanand"][1] + 10, tops["sanand"][2]), [(F(1, 0.25), F(2, 0))])
    tag("Singapore HBM pkg $7B", (tops["singapore"][0], tops["singapore"][1] + 10, tops["singapore"][2]), [(F(1, 0.45), F(2, 0))])
    tag("Hiroshima JPY 1.5T est", (tops["hiroshima"][0], tops["hiroshima"][1] + 10, tops["hiroshima"][2]), [(F(1, 0.6), F(2, 0))])

    # beat 2: beacons light in the order output starts, and wafers leave the lit sites
    order = [("sanand", 0.08, "2026: Sanand opens"), ("boise", 0.3, "2027: Boise ID1"),
             ("singapore", 0.42, "2027: Singapore HBM"), ("ny", 0.7, "2030: New York wafers")]
    for nm, u, t in order:
        x, y, z, side = tops[nm]
        bg = group(f"beacon_{nm}", [(F(2, u), END)])
        disc(f"beacon_{nm}_m", (x, y + 30, z), min(140.0, side * 0.35), 40, M["glow"], bg, 32)
        tag(t, (x, y + 60, z), [(F(2, u), END)])
        for w in range(3):
            e = group(f"waf_{nm}{w}")
            disc(f"waf_{nm}{w}_m", (x, y + 50, z), 60, 8, M["wafer"], e, 24)
            f0 = F(2, u) + 10 + w * 30
            f1 = min(f0 + 70, END - 1)
            fly(e, [(0, 0, 0), (0, 220, 300), (0, 160, 900 - z)], f0, f1, steps=4)
            show(e, [(f0, f1)])
    camera(ROOT, [
        ((-1850.0, 150.0, -550.0), 2450.0, 0.04, 0.55),
        ((1550.0, 100.0, -500.0), 2050.0, 0.04, 0.55),
        ((-50.0, 150.0, -500.0), 3600.0, 0.03, 0.50),
    ])


# ---- share: three towers trading the top spot ---------------------------------------------
# DRAM revenue share, TrendForce: 2024Q1 Samsung 43.9 / SK hynix 31.1 / Micron 21.5; 2025Q2
# SK hynix 38.7 / Samsung 32.7 / Micron 22.0; 2026Q2 Samsung 39.4 / SK hynix 24.9 / Micron 23.3;
# CXMT 9.5 2026Q2 (Herald Business). mkt-share.jsonl and the page share tab.


def share():
    k = 28.0
    W, D = 600.0, 420.0
    pos = {1: 0.0, 2: -950.0, 3: 950.0}
    floor(-2300, 2500)
    for r, x in pos.items():
        box(f"plinth{r}", (x - 380, 0, -D - 80), (x + 380, (4 - r) * 30, 80), M["cost"], ROOT)
    beats = [
        {"Samsung": (43.9, 1), "SK hynix": (31.1, 2), "Micron": (21.5, 3)},
        {"SK hynix": (38.7, 1), "Samsung": (32.7, 2), "Micron": (22.0, 3)},
        {"Samsung": (39.4, 1), "SK hynix": (24.9, 2), "Micron": (23.3, 3)},
    ]
    top = 45.0
    cols = {"Samsung": "slate", "SK hynix": "orange", "Micron": "cyan"}
    for nm in ("Samsung", "SK hynix", "Micron"):
        mv = group(f"mv_{nm}")
        pv = bar(mv, f"tw_{nm}", 0, W, D, top * k, M[cols[nm]], y0=0)
        hk, mk = [], []
        for b, bd in enumerate(beats):
            v, r = bd[nm]
            y = (4 - r) * 30
            t0, t1 = (F(b, 0.0) + (1 if b else 0), F(b, 0.25)) if b else (F(0, 0.02), F(0, 0.3))
            if b == 0:
                hk += [(t0, 0.02), (t1, v / top)]
                mk += [(t0, (pos[r], y, 0))]
            else:
                hk += [(t0, beats[b - 1][nm][0] / top), (t1, v / top)]
                mk += [(t0, (pos[beats[b - 1][nm][1]], (4 - beats[b - 1][nm][1]) * 30, 0)), (t1, (pos[r], y, 0))]
            hk += [(F(b + 1, 0) - 2, v / top)]
            mk += [(F(b + 1, 0) - 2, (pos[r], y, 0))]
        heights(pv, hk)
        move(mv, mk)
        for b, bd in enumerate(beats):
            v, r = bd[nm]
            tag(f"{nm} {v:.1f}%", (pos[r], (4 - r) * 30 + v * k + 15, -D / 2), [(F(b, 0.3), F(b + 1, 0))])
    cx = bar(None, "cxmt", 1950, 420, 300, 9.5 * k, M["red"])
    heights(cx, [(F(2, 0.3), 0.02), (F(2, 0.6), 1.0)])
    tag("CXMT 9.5% (2026Q2)", (1950, 9.5 * k + 15, -150), [(F(2, 0.6), END)])
    camera(ROOT, [
        ((300.0, 640.0, 0.0), 3250.0, 0.06, 0.13),
        ((300.0, 640.0, 0.0), 3250.0, 0.06, 0.13),
        ((400.0, 640.0, 0.0), 3250.0, 0.06, 0.13),
    ])


# ---- sources: what the page stands on, where sources disagree, and where they agree -------
# Row counts by basis (page sources tab): company stated 170, reported 137, estimate 39, market
# share 33, guidance 21, forecast 7; 105 conflicting values. 2026Q2 DRAM revenue TrendForce $36.00B
# est vs Micron 10-Q $31.33B; FY26 DRAM 10-K $100.68B vs StorageNewsletter $100.70B.


def sources():
    floor(-2700, 2700)
    stacks = [("stated", 170, "paper"), ("reported", 137, "paper2"), ("estimate", 39, "paper"),
              ("mkt share", 33, "paper2"), ("guidance", 21, "paper"), ("forecast", 7, "paper2")]
    sp = 360.0
    x0 = -2350.0
    per, th = 10, 46.0  # one slab = 10 sourced rows
    for i, (nm, n, mm) in enumerate(stacks):
        x = x0 + sp * i
        slabs = math.ceil(n / per)
        for s in range(slabs):
            frac = min(1.0, (n - s * per) / per)
            g = group(f"doc{i}_{s}", [(F(0, 0.05) + s * 5 + i * 3, END)])
            off = 8 * ((s * 7 + i * 3) % 3 - 1)
            box(f"doc{i}_{s}_m", (x - 130 + off, s * (th + 4), -280), (x + 130 + off, s * (th + 4) + th * frac, -20), M[mm], g)
    tg = lambda i, n: (x0 + sp * i, math.ceil(n / per) * (th + 4) + 15, -150)  # noqa: E731
    tag("company stated: 170", tg(0, 170), [(F(0, 0.5), F(1, 0))])
    tag("reported (10-K/10-Q): 137", tg(1, 137), [(F(0, 0.55), F(1, 0))])
    tag("estimates 39, mkt share 33", tg(2.5, 39), [(F(0, 0.6), F(1, 0))])
    tag("407 numbers, 88 pages", (x0 + sp * 4, 260, -150), [(F(0, 0.7), F(1, 0))])

    k = 20.0
    cx = (150.0, 550.0)
    for i, (v, mm) in enumerate(((36.0, "red"), (31.33, "dram"))):
        pv = bar(None, f"conf{i}", cx[i], 340, 340, v * k, M[mm])
        heights(pv, [(F(1, 0.05 + 0.1 * i), 0.02), (F(1, 0.4 + 0.1 * i), 1.0)])
    tag("TrendForce est $36.00B", (cx[0], 36 * k + 15, -170), [(F(1, 0.4), F(2, 0))])
    tag("10-Q $31.33B (FQ3 FY26)", (cx[1] + 170, 31.33 * k * 0.6, 0), [(F(1, 0.5), F(2, 0))])
    tag("calendar vs fiscal quarter", (cx[1] + 170, 200, 0), [(F(1, 0.65), F(2, 0))])
    tag("105 conflicting values", (cx[0], 36 * k + 140, -170), [(F(1, 0.3), F(2, 0))])

    k2 = 7.0
    ax = (1400.0, 1800.0)
    for i, (v, mm) in enumerate(((100.68, "dram"), (100.70, "nand"))):
        pv = bar(None, f"agree{i}", ax[i], 340, 340, v * k2, M[mm])
        heights(pv, [(F(2, 0.05 + 0.1 * i), 0.02), (F(2, 0.45 + 0.1 * i), 1.0)])
    tag("10-K FY26 DRAM $100.68B", (ax[0], 100.68 * k2 + 15, -170), [(F(2, 0.45), END)])
    tag("press $100.70B", (ax[1] + 170, 100.70 * k2 * 0.5, 0), [(F(2, 0.55), END)])
    tag("both FY26: agree to 0.02%", ((ax[0] + ax[1]) / 2, 100.7 * k2 + 140, -170), [(F(2, 0.65), END)])
    camera(ROOT, [
        ((-1250.0, 420.0, 0.0), 2300.0, 0.06, 0.13),
        ((-350.0, 440.0, 0.0), 3000.0, 0.06, 0.12),
        ((-100.0, 440.0, 0.0), 3250.0, 0.06, 0.12),
    ])


SCENES = {
    "snapshot": snapshot,
    "revenue": revenue,
    "dram_nand": dram_nand,
    "bus": bus,
    "hbm": hbm,
    "pricing": pricing,
    "capex": capex,
    "fabs": fabs,
    "share": share,
    "sources": sources,
}


def check_tags(tab):
    for f in range(0, END, 2):
        on = [t for t, iv in TAGS if any(a <= f < b for a, b in iv)]
        assert len(on) <= 4, f"{tab}: {len(on)} tags at frame {f}: {on}"


def export(tab):
    os.makedirs(OUT_DIR, exist_ok=True)
    glb = os.path.join(OUT_DIR, f"{SLUG}_{tab}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb,
        export_format="GLB",
        export_yup=True,
        export_animations=True,
        export_force_sampling=True,
        export_frame_step=1,
        export_cameras=False,
        export_lights=False,
        use_selection=False,
    )
    print("exported", glb)


def build(tab):
    global ROOT
    TAGS.clear()
    m, ROOT = start(f"{SLUG}_{tab}", beats=BEATS, page="mem")
    M.clear()
    M.update(m)
    mats(M)
    SCENES[tab]()
    check_tags(tab)
    export(tab)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for tab in argv or list(SCENES):
        build(tab)
