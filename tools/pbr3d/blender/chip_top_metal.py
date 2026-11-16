"""CHIP pictures for TOP METAL: the overview, five zoom-ins (a-e) and ten sections.

Run from the repo root (names after -- pick scenes, none means all of them):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_top_metal.py [-- zoom_a sec3 ...]

Writes blender/chip_top_metal*.blend and assets/chip_top_metal*.glb. One beat is 8 s.

Overview (6 beats): the whole chip first and last, the detailed cut-away (chip_top_metal_detail.py)
in between, beads riding the real copper:
  0 whole    the whole chip, the top tier (M10-M14) lit, the package bumps above it
  1 bumps    VDD from the substrate down a C4 bump and the Al pad onto an M14 VDD stripe
  2 grid     VDD and VSS stripes lit; VDD spreads along the M13 rail and down its vias
  3 clock    the clock spine on an M11 wire, taps down to M10, beads out from the middle
  4 thick    the same length of M11 wire and M13 rail: beads cross the thick rail far faster
  5 whole    back out: VSS climbs back up to its bump, the whole chip again

Zoom-ins (3 beats each), all detailed cut-aways:
  a the top loop: M14 etched with barrier + seed, plated and polished, then pad, passivation, bump
  b jobs of the thick levels (sec3)      c power delivery and IR drop (sec4)
  d bumps to hybrid bonds (sec5)         e backside power, BSPDN (sec6)
  b-e are those sections seen from the other side.

Sections, one per `# ` heading of CHIP_TOP_METAL.txt (3 beats; 10 has 4). They do not replay the
whole chip: each builds a cut-away of the parts themselves (chip_top_metal_detail.py), copper in
barrier and liner, vias, caps and low-k, the pad, passivation, UBM and bump:
  sec1 what happens: M14 plate and CMP, pad and passivation, the bump drops on
  sec2 whole stack: one column from transistors and contacts through M1-M14 to the bump
  sec3 jobs: VDD/VSS stripes and the M13 rail, the clock spine, RDL, underfill and substrate
  sec4 power delivery: the path down the via stack, IR drop along the rail, EM at a via
  sec5 connection density: C4 balls, Cu-pillar microbumps, hybrid-bonded pads at one scale
  sec6 backside power: front-side power next to a BSPDN column with nano-TSVs and BM levels
  sec7 by the numbers: the three joints, a 16-level Intel 4 stack, revenue bars
  sec8 who makes it: PowerVia vs Super Power Rail contacts, GPU current, an IR-drop map
  sec9 how it fails: droop and an EM void, microbump bridging, C4 fatigue and underfill
  sec10 sources: the top of the stack from four sides
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, cut  # noqa: E402
from chip_mid_metal_detail import EPS  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, P, ball, box, empty, glide_camera, key, label, mat, overlay, route, show, stream_of, tube  # noqa: E402

BEATS = 6

WHOLE = C.WHOLE
CHIP_ON = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]  # the schematic whole chip: first and last beat
DETAIL_ON = [(F(1, 0), F(5, 0))]  # the cut-away of the top of the stack in between
Y_TOP0 = C.level_y("top", 0)  # the whole chip's full-width rail nearest the pads
VSS_X = C.VSS_X
DOT_Z = 30.0  # beads on the whole chip run just in front of its cut plane


def span(b0, b1=None):
    """Shown for whole beats b0 through b1 (inclusive)."""
    b1 = b0 if b1 is None else b1
    return [(F(b0, 0), F(b1 + 1, 0))]


def _mats(m):
    m["clk"] = mat("chip_top_metal_clk", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=3.0)


# ---- the overview -----------------------------------------------------------------------------
#
# Beats 0 and 5 are the whole chip (chip_kit.py), the tab's shared story. Beats 1-4 swap it for the
# detailed cut-away of the top of the stack (chip_top_metal_detail.py) and the camera works on that.


def build(name="top_metal", poses=None):
    import chip_mid_metal_detail as D
    import chip_top_metal_detail as T
    m, root = start(name, BEATS, page="chip")
    C.mats(m)
    _mats(m)
    D.mats(m)
    T.extra_mats(m)
    chip = empty("chip_whole", root)
    C.chip(chip, m, top=CHIP_ON, bumps=CHIP_ON)
    show(chip, CHIP_ON)
    det = empty("detail", root)
    show(det, DETAIL_ON)
    lv = T.top_block(det, m)
    cp = T.top_cap(det, m, lv)
    m11, m12, m13, m14 = lv["M11"], lv["M12"], lv["M13"], lv["M14"]
    z = 14.0
    # beat 1: VDD from the package substrate, through the bump and pad, onto the M14 stripe and rail
    path = [(0.0, cp["sub_y"] - 10.0, z), (0.0, cp["bump_y"], z), (0.0, cp["pad_top"] - 30.0, z),
            (0.0, m14.yc, z), (0.0, m13.yc, z)]
    D.run(root, "vdd_in", path, 12, 24.0, m["d_vdd"], 1, 0.02, 0.6, 80)
    # beat 2: the grid: the stripes lit, VDD spreading along the M13 rail and down its vias
    g2 = group("grid", root, span(2))
    o = m14.w / 2 + m14.bt + m14.lt
    for k, x in enumerate(m14.xs):
        box(f"grid_s{k}", (x - o, m14.y0 - o * 0.1, -4.0), (x + o, m14.y1, 6.0), m["d_vdd_rail" if k in T.VDD_I else "d_vss_rail"], g2)
    box("grid_r", (T.X0 + 4, m13.y0, -4.0), (T.X1 - 4, m13.y1, 6.0), m["d_vdd_rail"], g2)
    for s, x in (("l", -720.0), ("r", 720.0)):
        D.run(root, f"grid_{s}", [(0.0, m14.yc, z), (0.0, m13.yc, z), (x, m13.yc, z), (x, m12.yc, z)], 10, 24.0, m["d_vdd"], 2, 0.02, 0.6, 80)
    # beat 3: the clock spine on M11, taps down to M10, beads both ways from the middle
    g3 = group("clock", root, span(3))
    a, b = m11.segs[0]
    box("clk_spine", (a, m11.y0 - 3, -4.0), (b, m11.y1 + 3, 6.0), m["d_clk_lit"], g3)
    taps = [x for k, x in enumerate(lv["M10"].xs) if a + 40 < x < b - 40 and k % 3 == 0]
    for k, x in enumerate(taps):
        box(f"clk_tap{k}", (x - 10.0, lv["M10"].y1 - 2, -4.0), (x + 10.0, m11.y0 + 2, 6.0), m["d_clk"], g3)
    for s, x in (("l", a + 30.0), ("r", b - 30.0)):
        D.run(root, f"clk_{s}", [(0.0, m11.yc, z), (x, m11.yc, z)], 9, 16.0, m["d_clk"], 3, 0.03, 0.6, 50)
    # beat 4: the same length of M11 wire and M13 rail: beads cross the thick rail far faster
    g4 = group("thick", root, span(4))
    box("thin_glow", (-900.0, m11.y0 - 3, -4.0), (-100.0, m11.y1 + 3, 6.0), m["d_hot"], g4)
    box("thick_glow", (-900.0, m13.y0 - 3, -4.0), (-100.0, m13.y1 + 3, 6.0), m["d_ok"], g4)
    D.run(root, "slow", [(-900.0, m11.yc, z), (-100.0, m11.yc, z)], 6, 14.0, m["d_vdd"], 4, 0.02, 0.5, 120)
    D.run(root, "fast", [(-900.0, m13.yc, z), (-100.0, m13.yc, z)], 6, 30.0, m["d_vdd"], 4, 0.02, 0.5, 30)
    # beat 5: back on the whole chip, VSS climbs to its bump
    s5, p5 = route([(VSS_X, Y_TOP0, DOT_Z), (VSS_X, C.BUMP_Y, DOT_Z)])
    stream_of(root, "vss_out", 9, s5, p5, 46, m["c_dot_gnd"], 5, 0.10, 0.60, 90)

    label("top metal M10-M14", (1520.0, C.level_y("top", 1), 0.0), root, span(0))
    label("package bumps", (VSS_X, C.BUMP_Y + 120, 0.0), root, span(0))
    label("VDD from the package", (0.0, cp["sub_y"] + 120.0, 2.0), root, span(1))
    label("C4 bump", (180.0, cp["bump_y"], 2.0), root, span(1))
    label("Al bond pad", (180.0, cp["pad_top"] - 30.0, 2.0), root, span(1))
    label("onto the M14 VDD stripe", (m14.xs[2] + 60, m14.yc, z), root, span(1))
    label("VDD stripe (M14)", (m14.xs[2], m14.y1 - 40.0, 6.0), root, span(2))
    label("VSS stripe", (m14.xs[3], m14.y1 - 40.0, 6.0), root, span(2))
    label("M13 rail spreads it", (-450.0, m13.yc, 6.0), root, span(2))
    label("clock spine on M11", (-500.0, m11.yc, 6.0), root, span(3))
    label("taps to the clock tree", (taps[1] if len(taps) > 1 else a, (lv["M10"].y1 + m11.y0) / 2, 6.0), root, span(3))
    label("M11: slow, more R", (-500.0, m11.yc, 6.0), root, span(4))
    label("M13: fast, low R", (-500.0, m13.yc, 6.0), root, span(4))
    label("R = rho L / (W T)", (-100.0, (m11.y1 + m13.y0) / 2 + 60, 2.0), root, span(4))
    label("VSS back to its bump", (VSS_X, C.BUMP_Y + 120, 0.0), root, span(5))
    cam(root, [
        WHOLE,
        frame(-700.0, m14.y0 - 60, 700.0, cp["sub_top"] + 20, yaw=0.25, pitch=0.16),
        frame(-1010.0, m12.y0 - 40, 1010.0, m14.y1 + 60, yaw=0.25, pitch=0.18),
        frame(-750.0, -150.0, 650.0, m12.y1, yaw=0.25, pitch=0.12),
        frame(-1000.0, m11.y0 - 100, 0.0, m13.y1 + 60, yaw=0.20, pitch=0.12),
        WHOLE,
    ])


# ---- zoom-ins ---------------------------------------------------------------------------------
#
# a builds the M14 damascene loop step by step. b-e are the matching sections (3, 4, 5, 6) seen from
# the other side: the same detailed parts, written out as zoom GLBs.


def zoom_a():
    """a: the top loop. The etched M14 trench with barrier and seed, copper plated and polished,
    then the pad, passivation and bump."""
    import chip_mid_metal_detail as D
    import chip_top_metal_detail as T
    m, root = _sbegin("zoom_a", 3)
    lv = T.top_block(root, m, specs=T.TOP_SPECS[:4])
    k = T.m14_by_hand(root, m, lv, etched=span(0, 2), shell=[(F(0, 0.35), F(1, 0))], copper=[(F(1, 0), F(3, 0))],
                      cap=[(F(1, 0.8), F(3, 0))])
    m13, m14 = lv["M13"], lv["M14"]
    pl = group("plasma", root, [(F(0, 0.05), F(0, 0.32))])
    for i, x in enumerate(k["xs"]):
        box(f"pl{i}", (x - k["hw"] + 4, k["yl"] + 4, T.Z0 + 10), (x + k["hw"] - 4, k["yt"] + 40, -3.0), m["d_plasma"], pl)
    over = group("over", root, [(F(1, 0.0), F(1, 0.72))])
    grow("over_p", over, (0.0, k["yt"] + 0.5, 0.0),
         lambda p: box("over_cu", (T.X0, 0.0, T.Z0), (T.X1, 70.0, 2.0), m["d_cu"], p), [(F(1, 0.02), (1, 1, 0.05)), (F(1, 0.35), (1, 1, 1))])
    pad = group("cmp", root, [(F(1, 0.4), F(1, 0.75))])
    pm = empty("cmp_move", pad)
    box("cmp_pad", (-500.0, k["yt"] + 72.0, T.Z0 - 40), (500.0, k["yt"] + 140.0, 40.0), m["d_mask"], pm)
    key(pm, F(1, 0.4), "location", P(-900.0, 0, 0), linear=True)
    key(pm, F(1, 0.72), "location", P(900.0, 0, 0), linear=True)
    cp = T.top_cap(root, m, lv, intervals=span(2), bump_iv=[(F(2, 0.3), F(3, 0))], sub_iv=[])
    gb = bpy.data.objects["cap_bump"]
    key(gb, F(2, 0.3), "location", P(0, 500.0, 0), linear=True)
    key(gb, F(2, 0.55), "location", P(0, 0, 0), linear=True)
    label("trench and via, etched", (k["xs"][3], k["yt"] - 40.0, 2.0), root, [(F(0, 0), F(0, 0.35))])
    label("TaN barrier + Cu seed", (k["xs"][1] - m14.w / 2 - m14.lt - m14.bt / 2, k["yl"] + 60.0, 2.0), root, [(F(0, 0.35), F(1, 0))])
    label("via down to M13", (0.0, (m13.cap_top + k["yl"]) / 2, 2.0), root, span(0))
    label("Cu plated past the top", (-600.0, k["yt"] + 50.0, 3.0), root, [(F(1, 0.05), F(1, 0.4))])
    label("CMP polishes it flat", (300.0, k["yt"] + 110.0, 41.0), root, [(F(1, 0.4), F(1, 0.75))])
    label("SiCN cap on M14", (600.0, m14.cap_top, 2.0), root, [(F(1, 0.8), F(2, 0))])
    label("Al bond pad", (150.0, cp["pad_top"] - 30.0, 2.0), root, span(2))
    label("SiN + polyimide passivation", (-450.0, cp["pi_top"] - 30.0, 2.0), root, span(2))
    label("solder bump on UBM", (0.0, cp["bump_y"], 2.0), root, [(F(2, 0.55), F(3, 0))])
    _send("zoom_a", root, [
        frame(-800.0, m13.y0 - 40, 800.0, k["yt"] + 120, yaw=-0.28, pitch=0.22),
        frame(-800.0, m13.y0 - 40, 800.0, k["yt"] + 160, yaw=-0.28, pitch=0.22),
        frame(-650.0, m14.y1 - 80, 650.0, cp["bump_top"] + 160, yaw=-0.25, pitch=0.18),
    ])


_AS = {}  # set by _as(): the section being written out as a zoom, under another name


def _as(fn, name):
    _AS.update(name=name)
    try:
        fn()
    finally:
        _AS.clear()


def zoom_b():
    """b: jobs of the thick levels: the power grid, the clock spine and long wires, RDL and underfill (sec3)."""
    _as(sec3, "zoom_b")


def zoom_c():
    """c: power delivery: the path down the via stack, IR drop along the rail, the EM limit (sec4)."""
    _as(sec4, "zoom_c")


def zoom_d():
    """d: bumps to hybrid bonds: C4, Cu-pillar microbumps, hybrid-bonded pads (sec5)."""
    _as(sec5, "zoom_d")


def zoom_e():
    """e: backside power: front-side power beside a BSPDN column (sec6)."""
    _as(sec6, "zoom_e")


# ---- sections: a cut-away of the top of the stack per `# ` heading of CHIP_TOP_METAL.txt -----
#
# The sections build the real parts (chip_top_metal_detail.py on chip_mid_metal_detail.py):
# M10-M14 copper in barrier and liner with their vias, SiCN caps and low-k, the Al pad,
# passivation, UBM and C4 bump, the joints from C4 to hybrid bonds, backside power. Schematic
# scale: the bump is drawn far smaller than life next to the wiring.

import chip_mid_metal_detail as D  # noqa: E402
import chip_top_metal_detail as T  # noqa: E402
from chip_mid_metal_detail import cam, dots, frame, group, grow, slab  # noqa: E402

DZ = 14.0  # dots run just in front of the cut face


def _sbegin(name, beats):
    m, root = start(f"top_metal_{name}", beats, page="chip")
    C.mats(m)
    _mats(m)
    D.mats(m)
    T.extra_mats(m)
    return m, root


def _send(name, root, poses):
    """The section camera and export; a section written out as a zoom (_as) is seen from the other
    side (yaw mirrored) and saved under the zoom's name."""
    if _AS:
        poses = [(t, d, -yaw, pitch) for t, d, yaw, pitch in poses]
        name = _AS["name"]
    cam(root, poses)
    finish(f"top_metal_{name}", page="chip")


