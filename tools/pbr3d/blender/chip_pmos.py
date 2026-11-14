"""CHIP scenes for the PMOS node: the overview (the whole chip, then in on the PMOS transistor),
the zoom-ins a-e and the numbered sections 1-10. Each is one Blender scene and one GLB.

Run from the repo root, one scene per run (no argument builds the overview):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_pmos.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_pmos.py -- zoom_a
    blender -b --factory-startup --python tools/pbr3d/blender/chip_pmos.py -- sec4

Writes blender/chip_pmos[_<key>].blend and assets/chip_pmos[_<key>].glb. One beat is 8 s.

The PMOS is a p+ source and drain in n-type silicon. It switches ON when its gate is LOW: holes
form a channel under the gate and flow from the VDD side, across the channel, to the output side.
chip_kit only lights the NMOS, so the PMOS gate, channel and holes are built here.

Overview beats:
  0 whole     the whole chip, the PMOS picked out, gate low
  1 low       zoomed in: gate low, the channel of holes forms under the gate
  2 flow      holes run from VDD, across the channel, up to the output
  3 high      gate high: the channel closes, the holes stop, the PMOS is off
  4 pair      pulled back to the pair: gate high, the NMOS on and the PMOS off (one is always off)
  5 whole     back out to the whole chip, the gate low again and the PMOS on

Zoom-ins (3 beats each): a n-well and its tap, b SiGe strain, c the CMOS inverter, d width ratio,
e GAA PFET and germanium. Sections (one scene per `# ` heading of CHIP_PMOS.txt): 1 what happens,
2 the parts, 3 CMOS pairing, 4 standard cell layout, 5 NMOS vs PMOS balance, 6 strain and doping,
7 germanium and GAA, 8 who makes it, 9 chokepoints and risks, 10 sources.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, ball, box, empty, label, mat, overlay, route, show, stream_of, tube  # noqa: E402

BEATS = 6

GATE_HIGH = [(F(3, 0), F(5, 0.2))]  # the shared gate is high: orange on both gates
CHANNEL = [(F(1, 0.35), F(3, 0.05))]  # the hole channel exists while the PMOS is on
HIGHLIGHT = [(F(0, 0), F(1, 0.1)), (F(5, 0.1), F(6, 0))]
WHOLE_TAGS = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
ZOOMED = [(F(1, 0.3), F(4, 0))]
PAIR_TAGS = [(F(4, 0.3), F(5, 0))]

WHOLE = C.WHOLE
ZOOM = ((C.PMOS_X, 150.0, 0.0), 1250.0, 0.0, 0.08)
PAIR = ((0.0, 120.0, 0.0), 3800.0, 0.0, 0.08)
POSES = [WHOLE, ZOOM, ZOOM, ZOOM, PAIR, WHOLE]

# the PMOS: its drain-side contact (x = 510) is the output, its source-side contact (x = 890) is VDD
VDD_SIDE = C.PMOS_X + C.SD
OUT_SIDE = C.PMOS_X - C.SD

# shared camera poses for the close-ups: (target, distance, yaw, pitch)
PMOS_CAM = ((C.PMOS_X, 80.0, 0.0), 1500.0, 0.0, 0.08)
PAIR_CAM = ((0.0, 120.0, 0.0), 3800.0, 0.0, 0.08)
HOLE_PATH = [(VDD_SIDE, 440, 12), (VDD_SIDE, -4, 12), (OUT_SIDE, -4, 12), (OUT_SIDE, 410, 12), (380, 410, 12)]


def build():
    m, root = start("pmos", BEATS, page="chip")
    C.mats(m)
    m["pm_hl"] = mat("chip_pmos_hl", (1.0, 0.45, 0.62), emit=(1.0, 0.40, 0.60), strength=1.0, alpha=0.16)
    m["pm_chan"] = mat("chip_pmos_chan", (1.0, 0.55, 0.20), emit=(1.0, 0.55, 0.20), strength=3.0, alpha=0.75)

    # the whole chip; the NMOS gate follows the same high/low input, as in an inverter
    C.chip(root, m, gate=GATE_HIGH)

    # the PMOS gate: orange while driven high, the same colour the NMOS gate uses
    overlay(root, "pmos_gate_on", (C.PMOS_X - C.GATE_HALF - 6, 14, -246),
            (C.PMOS_X + C.GATE_HALF + 6, 126, 6), m["c_gate_on"], GATE_HIGH)
    # the hole channel: a glowing strip at the silicon surface, in front of the cut, between the S/D
    overlay(root, "pmos_channel", (OUT_SIDE + 70, -6, -236), (VDD_SIDE - 70, 10, 10),
            m["pm_chan"], CHANNEL)
    # the whole-chip highlight around the PMOS
    overlay(root, "pmos_hl", (C.PMOS_X - 330, -140, -250), (C.PMOS_X + 330, 150, 14),
            m["pm_hl"], HIGHLIGHT)

    # holes: from the VDD side down into the source, across the channel, up the drain to the output
    s, p = route([(VDD_SIDE, 440, 12), (VDD_SIDE, -4, 12), (OUT_SIDE, -4, 12),
                  (OUT_SIDE, 410, 12), (380, 410, 12)])
    stream_of(root, "holes", 9, s, p, 40, m["c_dot_vdd"], 2, 0.05, 0.40, 110)

    label("PMOS", (C.PMOS_X, -150.0, 0), root, WHOLE_TAGS)
    label("VDD in", (C.VDD_X, C.BUMP_Y + 110, -60), root, WHOLE_TAGS)
    label("p+ source", (VDD_SIDE, -170.0, 0), root, ZOOMED)
    label("p+ drain", (OUT_SIDE, -170.0, 0), root, ZOOMED)
    label("gate low: PMOS on", (C.PMOS_X, 230.0, 0), root, [(F(1, 0.3), F(2, 0))])
    label("channel: holes", (C.PMOS_X, -60.0, 0), root, CHANNEL)
    label("from VDD", (VDD_SIDE, 480.0, 0), root, [(F(2, 0), F(3, 0))])
    label("holes: VDD to output", (C.PMOS_X, 230.0, 0), root, [(F(2, 0), F(3, 0))])
    label("to the output", (420.0, 470.0, 0), root, [(F(2, 0.2), F(3, 0))])
    label("gate high: PMOS off", (C.PMOS_X, 230.0, 0), root, [(F(3, 0), F(4, 0))])
    label("channel gone", (C.PMOS_X, -60.0, 0), root, [(F(3, 0.1), F(4, 0))])
    label("PMOS off", (C.PMOS_X, -330.0, 0), root, PAIR_TAGS)
    label("NMOS on", (C.NMOS_X, -330.0, 0), root, PAIR_TAGS)
    label("shared gate: high", (0.0, 520.0, 0), root, PAIR_TAGS)
    label("one is always off", (0.0, -560.0, 0), root, PAIR_TAGS)

    C.glide_camera(root, POSES)


# ---- shared pieces for the zooms and sections ---------------------------------------------


def mats_extra(m):
    """Materials the zooms and sections add on top of chip_kit's, all prefixed chip_pmos_."""
    m["pm_hl"] = mat("chip_pmos_hl", (1.0, 0.45, 0.62), emit=(1.0, 0.40, 0.60), strength=1.0, alpha=0.16)
    m["pm_chan"] = mat("chip_pmos_chan", (1.0, 0.55, 0.20), emit=(1.0, 0.55, 0.20), strength=3.0, alpha=0.75)
    m["nwell"] = mat("chip_pmos_nwell", (0.35, 0.55, 1.0), emit=(0.30, 0.50, 1.0), strength=0.8, alpha=0.30)
    m["sige"] = mat("chip_pmos_sige", (1.0, 0.62, 0.55), emit=(1.0, 0.50, 0.45), strength=1.2)
    m["boron"] = mat("chip_pmos_boron", (1.0, 0.85, 0.50), emit=(1.0, 0.80, 0.40), strength=3.0)
    m["si_bar"] = mat("chip_pmos_si", (0.80, 0.82, 0.86), metal=0.1, rough=0.4)
    m["ge"] = mat("chip_pmos_ge", (0.30, 0.90, 0.80), emit=(0.25, 0.90, 0.78), strength=1.5)
    m["wrap"] = mat("chip_pmos_wrap", (0.62, 0.64, 0.74), metal=0.6, rough=0.3, alpha=0.30)
    m["arrow"] = mat("chip_pmos_arrow", (1.0, 0.90, 0.60), emit=(1.0, 0.85, 0.50), strength=3.0)


