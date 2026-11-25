"""The PHOTODIODE node's numbered sections 1-9: one picture per heading of the page's write-up
(tui/src/screens/diagrams_pages/FIB_PD.txt, headings 1-9), three beats each.

Run from the repo root (through the bake queue):

    python3 tools/pbr3d/bake_queue.py bake tools/pbr3d/blender/fiber_photodiode_sections.py photodiode_section_<n> -- <n>

Or directly: blender -b --factory-startup --python tools/pbr3d/blender/fiber_photodiode_sections.py -- <n>

Writes blender/fiber_photodiode_section_<n>.blend and assets/fiber_photodiode_section_<n>.glb. One beat is 8 s.
Materials come from fiber_kit.py; the detailed parts (TO-can with ball lens, PIN chip cut into its layers,
TIA, bond wires, pins, a germanium-on-silicon photodiode) from fiber_photodiode_detail.py, drawn about
16x life size so the camera can frame each part tightly.

  1 What happens            light lands on the PIN; the InGaAs frees pairs swept to the contacts; the TIA
  2 The parts               the PIN layers; the TIA and its bond wire; a germanium-on-silicon photodiode
  3 Light becomes a voltage the six steps in order, numbered: lens, absorbed, pair, current, TIA, DSP
  4 Why InGaAs              1310 nm passes through silicon; InGaAs absorbs it; bandgap bars vs the photon
  5 Responsivity and speed  light and current gauges; fast pulses from a tiny diode; a spot that misses
  6 Noise and sensitivity   PAM4 levels on the TIA's output: clean, noisy, then squeezed until they blur
  7 The link budget         a power ladder from the laser, down at each connector and the fibre, above sensitivity
  8 Who makes it            the chip, the TIA and the germanium photodiode singled out and tagged with makers
  9 Chokepoints             faster diode and TIA; LPO with the DSP gone; dust on a connector eating the budget
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fiber_kit as K  # noqa: E402
import fiber_photodiode_detail as D  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402
from sand_overview import F, P, ball, beat, box, fly, key, label, show, tube  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
from fiber_photodiode_detail import blip, flash, frame, front, run  # noqa: E402

PAGE = "fiber_photodiode"
BEATS = 3
ALL = [(0, F(BEATS, 0))]


def from_beat(b):
    return [(F(b, 0), F(BEATS, 0))]


# Framing boxes (lo, hi) for the subjects the beats look at.
CHIP = ((8.0, -22.0, -20.0), (35.0, 22.0, 0.0))
CHIP_TIA = ((6.0, -32.0, -20.0), (36.0, 40.0, 0.0))
CAN = ((-56.0, -50.0, -50.0), (44.0, 50.0, 0.0))
CAN_PINS = ((-56.0, -50.0, -50.0), (130.0, 50.0, 0.0))
FIBRE_CAN = ((-160.0, -50.0, -50.0), (44.0, 50.0, 0.0))
TIA_MID = ((D.TIA_LO[0] + D.TIA_HI[0]) / 2, D.TIA_HI[1], 0.0)
OUT_AT = (100.0, D.PINS["OUT"][0], D.PINS["OUT"][1])


def pin_pts(nm, x0=D.POST_X0, x1=D.PIN_X1):
    py, pz = D.PINS[nm]
    return [(x0, py, pz), (x1, py, pz)]


def receiver(m, root, fibre=True, beam=True):
    """The cut-open receiver: fibre, beam, can with chip, TIA and bonds, pins."""
    if fibre:
        D.fibre(m, root)
    g = D.photodiode(m, root, cut_open=True)
    show(g, ALL)
    D.pins(m, root)
    if beam:
        bg = D.beam(m, root)
        show(bg, ALL)
    return g


def board(m, root, x1=140.0, z0=-90.0):
    return box("board", (-70.0, -54.0, z0), (x1, -50.0, 0.0), m["pcb"], root)


# ---- module (for 3 and 9) -------------------------------------------------------------------
MOD_X0, MOD_X1 = -360.0, 880.0
MOD_Z = -170.0
PCB_Y = (-30.0, -22.0)
DSP = ((420.0, -22.0, -120.0), (540.0, -8.0, -20.0))
Y_TR = PCB_Y[1] + 1.6


def module(m, root):
    """A pluggable's bottom shell (lid off, cut at z = 0): fibre port, ROSA barrel, flex, PCB on
    standoffs, copper trace, DSP, gold card-edge fingers. Returns (group, dsp group)."""
    g = empty("mod", root)
    box("mod_floor", (MOD_X0, -70.0, MOD_Z), (MOD_X1, -62.0, 0.0), m["dark_steel"], g)
    box("mod_side", (MOD_X0, -62.0, MOD_Z), (MOD_X1, 60.0, MOD_Z + 10.0), m["dark_steel"], g)
    box("mod_front", (MOD_X0, -62.0, MOD_Z), (MOD_X0 + 12.0, 60.0, 0.0), m["dark_steel"], g)
    D.ring_x("rosa_barrel", MOD_X0 + 12.0, D.CAP_X0, 14.0, 24.0, m["steel"], g, True)
    D.ring_x("lc_port", MOD_X0 - 30.0, MOD_X0 + 12.0, 11.0, 20.0, m["ink"], g, True)
    box("pcb", (150.0, PCB_Y[0], MOD_Z + 14.0), (MOD_X1 + 40.0, PCB_Y[1], 0.0), m["pcb"], g)
    for x in (200.0, 500.0, 800.0):
        tube(f"standoff_{x}", (x, -62.0, -60.0), (x, PCB_Y[0], -60.0), 6.0, m["steel"], g, 16)
    flex = mat("pd_flex", (0.85, 0.50, 0.12), rough=0.5)
    box("flex_v", (D.PIN_X1, -42.0, -44.0), (D.PIN_X1 + 4.0, 40.0, 0.0), flex, g)
    box("flex_h", (D.PIN_X1, PCB_Y[1], -44.0), (190.0, PCB_Y[1] + 1.5, 0.0), flex, g)
    box("trace", (185.0, PCB_Y[1], -24.0), (MOD_X1 - 40.0, PCB_Y[1] + 0.8, -16.0), m["copper"], g)
    dsp = empty("dsp", g)
    box("dsp_sub", (DSP[0][0], -22.0, DSP[0][2]), (DSP[1][0], -16.0, DSP[1][2]), m["substrate"], dsp)
    box("dsp_lid", (DSP[0][0] + 12.0, -16.0, DSP[0][2] + 12.0), (DSP[1][0] - 12.0, -8.0, DSP[1][2] - 12.0),
        m["steel"], dsp)
    for k in range(8):
        z = -150.0 + k * 18.0
        box(f"finger{k}", (MOD_X1 - 40.0, PCB_Y[1], z), (MOD_X1 + 38.0, PCB_Y[1] + 0.8, z + 10.0), m["gold"], g)
    return g, dsp


def to_dsp_path():
    return [(D.HEAD_X1, *D.PINS["OUT"]), (D.PIN_X1, *D.PINS["OUT"]), (D.PIN_X1 + 6.0, Y_TR, -20.0),
            (DSP[0][0], Y_TR, -20.0)]


# ---- 1 What happens --------------------------------------------------------------------------


def sec1(m, root):
    """Each photon becomes a little bit of current: light lands on the PIN, the InGaAs frees pairs
    that the bias sweeps to the contacts, the TIA turns the current into a voltage."""
    receiver(m, root)
    D.photons(root, "w_ph0", m, 0, 0.05, 0.8, n=8, life=55)
    label("FIBRE", (-130.0, 10.0, 0.0), root, beat(0))
    label("BALL LENS", (D.LENS_X, D.LENS_R, 0.0), root, beat(0))
    label("PIN PHOTODIODE", (20.0, D.MESA, 0.0), root, beat(0))
    D.pairs(root, "w_p1", m, 1, 0.15, 0.85, 7)
    label("InGaAs: PHOTON -> e + h", (19.0, -D.MESA, 0.0), root, beat(1))
    label("ELECTRONS TO n CONTACT", ((D.NC[0] + D.NC[1]) / 2, D.NC[2], 0.0), root, beat(1))
    label("HOLES TO p RING", (D.RING_X[0], 11.0, 0.0), root, beat(1))
    r = D.routes()
    run(root, "w_in", r["p_to_tia"], 6, 0.9, m["elec"], 2, 0.0, 0.4, 36)
    run(root, "w_out", r["tia_to_out"], 5, 1.1, m["volt"], 2, 0.2, 0.6, 36)
    run(root, "w_pin", pin_pts("OUT"), 5, 2.6, m["volt"], 2, 0.3, 0.85, 50)
    label("TIA: CURRENT TO VOLTAGE", TIA_MID, root, beat(2))
    label("OUT: TO THE DSP", (110.0, *D.PINS["OUT"]), root, beat(2))
    D.glide_camera(root, [
        frame(*FIBRE_CAN, yaw=-0.15, pitch=0.22, pad=1.0),
        frame(*CHIP, yaw=-0.2, pitch=0.12, pad=1.1),
        frame((5.0, -30.0, -35.0), (130.0, 42.0, 0.0), yaw=-0.5, pitch=0.25, pad=1.1),
    ])


# ---- 2 The parts -----------------------------------------------------------------------------


def sec2(m, root):
    """The parts: the PIN's layers, the TIA, a germanium photodiode on silicon."""
    receiver(m, root, fibre=False)
    D.ge_pd(m, root)
    D.pairs(root, "pt0", m, 0, 0.15, 0.85, 4)
    label("p-InP", (D.P_X[0] + 1.2, 6.0, 0.0), root, beat(0))
    label("i: InGaAs ABSORBER", ((D.I_X[0] + D.I_X[1]) / 2, -8.0, 0.0), root, beat(0))
    label("n-InP", ((D.N_X[0] + D.N_X[1]) / 2, 8.0, 0.0), root, beat(0))
    label("SiN PASSIVATION + BCB", (D.P_X[0], -D.MESA - 2.0, 0.0), root, beat(0))
    label("DEPLETION FIELD", ((D.I_X[0] + D.I_X[1]) / 2, 10.0, 0.3), root, beat(0))
    label("InP SUBSTRATE", ((D.S_X[0] + D.S_X[1]) / 2, -12.0, 0.0), root, beat(0))
    r = D.routes()
    D.pairs(root, "pt1", m, 1, 0.1, 0.6, 3)
    run(root, "pt_in", r["p_to_tia"], 6, 0.9, m["elec"], 1, 0.15, 0.6, 36)
    run(root, "pt_out", r["tia_to_out"], 5, 1.1, m["volt"], 1, 0.45, 0.85, 30)
    label("TIA", TIA_MID, root, beat(1))
    label("CURRENT IN", r["p_to_tia"][4], root, beat(1))
    label("VOLTAGE OUT", r["tia_to_out"][6], root, beat(1))
    D.ge_light(root, "pt_ge", m, 2, 0.15, 0.85, 6)
    label("GERMANIUM", (D.GX + 32.0, -5.0, 0.0), root, beat(2))
    label("SILICON WAVEGUIDE", (D.GX - 40.0, -14.0, 0.0), root, beat(2))
    label("SILICON CHIP", (D.GX - 20.0, -36.0, 0.0), root, beat(2))
    label("W PLUGS + Cu METAL", (D.GX + 34.0, 6.0, 0.0), root, beat(2))
    label("CONTACT", (D.GX + 24.0, 15.0, -7.0), root, beat(2))
    D.glide_camera(root, [
        frame(*CHIP, yaw=-0.2, pitch=0.12, pad=1.1),
        frame((6.0, -10.0, -14.0), (36.0, 40.0, 0.0), yaw=-0.55, pitch=0.15, pad=1.2),
        frame((D.GX - 60.0, -44.0, -20.0), (D.GX + 75.0, 16.0, 0.0), yaw=0.15, pitch=0.42, pad=1.05),
    ])


