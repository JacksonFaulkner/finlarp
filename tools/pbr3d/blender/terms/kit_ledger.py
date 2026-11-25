"""Shared parts for the finance and policy term scenes (family: market-ledger).

Used by trm_capex, trm_backlog, trm_design_win. Every builder takes a materials dict `m` (from
C.setup, plus ldg_materials) and a parent, and returns an empty group (or a pivot for things that
animate). Points are poly coordinates (x, y up, z toward the camera); use P() from sand_overview
to convert. API list, also in scratchpad/kit_api/ledger.md:

  ldg_materials(m)                          add the ldg_* materials (gold, red and blue glows, paper)
  coin_stack(m, parent, name, c, n, r, h)   n coins standing on c, upward; returns group
  coin_row(m, parent, name, x0, z, step, heights, r, h)
                                            side-by-side stacks, heights = list of coin counts
  ledger_bar(m, root, name, x, z, w, heights, mt)
                                            bar on the floor at (x, z); heights = {beat: height}, the
                                            bar steps to each height at that beat's start; returns pivot
  gauge(m, parent, name, x, z, h, ticks)    vertical glass column with tick marks; returns group
  ledger_sheet(m, parent, name, c, w, h, lines)
                                            a paper sheet standing upright, facing +z, with ink
                                            lines; returns group
  order_stack(m, parent, name, c, cols, rows, mt)
                                            grid of order crates standing on c; returns group
  socket(m, parent, name, c, w, d, h, pins) a dark socket frame with pin rows on c; returns group
  slide(obj, b, p0, p1, u0, u1)             moves obj from poly point p0 to p1 across beat b (fractions
                                            u0..u1); keyed, linear
  pipe(m, root, name, pts, mt, r)           a round pipe through pts (no flow); returns the curve object
"""

from sand_overview import F, P, empty, key, mat, pivot, tube  # noqa: E402
from power_vrm_detail import bx, join, polyline  # noqa: E402


def ldg_materials(m):
    m["ldg_gold"] = mat("ldg_gold", (0.90, 0.72, 0.30), metal=0.95, rough=0.22)
    m["ldg_gold_b"] = mat("ldg_gold_b", (1.0, 0.82, 0.35), emit=(1.0, 0.78, 0.30), strength=2.0)
    m["ldg_red_b"] = mat("ldg_red_b", (1.0, 0.30, 0.20), emit=(1.0, 0.28, 0.18), strength=3.0)
    m["ldg_blue_b"] = mat("ldg_blue_b", (0.35, 0.70, 1.0), emit=(0.30, 0.65, 1.0), strength=2.5)
    m["ldg_paper"] = mat("ldg_paper", (0.92, 0.90, 0.84), rough=0.8)
    m["ldg_glass"] = mat("ldg_glass", (0.55, 0.75, 0.85), rough=0.1, alpha=0.35)
    m["ldg_crate"] = mat("ldg_crate", (0.55, 0.40, 0.25), rough=0.8)
    return m


def coin_stack(m, parent, name, c, n, r=3.0, h=0.7, mt="ldg_gold"):
    """n coins stacked upward from c (x, y, z); one joined mesh."""
    g = empty(name, parent)
    parts = []
    for k in range(n):
        y = c[1] + k * h
        parts.append(tube(f"{name}_c{k}", (c[0], y, c[2]), (c[0], y + h * 0.8, c[2]), r, m[mt], g, 24))
    if parts:
        join(parts, f"{name}_m")
    return g


def coin_row(m, parent, name, x0, z, step, heights, r=3.0, h=0.7, mt="ldg_gold"):
    """Stacks of coins in a row from x0 along x, `step` apart; heights = coin counts."""
    g = empty(name, parent)
    for k, n in enumerate(heights):
        coin_stack(m, g, f"{name}_s{k}", (x0 + k * step, 0.0, z), n, r, h, mt)
    return g


