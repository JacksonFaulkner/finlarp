"""The nine numbered sections of the TRANSCEIVER page. Section N illustrates heading N of the page's
write-up (tui/src/screens/diagrams_pages/FIB_TRX.txt), so the menu title, the text pane and the
picture teach the same thing. The parts are the detailed builders in fiber_module_detail.py: an
800G OSFP DR8 module (finned shell cut open to its PCB, gold card-edge fingers, PAM4 DSP, laser
driver, TIA, TOSA with eight EML lasers, ROSA with eight photodiodes, fibres to an MPO-16 port), a
2xFR4 variant (mux blocks, duplex LC ports), a QSFP-DD, the switch's cage, connector, board and
ASIC, and a co-packaged-optics package.

Run from the repo root, one section per bake:

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_module_sections.py -- 3

It writes blender/fiber_module_section_<n>.blend and assets/fiber_module_section_<n>.glb. One beat is
8 s at 24 fps; each section has three beats (beat i covers frames 192*i .. 192*(i+1)). The camera
frames each beat's subject (detail.frame) and glides between beats.

  1 What happens      the module slides into its cage; the shell opens on its parts; it sends and receives at once
  2 The parts         OSFP beside QSFP-DD; DR8's MPO beside 2xFR4's duplex LCs; DAC beside AOC
  3 One module's job  lanes in and retimed; drivers, lasers, lenses, MPO; photodiodes, TIAs and the controller
  4 Reach             two switches: board copper and a DAC, then multimode (AOC/SR8), then single-mode (DR8/FR4)
  5 Lanes and speeds  8 lanes in at the card edge; DR8's 16 fibres; 2xFR4's 4 wavelengths per fibre
  6 Power and heat    a section through the DSP and fins; a row of ports at the faceplate; an LPO board, no DSP
  7 Scale             GPU servers to leaf switches, leaf to spine; a module at both ends of every link
  8 Who makes it      the module tagged with its makers; the lasers' suppliers; the lid going on (assembly)
  9 Chokepoints       EMLs and DSPs lit as the scarce parts; a tray of modules (where they are made); CPO
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, key, label, tube  # noqa: E402
from sand_zooms import start, finish, stream_of  # noqa: E402
from pbr_kit import empty  # noqa: E402
import fiber_module_detail as D  # noqa: E402
from fiber_module_detail import frame, glide_camera, glow, grp  # noqa: E402

_so0 = stream_of


def stream_of(parent, name, n, start_pt, path, size, m, b, u0, u1, life):
    """Denser flows: twice the beads, slightly smaller."""
    return _so0(parent, name, max(3, 2 * n), start_pt, path, size * 0.85, m, b, u0, u1, life)


PAGE = "fiber_module"
BEATS = 3
END = F(BEATS, 0)
B0, B1, B2 = beat(0), beat(1), beat(2)
TOP = D.TOP
BY = D.BEAM_Y


def begin(n):
    _, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    return D.mats(), root


# The renderer's near plane is 40 units from the eye, closer than these millimetre-sized close-ups
# need, so the whole scene (camera and tags included) is scaled up by S under its root at the end.
S = 6.0


def done(n, root):
    root.scale = (S, S, S)
    finish(f"section_{n}", page=PAGE)


def host(m, parent, cage_top=False, conn_cut=False, x1=95.0):
    """The switch side round the module: board, faceplate, cage, connector, host traces."""
    D.host_board(m, parent, x1=x1)
    D.bezel(m, parent)
    D.cage(m, parent, top=cage_top)
    D.connector(m, parent, cutaway=conn_cut)
    D.host_traces(m, parent, x1=x1)


def placed(parent, name, intervals=None):
    """A show switch with a placement empty inside: build at the origin, then set .location."""
    return empty(f"{name}_at", grp(name, parent, intervals))


def pkg_lid(m, parent, which, intervals):
    """The near wall and lid of the TOSA or ROSA, shown only during `intervals`."""
    (x0, y0, z0), (x1, y1, z1) = D.TOSA if which == "tosa" else D.ROSA
    g = grp(f"{which}_closed", parent, intervals)
    box(f"{which}_near_wall", (x0, y0, z1 - 0.4), (x1, y1, z1), m["pkg"], g)
    box(f"{which}_top", (x0, y1, z0), (x1, y1 + 0.35, z1), m["pkg"], g)
    return g


def fibre_path(i, rx=False):
    """The polyline of fibre i from its lens to the MPO face (absolute points)."""
    zs = D.PD_Z if rx else D.LASER_Z
    k = 8 + i if rx else i
    return [
        (D.LENS_X, BY, zs[i]),
        (D.FAU_X[0] - 0.8, BY, zs[i]),
        (-30.0, BY, zs[i] * 0.75 + D.MPO_Z[k] * 0.25),
        (D.MPO_REC[0][0], BY, D.MPO_Z[k]),
    ]


def rel(path):
    return [tuple(p[j] - path[0][j] for j in range(3)) for p in path]


# ---- signal streams on a module at the origin (DR8) ---------------------------------------------


def lanes_in(root, m, b, tag="in"):
    """The host's 8 lanes: card-edge fingers to the DSP."""
    for k in range(8):
        stream_of(root, f"{tag}_{k}", 3, (34.0, TOP + 0.3, -3.5 + k), [(0, 0, 0), (-23.0, 0, 0)], 0.3, m["elec"], b, 0.05 + 0.03 * k, 0.7, 40)


def lanes_out(root, m, b, tag="out"):
    for k in range(8):
        stream_of(root, f"{tag}_{k}", 3, (11.0, TOP + 0.3, -3.5 + k), [(0, 0, 0), (23.0, 0, 0)], 0.3, m["elec"], b, 0.05 + 0.03 * k, 0.7, 40)


def dsp_to_driver(root, m, b, tag="drv"):
    for k in range(4):
        stream_of(root, f"{tag}_{k}", 2, (-4.0, TOP + 0.3, -6.5 + 1.1 * k), [(0, 0, 0), (-3.7, 0, 0)], 0.3, m["elec"], b, 0.05 + 0.04 * k, 0.7, 24)


