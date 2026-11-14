"""The DRAM die as reusable Blender pieces for the BANK pictures (overview, zooms, sections), built on
sand_overview / sand_zooms and the template in docs/diagram-pages.md.

A schematic, not a layout drawing. Units are millimetres, Y up. The die lies face-on to the camera
(on +z), so bank fronts sit at z = 0 and the parts that move (command dots, data bursts, row
buffers) run in front of them at z = 40. Nothing is cut away.

The die: a substrate, bank groups of four banks (2 x 2 each) in a frame, a command bus along the
top edge, a data bus lane through the middle that runs out to the I/O pad on the right. An open
bank shows its row buffer as a bright plate standing off the front; PRECHARGE and refresh are
pink and cyan overlays on the bank.
"""

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, box, empty, fly, key, label, mat, show  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402,F401

END = F(40, 0)  # "until the end"; later than any scene
BANK_W, BANK_H, BANK_D = 300.0, 200.0, 60.0  # one bank, and its depth into the die
GAP = 40.0  # between banks in a group, and the frame's margin
GROUP_W = 2 * BANK_W + GAP  # 640: a group is 2 x 2 banks
GROUP_H = 2 * BANK_H + GAP  # 440
GROUPS = [(-720.0, 330.0), (720.0, 330.0), (-720.0, -330.0), (720.0, -330.0)]  # 4 groups (DDR4)
GROUPS_8 = [(x, y) for y in (330.0, -330.0) for x in (-1110.0, -370.0, 370.0, 1110.0)]  # 8 groups (DDR5)
SUB_X, SUB_Y = 1400.0, 700.0  # substrate half-size
IO_X = 1560.0  # the I/O pad sits right of the die
CMD_Y = 850.0  # the command bus runs along the top
DATA_Y = 0.0  # the data lane runs through the middle

_seq = itertools.count()


def mats(m):
    """The die's materials, added to the sand_overview set."""
    m["bank"] = mat("bank_tile", (0.92, 0.48, 0.20), metal=0.05, rough=0.5)
    m["substrate"] = mat("substrate", (0.10, 0.13, 0.11), rough=0.8)
    m["frame"] = mat("group_frame", (0.30, 0.32, 0.36), metal=0.5, rough=0.45)
    m["cmd_bus"] = mat("cmd_bus", (0.85, 0.80, 0.68), metal=0.7, rough=0.35)
    m["cmd_dot"] = mat("cmd_dot", (1.0, 1.0, 1.0), emit=(1.0, 1.0, 1.0), strength=3.0)
    m["data"] = mat("data_bus", (0.25, 0.85, 0.40), emit=(0.3, 1.0, 0.45), strength=1.6)
    m["data_dot"] = mat("data_dot", (0.4, 1.0, 0.5), emit=(0.4, 1.0, 0.5), strength=3.0)
    m["row"] = mat("row_buffer", (1.0, 0.92, 0.55), emit=(1.0, 0.9, 0.5), strength=2.5)
    m["pink"] = mat("pink_state", (1.0, 0.40, 0.65), emit=(1.0, 0.35, 0.6), strength=2.5)
    m["cyan"] = mat("cyan_state", (0.35, 0.90, 1.0), emit=(0.3, 0.85, 1.0), strength=2.2)
    m["io"] = mat("io_pad", (0.80, 0.82, 0.88), metal=0.8, rough=0.3)
    m["idle"] = mat("idle_strip", (0.45, 0.46, 0.50), metal=0.4, rough=0.5)
    m["stop"] = mat("stop_block", (0.55, 0.20, 0.20), emit=(0.8, 0.2, 0.15), strength=1.0)
    return m


def uniq(name):
    return f"{name}_{next(_seq)}"


def bank_xy(gx, gy, b):
    """Centre of bank `b` (0-3) in the group centred at (gx, gy)."""
    col, row = b % 2, b // 2
    return gx + (col - 0.5) * (BANK_W + GAP), gy + (row - 0.5) * (BANK_H + GAP)


def bank(parent, name, cx, cy, m, w=BANK_W, h=BANK_H, pop=60.0):
    """One bank: its body, its row buffer (`row`, a plate standing off the front) and two overlays,
    `pink` (precharge, conflict, waiting) and `cyan` (refresh). Switch them with show()."""
    g = empty(name, parent)
    box(f"{name}_body", (cx - w / 2, cy - h / 2, -BANK_D), (cx + w / 2, cy + h / 2, 0), m["bank"], g)
    row = empty(f"{name}_row", g)
    box(f"{name}_plate", (cx - w * 0.42, cy - h * 0.12, 0), (cx + w * 0.42, cy + h * 0.12, pop), m["row"], row)
    pk = empty(f"{name}_pink", g)
    box(f"{name}_pink_b", (cx - w / 2 - 8, cy - h / 2 - 8, 0), (cx + w / 2 + 8, cy + h / 2 + 8, 24), m["pink"], pk)
    cy_ = empty(f"{name}_cyan", g)
    box(f"{name}_cyan_b", (cx - w / 2 - 8, cy - h / 2 - 8, 0), (cx + w / 2 + 8, cy + h / 2 + 8, 24), m["cyan"], cy_)
    return {
        "name": name, "g": g, "row": row, "pink": pk, "cyan": cy_, "cx": cx, "cy": cy, "w": w, "h": h,
        "iv": {"row": [], "pink": [], "cyan": []},
    }


