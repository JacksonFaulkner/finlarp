"""The PHOTODIODE node's overview: the receiver close up, in the detailed parts of the sections.

Run from the repo root (on the worker, or locally):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_photodiode_overview.py

Writes blender/fiber_photodiode_overview.blend and assets/fiber_photodiode_overview.glb. One beat is 8 s.

The receiver (TO-can with ball lens, PIN chip cut into its layers, TIA, gold bond wires, pins) comes
from fiber_photodiode_detail.py, drawn about 16x life size with the can at the origin. The rest of the
link (DSP, laser, transceiver, CPO and the board under them) is fiber_kit.py's stations in a group
scaled 10x and shifted (LINK_AT) so the kit's photodiode station lands on the detailed can. The kit's
own photodiode and fibre are left out; the fibre here runs from the kit laser's window to the
detailed ferrule, and the current runs from the OUT pin down a flex and along a board trace into the
transceiver's cage.

Beats (match the seven beats in diagrams_nodes/fiber/photodiode/overview.rs):
  0 the whole link, the photodiode singled out   six labels, glowing outline round the receiver
  1 light lands at the window                     sealed can; light leaves the fibre, the lens catches it
  2 the chip absorbs the light                    can cut open; pairs freed in the InGaAs
  3 current out                                   current up the bond wire to the TIA, voltage out the pin
  4 more light, more current                      bright burst then dim burst; thick then thin current
  5 the pulse follows                             two short light pulses, a current pulse after each
  6 to the transceiver                            pull back: the current runs down the trace into the cage
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fiber_kit as K  # noqa: E402
import fiber_photodiode_detail as D  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402
from sand_overview import F, P, beat, box, fly, label, show, tube  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
from fiber_photodiode_detail import blip, frame, front, run  # noqa: E402

PAGE = "fiber_photodiode"
NAME = "overview"
BEATS = 7

KS = 10.0                              # kit scale
LINK_AT = (-10.0 * K.PD_X - 8.0, 20.0)  # kit (x, y) -> (KS * x + ax, KS * y + ay)
BOARD_TOP = KS * -7.0 + LINK_AT[1]      # -50: the board's top, which the can's mount stands on


def kit(x, y, z):
    """A kit (fiber_kit) point in this scene's coordinates."""
    return (KS * x + LINK_AT[0], KS * y + LINK_AT[1], KS * z)


CAGE_X0 = kit(K.MOD_X - 26.0, 0, 0)[0]   # the cage's near face
LASER_WIN = kit(K.LASER_X + 4.0, -4.0, 0.0)
FIBRE_JACKET = -300.0
TRACE_Y = BOARD_TOP + 1.0
FLEX_X = D.PIN_X1
TRACE_Z = -20.0
TRACE_Z_N = -34.0                          # OUT- runs beside OUT+ (a differential pair)
CAP_X = D.PIN_X1 + 70.0                    # the AC-coupling caps on the pair


def out_path():
    """OUT pin -> flex -> board trace -> into the transceiver's cage (absolute points)."""
    py, pz = D.PINS["OUT"]
    return [(D.HEAD_X1, py, pz), (D.PIN_X1, py, pz), (FLEX_X + 2.0, py, TRACE_Z),
            (FLEX_X + 2.0, TRACE_Y + 1.0, TRACE_Z), (CAGE_X0 - 30.0, TRACE_Y + 1.0, TRACE_Z),
            (CAGE_X0 - 18.0, BOARD_TOP + 16.0, TRACE_Z)]


def out_path_n():
    """OUT- : the complement, from the flex along the second trace."""
    return [(FLEX_X + 2.0, TRACE_Y + 1.0, TRACE_Z_N), (CAGE_X0 - 30.0, TRACE_Y + 1.0, TRACE_Z_N), (CAGE_X0 - 18.0, BOARD_TOP + 16.0, TRACE_Z_N)]


def fibre_pts():
    return D.curve_pts(LASER_WIN, (FIBRE_JACKET, 0.0, 0.0), (0.0, 25.0, 0.0), n=14)


