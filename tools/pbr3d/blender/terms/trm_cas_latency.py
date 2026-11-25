"""TRM_CAS_LATENCY: the Terms-tab overview for DRAM CAS latency (CL), on the GPU base board.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_cas_latency.py

Writes assets/term_TRM_CAS_LATENCY.glb. Captions live in specs/terms/TRM_CAS_LATENCY.json.

One HBM bank is drawn cut open on the bench with a command timeline in front of it: clock ticks,
command markers and timer bars that fill while the bank works. Row 3 is already open; a READ goes
in, the CL bar fills cycle by cycle, then the data burst leaves the row buffer.

Also holds stage()/timeline helpers that the sibling timing terms (tRCD, tRP, tRC) import.

Beats:
  0 hbm      HBM stacks beside the GPU package
  1 open     row 3 is open, row buffer full
  2 read     READ issued; the CL timer fills cycle by cycle
  3 burst    the data burst leaves the row buffer after CL
  4 numbers  CL in cycles vs nanoseconds, and why it matters less than bandwidth
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from sand_overview import empty, show  # noqa: E402
from power_vrm_detail import bx, frame, mat, present  # noqa: E402

SLUG = "TRM_CAS_LATENCY"
BEATS = [
    ("HBM stacks next to the GPU hold the model's data",
     "An AI accelerator reads its weights and activations from HBM, stacks of DRAM dies beside the GPU package. "
     "Every read lands in one bank of one die, and the bank answers on a fixed clock schedule set by timing numbers."),
    ("Row 3 is already open: the row buffer holds it",
     "An earlier ACTIVATE raised wordline 3 and the sense amps latched the whole row into the row buffer. "
     "Any column of this row can now be read without touching the cells again."),
    ("READ goes in, then the bank waits CL clock cycles",
     "The controller sends READ with a column address. The bank selects those columns in the row buffer and drives "
     "them toward the I/O pins, which takes a fixed number of clock cycles: the CAS latency, CL or tCL. "
     "Each block in the bar is one memory clock."),
    ("After CL, the data burst streams out",
     "When CL cycles have passed, the first data word appears on the bus and the rest of the burst follows on "
     "consecutive clock edges. The controller can already have the next READ queued, so bursts from the open row "
     "come back to back."),
    ("CL counts cycles; the real wait is cycles times clock period",
     "DDR5-6400 at CL40 and DDR4-3200 at CL22 both wait about 13 to 14 ns, because the faster clock needs more cycles. "
     "For AI, CL matters less than bandwidth: long tensor streams keep many reads in flight and hide the wait. "
     "Related: Micron (MU), SK hynix (000660.KS), Samsung (005930.KS)."),
]

BX0, BX1, BZ0, BZ1 = 160.0, 236.0, -72.0, -30.0
ROWS, COLS = 8, 12
TZ = -16.0           # command timeline z (in front of the bank)
TX0, TX1 = 160.0, 236.0


def stage(slug, n_beats):
    """Board + bank + timeline strip with clock ticks. Returns (m, root, b, bk)."""
    m, root = C.setup(slug, n_beats)
    K.mats(m)
    b = C.base(m, root)
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=ROWS, cols=COLS)
    present(bk["g"], [(F(1, 0), F(n_beats, 0))])
    bx("tl_strip", (TX0, 0.3, TZ - 4.0), (TX1, 0.6, TZ + 4.0), m["dram_sub"], bk["g"])
    clk = empty("tl_clk", bk["g"])
    for i in range(20):
        x = TX0 + 2.0 + i * (TX1 - TX0 - 4.0) / 19
        bx(f"tl_clk_{i}", (x - 0.2, 0.6, TZ + 4.2), (x + 0.2, 2.0, TZ + 4.8), m["dram_tick"], clk)
    C.magnify(m, root, (b["pk"]["hbm"][0], 0.0, b["pk"]["hbm"][2]), bk["pts"]["top"])
    return m, root, b, bk


def fill(m, parent, name, x0, x1, y, z, beat, u0, u1, until_beat, n=10, mt="dram_timer"):
    """Bold glowing timer bar (3x kit size): blocks light left to right over beat/u0..u1, stay to until_beat."""
    key = "tl_amber" if mt == "dram_timer" else "tl_cyan"
    if key not in m:
        col = (1.0, 0.62, 0.15) if key == "tl_amber" else (0.35, 0.85, 1.0)
        m[key] = mat(key, col, emit=col, strength=4.0)
    g = empty(name, parent)
    w = (x1 - x0) / n
    end = F(until_beat + 1, 0)
    for k in range(n):
        a = x0 + w * k
        blk = bx(f"{name}_{k}", (a, y, z - 3.6), (a + w, y + 3.0, z + 3.6), m[key], g)
        show(blk, [(F(beat, u0 + (u1 - u0) * k / n), end)])
    return g


def cmd(m, bk, name, x, beat, u, n_beats):
    """A command marker on the timeline, shown from beat/u onward."""
    t = K.tick(m, bk["g"], name, x, TZ)
    show(t, [(F(beat, u), F(n_beats, 0))])
    return t


def tx(frac):
    return TX0 + (TX1 - TX0) * frac


def plan(n_beats):
    cx, cz = (BX0 + BX1) / 2, (BZ0 + BZ1) / 2
    return [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame((cx, 6.0, cz), 120.0, 0.25, 0.45),
        frame((cx, 4.0, -30.0), 105.0, 0.30, 0.55),
        frame((cx + 10.0, 4.0, -32.0), 100.0, 0.30, 0.50),
        frame((cx, 4.0, -40.0), 125.0, 0.30, 0.55),
    ][:n_beats]


def build():
    n = len(BEATS)
    m, root, b, bk = stage(SLUG, n)
    pts, pk = bk["pts"], b["pk"]
    end = F(n, 0)
    # row 3 open from beat 1 on
    K.row_open(bk, 3, [(F(1, 0), end)])
    K.bl_show(bk, "hi", [(F(1, 0), end)])
    # READ at beat 2, CL fills over the beat, burst at beat 3
    cmd(m, bk, "tl_read", tx(0.08), 2, 0.05, n)
    fill(m, bk["g"], "tl_cl", tx(0.10), tx(0.62), 0.6, TZ, 2, 0.1, 0.9, n - 1, n=12)
    fill(m, bk["g"], "tl_burst", tx(0.63), tx(0.95), 0.6, TZ, 3, 0.0, 0.5, n - 1, n=8, mt="dram_rb_on")
    K.io_flow(m, bk, [3, 4, 5, 6, 7, 8], 3, 0.05, 0.9)
    K.io_flow(m, bk, [4, 5, 6], 4, 0.0, 0.6)

    C.tags(root, {
        0: [("HBM stacks beside the GPU", pk["hbm"]), ("GPU package", pk["top"]), ("one bank drawn on the bench", pts["top"])],
        1: [("row 3 open (earlier ACT)", pts["wl"](3)), ("row buffer holds row 3", pts["rb"](5)),
            ("timeline: one tick per clock", (tx(0.5), 1.0, TZ))],
        2: [("READ: column address in", (tx(0.08), 4.0, TZ)), ("CL: 12 clock blocks", (tx(0.36), 1.5, TZ)),
            ("columns picked in row buffer", pts["rb"](5))],
        3: [("burst: data on the bus", (tx(0.8), 1.5, TZ)), ("words leave row buffer", pts["io"])],
        4: [("CL40 @ DDR5-6400 ~ 12.5 ns", (tx(0.36), 1.5, TZ)), ("bandwidth hides the wait", pts["io"])],
    })
    C.done(SLUG, BEATS, plan(n), root)


if __name__ == "__main__":
    build()
