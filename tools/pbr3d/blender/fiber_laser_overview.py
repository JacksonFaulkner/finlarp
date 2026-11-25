"""The LASER node page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_laser_overview.py

Writes blender/fiber_laser_overview.blend and assets/fiber_laser_overview.glb. One beat is 8 s.

Beats 0 and 6 show the whole FIBER link from fiber_kit.py, as on the tab overview. Beats 1-5 move to a
detailed close-up built above the link (group BENCH, offset by OFF): a TO-can cut open with its gold
header, glass-sealed pins and heat-sink post, the InP EML on its AlN submount with the monitor
photodiode behind it, gold bond wires from the pins, the laser driver IC the pins run to, and outside
the window a lens, a gold sleeve and a ceramic ferrule holding the fibre. The parts come from
fiber_laser_detail.py, as in the numbered sections.

Beats (match the seven beats in diagrams_nodes/fiber/laser/overview.rs):
  0 context    the whole link; the laser station is highlighted
  1 TO-can     the can cut open: chip, submount, monitor photodiode, window, pins to the driver
  2 bits       bias and data run from the driver up the pins and wires; the facet steps through four levels
  3 window     the beam crosses the window, the lens focuses it into the ferrule
  4 power      back light lands on the monitor photodiode; its current runs back to the driver
  5 coupling   rays converge on the single-mode core at the ferrule's face
  6 next       the light runs down the fibre toward the photodiode

fiber_laser_zooms.py rebuilds this scene with its own camera and tags (it swaps LABEL and CAMERA).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, ball, tube, label, beat, show  # noqa: E402
from sand_zooms import start, finish, stream_of  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402
import fiber_kit as K  # noqa: E402
import fiber_laser_detail as D  # noqa: E402
from fiber_laser_detail import frame, camera_path, wire, offsets  # noqa: E402

PAGE = "fiber_laser"
NAME = "overview"
BEATS = 7

LX = K.LASER_X
PAM4_SEQ = (3, 0, 2, 1, 1, 3, 0, 2)  # four-level symbols, one per eighth of beat 2
OFF = (0.0, 400.0, 0.0)  # where the close-up bench sits, above the link

# the close-up's layout (bench coordinates, before OFF)
S = 0.25
C = (5.0, 0.0, 0.0)  # chip origin: back facet on the can's axis
PIN_BIAS, PIN_DATA, PIN_MON = (10.0, -14.0), (-14.0, -16.0), (18.0, -9.0)  # (y, z) through the header
DRV_X = -50.0  # the driver's face, where the pins end
LENS_X, FER_X, FIB_END = 58.0, 76.0, 150.0

# swapped by fiber_laser_zooms.py
LABEL = label
CAMERA = camera_path


def extra_materials():
    return {
        "highlight": mat("lzo_highlight", (1.0, 0.75, 0.25), rough=0.5, alpha=0.22),
    }


def at(p):
    """A bench point in scene coordinates."""
    return (p[0] + OFF[0], p[1] + OFF[1], p[2] + OFF[2])


def pose(c, size, yaw, pitch, **k):
    return frame(at(c), size, yaw, pitch, **k)


def bench(m, root):
    """The detailed close-up. Built at the origin under one group, then moved up by OFF.
    Returns the group and the points the labels and streams need (bench coordinates)."""
    g = empty("laser_bench", root)
    e_iso = {"garnet": mat("lzo_garnet", (0.75, 0.25, 0.15), rough=0.25, alpha=0.6),
             "jacket": mat("lzo_jacket", (0.85, 0.68, 0.12), rough=0.95)}
    D.header(m, g, -4.0, 0.0, 30.0, True, [PIN_BIAS, PIN_DATA, PIN_MON], "ovhdr")
    box("ov_post", (0.0, -22.0, -10.0), (30.0, -6.5, 0.0), m["post"], g)
    cp, lit = D.chip(m, g, C, S, name="ovchip")
    sp = D.submount(m, g, C, S, name="ovsub")
    D.cap(m, g, 0.0, 40.0, 26.0, True, name="ovcap")
    for k, (y, z) in enumerate((PIN_BIAS, PIN_DATA, PIN_MON)):
        D.pin(f"ov_pin{k}", [(DRV_X, y, z), (4.0, y, z)], m, g, 1.0)
    # the laser driver IC the pins run to (standing on the board edge, leads on its face)
    # the driver package, its top front corner cut away to show the die and its bond wires
    box("ov_drv", (DRV_X - 26.0, -26.0, -26.0), (DRV_X, 26.0, -6.0), m["ic"], g)
    box("ov_drv_t0", (DRV_X - 26.0, -26.0, -6.0), (DRV_X, 4.0, 0.0), m["ic"], g)
    box("ov_drv_t1", (DRV_X - 26.0, 22.0, -6.0), (DRV_X, 26.0, 0.0), m["ic"], g)
    box("ov_drv_t2", (DRV_X - 26.0, 4.0, -6.0), (DRV_X - 22.0, 22.0, 0.0), m["ic"], g)
    box("ov_drv_t3", (DRV_X - 4.0, 4.0, -6.0), (DRV_X, 22.0, 0.0), m["ic"], g)
    box("ov_drv_pad", (DRV_X - 20.0, 6.0, -6.0), (DRV_X - 6.0, 20.0, -5.6), m["gold"], g)
    box("ov_drv_die", (DRV_X - 18.0, 8.0, -5.6), (DRV_X - 8.0, 18.0, -4.4), m["si"], g)
    for i, y in enumerate((9.5, 12.0, 14.5, 17.0)):
        box(f"ov_drv_cell{i}", (DRV_X - 16.0, y - 0.6, -4.4), (DRV_X - 10.0, y + 0.6, -4.25), m["grid"], g)
        wire(f"ov_drv_bw{i}", (DRV_X - 8.0, y, -4.4), (DRV_X - 2.0, y, -2.0), 1.5, m["gold"], g, 0.2)
    for i, z in enumerate((-8.0, -14.0, -20.0)):
        box(f"ov_cap{i}", (DRV_X + 2.0, -26.0, z - 1.5), (DRV_X + 6.0, -23.5, z + 1.5), m["ic"], g)
        box(f"ov_cap{i}_a", (DRV_X + 1.6, -26.0, z - 1.6), (DRV_X + 2.6, -23.4, z + 1.6), m["steel"], g)
        box(f"ov_cap{i}_b", (DRV_X + 5.4, -26.0, z - 1.6), (DRV_X + 6.4, -23.4, z + 1.6), m["steel"], g)
    for i in range(4):
        box(f"ov_trace{i}", (DRV_X - 33.0, -26.0, -5.0 - 5.0 * i), (DRV_X - 26.0, -25.8, -4.0 - 5.0 * i), m["gold"], g)
    # thermistor on the post beside the submount (the bias loop reads it to hold wavelength)
    box("ov_ntc", (24.0, -6.5, -9.0), (27.5, -4.5, -6.0), m["zirconia"], g)
    box("ov_ntc_a", (23.6, -6.5, -9.1), (24.4, -4.3, -5.9), m["gold"], g)
    box("ov_ntc_b", (27.1, -6.5, -9.1), (27.9, -4.3, -5.9), m["gold"], g)
    for i in range(7):
        y = -21.0 + 7.0 * i
        box(f"ov_drv_lead{i}", (DRV_X - 0.3, y - 1.0, -4.0), (DRV_X + 1.4, y + 1.0, 0.0), m["gold"], g)
    tube("ov_drv_dot", (DRV_X - 22.0, -20.0, 0.0), (DRV_X - 22.0, -20.0, 0.15), 1.4, m["steel"], g, 12)
    box("ov_board", (DRV_X - 34.0, -34.0, -30.0), (DRV_X + 10.0, -26.0, 0.0), m["pcb"], g)
    wb = wire("ov_bias_w", (4.0, *PIN_BIAS), cp["dfb_pad"], 3.0, m["gold"], g, 0.3)
    wd = wire("ov_data_w", (4.0, *PIN_DATA), cp["eam_pad"], 6.0, m["gold"], g, 0.3)
    wm = wire("ov_mon_w", sp["pd_pad"], (4.0, *PIN_MON), 2.0, m["gold"], g, 0.3)
    # outside the window: lens, sleeve, ferrule, fibre (as in the sections' lens_fibre)
    D.pipe_x("ov_holder", LENS_X - 3.0, LENS_X + 3.0, 12.0, 8.5, m["steel"], g)
    o = D.ellipsoid("ov_lens", (LENS_X, 0.0, 0.0), 2.8, 9.0, 9.0, m["glass"], g)
    D.cut(o, 0.0)
    box("ov_lens_post", (LENS_X - 3.0, -40.0, -10.0), (LENS_X + 3.0, -12.0, 0.0), m["post"], g)
    D.pipe_x("ov_sleeve", FER_X - 2.0, FER_X + 24.0, 7.5, 5.0, m["gold"], g)
    D.pipe_x("ov_ferrule", FER_X, FER_X + 24.0, 5.0, 1.4, m["zirconia"], g)
    D.rod("ov_glass", (FER_X, 0.0, 0.0), (FIB_END, 0.0, 0.0), 1.4, m["clad"], g, True, 24)
    # stripped back in steps so every layer shows: glass, acrylate coating, buffer, jacket
    D.pipe_x("ov_coat", FER_X + 24.0, FIB_END - 14.0, 4.0, 1.4, m["coating"], g)
    D.pipe_x("ov_buffer", FER_X + 24.5, FIB_END - 26.0, 5.2, 4.0, m["zirconia"], g)
    D.pipe_x("ov_jacket", FER_X + 25.0, FIB_END - 38.0, 7.0, 5.2, e_iso["jacket"], g)
    # optical isolator between lens and ferrule: magnet ring round a Faraday garnet and polarisers
    D.pipe_x("ov_iso_mag", 65.5, 70.5, 8.4, 7.2, m["ic"], g)
    for k, (x0, x1, mt) in enumerate(((64.6, 65.2, "glass"), (67.4, 68.8, "garnet"), (70.8, 71.4, "glass"))):
        D.rod(f"ov_iso{k}", (x0, 0.0, 0.0), (x1, 0.0, 0.0), 7.0, e_iso[mt] if mt == "garnet" else m[mt], g, True, 32)
    box("ov_iso_post", (65.5, -40.0, -10.0), (70.5, -8.4, 0.0), m["post"], g)
    box("ov_fer_post", (FER_X + 4.0, -40.0, -10.0), (FER_X + 20.0, -7.5, 0.0), m["post"], g)
    box("ov_bench_plate", (DRV_X - 34.0, -44.0, -30.0), (FIB_END, -40.0, 0.0), m["dark_steel"], g)
    box("ov_can_post", (-4.0, -40.0, -10.0), (30.0, -30.0, 0.0), m["post"], g)
    lit_core = empty("ov_core", g)
    D.rod("ov_core_l", (FER_X, 0.0, 0.0), (FIB_END, 0.0, 0.0), 0.5, m["light"], lit_core, True, 12, front=0.6)

    fx = cp["front"][0]
    # the laser runs from beat 1 on
    show(lit["dfb"], [(F(1, 0.2), F(6, 0))])
    show(lit["eam"], [(F(1, 0.2), F(6, 0))])
    show(lit_core, [(F(3, 0.4), F(6, 0))])
    # beat 2: bias (blue) and data (pink) from the driver; the facet glow steps through four sizes
    bias = [(DRV_X, *PIN_BIAS), (4.0, *PIN_BIAS)] + wb[1:]
    data = [(DRV_X, *PIN_DATA), (4.0, *PIN_DATA)] + wd[1:]
    for b in (1, 2, 4):
        stream_of(g, f"ov_bias{b}", 12, bias[0], offsets(bias), 1.0, m["elec"], b, 0.0, 0.7, 60)
    stream_of(g, "ov_data", 14, data[0], offsets(data), 1.0, m["rf"], 2, 0.0, 0.75, 60)
    for k, r in enumerate((0.6, 1.1, 1.6, 2.1)):
        lv = empty(f"ov_level{k}", g)
        ball(f"ov_level{k}_glow", (fx, 0.0, 0.0), r, m["light"], lv, 16)
        show(lv, [(F(2, i / 8.0), F(2, (i + 1) / 8.0)) for i, s in enumerate(PAM4_SEQ) if s == k])
    # beats 3 and 5: the beam through the window and lens into the ferrule
    beam = empty("ov_beam", g)
    D.cone("ov_beam_a", (fx, 0, 0), (LENS_X - 1.0, 0, 0), 0.3, 8.0, m["beam"], beam, 32, half=True)
    D.cone("ov_beam_b", (LENS_X + 1.0, 0, 0), (FER_X, 0, 0), 8.0, 0.4, m["beam"], beam, 32, half=True)
    show(beam, [(F(3, 0.05), F(4, 0)), (F(5, 0), F(6, 0))])
    stream_of(g, "ov_ray3", 10, (fx, 0.0, 0.6), [(0, 0, 0), (LENS_X - fx, 0, 0), (FER_X - fx, 0, 0), (FIB_END - fx, 0, 0)],
              0.8, m["light"], 3, 0.05, 0.75, 70)
    # beat 4: back light on the monitor photodiode; its current back to the driver
    back = empty("ov_back", g)
    D.cone("ov_back_c", cp["back"], (sp["pd_face"][0] + 0.1, 0, 0), 0.3, 1.6, m["beam"], back, 24, 1.4, 1.0, half=True)
    show(back, beat(4))
    show(sp["pd_lit"], beat(4))
    mon = wm + [(DRV_X, *PIN_MON)]
    stream_of(g, "ov_mon", 12, mon[0], offsets(mon), 1.0, m["elec"], 4, 0.05, 0.8, 60)
    # beat 5: four rays converge on the core at the ferrule's face
    rays = empty("ov_rays", g)
    show(rays, beat(5))
    for k, (dy, dz) in enumerate(((7.0, 0.0), (-7.0, 0.0), (4.0, -5.0), (-4.0, -5.0))):
        tube(f"ov_rayline{k}", (LENS_X + 1.0, dy, dz), (FER_X, 0.0, 0.0), 0.25, m["light"], rays, 8)
        stream_of(g, f"ov_conv{k}", 2, (LENS_X + 1.0, dy, dz), [(0, 0, 0), (FER_X - LENS_X - 1.0, -dy, -dz)],
                  0.6, m["light"], 5, 0.05 + 0.1 * k, 0.5 + 0.1 * k, 30)
    stream_of(g, "ov_core5", 8, (FER_X, 0.0, 0.3), [(0, 0, 0), (FIB_END - FER_X, 0, 0)], 0.55, m["light"], 5, 0.3, 0.9, 50)
    g.location = P(*OFF)
    pts = {"cp": cp, "sp": sp, "wb": wb, "wd": wd, "wm": wm, "fx": fx}
    return g, pts


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = K.materials()
    m.update(D.materials())
    e = extra_materials()

    # the whole link (beats 0 and 6)
    K.board(m, root)
    K.trace(m, root)
    K.dsp(m, root)
    K.photodiode(m, root)
    K.module(m, root)
    K.cpo(m, root)
    K.laser(m, root)
    core = empty("laser_fibre_core", root)
    K.fibre(m, root, core_parent=core)
    show(core, [(F(6, 0), F(7, 0))])
    hl = box("lz_highlight", (28.0, -10.0, -9.0), (58.0, 7.0, 9.0), e["highlight"], root)
    show(hl, beat(0))
    stream_of(root, "beam_fib_s", 8, (LX + 14.0, K.FIBRE_Y, 0.0), [(0, 0, 0), (K.FIBRE_X1 - (LX + 14.0), 0, 0)],
              1.2, m["light"], 6, 0.05, 0.6, 40)
    stream_of(root, "dsp_to_laser", 8, (K.DSP_X + 14.0, -6.3, -9.0), [(0, 0, 0), (LX - K.DSP_X - 18.0, 0, 0)],
              1.2, m["elec"], 0, 0.05, 0.7, 40)

    g, p = bench(m, root)
    cp, sp, wb, wd, wm, fx = p["cp"], p["sp"], p["wb"], p["wd"], p["wm"], p["fx"]
    tags = {
        0: [("PAM4 DSP", (K.DSP_X, 3.0, 11.0)), ("LASER", (LX, 0.5, 0.0)), ("OPTICAL FIBER", (80.0, -2.4, 0.0))],
        1: [("cap, cut open", at((24.0, 25.0, 0.0))), ("laser chip on its submount", at((C[0] + S * 30, cp["top"], 0.0))),
            ("thermistor", at((25.7, -4.5, -7.5))),
            ("glass window", at((39.6, 7.0, 0.0))), ("gold pins to the driver IC", at((-24.0, PIN_BIAS[0], PIN_BIAS[1])))],
        2: [("laser driver IC", at((DRV_X - 13.0, 26.0, -13.0))), ("driver die, package cut open", at((DRV_X - 13.0, 13.0, -4.4))), ("bias + data up the pins", at(wd[6])),
            ("4 light levels at the facet", at((fx + 0.5, 1.8, 0.0)))],
        3: [("beam crosses the window", at((40.5, 3.5, 0.0))), ("lens focuses it", at((LENS_X, 9.0, 0.0))),
            ("isolator: blocks reflections", at((68.0, 10.0, 0.0))),
            ("gold sleeve + ceramic ferrule", at((FER_X + 12.0, 7.5, 0.0)))],
        4: [("monitor photodiode", at(sp["pd"])), ("back light lands on it", at(sp["pd_face"])),
            ("its current back to the driver", at((-24.0, PIN_MON[0], PIN_MON[1])))],
        5: [("rays converge on the core", at((FER_X - 6.0, 2.0, 0.0))), ("single-mode core, ~9 um", at((FER_X + 10.0, 0.5, 0.0))),
            ("ceramic ferrule", at((FER_X + 18.0, -5.0, 0.0)))],
        6: [("LASER", (LX, 0.5, 0.0)), ("OPTICAL FIBER", (80.0, -2.4, 0.0)), ("PHOTODIODE", (K.PD_X, 0.5, 0.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            LABEL(text, pos, root, beat(i))

    CAMERA(root, POSES)
    return root


POSES = [
    frame((66.0, 18.0, -12.0), 160.0, 0.28, 0.62, pad=1.0),
    pose((12.0, -2.0, 0.0), 78.0, 0.42, 0.30),
    pose((-10.0, 0.0, -6.0), 84.0, 0.38, 0.36),
    pose((54.0, 0.0, 0.0), 82.0, 0.30, 0.22),
    pose((-8.0, 4.0, -6.0), 62.0, 0.38, 0.32),
    pose((76.0, 0.0, 0.0), 44.0, 0.38, 0.22),
    frame((82.0, 10.0, -8.0), 116.0, 0.30, 0.45, pad=1.0),
]


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
