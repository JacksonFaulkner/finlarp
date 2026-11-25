"""Part kit for the PACKAGING tab's ASSEMBLY page (pkg_assembly_*.py): one CoWoS-S package cut open
along z = 0 (the camera sits on +z), drawn layer by layer so every assembly step can move, glow or
vanish on its own, plus the factory tools that do the steps.

Units: Y up, x across the package, z toward the camera. Heights are stretched (about 6x) so thin
layers read; widths are roughly to scale with one unit ~ 0.5 mm.

  package   bottom to top, each layer its own group (`L[name]` = (vis, mov) empties):
            bga    solder balls under the substrate (front row cut in half)
            sub    organic substrate: bottom ABF build-up, glass-cloth core with plated through-holes,
                   top ABF build-up, solder mask; copper lines, microvia stacks and PTHs on the cut face
            c4     C4 bumps (~130 um) between substrate and interposer
            uf2    the interposer-level underfill
            ip     silicon interposer: TSV columns, the RDL wiring on top (three copper levels)
            ub     microbumps: copper pillars with solder caps under the die and the HBM
            uf1    the die-level underfill
            die    the logic die face down: BEOL metal stack below, silicon above
            hbm    four HBM stacks (two a side); the front pair cut: base die, 8 DRAM dies, TSVs
            mold   molding compound in the gaps round the dies
            tim    thermal interface (indium) on the die and stacks
            lid    copper lid: a top plate and a ring of legs glued to the substrate
  tools     interposer wafer with its sites, pick-and-place head, dicing blade, back-grind wheel,
            underfill needle, probe card, test socket, carrier, conveyor
  paths     signal (HBM to die through the RDL), power (BGA up to the die), heat (die up the lid)

Bead, camera and show helpers come from power_vrm_detail (run, rise, present, frame, camera_path).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, cut, disc, empty, key, show, tube, mat  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, join, run, rise, present, frame, camera_path, bead, blink  # noqa: E402,F401

# ---- materials ------------------------------------------------------------------------------


def materials():
    return {
        "a_mask": mat("asm_mask", (0.10, 0.32, 0.20), rough=0.55),
        "a_abf": mat("asm_abf", (0.62, 0.52, 0.30), rough=0.75),
        "a_core": mat("asm_core", (0.36, 0.40, 0.26), rough=0.8),
        "a_cu": mat("asm_cu", (0.86, 0.52, 0.30), metal=0.9, rough=0.3),
        "a_solder": mat("asm_solder", (0.78, 0.79, 0.82), metal=0.9, rough=0.25),
        "a_si": mat("asm_si", (0.36, 0.40, 0.46), metal=0.5, rough=0.35),
        "a_oxide": mat("asm_oxide", (0.40, 0.47, 0.56), metal=0.2, rough=0.4),
        "a_die": mat("asm_die", (0.42, 0.30, 0.72), metal=0.3, rough=0.35),
        "a_beol": mat("asm_beol", (0.62, 0.50, 0.85), metal=0.4, rough=0.35),
        "a_dram": mat("asm_dram", (0.93, 0.55, 0.20), rough=0.45),
        "a_base": mat("asm_base", (0.25, 0.45, 0.95), metal=0.2, rough=0.4),
        "a_fill": mat("asm_fill", (0.09, 0.08, 0.08), rough=0.9),
        "a_mold": mat("asm_mold", (0.17, 0.18, 0.20), rough=0.8),
        "a_tim": mat("asm_tim", (0.85, 0.86, 0.90), metal=0.9, rough=0.2),
        "a_lid": mat("asm_lid", (0.80, 0.56, 0.38), metal=0.85, rough=0.3),
        "a_glue": mat("asm_glue", (0.85, 0.80, 0.60), rough=0.7),
        "a_tool": mat("asm_tool", (0.60, 0.63, 0.68), metal=0.8, rough=0.35),
        "a_dark": mat("asm_dark", (0.14, 0.15, 0.18), metal=0.4, rough=0.5),
        "a_blade": mat("asm_blade", (0.80, 0.82, 0.86), metal=0.95, rough=0.15),
        "a_glass": mat("asm_glass", (0.55, 0.75, 0.90), rough=0.1, alpha=0.45),
        "a_wafer": mat("asm_wafer", (0.30, 0.34, 0.40), metal=0.6, rough=0.25),
        "a_belt": mat("asm_belt", (0.12, 0.12, 0.14), rough=0.8),
        "a_tray": mat("asm_tray", (0.20, 0.22, 0.30), rough=0.7),
        # glows (beads small, so 6-8; big parts 1-2)
        "g_sig": mat("asm_g_sig", (0.30, 0.90, 1.0), emit=(0.20, 0.88, 1.0), strength=7.0),
        "g_pwr": mat("asm_g_pwr", (1.0, 0.85, 0.25), emit=(1.0, 0.80, 0.20), strength=7.0),
        "g_heat": mat("asm_g_heat", (1.0, 0.50, 0.20), emit=(1.0, 0.42, 0.12), strength=5.0),
        "g_reflow": mat("asm_g_reflow", (1.0, 0.55, 0.25), emit=(1.0, 0.45, 0.15), strength=3.0),
        "g_hot": mat("asm_g_hot", (0.95, 0.40, 0.15), emit=(1.0, 0.38, 0.10), strength=1.4),
        "g_good": mat("asm_g_good", (0.30, 1.0, 0.45), emit=(0.25, 1.0, 0.40), strength=2.0),
        "g_bad": mat("asm_g_bad", (1.0, 0.15, 0.10), emit=(1.0, 0.10, 0.06), strength=2.0),
        "g_good_a": mat("asm_g_good_a", (0.30, 1.0, 0.45), emit=(0.25, 1.0, 0.40), strength=1.5, alpha=0.55),
        "g_bad_a": mat("asm_g_bad_a", (1.0, 0.15, 0.10), emit=(1.0, 0.10, 0.06), strength=1.5, alpha=0.6),
        "g_epoxy": mat("asm_g_epoxy", (0.35, 0.30, 0.25), emit=(0.30, 0.22, 0.12), strength=1.0),
        "g_probe": mat("asm_g_probe", (0.55, 0.45, 1.0), emit=(0.50, 0.40, 1.0), strength=6.0),
        "g_cool": mat("asm_g_cool", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=4.0),
    }


# ---- layout (y bands) -----------------------------------------------------------------------

BGA_Y = (-9.0, -5.0)
SUB_Y = (-5.0, 5.0)
SB_BU = (-4.6, -1.5)  # bottom build-up
SB_CORE = (-1.5, 1.5)
SB_TU = (1.5, 4.6)  # top build-up
C4_Y = (5.0, 7.0)
IP_Y = (7.0, 10.8)
RDL_Y = (10.0, 10.8)
UB_Y = (10.8, 11.6)
DIE_Y = (11.6, 15.0)
BEOL_Y = (11.6, 12.4)
TIM_Y = (15.0, 15.6)
LID_Y = (15.6, 18.0)

SUB_X, SUB_Z = 56.0, -84.0  # half width, back edge
IP_X, IP_Z = 44.0, -64.0
DIE_X, DIE_Z = 16.0, -44.0
HBM_X = (19.0, 33.0)  # right side; mirrored
HBM_ZS = ((-15.0, 0.0), (-36.0, -21.0))
LID_X, LID_Z = 54.0, -82.0
CZ = -32.0  # centre z of the interposer (and the die)

C4_XS = [-42.0 + 2.8 * i for i in range(31)]
BGA_XS = [-52.0 + 4.0 * i for i in range(27)]


def layer(name, parent):
    """A (vis, mov) pair: show/present `vis`, key `mov`'s location; parts go under `mov`."""
    vis = empty(f"{name}_vis", parent)
    mov = empty(f"{name}_mov", vis)
    return vis, mov


