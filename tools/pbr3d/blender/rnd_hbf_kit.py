"""The HBF (high-bandwidth flash) stack as reusable Blender pieces for the R&D HBF pictures
(overview now; zooms and sections later). It sits on the HBM STACK kit (hbm_kit.py): the same
silicon interposer, substrate and GPU, the same schematic millimetres, the same cut-away
convention (everything cut at z = 0, camera on +z).

An HBF stack is 16 NAND dies on a base die. Each NAND die is two bonded layers, as in SanDisk's
CBA (CMOS directly bonded to array): a CMOS logic layer underneath and the NAND array on top.
The dies are thinner than the HBM kit's DRAM dies so that a 16-high HBF stack comes out the same
height as the overview's 8-high HBM stack: the spec puts HBF's stack height close to HBM4's.
Sizes are schematic, not to scale.

Stack layout (y up, the base die's floor at y = 0):
  base die        y 0 .. BASE_T                  (the UCIe link strip on the GPU side)
  bump layer      below die k, NB_T thick
  NAND die k      bottom = BASE_T + NB_T + k*NPITCH: CMOS layer CMOS_T, then array ARRAY_T

Every part is built at absolute coordinates under group empties at the origin, so cut faces stay
at z = 0; motion is keyed on the group empties only.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import P, box, empty, key, mat, tube  # noqa: E402
import hbm_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, BASE_T, DIE_HALF, TSV_X, TSV_R, BUMP_R  # noqa: E402

N_DIES = 16
CMOS_T = 7.0  # the logic layer under the array
ARRAY_T = 13.0  # the NAND array layer
NAND_T = CMOS_T + ARRAY_T
NB_T = 10.0  # microbump gap between NAND dies
NPITCH = NAND_T + NB_T

HBM_XS = (-1500.0, -850.0)  # HBM on the left of the GPU
HBF_XS = (850.0, 1500.0)  # HBF on the right
BACK_Z = -600.0  # the centre (z) of the extra row of HBF stacks in the six-stack beat
BACK_XS = (-1500.0, -850.0, 850.0, 1500.0)

STRINGS = 9  # vertical NAND strings drawn on each array layer's cut face


def nand_bottom(k):
    return BASE_T + NB_T + k * NPITCH


def nand_top(k):
    return nand_bottom(k) + NAND_T


HBF_TOP = nand_top(N_DIES - 1)


def mats(m):
    """The HBM kit's materials plus the flash stack's own."""
    K.mats(m)
    m["array"] = mat("nand_array", (0.18, 0.68, 0.62), rough=0.45)
    m["cmos"] = mat("nand_cmos", (0.28, 0.30, 0.42), metal=0.35, rough=0.4)
    m["string"] = mat("nand_string", (0.70, 0.95, 0.88), rough=0.3)
    m["bond"] = mat("cba_bond", (0.75, 1.0, 0.95), emit=(0.6, 1.0, 0.9), strength=3.0)
    m["ucie"] = mat("ucie_edge", (0.95, 0.80, 0.35), metal=0.4, rough=0.3)
    m["gpu_glow"] = mat("gpu_glow", (0.70, 0.45, 1.0), emit=(0.62, 0.38, 1.0), strength=1.4)
    m["page"] = mat("flash_page", (0.40, 1.0, 0.75), emit=(0.35, 1.0, 0.7), strength=3.0)
    return m


class FlashStack:
    """Handles on one built HBF stack."""

    def __init__(self, g, base, dies, arrays, bonds, bumps):
        self.g = g
        self.base = base
        self.dies = dies  # die k's group: moves with the die
        self.arrays = arrays  # the array layer of die k, nested in die k's group
        self.bonds = bonds  # the glowing bond line of die k (the caller show()s it)
        self.bumps = bumps


def flash_stack(root, m, x, name, z0=0.0, detail=True, ucie=-1):
    """A 16-high HBF stack centred on x, its front face at z0 (z0 = 0 is the cut plane). `detail`
    draws the TSVs and the NAND strings on the cut face (front row only). `ucie` puts the link
    strip on the x side facing the GPU."""
    zb, zf = z0 - DIE_HALF, z0  # the dies are cut in half at the front face, as in hbm_kit
    g = empty(name, root)
    base = empty(f"{name}_base", g)
    box(f"{name}_base_die", (x - BASE_HALF, 0, z0 - BASE_HALF), (x + BASE_HALF, BASE_T, zf), m["base"], base)
    if ucie:
        lo, hi = K.span(x + ucie * (BASE_HALF - 36), x + ucie * (BASE_HALF + 2))
        box(f"{name}_ucie", (lo, 10, z0 - BASE_HALF + 40), (hi, BASE_T - 10, zf - 40), m["ucie"], base)

    dies, arrays, bonds, bumps = [], [], [], []
    for k in range(N_DIES):
        bot = nand_bottom(k)
        mid = bot + CMOS_T
        top = mid + ARRAY_T
        d = empty(f"{name}_die{k}", g)
        box(f"{name}_cmos{k}", (x - DIE_HALF, bot, zb), (x + DIE_HALF, mid, zf), m["cmos"], d)
        a = empty(f"{name}_arr{k}", d)
        box(f"{name}_array{k}", (x - DIE_HALF, mid, zb), (x + DIE_HALF, top, zf), m["array"], a)
        if detail:
            for s in range(STRINGS):
                sx = x - DIE_HALF + 2 * DIE_HALF * (s + 0.5) / STRINGS
                box(f"{name}_str{k}_{s}", (sx - 3, mid + 2, zf - 2), (sx + 3, top - 2, zf + 1.5), m["string"], a)
            for i, tx in enumerate(TSV_X):
                tube(f"{name}_tsv{k}_{i}", (x + tx, bot - NB_T, zf), (x + tx, top, zf), TSV_R * 0.8, m["copper"], d, verts=10)
        bd = empty(f"{name}_bond{k}", d)
        box(f"{name}_bondl{k}", (x - DIE_HALF - 4, mid - 1.5, zb - 4), (x + DIE_HALF + 4, mid + 1.5, zf + 3), m["bond"], bd)
        b = empty(f"{name}_bump{k}", d)
        for i, tx in enumerate(TSV_X):
            tube(f"{name}_mb{k}_{i}", (x + tx, bot - NB_T, zf), (x + tx, bot, zf), BUMP_R * 0.8, m["bump"], b, verts=10)
        dies.append(d)
        arrays.append(a)
        bonds.append(bd)
        bumps.append(b)
    return FlashStack(g, base, dies, arrays, bonds, bumps)


def gpu_glow(root, m):
    """A glowing plate on the GPU die's top face (the caller show()s it). A whole emissive shell
    washes out the frame, so only the top lights."""
    return K.gbox("gpu_glow", (-K.GPU_X + 20, K.GPU_Y1, -K.GPU_Z + 20), (K.GPU_X - 20, K.GPU_Y1 + 5, -20), m["gpu_glow"], root)


def lift(stk, keys, step):
    """Die k of `stk` rises by amount * step * (k + 1) over `keys` [(frame, amount)]."""
    for k, d in enumerate(stk.dies):
        for f, a in keys:
            key(d, f, "location", P(0, a * step * (k + 1), 0))


def bus_path(x, phy_edge_off=BASE_HALF + 4):
    """The bus from a stack's link strip to the GPU's near edge across the interposer: inner
    stacks run straight in, outer ones arc over their neighbour."""
    side = 1 if x < 0 else -1
    edge = x + side * phy_edge_off
    gx = -K.GPU_X if side > 0 else K.GPU_X
    if abs(x) < 1000:
        return [(edge, 50.0, 0.0), (gx, 180.0, 0.0)]
    return [(edge, 50.0, 0.0), (edge, 660.0, 0.0), (gx, 660.0, 0.0), (gx, 220.0, 0.0)]

