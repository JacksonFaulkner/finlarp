"""TRM_COPPER_CLAD_LAMINATE: the Terms-tab overview for copper clad laminate (CCL).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_copper_clad_laminate.py

Writes assets/term_TRM_COPPER_CLAD_LAMINATE.glb. Captions live in specs/terms/TRM_COPPER_CLAD_LAMINATE.json.

A laminate line on the shop floor: an exploded CCL sheet on the bench (copper foil, resin, woven glass
yarns), a hot press closing on a stack of books, a sheet etched into a GPU board with signals running,
a loss race between FR-4 and low-loss traces, and a multilayer AI board cross-section.

Beats:
  0 layers   copper foil + resin + woven glass cloth, exploded
  1 press    books stacked in a hot vacuum press, platen comes down, heat
  2 etch     foil etched into traces; signals run to the chip
  3 loss     FR-4 eats the signal, low-loss resin carries it
  4 demand   20+ layer AI boards eat lots of CCL; tickers
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
import sand_overview as O  # noqa: E402
from sand_overview import mat, tube  # noqa: E402
from term_common import F, P, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, rise, run  # noqa: E402

SLUG = "TRM_COPPER_CLAD_LAMINATE"
BEATS = [
    ("A copper clad laminate is copper foil bonded to a glass-and-resin core",
     "CCL is the raw sheet every printed circuit board starts from. Its core is woven glass cloth soaked in "
     "resin, which gives it stiffness and insulation, and thin copper foil (often 12 to 35 microns) is bonded "
     "to one or both faces. The board maker later etches that copper into wiring."),
    ("Stacks of foil and prepreg are cured in a hot vacuum press",
     "Glass cloth is dipped in resin and part-cured into sheets called prepreg. Prepreg is stacked with foil "
     "between polished steel plates, and a press heats the stack near 200 C under pressure for an hour or more. "
     "The resin melts, flows round the glass and hardens, locking the foil on."),
    ("The board maker etches the foil into the wires of a server board",
     "A PCB maker coats the copper with a photo mask, exposes the circuit pattern and etches away the copper "
     "that is not wanted. What is left are traces that carry power and signals between chips. Many etched "
     "laminates are then pressed together into one multilayer board."),
    ("Low-loss resin keeps fast signals from fading in the board",
     "At 56 to 112 Gb/s per lane, ordinary FR-4 epoxy soaks up signal energy as heat, so pulses fade within "
     "a short run. Low-loss CCL uses resins with a low dielectric constant (Dk) and loss factor (Df), plus "
     "special glass, so signals reach the far chip. These grades are harder to make and few are qualified."),
    ("Every AI accelerator, switch and backplane adds layers of CCL",
     "An AI server board can stack 20 to 30 laminate layers, versus 4 to 8 in a PC board, and each accelerator, "
     "switch tray and backplane adds more. CCL demand therefore rises with AI rack builds, and the low-loss "
     "pool is tight. Related: Rogers (ROG), Taiwan Union Technology (6274.TW), Shengyi Technology (600183.SS)."),
]

# exploded sheet on the bench
LX0, LX1 = 20.0, 120.0
LZ0, LZ1 = -30.0, 20.0
# hot press, left
PX = -90.0
# etched board, right
BX0, BX1 = 150.0, 245.0


def mats(m):
    m["ccl_resin"] = mat("ccl_resin", (0.85, 0.65, 0.25), rough=0.3, alpha=0.40)
    m["ccl_glass"] = mat("ccl_glass", (0.88, 0.92, 0.95), metal=0.1, rough=0.25)
    m["ccl_cu"] = mat("ccl_cu", (0.90, 0.50, 0.28), metal=1.0, rough=0.25)
    m["ccl_core"] = mat("ccl_core", (0.70, 0.62, 0.30), rough=0.5)
    m["ccl_pp"] = mat("ccl_pp", (0.85, 0.75, 0.40), rough=0.6)
    m["ccl_plate"] = mat("ccl_plate", (0.75, 0.77, 0.80), metal=1.0, rough=0.15)
    m["ccl_heat"] = mat("ccl_heat", (1.0, 0.45, 0.15), emit=(1.0, 0.40, 0.12), strength=3.0)
    m["ccl_hotplate"] = mat("ccl_hotplate", (0.6, 0.3, 0.2), emit=(1.0, 0.35, 0.10), strength=0.8)
    m["ccl_sig"] = mat("ccl_sig", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=4.0)
    m["ccl_weak"] = mat("ccl_weak", (1.0, 0.3, 0.2), emit=(1.0, 0.3, 0.15), strength=3.0)


def move(obj, keys):
    """Keyframe obj's location offset (poly dy) at each (frame, dy)."""
    O._interp("LINEAR")
    for f, dy in keys:
        obj.location = P(0.0, dy, 0.0)
        obj.keyframe_insert("location", frame=f)