def _row_balls(name, xs, y, r, mt, g, zs=(0.0,), segs=10):
    parts = []
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            b = ball(f"{name}{j}_{i}", (x, y, z), r, mt, g, segs)
            if z == 0.0:
                cut(b, 0.0)
            parts.append(b)
    return join(parts, name)


# ---- package layers ---------------------------------------------------------------------------


def bga(m, g):
    _row_balls("bga", BGA_XS, (BGA_Y[0] + BGA_Y[1]) / 2, 1.7, m["a_solder"], g, zs=(0.0, -4.0, -8.0))


def substrate(m, g):
    x, z0 = SUB_X, SUB_Z
    bx("sub_mask_b", (-x, SUB_Y[0], z0), (x, SB_BU[0], 0.0), m["a_mask"], g)
    bx("sub_bu_b", (-x, SB_BU[0], z0), (x, SB_BU[1], 0.0), m["a_abf"], g)
    bx("sub_core", (-x, SB_CORE[0], z0), (x, SB_CORE[1], 0.0), m["a_core"], g)
    bx("sub_bu_t", (-x, SB_TU[0], z0), (x, SB_TU[1], 0.0), m["a_abf"], g)
    bx("sub_mask_t", (-x, SB_TU[1], z0), (x, SUB_Y[1], 0.0), m["a_mask"], g)
    cu = []
    # copper planes / lines in each build-up level, broken into segments on the cut face
    for k, y in enumerate((-4.0, -3.0, -2.0, 2.0, 3.0, 4.0)):
        xs = -x + 2.0
        i = 0
        while xs < x - 4.0:
            w = 5.0 + 3.0 * ((i * 7 + k * 3) % 4)
            cu.append(bx(f"sub_ln{k}_{i}", (xs, y - 0.22, -1.2), (min(xs + w, x - 2.0), y + 0.22, 0.12), m["a_cu"], g))
            xs += w + 1.6
            i += 1
    # plated through-holes through the core, with lands
    for i, xp in enumerate(range(-48, 49, 8)):
        cu.append(bx(f"sub_pth{i}", (xp - 0.9, SB_CORE[0] - 0.3, -1.6), (xp + 0.9, SB_CORE[1] + 0.3, 0.12), m["a_cu"], g))
        cu.append(bx(f"sub_pthl{i}", (xp - 1.8, SB_CORE[1], -1.6), (xp + 1.8, SB_CORE[1] + 0.35, 0.12), m["a_cu"], g))
        cu.append(bx(f"sub_pthb{i}", (xp - 1.8, SB_CORE[0] - 0.35, -1.6), (xp + 1.8, SB_CORE[0], 0.12), m["a_cu"], g))
    # stacked microvias up through the build-up to the C4 pads and down to the BGA pads
    for i, xc in enumerate(C4_XS[::2]):
        for k, (ya, yb) in enumerate(((SB_TU[0], 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, SUB_Y[1]))):
            off = 0.6 * ((k + i) % 2)
            cu.append(bx(f"sub_uv{i}_{k}", (xc - 0.45 + off, ya, -1.0), (xc + 0.45 + off, yb, 0.14), m["a_cu"], g))
    for i, xb in enumerate(BGA_XS[1:-1:2]):
        for k, (ya, yb) in enumerate(((SUB_Y[0], -4.0), (-4.0, -3.0), (-3.0, -2.0), (-2.0, SB_BU[1]))):
            cu.append(bx(f"sub_dv{i}_{k}", (xb - 0.5, ya, -1.0), (xb + 0.5, yb, 0.14), m["a_cu"], g))
    join(cu, "sub_copper")
    # pads on top for the C4, a few land-side caps under
    pads = [bx(f"sub_pad{i}", (xc - 0.9, SUB_Y[1], -1.0), (xc + 0.9, SUB_Y[1] + 0.2, 0.1), m["a_cu"], g) for i, xc in enumerate(C4_XS)]
    join(pads, "sub_pads")
    for i, xc in enumerate((-48.0, 48.0)):
        for j, zc in enumerate((-20.0, -60.0)):
            bx(f"sub_cap{i}{j}_b", (xc - 2.5, SUB_Y[1], zc - 1.4), (xc + 2.5, SUB_Y[1] + 1.4, zc + 1.4), m["mlcc"], g)
            for e in (-1, 1):
                bx(f"sub_cap{i}{j}_e{e}", (xc + e * 2.5 - 0.6 * (e > 0), SUB_Y[1], zc - 1.4), (xc + e * 2.5 + 0.6 * (e < 0), SUB_Y[1] + 1.4, zc + 1.4), m["mlcc_end"], g)


