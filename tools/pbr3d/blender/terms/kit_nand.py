"""Memory-NAND kit for the Terms scenes: floating-gate and charge-trap cells cut open, a control
gate, a 3D NAND stack, and a NAND package on a board. Shared by TRM_FLOATING_GATE, TRM_CHARGE_TRAP
and TRM_CONTROL_GATE (and later NAND terms).

Coordinates are the term poly frame: y is up from the board top (y = 0), the scene's cut face is
z = 0, and a device cut-open on the bench spans x 150..248 with its depth running from z0 to 0.

API (every part takes the materials dict m and a parent; each returns a group or a points dict):
  prep(m)                          -> m    adds the nand_* materials (call once after C.setup)
  context(m, root)                 -> {"pkg": top point of the NAND package, "pcb": group}
  cell_fg(m, parent, name, x0, x1, z0)
                                   -> {"grp", "fg", "tox", "chan", "cg", "sub", "src", "drn"}
                                      planar floating-gate cell cut at z = 0; "fg" = FG centre
  cell_ctf(m, parent, name, x0, x1, z0)
                                   -> {"grp", "tox", "sin", "cg", "chan", "cg_top", "trap"}
                                      planar charge-trap cell; "trap" = a defect point in the nitride
  electrons(m, parent, name, pts, n, size)
                                   -> group of n glowing beads (electrons), placed on the points
  traps(m, parent, name, pts, size)
                                   -> group of small glowing defect spheres at pts (charge in traps)
  tunnel_path(a, b, bend=1.0, steps=7)
                                   -> points from a to b, bowed sideways by `bend` (tunnelling path)
  wordline(m, parent, name, x0, x1, z0, z1, y0, y1)
                                   -> group: a control-gate strip spanning the cell width
  stack_3d(m, parent, name, x0, x1, z0, z1, y0, layers=8, pitch=4.0)
                                   -> {"grp", "top", "hole"}: 3D NAND word-line layers, channel hole
"""

import math
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import empty, mat, tube  # noqa: E402
from power_vrm_detail import bead, bx  # noqa: E402
import term_common as C  # noqa: E402


def prep(m):
    """Add the NAND materials (prefixed nand_ so they never clash with other families)."""
    m["nand_sub"] = mat("nand_sub", (0.36, 0.38, 0.46), metal=0.5, rough=0.35)
    m["nand_nplus"] = mat("nand_nplus", (0.30, 0.45, 0.80), rough=0.4)
    m["nand_ox"] = mat("nand_ox", (0.85, 0.90, 0.95), rough=0.2)
    m["nand_tox"] = mat("nand_tox", (0.78, 0.88, 0.98), rough=0.15)
    m["nand_fg"] = mat("nand_fg", (0.62, 0.40, 0.46), metal=0.6, rough=0.3)
    m["nand_ipd"] = mat("nand_ipd", (0.80, 0.86, 0.92), rough=0.2)
    m["nand_cg"] = mat("nand_cg", (0.55, 0.25, 0.25), metal=0.3, rough=0.4)
    m["nand_sin"] = mat("nand_sin", (0.30, 0.62, 0.58), rough=0.35)
    m["nand_chan"] = mat("nand_chan", (0.40, 0.85, 1.0), emit=(0.40, 0.85, 1.0), strength=2.5)
    m["nand_trap"] = mat("nand_trap", (0.95, 0.80, 1.0), emit=(0.95, 0.80, 1.0), strength=3.0)
    m["nand_e"] = mat("nand_e", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=3.0)
    return m


def context(m, root):
    """A NAND package on a small board, lying left of the bench (x 150..248 stays clear).
    Returns the package's top centre and the board group."""
    board = C.pcb(m, root, "nand_pcb", -260.0, 250.0, -220.0, 0.0)
    C.trace(m, board, "nand_tr", [(-120.0, 0.0, -150.0), (-40.0, 0.0, -150.0), (40.0, 0.0, -150.0)], w=1.2)
    C.trace(m, board, "nand_tr2", [(-40.0, 0.0, -150.0), (-40.0, 0.0, -90.0)], w=1.2)
    pkg = C.chip(m, root, "nand_pkg", (-40.0, 0.0, -70.0), 42.0, 30.0, h=3.0, pins=0, body="mold")
    C.chip(m, root, "nand_ctrl", (-130.0, 0.0, -80.0), 26.0, 22.0, h=2.2, pins=6, body="mold")
    return {"pkg": pkg, "pcb": board}


def _rect_cell(m, g, name, x0, x1, z0, tox_top):
    """The shared bottom of a planar cell: p-well, n+ source and drain, tunnel oxide on the channel."""
    bx(f"{name}_sub", (x0, 0.0, z0), (x1, 6.0, 0.0), m["nand_sub"], g)
    bx(f"{name}_src", (x0 + 4.0, 0.0, z0), (x0 + 24.0, 9.0, 0.0), m["nand_nplus"], g)
    bx(f"{name}_drn", (x1 - 24.0, 0.0, z0), (x1 - 4.0, 9.0, 0.0), m["nand_nplus"], g)
    bx(f"{name}_tox", (x0 + 24.0, 6.0, z0), (x1 - 24.0, tox_top, 0.0), m["nand_tox"], g)


