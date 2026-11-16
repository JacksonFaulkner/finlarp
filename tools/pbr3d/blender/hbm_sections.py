"""The ten HBM STACK write-up sections, each a 3D picture authored in Blender and exported for
pbr3d in the SAND template (docs/diagram-pages.md). The stack's pieces come from hbm_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/hbm_sections.py [-- 3 5]

For each section it writes blender/hbm_sec<N>.blend and assets/hbm_sec<N>.glb.

  1 what happens   the package, the dies pulled apart, a bus from the stacks to the GPU (3 beats)
  2 parts          DRAM dies, base logic die, TSVs, microbumps, interposer and GPU (5 beats)
  3 building       dies dropped on the base die, pulled apart, bonded, tested, mounted (5 beats)
  4 generations    data pins, rate per pin, bandwidth per stack (3 beats)
  5 height         8-, 12- and 16-high under the limit, which rises from 720 to 775 um (3 beats)
  6 bonding        microbumps, bonded on bumps, hybrid bonding (3 beats)
  7 packaging      interposer wiring, the package on its substrate, packaging capacity (3 beats)
  8 makers         Micron, SK hynix and Samsung, one in the spotlight each (3 beats)
  9 risks          packaging queue, yield with height, heat in tall stacks (3 beats)
  10 sources       seven source cards lighting up in groups (3 beats)

One beat is SEC (8) seconds at 24 fps.
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, beat, box, disc, empty, key, label, pivot, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
import hbm_kit as K  # noqa: E402
from hbm_kit import BASE_HALF, BUMP_T, DIE_HALF, END, GPU_X, STACK_XS, TSV_X, die_bottom, die_top, gbox  # noqa: E402


def begin(n, beats):
    m, root = start(f"sec{n}", beats, page="hbm")
    K.mats(m)
    return m, root


def drop(d, f0, height=300.0, dur=12):
    """Die group `d` starts `height` above its place at frame f0 and drops onto it."""
    key(d, f0, "location", P(0, height, 0))
    key(d, f0 + dur, "location", P(0, 0, 0))


def package(root, m, n=8):
    """The interposer, substrate and GPU with four stacks of n dies each."""
    K.package(root, m)
    return [K.stack(root, m, x, n, f"p{int(x)}", phy=1 if x < 0 else -1) for x in STACK_XS]


def bus_dots(root, m, b, u0, u1, life=70):
    """Cyan blobs from each stack's PHY edge across the interposer to the GPU, through beat b."""
    for s_x in STACK_XS:
        phy = 1 if s_x < 0 else -1
        edge = s_x + phy * (BASE_HALF + 4)
        gx = -GPU_X if phy > 0 else GPU_X
        if abs(s_x) < 1000:
            pts = [(edge, 60.0, 0.0), (gx, 200.0, 0.0)]
        else:
            pts = [(edge, 60.0, 0.0), (edge, 660.0, 0.0), (gx, 660.0, 0.0), (gx, 220.0, 0.0)]
        K.dots(root, m, f"bus{int(s_x)}_{b}_", pts, 3, "data", b, u0, u1, life, size=26.0)


def read_dots(root, m, x, b, u0, u1, top, life=60):
    """Yellow blobs down each TSV column of the stack at x, from `top` to the base, through b."""
    for tx in TSV_X:
        K.dots(root, m, f"read{int(x)}_{int(tx)}_{b}_", [(x + tx, top, 0.0), (x + tx, 30.0, 0.0)],
               3, "read", b, u0, u1, life, size=12.0)


def pkg_item(name):
    return bpy.data.objects[name]


# ---- 1. what happens -------------------------------------------------------------------------


