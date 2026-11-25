"""TRM_POWER_MOSFET on the MLCC base board: one power stage's low-side FET drawn huge on the bench,
cut through its trench cells, then the 16 phases switching in turn.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_power_mosfet.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_POWER_MOSFET"
BEATS = [
    ("Power MOSFETs sit in every phase round the GPU",
     "Each of the 16 phases round the GPU has a power stage: a small black package holding two power MOSFETs and their "
     "driver. Together they turn 12 V into the ~0.8 V the GPU core runs on, at more than a thousand amps."),
    ("Cut through: millions of trench cells in parallel",
     "Inside, a power MOSFET is not one transistor but millions of identical cells side by side. Each cell has a gate "
     "(doped polysilicon in a trench, wrapped in thin oxide), an n+ source on top, a p-type body, a thick lightly doped "
     "drift region that holds the voltage when off, and the n+ substrate and drain metal underneath."),
    ("Gate on: a channel opens and electrons pour down to the drain",
     "Put a few volts on the gate and the p-body next to each trench inverts into a thin n-type channel. Electrons flow "
     "from the source, down the channel, through the drift region to the drain. Gate off, the channel vanishes and the "
     "drift region blocks. The lower the on-resistance (Rds(on)), the less power is lost as heat."),
    ("The phases fire in turn, hundreds of thousands of times a second",
     "The controller switches each phase's MOSFETs on and off at hundreds of kHz to MHz, staggered so the phases take "
     "turns. The inductor smooths the pulses into steady current; the more phases, the smaller the ripple and the more "
     "total current the GPU can draw."),
    ("Every milliohm becomes heat",
     "Losses come from on-resistance (I^2 R) and from each switching edge. At 1,000+ A, tiny resistances add up to tens "
     "of watts, so FETs, packaging and cooling all matter. Makers: Infineon (IFNNY), onsemi (ON), Vishay (VSH), Alpha and "
     "Omega (AOSL), and power-stage vendors like Monolithic Power (MPWR)."),
]

X0, X1 = 152.0, 246.0
Z0 = -40.0
# y bands, bottom up
Y_DRAIN = (0.6, 4.0)
Y_SUB = (4.0, 14.0)
Y_DRIFT = (14.0, 32.0)
Y_BODY = (32.0, 39.0)
Y_SRC = (39.0, 42.0)
Y_MET = (43.5, 49.0)
TR_W = 5.0
N_TR = 6


def device(m, root):
    g = empty("fet", root)
    C.xsec(m, g, "fet_l", X0, X1, Z0, [(*Y_DRAIN, "alum"), (*Y_SUB, "nplus"), (*Y_DRIFT, "ndrift"), (*Y_BODY, "pbody"),
                                       (*Y_SRC, "nplus")])
    bx("fet_met", (X0, Y_MET[0], Z0), (X1, Y_MET[1], 0.0), m["alum"], g)
    pitch = (X1 - X0) / N_TR
    chan = empty("fet_chan", root)
    paths = []
    for k in range(N_TR):
        xc = X0 + pitch * (k + 0.5)
        a, b = xc - TR_W / 2, xc + TR_W / 2
        # trench: oxide liner, poly gate, oxide cap; it cuts down into the drift region
        bx(f"tr{k}_ox", (a, 28.0, Z0), (b, Y_SRC[1] + 0.01, 0.02), m["oxide"], g)
        bx(f"tr{k}_poly", (a + 0.8, 29.0, Z0), (b - 0.8, Y_SRC[1] - 0.3, 0.05), m["poly"], g)
        bx(f"tr{k}_cap", (a - 0.6, Y_SRC[1], Z0), (b + 0.6, Y_MET[0], 0.05), m["oxide"], g)
        # contacts between trenches: source metal down through the n+ to the body
        cx = xc + pitch / 2
        if k < N_TR - 1:
            bx(f"ct{k}", (cx - 1.6, Y_BODY[1] - 2.0, Z0), (cx + 1.6, Y_MET[0], 0.05), m["alum"], g)
        for s in (-1, 1):
            xe = xc + s * (TR_W / 2 + 0.35)
            bx(f"ch{k}{s}", (xe - 0.35, Y_BODY[0], Z0), (xe + 0.35, Y_BODY[1], 0.12), m["chan"], chan)
            paths.append([(xe, Y_MET[0] - 0.5, 1.0), (xe, Y_SRC[0], 1.0), (xe, Y_BODY[0], 1.0),
                          (xe + s * 3.0, Y_DRIFT[0] + 8.0, 1.0), (xe + s * 4.0, Y_DRAIN[1], 1.0)])
    # gate bus and source/drain pins out to the sides
    bx("fet_gpad", (X0 - 6.0, Y_MET[0], -12.0), (X0, Y_MET[0] + 2.0, -4.0), m["poly"], g)
    show(chan, [])
    pts = {"met": ((X0 + X1) / 2, Y_MET[1], -20.0), "drift": (X0 + 10.0, 24.0, 0.0), "body": (X0 + 30.0, 35.5, 0.0),
           "trench": (X0 + pitch / 2, 30.0, 0.0), "drain": (X1 - 10.0, 2.0, 0.0), "src": (X1 - 20.0, Y_MET[1], 0.0),
           "sub": (X0 + 60.0, 9.0, 0.0)}
    return pts, chan, paths


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root)
    ph, pk = b["ph"], b["pk"]
    pts, chan, paths = device(m, root)
    st = ph["st"][(1, 2)]
    C.magnify(m, root, st["top"], (X0 - 2.0, 30.0, -20.0))

    # beat 2: channel on, electrons down every cell
    show(chan, [(F(2, 0.15), F(3, 0))])
    for k, p in enumerate(paths):
        run(root, f"e{k}", p, 3, 0.8, m["e_blue"], 2, 0.2 + 0.02 * (k % 4), 0.9, 40)
    # beat 3: interleaved switching on every stage, current into the die
    order = [(s, k) for k in range(8) for s in (-1, 1)]
    for i, key_ in enumerate(order):
        blink(ph["sw"][key_], 3, [i % 8], n=8, on=0.45)
        blink(ph["sw"][key_], 4, [i % 8], n=8, on=0.45)
    for side in (-1, 1):
        run(root, f"amp{side}", D.front_path(side), 6, 1.2, m["amp"], [3, 4], 0.1, 0.9, 90)
    show(b["die_glow"], [(F(3, 0.3), F(5, 0))])
    # beat 4: heat off every stage and the big FET
    heat = empty("fet_heat", root)
    bx("fet_hot", (X0 + 1.0, Y_MET[1], Z0 + 1.0), (X1 - 1.0, Y_MET[1] + 0.8, -0.5), m["hot"], heat)
    show(heat, [(F(4, 0), F(5, 0))])
    rise(root, "h_fet", ((X0 + X1) / 2, Y_MET[1] + 1.0, -20.0), 8, 1.2, m["heat"], 4, 0.0, 0.85, 40.0, 70, (40.0, 15.0))
    for side in (-1, 1):
        for k in (0, 2, 4, 6):
            rise(root, f"h{side}{k}", ph["st"][(side, k)]["top"], 2, 0.8, m["heat"], 4, 0.05 * k, 0.9, 25.0, 60, (3.0, 3.0))

    C.tags(root, {
        0: [("power stage: 2 MOSFETs + driver", st["top"]), ("16 phases round the GPU", ph["ind"][(-1, 4)]["top"]),
            ("GPU package", pk["top"]), ("one FET, cut open", pts["met"])],
        1: [("source metal", pts["src"]), ("trench gate (poly in oxide)", pts["trench"]), ("p-body", pts["body"]),
            ("n- drift: blocks voltage", pts["drift"]), ("n+ substrate + drain", pts["drain"])],
        2: [("gate on: channel opens", pts["body"]), ("electrons to the drain", pts["drift"]), ("low Rds(on) = low loss", pts["met"])],
        3: [("phases take turns", ph["st"][(-1, 3)]["top"]), ("~1 MHz switching", ph["st"][(1, 5)]["top"]),
            ("1,000+ A into the GPU", pk["top"])],
        4: [("I^2 R + switching loss", pts["met"]), ("heat in every stage", ph["st"][(-1, 2)]["top"]), ("IFNNY, ON, VSH, AOSL", pts["sub"])],
    })
    cb = ((X0 + X1) / 2, 25.0, -12.0)
    C.done(SLUG, BEATS, [
        frame((40.0, 0.0, -90.0), 400.0, 0.30, 0.65, pad=1.0),
        frame(cb, 110.0, 0.25, 0.22),
        frame((X0 + 30.0, 28.0, -2.0), 60.0, 0.10, 0.08),
        frame((-10.0, 0.0, -90.0), 300.0, 0.15, 0.80, pad=1.0),
        frame((60.0, 10.0, -60.0), 330.0, 0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
