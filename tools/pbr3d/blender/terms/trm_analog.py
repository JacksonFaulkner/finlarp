"""TRM_ANALOG on the MLCC base board: a full signal chain laid out on the bench (sensor, amplifier,
filter, converter, MCU, driver, fan), the signal drawn above each stage, then the old-fab wafer.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_analog.py
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_ANALOG"
BEATS = [
    ("Analog chips are everywhere the board meets the real world",
     "Analog chips handle continuous quantities: voltage, current, temperature, sound, radio. On this GPU board the VRM "
     "controller, the current-sense amplifiers in each phase, the regulators for small rails and the fan drivers are all "
     "analog or mixed-signal. The bench lays one complete chain out in a row."),
    ("A sensor gives a tiny, noisy signal",
     "A temperature sensor on the hot inductor puts out a few millivolts that drift with heat, buried in electrical "
     "noise from the switching around it. Nothing digital can use it yet."),
    ("Amplify, then filter",
     "An operational amplifier multiplies the signal a hundredfold with precise, stable gain. A filter of resistors and "
     "capacitors then strips the high-frequency noise, leaving a clean, slow wave. Precision here is the hard part: "
     "microvolt offsets and low drift over years and temperature."),
    ("Convert, decide, and drive something physical",
     "An ADC turns the clean wave into numbers, a microcontroller decides the fan must speed up, and a driver chip turns "
     "its command back into real power: pulses that spin the fan's motor. Analog sits at both ends of every such loop."),
    ("Made on old fabs, sold for decades",
     "Analog parts rarely need leading-edge transistors; many are made on 200 mm and older 300 mm lines that are long "
     "paid off. Thousands of products sell to thousands of customers for 10-20 years, so margins are high and the business "
     "follows industrial and auto cycles. Makers: TI (TXN), Analog Devices (ADI), Microchip (MCHP), NXP (NXPI), onsemi (ON)."),
]

Z = -30.0  # the chain's row on the bench
YW = 26.0  # where the signal waves float
STAGES = {"sensor": 158.0, "amp": 174.0, "filt": 190.0, "adc": 206.0, "mcu": 222.0, "drv": 238.0}


def chain(m, root):
    g = empty("chain", root)
    tops = {}
    x = STAGES["sensor"]
    D.ball("ntc", (x, 3.0, Z), 2.6, m["ceramic"], g, 16)
    for s in (-1, 1):
        D.polyline(f"ntc_leg{s}", [(x + s * 1.2, 1.0, Z), (x + s * 2.5, 0.0, Z)], 0.3, m["tin"], g)
    tops["sensor"] = (x, 5.6, Z)
    tops["amp"] = C.chip(m, g, "opamp", (STAGES["amp"], 0.0, Z), 8.0, 6.0, 2.0, pins=4)
    xf = STAGES["filt"]
    bx("res_b", (xf - 5.0, 0.0, Z - 1.0), (xf - 1.0, 1.6, Z + 1.0), m["dark"], g)
    D.mlcc(m, g, "fcap", (xf + 3.0, 0.0, Z), 4.0, 2.0, 2.0)
    tops["filt"] = (xf, 2.0, Z)
    tops["adc"] = C.chip(m, g, "adc", (STAGES["adc"], 0.0, Z), 8.0, 8.0, 1.6, pins=5)
    tops["mcu"] = C.chip(m, g, "mcu", (STAGES["mcu"], 0.0, Z), 10.0, 10.0, 1.6, pins=7)
    tops["drv"] = C.chip(m, g, "drv", (STAGES["drv"], 0.0, Z), 7.0, 7.0, 1.8, pins=4)
    C.trace(m, g, "chain_tr", [(154.0, 0.0, Z), (246.0, 0.0, Z)], 0.5)
    # fan: a frame and a rotor with blades, standing behind the driver
    fc = (226.0, 26.0, -80.0)
    bx("fan_frame_b", (fc[0] - 20.0, 0.0, fc[2] - 3.0), (fc[0] + 20.0, 4.0, fc[2] + 3.0), m["plastic"], g)
    for s in (-1, 1):
        bx(f"fan_post{s}", (fc[0] + s * 20.0 - 2.0, 0.0, fc[2] - 3.0), (fc[0] + s * 20.0 + 2.0, 46.0, fc[2] + 3.0), m["plastic"], g)
    bx("fan_top", (fc[0] - 20.0, 44.0, fc[2] - 3.0), (fc[0] + 20.0, 48.0, fc[2] + 3.0), m["plastic"], g)
    piv = empty("fan_piv", root, D.P(*fc))
    rotor = empty("fan_rotor", piv)
    D.tube("hub", (0, 0, -2.0), (0, 0, 2.0), 5.0, m["dark"], rotor, 20)
    for k in range(7):
        a = 2 * math.pi * k / 7
        tip = (17.0 * math.cos(a), 17.0 * math.sin(a), 0.0)
        D.polyline(f"blade{k}", [(0, 0, 0), (tip[0] * 0.6, tip[1] * 0.6, 0.8), tip], 2.4, m["plastic"], rotor)
    D.polyline("fan_wire", [(STAGES["drv"] + 4.0, 1.0, Z), (STAGES["drv"] + 4.0, 1.0, fc[2] + 4.0), (fc[0], 2.0, fc[2] + 4.0)], 0.5, m["copper"], g)
    return tops, rotor, fc


def signals(m, root):
    """The signal over each stage: one polyline per stage, shown in the right beats."""
    def noisy(u):
        return 0.15 * math.sin(2 * math.pi * u) + 0.35 * math.sin(2 * math.pi * 11 * u + 1.0) * math.sin(2 * math.pi * 3 * u)

    def clean(u):
        return 0.8 * math.sin(2 * math.pi * u)

    def steps(u):
        return round(4 * clean(u)) / 4

    def pwm(u):
        duty = 0.5 + 0.35 * math.sin(2 * math.pi * u)
        return 0.8 if (u * 8) % 1 < duty else -0.8

    spec = [
        ("w_sensor", STAGES["sensor"], 2.0, noisy, "sig", [(1, 5)]),
        ("w_amp", STAGES["amp"], 9.0, noisy, "sig", [(2, 5)]),
        ("w_filt", STAGES["filt"], 9.0, clean, "sig", [(2, 5)]),
        ("w_adc", STAGES["adc"], 9.0, steps, "h_amber", [(3, 5)]),
        ("w_drv", STAGES["drv"], 9.0, pwm, "pwm", [(3, 5)]),
    ]
    for name, xc, amp, fn, mt, spans in spec:
        g = empty(name, root)
        pts = C.wave_pts(xc - 7.0, xc + 7.0, YW, Z, amp, 1.0, n=120, fn=fn)
        D.polyline(f"{name}_l", pts, 0.3, m[mt], g)
        show(g, [(F(a, 0.1 if a > 0 else 0.0), F(b, 0)) for a, b in spans])


def wafer(m, root):
    g = empty("wafer", root)
    c = (200.0, 0.6, -170.0)
    D.tube("wafer_disc", c, (c[0], 1.6, c[2]), 32.0, m["si"], g, 64)
    dies = []
    for i in range(-6, 7):
        for j in range(-6, 7):
            x, z = c[0] + 4.6 * i, c[2] + 4.6 * j
            if (x - c[0]) ** 2 + (z - c[2]) ** 2 < 29.0 ** 2:
                dies.append(bx(f"wd{i}_{j}", (x - 2.0, 1.6, z - 2.0), (x + 2.0, 1.9, z + 2.0), m["die"], g))
    D.join(dies, "wafer_dies")
    return (c[0], 2.0, c[2])


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root, ctrl=True)
    tops, rotor, fc = chain(m, root)
    signals(m, root)
    wc = wafer(m, root)
    ph = b["ph"]
    C.magnify(m, root, ph["ind"][(1, 1)]["top"], (STAGES["sensor"], 6.0, Z), r=6.0)
    up = lambda p: (p[0], p[1] + 1.0, p[2])  # noqa: E731
    run(root, "flow", [up(tops[k]) for k in ("sensor", "amp", "filt", "adc", "mcu", "drv")] + [(fc[0], 4.0, fc[2] + 4.0)],
        10, 0.8, m["v12"], [3], 0.0, 0.8, 90)
    run(root, "flow0", [up(tops["sensor"]), up(tops["amp"]), up(tops["filt"])], 6, 0.7, m["v12"], [1, 2], 0.0, 0.8, 50)
    C.spin(rotor, [3, 4], turns=3.0, axis=2)

    C.tags(root, {
        0: [("VRM controller: mixed-signal", b["ctrl"]), ("current-sense amps per phase", ph["st"][(-1, 2)]["top"]),
            ("one analog chain, laid out", (200.0, YW, Z))],
        1: [("sensor: a few mV, noisy", (STAGES["sensor"], YW + 4.0, Z)), ("on the hot inductor", ph["ind"][(1, 1)]["top"])],
        2: [("op-amp: x100 gain", (STAGES["amp"], YW + 10.0, Z)), ("RC filter: noise out", (STAGES["filt"], YW - 10.0, Z))],
        3: [("ADC -> numbers", (STAGES["adc"], YW + 10.0, Z)), ("MCU decides", tops["mcu"]), ("driver pulses power", (STAGES["drv"], YW + 10.0, Z)),
            ("fan spins up", (fc[0], fc[1] + 20.0, fc[2]))],
        4: [("200 mm wafer, old fab", wc), ("10-20 year product lives", (200.0, YW, Z)), ("TXN, ADI, MCHP, NXPI, ON", tops["mcu"])],
    })
    row = (200.0, 12.0, Z)
    C.done(SLUG, BEATS, [
        frame((60.0, 5.0, -100.0), 380.0, 0.30, 0.6, pad=1.0),
        frame((STAGES["sensor"] + 6.0, 14.0, Z), 50.0, 0.20, 0.20),
        frame((STAGES["filt"] - 6.0, 15.0, Z), 60.0, 0.15, 0.15),
        frame((205.0, 18.0, -50.0), 120.0, 0.25, 0.30),
        frame((200.0, 5.0, -120.0), 170.0, 0.25, 0.70),
    ], root)
    _ = row


if __name__ == "__main__":
    build()
