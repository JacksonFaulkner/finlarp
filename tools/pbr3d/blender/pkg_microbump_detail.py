"""Part kit for the PACKAGING tab's MICROBUMP page (pkg_microbump_*.py).

A 2.5D package drawn far larger than life and cut away along z = 0 (the camera sits on +z), so the
cut face shows every joint level in section. Y up, x across, z toward the camera. Stylised, but the
pitch ratios hold: BGA 5.0, C4 3.0, microbump 0.8 (real ~1,000 / 150 / 40 um), hybrid pads 0.2.

  stack     board (FR4, copper planes, mask) / BGA balls / substrate (bottom ABF build-up, glass-
            weave core with plated through-holes, top ABF build-up with stacked microvias) / C4
            bumps on pads / silicon interposer with lined TSVs / RDL (three copper levels in
            oxide) / microbump field / logic die (BEOL + silicon) and an HBM stack (base die + 8
            DRAM dies on their own microbumps and TSVs).
  joint     one microbump in section at any scale: interposer pad, IMC, solder, IMC, nickel
            barrier, copper pillar, UBM seed, aluminium pad in polyimide passivation.
  ladder    a C4 ball, a microbump and a hybrid-bond pad pair side by side at one scale.
  hybrid    two bonding surfaces in section: copper pads set in oxide, dished, then bonded.
  bridges   a row of solder bumps at shrinking pitch; at the tightest the solder bridges.

Uses the shapes, beads and camera of power_vrm_detail.py (imported, not edited).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, cut, disc, empty, key, show, mat  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, join, present  # noqa: E402

# ---- materials ------------------------------------------------------------------------------


def materials():
    m = D.materials()
    m.update({
        "abf": mat("ub_abf", (0.30, 0.42, 0.30), rough=0.7),
        "core": mat("ub_core", (0.62, 0.55, 0.36), rough=0.8),
        "si": mat("ub_si", (0.40, 0.43, 0.50), metal=0.5, rough=0.35),
        "oxide": mat("ub_oxide", (0.58, 0.66, 0.74), rough=0.35),
        "beol": mat("ub_beol", (0.24, 0.26, 0.34), rough=0.5),
        "pi": mat("ub_polyimide", (0.78, 0.48, 0.14), rough=0.5),
        "al": mat("ub_al", (0.78, 0.80, 0.84), metal=0.85, rough=0.3),
        "ni": mat("ub_ni", (0.55, 0.57, 0.60), metal=0.9, rough=0.35),
        "imc": mat("ub_imc", (0.52, 0.42, 0.30), metal=0.6, rough=0.5),
        "snag": mat("ub_snag", (0.80, 0.81, 0.84), metal=0.85, rough=0.25),
        "liner": mat("ub_liner", (0.70, 0.75, 0.85), rough=0.4),
        "uf": mat("ub_underfill", (0.12, 0.11, 0.10), rough=0.85),
        "uf_flow": mat("ub_uf_flow", (0.30, 0.20, 0.10), rough=0.6),
        "dram": mat("ub_dram", (0.24, 0.36, 0.62), metal=0.4, rough=0.35),
        "base": mat("ub_base", (0.30, 0.28, 0.50), metal=0.4, rough=0.35),
        "void": mat("ub_void", (0.02, 0.02, 0.03), rough=0.9),
        "flat": mat("ub_flat", (0.45, 0.85, 0.55), emit=(0.40, 0.85, 0.50), strength=2.0),
        "sig": mat("ub_sig", (0.30, 0.90, 1.0), emit=(0.20, 0.88, 1.0), strength=6.0),
        "pwr": mat("ub_pwr", (1.0, 0.70, 0.20), emit=(1.0, 0.62, 0.12), strength=6.0),
        "gnd_bead": mat("ub_gnd_bead", (0.55, 0.55, 1.0), emit=(0.45, 0.45, 1.0), strength=5.0),
        "stress": mat("ub_stress", (1.0, 0.15, 0.10), emit=(1.0, 0.12, 0.08), strength=1.8),
        "melt": mat("ub_melt", (0.95, 0.55, 0.25), emit=(1.0, 0.50, 0.20), strength=0.6),
    })
    return m


def cyl(name, x, y0, y1, z, r, m, parent, verts=20, front=False, cz=0.0):
    """An upright cylinder from y0 to y1 at (x, z); cut open at z = cz when `front` (an inner
    part nested in another is cut a hair further forward so the two faces don't fight)."""
    o = disc(name, (x, (y0 + y1) / 2, z), r, abs(y1 - y0), m, parent, verts)
    if front:
        cut(o, cz)
    return o


def grid(lo, hi, pitch):
    n = int(round((hi - lo) / pitch))
    return [lo + pitch * i for i in range(n + 1)]


# ---- layout (y bands) ------------------------------------------------------------------------

BOARD = (-16.0, -10.0)
BGA_Y, BGA_R = -8.4, 1.6
SUB_BOT, CORE_BOT, CORE_TOP, SUB_TOP = -6.8, -4.2, -1.0, 1.6
C4_Y, C4_R = 2.8, 1.2
IP_BOT, IP_TOP = 4.0, 7.0
RDL_TOP = 8.0
DIE_BOT = 9.2  # microbump slot 8.0..9.2
DIE_BEOL = 10.0
DIE_TOP = 12.2
LOGIC_X = (-26.0, 4.0)
HBM_X = (7.0, 21.0)
DEPTH = -26.0
UB_PITCH, C4_PITCH, BGA_PITCH = 0.8, 3.0, 5.0
UB_XS = grid(LOGIC_X[0] + 0.4, LOGIC_X[1] - 0.4, UB_PITCH)
HB_XS = grid(HBM_X[0] + 0.4, HBM_X[1] - 0.4, UB_PITCH)
C4_XS = grid(-30.0, 30.0, C4_PITCH)
BGA_XS = grid(-45.0, 45.0, BGA_PITCH)
UB_ZS = [-UB_PITCH * k for k in range(7)]
HBM_DIE_T, HBM_GAP = 0.5, 0.35
POWER_X = -21.0  # a power column: BGA / PTH / C4 / TSV under the logic die
SIGNAL = (3.6, 7.4)  # logic die edge bump > HBM base bump, through the RDL


# ---- one microbump ----------------------------------------------------------------------------


def joint(parts, x, y0, z, s, g, m, front, state="joint", pad=True, die_side=True):
    """One copper-pillar microbump standing on the interposer pad top at y0, scale s (s = 1 at the
    0.8 pitch). state: 'joint' (reflowed, IMC both ends), 'cap' (solder dome on the pillar tip,
    before reflow; drawn from the pillar down as if y0 were the pad), 'pillar' (no solder yet)."""
    def c(name, a, b, r, mm, v=20):
        parts.append(cyl(name, x, y0 + a * s, y0 + b * s, z, r * s, mm, g, v, front))

    n = f"j{x:.2f}_{z:.2f}_{s:.1f}".replace("-", "m").replace(".", "p")
    if pad:
        c(n + "pad", -0.06, 0.0, 0.27, m["copper"])
    if state == "joint":
        c(n + "imc0", 0.0, 0.03, 0.235, m["imc"])
        c(n + "sol", 0.03, 0.39, 0.215, m["snag"])
        o = ball(n + "bul", (x, y0 + 0.21 * s, z), 0.24 * s, m["snag"], g, 20)
        o.scale = (1.0, 1.0, 0.75)
        if front:
            cut(o)
        parts.append(o)
        c(n + "imc1", 0.39, 0.42, 0.215, m["imc"])
    elif state == "cap":
        o = ball(n + "cap", (x, y0 + 0.30 * s, z), 0.215 * s, m["snag"], g, 20)
        o.scale = (1.0, 1.0, 0.8)
        if front:
            cut(o)
        parts.append(o)
        c(n + "capb", 0.30, 0.42, 0.205, m["snag"])
    c(n + "ni", 0.42, 0.50, 0.205, m["ni"])
    c(n + "cu", 0.50, 1.10, 0.20, m["copper"])
    if die_side:
        c(n + "ubm", 1.10, 1.14, 0.22, m["al"])
        c(n + "alp", 1.14, 1.20, 0.26, m["al"])


# ---- the stack -----------------------------------------------------------------------------


def board(m, root):
    g = empty("board_grp", root)
    p = [bx("brd_fr4", (-60.0, BOARD[0], -60.0), (60.0, BOARD[1] - 0.4, 0.0), m["fr4"], g)]
    for k, y in enumerate((-11.8, -13.6)):
        p.append(bx(f"brd_cu{k}", (-60.0, y, -60.0), (60.0, y + 0.35, 0.0), m["plane12"] if k else m["gnd"], g))
    p.append(bx("brd_mask", (-60.0, BOARD[1] - 0.4, -60.0), (60.0, BOARD[1], 0.0), m["mask"], g))
    join(p, "board_mesh")
    bp = []
    for x in BGA_XS:
        bp.append(cyl(f"brd_pad{x}", x, BOARD[1] - 0.1, BOARD[1] + 0.05, 0.0, 1.1, m["copper"], g, 16, True))
    join(bp, "board_pads")
    return g


def bga(m, root):
    g = empty("bga_grp", root)
    p = []
    for k, z in enumerate((0.0, -5.0, -10.0, -15.0, -20.0)):
        for x in BGA_XS:
            o = ball(f"bga{x}_{k}", (x, BGA_Y, z), BGA_R, m["solder"], g, 16)
            o.scale = (1.0, 1.0, 0.85)
            if k == 0:
                cut(o)
            p.append(o)
    join(p, "bga_mesh")
    return g


def substrate(m, root):
    g = empty("sub_grp", root)
    x0, x1 = -48.0, 48.0
    p = []
    # bottom build-up: 4 ABF films, each topped by a patterned copper layer
    ys = [SUB_BOT + 0.65 * k for k in range(5)]
    for k in range(4):
        p.append(bx(f"sb_abf{k}", (x0, ys[k], DEPTH * 2), (x1, ys[k + 1], 0.0), m["abf"], g))
        for j, xa in enumerate(grid(x0 + 1.0, x1 - 4.0, 4.0)):
            if (j + k) % 3:
                p.append(bx(f"sb_tr{k}_{j}", (xa, ys[k + 1] - 0.14, -6.0), (xa + 2.6, ys[k + 1], 0.02), m["copper"], g))
    p.append(bx("sb_core", (x0, CORE_BOT, DEPTH * 2), (x1, CORE_TOP, 0.0), m["core"], g))
    for k in range(5):  # glass weave in the core
        y = CORE_BOT + 0.5 + 0.55 * k
        p.append(bx(f"sb_glass{k}", (x0, y, -0.3), (x1, y + 0.18, 0.03), m["ink"], g))
    ys2 = [CORE_TOP + 0.65 * k for k in range(5)]
    for k in range(4):
        p.append(bx(f"st_abf{k}", (x0, ys2[k], DEPTH * 2), (x1, ys2[k + 1], 0.0), m["abf"], g))
        for j, xa in enumerate(grid(x0 + 2.0, x1 - 4.0, 3.0)):
            if (j + k) % 2:
                p.append(bx(f"st_tr{k}_{j}", (xa, ys2[k + 1] - 0.12, -5.0), (xa + 1.4, ys2[k + 1], 0.02), m["copper"], g))
    p.append(bx("sb_mask", (x0, SUB_TOP - 0.12, DEPTH * 2), (x1, SUB_TOP, 0.0), m["mask"], g))
    join(p, "sub_mesh")
    v = []
    for x in C4_XS:  # stacked microvias through the top build-up, a PTH through the core
        for k in range(4):
            v.append(cyl(f"st_v{x}_{k}", x, ys2[k], ys2[k + 1], 0.0, 0.32 - 0.04 * (k % 2), m["copper"], g, 16, True))
        v.append(cyl(f"pth{x}", x, CORE_BOT, CORE_TOP, 0.0, 0.62, m["copper"], g, 20, True))
        v.append(cyl(f"pthf{x}", x, CORE_BOT + 0.01, CORE_TOP - 0.01, 0.0, 0.40, m["dark"], g, 16, True, 0.01))
        v.append(cyl(f"c4pad{x}", x, SUB_TOP - 0.12, SUB_TOP + 0.05, 0.0, 0.85, m["copper"], g, 16, True))
    for x in BGA_XS:
        for k in range(4):
            v.append(cyl(f"sb_v{x}_{k}", x, ys[k], ys[k + 1], 0.0, 0.34, m["copper"], g, 16, True))
        v.append(cyl(f"bgapad{x}", x, SUB_BOT - 0.05, SUB_BOT + 0.12, 0.0, 1.2, m["copper"], g, 16, True))
    join(v, "sub_vias")
    return g


def c4(m, root):
    g = empty("c4_grp", root)
    p = []
    for k, z in enumerate((0.0, -3.0, -6.0, -9.0, -12.0)):
        for x in C4_XS:
            o = ball(f"c4_{x}_{k}", (x, C4_Y, z), C4_R, m["snag"], g, 16)
            o.scale = (1.0, 1.0, 0.95)
            if k == 0:
                cut(o)
            p.append(o)
    join(p, "c4_mesh")
    return g


def interposer(m, root):
    g = empty("ip_grp", root)
    p = [bx("ip_si", (-34.0, IP_BOT, DEPTH * 1.3), (34.0, IP_TOP, 0.0), m["si"], g)]
    for k in range(3):  # RDL: oxide with three copper levels
        y = IP_TOP + 0.33 * k
        p.append(bx(f"rdl_ox{k}", (-34.0, y, DEPTH * 1.3), (34.0, y + 0.33, 0.0), m["oxide"], g))
    join(p, "ip_mesh")
    w = []
    for k in range(3):
        y = IP_TOP + 0.33 * k + 0.12
        for j, xa in enumerate(grid(-33.0, 32.0, 1.6)):
            if (j * 7 + k * 3) % 4:
                w.append(bx(f"rdl_w{k}_{j}", (xa, y, -2.5), (xa + 1.1, y + 0.12, 0.02), m["copper"], g))
    # the signal route: one long RDL wire from the logic edge to the HBM base
    w.append(bx("rdl_sig", (SIGNAL[0] - 0.2, IP_TOP + 0.45, -0.3), (SIGNAL[1] + 0.2, IP_TOP + 0.6, 0.02), m["gold"], g))
    for x in C4_XS:  # TSVs: copper in an oxide liner, landing on C4 pads below
        w.append(cyl(f"tsv_l{x}", x, IP_BOT, IP_TOP, 0.0, 0.42, m["liner"], g, 20, True))
        w.append(cyl(f"tsv{x}", x, IP_BOT - 0.01, IP_TOP + 0.01, 0.0, 0.34, m["copper"], g, 20, True, 0.01))
        w.append(cyl(f"ipc4pad{x}", x, IP_BOT - 0.1, IP_BOT, 0.0, 0.8, m["al"], g, 16, True))
    join(w, "ip_wires")
    return g


def ub_field(m, parent, xs, y0, state, name, zs=UB_ZS, front_only=False):
    """A field of microbumps (pillars hang from the die; pads belong to whoever is below). The cut
    front row is drawn in full; rows behind are pillar + solder only, each row joined as it is
    built so Blender stays fast."""
    g = empty(name, parent)
    for k, z in enumerate(zs[:1] if front_only else zs):
        parts = []
        for x in xs:
            if k == 0:
                joint(parts, x, y0, z, 1.0, g, m, True, state, pad=False)
            else:
                parts.append(cyl(f"{name}s{x:.2f}_{k}", x, y0, y0 + 0.42, z, 0.23, m["snag"], g, 10))
                parts.append(cyl(f"{name}c{x:.2f}_{k}", x, y0 + 0.42, y0 + 1.2, z, 0.2, m["copper"], g, 10))
        join(parts, f"{name}_row{k}")
    return g


def pads(m, parent, xs, y0, name, zs=UB_ZS[:2]):
    g = empty(name, parent)
    p = [cyl(f"{name}{x}_{z}", x, y0 - 0.06, y0, z, 0.27, m["copper"], g, 12, z == 0.0) for z in zs for x in xs]
    join(p, name + "_mesh")
    return g


def logic(m, root, xs=LOGIC_X, top=DIE_TOP):
    g = empty("logic_grp", root)
    p = [bx("lg_beol", (xs[0], DIE_BOT, DEPTH), (xs[1], DIE_BEOL, 0.0), m["beol"], g),
         bx("lg_pi", (xs[0], DIE_BOT, DEPTH), (xs[1], DIE_BOT + 0.08, 0.0), m["pi"], g),
         bx("lg_si", (xs[0], DIE_BEOL, DEPTH), (xs[1], top, 0.0), m["die"], g)]
    for k in range(5):  # BEOL metal levels on the cut face
        y = DIE_BOT + 0.16 + 0.15 * k
        for j, xa in enumerate(grid(xs[0] + 0.3, xs[1] - 1.0, 0.9)):
            if (j + k) % 3:
                p.append(bx(f"lg_m{k}_{j}", (xa, y, -0.5), (xa + 0.55 - 0.06 * k, y + 0.06, 0.02), m["copper"], g))
    join(p, "logic_mesh")
    return g


def hbm(m, root):
    """HBM: a base die and 8 DRAM dies, each pair joined by a microbump row with TSVs through."""
    g = empty("hbm_grp", root)
    p = [bx("hb_base", (HBM_X[0], DIE_BOT, -12.0), (HBM_X[1], DIE_BOT + 0.8, 0.0), m["base"], g)]
    y = DIE_BOT + 0.8
    tops = []
    for k in range(8):
        y += HBM_GAP
        p.append(bx(f"hb_d{k}", (HBM_X[0], y, -12.0), (HBM_X[1], y + HBM_DIE_T, 0.0), m["dram"], g))
        tops.append(y)
        y += HBM_DIE_T
    p.append(bx("hb_mold", (HBM_X[0] - 0.4, DIE_BOT, -12.4), (HBM_X[0], y, 0.0), m["mold"], g))
    p.append(bx("hb_mold2", (HBM_X[1], DIE_BOT, -12.4), (HBM_X[1] + 0.4, y, 0.0), m["mold"], g))
    join(p, "hbm_mesh")
    b = []
    for x in grid(HBM_X[0] + 1.0, HBM_X[1] - 1.0, 1.0):
        b.append(cyl(f"hb_tsv{x}", x, DIE_BOT + 0.1, y - HBM_DIE_T * 0.5, 0.0, 0.07, m["copper"], g, 10, True))
        for t in tops:
            b.append(cyl(f"hb_ub{x}_{t:.2f}", x, t - HBM_GAP, t, 0.0, 0.14, m["snag"], g, 12, True))
    join(b, "hbm_bumps")
    return g, y


def underfill(m, parent, xs, y0, y1, name, depth=DEPTH, fillet=1.2):
    g = empty(name, parent)
    p = [bx(name + "_gap", (xs[0], y0, depth), (xs[1], y1, -0.03), m["uf"], g),
         bx(name + "_fl", (xs[0] - fillet, y0, depth - fillet), (xs[0], y0 + (y1 - y0) * 0.6, 0.0), m["uf"], g),
         bx(name + "_fr", (xs[1], y0, depth - fillet), (xs[1] + fillet, y0 + (y1 - y0) * 0.6, 0.0), m["uf"], g)]
    join(p, name + "_mesh")
    return g


def hybrid_layer(m, parent, xs, y0, name, pitch=0.2):
    """The die's face bonded straight to the interposer: oxide with copper pads, no gap."""
    g = empty(name, parent)
    p = [bx(name + "_ox", (xs[0], y0, DEPTH), (xs[1], y0 + 0.24, 0.0), m["oxide"], g)]
    for x in grid(xs[0] + 0.2, xs[1] - 0.2, pitch * 2):
        p.append(bx(f"{name}_cu{x:.2f}", (x - pitch * 0.4, y0, -0.6), (x + pitch * 0.4, y0 + 0.24, 0.02), m["copper"], g))
    join(p, name + "_mesh")
    return g


def stack(m, root, hybrid=False):
    """The whole package. Groups come back in a dict so scenes can move or swap them."""
    s = {"board": board(m, root), "bga": bga(m, root), "sub": substrate(m, root), "c4": c4(m, root),
         "ip": interposer(m, root)}
    s["ip_pads"] = pads(m, s["ip"], UB_XS + HB_XS, RDL_TOP, "ip_ubpads")
    die = empty("die_grp", root)
    s["die"] = die
    s["logic"] = logic(m, die)
    s["ub_joint"] = ub_field(m, die, UB_XS, RDL_TOP, "joint", "ub_logic")
    s["hbm_grp"] = empty("hbm_side", root)
    s["hbm"], s["hbm_top"] = hbm(m, s["hbm_grp"])
    s["ub_hbm"] = ub_field(m, s["hbm_grp"], HB_XS, RDL_TOP, "joint", "ub_hbm")
    s["uf_die"] = underfill(m, root, (LOGIC_X[0], HBM_X[1]), RDL_TOP, DIE_BOT, "uf_die")
    s["uf_c4"] = underfill(m, root, (-34.0, 34.0), SUB_TOP, IP_BOT, "uf_c4", DEPTH * 1.3, 1.6)
    if hybrid:
        s["hyb"] = hybrid_layer(m, root, LOGIC_X, RDL_TOP, "hyb_logic")
    # named points for tags and beads
    s["pts"] = {
        "bga": (BGA_XS[5], BGA_Y, 0.4), "sub": (36.0, -2.6, 0.2), "core": (-40.0, -2.6, 0.2),
        "abf": (40.0, 0.4, 0.2), "c4": (C4_XS[3], C4_Y, 0.4), "tsv": (C4_XS[4], 5.5, 0.2),
        "rdl": (-30.0, 7.5, 0.2), "ub": (UB_XS[6], 8.6, 0.3), "logic": (-11.0, DIE_TOP, -8.0),
        "beol": (-18.0, 9.6, 0.2), "hbm": (14.0, s["hbm_top"], -4.0), "hbm_ub": (10.0, 10.2, 0.2),
        "board": (30.0, BOARD[1], -10.0), "ip": (24.0, 5.5, 0.2), "pth": (C4_XS[6], -2.6, 0.2),
    }
    return s


# ---- bead paths ------------------------------------------------------------------------------

ZB = 0.7  # beads ride just in front of the cut face


def power_path(x=POWER_X):
    xb = min(BGA_XS, key=lambda v: abs(v - x))
    xu = min(UB_XS, key=lambda v: abs(v - x))
    return [(xb, BOARD[0] + 2.0, ZB), (xb, BGA_Y, ZB), (xb, SUB_BOT, ZB), (xb, CORE_BOT - 0.4, ZB),
            (x, CORE_BOT, ZB), (x, SUB_TOP, ZB), (x, IP_BOT, ZB), (x, IP_TOP + 0.4, ZB),
            (xu, IP_TOP + 0.6, ZB), (xu, DIE_BOT, ZB), (xu, DIE_BEOL + 0.6, ZB)]


def signal_path():
    a, b = SIGNAL
    return [(a - 3.0, DIE_BEOL - 0.3, ZB), (a, DIE_BEOL - 0.3, ZB), (a, IP_TOP + 0.5, ZB),
            (b, IP_TOP + 0.5, ZB), (b, DIE_BOT + 0.4, ZB), (b + 3.0, DIE_BOT + 0.4, ZB)]


# ---- close-up benches ----------------------------------------------------------------------


def bench_joint(m, root, o, s, name="bj", state="joint", front=True):
    """One microbump drawn at scale s, cut open, between a slab of interposer (pad, RDL, TSV top)
    and a slab of die (aluminium pad in polyimide over BEOL). o is the pad-top centre."""
    g = empty(name, root)
    x, y, z = o
    w = 0.55 * s
    p = [bx(name + "_ox", (x - w, y - 0.45 * s, -w), (x + w, y - 0.06 * s, 0.0), m["oxide"], g),
         bx(name + "_rdl", (x - w, y - 0.30 * s, -w), (x + w * 0.2, y - 0.22 * s, 0.01 * s), m["copper"], g),
         bx(name + "_si", (x - w, y - 1.2 * s, -w), (x + w, y - 0.45 * s, 0.0), m["si"], g)]
    p.append(cyl(name + "_tsv", x, y - 1.2 * s, y - 0.30 * s, z, 0.10 * s, m["copper"], g, 24, front, 0.01 * s))
    p.append(cyl(name + "_tsvl", x, y - 1.2 * s, y - 0.45 * s, z, 0.125 * s, m["liner"], g, 24, front))
    joint(p, x, y, z, s, g, m, front, state, pad=True, die_side=True)
    top = y + 1.20 * s
    p += [bx(name + "_pi", (x - w, top - 0.06 * s, -w), (x + w, top + 0.04 * s, 0.0), m["pi"], g),
          bx(name + "_beol", (x - w, top + 0.04 * s, -w), (x + w, top + 0.40 * s, 0.0), m["beol"], g),
          bx(name + "_dsi", (x - w, top + 0.40 * s, -w), (x + w, top + 0.75 * s, 0.0), m["die"], g)]
    for k in range(3):
        yy = top + (0.10 + 0.1 * k) * s
        p.append(bx(f"{name}_m{k}", (x - w, yy, -0.02 * s), (x + w * (0.6 - 0.2 * k), yy + 0.04 * s, 0.01 * s), m["copper"], g))
    join(p, name + "_mesh")
    pts = {"pad": (x + 0.27 * s, y - 0.03 * s, 0.0), "imc0": (x + 0.24 * s, y + 0.015 * s, 0.0),
           "sol": (x + 0.25 * s, y + 0.2 * s, 0.0), "imc1": (x + 0.22 * s, y + 0.405 * s, 0.0),
           "ni": (x + 0.21 * s, y + 0.46 * s, 0.0), "cu": (x + 0.2 * s, y + 0.8 * s, 0.0),
           "ubm": (x + 0.22 * s, y + 1.12 * s, 0.0), "al": (x + 0.26 * s, y + 1.17 * s, 0.0),
           "pi": (x + w, top, 0.0), "beol": (x + w, top + 0.25 * s, 0.0), "die": (x + w, top + 0.6 * s, 0.0),
           "rdl": (x + w * 0.2, y - 0.26 * s, 0.0), "tsv": (x + 0.1 * s, y - 0.8 * s, 0.0),
           "si": (x + w, y - 0.9 * s, 0.0), "top": top}
    return g, pts


def ladder(m, root, o, s, name="ld"):
    """C4 ball, microbump and hybrid pad pair at one scale s (s = units per 40 um)."""
    g = empty(name, root)
    x, y, z = o
    p = []
    # C4: ~100 um ball at 150 um pitch, drawn on pads
    r = 1.25 * s
    xc = x - 4.5 * s
    p.append(cyl(name + "_c4p0", xc, y - 0.1 * s, y, z, 1.0 * s, m["copper"], g, 32, True))
    o2 = ball(name + "_c4", (xc, y + r * 0.9, z), r, m["snag"], g, 32)
    o2.scale = (1.0, 1.0, 0.9)
    cut(o2)
    p.append(o2)
    p.append(cyl(name + "_c4p1", xc, y + r * 1.8, y + r * 1.8 + 0.1 * s, z, 1.0 * s, m["al"], g, 32, True))
    joint(p, x, y, z, s, g, m, True, "joint")
    xh = x + 2.0 * s
    for k, yy in enumerate((y, y + 0.12 * s)):
        p.append(bx(f"{name}_hox{k}", (xh - 0.6 * s, yy, -0.6 * s), (xh + 0.6 * s, yy + 0.12 * s, 0.0), m["oxide"], g))
    for dx in (-0.4, -0.2, 0.0, 0.2, 0.4):
        p.append(bx(f"{name}_hcu{dx}", (xh + (dx - 0.05) * s, y, -0.1 * s), (xh + (dx + 0.05) * s, y + 0.24 * s, 0.01 * s), m["copper"], g))
    join(p, name + "_mesh")
    return g, {"c4": (xc + r, y + r, 0.0), "ub": (x + 0.25 * s, y + 0.6 * s, 0.0), "hb": (xh + 0.6 * s, y + 0.12 * s, 0.0),
               "c4x": xc, "ubx": x, "hbx": xh}


def hybrid(m, root, o, s, name="hy", gap=0.0, dish=True):
    """Two bonding faces in section: copper pads set in oxide over Cu wiring. The upper face is a
    child group so scenes can lower it; returns (group, upper group, pts)."""
    g = empty(name, root)
    x, y, z = o
    w = 2.2 * s
    xs = [x + (k - 2) * 0.8 * s for k in range(5)]
    lo = [bx(name + "_si0", (x - w, y - 1.0 * s, -w), (x + w, y - 0.5 * s, 0.0), m["si"], g),
          bx(name + "_ox0", (x - w, y - 0.5 * s, -w), (x + w, y, 0.0), m["oxide"], g)]
    for xx in xs:
        dd = 0.02 * s if dish else 0.0
        lo.append(bx(f"{name}_p0{xx:.2f}", (xx - 0.22 * s, y - 0.32 * s, -0.22 * s), (xx + 0.22 * s, y - dd, 0.01 * s), m["copper"], g))
        lo.append(bx(f"{name}_v0{xx:.2f}", (xx - 0.07 * s, y - 0.5 * s, -0.07 * s), (xx + 0.07 * s, y - 0.32 * s, 0.01 * s), m["copper"], g))
    join(lo, name + "_lo")
    up = empty(name + "_up", g)
    hi = [bx(name + "_ox1", (x - w, y + gap, -w), (x + w, y + gap + 0.5 * s, 0.0), m["oxide"], up),
          bx(name + "_si1", (x - w, y + gap + 0.5 * s, -w), (x + w, y + gap + 1.0 * s, 0.0), m["die"], up)]
    for xx in xs:
        dd = 0.02 * s if dish else 0.0
        hi.append(bx(f"{name}_p1{xx:.2f}", (xx - 0.22 * s, y + gap + dd, -0.22 * s), (xx + 0.22 * s, y + gap + 0.32 * s, 0.01 * s), m["copper"], up))
        hi.append(bx(f"{name}_v1{xx:.2f}", (xx - 0.07 * s, y + gap + 0.32 * s, -0.07 * s), (xx + 0.07 * s, y + gap + 0.5 * s, 0.01 * s), m["copper"], up))
    join(hi, name + "_hi")
    return g, up, {"ox": (x + w, y, 0.0), "cu": (xs[3] + 0.22 * s, y, 0.0), "pads": xs, "w": w, "y": y}


def bridges(m, root, o, s, pitches, name="br"):
    """Rows of reflowed solder bumps at each pitch in `pitches` (units at scale s); solder volume
    stays the same, so at the tightest pitch the balls touch. Returns per-row x lists."""
    g = empty(name, root)
    x0, y, z = o
    p, rows = [], []
    for k, pt in enumerate(pitches):
        zz = z - 3.0 * s * k
        xs = [x0 + pt * s * i for i in range(7)]
        rows.append((xs, zz))
        for xx in xs:
            p.append(cyl(f"{name}_pd{k}_{xx:.2f}", xx, y - 0.06 * s, y, zz, 0.27 * s, m["copper"], g, 16, k == 0))
            o2 = ball(f"{name}_b{k}_{xx:.2f}", (xx, y + 0.3 * s, zz), 0.36 * s, m["snag"], g, 16)
            o2.scale = (1.0, 1.0, 0.8)
            if k == 0:
                cut(o2)
            p.append(o2)
    p.append(bx(name + "_base", (x0 - 1.0 * s, y - 0.4 * s, z - 3.0 * s * len(pitches)), (x0 + 6.0 * pitches[0] * s + 1.0 * s, y - 0.06 * s, 0.0), m["oxide"], g))
    join(p, name + "_mesh")
    return g, rows


def glow_bridges(m, root, rows, k, s, y, name, iv):
    """Red solder bridges between neighbours of row k, shown during `iv`."""
    g = empty(name, root)
    xs, zz = rows[k]
    p = [bx(f"{name}{i}", (xs[i] + 0.2 * s, y + 0.24 * s, zz - 0.06 * s), (xs[i + 1] - 0.2 * s, y + 0.36 * s, zz + 0.06 * s), m["stress"], g) for i in range(len(xs) - 1)]
    join(p, name + "_mesh")
    show(g, iv)
    return g


def lower(obj, keys):
    """Key `obj`'s y offset: keys = [(frame, dy), ...], linear."""
    for f, dy in keys:
        key(obj, f, "location", P(0.0, dy, 0.0), linear=True)


def slide(obj, keys):
    """Key a full offset: keys = [(frame, (dx, dy, dz)), ...], linear."""
    for f, d in keys:
        key(obj, f, "location", P(*d), linear=True)


def glow_box(m, root, name, lo, hi, mm, iv):
    g = empty(name, root)
    bx(name + "_b", lo, hi, mm, g)
    show(g, iv)
    return g


def frame(c, size, yaw=0.30, pitch=0.30, pad=1.1):
    return D.frame(c, size, yaw, pitch, pad, min_d=4.0)


G = 8.0  # pbr3d's near plane is 40 units: the whole scene is scaled up by G at export


def finish(root, name, page):
    """Scale the root by G (the camera and tags ride along) and export."""
    import sand_zooms
    root.scale = (G, G, G)
    sand_zooms.finish(name, page=page)
