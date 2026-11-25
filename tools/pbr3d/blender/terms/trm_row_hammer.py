"""TRM_ROW_HAMMER: the Terms-tab overview for DRAM row hammer, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_row_hammer.py

Writes assets/term_TRM_ROW_HAMMER.glb. Captions live in specs/terms/TRM_ROW_HAMMER.json.

One HBM bank drawn large on the bench. The aggressor row (4) is opened and closed over and over:
its wordline flashes, coupling beads leak into the victim rows 3 and 5, and before the 64 ms
refresh bar fills, a few victim cells flip (red). Last beat: target row refresh rewrites the
victims and the attack stalls.

Beats:
  0 hbm      HBM stacks beside the GPU, one bank lifted onto the bench
  1 rows     rows sit tens of nanometres apart; every cell leaks and is refreshed every 64 ms
  2 hammer   row 4 opened and closed thousands of times: wordline flashes, charge leaks into 3 and 5
  3 flip     victim cells flip before refresh comes round
  4 defend   TRR / ECC refresh the victims; costs bandwidth
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F, empty, show  # noqa: E402
from power_vrm_detail import blink, bx, frame, present, run  # noqa: E402

SLUG = "TRM_ROW_HAMMER"
BEATS = [
    ("HBM and DRAM store every bit as charge in a dense grid",
     "The GPU's HBM stacks are DRAM: each die holds banks of cells, one tiny capacitor and one transistor per bit. "
     "Rows are packed tens of nanometres apart, and shrinking that gap is how DRAM gets denser each generation."),
    ("Every cell leaks, so DRAM refreshes each row every 64 ms",
     "A cell's charge drains away over time, so the chip reads and rewrites every row inside a refresh window, "
     "usually 64 ms. As long as nothing drains a cell faster than that, the data survives."),
    ("Hammering one row disturbs its neighbours",
     "Row hammer opens and closes the same aggressor row hundreds of thousands of times inside one refresh window. "
     "Each ACTIVATE swings the wordline, and electrical coupling plus trapped charge pull a little charge out of cells "
     "in the rows on either side."),
    ("Victim cells flip before refresh comes round",
     "If enough charge leaks before the victim row is refreshed, the sense amp reads the wrong value and a bit flips. "
     "Newer, denser DRAM flips after fewer hammers. Since a program can hammer rows it owns to flip bits it does not "
     "own, this is a security hole as well as a reliability one."),
    ("Defenses refresh the victims early, at a cost",
     "DRAM chips add target row refresh, which counts activations and refreshes neighbours of hot rows; DDR5 and HBM3 "
     "add refresh management, and servers add ECC to catch flips that slip through. Every extra refresh takes bank "
     "time away from real reads. Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS), Rambus (RMBS)."),
]

BX0, BX1, BZ0, BZ1 = 160.0, 236.0, -76.0, -28.0
ROWS, COLS = 8, 12
AGG = 4
VICT = (3, 5)
FLIPS = [(3, 2), (3, 7), (5, 4), (5, 9), (3, 10)]


def cell_box(m, parent, name, pts, r, c, mt, grow=0.15):
    x, y, z = pts["cell"](r, c)
    return bx(name, (x - 0.7 - grow, y - 7.0 - grow, z - 0.7 - grow), (x + 0.7 + grow, y + grow, z + 0.7 + grow), m[mt], parent)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=ROWS, cols=COLS)
    pts = bk["pts"]
    present(bk["g"], [(F(0, 0.45), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), pts["top"])
    g = empty("rh", root)
    present(g, [(F(0, 0.0), F(5, 0))])
    m["flip"] = C.mat("t_flip", (1.0, 0.18, 0.12), emit=(1.0, 0.18, 0.12), strength=4.5)

    # beat 1: cells hold charge (blue tint), refresh sweeps row by row
    for r in range(ROWS):
        tint = empty(f"tint{r}", g)
        for c in range(COLS):
            cell_box(m, tint, f"t{r}_{c}", pts, r, c, "dram_bl_eq", 0.05)
        show(tint, [(F(1, 0.1 + 0.08 * r), F(1, 0.1 + 0.08 * r + 0.12))])
    # refresh window bar beside the bank, used beats 1..3
    zt = BZ0 - 9.0
    K.cmd_strip(m, g, "win_strip", BX0, BX1, zt)
    K.fill(m, g, "win1", BX0, BX1, 0.6, zt, 1, 0.05, 0.9, 1, n=12)
    K.fill(m, g, "win2", BX0, BX1, 0.6, zt, 2, 0.0, 1.0, 3, n=12)

    # beat 2: aggressor row flashes, leak beads into the victims
    _, wl_glow = bk["wl"][AGG]
    hammer = empty("hammer", g)
    xs = pts["col_x"]
    for c in range(COLS):
        x, y, z = pts["cell"](AGG, c)
        bx(f"hm{c}", (x - 0.85, y - 7.1, z - 0.85), (x + 0.85, y + 0.1, z + 0.85), m["h_amber"], hammer)
    blink(hammer, 2, range(3), n=3, on=0.8)
    blink(hammer, 3, range(8), n=8, on=0.5, u1=0.5)
    show(wl_glow, [])
    blink(wl_glow, 2, range(3), n=3, on=0.8)
    blink(wl_glow, 3, range(8), n=8, on=0.5, u1=0.5)
    za = pts["row_z"](AGG)
    for v in VICT:
        zv = pts["row_z"](v)
        for c in range(1, COLS, 2):
            x = xs(c)
            run(g, f"leak{v}_{c}", [(x, 7.5, za), (x, 9.0, (za + zv) / 2), (x, 5.0, zv)], 3, 0.35, m["warn"],
                [2, 3], 0.05, 0.85, 30)
    # victims fade: dimmer tint on victim rows during beat 2
    for v in VICT:
        vt = empty(f"vic{v}", g)
        for c in range(COLS):
            cell_box(m, vt, f"v{v}_{c}", pts, v, c, "dim_glow", 0.05)
        show(vt, [(F(2, 0.2), F(4, 0.4))])

    # beat 3: flips
    for k, (r, c) in enumerate(FLIPS):
        x, y, z = pts["cell"](r, c)
        f = empty(f"flipg{k}", g)
        bx(f"flip{k}", (x - 4.5, y + 4.0, z - 4.5), (x + 4.5, y + 5.5, z + 4.5), m["flip"], f)
        show(f, [(F(3, 0.25 + 0.1 * k), F(4, 0.35))])

    # beat 4: TRR rewrites the victims, refresh bar resets
    for v in VICT:
        K.write_back(m, bk, v, 4, 0.05, 0.6)
        bk_wl = bk["wl"][v][1]
        show(bk_wl, [(F(4, 0.05), F(4, 0.35)) if v == 3 else (F(4, 0.4), F(4, 0.7))])
    show(bk["sa_on"], [(F(4, 0.05), F(4, 0.75))])
    K.fill(m, g, "trr_cost", BX0, BX0 + 20.0, 0.6, zt, 4, 0.1, 0.6, 4, n=4, mt="h_amber")

    C.tags(root, {
        0: [("HBM stacks: DRAM dies", pk["hbm"]), ("GPU package", pk["top"]), ("one bank, cut open", pts["top"])],
        1: [("rows nm apart", pts["wl"](2)), ("each cell: charge on a capacitor", pts["cell"](1, 3)),
            ("refresh window: 64 ms", (BX1, 1.0, zt))],
        2: [("aggressor row: ACT, PRE, repeat", pts["wl"](AGG)), ("charge leaks to row 3", pts["cell"](3, 5)),
            ("and to row 5", pts["cell"](5, 1))],
        3: [("victim bits flip", pts["cell"](3, 7)), ("before refresh arrives", (BX1, 1.0, zt)),
            ("wrong value at sense amp", pts["sa"](6))],
        4: [("TRR: refresh rows 3 and 5", pts["wl"](VICT[1])), ("victims rewritten", pts["cell"](3, 4)),
            ("extra refresh = lost bandwidth", (BX0 + 10.0, 1.0, zt))],
    })
    cx, cz = (BX0 + BX1) / 2, (BZ0 + BZ1) / 2
    C.done(SLUG, BEATS, [
        frame((40.0, 0.0, -70.0), 360.0, 0.30, 0.60, pad=1.0),
        frame((cx, 6.0, cz - 4.0), 85.0, 0.25, 0.50),
        frame((cx, 6.0, cz), 70.0, 0.22, 0.55),
        frame((cx, 6.0, cz - 3.0), 75.0, 0.30, 0.50),
        frame((cx, 6.0, cz), 85.0, 0.35, 0.45),
    ], root)


if __name__ == "__main__":
    build()