def _stripes(root, m, lv, intervals, name="stripes"):
    """VDD (orange) and VSS (blue) glows on the M14 stripes, and the M13 VDD rail under them."""
    g = group(name, root, intervals)
    m13, m14 = lv["M13"], lv["M14"]
    o = m14.w / 2 + m14.bt + m14.lt
    for k, x in enumerate(m14.xs):
        box(f"{name}_s{k}", (x - o, m14.y0 - m14.bt - m14.lt, -4.0), (x + o, m14.y1, 6.0),
            m["d_vdd_rail" if k in T.VDD_I else "d_vss_rail"], g)
    box(f"{name}_r", (T.X0 + 4, m13.y0, -4.0), (T.X1 - 4, m13.y1, 6.0), m["d_vdd_rail"], g)
    return g


def _stack_path(lv, cp, x=0.0, z=DZ):
    """The VDD path at x: substrate, bump, pad, then down every level to below M10."""
    pts = []
    if "sub_y" in cp:
        pts.append((cp["bump_x"], cp["sub_y"] - 10.0, z))
    pts.append((cp["bump_x"], cp["bump_y"], z))
    if cp["bump_x"] != x:
        pts.append((cp["bump_x"], cp["pi_top"] + 20.0, z))
        pts.append((x, cp["pi_top"] + 20.0, z))
    pts += [(x, cp["pad_top"] - 30.0, z)] + [(x, lv[k].yc, z) for k in ("M14", "M13", "M12", "M11", "M10")] + [(x, -70.0, z)]
    return pts


