"""Detailed parts for the TRANSCEIVER sections (fiber_module_sections.py): an 800G OSFP DR8 pluggable
with its finned shell, the PCB inside it (gold card-edge fingers, PAM4 DSP, laser driver, TIA, TOSA
with eight EML lasers, ROSA with eight photodiodes, fibres to an MPO-16 port), and the host side
(switch board, faceplate, cage, card-edge connector, host traces, switch ASIC with its heat sink,
and a co-packaged-optics package for the last section). Plus a framing camera.

Module frame: mm, Y up, the module's centre at x = 0, the optical port (faceplate side) toward -x,
the card edge toward +x (into the switch). The camera sits on +z, so cut-aways open the +z side.
Colours follow fiber_kit.materials() (board green, copper, gold, die, steel, light orange, elec cyan).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, fly, key, show, tube, ball  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402
import fiber_kit as K  # noqa: E402

# ---- module dimensions (an OSFP is ~100 x 22.6 x 13 mm; drawn a little shorter) ----------------
FRONT = -36.0           # front face of the nose
NOSE = -33.0            # back of the nose block
REAR = 28.0             # rear face of the shell
HW = 11.0               # shell half-width (z)
FLOOR = (-6.0, -5.0)    # shell floor (y)
PCB = (-5.0, -4.2)      # module PCB (y)
TOP = PCB[1]            # parts sit on the PCB here
LID = (3.0, 4.5)        # the shell's lid (y)
FIN_TOP = 11.0
FIN_Z = [-9.6 + 1.6 * k for k in range(13)]
PCB_X = (-31.0, 37.0)
EDGE_X = (29.0, 36.5)   # gold card-edge fingers
FINGER_Z = [-7.7 + 1.1 * k for k in range(15)]
CUT_X = 14.0            # in the "cut" shell, the lid and fins stay only behind this x

BEAM_Y = TOP + 1.25     # height of the light path in the TOSA / ROSA
TOSA = ((-28.0, TOP, -9.0), (-17.0, TOP + 3.2, -1.2))
ROSA = ((-28.0, TOP, 1.2), (-17.0, TOP + 3.2, 9.0))
LASER_Z = [-5.1 + 0.85 * (i - 3.5) for i in range(8)]
PD_Z = [5.1 + 0.85 * (i - 3.5) for i in range(8)]
MPO_Z = [-3.75 + 0.5 * k for k in range(16)]  # 16 fibre positions in one row: TX 0-7, RX 8-15
LASER_X = (-20.5, -19.0)
LENS_X = -23.0
FAU_X = (-27.2, -25.0)
DRIVER = ((-13.5, TOP, -8.0), (-8.0, TOP + 1.0, -2.0))
TIA = ((-13.5, TOP, 2.0), (-8.0, TOP + 1.0, 8.0))
DSP_SUB = ((-4.0, TOP + 0.5, -7.5), (11.0, TOP + 1.2, 7.5))
DSP_DIE = ((0.0, TOP + 1.4, -3.5), (7.0, TOP + 2.2, 3.5))
DSP_PAD = ((0.2, TOP + 2.2, -3.3), (6.8, TOP + 2.6, 3.3))
MCU = ((15.0, TOP, 4.5), (19.0, TOP + 0.9, 8.0))
REG = ((15.0, TOP, -8.0), (18.0, TOP + 0.9, -4.5))
MPO_REC = ((-38.0, -4.6, -5.0), (-32.0, -1.3, 5.0))

# ---- host side -------------------------------------------------------------------------------
BOARD_Y = -7.0
CAGE = ((-36.5, BOARD_Y, -12.0), (41.0, 12.5, 12.0))
CONN = ((28.5, BOARD_Y, -10.5), (40.5, -1.0, 10.5))
SLOT = (-5.3, -3.9)
HOST_TRACE_Z = [-5.6 + 1.6 * k for k in range(8)]


def mats():
    """fiber_kit's materials plus the opaque extras these parts use (no see-through housings)."""
    m = K.materials()
    m["shell"] = mat("fm_shell", (0.30, 0.32, 0.36), metal=0.7, rough=0.40)
    m["fin"] = mat("fm_fin", (0.62, 0.65, 0.70), metal=0.8, rough=0.35)
    m["cage_m"] = mat("fm_cage", (0.74, 0.76, 0.79), metal=0.85, rough=0.30)
    m["vent"] = mat("fm_vent", (0.05, 0.05, 0.06), rough=0.8)
    m["mpcb"] = mat("fm_mpcb", (0.06, 0.26, 0.16), rough=0.6)
    m["plastic"] = mat("fm_plastic", (0.07, 0.07, 0.08), rough=0.6)
    m["tab"] = mat("fm_tab", (0.20, 0.42, 0.62), rough=0.5)
    m["pkg"] = mat("fm_pkg", (0.78, 0.66, 0.42), metal=0.85, rough=0.30)  # gold-plated optics package
    m["ceramic"] = mat("fm_ceramic", (0.90, 0.88, 0.82), rough=0.6)
    m["inp"] = mat("fm_inp", (0.34, 0.24, 0.40), metal=0.3, rough=0.35)    # InP laser / PD chips
    m["lens"] = mat("fm_lens", (0.70, 0.88, 1.00), rough=0.05, alpha=0.75)
    m["fibre"] = mat("fm_fibre", (0.88, 0.93, 0.96), rough=0.25)
    m["jacket"] = mat("fm_jacket", (0.95, 0.78, 0.12), rough=0.5)         # OS2 single-mode yellow
    m["pad"] = mat("fm_pad", (0.42, 0.52, 0.68), rough=0.9)               # thermal gap pad
    m["smd"] = mat("fm_smd", (0.72, 0.58, 0.38), rough=0.5)
    m["alu"] = mat("fm_alu", (0.80, 0.82, 0.85), metal=0.85, rough=0.30)
    m["siph"] = mat("fm_siph", (0.22, 0.38, 0.62), metal=0.4, rough=0.30)
    m["heat"] = mat("fm_heat", (1.00, 0.50, 0.20), emit=(1.00, 0.45, 0.15), strength=3.0, alpha=0.6)
    m["hot"] = mat("fm_hot", (1.00, 0.45, 0.15), emit=(1.00, 0.40, 0.10), strength=2.5)
    m["elec_soft"] = mat("fm_elec_soft", (0.30, 0.85, 1.00), emit=(0.20, 0.85, 1.00), strength=1.6)
    m["light_soft"] = mat("fm_light_soft", (1.00, 0.45, 0.25), emit=(1.00, 0.35, 0.15), strength=2.5)
    for k, c in enumerate([(0.65, 0.35, 1.00), (0.25, 0.60, 1.00), (0.30, 1.00, 0.45), (1.00, 0.30, 0.30)]):
        m[f"cw{k}"] = mat(f"fm_cw{k}", c, emit=c, strength=5.0)  # CWDM lanes, false colour
    m["aqua"] = mat("fm_aqua", (0.25, 0.80, 0.80), rough=0.5)              # OM4 multimode aqua
    m["twinax"] = mat("fm_twinax", (0.10, 0.10, 0.11), rough=0.6)
    m["scarce"] = mat("fm_scarce", (1.00, 0.20, 0.15), emit=(1.00, 0.15, 0.10), strength=3.0)
    m["air"] = mat("fm_air", (0.80, 0.90, 1.00), emit=(0.70, 0.85, 1.00), strength=0.8, alpha=0.35)
    return m