def pmos_parts(root, m, gate=(), chan=(), hl=()):
    """The PMOS gate (orange while high), its channel (while on) and an optional highlight box."""
    overlay(root, "pmos_gate_on", (C.PMOS_X - C.GATE_HALF - 6, 14, -246),
            (C.PMOS_X + C.GATE_HALF + 6, 126, 6), m["c_gate_on"], list(gate))
    overlay(root, "pmos_channel", (OUT_SIDE + 70, -6, -236), (VDD_SIDE - 70, 10, 10),
            m["pm_chan"], list(chan))


def flow(root, name, pts, mat_, b, u0, u1, life, size=40, n=9):
    """`n` dots along the polyline `pts` (absolute poly points), launched in beat b."""
    s, p = route(pts)
    return stream_of(root, name, n, s, p, size, mat_, b, u0, u1, life)


def arrow(root, m, name, tail, head, intervals):
    """A push arrow: a shaft from `tail` to `head` with a ball tip, shown for `intervals`."""
    g = empty(name, root)
    tube(name + "_shaft", tail, head, 9, m["arrow"], g, verts=10)
    ball(name + "_tip", head, 22, m["arrow"], g, 10)
    show(g, list(intervals))
    return g


def device(root, m, cx, nmos, wf=1.0, sd=None, gate_lit=(), chan_lit=(), name=None):
    """One transistor on its own, drawn as chip_kit does (source and drain, oxide, gate). `wf`
    widens it (more fins or sheets): the source and drain move out by SD * wf."""
    g = empty(name or f"{'nmos' if nmos else 'pmos'}_{cx:.0f}_{wf:.1f}", root)
    half = C.SD * wf
    sdw = 70.0 * wf
    gh = C.GATE_HALF * wf
    sdm = sd or (m["c_nplus"] if nmos else m["c_pplus"])
    for sgn in (-1, 1):
        x = cx + sgn * half
        box(f"sd{sgn}", (x - sdw, -90, -240), (x + sdw, 6, 0), sdm, g)
    box("hik", (cx - gh - 8, 0, -240), (cx + gh + 8, 14, 0), m["c_oxide"], g)
    box("gate", (cx - gh, 14, -240), (cx + gh, 120, 0), m["c_gate"], g)
    if gate_lit:
        overlay(g, "gate_on", (cx - gh - 6, 14, -246), (cx + gh + 6, 126, 6), m["c_gate_on"], list(gate_lit))
    if chan_lit:
        inner = half - sdw
        chan = m["c_chan"] if nmos else m["pm_chan"]
        overlay(g, "chan_on", (cx - inner, -8, -20), (cx + inner, 10, 10), chan, list(chan_lit))
    return g


