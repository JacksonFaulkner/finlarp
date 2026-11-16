"""The PAM4 DSP node's nine numbered sections, one per `# ` heading of the page's write-up
(tui/src/screens/diagrams_pages/FIB_DSP.txt), three beats each, in the SAND template. Each section
is its own Blender scene and pictures what its heading's paragraph says.

Run from the repo root, with the section number (1-9) after `--`:

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_dsp_sections.py -- 4

Writes blender/fiber_dsp_section_<n>.blend and assets/fiber_dsp_section_<n>.glb. One beat is 8 s.
The detailed parts (the cut-away flip-chip package, the driver, the TO-can laser, the fibre) come
from fiber_dsp_detail.py; each beat's camera is framed on what the beat adds (detail.frame) and
glides in from the beat before (detail.glide).

Sections (match diagrams_nodes/fiber/dsp/sections.rs and the page's headings):
  1 what happens  a module cut open: blurred host lanes in, the DSP cleans them, clean symbols to the laser, the photodiode's signal back
  2 the parts     the die's floor plan: SerDes lanes and baud rate; PAM4 + FEC encoders; equaliser and the retimer's clock
  3 the trip      one symbol, steps 1-6 along the cut faces: host SerDes, smeared trace, DSP, FEC, driver, far end
  4 NRZ vs PAM4   a scope: NRZ's 2 levels; PAM4's 4 levels at the same baud rate; the gaps a third of NRZ's
  5 the eye       a closed eye of overlaid symbols; the FFE taps; the eye opens
  6 FEC           an RS(544,514) codeword on a screen: data + check symbols; errors land; the decoder fixes them
  7 power, LPO    a DSP module hot; the DSP lifted out and the host driving the optics (LPO); back on the transmit side only (LRO)
  8 who makes it  three DSP packages tagged Marvell, Broadcom, Credo; Credo's active electrical cable; a TSMC wafer
  9 chokepoints   a new DSP per lane-rate step; a faceplate of modules each with a DSP; LPO leaning on the host's SerDes
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from sand_overview import F, P, ball, box, disc, key, label, show, tube  # noqa: E402
from sand_zooms import start, finish, stream_of  # noqa: E402
from pbr_kit import empty  # noqa: E402
import fiber_dsp_detail as D  # noqa: E402
from fiber_dsp_detail import (  # noqa: E402
    BEOL_Y1, BOARD_Y0, BOARD_Y1, DIE, DIE_Y0, DIE_Y1, FIN_Y1, LID_Y1, frame, glide, lbox,
)

PAGE = "fiber_dsp"
BEATS = 3
SCALE = 4.0  # the whole scene's scale in the GLB (see build)
# PAM4 levels, Gray-coded as in IEEE 802.3 (bottom to top 00, 01, 11, 10), mm above the screen base
LEVELS = {"00": 0.0, "01": 3.5, "11": 7.0, "10": 10.5}
LV = list(LEVELS.values())
SEQ = ["10", "00", "11", "01", "00", "10", "01", "11"]


def span(a, b):
    """Beats a up to b (exclusive) as one interval."""
    return [(F(a, 0), F(b, 0))]


def tags(root, items):
    """Captions as (beat, text, point): each tag pinned at its point for its beat."""
    for i, text, at in items:
        label(text, at, root, span(i, i + 1))


def group(name, parent, intervals):
    g = empty(name, parent)
    show(g, intervals)
    return g


def overlay(name, lo, hi, m, parent, mt="path"):
    """A thin lit strip just proud of a cut face: a signal's copper path, glowing."""
    return box(name, lo, hi, m[mt], parent)


def bench(m, root, x0, x1, z0, z1):
    """A dark bench plate the boards and parts stand on."""
    box("bench", (x0, BOARD_Y0 - 1.0, z0), (x1, BOARD_Y0, z1), m["screen"], root)


# ---- shared layouts ---------------------------------------------------------------------------

OUT_Z = 7.5  # the transmit lane: its via and BGA ball sit on the x = 0 cut face
OUT_BUMP_Z = 4.2
IN_BALL_X = 12.5  # the receive-side host lane climbs at x = 12.5 on the z = 0 cut face
IN_BUMP_X = 5.4
IN_X1 = 40.0  # the host lane enters from an inner layer here
DRV_X0, DRV_X1 = 22.0, 28.0
LASER_HX = 36.0
FIBRE_X0, FIBRE_X1 = 42.5, 66.0


def tx_path(m, root, with_package=True, x1=None):
    """Board, package, the transmit trace, driver, TO-can laser and fibre along z = OUT_Z, and the
    host lane coming in at z ~ 0.3 to the ball on the z = 0 cut face. Returns the package's groups."""
    D.board(m, root, x0=-18.0, x1=x1 or FIBRE_X1 + 2, z0=-16.0, z1=16.0)
    G = D.package(m, root, quad=False) if with_package else None
    y = BOARD_Y1
    box("out_trace", (0.0, y, OUT_Z - 0.25), (DRV_X0 - 0.2, y + 0.18, OUT_Z + 0.25), m["copper"], root)
    box("drv_trace", (DRV_X1 + 0.2, y, OUT_Z - 0.25), (LASER_HX - 2.5, y + 0.18, OUT_Z + 0.25), m["copper"], root)
    D.driver(m, root, DRV_X0, DRV_X1, OUT_Z)
    D.laser(m, root, LASER_HX, OUT_Z)
    D.fibre(m, root, FIBRE_X0, FIBRE_X1, OUT_Z)
    box("pair_p", (IN_BALL_X, y, 0.05), (IN_X1, y + 0.18, 0.55), m["copper"], root)
    box("pair_n", (IN_BALL_X + 1.0, y, 1.05), (IN_X1, y + 0.18, 1.55), m["copper"], root)
    box("pair_n_pad", (IN_BALL_X + 0.4, y, 0.85), (IN_BALL_X + 1.2, y + 0.2, 1.75), m["copper"], root)
    for k, z in enumerate((0.3, 1.3)):
        tube(f"in_via{k}", (IN_X1, y - 0.5, z), (IN_X1, y + 0.22, z), 0.42, m["gold"], root, 12)
    return G


IN_ROUTE = [(0, 0, 0), (IN_BALL_X - IN_X1 + 1, 0, 0), (IN_BALL_X - IN_X1 + 1, 2.2, 0),
            (IN_BUMP_X - IN_X1 + 1, 2.2, 0), (IN_BUMP_X - IN_X1 + 1, 3.5, 0)]
IN_START = (IN_X1 - 1, BOARD_Y1 + 0.6, 0.6)


def out_lit(m, parent, trace=True):
    y = BOARD_Y1
    overlay("lit_bump", (0.02, -3.6, OUT_BUMP_Z - 0.3), (0.08, DIE_Y0, OUT_BUMP_Z + 0.3), m, parent)
    overlay("lit_osub", (0.02, -4.22, OUT_BUMP_Z), (0.08, -4.06, OUT_Z), m, parent)
    overlay("lit_ovia", (0.25, -5.9, OUT_Z - 0.3), (0.32, -3.9, OUT_Z + 0.3), m, parent)
    if trace:
        overlay("lit_otrace", (0.3, y + 0.18, OUT_Z - 0.25), (DRV_X0 - 0.2, y + 0.24, OUT_Z + 0.25), m, parent)
        overlay("lit_odrv", (DRV_X1 + 0.2, y + 0.18, OUT_Z - 0.25), (LASER_HX - 2.5, y + 0.24, OUT_Z + 0.25), m, parent)