def grp(name, parent, intervals=None):
    """An empty, switched on only during `intervals` if given."""
    g = empty(name, parent)
    if intervals is not None:
        show(g, intervals)
    return g


def add(p, d):
    return tuple(p[i] + d[i] for i in range(3))


# ---- the module ------------------------------------------------------------------------------


def wire(name, pts, r, m, parent):
    """A wire through `pts`: a tube per segment, a ball at each joint so it reads as one piece
    (the same helper as fiber_photodiode_detail.wire, copied so the pages stay independent)."""
    g = empty(name, parent)
    for k in range(len(pts) - 1):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, m, g, 8)
        if k:
            ball(f"{name}_j{k}", pts[k], r, m, g, 8)
    return g


def run(parent, name, pts, n, size, m, b, u0, u1, life):
    """`n` beads that each ride the absolute polyline `pts` over `life` frames, launched one after
    another between fractions u0 and u1 of beat `b` (as fiber_photodiode_detail.run)."""
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, m, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, len(pts) * 2))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


def chip_arc(i, rx):
    """Bond wire from the driver (or TIA) top edge, arched, down to lead i's inner end."""
    z = (PD_Z if rx else LASER_Z)[i]
    zd = (2.5 + 5.0 * i / 7) if rx else (-7.5 + 5.0 * i / 7)
    return [(-13.2, TOP + 1.0, zd), (-13.7, TOP + 1.8, zd * 0.7 + z * 0.3), (-14.5, TOP + 1.7, zd * 0.3 + z * 0.7), (-15.0, TOP + 0.5, z)]


def die_arc(i, rx):
    """Bond wire from lead i's outer end, arched, onto the laser (or photodiode) chip."""
    z = (PD_Z if rx else LASER_Z)[i]
    xe = -20.25 if rx else -19.4
    ye = TOP + 1.6 if rx else TOP + 1.5
    return [(-18.4, TOP + 0.5, z), (-18.5, TOP + 1.7, z), (xe + 0.4, ye + 0.45, z), (xe, ye, z)]


def lane_path(i, rx=False):
    """The bead path for lane i through its bond wires and lead: driver to laser, or photodiode to TIA."""
    pts = chip_arc(i, rx) + [(-18.4, TOP + 0.55, (PD_Z if rx else LASER_Z)[i])] + die_arc(i, rx)[1:]
    return list(reversed(pts)) if rx else pts


def bond_pair(m, g, name, i, rx):
    wire(f"{name}_c", chip_arc(i, rx), 0.07, m["gold"], g)
    wire(f"{name}_d", die_arc(i, rx), 0.07, m["gold"], g)