# ---- 3 Light becomes a voltage, in order ----------------------------------------------------


def sec3(m, root):
    """The six steps, numbered: lens, absorbed, pair, current; TIA, DSP."""
    receiver(m, root)
    module(m, root)
    D.photons(root, "o_ph0", m, 0, 0.05, 0.5, n=6, life=55)
    D.pairs(root, "o_p0", m, 0, 0.55, 0.9, 3)
    label("1 LENS FOCUSES THE LIGHT", (D.LENS_X, D.LENS_R, 0.0), root, beat(0))
    label("2 ABSORBED IN THE InGaAs", (19.0, -D.MESA, 0.0), root, beat(0))
    D.pairs(root, "o_p1", m, 1, 0.12, 0.8, 6)
    label("3 ONE ELECTRON + ONE HOLE", (19.0, -8.0, 0.0), root, beat(1))
    label("4 BIAS SWEEPS THEM: CURRENT", ((D.NC[0] + D.NC[1]) / 2, D.NC[2], 0.0), root, beat(1))
    r = D.routes()
    run(root, "o_out", r["tia_to_out"], 4, 1.4, m["volt"], 2, 0.0, 0.3, 30)
    run(root, "o_dsp", to_dsp_path(), 8, 4.5, m["volt"], 2, 0.1, 0.8, 70)
    label("5 TIA: CURRENT TO VOLTAGE", TIA_MID, root, beat(2))
    label("6 DSP DECIDES THE PAM4 LEVEL", ((DSP[0][0] + DSP[1][0]) / 2, -8.0, -70.0), root, beat(2))
    D.glide_camera(root, [
        frame((-60.0, -28.0, -20.0), (36.0, 28.0, 0.0), yaw=-0.3, pitch=0.22),
        frame(*CHIP, yaw=-0.2, pitch=0.12, pad=1.1),
        frame((-20.0, -70.0, -125.0), (550.0, 50.0, 0.0), yaw=0.25, pitch=0.55, pad=1.0),
    ])


