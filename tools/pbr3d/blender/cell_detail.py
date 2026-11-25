"""Detailed part builders for the CELL page (cell_sections.py, cell_overview.py).

The cell itself is rnd_3d_dram_kit.planar_cell: today's 6F2 1T1C cell with a buried word line
(BCAT): n+ drain and source in a silicon ridge, the word line buried in an oxide-lined trench with a
nitride cap, the channel a U round the trench bottom, the bit line behind the cut plane on its
contact, a storage-node contact, a landing pad and a tall TiN / high-k / TiN cylinder capacitor.
Units are schematic mm, Y up, camera on +z, cut at z = 0 (docs/diagram-pages.md). F = FS = 200.

This file adds what the CELL story needs around that cell:

  read_rig      one cell on a long bit line (BL) that runs left into an open-bit-line sense amp,
                and the twin line BL-bar that runs on to the neighbouring mat as the reference;
                the sense amp is two cross-coupled inverters; an equaliser (precharge) shorts BL to
                BL-bar at VDD/2; two voltage gauges, one per line.
  leak_paths    the four ways charge leaves the storage node, as bead streams with their own colour:
                subthreshold (through the off channel to the drain), junction (from the source n+ into
                the substrate), GIDL (at the gate edge of the drain) and the capacitor dielectric.
  support       the silicon-nitride lattice that holds the tall capacitors up (rings and bridges at
                two heights).
  field         an nx by nz block of planar cells with the lattice, for overviews.

Every overlay is built hidden; switch it with K.on(obj, intervals).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, disc, empty, key, mat, pivot, rel, tube  # noqa: E402
import rnd_3d_dram_kit as K  # noqa: E402
from rnd_3d_dram_kit import FS, PL_BL_Y, PL_BL_Z, PL_CAP0, PL_CAP_H, PL_CAP_R, PL_SN_X, PL_TR, hidden, on  # noqa: E402

VDD = 900.0  # gauge height for a full rail
BL_Z = (PL_BL_Z[0] + PL_BL_Z[1]) / 2  # bit-line centre z (behind the cut)
BL_YC = (PL_BL_Y[0] + PL_BL_Y[1]) / 2


def mats(m):
    """CELL extras on top of K.mats (call K.mats first)."""
    m["inv"] = mat("cd_inv", (0.34, 0.26, 0.52), rough=0.55)
    m["inv_on"] = mat("cd_inv_on", (0.65, 0.40, 1.0), emit=(0.62, 0.36, 1.0), strength=2.2)
    m["sa_box"] = mat("cd_sa_box", (0.16, 0.15, 0.22), rough=0.8)
    m["eq"] = mat("cd_eq", (0.22, 0.40, 0.28), rough=0.6)
    m["eq_on"] = mat("cd_eq_on", (0.35, 0.95, 0.50), emit=(0.32, 0.92, 0.48), strength=2.2)
    m["blb"] = mat("cd_blb", (0.20, 0.42, 0.62), metal=0.5, rough=0.3)
    m["gauge_bg"] = mat("cd_gauge_bg", (0.12, 0.13, 0.16), rough=0.8)
    m["gauge_bl"] = mat("cd_gauge_bl", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.8)
    m["gauge_blb"] = mat("cd_gauge_blb", (0.50, 0.62, 1.0), emit=(0.45, 0.58, 1.0), strength=1.6)
    m["half"] = mat("cd_half", (1.0, 1.0, 1.0), emit=(1.0, 1.0, 1.0), strength=1.2)
    m["lattice"] = mat("cd_lattice", (0.52, 0.66, 0.56), rough=0.5)
    m["lk_sub"] = mat("cd_lk_sub", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=3.0)
    m["lk_jn"] = mat("cd_lk_jn", (1.0, 0.35, 0.30), emit=(1.0, 0.30, 0.25), strength=3.0)
    m["lk_gidl"] = mat("cd_lk_gidl", (1.0, 0.45, 0.85), emit=(1.0, 0.40, 0.85), strength=3.0)
    m["lk_diel"] = mat("cd_lk_diel", (0.95, 0.95, 0.40), emit=(0.95, 0.95, 0.35), strength=3.0)
    return m


# ---- the read rig: cell, BL, sense amp, BL-bar, gauges -----------------------------------------

SA_X = -1000.0  # sense amp centre x
REF_X1 = -2700.0  # far end of BL-bar (the neighbouring mat)
GAUGE_Y0 = 720.0  # gauge bars stand above the sense amp, clear of the capacitor top
GAUGE_DX = 180.0


class Rig:
    def __init__(self):
        self.cell = None  # the PlanarCell
        self.ref_cells = []  # cells on BL-bar, never selected
        self.bl_bar_on = None
        self.sa_on = None
        self.eq_on = None
        self.charge = None  # orange strips on the storage-node electrode (hidden)
        self.level = None  # their pivot: scale (1, 1, v) for a charge level v
        self.g_bl = None  # gauge bar pivots: scale y, 1.0 = VDD, 0.5 = VDD/2
        self.g_blb = None
        self.pts = {}
        self.share = []  # path cap -> BL -> sense amp
        self.restore = []  # sense amp -> BL -> cap


def _gauge(parent, m, x, mk, name):
    g = empty(name, parent)
    z = BL_Z
    box(f"{name}_bg", (x - 70, GAUGE_Y0, z - 40), (x + 70, GAUGE_Y0 + VDD, z - 20), m["gauge_bg"], g)
    box(f"{name}_half", (x - 95, GAUGE_Y0 + VDD / 2 - 5, z - 40), (x + 95, GAUGE_Y0 + VDD / 2 + 5, z + 30), m["half"], g)
    pv = pivot(f"{name}_lv", (x, GAUGE_Y0, z), g)
    box(f"{name}_bar", rel((x, GAUGE_Y0, z), (x - 50, GAUGE_Y0, z - 15)), rel((x, GAUGE_Y0, z), (x + 50, GAUGE_Y0 + VDD, z + 15)), m[mk], pv)
    return pv


def _inverter(parent, m, name, c, flip):
    """An inverter symbol lying in the x-y plane: a wedge (stacked boxes) and its output bubble."""
    x, y, z = c
    s = -1 if flip else 1
    objs = []
    for k in range(5):
        hh = 110 - k * 22
        xx = x + s * (k * 36 - 72)
        objs.append(box(f"{name}_w{k}", (xx - 18, y - hh, z - 25), (xx + 18, y + hh, z + 25), m["inv"], parent))
    K.join(objs, f"{name}_body")
    ball_ = disc(f"{name}_dot", (x + s * 120, y, z), 22, 50, m["inv"], parent, verts=16)
    return ball_


def read_rig(parent, m, o=(0.0, 0.0, 0.0), refs=2):
    """The cell at o on a bit line that runs left into the sense amp at SA_X; BL-bar leaves the
    sense amp's far side to `refs` reference cells of the neighbouring mat. Returns a Rig."""
    ox, oy, oz = o
    r = Rig()
    g = empty("rig", parent)
    bl_x0 = ox + SA_X + 160
    r.cell = K.planar_cell(g, m, o, "c0", cutp=True, tile=False, bl_span=(bl_x0, ox + 320))
    # BL-bar: the same height and z, from the sense amp's far side to the neighbouring mat
    blb_x1 = ox + SA_X - 160
    y0, y1 = oy + PL_BL_Y[0], oy + PL_BL_Y[1]
    z0, z1 = oz + PL_BL_Z[0], oz + PL_BL_Z[1]
    box("blb", (ox + REF_X1, y0, z0), (blb_x1, y1, z1), m["blb"], g)
    r.bl_bar_on = hidden("blb_on", g)
    box("blb_glow", (ox + REF_X1, y0 - 10, z0 - 10), (blb_x1, y1 + 10, z1 + 10), m["bl_on"], r.bl_bar_on)
    for i in range(refs):
        x = ox + SA_X - 700 - i * 3 * FS
        c = K.planar_cell(g, m, (x, oy, oz), f"ref{i}", cutp=True, tile=False, bl_span=(x - 300, x + 300), cap_h=PL_CAP_H)
        r.ref_cells.append(c)
    # sense amp: a dark box on the bit-line level with two cross-coupled inverters on its face
    sx = ox + SA_X
    box("sa_box", (sx - 160, oy + 60, z0 - 80), (sx + 160, oy + 640, z1 + 60), m["sa_box"], g)
    zf = z1 + 70
    _inverter(g, m, "inv_a", (sx, oy + 470, zf), False)
    _inverter(g, m, "inv_b", (sx, oy + 230, zf), True)
    tube("x_ab", (sx + 120, oy + 470, zf), (sx - 120, oy + 230, zf), 12, m["inv"], g, verts=8)
    tube("x_ba", (sx - 120, oy + 470, zf), (sx + 120, oy + 230, zf), 12, m["inv"], g, verts=8)
    r.sa_on = hidden("sa_on", g)
    box("sa_glow", (sx - 175, oy + 45, zf - 10), (sx + 175, oy + 655, zf + 5), m["inv_on"], r.sa_on)
    # equaliser / precharge: a green link across the two line ends, under the sense amp
    box("eq", (sx - 200, oy + 20, z0 - 20), (sx + 200, oy + 60, z1 + 20), m["eq"], g)
    r.eq_on = hidden("eq_on", g)
    box("eq_glow", (sx - 215, oy + 10, z0 - 30), (sx + 215, oy + 70, z1 + 30), m["eq_on"], r.eq_on)
    # gauges over the sense amp: BL on the right, BL-bar on the left
    r.g_bl = _gauge(g, m, sx + GAUGE_DX, "gauge_bl", "g_bl")
    r.g_blb = _gauge(g, m, sx - GAUGE_DX, "gauge_blb", "g_blb")
    for pv in (r.g_bl, r.g_blb):
        key(pv, 0, "scale", (1, 1, 0.5))
    r.charge, r.level = q_strips(g, m, o, "q")
    zt = oz + 12
    r.pts = dict(r.cell.pts)
    r.pts.update({
        "sa": (sx, oy + 640, zt), "eq": (sx + 200, oy + 40, zt), "blb": (ox + REF_X1 + 200, BL_YC + oy, oz + BL_Z),
        "bl_mid": (ox - 800, BL_YC + oy, oz + BL_Z), "g_bl": (sx + GAUGE_DX + 70, GAUGE_Y0 + VDD * 0.75, oz),
        "g_blb": (sx - GAUGE_DX - 70, GAUGE_Y0 + VDD * 0.75, oz), "half": (sx, GAUGE_Y0 + VDD / 2, oz),
        "ref": r.ref_cells[0].pts["cap"] if r.ref_cells else (ox + REF_X1, 0, 0),
    })
    path = list(r.cell.read_path[:-1])
    yb = path[-1][1]
    r.share = path + [(sx + 170, yb, zt)]
    r.restore = list(reversed(r.share))
    return r


