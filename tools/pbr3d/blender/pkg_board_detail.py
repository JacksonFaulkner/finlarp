"""Part kit for the PACKAGING tab's BOARD page (pkg_board_*.py).

One GPU module, drawn far larger than life and cut through its middle along z = 0 (the camera sits
on +z), so the cut face shows every layer from the board to the cold plate. Units: Y up, x across,
z toward the camera. Heights are stretched so thin layers read.

  board      a multilayer PCB: solder mask, signal copper, ground, a thick power plane, ground,
             back mask; plated vias under the package; MLCC decoupling caps on the back side;
             a steel bolster plate and four load screws.
  package    BGA balls (half balls on the cut face) on copper pads, an organic substrate (ABF
             build-up layers with copper traces, a glass-fibre core with plated through-holes),
             C4 bumps, a silicon interposer with TSVs and an RDL, microbumps, two GPU dies and
             four HBM stacks (eight DRAM layers on a base die), underfill fillets and mould.
  lid        a nickel-plated copper lid glued to the substrate, TIM1 under it, TIM2 above it.
  cold plate a copper base with skived fins, a cover, an inlet and outlet at the back.
  vrm        power stages and inductors down both sides, output caps beside the package.
  nvlink     a high-speed connector at the right edge; traces in the board; twinax cables.
  tray       (far above, at TRAY_Y) a compute tray: four modules, NVLink cables to a switch tray,
             coolant manifolds; `rack` stacks trays into a rack.
  column     (at BY) one vertical slice through the stack at 4x: the anatomy close-up.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O  # noqa: E402
from sand_overview import F, P, empty, show, tube, mat, cut, label, beat, key  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, join, run, rise, present, blink, frame, camera_path  # noqa: E402,F401

# ---- materials ------------------------------------------------------------------------------


def materials():
    m = D.materials()
    m.update({
        "abf": mat("bd_abf", (0.20, 0.24, 0.17), rough=0.7),
        "core": mat("bd_core", (0.66, 0.60, 0.40), rough=0.8),
        "pad": mat("bd_pad", (0.90, 0.75, 0.36), metal=0.95, rough=0.25),
        "underfill": mat("bd_underfill", (0.34, 0.27, 0.16), rough=0.7),
        "tim": mat("bd_tim", (0.62, 0.66, 0.72), metal=0.5, rough=0.45),
        "tim2": mat("bd_tim2", (0.85, 0.82, 0.70), rough=0.6),
        "lid": mat("bd_lid", (0.74, 0.73, 0.70), metal=0.9, rough=0.28),
        "glue": mat("bd_glue", (0.22, 0.22, 0.24), rough=0.8),
        "plate": mat("bd_plate", (0.80, 0.50, 0.32), metal=0.9, rough=0.3),
        "cover": mat("bd_cover", (0.55, 0.58, 0.62), metal=0.8, rough=0.35),
        "steel": mat("bd_steel", (0.45, 0.47, 0.50), metal=0.85, rough=0.4),
        "conn": mat("bd_conn", (0.10, 0.10, 0.11), rough=0.6),
        "cable": mat("bd_cable", (0.10, 0.28, 0.32), rough=0.5),
        "hose": mat("bd_hose", (0.12, 0.14, 0.18), rough=0.6),
        "hose_cold": mat("bd_hose_c", (0.16, 0.36, 0.70), rough=0.5),
        "hose_hot": mat("bd_hose_h", (0.70, 0.26, 0.14), rough=0.5),
        "mould": mat("bd_mould", (0.12, 0.12, 0.13), rough=0.6),
        "rack": mat("bd_rack", (0.18, 0.19, 0.22), metal=0.6, rough=0.5),
        "ghost": mat("bd_ghost", (0.45, 0.30, 0.18), rough=0.8, alpha=0.22),
        "ghost_si": mat("bd_ghost_si", (0.36, 0.40, 0.46), metal=0.4, rough=0.5, alpha=0.22),
        "ghost_lid": mat("bd_ghost_lid", (0.74, 0.73, 0.70), metal=0.6, rough=0.4, alpha=0.25),
        "sig": mat("bd_sig", (0.30, 0.95, 0.85), emit=(0.20, 0.95, 0.85), strength=5.0),
        "warp": mat("bd_warp", (1.0, 0.25, 0.25), emit=(1.0, 0.2, 0.2), strength=1.5),
        "cool_glow": mat("bd_coolglow", (0.30, 0.65, 1.0), emit=(0.25, 0.60, 1.0), strength=1.2, alpha=0.75),
    })
    return m


# ---- layout -----------------------------------------------------------------------------------

BX0, BX1, BZ0 = -170.0, 170.0, -150.0  # board extents (front edge at z = 0)
# board layers (y bands), top down
Y_MASK = (-0.6, 0.0)
Y_SIG1 = (-1.4, -0.6)
Y_D1 = (-3.0, -1.4)
Y_GND1 = (-4.0, -3.0)
Y_D2 = (-5.6, -4.0)
Y_PWR = (-8.0, -5.6)
Y_D3 = (-9.6, -8.0)
Y_GND2 = (-10.6, -9.6)
Y_D4 = (-13.2, -10.6)
Y_MASKB = (-14.0, -13.2)
BOT = -14.0
PWR_Y = -6.8
SIG_Y = -1.0

BGA = (0.0, 3.0)  # balls between board and substrate
BGA_R = 1.45
BGA_PITCH = 4.0
SUB_X = 56.0
SUB_BU0 = (3.0, 5.8)  # bottom build-up
SUB_CORE = (5.8, 10.2)
SUB_BU1 = (10.2, 13.0)  # top build-up
C4 = (13.0, 14.6)
IP_X = 46.0
IP = (14.6, 18.4)
RDL = (18.4, 19.4)
UB = (19.4, 20.2)
DIE = (20.2, 27.0)
DIES = ((-27.0, -1.0), (1.0, 27.0))
HBM_XS = ((-44.0, -31.0), (31.0, 44.0))
HBM_ZS = ((-22.0, -4.0),)  # the cut runs through one stack each side (another sits behind)
TIM1 = (27.0, 27.8)
LID = (27.8, 31.0)
LID_X = 52.0
TIM2 = (31.0, 31.8)
PLATE = (31.8, 34.6)
FINS = (34.6, 41.0)
COVER = (41.0, 43.4)
PLATE_X = 50.0
PKG_Z = -56.0
PWR_XS = (-36.0, -20.0, 20.0, 36.0)  # columns the power climbs
SIG_X = 24.0  # a signal column to the NVLink connector
CONN = (128.0, 156.0)
PH_X = (78.0, 118.0)  # VRM phases (right side; left mirrors)
PH_Z = (-10.0, -36.0, -62.0, -88.0)
BY = 300.0  # close-up column height
TRAY_Y = 700.0  # tray and rack height


def sx(side, x):
    return -x if side < 0 else x


def halfballs(name, centres, r, m, parent, segs=10):
    """Many spheres as one mesh, cut at z = 0 so the front row shows half balls."""
    bm = bmesh.new()
    for c in centres:
        bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r, matrix=Matrix.Translation(P(*c)))
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    cut(o)
    return o


def grid(x0, x1, z0, pitch):
    xs = []
    x = x0
    while x <= x1 + 1e-6:
        xs.append(x)
        x += pitch
    zs = []
    z = 0.0
    while z >= z0 - 1e-6:
        zs.append(z)
        z -= pitch
    return [(a, b) for a in xs for b in zs]


def columns(name, xs, y0, y1, w, m, parent, d=None):
    """Half columns on the cut face (vias, PTHs, TSVs) at each x, from y0 to y1, as one mesh."""
    d = w if d is None else d
    objs = [bx(f"{name}_{k}", (x - w / 2, y0, -d), (x + w / 2, y1, 0.08), m, parent) for k, x in enumerate(xs)]
    return join(objs, name)


# ---- board --------------------------------------------------------------------------------------


def board(m, parent, ghost=False):
    g = empty("board", parent)
    lay = [(Y_MASK, "mask"), (Y_SIG1, "fr4"), (Y_D1, "fr4"), (Y_GND1, "gnd"), (Y_D2, "fr4"), (Y_PWR, "plane08"),
           (Y_D3, "fr4"), (Y_GND2, "gnd"), (Y_D4, "fr4"), (Y_MASKB, "mask")]
    for k, (y, mn) in enumerate(lay):
        bx(f"bl{k}", (BX0, y[0], BZ0), (BX1, y[1], 0.0), m["ghost" if ghost and mn == "fr4" else mn], g)
    # signal copper on the cut face: traces in the top layer (stripes)
    tr = [bx(f"tr{k}", (x, Y_SIG1[0], -0.8), (x + 3.0, Y_SIG1[1], 0.08), m["copper"], g)
          for k, x in enumerate(range(-160, 160, 7)) if abs(x) > 60]
    join(tr, "traces")
    # NVLink traces: a long strip on the right in the signal layer
    bx("nvl_trace", (SUB_X - 4.0, Y_SIG1[0], -1.6), (CONN[0], Y_SIG1[1], -0.4), m["copper"], g)
    # vias under the package (through every layer), on the ball pitch
    xs = [x for x in [-52.0 + 4.0 * k for k in range(27)]]
    columns("vias", xs, BOT, 0.0, 1.2, m["copper"], g)
    return g


def backside(m, parent):
    g = empty("backside", parent)
    caps = []
    for k, x in enumerate([-44.0 + 8.0 * i for i in range(12)]):
        for j, z in enumerate((-3.0, -15.0, -27.0, -39.0)):
            caps.append(bx(f"mlcc{k}_{j}", (x - 2.4, BOT - 2.0, z - 1.6), (x + 2.4, BOT, z + 1.6), m["mlcc"], g))
            caps.append(bx(f"mlce{k}_{j}", (x - 2.4, BOT - 2.05, z - 1.65), (x - 1.6, BOT, z + 1.65), m["mlcc_end"], g))
            caps.append(bx(f"mlcf{k}_{j}", (x + 1.6, BOT - 2.05, z - 1.65), (x + 2.4, BOT, z + 1.65), m["mlcc_end"], g))
    for o in caps:
        cut(o)
    join(caps, "mlccs")
    # bolster plate (a window for the caps) and load screws
    bx("bolster_l", (-80.0, BOT - 5.0, -80.0), (-52.0, BOT - 1.0, 0.0), m["steel"], g)
    bx("bolster_r", (52.0, BOT - 5.0, -80.0), (80.0, BOT - 1.0, 0.0), m["steel"], g)
    bx("bolster_b", (-80.0, BOT - 5.0, -80.0), (80.0, BOT - 1.0, -56.0), m["steel"], g)
    for k, x in enumerate((-66.0, 66.0)):
        tube(f"screw{k}", (x, BOT - 5.0, -68.0), (x, COVER[1] + 2.0, -68.0), 1.6, m["steel"], g, 12)
        O.disc(f"spring{k}", (x, COVER[1] + 1.0, -68.0), 3.0, 2.0, m["steel"], g, 24)
    return g


# ---- package ------------------------------------------------------------------------------------


def bga(m, parent):
    g = empty("bga", parent)
    cs = [(x, (BGA[0] + BGA[1]) / 2, z) for x, z in grid(-52.0, 52.0, -52.0, BGA_PITCH)]
    halfballs("balls", cs, BGA_R, m["solder"], g)
    pads = []
    for k, x in enumerate([-52.0 + 4.0 * i for i in range(27)]):
        pads.append(bx(f"bp{k}", (x - 1.3, BGA[0], -1.3), (x + 1.3, BGA[0] + 0.3, 0.08), m["pad"], g))
        pads.append(bx(f"sp{k}", (x - 1.3, BGA[1] - 0.3, -1.3), (x + 1.3, BGA[1], 0.08), m["pad"], g))
    join(pads, "bga_pads")
    return g


def substrate(m, parent, ghost=False):
    g = empty("substrate", parent)
    ab = m["ghost"] if ghost else m["abf"]
    core = m["ghost"] if ghost else m["core"]
    parts = []
    for name, (y0, y1) in (("bu0", SUB_BU0), ("bu1", SUB_BU1)):
        n = 4
        h = (y1 - y0) / n
        for k in range(n):
            a = y0 + h * k
            parts.append(bx(f"{name}_d{k}", (-SUB_X, a, PKG_Z), (SUB_X, a + h, 0.0), ab, g))
            # copper lines in each build-up layer on the cut face
            for j, x in enumerate(range(-52, 52, 5)):
                if (j + k) % 3:
                    parts.append(bx(f"{name}_c{k}_{j}", (x, a + h * 0.65, -0.6), (x + 3.0, a + h, 0.08), m["copper"], g))
            # stacked microvias at the power and signal columns
            for j, x in enumerate(PWR_XS + (SIG_X, -SIG_X)):
                parts.append(bx(f"{name}_mv{k}_{j}", (x - 0.7, a, -0.7), (x + 0.7, a + h, 0.08), m["copper"], g))
    join(parts, "buildup")
    bx("core", (-SUB_X, SUB_CORE[0], PKG_Z), (SUB_X, SUB_CORE[1], 0.0), core, g)
    # glass weave in the core: thin pale bands
    gl = [bx(f"weave{k}", (-SUB_X, y, -0.3), (SUB_X, y + 0.25, 0.08), m["ink"], g) for k, y in enumerate((6.8, 8.0, 9.2))]
    join(gl, "weave")
    # plated through-holes: copper barrels with a dark plug
    pth = [x for x in (-48.0, -36.0, -28.0, -20.0, -12.0, 12.0, 20.0, 28.0, 36.0, 48.0)]
    columns("pth", pth, SUB_CORE[0], SUB_CORE[1], 2.6, m["copper"], g)
    columns("pth_plug", pth, SUB_CORE[0], SUB_CORE[1], 1.4, m["mould"], g, d=1.5)
    return g


def interposer(m, parent, ghost=False):
    g = empty("interposer", parent)
    si = m["ghost_si"] if ghost else m["silicon"]
    bx("ip", (-IP_X, IP[0], -44.0), (IP_X, IP[1], 0.0), si, g)
    xs = [-44.0 + 2.0 * k for k in range(45)]
    halfballs("c4", [(x, (C4[0] + C4[1]) / 2, z) for x in xs for z in (0.0, -2.0, -4.0, -6.0)], 0.75, m["solder"], g, 8)
    columns("tsv", [x for x in xs if int(x) % 4 == 0], IP[0], IP[1], 0.7, m["copper"], g)
    rd = [bx("rdl", (-IP_X, RDL[0], -44.0), (IP_X, RDL[1], 0.0), m["abf"], g)]
    for k in range(3):
        y = RDL[0] + 0.2 + 0.3 * k
        for j, x in enumerate(range(-44, 44, 3)):
            if (j + k) % 2:
                rd.append(bx(f"rdl_c{k}_{j}", (x, y, -0.5), (x + 2.2, y + 0.15, 0.08), m["copper"], g))
    join(rd, "rdl_all")
    # underfill under the interposer: a fillet ring
    bx("uf_c4", (-IP_X - 2.0, C4[0], -46.0), (IP_X + 2.0, C4[1], 0.0), m["underfill"], g)
    return g


def dies(m, parent, hot=False):
    g = empty("dies", parent)
    for k, (x0, x1) in enumerate(DIES):
        bx(f"die{k}", (x0, DIE[0], -30.0), (x1, DIE[1], 0.0), m["die_hot" if hot else "die"], g)
        bx(f"die_be{k}", (x0, DIE[0], -30.0), (x1, DIE[0] + 0.6, 0.08), m["gold"], g)  # metal stack
    ub = [(x, (UB[0] + UB[1]) / 2, z) for x in [-44.0 + 1.0 * k for k in range(89)] for z in (0.0, -1.0)]
    halfballs("ubumps", ub, 0.38, m["solder"], g, 6)
    bx("uf_ub", (-45.0, UB[0], -32.0), (45.0, UB[1], 0.0), m["underfill"], g)
    for k, (x0, x1) in enumerate(HBM_XS):
        bx(f"hbm_base{k}", (x0, UB[1], -22.0), (x1, UB[1] + 0.8, 0.0), m["fet"], g)
        n = 8
        h = (DIE[1] - UB[1] - 0.8) / n
        for j in range(n):
            y = UB[1] + 0.8 + h * j
            bx(f"hbm{k}_{j}", (x0, y, -22.0), (x1, y + h * 0.82, 0.0), m["hbm_dram"], g)
            bx(f"hbm{k}_{j}b", (x0, y + h * 0.82, -22.0), (x1, y + h, 0.0), m["hbm"], g)
        columns(f"hbm_tsv{k}", [x0 + 3.0 + 2.0 * i for i in range(4)], UB[1], DIE[1], 0.5, m["copper"], g)
    bx("mould_mid", (-31.0, UB[1], -22.0), (-27.0, DIE[1], 0.08), m["mould"], g)
    bx("mould_mid2", (27.0, UB[1], -22.0), (31.0, DIE[1], 0.08), m["mould"], g)
    return g


def lid(m, parent, ghost=False):
    g = empty("lid", parent)
    lm = m["ghost_lid"] if ghost else m["lid"]
    bx("tim1", (-44.0, TIM1[0], -30.0), (44.0, TIM1[1], 0.0), m["tim"], g)
    bx("lid_top", (-LID_X, LID[0], PKG_Z + 2.0), (LID_X, LID[1], 0.0), lm, g)
    for k, s in enumerate((-1, 1)):
        bx(f"lid_leg{k}", (s * (LID_X - 4.0), SUB_BU1[1] + 0.6, PKG_Z + 2.0), (s * LID_X, LID[0], 0.0), lm, g)
        bx(f"glue{k}", (s * (LID_X - 4.0), SUB_BU1[1], PKG_Z + 2.0), (s * LID_X, SUB_BU1[1] + 0.6, 0.0), m["glue"], g)
    bx("lid_back", (-LID_X, SUB_BU1[1] + 0.6, PKG_Z + 2.0), (LID_X, LID[0], PKG_Z + 6.0), lm, g)
    return g


def cold_plate(m, parent, ghost_cover=False):
    g = empty("cold_plate", parent)
    bx("tim2", (-PLATE_X, TIM2[0], -50.0), (PLATE_X, TIM2[1], 0.0), m["tim2"], g)
    bx("plate_base", (-PLATE_X - 14.0, PLATE[0], -70.0), (PLATE_X + 14.0, PLATE[1], 0.0), m["plate"], g)
    fins = [bx(f"fin{k}", (x - 0.5, FINS[0], -50.0), (x + 0.5, FINS[1], 0.0), m["plate"], g)
            for k, x in enumerate([-40.0 + 2.5 * i for i in range(33)])]
    join(fins, "fins")
    cv = m["ghost_lid"] if ghost_cover else m["cover"]
    bx("cover_top", (-PLATE_X - 14.0, FINS[1], -70.0), (PLATE_X + 14.0, COVER[1], 0.0), cv, g)
    for k, s in enumerate((-1, 1)):
        bx(f"cover_side{k}", (s * 42.0, FINS[0], -70.0), (s * (PLATE_X + 14.0), FINS[1], 0.0), cv, g)
    for k, (x, hm) in enumerate(((-22.0, "hose_cold"), (22.0, "hose_hot"))):
        tube(f"port{k}", (x, COVER[1], -60.0), (x, COVER[1] + 8.0, -60.0), 3.4, m["steel"], g, 16)
        D.polyline(f"hose{k}", [(x, COVER[1] + 8.0, -60.0), (x, COVER[1] + 22.0, -70.0), (x, COVER[1] + 24.0, -150.0)], 3.0, m[hm], g)
    return g


def vrm(m, parent):
    g = empty("vrm", parent)
    parts = []
    for side in (-1, 1):
        for k, z in enumerate(PH_Z):
            a, b = sx(side, PH_X[0]), sx(side, PH_X[0] + 12.0)
            parts.append(bx(f"st{side}{k}", (a, 0.0, z - 6.0), (b, 3.0, z + 6.0), m["mold"], g))
            c, d = sx(side, PH_X[0] + 16.0), sx(side, PH_X[1])
            parts.append(bx(f"in{side}{k}", (c, 0.0, z - 9.0), (d, 14.0, z + 9.0), m["ferrite"], g))
            parts.append(bx(f"ins{side}{k}", (c, 14.0, z - 3.0), (d, 14.6, z + 3.0), m["copper"], g))
            for j in range(3):
                e = sx(side, 64.0 - 4.0 * j)
                parts.append(bx(f"oc{side}{k}{j}", (e - 1.2, 0.0, z - 2.5), (e + 1.2, 2.4, z + 2.5), m["mlcc"], g))
    for o in parts:
        cut(o)
    join(parts, "phases")
    bx("ctrl", (-14.0, 0.0, -130.0), (14.0, 2.0, -112.0), m["dark"], g)
    return g


def nvlink(m, parent):
    g = empty("nvlink", parent)
    bx("conn", (CONN[0], 0.0, -70.0), (CONN[1], 12.0, 0.0), m["conn"], g)
    pins = [bx(f"pin{k}", (CONN[0] + 2.0 + 3.0 * k, 2.0, -0.8), (CONN[0] + 3.4 + 3.0 * k, 10.0, 0.08), m["gold"], g) for k in range(8)]
    join(pins, "pins")
    for k, z in enumerate((-12.0, -30.0, -48.0)):
        D.polyline(f"twinax{k}", [(CONN[1], 7.0, z), (CONN[1] + 20.0, 10.0, z), (BX1 + 40.0, 18.0, z - 10.0)], 2.2, m["cable"], g)
    return g


# ---- whole module -------------------------------------------------------------------------------


def module(m, root, ghost=False, extras=True):
    """Every part as its own direct child of root (so a scene can show or present each)."""
    s = {}
    for name, fn in (("board", board), ("bga", bga), ("sub", substrate), ("ip", interposer)):
        g = empty(f"{name}_grp", root)
        fn(m, g)
        s[name] = g
    for name, fn in (("dies", dies), ("lid", lid), ("plate", cold_plate)):
        g = empty(f"{name}_grp", root)
        fn(m, g)
        s[name] = g
    g = empty("dies_hot_grp", root)
    dies(m, g, hot=True)
    present(g, [])
    s["dies_hot"] = g
    if extras:
        for name, fn in (("back", backside), ("vrm", vrm), ("nvl", nvlink)):
            g = empty(f"{name}_grp", root)
            fn(m, g)
            s[name] = g
    # see-through twins for power and heat views
    for name, fn in (("sub_ghost", substrate), ("ip_ghost", interposer), ("lid_ghost", lid)):
        g = empty(f"{name}_grp", root)
        fn(m, g, ghost=True)
        present(g, [])
        s[name] = g
    g = empty("plate_ghost_grp", root)
    cold_plate(m, g, ghost_cover=True)
    present(g, [])
    s["plate_ghost"] = g
    return s


def swap(s, solid, ghost, intervals, total):
    """Show `ghost` instead of `solid` during intervals (both groups present()-driven)."""
    present(s[ghost], intervals)
    rest, t = [], 0
    for a, b in sorted(intervals):
        if a > t:
            rest.append((t, a))
        t = b
    if t < total:
        rest.append((t, total))
    present(s[solid], rest)


# ---- bead paths -------------------------------------------------------------------------------


def power_path(side, k=0):
    """From one phase's inductor down into the power plane, along it, up a via, a ball, a PTH,
    microvias, a C4 bump, a TSV and a microbump into the die."""
    z = PH_Z[k]
    x = sx(side, 36.0 if k % 2 == 0 else 20.0)
    xi = sx(side, PH_X[0] + 26.0)
    return [(xi, 14.0, z), (xi, 2.0, z), (xi, PWR_Y, z * 0.5), (x, PWR_Y, 0.4), (x, BGA[1], 0.4), (x, SUB_CORE[1], 0.4),
            (x, C4[1], 0.4), (x * 0.95, IP[1], 0.4), (x * 0.6 if abs(x) > 30 else x, DIE[0] + 2.0, 0.4)]


def signal_path():
    return [(SIG_X - 10.0, DIE[0] + 1.0, 0.4), (SIG_X, UB[0], 0.4), (SIG_X, IP[0], 0.4), (SIG_X + 8.0, C4[0], 0.4),
            (SIG_X + 8.0, SUB_BU1[0], 0.4), (SIG_X + 8.0, SUB_CORE[0], 0.4), (52.0, BGA[1], 0.4), (52.0, SIG_Y, 0.4),
            (CONN[0], SIG_Y, 0.4), (CONN[0] + 6.0, 7.0, 0.4), (CONN[1], 7.0, -12.0), (BX1 + 40.0, 18.0, -22.0)]


def heat_path(x):
    return [(x, DIE[1] - 1.0, 0.6), (x, LID[1], 0.6), (x, PLATE[1], 0.6), (x * 1.05, FINS[1] - 1.0, 0.6)]


def coolant_path(x):
    return [(x, (FINS[0] + FINS[1]) / 2, -50.0), (x, (FINS[0] + FINS[1]) / 2, 0.6)]


def heat(m, root, name, beats, n=10, u0=0.05, u1=0.85, size=1.7):
    xs = [-22.0, -10.0, 0.0, 10.0, 22.0, -16.0, 16.0, -4.0, 4.0, 26.0]
    for k in range(n):
        run(root, f"{name}{k}", heat_path(xs[k % len(xs)]), 1, size, m["heat"], beats, u0 + (u1 - u0) * k / max(1, n - 1), u1, 50)


def coolant(m, root, name, beats, n=12):
    for k, x in enumerate([-38.75 + 5.0 * i for i in range(16)][:n]):
        run(root, f"{name}{k}", coolant_path(x), 3, 1.0, m["cool"], beats, 0.02 + 0.01 * k, 0.85, 60)


def power(m, root, name, beats, sides=(-1, 1), ks=(0, 1), n=5, size=1.7):
    for side in sides:
        for k in ks:
            run(root, f"{name}{side}{k}", power_path(side, k), n, size, m["amp"], beats, 0.02 + 0.06 * k, 0.8, 70)


# ---- column close-up at BY (one slice through the stack, scaled) -------------------------------


def column(m, parent, s=4.0, x0=0.0):
    """One BGA ball's column from the power plane to the fins, `s` times larger, centred at x0, BY.
    Returns tag points."""
    g = empty("column", parent)

    def Y(y):
        return BY + y * s

    w = 7.0 * s  # half width
    pts = {}
    lay = [((Y_MASK), "mask"), (Y_SIG1, "fr4"), (Y_D1, "fr4"), (Y_GND1, "gnd"), (Y_D2, "fr4"), (Y_PWR, "plane08"),
           (Y_D3, "fr4"), (Y_GND2, "gnd"), (Y_D4, "fr4"), (Y_MASKB, "mask")]
    for k, (y, mn) in enumerate(lay):
        bx(f"cl{k}", (x0 - w, Y(y[0]), -w), (x0 + w, Y(y[1]), 0.0), m[mn], g)
    bx("c_via", (x0 - 0.7 * s, Y(BOT), -0.7 * s), (x0 + 0.7 * s, Y(0.0), 0.08), m["copper"], g)
    bx("c_via_fill", (x0 - 0.35 * s, Y(BOT), -0.4 * s), (x0 + 0.35 * s, Y(0.0), 0.08), m["mould"], g)
    bx("c_pad0", (x0 - 1.4 * s, Y(0.0), -1.4 * s), (x0 + 1.4 * s, Y(0.3), 0.08), m["pad"], g)
    b = O.ball("c_ball", (x0, Y(1.5), 0.0), BGA_R * s, m["solder"], g, 32)
    cut(b)
    bx("c_pad1", (x0 - 1.4 * s, Y(2.7), -1.4 * s), (x0 + 1.4 * s, Y(3.0), 0.08), m["pad"], g)
    pts["ball"] = (x0 + BGA_R * s, Y(1.5), 0.0)
    pts["via"] = (x0, Y(-4.0), 0.0)
    pts["plane"] = (x0 - w * 0.7, Y(PWR_Y), 0.0)
    # build-up and core
    for name, (y0, y1) in (("bu0", SUB_BU0), ("bu1", SUB_BU1)):
        h = (y1 - y0) / 4
        for k in range(4):
            a = y0 + h * k
            bx(f"c_{name}{k}", (x0 - w, Y(a), -w), (x0 + w, Y(a + h), 0.0), m["abf"], g)
            bx(f"c_{name}t{k}", (x0 - w, Y(a + h * 0.7), -0.6 * s), (x0 - w * 0.4, Y(a + h), 0.08), m["copper"], g)
            off = 0.5 * s * (1 if k % 2 else -1)
            bx(f"c_{name}mv{k}", (x0 + off - 0.6 * s, Y(a), -0.6 * s), (x0 + off + 0.6 * s, Y(a + h), 0.08), m["copper"], g)
    pts["buildup"] = (x0 - w * 0.6, Y(SUB_BU1[1] - 0.6), 0.0)
    bx("c_core", (x0 - w, Y(SUB_CORE[0]), -w), (x0 + w, Y(SUB_CORE[1]), 0.0), m["core"], g)
    for k, y in enumerate((6.8, 8.0, 9.2)):
        bx(f"c_weave{k}", (x0 - w, Y(y), -0.4), (x0 + w, Y(y + 0.25), 0.08), m["ink"], g)
    bx("c_pth", (x0 - 1.3 * s, Y(SUB_CORE[0]), -1.3 * s), (x0 + 1.3 * s, Y(SUB_CORE[1]), 0.08), m["copper"], g)
    bx("c_pthp", (x0 - 0.8 * s, Y(SUB_CORE[0]), -0.9 * s), (x0 + 0.8 * s, Y(SUB_CORE[1]), 0.08), m["mould"], g)
    pts["core"] = (x0 + w * 0.6, Y(8.0), 0.0)
    pts["pth"] = (x0, Y(8.0), 0.0)
    # C4s, interposer, TSVs, RDL, microbumps, die
    for k, dx in enumerate((-1.0, 1.0)):
        c = O.ball(f"c_c4{k}", (x0 + dx * 2.0 * s, Y(13.8), 0.0), 0.75 * s, m["solder"], g, 24)
        cut(c)
    bx("c_ufc4", (x0 - w, Y(C4[0]), -w), (x0 + w, Y(C4[1]), -0.8 * s), m["underfill"], g)
    pts["c4"] = (x0 + 2.0 * s, Y(13.8), 0.0)
    bx("c_ip", (x0 - w, Y(IP[0]), -w), (x0 + w, Y(IP[1]), 0.0), m["silicon"], g)
    for k, dx in enumerate((-2.0, 0.0, 2.0)):
        bx(f"c_tsv{k}", (x0 + dx * s - 0.35 * s, Y(IP[0]), -0.4 * s), (x0 + dx * s + 0.35 * s, Y(IP[1]), 0.08), m["copper"], g)
    pts["tsv"] = (x0 + 2.0 * s, Y(16.5), 0.0)
    bx("c_rdl", (x0 - w, Y(RDL[0]), -w), (x0 + w, Y(RDL[1]), 0.0), m["abf"], g)
    for k in range(3):
        y = RDL[0] + 0.2 + 0.3 * k
        bx(f"c_rdlc{k}", (x0 - w * (0.9 - 0.2 * k), Y(y), -0.3 * s), (x0 + w * (0.2 + 0.2 * k), Y(y + 0.15), 0.08), m["copper"], g)
    pts["rdl"] = (x0 - w * 0.5, Y(RDL[1]), 0.0)
    for k in range(-5, 6):
        u = O.ball(f"c_ub{k}", (x0 + k * 1.0 * s, Y(19.8), 0.0), 0.38 * s, m["solder"], g, 12)
        cut(u)
    pts["ubump"] = (x0 + 3.0 * s, Y(19.8), 0.0)
    bx("c_die", (x0 - w, Y(DIE[0]), -w), (x0 + w, Y(DIE[1]), 0.0), m["die"], g)
    for k in range(6):
        y = DIE[0] + 0.1 * k
        bx(f"c_beol{k}", (x0 - w, Y(y), -0.3 * s), (x0 + w, Y(y + 0.06), 0.08), m["gold"], g)
    pts["die"] = (x0 - w * 0.5, Y(24.0), 0.0)
    pts["beol"] = (x0 + w * 0.6, Y(DIE[0] + 0.3), 0.0)
    bx("c_tim1", (x0 - w, Y(TIM1[0]), -w), (x0 + w, Y(TIM1[1]), 0.0), m["tim"], g)
    bx("c_lid", (x0 - w, Y(LID[0]), -w), (x0 + w, Y(LID[1]), 0.0), m["lid"], g)
    bx("c_tim2", (x0 - w, Y(TIM2[0]), -w), (x0 + w, Y(TIM2[1]), 0.0), m["tim2"], g)
    bx("c_plate", (x0 - w, Y(PLATE[0]), -w), (x0 + w, Y(PLATE[1]), 0.0), m["plate"], g)
    for k in range(-4, 5):
        bx(f"c_fin{k}", (x0 + k * 2.5 * s / 2.0 - 0.25 * s, Y(FINS[0]), -w), (x0 + k * 2.5 * s / 2.0 + 0.25 * s, Y(FINS[1]), 0.0), m["plate"], g)
    pts["tim1"] = (x0 - w * 0.6, Y(27.4), 0.0)
    pts["lid"] = (x0 + w * 0.6, Y(29.4), 0.0)
    pts["tim2"] = (x0 - w * 0.6, Y(31.4), 0.0)
    pts["plate"] = (x0 + w * 0.6, Y(33.2), 0.0)
    pts["fins"] = (x0, Y(38.0), 0.0)
    pts["w"] = w
    pts["Y"] = Y
    return g, pts


def column_power(x0=0.0, s=4.0):
    Y = lambda y: BY + y * s  # noqa: E731
    return [(x0 - 6.0 * s, Y(PWR_Y), 0.6), (x0, Y(PWR_Y), 0.6), (x0, Y(1.5), 0.6), (x0, Y(SUB_CORE[1]), 0.6),
            (x0 + 2.0 * s, Y(13.8), 0.6), (x0 + 2.0 * s, Y(IP[1]), 0.6), (x0 + 1.0 * s, Y(19.8), 0.6), (x0, Y(22.0), 0.6)]


def column_heat(x, s=4.0):
    Y = lambda y: BY + y * s  # noqa: E731
    return [(x, Y(DIE[1] - 1.0), 0.6), (x, Y(LID[1]), 0.6), (x, Y(PLATE[1]), 0.6), (x, Y(FINS[1] - 1.0), 0.6)]


# ---- tray and rack (at TRAY_Y) ------------------------------------------------------------------


def tray(m, parent, y=TRAY_Y, z0=0.0, cables=True, name="tray"):
    """A compute tray: four GPU modules (cold plates on top), NVLink connectors at the back
    and cables up to a switch tray; coolant manifolds in blue and red."""
    g = empty(name, parent)
    bx(f"{name}_pan", (-200.0, y - 4.0, z0 - 150.0), (200.0, y, z0), m["rack"], g)
    bx(f"{name}_pcb", (-190.0, y, z0 - 140.0), (190.0, y + 2.0, z0 - 6.0), m["mask"], g)
    pts = {"mods": []}
    for k, x in enumerate((-135.0, -45.0, 45.0, 135.0)):
        bx(f"{name}_sub{k}", (x - 28.0, y + 2.0, z0 - 100.0), (x + 28.0, y + 6.0, z0 - 44.0), m["substrate"], g)
        bx(f"{name}_cp{k}", (x - 26.0, y + 6.0, z0 - 98.0), (x + 26.0, y + 14.0, z0 - 46.0), m["plate"], g)
        bx(f"{name}_cn{k}", (x - 20.0, y + 2.0, z0 - 140.0), (x + 20.0, y + 10.0, z0 - 128.0), m["conn"], g)
        for j, (dx, hm) in enumerate(((-10.0, "hose_cold"), (10.0, "hose_hot"))):
            D.polyline(f"{name}_h{k}{j}", [(x + dx, y + 14.0, z0 - 72.0), (x + dx, y + 20.0, z0 - 110.0), (x + dx, y + 20.0, z0 - 146.0)], 2.0, m[hm], g)
        pts["mods"].append((x, y + 14.0, z0 - 72.0))
    tube(f"{name}_man_c", (-195.0, y + 20.0, z0 - 146.0 + 3.0), (195.0, y + 20.0, z0 - 146.0 + 3.0), 3.0, m["hose_cold"], g, 12)
    tube(f"{name}_man_h", (-195.0, y + 26.0, z0 - 146.0 + 3.0), (195.0, y + 26.0, z0 - 146.0 + 3.0), 3.0, m["hose_hot"], g, 12)
    return g, pts


def switch_tray(m, parent, y, z0=0.0, name="sw"):
    g = empty(name, parent)
    bx(f"{name}_pan", (-200.0, y - 4.0, z0 - 150.0), (200.0, y, z0), m["rack"], g)
    for k, x in enumerate((-80.0, 80.0)):
        bx(f"{name}_chip{k}", (x - 30.0, y, z0 - 100.0), (x + 30.0, y + 10.0, z0 - 40.0), m["cold"], g)
    bx(f"{name}_ports", (-190.0, y, z0 - 150.0), (190.0, y + 10.0, z0 - 136.0), m["conn"], g)
    return g


def nvl_cables(m, parent, y0, y1, n=4, name="nvc"):
    g = empty(name, parent)
    for k in range(n):
        x = -135.0 + 90.0 * k
        D.polyline(f"{name}{k}", [(x, y0 + 6.0, -134.0), (x, y0 + 12.0, -160.0), (x * 0.4, y1 + 5.0, -160.0), (x * 0.4, y1 + 5.0, -143.0)], 2.2, m["cable"], g)
    return g


def nvl_path(k, y0, y1):
    x = -135.0 + 90.0 * k
    return [(x, y0 + 8.0, -72.0), (x, y0 + 8.0, -134.0), (x, y0 + 12.0, -160.0), (x * 0.4, y1 + 5.0, -160.0), (x * 0.4, y1 + 5.0, -100.0)]


def rack(m, parent, y0=TRAY_Y, n=6):
    """Trays stacked with switch trays in the middle; a frame and vertical manifolds."""
    g = empty("rack", parent)
    h = 40.0
    ys = []
    for k in range(n):
        yk = y0 + h * k + (2 * h if k >= n // 2 else 0.0)
        tray(m, g, y=yk, name=f"rt{k}")
        ys.append(yk)
    for j in range(2):
        switch_tray(m, g, y0 + h * (n // 2) + h * j, name=f"rs{j}")
    top = y0 + h * (n + 2)
    for k, x in enumerate((-210.0, 210.0)):
        bx(f"rpost{k}", (x - 4.0, y0 - 10.0, -154.0), (x + 4.0, top, -146.0), m["rack"], g)
        bx(f"rpostf{k}", (x - 4.0, y0 - 10.0, -8.0), (x + 4.0, top, 0.0), m["rack"], g)
    tube("rman_c", (-188.0, y0 - 10.0, -160.0), (-188.0, top, -160.0), 5.0, m["hose_cold"], g, 16)
    tube("rman_h", (188.0, y0 - 10.0, -160.0), (188.0, top, -160.0), 5.0, m["hose_hot"], g, 16)
    return g, ys, top


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))