# ---- 4 Why InGaAs (and germanium) -----------------------------------------------------------
SI_X = (-200.0, -140.0)
IG_X = (100.0, 130.0)
BARS_Y0 = -40.0
EV = 100.0  # bar height per eV


def sec4(m, root):
    """Silicon lets 1310 nm through; InGaAs absorbs it; the bandgaps against the photon's energy."""
    box("bench_a", (-320.0, -44.0, -50.0), (170.0, -40.0, 0.0), m["dark_steel"], root)
    for x0 in (-300.0, 0.0):
        tube(f"src_{x0}", (x0, 0.0, 0.0), (x0 + 50.0, 0.0, 0.0), 10.0, m["gold"], root, 32)
        tube(f"src_core_{x0}", (x0 + 49.0, 0.0, 0.0), (x0 + 50.3, 0.0, 0.0), 1.2, m["light"], root, 12)
        box(f"src_post_{x0}", (x0 + 15.0, -40.0, -8.0), (x0 + 35.0, -10.0, 0.0), m["dark_steel"], root)
    # Silicon: a plain slab. The light passes straight through it.
    box("si_slab", (SI_X[0], -40.0, -40.0), (SI_X[1], 40.0, 0.0), m["si"], root)
    for b in range(BEATS):
        for k in range(18):
            y = [-6.0, 4.0, -2.0, 7.0, 0.0, -5.0, 3.0, 6.0, -8.0][k % 9] * (1.0 if k < 9 else 0.6)
            f0 = F(b, 0.03 + 0.82 * k / 17)
            blip(root, f"si_ph{b}_{k}", [front((-250.0, y * 0.3, 0)), front((SI_X[0], y, 0)),
                                         front((-40.0, y * 1.3, 0))], 2.0, m["light"], f0, 70)
    # InGaAs on InP: the light stops in the InGaAs and frees pairs.
    box("ig_inp", (IG_X[1], -40.0, -40.0), (IG_X[1] + 30.0, 40.0, 0.0), m["inp_sub"], root)
    box("ig_layer", (IG_X[0], -40.0, -40.0), (IG_X[1], 40.0, 0.0), m["ingaas"], root)
    for b in range(BEATS):
        for k in range(16):
            y = [-6.0, 4.0, -2.0, 7.0, 0.0, -5.0, 3.0, 6.0][k % 8] * (1.0 if k < 8 else 1.8)
            x = IG_X[0] + [6.0, 14.0, 9.0, 20.0, 4.0, 16.0, 11.0, 24.0][k % 8]
            f0 = F(b, 0.03 + 0.82 * k / 15)
            blip(root, f"ig_ph{b}_{k}", [front((50.0, y * 0.3, 0)), front((x, y, 0))], 2.0, m["light"],
                 f0, 22)
            flash(root, f"ig_f{b}_{k}", front((x, y, 0)), m["flash"], f0 + 22, r=2.6)
            blip(root, f"ig_e{b}_{k}", [front((x, y, 0)), front((x, y + 22.0, 0))], 1.6, m["elec"], f0 + 26, 34)
            blip(root, f"ig_h{b}_{k}", [front((x, y, 0)), front((x, y - 22.0, 0))], 1.6, m["hole"], f0 + 26, 34)
    label("SILICON", (sum(SI_X) / 2, 40.0, 0.0), root, beat(0))
    label("1310 nm LIGHT IN", (-240.0, 0.0, 0.0), root, beat(0))
    label("PASSES STRAIGHT THROUGH", (-70.0, 0.0, 0.0), root, beat(0))
    label("InGaAs (ON InP)", (sum(IG_X) / 2, 40.0, 0.0), root, beat(1))
    label("ABSORBED: ELECTRON + HOLE", (IG_X[0] + 12.0, -12.0, 0.0), root, beat(1))
    label("1310 nm LIGHT IN", (60.0, 0.0, 0.0), root, beat(1))
    # Bandgap bars against the photon's energy.
    box("bench_b", (200.0, -44.0, -50.0), (420.0, -40.0, 0.0), m["dark_steel"], root)
    bars = (("Si 1.12 eV", 220.0, 1.12, m["si"]), ("InGaAs ~0.75 eV", 290.0, 0.75, m["ingaas"]),
            ("Ge ~0.66 eV", 360.0, 0.66, m["ge"]))
    for text, x, ev, mt in bars:
        box(f"bar_{x}", (x, BARS_Y0, -30.0), (x + 40.0, BARS_Y0 + ev * EV, 0.0), mt, root)
        label(text, (x + 20.0, BARS_Y0 + ev * EV, 0.0), root, beat(2))
    yph = BARS_Y0 + 0.95 * EV
    tube("photon_line", (205.0, yph, 1.0), (415.0, yph, 1.0), 1.0, m["light"], root, 12)
    run(root, "line_ph", [(205.0, yph, 1.5), (415.0, yph, 1.5)], 6, 2.0, m["light"], 2, 0.05, 0.85, 50)
    # a photon dropping onto each bar: bounces off silicon (red), is absorbed by InGaAs and Ge (flash + pair)
    for k in range(5):
        for text, x, ev, mt in bars:
            f0 = F(2, 0.1 + 0.16 * k) + int(x) % 7
            top = BARS_Y0 + ev * EV
            cx = x + 20.0
            if ev > 0.95:
                blip(root, f"bar_ph{x}_{k}", [(cx, yph + 25.0, 2.0), (cx, yph + 2.0, 2.0), (cx + 18.0, yph + 25.0, 2.0)],
                     2.0, m["light"], f0, 30)
                flash(root, f"bar_x{x}_{k}", (cx, yph, 2.0), m["red"], f0 + 15, r=3.0, life=8)
            else:
                blip(root, f"bar_ph{x}_{k}", [(cx, yph + 25.0, 2.0), (cx, top, 2.0)], 2.0, m["light"], f0, 18)
                flash(root, f"bar_f{x}_{k}", (cx, top, 2.0), m["flash"], f0 + 18, r=3.0, life=8)
                blip(root, f"bar_e{x}_{k}", [(cx, top, 2.0), (cx - 12.0, top - 25.0, 2.0)], 1.6, m["elec"], f0 + 20, 26)
                blip(root, f"bar_h{x}_{k}", [(cx, top, 2.0), (cx + 12.0, top - 25.0, 2.0)], 1.6, m["hole"], f0 + 20, 26)
    label("PHOTON ABOVE THE GAP: ABSORBED", (310.0, BARS_Y0 + 0.75 * EV, 0.0), root, beat(2))
    label("BELOW SILICON'S GAP: PASSES", (240.0, BARS_Y0 + 1.12 * EV + 15.0, 0.0), root, beat(2))
    label("1310 nm PHOTON: 0.95 eV", (415.0, yph, 1.0), root, beat(2))
    D.glide_camera(root, [
        frame((-310.0, -44.0, -50.0), (-40.0, 45.0, 0.0), yaw=0.0, pitch=0.2),
        frame((-10.0, -44.0, -50.0), (165.0, 45.0, 0.0), yaw=0.0, pitch=0.2),
        frame((195.0, -44.0, -50.0), (425.0, 95.0, 0.0), yaw=0.2, pitch=0.2),
    ])


