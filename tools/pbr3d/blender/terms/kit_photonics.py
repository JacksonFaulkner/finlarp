"""Photonics kit: shared parts for the optics terms (TRM_MACH_ZEHNDER, TRM_THIN_FILM_LITHIUM_NIOBATE,
TRM_WDM). Every part takes a materials dict `m` (from mats()) and a `parent`, and returns a group
or a dict of points and groups. Scene units: y is up, the chip or card lies in x-z at its top y.

API
  mats(m)
      add the ph_* materials (silicon, oxide, lithium niobate, gold, glass, PCB, case) and glows
      (laser colours, drive amber, field violet) to m. Call once after C.setup.
  pic(m, parent, name, x0, x1, z0, z1, y=0.0, sub="ph_si") -> group
      a photonic die: silicon substrate with a buried oxide layer on top. Top at y + 4.
  wg(m, parent, name, pts, r=0.6, mt="ph_wg") -> group
      a waveguide (round wire) through absolute points pts.
  mzm(m, parent, name, cx, cz, L, arm, y, ln=False) -> dict
      a Mach-Zehnder: input and output guides, a splitter, two arms bowing out to +/- arm,
      recombination. ln=True uses the thin-film lithium niobate ridge material. Returns
      {"in": pts, "out": pts, "arms": {+1: pts, -1: pts}, "elec": {+1: group, -1: group},
       "pts": {"in", "split", "top", "bot", "recomb", "out"} (absolute points), "group": group}.
      Electrode pairs (signal + ground) run alongside each arm, centre section only.
  arm_pts(cx, cz, L, arm, sign, y, n=28) -> list
      points of one arm (used by mzm; exposed so beads can ride one arm).
  module(m, parent, name, c, w, h, d, cut=True) -> group
      a pluggable optical module: a dark case, open top when cut=True so the chip inside shows.
  pcb(m, parent, name, x0, x1, z0, z1, y=0.0) -> group
      a green board slab at height y.
  dsp(m, parent, name, c, w, d, h=1.2) -> group
      a dark IC block (the DSP next to an optics module).
  fiber(m, parent, name, pts, r=0.45) -> group
      a fibre through absolute points.
  laser(m, parent, name, c, col, size=3.0) -> group
      a laser die: a small block with a glowing top facet. col is "ph_red", "ph_cyan", "ph_green",
      "ph_amber" or "ph_violet" (glow materials from mats()).
  awg(m, parent, name, c, w, d, h, n) -> dict
      an arrayed-waveguide grating (mux or demux) box with n glowing ports on its +x face.
      Returns {"group", "ports": [(x, y, z)...] absolute, "in": (x, y, z)}.
  switch_panel(m, parent, name, x0, x1, y0, y1, z, cols=8, rows=2) -> group
      a switch faceplate: a dark box with a grid of small port sockets on its front.
  chan_mats() -> list of 8 glow material names, one per WDM channel.
  tfln_xsec(m, parent, name, cx, cy, cz, length, w=2.4) -> dict
      cut-open thin-film lithium niobate waveguide: silicon, oxide, the LN film and ridge, two gold
      electrodes. Returns {"group", "ridge", "elec", "field", "pts"}.
  front(m, parent, name, c, size=1.0) -> group
      the blue-grey card that sits behind a term's bench (plain cutaway backdrop).
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
sys.path.insert(0, BL)
from sand_overview import empty, mat  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, polyline  # noqa: E402

CHANNEL_GLOWS = ["ph_c0", "ph_c1", "ph_c2", "ph_c3", "ph_c4", "ph_c5", "ph_c6", "ph_c7"]
_CHAN_RGB = [
    (1.00, 0.30, 0.25), (1.00, 0.70, 0.20), (0.95, 0.95, 0.30), (0.35, 1.00, 0.45),
    (0.25, 0.95, 1.00), (0.35, 0.50, 1.00), (0.75, 0.40, 1.00), (1.00, 0.40, 0.80),
]


def mats(m):
    m["ph_si"] = mat("ph_si", (0.36, 0.38, 0.46), metal=0.5, rough=0.35)
    m["ph_oxide"] = mat("ph_oxide", (0.85, 0.90, 0.95), rough=0.2)
    m["ph_ln"] = mat("ph_ln", (0.62, 0.50, 0.78), rough=0.3)
    m["ph_gold"] = mat("ph_gold", (0.88, 0.72, 0.30), metal=0.95, rough=0.25)
    m["ph_wg"] = mat("ph_wg", (0.55, 0.70, 0.95), rough=0.15)
    m["ph_fiber"] = mat("ph_fiber", (0.72, 0.84, 0.95), rough=0.08)
    m["ph_pcb"] = mat("ph_pcb", (0.08, 0.30, 0.20), rough=0.55)
    m["ph_case"] = mat("ph_case", (0.14, 0.15, 0.18), metal=0.5, rough=0.4)
    m["ph_dsp"] = mat("ph_dsp", (0.10, 0.10, 0.12), metal=0.3, rough=0.5)
    m["ph_port"] = mat("ph_port", (0.05, 0.05, 0.06), rough=0.6)
    m["ph_front"] = mat("ph_front", (0.22, 0.26, 0.32), metal=0.4, rough=0.5)
    m["ph_red"] = mat("ph_red", (1.0, 0.25, 0.20), emit=(1.0, 0.2, 0.15), strength=3.0)
    m["ph_cyan"] = mat("ph_cyan", (0.30, 0.90, 1.0), emit=(0.25, 0.85, 1.0), strength=3.0)
    m["ph_green"] = mat("ph_green", (0.35, 1.0, 0.45), emit=(0.3, 1.0, 0.4), strength=3.0)
    m["ph_amber"] = mat("ph_amber", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=3.0)
    m["ph_violet"] = mat("ph_violet", (0.70, 0.50, 1.0), emit=(0.65, 0.45, 1.0), strength=2.5)
    for k, rgb in enumerate(_CHAN_RGB):
        m[CHANNEL_GLOWS[k]] = mat(CHANNEL_GLOWS[k], rgb, emit=rgb, strength=3.0)


def chan_mats():
    return list(CHANNEL_GLOWS)


def pic(m, parent, name, x0, x1, z0, z1, y=0.0, sub="ph_si"):
    g = empty(name, parent)
    bx(f"{name}_sub", (x0, y, z0), (x1, y + 3.0, z1), m[sub], g)
    bx(f"{name}_box", (x0, y + 3.0, z0), (x1, y + 4.0, z1), m["ph_oxide"], g)
    return g


def wg(m, parent, name, pts, r=0.6, mt="ph_wg"):
    return polyline(name, pts, r, m[mt], parent)


def arm_pts(cx, cz, L, arm, sign, y, n=28):
    x0, x1 = cx - L / 2 + 8, cx + L / 2 - 8
    out = []
    for i in range(n + 1):
        u = i / n
        out.append((x0 + (x1 - x0) * u, y, cz + sign * arm * math.sin(math.pi * u)))
    return out


def mzm(m, parent, name, cx, cz, L, arm, y, ln=False):
    g = empty(name, parent)
    mt = "ph_ln" if ln else "ph_wg"
    r = 0.9 if ln else 0.6
    yw = y + 1.0
    lo = (cx - L / 2 - 6, yw, cz)
    ro = (cx + L / 2 + 6, yw, cz)
    x0, x1 = cx - L / 2 + 8, cx + L / 2 - 8
    pin = [lo, (x0, yw, cz)]
    pout = [(x1, yw, cz), ro]
    wg(m, g, f"{name}_in", pin, r, mt)
    wg(m, g, f"{name}_out", pout, r, mt)
    arms, elec = {}, {}
    eg = empty(f"{name}_elec", g)
    for sign in (1, -1):
        pts = arm_pts(cx, cz, L, arm, sign, yw)
        arms[sign] = pts
        wg(m, g, f"{name}_arm{sign}", pts, r, mt)
        grp = empty(f"{name}_e{sign}", eg)
        for dz, tag in ((2.6, "sig"), (-2.6, "gnd")):
            e = [(x, yw + 0.5, z + dz * sign) for (x, _, z) in pts[7:-7]]
            polyline(f"{name}_e{sign}{tag}", e, 0.7, m["ph_gold"], grp)
        elec[sign] = grp
    top = arms[1][len(arms[1]) // 2]
    bot = arms[-1][len(arms[-1]) // 2]
    return {
        "in": pin, "out": pout, "arms": arms, "elec": elec, "group": g,
        "pts": {
            "in": (lo[0] + 4.0, yw + 2.0, cz), "split": (x0, yw + 2.0, cz),
            "top": (top[0], yw + 3.0, top[2]), "bot": (bot[0], yw + 3.0, bot[2]),
            "recomb": (x1, yw + 2.0, cz), "out": (ro[0] - 3.0, yw + 2.0, cz),
        },
    }


def module(m, parent, name, c, w, h, d, cut=True):
    g = empty(name, parent)
    x, y, z = c
    hw, hd = w / 2, d / 2
    bx(f"{name}_base", (x - hw, y, z - hd), (x + hw, y + 0.8, z + hd), m["ph_case"], g)
    for k, (xa, xb, za, zb) in enumerate(((x - hw, x - hw + 0.8, z - hd, z + hd),
                                          (x + hw - 0.8, x + hw, z - hd, z + hd),
                                          (x - hw, x + hw, z - hd, z - hd + 0.8),
                                          (x - hw, x + hw, z + hd - 0.8, z + hd))):
        bx(f"{name}_w{k}", (xa, y, za), (xb, y + h, zb), m["ph_case"], g)
    if not cut:
        bx(f"{name}_lid", (x - hw, y + h, z - hd), (x + hw, y + h + 0.8, z + hd), m["ph_case"], g)
    return g


def pcb(m, parent, name, x0, x1, z0, z1, y=0.0):
    return bx(name, (x0, y, z0), (x1, y + 1.6, z1), m["ph_pcb"], parent)


def dsp(m, parent, name, c, w, d, h=1.2):
    x, y, z = c
    return bx(name, (x - w / 2, y, z - d / 2), (x + w / 2, y + h, z + d / 2), m["ph_dsp"], parent)


def fiber(m, parent, name, pts, r=0.45):
    return polyline(name, pts, r, m["ph_fiber"], parent)


def laser(m, parent, name, c, col, size=3.0):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_die", (x - size, y, z - size), (x + size, y + size * 0.8, z + size), m["ph_si"], g)
    bx(f"{name}_facet", (x + size - 0.4, y + 0.4, z - size * 0.4), (x + size + 0.2, y + size * 0.5, z + size * 0.4), m[col], g)
    return g


def awg(m, parent, name, c, w, d, h, n):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_box", (x - w / 2, y, z - d / 2), (x + w / 2, y + h, z + d / 2), m["ph_si"], g)
    ports = []
    for k in range(n):
        zk = z - d / 2 + d * (k + 0.5) / n
        bx(f"{name}_p{k}", (x + w / 2 - 0.2, y + h * 0.4, zk - 0.5), (x + w / 2 + 1.2, y + h * 0.6, zk + 0.5), m["ph_port"], g)
        ports.append((x + w / 2 + 1.2, y + h * 0.5, zk))
    return {"group": g, "ports": ports, "in": (x - w / 2 - 1.2, y + h * 0.5, z)}


def switch_panel(m, parent, name, x0, x1, y0, y1, z, cols=8, rows=2):
    g = empty(name, parent)
    bx(f"{name}_face", (x0, y0, z - 1.6), (x1, y1, z), m["ph_front"], g)
    for r in range(rows):
        for c in range(cols):
            px = x0 + (x1 - x0) * (c + 0.5) / cols
            py = y0 + (y1 - y0) * (r + 0.5) / rows
            bx(f"{name}_s{r}_{c}", (px - 1.2, py - 0.9, z), (px + 1.2, py + 0.9, z + 0.6), m["ph_port"], g)
    return g


def tfln_xsec(m, parent, name, cx, cy, cz, length, w=2.4):
    g = empty(name, parent)
    x0, x1 = cx - length / 2, cx + length / 2
    bx(f"{name}_si", (x0, cy - 4.0, cz - 6.0), (x1, cy, cz + 6.0), m["ph_si"], g)
    bx(f"{name}_ox", (x0, cy, cz - 6.0), (x1, cy + 2.0, cz + 6.0), m["ph_oxide"], g)
    bx(f"{name}_film", (x0, cy + 2.0, cz - 3.5), (x1, cy + 2.6, cz + 3.5), m["ph_ln"], g)
    ridge = bx(f"{name}_ridge", (x0, cy + 2.6, cz - w / 2), (x1, cy + 3.8, cz + w / 2), m["ph_ln"], g)
    elec = empty(f"{name}_elec", g)
    for k, sgn in enumerate((-1, 1)):
        ez = cz + sgn * (w / 2 + 1.8)
        bx(f"{name}_el{k}", (x0, cy + 2.6, ez - 0.9), (x1, cy + 3.6, ez + 0.9), m["ph_gold"], elec)
    field = empty(f"{name}_field", g)
    for j, xf in enumerate([x0 + length * (i + 0.5) / 8 for i in range(8)]):
        bx(f"{name}_fl{j}", (xf - 0.2, cy + 3.8, cz - w * 0.9), (xf + 0.2, cy + 4.6, cz + w * 0.9), m["ph_violet"], field)
    pts = {"ridge": (cx, cy + 4.0, cz), "elec": (cx, cy + 3.6, cz + w / 2 + 1.8), "film": (cx, cy + 2.4, cz - 3.5),
           "sub": (cx, cy - 2.0, cz)}
    return {"group": g, "ridge": ridge, "elec": elec, "field": field, "pts": pts}


def front(m, parent, name, c, size=1.0):
    x, y, z = c
    return bx(name, (x - 40 * size, y - 2.0, z - 1.0), (x + 40 * size, y, z), m["ph_front"], parent)
