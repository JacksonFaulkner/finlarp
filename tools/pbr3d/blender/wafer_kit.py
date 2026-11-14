"""The WAFER pictures' shared pieces (overview, zooms, sections), built on the sand and poly helpers
the MELT pictures use (see melt_kit.py). Units are millimetres, Y up, cut-away at z = 0, the camera
on +z (docs/diagram-pages.md).

The wafer is a 300 mm disc, 775 um thick on the datasheet. It is drawn THICK = 6 mm thick (about
8x) so the layers and the bevel read at overview distance. Zoom and section cross-sections are
drawn thicker still; their text says so.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, box, disc, empty, key, label, mat, pivot, show  # noqa: E402
from sand_zooms import scale_keys  # noqa: E402

END = F(40, 0)  # "until the end" for intervals; later than any scene

R = 150.0  # 300 mm
THICK = 6.0  # drawn thickness of the disc (datasheet 775 um)
SITE = 26.0  # scanner-field pitch, drawn
SITE_IN = 22.0  # a site's drawn size, with a gap between sites
EDGE_BAND = 40.0  # sites this close to the rim count as edge sites
FOUP_HALF = 170.0
FOUP_H = 330.0


def mats(m):
    m["si"] = mat("wafer_si", (0.50, 0.53, 0.58), metal=0.9, rough=0.16)
    m["bulk"] = mat("bulk_si", (0.42, 0.46, 0.52), metal=0.5, rough=0.4)
    m["epi"] = mat("epi_layer", (0.80, 0.64, 0.42), metal=0.2, rough=0.4)
    m["box"] = mat("buried_oxide", (0.95, 0.72, 0.28), rough=0.3, emit=(0.9, 0.6, 0.2), strength=0.6)
    m["handle"] = mat("handle_si", (0.30, 0.32, 0.37), metal=0.7, rough=0.35)
    m["device"] = mat("device_si", (0.40, 0.70, 0.72), metal=0.6, rough=0.25)
    m["notch"] = mat("notch", (0.03, 0.03, 0.04), rough=0.8)
    m["ion"] = mat("ion_beam", (0.4, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=3.0)
    m["weak"] = mat("weak_layer", (1.0, 0.8, 0.3), emit=(1.0, 0.8, 0.3), strength=3.0)
    m["scan"] = mat("scan_bar", (0.4, 0.9, 1.0), emit=(0.4, 0.9, 1.0), strength=2.0)
    m["site"] = mat("site_grey", (0.55, 0.58, 0.64), metal=0.3, rough=0.5)
    m["ok"] = mat("site_ok", (0.45, 0.95, 0.8), emit=(0.45, 0.95, 0.8), strength=1.6)
    m["edge"] = mat("site_edge", (0.94, 0.74, 0.38), emit=(0.94, 0.74, 0.38), strength=1.6)
    m["bad"] = mat("site_bad", (1.0, 0.25, 0.2), emit=(1.0, 0.25, 0.2), strength=2.5)
    m["gas"] = mat("gas_cvd", (0.75, 0.88, 1.0), emit=(0.7, 0.85, 1.0), strength=1.2, alpha=0.5)
    m["foup_glass"] = mat("foup_glass", (0.85, 0.92, 1.0), rough=0.05, alpha=0.22)
    m["foup_base"] = mat("foup_base", (0.30, 0.32, 0.36), metal=0.6, rough=0.4)
    m["gold"] = mat("gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["gold_glow"] = mat("gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["blue"] = mat("blue", (0.36, 0.56, 0.82), metal=0.2, rough=0.45)
    m["grey"] = mat("grey", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    m["red"] = mat("red", (0.90, 0.22, 0.18), emit=(0.9, 0.15, 0.1), strength=2.5)
    m["quake"] = mat("quake_block", (0.75, 0.35, 0.2), rough=0.6)
    m["plinth"] = mat("plinth", (0.18, 0.19, 0.23), rough=0.8)
    m["paper"] = mat("paper", (0.90, 0.88, 0.82), rough=0.85)
    m["ghost"] = mat("ghost", (0.6, 0.75, 0.95), rough=0.2, alpha=0.18)
    m["tool"] = mat("tool_steel", (0.22, 0.24, 0.28), metal=0.5, rough=0.5)
    return m


# ---- the wafer ------------------------------------------------------------------------


def wafer(parent, m, name="wafer", y0=0.0, notch=True):
    """The polished disc, its bottom at poly height y0, with the datasheet notch on the rim."""
    holder = empty(name, parent)
    disc("disc", (0, y0 + THICK / 2, 0), R, THICK, m["si"], holder, verts=128)
    if notch:
        box("notch", (-6, y0 + THICK / 2 - 1, -R - 1), (6, y0 + THICK / 2 + 1, -R + 9), m["notch"], holder)
    return holder


def site_cells():
    """Scanner-field sites that fit inside the rim with 3 mm edge exclusion: (i, j, x, z, edge)."""
    out = []
    n = int(R // SITE) + 1
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            cx, cz = SITE * i, SITE * j
            far = math.hypot(abs(cx) + SITE_IN / 2, abs(cz) + SITE_IN / 2)
            if far <= R - 3.0:
                edge = math.hypot(cx, cz) > R - EDGE_BAND
                out.append((i, j, cx, cz, edge))
    return out


def grid(parent, m, name, cells, mat_key, y_top, intervals, keep=None):
    """The sites in `cells` that `keep` accepts, as thin tiles on the top face, shown in `intervals`."""
    g = empty(name, parent)
    for i, j, cx, cz, edge in cells:
        if keep is not None and not keep(i, j, cx, cz, edge):
            continue
        box(f"{name}_{i}_{j}", (cx - SITE_IN / 2, y_top, cz - SITE_IN / 2), (cx + SITE_IN / 2, y_top + 0.6, cz + SITE_IN / 2), m[mat_key], g)
    show(g, intervals)
    return g


# ---- cut-away slabs (cross-sections, drawn thicker than life) ----------------------------


def slab(parent, m, name, layers, w=240.0, d=60.0, y0=0.0):
    """A cut-away piece of wafer: `layers` is a list of (mat key, height, part name) stacked up from
    poly height y0. The front faces sit on the cut plane z = 0."""
    g = empty(name, parent)
    y = y0
    for mk, h, part in layers:
        box(part, (-w / 2, y, -d), (w / 2, y + h, 0.0), m[mk], g)
        y += h
    return g


def plinth(parent, m, x0, x1, z0, z1, y=-6.0):
    box("plinth", (x0, y - 6, z0), (x1, y, z1), m["plinth"], parent)


def station(parent, m, x, name, w=120.0, h=110.0):
    """A tool or station block on the track, top at poly height h."""
    return box(name, (x - w / 2, 0, -90), (x + w / 2, h, 90), m["tool"], parent)


def foup(parent, m, cx, name="foup"):
    """A FOUP carrier: a base and four glass walls, its floor on poly height 0 of `parent`."""
    g = empty(name, parent)
    h = FOUP_HALF
    box("foup_base", (cx - h, 0, -h), (cx + h, 6, h), m["foup_base"], g)
    box("foup_back", (cx - h, 6, -h), (cx + h, FOUP_H, -h + 5), m["foup_glass"], g)
    box("foup_front", (cx - h, 6, h - 5), (cx + h, FOUP_H, h), m["foup_glass"], g)
    box("foup_left", (cx - h, 6, -h), (cx - h + 5, FOUP_H, h), m["foup_glass"], g)
    box("foup_right", (cx + h - 5, 6, -h), (cx + h, FOUP_H, h), m["foup_glass"], g)
    return g


# ---- bars and tiles -------------------------------------------------------------------


def grow_bar(parent, name, x, z, w, h, m, f0, f1, y0=0.0, depth=None):
    """A bar standing at (x, y0, z) that grows from nothing to height h over [f0, f1]."""
    d = depth or w
    b = pivot(name, (x, y0, z), parent)
    box(f"{name}_box", (-w / 2, 0, -d / 2), (w / 2, h, d / 2), m, b)
    scale_keys(b, [(0, (OFF,) * 3), (f0, (1, 1, OFF)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    return b


def grow_hbar(parent, name, x, y, z, length, thick, m, f0, f1):
    """A horizontal bar from (x, y, z) to the right that grows to `length` over [f0, f1]."""
    b = pivot(name, (x, y, z), parent)
    box(f"{name}_box", (0, -thick / 2, -thick / 2), (length, thick / 2, thick / 2), m, b)
    scale_keys(b, [(0, (OFF,) * 3), (f0, (OFF, 1, 1)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    return b


def tile(g, name, x, y, w, h, text, f0, m, iv=None):
    """A paper card that flies in at f0 and carries one tag."""
    e = empty(name, g)
    box(f"{name}_b", (x - w / 2, y - h / 2, -80), (x + w / 2, y + h / 2, 0), m["paper"], e)
    box(f"{name}_rule", (x - w / 2 + 40, y + h / 2 - 70, 0), (x + w / 2 - 40, y + h / 2 - 50, 6), m["gold"], e)
    key(e, f0, "location", P(0, 900, 300))
    key(e, f0 + 14, "location", P(0, 0, 0))
    show(e, [(f0, END)])
    label(text, (x - w / 2 + 40, y, 10), e, iv or [(f0 + 10, END)])
    return e


def placed(root, name, x):
    """A group built at the origin, then moved to x, so cut-free builds and pivots stay simple."""
    g = empty(name, root)
    return g, lambda: setattr(g, "location", P(x, 0, 0))
