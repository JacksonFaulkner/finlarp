"""CHIP overview for the GATE-ALL-AROUND node: the whole chip, then in on the nanosheet stack.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/chip_gaa.py [-- a 3 sec5]

With no arguments it writes everything: the overview (blender/chip_gaa.blend, assets/chip_gaa.glb),
zoom-ins a-e (assets/chip_gaa_zoom_<key>.glb) and sections 1-10 (assets/chip_gaa_sec<N>.glb).
Named arguments after `--` pick scenes: `overview`, `a`..`e`, or a section number.

One beat is 8 s. The chip is built from chip_kit's parts (silicon, contacts, wiring, bumps, and the
planar PMOS), not chip(): the NMOS spot at chip_kit.NMOS_X gets this node's gate-all-around stack
instead of a planar device. Sheets run source to drain along x, stacked up y; the cut plane is
z = 0, so the sheet width is its depth along z.

Overview beats:
  0 whole     the whole chip, the GAA transistor at the NMOS spot picked out
  1 stack     in on the transistor: raised source and drain epi, three nanosheets between them
  2 wrap      the gate turns on and wraps the top, bottom and both faces of every sheet
  3 current   carriers stream from source to drain through every sheet at once
  4 wide      a wide sheet: more channel area under the gate, more drive current
  5 narrow    a narrow sheet: less area and leakage, less drive current
  6 whole     back out to the whole chip, the highlight glows once more (loops to beat 0)

Zoom-ins (the process flow, release, sheet width, backside power, roadmap) and sections 1-10 are
built below from the same helpers; they are listed in the page's zoom and section data.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, scale_keys, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, box, empty, label, overlay, pivot, rel, route, show, stream_of, tube  # noqa: E402
from sand_overview import disc, mat  # noqa: E402

BEATS = 7

CX = C.NMOS_X  # the GAA transistor sits where the planar NMOS was
GATE_HALF = C.GATE_HALF  # the gate runs cx +- 100
INNER = 120.0  # sheets and inner spacers meet the raised epi this far from cx
EPI_OUT = 260.0  # outer face of the raised source and drain
EPI_BOT, EPI_TOP = -90.0, 112.0  # the epi rises past the top sheet, so every sheet lands on it
GATE_LO, GATE_HI = 14.0, 120.0  # the gate stack, same bottom and top as the planar gate
OX = 3.0  # high-k thickness on each sheet face
SHEETS = [(28.0, 40.0), (62.0, 74.0), (96.0, 108.0)]  # (lo, hi) of each nanosheet, bottom to top
GAPS = [(GATE_LO, 28.0), (40.0, 62.0), (74.0, 96.0), (108.0, GATE_HI)]  # gate fill between sheets
DEPTH = -240.0  # the gate and epi run behind the cut plane, as in chip_kit
WIDTH = {"mid": 120.0, "wide": 200.0, "narrow": 60.0}  # sheet width along z
FIN_Z = (-40.0, -120.0, -200.0)  # FinFET fin centres along z, 80 apart

WHOLE = C.WHOLE
ZOOM = ((CX, 60.0, 0.0), 1100.0, 0.0, 0.10)  # square on the stack, front view
ZOOM_SIDE = ((CX, 60.0, 0.0), 1100.0, 0.55, 0.20)  # turned so the sheet width shows in depth
ZOOM_TOP = ((CX, 700.0, 0.0), 2400.0, 0.0, 0.10)  # the stack and the wiring above it
ZOOM_LOW = ((CX, -200.0, 0.0), 1800.0, 0.0, -0.25)  # under the substrate, the rails
ZOOM_OUT = ((CX, 60.0, 0.0), 2400.0, 0.0, 0.10)  # two devices side by side
POSES = [WHOLE, ZOOM, ZOOM, ZOOM, ZOOM_SIDE, ZOOM_SIDE, WHOLE]

GATE_ON = [(F(2, 0.10), F(6, 0.0))]
WRAP_ON = [(F(2, 0.10), F(4, 0.0))]
CHAN_ON = [(F(3, 0.05), F(4, 0.0))]
HL_ON = [(F(0, 0), F(1, 0)), (F(6, 0.1), F(7, 0))]
WHOLE_TAGS = [(F(0, 0), F(1, 0)), (F(6, 0), F(7, 0))]
MID_ON = [(F(0, 0), F(4, 0)), (F(6, 0), F(7, 0))]  # mid-width sheets: the default, and the loop
WIDE_ON = [(F(4, 0), F(5, 0))]
NARROW_ON = [(F(5, 0), F(6, 0))]


def mats(m):
    m["g_sheet"] = mat("chip_gaa_sheet", (0.80, 0.88, 0.94), metal=0.1, rough=0.25)
    m["g_spacer"] = mat("chip_gaa_spacer", (0.62, 0.76, 0.66), rough=0.5)
    m["g_wrap"] = mat("chip_gaa_wrap", (0.45, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.2, alpha=0.22)
    m["g_chan"] = mat("chip_gaa_chan", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.0, alpha=0.5)
    m["g_hl"] = mat("chip_gaa_hl", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.16)
    m["g_sige"] = mat("chip_gaa_sige", (0.62, 0.42, 0.78), rough=0.6)
    m["g_dummy"] = mat("chip_gaa_dummy", (0.55, 0.58, 0.66), rough=0.4, alpha=0.3)
    m["g_wall"] = mat("chip_gaa_wall", (0.50, 0.56, 0.72), rough=0.5)
    m["g_wafer"] = mat("chip_gaa_wafer", (0.72, 0.74, 0.78), metal=0.4, rough=0.4)
    m["g_plinth"] = mat("chip_gaa_plinth", (0.30, 0.32, 0.38), rough=0.8)
    m["g_card"] = mat("chip_gaa_card", (0.93, 0.92, 0.88), rough=0.8)
    m["g_card_on"] = mat("chip_gaa_card_on", (1.0, 0.82, 0.40), emit=(1.0, 0.78, 0.30), strength=2.0)


def epi(root, m, cx=CX, dy=0.0):
    """Raised source and drain: n+ blocks either side of the stack, up past the top sheet."""
    g = empty("gaa_epi", root)
    for sgn in (-1, 1):
        x0, x1 = (cx - EPI_OUT, cx - INNER) if sgn < 0 else (cx + INNER, cx + EPI_OUT)
        box(f"epi{sgn:+d}", (x0, EPI_BOT + dy, DEPTH), (x1, EPI_TOP + dy, 0.0), m["c_nplus"], g)
    return g


def gate(root, m, cx=CX, dy=0.0):
    """The gate fill: metal in every gap between the sheets (and under the lowest, above the
    substrate), a high-k skin on each sheet face and the inner spacers at both ends."""
    g = empty("gaa_gate", root)
    x0, x1 = cx - GATE_HALF, cx + GATE_HALF
    box("hik_base", (x0 - 8, dy, DEPTH), (x1 + 8, GATE_LO + dy, 0.0), m["c_oxide"], g)
    for k, (lo, hi) in enumerate(GAPS):
        y0 = lo if lo == GATE_LO else lo + OX
        y1 = hi if hi == GATE_HI else hi - OX
        box(f"gate{k}", (x0, y0 + dy, DEPTH), (x1, y1 + dy, 0.0), m["c_gate"], g)
        if lo != GATE_LO:
            box(f"hik_lo{k}", (x0, lo + dy, DEPTH), (x1, lo + OX + dy, 0.0), m["c_oxide"], g)
        if hi != GATE_HI:
            box(f"hik_hi{k}", (x0, hi - OX + dy, DEPTH), (x1, hi + dy, 0.0), m["c_oxide"], g)
        for sgn in (-1, 1):
            xa, xb = (cx - INNER, x0) if sgn < 0 else (x1, cx + INNER)
            box(f"spacer{k}{sgn:+d}", (xa, lo + dy, DEPTH), (xb, hi + dy, 0.0), m["g_spacer"], g)
    return g


def sheets(root, m, name, w, intervals, cx=CX, dy=0.0):
    """The three nanosheets at width `w`, each with its gate behind it (the wrap along z)."""
    g = empty(f"gaa_sheets_{name}", root)
    show(g, intervals)
    for i, (lo, hi) in enumerate(SHEETS):
        box(f"{name}_sheet{i}", (cx - INNER, lo + dy, -w), (cx + INNER, hi + dy, 0.0), m["g_sheet"], g)
        box(f"{name}_back{i}", (cx - GATE_HALF, lo + dy, -w - 14.0), (cx + GATE_HALF, hi + dy, -w), m["c_gate"], g)
    return g


def wrap(root, m, name, w, intervals, cx=CX, dy=0.0):
    """A translucent shell round each sheet: the gate on all four sides, at width `w`."""
    g = empty(f"gaa_wrap_{name}", root)
    show(g, intervals)
    for i, (lo, hi) in enumerate(SHEETS):
        box(f"{name}_shell{i}", (cx - INNER - 6, lo - 6 + dy, -w - 18), (cx + INNER + 6, hi + 6 + dy, 6.0), m["g_wrap"], g)
    return g


def build():
    m, root = start("gaa", BEATS, page="chip")
    C.mats(m)
    mats(m)

    # the whole chip, from chip_kit's parts; the NMOS spot is the GAA stack built below
    C.silicon(root, m)
    C.transistor(root, m, C.PMOS_X, False)
    C.contacts(root, m)
    C.wiring(root, m)
    C.bumps(root, m)

    epi(root, m)
    gate(root, m)
    sheets(root, m, "mid", WIDTH["mid"], MID_ON)
    sheets(root, m, "wide", WIDTH["wide"], WIDE_ON)
    sheets(root, m, "narrow", WIDTH["narrow"], NARROW_ON)

    # the gate turns on: amber on the metal, the shell round each sheet
    for k, (lo, hi) in enumerate(GAPS):
        overlay(root, f"gate_on{k}", (CX - GATE_HALF - 6, lo, DEPTH - 6), (CX + GATE_HALF + 6, hi, 6.0), m["c_gate_on"], GATE_ON)
    wrap(root, m, "mid", WIDTH["mid"], WRAP_ON)
    wrap(root, m, "wide", WIDTH["wide"], [(F(4, 0), F(5, 0))])
    wrap(root, m, "narrow", WIDTH["narrow"], [(F(5, 0), F(6, 0))])

    # the current: each sheet glows and carries a stream of carriers source to drain
    for i, (lo, hi) in enumerate(SHEETS):
        overlay(root, f"chan{i}", (CX - INNER, lo - 2, -WIDTH["mid"] - 2), (CX + INNER, hi + 2, 6.0), m["g_chan"], CHAN_ON)
        yc = (lo + hi) / 2
        s, p = route([(CX - INNER, yc, 12.0), (CX + INNER, yc, 12.0)])
        stream_of(root, f"elec{i}", 9, s, p, 12, m["c_dot_sig"], 3, 0.05, 0.75, 80)

    # the highlight on the GAA transistor in the whole-chip views
    overlay(root, "gaa_hl", (CX - 330, -140, -250), (CX + 330, 150, 14), m["g_hl"], HL_ON)

    label("GAA transistor", (CX, -150.0, 0), root, WHOLE_TAGS)
    label("source epi", (CX - 190, 150.0, 0), root, [(F(1, 0.3), F(6, 0))])
    label("drain epi", (CX + 190, 150.0, 0), root, [(F(1, 0.3), F(6, 0))])
    label("3 nanosheets", (CX - 330, 74.0, 0), root, [(F(1, 0.3), F(6, 0))])
    label("gate metal", (CX - 60, 165.0, 0), root, [(F(1, 0.3), F(2, 0.1))])
    label("gate on: four sides", (CX, 200.0, 0), root, [(F(2, 0.2), F(6, 0))])
    label("carriers: source to drain", (CX, -60.0, 0), root, [(F(3, 0.05), F(4, 0))])
    label("wide sheet: more drive", (CX + 330, 200.0, 0), root, [(F(4, 0.1), F(5, 0))])
    label("narrow sheet: less leakage", (CX + 330, 200.0, 0), root, [(F(5, 0.1), F(6, 0))])

    C.glide_camera(root, POSES)


# ---- parts for the zoom-ins and sections ------------------------------------------------------


def begin(name, beats):
    """A fresh scene: the chip's materials and this node's, under a root named after `name`."""
    m, root = start(name, beats, page="chip")
    C.mats(m)
    mats(m)
    return m, root


def base(root, m):
    """The chip around the node: silicon, PMOS, contacts, wiring and bumps (the NMOS spot is the GAA)."""
    C.silicon(root, m)
    C.transistor(root, m, C.PMOS_X, False)
    C.contacts(root, m)
    C.wiring(root, m)
    C.bumps(root, m)


def si_sheets(root, m, w, intervals, cx=CX, dy=0.0):
    """The three silicon sheets alone, before any gate (the superlattice and release steps)."""
    g = empty("gaa_si", root)
    show(g, intervals)
    for i, (lo, hi) in enumerate(SHEETS):
        box(f"si_sheet{i}", (cx - INNER, lo + dy, -w), (cx + INNER, hi + dy, 0.0), m["g_sheet"], g)
    return g


def sige(root, m, w, intervals, cx=CX, dy=0.0, shrink=None):
    """The four sacrificial SiGe layers in the gaps. Each is built about its own centre, so the
    `shrink` scale keys can etch it back from both ends."""
    g = empty("gaa_sige", root)
    show(g, intervals)
    for k, (lo, hi) in enumerate(GAPS):
        y0, y1 = lo + dy, hi + dy
        at = (cx, (y0 + y1) / 2, -w / 2)
        pv = pivot(f"sige{k}", at, g)
        box(f"sige{k}_bar", rel(at, (cx - INNER, y0, -w)), rel(at, (cx + INNER, y1, 0.0)), m["g_sige"], pv)
        if shrink:
            scale_keys(pv, shrink)
    return g


def spacers(root, m, intervals, cx=CX, dy=0.0):
    """Inner spacers alone: nitride at both ends of each gap, between the future gate and the epi."""
    g = empty("gaa_spacers", root)
    show(g, intervals)
    for k, (lo, hi) in enumerate(GAPS):
        for sgn in (-1, 1):
            xa, xb = (cx - INNER, cx - GATE_HALF) if sgn < 0 else (cx + GATE_HALF, cx + INNER)
            box(f"inner{k}{sgn:+d}", (xa, lo + dy, DEPTH), (xb, hi + dy, 0.0), m["g_spacer"], g)
    return g


def dummy(root, m, intervals, cx=CX, dy=0.0):
    """The placeholder gate of the replacement-gate flow: translucent, over the channel."""
    g = empty("gaa_dummy", root)
    show(g, intervals)
    box("dummy_gate", (cx - GATE_HALF, GATE_LO + dy, DEPTH), (cx + GATE_HALF, GATE_HI + dy, 0.0), m["g_dummy"], g)
    return g


def device(root, m, name, intervals, cx=CX, dy=0.0, w=WIDTH["mid"]):
    """A whole GAA device at `cx`, `dy` up: the epi, three sheets and the gate with its spacers."""
    show(epi(root, m, cx, dy), intervals)
    sheets(root, m, name, w, intervals, cx, dy)
    show(gate(root, m, cx, dy), intervals)


def fins(root, m, intervals, count=3, cx=CX):
    """FinFET: `count` whole fins, each with gate metal on its top and both sides."""
    g = empty("gaa_fins", root)
    show(g, intervals)
    for i, zc in enumerate(FIN_Z[:count]):
        box(f"fin{i}", (cx - INNER, GATE_LO, zc - 20.0), (cx + INNER, 120.0, zc + 20.0), m["g_sheet"], g)
        box(f"fin{i}_front", (cx - GATE_HALF, GATE_LO, zc + 20.0), (cx + GATE_HALF, 120.0, zc + 26.0), m["c_gate"], g)
        box(f"fin{i}_back", (cx - GATE_HALF, GATE_LO, zc - 26.0), (cx + GATE_HALF, 120.0, zc - 20.0), m["c_gate"], g)
    box("fin_top_gate", (cx - GATE_HALF, 120.0, FIN_Z[count - 1] - 26.0), (cx + GATE_HALF, 140.0, 0.0), m["c_gate"], g)
    return g


def current(root, m, b, tag="", cx=CX, dy=0.0, w=WIDTH["mid"]):
    """Carriers in beat `b`: a glowing channel in each sheet and dots from source to drain."""
    for i, (lo, hi) in enumerate(SHEETS):
        overlay(root, f"chan{tag}{i}", (cx - INNER, lo + dy - 2, -w - 2), (cx + INNER, hi + dy + 2, 6.0),
                m["g_chan"], [(F(b, 0.05), F(b + 1, 0))])
        yc = (lo + hi) / 2 + dy
        s, p = route([(cx - INNER, yc, 12.0), (cx + INNER, yc, 12.0)])
        stream_of(root, f"elec{tag}{i}", 9, s, p, 12, m["c_dot_sig"], b, 0.05, 0.75, 80)


def rails(root, m, intervals):
    """Backside power: two rails under the substrate and a nano-TSV up to each device contact."""
    g = empty("gaa_rails", root)
    show(g, intervals)
    box("rail_vss", (-1100.0, -380.0, -100.0), (0.0, -340.0, -20.0), m["c_w"], g)
    box("rail_vdd", (0.0, -380.0, -100.0), (1100.0, -340.0, -20.0), m["c_cu_top"], g)
    tube("tsv_vss", (CX, -340.0, -60.0), (CX, 6.0, -60.0), 14, m["c_w"], g, verts=8)
    tube("tsv_vdd", (C.PMOS_X, -340.0, -60.0), (C.PMOS_X, 6.0, -60.0), 14, m["c_cu_top"], g, verts=8)
    return g


def rail_dots(root, m, b):
    """Power dots in beat `b`, rising through the TSV from the VDD rail to the PMOS."""
    s, p = route([(C.PMOS_X, -360.0, -60.0), (C.PMOS_X, 6.0, -60.0)])
    stream_of(root, "rail_vdd_dots", 9, s, p, 46, m["c_dot_vdd"], b, 0.10, 0.60, 90)


def finish_as(name):
    finish(name, page="chip")


# ---- zoom-ins a-e -----------------------------------------------------------------------------


def zoom_a():
    """a, the process flow: superlattice; dummy gate, inner spacer and S/D epi; the release and the
    real gate. Three beats."""
    m, root = begin("gaa_zoom_a", 3)
    base(root, m)
    sige(root, m, WIDTH["mid"], [(F(0, 0), F(2, 0))], shrink=[(F(1, 0), (1, 1, 1)), (F(1, 0.6), (0.83, 1, 1))])
    si_sheets(root, m, WIDTH["mid"], [(F(0, 0), F(3, 0))])
    dummy(root, m, [(F(1, 0), F(2, 0))])
    spacers(root, m, [(F(1, 0), F(2, 0))])
    show(epi(root, m), [(F(1, 0), F(3, 0))])
    show(gate(root, m), [(F(2, 0), F(3, 0))])
    label("superlattice: Si and SiGe", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("dummy gate", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("inner spacer", (CX - 230.0, 40.0, 0), root, [(F(1, 0), F(2, 0))])
    label("S/D epi", (CX - 230.0, 150.0, 0), root, [(F(1, 0), F(3, 0))])
    label("gate metal", (CX, 165.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM, ZOOM, ZOOM])
    finish_as("gaa_zoom_a")


def zoom_b():
    """b, release: the SiGe is etched sideways out of the gaps, then the gate metal takes its place."""
    m, root = begin("gaa_zoom_b", 3)
    base(root, m)
    sige(root, m, WIDTH["mid"], [(F(0, 0), F(2, 0))], shrink=[(F(1, 0), (1, 1, 1)), (F(1, 0.9), (0.2, 1, 1))])
    si_sheets(root, m, WIDTH["mid"], [(F(0, 0), F(3, 0))])
    show(epi(root, m), [(F(0, 0), F(3, 0))])
    show(gate(root, m), [(F(2, 0), F(3, 0))])
    label("sacrificial SiGe", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("SiGe etched sideways", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("gate metal in the gaps", (CX, 165.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM, ZOOM, ZOOM_SIDE])
    finish_as("gaa_zoom_b")


def width_scene(name):
    """c, and section 5: FinFET whole fins, then a wide sheet, then a narrow one."""
    m, root = begin(name, 3)
    base(root, m)
    fins(root, m, [(F(0, 0), F(1, 0))])
    show(epi(root, m), [(F(1, 0), F(3, 0))])
    sheets(root, m, "wide", WIDTH["wide"], [(F(1, 0), F(2, 0))])
    sheets(root, m, "narrow", WIDTH["narrow"], [(F(2, 0), F(3, 0))])
    label("FinFET: whole fins", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("wide sheet: drive", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("narrow sheet: leakage", (CX, 165.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM_SIDE, ZOOM_SIDE, ZOOM_SIDE])
    finish_as(name)


def zoom_c():
    width_scene("gaa_zoom_c")


def power_scene(name):
    """d, and section 6: front-side power on the shared metal, then the rails under the substrate,
    then the front metal left to signals."""
    m, root = begin(name, 3)
    base(root, m)
    device(root, m, "mid", [(F(0, 0), F(3, 0))])
    s, p = route([(C.VDD_X, C.BUMP_Y, -60.0), (C.VDD_X, 6.0, -60.0)])
    stream_of(root, "vdd", 9, s, p, 46, m["c_dot_vdd"], 0, 0.10, 0.60, 90)
    s, p = route([(C.VSS_X, 6.0, -60.0), (C.VSS_X, C.BUMP_Y, -60.0)])
    stream_of(root, "vss", 9, s, p, 46, m["c_dot_gnd"], 0, 0.10, 0.60, 90)
    rails(root, m, [(F(1, 0), F(3, 0))])
    rail_dots(root, m, 1)
    y1 = C.level_y("thin", 0)
    s, p = route([(-510.0, 6.0, -60.0), (-510.0, y1, -60.0), (C.OUT_X, y1, -60.0)])
    stream_of(root, "sig", 9, s, p, 46, m["c_dot_out"], 2, 0.05, 0.55, 90)
    label("front: power and signal", (C.VDD_X - 160.0, C.THIN[1] - 40.0, 0), root, [(F(0, 0), F(1, 0))])
    label("rails under the substrate", (CX + 230.0, -440.0, 0), root, [(F(1, 0), F(3, 0))])
    label("front: signals only", (C.OUT_X, 640.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM_TOP, ZOOM_LOW, ZOOM_TOP])
    finish_as(name)


def zoom_d():
    power_scene("gaa_zoom_d")


def zoom_e():
    """e, roadmap: a FinFET, the nanosheet, the forksheet wall, then the CFET with NMOS over PMOS."""
    m, root = begin("gaa_zoom_e", 4)
    base(root, m)
    fins(root, m, [(F(0, 0), F(1, 0))], count=1)
    device(root, m, "nano", [(F(1, 0), F(2, 0))])
    wrap(root, m, "nano", WIDTH["mid"], [(F(1, 0), F(2, 0))])
    wall = empty("gaa_fork", root)
    show(wall, [(F(2, 0), F(3, 0))])
    box("fork_wall", (CX - 20.0, EPI_BOT, DEPTH), (CX + 20.0, GATE_HI + 10.0, 0.0), m["g_wall"], wall)
    device(root, m, "fork_n", [(F(2, 0), F(3, 0))], cx=CX - 300.0)
    device(root, m, "fork_p", [(F(2, 0), F(3, 0))], cx=CX + 300.0)
    device(root, m, "cfet_n", [(F(3, 0), F(4, 0))])
    device(root, m, "cfet_p", [(F(3, 0), F(4, 0))], dy=230.0)
    label("FinFET: 3 sides", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("nanosheet: 4 sides", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("forksheet: a wall", (CX, 200.0, 0), root, [(F(2, 0), F(3, 0))])
    label("CFET: NMOS over PMOS", (CX, 400.0, 0), root, [(F(3, 0), F(4, 0))])
    C.glide_camera(root, [ZOOM_SIDE, ZOOM, ZOOM_OUT, ((CX, 170.0, 0.0), 2000.0, 0.0, 0.10)])
    finish_as("gaa_zoom_e")


# ---- sections 1-10 ----------------------------------------------------------------------------


def sec1():
    m, root = begin("gaa_sec1", 3)
    base(root, m)
    sige(root, m, WIDTH["mid"], [(F(0, 0), F(2, 0))], shrink=[(F(1, 0), (1, 1, 1)), (F(1, 0.9), (0.2, 1, 1))])
    si_sheets(root, m, WIDTH["mid"], [(F(0, 0), F(3, 0))])
    show(epi(root, m), [(F(0, 0), F(3, 0))])
    show(gate(root, m), [(F(2, 0), F(3, 0))])
    wrap(root, m, "mid", WIDTH["mid"], [(F(2, 0), F(3, 0))])
    label("stack: Si sheets, SiGe between", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("release: SiGe out", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("wrap: gate on four sides", (CX, 165.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM, ZOOM, ZOOM])
    finish_as("gaa_sec1")


def sec2():
    m, root = begin("gaa_sec2", 3)
    base(root, m)
    show(epi(root, m), [(F(0, 0), F(3, 0))])
    si_sheets(root, m, WIDTH["mid"], [(F(0, 0), F(3, 0))])
    current(root, m, 1)
    show(gate(root, m), [(F(2, 0), F(3, 0))])
    label("source and drain epi", (CX - 230.0, 150.0, 0), root, [(F(0, 0), F(1, 0))])
    label("carriers through every sheet", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("gate and inner spacers", (CX, 165.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM, ZOOM, ZOOM_SIDE])
    finish_as("gaa_sec2")


def sec3():
    m, root = begin("gaa_sec3", 3)
    base(root, m)
    sige(root, m, WIDTH["mid"], [(F(0, 0), F(2, 0))], shrink=[(F(1, 0), (1, 1, 1)), (F(1, 0.6), (0.83, 1, 1))])
    si_sheets(root, m, WIDTH["mid"], [(F(0, 0), F(3, 0))])
    show(epi(root, m), [(F(0, 0), F(3, 0))])
    spacers(root, m, [(F(1, 0), F(2, 0))])
    show(gate(root, m), [(F(2, 0), F(3, 0))])
    label("before release", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("SiGe recessed, nitride in", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("after release: gate metal", (CX, 165.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM, ZOOM, ZOOM_SIDE])
    finish_as("gaa_sec3")


def sec4():
    m, root = begin("gaa_sec4", 5)
    base(root, m)
    sige(root, m, WIDTH["mid"], [(F(0, 0), F(3, 0))], shrink=[(F(1, 0), (1, 1, 1)), (F(1, 0.6), (0.83, 1, 1))])
    si_sheets(root, m, WIDTH["mid"], [(F(0, 0), F(5, 0))])
    spacers(root, m, [(F(1, 0), F(4, 0))])
    show(epi(root, m), [(F(2, 0), F(5, 0))])
    show(gate(root, m), [(F(4, 0), F(5, 0))])
    wrap(root, m, "mid", WIDTH["mid"], [(F(4, 0), F(5, 0))])
    label("SUPERLATTICE: Si and SiGe", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("INNER SPACER", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("S/D EPI", (CX - 230.0, 150.0, 0), root, [(F(2, 0), F(3, 0))])
    label("RELEASE: SiGe out", (CX, 165.0, 0), root, [(F(3, 0), F(4, 0))])
    label("HK/METAL GATE", (CX, 165.0, 0), root, [(F(4, 0), F(5, 0))])
    C.glide_camera(root, [ZOOM, ZOOM, ZOOM, ZOOM, ZOOM])
    finish_as("gaa_sec4")


def sec5():
    width_scene("gaa_sec5")


def sec6():
    power_scene("gaa_sec6")


def sec7():
    """Node comparison: the same device through the three nodes, the rails added at A16."""
    m, root = begin("gaa_sec7", 3)
    base(root, m)
    device(root, m, "mid", [(F(0, 0), F(3, 0))])
    wrap(root, m, "mid", WIDTH["mid"], [(F(0, 0), F(3, 0))])
    current(root, m, 1, tag="a")
    current(root, m, 2, tag="b")
    rails(root, m, [(F(2, 0), F(3, 0))])
    rail_dots(root, m, 2)
    label("Samsung SF3E, 2022", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("N2 and 18A, 2025", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("A16, 2026+: backside", (CX, 165.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM, ZOOM, ZOOM_LOW])
    finish_as("gaa_sec7")


def sec8():
    """Roadmap and who makes it: the nodes, the tools, then the CFET pair."""
    m, root = begin("gaa_sec8", 3)
    base(root, m)
    device(root, m, "mid", [(F(0, 0), F(2, 0))])
    wrap(root, m, "mid", WIDTH["mid"], [(F(1, 0), F(2, 0))])
    device(root, m, "cfet_n", [(F(2, 0), F(3, 0))])
    device(root, m, "cfet_p", [(F(2, 0), F(3, 0))], dy=230.0)
    label("SF3, N2, 18A, A16", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("epi", (CX - 230.0, 150.0, 0), root, [(F(1, 0), F(2, 0))])
    label("ALD gate", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("CFET: NMOS over PMOS", (CX, 400.0, 0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM, ZOOM, ZOOM_OUT])
    finish_as("gaa_sec8")


def sec9():
    """Yield and cost: a device, the FinFET it replaces, and a wafer priced in the press."""
    m, root = begin("gaa_sec9", 3)
    base(root, m)
    device(root, m, "mid", [(F(0, 0), F(1, 0))])
    wrap(root, m, "mid", WIDTH["mid"], [(F(0, 0), F(1, 0))])
    fins(root, m, [(F(1, 0), F(2, 0))])
    show(disc("wafer", (CX, -420.0, -600.0), 900.0, 60.0, m["g_wafer"], root), [(F(2, 0), F(3, 0))])
    label("Samsung SF3E yield 50-60%", (CX, 165.0, 0), root, [(F(0, 0), F(1, 0))])
    label("N3E FinFET: 82-86%", (CX, 165.0, 0), root, [(F(1, 0), F(2, 0))])
    label("N2 wafer: over $30k (reported)", (CX + 200.0, -360.0, -300.0), root, [(F(2, 0), F(3, 0))])
    C.glide_camera(root, [ZOOM, ZOOM_SIDE, ((CX, -300.0, -300.0), 3200.0, 0.0, 0.35)])
    finish_as("gaa_sec9")


def sec10():
    """Sources: four cards on a plinth, one lit per beat, as in the cell page."""
    m, root = begin("gaa_sec10", 4)
    box("plinth", (-1800, 0, -900), (1800, 30, 900), m["g_plinth"], root)
    cards = [
        ((-800.0, 0.0, -400.0), "Samsung 3GAA, Intel 18A"),
        ((800.0, 0.0, -400.0), "TSMC N2 and A16"),
        ((-800.0, 0.0, 400.0), "imec, press reports"),
        ((800.0, 0.0, 400.0), "AMAT, Lam, IBM"),
    ]
    for i, (c, text) in enumerate(cards):
        x, _, z = c
        box(f"card{i}", (x - 600, 30, z - 380), (x + 600, 50, z + 380), m["g_card"], root)
        lit = box(f"card{i}_lit", (x - 620, 50, z - 400), (x + 620, 60, z + 400), m["g_card_on"], root)
        show(lit, [(F(i, 0.1), F(i + 1, 0))])
        label(text, (x - 600, 70, z + 400), root, [(F(i, 0.1), F(i + 1, 0))])
    C.glide_camera(root, [
        ((-800.0, 0.0, -400.0), 3200.0, 0.0, 0.95),
        ((800.0, 0.0, -400.0), 3200.0, 0.0, 0.95),
        ((-800.0, 0.0, 400.0), 3200.0, 0.0, 0.95),
        ((800.0, 0.0, 400.0), 3200.0, 0.0, 0.95),
    ])
    finish_as("gaa_sec10")


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}
SECTIONS = [sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9, sec10]


if __name__ == "__main__":
    picks = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not picks:
        picks = ["overview", *ZOOMS, *[str(n) for n in range(1, 11)]]
    for pick in picks:
        if pick == "overview":
            build()
            finish("gaa", page="chip")
        elif pick in ZOOMS:
            ZOOMS[pick]()
        else:
            SECTIONS[int(pick) - 1]()
