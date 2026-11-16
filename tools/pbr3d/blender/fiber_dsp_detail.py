"""Detailed part builders for the PAM4 DSP sections (fiber_dsp_sections.py).

The package is a real flip-chip BGA in cut-away: a layered board, BGA balls, a build-up substrate
with copper planes and vias, C4 bumps in underfill, the die (silicon over its metal stack) face
down, thermal paste, a hat-shaped steel lid on a sealant bead, and fins. The quadrant facing the
camera (x > 0, z > 0) is built into a separate group, so a scene can show the package whole and
then slide that quadrant away to open the cut faces.

Also: the laser driver chip, a TO-can laser cut open, the fibre in its ferrule, and a camera that
frames a box in the left pane (`frame`) and glides between beat poses (`glide`).

Units mm, Y up, camera on +z.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, box, cut, key, tube  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402
from sand_overview import fly, show  # noqa: E402

# ---- heights (mm, Y up). Thicknesses are drawn larger than life so each layer reads. --------
BOARD_Y0, BOARD_Y1 = -10.0, -7.0
BGA_R = 0.55
SUB_Y0, SUB_Y1 = -5.9, -3.9  # substrate: bottom build-up, core, top build-up
CORE_Y0, CORE_Y1 = -5.4, -4.4
DIE_Y0, DIE_Y1 = -3.1, -1.6  # die: metal stack (bottom, face down) then silicon
BEOL_Y1 = -2.8
TIM_Y1 = -1.3  # thermal paste on the die's back
LID_Y1 = 0.2  # lid plate top
FIN_Y1 = 4.2
SEAL_Y1 = -3.6  # sealant bead under the lid's skirt

SUB = (-15.0, -13.0, 15.0, 13.0)  # substrate x0, z0, x1, z1
DIE = (-8.0, -7.0, 8.0, 7.0)
LID = (-14.0, -12.0, 14.0, 12.0)
SKIRT = 1.0
BGA_PITCH = 2.5
BUMP_PITCH = 1.2
FIN_ZS = [2.2 * k for k in range(-5, 6)]
FIN_T = 0.8


def materials():
    m = {
        "board": mat("fib_board", (0.10, 0.34, 0.20), rough=0.7),
        "copper": mat("fib_copper", (0.80, 0.50, 0.30), metal=0.9, rough=0.3),
        "substrate": mat("fib_substrate", (0.42, 0.27, 0.15), rough=0.8),
        "die": mat("fib_die", (0.16, 0.18, 0.22), metal=0.3, rough=0.4),
        "steel": mat("fib_steel", (0.62, 0.65, 0.70), metal=0.8, rough=0.35),
        "dark_steel": mat("fib_dark_steel", (0.25, 0.27, 0.30), metal=0.7, rough=0.45),
        "gold": mat("fib_gold", (0.85, 0.70, 0.30), metal=0.9, rough=0.3),
        "oe": mat("fib_oe", (0.20, 0.40, 0.70), metal=0.4, rough=0.35),
        "glass": mat("fib_glass", (0.60, 0.80, 0.90), rough=0.1, alpha=0.2),
        "cladding": mat("fib_cladding", (0.70, 0.85, 0.95), rough=0.2, alpha=0.35),
        "light": mat("fib_light", (1.0, 0.35, 0.20), emit=(1.0, 0.35, 0.20), strength=8.0),
        "elec": mat("fib_elec", (0.30, 0.90, 1.00), emit=(0.20, 0.90, 1.00), strength=8.0),
        "cage": mat("fib_cage", (0.45, 0.48, 0.52), metal=0.6, rough=0.5, alpha=0.3),
    }
    m.update({
        "fr4": mat("d_fr4", (0.10, 0.34, 0.20), rough=0.7),
        "mask": mat("d_mask", (0.05, 0.22, 0.12), rough=0.5),
        "core": mat("d_core", (0.42, 0.27, 0.15), rough=0.8),
        "buildup": mat("d_buildup", (0.20, 0.24, 0.16), rough=0.6),
        "solder": mat("d_solder", (0.78, 0.79, 0.82), metal=0.9, rough=0.25),
        "underfill": mat("d_underfill", (0.30, 0.22, 0.12), rough=0.6),
        "silicon": mat("d_silicon", (0.20, 0.22, 0.30), metal=0.3, rough=0.35),
        "beol": mat("d_beol", (0.45, 0.32, 0.62), metal=0.4, rough=0.4),
        "paste": mat("d_paste", (0.80, 0.78, 0.70), rough=0.7),
        "seal": mat("d_seal", (0.12, 0.12, 0.13), rough=0.6),
        "lid": mat("d_lid", (0.66, 0.69, 0.74), metal=0.8, rough=0.3),
        "ceramic": mat("d_ceramic", (0.92, 0.91, 0.88), rough=0.4),
        "mold": mat("d_mold", (0.10, 0.10, 0.11), rough=0.6),
        "analog": mat("d_analog", (0.55, 0.45, 0.22), metal=0.5, rough=0.4),
        "logic": mat("d_logic", (0.16, 0.20, 0.30), metal=0.4, rough=0.4),
        "sram": mat("d_sram", (0.22, 0.34, 0.40), metal=0.4, rough=0.35),
        "hl": mat("d_hl", (1.0, 0.70, 0.25), rough=0.5, emit=(1.0, 0.62, 0.20), strength=3.0),
        "hl_eq": mat("d_hl_eq", (0.30, 0.90, 1.0), rough=0.5, emit=(0.25, 0.85, 1.0), strength=3.0),
        "lit_tx": mat("d_lit_tx", (1.0, 0.60, 0.20), emit=(1.0, 0.55, 0.15), strength=0.8, alpha=0.5),
        "lit_rx": mat("d_lit_rx", (0.30, 0.80, 1.0), emit=(0.25, 0.75, 1.0), strength=0.8, alpha=0.5),
        "path": mat("d_path", (0.30, 0.90, 1.00), emit=(0.20, 0.90, 1.00), strength=4.0),
        "noise": mat("d_noise", (1.0, 0.45, 0.15), emit=(1.0, 0.42, 0.12), strength=2.2),
        "fuzz": mat("d_fuzz", (0.38, 0.18, 0.08), rough=0.8, alpha=0.3),
        "heat": mat("d_heat", (1.0, 0.42, 0.12), emit=(1.0, 0.35, 0.08), strength=0.7, alpha=0.45),
        "hot": mat("d_hot", (1.0, 0.40, 0.12), emit=(1.0, 0.32, 0.06), strength=1.6),
        "air": mat("d_air", (0.70, 0.85, 1.0), emit=(0.60, 0.80, 1.0), strength=1.5, alpha=0.6),
        "screen": mat("d_screen", (0.04, 0.06, 0.08), rough=0.6),
        "grid": mat("d_grid", (0.20, 0.32, 0.36), rough=0.6),
        "rung": mat("d_rung", (0.70, 0.72, 0.76), metal=0.8, rough=0.35),
        "thresh": mat("d_thresh", (1.0, 0.35, 0.45), emit=(1.0, 0.30, 0.40), strength=2.5),
        "light1": mat("d_light1", (1.0, 0.35, 0.20), emit=(1.0, 0.35, 0.20), strength=1.5, alpha=0.5),
        "light2": mat("d_light2", (1.0, 0.35, 0.20), emit=(1.0, 0.35, 0.20), strength=4.0, alpha=0.7),
        "light3": mat("d_light3", (1.0, 0.40, 0.22), emit=(1.0, 0.40, 0.22), strength=9.0),
    })
    return m


# ---- the quadrant cut ------------------------------------------------------------------------


def lbox(name, lo, hi, mt, g, q=None, o=0.0):
    """A box with its (x > o, z > o) quadrant cut out. The quadrant goes to group `q` if given
    (so the whole part can be shown, then opened), else it is dropped. A small `o` puts an inner
    layer's cut faces just proud of the part around it, so they don't z-fight."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    if x1 <= o or z1 <= o:
        return [box(name, lo, hi, mt, g)]
    out = []
    if z0 < o:
        out.append(box(f"{name}_b", (x0, y0, z0), (x1, y1, o), mt, g))
    if x0 < o:
        out.append(box(f"{name}_f", (x0, y0, max(z0, o)), (o, y1, z1), mt, g))
    if q is not None:
        out.append(box(f"{name}_q", (max(x0, o), y0, max(z0, o)), (x1, y1, z1), mt, q))
    return out