def out_streams(m, root, b, u0=0.05):
    y = BOARD_Y1
    stream_of(root, f"down{b}", 3, (0.6, -3.2, OUT_BUMP_Z), [(0, 0, 0), (0, -0.9, 0), (0, -0.9, OUT_Z - OUT_BUMP_Z),
                                                             (0, -3.4, OUT_Z - OUT_BUMP_Z)],
              0.35, m["path"], b, u0, u0 + 0.5, 40)
    stream_of(root, f"along{b}", 5, (0.6, y + 0.6, OUT_Z), [(0, 0, 0), (DRV_X0 - 1.0, 0, 0)], 0.45, m["path"], b,
              u0 + 0.1, u0 + 0.7, 50)
    stream_of(root, f"on{b}", 4, (DRV_X1 + 0.5, y + 0.6, OUT_Z), [(0, 0, 0), (LASER_HX - 3.0 - DRV_X1, 0, 0)],
              0.45, m["path"], b, u0 + 0.3, u0 + 0.8, 30)


def laser_on(m, root, intervals):
    box("chip_glow", (LASER_HX + 2.35, D.AXIS_Y - 0.35, OUT_Z - 0.55), (LASER_HX + 3.65, D.AXIS_Y + 0.15, OUT_Z + 0.1),
        m["light3"], group("chip_on", root, intervals))


def fibre_pulses(m, root, b, n=8, zc=OUT_Z, x0=FIBRE_X0, x1=FIBRE_X1, name="pulse"):
    for k in range(n):
        mt = ("light1", "light2", "light3", "light2")[k % 4]
        e = empty(f"{name}{k}", root)
        tube(f"{name}{k}_t", (x0, D.AXIS_Y, zc + 0.2), (x0 + 2.6, D.AXIS_Y, zc + 0.2), 0.3, m[mt], e, 10)
        f0 = F(b, 0.02 + 0.1 * k)
        f1 = f0 + 70
        key(e, f0, "location", P(0, 0, 0), linear=True)
        key(e, f1, "location", P(x1 - x0 - 3.0, 0, 0), linear=True)
        show(e, [(f0, min(f1, F(b + 1, 0)))])


def die_glow(m, parent, mt="path"):
    """The die's metal stack lit on both cut faces (where its circuits are)."""
    dx0, dz0, dx1, dz1 = DIE
    lbox("die_lit", (dx0 - 0.08, DIE_Y0 - 0.02, dz0 - 0.08), (dx1 + 0.08, BEOL_Y1, dz1 + 0.08), m[mt], parent, None, 0.08)


# ---- 1 what happens ---------------------------------------------------------------------------

M_X0, M_X1 = -50.0, 74.0  # the module's board
RX_Z = -7.5


def module(m, root, arched=False):
    """A pluggable module with its shell cut away: board, DSP package, 8 host lanes from the gold edge
    connector, the driver, TO-can laser and fibre (transmit, z = OUT_Z), the photodiode can and its
    fibre (receive, z = RX_Z), and the fibre receptacle. Returns the package's groups."""
    y = BOARD_Y1
    D.board(m, root, x0=M_X0, x1=M_X1, z0=-18.0, z1=16.0)
    G = D.package(m, root, quad=False)
    # the module shell: floor under the board, back and end walls, a finned roof over the back half
    box("shell_floor", (M_X0 - 2, BOARD_Y0 - 0.9, -20), (M_X1 + 2, BOARD_Y0 - 0.05, 18), m["dark_steel"], root)
    box("shell_back", (M_X0 - 2, BOARD_Y0 - 0.9, -21), (M_X1 + 2, 9.0, -20), m["dark_steel"], root)
    box("shell_end", (M_X1 + 2, BOARD_Y0 - 0.9, -21), (M_X1 + 3, 9.0, 18), m["dark_steel"], root)
    box("shell_roof", (M_X0 - 2, 8.0, -21), (M_X1 + 3, 9.0, -14), m["dark_steel"], root)
    for k in range(16):
        x = M_X0 + 2 + 8 * k
        box(f"shell_fin{k}", (x, 9.0, -21), (x + 0.8, 12.0, -14), m["steel"], root)
    # edge connector: gold fingers at the host end, and 8 host lanes to the package
    for k in range(8):
        z = -9.1 + 2.6 * k
        box(f"finger{k}", (M_X0, y, z - 0.8), (M_X0 + 6, y + 0.12, z + 0.8), m["gold"], root)
        box(f"host_lane{k}", (M_X0 + 6, y, z - 0.25), (-15.5, y + 0.18, z + 0.25), m["copper"], root)
    # transmit: driver, laser, fibre at z = OUT_Z; receive: photodiode can and its fibre at RX_Z
    box("out_trace", (0.0, y, OUT_Z - 0.25), (DRV_X0 - 0.2, y + 0.18, OUT_Z + 0.25), m["copper"], root)
    box("drv_trace", (DRV_X1 + 0.2, y, OUT_Z - 0.25), (LASER_HX - 2.5, y + 0.18, OUT_Z + 0.25), m["copper"], root)
    D.driver(m, root, DRV_X0, DRV_X1, OUT_Z, arched=arched)
    D.laser(m, root, LASER_HX, OUT_Z)
    D.fibre(m, root, FIBRE_X0, FIBRE_X1, OUT_Z)
    D.laser(m, root, LASER_HX, RX_Z, name="pd")
    D.fibre(m, root, FIBRE_X0, FIBRE_X1, RX_Z, name="rx_fibre")
    box("rx_trace", (15.2, y, RX_Z - 0.25), (LASER_HX - 2.5, y + 0.18, RX_Z + 0.25), m["copper"], root)
    box("receptacle", (FIBRE_X1, BOARD_Y1, -12), (M_X1, 2.0, 12), m["mold"], root)
    return G


def sec_whole(m, root):
    """1 what happens: a pluggable module with its shell cut away. Blurred host lanes come in at the
    edge connector, the DSP cleans them, clean symbols go to the laser driver and laser; the
    photodiode's weak signal comes back into the DSP."""
    y = BOARD_Y1
    G = module(m, root)
    # beat 0: blurred host symbols come in along the lanes
    for k in range(4):
        z = -9.1 + 2.6 * (2 * k + 1)
        stream_of(root, f"host{k}", 4, (M_X0 + 4, y + 0.6, z), [(0, 0, 0), (M_X0 * -1 - 19, 0, 0)], 0.5, m["noise"], 0,
                  0.04 + 0.05 * k, 0.6 + 0.05 * k, 70)
    # beat 1: the die lights, blurred in, clean out
    die_glow(m, group("die_on", G["die"], span(1, 3)))
    stream_of(root, "in1", 6, (M_X0 + 4, y + 0.6, 6.5), [(0, 0, 0), (M_X0 * -1 - 19, 0, 0)], 0.5, m["noise"], 1,
              0.0, 0.5, 70)
    lit = group("out_on", root, span(1, 3))
    out_lit(m, lit, trace=False)
    out_streams(m, root, 1, 0.2)
    # beat 2: clean symbols to the laser and down the fibre; the photodiode's signal back in
    out_lit(m, group("trace_on", root, span(2, 3)), trace=True)
    out_streams(m, root, 2)
    laser_on(m, root, [(F(2, 0.4), F(3, 0))])
    fibre_pulses(m, root, 2)
    stream_of(root, "rx", 5, (LASER_HX - 3.0, y + 0.6, RX_Z), [(0, 0, 0), (15.5 - LASER_HX + 2.0, 0, 0)], 0.45,
              m["noise"], 2, 0.05, 0.7, 50)
    tags(root, [
        (0, "edge connector to the host", (M_X0 + 3, y, 9.1)),
        (0, "8 host lanes, blurred", (-30, y + 0.2, 1.3)),
        (0, "PAM4 DSP", (-6, FIN_Y1, 6)),
        (0, "module shell, cut away", (M_X0 + 10, 9.0, -17)),
        (1, "DSP samples + equalises", (4, -2.95, 0)),
        (1, "lanes arrive blurred", (-22, y + 0.6, 6.5)),
        (2, "clean symbols to the laser", (DRV_X0 + 2, -5.2, OUT_Z)),
        (2, "light out on the fibre", (54, D.AXIS_Y, OUT_Z)),
        (2, "photodiode: weak signal back", (LASER_HX + 3, D.AXIS_Y + 2.5, RX_Z)),
    ])
    return [
        frame((M_X0, -11, -21), (M_X1, 12, 16), 0.45, 0.55, fill=0.98),
        frame((-30, -10, -12), (15, FIN_Y1, 12), 0.45, 0.40, fill=0.92),
        frame((-4, -9, -10), (62, 0, 10), 0.40, 0.45, fill=0.95),
    ]


