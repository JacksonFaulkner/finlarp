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

Every scene uses the detailed transistor of chip_mos_detail.py; the overview swaps it into the
whole chip in place of chip_kit's plain one.

Zoom-ins (same letters and labels; 3 or 4 beats each): a the gate stack, b subthreshold,
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
import chip_mos_detail as D  # noqa: E402
from chip_kit import F, empty, label, show  # noqa: E402

BEATS = 6
WHOLE = C.WHOLE


def build():
    """The overview: the whole chip, in on the detailed NMOS (off, gate up, flow, gate down), out."""
    m, root = start("nmos", BEATS, page="chip")
    C.mats(m)
    D.mats(m)
    d, _ = D.in_chip(m, root)
    cx = d.cx
    D.outline(root, m, "nmos_pick", (cx - d.half - 30, -350.0), (cx + d.half + 30, d.ct_top + 40),
              [(F(0, 0), F(1, 0.2)), (F(5, 0.2), F(6, 0))], t=22.0, z=12.0)
    whole = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
    label("NMOS", (cx, d.ct_top + 60, 12), root, whole)
    label("copper wiring", (0.0, C.MID[0], 0), root, whole)
    label("package bumps", (C.bump_x(5), C.BUMP_Y, -60), root, whole)
    # 1 off: holes everywhere in the well, no channel
    D.majority_dots(root, m, d, D.beats(1, 5), [(F(1, 0), F(2, 0.45)), (F(4, 0.35), F(5, 0))])
    D.depletion(root, m, d, D.beats(1), under_gate=False)
    label("n+ source: ground", (cx - d.ct_x, -70.0, 0), root, D.beats(1))
    label("n+ drain: output", (cx + d.ct_x, -70.0, 0), root, D.beats(1))
    label("gate 0 V: off", (cx, 120.0, 0), root, D.beats(1))
    label("p-well: holes", (cx - 230.0, -180.0, D.CZ), root, D.beats(1))
    # 2 the gate rises, the field reaches down, the channel forms
    D.gate_glow(root, m, d, [(F(2, 0.1), F(4, 0.25))])
    D.field(root, m, d, [(F(2, 0.1), F(3, 0))])
    D.channel(root, m, d, [(F(2, 0.45), F(4, 0.25))])
    label("gate rises to ~0.75 V", (cx, 120.0, 0), root, D.beats(2))
    label("field through the high-k", (cx, 60.0, D.CZ), root, D.beats(2))
    label("electron channel forms", (cx + 25, -8.0, 2), root, [(F(2, 0.45), F(3, 0))])
    # 3 electrons ride in through the source contact, across, and out through the drain
    D.beads(root, "elec_in", D.carrier_path(d), 14, 10.0, m["mos_elec"], 3, 0.03, 0.8, 100)
    label("electrons from ground", (cx - d.ct_x, 300.0, D.CZ), root, D.beats(3))
    label("across the channel", (cx, -8.0, 2), root, D.beats(3))
    label("out to the drain", (cx + d.ct_x, 300.0, D.CZ), root, D.beats(3))
    # 4 the gate falls, the channel empties, a trickle of leakage
    D.leak(root, m, d, 4, n=5)
    label("gate falls to 0 V", (cx, 120.0, 0), root, D.beats(4))
    label("channel empties", (cx, -8.0, 2), root, [(F(4, 0.2), F(5, 0))])
    label("leakage only", (cx - 120.0, -52.0, D.CZ), root, D.beats(4))
    label("one switch of billions", (cx, -420.0, 0), root, D.beats(5))
    zoom = D.frame_dev(d, bottom=-300, pad=1.16)
    close = D.frame_dev(d, x0=cx - 330, x1=cx + 330, bottom=-200, top=240, pad=1.12)
    C.glide_camera(root, [WHOLE, zoom, close, zoom, close, WHOLE])


# ---- zoom-ins a-e ----------------------------------------------------------------------------
# Close-ups of the detailed NMOS on its own (chip_mos_detail), like the sections. Each zoom
# function builds its pieces and returns one camera pose per beat.

def _dev(m, root, iv=None, **kw):
    D.mats(m)
    return D.planar(m, root, "n", 0.0, name="nm", iv=iv, **kw)