def in_quad(x, z):
    return x > 1e-3 and z > 1e-3


# ---- the board and the package ---------------------------------------------------------------


def board(m, parent, x0=-26.0, x1=26.0, z0=-22.0, z1=22.0, name="board"):
    """A chunk of the host board: solder mask over FR-4 with two copper planes in its edge."""
    g = empty(name, parent)
    box(f"{name}_fr4", (x0, BOARD_Y0, z0), (x1, BOARD_Y1 - 0.15, z1), m["fr4"], g)
    box(f"{name}_mask", (x0, BOARD_Y1 - 0.15, z0), (x1, BOARD_Y1, z1), m["mask"], g)
    for k, y in enumerate((-9.1, -8.1)):
        box(f"{name}_plane{k}", (x0 - 0.02, y, z0 - 0.02), (x1 + 0.02, y + 0.22, z1 + 0.02), m["copper"], g)
    return g


def package(m, parent, quad=True):
    """The flip-chip DSP package, cut away. Returns a dict of groups:
    base (board-side parts that never move), bga, bumps, die, tim, lid (plate, skirt and fins),
    seal, and q (the removed quadrant, with its own lid part in q_lid)."""
    g = empty("package", parent)
    G = {k: empty(f"pkg_{k}", g) for k in ("base", "bga", "bumps", "die", "tim", "lid", "seal", "q", "q_lid")}
    q = G["q"] if quad else None
    ql = G["q_lid"] if quad else None
    sx0, sz0, sx1, sz1 = SUB
    # BGA balls on board pads, a 2.5 mm grid with a row on each cut face
    n = int(round(12.5 / BGA_PITCH))
    for i in range(-n, n + 1):
        for j in range(-n + 1, n):
            x, z = i * BGA_PITCH, j * BGA_PITCH
            tgt = q if in_quad(x, z) else G["bga"]
            if tgt is None:
                continue
            ball(f"bga_{i}_{j}", (x, BOARD_Y1 + BGA_R - 0.05, z), BGA_R, m["solder"], tgt, 10)
    # substrate: bottom build-up, core, top build-up, copper planes between
    lbox("sub_bot", (sx0, SUB_Y0, sz0), (sx1, CORE_Y0, sz1), m["buildup"], G["base"], q)
    lbox("sub_core", (sx0, CORE_Y0, sz0), (sx1, CORE_Y1, sz1), m["core"], G["base"], q)
    lbox("sub_top", (sx0, CORE_Y1, sz0), (sx1, SUB_Y1, sz1), m["buildup"], G["base"], q)
    for k, y in enumerate((-5.65, -4.2)):
        lbox(f"sub_cu{k}", (sx0 + 0.3, y, sz0 + 0.3), (sx1 - 0.3, y + 0.12, sz1 - 0.3), m["copper"], G["base"], None, 0.03)
    # plated vias through the core, half sunk in the cut faces
    for k, x in enumerate((2.5, 7.5, 12.5)):
        tube(f"via_x{k}", (x, SUB_Y0 + 0.1, 0.0), (x, SUB_Y1 - 0.1, 0.0), 0.28, m["copper"], G["base"], 10)
    for k, z in enumerate((2.5, 7.5, 10.0)):
        tube(f"via_z{k}", (0.0, SUB_Y0 + 0.1, z), (0.0, SUB_Y1 - 0.1, z), 0.28, m["copper"], G["base"], 10)
    # underfill under the die (a fillet a little wider than the die), C4 bumps on the cut faces
    dx0, dz0, dx1, dz1 = DIE
    lbox("underfill", (dx0 - 0.6, SUB_Y1, dz0 - 0.6), (dx1 + 0.6, DIE_Y0, dz1 + 0.6), m["underfill"], G["bumps"], q)
    pts = [(BUMP_PITCH * (k + 0.5), 0.0) for k in range(7)] + [(0.0, BUMP_PITCH * (k + 0.5)) for k in range(6)]
    for k, (x, z) in enumerate(pts):
        tube(f"pillar{k}", (x, -3.45, z), (x, DIE_Y0, z), 0.26, m["copper"], G["bumps"], 8)
        ball(f"c4_{k}", (x, -3.6, z), 0.33, m["solder"], G["bumps"], 10)
    # the die, face down: metal stack at the bottom, silicon above
    lbox("die_beol", (dx0, DIE_Y0, dz0), (dx1, BEOL_Y1, dz1), m["beol"], G["die"], q)
    lbox("die_si", (dx0, BEOL_Y1, dz0), (dx1, DIE_Y1, dz1), m["silicon"], G["die"], q)
    lbox("tim", (dx0 + 0.2, DIE_Y1, dz0 + 0.2), (dx1 - 0.2, TIM_Y1, dz1 - 0.2), m["paste"], G["tim"], q)
    # the hat lid: plate, skirt walls on a sealant bead, fins on top
    lx0, lz0, lx1, lz1 = LID
    lbox("lid_plate", (lx0, TIM_Y1, lz0), (lx1, LID_Y1, lz1), m["lid"], G["lid"], ql)
    walls = [((lx0, lz0), (lx0 + SKIRT, lz1)), ((lx1 - SKIRT, lz0), (lx1, lz1)),
             ((lx0 + SKIRT, lz0), (lx1 - SKIRT, lz0 + SKIRT)), ((lx0 + SKIRT, lz1 - SKIRT), (lx1 - SKIRT, lz1))]
    for k, ((a, b), (c, d)) in enumerate(walls):
        lbox(f"skirt{k}", (a, SEAL_Y1, b), (c, TIM_Y1, d), m["lid"], G["lid"], ql)
        lbox(f"seal{k}", (a - 0.1, SUB_Y1, b - 0.1), (c + 0.1, SEAL_Y1, d + 0.1), m["seal"], G["seal"], q)
    for k, z in enumerate(FIN_ZS):
        lbox(f"fin{k}", (lx0 + 0.6, LID_Y1, z - FIN_T / 2), (lx1 - 0.6, FIN_Y1, z + FIN_T / 2), m["lid"], G["lid"], ql)
    return G