# ---- 5 Responsivity and speed ---------------------------------------------------------------


def gauge(m, root, name, x, z, mt, levels):
    """A glass gauge standing on the board at (x, z): a foot, ticks, and a glowing fill that rises
    to `levels` [(frame, fraction)]."""
    g = empty(name, root)
    y0, h, r = -50.0, 80.0, 7.0
    tube(f"{name}_foot", (x, y0, z), (x, y0 + 4.0, z), r + 3.0, m["dark_steel"], g, 24)
    tube(f"{name}_glass", (x, y0 + 4.0, z), (x, y0 + 4.0 + h, z), r, m["glass"], g, 24)
    for k in range(1, 5):
        yk = y0 + 4.0 + h * k / 4
        tube(f"{name}_tick{k}", (x, yk - 0.4, z), (x, yk + 0.4, z), r + 0.6, m["steel"], g, 24)
    piv = empty(f"{name}_fill", g, P(x, y0 + 4.0, z))
    tube(f"{name}_fill_t", (0.0, 0.0, 0.0), (0.0, h, 0.0), r - 1.5, mt, piv, 24)
    for f, s in levels:
        key(piv, f, "scale", (1.0, 1.0, max(s, 0.02)), linear=True)
    return g


def pulse(root, name, m, nm, f0, length, life=64, r=2.6):
    """One current pulse: a glowing sleeve `length` long running out along pin `nm`."""
    py, pz = D.PINS[nm]
    e = empty(name, root)
    tube(f"{name}_t", (D.HEAD_X1, py, pz), (D.HEAD_X1 + length, py, pz), r, m["volt"], e, 12)
    fly(e, [(0, 0, 0), (D.PIN_X1 - D.HEAD_X1 - length, 0, 0)], f0, f0 + life, steps=2)
    show(e, [(f0, f0 + life)])
    return e