def cpo_package(m, parent, cx, name="cpo"):
    """A co-packaged-optics switch package at x = cx: substrate, lidded ASIC under a finned heat
    sink, eight optical engines round it (silicon photonics, driver/TIA die, fibre block) with
    yellow fibre stubs leaving outward."""
    g = empty(name, parent)
    y = BOARD_Y
    box(f"{name}_sub", (cx - 26, y + 0.6, -26), (cx + 26, y + 2.0, 26), m["substrate"], g)
    box(f"{name}_balls", (cx - 25, y, -25), (cx + 25, y + 0.6, 25), m["gold"], g)
    box(f"{name}_lid", (cx - 13, y + 2.0, -13), (cx + 13, y + 4.0, 13), m["steel"], g)
    box(f"{name}_sink", (cx - 12, y + 4.0, -12), (cx + 12, y + 6.0, 12), m["alu"], g)
    for k in range(8):
        z = -11.0 + 22.0 * k / 7
        box(f"{name}_fin_{k}", (cx - 12, y + 6.0, z - 0.45), (cx + 12, y + 22.0, z + 0.45), m["alu"], g)
    w = 3.6
    spots = [(cx + dx, dz, (sx, sz)) for (dx, dz, sx, sz) in
             [(-20, -7, -1, 0), (-20, 7, -1, 0), (20, -7, 1, 0), (20, 7, 1, 0), (-7, -20, 0, -1), (7, -20, 0, -1), (-7, 20, 0, 1), (7, 20, 0, 1)]]
    for i, (x, z, (sx, sz)) in enumerate(spots):
        box(f"{name}_oe{i}_pic", (x - w, y + 2.0, z - w), (x + w, y + 2.7, z + w), m["siph"], g)
        box(f"{name}_oe{i}_eic", (x - 1.8, y + 2.7, z - 1.8), (x + 1.8, y + 3.4, z + 1.8), m["die"], g)
        fx, fz = x + sx * (w - 0.8), z + sz * (w - 0.8)
        box(f"{name}_oe{i}_fau", (fx - (0.8 if sx else 2.6), y + 2.7, fz - (0.8 if sz else 2.6)), (fx + (0.8 if sx else 2.6), y + 3.9, fz + (0.8 if sz else 2.6)), m["lens"], g)
        tube(f"{name}_oe{i}_fibre", (x + sx * w, y + 3.3, z + sz * w), (x + sx * (w + 12), y + 3.3, z + sz * (w + 12)), 0.7, m["jacket"], g, 10)
    return g


