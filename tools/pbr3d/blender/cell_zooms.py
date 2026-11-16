"""The five CELL zoom-ins, authored in Blender and exported for pbr3d in the MELT + PULL template
(docs/diagram-pages.md), built from the cell pieces in cell_kit.py. Each zoom is four beats.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/cell_zooms.py [-- cap read rows shrink layout]

For each zoom it writes blender/cell_<name>.blend and assets/cell_<name>.glb.

  a cap     the storage capacitor: full = 1, charge leaks out of the plates, refresh tops it up
  b read    a read on the cell: charge sharing, sense and restore, precharge, then a 0
  c rows    refresh across the rows: the pointer walks the rows, each rewritten at full charge
  d shrink  shrinking the cell: a smaller footprint, the plates grow taller to keep the charge
  e layout  open vs folded bit lines: a reference line moves beside the signal, noise hits both

One beat is SEC (8) seconds at 24 fps.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, box, empty, key, label, pivot, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start, stream_of  # noqa: E402
import cell_kit as K  # noqa: E402
from cell_kit import ZC, SRC_X, DRN_X, BL_Y, CAP_Y0, CAP_Y1  # noqa: E402

BEATS = 4


def begin(name):
    m, root = start(name, BEATS, page="cell")
    K.mats(m)
    return m, root


# ---- a: the storage capacitor -----------------------------------------------------------


def cap():
    m, root = begin("cap")
    # the storage node and the source block it hangs from, then the capacitor without its outer
    # plate, so the charge inside shows
    box("source_n", (-150, -60, -150), (150, 20, 150), m["n_plus"], root)
    tube("storage_node", (0, 0, 0), (0, CAP_Y0 + 10, 0), 60, m["plug"], root, verts=12)
    H = CAP_Y1 - CAP_Y0
    _, fill = K.cap_stack(root, m, (0, CAP_Y0, 0), H, outer=False)
    scale_keys(fill, [
        (0, (1, 1, 1.0)),
        (F(1, 0.55), (1, 1, 1.0)),
        (F(1, 0.95), (1, 1, 0.70)),
        (F(2, 0.90), (1, 1, 0.45)),
        (F(3, 0.10), (1, 1, 0.45)),
        (F(3, 0.85), (1, 1, 1.0)),
    ])
    # leakage out of the plate, then the refill from the bit line above
    stream_of(root, "leak", 6, (-120, 380.0, 0), K.PATH_LEAK, 22, m["orange_dot"], 1, 0.15, 0.85, 80)
    stream_of(root, "refill", 6, (0, 900.0, 0), [(0, 0, 0), (0, -560, 0)], 22, m["cyan_dot"], 3, 0.10, 0.60, 50)
    label("full charge = 1", (0, CAP_Y1 + 60, 260), root, [(F(0, 0), F(1, 0))])
    label("charge leaks from the plate", (-330, 250, 200), root, [(F(1, 0), F(2, 0))])
    label("charge drains away", (260, 430, 260), root, [(F(2, 0), F(3, 0))])
    label("refresh tops it back up", (0, CAP_Y1 + 60, 260), root, [(F(3, 0), F(4, 0))])
    camera(root, [
        ((0.0, 520.0, 0.0), 2100.0, 0.40, 0.12),
        ((0.0, 520.0, 0.0), 2100.0, 0.36, 0.12),
        ((0.0, 520.0, 0.0), 2100.0, 0.30, 0.12),
        ((0.0, 520.0, 0.0), 2100.0, 0.34, 0.12),
    ])
    finish("cap", page="cell")


# ---- b: a read --------------------------------------------------------------------------


def read():
    m, root = begin("read")
    wl_high = [(F(0, 0), F(2, 0.1)), (F(3, 0.1), F(3, 0.9))]
    bl_on = [(F(0, 0.1), F(2, 0.2)), (F(3, 0.1), F(3, 0.9))]
    sa_on = [(F(1, 0.0), F(1, 0.95)), (F(3, 0.5), F(3, 0.95))]
    pre_on = [(F(2, 0.15), F(3, 0.0))]
    parts = K.cell(root, m, lit_wl=wl_high, lit_sa=sa_on, lit_pre=pre_on, lit_bl=bl_on)
    scale_keys(parts["bar"], [
        (0, (1, 1, 0.5)),
        (F(0, 0.70), (1, 1, 0.6)),
        (F(1, 0.50), (1, 1, 1.0)),
        (F(2, 0.70), (1, 1, 0.5)),
        (F(3, 0.00), (1, 1, 0.5)),
        (F(3, 0.60), (1, 1, 0.42)),
        (F(3, 0.85), (1, 1, 0.02)),
    ])
    scale_keys(parts["fill"], [
        (0, (1, 1, 1.0)),
        (F(0, 0.90), (1, 1, 0.85)),
        (F(1, 0.90), (1, 1, 1.0)),
        (F(3, 0.00), (1, 1, 0.05)),
    ])
    stream_of(root, "share", 6, K.SHARE_START, K.PATH_CAP_TO_BL, 28, m["cyan_dot"], 0, 0.20, 0.60, 60)
    stream_of(root, "restore", 6, K.RESTORE_START, K.PATH_BL_TO_CAP, 28, m["violet_dot"], 1, 0.10, 0.50, 60)
    label("charge sharing: cell to bit line", (DRN_X, BL_Y + 130, ZC), root, [(F(0, 0), F(1, 0))])
    label("sense amp restores the cell", (-1340, BL_Y + 210, ZC), root, [(F(1, 0), F(2, 0))])
    label("precharge to VDD/2", (1150, BL_Y + 210, ZC), root, [(F(2, 0), F(3, 0))])
    label("a 0 pulls the line down", (K.GAUGE_X + 60, 300, ZC), root, [(F(3, 0), F(4, 0))])
    camera(root, [
        ((0.0, 500.0, ZC), 4800.0, 0.45, 0.16),
        ((-700.0, 700.0, ZC), 4400.0, 0.45, 0.16),
        ((400.0, 600.0, ZC), 4800.0, 0.45, 0.16),
        ((-600.0, 500.0, ZC), 4800.0, 0.45, 0.16),
    ])
    finish("read", page="cell")


# ---- c: refresh across the rows ---------------------------------------------------------

ROWS = 6
PITCH = 420.0
Z_LO, Z_HI = -1050.0, 1050.0


def rows():
    m, root = begin("rows")
    cells = K.rows_of_cells(root, m, 1, ROWS, PITCH)
    t0, t1 = F(0, 0), F(2, 0.9)
    ptr = empty("pointer", root)
    box("pointer_m", (-200, 820, -110), (200, 850, 110), m["pointer"], ptr)
    key(ptr, t0, "location", P(0, 0, Z_LO), linear=True)
    key(ptr, t1, "location", P(0, 0, Z_HI), linear=True)
    for j, (g, pv) in enumerate(cells):
        z = (j - (ROWS - 1) / 2) * PITCH
        t_at = t0 + round((z - Z_LO) / (Z_HI - Z_LO) * (t1 - t0))
        keys = [(0, (1, 1, 0.85)), (t_at, (1, 1, 0.85)), (t_at + 34, (1, 1, 1.0)), (F(3, 0.0), (1, 1, 1.0)), (F(3, 0.95), (1, 1, 0.88))]
        scale_keys(pv, keys)
    label("refresh pointer walks the rows", (0, 900, -300), root, [(F(0, 0), F(1, 0))])
    label("row read, then rewritten", (0, 900, 150), root, [(F(1, 0), F(2, 0))])
    label("every row inside 64 ms", (0, 900, 300), root, [(F(2, 0), F(3, 0))])
    label("the cycle starts again", (0, 900, -300), root, [(F(3, 0), F(4, 0))])
    camera(root, [
        ((0.0, 420.0, 0.0), 4300.0, 1.25, 0.24),
        ((0.0, 420.0, 0.0), 4200.0, 1.25, 0.24),
        ((0.0, 420.0, 0.0), 4300.0, 1.25, 0.24),
        ((0.0, 420.0, 0.0), 4500.0, 1.25, 0.24),
    ])
    finish("rows", page="cell")


# ---- d: shrinking the cell --------------------------------------------------------------


def shrink():
    m, root = begin("shrink")
    H = CAP_Y1 - CAP_Y0
    box("source_n", (-150, -60, -150), (150, 20, 150), m["n_plus"], root)
    tube("storage_node", (0, 0, 0), (0, CAP_Y0 + 10, 0), 60, m["plug"], root, verts=12)
    stack, fill = K.cap_stack(root, m, (0, CAP_Y0, 0), H, outer=True)
    scale_keys(stack, [
        (0, (1, 1, 1)),
        (F(1, 0.10), (1, 1, 1)),
        (F(1, 0.70), (0.5, 1, 0.5)),
        (F(2, 0.10), (0.5, 1, 0.5)),
        (F(2, 0.80), (0.5, 1.6, 0.5)),
        (F(3, 0.95), (0.5, 1.6, 0.5)),
    ])
    label("a wide cell: a big capacitor", (0, CAP_Y1 + 90, 260), root, [(F(0, 0), F(1, 0))])
    label("smaller F: narrower capacitor", (0, CAP_Y1 + 90, 260), root, [(F(1, 0), F(2, 0))])
    label("taller plates keep Cc up", (0, CAP_Y1 + 90, 260), root, [(F(2, 0), F(3, 0))])
    label("same charge, smaller footprint", (0, CAP_Y1 + 90, 260), root, [(F(3, 0), F(4, 0))])
    camera(root, [
        ((0.0, 600.0, 0.0), 3000.0, 0.40, 0.12),
        ((0.0, 600.0, 0.0), 3000.0, 0.40, 0.12),
        ((0.0, 700.0, 0.0), 3000.0, 0.40, 0.12),
        ((0.0, 700.0, 0.0), 3200.0, 0.40, 0.12),
    ])
    finish("shrink", page="cell")


# ---- e: open vs folded bit lines --------------------------------------------------------


def layout():
    m, root = begin("layout")
    # two arrays with the sense amp between them
    box("array_a", (-1500, 0, -350), (-420, 40, 350), m["plinth"], root)
    box("array_b", (420, 0, -350), (1500, 40, 350), m["plinth"], root)
    box("sense_amp_e", (-300, 200, -160), (300, 400, 160), m["sa"], root)
    sig = empty("signal_line", root)
    tube("sig_w", (-1300, 300, 0), (-500, 300, 0), 40, m["bl"], sig, verts=12)
    ref = empty("ref_line", root)
    tube("ref_w", (500, 300, 0), (1300, 300, 0), 40, m["orange_dot"], ref, verts=12)
    # folded: the reference slides beside the signal in array a
    key(ref, 0, "location", P(0, 0, 0), linear=True)
    key(ref, F(1, 0.10), "location", P(0, 0, 0), linear=True)
    key(ref, F(1, 0.60), "location", P(-1800, 0, 120), linear=True)
    key(ref, F(4, 0), "location", P(-1800, 0, 120), linear=True)
    # noise: both lines bump up together, the difference line on the floor stays flat
    for g in (sig, ref):
        key(g, F(2, 0.20), "location", P(0, 0, 0) if g is sig else P(-1800, 0, 120), linear=True)
    key(sig, F(2, 0.35), "location", P(0, 120, 0), linear=True)
    key(ref, F(2, 0.35), "location", P(-1800, 120, 120), linear=True)
    key(sig, F(2, 0.65), "location", P(0, 0, 0), linear=True)
    key(ref, F(2, 0.65), "location", P(-1800, 0, 120), linear=True)
    band = box("noise_band", (-1500, 250, -380), (-420, 350, 380), m["pink_band"] if "pink_band" in m else m["red"], root)
    K.switch(band, [(F(2, 0.25), F(2, 0.75))])
    diff = box("difference_line", (-1200, 42, 280), (-600, 58, 330), m["gold_glow"], root)
    K.switch(diff, [(F(3, 0.0), F(4, 0.0))])
    label("open: reference in the other array", (0, 620, 0), root, [(F(0, 0), F(1, 0))])
    label("folded: the pair sits side by side", (-900, 520, 150), root, [(F(1, 0), F(2, 0))])
    label("noise hits both lines", (-900, 480, 0), root, [(F(2, 0), F(3, 0))])
    label("difference stays flat", (-900, 58, 305), root, [(F(3, 0), F(4, 0))])
    camera(root, [
        ((0.0, 250.0, 0.0), 4200.0, 0.10, 0.25),
        ((-400.0, 250.0, 60.0), 3600.0, 0.10, 0.25),
        ((-600.0, 300.0, 60.0), 3600.0, 0.10, 0.25),
        ((-300.0, 250.0, 0.0), 3900.0, 0.10, 0.25),
    ])
    finish("layout", page="cell")


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["cap", "read", "rows", "shrink", "layout"]
    for name in which:
        globals()[name]()