def highlight(root, m, name, lo, hi, intervals):
    overlay(root, name, lo, hi, m["pm_hl"], list(intervals))


# ---- zoom-ins ---------------------------------------------------------------------------------

ZA_POSES = [
    ((C.PMOS_X + 200.0, 80.0, 0.0), 1500.0, 0.0, 0.08),
    ((1000.0, 80.0, 0.0), 1800.0, 0.0, 0.08),
    ((C.PMOS_X + 200.0, 80.0, 0.0), 1500.0, 0.0, 0.08),
]


def zoom_a(m, root):
    """a the n-well and its tap: the well around the PMOS, tied to VDD, and the channel only."""
    C.silicon(root, m)
    overlay(root, "nwell", (C.PMOS_X - 330, -260, -240), (C.PMOS_X + 560, -2, 8), m["nwell"],
            [(F(0, 0), F(3, 0))])
    device(root, m, C.PMOS_X, False, chan_lit=[(F(2, 0.2), F(3, 0))])
    # the n+ tap at the right-hand edge of the well, plugged up to thin metal (VDD)
    box("tap_n", (1150, -90, -240), (1250, 6, 0), m["c_nplus"], root)
    tube("tap_plug", (1200, 6, -60), (1200, C.level_y("thin", 0), -60), 28, m["c_w"], root, verts=10)
    label("n-well under the PMOS", (C.PMOS_X - 200.0, 200.0, 0), root, [(F(0, 0), F(1, 0))])
    label("tap ties the well to VDD", (1200.0, 200.0, 0), root, [(F(1, 0), F(2, 0))])
    label("n+ tap", (1200.0, -130.0, 0), root, [(F(1, 0), F(2, 0))])
    label("only the channel conducts", (C.PMOS_X, 200.0, 0), root, [(F(2, 0), F(3, 0))])