def sec5(m, root):
    """Responsivity ~1 A/W: a milliwatt gives about a milliamp. Speed: a tiny diode and a fast TIA
    follow 106 GBd. A smaller diode is harder to hit with the light."""
    receiver(m, root)
    board(m, root)
    lv = [(F(0, 0), 0.4), (F(0, 0.25), 0.95), (F(0, 0.5), 0.45), (F(0, 0.75), 0.8), (F(1, 0), 0.6)]
    for g in (gauge(m, root, "g_light", 75.0, -55.0, m["light"], lv),
              gauge(m, root, "g_cur", 105.0, -55.0, m["elec"], [(f, s * 0.95) for f, s in lv])):
        show(g, beat(0))
    D.photons(root, "g_ph", m, 0, 0.05, 0.85, n=8, life=50)
    run(root, "g_out", pin_pts("OUT", D.HEAD_X1, D.PIN_X1), 6, 2.4, m["volt"], 0, 0.05, 0.85, 40)
    label("LIGHT IN", (75.0, 34.0, -55.0), root, beat(0))
    label("CURRENT OUT", (105.0, 34.0, -55.0), root, beat(0))
    label("1 mW IN -> ~1 mA OUT", (0.0, D.CAN_R, 0.0), root, beat(0))
    for k in range(12):
        u = 0.05 + 0.75 * k / 11
        D.photons(root, f"sp{k}", m, 1, u, u + 0.01, n=2, life=34, spread=3.0)
        pulse(root, f"sp_cur{k}", m, "OUT", F(1, u) + 34, 5.0)
    label("TINY DIODE: LOW CAPACITANCE", (20.0, -D.MESA, 0.0), root, beat(1))
    label("FAST TIA", TIA_MID, root, beat(1))
    label("106 GBd SYMBOLS", OUT_AT, root, beat(1))
    # Beat 2: the focused spot is wider than the window; the light outside it lands on the ring.
    for k, y in enumerate((2.0, -10.0, 4.0, 11.0, -3.0, -12.0, 9.5, 0.5)):
        f0 = F(2, 0.12 + 0.75 * k / 7)
        src = front((D.LENS_X + D.LENS_R, y * 0.35, 0.0))
        if abs(y) < D.RING_IN:
            x = 17.0 + (k % 3) * 2.0
            blip(root, f"hit{k}", [src, front((D.RING_X[0], y, 0)), front((x, y, 0))], 1.0, m["light"],
                 f0 - 26, 26)
            D.pair(root, f"hitp{k}", m, y, x, f0)
        else:
            blip(root, f"miss{k}", [src, front((D.RING_X[0] - 0.5, y, 0))], 1.0, m["light"], f0 - 26, 26)
            flash(root, f"missf{k}", front((D.RING_X[0] - 0.5, y, 0)), m["red"], f0, r=1.4, life=10)
    label("SPOT WIDER THAN THE WINDOW", (D.RING_X[0] - 2.0, 3.0, 0.0), root, beat(2))
    label("LOST ON THE RING", (D.RING_X[0], 11.5, 0.0), root, beat(2))
    D.glide_camera(root, [
        frame((-56.0, -54.0, -60.0), (115.0, 40.0, 0.0), yaw=0.15, pitch=0.22, pad=1.08),
        frame(*CAN_PINS, yaw=0.1, pitch=0.22, pad=1.05),
        frame((-20.0, -20.0, -18.0), (28.0, 20.0, 0.0), yaw=-0.3, pitch=0.12, pad=1.1),
    ])


# ---- 6 Noise and sensitivity ----------------------------------------------------------------
PANEL = ((150.0, -46.0, -80.0), (290.0, 70.0, -70.0))
LEVELS = {0: [-20.0, 5.0, 30.0, 55.0], 1: [-20.0, 5.0, 30.0, 55.0], 2: [3.0, 13.0, 23.0, 33.0]}
JITTER = {0: 0.8, 1: 7.0, 2: 7.0}


