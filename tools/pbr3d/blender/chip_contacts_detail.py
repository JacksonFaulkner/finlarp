"""Detailed parts for the CONTACTS sections (chip_contacts.py sec1-sec10).

The sections build a cut-away of one transistor's middle of line at about 10 scene mm per nm,
not the schematic chip:

  device()  silicon, raised n+ source/drain epi, three metal gates (high-k, gate metal, SiN
            self-aligned cap, spacers), TiSi silicide on the epi, trench contacts (Ti/TiN liner
            round a tungsten core) on the source/drain, a gate contact through the cap, the oxide
            between them, and over that the etch stop, via0 and the M1 lines.
  plug()    a lone contact plug in a block of oxide, for the liner and metal comparisons.
  column()  a labelled bar for a quantity (resistivity, barrier height, revenue).

Camera and tag helpers come from chip_thin_metal_detail. Y up, the cut plane at z = 0, the camera
on +z; fill materials stop at z = -1 and the parts in them come forward to z = +1..+3.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, box, empty, mat, show  # noqa: E402
import chip_thin_metal_detail as T  # noqa: E402
from chip_thin_metal_detail import frame, glide, group, lined, span, sub, tags  # noqa: E402,F401

ZB = -1200.0
XA, XB = -1000.0, 1000.0
GX = (-600.0, 0.0, 600.0)  # gate centres
SX = (-300.0, 300.0)  # source and drain centres
GL = 80.0  # half the gate length
SP = 60.0  # spacer width
SI_Y0 = -500.0
EPI = (-220.0, 60.0, 110.0)  # epi bottom, shoulder, top
SIL = (110.0, 140.0)  # silicide
GATE_TOP, CAP_TOP, ILD0_TOP = 450.0, 600.0, 650.0
ES_TOP, V0_TOP, M1_TOP = 680.0, 880.0, 1160.0
TS_HALF = 100.0  # trench contact: 20 nm wide
LINER = 30.0  # Ti/TiN, 3 nm a side
M1_X = (-900.0, -600.0, -300.0, 0.0, 300.0, 600.0, 900.0)
M1_HALF = 70.0
GC_Z0 = -240.0  # the gate contact is a plug: it runs only this far back

LO = (XA, SI_Y0, ZB)
HI = (XB, M1_TOP, 0.0)


def materials(m):
    T.materials(m)
    m["epi"] = mat("c_epi_n", (0.40, 0.66, 0.42), rough=0.55)
    m["sil"] = mat("c_silicide", (0.86, 0.84, 0.98), metal=0.9, rough=0.15, emit=(0.6, 0.6, 0.9), strength=0.4)
    m["hik"] = mat("c_hik", (0.92, 0.84, 0.50), rough=0.5)
    m["gmetal"] = mat("c_gmetal", (0.36, 0.34, 0.46), metal=0.75, rough=0.35)
    m["spacer"] = mat("c_spacer", (0.40, 0.54, 0.52), rough=0.6)
    m["sin"] = mat("c_sin", (0.70, 0.84, 0.94), rough=0.45)
    m["ox"] = mat("c_ox", (0.66, 0.62, 0.55), rough=0.85)
    m["void"] = mat("c_void", (0.03, 0.03, 0.05), rough=0.9)
    m["mfp"] = mat("c_mfp", (1.0, 0.85, 0.30), emit=(1.0, 0.80, 0.25), strength=4.0)
    m["sbh"] = mat("c_sbh", (0.95, 0.32, 0.20), emit=(1.0, 0.30, 0.15), strength=0.5)
    m["e"] = mat("c_e", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=4.0)
    m["amat1"] = mat("c_amat1", (0.16, 0.40, 0.85), emit=(0.15, 0.38, 0.85), strength=0.3)
    m["amat2"] = mat("c_amat2", (0.22, 0.70, 0.62), emit=(0.20, 0.65, 0.58), strength=0.3)
    m["amat3"] = mat("c_amat3", (0.75, 0.75, 0.80), rough=0.5)
    return m


def device(m, parent, metal="w", liner=LINER, shown=None, seam=False):
    """The cut-away transistor and its contacts. `shown` maps part groups to intervals:
    'ild_full' (oxide filling the contact holes), 'sil', 'liner', 'core', 'gc' (gate contact),
    'beol' (etch stop, via0, M1); groups not named are always on. Returns pin points."""
    shown = shown or {}
    g = empty("device", parent)

    def part(name):
        return group(name, g, shown.get(name))

    box("si", (XA, SI_Y0, ZB), (XB, 0.0, -1.0), m["si"], g)
    for k, x in enumerate(SX):
        box(f"epi{k}", (x - 150, EPI[0], ZB), (x + 150, EPI[1], 1.0), m["epi"], g)
        box(f"epi_top{k}", (x - 110, EPI[1], ZB), (x + 110, EPI[2], 1.0), m["epi"], g)
    for k, x in enumerate(GX):
        box(f"hik{k}", (x - GL, 0.0, ZB), (x + GL, GATE_TOP, 0.5), m["hik"], g)
        box(f"gm{k}", (x - GL + 16, 16.0, ZB), (x + GL - 16, GATE_TOP + 0.5, 1.5), m["gmetal"], g)
        box(f"cap{k}", (x - GL, GATE_TOP, ZB), (x + GL, CAP_TOP, 0.5), m["sin"], g)
        for s in (-1, 1):
            a, b = sorted((x + s * GL, x + s * (GL + SP)))
            box(f"sp{k}{s}", (a, 0.0, ZB), (b, CAP_TOP, 0.5), m["spacer"], g)
    # oxide between the parts (ILD0): beside each contact, over the gates, and out at the ends
    for k, x in enumerate(SX):
        for a, b in ((x - 160, x - TS_HALF), (x + TS_HALF, x + 160)):
            box(f"ild_s{k}{a:.0f}", (a, EPI[1], ZB), (b, ILD0_TOP, -1.0), m["ox"], g)
    for k, x in enumerate(GX):
        box(f"ild_g{k}", (x - GL - SP, CAP_TOP, ZB), (x + GL + SP, ILD0_TOP, -1.0), m["ox"], g)
    box("ild_l", (XA, 0.0, ZB), (GX[0] - GL - SP, ILD0_TOP, -1.0), m["ox"], g)
    box("ild_r", (GX[2] + GL + SP, 0.0, ZB), (XB, ILD0_TOP, -1.0), m["ox"], g)
    if "ild_full" in shown:
        fill = part("ild_full")
        for k, x in enumerate(SX):
            box(f"ild_hole{k}", (x - TS_HALF, SIL[0], ZB), (x + TS_HALF, ILD0_TOP, -1.0), m["ox"], fill)
    sil = part("sil")
    for k, x in enumerate(SX):
        box(f"sil{k}", (x - 110, SIL[0], ZB), (x + 110, SIL[1], 2.0), m["sil"], sil)
    # trench contacts: liner (bottom and walls) and core, as separate groups so a process can
    # add them in turn
    lin = part("liner")
    core = part("core")
    for k, x in enumerate(SX):
        _contact(m, lin, core, f"ts{k}", x, SIL[1], ILD0_TOP, ZB, 0.0, metal, liner, seam)
    gc = part("gc")
    _contact(m, gc, gc, "gc", GX[1], GATE_TOP - 10, ILD0_TOP, GC_Z0, 0.0, metal, liner, False, half=60.0)
    beol = part("beol")
    box("es", (XA, ILD0_TOP, ZB), (XB, ES_TOP, -1.0), m["sin"], beol)
    box("ild1", (XA, ES_TOP, ZB), (XB, V0_TOP, -1.0), m["ox"], beol)
    for k, x in enumerate((SX[0], GX[1], SX[1])):
        lined(f"v0_{k}", (x - 55, ILD0_TOP - 2, -110.0), (x + 55, V0_TOP + 2, 0.0), 12.0, m["tan"], m["cu"], beol,
              liner=8.0, ml=m["co"], axis="y")
    edges = [XA] + [e for x in M1_X for e in (x - M1_HALF, x + M1_HALF)] + [XB]
    for k, x in enumerate(M1_X):
        lined(f"m1_{k}", (x - M1_HALF, V0_TOP, ZB), (x + M1_HALF, M1_TOP, 0.0), 12.0, m["tan"], m["cu"], beol,
              liner=8.0, ml=m["co"])
    for k in range(0, len(edges), 2):
        if edges[k + 1] - edges[k] > 1:
            box(f"m1gap{k}", (edges[k], V0_TOP, ZB), (edges[k + 1], M1_TOP, -1.0), m["lowk"], beol)
    d = SX[1]
    return dict(
        si=(-800.0, -300.0, 2.0), epi=(d + 60, -80.0, 3.0), sil=(d + 70, 125.0, 4.0), liner=(d - TS_HALF + 12, 380.0, 4.0),
        core=(d, 380.0, 4.0), gate=(GX[2], 250.0, 3.0), cap=(GX[2], 530.0, 3.0), spacer=(GX[2] - GL - 30, 300.0, 3.0),
        gc=(GX[1], 560.0, 4.0), v0=(d, 780.0, 4.0), m1=(d, 1020.0, 4.0), ild=(d + 130, 400.0, 2.0),
        chan=(GX[1], -40.0, 2.0), es=(-800.0, 665.0, 2.0),
    )


def _contact(m, lin_g, core_g, name, x, y0, y1, z0, z1, metal, liner, seam, half=TS_HALF):
    """A contact from y0 to y1, x +- half: the liner (walls and floor) in lin_g, the core in core_g."""
    if liner > 0:
        box(name + "_lf", (x - half, y0, z0), (x + half, y0 + liner, z1 + 1.0), m["tin"], lin_g)
        box(name + "_ll", (x - half, y0, z0), (x - half + liner, y1, z1 + 1.0), m["tin"], lin_g)
        box(name + "_lr", (x + half - liner, y0, z0), (x + half, y1, z1 + 1.0), m["tin"], lin_g)
    t = liner
    box(name + "_core", (x - half + t, y0 + t, z0), (x + half - t, y1 + 1.0, z1 + 2.0), m[metal], core_g)
    if seam:
        box(name + "_seam", (x - 6, y0 + t + 80, z0), (x + 6, y1 - 60, z1 + 3.0), m["void"], core_g)


def plug(m, parent, name, x, hole, liner, metal, lm="tin", seam=False, y0=0.0, y1=600.0, block=True):
    """A lone contact plug `hole` wide at x in an oxide block, its cut face at z = 0. Returns
    (core pin, liner pin, top y)."""
    g = empty(name, parent)
    h = hole / 2
    d = max(hole, 200.0)
    if block:
        box(name + "_base", (x - h - 120, y0 - 100, -d - 200), (x + h + 120, y0, -1.0), m["epi"], g)
        box(name + "_sil", (x - h - 20, y0 - 30, -d - 100), (x + h + 20, y0 + 1.0, 1.5), m["sil"], g)
        box(name + "_oxl", (x - h - 120, y0, -d - 200), (x - h, y1, -1.0), m["ox"], g)
        box(name + "_oxr", (x + h, y0, -d - 200), (x + h + 120, y1, -1.0), m["ox"], g)
        box(name + "_oxb", (x - h, y0, -d - 200), (x + h, y1, -d), m["ox"], g)
    if liner > 0:
        box(name + "_lin", (x - h, y0, -d), (x + h, y1, 1.0), m[lm], g)
    box(name + "_core", (x - h + liner, y0 + liner, -d + liner), (x + h - liner, y1 + 1.0, 2.0), m[metal], g)
    if seam:
        box(name + "_seam", (x - 5, y0 + 150, -d + liner), (x + 5, y1 - 80, 3.0), m["void"], g)
    return (x, (y0 + y1) * 0.55, 3.0), (x - h + 4, (y0 + y1) * 0.35, 3.0), y1


def column(m, parent, name, x, value, scale, mt, y0=0.0, w=160.0, d=160.0):
    """A bar `value * scale` tall standing on y0 at x, on a dark plinth. Returns its top pin."""
    g = empty(name, parent)
    h = value * scale
    box(name + "_plinth", (x - w / 2 - 20, y0 - 30, -d - 20), (x + w / 2 + 20, y0, 20.0), m["base"], g)
    box(name + "_bar", (x - w / 2, y0, -d), (x + w / 2, y0 + h, 0.0), mt, g)
    return (x, y0 + h - 30, 2.0), g


__all__ = ["device", "plug", "column", "materials", "frame", "glide", "group", "lined", "span", "sub", "tags",
           "LO", "HI", "SX", "GX", "F", "P", "ball", "box", "empty", "show"]