def c4(m, g):
    _row_balls("c4", C4_XS, (C4_Y[0] + C4_Y[1]) / 2, 1.05, m["a_solder"], g, zs=(0.0, -3.0))


def uf2(m, g):
    bx("uf2", (-IP_X + 0.2, C4_Y[0], IP_Z + 0.4), (IP_X - 0.2, C4_Y[1], -0.06), m["a_fill"], g)
    for s in (-1, 1):  # fillet: a sloped bead along the side
        bx(f"uf2_fil{s}", (s * IP_X, C4_Y[0], IP_Z), (s * (IP_X + 1.6), C4_Y[0] + 1.0, -0.06), m["a_fill"], g)
        bx(f"uf2_fil2{s}", (s * IP_X, C4_Y[0] + 1.0, IP_Z), (s * (IP_X + 0.8), C4_Y[1] - 0.2, -0.06), m["a_fill"], g)


def interposer(m, g):
    bx("ip_si", (-IP_X, IP_Y[0], IP_Z), (IP_X, RDL_Y[0], 0.0), m["a_si"], g)
    bx("ip_rdl", (-IP_X, RDL_Y[0], IP_Z), (IP_X, RDL_Y[1], 0.0), m["a_oxide"], g)
    cu = []
    for i, xc in enumerate(C4_XS):  # TSVs down from the RDL to every C4 pad
        cu.append(bx(f"ip_tsv{i}", (xc - 0.32, IP_Y[0], -0.9), (xc + 0.32, RDL_Y[0], 0.12), m["a_cu"], g))
        cu.append(bx(f"ip_tpad{i}", (xc - 0.8, IP_Y[0] - 0.15, -0.9), (xc + 0.8, IP_Y[0], 0.12), m["a_cu"], g))
    for k, y in enumerate((10.2, 10.45, 10.68)):
        xs, i = -IP_X + 1.0, 0
        while xs < IP_X - 2.0:
            w = 1.2 + 0.8 * ((i + k) % 3)
            cu.append(bx(f"ip_rl{k}_{i}", (xs, y - 0.07, -0.8), (xs + w, y + 0.07, 0.12), m["a_cu"], g))
            xs += w + 0.5
            i += 1
    join(cu, "ip_copper")
    # the HBM-to-die links, picked out across the RDL (x 14..22 each side)
    for s in (-1, 1):
        bx(f"ip_link{s}", (s * 13.0, 10.40, -0.5), (s * 22.0, 10.52, 0.16), m["a_cu"], g)


