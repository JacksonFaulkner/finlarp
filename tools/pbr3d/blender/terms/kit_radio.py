"""Telecom-radio kit for the Terms tab: antenna arrays, radio units, beamformer chips, mmWave
modules, towers, small cells and the street or city context they sit in.

Conventions: y is up, antenna panels stand in the x-y plane and face +z (toward the camera by
default). Every part takes a materials dict m (from radio_materials) and a parent, and returns a
group empty or a points dict. Materials it adds are prefixed "radio_".

API (name: args -> returns, one line each)
  radio_materials(m) -> m          add the radio_* materials (patch, beam glows, wall, glass)
  antenna_panel(m, parent, name, c, nx=8, ny=8, pitch=2.2, size=1.3)
      -> {"group", "el": [(x,y,z) per element, row-major], "top", "centre"}
          vertical array board centred on c, element centres in "el"
  aau(m, parent, name, c, w=60, h=40, d=18, nx=8, ny=8)
      -> {"group", "panel": antenna_panel dict, "top", "front"}  active antenna unit (radio box + array)
  transceiver(m, parent, name, c, s=1.0)
      -> {"group", "top"}  one per-element RF chain: small module with a transceiver chip
  beamformer(m, parent, name, c, n=8, s=1.0)
      -> {"group", "top", "pads": [(x,y,z)...]}  phased-array beamformer RFIC, n phase-shifter pads
  aip(m, parent, name, c, s=1.0, n=4)
      -> {"group", "top", "patches": [(x,y,z)...]}  mmWave antenna-in-package, cut open: patch layer over RFIC
  tower(m, parent, name, c, h=180.0, w=18.0)
      -> {"group", "top", "aau_at": (x,y,z)}  macro tower with the AAU fixed at the top
  small_cell(m, parent, name, c, s=1.0)
      -> {"group", "top", "front": (x,y,z)}  street-light small cell
  building(m, parent, name, x0, x1, h, z0, z1, floors=8)
      -> group  glazed block with floor bands (city context)
  phone(m, parent, name, c, s=1.0)
      -> {"group", "top"}  handset with a small antenna module on the back
  beam_paths(origin, target, n=5, spread=6.0, lift=0.0)
      -> [polyline, ...]  n fanned rays from origin toward target (feed run() for beads)
  steer_paths(origin, angles, length=120.0)
      -> [polyline, ...]  rays from origin at the given angles (deg from +y) in the x-y plane
  lobe(m, parent, name, origin, target, width=10.0, n=3)
      -> group  translucent glow cone of thin tubes from origin to target
  ground(m, parent, name, x0, x1, z0, z1, y=0.0)
      -> group  street or site pad under the scene
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, BL]
import sand_overview as O  # noqa: E402
from sand_overview import empty, tube  # noqa: E402
from power_vrm_detail import bx, mat, join, polyline  # noqa: E402


def radio_materials(m):
    m["radio_patch"] = mat("radio_patch", (0.88, 0.70, 0.36), metal=0.9, rough=0.25)
    m["radio_panel"] = mat("radio_panel", (0.12, 0.14, 0.18), metal=0.3, rough=0.45)
    m["radio_fin"] = mat("radio_fin", (0.55, 0.58, 0.62), metal=0.85, rough=0.35)
    m["radio_chip"] = mat("radio_chip", (0.08, 0.08, 0.09), rough=0.6)
    m["radio_pcb"] = mat("radio_pcb", (0.10, 0.22, 0.34), rough=0.6)
    m["radio_steel"] = mat("radio_steel", (0.60, 0.62, 0.66), metal=0.9, rough=0.35)
    m["radio_wall"] = mat("radio_wall", (0.56, 0.54, 0.50), rough=0.85)
    m["radio_glass"] = mat("radio_glass", (0.20, 0.30, 0.40), metal=0.3, rough=0.1)
    m["radio_ground"] = mat("radio_ground", (0.22, 0.22, 0.24), rough=0.9)
    m["radio_beam"] = mat("radio_beam", (0.35, 0.85, 1.0), emit=(0.30, 0.80, 1.0), strength=3.0)
    m["radio_beam2"] = mat("radio_beam2", (0.95, 0.55, 1.0), emit=(0.90, 0.50, 1.0), strength=3.0)
    m["radio_mmw"] = mat("radio_mmw", (0.55, 0.45, 1.0), emit=(0.50, 0.40, 1.0), strength=3.5)
    m["radio_lobe"] = mat("radio_lobe", (0.40, 0.85, 1.0), emit=(0.30, 0.75, 1.0), strength=1.2, alpha=0.35)
    m["radio_hot"] = mat("radio_hot", (1.0, 0.45, 0.15), emit=(1.0, 0.38, 0.10), strength=2.5)
    return m


def antenna_panel(m, parent, name, c, nx=8, ny=8, pitch=2.2, size=1.3):
    """Vertical array in the x-y plane, facing +z. Elements are patches on a dark board."""
    g = empty(name, parent)
    cx, cy, cz = c
    w, h = nx * pitch, ny * pitch
    bx(f"{name}_board", (cx - w / 2, cy - h / 2, cz - 0.6), (cx + w / 2, cy + h / 2, cz), m["radio_panel"], g)
    el = []
    patches = []
    for j in range(ny):
        for i in range(nx):
            x = cx - w / 2 + pitch * (i + 0.5)
            y = cy - h / 2 + pitch * (j + 0.5)
            el.append((x, y, cz + 0.2))
            patches.append(bx(f"{name}_p{i}_{j}", (x - size / 2, y - size / 2, cz), (x + size / 2, y + size / 2, cz + 0.3), m["radio_patch"], g))
    join(patches, f"{name}_patches")
    return {"group": g, "el": el, "top": (cx, cy + h / 2, cz), "centre": (cx, cy, cz)}


def aau(m, parent, name, c, w=60.0, h=40.0, d=18.0, nx=8, ny=8):
    """Active antenna unit: a radio box with fins on its back and the array on its front face."""
    g = empty(name, parent)
    cx, cy, cz = c
    bx(f"{name}_box", (cx - w / 2, cy - h / 2, cz - d / 2), (cx + w / 2, cy + h / 2, cz + d / 2), m["radio_fin"], g)
    fins = []
    for k in range(10):
        x = cx - w / 2 + w * (k + 0.5) / 10
        fins.append(bx(f"{name}_fin{k}", (x - 0.4, cy - h / 2 + 1.0, cz - d / 2 - 5.0), (x + 0.4, cy + h / 2 - 1.0, cz - d / 2), m["radio_panel"], g))
    join(fins, f"{name}_fins")
    panel = antenna_panel(m, g, f"{name}_arr", (cx, cy, cz + d / 2), nx=nx, ny=ny, pitch=min(w, h) / (max(nx, ny) + 1))
    return {"group": g, "panel": panel, "top": (cx, cy + h / 2, cz), "front": (cx, cy, cz + d / 2)}


def transceiver(m, parent, name, c, s=1.0):
    """A small module: PCB, one transceiver chip, a few passives."""
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_pcb", (x - 4 * s, y, z - 3 * s), (x + 4 * s, y + 0.4 * s, z + 3 * s), m["radio_pcb"], g)
    bx(f"{name}_chip", (x - 1.6 * s, y + 0.4 * s, z - 1.6 * s), (x + 1.6 * s, y + 1.2 * s, z + 1.6 * s), m["radio_chip"], g)
    for k in range(3):
        xp = x - 2.8 * s + 2.8 * s * k
        bx(f"{name}_c{k}", (xp - 0.4 * s, y + 0.4 * s, z + 2.4 * s), (xp + 0.4 * s, y + 0.9 * s, z + 3.0 * s), m["alu"], g)
    return {"group": g, "top": (x, y + 1.2 * s, z)}


def beamformer(m, parent, name, c, n=8, s=1.0):
    """Beamformer RFIC: a package with n phase-shifter blocks along its front edge."""
    g = empty(name, parent)
    x, y, z = c
    w = 2.0 * n * s
    bx(f"{name}_pkg", (x - w / 2, y, z - 3.0 * s), (x + w / 2, y + 1.2 * s, z + 3.0 * s), m["radio_chip"], g)
    pads = []
    for k in range(n):
        xp = x - w / 2 + (k + 0.5) * w / n
        bx(f"{name}_ps{k}", (xp - 0.6 * s, y + 1.2 * s, z - 0.8 * s), (xp + 0.6 * s, y + 1.6 * s, z + 0.8 * s), m["radio_steel"], g)
        pads.append((xp, y + 1.6 * s, z))
    return {"group": g, "top": (x, y + 1.6 * s, z), "pads": pads}


def aip(m, parent, name, c, s=1.0, n=4):
    """mmWave antenna-in-package, cut open at the middle: a patch layer on a laminate over an RFIC."""
    g = empty(name, parent)
    x, y, z = c
    half = 3.0 * n * s
    bx(f"{name}_laminate", (x - half, y, z - half), (x + half, y + 0.8 * s, z + half), m["radio_pcb"], g)
    bx(f"{name}_rfic", (x - half * 0.5, y + 0.8 * s, z - half * 0.5), (x + half * 0.5, y + 2.0 * s, z + half * 0.5), m["radio_chip"], g)
    patches = []
    for i in range(n):
        for j in range(n):
            px = x - half + (i + 0.5) * (2 * half / n)
            pz = z - half + (j + 0.5) * (2 * half / n)
            patches.append(bx(f"{name}_pt{i}_{j}", (px - 1.1 * s, y + 0.8 * s + 0.05, pz - 1.1 * s), (px + 1.1 * s, y + 0.8 * s + 0.35 * s, pz + 1.1 * s), m["radio_patch"], g))
    join(patches, f"{name}_patches")
    pts = [(x - half + (i + 0.5) * (2 * half / n), y + 1.2 * s, z) for i in range(n)]
    return {"group": g, "top": (x, y + 2.0 * s, z), "patches": pts}


def tower(m, parent, name, c, h=180.0, w=18.0):
    """Macro tower: a lattice mast on a base, the AAU fixed at the top."""
    g = empty(name, parent)
    x, y, z = c
    legs = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            legs.append(tube(f"{name}_leg{sx}{sz}", (x + sx * w / 2, y, z + sz * w / 2), (x + sx * 1.2, y + h, z + sz * 1.2), 0.9, m["radio_steel"], g, 8))
    for k in range(int(h / 14)):
        yy = y + 14.0 * k
        ww = w * (1 - 0.6 * (yy - y) / h) / 2
        for sz in (-1, 1):
            legs.append(tube(f"{name}_rung{k}{sz}", (x - ww, yy, z + sz * ww), (x + ww, yy, z + sz * ww), 0.35, m["radio_steel"], g, 6))
    join(legs, f"{name}_lattice")
    bx(f"{name}_base", (x - 8, y - 2.0, z - 8), (x + 8, y, z + 8), m["radio_wall"], g)
    return {"group": g, "top": (x, y + h, z), "aau_at": (x, y + h + 10.0, z)}


def small_cell(m, parent, name, c, s=1.0):
    """Street-light small cell: a pole, a dark radio head and a panel on its front."""
    g = empty(name, parent)
    x, y, z = c
    tube(f"{name}_pole", (x, y, z), (x, y + 22.0 * s, z), 0.8 * s, m["radio_steel"], g, 10)
    bx(f"{name}_head", (x - 4 * s, y + 22.0 * s, z - 2.5 * s), (x + 4 * s, y + 28.0 * s, z + 2.5 * s), m["radio_fin"], g)
    panel = antenna_panel(m, g, f"{name}_arr", (x, y + 25.0 * s, z + 2.6 * s), nx=4, ny=3, pitch=1.6 * s, size=0.9 * s)
    return {"group": g, "top": (x, y + 28.0 * s, z), "front": (x, y + 25.0 * s, z + 3.0 * s), "panel": panel}


def building(m, parent, name, x0, x1, h, z0, z1, floors=8):
    g = empty(name, parent)
    bx(f"{name}_body", (x0, 0.0, z0), (x1, h, z1), m["radio_wall"], g)
    bands = []
    for k in range(floors):
        yy = h * (k + 0.5) / floors
        bands.append(bx(f"{name}_win{k}", (x0 - 0.1, yy - 1.2, z1 - 0.1), (x1 + 0.1, yy + 1.2, z1 + 0.2), m["radio_glass"], g))
    join(bands, f"{name}_windows")
    return g


def phone(m, parent, name, c, s=1.0):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_body", (x - 3.6 * s, y, z - 7.5 * s), (x + 3.6 * s, y + 0.8 * s, z + 7.5 * s), m["radio_fin"], g)
    bx(f"{name}_glass", (x - 3.2 * s, y + 0.8 * s, z - 6.8 * s), (x + 3.2 * s, y + 0.9 * s, z + 6.8 * s), m["radio_glass"], g)
    bx(f"{name}_ant", (x - 2.0 * s, y + 0.9 * s, z + 3.0 * s), (x + 2.0 * s, y + 1.2 * s, z + 5.0 * s), m["radio_patch"], g)
    return {"group": g, "top": (x, y + 1.0 * s, z)}


def beam_paths(origin, target, n=5, spread=6.0, lift=0.0):
    """n rays from origin toward target, fanned sideways by up to `spread` units at the far end."""
    out = []
    ox, oy, oz = origin
    tx, ty, tz = target
    for k in range(n):
        f = 0.0 if n == 1 else (k / (n - 1)) * 2 - 1
        ex, ez = tx + f * spread, tz
        mid = ((ox + ex) / 2, (oy + ty) / 2 + lift, (oz + ez) / 2)
        out.append([(ox, oy, oz), mid, (ex, ty, ez)])
    return out


def steer_paths(origin, angles, length=120.0):
    """Rays in the x-y plane from origin; angles in degrees measured from +y toward +x."""
    ox, oy, oz = origin
    out = []
    for a in angles:
        r = math.radians(a)
        out.append([(ox, oy, oz), (ox + length * math.sin(r) * 0.5, oy + length * math.cos(r) * 0.5, oz),
                    (ox + length * math.sin(r), oy + length * math.cos(r), oz)])
    return out


def lobe(m, parent, name, origin, target, width=10.0, n=3):
    """A soft cone: n thin tubes from origin toward target, spread to `width` at the far end."""
    g = empty(name, parent)
    ox, oy, oz = origin
    tx, ty, tz = target
    rays = []
    for k in range(n):
        f = 0.0 if n == 1 else (k / (n - 1)) * 2 - 1
        a = (ox, oy, oz)
        b = (tx + f * width, ty, tz)
        rays.append(tube(f"{name}_r{k}", a, b, 0.5, m["radio_lobe"], g, 8))
    join(rays, f"{name}_rays")
    return g


def ground(m, parent, name, x0, x1, z0, z1, y=0.0):
    g = empty(name, parent)
    bx(f"{name}_pad", (x0, y - 1.0, z0), (x1, y, z1), m["radio_ground"], g)
    return g
