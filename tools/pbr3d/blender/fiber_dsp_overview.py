"""The PAM4 DSP node overview, in the SAND template: a pluggable module with its shell cut away, the
flip-chip DSP package at its heart, and a scope on the bench probing one host lane.

Run from the repo root (on the worker, or locally):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_dsp_overview.py

Writes blender/fiber_dsp_overview.blend and assets/fiber_dsp_overview.glb. One beat is 8 s.
The parts come from fiber_dsp_detail.py and the module layout from fiber_dsp_sections.module; this
page no longer builds from the shared fiber_kit stations. Signals ride arched, segmented wires as
glowing beads (detail.wire + detail.run): the driver's bond wires, the laser's bond wire, the probe.

Beats (match the seven beats in diagrams_nodes/fiber/dsp/overview.rs):
  0 context   the module cut open, the DSP lit: the first station; laser, fibre and photodiode after it
  1 bits in   blurred PAM4 symbols ride the 8 host lanes in from the edge connector
  2 inside    the finned lid lifts off; the die face down on its bumps, paste on its back
  3 PAM4      a scope probes a host lane: one symbol at a time between four levels, two bits each
  4 clean     blurred symbols in, the die lights, clean symbols out down the package and to the driver
  5 heat      the die glows; heat rises off the fins
  6 next      clean symbols ride the driver's bond wires and the laser's wire; light goes down the fibre
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, box, key, label, show, tube  # noqa: E402
from sand_zooms import start, finish, stream_of  # noqa: E402
from pbr_kit import empty  # noqa: E402
import fiber_dsp_detail as D  # noqa: E402
from fiber_dsp_detail import BOARD_Y1, DIE, DIE_Y0, DIE_Y1, FIN_Y1, TIM_Y1, frame, glide, lbox  # noqa: E402
import fiber_dsp_sections as S  # noqa: E402
from fiber_dsp_sections import (  # noqa: E402
    DRV_X0, DRV_X1, FIBRE_X1, LASER_HX, LEVELS, M_X0, M_X1, OUT_BUMP_Z, OUT_Z, SEQ, SYM_W, WAVE_X0, group, span,
)

PAGE = "fiber_dsp"
NAME = "overview"
BEATS = 7
SCALE = 4.0  # the renderer's near plane is 40 mm; parts are a few mm, so the scene is drawn 4x
LID_UP = 9.0
SCOPE_AT = (-87.0, -3.4, 0.0)  # the scope's offset: its feet stand on the bench, left of the module
BENCH_TOP = -10.9
LANES = [-9.1 + 2.6 * k for k in range(8)]
PROBE_LANE = LANES[5]


def beat(i):
    return span(i, i + 1)


def world(p, at=SCOPE_AT):
    return tuple(p[i] + at[i] for i in range(3))


def out_chain():
    """The transmit path as one polyline: up from a bump, down the substrate and ball, along the board,
    over the driver's input bond wire, die, output bond wire, along to the laser's pin, up its pin,
    over the laser's bond wire onto the chip."""
    y = BOARD_Y1 + 0.4
    wires = D.driver_wires(DRV_X0, DRV_X1, OUT_Z)
    pts = [(0.6, -3.2, OUT_BUMP_Z), (0.6, -4.1, OUT_BUMP_Z), (0.6, -4.1, OUT_Z), (0.6, y, OUT_Z),
           (DRV_X0 - 0.3, y, OUT_Z)]
    pts += wires[0] + wires[2]
    pts += [(DRV_X1 + 0.3, y, OUT_Z), (LASER_HX - 2.5, y, OUT_Z), (LASER_HX - 2.5, -4.1, OUT_Z), (LASER_HX, -4.1, OUT_Z)]
    pts += D.laser_wire(LASER_HX, OUT_Z)
    return pts