def _gate_close(d):
    return D.frame((-230.0, -90.0, -40.0), (230.0, 210.0, 0.0), pitch=0.10, pad=1.12)


def zoom_a(m, root):
    """a the gate stack: its layers, the field through them, the channel it draws, high-k."""
    d = _dev(m, root, contacts=False)
    label("fill metal (W)", (0.0, 120.0, 0), root, D.beats(0))
    label("work-function metal", (d.gh - 15, 90.0, 0), root, D.beats(0))
    label("high-k HfO2", (-d.gh + 4, 60.0, 0), root, D.beats(0))
    label("SiO2 interlayer", (-30.0, 3.0, 0), root, D.beats(0))
    label("nitride spacer", (-d.gh - 19, 150.0, 0), root, D.beats(0))
    D.gate_glow(root, m, d, D.beats(1, 4))
    D.field(root, m, d, D.beats(1, 3))
    D.majority_dots(root, m, d, D.beats(0, 4), D.beats(0, 2))
    label("gate at ~0.75 V", (0.0, 140.0, 0), root, D.beats(1))
    label("field crosses the oxide", (0.0, 60.0, D.CZ), root, D.beats(1))
    label("no current into the gate", (d.gh + 19, 150.0, 0), root, D.beats(1))
    D.channel(root, m, d, D.beats(2, 4))
    label("electron channel", (20.0, -8.0, 2), root, D.beats(2))
    label("holes pushed down", (-60.0, -88.0, D.CZ), root, D.beats(2))
    D.outline(root, m, "hik_hl", (-d.gh - 2, 4.0), (d.gh + 2, 19.0), D.beats(3), t=3.0)
    D.outline(root, m, "hik_l", (-d.gh - 2, 19.0), (-d.gh + 11, 167.0), D.beats(3), t=3.0)
    label("high-k: thicker, same pull", (-d.gh + 4, 60.0, 0), root, D.beats(3))
    label("acts like ~1 nm of SiO2", (0.0, 12.0, 4), root, D.beats(3))
    c = D.frame((-170.0, -100.0, -40.0), (170.0, 200.0, 0.0), pitch=0.10, pad=1.08)
    return [c, c, c, c]


def zoom_b(m, root):
    """b subthreshold, threshold and on, with a current gauge that climbs decade by decade."""
    d = _dev(m, root)
    D.meter(root, m, "id", 560.0, -200.0, [0.12, 0.45, 0.95])
    label("drain current (log)", (560.0, 130.0, -10), root, D.beats(0, 3))
    D.gate_glow(root, m, d, D.beats(0, 2), weak=True)
    D.depletion(root, m, d, D.beats(0, 3), junctions=False)
    D.leak(root, m, d, 0, n=6, y=-22.0)
    label("VG below Vt", (0.0, 120.0, 0), root, D.beats(0))
    label("few electrons over the barrier", (-40.0, -22.0, D.CZ), root, D.beats(0))
    label("leakage", (560.0, -170.0, -10), root, D.beats(0))
    D.channel(root, m, d, D.beats(1), weak=True)
    D.flow(root, m, d, 1, n=5, life=150)
    label("VG = Vt ~0.3 V", (0.0, 120.0, 0), root, D.beats(1))
    label("inversion starts", (20.0, -8.0, 2), root, D.beats(1))
    D.gate_glow(root, m, d, D.beats(2))
    D.channel(root, m, d, D.beats(2))
    D.flow(root, m, d, 2, n=16, life=90)
    label("VG ~0.75 V: fully on", (0.0, 120.0, 0), root, D.beats(2))
    label("~5-6 decades above leakage", (560.0, 90.0, -10), root, D.beats(2))
    p = D.frame((-440.0, -260.0, -40.0), (620.0, 340.0, 0.0), pitch=0.10, pad=1.06)
    return [p, p, p]