def sec1():
    """1, what happens: the thick M14 loop (plate, polish), then pad and passivation, then the bump."""
    m, root = _sbegin("sec1", 3)
    lv = T.top_block(root, m)
    m13, m14 = lv["M13"], lv["M14"]
    over = group("over", root, [(F(0, 0.1), F(0, 0.62))])
    grow("over_p", over, (0.0, m14.y1 + 0.5, 0.0),
         lambda p: box("over_cu", (T.X0, 0.0, T.Z0), (T.X1, 70.0, 2.0), m["d_cu"], p), [(F(0, 0.12), (1, 1, 0.05)), (F(0, 0.42), (1, 1, 1))])
    pad = group("cmp", root, [(F(0, 0.42), F(0, 0.72))])
    pm = empty("cmp_move", pad)
    box("cmp_pad", (-500.0, m14.y1 + 72.0, T.Z0 - 40), (500.0, m14.y1 + 140.0, 40.0), m["d_mask"], pm)
    key(pm, F(0, 0.42), "location", P(-900.0, 0, 0), linear=True)
    key(pm, F(0, 0.72), "location", P(900.0, 0, 0), linear=True)
    cp = T.top_cap(root, m, lv, intervals=[(F(1, 0.12), F(3, 0))], bump_iv=[(F(2, 0.05), F(3, 0))], sub_iv=[])
    # the bump drops on at the start of beat 2 (the ball and UBM group slides down into place)
    gb = bpy.data.objects["cap_bump"]
    key(gb, F(2, 0.05), "location", P(0, 500.0, 0), linear=True)
    key(gb, F(2, 0.35), "location", P(0, 0, 0), linear=True)
    xs = m14.xs
    label("M14: the thickest copper", (xs[3], m14.yc, 2.0), root, span(0))
    label("TaN barrier + Cu seed", (xs[1] - m14.w / 2 - m14.lt - m14.bt / 2, m14.y0 + 40.0, 2.0), root, [(F(0, 0), F(0, 0.4))])
    label("plated Cu overburden", (-600.0, m14.y1 + 50.0, 3.0), root, [(F(0, 0.15), F(0, 0.45))])
    label("CMP polishes it flat", (300.0, m14.y1 + 110.0, 41.0), root, [(F(0, 0.45), F(0, 0.75))])
    label("SiCN cap on M14", (600.0, m14.cap_top, 2.0), root, [(F(0, 0.75), F(1, 0))])
    label("Al bond pad", (150.0, cp["pad_top"] - 30.0, 2.0), root, span(1))
    label("SiN passivation", (-500.0, cp["sin_top"] - 20.0, 2.0), root, span(1))
    label("polyimide, opened over pad", (450.0, cp["pi_top"] - 30.0, 2.0), root, span(1))
    label("vias down to M14", (70.0, (m14.y1 + cp["y0"] + 60) / 2, 2.0), root, span(1))
    label("UBM: Ti, Cu, Ni", (150.0, cp["ubm_top"] - 20.0, 3.0), root, [(F(2, 0.35), F(3, 0))])
    label("C4 solder bump", (0.0, cp["bump_y"], 2.0), root, [(F(2, 0.35), F(3, 0))])
    _send("sec1", root, [
        frame(-800.0, m13.y0 - 40, 800.0, m14.y1 + 160, yaw=0.30, pitch=0.22),
        frame(-650.0, m14.y0 - 40, 650.0, cp["pi_top"] + 80, yaw=0.28, pitch=0.20),
        frame(-650.0, m14.y1 - 80, 650.0, cp["bump_top"] + 60, yaw=0.28, pitch=0.18),
    ])