def ubumps(m, g):
    xs = [x * 0.9 for x in range(-17, 18)] + [s * (19.6 + 0.9 * k) for s in (-1, 1) for k in range(15)]
    parts = []
    for i, x in enumerate(xs):
        parts.append(bx(f"ub_p{i}", (x - 0.24, UB_Y[0], -0.5), (x + 0.24, UB_Y[0] + 0.5, 0.12), m["a_cu"], g))
        b = ball(f"ub_c{i}", (x, UB_Y[0] + 0.58, 0.0), 0.26, m["a_solder"], g, 8)
        cut(b, 0.0)
        parts.append(b)
    join(parts, "ubumps")


def uf1(m, g):
    for k, (x0, x1, z0, z1) in enumerate([(-DIE_X, DIE_X, DIE_Z, 0.0)] + [(s * HBM_X[0], s * HBM_X[1], a, b) for s in (-1, 1) for a, b in HBM_ZS]):
        a, b = sorted((x0, x1))
        bx(f"uf1_{k}", (a - 0.6, UB_Y[0], z0 - 0.6), (b + 0.6, UB_Y[1], min(z1 + 0.6, -0.06)), m["a_fill"], g)


def die(m, g):
    bx("die_beol", (-DIE_X, BEOL_Y[0], DIE_Z), (DIE_X, BEOL_Y[1], 0.0), m["a_beol"], g)
    bx("die_si", (-DIE_X, BEOL_Y[1], DIE_Z), (DIE_X, DIE_Y[1], 0.0), m["a_die"], g)
    cu = []
    for k, y in enumerate((11.75, 11.92, 12.08, 12.24)):
        xs, i = -DIE_X + 0.4, 0
        while xs < DIE_X - 1.0:
            w = 0.6 + 0.5 * k + 0.3 * (i % 3)
            cu.append(bx(f"die_m{k}_{i}", (xs, y - 0.05, -0.6), (xs + w, y + 0.05, 0.12), m["a_cu"], g))
            xs += w + 0.35
            i += 1
    join(cu, "die_metal")
    bx("die_fet", (-DIE_X + 0.3, BEOL_Y[1], -0.6), (DIE_X - 0.3, BEOL_Y[1] + 0.12, 0.12), m["a_oxide"], g)


def hbm(m, g, n=8):
    """Four stacks; each its own sub-group (returned) so they can be placed one at a time."""
    out = []
    y0, y1 = DIE_Y
    base = 0.8
    pitch = (y1 - y0 - base) / n
    for s in (-1, 1):
        for j, (z0, z1) in enumerate(HBM_ZS):
            sg = empty(f"hbm{s}{j}", g)
            xa, xb = sorted((s * HBM_X[0], s * HBM_X[1]))
            bx(f"hbm{s}{j}_base", (xa, y0, z0), (xb, y0 + base, z1), m["a_base"], sg)
            for k in range(n):
                yb = y0 + base + k * pitch
                bx(f"hbm{s}{j}_g{k}", (xa + 0.3, yb, z0 + 0.3), (xb - 0.3, yb + 0.12, z1 - (0.0 if z1 == 0.0 else 0.3)), m["a_fill"], sg)
                bx(f"hbm{s}{j}_d{k}", (xa, yb + 0.12, z0), (xb, yb + pitch, z1), m["a_dram"], sg)
            tsv = [bx(f"hbm{s}{j}_t{i}", (xa + 2.5 + 2.2 * i - 0.18, y0 + 0.2, z1 - 0.7), (xa + 2.5 + 2.2 * i + 0.18, y1 - 0.15, z1 + 0.1), m["a_cu"], sg)
                   for i in range(5)]
            join(tsv, f"hbm{s}{j}_tsv")
            out.append(sg)
    return out