def zoom_c(m, root):
    """c saturation: an even channel, the drain end thinning, pinch-off at the drain."""
    d = _dev(m, root)
    D.gate_glow(root, m, d, D.beats(0, 3))
    D.channel(root, m, d, D.beats(0))
    D.flow(root, m, d, 0, n=10, life=130)
    label("drain ~0.05 V: even channel", (0.0, -8.0, 2), root, D.beats(0))
    label("acts like a resistor", (d.ct_x, 250.0, 0), root, D.beats(0))
    D.pinch(root, m, d, D.beats(1), thin=True, name="nm_thin")
    D.flow(root, m, d, 1, n=12, life=110)
    label("drain end thins", (0.6 * d.ext_in, -8.0, 2), root, D.beats(1))
    label("drain voltage rising", (d.ct_x, 250.0, 0), root, D.beats(1))
    D.pinch(root, m, d, D.beats(2))
    D.depletion(root, m, d, D.beats(2), under_gate=False, reach=30.0, name="nm_dep_sat")
    D.flow(root, m, d, 2, n=12, life=110)
    label("pinch-off at the drain", (0.45 * d.ext_in, -8.0, 2), root, D.beats(2))
    label("drain ~0.75 V: current levels off", (d.ct_x, 250.0, 0), root, D.beats(2))
    p = D.frame_dev(d, x0=-420, x1=420, bottom=-180, top=300)
    return [p, p, p]


def zoom_d(m, root):
    """d short channels: a long gate owns the barrier; a short one lets the drain reach the source."""
    D.mats(m)
    dl = D.planar(m, root, "n", 0.0, name="nm_long", gh=110.0, sd_out=400.0, half=480.0, iv=D.beats(0))
    D.depletion(root, m, dl, D.beats(0), name="long_dep")
    label("long gate", (0.0, 120.0, 0), root, D.beats(0))
    label("gate's depletion owns the barrier", (0.0, -60.0, 2), root, D.beats(0))
    label("drain field stays near the drain", (dl.ct_x, -128.0, 0), root, D.beats(0))
    d = D.planar(m, root, "n", 0.0, name="nm_short", gh=38.0, iv=D.beats(1, 3))
    D.depletion(root, m, d, D.beats(1), reach=70.0, name="short_dep1")
    D.depletion(root, m, d, D.beats(2), reach=105.0, name="short_dep2")
    D.arrows(root, m, "dibl1", [((d.sd_in + 60, -60, D.CZ + 6), (-10, -60, D.CZ + 6))], D.beats(1))
    D.arrows(root, m, "dibl2", [((d.sd_in + 60, -60, D.CZ + 6), (-d.ext_in - 10, -60, D.CZ + 6)),
                                ((d.sd_in + 60, -95, D.CZ + 6), (-d.ext_in - 10, -95, D.CZ + 6))], D.beats(2))
    D.leak(root, m, d, 1, n=5, y=-40.0)
    D.leak(root, m, d, 2, n=12, y=-40.0, life=110)
    label("short gate", (0.0, 120.0, 0), root, D.beats(1, 3))
    label("drain field reaches the source", (d.sd_in + 40, -60.0, D.CZ), root, D.beats(1))
    label("Vt falls: leakage", (-d.ext_in - 20, -40.0, D.CZ), root, D.beats(1))
    label("higher drain voltage", (d.ct_x, 250.0, 0), root, D.beats(2))
    label("barrier lower, more leakage", (-d.ext_in - 20, -40.0, D.CZ), root, D.beats(2))
    return [D.frame_dev(dl, x0=-480, x1=480, bottom=-200), D.frame_dev(d, x0=-420, x1=420, bottom=-200),
            D.frame_dev(d, x0=-420, x1=420, bottom=-200)]


def zoom_e(m, root):
    """e dopants and strain: the dopant atoms, Si:P and the halo pockets, tensile strain."""
    return sec6(m, root)


# ---- sections 1-10 --------------------------------------------------------------------------
# The sections are close-ups of one detailed NMOS in cut-away (chip_mos_detail): each section
# function builds its pieces and returns one camera pose per beat.

