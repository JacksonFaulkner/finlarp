"""TRM_TIMING on the MLCC base board: an oscillator and clock buffer on the board, a crystal
oscillator cut open on the bench, clock edges fanning out, and jitter.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_timing.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_TIMING"
BEATS = [
    ("A tiny oscillator sets the beat for the whole board",
     "Every digital chip needs a clock. On this board a small crystal oscillator makes a reference tone and a clock "
     "generator/buffer chip multiplies and copies it to the GPU, the controller and every high-speed link."),
    ("Inside: a slice of quartz between two electrodes",
     "Open the oscillator's ceramic package and there is a thin quartz blank held on conductive mounts, with metal "
     "electrodes on both faces, and a small driver chip. MEMS oscillators replace the quartz with a tiny silicon "
     "resonator, which is SiTime's approach."),
    ("It rings at one exact frequency",
     "Quartz is piezoelectric: a voltage bends it, and bending makes a voltage. The driver keeps it ringing at its "
     "natural frequency (here, as often, ~25-156 MHz), turning the vibration into a square-wave clock accurate to parts "
     "per million."),
    ("The clock fans out to every chip in step",
     "The clock generator multiplies the reference with phase-locked loops and buffers copies out on matched traces, so "
     "the GPU, controller and SerDes all tick in step. A switch or AI server carries dozens of these outputs."),
    ("Jitter: a few hundred femtoseconds can break a link",
     "Real edges wobble a little in time (jitter). At 112-224 Gb/s per lane a bit lasts only a few picoseconds, so "
     "SerDes need clocks with jitter in the tens of femtoseconds. Faster links mean more, better timing parts per box: "
     "SiTime (SITM), Renesas (RNECY), TI (TXN), Microchip (MCHP), Skyworks (SWKS)."),
]

# the board-side parts: oscillator and clock buffer near the right edge, behind the phases
OSC = (175.0, 0.0, -150.0)
BUF = (205.0, 0.0, -150.0)
# the giant cut-open oscillator on the bench
GX0, GX1, GZ0 = 160.0, 240.0, -50.0
GY0 = 0.6


def giant(m, root):
    g = empty("xo", root)
    bx("xo_base", (GX0, GY0, GZ0), (GX1, GY0 + 6.0, 0.0), m["ceramic"], g)
    bx("xo_wall_l", (GX0, GY0 + 6.0, GZ0), (GX0 + 4.0, GY0 + 26.0, 0.0), m["ceramic"], g)
    bx("xo_wall_r", (GX1 - 4.0, GY0 + 6.0, GZ0), (GX1, GY0 + 26.0, 0.0), m["ceramic"], g)
    bx("xo_wall_b", (GX0, GY0 + 6.0, GZ0), (GX1, GY0 + 26.0, GZ0 + 4.0), m["ceramic"], g)
    bx("xo_lid", (GX0 - 1.0, GY0 + 26.0, GZ0 - 1.0), (GX1 + 1.0, GY0 + 28.0, -22.0), m["steel"], g)
    for i, x in enumerate((GX0 + 6.0, GX1 - 14.0)):
        bx(f"xo_pad{i}", (x, GY0 - 0.4, GZ0 + 6.0), (x + 8.0, GY0, -6.0), m["gold"], g)
    # driver chip on the floor with bond wires
    bx("xo_ic", (GX0 + 10.0, GY0 + 6.0, GZ0 + 10.0), (GX0 + 30.0, GY0 + 8.0, -6.0), m["si"], g)
    for k in range(4):
        z = GZ0 + 14.0 + 7.0 * k
        D.wire(f"xo_bw{k}", D.arc((GX0 + 28.0, GY0 + 8.0, z), (GX0 + 36.0, GY0 + 6.0, z), 3.0, 6), 0.2, m["gold"], g, 6)
    # quartz blank on two conductive mounts, electrodes on both faces: this group vibrates
    bx("mount_l", (GX0 + 36.0, GY0 + 6.0, GZ0 + 14.0), (GX0 + 40.0, GY0 + 16.0, GZ0 + 20.0), m["silicon"], g)
    bx("mount_r", (GX1 - 10.0, GY0 + 6.0, GZ0 + 14.0), (GX1 - 6.0, GY0 + 16.0, GZ0 + 20.0), m["silicon"], g)
    blank = empty("blank", root)
    bx("blank_q", (GX0 + 34.0, GY0 + 16.0, GZ0 + 8.0), (GX1 - 4.0, GY0 + 18.0, -0.5), m["quartz_c"], blank)
    bx("blank_et", (GX0 + 44.0, GY0 + 18.0, GZ0 + 14.0), (GX1 - 14.0, GY0 + 18.4, -6.0), m["gold"], blank)
    bx("blank_eb", (GX0 + 44.0, GY0 + 15.6, GZ0 + 14.0), (GX1 - 14.0, GY0 + 16.0, -6.0), m["gold"], blank)
    glow = empty("blank_glow", blank)
    bx("blank_g", (GX0 + 35.0, GY0 + 16.2, GZ0 + 9.0), (GX1 - 5.0, GY0 + 17.8, -0.3), m["chan"], glow)
    show(glow, [])
    return blank, glow, {"blank": ((GX0 + GX1) / 2 + 10.0, GY0 + 18.0, -4.0), "ic": (GX0 + 20.0, GY0 + 8.0, -6.0),
                         "can": ((GX0 + GX1) / 2, GY0 + 28.0, -30.0), "mount": (GX1 - 8.0, GY0 + 16.0, GZ0 + 17.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root, ctrl=True)
    brd = empty("clk", root)
    osc_top = C.chip(m, brd, "osc", OSC, 10.0, 8.0, 2.4, pins=2, body="ceramic", lead="gold")
    buf_top = C.chip(m, brd, "cbuf", BUF, 16.0, 16.0, 1.6, pins=8)
    C.trace(m, brd, "t_ob", [(OSC[0] + 5.0, 0.0, OSC[2]), (BUF[0] - 8.0, 0.0, BUF[2])], 0.6)
    outs = {
        "gpu": [(BUF[0] - 8.0, 0.0, BUF[2] + 4.0), (150.0, 0.0, BUF[2] + 4.0), (150.0, 0.0, -70.0), (40.0, 0.0, -70.0)],
        "ctrl": [(BUF[0] - 8.0, 0.0, BUF[2] - 4.0), (145.0, 0.0, BUF[2] - 4.0), (145.0, 0.0, -200.0), (14.0, 0.0, -200.0)],
        "edge": [(BUF[0] + 8.0, 0.0, BUF[2]), (245.0, 0.0, BUF[2]), (245.0, 0.0, -205.0)],
    }
    for k, p in outs.items():
        C.trace(m, brd, f"t_{k}", p, 0.6)
    blank, glow, gp = giant(m, root)
    C.magnify(m, root, osc_top, (GX0, 15.0, -25.0), r=7.0)
    C.wiggle(blank, [2], amp=(0.0, 0.5, 0.0), period=4)
    show(glow, [(F(2, 0.05), F(3, 0))])
    # square-wave edges coming off the driver
    sq = []
    x = GX0 + 4.0
    for k in range(10):
        sq += [(x, 36.0, -2.0), (x, 42.0, -2.0), (x + 4.0, 42.0, -2.0), (x + 4.0, 36.0, -2.0)]
        x += 8.0
    sqg = empty("square", root)
    D.polyline("square_l", sq, 0.35, m["pwm"], sqg)
    show(sqg, [(F(2, 0.3), F(3, 0))])
    for k, p in outs.items():
        pp = [(q[0], 0.8, q[2]) for q in p]
        run(root, f"clk_{k}", pp, 10, 0.9, m["pwm"], 3, 0.0, 0.9, 60)
    run(root, "clk_in", [(OSC[0] + 5.0, 0.8, OSC[2]), (BUF[0] - 8.0, 0.8, BUF[2])], 6, 0.9, m["pwm"], 3, 0.0, 0.9, 20)
    # jitter: clean edges vs wobbly edges on two traces above the bench
    for name, yb, jit, mt in (("clean", 50.0, 0.0, "sig"), ("jitter", 62.0, 1.6, "warn")):
        pts = []
        x = GX0 + 4.0
        for k in range(9):
            d = jit * ((k * 7) % 5 - 2) / 2
            pts += [(x + d, yb, -2.0), (x + d, yb + 6.0, -2.0), (x + 4.0 + d, yb + 6.0, -2.0), (x + 4.0 + d, yb, -2.0)]
            x += 8.5
        gg = empty(name, root)
        D.polyline(f"{name}_l", pts, 0.35, m[mt], gg)
        show(gg, [(F(4, 0), F(5, 0))])

    C.tags(root, {
        0: [("crystal oscillator", osc_top), ("clock generator / buffer", buf_top), ("GPU package", b["pk"]["top"])],
        1: [("quartz blank", gp["blank"]), ("driver IC", gp["ic"]), ("ceramic package, lid", gp["can"]), ("conductive mount", gp["mount"])],
        2: [("piezo: rings at one frequency", gp["blank"]), ("square-wave clock out", (GX0 + 40.0, 42.0, -2.0))],
        3: [("PLL multiplies, buffer copies", buf_top), ("to the GPU", (40.0, 1.0, -70.0)), ("to the controller", b["ctrl"])],
        4: [("clean edges", (GX0 + 4.0, 56.0, -2.0)), ("jittered edges: bit errors", (GX0 + 40.0, 68.0, -2.0)),
            ("SITM, RNECY, TXN, MCHP", gp["can"])],
    })
    bc = ((GX0 + GX1) / 2, 20.0, -20.0)
    C.done(SLUG, BEATS, [
        frame((90.0, 0.0, -110.0), 330.0, 0.35, 0.65, pad=1.0),
        frame(bc, 100.0, 0.25, 0.30),
        frame((bc[0], 28.0, -10.0), 100.0, 0.10, 0.15),
        frame((80.0, 0.0, -130.0), 330.0, 0.15, 0.85, pad=1.0),
        frame((bc[0], 50.0, -4.0), 100.0, 0.05, 0.05),
    ], root)


if __name__ == "__main__":
    build()
