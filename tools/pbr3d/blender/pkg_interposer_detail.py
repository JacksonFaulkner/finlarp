"""Part kit for the PACKAGING tab's INTERPOSER page (pkg_interposer_*.py).

One CoWoS package drawn as a cut-away along z = 0 (the camera sits on +z), with the vertical scale
stretched so every layer reads. Units: drawing units, Y up, x across the package, z toward the camera.

  board        green PCB under the package, BGA balls on it
  substrate    organic package substrate: bottom ABF build-up, a glass-fibre core with plated
               through-holes, top ABF build-up (copper lines and stacked microvias in each layer)
  c4           C4 solder bumps between substrate and interposer, half out of the underfill
  interposer   mode "S": a silicon slab (backside passivation and pads, TSVs with oxide liners,
               a 4-level copper BEOL on top). Mode "L": an organic RDL interposer with copper
               through-interposer vias (TIVs) and LSI bridge chips sunk under the die-HBM seams
  ubumps       copper-pillar microbumps with solder caps under the die and the stacks
  die          a GPU logic die (its own BEOL band at the bottom) or two dies (mode "L")
  hbm          HBM stacks: blue base die, 8 orange DRAM dies, gold TSV columns on the cut face
  lid          TIM and a nickel-plated copper lid with feet (hidden until shown)

Close-up benches for the sections (built well above the package at BY): a TSV cut through, a BEOL
stack, line-pitch comparison strips, a bridge chip, a 300 mm wafer of interposer squares, a reticle
plane. Bead paths for data (cyan), power (yellow) and heat (orange) ride in front of the cut face.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, tube, disc, show, mat  # noqa: E402
from power_vrm_detail import bx, join, empty, present, run, rise, frame, camera_path, polyline  # noqa: E402,F401

# ---- levels (y) ---------------------------------------------------------------------------------
Z0 = -30.0  # back of the cut-away; the cut face is z = 0
FZ = 0.45  # beads ride this far in front of the cut face

BOARD = (-21.0, -15.5)
BGA_Y, BGA_R = -14.2, 1.2
SUB_B = (-12.8, -10.6)  # bottom build-up
CORE = (-10.6, -6.8)
SUB_T = (-6.8, -3.8)  # top build-up
SUB_X = 58.0
C4_Y, C4_R = -2.75, 0.95
IP_B = -1.8  # interposer bottom (backside passivation)
SI = (-1.5, 1.3)  # silicon body
BEOL = (1.3, 2.7)
M_Y = [1.45, 1.78, 2.11, 2.44]  # M1-M4 centre heights
UB = (2.7, 3.5)
DIE = (3.5, 6.6)
DIE_BEOL = 0.55
HBM_Y = (3.5, 10.4)
TIM = (6.6, 7.2)
LID = (10.6, 12.0)
IP_X = 40.0
DIE_X = 14.0
HBM_X = (17.0, 29.0)


def materials():
    return {
        "ip_board": mat("ipx_board", (0.08, 0.30, 0.17), rough=0.6),
        "ip_core": mat("ipx_core", (0.62, 0.55, 0.36), rough=0.8),
        "ip_abf": mat("ipx_abf", (0.20, 0.17, 0.13), rough=0.75),
        "ip_cu": mat("ipx_cu", (0.86, 0.52, 0.30), metal=0.9, rough=0.3),
        "ip_cu_dark": mat("ipx_cu_dark", (0.66, 0.36, 0.22), metal=0.9, rough=0.35),
        "ip_solder": mat("ipx_solder", (0.76, 0.78, 0.82), metal=0.9, rough=0.25),
        "ip_si": mat("ipx_si", (0.36, 0.40, 0.48), metal=0.5, rough=0.35),
        "ip_oxide": mat("ipx_oxide", (0.70, 0.78, 0.84), rough=0.3),
        "ip_liner": mat("ipx_liner", (0.88, 0.90, 0.94), rough=0.3),
        "ip_barrier": mat("ipx_barrier", (0.32, 0.30, 0.42), metal=0.7, rough=0.3),
        "ip_pass": mat("ipx_pass", (0.40, 0.62, 0.52), rough=0.4),
        "ip_organic": mat("ipx_organic", (0.22, 0.20, 0.18), rough=0.75),
        "ip_pi": mat("ipx_pi", (0.62, 0.42, 0.16), rough=0.5),
        "ip_bridge": mat("ipx_bridge", (0.25, 0.80, 0.80), metal=0.3, rough=0.35),
        "ip_mold": mat("ipx_mold", (0.10, 0.10, 0.11), rough=0.6),
        "ip_fill": mat("ipx_fill", (0.13, 0.11, 0.10), rough=0.9),
        "ip_die": mat("ipx_die", (0.40, 0.30, 0.70), metal=0.3, rough=0.3),
        "ip_die_beol": mat("ipx_die_beol", (0.62, 0.50, 0.86), metal=0.3, rough=0.3),
        "ip_base": mat("ipx_base", (0.25, 0.45, 0.95), metal=0.2, rough=0.4),
        "ip_dram": mat("ipx_dram", (0.93, 0.52, 0.18), rough=0.45),
        "ip_gold": mat("ipx_gold", (1.0, 0.80, 0.32), metal=0.8, rough=0.25),
        "ip_tim": mat("ipx_tim", (0.62, 0.64, 0.68), metal=0.6, rough=0.5),
        "ip_lid": mat("ipx_lid", (0.66, 0.68, 0.72), metal=0.85, rough=0.3),
        "ip_wafer": mat("ipx_wafer", (0.30, 0.32, 0.42), metal=0.4, rough=0.45),
        "ip_square": mat("ipx_square", (0.55, 0.62, 0.72), metal=0.5, rough=0.3),
        "ip_reticle": mat("ipx_reticle", (0.95, 0.70, 0.30), emit=(1.0, 0.65, 0.25), strength=1.2),
        "ip_grid": mat("ipx_grid", (0.24, 0.28, 0.34), rough=0.6),
        # glows
        "ip_data": mat("ipx_data", (0.30, 0.90, 1.0), emit=(0.20, 0.90, 1.0), strength=4.0),
        "ip_power": mat("ipx_power", (1.0, 0.85, 0.20), emit=(1.0, 0.80, 0.20), strength=4.0),
        "ip_heat": mat("ipx_heat", (1.0, 0.50, 0.20), emit=(1.0, 0.42, 0.12), strength=3.5),
        "ip_hot": mat("ipx_hot", (0.95, 0.40, 0.15), emit=(1.0, 0.38, 0.10), strength=1.3),
        "ip_glow": mat("ipx_glow", (0.30, 0.90, 1.0), emit=(0.25, 0.85, 1.0), strength=1.4),
        "ip_fail": mat("ipx_fail", (1.0, 0.15, 0.10), emit=(1.0, 0.10, 0.06), strength=2.0),
    }


def xs(x0, x1, pitch):
    n = int(round((x1 - x0) / pitch))
    return [x0 + pitch * i for i in range(n + 1)]


# ---- parts --------------------------------------------------------------------------------------


def board(m, parent, half=SUB_X + 22.0):
    g = empty("ip_board_grp", parent)
    bx("ip_board", (-half, BOARD[0], Z0 - 20.0), (half, BOARD[1], 0.0), m["ip_board"], g)
    bx("ip_board_pad", (-half, BOARD[1], Z0 - 20.0), (half, BOARD[1] + 0.15, 0.0), m["ip_cu_dark"], g)
    balls = [ball(f"ip_bga{i}", (x, BGA_Y, -0.3), BGA_R, m["ip_solder"], g, 14) for i, x in enumerate(xs(-52.0, 52.0, 4.0))]
    join(balls, "ip_bga")
    return g


def substrate(m, parent, half=SUB_X):
    """ABF build-up on a glass-fibre core: copper lines on the cut face, microvias and PTHs."""
    g = empty("ip_sub_grp", parent)
    bx("ip_sub_core", (-half, CORE[0], Z0), (half, CORE[1], 0.0), m["ip_core"], g)
    bx("ip_sub_bot", (-half, SUB_B[0], Z0), (half, SUB_B[1], 0.0), m["ip_abf"], g)
    bx("ip_sub_top", (-half, SUB_T[0], Z0), (half, SUB_T[1], 0.0), m["ip_abf"], g)
    cu = []
    # copper planes / lines in the build-up layers (broken lines on the cut face)
    for li, y in enumerate([SUB_B[0] + 0.5, SUB_B[0] + 1.4, SUB_T[0] + 0.5, SUB_T[0] + 1.4, SUB_T[0] + 2.3]):
        off = 1.5 * (li % 2)
        for k, x in enumerate(xs(-half + 2.0 + off, half - 4.0, 5.0)):
            cu.append(bx(f"ip_subl{li}_{k}", (x, y - 0.2, -6.0), (x + 3.4, y + 0.2, 0.08), m["ip_cu"], g))
    # stacked microvias in the top build-up and plated through-holes in the core
    for k, x in enumerate(xs(-36.0, 36.0, 6.0)):
        cu.append(tube(f"ip_pth{k}", (x, CORE[0], -0.4), (x, CORE[1], -0.4), 0.55, m["ip_cu"], g, 12))
        for j, (ya, yb) in enumerate([(SUB_T[0], SUB_T[0] + 1.4), (SUB_T[0] + 1.4, SUB_T[1]), (SUB_B[0], SUB_B[1])]):
            cu.append(tube(f"ip_mv{k}_{j}", (x, ya, -0.3), (x, yb, -0.3), 0.32, m["ip_cu"], g, 10))
    join(cu, "ip_sub_cu")
    return g


def c4(m, parent, half=IP_X - 2.0, pitch=3.2):
    g = empty("ip_c4_grp", parent)
    bx("ip_c4_fill", (-half - 1.5, SUB_T[1], Z0), (half + 1.5, IP_B, -1.0), m["ip_fill"], g)
    parts = []
    for i, x in enumerate(xs(-half, half, pitch)):
        parts.append(ball(f"ip_c4_{i}", (x, C4_Y, -0.5), C4_R, m["ip_solder"], g, 14))
        parts.append(bx(f"ip_c4p{i}", (x - 0.8, SUB_T[1], -1.4), (x + 0.8, SUB_T[1] + 0.15, 0.3), m["ip_cu"], g))
    join(parts, "ip_c4")
    return g


def interposer_s(m, parent, half=IP_X):
    """Silicon interposer: backside pads, TSVs with oxide liners, a 4-level BEOL on top."""
    g = empty("ip_si_grp", parent)
    bx("ip_si_back", (-half, IP_B, Z0), (half, SI[0], 0.0), m["ip_pass"], g)
    bx("ip_si_body", (-half, SI[0], Z0), (half, SI[1], 0.0), m["ip_si"], g)
    bx("ip_beol_ild", (-half, BEOL[0], Z0), (half, BEOL[1], 0.0), m["ip_oxide"], g)
    tsv, liner, cu = [], [], []
    for i, x in enumerate(xs(-half + 2.0, half - 2.0, 3.2)):
        liner.append(tube(f"ip_tsvl{i}", (x, SI[0], -0.35), (x, SI[1], -0.35), 0.62, m["ip_liner"], g, 14))
        tsv.append(tube(f"ip_tsv{i}", (x, SI[0] - 0.05, 0.0), (x, SI[1] + 0.05, 0.0), 0.42, m["ip_cu"], g, 14))
        cu.append(bx(f"ip_bpad{i}", (x - 0.8, IP_B, -1.0), (x + 0.8, SI[0], 0.05), m["ip_cu_dark"], g))
    join(liner, "ip_tsv_liner")
    join(tsv, "ip_tsv")
    # BEOL: M1-M4 lines; finer (shorter, denser) low, coarser high; vias between
    for li, y in enumerate(M_Y):
        seg, gap = (1.2, 0.6) if li < 2 else (2.6, 1.0)
        x = -half + 0.6 + 0.4 * li
        k = 0
        while x + seg < half - 0.6:
            cu.append(bx(f"ip_m{li}_{k}", (x, y - 0.09, -8.0), (x + seg, y + 0.09, 0.04), m["ip_cu"], g))
            if li < 3 and k % 2 == 0:
                cu.append(bx(f"ip_v{li}_{k}", (x + seg * 0.4, y + 0.09, -0.8), (x + seg * 0.4 + 0.22, M_Y[li + 1] - 0.09, 0.04), m["ip_cu"], g))
            x += seg + gap
            k += 1
    join(cu, "ip_beol_cu")
    return g


def interposer_l(m, parent, half=IP_X, bridges=(-15.5, 15.5), seam=False):
    """CoWoS-L: organic RDL interposer (polyimide layers with copper), copper TIVs, and LSI
    bridge chips sunk under the die-HBM seams (and under the die-die seam when `seam`)."""
    g = empty("ip_org_grp", parent)
    bx("ip_org_body", (-half, IP_B, Z0), (half, SI[1], 0.0), m["ip_mold"], g)
    bx("ip_org_rdl", (-half, BEOL[0], Z0), (half, BEOL[1], 0.0), m["ip_pi"], g)
    cu = []
    br_x = list(bridges) + ([0.0] if seam else [])
    for li, y in enumerate([1.55, 2.0, 2.45]):
        for k, x in enumerate(xs(-half + 1.0 + li, half - 3.5, 3.4)):
            cu.append(bx(f"ip_rdl{li}_{k}", (x, y - 0.11, -8.0), (x + 2.2, y + 0.11, 0.04), m["ip_cu"], g))
    for i, x in enumerate(xs(-half + 2.0, half - 2.0, 3.2)):
        if any(abs(x - b) < 4.6 for b in br_x):
            continue
        cu.append(tube(f"ip_tiv{i}", (x, IP_B, -0.1), (x, SI[1], -0.1), 0.5, m["ip_cu"], g, 12))
    join(cu, "ip_org_cu")
    pts = {}
    for j, b in enumerate(br_x):
        pts[j] = bridge(m, g, b, f"ip_br{j}")
    return g, pts


def bridge(m, parent, xc, name, w=4.0):
    """One LSI bridge chip under a seam: silicon with a fine 4-line BEOL on top, its own bumps."""
    bx(f"{name}_si", (xc - w, -0.9, -14.0), (xc + w, 0.9, 0.0), m["ip_bridge"], parent)
    bx(f"{name}_beol", (xc - w, 0.9, -14.0), (xc + w, 1.3, 0.0), m["ip_oxide"], parent)
    cu = []
    for li, y in enumerate([0.98, 1.1, 1.22]):
        for k, x in enumerate(xs(xc - w + 0.3 + 0.15 * li, xc + w - 0.6, 0.55)):
            cu.append(bx(f"{name}_l{li}_{k}", (x, y - 0.035, -6.0), (x + 0.32, y + 0.035, 0.04), m["ip_cu"], parent))
    join(cu, f"{name}_cu")
    return (xc, 1.1, 0.0)


def ubumps(m, parent, spans, pitch=0.9):
    """Copper pillars with solder caps between UB[0] and UB[1], across each (x0, x1) span."""
    g = empty("ip_ub_grp", parent)
    pil, cap, fill = [], [], []
    for si, (x0, x1) in enumerate(spans):
        fill.append(bx(f"ip_ubf{si}", (x0 - 0.4, UB[0], Z0 + 10.0), (x1 + 0.4, UB[1], -0.7), m["ip_fill"], g))
        for i, x in enumerate(xs(x0 + 0.3, x1 - 0.3, pitch)):
            pil.append(tube(f"ip_ubp{si}_{i}", (x, UB[0], -0.2), (x, UB[0] + 0.5, -0.2), 0.28, m["ip_cu"], g, 10))
            cap.append(tube(f"ip_ubc{si}_{i}", (x, UB[0] + 0.5, -0.2), (x, UB[1], -0.2), 0.30, m["ip_solder"], g, 10))
    join(pil, "ip_ub_pillar")
    join(cap, "ip_ub_cap")
    join(fill, "ip_ub_fill")
    return g


def die(m, parent, x0=-DIE_X, x1=DIE_X, name="ip_die"):
    g = empty(f"{name}_grp", parent)
    bx(f"{name}_beol", (x0, DIE[0], Z0 + 6.0), (x1, DIE[0] + DIE_BEOL, 0.0), m["ip_die_beol"], g)
    bx(f"{name}_si", (x0, DIE[0] + DIE_BEOL, Z0 + 6.0), (x1, DIE[1], 0.0), m["ip_die"], g)
    glow = empty(f"{name}_glow", parent)
    bx(f"{name}_glow_b", (x0 + 0.2, DIE[0] + DIE_BEOL, 0.0), (x1 - 0.2, DIE[1] - 0.2, 0.08), m["ip_hot"], glow)
    present(glow, [])
    return g, glow


def hbm(m, parent, x0, x1, name, n=8):
    """One HBM stack, cut through on its face: base die, n DRAM dies on underfill, TSV columns."""
    g = empty(name, parent)
    y0, y1 = HBM_Y
    bt = 1.0
    pitch = (y1 - y0 - bt) / n
    bx(f"{name}_base", (x0, y0, -12.0), (x1, y0 + bt, 0.0), m["ip_base"], g)
    dram, fill = [], []
    for k in range(n):
        yb = y0 + bt + k * pitch
        fill.append(bx(f"{name}_f{k}", (x0 + 0.3, yb, -11.7), (x1 - 0.3, yb + 0.22 * pitch, -0.1), m["ip_fill"], g))
        dram.append(bx(f"{name}_d{k}", (x0, yb + 0.22 * pitch, -12.0), (x1, yb + pitch, 0.0), m["ip_dram"], g))
    join(dram, f"{name}_dram")
    join(fill, f"{name}_fill")
    cols = [tube(f"{name}_t{i}", (x, y0 + 0.4, -0.05), (x, y1, -0.05), 0.22, m["ip_gold"], g, 8)
            for i, x in enumerate(xs(x0 + 2.0, x1 - 2.0, 2.0))]
    join(cols, f"{name}_tsv")
    return g


def lid(m, parent, half=IP_X + 6.0):
    g = empty("ip_lid_grp", parent)
    bx("ip_tim", (-DIE_X, TIM[0], Z0 + 6.0), (DIE_X, LID[0], 0.0), m["ip_tim"], g)
    for s in (-1, 1):
        bx(f"ip_tim_h{s}", (s * HBM_X[0], HBM_Y[1], -12.0), (s * HBM_X[1], LID[0], 0.0), m["ip_tim"], g)
        bx(f"ip_lid_foot{s}", (s * half, SUB_T[1], Z0), (s * (half + 3.0), LID[0], 0.0), m["ip_lid"], g)
    bx("ip_lid_top", (-half - 3.0, LID[0], Z0), (half + 3.0, LID[1], 0.0), m["ip_lid"], g)
    return g


# ---- whole package ------------------------------------------------------------------------------


def scene(m, root, mode="S", with_lid=True, with_board=True, two_dies=None):
    """The whole package in mode "S" (silicon) or "L" (organic + bridges). Returns groups and points."""
    two = (mode == "L") if two_dies is None else two_dies
    out = {"mode": mode}
    if with_board:
        out["board"] = board(m, root)
    out["sub"] = substrate(m, root)
    out["c4"] = c4(m, root)
    if mode == "S":
        out["ip"] = interposer_s(m, root)
        out["br"] = {}
    else:
        out["ip"], out["br"] = interposer_l(m, root, seam=two)
    spans = [(-HBM_X[1], -HBM_X[0]), (HBM_X[0], HBM_X[1])]
    spans += [(-DIE_X, -0.6), (0.6, DIE_X)] if two else [(-DIE_X, DIE_X)]
    out["ub"] = ubumps(m, root, spans)
    if two:
        dl, gl = die(m, root, -DIE_X, -0.6, "ip_die_l")
        dr, gr = die(m, root, 0.6, DIE_X, "ip_die_r")
        out["die"] = [dl, dr]
        out["glow"] = [gl, gr]
    else:
        d, gl = die(m, root)
        out["die"] = [d]
        out["glow"] = [gl]
    out["hbm"] = [hbm(m, root, -HBM_X[1], -HBM_X[0], "ip_hbm_l"), hbm(m, root, HBM_X[0], HBM_X[1], "ip_hbm_r")]
    if with_lid:
        out["lid"] = lid(m, root)
        present(out["lid"], [])
    out["pts"] = {
        "die": (0.0, DIE[1], 0.0), "die_beol": (-6.0, DIE[0] + 0.3, 0.0), "hbm": (HBM_X[1] - 1.0, HBM_Y[1], 0.0),
        "hbm_base": (HBM_X[0] + 3.0, HBM_Y[0] + 0.5, 0.0), "dram": (-HBM_X[0] - 4.0, 7.0, 0.0),
        "beol": (-30.0, BEOL[1], 0.0), "m1": (-24.0, M_Y[0], 0.0), "si": (-34.0, 0.0, 0.0),
        "tsv": (-8.4, 0.0, 0.0), "c4": (-11.0, C4_Y, 0.0), "ub": (-4.0, UB[1], 0.0),
        "sub_top": (40.0, SUB_T[1], 0.0), "core": (-45.0, -8.7, 0.0), "pth": (-36.0, -8.7, 0.0),
        "abf": (50.0, SUB_B[0] + 1.0, 0.0), "bga": (-30.0, BGA_Y, 0.0), "board": (55.0, BOARD[1], 0.0),
        "lid": (30.0, LID[1], 0.0), "tim": (-8.0, TIM[1], 0.0), "underfill": (-14.6, UB[0] + 0.4, 0.0),
    }
    return out


# ---- bead paths (in front of the cut face) --------------------------------------------------------


def data_path(side, k):
    """HBM base die -> microbump -> down into the BEOL (M2) -> across -> up into the die edge."""
    xh = side * (HBM_X[0] + 2.0 + 1.3 * k)
    xd = side * (DIE_X - 1.5 - 1.3 * k)
    y = M_Y[1 + k % 2]
    return [(xh, HBM_Y[0] + 0.6, FZ), (xh, UB[0], FZ), (xh, y, FZ), (xd, y, FZ), (xd, UB[1], FZ), (xd, DIE[0] + 0.4, FZ)]


def bridge_path(side, k):
    """Same trip through an LSI bridge in mode L: down, through the bridge's fine lines, up."""
    xh = side * (HBM_X[0] + 0.8 + 0.7 * k)
    xd = side * (DIE_X - 0.8 - 0.7 * k)
    y = 0.98 + 0.12 * (k % 3)
    return [(xh, HBM_Y[0] + 0.6, FZ), (xh, UB[0], FZ), (xh, y, FZ), (xd, y, FZ), (xd, UB[1], FZ), (xd, DIE[0] + 0.4, FZ)]


