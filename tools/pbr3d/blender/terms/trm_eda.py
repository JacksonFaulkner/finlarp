"""TRM_EDA: chip design software, drawn as the design flow on a bench. A workstation screen of RTL
code on the left, a giant block of chip layout in the middle (standard-cell rows on silicon with
two metal routing layers and vias above, cut at the front), a compute-farm rack behind that runs
simulation and timing, and a finished wafer on the right (tapeout).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_eda.py

Beats:
  0 flow      code -> gates -> layout -> wafer, the whole bench
  1 synthesis RTL lines turn into rows of standard cells
  2 route     metal 1 and metal 2 wires and vias appear over the cells
  3 verify    the compute farm blinks; a critical path fails timing, gets fixed
  4 tapeout   the layout ships to the fab as a wafer; who sells the tools
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_EDA"
BEATS = [
    ("EDA software turns a chip idea into a layout a fab can print",
     "Electronic design automation (EDA) is the software chain every chip goes through: engineers describe logic in "
     "code, tools turn it into billions of transistors placed and wired on silicon, simulators and checkers prove it "
     "works, and the final layout goes to the fab. A big AI chip can't be designed any other way."),
    ("Synthesis: code becomes rows of logic gates",
     "Designers write register-transfer-level (RTL) code in Verilog or VHDL. Logic synthesis maps it onto a library "
     "of standard cells (NAND, flip-flop, buffer...) supplied for a specific process node, then placement packs "
     "those cells into rows on the die, trying to keep connected cells close."),
    ("Place and route: wiring billions of cells on a dozen metal layers",
     "Routing tools draw the wires: short local links on the lowest metal layers, longer ones on higher layers, "
     "joined by vias, alternating direction from layer to layer. A leading-edge chip has 15+ metal layers and "
     "tens of kilometres of wire, all of it laid out by software under strict spacing rules."),
    ("Verification: simulate, check timing, fix, repeat",
     "Before tapeout, server farms run simulation and emulation for months, static timing analysis checks every "
     "path meets the clock (here one path is too slow and gets re-buffered), and physical checks confirm the layout "
     "follows the fab's rules. A mistake found after manufacturing costs a re-spin: months and tens of millions."),
    ("Tapeout goes to the fab; two vendors sell most of the tools",
     "The finished layout is sent to the foundry (tapeout) and becomes masks and wafers. The market is a near "
     "duopoly of Synopsys (SNPS) and Cadence (CDNS), with Siemens EDA third, sold as multi-year licences, plus IP "
     "blocks like interfaces and Arm (ARM) CPU cores. More custom AI chips means more design seats and more IP."),
]

# layout block (middle)
LX0, LX1, LZ0 = -70.0, 70.0, -90.0
SUBY = (-12.0, 0.0)
NROW = 8
# screen (left), rack (behind), wafer (right)
SX0, SX1 = -170.0, -100.0
RACK = (-30.0, 30.0, -180.0, -140.0)
WC = (140.0, 0.0, -45.0)


def mats(m):
    m["cell"] = mat("eda_cell", (0.55, 0.35, 0.65), metal=0.3, rough=0.4)
    m["cell2"] = mat("eda_cell2", (0.35, 0.55, 0.70), metal=0.3, rough=0.4)
    m["m1"] = mat("eda_m1", (0.30, 0.65, 1.0), emit=(0.25, 0.60, 1.0), strength=2.0)
    m["m2"] = mat("eda_m2", (1.0, 0.45, 0.70), emit=(1.0, 0.40, 0.65), strength=2.0)
    m["code"] = mat("eda_code", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=2.5)
    m["wafer"] = mat("eda_wafer", (0.45, 0.47, 0.60), metal=0.8, rough=0.15)


def screen(m, root):
    g = empty("ws", root)
    bx("ws_desk", (SX0 - 10.0, -2.0, -60.0), (SX1 + 10.0, 0.0, 0.0), m["dark"], g)
    bx("ws_stand", ((SX0 + SX1) / 2 - 3.0, 0.0, -42.0), ((SX0 + SX1) / 2 + 3.0, 10.0, -38.0), m["alu"], g)
    bx("ws_bezel", (SX0, 10.0, -44.0), (SX1, 56.0, -40.0), m["plastic"], g)
    bx("ws_scr", (SX0 + 2.0, 12.0, -40.0), (SX1 - 2.0, 54.0, -39.8), m["screen"], g)
    bx("ws_kb", (SX0 + 10.0, 0.0, -24.0), (SX1 - 10.0, 1.2, -12.0), m["plastic"], g)
    lines = []
    for r in range(12):
        ind = 4.0 * ((r * 5) % 3)
        w = 14.0 + 22.0 * ((r * 7) % 5) / 4
        y = 51.0 - 3.3 * r
        lines.append(empty(f"ws_l{r}", root))
        bx(f"ws_lb{r}", (SX0 + 5.0 + ind, y - 1.0, -39.7), (SX0 + 5.0 + ind + w, y, -39.5), m["code"], lines[-1])
    return lines, {"scr": ((SX0 + SX1) / 2, 54.0, -40.0), "kb": ((SX0 + SX1) / 2, 1.2, -18.0)}


def layout(m, root):
    """Silicon, cell rows, M1 (along x), M2 (along z), vias. Returns groups and points."""
    g = empty("lay", root)
    bx("lay_si", (LX0, SUBY[0], LZ0), (LX1, SUBY[1], 0.0), m["si"], g)
    bx("lay_well", (LX0, -2.0, LZ0), (LX1, 0.0, 0.0), m["nplus"], g)
    rd = (-LZ0 - 6.0) / NROW
    rows = []
    for r in range(NROW):
        rg = empty(f"row{r}", root)
        z0 = LZ0 + 3.0 + rd * r
        x = LX0 + 3.0
        k = 0
        while x < LX1 - 6.0:
            w = 4.0 + 3.0 * ((r * 3 + k * 7) % 4)
            x1 = min(x + w, LX1 - 3.0)
            bx(f"cell{r}_{k}", (x, 0.0, z0 + 0.4), (x1 - 0.5, 3.0, z0 + rd - 0.4), m["cell" if (r + k) % 2 else "cell2"], rg)
            x = x1
            k += 1
        bx(f"rail{r}", (LX0 + 2.0, 3.0, z0 - 0.2), (LX1 - 2.0, 3.4, z0 + 0.4), m["copper"], rg)
        show(rg, [(F(0, 0), F(1, 0)), (F(1, 0.1 + 0.08 * r), F(5, 0))])
        rows.append(rg)
    m1, m2, vias = empty("m1", root), empty("m2", root), empty("vias", root)
    for r in range(NROW * 2):
        z = LZ0 + 5.0 + (rd / 2) * r
        xa = LX0 + 6.0 + 9.0 * ((r * 5) % 7)
        xb = min(LX1 - 4.0, xa + 30.0 + 8.0 * ((r * 3) % 5))
        bx(f"m1_{r}", (xa, 6.0, z - 0.6), (xb, 7.0, z + 0.6), m["m1"], m1)
    for c in range(14):
        x = LX0 + 6.0 + 9.6 * c
        za = LZ0 + 6.0 + 7.0 * ((c * 3) % 5)
        zb = min(-2.0, za + 35.0 + 6.0 * (c % 3))
        bx(f"m2_{c}", (x - 0.6, 10.0, za), (x + 0.6, 11.0, zb), m["m2"], m2)
        for v in range(2):
            vz = za + 2.0 + (zb - za - 4.0) * v
            bx(f"v_{c}{v}", (x - 0.5, 3.4, vz - 0.5), (x + 0.5, 10.0, vz + 0.5), m["tin"], vias)
    show(m1, [(F(2, 0.1), F(5, 0))])
    show(m2, [(F(2, 0.4), F(5, 0))])
    show(vias, [(F(2, 0.4), F(5, 0))])
    return rows, {"cells": (LX0 + 20.0, 3.0, -4.0), "m1": (LX0 + 40.0, 7.0, LZ0 + 60.0), "m2": (LX1 - 20.0, 11.0, -20.0),
                  "si": (LX1 - 10.0, -6.0, 0.0), "lay": (0.0, 12.0, LZ0 / 2)}


def rack(m, root):
    x0, x1, z0, z1 = RACK
    g = empty("rack", root)
    bx("rk_frame", (x0, 0.0, z0), (x1, 90.0, z1), m["dark"], g)
    leds = [empty(f"rk_led{k}", root) for k in range(4)]
    for s in range(14):
        y = 4.0 + 6.0 * s
        bx(f"rk_srv{s}", (x0 + 2.0, y, z1 - 2.0), (x1 - 2.0, y + 5.0, z1 + 0.2), m["grid"], g)
        for j in range(5):
            x = x0 + 6.0 + 4.0 * j
            bx(f"rk_l{s}{j}", (x, y + 2.0, z1 + 0.2), (x + 2.0, y + 3.0, z1 + 0.5), m["sig"], leds[(s + j) % 4])
    for k, l in enumerate(leds):
        show(l, [])
    return leds, {"rack": ((x0 + x1) / 2, 92.0, z1)}


def wafer(m, root):
    g = empty("wf", root)
    bx("wf_stand", (WC[0] - 30.0, -4.0, WC[2] - 30.0), (WC[0] + 30.0, 0.0, WC[2] + 30.0), m["dark"], g)
    D.tube("wf_disc", (WC[0], 0.0, WC[2]), (WC[0], 1.2, WC[2]), 26.0, m["wafer"], g, 64)
    dies = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            x, z = WC[0] + 5.2 * i, WC[2] + 5.2 * j
            if (5.2 * i) ** 2 + (5.2 * j) ** 2 < 22.0 ** 2:
                dies.append(bx(f"wf_d{i}{j}", (x - 2.3, 1.2, z - 2.3), (x + 2.3, 1.5, z + 2.3), m["die"], g))
    D.join(dies, "wf_dies")
    show(g, [(F(0, 0), F(1, 0)), (F(4, 0.25), F(5, 0))])
    return {"wf": (WC[0], 1.5, WC[2] + 20.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("floor", (-200.0, -14.0, -200.0), (190.0, -12.0, 30.0), m["grid"], root)
    lines, sp = screen(m, root)
    rows, lp = layout(m, root)
    leds, rp = rack(m, root)
    wp = wafer(m, root)
    for k, l in enumerate(lines):
        show(l, [(F(0, 0.05 * k), F(5, 0))])

    # beat 0: one bead tour of the flow
    run(root, "flow", [((SX0 + SX1) / 2, 30.0, -38.0), (LX0, 20.0, -40.0), (LX1, 20.0, -40.0), (WC[0], 10.0, WC[2])], 4, 1.4, m["code"], 0, 0.2, 0.8, 70)
    # beat 1: code lines fly into the cell rows
    for r in range(NROW):
        z0 = LZ0 + 3.0 + (-LZ0 - 6.0) / NROW * (r + 0.5)
        run(root, f"syn{r}", [(SX1 - 4.0, 50.0 - 3.3 * r, -39.0), (LX0 - 10.0, 22.0, z0), (LX0 + 20.0 + 10.0 * r, 4.0, z0)], 1, 1.0, m["code"], 1, 0.02 + 0.08 * r, 0.02 + 0.08 * r, 25)
    # beat 2: signal beads run along M1 and M2
    run(root, "r1", [(LX0 + 10.0, 7.5, -30.0), (LX1 - 10.0, 7.5, -30.0)], 6, 0.7, m["m1"], 2, 0.2, 0.9, 30)
    run(root, "r2", [(LX0 + 25.0, 11.5, LZ0 + 10.0), (LX0 + 25.0, 11.5, -5.0)], 5, 0.7, m["m2"], 2, 0.5, 0.95, 30)
    # beat 3: farm blinks; a critical path is red (too slow), then green after a buffer is inserted
    for k, l in enumerate(leds):
        blink(l, 3, [k, k + 4], n=8, on=0.7)
        blink(l, 1, [k], n=4, on=0.5)
    crit = [(LX0 + 8.0, 15.0, LZ0 + 8.0), (LX0 + 8.0, 15.0, -40.0), (LX1 - 30.0, 15.0, -40.0), (LX1 - 30.0, 15.0, -6.0)]
    bad, good = empty("crit_bad", root), empty("crit_good", root)
    D.polyline("crit_b", crit, 0.9, m["warn"], bad)
    D.polyline("crit_g", crit, 0.9, m["sig"], good)
    bx("buf_cell", (LX0 + 20.0, 15.0, -42.5), (LX0 + 26.0, 16.0, -37.5), m["sig"], good)
    show(bad, [(F(3, 0.05), F(3, 0.55))])
    show(good, [(F(3, 0.55), F(4, 0))])
    run(root, "crit_slow", crit, 3, 1.0, m["warn"], 3, 0.05, 0.25, 45, until=F(3, 0.55))
    run(root, "crit_fast", crit, 3, 1.0, m["sig"], 3, 0.6, 0.8, 22)
    run(root, "farm", [(0.0, 50.0, RACK[3]), (0.0, 30.0, LZ0 - 4.0), (0.0, 14.0, -50.0)], 5, 0.9, m["e_blue"], 3, 0.0, 0.5, 35)
    rise(root, "farm_heat", (0.0, 92.0, (RACK[2] + RACK[3]) / 2), 6, 1.0, m["heat"], 3, 0.0, 0.8, 25.0, 50, (20.0, 12.0))
    # beat 4: the layout ships to the wafer
    run(root, "tapeout", [(LX1 - 10.0, 16.0, -45.0), ((LX1 + WC[0]) / 2, 30.0, -45.0), (WC[0], 4.0, WC[2])], 8, 1.2, m["v12"], 4, 0.0, 0.5, 40)

    C.tags(root, {
        0: [("RTL code (Verilog)", sp["scr"]), ("chip layout, cut open", lp["lay"]), ("compute farm", rp["rack"]),
            ("wafer: the goal", wp["wf"])],
        1: [("RTL code", sp["scr"]), ("standard-cell rows", lp["cells"]), ("silicon die", lp["si"])],
        2: [("metal 1: short wires along x", lp["m1"]), ("metal 2: along z, via down", lp["m2"]),
            ("15+ layers on a real chip", lp["lay"])],
        3: [("sim + timing on server farms", rp["rack"]), ("slow path fails timing", (LX0 + 8.0, 14.0, -60.0)),
            ("buffer inserted: passes", (LX0 + 23.0, 16.0, -40.0))],
        4: [("tapeout -> masks, wafers", wp["wf"]), ("SNPS, CDNS, Siemens", lp["lay"]), ("IP: Arm (ARM) cores", sp["scr"])],
    })
    C.done(SLUG, BEATS, [
        frame((-10.0, 30.0, -70.0), 330.0, 0.15, 0.45, pad=1.0),
        frame((-80.0, 20.0, -40.0), 190.0, 0.25, 0.45),
        frame((0.0, 6.0, -45.0), 140.0, 0.20, 0.70),
        frame((0.0, 30.0, -90.0), 190.0, 0.30, 0.40),
        frame((40.0, 10.0, -60.0), 260.0, -0.20, 0.50, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