ZB_POSES = [PMOS_CAM, PMOS_CAM, PMOS_CAM]


def sige_strain(m, root, b_beat=0):
    """SiGe source and drain, the squeeze arrows and holes moving faster. Used by zoom b and
    section 6."""
    C.silicon(root, m)
    cx = C.PMOS_X
    half, sdw = C.SD, 70.0
    device(root, m, cx, False, sd=m["sige"], chan_lit=[(F(1, 0.3), F(3, 0))])
    # boron atoms in front of the regrown source and drain, shown while they are grown in
    g = empty("boron", root)
    for x in (cx - half - 30, cx - half + 30, cx + half - 30, cx + half + 30):
        for y in (-70.0, -30.0):
            ball(f"boron_{x:.0f}_{y:.0f}", (x, y, 25.0), 14, m["boron"], g, 8)
    show(g, [(F(0, 0), F(2, 0))])
    # squeeze arrows pressing in from both sides, in front of the source and drain
    for side in (-1, 1):
        outer = cx + side * (half + sdw)
        for y in (-60.0, -20.0):
            arrow(root, m, f"squeeze_{side}_{y:.0f}", (outer + side * 90.0, y, 30.0),
                  (outer - side * 60.0, y, 30.0), [(F(1, 0), F(2, 0))])
    label("SiGe:B source and drain", (cx, 200.0, 0), root, [(F(0, 0), F(1, 0))])
    label("SiGe squeezes the channel", (cx, 200.0, 0), root, [(F(1, 0), F(2, 0))])
    label("faster holes", (cx, 200.0, 0), root, [(F(2, 0), F(3, 0))])
    flow(root, "holes_fast", [(cx + half, 200, 12), (cx + half, -4, 12), (cx - half, -4, 12),
                              (cx - half, 200, 12)], m["c_dot_vdd"], 2, 0.05, 0.5, 60)


def zoom_b(m, root):
    """b SiGe strain: the regrown source and drain squeeze the channel, and holes move faster."""
    sige_strain(m, root)


ZC_POSES = [PAIR_CAM, PAIR_CAM, PAIR_CAM]


def inverter(m, root, idle_tags=True):
    """The CMOS pair: the PMOS (pull-up) and NMOS (pull-down) with the shared input. Beat 0 is
    idle, beat 1 input low (PMOS on, output high), beat 2 input high (NMOS on, output low)."""
    hi2 = [(F(2, 0), F(3, 0))]
    C.chip(root, m, gate=hi2)
    pmos_parts(root, m, gate=hi2, chan=[(F(1, 0.3), F(2, 0))])
    flow(root, "holes_out", HOLE_PATH, m["c_dot_vdd"], 1, 0.05, 0.4, 110)
    flow(root, "electrons_out", [(-510, 410, 12), (-510, -4, 12), (-890, -4, 12), (-890, 440, 12)],
         m["c_dot_gnd"], 2, 0.1, 0.6, 100)
    if idle_tags:
        label("PMOS: pull-up to VDD", (C.PMOS_X, -330.0, 0), root, [(F(0, 0), F(1, 0))])
        label("NMOS: pull-down to ground", (C.NMOS_X, -330.0, 0), root, [(F(0, 0), F(1, 0))])
    label("input 0: PMOS on", (C.PMOS_X, 230.0, 0), root, [(F(1, 0), F(2, 0))])
    label("output high", (420.0, 470.0, 0), root, [(F(1, 0), F(2, 0))])
    label("input 1: NMOS on", (C.NMOS_X, 230.0, 0), root, [(F(2, 0), F(3, 0))])
    label("output low", (-420.0, 470.0, 0), root, [(F(2, 0), F(3, 0))])


def zoom_c(m, root):
    """c the CMOS inverter: PMOS pulls up, NMOS pulls down, one of them on at a time."""
    inverter(m, root)


ZD_POSES = [((190.0, 80.0, 0.0), 3500.0, 0.0, 0.08)] * 3