def mold(m, g):
    for s in (-1, 1):
        bx(f"mold_gap{s}", (s * (DIE_X + 0.2), UB_Y[1], DIE_Z), (s * (HBM_X[0] - 0.2), DIE_Y[1], -0.02), m["a_mold"], g)
        bx(f"mold_out{s}", (s * (HBM_X[1] + 0.2), UB_Y[0], IP_Z + 2.0), (s * (IP_X - 1.0), DIE_Y[1], -0.02), m["a_mold"], g)
    bx("mold_back", (-IP_X + 1.0, UB_Y[0], IP_Z + 2.0), (IP_X - 1.0, DIE_Y[1], DIE_Z - 0.2), m["a_mold"], g)


def tim(m, g):
    bx("tim", (-HBM_X[1], TIM_Y[0], DIE_Z), (HBM_X[1], TIM_Y[1], 0.0), m["a_tim"], g)


def lid(m, g):
    bx("lid_top", (-LID_X, LID_Y[0], LID_Z), (LID_X, LID_Y[1], 0.0), m["a_lid"], g)
    for s in (-1, 1):
        bx(f"lid_leg{s}", (s * (LID_X - 4.0), SUB_Y[1] + 0.4, LID_Z), (s * LID_X, LID_Y[0], 0.0), m["a_lid"], g)
        bx(f"lid_glue{s}", (s * (LID_X - 4.0), SUB_Y[1], LID_Z), (s * LID_X, SUB_Y[1] + 0.4, 0.0), m["a_glue"], g)
    bx("lid_legb", (-LID_X, SUB_Y[1] + 0.4, LID_Z), (LID_X, LID_Y[0], LID_Z + 4.0), m["a_lid"], g)


ORDER = ["bga", "sub", "c4", "uf2", "ip", "ub", "uf1", "die", "hbm", "mold", "tim", "lid"]
BUILD = {"bga": bga, "sub": substrate, "c4": c4, "uf2": uf2, "ip": interposer, "ub": ubumps, "uf1": uf1, "die": die,
         "hbm": hbm, "mold": mold, "tim": tim, "lid": lid}


def package(m, root, parts=None, name="pk"):
    """The cut-open package; returns {"L": {layer: (vis, mov)}, "hbm": [stack groups], "glow": {...}}."""
    parts = ORDER if parts is None else parts
    L, out = {}, {}
    for p in parts:
        vis, mov = layer(f"{name}_{p}", root)
        r = BUILD[p](m, mov)
        L[p] = (vis, mov)
        if p == "hbm":
            out["hbm"] = r
    out["L"] = L
    glow = {}
    if "die" in parts:
        gd = empty(f"{name}_die_hot", root)
        bx(f"{name}_die_hot_t", (-DIE_X + 0.3, DIE_Y[1], DIE_Z + 0.3), (DIE_X - 0.3, DIE_Y[1] + 0.25, -0.1), m["g_hot"], gd)
        bx(f"{name}_die_hot_f", (-DIE_X + 0.3, BEOL_Y[1] + 0.2, -0.05), (DIE_X - 0.3, DIE_Y[1] - 0.2, 0.08), m["g_hot"], gd)
        show(gd, [])
        glow["die"] = gd
    if "c4" in parts:  # reflow glow on the C4 row
        gc = empty(f"{name}_c4_hot", root)
        _row_balls(f"{name}_c4h", C4_XS, (C4_Y[0] + C4_Y[1]) / 2, 1.1, m["g_reflow"], gc)
        show(gc, [])
        glow["c4"] = gc
    if "ub" in parts:
        gu = empty(f"{name}_ub_hot", root)
        xs = [x * 0.9 for x in range(-17, 18, 2)] + [s * (19.6 + 0.9 * k) for s in (-1, 1) for k in range(0, 15, 2)]
        join([ball(f"{name}_ubh{i}", (x, UB_Y[0] + 0.58, 0.05), 0.3, m["g_reflow"], gu, 8) for i, x in enumerate(xs)], f"{name}_ubh")
        show(gu, [])
        glow["ub"] = gu
    out["glow"] = glow
    return out


def move(obj, keys):
    """keys: [(frame, (dx, dy, dz))]: the group's offset from where it is built."""
    for f, d in keys:
        key(obj, f, "location", P(*d))


def drop(L, name, b, u0, u1, h=20.0, hold_from=0):
    """Layer `name` falls from h above into place over [u0, u1] of beat b."""
    mov = L[name][1]
    move(mov, [(F(hold_from, 0.0), (0.0, h, 0.0)), (F(b, u0), (0.0, h, 0.0)), (F(b, u1), (0.0, 0.0, 0.0))])


def vis(L, names, intervals):
    for n in names:
        present(L[n][0], intervals)


# ---- paths -------------------------------------------------------------------------------------