def link(m, root):
    """The kit's stations, 10x, with the board; the detailed fibre, mount, flex and trace."""
    g = empty("link", root, P(LINK_AT[0], LINK_AT[1], 0.0))
    g.scale = (KS, KS, KS)
    K.board(m, g)
    K.trace(m, g)
    K.dsp(m, g)
    K.laser(m, g)
    K.module(m, g)
    K.cpo(m, g)
    D.wire("fibre_run", fibre_pts(), 4.0, m["cladding"], root)
    D.fibre(m, root)
    # The can's mount: a steel saddle from the board up to the can and the fibre ferrule.
    box("pd_mount", (-40.0, BOARD_TOP, -30.0), (30.0, -44.0, 0.0), m["dark_steel"], root)
    box("ferrule_mount", (-140.0, BOARD_TOP, -8.0), (-105.0, -9.0, 0.0), m["dark_steel"], root)
    # Flex from the pins down to the board, and the copper trace into the cage.
    flex = mat("pd_flex", (0.85, 0.50, 0.12), rough=0.5)
    box("flex_v", (FLEX_X, BOARD_TOP, -40.0), (FLEX_X + 3.0, 36.0, -12.0), flex, root)
    # copper traces printed on the flex, one per pin, and solder fillets where the pins land
    for nm, (py, pz) in D.PINS.items():
        box(f"flex_tr_{nm}", (FLEX_X + 3.0, BOARD_TOP, pz - 1.2), (FLEX_X + 3.4, py, pz + 1.2), m["copper"], root)
        tube(f"fillet_{nm}", (FLEX_X - 1.0, py, pz), (FLEX_X + 3.6, py, pz), 2.6, m["solder"], root, 12)
    # the receive pair on the board: OUT+ and OUT-, AC-coupling caps, a ground via fence
    for k, z in enumerate((TRACE_Z, TRACE_Z_N)):
        box(f"trace_rx{k}", (FLEX_X, BOARD_TOP, z - 3.0), (CAGE_X0 - 30.0, TRACE_Y, z + 3.0), m["copper"], root)
        cx = CAP_X
        box(f"accap{k}", (cx - 6.0, TRACE_Y, z - 4.0), (cx + 6.0, TRACE_Y + 5.0, z + 4.0), m["mlcc"], root)
        for e in (-1, 1):
            box(f"accap_end{k}{e}", (cx + e * 6.0 - 2.0, TRACE_Y - 0.1, z - 4.2), (cx + e * 6.0 + 2.0, TRACE_Y + 5.2, z + 4.2),
                m["solder"], root)
    box("trace_gap", (CAP_X - 2.0, BOARD_TOP - 0.2, TRACE_Z_N - 4.0), (CAP_X + 2.0, TRACE_Y + 0.2, TRACE_Z + 4.0),
        m["pcb_dark"], root)
    for k in range(9):
        x = FLEX_X + 30.0 + k * (CAGE_X0 - FLEX_X - 40.0) / 8
        for z in (TRACE_Z + 12.0, TRACE_Z_N - 12.0):
            tube(f"via_{k}_{z}", (x, BOARD_TOP - 0.5, z), (x, TRACE_Y + 0.3, z), 1.8, m["solder"], root, 10)
    # the cage's mouth: a dark opening and the host's card-edge connector inside it
    box("cage_mouth", (CAGE_X0 - 1.0, BOARD_TOP, -60.0), (CAGE_X0 + 1.0, BOARD_TOP + 30.0, 30.0), m["pcb_dark"], root)
    box("edge_conn", (CAGE_X0 - 32.0, BOARD_TOP, -55.0), (CAGE_X0 - 4.0, BOARD_TOP + 14.0, 5.0), m["ink"], root)
    for k in range(10):
        z = -50.0 + k * 5.5
        box(f"edge_pin{k}", (CAGE_X0 - 30.0, BOARD_TOP + 14.0, z), (CAGE_X0 - 6.0, BOARD_TOP + 15.0, z + 2.5), m["gold"], root)


