"""CHIP pictures for TOP METAL: the overview, five zoom-ins (a-e) and ten sections.

Run from the repo root (names after -- pick scenes, none means all of them):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_top_metal.py [-- zoom_a sec3 ...]

Writes blender/chip_top_metal*.blend and assets/chip_top_metal*.glb. One beat is 8 s.

Overview (6 beats, the whole chip, in on the thick top levels M10-M14):
  0 whole    the whole chip, the top tier (M10-M14) lit, the package bumps above it
  1 bumps    zoomed in: VDD comes in through a bump, down the bond pad onto the top rail
  2 grid     the camera on the fat rails: the VDD current spreads both ways along them
  3 clock    the clock trunk on the middle top level fans out from one point
  4 thick    a thin wire and a top rail of the same length: the thick one has the lower R
  5 whole    back out: VSS climbs back up to its bump, the whole chip again

Zoom-ins, the same chip with the camera gliding into one part (3 beats each):
  a the top loop: metal, pads, bumps     b jobs of the thick levels
  c power delivery and IR drop           d bumps to hybrid bonds
  e backside power (BSPDN)

Sections, one whole-chip picture per `# ` heading of CHIP_TOP_METAL.txt (3 beats; 10 has 4):
  sec1 what happens   sec2 whole stack   sec3 jobs   sec4 power delivery   sec5 connection density
  sec6 backside power sec7 by the numbers sec8 who makes it sec9 how it fails sec10 sources
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, P, ball, box, empty, glide_camera, key, label, mat, overlay, route, show, stream_of, tube  # noqa: E402

BEATS = 6

TOP_LIT = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
BUMPS_LIT = [(F(1, 0.05), F(2, 0)), (F(5, 0), F(6, 0))]
CLOCK_ON = [(F(3, 0), F(4, 0))]
THICK_ON = [(F(4, 0), F(5, 0))]

WHOLE = C.WHOLE
BUMPS_POSE = ((700.0, 1300.0, 0.0), 1500.0, 0.0, 0.10)
RAILS_POSE = ((0.0, 1230.0, 0.0), 3400.0, 0.0, 0.10)
THICK_POSE = ((1760.0, 830.0, 0.0), 1900.0, 0.0, 0.10)
POSES = [WHOLE, BUMPS_POSE, RAILS_POSE, RAILS_POSE, THICK_POSE, WHOLE]

Y_TOP0 = C.level_y("top", 0)  # the full-width rail nearest the pads
Y_CLK = C.level_y("top", 1)  # the middle top level, broken by a gap at the centre
Y_TOP2 = C.level_y("top", 2)  # the full-width rail under the bumps
Y_THIN = C.level_y("thin", 1)  # a thin wire, for the comparison
Y_MID2 = C.level_y("mid", 2)  # a medium block-signal level
_, _, TOP_H, TOP_D = C.TIERS["top"]
X0, X1 = 1620.0, 1960.0  # the comparison stubs, same length
DOT_Z = 30.0  # stream dots run just in front of the cut plane, so the copper does not hide them
TOP = C.TOP
BUMP_Y = C.BUMP_Y
VDD_X, VSS_X = C.VDD_X, C.VSS_X
TOP_BOT_Y = 410.0  # the bottom of the VDD via column (level 0 of the thin tier)
TOP_VIA_Y = TOP[1] - 40.0  # the top of that via column


def span(b0, b1=None):
    """Shown for whole beats b0 through b1 (inclusive)."""
    b1 = b0 if b1 is None else b1
    return [(F(b0, 0), F(b1 + 1, 0))]


def _mats(m):
    m["clk"] = mat("chip_top_metal_clk", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=3.0)
    m["clk_dot"] = mat("chip_top_metal_clk_dot", (0.50, 1.0, 0.55), emit=(0.45, 1.0, 0.50), strength=3.5)
    m["clk_lit"] = mat("chip_top_metal_clk_lit", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=1.0, alpha=0.25)
    m["hot"] = mat("chip_top_metal_hot", (1.0, 0.35, 0.15), emit=(1.0, 0.30, 0.10), strength=2.0, alpha=0.45)
    m["hot_dot"] = mat("chip_top_metal_hot_dot", (1.0, 0.45, 0.20), emit=(1.0, 0.40, 0.18), strength=3.5)
    m["barrier"] = mat("chip_top_metal_barrier", (0.80, 0.86, 1.0), emit=(0.75, 0.85, 1.0), strength=1.2, alpha=0.35)
    m["passiv"] = mat("chip_top_metal_passiv", (0.45, 0.55, 0.85), rough=0.5, alpha=0.30)
    m["trace"] = mat("chip_top_metal_trace", (0.85, 0.55, 1.0), emit=(0.80, 0.50, 1.0), strength=2.5)
    m["underfill"] = mat("chip_top_metal_underfill", (0.55, 0.62, 0.78), rough=0.5, alpha=0.18)
    m["tsv"] = mat("chip_top_metal_tsv", (0.95, 0.62, 0.30), emit=(1.0, 0.60, 0.30), strength=1.5)
    m["rail_bs"] = mat("chip_top_metal_rail_bs", (0.85, 0.55, 0.30), metal=0.8, rough=0.35)
    m["pillar"] = mat("chip_top_metal_pillar", (0.80, 0.85, 0.92), metal=0.7, rough=0.3)


def _begin(name, beats):
    m, root = start(f"top_metal_{name}", beats, page="chip")
    C.mats(m)
    _mats(m)
    parts = C.chip(root, m)
    return m, root, parts


def _end(name, root, poses):
    glide_camera(root, poses)
    finish(f"top_metal_{name}", page="chip")


def hl(root, name, x0, x1, y0, y1, m, intervals, z0=-130.0, z1=12.0):
    """A lit overlay on a rectangle of the chip, in front of the cut plane's copper."""
    return overlay(root, name, (x0, y0, z0), (x1, y1, z1), m, intervals)


