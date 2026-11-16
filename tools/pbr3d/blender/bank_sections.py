"""The ten BANK write-up sections, each a 3D picture authored in Blender and exported for pbr3d in the
MELT template (docs/diagram-pages.md). One per `# ` heading of MEM_BANK.txt, in order; section 10
is the sources page. The die is in bank_kit.py, the zoom helpers in bank_zooms.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/bank_sections.py [-- 3 5]

For each section it writes blender/bank_sec<N>.blend and assets/bank_sec<N>.glb.

  1 what happens   one bank waits on the bus; two overlap; four take turns on the bus (three beats)
  2 parts          bank, bank group, command bus, data bus, controller (five beats)
  3 one access     ACT A, ACT B, READ A, READ B, PRECHARGE both (five beats)
  4 timing rules   tRRD, tCCD, tFAW on a time axis (three beats)
  5 conflicts      eight banks overlap; one bank with several rows; reordered (three beats)
  6 numbers        16 banks in 4 groups; 32 in 8 groups; 8 vs 16 transfers per burst (three beats)
  7 refresh        DDR4 all-bank; DDR5 same-bank; reads carry on (three beats)
  8 makers         three makers' chips, one lit per beat (three beats)
  9 risks          two cores on one bank; tFAW; denser chips (three beats)
 10 sources        eight source cards lit in three groups (three beats)

One beat is SEC (8) seconds at 24 fps.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, beat, box, empty, mat, show  # noqa: E402
from sand_zooms import camera, finish  # noqa: E402
import bank_kit as K  # noqa: E402
from bank_kit import CMD_Y, END, GROUPS, GROUPS_8, GROUP_H, IO_X  # noqa: E402
from bank_zooms import begin, tag, timed  # noqa: E402


def _chip_die(root, m, groups=GROUPS):
    return K.die(root, m, groups=groups)


def _cam(root, n, target, dist, yaw=0.0, pitch=0.10):
    camera(root, [(target, dist, yaw, pitch)] * n)


# ---- 1 what happens -----------------------------------------------------------------------


def sec1():
    m, root = begin("sec1", 3)
    d = _chip_die(root, m)
    A, B, C, D = d["banks"][0][0], d["banks"][1][0], d["banks"][2][0], d["banks"][3][0]
    # beat 0: one bank works alone; the data bus carries only its bursts
    K.activate(root, A, F(0, 0.05), F(0, 0.30), m)
    K.set_state(A, "row", [(F(0, 0.30), F(0, 0.85))])
    K.reads(root, A, F(0, 0.40), F(0, 0.90), 3, m)
    tag(root, "one bank: the bus waits", K.above(A), beat(0))
    # beat 1: two banks overlap; B opens while A still has its row open
    K.activate(root, A, F(1, 0.05), F(1, 0.20), m)
    K.activate(root, B, F(1, 0.20), F(1, 0.35), m)
    K.set_state(A, "row", [(F(1, 0.20), F(1, 0.95))])
    K.set_state(B, "row", [(F(1, 0.35), F(1, 0.95))])
    K.reads(root, A, F(1, 0.25), F(1, 0.60), 2, m)
    K.reads(root, B, F(1, 0.60), F(1, 0.95), 2, m)
    tag(root, "two banks overlap", K.above(B), beat(1))
    # beat 2: four banks take turns, so the data bus stays busy
    for k, bk in enumerate((A, B, C, D)):
        f0 = 0.05 + 0.12 * k
        K.activate(root, bk, F(2, f0), F(2, f0 + 0.10), m)
        K.set_state(bk, "row", [(F(2, f0 + 0.10), F(2, 0.95))])
        K.reads(root, bk, F(2, 0.30 + 0.14 * k), F(2, 0.30 + 0.14 * k + 0.12), 2, m)
    tag(root, "four banks in turn: bus busy", (-420.0, 90.0, 40.0), beat(2))
    K.commit(d)
    _cam(root, 3, (160.0, 100.0, 0.0), 6000.0, 0.14, 0.16)


# ---- 2 parts ------------------------------------------------------------------------------


def sec2():
    m, root = begin("sec2", 5)
    d = _chip_die(root, m)
    g = d["banks"]
    A = g[0][0]
    # controller at the left, in the processor
    box("controller", (-2150.0, -260.0, -100.0), (-1750.0, 260.0, 100.0), m["frame"], root)
    # beat 0: a bank has its own row buffer
    K.set_state(A, "row", [(F(0, 0.0), F(1, 0.0))])
    tag(root, "bank: array with its own row buffer", K.above(A), beat(0))
    # beat 1: a bank group is four banks sharing circuits
    for b in range(4):
        K.set_state(g[0][b], "row", [(F(1, 0.0), F(2, 0.0))])
    tag(root, "bank group: four banks", (-720.0, GROUP_H / 2 + 110.0, 40.0), beat(1))
    # beat 2: the command bus carries one command at a time
    for k in range(4):
        K.send(root, "cmdbus", [(-1300.0, CMD_Y, 40.0), (1300.0, CMD_Y, 40.0)], F(2, 0.05 + 0.2 * k), F(2, 0.25 + 0.2 * k), m["cmd_dot"])
    tag(root, "command bus: one command at a time", (0.0, CMD_Y + 70.0, 40.0), beat(2))
    # beat 3: the data bus is shared by every bank and runs out to the I/O pad
    for gi, bk in enumerate((g[0][0], g[1][0], g[2][0], g[3][0])):
        K.reads(root, bk, F(3, 0.10 + 0.05 * gi), F(3, 0.90), 2, m)
    tag(root, "data bus: shared by every bank", (420.0, 70.0, 40.0), beat(3))
    # beat 4: the controller picks the order of commands
    for k in range(5):
        K.send(root, "ctl", [(-1750.0, 0.0, 40.0), (-1400.0, CMD_Y, 40.0), (-900.0, CMD_Y, 40.0)], F(4, 0.05 + 0.12 * k), F(4, 0.30 + 0.12 * k), m["cmd_dot"])
    tag(root, "controller: picks the order", (-1950.0, 320.0, 100.0), beat(4))
    K.commit(d)
    camera(root, [
        ((-700.0, 330.0, 0.0), 2600.0, 0.08, 0.12),
        ((-700.0, 360.0, 0.0), 3000.0, 0.08, 0.12),
        ((0.0, 420.0, 0.0), 5600.0, 0.04, 0.14),
        ((160.0, 100.0, 0.0), 6000.0, 0.06, 0.14),
        ((-1300.0, 300.0, 0.0), 3900.0, 0.10, 0.12),
    ])


# ---- 3 one interleaved access ------------------------------------------------------------


def sec3():
    m, root = begin("sec3", 5)
    d = _chip_die(root, m)
    g = d["banks"]
    A, B = g[0][0], g[1][0]
    # 1. ACTIVATE bank A
    K.activate(root, A, F(0, 0.05), F(0, 0.35), m)
    K.set_state(A, "row", [(F(0, 0.40), F(4, 0.10))])
    tag(root, "1. ACT bank A", K.above(A), beat(0))
    # 2. ACTIVATE bank B, another group, while A opens
    K.activate(root, B, F(1, 0.05), F(1, 0.35), m)
    K.set_state(B, "row", [(F(1, 0.40), F(4, 0.10))])
    tag(root, "2. ACT bank B (another group)", K.above(B), beat(1))
    # 3. READ A: a burst leaves A's row buffer
    K.reads(root, A, F(2, 0.10), F(2, 0.90), 3, m)
    tag(root, "3. READ A", (-420.0, 90.0, 40.0), beat(2))
    # 4. READ B: follows straight after on the data bus
    K.reads(root, B, F(3, 0.10), F(3, 0.90), 3, m)
    tag(root, "4. READ B", (-420.0, 90.0, 40.0), beat(3))
    # 5. PRECHARGE both: the rows close
    K.activate(root, A, F(4, 0.00), F(4, 0.30), m)
    K.activate(root, B, F(4, 0.10), F(4, 0.40), m)
    K.set_state(A, "pink", [(F(4, 0.10), F(4, 0.80))])
    K.set_state(B, "pink", [(F(4, 0.10), F(4, 0.80))])
    tag(root, "5. PRECHARGE both", K.above(A), beat(4))
    K.commit(d)
    _cam(root, 5, (160.0, 100.0, 0.0), 5800.0, 0.12, 0.16)


# ---- 4 timing rules -----------------------------------------------------------------------

SLOT_MM = 30.0  # the timeline's scale: 30 mm per ns


def sec4():
    m, root = begin("sec4", 3)
    box("axis", (-1300.0, -300.0, -40.0), (1000.0, 300.0, 0.0), m["plinth"], root)
    # beat 0: tRRD. ACTs across groups 3.7 ns apart, within one group 5.3 ns
    x0 = -900.0
    acts = [x0, x0 + 3.7 * SLOT_MM, x0 + (3.7 + 5.3) * SLOT_MM]
    for i, x in enumerate(acts):
        timed(root, f"act{i}", (x, -40.0, 0.0), (x + 70.0, 200.0, 60.0), m["act"], beat(0))
    tag(root, "tRRD_S about 3.7 ns (across groups)", (acts[0] + 60.0, 300.0, 60.0), beat(0))
    tag(root, "tRRD_L about 5.3 ns (within one)", (acts[1] + 90.0, -260.0, 60.0), beat(0))
    # beat 1: tCCD. READs across groups back to back; within one group a gap
    for k in range(3):
        x = -900.0 + 200.0 * k
        timed(root, f"rd_x{k}", (x, 80.0, 0.0), (x + 180.0, 220.0, 60.0), m["rd2"], beat(1))
    for k in range(2):
        x = -900.0 + 420.0 * k
        timed(root, f"rd_g{k}", (x, -220.0, 0.0), (x + 180.0, -80.0, 60.0), m["rd"], beat(1))
    tag(root, "tCCD_S 2.5 ns: one burst", (-900.0, 300.0, 60.0), beat(1))
    tag(root, "tCCD_L about 5.36 ns: same group", (-900.0, -420.0, 60.0), beat(1))
    # beat 2: tFAW. Four ACTs in one window; a fifth must wait
    for k in range(4):
        x = -700.0 + 110.0 * k
        timed(root, f"faw_act{k}", (x, -40.0, 0.0), (x + 70.0, 200.0, 60.0), m["act"], beat(2))
    timed(root, "faw_win", (-700.0, -340.0, 0.0), (-700.0 + 630.0, -300.0, 40.0), m["window"], beat(2))
    timed(root, "faw_act5", (-700.0 + 630.0, -40.0, 0.0), (-700.0 + 700.0, 200.0, 60.0), m["act"], [(F(2, 0.5), END)])
    tag(root, "tFAW about 21 ns: four ACTs max", (-700.0, 300.0, 60.0), beat(2))
    _cam(root, 3, (-480.0, 0.0, 0.0), 2500.0, 0.0, 0.10)
    K.commit({"all": []})


# ---- 5 conflicts and parallelism ---------------------------------------------------------


def sec5():
    m, root = begin("sec5", 3)
    d = _chip_die(root, m)
    g = d["banks"]
    # beat 0: eight requests spread over eight banks overlap in a quick stagger
    spread = [g[gi][b] for gi in range(4) for b in (0, 3)]
    for k, bk in enumerate(spread):
        f0 = 0.05 + 0.10 * k
        K.activate(root, bk, F(0, f0), F(0, f0 + 0.08), m)
        K.set_state(bk, "row", [(F(0, f0 + 0.08), F(1, 0.0))])
        K.reads(root, bk, F(0, f0 + 0.12), F(0, f0 + 0.30), 1, m)
    tag(root, "parallel banks hide each other's waits", (-420.0, 90.0, 40.0), beat(0))
    # beat 1: four requests, each a new row in bank A: every one waits a full conflict
    A = g[0][0]
    for k in range(4):
        f0 = 0.05 + 0.23 * k
        K.set_state(A, "pink", [(F(1, f0), F(1, f0 + 0.15))])
        K.set_state(A, "row", [(F(1, f0 + 0.15), F(1, f0 + 0.23))])
    tag(root, "same bank, new row: full conflict", K.above(A), beat(1))
    # beat 2: reordered: bank A serves its row hits; the others open and read
    K.set_state(A, "row", [(F(2, 0.0), F(3, 0.0))])
    K.reads(root, A, F(2, 0.05), F(2, 0.95), 6, m)
    for bk in (g[1][0], g[2][0], g[3][0]):
        K.set_state(bk, "row", [(F(2, 0.10), F(3, 0.0))])
        K.reads(root, bk, F(2, 0.30), F(2, 0.90), 2, m)
    tag(root, "row hits first, rest spread", K.above(A), beat(2))
    K.commit(d)
    _cam(root, 3, (160.0, 100.0, 0.0), 6000.0, 0.12, 0.16)


# ---- 6 numbers ----------------------------------------------------------------------------


def sec6():
    m, root = begin("sec6", 3)
    d4 = _chip_die(root, m, GROUPS)
    tag(root, "DDR4: 16 banks, 4 groups", (-1080.0, 620.0, 40.0), beat(0))
    show(d4["root"], beat(0))
    K.commit(d4)
    # beat 1: DDR5, eight groups of four
    d8 = _chip_die(root, m, GROUPS_8)
    tag(root, "DDR5: 32 banks in 8 groups", (-1480.0, 620.0, 40.0), beat(1))
    show(d8["root"], beat(1))
    K.commit(d8)
    camera(root, [
        ((160.0, 100.0, 0.0), 6000.0, 0.08, 0.16),
        ((180.0, 100.0, 0.0), 6600.0, 0.06, 0.16),
        ((0.0, 0.0, 0.0), 3000.0, 0.0, 0.08),
    ])
    # beat 2: transfers per burst, drawn as cubes: DDR4 8, DDR5 16
    for k in range(8):
        x = -800.0 + 100.0 * k
        timed(root, f"bl8_{k}", (x, 90.0, 0.0), (x + 80.0, 170.0, 60.0), m["rd"], beat(2))
    for k in range(16):
        x = -800.0 + 100.0 * k
        timed(root, f"bl16_{k}", (x, -170.0, 0.0), (x + 80.0, -90.0, 60.0), m["rd2"], beat(2))
    tag(root, "DDR4 burst: 8 transfers", (-800.0, 240.0, 60.0), beat(2))
    tag(root, "DDR5 burst: 16 transfers", (-800.0, -340.0, 60.0), beat(2))
    return root


# ---- 7 refresh ----------------------------------------------------------------------------


def sec7():
    m, root = begin("sec7", 3)
    d = _chip_die(root, m)
    g = d["banks"]
    # beat 0: DDR4: every bank closes and refreshes; the rank is locked
    for bk in d["all"]:
        K.set_state(bk, "cyan", [(F(0, 0.10), F(1, 0.0))])
    timed(root, "lock", (-1300.0, -22.0, 40.0), (1400.0, 22.0, 70.0), m["stop"], beat(0))
    tag(root, "DDR4 refresh: rank locked", (0.0, 640.0, 40.0), beat(0))
    # beat 1: DDR5: one bank index per group steps through the refresh
    for b in range(4):
        for gi in range(len(g)):
            K.set_state(g[gi][b], "cyan", [(F(1, 0.05 + 0.22 * b), F(1, 0.05 + 0.22 * (b + 1)))])
    tag(root, "DDR5 same-bank refresh", (0.0, 640.0, 40.0), beat(1))
    # beat 2: the other banks keep serving reads
    for gi in range(len(g)):
        K.set_state(g[gi][0], "cyan", [(F(2, 0.0), F(3, 0.0))])
        for b in (1, 2, 3):
            K.reads(root, g[gi][b], F(2, 0.10), F(2, 0.90), 2, m)
    tag(root, "other banks keep serving reads", (-1000.0, 640.0, 40.0), beat(2))
    K.commit(d)
    _cam(root, 3, (160.0, 100.0, 0.0), 6200.0, 0.12, 0.16)


# ---- 8 who makes it -----------------------------------------------------------------------

CHIPS = [(-1000.0, "Micron (MU)"), (0.0, "SK hynix (000660.KS)"), (1000.0, "Samsung (005930.KS)")]


def sec8():
    m, root = begin("sec8", 3)
    box("plinth", (-1500.0, -300.0, -60.0), (1500.0, 300.0, 0.0), m["plinth"], root)
    for i, (x, name) in enumerate(CHIPS):
        box(f"chip{i}", (x - 280.0, -180.0, 0.0), (x + 280.0, 180.0, 80.0), m["bank"], root)
        timed(root, f"lit{i}", (x - 280.0, -180.0, 80.0), (x + 280.0, 180.0, 110.0), m["row"], beat(i))
        tag(root, name, (x, 260.0, 110.0), beat(i))
    _cam(root, 3, (0.0, 0.0, 0.0), 5600.0, 0.0, 0.14)
    K.commit({"all": []})


# ---- 9 chokepoints and risks --------------------------------------------------------------


def sec9():
    m, root = begin("sec9", 3)
    d = _chip_die(root, m)
    g = d["banks"]
    A = g[0][0]
    # beat 0: two cores send requests to different rows of one bank
    K.set_state(A, "pink", [(F(0, 0.05), F(1, 0.0))])
    for k in range(3):
        K.send(root, "core_a", [(-1700.0, 400.0, 40.0), (A["cx"], A["cy"], 40.0)], F(0, 0.10 + 0.20 * k), F(0, 0.30 + 0.20 * k), m["cmd_dot"])
        K.send(root, "core_b", [(1700.0, 200.0, 40.0), (A["cx"], A["cy"], 40.0)], F(0, 0.20 + 0.20 * k), F(0, 0.40 + 0.20 * k), m["data_dot"])
    tag(root, "two cores fight over one bank", K.above(A), beat(0))
    K.commit(d)
    show(d["root"], beat(0))
    camera(root, [
        ((160.0, 100.0, 0.0), 6200.0, 0.12, 0.16),
        ((300.0, 140.0, 0.0), 3700.0, 0.06, 0.10),
        ((50.0, 200.0, 0.0), 3300.0, 0.06, 0.10),
    ])
    # beat 1: four ACTs fit in the window; the lid is tFAW, two more wait outside
    for i in range(4):
        timed(root, f"lit{i}", (-600.0 + 280.0 * i, -200.0, 0.0), (-600.0 + 280.0 * i + 180.0, 300.0, 200.0), m["row"], beat(1))
    for i in range(2):
        timed(root, f"wait{i}", (1000.0 + 280.0 * i, -200.0, 0.0), (1000.0 + 280.0 * i + 180.0, 300.0, 200.0), m["plinth"], beat(1))
    timed(root, "lid", (-700.0, 380.0, 0.0), (1300.0, 440.0, 80.0), m["window"], beat(1))
    tag(root, "tFAW caps how fast rows open", (-700.0, 520.0, 60.0), beat(1))
    # beat 2: denser chips: each doubles the rows, so more refresh work
    for k, h in enumerate((200.0, 400.0, 800.0)):
        x = -600.0 + 500.0 * k
        timed(root, f"stack{k}", (x, -300.0, 0.0), (x + 300.0, -300.0 + h, 120.0), m["cyan"], beat(2))
    tag(root, "denser chips: more rows to refresh", (-600.0, 620.0, 60.0), beat(2))
    return root


# ---- 10 sources -----------------------------------------------------------------------------

CARDS = [
    "[1] Micron DDR5 white paper",
    "[2] Wikipedia, DDR5 SDRAM",
    "[3] PCPer, Micron DDR5 program",
    "[4] DDR4-3200 SPD dump",
    "[5] G.Skill DDR4-3200 SPD",
    "[6] arXiv 1607.08578",
    "[7] arXiv 1509.03721 (DReAM)",
    "[8] HPCA 2012: bank partitioning",
]
LIT = [(0, 1, 2), (3, 4), (5, 6, 7)]


def _card_xy(i):
    return -1500.0 + 1000.0 * (i % 4), (300.0 if i < 4 else -340.0)


def sec10():
    m, root = begin("sec10", 3)
    box("plinth", (-2300.0, -600.0, -60.0), (2300.0, 600.0, 0.0), m["plinth"], root)
    for i in range(len(CARDS)):
        x, y = _card_xy(i)
        box(f"card{i}", (x - 250.0, y - 130.0, 0.0), (x + 250.0, y + 130.0, 30.0), m["paper"] if "paper" in m else m["bank"], root)
    for beat_i, group in enumerate(LIT):
        for i in group:
            x, y = _card_xy(i)
            timed(root, f"lit{i}", (x - 250.0, y - 130.0, 30.0), (x + 250.0, y + 130.0, 50.0), m["row"], beat(beat_i))
            ty = y + 230.0 if i < 4 else y - 230.0  # top-row tags above their cards, bottom-row tags below
            tag(root, CARDS[i], (x, ty, 60.0), beat(beat_i))
    _cam(root, 3, (0.0, 0.0, 0.0), 8200.0, 0.0, 0.10)
    K.commit({"all": []})


SECTIONS = [sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9, sec10]

if __name__ == "__main__":
    which = [int(n) for n in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else range(1, 11)
    for n in which:
        SECTIONS[n - 1]()
        finish(f"sec{n}", page="bank")