def tia_to_dsp(root, m, b, tag="tia"):
    for k in range(4):
        stream_of(root, f"{tag}_{k}", 2, (-7.7, TOP + 0.3, 6.5 - 1.1 * k), [(0, 0, 0), (3.7, 0, 0)], 0.3, m["elec"], b, 0.10 + 0.04 * k, 0.75, 24)


def driver_to_lasers(root, m, b, tag="lead"):
    for i, z in enumerate(D.LASER_Z):
        stream_of(root, f"{tag}_{i}", 2, (-13.5, TOP + 0.6, z), [(0, 0, 0), (-5.5, 0, 0)], 0.22, m["elec"], b, 0.05 + 0.02 * i, 0.7, 30)


def pds_to_tia(root, m, b, tag="pdc"):
    for i, z in enumerate(D.PD_Z):
        stream_of(root, f"{tag}_{i}", 2, (-18.5, TOP + 0.6, z), [(0, 0, 0), (5.0, 0, 0)], 0.22, m["elec"], b, 0.05 + 0.02 * i, 0.7, 30)


def tx_light(root, m, b, tag="tx", u0=0.05):
    """Light from each laser along its fibre and out of the MPO."""
    for i in range(8):
        path = fibre_path(i)
        path = path + [(path[-1][0] - 15.0, BY, path[-1][2])]
        stream_of(root, f"{tag}_{i}", 2, path[0], rel(path), 0.45, m["light"], b, u0 + 0.03 * i, 0.6, 50)


def rx_light(root, m, b, tag="rx", u0=0.02):
    """Light in at the MPO, along each fibre to its photodiode."""
    for i in range(8):
        path = list(reversed(fibre_path(i, rx=True)))
        path = [(-52.0, BY, path[0][2])] + path + [(-20.5, BY, D.PD_Z[i])]
        stream_of(root, f"{tag}_{i}", 2, path[0], rel(path), 0.45, m["light"], b, u0 + 0.03 * i, 0.55, 60)


def lasers_lit(parent, m, intervals, mat_="light_soft", tag="las"):
    for i, z in enumerate(D.LASER_Z):
        glow(parent, f"{tag}_{i}", (D.LASER_X[0], TOP + 1.0, z - 0.25), (D.LASER_X[1], TOP + 1.5, z + 0.25), m[mat_], intervals, 0.06)


def pds_lit(parent, m, intervals, mat_="light_soft", tag="pdl"):
    for i, z in enumerate(D.PD_Z):
        glow(parent, f"{tag}_{i}", (-20.5, TOP + 1.0, z - 0.3), (-20.0, TOP + 1.6, z + 0.3), m[mat_], intervals, 0.06)


def beams(parent, m, intervals, tag="beam"):
    g = grp(tag, parent, intervals)
    for i, z in enumerate(D.LASER_Z):
        tube(f"{tag}_{i}", (D.LASER_X[0], BY, z), (D.FAU_X[1], BY, z), 0.12, m["light"], g, 8)


def cable(m, parent, name, x0, sag, r, mat_, intervals):
    """A cable hanging between x = -x0 and +x0 at the MPO's height, as one show group."""
    g = grp(name, parent, intervals)
    pts = [(-x0 + 2 * x0 * k / 12, BY - sag * (1 - ((-x0 + 2 * x0 * k / 12) / x0) ** 2), 0.0) for k in range(13)]
    for k in range(12):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, mat_, g, 12)
    return pts


# ---- 1. What happens: one module holds both ends of the conversion ----------------------------


def sec1():
    m, root = begin(1)
    host(m, root)
    closed = grp("closed", root, [(0, F(1, 0))])
    mod = D.module(m, closed, lid="full", name="module_closed")
    key(mod, F(0, 0), "location", P(-55.0, 0, 0))
    key(mod, F(0, 0.08), "location", P(-55.0, 0, 0), linear=True)
    key(mod, F(0, 0.65), "location", P(0, 0, 0))
    opened = grp("opened", root, [(F(1, 0), END)])
    mo = D.module(m, opened, lid="cut", pkg_lid=False, name="module_open")
    glow(mo, "dsp_on", *D.DSP_DIE, m["elec_soft"], [(F(1, 0.2), END)], 0.06)
    glow(mo, "drv_on", *D.DRIVER, m["elec_soft"], [(F(2, 0), END)])
    glow(mo, "tia_on", *D.TIA, m["elec_soft"], [(F(2, 0.3), END)])
    lasers_lit(mo, m, [(F(2, 0.05), END)])
    pds_lit(mo, m, [(F(2, 0.35), END)])
    beams(mo, m, B2)
    tx_light(root, m, 2)
    rx_light(root, m, 2)
    driver_to_lasers(root, m, 2)
    pds_to_tia(root, m, 2)
    label("pluggable transceiver", (-6.0, 11.0, 0.0), mod, B0)
    label("cage on the front panel", (8.0, 12.5, -12.0), root, B0)
    label("edge connector: 8 host lanes", (36.0, -1.0, 4.0), root, B0)
    label("DSP", (3.5, TOP + 2.6, 3.3), mo, B1)
    label("drivers and lasers", (-19.75, TOP + 1.5, -2.1), mo, B1)
    label("photodiodes and TIAs", (-20.25, TOP + 1.6, 8.5), mo, B1)
    label("MPO fibre connector", (-38.0, -1.3, 3.0), mo, B1)
    label("sends: lanes to light", (-19.75, TOP + 1.5, -2.1), mo, B2)
    label("receives: light to lanes", (-20.25, TOP + 1.6, 8.5), mo, B2)
    label("lenses", (D.LENS_X, BY + 0.4, -8.1), mo, B2)
    glide_camera(root, [
        frame((-95, -7, -12), (41, 13, 12), -0.95, 0.70, pad=0.98),
        frame((-40, -5, -10), (14, 0, 10), 0.10, 0.90, pad=1.05),
        frame((-54, -5, -9), (-6, -1, 9), 0.0, 0.95, pad=1.05),
    ])
    done(1, root)


# ---- 2. The parts: form factors, optical ports, cables -----------------------------------------