def _tower_cap(root, m, lv, x0=-160.0, x1=160.0, z0=-200.0):
    """A small pad, passivation, UBM and bump on the narrow tower."""
    g = empty("tcap", root)
    y = lv["_top"]
    box("t_pad", (-120.0, y, z0 + 4), (120.0, y + 40.0, EPS), m["d_al"], g)
    T.D_holes("t_sin", g, m["d_sin"], x0, x1, [(-120.0, 120.0)], y, y + 40.0, z0)
    T.D_holes("t_pi", g, m["d_pi_o"], x0, x1, [(-90.0, 90.0)], y + 40.0, y + 100.0, z0)
    box("t_ubm", (-90.0, y + 40.0, z0 + 6), (90.0, y + 110.0, EPS * 2), m["d_ubm"], g)
    b = ball("t_ball", (0.0, y + 110.0 + 120.0, -60.0), 140.0, m["d_solder"], g, 28)
    b.scale = (1.0, 1.0, 0.85)
    cut(b, EPS * 3)
    return y + 110.0 + 120.0, y + 110.0 + 240.0


def sec2():
    """2, the whole stack: transistors and contacts with M1-M4, then M5-M9, then M10-M14 and the bump."""
    m, root = _sbegin("sec2", 3)
    lv = T.full_tower(root, m)
    by, btop = _tower_cap(root, m, lv)
    m1, m4, m5, m9, m10, m13, m14 = (lv[k] for k in ("M1", "M4", "M5", "M9", "M10", "M13", "M14"))
    label("transistors in silicon", (lv["xs"][2], -40.0, 2.0), root, span(0))
    label("tungsten contacts", (m1.xs[3] if m1.xs else -100.0, 24.0, 2.0), root, span(0))
    label("M1-M4: thin Cu", (60.0, m4.yc, 2.0), root, span(0))
    label("M5-M9: medium Cu", (60.0, lv["M7"].yc, 2.0), root, span(1))
    label("vias join the levels", (lv["M6"].vias_at[0] if lv["M6"].vias_at else 0.0, (lv["M5"].cap_top + lv["M6"].y0) / 2, 2.0), root, span(1))
    label("M10-M12: wider again", (60.0, lv["M11"].yc, 2.0), root, span(2))
    label("M13-M14: power grid", (60.0, m14.yc, 2.0), root, span(2))
    label("pad and C4 bump", (0.0, by, 2.0), root, span(2))
    _send("sec2", root, [
        frame(-175.0, -95.0, 175.0, m4.cap_top + 30.0, yaw=0.30, pitch=0.18),
        frame(-175.0, m4.y0 - 10.0, 175.0, m9.cap_top + 30.0, yaw=0.30, pitch=0.18),
        frame(-300.0, m10.y0 - 20.0, 300.0, btop + 20.0, yaw=0.30, pitch=0.16),
    ])


def sec3():
    """3, jobs of the thick levels: the power grid, the clock spine, the RDL and underfill."""
    m, root = _sbegin("sec3", 3)
    lv = T.top_block(root, m)
    m10, m11, m12, m13, m14 = (lv[k] for k in ("M10", "M11", "M12", "M13", "M14"))
    cp = T.top_cap(root, m, lv, pad_x=0.0, bump_x=600.0, rdl=True, sub_iv=span(2))
    T.underfill(root, m, cp, span(2))
    # beat 0: VDD in through the bump, along the RDL, down to the rail and out along it
    _stripes(root, m, lv, span(0))
    path = _stack_path(lv, cp)[:-4]  # stop on the M13 rail
    dots(root, "vdd_in", path, 10, 26.0, m["d_vdd"], 0, 0.02, 0.45, 90)
    for s, x in (("l", -950.0), ("r", 950.0)):
        dots(root, f"vdd_{s}", [(0.0, m13.yc, DZ), (x, m13.yc, DZ)], 8, 26.0, m["d_vdd"], 0, 0.35, 0.8, 50)
    # beat 1: the clock spine along the M11 wire, with taps down to M10
    clk = group("clk", root, span(1))
    a, b = m11.segs[0]
    box("clk_spine", (a, m11.y0 - 3, -4.0), (b, m11.y1 + 3, 6.0), m["d_clk_lit"], clk)
    for k, x in enumerate(m10.xs):
        if a + 40 < x < b - 40 and k % 3 == 0:
            box(f"clk_tap{k}", (x - 10.0, m10.y1 - 2, -4.0), (x + 10.0, m11.y0 + 2, 6.0), m["d_clk"], clk)
    for s, x in (("l", a + 30.0), ("r", b - 30.0)):
        dots(root, f"clk_{s}", [(0.0, m11.yc, DZ), (x, m11.yc, DZ)], 8, 18.0, m["d_clk"], 1, 0.03, 0.6, 50)
    dots(root, "bus", [(-950.0, m12.yc, DZ), (950.0, m12.yc, DZ)], 6, 18.0, m["d_sig"], 1, 0.1, 0.6, 70)
    label("VDD stripe (M14)", (m14.xs[2], m14.y1 - 40.0, 6.0), root, span(0))
    label("VSS stripe", (m14.xs[3], m14.y1 - 40.0, 6.0), root, span(0))
    label("M13 rail feeds the vias", (-600.0, m13.yc, 6.0), root, span(0))
    label("power in at the bump", (600.0, cp["bump_y"], 3.0), root, span(0))
    label("clock spine on M11", (-500.0, m11.yc, 6.0), root, span(1))
    label("taps down to the clock tree", (m10.xs[3], (m10.y1 + m11.y0) / 2, 6.0), root, span(1))
    label("long bus wires", (600.0, m12.yc + 30, 6.0), root, span(1))
    label("RDL moves the bump off the pad", (300.0, cp["pi_top"] + 20.0, 2.0), root, span(2))
    label("underfill epoxy", (-500.0, cp["bump_y"], 2.0), root, span(2))
    label("package substrate", (-300.0, cp["sub_y"] + 160.0, 2.0), root, span(2))
    label("Al pad", (-150.0, cp["pad_top"] - 30.0, 2.0), root, span(2))
    _send("sec3", root, [
        frame(-1010.0, m12.y0 - 40, 1010.0, cp["bump_top"] + 40, yaw=0.25, pitch=0.18),
        frame(-1010.0, -200.0, 1010.0, m11.y1 + 60, yaw=0.25, pitch=0.12),
        frame(-500.0, m14.y0 - 40, 1000.0, cp["sub_top"] + 20, yaw=0.25, pitch=0.16),
    ])