def sec1():
    m, root = begin(1, 3)
    stacks = package(root, m, 8)
    for s in stacks:
        K.lift(s, [(F(0, 0), 0.0), (F(1, 0.1), 0.0), (F(1, 0.6), 1.0), (F(2, 0.4), 0.0)], step=35.0)
        for b in s.bumps:
            show(b, [(F(1, 0.3), END)])
    bus_dots(root, m, 2, 0.1, 0.6)
    label("GPU", (0.0, 420.0, 40.0), root, beat(0))
    label("HBM stacks beside the GPU", (-1500.0, 640.0, 0.0), root, beat(0))
    label("silicon interposer", (1150.0, -60.0, 0.0), root, beat(0))
    label("microbumps join each die", (-660.0, 330.0, 0.0), root, beat(1))
    label("PHY drives the bus to the GPU", (-300.0, 330.0, 0.0), root, beat(2))
    camera(root, [
        ((0.0, 260.0, 0.0), 5200.0, 0.30, 0.16),
        ((-850.0, 450.0, 0.0), 2600.0, 0.24, 0.12),
        ((-300.0, 330.0, 0.0), 4300.0, 0.30, 0.14),
    ])
    finish("sec1", page="hbm")


# ---- 2. parts ----------------------------------------------------------------------------------

SX = -850.0


def sec2():
    m, root = begin(2, 5)
    K.package(root, m)
    s = K.stack(root, m, SX, 8, "parts", phy=1)
    K.lift(s, [(F(0, 0), 0.0), (F(1, 0.1), 0.0), (F(1, 0.5), 1.0), (F(2, 0.25), 1.0), (F(2, 0.6), 0.0),
               (F(3, 0.1), 0.0), (F(3, 0.5), 1.0), (F(4, 0.0), 1.0), (F(4, 0.4), 0.0)], step=60.0)
    for b in s.bumps:
        show(b, [(F(3, 0.2), END)])
    for name in ("interposer", "substrate", "gpu"):
        show(pkg_item(name), [(F(4, 0.0), END)])
    label("DRAM dies", (SX + DIE_HALF + 10, 330.0, 0.0), root, beat(0))
    label("base logic die", (SX + BASE_HALF + 10, 35.0, 0.0), root, beat(1))
    label("TSVs: copper through each die", (SX + 130.0, 300.0, 0.0), root, beat(2))
    label("microbumps", (SX + 130.0, 120.0, 0.0), root, beat(3))
    label("silicon interposer", (-100.0, -60.0, 0.0), root, beat(4))
    label("GPU", (500.0, 400.0, 40.0), root, beat(4))
    camera(root, [
        ((SX, 300.0, 0.0), 1400.0, 0.30, 0.10),
        ((SX, 60.0, 0.0), 1000.0, 0.30, 0.12),
        ((SX, 320.0, 0.0), 1700.0, 0.30, 0.10),
        ((SX, 540.0, 0.0), 2500.0, 0.30, 0.12),
        ((-300.0, 250.0, 0.0), 3800.0, 0.30, 0.14),
    ])
    finish("sec2", page="hbm")


# ---- 3. building -------------------------------------------------------------------------------


def sec3():
    m, root = begin(3, 5)
    K.package(root, m)
    s = K.stack(root, m, SX, 8, "build", phy=1)
    for k, d in enumerate(s.dies):
        u = 0.04 + 0.11 * k
        drop(d, F(0, u))
        show(d, [(F(0, u), END)])
    K.lift(s, [(F(1, 0.1), 0.0), (F(1, 0.5), 1.0), (F(2, 0.5), 0.0)], step=60.0)
    for b in s.bumps:
        show(b, [(F(1, 0.2), END)])
    test = gbox("test_field", (SX - 130, 71, -150), (SX + 130, 76, -20), m["read"], root)
    show(test, [(F(3, 0.0), END)])
    for name in ("interposer", "substrate", "gpu"):
        show(pkg_item(name), [(F(4, 0.0), END)])
    bus_dots(root, m, 4, 0.2, 0.6)
    # Beat 3: the test field sits under the dies, so the test signal is shown running down the TSVs
    read_dots(root, m, SX, 3, 0.1, 0.8, die_top(7) - 10)
    label("1. dies placed one by one", (SX + DIE_HALF + 10, 300.0, 0.0), root, beat(0))
    label("2. thinned, TSVs and bumps", (SX + 130.0, 150.0, 0.0), root, beat(1))
    label("3. bonded onto the base die", (SX + BASE_HALF + 10, 200.0, 0.0), root, beat(2))
    label("4. tested through the TSVs", (SX - 110.0, 300.0, 0.0), root, beat(3))
    label("5. mounted beside the GPU", (-300.0, 330.0, 0.0), root, beat(4))
    camera(root, [
        ((SX, 300.0, 0.0), 1400.0, 0.30, 0.10),
        ((SX, 440.0, 0.0), 2300.0, 0.30, 0.10),
        ((SX, 300.0, 0.0), 1400.0, 0.30, 0.10),
        ((SX, 300.0, 0.0), 1400.0, 0.30, 0.10),
        ((-300.0, 250.0, 0.0), 3800.0, 0.30, 0.14),
    ])
    finish("sec3", page="hbm")