def _light_top(root, m, intervals):
    hl(root, "top_lit", -1450.0, 1450.0, TOP[0] - 4, TOP[1] + 4, m["c_lit_top"], intervals, z0=-660.0, z1=6.0)


def _light_bumps(root, m, b, all_=False, xs=None):
    xs = [C.bump_x(i) for i in C.BUMP_I] if all_ else (xs or [VSS_X, VDD_X])
    g = empty(f"bumps_lit{b}", root)
    for x in xs:
        ball(f"bl{b}_{x:.0f}", (x, BUMP_Y, -60.0), 70, m["c_bump_on"], g, 14)
    show(g, span(b))


def _power_grid(root, m, b):
    """Vdd on the full-width top rails: the current from the VDD bump spreads both ways."""
    hl(root, f"grid_lit{b}", -1450.0, 1450.0, Y_TOP0 - 60, Y_TOP2 + 60, m["c_lit_top"], span(b))
    s, p = route([(VDD_X, Y_TOP0, DOT_Z), (-1420.0, Y_TOP0, DOT_Z)])
    stream_of(root, f"grid_l{b}", 10, s, p, 46, m["c_dot_vdd"], b, 0.05, 0.50, 110)
    s, p = route([(VDD_X, Y_TOP0, DOT_Z), (1420.0, Y_TOP0, DOT_Z)])
    stream_of(root, f"grid_r{b}", 8, s, p, 46, m["c_dot_vdd"], b, 0.05, 0.50, 110)
    label("Vdd stripe", (1000.0, Y_TOP0 + 110.0, 0.0), root, span(b))
    label("Vss stripe", (-1000.0, Y_TOP2 + 110.0, 0.0), root, span(b))


