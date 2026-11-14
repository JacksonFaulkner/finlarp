"""The five BANK zoom-ins, authored in Blender and exported for pbr3d in the MELT template
(docs/diagram-pages.md), built from the die pieces in bank_kit.py. Zoom keys match the old
procedural page: a one bank, b bank groups, c the four-activate window, d address mapping,
e refresh.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/bank_zooms.py [-- one groups]

For each zoom it writes blender/bank_<name>.blend and assets/bank_<name>.glb.

  one     one bank: ACTIVATE opens a row into the row buffer, READs leave it, PRECHARGE closes it,
          then a new row is opened
  groups  READs inside one group are tCCD_L apart; alternating groups fill the data bus
  faw     four ACTIVATEs tRRD apart inside one tFAW window; the fifth waits for the window
  map     the address fields (row, bank, group, column); consecutive addresses and a stride
  refresh DDR4's all-bank refresh vs DDR5's same-bank refresh, with reads carrying on

One beat is SEC (8) seconds at 24 fps; every zoom is four beats.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, OFF, P, beat, box, empty, mat, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402
import bank_kit as K  # noqa: E402
from bank_kit import END, IO_X  # noqa: E402

BEATS = 4


def begin(name, beats=BEATS):
    m, root = start(name, beats, page="bank")
    K.mats(m)
    m["gold"] = mat("gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["field_row"] = mat("field_row", (0.62, 0.45, 0.85), emit=(0.6, 0.4, 0.9), strength=1.2)
    m["field_bank"] = mat("field_bank", (0.35, 0.80, 0.90), emit=(0.3, 0.75, 0.9), strength=1.2)
    m["field_group"] = m["gold"]
    m["field_col"] = mat("field_col", (0.45, 0.90, 0.50), emit=(0.4, 0.9, 0.45), strength=1.2)
    m["rd"] = mat("rd_block", (0.95, 0.55, 0.20), emit=(0.9, 0.5, 0.15), strength=1.0)
    m["rd2"] = mat("rd_block2", (0.35, 0.90, 1.0), emit=(0.3, 0.85, 1.0), strength=1.2)
    m["act"] = mat("act_block", (0.95, 0.55, 0.20), metal=0.1, rough=0.4)
    m["ghost"] = mat("ghost_pink", (1.0, 0.40, 0.65), emit=(1.0, 0.35, 0.6), strength=0.9, alpha=0.45)
    m["window"] = mat("window_pink", (1.0, 0.40, 0.65), emit=(1.0, 0.35, 0.6), strength=1.6, alpha=0.6)
    m["plinth"] = mat("plinth", (0.18, 0.19, 0.23), rough=0.8)
    return m, root


def timed(root, name, lo, hi, m, intervals):
    """A solid block from poly `lo` to `hi`, switched on for `intervals`."""
    e = empty(name, root)
    box(name + "_b", lo, hi, m, e)
    show(e, intervals)
    return e


def tag(root, text, at, intervals):
    return K.tag(root, text, at, intervals)


# ---- one: one bank -------------------------------------------------------------------------


def one():
    m, root = begin("one")
    bk = K.bank(root, "bank", 0.0, 0.0, m, w=1400.0, h=900.0, pop=80.0)
    K.set_state(bk, "row", [(F(0, 0.5), F(2, 0.10)), (F(3, 0.25), END)])
    K.set_state(bk, "pink", [(F(2, 0.10), F(2, 0.55))])
    K.activate(root, bk, F(0, 0.10), F(0, 0.48), m)
    K.reads(root, bk, F(1, 0.10), F(1, 0.95), 6, m)
    K.send(root, "pre", [(0.0, 900.0, 40.0), (0.0, 60.0, 40.0)], F(2, 0.05), F(2, 0.40), m["cmd_dot"])
    K.send(root, "act2", [(0.0, 900.0, 40.0), (0.0, 60.0, 40.0)], F(3, 0.05), F(3, 0.25), m["cmd_dot"])
    tag(root, "ACTIVATE: row into the row buffer", (0.0, 500.0, 60.0), beat(0))
    tag(root, "READs leave the row buffer", (700.0, 120.0, 60.0), beat(1))
    tag(root, "PRECHARGE: row closes", (-620.0, 500.0, 60.0), beat(2))
    tag(root, "next ACTIVATE opens a new row", (-620.0, 500.0, 60.0), beat(3))
    K.commit({"all": [bk]})
    camera(root, [((0.0, 0.0, 0.0), 3500.0, 0.22, 0.14)] * BEATS)


# ---- groups: bank groups and tCCD ----------------------------------------------------------

BURST = 200.0
SAME_STEP = 430.0  # READs in one group: a burst plus the rest of tCCD_L (about 2.1 bursts)
ALT_STEP = 210.0  # READs across groups: one burst apart


def groups():
    m, root = begin("groups")
    box("base", (-1050, -300, -40), (1050, 300, 0), m["plinth"], root)
    tag(root, "tCCD_L: same group, longer gap", (-80.0, 360.0, 40.0), beat(0))
    tag(root, "alternating groups: no gap", (-80.0, 360.0, 40.0), beat(1))
    tag(root, "idle bus slots: the gaps", (-80.0, 360.0, 40.0), beat(2))
    tag(root, "same bus: alternating fills it", (-80.0, 360.0, 40.0), beat(3))
    same_y, alt_y = 150.0, -150.0
    for k in range(5):
        x = -860.0 + SAME_STEP * k
        timed(root, f"rd_same{k}", (x, same_y - 90, 0), (x + BURST, same_y + 90, 50), m["rd"], [(F(0, 0.05), F(3, 0))])
    for k in range(6):
        x = -840.0 + ALT_STEP * k
        timed(root, f"rd_alt{k}", (x, same_y - 90, 0), (x + BURST, same_y + 90, 50), m["rd2"] if k % 2 else m["rd"], [(F(1, 0.05), F(2, 0.0))])
    for k in range(4):
        x = -860.0 + SAME_STEP * k + BURST
        timed(root, f"gap{k}", (x, same_y - 90, 0), (x + SAME_STEP - BURST, same_y + 90, 40), m["window"], [(F(2, 0.05), F(3, 0))])
    for k in range(8):
        x = -840.0 + ALT_STEP * k
        timed(root, f"rd_low{k}", (x, alt_y - 90, 0), (x + BURST, alt_y + 90, 50), m["rd2"] if k % 2 else m["rd"], [(F(3, 0.05), F(4, 0.0))])
    camera(root, [((0.0, 0.0, 0.0), 4300.0, 0.0, 0.10)] * BEATS)
    K.commit({"all": []})


# ---- faw: the four-activate window -----------------------------------------------------

SLOT = 110.0  # tRRD, about 3.7 ns, drawn as a slot
WIN = 630.0  # tFAW, about 21 ns, drawn as 5.7 slots
X0 = -700.0


def faw():
    m, root = begin("faw")
    box("base", (-900, -420, -40), (400, 300, 0), m["plinth"], root)
    acts = []
    for i in range(5):
        x = X0 + SLOT * i
        acts.append((x, F(0, 0.10 + 0.08 * i) if i < 4 else F(2, 0.55)))
    for i, (x, f0) in enumerate(acts[:4]):
        timed(root, f"act{i}", (x, -40, 0), (x + 80, 200, 60), m["act"], [(f0, END)])
    # the fifth ACTIVATE is wanted at slot 4 but must wait for the window to end
    timed(root, "act_wanted", (X0 + SLOT * 4, -40, 0), (X0 + SLOT * 4 + 80, 200, 60), m["ghost"], [(F(1, 0.0), F(2, 0.5))])
    timed(root, "act4", (X0 + WIN, -40, 0), (X0 + WIN + 80, 200, 60), m["act"], [(F(2, 0.55), END)])
    timed(root, "win1", (X0, -340, 0), (X0 + WIN, -300, 40), m["window"], [(F(1, 0.0), F(3, 0.0))])
    timed(root, "win2", (X0 + SLOT, -340, 0), (X0 + SLOT + WIN, -300, 40), m["window"], [(F(3, 0.0), END)])
    tag(root, "four ACTs, tRRD apart", (X0 + 150, 260.0, 60.0), beat(0))
    tag(root, "tFAW: no more than four", (X0 + 300, -260.0, 60.0), beat(1))
    tag(root, "the fifth waits for the window", (X0 + SLOT * 4, 260.0, 60.0), beat(2))
    tag(root, "window slides: ACT 5 now fits", (X0 + SLOT * 2, 260.0, 60.0), beat(3))
    camera(root, [((-200.0, 0.0, 0.0), 3300.0, 0.0, 0.10)] * BEATS)
    K.commit({"all": []})


# ---- map: address mapping ------------------------------------------------------------------


def mapping():
    m, root = begin("map")
    fields = [("row bits", -700.0, -220.0, "field_row"), ("bank", -200.0, -60.0, "field_bank"),
              ("group", -40.0, 60.0, "field_group"), ("column bits", 80.0, 600.0, "field_col")]
    for name, x0, x1, mm in fields:
        timed(root, f"field_{name.replace(' ', '_')}", (x0, 300, 0), (x1, 420, 60), m[mm], [(F(0, 0.0), END)])
    tag(root, "column bits: lowest", (340.0, 470.0, 60.0), beat(0))
    tag(root, "bank bits pick the bank", (-120.0, 470.0, 60.0), beat(0))
    banks = []
    for k, cx in enumerate((-330.0, -110.0, 110.0, 330.0)):
        bk = K.bank(root, f"bank{k}", cx, -170.0, m, w=180.0, h=130.0, pop=40.0)
        banks.append(bk)
    # beat 1: consecutive addresses all hit one open row of bank 0
    K.set_state(banks[0], "row", [(F(1, 0.05), END)])
    for k in range(4):
        K.send(root, "seq", [(340.0 - 60 * k, 360.0, 40.0), (-330.0, -170.0, 40.0)], F(1, 0.10 + 0.18 * k), F(1, 0.22 + 0.18 * k), m["cmd_dot"])
    tag(root, "consecutive: one open row", (-330.0, 40.0, 60.0), beat(1))
    # beat 2: a stride flips the bank bits; each request goes to another bank
    for k, bk in enumerate(banks):
        K.set_state(bk, "row", [(F(2, 0.05 + 0.1 * k), END)])
        K.send(root, "stride", [(-120.0 + 90 * k, 360.0, 40.0), (bk["cx"], bk["cy"], 40.0)], F(2, 0.05 + 0.1 * k), F(2, 0.25 + 0.1 * k), m["cmd_dot"])
    tag(root, "stride: many banks at once", (0.0, 40.0, 60.0), beat(2))
    # beat 3: reorder: bank 0 keeps reading its row; the rest spread out
    K.reads(root, banks[0], F(3, 0.10), F(3, 0.95), 6, m)
    for bk in banks[1:]:
        K.reads(root, bk, F(3, 0.30), F(3, 0.90), 2, m)
    tag(root, "row hits first, rest spread", (-120.0, 40.0, 60.0), beat(3))
    K.commit({"all": banks})
    camera(root, [((0.0, 100.0, 0.0), 3600.0, 0.10, 0.22)] * BEATS)


# ---- refresh: DDR4 all-bank vs DDR5 same-bank -----------------------------------------------


def refresh():
    m, root = begin("refresh")
    d = K.die(root, m)
    g = d["banks"]
    tag(root, "rank locked during all-bank refresh", (0.0, 640.0, 40.0), beat(0))
    tag(root, "same bank in every group", (0.0, 640.0, 40.0), beat(1))
    tag(root, "other banks keep serving reads", (-1000.0, 640.0, 40.0), beat(2))
    tag(root, "denser: refresh eats more time", (0.0, 640.0, 40.0), beat(3))
    # beat 0: DDR4, every bank closes and refreshes at once
    for bk in d["all"]:
        K.set_state(bk, "cyan", [(F(0, 0.20), F(1, 0.50))])
    # beat 1: DDR5, one bank index per group at a time
    for b in range(4):
        for gi in range(len(g)):
            K.set_state(g[gi][b], "cyan", [(F(1, 0.05 + 0.22 * b), F(1, 0.05 + 0.22 * (b + 1)))])
    # beat 2: the other banks keep serving reads while one index refreshes
    for gi in range(len(g)):
        for b in (1, 2, 3):
            K.reads(root, g[gi][b], F(2, 0.10), F(2, 0.90), 2, m)
    K.set_state(g[0][0], "cyan", [(F(2, 0.0), F(2, 0.9))])
    # beat 3: denser chips; two indices refresh in every group
    for gi in range(len(g)):
        for b in (0, 1):
            K.set_state(g[gi][b], "cyan", [(F(3, 0.0), END)])
    K.commit(d)
    camera(root, [((60.0, 100.0, 0.0), 6000.0, 0.14, 0.18)] * BEATS)


ZOOMS = {"one": one, "groups": groups, "faw": faw, "map": mapping, "refresh": refresh}

if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(ZOOMS)
    for name in which:
        ZOOMS[name]()
        finish(name, page="bank")
