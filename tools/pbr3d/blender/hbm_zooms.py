"""The six HBM STACK zoom-ins, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md), built from the stack pieces in hbm_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/hbm_zooms.py [-- tsv base channels bond cowos die]

For each zoom it writes blender/hbm_<name>.blend and assets/hbm_<name>.glb.

  a tsv       a copper TSV and its microbumps, cut open: a signal runs down the column, the dies
              thin, the bumps shrink
  b base      the base logic die with the DRAM dies lifted off: the PHY to the GPU, the HBM4
              foundry note, the test logic
  c channels  one stack's 1024-bit bus, split into 16 channels, then 32 for HBM4, each running
              on its own
  d bond      microbumps on the left, hybrid bonding on the right, and the height limit moving
              from 720 to 775 um
  e cowos     the GPU and stacks on one interposer, more stacks on a bigger one, fewer
              interposers per wafer, and the package on its substrate
  f die       inside one DRAM core die: lifted out of the stack and laid flat, the TSV field
              down its middle, banks grouped into channels, one bank tiled into mats, and cells

One beat is SEC (8) seconds at 24 fps; every zoom is four beats (diagrams_nodes/hbm/zoom.rs).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, disc, key, label, show, tube  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import hbm_kit as K  # noqa: E402
from hbm_kit import gbox  # noqa: E402
from hbm_kit import BASE_HALF, BUMP_T, DIE_T, END, GPU_X, TSV_X, die_bottom, die_top  # noqa: E402

BEATS = 4


def begin(name):
    m, root = start(name, BEATS, page="hbm")
    K.mats(m)
    return m, root


def squash(d, centre, s):
    """Keys die/bump group `d` to scale (1, 1, s) about height `centre`, so its middle stays put."""
    return (1.0, 1.0, s), P(0, centre * (1.0 - s), 0)


def set_squash(d, frames_s, centre):
    for f, s in frames_s:
        scale, loc = squash(d, centre, s)
        key(d, f, "scale", scale)
        key(d, f, "location", loc)


# ---- a: the TSV ---------------------------------------------------------------------------


def tsv():
    m, root = begin("tsv")
    s = K.stack(root, m, 0.0, 3, "tsv")
    for k, d in enumerate(s.dies):
        mid = (die_bottom(k) + die_top(k)) / 2
        set_squash(d, [(0, 1.0), (F(2, 0.15), 1.0), (F(2, 0.5), 0.55), (F(2, 0.95), 0.55), (F(3, 0.0), 1.0), (F(3, 0.1), 1.0)], mid)
    for k, b in enumerate(s.bumps):
        c = die_bottom(k) - BUMP_T / 2
        set_squash(b, [(0, 1.0), (F(3, 0.2), 1.0), (F(3, 0.75), 0.5), (END, 0.5)], c)
    for x in TSV_X:
        K.dots(root, m, f"sig{int(x)}_", [(x, die_top(2) + 10, 0.0), (x, 20.0, 0.0)], 3, "data", 1, 0.05, 0.5, 90, size=12.0)
    label("copper TSV", (110.0, 150.0, 0.0), root, beat(0))
    label("microbump", (110.0, 80.0, 0.0), root, beat(0))
    label("signal down the TSV", (-150.0, 150.0, 0.0), root, beat(1))
    label("dies thinned to 30-50 um", (200.0, 120.0, 0.0), root, beat(2))
    label("bump pitch ~40 um -> 10 um", (200.0, 60.0, 0.0), root, beat(3))
    camera(root, [
        ((0.0, 150.0, 0.0), 700.0, 0.50, 0.12),
        ((0.0, 150.0, 0.0), 680.0, 0.50, 0.12),
        ((0.0, 150.0, 0.0), 650.0, 0.45, 0.12),
        ((0.0, 150.0, 0.0), 650.0, 0.42, 0.12),
    ])
    finish("tsv", page="hbm")


# ---- b: the base die ----------------------------------------------------------------------


def base():
    m, root = begin("base")
    s = K.stack(root, m, 0.0, 3, "base", phy=1)
    K.lift(s, [(F(0, 0.35), 0.0), (F(0, 0.9), 1.0)], step=180.0)
    for x in TSV_X:
        box(f"pad{int(x)}", (x - 22, 70.0, -22), (x + 22, 76, 0), m["copper"], root)
    box("gpu_die", (450, 0, -400), (950, 380, 0), m["gpu"], root)
    K.dots(root, m, "phy", [(205, 45, 0.0), (440, 110, 0.0)], 3, "data", 1, 0.1, 0.6, 60, size=12.0)
    test = gbox("test_logic", (-130, 71, -150), (130, 76, -20), m["read"], root)
    show(test, [(F(3, 0.0), END)])
    label("PHY: 1024 bits to the GPU", (193, 40, -60), root, [(F(1, 0.0), F(2, 0))])
    label("HBM4: foundry logic die (reported)", (-120, 95, 0.0), root, [(F(2, 0.0), F(3, 0))])
    label("base logic die: test logic", (-120, 74, -20), root, [(F(3, 0.0), END)])
    label("copper landing pads", (-150, 70, 0.0), root, beat(0))
    camera(root, [
        ((0.0, 70.0, 0.0), 800.0, 0.45, 0.20),
        ((330.0, 150.0, 0.0), 1500.0, 0.30, 0.16),
        ((0.0, 90.0, 0.0), 900.0, 0.40, 0.18),
        ((0.0, 90.0, 0.0), 800.0, 0.40, 0.18),
    ])
    finish("base", page="hbm")


# ---- c: the channels -----------------------------------------------------------------------


def channels():
    m, root = begin("channels")
    s = K.stack(root, m, -600.0, 4, "chan", phy=1)
    x_edge = -600.0 + BASE_HALF
    box("gpu_die", (0.0, 0.0, -400.0), (GPU_X, 380.0, 0.0), m["gpu"], root)
    bus = gbox("bus_1024", (x_edge, 60.0, -30.0), (0.0, 120.0, 0.0), m["data"], root)
    show(bus, [(0, F(1, 0.0))])
    n16 = [60.0 + i * 230.0 / 15 for i in range(16)]
    n32 = [60.0 + i * 230.0 / 31 for i in range(32)]
    ch16 = empty_group(root, "ch16")
    for i, y in enumerate(n16):
        tube(f"c16_{i}", (x_edge, y, 0.0), (0.0, y, 0.0), 5.0, m["data"], ch16, verts=8)
    show(ch16, [(F(1, 0.0), F(2, 0.0))])
    ch32 = empty_group(root, "ch32")
    for i, y in enumerate(n32):
        tube(f"c32_{i}", (x_edge, y, 0.0), (0.0, y, 0.0), 3.0, m["data"], ch32, verts=8)
    show(ch32, [(F(2, 0.0), END)])
    for j in range(8):
        y = 60.0 + j * 230.0 / 7
        K.dots(root, m, f"lane{j}_", [(x_edge, y, 0.0), (0.0, y, 0.0)], 2, "read", 3, 0.05 + 0.04 * j, 0.6 + 0.02 * j, 50, size=9.0)
    label("1024 bits from one HBM3 stack", (-200.0, 170.0, 0.0), root, beat(0))
    label("split into 16 channels", (-200.0, 300.0, 0.0), root, beat(1))
    label("HBM4: 32 channels, 2048 bits", (-200.0, 320.0, 0.0), root, beat(2))
    label("each channel runs on its own", (-200.0, 340.0, 0.0), root, beat(3))
    camera(root, [
        ((-250.0, 180.0, 0.0), 1700.0, 0.20, 0.10),
        ((-250.0, 180.0, 0.0), 1700.0, 0.20, 0.10),
        ((-250.0, 180.0, 0.0), 1700.0, 0.20, 0.10),
        ((-250.0, 180.0, 0.0), 1700.0, 0.20, 0.10),
    ])
    finish("channels", page="hbm")


def empty_group(root, name):
    from sand_overview import empty

    return empty(name, root)


# ---- d: microbumps against hybrid bonding -------------------------------------------------


def bond():
    m, root = begin("bond")
    left = K.stack(root, m, -700.0, 16, "micro")
    right = K.stack(root, m, 700.0, 16, "hybrid")
    # Hybrid: every die drops onto the one below and the bumps go, so the stack shortens.
    for k, d in enumerate(right.dies):
        key(d, F(1, 0.1), "location", P(0, 0, 0))
        key(d, F(1, 0.5), "location", P(0, -BUMP_T * (k + 1), 0))
    for b in right.bumps:
        show(b, [(0, F(1, 0.45))])
    limit_old = K.limit_plane(root, m, -1200.0, 1200.0, K.LIMIT_OLD_Y, z0=-900.0, name="limit_720",
                              intervals=[(F(2, 0.0), F(2, 0.5))])
    limit_new = K.limit_plane(root, m, -1200.0, 1200.0, K.LIMIT_NEW_Y, z0=-900.0, name="limit_775",
                              intervals=[(F(2, 0.5), END)])
    label("microbumps: a gap per joint", (-500.0, 150.0, 0.0), root, beat(0))
    label("hybrid bonding: no gap", (860.0, 400.0, 0.0), root, beat(1))
    label("height limit 720 -> 775 um", (-300.0, K.LIMIT_NEW_Y + 60, 0.0), root, [(F(2, 0.0), END)])
    label("16-high under the raised limit", (860.0, 700.0, 0.0), root, beat(3))
    camera(root, [
        ((0.0, 560.0, 0.0), 3300.0, 0.25, 0.10),
        ((0.0, 560.0, 0.0), 3300.0, 0.25, 0.10),
        ((0.0, 600.0, 0.0), 3300.0, 0.25, 0.10),
        ((0.0, 600.0, 0.0), 3800.0, 0.22, 0.10),
    ])
    finish("bond", page="hbm")


# ---- e: CoWoS -----------------------------------------------------------------------------


WZ = 4000.0  # the wafer sits well behind the package so the top-down beat sees only it


def cowos():
    m, root = begin("cowos")
    K.package(root, m)
    import bpy

    inter = bpy.data.objects["interposer"]
    sub = bpy.data.objects["substrate"]
    for obj in (inter, sub):
        key(obj, 0, "scale", (1.0, 1.0, 1.0))
        key(obj, F(1, 0.1), "scale", (1.0, 1.0, 1.0))
        key(obj, F(1, 0.6), "scale", (1.5, 1.0, 1.0))
    for x in K.STACK_XS:
        K.stack(root, m, x, 8, f"s{int(x)}", phy=1 if x < 0 else -1)
    extra = []
    for x in (-2550.0, -2100.0, 2100.0, 2550.0):
        s = K.stack(root, m, x, 8, f"x{int(x)}", phy=1 if x < 0 else -1)
        show(s.g, [(F(1, 0.2), END)])
        extra.append(s)
    # beat 2: a wafer of interposers, many small ones and then fewer large ones
    wafer = disc("wafer", (0.0, -700.0, -WZ), 1800.0, 20.0, m["wafer"], root)
    show(wafer, beat(2))
    small, big = [], []
    for i, x in enumerate((-800.0, -400.0, 0.0, 400.0, 800.0)):
        for j, z in enumerate((-WZ + 500.0, -WZ + 250.0, -WZ, -WZ - 250.0, -WZ - 500.0)):
            small.append(gbox(f"sm{i}{j}", (x - 150, -690, z - 90), (x + 150, -680, z + 90), m["interposer"], root))
    for i, x in enumerate((-600.0, 0.0, 600.0)):
        for j, z in enumerate((-WZ + 400.0, -WZ - 400.0)):
            big.append(gbox(f"bg{i}{j}", (x - 250, -690, z - 190), (x + 250, -680, z + 190), m["interposer"], root))
    for g in small:
        show(g, [(F(2, 0.0), F(2, 0.5))])
    for g in big:
        show(g, [(F(2, 0.5), END)])
    # beat 3: from the side, the package on its substrate
    label("GPU", (0.0, 420.0, 40.0), root, beat(0))
    label("HBM stacks", (-850.0, 600.0, 0.0), root, beat(0))
    label("one interposer for all", (1150.0, -60.0, 0.0), root, beat(0))
    label("4 more stacks, wider interposer", (2100.0, 720.0, 0.0), root, beat(1))
    label("fewer per wafer as they grow", (0.0, -680.0, -WZ + 900.0), root, beat(2))
    label("on a package substrate", (1700.0, -220.0, 0.0), root, beat(3))
    camera(root, [
        ((0.0, 260.0, 0.0), 5200.0, 0.30, 0.40),
        ((700.0, 250.0, 0.0), 7000.0, 0.12, 0.35),
        ((0.0, -700.0, -WZ), 4200.0, 0.10, 0.95),
        ((1500.0, 100.0, 0.0), 4000.0, 0.15, 0.08),
    ])
    finish("cowos", page="hbm")


# ---- f: inside one DRAM die ---------------------------------------------------------------
# One core die out of the stack, laid flat and seen from above. The floor plan is schematic
# (layouts differ by maker): a TSV field down the middle, banks either side, the banks grouped
# into channels; then one bank opened up into mats with sense-amp stripes, and one mat's cells.

DX0, DX1 = -1200.0, 1200.0  # the flat die, x
DZ0, DZ1 = -1700.0, -100.0  # and z (the camera looks down from +z, above)
DT = 40.0  # its thickness
STRIP = 120.0  # half width of the TSV field
BANK_W, BANK_GAP = 480.0, 25.0
ROWS = 4
CHANNEL_KEYS = ("ch0", "ch1", "ch2", "ch3")


def bank_boxes():
    """(side, col, row) -> (x0, x1, z0, z1) of each bank: 2 columns x 4 rows on each side."""
    out = {}
    row_h = (DZ1 - DZ0 - (ROWS + 1) * BANK_GAP) / ROWS
    for side in (-1, 1):
        for col in range(2):
            a = STRIP + BANK_GAP + col * (BANK_W + BANK_GAP)
            x0, x1 = sorted((side * a, side * (a + BANK_W)))
            for row in range(ROWS):
                z0 = DZ0 + BANK_GAP + row * (row_h + BANK_GAP)
                out[(side, col, row)] = (x0, x1, z0, z0 + row_h)
    return out


def die():
    m, root = begin("die")
    from sand_overview import mat

    m["ch0"] = mat("hbm_ch0", (0.35, 0.60, 0.95), rough=0.45)
    m["ch1"] = mat("hbm_ch1", (0.35, 0.80, 0.50), rough=0.45)
    m["ch2"] = mat("hbm_ch2", (0.70, 0.50, 0.95), rough=0.45)
    m["ch3"] = mat("hbm_ch3", (0.95, 0.45, 0.55), rough=0.45)
    m["mat_tile"] = mat("hbm_mat_tile", (0.78, 0.52, 0.30), rough=0.5)
    m["sense"] = mat("hbm_sense", (0.30, 0.95, 1.0), emit=(0.25, 0.9, 1.0), strength=1.6)
    m["wld"] = mat("hbm_wordline_drv", (0.55, 0.58, 0.66), metal=0.3, rough=0.5)
    m["cap"] = mat("hbm_cap", (0.70, 0.74, 0.80), metal=0.7, rough=0.3)

    # beat 0: an 8-high stack; die 4 rises out of it
    st = K.stack(root, m, 0.0, 8, "st")
    show(st.g, beat(0))
    d = st.dies[4]
    for f, dx in ((F(0, 0.0), 0.0), (F(0, 0.25), 0.0), (F(0, 0.75), 520.0)):  # slides out sideways
        key(d, f, "location", P(dx, 0, 0))
    label("8 DRAM dies on a base die", (-260.0, 300.0, 0.0), root, [(F(0, 0.05), F(0, 0.5))])
    label("one core die, 30-50 um thick", (520.0 + 170.0, die_top(4), 0.0), root, [(F(0, 0.55), F(1, 0))])

    # beats 1-3: the same die, flat and large, seen from above
    flat = gbox("die_flat", (DX0, -DT, DZ0), (DX1, 0.0, DZ1), m["dram"], root)
    show(flat, [(F(1, 0), END)])
    # the TSV field: copper ends in three columns down the middle
    tsv_g = []
    for r in range(14):
        z = DZ0 + 70.0 + r * (DZ1 - DZ0 - 140.0) / 13
        for c, x in enumerate((-70.0, 0.0, 70.0)):
            t = disc(f"tsv_end{r}_{c}", (x, 4.0, z), 22.0, 10.0, m["copper"], root, verts=16)
            show(t, [(F(1, 0.05 + 0.02 * r), END)])
            tsv_g.append((r, t))
    strip = gbox("tsv_field", (-STRIP, 0.0, DZ0), (STRIP, 2.0, DZ1), m["grey"], root)
    show(strip, [(F(1, 0.0), END)])
    # signals: cyan dots light the TSV ends row by row, top to bottom, twice
    for r in range(14):
        z = DZ0 + 70.0 + r * (DZ1 - DZ0 - 140.0) / 13
        dot = disc(f"sig{r}", (0.0, 12.0, z), 30.0, 6.0, m["data"], root, verts=16)
        a = 0.15 + 0.03 * r
        show(dot, [(F(1, a), F(1, a + 0.12)), (F(1, a + 0.42), F(1, a + 0.54))])
    label("TSV field: data, command and power", (0.0, 20.0, DZ1 + 40.0), root, beat(1))
    label("TSVs pass down through the die", (90.0, 20.0, (DZ0 + DZ1) / 2), root, [(F(1, 0.4), F(2, 0))])

    # beat 2: the banks either side, coloured by the channel they belong to
    boxes = bank_boxes()
    detail_key = (-1, 1, 3)  # the bank opened up in beat 3: left side, outer column, top row
    for (side, col, row), (x0, x1, z0, z1) in boxes.items():
        ch = (0 if side < 0 else 2) + (0 if row < 2 else 1)
        b = gbox(f"bank{side}_{col}_{row}", (x0, 0.0, z0), (x1, 14.0, z1), m[CHANNEL_KEYS[ch]], root)
        u = 0.05 + 0.04 * (row + 4 * col + (0 if side < 0 else 2))
        show(b, [(F(2, min(u, 0.6)), END)])
    label("16 banks drawn, each its own array", (-700.0, 30.0, DZ1 - 10.0), root, beat(2))
    label("banks grouped into channels", (700.0, 30.0, DZ0 + 380.0), root, [(F(2, 0.45), F(3, 0))])
    label("schematic floor plan", (0.0, 30.0, DZ0 - 10.0), root, [(F(2, 0.7), F(3, 0))])

    # beat 3: inside one bank: a 4 x 4 grid of mats, sense-amp stripes between mat rows,
    # word-line drivers between mat columns; then one mat's cells (capacitors)
    x0, x1, z0, z1 = boxes[detail_key]
    nm, gap = 4, 18.0
    mw = (x1 - x0 - (nm + 1) * gap) / nm
    mh = (z1 - z0 - (nm + 1) * gap) / nm
    for i in range(nm):
        for j in range(nm):
            mx0 = x0 + gap + i * (mw + gap)
            mz0 = z0 + gap + j * (mh + gap)
            t = gbox(f"mat{i}{j}", (mx0, 14.0, mz0), (mx0 + mw, 22.0, mz0 + mh), m["mat_tile"], root)
            show(t, [(F(3, 0.08 + 0.01 * (i + nm * j)), END)])
    for j in range(nm + 1):
        z = z0 + j * (mh + gap)
        s = gbox(f"sense{j}", (x0 + gap, 14.0, z + 2), (x1 - gap, 24.0, z + gap - 2), m["sense"], root)
        show(s, [(F(3, 0.2), END)])
    for i in range(nm + 1):
        x = x0 + i * (mw + gap)
        w = gbox(f"wld{i}", (x + 2, 14.0, z0 + gap), (x + gap - 2, 23.0, z1 - gap), m["wld"], root)
        show(w, [(F(3, 0.25), END)])
    # one mat's cells: a grid of capacitors standing on the top-left mat
    cx0, cz0 = x0 + gap, z0 + gap + (nm - 1) * (mh + gap)
    for i in range(6):
        for j in range(6):
            c = disc(f"cap{i}{j}", (cx0 + (i + 0.5) * mw / 6, 30.0, cz0 + (j + 0.5) * mh / 6), mw / 22, 16.0,
                     m["cap"], root, verts=12)
            show(c, [(F(3, 0.55 + 0.004 * (i + 6 * j)), END)])
    bx, bz = (x0 + x1) / 2, (z0 + z1) / 2
    label("one bank: tiled into mats", (bx, 40.0, z1), root, [(F(3, 0.05), F(3, 0.5))])
    label("sense-amp stripes: the row buffer", (x1, 30.0, bz), root, [(F(3, 0.25), F(4, 0))])
    label("a mat: about 512 x 512 cells", (cx0 + mw / 2, 40.0, cz0 + mh), root, [(F(3, 0.5), F(4, 0))])
    label("each cell: 1 transistor + 1 capacitor", (cx0 + mw, 40.0, cz0 + mh / 2), root, [(F(3, 0.65), F(4, 0))])

    camera(root, [
        ((260.0, 300.0, 0.0), 1700.0, 0.45, 0.25),
        ((0.0, 0.0, (DZ0 + DZ1) / 2), 3300.0, 0.0, 1.15),
        ((0.0, 0.0, (DZ0 + DZ1) / 2), 4000.0, 0.05, 1.10),
        ((bx, 0.0, bz), 1100.0, 0.10, 1.05),
    ])
    finish("die", page="hbm")


ZOOMS = {"tsv": tsv, "base": base, "channels": channels, "bond": bond, "cowos": cowos, "die": die}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ZOOMS)
    for name in which:
        ZOOMS[name]()