def _clock(root, m, b):
    """The clock source in the gap of the middle top level; its trunk fans out both ways."""
    show(ball(f"clk_src{b}", (0.0, Y_CLK, -60.0), 70, m["clk"], root, 14), span(b))
    for k, (x0, x1) in enumerate(((-1460.0, -100.0), (100.0, 1460.0))):
        overlay(root, f"clk_band{b}_{k}", (x0, Y_CLK - TOP_H / 2 - 8, -60 - TOP_D / 2 - 8),
                (x1, Y_CLK + TOP_H / 2 + 8, -60 + TOP_D / 2 + 8), m["clk_lit"], span(b))
    for name_, x1 in (("clk_left", -1420.0), ("clk_right", 1420.0)):
        s, p = route([(0.0, Y_CLK, DOT_Z), (x1, Y_CLK, DOT_Z)])
        stream_of(root, f"{name_}{b}", 9, s, p, 46, m["clk_dot"], b, 0.05, 0.55, 90)
    s, p = route([(-1420.0, Y_TOP2, DOT_Z), (1420.0, Y_TOP2, DOT_Z)])
    stream_of(root, f"long{b}", 9, s, p, 46, m["c_dot_out"], b, 0.10, 0.60, 110)
    label("clock source", (0.0, Y_CLK + 150.0, 0.0), root, span(b))
    label("clock trunk", (760.0, Y_CLK - 150.0, 0.0), root, span(b))
    label("long wires", (-900.0, Y_TOP2 + 110.0, 0.0), root, span(b))


def _rdl(root, m, b):
    """A redistribution trace re-routes the VDD pad; the underfill epoxy sits round the bumps."""
    overlay(root, f"rdl{b}", (VDD_X, TOP[1] + 14.0, -10.0), (VDD_X + 360.0, TOP[1] + 30.0, 14.0), m["trace"], span(b))
    overlay(root, f"underfill{b}", (-1500.0, BUMP_Y - 60.0, -150.0), (1500.0, BUMP_Y - 20.0, 40.0), m["underfill"], span(b))
    _light_bumps(root, m, b, xs=(VDD_X, VSS_X))
    label("RDL re-routes the pad", (VDD_X + 420.0, TOP[1] + 60.0, 14.0), root, span(b))
    label("underfill epoxy", (-1100.0, BUMP_Y + 100.0, 40.0), root, span(b))


def _path(root, m, b):
    """Current from the bump, down the VDD via column to the PMOS source."""
    s, p = route([(VDD_X, BUMP_Y, DOT_Z), (VDD_X, Y_TOP0, DOT_Z), (VDD_X, C.level_y("thin", 0), DOT_Z), (VDD_X, 6.0, DOT_Z)])
    stream_of(root, f"path{b}", 10, s, p, 46, m["c_dot_vdd"], b, 0.05, 0.60, 150)
    label("bump to transistor", (VDD_X + 170.0, 850.0, 30.0), root, span(b))


def _hot_top(root, m, b):
    """The top rail heats up and the voltage drops with distance from the bump."""
    hl(root, f"hot_rail{b}", VDD_X, 1450.0, Y_TOP0 - 60, Y_TOP0 + 60, m["hot"], span(b))
    s, p = route([(VDD_X, Y_TOP0, DOT_Z), (1420.0, Y_TOP0, DOT_Z)])
    stream_of(root, f"hot_flow{b}", 7, s, p, 46, m["hot_dot"], b, 0.05, 0.50, 110)
    label("top rail: V drops", (1150.0, Y_TOP0 + 120.0, 0.0), root, span(b))


def _hot_via(root, m, b):
    """The VDD via column carries the most current per area: it is where electromigration starts."""
    overlay(root, f"hot_via{b}", (VDD_X - 50.0, TOP_BOT_Y - 10, -90.0), (VDD_X + 50.0, TOP_VIA_Y + 10, -30.0),
            m["hot"], span(b))
    s, p = route([(VDD_X, TOP_BOT_Y, DOT_Z), (VDD_X, TOP_VIA_Y, DOT_Z)])
    stream_of(root, f"hot_up{b}", 9, s, p, 46, m["hot_dot"], b, 0.05, 0.60, 60)
    label("via: EM limit", (VDD_X + 170.0, 900.0, 30.0), root, span(b))


def _pillars(root, m, b):
    """Microbumps: a row of fine copper pillars at about 40 um pitch."""
    g = empty(f"micro{b}", root)
    for k in range(5):
        x = VDD_X - 80.0 + 40.0 * k
        tube(f"pillar{b}_{k}", (x, Y_TOP2 + 45.0, -60.0), (x, Y_TOP2 + 135.0, -60.0), 16, m["pillar"], g, verts=10)
        ball(f"pillar_cap{b}_{k}", (x, Y_TOP2 + 150.0, -60.0), 20, m["c_bump"], g, 12)
    show(g, span(b))
    label("microbump, 40 um pitch", (VDD_X, Y_TOP2 + 230.0, 0.0), root, span(b))


