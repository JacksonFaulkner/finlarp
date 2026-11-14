"""The five BANDWIDTH zoom-ins, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md), built from the parts in bandwidth_kit.py. Four beats each.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/bandwidth_zooms.py [-- pin subch gddr gaps wall]

For each zoom it writes blender/bandwidth_<name>.blend and assets/bandwidth_<name>.glb.

  a pin    one pin: a transfer per clock, then one on each edge (DDR), then PAM4's four levels
  b subch  DDR4's chips in lockstep, DDR5's two subchannels, two requests at once, 38.4 GB/s
  c gddr   GDDR6 chips on a board with 32 pins each, HBM3's 1024 pins on an interposer, and both
  d gaps   the bus as slots: full, turned around for writes, refresh, row misses
  e wall   peak compute against DRAM and interconnect bandwidth, growing over two-year steps

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, beat, box, empty, label, show, tube  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import bandwidth_kit as K  # noqa: E402
from bandwidth_kit import END  # noqa: E402

BEATS = 4


def begin(name):
    m, root = start(name, BEATS, page="bandwidth")
    K.mats(m)
    return m, root


def dimm_half(parent, name, yc, m, x0, side):
    """Half a DIMM: its own board strip and four chips, in the colour of its subchannel."""
    g = empty(name, parent)
    lo = yc - K.DIMM_H / 2 if side == 0 else yc
    hi = yc if side == 0 else yc + K.DIMM_H / 2
    box(f"{name}_pcb", (x0, lo, -40), (x0 + K.DIMM_LEN, hi, 0), m["pcb"], g)
    pitch = (K.DIMM_LEN - 140) / 8
    for k in range(4):
        cx = x0 + 70 + pitch * (k + 4 * side)
        box(f"{name}_chip{k}", (cx, lo + 25, 0), (cx + pitch - 40, hi - 25, 50), m["cyan"] if side == 0 else m["write"], g)
    return g


# ---- a: one pin -------------------------------------------------------------------------


def pin():
    m, root = begin("pin")
    # the clock: twelve half-cycles of a square wave above the pin
    xs = [-1400.0 + 230.0 * i for i in range(12)]
    clk = empty("clock", root)
    for i in range(11):
        lvl = 820.0 if i % 2 == 0 else 640.0
        box(f"clk{i}", (xs[i], lvl - 14, -30), (xs[i + 1], lvl + 14, 0), m["gold_glow"], clk)
        nxt = 820.0 if (i + 1) % 2 == 0 else 640.0
        box(f"clkedge{i}", (xs[i + 1] - 14, min(lvl, nxt) - 14, -30), (xs[i + 1] + 14, max(lvl, nxt) + 14, 0), m["gold_glow"], clk)
    label("clock: 1600 MHz", (xs[0], 900.0, -30), root, beat(0) + beat(1) + beat(2) + beat(3))

    # the pin itself
    tube("pin_wire", (-1500.0, 0.0, -40), (1500.0, 0.0, -40), 7.0, m["copper"], root, verts=8)

    # beat 0: one transfer per clock, so one dot per clock on the wire
    K.dots(root, "one_per_clock", (-1450.0, 0.0, -40), (1450.0, 0.0, -40), 6, m["read"], 0, 0.02, 0.6, 70, size=16)
    label("one transfer per clock", (-300.0, 260.0, -40), root, beat(0))

    # beat 1: DDR, a transfer on each edge; the extra blocks sit under the wire
    edges = empty("ddr_blocks", root)
    for i in range(12):
        x = xs[i] + 115.0
        box(f"ddrb{i}", (x - 45, -260, -40), (x + 45, -170, 0), m["read"], edges)
    show(edges, [(F(1, 0), F(3, 0))])
    K.dots(root, "ddr_dots", (-1450.0, 0.0, -40), (1450.0, 0.0, -40), 12, m["read"], 1, 0.0, 0.9, 40, size=16)
    label("DDR: a transfer on each edge", (-300.0, 260.0, -40), root, beat(1))

    # beat 2: the DDR4-3200 rate
    K.dots(root, "ddr4_dots", (-1450.0, 0.0, -40), (1450.0, 0.0, -40), 12, m["read"], 2, 0.0, 0.9, 40, size=16)
    label("DDR4-3200: 3200 MT/s", (-300.0, 260.0, -40), root, beat(2))

    # beat 3: PAM4, four levels, each block takes one of four heights
    levels = [-520.0, -390.0, -260.0, -130.0]
    pam = empty("pam4", root)
    for j, y in enumerate(levels):
        tube(f"level{j}", (-1500.0, y, -40), (1500.0, y, -40), 2.5, m["grey"], pam, verts=6)
    for i in range(10):
        y = levels[(i * 3) % 4]
        box(f"pam{i}", (xs[i] + 40, y - 30, -30), (xs[i] + 180, y + 30, 0), m["gap"] if i % 2 else m["read"], pam)
    show(pam, [(F(3, 0), END)])
    label("PAM4: four levels, two bits", (-300.0, 260.0, -40), root, beat(3))

    camera(root, [
        ((0.0, 350.0, 0.0), 4600.0, 0.08, 0.06),
        ((0.0, 350.0, 0.0), 4600.0, 0.06, 0.06),
        ((0.0, 350.0, 0.0), 4600.0, 0.04, 0.06),
        ((0.0, 250.0, 0.0), 4200.0, 0.02, 0.06),
    ])
    finish("pin", page="bandwidth")


# ---- b: DDR5 subchannels ---------------------------------------------------------------


def subch():
    m, root = begin("subch")
    yc = 0.0
    x0 = -650.0
    # beats 0: the whole DIMM, all eight chips answering together over sixty-four lanes
    whole = K.dimm(root, "dimm", yc, m, x0=x0)
    show(whole, [(F(0, 0), F(1, 0))])
    lanes = K.lanes(root, "lanes64", x0 + K.DIMM_LEN, x0 + K.DIMM_LEN + 500.0, yc, m, n=8)
    show(lanes, [(F(0, 0), F(1, 0))])
    K.dots(root, "chips_together", (x0 + 20.0, yc, 60.0), (x0 + K.DIMM_LEN + 480.0, yc, -40.0), 6, m["read"], 0, 0.05, 0.6, 80, size=12)
    label("8 chips answer together", (x0 + 40.0, 260.0, 60.0), root, beat(0))

    # beats 1 onward: the DIMM splits into two 32-bit subchannels, each with its own lanes
    for side in (0, 1):
        half = dimm_half(root, f"half{side}", yc, m, x0, side)
        show(half, [(F(1, 0), END)])
        ly = yc + (60.0 if side == 0 else -60.0)
        sub = K.lanes(root, f"sub{side}_lanes", x0 + K.DIMM_LEN, x0 + K.DIMM_LEN + 500.0, ly, m, n=4)
        show(sub, [(F(1, 0), END)])
    label("DDR5: two 32-bit subchannels", (x0 + 40.0, 260.0, 60.0), root, beat(1))

    # beat 2: two requests at once, one per subchannel
    for side, mat_name in ((0, "cyan"), (1, "write")):
        ly = yc + (60.0 if side == 0 else -60.0)
        for i in range(4):
            K.dots(root, f"req{side}_{i}", (x0 + K.DIMM_LEN + 20.0, ly + (i - 1.5) * 25.0, -40.0), (x0 + K.DIMM_LEN + 480.0, ly + (i - 1.5) * 25.0, -40.0), 2, m["read"] if side == 0 else m["write"], 2, 0.05 * i, 0.5 + 0.05 * i, 80, size=10)
    label("two requests at once", (x0 + 40.0, 260.0, 60.0), root, beat(2))

    # beat 3: the rate
    label("DDR5-4800 DIMM: 38.4 GB/s", (x0 + 40.0, 260.0, 60.0), root, beat(3))
    for side in (0, 1):
        ly = yc + (60.0 if side == 0 else -60.0)
        for i in range(2):
            K.dots(root, f"rate{side}_{i}", (x0 + K.DIMM_LEN + 20.0, ly, -40.0), (x0 + K.DIMM_LEN + 480.0, ly, -40.0), 2, m["read"], 3, 0.1 * i, 0.5 + 0.1 * i, 80, size=10)

    camera(root, [
        ((0.0, 0.0, 0.0), 3800.0, 0.10, 0.08),
        ((0.0, 0.0, 0.0), 3800.0, 0.08, 0.08),
        ((0.0, 0.0, 0.0), 3800.0, 0.06, 0.08),
        ((0.0, 0.0, 0.0), 3800.0, 0.04, 0.08),
    ])
    finish("subch", page="bandwidth")


# ---- c: GDDR next to HBM ------------------------------------------------------------------


def gddr():
    m, root = begin("gddr")
    # a GPU on the board, with four GDDR6 chips around it
    box("board", (-1300.0, -300.0, -160.0), (1300.0, -230.0, -80.0), m["pcb"], root)
    gpu = empty("gpu", root)
    box("gpu_die", (-300.0, -230.0, -900.0), (300.0, 150.0, -200.0), m["cpu"], gpu)
    chips = empty("gddr_chips", root)
    spots = [(-1000.0, 0.0), (800.0, 0.0)]
    for i, (x, y) in enumerate(spots):
        box(f"gddr{i}", (x, y - 110.0, -60.0), (x + 220.0, y + 110.0, 40.0), m["dram"], chips)
        K.lanes(chips, f"gddr{i}_lanes", x + 220.0 if x < 0 else 300.0, -300.0 if x < 0 else x, y, m, n=8, z=-60.0)
    show(chips, [(0, F(1, 0)), (F(3, 0), END)])
    label("GDDR6: 32 pins, 64 GB/s", (-1000.0, 560.0, 40.0), root, beat(0))
    for i in range(3):
        K.dots(root, f"gddr_dots{i}", (-780.0, 0.0 + 30.0 * i, -60.0), (-300.0, 30.0 * i, -60.0), 3, m["read"], 0, 0.1, 0.7, 60, size=10)
    for i in range(3):
        K.dots(root, f"gddr_dots_r{i}", (780.0, 30.0 * i, -60.0), (320.0, 30.0 * i, -60.0), 3, m["read"], 3, 0.1, 0.7, 60, size=10)

    # HBM3 beside the GPU on an interposer, from beat 1
    hb = K.hbm(root, m, 480.0, 1080.0, -230.0, -700.0, -360.0)
    show(hb, [(F(1, 0), END)])
    label("HBM3: 1024 pins, 819 GB/s", (480.0, 600.0, -360.0), root, beat(1) + beat(2) + beat(3))

    # beat 2: the interposer's short, dense wires (a comb of lanes)
    comb = K.hbm_comb(root, "comb", 300.0, 480.0, -180.0, -500.0, 24, 22.0, m, r=3.0)
    show(comb, [(F(2, 0), END)])
    for i in range(6):
        K.dots(root, f"comb_dots{i}", (310.0, -180.0 + 22.0 * (i * 4), -500.0), (470.0, -180.0 + 22.0 * (i * 4), -500.0), 2, m["read"], 2, 0.05 * i, 0.6, 40, size=7)
    label("short, dense wires on the interposer", (300.0, 600.0, -360.0), root, beat(2))
    label("both at once: GDDR long board wires, HBM short ones", (-1000.0, 560.0, 40.0), root, beat(3))

    camera(root, [
        ((0.0, 200.0, -300.0), 5000.0, 0.12, 0.12),
        ((450.0, 200.0, -300.0), 3800.0, 0.18, 0.12),
        ((450.0, 200.0, -300.0), 3600.0, 0.10, 0.12),
        ((0.0, 200.0, -300.0), 5200.0, 0.06, 0.12),
    ])
    finish("gddr", page="bandwidth")


# ---- d: where peak goes -------------------------------------------------------------------

SLOTS = 40
SLOT_X0, SLOT_PITCH = -1500.0, 75.0


def slot_pattern(beat_index):
    """The kind of each bus slot in a beat: 'd' data, 'w' write, 'x' empty or turnaround gap."""
    if beat_index == 0:
        return "d" * SLOTS
    if beat_index == 1:  # reads, a turnaround, writes, a turnaround, reads
        return "d" * 14 + "xx" + "w" * 10 + "xx" + "d" * 14
    if beat_index == 2:  # refresh: a run of slots with no data
        return "d" * 16 + "e" * 10 + "d" * 14
    return "dddddxxdddddddxdddddddxxdddddddxxdddd"[:SLOTS]  # row misses and bank waits


def gaps():
    m, root = begin("gaps")
    # the peak lane, every slot full
    peak = empty("peak_lane", root)
    box("peak_bar", (SLOT_X0 - 40.0, 230.0, -40.0), (SLOT_X0 + SLOT_PITCH * SLOTS, 270.0, 0.0), m["cyan"], peak)
    label("peak: every slot full", (SLOT_X0, 330.0, 0.0), root, beat(0))
    kinds = {"d": ("read", m["read"]), "w": ("write", m["write"]), "x": ("gap", m["gap"]), "e": ("empty", m["grey"])}
    for b in range(BEATS):
        pat = slot_pattern(b)
        for code in "dwxe":
            grp = empty(f"b{b}_{code}", root)
            for i, c in enumerate(pat):
                if c != code:
                    continue
                x = SLOT_X0 + SLOT_PITCH * i
                box(f"b{b}_{code}{i}", (x, -60.0, -40.0), (x + 55.0, 60.0, 0.0), kinds[code][1], grp)
            show(grp, [(F(b, 0), F(b + 1, 0))])
    label("turnaround: bus idle", (SLOT_X0 + 1000.0, 330.0, 0.0), root, beat(1))
    label("refresh: no data", (SLOT_X0 + 900.0, 330.0, 0.0), root, beat(2))
    label("row misses and bank waits", (SLOT_X0 + 500.0, 330.0, 0.0), root, beat(3))
    label("effective = the slots with data", (SLOT_X0, -330.0, 0.0), root, beat(3))

    camera(root, [((0.0, 120.0, 0.0), 5600.0, 0.02, 0.06)] * BEATS)
    finish("gaps", page="bandwidth")


# ---- e: the memory wall -------------------------------------------------------------------

STEPS = 11  # two-year steps, twenty years


def wall():
    m, root = begin("wall")
    x_of = lambda k: -1300.0 + 260.0 * k  # noqa: E731
    unit = 100.0  # bar height for one step of the log scale
    log3 = math.log(3.0)
    for k in range(STEPS):
        # compute: 3.0x every two years; heights on a log scale, so each step adds the same
        hc = unit * (k + 1)
        t0 = 0.02 + 0.07 * k
        K.bar(root, f"compute{k}", x_of(k) - 50.0, -100.0, 70.0, 120.0, hc, m["pink_bar"],
              [(0, OFF), (F(0, t0), OFF), (F(0, t0 + 0.06), 1.0)])
        # DRAM bandwidth 1.6x and interconnect 1.4x, same log scale
        hd = unit * (k + 1) * math.log(1.6) / log3
        hi = unit * (k + 1) * math.log(1.4) / log3
        K.bar(root, f"dram{k}", x_of(k) + 30.0, -100.0, 60.0, 120.0, hd, m["cyan"],
              [(0, OFF), (F(1, t0), OFF), (F(1, t0 + 0.06), 1.0)])
        K.bar(root, f"ic{k}", x_of(k) + 110.0, -100.0, 60.0, 120.0, hi, m["purple"],
              [(0, OFF), (F(1, t0 + 0.02), OFF), (F(1, t0 + 0.08), 1.0)])
    label("compute: 3.0x every 2 years", (x_of(0) - 50.0, 1250.0, -120.0), root, beat(0))
    label("DRAM bandwidth 1.6x, interconnect 1.4x", (x_of(0), 1250.0, -120.0), root, beat(1))
    gap_top = unit * STEPS
    tube("bracket_top", (x_of(STEPS - 1) - 80.0, gap_top + 40.0, -120.0), (x_of(STEPS - 1) + 170.0, gap_top + 40.0, -120.0), 6.0, m["gold"], root, verts=8)
    label("the gap is the wall", (x_of(STEPS - 1) - 400.0, gap_top + 120.0, -120.0), root, beat(2))
    cpu = empty("cpu_block", root)
    box("cpu_big", (-1500.0, -260.0, -700.0), (-1100.0, -20.0, -300.0), m["cpu"], cpu)
    show(cpu, [(F(3, 0), END)])
    label("large models wait on memory", (-1500.0, 100.0, -300.0), root, beat(3))

    camera(root, [
        ((0.0, 500.0, 0.0), 8200.0, 0.08, 0.08),
        ((0.0, 500.0, 0.0), 8200.0, 0.06, 0.08),
        ((0.0, 500.0, 0.0), 8200.0, 0.04, 0.08),
        ((-400.0, 400.0, 0.0), 7600.0, 0.02, 0.08),
    ])
    finish("wall", page="bandwidth")


ALL = {"pin": pin, "subch": subch, "gddr": gddr, "gaps": gaps, "wall": wall}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ALL)
    for name in which:
        ALL[name]()