def optics_pkg(m, g, tag, lo, hi, lid):
    """A gold-plated optics package: floor, walls (no near wall: the cut-away side), lid if asked."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    t = 0.4
    box(f"{tag}_floor", (x0, y0, z0), (x1, y0 + 0.4, z1), m["pkg"], g)
    box(f"{tag}_far", (x0, y0, z0), (x1, y1, z0 + t), m["pkg"], g)
    box(f"{tag}_back", (x1 - t, y0, z0), (x1, y1, z1), m["pkg"], g)
    box(f"{tag}_front", (x0, y0, z0), (x0 + t, y1, z1), m["pkg"], g)
    if lid:
        box(f"{tag}_near", (x0, y0, z1 - t), (x1, y1, z1), m["pkg"], g)
        box(f"{tag}_lid", (x0, y1, z0), (x1, y1 + 0.35, z1), m["pkg"], g)


def tosa(m, g, lid, fau=True):
    optics_pkg(m, g, "tosa", *TOSA, lid)
    zc = (TOSA[0][2] + TOSA[1][2]) / 2
    box("tosa_submount", (-21.0, TOP + 0.4, -8.5), (-18.5, TOP + 1.0, -1.7), m["ceramic"], g)
    if fau:
        box("tosa_fau", (FAU_X[0], TOP + 0.4, -8.5), (FAU_X[1], TOP + 1.9, -1.7), m["lens"], g)
    for i, z in enumerate(LASER_Z):
        box(f"laser_{i}", (LASER_X[0], TOP + 1.0, z - 0.25), (LASER_X[1], TOP + 1.5, z + 0.25), m["inp"], g)
        # EML anatomy: the electro-absorption modulator's own gold electrode at the output (front)
        # end, the DFB laser's electrode behind it, and a monitor photodiode on the rear facet
        box(f"laser_ea_pad_{i}", (LASER_X[0] + 0.05, TOP + 1.5, z - 0.13), (LASER_X[0] + 0.45, TOP + 1.56, z + 0.13), m["gold"], g)
        box(f"laser_dfb_pad_{i}", (LASER_X[0] + 0.65, TOP + 1.5, z - 0.13), (LASER_X[1] - 0.1, TOP + 1.56, z + 0.13), m["gold"], g)
        box(f"laser_mpd_{i}", (LASER_X[1] + 0.05, TOP + 1.0, z - 0.2), (LASER_X[1] + 0.4, TOP + 1.4, z + 0.2), m["die"], g)
        ball(f"tosa_lens_{i}", (LENS_X, BEAM_Y, z), 0.36, m["lens"], g)
        # RF feedthrough: a gold lead from the driver through the back wall to each laser
        box(f"tosa_lead_{i}", (-18.5, TOP + 0.4, z - 0.12), (-15.0, TOP + 0.5, z + 0.12), m["gold"], g)
        bond_pair(m, g, f"tosa_bond_{i}", i, rx=False)
    # optical isolator between the lens row and the fibre block: stops reflections re-entering the lasers
    box("tosa_isolator", (-24.7, BEAM_Y - 0.55, -8.3), (-24.1, BEAM_Y + 0.55, -1.9), m["ceramic"], g)
    for s in (-1, 1):
        box(f"tosa_isolator_magnet_{s}", (-24.8, BEAM_Y + s * 0.55 - (0.2 if s < 0 else 0.0), -8.3), (-24.0, BEAM_Y + s * 0.55 + (0.2 if s > 0 else 0.0), -1.9), m["dark_steel"], g)
    # thermoelectric cooler under the laser submount: EMLs hold their wavelength only at a fixed temperature
    for k in range(6):
        z = -8.2 + 1.2 * k
        box(f"tosa_tec_pellet_{k}", (-21.5, TOP + 0.4, z), (-21.1, TOP + 0.95, z + 0.5), m["ceramic"], g)
    return zc


def rosa(m, g, lid, fau=True):
    optics_pkg(m, g, "rosa", *ROSA, lid)
    box("rosa_submount", (-21.0, TOP + 0.4, 1.7), (-18.5, TOP + 1.0, 8.5), m["ceramic"], g)
    if fau:
        box("rosa_fau", (FAU_X[0], TOP + 0.4, 1.7), (FAU_X[1], TOP + 1.9, 8.5), m["lens"], g)
    for i, z in enumerate(PD_Z):
        box(f"pd_{i}", (-20.5, TOP + 1.0, z - 0.3), (-20.0, TOP + 1.6, z + 0.3), m["inp"], g)
        box(f"pd_eye_{i}", (-20.6, BEAM_Y - 0.15, z - 0.15), (-20.5, BEAM_Y + 0.15, z + 0.15), m["gold"], g)
        ball(f"rosa_lens_{i}", (LENS_X, BEAM_Y, z), 0.36, m["lens"], g)
        box(f"rosa_lead_{i}", (-18.5, TOP + 0.4, z - 0.12), (-15.0, TOP + 0.5, z + 0.12), m["gold"], g)
        bond_pair(m, g, f"rosa_bond_{i}", i, rx=True)


def fibre_runs(m, g):
    """Bare fibres from each package's fibre block to the back of the MPO receptacle."""
    for i in range(8):
        for tag, zs, k in (("tx", LASER_Z, i), ("rx", PD_Z, 8 + i)):
            a = (FAU_X[0] - 0.8, BEAM_Y, zs[i])
            b = (-30.0, BEAM_Y, zs[i] * 0.75 + MPO_Z[k] * 0.25)
            c = (MPO_REC[1][0], BEAM_Y, MPO_Z[k])
            tube(f"{tag}_fib_{i}_a", (FAU_X[0], BEAM_Y, zs[i]), a, 0.12, m["fibre"], g, 6)
            tube(f"{tag}_fib_{i}_b", a, b, 0.12, m["fibre"], g, 6)
            tube(f"{tag}_fib_{i}_c", b, c, 0.12, m["fibre"], g, 6)
    # the fibres pass through the packages' front walls in a strain-relief boot
    box("tx_boot", (-29.5, BEAM_Y - 0.5, -8.6), (-28.0, BEAM_Y + 0.5, -1.6), m["plastic"], g)
    box("rx_boot", (-29.5, BEAM_Y - 0.5, 1.6), (-28.0, BEAM_Y + 0.5, 8.6), m["plastic"], g)


def mpo_receptacle(m, g):
    (x0, y0, z0), (x1, y1, z1) = MPO_REC
    box("mpo_body", (x0 + 0.6, y0, z0), (x1, y1, z1), m["plastic"], g)
    box("mpo_ferrule", (x0, BEAM_Y - 0.7, -4.2), (x0 + 0.6, BEAM_Y + 0.7, 4.2), m["ceramic"], g)
    for k, z in enumerate(MPO_Z):
        box(f"mpo_end_{k}", (x0 - 0.05, BEAM_Y - 0.15, z - 0.15), (x0, BEAM_Y + 0.15, z + 0.15),
            m["fibre"], g)
    for s in (-1, 1):
        tube(f"mpo_pin_hole_{s}", (x0 - 0.06, BEAM_Y, 4.6 * s), (x0 + 0.5, BEAM_Y, 4.6 * s), 0.3, m["vent"], g, 10)