def sec6(m, root):
    """The TIA's output as four PAM4 levels on a readout: clean, then noisy, then squeezed by weak
    light until the noise blurs them together."""
    receiver(m, root)
    board(m, root, x1=300.0)
    box("panel", PANEL[0], PANEL[1], m["tia"], root)
    box("panel_rim", (PANEL[0][0] - 3.0, PANEL[0][1] - 3.0, -82.0), (PANEL[1][0] + 3.0, PANEL[1][1] + 3.0, -80.0),
        m["dark_steel"], root)
    box("panel_foot", (205.0, -50.0, -92.0), (235.0, -46.0, -62.0), m["dark_steel"], root)
    py, pz = D.PINS["OUT"]
    D.wire("cable", D.curve_pts((D.PIN_X1, py, pz), (PANEL[0][0], 40.0, -75.0), (8.0, 12.0, 0.0)), 1.6,
           m["dark_steel"], root)
    rng = random.Random(7)
    zf = PANEL[1][2] + 1.5
    for b in range(BEATS):
        for i, ly in enumerate(LEVELS[b]):
            gl = tube(f"lvl{b}_{i}", (160.0, ly, zf - 0.5), (280.0, ly, zf - 0.5), 0.7, m["guide"], root, 8)
            show(gl, beat(b) if b == 2 else ([(0, F(2, 0))] if b == 0 else []))
            for k in range(22):
                xs = [160.0 + 20.0 * j for j in range(7)]
                pts = [(x, ly + rng.uniform(-1, 1) * JITTER[b], zf) for x in xs]
                f0 = F(b, 0.02 + 0.8 * k / 21) + i * 3
                blip(root, f"smp{b}_{i}_{k}", pts, 1.8, m["volt"], f0, 44)
        run(root, f"n_out{b}", pin_pts("OUT", D.HEAD_X1, D.PIN_X1), 5, 2.4, m["volt"], b, 0.05, 0.85, 40)
    D.pairs(root, "n_p1", m, 1, 0.15, 0.85, 4)
    # the DSP's three decision thresholds sit between the levels; red when noise crosses them
    for b in range(BEATS):
        lv = LEVELS[b]
        for i in range(3):
            ty = (lv[i] + lv[i + 1]) / 2
            th = tube(f"thr{b}_{i}", (160.0, ty, zf - 0.3), (280.0, ty, zf - 0.3), 0.5,
                      m["red"] if b == 2 else m["field_line"], root, 8)
            show(th, beat(b))
        if b == 2:
            for k in range(10):
                i = k % 3
                ty = (lv[i] + lv[i + 1]) / 2
                flash(root, f"err{k}", (175.0 + k * 11.0, ty, zf + 0.5), m["red"], F(2, 0.1 + 0.075 * k), r=2.8, life=10)
    label("DECISION THRESHOLDS", (160.0, (LEVELS[0][0] + LEVELS[0][1]) / 2, zf), root, beat(0))
    label("RED: SYMBOL ERRORS", (225.0, 40.0, zf), root, beat(2))
    label("TIA OUTPUT", (215.0, 70.0, -70.0), root, beat(0))
    label("4 PAM4 LEVELS", (280.0, 55.0, zf), root, beat(0))
    label("TIA NOISE", TIA_MID, root, beat(1))
    label("SHOT NOISE", (19.0, -D.MESA, 0.0), root, beat(1))
    label("LEVELS BLUR", (280.0, 30.0, zf), root, beat(1))
    label("WEAK LIGHT: LEVELS CLOSER", (280.0, 33.0, zf), root, beat(2))
    label("NOISE NOW CROSSES THEM", (160.0, 13.0, zf), root, beat(2))
    D.glide_camera(root, [
        frame((-56.0, -54.0, -90.0), (295.0, 75.0, 0.0), yaw=0.1, pitch=0.2, pad=1.02),
        frame((0.0, -50.0, -85.0), (295.0, 75.0, 0.0), yaw=0.0, pitch=0.18, pad=1.02),
        frame((145.0, -50.0, -90.0), (295.0, 75.0, -60.0), yaw=-0.15, pitch=0.12, pad=1.3),
    ])


# ---- 7 The link budget ------------------------------------------------------------------------
LASER_X = -800.0
C1, C2 = -560.0, -260.0
L0, DB = 230.0, 60.0  # ladder top and units per dB
SENS = 90.0


def connector(m, root, c):
    for s in (-1, 1):
        a, b = sorted((c + s * 4.0, c + s * 34.0))
        box(f"lc_{c}_{s}", (a, -9.0, -9.0), (b, 9.0, 9.0), m["oe"], root)
    box(f"adapter_{c}", (c - 6.0, -11.0, -11.0), (c + 6.0, 11.0, 11.0), m["ink"], root)