# ---- 2 the parts ------------------------------------------------------------------------------


def tiles(name, x0, z0, x1, z1, mt, parent, nx=3, nz=2, y=0.0):
    """A block of the floor plan: a raised base with nx x nz cells on it."""
    box(f"{name}_base", (x0, y, z0), (x1, y + 0.12, z1), mt, parent)
    gx, gz = (x1 - x0) / nx, (z1 - z0) / nz
    for i in range(nx):
        for j in range(nz):
            box(f"{name}_c{i}{j}", (x0 + gx * i + 0.12, y + 0.12, z0 + gz * j + 0.12),
                (x0 + gx * (i + 1) - 0.12, y + 0.25, z0 + gz * (j + 1) - 0.12), mt, parent)


def glow(name, x0, z0, x1, z1, mt, parent, y=0.26):
    box(name, (x0, y, z0), (x1, y + 0.06, z1), mt, parent)


def die_plan(m, root):
    """The DSP die face up in a carrier tray: 8 host and 8 line SerDes lanes down its edges, the
    transmit blocks behind (z < 0), the receive blocks in front, a clock (PLL) in the middle."""
    box("tray", (-11, -1.6, -10), (11, -0.6, 10), m["mold"], root)
    box("tray_pocket", (-8.6, -0.6, -7.6), (8.6, -0.5, 7.6), m["seal"], root)
    box("die_si", (-8, -0.5, -7), (8, 0.0, 7), m["silicon"], root)
    for k, (a, b) in enumerate((((-8, -7), (8, -6.8)), ((-8, 6.8), (8, 7)), ((-8, -7), (-7.8, 7)), ((7.8, -7), (8, 7)))):
        box(f"seal_ring{k}", (a[0], 0.0, a[1]), (b[0], 0.15, b[1]), m["copper"], root)
    for side, (x0, x1) in (("host", (-7.5, -5.7)), ("line", (5.7, 7.5))):
        for k in range(8):
            z = -6.2 + k * 1.6
            box(f"{side}_lane{k}", (x0, 0.0, z), (x1, 0.3, z + 1.2), m["analog"], root)
    tiles("fec_enc", -5.2, -6.4, -1.6, -0.6, m["logic"], root)
    tiles("pam4_enc", -1.2, -6.4, 2.0, -0.6, m["logic"], root, nx=2)
    tiles("tx_dac", 2.4, -6.4, 5.2, -0.6, m["analog"], root, nx=2, nz=3)
    tiles("fec_dec", -5.2, 0.6, -1.8, 6.4, m["logic"], root)
    tiles("eq", -1.4, 0.6, 2.6, 6.4, m["sram"], root, nx=4, nz=3)
    tiles("adc", 3.0, 0.6, 5.2, 6.4, m["analog"], root, nx=2, nz=3)
    box("pll", (-0.8, 0.0, -0.4), (0.8, 0.3, 0.4), m["gold"], root)


def sec_parts(m, root):
    """2 the parts: the die's floor plan. Beat 0 lights the SerDes lanes (baud rate); beat 1 the
    transmit blocks (PAM4 and FEC encoders); beat 2 the receive blocks (equaliser, FEC decoder)
    and the clock that makes the DSP a retimer."""
    die_plan(m, root)
    ser = group("serdes_lit", root, span(0, 1))
    glow("ser_host", -7.5, -6.2, -5.7, 6.6, m["lit_tx"], ser, y=0.31)
    glow("ser_line", 5.7, -6.2, 7.5, 6.6, m["lit_rx"], ser, y=0.31)
    tx = group("tx_lit", root, span(1, 2))
    glow("tx_fec", -5.2, -6.4, -1.6, -0.6, m["lit_tx"], tx)
    glow("tx_pam", -1.2, -6.4, 2.0, -0.6, m["lit_tx"], tx)
    glow("tx_dac", 2.4, -6.4, 5.2, -0.6, m["lit_tx"], tx)
    rx = group("rx_lit", root, span(2, 3))
    glow("rx_adc", 3.0, 0.6, 5.2, 6.4, m["lit_rx"], rx)
    glow("rx_eq", -1.4, 0.6, 2.6, 6.4, m["lit_rx"], rx)
    glow("rx_fec", -5.2, 0.6, -1.8, 6.4, m["lit_rx"], rx)
    glow("rx_pll", -0.8, -0.4, 0.8, 0.4, m["hl"], rx, y=0.31)
    for k in range(4):
        z = -5.6 + 3.2 * k
        stream_of(root, f"lane_h{k}", 3, (-9.5, 0.7, z), [(0, 0, 0), (3.0, 0, 0)], 0.3, m["path"], 0,
                  0.05 + 0.05 * k, 0.6 + 0.05 * k, 40)
        stream_of(root, f"lane_l{k}", 3, (6.5, 0.7, z), [(0, 0, 0), (3.0, 0, 0)], 0.3, m["path"], 0,
                  0.1 + 0.05 * k, 0.65 + 0.05 * k, 40)
    for k in range(3):
        z = -5.0 + 1.6 * k
        stream_of(root, f"tx{k}", 4, (-7.0, 0.7, z), [(0, 0, 0), (14.0, 0, 0)], 0.35, m["path"], 1,
                  0.05 + 0.04 * k, 0.6 + 0.04 * k, 70)
        z = 2.0 + 1.6 * k
        stream_of(root, f"rx{k}", 4, (7.0, 0.7, z), [(0, 0, 0), (-14.0, 0, 0)], 0.35, m["noise"], 2,
                  0.05 + 0.04 * k, 0.6 + 0.04 * k, 70)
    tags(root, [
        (0, "SerDes: 8 host lanes", (-6.6, 0.3, 5.0)),
        (0, "SerDes: 8 line lanes", (6.6, 0.3, -5.0)),
        (0, "53.125 GBd per 100G lane", (-6.6, 0.3, -5.0)),
        (1, "PAM4 encoder: 2 bits a symbol", (0.4, 0.3, -3.5)),
        (1, "FEC encoder: check bits", (-3.4, 0.3, -3.5)),
        (1, "DAC: out to the laser driver", (3.8, 0.3, -3.5)),
        (2, "equaliser", (0.6, 0.3, 3.5)),
        (2, "FEC decoder", (-3.5, 0.3, 3.5)),
        (2, "clock recovery: a retimer", (0, 0.3, 0)),
    ])
    return [
        frame((-9, -1.6, -8), (9, 0.4, 8), 0.25, 0.95),
        frame((-8, -0.5, -7), (8, 0.4, 0), 0.15, 0.85, fill=0.92),
        frame((-8, -0.5, -1), (8, 0.4, 7), 0.30, 0.85, fill=0.92),
    ]


# ---- 3 one symbol's trip ----------------------------------------------------------------------


