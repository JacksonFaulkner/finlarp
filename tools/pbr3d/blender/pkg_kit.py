"""Shared package geometry for the PACKAGING tab overviews (LOGIC, MICROBUMP, INTERPOSER,
SUBSTRATE, ASSEMBLY, BOARD). Units mm, Y up; one stack, bottom to top:

  board -- BGA balls -- substrate -- C4 balls -- interposer -- microbumps -- die + HBM -- lid -- cold plate

Each node script builds the parts it needs with these helpers and sets its own beats, camera
and tags. Built on sand_overview / pbr_kit helpers (see docs/diagram-pages.md).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import ball, box, tube  # noqa: E402
from pbr_kit import mat, empty  # noqa: E402

# Levels (mm, Y up).
BOARD_TOP = -8.0
SUB_BOT, SUB_TOP = -6.0, -2.0
IP_BOT, IP_TOP = 0.0, 1.6
UB_TOP = 2.8
DIE_TOP = 4.2
STACK_TOP = 6.6
LID_BOT, LID_TOP = 7.5, 8.7
PLATE_TOP = 11.0

DIE_HALF_X, DIE_HALF_Z = 12.75, 16.0  # the logic die, 25.5 x 32 mm


def materials():
    return {
        "board": mat("pkg_board", (0.10, 0.34, 0.20), rough=0.7),
        "substrate": mat("pkg_substrate", (0.42, 0.27, 0.15), rough=0.8),
        "abf": mat("pkg_abf_copper", (0.78, 0.46, 0.28), metal=0.9, rough=0.35),
        "silicon": mat("pkg_interposer_si", (0.30, 0.36, 0.40), metal=0.4, rough=0.5),
        "organic": mat("pkg_organic", (0.20, 0.22, 0.24), rough=0.8),
        "die": mat("pkg_die_purple", (0.42, 0.30, 0.72), metal=0.2, rough=0.35),
        "hbm": mat("pkg_hbm_grey", (0.72, 0.74, 0.78), metal=0.3, rough=0.4),
        "solder": mat("pkg_solder", (0.82, 0.82, 0.80), metal=0.8, rough=0.35),
        "copper": mat("pkg_copper", (0.85, 0.55, 0.35), metal=0.9, rough=0.3),
        "underfill": mat("pkg_underfill", (0.08, 0.07, 0.07), rough=0.9),
        "lid": mat("pkg_lid_steel", (0.55, 0.58, 0.62), metal=0.7, rough=0.4),
        "plate": mat("pkg_cold_copper", (0.85, 0.55, 0.35), metal=0.9, rough=0.3),
        "coolant": mat("pkg_coolant", (0.30, 0.60, 1.00), emit=(0.3, 0.6, 1.0), strength=1.5),
        "bridge": mat("pkg_bridge_cyan", (0.25, 0.85, 0.85), metal=0.3, rough=0.4),
        "power": mat("pkg_power_yellow", (1.0, 0.85, 0.20), emit=(1.0, 0.80, 0.20), strength=10.0),
        "data": mat("pkg_data_cyan", (0.30, 0.90, 1.0), emit=(0.20, 0.90, 1.0), strength=10.0),
        "heat": mat("pkg_heat", (1.0, 0.50, 0.20), emit=(1.0, 0.40, 0.10), strength=2.0, alpha=0.5),
        "die_hot": mat("pkg_die_hot", (0.90, 0.35, 0.15), emit=(1.0, 0.40, 0.10), strength=0.8),
        **hbm_materials(),
    }


def hbm_materials():
    """The detailed HBM stack's colours, as on the HBM STACK memory pages (hbm_kit.mats)."""
    return {
        "hbm_dram": mat("pkg_hbm_dram", (0.93, 0.52, 0.18), rough=0.45),
        "hbm_base": mat("pkg_hbm_base", (0.25, 0.45, 0.95), metal=0.2, rough=0.4),
        "hbm_fill": mat("pkg_hbm_fill", (0.10, 0.09, 0.09), rough=0.9),
        "hbm_tsv": mat("pkg_hbm_tsv", (1.0, 0.82, 0.30), metal=0.6, rough=0.3, emit=(1.0, 0.75, 0.25), strength=1.5),
    }