def ledger_bar(m, root, name, x, z, w, heights, mt):
    """A floor bar of width w at (x, z). heights = {beat: height}: the bar scales to each height at
    the start of its beat and holds it. Returns the pivot empty (scales about its foot)."""
    at = (x, 0.0, z)
    pv = pivot(name, at, root)
    bx(f"{name}_b", (x - w / 2 - x, 0.0, z - w / 2 - z), (x + w / 2 - x, 1.0, z + w / 2 - z), m[mt], pv)
    prev = None
    for b, h in sorted(heights.items()):
        hv = max(h, 1e-4)
        if prev is not None:
            key(pv, F(b, 0.05), "scale", (1.0, 1.0, max(prev, 1e-4)), linear=True)
        prev = h
        key(pv, F(b, 0) if b == 0 else F(b, 0.15), "scale", (1.0, 1.0, hv), linear=True)
        key(pv, F(b, 0.45), "scale", (1.0, 1.0, hv), linear=True)
    return pv


def gauge(m, parent, name, x, z, h, ticks=5):
    """A vertical glass column with `ticks` tick marks on its right; the fill is a ledger_bar."""
    g = empty(name, parent)
    parts = [bx(f"{name}_col", (x - 2.0, 0.0, z - 2.0), (x + 2.0, h, z + 2.0), m["ldg_glass"], g)]
    for k in range(ticks + 1):
        y = h * k / ticks
        parts.append(bx(f"{name}_t{k}", (x + 2.0, y - 0.4, z + 1.0), (x + 4.0, y + 0.4, z + 1.6), m["ink"], g))
    join(parts, f"{name}_m")
    return g


def ledger_sheet(m, parent, name, c, w, h, lines=6):
    """A paper sheet standing upright on the plane z = c[2], centred on c, with ink lines."""
    g = empty(name, parent)
    x, y, z = c
    parts = [bx(f"{name}_p", (x - w / 2, y - h / 2, z), (x + w / 2, y + h / 2, z + 0.5), m["ldg_paper"], g)]
    for k in range(lines):
        yy = y + h / 2 - 3.0 - k * (h - 6.0) / max(lines - 1, 1)
        parts.append(bx(f"{name}_l{k}", (x - w / 2 + 2.5, yy - 0.5, z + 0.5), (x + w / 2 - 2.5, yy + 0.5, z + 0.8), m["ink"], g))
    join(parts, f"{name}_m")
    return g


def order_stack(m, parent, name, c, cols, rows, mt="ldg_crate", s=4.0):
    """A grid of crates standing on c: cols along x, rows along z, each s wide and s tall."""
    g = empty(name, parent)
    parts = []
    x0, y0, z0 = c
    for i in range(cols):
        for j in range(rows):
            x = x0 + (i - cols / 2) * (s + 0.8)
            z = z0 + (j - rows / 2) * (s + 0.8)
            parts.append(bx(f"{name}_{i}{j}", (x - s / 2, y0, z - s / 2), (x + s / 2, y0 + s, z + s / 2), m[mt], g))
    if parts:
        join(parts, f"{name}_m")
    return g


def socket(m, parent, name, c, w, d, h, pins=8):
    """A dark socket frame of w x d x h standing on c, with a row of pins along each long side."""
    g = empty(name, parent)
    x, y, z = c
    parts = [bx(f"{name}_f", (x - w / 2, y, z - d / 2), (x + w / 2, y + h, z + d / 2), m["dark"], g)]
    for k in range(pins):
        px = x - w / 2 + 2.0 + k * (w - 4.0) / max(pins - 1, 1)
        for side in (-1, 1):
            pz = z + side * (d / 2 - 1.0)
            parts.append(bx(f"{name}_p{k}{side}", (px - 0.4, y - 1.5, pz - 0.4), (px + 0.4, y + h * 0.5, pz + 0.4), m["gold"], g))
    join(parts, f"{name}_m")
    return g


def slide(obj, b, p0, p1, u0=0.0, u1=0.6):
    """Move obj from poly point p0 to p1 across beat b (fractions u0..u1); holds p1 afterwards."""
    key(obj, F(b, u0), "location", P(*p0), linear=True)
    key(obj, F(b, u1), "location", P(*p1), linear=True)


def pipe(m, root, name, pts, mt="steel", r=2.4):
    """A round pipe through pts (poly points), as one curve; returns it."""
    return polyline(name, pts, r, m[mt], root)
