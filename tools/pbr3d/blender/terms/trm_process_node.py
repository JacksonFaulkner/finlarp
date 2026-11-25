"""TRM_PROCESS_NODE: three transistor generations side by side on a bench, each cut open at the
front: a planar MOSFET (gate on top of a flat channel), a FinFET (gate wrapped over two fins) and a
gate-all-around transistor (three stacked nanosheets with gate between them). Behind each stands a
density panel: the same square millimetre, holding more glowing transistors per generation.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_process_node.py

Beats:
  0 lineup   the three generations and their node names
  1 planar   electrons cross the surface channel; leakage sneaks underneath
  2 finfet   the gate wraps the fin on three sides; current runs through the fins
  3 gaa      nanosheets fully wrapped; current through every sheet
  4 density  the panels light: more transistors per mm2; who can build it
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_PROCESS_NODE"
BEATS = [
    ("A process node is a generation of chip-making technology",
     "Names like 28nm, TSMC N5, N3, N2 or Intel 18A label generations of manufacturing. They stopped matching any "
     "real dimension around 2010; now they mark steps in how densely transistors pack and how fast and efficiently "
     "they switch. The biggest changes came from the transistor's shape: planar, then FinFET, now gate-all-around."),
    ("Planar: the gate sits on top of a flat channel",
     "In a planar transistor the gate presses down on a flat strip of silicon between source and drain. Voltage on "
     "the gate opens a thin channel at the surface and electrons flow. Shrink it below ~20nm and the gate loses grip: "
     "current leaks underneath even when the switch is off, wasting power as heat."),
    ("FinFET: the channel stands up as a fin, gate on three sides",
     "From 22/16nm (2012-2015) the channel became a thin vertical fin and the gate drapes over it, controlling it from "
     "three sides. Leakage dropped and the fins could be packed tightly, which carried the industry from 16nm through "
     "TSMC N3. Two or three fins side by side make one stronger transistor."),
    ("Gate-all-around: stacked nanosheets, gate on every side",
     "At TSMC N2, Samsung 3nm and Intel 18A the fin is replaced by a stack of thin horizontal silicon sheets, with gate "
     "material filling the gaps so it surrounds each sheet completely. Better control means lower voltage and less "
     "leakage at the same speed; sheet width can be tuned per transistor."),
    ("Each node packs more transistors per mm2 for 10-30% better power or speed",
     "A new node typically gives 10-30% more speed or lower power and a density gain, at a much higher wafer price "
     "(a leading-edge wafer is $20k-30k). AI accelerators, CPUs and phone chips move first. Only TSMC (TSM), Samsung "
     "and Intel (INTC) build at the leading edge; NVIDIA (NVDA) and Apple (AAPL) are TSMC's biggest leading-node buyers."),
]

XS = {"planar": -125.0, "fin": 0.0, "gaa": 125.0}
HW = 42.0  # half width of each device block
ZB = -44.0  # back of the device blocks
PZ = -70.0  # density panel plane


def mats(m):
    m["gate"] = mat("pn_gate", (0.62, 0.30, 0.28), metal=0.5, rough=0.35)
    m["metalg"] = mat("pn_metalg", (0.55, 0.58, 0.66), metal=0.9, rough=0.25)
    m["hk"] = mat("pn_hk", (0.90, 0.85, 0.50), rough=0.3)
    m["sd"] = mat("pn_sd", (0.30, 0.45, 0.80), metal=0.3, rough=0.4)
    m["sti"] = mat("pn_sti", (0.80, 0.86, 0.92), rough=0.25)
    m["e"] = mat("pn_e", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=4.0)
    m["leak"] = mat("pn_leak", (1.0, 0.30, 0.15), emit=(1.0, 0.25, 0.10), strength=4.0)
    m["chg"] = mat("pn_chan", (0.40, 0.85, 1.0), emit=(0.35, 0.80, 1.0), strength=1.3)
    m["cellg"] = mat("pn_cell", (0.45, 1.0, 0.60), emit=(0.40, 1.0, 0.55), strength=2.5)
    m["plate"] = mat("pn_plate", (0.85, 0.85, 0.80), rough=0.6)


def bench(m, root):
    g = empty("bench", root)
    bx("bench_top", (-200.0, -26.0, -95.0), (200.0, -22.0, 22.0), m["dark"], g)
    for name, x in XS.items():
        bx(f"{name}_plinth", (x - HW - 4.0, -22.0, ZB - 4.0), (x + HW + 4.0, -20.0, 4.0), m["grid"], g)
        bx(f"{name}_plate", (x - 18.0, -21.9, 6.0), (x + 18.0, -21.0, 14.0), m["plate"], g)


def substrate(m, g, name, x, sti=True):
    bx(f"{name}_sub", (x - HW, -20.0, ZB), (x + HW, -4.0, 0.0), m["si"], g)
    if sti:  # shallow trench isolation at both ends
        for s in (-1, 1):
            bx(f"{name}_sti{s}", (x + s * HW, -12.0, ZB), (x + s * (HW - 5.0), 0.0, 0.0), m["sti"], g)


def planar(m, root):
    x = XS["planar"]
    g = empty("planar", root)
    substrate(m, g, "pl", x)
    bx("pl_well", (x - HW + 5.0, -4.0, ZB), (x + HW - 5.0, 0.0, 0.0), m["pbody"], g)
    for s in (-1, 1):  # source / drain wells and their contacts
        bx(f"pl_sd{s}", (x + s * 10.0, -6.0, ZB), (x + s * (HW - 5.0), 0.1, 0.0), m["sd"], g)
        bx(f"pl_ct{s}", (x + s * 20.0, 0.1, -30.0), (x + s * 28.0, 22.0, -6.0), m["tin"], g)
        bx(f"pl_sp{s}", (x + s * 8.0, 0.1, ZB), (x + s * 10.5, 14.0, 0.0), m["sti"], g)
    bx("pl_ox", (x - 8.0, 0.0, ZB), (x + 8.0, 0.8, 0.0), m["oxide"], g)
    bx("pl_gate", (x - 8.0, 0.8, ZB), (x + 8.0, 14.0, 0.0), m["gate"], g)
    bx("pl_gc", (x - 4.0, 14.0, -30.0), (x + 4.0, 22.0, -10.0), m["tin"], g)
    ch = empty("pl_chan", root)
    bx("pl_ch", (x - 10.0, -1.2, ZB + 1.0), (x + 10.0, 0.05, 0.15), m["chg"], ch)
    show(ch, [(F(1, 0.15), F(2, 0)), (F(4, 0), F(5, 0))])
    run(root, "pl_e", [(x - 30.0, -1.0, 1.0), (x - 10.0, -0.6, 1.0), (x + 10.0, -0.6, 1.0), (x + 30.0, -1.0, 1.0)],
        8, 1.0, m["e"], [1, 4], 0.15, 0.85, 40)
    run(root, "pl_leak", [(x - 26.0, -4.0, 1.0), (x - 8.0, -10.0, 1.0), (x + 8.0, -10.0, 1.0), (x + 26.0, -4.0, 1.0)],
        5, 0.9, m["leak"], [1], 0.35, 0.95, 45)
    rise(root, "pl_heat", (x, 14.0, -20.0), 4, 0.9, m["heat"], 1, 0.4, 0.95, 20.0, 50, (6.0, 8.0))
    return {"gate": (x, 14.0, -10.0), "ch": (x, 0.0, 0.0), "leak": (x, -10.0, 0.0), "sd": (x + 28.0, 0.0, 0.0),
            "c": (x, 4.0, -18.0)}


def finfet(m, root):
    x = XS["fin"]
    g = empty("finfet", root)
    substrate(m, g, "ff", x, sti=False)
    bx("ff_sti", (x - HW, -4.0, ZB), (x + HW, 0.0, 0.0), m["sti"], g)
    fins = (-10.0, -30.0)  # fin centre z; width 5
    fh = 18.0
    for k, zc in enumerate(fins):
        bx(f"ff_fin{k}", (x - HW + 4.0, -4.0, zc - 2.5), (x + HW - 4.0, fh, zc + 2.5), m["si"], g)
        for s in (-1, 1):  # epitaxial source / drain grown over the fin ends
            bx(f"ff_epi{k}{s}", (x + s * (HW - 14.0), 0.0, zc - 3.5), (x + s * (HW - 4.0), fh + 1.0, zc + 3.5), m["sd"], g)
    for s in (-1, 1):
        bx(f"ff_ct{s}", (x + s * (HW - 12.0), fh + 1.0, -34.0), (x + s * (HW - 6.0), fh + 7.0, -6.0), m["tin"], g)
    # the gate: high-k liner + metal over the top and down the back and middle; the front wall is
    # cut away so the front fin shows inside it
    gx0, gx1 = x - 9.0, x + 9.0
    bx("ff_hk_top", (gx0, fh, ZB + 2.0), (gx1, fh + 1.0, -7.0), m["hk"], g)
    bx("ff_g_top", (gx0, fh + 1.0, ZB + 2.0), (gx1, fh + 10.0, -7.0), m["metalg"], g)
    bx("ff_g_mid", (gx0, 0.0, -26.5), (gx1, fh, -13.5), m["metalg"], g)
    bx("ff_g_back", (gx0, 0.0, ZB + 2.0), (gx1, fh, -33.5), m["metalg"], g)
    for zc in fins:
        for s in (-1, 1):
            if zc == fins[0] and s == 1:
                continue
            bx(f"ff_hk{zc:.0f}{s}", (gx0, 0.0, zc + s * 2.5), (gx1, fh, zc + s * 3.5), m["hk"], g)
    ch = empty("ff_chan", root)
    bx("ff_ch", (gx0, 1.0, -7.5), (gx1, fh - 1.0, -7.3), m["chg"], ch)
    show(ch, [(F(2, 0.2), F(3, 0)), (F(4, 0), F(5, 0))])
    for k, y in enumerate((5.0, 10.0, 15.0)):
        run(root, f"ff_e{k}", [(x - 34.0, y, -7.0), (x + 34.0, y, -7.0)], 5, 0.9, m["e"], [2, 4], 0.1 + 0.05 * k, 0.9, 40)
    return {"gate": (x, fh + 10.0, -20.0), "fin": (x - 20.0, fh, -7.5), "hk": (x + 9.0, fh, -7.0),
            "epi": (x + 32.0, fh + 1.0, -6.5), "c": (x, 8.0, -18.0)}


def gaa(m, root):
    x = XS["gaa"]
    g = empty("gaa", root)
    substrate(m, g, "ga", x, sti=False)
    bx("ga_sti", (x - HW, -4.0, ZB), (x + HW, 0.0, 0.0), m["sti"], g)
    sz0, sz1 = -32.0, -6.0  # sheet width in z
    ys = (3.0, 9.0, 15.0)  # sheet bottoms, 3 thick, 3 gap
    for k, y in enumerate(ys):
        bx(f"ga_sh{k}", (x - HW + 6.0, y, sz0), (x + HW - 6.0, y + 3.0, sz1), m["si"], g)
    for s in (-1, 1):
        bx(f"ga_sd{s}", (x + s * 13.0, 0.0, sz0 - 2.0), (x + s * (HW - 4.0), 21.0, sz1 + 2.0), m["sd"], g)
        bx(f"ga_ct{s}", (x + s * 22.0, 21.0, -30.0), (x + s * 32.0, 27.0, -8.0), m["tin"], g)
        bx(f"ga_isp{s}", (x + s * 9.0, 0.0, sz0), (x + s * 11.0, 18.0, sz1), m["sti"], g)
    gx0, gx1 = x - 9.0, x + 9.0
    # gate fills under, between and above every sheet, and wraps the back; front face cut open
    gaps = [(0.0, 3.0)] + [(ys[k] + 3.0, ys[k + 1]) for k in range(2)] + [(ys[2] + 3.0, 28.0)]
    for k, (y0, y1) in enumerate(gaps):
        bx(f"ga_hk{k}", (gx0, y0, sz0), (gx1, y0 + 0.6, sz1), m["hk"], g)
        bx(f"ga_g{k}", (gx0, y0 + 0.6, sz0), (gx1, y1 - (0.6 if k < 3 else 0.0), sz1), m["metalg"], g)
        if k < 3:
            bx(f"ga_hkt{k}", (gx0, y1 - 0.6, sz0), (gx1, y1, sz1), m["hk"], g)
    bx("ga_back", (gx0, 0.0, ZB + 2.0), (gx1, 28.0, sz0), m["metalg"], g)
    ch = empty("ga_chan", root)
    for k, y in enumerate(ys):
        bx(f"ga_ch{k}", (gx0 - 1.0, y + 0.2, sz1 - 0.2), (gx1 + 1.0, y + 2.8, sz1 + 0.15), m["chg"], ch)
    show(ch, [(F(3, 0.2), F(4, 0)), (F(4, 0), F(5, 0))])
    for k, y in enumerate(ys):
        run(root, f"ga_e{k}", [(x - 34.0, y + 1.5, -5.0), (x + 34.0, y + 1.5, -5.0)], 5, 0.9, m["e"], [3, 4], 0.1 + 0.05 * k, 0.9, 40)
    return {"gate": (x, 28.0, -20.0), "sheet": (x - 22.0, 18.0, -6.0), "gap": (x, 12.0, 0.0),
            "sd": (x + 30.0, 21.0, -6.0), "c": (x, 10.0, -18.0)}


def panels(m, root):
    """A 'one square millimetre' panel behind each device, filled with a grid of cells."""
    out = []
    for (name, x), n in zip(XS.items(), (3, 7, 10)):
        g = empty(f"pan_{name}", root)
        bx(f"pan_{name}_f", (x - 32.0, 30.0, PZ - 2.0), (x + 32.0, 94.0, PZ), m["dark"], g)
        bx(f"pan_{name}_leg", (x - 2.0, -20.0, PZ - 2.0), (x + 2.0, 30.0, PZ), m["dark"], g)
        cells = empty(f"pan_{name}_c", root)
        p = 56.0 / n
        for i in range(n):
            for j in range(n):
                cx, cy = x - 28.0 + p * (i + 0.5), 34.0 + p * (j + 0.5)
                bx(f"pan_{name}_{i}_{j}", (cx - p * 0.35, cy - p * 0.35, PZ), (cx + p * 0.35, cy + p * 0.35, PZ + 0.4), m["cellg"], cells)
        show(cells, [(F(0, 0), F(1, 0)), (F(4, 0.1), F(5, 0))])
        out.append((x, 94.0, PZ))
    return out


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bench(m, root)
    pl, ff, ga = planar(m, root), finfet(m, root), gaa(m, root)
    pan = panels(m, root)
    C.tags(root, {
        0: [("planar: 28nm era", (XS["planar"], 24.0, 10.0)), ("FinFET: 16nm to N3", (XS["fin"], 30.0, 10.0)),
            ("gate-all-around: N2, 18A", (XS["gaa"], 30.0, 10.0)), ("same 1 mm2, more transistors", pan[1])],
        1: [("gate on top only", pl["gate"]), ("surface channel opens", pl["ch"]),
            ("leakage underneath", pl["leak"]), ("source / drain", pl["sd"])],
        2: [("gate wraps 3 sides", ff["gate"]), ("silicon fin", ff["fin"]), ("high-k liner", ff["hk"]),
            ("epitaxial drain", ff["epi"])],
        3: [("gate on all 4 sides", ga["gate"]), ("3 stacked nanosheets", ga["sheet"]),
            ("gate fills the gaps", ga["gap"]), ("source / drain", ga["sd"])],
        4: [("~15 MTr/mm2", pan[0]), ("~140 MTr/mm2 (N5)", pan[1]), ("~250 MTr/mm2 (N2 est.)", pan[2]),
            ("TSMC, Samsung, Intel", (XS["fin"], -20.0, 14.0))],
    })
    C.done(SLUG, BEATS, [
        frame((10.0, 30.0, -30.0), 380.0, 0.20, 0.30, pad=1.15),
        frame(pl["c"], 100.0, 0.30, 0.25),
        frame(ff["c"], 100.0, 0.30, 0.30),
        frame(ga["c"], 100.0, 0.30, 0.25),
        frame((10.0, 40.0, -40.0), 380.0, -0.15, 0.25, pad=1.15),
    ], root)


if __name__ == "__main__":
    build()