def sig_path(s=1, z=0.6):
    """HBM base die down a microbump, across the RDL link, up a microbump into the die's PHY."""
    return [(s * 26.0, DIE_Y[0] + 0.4, z), (s * 21.5, DIE_Y[0] + 0.3, z), (s * 21.5, UB_Y[0] + 0.4, z), (s * 21.5, 10.46, z),
            (s * 13.5, 10.46, z), (s * 13.5, UB_Y[1], z), (s * 13.5, 12.0, z), (s * 6.0, 12.0, z)]


def pwr_path(x, z=0.7):
    """From a BGA ball up the substrate vias, through a C4, a TSV, the RDL and a microbump into the die."""
    xc = min(C4_XS, key=lambda c: abs(c - x))
    xd = max(-DIE_X + 2.0, min(DIE_X - 2.0, xc * 0.4))
    return [(x, -8.5, z), (x, -5.0, z), (x, 0.0, z), (xc, 3.0, z), (xc, 6.0, z), (xc, 7.2, z), (xc, 10.3, z),
            (xd, 10.6, z), (xd, UB_Y[1], z), (xd, 13.0, z)]


def heat_path(x, z=-8.0, top=40.0):
    return [(x, DIE_Y[1] - 0.5, z), (x, TIM_Y[1], z), (x, LID_Y[1] + 0.4, z), (x * 1.1, top, z)]


def flows(m, root, tag, beats, sig=True, pwr=True, heat=True, u0=0.0, u1=0.8, n=4):
    if sig:
        for s in (-1, 1):
            run(root, f"{tag}_sig{s}", sig_path(s), n, 0.45, m["g_sig"], beats, u0, u1, 50)
    if pwr:
        for x in (-44.0, -28.0, 28.0, 44.0):
            run(root, f"{tag}_pwr{x:+.0f}", pwr_path(x), n, 0.55, m["g_pwr"], beats, u0 + 0.05, u1, 70)
    if heat:
        for x in (-10.0, 0.0, 10.0):
            run(root, f"{tag}_ht{x:+.0f}", heat_path(x), max(2, n - 1), 0.8, m["g_heat"], beats, u0 + 0.1, u1, 60)


# ---- factory tools -----------------------------------------------------------------------------

SITE = 92.0  # interposer pitch on the wafer


def wafer_sites(R=300.0, cz=CZ):
    """Site centres on a 300 mm interposer wafer centred at (0, cz) whose sites fit inside R; the
    hero site is at (0, cz)."""
    out = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            x, z = i * SITE, cz + j * SITE
            if math.hypot(abs(x) + SITE / 2, abs(z - cz) + SITE / 2) <= R + 8.0 and (i, j) != (0, 0):
                out.append((x, z))
    return out


def wafer(m, parent, R=300.0, cz=CZ, cut_front=True, name="wf"):
    """The interposer wafer (silicon, RDL face up) with scribe streets drawn in."""
    g = empty(name, parent)
    w = disc(f"{name}_disc", (0.0, (IP_Y[0] + RDL_Y[1]) / 2, cz), R, RDL_Y[1] - IP_Y[0] - 0.3, m["a_wafer"], g, 128)
    if cut_front:
        cut(w, -0.1)  # just behind the hero interposer's own cut face
    st = []
    for k in range(-4, 5):
        a = (k + 0.5) * SITE
        if abs(a) >= R:
            continue
        h = math.sqrt(R * R - a * a)
        za, zb = cz - R, (0.0 if cut_front else cz + R)
        st.append(bx(f"{name}_sx{k}", (a - 0.6, RDL_Y[1], max(za, cz - h)), (a + 0.6, RDL_Y[1] + 0.05, min(zb, cz + h)), m["a_dark"], g))
        z = cz + a
        if not cut_front or z < 0.0:
            st.append(bx(f"{name}_sz{k}", (-h, RDL_Y[1], z - 0.6), (h, RDL_Y[1] + 0.05, z + 0.6), m["a_dark"], g))
    join(st, f"{name}_streets")
    return g


def site_kit(m, parent, x, z, name, hbm_on=True, die_on=True):
    """A simple die + four stacks on one wafer site (for the sites other than the hero's)."""
    g = empty(name, parent)
    dz = z - CZ
    if die_on:
        bx(f"{name}_die", (x - DIE_X, UB_Y[1], dz + DIE_Z), (x + DIE_X, DIE_Y[1], dz), m["a_die"], g)
    if hbm_on:
        for s in (-1, 1):
            for j, (z0, z1) in enumerate(HBM_ZS):
                xa, xb = sorted((x + s * HBM_X[0], x + s * HBM_X[1]))
                bx(f"{name}_h{s}{j}", (xa, UB_Y[1], dz + z0), (xb, DIE_Y[1], dz + z1), m["a_dram"], g)
    return g


