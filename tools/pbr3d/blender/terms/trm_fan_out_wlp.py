"""TRM_FAN_OUT_WLP: the Terms-tab overview for fan-out wafer-level packaging.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_fan_out_wlp.py

Left: a round carrier wafer being populated with known-good dies by a pick-and-place head, then
over-molded into a reconstituted wafer. Right: one finished fan-out package ~25x life size, cut
open at z = 0: die in epoxy mold, three copper redistribution layers (RDL) in polyimide spreading
the die pads out to solder balls well beyond the die edge, and (last beat) through-mold vias
carrying a DRAM package on top (InFO-PoP).

Beats:
  0 place     dies land face-down on the carrier
  1 mold      epoxy mold covers them: a reconstituted wafer
  2 RDL       the package cut open, copper lines leaving the die footprint
  3 fan out   signals run from the die pads out to balls beyond the edge
  4 InFO-PoP  through-mold vias and a memory package on top
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, P, empty, key, show, tube, ball  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_FAN_OUT_WLP"
BEATS = [
    ("Known-good dies are placed face-down on a round carrier",
     "Fan-out starts after the wafer is diced. Each die is tested first, and only the known-good ones are picked up and "
     "placed face-down on a temporary carrier, spaced wider apart than they sat on the original wafer. That extra room "
     "around each die is what the package will use for wiring."),
    ("Epoxy mold fills around them: a reconstituted wafer",
     "The carrier is flooded with epoxy mold compound and cured, locking every die in a disc of plastic the same size as a "
     "silicon wafer. The carrier is then released. The result looks like a wafer and runs on wafer tools, but it is "
     "mostly mold with dies embedded in it."),
    ("Copper redistribution layers spread the pads outward",
     "On the die side, thin layers of polyimide and plated copper are built up like a tiny circuit board: the "
     "redistribution layer (RDL). Lines a few microns wide leave each die pad and route outward, past the die edge, "
     "onto the mold around it. No silicon interposer and no laminate substrate are needed."),
    ("Signals fan out to solder balls beyond the die edge",
     "A die's pads are packed at tens of microns; a phone board needs balls about 0.35-0.5 mm apart. Fan-in packaging "
     "can only put balls under the die itself, which caps the I/O count. Fan-out uses the mold area too, so a small die "
     "can still have hundreds of balls, with short, thin wiring that keeps the package low and fast."),
    ("Through-mold vias stack memory on top: TSMC's InFO",
     "Copper pillars through the mold carry signals up to a DRAM package stacked on top. That is InFO-PoP, used for Apple's "
     "phone processors since 2016; bigger variants (InFO-oS, CoWoS-R) use fan-out RDL to join chiplets for AI and "
     "networking. Main players: TSMC (TSM), ASE (ASX), Amkor (AMKR), and JCET in China."),
]

WC = (-120.0, -70.0)  # carrier wafer centre (x, z)
WR = 62.0
PX0, PX1 = 20.0, 210.0  # package cross-section x extents
DX0, DX1 = 85.0, 145.0  # die
Y_BALL = 7.0  # ball tops / RDL bottom
RDL = [(7.0, 9.0), (9.0, 11.0), (11.0, 13.0), (13.0, 15.0)]  # four dielectric bands
Y_DIE = (15.0, 31.0)
Y_MOLD = 35.0
PZ0 = -44.0


def mats(m):
    m["pi"] = mat("fo_pi", (0.78, 0.48, 0.18), rough=0.45)  # polyimide, amber
    m["moldc"] = mat("fo_mold", (0.10, 0.10, 0.12), rough=0.7)
    m["carrier"] = mat("fo_glass", (0.70, 0.80, 0.85), metal=0.0, rough=0.12)
    m["edge"] = mat("fo_edge", (0.4, 1.0, 0.6), emit=(0.35, 1.0, 0.55), strength=1.8)


def wafer(m, root):
    """Carrier, dies (in 4 batches) and the mold disc. Returns batch groups, mold group, head."""
    x0, z0 = WC
    tube("carrier", (x0, -4.0, z0), (x0, 0.0, z0), WR, m["carrier"], root, 72)
    bx("carrier_notch", (x0 - 3.0, -4.2, z0 + WR - 3.0), (x0 + 3.0, 0.2, z0 + WR + 0.5), m["dark"], root)
    pitch, half = 16.0, 5.5
    sites = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            x, z = x0 + i * pitch, z0 + j * pitch
            if math.hypot(i * pitch, j * pitch) + half * 1.5 < WR - 4.0:
                sites.append((x, z))
    batches = [empty(f"dies{k}", root) for k in range(4)]
    for n, (x, z) in enumerate(sites):
        g = batches[min(3, n * 4 // len(sites))]
        bx(f"d{n}", (x - half, 0.0, z - half), (x + half, 2.5, z + half), m["die"], g)
        bx(f"dp{n}", (x - half + 1.0, 2.5, z - half + 1.0), (x + half - 1.0, 2.7, z + half - 1.0), m["silicon"], g)
    for k, g in enumerate(batches):
        show(g, [(F(0, 0.15 + 0.18 * k), F(1, 0.35))])
    mold = empty("mold_disc", root)
    tube("mold_d", (x0, 0.0, z0), (x0, 4.0, z0), WR - 1.0, m["moldc"], mold, 72)
    for i in range(-4, 5):  # scribe lines on the mold
        c = i * pitch + pitch / 2
        L = math.sqrt(max(0.0, (WR - 6.0) ** 2 - c * c))
        if L > 4:
            bx(f"sx{i}", (x0 + c - 0.2, 4.0, z0 - L), (x0 + c + 0.2, 4.15, z0 + L), m["dim_glow"], mold)
            bx(f"sz{i}", (x0 - L, 4.0, z0 + c - 0.2), (x0 + L, 4.15, z0 + c + 0.2), m["dim_glow"], mold)
    show(mold, [(F(1, 0.3), F(2, 0.0)), (F(2, 0.0), F(5, 0))])
    # mold being dispensed: a nozzle and glowing pour
    head = empty("pp_head", root)
    tube("pp_noz", (0.0, 3.0, 0.0), (0.0, 30.0, 0.0), 1.6, m["alu"], head, 16)
    bx("pp_arm", (-2.5, 30.0, -2.5), (2.5, 34.0, 40.0), m["alu"], head)
    bx("pp_die", (-5.5, 0.4, -5.5), (5.5, 2.9, 5.5), m["die"], head)
    O_head = empty("pp_holder", root)
    head.parent = O_head
    # head drops onto a few sites in beat 0
    pick = sites[len(sites) // 2 - 3: len(sites) // 2 + 1]
    for k, (x, z) in enumerate(pick):
        fa = F(0, 0.12 + 0.2 * k)
        key(head, fa, "location", P(x, 26.0, z), linear=True)
        key(head, fa + 12, "location", P(x, 0.2, z), linear=True)
        key(head, fa + 18, "location", P(x, 0.2, z), linear=True)
        key(head, fa + 30, "location", P(x, 26.0, z), linear=True)
    show(O_head, [(F(0, 0.1), F(1, 0))])
    pour = empty("pour", root)
    tube("pour_n", (x0, 30.0, z0), (x0, 70.0, z0), 3.0, m["alu"], pour, 16)
    show(pour, [(F(1, 0.05), F(1, 0.6))])
    run(root, "pourb", [(x0, 30.0, z0), (x0, 5.0, z0), (x0 + 30.0, 4.5, z0 + 10.0)], 8, 1.4, m["dim_glow"], 1, 0.05, 0.5, 30)
    return {"wafer": (x0, 4.0, z0), "edge": (x0 + WR * 0.7, 2.0, z0 + WR * 0.7), "die": sites[0] }


def balls_x():
    n = 9
    return [PX0 + 10.0 + (PX1 - PX0 - 20.0) * i / (n - 1) for i in range(n)]


def package(m, root):
    g = empty("pkg", root)
    # solder balls
    for i, x in enumerate(balls_x()):
        ball(f"ball{i}", (x, 3.5, -8.0), 3.6, m["solder"], g, 20)
        ball(f"ballb{i}", (x, 3.5, -24.0), 3.6, m["solder"], g, 20)
        bx(f"ubm{i}", (x - 4.0, 6.4, PZ0), (x + 4.0, 7.0, 0.0), m["copper"], g)
    # RDL dielectric bands (slightly different shades) with copper planes in the back
    for k, (y0, y1) in enumerate(RDL):
        bx(f"pi{k}", (PX0, y0, PZ0), (PX1, y1, 0.0), m["pi"], g)
    # die and mold
    bx("die", (DX0, Y_DIE[0], PZ0 + 6.0), (DX1, Y_DIE[1], 0.0), m["die"], g)
    bx("die_act", (DX0, Y_DIE[0], PZ0 + 6.0), (DX1, Y_DIE[0] + 1.2, 0.0), m["silicon"], g)
    for sname, (xa, xb) in (("l", (PX0, DX0)), ("r", (DX1, PX1))):
        bx(f"mold_{sname}", (xa, Y_DIE[0], PZ0), (xb, Y_MOLD, 0.0), m["moldc"], g)
    bx("mold_top", (DX0, Y_DIE[1], PZ0), (DX1, Y_MOLD, 0.0), m["moldc"], g)
    bx("mold_back", (DX0, Y_DIE[0], PZ0), (DX1, Y_DIE[1], PZ0 + 6.0), m["moldc"], g)
    # die pads and copper routes through the RDL: pad -> via -> lateral -> via -> UBM
    pads = [DX0 + 5.0 + (DX1 - DX0 - 10.0) * i / 8 for i in range(9)]
    paths = []
    order = sorted(range(9), key=lambda i: abs(pads[i] - (DX0 + DX1) / 2))
    for i, (px, bxp) in enumerate(zip(pads, balls_x())):
        lvl = 1 + order.index(i) % 3  # route level 1..3
        yl = RDL[lvl][0] + 1.0
        zf = 0.3
        bx(f"pad{i}", (px - 1.6, Y_DIE[0] - 0.4, PZ0 + 6.0), (px + 1.6, Y_DIE[0] + 0.2, zf + 0.2), m["alu"], g)
        pts = [(px, Y_DIE[0] - 0.2, zf), (px, yl, zf), (bxp, yl, zf), (bxp, Y_BALL - 0.2, zf)]
        for s in range(3):
            a, b = pts[s], pts[s + 1]
            lo = (min(a[0], b[0]) - 0.6, min(a[1], b[1]) - 0.4, PZ0 + 4.0)
            hi = (max(a[0], b[0]) + 0.6, max(a[1], b[1]) + 0.4, zf + 0.15)
            bx(f"rdl{i}_{s}", lo, hi, m["copper"], g)
        paths.append(pts + [(bxp, 3.5, zf + 3.0)])
    # die-edge markers
    edge = empty("edge", root)
    for x in (DX0, DX1):
        bx(f"edge{x:.0f}", (x - 0.25, 1.0, 0.3), (x + 0.25, Y_MOLD + 6.0, 0.6), m["edge"], edge)
    show(edge, [(F(2, 0.3), F(4, 0))])
    # InFO-PoP: through-mold vias + DRAM package on top
    pop = empty("pop", root)
    tivs = [PX0 + 12.0, PX0 + 30.0, PX0 + 48.0, PX1 - 48.0, PX1 - 30.0, PX1 - 12.0]
    for i, x in enumerate(tivs):
        bx(f"tiv{i}", (x - 1.4, 15.0, -10.0), (x + 1.4, Y_MOLD, 0.3), m["copper"], pop)
        ball(f"pball{i}", (x, Y_MOLD + 3.0, -5.0), 3.0, m["solder"], pop, 16)
    bx("dram_sub", (PX0 + 4.0, Y_MOLD + 5.5, PZ0), (PX1 - 4.0, Y_MOLD + 9.5, 0.0), m["substrate"], pop)
    for k in range(2):
        y = Y_MOLD + 9.5 + 5.0 * k
        bx(f"dram{k}", (PX0 + 30.0 + 6 * k, y + 0.5, PZ0 + 4.0), (PX1 - 30.0 - 6 * k, y + 4.5, -2.0), m["hbm_dram"], pop)
    bx("dram_mold", (PX0 + 4.0, Y_MOLD + 9.5, PZ0), (PX1 - 4.0, Y_MOLD + 22.0, -2.0 - 0.01), m["moldc"], pop)
    D.present(pop, [(F(4, 0.1), F(5, 0))])
    up = [[(x, 3.5, 2.0), (x, 15.0, 1.0), (x, Y_MOLD + 4.0, 1.0), (x, Y_MOLD + 9.0, 1.0)] for x in tivs]
    return paths, up, tivs


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    # a work surface under everything
    bx("table", (-200.0, -8.0, -150.0), (240.0, -4.0, 30.0), m["dark"], root)
    bx("chuck", (0.0, -4.0, -60.0), (230.0, 0.0, 10.0), m["alu"], root)
    wp = wafer(m, root)
    paths, up, tivs = package(m, root)
    for k, p in enumerate(paths):
        run(root, f"sig{k}", p, 3, 0.9, m["sig"], 3, 0.0 + 0.04 * (k % 4), 0.7, 40)
    for k, p in enumerate(paths[::2]):
        run(root, f"sig2_{k}", p, 2, 0.9, m["sig"], 4, 0.4, 0.8, 40)
    for k, p in enumerate(up):
        run(root, f"up{k}", p, 3, 0.9, m["bit"], 4, 0.25, 0.85, 30)
    rise(root, "dieheat", ((DX0 + DX1) / 2, Y_MOLD + 1.0, -16.0), 5, 1.0, m["heat"], 3, 0.2, 0.9, 25.0, 50, (18.0, 8.0))
    # magnifier from one wafer die to the package
    C.magnify(m, root, (wp["die"][0], 4.2, wp["die"][1]), (PX0 - 4.0, 20.0, -20.0), 3.0)
    xm = (PX0 + PX1) / 2
    C.tags(root, {
        0: [("carrier wafer", (WC[0] - WR * 0.7, 0.0, WC[1] + WR * 0.6)), ("known-good dies only", wp["wafer"]),
            ("pick-and-place head", (WC[0] + 10.0, 30.0, WC[1])), ("spaced wider than on the wafer", wp["edge"])],
        1: [("epoxy mold poured over", (WC[0], 30.0, WC[1])), ("reconstituted wafer", wp["wafer"]),
            ("saw lines between packages", wp["edge"])],
        2: [("die in mold", ((DX0 + DX1) / 2, Y_DIE[1], 0.0)), ("polyimide + copper RDL", (PX0 + 20.0, 11.0, 0.0)),
            ("die edge", (DX1, Y_MOLD + 6.0, 0.5)), ("solder balls", (PX1 - 10.0, 0.0, -8.0))],
        3: [("pads at tens of microns", ((DX0 + DX1) / 2, Y_DIE[0], 0.0)), ("routes past the die edge", (PX0 + 30.0, 12.0, 0.0)),
            ("balls under the mold too", (PX0 + 10.0, 0.0, -8.0))],
        4: [("DRAM package on top", (xm, Y_MOLD + 22.0, -10.0)), ("through-mold vias", (tivs[0], Y_MOLD - 6.0, 0.3)),
            ("InFO-PoP: TSM, ASX, AMKR", (PX1 - 20.0, Y_MOLD + 12.0, 0.0))],
    })
    C.done(SLUG, BEATS, [
        frame((WC[0] + 10.0, 6.0, WC[1]), 150.0, 0.25, 0.75),
        frame((WC[0], 4.0, WC[1]), 140.0, -0.15, 0.85),
        [(0.0, frame((xm, 18.0, -14.0), 160.0, 0.20, 0.28)), (0.55, frame((xm, 18.0, -8.0), 130.0, 0.08, 0.12))],
        frame((xm - 20.0, 16.0, -6.0), 95.0, 0.10, 0.10),
        frame((xm, 30.0, -14.0), 165.0, 0.28, 0.25),
    ], root)


if __name__ == "__main__":
    build()
