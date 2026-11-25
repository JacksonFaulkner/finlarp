"""TRM_SELF_REFRESH: the Terms-tab overview for DRAM self-refresh, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_self_refresh.py

Writes assets/term_TRM_SELF_REFRESH.glb. Captions live in specs/terms/TRM_SELF_REFRESH.json.

Command beads run from the GPU's memory controller to the HBM; on self-refresh entry they stop, the
DRAM's own timer fills and its rows refresh one by one on the bench; on exit commands resume.

Beats:
  0 active   the controller streams commands, including REFRESH
  1 enter    SRE: the controller goes quiet, link idle
  2 internal the die's own timer refreshes rows in turn
  3 power    I/O and clocks off, only refresh draws power
  4 exit     SRX, wait, commands resume; related tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from sand_overview import empty  # noqa: E402
from power_vrm_detail import bx, frame, mat, present, run  # noqa: E402

SLUG = "TRM_SELF_REFRESH"
BEATS = [
    ("Normally the GPU's controller drives every DRAM command",
     "While the accelerator is busy, its memory controller sends a constant stream of ACTIVATE, READ, WRITE and "
     "REFRESH commands to the HBM stacks. Refresh is the controller's job: it must hit every row about every 64 ms."),
    ("Self-refresh entry: the controller goes quiet",
     "When memory will sit idle, the controller issues a self-refresh entry command and stops talking. The DRAM takes "
     "over its own refresh, so the link and the controller's PHY can power down."),
    ("The DRAM's own timer refreshes each row in turn",
     "An internal oscillator and row counter inside the die open and rewrite rows one after another, keeping every "
     "cell inside its retention window. The data stays valid with no outside commands."),
    ("Only refresh draws power; the interface sleeps",
     "Clocks, I/O drivers and receivers are off, so the device draws a few milliwatts instead of watts. Many parts "
     "also adjust the refresh rate to temperature, refreshing less often when cool."),
    ("Exit takes time, so it suits idle memory, not training",
     "Leaving self-refresh needs a wake-up delay of hundreds of nanoseconds before commands resume, so busy training "
     "jobs never use it. It matters for idle nodes, system suspend and memory power budgets. "
     "Related: Micron (MU), SK hynix (000660.KS), Rambus (RMBS)."),
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
    m["sr_cmd"] = mat("sr_cmd", (0.45, 0.90, 1.0), emit=(0.40, 0.86, 1.0), strength=3.5)
    m["sr_osc"] = mat("sr_osc", (0.30, 0.34, 0.42), metal=0.5, rough=0.35)
    m["sr_osc_on"] = mat("sr_osc_on", (0.5, 0.9, 0.4), emit=(0.4, 0.9, 0.3), strength=3.0)
    m["sr_sleep"] = mat("sr_sleep", (0.35, 0.40, 0.60), emit=(0.30, 0.36, 0.60), strength=4.0)
    b = C.base(m, root)
    pk = b["pk"]
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=ROWS, cols=COLS)
    pts = bk["pts"]
    present(bk["g"], [(F(0, 0), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), pts["top"])

    # commands GPU -> HBM in beats 0 and 4
    top, hbm = pk["top"], pk["hbm"]
    path = [(top[0], top[1] + 3.0, top[2]), ((top[0] + hbm[0]) / 2, top[1] + 8.0, (top[2] + hbm[2]) / 2),
            (hbm[0], hbm[1] + 3.0, hbm[2])]
    run(root, "cmd", path, 8, 1.2, m["sr_cmd"], [0], 0.0, 0.9, 25)
    run(root, "cmd4", path, 8, 1.2, m["sr_cmd"], [4], 0.5, 0.95, 20)
    # an internal oscillator + row counter block on the bank's left edge
    osc = (BX0 - 12.0, 0.5, -64.0)
    present(gbx("osc", (osc[0] - 4, 0.3, osc[2] - 6), (osc[0] + 4, 5.0, osc[2] + 6), m["sr_osc"], root),
            [(F(0, 0), F(5, 0))])
    present(gbx("osc_on", (osc[0] - 4.6, 0.2, osc[2] - 6.6), (osc[0] + 4.6, 8.0, osc[2] + 6.6), m["sr_osc_on"], root),
            [(F(2, 0), F(4, 0))])
    # sleeping link marker over the HBM in beats 1-3
    present(gbx("sleep", (hbm[0] - 8, hbm[1] + 6, hbm[2] - 8), (hbm[0] + 8, hbm[1] + 7, hbm[2] + 8), m["sr_sleep"], root),
            [(F(1, 0), F(4, 0))])
    for bt in (2, 3):
        for r in range(ROWS):
            u = 0.05 + 0.15 * r
            K.row_open(bk, r, [(F(bt, u), F(bt, u + 0.13))])
            hot_row(m, root, bk, r, [(F(bt, u), F(bt, u + 0.13))])
            K.write_back(m, bk, r, bt, u, u + 0.12)
            run(root, f"osc{bt}{r}", [(osc[0] + 4, 5.0, osc[2]), (BX0 - 2, 9.0, pts["row_z"](r))], 1, 1.6,
                m["sr_osc_on"], bt, u - 0.04, u - 0.04, 6)
    K.cmd_strip(m, root, "tl", BX0, BX1, -18.0)
    present(K.fill(m, root, "tim", BX0, BX1, 1.4, -18.0, 2, 0.0, 0.95, 3, mt="sr_osc_on"), [(F(2, 0), F(4, 0))])

    C.tags(root, {
        0: [("controller sends commands", path[1]), ("HBM stacks", hbm), ("GPU + memory controller", top)],
        1: [("SRE: controller goes quiet", top), ("link and PHY power down", hbm), ("bank keeps its data", pts["top"])],
        2: [("internal oscillator", osc), ("row counter opens rows in turn", pts["wl"](2)),
            ("cells rewritten in place", pts["sa"](5))],
        3: [("I/O and clocks off", hbm), ("mW, not W", pts["top"]), ("refresh timer keeps running", (BX1, 2.0, -18.0))],
        4: [("SRX: wake-up delay", hbm), ("commands resume", path[1])],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame((105.0, 0.0, -70.0), 290.0, 0.30, 0.55, pad=1.0),
        frame(((BX0 + BX1) / 2 - 6, 6.0, -58.0), 120.0, 0.25, 0.45),
        frame(((BX0 + BX1) / 2, 6.0, -52.0), 125.0, 0.30, 0.50),
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.60, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