# ---- the laser driver, the TO-can laser and the fibre ----------------------------------------

AXIS_Y = -3.5  # the laser and fibre axis height


def driver(m, parent, x0, x1, zc, name="drv", arched=False):
    """A small QFN laser driver: moulded body with its top cut back to show the die and bond wires,
    tin leads round the edge."""
    g = empty(name, parent)
    w = (x1 - x0) / 2
    xc = (x0 + x1) / 2
    box(f"{name}_pad", (xc - w + 0.3, BOARD_Y1, zc - w + 0.3), (xc + w - 0.3, BOARD_Y1 + 0.2, zc + w - 0.3), m["copper"], g)
    body = box(f"{name}_body", (x0, BOARD_Y1 + 0.2, zc - w), (x1, -5.2, zc + w), m["mold"], g)
    cut(body, zc)
    box(f"{name}_die", (xc - 1.4, BOARD_Y1 + 0.3, zc - 1.4), (xc + 1.4, -6.1, zc + 0.05), m["silicon"], g)
    for k in range(4):
        x = x0 + 0.6 + k * (2 * w - 1.2) / 3
        box(f"{name}_lead_s{k}", (x - 0.25, BOARD_Y1, zc - w - 0.3), (x + 0.25, BOARD_Y1 + 0.35, zc - w + 0.2), m["solder"], g)
    for side, xe in ((-1, x0), (1, x1)):
        for k, z in enumerate((zc - 1.6, zc - 0.5)):
            box(f"{name}_lead_{side}_{k}", (xe - 0.3 if side > 0 else xe - 0.2, BOARD_Y1, z - 0.25),
                (xe + 0.2 if side > 0 else xe + 0.3, BOARD_Y1 + 0.35, z + 0.25), m["solder"], g)
            if not arched:
                tube(f"{name}_wire_{side}_{k}", (xc + side * 1.3, -6.1, zc + 0.08), (xe - side * 0.4, -6.5 + 0.3 * k, zc + 0.08),
                     0.07, m["gold"], g, 6)
    if arched:
        for k, pts in enumerate(driver_wires(x0, x1, zc)):
            wire(f"{name}_wire{k}", pts, 0.06, m["gold"], g)
    return g