def bench(m, root):
    box("bench", (-120.0, -8.0, -40.0), (70.0, -6.0, 40.0), m["dark_steel"], root)


def mpo_plug(m, parent, name, colour):
    box(f"{name}_body", (-46.0, -4.8, -5.0), (-38.0, -1.1, 5.0), m["plastic"], parent)
    tube(f"{name}_boot", (-46.0, BY, 0.0), (-54.0, BY, 0.0), 1.6, colour, parent, 16)
    tube(f"{name}_cable", (-54.0, BY, 0.0), (-80.0, BY, 0.0), 1.2, colour, parent, 12)


def lc_plugs(m, parent, name):
    for j, zc in enumerate(D.LC_Z):
        for hole in (zc - 1.6, zc + 1.6):
            box(f"{name}_{j}_{hole}", (-47.0, BY - 1.2, hole - 1.0), (-38.0, BY + 1.2, hole + 1.0), m["tab"], parent)
            tube(f"{name}_cord_{j}_{hole}", (-47.0, BY, hole), (-80.0, BY, hole * 1.6), 0.7, m["jacket"], parent, 10)
        box(f"{name}_clip_{j}", (-45.0, BY + 1.2, zc - 2.6), (-41.0, BY + 1.7, zc + 2.6), m["tab"], parent)


def sec2():
    m, root = begin(2)
    bench(m, root)
    # beat 0: form factors
    a = placed(root, "osfp", B0)
    D.module(m, a, lid="full", name="osfp_mod")
    a.location = P(0, 0, -15.0)
    b = placed(root, "qsfpdd", B0)
    D.qsfpdd(m, b)
    b.location = P(0, 0, 15.0)
    # beat 1: optical ports
    c = placed(root, "dr8", B1)
    D.module(m, c, lid="full", name="dr8_mod")
    mpo_plug(m, c, "mpo", m["jacket"])
    c.location = P(0, 0, -15.0)
    d = placed(root, "fr4", B1)
    D.module(m, d, lid="full", name="fr4_mod", optics="fr4")
    lc_plugs(m, d, "lc")
    d.location = P(0, 0, 15.0)
    # beat 2: cable assemblies
    e = placed(root, "dac", B2)
    D.module(m, e, lid="full", name="dac_mod")
    tube("twinax", (-36.0, BY, 0.0), (-105.0, BY, 0.0), 3.0, m["twinax"], e, 16)
    tube("dac_boot", (-36.0, BY, 0.0), (-44.0, BY, 0.0), 3.6, m["plastic"], e, 16)
    e.location = P(0, 0, -15.0)
    f = placed(root, "aoc", B2)
    D.module(m, f, lid="full", name="aoc_mod")
    tube("aoc_cable", (-36.0, BY, 0.0), (-105.0, BY, 0.0), 1.6, m["aqua"], f, 16)
    tube("aoc_boot", (-36.0, BY, 0.0), (-44.0, BY, 0.0), 2.4, m["plastic"], f, 16)
    f.location = P(0, 0, 15.0)
    for k, z in enumerate((-17.0, -15.0, -13.0)):
        stream_of(root, f"dac_sig_{k}", 3, (-100.0, BY + 3.1, z), [(0, 0, 0), (60.0, 0, 0)], 0.6, m["elec"], 2, 0.05 + 0.1 * k, 0.6, 60)
        stream_of(root, f"aoc_light_{k}", 3, (-100.0, BY + 1.7, 15.0 + (k - 1) * 0.6), [(0, 0, 0), (60.0, 0, 0)], 0.5, m["light"], 2, 0.1 + 0.1 * k, 0.6, 60)
    label("OSFP: finned, room for ~25 W", (-6.0, 11.0, -15.0), root, B0)
    label("QSFP-DD: smaller, cooler", (-12.0, 2.5, 15.0), root, B0)
    label("both: 8 electrical lanes", (33.0, TOP, -9.0), root, B0)
    label("DR8: one MPO, 16 fibres", (-42.0, -1.1, -15.0), root, B1)
    label("2xFR4: two duplex LC ports", (-42.0, BY + 1.7, 19.5), root, B1)
    label("DAC: copper, no optics", (-80.0, BY + 3.0, -15.0), root, B2)
    label("AOC: optics fixed to the fibre", (-80.0, BY + 1.6, 15.0), root, B2)
    glide_camera(root, [
        frame((-55, -7, -27), (46, 12, 27), -0.60, 0.65, pad=1.0),
        frame((-80, -7, -27), (-20, 6, 27), -0.85, 0.55, pad=1.0),
        frame((-105, -7, -27), (30, 12, 27), -0.55, 0.65, pad=1.0),
    ])
    done(2, root)


# ---- 3. One module's job, in order ------------------------------------------------------------


def sec3():
    m, root = begin(3)
    host(m, root)
    mo = D.module(m, root, lid="none", pkg_lid=False)
    lanes_in(root, m, 0)
    glow(mo, "dsp_on", *D.DSP_DIE, m["elec_soft"], [(F(0, 0.45), END)], 0.06)
    dsp_to_driver(root, m, 1)
    glow(mo, "drv_on", *D.DRIVER, m["elec_soft"], [(F(1, 0.15), F(2, 0))])
    driver_to_lasers(root, m, 1)
    lasers_lit(mo, m, [(F(1, 0.3), F(2, 0))])
    beams(mo, m, B1)
    tx_light(root, m, 1, u0=0.35)
    rx_light(root, m, 2)
    pds_lit(mo, m, [(F(2, 0.25), END)])
    pds_to_tia(root, m, 2)
    glow(mo, "tia_on", *D.TIA, m["elec_soft"], [(F(2, 0.35), END)])
    tia_to_dsp(root, m, 2)
    lanes_out(root, m, 2)
    glow(mo, "mcu_on", *D.MCU, m["elec_soft"], [(F(2, 0.5), END)])
    label("1. 8 lanes arrive at the edge", (30.0, TOP, 3.5), mo, B0)
    label("2. the DSP retimes them", (3.5, TOP + 2.6, 3.3), mo, B0)
    label("3. drivers and lasers", (-19.75, TOP + 1.5, -2.1), mo, B1)
    label("EML: laser + modulator pads, monitor PD", (-19.75, TOP + 1.6, -6.5), mo, B1)
    label("isolator: blocks reflections", (-24.4, BY + 0.6, -6.0), mo, B1)
    label("4. lenses couple into the MPO", (D.LENS_X, BY + 0.4, -8.1), mo, B1)
    label("5. photodiodes and TIAs", (-20.25, TOP + 1.6, 8.5), mo, B2)
    label("6. controller reports to host", (17.0, TOP + 0.9, 8.0), mo, B2)
    glide_camera(root, [
        frame((-5, -5, -8), (40, -1, 8), 0.30, 0.85, pad=1.05),
        frame((-50, -5, -9), (0, -1, 0), -0.20, 0.90, pad=1.02),
        frame((-50, -5, -9), (38, -1, 9), 0.10, 0.90, pad=1.0),
    ])
    done(3, root)