def power_path(x):
    """Board -> BGA -> PTH through the core -> C4 -> TSV -> BEOL -> microbump -> die."""
    xp = round(x / 6.0) * 6.0
    xt = round((x + 38.0) / 3.2) * 3.2 - 38.0
    return [(xp, BOARD[1], FZ), (xp, BGA_Y, FZ), (xp, CORE[1], FZ), (xp, SUB_T[1], FZ), (xt, C4_Y, FZ),
            (xt, SI[0], FZ), (xt, SI[1], FZ), (xt, UB[1], FZ), (xt, DIE[0] + 0.6, FZ)]


# ---- benches (close-ups above the package) ---------------------------------------------------------

BY = 200.0


def tsv_bench(m, parent, o=(0.0, BY, 0.0), s=6.0, name="tb"):
    """One TSV cut through, large: silicon, oxide liner, barrier, copper fill, BEOL landing pad and
    M1 above, backside pad and C4 below. Returns points (absolute)."""
    ox, oy, oz = o
    g = empty(f"{name}_grp", parent)
    h = 3.0 * s  # silicon thickness
    w = 4.0 * s

    def B(n, a, b, mt):
        return bx(f"{name}_{n}", (ox + a[0] * s, oy + a[1] * s, oz + a[2] * s), (ox + b[0] * s, oy + b[1] * s, oz + b[2] * s), mt, g)

    B("si_l", (-4.0, 0.0, -3.0), (-0.85, 3.0, 0.0), m["ip_si"])
    B("si_r", (0.85, 0.0, -3.0), (4.0, 3.0, 0.0), m["ip_si"])
    B("si_back", (-0.85, 0.0, -3.0), (0.85, 3.0, -0.85), m["ip_si"])
    for sx in (-1, 1):
        B(f"liner{sx}", (sx * 0.85, 0.0, -0.85), (sx * 0.62, 3.0, 0.0), m["ip_liner"])
        B(f"bar{sx}", (sx * 0.62, 0.0, -0.62), (sx * 0.52, 3.0, 0.0), m["ip_barrier"])
    B("liner_back", (-0.85, 0.0, -0.85), (0.85, 3.0, -0.62), m["ip_liner"])
    B("bar_back", (-0.62, 0.0, -0.62), (0.62, 3.0, -0.52), m["ip_barrier"])
    B("cu", (-0.52, -0.05, -0.52), (0.52, 3.05, 0.0), m["ip_cu"])
    B("ild", (-4.0, 3.0, -3.0), (4.0, 4.1, 0.0), m["ip_oxide"])
    B("m1", (-1.6, 3.05, -2.0), (1.6, 3.35, 0.03), m["ip_cu"])
    B("v1", (-0.3, 3.35, -1.0), (0.3, 3.7, 0.03), m["ip_cu"])
    B("m2", (-3.0, 3.7, -2.0), (0.9, 3.95, 0.03), m["ip_cu"])
    B("pass", (-4.0, -0.4, -3.0), (4.0, 0.0, 0.0), m["ip_pass"])
    B("bpad", (-1.4, -0.45, -1.4), (1.4, -0.05, 0.03), m["ip_cu_dark"])
    ball(f"{name}_c4", (ox, oy - 1.45 * s, oz - 0.3 * s), 1.05 * s, m["ip_solder"], g, 24)
    B("sub", (-4.0, -3.4, -3.0), (4.0, -2.4, 0.0), m["ip_abf"])
    B("subpad", (-1.3, -2.4, -1.3), (1.3, -2.25, 0.03), m["ip_cu"])
    p = lambda a, b: (ox + a * s, oy + b * s, oz + 0.12 * s)  # noqa: E731
    pts = {"cu": p(0.0, 1.5), "liner": p(-0.75, 2.3), "bar": p(0.57, 0.8), "si": p(-2.6, 1.8), "m1": p(1.2, 3.2),
           "bpad": p(1.2, -0.25), "c4": p(0.6, -1.5), "ild": p(-3.0, 3.8), "sub": p(-3.0, -2.9),
           "path": [p(0.0, -3.0), p(0.0, -1.5), p(0.0, -0.2), p(0.0, 1.5), p(0.0, 3.2), p(0.0, 3.85), p(-2.6, 3.85)]}
    return g, pts