def dsp(m, g):
    (x0, y0, z0), (x1, y1, z1) = DSP_SUB
    for i in range(6):
        for j in range(6):
            x = x0 + 1.2 + (x1 - x0 - 2.4) * i / 5
            z = z0 + 1.2 + (z1 - z0 - 2.4) * j / 5
            tube(f"dsp_ball_{i}_{j}", (x, TOP, z), (x, y0, z), 0.32, m["gold"], g, 8)
    box("dsp_substrate", DSP_SUB[0], DSP_SUB[1], m["substrate"], g)
    box("dsp_underfill", (DSP_DIE[0][0] - 0.3, y1, DSP_DIE[0][2] - 0.3), (DSP_DIE[1][0] + 0.3, DSP_DIE[0][1], DSP_DIE[1][2] + 0.3), m["plastic"], g)
    box("dsp_die", DSP_DIE[0], DSP_DIE[1], m["die"], g)
    box("dsp_pad", DSP_PAD[0], DSP_PAD[1], m["pad"], g)
    # decoupling capacitors round the die, on the substrate
    for k, (x, z) in enumerate([(-2.5, -6), (-2.5, 6), (9.5, -6), (9.5, 6), (3.5, -6.3), (3.5, 6.3)]):
        box(f"dsp_cap_{k}", (x - 0.5, y1, z - 0.3), (x + 0.5, y1 + 0.5, z + 0.3), m["smd"], g)


def chips(m, g):
    for tag, (lo, hi) in (("driver", DRIVER), ("tia", TIA)):
        box(f"{tag}_body", lo, hi, m["die"], g)
        # leads along both long sides
        for k in range(6):
            z = lo[2] + 0.5 + (hi[2] - lo[2] - 1.0) * k / 5
            for x in (lo[0] - 0.3, hi[0]):
                box(f"{tag}_leg_{k}_{x}", (x, TOP, z - 0.15), (x + 0.3, TOP + 0.25, z + 0.15), m["steel"], g)
    box("mcu", MCU[0], MCU[1], m["plastic"], g)
    box("reg", REG[0], REG[1], m["plastic"], g)
    box("inductor", (20.0, TOP, -8.0), (23.0, TOP + 1.8, -5.0), m["dark_steel"], g)
    for k, (x, z) in enumerate([(20.5, 5.0), (20.5, 7.0), (22.5, 6.0), (-15.5, -5.0), (-15.5, 5.0), (13.0, -2.0), (13.0, 2.0)]):
        box(f"cap_{k}", (x - 0.5, TOP, z - 0.3), (x + 0.5, TOP + 0.55, z + 0.3), m["smd"], g)


def traces(m, g):
    """Copper on the module PCB: fingers to DSP, DSP to driver, TIA to DSP."""
    y0, y1 = TOP, TOP + 0.04
    for k in range(8):
        z = -3.5 + 1.0 * k
        box(f"tr_edge_{k}", (11.0, y0, z - 0.18), (EDGE_X[0], y1, z + 0.18), m["copper"], g)
    for k in range(4):
        z = -6.5 + 1.1 * k
        box(f"tr_drv_{k}", (DRIVER[1][0] + 0.3, y0, z - 0.15), (DSP_SUB[0][0], y1, z + 0.15), m["copper"], g)
        box(f"tr_tia_{k}", (TIA[1][0] + 0.3, y0, -z - 0.15), (DSP_SUB[0][0], y1, -z + 0.15), m["copper"], g)


def card_edge(m, g):
    for k, z in enumerate(FINGER_Z):
        box(f"finger_top_{k}", (EDGE_X[0], TOP, z - 0.35), (EDGE_X[1], TOP + 0.05, z + 0.35), m["gold"], g)
        box(f"finger_bot_{k}", (EDGE_X[0], PCB[0] - 0.05, z - 0.35), (EDGE_X[1], PCB[0], z + 0.35), m["gold"], g)


def shell(m, g, lid):
    """The finned shell. lid: "full" (closed), "cut" (lid, fins and near wall only behind CUT_X,
    so the front of the board shows), "none" (no lid at all, near wall gone)."""
    box("shell_floor", (NOSE, FLOOR[0], -HW), (REAR, FLOOR[1], HW), m["shell"], g)
    box("shell_nose", (FRONT, FLOOR[0], -HW), (NOSE, LID[1], HW), m["shell"], g)
    box("shell_far", (NOSE, FLOOR[1], -HW), (REAR, LID[0], -HW + 1.0), m["shell"], g)
    box("shell_rear", (REAR - 1.0, -4.0, -HW), (REAR, LID[0], HW), m["shell"], g)
    x_from = {"full": NOSE, "cut": CUT_X, "none": None}[lid]
    if x_from is None:
        return
    box("shell_near", (x_from, FLOOR[1], HW - 1.0), (REAR, LID[0], HW), m["shell"], g)
    box("shell_lid", (x_from, LID[0], -HW), (REAR, LID[1], HW), m["shell"], g)
    if lid == "full":
        # the lid's pedestal down onto the DSP's thermal pad
        box("shell_pedestal", (DSP_PAD[0][0], DSP_PAD[1][1], DSP_PAD[0][2]), (DSP_PAD[1][0], LID[0], DSP_PAD[1][2]), m["shell"], g)
    fx0 = max(x_from, -30.0)
    for k, z in enumerate(FIN_Z):
        box(f"fin_{k}", (fx0, LID[1], z - 0.3), (REAR - 3.0, FIN_TOP, z + 0.3), m["fin"], g)