def _hybrid(root, m, b):
    """Hybrid bonding: flat copper pads meet directly, with no solder."""
    g = empty(f"hybrid{b}", root)
    for k in range(12):
        x = 780.0 + 22.0 * k
        box(f"hpad{b}_{k}", (x, Y_TOP2 + 45.0, -90.0), (x + 12.0, Y_TOP2 + 57.0, -20.0), m["c_cu_top"], g)
    show(g, span(b))
    label("hybrid bond, no solder", (VDD_X, Y_TOP2 + 140.0, 0.0), root, span(b))


def _rails(root, m, intervals, name="rails"):
    """The backside metals under the thinned silicon, with nano-TSVs up to the devices."""
    g = empty(name, root)
    box(f"{name}_vss", (-1450.0, -360.0, -260.0), (1450.0, -320.0, -40.0), m["rail_bs"], g)
    box(f"{name}_vdd", (-1450.0, -360.0, -520.0), (1450.0, -320.0, -300.0), m["c_cu_mid"], g)
    for x in (VDD_X, VSS_X):
        tube(f"{name}_tsv{x:.0f}", (x, -330.0, -150.0), (x, 6.0, -150.0), 22, m["tsv"], g, verts=10)
    show(g, intervals)


def _back_power(root, m, b):
    """Power comes up from the backside rail through the nano-TSV to the PMOS source."""
    s, p = route([(VDD_X, -340.0, DOT_Z), (VDD_X, 6.0, DOT_Z)])
    stream_of(root, f"back{b}", 9, s, p, 46, m["c_dot_vdd"], b, 0.05, 0.60, 110)


def _signal(root, m, b, text=None):
    """Signals run on the front, across a medium level."""
    s, p = route([(-1300.0, Y_MID2, DOT_Z), (1300.0, Y_MID2, DOT_Z)])
    stream_of(root, f"sig{b}", 8, s, p, 46, m["c_dot_sig"], b, 0.05, 0.50, 110)
    if text:
        label(text, (-1150.0, Y_MID2 + 120.0, 30.0), root, span(b))


def _explode(parts):
    """The tiers slide apart (beat 1) and back together (beat 2)."""
    for tier, off in (("top", 300.0), ("bumps", 480.0), ("mid", 150.0)):
        g = parts[tier]
        key(g, F(0, 0), "location", P(0, 0, 0), linear=True)
        key(g, F(1, 0), "location", P(0, 0, 0), linear=True)
        key(g, F(1, 0.6), "location", P(0, off, 0), linear=True)
        key(g, F(2, 0.4), "location", P(0, off, 0), linear=True)
        key(g, F(2, 0.9), "location", P(0, 0, 0), linear=True)
        key(g, F(3, 0), "location", P(0, 0, 0), linear=True)


# ---- the overview ---------------------------------------------------------------------------


