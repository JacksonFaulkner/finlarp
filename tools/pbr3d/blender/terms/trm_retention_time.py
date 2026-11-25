"""TRM_RETENTION_TIME: the Terms-tab overview for DRAM retention time, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_retention_time.py

Writes assets/term_TRM_RETENTION_TIME.glb. Captions live in specs/terms/TRM_RETENTION_TIME.json.

A bank of an HBM die on the bench: freshly written cells glow full, charge beads leak out into the
substrate while a 64 ms timer fills, a refresh re-reads and rewrites the row, and heat rising off
the bank halves the window.

Beats:
  0 hbm      HBM stacks beside the GPU package
  1 written  cells hold full charge right after a write
  2 leak     charge leaks away; the 64 ms timer fills
  3 refresh  rows are opened and rewritten before the deadline
  4 heat     hot DRAM leaks faster: 32 ms window, more refresh
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from sand_overview import empty  # noqa: E402
from power_vrm_detail import bx, frame, mat, present, rise, run  # noqa: E402

SLUG = "TRM_RETENTION_TIME"
BEATS = [
    ("HBM stacks feed the GPU, and every bit is charge on a capacitor",
     "The HBM stacks beside an AI accelerator are DRAM: each bit is a small charge on a capacitor of a few "
     "femtofarads, gated by one transistor. That charge does not stay put forever."),
    ("Right after a write, each cell holds full charge",
     "A write or refresh pushes the capacitor to a full 1 or empties it to 0. The sense amp can tell them apart as "
     "long as the stored charge stays well above the halfway point."),
    ("Charge leaks away; retention time is how long a bit survives",
     "Leakage through the access transistor and the junction drains the capacitor. Retention time is how long a cell "
     "keeps a readable charge. Most cells last seconds, but the weakest few set the rule: every row must be refreshed "
     "within about 64 ms."),
    ("Refresh reads each row and writes it back before the deadline",
     "The controller issues REFRESH commands that open rows in turn, let the sense amps restore full charge, and close "
     "them again. While a bank refreshes it cannot serve reads, so refresh costs bandwidth and power."),
    ("Heat shortens retention, so hot memory refreshes twice as often",
     "Leakage roughly doubles every 10 C or so. Above 85 C the DDR rules halve the window to 32 ms, doubling refresh "
     "overhead. Dense AI servers run memory hot, so retention drives both lost bandwidth and DRAM design. "
     "Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS)."),
]

BX0, BX1, BZ0, BZ1 = 162.0, 234.0, -80.0, -44.0
ROWS, COLS = 6, 10



def gbx(name, lo, hi, mt, root):
    """A box inside its own empty at the origin, so present() can move it in and out."""
    g = empty(name + "_g", root)
    bx(name, lo, hi, mt, g)
    return g

_N = [0]


def hot_row(m, root, bk, row, spans):
    """A thick glowing bar over row `row`, clearly above the cell tops and bitlines."""
    _N[0] += 1
    name = f"hot{_N[0]}"
    z = bk["pts"]["row_z"](row)
    xs = [bk["pts"]["col_x"](c) for c in range(bk["cols"])]
    present(gbx(name, (xs[0] - 3.0, 11.4, z - 1.3), (xs[-1] + 3.0, 13.4, z + 1.3), m["hot_wl"], root), spans)


def hot_mats(m):
    m["hot_wl"] = mat("hot_wl", (1.0, 0.62, 0.20), emit=(1.0, 0.55, 0.15), strength=5.0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    hot_mats(m)
    m["rt_full"] = mat("rt_full", (1.0, 0.70, 0.30), emit=(1.0, 0.62, 0.22), strength=3.0)
    m["rt_low"] = mat("rt_low", (0.55, 0.40, 0.25), emit=(0.50, 0.32, 0.15), strength=3.0)
    m["rt_heat"] = mat("rt_heat", (1.0, 0.35, 0.15), emit=(1.0, 0.30, 0.10), strength=5.0)
    m["rt_leak"] = mat("rt_leak", (1.0, 0.70, 0.30), emit=(1.0, 0.62, 0.25), strength=5.0)
    b = C.base(m, root)
    pk = b["pk"]
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=ROWS, cols=COLS)
    pts = bk["pts"]
    present(bk["g"], [(F(1, 0), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), pts["top"])

    # charge level overlays on the cell tops
    full, low = [], []
    for r in range(ROWS):
        for c in range(COLS):
            x, y, z = pts["cell"](r, c)
            full.append(gbx(f"q{r}_{c}", (x - 1.6, y + 3.4, z - 1.6), (x + 1.6, y + 6.4, z + 1.6), m["rt_full"], root))
            low.append(gbx(f"l{r}_{c}", (x - 1.0, y + 3.4, z - 1.0), (x + 1.0, y + 4.2, z + 1.0), m["rt_low"], root))
    for o in full:
        present(o, [(F(1, 0), F(2, 0.5)), (F(3, 0.3), F(4, 0.4))])
    for o in low:
        present(o, [(F(2, 0.5), F(3, 0.3)), (F(4, 0.4), F(5, 0))])
    # leakage beads: cells drip charge sideways into the substrate
    for i, (r, c) in enumerate([(0, 1), (1, 6), (2, 3), (3, 8), (4, 2), (5, 5), (2, 9), (4, 7)]):
        x, y, z = pts["cell"](r, c)
        run(root, f"leak{i}", [(x, y + 4.0, z), (x + 1.5, 1.0, z + 1.5), (x + 4.0, 0.5, z + 3.0)], 3, 1.0,
            m["rt_leak"], [2, 4], 0.0, 0.8, 30)
    # refresh: rows opened in turn and rewritten
    for r in range(ROWS):
        u = 0.05 + 0.13 * r
        K.row_open(bk, r, [(F(3, u), F(3, u + 0.12))])
        hot_row(m, root, bk, r, [(F(3, u), F(3, u + 0.12))])
        K.write_back(m, bk, r, 3, u, u + 0.1)
    # 64 ms timer, then 32 ms timer filling twice as fast under heat
    K.cmd_strip(m, root, "tl", BX0, BX1, -18.0)
    present(K.fill(m, root, "t64", BX0, BX1, 1.4, -18.0, 2, 0.0, 0.95, 2), [(F(2, 0), F(3, 0))])
    present(K.fill(m, root, "t64b", BX0, BX1, 1.4, -18.0, 3, 0.0, 0.9, 3), [(F(3, 0), F(4, 0))])
    present(K.fill(m, root, "t32", BX0, (BX0 + BX1) / 2, 1.4, -18.0, 4, 0.0, 0.5, 4, mt="rt_heat"),
            [(F(4, 0), F(5, 0))])
    rise(root, "heat", (198.0, 12.0, -62.0), 24, 2.0, m["rt_heat"], 4, 0.0, 0.85, h=30.0, life=50,
         spread=(30.0, 16.0))

    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]),
            ("each bit: charge on a capacitor", pts["top"])],
        1: [("fresh write: full charge", pts["cell"](2, 4)), ("1T1C cell grid", pts["top"])],
        2: [("charge leaks to substrate", pts["cell"](3, 8)), ("64 ms refresh deadline", (BX1, 2.0, -18.0)),
            ("weakest cells set the rule", pts["cell"](0, 1))],
        3: [("REFRESH: open row, restore", pts["wl"](2)), ("sense amps rewrite charge", pts["sa"](5)),
            ("bank busy: no reads", pts["rb"](3))],
        4: [("hot DRAM leaks faster", (198.0, 30.0, -62.0)), ("above 85 C: 32 ms window", ((BX0 + BX1) / 2, 2.0, -18.0)),
            ("2x refresh overhead", pts["top"])],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame(((BX0 + BX1) / 2, 6.0, -60.0), 110.0, 0.25, 0.45),
        frame(((BX0 + BX1) / 2, 6.0, -52.0), 120.0, 0.25, 0.50),
        frame(((BX0 + BX1) / 2, 6.0, -55.0), 115.0, 0.30, 0.45),
        frame(((BX0 + BX1) / 2, 12.0, -52.0), 130.0, 0.25, 0.40),
    ], root)


if __name__ == "__main__":
    build()