def sec4():
    """4, power delivery: the path down the stack, the IR drop along the rail, the EM limit at a via."""
    m, root = _sbegin("sec4", 3)
    lv = T.top_block(root, m)
    m10, m12, m13, m14 = lv["M10"], lv["M12"], lv["M13"], lv["M14"]
    cp = T.top_cap(root, m, lv)
    dots(root, "path", _stack_path(lv, cp), 14, 26.0, m["d_vdd"], 0, 0.02, 0.6, 110)
    # beat 1: the rail coloured by its voltage, high at the via under the bump, low at the ends
    ir = group("ir", root, span(1))
    for s, (a, b) in (("r", (0.0, 1000.0)), ("l", (0.0, -1000.0))):
        D.heat_strip(ir, m, f"ir_{s}", min(a, b), max(a, b), m13.y0 - 2, m13.y1 + 2, -4.0, 6.0, n=6, reverse=(s == "l"))
    for s, x in (("l", -950.0), ("r", 950.0)):
        dots(root, f"ir_{s}", [(0.0, m13.yc, DZ + 6), (x, m13.yc, DZ + 6)], 8, 22.0, m["d_vdd"], 1, 0.02, 0.6, 70)
    # beat 2: the via stack under the bump carries the most current per area
    hot = group("emhot", root, span(2))
    for k, (ya, yb, w) in enumerate(((m13.y1, m14.y0, lv["M14"].via_w), (m12.y1, m13.y0, 0.62 * 70.0))):
        box(f"emv{k}", (-w / 2 - 6, ya - 4, -w - 8), (w / 2 + 6, yb + 4, 8.0), m["d_hot"], hot)
    dots(root, "em", [(0.0, m14.yc, DZ), (0.0, m12.yc, DZ)], 16, 18.0, m["d_vdd"], 2, 0.02, 0.8, 40)
    vg = group("emvoid", root, span(2))
    grow("void_p", vg, (0.0, m13.y1, 0.0), lambda p: box("void_b", (-50.0, 0.0, -60.0), (50.0, 22.0, 9.0), m["d_void"], p),
         [(F(2, 0.2), 0.05), (F(2, 0.8), 1.0)])
    label("from the board VRM and package", (0.0, cp["sub_y"] + 120.0, 2.0), root, span(0))
    label("bump and pad", (180.0, cp["bump_y"] - 120.0, 2.0), root, span(0))
    label("down the via stack", (0.0, m12.yc, DZ), root, span(0))
    label("on to M1 and the cells", (0.0, -50.0, DZ), root, span(0))
    label("full V under the bump", (60.0, m13.yc, 6.0), root, span(1))
    label("V = I x R: lower at the ends", (880.0, m13.yc, 6.0), root, span(1))
    label("current crowds into the vias", (0.0, (m13.y1 + m14.y0) / 2, 8.0), root, span(2))
    label("EM void at the via foot", (40.0, m13.y1 + 10, 9.0), root, span(2))
    _send("sec4", root, [
        frame(-700.0, -90.0, 700.0, cp["sub_top"] + 20.0, yaw=0.25, pitch=0.16),
        frame(-1010.0, m12.y0 - 40, 1010.0, m14.y1 + 40, yaw=0.20, pitch=0.18),
        frame(-450.0, m12.y0 - 30, 450.0, m14.y1 + 30, yaw=0.25, pitch=0.16),
    ])


C4X, UBX, HBX = -3600.0, 0.0, 3600.0


def _joints(root, m, xs=(C4X, UBX, HBX), w=3000.0):
    g = empty("joints", root)
    c4 = T.c4_window(g, m, xs[0], w=w)
    ub = T.pillar_window(g, m, xs[1], w=w)
    hb = T.hybrid_window(g, m, xs[2], w=w)
    return c4, ub, hb


def sec5():
    """5, connection density: C4 bumps, Cu-pillar microbumps, hybrid bonds, at one scale."""
    m, root = _sbegin("sec5", 3)
    (c4x, gap), (ubx, ubtop), hbx = _joints(root, m)
    label("C4 solder ball", (c4x[0], gap / 2, 2.0), root, span(0))
    label("~150 um pitch", ((c4x[0] + c4x[1]) / 2, gap / 2, 2.0), root, span(0))
    label("organic substrate", (C4X + 900, -300.0, 2.0), root, span(0))
    label("die", (C4X - 900, gap + 400.0, 2.0), root, span(0))
    label("Cu pillar", (ubx[3], 30.0 + 110.0 + 150.0, 2.0), root, span(1))
    label("solder cap", (ubx[4], 85.0, 3.0), root, span(1))
    label("~40 um pitch", ((ubx[1] + ubx[2]) / 2, 200.0, 2.0), root, span(1))
    label("silicon interposer", (UBX - 900, -300.0, 2.0), root, span(1))
    label("Cu pads bond, no solder", (hbx[14], 0.0, 2.0), root, span(2))
    label("oxide bonds to oxide", (hbx[11] + 50, 20.0, 2.0), root, span(2))
    label("~10 um pitch and below", (hbx[18], -20.0, 2.0), root, span(2))
    _send("sec5", root, [
        frame(C4X - 1550, -650.0, C4X + 1550, gap + 800.0, yaw=0.25, pitch=0.15, zc=-500.0),
        frame(UBX - 1550, -550.0, UBX + 1550, ubtop + 700.0, yaw=0.25, pitch=0.15, zc=-500.0),
        frame(HBX - 650, -300.0, HBX + 650, 300.0, yaw=0.25, pitch=0.15, zc=-400.0),
    ])