# ---- 4. generations ----------------------------------------------------------------------------


def bar(root, m, name, x, h, f0, f1, iv):
    """A bar standing at x that grows to height h over [f0, f1], shown during the intervals `iv`."""
    g = empty(f"{name}_show", root)
    b = pivot(f"{name}_grow", (x, 0.0, 0.0), g)
    box(f"{name}_box", (-130, 0.0, -130), (130, h, 130), m["dram"], b)
    scale_keys(b, [(0, (1, 1, OFF)), (f0, (1, 1, OFF)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    show(g, iv)
    return b


def sec4():
    m, root = begin(4, 3)
    bar(root, m, "pin3", -400.0, 500.0, F(0, 0.05), F(0, 0.4), beat(0))
    bar(root, m, "pin4", 400.0, 1000.0, F(0, 0.05), F(0, 0.4), beat(0))
    bar(root, m, "rate3", -400.0, 400.0, F(1, 0.05), F(1, 0.4), beat(1))
    bar(root, m, "rate4", 400.0, 500.0, F(1, 0.05), F(1, 0.4), beat(1))
    bar(root, m, "bw3", -400.0, 400.0, F(2, 0.05), F(2, 0.4), beat(2))
    bar(root, m, "bw4", 400.0, 1000.0, F(2, 0.05), F(2, 0.4), beat(2))
    label("HBM3: 1024 data pins", (-400.0, 560.0, 0.0), root, beat(0))
    label("HBM4: 2048 data pins", (400.0, 1060.0, 0.0), root, beat(0))
    label("HBM3: 6.4 Gb/s per pin", (-400.0, 460.0, 0.0), root, beat(1))
    label("HBM4: 8 Gb/s per pin", (400.0, 560.0, 0.0), root, beat(1))
    label("HBM3: 819 GB/s per stack", (-400.0, 460.0, 0.0), root, beat(2))
    label("HBM4: up to 2 TB/s per stack", (400.0, 1060.0, 0.0), root, beat(2))
    camera(root, [((0.0, 520.0, 0.0), 4800.0, 0.0, 0.05)] * 3)
    finish("sec4", page="hbm")


# ---- 5. height ---------------------------------------------------------------------------------


def sec5():
    m, root = begin(5, 3)
    s = K.stack(root, m, 0.0, 16, "height", glow=True)
    for k in range(8, 16):
        f0 = F(1, 0.1) if k < 12 else F(2, 0.1)
        drop(s.dies[k], f0)
        show(s.dies[k], [(f0, END)])
    for k in range(16):
        if k <= 5:
            show(s.glows[k], [(F(1, 0.5), END)])
        else:
            show(s.glows[k], [])
    K.limit_plane(root, m, -1000.0, 1000.0, K.LIMIT_OLD_Y, z0=-900.0, name="limit_720",
                  intervals=[(0, F(2, 0.45))])
    K.limit_plane(root, m, -1000.0, 1000.0, K.LIMIT_NEW_Y, z0=-900.0, name="limit_775",
                  intervals=[(F(2, 0.45), END)])
    label("8-high, under the limit", (250.0, 400.0, 0.0), root, beat(0))
    label("12-high: heat starts to build", (250.0, 700.0, 0.0), root, beat(1))
    label("16-high: limit 720 -> 775 um", (250.0, 1000.0, 0.0), root, beat(2))
    label("lower dies run hottest", (250.0, 200.0, 0.0), root, [(F(1, 0.5), END)])
    camera(root, [
        ((0.0, 520.0, 0.0), 2700.0, 0.30, 0.10),
        ((0.0, 560.0, 0.0), 2800.0, 0.30, 0.10),
        ((0.0, 560.0, 0.0), 2800.0, 0.30, 0.10),
    ])
    finish("sec5", page="hbm")


# ---- 6. bonding --------------------------------------------------------------------------------


def sec6():
    m, root = begin(6, 3)
    s = K.stack(root, m, 0.0, 8, "bond", phy=0)
    K.lift(s, [(F(0, 0), 1.0), (F(1, 0.4), 1.0), (F(1, 0.6), 0.0)], step=60.0)
    for k, d in enumerate(s.dies):
        key(d, F(2, 0.1), "location", P(0, 0, 0))
        key(d, F(2, 0.6), "location", P(0, -BUMP_T * (k + 1), 0))
    for b in s.bumps:
        show(b, [(0, F(2, 0.4))])
    label("microbump: a gap per joint", (250.0, 150.0, 0.0), root, beat(0))
    label("bonded on bumps: a gap remains", (250.0, 300.0, 0.0), root, beat(1))
    label("hybrid bonding: copper, no gap", (250.0, 250.0, 0.0), root, beat(2))
    camera(root, [
        ((0.0, 500.0, 0.0), 2400.0, 0.30, 0.10),
        ((0.0, 400.0, 0.0), 2100.0, 0.30, 0.10),
        ((0.0, 400.0, 0.0), 2000.0, 0.30, 0.10),
    ])
    finish("sec6", page="hbm")


# ---- 7. packaging ------------------------------------------------------------------------------


def sec7():
    m, root = begin(7, 3)
    package(root, m, 8)
    wires = []
    for i in range(22):
        z = -880.0 + i * 40.0
        wires.append(box(f"wire{i}", (-1800.0, 0.0, z - 4), (1800.0, 8.0, z + 4), m["copper"], root))
    label("interposer wiring", (-660.0, 10.0, -650.0), root, beat(0))
    label("on a package substrate", (1700.0, -220.0, 0.0), root, beat(1))
    label("packaging capacity limits output", (0.0, 640.0, 0.0), root, beat(2))
    camera(root, [
        ((-600.0, 0.0, -700.0), 2200.0, 0.0, 1.4),
        ((1400.0, 100.0, 0.0), 3800.0, 0.15, 0.08),
        ((0.0, 200.0, 0.0), 5200.0, 0.30, 0.40),
    ])
    finish("sec7", page="hbm")


# ---- 8. makers ---------------------------------------------------------------------------------

MAKERS = [(-1200.0, "Micron (MU)"), (0.0, "SK hynix (000660.KS)"), (1200.0, "Samsung (005930.KS)")]


def sec8():
    m, root = begin(8, 3)
    box("plinth", (-1900.0, -80.0, -400.0), (1900.0, 0.0, 200.0), m["plinth"], root)
    for i, (x, name) in enumerate(MAKERS):
        box(f"wafer{i}", (x - 300, 0.0, -20.0), (x + 300, 560.0, 0.0), m["grey"], root)
        spot = gbox(f"spot{i}", (x - 320, -6.0, 0.0), (x + 320, 580.0, 12.0), m["gold_glow"], root)
        show(spot, beat(i))
        label(name, (x, 600.0, 30.0), root, beat(i))
    camera(root, [((x, 300.0, 0.0), 2600.0, 0.0, 0.10) for x, _ in MAKERS])
    finish("sec8", page="hbm")


# ---- 9. risks ----------------------------------------------------------------------------------


def sec9():
    m, root = begin(9, 3)
    queue = empty("queue", root)  # only in beat 0, so it does not stand among the bars and the stack
    box("cowos_line", (-1500.0, -60.0, -300.0), (-100.0, 0.0, 300.0), m["interposer"], queue)
    for i in range(5):
        box(f"queued_gpu{i}", (-1400.0 + 260 * i, 0.0, -120.0), (-1200.0 + 260 * i, 220.0, 120.0), m["gpu"], queue)
    show(queue, beat(0))
    for i in range(3):
        bar_x = -200.0 + 300.0 * i
        h = (600.0, 540.0, 480.0)[i]
        g = empty(f"yield_show{i}", root)
        b = pivot(f"yield_grow{i}", (bar_x, 0.0, 0.0), g)
        box(f"yield_bar{i}", (-110, 0.0, -110), (110, h, 110), m["dram"], b)
        scale_keys(b, [(0, (1, 1, OFF)), (F(1, 0.05), (1, 1, OFF)), (F(1, 0.4), (1, 1, 1)), (END, (1, 1, 1))], until=F(1, 0.05))
        show(g, beat(1))
    stack = K.stack(root, m, 0.0, 16, "risk", glow=True)
    show(stack.g, beat(2))
    for k in range(16):
        if k <= 5:
            show(stack.glows[k], beat(2))
        else:
            show(stack.glows[k], [])
    label("GPU dies queue at packaging", (-800.0, 260.0, 0.0), root, beat(0))
    label("CoWoS: one supplier does most", (-250.0, -30.0, 300.0), root, beat(0))
    label("yield falls as stacks grow", (100.0, 600.0, 0.0), root, beat(1))
    label("heat from the lower dies", (250.0, 200.0, 0.0), root, beat(2))
    camera(root, [
        ((-600.0, 200.0, 0.0), 3200.0, 0.10, 0.10),
        ((100.0, 320.0, 0.0), 2400.0, 0.10, 0.08),
        ((0.0, 520.0, 0.0), 2700.0, 0.10, 0.08),
    ])
    finish("sec9", page="hbm")


# ---- 10. sources -------------------------------------------------------------------------------

# Two staggered rows, 2200 mm apart along x, so each source label has its own space.
CARDS = [
    (-2900.0, -900.0, "JEDEC JESD238 (HBM3)", 0, 0.15),
    (-900.0, -900.0, "JEDEC JESD270-4 (HBM4)", 0, 0.45),
    (1100.0, -900.0, "SemiEngineering: microbumps", 0, 0.75),
    (3000.0, -900.0, "Tom's Hardware: hybrid bonding", 1, 0.15),
    (-2200.0, 900.0, "Tom's Hardware: CoWoS", 1, 0.45),
    (0.0, 900.0, "TrendForce: CoWoS capacity", 2, 0.15),
    (2200.0, 900.0, "PC Watch: HBM3 channels", 2, 0.45),
]


def sec10():
    m, root = begin(10, 3)
    g = empty("sources", root)
    box("plinth", (-4300.0, -80.0, -1800.0), (4300.0, 0.0, 1800.0), m["plinth"], g)
    for n, (x, z, text, b, u) in enumerate(CARDS):
        box(f"card{n}", (x - 700, 0.0, z - 500), (x + 700, 30.0, z + 500), m["paper"], g)
        lit = empty(f"lit{n}", g)
        box(f"lit{n}_m", (x - 600, 30.0, z - 380), (x + 300, 36.0, z - 340), m["gold_glow"], lit)
        show(lit, [(F(b, u), END)])
        label(text, (x - 700, 40.0, z + 500), g, [(F(b, u), END)])
    camera(root, [
        ((250.0, 0.0, 0.0), 19500.0, 0.05, 0.85),
        ((250.0, 0.0, 0.0), 19500.0, 0.03, 0.85),
        ((250.0, 0.0, 0.0), 19500.0, -0.02, 0.85),
    ])
    finish("sec10", page="hbm")


SECS = {n: globals()[f"sec{n}"] for n in range(1, 11)}

if __name__ == "__main__":
    which = [int(a) for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(SECS)
    for n in which:
        SECS[n]()