def sec1(m, root):
    """1 what happens: off, the gate high and the channel forming, then the electrons flowing."""
    d = _dev(m, root)
    D.majority_dots(root, m, d, D.beats(0, 3), D.beats(0))
    D.gate_glow(root, m, d, D.beats(1, 3))
    D.field(root, m, d, D.beats(1))
    D.channel(root, m, d, D.beats(1, 3))
    D.flow(root, m, d, 2, n=12)
    label("n+ source: 0 V", (-d.ct_x, -60.0, 0), root, D.beats(0))
    label("n+ drain", (d.ct_x, -60.0, 0), root, D.beats(0))
    label("gate 0 V: off", (0.0, 120.0, 0), root, D.beats(0))
    label("p-well: holes", (-230.0, -180.0, 0), root, D.beats(0))
    label("gate ~0.75 V", (0.0, 120.0, 0), root, D.beats(1))
    label("field through the oxide", (0.0, 60.0, D.CZ), root, D.beats(1))
    label("electron channel", (25.0, -8.0, 2), root, D.beats(1))
    label("electrons: source to drain", (-d.ct_x, 180.0, D.CZ), root, D.beats(2))
    label("drain ~0.75 V", (d.ct_x, 250.0, 0), root, D.beats(2))
    label("channel on", (0.0, -8.0, 2), root, D.beats(2))
    whole = D.frame_dev(d)
    return [whole, _gate_close(d), whole]


def sec2(m, root):
    """2 the parts: source, gate stack, drain, p-well, then halos, spacers and STI."""
    d = _dev(m, root)
    D.hl(root, m, d, "source", D.beats(0), pad=6.0)
    label("n+ source", (-d.ct_x, -70.0, 0), root, D.beats(0))
    label("Si:P raised epitaxy", (-d.ct_x - 60, 22.0, 0), root, D.beats(0))
    label("silicide", (-d.ct_x + 60, 48.0, 0), root, D.beats(0))
    label("tungsten contact", (-d.ct_x, 250.0, 0), root, D.beats(0))
    label("fill metal", (0.0, 120.0, 0), root, D.beats(1))
    label("work-function metal", (d.gh - 15, 90.0, 0), root, D.beats(1))
    label("high-k HfO2", (-d.gh + 4, 60.0, 0), root, D.beats(1))
    label("SiO2 interlayer", (-30.0, 3.0, 0), root, D.beats(1))
    label("nitride cap", (0.0, 178.0, 0), root, D.beats(1))
    D.hl(root, m, d, "drain", D.beats(2), pad=6.0)
    label("n+ drain: the output", (d.ct_x, -70.0, 0), root, D.beats(2))
    label("contact to the output", (d.ct_x, 250.0, 0), root, D.beats(2))
    D.outline(root, m, "well_hl", (-d.half + 70, -228.0), (d.half - 70, -118.0), D.beats(3))
    D.majority_dots(root, m, d, D.beats(3), D.beats(3))
    label("p-well: boron-doped", (-200.0, -170.0, 0), root, D.beats(3))
    label("holes: majority carrier", (130.0, -150.0, D.CZ), root, D.beats(3))
    label("p substrate", (0.0, -285.0, 0), root, D.beats(3))
    D.hl(root, m, d, "halo-1", D.beats(4), pad=3.0)
    D.hl(root, m, d, "halo1", D.beats(4), pad=3.0)
    label("halo pocket", (-d.ext_in - 5, -55.0, 0), root, D.beats(4))
    label("extension", (d.ext_in + 25, -18.0, 0), root, D.beats(4))
    label("nitride spacer", (-d.gh - 19, 140.0, 0), root, D.beats(4))
    label("STI oxide", (d.half - 35, -100.0, 0), root, D.beats(4))
    whole = D.frame_dev(d)
    return [D.frame_dev(d, x0=-470, x1=40, bottom=-150, top=350), _gate_close(d),
            D.frame_dev(d, x0=-40, x1=470, bottom=-150, top=350), whole, whole]