def set_state(bk, which, intervals):
    """Record when bank `bk`'s `which` ("row", "pink" or "cyan") is on. Call commit() once at the end;
    show() can key an object only once."""
    bk["iv"][which].extend(intervals)


def _merge(iv):
    """Sorted intervals with overlaps and touching ends joined, so show() keys each once."""
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def commit(d):
    """Key every bank's state switches. Anything never set stays off."""
    for bk in d["all"]:
        for which in ("row", "pink", "cyan"):
            show(bk[which], _merge(bk["iv"][which]))


def die(root, m, groups=GROUPS, lane=True):
    """The die: substrate, one frame per group, banks[g][b], the data lane, the I/O pad and the
    command bus. Returns {"banks": [[bank, ...] per group], "all": [bank, ...]}."""
    g0 = empty("die", root)
    half = max(SUB_X, max(abs(gx) for gx, _ in groups) + GROUP_W / 2 + 80.0)
    box("substrate", (-half, -SUB_Y, -140), (half, SUB_Y, -90), m["substrate"], g0)
    banks = []
    for gi, (gx, gy) in enumerate(groups):
        box(
            f"frame{gi}",
            (gx - GROUP_W / 2 - 40, gy - GROUP_H / 2 - 40, -90),
            (gx + GROUP_W / 2 + 40, gy + GROUP_H / 2 + 40, -60),
            m["frame"],
            g0,
        )
        row = []
        for b in range(4):
            cx, cy = bank_xy(gx, gy, b)
            row.append(bank(g0, f"bank{gi}_{b}", cx, cy, m))
        banks.append(row)
    if lane:
        box("data_lane", (-SUB_X, DATA_Y - 45, -30), (IO_X, DATA_Y + 45, 30), m["data"], g0)
    box("io_pad", (IO_X, -170, -40), (IO_X + 120, 170, 60), m["io"], g0)
    box("cmd_bus", (-SUB_X, CMD_Y - 30, -40), (SUB_X, CMD_Y + 30, 40), m["cmd_bus"], g0)
    return {"banks": banks, "all": [b for row in banks for b in row], "root": g0}


def send(parent, name, path, f0, f1, m, r=22.0):
    """One dot that travels `path` (absolute poly points) between frames f0 and f1."""
    e = empty(uniq(name), parent)
    ball(e.name + "_s", (0, 0, 0), r, m, e, 10)
    fly(e, path, f0, f1, steps=3)
    show(e, [(f0, f1)])
    return e


def cmd_path(bk):
    """From the command bus down to the front of bank `bk`."""
    return [(bk["cx"], CMD_Y, 40), (bk["cx"], bk["cy"] + bk["h"] / 2 + 50, 40), (bk["cx"], bk["cy"], 40)]


def data_path(bk):
    """From the front of bank `bk` down onto the data lane and out to the I/O pad."""
    return [(bk["cx"], bk["cy"], 40), (bk["cx"], DATA_Y, 40), (IO_X, DATA_Y, 40)]


def activate(root, bk, f0, f1, m):
    """A command dot (ACTIVATE, PRECHARGE...) sent to bank `bk` from frame f0 to f1."""
    return send(root, f"cmd_{bk['name']}", cmd_path(bk), f0, f1, m["cmd_dot"])


def reads(root, bk, f0, f1, n, m):
    """`n` data bursts leaving `bank`, spread over frames f0 to f1."""
    span = (f1 - f0) / n
    for k in range(n):
        a = round(f0 + span * k)
        send(root, f"rd_{bk['name']}", data_path(bk), a, round(a + span * 0.85), m["data_dot"])


def tag(root, text, at, intervals):
    """A tag pinned at poly point `at` for `intervals` (see sand_overview.label)."""
    return label(text, at, root, intervals)


def above(bk, dy=25.0):
    """A point just above bank `bk`, in front of the die, for a tag."""
    return (bk["cx"], bk["cy"] + bk["h"] / 2 + dy, 60)


def front(bk, dz=60.0):
    return (bk["cx"], bk["cy"], dz)


def scene_root(name, beats, page="bank"):
    """A fresh scene with the die's materials; returns (materials, root)."""
    m, root = start(name, beats, page=page)
    mats(m)
    return m, root


def export(name, page="bank"):
    finish(name, page=page)
