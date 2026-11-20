"""The PACKAGE node page's overview (the back end, after PICK), in the picture-and-panel template,
built the same way as power_grid_overview.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/package_overview.py

Writes blender/package_overview.blend and assets/package_overview.glb. One beat is 8 s.

One package, taken apart beat by beat (geometry from pkg_kit, the PACKAGING tab's shared kit, which
this script imports but does not change): a wire-bonded die on a leadframe, a flip-chip die on a
substrate piece, a clear mould over the wire-bond die, the organic substrate with its C4 and BGA
balls on the board, an HBM stack with a data bead climbing a TSV, a GPU die and HBM stacks on one
silicon interposer, and the lid and cold plate lowering onto the stack.

Beats (match the seven beats in diagrams_nodes/package/overview.rs):
  0 a package       the whole stack: board, substrate, interposer, die, HBM stacks
  1 die attach      wire bond on the left (gold wires to pads); flip chip on the right (solder bumps)
  2 mould           the wire-bond die sealed in clear mould; underfill fills the flip-chip gap
  3 substrate       the organic substrate with its C4 bumps and BGA balls, on the board
  4 HBM stack       the stack alone, with a data bead climbing one TSV
  5 CoWoS           GPU die and HBM stacks on one interposer; data runs under the die
  6 lid             the lid and cold plate lower onto the stack: the package is closed
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, ball, tube, show, label, beat, fly  # noqa: E402
from sand_zooms import start, camera, finish  # noqa: E402
from pbr_kit import mat, empty  # noqa: E402
import pkg_kit as K  # noqa: E402

PAGE = "package"
NAME = "overview"
BEATS = 7

PANE = 0.53  # the share of the left pane a subject fills (as in power_grid_detail.frame)


def frame(c, size, yaw=0.35, pitch=0.22, pad=1.12, min_d=90.0):
    """A pose that fits a subject `size` mm across, centred on c, in the left pane."""
    return (tuple(c), max(size / PANE * pad, min_d), yaw, pitch)


POSES = [
    frame((0.0, 4.0, 0.0), 90.0, 0.45, 0.30),  # beat 0: the whole stack
    frame((0.0, 3.0, 0.0), 120.0, 0.30, 0.30),  # beat 1: wire bond and flip chip side by side
    frame((-40.0, 5.0, 0.0), 80.0, 0.40, 0.22),  # beat 2: the mould over the wire-bond die
    frame((0.0, -4.0, 0.0), 110.0, 0.55, 0.25),  # beat 3: the substrate and its balls
    frame((18.0, 4.0, 0.0), 60.0, 0.55, 0.20),  # beat 4: one HBM stack
    frame((0.0, 2.0, 0.0), 95.0, 0.50, 0.28),  # beat 5: the interposer
    frame((0.0, 6.0, 0.0), 120.0, 0.35, 0.30),  # beat 6: the lid closes
]

LID_DROP = 25.0  # mm the lid starts above the stack in beat 6


def materials():
    m = K.materials()
    m["gold"] = mat("pkg_gold_wire", (0.95, 0.72, 0.30), metal=0.9, rough=0.3)
    m["mould"] = mat("pkg_mould_clear", (0.30, 0.30, 0.34), rough=0.35, alpha=0.3)
    return m


def wire_bond(m, g):
    """A leadframe pad with a die glued face-up on epoxy, and four gold wires from its bond pads
    up and over to the pad's bond sites."""
    box("wb_pad", (-62.0, -1.0, -18.0), (-18.0, 0.0, 18.0), m["copper"], g)
    box("wb_epoxy", (-52.5, 0.0, -10.5), (-27.5, 0.3, 10.5), m["underfill"], g)
    box("wb_die", (-52.0, 0.3, -10.0), (-28.0, 4.3, 10.0), m["die"], g)
    for k, z in enumerate((-6.0, -2.0, 2.0, 6.0)):
        box(f"wb_bp{k}", (-31.0, 4.3, z - 1.0), (-29.0, 4.6, z + 1.0), m["copper"], g)
        tube(f"wb_wire{k}a", (-30.0, 4.5, z), (-25.0, 9.0, z), 0.3, m["gold"], g, 8)
        tube(f"wb_wire{k}b", (-25.0, 9.0, z), (-20.0, 0.5, z), 0.3, m["gold"], g, 8)


def flip_chip(m, g):
    """A die flipped face-down over a substrate piece, joined to it by a grid of solder bumps."""
    box("fc_sub", (18.0, -2.0, -18.0), (62.0, 0.0, 18.0), m["substrate"], g)
    for i, x in enumerate(range(24, 53, 4)):
        for j, z in enumerate(range(-10, 11, 5)):
            ball(f"fc_bump{i}_{j}", (float(x), 1.0, float(z)), 0.8, m["solder"], g, 12)
    box("fc_die", (22.0, 2.0, -14.0), (58.0, 5.5, 14.0), m["die"], g)