def sec3(m, root):
    """3 one switching cycle: off, depletion, inversion, linear then saturation, turn-off."""
    d = _dev(m, root)
    D.majority_dots(root, m, d, D.beats(0, 5), [(F(0, 0), F(1, 0)), (F(4, 0.35), F(5, 0))])
    D.depletion(root, m, d, D.beats(0), under_gate=False)
    label("VG = 0 V", (0.0, 120.0, 0), root, D.beats(0))
    label("reverse-biased junction", (d.ct_x, -128.0, 0), root, D.beats(0))
    D.gate_glow(root, m, d, D.beats(1), weak=True)
    D.depletion(root, m, d, D.beats(1, 4), name="nm_dep_on")
    label("0 < VG < Vt", (0.0, 120.0, 0), root, D.beats(1))
    label("depletion: holes pushed down", (0.0, -50.0, 0), root, D.beats(1))
    D.gate_glow(root, m, d, D.beats(2, 4))
    D.field(root, m, d, D.beats(2))
    D.channel(root, m, d, D.beats(2))
    label("VG > Vt", (0.0, 120.0, 0), root, D.beats(2))
    label("inversion layer", (20.0, -8.0, 2), root, D.beats(2))
    D.channel(root, m, d, [(F(3, 0), F(3, 0.5))], name="nm_lin")
    D.pinch(root, m, d, [(F(3, 0.5), F(4, 0))])
    D.flow(root, m, d, 3, n=12, u1=0.8)
    label("linear: even channel", (-20.0, -8.0, 2), root, [(F(3, 0), F(3, 0.5))])
    label("saturation: pinch-off", (0.5 * d.ext_in, -8.0, 2), root, [(F(3, 0.5), F(4, 0))])
    label("electrons", (-d.ct_x, 200.0, D.CZ), root, D.beats(3))
    D.leak(root, m, d, 4, n=5)
    D.gate_glow(root, m, d, [(F(4, 0), F(4, 0.25))], weak=True, name="nm_fall")
    D.channel(root, m, d, [(F(4, 0), F(4, 0.25))], weak=True, name="nm_fade")
    label("VG back to 0 V", (0.0, 120.0, 0), root, D.beats(4))
    label("channel empties", (0.0, -8.0, 2), root, D.beats(4))
    label("leakage remains", (-120.0, -52.0, D.CZ), root, D.beats(4))
    whole = D.frame_dev(d)
    close = D.frame_dev(d, x0=-330, x1=330, bottom=-190, top=230)
    return [whole, close, close, whole, close]


def sec4(m, root):
    """4 threshold: subthreshold leakage, the channel at threshold, full current above it."""
    d = _dev(m, root)
    D.gate_glow(root, m, d, D.beats(0, 2), weak=True)
    D.depletion(root, m, d, D.beats(0, 3), junctions=False)
    D.leak(root, m, d, 0, n=6, y=-22.0)
    label("VG ~0.15 V: below Vt", (0.0, 120.0, 0), root, D.beats(0))
    label("barrier: few electrons cross", (-40.0, -22.0, D.CZ), root, D.beats(0))
    D.channel(root, m, d, D.beats(1), weak=True)
    D.flow(root, m, d, 1, n=5, life=150)
    label("VG = Vt ~0.3 V", (0.0, 120.0, 0), root, D.beats(1))
    label("thin inversion layer", (20.0, -8.0, 2), root, D.beats(1))
    D.gate_glow(root, m, d, D.beats(2))
    D.channel(root, m, d, D.beats(2))
    D.flow(root, m, d, 2, n=16, life=90)
    label("VG ~0.75 V: fully on", (0.0, 120.0, 0), root, D.beats(2))
    label("strong channel", (20.0, -8.0, 2), root, D.beats(2))
    label("full current", (d.ct_x, 220.0, D.CZ), root, D.beats(2))
    whole = D.frame_dev(d, x0=-420, x1=420, bottom=-200)
    return [whole, whole, whole]