def pull_tab(m, g):
    box("tab_strip", (-52.0, -5.6, -4.0), (FRONT, -5.0, 4.0), m["tab"], g)
    box("tab_grip", (-54.0, -5.6, -4.5), (-51.0, -4.4, 4.5), m["tab"], g)


def module(m, parent, lid="full", pkg_lid=True, name="module", optics="dr8", with_dsp=True):
    """The whole pluggable in one group at the origin (key its location to slide it).
    optics: "dr8" (8 lasers, 8 fibres each way, an MPO-16 port) or "fr4" (2xFR4: each set of
    4 lasers muxed onto one fibre, two duplex LC ports). with_dsp=False draws a linear (LPO) board:
    no DSP, the card-edge traces run straight on toward the driver and TIA."""
    g = empty(name, parent)
    shell(m, g, lid)
    pull_tab(m, g)
    box("mod_pcb", (PCB_X[0], PCB[0], -9.5), (PCB_X[1], PCB[1], 9.5), m["mpcb"], g)
    card_edge(m, g)
    traces(m, g)
    if with_dsp:
        dsp(m, g)
    else:
        for k in range(4):
            z = -6.5 + 1.1 * k
            for zz in (z, -z):
                box(f"tr_lpo_{zz}", (DSP_SUB[0][0], TOP, zz - 0.15), (DSP_SUB[1][0] + 0.3, TOP + 0.04, zz + 0.15), m["copper"], g)
        for k in range(8):  # the card-edge traces fan out to the driver/TIA lines
            z = -3.5 + 1.0 * k
            zt = (-6.5 + 1.1 * (k % 4)) * (1 if k < 4 else -1)
            box(f"tr_lpo_join_{k}", (DSP_SUB[1][0] + 0.1, TOP, min(z, zt) - 0.15), (DSP_SUB[1][0] + 0.5, TOP + 0.04, max(z, zt) + 0.15), m["copper"], g)
    chips(m, g)
    if lid == "full":
        # gap pads from the driver and TIA up into the lid: their heat path, like the DSP's pad
        for tag, (lo, hi) in (("driver", DRIVER), ("tia", TIA)):
            box(f"{tag}_gap_pad", (lo[0] + 0.3, hi[1], lo[2] + 0.3), (hi[0] - 0.3, LID[0], hi[2] - 0.3), m["pad"], g)
    fr4 = optics == "fr4"
    tosa(m, g, pkg_lid, fau=not fr4)
    rosa(m, g, pkg_lid, fau=not fr4)
    if fr4:
        fr4_optics(m, g)
    else:
        fibre_runs(m, g)
        mpo_receptacle(m, g)
    return g


# 2xFR4: two mux blocks in the TOSA, two demux blocks in the ROSA, two duplex LC ports.
MUX_Z = ((-8.5, -5.2), (-5.0, -1.7))
LC_Z = (-4.5, 4.5)                       # port centres
LC_HOLE = {"tx0": -6.1, "rx0": -2.9, "tx1": 2.9, "rx1": 6.1}


def fr4_paths():
    """name -> polyline from the mux/demux face to its LC hole. Crossing fibres hop up."""
    out = {}
    for j, (z0, z1) in enumerate(MUX_Z):
        zc = (z0 + z1) / 2
        for side, s in (("tx", 1), ("rx", -1)):
            a = (FAU_X[0], BEAM_Y, s * zc)
            hole = LC_HOLE[f"{side}{j}"]
            hop = 0.9 if (s * zc) * hole < 0 else 0.0
            out[f"{side}{j}"] = [a, (-29.0, BEAM_Y + hop, s * zc), (-31.0, BEAM_Y + hop, hole), (MPO_REC[1][0], BEAM_Y, hole)]
    return out


def fr4_optics(m, g):
    for j, (z0, z1) in enumerate(MUX_Z):
        box(f"mux_{j}", (FAU_X[0], TOP + 0.4, z0), (FAU_X[1], TOP + 1.9, z1), m["lens"], g)
        box(f"demux_{j}", (FAU_X[0], TOP + 0.4, -z1), (FAU_X[1], TOP + 1.9, -z0), m["lens"], g)
    for name, pts in fr4_paths().items():
        for k in range(len(pts) - 1):
            tube(f"fr4_fib_{name}_{k}", pts[k], pts[k + 1], 0.14, m["fibre"], g, 6)
    (x0, y0, _), (x1, y1, _) = MPO_REC
    for j, zc in enumerate(LC_Z):
        box(f"lc_body_{j}", (x0 + 0.6, y0, zc - 3.4), (x1, y1, zc + 3.4), m["plastic"], g)
        for hole in (zc - 1.6, zc + 1.6):
            box(f"lc_bore_{j}_{hole}", (x0, BEAM_Y - 0.9, hole - 0.9), (x0 + 0.6, BEAM_Y + 0.9, hole + 0.9), m["vent"], g)
            tube(f"lc_ferrule_{j}_{hole}", (x0 - 0.1, BEAM_Y, hole), (x0 + 0.6, BEAM_Y, hole), 0.45, m["ceramic"], g, 12)


