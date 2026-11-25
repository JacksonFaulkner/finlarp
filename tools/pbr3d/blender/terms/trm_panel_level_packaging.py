"""TRM_PANEL_LEVEL_PACKAGING: the Terms-tab overview for panel-level packaging.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_panel_level_packaging.py

Scale 1 unit = 2 mm. A 300 mm round wafer and a 510 x 515 mm panel lie side by side on a tool
table, both tiled with the same large AI package sites (~57 mm pitch with saw street). Sites that
fit light up; partial sites at the wafer edge glow red as waste. A process gantry sweeps both,
a bowed panel shows warpage, and a sample package is drawn on the panel (interposer, GPU, HBM).

Beats:
  0 wafer   the round wafer and how few big packages fit
  1 panel   the panel beside it, many more sites
  2 pass    one gantry pass treats every site
  3 warp    a big thin panel bows; edge sites lose yield
  4 status  early volume, tickers
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, P, empty, key, show, tube  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, blink, mat  # noqa: E402

S = 0.5  # units per mm
SITE, PITCH = 55.0 * S, 58.0 * S
WC, WR = (-170.0, -100.0), 150.0 * S
PW, PD = 510.0 * S, 515.0 * S
PC = (110.0, -150.0)


def wafer_sites():
    full, part = [], []
    n = 4
    for i in range(-n, n):
        for j in range(-n, n):
            cx, cz = (i + 0.5) * PITCH, (j + 0.5) * PITCH
            corners = [math.hypot(cx + a * SITE / 2, cz + b * SITE / 2) for a in (-1, 1) for b in (-1, 1)]
            if max(corners) < WR - 3.0:
                full.append((WC[0] + cx, WC[1] + cz))
            elif min(corners) < WR:
                part.append((WC[0] + cx, WC[1] + cz))
    return full, part


def panel_sites():
    nx, nz = int((PW - 6.0) // PITCH), int((PD - 6.0) // PITCH)
    out = []
    for i in range(nx):
        for j in range(nz):
            out.append((PC[0] - nx * PITCH / 2 + (i + 0.5) * PITCH, PC[1] - nz * PITCH / 2 + (j + 0.5) * PITCH))
    return out, nx, nz


WFULL, WPART = wafer_sites()
PSITES, NX, NZ = panel_sites()
NW, NP = len(WFULL), len(PSITES)

SLUG = "TRM_PANEL_LEVEL_PACKAGING"
BEATS = [
    (f"A 300 mm wafer fits only ~{NW} big AI packages",
     "Advanced AI packages such as CoWoS put a GPU and several HBM stacks on a silicon or organic interposer that can "
     f"be 50-80 mm across. Square sites that size tile badly inside a 300 mm circle: here only {NW} of 55 mm fit, and "
     "the curved edge is wasted. As packages grow, the waste grows."),
    (f"A 510 x 515 mm panel holds {NP}: ~{NP / max(1, NW):.0f}x more",
     "Panel-level packaging builds the same packages on a large rectangle, glass or organic, borrowed from PCB and "
     f"display-glass tooling. A 510 x 515 mm panel has about 3.7x the area of a 300 mm wafer and wastes almost no "
     f"edge, so it fits {NP} of these sites against {NW}."),
    ("One pass treats every site: cost per package falls",
     "Most steps (coating, exposure, plating, molding, placement) take roughly the same time per substrate, whatever its "
     "size. More packages per substrate means more packages per tool-hour and less edge scrap, which is why TSMC, ASE "
     "and others see panels as the way to cut the cost of big AI packages."),
    ("Big thin panels warp, and every defect costs more",
     "A half-metre sheet of thin mold or glass bends as it heats and cools, so features at the edges drift out of focus "
     "and alignment. Panel lithography and handling tools are less mature than wafer tools, and a bad panel scraps "
     "more packages at once. Yield, warpage and tooling are the hurdles."),
    ("Early volume now: pilots across OSATs and foundries",
     "Samsung and PTI already run fan-out panels for smaller chips; for AI-size packages TSMC (CoPoS), ASE, Amkor and "
     "Intel (glass core) are building pilot lines, with volume expected late in the decade. Related: Amkor (AMKR), "
     "ASE (ASX), TSMC (TSM)."),
]


def mats(m):
    m["glass_p"] = mat("pl_glass", (0.55, 0.70, 0.72), rough=0.15)
    m["wafer_s"] = mat("pl_wafer", (0.40, 0.42, 0.52), metal=0.6, rough=0.2)
    m["ok"] = mat("pl_ok", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=1.4)
    m["waste"] = mat("pl_waste", (1.0, 0.3, 0.2), emit=(1.0, 0.25, 0.15), strength=0.9)
    m["beam"] = mat("pl_beam", (0.5, 0.75, 1.0), emit=(0.4, 0.7, 1.0), strength=2.5)


def site(m, g, name, x, z, y, detailed=False):
    h = SITE / 2
    bx(f"{name}_ip", (x - h, y, z - h), (x + h, y + 0.8, z + h), m["silicon"], g)
    bx(f"{name}_gpu", (x - h * 0.45, y + 0.8, z - h * 0.55), (x + h * 0.45, y + 2.6, z + h * 0.55), m["die"], g)
    for sx in (-1, 1):
        for k in range(2 if not detailed else 3):
            zz = z - h * 0.5 + k * (h if not detailed else h * 0.5)
            bx(f"{name}_hbm{sx}{k}", (x + sx * h * 0.55 - 3.0, y + 0.8, zz - 2.8), (x + sx * h * 0.55 + 3.0, y + 4.0, zz + 2.8), m["hbm"], g)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("table", (-270.0, -10.0, -300.0), (260.0, -2.0, 20.0), m["dark"], root)
    # wafer
    tube("wafer", (WC[0], -2.0, WC[1]), (WC[0], 0.0, WC[1]), WR, m["wafer_s"], root, 96)
    bx("w_notch", (WC[0] - 2.0, -2.2, WC[1] + WR - 2.0), (WC[0] + 2.0, 0.2, WC[1] + WR + 0.2), m["dark"], root)
    wg = empty("w_sites", root)
    for k, (x, z) in enumerate(WFULL):
        site(m, wg, f"ws{k}", x, z, 0.0)
    wok, wbad = empty("w_ok", root), empty("w_bad", root)
    for k, (x, z) in enumerate(WFULL):
        bx(f"wok{k}", (x - SITE / 2, 0.05, z - SITE / 2), (x + SITE / 2, 0.3, z + SITE / 2), m["ok"], wok)
    for k, (x, z) in enumerate(WPART):
        dx, dz = x - WC[0], z - WC[1]
        r = math.hypot(dx, dz)
        lim = WR - SITE * 0.25
        if r > lim:
            x, z = WC[0] + dx * lim / r, WC[1] + dz * lim / r
        bx(f"wbad{k}", (x - SITE * 0.2, 0.05, z - SITE * 0.2), (x + SITE * 0.2, 0.3, z + SITE * 0.2), m["waste"], wbad)
    show(wok, [(F(0, 0.3), F(2, 0))])
    show(wbad, [(F(0, 0.5), F(1, 0)), (F(3, 0.0), F(4, 0))])
    # panel (flat) and its sites
    flat = empty("panel_flat", root)
    bx("panel", (PC[0] - PW / 2, -2.0, PC[1] - PD / 2), (PC[0] + PW / 2, 0.0, PC[1] + PD / 2), m["glass_p"], flat)
    for k, (x, z) in enumerate(PSITES):
        site(m, flat, f"ps{k}", x, z, 0.0, detailed=(k == NZ * (NX // 2) + NZ - 1))
    D.present(flat, [(F(0, 0), F(3, 0.15)), (F(4, 0), F(5, 0))])
    pok = empty("p_ok", root)
    for k, (x, z) in enumerate(PSITES):
        bx(f"pok{k}", (x - SITE / 2, 0.05, z - SITE / 2), (x + SITE / 2, 0.3, z + SITE / 2), m["ok"], pok)
    show(pok, [(F(1, 0.3), F(2, 0))])
    # warped panel: strips bowed (higher at the edges)
    warp = empty("panel_warp", root)
    nstrip = 24
    for i in range(nstrip):
        xa = PC[0] - PW / 2 + PW * i / nstrip
        xb = xa + PW / nstrip
        u = (xa + xb) / 2 - PC[0]
        y = 22.0 * (u / (PW / 2)) ** 2
        bx(f"warp{i}", (xa, y - 2.0, PC[1] - PD / 2), (xb + 0.6, y, PC[1] + PD / 2), m["glass_p"], warp)
        if abs(u) > PW * 0.3:
            bx(f"warpbad{i}", (xa, y, PC[1] - PD / 2), (xb, y + 0.3, PC[1] + PD / 2), m["waste"], warp)
    D.present(warp, [(F(3, 0.15), F(4, 0))])
    # gantry sweeping across both
    gan = empty("gantry", root)
    gh = empty("gantry_h", gan)
    for z in (20.0, -300.0):
        bx(f"gleg{z:.0f}", (-4.0, 0.0, z - 4.0), (4.0, 50.0, z + 4.0), m["alu"], gh)
    bx("gbar", (-5.0, 50.0, -304.0), (5.0, 58.0, 24.0), m["alu"], gh)
    bx("gbeam", (-1.2, 1.0, -290.0), (1.2, 49.0, 10.0), m["beam"], gh)
    for (b, xa, xb) in ((2, -260.0, 250.0),):
        key(gh, F(b, 0.05), "location", P(xa, 0.0, 0.0), linear=True)
        key(gh, F(b, 0.9), "location", P(xb, 0.0, 0.0), linear=True)
    D.present(gan, [(F(2, 0.0), F(3, 0))])
    # sites flash as the beam passes
    cols = {}
    for x, z in PSITES + WFULL:
        cols.setdefault(round(x, 1), []).append((x, z))
    for k, (cx, pts) in enumerate(sorted(cols.items())):
        g = empty(f"flash{k}", root)
        for j, (x, z) in enumerate(pts):
            bx(f"fl{k}_{j}", (x - SITE / 2, 0.35, z - SITE / 2), (x + SITE / 2, 0.6, z + SITE / 2), m["ok"], g)
        u = 0.05 + 0.85 * (cx + 260.0) / 510.0
        show(g, [(F(2, u), F(2, min(0.98, u + 0.06)))])
    # tool-hour beads: packages leaving the table
    for k in range(6):
        x = PC[0] - PW / 2 + 20.0 + 40.0 * k
        run(root, f"out{k}", [(x, 4.0, 2.0), (x, 4.0, 30.0)], 3, 1.6, m["sig"], 2, 0.5 + 0.05 * k, 0.95, 30)
    run(root, "outw", [(WC[0], 4.0, WC[1] + WR), (WC[0], 4.0, 30.0)], 2, 1.6, m["sig"], 2, 0.5, 0.95, 30)
    ds = PSITES[NZ * (NX // 2) + NZ - 1]
    C.tags(root, {
        0: [("300 mm wafer", (WC[0] - WR * 0.7, 0.0, WC[1] + WR * 0.7)), (f"{NW} full 55 mm sites", (WFULL[0][0], 2.0, WFULL[0][1])),
            ("edge sites wasted", (WPART[0][0], 0.3, WPART[0][1]))],
        1: [("510 x 515 mm panel", (PC[0] + PW / 2, 0.0, PC[1] + PD / 2)), (f"{NP} sites, almost no edge loss", (PC[0], 2.0, PC[1])),
            ("same 300 mm wafer", (WC[0], 0.0, WC[1]))],
        2: [("one pass covers every site", (0.0, 56.0, -140.0)), ("more packages per tool-hour", (PC[0], 4.0, 20.0)),
            ("GPU + HBM on interposer", (ds[0], 4.0, ds[1]))],
        3: [("panel bows as it cools", (PC[0] + PW / 2, 22.0, PC[1])), ("edge sites drift out of focus", (PC[0] - PW * 0.42, 18.0, PC[1])),
            ("wafer tools are more mature", (WC[0], 0.0, WC[1]))],
        4: [("pilot lines, volume ~2028+", (PC[0], 2.0, PC[1])), ("AMKR, ASX, TSM", (WC[0], 2.0, WC[1]))],
    })
    C.done(SLUG, BEATS, [
        frame((WC[0], 0.0, WC[1]), 170.0, 0.20, 0.95),
        frame((-30.0, 0.0, -140.0), 470.0, 0.15, 0.95, pad=1.0),
        frame((-20.0, 15.0, -130.0), 500.0, 0.35, 0.60, pad=1.0),
        frame((PC[0], 10.0, PC[1]), 300.0, 0.05, 0.18),
        frame((-30.0, 0.0, -140.0), 480.0, 0.30, 0.75, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
