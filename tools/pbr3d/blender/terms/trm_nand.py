"""TRM_NAND: a NAND package on its board, then a 3D NAND block cut open on the bench: stacked
word lines, a glowing channel hole, a string read top to bottom, and cells written by tunnelling.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_nand.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run, wire, blink, bx  # noqa: E402
from sand_overview import empty, tube  # noqa: E402

SLUG = "TRM_NAND"
BEATS = [
    ("NAND flash keeps data with the power off",
     "A NAND package sits on every SSD board next to its controller. It holds bits as charge trapped in its cells, so "
     "nothing is lost when power drops. AI clusters fill racks of SSDs with it for datasets and checkpoints."),
    ("Inside: cells stacked hundreds of layers high",
     "Modern NAND is 3D: word-line plates are stacked in oxide, 200 to 300+ layers, and a vertical channel hole is "
     "etched through all of them. Each place a plate wraps the hole is one cell."),
    ("A string: the cells share one channel in series",
     "The cells down one hole are wired in series like a string of lights, with a bit line on top and a source at the "
     "bottom. To read one cell, the others are switched fully on and current only flows if the chosen cell conducts."),
    ("Write: electrons tunnel into a layer's charge store",
     "A high voltage on one word line pulls electrons from the channel into that layer's charge-trap film. More stored "
     "charge raises the cell's threshold. Storing 1 to 4 bits per cell (SLC to QLC) means sorting it into 2 to 16 levels."),
    ("Erase is per block, and cycling wears it out",
     "Erase pulls charge out of a whole block at once, so the controller remaps writes and wears cells evenly. "
     "TLC endures about 3,000 cycles, QLC about 1,000. Makers: Samsung (005930.KS), SK hynix (000660.KS), Micron (MU), "
     "Kioxia (285A.T), Sandisk (SNDK)."),
]

X0, X1 = 172.0, 226.0
Z0, Z1 = -24.0, 0.0
CX, CZ = (X0 + X1) / 2, -6.0
LAYERS, PITCH = 8, 4.0


def stack(m, root):
    """A 3D NAND block sliced through its channel hole at z = 0: word-line plates and oxide, a
    charge-trap film lining the hole, and the glowing poly channel down the middle."""
    g = empty("stack", root)
    xc, y0 = CX, 2.0
    bx("st_base", (X0, 0.0, Z0), (X1, y0, Z1), m["nand_sub"], g)
    for k in range(LAYERS):
        y = y0 + k * PITCH
        bx(f"st_ox{k}", (X0, y, Z0), (X1, y + 1.6, Z1), m["nand_ox"], g)
        for a, b in ((X0, xc - 5.0), (xc + 5.0, X1)):
            bx(f"st_wl{k}_{a:.0f}", (a, y + 1.6, Z0), (b, y + PITCH, Z1), m["nand_cg"], g)
    top = y0 + LAYERS * PITCH
    bx("st_cap", (X0, top, Z0), (X1, top + 1.5, Z1), m["nand_ox"], g)
    for s in (-1, 1):
        bx(f"st_sin{s}", (xc + s * 5.0, y0, Z0), (xc + s * 3.6, top, Z1 + 0.2), m["nand_sin"], g)
        bx(f"st_tox{s}", (xc + s * 3.6, y0, Z0), (xc + s * 3.0, top, Z1 + 0.2), m["nand_tox"], g)
    tube("st_chan", (xc, y0, 0.0), (xc, top + 3.0, 0.0), 3.0, m["nand_chan"], g, 16)
    return {"top": (xc, top + 3.0, 0.0), "hole": [(xc, y0 + k * PITCH + 2.8, 0.0) for k in range(LAYERS)]}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    ctx = K.context(m, root)
    st = stack(m, root)
    C.magnify(m, root, ctx["pkg"], (X0 - 2.0, 16.0, CZ))
    top, hole = st["top"], st["hole"]
    hx, hz = top[0], top[2]
    # bit line on top and source line under the block
    wire("bitline", [(X0, top[1] + 1.5, hz), (hx, top[1] + 1.5, hz), (hx, top[1], hz)], 0.9, m["copper"], root)
    wire("srcline", [(X0, 0.8, hz), (X1, 0.8, hz)], 0.9, m["copper"], root)
    # beat 2: read current runs down the string
    run(root, "read", [(X0, top[1] + 1.5, hz), (hx, top[1] + 1.5, hz)] + list(reversed(hole)) + [(hx, 0.8, hz), (X1, 0.8, hz)],
        8, 0.8, m["nand_e"], 2, 0.05, 0.85, 50)
    # beat 3: electrons tunnel from the hole into layer 4's charge store (both sides)
    ly = hole[4][1]
    for s in (-1, 1):
        run(root, f"prog{s}", K.tunnel_path((hx, ly, hz), (hx + s * 4.3, ly, hz), bend=0.6), 3, 0.7, m["nand_e"], 3, 0.1, 0.6, 30)
    stored = K.traps(m, root, "stored", [(hx + s * 4.3, ly - 0.8 + 0.8 * k, 0.6) for s in (-1, 1) for k in range(3)], 0.7)
    show(stored, [(F(3, 0.55), F(4, 0.3))])
    # beat 4: erase, the whole block empties back into the channel
    for i in (1, 3, 5):
        y = hole[i][1]
        run(root, f"erase{i}", [(hx + 4.3, y, 0.6), (hx, y, 0.6)], 2, 0.7, m["nand_e"], 4, 0.05 + 0.1 * (i % 3), 0.7, 25)

    C.tags(root, {
        0: [("NAND package on the SSD board", ctx["pkg"]), ("non-volatile: keeps bits unpowered", (CX, 30.0, CZ))],
        1: [("word-line plates in oxide", (X1 - 6.0, hole[5][1], 0.0)), ("channel hole through every layer", top),
            ("one cell per plate crossing", (CX - 8.0, hole[3][1], 0.0))],
        2: [("bit line on top", (X0 + 8.0, top[1] + 2.0, hz)), ("cells in series down the hole", hole[4]),
            ("source line at the bottom", (X1 - 8.0, 1.0, hz))],
        3: [("word line at program voltage", (hx + 14.0, ly, 0.0)), ("electrons tunnel into the trap film", (hx, ly, hz)),
            ("1-4 bits = 2-16 charge levels", (CX, top[1] + 8.0, CZ))],
        4: [("erase: whole block at once", hole[2]), ("TLC ~3k, QLC ~1k cycles", (CX, top[1] + 8.0, CZ)),
            ("005930.KS, MU, 285A.T, SNDK", (CX, 1.0, CZ))],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 20.0, -60.0), 540.0, 0.30, 0.45, pad=1.0),
        frame((CX, 18.0, CZ), 75.0, 0.40, 0.22),
        frame((CX, 18.0, CZ), 70.0, 0.25, 0.15),
        frame((CX, 20.0, CZ), 50.0, 0.20, 0.12),
        frame((CX, 18.0, CZ), 75.0, 0.45, 0.22),
    ], root)


if __name__ == "__main__":
    build()