def lid_part(m, parent, name="lid"):
    """The shell's lid on its own (near wall, lid, pedestal, fins) in a group at the origin, for a
    module built with lid="none" whose lid comes and goes."""
    g = empty(name, parent)
    box(f"{name}_near", (NOSE, FLOOR[1], HW - 1.0), (REAR, LID[0], HW), m["shell"], g)
    box(f"{name}_plate", (NOSE, LID[0], -HW), (REAR, LID[1], HW), m["shell"], g)
    box(f"{name}_pedestal", (DSP_PAD[0][0], DSP_PAD[1][1], DSP_PAD[0][2]), (DSP_PAD[1][0], LID[0], DSP_PAD[1][2]), m["shell"], g)
    for k, z in enumerate(FIN_Z):
        box(f"{name}_fin_{k}", (-30.0, LID[1], z - 0.3), (REAR - 3.0, FIN_TOP, z + 0.3), m["fin"], g)
    return g


def qsfpdd(m, parent, name="qsfpdd"):
    """A QSFP-DD at the same scale as the OSFP: a smaller, flat shell with no fins (~89 x 18.4 x
    8.5 mm against the OSFP's ~100 x 22.6 x 13), its pull tab and a card edge with two rows of fingers."""
    g = empty(name, parent)
    hw, x0, x1, y1 = 9.0, FRONT, FRONT + 57.0, FLOOR[0] + 8.5
    box(f"{name}_body", (x0 + 3.0, FLOOR[0], -hw), (x1, y1, hw), m["shell"], g)
    box(f"{name}_nose", (x0, FLOOR[0], -hw), (x0 + 3.0, y1 + 0.4, hw), m["shell"], g)
    box(f"{name}_label", (x0 + 12.0, y1, -hw + 1.5), (x1 - 8.0, y1 + 0.05, hw - 1.5), m["fin"], g)
    box(f"{name}_pcb", (x1 - 1.0, PCB[0], -hw + 1.0), (x1 + 8.0, PCB[1], hw - 1.0), m["mpcb"], g)
    for row, (xa, xb) in enumerate(((x1 + 0.5, x1 + 3.5), (x1 + 4.5, x1 + 7.5))):
        for k in range(12):
            z = -hw + 1.8 + (2 * hw - 3.6) * k / 11
            box(f"{name}_finger_{row}_{k}", (xa, TOP, z - 0.3), (xb, TOP + 0.05, z + 0.3), m["gold"], g)
    box(f"{name}_tab", (x0 - 14.0, FLOOR[0] + 0.4, -3.0), (x0, FLOOR[0] + 1.0, 3.0), m["tab"], g)
    box(f"{name}_grip", (x0 - 16.0, FLOOR[0] + 0.4, -3.5), (x0 - 13.0, FLOOR[0] + 1.8, 3.5), m["tab"], g)
    return g


def meshes(g):
    for c in g.children:
        if c.type == "MESH":
            yield c
        yield from meshes(c)