def q_strips(parent, m, o, name):
    """The charge on a cut cell's storage node: two glowing strips on the cut face where the TiN
    electrode is, plus the contact below. Hidden switch, and a level pivot at the capacitor foot
    (scale (1, 1, v) to drain or fill). Returns (switch, level_pivot)."""
    ox, oy, oz = o
    sw = hidden(f"{name}_on", parent)
    pv = pivot(f"{name}_lv", (ox + PL_SN_X, oy + PL_CAP0, oz), sw)
    base = (ox + PL_SN_X, oy + PL_CAP0, oz)
    for s_ in (-1, 1):
        xa, xb = sorted((ox + PL_SN_X + s_ * PL_CAP_R * 0.50, ox + PL_SN_X + s_ * PL_CAP_R * 0.74))
        box(f"{name}{s_}", rel(base, (xa, oy + PL_CAP0 + 20, oz + 7)), rel(base, (xb, oy + PL_CAP0 + PL_CAP_H - 40, oz + 9)), m["charge"], pv)
    box(f"{name}_snc", (ox + PL_SN_X - 30, oy + 10, oz + 7), (ox + PL_SN_X + 30, oy + PL_CAP0, oz + 9), m["charge"], sw)
    return sw, pv


def level_keys(pv, keys):
    for f, v in keys:
        key(pv, f, "scale", (1, 1, max(v, 0.01)))