def weave(m, parent, name, x0, x1, z0, z1, y, pitch=5.0, amp=0.6, r=0.9):
    """Plain weave: warp yarns along x and weft along z, each going over and under the other."""
    g = empty(name, parent)
    nx = int((z1 - z0) / pitch)
    nz = int((x1 - x0) / pitch)
    for i in range(nx + 1):
        z = z0 + i * pitch
        pts = [(x0 + k * pitch / 2, y + amp * (1 if (k + i) % 2 else -1), z) for k in range(2 * nz + 1)]
        K.pipe(m, g, f"{name}_wp{i}", pts, r, "ccl_glass")
    for j in range(nz + 1):
        x = x0 + j * pitch
        pts = [(x, y + amp * (-1 if (k + j) % 2 else 1), z0 + k * pitch / 2) for k in range(2 * nx + 1)]
        K.pipe(m, g, f"{name}_wf{j}", pts, r, "ccl_glass")
    return g


def sheet(m, root):
    """The exploded laminate: bottom foil, a resin core with two glass plies, top foil."""
    g = empty("sheet", root)
    bx("sh_cu_bot", (LX0, 2.0, LZ0), (LX1, 3.0, LZ1), m["ccl_cu"], g)
    bx("sh_resin", (LX0, 9.0, LZ0), (LX1, 21.0, LZ1), m["ccl_resin"], g)
    weave(m, g, "ply_a", LX0 + 2, LX1 - 2, LZ0 + 2, LZ1 - 2, 12.5)
    weave(m, g, "ply_b", LX0 + 2, LX1 - 2, LZ0 + 2, LZ1 - 2, 17.5)
    cu_top = empty("sh_cu_top_g", g)
    bx("sh_cu_top", (LX0, 28.0, LZ0), (LX1, 29.0, LZ1), m["ccl_cu"], cu_top)
    # guide posts that show the stack lines up
    for x in (LX0 - 3, LX1 + 3):
        for z in (LZ0 - 3, LZ1 + 3):
            tube(f"sh_post_{x}_{z}", (x, 0.0, z), (x, 32.0, z), 0.5, m["ccl_plate"], g, 8)
    return g, cu_top


def press(m, root):
    """A hydraulic laminating press: four columns, a heated bed, a moving heated platen, and a stack
    of books (steel plate, foil, prepreg, foil) between them. Returns the moving platen."""
    g = empty("press", root)
    z0, z1 = -55.0, -5.0
    x0, x1 = PX - 30.0, PX + 30.0
    for x in (x0 - 4, x1 + 4):
        for z in (z0 - 4, z1 + 4):
            tube(f"pr_col_{x}_{z}", (x, 0.0, z), (x, 95.0, z), 2.5, m["sup_steel"], g, 16)
    bx("pr_crown", (x0 - 9, 95.0, z0 - 9), (x1 + 9, 104.0, z1 + 9), m["sup_steel"], g)
    bx("pr_bed", (x0 - 6, 0.0, z0 - 6), (x1 + 6, 14.0, z1 + 6), m["sup_steel"], g)
    bx("pr_bed_hot", (x0, 14.0, z0), (x1, 16.0, z1), m["ccl_hotplate"], g)
    # stack of books
    y = 16.0
    for k in range(4):
        bx(f"pr_plate{k}", (x0, y, z0), (x1, y + 1.6, z1), m["ccl_plate"], g)
        y += 1.6
        bx(f"pr_foilA{k}", (x0 + 1, y, z0 + 1), (x1 - 1, y + 0.4, z1 - 1), m["ccl_cu"], g)
        y += 0.4
        for p in range(3):
            bx(f"pr_pp{k}_{p}", (x0 + 1, y, z0 + 1), (x1 - 1, y + 1.0, z1 - 1), m["ccl_pp"], g)
            y += 1.0
        bx(f"pr_foilB{k}", (x0 + 1, y, z0 + 1), (x1 - 1, y + 0.4, z1 - 1), m["ccl_cu"], g)
        y += 0.4
    top = y
    plat = empty("pr_platen", g)
    bx("pr_platen_hot", (x0, top + 14.0, z0), (x1, top + 16.0, z1), m["ccl_hotplate"], plat)
    bx("pr_platen_body", (x0 - 6, top + 16.0, z0 - 6), (x1 + 6, top + 26.0, z1 + 6), m["sup_steel"], plat)
    tube("pr_ram", (PX, top + 26.0, (z0 + z1) / 2), (PX, 95.0, (z0 + z1) / 2), 6.0, m["ccl_plate"], plat, 24)
    # vacuum line
    K.pipe(m, g, "pr_vac", [(x1 + 6, 8.0, z1), (x1 + 25, 8.0, z1), (x1 + 25, 0.5, z1)], 1.4)
    return g, plat, top