# ---- 4. Reach decides the type ----------------------------------------------------------------

SIDE_X = 80.0      # module centres at x = -SIDE_X (switch A, facing +x) and +SIDE_X (switch B)
ASIC_X = 135.0     # the ASIC behind each cage, in the side's own frame
CABLE_X = 52.0     # an optical cable leaves each MPO plug's boot here, in the side's own frame


def side(m, root, name, x, flip, plug_on):
    """One switch: board, faceplate, cage, connector, traces, ASIC and its module, with an MPO
    plug in during `plug_on`. Built facing -x at the origin, then placed at x (turned to face +x if flip)."""
    g = empty(name, root)
    D.host_board(m, g, x1=165.0, hz=28.0)
    box(f"{name}_bezel", (-37.6, D.BOARD_Y - 3.0, -28.0), (-36.6, 16.0, -12.0), m["dark_steel"], g)
    box(f"{name}_bezel_n", (-37.6, D.BOARD_Y - 3.0, 12.0), (-36.6, 16.0, 28.0), m["dark_steel"], g)
    D.cage(m, g, top=False)
    D.connector(m, g)
    D.host_traces(m, g, x1=ASIC_X - 22.0)
    D.asic(m, g, ASIC_X, half=22.0, name=f"{name}_asic")
    D.module(m, g, lid="full", name=f"{name}_module")
    plug = grp(f"{name}_plug", g, plug_on)
    box(f"{name}_plug_body", (-46.0, -4.8, -5.0), (-38.0, -1.1, 5.0), m["plastic"], plug)
    tube(f"{name}_plug_boot", (-46.0, BY, 0.0), (-CABLE_X, BY, 0.0), 1.6, m["plastic"], plug, 16)
    dac = grp(f"{name}_dac_boot", g, [(0, F(1, 0))])
    tube(f"{name}_dac_boot_t", (-36.0, BY, 0.0), (-44.0, BY, 0.0), 3.6, m["plastic"], dac, 16)
    g.location = P(x, 0, 0)
    if flip:
        g.rotation_euler = (0.0, 0.0, math.pi)
    return g


def sec4():
    m, root = begin(4)
    a = side(m, root, "switch_a", -SIDE_X, True, [(F(1, 0), END)])
    side(m, root, "switch_b", SIDE_X, False, [(F(1, 0), END)])
    dac = cable(m, root, "dac", SIDE_X - 44.0, 8.0, 2.6, m["twinax"], B0)
    mmf = cable(m, root, "mmf", SIDE_X - CABLE_X, 22.0, 1.3, m["aqua"], B1)
    smf = cable(m, root, "smf", SIDE_X - CABLE_X, 22.0, 1.3, m["jacket"], B2)
    for k, z in enumerate((-3.2, 0.0, 3.2)):
        ax = -SIDE_X - ASIC_X + 22.0
        stream_of(root, f"board_{k}", 4, (ax, -6.6, z), [(0, 0, 0), (-SIDE_X - 40.5 - ax, 0, 0)], 0.9, m["elec"], 0, 0.02 + 0.05 * k, 0.45, 60)
    for k in range(3):
        stream_of(root, f"dac_sig_{k}", 6, dac[0], rel(dac), 2.8, m["elec"], 0, 0.25 + 0.08 * k, 0.75, 50)
        stream_of(root, f"mmf_light_{k}", 8, mmf[0], rel(mmf), 1.1, m["light"], 1, 0.05 + 0.1 * k, 0.6, 70)
        stream_of(root, f"smf_light_{k}", 8, smf[0], rel(smf), 1.1, m["light"], 2, 0.05 + 0.1 * k, 0.6, 70)
    # fibre end faces in cross-section: multimode's wide 50 um core vs single-mode's 9 um core
    for name, core, ivl, mat_ in (("mm_face", 0.9, B1, m["aqua"]), ("sm_face", 0.25, B2, m["jacket"])):
        g = grp(name, root, ivl)
        tube(f"{name}_clad", (0.0, BY + 5.0, -6.0), (0.0, BY + 5.0, -5.6), 2.4, m["lens"], g, 24)
        tube(f"{name}_core", (0.0, BY + 5.0, -5.65), (0.0, BY + 5.0, -5.45), core, m["light"], g, 16)
    label("50 um core: modes smear by ~100 m", (0.0, BY + 7.6, -6.0), root, B1)
    label("9 um core: one mode, km reach", (0.0, BY + 7.6, -6.0), root, B2)
    label("on a board: copper traces", (75.0, -6.8, 4.0), a, B0)
    label("DAC copper: a few metres", (0.0, BY - 8.0, 0.0), root, B0)
    label("AOC or SR8 multimode: ~100 m", (0.0, BY - 22.0, 0.0), root, B1)
    label("MPO plug", (-44.0, -1.1, 0.0), a, B1)
    label("DR8 500 m, 2xFR4 2 km", (0.0, BY - 22.0, 0.0), root, B2)
    label("single-mode fibre", (20.0, BY - 14.0, 0.0), root, B2)
    glide_camera(root, [
        frame((-200, -14, -28), (45, 14, 28), 0.55, 0.55, pad=0.92),
        frame((-62, -30, -14), (62, 13, 14), 0.0, 0.25, pad=1.05),
        frame((-62, -30, -14), (62, 13, 14), 0.35, 0.35, pad=1.0),
    ])
    done(4, root)