def sec5(m, root):
    """5 short channels and body bias, then the gate wrapped round a fin."""
    d = _dev(m, root, iv=D.beats(0, 2), tap=True)
    D.depletion(root, m, d, D.beats(0), reach=110.0)
    D.arrows(root, m, "dibl", [((d.ext_in + 40, -60, D.CZ + 6), (-20, -60, D.CZ + 6)),
                               ((d.ext_in + 40, -95, D.CZ + 6), (-20, -95, D.CZ + 6))], D.beats(0))
    D.leak(root, m, d, 0, n=8, y=-40.0)
    label("drain field reaches under", (d.ext_in + 30, -95.0, D.CZ), root, D.beats(0))
    label("source barrier lowered", (-d.ext_in, -40.0, D.CZ), root, D.beats(0))
    label("drain ~0.75 V", (d.ct_x, 250.0, 0), root, D.beats(0))
    D.hl(root, m, d, "tap", D.beats(1), pad=6.0)
    D.hl(root, m, d, "tap_ct", D.beats(1), pad=4.0)
    D.depletion(root, m, d, D.beats(1), junctions=False, deep=130.0, name="nm_dep_bb")
    D.arrows(root, m, "bias", [((d.half + 65, -120, D.CZ + 6), (120, -150, D.CZ + 6))], D.beats(1))
    label("body tap (p+)", (d.half + 65, 200.0, 0), root, D.beats(1))
    label("well bias shifts Vt", (230.0, -160.0, D.CZ), root, D.beats(1))
    label("wider depletion", (0.0, -110.0, 0), root, D.beats(1))
    _, zs, ext = D.finfet(m, root, "n", nfins=2, iv=D.beats(2), lit=D.beats(2))
    label("silicon fin", (-4.0, 60.0, zs[0]), root, D.beats(2))
    label("gate wraps 3 sides", (-4.0, D.FIN_H + 40, zs[1] + 40), root, D.beats(2))
    label("high-k", (-4.0, 80.0, zs[1] + D.FIN_W / 2 + 4), root, D.beats(2))
    label("n+ epitaxy", (300.0, D.FIN_H + 10, zs[1] + 50), root, D.beats(2))
    return [D.frame_dev(d, x0=-300, x1=460, bottom=-200), D.frame_dev(d, x0=-200, x1=d.half + 140, bottom=-330),
            D.frame(ext[0], ext[1], yaw=-0.75, pitch=0.25, pad=1.05)]


def sec6(m, root):
    """6 dopants and strain: the dopant atoms, the halos and Si:P, then tensile strain."""
    d = _dev(m, root)
    D.dopants(root, m, d, D.beats(0, 2))
    D.hl(root, m, d, "ext-1", D.beats(0), pad=4.0)
    D.hl(root, m, d, "ext1", D.beats(0), pad=4.0)
    label("arsenic: shallow extension", (-d.ext_in - 20, -18.0, D.CZ), root, D.beats(0))
    label("phosphorus: deep S/D", (d.ct_x, -95.0, D.CZ), root, D.beats(0))
    D.hl(root, m, d, "epi-1", D.beats(1), pad=4.0)
    D.hl(root, m, d, "epi1", D.beats(1), pad=4.0)
    D.hl(root, m, d, "halo-1", D.beats(1), pad=3.0)
    D.hl(root, m, d, "halo1", D.beats(1), pad=3.0)
    label("Si:P epi ~1e21 /cm3", (d.ct_x, 22.0, 0), root, D.beats(1))
    label("halo pocket (boron)", (-d.ext_in - 5, -55.0, 0), root, D.beats(1))
    D.strain(root, m, d, D.beats(2))
    D.gate_glow(root, m, d, D.beats(2))
    D.channel(root, m, d, D.beats(2))
    D.flow(root, m, d, 2, n=14, life=80)
    label("tensile strain", (-120.0, -60.0, D.CZ), root, D.beats(2))
    label("faster electrons", (d.ct_x, 200.0, D.CZ), root, D.beats(2))
    close = D.frame_dev(d, x0=-420, x1=420, bottom=-180, top=200)
    return [close, close, close]


ARR = dict(cols=24, rows=3, pitch=90.0, row_h=520.0)


