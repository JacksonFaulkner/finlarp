"""The CHIP tab, MID METAL: the middle wiring tier, M5-M9, which routes signals block to block.
The overview opens and closes on the whole-chip scene (chip_kit.py); everything else is a detailed
cut-away of the wiring itself (chip_mid_metal_detail.py), with beads riding the real wires.

Run from the repo root (all scenes, or the named ones after `--`):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_mid_metal.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_mid_metal.py -- zoom_a sec3

Each scene writes blender/chip_mid_metal_<name>.blend and assets/chip_mid_metal_<name>.glb (the
overview writes assets/chip_mid_metal.glb). One beat is 8 s; the TUI samples at t = (beat + local)
* 8 (diagrams_nodes/chip/mid_metal.rs).

Overview (6 beats):
  0 whole    the whole chip, the middle tier lit
  1 zoom     the M5-M9 cut-away: five levels, vias, caps
  2 short    a signal leaves a via and crosses one block over on a short mid wire
  3 long     the same signal on a longer run: it takes longer to arrive
  4 RC       close on one wire: R from its narrow copper, C to the wire beside it
  5 whole    the longest runs climb to the thick top tier, which is lit

Zoom-ins (3 beats each, key: label as in the old MID METAL page; a shares section 1's builder,
d is section 6 seen from the other side, e shares section 7's):
  a one dual-damascene pass   trench and via, plated Cu, the CMP and the cap
  b RC delay                  R on one wire, C to the wire below it, RC ~ L^2
  c low-k, air gaps and ruthenium
  d electromigration          electrons push atoms, a void and heat, caps slow the drift
  e vias, edge placement and RC extraction

Sections (one per `# ` heading of CHIP_MID_METAL.txt):
  1 what happens: five passes, M5 to M9      (4 beats)
  2 dual damascene in section                (4 beats)
  3 RC delay: why levels get fatter         (3 beats)
  4 pitch and patterning per level           (3 beats)
  5 the dielectric: lower k, softer film     (4 beats)
  6 electromigration                         (3 beats)
  7 vias and edge placement                  (3 beats)
  8 who makes it                             (3 beats)
  9 chokepoints and risks                    (3 beats)
 10 sources                                  (4 beats, the whole chip pulled back)

Bead flight time follows the RC story (delay grows roughly with length squared); the scale is
schematic, not a timing measurement.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, ball, beat, empty, key, label, mat, show, tube  # noqa: E402
from sand_overview import F as FF  # noqa: E402
from sand_zooms import finish, start, stream_of  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import route  # noqa: E402

BEATS = 6  # the overview

# ---- scene pieces ---------------------------------------------------------------------------


def mats(m):
    """chip_kit's materials, plus this node's (prefixed, since mat() caches by name)."""
    C.mats(m)
    m["chip_mid_metal_ru"] = mat("chip_mid_metal_ru", (0.55, 0.72, 0.90), metal=0.9, rough=0.25)


# ---- the overview -----------------------------------------------------------------------------
#
# Beats 0 and 5 are the whole chip (chip_kit.py), the tab's shared story. Beats 1-4 swap it for the
# detailed M5-M9 cut-away (chip_mid_metal_detail.py), with signal beads riding the real wires.

CHIP_ON = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
DETAIL_ON = [(F(1, 0), F(5, 0))]
WHOLE = C.WHOLE


def build(name="mid_metal"):
    import chip_mid_metal_detail as D
    m, root = start(name, BEATS, page="chip")
    mats(m)
    D.mats(m)
    chip = empty("chip_whole", root)
    C.chip(chip, m, mid=[(F(0, 0), F(1, 0))], top=[(F(5, 0), F(6, 0))])
    show(chip, CHIP_ON)
    det = empty("detail", root)
    show(det, DETAIL_ON)
    specs = [_spec("M5", "x", full=True), _spec("M6", "z"), _spec("M7", "x"), _spec("M8", "z"), _spec("M9", "x")]
    g, lv = _block(det, m, specs)
    m5, m6, m7, m8, m9 = (lv[k] for k in ("M5", "M6", "M7", "M8", "M9"))
    z = 8.0
    # beat 1: the five levels; a few signals already moving on M7 and M9
    D.run(root, "warm7", [(m7.segs[1][0] + 10, m7.yc, z), (m7.segs[1][1] - 10, m7.yc, z)], 5, 9.0, m["d_sig"], 1, 0.1, 0.7, 50)
    D.run(root, "warm9", [(m9.segs[0][1] - 10, m9.yc, z), (m9.segs[0][0] + 10, m9.yc, z)], 5, 9.0, m["d_sig"], 1, 0.2, 0.8, 50)
    # beat 2: a short hop: up a via from an M6 line onto an M7 wire, one block over
    xv = m7.vias_at[-1]
    a, b = next(sg for sg in m7.segs if sg[0] < xv < sg[1])
    end = max(a + 10, xv - 110.0) if xv - a > b - xv else min(b - 10, xv + 110.0)
    short = [(xv, m6.yc, z), (xv, m7.yc, z), (end, m7.yc, z)]
    D.run(root, "short", short, 14, 10.0, m["d_sig"], 2, 0.03, 0.8, 34)
    # beat 3: the same signal on the full-length M5 wire: delay grows about with length squared
    xl = m6.vias_at[0]
    long_ = [(xl, m6.yc, z), (xl, m5.yc, z), (X0 + 6 if xl > 0 else X1 - 6, m5.yc, z)]
    D.run(root, "long", long_, 6, 10.0, m["d_sig"], 3, 0.03, 0.4, 110)
    # beat 4: close on one M7 wire: R along its copper, C to the M6 lines under it
    g4 = group("rc", root, span(4))
    box("r_glow", (a, m7.y0 - 2, -4.0), (b, m7.y1 + 2, 5.0), m["d_hot"], g4)
    for k, x in enumerate(m6.xs):
        if a + 10 < x < b - 10:
            box(f"c_glow{k}", (x - 16, m6.y1 + 2, -4.0), (x + 16, m7.y0 - 2, 5.0), m["d_field"], g4)
    D.run(root, "rc_e", [(a + 6, m7.yc, z), (b - 6, m7.yc, z)], 6, 9.0, m["d_elec"], 4, 0.05, 0.6, 60)

    label("mid metal M5-M9", (1000.0, C.MID[1] - 60, 0), root, span(0))
    label("five levels, block to block", (X1 - 20, m9.yc, 2.0), root, span(1))
    label("vias join the levels", (m8.vias_at[0], (m7.cap_top + m8.y0) / 2, 2.0), root, span(1))
    label("SiCN cap on every level", (-150.0, m6.cap_top, 2.0), root, span(1))
    label("up a via", (xv, (m6.cap_top + m7.y0) / 2, z), root, span(2))
    label("short hop: one block over", ((xv + end) / 2, m7.yc, z), root, span(2))
    label("long run: arrives much later", ((xl + long_[-1][0]) / 2, m5.yc, z), root, span(3))
    label("R: the narrow copper", ((a + b) / 2, m7.yc, 5.0), root, span(4))
    label("C: to the wires below", (next((x for x in m6.xs if a + 10 < x < b - 10), a), (m6.y1 + m7.y0) / 2, 5.0), root, span(4))
    label("top metal M10-M14: lowest R", (1000.0, C.TOP[1] - 60, 0), root, span(5))
    label("long runs move up", (-1100.0, 1300.0, 0), root, span(5))
    cam(root, [
        WHOLE,
        frame(X0 - 10, -60.0, X1 + 10, lv["_top"] + 20, yaw=0.32, pitch=0.18),
        frame(X0 - 10, m6.y0 - 30, X1 + 10, m7.y1 + 40, yaw=0.25, pitch=0.15),
        frame(X0 - 10, -60.0, X1 + 10, m6.y1 + 30, yaw=0.25, pitch=0.15),
        frame(a - 30, m6.y0 - 20, b + 30, m7.y1 + 30, yaw=0.22, pitch=0.12),
        WHOLE,
    ])


def overview():
    build()
    finish("mid_metal", page="chip")


# ---- zoom-ins a-e -----------------------------------------------------------------------------
#
# a and e share their builders with sections 1 and 7; d is section 6 seen from the other side.

_AS = {}  # set by _as(): a section written out as a zoom, under the zoom's name


def _as(fn, name):
    _AS.update(name=name)
    try:
        fn()
    finally:
        _AS.clear()


def _cam(root, poses):
    if _AS:
        poses = [(t, d, -yaw, pitch) for t, d, yaw, pitch in poses]
    cam(root, poses)


def _finish(name, page="chip"):
    finish(f"mid_metal_{_AS['name']}" if _AS else name, page=page)


def zoom_a():
    """a, one dual-damascene pass: trench and via in one mask, one copper fill, CMP and the cap."""
    _damascene("zoom_a", 1)


def zoom_b():
    """b, RC delay: R along one wire, C through the low-k to the wires below, delay ~ L^2."""
    import chip_mid_metal_detail as D
    m, root = _sbegin("zoom_b", 3)
    g, lv = _block(root, m, [_spec("M5", "x", full=True), _spec("M6", "z"), _spec("M7", "x", full=True)])
    m5, m6, m7 = lv["M5"], lv["M6"], lv["M7"]
    z = 8.0
    g0 = group("r", root, span(0))
    box("r_glow", (X0 + 2, m7.y0 - 2, -4.0), (X1 - 2, m7.y1 + 2, 5.0), m["d_hot"], g0)
    D.run(root, "r_e", [(X0 + 8, m7.yc, z), (X1 - 8, m7.yc, z)], 9, 9.0, m["d_elec"], 0, 0.02, 0.7, 70)
    g1 = group("c", root, span(1))
    for k, x in enumerate(m6.xs):
        box(f"cv{k}", (x - 16, m6.y1 + 2, -4.0), (x + 16, m7.y0 - 2, 5.0), m["d_field"], g1)
    _field(g1, m, "cl", m6)
    D.run(root, "long", [(X0 + 8, m7.yc, z), (X1 - 8, m7.yc, z)], 5, 10.0, m["d_sig"], 2, 0.02, 0.3, 150)
    D.run(root, "short", [(-60.0, m5.yc, z), (80.0, m5.yc, z)], 16, 10.0, m["d_sig"], 2, 0.02, 0.85, 18)
    label("R = rho L / (W H)", (0.0, m7.yc, 5.0), root, span(0))
    label("electrons in the copper", (X1 - 60, m7.yc - 20, z), root, span(0))
    label("C: down to M6, through low-k", (m6.xs[2], (m6.y1 + m7.y0) / 2, 5.0), root, span(1))
    label("and line to line", ((m6.xs[3] + m6.xs[4]) / 2, m6.yc, 4.0), root, span(1))
    label("long wire: slow, delay ~ L^2", (X1 - 80, m7.yc, z), root, span(2))
    label("short hop: fast", (20.0, m5.yc, z), root, span(2))
    fr = frame(X0 - 10, -40.0, X1 + 10, m7.cap_top + 30, yaw=-0.28, pitch=0.16)
    cam(root, [frame(X0 - 10, m6.y1 - 20, X1 + 10, m7.cap_top + 40, yaw=-0.25, pitch=0.16),
               frame(X0 - 10, m6.y0 - 20, X1 + 10, m7.cap_top + 30, yaw=-0.25, pitch=0.16), fr])
    finish("mid_metal_zoom_b", page="chip")


def zoom_c():
    """c, low-k, air gaps and ruthenium: a porous film, then an air gap, then etched Ru lines."""
    m, root = _sbegin("zoom_c", 3)
    m["d_por"] = mat("d_por", (0.66, 0.70, 0.88), rough=0.6)
    g, lv = _block(root, m, [_spec("M6", "z", w=30.0)], x0=-160.0, x1=160.0)
    m6 = lv["M6"]
    gaps = _gaps(m6, -160.0, 160.0)
    mid = [(a + c) / 2 for a, c in gaps]
    for b, (mt, npores) in enumerate((("d_por", 9), ("d_air", 0))):
        sg = group(f"film{b}", root, span(b))
        for k, (a, c) in enumerate(gaps):
            if c - a < 1.0:
                continue
            box(f"film{b}_{k}", (a + 0.3, m6.y0 - 8, Z0 + 4 if mt == "d_air" else -8.0), (c - 0.3, m6.y1 + 0.2, -0.2), m[mt], sg)
            if npores:
                _pores(sg, m, f"p{b}_{k}_", a + 5, c - 5, m6.y0, m6.y1 - 4, [], npores, 4.5, k + 3)
    rx, rh = _grating(root, m, "ru", 300.0, 8, 25.0, ru=True)
    label("porous low-k: k ~2.5, soft", (mid[2], m6.yc, 2.0), root, span(0))
    label("pores lower k", (mid[3], m6.y0 + 10, 2.0), root, span(0))
    label("air gap: C down 25%+", (mid[2], m6.yc, 2.0), root, span(1))
    label("cap bridges the gap", (mid[3], m6.cap_top, 2.0), root, span(1))
    label("Ru: etched, no barrier", (rx[2], rh / 2, 2.0), root, span(2))
    label("air between the Ru lines", ((rx[4] + rx[5]) / 2, rh * 0.4, 2.0), root, span(2))
    fr = frame(-170.0, -70.0, 170.0, m6.cap_top + 30.0, yaw=-0.28, pitch=0.18)
    cam(root, [fr, fr, frame(290.0, -40.0, 510.0, 70.0, yaw=-0.22, pitch=0.22)])
    finish("mid_metal_zoom_c", page="chip")


def zoom_d():
    """d, electromigration: section 6 seen from the other side."""
    _as(sec6, "zoom_d")


def zoom_e():
    """e, vias, edge placement and RC extraction."""
    _vias("zoom_e", extract=True)


# ---- sections 1-10 ---------------------------------------------------------------------------
#
# The sections build a cut-away of the M5-M9 wiring itself (chip_mid_metal_detail.py), about
# 1 unit = 1 nm: copper lines at 80 nm pitch in TaN barrier and Ru/Co liner, vias, SiCN caps and
# low-k between. Barrier and liner are drawn a little thicker than life so they read.

import chip_mid_metal_detail as D  # noqa: E402
from chip_mid_metal_detail import box, cam, dots, frame, group, grow, slab, span, via, zline  # noqa: E402

X0, X1, Z0 = -240.0, 240.0, -300.0
BT, LT = 6.0, 4.0  # barrier and liner, drawn


def _spec(name, d, h=80.0, w=40.0, pitch=80.0, **kw):
    return dict(name=name, h=h, w=w, pitch=pitch, dir=d, gap=60.0, **kw)


MID_SPECS = [_spec("M5", "x"), _spec("M6", "z"), _spec("M7", "x"), _spec("M8", "z"), _spec("M9", "x")]


def _sbegin(name, beats):
    m, root = start(name, beats, page="chip")
    mats(m)
    D.mats(m)
    return m, root


def _block(root, m, specs, x0=X0, x1=X1, z0=Z0, base=60.0, **kw):
    g = empty("block", root)
    slab("base", x0, x1, -base, 0.0, z0, m["d_lowk"], g)
    return g, D.tower(g, m, specs, x0, x1, z0, bt=BT, lt=LT, **kw)


def _holes(name, g, mt, x0, x1, holes, y0, y1, z0, z1=-0.5):
    """A slab with gaps cut out along x (the trench or via openings)."""
    edges = [x0]
    for a, b in sorted(holes):
        edges += [a, b]
    edges.append(x1)
    for i in range(0, len(edges), 2):
        if edges[i + 1] - edges[i] > 0.5:
            box(f"{name}{i}", (edges[i], y0, z0), (edges[i + 1], y1, z1), mt, g)


def _pores(g, m, name, x0, x1, y0, y1, avoid, n, r=5.0, seed=1):
    """Dark pores dotted on the cut face of the dielectric, kept out of the `avoid` x spans."""
    k, i = 0, 0
    while k < n and i < n * 20:
        i += 1
        u = (math.sin(seed * 12.9898 + i * 78.233) * 43758.5453) % 1.0
        v = (math.sin(seed * 39.3468 + i * 11.135) * 24634.6345) % 1.0
        x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * v
        if any(a - r - 2 < x < b + r + 2 for a, b in avoid):
            continue
        ball(f"{name}{k}", (x, y, -2.0), r, m["d_pore"], g, 8)
        k += 1


def _gaps(lev, x0=X0, x1=X1):
    """The x spans between the outer barrier faces of a z level's lines."""
    o = lev.w / 2 + lev.lt + lev.bt
    edges = [x0] + [e for x in lev.xs for e in (x - o, x + o)] + [x1]
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


