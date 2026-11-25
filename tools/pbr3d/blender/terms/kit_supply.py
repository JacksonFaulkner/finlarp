"""Materials-supply kit for the Terms-tab overviews (rare earths, gallium, helium).

Import from a trm_*.py script after term_common.setup(); every part takes the materials dict m and a
parent, and builds in scene coordinates (Y up, mm). Positions in `c` are the base centre of a part
unless noted. Children of a pivot are built relative to it (power_vrm_detail.rel).

API
  materials(m)                                       add the sup_* materials (call once after setup)
  rock_pile(m, parent, name, c, r, n=7, mt)  -> grp  heap of ore lumps on c; mt default "sup_ore"
  drum(m, parent, name, c, r, h, mt)         -> grp  solid steel drum standing on c, two hoops
  tank(m, parent, name, c, r, h, mt)   -> (grp, pts) open-top vessel on c; pts: top, mid
  pipe(m, parent, name, pts, r, mt)          -> grp  segmented pipe through absolute points pts
  ring(m, parent, name, c, r, tube_r, mt, axis, n) -> grp
                                                     closed loop of tubes centred on c; axis "y" (flat
                                                     in xz) or "z" (flat in xy)
  magnet(m, parent, name, c, size, pole)     -> obj  block magnet centred at c; pole "n" red, "s" blue
  motor(m, parent, name, c, r, h, poles)  -> (grp, rotor, pts)
                                                     fan/robot motor on c: steel case, copper coil ring,
                                                     magnet rotor (rotor is a pivot: spin it); pts: top
  lattice(m, parent, name, c, nx, nz, pitch, r, mt_a, mt_b) -> grp
                                                     square grid of atoms in the xz plane at height c[1];
                                                     odd sites use mt_b when given
  arrows(m, parent, name, items, length, mt) -> grp  short tubes; items = [(centre, unit_dir), ...]
  cloud(m, parent, name, c, n, spread, r, mt) -> grp n atoms scattered within `spread` of c
  dewar(m, parent, name, c, r, h, mt)   -> (grp, liquid_obj, pts)
                                                     steel vacuum tank on c, liquid bath to 60% height,
                                                     coil ring inside the bath; pts: liquid, coil
  chamber(m, parent, name, c, w, h, d)  -> (grp, pts) steel process box on c with a glass front; pts:
                                                     front, top
  gantry(m, parent, name, c, r, depth)  -> (grp, pts) horizontal scanner bore along z centred at c;
                                                     pts: bore (front face centre)
  die(m, parent, name, c, w, d, mt)     -> (grp, glow_obj, pts)
                                                     small black package on a board with a die on top;
                                                     pts: top

Material keys: sup_steel sup_ore sup_gas sup_ndfeb sup_pole_n sup_pole_s sup_ga sup_coil sup_cryo
sup_he sup_flow sup_glass sup_ga_atom sup_n_atom sup_pcb sup_pkg sup_hot sup_arrow_up sup_arrow_dn
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sand_overview as O  # noqa: E402
from sand_overview import mat, empty  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx  # noqa: E402

# name: (base colour, metallic, roughness, emission colour or None, emission strength)
_SPEC = {
    "sup_steel": ((0.55, 0.57, 0.60), 0.85, 0.35, None, 0.0),
    "sup_ore": ((0.48, 0.30, 0.20), 0.0, 0.85, None, 0.0),
    "sup_gas": ((0.70, 0.74, 0.78), 0.8, 0.3, None, 0.0),
    "sup_ndfeb": ((0.30, 0.31, 0.34), 0.7, 0.4, None, 0.0),
    "sup_pole_n": ((0.85, 0.22, 0.22), 0.0, 0.5, (0.9, 0.2, 0.2), 1.8),
    "sup_pole_s": ((0.25, 0.45, 0.90), 0.0, 0.5, (0.25, 0.5, 1.0), 1.8),
    "sup_ga": ((0.80, 0.82, 0.86), 0.9, 0.08, None, 0.0),
    "sup_coil": ((0.75, 0.45, 0.25), 0.9, 0.3, None, 0.0),
    "sup_cryo": ((0.55, 0.85, 1.0), 0.0, 0.2, (0.40, 0.85, 1.0), 1.5),
    "sup_he": ((0.40, 0.90, 1.0), 0.0, 0.3, (0.35, 0.90, 1.0), 2.0),
    "sup_flow": ((1.0, 0.60, 0.20), 0.0, 0.3, (1.0, 0.55, 0.15), 2.5),
    "sup_ga_atom": ((0.72, 0.74, 0.80), 0.7, 0.3, None, 0.0),
    "sup_n_atom": ((0.30, 0.55, 0.95), 0.0, 0.4, None, 0.0),
    "sup_pcb": ((0.10, 0.18, 0.40), 0.0, 0.55, None, 0.0),
    "sup_pkg": ((0.08, 0.08, 0.09), 0.0, 0.6, None, 0.0),
    "sup_hot": ((1.0, 0.40, 0.20), 0.0, 0.4, (1.0, 0.40, 0.15), 2.0),
    "sup_arrow_up": ((0.95, 0.50, 0.20), 0.0, 0.4, (1.0, 0.50, 0.15), 1.5),
    "sup_arrow_dn": ((0.30, 0.60, 1.00), 0.0, 0.4, (0.25, 0.60, 1.0), 1.5),
}


def materials(m):
    for k, (c, metal, rough, emit, strength) in _SPEC.items():
        m[k] = mat(k, c, metal=metal, rough=rough, emit=emit, strength=strength)
    m["sup_glass"] = mat("sup_glass", (0.75, 0.90, 1.0), rough=0.05, alpha=0.25)


def rock_pile(m, parent, name, c, r, n=7, mt="sup_ore"):
    g = empty(name, parent)
    for k in range(n):
        a = 2.399 * k
        d = r * (0.4 + 0.6 * ((k * 0.37) % 1.0))
        rr = r * (0.45 + 0.25 * ((k * 0.61) % 1.0))
        O.rock(f"{name}_{k}", (c[0] + d * math.cos(a), c[1] + rr * 0.6, c[2] + d * math.sin(a)), rr, m[mt], g)
    return g


def drum(m, parent, name, c, r, h, mt="sup_steel"):
    g = empty(name, parent)
    O.disc(f"{name}_body", (c[0], c[1] + h / 2, c[2]), r, h, m[mt], g, 48)
    for k, f in enumerate((0.2, 0.8)):
        O.disc(f"{name}_hoop{k}", (c[0], c[1] + h * f, c[2]), r * 1.03, h * 0.06, m["sup_steel"], g, 48)
    return g


def tank(m, parent, name, c, r, h, mt="sup_steel"):
    g = empty(name, parent)
    O.cup(f"{name}_wall", c, r, h, m[mt], g)
    O.disc(f"{name}_floor", (c[0], c[1] + 0.5, c[2]), r, 1.0, m[mt], g)
    return g, {"top": (c[0], c[1] + h, c[2]), "mid": (c[0], c[1] + h / 2, c[2] + r)}


def pipe(m, parent, name, pts, r, mt="sup_steel"):
    return D.wire(name, pts, r, m[mt], parent)


def ring(m, parent, name, c, r, tube_r, mt="sup_coil", axis="y", n=28):
    g = empty(name, parent)
    pts = []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        u, v = r * math.cos(a), r * math.sin(a)
        pts.append((c[0] + u, c[1], c[2] + v) if axis == "y" else (c[0] + u, c[1] + v, c[2]))
    for k in range(n):
        O.tube(f"{name}_{k}", pts[k], pts[k + 1], tube_r, m[mt], g, 8)
    return g


def magnet(m, parent, name, c, size, pole="n"):
    h = [s / 2 for s in size]
    key = "sup_pole_n" if pole == "n" else "sup_pole_s"
    return bx(name, tuple(c[i] - h[i] for i in range(3)), tuple(c[i] + h[i] for i in range(3)), m[key], parent)


def motor(m, parent, name, c, r, h, poles=8):
    g = empty(name, parent)
    O.cup(f"{name}_case", c, r, h, m["sup_steel"], g)
    O.disc(f"{name}_base", (c[0], c[1] + 0.5, c[2]), r, 1.0, m["sup_steel"], g)
    ring(m, g, f"{name}_coil", (c[0], c[1] + h * 0.7, c[2]), r * 0.85, max(0.8, r * 0.07), "sup_coil", "y", 24)
    at = (c[0], c[1] + h * 0.5, c[2])
    rot = O.pivot(f"{name}_rotor", at, g)
    O.disc(f"{name}_disc", (0.0, 0.0, 0.0), r * 0.7, h * 0.25, m["sup_steel"], rot)
    for k in range(poles):
        a = 2 * math.pi * k / poles
        p = (r * 0.6 * math.cos(a), 0.0, r * 0.6 * math.sin(a))
        magnet(m, rot, f"{name}_mag{k}", p, (r * 0.22, h * 0.22, r * 0.22), "n" if k % 2 == 0 else "s")
    return g, rot, {"top": (c[0], c[1] + h, c[2])}


def lattice(m, parent, name, c, nx, nz, pitch, r, mt_a, mt_b=None):
    g = empty(name, parent)
    for i in range(nx):
        for j in range(nz):
            x = c[0] + (i - (nx - 1) / 2) * pitch
            z = c[2] + (j - (nz - 1) / 2) * pitch
            mt = mt_b if (mt_b and (i + j) % 2) else mt_a
            O.ball(f"{name}_{i}_{j}", (x, c[1], z), r, m[mt], g, 8)
    return g


def arrows(m, parent, name, items, length, mt):
    g = empty(name, parent)
    for k, (c, d) in enumerate(items):
        a = tuple(c[i] - d[i] * length / 2 for i in range(3))
        b = tuple(c[i] + d[i] * length / 2 for i in range(3))
        O.tube(f"{name}_{k}", a, b, length * 0.12, m[mt], g, 6)
    return g


def cloud(m, parent, name, c, n, spread, r, mt="sup_he"):
    g = empty(name, parent)
    for k in range(n):
        u = ((k * 0.618) % 1.0) * 2 - 1
        v = ((k * 0.382 + 0.3) % 1.0) * 2 - 1
        w = ((k * 0.733 + 0.6) % 1.0) * 2 - 1
        O.ball(f"{name}_{k}", (c[0] + spread * u, c[1] + spread * v, c[2] + spread * w), r, m[mt], g, 8)
    return g


def dewar(m, parent, name, c, r, h, mt="sup_steel"):
    g = empty(name, parent)
    O.cup(f"{name}_shell", c, r, h, m[mt], g)
    O.disc(f"{name}_base", (c[0], c[1] + 0.5, c[2]), r, 1.0, m[mt], g)
    liq_h = h * 0.6
    liq = O.disc(f"{name}_liquid", (c[0], c[1] + liq_h / 2, c[2]), r * 0.9, liq_h, m["sup_cryo"], g)
    coil_c = (c[0], c[1] + liq_h * 0.5, c[2])
    ring(m, g, f"{name}_coil", coil_c, r * 0.55, max(0.8, r * 0.06), "sup_coil", "y", 24)
    return g, liq, {"liquid": (c[0], c[1] + liq_h, c[2]), "coil": (c[0] + r * 0.55, coil_c[1], c[2])}


def chamber(m, parent, name, c, w, h, d):
    g = empty(name, parent)
    x0, x1 = c[0] - w / 2, c[0] + w / 2
    z0, z1 = c[2] - d / 2, c[2] + d / 2
    bx(f"{name}_body", (x0, c[1], z0), (x1, c[1] + h, z1), m["sup_steel"], g)
    bx(f"{name}_window", (x0 + w * 0.1, c[1] + h * 0.2, z1), (x1 - w * 0.1, c[1] + h * 0.8, z1 + 1.0),
       m["sup_glass"], g)
    return g, {"front": (c[0], c[1] + h * 0.5, z1 + 1.0), "top": (c[0], c[1] + h, c[2])}


def gantry(m, parent, name, c, r, depth):
    g = empty(name, parent)
    O.tube(f"{name}_body", (c[0], c[1], c[2] - depth / 2), (c[0], c[1], c[2] + depth / 2), r, m["sup_steel"], g, 32)
    ring(m, g, f"{name}_bore", (c[0], c[1], c[2] + depth / 2 + 0.5), r * 0.7, max(0.6, r * 0.06), "sup_cryo", "z", 28)
    return g, {"bore": (c[0], c[1], c[2] + depth / 2 + 1.0)}


def die(m, parent, name, c, w, d, mt="sup_hot"):
    g = empty(name, parent)
    bx(f"{name}_board", (c[0] - w, c[1] - 1.6, c[2] - d), (c[0] + w, c[1], c[2] + d), m["sup_pcb"], g)
    bx(f"{name}_pkg", (c[0] - w * 0.5, c[1], c[2] - d * 0.5), (c[0] + w * 0.5, c[1] + 2.0, c[2] + d * 0.5),
       m["sup_pkg"], g)
    glow = bx(f"{name}_die", (c[0] - w * 0.2, c[1] + 2.0, c[2] - d * 0.2), (c[0] + w * 0.2, c[1] + 2.3, c[2] + d * 0.2),
              m[mt], g)
    return g, glow, {"top": (c[0], c[1] + 2.3, c[2])}