def nozzle(m, parent, name="nz"):
    """Pick-and-place bond head: a vertical shaft, a heated collet block and a vacuum tip (built
    with its tip at y = 0, at x = z = 0)."""
    g = empty(name, parent)
    tube(f"{name}_shaft", (0.0, 6.0, -10.0), (0.0, 60.0, -10.0), 2.6, m["a_tool"], g, 16)
    bx(f"{name}_head", (-10.0, 3.0, -20.0), (10.0, 8.0, 0.0), m["a_dark"], g)
    bx(f"{name}_tip", (-7.0, 0.0, -16.0), (7.0, 3.0, -4.0), m["a_tool"], g)
    return g


def blade(m, parent, name="bl", r=26.0):
    """A dicing blade: a thin disc standing in the y-z plane (spins about x), on its hub."""
    g = empty(name, parent)
    t = tube(f"{name}_disc", (-0.4, 0.0, 0.0), (0.4, 0.0, 0.0), r, m["a_blade"], g, 64)
    tube(f"{name}_hub", (-3.0, 0.0, 0.0), (3.0, 0.0, 0.0), r * 0.45, m["a_tool"], g, 32)
    tube(f"{name}_axle", (3.0, 0.0, 0.0), (40.0, 0.0, 0.0), 3.0, m["a_dark"], g, 16)
    return g, t


def grinder(m, parent, name="gr", r=60.0):
    g = empty(name, parent)
    disc(f"{name}_wheel", (0.0, 3.0, 0.0), r, 6.0, m["a_tool"], g, 96)
    disc(f"{name}_teeth", (0.0, 0.0, 0.0), r * 0.95, 1.0, m["a_dark"], g, 96)
    tube(f"{name}_spindle", (0.0, 6.0, 0.0), (0.0, 60.0, 0.0), 8.0, m["a_dark"], g, 24)
    return g


def needle(m, parent, name="nd"):
    """Underfill dispenser: syringe body and a fine needle, tip at the origin."""
    g = empty(name, parent)
    tube(f"{name}_needle", (0.0, 0.0, 0.0), (0.0, 12.0, 0.0), 0.5, m["a_tool"], g, 10)
    tube(f"{name}_body", (0.0, 12.0, 0.0), (0.0, 40.0, 0.0), 4.0, m["a_glass"], g, 20)
    tube(f"{name}_epoxy", (0.0, 12.5, 0.0), (0.0, 30.0, 0.0), 3.4, m["a_fill"], g, 20)
    tube(f"{name}_plunger", (0.0, 30.0, 0.0), (0.0, 52.0, 0.0), 1.2, m["a_dark"], g, 10)
    return g


def probe_card(m, parent, x0, x1, z0, z1, y, name="pc", pitch=4.0):
    """A probe card: a dark PCB with a ring stiffener and a field of needles pointing down to `y`."""
    g = empty(name, parent)
    bx(f"{name}_pcb", (x0 - 14.0, y + 10.0, z0 - 14.0), (x1 + 14.0, y + 13.0, z1 + 14.0), m["mask"], g)
    bx(f"{name}_st", (x0 - 6.0, y + 13.0, z0 - 6.0), (x1 + 6.0, y + 17.0, z1 + 6.0), m["a_tool"], g)
    bx(f"{name}_head", (x0, y + 6.0, z0), (x1, y + 10.0, z1), m["a_dark"], g)
    pins = []
    x = x0 + 2.0
    i = 0
    while x < x1 - 1.0:
        z = z0 + 2.0
        while z < z1 - 1.0:
            pins.append(tube(f"{name}_p{i}", (x, y, z), (x, y + 6.0, z), 0.25, m["a_tool"], g, 6))
            i += 1
            z += pitch
        x += pitch
    join(pins, f"{name}_pins")
    return g


def socket(m, parent, name="sk"):
    """A final-test socket round the package: a frame, pogo pins under the BGA and a clamp lid."""
    g = empty(name, parent)
    for s in (-1, 1):
        bx(f"{name}_w{s}", (s * (SUB_X + 2.0), -16.0, SUB_Z - 6.0), (s * (SUB_X + 10.0), 2.0, 0.0), m["a_dark"], g)
    bx(f"{name}_wb", (-SUB_X - 10.0, -16.0, SUB_Z - 10.0), (SUB_X + 10.0, 2.0, SUB_Z - 2.0), m["a_dark"], g)
    bx(f"{name}_base", (-SUB_X - 10.0, -20.0, SUB_Z - 10.0), (SUB_X + 10.0, -16.0, 0.0), m["a_dark"], g)
    pins = [tube(f"{name}_pg{i}", (x, -16.0, -1.0), (x, BGA_Y[0], -1.0), 0.5, m["a_tool"], g, 8) for i, x in enumerate(BGA_XS)]
    join(pins, f"{name}_pogo")
    return g