def sec7(m, root):
    """7 transistor count: one NMOS, rows of them from above, then the wiring over them."""
    d = _dev(m, root, iv=D.beats(0))
    D.gate_glow(root, m, d, D.beats(0))
    D.channel(root, m, d, D.beats(0))
    D.flow(root, m, d, 0, n=10)
    label("one NMOS: one switch", (0.0, 120.0, 0), root, D.beats(0))
    label("~0.1 um across (estimate)", (0.0, -200.0, 0), root, D.beats(0))
    D.array(m, root, "arr", iv=D.beats(1, 3), wires_iv=D.beats(2), **ARR)
    W, H = ARR["cols"] * ARR["pitch"], ARR["rows"] * ARR["row_h"]
    label("gate lines", (W * 0.52, H - 60, 6), root, D.beats(1))
    label("NMOS rows (blue)", (W * 0.25, 120.0, 0), root, D.beats(1))
    label("PMOS rows (pink)", (W * 0.75, 360.0, 0), root, D.beats(1))
    label("B200: ~208 billion", (W * 0.5, H * 0.55, 6), root, D.beats(1))
    label("copper wiring on top", (W * 0.4, 120.0 + ARR["row_h"], 26), root, D.beats(2))
    label("contacts down to each", (W * 0.7, H * 0.8, 40), root, D.beats(2))
    arr = D.frame((0.0, -20.0, -16.0), (W, H, 40.0), pitch=0.0, pad=1.05)
    return [D.frame_dev(d), arr, arr]


def sec8(m, root):
    """8 who makes it: a FinFET (TSMC), stacked sheets (Intel 18A), a simulated device."""
    D.mats(m)
    _, zs, e0 = D.finfet(m, root, "n", nfins=2, iv=D.beats(0), lit=D.beats(0), name="f8")
    label("TSMC N3: FinFET", (-4.0, D.FIN_H + 72, zs[0]), root, D.beats(0))
    label("fin ~5-7 nm wide", (-4.0, 50.0, zs[1]), root, D.beats(0))
    _, e1 = D.gaa(m, root, "n", iv=D.beats(1), lit=D.beats(1), name="g8")
    label("Intel 18A: RibbonFET", (-4.0, D.SHEET_Y[-1] + 80, 0.0), root, D.beats(1))
    label("stacked sheets", (-4.0, D.SHEET_Y[1] + 15, -40.0), root, D.beats(1))
    label("gate all round", (-4.0, D.SHEET_Y[0] - 8, 100.0), root, D.beats(1))
    d = D.planar(m, root, "n", 0.0, name="nm", iv=D.beats(2))
    D.gate_glow(root, m, d, D.beats(2))
    D.channel(root, m, d, D.beats(2))
    g = []
    for i, xx in enumerate(range(-420, 421, 60)):
        g.append(((xx, -230, 4.0), (xx, 200, 4.0)))
    for yy in range(-220, 201, 40):
        g.append(((-420, yy, 4.0), (420, yy, 4.0)))
    D.arrows(root, m, "mesh", g, D.beats(2), mt="mos_grid", r=1.2, tip=1.6)
    D.box_on(root, "pot", (-d.ext_in - 30, -90, -40), (d.ext_in + 30, -16, 3.0), m["mos_dep"], D.beats(2))
    label("Synopsys, Cadence: TCAD mesh", (-300.0, 150.0, 4), root, D.beats(2))
    label("solved potential", (0.0, -60.0, 3), root, D.beats(2))
    return [D.frame(e0[0], e0[1], yaw=-0.75, pitch=0.25, pad=1.05),
            D.frame(e1[0], e1[1], yaw=-0.75, pitch=0.25, pad=1.05), D.frame_dev(d)]


def sec9(m, root):
    """9 chokepoints and risks: leakage and variability, contact resistance, very few fabs."""
    d = _dev(m, root, iv=D.beats(0, 2))
    D.leak(root, m, d, 0, n=8)
    D.gate_leak(root, m, d, 0)
    g = empty("rnd", root)
    for i, (xx, yy) in enumerate(((-30, -30), (20, -55), (-5, -80), (35, -20))):
        D.ball(f"rdop{i}", (xx, yy, D.CZ + 4), 10.0, m["mos_atom_n"], g, 8)
    show(g, D.beats(0))
    label("leakage under the gate", (-120.0, -52.0, D.CZ), root, D.beats(0))
    label("gate-oxide tunnelling", (-15.0, 40.0, D.CZ), root, D.beats(0))
    label("few dopants: Vt varies", (30.0, -85.0, D.CZ), root, D.beats(0))
    D.gate_glow(root, m, d, D.beats(1))
    D.channel(root, m, d, D.beats(1))
    D.flow(root, m, d, 1, n=10, life=150)
    for s in (-1, 1):
        D.hl(root, m, d, f"ct{s}", D.beats(1), pad=5.0, mt="mos_warn")
        D.box_on(root, f"hot{s}", (s * d.ct_x - 34, d.sil_top - 6, -40), (s * d.ct_x + 34, d.sil_top + 6, 4.0),
                 m["mos_hot"], D.beats(1))
    label("contact resistance", (d.ct_x, 250.0, 0), root, D.beats(1))
    label("silicide interface", (-d.ct_x, d.sil_top, 4), root, D.beats(1))
    e = D.makers_row(m, root, "n", D.beats(2))
    label("TSMC: N3 FinFET, N2 GAA", (-4.0, 250.0, D.ROW_Z[0]), root, D.beats(2))
    label("Intel: 18A", (-4.0, 250.0, D.ROW_Z[1]), root, D.beats(2))
    label("Samsung: SF3, SF2 GAA", (-4.0, 250.0, D.ROW_Z[2]), root, D.beats(2))
    close = D.frame_dev(d, x0=-420, x1=420, bottom=-180)
    return [close, close, D.row_pose(e)]


