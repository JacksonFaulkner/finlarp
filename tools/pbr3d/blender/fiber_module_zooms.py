"""Zoom-ins (a-e) for the TRANSCEIVER overview: each is its own three-beat close-up built from the
detailed parts in fiber_module_detail.py (the same module and switch as the overview), the camera
framed on its subject in every beat, tags pinned to the parts they name.

  a the finned lid        the finned shell; heat rising off the fins; a section: cover and heat sink
  b TOSA: transmit port   the MPO port at the nose; light leaving the transmit fibres; the receive fibres beside them
  c ROSA: receive can     the closed ROSA; light in through the lenses onto the photodiodes; current to the TIA
  d PCB and chips         the module board; the laser driver and its bond wires; the TIA (amplifier)
  e gold edge pins        the card edge short of the connector; it slides in, lanes arrive; both directions

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_module_zooms.py -- a

Writes assets/fiber_module_zoom_<letter>.glb (and blender/fiber_module_zoom_<letter>.blend).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, key, label, tube  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
from pbr_kit import empty  # noqa: E402
import fiber_module_detail as D  # noqa: E402
from fiber_module_detail import frame, glide_camera, glow, grp, run  # noqa: E402

PAGE = "fiber_module"
BEATS = 3
END = F(BEATS, 0)
B0, B1, B2 = beat(0), beat(1), beat(2)
TOP = D.TOP
BY = D.BEAM_Y
S = 6.0
SEC_X = 3.5


def host(m, parent, conn_cut=False):
    D.host_board(m, parent)
    D.bezel(m, parent)
    D.cage(m, parent, top=False)
    D.connector(m, parent, cutaway=conn_cut)
    D.host_traces(m, parent)


def fibre_path(i, rx=False):
    zs = D.PD_Z if rx else D.LASER_Z
    k = 8 + i if rx else i
    return [(D.LENS_X, BY, zs[i]), (D.FAU_X[0] - 0.8, BY, zs[i]), (-30.0, BY, zs[i] * 0.75 + D.MPO_Z[k] * 0.25), (D.MPO_REC[0][0], BY, D.MPO_Z[k])]


def pkg_lid(m, parent, which, intervals):
    (x0, y0, z0), (x1, y1, z1) = D.TOSA if which == "tosa" else D.ROSA
    g = grp(f"{which}_closed", parent, intervals)
    box(f"{which}_near_wall", (x0, y0, z1 - 0.4), (x1, y1, z1), m["pkg"], g)
    box(f"{which}_top", (x0, y1, z0), (x1, y1 + 0.35, z1), m["pkg"], g)


def zoom_a(m, root):
    whole = grp("whole", root, B0 + B1)
    host(m, whole)
    D.module(m, whole, lid="full", name="module_whole")
    for k, x in enumerate((-20.0, -4.0, 12.0)):
        for j, z in enumerate((-6.4, 0.0, 6.4)):
            run(root, f"heat_{k}_{j}", [(x, 11.5, z), (x + 2.0, 16.0, z), (x + 8.0, 23.0, z * 1.2)], 3, 0.7, m["heat"], 1, 0.05 + 0.05 * k + 0.03 * j, 0.8, 60)
    sec = grp("section", root, B2)
    rot = empty("section_rot", sec)
    D.host_board(m, rot)
    D.cage(m, rot, top=True, near=True)
    D.module(m, rot, lid="full", name="module_cut")
    for o in list(D.meshes(rot)):
        D.cut_x(o, SEC_X)
    rot.rotation_euler = (0.0, 0.0, -math.pi / 2)
    glow(rot, "dsp_hot", D.DSP_DIE[0], (SEC_X, D.DSP_PAD[1][1], D.DSP_DIE[1][2]), m["hot"], [(F(2, 0.1), END)], 0.04)
    for k, z in enumerate((-2.4, 0.0, 2.4)):
        run(rot, f"heat_up_{k}", [(SEC_X + 0.2, TOP + 2.4, z), (SEC_X + 0.2, D.LID[1], z), (SEC_X + 0.2, D.FIN_TOP + 0.5, 3.0 * (k - 1))], 3, 0.4, m["heat"], 2, 0.1 + 0.08 * k, 0.8, 60)
    label("fins cast into the lid", (-6.0, D.FIN_TOP, 3.0), root, B0)
    label("lid: the module's top cover", (-30.0, D.LID[1], 10.0), root, B0)
    label("heat rises off the fins", (2.0, D.FIN_TOP + 6.0, 0.0), root, B1)
    label("DSP heat into the lid", (SEC_X, TOP + 2.2, 3.5), rot, B2)
    label("cover and heat sink in one", (SEC_X, D.FIN_TOP, -8.0), rot, B2)
    return [
        frame((-36, -6, -11), (28, 11, 11), 0.45, 0.55, pad=1.0),
        frame((-36, -6, -11), (28, 22, 11), 0.40, 0.40, pad=1.0),
        frame((-13, -9, 0), (13, 12, SEC_X), 0.0, 0.20, pad=1.08),
    ]


def zoom_b(m, root):
    host(m, root)
    mod = D.module(m, root, lid="cut", pkg_lid=False)
    pkg_lid(m, mod, "rosa", [(0, END)])
    for i in range(8):
        tx = [(D.LASER_X[0], BY, D.LASER_Z[i])] + fibre_path(i) + [(-52.0, BY, D.MPO_Z[i])]
        run(root, f"tx_{i}", tx, 2, 0.4, m["light"], 1, 0.05 + 0.04 * i, 0.6, 60)
        run(root, f"tx2_{i}", tx, 1, 0.4, m["light"], 2, 0.05 + 0.04 * i, 0.4, 60)
        rx = [(-52.0, BY, D.MPO_Z[8 + i])] + list(reversed(fibre_path(i, rx=True)))
        run(root, f"rx_{i}", rx, 2, 0.4, m["light"], 2, 0.20 + 0.04 * i, 0.7, 60)
        glow(mod, f"las_{i}", (D.LASER_X[0], TOP + 1.0, D.LASER_Z[i] - 0.25), (D.LASER_X[1], TOP + 1.5, D.LASER_Z[i] + 0.25), m["light_soft"], [(F(1, 0), END)], 0.06)
    ends = grp("tx_ends", mod, [(F(1, 0.2), END)])
    rx_ends = grp("rx_ends", mod, [(F(2, 0.3), END)])
    for k, z in enumerate(D.MPO_Z):
        box(f"mpo_lit_{k}", (D.MPO_REC[0][0] - 0.15, BY - 0.2, z - 0.2), (D.MPO_REC[0][0], BY + 0.2, z + 0.2), m["light"], ends if k < 8 else rx_ends)
    label("MPO port: 16 fibres", (-38.0, -1.3, 0.0), mod, B0)
    label("transmit fibres from the TOSA", (-30.0, BY, -2.5), mod, B0)
    label("8 beams out, one per fibre", (-48.0, BY, -2.0), root, B1)
    label("receive fibres, same MPO", (-38.0, BY, 3.5), mod, B2)
    label("to the ROSA", (-30.0, BY, 2.5), mod, B2)
    return [
        frame((-46, -6, -10), (-18, 0, 10), -0.55, 0.60, pad=1.02),
        frame((-56, -6, -10), (-18, 0, 4), -0.40, 0.70, pad=1.02),
        frame((-56, -6, -6), (-18, 0, 10), -0.35, 0.70, pad=1.02),
    ]


def zoom_c(m, root):
    host(m, root)
    mod = D.module(m, root, lid="cut", pkg_lid=False)
    pkg_lid(m, mod, "rosa", B0)
    pkg_lid(m, mod, "tosa", [(0, END)])
    for i, z in enumerate(D.PD_Z):
        rx = [(-46.0, BY, D.MPO_Z[8 + i])] + list(reversed(fibre_path(i, rx=True))) + [(-20.5, BY, z)]
        run(root, f"rx_{i}", rx, 2, 0.4, m["light"], 1, 0.03 + 0.04 * i, 0.6, 60)
        glow(mod, f"pd_{i}", (-20.5, TOP + 1.0, z - 0.3), (-20.0, TOP + 1.6, z + 0.3), m["light_soft"], [(F(1, 0.3), END)], 0.06)
        run(root, f"pdc_{i}", D.lane_path(i, rx=True), 3, 0.2, m["elec"], 2, 0.05 + 0.03 * i, 0.7, 40)
    glow(mod, "tia_on", *D.TIA, m["elec_soft"], [(F(2, 0.3), END)])
    label("ROSA: the receive package", (-22.5, TOP + 3.6, 5.0), mod, B0)
    label("fibres in from the MPO", (-30.0, BY, 2.5), mod, B0)
    label("lenses focus the light", (D.LENS_X, BY + 0.4, 8.1), mod, B1)
    label("8 photodiodes", (-20.25, TOP + 1.6, 8.5), mod, B1)
    label("bond wires to the TIA", (-14.0, TOP + 1.8, 6.0), mod, B2)
    label("TIA: the amplifier", (-10.75, TOP + 1.0, 5.0), mod, B2)
    return [
        frame((-30, -5, 0), (-12, 0, 9), 0.0, 0.80, pad=1.05),
        frame((-30, -5, 0), (-17, -1, 9), 0.0, 0.95, pad=1.05),
        frame((-22, -5, 1), (-7, -1, 9), 0.15, 0.85, pad=1.05),
    ]


def zoom_d(m, root):
    host(m, root)
    mod = D.module(m, root, lid="none", pkg_lid=False)
    glow(mod, "drv_on", *D.DRIVER, m["elec_soft"], [(F(1, 0.15), F(2, 0))])
    glow(mod, "tia_on", *D.TIA, m["elec_soft"], [(F(2, 0.15), END)])
    for k in range(4):
        z = -6.5 + 1.1 * k
        run(root, f"to_drv_{k}", [(-4.0, TOP + 0.2, z), (-7.7, TOP + 0.2, z), (-9.0, TOP + 1.0, z)], 2, 0.3, m["elec"], 1, 0.05 + 0.04 * k, 0.5, 30)
        run(root, f"from_tia_{k}", [(-9.0, TOP + 1.0, -z), (-7.7, TOP + 0.2, -z), (-4.0, TOP + 0.2, -z)], 2, 0.3, m["elec"], 2, 0.45 + 0.04 * k, 0.8, 30)
    for i in range(8):
        run(root, f"bond_tx_{i}", D.lane_path(i), 3, 0.2, m["elec"], 1, 0.25 + 0.03 * i, 0.75, 40)
        run(root, f"bond_rx_{i}", D.lane_path(i, rx=True), 3, 0.2, m["elec"], 2, 0.05 + 0.03 * i, 0.5, 40)
        glow(mod, f"las_{i}", (D.LASER_X[0], TOP + 1.0, D.LASER_Z[i] - 0.25), (D.LASER_X[1], TOP + 1.5, D.LASER_Z[i] + 0.25), m["light_soft"], [(F(1, 0.4), F(2, 0))], 0.06)
    label("module PCB", (-16.0, TOP, 0.0), mod, B0)
    label("PAM4 DSP", (3.5, TOP + 2.6, 3.3), mod, B0)
    label("controller", (17.0, TOP + 0.9, 8.0), mod, B0)
    label("laser driver", (-10.75, TOP + 1.0, -5.0), mod, B1)
    label("bond wires to the lasers", (-14.0, TOP + 1.8, -4.5), mod, B1)
    label("TIA: the amplifier", (-10.75, TOP + 1.0, 5.0), mod, B2)
    label("received lanes to the DSP", (-5.0, TOP, 6.5), mod, B2)
    return [
        frame((-32, -5, -10), (24, 0, 10), 0.10, 0.90, pad=1.0),
        frame((-21, -5, -8.5), (-4, -1, -1.5), 0.10, 0.85, pad=1.05),
        frame((-21, -5, 1.5), (-4, -1, 8.5), 0.10, 0.85, pad=1.05),
    ]


def zoom_e(m, root):
    host(m, root, conn_cut=True)
    mod = D.module(m, root, lid="full")
    key(mod, F(0, 0), "location", P(-12.0, 0, 0))
    key(mod, F(1, 0.05), "location", P(-12.0, 0, 0), linear=True)
    key(mod, F(1, 0.6), "location", P(0, 0, 0))
    for k, z in enumerate(D.HOST_TRACE_Z):
        run(root, f"in_{k}", [(78.0, -6.7, z), (40.5, -6.7, z), (33.0, -5.1, z * 1.2)], 2, 0.5, m["elec"], 1, 0.65 + 0.03 * k, 0.95, 30)
        run(root, f"in2_{k}", [(78.0, -6.7, z), (40.5, -6.7, z), (33.0, -5.1, z * 1.2)], 2, 0.5, m["elec"], 2, 0.03 + 0.03 * k, 0.5, 40)
        run(root, f"out_{k}", [(33.0, -5.1, z * 1.2), (40.5, -6.7, z + 0.3), (78.0, -6.7, z + 0.3)], 2, 0.5, m["elec"], 2, 0.35 + 0.03 * k, 0.8, 40)
    for k, z in enumerate(D.FINGER_Z):
        glow(root, f"contact_{k}", (29.5, D.SLOT[0], z - 0.3), (33.5, D.SLOT[0] + 0.12, z + 0.3), m["elec"], [(F(1, 0.6), END)], 0.05)
    label("gold fingers, top and bottom", (36.5, TOP, 4.0), mod, B0)
    label("connector slot", (29.0, -4.6, 8.0), root, B0)
    label("fingers on the springs", (31.0, D.SLOT[0], 7.0), root, B1)
    label("lanes in from the switch", (60.0, -6.8, 5.6), root, B1)
    label("8 lanes in, 8 lanes out", (60.0, -6.8, 5.6), root, B2)
    return [
        frame((12, -8, -11), (42, 0, 11), 0.55, 0.45, pad=1.0),
        frame((18, -8, -11), (60, 0, 11), 0.45, 0.50, pad=1.0),
        frame((24, -8, -11), (70, 0, 11), 0.45, 0.60, pad=1.02),
    ]


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    if letter not in ZOOMS:
        raise SystemExit(f"unknown zoom {letter!r}; one of {sorted(ZOOMS)}")
    _, root = start(f"zoom_{letter}", beats=BEATS, page=PAGE)
    m = D.mats()
    poses = ZOOMS[letter](m, root)
    glide_camera(root, poses)
    root.scale = (S, S, S)
    finish(f"zoom_{letter}", page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1:
        raise SystemExit("usage: blender -b --python fiber_module_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
