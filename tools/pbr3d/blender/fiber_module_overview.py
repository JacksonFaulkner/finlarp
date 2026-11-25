"""The TRANSCEIVER overview, in the SAND template (docs/diagram-pages.md), built from the detailed
parts in fiber_module_detail.py: an 800G OSFP DR8 module (finned shell, card edge, PAM4 DSP, laser
driver, TIA, TOSA with eight lasers, ROSA with eight photodiodes, fibres to an MPO-16 port) seated in
its cage on a switch board, with the switch ASIC behind it and an MPO cable in front.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_module_overview.py

Writes blender/fiber_module_overview.blend and assets/fiber_module_overview.glb. One beat is 8 s.
Module frame: mm, Y up, the module's centre at x = 0, the faceplate toward -x, the ASIC toward +x.

Beats (match the seven beats in diagrams_nodes/fiber/module/overview.rs):
  0 the module in the link       ASIC, board copper, the module in its cage, the fibre leaving
  1 plug in: the module seats    the module slides in, card-edge fingers first, into the connector
  2 lid off: the optics          the finned lid lifts away: TOSA, ROSA, driver, TIA, DSP
  3 light at the front           light from the lasers out of the MPO; light back in to the photodiodes
  4 electrical in and out        lanes in at the card edge, DSP, bond wires to the lasers; back via TIA
  5 fins shed the heat           the lid comes back; heat rises off the fins into the fans' air
  6 next: the CPO                the ASIC becomes a CPO package with optics on it
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, key, label, tube  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
from pbr_kit import empty  # noqa: E402
import fiber_module_detail as D  # noqa: E402
from fiber_module_detail import frame, glide_camera, glow, grp, run  # noqa: E402

# Denser bead flows (2026-11 enhancement): twice the beads, slightly smaller, so each stream reads as a flow.
_run0 = run


def run(parent, name, pts, n, size, m, b, u0, u1, life):
    return _run0(parent, name, pts, max(3, 2 * n), size * 0.85, m, b, u0, u1, life)


PAGE = "fiber_module"
NAME = "overview"
BEATS = 7
END = F(BEATS, 0)
TOP = D.TOP
BY = D.BEAM_Y
ASIC_X = 135.0
S = 6.0  # the scene is scaled up under its root: the renderer's near plane is 40 units


def fibre_path(i, rx=False):
    zs = D.PD_Z if rx else D.LASER_Z
    k = 8 + i if rx else i
    return [(D.LENS_X, BY, zs[i]), (D.FAU_X[0] - 0.8, BY, zs[i]), (-30.0, BY, zs[i] * 0.75 + D.MPO_Z[k] * 0.25), (D.MPO_REC[0][0], BY, D.MPO_Z[k])]


CABLE = [(-46.0, BY, 0.0), (-60.0, BY - 1.0, 0.0), (-80.0, BY - 6.0, 0.0), (-105.0, BY - 14.0, 0.0), (-130.0, BY - 18.0, 0.0)]


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = D.mats()
    b = [beat(i) for i in range(BEATS)]

    # the switch: board, faceplate, cage, connector, host traces
    D.host_board(m, root, x1=165.0, hz=28.0)
    D.bezel(m, root, z0=-28.0)
    D.cage(m, root, top=False)
    D.connector(m, root)
    D.host_traces(m, root, x1=ASIC_X - 22.0)
    asic = grp("asic_on", root, [(0, F(6, 0))])
    D.asic(m, asic, ASIC_X, half=22.0)
    cpo = grp("cpo_on", root, b[6])
    D.cpo_package(m, cpo, ASIC_X)

    # the module: lid off underneath, the lid as its own part that comes and goes
    mod = D.module(m, root, lid="none", pkg_lid=False)
    key(mod, F(0, 0), "location", P(0, 0, 0))
    key(mod, F(1, 0) - 1, "location", P(0, 0, 0))
    key(mod, F(1, 0), "location", P(-60.0, 0, 0), linear=True)
    key(mod, F(1, 0.1), "location", P(-60.0, 0, 0), linear=True)
    key(mod, F(1, 0.7), "location", P(0, 0, 0))
    lid = D.lid_part(m, mod)
    key(lid, F(2, 0.05), "location", P(0, 0, 0))
    key(lid, F(2, 0.40), "location", P(0, 260.0, 0))
    key(lid, F(5, 0) - 1, "location", P(0, 260.0, 0))
    key(lid, F(5, 0), "location", P(0, 30.0, 0))
    key(lid, F(5, 0.05), "location", P(0, 30.0, 0))
    key(lid, F(5, 0.35), "location", P(0, 0, 0))

    # the MPO plug and its cable, in while the module is seated and closed or lit
    plug = grp("plug", root, b[0] + b[3] + b[6])
    box("plug_body", (-46.0, -4.8, -5.0), (-38.0, -1.1, 5.0), m["plastic"], plug)
    for k in range(len(CABLE) - 1):
        tube(f"cable_{k}", CABLE[k], CABLE[k + 1], 1.4 if k else 1.8, m["jacket"], plug, 14)

    # beat 0: lanes from the ASIC into the module, light out along the cable
    for k, z in enumerate(D.HOST_TRACE_Z[1::2]):
        run(root, f"b0_lane_{k}", [(ASIC_X - 22.0, -6.6, z), (40.5, -6.6, z), (36.0, -3.0, z * 0.5)], 3, 0.8, m["elec"], 0, 0.05 + 0.05 * k, 0.6, 60)
    run(root, "b0_light", CABLE, 4, 1.6, m["light"], 0, 0.2, 0.7, 60)

    # beat 3: light out of the lasers and in to the photodiodes
    for i in range(8):
        tx = fibre_path(i)
        run(root, f"tx_{i}", [(D.LASER_X[0], BY, D.LASER_Z[i])] + tx, 2, 0.4, m["light"], 3, 0.05 + 0.04 * i, 0.6, 70)
        rx = list(reversed(fibre_path(i, rx=True))) + [(-20.5, BY, D.PD_Z[i])]
        run(root, f"rx_{i}", rx, 2, 0.4, m["light"], 3, 0.10 + 0.04 * i, 0.65, 70)
        glow(mod, f"las_{i}", (D.LASER_X[0], TOP + 1.0, D.LASER_Z[i] - 0.25), (D.LASER_X[1], TOP + 1.5, D.LASER_Z[i] + 0.25), m["light_soft"], b[3], 0.06)
        glow(mod, f"pd_{i}", (-20.5, TOP + 1.0, D.PD_Z[i] - 0.3), (-20.0, TOP + 1.6, D.PD_Z[i] + 0.3), m["light_soft"], [(F(3, 0.4), F(4, 0))], 0.06)
    run(root, "cable_out", CABLE, 4, 1.9, m["light"], 3, 0.30, 0.75, 60)
    run(root, "cable_in", list(reversed(CABLE)), 4, 1.9, m["light"], 3, 0.02, 0.45, 60)
    beams = grp("beams", mod, b[3])
    for i, z in enumerate(D.LASER_Z):
        tube(f"beam_{i}", (D.LASER_X[0], BY, z), (D.FAU_X[1], BY, z), 0.12, m["light"], beams, 8)

    # beat 4: lanes in at the card edge to the DSP, on to the driver and over the bond wires to the
    # lasers; back from the photodiodes over the bond wires to the TIA, the DSP and the card edge
    for k in range(8):
        z = -3.5 + k
        run(root, f"in_{k}", [(34.0, TOP + 0.2, z), (11.0, TOP + 0.2, z), (7.0, TOP + 2.3, z * 0.6)], 2, 0.3, m["elec"], 4, 0.02 + 0.02 * k, 0.35, 40)
        run(root, f"out_{k}", [(7.0, TOP + 2.3, z * 0.6), (11.0, TOP + 0.2, z), (34.0, TOP + 0.2, z)], 2, 0.3, m["elec"], 4, 0.55 + 0.02 * k, 0.8, 40)
    for k in range(4):
        z = -6.5 + 1.1 * k
        run(root, f"to_drv_{k}", [(-4.0, TOP + 0.2, z), (-7.7, TOP + 0.2, z), (-9.0, TOP + 1.0, z)], 2, 0.3, m["elec"], 4, 0.25 + 0.03 * k, 0.5, 30)
        run(root, f"from_tia_{k}", [(-9.0, TOP + 1.0, -z), (-7.7, TOP + 0.2, -z), (-4.0, TOP + 0.2, -z)], 2, 0.3, m["elec"], 4, 0.45 + 0.03 * k, 0.7, 30)
    for i in range(8):
        run(root, f"bond_tx_{i}", D.lane_path(i), 2, 0.2, m["elec"], 4, 0.30 + 0.02 * i, 0.55, 40)
        run(root, f"bond_rx_{i}", D.lane_path(i, rx=True), 2, 0.2, m["elec"], 4, 0.35 + 0.02 * i, 0.6, 40)
    glow(mod, "dsp_on", *D.DSP_DIE, m["elec_soft"], [(F(4, 0.15), F(5, 0))], 0.06)
    glow(mod, "drv_on", *D.DRIVER, m["elec_soft"], [(F(4, 0.3), F(5, 0))])
    glow(mod, "tia_on", *D.TIA, m["elec_soft"], [(F(4, 0.4), F(5, 0))])

    # beat 5: heat rising off the fins, the fans' air along them
    for k, x in enumerate((-20.0, -4.0, 12.0)):
        for j, z in enumerate((-6.4, 0.0, 6.4)):
            run(root, f"heat_{k}_{j}", [(x, 11.5, z), (x + 2.0, 16.0, z), (x + 8.0, 22.0, z * 1.2)], 2, 0.7, m["heat"], 5, 0.30 + 0.05 * k + 0.03 * j, 0.8, 60)
    for j, z in enumerate((-4.0, 0.8, 5.6)):
        run(root, f"air_{j}", [(-60.0, 8.5, z), (45.0, 8.5, z)], 3, 0.6, m["air"], 5, 0.35 + 0.05 * j, 0.75, 80)

    # beat 6: data on to the CPO
    for k, z in enumerate((-3.2, 0.0, 3.2)):
        run(root, f"to_cpo_{k}", [(36.0, -3.0, z), (40.5, -6.6, z), (ASIC_X - 26.0, -6.6, z)], 3, 0.8, m["elec"], 6, 0.05 + 0.05 * k, 0.6, 60)

    # tags
    label("switch ASIC", (ASIC_X, D.BOARD_Y + 30.0, 0.0), root, b[0])
    label("TRANSCEIVER", (-6.0, D.FIN_TOP, 0.0), root, b[0])
    label("fibre to the next switch", CABLE[3], root, b[0])
    label("card-edge fingers lead", (36.5, TOP, 4.0), mod, b[1])
    label("OSFP cage", (8.0, 12.5, -12.0), root, b[1])
    label("isolator + TEC: EMLs need both", (-24.4, BY + 0.6, -5.0), mod, b[2])
    label("TOSA: transmit", (-22.5, TOP + 3.2, -5.0), mod, b[2])
    label("ROSA: receive", (-22.5, TOP + 3.2, 5.0), mod, b[2])
    label("PAM4 DSP", (3.5, TOP + 2.6, 3.3), mod, b[2])
    label("light out: 8 fibres", (-30.0, BY, -2.5), mod, b[3])
    label("light in: 8 fibres", (-30.0, BY, 2.5), mod, b[3])
    label("MPO plug", (-42.0, -1.1, 3.0), root, b[3])
    label("lanes in at the card edge", (30.0, TOP, 3.5), mod, b[4])
    label("bond wires to the lasers", (-14.0, TOP + 1.8, -4.5), mod, b[4])
    label("back out via the TIA", (-14.0, TOP + 1.8, 5.5), mod, b[4])
    label("finned shell: the heat sink", (-6.0, D.FIN_TOP, 3.0), root, b[5])
    label("fan air along the fins", (-40.0, 8.5, 0.8), root, b[5])
    label("CPO: optics on the package", (ASIC_X - 20.0, D.BOARD_Y + 3.9, 7.0), root, b[6])
    label("the pluggable today", (-6.0, D.FIN_TOP, 0.0), root, b[6])

    glide_camera(root, [
        frame((-110, -20, -28), (160, 25, 28), 0.75, 0.75, pad=0.80),
        frame((-100, -7, -14), (42, 13, 12), -0.90, 0.60, pad=0.84),
        frame((-40, -5, -10), (38, 2, 10), 0.10, 0.90, pad=1.0),
        frame((-70, -14, -9), (-14, 0, 9), -0.15, 0.80, pad=1.0),
        frame((-28, -5, -9), (38, -1, 9), 0.10, 0.90, pad=1.0),
        frame((-62, -6, -12), (46, 24, 12), 0.45, 0.50, pad=0.86),
        frame((-40, -10, -40), (178, 25, 40), 0.55, 0.85, pad=0.80),
    ])
    return root


if __name__ == "__main__":
    r = build()
    r.scale = (S, S, S)
    finish(NAME, page=PAGE)
