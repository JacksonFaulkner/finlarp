"""CHIP scenes for the NMOS node: the overview (the whole chip, then in on the NMOS transistor),
the zoom-ins a-e and the numbered sections 1-10. Each is one Blender scene and one GLB.

Run from the repo root, one scene per run (no argument builds the overview):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_nmos.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_nmos.py -- zoom_a
    blender -b --factory-startup --python tools/pbr3d/blender/chip_nmos.py -- sec4

Writes blender/chip_nmos[_<key>].blend and assets/chip_nmos[_<key>].glb. One beat is 8 s.

Overview beats:
  0 whole     the whole chip, the NMOS picked out
  1 off       zoomed in: n+ source and drain in p-type silicon, gate low, no channel
  2 gate up   the gate rises, the channel forms under it
  3 flow      electrons run from the source through the channel to the drain
  4 gate down the gate falls, the channel closes, the flow stops
  5 whole     back out to the whole chip

Zoom-ins (the old a-e, same letters and labels; 3 or 4 beats each): a the gate stack, b subthreshold,
threshold and on, c saturation and pinch-off, d short channels and DIBL, e dopants and strain.
Sections (one scene per `# ` heading of CHIP_NMOS.txt): 1 what happens, 2 the parts, 3 one switching
cycle, 4 threshold, 5 short channels and body bias, 6 dopants and strain, 7 transistor count,
8 who makes it, 9 chokepoints and risks, 10 sources.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, label, mat, overlay, route, show, stream_of, tube, empty, ball  # noqa: E402

BEATS = 6
WHOLE_POSE = C.WHOLE
ZOOM_POSE = ((C.NMOS_X, 60.0, 0.0), 1500.0, 0.0, 0.08)  # the overview's zoom
CLOSE_POSE = ((C.NMOS_X, 80.0, 0.0), 700.0, 0.0, 0.12)  # close on the channel and gate
MID_POSE = ((C.NMOS_X, 60.0, 0.0), 1100.0, 0.0, 0.10)
PULL_POSES = [
    WHOLE_POSE,
    ((0.0, 620.0, 0.0), 6300.0, 0.0, 0.10),
    ((0.0, 620.0, 0.0), 6800.0, 0.0, 0.10),
    ((0.0, 620.0, 0.0), 7300.0, 0.0, 0.10),
]

GATE_RISE, GATE_FALL = F(2, 0.10), F(4, 0.25)  # the overview's gate glow
GATE_HALF = C.GATE_HALF
ZOOM = ((C.NMOS_X, 60.0, 0.0), 1500.0, 0.0, 0.08)
WHOLE = C.WHOLE


def build():
    m, root = start("nmos", BEATS, page="chip")
    C.mats(m)
    C.chip(root, m)
    cx = C.NMOS_X

    m["hl"] = mat("chip_nmos_hl", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.16)
    C.overlay(root, "nmos_hl", (cx - 330, -140, -250), (cx + 330, 150, 14), m["hl"],
              [(F(0, 0), F(1, 0.3)), (F(5, 0.1), F(6, 0))])

    # the gate's voltage: a glow on the gate stack, in front of the cut face
    m["gate_on"] = mat("chip_nmos_gate_on", (1.0, 0.72, 0.35), emit=(1.0, 0.65, 0.25), strength=1.2, alpha=0.5)
    C.overlay(root, "gate_on", (cx - C.GATE_HALF - 6, 14, -246), (cx + C.GATE_HALF + 6, 126, 6),
              m["gate_on"], [(GATE_RISE, GATE_FALL)])
    # the inversion layer: a cyan sheet on the silicon surface between the n+ islands, in front of the cut
    m["chan"] = mat("chip_nmos_chan", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=6.0)
    C.overlay(root, "chan_on", (cx - 150, -14, -40), (cx + 150, 16, 10), m["chan"],
              [(CHAN_FORM, GATE_FALL)])

    # electrons: out of the grounded source contact, along the surface through the channel, up the drain contact
    s, p = route([(cx - C.SD, 410.0, 12), (cx - C.SD, 0.0, 12), (cx + C.SD, 0.0, 12), (cx + C.SD, 410.0, 12)])
    stream_of(root, "elec", 12, s, p, 22, m["c_dot_sig"], 3, 0.05, 0.70, 100)

    whole = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
    label("NMOS", (cx, -190.0, 0), root, whole)
    label("n+ source", (cx - C.SD, -130.0, 0), root, ZW)
    label("n+ drain", (cx + C.SD, -130.0, 0), root, ZW)
    label("p-type silicon", (cx - 330.0, -230.0, 0), root, [(F(1, 0), F(2, 0.1))])
    label("gate low: no channel", (cx, 290.0, 0), root, [(F(1, 0), F(2, 0.1)), (F(4, 0.25), F(5, 0))])
    label("gate high", (cx, 290.0, 0), root, [(GATE_RISE, GATE_FALL)])
    label("channel: electrons", (cx, -60.0, 0), root, [(CHAN_FORM, GATE_FALL)])
    label("current: source to drain", (cx + 50, 330.0, 0), root, [(F(3, 0.1), F(4, 0.0))])

    C.glide_camera(root, POSES)


ZOOM_IN = ((C.NMOS_X, 60.0, 0.0), 1400.0, 0.0, 0.08)
POSES = [WHOLE, ZOOM, ZOOM, ZOOM_IN, ZOOM, WHOLE]
ZW = [(F(1, 0), F(5, 0))]  # the zoomed-in tags: beats 1 to 4
CHAN_FORM = F(2, 0.50)  # the channel forms once the gate is up


# ---- shared pieces ---------------------------------------------------------------------------

NX, SD = C.NMOS_X, C.SD


def span(a, b):
    """Beats a up to b, as one interval."""
    return [(F(a, 0), F(b, 0))]


def nmos_mats(m):
    """The NMOS-only materials, named chip_nmos_* (mat() caches by name)."""
    return {
        "gate_on": mat("chip_nmos_gate_on2", (1.0, 0.72, 0.35), emit=(1.0, 0.65, 0.25), strength=1.6, alpha=0.5),
        "chan": mat("chip_nmos_chan2", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=6.0),
        "part": mat("chip_nmos_part", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.5, alpha=0.35),
        "dep": mat("chip_nmos_dep", (0.70, 0.50, 1.0), emit=(0.70, 0.50, 1.0), strength=2.0, alpha=0.5),
        "halo": mat("chip_nmos_halo", (0.75, 0.60, 1.0), emit=(0.70, 0.50, 1.0), strength=2.5, alpha=0.6),
        "field": mat("chip_nmos_field", (1.0, 0.55, 0.85), emit=(1.0, 0.50, 0.80), strength=3.0),
        "strain": mat("chip_nmos_strain", (1.0, 0.82, 0.35), emit=(1.0, 0.78, 0.30), strength=3.0),
        "dopant": mat("chip_nmos_dopant", (1.0, 0.90, 0.55), emit=(1.0, 0.85, 0.40), strength=1.2, alpha=0.5),
        "atom": mat("chip_nmos_atom", (1.0, 0.95, 0.60), emit=(1.0, 0.92, 0.50), strength=6.0),
        "hik": mat("chip_nmos_hik", (0.85, 0.90, 1.0), emit=(0.80, 0.90, 1.0), strength=2.0, alpha=0.6),
        "fin": mat("chip_nmos_fin", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=4.0, alpha=0.7),
        "sheet": mat("chip_nmos_sheet", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=4.0),
        "well": mat("chip_nmos_well", (0.70, 0.50, 1.0), emit=(0.70, 0.50, 1.0), strength=2.0, alpha=0.45),
        "sim": mat("chip_nmos_sim", (0.60, 0.75, 1.0), emit=(0.60, 0.75, 1.0), strength=2.0),
        "warn": mat("chip_nmos_warn", (1.0, 0.30, 0.30), emit=(1.0, 0.25, 0.25), strength=3.0, alpha=0.5),
        "cont": mat("chip_nmos_cont", (1.0, 0.82, 0.40), emit=(1.0, 0.78, 0.30), strength=4.0, alpha=0.6),
    }


def gate_glow(root, x, iv):
    return overlay(root, "gate_glow", (NX - GATE_HALF - 6, 14, -246), (NX + GATE_HALF + 6, 126, 6), x["gate_on"], iv)


def channel(root, x, iv, x1=150.0):
    """The inversion layer from the source side to x1 (offset from the NMOS centre)."""
    return overlay(root, "chan_on", (NX - 150, -14, -40), (NX + x1, 16, 10), x["chan"], iv)


def part(root, x, name, lo, hi, iv, mat_key="part"):
    return overlay(root, name, lo, hi, x[mat_key], iv)


def lines(root, name, segs, m, r, iv, verts=8):
    """Tubes (poly point pairs) grouped and switched on for `iv`."""
    g = empty(name, root)
    for i, (a, b) in enumerate(segs):
        tube(f"{name}{i}", a, b, r, m, g, verts=verts)
    show(g, iv)
    return g


def leak(root, m, b, n=9, u0=0.05, u1=0.7, life=100):
    """Off-state leakage: dots under the surface, from source to drain, in beat b."""
    s, p = route([(NX - SD, -40.0, 30.0), (NX + SD, -40.0, 30.0)])
    return stream_of(root, f"leak{b}", n, s, p, 12, m["c_dot_out"], b, u0, u1, life)


def current(root, m, b, n=10, u0=0.05, u1=0.7, life=100):
    """On-state electrons along the surface, from source to drain, in beat b."""
    s, p = route([(NX - SD, 20.0, 14.0), (NX + SD, 20.0, 14.0)])
    return stream_of(root, f"flow{b}", n, s, p, 16, m["c_dot_sig"], b, u0, u1, life)


def whole(root, m, **lit):
    C.chip(root, m, **lit)


# ---- zoom-ins a-e ----------------------------------------------------------------------------

ZA_POSES = [ZOOM_POSE, CLOSE_POSE, CLOSE_POSE, CLOSE_POSE]
ZB_POSES = [ZOOM_POSE, CLOSE_POSE, CLOSE_POSE]
ZC_POSES = [ZOOM_POSE, CLOSE_POSE, CLOSE_POSE]
ZD_POSES = [ZOOM_POSE, CLOSE_POSE, CLOSE_POSE]
ZE_POSES = [ZOOM_POSE, CLOSE_POSE, CLOSE_POSE]


def zoom_a(m, root, x=None):
    """a the gate stack: metal on high-k, the field through it, the channel it draws."""
    x = x or nmos_mats(m)
    whole(root, m)
    part(root, x, "hik_on", (NX - 108, -2, -244), (NX + 108, 26, 10), span(0, 4), "hik")
    label("metal gate", (NX + 130, 96, 14), root, span(0, 4))
    label("high-k dielectric", (NX + 150, 8, 14), root, span(0, 4))
    label("p-type silicon", (NX + 330, -45, 0), root, span(0, 4))
    gate_glow(root, x, span(1, 4))
    lines(root, "field", [((NX - 70, 130, 30), (NX - 70, -30, 30)), ((NX + 70, 130, 30), (NX + 70, -30, 30))],
          x["field"], 4, span(1, 2))
    label("field through the oxide", (NX - 240, 60, 30), root, span(1, 2))
    channel(root, x, span(2, 4))
    label("channel: electrons", (NX, -40, 24), root, span(2, 4))
    label("thick, but electrically thin", (NX - 260, 40, 14), root, span(3, 4))


def zoom_b(m, root, x=None):
    """b subthreshold, threshold and on: leakage, then the channel forms, then full current."""
    x = x or nmos_mats(m)
    whole(root, m)
    leak(root, m, 0)
    label("below threshold: leakage only", (NX, -95, 30), root, span(0, 1))
    gate_glow(root, x, span(1, 3))
    channel(root, x, span(1, 3))
    label("threshold: inversion starts", (NX, 60, 40), root, span(1, 2))
    current(root, m, 2)
    label("above threshold: full current", (NX, 170, 30), root, span(2, 3))


def zoom_c(m, root, x=None):
    """c saturation: an even channel, the drain end thins, the channel pinches off at the drain."""
    x = x or nmos_mats(m)
    whole(root, m)
    gate_glow(root, x, span(0, 3))
    channel(root, x, span(0, 1))
    current(root, m, 0, n=10, life=100)
    label("low drain voltage: even channel", (NX, 170, 30), root, span(0, 1))
    channel(root, x, span(1, 2), x1=90.0)
    current(root, m, 1, n=10)
    label("the drain end thins", (NX + 150, 170, 30), root, span(1, 2))
    channel(root, x, span(2, 3), x1=40.0)
    current(root, m, 2, n=10, life=70)
    label("pinch-off at the drain", (NX + 150, 170, 30), root, span(2, 3))


def zoom_d(m, root, x=None):
    """d short channels: the gate owns the barrier, then the drain reaches the source side, then leakage."""
    x = x or nmos_mats(m)
    whole(root, m)
    gate_glow(root, x, span(0, 1))
    channel(root, x, span(0, 1))
    label("long gate: the gate owns the barrier", (NX, 170, 30), root, span(0, 1))
    drain_field = [((NX + SD, y, 30), (NX - 40, y, 30)) for y in (40.0, 62.0, 84.0)]
    lines(root, "drain_field", drain_field, x["field"], 3, span(1, 3))
    label("drain field reaches the source", (NX + 60, 130, 30), root, span(1, 3))
    leak(root, m, 1, n=9)
    label("short channel: Vt falls", (NX, -95, 30), root, span(1, 2))
    leak(root, m, 2, n=12)
    label("higher drain voltage: more leakage", (NX, -95, 30), root, span(2, 3))


def zoom_e(m, root, x=None):
    """e dopants and strain: the dopant atoms, the halo pockets and Si:P, then the tensile strain."""
    x = x or nmos_mats(m)
    whole(root, m)
    dopants_body(root, m, x, 0)
    label("As / P atoms", (NX + SD + 150, -80, 40), root, span(0, 1))
    halo_body(root, m, x, 1)
    label("halo pocket", (NX + 95, 40, 30), root, span(1, 2))
    label("Si:P epitaxy", (NX - SD, -120, 40), root, span(1, 2))
    gate_glow(root, x, span(2, 3))
    channel(root, x, span(2, 3))
    lines(root, "strain", [((NX - 40, 28, 30), (NX - 240, 28, 30)), ((NX + 40, 28, 30), (NX + 240, 28, 30))],
          x["strain"], 5, span(2, 3))
    current(root, m, 2, n=10, life=80)
    label("tensile strain: faster electrons", (NX, 170, 30), root, span(2, 3))


def dopants_body(root, m, x, b):
    """The source and drain lit as doped n+ silicon, with dopant atoms in front of them."""
    overlay(root, "dop_src", (NX - SD - 72, -92, -244), (NX - SD + 72, 8, 10), x["dopant"], span(b, b + 2))
    overlay(root, "dop_drn", (NX + SD - 72, -92, -244), (NX + SD + 72, 8, 10), x["dopant"], span(b, b + 2))
    g = empty("atoms", root)
    for xi, xo in enumerate((NX - SD - 40, NX - SD + 40, NX + SD - 40, NX + SD + 40)):
        for yi, yo in enumerate((-70.0, -40.0, -12.0)):
            ball(f"atom{xi}_{yi}", (xo, yo, 16.0), 9.0, x["atom"], g, 8)
    show(g, span(b, b + 1))


def halo_body(root, m, x, b):
    """Halo pockets beside the channel ends, and the Si:P source and drain still lit."""
    overlay(root, "halo_l", (NX - 125, -40, -200), (NX - 70, 12, 8), x["halo"], span(b, b + 1))
    overlay(root, "halo_r", (NX + 70, -40, -200), (NX + 125, 12, 8), x["halo"], span(b, b + 1))
    overlay(root, "dop_src", (NX - SD - 72, -92, -244), (NX - SD + 72, 8, 10), x["dopant"], span(b, b + 1))
    overlay(root, "dop_drn", (NX + SD - 72, -92, -244), (NX + SD + 72, 8, 10), x["dopant"], span(b, b + 1))


# ---- sections 1-10 --------------------------------------------------------------------------

S1_POSES = [ZOOM_POSE] * 3
S2_POSES = [ZOOM_POSE] * 5
S3_POSES = [ZOOM_POSE] * 5
S4_POSES = [MID_POSE] * 3
S5_POSES = [ZOOM_POSE] * 3
S6_POSES = [ZOOM_POSE] * 3
S7_POSES = [CLOSE_POSE, WHOLE, WHOLE]
S8_POSES = [ZOOM_POSE] * 3
S9_POSES = [ZOOM_POSE, ZOOM_POSE, WHOLE]
S10_POSES = PULL_POSES


def sec1(m, root, x=None):
    """1 what happens: off, then the channel and gate on, then the current."""
    x = x or nmos_mats(m)
    whole(root, m)
    label("gate low: no channel", (NX, 290.0, 0), root, span(0, 1))
    label("n+ source", (NX - SD, -130.0, 0), root, span(0, 3))
    label("n+ drain", (NX + SD, -130.0, 0), root, span(0, 3))
    gate_glow(root, x, span(1, 3))
    channel(root, x, span(1, 3))
    label("gate high: electron channel", (NX, 290.0, 0), root, span(1, 2))
    current(root, m, 2)
    label("current: source to drain", (NX + 50, 330.0, 0), root, span(2, 3))


def sec2(m, root, x=None):
    """2 the parts: source, gate stack, drain, p-well, and the parts inside, each lit in turn."""
    x = x or nmos_mats(m)
    whole(root, m)
    part(root, x, "src_hl", (NX - SD - 75, -96, -246), (NX - SD + 75, 12, 8), span(0, 1))
    label("N+ SOURCE", (NX - SD, -130.0, 0), root, span(0, 1))
    part(root, x, "gate_hl", (NX - GATE_HALF - 8, 10, -248), (NX + GATE_HALF + 8, 126, 8), span(1, 2))
    label("GATE STACK", (NX, 170.0, 0), root, span(1, 2))
    part(root, x, "drn_hl", (NX + SD - 75, -96, -246), (NX + SD + 75, 12, 8), span(2, 3))
    label("N+ DRAIN", (NX + SD, -130.0, 0), root, span(2, 3))
    part(root, x, "well_hl", (NX - 420, -300, -244), (NX + 420, -2, 8), span(3, 4))
    label("P-WELL", (NX - 330.0, -230.0, 0), root, span(3, 4))
    overlay(root, "halo_l", (NX - 125, -40, -200), (NX - 70, 12, 8), x["halo"], span(4, 5))
    overlay(root, "halo_r", (NX + 70, -40, -200), (NX + 125, 12, 8), x["halo"], span(4, 5))
    overlay(root, "sti", (NX + 290, -120, -240), (NX + 320, 14, 6), x["well"], span(4, 5))
    label("halo pockets, spacers, STI", (NX + 330, 40.0, 0), root, span(4, 5))


def sec3(m, root, x=None):
    """3 one switching cycle: off, depletion, inversion, linear then saturation, turn-off."""
    x = x or nmos_mats(m)
    whole(root, m)
    label("1. off: gate at 0 V", (NX, 290.0, 0), root, span(0, 1))
    overlay(root, "depletion", (NX - GATE_HALF, -60, -200), (NX + GATE_HALF, -2, 8), x["dep"], span(1, 2))
    label("2. depletion: holes pushed away", (NX, 290.0, 0), root, span(1, 2))
    gate_glow(root, x, span(2, 4))
    channel(root, x, span(2, 4))
    label("3. inversion: electron channel", (NX, 290.0, 0), root, span(2, 3))
    channel(root, x, [(F(3, 0), F(3, 0.5))])
    channel(root, x, [(F(3, 0.5), F(4, 0))], x1=40.0)
    current(root, m, 3, n=10, u0=0.05, u1=0.6)
    label("4. linear, then saturation", (NX, 290.0, 0), root, span(3, 4))
    leak(root, m, 4, n=9)
    label("5. turn-off: channel empties", (NX, 290.0, 0), root, span(4, 5))


def sec4(m, root, x=None):
    """4 threshold and subthreshold: leakage below it, the channel at it, full current above it."""
    zoom_b(m, root, x)


def sec5(m, root, x=None):
    """5 short channels and body bias, then wrapping the gate."""
    x = x or nmos_mats(m)
    whole(root, m)
    leak(root, m, 0, n=9)
    label("DIBL: drain lowers the barrier", (NX, 170.0, 30), root, span(0, 1))
    overlay(root, "well_on", (NX - 420, -300, -240), (NX + 420, -4, 6), x["well"], span(1, 2))
    label("body bias: the well shifts Vt", (NX + 330, -150, 20), root, span(1, 2))
    gate_glow(root, x, span(2, 3))
    overlay(root, "fin", (NX - 40, -30, -200), (NX + 40, 110, 8), x["fin"], span(2, 3))
    label("fin: the gate wraps the channel", (NX + 120, 150, 20), root, span(2, 3))


def sec6(m, root, x=None):
    """6 dopants and strain: the dopant atoms, the halo pockets, the tensile strain."""
    zoom_e(m, root, x)


def sec7(m, root, x=None):
    """7 transistor count: one NMOS, billions of them, then the chip wired up."""
    x = x or nmos_mats(m)
    whole(root, m)
    part(root, x, "one_hl", (NX - 330, -140, -250), (NX + 330, 150, 14), span(0, 1))
    label("one NMOS", (NX, -190.0, 0), root, span(0, 1))
    label("billions of switches like this one", (0.0, -380.0, 0), root, span(1, 2))
    overlay(root, "lit_thin", (-C.HALF - 6, C.THIN[0] - 14, -C.DEPTH + 40), (C.HALF + 6, C.THIN[1] + 14, 6),
            m["c_lit_thin"], span(2, 3))
    label("contacts and copper wiring", (1100.0, 500.0, 0), root, span(2, 3))


def sec8(m, root, x=None):
    """8 who makes it: a FinFET (TSMC), stacked sheets (Intel), the device simulated (Synopsys, Cadence)."""
    x = x or nmos_mats(m)
    whole(root, m)
    overlay(root, "fin", (NX - 40, -30, -200), (NX + 40, 110, 8), x["fin"], span(0, 1))
    label("TSMC: FinFET, N3/N5", (NX + 120, 150, 20), root, span(0, 1))
    for i, y in enumerate((40.0, 70.0, 100.0)):
        overlay(root, f"sheet{i}", (NX - 150, y, -12), (NX + 150, y + 12, 12), x["sheet"], span(1, 2))
    label("Intel 18A: RibbonFET, stacked sheets", (NX + 120, 150, 20), root, span(1, 2))
    grid = [((NX + dx, -100.0, 14.0), (NX + dx, 170.0, 14.0)) for dx in (-240.0, -120.0, 0.0, 120.0, 240.0)]
    grid += [((NX - 260.0, y, 14.0), (NX + 260.0, y, 14.0)) for y in (-90.0, -30.0, 30.0, 90.0, 150.0)]
    lines(root, "sim", grid, x["sim"], 1.5, span(2, 3), verts=6)
    label("Synopsys, Cadence: device equations", (NX + 120, 150, 20), root, span(2, 3))


def sec9(m, root, x=None):
    """9 chokepoints and risks: leakage, contact resistance, very few fabs."""
    x = x or nmos_mats(m)
    whole(root, m)
    leak(root, m, 0, n=9)
    label("leakage and Vt variability", (NX, 170.0, 30), root, span(0, 1))
    overlay(root, "cont_s", (NX - SD - 36, 8, -40), (NX - SD + 36, 410, 12), x["cont"], span(1, 2))
    overlay(root, "cont_d", (NX + SD - 36, 8, -40), (NX + SD + 36, 410, 12), x["cont"], span(1, 2))
    overlay(root, "cont_g", (NX - 36, 120, -40), (NX + 36, 410, 12), x["cont"], span(1, 2))
    label("contact resistance limits drive", (NX + SD + 80, 300, 20), root, span(1, 2))
    part(root, x, "risk_hl", (NX - 330, -140, -250), (NX + 330, 150, 14), span(2, 3), "warn")
    label("very few leading fabs", (NX, -190.0, 0), root, span(2, 3))


def sec10(m, root, x=None):
    """10 sources: the whole chip, pulled back slowly, the four source groups tagged in turn."""
    x = x or nmos_mats(m)
    whole(root, m)
    part(root, x, "src_all", (NX - 330, -140, -250), (NX + 330, 150, 14), span(0, 1))
    label("transistor counts", (NX, -190.0, 0), root, span(0, 1))
    part(root, x, "src_sd", (NX - SD - 75, -96, -246), (NX + SD + 75, 12, 8), span(1, 2))
    label("dopants and Si:P", (NX, -190.0, 0), root, span(1, 2))
    part(root, x, "src_gate", (NX - GATE_HALF - 8, 10, -248), (NX + GATE_HALF + 8, 126, 8), span(2, 3))
    label("swing and DIBL", (NX, -190.0, 0), root, span(2, 3))
    label("makers and simulators", (NX, -190.0, 0), root, span(3, 4))


# ---- registry and entry point ----------------------------------------------------------------

# key -> (beats, camera poses, builder)
SCENES = {
    "zoom_a": (4, ZA_POSES, zoom_a),
    "zoom_b": (3, ZB_POSES, zoom_b),
    "zoom_c": (3, ZC_POSES, zoom_c),
    "zoom_d": (3, ZD_POSES, zoom_d),
    "zoom_e": (3, ZE_POSES, zoom_e),
    "sec1": (3, S1_POSES, sec1),
    "sec2": (5, S2_POSES, sec2),
    "sec3": (5, S3_POSES, sec3),
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
    name = f"nmos_{key}"
    m, root = start(name, beats, page="chip")
    C.mats(m)
    fn(m, root, nmos_mats(m))
    C.glide_camera(root, poses)
    finish(name, page="chip")


if __name__ == "__main__":
    key = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "overview"
    if key == "overview":
        build()
        finish("nmos", page="chip")
    else:
        scene(key)
