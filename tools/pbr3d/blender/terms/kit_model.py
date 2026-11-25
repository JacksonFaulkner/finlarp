"""Model-family kit for the Terms-tab overviews (trm_mixture_of_experts, trm_tokens, trm_rag, ...).

Every part takes the material dict m (C.setup + materials(m)) and a parent group, and builds real
geometry. Each returns a group empty, plus whatever anchor points or per-part groups the caller
animates (show / run / present). Coordinates are scene units: x right, y up, z to the front; floor
at y = 0.

API
  materials(m)
      Adds m["mdl_*"] materials. Call once after C.setup.
  token_row(m, parent, name, xs, z, size=10.0, mt=None) -> (group, centres)
      A row of token cubes standing on the floor at z; centres sit just above each cube.
  chunk_grid(m, parent, name, c, cols, rows, s=6.0, gap=2.0, mt=None) -> (group, centres)
      A grid of small chunk blocks; c is the grid's floor centre.
  doc_stack(m, parent, name, c, n=6, w=40.0, h=1.2, d=30.0, mt=None) -> (group, top)
      n stacked page slabs rising from floor centre c; top is the top face centre.
  window_strip(m, parent, name, x0, x1, z, h=4.0, cells=20, mt=None) -> (group, cells)
      A long strip cut into cells (a context window); cells[i] is an empty to show per cell.
  router(m, parent, name, c, w=20.0, h=24.0, d=14.0) -> (group, top)
      A gate block with a glowing slot on its front; top is the top centre.
  gpu_tray(m, parent, name, x0, x1, z0, z1, n=8) -> (group, tops)
      A PCB tray with n GPUs in a row (die plus HBM stacks); tops are the GPU top centres (y 6.2).
  expert_row(m, parent, name, x0, x1, z, n, y0=0.0, w=12.0, h=16.0, d=12.0) -> (group, lids, tops)
      n expert blocks in a row from y0. lids[i] is a glowing lid group; show it to light expert i.
      tops are the lid centres (the point to run beads to).
  bar_chart(m, parent, name, x0, z, heights, step=12.0, w=8.0, mt=None, hi=None) -> (group, hi_group, tops)
      Bars on the floor from x0 spaced step; hi_group is a glow over bar hi (show it to highlight).
  panel(m, parent, name, lo, hi, mt=None) -> group
      A flat slab (prompt box, invoice, screen). lo and hi are opposite corners.
  fabric(m, parent, name, tops, h=20.0, mt=None) -> group
      Arcs between every pair of tops (all-to-all link traffic, e.g. NVLink between GPUs).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
for _p in (BL, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from sand_overview import empty, mat  # noqa: E402
from power_vrm_detail import bx, polyline, arc  # noqa: E402


def materials(m):
    m["mdl_steel"] = mat("mdl_steel", (0.45, 0.48, 0.54), metal=0.85, rough=0.3)
    m["mdl_paper"] = mat("mdl_paper", (0.86, 0.84, 0.76), rough=0.7)
    m["mdl_doc"] = mat("mdl_doc", (0.30, 0.42, 0.62), rough=0.5)
    m["mdl_chunk"] = mat("mdl_chunk", (0.50, 0.78, 0.70), rough=0.4)
    m["mdl_token"] = mat("mdl_token", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=2.5)
    m["mdl_bar"] = mat("mdl_bar", (0.55, 0.58, 0.66), metal=0.3, rough=0.4)
    m["mdl_hit"] = mat("mdl_hit", (1.0, 0.85, 0.35), emit=(1.0, 0.80, 0.30), strength=3.0)
    m["mdl_expert"] = mat("mdl_expert", (0.26, 0.36, 0.52), metal=0.4, rough=0.4)
    m["mdl_expert_on"] = mat("mdl_expert_on", (0.45, 0.80, 1.0), emit=(0.40, 0.78, 1.0), strength=2.5)
    m["mdl_gpu"] = mat("mdl_gpu", (0.14, 0.16, 0.22), metal=0.5, rough=0.35)
    m["mdl_hbm"] = mat("mdl_hbm", (0.20, 0.34, 0.62), metal=0.4, rough=0.35)
    m["mdl_pcb"] = mat("mdl_pcb", (0.07, 0.30, 0.16), rough=0.55)
    m["mdl_link"] = mat("mdl_link", (0.40, 1.0, 0.80), emit=(0.35, 1.0, 0.75), strength=3.0)
    m["mdl_cell"] = mat("mdl_cell", (0.30, 0.34, 0.42), metal=0.3, rough=0.5)


def token_row(m, parent, name, xs, z, size=10.0, mt=None):
    g = empty(name, parent)
    centres = []
    for i, x in enumerate(xs):
        bx(f"{name}{i}", (x - size / 2, 0.0, z - size / 2), (x + size / 2, size, z + size / 2), mt or m["mdl_token"], g)
        centres.append((x, size + 1.0, z))
    return g, centres


def chunk_grid(m, parent, name, c, cols, rows, s=6.0, gap=2.0, mt=None):
    g = empty(name, parent)
    x0, _, z0 = c
    pitch = s + gap
    x_start = x0 - (cols - 1) * pitch / 2
    z_start = z0 - (rows - 1) * pitch / 2
    centres = []
    for r in range(rows):
        for k in range(cols):
            x = x_start + k * pitch
            z = z_start + r * pitch
            bx(f"{name}_{r}_{k}", (x - s / 2, 0.0, z - s / 2), (x + s / 2, s, z + s / 2), mt or m["mdl_chunk"], g)
            centres.append((x, s + 1.0, z))
    return g, centres


def doc_stack(m, parent, name, c, n=6, w=40.0, h=1.2, d=30.0, mt=None):
    g = empty(name, parent)
    x, y0, z = c
    for i in range(n):
        y = y0 + i * h
        bx(f"{name}_p{i}", (x - w / 2, y, z - d / 2), (x + w / 2, y + h * 0.8, z + d / 2), mt or m["mdl_paper"], g)
    return g, (x, y0 + n * h, z)


def window_strip(m, parent, name, x0, x1, z, h=4.0, cells=20, mt=None):
    g = empty(name, parent)
    bx(f"{name}_base", (x0, 0.0, z - 6.0), (x1, h, z + 6.0), m["mdl_cell"], g)
    step = (x1 - x0) / cells
    out = []
    for i in range(cells):
        c = empty(f"{name}{i}", g)
        xa = x0 + i * step + 0.8
        bx(f"{name}{i}_f", (xa, h, z - 4.0), (xa + step - 1.6, h + 0.8, z + 4.0), mt or m["mdl_token"], c)
        out.append(c)
    return g, out


def router(m, parent, name, c, w=20.0, h=24.0, d=14.0):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_b", (x - w / 2, y, z - d / 2), (x + w / 2, y + h, z + d / 2), m["mdl_steel"], g)
    bx(f"{name}_slot", (x - w / 2 + 2.0, y + h * 0.55, z + d / 2), (x + w / 2 - 2.0, y + h * 0.7, z + d / 2 + 0.6), m["mdl_expert_on"], g)
    return g, (x, y + h, z)


def gpu_tray(m, parent, name, x0, x1, z0, z1, n=8):
    g = empty(name, parent)
    bx(f"{name}_pcb", (x0, 0.0, z0), (x1, 2.0, z1), m["mdl_pcb"], g)
    step = (x1 - x0) / n
    zc = (z0 + z1) / 2
    s = min(step * 0.30, (z1 - z0) * 0.30)
    tops = []
    for i in range(n):
        x = x0 + step * (i + 0.5)
        bx(f"{name}{i}_sub", (x - step * 0.36, 2.0, zc - s * 1.3), (x + step * 0.36, 3.2, zc + s * 1.3), m["substrate"], g)
        bx(f"{name}{i}_die", (x - s * 0.5, 3.2, zc - s * 0.5), (x + s * 0.5, 6.2, zc + s * 0.5), m["mdl_gpu"], g)
        for side in (-1, 1):
            hx = x + side * s * 0.95
            bx(f"{name}{i}_h{side}", (hx - s * 0.25, 3.2, zc - s * 0.9), (hx + s * 0.25, 5.6, zc + s * 0.9), m["mdl_hbm"], g)
        tops.append((x, 6.2, zc))
    return g, tops


def expert_row(m, parent, name, x0, x1, z, n, y0=0.0, w=12.0, h=16.0, d=12.0):
    g = empty(name, parent)
    lids, tops = [], []
    step = (x1 - x0) / n
    for i in range(n):
        x = x0 + step * (i + 0.5)
        bx(f"{name}{i}_b", (x - w / 2, y0, z - d / 2), (x + w / 2, y0 + h, z + d / 2), m["mdl_expert"], g)
        lid = empty(f"{name}{i}_lid", g)
        bx(f"{name}{i}_lit", (x - w / 2 + 1.0, y0 + h, z - d / 2 + 1.0), (x + w / 2 - 1.0, y0 + h + 1.4, z + d / 2 - 1.0),
           m["mdl_expert_on"], lid)
        lids.append(lid)
        tops.append((x, y0 + h + 1.4, z))
    return g, lids, tops


def bar_chart(m, parent, name, x0, z, heights, step=12.0, w=8.0, mt=None, hi=None):
    g = empty(name, parent)
    hg = empty(f"{name}_hi", parent)
    tops = []
    for i, h in enumerate(heights):
        x = x0 + step * i
        bx(f"{name}{i}", (x, 0.0, z - w / 2), (x + w, h, z + w / 2), mt or m["mdl_bar"], g)
        tops.append((x + w / 2, h + 1.0, z))
        if i == hi:
            bx(f"{name}_hit", (x - 0.4, 0.0, z - w / 2 - 0.4), (x + w + 0.4, h + 0.4, z + w / 2 + 0.4), m["mdl_hit"], hg)
    return g, hg, tops


def panel(m, parent, name, lo, hi, mt=None):
    g = empty(name, parent)
    bx(name, lo, hi, mt or m["mdl_cell"], g)
    return g


def fabric(m, parent, name, tops, h=20.0, mt=None):
    g = empty(name, parent)
    k = 0
    for i in range(len(tops)):
        for j in range(i + 1, len(tops)):
            a, b = tops[i], tops[j]
            polyline(f"{name}_{k}", arc(a, b, h * (1.0 + 0.15 * ((j - i) % 3)), 12), 0.35, mt or m["mdl_link"], g)
            k += 1
    return g