def _bspdn(root, m, cx, back, name):
    """One column of devices and wiring, power from the front (back=False) or from below."""
    g = empty(name, root)
    g.location = P(cx, 0.0, 0.0)
    x0, x1, z0 = -170.0, 170.0, -200.0
    xs = D.transistors(g, m, x0, x1, z0, 0.0, pitch=40.0, gate_w=12.0, h_si=(40.0 if back else 90.0))
    slab(f"{name}_pmd", x0, x1, 0.0, 48.0, z0, m["d_sio2"], g)
    specs = [dict(s, name=f"{name}{s['name']}") for s in T.FRONT_SPECS]
    if not back:
        specs += [dict(name=f"{name}P1", h=60.0, w=36.0, pitch=80.0, dir="z", gap=48.0),
                  dict(name=f"{name}P2", h=110.0, w=80.0, pitch=170.0, dir="x", gap=80.0, full=True, bt=6.0, lt=4.0)]
    lv = D.tower(g, m, specs, x0, x1, z0, y=48.0)
    top = lv["_top"]
    out = dict(g=g, lv=lv, top=top, xs=xs)
    if back:
        # a carrier wafer bonded on the front; the thinned silicon; backside metal and bumps below
        slab(f"{name}_bond", x0, x1, top, top + 20.0, z0, m["d_sio2"], g)
        slab(f"{name}_carrier", x0, x1, top + 20.0, top + 220.0, z0, m["d_die"], g)
        bl = D.tower(g, m, [dict(s, name=f"{name}{s['name']}") for s in T.BACK_SPECS], x0, x1, z0, y=-330.0)
        slab(f"{name}_bgap", x0, x1, bl["_top"], -40.0, z0, m["d_lowk"], g)
        for k, x in enumerate(xs[::2]):
            sx = x + 20.0
            box(f"{name}_ntsv{k}", (sx - 6.0, bl["_top"] - 2.0, -12.0), (sx + 6.0, -10.0, EPS * 2), m["d_cu"], g)
        slab(f"{name}_bpass", x0, x1, -400.0, -330.0, z0, m["d_sin"], g)
        for k, x in enumerate((-90.0, 90.0)):
            b = ball(f"{name}_bump{k}", (x, -460.0, -40.0), 70.0, m["d_solder"], g, 24)
            cut(b, EPS * 3)
        out.update(bl=bl, bump_y=-460.0, bot=-540.0)
    else:
        for k, x in enumerate((-90.0, 90.0)):
            b = ball(f"{name}_bump{k}", (x, top + 70.0, -40.0), 70.0, m["d_solder"], g, 24)
            cut(b, EPS * 3)
        out.update(bump_y=top + 70.0, bot=-100.0, top_all=top + 140.0)
    return out


def sec6():
    """6, backside power: front-side power shares the stack; BSPDN moves it under the silicon."""
    m, root = _sbegin("sec6", 3)
    fx, bx = -260.0, 260.0
    f = _bspdn(root, m, fx, False, "fs")
    b = _bspdn(root, m, bx, True, "bs")
    # beat 0 (and 2): power from the top bumps down the whole front stack; signals on F5
    for bb in (0, 2):
        dots(root, f"fp{bb}", [(fx - 90, f["bump_y"], DZ), (fx - 90, 10.0, DZ)], 10, 9.0, m["d_vdd"], bb, 0.02, 0.6, 80)
        dots(root, f"fsig{bb}", [(fx - 165, f["lv"]["fsF4"].yc, DZ), (fx + 165, f["lv"]["fsF4"].yc, DZ)], 6, 7.0, m["d_sig"], bb, 0.1, 0.6, 50)
    # beat 1 (and 2): power up from the back bumps through the BM levels and nano-TSVs
    for bb in (1, 2):
        dots(root, f"bp{bb}", [(bx - 90, b["bump_y"], DZ), (bx - 90, b["bl"]["bsBM2"].yc, DZ), (bx - 60, b["bl"]["bsBM2"].yc, DZ),
                               (bx - 60, -10.0, DZ)], 10, 9.0, m["d_vdd"], bb, 0.02, 0.6, 70)
        dots(root, f"bsig{bb}", [(bx - 165, b["lv"]["bsF4"].yc, DZ), (bx + 165, b["lv"]["bsF4"].yc, DZ)], 6, 7.0, m["d_sig"], bb, 0.1, 0.6, 50)
    label("bumps on the front", (fx + 90, f["bump_y"], 2.0), root, span(0))
    label("power shares M1-M8 with signals", (fx + 60, f["lv"]["fsP1"].yc, 2.0), root, span(0))
    label("a long way down to the devices", (fx - 90, f["lv"]["fsF3"].yc, DZ), root, span(0))
    label("backside metal BM0-BM2", (bx + 60, b["bl"]["bsBM1"].yc, 2.0), root, span(1))
    label("nano-TSVs through thin Si", (bx - 60, -25.0, DZ), root, span(1))
    label("bumps on the back", (bx + 90, b["bump_y"], 2.0), root, span(1))
    label("carrier wafer on the front", (bx, b["top"] + 120.0, 2.0), root, span(1))
    label("front: signals only", (bx + 100, b["lv"]["bsF5"].yc, 2.0), root, span(2))
    label("PowerVia: >30% lower droop", (bx - 100, b["bl"]["bsBM2"].yc, 2.0), root, span(2))
    label("front-side power today", (fx + 60, f["lv"]["fsP2"].yc, 2.0), root, span(2))
    _send("sec6", root, [
        frame(fx - 180, -110.0, fx + 180, f["top_all"] + 10, yaw=0.25, pitch=0.15),
        frame(bx - 180, b["bot"] - 10, bx + 180, b["top"] + 230, yaw=0.25, pitch=0.15),
        frame(fx - 190, b["bot"] - 10, bx + 190, b["top"] + 230, yaw=0.22, pitch=0.12),
    ])


INTEL4 = [30, 40, 45, 45, 50, 60, 60, 80, 80, 100, 100, 160, 160, 280, 400, 600]
TX, BX = 3500.0, 5000.0
J7 = (-1800.0, 0.0, 1800.0)  # the three joints, 1500 wide each, side by side


