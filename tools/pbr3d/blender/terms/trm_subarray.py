"""TRM_SUBARRAY: the Terms-tab overview for a DRAM subarray, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_subarray.py

Writes assets/term_TRM_SUBARRAY.glb. Captions live in specs/terms/TRM_SUBARRAY.json.

One bank of an HBM die is drawn on the bench as three stacked subarrays, each a cell grid with its
own sense amps and row buffer, joined by a global data bus. One subarray opens a row; then two open
at once (subarray-level parallelism).

Beats:
  0 hbm      HBM stacks beside the GPU package
  1 split    a bank built from subarrays, each with its own sense amps
  2 one      one subarray opens a row, the others idle
  3 parallel two subarrays hold open rows at once, data to the global bus
  4 why      bank conflicts, bandwidth and related tickers
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

SLUG = "TRM_SUBARRAY"
BEATS = [
    ("HBM stacks feed the GPU; every bank is built from subarrays",
     "AI accelerators stream weights and activations from HBM stacks next to the GPU. Each DRAM die holds many banks, "
     "and each bank is not one big grid: it is a stack of subarrays, typically 512 to 1024 rows each."),
    ("A subarray is a block of rows with its own sense amps",
     "Every subarray has a local row of sense amplifiers at its edge. Its bitlines only run the height of the "
     "subarray, which keeps them short enough for a cell's tiny charge to be read reliably."),
    ("ACTIVATE opens one row in one subarray",
     "The row address picks a subarray and a row in it. That subarray's wordline rises and its sense amps latch the "
     "row; the other subarrays in the bank stay idle with their sense amps precharged."),
    ("Separate sense amps let several subarrays work at once",
     "Because each subarray latches its own row, a bank can in principle keep rows open in two subarrays and overlap "
     "their activate and precharge. Designs that exploit this (subarray-level parallelism) cut the penalty when "
     "requests hit different rows of the same bank."),
    ("Subarray wiring sets how well a bank handles mixed requests",
     "When two requests hit different rows in one bank, a plain bank must close one row before opening the next, which "
     "costs tens of nanoseconds. Accelerators issue huge numbers of such requests, so bank and subarray parallelism "
     "drives the bandwidth actually delivered. Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS)."),
]

SUBS = [(-100.0, -92.0), (-76.0, -68.0), (-52.0, -44.0)]
X0, X1 = 158.0, 232.0



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
    m["sa_bus"] = mat("sa_bus", (0.62, 0.55, 0.40), metal=0.8, rough=0.3)
    m["sa_bus_on"] = mat("sa_bus_on", (0.45, 0.95, 1.0), emit=(0.40, 0.90, 1.0), strength=5.0)
    m["sa_tint"] = mat("sa_tint", (0.35, 0.72, 1.0), emit=(0.30, 0.66, 1.0), strength=5.0)
    b = C.base(m, root)
    pk = b["pk"]
    span = [(F(1, 0), F(5, 0))]
    subs = []
    for i, (z0, z1) in enumerate(SUBS):
        s = K.bank(m, root, f"sub{i}", X0, X1, z0, z1, rows=3, cols=12)
        present(s["g"], span)
        subs.append(s)
        # outline glow in beat 1 marks each subarray
        present(gbx(f"sub{i}_edge", (X0 - 5.0, 0.0, z0 - 3.4), (X0 - 3.0, 4.0, z1 + 10.4), m["sa_tint"], root),
                [(F(1, 0), F(2, 0))])
    # global data bus along z at the right side
    present(gbx("gbus", (240.0, 0.2, -104.0), (243.0, 2.2, -30.0), m["sa_bus"], root), span)
    present(gbx("gbus_on", (238.5, 0.1, -104.2), (244.5, 6.0, -29.8), m["sa_bus_on"], root), [(F(3, 0), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), (195.0, 10.0, -66.0))

    K.row_open(subs[1], 1, [(F(2, 0), F(3, 0))])
    hot_row(m, root, subs[1], 1, [(F(2, 0), F(3, 0))])
    K.charge_share(m, subs[1], 1, 2, 0.0, 0.6)
    K.bl_show(subs[1], "hi", [(F(2, 0.3), F(3, 0))])
    for i, r in ((0, 2), (2, 0)):
        K.row_open(subs[i], r, [(F(3, 0), F(5, 0))])
        hot_row(m, root, subs[i], r, [(F(3, 0), F(5, 0))])
        K.charge_share(m, subs[i], r, 3, 0.0, 0.5)
        K.bl_show(subs[i], "hi", [(F(3, 0.2), F(5, 0))])
        K.io_flow(m, subs[i], [3, 6, 9], 3, 0.3, 0.9)
        K.io_flow(m, subs[i], [2, 5, 8], 4, 0.0, 0.8)

    p = [s["pts"] for s in subs]
    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]),
            ("bank = stack of subarrays", (195.0, 10.0, -66.0))],
        1: [("subarray 0", p[0]["top"]), ("subarray 1", p[1]["top"]), ("subarray 2", p[2]["top"]),
            ("own sense amps per subarray", p[2]["sa"](8))],
        2: [("ACT: row opens in subarray 1", p[1]["wl"](1)), ("its sense amps latch", p[1]["sa"](6)),
            ("subarray 0 idle", p[0]["top"])],
        3: [("two rows open at once", p[0]["wl"](2)), ("second open row", p[2]["wl"](0)),
            ("global data bus", (241.0, 2.2, -36.0))],
        4: [("row conflict: close, then open", p[1]["top"]), ("parallel rows hide the wait", p[2]["sa"](4))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame((198.0, 6.0, -68.0), 130.0, 0.25, 0.55),
        frame((195.0, 6.0, -66.0), 95.0, 0.25, 0.45),
        frame((200.0, 6.0, -68.0), 125.0, 0.30, 0.50),
        frame((198.0, 6.0, -68.0), 140.0, 0.20, 0.55),
    ], root)


if __name__ == "__main__":
    build()
