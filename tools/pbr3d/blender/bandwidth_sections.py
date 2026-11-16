"""The ten BANDWIDTH write-up sections, each a 3D picture authored in Blender and exported for pbr3d
in the SAND template (docs/diagram-pages.md). Parts come from bandwidth_kit.py; the bus slots and
the wall chart reuse bandwidth_zooms.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/bandwidth_sections.py [-- 3 5]

For each section it writes blender/bandwidth_sec<N>.blend and assets/bandwidth_sec<N>.glb.

  1 what happens   one pin, a 64-pin channel, four channels, real traffic under the peak (four beats)
  2 parts          data rate, data pins, DIMM, memory controller, HBM stack (five beats)
  3 computing      the steps 3200 MT/s, x 64, / 8, 25.6 GB/s, x 4 = 102.4 GB/s (five beats)
  4 DDR, GDDR, HBM DIMM 38.4, GDDR6 64, HBM3 819 GB/s, board wires against an interposer (four beats)
  5 effective      the bus as slots: full, turned around, refresh and row misses (three beats)
  6 numbers        the table: rate per pin, data pins, GB/s per device (three beats)
  7 wall           compute against DRAM and interconnect, and the gap (three beats)
  8 makers         Micron, SK hynix, Samsung (three beats)
  9 risks          the wall, pins, interposer packaging, access patterns (four beats)
 10 sources        six source cards lighting up in groups (three beats)

One beat is SEC (8) seconds at 24 fps.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, beat, box, empty, label, show, tube  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import bandwidth_kit as K  # noqa: E402
from bandwidth_kit import DIMM_X0, END, PORT_X  # noqa: E402
import bandwidth_zooms as Z  # noqa: E402

CH_Y = [1050.0, 780.0, 510.0, 240.0]


def begin(n, beats):
    m, root = start(f"sec{n}", beats, page="bandwidth")
    K.mats(m)
    return m, root


def cam(root, poses):
    camera(root, poses)


def pin_and_dots(root, m, beat_i, y=0.0, n=3):
    K.dots(root, f"pin_dots{beat_i}", (PORT_X + 40, y, -40), (DIMM_X0 - 20, y, -40), n, m["read"], beat_i, 0.05, 0.7, 80, size=10)


# ---- 1. what happens --------------------------------------------------------------------


def sec1():
    m, root = begin(1, 4)
    K.processor(root, m)
    # beat 0: one pin
    pin = empty("pin", root)
    tube("pin_wire", (PORT_X, CH_Y[0], -40), (DIMM_X0, CH_Y[0], -40), 14.0, m["copper"], pin, verts=10)
    show(pin, [(0, F(1, 0))])
    K.dots(root, "pin_dots", (PORT_X + 40, CH_Y[0], -40), (DIMM_X0 - 20, CH_Y[0], -40), 3, m["read"], 0, 0.05, 0.7, 80, size=24)
    label("one pin: 3200 MT/s", (-300.0, CH_Y[0] + 110.0, -40), root, beat(0))
    # beat 1: a 64-pin channel
    show(K.lanes(root, "ch0_lanes", PORT_X, DIMM_X0, CH_Y[0], m, n=8), [(F(1, 0), END)])
    for i, y in enumerate(K.lane_ys(CH_Y[0])):
        K.dots(root, f"ch0_d{i}", (PORT_X + 40, y, -40), (DIMM_X0 - 20, y, -40), 2, m["read"], 1, 0.05, 0.6, 90, size=8)
    show(K.dimm(root, "dimm0", CH_Y[0], m), [(F(1, 0), END)])
    label("64 data pins: 25.6 GB/s", (-300.0, CH_Y[0] + 190.0, -40), root, beat(1))
    # beat 2: four channels
    for c in range(1, 4):
        show(K.lanes(root, f"ch{c}_lanes", PORT_X, DIMM_X0, CH_Y[c], m, n=8), [(F(2, 0), END)])
        show(K.dimm(root, f"dimm{c}", CH_Y[c], m), [(F(2, 0), END)])
    for c in range(4):
        for i, y in enumerate(K.lane_ys(CH_Y[c])[::3]):
            K.dots(root, f"c{c}_b2_{i}", (PORT_X + 40, y, -40), (DIMM_X0 - 20, y, -40), 2, m["read"], 2, 0.05, 0.6, 90, size=8)
    label("four channels: 102.4 GB/s peak", (-300.0, 1420.0, -40), root, beat(2) + beat(3))
    # beat 3: real traffic leaves holes
    gaps = empty("gaps", root)
    for c in range(4):
        for x in (-500.0, 100.0, 700.0):
            box(f"gap{c}_{int(x)}", (x - 60, CH_Y[c] - 40, -20), (x + 60, CH_Y[c] + 40, 30), m["gap"], gaps)
    show(gaps, [(F(3, 0), END)])
    label("pink: a slot with no data", (-300.0, 1420.0, -40), root, beat(3))
    cam(root, [
        ((-650.0, 1000.0, 0.0), 4400.0, 0.10, 0.08),
        ((0.0, 950.0, 0.0), 6200.0, 0.10, 0.10),
        ((0.0, 700.0, 0.0), 6400.0, 0.10, 0.12),
        ((0.0, 700.0, 0.0), 6400.0, 0.10, 0.12),
    ])
    finish("sec1", page="bandwidth")


# ---- 2. the parts ------------------------------------------------------------------------


def sec2():
    m, root = begin(2, 5)
    K.processor(root, m)
    # beat 0: the data rate on one pin
    pin = empty("pin", root)
    tube("pin_wire", (PORT_X, 0.0, -40), (DIMM_X0, 0.0, -40), 14.0, m["copper"], pin, verts=10)
    show(pin, [(0, F(1, 0))])
    K.dots(root, "rate_dots", (PORT_X + 40, 0.0, -40), (DIMM_X0 - 20, 0.0, -40), 3, m["read"], 0, 0.05, 0.7, 80, size=24)
    label("data rate: transfers per pin per second", (-300.0, 180.0, -40), root, beat(0))
    # beat 1: data pins, a ribbon of lanes
    show(K.lanes(root, "lanes8", PORT_X, DIMM_X0, 0.0, m, n=8), [(F(1, 0), END)])
    for i, y in enumerate(K.lane_ys(0.0)):
        K.dots(root, f"pins_d{i}", (PORT_X + 40, y, -40), (DIMM_X0 - 20, y, -40), 2, m["read"], 1, 0.05, 0.6, 90, size=8)
    label("data pins: 64 per DDR channel", (-300.0, 180.0, -40), root, beat(1))
    # beat 2: the DIMM holding the chips
    show(K.dimm(root, "dimm", 0.0, m), [(F(2, 0), END)])
    label("DIMM: chips fill the channel width", (DIMM_X0 + 40.0, 260.0, 60.0), root, beat(2))
    # beat 3: the controller drives the channels (its ports lit)
    show(K.lanes(root, "ctrl_lanes", PORT_X, DIMM_X0, 0.0, m, n=8), [(F(3, 0), END)])
    show(K.dimm(root, "dimm_c", 0.0, m), [(F(3, 0), END)])
    label("memory controller: drives every channel", (PORT_X - 500.0, 1350.0, -300.0), root, beat(3))
    # beat 4: an HBM stack beside the processor
    show(K.hbm(root, m, -2900.0, -2300.0, -200.0, -700.0, -350.0), [(F(4, 0), END)])
    show(K.hbm_comb(root, "hbm_comb", -2300.0, PORT_X - 600.0, -150.0, -500.0, 12, 26.0, m), [(F(4, 0), END)])
    label("HBM stack: 1024 pins", (-2900.0, 420.0, -340.0), root, beat(4))
    cam(root, [
        ((-500.0, 300.0, 0.0), 4400.0, 0.08, 0.08),
        ((-500.0, 300.0, 0.0), 4400.0, 0.08, 0.08),
        ((0.0, 450.0, 0.0), 6400.0, 0.10, 0.10),
        ((0.0, 450.0, 0.0), 6400.0, 0.10, 0.10),
        ((-1600.0, 300.0, -300.0), 7000.0, 0.22, 0.10),
    ])
    finish("sec2", page="bandwidth")


# ---- 3. computing peak bandwidth ------------------------------------------------------------


def sec3():
    m, root = begin(3, 5)
    # beat 0: 3200 MT/s on one pin
    pin = empty("pin", root)
    tube("pin_wire", (-1200.0, 0.0, -40), (1200.0, 0.0, -40), K.LANE_R, m["copper"], pin, verts=8)
    show(pin, [(0, F(1, 0))])
    K.dots(root, "pin_dots", (-1180.0, 0.0, -40), (1180.0, 0.0, -40), 5, m["read"], 0, 0.02, 0.6, 80, size=10)
    label("1. 3200 MT/s on one pin", (-400.0, 220.0, -40), root, beat(0))
    # beat 1: x 64 pins
    show(K.lanes(root, "lanes64", -1200.0, 1200.0, 0.0, m, n=8), [(F(1, 0), END)])
    label("2. x 64 pins = 204,800 Mb/s", (-400.0, 220.0, -40), root, beat(1))
    # beat 2: / 8 bits per byte, eight bit cubes make one byte
    bits = empty("bits", root)
    for i in range(8):
        x = -400.0 + 70.0 * i
        box(f"bit{i}", (x, -120.0, -40.0), (x + 55.0, -65.0, 0.0), m["read"], bits)
    show(bits, [(F(2, 0), END)])
    label("3. / 8 bits per byte", (-400.0, 220.0, -40), root, beat(2))
    # beat 3: 25.6 GB/s per channel, on a bar to scale with 102.4 at full height
    bar_ch = empty("bar_channel_show", root)
    show(bar_ch, [(F(3, 0), END)])
    g = K.bar(bar_ch, "bar_channel", 0.0, 0.0, 300.0, 120.0, 1300.0, m["cyan"], [(0, OFF), (F(3, 0.1), OFF), (F(3, 0.5), 25.6 / 102.4)])
    label("4. = 25.6 GB/s per channel", (300.0, 380.0, -40), root, beat(3))
    # beat 4: four channels
    bar_tot = empty("bar_total_show", root)
    show(bar_tot, [(F(4, 0), END)])
    K.bar(bar_tot, "bar_total", 0.0, 0.0, 300.0, 120.0, 1300.0, m["cyan"], [(0, OFF), (F(4, 0.1), OFF), (F(4, 0.4), 1.0)])
    label("5. x 4 channels = 102.4 GB/s", (300.0, 1420.0, -40), root, beat(4))
    cam(root, [
        ((0.0, 300.0, 0.0), 4000.0, 0.02, 0.06),
        ((0.0, 300.0, 0.0), 4000.0, 0.02, 0.06),
        ((0.0, 300.0, 0.0), 4000.0, 0.02, 0.06),
        ((0.0, 600.0, 0.0), 4600.0, 0.02, 0.06),
        ((0.0, 700.0, 0.0), 4800.0, 0.02, 0.06),
    ])
    finish("sec3", page="bandwidth")


# ---- 4. DDR, GDDR and HBM ------------------------------------------------------------------


def sec4():
    m, root = begin(4, 4)
    # beat 0: DDR5-4800 DIMM as two 32-bit halves
    for side in (0, 1):
        show(Z.dimm_half(root, f"half{side}", 0.0, m, -650.0, side), [(0, F(1, 0))])
    label("DDR5-4800 DIMM: 38.4 GB/s", (-610.0, 110.0, 50.0), root, beat(0))
    # beat 1: GDDR6 chip, 32 pins to the GPU on the board
    gpu_scene = empty("gpu_scene", root)
    show(gpu_scene, [(F(1, 0), END)])
    board = box("board", (-1300.0, -300.0, -160.0), (1300.0, -230.0, -80.0), m["pcb"], gpu_scene)
    gpu = box("gpu_die", (-300.0, -230.0, -900.0), (300.0, 150.0, -200.0), m["cpu"], gpu_scene)
    chip = empty("gddr_group", root)
    box("gddr", (-1000.0, -60.0, -60.0), (-780.0, 120.0, 40.0), m["dram"], chip)
    lanes = K.lanes(root, "gddr_lanes", -780.0, -300.0, 30.0, m, n=8, z=-60.0)
    show(chip, [(F(1, 0), F(2, 0))])
    show(lanes, [(F(1, 0), F(2, 0))])
    K.dots(root, "gddr_dots", (-770.0, 30.0, -60.0), (-320.0, 30.0, -60.0), 4, m["read"], 1, 0.05, 0.7, 60, size=8)
    label("GDDR6: 32 pins x 16 Gb/s = 64 GB/s", (-1000.0, 420.0, 40.0), root, beat(1))
    # beat 2: HBM3 stack on an interposer
    show(K.hbm(root, m, 480.0, 1080.0, -230.0, -700.0, -360.0), [(F(2, 0), F(3, 0)), (F(3, 0), END)])
    label("HBM3: 1024 pins x 6.4 Gb/s = 819 GB/s", (780.0, 200.0, -380.0), root, beat(2))
    # beat 3: both, board wires against the interposer
    show(chip, [(F(3, 0), END)])
    show(lanes, [(F(3, 0), END)])
    label("board wires (GDDR) vs interposer (HBM)", (-1000.0, 420.0, 40.0), root, beat(3))
    cam(root, [
        ((0.0, 0.0, 0.0), 3300.0, 0.08, 0.08),
        ((-200.0, 200.0, -300.0), 5000.0, 0.12, 0.10),
        ((250.0, 200.0, -300.0), 5000.0, 0.14, 0.10),
        ((0.0, 200.0, -300.0), 6000.0, 0.10, 0.10),
    ])
    finish("sec4", page="bandwidth")


# ---- 5. effective vs peak --------------------------------------------------------------


def sec5():
    m, root = begin(5, 3)
    peak = empty("peak_lane", root)
    box("peak_bar", (Z.SLOT_X0 - 40.0, 230.0, -40.0), (Z.SLOT_X0 + Z.SLOT_PITCH * Z.SLOTS, 270.0, 0.0), m["cyan"], peak)
    label("peak: every slot full", (Z.SLOT_X0, 330.0, 0.0), root, beat(0))
    kinds = {"d": m["read"], "w": m["write"], "x": m["gap"], "e": m["grey"]}
    pats = [Z.slot_pattern(0), Z.slot_pattern(1), Z.slot_pattern(2)]
    for b, pat in enumerate(pats):
        for code in "dwxe":
            grp = empty(f"b{b}_{code}", root)
            for i, c in enumerate(pat):
                if c == code:
                    x = Z.SLOT_X0 + Z.SLOT_PITCH * i
                    box(f"b{b}_{code}{i}", (x, -60.0, -40.0), (x + 55.0, 60.0, 0.0), kinds[code], grp)
            show(grp, [(F(b, 0), F(b + 1, 0))])
    label("turnaround: bus idle", (Z.SLOT_X0 + 1000.0, 330.0, 0.0), root, beat(1))
    label("refresh and row misses: effective", (Z.SLOT_X0 + 400.0, 330.0, 0.0), root, beat(2))
    cam(root, [((0.0, 120.0, 0.0), 5600.0, 0.02, 0.06)] * 3)
    finish("sec5", page="bandwidth")


# ---- 6. by the numbers -----------------------------------------------------------------


def sec6():
    m, root = begin(6, 3)
    names = ["DDR4-3200", "DDR5-4800", "GDDR6", "HBM3"]
    xs = [-1000.0, -330.0, 330.0, 1000.0]
    sets = [
        (3.2, 4.8, 16.0, 6.4),  # Gb/s per pin
        (64.0, 64.0, 32.0, 1024.0),  # data pins
        (25.6, 38.4, 64.0, 819.0),  # GB/s per device
    ]
    labels = ["Gb/s per pin", "data pins", "GB/s per device"]
    scale = [1300.0 / 16.0, 1300.0 / 1024.0, 1300.0 / 819.0]
    for b in range(3):
        grp = empty(f"b{b}_bars", root)
        show(grp, beat(b))
        for k, x in enumerate(xs):
            h = sets[b][k] * scale[b]
            col = [m["cyan"], m["purple"], m["pink_bar"], m["gold_glow"]][k]
            K.bar(grp, f"b{b}_bar{k}", x, 0.0, 200.0, 120.0, h, col,
                  [(0, OFF), (F(b, 0.05 + 0.05 * k), OFF), (F(b, 0.2 + 0.05 * k), 1.0)])
        label(labels[b], (-1000.0, 1450.0, -40.0), root, beat(b))
    for k, x in enumerate(xs):
        label(f"{names[k]}", (x - 40.0, -120.0, 60.0), root, beat(0) + beat(1) + beat(2))
    cam(root, [((0.0, 600.0, 0.0), 6200.0, 0.10, 0.08)] * 3)
    finish("sec6", page="bandwidth")


# ---- 7. memory wall -----------------------------------------------------------------------


def sec7():
    m, root = begin(7, 3)
    unit = 100.0
    log3 = math.log(3.0)
    x_of = lambda k: -1300.0 + 260.0 * k  # noqa: E731
    for k in range(11):
        t0 = 0.02 + 0.07 * k
        K.bar(root, f"compute{k}", x_of(k) - 50.0, -100.0, 70.0, 120.0, unit * (k + 1), m["pink_bar"],
              [(0, OFF), (F(0, t0), OFF), (F(0, t0 + 0.06), 1.0)])
        K.bar(root, f"dram{k}", x_of(k) + 30.0, -100.0, 60.0, 120.0, unit * (k + 1) * math.log(1.6) / log3, m["cyan"],
              [(0, OFF), (F(1, t0), OFF), (F(1, t0 + 0.06), 1.0)])
        K.bar(root, f"ic{k}", x_of(k) + 110.0, -100.0, 60.0, 120.0, unit * (k + 1) * math.log(1.4) / log3, m["purple"],
              [(0, OFF), (F(1, t0 + 0.02), OFF), (F(1, t0 + 0.08), 1.0)])
    label("compute: 3.0x every 2 years", (x_of(0) - 50.0, 1250.0, -120.0), root, beat(0))
    label("DRAM bandwidth 1.6x, interconnect 1.4x", (x_of(0), 1250.0, -120.0), root, beat(1))
    tube("bracket_top", (x_of(10) - 80.0, unit * 11 + 40.0, -120.0), (x_of(10) + 170.0, unit * 11 + 40.0, -120.0), 6.0, m["gold"], root, verts=8)
    label("the gap is the wall", (x_of(10) - 400.0, unit * 11 + 120.0, -120.0), root, beat(2))
    cam(root, [((80.0, 560.0, 0.0), 5600.0, 0.08, 0.08)] * 3)
    finish("sec7", page="bandwidth")


# ---- 8. who makes it ----------------------------------------------------------------------


def sec8():
    m, root = begin(8, 3)
    names = [("Micron (MU)", -1200.0), ("SK hynix (000660.KS)", 0.0), ("Samsung (005930.KS)", 1200.0)]
    for i, (text, x) in enumerate(names):
        g = empty(f"card{i}", root)
        box(f"card{i}_m", (x - 500.0, -300.0, -40.0), (x + 500.0, 300.0, 0.0), m["paper"], g)
        lit = empty(f"lit{i}", g)
        box(f"lit{i}_m", (x - 450.0, 300.0, -40.0), (x + 450.0, 340.0, 0.0), m["gold_glow"], lit)
        show(lit, [(F(i, 0.1), END)])
        label(text, (x - 500.0, 360.0, 0.0), root, [(F(i, 0.1), END)])
    label("DRAM, GDDR and HBM makers", (-1200.0, -420.0, 0.0), root, beat(0) + beat(1) + beat(2))
    cam(root, [((0.0, 0.0, 0.0), 6200.0, 0.02, 0.05)] * 3)
    finish("sec8", page="bandwidth")


# ---- 9. chokepoints and risks ---------------------------------------------------------------


def sec9():
    m, root = begin(9, 4)
    # beat 0: a processor fed through a thin pipe
    cpu = empty("cpu_group", root)
    box("cpu0", (700.0, -200.0, -700.0), (1500.0, 500.0, -200.0), m["cpu"], cpu)
    mem = box("mem0", (-1500.0, -200.0, -700.0), (-700.0, 500.0, -200.0), m["dram"], cpu)
    pipe = tube("thin_pipe", (-700.0, 150.0, -450.0), (700.0, 150.0, -450.0), 14.0, m["copper"], cpu, verts=8)
    show(cpu, beat(0))  # the beat-0 picture only: it stood in front of the pin grid and the HBM
    K.dots(root, "pipe_dots", (-680.0, 150.0, -450.0), (680.0, 150.0, -450.0), 3, m["read"], 0, 0.05, 0.6, 80, size=12)
    label("memory wall: compute outgrows bandwidth", (-400.0, 700.0, -450.0), root, beat(0))
    # beat 1: pins cost package area and power
    grid = empty("pin_grid", root)
    for i in range(7):
        for j in range(7):
            box(f"pin{i}_{j}", (-900.0 + 260.0 * i, -60.0, -200.0 - 130.0 * j), (-900.0 + 260.0 * i + 80.0, 60.0, -120.0 - 130.0 * j), m["gold"], grid)
    show(grid, [(F(1, 0), F(2, 0))])
    label("pins cost area, routing and power", (-860.0, 60.0, -160.0), root, beat(1))
    # beat 2: HBM needs an interposer beside the processor
    show(K.hbm(root, m, -1200.0, -500.0, -200.0, -700.0, -350.0), beat(2))
    show(K.processor(root, m), beat(2))
    label("HBM width needs interposer packaging", (-850.0, 230.0, -380.0), root, beat(2))
    # beat 3: effective bandwidth depends on the access pattern
    cad = empty("access", root)
    for i, c in enumerate(Z.slot_pattern(3)):
        x = Z.SLOT_X0 + Z.SLOT_PITCH * i
        box(f"acc{i}", (x, -60.0, -40.0), (x + 55.0, 60.0, 0.0), m["read"] if c == "d" else m["gap"], cad)
    show(cad, [(F(3, 0), END)])
    label("effective depends on access patterns", (Z.SLOT_X0, 330.0, 0.0), root, beat(3))
    cam(root, [
        ((0.0, 300.0, -300.0), 5600.0, 0.10, 0.08),
        ((-120.0, 0.0, -560.0), 3600.0, 0.10, 0.85),
        ((-1100.0, 250.0, -400.0), 4000.0, 0.15, 0.10),
        ((0.0, 120.0, 0.0), 5600.0, 0.02, 0.06),
    ])
    finish("sec9", page="bandwidth")


# ---- 10. sources ------------------------------------------------------------------------------


def sec10():
    m, root = begin(10, 3)
    cards = {
        0: ("[1] JEDEC JESD238 HBM3", -1500.0, -800.0),
        1: ("[2] Micron GDDR6 flyer", -500.0, -800.0),
        2: ("[3] Micron GDDR6X PAM4 brief", 500.0, -800.0),
        3: ("[4] Micron DDR5 modules", 1500.0, -800.0),
        4: ("[5] Gholami et al., arXiv 2403.14123", -1000.0, 800.0),
        5: ("[6] arithmetic; BANK and HBM STACK nodes", 400.0, 800.0),
    }
    order = {0: [0, 1], 1: [2, 3], 2: [4, 5]}
    for n, (text, x, z) in cards.items():
        box(f"card{n}", (x - 450.0, 0.0, z - 300.0), (x + 450.0, 30.0, z + 300.0), m["paper"], root)
        b = [k for k, v in order.items() if n in v][0]
        u = 0.15 + 0.35 * order[b].index(n)
        lit = empty(f"litg{n}", root)
        box(f"lit{n}", (x - 400.0, 30.0, z - 260.0), (x + 400.0, 40.0, z - 220.0), m["gold_glow"], lit)
        show(lit, [(F(b, u), END)])
        label(text, (x - 450.0, 60.0, z + 300.0), root, [(F(b, u), END)])
    cam(root, [((0.0, 0.0, 0.0), 9500.0, 0.04, 0.85)] * 3)
    finish("sec10", page="bandwidth")


ALL = [sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9, sec10]

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [str(n) for n in range(1, 11)]
    for n in which:
        ALL[int(n) - 1]()