def beol_bench(m, parent, o=(0.0, BY, 0.0), s=7.0, name="bb"):
    """The interposer's BEOL, large: silicon at the bottom, M1-M4 in oxide with vias, a top pad and
    a microbump pillar. Fine lines low, fatter lines high. Returns (group, points, path)."""
    ox, oy, oz = o
    g = empty(f"{name}_grp", parent)

    def B(n, a, b, mt):
        return bx(f"{name}_{n}", (ox + a[0] * s, oy + a[1] * s, oz + a[2] * s), (ox + b[0] * s, oy + b[1] * s, oz + b[2] * s), mt, g)

    B("si", (-5.0, -1.2, -3.0), (5.0, 0.0, 0.0), m["ip_si"])
    B("ild", (-5.0, 0.0, -3.0), (5.0, 3.6, 0.0), m["ip_oxide"])
    cu = []
    levels = [(0.35, 0.18, 0.4, 0.4), (1.1, 0.22, 0.4, 0.4), (1.95, 0.35, 0.9, 0.6), (2.85, 0.45, 1.6, 0.8)]
    for li, (y, t, w, gap) in enumerate(levels):
        x = -4.8
        k = 0
        while x + w < 4.8:
            cu.append(B(f"m{li}_{k}", (x, y - t / 2, -2.5), (x + w, y + t / 2, 0.02), m["ip_cu"]))
            if li < 3 and k % 3 == 1:
                ny = levels[li + 1][0] - levels[li + 1][1] / 2
                cu.append(B(f"v{li}_{k}", (x + w * 0.3, y + t / 2, -1.0), (x + w * 0.3 + 0.16, ny, 0.02), m["ip_cu"]))
            x += w + gap
            k += 1
    join(cu, f"{name}_cu")
    B("pad", (-1.0, 3.6, -1.2), (1.0, 3.75, 0.02), m["ip_cu"])
    B("pillar", (-0.6, 3.75, -0.8), (0.6, 4.9, 0.0), m["ip_cu"])
    B("cap", (-0.65, 4.9, -0.85), (0.65, 5.5, 0.0), m["ip_solder"])
    p = lambda a, b: (ox + a * s, oy + b * s, oz + 0.15 * s)  # noqa: E731
    pts = {"m1": p(-3.0, 0.35), "m2": p(3.0, 1.1), "m3": p(-2.6, 1.95), "m4": p(2.5, 2.85), "si": p(-3.6, -0.6),
           "ild": p(4.3, 3.3), "ub": p(0.0, 5.2), "pad": p(0.9, 3.7)}
    path = [p(0.0, 5.3), p(0.0, 3.7), p(-0.1, 2.85), p(-2.0, 2.85), p(-2.0, 1.1), p(-4.6, 1.1)]
    return g, pts, path


