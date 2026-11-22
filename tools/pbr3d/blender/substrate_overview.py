"""The SUBSTRATE overview (PACKAGING tab), in the SAND template (docs/diagram-pages.md).

Run from the repo root (on the worker, or locally):

    blender -b --factory-startup --python tools/pbr3d/blender/substrate_overview.py

Writes blender/substrate_overview.blend and assets/substrate_overview.glb. One beat is 8 s.

Beats (match SUBSTRATE in diagrams_pkg_nodes.rs, S_B):
  0 the substrate under the interposer   the package sits on a brown substrate
  1 C4 bumps on top                      the package lifts; the C4 row shows
  2 build-up layers of ABF and copper    a cut face: a core, 12 build-up copper layers, vias
  3 BGA balls below                      low view into the ball gap under the substrate
  4 power fans in from the board         yellow power planes in the cut layers; power streams
                                         run from the board edge up into the stack
  5 warpage: the big laminate bends      the substrate bows (ends up, middle down)
  6 bigger packages, bigger substrates   a two-die package on a substrate of twice the area
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, box, ball, key, label, beat, show  # noqa: E402
from sand_zooms import start, camera, finish, stream_of  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402
import pkg_kit as K  # noqa: E402

PAGE = "substrate"
NAME = "overview"
BEATS = 7

HALF = 40.0  # the substrate: 80 mm square
BIG_HALF = 56.0  # the two-die substrate: 112 mm square, about twice the area (1.96x)
SUB_MID = (K.SUB_BOT + K.SUB_TOP) / 2  # -4

# The cut face (beat 2, and beat 4 for the power planes): the back half of the substrate, z <= 0.
# A core in the middle, six build-up layers of ABF and copper on each side (12 copper layers).
CORE_BOT, CORE_TOP = -4.5, -3.5
PITCH = 0.25  # one build-up layer: ABF then copper
ABF_T = 0.17
LAYERS_PER_SIDE = 6
VIA_X = tuple(range(-32, 33, 8))
CUT_STRETCH = 3.5  # beat 2: the cut stack drawn 3.5x taller (14 mm) so its layers read

# The warp (beat 5): a row of short segments hinged end to end, bowed with ends up.
N_BEND = 16
W_BEND = 2 * HALF / N_BEND
BEND_A = 0.4  # radians: the slope at each end; the middle sits BEND_A * HALF / 2 (8 mm) lower

POSES = [
    ((0.0, 0.0, 0.0), 120.0, 0.60, 0.30),
    ((0.0, 2.0, 0.0), 130.0, 0.50, 0.30),
    ((0.0, -4.0, 0.0), 58.0, 0.30, 0.10),
    ((0.0, -6.0, 0.0), 85.0, 0.50, 0.05),
    ((30.0, -4.5, 0.0), 70.0, 0.40, 0.12),
    ((0.0, -2.0, 0.0), 140.0, 0.25, 0.20),
    ((0.0, 0.0, 0.0), 170.0, 0.50, 0.30),
]

# Package lift (mm) per beat: 0 at rest, lifted in beat 1, back at rest in beat 2.
TOP_STEPS = [(0, 0.0), (1, 8.0), (2, 0.0)]


def from_beat(k):
    return [(F(k, 0), F(BEATS, 0))]


def until_beat(k):
    return [(F(0, 0), F(k, 0))]


def materials():
    m = K.materials()
    m["abf"] = mat("sub_abf_film", (0.80, 0.66, 0.42), rough=0.55)
    m["cu"] = mat("sub_copper", (0.92, 0.52, 0.26), metal=0.5, rough=0.3)
    m["plane"] = mat("sub_power_plane", (1.0, 0.75, 0.10), emit=(1.0, 0.72, 0.1), strength=3.0)
    m["core"] = m["substrate"]
    return m


def _traces(idx):
    """Copper segments of build-up layer idx: a row along x with gaps, shifted per layer."""
    shift = (idx * 7) % 12
    cuts = [-HALF + shift + 12 * j for j in range(8)]
    cuts = [c for c in cuts if -HALF < c < HALF]
    out, start_x = [], -HALF
    for c in cuts:
        out.append((start_x, c))
        start_x = c + 2.0
    if start_x < HALF - 0.5:
        out.append((start_x, HALF))
    return [s for s in out if s[1] - s[0] > 0.5]


def _layer_bases():
    """(base y, idx) for the 12 build-up layers: six under the core, six over it."""
    out = []
    for k in range(LAYERS_PER_SIDE):
        out.append((K.SUB_BOT + k * PITCH, len(out)))
    for k in range(LAYERS_PER_SIDE):
        out.append((CORE_TOP + k * PITCH, len(out)))
    return out


def cut_layers(m, parent, stretch=1.0, name="cut"):
    """The cut face: the back half (z <= 0) of the substrate, with its core, ABF film, copper
    traces and vias. Copper is the thin bar in each layer; its gaps show the film.
    `stretch` > 1 draws the stack that many times taller about its middle (SUB_MID), so the
    4 mm stack reads at a camera distance the renderer's 40 mm near plane allows."""
    g = empty(name, parent)

    def y(v):
        return SUB_MID + stretch * (v - SUB_MID)

    def bx(n, lo, hi, mm):
        return box(f"{name}_{n}" if stretch != 1.0 else n, (lo[0], y(lo[1]), lo[2]), (hi[0], y(hi[1]), hi[2]), mm, g)

    bx("core", (-HALF, CORE_BOT, -HALF), (HALF, CORE_TOP, 0.0), m["core"])
    for base, idx in _layer_bases():
        bx(f"abf_{idx}", (-HALF, base, -HALF), (HALF, base + ABF_T, 0.0), m["abf"])
        for j, (x0, x1) in enumerate(_traces(idx)):
            bx(f"cu_{idx}_{j}", (x0, base + ABF_T, -HALF), (x1, base + PITCH, 0.0), m["cu"])
    for i, x in enumerate(VIA_X):
        bx(f"via_{i}", (x - 0.6, K.SUB_BOT, -1.0), (x + 0.6, K.SUB_TOP, 0.05), m["cu"])
    return g


