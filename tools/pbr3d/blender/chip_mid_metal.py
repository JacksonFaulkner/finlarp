"""The CHIP tab, MID METAL: the whole-chip scene (chip_kit.py) with the camera gliding in on the
middle wiring tier, M5-M9, which routes signals block to block. Same template as chip_hero.py
(docs/diagram-pages.md): no cuts, the camera eases from one pose to the next.

Run from the repo root (all scenes, or the named ones after `--`):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_mid_metal.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_mid_metal.py -- zoom_a sec3

Each scene writes blender/chip_mid_metal_<name>.blend and assets/chip_mid_metal_<name>.glb (the
overview writes assets/chip_mid_metal.glb). One beat is 8 s; the TUI samples at t = (beat + local)
* 8 (diagrams_nodes/chip/mid_metal.rs).

Overview (6 beats):
  0 whole    the whole chip, the middle tier lit
  1 zoom     the camera glides in on the middle tier, still lit
  2 short    a signal leaves a via and crosses one block over on a short mid wire
  3 long     the same signal on a longer run: it takes longer to arrive
  4 RC       close on one wire: R from its narrow copper, C to the wire beside it
  5 whole    the longest runs climb to the thick top tier, which is lit

Zoom-ins (3 beats each, key: label as in the old MID METAL page):
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

The wire runs and their levels are mirrored from chip_kit._wires (mid tier), so the overlays sit
exactly on the copper. Dot flight time follows the RC story: delay grows with length squared.
The scale is schematic, not a timing measurement.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, ball, beat, empty, label, mat, show, tube  # noqa: E402
from sand_zooms import finish, start, stream_of  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import route  # noqa: E402

BEATS = 6  # the overview

# ---- the mid tier, as chip_kit builds it ----------------------------------------------------

MID_BAND, _, MID_WH, MID_WD = C.TIERS["mid"]  # band (640, 1020), 5 levels, 40 high, 70 deep
MID_RUNS = [  # wire runs per level, M5 (level 0) at the bottom of the tier
    [(-1400, -300)],
    [(-300, 500)],
    [(500, 1400)],
    [(-900, 100)],
    [(100, 1100)],
]
Z_WIRE = -60.0  # the wires' centre plane
VIA_X = -510.0  # the via between M5 and M8
VIA_X2 = 510.0

# ---- scene pieces ---------------------------------------------------------------------------


def mats(m):
    """chip_kit's materials, plus this node's (prefixed, since mat() caches by name)."""
    C.mats(m)
    m["chip_mid_metal_ru"] = mat("chip_mid_metal_ru", (0.55, 0.72, 0.90), metal=0.9, rough=0.25)
    m["chip_mid_metal_hot"] = mat("chip_mid_metal_hot", (1.0, 0.40, 0.15), emit=(1.0, 0.35, 0.12), strength=3.0)
    m["chip_mid_metal_cap"] = mat(
        "chip_mid_metal_cap", (1.0, 0.85, 0.45), emit=(1.0, 0.80, 0.40), strength=2.5, alpha=0.6
    )
    m["chip_mid_metal_gap"] = mat(
        "chip_mid_metal_gap", (0.85, 0.95, 1.0), emit=(0.80, 0.92, 1.0), strength=1.2, alpha=0.35
    )
    m["chip_mid_metal_plate"] = mat(
        "chip_mid_metal_plate", (1.0, 0.62, 0.30), emit=(1.0, 0.55, 0.25), strength=1.0, alpha=0.4
    )
    m["chip_mid_metal_void"] = mat("chip_mid_metal_void", (0.03, 0.03, 0.05), rough=0.9)
    m["chip_mid_metal_pore"] = mat("chip_mid_metal_pore", (0.95, 0.95, 1.0), emit=(0.9, 0.9, 1.0), strength=1.5)


def level_y(i):
    return C.level_y("mid", i)


def run_box(i, k, g=12.0):
    """The lo and hi corners of run k on mid level i, grown by g so an overlay wraps it."""
    x0, x1 = MID_RUNS[i][k]
    y = level_y(i)
    lo = (x0 - g, y - MID_WH / 2 - g, Z_WIRE - MID_WD / 2 - g)
    hi = (x1 + g, y + MID_WH / 2 + g, Z_WIRE + MID_WD / 2 + g)
    return lo, hi


def glow_level(root, m, name, i, mat_key, intervals):
    """An overlay on every wire run of mid level i, shown for `intervals`."""
    g = empty(name, root)
    for k in range(len(MID_RUNS[i])):
        lo, hi = run_box(i, k)
        C.overlay(g, f"{name}{k}", lo, hi, m[mat_key], intervals)
    return g


def glow_gap(root, m, name, x0, x1, y0, y1, intervals):
    """An overlay on the dielectric gap between two levels (no wire in it), the air-gap glow."""
    return C.overlay(root, name, (x0, y0, Z_WIRE - MID_WD / 2), (x1, y1, Z_WIRE + MID_WD / 2), m["chip_mid_metal_gap"], intervals)


def via_glow(root, m, name, x, y0, y1, r, mat_key, intervals, verts=12):
    """A tube overlay on a via, from y0 to y1, shown for `intervals`."""
    g = empty(name, root)
    tube(name + "_t", (x, y0, Z_WIRE), (x, y1, Z_WIRE), r, m[mat_key], g, verts=verts)
    show(g, intervals)
    return g


def dots_along(root, name, pts, b, u0, u1, life, n=9, m=None):
    """A train of signal dots along the polyline `pts` (wire centre plane), in beat b."""
    s, path = route([(p[0], p[1], Z_WIRE) for p in pts])
    return stream_of(root, name, n, s, path, 46, m, b, u0, u1, life)


def tag(text, x, y, root, intervals, z=0.0):
    return label(text, (x, y, z), root, intervals)


def poses_close(target, dist, yaw=0.05, pitch=0.08, n=3):
    return [(target, dist, yaw, pitch)] * n


# ---- the overview -----------------------------------------------------------------------------

MID_ON = [(F(0, 0), F(5, 0))]  # the node's part: lit for beats 0 to 4
TOP_ON = [(F(5, 0), F(6, 0))]  # beat 5: the longest runs climb to the top tier

WHOLE = ((0.0, 620.0, 0.0), 5800.0, 0.0, 0.10)
POSES = [
    WHOLE,
    ((-300.0, 840.0, 0.0), 3900.0, 0.0, 0.10),  # in on the middle tier
    ((-300.0, 840.0, 0.0), 3900.0, 0.0, 0.10),
    ((-300.0, 840.0, 0.0), 3900.0, 0.0, 0.10),
    ((-600.0, 830.0, 0.0), 1400.0, 0.0, 0.10),  # close on one wire and the via beside it
    WHOLE,
]

# the two signal paths, both leaving the via at x = -510
Y_SHORT = C.level_y("mid", 3)  # a run that reaches from the via to x = 100
Y_LONG = C.level_y("mid", 0)  # the longest mid run, from the via left to x = -1400
X_VIA = -510.0
X_SHORT_END = 100.0
X_LONG_END = -1350.0  # the run itself ends at -1400; stop just short of its end

S_SHORT, P_SHORT = route([(X_VIA, Y_SHORT, -60.0), (X_SHORT_END, Y_SHORT, -60.0)])
S_LONG, P_LONG = route([(X_VIA, Y_LONG, -60.0), (X_LONG_END, Y_LONG, -60.0)])
LEN_SHORT = math.dist((X_VIA, Y_SHORT), (X_SHORT_END, Y_SHORT))
LEN_LONG = math.dist((X_VIA, Y_LONG), (X_LONG_END, Y_LONG))
LIFE_SHORT = 36  # frames for a dot on the short run
LIFE_LONG = round(LIFE_SHORT * (LEN_LONG / LEN_SHORT) ** 2)  # delay ~ length squared


def build(name="mid_metal", poses=POSES):
    m, root = start(name, BEATS, page="chip")
    mats(m)
    C.chip(root, m, mid=MID_ON, top=TOP_ON)

    # beats 2 and 3: the same signal, one short hop, then a longer run
    stream_of(root, "short", 9, S_SHORT, P_SHORT, 46, m["c_dot_sig"], 2, 0.05, 0.55, LIFE_SHORT)
    stream_of(root, "long", 9, S_LONG, P_LONG, 46, m["c_dot_sig"], 3, 0.05, 0.55, LIFE_LONG)

    # tags: 2 to 4 per beat, each shown only for the beat it explains
    label("mid metal M5-M9", (1000.0, C.MID[1] - 60, 0), root, [(F(0, 0), F(1, 0))])
    label("five levels, block to block", (600.0, 1110.0, 0), root, [(F(1, 0), F(2, 0))])
    label("short hop: one block over", (-300.0, 1000.0, 0), root, [(F(2, 0), F(3, 0))])
    label("longer run: more R and C", (-1000.0, 600.0, 0), root, [(F(3, 0), F(4, 0))])
    label("R: narrow copper", (-850.0, 960.0, 0), root, [(F(4, 0), F(5, 0))])
    label("C: wire to wire", (-700.0, 790.0, 0), root, [(F(4, 0), F(5, 0))])
    label("top metal M10-M14: lowest R", (1000.0, C.TOP[1] - 60, 0), root, [(F(5, 0), F(6, 0))])
    label("long runs move up", (-1100.0, 1300.0, 0), root, [(F(5, 0), F(6, 0))])

    C.glide_camera(root, poses)


def overview():
    build()
    finish("mid_metal", page="chip")


# ---- zoom-ins a-e -----------------------------------------------------------------------------

ZOOM_BEATS = 3
Y0 = level_y(0)  # M5, the trench the via lands in
Y3 = level_y(3)  # M8


def zoom_a():
    """a, one dual-damascene pass: the level lit as it forms, copper plated in, then CMP and cap."""
    m, root = start("zoom_a", ZOOM_BEATS, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(0))
    # beat 1: the copper plates the trench and the via in one fill, flowing out from the via
    glow_level(root, m, "plate_a", 0, "chip_mid_metal_plate", beat(1))
    dots_along(root, "plate_dots", [(VIA_X, Y0), (-1350.0, Y0)], 1, 0.05, 0.6, 64, m=m["c_dot_sig"])
    # beat 2: CMP levels the top, then the SiCN cap seals it
    glow_level(root, m, "cap_a", 0, "chip_mid_metal_cap", beat(2))
    tag("trench and via, one mask", -600.0, 1000.0, root, beat(0))
    tag("plated Cu fills both at once", -1000.0, 600.0, root, beat(1))
    tag("CMP, then a SiCN cap", -1000.0, 600.0, root, beat(2))
    C.glide_camera(
        root,
        [
            ((-600.0, 820.0, 0.0), 4200.0, 0.05, 0.08),
            ((-700.0, 800.0, 0.0), 2900.0, 0.05, 0.08),
            ((-700.0, 820.0, 0.0), 3000.0, 0.04, 0.08),
        ],
    )
    finish("mid_metal_zoom_a", page="chip")


def zoom_b():
    """b, RC delay: R on one wire, C to the wire below it through the dielectric, then RC ~ L^2."""
    m, root = start("zoom_b", ZOOM_BEATS, page="chip")
    mats(m)
    C.chip(root, m)
    # beat 0: R, the narrow copper of one wire
    glow_level(root, m, "r_b", 0, "c_lit_mid", beat(0))
    tag("R = rho L / (W H)", -1000.0, 630.0, root, beat(0))
    # beat 1: C, two wires with low-k between them
    glow_level(root, m, "c_b0", 0, "c_lit_mid", beat(1))
    glow_level(root, m, "c_b3", 3, "c_lit_mid", beat(1))
    tag("C: wire to wire through low-k", -600.0, 800.0, root, beat(1))
    # beat 2: a long run, its dots slow, RC grows with L^2
    glow_level(root, m, "l_b0", 0, "c_lit_mid", beat(2))
    dots_along(root, "long_b", [(-1350.0, Y0), (-310.0, Y0)], 2, 0.05, 0.5, 70, m=m["c_dot_sig"])
    tag("long run: delay ~ L^2", -1000.0, 600.0, root, beat(2))
    C.glide_camera(root, poses_close((-800.0, 800.0, 0.0), 2800.0, n=3))
    finish("mid_metal_zoom_b", page="chip")


def zoom_c():
    """c, low-k, air gaps and ruthenium: the dielectric lit, a gap with no dielectric, Ru lines."""
    m, root = start("zoom_c", ZOOM_BEATS, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(0) + beat(1) + beat(2))
    # beat 0: low-k, the soft film between the lines
    tag("k 2.7 CDO: 7-10 GPa", 1000.0, 760.0, root, beat(0))
    # beat 1: the air gap, between two wires with no dielectric
    glow_gap(root, m, "chip_mid_metal_gap", 600.0, 1000.0, level_y(2) + MID_WH / 2, level_y(4) - MID_WH / 2, beat(1))
    tag("air gap: -25% C", 1150.0, 900.0, root, beat(1))
    # beat 2: ruthenium lines, etched, with no barrier
    glow_level(root, m, "ru_c2", 2, "chip_mid_metal_ru", beat(2))
    glow_level(root, m, "ru_c4", 4, "chip_mid_metal_ru", beat(2))
    tag("Ru: etched, no barrier", 1150.0, 1080.0, root, beat(2))
    C.glide_camera(
        root,
        [
            ((800.0, 860.0, 0.0), 2600.0, 0.05, 0.08),
            ((800.0, 900.0, 0.0), 2200.0, 0.05, 0.08),
            ((800.0, 900.0, 0.0), 2200.0, 0.05, 0.08),
        ],
    )
    finish("mid_metal_zoom_c", page="chip")


def zoom_d():
    """d, electromigration: electrons drag atoms along a line, a void forms, caps slow the drift."""
    m, root = start("zoom_d", ZOOM_BEATS, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(1) + beat(2))
    # beat 0: the current pushes copper atoms along the wire
    dots_along(root, "drift_d", [(-880.0, Y3), (80.0, Y3)], 0, 0.05, 0.6, 84, m=m["c_dot_sig"])
    tag("electrons push Cu atoms", -400.0, 990.0, root, beat(0))
    # beat 1: the wire heats, a void opens upstream
    glow_level(root, m, "hot_d", 3, "chip_mid_metal_hot", beat(1))
    C.overlay(root, "void_d", (-620.0, Y3 - 24, Z_WIRE - 30), (-580.0, Y3 + 24, Z_WIRE + 30), m["chip_mid_metal_void"], beat(1) + beat(2))
    tag("void upstream, heat: MTTF falls", -400.0, 1040.0, root, beat(1))
    # beat 2: caps and liners slow the drift
    glow_level(root, m, "cap_d", 3, "chip_mid_metal_cap", beat(2))
    tag("CoWP or Co cap slows drift", -400.0, 1040.0, root, beat(2))
    C.glide_camera(root, poses_close((-400.0, 880.0, 0.0), 2400.0, n=3))
    finish("mid_metal_zoom_d", page="chip")


def zoom_e():
    """e, vias and edge placement, then the whole stack pulled back for RC extraction."""
    m, root = start("zoom_e", ZOOM_BEATS, page="chip")
    mats(m)
    C.chip(root, m)
    # beat 0: a via that lands where it was drawn
    via_glow(root, m, "via_ok", VIA_X, Y0 - 40, Y3 + 40, 30, "c_lit_mid", beat(0))
    tag("via: lands on target, low R", -420.0, 1000.0, root, beat(0))
    # beat 1: a misaligned via, narrow at the bottom
    via_glow(root, m, "via_bad", -460.0, Y0 - 40, Y3 + 40, 14, "chip_mid_metal_hot", beat(1))
    tag("misaligned: narrow, R up", -300.0, 720.0, root, beat(1))
    # beat 2: every wire's R and C extracted for timing signoff
    dots_along(root, "rc_lo", [(-1350.0, Y0), (-310.0, Y0)], 2, 0.05, 0.5, 70, m=m["c_dot_sig"])
    dots_along(root, "rc_hi", [(-880.0, Y3), (80.0, Y3)], 2, 0.05, 0.5, 84, m=m["c_dot_sig"])
    tag("StarRC, Quantus: R and C per wire", -300.0, 1150.0, root, beat(2))
    C.glide_camera(
        root,
        [
            ((-510.0, 800.0, 0.0), 1800.0, 0.05, 0.06),
            ((-480.0, 800.0, 0.0), 1800.0, 0.05, 0.06),
            ((-300.0, 880.0, 0.0), 4000.0, 0.02, 0.10),
        ],
    )
    finish("mid_metal_zoom_e", page="chip")


# ---- sections 1-10 ---------------------------------------------------------------------------


def sec1():
    """1, what happens: the five passes, one level at a time."""
    m, root = start("sec1", 4, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(0))
    tag("M5-M9: five passes", 1000.0, 1100.0, root, beat(0))
    glow_level(root, m, "m5", 0, "chip_mid_metal_plate", beat(1))
    tag("M5: one pass", -1000.0, 600.0, root, beat(1))
    glow_level(root, m, "m6", 1, "chip_mid_metal_plate", beat(2))
    tag("M6: the next pass", 300.0, 640.0, root, beat(2))
    for i in (2, 3, 4):
        glow_level(root, m, f"m{5 + i}", i, "chip_mid_metal_plate", beat(3))
    tag("M7 to M9: three more", 1200.0, 1120.0, root, beat(3))
    C.glide_camera(
        root,
        [
            WHOLE,
            ((-300.0, 800.0, 0.0), 3000.0, 0.0, 0.08),
            ((0.0, 800.0, 0.0), 3000.0, 0.0, 0.08),
            ((0.0, 900.0, 0.0), 3600.0, 0.0, 0.08),
        ],
    )
    finish("mid_metal_sec1", page="chip")


def sec2():
    """2, dual damascene in section: the trench, the via, one fill, the barrier at the via foot."""
    m, root = start("sec2", 4, page="chip")
    mats(m)
    C.chip(root, m)
    glow_level(root, m, "trench_s2", 0, "c_lit_mid", beat(0))
    tag("trench: the lateral wire", -1000.0, 600.0, root, beat(0))
    via_glow(root, m, "via_s2", VIA_X, Y0 - 40, Y3 + 40, 30, "c_lit_mid", beat(1))
    tag("via: the plug down", -420.0, 1000.0, root, beat(1))
    dots_along(root, "fill_s2", [(VIA_X, Y3), (VIA_X, Y0), (-1350.0, Y0)], 2, 0.05, 0.6, 60, m=m["c_dot_sig"])
    tag("one fill for both", -1000.0, 600.0, root, beat(2))
    tag("barrier stops at via foot", -420.0, 800.0, root, beat(3))
    C.glide_camera(root, poses_close((-420.0, 820.0, 0.0), 2400.0, n=4))
    finish("mid_metal_sec2", page="chip")


def sec3():
    """3, RC delay: thin, medium and thick tiers, with the R and C story across them."""
    m, root = start("sec3", 3, page="chip")
    mats(m)
    C.chip(root, m, thin=beat(0), mid=beat(1), top=beat(2))
    tag("thin: high R", 1000.0, 500.0, root, beat(0))
    tag("medium: R and C balanced", 1000.0, 830.0, root, beat(1))
    tag("thick: lowest R", 1000.0, 1230.0, root, beat(2))
    tag("R x C ~ L^2", -1100.0, 1300.0, root, beat(0) + beat(1) + beat(2))
    C.glide_camera(root, [WHOLE, WHOLE, WHOLE])
    finish("mid_metal_sec3", page="chip")


def sec4():
    """4, pitch and patterning per level: the foundry points, one tier at a time."""
    m, root = start("sec4", 3, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(0), thin=beat(1))
    tag("Intel 7 M2/M4: 44-52 nm", -1000.0, 700.0, root, beat(0))
    tag("Intel 4: 45 nm, some EUV", 1000.0, 1000.0, root, beat(0))
    tag("TSMC N3E: 23 nm, EUV single", 1000.0, 500.0, root, beat(1))
    tag("TSMC N5 Mx: ~30% tighter", -1000.0, 450.0, root, beat(1))
    tag("no full per-level tables", 1000.0, 830.0, root, beat(2))
    C.glide_camera(
        root,
        [
            ((0.0, 830.0, 0.0), 3600.0, 0.0, 0.08),
            ((0.0, 500.0, 0.0), 3600.0, 0.0, 0.08),
            WHOLE,
        ],
    )
    finish("mid_metal_sec4", page="chip")


def sec5():
    """5, the dielectric: SiO2, then CDO, then porous CDO, then the air gap."""
    m, root = start("sec5", 4, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(0) + beat(1) + beat(2) + beat(3))
    tag("SiO2 k 4.0: 72 GPa", 1000.0, 1050.0, root, beat(0))
    tag("k 2.7 CDO: 7-10 GPa", 1000.0, 1050.0, root, beat(1))
    tag("58% porous CDO: 3 GPa", 1000.0, 1050.0, root, beat(2))
    # pores in the dielectric, shown only for the porous film
    grp = empty("pores_s5", root)
    for k, (x, y) in enumerate(((-300, 700), (80, 960), (420, 700), (900, 980), (-980, 720), (-600, 960), (640, 720))):
        ball(f"pore_s5_{k}", (x, y, -20.0), 20, m["chip_mid_metal_pore"], grp, 8)
    show(grp, beat(2))
    glow_gap(root, m, "chip_mid_metal_gap", 600.0, 1000.0, level_y(2) + MID_WH / 2, level_y(4) - MID_WH / 2, beat(3))
    tag("air gap: -25% C", 1150.0, 900.0, root, beat(3))
    C.glide_camera(root, poses_close((800.0, 860.0, 0.0), 2600.0, n=4))
    finish("mid_metal_sec5", page="chip")


def sec6():
    """6, electromigration: electrons push atoms, heat makes it worse, caps slow it."""
    m, root = start("sec6", 3, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(0) + beat(1) + beat(2))
    dots_along(root, "drift_s6", [(-880.0, Y3), (80.0, Y3)], 0, 0.05, 0.6, 84, m=m["c_dot_sig"])
    tag("electrons push Cu atoms", -400.0, 1040.0, root, beat(0))
    glow_level(root, m, "hot_s6", 3, "chip_mid_metal_hot", beat(1))
    tag("MTTF = A J^-n exp(Ea/kT)", -400.0, 1040.0, root, beat(1))
    glow_level(root, m, "cap_s6", 3, "chip_mid_metal_cap", beat(2))
    tag("caps and liners slow it", -400.0, 1040.0, root, beat(2))
    C.glide_camera(root, poses_close((-200.0, 800.0, 0.0), 3600.0, n=3))
    finish("mid_metal_sec6", page="chip")


def sec7():
    """7, vias and edge placement: a landed via, a misaligned one, and the RC extraction."""
    m, root = start("sec7", 3, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(0) + beat(1) + beat(2))
    via_glow(root, m, "via_ok_s7", VIA_X, Y0 - 40, Y3 + 40, 30, "c_lit_mid", beat(0))
    via_glow(root, m, "via_ok2_s7", VIA_X2, Y0 - 40, Y3 + 40, 30, "c_lit_mid", beat(0))
    tag("via: lands on target", -380.0, 1040.0, root, beat(0))
    via_glow(root, m, "via_bad_s7", -460.0, Y0 - 40, Y3 + 40, 14, "chip_mid_metal_hot", beat(1))
    tag("misaligned: narrow bottom", -300.0, 720.0, root, beat(1))
    dots_along(root, "rc_lo_s7", [(-1350.0, Y0), (-310.0, Y0)], 2, 0.05, 0.5, 70, m=m["c_dot_sig"])
    tag("StarRC, Quantus: R and C", -300.0, 1150.0, root, beat(2))
    C.glide_camera(root, poses_close((0.0, 830.0, 0.0), 2600.0, n=3))
    finish("mid_metal_sec7", page="chip")


def sec8():
    """8, who makes it: the tool makers on the middle tier, the fabs and designers, China."""
    m, root = start("sec8", 3, page="chip")
    mats(m)
    C.chip(root, m, mid=beat(0) + beat(1) + beat(2))
    tag("Applied: Endura CuBS, Black Diamond", -1000.0, 1080.0, root, beat(0))
    tag("Lam: SABRE copper plating", 1000.0, 700.0, root, beat(0))
    tag("fabs: TSMC, Intel, Samsung", -700.0, -150.0, root, beat(1))
    tag("designers: Arm, NVIDIA, AMD", 1000.0, 1300.0, root, beat(1))
    tag("China: 30% of Applied sales", 1000.0, 830.0, root, beat(2))
    tag("FY2025: $8,529M of $28,368M", 1000.0, 760.0, root, beat(2))
    C.glide_camera(root, [WHOLE, WHOLE, WHOLE])
    finish("mid_metal_sec8", page="chip")


def sec9():
    """9, chokepoints and risks: the copper wall, the porous film and EM, the tool and China shifts."""
    m, root = start("sec9", 3, page="chip")
    mats(m)
    C.chip(root, m, thin=beat(0), mid=beat(1), top=beat(2))
    tag("Cu wall below ~20 nm pitch", 1000.0, 500.0, root, beat(0))
    glow_level(root, m, "hot_s9", 3, "chip_mid_metal_hot", beat(1))
    tag("porous ULK damages easily", 1000.0, 830.0, root, beat(1))
    tag("EM: more current, faster", -1000.0, 1000.0, root, beat(1))
    tag("tools shift to Ru", 1000.0, 1230.0, root, beat(2))
    tag("China: 30% of Applied", -1000.0, 1300.0, root, beat(2))
    C.glide_camera(root, [WHOLE, WHOLE, WHOLE])
    finish("mid_metal_sec9", page="chip")


def sec10():
    """10, sources: the whole chip, slowly pulled back; the source list is the beat text."""
    m, root = start("sec10", 4, page="chip")
    mats(m)
    C.chip(root, m)
    C.glide_camera(
        root,
        [
            ((0.0, 620.0, 0.0), 4200.0, 0.0, 0.10),
            ((0.0, 620.0, 0.0), 4600.0, 0.05, 0.10),
            ((0.0, 620.0, 0.0), 5000.0, -0.05, 0.10),
            WHOLE,
        ],
    )
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
