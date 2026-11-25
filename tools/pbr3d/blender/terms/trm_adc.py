"""TRM_ADC on the MLCC base board: the VRM controller digitizes the rail; the bench shows a scope
screen where a wave is sampled, quantized to codes, and rebuilt by a DAC.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_adc.py
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_ADC"
BEATS = [
    ("The VRM controller measures the rail with ADCs",
     "Every system that touches the real world needs data converters. On this GPU board, the multiphase controller uses "
     "analog-to-digital converters (ADCs) to read the core voltage and each phase's current thousands of times a second, "
     "so it can steer the power stages."),
    ("A real signal is a continuous wave",
     "The voltage on a wire can take any value at any instant: a smooth, continuous wave. Digital logic can only store "
     "numbers, so the wave has to be measured at moments in time."),
    ("Sampling: freeze the wave at regular ticks",
     "A sample-and-hold circuit grabs the voltage at every clock tick. The tick rate must be more than twice the fastest "
     "frequency in the signal (Nyquist), or fast wiggles fold back as false slow ones."),
    ("Quantizing: round each sample to a code",
     "Each held sample is compared against fixed levels and rounded to the nearest one, giving a binary code. Here 3 bits "
     "give 8 levels; real parts use 12 to 24 bits for precision, or fewer bits at GHz rates in optical DSPs and radios."),
    ("A DAC turns codes back into a voltage",
     "A digital-to-analog converter does the reverse: each code sets an output level, and a filter smooths the steps into a "
     "wave again. Converters sit in radios, radar, test gear and every 800G optical link. Makers: Analog Devices (ADI), "
     "Texas Instruments (TXN), Microchip (MCHP); in-house in Marvell (MRVL) and Broadcom (AVGO) DSPs."),
]

CX, CY, CZ = 199.0, 38.0, -12.0
W, H = 86.0, 56.0
X0, X1 = CX - W / 2 + 4.0, CX + W / 2 - 4.0
AMP = 20.0
NS = 16
LEVELS = 8


def wave(u):
    return 0.8 * math.sin(2 * math.pi * 1.0 * u) + 0.2 * math.sin(2 * math.pi * 3.0 * u + 0.6)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m["bitc"] = C.mat("t_bitc", (0.9, 0.95, 1.0), emit=(0.9, 0.95, 1.0), strength=1.5)
    b = C.base(m, root, ctrl=True)
    g = empty("scope", root)
    bx("stand", (CX - 6.0, 0.0, CZ - 12.0), (CX + 6.0, CY - H / 2 - 6.0, CZ - 4.0), m["dark"], g)
    D.scope(m, g, (CX, CY, CZ), W, H, "sc")
    z = CZ + 0.5
    wpts = C.wave_pts(X0, X1, CY, z, AMP, 1.0, n=96, fn=wave)
    sig = empty("sig", root)
    D.polyline("sig_w", wpts, 0.45, m["sig"], sig)
    show(sig, [(F(1, 0.0), F(4, 0.0)), (F(4, 0.55), F(5, 0))])
    run(root, "trace", wpts, 3, 1.0, m["bit"], 1, 0.0, 0.7, 70)

    step = (X1 - X0) / NS
    lvl = 2 * AMP / (LEVELS - 1)
    stairs, codes = [], []
    for k in range(NS):
        u = (k + 0.5) / NS
        x = X0 + (X1 - X0) * u
        v = AMP * wave(u)
        q = round((v + AMP) / lvl)
        codes.append(q)
        st = empty(f"stem{k}", root)
        bx(f"stem{k}_b", (x - 0.5, min(CY, CY + v), z), (x + 0.5, max(CY, CY + v), z + 0.4), m["bit"], st)
        D.bead(f"stem{k}_d", (x, CY + v, z + 0.6), 1.2, m["bit"], st)
        show(st, [(F(2, 0.05 + 0.85 * k / NS), F(3, 0.0))])
        stairs += [(x - step / 2, CY - AMP + q * lvl, z + 0.2), (x + step / 2, CY - AMP + q * lvl, z + 0.2)]
        # 3-bit code above the screen
        for bit in range(3):
            on = (q >> bit) & 1
            y = CY + H / 2 + 9.0 + 3.2 * (2 - bit)
            cb = empty(f"code{k}_{bit}", root)
            bx(f"code{k}_{bit}_b", (x - 1.3, y, CZ - 1.3), (x + 1.3, y + 2.6, CZ + 1.3), m["bitc" if on else "dim_glow"], cb)
            show(cb, [(F(3, 0.1 + 0.8 * k / NS), F(5, 0))])
    lv = empty("levels", root)
    for j in range(LEVELS):
        y = CY - AMP + j * lvl
        bx(f"lv{j}", (X0, y - 0.12, z - 0.1), (X1, y + 0.12, z + 0.1), m["dim_glow"], lv)
    show(lv, [(F(3, 0), F(5, 0))])
    stair = empty("stair", root)
    D.polyline("stair_l", stairs, 0.5, m["h_amber"], stair)
    show(stair, [(F(3, 0.2), F(5, 0))])
    # beat 4: codes stream from the controller across the board to the scope
    run(root, "codes", [(b["ctrl"][0], 3.5, b["ctrl"][2]), (150.0, 3.5, -200.0), (150.0, 3.5, -40.0), (CX, 6.0, CZ)],
        8, 1.0, m["pwm"], [0, 4], 0.0, 0.8, 50)
    C.magnify(m, root, (b["ctrl"][0], 3.0, b["ctrl"][2]), (CX - W / 2, CY, CZ), r=10.0)

    C.tags(root, {
        0: [("controller: ADCs read V and A", b["ctrl"]), ("16 phases it steers", b["ph"]["ind"][(-1, 3)]["top"]),
            ("GPU package", b["pk"]["top"])],
        1: [("continuous analog wave", (X0 + 10.0, CY + AMP * wave(0.1), z))],
        2: [("sampled at each clock tick", (X0 + 3 * step, CY + AMP * wave(3.5 / NS), z)),
            ("rate > 2x top frequency", (CX, CY - H / 2, CZ))],
        3: [("rounded to 8 levels", (X1, CY, z)), ("3-bit code per sample", (CX, CY + H / 2 + 18.0, CZ))],
        4: [("DAC: codes -> steps -> smooth", (X1 - 10.0, CY + AMP * wave(0.85), z)), ("ADI, TXN, MCHP", (CX, CY - H / 2, CZ))],
    })
    sc = (CX, CY + 6.0, CZ)
    C.done(SLUG, BEATS, [
        frame((40.0, 5.0, -100.0), 420.0, 0.30, 0.6, pad=1.0),
        frame(sc, 110.0, 0.05, 0.05),
        frame(sc, 100.0, 0.05, 0.05),
        frame(sc, 110.0, 0.10, 0.08),
        frame(sc, 120.0, 0.22, 0.12),
    ], root)


if __name__ == "__main__":
    build()
