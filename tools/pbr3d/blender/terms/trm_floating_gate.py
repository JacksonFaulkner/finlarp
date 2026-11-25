"""TRM_FLOATING_GATE: a NAND cell drawn huge on the bench, cut through its floating gate, then
electrons tunnelled in (program), read by threshold, and pulled back out (erase).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_floating_gate.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_FLOATING_GATE"
BEATS = [
    ("NAND stores each bit as charge on a hidden gate",
     "A NAND flash package holds the bits for an SSD or an AI server's storage. Inside it, each cell is one transistor with "
     "a second gate sitting between the usual gate and the channel. That second gate stores the bit as a charge."),
    ("Cut through: a floating gate sealed in oxide",
     "The floating gate is a conductive poly island with nowhere to go: oxide wraps it on every side, from the thin tunnel "
     "oxide below to the inter-poly dielectric above. The control gate sits on top, and the n+ source and drain sit either "
     "side of the channel."),
    ("Program: electrons tunnel up and get stuck",
     "A high voltage on the control gate pulls electrons up from the channel through the tunnel oxide. Each one that "
     "lands on the floating gate stays there, because the oxide around it is a good insulator."),
    ("Read: the stored charge shifts the threshold",
     "Trapped electrons repel the control gate's field, so the cell needs a higher voltage to switch on. The controller "
     "reads that threshold: a charged cell is a 0 and an empty one is a 1 (or the reverse, by convention)."),
    ("Erase: charge is pulled back out, block by block",
     "Erase reverses the field, so electrons tunnel back out. It happens to a whole block at once, which is why NAND wears "
     "out with cycling. Makers: Micron (MU), Kioxia (285A.T), SanDisk (SNDK), Samsung (005930.KS)."),
]

X0, X1 = 152.0, 246.0
Z0 = -40.0
CX, CZ = (X0 + X1) / 2, -20.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    ctx = K.context(m, root)
    cell = K.cell_fg(m, root, "cell", X0, X1, Z0)
    C.magnify(m, root, ctx["pkg"], (X0 - 2.0, 14.0, CZ))

    chan, fg = cell["chan"], cell["fg"]
    # electrons: a string of them sitting in the floating gate once programmed
    stored = K.electrons(m, root, "stored", [(188.0 + 3.0 * k, 12.0 + 1.0 * (k % 2), -1.5) for k in range(9)], 9, 1.1)
    show(stored, [(F(2, 0.6), F(4, 0.3))])
    # beat 2: program pulse, electrons climb the channel and tunnel through the oxide
    path = K.tunnel_path((chan[0], chan[1], -1.5), (fg[0], fg[1], -1.5), bend=4.0)
    run(root, "prog", path, 4, 0.8, m["nand_e"], 2, 0.15, 0.6, 40)
    # beat 4: erase, electrons pulled back out through the oxide
    back = list(reversed(path))
    run(root, "erase", back, 4, 0.8, m["nand_e"], 4, 0.1, 0.55, 40)

    C.tags(root, {
        0: [("NAND package on the SSD board", ctx["pkg"]), ("controller beside it", (-130.0, 8.0, -80.0)),
            ("one cell, cut open at the bench", (CX, 25.0, CZ))],
        1: [("n+ source", cell["src"]), ("tunnel oxide", cell["tox"]), ("floating gate, sealed in oxide", fg),
            ("control gate on top", cell["cg"])],
        2: [("control gate pulls electrons up", (CX, 10.0, CZ)), ("electrons tunnel through oxide", (CX, 7.0, CZ)),
            ("trapped in the floating gate", fg)],
        3: [("charge raises the threshold", fg), ("threshold read = the bit", cell["cg"]), ("charged vs empty = 0 or 1", (CX, 12.0, CZ))],
        4: [("erase: electrons leave the gate", (CX, 10.0, CZ)), ("wear: oxide degrades per cycle", (CX, 7.0, CZ)),
            ("MU, 285A.T, SNDK, 005930.KS", cell["sub"])],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 20.0, -60.0), 540.0, 0.30, 0.45, pad=1.0),
        frame((CX, 12.0, CZ), 120.0, 0.25, 0.22),
        frame((CX, 12.0, CZ), 110.0, 0.30, 0.25),
        frame((CX, 12.0, CZ), 110.0, 0.20, 0.25),
        frame((CX, 12.0, CZ), 120.0, 0.35, 0.30),
    ], root)


if __name__ == "__main__":
    build()
