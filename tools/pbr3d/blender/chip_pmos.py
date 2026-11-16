"""CHIP scenes for the PMOS node: the overview (the whole chip, then in on the PMOS transistor),
the zoom-ins a-e and the numbered sections 1-10. Each is one Blender scene and one GLB.

Run from the repo root, one scene per run (no argument builds the overview):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_pmos.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_pmos.py -- zoom_a
    blender -b --factory-startup --python tools/pbr3d/blender/chip_pmos.py -- sec4

Writes blender/chip_pmos[_<key>].blend and assets/chip_pmos[_<key>].glb. One beat is 8 s.

The PMOS is a p+ source and drain in n-type silicon. It switches ON when its gate is LOW: holes
form a channel under the gate and flow from the VDD side, across the channel, to the output side.
Every scene uses the detailed transistors of chip_mos_detail.py; the overview swaps them into the
whole chip in place of chip_kit's plain ones.

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
import chip_mos_detail as D  # noqa: E402
from chip_kit import F, empty, label, show  # noqa: E402

BEATS = 6
WHOLE = C.WHOLE


def build():
    """The overview: the whole chip, in on the detailed PMOS (gate low and the hole channel,
    holes flowing, gate high and off), out to the pair (NMOS on, PMOS off), out to the chip."""
    m, root = start("pmos", BEATS, page="chip")
    C.mats(m)
    D.mats(m)
    dn, d = D.in_chip(m, root)
    cx = d.cx
    D.outline(root, m, "pmos_pick", (cx - d.half - 30, -350.0), (cx + d.half + 30, d.ct_top + 40),
              [(F(0, 0), F(1, 0.2)), (F(5, 0.2), F(6, 0))], t=22.0, z=12.0)
    whole = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
    label("PMOS", (cx, d.ct_top + 60, 12), root, whole)
    label("VDD in", (C.VDD_X, C.BUMP_Y + 60, -60), root, whole)
    D.channel(root, m, d, [(F(0, 0), F(1, 0)), (F(1, 0.35), F(3, 0.05)), (F(5, 0), F(6, 0))])
    D.majority_dots(root, m, d, D.beats(1, 5), [(F(3, 0.2), F(5, 0))])
    # 1 gate low: the channel forms
    label("p+ source: VDD", (cx + d.ct_x, -70.0, 0), root, D.beats(1))
    label("p+ drain: output", (cx - d.ct_x, -70.0, 0), root, D.beats(1))
    label("gate 0 V: on", (cx, 120.0, 0), root, D.beats(1))
    label("n-well: electrons", (cx - 230.0, -180.0, D.CZ), root, D.beats(1))
    label("hole channel", (cx - 20, -8.0, 2), root, [(F(1, 0.35), F(2, 0))])
    # 2 holes ride down the VDD contact, across, and up to the output
    D.beads(root, "holes", D.carrier_path(d), 12, 10.0, m["mos_hole"], 2, 0.03, 0.8, 140)
    label("holes from VDD", (cx + d.ct_x, 300.0, D.CZ), root, D.beats(2))
    label("across the channel", (cx, -8.0, 2), root, D.beats(2))
    label("up to the output", (cx - d.ct_x, 300.0, D.CZ), root, D.beats(2))
    # 3 gate high: the PMOS is off (and in the pair, the NMOS is on)
    hi = [(F(3, 0), F(5, 0.2))]
    D.gate_glow(root, m, d, hi)
    D.gate_glow(root, m, dn, hi)
    label("gate high ~0.75 V: off", (cx, 120.0, 0), root, D.beats(3))
    label("channel gone", (cx, -8.0, 2), root, D.beats(3))
    label("electrons back under the gate", (cx + 60, -88.0, D.CZ), root, D.beats(3))
    # 4 the pair: NMOS on pulling the output down, PMOS off
    D.channel(root, m, dn, D.beats(4))
    D.beads(root, "elec", D.carrier_path(dn), 12, 10.0, m["mos_elec"], 4, 0.03, 0.8, 110)
    label("NMOS on", (dn.cx, 120.0, 0), root, D.beats(4))
    label("PMOS off", (cx, 120.0, 0), root, D.beats(4))
    label("shared input: high", (0.0, 300.0, 0), root, D.beats(4))
    label("one is always off", (0.0, -420.0, 0), root, D.beats(4))
    label("gate low again: PMOS on", (cx, -420.0, 0), root, D.beats(5))
    zoom = D.frame_dev(d, bottom=-300, pad=1.16)
    pair = D.frame((dn.cx - dn.half, -330.0, -40.0), (cx + d.half, 460.0, 0.0), pitch=0.10, pad=1.04)
    C.glide_camera(root, [WHOLE, zoom, zoom, zoom, pair, WHOLE])


# ---- zoom-ins a-e ---------------------------------------------------------------------------------
# Close-ups of the detailed PMOS (chip_mos_detail), like the sections. Zooms b, d and e show the
# same pictures as sections 6, 5 and 7; a and c are their own. Each returns one pose per beat.

def zoom_a(m, root):
    """a the n-well and its tap: the well round the PMOS, the tap wired to VDD, only the channel
    conducts."""
    d = _dev(m, root, tap=True)
    D.outline(root, m, "well_hl", (-d.half + 70, -228.0), (d.half + 120, -118.0), D.beats(0))
    D.majority_dots(root, m, d, D.beats(0, 3), D.beats(0, 2))
    label("n-well (phosphorus)", (-200.0, -170.0, 0), root, D.beats(0))
    label("electrons: majority carrier", (130.0, -150.0, D.CZ), root, D.beats(0))
    label("p substrate", (0.0, -285.0, 0), root, D.beats(0))
    tap_x = d.half + 65
    rail = D.arch((d.ct_x, d.ct_top, -60.0), (tap_x, d.ct_top, -60.0), 70.0, 10)
    D.wire("vdd_rail", rail, 12.0, m["mos_vdd"], root, D.beats(1, 3))
    D.hl(root, m, d, "tap", D.beats(1), pad=6.0)
    D.hl(root, m, d, "tap_ct", D.beats(1), pad=4.0)
    label("n+ tap", (tap_x, -50.0, 0), root, D.beats(1))
    label("wired to VDD", (0.5 * (d.ct_x + tap_x), d.ct_top + 70, -60), root, D.beats(1))
    label("well at VDD", (150.0, -170.0, 0), root, D.beats(1))
    D.depletion(root, m, d, D.beats(2), under_gate=False)
    D.channel(root, m, d, D.beats(2))
    D.flow(root, m, d, 2, n=10, life=140)
    label("only the channel conducts", (0.0, -8.0, 2), root, D.beats(2))
    label("blocked junction", (-d.ct_x, -128.0, 0), root, D.beats(2))
    return [D.frame_dev(d, x0=-440, x1=d.half + 130, bottom=-330),
            D.frame_dev(d, x0=-260, x1=d.half + 140, bottom=-240, top=d.ct_top + 90),
            D.frame_dev(d, x0=-440, x1=d.half + 130, bottom=-200)]


def zoom_b(m, root):
    """b SiGe strain: the regrown SiGe:B, the squeeze, faster holes (as section 6)."""
    return sec6(m, root)


def zoom_c(m, root):
    """c the CMOS inverter: an arched output wire to the next gate's input, charged through the
    PMOS (input 0) and discharged through the NMOS (input 1)."""
    D.mats(m)
    dn, dp, _ = D.inverter(m, root, D.beats(0, 3), name="zc", wires=False)
    top = dn.ct_top
    zw = D.CZ - 6
    xn, xp = dn.src(1), dp.src(-1)
    out = D.arch((xn, top, zw), (xp, top, zw), 120.0, 12)
    apex = out[6]
    load_y = apex[1] + 120
    D.wire("out_arch", out, 9.0, m["mos_cu"], root)
    D.wire("out_up", [apex, (apex[0], load_y, zw)], 9.0, m["mos_cu"], root)
    D.box_on(root, "load_a", (-80, load_y, -40), (80, load_y + 12, zw), m["mos_cu"], D.beats(0, 3))
    D.box_on(root, "load_b", (-80, load_y + 36, -40), (80, load_y + 48, zw), m["mos_cu"], D.beats(0, 3))
    g = empty("zc_in", root)
    for i, d in enumerate((dn, dp)):
        D.box(f"zc_gct{i}", (d.cx - 18, d.ytop, -240), (d.cx + 18, 290, -200), m["mos_w"], g)
    D.box("zc_inbar", (dn.cx - 30, 270, -240), (dp.cx + 30, 300, -200), m["mos_cu"], g)
    D.box("zc_gnd", (dn.src(-1) - 50, top, -120), (dn.src(-1) + 50, top + 30, 0), m["mos_gnd"], g)
    D.box("zc_vdd", (dp.src(1) - 50, top, -120), (dp.src(1) + 50, top + 30, 0), m["mos_vdd"], g)
    label("PMOS: pull-up to VDD", (dp.cx, -150.0, 0), root, D.beats(0))
    label("NMOS: pull-down to ground", (dn.cx, -150.0, 0), root, D.beats(0))
    label("output wire", (out[3][0], out[3][1], zw), root, D.beats(0))
    label("load: the next gate", (0.0, load_y + 24, zw), root, D.beats(0, 3))
    label("input (both gates)", (0.0, 285.0, -200), root, D.beats(0))
    label("VDD", (dp.src(1), top + 15, 0), root, D.beats(0, 3))
    label("ground", (dn.src(-1), top + 15, 0), root, D.beats(0, 3))
    # input 0: the PMOS conducts, holes ride from VDD to the output and up to the load
    D.channel(root, m, dp, D.beats(1))
    hp = D.carrier_path(dp)[:3] + [(xp, top, D.CZ)] + [(p[0], p[1], D.CZ) for p in out[6:][::-1]] + [(apex[0], load_y, D.CZ)]
    D.beads(root, "zc_holes", hp, 12, 10.0, m["mos_hole"], 1, 0.03, 0.7, 150)
    label("input 0 V: PMOS on", (dp.cx, 120.0, 0), root, D.beats(1))
    label("output charges to VDD", (out[9][0], out[9][1], zw), root, D.beats(1))
    # input 1: the NMOS conducts, electrons ride from ground to the output: the load discharges
    D.gate_glow(root, m, dn, D.beats(2))
    D.gate_glow(root, m, dp, D.beats(2))
    D.channel(root, m, dn, D.beats(2))
    hn = D.carrier_path(dn)[:3] + [(xn, top, D.CZ)] + [(p[0], p[1], D.CZ) for p in out[:7]] + [(apex[0], load_y, D.CZ)]
    D.beads(root, "zc_elec", hn, 14, 10.0, m["mos_elec"], 2, 0.03, 0.7, 130)
    label("input high: NMOS on", (dn.cx, 120.0, 0), root, D.beats(2))
    label("output pulled to ground", (out[3][0], out[3][1], zw), root, D.beats(2))
    p = D.frame((dn.cx - dn.half, -240.0, -40.0), (dp.cx + dp.half, load_y + 60, 0.0), pitch=0.10, pad=1.05)
    return [p, p, p]


def zoom_d(m, root):
    """d width ratio: slow holes, a wider PMOS, more fins (as section 5)."""
    return sec5(m, root)


def zoom_e(m, root):
    """e GAA PFET and germanium: silicon, SiGe and germanium sheets (as section 7)."""
    return sec7(m, root)


def _dev(m, root, iv=None, **kw):
    D.mats(m)
    return D.planar(m, root, "p", 0.0, name="pm", iv=iv, **kw)


# ---- numbered sections --------------------------------------------------------------------------
# The sections are close-ups of one detailed PMOS in cut-away (chip_mos_detail): SiGe:B source
# and drain in an n-well, the source on the right (the VDD side), holes flowing right to left.
# Each section function builds its pieces and returns one camera pose per beat.


def _inv_pose(e, pad=1.06):
    return D.frame(e[0], e[1], pitch=0.10, pad=pad)


CELL_W, CELL_H = 420.0, 600.0


def sec1(m, root):
    """1 what happens: the PMOS off (gate high), on (gate low, holes flow), then paired."""
    d = _dev(m, root, iv=D.beats(0, 2))
    D.majority_dots(root, m, d, D.beats(0, 2), D.beats(0, 2))
    D.gate_glow(root, m, d, D.beats(0))
    label("p+ source: VDD", (d.ct_x, -60.0, 0), root, D.beats(0))
    label("p+ drain: output", (-d.ct_x, -60.0, 0), root, D.beats(0))
    label("gate ~0.75 V: off", (0.0, 120.0, 0), root, D.beats(0))
    label("n-well: electrons", (-230.0, -180.0, D.CZ), root, D.beats(0))
    D.channel(root, m, d, D.beats(1))
    D.flow(root, m, d, 1, n=10, life=150)
    label("gate 0 V: on", (0.0, 120.0, 0), root, D.beats(1))
    label("hole channel", (-20.0, -8.0, 2), root, D.beats(1))
    label("holes: source to drain", (d.ct_x, 200.0, D.CZ), root, D.beats(1))
    dn, dp, e = D.inverter(m, root, D.beats(2))
    label("NMOS: pull-down", (dn.cx, -150.0, 0), root, D.beats(2))
    label("PMOS: pull-up", (dp.cx, -150.0, 0), root, D.beats(2))
    label("gates tied: input", (0.0, dn.ct_top + 127, 0), root, D.beats(2))
    label("drains tied: output", (0.0, dn.ct_top + 17, 0), root, D.beats(2))
    whole = D.frame_dev(d)
    return [whole, whole, _inv_pose(e)]


def sec2(m, root):
    """2 the parts: source, channel, drain, gate stack, then the n-well and its tap."""
    d = _dev(m, root, tap=True)
    D.hl(root, m, d, "source", D.beats(0), pad=6.0)
    label("p+ source (VDD side)", (d.ct_x, -70.0, 0), root, D.beats(0))
    label("SiGe:B raised epitaxy", (d.ct_x + 60, 22.0, 0), root, D.beats(0))
    label("silicide", (d.ct_x - 60, 48.0, 0), root, D.beats(0))
    D.channel(root, m, d, D.beats(1))
    D.flow(root, m, d, 1, n=10, life=150, contacts=False)
    label("hole channel", (0.0, -8.0, 2), root, D.beats(1))
    label("gate 0 V", (0.0, 120.0, 0), root, D.beats(1))
    D.hl(root, m, d, "drain", D.beats(2), pad=6.0)
    label("p+ drain: the output", (-d.ct_x, -70.0, 0), root, D.beats(2))
    label("contact to the output", (-d.ct_x, 250.0, 0), root, D.beats(2))
    label("fill metal", (0.0, 120.0, 0), root, D.beats(3))
    label("p-type work-function metal", (d.gh - 15, 90.0, 0), root, D.beats(3))
    label("high-k HfO2", (-d.gh + 4, 60.0, 0), root, D.beats(3))
    label("SiO2 interlayer", (-30.0, 3.0, 0), root, D.beats(3))
    label("nitride spacer", (d.gh + 19, 150.0, 0), root, D.beats(3))
    D.outline(root, m, "well_hl", (-d.half + 70, -228.0), (d.half + 120, -118.0), D.beats(4))
    D.hl(root, m, d, "tap", D.beats(4), pad=6.0)
    D.majority_dots(root, m, d, D.beats(4), D.beats(4))
    label("n-well: phosphorus", (-200.0, -170.0, 0), root, D.beats(4))
    label("n+ tap to VDD", (d.half + 65, 200.0, 0), root, D.beats(4))
    label("electrons: majority", (130.0, -150.0, D.CZ), root, D.beats(4))
    label("p substrate", (0.0, -285.0, 0), root, D.beats(4))
    gate = D.frame((-230.0, -90.0, -40.0), (230.0, 210.0, 0.0), pitch=0.10, pad=1.12)
    return [D.frame_dev(d, x0=-40, x1=470, bottom=-150, top=350), D.frame_dev(d, x0=-330, x1=330, bottom=-190, top=230),
            D.frame_dev(d, x0=-470, x1=40, bottom=-150, top=350), gate,
            D.frame_dev(d, x0=-440, x1=d.half + 130, bottom=-330)]


def sec3(m, root):
    """3 CMOS pairing: the inverter at rest, input low (PMOS on), input high (NMOS on)."""
    D.mats(m)
    dn, dp, e = D.inverter(m, root, D.beats(0, 3))
    label("PMOS: pull-up to VDD", (dp.cx, -150.0, 0), root, D.beats(0))
    label("NMOS: pull-down to ground", (dn.cx, -150.0, 0), root, D.beats(0))
    label("VDD", (dp.src(1), dp.ct_top + 17, 0), root, D.beats(0, 3))
    label("ground", (dn.src(-1), dn.ct_top + 17, 0), root, D.beats(0, 3))
    label("input", (0.0, dn.ct_top + 127, 0), root, D.beats(0))
    label("output", (0.0, dn.ct_top + 17, 0), root, D.beats(0))
    # input 0: PMOS on, holes from VDD to the output
    D.channel(root, m, dp, D.beats(1))
    D.flow(root, m, dp, 1, n=10, life=130)
    label("input 0 V: PMOS on", (dp.cx, 120.0, 0), root, D.beats(1))
    label("NMOS off", (dn.cx, 120.0, 0), root, D.beats(1))
    label("output charged to VDD", (0.0, dn.ct_top + 17, 0), root, D.beats(1))
    # input 1: NMOS on, electrons from ground to the output; both gates high
    D.gate_glow(root, m, dn, D.beats(2))
    D.gate_glow(root, m, dp, D.beats(2))
    D.channel(root, m, dn, D.beats(2))
    D.flow(root, m, dn, 2, n=12, life=100)
    label("input high: NMOS on", (dn.cx, 120.0, 0), root, D.beats(2))
    label("PMOS off", (dp.cx, 120.0, 0), root, D.beats(2))
    label("output pulled to ground", (0.0, dn.ct_top + 17, 0), root, D.beats(2))
    return [_inv_pose(e), _inv_pose(e), _inv_pose(e)]


def sec4(m, root):
    """4 standard cell layout: one inverter cell from above, its rails, then rows with tap cells."""
    D.mats(m)
    g = empty("rows", root)
    for r in range(2):
        for k in range(5):
            D.cell(m, g, k * CELL_W, f"cell_{r}_{k}", w=CELL_W, h=CELL_H, flip=bool(r), tap=k in (0, 4))
    # the flipped row goes on top, sharing the VDD rail: move its cell groups up one cell height
    for o in list(g.children):
        if o.name.startswith("cell_1_"):
            o.location = C.P(0.0, CELL_H, 0.0)
    W = 5 * CELL_W
    c0 = 2 * CELL_W  # the middle cell is the inverter shown first
    D.outline(root, m, "cell_hl", (c0, 0.0), (c0 + CELL_W, CELL_H), D.beats(0), t=8.0, z=40.0)
    label("PMOS in the n-well", (c0 + 0.5 * CELL_W, CELL_H * 0.72, 10), root, D.beats(0))
    label("NMOS in the p-well", (c0 + 0.5 * CELL_W, CELL_H * 0.22, 10), root, D.beats(0))
    label("shared gate", (c0 + 0.33 * CELL_W, CELL_H * 0.5, 14), root, D.beats(0))
    label("M1 output", (c0 + 0.5 * CELL_W, CELL_H * 0.4, 24), root, D.beats(0))
    D.outline(root, m, "rail_v", (0.0, CELL_H - 40), (W, CELL_H + 40), D.beats(1), t=8.0, z=40.0)
    D.outline(root, m, "rail_g", (0.0, -40.0), (W, 40.0), D.beats(1), t=8.0, z=40.0)
    label("VDD rail", (c0 + 0.7 * CELL_W, CELL_H, 30), root, D.beats(1))
    label("ground rail", (c0 + 0.7 * CELL_W, 0.0, 30), root, D.beats(1))
    label("height: 7.5-12 tracks", (c0 + CELL_W + 20, CELL_H * 0.5, 30), root, D.beats(1))
    for k in (0, 4):
        D.outline(root, m, f"tap_hl{k}", (k * CELL_W, 0.0), ((k + 1) * CELL_W, 2 * CELL_H), D.beats(2), t=8.0, z=40.0)
    label("tap cell", (0.5 * CELL_W, CELL_H * 0.82, 10), root, D.beats(2))
    label("tap cell", (4.5 * CELL_W, CELL_H * 1.18, 10), root, D.beats(2))
    label("rows share the VDD rail", (2.5 * CELL_W, CELL_H, 30), root, D.beats(2))
    cell = D.frame((c0 - 60, -60.0, -10.0), (c0 + CELL_W + 60, CELL_H + 60, 40.0), pitch=0.0, pad=1.1)
    row = D.frame((0.0, -60.0, -10.0), (W, 2 * CELL_H + 60, 40.0), pitch=0.0, pad=1.05)
    return [cell, cell, row]


def sec5(m, root):
    """5 NMOS vs PMOS balance: slow holes, the PMOS drawn wider, then fins: 2 NMOS, 3 PMOS."""
    D.mats(m)
    dn, dp, e = D.inverter(m, root, D.beats(0), name="a", wires=False)
    D.gate_glow(root, m, dn, D.beats(0))
    D.channel(root, m, dn, D.beats(0))
    D.channel(root, m, dp, D.beats(0))
    D.flow(root, m, dn, 0, n=14, life=60, u1=0.85)
    D.flow(root, m, dp, 0, n=8, life=170, u1=0.7)
    label("electrons ~1400 cm2/Vs", (dn.cx, 250.0, 0), root, D.beats(0))
    label("holes ~450 cm2/Vs", (dp.cx, 250.0, 0), root, D.beats(0))
    label("same size, ~1/3 the current", (dp.cx, -150.0, 0), root, D.beats(0))
    bn, bp, eb = D.inverter(m, root, D.beats(1), name="b", wires=False, depth_n=260.0, depth_p=600.0)
    D.channel(root, m, bp, D.beats(1))
    D.flow(root, m, bp, 1, n=14, life=150, u1=0.8)
    label("NMOS width W", (bn.cx, 120.0, 0), root, D.beats(1))
    label("PMOS ~2-2.5x wider", (bp.cx, 120.0, -300), root, D.beats(1))
    label("equal pull-up and pull-down", (bp.cx, -150.0, 0), root, D.beats(1))
    _, zn, en = D.finfet(m, root, "n", nfins=2, z0=-260.0, name="fn", iv=D.beats(2), lit=D.beats(2), length=300.0)
    _, zp, ep = D.finfet(m, root, "p", nfins=3, z0=260.0, name="fp", iv=D.beats(2), lit=D.beats(2), length=300.0)
    label("NMOS: 2 fins", (-4.0, D.FIN_H + 100, -260.0), root, D.beats(2))
    label("PMOS: 3 fins", (-4.0, D.FIN_H + 100, 260.0), root, D.beats(2))
    label("width comes in whole fins", (-4.0, -100.0, 0.0), root, D.beats(2))
    lo = (0.0, -170.0, en[0][2])
    hi = (300.0, D.FIN_H + 86, ep[1][2])
    eb2 = ((eb[0][0], eb[0][1], -600.0), eb[1])
    return [_inv_pose(e), D.frame(eb2[0], eb2[1], yaw=0.45, pitch=0.30, pad=1.06),
            D.frame(lo, hi, yaw=-0.95, pitch=0.25, pad=1.06)]


def sec6(m, root):
    """6 strain and doping: SiGe:B source and drain with boron, the squeeze, faster holes."""
    d = _dev(m, root)
    D.dopants(root, m, d, D.beats(0))
    D.hl(root, m, d, "epi-1", D.beats(0), pad=4.0)
    D.hl(root, m, d, "epi1", D.beats(0), pad=4.0)
    label("SiGe:B grown in place", (d.ct_x, 22.0, D.CZ), root, D.beats(0))
    label("boron atoms", (-d.ct_x, -60.0, D.CZ), root, D.beats(0))
    D.strain(root, m, d, D.beats(1, 3))
    D.channel(root, m, d, D.beats(1, 3))
    label("Ge is bigger: SiGe pushes in", (d.sd_in + 40, -60.0, D.CZ), root, D.beats(1))
    label("compressive channel", (0.0, -22.0, D.CZ), root, D.beats(1))
    D.flow(root, m, d, 2, n=14, life=85)
    label("faster holes", (d.ct_x, 200.0, D.CZ), root, D.beats(2))
    label("+25% drive at 90 nm (Intel)", (0.0, 120.0, 0), root, D.beats(2))
    close = D.frame_dev(d, x0=-420, x1=420, bottom=-180, top=200)
    return [close, close, D.frame_dev(d)]


def sec7(m, root):
    """7 germanium and GAA: stacked sheets of silicon, then SiGe, then germanium."""
    D.mats(m)
    _, e = D.gaa(m, root, "p", sheet_ivs={"mos_si": D.beats(0), "mos_sige": D.beats(1), "mos_ge": D.beats(2)},
                 lit=D.beats(2), name="g7")
    top = D.SHEET_Y[-1] + D.SHEET_T
    label("silicon sheets", (-4.0, D.SHEET_Y[1] + 15, -40.0), root, D.beats(0))
    label("gate all round each", (-4.0, D.SHEET_Y[0] - 8, 100.0), root, D.beats(0))
    label("SiGe:B source/drain", (300.0, top + 10, 60.0), root, D.beats(0))
    label("SiGe sheets: ~1 GPa squeeze", (-4.0, D.SHEET_Y[1] + 15, -40.0), root, D.beats(1))
    label("peak hole mobility +100%", (-4.0, top + 50, 0.0), root, D.beats(1))
    label("germanium: ~1900 cm2/Vs", (-4.0, D.SHEET_Y[1] + 15, -40.0), root, D.beats(2))
    label("hole channel on each sheet", (-4.0, D.SHEET_Y[0] - 8, 100.0), root, D.beats(2))
    p = D.frame(e[0], e[1], yaw=-0.75, pitch=0.25, pad=1.05)
    return [p, p, p]


def sec8(m, root):
    """8 who makes it: the foundries, the epi tools, the cell and layout tools."""
    D.mats(m)
    e = D.makers_row(m, root, "p", D.beats(0))
    label("TSMC: FinFET, then N2 GAA", (-4.0, 250.0, D.ROW_Z[0]), root, D.beats(0))
    label("Intel: 18A RibbonFET", (-4.0, 250.0, D.ROW_Z[1]), root, D.beats(0))
    label("Samsung: GAA", (-4.0, 250.0, D.ROW_Z[2]), root, D.beats(0))
    d = D.planar(m, root, "p", 0.0, name="pm", iv=D.beats(1))
    D.hl(root, m, d, "epi-1", D.beats(1), pad=4.0)
    D.hl(root, m, d, "epi1", D.beats(1), pad=4.0)
    label("SiGe epi: Applied, ASM", (d.ct_x, 22.0, D.CZ), root, D.beats(1))
    label("grown in an epi reactor", (-d.ct_x, 22.0, D.CZ), root, D.beats(1))
    g = empty("rows8", root)
    for k in range(5):
        D.cell(m, g, k * CELL_W, f"c8_{k}", w=CELL_W, h=CELL_H, tap=k in (0, 4))
    show(g, D.beats(2))
    label("cell libraries: Arm", (2.5 * CELL_W, CELL_H * 0.72, 10), root, D.beats(2))
    label("place and route: Synopsys, Cadence", (1.5 * CELL_W, CELL_H * 0.22, 24), root, D.beats(2))
    row = D.frame((0.0, -60.0, -10.0), (5 * CELL_W, CELL_H + 60, 40.0), pitch=0.0, pad=1.05)
    return [D.row_pose(e), D.frame_dev(d), row]


def sec9(m, root):
    """9 chokepoints and risks: slow holes, boron drifting into the channel, few epi vendors."""
    d = _dev(m, root)
    D.channel(root, m, d, D.beats(0))
    D.flow(root, m, d, 0, n=6, life=220, u1=0.6)
    label("holes: the weaker carrier", (0.0, -8.0, 2), root, D.beats(0))
    label("needs new strain each node", (0.0, 120.0, 0), root, D.beats(0))
    D.dopants(root, m, d, D.beats(1))
    for s in (-1, 1):
        st = (s * (d.sd_in + 10), -30.0, D.CZ)
        D.stream_of(root, f"bdrift{s}", 6, st, [(0, 0, 0), (-s * (d.sd_in - 10), -10.0, 0)], 8.0, m["mos_atom_b"], 1, 0.05, 0.7, 110)
    D.box_on(root, "chan_warn", (-d.ext_in, -60, -40), (d.ext_in, -1, 3.0), m["mos_warn"], D.beats(1))
    label("boron diffuses inward", (-d.sd_in, -30.0, D.CZ), root, D.beats(1))
    label("shifts Vt, leaks", (0.0, -60.0, 3), root, D.beats(1))
    for k in ("epi-1", "epi1"):
        D.hl(root, m, d, k, D.beats(2), pad=4.0, mt="mos_warn")
    label("epi tools: few vendors", (d.ct_x, 22.0, D.CZ), root, D.beats(2))
    label("current shares not public", (-d.ct_x, 22.0, D.CZ), root, D.beats(2))
    close = D.frame_dev(d, x0=-420, x1=420, bottom=-180, top=230)
    return [close, close, close]


def sec10(m, root):
    """10 sources: each beat lights the part its sources back."""
    d = _dev(m, root, iv=D.beats(0))
    D.strain(root, m, d, D.beats(0))
    D.channel(root, m, d, D.beats(0))
    label("[1][2] Intel 90 nm, VLSI 2004", (0.0, 120.0, 0), root, D.beats(0))
    _, e1 = D.gaa(m, root, "p", sheet_ivs={"mos_sige": None}, iv=D.beats(1), name="g10")
    label("[3] IBM SiGe nanosheet pFET", (-4.0, D.SHEET_Y[1] + 15, -40.0), root, D.beats(1))
    label("[6] GAA SiGe S/D patent", (300.0, D.SHEET_Y[-1] + D.SHEET_T + 10, 60.0), root, D.beats(1))
    dn, dp, e2 = D.inverter(m, root, D.beats(2), name="i10")
    D.hl(root, m, dp, "epi1", D.beats(2), pad=4.0)
    label("[4] UCSB inverter sizing", (0.0, dn.ct_top + 127, 0), root, D.beats(2))
    label("[5] Applied epi release", (dp.src(1), 22.0, D.CZ), root, D.beats(2))
    g = empty("rows10", root)
    for k in range(5):
        D.cell(m, g, k * CELL_W, f"c10_{k}", w=CELL_W, h=CELL_H, tap=k in (0, 4))
    show(g, D.beats(3))
    label("[7] ASAP7 cells", (2.5 * CELL_W, CELL_H * 0.72, 10), root, D.beats(3))
    label("[8] cell library lecture", (1.5 * CELL_W, CELL_H * 0.22, 24), root, D.beats(3))
    row = D.frame((0.0, -60.0, -10.0), (5 * CELL_W, CELL_H + 60, 40.0), pitch=0.0, pad=1.05)
    return [D.frame_dev(d, x0=-420, x1=420, bottom=-180, top=230), D.frame(e1[0], e1[1], yaw=-0.75, pitch=0.25, pad=1.05),
            _inv_pose(e2), row]


# ---- registry and entry point ----------------------------------------------------------------

# key -> (beats, camera poses, builder)
SCENES = {
    "zoom_a": (3, None, zoom_a),
    "zoom_b": (3, None, zoom_b),
    "zoom_c": (3, None, zoom_c),
    "zoom_d": (3, None, zoom_d),
    "zoom_e": (3, None, zoom_e),
    "sec1": (3, None, sec1),
    "sec2": (5, None, sec2),
    "sec3": (3, None, sec3),
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
    name = f"pmos_{key}"
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
        finish("pmos", page="chip")
    else:
        scene(key)