def board(m, root):
    """An etched server board with a chip; foil that is etched away; returns (foil, traces, paths)."""
    g = empty("board", root)
    zb0, zb1 = -40.0, 10.0
    bx("bd_core", (BX0, 0.0, zb0), (BX1, 3.0, zb1), m["ccl_core"], g)
    foil = empty("bd_foil", g)
    bx("bd_foil_s", (BX0, 3.0, zb0), (BX1, 3.4, zb1), m["ccl_cu"], foil)
    tr = empty("bd_traces", g)
    chip_c = (BX1 - 20.0, 3.4, -15.0)
    C.chip(m, tr, "bd_gpu", chip_c, 18.0, 18.0, h=2.5, pins=10)
    paths = []
    for k in range(6):
        z = -32.0 + k * 6.0
        zz = -25.0 + k * 4.0
        pts = [(BX0 + 4.0, 3.5, z), (BX0 + 30.0, 3.5, z), (BX0 + 45.0, 3.5, zz), (chip_c[0] - 12.0, 3.5, zz)]
        C.trace(m, tr, f"bd_tr{k}", pts, w=1.2, mt="ccl_cu")
        paths.append([(p[0], p[1] + 0.8, p[2]) for p in pts])
    for k in range(3):
        C.chip(m, tr, f"bd_ic{k}", (BX0 + 60.0 + k * 9.0, 3.4, 4.0), 6.0, 4.0, h=1.2, pins=4)
    return g, foil, tr, paths, chip_c


def loss_race(m, root):
    """Two long traces side by side on separate cores: FR-4 and low-loss."""
    g = empty("race", root)
    out = {}
    for name, z, mt in (("fr4", 40.0, "fr4"), ("low", 62.0, "ccl_core")):
        bx(f"rc_{name}_core", (BX0, 0.0, z - 7.0), (BX1, 3.0, z + 7.0), m[mt], g)
        C.trace(m, g, f"rc_{name}_tr", [(BX0 + 3.0, 3.1, z), (BX1 - 3.0, 3.1, z)], w=1.6, mt="ccl_cu")
        C.chip(m, g, f"rc_{name}_tx", (BX0 + 6.0, 3.0, z), 7.0, 7.0, h=1.6, pins=4)
        C.chip(m, g, f"rc_{name}_rx", (BX1 - 6.0, 3.0, z), 7.0, 7.0, h=1.6, pins=4)
        out[name] = z
    return g, out