def sec_trip(m, root):
    """3 the trip, numbered as the write-up: (1) the host lane brings a symbol in, (2) smeared by the
    trace; (3) up the package into the die, which samples and equalises it, (4) and re-encodes the
    FEC; (5) out to the driver and the laser, (6) and down the fibre to the far end."""
    tx_path(m, root)
    y = BOARD_Y1
    in1 = group("in_lit1", root, span(0, 3))
    overlay("lit_trace", (IN_BALL_X, y + 0.18, 0.05), (IN_X1, y + 0.24, 0.55), m, in1, "noise")
    in2 = group("in_lit2", root, span(1, 3))
    overlay("lit_via", (IN_BALL_X - 0.3, -5.9, 0.28), (IN_BALL_X + 0.3, -3.9, 0.34), m, in2)
    overlay("lit_sub", (IN_BUMP_X, -4.22, 0.02), (IN_BALL_X, -4.06, 0.08), m, in2)
    lbox("die_lit", (DIE[0] - 0.08, DIE_Y0 - 0.02, DIE[1] - 0.08), (DIE[2] + 0.08, BEOL_Y1, DIE[3] + 0.08),
         m["path"], in2, None, 0.08)
    stream_of(root, "smear", 6, IN_START, IN_ROUTE[:2], 0.5, m["noise"], 0, 0.05, 0.7, 60)
    stream_of(root, "up", 5, IN_START, IN_ROUTE, 0.45, m["path"], 1, 0.0, 0.5, 72)
    out_lit(m, group("out_on", root, span(2, 3)))
    out_streams(m, root, 2)
    laser_on(m, root, [(F(2, 0.35), F(3, 0))])
    fibre_pulses(m, root, 2)
    tags(root, [
        (0, "1 host SerDes sends a symbol", (IN_X1, y + 0.2, 1.0)),
        (0, "2 trace + connector smear it", (26, y + 0.6, 0.6)),
        (0, "DSP package, cut open", (8, LID_Y1, 0)),
        (1, "into the die by a bump", (IN_BUMP_X, -3.5, 0.3)),
        (1, "3 sampled + equalised", (3.0, -2.95, 0.1)),
        (1, "4 FEC checked, re-encoded", (6.5, -2.2, 0)),
        (2, "5 driver: symbol to laser current", (DRV_X0 + 1, -5.2, OUT_Z - 3)),
        (2, "6 far end: a DSP in reverse", (60, D.AXIS_Y, OUT_Z)),
    ])
    return [
        frame((4, -8, -1), (IN_X1 + 1, -3, 3), 0.40, 0.35, fill=0.95),
        frame((0, -7.5, 0), (15, -1.5, 1), 0.35, 0.18, fill=0.95),
        frame((-2, -8, 0), (FIBRE_X1, 0, 11), 0.35, 0.45, fill=0.97),
    ]


# ---- 4 NRZ vs PAM4 ----------------------------------------------------------------------------

SCOPE_X0, SCOPE_X1 = -7.0, 27.0
SYM_W = 3.0  # one symbol, mm across the screen
WAVE_X0 = 0.5
NRZ = "10110100"


def scope(m, root, x0, x1, y0=-3.0, y1=13.5, grid=True):
    """An oscilloscope: housing on feet, a bezel round a dark screen with a faint grid."""
    box("scope_body", (x0 - 2, y0 - 3.5, -6.0), (x1 + 2, y1 + 2, -1.4), m["dark_steel"], root)
    for k, x in enumerate((x0, x1 - 2)):
        box(f"scope_foot{k}", (x, y0 - 4.5, -5.5), (x + 2, y0 - 3.5, -2.0), m["seal"], root)
    box("scope_screen", (x0, y0, -1.5), (x1, y1, -1.2), m["screen"], root)
    for k, (a, b) in enumerate((((x0 - 0.8, y0 - 0.8), (x1 + 0.8, y0)), ((x0 - 0.8, y1), (x1 + 0.8, y1 + 0.8)),
                                ((x0 - 0.8, y0), (x0, y1)), ((x1, y0), (x1 + 0.8, y1)))):
        box(f"scope_bezel{k}", (a[0], a[1], -1.5), (b[0], b[1], -0.6), m["mold"], root)
    for k in range(4):
        box(f"scope_knob{k}", (x1 - 1.0 - 2.4 * k, y0 - 2.6, -1.4), (x1 - 0.2 - 2.4 * k, y0 - 1.6, -0.9), m["steel"], root)
    if not grid:
        return
    x = x0 + 2.0
    while x < x1:
        box(f"grid_v{x:.0f}", (x - 0.04, y0, -1.2), (x + 0.04, y1, -1.15), m["grid"], root)
        x += SYM_W
    for name, y in LEVELS.items():
        box(f"grid_h{name}", (x0, y - 0.04, -1.2), (x1, y + 0.04, -1.15), m["grid"], root)


def waveform(m, parent, levels, seq, b, name, mt="path"):
    """A stepped trace drawing in symbol by symbol through beat b; returns the dot's (u, point) path."""
    path = []
    for k, y in enumerate(levels[s] for s in seq):
        xa, xb = WAVE_X0 + SYM_W * k, WAVE_X0 + SYM_W * (k + 1)
        u = 0.05 + 0.8 * k / len(seq)
        seg = group(f"{name}{k}", parent, [(F(b, u), F(b + 1, 0))])
        tube(f"{name}{k}_t", (xa, y, -0.6), (xb, y, -0.6), 0.28, m[mt], seg, 8)
        if k:
            yp = levels[seq[k - 1]]
            if yp != y:
                tube(f"{name}{k}_e", (xa, yp, -0.6), (xa, y, -0.6), 0.2, m[mt], seg, 8)
        path.append((u, (xa + SYM_W / 2, y, -0.2)))
    return path


def ride(m, root, path, b, name):
    g = group(f"{name}_g", root, span(b, b + 1))
    dot = ball(name, path[0][1], 0.8, m["hl"], g, 16)
    for u, p in path:
        key(dot, F(b, u), "location", P(*p), linear=True)
        key(dot, F(b, u + 0.06), "location", P(*p), linear=True)


def bracket(m, parent, x, y0, y1, name, mt="hl"):
    """A gap marker: an upright bar with short caps, at x from y0 to y1."""
    tube(f"{name}_v", (x, y0, -0.5), (x, y1, -0.5), 0.15, m[mt], parent, 8)
    for k, y in enumerate((y0, y1)):
        tube(f"{name}_c{k}", (x - 0.7, y, -0.5), (x + 0.7, y, -0.5), 0.15, m[mt], parent, 8)