def width_ratio(m, root):
    """d (and section 5) width ratio: holes are slow, so the PMOS is drawn wider (more fins)."""
    C.silicon(root, m)
    cx_n, cx_p = C.NMOS_X, C.PMOS_X
    device(root, m, cx_n, True, name="nmos_narrow")
    narrow = device(root, m, cx_p, False, wf=1.0, name="pmos_narrow")
    show(narrow, [(F(0, 0), F(1, 0))])
    wide = device(root, m, cx_p, False, wf=2.2, chan_lit=[(F(1, 0), F(3, 0))], name="pmos_wide")
    show(wide, [(F(1, 0), F(3, 0))])
    # fins: the NMOS has 2, the PMOS 3 once it is wide
    fins = empty("fins", root)
    for x in (cx_n - 100, cx_n + 100):
        box(f"fin_n_{x:.0f}", (x - 22, 0, 20), (x + 22, 150, 50), m["si_bar"], fins)
    for x in (cx_p - 200, cx_p, cx_p + 200):
        box(f"fin_p_{x:.0f}", (x - 22, 0, 20), (x + 22, 150, 50), m["si_bar"], fins)
    show(fins, [(F(2, 0), F(3, 0))])
    label("mu_p ~450: holes slow", (cx_p, 230.0, 0), root, [(F(0, 0), F(1, 0))])
    label("mu_n ~1400: electrons fast", (cx_n, 230.0, 0), root, [(F(0, 0), F(1, 0))])
    label("PMOS made 2.2x wider", (cx_p, 230.0, 0), root, [(F(1, 0), F(2, 0))])
    label("Wp/Wn ~2-2.5", (190.0, 330.0, 0), root, [(F(1, 0), F(3, 0))])
    label("fins: 2 NMOS, 3 PMOS", (190.0, 330.0, 0), root, [(F(2, 0), F(3, 0))])
    flow(root, "holes_slow", [(cx_p + C.SD, 200, 12), (cx_p + C.SD, -4, 12), (cx_p - C.SD, -4, 12),
                              (cx_p - C.SD, 200, 12)], m["c_dot_vdd"], 0, 0.05, 0.5, 220)
    flow(root, "electrons_fast", [(cx_n + C.SD, 200, 12), (cx_n + C.SD, -4, 12), (cx_n - C.SD, -4, 12),
                                  (cx_n - C.SD, 200, 12)], m["c_dot_gnd"], 0, 0.1, 0.6, 60)
    flow(root, "holes_wide", [(cx_p + 418, 200, 12), (cx_p + 418, -4, 12), (cx_p - 418, -4, 12),
                              (cx_p - 418, 200, 12)], m["c_dot_vdd"], 1, 0.05, 0.5, 110)


ZE_POSES = [((C.PMOS_X, 150.0, 0.0), 1400.0, 0.0, 0.08)] * 3
SHEET_Y = (40.0, 120.0, 200.0)


def sheet_group(root, cx, name, mat_, intervals):
    g = empty(name, root)
    for y0 in SHEET_Y:
        box(f"{name}_{y0:.0f}", (cx - 250, y0, -150), (cx + 250, y0 + 36, -60), mat_, g)
    show(g, list(intervals))
    return g


def gaa(m, root):
    """e (and section 7) GAA PFET and germanium: a stack of sheets wrapped by the gate, first
    silicon, then SiGe under strain, then germanium with holes running along the sheets."""
    C.silicon(root, m)
    cx = C.PMOS_X
    for sgn in (-1, 1):
        x = cx + sgn * 300.0
        box(f"sd{sgn}", (x - 40, -90, -240), (x + 40, 260, 0), m["c_pplus"], root)
    sheet_group(root, cx, "sheets_si", m["si_bar"], [(F(0, 0), F(1, 0))])
    sheet_group(root, cx, "sheets_sige", m["sige"], [(F(1, 0), F(2, 0))])
    sheet_group(root, cx, "sheets_ge", m["ge"], [(F(2, 0), F(3, 0))])
    box("gate_wrap", (cx - 170, 20, -170), (cx + 170, 250, -40), m["wrap"], root)
    for y0 in SHEET_Y:
        arrow(root, m, f"press_{y0:.0f}", (cx + 340, y0 + 18, 20), (cx + 270, y0 + 18, 20),
              [(F(1, 0), F(2, 0))])
        flow(root, f"holes_sheet_{y0:.0f}", [(cx - 250, y0 + 18, 20), (cx + 250, y0 + 18, 20)],
             m["c_dot_vdd"], 2, 0.05, 0.6, 80, size=30, n=9)
    label("PMOS sheets, gate wraps them", (cx, 300.0, 0), root, [(F(0, 0), F(1, 0))])
    label("SiGe sheets: ~1 GPa", (cx, 300.0, 0), root, [(F(1, 0), F(2, 0))])
    label("Ge: ~1900 cm2/Vs", (cx, 300.0, 0), root, [(F(2, 0), F(3, 0))])


