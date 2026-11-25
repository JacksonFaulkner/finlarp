"""TRM_MICROCONTROLLER on the MLCC base board: the board's housekeeping MCU, then a QFP opened up
on the bench to show the die's CPU, flash, SRAM, peripherals and a small NPU.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_microcontroller.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, blink  # noqa: E402

SLUG = "TRM_MICROCONTROLLER"
BEATS = [
    ("A small MCU keeps the big board in order",
     "Next to the GPU sits a tiny computer: a microcontroller (MCU) that sequences the power rails on and off, watches "
     "temperatures and fans, and talks to the voltage controller. Cars carry dozens of MCUs, a washing machine a few, and "
     "factories millions."),
    ("Open the package: a whole computer on one die",
     "Inside the plastic package a lead frame fans out to dozens of pins, each tied to the die by a gold bond wire. The die "
     "holds a CPU core, flash memory for the program, SRAM for working data, and peripherals: ADCs, timers, serial ports "
     "and PWM outputs. Cheap MCUs run on older, depreciated nodes (40-180 nm)."),
    ("Fetch, execute, store, millions of times a second",
     "The CPU fetches each instruction from flash, works on data held in SRAM and writes results back, typically at "
     "tens to hundreds of MHz. Because the program lives on the chip, an MCU boots instantly and runs for years."),
    ("Pins talk to the world: sensors in, commands out",
     "The peripherals turn pins into inputs and outputs: here the MCU reads temperatures, toggles enable pins in the right "
     "order and sends commands to the VRM controller over a serial bus."),
    ("New MCUs add a tiny neural accelerator",
     "Edge AI parts add a small NPU block of multiply-accumulate units so the MCU can run keyword spotting, vibration or "
     "vision models locally at milliwatts. Pricing follows auto and industrial inventory cycles. Makers: Microchip (MCHP), "
     "NXP (NXPI), STMicro (STM), Renesas (RNECY), TI (TXN), Infineon (IFNNY)."),
]

MCU = (190.0, 0.0, -150.0)
CX, CZ = 199.0, -42.0
S = 36.0  # package half size on the bench
DIE = 13.0


def package(m, root):
    g = empty("qfp", root)
    bx("q_mold_b", (CX - S, 0.6, CZ - S), (CX + S, 4.0, CZ + S), m["mold"], g)
    # lid half: only the back half stays, so the die shows
    bx("q_mold_t", (CX - S, 4.0, CZ - S), (CX + S, 9.0, CZ - S + 12.0), m["mold"], g)
    bx("q_pad", (CX - DIE - 2.0, 4.0, CZ - DIE - 2.0), (CX + DIE + 2.0, 4.6, CZ + DIE + 2.0), m["copper"], g)
    bx("q_die", (CX - DIE, 4.6, CZ - DIE), (CX + DIE, 5.6, CZ + DIE), m["si"], g)
    n = 12
    leads = {}
    for side in range(4):
        for i in range(n):
            u = -S + 6.0 + (2 * S - 12.0) * i / (n - 1)
            if side == 0:
                inner, outer, axis = (CX + u, CZ + S - 8.0), (CX + u, CZ + S + 6.0), "z"
            elif side == 1:
                inner, outer, axis = (CX + u, CZ - S + 8.0), (CX + u, CZ - S - 6.0), "z"
            elif side == 2:
                inner, outer, axis = (CX + S - 8.0, CZ + u), (CX + S + 6.0, CZ + u), "x"
            else:
                inner, outer, axis = (CX - S + 8.0, CZ + u), (CX - S - 6.0, CZ + u), "x"
            w = 1.0
            lo = (min(inner[0], outer[0]) - (w if axis == "z" else 0), 3.6, min(inner[1], outer[1]) - (w if axis == "x" else 0))
            hi = (max(inner[0], outer[0]) + (w if axis == "z" else 0), 4.2, max(inner[1], outer[1]) + (w if axis == "x" else 0))
            bx(f"ld{side}_{i}", lo, hi, m["tin"], g)
            # die edge pad -> lead tip bond wire
            dx = max(-DIE + 1.0, min(DIE - 1.0, inner[0] - CX))
            dz = max(-DIE + 1.0, min(DIE - 1.0, inner[1] - CZ))
            D.wire(f"bw{side}_{i}", D.arc((CX + dx, 5.6, CZ + dz), (inner[0], 4.2, inner[1]), 3.0, 6), 0.15, m["gold"], g, 6)
            leads[(side, i)] = (inner[0], 4.4, inner[1])
    return leads


def blocks(m, root):
    """Die floorplan on the die top (y 5.6)."""
    y = 5.6
    g = empty("fp", root)
    x0, z0 = CX - DIE + 1.0, CZ - DIE + 1.0
    blk = {
        "cpu": (x0, z0 + 13.0, x0 + 9.0, z0 + 24.0, "dark"),
        "flash": (x0 + 10.0, z0 + 12.0, x0 + 24.0, z0 + 24.0, "fet"),
        "sram": (x0, z0, x0 + 9.0, z0 + 12.0, "hbm"),
        "npu": (x0 + 10.0, z0, x0 + 17.0, z0 + 11.0, "driver"),
        "periph": (x0 + 18.0, z0, x0 + 24.0, z0 + 11.0, "gnd"),
    }
    cen = {}
    for k, (a, b_, c, d, mt) in blk.items():
        bx(f"blk_{k}", (a, y, b_), (c, y + 0.3, d), m[mt], g)
        cen[k] = ((a + c) / 2, y + 0.3, (b_ + d) / 2)
    # flash and sram cell grids, CPU pipeline stripes
    cells = []
    for i in range(10):
        for j in range(8):
            cells.append(bx(f"fc{i}{j}", (x0 + 10.6 + 1.3 * i, y + 0.3, z0 + 12.8 + 1.4 * j), (x0 + 11.5 + 1.3 * i, y + 0.45, z0 + 13.8 + 1.4 * j), m["copper"], g))
    for i in range(6):
        for j in range(8):
            cells.append(bx(f"sc{i}{j}", (x0 + 0.6 + 1.35 * i, y + 0.3, z0 + 0.6 + 1.4 * j), (x0 + 1.5 + 1.35 * i, y + 0.45, z0 + 1.5 + 1.4 * j), m["solder"], g))
    D.join(cells, "cells")
    npu = empty("npu_glow", root)
    for i in range(4):
        for j in range(6):
            bx(f"mac{i}{j}", (x0 + 10.6 + 1.6 * i, y + 0.35, z0 + 0.8 + 1.7 * j), (x0 + 11.7 + 1.6 * i, y + 0.6, z0 + 1.9 + 1.7 * j), m["sig"], npu)
    show(npu, [])
    return cen, npu


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root, ctrl=True)
    brd = empty("mcu_brd", root)
    top = C.chip(m, brd, "mcu", MCU, 14.0, 14.0, 1.6, pins=10)
    bus = [(MCU[0] - 8.0, 0.0, MCU[2]), (145.0, 0.0, MCU[2]), (145.0, 0.0, -201.0), (14.0, 0.0, -201.0)]
    C.trace(m, brd, "i2c", bus, 0.6)
    leads = package(m, root)
    cen, npu = blocks(m, root)
    C.magnify(m, root, top, (CX - S, 10.0, CZ), r=4.0)

    lift = 0.5
    up = lambda p: (p[0], p[1] + lift, p[2])  # noqa: E731
    run(root, "fetch", [up(cen["flash"]), up(cen["cpu"])], 6, 0.6, m["pwm"], 2, 0.0, 0.9, 25)
    run(root, "store", [up(cen["cpu"]), up(cen["sram"])], 6, 0.6, m["v12"], 2, 0.1, 0.95, 25)
    run(root, "load", [up(cen["sram"]), (cen["cpu"][0] + 2.0, cen["cpu"][1] + lift, cen["cpu"][2] - 2.0)], 4, 0.6, m["sig"], 2, 0.3, 0.95, 25)
    # beat 3: pins toggle; commands go out over the bus to the VRM controller
    pins = empty("pin_glow", root)
    for k, ((side, i), p) in enumerate(leads.items()):
        if k % 3 == 0:
            g = empty(f"pg{k}", pins)
            bx(f"pgb{k}", (p[0] - 1.0, 4.2, p[2] - 1.0), (p[0] + 1.0, 4.6, p[2] + 1.0), m["v12"], g)
            blink(g, 3, [k % 8], n=8, on=0.5)
    run(root, "cmd", [(q[0], 0.8, q[2]) for q in bus], 6, 0.9, m["pwm"], [0, 3], 0.0, 0.85, 70)
    run(root, "periph", [up(cen["periph"]), (CX + S - 8.0, 4.8, CZ)], 4, 0.6, m["v12"], 3, 0.0, 0.8, 20)
    # beat 4: the NPU lights in waves
    blink(npu, 4, [0, 2, 4, 6], n=8, on=0.6)

    C.tags(root, {
        0: [("housekeeping MCU", top), ("serial bus to the VRM controller", (145.0, 1.0, -170.0)), ("GPU package", b["pk"]["top"])],
        1: [("CPU core", cen["cpu"]), ("flash: the program", cen["flash"]), ("SRAM: working data", cen["sram"]),
            ("gold bond wires to pins", leads[(0, 3)]), ("ADC, timers, UART", cen["periph"])],
        2: [("fetch from flash", cen["flash"]), ("compute in the core", cen["cpu"]), ("data in SRAM", cen["sram"])],
        3: [("pins toggle: enables, PWM", leads[(2, 5)]), ("commands to the controller", b["ctrl"])],
        4: [("tiny NPU: edge AI at mW", cen["npu"]), ("MCHP, NXPI, STM, RNECY, TXN", (CX, 9.0, CZ - S + 6.0))],
    })
    die = (CX, 5.0, CZ)
    C.done(SLUG, BEATS, [
        frame((90.0, 0.0, -110.0), 330.0, 0.35, 0.65, pad=1.0),
        frame(die, 95.0, 0.25, 0.70),
        frame(die, 40.0, 0.15, 0.95),
        frame((CX - 10.0, 3.0, CZ - 40.0), 170.0, 0.30, 0.75),
        frame(die, 38.0, 0.30, 0.90),
    ], root)


if __name__ == "__main__":
    build()