def cut_x(obj, x):
    """Remove the part of `obj` behind the plane x = `x` (x larger) and cap the opening: a cross
    section across the module. Like sand_overview.cut, in the object's parent's frame (the parents
    must sit at identity while this runs)."""
    import bmesh
    from mathutils import Matrix
    me = obj.data
    me.transform(obj.matrix_basis)
    obj.matrix_basis = Matrix.Identity(4)
    bm = bmesh.new()
    bm.from_mesh(me)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(x, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return obj


# ---- host side -------------------------------------------------------------------------------


def host_board(m, parent, x0=-37.5, x1=95.0, hz=25.0):
    box("host_board", (x0, BOARD_Y - 3.0, -hz), (x1, BOARD_Y, hz), m["board"], parent)


def bezel(m, parent, z0=-25.0, z1=-12.0, top=20.0):
    box("bezel", (-37.6, BOARD_Y - 3.0, z0), (-36.6, top, z1), m["dark_steel"], parent)


def cage(m, parent, top=True, near=True, far=True):
    """The OSFP cage: sheet metal on the board round the module, its near (+z) side cut away
    (only a low strip left) and its top cut back to z < -5, vents in the far wall."""
    (x0, y0, z0), (x1, y1, z1) = CAGE
    t = 0.3
    g = empty("cage", parent)
    if far:
        box("cage_far", (x0, y0, z0), (x1, y1, z0 + t), m["cage_m"], g)
        for i in range(17):
            for j, y in enumerate((1.0, 5.0, 9.0)):
                x = x0 + 4.0 + 4.3 * i
                box(f"cage_vent_{i}_{j}", (x - 0.9, y - 0.9, z0 + t), (x + 0.9, y + 0.9, z0 + t + 0.02), m["vent"], g)
    box("cage_back", (x1 - t, y0, z0), (x1, y1, z1), m["cage_m"], g)
    if top:
        box("cage_top", (x0, y1 - t, z0), (x1, y1, -5.0), m["cage_m"], g)
        for k in range(4):  # EMI spring fingers at the mouth
            z = z0 + 1.0 + 1.7 * k
            box(f"cage_spring_{k}", (x0, y1, z), (x0 + 1.8, y1 + 0.35, z + 1.0), m["cage_m"], g)
    if near:
        box("cage_near", (x0, y0, z1 - t), (x1, y0 + 1.6, z1), m["cage_m"], g)
    return g


def connector(m, parent, cutaway=False):
    """The host's card-edge connector at the back of the cage: a black body with a slot at the
    height of the module PCB, gold spring contacts on the slot's floor."""
    (x0, y0, z0), (x1, y1, z1) = CONN
    g = empty("connector", parent)
    box("conn_low", (x0, y0, z0), (x1, SLOT[0], z1), m["plastic"], g)
    box("conn_up", (x0, SLOT[1], z0), (x1, y1, 0.0 if cutaway else z1), m["plastic"], g)
    box("conn_back", (37.5, SLOT[0], z0), (x1, SLOT[1], z1), m["plastic"], g)
    for k, z in enumerate(FINGER_Z):
        box(f"conn_contact_{k}", (x0 + 1.0, SLOT[0], z - 0.3), (x0 + 5.0, SLOT[0] + 0.12, z + 0.3), m["gold"], g)
    return g


def host_traces(m, parent, x0=40.5, x1=95.0):
    for k, z in enumerate(HOST_TRACE_Z):
        box(f"host_tr_{k}", (x0, BOARD_Y, z - 0.3), (x1, BOARD_Y + 0.04, z + 0.3), m["copper"], parent)


def asic(m, parent, cx, cz=0.0, half=20.0, sink=True, name="asic"):
    """A switch ASIC: BGA substrate, lidded package, a finned aluminium heat sink on top."""
    g = empty(name, parent)
    box(f"{name}_sub", (cx - half, BOARD_Y + 0.6, cz - half), (cx + half, BOARD_Y + 2.0, cz + half), m["substrate"], g)
    box(f"{name}_balls", (cx - half + 1, BOARD_Y, cz - half + 1), (cx + half - 1, BOARD_Y + 0.6, cz + half - 1), m["gold"], g)
    lh = half * 0.75
    box(f"{name}_lid", (cx - lh, BOARD_Y + 2.0, cz - lh), (cx + lh, BOARD_Y + 4.0, cz + lh), m["steel"], g)
    if sink:
        sh = half * 0.95
        box(f"{name}_sink_base", (cx - sh, BOARD_Y + 4.0, cz - sh), (cx + sh, BOARD_Y + 7.0, cz + sh), m["alu"], g)
        n = 11
        for k in range(n):
            z = cz - sh + 1.0 + (2 * sh - 2.0) * k / (n - 1)
            box(f"{name}_sink_fin_{k}", (cx - sh, BOARD_Y + 7.0, z - 0.5), (cx + sh, BOARD_Y + 30.0, z + 0.5), m["alu"], g)
    return g


# ---- the camera ------------------------------------------------------------------------------

TAN_V = math.tan(0.26)          # half the vertical field of view
TAN_H = TAN_V * 819.0 / 720.0   # the left pane is 819 x 720 of a 1280 x 720 frame


def frame(lo, hi, yaw, pitch, pad=1.18, shift=(0.0, 0.0, 0.0)):
    """A (target, distance, yaw, pitch) pose that fits the box lo..hi in the left pane."""
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    e = (cp * sy, sp, cp * cy)                      # toward the camera
    r = (cy, 0.0, -sy)                              # screen right
    u = (-sp * sy, cp, -sp * cy)                    # screen up
    c = tuple((lo[i] + hi[i]) / 2 + shift[i] for i in range(3))
    w = h = near = 0.0
    for x in (lo[0], hi[0]):
        for y in (lo[1], hi[1]):
            for z in (lo[2], hi[2]):
                d = (x - c[0], y - c[1], z - c[2])
                w = max(w, abs(sum(d[i] * r[i] for i in range(3))))
                h = max(h, abs(sum(d[i] * u[i] for i in range(3))))
                near = max(near, sum(d[i] * e[i] for i in range(3)))
    dist = max(h / TAN_V, w / TAN_H) * pad + near
    return (c, dist, yaw, pitch)


def glide_camera(root, poses, glide=0.28):
    """One pose per beat. The camera eases from the last pose into the next over the first `glide`
    of the beat, then pushes in slowly; beat 0 starts on its pose."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        cp, sp = math.cos(pitch), math.sin(pitch)
        a = F(i, 0) if i == 0 else F(i, glide)
        b = F(i + 1, 0) - 1
        for f, d in ((a, dist * 1.04), (b, dist * 0.97)):
            e = (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))
            key(target, f, "location", P(*t))
            key(eye, f, "location", P(*e))


def glow(parent, name, lo, hi, m, intervals, pad=0.08):
    """An emissive skin round a part, on during `intervals`: the part reads as active."""
    for j, iv in enumerate(intervals):
        g = grp(f"{name}_on{j}", parent, [iv])
        box(f"{name}_glow{j}", tuple(v - pad for v in lo), tuple(v + pad for v in hi), m, g)
