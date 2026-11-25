"""TRM_PRECHARGE_COMMAND: the Terms-tab overview for DRAM PRECHARGE, on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_precharge_command.py

Writes assets/term_TRM_PRECHARGE_COMMAND.glb. Captions live in specs/terms/TRM_PRECHARGE_COMMAND.json.

One bank of an HBM die is drawn cut open on the bench with row 2 already open. PRECHARGE writes
the row buffer back into the cells, drops the wordline and equalizes every bitline to half VDD
(blue), so the bank can ACTIVATE row 6. A command timeline under the bank shows tRP.

Beats:
  0 hbm      HBM stacks beside the GPU package
  1 open     row 2 open: wordline up, bitlines at full swing, row buffer full
  2 restore  PRECHARGE: row buffer writes back down into the row's cells
  3 equalize wordline drops, bitlines equalize to half VDD, tRP timer fills
  4 next     ACTIVATE row 6; the row-switch cost and why controllers reuse open rows
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from power_vrm_detail import bx, mat, frame, present, run  # noqa: E402
from sand_overview import empty, show  # noqa: E402

SLUG = "TRM_PRECHARGE_COMMAND"
BEATS = [
    ("HBM stacks beside the GPU hold its working data",
     "An AI accelerator keeps weights and activations in HBM, stacks of DRAM dies next to the GPU. Each die has many "
     "banks, and each bank can have only one row open at a time."),
    ("A bank with row 2 open: the row buffer holds its data",
     "An earlier ACTIVATE raised row 2's wordline. The sense amps drove every bitline to a full 0 or 1 and the row "
     "buffer now holds the whole row. Reads of that row are fast, but no other row in this bank can be reached."),
    ("PRECHARGE first restores the row into its cells",
     "Reading a DRAM cell drains its charge, so the data lives only in the sense amps after ACTIVATE. Before the row "
     "closes, the sense amps drive full-strength charge back into every cell of the row. That write-back is what "
     "keeps the bits from being lost."),
    ("Then the wordline drops and bitlines settle to half voltage",
     "The wordline falls, sealing each capacitor, and every bitline pair is shorted to half the supply voltage. A "
     "bitline sitting at the midpoint is what lets the next row's tiny charge tip it up or down. The time this takes "
     "is tRP, about 14 ns in modern DRAM."),
    ("Only now can the bank open another row",
     "A new ACTIVATE (row 6 here) can start once tRP has passed. Random access that keeps jumping rows pays "
     "PRECHARGE plus ACTIVATE every time, so controllers reorder requests to hit already-open rows. Related: Micron "
     "(MU), SK hynix (000660.KS), Rambus (RMBS)."),
]

BX0, BX1, BZ0, BZ1 = 160.0, 236.0, -72.0, -24.0
ROWS, COLS = 8, 12
TZ = -11.0  # command timeline


def bigfill(m, parent, name, x0, x1, y, z, beat, u0, u1, until_beat, n=10, mt="dram_timer", hw=3.6, h=3.0):
    """kit_dram.fill, about 3x thicker: blocks appear left to right over beat/u0..u1."""
    g = empty(name, parent)
    w = (x1 - x0) / n
    for k in range(n):
        a = x0 + w * k
        blk = empty(f"{name}_e{k}", g)
        bx(f"{name}_{k}", (a + 0.3, y, z - hw), (a + w - 0.3, y + h, z + hw), m[mt], blk)
        show(blk, [(F(beat, u0 + (u1 - u0) * k / n), F(until_beat + 1, 0))])
    return g


def lane(m, parent, name, x0, x1, z, mt="dram_sub"):
    g = empty(name + "_e", parent)
    bx(name, (x0, 0.2, z - 4.2), (x1, 0.8, z + 4.2), m[mt], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    for k, c in {"lq": (1.0, 0.85, 0.35), "lr": (1.0, 0.45, 0.10), "lc": (1.0, 0.20, 0.25),
                 "lb": (0.15, 0.85, 1.0), "le": (0.25, 0.45, 1.0)}.items():
        m[k] = mat(f"lat_{k}", tuple(v * 0.6 for v in c), emit=c, strength=1.4)
    b = C.base(m, root)
    pk = b["pk"]
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=ROWS, cols=COLS)
    pts = bk["pts"]
    present(bk["g"], [(F(1, 0), F(5, 0))])
    C.magnify(m, root, (pk["hbm"][0], 0.0, pk["hbm"][2]), pts["top"])

    # row 2 open through beats 1-3 (wordline drops at mid beat 3)
    K.row_open(bk, 2, [(F(1, 0), F(3, 0.3))])
    K.bl_show(bk, "hi", [(F(1, 0), F(3, 0.3))])
    K.io_flow(m, bk, [3, 5, 7, 9], 1, 0.2, 0.8)
    # beat 2: write back
    K.write_back(m, bk, 2, 2, 0.05, 0.7)
    # beat 3: equalize, then beat 4 equalized until row 6 opens
    K.bl_show(bk, "eq", [(F(3, 0.3), F(4, 0.35))])
    K.row_open(bk, 6, [(F(4, 0.35), F(5, 0))])
    K.charge_share(m, bk, 6, 4, 0.35, 0.8)
    K.bl_show(bk, "hi", [(F(4, 0.75), F(5, 0))])

    # command timeline: PRE tick, tRP fill, ACT tick
    strip = lane(m, root, "cmd", BX0, BX1, TZ)
    show(strip, [(F(1, 0), F(5, 0))])
    pre = empty("t_pre_e", root)
    bx("t_pre", (BX0 + 7.0, 0.6, TZ - 5.0), (BX0 + 8.5, 10.0, TZ + 5.0), m["warn"], pre)
    act = empty("t_act_e", root)
    bx("t_act", (BX0 + 51.5, 0.6, TZ - 5.0), (BX0 + 53.0, 10.0, TZ + 5.0), m["sig"], act)
    show(pre, [(F(2, 0), F(5, 0))])
    show(act, [(F(4, 0.3), F(5, 0))])
    bigfill(m, root, "trp", BX0 + 9.0, BX0 + 51.0, 0.8, TZ, 2, 0.1, 1.0, 3, n=6, mt="lq")
    bigfill(m, root, "trp2", BX0 + 9.0, BX0 + 51.0, 3.9, TZ, 3, 0.0, 0.9, 4, n=6, mt="le")

    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]), ("one bank, cut open ->", (130.0, 4.0, -50.0))],
        1: [("row 2 open: wordline up", pts["wl"](2)), ("bitlines at full swing", pts["bl"](5)),
            ("row buffer holds row 2", pts["rb"](6)), ("reads hit the open row", pts["io"])],
        2: [("PRE issued", (BX0 + 8.0, 10.0, TZ)), ("row buffer writes back", pts["rb"](4)),
            ("cells refilled at full charge", pts["wl"](2))],
        3: [("wordline drops, row sealed", pts["wl"](2)), ("bitlines equalize to VDD/2", pts["bl"](8)),
            ("tRP: about 14 ns", (BX0 + 30.0, 7.0, TZ))],
        4: [("ACT row 6 after tRP", pts["wl"](6)), ("PRE + ACT on every row switch", (BX0 + 52.0, 10.0, TZ)),
            ("controllers reuse open rows", pts["rb"](3))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame(((BX0 + BX1) / 2, 6.0, -44.0), 125.0, 0.25, 0.50),
        frame(((BX0 + BX1) / 2, 6.0, -42.0), 110.0, 0.20, 0.55),
        frame(((BX0 + BX1) / 2, 4.0, -40.0), 115.0, 0.28, 0.60),
        frame(((BX0 + BX1) / 2, 4.0, -42.0), 130.0, 0.32, 0.55),
    ], root)


if __name__ == "__main__":
    build()