def power_planes(m, parent):
    """Yellow power planes: every other copper layer, drawn over its copper (beat 4)."""
    g = empty("planes", parent)
    for base, idx in _layer_bases():
        if idx % 2 == 0:
            box(f"plane_{idx}", (-HALF, base + ABF_T - 0.02, -HALF), (HALF, base + PITCH + 0.02, 0.02), m["plane"], g)
    return g


def bga(m, parent, half=36.0, pitch=7.0, r=1.0):
    """BGA balls wider apart than the C4 row (fan-out), each touching the board and the substrate."""
    g = empty("bga", parent)
    for i, (x, z) in enumerate(K.grid(half, pitch)):
        ball(f"bga_{i}", (x, K.BOARD_TOP + 1.0, z), r, m["solder"], g, 12)
    return g


def bent(m, parent):
    """The substrate as N_BEND segments hinged end to end; each hinge turns the rest of the chain.
    Rest is flat; in beat 5 the chain bows, its ends up and its middle down. Each segment carries
    its own C4 balls so the row bends with it."""
    g = empty("bent", parent)
    pivots = []
    prev = g
    for k in range(N_BEND):
        loc = P(-HALF, SUB_MID, 0) if k == 0 else P(W_BEND, 0, 0)
        piv = empty(f"bend_{k}", prev, loc)
        box(f"sub_seg_{k}", (0, -2.0, -HALF), (W_BEND, 2.0, HALF), m["substrate"], piv)
        pivots.append(piv)
        prev = piv
    for i, (x, z) in enumerate(K.grid(30.0, 5.0)):
        k = min(N_BEND - 1, int((x + HALF) // W_BEND))
        xl = x - (-HALF + k * W_BEND)
        ball(f"c4b_{i}", (xl, K.SUB_TOP + 0.9 - SUB_MID, z), 0.9, m["solder"], pivots[k], 12)
    # Bend: the first hinge tilts the start by BEND_A, each later hinge takes back 2*BEND_A/(N-1),
    # so the tangent runs from -BEND_A at one end to +BEND_A at the other.
    for k, piv in enumerate(pivots):
        th = BEND_A if k == 0 else -2 * BEND_A / (N_BEND - 1)
        key(piv, F(5, 0), "rotation_euler", (0.0, 0.0, 0.0))
        key(piv, F(5, 0.5), "rotation_euler", (0.0, th, 0.0))
        key(piv, F(6, 0) - 1, "rotation_euler", (0.0, th, 0.0))
        key(piv, F(6, 0), "rotation_euler", (0.0, 0.0, 0.0))
    return g, pivots


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = materials()

    # Beats 0, 1, 3: the flat substrate with its C4 row.
    flat = empty("flat", root)
    show(flat, [(F(0, 0), F(2, 0)), (F(3, 0), F(4, 0))])
    K.substrate(m, flat, half=HALF)
    K.c4(m, flat, half=30.0)

    # Beat 2 and beat 4: the cut face of the substrate.
    # Beat 2 shows the stack stretched CUT_STRETCH times taller (exploded) so the layers read.
    cut_big = cut_layers(m, root, stretch=CUT_STRETCH, name="cut_big")
    show(cut_big, [(F(2, 0), F(3, 0))])
    cut = cut_layers(m, root)
    show(cut, [(F(4, 0), F(5, 0))])
    planes = power_planes(m, root)
    show(planes, [(F(4, 0), F(5, 0))])

    # Beat 5: the bowing substrate.
    bent_g, pivots = bent(m, root)
    show(bent_g, [(F(5, 0), F(6, 0))])

    # The package on top (small interposer, die, four stacks): beats 0, 1 and 3 (lifted in beat 1).
    top = empty("top", root)
    show(top, [(F(0, 0), F(2, 0)), (F(3, 0), F(4, 0))])
    K.interposer(m, top, half=26.0)
    K.die(m, top)
    K.stacks(m, top, zs=(-9.0, 9.0))
    _lift(top, TOP_STEPS)

    # Board and BGA below the substrate, in every beat: the substrate always sits on its board.
    board_grp = empty("board_grp", root)
    show(board_grp, [(F(0, 0), F(BEATS, 0))])
    K.board(m, board_grp)
    bga(m, board_grp)

    # Bigger package and substrate, beat 6 only.
    big = empty("big", root)
    show(big, from_beat(6))
    K.substrate(m, big, half=BIG_HALF)
    K.c4(m, big, half=44.0)
    K.interposer(m, big, half=46.0, name="big_interposer", mat_name="organic")
    K.die(m, big, x0=-13.5, x1=-1.2, name="big_die_l")
    K.die(m, big, x0=1.2, x1=13.5, name="big_die_r")
    K.stacks(m, big, zs=(-21.0, -9.0, 9.0, 21.0))

    # Power in beat 4: four streams leave the board's edge at y = -7 (the BGA layer's top) and
    # climb in front of the cut face into the layers, fanning to four heights of x.
    for k, x_k in enumerate((36.0, 28.0, 20.0, 12.0)):
        dx = x_k - 54.0
        stream_of(root, f"power_{k}", 6, (54.0, -7.0, 0.6), [(0, 0, 0), (dx, 0, 0), (dx, 4.0, 0)],
                  1.2, m["power"], 4, 0.1 + 0.08 * k, 0.5 + 0.08 * k, 48)

    # The bend's tag sits on a segment near x = 30, so it moves with the bend.
    bend_tag_parent = pivots[int((30.0 + HALF) // W_BEND)]

    labels = {
        0: [("substrate under the interposer", (34.0, -2.0, 20.0), root)],
        1: [("C4 bumps on top", (14.0, -1.0, 14.0), root)],
        2: [("ABF and copper build-up layers", (-8.0, -1.0, 0.1), root)],
        3: [("BGA balls below", (20.0, -7.0, 20.0), root),
            ("the board", (10.0, -8.0, 40.0), root)],
        4: [("power fans in from the board", (46.0, -7.0, 0.6), root)],
        5: [("the big laminate bends", (2.5, 2.0, 0.0), bend_tag_parent)],
        6: [("bigger packages, bigger substrates", (-30.0, -2.0, 40.0), root),
            ("two dies on one substrate", (-7.0, 4.2, 0.0), root)],
    }
    for i, items in labels.items():
        for text, at, parent in items:
            label(text, at, parent, beat(i))

    camera(root, POSES)
    return root


def _lift(grp, steps):
    prev = None
    for b, dy in steps:
        if prev is None:
            key(grp, F(b, 0), "location", P(0.0, dy, 0.0))
        else:
            key(grp, F(b, 0), "location", P(0.0, prev, 0.0))
            key(grp, F(b, 0.5), "location", P(0.0, dy, 0.0))
        prev = dy


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
