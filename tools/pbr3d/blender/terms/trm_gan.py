"""TRM_GAN on the MLCC base board: a GaN-on-silicon HEMT cut open on the bench, its 2DEG sheet
carrying electrons, then GaN versus silicon switching.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_gan.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_GAN"
BEATS = [
    ("GaN switches in the power path feeding the GPU",
     "Gallium nitride (GaN) transistors show up in the high-density power supplies and 48 V-to-12 V converters that feed "
     "AI boards, and increasingly in the phases round the GPU. They switch faster and lose less than silicon, so the "
     "same power fits in a smaller box."),
    ("A thin GaN film on a silicon wafer",
     "A GaN power transistor is built on an ordinary silicon wafer: buffer layers grade the crystal from silicon to GaN, "
     "then a GaN channel layer and a very thin AlGaN barrier on top. Source and drain contacts sit at the ends and the "
     "gate in between, with field plates to spread the high-voltage field."),
    ("Electrons race along a sheet only nanometres thick",
     "Where AlGaN meets GaN, the crystals' built-in polarization pulls a sheet of electrons into the interface: a "
     "two-dimensional electron gas (2DEG). Electrons there move very fast with no doping needed, so the device is a "
     "High Electron Mobility Transistor (HEMT). The gate pinches the sheet off to switch."),
    ("Faster switching: smaller inductors and capacitors",
     "Because GaN has tiny capacitance and no stored charge to clear, it switches several times faster than silicon "
     "with less loss per edge. Higher frequency lets designers shrink the magnetics and capacitors round it, and a power "
     "shelf packs more watts per rack unit."),
    ("Less heat per watt delivered",
     "Each switching edge costs less energy, so for the same load the GaN stage runs cooler. Players: Navitas (NVTS), "
     "Infineon (IFNNY, after buying GaN Systems), Texas Instruments (TXN), EPC, and for RF GaN Qorvo (QRVO) and Wolfspeed (WOLF)."),
]

X0, X1, Z0 = 152.0, 246.0, -40.0
Y_SI = (0.6, 14.0)
Y_BUF = (14.0, 22.0)
Y_GAN = (22.0, 34.0)
Y_2DEG = 34.0
Y_ALGAN = (34.0, 36.0)
Y_SIN = (36.0, 38.0)


def hemt(m, root):
    g = empty("hemt", root)
    C.xsec(m, g, "hm", X0, X1, Z0, [(*Y_SI, "si"), (*Y_GAN, "gan"), (*Y_ALGAN, "algan")])
    for k in range(8):  # graded buffer stripes
        y = Y_BUF[0] + k
        bx(f"buf{k}", (X0, y, Z0), (X1, y + 1.0, 0.0), m["aln" if k % 2 else "gan"], g)
    sx, dx, gx = X0 + 12.0, X1 - 12.0, X0 + 34.0
    bx("sin_l", (sx + 6.0, Y_SIN[0], Z0), (gx - 3.0, Y_SIN[1], 0.0), m["oxide"], g)
    bx("sin_r", (gx + 3.0, Y_SIN[0], Z0), (dx - 6.0, Y_SIN[1], 0.0), m["oxide"], g)
    for name, x in (("src", sx), ("drn", dx)):
        bx(name, (x - 6.0, Y_GAN[1] - 1.0, Z0), (x + 6.0, 44.0, 0.05), m["gold"], g)
    bx("gate", (gx - 2.0, Y_ALGAN[1], Z0), (gx + 2.0, 42.0, 0.05), m["nickel"], g)
    bx("gate_pgan", (gx - 2.0, Y_ALGAN[1], Z0), (gx + 2.0, Y_ALGAN[1] + 1.0, 0.06), m["pbody"], g)
    bx("fplate", (gx - 2.0, 42.0, Z0), (gx + 16.0, 43.5, 0.05), m["alum"], g)
    deg = empty("deg", root)
    bx("deg_b", (sx, Y_2DEG - 0.4, Z0), (dx, Y_2DEG + 0.1, 0.15), m["chan"], deg)
    show(deg, [])
    path = [(sx + 5.0, Y_2DEG, 1.0), (gx, Y_2DEG, 1.0), (dx - 5.0, Y_2DEG, 1.0)]
    pts = {"src": (sx, 44.0, -20.0), "drn": (dx, 44.0, -20.0), "gate": (gx, 42.0, 0.0), "si": (X0 + 60.0, 7.0, 0.0),
           "buf": (X0 + 70.0, 18.0, 0.0), "gan": (X0 + 70.0, 28.0, 0.0), "algan": (X0 + 60.0, 35.0, 0.0),
           "deg": (X0 + 55.0, Y_2DEG, 0.0), "fp": (gx + 10.0, 43.5, 0.0)}
    return pts, deg, path


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root)
    ph = b["ph"]
    pts, deg, path = hemt(m, root)
    C.magnify(m, root, ph["st"][(1, 1)]["top"], (X0 - 2.0, 30.0, -20.0))
    show(deg, [(F(2, 0.1), F(3, 0)), (F(3, 0), F(5, 0))])
    run(root, "e2", path, 12, 0.7, m["e_blue"], 2, 0.1, 0.95, 25)
    # beat 3: fast edges: the 2DEG flicks on and off, many times
    blink(deg, 3, [0, 2, 4, 6, 8, 10, 12, 14], n=16, on=0.5)
    order = [(s, k) for k in range(8) for s in (-1, 1)]
    for i, key_ in enumerate(order):
        blink(ph["sw"][key_], 3, [i % 16], n=16, on=0.5)
    for side in (-1, 1):
        run(root, f"amp{side}", D.front_path(side), 6, 1.2, m["amp"], [3, 4], 0.1, 0.9, 90)
    rise(root, "gh", ((X0 + X1) / 2, 45.0, -20.0), 3, 0.8, m["heat"], 4, 0.1, 0.8, 18.0, 60, (30.0, 10.0))

    C.tags(root, {
        0: [("phases + power shelves: GaN", ph["st"][(1, 1)]["top"]), ("one GaN HEMT, cut open", pts["src"]),
            ("GPU package", b["pk"]["top"])],
        1: [("silicon wafer", pts["si"]), ("graded buffer", pts["buf"]), ("GaN channel layer", pts["gan"]),
            ("thin AlGaN barrier", pts["algan"]), ("source / gate / drain", pts["drn"])],
        2: [("2DEG: electron sheet", pts["deg"]), ("no doping, very fast", pts["gan"]), ("gate pinches it off", pts["gate"])],
        3: [("switches ~MHz, sharp edges", pts["deg"]), ("smaller inductors and caps", ph["ind"][(-1, 3)]["top"])],
        4: [("cooler per watt", pts["src"]), ("NVTS, IFNNY, TXN, EPC", pts["si"])],
    })
    cb = ((X0 + X1) / 2, 28.0, -12.0)
    C.done(SLUG, BEATS, [
        frame((60.0, 5.0, -90.0), 380.0, 0.32, 0.6, pad=1.0),
        frame(cb, 110.0, 0.25, 0.18),
        frame((X0 + 45.0, 32.0, -6.0), 85.0, 0.15, 0.18),
        frame((60.0, 10.0, -60.0), 300.0, 0.22, 0.50, pad=1.0),
        frame(cb, 120.0, 0.30, 0.30),
    ], root)


if __name__ == "__main__":
    build()