def build(name="top_metal", poses=POSES):
    m, root = start(name, BEATS, page="chip")
    C.mats(m)
    _mats(m)
    C.chip(root, m, top=TOP_LIT, bumps=BUMPS_LIT)

    # beat 1: VDD comes in through the bump, down the pad onto the top rail
    s, p = route([(VDD_X, BUMP_Y, DOT_Z), (VDD_X, Y_TOP0, DOT_Z)])
    stream_of(root, "vdd_in", 9, s, p, 46, m["c_dot_vdd"], 1, 0.10, 0.60, 90)

    # beat 2: along the full-width rail, away from the bump, both ways
    s, p = route([(VDD_X, Y_TOP0, DOT_Z), (-1420.0, Y_TOP0, DOT_Z)])
    stream_of(root, "vdd_left", 10, s, p, 46, m["c_dot_vdd"], 2, 0.05, 0.50, 110)
    s, p = route([(VDD_X, Y_TOP0, DOT_Z), (1420.0, Y_TOP0, DOT_Z)])
    stream_of(root, "vdd_right", 6, s, p, 46, m["c_dot_vdd"], 2, 0.05, 0.50, 60)

    # beat 3: the clock source in the gap of the middle top level, and its trunk fanning out
    src = ball("clk_src", (0.0, Y_CLK, -60.0), 70, m["clk"], root, 14)
    show(src, CLOCK_ON)
    for k, (x0, x1) in enumerate(((-1460.0, -100.0), (100.0, 1460.0))):
        overlay(root, f"clk_band{k}", (x0, Y_CLK - TOP_H / 2 - 8, -60 - TOP_D / 2 - 8),
                (x1, Y_CLK + TOP_H / 2 + 8, -60 + TOP_D / 2 + 8), m["clk_lit"], CLOCK_ON)
    for name_, x1 in (("clk_left", -1420.0), ("clk_right", 1420.0)):
        s, p = route([(0.0, Y_CLK, DOT_Z), (x1, Y_CLK, DOT_Z)])
        stream_of(root, name_, 9, s, p, 46, m["clk_dot"], 3, 0.05, 0.55, 90)

    # beat 4: two stubs of the same length, the thin wire below and the top rail above
    cmp = empty("compare", root)
    box("thin_stub", (X0, Y_THIN - 12, -60 - 20), (X1, Y_THIN + 12, -60 + 20), m["c_cu_thin"], cmp)
    box("top_stub", (X0, Y_CLK - TOP_H / 2, -60 - TOP_D / 2), (X1, Y_CLK + TOP_H / 2, -60 + TOP_D / 2),
        m["c_cu_top"], cmp)
    show(cmp, THICK_ON)
    s, p = route([(X0, Y_THIN, DOT_Z), (X1, Y_THIN, DOT_Z)])
    stream_of(root, "thin_flow", 6, s, p, 24, m["c_dot_vdd"], 4, 0.05, 0.50, 60)
    s, p = route([(X0, Y_CLK, DOT_Z), (X1, Y_CLK, DOT_Z)])
    stream_of(root, "top_flow", 6, s, p, 40, m["c_dot_vdd"], 4, 0.05, 0.50, 60)

    # beat 5: VSS climbs back up the top rail to its bump
    s, p = route([(VSS_X, Y_TOP0, DOT_Z), (VSS_X, BUMP_Y, DOT_Z)])
    stream_of(root, "vss_out", 9, s, p, 46, m["c_dot_gnd"], 5, 0.10, 0.60, 90)

    whole = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
    label("top metal M10-M14", (1520.0, Y_CLK, 0.0), root, whole)
    label("package bumps", (VSS_X, BUMP_Y + 120, 0.0), root, [(F(0, 0), F(1, 0))])
    label("VDD in", (VDD_X, BUMP_Y + 120, 0.0), root, [(F(1, 0), F(2, 0))])
    label("bond pad", (VDD_X + 200, 1060.0, 0.0), root, [(F(1, 0), F(2, 0))])
    label("top rail: Vdd", (VDD_X + 200, Y_TOP0 + 110, 0.0), root, [(F(1, 0), F(2, 0))])
    label("Vdd spreads both ways", (-700.0, Y_TOP2 + 60.0, 0.0), root, [(F(2, 0), F(3, 0.9))])
    label("clock source", (0.0, Y_CLK + 150.0, 0.0), root, [(F(3, 0), F(4, 0))])
    label("clock trunk", (760.0, Y_CLK - 150.0, 0.0), root, [(F(3, 0.1), F(4, 0))])
    label("thin wire M1-M4", (X0, Y_THIN - 80.0, 0.0), root, [(F(4, 0), F(5, 0))])
    label("top rail M10-M14", (X0, Y_CLK + 85.0, 0.0), root, [(F(4, 0), F(5, 0))])
    label("R = rho L / (W T)", (X0, 640.0, 0.0), root, [(F(4, 0), F(5, 0))])
    label("VSS return", (VSS_X, BUMP_Y + 120, 0.0), root, [(F(5, 0), F(6, 0))])

    glide_camera(root, poses)