# ---- numbered sections --------------------------------------------------------------------------

S1_POSES = [PMOS_CAM, PMOS_CAM, PAIR_CAM]


def sec1(m, root):
    """1 what happens: the PMOS off (gate high), on (gate low, holes flow), then paired."""
    hi0 = [(F(0, 0), F(1, 0))]
    C.chip(root, m, gate=hi0)
    pmos_parts(root, m, gate=hi0, chan=[(F(1, 0), F(2, 0))])
    flow(root, "holes_s1", HOLE_PATH, m["c_dot_vdd"], 1, 0.05, 0.4, 110)
    label("PMOS: gate high, off", (C.PMOS_X, 230.0, 0), root, hi0)
    label("gate low: holes flow", (C.PMOS_X, 230.0, 0), root, [(F(1, 0), F(2, 0))])
    label("paired with an NMOS", (0.0, 520.0, 0), root, [(F(2, 0), F(3, 0))])


S2_POSES = [PMOS_CAM] * 5


def sec2(m, root):
    """2 the parts: source, channel, drain, gate and the n-well, each lit in turn."""
    C.chip(root, m)
    pmos_parts(root, m, gate=[(F(3, 0), F(4, 0))], chan=[(F(1, 0), F(2, 0))])
    highlight(root, m, "hl_source", (VDD_SIDE - 90, -100, -250), (VDD_SIDE + 90, 14, 10), [(F(0, 0), F(1, 0))])
    label("p+ source: SiGe:B", (VDD_SIDE, -170.0, 0), root, [(F(0, 0), F(1, 0))])
    label("PMOS channel: holes", (C.PMOS_X, 230.0, 0), root, [(F(1, 0), F(2, 0))])
    highlight(root, m, "hl_drain", (OUT_SIDE - 90, -100, -250), (OUT_SIDE + 90, 14, 10), [(F(2, 0), F(3, 0))])
    label("p+ drain: the output", (OUT_SIDE, -170.0, 0), root, [(F(2, 0), F(3, 0))])
    label("PMOS gate: high-k metal", (C.PMOS_X, 230.0, 0), root, [(F(3, 0), F(4, 0))])
    overlay(root, "nwell_s2", (C.PMOS_X - 330, -260, -240), (C.PMOS_X + 560, -2, 8), m["nwell"],
            [(F(4, 0), F(5, 0))])
    label("n-well tied to VDD", (C.PMOS_X + 200.0, 230.0, 0), root, [(F(4, 0), F(5, 0))])


S3_POSES = ZC_POSES


def sec3(m, root):
    """3 CMOS pairing: the inverter at rest, input low, input high."""
    inverter(m, root)


S4_POSES = [PAIR_CAM, PAIR_CAM, WHOLE]


def sec4(m, root):
    """4 standard cell layout: the pair as one cell, its rails along the thin metal, then tap
    cells and rows across the chip."""
    C.chip(root, m)
    label("standard cell: PMOS over NMOS", (0.0, -330.0, 0), root, [(F(0, 0), F(1, 0))])
    overlay(root, "rails_hl", (-1450, C.THIN[0] + 10, -110), (1450, C.THIN[1] - 10, -20), m["pm_hl"],
            [(F(1, 0), F(2, 0))])
    label("rails: Vdd and ground", (-300.0, C.THIN[1] + 90.0, 0), root, [(F(1, 0), F(2, 0))])
    label("tap cells tie the wells to rails", (0.0, C.BUMP_Y + 150.0, 0), root, [(F(2, 0), F(3, 0))])


S5_POSES = ZD_POSES


def sec5(m, root):
    """5 NMOS vs PMOS balance: width ratio, fins."""
    width_ratio(m, root)


S6_POSES = ZB_POSES


def sec6(m, root):
    """6 strain and doping: SiGe source and drain, squeezed channel, boron."""
    sige_strain(m, root)


S7_POSES = ZE_POSES


def sec7(m, root):
    """7 germanium channels and GAA PMOS: sheets, SiGe, germanium."""
    gaa(m, root)


