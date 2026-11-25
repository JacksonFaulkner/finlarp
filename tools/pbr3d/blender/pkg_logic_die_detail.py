"""Part kit for the PACKAGING tab's LOGIC DIE page (pkg_logic_die_*.py).

A CoWoS-style GPU package cut open along z = 0 (the camera sits on +z), so every layer shows on the
cut face. Heights are stretched (a 0.8 mm die would be a hairline), widths are true-ish mm.
Bottom to top:

  board       green PCB with copper planes
  bga         solder balls, about 1 mm pitch in life
  substrate   ABF build-up layers (copper lines in dielectric, microvias) over and under a glass-
              fibre core with plated through-holes
  c4          C4 solder bumps, substrate to interposer
  interposer  silicon with TSVs and a fine RDL on top; a silicon bridge (LSI) sits in it under the
              gap between the two dies
  ubumps      microbumps (copper pillar + solder cap) under the dies and the HBM
  dies        two logic dies, FLIP-CHIP: the BEOL metal stack faces down onto the bumps, the
              transistor layer sits above it, bulk silicon on top against the TIM
  hbm         HBM stacks along the dies' long edges (pkg_kit.hbm_stack)
  underfill   black epoxy round the bumps
  tim + lid   thermal interface and a nickel-plated copper lid

Close-ups built elsewhere in space:
  die_block   one die's cross-section ~40x life: bulk, fins + gates, M1..M12 getting thicker
              upward toward the bumps (drawn flipped, as mounted), vias, pads, microbumps
  wafer       a 300 mm wafer printed field by field (26 x 33 mm reticle fields)
  bridge_block the die-to-die bridge cut open: fine wires under two rows of fine-pitch bumps

Helpers frame/camera_path/run/rise/present/blink/bx/empty come from power_vrm_detail.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, tube, disc, show, key, mat  # noqa: E402
from power_vrm_detail import (  # noqa: E402,F401
    bx, empty, join, frame, camera_path, run, rise, present, blink, bead, polyline,
)
import pkg_kit as K  # noqa: E402

# ---- levels (y, stretched) --------------------------------------------------------------------
BOARD = (-12.0, -7.0)
BGA_Y = -6.2
SUB = (-5.4, 0.0)
SUB_CORE = (-4.0, -1.4)
C4_Y = 0.6
IP = (1.2, 3.0)
IP_SI = (1.2, 2.4)
UB = (3.0, 3.6)
DIE = (3.6, 8.0)
BEOL = (3.6, 4.9)
DEV = (4.9, 5.2)
HBM_Y = (3.6, 8.0)
TIM = (8.0, 8.5)
LID = (8.5, 10.3)

# ---- plan (x across, z toward camera; everything lives at z <= 0) ----------------------------
DIES = ((-26.0, -1.2), (1.2, 26.0))
DIE_Z = -32.0
HBM_X = ((-37.0, -28.0), (28.0, 37.0))
HBM_ZS = ((-10.0, 0.0), (-22.0, -12.0))
IP_HALF = 42.0
SUB_HALF = 56.0
BOARD_HALF = 80.0
BRIDGE = (-5.0, 5.0)
BACK = -36.0  # interposer back z
SUB_BACK = -48.0

WAFER_C = (0.0, 200.0, -420.0)  # wafer scenes, far from the package
BLOCK_O = (0.0, 120.0, 0.0)  # die_block origin (cut face at z = 0)


def materials():
    m = K.materials()
    m.update({
        "mask": mat("ld_mask", (0.07, 0.30, 0.16), rough=0.55),
        "fr4": mat("ld_fr4", (0.55, 0.47, 0.30), rough=0.8),
        "core": mat("ld_core", (0.62, 0.58, 0.42), rough=0.8),
        "abf": mat("ld_abf", (0.36, 0.42, 0.22), rough=0.7),
        "cu": mat("ld_cu", (0.85, 0.50, 0.28), metal=0.9, rough=0.3),
        "solder": mat("ld_solder", (0.78, 0.80, 0.82), metal=0.9, rough=0.25),
        "si": mat("ld_si", (0.34, 0.38, 0.46), metal=0.5, rough=0.35),
        "bulk": mat("ld_bulk", (0.42, 0.32, 0.70), metal=0.25, rough=0.35),
        "device": mat("ld_device", (0.18, 0.70, 0.66), metal=0.2, rough=0.4),
        "gate": mat("ld_gate", (0.95, 0.80, 0.35), metal=0.7, rough=0.3),
        "fin": mat("ld_fin", (0.55, 0.58, 0.70), metal=0.4, rough=0.35),
        "lowk": mat("ld_lowk", (0.70, 0.78, 0.86), rough=0.4, alpha=0.55),
        "oxide": mat("ld_oxide", (0.62, 0.70, 0.80), rough=0.4),
        "rdl": mat("ld_rdl", (0.92, 0.62, 0.32), metal=0.9, rough=0.25),
        "fill": mat("ld_fill", (0.08, 0.07, 0.07), rough=0.9),
        "tim": mat("ld_tim", (0.80, 0.82, 0.84), metal=0.7, rough=0.5),
        "lid": mat("ld_lid", (0.72, 0.74, 0.78), metal=0.8, rough=0.3),
        "lid_see": mat("ld_lid_see", (0.75, 0.78, 0.82), metal=0.5, rough=0.25, alpha=0.35),
        "bridge": mat("ld_bridge", (0.25, 0.80, 0.82), metal=0.3, rough=0.4),
        "wafer": mat("ld_wafer", (0.30, 0.32, 0.42), metal=0.6, rough=0.5),
        "field": mat("ld_field", (0.48, 0.36, 0.78), metal=0.3, rough=0.35),
        "field_good": mat("ld_good", (0.25, 0.75, 0.45), emit=(0.2, 0.8, 0.4), strength=1.2),
        "field_bad": mat("ld_bad", (0.85, 0.15, 0.12), emit=(1.0, 0.12, 0.08), strength=1.3),
        "sm": mat("ld_sm", (0.62, 0.48, 0.88), metal=0.3, rough=0.3),
        "gpc": mat("ld_gpc", (0.30, 0.20, 0.50), metal=0.2, rough=0.5),
        "l2": mat("ld_l2", (0.30, 0.45, 0.85), metal=0.4, rough=0.3),
        "phy": mat("ld_phy", (0.95, 0.75, 0.30), metal=0.8, rough=0.3),
        # glows
        "data": mat("ld_data", (0.30, 0.90, 1.0), emit=(0.20, 0.90, 1.0), strength=6.0),
        "d2d": mat("ld_d2d", (0.70, 1.0, 0.85), emit=(0.55, 1.0, 0.75), strength=6.0),
        "power": mat("ld_power", (1.0, 0.85, 0.20), emit=(1.0, 0.80, 0.20), strength=6.0),
        "heat": mat("ld_heat", (1.0, 0.50, 0.20), emit=(1.0, 0.45, 0.15), strength=4.0),
        "hot": mat("ld_hot", (0.90, 0.35, 0.15), emit=(1.0, 0.38, 0.10), strength=1.6),
        "reticle": mat("ld_reticle", (1.0, 0.40, 0.70), emit=(1.0, 0.35, 0.65), strength=3.0),
        "slit": mat("ld_slit", (0.75, 0.55, 1.0), emit=(0.7, 0.5, 1.0), strength=2.0, alpha=0.6),
        "defect": mat("ld_defect", (1.0, 0.10, 0.10), emit=(1.0, 0.05, 0.05), strength=4.0),
        "test": mat("ld_test", (0.36, 0.26, 0.78), emit=(0.55, 0.40, 1.0), strength=1.4),
    })
    return m


# ---- package ------------------------------------------------------------------------------------


def _row_x(x0, x1, pitch):
    n = max(1, int((x1 - x0) // pitch))
    off = (x1 - x0 - (n - 1) * pitch) / 2
    return [x0 + off + pitch * i for i in range(n)]


def balls(m, parent, name, xs, y, r, zs, mt="solder"):
    parts = []
    g = empty(name, parent)
    for z in zs:
        for i, x in enumerate(xs):
            parts.append(ball(f"{name}_{z}_{i}", (x, y, z), r, m[mt], g, 10))
    join(parts, f"{name}_mesh")
    return g


def board(m, parent):
    g = empty("board", parent)
    h = BOARD_HALF
    bx("board_fr4", (-h, BOARD[0], -h), (h, BOARD[1] - 0.4, 0.0), m["fr4"], g)
    for k, y in enumerate((-11.0, -9.8, -8.6)):
        bx(f"board_plane{k}", (-h, y, -h), (h, y + 0.35, 0.0), m["cu"], g)
    bx("board_mask", (-h, BOARD[1] - 0.4, -h), (h, BOARD[1], 0.0), m["mask"], g)
    return g


def bga(m, parent):
    return balls(m, parent, "bga", _row_x(-SUB_HALF + 3, SUB_HALF - 3, 3.0), BGA_Y, 0.85, (-0.9, -4.0, -8.0, -14.0, -22.0, -32.0, -44.0))


def substrate(m, parent):
    """Build-up / core / build-up, each build-up layer an ABF slab carrying copper lines."""
    g = empty("substrate", parent)
    h, zb = SUB_HALF, SUB_BACK
    bx("core", (-h, SUB_CORE[0], zb), (h, SUB_CORE[1], 0.0), m["core"], g)
    for i, x in enumerate(_row_x(-h + 4, h - 4, 6.0)):
        tube(f"pth_{i}", (x, SUB_CORE[0], -1.0), (x, SUB_CORE[1], -1.0), 0.55, m["cu"], g, 10)
    lines = []
    for side, (y0, y1) in (("bot", (SUB[0], SUB_CORE[0])), ("top", (SUB_CORE[1], SUB[1]))):
        n = 4
        t = (y1 - y0) / n
        for k in range(n):
            ya = y0 + k * t
            bx(f"abf_{side}{k}", (-h, ya, zb), (h, ya + t, 0.0), m["abf"], g)
            pitch = 2.0 if (side == "top" and k >= 2) else 3.2
            for i, x in enumerate(_row_x(-h + 2, h - 2, pitch)):
                lines.append(bx(f"ln_{side}{k}_{i}", (x - 0.45, ya + t * 0.55, zb), (x + 0.45, ya + t * 0.95, 0.02), m["cu"], g))
                if i % 3 == k % 3:
                    lines.append(tube(f"mv_{side}{k}_{i}", (x, ya, -0.6), (x, ya + t * 0.6, -0.6), 0.22, m["cu"], g, 6))
    join(lines, "sub_cu")
    return g


def c4(m, parent):
    return balls(m, parent, "c4", _row_x(-IP_HALF + 2, IP_HALF - 2, 2.2), C4_Y, 0.55, (-0.7, -3.0, -6.0, -10.0, -16.0, -24.0, -32.0))


def interposer(m, parent, bridge=True):
    g = empty("interposer", parent)
    h = IP_HALF
    bx("ip_si", (-h, IP_SI[0], BACK), (h, IP_SI[1], 0.0), m["si"], g)
    tsv = [tube(f"tsv_{i}", (x, IP_SI[0], -0.5), (x, IP_SI[1], -0.5), 0.22, m["cu"], g, 8)
           for i, x in enumerate(_row_x(-h + 2, h - 2, 2.2))]
    join(tsv, "tsvs")
    rd = []
    t = (IP[1] - IP_SI[1]) / 4
    for k in range(4):
        ya = IP_SI[1] + k * t
        bx(f"rdl_ox{k}", (-h, ya, BACK), (h, ya + t, 0.0), m["oxide"], g)
        for i, x in enumerate(_row_x(-h + 1, h - 1, 0.9 if k < 3 else 1.6)):
            rd.append(bx(f"rdl_{k}_{i}", (x - 0.18, ya + t * 0.3, BACK), (x + 0.18, ya + t * 0.8, 0.02), m["rdl"], g))
    # the HBM links: long horizontal RDL traces from die edge to stack, shown at the cut face
    for side in (-1, 1):
        for j in range(3):
            y = IP_SI[1] + t * (0.4 + j * 1.1)
            x0, x1 = sorted((side * 22.0, side * 32.0))
            rd.append(bx(f"rdl_hbm{side}{j}", (x0, y, -1.2), (x1, y + 0.18, 0.02), m["rdl"], g))
    join(rd, "rdl_cu")
    out = {"group": g}
    if bridge:
        b = empty("bridge", g)
        bx("bridge_si", (BRIDGE[0], IP_SI[0] + 0.3, -26.0), (BRIDGE[1], IP_SI[1], 0.02), m["bridge"], b)
        wl = [bx(f"br_w{j}", (BRIDGE[0] + 0.4, IP_SI[1] - 0.25 - 0.2 * j, -26.0), (BRIDGE[1] - 0.4, IP_SI[1] - 0.15 - 0.2 * j, 0.04), m["rdl"], b)
              for j in range(4)]
        join(wl, "br_wires")
        out["bridge"] = b
    return out


def ubumps(m, parent):
    g = empty("ubumps", parent)
    parts = []
    xs = []
    for x0, x1 in DIES:
        xs += _row_x(x0 + 0.5, x1 - 0.5, 0.9)
    for x0, x1 in HBM_X:
        xs += _row_x(x0 + 0.5, x1 - 0.5, 0.9)
    for z in (-0.4, -2.0, -5.0, -9.0, -15.0, -22.0, -30.0):
        for i, x in enumerate(xs):
            parts.append(tube(f"ubp_{z}_{i}", (x, UB[0], z), (x, UB[0] + 0.38, z), 0.22, m["cu"], g, 6))
            parts.append(ball(f"ubs_{z}_{i}", (x, UB[0] + 0.45, z), 0.2, m["solder"], g, 6))
    join(parts, "ubump_mesh")
    return g


def underfill(m, parent):
    g = empty("underfill", parent)
    for x0, x1 in DIES:
        bx(f"uf_{x0}", (x0 - 0.8, UB[0], DIE_Z - 0.8), (x1 + 0.8, UB[1], -2.5), m["fill"], g)
    for x0, x1 in HBM_X:
        for z0, z1 in HBM_ZS:
            bx(f"uf_h{x0}{z0}", (x0 - 0.5, UB[0], z0 - 0.5), (x1 + 0.5, UB[1], z1 - 2.5), m["fill"], g)
    return g


def die(m, parent, name, x0, x1, floorplan=False):
    """One flip-chip die, cut at z = 0: metal stack at the bottom (on the bumps), transistor
    layer, bulk silicon on top."""
    g = empty(name, parent)
    z0 = DIE_Z
    bx(f"{name}_bulk", (x0, DEV[1], z0), (x1, DIE[1], 0.0), m["bulk"], g)
    bx(f"{name}_dev", (x0, DEV[0], z0), (x1, DEV[1], 0.0), m["device"], g)
    n = 6
    t = (BEOL[1] - BEOL[0]) / n
    cu = []
    for k in range(n):
        ya = BEOL[0] + k * t
        bx(f"{name}_ild{k}", (x0, ya, z0), (x1, ya + t, 0.0), m["lowk"], g)
        pitch = (1.2, 0.9, 0.6, 0.45, 0.35, 0.3)[k]  # thick on the bump side, fine near the transistors
        w = pitch * 0.45
        for i, x in enumerate(_row_x(x0 + 0.3, x1 - 0.3, pitch)):
            cu.append(bx(f"{name}_m{k}_{i}", (x - w / 2, ya + t * 0.25, z0), (x + w / 2, ya + t * 0.85, 0.02), m["cu"], g))
    join(cu, f"{name}_metal")
    if floorplan:
        top = DIE[1]
        fp = []
        fp.append(bx(f"{name}_phy", (x0 if x0 < 0 else x1 - 1.0, top, z0 + 1), (x0 + 1.0 if x0 < 0 else x1, top + 0.08, -1), m["phy"], g))
        w = (x1 - x0 - 2.5)
        for c in range(6):
            for r in range(9):
                xa = x0 + 1.6 + c * w / 6
                za = z0 + 1.2 + r * 3.3
                if 14.0 < za - z0 < 17.0:
                    continue
                fp.append(bx(f"{name}_sm{c}_{r}", (xa, top, za), (xa + w / 6 - 0.4, top + 0.06, za + 2.8), m["sm"], g))
        fp.append(bx(f"{name}_l2", (x0 + 1.6, top, z0 + 14.2), (x1 - 0.9, top + 0.06, z0 + 16.8), m["l2"], g))
        join(fp, f"{name}_fp")
    return g


def hbm(m, parent):
    g = empty("hbm", parent)
    hm = K.hbm_materials()
    for side, (x0, x1) in zip((-1, 1), HBM_X):
        for z0, z1 in HBM_ZS:
            K.hbm_stack(f"hbm_{side}_{z0}", (x0, HBM_Y[0], z0), (x1, HBM_Y[1], z1), hm, g)
    return g


def lid(m, parent, see=False):
    g = empty("lid", parent)
    for x0, x1 in DIES:
        bx(f"tim_{x0}", (x0, TIM[0], DIE_Z), (x1, TIM[1], 0.0), m["tim"], g)
    mt = m["lid_see" if see else "lid"]
    h = SUB_HALF - 3
    bx("lid_top", (-h, LID[0], SUB_BACK + 3), (h, LID[1], 0.0), mt, g)
    for s in (-1, 1):
        bx(f"lid_foot{s}", (s * h, SUB[1], SUB_BACK + 3), (s * (h - 3), LID[0], 0.0), mt, g)
    return g


def package(m, root, lid_on=True, floorplan=False, see=True):
    s = {}
    s["board"] = board(m, root)
    s["bga"] = bga(m, root)
    s["sub"] = substrate(m, root)
    s["c4"] = c4(m, root)
    ip = interposer(m, root)
    s["ip"], s["bridge"] = ip["group"], ip["bridge"]
    s["ub"] = ubumps(m, root)
    s["uf"] = underfill(m, root)
    s["dies"] = [die(m, root, f"die{i}", x0, x1, floorplan) for i, (x0, x1) in enumerate(DIES)]
    s["hbm"] = hbm(m, root)
    if lid_on:
        s["lid"] = lid(m, root, see)
    # glows over each die, switched with show()
    s["hot"] = []
    for i, (x0, x1) in enumerate(DIES):
        g = empty(f"hot{i}", root)
        bx(f"hot{i}_b", (x0 - 0.02, DEV[0], DIE_Z - 0.02), (x1 + 0.02, TIM[1] + 0.03, 0.04), m["hot"], g)
        show(g, [])
        s["hot"].append(g)
    return s


# ---- bead paths (package) ------------------------------------------------------------------------

def power_path(x):
    """Board plane up through a BGA ball, a core PTH, C4, a TSV, the RDL, a microbump, into the die."""
    return [(x, -9.6, 0.4), (x, BGA_Y, 0.4), (x, SUB_CORE[0], 0.4), (x, SUB[1], 0.4), (x, IP_SI[0], 0.4),
            (x, IP[1], 0.4), (x, UB[1], 0.4), (x, DEV[1], 0.4)]


def data_path(side):
    """Die edge PHY down a microbump, out along the RDL, up into an HBM base die."""
    a, b = side * 24.5, side * 31.0
    return [(a, DEV[0], 0.5), (a, UB[0], 0.5), (a, IP[1] - 0.3, 0.5), (b, IP[1] - 0.3, 0.5), (b, UB[1], 0.5), (b, HBM_Y[0] + 0.6, 0.5)]


def d2d_path(sign=1):
    a, b = -3.5 * sign, 3.5 * sign
    return [(a, DEV[0], 0.6), (a, UB[0], 0.6), (a, IP[1] - 0.5, 0.6), (b, IP[1] - 0.5, 0.6), (b, UB[1], 0.6), (b, DEV[0], 0.6)]


def heat_base(i):
    x0, x1 = DIES[i]
    return ((x0 + x1) / 2, LID[1], -8.0)


# ---- die cross-section close-up -------------------------------------------------------------------

def die_block(m, parent, o=BLOCK_O, w=70.0, flip=True):
    """One die's cross-section, cut at z = 0, ~40x stretched. flip=True draws it as mounted: pads
    and microbumps at the bottom, then M12 (thick) down to M1 (fine), the transistor layer, and bulk
    silicon on top. Returns key points for tags and beads."""
    ox, oy, oz = o
    g = empty("block", parent)
    D = 14.0  # depth back from the cut face
    x0, x1 = ox - w / 2, ox + w / 2
    y = oy
    pts = {}
    # microbumps + pads
    bumps = []
    for i, x in enumerate(_row_x(x0 + 3, x1 - 3, 9.0)):
        bumps.append(tube(f"blk_pil{i}", (x, y, -2.0), (x, y + 3.0, -2.0), 1.6, m["cu"], g, 14))
        bumps.append(ball(f"blk_cap{i}", (x, y - 0.2, -2.0), 1.7, m["solder"], g, 12))
    join(bumps, "blk_bumps")
    pts["bump"] = (x0 + 7.5, y, -0.5)
    y += 3.0
    bx("blk_pad", (x0, y, -D), (x1, y + 1.0, 0.0), m["oxide"], g)
    pads = [bx(f"blk_padcu{i}", (x - 2.2, y, -D), (x + 2.2, y + 1.0, 0.04), m["rdl"], g) for i, x in enumerate(_row_x(x0 + 3, x1 - 3, 9.0))]
    join(pads, "blk_pads")
    pts["pad"] = (x1 - 3, y + 0.5, 0.0)
    y += 1.0
    # metal levels, thick (global) to fine (local) going up toward the transistors
    levels = [(3.0, 9.0), (2.6, 9.0), (2.0, 6.0), (1.6, 4.5), (1.3, 3.0), (1.1, 2.4), (0.9, 1.8), (0.8, 1.4), (0.7, 1.1), (0.6, 0.9)]
    lvl_y = []
    cu = []
    for k, (t, pitch) in enumerate(levels):
        bx(f"blk_ild{k}", (x0, y, -D), (x1, y + t, 0.0), m["lowk"], g)
        xs = _row_x(x0 + 0.5, x1 - 0.5, pitch)
        for i, x in enumerate(xs):
            cu.append(bx(f"blk_m{k}_{i}", (x - pitch * 0.25, y + t * 0.35, -D), (x + pitch * 0.25, y + t, 0.05), m["cu"], g))
            if i % 2 == k % 2:
                cu.append(bx(f"blk_v{k}_{i}", (x - pitch * 0.1, y, -1.4), (x + pitch * 0.1, y + t * 0.35, -0.6), m["cu"], g))
        lvl_y.append(y + t / 2)
        y += t
    join(cu, "blk_metal")
    pts["global"] = (x1, lvl_y[0], 0.0)
    pts["local"] = (x1, lvl_y[-1], 0.0)
    pts["levels"] = lvl_y
    # transistors: fins along z under gate lines along x (as mounted the gates point down)
    bx("blk_dev", (x0, y, -D), (x1, y + 2.4, 0.0), m["oxide"], g)
    tr = []
    for i, x in enumerate(_row_x(x0 + 0.8, x1 - 0.8, 1.6)):
        tr.append(bx(f"blk_fin{i}", (x - 0.25, y + 1.1, -D), (x + 0.25, y + 2.4, 0.06), m["fin"], g))
    for j, z in enumerate((-1.0, -3.4, -5.8, -8.2, -10.6, -13.0)):
        tr.append(bx(f"blk_gate{j}", (x0, y + 0.2, z - 0.5), (x1, y + 1.6, z + 0.5), m["gate"], g))
    join(tr, "blk_transistors")
    pts["dev"] = (x0, y + 1.2, 0.0)
    pts["dev_y"] = y + 1.2
    y += 2.4
    bx("blk_bulk", (x0, y, -D), (x1, y + 14.0, 0.0), m["bulk"], g)
    pts["bulk"] = (x0 + 6, y + 7.0, 0.0)
    pts["top"] = (ox, y + 14.0, -D / 2)
    pts["y0"], pts["y1"] = oy, y + 14.0
    pts["x"] = (x0, x1)
    return g, pts


def block_signal(pts, x):
    """A signal from a microbump up through the stack to a transistor (absolute points)."""
    ys = [pts["y0"], pts["levels"][0], pts["levels"][3], pts["levels"][6], pts["levels"][-1], pts["dev_y"]]
    return [(x + 0.3 * (k % 2), yy, 0.6) for k, yy in enumerate(ys)]


# ---- wafer --------------------------------------------------------------------------------------

FIELD = (26.0, 33.0)


def wafer(m, parent, c=WAFER_C, r=150.0, cells=1, name="wafer"):
    """A 300 mm wafer with the reticle fields that fit, each cut into cells x cells dies. Returns
    the group and a list of (x, z, w, d) die rects (absolute)."""
    g = empty(name, parent)
    cx, cy, cz = c
    disc(f"{name}_disc", (cx, cy - 0.6, cz), r, 1.2, m["wafer"], g)
    fw, fd = FIELD
    rects = []
    parts = []
    nx, nz = int(r // fw) + 1, int(r // fd) + 1
    for i in range(-nx, nx):
        for j in range(-nz, nz):
            fx, fz = cx + i * fw, cz + j * fd
            corners = [(fx, fz), (fx + fw, fz), (fx, fz + fd), (fx + fw, fz + fd)]
            if any(math.hypot(a - cx, b - cz) > r - 2 for a, b in corners):
                continue
            dw, dd = fw / cells, fd / cells
            for a in range(cells):
                for b in range(cells):
                    x0, z0 = fx + a * dw + 0.5, fz + b * dd + 0.5
                    parts.append(bx(f"{name}_d{i}_{j}_{a}{b}", (x0, cy, z0), (x0 + dw - 1.0, cy + 0.5, z0 + dd - 1.0), m["field"], g))
                    rects.append((x0, z0, dw - 1.0, dd - 1.0))
    join(parts, f"{name}_dies")
    return g, rects


def marks(m, parent, name, rects, mt, y, pick):
    """Overlay boxes on the die rects whose index is in `pick` (one joined mesh, in a group)."""
    g = empty(name, parent)
    parts = [bx(f"{name}_{i}", (x, y, z), (x + w, y + 0.25, z + d), m[mt], g) for i, (x, z, w, d) in enumerate(rects) if i in pick]
    if parts:
        join(parts, f"{name}_mesh")
    return g


def defects(m, parent, name, c=WAFER_C, r=150.0, n=26, seed=3, size=2.2):
    """`n` pseudo-random defect points on the wafer; returns group and their (x, z)."""
    g = empty(name, parent)
    pts = []
    rng = random.Random(seed)
    for k in range(n):
        a = rng.uniform(0.0, 2 * math.pi)
        rr = r * 0.9 * math.sqrt(rng.random())
        x, z = c[0] + rr * math.cos(a), c[2] + rr * math.sin(a)
        pts.append((x, z))
        ball(f"{name}_{k}", (x, c[1] + 0.8, z), size, m["defect"], g, 10)
    return g, pts


def hit(rects, pts):
    out = set()
    for i, (x, z, w, d) in enumerate(rects):
        for px, pz in pts:
            if x - 1 <= px <= x + w + 1 and z - 1 <= pz <= z + d + 1:
                out.add(i)
    return out


# ---- die-to-die bridge close-up -------------------------------------------------------------------

BRIDGE_O = (0.0, 120.0, -80.0)


def bridge_block(m, parent, o=BRIDGE_O):
    """The two dies' facing edges over a silicon bridge sunk in the interposer, cut at the block's
    front (z = o.z): fine-pitch bumps in two rows, wires across the bridge."""
    ox, oy, oz = o
    g = empty("bblk", parent)
    D = 16.0
    # interposer (mould / silicon) with the bridge inset
    bx("bblk_ip", (ox - 40, oy, oz - D), (ox + 40, oy + 8, oz), m["si"], g)
    bx("bblk_br", (ox - 18, oy + 2, oz - D), (ox + 18, oy + 8, oz + 0.05), m["bridge"], g)
    wires = []
    for j in range(5):
        yy = oy + 7.4 - j * 0.9
        wires.append(bx(f"bblk_w{j}", (ox - 15 + j, yy, oz - D), (ox + 15 - j, yy + 0.4, oz + 0.1), m["rdl"], g))
        for s in (-1, 1):
            xv = ox + s * (15 - j)
            wires.append(bx(f"bblk_v{j}{s}", (xv - 0.2, yy, oz - 1.0), (xv + 0.2, oy + 8, oz - 0.3), m["rdl"], g))
    join(wires, "bblk_wires")
    bumps = []
    bump_x = [ox + s * (6 + 1.8 * i) for s in (-1, 1) for i in range(5)] + [ox + s * (22 + 4.0 * i) for s in (-1, 1) for i in range(4)]
    for i, x in enumerate(bump_x):
        fine = abs(x - ox) < 16
        r = 0.6 if fine else 1.3
        bumps.append(tube(f"bblk_p{i}", (x, oy + 8, oz - 1.6), (x, oy + 10.2, oz - 1.6), r, m["cu"], g, 10))
    join(bumps, "bblk_bumps")
    for s in (-1, 1):
        a, b = sorted((ox + s * 3, ox + s * 40))
        bx(f"bblk_die{s}", (a, oy + 10.2, oz - D), (b, oy + 22, oz), m["bulk"], g)
        bx(f"bblk_beol{s}", (a, oy + 10.2, oz - D), (b, oy + 13, oz + 0.02), m["lowk"], g)
    return g, {"bridge": (ox, oy + 5, oz), "fine": (ox - 7.8, oy + 9, oz), "coarse": (ox + 26, oy + 9, oz),
               "dieL": (ox - 22, oy + 18, oz), "dieR": (ox + 22, oy + 18, oz), "y": oy}


def bridge_path(o=BRIDGE_O, j=0, sign=1):
    ox, oy, oz = o
    yy = oy + 7.6 - j * 0.9
    a, b = ox - sign * (15 - j), ox + sign * (15 - j)
    return [(a, oy + 12, oz + 0.6), (a, yy, oz + 0.6), (b, yy, oz + 0.6), (b, oy + 12, oz + 0.6)]