def flip_underfill(m, g):
    """The epoxy that fills the gap under the flipped die, around the bumps."""
    box("fc_underfill", (23.0, 0.0, -15.0), (57.0, 2.0, 15.0), m["underfill"], g)


def mould(m, g):
    """Clear mould sealing the wire-bond die and its wires."""
    box("mould", (-66.0, -1.0, -24.0), (-16.0, 12.0, 24.0), m["mould"], g)


def stack_base(m, g):
    """The board, the BGA balls under the substrate, the substrate itself, and its C4 bumps."""
    K.board(m, g)
    K.bga(m, g)
    K.substrate(m, g)
    K.c4(m, g)


def chips(m, g):
    """The interposer with its microbumps, the GPU die, the HBM stacks, and the underfill rim."""
    K.package(m, g)
    K.underfill_rim(m, g)


def lid_parts(m, g):
    K.lid(m, g)
    K.cold_plate(m, g)


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = materials()

    # beats 1-2: the two die-attach examples, side by side
    wb = empty("pk_wire_bond", root)
    wire_bond(m, wb)
    show(wb, [(F(1, 0), F(3, 0))])

    fc = empty("pk_flip_chip", root)
    flip_chip(m, fc)
    show(fc, [(F(1, 0), F(3, 0))])

    uf = empty("pk_flip_underfill", root)
    flip_underfill(m, uf)
    show(uf, beat(2))

    mo = empty("pk_mould", root)
    mould(m, mo)
    show(mo, beat(2))

    # the full package, and the substrate on its own
    base = empty("pk_base", root)
    stack_base(m, base)
    show(base, [(F(0, 0), F(1, 0)), (F(3, 0), F(4, 0)), (F(5, 0), F(7, 0))])

    ch = empty("pk_chips", root)
    chips(m, ch)
    show(ch, [(F(0, 0), F(1, 0)), (F(4, 0), F(7, 0))])

    # beat 4: a data bead climbs the TSV of the right-hand stack, and one on the left
    for k, sgn in enumerate((1.0, -1.0)):
        bead = ball(f"pk_tsv_bead{k}", (0.0, 0.0, 0.0), 0.5, m["data"], root, 12)
        x = sgn * 18.375
        show(bead, beat(4))
        fly(bead, [(x, 2.4, 9.0), (x, 6.6, 9.0)], F(4, 0.1 + 0.1 * k), F(4, 0.9))

    # beat 5: data runs from stack to stack under the die
    for k, z in enumerate((-9.0, -3.0, 3.0, 9.0)):
        bead = ball(f"pk_data_bead{k}", (0.0, 0.0, 0.0), 0.6, m["data"], root, 12)
        show(bead, beat(5))
        fly(bead, [(-14.5, 2.0, z), (14.5, 2.0, z)], F(5, 0.1 + 0.05 * k), F(5, 0.9))

    # beat 6: the lid and cold plate lower onto the stack
    lid = empty("pk_lid", root)
    lid_parts(m, lid)
    show(lid, beat(6))
    fly(lid, [(0.0, LID_DROP, 0.0), (0.0, 0.0, 0.0)], F(6, 0.05), F(6, 0.45))

    tags = {
        0: [("board", (40.0, -8.0, 40.0)), ("organic substrate", (34.0, -2.0, 0.0)),
            ("silicon interposer", (-24.0, 1.6, -24.0)), ("HBM stacks", (18.4, 6.6, 9.0)),
            ("GPU die", (0.0, 4.2, 0.0))],
        1: [("wire bond: gold wire to pads", (-40.0, 9.5, 0.0)), ("flip chip: solder bumps", (40.0, 7.0, 0.0))],
        2: [("mould compound seals the die", (-40.0, 12.5, 0.0)), ("underfill fills the gap", (40.0, 2.0, 16.0))],
        3: [("BGA balls to the board", (0.0, -7.0, 28.0)), ("C4 bumps", (-34.0, -1.0, 0.0)),
            ("organic substrate, many layers", (34.0, -2.0, 0.0))],
        4: [("DRAM dies", (22.25, 4.0, -9.0)), ("TSV through each die", (18.4, 6.6, 9.0)),
            ("base logic die", (22.25, 0.9, 9.0))],
        5: [("interposer: wiring only", (-24.0, 1.6, -24.0)), ("data runs under the die", (0.0, 2.0, 9.0)),
            ("GPU die", (0.0, 4.2, 0.0))],
        6: [("lid and cold plate", (0.0, 12.0, 0.0)), ("package closed", (-24.0, 1.6, -24.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
