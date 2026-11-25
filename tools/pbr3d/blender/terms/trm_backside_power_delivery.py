"""TRM_BACKSIDE_POWER_DELIVERY: the Terms-tab overview for backside power delivery (BSPDN).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_backside_power_delivery.py

The shared GPU board, with a slice of the GPU die drawn huge on the bench and cut open. In the
conventional version power and signal share one front-side metal stack and the bumps sit on top;
in the backside version the wafer is bonded to a carrier, the silicon is thinned to a few microns,
nano-TSVs and thick backside power rails feed the transistors from below, and the front stack
carries only signals.

Beats:
  0 board     the board, the package, a slice of the die on the bench
  1 today     power beads crawl down a dozen-plus front layers; droop meter high
  2 flip      carrier bonded on top, substrate thinned, nano-TSVs and back rails appear
  3 backside  power comes straight up from the back; freed front layers fill with signal wires
  4 who       Intel PowerVia 18A, TSMC A16, Samsung; tool and bonding vendors
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_BACKSIDE_POWER_DELIVERY"
BEATS = [
    ("Backside power moves a chip's power wiring under the transistors",
     "Every transistor on a GPU die needs two things: power and signals. Both have always come in from the front, "
     "through the same stack of a dozen-plus copper wiring layers built on top of the transistors. Backside power "
     "delivery (BSPDN) moves the power wires to the back of the silicon, leaving the front for signals only."),
    ("Today power fights signals for space in one front-side stack",
     "In a conventional flip-chip die, current from the bumps has to squeeze down through every metal layer, getting "
     "thinner and more resistive near the transistors. That resistance drops voltage (IR droop) exactly where the "
     "load is highest, and the fat power rails eat a big share of the routing tracks signals also need."),
    ("The wafer is flipped, bonded to a carrier and thinned to microns",
     "To reach the transistors from behind, the finished front side is bonded face-down to a carrier wafer, then the "
     "original silicon is ground and polished from hundreds of microns down to a few hundred nanometres to a few "
     "microns. Tiny nano-TSVs are etched through to the transistor level and thick power rails are built on the back."),
    ("Power comes straight up from below; the front carries only signals",
     "Now current takes a short, thick path from the bumps through the backside rails into each cell, so droop falls "
     "(Intel reported ~30% less) and cells can pack tighter. The front layers freed of power rails take more signal "
     "wires. For power-hungry AI chips that means higher clocks at the same voltage, or less power at the same speed."),
    ("Intel ships it first; TSMC and Samsung follow at 2 nm-class",
     "Intel's PowerVia is in production on its 18A node; TSMC's Super Power Rail arrives with A16 and Samsung has its "
     "own version on 2 nm-class processes. The extra wafer bonding, thinning, etch and deposition steps add work for "
     "tool makers like Applied Materials (AMAT) and Lam Research (LRCX). Related: Intel (INTC), TSMC (TSM)."),
]

# the giant die slice on the bench: x along the slice, cut at z = 0
X0, X1 = 158.0, 242.0
Z0 = -28.0
Y_BUMP = (0.0, 4.0)
Y_BMET = (4.0, 13.0)  # backside power metal
Y_SUBT = (13.0, 15.5)  # thinned silicon
Y_SUBK = (4.0, 15.5)  # thick substrate (conventional)
Y_FEOL = (15.5, 19.0)  # transistor layer
Y_FMET = (19.0, 44.0)  # front metal stack
Y_CARR = (44.0, 52.0)  # carrier wafer (backside) / front bumps (conventional)
N_LAY = 10


def mats(m):
    m["fet_c"] = mat("bs_fet", (0.55, 0.35, 0.65), metal=0.3, rough=0.4)
    m["sigw"] = mat("bs_sig", (0.30, 0.85, 1.0), emit=(0.25, 0.80, 1.0), strength=2.2)
    m["pwrw"] = mat("bs_pwr", (1.0, 0.60, 0.20), emit=(1.0, 0.55, 0.15), strength=2.4)
    m["ild"] = mat("bs_ild", (0.80, 0.86, 0.92), rough=0.25)
    m["bond"] = mat("bs_bond", (0.55, 0.85, 0.75), emit=(0.45, 0.85, 0.70), strength=1.6)
    m["gauge"] = mat("bs_gauge", (0.10, 0.11, 0.13), rough=0.6)


def lay_y(k):
    """Bottom of front metal layer k (0 = M1 next to the transistors)."""
    return Y_FMET[0] + (Y_FMET[1] - Y_FMET[0]) * k / N_LAY


def slice_(m, root):
    """The die slice. Returns groups: conv (thick substrate, front power, front bumps), bsp
    (thin substrate, nTSVs, back rails, back bumps, carrier), extra (signal wires on freed tracks)."""
    g = empty("sl", root)
    # transistor layer: a row of cells with gates, always visible
    bx("sl_feol", (X0, Y_FEOL[0], Z0), (X1, Y_FEOL[0] + 1.2, 0.0), m["si"], g)
    cells = []
    x = X0 + 1.5
    k = 0
    while x < X1 - 3.0:
        w = 3.0 + 1.5 * (k % 3)
        cells.append(bx(f"sl_c{k}", (x, Y_FEOL[0] + 1.2, Z0 + 2.0), (x + w - 0.6, Y_FEOL[1], -0.3), m["fet_c"], g))
        for gi in range(2):
            gx = x + (w - 0.6) * (gi + 1) / 3
            cells.append(bx(f"sl_g{k}{gi}", (gx - 0.25, Y_FEOL[0] + 1.2, Z0 + 1.0), (gx + 0.25, Y_FEOL[1] + 0.4, -0.1), m["poly"], g))
        x += w
        k += 1
    D.join(cells, "sl_cells")
    # front stack dielectric slabs (thin, translucent-looking) and signal wires on every layer
    ild, sig = [], []
    for k in range(N_LAY):
        y0 = lay_y(k)
        ild.append(bx(f"sl_ild{k}", (X0, y0, Z0), (X1, y0 + 0.3, 0.0), m["ild"], g))
        h = 0.5 + 0.12 * k
        pitch = 2.0 + 0.6 * k
        n = int((X1 - X0 - 4.0) / pitch)
        for i in range(n):
            if i % 3 == 1:  # every third track left for power in the conventional stack
                continue
            xc = X0 + 2.0 + pitch * (i + 0.5)
            if k % 2 == 0:  # wires along z
                sig.append(bx(f"sl_s{k}_{i}", (xc - pitch * 0.18, y0 + 0.6, Z0 + 1.0), (xc + pitch * 0.18, y0 + 0.6 + h, 0.05), m["copper"], g))
            elif i % 2 == 0:  # wires along x, seen end-on as stubs at the cut
                sig.append(bx(f"sl_s{k}_{i}", (xc - pitch * 0.4, y0 + 0.6, -4.0), (xc + pitch * 0.4, y0 + 0.6 + h, 0.05), m["copper"], g))
    D.join(ild, "sl_ild")
    D.join(sig, "sl_sig")

    conv = empty("conv", root)
    bx("cv_sub", (X0, Y_SUBK[0], Z0), (X1, Y_SUBK[1], 0.0), m["si"], conv)
    pw = []
    for k in range(N_LAY):
        y0 = lay_y(k)
        h = 0.5 + 0.12 * k
        pitch = 2.0 + 0.6 * k
        n = int((X1 - X0 - 4.0) / pitch)
        for i in range(1, n, 3):
            xc = X0 + 2.0 + pitch * (i + 0.5)
            pw.append(bx(f"cv_p{k}_{i}", (xc - pitch * 0.3, y0 + 0.6, Z0 + 1.0), (xc + pitch * 0.3, y0 + 0.6 + h, 0.1), m["copper"], conv))
    # via towers that carry power down through the stack
    for i in range(6):
        xc = X0 + 7.0 + (X1 - X0 - 14.0) * i / 5
        pw.append(bx(f"cv_tow{i}", (xc - 0.9, Y_FEOL[1], -3.0), (xc + 0.9, Y_FMET[1], 0.15), m["tin"], conv))
    D.join(pw, "cv_pwr")
    for i in range(10):
        xc = X0 + 4.0 + (X1 - X0 - 8.0) * i / 9
        D.tube(f"cv_bump{i}", (xc, Y_FMET[1], -3.0), (xc, Y_FMET[1] + 3.5, -3.0), 2.2, m["solder"], conv, 14)
    pglow = empty("cv_pglow", root)  # the power towers glowing hot (droop)
    for i in range(6):
        xc = X0 + 7.0 + (X1 - X0 - 14.0) * i / 5
        bx(f"cv_pg{i}", (xc - 0.6, Y_FEOL[1], 0.15), (xc + 0.6, Y_FMET[1], 0.4), m["pwrw"], pglow)

    bsp = empty("bsp", root)
    bx("bs_sub", (X0, Y_SUBT[0], Z0), (X1, Y_SUBT[1], 0.0), m["si"], bsp)
    bx("bs_carrier", (X0, Y_CARR[0], Z0), (X1, Y_CARR[1], 0.0), m["silicon"], bsp)
    bx("bs_bondl", (X0, Y_CARR[0] - 0.2, Z0), (X1, Y_CARR[0] + 0.6, 0.0), m["bond"], bsp)
    bm = []
    for k, (y0, y1) in enumerate(((Y_BMET[1] - 2.2, Y_BMET[1] - 0.4), (Y_BMET[0] + 3.5, Y_BMET[0] + 6.0))):
        bm.append(bx(f"bs_dl{k}", (X0, y1, Z0), (X1, y1 + 0.3, 0.0), m["ild"], bsp))
        pitch = 6.0 + 6.0 * k
        n = int((X1 - X0 - 4.0) / pitch)
        for i in range(n):
            xc = X0 + 2.0 + pitch * (i + 0.5)
            bm.append(bx(f"bs_r{k}_{i}", (xc - pitch * 0.32, y0, Z0 + 1.0), (xc + pitch * 0.32, y1, 0.1), m["copper"], bsp))
    ntsv = []
    for i in range(14):
        xc = X0 + 4.0 + (X1 - X0 - 8.0) * i / 13
        ntsv.append(bx(f"bs_tsv{i}", (xc - 0.4, Y_BMET[1] - 0.4, -2.0), (xc + 0.4, Y_FEOL[0] + 1.4, 0.15), m["tin"], bsp))
    D.join(bm + ntsv, "bs_metal")
    for i in range(10):
        xc = X0 + 4.0 + (X1 - X0 - 8.0) * i / 9
        D.tube(f"bs_bump{i}", (xc, Y_BUMP[0], -3.0), (xc, Y_BUMP[1], -3.0), 2.4, m["solder"], bsp, 14)

    extra = empty("extra", root)  # freed tracks take signal wires
    for k in range(N_LAY):
        y0 = lay_y(k)
        h = 0.5 + 0.12 * k
        pitch = 2.0 + 0.6 * k
        n = int((X1 - X0 - 4.0) / pitch)
        for i in range(1, n, 3):
            xc = X0 + 2.0 + pitch * (i + 0.5)
            bx(f"ex_{k}_{i}", (xc - pitch * 0.18, y0 + 0.6, Z0 + 1.0), (xc + pitch * 0.18, y0 + 0.6 + h, 0.25), m["sigw"], extra)
    return conv, pglow, bsp, extra


def gauge(m, root, x, z):
    """A droop meter: a frame and two fills (tall red = big droop, short green = small)."""
    g = empty("gauge", root)
    bx("ga_back", (x - 4.0, 0.0, z - 2.0), (x + 4.0, 40.0, z), m["gauge"], g)
    for k in range(9):
        bx(f"ga_tick{k}", (x - 4.0, 2.0 + 4.0 * k, z), (x - 2.0, 2.4 + 4.0 * k, z + 0.3), m["ink"], g)
    hi, lo = empty("ga_hi", root), empty("ga_lo", root)
    bx("ga_hif", (x - 1.5, 1.0, z), (x + 3.0, 32.0, z + 0.5), m["warn"], hi)
    bx("ga_lof", (x - 1.5, 1.0, z), (x + 3.0, 12.0, z + 0.5), m["sig"], lo)
    return hi, lo, (x, 40.0, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk, ph, die_glow = b["pk"], b["ph"], b["die_glow"]
    conv, pglow, bsp, extra = slice_(m, root)
    C.magnify(m, root, (-15.0, D.DIE_Y[1], -10.0), (X0 - 2.0, 28.0, -10.0))
    hi, lo, gp = gauge(m, root, X1 + 12.0, -6.0)

    show(conv, [(F(0, 0), F(2, 0.35))])
    show(pglow, [(F(1, 0.1), F(2, 0))])
    show(bsp, [(F(2, 0.35), F(5, 0))])
    show(extra, [(F(3, 0.45), F(5, 0))])
    show(hi, [(F(1, 0.2), F(2, 0))])
    show(lo, [(F(3, 0.3), F(5, 0))])
    show(die_glow, [(F(1, 0), F(2, 0)), (F(3, 0), F(5, 0))])

    # beat 1: power crawls down from the front bumps through the stack (slow, many steps)
    for i in range(6):
        xc = X0 + 7.0 + (X1 - X0 - 14.0) * i / 5
        pts = [(xc, Y_FMET[1] + 4.0, 0.8)]
        for k in range(N_LAY, -1, -1):
            pts.append((xc + (0.8 if k % 2 else -0.8), lay_y(k) + 0.8, 0.8))
        pts.append((xc, Y_FEOL[1], 0.8))
        run(root, f"cv_i{i}", pts, 3, 0.7, m["v12"], 1, 0.05 + 0.04 * i, 0.55 + 0.04 * i, 70)
    rise(root, "cv_heat", ((X0 + X1) / 2, Y_FMET[1] + 4.0, -10.0), 6, 0.8, m["heat"], 1, 0.2, 0.9, 18.0, 50, (30.0, 8.0))
    # beat 2: grinding the substrate: sparks off the back; bond line glows
    rise(root, "grind", ((X0 + X1) / 2, Y_SUBT[0] - 1.0, -12.0), 8, 0.6, m["dim_glow"], 2, 0.35, 0.95, -10.0, 30, (36.0, 10.0))
    # beat 3: power straight up from the back bumps through the rails and nTSVs
    for i in range(10):
        xc = X0 + 4.0 + (X1 - X0 - 8.0) * i / 9
        pts = [(xc, Y_BUMP[0] - 6.0, 0.8), (xc, Y_BMET[0] + 2.0, 0.8), (xc, Y_BMET[1] - 1.0, 0.8), (xc, Y_FEOL[0] + 2.0, 0.8)]
        run(root, f"bs_i{i}", pts, 3, 0.8, m["v12"], [3, 4], 0.05 + 0.02 * i, 0.6 + 0.02 * i, 30)
    for k in (1, 4, 7):
        y = lay_y(k) + 1.2
        run(root, f"sg{k}", [(X0 + 2.0, y, 0.8), (X1 - 2.0, y, 0.8)], 5, 0.6, m["sigw"], [3, 4], 0.4, 0.95, 35)
    # board: power into the package from the phases in every beat but 2
    for side in (-1, 1):
        run(root, f"brd{side}", D.front_path(side), 5, 1.1, m["amp"], [0, 4], 0.1, 0.9, 70)

    C.tags(root, {
        0: [("GPU package", pk["top"]), ("VRM phases", ph["ind"][(-1, 3)]["top"]),
            ("slice of the die, cut open", ((X0 + X1) / 2, Y_CARR[1], -10.0))],
        1: [("power + signal share the front", ((X0 + X1) / 2, Y_FMET[1] + 4.0, 0.0)),
            ("transistors", (X0 + 8.0, Y_FEOL[1], 0.0)), ("thick silicon substrate", (X1 - 10.0, 8.0, 0.0)),
            ("IR droop: high", gp)],
        2: [("bonded to a carrier wafer", ((X0 + X1) / 2, Y_CARR[1], 0.0)), ("silicon thinned to microns", (X0 + 10.0, Y_SUBT[1], 0.0)),
            ("nano-TSVs + back power rails", (X1 - 14.0, Y_BMET[0] + 4.0, 0.0))],
        3: [("power straight up from below", (X0 + 10.0, Y_BUMP[1], 0.0)), ("front: signals only", ((X0 + X1) / 2, Y_FMET[1], 0.0)),
            ("IR droop: low", gp)],
        4: [("Intel PowerVia (18A)", ((X0 + X1) / 2, Y_CARR[1], -10.0)), ("TSMC A16 Super Power Rail", (X1 - 10.0, Y_BUMP[0], 0.0)),
            ("tools: AMAT, LRCX", pk["top"])],
    })
    xm, ym = (X0 + X1) / 2, (Y_BUMP[0] + Y_CARR[1]) / 2
    C.done(SLUG, BEATS, [
        frame((40.0, 0.0, -70.0), 380.0, 0.30, 0.55, pad=1.0),
        frame((xm + 4.0, ym, -6.0), 100.0, 0.12, 0.10),
        frame((xm, ym - 4.0, -6.0), 95.0, -0.18, 0.12),
        frame((xm + 4.0, ym, -6.0), 100.0, 0.10, 0.06),
        [(0.16, frame((xm, ym, -8.0), 110.0, 0.25, 0.20)), (0.6, frame((80.0, 0.0, -60.0), 320.0, 0.25, 0.5, pad=1.0))],
    ], root)


if __name__ == "__main__":
    build()