def laser(m, parent, hx, zc, name="laser"):
    """A TO-can laser lying along +x, cut open on its axis: gold header with leads into the board,
    steel cap, a chip on a submount on the header post, a ball lens in the cap's nose."""
    g = empty(name, parent)
    y = AXIS_Y
    box(f"{name}_mount", (hx + 1.5, BOARD_Y1, zc - 1.8), (hx + 5.5, y - 2.4, zc + 1.8), m["steel"], g)
    hdr = tube(f"{name}_header", (hx, y, zc), (hx + 1.0, y, zc), 3.2, m["gold"], g, 32)
    cut(hdr, zc)
    cap = tube(f"{name}_cap", (hx + 1.0, y, zc), (hx + 6.0, y, zc), 2.5, m["steel"], g, 32)
    # hollow the cap: an inner cylinder in a darker material reads as the cavity on the cut face
    cut(cap, zc + 0.01)
    cav = tube(f"{name}_cavity", (hx + 1.0, y, zc), (hx + 5.6, y, zc), 2.1, m["seal"], g, 32)
    cut(cav, zc + 0.03)
    box(f"{name}_post", (hx + 1.0, y - 1.6, zc - 1.0), (hx + 3.6, y - 0.6, zc + 0.04), m["gold"], g)
    box(f"{name}_submount", (hx + 2.2, y - 0.6, zc - 0.8), (hx + 3.6, y - 0.3, zc + 0.05), m["ceramic"], g)
    chip = box(f"{name}_chip", (hx + 2.4, y - 0.3, zc - 0.5), (hx + 3.6, y + 0.1, zc + 0.06), m["die"], g)
    lens = ball(f"{name}_lens", (hx + 5.2, y, zc), 0.9, m["glass"], g, 16)
    for k, dz in enumerate((-1.2, 0.0, 1.2)):
        tube(f"{name}_pin{k}", (hx, y + dz * 0.4 - 0.6, zc + dz), (hx - 2.5, y + dz * 0.4 - 0.6, zc + dz), 0.18, m["gold"], g, 8)
        tube(f"{name}_pin{k}_dn", (hx - 2.5, y + dz * 0.4 - 0.6, zc + dz), (hx - 2.5, BOARD_Y1, zc + dz), 0.18, m["gold"], g, 8)
    return g, chip, lens