def sec7(m, root):
    """A power ladder above the link: laser out, down ~0.5 dB at each connector and a little along
    the fibre, still above the receiver's sensitivity at the photodiode, with margin."""
    box("bench", (-870.0, -54.0, -90.0), (80.0, -50.0, 0.0), m["guide"], root)
    laser = empty("laser_grp", root, P(LASER_X, 0.0, 0.0))
    laser.rotation_euler = (0.0, 0.0, math.pi)
    D.photodiode(m, laser, cut_open=False)
    D.pins(m, laser)
    pd = D.photodiode(m, root, cut_open=False)
    show(pd, ALL)
    D.pins(m, root)
    jacket = mat("pd_jacket", (0.95, 0.80, 0.15), rough=0.6)
    lx = LASER_X + 50.0
    tube("patch", (lx, 0.0, 0.0), (-50.0, 0.0, 0.0), 3.5, jacket, root, 16)
    for c in (C1, C2):
        connector(m, root, c)
    for b in range(BEATS):
        run(root, f"lb_ph{b}", [(lx, 0.0, 5.0), (-50.0, 0.0, 5.0)], 16, 2.6, m["light"], b, 0.0, 0.85, 60)
        for k in range(5):
            for c in (C1, C2):
                flash(root, f"loss{b}_{c}_{k}", (c, 12.0 + 4.0 * (k % 3), 6.0), m["red"], F(b, 0.1 + 0.17 * k), r=2.4, life=10)
    lv1 = L0 - 0.5 * DB
    lv2 = lv1 - 0.25 * DB
    lv3 = lv2 - 0.5 * DB
    segs = [  # (name, a, b, beat it appears)
        ("s0", (lx, L0, 0.0), (C1, L0, 0.0), 0), ("d1", (C1, L0, 0.0), (C1, lv1, 0.0), 0),
        ("s1", (C1, lv1, 0.0), (C2, lv2, 0.0), 1), ("d2", (C2, lv2, 0.0), (C2, lv3, 0.0), 1),
        ("s2", (C2, lv3, 0.0), (-50.0, lv3, 0.0), 2),
    ]
    for nm, a, b2, bt in segs:
        o = tube(f"ladder_{nm}", a, b2, 2.6, m["light"], root, 12)
        show(o, from_beat(bt))
    for nm, x, top, bt in (("g0", lx, L0, 0), ("g1", C1, lv1, 0), ("g2", C2, lv3, 1), ("g3", -50.0, lv3, 2)):
        o = tube(f"guide_{nm}", (x, 14.0, 0.0), (x, top, 0.0), 0.8, m["guide"], root, 8)
        show(o, from_beat(bt))
    sens = tube("sensitivity", (-760.0, SENS, 0.0), (0.0, SENS, 0.0), 2.0, m["red"], root, 12)
    show(sens, beat(2))
    marg = tube("margin", (-20.0, SENS, 0.0), (-20.0, lv3, 0.0), 2.4, m["volt"], root, 12)
    show(marg, beat(2))
    label("LASER", (LASER_X, D.CAN_R, 0.0), root, beat(0))
    label("LASER OUT", (lx, L0, 0.0), root, beat(0))
    label("CONNECTOR: ~0.5 dB", (C1, (L0 + lv1) / 2, 0.0), root, beat(0))
    label("RED: LIGHT SCATTERED AT THE JOINT", (C1, 22.0, 6.0), root, beat(0))
    label("FIBRE: 0.32 dB/km @1310", ((C1 + C2) / 2, (lv1 + lv2) / 2, 0.0), root, beat(1))
    label("CONNECTOR: ~0.5 dB", (C2, (lv2 + lv3) / 2, 0.0), root, beat(1))
    label("RECEIVER SENSITIVITY", (-200.0, SENS, 0.0), root, beat(2))
    label("MARGIN", (-20.0, (SENS + lv3) / 2, 0.0), root, beat(2))
    label("PHOTODIODE", (0.0, D.CAN_R, 0.0), root, beat(2))
    D.glide_camera(root, [
        frame((-860.0, -54.0, -50.0), (-500.0, 240.0, 50.0), yaw=0.0, pitch=0.15),
        frame((-600.0, -54.0, -20.0), (-220.0, 240.0, 20.0), yaw=0.0, pitch=0.15),
        frame((-330.0, -54.0, -50.0), (60.0, 240.0, 50.0), yaw=0.0, pitch=0.15),
    ])


# ---- 8 Who makes it ---------------------------------------------------------------------------


def sec8(m, root):
    """The photodiode chip, the TIA and the germanium photodiode singled out, each tagged with
    the companies that make it."""
    receiver(m, root, fibre=False)
    D.ge_pd(m, root)
    D.halo(m, root, "halo_chip", (D.RING_X[0], -D.BASE, -D.BASE), (D.S_X[1], D.BASE, 0.0), beat(0), pad=2.0)
    D.halo(m, root, "halo_tia", D.TIA_LO, D.TIA_HI, beat(1), pad=2.0)
    D.halo(m, root, "halo_ge", (D.GX + 10.0, -20.0, -14.0), (D.GX + 55.0, -3.5, 0.0), beat(2), pad=3.0)
    D.pairs(root, "mk0", m, 0, 0.15, 0.85, 4)
    label("COHERENT (COHR)", (D.P_X[0], D.MESA, 0.0), root, beat(0))
    label("LUMENTUM (LITE)", (D.S_X[1], D.BASE, 0.0), root, beat(0))
    label("HAMAMATSU", (D.S_X[1], -D.BASE, 0.0), root, beat(0))
    label("MODULE MAKERS' OWN LINES", (D.P_X[0], -D.MESA, 0.0), root, beat(0))
    run(root, "mk_in", D.routes()["p_to_tia"], 6, 0.9, m["elec"], 1, 0.1, 0.85, 36)
    label("MACOM (MTSI)", (D.TIA_LO[0], D.TIA_HI[1], 0.0), root, beat(1))
    label("SEMTECH (SMTC)", (D.TIA_HI[0], D.TIA_HI[1], 0.0), root, beat(1))
    label("MARVELL (MRVL)", (D.TIA_LO[0], D.TIA_LO[1], 0.0), root, beat(1))
    label("BROADCOM (AVGO)", (D.TIA_HI[0], D.TIA_LO[1], 0.0), root, beat(1))
    D.ge_light(root, "mk_ge", m, 2, 0.15, 0.85, 6)
    label("Ge PD: PART OF THE SiPh CHIP", (D.GX + 40.0, -5.0, 0.0), root, beat(2))
    label("SAME FAB AS THE MODULATORS", (D.GX - 30.0, -36.0, 0.0), root, beat(2))
    D.glide_camera(root, [
        frame(*CHIP, yaw=-0.2, pitch=0.12, pad=1.25),
        frame((8.0, -5.0, -14.0), (40.0, 42.0, 0.0), yaw=-0.5, pitch=0.15, pad=1.25),
        frame((D.GX - 60.0, -44.0, -20.0), (D.GX + 75.0, 16.0, 0.0), yaw=0.15, pitch=0.42, pad=1.1),
    ])


