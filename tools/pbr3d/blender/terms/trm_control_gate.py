"""TRM_CONTROL_GATE: the control gate on top of a NAND cell, drawn huge on the bench. The word line
runs along a row of cells, so one voltage selects every cell in that row.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_control_gate.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_CONTROL_GATE"
BEATS = [
    ("The control gate is the top electrode of each cell",
     "On a NAND die, every cell has a control gate on top of its floating gate (or trap layer). The control gate sets the "
     "voltage that programs, reads or erases that cell."),
    ("Cut through: the control gate sits above the stored charge",
     "The control gate is a metal-filled poly plate. Between it and the floating gate lies the inter-poly dielectric, which "
     "lets the field from the gate reach the charge without leaking it away."),
    ("Word line: one row's control gates share one wire",
     "Control gates in a row connect along one word line. One voltage on that wire selects every cell in the row, so the "
     "controller programs or reads a whole page at once."),
    ("Read or program: the voltage on the gate sets the outcome",
     "A read puts a voltage on the word line and senses which cells conduct. A program pulse drives a higher voltage that "
     "pushes electrons in. The gate voltage, not the cell alone, decides what happens."),
    ("Makers: Micron (MU), Samsung (005930.KS), Kioxia (285A.T), SanDisk (SNDK)",
     "These four makers build NAND dies with control gates in this layout. Their word line wiring is what sets how many "
     "pages a die can address."),
]

X0, X1 = 152.0, 246.0
Z0 = -40.0
CX, CZ = (X0 + X1) / 2, -20.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    ctx = K.context(m, root)
    cell = K.cell_fg(m, root, "cell", X0, X1, Z0)
    wl = K.wordline(m, root, "wl", -40.0, 260.0, -40.0, -30.0, 18.0, 25.0)
    C.magnify(m, root, ctx["pkg"], (X0 - 2.0, 14.0, CZ))
    pulse = K.tunnel_path((CX, 25.0, -2.0), (CX, 16.0, -2.0), bend=0.0)
    run(root, "pgm", pulse, 3, 0.8, m["nand_e"], 3, 0.2, 0.5, 30)
    show(wl, [(F(0, 0.0), F(5, 0))])
    C.tags(root, {
        0: [("NAND package on the SSD board", ctx["pkg"]), ("one cell, cut open at the bench", (CX, 25.0, CZ))],
        1: [("control gate: top electrode", cell["cg"]), ("inter-poly dielectric", (CX + 10.0, 17.0, -2.0)), ("floating gate below", cell["fg"])],
        2: [("word line runs along the row", (-40.0, 22.0, -35.0)), ("one voltage picks the row", (CX, 22.0, -35.0)), ("one page at a time", (240.0, 22.0, -35.0))],
        3: [("read: sense the conduction", cell["cg"]), ("program: high gate pulse", (CX, 22.0, -2.0)), ("gate voltage sets the outcome", cell["fg"])],
        4: [("MU, 005930.KS, 285A.T", cell["cg"]), ("SNDK", (CX, 22.0, -2.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 20.0, -60.0), 540.0, 0.30, 0.45, pad=1.0),
        frame((CX, 16.0, CZ), 120.0, 0.25, 0.22),
        frame((CX, 16.0, CZ), 150.0, 0.30, 0.30),
        frame((CX, 16.0, CZ), 120.0, 0.20, 0.25),
        frame((CX, 16.0, CZ), 120.0, 0.35, 0.30),
    ], root)


if __name__ == "__main__":
    build()
