"""TRM_WFE: a fab floor cut open, one bay per tool family: an EUV scanner (light source, mask,
optics, wafer stage), a deposition chamber and an etch chamber with their plasmas, and an
inspection tool scanning a wafer. Wafer pods ride an overhead rail between them; in the last beat
capex beads flow from the chipmakers' budget into every tool.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_wfe.py

Beats:
  0 floor    the bays and the overhead rail carrying wafer pods
  1 litho    the scanner prints a layer: light, mask, mirrors, wafer
  2 dep/etch deposition adds a film, etch cuts it; plasma glows
  3 control  inspection scans every wafer for defects
  4 capex    the money: ~$100B a year, split by tool type
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_WFE"
BEATS = [
    ("WFE is the tools that make chips, inside every fab",
     "Wafer fab equipment (WFE) is the machinery that processes wafers: lithography, deposition, etch, cleaning, "
     "implant, polishing and process control. A leading-edge fab holds a thousand or more tools, and wafers shuttle "
     "between them in sealed pods on overhead rails for months. Equipment is most of what a new fab costs."),
    ("Lithography prints each layer's pattern",
     "A scanner shines light through a photomask and shrinks the pattern onto the wafer's resist, field by field. "
     "EUV scanners use 13.5nm light made by blasting tin droplets with a laser and steered by mirrors, cost roughly "
     "$200M+ each, and come from one company: ASML (ASML). Litho is about a fifth to a quarter of WFE."),
    ("Deposition lays films down; etch carves them",
     "Deposition chambers grow thin films of metal or insulator a few atoms at a time (CVD, ALD, PVD). Etch chambers "
     "use plasma to cut the printed pattern into those films. Each chip layer cycles through both, so they are the "
     "biggest slice of WFE: Applied Materials (AMAT), Lam Research (LRCX) and Tokyo Electron lead."),
    ("Process control inspects and measures every step",
     "Inspection and metrology tools scan wafers with light and electron beams to find defects and check film "
     "thickness and overlay. Catching a problem early saves whole lots of wafers, so spending here rises with each "
     "node's complexity. KLA (KLAC) dominates this segment."),
    ("About $100B a year, driven by foundry and memory capex",
     "WFE is the bulk of chipmakers' capital spending, roughly $100B+ a year. It follows foundry and memory capex: "
     "AI demand for leading-edge logic (TSMC) and HBM memory (SK hynix, Micron, Samsung) lifts orders, and China "
     "has been a large buyer. Related: ASML (ASML), AMAT, LRCX, KLAC, Tokyo Electron."),
]

BAYS = {"litho": (-190.0, -70.0), "dep": (-55.0, 5.0), "etch": (20.0, 80.0), "insp": (95.0, 165.0)}
RAIL_Y = 92.0
RZ = -20.0


def mats(m):
    m["shell"] = mat("wf_shell", (0.86, 0.88, 0.90), rough=0.5)
    m["wafer"] = mat("wf_wafer", (0.45, 0.47, 0.60), metal=0.8, rough=0.15)
    m["euv"] = mat("wf_euv", (0.75, 0.55, 1.0), emit=(0.70, 0.50, 1.0), strength=4.0)
    m["plasma_d"] = mat("wf_pd", (0.40, 0.75, 1.0), emit=(0.35, 0.70, 1.0), strength=2.5)
    m["plasma_e"] = mat("wf_pe", (1.0, 0.45, 0.85), emit=(1.0, 0.40, 0.80), strength=2.5)
    m["scan"] = mat("wf_scan", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=4.0)
    m["cash"] = mat("wf_cash", (0.55, 1.0, 0.45), emit=(0.50, 1.0, 0.40), strength=4.0)
    m["foup"] = mat("wf_foup", (0.85, 0.60, 0.25), rough=0.5)
    m["mirror"] = mat("wf_mirror", (0.85, 0.87, 0.92), metal=1.0, rough=0.05)


def floor(m, root):
    g = empty("floor", root)
    bx("raised", (-205.0, -4.0, -110.0), (180.0, 0.0, 25.0), m["grid"], g)
    bx("wall", (-205.0, 0.0, -110.0), (180.0, 110.0, -106.0), m["shell"], g)
    for k in range(16):  # raised-floor tile seams
        x = -205.0 + 24.0 * k
        bx(f"seam{k}", (x, 0.0, -106.0), (x + 0.4, 0.1, 25.0), m["dark"], g)
    # overhead hoist rail with hangers
    bx("rail", (-200.0, RAIL_Y, RZ - 2.0), (175.0, RAIL_Y + 2.0, RZ + 2.0), m["steel"], g)
    for k in range(8):
        x = -190.0 + 50.0 * k
        bx(f"hang{k}", (x - 0.6, RAIL_Y + 2.0, RZ - 0.6), (x + 0.6, 110.0, RZ + 0.6), m["steel"], g)
    pods = []
    for k in range(4):
        o = empty(f"pod{k}", root)
        bx(f"pod{k}_b", (-6.0, -10.0, -6.0), (6.0, 0.0, 6.0), m["foup"], o)
        bx(f"pod{k}_h", (-3.0, 0.0, -3.0), (3.0, 2.0, 3.0), m["steel"], o)
        pods.append(o)
    # pods glide along the rail through every beat
    from sand_overview import P, key
    for k, o in enumerate(pods):
        for b in range(5):
            x0 = -190.0 + 95.0 * k + 20.0 * b
            x1 = x0 + 60.0
            key(o, F(b, 0), "location", P(x0 if x0 < 170 else x0 - 360, RAIL_Y, RZ), linear=True)
            key(o, F(b + 1, 0) - 1, "location", P(x1 if x1 < 170 else x1 - 360, RAIL_Y, RZ), linear=True)
    return g


def bay(m, g, name, x0, x1, h=72.0):
    """A tool body cut open at the front: back, sides, roof, a load port at the rail side."""
    bx(f"{name}_back", (x0, 0.0, -70.0), (x1, h, -66.0), m["shell"], g)
    bx(f"{name}_roof", (x0, h, -70.0), (x1, h + 4.0, -10.0), m["shell"], g)
    for s, x in ((-1, x0), (1, x1)):
        bx(f"{name}_side{s}", (x, 0.0, -70.0), (x - s * 3.0, h, -10.0), m["shell"], g)
    bx(f"{name}_port", (x1 - 16.0, 0.0, -10.0), (x1 - 3.0, 26.0, 2.0), m["alu"], g)
    bx(f"{name}_led", (x1 - 12.0, 22.0, 2.0), (x1 - 7.0, 24.0, 2.3), m["scan"], g)


def litho(m, root):
    x0, x1 = BAYS["litho"]
    g = empty("litho", root)
    bay(m, g, "li", x0, x1, 80.0)
    # tin-plasma source vessel on the left, collector mirror
    D.tube("li_src", (x0 + 18.0, 8.0, -40.0), (x0 + 18.0, 50.0, -40.0), 13.0, m["steel"], g, 32)
    bx("li_coll", (x0 + 28.0, 26.0, -50.0), (x0 + 31.0, 44.0, -30.0), m["mirror"], g)
    # reticle stage up top, projection mirrors, wafer stage at the bottom
    bx("li_rs", (x0 + 56.0, 66.0, -56.0), (x0 + 96.0, 70.0, -24.0), m["dark"], g)
    bx("li_ret", (x0 + 68.0, 64.0, -48.0), (x0 + 86.0, 66.0, -32.0), m["quartz_c"], g)
    for k, (mx, my) in enumerate(((x0 + 62.0, 46.0), (x0 + 90.0, 34.0), (x0 + 66.0, 22.0))):
        bx(f"li_m{k}", (mx - 7.0, my - 1.0, -50.0), (mx + 7.0, my + 1.0, -30.0), m["mirror"], g)
    bx("li_ws", (x0 + 56.0, 0.0, -58.0), (x0 + 100.0, 8.0, -22.0), m["dark"], g)
    wafer = empty("li_wafer", root)
    D.tube("li_wd", (x0 + 77.0, 8.0, -40.0), (x0 + 77.0, 9.0, -40.0), 14.0, m["wafer"], wafer, 48)
    drop = empty("li_drop", root)
    D.tube("li_pl", (x0 + 18.0, 30.0, -40.0), (x0 + 18.0, 32.0, -40.0), 4.0, m["euv"], drop, 16)
    blink(drop, 1, list(range(16)), n=16, on=0.5)
    blink(drop, 4, list(range(8)), n=8, on=0.5)
    beam = [(x0 + 22.0, 32.0, -40.0), (x0 + 30.0, 36.0, -40.0), (x0 + 76.0, 64.0, -40.0), (x0 + 62.0, 47.0, -40.0),
            (x0 + 90.0, 35.0, -40.0), (x0 + 66.0, 23.0, -40.0), (x0 + 77.0, 9.0, -40.0)]
    bm = empty("li_bm", root)
    D.polyline("li_bml", beam, 0.5, m["euv"], bm)
    show(bm, [(F(1, 0.1), F(2, 0)), (F(4, 0), F(5, 0))])
    run(root, "li_beam", beam, 14, 0.9, m["euv"], [1, 4], 0.05, 0.95, 40)
    run(root, "li_beam0", beam, 5, 0.9, m["euv"], [0], 0.1, 0.9, 40)
    return {"src": (x0 + 18.0, 50.0, -27.0), "ret": (x0 + 77.0, 70.0, -30.0), "mir": (x0 + 90.0, 35.0, -30.0),
            "wafer": (x0 + 77.0, 9.0, -26.0), "top": ((x0 + x1) / 2, 84.0, -40.0), "c": ((x0 + x1) / 2, 40.0, -40.0)}


def chamber(m, root, name, x0, x1, plasma, beat_on, film):
    g = empty(name, root)
    bay(m, g, name, x0, x1, 72.0)
    xc = (x0 + x1) / 2
    # vacuum chamber: a cylinder cut in half (we draw the back half wall as boxes) with showerhead
    bx(f"{name}_cb", (xc - 20.0, 10.0, -54.0), (xc + 20.0, 46.0, -50.0), m["steel"], g)
    for s in (-1, 1):
        bx(f"{name}_cw{s}", (xc + s * 20.0, 10.0, -54.0), (xc + s * 22.0, 46.0, -14.0), m["steel"], g)
    bx(f"{name}_lid", (xc - 22.0, 46.0, -54.0), (xc + 22.0, 50.0, -14.0), m["steel"], g)
    bx(f"{name}_shw", (xc - 16.0, 40.0, -48.0), (xc + 16.0, 42.0, -20.0), m["alu"], g)
    for k in range(7):
        bx(f"{name}_hole{k}", (xc - 13.0 + 4.3 * k, 39.6, -40.0), (xc - 12.0 + 4.3 * k, 40.0, -28.0), m["dark"], g)
    bx(f"{name}_chuck", (xc - 15.0, 0.0, -46.0), (xc + 15.0, 16.0, -22.0), m["dark"], g)
    D.tube(f"{name}_wd", (xc, 16.0, -34.0), (xc, 17.0, -34.0), 13.0, m["wafer"], g, 48)
    bx(f"{name}_pump", (xc - 6.0, 50.0, -40.0), (xc + 6.0, 64.0, -28.0), m["alu"], g)
    pl = empty(f"{name}_plasma", root)
    bx(f"{name}_pb", (xc - 14.0, 19.0, -44.0), (xc + 14.0, 38.0, -24.0), m[plasma], pl)
    show(pl, [(F(beat_on, 0.1), F(beat_on + 1, 0)), (F(4, 0), F(5, 0))])
    fl = empty(f"{name}_film", root)
    bx(f"{name}_fb", (xc - 13.0, 17.0, -46.0), (xc + 13.0, 18.2, -22.0), m[film], fl)
    show(fl, [(F(beat_on, 0.5), F(5, 0))])
    run(root, f"{name}_gas", [(xc, 62.0, -34.0), (xc, 42.0, -34.0), (xc + 6.0, 20.0, -30.0)], 8, 0.8, m[plasma],
        [beat_on], 0.05, 0.9, 30)
    return {"pl": (xc + 14.0, 30.0, -24.0), "shw": (xc - 16.0, 42.0, -20.0), "film": (xc - 13.0, 18.0, -22.0),
            "top": (xc, 76.0, -40.0), "c": (xc, 34.0, -36.0)}


def inspect(m, root):
    x0, x1 = BAYS["insp"]
    g = empty("insp", root)
    bay(m, g, "in", x0, x1, 72.0)
    xc = (x0 + x1) / 2
    bx("in_gran", (x0 + 6.0, 0.0, -60.0), (x1 - 6.0, 12.0, -16.0), m["dark"], g)
    bx("in_gx", (x0 + 6.0, 44.0, -40.0), (x1 - 6.0, 50.0, -34.0), m["steel"], g)
    bx("in_col", (xc - 5.0, 28.0, -42.0), (xc + 5.0, 44.0, -32.0), m["alu"], g)
    D.tube("in_wd", (xc, 12.0, -38.0), (xc, 13.0, -38.0), 18.0, m["wafer"], g, 48)
    # a wafer map: a few defects lit red as the scan passes
    dmap = empty("in_def", root)
    for k, (dx, dz) in enumerate(((-8.0, -6.0), (5.0, 8.0), (11.0, -9.0), (-3.0, 12.0))):
        bx(f"in_d{k}", (xc + dx - 1.0, 13.0, -38.0 + dz - 1.0), (xc + dx + 1.0, 13.6, -38.0 + dz + 1.0), m["warn"], dmap)
    show(dmap, [(F(3, 0.5), F(5, 0))])
    beam = empty("in_beam", root)
    D.tube("in_b", (xc, 28.0, -37.0), (xc, 13.2, -37.0), 0.6, m["scan"], beam, 8)
    show(beam, [(F(3, 0.1), F(4, 0))])
    C.rings(m, root, "in_sweep", (xc, 13.4, -38.0), 3, n=3, r0=2.0, r1=18.0, mt="scan", axis="xz")
    bx("in_scr", (x1 - 2.0, 30.0, -60.0), (x1 + 0.5, 50.0, -30.0), m["screen"], g)
    return {"col": (xc + 5.0, 40.0, -32.0), "wafer": (xc + 18.0, 13.0, -38.0), "def": (xc + 11.0, 13.6, -47.0),
            "top": (xc, 76.0, -40.0), "c": (xc, 30.0, -38.0)}


def capex(m, root):
    """Budget beads from a 'capex' block in front, splitting to every tool, sized by WFE share."""
    g = empty("capex", root)
    bx("cx_b", (-30.0, 0.0, 6.0), (10.0, 10.0, 22.0), m["dark"], g)
    bx("cx_t", (-24.0, 10.0, 11.0), (4.0, 10.6, 17.0), m["cash"], g)
    src = (-10.0, 11.0, 14.0)
    for name, n in (("litho", 7), ("dep", 9), ("etch", 9), ("insp", 4)):
        x0, x1 = BAYS[name]
        tgt = (x1 - 9.0, 26.0, -4.0)
        run(root, f"cx_{name}", [src, ((src[0] + tgt[0]) / 2, 40.0, 4.0), tgt], n, 1.1, m["cash"], [4], 0.05, 0.9, 40)
    return {"box": (-10.0, 10.6, 20.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    floor(m, root)
    li = litho(m, root)
    dp = chamber(m, root, "dep", *BAYS["dep"], "plasma_d", 2, "alum")
    et = chamber(m, root, "etch", *BAYS["etch"], "plasma_e", 2, "copper")
    ins = inspect(m, root)
    cx = capex(m, root)
    C.tags(root, {
        0: [("lithography", li["top"]), ("deposition", dp["top"]), ("etch", et["top"]),
            ("inspection", ins["top"]), ("wafer pods on a rail", (-60.0, RAIL_Y + 2.0, RZ))],
        1: [("EUV light from tin plasma", li["src"]), ("photomask", li["ret"]), ("mirror optics", li["mir"]),
            ("wafer gets the pattern", li["wafer"])],
        2: [("deposition: add a film", dp["pl"]), ("gas through showerhead", dp["shw"]),
            ("etch: plasma cuts it", et["pl"]), ("AMAT, LRCX, Tokyo Electron", et["top"])],
        3: [("light / e-beam scan", ins["col"]), ("defects found and mapped", ins["def"]), ("KLA leads", ins["top"])],
        4: [("~$100B a year of tools", cx["box"]), ("litho ~1/4: ASML", li["top"]),
            ("dep + etch: biggest slice", dp["top"]), ("process control: KLAC", ins["top"])],
    })
    C.done(SLUG, BEATS, [
        frame((-10.0, 50.0, -40.0), 380.0, 0.15, 0.30, pad=0.9),
        frame(li["c"], 130.0, 0.15, 0.15),
        frame((12.0, 34.0, -36.0), 150.0, 0.15, 0.20),
        frame(ins["c"], 90.0, 0.20, 0.35),
        frame((-10.0, 45.0, -30.0), 380.0, -0.10, 0.35, pad=0.9),
    ], root)


if __name__ == "__main__":
    build()
