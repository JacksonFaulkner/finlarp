"""The five HBM STACK zoom-ins, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md), built from the stack pieces in hbm_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/hbm_zooms.py [-- tsv base channels bond cowos]

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


ZOOMS = {"tsv": tsv, "base": base, "channels": channels, "bond": bond, "cowos": cowos}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ZOOMS)
    for name in which:
        ZOOMS[name]()