def stackup(m, root):
    """A multilayer AI board cut open: 24 copper/dielectric pairs with plated vias."""
    g = empty("stackup", root)
    x0, x1, z0, z1 = 20.0, 120.0, 40.0, 70.0
    y = 0.0
    for k in range(24):
        bx(f"su_d{k}", (x0, y, z0), (x1, y + 1.4, z1), m["ccl_core"], g)
        y += 1.4
        for s in range(6):
            xa = x0 + 2 + s * 16.5
            bx(f"su_c{k}_{s}", (xa, y, z0), (xa + 12.0, y + 0.45, z1), m["ccl_cu"], g)
        y += 0.45
    for s in range(5):
        xv = x0 + 15.5 + s * 16.5
        tube(f"su_via{s}", (xv, 0.0, z1 - 0.8), (xv, y, z1 - 0.8), 0.9, m["ccl_cu"], g, 12)
    return g, y, (x0, x1, z0, z1)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    mats(m)
    bx("floor", (-150.0, -3.0, -80.0), (260.0, 0.0, 90.0), m["sup_steel"], root)

    sh, cu_top = sheet(m, root)
    move(cu_top, [(F(0, 0.0), 14.0), (F(0, 0.6), 0.0)])  # top foil settles down onto the stack
    show(sh, [(F(0, 0), F(2, 0))])

    pr, plat, top = press(m, root)
    move(plat, [(F(0, 0), 0.0), (F(1, 0.15), 0.0), (F(1, 0.45), -13.6), (F(5, 0), -13.6)])
    rise(root, "pr_heat", (PX, top + 30.0, -30.0), 10, 0.9, m["ccl_heat"], [1], 0.4, 0.9, h=25.0,
         life=40, spread=(26.0, 20.0))
    rise(root, "pr_heat_lo", (PX - 40.0, 10.0, -30.0), 5, 0.8, m["ccl_heat"], [1], 0.4, 0.9, h=20.0,
         life=40, spread=(2.0, 18.0))

    bd, foil, tr, paths, chip_c = board(m, root)
    show(foil, [(F(0, 0), F(2, 0.30))])
    show(tr, [(F(2, 0.30), F(5, 0))])
    for k, p in enumerate(paths):
        run(root, f"sig{k}", p, 3, 0.8, m["ccl_sig"], [2, 4], 0.40 + 0.02 * k, 0.85, 35)

    rc, zz = loss_race(m, root)
    show(rc, [(F(3, 0), F(5, 0))])
    zf, zl = zz["fr4"], zz["low"]
    run(root, "rc_low_b", [(BX0 + 10.0, 4.5, zl), (BX1 - 10.0, 4.5, zl)], 6, 1.1, m["ccl_sig"], [3], 0.05, 0.8, 40)
    run(root, "rc_fr4_b", [(BX0 + 10.0, 4.5, zf), (BX0 + 48.0, 4.5, zf)], 6, 1.1, m["ccl_weak"], [3], 0.05, 0.8, 22)
    rise(root, "rc_fr4_heat", (BX0 + 35.0, 4.0, zf), 8, 0.6, m["ccl_heat"], [3], 0.1, 0.9, h=12.0, life=30,
         spread=(14.0, 2.0))

    su, sy, (sx0, sx1, sz0, sz1) = stackup(m, root)
    show(su, [(F(4, 0), F(5, 0))])

    C.tags(root, {
        0: [("copper foil, 12-35 um", (LX1, 29.0, LZ1)), ("resin: the insulator", (LX0, 21.0, LZ1)),
            ("woven glass cloth plies", (70.0, 17.5, LZ1)), ("bottom foil", (LX0, 3.0, LZ1))],
        1: [("hot platen, ~200 C", (PX, top + 18.0, -5.0)), ("books: plate, foil, prepreg", (PX + 30.0, 22.0, -5.0)),
            ("vacuum pulls out air", (PX + 55.0, 8.0, -5.0))],
        2: [("foil etched into traces", (BX0 + 30.0, 3.5, -32.0)), ("signals to the chip", (chip_c[0], 6.0, -6.0)),
            ("one layer of many", (BX0 + 5.0, 3.0, 10.0))],
        3: [("FR-4: signal fades as heat", (BX0 + 45.0, 5.0, zf)), ("low-loss: low Dk and Df", (BX1 - 25.0, 5.0, zl)),
            ("56-112 Gb/s lanes", (BX0 + 6.0, 5.0, zl))],
        4: [("24-layer AI board", (sx1, sy, sz1)), ("plated vias join layers", (sx0 + 15.5, sy * 0.5, sz1)),
            ("ROG, 6274.TW, 600183.SS", (BX1 - 20.0, 6.0, -15.0))],
    })
    C.done(SLUG, BEATS, [
        [(0.0, frame((70.0, 15.0, -5.0), 120.0, 0.35, 0.40)), (1.0, frame((70.0, 15.0, -5.0), 100.0, 0.20, 0.30))],
        frame((PX, 40.0, -30.0), 120.0, 0.30, 0.20),
        [(0.0, frame((195.0, 3.0, -15.0), 100.0, 0.25, 0.55)), (1.0, frame((200.0, 3.0, -15.0), 80.0, 0.10, 0.50))],
        frame((197.0, 3.0, 51.0), 100.0, 0.10, 0.60),
        frame((120.0, 15.0, 15.0), 240.0, 0.30, 0.45),
    ], root)


if __name__ == "__main__":
    build()