# ---- 9 Chokepoints and risks ----------------------------------------------------------------
FER_A = (-520.0, -405.0)   # patch-cord ferrule
FER_B = (-395.0, -340.0)   # receptacle ferrule


def sec9(m, root):
    """Faster lanes need a smaller diode and a faster TIA; LPO takes the DSP out; dust on a
    connector eats the budget."""
    receiver(m, root, beam=True)
    _, dsp = module(m, root)
    show(dsp, [(0, F(1, 0.3)), (F(2, 0), F(BEATS, 0))])
    D.pairs(root, "ck0", m, 0, 0.15, 0.85, 4)
    run(root, "ck_in", D.routes()["p_to_tia"], 8, 0.9, m["elec"], 0, 0.1, 0.85, 30)
    label("SMALLER, LOWER-CAP DIODE", (20.0, -D.MESA, 0.0), root, beat(0))
    label("FASTER TIA", TIA_MID, root, beat(0))
    # Beat 1: LPO. The DSP vanishes; the TIA's output runs straight to the card edge.
    lpo = to_dsp_path()[:-1] + [(MOD_X1 - 30.0, Y_TR, -20.0), (MOD_X1 - 30.0, Y_TR, -60.0),
                                (MOD_X1 + 38.0, Y_TR, -60.0)]
    run(root, "ck_lpo", lpo, 16, 4.5, m["volt"], 1, 0.3, 0.9, 70)
    gh = D.halo(m, root, "ck_ghost", DSP[0], DSP[1], [(F(1, 0.3), F(2, 0))], pad=4.0, r=1.2)
    for k in range(6):
        flash(root, f"ck_gone{k}", ((DSP[0][0] + DSP[1][0]) / 2 + (k - 2.5) * 16.0, -12.0, -70.0), m["red"],
              F(1, 0.22 + k * 0.015), r=4.0, life=14)
    label("THE DSP'S POWER AND LATENCY SAVED", ((DSP[0][0] + DSP[1][0]) / 2, -8.0, -20.0), root, beat(1))
    label("LPO: NO DSP", ((DSP[0][0] + DSP[1][0]) / 2, -18.0, -70.0), root, beat(1))
    label("TIA DRIVES THE HOST SerDes", (MOD_X1 + 20.0, PCB_Y[1], -100.0), root, beat(1))
    # Beat 2: a patch cord plugged into the port, dust on its ferrule's end face.
    jacket = mat("pd_jacket", (0.95, 0.80, 0.15), rough=0.6)
    tube("cord", (-760.0, 0.0, 0.0), (FER_A[0], 0.0, 0.0), 6.0, jacket, root, 16)
    D.ring_x("fer_a", FER_A[0], FER_A[1], 0.0, 10.0, m["ink"], root, True, 32)
    D.ring_x("fer_b", FER_B[0], FER_B[1], 0.0, 10.0, m["ink"], root, True, 32)
    for nm, (x0, x1) in (("a", FER_A), ("b", FER_B)):
        tube(f"fcore_{nm}", (x0, 0.0, 0.0), (x1, 0.0, 0.0), 1.0, m["glass"], root, 12)
    dust = [(-1.6, 0.8), (1.2, 1.1), (3.5, 0.7), (-4.0, 1.0)]
    for k, (y, r) in enumerate(dust):
        ball(f"dust{k}", (FER_A[1] + 0.6, y, 1.0), r, m["dust"], root, 10)
    for k in range(20):
        y = [-1.6, 0.4, 1.2, -0.6, 3.5, 0.0, -1.6, 1.2, -0.3, 0.8][k % 10] + (0.15 if k >= 10 else 0.0)
        f0 = F(2, 0.05 + 0.8 * k / 19)
        blocked = any(abs(y - dy) < dr for dy, dr in dust)
        end = FER_A[1] - 0.5 if blocked else FER_B[1]
        blip(root, f"cd_ph{k}", [front((-470.0, y, 0)), front((end, y, 0))], 0.9, m["light"], f0, 30 if blocked else 50)
        if blocked:
            flash(root, f"cd_x{k}", front((end, y, 0)), m["red"], f0 + 30, r=1.3, life=10)
    label("DUST ON THE FERRULE", (FER_A[1], 3.5, 1.0), root, beat(2))
    label("LIGHT LOST AT THE JOINT", (FER_A[1], -1.6, 1.0), root, beat(2))
    label("PATCH CORD", (-470.0, 10.0, 0.0), root, beat(2))
    D.glide_camera(root, [
        frame(*CHIP_TIA, yaw=-0.5, pitch=0.15, pad=1.2),
        frame((120.0, -70.0, MOD_Z), (MOD_X1 + 40.0, 50.0, 0.0), yaw=0.2, pitch=0.6, pad=1.0),
        frame((-470.0, -14.0, -12.0), (-360.0, 14.0, 2.0), yaw=-0.35, pitch=0.3, pad=1.15),
    ])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    _, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    m = D.materials(K.materials())
    SECTIONS[n](m, root)
    return root


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--") + 1])
    if n not in SECTIONS:
        raise SystemExit(f"section must be 1..9, got {n}")
    build(n)
    finish(f"section_{n}", page=PAGE)