def sec7():
    """7, by the numbers: the joints at one scale, a 16-level stack, the revenue bars."""
    m, root = _sbegin("sec7", 3)
    (c4x, gap), (ubx, ubtop), hbx = _joints(root, m, J7, w=1500.0)
    g = empty("intel4", root)
    g.location = P(TX, 0.0, 0.0)
    specs = [dict(name=f"I{i}", h=float(p), w=p / 2.0, pitch=float(p), dir="z" if i % 2 == 0 else "x", gap=0.8 * p,
                  full=True) for i, p in enumerate(INTEL4)]
    lv = D.tower(g, m, specs, -300.0, 300.0, -300.0)
    top = lv["_top"]
    bars = empty("bars", root)
    items = [("Intel 2025: $52.9B", 52.9, "d_cu"), ("TSMC 2025: ~US$122B", 122.0, "d_cu"),
             ("Synopsys FY25: $7.1B", 7.1, "d_ru"), ("Cadence 2025: $5.3B", 5.3, "d_ru")]
    box("bar_plinth", (BX - 60, -60.0, -260.0), (BX + 4 * 380 - 60, 0.0, 20.0), m["d_si"], bars)
    for k, (text, v, mt) in enumerate(items):
        x = BX + k * 380
        box(f"bar{k}", (x, 0.0, -220.0), (x + 260, v * 20.0, 0.0), m[mt], bars)
        label(text, (x + 130, v * 20.0, 2.0), root, span(2))
    label("C4: ~150 um", (c4x[0], gap / 2, 2.0), root, span(0))
    label("microbump: 40 um", (ubx[1], 250.0, 2.0), root, span(0))
    label("hybrid: <=10 um", (hbx[7], 0.0, 2.0), root, span(0))
    label("Intel 4: M0 pitch 30 nm", (TX, lv["I0"].yc, 2.0), root, span(1))
    label("16 metal layers", (TX + 200, lv["I8"].yc, 2.0), root, span(1))
    label("top levels: widest, thickest", (TX, lv["I15"].yc, 2.0), root, span(1))
    _send("sec7", root, [
        frame(J7[0] - 780, -650.0, J7[2] + 780, 1650.0, yaw=0.15, pitch=0.12, pad=1.0, zc=-600.0),
        frame(TX - 320, -100.0, TX + 320, top + 30, yaw=0.40, pitch=0.12),
        frame(BX - 100, -100.0, BX + 4 * 380, 2600.0, yaw=0.20, pitch=0.12),
    ])


def _devices(root, m, cx, spr, name, oy=0.0):
    """One transistor on thinned silicon with backside metal under it: Intel PowerVia
    (spr=False, a nano-TSV beside the device up to the front contact) or TSMC Super Power Rail
    (spr=True, a contact straight from the backside rail into the source)."""
    g = empty(name, root)
    g.location = P(cx, oy, 0.0)
    z0 = -160.0
    slab(f"{name}_si", -200.0, 200.0, -40.0, 0.0, z0, m["d_si"], g)
    slab(f"{name}_sti", 100.0, 200.0, -40.0, 0.0, z0, m["d_sio2"], g, front=-0.2)
    for k, x in enumerate((-60.0, 60.0)):
        box(f"{name}_sd{k}", (x - 30.0, -32.0, z0 + 2), (x + 30.0, 8.0, 0.5), m["d_pplus"], g)
    box(f"{name}_gate", (-18.0, 0.0, z0 + 2), (18.0, 46.0, 0.6), m["d_gate"], g)
    slab(f"{name}_pmd", -200.0, 200.0, 0.0, 90.0, z0, m["d_sio2"], g)
    D.xline(f"{name}_m0", g, m, -190.0, 190.0, 90.0, 22.0, -14.0, 20.0, 3.0, 2.0)
    slab(f"{name}_ild", -200.0, 200.0, 90.0, 112.0, z0, m["d_lowk"], g)
    slab(f"{name}_bild", -200.0, 200.0, -110.0, -40.0, z0, m["d_lowk"], g)
    D.xline(f"{name}_bm0", g, m, -190.0, 190.0, -100.0, 40.0, -16.0, 24.0, 3.0, 2.0)
    slab(f"{name}_bsub", -200.0, 200.0, -170.0, -110.0, z0, m["d_si"], g)
    if spr:
        box(f"{name}_bsc", (30.0, -60.0, -24.0), (90.0, -32.0, EPS * 2), m["d_cu"], g)
    else:
        box(f"{name}_ct", (40.0, 8.0, -14.0), (80.0, 90.0, EPS * 2), m["d_w"], g)
        box(f"{name}_ntsv", (135.0, -60.0, -18.0), (165.0, 90.0, EPS * 2), m["d_cu"], g)
    return g


def sec8():
    """8, who makes it: Intel and TSMC backside contacts, the current a big GPU draws, sign-off."""
    m, root = _sbegin("sec8", 3)
    DX, SY = -1500.0, -400.0  # the two devices, one above the other, left of the grid block
    _devices(root, m, DX, False, "pv")
    _devices(root, m, DX, True, "spr", oy=SY)
    dots(root, "pv_i", [(DX + 150, -80.0, DZ), (DX + 150, 101.0, DZ), (DX + 60, 101.0, DZ), (DX + 60, -10.0, DZ)],
         8, 9.0, m["d_vdd"], 0, 0.02, 0.6, 60)
    dots(root, "spr_i", [(DX + 60, SY - 80.0, DZ), (DX + 60, SY - 10.0, DZ)], 8, 9.0, m["d_vdd"], 0, 0.02, 0.6, 40)
    lv = T.top_block(root, m)
    m13, m14 = lv["M13"], lv["M14"]
    cp = T.top_cap(root, m, lv, intervals=span(1), bump_iv=span(1), sub_iv=[])
    for k, x in enumerate((-20.0, 0.0, 20.0)):
        dots(root, f"amps{k}", _stack_path(lv, cp, x=x, z=DZ + k * 6)[:-1], 16, 22.0, m["d_vdd"], 1, 0.0 + k * 0.03, 0.75, 70)
    _stripes(root, m, lv, span(1), name="st8")
    # beat 2: an IR-drop map laid on the top of the grid, worst far from the bump sites
    hm = group("heat", root, span(2))
    top = lv["_top"]
    nx, nz = 10, 5
    sites = [(-600.0, -230.0), (600.0, -230.0)]
    for i in range(nx):
        for j in range(nz):
            xa = T.X0 + (T.X1 - T.X0) * i / nx
            za = T.Z0 + (0.0 - T.Z0) * j / nz
            xc, zc = xa + 100.0, za + 46.0
            d = min(math.hypot(xc - sx, zc - sz) for sx, sz in sites)
            lvl = min(4, int(d / 95.0))
            box(f"hm{i}_{j}", (xa + 3, top + 1.0, za + 3), (xa + 197, top + 6.0, za + 89), m[f"d_heat{lvl}"], hm)
    for k, (sx, sz) in enumerate(sites):
        ball(f"site{k}", (sx, top + 40.0, sz), 40.0, m["d_solder"], hm, 16)
    label("Intel PowerVia: nano-TSV", (DX + 150, 30.0, DZ), root, span(0))
    label("TSMC A16: contact into source", (DX + 60, SY - 46.0, DZ), root, span(0))
    label("backside power rail", (DX - 120, SY - 80.0, 2.0), root, span(0))
    label("transistor", (DX, 40.0, 2.0), root, span(0))
    label("big GPU: ~1 kW, 1,000+ A", (0.0, cp["bump_y"], 2.0), root, span(1))
    label("current down the via stack", (0.0, m13.yc, DZ), root, span(1))
    label("IR-drop map: red = worst", (850.0, top, -60.0), root, span(2))
    label("least drop near the bumps", (-600.0, top + 40.0, -230.0), root, span(2))
    _send("sec8", root, [
        frame(DX - 210.0, SY - 180.0, DX + 210.0, 130.0, yaw=0.22, pitch=0.15),
        frame(-800.0, m13.y0 - 40, 800.0, cp["bump_top"] + 40, yaw=0.25, pitch=0.16),
        ((0.0, top, -230.0), 3900.0, 0.0, 1.25),
    ])