def sec_nrz(m, root):
    """4 NRZ vs PAM4 on a scope: NRZ's two levels, one bit a symbol; PAM4's four levels at the same
    symbol width, two bits a symbol; then each PAM4 gap beside NRZ's, a third the height."""
    scope(m, root, SCOPE_X0, SCOPE_X1)
    lo, hi = LEVELS["00"], LEVELS["10"]
    nrz_rungs = group("nrz_rungs", root, span(0, 1))
    for k, y in enumerate((lo, hi)):
        tube(f"nrz_rung{k}", (SCOPE_X0 + 0.5, y, -0.9), (SCOPE_X1 - 0.5, y, -0.9), 0.22, m["rung"], nrz_rungs, 10)
    pam_rungs = group("pam_rungs", root, span(1, 3))
    for name, y in LEVELS.items():
        tube(f"rung_{name}", (SCOPE_X0 + 0.5, y, -0.9), (SCOPE_X1 - 0.5, y, -0.9), 0.22, m["rung"], pam_rungs, 10)
    nrz = waveform(m, empty("nrz_wave", root), {"0": lo, "1": hi}, NRZ, 0, "nrz", "noise")
    ride(m, root, nrz, 0, "nrz_dot")
    pam = waveform(m, empty("pam_wave", root), LEVELS, SEQ, 1, "pam")
    ride(m, root, pam, 1, "pam_dot")
    keep = group("pam_keep", root, span(2, 3))
    for k, s in enumerate(SEQ):
        xa = WAVE_X0 + SYM_W * k
        tube(f"keep{k}", (xa, LEVELS[s], -0.6), (xa + SYM_W, LEVELS[s], -0.6), 0.2, m["path"], keep, 8)
    gaps = group("gaps", root, span(2, 3))
    bracket(m, gaps, SCOPE_X1 - 4.5, lo, hi, "gap_nrz", "noise")
    for k, (a, b) in enumerate(zip(LV, LV[1:])):
        bracket(m, gaps, SCOPE_X1 - 1.4, a + 0.25, b - 0.25, f"gap_pam{k}")
    tags(root, [
        (0, "NRZ: 2 levels, 1 bit each", (WAVE_X0 + SYM_W * 0.5, hi, -0.6)),
        (0, "one symbol", (WAVE_X0 + SYM_W * 2.5, hi, -0.6)),
        (1, "PAM4: 4 levels, 2 bits each", (WAVE_X0 + SYM_W * 0.5, LEVELS["10"], -0.6)),
        (1, "same symbol width", (WAVE_X0 + SYM_W * 4.5, LEVELS["00"], -0.6)),
        (2, "NRZ gap", (SCOPE_X1 - 4.5, 5.25, -0.5)),
        (2, "PAM4 gap: a third", (SCOPE_X1 - 1.4, 8.75, -0.5)),
        (2, "~9.5 dB less margin", (SCOPE_X1 - 1.4, 1.75, -0.5)),
    ])
    return [
        frame((SCOPE_X0 - 1, -3.8, -1), (SCOPE_X1 + 1, 14.3, 0), 0.15, 0.10, fill=0.95),
        frame((SCOPE_X0 - 1, -3.8, -1), (SCOPE_X1 + 1, 14.3, 0), 0.10, 0.10, fill=0.98),
        frame((8, -3, -1), (SCOPE_X1 + 1, 14, 0), 0.25, 0.12, fill=0.95),
    ]


# ---- 5 equalization and the eye ---------------------------------------------------------------

U = 11.0  # one symbol (UI) across the eye screen
EYE_X0 = 0.0
TAP_X0 = 2 * U + 3.0


def curve(name, pts, r, mt, parent):
    """A smooth tube along a polyline (one mesh, made from a bevelled curve)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 0
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        v = P(*p)
        sp.points[i].co = (v.x, v.y, v.z, 1.0)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    cu.materials.append(mt)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target="MESH")
    ob.parent = parent
    return ob


def eye_trace(a, b, c, z):
    """One trace through the eye window (two symbols wide): level a, cross to b, cross to c."""
    import math

    def sig(t):
        return 1 / (1 + math.exp(-t))

    pts = []
    for i in range(25):
        x = 2 * U * i / 24
        y = a + (b - a) * sig(10 * (x - 0.5 * U) / U) + (c - b) * sig(10 * (x - 1.5 * U) / U)
        pts.append((EYE_X0 + x, y, z))
    return pts


def eye(m, parent, isi, noise, mt, name, copies=2, seed=1):
    rnd = random.Random(seed)
    k = 0
    for a in LV:
        for b in LV:
            for _ in range(copies):
                c = rnd.choice(LV)
                # ISI pulls each level toward its neighbours; noise shifts the whole trace a little
                bb = b + isi * ((a - b) + (c - b)) / 2 + rnd.uniform(-noise, noise)
                aa = a + rnd.uniform(-noise, noise)
                cc = c + rnd.uniform(-noise, noise)
                curve(f"{name}{k}", eye_trace(aa, bb, cc, -0.7), 0.09, mt, parent)
                k += 1


def sec_eye(m, root):
    """5 the eye: many symbols overlaid on a scope make eyes. Copper and lasers blur them shut;
    the DSP's FFE taps reshape the signal; the three eyes open again."""
    scope(m, root, -3.0, TAP_X0 + 11.0, grid=False)
    for k in range(5):
        x = EYE_X0 + k * U / 2
        box(f"eg_v{k}", (x - 0.04, -3.0, -1.2), (x + 0.04, 13.5, -1.15), m["grid"], root)
    closed = group("eye_closed", root, [(0, F(1, 0.45))])
    eye(m, closed, 0.33, 0.55, m["noise"], "closed")
    opened = group("eye_open", root, [(F(1, 0.45), F(3, 0))])
    eye(m, opened, 0.03, 0.12, m["path"], "open", seed=2)
    # the FFE taps as a bar chart in a panel at the right of the screen
    box("dsp_panel", (TAP_X0, -2.5, -1.15), (TAP_X0 + 10, 13.0, -1.05), m["logic"], root)
    for k, (a, b) in enumerate((((TAP_X0, -2.5), (TAP_X0 + 10, -2.1)), ((TAP_X0, 12.6), (TAP_X0 + 10, 13.0)),
                                ((TAP_X0, -2.5), (TAP_X0 + 0.4, 13.0)), ((TAP_X0 + 9.6, -2.5), (TAP_X0 + 10, 13.0)))):
        box(f"dsp_rim{k}", (a[0], a[1], -1.05), (b[0], b[1], -0.85), m["gold"], root)
    base = 3.5
    box("tap_axis", (TAP_X0 + 0.8, base - 0.05, -1.0), (TAP_X0 + 9.2, base + 0.05, -0.9), m["grid"], root)
    on = group("taps_on", root, span(1, 3))
    for k, t in enumerate((0.06, -0.15, 1.0, -0.3, 0.12, -0.05, 0.03)):
        x = TAP_X0 + 1.3 + k * 1.25
        pv = empty(f"tap{k}", on, P(x, base, -0.9))
        h = 7.0 * t
        box(f"tap{k}_bar", (-0.4, min(0, h), -0.1), (0.4, max(0, h) if abs(h) > 0.05 else 0.05, 0.1), m["hl_eq"], pv)
        key(pv, F(1, 0.0), "scale", (1, 1, 0.02))
        key(pv, F(1, 0.05 + 0.04 * k), "scale", (1, 1, 0.02))
        key(pv, F(1, 0.40 + 0.03 * k), "scale", (1, 1, 1))
    marks = group("eye_marks", root, span(2, 3))
    for k, (a, b) in enumerate(zip(LV, LV[1:])):
        mid, h = (a + b) / 2, (b - a) / 2 - 0.5
        pts = [(U - 3.0, mid), (U, mid + h), (U + 3.0, mid), (U, mid - h), (U - 3.0, mid)]
        for j in range(4):
            (x0, y0), (x1, y1) = pts[j], pts[j + 1]
            tube(f"mark{k}_{j}", (x0, y0, -0.4), (x1, y1, -0.4), 0.13, m["hl"], marks, 6)
    # a sampling dot sweeps the eye's centre each beat, so every beat moves
    for b in range(3):
        g = group(f"probe{b}", root, span(b, b + 1))
        d = ball(f"probe{b}_d", (U, LV[0], -0.3), 0.45, m["hl"], g, 12)
        for j, y in enumerate(LV):
            key(d, F(b, 0.1 + 0.22 * j), "location", P(U, y, -0.3), linear=True)
    tags(root, [
        (0, "many symbols overlaid", (U * 0.3, LV[3], -0.7)),
        (0, "eye closed: levels blur", (U, (LV[1] + LV[2]) / 2, -0.7)),
        (1, "equaliser taps", (TAP_X0 + 5, 12.6, -0.9)),
        (1, "the eye opens", (U, (LV[2] + LV[3]) / 2, -0.7)),
        (2, "3 open eyes", (U + 3.0, (LV[2] + LV[3]) / 2, -0.4)),
        (2, "decide here", (U, (LV[0] + LV[1]) / 2, -0.4)),
    ])
    return [
        frame((-3.8, -3.8, -1), (2 * U + 1, 14.3, 0), 0.15, 0.10, fill=0.95),
        frame((-3.8, -3.8, -1), (TAP_X0 + 11.8, 14.3, 0), 0.10, 0.10, fill=0.98),
        frame((-0.5, -1.5, -1), (2 * U + 0.5, 12.5, 0), 0.10, 0.08, fill=0.95),
    ]


