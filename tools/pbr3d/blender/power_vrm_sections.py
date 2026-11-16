"""The VRM page's nine numbered sections, in the picture-and-panel template (docs/diagram-pages.md).
Section N illustrates heading N of tui/src/screens/diagrams_pages/PWR_VRM.txt (the tenth, Sources,
is text only). Three beats each, one beat is 8 s.

Run one section per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/power_vrm_sections.py -- <n>

Writes blender/power_vrm_section_<n>.blend and assets/power_vrm_section_<n>.glb. The board, package,
phases, brick and vertical modules come from power_vrm_detail.py; close-ups (one phase drawn three
times larger, a scope, two copper bars) are built above the board at BY.

  1 what happens   50 V into the brick; 12 V through the phases; over 1,000 A into the package
  2 the parts      the board's parts; one phase cut open; core voltage, vertical power, I2R
  3 in order       busbar and brick; controller and stages; inductor, board, package, GPU
  4 why so much    1,000-1,200 W; at 0.8 V that is 1,250-1,500 A; split across 16 phases
  5 phases         one phase's inductor storing energy; staggered ripples cancel; capacitors
  6 I2R loss       twice the current, four times the heat; 225 W in 0.1 milliohm; shorter path
  7 vertical       beside the GPU; modules under it; seen from below
  8 who makes it   makers tagged on controller, stages, brick and vertical modules
  9 chokepoints    rising current; crowded board; regulator heat under a cold plate
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key, tube  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import frame, camera_path, run, rise, bx, empty, polyline  # noqa: E402
import power_vrm_overview as OV  # noqa: E402

PAGE = "power_vrm"
BEATS = 3
BY = 300.0  # close-ups are built this high above the board


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def after(b, u):
    return [(F(b, u), F(BEATS, 0))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def board(m, root, **k):
    return D.scene(m, root, **k)


def bench(m, root, beats, name="bp"):
    """One phase, three times larger, centred on x = 0 at height BY, shown only in `beats`."""
    s = 3.0
    g = empty(f"{name}_grp", root)
    pts, paths = D.bench_phase(m, g, (-26.0 * s, BY, 0.0), s, name)
    D.present(g, [iv for b in beats for iv in beat(b)])
    return pts, paths


# shared views
V_BRICK = frame((-262.0, 8.0, -20.0), 120.0, 0.25, 0.30)
V_LEFT = frame((-160.0, 0.0, -80.0), 200.0, 0.22, 0.85, pad=1.0)
V_FRONT = frame((-60.0, 0.0, 0.0), 150.0, 0.18, 0.22)
V_PKG = frame((0.0, 6.0, -8.0), 150.0, 0.15, 0.30)
V_TOP = frame((0.0, 0.0, -105.0), 330.0, 0.0, 1.0, pad=1.0)
V_VERT = frame((0.0, -10.0, -6.0), 140.0, 0.35, 0.10)
V_BENCH = frame((-24.0, BY + 18.0, -6.0), 170.0, 0.20, 0.24, pad=1.0)


# ---- 1 what happens ---------------------------------------------------------------------------------


def sec1(m, root):
    s = board(m, root)
    br, bp = s["brick"], s["bpaths"]
    run(root, "s1_v50", bp["p50"], 7, 1.6, m["v50"], 0, 0.0, 0.5, 90)
    run(root, "s1_v12", bp["out12"], 6, 1.4, m["v12"], 0, 0.35, 0.85, 50)
    for k in range(3):
        run(root, f"s1_p12_{k}", D.p12_path(k), 5, 1.3, m["v12"], 1, 0.0 + 0.04 * k, 0.8, 50)
    OV.interleave(m, root, s, [1], rounds=2, sides=(-1,))
    for k in range(1, 8):
        run(root, f"s1_pour{k}", D.pour_path(-1, k), 2, 1.2, m["amp"], 1, 0.1 + 0.03 * k, 0.85, 40)
    OV.currents(m, root, [2], n_front=10)
    show(s["die_glow"], after(2, 0.35))
    tags(root, [
        [("~50 V DC from the busbar", (D.BX0 - 30.0, 10.0, D.BUS_Z[0])), ("INTERMEDIATE BUS: 50 V > 12 V", br["xf"]), ("12 V out", br["tab"])],
        [("12 V plane", (-195.0, D.Y_P12[1], -40.0)), ("MULTIPHASE: phases in turn", s["ph"]["st"][(-1, 3)]["top"]),
         ("INDUCTORS: ~0.8 V out", s["ph"]["ind"][(-1, 5)]["top"])],
        [("CORE VOLTAGE ~0.8 V", s["pkg"]["top"]), ("well over 1,000 A", (-66.0, 1.0, 0.0)), ("up into the package", s["pkg"]["bga"])],
    ])
    camera_path(root, [frame((-262.0, 8.0, -30.0), 150.0, 0.30, 0.42), V_LEFT, frame((-40.0, 2.0, -20.0), 190.0, 0.22, 0.40)])


# ---- 2 the parts --------------------------------------------------------------------------------------


def sec2(m, root):
    s = board(m, root)
    bpt, paths = bench(m, root, [1])
    show(bpt["field"], beat(1))
    D.blink(bpt["sw"], 1, range(8), 8, 0.45)
    run(root, "s2_in", paths["p12"], 5, 2.2, m["v12"], 1, 0.0, 0.85, 50)
    run(root, "s2_sw", paths["sw"], 6, 2.2, m["amp"], 1, 0.05, 0.9, 70)
    D.present(s["vert"], beat(2))
    show(s["plane_hot"], beat(2))
    show(s["die_glow"], beat(2))
    for x in (-38.5, 14.0):
        run(root, f"s2_v{x}", D.vert_path(x), 4, 1.3, m["amp"], 2, 0.1, 0.85, 50)
    st = bpt["st"]
    tags(root, [
        [("INTERMEDIATE BUS brick", s["brick"]["brick"]), ("VOLTAGE REGULATOR controller", s["ctrl"]["ctrl"]),
         ("MULTIPHASE: 8 phases a side", s["ph"]["ind"][(1, 3)]["top"]), ("GPU", s["pkg"]["top"])],
        [("POWER STAGE: FETs + driver", st["top"]), ("high-side FET", st["hs"]), ("low-side FET + clip", st["clip"]),
         ("INDUCTOR: ferrite + copper", bpt["ind"]["core"])],
        [("CORE VOLTAGE ~0.8 V", s["pkg"]["die_face"]), ("I2R LOSS: hot copper", (-90.0, D.P08_Y, 0.0)),
         ("VERTICAL POWER: under the GPU", s["vpts"]["vm"])],
    ])
    camera_path(root, [
        frame((-40.0, 0.0, -100.0), 440.0, 0.22, 0.65, pad=1.0),
        V_BENCH,
        frame((-20.0, -8.0, -4.0), 190.0, 0.30, 0.14),
    ])


# ---- 3 down to the chip, in order ------------------------------------------------------------------


def sec3(m, root):
    s = board(m, root)
    br, bp = s["brick"], s["bpaths"]
    run(root, "s3_v50", bp["p50"], 7, 1.6, m["v50"], 0, 0.0, 0.5, 90)
    run(root, "s3_v12", bp["out12"], 6, 1.4, m["v12"], 0, 0.35, 0.85, 50)
    for k in range(3):
        run(root, f"s3_p12_{k}", D.p12_path(k), 4, 1.3, m["v12"], 1, 0.0 + 0.04 * k, 0.8, 50)
    OV.interleave(m, root, s, [1], rounds=2, sides=(-1,))
    fp = D.front_path(-1)
    run(root, "s3_sw", fp[2:8], 6, 1.3, m["amp"], 2, 0.0, 0.5, 50)
    run(root, "s3_out", fp[6:], 8, 1.5, m["amp"], 2, 0.2, 0.85, 80)
    show(s["die_glow"], after(2, 0.5))
    tags(root, [
        [("1 ~50 V DC arrives", (D.BX0 - 30.0, 10.0, D.BUS_Z[0])), ("2 bus converter makes 12 V", br["xf"])],
        [("3 controller: when to switch", s["ctrl"]["ctrl"]), ("PWM traces", (-D.TR_X - 4.0, 0.4, -120.0)),
         ("4 POWER STAGE chops 12 V", s["ph"]["st"][(-1, 2)]["top"])],
        [("5 INDUCTOR: ~0.8 V current", (-94.0, D.IN_H, 0.0)), ("6 through the board", (-50.0, D.P08_Y, 0.0)),
         ("and package into the GPU", s["pkg"]["die_face"])],
    ])
    camera_path(root, [frame((-262.0, 8.0, -30.0), 150.0, 0.30, 0.42), V_LEFT, V_FRONT])


# ---- 4 why so much current ----------------------------------------------------------------------------


def sec4(m, root):
    s = board(m, root)
    show(s["die_glow"], span(0, 0.15, 2, 0.0) + after(2, 0.4))
    rise(root, "s4_heat", (0.0, D.DIE_Y[1] + 1.0, -16.0), 8, 1.0, m["heat"], 0, 0.05, 0.85, 36.0, 70, (14.0, 10.0))
    for x in (-40.0, -24.0, -8.0, 8.0, 24.0, 40.0):
        run(root, f"s4_v{x}", [(x, D.P08_Y, 1.0), (x, 2.0, 2.2), (x, 13.0, 1.0), (x, 17.5, 1.0), (x * 0.6, 20.5, 1.5)],
            5, 1.1, m["amp"], 1, 0.0, 0.85, 40)
    OV.currents(m, root, [1], n_front=10, big=1.5)
    OV.interleave(m, root, s, [2], rounds=2)
    tags(root, [
        [("Blackwell GPU", s["pkg"]["top"]), ("1,000-1,200 W", (20.0, D.DIE_Y[1], -20.0))],
        [("~0.8 V CORE VOLTAGE", s["pkg"]["die_face"]), ("= 1,250-1,500 A", (-40.0, 2.0, 0.0)), ("P = V x I", (40.0, 13.0, 0.0))],
        [("split across 16 phases", s["ph"]["ind"][(1, 3)]["top"]), ("Infineon 2019: first 1,000+ A", s["ctrl"]["ctrl"])],
    ])
    camera_path(root, [frame((0.0, 14.0, -24.0), 120.0, 0.20, 0.60), V_PKG, V_TOP])


# ---- 5 phases, inductors and capacitors --------------------------------------------------------------

SC5 = (0.0, BY + 600.0, 0.0)  # the scope, well clear of the bench


def tri(u):
    """A triangle wave, 0..1, period 1."""
    u = u % 1.0
    return 2 * u if u < 0.5 else 2 - 2 * u


def sec5(m, root):
    s = board(m, root)
    bpt, paths = bench(m, root, [0])
    # beat 0: the inductor stores energy while the stage is on, gives it back while it is off
    D.blink(bpt["sw"], 0, range(8), 8, 0.5)
    D.blink(bpt["field"], 0, range(8), 8, 0.5, u0=0.03)
    run(root, "s5_sw", paths["sw"], 8, 2.2, m["amp"], 0, 0.0, 0.85, 70)
    run(root, "s5_out", paths["out"], 6, 2.2, m["amp"], 0, 0.2, 0.9, 50)
    # beat 1: four phases' ripple, staggered, and their sum
    cx, cy, cz = SC5
    W, H = 200.0, 120.0
    scg = empty("s5_scope", root)
    D.present(scg, beat(1))
    D.scope(m, scg, SC5, W, H, "s5sc")
    x0, x1 = cx - W / 2 + 6.0, cx + W / 2 - 6.0
    cols = ("pwm", "v12", "field", "v50")
    lanes = []
    for k in range(4):
        base = cy + H / 2 - 16.0 - 18.0 * k
        pts = [(x0 + (x1 - x0) * i / 64, base + 9.0 * tri(4 * i / 64 + k / 4.0), cz + 0.6) for i in range(65)]
        polyline(f"s5_ph{k}", pts, 0.55, m[cols[k]], scg)
        lanes.append(pts)
    base = cy - H / 2 + 12.0
    tot = [(x0 + (x1 - x0) * i / 64, base + 9.0 * (sum(tri(4 * i / 64 + k / 4.0) for k in range(4)) - 2.0), cz + 0.6) for i in range(65)]
    polyline("s5_sum", tot, 0.75, m["amp"], scg)
    for k, pts in enumerate(lanes):
        run(root, f"s5_dot{k}", pts, 1, 1.6, m["sw"], 1, 0.05, 0.05, 160)
    run(root, "s5_dsum", tot, 1, 2.0, m["sw"], 1, 0.05, 0.05, 160)
    # beat 2: capacitors next to the GPU answer a load step first
    flash = empty("s5_flash", root)
    for side in (-1, 1):
        for k in range(4):
            zc = D.PHASE_Z[k]
            for dz in ((-5.0,) if k == 0 else (-5.0, 5.0)):
                c = (D.sx(side, (D.CAP_X[0] + D.CAP_X[1]) / 2), 3.0, zc + dz)
                bx(f"s5_fl{side}{k}{dz}", (c[0] - 2.5, 3.0, c[2] - 1.8), (c[0] + 2.5, 4.0, c[2] + 1.8), m["sw"], flash)
            run(root, f"s5_cap{side}{k}", [(D.sx(side, -74.0), 3.5, min(zc, -1.5)), (D.sx(side, -62.0), 1.0, min(zc, -1.5))],
                3, 1.2, m["amp"], 2, 0.42, 0.62, 30)
    show(flash, span(2, 0.4, 2, 0.7))
    show(s["die_glow"], span(2, 0.38, 3, 0.0))
    OV.currents(m, root, [2], n_front=6, u0=0.5, u1=0.9)
    tags(root, [
        [("tens of amps per phase", bpt["ind"]["strap"]), ("INDUCTOR stores energy", bpt["ind"]["core"]),
         ("stage on, stage off", bpt["st"]["top"])],
        [("each phase's ripple", (x0 + 30.0, cy + H / 2 - 7.0, cz + 0.6)), ("staggered in time", (cx + 40.0, cy + H / 2 - 34.0 - 18.0, cz + 0.6)),
         ("together: ripples cancel", (cx, base + 2.0, cz + 0.8))],
        [("capacitors by the GPU", (-74.0, 3.0, -5.0)), ("load jumps: caps answer first", (D.CAP_X[1], 3.0, -29.0)),
         ("faster than the regulator", s["pkg"]["top"])],
    ])
    camera_path(root, [V_BENCH, frame((cx, cy, cz), W + 20.0, 0.0, 0.05, pad=1.05), frame((-40.0, 2.0, -20.0), 170.0, 0.22, 0.45)])


# ---- 6 I2R loss ---------------------------------------------------------------------------------------


def sec6(m, root):
    s = board(m, root)
    # beat 0: two copper bars, one carrying twice the current: four times the heat
    L = 160.0
    bars = empty("s6_bars", root)
    D.present(bars, beat(0))
    for j, (y, n, hot) in enumerate(((BY + 30.0, 6, 1), (BY - 10.0, 12, 4))):
        bx(f"s6_bar{j}", (-L / 2, y, -14.0), (L / 2, y + 10.0, 0.0), m["copper"], bars)
        bx(f"s6_pad{j}a", (-L / 2 - 12.0, y - 3.0, -16.0), (-L / 2, y + 13.0, 2.0), m["dark"], bars)
        bx(f"s6_pad{j}b", (L / 2, y - 3.0, -16.0), (L / 2 + 12.0, y + 13.0, 2.0), m["dark"], bars)
        g = empty(f"s6_hot{j}", root)
        for h in range(hot):
            xa = -L / 2 + 10.0 + (L - 20.0) * h / 4
            bx(f"s6_hot{j}_{h}", (xa, y + 10.0, -12.0), (xa + (L - 20.0) / 4 - 4.0, y + 11.2, -2.0), m["hot"], g)
        show(g, span(0, 0.25, 1, 0.0))
        run(root, f"s6_i{j}", [(-L / 2 - 6.0, y + 5.0, 1.5), (L / 2 + 6.0, y + 5.0, 1.5)], n, 2.0, m["amp"], 0, 0.0, 0.85, 60)
        rise(root, f"s6_r{j}", (0.0, y + 11.5, -7.0), 2 * hot, 1.1, m["heat"], 0, 0.3, 0.9, 20.0, 50, (60.0, 4.0))
    # beat 1: the 0.8 V plane at 1,500 A
    show(s["plane_hot"], beat(1))
    OV.currents(m, root, [1, 2], n_front=8)
    rise(root, "s6_plane", (-40.0, 0.5, 2.0), 6, 1.0, m["heat"], 1, 0.05, 0.85, 26.0, 60, (40.0, 0.0))
    # beat 2: a ruler from the inductor to the die: the distance that costs power
    ruler = empty("s6_ruler", root)
    y = 32.0
    bx("s6_rule", (-82.0, y, 0.5), (-12.0, y + 1.2, 1.7), m["v50"], ruler)
    for i in range(8):
        x = -82.0 + 10.0 * i
        bx(f"s6_tick{i}", (x - 0.4, y - 3.0, 0.5), (x + 0.4, y + 1.2, 1.7), m["v50"], ruler)
    show(ruler, beat(2))
    tags(root, [
        [("1x current: 1x heat", (L / 2 - 20.0, BY + 40.0, 0.0)), ("2x current: 4x heat", (L / 2 - 20.0, BY, 0.0)),
         ("loss = I x I x R", (-L / 2 + 20.0, BY + 40.0, 0.0))],
        [("0.8 V plane at ~1,500 A", (-80.0, D.P08_Y, 0.0)), ("0.1 mOhm here = 225 W", (10.0, D.P08_Y, 0.0))],
        [("every mm costs watts and volts", (-47.0, y + 1.2, 1.0)), ("regulator", (-94.0, D.IN_H, 0.0)), ("GPU", s["pkg"]["die_face"])],
    ])
    camera_path(root, [frame((0.0, BY + 18.0, -4.0), 210.0, 0.15, 0.25, pad=1.0), frame((-30.0, -6.0, 0.0), 150.0, 0.15, 0.16), V_FRONT])


# ---- 7 vertical power -----------------------------------------------------------------------------


def sec7(m, root):
    s = board(m, root)
    OV.currents(m, root, [0], n_front=10)
    D.present(s["ph"]["group"], beat(0))
    D.present(s["vert"], span(1, 0.0, 3, 0.0))
    lift = s["vpts"]["lift"]
    key(lift, F(1, 0.0), "location", P(0.0, -60.0, 0.0), linear=True)
    key(lift, F(1, 0.1), "location", P(0.0, -60.0, 0.0), linear=True)
    key(lift, F(1, 0.55), "location", P(0.0, 0.0, 0.0), linear=True)
    for x in (-38.5, -14.0, 14.0, 38.5):
        run(root, f"s7_v{x}", D.vert_path(x), 5, 1.3, m["amp"], [1, 2], 0.25, 0.9, 50)
    show(s["die_glow"], after(1, 0.5))
    tags(root, [
        [("today: beside the GPU", (-94.0, D.IN_H, 0.0)), ("current crosses the board", (-50.0, D.P08_Y, 0.0))],
        [("VERTICAL POWER: on the back", s["vpts"]["vm"]), ("straight up through the board", (-14.0, -8.0, 0.0))],
        [("Crescendo: 16 stacked regulators", (0.0, D.VM_Y[0], -26.0)), ("~1,000 A at 0.75 V", (38.0, D.VM_Y[0], -12.0)),
         ("Infineon modules: 2026", (-38.0, D.VM_Y[0], -40.0))],
    ])
    camera_path(root, [V_FRONT, V_VERT, frame((0.0, -30.0, -26.0), 130.0, 0.30, -0.55)])


# ---- 8 who makes it -----------------------------------------------------------------------------------


def sec8(m, root):
    s = board(m, root)
    OV.interleave(m, root, s, [0], rounds=2)
    run(root, "s8_v50", s["bpaths"]["p50"], 6, 1.6, m["v50"], 1, 0.0, 0.5, 90)
    run(root, "s8_v12", s["bpaths"]["out12"], 5, 1.4, m["v12"], 1, 0.3, 0.85, 50)
    D.present(s["vert"], beat(2))
    for x in (-38.5, -14.0, 14.0, 38.5):
        run(root, f"s8_v{x}", D.vert_path(x), 4, 1.3, m["amp"], 2, 0.1, 0.85, 50)
    tags(root, [
        [("controllers: Infineon, Renesas", s["ctrl"]["ctrl"]), ("also MPS (MPWR), TI", (D.CTRL[1], 0.0, D.CTRL[3])),
         ("power stages: same makers", s["ph"]["st"][(-1, 5)]["top"])],
        [("power modules: Vicor (VICR)", s["brick"]["brick"]), ("and Infineon, MPS, TI, Renesas", s["brick"]["xf"])],
        [("vertical modules: Delta, others", s["vpts"]["vm"]), ("Infineon: vertical, 2026", (38.0, D.VM_Y[0], 0.0)),
         ("shares: not sourced here", (0.0, D.DIE_Y[1], -10.0))],
    ])
    camera_path(root, [frame((-90.0, 0.0, -110.0), 260.0, 0.0, 1.0, pad=1.0), V_BRICK, V_VERT])


# ---- 9 chokepoints and risks ---------------------------------------------------------------------------


def sec9(m, root):
    s = board(m, root)
    OV.currents(m, root, [0], n_front=14, big=1.6)
    show(s["die_glow"], beat(0) + beat(2))
    # beat 1: crowding: HBM along the dies, phases pressed against the package
    # beat 2: a cold plate over the GPU; the phases' heat beside it
    cp = empty("s9_cold", root)
    bx("s9_plate", (-50.0, 28.0, -50.0), (50.0, 40.0, 0.0), m["cold"], cp)
    for i in range(5):
        x = -36.0 + 18.0 * i
        bx(f"s9_ch{i}", (x - 4.0, 31.0, -46.0), (x + 4.0, 37.0, 0.3), m["cool"], cp)
    tube("s9_pipe_in", (-30.0, 40.0, -30.0), (-30.0, 60.0, -30.0), 3.0, m["cold"], cp, 16)
    tube("s9_pipe_out", (30.0, 40.0, -30.0), (30.0, 60.0, -30.0), 3.0, m["cold"], cp, 16)
    for i in range(4):
        bx(f"s9_post{i}", (-48.0 + 92.0 * (i % 2), D.DIE_Y[1], -48.0 + 44.0 * (i // 2)), (-44.0 + 92.0 * (i % 2), 28.0, -44.0 + 44.0 * (i // 2)),
           m["cold"], cp)
    D.present(cp, beat(2))
    for i in range(5):
        x = -36.0 + 18.0 * i
        run(root, f"s9_c{i}", [(x, 34.0, -40.0), (x, 34.0, 1.2)], 3, 1.2, m["cool"], 2, 0.0 + 0.04 * i, 0.8, 50)
    show(s["ph"]["heat"], beat(2))
    for side in (-1, 1):
        for k in (0, 2, 4):
            rise(root, f"s9_h{side}{k}", s["ph"]["ind"][(side, k)]["top"], 2, 0.9, m["heat"], 2, 0.05 + 0.03 * k, 0.8, 30.0, 60, (4.0, 4.0))
    tags(root, [
        [("current rises faster than V falls", s["pkg"]["die_face"]), ("more amps every generation", (-66.0, 1.0, 0.0))],
        [("HBM along the dies", s["pkg"]["hbm"]), ("phases squeezed beside", s["ph"]["ind"][(-1, 1)]["top"]),
         ("I/O needs this space too", (D.IP[1], D.IP[3], -40.0))],
        [("liquid cold plate on the GPU", (0.0, 40.0, -25.0)), ("regulator heat adds to it", s["ph"]["ind"][(-1, 2)]["top"])],
    ])
    camera_path(root, [frame((-40.0, 2.0, -10.0), 160.0, 0.20, 0.25), frame((-30.0, 0.0, -50.0), 200.0, 0.10, 0.95, pad=1.0),
                       frame((0.0, 12.0, -40.0), 270.0, 0.20, 0.55, pad=1.0)])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    m.update(D.materials())
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
