"""TRM_CHARGE_TRAP: a charge-trap NAND cell drawn huge on the bench. The charge sits in defects inside
one continuous nitride film instead of a conductive floating gate.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_charge_trap.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_CHARGE_TRAP"
BEATS = [
    ("3D NAND stacks the cells: tall towers of word-line layers",
     "Modern NAND builds its cells in a vertical stack of dozens to hundreds of layers, with a channel hole running "
     "through them. Each layer's gate is one cell's control gate on that layer."),
    ("Cut through: electrons caught in traps in a nitride film",
     "A charge-trap cell replaces the conductive floating gate with a silicon nitride film full of defects. Electrons "
     "park in these traps, and the film is continuous, so charge stays local to its trap."),
    ("One defect holds a few electrons; a leak drains only that spot",
     "Because the charge is local, a single defect in the film does not drain the whole cell. That makes the cell more "
     "robust than a floating gate and lets the cells sit closer together."),
    ("Used in most high-layer 3D NAND",
     "Many 3D NAND products use this structure for their high layer counts, since the stacked layers are easier to make "
     "with a continuous film than with isolated poly islands."),
    ("Makers: Samsung, SK Hynix, Kioxia, Lam Research (LRCX)",
     "Samsung (005930.KS), SK Hynix (000660.KS), Kioxia (285A.T) and Lam Research (LRCX) (deposition and etch tools) "
     "make and enable these stacks."),
]

X0, X1 = 152.0, 246.0
Z0 = -40.0
CX, CZ = (X0 + X1) / 2, -20.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    ctx = K.context(m, root)
    stack = K.stack_3d(m, root, "stack", -60.0, 40.0, -150.0, -90.0, 0.0, layers=10, pitch=4.0)
    cell = K.cell_ctf(m, root, "cell", X0, X1, Z0)
    C.magnify(m, root, ctx["pkg"], (X0 - 2.0, 14.0, CZ))
    z = -1.5
    traps_pts = [(CX - 9.0 + 3.0 * (k % 4), 10.5 + 1.2 * (k % 3), z - 3.0 * (k % 2)) for k in range(8)]
    tr = K.traps(m, root, "traps", traps_pts, 0.9)
    show(tr, [(F(2, 0.4), F(5, 0))])
    path = K.tunnel_path((CX, 6.6, z), (CX - 9.0, 10.5, z), bend=3.0)
    run(root, "inj", path, 4, 0.8, m["nand_e"], 1, 0.2, 0.6, 40)
    frame_c = (CX, 12.0, CZ)
    C.tags(root, {
        0: [("3D NAND: stacked word lines", stack["top"]), ("channel hole through layers", stack["hole"][5]),
            ("one cell, cut open at the bench", (CX, 25.0, CZ))],
        1: [("nitride film holds the charge", cell["sin"]), ("tunnel oxide", cell["tox"]), ("control gate on top", cell["cg_top"])],
        2: [("electrons park in defects", cell["trap"]), ("one leak drains one trap", (CX - 9.0, 10.5, z)),
            ("film stays continuous", (CX + 20.0, 11.0, z))],
        3: [("most high-layer NAND", stack["top"]), ("continuous film stacks well", cell["sin"]), ("more layers, more bits", stack["hole"][0])],
        4: [("Samsung 005930.KS", cell["sin"]), ("SK Hynix 000660.KS", cell["cg_top"]), ("LRCX, 285A.T", cell["tox"])],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 40.0, -100.0), 260.0, 0.30, 0.40, pad=1.0),
        frame(frame_c, 120.0, 0.25, 0.22),
        frame(frame_c, 110.0, 0.30, 0.25),
        frame((-10.0, 20.0, -110.0), 220.0, 0.20, 0.35, pad=1.0),
        frame(frame_c, 120.0, 0.35, 0.30),
    ], root)


if __name__ == "__main__":
    build()