def _lines(lev):
    o = lev.w / 2 + lev.lt + lev.bt
    return [(x - o, x + o) for x in lev.xs]


def _field(g, m, name, lev, x0=X0, x1=X1):
    """Yellow bands across the gaps between neighbouring lines: the line-to-line capacitance."""
    for k, (a, b) in enumerate(_gaps(lev, x0, x1)[1:-1]):
        box(f"{name}{k}", (a + 2, lev.y0 + 12, -4.0), (b - 2, lev.y1 - 12, 3.0), m["d_field"], g)


def _bars(root, m, name, x0, items, scale, intervals_for, base=0.0, w=70.0, gap=50.0):
    """A bar chart of copper bars standing on a dark plinth: items [(height value, material)]."""
    g = empty(name, root)
    box(f"{name}_plinth", (x0 - 20, base - 20, -90), (x0 + len(items) * (w + gap) - gap + 20, base, 10), m["d_si"], g)
    tops = []
    for k, (v, mt) in enumerate(items):
        bg = group(f"{name}_b{k}", g, intervals_for(k))
        a = x0 + k * (w + gap)
        box(f"{name}_bar{k}", (a, base, -70), (a + w, base + v * scale, 0.0), m[mt], bg)
        tops.append((a + w / 2, base + v * scale))
    return tops