def sec10(m, root):
    """10 sources: each beat lights the part its sources back."""
    D.mats(m)
    D.array(m, root, "arr", iv=D.beats(0), **ARR)
    W, H = ARR["cols"] * ARR["pitch"], ARR["rows"] * ARR["row_h"]
    label("[1]-[3] [11] transistor counts", (W * 0.5, H * 0.55, 6), root, D.beats(0))
    d = D.planar(m, root, "n", 0.0, name="nm", iv=D.beats(1, 3))
    D.dopants(root, m, d, D.beats(1))
    for k in ("source", "drain"):
        D.hl(root, m, d, k, D.beats(1), pad=6.0)
    label("[4] As vs P patents", (-d.ct_x, -60.0, D.CZ), root, D.beats(1))
    label("[5] Si:P patent and ECS paper", (d.ct_x, 22.0, D.CZ), root, D.beats(1))
    D.gate_glow(root, m, d, D.beats(2), weak=True)
    D.depletion(root, m, d, D.beats(2), reach=80.0)
    D.hl(root, m, d, "stack", D.beats(2), pad=4.0)
    label("[6] swing and DIBL: UCSB, arXiv", (0.0, 120.0, 0), root, D.beats(2))
    e = D.makers_row(m, root, "n", D.beats(3))
    label("[7] Intel 18A", (-4.0, 250.0, D.ROW_Z[1]), root, D.beats(3))
    label("[8] TSMC 6-K", (-4.0, 250.0, D.ROW_Z[0]), root, D.beats(3))
    label("[9] [10] NVIDIA, Synopsys, Cadence", (-4.0, 250.0, D.ROW_Z[2]), root, D.beats(3))
    arr = D.frame((0.0, -20.0, -16.0), (W, H, 40.0), pitch=0.0, pad=1.05)
    return [arr, D.frame_dev(d), D.frame_dev(d, x0=-330, x1=330, bottom=-190, top=230),
            D.row_pose(e)]


# ---- registry and entry point ----------------------------------------------------------------

# key -> (beats, camera poses, builder)
SCENES = {
    "zoom_a": (4, None, zoom_a),
    "zoom_b": (3, None, zoom_b),
    "zoom_c": (3, None, zoom_c),
    "zoom_d": (3, None, zoom_d),
    "zoom_e": (3, None, zoom_e),
    "sec1": (3, None, sec1),
    "sec2": (5, None, sec2),
    "sec3": (5, None, sec3),
    "sec4": (3, None, sec4),
    "sec5": (3, None, sec5),
    "sec6": (3, None, sec6),
    "sec7": (3, None, sec7),
    "sec8": (3, None, sec8),
    "sec9": (3, None, sec9),
    "sec10": (4, None, sec10),
}


def scene(key):
    beats, poses, fn = SCENES[key]
    name = f"nmos_{key}"
    m, root = start(name, beats, page="chip")
    C.mats(m)
    D.mats(m)
    out = fn(m, root)
    C.glide_camera(root, out if poses is None else poses)
    finish(name, page="chip")


if __name__ == "__main__":
    key = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "overview"
    if key == "overview":
        build()
        finish("nmos", page="chip")
    else:
        scene(key)
