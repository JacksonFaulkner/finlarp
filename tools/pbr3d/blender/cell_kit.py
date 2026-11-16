"""The 1T1C DRAM cell as reusable Blender pieces for the CELL pictures (overview, zooms, sections).

The cell sits on its centre plane ZC (z), with the word line running along z, the bit line along x
and the stacked storage capacitor on the source side. Cut-aways are taken at ZC. Units are
millimetres, Y up (docs/diagram-pages.md). The shapes are schematic, not to scale.

Every light is an overlay: a slightly larger copy in an emissive material, switched on with
`show` for the beats where it is active. Levels (the charge in the capacitor, the bit-line
voltage) are scale keys on a pivot at the bottom of the bar, so they rise and fall from the base.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, box, cut, disc, empty, key, label, mat, pivot, rel, show, tube, cup  # noqa: E402
from sand_zooms import scale_keys, stream_of  # noqa: E402

END = F(40, 0)  # "until the end" for intervals; later than any scene

ZC = -250.0  # the cell's centre plane: the word line, bit line plug and capacitor axis sit here
DRN_X, SRC_X = -370.0, 370.0  # drain (bit-line side) and source (storage-node side) centres
BL_Y = 1000.0  # bit line height, above the capacitor
CAP_Y0, CAP_Y1 = 300.0, 900.0  # capacitor walls from the storage node up
CAP_R, DIE_R, IN_R = 230.0, 205.0, 170.0  # outer plate, dielectric, inner plate radii
WL_Y = 110.0  # word line centre height over the channel
VDD = 1000.0  # full rail: the gauge height
GAUGE_X = -1520.0
HALF_Y = VDD / 2  # VDD/2, the precharge level
# where a tag on the capacitor pins: on its right flank, clear of the bit line above it
CAP_TAG = (SRC_X + CAP_R, (CAP_Y0 + CAP_Y1) / 2 + 120, ZC + 60)


def mats(m):
    """The cell's materials, added to the sand base set (start() makes that)."""
    m["silicon"] = mat("cell_silicon", (0.34, 0.36, 0.41), rough=0.9)
    m["n_plus"] = mat("n_plus", (0.50, 0.62, 0.86), rough=0.6)
    m["oxide"] = mat("oxide", (0.80, 0.82, 0.86), rough=0.5)
    m["wl"] = mat("wordline", (0.50, 0.28, 0.36), rough=0.4)
    m["wl_on"] = mat("wordline_on", (1.0, 0.45, 0.62), emit=(1.0, 0.40, 0.60), strength=2.5)
    m["bl"] = mat("bitline", (0.22, 0.62, 0.78), metal=0.5, rough=0.3)
    m["bl_on"] = mat("bitline_on", (0.45, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.5)
    m["plug"] = mat("plug", (0.70, 0.72, 0.76), metal=0.9, rough=0.3)
    m["cap_in"] = mat("cap_inner", (0.80, 0.60, 0.32), metal=0.0, rough=0.5, alpha=0.10)
    m["cap_out"] = mat("cap_outer", (0.42, 0.47, 0.58), metal=0.5, rough=0.4, alpha=0.09)
    m["diel"] = mat("dielectric", (0.92, 0.90, 0.70), rough=0.3, alpha=0.05)
    m["charge"] = mat("cell_charge", (1.0, 0.55, 0.15), emit=(1.0, 0.50, 0.10), strength=1.8)
    m["sa"] = mat("sense_amp", (0.55, 0.32, 0.85), emit=(0.65, 0.35, 1.0), strength=2.5)
    m["sa_dim"] = mat("sense_amp_dim", (0.24, 0.18, 0.34), rough=0.8)
    m["pre"] = mat("precharge", (0.35, 0.90, 0.45), emit=(0.35, 0.90, 0.45), strength=2.5)
    m["pre_dim"] = mat("precharge_dim", (0.18, 0.28, 0.20), rough=0.8)
    m["glow_steel"] = mat("glow_steel", (0.60, 0.62, 0.66), metal=0.6, rough=0.4)
    m["gauge_bar"] = mat("gauge_bar", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.0)
    m["ring"] = mat("vdd_half_ring", (1.0, 1.0, 1.0), emit=(1.0, 1.0, 1.0), strength=1.5)
    m["cyan_dot"] = mat("dot_cyan", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=3.0)
    m["violet_dot"] = mat("dot_violet", (0.70, 0.50, 1.0), emit=(0.70, 0.50, 1.0), strength=3.0)
    m["orange_dot"] = mat("dot_orange", (1.0, 0.60, 0.20), emit=(1.0, 0.60, 0.20), strength=3.0)
    m["pointer"] = mat("pointer_white", (1.0, 1.0, 1.0), emit=(1.0, 1.0, 1.0), strength=2.0)
    m["red"] = mat("red", (0.90, 0.22, 0.18), emit=(0.9, 0.15, 0.1), strength=2.5)
    m["gold"] = mat("gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["gold_glow"] = mat("gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["paper"] = mat("paper", (0.90, 0.88, 0.82), rough=0.85)
    m["grey"] = mat("grey", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    m["plinth"] = mat("plinth", (0.18, 0.19, 0.23), rough=0.8)
    return m


def switch(obj, intervals):
    """Show `obj` only during `intervals`. A box's scale is its size, so `show` on the box itself
    would shrink it to a 1 mm speck; the switch goes on an empty at the origin wrapped around it."""
    e = empty(obj.name + "_sw", obj.parent)
    obj.parent = e
    show(e, intervals)
    return e


def overlay(parent, name, lo, hi, m, intervals):
    """A box in an emissive material over the same space, switched on for `intervals`."""
    o = box(name, lo, hi, m, parent)
    switch(o, intervals)
    return o


# ---- the cell -----------------------------------------------------------------------------


def substrate(root, m):
    """The silicon block, cut open at the cell's centre plane so the transistor shows inside."""
    o = box("silicon", (-1100, -600, -900), (1100, 0, 0), m["silicon"], root)
    return cut(o, ZC)


def transistor(root, m, lit=()):
    """Drain and source (N+), the gate oxide and the word line over the channel.
    `lit` lists intervals for the word line lit up (the row is selected); the channel glows then
    as well. Returns the group."""
    g = empty("transistor", root)
    box("drain_n", (DRN_X - 150, -60, ZC - 130), (DRN_X + 150, 20, ZC + 130), m["n_plus"], g)
    box("source_n", (SRC_X - 150, -60, ZC - 130), (SRC_X + 150, 20, ZC + 130), m["n_plus"], g)
    box("gate_oxide", (-240, 0, ZC - 140), (240, 30, ZC + 140), m["oxide"], g)
    # word line: a rod along z over the channel, dim, with a lit overlay
    box("wordline", (-120, WL_Y - 60, -900), (120, WL_Y + 60, ZC + 150), m["wl"], g)
    if lit:
        overlay(g, "wordline_on", (-132, WL_Y - 72, -900), (132, WL_Y + 72, ZC + 150), m["wl_on"], lit)
        overlay(g, "channel_on", (-220, -10, ZC - 120), (220, 36, ZC + 120), m["cyan_dot"], lit)
    return g


def bitline(root, m, lit=()):
    """The bit line along x above the cell, its plug down to the drain, and its ends."""
    g = empty("bitline", root)
    tube("bitline_w", (-1250, BL_Y, ZC), (1150, BL_Y, ZC), 60, m["bl"], g, verts=12)
    tube("bl_plug", (DRN_X, 0, ZC), (DRN_X, BL_Y, ZC), 45, m["plug"], g, verts=12)
    if lit:
        overlay(g, "bitline_on", (-1250, BL_Y - 75, ZC - 75), (1150, BL_Y + 75, ZC + 75), m["bl_on"], lit)
    return g


def sense_amp(root, m, lit=()):
    """The sense amp at the bit line's left end: a dim block, lit (purple) while it latches."""
    g = empty("sense_amp", root)
    box("sa_block", (-1340, 930, ZC - 130), (-1160, 1170, ZC + 130), m["sa_dim"], g)
    if lit:
        overlay(g, "sa_on", (-1355, 915, ZC - 145), (-1145, 1185, ZC + 145), m["sa"], lit)
    return g


def precharge(root, m, lit=()):
    """The precharge block at the bit line's right end, green while it holds VDD/2."""
    g = empty("precharge", root)
    box("pre_block", (1060, 930, ZC - 130), (1240, 1170, ZC + 130), m["pre_dim"], g)
    if lit:
        overlay(g, "pre_on", (1045, 915, ZC - 145), (1255, 1185, ZC + 145), m["pre"], lit)
    return g


def capacitor(root, m):
    """The stacked storage capacitor on the source: the storage node, the outer plate, the
    dielectric, the inner plate and a charge fill. Returns (group, fill). Scale `fill` in y to set
    the charge (1 full, 0 empty); it grows from its base."""
    g = empty("capacitor", root)
    tube("storage_node", (SRC_X, 0, ZC), (SRC_X, CAP_Y0 + 10, ZC), 60, m["plug"], g, verts=12)
    H = CAP_Y1 - CAP_Y0
    cup("cap_outer", (SRC_X, CAP_Y0, ZC), CAP_R, H, m["cap_out"], g)
    cup("dielectric", (SRC_X, CAP_Y0, ZC), DIE_R, H, m["diel"], g)
    cup("cap_inner", (SRC_X, CAP_Y0, ZC), IN_R, H, m["cap_in"], g)
    base = (SRC_X, CAP_Y0 + 20, ZC)
    fill_pv = pivot("charge_level", base, g)
    disc("charge_fill", rel(base, (SRC_X, CAP_Y0 + 20 + (H - 40) / 2, ZC)), IN_R - 25, H - 40, m["charge"], fill_pv, verts=48)
    return g, fill_pv


def gauge(root, m, lit=()):
    """The bit-line voltage gauge: a pole from the ground to VDD, a bar that rises from its base
    (the scale is the level, 0.5 at VDD/2), and a white ring at VDD/2. Returns (group, bar)."""
    g = empty("gauge", root)
    box("gauge_pole", (GAUGE_X - 40, 0, ZC - 40), (GAUGE_X + 40, VDD, ZC + 40), m["grey"], g)
    base = (GAUGE_X, 0.0, ZC)
    bar_pv = pivot("gauge_level", base, g)
    box("gauge_bar_m", rel(base, (GAUGE_X - 90, 0, ZC - 90)), rel(base, (GAUGE_X + 90, VDD, ZC + 90)), m["gauge_bar"], bar_pv)
    box("vdd_half", (GAUGE_X - 120, HALF_Y - 6, ZC - 120), (GAUGE_X + 120, HALF_Y + 6, ZC + 120), m["ring"], g)
    return g, bar_pv


def bit_level(bar, keys):
    """Keys for the gauge bar's height: `keys` are (frame, level) with 1.0 = VDD, 0.5 = VDD/2."""
    scale_keys(bar, [(f, (1, 1, v)) for f, v in keys])


def cell(root, m, lit_wl=(), lit_sa=(), lit_pre=(), lit_bl=(), lit_wl_only=None):
    """The whole cell with its parts, in their dim state. Returns a dict of the groups and the
    capacitor's charge and gauge pivots (for keys)."""
    parts = {}
    parts["si"] = substrate(root, m)
    parts["tr"] = transistor(root, m, lit=lit_wl)
    parts["bl"] = bitline(root, m, lit=lit_bl)
    parts["sa"] = sense_amp(root, m, lit=lit_sa)
    parts["pre"] = precharge(root, m, lit=lit_pre)
    parts["cap"], parts["fill"] = capacitor(root, m)
    parts["gauge"], parts["bar"] = gauge(root, m)
    return parts


# ---- moving charge ------------------------------------------------------------------------

# Dots run on a plane just in front of the cell (ZF), so the opaque plugs, the channel and the
# capacitor don't hide them; the paths are offsets in x and y only.
ZF = ZC + CAP_R + 40.0
SHARE_START = (SRC_X, 600.0, ZF)  # inside the capacitor's height, in front of it
RESTORE_START = (DRN_X, BL_Y, ZF)  # at the bit line, in front of the plug
LEAK_START = (SRC_X - 150, 380.0, ZF)
# The storage node to the bit line: down the storage node out of the cap, left under the channel
# and up the drain plug to the bit line (offsets from SHARE_START).
PATH_CAP_TO_BL = [(0, 0, 0), (0, -560, 0), (-740, -560, 0), (-740, 420, 0)]
# The reverse: from the bit line down the plug, right under the channel, and up the storage node
# into the capacitor (offsets from RESTORE_START).
PATH_BL_TO_CAP = [(0, 0, 0), (0, -960, 0), (740, -960, 0), (740, -400, 0)]
PATH_LEAK = [(0, 0, 0), (-260, -120, 0), (-420, -330, 0)]


def dots(parent, name, n, start_pt, path, mat_, beat, u0, u1, life=60, size=14):
    """A train of `n` dots along `path` from `start_pt`, sent between fractions u0 and u1 of beat."""
    return stream_of(parent, name, n, start_pt, path, size, mat_, beat, u0, u1, life)


def tag_pt(name, text, at, parent, intervals):
    """A `label:` tag at poly point `at`, shown during `intervals`."""
    return label(text, at, parent, intervals)


def wl_intervals(on):
    """Word-line on intervals: a list of [f0,f1) pairs from (beat, u0, u1) triples."""
    return [(F(b, u0), F(b, u1)) for b, u0, u1 in on]


def rows_of_cells(root, m, nx, nz, pitch, lit_at=None):
    """A small array of plain cells (capacitor tops only) for the refresh-across-rows picture.
    Each entry is a capacitor tube with a level; returns the list of (group, fill)."""
    out = []
    for i in range(nx):
        for j in range(nz):
            x = (i - (nx - 1) / 2) * pitch
            z = (j - (nz - 1) / 2) * pitch
            g = empty(f"row_cell_{i}_{j}", root)
            H = 700.0
            cup(f"rc_out_{i}_{j}", (x, 0, z), 150, H, m["cap_out"], g)
            pv = pivot(f"rc_level_{i}_{j}", (x, 20, z), g)
            disc(f"rc_fill_{i}_{j}", rel((x, 20, z), (x, 20 + (H - 40) / 2, z)), 120, H - 40, m["charge"], pv, verts=24)
            out.append((g, pv))
    return out


__all__ = [
    "END", "ZC", "DRN_X", "SRC_X", "BL_Y", "CAP_Y0", "CAP_Y1", "CAP_R", "DIE_R", "IN_R", "WL_Y",
    "VDD", "GAUGE_X", "HALF_Y", "CAP_TAG", "mats", "switch", "overlay", "substrate", "transistor", "bitline", "sense_amp",
    "precharge", "capacitor", "gauge", "bit_level", "cell", "dots", "tag_pt", "wl_intervals",
    "rows_of_cells", "ZF", "SHARE_START", "RESTORE_START", "LEAK_START", "PATH_CAP_TO_BL", "PATH_BL_TO_CAP", "PATH_LEAK",
]
_unused = (math, key, P, OFF, END)


def cap_stack(parent, m, base, H, outer=True, scale_r=1.0):
    """A stacked capacitor standing on poly point `base`, `H` tall. Its parts are built relative to
    a pivot at the base, so the whole stack can be scaled (shrink, grow) about its foot. `outer`
    False leaves out the outer plate so the charge inside shows. Returns (group, fill_pivot)."""
    g = pivot("cap_stack", base, parent)
    if outer:
        cup("cap_outer", (0, 0, 0), CAP_R * scale_r, H, m["cap_out"], g)
        cup("dielectric", (0, 0, 0), DIE_R * scale_r, H, m["diel"], g)
    cup("cap_inner", (0, 0, 0), IN_R * scale_r, H, m["cap_in"], g)
    fill_pv = pivot("charge_level", (0, 20, 0), g)
    disc("charge_fill", (0, (H - 40) / 2, 0), (IN_R - 25) * scale_r, H - 40, m["charge"], fill_pv, verts=48)
    return g, fill_pv


def pair_of_lines(root, m, z0, z1, y, x0, x1, mat_a, mat_b):
    """Two parallel bit lines along x, at z0 and z1 and height y. Returns (line_a, line_b)."""
    a = tube("line_a", (x0, y, z0), (x1, y, z0), 40, mat_a, root, verts=12)
    b = tube("line_b", (x0, y, z1), (x1, y, z1), 40, mat_b, root, verts=12)
    return a, b