def _damascene(name, first):
    """One dual-damascene pass, building M6 on M5, in four states: 0 deposit, 1 pattern and etch,
    2 barrier and plate, 3 CMP and cap. `first` drops the states before it (section 1 plays all
    four; zoom a starts at the etch)."""
    m, root = _sbegin(name, 4 - first)

    def F(k, u):  # state k's beat, shifted; states before `first` fall before frame 0
        return FF(k - first, u)

    def span(k0, k1=None):
        k1 = k0 if k1 is None else k1
        return [] if k1 < first else [(F(max(k0, first), 0), F(k1 + 1, 0))]

    g, lv = _block(root, m, [_spec("M5", "x", full=True)])
    ya = lv["_top"]
    yt, yb = ya + 60.0, ya + 140.0  # via band ya..yt, trench band yt..yb
    xs, vx = [-160.0, -80.0, 0.0, 80.0, 160.0], [-80.0, 80.0]
    hw = 20.0 + LT + BT
    zv = -(20.0 + LT + BT) * 2 - 1.0  # the via openings reach this far back from the cut face

    # beat 0: the low-k film grows on the etch stop, then the TiN hard mask goes on
    dep = group("dep", root, span(0))
    grow("dep_p", dep, (0.0, ya, 0.0), lambda p: box("dep_slab", (X0, 0.0, Z0), (X1, yb - ya, -0.5), m["d_lowk"], p),
         [(F(0, 0.05), (1, 1, 0.03)), (F(0, 0.5), (1, 1, 1))])
    mask_full = group("mask_full", root, ([(F(0, 0.55), F(1, 0))] if first == 0 else []))
    slab("mask_f", X0, X1, yb, yb + 10.0, Z0, m["d_mask"], mask_full, front=-0.3)

    # beats 1-3: the etched film (trenches and via holes cut out)
    et = group("etched", root, span(1, 3))
    _holes("trench_ild", et, m["d_lowk"], X0, X1, [(x - hw, x + hw) for x in xs], yt, yb, Z0)
    _holes("via_ild_f", et, m["d_lowk"], X0, X1, [(x - hw, x + hw) for x in vx], ya, yt, zv)
    slab("via_ild_b", X0, X1, ya, yt, Z0, m["d_lowk"], et, front=zv)
    mask = group("mask_holes", root, [(F(1, 0), F(3, 0.3))])
    _holes("mask_h", mask, m["d_mask"], X0, X1, [(x - hw, x + hw) for x in xs], yb, yb + 10.0, Z0, z1=-0.3)
    plasma = group("plasma", root, [(F(1, 0.1), F(1, 0.6))])
    for k, x in enumerate(xs):
        box(f"pl{k}", (x - hw + 3, yt + 3, Z0 + 10), (x + hw - 3, yb + 30, -3.0), m["d_plasma"], plasma)
    for k, x in enumerate(vx):
        box(f"plv{k}", (x - hw + 3, ya + 3, zv + 3), (x + hw - 3, yt, -3.0), m["d_plasma"], plasma)

    # beat 2: barrier and liner first, then copper plates up through via and trench at once
    shell = group("shell", root, [(F(2, 0), F(2, 0.35))])
    for k, x in enumerate(xs):
        zline(f"sh{k}", shell, m, x, yt, 40.0, 80.0, Z0 + 2, BT, LT, cu=False)
    for k, x in enumerate(vx):
        via(f"shv{k}", shell, m, x, -20.5, lv["M5"].y1, yt, 40.0, BT, LT, front=0.0, cu=False)
    cu = group("cu", root, [(F(2, 0.35), F(4, 0))])
    for k, x in enumerate(xs):
        zline(f"ln{k}", cu, m, x, yt, 40.0, 80.0, Z0 + 2, BT, LT)
    for k, x in enumerate(vx):
        via(f"lv{k}", cu, m, x, -20.5, lv["M5"].y1, yt, 40.0, BT, LT, front=0.0)
    over = group("overburden", root, [(F(2, 0.35), F(3, 0.3))])
    grow("over_p", over, (0.0, yb + 10.0, 0.0), lambda p: box("over_cu", (X0, 0.0, Z0), (X1, 40.0, 1.0), m["d_cu"], p),
         [(F(2, 0.4), (1, 1, 0.05)), (F(2, 0.85), (1, 1, 1))])

    # beat 3: the CMP pad sweeps across, then the SiCN cap seals the level
    pad = group("cmp", root, [(F(3, 0), F(3, 0.32))])
    pad_m = empty("cmp_move", pad)
    box("cmp_pad", (-260.0, yb + 52.0, Z0 - 20), (260.0, yb + 90.0, 20.0), m["d_mask"], pad_m)
    key(pad_m, F(3, 0), "location", D_P(-500.0, 0, 0), linear=True)
    key(pad_m, F(3, 0.3), "location", D_P(500.0, 0, 0), linear=True)
    cap = group("cap6", root, [(F(3, 0.3), F(4, 0))])
    slab("cap6_s", X0, X1, yb + 0.4, yb + 10.0, Z0, m["d_cap"], cap, front=-0.3)

    label("low-k film deposited", (X1 - 30.0, ya + 90.0, 2.0), root, ([(F(0, 0.3), F(1, 0))] if first == 0 else []))
    label("SiCN etch stop", (-200.0, ya - 4.0, 2.0), root, span(0))
    label("TiN hard mask", (120.0, yb + 6.0, 2.0), root, ([(F(0, 0.55), F(1, 0))] if first == 0 else []))
    label("trench: the wire", (0.0, yb - 20.0, 2.0), root, span(1))
    label("via hole down to M5", (80.0, ya + 20.0, 2.0), root, span(1))
    label("M5 below", (-200.0, ya - 50.0, 2.0), root, span(1))
    label("TaN barrier + Ru liner", (-160.0 - 20.0 - LT - BT / 2, yt + 40.0, 2.0), root, [(F(2, 0), F(2, 0.4))])
    label("Cu plated: via and trench", (-80.0, yt - 30.0, 2.0), root, [(F(2, 0.4), F(3, 0))])
    label("excess copper", (150.0, yb + 40.0, 2.0), root, [(F(2, 0.6), F(3, 0))])
    label("CMP polishes flat", (0.0, yb + 70.0, 2.0), root, [(F(3, 0), F(3, 0.35))])
    label("SiCN cap seals M6", (150.0, yb + 6.0, 2.0), root, [(F(3, 0.35), F(4, 0))])
    label("repeat: M7, M8, M9", (-150.0, yb + 6.0, 2.0), root, [(F(3, 0.5), F(4, 0))])
    yaw = 0.32 if first == 0 else -0.30
    fr = frame(X0 - 10, -30.0, X1 + 10, yb + 70.0, yaw=yaw, pitch=0.22)
    poses = [fr, fr, frame(X0, ya - 40, X1, yb + 60, yaw=yaw, pitch=0.22), fr]
    cam(root, poses[first:])
    finish(f"mid_metal_{name}", page="chip")