def pitch_strips(m, parent, o=(0.0, BY, 0.0), name="ps"):
    """Three strips side by side, seen from above, all at one scale (1 um = 1 unit, each strip 40
    wide): silicon BEOL (0.4 um lines), organic RDL (2 um), substrate build-up (10 um). Copper lines
    run along z on top of each strip's insulator."""
    ox, oy, oz = o
    g = empty(f"{name}_grp", parent)
    cols = {"si": -48.0, "rdl": 0.0, "sub": 48.0}
    specs = {"si": (0.4, 0.4, m["ip_oxide"]), "rdl": (2.0, 2.0, m["ip_pi"]), "sub": (10.0, 10.0, m["ip_abf"])}
    pts = {}
    for key_, (w, gap, body) in specs.items():
        cx = ox + cols[key_]
        bx(f"{name}_{key_}_body", (cx - 20.0, oy - 3.0, oz - 30.0), (cx + 20.0, oy, oz), body, g)
        cu = []
        x = cx - 19.5 + (gap / 2 if w > 1 else 0.0)
        k = 0
        while x + w <= cx + 19.6:
            cu.append(bx(f"{name}_{key_}_{k}", (x, oy, oz - 29.0), (x + w, oy + 0.35, oz - 1.0), m["ip_cu"], g))
            x += w + gap
            k += 1
        join(cu, f"{name}_{key_}_cu")
        pts[key_] = (cx, oy + 0.4, oz - 29.0)
        pts[key_ + "_lo"] = (cx - 10.0, oy + 0.4, oz - 4.0)
        pts[key_ + "_n"] = k
    return g, pts


