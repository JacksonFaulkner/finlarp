"""The CELL overview, authored in Blender and exported for pbr3d in the MELT + PULL template
(docs/diagram-pages.md): one 1T1C DRAM cell cut open at its centre plane, with the camera on +z
and one pose per beat, and `label:<text>` empties for the tags the TUI pins on. The cell's pieces
are in cell_kit.py, shared with the zooms and sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/cell_overview.py

It writes:
  blender/cell_overview.blend   open it in Blender to edit by hand
  assets/cell_overview.glb      what pbr3d embeds and plays back

One beat is SEC (8) seconds at 24 fps; the TUI samples the file at t = (beat + local) * 8
(diagrams_nodes/cell/overview.rs).

Beats (match the CELL overview page):
  0 idle      a full capacitor holds the bit; the word line is low; the bit line sits at VDD/2
  1 word line the word line rises and the access transistor switches on
  2 sharing   charge moves from the cell onto the bit line: a small bump up (dV), a 0 would dip
  3 sense     the sense amp latches the bit line to a full rail and drives the cell back to full
  4 precharge the word line falls and the bit line is precharged back to VDD/2
  5 leakage   charge drains from the capacitor while the row is idle; a clock fills toward the
              refresh window and a red mark shows the level below which a read fails
  6 refresh   the row is read and rewritten before the charge is gone
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, empty, label, pivot, rel, show  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start, stream_of  # noqa: E402
import cell_kit as K  # noqa: E402
from cell_kit import ZC, SRC_X, DRN_X, BL_Y, CAP_Y0, CAP_Y1, WL_Y  # noqa: E402

BEATS = 7

WL_HIGH = [(F(1, 0), F(4, 0)), (F(6, 0.1), F(6, 0.96))]  # word line up for the read, down for precharge
BL_ACTIVE = [(F(2, 0), F(4, 0)), (F(6, 0), F(7, 0))]
SA_ON = [(F(3, 0.05), F(3, 0.95)), (F(6, 0.55), F(6, 0.95))]  # latches in the read and in the refresh
PRE_ON = [(F(0, 0), F(1, 0)), (F(4, 0), F(5, 0))]

# Charge is conserved on screen: each dot is a slice of charge, so the number of dots, and when the
# charge level and the gauge move, follow the dots. A dot takes LIFE frames to cross; the level at
# the source drops as dots leave, the level at the sink moves as they arrive.
LIFE = 60
SHARED = 0.15  # fraction of the cell's charge the bit line takes in a read
LEAKED = 0.26  # fraction lost to leakage by the end of the idle beat (down to DEADLINE_LV + margin)
LOW = 1.0 - LEAKED  # the charge level at the end of the leak
DEADLINE_LV = 0.70  # below this a read can no longer tell the bit: the weakest-cell deadline

POSES = [
    ((-100.0, 520.0, ZC), 5800.0, 0.30, 0.16),
    ((-100.0, 330.0, -420.0), 4300.0, 0.45, 0.20),
    ((-380.0, 620.0, ZC), 4600.0, 0.30, 0.16),
    ((-420.0, 700.0, ZC), 5000.0, 0.30, 0.16),
    ((-100.0, 650.0, ZC), 5800.0, 0.30, 0.16),
    ((SRC_X - 100.0, 450.0, ZC), 3600.0, 0.35, 0.18),
    ((-100.0, 520.0, ZC), 5800.0, 0.30, 0.18),
]


def build():
    m, root = start("overview", BEATS, page="cell")
    K.mats(m)
    parts = K.cell(root, m, lit_wl=WL_HIGH, lit_sa=SA_ON, lit_pre=PRE_ON, lit_bl=BL_ACTIVE)

    lag = LIFE / 192.0  # a dot's crossing time as a fraction of a beat

    # the bit-line gauge follows the dots as they land: a small bump on the read, then the latch
    # to 1.0, back to VDD/2 in precharge, and the same again in the refresh
    scale_keys(parts["bar"], [
        (0, (1, 1, 0.5)),
        (F(2, 0.25 + lag), (1, 1, 0.5)),
        (F(2, 0.55 + lag), (1, 1, 0.6)),
        (F(3, 0.60), (1, 1, 1.0)),
        (F(4, 0.60), (1, 1, 0.5)),
        (F(6, 0.05 + lag), (1, 1, 0.5)),
        (F(6, 0.28 + lag), (1, 1, 0.6)),
        (F(6, 0.58), (1, 1, 1.0)),
        (F(6, 0.97), (1, 1, 0.5)),
    ])
    # the charge: it leaves as dots leave and arrives as dots arrive. Full, shared out during the
    # read, restored by the latch, leaking, then read and rewritten in the refresh
    scale_keys(parts["fill"], [
        (0, (1, 1, 1.0)),
        (F(2, 0.25), (1, 1, 1.0)),
        (F(2, 0.55), (1, 1, 1.0 - SHARED)),
        (F(3, 0.10), (1, 1, 1.0 - SHARED)),
        (F(3, 0.45 + lag), (1, 1, 1.0)),
        (F(5, 0.10), (1, 1, 1.0)),
        (F(5, 0.85), (1, 1, LOW)),
        (F(6, 0.05), (1, 1, LOW)),
        (F(6, 0.28), (1, 1, LOW - 0.10)),  # the read takes charge out again before the rewrite
        (F(6, 0.58), (1, 1, LOW - 0.10)),
        (F(6, 0.74 + lag - 0.05), (1, 1, 1.0)),
    ])

    # charge sharing: a dot is a slice of charge, so the counts follow the amounts moved; the latch sends violet back
    stream_of(root, "share", 6, (SRC_X, 600.0, ZC), K.PATH_CAP_TO_BL, 14, m["cyan_dot"], 2, 0.25, 0.55, LIFE)
    stream_of(root, "restore", 6, (DRN_X, BL_Y, ZC), K.PATH_BL_TO_CAP, 14, m["violet_dot"], 3, 0.10, 0.45, LIFE)
    # leakage: orange dots drain out of the capacitor's side, steadily, while the level falls
    stream_of(root, "leak", 6, (SRC_X - 150, 380.0, ZC), K.PATH_LEAK, 18, m["orange_dot"], 5, 0.10, 0.85, 80)
    # refresh: read (cyan) up, then the latch, then rewrite (violet) back down
    stream_of(root, "refresh_read", 5, (SRC_X, 600.0, ZC), K.PATH_CAP_TO_BL, 14, m["cyan_dot"], 6, 0.05, 0.28, LIFE)
    stream_of(root, "refresh_write", 5, (DRN_X, BL_Y, ZC), K.PATH_BL_TO_CAP, 18, m["violet_dot"], 6, 0.58, 0.74, LIFE)

    # the margin: a 1 bumps the bit line up by dV, a 0 would dip it down by as much. The sense
    # amp only has to tell which way it moved.
    land = [(F(2, 0.55 + lag), F(3, 0.0))]
    dv = box("dv_bracket", (K.GAUGE_X + 170, K.HALF_Y, ZC - 20), (K.GAUGE_X + 210, K.HALF_Y + 100, ZC + 20), m["gold_glow"], root)
    show(dv, land)
    zero = box("zero_tick", (K.GAUGE_X - 125, K.HALF_Y - 100 - 7, ZC - 125), (K.GAUGE_X + 125, K.HALF_Y - 100 + 7, ZC + 125), m["gold_glow"], root)
    show(zero, land)

    # the clock: time since the last refresh, filling over the idle beat toward the 64 ms window
    # and emptying when the row is rewritten; and the deadline, the level below which a read fails
    clk_x = SRC_X + K.CAP_R + 330
    cg = empty("clock", root)
    show(cg, [(F(5, 0), F(7, 0))])
    box("clock_pole", (clk_x - 30, CAP_Y0, ZC - 30), (clk_x + 30, CAP_Y1, ZC + 30), m["grey"], cg)
    base = (clk_x, CAP_Y0, ZC)
    pv = pivot("clock_level", base, cg)
    box("clock_bar", rel(base, (clk_x - 70, CAP_Y0, ZC - 70)), rel(base, (clk_x + 70, CAP_Y1, ZC + 70)), m["gold_glow"], pv)
    scale_keys(pv, [
        (0, (1, 1, 0.02)),
        (F(5, 0.10), (1, 1, 0.02)),
        (F(5, 0.85), (1, 1, 1.0)),
        (F(6, 0.58), (1, 1, 1.0)),
        (F(6, 0.95), (1, 1, 0.02)),
    ])
    dl_y = CAP_Y0 + 20 + DEADLINE_LV * (CAP_Y1 - CAP_Y0 - 40)
    box("deadline", (SRC_X + K.CAP_R + 20, dl_y - 8, ZC - 25), (SRC_X + K.CAP_R + 230, dl_y + 8, ZC + 25), m["red"], cg)

    label("storage capacitor", (SRC_X + 40, CAP_Y1 + 70, ZC), root, [(F(0, 0), F(1, 0))])
    label("bit line at VDD/2", (K.GAUGE_X + 60, K.HALF_Y + 120, ZC), root, [(F(0, 0), F(2, 0))])
    label("word line: row select", (0, WL_Y + 190, ZC + 170), root, [(F(1, 0), F(2, 0))])
    label("access transistor", (-120, 60, ZC + 150), root, [(F(1, 0), F(2, 0))])
    label("charge sharing", (DRN_X, BL_Y + 130, ZC), root, [(F(2, 0), F(3, 0))])
    label("dV: all the sense amp sees", (K.GAUGE_X + 210, K.HALF_Y + 160, ZC), root, land)
    label("a 0 would dip, not rise", (K.GAUGE_X - 125, K.HALF_Y - 150, ZC), root, land)
    label("sense amp latches", (-1340, BL_Y + 210, ZC), root, [(F(3, 0), F(4, 0))])
    label("precharge to VDD/2", (1150, BL_Y + 210, ZC), root, [(F(4, 0), F(5, 0))])
    label("charge leaks away", (SRC_X - 260, 330, ZC + 80), root, [(F(5, 0), F(6, 0))])
    label("refresh rewrites the row", (SRC_X, CAP_Y1 + 230, ZC), root, [(F(6, 0), F(7, 0))])
    label("time since last refresh", (clk_x, CAP_Y1 + 70, ZC), root, [(F(5, 0), F(7, 0))])
    label("below this a read fails", (SRC_X + K.CAP_R + 230, dl_y, ZC), root, [(F(5, 0), F(7, 0))])

    camera(root, POSES)


if __name__ == "__main__":
    build()
    finish("overview", page="cell")