def sec1():
    """1, what happens: one dual-damascene pass, building M6 on M5: deposit, etch, fill, polish."""
    _damascene("sec1", 0)


def D_P(x, y, z):
    from sand_overview import P
    return P(x, y, z)


def sec2():
    """2, dual damascene in section: the line, the via, the cap, the ultra-low-k."""
    m, root = _sbegin("sec2", 4)
    g, lv = _block(root, m, MID_SPECS[:3])
    m6, m7 = lv["M6"], lv["M7"]
    xv = m7.vias_at[0]  # a line with a via up to M7
    busy = set(m7.vias_at) | set(m6.vias_at)
    xl = min((x for x in m6.xs if x not in busy), key=lambda x: abs(x - (xv - 80.0)))  # a plain line
    # beat 1: the via foot, copper on copper
    foot = group("foot", root, span(1))
    box("foot_glow", (xv - m7.via_w / 2 - 4, m6.y1 - 4, -m7.via_w - 6), (xv + m7.via_w / 2 + 4, m6.y1 + 6, 3.0), m["d_ok"], foot)
    # beat 2: the cap glows
    capg = group("capglow", root, span(2))
    box("cap_glow", (X0, m6.y1 + 0.4, -6.0), (X1, m6.cap_top + 1.0, 2.0), m["d_field"], capg)
    # beat 3: the pores of the ultra-low-k
    pores = group("pores", root, span(3))
    _pores(pores, m, "pore", X0 + 8, X1 - 8, m6.y0 + 4, m6.y1 - 4, _lines(m6), 26, 5.0, 2)
    _pores(pores, m, "porev", X0 + 8, X1 - 8, m6.cap_top + 6, m7.y0 - 14, [(x - 26, x + 26) for x in m7.vias_at], 14, 5.0, 3)

    o = 20.0 + LT
    label("Cu line, 40 nm wide", (xl, m6.yc, 2.0), root, span(0))
    label("TaN/Ta barrier", (xl - o - BT / 2, m6.y0 + 12, 2.0), root, span(0))
    label("Ru or Co liner", (xl + 20.0 + LT / 2, m6.yc - 10, 2.0), root, span(0))
    label("via and line: one Cu fill", (xv, (m6.cap_top + m7.y0) / 2, 2.0), root, span(1))
    label("no barrier at the via foot", (xv + 20, m6.y1, 3.0), root, span(1))
    label("M7 line above", (60.0, m7.yc, 2.0), root, span(1))
    label("SiCN cap: higher k", (150.0, (m6.y1 + m6.cap_top) / 2, 3.0), root, span(2))
    label("cap between every level", (-200.0, (m7.y1 + m7.cap_top) / 2, 3.0), root, span(2))
    label("ultra-low-k between lines", ((m6.xs[3] + m6.xs[4]) / 2, m6.yc + 20, 2.0), root, span(3))
    label("pores lower k", (-200.0, (m6.cap_top + m7.y0) / 2, 2.0), root, span(3))
    cam(root, [
        frame(xl - 110, m6.y0 - 40, xl + 110, m6.y1 + 50, yaw=0.18, pitch=0.12),
        frame(max(X0 - 10, xv - 130), m6.y0 - 20, max(X0 - 10, xv - 130) + 260, m7.y1 + 30, yaw=0.25, pitch=0.15),
        frame(X0, m6.y0 - 20, X1, m7.y1 + 30, yaw=0.30, pitch=0.18),
        frame(X0, lv["M5"].y0 - 20, X1, m7.cap_top + 20, yaw=0.30, pitch=0.20),
    ])
    finish("mid_metal_sec2", page="chip")