# ---- zoom-ins (the same chip, the camera in on one part) ------------------------------------


def zoom_a():
    """a: the top loop. Trench and barrier, copper plate and CMP, then the pad and the bump."""
    m, root, parts = _begin("zoom_a", 3)
    _light_top(root, m, span(0, 2))
    hl(root, "barrier", 600.0, 1000.0, Y_CLK - TOP_H / 2 - 12, Y_CLK + TOP_H / 2 + 12, m["barrier"], span(0))
    label("trench, barrier + seed", (1000.0, Y_CLK + 120.0, 0.0), root, span(0))
    hl(root, "cu_plate", 600.0, 1000.0, Y_CLK - TOP_H / 2 - 12, Y_CLK + TOP_H / 2 + 12, m["c_lit_top"], span(1))
    label("Cu plate, then CMP", (1000.0, Y_CLK + 120.0, 0.0), root, span(1))
    hl(root, "passiv", VDD_X - 190.0, VDD_X + 190.0, TOP[1] + 4, TOP[1] + 46, m["passiv"], span(2))
    label("passivation", (VDD_X - 260.0, TOP[1] + 80.0, 12.0), root, span(2))
    label("bond pad", (VDD_X + 260.0, TOP[1] + 20.0, 0.0), root, span(2))
    _light_bumps(root, m, 2, xs=(VDD_X,))
    label("solder bump", (VDD_X + 160.0, BUMP_Y + 110.0, 0.0), root, span(2))
    _end("zoom_a", root, [((800.0, Y_CLK, 0.0), 1500.0, 0.10, 0.05),
                          ((800.0, Y_CLK, 0.0), 1300.0, 0.10, 0.05),
                          ((850.0, 1380.0, 0.0), 1100.0, 0.10, 0.10)])


def zoom_b():
    """b: jobs of the thick levels. The power grid, the clock trunk and long wires, the RDL."""
    m, root, parts = _begin("zoom_b", 3)
    _power_grid(root, m, 0)
    _clock(root, m, 1)
    _rdl(root, m, 2)
    _end("zoom_b", root, [((0.0, Y_TOP0 + 60.0, 0.0), 3000.0, 0.05, 0.05),
                          ((0.0, Y_CLK, 0.0), 2800.0, 0.05, 0.05),
                          ((900.0, 1440.0, 0.0), 1400.0, 0.10, 0.10)])


def zoom_c():
    """c: power delivery and IR drop. The path down the vias, the droop along the rail, the EM limit."""
    m, root, parts = _begin("zoom_c", 3)
    _path(root, m, 0)
    _hot_top(root, m, 1)
    _hot_via(root, m, 2)
    _end("zoom_c", root, [((700.0, 760.0, 0.0), 3000.0, 0.10, 0.05),
                          ((1100.0, Y_TOP0, 0.0), 1800.0, 0.05, 0.05),
                          ((760.0, 900.0, 0.0), 2600.0, 0.10, 0.05)])


def zoom_d():
    """d: bumps to hybrid bonds. The C4 bump row, then the microbump pillars, then flat hybrid pads."""
    m, root, parts = _begin("zoom_d", 3)
    show(parts["bumps"], span(0))
    _light_bumps(root, m, 0, all_=True)
    label("C4 bumps, 150 um", (-300.0, BUMP_Y + 170.0, 0.0), root, span(0))
    _pillars(root, m, 1)
    _hybrid(root, m, 2)
    _end("zoom_d", root, [((0.0, BUMP_Y, 0.0), 2600.0, 0.05, 0.05),
                          ((VDD_X, Y_TOP2 + 100.0, 0.0), 900.0, 0.05, 0.10),
                          ((VDD_X, Y_TOP2 + 100.0, 0.0), 800.0, 0.05, 0.10)])