# ---- 5. Lanes and speeds ----------------------------------------------------------------------

CW_ORDER = [0, 1, 2, 3, 0, 1, 2, 3]  # each set of 4 lasers: four CWDM wavelengths (false colour)


def sec5():
    m, root = begin(5)
    host(m, root)
    dr = grp("dr8", root, [(0, F(2, 0))])
    mo = D.module(m, dr, lid="none", pkg_lid=False, name="module_dr8")
    lanes_in(root, m, 0)
    glow(mo, "dsp_on", *D.DSP_DIE, m["elec_soft"], [(F(0, 0.45), F(1, 0))], 0.06)
    lasers_lit(mo, m, B1)
    pds_lit(mo, m, B1)
    beams(mo, m, B1)
    tx_light(root, m, 1)
    rx_light(root, m, 1)
    ends = grp("mpo_ends_lit", mo, B1)
    for k, z in enumerate(D.MPO_Z):
        box(f"mpo_lit_{k}", (D.MPO_REC[0][0] - 0.15, BY - 0.2, z - 0.2), (D.MPO_REC[0][0], BY + 0.2, z + 0.2), m["light"], ends)

    fr = grp("fr4", root, [(F(2, 0), END)])
    mf = D.module(m, fr, lid="none", pkg_lid=False, name="module_fr4", optics="fr4")
    cw = grp("cw_lit", mf, B2)
    for i, z in enumerate(D.LASER_Z):
        c = m[f"cw{CW_ORDER[i]}"]
        box(f"cw_laser_{i}", (D.LASER_X[0] - 0.06, TOP + 0.94, z - 0.31), (D.LASER_X[1] + 0.06, TOP + 1.56, z + 0.31), c, cw)
        tube(f"cw_beam_{i}", (D.LASER_X[0], BY, z), (D.FAU_X[1], BY, z), 0.12, c, cw, 8)
    for name, pts in D.fr4_paths().items():
        if name.startswith("tx"):
            pts = pts + [(pts[-1][0] - 15.0, BY, pts[-1][2])]
        else:
            pts = [(-52.0, BY, pts[-1][2])] + list(reversed(pts))
        stream_of(root, f"fr4_{name}", 4, pts[0], rel(pts), 0.5, m["light"], 2, 0.05, 0.6, 50)
    label("800G: 8 lanes x 100G PAM4", (30.0, TOP, 3.5), mo, B0)
    label("1.6T: 8 x 200G, 3 nm DSP", (3.5, TOP + 2.6, 3.3), mo, B0)
    label("DR8: one fibre per lane", (-30.0, BY, -1.5), mo, B1)
    label("16 fibres in one MPO", (-38.0, -1.3, 0.0), mo, B1)
    label("4 wavelengths into one fibre", (D.FAU_X[0], BY + 0.8, -6.85), mf, B2)
    label("2xFR4: 4 fibres in all", (-38.0, -1.3, 4.5), mf, B2)
    glide_camera(root, [
        frame((-5, -5, -8), (40, -1, 8), 0.30, 0.85, pad=1.05),
        frame((-54, -5, -9), (-17, -1, 9), -0.20, 0.95, pad=1.05),
        frame((-42, -5, -9), (-15, -1, 3), -0.10, 0.95, pad=1.05),
    ])
    done(5, root)


# ---- 6. Power and heat ------------------------------------------------------------------------

SEC_X = 3.5  # the cross-section cuts the module across here, through the DSP
ROW_Z = (-36.0, -12.0, 12.0, 36.0)


def sec6():
    m, root = begin(6)
    # beat 0: a cross-section through the DSP, turned so the cut face looks at the camera
    sec = grp("section", root, B0)
    rot = empty("section_rot", sec)
    D.host_board(m, rot)
    D.cage(m, rot, top=True, near=True)
    D.module(m, rot, lid="full", name="module_cut")
    for o in list(D.meshes(rot)):
        D.cut_x(o, SEC_X)
    rot.rotation_euler = (0.0, 0.0, -math.pi / 2)
    glow(rot, "dsp_hot", D.DSP_DIE[0], (SEC_X, D.DSP_PAD[1][1], D.DSP_DIE[1][2]), m["hot"], [(F(0, 0.1), F(1, 0))], 0.04)
    for k, z in enumerate((-2.4, -1.2, 0.0, 1.2, 2.4)):
        stream_of(rot, f"heat_up_{k}", 6, (SEC_X + 0.2, TOP + 2.4, z), [(0, 0, 0), (0, D.LID[1] - TOP - 2.4, 0), (0, D.FIN_TOP - TOP - 2.0, 1.5 * (k - 2))],
                  0.3, m["heat"], 0, 0.08 + 0.05 * k, 0.85, 60)
    label("DSP: the hottest chip", (SEC_X, TOP + 2.2, 3.5), rot, B0)
    label("heat up into the finned shell", (SEC_X, D.FIN_TOP, -8.0), rot, B0)

    # beat 1: a row of ports at the faceplate, every module shedding heat into the fans' air
    row = grp("row", root, B1)
    box("row_board", (-38.0, D.BOARD_Y - 3.0, -50.0), (60.0, D.BOARD_Y, 50.0), m["board"], row)
    for k, z in enumerate(ROW_Z):
        p = empty(f"port_{k}", row)
        D.cage(m, p, top=False, near=(k == 3))
        D.connector(m, p)
        D.module(m, p, lid="full", name=f"row_module_{k}")
        p.location = P(0, 0, z)
        for j, x in enumerate((-12.0, 4.0, 18.0)):
            stream_of(root, f"heat_{k}_{j}", 2, (x, 11.5, z), [(0, 0, 0), (6.0, 14.0, 0)], 0.9, m["heat"], 1, 0.05 + 0.06 * j + 0.03 * k, 0.8, 60)
        stream_of(root, f"air_{k}", 3, (-55.0, 8.5, z + 0.8), [(0, 0, 0), (110.0, 0, 0)], 0.7, m["air"], 1, 0.05 + 0.04 * k, 0.7, 80)
    label("1.6T modules: up to ~25-26 W", (-6.0, 11.0, 36.0), root, B1)
    label("64 ports: over a kilowatt", (-6.0, 11.0, -36.0), root, B1)
    label("fins and fans carry it away", (40.0, 9.0, 12.8), root, B1)

    # beat 2: a linear (LPO) board, no DSP
    lpo = grp("lpo", root, B2)
    host(m, lpo)
    mo = D.module(m, lpo, lid="none", pkg_lid=False, name="module_lpo", with_dsp=False)
    glow(mo, "drv_on", *D.DRIVER, m["elec_soft"], [(F(2, 0.3), END)])
    glow(mo, "tia_on", *D.TIA, m["elec_soft"], [(F(2, 0.3), END)])
    for k in range(4):
        stream_of(root, f"lpo_{k}", 3, (34.0, TOP + 0.3, -3.5 + k), [(0, 0, 0), (-22.6, 0, 0), (-22.6, 0, -3.0 + 0.1 * k), (-45.3, 0, -3.0 + 0.1 * k)],
                  0.3, m["elec"], 2, 0.05 + 0.05 * k, 0.6, 60)
    label("LPO: no DSP on the board", (3.5, TOP, 0.5), mo, B2)
    label("power: roughly half or less", (-10.75, TOP + 1.0, -5.0), mo, B2)
    glide_camera(root, [
        frame((-13, -9, 0), (13, 12, SEC_X), 0.0, 0.20, pad=1.08),
        frame((-55, -10, -50), (45, 25, 50), 0.60, 0.80, pad=0.97),
        frame((-20, -5, -9), (38, -1, 9), 0.20, 0.90, pad=1.02),
    ])
    done(6, root)