def lane(k):
    y = BOARD_Y1 + 0.4
    return [(M_X0 + 3, y, LANES[k]), (-16.0, y, LANES[k])]


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = D.materials()
    box("bench", (M_X0 - 60, BENCH_TOP - 1.0, -30), (M_X1 + 8, BENCH_TOP, 24), m["screen"], root)
    G = S.module(m, root, arched=True)
    D.wire("laser_bond", D.laser_wire(LASER_HX, OUT_Z), 0.06, m["gold"], root)
    y = BOARD_Y1

    # 0: the DSP lit, a gold frame round its package on the board; slow blurred symbols on the lanes
    hl = group("dsp_frame", root, beat(0))
    for k, (a, b) in enumerate((((-16.5, -14.5), (16.5, -13.8)), ((-16.5, 13.8), (16.5, 14.5)),
                                ((-16.5, -14.5), (-15.8, 14.5)), ((15.8, -14.5), (16.5, 14.5)))):
        box(f"dsp_frame{k}", (a[0], y, a[1]), (b[0], y + 0.3, b[1]), m["hl"], hl)
    for k in (1, 4, 6):
        D.run(root, f"idle{k}", lane(k), 3, 0.45, m["noise"], 0, 0.05 + 0.1 * k, 0.6 + 0.04 * k, 110)

    # 1: blurred symbols ride all 8 host lanes in
    for k in range(8):
        D.run(root, f"in{k}", lane(k), 3, 0.5, m["noise"], 1, 0.03 + 0.03 * k, 0.6 + 0.03 * k, 90)
    lit = group("lanes_lit", root, beat(1))
    for k, z in enumerate(LANES):
        box(f"lane_lit{k}", (M_X0 + 6, y + 0.18, z - 0.25), (-15.5, y + 0.24, z + 0.25), m["fuzz"], lit)

    # 2: the lid lifts off; it stays up through beat 3 and drops back early in beat 4
    lid = G["lid"]
    key(lid, F(2, 0.08), "location", P(0, 0, 0))
    key(lid, F(2, 0.40), "location", P(0, LID_UP, 0))
    key(lid, F(4, 0.02), "location", P(0, LID_UP, 0))
    key(lid, F(4, 0.25), "location", P(0, 0, 0))

    # 2 (cont.): with the lid up, signals still climb the bumps into the die and heat leaves its back
    for k, x in enumerate((1.8, 4.2, 6.6)):
        D.run(root, f"bump2_{k}", [(x, -3.9, 0.35), (x, DIE_Y0 + 0.1, 0.35)], 3, 0.22, m["path"], 2,
              0.35 + 0.08 * k, 0.85, 25)
    for k, x in enumerate((-5.0, -1.0, 3.0, 7.0)):
        D.run(root, f"tim2_{k}", [(x, TIM_Y1, 0.4), (x, TIM_Y1 + 2.0, 0.4)], 3, 0.35, m["heat"], 2,
              0.45 + 0.04 * k, 0.9, 30)

    # 3: a scope on the bench, probing host lane 5 through an arched probe lead
    sg = empty("scope_at", root)
    sg.location = P(*SCOPE_AT)
    S.scope(m, sg, S.SCOPE_X0, S.SCOPE_X1)
    for name, yl in LEVELS.items():
        tube(f"rung_{name}", (S.SCOPE_X0 + 0.5, yl, -0.9), (S.SCOPE_X1 - 0.5, yl, -0.9), 0.22, m["rung"], sg, 10)
    path = S.waveform(m, empty("wave", sg), LEVELS, SEQ, 3, "pam")
    dg = group("dot_g", sg, beat(3))
    dot = ball("dot", path[0][1], 0.8, m["hl"], dg, 16)
    for u, p in path:
        key(dot, F(3, u), "location", P(*p), linear=True)
        key(dot, F(3, u + 0.06), "location", P(*p), linear=True)
    probe = D.arch(world((S.SCOPE_X1 - 2.0, -4.0, -0.4)), (-42.0, y + 0.3, PROBE_LANE), 7.0, n=14)
    D.wire("probe", probe, 0.25, m["dark_steel"], root)
    ball("probe_tip", (-42.0, y + 0.3, PROBE_LANE), 0.45, m["gold"], root, 12)
    D.run(root, "probe_beads", probe[::-1], 5, 0.4, m["path"], 3, 0.02, 0.75, 60)

    # 4: blurred in, the die lights, clean out down the package and over the driver's bond wires
    for k in range(0, 8, 2):
        D.run(root, f"in4_{k}", lane(k), 2, 0.5, m["noise"], 4, 0.02 + 0.04 * k, 0.4 + 0.04 * k, 80)
    S.die_glow(m, group("die_on", G["die"], [(F(4, 0.25), F(5, 0)), (F(6, 0), F(7, 0))]))
    chain = out_chain()
    D.run(root, "clean4", chain[:12], 5, 0.4, m["path"], 4, 0.35, 0.8, 50)
    S.out_lit(m, group("out_on", root, [(F(4, 0.3), F(5, 0)), (F(6, 0), F(7, 0))]), trace=True)

    # 5: the die hot; heat climbs and rises off the lid's fins and the module's roof fins
    hot = group("hot", G["die"], beat(5))
    dx0, dz0, dx1, dz1 = DIE
    o = 0.05
    lbox("hot_die", (dx0 - o, DIE_Y0 - o, dz0 - o), (dx1 + o, DIE_Y1 + o, dz1 + o), m["heat"], hot, None, o)
    lbox("hot_tim", (dx0 + 0.15, DIE_Y1, dz0 + 0.15), (dx1 - 0.15, TIM_Y1 + o, dz1 - 0.15), m["heat"], hot, None, o)
    for k, (dx, dz) in enumerate(((-9.0, -6.6), (-4.0, -2.2), (3.0, -4.4), (8.0, -8.8), (-6.0, 4.4), (-2.0, 8.8))):
        stream_of(root, f"puff{k}", 4, (dx, FIN_Y1 + 0.3, dz), [(0, 0, 0), (dx * 0.15, 9.0, 0)], 0.8, m["heat"], 5,
                  0.03 + 0.05 * k, 0.65 + 0.05 * k, 70)
    # the heat's path on the cut face: die -> paste -> lid plate -> fins
    for k, x in enumerate((-6.0, -2.0, 2.0, 6.0)):
        D.run(root, f"climb5_{k}", [(x, DIE_Y0 + 0.2, 0.3), (x, D.LID_Y1, 0.3), (x, FIN_Y1 + 0.5, 0.3)], 4, 0.4,
              m["heat"], 5, 0.02 + 0.04 * k, 0.7 + 0.04 * k, 45)
    # fan air sweeping through the fin gaps
    for k, z in enumerate((-7.7, -3.3, 1.1, 5.5, 9.9)):
        D.run(root, f"air5_{k}", [(18.0, FIN_Y1 - 1.2, z), (-18.0, FIN_Y1 - 1.2, z)], 5, 0.4, m["air"], 5,
              0.05 + 0.04 * k, 0.75 + 0.04 * k, 50)

    # 6: clean symbols ride the whole chain to the laser chip; it lights; light runs down the fibre
    D.run(root, "clean6", chain, 6, 0.4, m["path"], 6, 0.0, 0.6, 110)
    S.laser_on(m, root, [(F(6, 0.35), F(7, 0))])
    S.fibre_pulses(m, root, 6)

    tags = {
        0: [("PAM4 DSP: the first station", (-6, FIN_Y1, 6)),
            ("edge connector to the host", (M_X0 + 3, y, 9.1)),
            ("laser: next", (LASER_HX + 3, D.AXIS_Y + 2.5, OUT_Z)),
            ("photodiode", (LASER_HX + 3, D.AXIS_Y + 2.5, S.RX_Z))],
        1: [("8 host lanes in", (-30, y + 0.3, LANES[3])),
            ("edge connector", (M_X0 + 3, y, LANES[7])),
            ("blurred PAM4 symbols", (-24, y + 0.6, LANES[6]))],
        2: [("lid + fins lifted", (8, LID_UP + 1, 0)),
            ("die, face down", (4, -2.2, 0)),
            ("thermal paste", (6, TIM_Y1 - 0.1, 0)),
            ("C4 bumps", (3.0, -3.5, 0)),
            ("heat leaves the die's back", (-5.0, TIM_Y1 + 1.5, 0.4))],
        3: [("4 levels: 2 bits a symbol", world((WAVE_X0 + SYM_W * 0.5, LEVELS["10"], -0.6))),
            ("one symbol at a time", world((WAVE_X0 + SYM_W * 4.5, LEVELS["00"], -0.6))),
            ("probe on a host lane", (-42.0, y + 0.3, PROBE_LANE))],
        4: [("blurred symbols in", (-30, y + 0.6, LANES[4])),
            ("DSP: equalise + FEC", (4, -2.95, 0)),
            ("clean symbols out", (DRV_X0 - 6, y + 0.4, OUT_Z))],
        5: [("die: most of the power", (4, -2.3, 0)),
            ("heat off the fins", (0, FIN_Y1 + 6, 0)),
            ("die -> paste -> lid -> fins", (-2.0, D.LID_Y1, 0.3)),
            ("fan air through the fins", (-14.0, FIN_Y1 - 1.2, 9.9))],
        6: [("driver's bond wires", ((DRV_X0 + DRV_X1) / 2, -6.0, OUT_Z)),
            ("next: the laser", (LASER_HX + 3, D.AXIS_Y + 0.2, OUT_Z)),
            ("light into the fibre", (54, D.AXIS_Y, OUT_Z))],
    }
    for i, items in tags.items():
        for text, at in items:
            label(text, at, root, beat(i))

    sx0, sx1 = world((S.SCOPE_X0 - 2, 0, 0))[0], world((S.SCOPE_X1 + 2, 0, 0))[0]
    poses = [
        frame((M_X0, -11, -21), (M_X1, 12, 16), 0.45, 0.55, fill=0.98),
        frame((M_X0 - 2, -10, -12), (10, 3, 12), 0.40, 0.55, fill=0.95),
        frame((-12, -8, -8), (14, FIN_Y1 + LID_UP, 12), 0.60, 0.30, fill=0.97),
        frame((sx0, BENCH_TOP, -2), (-40, 12, 6), 0.30, 0.15, fill=0.97),
        frame((M_X0 - 2, -10, -12), (DRV_X1 + 2, 3, 12), 0.40, 0.50, fill=0.95),
        frame((-15, -10, -13), (15, FIN_Y1 + 9, 13), 0.55, 0.40, fill=0.95),
        frame((DRV_X0 - 3, -8, 4), (LASER_HX + 20, -1, 11), 0.30, 0.35, fill=0.97),
    ]
    del sx1
    glide(root, poses)
    root.scale = (SCALE, SCALE, SCALE)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