THREE_TIERS = [
    dict(name="M2", h=30.0, w=16.0, pitch=32.0, dir="z", gap=24.0, bt=3.0, lt=2.0),
    dict(name="M3", h=30.0, w=16.0, pitch=32.0, dir="x", gap=24.0, bt=3.0, lt=2.0),
    dict(name="M6", h=80.0, w=40.0, pitch=80.0, dir="z", gap=60.0),
    dict(name="M7", h=80.0, w=40.0, pitch=80.0, dir="x", gap=60.0),
    dict(name="M12", h=240.0, w=200.0, pitch=300.0, dir="z", gap=160.0, bt=10.0, lt=6.0),
    dict(name="M13", h=240.0, w=200.0, pitch=300.0, dir="x", gap=160.0, bt=10.0, lt=6.0),
]


def sec3():
    """3, RC delay: a thin, a medium and a thick level; the signal crosses each at its own speed."""
    m, root = _sbegin("sec3", 3)
    g = empty("block", root)
    slab("base", -300.0, 300.0, -40.0, 0.0, Z0, m["d_lowk"], g)
    lv = D.tower(g, m, THREE_TIERS, -300.0, 300.0, Z0, bt=BT, lt=LT)
    m2, m3, m6, m7, m12, m13 = (lv[k] for k in ("M2", "M3", "M6", "M7", "M12", "M13"))
    # beat 0: one signal across each tier's front line; thin is slowest
    for name, lev, life, size in (("thin", m3, 170, 12.0), ("mid", m7, 70, 22.0), ("thick", m13, 26, 40.0)):
        dots(root, f"sig_{name}", [(-290.0, lev.yc, 6.0), (290.0, lev.yc, 6.0)], 7, size, m["d_sig"], 0, 0.03, 0.55, life)
    # beat 1: the capacitance between neighbouring M6 lines
    fg = group("field", root, span(1))
    _field(fg, m, "fld", m6, -300.0, 300.0)
    # beat 2: the size effect: the thin lines run hot, the wide ones do not
    hot = group("hot", root, span(2))
    for k, x in enumerate(m2.xs):
        box(f"hot{k}", (x - 8.5, m2.y0 - 1, -3.0), (x + 8.5, m2.y1 + 1, 3.0), m["d_hot"], hot)
    label("M2-M3: thin, highest R", (220.0, m3.yc, 6.0), root, span(0))
    label("M6-M7: R and C balanced", (220.0, m7.yc, 6.0), root, span(0))
    label("M12-M13: thick, lowest R", (150.0, m13.yc, 6.0), root, span(0))
    label("C: line to line", (0.0, m6.yc, 4.0), root, span(1))
    label("C grows with k and H/S", (-200.0, m6.y1 - 10, 4.0), root, span(1))
    label("R falls with W x H", (150.0, m7.yc, 2.0), root, span(1))
    label("thin Cu: over 3.0 uOhm-cm", (m2.xs[len(m2.xs) // 2], m2.yc, 4.0), root, span(2))
    label("wide Cu: about 2.0 uOhm-cm", (0.0, m6.yc, 2.0), root, span(2))
    top = lv["_top"]
    cam(root, [
        frame(-310.0, -40.0, 310.0, top + 20.0, yaw=0.28, pitch=0.16),
        frame(-310.0, m6.y0 - 40, 310.0, m7.y1 + 40, yaw=0.25, pitch=0.16),
        frame(-310.0, m2.y0 - 40, 310.0, m6.y1 + 40, yaw=0.25, pitch=0.18),
    ])
    finish("mid_metal_sec3", page="chip")


def _grating(root, m, name, x0, n, pitch, intervals=None, two_tone=False, ru=False, depth=160.0, oy=0.0):
    """A row of n lines at `pitch` (w = pitch / 2, h = pitch) on a dielectric base, cut-away.
    two_tone: alternate lines tinted (two exposures); ru: etched ruthenium, no barrier, air gaps."""
    g = empty(name, root) if intervals is None else group(name, root, intervals)
    g.location = D_P(0.0, oy, 0.0)
    w, h = pitch / 2, pitch
    x1 = x0 + n * pitch
    slab(f"{name}_base", x0, x1, -pitch * 0.6, 0.0, -depth, m["d_lowk"], g)
    xs = [x0 + pitch / 2 + k * pitch for k in range(n)]
    for k, x in enumerate(xs):
        if ru:
            box(f"{name}_ru{k}", (x - w / 2, 0.0, -depth + 2), (x + w / 2, h, D.EPS), m["d_ru"], g)
        else:
            y0 = max(1.5, 0.06 * pitch) + max(1.0, 0.04 * pitch)
            zline(f"{name}_l{k}", g, m, x, y0, w, h - y0, -depth + 2,
                  max(1.5, 0.06 * pitch), max(1.0, 0.04 * pitch))
        if two_tone:
            mt = m["d_vdd_rail"] if k % 2 == 0 else m["d_vss_rail"]
            box(f"{name}_tone{k}", (x - w / 2 - 1.5, h + 4, -depth + 2), (x + w / 2 + 1.5, h + 4 + pitch * 0.18, 2.0), mt, g)
    if ru:
        for k in range(n - 1):
            a, b = xs[k] + w / 2, xs[k + 1] - w / 2
            box(f"{name}_air{k}", (a + 0.6, 0.0, -depth + 2), (b - 0.6, h * 0.85, 0.2), m["d_air"], g)
        slab(f"{name}_ild", x0, x1, h * 0.85, h + 0.4, -depth, m["d_lowk"], g)
        slab(f"{name}_cap", x0, x1, h + 0.4, h + pitch * 0.12, -depth, m["d_cap"], g, front=-0.3)
    else:
        slab(f"{name}_ild", x0, x1, 0.0, h + 0.3, -depth, m["d_lowk"], g)
        slab(f"{name}_cap", x0, x1, h + 0.5, h + pitch * 0.12, -depth, m["d_cap"], g, front=-0.3)
    # a dimension bar over one pitch, line centre to line centre
    box(f"{name}_dim", (xs[1], h + pitch * 0.45, -2.0), (xs[2], h + pitch * 0.45 + 2.0, 3.0), m["d_field"], g)
    for k, x in enumerate((xs[1], xs[2])):
        box(f"{name}_tick{k}", (x - 1.0, h + pitch * 0.3, -2.0), (x + 1.0, h + pitch * 0.6, 3.0), m["d_field"], g)
    return xs, h


def sec4():
    """4, pitch and patterning: published pitches as gratings, EUV single vs double, etched Ru."""
    m, root = _sbegin("sec4", 3)
    a, ah = _grating(root, m, "i7m2", -110.0, 5, 44.0, oy=0.0)
    b, bh = _grating(root, m, "i7m4", -130.0, 5, 52.0, oy=150.0)
    c, ch = _grating(root, m, "i4m2", -112.0, 5, 45.0, oy=310.0)
    d, dh = _grating(root, m, "n3e", 400.0, 8, 23.0, oy=0.0)
    e, eh = _grating(root, m, "n3b", 400.0, 8, 23.0, two_tone=True, oy=90.0)
    f, fh = _grating(root, m, "ru", 1000.0, 8, 25.0, ru=True)
    label("Intel 7 M2: 44 nm", ((a[1] + a[2]) / 2, ah + 22.0, 3.0), root, span(0))
    label("Intel 7 M4: 52 nm", ((b[1] + b[2]) / 2, 150.0 + bh + 26.0, 3.0), root, span(0))
    label("Intel 4 M2: 45 nm, some EUV", ((c[1] + c[2]) / 2, 310.0 + ch + 22.0, 3.0), root, span(0))
    label("TSMC N3E M0: 23 nm", ((d[1] + d[2]) / 2, dh + 11.0, 3.0), root, span(1))
    label("one EUV exposure", (d[6], dh / 2, 2.0), root, span(1))
    label("two exposures, two colours", (e[5], 90.0 + eh + 6.0, 3.0), root, span(1))
    label("etched Ru, no barrier", (f[2], fh / 2, 2.0), root, span(2))
    label("air gap: -25% line-line C", ((f[4] + f[5]) / 2, fh * 0.4, 2.0), root, span(2))
    label("Intel IEDM 2024: 25 nm", ((f[1] + f[2]) / 2, fh + 12.0, 3.0), root, span(2))
    cam(root, [
        frame(-140.0, -40.0, 160.0, 420.0, yaw=0.25, pitch=0.20),
        frame(390.0, -30.0, 600.0, 150.0, yaw=0.25, pitch=0.22),
        frame(990.0, -40.0, 1210.0, 70.0, yaw=0.22, pitch=0.22),
    ])
    finish("mid_metal_sec4", page="chip")


def sec5():
    """5, the dielectric: SiO2, carbon-doped oxide, porous CDO, then an air gap, with stiffness bars."""
    m, root = _sbegin("sec5", 4)
    m["d_cdo"] = D.mat("d_cdo", (0.50, 0.56, 0.80), rough=0.5)
    m["d_por"] = D.mat("d_por", (0.66, 0.70, 0.88), rough=0.6)
    m["d_sio2s"] = D.mat("d_sio2s", (0.86, 0.88, 0.95), rough=0.35)
    g, lv = _block(root, m, [_spec("M6", "z", w=30.0)], x0=-160.0, x1=160.0)
    m6 = lv["M6"]
    gaps = _gaps(m6, -160.0, 160.0)
    mid = [((a + c) / 2) for a, c in gaps]
    for b, (mt, npores) in enumerate((("d_sio2s", 0), ("d_cdo", 3), ("d_por", 9), ("d_air", 0))):
        sg = group(f"film{b}", root, span(b))
        for k, (a, c) in enumerate(gaps):
            if c - a < 1.0:
                continue
            z_back = Z0 + 4 if mt == "d_air" else -8.0
            box(f"film{b}_{k}", (a + 0.3, m6.y0 - 8, z_back), (c - 0.3, m6.y1 + 0.2, -0.2), m[mt], sg)
            if npores:
                _pores(sg, m, f"p{b}_{k}_", a + 5, c - 5, m6.y0, m6.y1 - 4, [], npores, 4.5, b * 10 + k)
        lower = "d_sio2s" if mt == "d_air" else mt
        box(f"film{b}_low", (-159.7, -59.0, -8.0), (159.7, m6.y0 - 8, -0.2), m[lower], sg)
        if npores:
            _pores(sg, m, f"pl{b}_", -150.0, 150.0, -50.0, m6.y0 - 14, [], npores * 4, 4.5, b * 7 + 3)
    tops = _bars(root, m, "gpa", 200.0, [(72.0, "d_sio2s"), (8.5, "d_cdo"), (3.0, "d_por")], 3.0,
                 lambda k: [(F(k, 0), F(4, 0))], base=-60.0, w=50.0, gap=30.0)
    label("SiO2: k 4.0", (mid[2], m6.yc, 2.0), root, span(0))
    label("SiO2: 72 GPa, stiff", (tops[0][0], tops[0][1], 2.0), root, span(0))
    label("carbon-doped oxide: k 2.7", (mid[2], m6.yc, 2.0), root, span(1))
    label("CDO: 7-10 GPa", (tops[1][0], tops[1][1] + 4, 2.0), root, span(1))
    label("58% porous CDO", (mid[2], m6.yc, 2.0), root, span(2))
    label("porous: 3 GPa, soft", (tops[2][0], tops[2][1] + 4, 2.0), root, span(2))
    label("air gap: C down 25%+", (mid[2], m6.yc, 2.0), root, span(3))
    label("cap bridges the gap", (mid[3], m6.cap_top, 2.0), root, span(3))
    fr = frame(-170.0, -80.0, 440.0, 170.0, yaw=0.22, pitch=0.16)
    cam(root, [fr, fr, fr, frame(-170.0, -70.0, 170.0, m6.cap_top + 30.0, yaw=0.30, pitch=0.18)])
    finish("mid_metal_sec5", page="chip")


def sec6():
    """6, electromigration: electron wind drifts copper atoms; a void and a hillock; a cobalt cap."""
    m, root = _sbegin("sec6", 3)
    specs = [_spec("M6", "z"), _spec("M7", "x", via_at=[0], full=True), _spec("M8", "z", via_at=[9])]
    g, lv = _block(root, m, specs, x0=-420.0, x1=420.0)
    m6, m7, m8 = lv["M6"], lv["M7"], lv["M8"]
    xa, xb = m6.xs[0], m8.xs[-1]
    zc = 6.0
    for b, n in ((0, 12), (1, 12), (2, 12)):
        dots(root, f"e{b}", [(xa, m7.yc - 10, zc), (xb, m7.yc - 10, zc)], n, 9.0, m["d_elec"], b, 0.02, 0.7, 40)
    dots(root, "atoms0", [(xa + 30, m7.y1 - 8, zc), (xb - 30, m7.y1 - 8, zc)], 10, 6.0, m["d_atom"], 0, 0.02, 0.7, 150)
    dots(root, "atoms1", [(xa + 30, m7.y1 - 8, zc), (xb - 30, m7.y1 - 8, zc)], 10, 6.0, m["d_atom"], 1, 0.02, 0.7, 150)
    dots(root, "atoms2", [(xa + 30, m7.y1 - 8, zc), (xa + 160, m7.y1 - 8, zc)], 4, 6.0, m["d_atom"], 2, 0.05, 0.6, 150)
    # beat 1: a void opens just downstream of the via, a hillock grows at the far end
    vg = group("void", root, span(1))
    grow("void_p", vg, (xa + 70.0, m7.y1, 0.0), lambda p: box("void_b", (-45.0, -50.0, -50.0), (45.0, 0.5, 7.0), m["d_void"], p),
         [(F(1, 0.1), 0.05), (F(1, 0.7), 1.0)])
    hg = group("hill", root, span(1))
    grow("hill_p", hg, (xb - 90.0, m7.y1, 0.0), lambda p: box("hill_b", (-40.0, 0.0, -50.0), (40.0, 36.0, 7.0), m["d_cu"], p),
         [(F(1, 0.1), 0.05), (F(1, 0.7), 1.0)])
    hot = group("hot", root, [(F(1, 0.3), F(2, 0))])
    box("hot_line", (xa + 130.0, m7.y0 - 2, -3.0), (xb - 150.0, m7.y1 + 2, 4.0), m["d_hot"], hot)
    # beat 2: a cobalt cap on the copper replaces the SiCN interface
    co = group("cocap", root, span(2))
    box("co_cap", (-418.0, m7.y1 + 0.5, Z0 + 2), (418.0, m7.y1 + 7.0, 1.5), m["d_cocap"], co)
    label("electron wind", (0.0, m7.yc - 10, zc), root, span(0))
    label("Cu atoms drift along the cap", (xb - 200.0, m7.y1 - 8, zc), root, span(0))
    label("void opens: R rises", (xa + 70.0, m7.y1 - 30, 3.0), root, span(1))
    label("hillock pushes up", (xb - 90.0, m7.y1 + 20, 3.0), root, span(1))
    label("MTTF = A J^-n exp(Ea/kT)", (0.0, m8.yc, 2.0), root, span(1))
    label("Co cap: the drift slows", (100.0, m7.y1 + 4, 3.0), root, span(2))
    label("current in via", (xa, (m6.y1 + m7.y0) / 2, 2.0), root, span(0))
    fr = frame(-430.0, m6.y0 - 20, 430.0, m8.y1 + 20, yaw=0.18, pitch=0.12)
    _cam(root, [fr, fr, frame(-430.0, m6.y1 - 20, 430.0, m7.cap_top + 120, yaw=0.18, pitch=0.18)])
    _finish("mid_metal_sec6")


def _vias(name, extract=False):
    """A landed via, a misplaced one, then a self-aligned one (section 7) or, with `extract`, the
    R and C of every wire picked out for timing sign-off (zoom e)."""
    m, root = _sbegin(name, 3)
    g, lv = _block(root, m, [_spec("M6", "z"), _spec("M7", "x", full=True)], vias=False)
    m6, m7 = lv["M6"], lv["M7"]
    xt = -40.0
    for b, (x, s, glow) in enumerate(((xt, 40.0, "d_ok"), (xt + 24.0, 40.0, "d_bad"), (xt, 40.0, "d_ok"))[: 2 if extract else 3]):
        vg = group(f"via{b}", root, span(b))
        via(f"v{b}", vg, m, x, -20.5, m6.y1, m7.y0, s, BT, LT, front=0.0)
        if b == 1:
            # the overhang off the line's edge, and the thin dielectric left to the neighbour
            box("over_glow", (xt + 20 + LT + BT, m6.y1 - 30, -42.0), (x + 20 + LT + BT, m6.y1 + 2, 3.0), m["d_bad"], vg)
        else:
            box(f"foot{b}", (x - 22, m6.y1 - 3, -42.0), (x + 22, m6.y1 + 5, 3.0), m[glow], vg)
        if b == 2:
            # the mask opening was wider and off-centre; the line grating trimmed it to the line
            box("sav_mask", (xt - 36, m7.y0 - 4, -46.0), (xt + 46, m7.y0 + 4, 3.0), m["d_field"], vg)
    label("via lands on the line", (xt, (m6.cap_top + m7.y0) / 2, 3.0), root, span(0))
    label("full contact, low R", (xt - 20, m6.y1, 3.0), root, span(0))
    label("off by ~1/4 pitch: less contact", (xt + 34, m6.y1 - 14, 3.0), root, span(1))
    label("thin gap to neighbour: short risk", (40.0 - 26, m6.yc, 3.0), root, span(1))
    if extract:
        import chip_mid_metal_detail as D
        rc = group("rc", root, span(2))
        via("v_rc", rc, m, xt, -20.5, m6.y1, m7.y0, 40.0, BT, LT, front=0.0)
        box("r_glow", (X0 + 2, m7.y0 - 2, -4.0), (X1 - 2, m7.y1 + 2, 5.0), m["d_hot"], rc)
        _field(rc, m, "cl", m6)
        D.run(root, "rc_e", [(X0 + 8, m7.yc, 8.0), (X1 - 8, m7.yc, 8.0)], 6, 9.0, m["d_elec"], 2, 0.05, 0.6, 60)
        label("R of the wire", (120.0, m7.yc, 5.0), root, span(2))
        label("C to its neighbours", ((m6.xs[3] + m6.xs[4]) / 2, m6.yc, 4.0), root, span(2))
        label("StarRC, Quantus extract both", (-150.0, m7.y1 - 10, 5.0), root, span(2))
        poses = [frame(-230.0, m6.y0 - 30, 170.0, m7.y1 + 30, yaw=-0.22, pitch=0.12)] * 2
        poses.append(frame(X0 - 10, m6.y0 - 40, X1 + 10, m7.cap_top + 30, yaw=-0.25, pitch=0.15))
    else:
        label("self-aligned via", (xt, (m6.cap_top + m7.y0) / 2, 3.0), root, span(2))
        label("wide opening, trimmed to line", (xt + 40, m7.y0, 3.0), root, span(2))
        poses = [frame(-230.0, m6.y0 - 30, 170.0, m7.y1 + 30, yaw=0.22, pitch=0.12)] * 3
    cam(root, poses)
    finish(f"mid_metal_{name}", page="chip")


def sec7():
    """7, vias and edge placement: a landed via, a misplaced one, a self-aligned one."""
    _vias("sec7")


def sec8():
    """8, who makes it: the tool for each layer, then RC extraction, then Applied's China share."""
    m, root = _sbegin("sec8", 3)
    g, lv = _block(root, m, MID_SPECS[:3])
    m5, m6, m7 = lv["M5"], lv["M6"], lv["M7"]
    rc = group("rc", root, span(1))
    _field(rc, m, "fld", m6)
    box("r_line", (X0 + 2, m7.y0 - 2, -3.0), (X1 - 2, m7.y1 + 2, 4.0), m["d_hot"], rc)
    tops = _bars(root, m, "amat", 340.0, [(28.4, "d_cu"), (8.5, "d_hot")], 14.0, lambda k: span(2), base=0.0, w=70.0, gap=40.0)
    label("low-k: Applied Black Diamond", (-200.0, (m6.cap_top + m7.y0) / 2, 2.0), root, span(0))
    label("barrier, seed: Applied Endura", (-120.0 - 20 - LT - BT / 2, m6.yc, 2.0), root, span(0))
    label("Cu plating: Lam SABRE", (-40.0, m6.yc, 2.0), root, span(0))
    label("CMP: Applied, Ebara", (150.0, m7.cap_top, 2.0), root, span(0))
    label("R of each wire", (150.0, m7.yc, 4.0), root, span(1))
    label("C between wires", (0.0, m6.yc, 4.0), root, span(1))
    label("StarRC, Quantus extract both", (-150.0, m5.yc, 2.0), root, span(1))
    label("Applied FY2025: $28.4B", tops[0] + (2.0,), root, span(2))
    label("China: $8.5B, 30%", tops[1] + (2.0,), root, span(2))
    fr = frame(X0 - 10, -40.0, X1 + 10, m7.cap_top + 30, yaw=0.30, pitch=0.18)
    cam(root, [fr, fr, frame(X0, -40.0, 560.0, 440.0, yaw=0.20, pitch=0.15)])
    finish("mid_metal_sec8", page="chip")


def sec9():
    """9, chokepoints: the copper wall at tight pitch, damaged porous low-k, the shift to Ru."""
    m, root = _sbegin("sec9", 3)
    # beat 0: copper and ruthenium at ~20 nm pitch, side by side
    g0 = empty("narrow", root)
    slab("nb", -70.0, 70.0, -14.0, 0.0, -120.0, m["d_lowk"], g0)
    slab("n_ild", -70.0, 70.0, 0.0, 22.0, -120.0, m["d_lowk"], g0)
    slab("n_cap", -70.0, 70.0, 22.4, 25.0, -120.0, m["d_cap"], g0, front=-0.3)
    cu_x = [-50.0 + 20 * k for k in range(6)]
    ru_x = cu_x
    for k, x in enumerate(cu_x):
        zline(f"ncu{k}", g0, m, x, 3.5, 3.0, 18.5, -118.0, 2.5, 1.0)
    g0r = empty("narrow_ru", root)
    g0r.location = D_P(0.0, -60.0, 0.0)
    slab("rb", -70.0, 70.0, -14.0, 0.0, -120.0, m["d_lowk"], g0r)
    slab("r_cap", -70.0, 70.0, 22.4, 25.0, -120.0, m["d_cap"], g0r, front=-0.3)
    for k, x in enumerate(ru_x):
        box(f"nru{k}", (x - 5.0, 0.0, -118.0), (x + 5.0, 22.0, D.EPS), m["d_ru"], g0r)
        if k < 5:
            box(f"nair{k}", (x + 5.6, 0.0, -118.0), (x + 14.4, 19.0, 0.2), m["d_air"], g0r)
    slab("r_top", -70.0, 70.0, 19.0, 22.4, -120.0, m["d_lowk"], g0r)
    # beat 1: the porous low-k next to a mid level, its trench walls damaged by the etch plasma
    g1 = empty("ulk", root)
    g1.location = D_P(700.0, 0.0, 0.0)
    _, lv = _block(g1, m, [_spec("M6", "z"), _spec("M7", "x")], x0=-200.0, x1=200.0)
    m6 = lv["M6"]
    dmg = group("damage", g1, span(1))
    for k, x in enumerate(m6.xs):
        for s in (-1, 1):
            a = x + s * (20 + LT + BT)
            box(f"dmg{k}_{s}", (min(a, a + s * 9), m6.y0 - 8, -60.0), (max(a, a + s * 9), m6.y1, 1.2), m["d_damage"], dmg)
    pl = group("plasma9", g1, [(F(1, 0), F(1, 0.35))])
    for k, x in enumerate(m6.xs):
        box(f"pl9{k}", (x - 30, m6.y1 + 2, -60.0), (x + 30, m6.y1 + 60, 0.0), m["d_plasma"], pl)
    hot = group("hot9", g1, [(F(1, 0.4), F(2, 0))])
    box("hot9_l", (m6.xs[2] - 22, m6.y0 - 2, -4.0), (m6.xs[2] + 22, m6.y1 + 2, 3.0), m["d_hot"], hot)
    # beat 2: Applied's sales by region and the etched-Ru line that changes the tool mix
    tops = _bars(root, m, "china", 1300.0, [(70.0, "d_cu_dim"), (30.0, "d_hot")], 3.0, lambda k: span(2), base=0.0, w=70.0, gap=40.0)
    rx, rh = _grating(root, m, "ru9", 1560.0, 6, 25.0, intervals=span(2), ru=True, oy=0.0)
    label("Cu at ~20 nm pitch: barrier eats it", (cu_x[2], 12.0, 2.0), root, span(0))
    label("Ru: no barrier, more metal", (ru_x[3], -48.0, 2.0), root, span(0))
    label("plasma-damaged ULK wall", (700.0 + m6.xs[1] + 26, m6.yc, 2.0), root, span(1))
    label("more current: EM", (700.0 + m6.xs[2], m6.y1 - 10, 4.0), root, span(1))
    label("Applied FY2025: China ~30%", tops[1] + (2.0,), root, span(2))
    label("rest of world ~70%", tops[0] + (2.0,), root, span(2))
    label("tight levels: etched Ru", (rx[3], rh / 2, 2.0), root, span(2))
    cam(root, [
        frame(-75.0, -80.0, 75.0, 30.0, yaw=0.20, pitch=0.18, zc=-10.0),
        frame(480.0, -40.0, 920.0, 330.0, yaw=0.25, pitch=0.18),
        frame(1280.0, -30.0, 1720.0, 240.0, yaw=0.20, pitch=0.15),
    ])
    finish("mid_metal_sec9", page="chip")


def sec10():
    """10, sources: the M5-M9 cut-away from four sides while the source list is read."""
    m, root = _sbegin("sec10", 4)
    g, lv = _block(root, m, MID_SPECS)
    top = lv["_top"]
    label("M5-M9 cut-away", (X1 - 30, top - 30, 2.0), root, span(0))
    label("via between levels", (lv["M7"].vias_at[0], (lv["M6"].cap_top + lv["M7"].y0) / 2, 2.0), root, span(1))
    label("Cu lines in low-k", (-120.0, lv["M8"].yc, 2.0), root, span(2))
    label("SiCN caps", (150.0, lv["M7"].cap_top, 2.0), root, span(3))
    cam(root, [
        frame(X0, -60.0, X1, top + 20, yaw=0.35, pitch=0.18),
        frame(lv["M7"].vias_at[0] - 120, lv["M6"].y0 - 20, lv["M7"].vias_at[0] + 120, lv["M7"].y1 + 20, yaw=0.20, pitch=0.12),
        frame(X0, -60.0, X1, top + 20, yaw=-0.30, pitch=0.30),
        frame(X0, -60.0, X1, top + 20, yaw=0.10, pitch=0.10),
    ])
    finish("mid_metal_sec10", page="chip")


SCENES = {
    "overview": overview,
    "zoom_a": zoom_a,
    "zoom_b": zoom_b,
    "zoom_c": zoom_c,
    "zoom_d": zoom_d,
    "zoom_e": zoom_e,
    "sec1": sec1,
    "sec2": sec2,
    "sec3": sec3,
    "sec4": sec4,
    "sec5": sec5,
    "sec6": sec6,
    "sec7": sec7,
    "sec8": sec8,
    "sec9": sec9,
    "sec10": sec10,
}


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    for name in which or SCENES:
        SCENES[name]()
