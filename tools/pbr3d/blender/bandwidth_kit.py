"""Memory-channel parts for the BANDWIDTH pictures (overview, zooms, sections), in the SAND template
(docs/diagram-pages.md): a processor with its memory controller, DDR channels (ribbons of data
pins) running to DIMMs, data dots streaming along them, an HBM stack on an interposer, and grow
bars for the gauge and the charts. Built on sand_overview.py and poly_overview.py.

Schematic millimetres, Y up, cut-away at z = 0 with the camera on +z. Boxes keep z <= 0 so their
front faces show without a cut. Groups sit at the origin, so absolute poly coordinates work; the
bars use a pivot at their base and children in offsets from it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, empty, key, label, mat, pivot, show, tube  # noqa: E402
from poly_overview import run  # noqa: E402

END = F(40, 0)  # "until the end" for intervals; later than any scene

# A DDR channel: one controller port, its DIMM and the lanes between them.
DIMM_X0, DIMM_LEN, DIMM_H = 600.0, 1300.0, 220.0
PORT_X = -1300.0  # the processor's right face, where the channels leave it
LANE_PITCH, LANE_R = 25.0, 5.0


def mats(m):
    m["substrate"] = mat("substrate", (0.25, 0.20, 0.14), rough=0.9)
    m["cpu"] = mat("processor_die", (0.20, 0.21, 0.24), metal=0.4, rough=0.4)
    m["ctrl"] = mat("memory_controller", (0.85, 0.62, 0.25), metal=0.5, rough=0.35)
    m["pcb"] = mat("dimm_pcb", (0.10, 0.36, 0.18), rough=0.5)
    m["dram"] = mat("dram_chip", (0.07, 0.07, 0.08), rough=0.35)
    m["die"] = mat("silicon_die", (0.55, 0.58, 0.64), metal=0.6, rough=0.3)
    m["interposer"] = mat("interposer", (0.50, 0.42, 0.30), rough=0.8)
    m["copper"] = mat("copper_lane", (0.80, 0.50, 0.30), metal=0.9, rough=0.3)
    m["read"] = mat("read_data", (0.35, 1.0, 0.45), emit=(0.3, 1.0, 0.4), strength=3.0)
    m["write"] = mat("write_data", (1.0, 0.55, 0.15), emit=(1.0, 0.5, 0.1), strength=3.0)
    m["gap"] = mat("gap_marker", (1.0, 0.25, 0.55), emit=(1.0, 0.2, 0.5), strength=3.0)
    m["cyan"] = mat("cyan_bar", (0.25, 0.85, 0.95), emit=(0.2, 0.8, 0.95), strength=1.5)
    m["purple"] = mat("purple_bar", (0.62, 0.42, 0.95), emit=(0.55, 0.35, 0.95), strength=1.5)
    m["pink_bar"] = mat("pink_bar", (1.0, 0.35, 0.60), emit=(1.0, 0.3, 0.55), strength=1.5)
    m["gold"] = mat("gold_mark", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["gold_glow"] = mat("gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["plinth"] = mat("plinth", (0.18, 0.19, 0.23), rough=0.8)
    m["paper"] = mat("paper", (0.90, 0.88, 0.82), rough=0.85)
    m["grey"] = mat("grey_rule", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    m["red"] = mat("red_mark", (0.90, 0.22, 0.18), emit=(0.9, 0.15, 0.1), strength=2.5)
    return m


def grow(obj, keys):
    """Height keys (frame, fraction) on `obj`: Blender's Z is the poly Y (height), linear between
    the keys and held outside them."""
    for f, v in keys:
        key(obj, f, "scale", (1, 1, v), linear=True)


def bar(parent, name, x, z, w, d, h, m, keys, y0=0.0):
    """A bar standing on (x, y0, z), w wide, d deep, h tall at fraction 1; `keys` grow it."""
    b = pivot(name, (x, y0, z), parent)
    box(f"{name}_m", (-w / 2, 0, -d / 2), (w / 2, h, d / 2), m, b)
    grow(b, keys)
    return b


def dots(parent, name, a, b, n, m, beat, u0=0.05, u1=0.6, life=110, size=13, rev=False):
    """`n` data dots launched along the segment a -> b (poly points) during `beat`."""
    pts = [b, a] if rev else [a, b]
    return run(parent, name, n, pts, size, m, beat, u0, u1, life)


def lanes(parent, name, x0, x1, yc, m, n=8, z=-40.0):
    """A ribbon of `n` copper lanes running from x0 to x1, centred on height yc."""
    g = empty(name, parent)
    span = LANE_PITCH * (n - 1)
    for i in range(n):
        y = yc - span / 2 + LANE_PITCH * i
        tube(f"{name}_lane{i}", (x0, y, z), (x1, y, z), LANE_R, m["copper"], g, verts=8)
    return g


def lane_ys(yc, n=8):
    span = LANE_PITCH * (n - 1)
    return [yc - span / 2 + LANE_PITCH * i for i in range(n)]


def dimm(parent, name, yc, m, x0=DIMM_X0, chips=8):
    """A DIMM: a green board along x with `chips` black DRAM packages on its front."""
    g = empty(name, parent)
    box(f"{name}_pcb", (x0, yc - DIMM_H / 2, -40), (x0 + DIMM_LEN, yc + DIMM_H / 2, 0), m["pcb"], g)
    pitch = (DIMM_LEN - 140) / chips
    for k in range(chips):
        cx = x0 + 70 + pitch * k
        box(f"{name}_chip{k}", (cx, yc - 85, 0), (cx + pitch - 40, yc + 85, 50), m["dram"], g)
    return g


def processor(parent, m):
    """The processor package: substrate, die, and the memory controller on its front."""
    g = empty("processor", parent)
    box("substrate", (-1950, -260, -900), (-1250, -200, -80), m["substrate"], g)
    box("die", (-1900, -200, -850), (PORT_X, 1300, -150), m["cpu"], g)
    box("controller", (-1600, 300, -600), (PORT_X, 1100, -100), m["ctrl"], g)
    return g


def hbm(parent, m, x0, x1, y0, z0, z1, dies=8):
    """An HBM stack: a base die, `dies` silicon dies stacked above it, on an interposer."""
    g = empty("hbm", parent)
    box("interposer", (x0 - 120, y0 - 60, z0 - 120), (x1 + 120, y0, z1 + 120), m["interposer"], g)
    box("base_die", (x0, y0, z0), (x1, y0 + 60, z1), m["cpu"], g)
    for k in range(dies):
        y = y0 + 80 + 42 * k
        box(f"die{k}", (x0 + 30, y, z0 + 30), (x1 - 30, y + 28, z1 - 30), m["die"], g)
    return g


def hbm_comb(parent, name, x0, x1, y0, z, n, pitch, m, r=4.0):
    """A dense comb of `n` short wires from x0 to x1 (the interposer's fine wiring)."""
    g = empty(name, parent)
    for i in range(n):
        y = y0 + pitch * i
        tube(f"{name}_w{i}", (x0, y, z), (x1, y, z), r, m["copper"], g, verts=6)
    return g


def steady(beats):
    """Interval covering beats [b0, b1) for show()."""
    return [(F(b0, 0), F(b1, 0)) for b0, b1 in beats]


__all__ = [
    "END", "OFF", "F", "P", "ball", "box", "empty", "key", "label", "pivot", "show", "tube",
    "bar", "dimm", "dots", "grow", "hbm", "hbm_comb", "lanes", "lane_ys", "mats", "processor",
    "steady", "DIMM_X0", "DIMM_LEN", "DIMM_H", "PORT_X",
]