def zoom_e():
    """e: backside power. Front-side power shares the stack; then the rails move under the silicon."""
    m, root, parts = _begin("zoom_e", 3)
    _path(root, m, 0)
    _signal(root, m, 0, "power and signal share the front")
    _rails(root, m, span(1, 2))
    _back_power(root, m, 1)
    label("backside metals BM0-BM5", (-1100.0, -340.0, 40.0), root, span(1))
    _back_power(root, m, 2)
    _signal(root, m, 2)
    label("over 30% lower droop", (-1100.0, -340.0, 40.0), root, span(2))
    _end("zoom_e", root, [((0.0, 700.0, 0.0), 3200.0, 0.10, 0.10),
                          ((0.0, -120.0, 0.0), 2400.0, 0.10, 0.12),
                          ((0.0, 300.0, 0.0), 3300.0, 0.10, 0.10)])


# ---- sections: one whole-chip picture per `# ` heading of CHIP_TOP_METAL.txt ----------------


def sec1():
    """1 what happens: the top tier is built, then the pads and bumps go on it."""
    m, root, parts = _begin("sec1", 3)
    _light_top(root, m, span(0))
    label("M10-M14 thick copper", (1250.0, Y_CLK, 0.0), root, span(0))
    _light_bumps(root, m, 1, all_=True)
    label("bumps and pads", (VSS_X, BUMP_Y + 150.0, 0.0), root, span(1))
    label("ready for packaging", (0.0, 1700.0, 0.0), root, span(2))
    _end("sec1", root, [WHOLE, ((0.0, 1350.0, 0.0), 3000.0, 0.05, 0.10), WHOLE])


def sec2():
    """2 the whole stack: thin wires, then medium, then the thick top and the bumps."""
    m, root, parts = _begin("sec2", 3)
    hl(root, "thin_lit", -1450.0, 1450.0, C.THIN[0] - 10, C.THIN[1] + 10, m["c_lit_thin"], span(0))
    label("transistors, M1-M4", (1250.0, 500.0, 0.0), root, span(0))
    hl(root, "mid_lit", -1450.0, 1450.0, C.MID[0] - 10, C.MID[1] + 10, m["c_lit_mid"], span(1))
    label("M5-M9 medium copper", (1250.0, 830.0, 0.0), root, span(1))
    _light_top(root, m, span(2))
    _light_bumps(root, m, 2, all_=True)
    label("M10-M14 and bumps", (1250.0, Y_CLK, 0.0), root, span(2))
    _end("sec2", root, [WHOLE, WHOLE, WHOLE])


def sec3():
    """3 jobs of the thick layers: the power grid, the clock trunk and long wires, the RDL."""
    m, root, parts = _begin("sec3", 3)
    _power_grid(root, m, 0)
    _clock(root, m, 1)
    _rdl(root, m, 2)
    _end("sec3", root, [((0.0, 1000.0, 0.0), 4200.0, 0.05, 0.10)] * 3)


def sec4():
    """4 power delivery: the path from the bump, the droop along the rail, the EM limit."""
    m, root, parts = _begin("sec4", 3)
    _path(root, m, 0)
    _hot_top(root, m, 1)
    _hot_via(root, m, 2)
    _end("sec4", root, [((0.0, 760.0, 0.0), 5000.0, 0.05, 0.10)] * 3)


def sec5():
    """5 connection density: C4 bumps, then microbumps, then hybrid bonds."""
    m, root, parts = _begin("sec5", 3)
    show(parts["bumps"], span(0))
    _light_bumps(root, m, 0, all_=True)
    label("C4 bumps, 150 um", (-300.0, BUMP_Y + 170.0, 0.0), root, span(0))
    _pillars(root, m, 1)
    _hybrid(root, m, 2)
    _end("sec5", root, [WHOLE, ((VDD_X, Y_TOP2 + 100.0, 0.0), 1900.0, 0.05, 0.10),
                        ((VDD_X, Y_TOP2 + 100.0, 0.0), 1400.0, 0.05, 0.10)])