def cell_fg(m, parent, name, x0, x1, z0):
    g = empty(name, parent)
    _rect_cell(m, g, name, x0, x1, z0, 8.5)
    # floating gate: poly fully inside oxide (side spacers and the IPD above it)
    bx(f"{name}_fg", (x0 + 30.0, 8.5, z0 + 4.0), (x1 - 30.0, 16.0, -4.0), m["nand_fg"], g)
    bx(f"{name}_ox_l", (x0 + 24.0, 8.5, z0), (x0 + 30.0, 16.0, 0.0), m["nand_ox"], g)
    bx(f"{name}_ox_r", (x1 - 30.0, 8.5, z0), (x1 - 24.0, 16.0, 0.0), m["nand_ox"], g)
    bx(f"{name}_ipd", (x0 + 24.0, 16.0, z0), (x1 - 24.0, 18.0, 0.0), m["nand_ipd"], g)
    bx(f"{name}_cg", (x0 + 24.0, 18.0, z0), (x1 - 24.0, 25.0, 0.0), m["nand_cg"], g)
    cx = (x0 + x1) / 2
    return {"grp": g, "fg": (cx, 12.0, z0 / 2), "tox": (cx, 7.2, z0 / 2), "chan": (cx, 6.6, z0 / 2),
            "cg": (cx, 21.5, z0 / 2), "sub": (x0 + 60.0, 3.0, z0 / 2),
            "src": (x0 + 14.0, 9.5, z0 / 2), "drn": (x1 - 14.0, 9.5, z0 / 2)}


def cell_ctf(m, parent, name, x0, x1, z0):
    g = empty(name, parent)
    _rect_cell(m, g, name, x0, x1, z0, 8.5)
    # charge-trap layer: one continuous nitride film, then the blocking oxide and the gate
    bx(f"{name}_sin", (x0 + 24.0, 8.5, z0), (x1 - 24.0, 13.5, 0.0), m["nand_sin"], g)
    bx(f"{name}_blk", (x0 + 24.0, 13.5, z0), (x1 - 24.0, 16.0, 0.0), m["nand_ox"], g)
    bx(f"{name}_cg", (x0 + 24.0, 16.0, z0), (x1 - 24.0, 23.0, 0.0), m["nand_cg"], g)
    cx = (x0 + x1) / 2
    trap = (cx - 10.0, 11.0, z0 / 2 + 6.0)
    return {"grp": g, "tox": (cx, 7.2, z0 / 2), "sin": (cx, 11.0, z0 / 2), "cg": (cx, 19.5, z0 / 2),
            "chan": (cx, 6.6, z0 / 2), "cg_top": (cx, 23.0, z0 / 2), "trap": trap}


def electrons(m, parent, name, pts, n, size):
    """n electron beads, one per point in pts (cycled), so a run can start from them."""
    g = empty(name, parent)
    for k in range(n):
        bead(f"{name}{k}", pts[k % len(pts)], size, m["nand_e"], g)
    return g


def traps(m, parent, name, pts, size):
    """Small glowing spheres where charge sits in the nitride traps."""
    g = empty(name, parent)
    for k, p in enumerate(pts):
        bead(f"{name}{k}", p, size, m["nand_trap"], g, 8)
    return g


def tunnel_path(a, b, bend=1.0, steps=7):
    """Points from a to b, bowed sideways by `bend`: the tunnelling route through the oxide."""
    out = []
    for k in range(steps):
        t = k / (steps - 1)
        s = math.sin(math.pi * t) * bend
        out.append((a[0] + (b[0] - a[0]) * t + s, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t))
    return out


def wordline(m, parent, name, x0, x1, z0, z1, y0, y1):
    """A control-gate strip spanning the cell width, cut at z = 0 like the cells."""
    g = empty(name, parent)
    bx(f"{name}_wl", (x0, y0, z0), (x1, y1, z1), m["nand_cg"], g)
    return g


def stack_3d(m, parent, name, x0, x1, z0, z1, y0, layers=8, pitch=4.0):
    """A 3D NAND block: `layers` word-line plates stacked in oxide, and a channel hole down the middle
    that rises a little above the top so the glow reads. Returns the top centre and the hole points."""
    g = empty(name, parent)
    top = y0 + layers * pitch
    bx(f"{name}_ox", (x0, y0, z0), (x1, top, z1), m["nand_ox"], g)
    t = pitch * 0.45
    for k in range(layers):
        yb = y0 + k * pitch + (pitch - t) / 2
        bx(f"{name}_wl{k}", (x0 + 4.0, yb, z0 + 2.0), (x1 - 4.0, yb + t, z1 - 2.0), m["nand_cg"], g)
    xc, zc = (x0 + x1) / 2, (z0 + z1) / 2
    tube(f"{name}_hole", (xc, y0 - 2.0, zc), (xc, top + 6.0, zc), 3.0, m["nand_chan"], g, 12)
    return {"grp": g, "top": (xc, top + 6.0, zc), "hole": [(xc, y0 + k * pitch, zc) for k in range(layers)]}