def tray(m, parent, name="tr"):
    """A JEDEC-style tray of tested dies and HBM stacks (as in the old overview), centred at x = -150."""
    g = empty(name, parent)
    bx(f"{name}_tray", (-215.0, -2.0, -80.0), (-85.0, 0.0, 0.0), m["a_tray"], g)
    for i in range(3):
        for j in range(2):
            x, z = -195.0 + 26.0 * i, -60.0 + 34.0 * j
            bx(f"{name}_pk{i}{j}", (x - 10.0, 0.0, z - 13.0), (x + 10.0, 0.6, z + 13.0), m["a_dark"], g)
            bx(f"{name}_d{i}{j}", (x - 8.0, 0.6, z - 11.0), (x + 8.0, 2.4, z + 11.0), m["a_die"], g)
    for i in range(2):
        for j in range(3):
            x, z = -115.0 + 14.0 * i, -66.0 + 22.0 * j
            bx(f"{name}_hb{i}{j}", (x - 4.5, 0.0, z - 5.0), (x + 4.5, 5.0, z + 5.0), m["a_dram"], g)
            bx(f"{name}_hbb{i}{j}", (x - 4.5, 0.0, z - 5.0), (x + 4.5, 0.8, z + 5.0), m["a_base"], g)
    return g


def mini_package(m, parent, x, z, name, s=0.5):
    """A small finished package (lidded) at (x, z), for rows on a line."""
    g = empty(name, parent)
    bx(f"{name}_sub", (x - SUB_X * s, 0.0, z - 84.0 * s), (x + SUB_X * s, 3.0, z), m["a_mask"], g)
    bx(f"{name}_lid", (x - LID_X * s, 3.0, z - 82.0 * s), (x + LID_X * s, 6.0, z - 0.5), m["a_lid"], g)
    return g


def conveyor(m, parent, x0, x1, z0, z1, name="cv"):
    g = empty(name, parent)
    bx(f"{name}_belt", (x0, -2.0, z0), (x1, 0.0, z1), m["a_belt"], g)
    for s, zz in ((0, z0 - 3.0), (1, z1)):
        bx(f"{name}_rail{s}", (x0, -3.0, zz), (x1, 2.0, zz + 3.0), m["a_tool"], g)
    return g


YIELD_PARTS = [
    ("logic die", (-DIE_X, DIE_X, BEOL_Y[1], DIE_Y[1])),
    ("HBM 1", (-HBM_X[1], -HBM_X[0], DIE_Y[0], DIE_Y[1])),
    ("HBM 2", (HBM_X[0], HBM_X[1], DIE_Y[0], DIE_Y[1])),
    ("die bumps", (-DIE_X, DIE_X, UB_Y[0], UB_Y[1])),
    ("HBM bumps", (HBM_X[0], HBM_X[1], UB_Y[0], UB_Y[1])),
    ("interposer", (-IP_X, IP_X, IP_Y[0], RDL_Y[0])),
    ("RDL wiring", (-IP_X, IP_X, RDL_Y[0], RDL_Y[1])),
    ("C4 joints", (-IP_X, IP_X, C4_Y[0], C4_Y[1])),
    ("substrate", (-SUB_X, SUB_X, SUB_Y[0], SUB_Y[1])),
    ("BGA", (-SUB_X, SUB_X, BGA_Y[0], BGA_Y[1])),
]


def yield_marks(m, root, mt, name="ym"):
    """A glowing strip over each of the ten parts' band on the cut face; one group each."""
    out = []
    for k, (_, (x0, x1, y0, y1)) in enumerate(YIELD_PARTS):
        g = empty(f"{name}{k}", root)
        bx(f"{name}{k}_b", (x0, y0 + 0.05, 0.25), (x1, y1 - 0.05, 0.4), mt, g)
        out.append(g)
    return out


def views():
    """Shared camera poses."""
    return {
        "whole": frame((0.0, 4.0, -30.0), 130.0, 0.30, 0.40),
        "face": frame((0.0, 4.0, -4.0), 120.0, 0.12, 0.14),
        "die_edge": frame((20.0, 11.0, 0.0), 34.0, 0.25, 0.18, min_d=40.0),
        "sub_face": frame((-26.0, 0.0, 0.0), 60.0, 0.15, 0.10),
        "c4": frame((-30.0, 6.0, 0.0), 30.0, 0.20, 0.12, min_d=40.0),
        "wafer": frame((0.0, 9.0, -140.0), 480.0, 0.15, 0.85, pad=1.0),
        "site": frame((0.0, 9.0, -30.0), 150.0, 0.25, 0.55),
        "top": frame((0.0, 8.0, -36.0), 150.0, 0.10, 1.0),
    }