def grid(half, pitch):
    n = int(half // pitch)
    return [(pitch * i, pitch * j) for i in range(-n, n + 1) for j in range(-n, n + 1)]


def board(m, parent):
    return box("board", (-60.0, -14.0, -60.0), (60.0, BOARD_TOP, 60.0), m["board"], parent)


def bga(m, parent, half=20.0, pitch=4.0):
    g = empty("bga", parent)
    for i, (x, z) in enumerate(grid(half, pitch)):
        ball(f"bga_{i}", (x, BOARD_TOP + 1.0, z), 0.9, m["solder"], g, 12)
    return g


def substrate(m, parent, half=30.0):
    return box("substrate", (-half, SUB_BOT, -half), (half, SUB_TOP, half), m["substrate"], parent)


def c4(m, parent, half=20.0, pitch=5.0):
    g = empty("c4", parent)
    for i, (x, z) in enumerate(grid(half, pitch)):
        ball(f"c4_{i}", (x, SUB_TOP + 0.9, z), 0.9, m["solder"], g, 12)
    return g


def interposer(m, parent, half=26.0, name="interposer", mat_name="silicon"):
    return box(name, (-half, IP_BOT, -half), (half, IP_TOP, half), m[mat_name], parent)


def die(m, parent, x0=-DIE_HALF_X, x1=DIE_HALF_X, z0=-DIE_HALF_Z, z1=DIE_HALF_Z, name="die", mat_name="die"):
    return box(name, (x0, UB_TOP, z0), (x1, DIE_TOP, z1), m[mat_name], parent)


HBM_DIES = 8  # DRAM dies per stack (an 8-high stack)


def hbm_stack(name, lo, hi, m, parent, n=HBM_DIES):
    """One HBM stack filling the box `lo`..`hi`: a blue base logic die, `n` thin orange DRAM dies
    on dark underfill gaps, and copper-gold TSV columns through the middle. The quadrant facing
    the cameras (+x, +z) is cut away down to the base die, so the layers and the TSVs show on the
    two cut faces that meet at the stack's centre. Returns a group empty (at the origin, parts at
    absolute coordinates) that can be shown, keyed or moved like the old box's parent.

    With only m["hbm"] (a see-through copy, say) it is the plain box, in a group all the same."""
    g = empty(name, parent)
    if "hbm_dram" not in m:
        box(f"{name}_box", lo, hi, m["hbm"], g)
        return g
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
    h = y1 - y0
    bt = 0.16 * h  # base die
    pitch = (h - bt) / n
    gap = 0.28 * pitch
    inset = 0.04 * min(x1 - x0, z1 - z0)  # the underfill sits back from the die edges

    def ell(tag, ya, yb, mt, d=0.0):
        # The L that is left of a layer once the (+x, +z) quadrant is cut away; `d` insets the
        # outer faces only, so the cut faces stay flush.
        box(f"{name}_{tag}_back", (x0 + d, ya, z0 + d), (x1 - d, yb, zm), mt, g)
        box(f"{name}_{tag}_front", (x0 + d, ya, zm), (xm, yb, z1 - d), mt, g)

    box(f"{name}_base", (x0, y0, z0), (x1, y0 + bt, z1), m["hbm_base"], g)
    for k in range(n):
        yb = y0 + bt + k * pitch
        ell(f"gap{k}", yb, yb + gap, m["hbm_fill"], inset)
        ell(f"dram{k}", yb + gap, yb + pitch, m["hbm_dram"])
    # TSV columns, half sunk in the cut faces: one at the corner where they meet, two out along
    # each face.
    r = 0.035 * min(x1 - x0, z1 - z0)
    wx, wz = x1 - xm, z1 - zm
    pts = [(xm, zm)] + [(xm + f * wx, zm) for f in (0.3, 0.6)] + [(xm, zm + f * wz) for f in (0.3, 0.6)]
    for i, (x, z) in enumerate(pts):
        tube(f"{name}_tsv{i}", (x, y0 + bt, z), (x, y1, z), r, m["hbm_tsv"], g, 8)
    return g


def stacks(m, parent, zs, inner=14.5, width=7.75, height=5.0, depth=8.0, base=IP_TOP):
    """HBM stacks on the interposer, two per side at each z in `zs` (the die's shoreline). Each
    is one group under `parent` (see hbm_stack)."""
    out = []
    for side in (-1, 1):
        for zc in zs:
            a, b = side * inner, side * (inner + width)
            lo = (min(a, b), base, zc - depth / 2)
            hi = (max(a, b), base + height, zc + depth / 2)
            out.append(hbm_stack(f"hbm_{side}_{zc}", lo, hi, m, parent))
    return out


def ubumps(m, parent, half=5.6, pitch=2.8, r=0.35):
    g = empty("ubumps", parent)
    for i in range(-2, 3):
        for j in range(-2, 3):
            tube(f"ub_{i}_{j}", (pitch * i, IP_TOP, pitch * j), (pitch * i, UB_TOP, pitch * j), r, m["copper"], g, 12)
    return g


def underfill_rim(m, parent):
    g = empty("underfill", parent)
    box("uf_front", (-DIE_HALF_X - 0.6, IP_TOP, DIE_HALF_Z - 0.4), (DIE_HALF_X + 0.6, UB_TOP, DIE_HALF_Z + 0.6), m["underfill"], g)
    box("uf_back", (-DIE_HALF_X - 0.6, IP_TOP, -DIE_HALF_Z - 0.6), (DIE_HALF_X + 0.6, UB_TOP, -DIE_HALF_Z + 0.4), m["underfill"], g)
    box("uf_left", (-DIE_HALF_X - 0.6, IP_TOP, -DIE_HALF_Z + 0.4), (-DIE_HALF_X + 0.4, UB_TOP, DIE_HALF_Z - 0.4), m["underfill"], g)
    box("uf_right", (DIE_HALF_X - 0.4, IP_TOP, -DIE_HALF_Z + 0.4), (DIE_HALF_X + 0.6, UB_TOP, DIE_HALF_Z - 0.4), m["underfill"], g)
    return g


def lid(m, parent, half=24.0):
    return box("lid", (-half, LID_BOT, -half), (half, LID_TOP, half), m["lid"], parent)


def cold_plate(m, parent, half=24.0, fins=11, fin_h=4.0):
    g = empty("cold_plate", parent)
    box("plate_base", (-half, LID_TOP, -half), (half, PLATE_TOP, half), m["plate"], g)
    step = 2 * half / fins
    for k in range(fins):
        x = -half + step * (k + 0.5)
        box(f"fin_{k}", (x - 0.3, PLATE_TOP, -half + 1), (x + 0.3, PLATE_TOP + fin_h, half - 1), m["plate"], g)
    return g


def package(m, parent, interposer_half=26.0, stack_zs=(-9.0, 9.0, -21.0, 21.0)):
    """Substrate-free package for the upper overviews: interposer, die, stacks, microbumps."""
    ip = interposer(m, parent, interposer_half)
    ub = ubumps(m, parent)
    d = die(m, parent)
    hb = stacks(m, parent, stack_zs)
    return {"interposer": ip, "ubumps": ub, "die": d, "stacks": hb}