# ---- 6 FEC ------------------------------------------------------------------------------------

CELLS = 32  # a codeword drawn as 32 cells: 30 data, 2 check (RS(544,514): 514 data, 30 check symbols)
CW, CH = 1.4, 2.6
ROW_Y = (7.5, 2.0)
BAD = (5, 13, 22)


def cell_xy(k):
    row, col = divmod(k, CELLS // 2)
    return -1.0 + col * (CW + 0.25), ROW_Y[row]


def sec_fec(m, root):
    """6 FEC: a codeword on a test screen. Beat 0 builds it, data then check symbols; beat 1 the
    link flips a few symbols (red); beat 2 the decoder finds and fixes them."""
    x1 = -1.0 + (CELLS // 2) * (CW + 0.25) + 0.5
    scope(m, root, -3.0, x1 + 1.5, grid=False)
    for k in range(CELLS):
        x, y = cell_xy(k)
        check = k >= CELLS - 2
        g = group(f"cell{k}", root, [(F(0, 0.05 + 0.7 * k / CELLS), F(3, 0))])
        box(f"cell{k}_b", (x, y, -1.1), (x + CW, y + CH, -0.7), m["gold" if check else "sram"], g)
    for k in BAD:
        x, y = cell_xy(k)
        g = group(f"bad{k}", root, [(F(1, 0.25 + 0.15 * BAD.index(k)), F(2, 0.15 + 0.25 * BAD.index(k)))])
        box(f"bad{k}_b", (x - 0.1, y - 0.1, -0.68), (x + CW + 0.1, y + CH + 0.1, -0.55), m["thresh"], g)
        f = group(f"fixed{k}", root, [(F(2, 0.15 + 0.25 * BAD.index(k)), F(3, 0))])
        box(f"fixed{k}_b", (x - 0.1, y - 0.1, -0.68), (x + CW + 0.1, y + CH + 0.1, -0.6), m["lit_rx"], f)
    # beat 1: a band of noise sweeps across the codeword (the link)
    sweep = group("sweep_g", root, span(1, 2))
    sw = empty("sweep", sweep)
    box("sweep_bar", (-1.6, -1.0, -0.5), (-1.0, 11.5, -0.4), m["noise"], sw)
    key(sw, F(1, 0.05), "location", P(0, 0, 0), linear=True)
    key(sw, F(1, 0.95), "location", P(x1 + 0.5, 0, 0), linear=True)
    # beat 2: the decoder's read head sweeps and fixes
    dec = group("dec_g", root, span(2, 3))
    dh = empty("dec", dec)
    box("dec_bar", (-1.6, -1.0, -0.5), (-1.0, 11.5, -0.4), m["path"], dh)
    key(dh, F(2, 0.02), "location", P(0, 0, 0), linear=True)
    key(dh, F(2, 0.95), "location", P(x1 + 0.5, 0, 0), linear=True)
    xd, yd = cell_xy(4)
    xc, yc = cell_xy(CELLS - 1)
    tags(root, [
        (0, "data: 514 symbols", (xd + CW / 2, yd + CH, -0.7)),
        (0, "check: 30 symbols, ~5%", (xc + CW / 2, yc + CH, -0.7)),
        (0, "RS(544,514), 'KP4'", (xd, ROW_Y[1], -0.7)),
        (1, "the link flips a few", (cell_xy(BAD[1])[0] + CW / 2, cell_xy(BAD[1])[1] + CH, -0.6)),
        (1, "~2 in 10,000 raw", (cell_xy(BAD[2])[0] + CW / 2, cell_xy(BAD[2])[1], -0.6)),
        (2, "decoder fixes them", (cell_xy(BAD[1])[0] + CW / 2, cell_xy(BAD[1])[1] + CH, -0.6)),
        (2, "near error-free out", (cell_xy(BAD[2])[0] + CW / 2, cell_xy(BAD[2])[1], -0.6)),
    ])
    return [
        frame((-3.8, -3.8, -1), (x1 + 2.3, 14.3, 0), 0.15, 0.12, fill=0.95),
        frame((-2, -1, -1), (x1 + 1, 11.5, 0), 0.12, 0.10, fill=0.95),
        frame((-2, -1, -1), (x1 + 1, 11.5, 0), 0.20, 0.10, fill=0.95),
    ]


# ---- 7 power, and taking the DSP out ----------------------------------------------------------

LIFT = 22.0


def sec_power(m, root):
    """7 power: the DSP module runs hot; LPO lifts the DSP out and lets the host lane drive the
    driver directly; LRO puts the DSP back on the transmit side only."""
    G = tx_path(m, root)
    y = BOARD_Y1
    pkg = G["base"].parent
    # the empty footprint the package leaves: its board pads
    for i in range(-5, 6):
        for j in range(-4, 5):
            x, z = i * 2.5, j * 2.5
            if x > 0 and z > 0:
                continue
            box(f"pad_{i}_{j}", (x - 0.45, y, z - 0.45), (x + 0.45, y + 0.05, z + 0.45), m["copper"], root)
    key(pkg, F(1, 0.05), "location", P(0, 0, 0))
    key(pkg, F(1, 0.40), "location", P(0, LIFT, 0))
    key(pkg, F(2, 0.02), "location", P(0, LIFT, 0))
    key(pkg, F(2, 0.30), "location", P(0, 0, 0))
    show(pkg, [(0, F(1, 0.45)), (F(2, 0.0), F(3, 0))])
    hot = group("hot", G["die"], span(0, 1))
    dx0, dz0, dx1, dz1 = DIE
    o = 0.05
    lbox("hot_die", (dx0 - o, DIE_Y0 - o, dz0 - o), (dx1 + o, DIE_Y1 + o, dz1 + o), m["heat"], hot, None, o)
    for k, (dx, dz) in enumerate(((-9.0, -6.6), (-3.0, -2.2), (4.0, -8.8), (-6.0, 4.4))):
        stream_of(root, f"puff{k}", 3, (dx, FIN_Y1 + 0.3, dz), [(0, 0, 0), (dx * 0.15, 7.0, 0)], 0.8, m["heat"], 0,
                  0.03 + 0.06 * k, 0.6 + 0.05 * k, 70)
    # LPO: the host lane runs straight on to the driver
    lpo = group("lpo", root, [(F(1, 0.40), F(2, 0.0))])
    box("bypass_a", (DRV_X0 + 2.5, y + 0.18, 0.05), (IN_X1, y + 0.26, 0.55), m["path"], lpo)
    box("bypass_b", (DRV_X0 + 2.5, y, 0.05), (DRV_X0 + 3.0, y + 0.26, OUT_Z - 3.0), m["path"], lpo)
    stream_of(root, "lpo_in", 5, IN_START, [(0, 0, 0), (DRV_X0 + 2.75 - IN_X1 + 1, 0, 0),
                                             (DRV_X0 + 2.75 - IN_X1 + 1, 0, OUT_Z - 3.6)],
              0.45, m["path"], 1, 0.45, 0.8, 40)
    # LRO: only the transmit path is lit through the DSP
    lro = group("lro", root, [(F(2, 0.3), F(3, 0))])
    out_lit(m, lro)
    out_streams(m, root, 2, 0.35)
    tags(root, [
        (0, "DSP module: hot", (4, -2.3, 0)),
        (0, "~18.75 pJ/bit (5 nm DSP)", (-6, FIN_Y1 + 3, 6)),
        (0, "1.6T, 3 nm: up to ~25 W", (-12, LID_Y1, 12)),
        (1, "LPO: no DSP, ~6.25 pJ/bit", (DRV_X0 + 2.75, y + 0.3, 1.0)),
        (1, "empty DSP footprint", (-5, y, 5)),
        (1, "host lane drives the optics", (30, y + 0.3, 0.3)),
        (2, "LRO: DSP on transmit only", (0, -5.0, OUT_Z)),
        (2, "trade: host SerDes must be good", (30, y + 0.3, 0.3)),
    ])
    return [
        frame((-15, -10, -13), (15, FIN_Y1 + 6, 13), 0.55, 0.40, fill=0.95),
        frame((-15, -10, -10), (IN_X1 + 1, -4, 10), 0.40, 0.55, fill=0.95),
        frame((-4, -9, -2), (LASER_HX + 6, -1, 11), 0.40, 0.45, fill=0.95),
    ]


# ---- 8 who makes it ---------------------------------------------------------------------------

MAKERS = ((-40.0, "Marvell (MRVL)"), (0.0, "Broadcom (AVGO)"), (40.0, "Credo (CRDO)"))
AEC_Z = 34.0
WAFER = (0.0, -48.0)


def at(obj, x, z):
    obj.location = P(x, 0, z)
    return obj


def sec_makers(m, root):
    """8 who makes it: three DSP packages side by side, one per maker; Credo's active electrical
    cable with a DSP in its plug; a wafer, since all three are fabbed at TSMC."""
    bench(m, root, -66, 66, -82, 48)
    D.board(m, root, x0=-62.0, x1=62.0, z0=-18.0, z1=18.0)
    for x, name in MAKERS:
        pe = empty(f"pkg_at_{x:.0f}", root)
        D.package(m, pe, quad=False)
        at(pe, x, 0.0)
    # Credo's active electrical cable: a plug shell cut open with a small DSP board inside
    y0 = BOARD_Y0
    box("aec_floor", (-12, y0, AEC_Z - 6), (12, y0 + 0.6, AEC_Z + 6), m["dark_steel"], root)
    box("aec_back", (-12, y0, AEC_Z - 6), (12, y0 + 7, AEC_Z - 5.4), m["dark_steel"], root)
    box("aec_side", (-12, y0, AEC_Z - 6), (-11.4, y0 + 7, AEC_Z + 6), m["dark_steel"], root)
    box("aec_pcb", (-11.4, y0 + 1.2, AEC_Z - 5), (10, y0 + 1.6, AEC_Z + 5), m["fr4"], root)
    for k in range(5):
        z = AEC_Z - 4 + 2 * k
        box(f"aec_finger{k}", (-11.4, y0 + 1.6, z - 0.6), (-8.5, y0 + 1.7, z + 0.6), m["gold"], root)
    box("aec_sub", (-4, y0 + 1.6, AEC_Z - 3), (2, y0 + 2.2, AEC_Z + 3), m["core"], root)
    box("aec_die", (-2.6, y0 + 2.2, AEC_Z - 1.8), (0.6, y0 + 2.9, AEC_Z + 1.8), m["silicon"], root)
    for k, z in enumerate((AEC_Z - 2.5, AEC_Z + 2.5)):
        tube(f"aec_cable{k}", (12, y0 + 2.2, z), (40, y0 + 2.2, z), 1.6, m["mold"], root, 16)
        tube(f"aec_core{k}", (8, y0 + 2.2, z), (41, y0 + 2.2, z), 0.6, m["copper"], root, 10)
    stream_of(root, "aec_data", 6, (39, y0 + 4.2, AEC_Z - 2.5), [(0, 0, 0), (-38, 0, 0)], 0.5, m["path"], 1,
              0.05, 0.7, 60)
    # a wafer on a chuck: all three are fabbed at TSMC
    wx, wz = WAFER
    disc("chuck", (wx, y0 + 1.0, wz), 27.0, 2.0, m["dark_steel"], root, 64)
    disc("wafer", (wx, y0 + 2.3, wz), 25.0, 0.6, m["silicon"], root, 96)
    for i in range(-6, 7):
        for j in range(-6, 7):
            x, z = wx + i * 3.6, wz + j * 3.6
            if (i * 3.6) ** 2 + (j * 3.6) ** 2 > (23.0 - 2.6) ** 2:
                continue
            box(f"wdie_{i}_{j}", (x - 1.6, y0 + 2.6, z - 1.6), (x + 1.6, y0 + 2.75, z + 1.6), m["beol"], root)
    for b in (0, 2):
        for k, (x, _) in enumerate(MAKERS):
            stream_of(root, f"mk{b}_{k}", 3, (x - 14, BOARD_Y1 + 0.6, 14.5), [(0, 0, 0), (28, 0, 0)], 0.5, m["path"],
                      b, 0.05 + 0.1 * k, 0.6 + 0.1 * k, 60)
    tags(root, [
        (0, "Marvell (MRVL)", (-46, FIN_Y1, 6)),
        (0, "Broadcom (AVGO): Sian3, 3 nm", (-6, FIN_Y1, 6)),
        (0, "Credo (CRDO)", (34, FIN_Y1, 6)),
        (1, "Credo AEC: a DSP in the plug", (-1, y0 + 2.9, AEC_Z)),
        (1, "copper cable", (28, y0 + 3.8, AEC_Z + 2.5)),
        (1, "plug's card edge", (-10, y0 + 1.7, AEC_Z + 4)),
        (2, "all fabbed at TSMC", (wx, y0 + 2.75, wz + 18)),
        (2, "one die per DSP", (wx + 3.6, y0 + 2.75, wz + 3.6)),
    ])
    return [
        frame((-56, -10, -14), (56, FIN_Y1 + 2, 14), 0.30, 0.50, fill=0.97),
        frame((-13, -10, AEC_Z - 7), (41, 0, AEC_Z + 7), 0.30, 0.55, fill=0.97),
        frame((wx - 27, -10, wz - 27), (wx + 27, -5, wz + 27), 0.25, 0.85, fill=0.97),
    ]


# ---- 9 chokepoints and risks ------------------------------------------------------------------

TRAY_X = -70.0
FACE_X0 = -16.0
LPO_X = 70.0


def mini_die(m, parent, name, x, z, ghost=False):
    """A small DSP die: lane tiles down both edges, a logic core."""
    si = m["cage"] if ghost else m["silicon"]
    box(f"{name}_si", (x - 5, -0.5, z - 5), (x + 5, 0.0, z + 5), si, parent)
    for side in (-1, 1):
        for k in range(4):
            zz = z - 3.9 + 2.2 * k
            box(f"{name}_lane{side}{k}", (x + side * 4.4 - 0.5, 0.0, zz - 0.8), (x + side * 4.4 + 0.5, 0.25, zz + 0.8),
                m["cage"] if ghost else m["analog"], parent)
    box(f"{name}_core", (x - 3.2, 0.0, z - 4), (x + 3.2, 0.2, z + 4), m["cage"] if ghost else m["logic"], parent)


def sec_risks(m, root):
    """9 chokepoints: (1) every lane-rate step needs a new DSP on a newer node; (2) a faceplate of
    modules, each with its own DSP, all adding power; (3) LPO: no DSP, so the link rests on the
    host chip's SerDes."""
    bench(m, root, TRAY_X - 30, LPO_X + 70, -30, 30)
    # 1: three dies on a tray, 100G, 200G, a ghost for 400G, arrows between
    y0 = BOARD_Y0
    box("tray", (TRAY_X - 22, y0, -9), (TRAY_X + 22, y0 + 1.0, 9), m["mold"], root)
    trayg = empty("dies", root)
    trayg.location = P(0, y0 + 1.5, 0)
    for k, ghost in enumerate((False, False, True)):
        mini_die(m, trayg, f"die{k}", TRAY_X - 14 + 14 * k, 0.0, ghost)
    for k in range(2):
        x = TRAY_X - 8 + 14 * k
        tube(f"arrow{k}", (x, y0 + 2.0, 0), (x + 2.2, y0 + 2.0, 0), 0.3, m["hl"], root, 8)
        tube(f"arrow{k}_h1", (x + 2.2, y0 + 2.0, 0), (x + 1.4, y0 + 2.0, 0.8), 0.3, m["hl"], root, 8)
        tube(f"arrow{k}_h2", (x + 2.2, y0 + 2.0, 0), (x + 1.4, y0 + 2.0, -0.8), 0.3, m["hl"], root, 8)
    pulse = group("next_pulse", root, span(0, 1))
    pp = empty("next_pp", pulse, P(TRAY_X + 14, y0 + 2.0, 0))
    for k, (a, b) in enumerate((((-5.6, -5.6), (5.6, -5.2)), ((-5.6, 5.2), (5.6, 5.6)),
                                ((-5.6, -5.6), (-5.2, 5.6)), ((5.2, -5.6), (5.6, 5.6)))):
        box(f"next_ring{k}", (a[0], -0.1, a[1]), (b[0], 0.1, b[1]), m["hl"], pp)
    for j, s in enumerate((1.0, 1.15, 1.0, 1.15, 1.0)):
        key(pp, F(0, 0.2 * j), "scale", (s, s, 1))
    # 2: a switch faceplate full of pluggables, each with a hot DSP
    box("face", (FACE_X0, y0, -2), (FACE_X0 + 52, y0 + 18, 0), m["dark_steel"], root)
    hot = group("mods_hot", root, span(1, 2))
    for r, yb in enumerate((y0 + 1.5, y0 + 9.5)):
        for c in range(8):
            x = FACE_X0 + 2.5 + 6.2 * c
            box(f"mod{r}{c}", (x, yb, 0), (x + 5, yb + 6, 16), m["steel"], root)
            for f in range(3):
                box(f"mod{r}{c}_fin{f}", (x + 0.6 + 1.5 * f, yb + 6, 2), (x + 1.2 + 1.5 * f, yb + 6.8, 14), m["steel"], root)
            box(f"mod{r}{c}_tab", (x + 1.5, yb + 1, 16), (x + 3.5, yb + 2, 19), m["oe"], root)
            box(f"mod{r}{c}_hot", (x - 0.05, yb + 1.5, 4), (x + 5.05, yb + 4.5, 9), m["heat"], hot)
    for c in range(0, 8, 2):
        x = FACE_X0 + 5 + 6.2 * c
        stream_of(root, f"mheat{c}", 3, (x, y0 + 16.5, 6), [(0, 0, 0), (0, 8, 0)], 0.8, m["heat"], 1,
                  0.05 + 0.05 * c, 0.6 + 0.05 * c, 60)
    # 3: a host switch chip on its board driving an LPO module directly
    bd = empty("lpo_board", root)
    D.board(m, bd, x0=LPO_X - 22, x1=LPO_X + 66, z0=-16, z1=16)
    pe = empty("host_pkg", root)
    G = D.package(m, pe, quad=False)
    at(pe, LPO_X, 0.0)
    host = group("host_lit", G["die"], span(2, 3))
    die_glow(m, host, "lit_tx")
    yb = BOARD_Y1
    mx0, mx1 = LPO_X + 26, LPO_X + 64
    box("lpo_floor", (mx0, yb, -7), (mx1, yb + 0.5, 7), m["dark_steel"], root)
    box("lpo_wall", (mx0, yb, -7), (mx1, yb + 6, -6.4), m["dark_steel"], root)
    box("lpo_pcb", (mx0 + 1, yb + 0.5, -6), (mx1 - 1, yb + 1.0, 6), m["fr4"], root)
    box("host_trace", (LPO_X + 15.5, yb, -0.25), (mx0 + 9, yb + 0.18, 0.25), m["copper"], root)
    for k, (a, b) in enumerate((((mx0 + 3, -3), (mx0 + 9, -2.8)), ((mx0 + 3, 2.8), (mx0 + 9, 3)),
                                ((mx0 + 3, -3), (mx0 + 3.2, 3)), ((mx0 + 8.8, -3), (mx0 + 9, 3)))):
        box(f"empty_fp{k}", (a[0], yb + 1.0, a[1]), (b[0], yb + 1.15, b[1]), m["thresh"], root)
    drv = empty("lpo_drv_at", root)
    D.driver(m, drv, mx0 + 12, mx0 + 17, 0.0, name="lpo_drv")
    drv.location = P(0, 1.0, 0)
    box("lpo_drv_trace", (mx0 + 9, yb + 1.0, -0.25), (mx0 + 12, yb + 1.18, 0.25), m["copper"], root)
    stream_of(root, "host_drive", 6, (LPO_X + 16, yb + 0.6, 0), [(0, 0, 0), (mx0 + 12 - LPO_X - 16, 0, 0)], 0.45,
              m["path"], 2, 0.05, 0.7, 60)
    tags(root, [
        (0, "100G/lane DSP: 5 nm", (TRAY_X - 14, y0 + 1.8, 4)),
        (0, "200G/lane: 3 nm (Sian3)", (TRAY_X, y0 + 1.8, 4)),
        (0, "400G/lane: a new DSP again", (TRAY_X + 14, y0 + 1.8, 4)),
        (1, "one DSP in every module", (FACE_X0 + 5, y0 + 13, 16)),
        (1, "tens of thousands per cluster", (FACE_X0 + 40, y0 + 5, 16)),
        (2, "host chip's SerDes", (LPO_X + 4, -2.95, 0)),
        (2, "LPO module: no DSP", (mx0 + 6, yb + 1.15, 3)),
        (2, "link rests on the host", (LPO_X + 22, yb + 0.6, 0)),
    ])
    return [
        frame((TRAY_X - 22, y0, -9), (TRAY_X + 22, y0 + 2.5, 9), 0.20, 0.75, fill=0.95),
        frame((FACE_X0, y0, -2), (FACE_X0 + 52, y0 + 22, 19), 0.35, 0.30, fill=0.97),
        frame((LPO_X - 15, -10, -13), (mx1, FIN_Y1, 13), 0.35, 0.50, fill=0.97),
    ]


SECTIONS = {1: sec_whole, 2: sec_parts, 3: sec_trip, 4: sec_nrz, 5: sec_eye,
            6: sec_fec, 7: sec_power, 8: sec_makers, 9: sec_risks}


def build(n):
    name = f"section_{n}"
    _, root = start(name, beats=BEATS, page=PAGE)
    m = D.materials()
    poses = SECTIONS[n](m, root)
    glide(root, poses)
    # The renderer's near plane is 40 mm and these parts are only a few mm across, so the whole
    # scene (camera included) is drawn SCALE times larger; the picture is the same, just unclipped.
    root.scale = (SCALE, SCALE, SCALE)
    print("poses", n, [(tuple(round(v, 1) for v in t), round(d, 1)) for t, d, _, _ in poses])
    return name


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--") + 1])
    finish(build(n), page=PAGE)