# ---- 7. Scale: modules per GPU ----------------------------------------------------------------

SERVERS = [(-165.0 + 110.0 * i, 0.0) for i in range(4)]   # (x, y) of each GPU server
LEAVES = [(-80.0, 160.0), (80.0, 160.0)]
SPINES = [(-80.0, 320.0), (80.0, 320.0)]
DEPTH = 90.0


def nose(m, g, name, x, y):
    """A module's nose sticking out of a front panel at (x, y, 0): shell, MPO, pull tab."""
    box(f"{name}_shell", (x - 5.5, y - 3.5, 0.0), (x + 5.5, y + 3.5, 6.0), m["shell"], g)
    box(f"{name}_mpo", (x - 2.5, y - 1.0, 6.0), (x + 2.5, y + 1.0, 6.4), m["plastic"], g)
    box(f"{name}_tab", (x - 2.0, y - 3.3, 6.0), (x + 2.0, y - 2.7, 11.0), m["tab"], g)
    return (x, y, 6.4)


def switch_box(m, g, name, cx, cy, ports, w=140.0, h=16.0):
    box(f"{name}_body", (cx - w / 2, cy, -DEPTH), (cx + w / 2, cy + h, 0.0), m["dark_steel"], g)
    box(f"{name}_panel", (cx - w / 2, cy + 1.0, -0.4), (cx + w / 2, cy + h - 1.0, 0.0), m["shell"], g)
    out = []
    for k in range(ports):
        x = cx - w / 2 + w * (k + 0.5) / ports
        out.append(nose(m, g, f"{name}_p{k}", x, cy + h / 2))
    return out


def server_box(m, g, name, cx, cy, w=100.0, h=22.0):
    """A GPU server with its lid off: two GPU packages with heat sinks on the board, two NIC ports."""
    box(f"{name}_floor", (cx - w / 2, cy, -DEPTH), (cx + w / 2, cy + 2.0, 0.0), m["dark_steel"], g)
    box(f"{name}_back", (cx - w / 2, cy, -DEPTH), (cx + w / 2, cy + h, -DEPTH + 2.0), m["dark_steel"], g)
    for s in (-1, 1):
        box(f"{name}_side_{s}", (cx + s * w / 2 - (2.0 if s > 0 else 0.0), cy, -DEPTH), (cx + s * w / 2 + (0.0 if s > 0 else 2.0), cy + h, 0.0), m["dark_steel"], g)
    box(f"{name}_front", (cx - w / 2, cy, -2.0), (cx + w / 2, cy + h, 0.0), m["shell"], g)
    box(f"{name}_board", (cx - w / 2 + 3, cy + 2.0, -DEPTH + 3), (cx + w / 2 - 3, cy + 3.0, -4.0), m["board"], g)
    for j, gx in enumerate((cx - 23.0, cx + 23.0)):
        box(f"{name}_gpu{j}_sub", (gx - 17, cy + 3.0, -60.0), (gx + 17, cy + 4.5, -20.0), m["substrate"], g)
        for k in range(8):
            z = -58.0 + 36.0 * k / 7
            box(f"{name}_gpu{j}_fin{k}", (gx - 15, cy + 4.5, z - 0.8), (gx + 15, cy + 18.0, z + 0.8), m["alu"], g)
    return [nose(m, g, f"{name}_nic{k}", cx + dx, cy + h / 2) for k, dx in enumerate((-22.0, 22.0))]


def link(m, g, name, a, b):
    pts = [a, (a[0], a[1], 28.0), (b[0], b[1], 28.0), b]
    for k in range(3):
        tube(f"{name}_{k}", pts[k], pts[k + 1], 0.9, m["jacket"], g, 8)
    return pts


def nose_glow(parent, m, name, p, intervals):
    x, y, _ = p
    glow(parent, name, (x - 5.5, y - 3.5, 0.0), (x + 5.5, y + 3.5, 6.0), m["light_soft"], intervals, 0.25)


