"""TRM_YIELD: the Terms-tab overview for yield, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_yield.py

Two 300 mm wafers side by side on a prober chuck, the same random defects landing on both. The
left wafer is cut into small dies, the right into big AI-class dies. Every die a defect lands in
is lit red; the good counts are computed here from the actual layout, so the tags are honest.
Behind them, bars of cost per good die; in front, an inspection head sweeping a wafer.

Beats:
  0 wafer     the wafer, the die grid, the prober
  1 defects   particles land on both wafers
  2 sort      probe test: dies with a defect go red
  3 big die   same defects kill far more of the big-die wafer
  4 cost      wafer cost / good dies: cost-per-die bars
  5 learning  inspection finds defect sources; density falls, yield climbs
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, P, bx, empty, show, mat, key  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402
from sand_overview import disc, tube, pivot, rel  # noqa: E402

SLUG = "TRM_YIELD"
R = 75.0  # wafer radius (scene units: 1 unit = 2 mm)
WX = {"s": -95.0, "b": 95.0}  # wafer centres (x); z centre WZ
WZ = -85.0
DIE = {"s": 6.0, "b": 14.0}  # die edge (12 mm vs 28 mm)
WY = 8.0  # wafer top

# fixed defect positions relative to a wafer centre (same on both wafers)
DEFECTS = [(r * math.cos(a), r * math.sin(a)) for r, a in (
    (12, 0.3), (33, 1.4), (51, 2.2), (64, 3.1), (22, 3.9), (45, 4.6), (58, 5.5), (28, 6.0),
    (68, 0.9), (40, 2.8), (55, 0.1), (17, 5.0), (62, 4.1), (36, 3.5))]


def dies(kind):
    """Die cells fully inside the wafer edge (with a 3-unit edge exclusion)."""
    s = DIE[kind]
    n = int(R / s) + 1
    out = []
    for i in range(-n, n):
        for j in range(-n, n):
            x0, z0 = i * s, j * s
            corners = [(x0, z0), (x0 + s, z0), (x0, z0 + s), (x0 + s, z0 + s)]
            if all(math.hypot(cx, cz) < R - 3.0 for cx, cz in corners):
                out.append((x0, z0, s))
    return out


def hit(cell, defs):
    x0, z0, s = cell
    return any(x0 <= dx < x0 + s and z0 <= dz < z0 + s for dx, dz in defs)


def stats(kind, defs):
    cells = dies(kind)
    bad = sum(1 for c in cells if hit(c, defs))
    return len(cells), len(cells) - bad


SN, SG = stats("s", DEFECTS)
BN, BG = stats("b", DEFECTS)
FEW = DEFECTS[::3]  # after learning: a third of the defects
BG2 = stats("b", FEW)[1]
YS, YB, YB2 = round(100 * SG / SN), round(100 * BG / BN), round(100 * BG2 / BN)
WAFER_COST = 20000

BEATS = [
    ("Yield is the share of dies on a wafer that work",
     "A 300 mm wafer is printed with a grid of identical chips (dies), then each is probed electrically before it is "
     "cut out. Yield is good dies divided by all dies. A mature process on a small chip can pass well over 90%; "
     "a new node or a huge chip can start far lower."),
    ("Random defects land on the wafer during hundreds of steps",
     "Particles, scratches, pattern flaws and contamination hit the wafer at some rate per square centimetre, called "
     "defect density (D0). Over hundreds of process steps a few dozen killer defects per wafer is normal. Where they "
     "land is close to random."),
    ("At wafer sort, any die with a killer defect fails",
     "A probe card touches every die's pads and runs tests. One killer defect anywhere in a die usually scraps it, or "
     "forces it to be sold as a cut-down part with blocks disabled. The failing dies are inked out in the wafer map "
     f"and never packaged. Here the small-die wafer passes {SG} of {SN} ({YS}%)."),
    ("The same defects kill far more big dies",
     "Yield falls roughly exponentially with die area times defect density. The same defects that cost a few small "
     f"dies wipe out a large share of big ones: here only {BG} of {BN} big dies survive ({YB}%). That is why "
     "reticle-size AI chips are expensive and why makers split designs into chiplets."),
    ("Wafer cost divided by good dies is the real cost per chip",
     f"A leading-edge wafer costs around ${WAFER_COST // 1000}k or more whether its dies work or not. Fewer dies per "
     "wafer and lower yield multiply together, so a big die can cost many times more per good unit than its area "
     "alone suggests. Yield gains drop straight into gross margin."),
    ("Inspection finds the defect sources and yield climbs as a node matures",
     "Fabs scan wafers with optical and e-beam inspection tools, trace defects back to the step and tool that caused "
     f"them, and fix them. Cut the defects to a third and the big-die yield here rises to {YB2}%. That learning curve "
     "is why new nodes ramp slowly. Related: Taiwan Semiconductor (TSM), Intel (INTC), KLA (KLAC), NVIDIA (NVDA)."),
]


def mats(m):
    m["wafer"] = mat("y_wafer", (0.30, 0.32, 0.40), metal=0.8, rough=0.18)
    m["good"] = mat("y_good", (0.18, 0.30, 0.42), metal=0.5, rough=0.3)
    m["good_g"] = mat("y_good_g", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=1.6)
    m["bad_g"] = mat("y_bad_g", (1.0, 0.25, 0.15), emit=(1.0, 0.20, 0.10), strength=3.0)
    m["defect"] = mat("y_defect", (1.0, 0.55, 0.15), emit=(1.0, 0.50, 0.10), strength=5.0)
    m["chuck"] = mat("y_chuck", (0.55, 0.57, 0.60), metal=0.9, rough=0.35)
    m["floor"] = mat("y_floor", (0.16, 0.17, 0.19), rough=0.8)
    m["bar_s"] = mat("y_bar_s", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=1.5)
    m["bar_b"] = mat("y_bar_b", (1.0, 0.62, 0.18), emit=(1.0, 0.62, 0.18), strength=1.5)
    m["beam"] = mat("y_beam", (0.40, 0.85, 1.0), emit=(0.40, 0.85, 1.0), strength=4.0)


def wafer(m, root, kind):
    """Chuck, wafer, die grid, scribe lines, notch. Returns (red groups per die that fails with all
    defects, red groups that still fail after learning, green group)."""
    cx = WX[kind]
    g = empty(f"w_{kind}", root)
    # prober chuck: a thick steel disc on a stage with vacuum grooves
    bx(f"stage_{kind}", (cx - 90, -14.0, WZ - 90), (cx + 90, -6.0, WZ + 90), m["steel"], g)
    disc(f"chuck_{kind}", (cx, -2.0, WZ), R + 6.0, 8.0, m["chuck"], g)
    for r in (20.0, 40.0, 60.0):
        D.polyline(f"groove_{kind}{r:.0f}",
                   [(cx + r * math.cos(a / 30 * 2 * math.pi), 2.05, WZ + r * math.sin(a / 30 * 2 * math.pi)) for a in range(31)],
                   0.5, m["mold"], g)
    disc(f"wafer_{kind}", (cx, WY - 3.0, WZ), R, 2.0, m["wafer"], g)
    bx(f"notch_{kind}", (cx - 2.0, WY - 4.1, WZ + R - 2.0), (cx + 2.0, WY - 1.9, WZ + R + 0.5), m["floor"], g)
    cells = dies(kind)
    tiles = []
    gap = 0.5 if kind == "s" else 0.8
    for k, (x0, z0, s) in enumerate(cells):
        tiles.append(bx(f"d_{kind}{k}", (cx + x0 + gap, WY - 2.0, WZ + z0 + gap), (cx + x0 + s - gap, WY - 1.4, WZ + z0 + s - gap), m["good"], g))
        if kind == "b":  # big dies: show the core blocks and an HBM-facing PHY strip
            for a in range(2):
                for b in range(2):
                    xa = cx + x0 + 2.0 + a * (s - 4.0) / 2
                    za = WZ + z0 + 2.0 + b * (s - 6.0) / 2
                    tiles.append(bx(f"dc_{kind}{k}{a}{b}", (xa + 0.3, WY - 1.4, za + 0.3), (xa + (s - 4.0) / 2 - 0.3, WY - 1.15, za + (s - 6.0) / 2 - 0.3), m["die"], g))
            tiles.append(bx(f"dp_{kind}{k}", (cx + x0 + 2.0, WY - 1.4, WZ + z0 + s - 3.4), (cx + x0 + s - 2.0, WY - 1.15, WZ + z0 + s - 2.0), m["gold"], g))
        else:
            tiles.append(bx(f"dc_{kind}{k}", (cx + x0 + 1.5, WY - 1.4, WZ + z0 + 1.5), (cx + x0 + s - 1.5, WY - 1.2, WZ + z0 + s - 1.5), m["die"], g))
    D.join(tiles, f"dies_{kind}")
    red, red2 = empty(f"red_{kind}", root), empty(f"red2_{kind}", root)
    green = empty(f"green_{kind}", root)
    rr, rr2, gg = [], [], []
    for k, c in enumerate(cells):
        x0, z0, s = c
        lo, hi = (cx + x0 + gap, WY - 1.1, WZ + z0 + gap), (cx + x0 + s - gap, WY - 0.8, WZ + z0 + s - gap)
        if hit(c, DEFECTS):
            rr.append(bx(f"r_{kind}{k}", lo, hi, m["bad_g"], red))
            if hit(c, FEW):
                rr2.append(bx(f"r2_{kind}{k}", lo, hi, m["bad_g"], red2))
        else:
            q = s * 0.3
            gg.append(bx(f"g_{kind}{k}", (lo[0] + q, hi[1] - 0.1, lo[2] + q), (hi[0] - q, hi[1], hi[2] - q), m["good_g"], green))
    for grp, parts, nm in ((red, rr, "rm"), (red2, rr2, "r2m"), (green, gg, "gm")):
        if parts:
            D.join(parts, f"{nm}_{kind}")
    return red, red2, green


def defects(m, root, kind, defs, name):
    g = empty(name, root)
    for k, (dx, dz) in enumerate(defs):
        x, z = WX[kind] + dx, WZ + dz
        D.bead(f"{name}{k}", (x, WY - 0.6, z), 1.1, m["defect"], g)
    return g


def prober(m, root):
    """A probe card over the small-die wafer: ring PCB, needles fanning to the centre."""
    g = empty("probe", root)
    cx, y = WX["s"], 34.0
    ring = []
    for a in range(24):
        a0, a1 = a / 24 * 2 * math.pi, (a + 1) / 24 * 2 * math.pi
        ring.append(tube(f"pc{a}", (cx + 40 * math.cos(a0), y, WZ + 40 * math.sin(a0)),
                         (cx + 40 * math.cos(a1), y, WZ + 40 * math.sin(a1)), 6.0, m["pcb_blue"], g, 8))
    D.join(ring, "probe_ring")
    for k in range(12):
        a = k / 12 * 2 * math.pi
        D.polyline(f"ndl{k}", [(cx + 34 * math.cos(a), y - 2, WZ + 34 * math.sin(a)),
                               (cx + 6 * math.cos(a), WY + 1.0, WZ + 6 * math.sin(a))], 0.35, m["tin"], g)
    tube("probe_arm", (cx + 40, y, WZ), (cx + 40, 80.0, WZ), 4.0, m["steel"], g, 12)
    bx("probe_head", (cx + 25, 80.0, WZ - 18), (cx + 70, 96.0, WZ + 18), m["car"], g)
    return g


def bar(m, root, name, x, z, w, heights, mt):
    """A bar standing at (x, 0, z) whose height steps to heights[beat] at each beat's start."""
    pv = pivot(name, (x, 0.0, z), root)
    bx(f"{name}_b", rel((x, 0, z), (x - w / 2, 0.0, z - w / 2)), rel((x, 0, z), (x + w / 2, 1.0, z + w / 2)), m[mt], pv)
    prev = None
    for b, h in sorted(heights.items()):
        if prev is not None:
            key(pv, F(b, 0.05), "scale", (1.0, 1.0, max(prev, 1e-4)), linear=True)
        prev = h
        key(pv, F(b, 0) if b == 0 else F(b, 0.15), "scale", (1.0, 1.0, max(h, 1e-4)), linear=True)
        key(pv, F(b, 0.45), "scale", (1.0, 1.0, max(h, 1e-4)), linear=True)
    return pv


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-260.0, -16.0, -300.0), (260.0, -14.0, 120.0), m["floor"], root)
    red, red2, green = {}, {}, {}
    for k in ("s", "b"):
        red[k], red2[k], green[k] = wafer(m, root, k)
    pg = prober(m, root)
    show(pg, [(F(0, 0), F(3, 0))])
    dall = {k: defects(m, root, k, DEFECTS, f"def_{k}") for k in ("s", "b")}
    dfew = defects(m, root, "b", FEW, "few_b")
    for k in ("s", "b"):
        show(dall[k], [(F(1, 0.55), F(5, 0))])
        # particles rain down onto the wafer
        for j, (dx, dz) in enumerate(DEFECTS):
            x, z = WX[k] + dx, WZ + dz
            run(root, f"rain_{k}{j}", [(x, 70.0, z), (x, WY, z)], 1, 1.1, m["defect"], 1, 0.05 + 0.03 * j, 0.05 + 0.03 * j, 22)
        show(green[k], [(F(2, 0.35), F(5, 0))])
    show(dfew, [(F(5, 0.5), F(6, 0))])
    show(red["s"], [(F(2, 0.35), F(5, 0))])
    show(red["b"], [(F(3, 0.2), F(5, 0.5))])
    show(red2["b"], [(F(5, 0.5), F(6, 0))])
    show(green["b"], [(F(3, 0.2), F(6, 0))])

    # test signals: probe needles to the tester head
    run(root, "test", [(WX["s"] + 47, 96.0, WZ), (WX["s"] + 40, 40.0, WZ), (WX["s"], WY + 1.0, WZ)], 8, 0.9, m["sig"], 2, 0.0, 0.7, 30)

    # cost per good die bars behind the wafers (height ~ wafer cost / good dies)
    cs, cb = WAFER_COST / SG, WAFER_COST / BG
    scale = 110.0 / cb
    bar(m, root, "bar_s", -40.0, -205.0, 26.0, {0: 0.0, 4: cs * scale, 5: cs * scale}, "bar_s")
    bar(m, root, "bar_b", 40.0, -205.0, 26.0, {0: 0.0, 4: cb * scale, 5: WAFER_COST / BG2 * scale}, "bar_b")
    bx("bar_plinth", (-70.0, -14.0, -225.0), (70.0, -10.0, -185.0), m["steel"], root)
    # cash beads: wafer cost split over the good dies
    for k, x in (("s", -40.0), ("b", 40.0)):
        run(root, f"cash_{k}", [(WX[k], WY + 2.0, WZ - 40), (WX[k] * 0.6, 50.0, -170.0), (x, 30.0, -205.0)], 10, 1.4, m["v12"], 4, 0.0, 0.6, 40)

    # inspection head over the big-die wafer in beat 5: gantry + sweeping beam
    ig = empty("insp", root)
    bx("insp_rail_l", (WX["b"] - 90, 46.0, WZ - 92), (WX["b"] - 84, 52.0, WZ + 92), m["steel"], ig)
    bx("insp_rail_r", (WX["b"] + 84, 46.0, WZ - 92), (WX["b"] + 90, 52.0, WZ + 92), m["steel"], ig)
    hd = empty("insp_head", ig)
    bx("insp_bridge", (WX["b"] - 90, 52.0, WZ - 82), (WX["b"] + 90, 60.0, WZ - 70), m["car"], hd)
    bx("insp_optic", (WX["b"] - 8, 30.0, WZ - 82), (WX["b"] + 8, 52.0, WZ - 70), m["mold"], hd)
    D.polyline("insp_beam", [(WX["b"], 30.0, WZ - 76), (WX["b"] - 70, WY, WZ - 76), (WX["b"] + 70, WY, WZ - 76), (WX["b"], 30.0, WZ - 76)], 0.4, m["beam"], hd)
    for j in range(5):
        key(hd, F(5, 0.1 + 0.16 * j), "location", P(0, 0, 0 if j % 2 == 0 else 150.0), linear=True)
    show(ig, [(F(5, 0.0), F(6, 0))])
    rise(root, "fix", (WX["b"], WY, WZ), 8, 1.0, m["sig"], 5, 0.3, 0.9, 40.0, 50, (50.0, 50.0))

    T = {
        0: [("300 mm wafer on the prober chuck", (WX["s"], WY, WZ + 60)), (f"{SN} small dies (12 mm)", (WX["s"], WY, WZ)),
            (f"{BN} big AI dies (28 mm)", (WX["b"], WY, WZ)), ("probe card", (WX["s"] + 40, 34.0, WZ))],
        1: [("killer defects land at random", (WX["s"] + 20, WY, WZ - 30)), ("same defects on both wafers", (WX["b"], WY, WZ - 40)),
            ("D0: defects per cm2", (0.0, 40.0, WZ))],
        2: [("probe tests every die", (WX["s"] + 40, 34.0, WZ)), (f"small die: {SG}/{SN} good = {YS}%", (WX["s"], WY, WZ + 50)),
            ("one defect scraps a die", (WX["s"] + 12, WY, WZ + 4))],
        3: [(f"big die: {BG}/{BN} good = {YB}%", (WX["b"], WY, WZ + 50)), ("bigger area, more hits", (WX["b"], WY, WZ)),
            (f"small die: {YS}%", (WX["s"], WY, WZ))],
        4: [(f"~${WAFER_COST // 1000}k per wafer either way", (0.0, 50.0, -170.0)), (f"small: ${cs:.0f} per good die", (-40.0, cs * scale, -205.0)),
            (f"big: ${cb:.0f} per good die", (40.0, cb * scale, -205.0))],
        5: [("inspection finds the sources", (WX["b"], 60.0, WZ - 76)), (f"1/3 the defects: {YB2}% yield", (WX["b"], WY, WZ + 50)),
            (f"cost falls to ${WAFER_COST / BG2:.0f}", (40.0, WAFER_COST / BG2 * scale, -205.0)), ("TSM INTC KLAC NVDA", (0.0, 40.0, WZ + 40))],
    }
    C.tags(root, T)
    C.done(SLUG, BEATS, [
        frame((0.0, 0.0, WZ), 360.0, 0.25, 0.75),
        frame((0.0, 10.0, WZ), 340.0, 0.20, 0.85),
        frame((WX["s"], 10.0, WZ), 190.0, 0.30, 0.80),
        frame((WX["b"], 5.0, WZ), 190.0, -0.30, 0.80),
        frame((0.0, 40.0, -150.0), 300.0, 0.15, 0.45),
        frame((WX["b"] - 20, 20.0, WZ - 30), 260.0, -0.35, 0.65),
    ], root)


if __name__ == "__main__":
    build()
