"""TRM_GLASS_FIBER_CLOTH: the Terms-tab overview for glass fiber cloth.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_glass_fiber_cloth.py

Writes assets/term_TRM_GLASS_FIBER_CLOTH.glb. Captions live in specs/terms/TRM_GLASS_FIBER_CLOTH.json.

A glass mill: a melt furnace with a platinum bushing drawing glowing filaments down onto a spinning
winder, a loom where a shuttle carries weft through the warp, a magnified weave on the bench (each
yarn a bundle of filaments), a resin dip line turning cloth into prepreg, and a board signal that runs
past the glass.

Beats:
  0 draw     melt -> bushing -> filaments -> winder
  1 weave    warp + weft on a loom, shuttle running
  2 yarn     magnified over-under weave, a yarn is hundreds of filaments
  3 resin    cloth through a resin bath into prepreg, signals in the board
  4 supply   low-Dk / low-CTE grades from a few makers; tickers
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
import sand_overview as O  # noqa: E402
from sand_overview import mat, tube, disc  # noqa: E402
from term_common import F, P, bx, empty, show, spin  # noqa: E402
from power_vrm_detail import frame, rise, run  # noqa: E402

SLUG = "TRM_GLASS_FIBER_CLOTH"
BEATS = [
    ("Molten glass is drawn through a platinum bushing into fine filaments",
     "Glass batch is melted near 1,500 C and flows into a platinum-rhodium bushing with thousands of tiny "
     "nozzles. Filaments 5 to 9 microns thick are pulled out and cooled in a fraction of a second, then gathered "
     "and wound onto a spinning drum. The draw speed sets how thin each filament is."),
    ("A loom weaves the yarn into a thin, even cloth",
     "Bundles of filaments are twisted into yarn and set up as warp threads along the loom. The weft is shot "
     "across between them, over one and under the next, row after row. PCB cloth is very thin, some styles "
     "under 20 microns, and must be flat and even with no gaps."),
    ("Each yarn in the weave is a bundle of hundreds of glass filaments",
     "Up close the cloth is an over-under grid of flattened yarns, and each yarn holds a few hundred filaments. "
     "Glass gives the laminate its strength and keeps it from swelling with heat. Where glass and resin "
     "alternate, a fast signal sees a bumpy dielectric, so cloth for AI boards is spread flat to even it out."),
    ("Soaked in resin, the cloth becomes prepreg, the core of every laminate",
     "The cloth runs through a resin bath and a drying oven to become prepreg, which is pressed with copper "
     "into copper clad laminate and package substrates. Ordinary E-glass works for common boards. AI boards "
     "and substrates need low-Dk glass so signals lose less, and low-expansion T-glass so big chips stay flat."),
    ("Only a few mills make the special grades, and they ran short",
     "Low-Dk, T-glass and quartz yarns come mostly from a handful of makers in Japan and Taiwan. In 2024 and "
     "2025 shortages of these grades held back laminate and substrate output as AI demand grew. "
     "Related: Owens Corning (OC), Nittobo (3110.T), AGC (5201.T)."),
]

FX = -110.0          # furnace / bushing x
LOOM = (0.0, 0.0, -40.0)
BENCH = (180.0, 20.0, -10.0)
DIP = (-40.0, 0.0, 50.0)


def mats(m):
    m["gf_glass"] = mat("gf_glass", (0.90, 0.94, 0.97), metal=0.1, rough=0.2)
    m["gf_fil"] = mat("gf_fil", (1.0, 0.75, 0.40), emit=(1.0, 0.60, 0.25), strength=2.5)
    m["gf_melt"] = mat("gf_melt", (1.0, 0.5, 0.2), emit=(1.0, 0.45, 0.12), strength=3.0)
    m["gf_pt"] = mat("gf_pt", (0.85, 0.86, 0.88), metal=1.0, rough=0.15)
    m["gf_brick"] = mat("gf_brick", (0.55, 0.35, 0.28), rough=0.85)
    m["gf_resin"] = mat("gf_resin", (0.85, 0.62, 0.20), rough=0.2, alpha=0.6)
    m["gf_pp"] = mat("gf_pp", (0.85, 0.75, 0.40), rough=0.55)
    m["gf_wood"] = mat("gf_wood", (0.45, 0.33, 0.22), rough=0.8)
    m["gf_sig"] = mat("gf_sig", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=4.0)
    m["gf_shut"] = mat("gf_shut", (0.3, 0.65, 1.0), emit=(0.3, 0.65, 1.0), strength=3.0)
    m["gf_cu"] = mat("gf_cu", (0.90, 0.50, 0.28), metal=1.0, rough=0.25)


def weave(m, parent, name, x0, x1, z0, z1, y, pitch, amp, r, mt="gf_glass", flat=1.0):
    g = empty(name, parent)
    nx, nz = int((z1 - z0) / pitch), int((x1 - x0) / pitch)
    for i in range(nx + 1):
        z = z0 + i * pitch
        pts = [(x0 + k * pitch / 2, y + amp * (1 if (k + i) % 2 else -1), z) for k in range(2 * nz + 1)]
        K.pipe(m, g, f"{name}_wp{i}", pts, r, mt)
    for j in range(nz + 1):
        x = x0 + j * pitch
        pts = [(x, y + amp * (-1 if (k + j) % 2 else 1), z0 + k * pitch / 2) for k in range(2 * nx + 1)]
        K.pipe(m, g, f"{name}_wf{j}", pts, r, mt)
    return g


def furnace(m, root):
    g = empty("furnace", root)
    bx("fu_body", (FX - 30, 70.0, -70.0), (FX + 30, 100.0, -30.0), m["gf_brick"], g)
    bx("fu_melt", (FX - 26, 96.0, -66.0), (FX + 26, 100.5, -34.0), m["gf_melt"], g)
    bx("fu_bush", (FX - 14, 66.0, -54.0), (FX + 14, 70.0, -46.0), m["gf_pt"], g)
    for x in (FX - 28, FX + 28):
        tube(f"fu_leg{x}", (x, 0.0, -50.0), (x, 70.0, -50.0), 2.5, m["sup_steel"], g)
    # filaments fan from bushing into a gathering shoe, then down to the winder
    shoe = (FX, 30.0, -50.0)
    for k in range(14):
        x = FX - 13 + k * 2.0
        tube(f"fu_fil{k}", (x, 66.0, -50.0), shoe, 0.18, m["gf_fil"], g, 6)
    disc("fu_shoe", shoe, 2.0, 1.5, m["gf_pt"], g)
    tube("fu_strand", shoe, (FX, 14.0, -50.0), 0.5, m["gf_glass"], g, 8)
    # winder: a drum turning about y? use a vertical pivot with cake
    wind = empty("fu_wind", g, P(FX, 8.0, -50.0))
    disc("fu_cake", (0.0, 0.0, 0.0), 9.0, 10.0, m["gf_glass"], wind, 32)
    for k in range(6):
        a = 2 * math.pi * k / 6
        bx(f"fu_rib{k}", (9.0 * math.cos(a) - 0.6, -5.2, 9.0 * math.sin(a) - 0.6),
           (9.0 * math.cos(a) + 0.6, 5.2, 9.0 * math.sin(a) + 0.6), m["gf_pt"], wind)
    bx("fu_wbase", (FX - 12, 0.0, -62.0), (FX + 12, 3.0, -38.0), m["sup_steel"], g)
    return g, wind, shoe


def loom(m, root):
    g = empty("loom", root)
    x0, x1, z0, z1 = LOOM[0] - 40, LOOM[0] + 40, LOOM[2] - 25, LOOM[2] + 25
    for x in (x0 - 4, x1 + 4):
        for z in (z0, z1):
            tube(f"lm_post{x}_{z}", (x, 0.0, z), (x, 32.0, z), 1.6, m["gf_wood"], g)
        tube(f"lm_rail{x}", (x, 32.0, z0), (x, 32.0, z1), 1.4, m["gf_wood"], g)
    tube("lm_beam_back", (x0 - 4, 22.0, z0), (x1 + 4, 22.0, z0), 4.0, m["gf_wood"], g, 20)
    tube("lm_cloth_roll", (x0 - 4, 22.0, z1), (x1 + 4, 22.0, z1), 5.0, m["gf_glass"], g, 20)
    # warp threads, alternate up/down sheds
    for k in range(21):
        x = x0 + 4 + k * 3.6
        dy = 2.0 if k % 2 else -2.0
        K.pipe(m, g, f"lm_warp{k}", [(x, 22.0, z0 + 4), (x, 22.0 + dy, LOOM[2] - 2), (x, 22.0, LOOM[2] + 6)],
               0.35, "gf_glass")
    # woven part
    weave(m, g, "lm_woven", x0 + 4, x1 - 4, LOOM[2] + 6, z1 - 4, 22.0, 3.6, 0.3, 0.45)
    # heddle frame
    bx("lm_heddle", (x0, 28.0, LOOM[2] - 3), (x1, 30.0, LOOM[2] - 1), m["gf_wood"], g)
    return g, (x0, x1)


def bench_weave(m, root):
    """Magnified weave: flat yarns made of filament bundles."""
    g = empty("bw", root)
    cx, cy, cz = BENCH
    bx("bw_table", (cx - 55, 0.0, cz - 40), (cx + 55, cy - 8, cz + 40), m["sup_steel"], g)
    pitch, amp = 18.0, 2.2
    x0, x1, z0, z1 = cx - 45, cx + 45, cz - 27, cz + 27
    nx, nz = int((z1 - z0) / pitch), int((x1 - x0) / pitch)
    offs = [(-1.4, -0.6), (0.0, -0.6), (1.4, -0.6), (-0.7, 0.6), (0.7, 0.6), (-2.6, 0.0), (2.6, 0.0)]
    for i in range(nx + 1):
        z = z0 + i * pitch
        for f, (dz, dy) in enumerate(offs):
            pts = [(x0 + k * pitch / 2, cy + dy + amp * (1 if (k + i) % 2 else -1), z + dz * 1.6) for k in range(2 * nz + 1)]
            K.pipe(m, g, f"bw_wp{i}_{f}", pts, 1.0, "gf_glass")
    for j in range(nz + 1):
        x = x0 + j * pitch
        for f, (dx, dy) in enumerate(offs):
            pts = [(x + dx * 1.6, cy + dy + amp * (-1 if (k + j) % 2 else 1), z0 + k * pitch / 2) for k in range(2 * nx + 1)]
            K.pipe(m, g, f"bw_wf{j}_{f}", pts, 1.0, "gf_glass")
    # resin pocket blocks (translucent) between yarns
    resin = empty("bw_resin", g)
    bx("bw_resin_s", (x0 - 2, cy - 6, z0 - 3), (x1 + 2, cy + 6, z1 + 3), m["gf_resin"], resin)
    return g, resin, (x0, x1, z0, z1)


def dip_line(m, root):
    g = empty("dip", root)
    dx, _, dz = DIP
    tube("dp_roll_in", (dx - 60, 20.0, dz - 15), (dx - 60, 20.0, dz + 15), 7.0, m["gf_glass"], g, 24)
    tank, pts = K.tank(m, g, "dp_tank", (dx - 25, 0.0, dz), 15.0, 14.0)
    disc("dp_bath", (dx - 25, 12.0, dz), 14.0, 1.0, m["gf_resin"], g)
    tube("dp_roller", (dx - 25, 6.0, dz - 15), (dx - 25, 6.0, dz + 15), 2.5, m["sup_steel"], g)
    bx("dp_oven", (dx + 5, 0.0, dz - 18), (dx + 55, 30.0, dz + 18), m["gf_brick"], g)
    # web path
    web = [(dx - 60, 27.0), (dx - 25, 6.0 - 2.5), (dx + 5, 18.0), (dx + 55, 18.0), (dx + 70, 18.0)]
    for k in range(len(web) - 1):
        (xa, ya), (xb, yb) = web[k], web[k + 1]
        mt = "gf_glass" if k == 0 else "gf_pp"
        L = math.hypot(xb - xa, yb - ya)
        n = max(1, int(L / 4))
        for s in range(n):
            u0, u1 = s / n, (s + 1) / n
            bx(f"dp_web{k}_{s}", (xa + (xb - xa) * u0, min(ya + (yb - ya) * u0, ya + (yb - ya) * u1) - 0.3, dz - 13),
               (xa + (xb - xa) * u1, max(ya + (yb - ya) * u0, ya + (yb - ya) * u1) + 0.3, dz + 13), m[mt], g)
    # stack of prepreg sheets
    for k in range(6):
        bx(f"dp_sheet{k}", (dx + 72, k * 1.2, dz - 13), (dx + 100, k * 1.2 + 0.9, dz + 13), m["gf_pp"], g)
    path = [(x, y + 1.2, dz) for x, y in web]
    return g, path, pts


def board_xsec(m, root):
    """A laminate cut-away: copper trace over a resin + glass core, signal running."""
    g = empty("xs", root)
    x0, x1, z = 60.0, 140.0, 50.0
    bx("xs_core", (x0, 0.0, z - 10), (x1, 8.0, z + 10), m["gf_resin"], g)
    for k in range(9):
        tube(f"xs_yarn{k}", (x0 + 4 + k * 9.0, 4.0, z - 10), (x0 + 4 + k * 9.0, 4.0, z + 10), 1.6, m["gf_glass"], g, 12)
    K.pipe(m, g, "xs_fill", [(x0 + i * 4.0, 4.0 + 1.4 * (1 if i % 2 else -1), z) for i in range(21)], 0.9, "gf_glass")
    bx("xs_trace", (x0, 8.0, z - 1.5), (x1, 8.8, z + 1.5), m["gf_cu"], g)
    bx("xs_gnd", (x0, -0.8, z - 10), (x1, 0.0, z + 10), m["gf_cu"], g)
    return g, (x0, x1, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    mats(m)
    bx("floor", (-160.0, -3.0, -90.0), (250.0, 0.0, 90.0), m["sup_steel"], root)

    fu, wind, shoe = furnace(m, root)
    spin(wind, [0, 4], turns=3.0)
    run(root, "fu_drip", [(FX, 66.0, -50.0), shoe, (FX, 14.0, -50.0)], 8, 0.6, m["gf_fil"], [0], 0.0, 0.85, 25)
    rise(root, "fu_heat", (FX, 101.0, -50.0), 8, 0.8, m["gf_melt"], [0], 0.0, 0.85, h=18.0, life=40,
         spread=(22.0, 12.0))

    lm, (lx0, lx1) = loom(m, root)
    sh_path = [(lx0 - 2, 22.0, LOOM[2] + 3), (lx1 + 2, 22.0, LOOM[2] + 3), (lx0 - 2, 22.0, LOOM[2] + 4)]
    run(root, "lm_shuttle", sh_path, 3, 1.4, m["gf_shut"], [1], 0.0, 0.6, 45)

    bw, resin, (wx0, wx1, wz0, wz1) = bench_weave(m, root)
    show(resin, [(F(3, 0), F(5, 0))])
    C.magnify(m, root, (LOOM[0] + 20, 23.0, LOOM[2] + 12), (BENCH[0] - 50, 25.0, BENCH[2]), name="mag")

    dp, dpath, tpts = dip_line(m, root)
    run(root, "dp_web_b", dpath, 6, 1.0, m["gf_shut"], [3], 0.0, 0.8, 40)

    xs, (xx0, xx1, xz) = board_xsec(m, root)
    run(root, "xs_sig", [(xx0 + 2, 10.0, xz), (xx1 - 2, 10.0, xz)], 5, 1.0, m["gf_sig"], [3, 4], 0.1, 0.8, 35)

    C.tags(root, {
        0: [("melt ~1,500 C", (FX + 30, 100.0, -50.0)), ("platinum bushing nozzles", (FX + 14, 68.0, -46.0)),
            ("filaments 5-9 um", (FX + 6, 48.0, -50.0)), ("winder pulls the strand", (FX + 9, 8.0, -41.0))],
        1: [("warp: yarns along the loom", (lx0 + 10, 23.0, LOOM[2] - 12)), ("shuttle carries the weft", (lx1, 22.0, LOOM[2] + 3)),
            ("finished cloth roll", (lx1, 27.0, LOOM[2] + 25))],
        2: [("yarn: hundreds of filaments", (wx0 + 9, BENCH[1] + 3, wz1)), ("over one, under the next", (BENCH[0], BENCH[1] + 3, BENCH[2])),
            ("gaps make a bumpy Dk", (wx1, BENCH[1], wz0))],
        3: [("resin bath", tpts["top"]), ("drying oven -> prepreg", (DIP[0] + 30, 30.0, DIP[2])),
            ("glass in the board core", (xx0 + 40, 4.0, xz + 10)), ("resin fills the weave", (BENCH[0] + 45, BENCH[1] + 6, BENCH[2]))],
        4: [("low-Dk, T-glass, quartz", (BENCH[0], BENCH[1] + 6, BENCH[2])), ("few mills: Japan, Taiwan", (FX + 30, 100.0, -50.0)),
            ("OC, 3110.T, 5201.T", (DIP[0] + 30, 30.0, DIP[2]))],
    })
    C.done(SLUG, BEATS, [
        [(0.0, frame((FX, 55.0, -50.0), 110.0, 0.35, 0.15)), (1.0, frame((FX, 40.0, -50.0), 90.0, 0.15, 0.10))],
        frame((LOOM[0], 20.0, LOOM[2]), 100.0, 0.25, 0.50),
        [(0.0, frame((BENCH[0], BENCH[1], BENCH[2]), 110.0, 0.30, 0.55)), (1.0, frame((BENCH[0], BENCH[1], BENCH[2]), 70.0, 0.15, 0.45))],
        frame((40.0, 10.0, 40.0), 190.0, 0.15, 0.45),
        frame((40.0, 30.0, -10.0), 300.0, 0.30, 0.40),
    ], root)


if __name__ == "__main__":
    build()
