"""The HBM stack as reusable Blender pieces for the HBM STACK pictures (overview, zooms, sections):
DRAM dies on a base logic die, copper TSVs and microbumps, the GPU on a silicon interposer over a
substrate, and the stack-height limit plane. Sizes are millimetres of a schematic stack, not to
scale (the page says so). Units and the cut-away convention are the SAND template's
(docs/diagram-pages.md): everything is cut at z = 0 and the camera sits on +z.

Every part is built at absolute coordinates under a group empty at the origin, so cut() and the
z = 0 plane hold. Movement is keyed on the group empties (die groups, bump groups), never on a
cut mesh.

Stack layout (y up, the base die's floor at y = 0):
  base logic die  y 0 .. BASE_T
  bump layer      BASE_T + k*PITCH .. + BUMP_T   (below die k)
  DRAM die k      bottom = BASE_T + BUMP_T + k*PITCH, DIE_T thick
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, disc, empty, key, label, mat, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
from poly_overview import run  # noqa: E402

END = F(40, 0)  # "until the end" for intervals; later than any scene

DIE_HALF = 170.0  # half the width of a DRAM die (x and z)
DIE_T = 40.0  # a thinned die (the page: 30-50 um)
BUMP_T = 20.0  # the microbump gap between dies
PITCH = DIE_T + BUMP_T
BASE_T = 70.0
BASE_HALF = 190.0
TSV_X = (-110.0, 0.0, 110.0)  # the copper columns seen in the cut face
TSV_R, BUMP_R = 9.0, 11.0

GPU_X, GPU_Y1, GPU_Z = 500.0, 380.0, 450.0
INTER_X, INTER_Y0, INTER_Z = 1900.0, -120.0, 900.0
SUB_X, SUB_Y0, SUB_Z = 2300.0, -320.0, 1000.0
STACK_XS = (-1500.0, -850.0, 850.0, 1500.0)  # four stacks, two either side of the GPU

# The stack-height limit, on the schematic scale: 720 um and 775 um of the page map to these
# heights (a 16-high stack reaches about 1030 mm here).
LIMIT_OLD_Y, LIMIT_NEW_Y = 960.0, 1040.0

DIE_TOP_16 = BASE_T + BUMP_T + 15 * PITCH + DIE_T  # top of a 16-high stack


def die_bottom(k):
    return BASE_T + BUMP_T + k * PITCH


def die_top(k):
    return die_bottom(k) + DIE_T


def mats(m):
    """The stack's materials, added to the ones `start` made."""
    m["dram"] = mat("dram_die", (0.93, 0.52, 0.18), rough=0.45)
    m["base"] = mat("base_die", (0.25, 0.45, 0.95), metal=0.2, rough=0.4)
    m["phy"] = mat("phy_edge", (0.45, 0.85, 0.95), metal=0.4, rough=0.3)
    m["copper"] = mat("copper_tsv", (0.85, 0.50, 0.30), metal=0.9, rough=0.3)
    m["bump"] = mat("microbump", (1.0, 0.85, 0.20), emit=(1.0, 0.82, 0.15), strength=1.2, rough=0.35)
    m["gpu"] = mat("gpu_die", (0.55, 0.32, 0.90), metal=0.2, rough=0.4)
    m["interposer"] = mat("interposer", (0.55, 0.58, 0.62), metal=0.8, rough=0.3)
    m["substrate"] = mat("package_substrate", (0.20, 0.45, 0.25), rough=0.8)
    m["limit"] = mat("height_limit", (1.0, 0.45, 0.70), emit=(1.0, 0.4, 0.65), strength=1.2)
    m["hot"] = mat("heat_glow", (1.0, 0.42, 0.15), emit=(1.0, 0.38, 0.10), strength=2.2, rough=0.5)
    m["heat"] = mat("heat_dot", (1.0, 0.55, 0.20), emit=(1.0, 0.5, 0.15), strength=3.0)
    m["data"] = mat("data_cyan", (0.30, 0.95, 1.0), emit=(0.25, 0.9, 1.0), strength=3.0)
    m["read"] = mat("read_yellow", (1.0, 0.92, 0.35), emit=(1.0, 0.9, 0.3), strength=3.0)
    m["ghost"] = mat("ghost_die", (0.60, 0.75, 0.95), rough=0.2, alpha=0.18)
    m["wafer"] = mat("wafer", (0.72, 0.74, 0.78), metal=0.6, rough=0.3)
    m["plinth"] = mat("hbm_plinth", (0.18, 0.19, 0.23), rough=0.8)
    m["paper"] = mat("hbm_paper", (0.90, 0.88, 0.82), rough=0.85)
    m["grey"] = mat("hbm_grey", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    m["gold"] = mat("hbm_gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["gold_glow"] = mat("hbm_gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["steel"] = m.get("steel") or mat("steel", (0.35, 0.37, 0.42), metal=0.6, rough=0.4)
    return m


def span(a, b):
    return (min(a, b), max(a, b))


class Stack:
    """Handles on one built stack: its group, its base die, and per-die groups."""

    def __init__(self, g, base, dies, bumps, glows):
        self.g = g
        self.base = base
        self.dies = dies  # die k's group: moves with the die
        self.bumps = bumps  # the bump layer under die k, nested in die k's group
        self.glows = glows  # heat-glow plate on die k (or None)


def stack(root, m, x, n, name, phy=0, glow=False, tsv=True):
    """A stack of `n` DRAM dies on a base logic die, centred on x, cut at z = 0. `phy` is +1 or -1
    to put the PHY strip on the x side that faces the GPU (0: none). `glow` adds a heat plate to
    each die; the caller show()s each plate, since a plate with no show stays on."""
    g = empty(name, root)
    base = empty(f"{name}_base", g)
    box(f"{name}_base_die", (x - BASE_HALF, 0, -BASE_HALF), (x + BASE_HALF, BASE_T, 0), m["base"], base)
    if phy:
        lo, hi = span(x + phy * (BASE_HALF - 36), x + phy * (BASE_HALF + 2))
        box(f"{name}_phy", (lo, 10, -BASE_HALF + 40), (hi, BASE_T - 10, -40), m["phy"], base)

    dies, bumps, glows = [], [], []
    for k in range(n):
        bot, top = die_bottom(k), die_top(k)
        d = empty(f"{name}_die{k}", g)
        box(f"{name}_dram{k}", (x - DIE_HALF, bot, -DIE_HALF), (x + DIE_HALF, top, 0), m["dram"], d)
        if tsv:
            for i, tx in enumerate(TSV_X):
                tube(f"{name}_tsv{k}_{i}", (x + tx, bot - BUMP_T, 0), (x + tx, top, 0), TSV_R, m["copper"], d, verts=10)
        b = empty(f"{name}_bump{k}", d)
        for i, tx in enumerate(TSV_X):
            tube(f"{name}_mb{k}_{i}", (x + tx, bot - BUMP_T, 0), (x + tx, bot, 0), BUMP_R, m["bump"], b, verts=10)
        dies.append(d)
        bumps.append(b)
        if glow:
            gl = empty(f"{name}_glow{k}", d)
            box(f"{name}_heat{k}", (x - DIE_HALF - 6, bot - 4, -DIE_HALF - 6), (x + DIE_HALF + 6, top + 4, 4), m["hot"], gl)
            glows.append(gl)  # the caller must show() it, or it stays on
        else:
            glows.append(None)
    return Stack(g, base, dies, bumps, glows)


def gbox(name, lo, hi, m, parent=None):
    """A box inside a group empty, which is the object to show() or key. box() keeps the size in
    the object's own scale, so animating a bare box would reset its size to 1 mm."""
    g = empty(name, parent)
    box(f"{name}_m", lo, hi, m, g)
    return g


def package(root, m):
    """The silicon interposer, the package substrate and the GPU die on top of the interposer."""
    gbox("interposer", (-INTER_X, INTER_Y0, -INTER_Z), (INTER_X, 0, 0), m["interposer"], root)
    gbox("substrate", (-SUB_X, SUB_Y0, -SUB_Z), (SUB_X, INTER_Y0, 0), m["substrate"], root)
    gbox("gpu", (-GPU_X, 0, -GPU_Z), (GPU_X, GPU_Y1, 0), m["gpu"], root)


def lift(stk, keys, step=35.0):
    """Lifts die k of `stk` by amount * step * (k + 1) over the frames of `keys` (a list of
    (frame, amount)). Amount 0 is the closed stack, 1 the pulled-apart one."""
    for k, d in enumerate(stk.dies):
        for f, a in keys:
            key(d, f, "location", P(0, a * step * (k + 1), 0))


def limit_plane(root, m, x0, x1, y, z0=-900.0, name="limit", intervals=()):
    """A translucent plane at height y, shown during `intervals`."""
    g = gbox(name, (x0, y - 6, z0), (x1, y + 6, 0), m["limit"], root)
    show(g, list(intervals))
    return g


def dots(root, m, name, pts, n, mat_key, b, u0, u1, life, size=14.0):
    """Blobs that travel the absolute polyline `pts` through beat `b`."""
    return run(root, name, n, pts, size, m[mat_key], b, u0, u1, life)
