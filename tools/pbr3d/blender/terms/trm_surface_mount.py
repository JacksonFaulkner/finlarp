"""TRM_SURFACE_MOUNT: the Terms-tab overview for surface mount technology (SMT), at POWER-page detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_surface_mount.py

A whole SMT line stands at the back (loader, paste printer, two pick-and-place machines, reflow oven,
inspection). In front, one board section ~10x life size goes through the line's steps in place: a steel
stencil and squeegee print paste onto the pads, a vacuum nozzle drops parts onto the wet paste, the board
heats along a reflow profile and the dull paste turns to shiny solder fillets, then an inspection camera
scans it.

Beats:
  0 line      the SMT line and the bare board with copper pads
  1 print     stencil + squeegee leave paste on every pad
  2 place     the nozzle picks and drops each part onto its paste
  3 reflow    heat profile; paste melts and wets into fillets
  4 inspect   optical/X-ray check, finished board; who runs these lines
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, P, bx, empty, key, mat, show, tube  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import frame, run, rise, present, blink  # noqa: E402

SLUG = "TRM_SURFACE_MOUNT"
BEATS = [
    ("Surface mount puts parts straight onto pads on the board's surface",
     "Older boards pushed component leads through drilled holes. Surface mount technology (SMT) instead sets each part "
     "on flat copper pads and solders it there, so parts can be tiny and sit on both sides of the board. A line is a "
     "row of machines: board loader, paste printer, pick-and-place, reflow oven, inspection."),
    ("A stencil and squeegee print solder paste onto every pad",
     "A laser-cut steel stencil, about 0.1 mm thick, is clamped on the board with an opening over each pad. A squeegee "
     "drags solder paste (tiny tin-silver-copper balls in flux) across it, leaving a measured deposit on every pad at "
     "once. Most assembly defects trace back to this step, so 3D paste inspection usually follows."),
    ("Pick-and-place nozzles set every part onto the wet paste",
     "Vacuum nozzles lift parts off reels and trays, a camera checks each one's position, and the head sets it down on "
     "its paste. Fast machines place tens of thousands of parts per hour; a GPU server board carries thousands of "
     "them, mostly tiny capacitors, plus big BGA chips that need extra accuracy."),
    ("A reflow oven melts the paste into solder joints",
     "The board rides through zones that preheat, soak to activate the flux, peak around 240-250 C for lead-free "
     "solder, then cool. The paste melts, wets the pads and leads, and surface tension pulls parts into line. Under a "
     "BGA, hundreds of hidden balls melt at once."),
    ("Inspection checks every joint; contract makers run the lines",
     "Optical cameras check placement and fillets, X-ray looks under BGAs, then electrical test. Heavy AI boards with "
     "big packages are hard to reflow without warping, which favours experienced builders. Related: Jabil (JBL), "
     "Flex (FLEX), Celestica (CLS); machines from ASMPT and Fuji."),
]

BX0, BX1, BZ0 = -95.0, 95.0, -75.0  # the big board section (front cut at z = 0)
LZ = -235.0  # the line at the back


def mats(m):
    m["sm_paste"] = mat("sm_paste", (0.48, 0.49, 0.50), metal=0.2, rough=0.9)
    m["sm_stencil"] = mat("sm_stencil", (0.70, 0.72, 0.75), metal=0.9, rough=0.3, alpha=0.55)
    m["sm_mach"] = mat("sm_mach", (0.80, 0.81, 0.83), metal=0.3, rough=0.45)
    m["sm_belt"] = mat("sm_belt", (0.08, 0.08, 0.09), rough=0.7)
    m["sm_floor"] = mat("sm_floor", (0.15, 0.16, 0.18), rough=0.85)
    m["sm_win"] = mat("sm_win", (1.0, 0.45, 0.15), emit=(1.0, 0.45, 0.15), strength=1.8)
    m["sm_ok"] = mat("sm_ok", (0.30, 0.95, 0.45), emit=(0.30, 0.95, 0.45), strength=3.0)
    m["sm_scan"] = mat("sm_scan", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=1.6, alpha=0.6)
    m["sm_hotpad"] = mat("sm_hotpad", (1.0, 0.5, 0.2), emit=(1.0, 0.45, 0.15), strength=1.2)
    m["sm_axis"] = mat("sm_axis", (0.75, 0.78, 0.82), rough=0.5)
    m["sm_curve"] = mat("sm_curve", (1.0, 0.55, 0.2), emit=(1.0, 0.5, 0.15), strength=3.0)


# ---- parts and their pads ----------------------------------------------------------------------
# each site: kind, centre (x, z), and a builder; pads are (x0, z0, x1, z1)

def mlcc_pads(x, z, w=10.0, d=5.0):
    return [(x - w / 2 - 1.0, z - d / 2 - 0.5, x - w / 2 + 2.5, z + d / 2 + 0.5),
            (x + w / 2 - 2.5, z - d / 2 - 0.5, x + w / 2 + 1.0, z + d / 2 + 0.5)]


def soic_pads(x, z, w=26.0, d=14.0, n=6):
    p = w / (n + 1)
    out = []
    for side in (-1, 1):
        for i in range(n):
            px = x - w / 2 + p * (i + 1)
            z0, z1 = z + side * (d / 2 + 0.2), z + side * (d / 2 + 3.4)
            out.append((px - p * 0.28, min(z0, z1), px + p * 0.28, max(z0, z1)))
    return out


def bga_pads(x, z, half=15.0, n=6):
    out = []
    pitch = 2 * half / n
    for i in range(n):
        for j in range(n):
            px, pz = x - half + pitch * (i + 0.5), z - half + pitch * (j + 0.5)
            out.append((px - 1.1, pz - 1.1, px + 1.1, pz + 1.1))
    return out


SITES = [
    ("mlcc", (-70.0, -14.0)),
    ("mlcc", (-70.0, -40.0)),
    ("soic", (-30.0, -22.0)),
    ("mlcc", (-40.0, -58.0)),
    ("bga", (32.0, -36.0)),
    ("ind", (74.0, -16.0)),
    ("mlcc", (74.0, -52.0)),
]


def pads_for(kind, x, z):
    if kind == "mlcc":
        return mlcc_pads(x, z)
    if kind == "soic":
        return soic_pads(x, z)
    if kind == "bga":
        return bga_pads(x, z)
    return mlcc_pads(x, z, w=20.0, d=14.0)


def part(m, g, k, kind, x, z):
    """The part, built at its seated position (bottom at y = 0.6, on the paste). Returns top y."""
    y = 0.6
    if kind == "mlcc":
        D.mlcc(m, g, f"p{k}", (x, y, z), 10.0, 5.0, 5.0)
        return y + 5.0
    if kind == "soic":
        return C.chip(m, g, f"p{k}", (x, y, z), 26.0, 14.0, h=5.0, pins=6, pitch=26.0 / 7)[1]
    if kind == "bga":
        bx(f"p{k}_sub", (x - 16.0, y + 1.6, z - 16.0), (x + 16.0, y + 3.4, z + 16.0), m["substrate"], g)
        bx(f"p{k}_mold", (x - 14.0, y + 3.4, z - 14.0), (x + 14.0, y + 8.0, z + 14.0), m["mold"], g)
        bx(f"p{k}_die", (x - 7.0, y + 8.0, z - 7.0), (x + 7.0, y + 8.3, z + 7.0), m["die"], g)
        for (a, b, c, d) in bga_pads(x, z):
            O_ball = C.O.ball(f"p{k}_ball{a:.0f}_{b:.0f}", ((a + c) / 2, y + 0.9, (b + d) / 2), 1.0, m["solder"], g, 10)
        return y + 8.3
    # power inductor
    bx(f"p{k}_core", (x - 9.0, y + 0.6, z - 7.0), (x + 9.0, y + 11.0, z + 7.0), m["ferrite"], g)
    for s in (-1, 1):
        bx(f"p{k}_t{s}", (x + s * 9.0, y, z - 5.0), (x + s * 10.0, y + 4.0, z + 5.0), m["copper"], g)
    return y + 11.0


def line_back(m, root):
    """The SMT line at the back: loader, printer, 2 pick-and-place, oven, AOI, unloader."""
    g = empty("line", root)
    bx("sm_floor", (-330.0, -24.0, LZ - 70.0), (330.0, -22.0, 20.0), m["sm_floor"], root)
    bx("belt", (-300.0, 10.0, LZ - 6.0), (300.0, 12.0, LZ + 6.0), m["sm_belt"], g)
    for i in range(16):
        x = -296.0 + i * 39.0
        bx(f"bl{i}", (x, -22.0, LZ - 6.0), (x + 2.0, 10.0, LZ - 4.0), m["steel"], g)
    st = [(-270.0, 26.0, 30.0, "loader"), (-200.0, 44.0, 38.0, "printer"), (-120.0, 56.0, 46.0, "pnp1"),
          (-50.0, 56.0, 46.0, "pnp2"), (70.0, 40.0, 150.0, "oven"), (210.0, 50.0, 40.0, "aoi"), (275.0, 26.0, 30.0, "unl")]
    out = {}
    for x, h, w, name in st:
        bx(f"m_{name}", (x - w / 2, -22.0, LZ - 26.0), (x + w / 2, h, LZ + 22.0), m["sm_mach"], g)
        bx(f"m_{name}_top", (x - w / 2 + 2.0, h, LZ - 24.0), (x + w / 2 - 2.0, h + 2.0, LZ + 20.0), m["dark"], g)
        # front slot the belt passes through
        bx(f"m_{name}_slot", (x - w / 2 - 0.2, 8.0, LZ + 22.0), (x + w / 2 + 0.2, 16.0, LZ + 22.4), m["screen"], g)
        out[name] = (x, h, LZ)
    for k in range(6):  # oven zone windows
        bx(f"ovw{k}", (-2.0 + k * 24.0, 22.0, LZ + 22.0), (14.0 + k * 24.0, 32.0, LZ + 22.6), m["sm_win"], g)
    for name in ("pnp1", "pnp2"):  # feeder banks of reels
        x = out[name][0]
        for r in range(6):
            tube(f"{name}_reel{r}", (x - 18.0 + r * 7.0, 12.0, LZ + 28.0), (x - 18.0 + r * 7.0, 12.0, LZ + 31.0), 5.0, m["plastic"], g, 18)
    lamp = empty("aoi_lamp", root)
    bx("aoi_l", (204.0, 52.0, LZ - 4.0), (216.0, 58.0, LZ + 4.0), m["sm_ok"], lamp)
    show(lamp, [(F(0, 0.3), F(1, 0)), (F(4, 0.2), F(5, 0))])
    run(root, "boards", [(-300.0, 14.0, LZ), (300.0, 14.0, LZ)], 9, 3.0, m["sm_ok"], [0, 4], 0.0, 0.85, 90)
    rise(root, "ov_heat", (70.0, 42.0, LZ), 10, 1.6, m["heat"], [0, 3], 0.0, 0.8, 28.0, 60, (60.0, 10.0))
    return out


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    st = line_back(m, root)
    C.pcb(m, root, "bd", BX0, BX1, BZ0, 0.0, t=4.0)
    # inner copper layers show at the front cut
    for k, y in enumerate((-1.6, -2.6)):
        bx(f"bd_in{k}", (BX0, y - 0.25, -0.3), (BX1, y + 0.25, 0.05), m["copper"], root)
    # traces between sites (a little routing)
    C.trace(m, root, "tr0", [(-64.0, 0.02, -14.0), (-45.0, 0.02, -14.0), (-45.0, 0.02, -15.0)], 1.0)
    C.trace(m, root, "tr1", [(-30.0, 0.02, -32.0), (-30.0, 0.02, -46.0), (14.0, 0.02, -46.0)], 1.0)
    C.trace(m, root, "tr2", [(50.0, 0.02, -36.0), (62.0, 0.02, -36.0), (62.0, 0.02, -16.0)], 1.0)
    C.trace(m, root, "tr3", [(78.0, 0.02, -24.0), (78.0, 0.02, -48.0)], 1.0)

    paste, fil = [], []
    site_pts = []
    parts = []
    for k, (kind, (x, z)) in enumerate(SITES):
        pads = pads_for(kind, x, z)
        pg, fg = empty(f"paste{k}", root), empty(f"fil{k}", root)
        for j, (a, b, c, d) in enumerate(pads):
            bx(f"pad{k}_{j}", (a, 0.0, b), (c, 0.3, d), m["copper"], root)
            bx(f"pst{k}_{j}", (a + 0.2, 0.3, b + 0.2), (c - 0.2, 1.4, d - 0.2), m["sm_paste"], pg)
            if kind != "bga":  # fillet: a wider, lower shiny wedge
                bx(f"fl{k}_{j}", (a - 0.3, 0.3, b - 0.3), (c + 0.3, 1.0, d + 0.3), m["solder"], fg)
                cx, cz = (a + c) / 2, (b + d) / 2
                bx(f"fl{k}_{j}t", (cx - (c - a) * 0.25, 1.0, cz - (d - b) * 0.25), (cx + (c - a) * 0.25, 2.4, cz + (d - b) * 0.25), m["solder"], fg)
        # paste appears as the squeegee passes (x-sweep in beat 1)
        u = 0.15 + 0.6 * (x - BX0) / (BX1 - BX0)
        show(pg, [(F(1, u), F(3, 0.45))])
        show(fg, [(F(3, 0.45), F(5, 0))])
        paste.append(pg)
        fil.append(fg)
        g = empty(f"part{k}", root)
        top = part(m, g, k, kind, x, z)
        parts.append(g)
        site_pts.append((x, top, z))

    # beat 1: stencil + squeegee
    sten = empty("stencil", root)
    bx("sten", (BX0 - 6.0, 1.5, BZ0 - 6.0), (BX1 + 6.0, 1.9, 0.0), m["sm_stencil"], sten)
    for s, (za, zb) in enumerate(((BZ0 - 12.0, BZ0 - 6.0),)):
        bx(f"sten_fr{s}", (BX0 - 12.0, 1.5, za), (BX1 + 12.0, 4.5, zb), m["alu"], sten)
    present(sten, [(F(1, 0.05), F(1, 0.85))])
    sq = empty("squeegee", root)
    sq_in = empty("sq_in", sq)
    bx("sq_blade", (BX0 - 3.0, 1.9, BZ0 - 4.0), (BX0 - 1.5, 14.0, -1.0), m["steel"], sq_in)
    bx("sq_hold", (BX0 - 5.0, 14.0, BZ0 - 6.0), (BX0 + 1.0, 20.0, 0.0), m["dark"], sq_in)
    tube("sq_roll", (BX0 + 2.0, 3.2, BZ0 - 3.0), (BX0 + 2.0, 3.2, -1.5), 1.6, m["sm_paste"], sq_in, 14)
    for f, x in ((F(1, 0.1), 0.0), (F(1, 0.8), BX1 - BX0)):
        key(sq_in, f, "location", P(x, 0.0, 0.0), linear=True)
    present(sq, [(F(1, 0.08), F(1, 0.85))])

    # beat 2: parts drop in; the nozzle visits each site
    noz = empty("nozzle", root)
    nz_in = empty("nz_in", noz)
    tube("nz_tip", (0.0, 0.0, 0.0), (0.0, 10.0, 0.0), 1.2, m["steel"], nz_in, 12)
    tube("nz_body", (0.0, 10.0, 0.0), (0.0, 34.0, 0.0), 3.0, m["sm_mach"], nz_in, 16)
    bx("nz_head", (-10.0, 34.0, -8.0), (10.0, 46.0, 8.0), m["dark"], nz_in)
    bx("nz_cam", (10.0, 36.0, -3.0), (16.0, 42.0, 3.0), m["sm_ok"], nz_in)
    n = len(SITES)
    for k, g in enumerate(parts):
        x, top, z = site_pts[k]
        ua, ub = 0.08 + 0.85 * k / n, 0.08 + 0.85 * (k + 0.75) / n
        um = (ua + ub) / 2
        key(g, 0, "location", P(0.0, 30.0, 0.0))
        key(g, F(2, ua), "location", P(0.0, 30.0, 0.0), linear=True)
        key(g, F(2, um), "location", P(0.0, 0.0, 0.0), linear=True)
        show(g, [(F(2, ua), F(5, 0))])
        key(nz_in, F(2, ua), "location", P(x, top + 30.0, z), linear=True)
        key(nz_in, F(2, um), "location", P(x, top, z), linear=True)
        key(nz_in, F(2, ub), "location", P(x, top + 30.0, z), linear=True)
    present(noz, [(F(2, 0.05), F(3, 0))])

    # beat 3: reflow profile curve + heat
    prof = empty("prof", root)
    gx0, gx1, gy0, gy1, gz = -90.0, 90.0, 70.0, 130.0, -95.0
    bx("ax_x", (gx0, gy0 - 0.4, gz), (gx1, gy0 + 0.4, gz + 0.8), m["sm_axis"], prof)
    bx("ax_y", (gx0 - 0.4, gy0, gz), (gx0 + 0.4, gy1, gz + 0.8), m["sm_axis"], prof)
    bx("ax_peak", (gx0, gy0 + 0.92 * (gy1 - gy0) - 0.2, gz), (gx1, gy0 + 0.92 * (gy1 - gy0) + 0.2, gz + 0.4), m["dim_glow"], prof)

    def temp(u):  # 0..1 normalized temperature along the oven
        if u < 0.25:
            return 0.1 + 0.5 * u / 0.25
        if u < 0.55:
            return 0.6 + 0.12 * (u - 0.25) / 0.3
        if u < 0.7:
            return 0.72 + 0.2 * math.sin(math.pi * (u - 0.55) / 0.15 / 2)
        if u < 0.78:
            return 0.92 - 0.02 * (u - 0.7) / 0.08
        return 0.9 - 0.75 * (u - 0.78) / 0.22

    pts = [(gx0 + (gx1 - gx0) * i / 60, gy0 + (gy1 - gy0) * temp(i / 60), gz + 0.6) for i in range(61)]
    D.polyline("prof_curve", pts, 0.7, m["sm_curve"], prof)
    for k, (u0, u1, nm) in enumerate(((0.0, 0.25, "pre"), (0.25, 0.55, "soak"), (0.55, 0.78, "peak"), (0.78, 1.0, "cool"))):
        xa = gx0 + (gx1 - gx0) * u1
        bx(f"zone{k}", (xa - 0.3, gy0, gz), (xa + 0.3, gy1, gz + 0.4), m["dim_glow"], prof)
    present(prof, [(F(3, 0), F(4, 0))])
    run(root, "prof_bead", pts, 1, 2.2, m["v12"], 3, 0.05, 0.05, 150)
    hot = empty("hotpads", root)
    for k, (kind, (x, z)) in enumerate(SITES):
        for j, (a, b, c, d) in enumerate(pads_for(kind, x, z)[:4]):
            bx(f"hp{k}_{j}", (a - 0.6, 0.31, b - 0.6), (c + 0.6, 0.45, d + 0.6), m["sm_hotpad"], hot)
    show(hot, [(F(3, 0.3), F(3, 0.62))])
    rise(root, "bd_heat", (0.0, 8.0, -38.0), 14, 1.2, m["heat"], 3, 0.05, 0.75, 32.0, 50, (80.0, 30.0))

    # beat 4: inspection scan bar sweeping, green checks over parts
    scan = empty("scan", root)
    sc_in = empty("sc_in", scan)
    bx("scan_bar", (BX0, 0.5, BZ0), (BX0 + 3.0, 22.0, 0.0), m["sm_scan"], sc_in)
    bx("scan_head", (BX0 - 4.0, 22.0, BZ0 - 4.0), (BX0 + 7.0, 30.0, 4.0), m["dark"], sc_in)
    for f, x in ((F(4, 0.05), 0.0), (F(4, 0.6), BX1 - BX0 - 3.0)):
        key(sc_in, f, "location", P(x, 0.0, 0.0), linear=True)
    present(scan, [(F(4, 0.0), F(4, 0.65))])
    for k, (x, top, z) in enumerate(site_pts):
        ok = empty(f"ok{k}", root)
        bx(f"okb{k}", (x - 1.5, top + 3.0, z - 1.5), (x + 1.5, top + 6.0, z + 1.5), m["sm_ok"], ok)
        u = 0.05 + 0.55 * (x - BX0) / (BX1 - BX0)
        show(ok, [(F(4, u), F(5, 0))])

    soic, bga, ind = site_pts[2], site_pts[4], site_pts[5]
    C.tags(root, {
        0: [("SMT line: print, place, reflow", (-120.0, 70.0, LZ)), ("reflow oven", (70.0, 45.0, LZ)),
            ("bare board, copper pads", (-30.0, 1.0, -22.0)), ("board ~10x life size", (60.0, 1.0, -70.0))],
        1: [("steel stencil ~0.1 mm", (40.0, 2.0, -70.0)), ("squeegee drags paste", (-80.0, 20.0, -40.0)),
            ("paste on every pad", (-70.0, 1.4, -14.0))],
        2: [("vacuum nozzle", (0.0, 45.0, -30.0)), ("tiny caps by the thousand", site_pts[0]),
            ("BGA: balls underneath", bga), ("power inductor", ind)],
        3: [("peak ~245 C", (10.0, 128.0, -95.0)), ("preheat, soak, peak, cool", (-60.0, 95.0, -95.0)),
            ("paste melts into fillets", soic)],
        4: [("camera checks every joint", (-60.0, 30.0, -40.0)), ("X-ray under the BGA", bga),
            ("JBL  FLEX  CLS", (0.0, 60.0, LZ)), ("finished board", (60.0, 1.0, -70.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-20.0, 20.0, -120.0), 600.0, 0.25, 0.45, pad=1.0),
        frame((0.0, 5.0, -38.0), 200.0, 0.30, 0.60),
        frame((0.0, 10.0, -36.0), 190.0, 0.20, 0.50),
        frame((0.0, 50.0, -60.0), 240.0, 0.10, 0.30),
        [(0.0, frame((0.0, 8.0, -38.0), 200.0, -0.20, 0.55)), (0.7, frame((0.0, 20.0, -120.0), 480.0, -0.15, 0.40, pad=1.0))],
    ], root)


if __name__ == "__main__":
    build()