def sec6():
    """6 backside power: front-side power shares the stack, then the rails go under the silicon."""
    m, root, parts = _begin("sec6", 3)
    _path(root, m, 0)
    _signal(root, m, 0, "power and signal share the front")
    _rails(root, m, span(1, 2))
    _back_power(root, m, 1)
    label("backside metals BM0-BM5", (-1100.0, -340.0, 40.0), root, span(1))
    _back_power(root, m, 2)
    _signal(root, m, 2)
    label("over 30% lower droop", (-1100.0, -340.0, 40.0), root, span(2))
    _end("sec6", root, [((0.0, 700.0, 0.0), 5000.0, 0.05, 0.10),
                        ((0.0, 0.0, 0.0), 4200.0, 0.05, 0.12),
                        ((0.0, 200.0, 0.0), 5000.0, 0.05, 0.10)])


def sec7():
    """7 by the numbers: the pitches, the Intel stack exploded, the revenue labels."""
    m, root, parts = _begin("sec7", 3)
    _explode(parts)
    label("C4 ~150 um", (-1000.0, BUMP_Y + 170.0, 0.0), root, span(0))
    label("microbump 40 um", (0.0, BUMP_Y + 170.0, 0.0), root, span(0))
    label("hybrid <=10 um", (1000.0, BUMP_Y + 170.0, 0.0), root, span(0))
    label("16 metal layers (Intel 4)", (1250.0, 1800.0, 0.0), root, span(1))
    label("M0 pitch 30 nm", (-1250.0, 400.0, 0.0), root, span(1))
    label("Intel $52.9B", (-1250.0, 1100.0, 0.0), root, span(2))
    label("TSMC ~$122B", (1250.0, 1100.0, 0.0), root, span(2))
    _end("sec7", root, [WHOLE, ((0.0, 800.0, 0.0), 4600.0, 0.05, 0.12), WHOLE])


def sec8():
    """8 who makes it: the backside rails (TSMC, Intel), big currents (NVIDIA, AMD, Arm), sign-off."""
    m, root, parts = _begin("sec8", 3)
    _rails(root, m, span(0), name="rails8")
    label("TSMC A16, Intel 18A", (0.0, -440.0, 0.0), root, span(0))
    s, p = route([(VDD_X, BUMP_Y, DOT_Z), (VDD_X, Y_TOP0, DOT_Z), (VDD_X, C.level_y("thin", 0), DOT_Z), (VDD_X, 6.0, DOT_Z)])
    stream_of(root, "current8", 16, s, p, 56, m["c_dot_vdd"], 1, 0.05, 0.60, 150)
    label("huge supply currents", (VDD_X + 170.0, 850.0, 30.0), root, span(1))
    _hot_top(root, m, 2)
    label("Synopsys, Cadence: sign-off", (-900.0, Y_TOP2 + 110.0, 0.0), root, span(2))
    _end("sec8", root, [((0.0, 300.0, 0.0), 4200.0, 0.05, 0.10),
                        ((700.0, 800.0, 0.0), 3500.0, 0.05, 0.10),
                        ((700.0, 800.0, 0.0), 3500.0, 0.05, 0.10)])


def sec9():
    """9 how the top of the stack fails: droop and EM, vias and voids, C4 fatigue."""
    m, root, parts = _begin("sec9", 3)
    _hot_top(root, m, 0)
    _hot_via(root, m, 1)
    _light_bumps(root, m, 2, all_=True)
    label("C4 joints fatigue", (-300.0, BUMP_Y + 170.0, 0.0), root, span(2))
    _end("sec9", root, [((0.0, 1000.0, 0.0), 4200.0, 0.05, 0.10),
                        ((0.0, 1000.0, 0.0), 4200.0, 0.05, 0.10),
                        ((0.0, 1100.0, 0.0), 4200.0, 0.05, 0.10)])


def sec10():
    """10 sources: the whole chip, a slow pull-back, one group of sources lit in turn."""
    m, root, parts = _begin("sec10", 4)
    _light_top(root, m, span(0))
    _rails(root, m, span(1), name="rails10")
    _light_bumps(root, m, 2, all_=True)
    _end("sec10", root, [((0.0, 620.0, 0.0), 4600.0, 0.0, 0.10),
                         ((0.0, 620.0, 0.0), 5000.0, 0.0, 0.10),
                         ((0.0, 620.0, 0.0), 5400.0, 0.0, 0.10),
                         ((0.0, 620.0, 0.0), 5800.0, 0.0, 0.10)])


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