def gauge_keys(pv, keys):
    """(frame, level) keys, level 1.0 = VDD, 0.5 = VDD/2, 0 = ground."""
    for f, v in keys:
        key(pv, f, "scale", (1, 1, max(v, 0.01)))


# ---- leakage ----------------------------------------------------------------------------------


def leak_paths(cell, o=(0.0, 0.0, 0.0)):
    """Absolute polylines (in front of the cut) for the four leaks out of `cell`'s storage node.
    Returns {kind: pts} for kinds "sub", "jn", "gidl", "diel"."""
    ox, oy, oz = o
    z = oz + 14

    def A(x, y):
        return (ox + x, oy + y, z)

    cap_mid = PL_CAP0 + PL_CAP_H * 0.45
    return {
        # through the off transistor: storage node down, round the trench bottom, out the drain
        "sub": [A(PL_SN_X, cap_mid), A(PL_SN_X, 10), A(-20, -110), A(-30, -PL_TR - 20), A(-175, -PL_TR - 20), A(-185, -110), A(-260, -40)],
        # source n+ junction into the p-type substrate
        "jn": [A(PL_SN_X, cap_mid - 200), A(PL_SN_X, 10), A(40, -130), A(30, -330), A(20, -560)],
        # gate-induced drain leakage: the strong field where the gate meets the n+ drain edge
        "gidl": [A(-150, -80), A(-200, -150), A(-210, -300), A(-205, -560)],
        # through the thin capacitor dielectric to the plate
        "diel": [A(PL_SN_X, cap_mid + 300), A(PL_SN_X + PL_CAP_R * 0.7, cap_mid + 300), A(PL_SN_X + PL_CAP_R + 160, cap_mid + 330)],
    }