S8_POSES = [WHOLE, PAIR_CAM, PAIR_CAM]


def sec8(m, root):
    """8 who makes it: the foundries, the epi tools, the design tools."""
    C.chip(root, m)
    label("TSMC, Intel, Samsung", (0.0, C.BUMP_Y + 150.0, 0), root, [(F(0, 0), F(1, 0))])
    label("epitaxy: Applied Materials", (C.PMOS_X, 230.0, 0), root, [(F(1, 0), F(2, 0))])
    label("cells: Synopsys, Cadence, Arm", (0.0, 470.0, 0), root, [(F(2, 0), F(3, 0))])


S9_POSES = [PMOS_CAM, PMOS_CAM, PMOS_CAM]


def sec9(m, root):
    """9 chokepoints and risks: slow holes, boron into the channel, few epi tool vendors."""
    C.chip(root, m)
    pmos_parts(root, m, chan=[(F(0, 0), F(1, 0))])
    flow(root, "holes_slow9", HOLE_PATH, m["c_dot_vdd"], 0, 0.05, 0.5, 220)
    label("holes: the weaker carrier", (C.PMOS_X, 230.0, 0), root, [(F(0, 0), F(1, 0))])
    flow(root, "boron_drift", [(OUT_SIDE, 60, 12), (OUT_SIDE, -4, 12), (C.PMOS_X, -4, 12)],
         m["boron"], 1, 0.05, 0.6, 110, size=30, n=9)
    label("boron drifts into the channel", (C.PMOS_X, 230.0, 0), root, [(F(1, 0), F(2, 0))])
    highlight(root, m, "hl_epi", (VDD_SIDE - 90, -100, -250), (OUT_SIDE + 90, 14, 10), [(F(2, 0), F(3, 0))])
    label("few epi tool vendors", (C.PMOS_X, 230.0, 0), root, [(F(2, 0), F(3, 0))])


S10_POSES = [
    ((0.0, 620.0, 0.0), 5000.0, 0.0, 0.10),
    ((0.0, 620.0, 0.0), 5800.0, 0.0, 0.10),
    ((0.0, 700.0, 0.0), 6600.0, 0.0, 0.10),
    WHOLE,
]


def sec10(m, root):
    """10 sources: the whole chip pulls back while each beat names its sources."""
    C.chip(root, m)
    label("[1][2] Intel 90 nm, VLSI 2004", (0.0, C.BUMP_Y + 150.0, 0), root, [(F(0, 0), F(1, 0))])
    label("[3] IBM SiGe nanosheet pFET", (0.0, C.BUMP_Y + 150.0, 0), root, [(F(1, 0), F(2, 0))])
    label("[4][5] UCSB lecture, Applied", (0.0, C.BUMP_Y + 150.0, 0), root, [(F(2, 0), F(3, 0))])
    label("[6][7][8] USPTO, ASAP7, cells", (0.0, C.BUMP_Y + 150.0, 0), root, [(F(3, 0), F(4, 0))])


# ---- registry and entry point ----------------------------------------------------------------

# key -> (beats, camera poses, builder)
SCENES = {
    "zoom_a": (3, ZA_POSES, zoom_a),
    "zoom_b": (3, ZB_POSES, zoom_b),
    "zoom_c": (3, ZC_POSES, zoom_c),
    "zoom_d": (3, ZD_POSES, width_ratio),
    "zoom_e": (3, ZE_POSES, gaa),
    "sec1": (3, S1_POSES, sec1),
    "sec2": (5, S2_POSES, sec2),
    "sec3": (3, S3_POSES, sec3),
    "sec4": (3, S4_POSES, sec4),
    "sec5": (3, S5_POSES, sec5),
    "sec6": (3, S6_POSES, sec6),
    "sec7": (3, S7_POSES, sec7),
    "sec8": (3, S8_POSES, sec8),
    "sec9": (3, S9_POSES, sec9),
    "sec10": (4, S10_POSES, sec10),
}


def scene(key):
    beats, poses, fn = SCENES[key]
    name = f"pmos_{key}"
    m, root = start(name, beats, page="chip")
    C.mats(m)
    mats_extra(m)
    fn(m, root)
    C.glide_camera(root, poses)
    finish(name, page="chip")


if __name__ == "__main__":
    key = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "overview"
    if key == "overview":
        build()
        finish("pmos", page="chip")
    else:
        scene(key)