def fibre(m, parent, x0, x1, zc, name="fibre"):
    """The fibre from its ferrule: a white ceramic ferrule in a steel sleeve, then the jacketed
    fibre, all cut on the axis so the glass core shows. Returns (group, core start x)."""
    g = empty(name, parent)
    y = AXIS_Y
    sl = tube(f"{name}_sleeve", (x0, y, zc), (x0 + 6.0, y, zc), 1.9, m["steel"], g, 24)
    cut(sl, zc)
    fe = tube(f"{name}_ferrule", (x0, y, zc), (x0 + 7.5, y, zc), 1.25, m["ceramic"], g, 24)
    cut(fe, zc + 0.02)
    jk = tube(f"{name}_jacket", (x0 + 7.5, y, zc), (x1, y, zc), 1.1, m["cage"], g, 24)
    cut(jk, zc)
    cl = tube(f"{name}_clad", (x0, y, zc), (x1, y, zc), 0.62, m["cladding"], g, 20)
    cut(cl, zc + 0.04)
    box(f"{name}_mount", (x0 + 1.0, BOARD_Y1, zc - 1.6), (x0 + 5.0, y - 1.9, zc + 1.6), m["steel"], g)
    return g


# ---- arched wires with beads riding them --------------------------------------------------------


def arch(a, b, h, n=8):
    """Points on an arch from a to b (same z), rising h above the higher end at its middle."""
    top = max(a[1], b[1]) + h
    pts = []
    for i in range(n + 1):
        t = i / n
        x = a[0] + (b[0] - a[0]) * t
        z = a[2] + (b[2] - a[2]) * t
        base = a[1] + (b[1] - a[1]) * t
        y = base + 4 * t * (1 - t) * (top - (a[1] + b[1]) / 2)
        pts.append((x, y, z))
    return pts