def sec7():
    m, root = begin(7)
    g = empty("fabric", root)
    srv = [server_box(m, g, f"server{i}", x, y) for i, (x, y) in enumerate(SERVERS)]
    leaf = [switch_box(m, g, f"leaf{i}", x, y, 8) for i, (x, y) in enumerate(LEAVES)]
    spine = [switch_box(m, g, f"spine{i}", x, y, 4) for i, (x, y) in enumerate(SPINES)]
    down, up = [], []
    for i in range(4):
        for k in range(2):
            down.append((srv[i][k], leaf[i // 2][(i % 2) * 2 + k]))
    for li in range(2):
        for k in range(4):
            up.append((leaf[li][4 + k], spine[k // 2][li * 2 + k % 2]))
    for n, (a, b) in enumerate(down):
        pts = link(m, g, f"down{n}", a, b)
        stream_of(root, f"down_light_{n}", 2, pts[0], rel(pts), 3.2, m["light"], 0, 0.05 + 0.04 * n, 0.7, 60)
        stream_of(root, f"down_light2_{n}", 1, pts[0], rel(pts), 3.2, m["light"], 2, 0.05 + 0.04 * n, 0.4, 60)
        for e, p in enumerate((a, b)):
            nose_glow(g, m, f"down_glow_{n}_{e}", p, [(F(0, 0.2), F(1, 0)), (F(2, 0.1), END)])
    for n, (a, b) in enumerate(up):
        pts = link(m, g, f"up{n}", a, b)
        stream_of(root, f"up_light_{n}", 2, pts[0], rel(pts), 3.2, m["light"], 1, 0.05 + 0.04 * n, 0.7, 60)
        stream_of(root, f"up_light2_{n}", 1, pts[0], rel(pts), 3.2, m["light"], 2, 0.45 + 0.04 * n, 0.85, 60)
        for e, p in enumerate((a, b)):
            nose_glow(g, m, f"up_glow_{n}_{e}", p, [(F(1, 0.2), F(2, 0)), (F(2, 0.1), END)])
    label("GPU servers", (SERVERS[0][0], 18.0, -40.0), root, B0)
    label("leaf switch", (LEAVES[0][0] - 50.0, LEAVES[0][1] + 16.0, -30.0), root, B0)
    label("GPU to switch: a module each end", srv[1][1], root, B0)
    label("spine switch", (SPINES[1][0] + 50.0, SPINES[1][1] + 16.0, -30.0), root, B1)
    label("switch to switch: a module each end", up[5][1], root, B1)
    label("here: 32 modules for 8 GPUs", (0.0, 250.0, 28.0), root, B2)
    label("every link: 2 modules", up[2][0], root, B2)
    glide_camera(root, [
        frame((-220, -5, -60), (220, 180, 30), 0.0, 0.25, pad=1.0),
        frame((-160, 150, -60), (160, 340, 30), 0.0, 0.20, pad=1.0),
        frame((-220, -5, -60), (220, 340, 30), 0.0, 0.15, pad=0.98),
    ])
    done(7, root)


# ---- 8. Who makes it --------------------------------------------------------------------------


def sec8():
    m, root = begin(8)
    host(m, root)
    mo = D.module(m, root, lid="none", pkg_lid=False)
    lid = D.lid_part(m, root)
    key(lid, F(0, 0), "location", P(0, 0, 0))
    key(lid, F(1, 0.05), "location", P(0, 0, 0))
    key(lid, F(1, 0.35), "location", P(0, 300.0, 0))
    key(lid, F(2, 0) - 1, "location", P(0, 300.0, 0))
    key(lid, F(2, 0), "location", P(0, 40.0, 0))
    key(lid, F(2, 0.15), "location", P(0, 40.0, 0))
    key(lid, F(2, 0.65), "location", P(0, 0, 0))
    lasers_lit(mo, m, [(F(1, 0.2), F(2, 0))])
    glow(mo, "dsp_on", *D.DSP_DIE, m["elec_soft"], [(F(1, 0.2), F(2, 0))], 0.06)
    label("Innolight: #1, over $3.3B (2024)", (-6.0, 11.0, 0.0), root, B0)
    label("Eoptolink: #3, $1.2B (2024)", (10.0, 3.0, 11.0), root, B0)
    label("Coherent (COHR): long a leader", (-36.0, 3.0, 8.0), root, B0)
    label("EML lasers: Lumentum, Broadcom", (-19.75, TOP + 1.5, -2.1), mo, B1)
    label("PAM4 DSP", (3.5, TOP + 2.6, 3.3), mo, B1)
    label("contract assembly: Fabrinet (FN)", (-6.0, 11.0, 0.0), lid, B2)
    glide_camera(root, [
        frame((-55, -7, -12), (41, 13, 12), -0.75, 0.60, pad=1.0),
        frame((-30, -5, -10), (12, 0, 10), 0.10, 0.90, pad=1.05),
        frame((-50, -7, -12), (35, 50, 12), -0.55, 0.40, pad=0.97),
    ])
    done(8, root)


# ---- 9. Chokepoints and risks -----------------------------------------------------------------

OE_W = 4.5
OES = [(-27.0, z, "x") for z in (-21.0, -7.0, 7.0, 21.0)] + [(x, s * 27.0, "z") for x in (-14.0, 4.0) for s in (-1, 1)]


def oe(m, g, i, x, z, axis):
    """One optical engine: a silicon-photonics chip, a driver/TIA die on top, a fibre block at the
    outer edge. `axis` is the direction it faces out of the package ("x" toward -x, "z" toward +-z)."""
    y0 = D.BOARD_Y + 2.0
    box(f"oe_{i}_pic", (x - OE_W, y0, z - OE_W), (x + OE_W, y0 + 0.8, z + OE_W), m["siph"], g)
    if axis == "x":
        box(f"oe_{i}_eic", (x - 0.5, y0 + 0.8, z - 3.0), (x + 3.8, y0 + 1.6, z + 3.0), m["die"], g)
        box(f"oe_{i}_fau", (x - OE_W, y0 + 0.8, z - 3.2), (x - OE_W + 2.0, y0 + 2.2, z + 3.2), m["lens"], g)
        tube(f"oe_{i}_ribbon", (x - OE_W, y0 + 1.5, z), (-62.0, y0 + 1.5, z), 0.9, m["jacket"], g, 10)
    else:
        s = 1 if z > 0 else -1
        box(f"oe_{i}_eic", (x - 3.0, y0 + 0.8, z - s * 0.5), (x + 3.0, y0 + 1.6, z - s * 3.8), m["die"], g)
        box(f"oe_{i}_fau", (x - 3.2, y0 + 0.8, z + s * OE_W), (x + 3.2, y0 + 2.2, z + s * (OE_W - 2.0)), m["lens"], g)
        tube(f"oe_{i}_ribbon_a", (x, y0 + 1.5, z + s * OE_W), (x, y0 + 1.5, s * 40.0), 0.9, m["jacket"], g, 10)
        tube(f"oe_{i}_ribbon_b", (x, y0 + 1.5, s * 40.0), (-62.0, y0 + 1.5, s * (36.0 if x < 0 else 44.0)), 0.9, m["jacket"], g, 10)


def sec9():
    m, root = begin(9)
    # beat 0: the scarce parts lit on the open board
    b0 = grp("scarce", root, B0)
    host(m, b0)
    mo = D.module(m, b0, lid="none", pkg_lid=False)
    lasers_lit(mo, m, [(F(0, 0.15), F(1, 0))], mat_="scarce", tag="eml")
    glow(mo, "dsp_scarce", *D.DSP_DIE, m["scarce"], [(F(0, 0.35), F(1, 0))], 0.08)
    label("EMLs: limit how many ship", (-19.75, TOP + 1.5, -2.1), mo, B0)
    label("DSPs: the other limit", (3.5, TOP + 2.6, 3.3), mo, B0)

    # beat 1: a tray of finished modules
    b1 = grp("tray", root, B1)
    box("tray_base", (-60.0, -8.0, -42.0), (46.0, -6.0, 42.0), m["plastic"], b1)
    for s in (-1, 1):
        box(f"tray_wall_x{s}", (-60.0, -8.0, s * 42.0 - (1.5 if s > 0 else 0.0)), (46.0, 0.0, s * 42.0 + (0.0 if s > 0 else 1.5)), m["plastic"], b1)
    box("tray_wall_far", (-60.0, -8.0, -42.0), (-58.5, 0.0, 42.0), m["plastic"], b1)
    box("tray_wall_near", (44.5, -8.0, -42.0), (46.0, 0.0, 42.0), m["plastic"], b1)
    for k, z in enumerate((-27.0, 0.0, 27.0)):
        p = empty(f"tray_slot_{k}", b1)
        box(f"tray_rib_{k}", (-58.5, -6.0, -13.0), (44.5, -3.0, -12.0), m["plastic"], p)
        D.module(m, p, lid="full", name=f"tray_module_{k}")
        p.location = P(0, 0, z)
    label("most volume: China, SE Asia", (-6.0, 11.0, 27.0), root, B1)
    label("exposed to trade policy", (-6.0, 11.0, -27.0), root, B1)

    # beat 2: co-packaged optics, where module power pushes the industry
    b2 = grp("cpo", root, B2)
    box("cpo_board", (-64.0, D.BOARD_Y - 3.0, -48.0), (40.0, D.BOARD_Y, 48.0), m["board"], b2)
    box("cpo_sub", (-34.0, D.BOARD_Y + 0.6, -34.0), (34.0, D.BOARD_Y + 2.0, 34.0), m["substrate"], b2)
    box("cpo_balls", (-33.0, D.BOARD_Y, -33.0), (33.0, D.BOARD_Y + 0.6, 33.0), m["gold"], b2)
    box("cpo_lid", (-16.0, D.BOARD_Y + 2.0, -16.0), (16.0, D.BOARD_Y + 4.0, 16.0), m["steel"], b2)
    box("cpo_sink", (-15.0, D.BOARD_Y + 4.0, -15.0), (15.0, D.BOARD_Y + 6.5, 15.0), m["alu"], b2)
    for k in range(9):
        z = -14.0 + 28.0 * k / 8
        box(f"cpo_fin_{k}", (-15.0, D.BOARD_Y + 6.5, z - 0.5), (15.0, D.BOARD_Y + 26.0, z + 0.5), m["alu"], b2)
    for i, (x, z, axis) in enumerate(OES):
        oe(m, b2, i, x, z, axis)
    for k, z in enumerate((-21.0, -7.0, 7.0, 21.0)):
        stream_of(root, f"cpo_light_{k}", 4, (-32.0, D.BOARD_Y + 3.5, z), [(0, 0, 0), (-30.0, 0, 0)], 2.2, m["light"], 2, 0.05 + 0.08 * k, 0.7, 50)
        stream_of(root, f"cpo_elec_{k}", 3, (-16.0, D.BOARD_Y + 2.4, z * 0.6), [(0, 0, 0), (-8.0, 0, z * 0.4)], 0.5, m["elec"], 2, 0.1 + 0.08 * k, 0.75, 30)
    for i, (x, z, axis) in enumerate(OES):
        glow(b2, f"oe_lit_{i}", (x - OE_W, D.BOARD_Y + 2.0, z - OE_W), (x + OE_W, D.BOARD_Y + 2.8, z + OE_W), m["light_soft"], [(F(2, 0.2 + 0.04 * i), END)], 0.1)
    label("CPO: optics on the package", (-27.0, D.BOARD_Y + 3.6, 21.0), root, B2)
    label("switch ASIC under its heat sink", (0.0, D.BOARD_Y + 26.0, 0.0), root, B2)
    label("ASIC SerDes: millimetres to the optics", (-12.0, D.BOARD_Y + 2.4, 0.0), root, B2)
    label("no module, no module DSP", (-55.0, D.BOARD_Y + 3.5, -21.0), root, B2)
    glide_camera(root, [
        frame((-30, -5, -10), (12, 0, 10), 0.10, 0.90, pad=1.05),
        frame((-62, -8, -43), (47, 12, 43), 0.45, 0.85, pad=0.97),
        frame((-62, -10, -45), (36, 20, 45), 0.50, 0.85, pad=0.97),
    ])
    done(9, root)


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}

if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--") + 1])
    if n not in SECTIONS:
        raise SystemExit(f"section must be 1..9, got {n}")
    SECTIONS[n]()