def build(camera=None):
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = D.materials(K.materials())
    m["solder"] = mat("pd_solder", (0.78, 0.78, 0.80), metal=0.9, rough=0.25)
    m["mlcc"] = mat("pd_mlcc", (0.55, 0.42, 0.28), rough=0.5)
    m["pcb_dark"] = mat("pd_pcb_dark", (0.04, 0.05, 0.06), rough=0.8)
    link(m, root)
    whole = D.photodiode(m, root, cut_open=False)
    cut = D.photodiode(m, root, cut_open=True)
    D.pins(m, root)
    show(whole, [(0, F(2, 0)), (F(6, 0), F(BEATS, 0))])
    show(cut, [(F(2, 0), F(6, 0))])
    bg = D.beam(m, root)
    show(bg, [(F(2, 0), F(6, 0))])
    r = D.routes()
    fp = [front(p) for p in fibre_pts()] + [front((D.FIBRE_TIP, 0.0, 0.0))]

    # 0: the whole link; light runs down the fibre into the outlined receiver.
    D.halo(m, root, "pd_outline", (-56.0, -50.0, -50.0), (D.PIN_X1, 50.0, 50.0), beat(0), pad=6.0, r=3.0)
    run(root, "link_ph", fp, 8, 6.0, m["light"], 0, 0.0, 0.8, 70)

    # 1: light leaves the fibre and the ball lens catches it.
    D.photons(root, "in_ph", m, 1, 0.05, 0.8, n=8, life=40, to=(D.LENS_X, 0.0, 0.0))

    # 2: the can cut open; photons absorbed in the InGaAs free pairs.
    D.photons(root, "chip_ph", m, 2, 0.02, 0.2, n=4, life=55)
    D.pairs(root, "chip_p", m, 2, 0.2, 0.9, 7)

    # 3: current up the bond wire into the TIA; voltage out along the second wire and the OUT pin.
    D.pairs(root, "out_p", m, 3, 0.05, 0.6, 4)
    run(root, "tia_in", r["p_to_tia"], 8, 0.9, m["elec"], 3, 0.05, 0.6, 36)
    run(root, "tia_out", r["tia_to_out"], 6, 1.2, m["volt"], 3, 0.2, 0.7, 30)
    run(root, "out_pin", [(D.POST_X0, *D.PINS["OUT"]), (D.PIN_X1, *D.PINS["OUT"])], 6, 2.6, m["volt"],
        3, 0.3, 0.85, 40)

    # 4: a bright burst, then a dim one; thick then thin current down the path.
    D.photons(root, "bright_ph", m, 4, 0.02, 0.25, n=10, life=40, spread=8.0)
    D.photons(root, "dim_ph", m, 4, 0.5, 0.62, n=3, life=40, spread=3.0)
    run(root, "bright_i", out_path(), 14, 4.0, m["volt"], 4, 0.15, 0.4, 60)
    run(root, "dim_i", out_path(), 4, 1.8, m["volt"], 4, 0.62, 0.75, 60)
    run(root, "bright_n", out_path_n(), 10, 3.0, m["elec"], 4, 0.25, 0.45, 40)
    run(root, "dim_n", out_path_n(), 3, 1.5, m["elec"], 4, 0.68, 0.78, 40)

    # 5: two short light pulses; a current pulse follows each.
    for k, u in enumerate((0.05, 0.5)):
        D.photons(root, f"pulse_ph{k}", m, 5, u, u + 0.04, n=4, life=34, spread=4.0)
        run(root, f"pulse_i{k}", out_path(), 6, 3.0, m["volt"], 5, u + 0.18, u + 0.24, 60)
        run(root, f"pulse_n{k}", out_path_n(), 5, 2.4, m["elec"], 5, u + 0.26, u + 0.32, 40)

    # 6: pulled back; the current runs down the flex and the trace into the transceiver's cage.
    run(root, "to_mod", out_path(), 16, 4.0, m["volt"], 6, 0.0, 0.8, 70)
    run(root, "to_mod_n", out_path_n(), 14, 3.2, m["elec"], 6, 0.05, 0.85, 50)
    for k in range(6):
        blip(root, f"edge_glow{k}", [(CAGE_X0 - 30.0, BOARD_TOP + 16.5, -45.0 + k * 8.0),
                                     (CAGE_X0 - 6.0, BOARD_TOP + 16.5, -45.0 + k * 8.0)], 2.2, m["volt"],
             F(6, 0.2 + k * 0.1), 30)
    run(root, "link_ph6", fp, 6, 6.0, m["light"], 6, 0.0, 0.7, 70)

    labels = {
        0: [("PAM4 DSP", kit(K.DSP_X, 5.0, 12.0)), ("LASER", kit(K.LASER_X, 2.0, 0.0)),
            ("OPTICAL FIBER", fibre_pts()[7]), ("PHOTODIODE", (0.0, 56.0, 0.0)),
            ("TRANSCEIVER", kit(K.MOD_X, 13.0, 0.0)), ("CPO", kit(K.CPO_X, -1.5, 0.0))],
        1: [("FIBRE END", (D.FIBRE_TIP - 20.0, 10.0, 0.0)), ("BALL LENS", (D.LENS_X, D.LENS_R, 0.0)),
            ("TO-CAN", (0.0, D.CAN_R, 0.0))],
        2: [("p-InP", (D.P_X[0] + 1.2, 6.0, 0.0)), ("InGaAs ABSORBER", (19.0, -8.0, 0.0)),
            ("n-InP", ((D.N_X[0] + D.N_X[1]) / 2, 8.0, 0.0))],
        4: [("BRIGHT BURST", (-60.0, 8.0, 0.0)), ("THICK CURRENT", (100.0, *D.PINS["OUT"])),
            ("AC CAPS", (CAP_X, TRACE_Y + 5.0, TRACE_Z))],
        3: [("BOND WIRE", r["p_to_tia"][5]), ("TIA", ((D.TIA_LO[0] + D.TIA_HI[0]) / 2, D.TIA_HI[1], 0.0)),
            ("OUT PIN", (100.0, *D.PINS["OUT"]))],
        5: [("LIGHT PULSES", (-60.0, 6.0, 0.0)), ("CURRENT PULSES", (100.0, *D.PINS["OUT"]))],
        6: [("OUT+ / OUT- PAIR", ((FLEX_X + CAGE_X0) / 2, TRACE_Y, TRACE_Z)), ("AC CAPS", (CAP_X, TRACE_Y + 5.0, TRACE_Z)),
            ("CAGE CONNECTOR", (CAGE_X0 - 18.0, BOARD_TOP + 15.0, -25.0)), ("TRANSCEIVER", kit(K.MOD_X, 13.0, 0.0)),
            ("PHOTODIODE", (0.0, D.CAN_R, 0.0))],
    }
    for i, items in labels.items():
        for text, at in items:
            label(text, at, root, beat(i))

    poses = [
        frame((-1560.0, -60.0, -300.0), (1500.0, 160.0, 300.0), yaw=0.2, pitch=0.42, pad=1.0),
        frame((-170.0, -50.0, -20.0), (44.0, 50.0, 50.0), yaw=-0.2, pitch=0.22),
        frame(*D_CHIP, yaw=-0.2, pitch=0.12, pad=1.1),
        frame((5.0, -30.0, -35.0), (130.0, 42.0, 0.0), yaw=-0.5, pitch=0.25, pad=1.1),
        frame((-110.0, -55.0, -50.0), (CAP_X + 20.0, 50.0, 0.0), yaw=0.15, pitch=0.3, pad=1.0),
        frame((-110.0, -50.0, -50.0), (135.0, 50.0, 0.0), yaw=0.15, pitch=0.25, pad=1.0),
        frame((-60.0, -60.0, -70.0), (CAGE_X0 + 160.0, 80.0, 40.0), yaw=0.35, pitch=0.5, pad=1.0),
    ]
    (camera or D.glide_camera)(root, poses)
    return root


D_CHIP = ((8.0, -22.0, -20.0), (35.0, 22.0, 0.0))


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
