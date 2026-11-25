"""TRM_MEMORY_MAT: the Terms-tab overview for a DRAM memory mat, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_memory_mat.py

Writes assets/term_TRM_MEMORY_MAT.glb. Captions live in specs/terms/TRM_MEMORY_MAT.json.

One subarray of an HBM die is drawn large on the bench as a 2x2 tile of mats. Each mat has its own
local row drivers and sense amps; a global wordline runs over all of them, and only the selected
mat fires its local wordline. Short local bitlines are why mats exist.

Beats:
  0 hbm     HBM stacks beside the GPU package
  1 tiles   a subarray split into four mats, each with drivers and sense amps
  2 select  global wordline lit, only mat A fires a local wordline
  3 short   short local bitlines: big signal, fast sense
  4 trade   more mats = more sense amps (area) vs lower energy per bit
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

SLUG = "TRM_MEMORY_MAT"
BEATS = [
    ("HBM stacks feed the GPU; each die is tiled into mats",
     "AI accelerators read weights and activations from HBM stacks beside the GPU. Inside each DRAM die, a bank is "
     "split into subarrays, and each subarray is tiled again into mats: small cell arrays of roughly 512 x 512 bits."),
    ("A mat is a small cell array with its own drivers and sense amps",
     "Each mat has local row drivers along one edge and a strip of local sense amps along another. The mat is the "
     "unit that physically switches on: its wordlines and bitlines stop at the mat's border."),
    ("A global wordline selects; only one mat fires its local wordline",
     "The row address travels on a global wordline in a high metal layer over all the mats. Only the selected mat's "
     "driver raises its short local wordline, so the other mats stay idle and burn no switching energy."),
    ("Short bitlines give a bigger signal and a faster read",
     "A cell's charge is tiny, and the bitline's own capacitance dilutes it. A mat keeps bitlines short, so the "
     "voltage swing the sense amp sees is larger and it settles sooner. That cuts both latency and energy per access."),
    ("Mat size trades area against speed and energy per bit",
     "Smaller mats mean more sense amps and drivers, which take die area that could hold cells and raise cost per "
     "bit. HBM uses finer mats and shorter wires than DDR5 to lower picojoules per bit, which matters when AI servers "
     "are power limited. Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS)."),
]

MATS = {"A": (156.0, 194.0, -86.0, -70.0), "B": (204.0, 242.0, -86.0, -70.0),
        "C": (156.0, 194.0, -52.0, -36.0), "D": (204.0, 242.0, -52.0, -36.0)}



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
    m["mm_drv"] = mat("mm_drv", (0.42, 0.36, 0.52), metal=0.5, rough=0.35)
    m["mm_drv_on"] = mat("mm_drv_on", (1.0, 0.62, 0.20), emit=(1.0, 0.55, 0.15), strength=3.5)
    m["mm_gwl"] = mat("mm_gwl", (0.62, 0.55, 0.40), metal=0.8, rough=0.3)
    m["mm_gwl_on"] = mat("mm_gwl_on", (1.0, 0.80, 0.35), emit=(1.0, 0.75, 0.30), strength=3.0)
    m["mm_edge"] = mat("mm_edge", (0.35, 0.72, 1.0), emit=(0.30, 0.66, 1.0), strength=5.0)
    b = C.base(m, root)
    pk = b["pk"]
    span = [(F(1, 0), F(5, 0))]
    bk = {}
    for k, (x0, x1, z0, z1) in MATS.items():
        bk[k] = K.bank(m, root, f"mat{k}", x0, x1, z0, z1, rows=4, cols=6)
        present(bk[k]["g"], span)
        d = gbx(f"drv{k}", (x0 - 7.0, 0.2, z0 - 2.0), (x0 - 3.5, 5.0, z1 + 2.0), m["mm_drv"], root)
        present(d, span)
        # mat border outline (glows in beat 1)
        for i, (lo, hi) in enumerate([((x0 - 3, 0, z0 - 4.6), (x1 + 3, 3.0, z0 - 3)),
                                      ((x0 - 3, 0, z1 + 10), (x1 + 3, 3.0, z1 + 11.6)),
                                      ((x0 - 4.6, 0, z0 - 3), (x0 - 3, 3.0, z1 + 10)),
                                      ((x1 + 3, 0, z0 - 3), (x1 + 4.6, 3.0, z1 + 10))]):
            present(gbx(f"edge{k}{i}", lo, hi, m["mm_edge"], root), [(F(1, 0.0), F(2, 0))])
    A = bk["A"]
    xA0, xA1, zA0, zA1 = MATS["A"]
    dA = gbx("drvA_on", (xA0 - 8.0, 0.1, zA0 - 3.0), (xA0 - 2.8, 7.0, zA1 + 3.0), m["mm_drv_on"], root)
    present(dA, [(F(2, 0.0), F(5, 0))])
    # global wordline over A and B (row 1), high metal
    zg = A["pts"]["row_z"](1)
    present(gbx("gwl", (150.0, 16.0, zg - 0.6), (248.0, 17.0, zg + 0.6), m["mm_gwl"], root), span)
    present(gbx("gwl_on", (150.0, 16.0, zg - 1.0), (248.0, 18.0, zg + 1.0), m["mm_gwl_on"], root),
            [(F(2, 0.0), F(5, 0))])
    run(root, "gwl_b", [(150.0, 17.5, zg), (xA0 - 5.0, 17.5, zg), (xA0 - 5.0, 5.5, zg)], 3, 0.8,
        m["dram_bead_w"], 2, 0.0, 0.3, 20)
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), (200.0, 10.0, -60.0))

    K.row_open(A, 1, [(F(2, 0.0), F(5, 0))])
    hot_row(m, root, A, 1, [(F(2, 0.0), F(5, 0))])
    K.charge_share(m, A, 1, 2, 0.3, 0.8)
    K.bl_show(A, "hi", [(F(3, 0.0), F(5, 0))])
    K.charge_share(m, A, 1, 3, 0.0, 0.5)
    K.io_flow(m, A, [1, 2, 3, 4], 3, 0.4, 0.9)
    # beat 4: mats C and D take turns, energy only where active
    C2 = bk["D"]
    K.row_open(C2, 2, [(F(4, 0.0), F(5, 0))])
    hot_row(m, root, C2, 2, [(F(4, 0.0), F(5, 0))])
    K.charge_share(m, C2, 2, 4, 0.3, 0.8)

    pa, pb, pd = A["pts"], bk["B"]["pts"], C2["pts"]
    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]),
            ("bank > subarray > mats", (200.0, 10.0, -60.0))],
        1: [("mat: ~512 x 512 cells", pa["top"]), ("local row drivers", (xA0 - 5.0, 5.0, zA0)),
            ("local sense amps", pa["sa"](3)), ("four mats, one subarray", pd["top"])],
        2: [("global wordline over all mats", (246.0, 17.0, zg)), ("only mat A's driver fires", (xA0 - 5.0, 5.2, zA0)),
            ("mat B stays idle", pb["top"])],
        3: [("short local bitlines", pa["bl"](4)), ("bigger swing, faster sense", pa["sa"](2)),
            ("data out of the mat", pa["io"])],
        4: [("more mats = more sense amps", pd["sa"](3)), ("area vs pJ per bit", pd["top"]),
            ("HBM: finer mats than DDR5", pa["top"])],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame((199.0, 6.0, -56.0), 135.0, 0.25, 0.50),
        frame((185.0, 8.0, -70.0), 100.0, 0.25, 0.45),
        frame((176.0, 6.0, -70.0), 70.0, 0.25, 0.40),
        frame((199.0, 6.0, -56.0), 140.0, 0.30, 0.55),
    ], root)


if __name__ == "__main__":
    build()