def sec9():
    """9, how the top of the stack fails: droop and EM, microbump bridging, C4 fatigue."""
    m, root = _sbegin("sec9", 3)
    lv = T.top_block(root, m)
    m12, m13, m14 = lv["M12"], lv["M13"], lv["M14"]
    ir = group("ir9", root, span(0))
    for s, (a, b) in (("r", (0.0, 1000.0)), ("l", (0.0, -1000.0))):
        D.heat_strip(ir, m, f"ir9_{s}", min(a, b), max(a, b), m13.y0 - 2, m13.y1 + 2, -4.0, 6.0, n=6, reverse=(s == "l"))
    vg = group("void9", root, span(0))
    grow("void9_p", vg, (800.0, m13.y1, 0.0), lambda p: box("void9_b", (-50.0, 0.0, -60.0), (50.0, 24.0, 9.0), m["d_void"], p),
         [(F(0, 0.2), 0.05), (F(0, 0.8), 1.0)])
    # beat 1: microbumps at fine pitch, two solder caps run together
    g1 = empty("ub9", root)
    UX = 2700.0
    xs, ubtop = T.pillar_window(g1, m, UX, w=1600.0, name="ub9")
    a, b = xs[1], xs[2]
    br = group("bridge", root, [(F(1, 0.3), F(2, 0))])
    box("bridge_sn", (a, 40.0, -200.0), (b, 120.0, EPS * 4), m["d_solder"], br)
    box("bridge_glow", (a - 20, 30.0, -10.0), (b + 20, 130.0, EPS * 6), m["d_bad"], br)
    # beat 2: a C4 joint between a die and a substrate that expand by different amounts
    cx = 5600.0
    g2 = empty("c4f", root)
    sub = empty("c4f_sub", g2)
    T.slab("c4f_subs", cx - 1300, cx + 1300, -600.0, 0.0, -1200.0, m["d_subst"], sub)
    box("c4f_lp", (cx - 380, 0.0, -1100.0), (cx + 380, 30.0, EPS), m["d_cu"], sub)
    for k, f in enumerate((0.0, 0.25, 0.5, 0.75, 1.0)):
        key(sub, F(2, f), "location", P(-50.0 if k % 2 else 50.0, 0, 0))
    bl = ball("c4f_ball", (cx, 400.0, -250.0), 500.0, m["d_solder"], g2, 32)
    bl.scale = (1.0, 1.0, 0.8)
    cut(bl, EPS * 2)
    box("c4f_up", (cx - 330, 770.0, -1100.0), (cx + 330, 800.0, EPS), m["d_ubm"], g2)
    T.die(g2, m, "c4f_die", cx - 1300, cx + 1300, 800.0, thick=700.0, beol=80.0)
    ck = group("crack", root, span(2))
    grow("crack_p", ck, (cx - 300.0, 735.0, 0.0), lambda p: box("crack_b", (0.0, -8.0, -40.0), (360.0, 8.0, EPS * 5), m["d_crack"], p),
         [(F(2, 0.1), (0.05, 1, 1)), (F(2, 0.6), (1, 1, 1))])
    uf = group("uf9", root, [(F(2, 0.65), F(3, 0))])
    box("uf9_l", (cx - 1300, 30.0, -1200.0), (cx - 505, 770.0, -0.6), m["d_underfill_o"], uf)
    box("uf9_r", (cx + 505, 30.0, -1200.0), (cx + 1300, 770.0, -0.6), m["d_underfill_o"], uf)
    label("IR drop: lowest V at the ends", (850.0, m13.yc, 6.0), root, span(0))
    label("EM void at a via", (800.0, m13.y1 + 12, 9.0), root, span(0))
    label("solder caps bridge: a short", ((a + b) / 2, 80.0, 6.0), root, [(F(1, 0.3), F(2, 0))])
    label("~40 um pitch, little room", (xs[3], 300.0, 2.0), root, span(1))
    label("Si ~3 ppm/K", (cx + 700, 1200.0, 2.0), root, span(2))
    label("substrate ~15+ ppm/K", (cx + 700, -300.0, 2.0), root, span(2))
    label("crack at the neck", (cx - 120, 735.0, 6.0), root, [(F(2, 0.15), F(2, 0.65))])
    label("underfill: >10x life", (cx - 900, 400.0, 2.0), root, [(F(2, 0.65), F(3, 0))])
    _send("sec9", root, [
        frame(-1010.0, m12.y0 - 30, 1010.0, m14.y1 + 30, yaw=0.20, pitch=0.18),
        frame(UX - 820, -520.0, UX + 820, ubtop + 400.0, yaw=0.25, pitch=0.15, zc=-500.0),
        frame(cx - 1350, -650.0, cx + 1350, 1600.0, yaw=0.20, pitch=0.12, zc=-500.0),
    ])


def sec10():
    """10, sources: the top of the stack, turned, while the source list is read."""
    m, root = _sbegin("sec10", 4)
    lv = T.top_block(root, m)
    cp = T.top_cap(root, m, lv)
    label("M10-M14 under the bump", (-600.0, lv["M13"].yc, 2.0), root, span(0))
    label("C4 bump and pad", (0.0, cp["bump_y"], 2.0), root, span(1))
    label("M14 power stripes", (lv["M14"].xs[3], lv["M14"].yc, 2.0), root, span(2))
    label("package substrate", (-500.0, cp["sub_y"] + 160.0, 2.0), root, span(3))
    _send("sec10", root, [
        frame(-1010.0, -90.0, 1010.0, cp["sub_top"], yaw=0.35, pitch=0.18),
        frame(-500.0, lv["M14"].y0, 500.0, cp["sub_top"], yaw=0.25, pitch=0.15),
        frame(-1010.0, lv["M12"].y0, 1010.0, lv["M14"].y1 + 60, yaw=-0.30, pitch=0.25),
        frame(-1010.0, -90.0, 1010.0, cp["sub_top"], yaw=0.05, pitch=0.10),
    ])


SCENES = {
    "zoom_a": zoom_a, "zoom_b": zoom_b, "zoom_c": zoom_c, "zoom_d": zoom_d, "zoom_e": zoom_e,
    "sec1": sec1, "sec2": sec2, "sec3": sec3, "sec4": sec4, "sec5": sec5,
    "sec6": sec6, "sec7": sec7, "sec8": sec8, "sec9": sec9, "sec10": sec10,
}


if __name__ == "__main__":
    names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not names:
        build()
        finish("top_metal", page="chip")
        names = list(SCENES)
    for name in names:
        if name == "overview":
            build()
            finish("top_metal", page="chip")
        else:
            SCENES[name]()