def wire(name, pts, r, mt, parent):
    """A wire through `pts`: a tube per segment, a ball at each joint so it reads as one piece."""
    g = empty(name, parent)
    for k in range(len(pts) - 1):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, mt, g, 8)
        if k:
            ball(f"{name}_j{k}", pts[k], r, mt, g, 8)
    return g


def run(parent, name, pts, n, size, mt, b, u0, u1, life):
    """`n` glowing beads that each travel the absolute polyline `pts` over `life` frames, launched one
    after another between fractions u0 and u1 of beat `b`."""
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, mt, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, len(pts) * 2))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


def driver_wires(x0, x1, zc):
    """The arched bond wires of a driver built by driver(..., arched=True): die pad to lead, each a
    point list on the cut face, input side (x0) first."""
    xc = (x0 + x1) / 2
    out = []
    for side, xe in ((-1, x0), (1, x1)):
        for k in range(2):
            a = (xc + side * 1.2, -6.1, zc + 0.1 + 0.05 * k)
            b = (xe - side * 0.25, -6.6, zc + 0.1 + 0.05 * k)
            pts = arch(a, b, 0.45 + 0.15 * k)
            out.append(pts if side > 0 else pts[::-1])
    return out


def laser_wire(hx, zc):
    """The laser's bond wire, from the header post up over to the chip's top, on the cut face."""
    y = AXIS_Y
    return arch((hx + 1.3, y - 0.6, zc + 0.08), (hx + 3.0, y + 0.1, zc + 0.08), 0.6)


# ---- the camera ------------------------------------------------------------------------------

HALF_H = 0.266  # tan of half the vertical field of view (0.52 rad)
HALF_W = 0.29  # the left pane is a little wider than tall


def frame(lo, hi, yaw, pitch, fill=0.86):
    """The (target, distance, yaw, pitch) pose that fits the box lo..hi in the left pane, seen
    from (yaw, pitch). Exact for a pinhole camera aimed at the box centre."""
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    e = (cp * sy, sp, cp * cy)  # toward the eye
    r = (cy, 0.0, -sy)
    u = (-sp * sy, cp, -sp * cy)
    d = 0.0
    for X in (lo[0], hi[0]):
        for Y in (lo[1], hi[1]):
            for Z in (lo[2], hi[2]):
                v = (X - c[0], Y - c[1], Z - c[2])
                de = sum(v[i] * e[i] for i in range(3))
                a = abs(sum(v[i] * r[i] for i in range(3)))
                b = abs(sum(v[i] * u[i] for i in range(3)))
                d = max(d, de + a / (HALF_W * fill), de + b / (HALF_H * fill))
    return (tuple(c), d, yaw, pitch)


def glide(root, poses, glide_u=0.3):
    """One pose per beat. Beat 0 holds its pose from the start; later beats ease in from the
    previous pose over the first `glide_u` of the beat, then hold with a slow push-in."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        cp, sp = math.cos(pitch), math.sin(pitch)
        a = F(i, 0) if i == 0 else F(i, glide_u)
        b = F(i + 1, 0) - 1
        for f, d in ((a, dist * 1.03), (b, dist * 0.97)):
            e = (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))
            key(target, f, "location", P(*t))
            key(eye, f, "location", P(*e))