def wafer(m, parent, c, sq_w, sq_h, name, r=150.0, show_squares=True):
    """A 300 mm wafer (r = 150 units = mm) of interposer squares sq_w x sq_h mm, lying flat. Returns
    (group, whole squares that fit)."""
    g = empty(f"{name}_grp", parent)
    disc(f"{name}_disc", c, r, 1.2, m["ip_wafer"], g, 128)
    cx, cy, cz = c
    sq = []
    gap = 2.0
    nx = int(r * 2 // (sq_w + gap)) + 1
    nz = int(r * 2 // (sq_h + gap)) + 1
    count = 0
    for i in range(-nx, nx + 1):
        for j in range(-nz, nz + 1):
            x0 = i * (sq_w + gap) - sq_w / 2
            z0 = j * (sq_h + gap) - sq_h / 2
            corners = [(x0, z0), (x0 + sq_w, z0), (x0, z0 + sq_h), (x0 + sq_w, z0 + sq_h)]
            if all(math.hypot(a, b) < r - 3.0 for a, b in corners):
                count += 1
                if show_squares:
                    sq.append(bx(f"{name}_sq{i}_{j}", (cx + x0, cy + 0.6, cz + z0), (cx + x0 + sq_w, cy + 1.0, cz + z0 + sq_h), m["ip_square"], g))
    if sq:
        join(sq, f"{name}_squares")
    return g, count


RET_W, RET_H = 26.0, 33.0  # one reticle field, mm


def reticle_plane(m, parent, c, n_w, n_h, name, frac=1.0):
    """A flat plate of n_w x n_h reticle fields (glowing outlines), its area `frac` of the full grid."""
    g = empty(f"{name}_grp", parent)
    cx, cy, cz = c
    W, H = RET_W * n_w * math.sqrt(frac), RET_H * n_h * math.sqrt(frac)
    bx(f"{name}_plate", (cx - W / 2, cy, cz - H / 2), (cx + W / 2, cy + 0.8, cz + H / 2), m["ip_si"], g)
    lines = []
    for i in range(n_w + 1):
        x = cx - RET_W * n_w / 2 + RET_W * i
        lines.append(bx(f"{name}_vx{i}", (x - 0.25, cy + 0.8, cz - RET_H * n_h / 2), (x + 0.25, cy + 1.0, cz + RET_H * n_h / 2), m["ip_reticle"], g))
    for j in range(n_h + 1):
        z = cz - RET_H * n_h / 2 + RET_H * j
        lines.append(bx(f"{name}_hz{j}", (cx - RET_W * n_w / 2, cy + 0.8, z - 0.25), (cx + RET_W * n_w / 2, cy + 1.0, z + 0.25), m["ip_reticle"], g))
    join(lines, f"{name}_lines")
    return g


def topdown_package(m, parent, c, w, h, n_dies, n_hbm, name, organic=False):
    """A package seen from above on its interposer: w x h mm slab, dies in the middle, HBM stacks
    (11 x 11 mm) down both long sides. Returns group."""
    g = empty(f"{name}_grp", parent)
    cx, cy, cz = c
    bx(f"{name}_slab", (cx - w / 2, cy, cz - h / 2), (cx + w / 2, cy + 1.6, cz + h / 2), m["ip_organic" if organic else "ip_si"], g)
    dw = min(26.0, (w - 4.0) / n_dies - 2.0)
    tot = n_dies * dw + (n_dies - 1) * 2.0
    parts = []
    for k in range(n_dies):
        x0 = cx - tot / 2 + k * (dw + 2.0)
        parts.append(bx(f"{name}_die{k}", (x0, cy + 1.6, cz - 16.5), (x0 + dw, cy + 3.6, cz + 16.5), m["ip_die"], g))
    per_side = n_hbm // 2
    for s in (-1, 1):
        for k in range(per_side):
            x0 = cx - per_side * 12.0 / 2 + k * 12.0
            z0 = cz + s * 19.0
            parts.append(bx(f"{name}_h{s}_{k}", (x0 + 0.5, cy + 1.6, z0), (x0 + 11.5, cy + 4.6, z0 + s * 11.0), m["ip_dram"], g))
    return g