LEAK_MAT = {"sub": "lk_sub", "jn": "lk_jn", "gidl": "lk_gidl", "diel": "lk_diel"}


def leak(parent, m, paths, kind, n, b, u0, u1, life=70, size=16.0):
    return K.beads(parent, m, f"lk_{kind}_{b}", paths[kind], n, b, u0, u1, life=life, size=size, mk=LEAK_MAT[kind])


# ---- the nitride support lattice and a field of cells ------------------------------------------


def support(parent, m, centres, y, r=PL_CAP_R, name="lat"):
    """A nitride lattice at height y: a ring round each capacitor and bridges between neighbours."""
    g = empty(name, parent)
    objs = []
    for k, (x, z) in enumerate(centres):
        objs.append(disc(f"{name}_r{k}", (x, y, z), r + 28, 40, m["lattice"], g, verts=20))
    cs = sorted(centres)
    for k, (a, b) in enumerate(zip(cs, cs[1:])):
        if abs(a[1] - b[1]) < 1 and abs(a[0] - b[0]) < 3.5 * FS:
            objs.append(box(f"{name}_bx{k}", (a[0], y - 20, a[1] - 22), (b[0], y + 20, a[1] + 22), m["lattice"], g))
    bz = sorted(centres, key=lambda c: (c[0], c[1]))
    for k, (a, b) in enumerate(zip(bz, bz[1:])):
        if abs(a[0] - b[0]) < 1 and abs(a[1] - b[1]) < 2.5 * FS:
            objs.append(box(f"{name}_bz{k}", (a[0] - 22, y - 20, a[1]), (a[0] + 22, y + 20, b[1]), m["lattice"], g))
    K.join(objs, f"{name}_mesh")
    return g


def field(parent, m, o=(0.0, 0.0, 0.0), nx=3, nz=3, name="fld", lattice=True):
    """nx by nz planar cells (front row cut) with the nitride lattice at 45 % and 90 % height."""
    a = K.planar_array(parent, m, o, nx, nz, name=name, tile_at=None)
    if lattice:
        ox, oy, oz = o
        cs = [(c.pts["cap_top"][0], c.pts["cap_top"][2]) for c in a.cells.values() if c.pts["cap_top"][2] < oz - 1]
        for frac, nm in ((0.45, "mid"), (0.9, "top")):
            support(a.g, m, cs, oy + PL_CAP0 + PL_CAP_H * frac, name=f"{name}_lat_{nm}")
    return a


__all__ = ["mats", "read_rig", "gauge_keys", "leak_paths", "leak", "support", "field", "on", "VDD", "SA_X", "F", "P"]
