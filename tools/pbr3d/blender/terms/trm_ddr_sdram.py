"""TRM_DDR_SDRAM: the Terms-tab overview for DDR SDRAM, on a server motherboard.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_ddr_sdram.py

Writes assets/term_TRM_DDR_SDRAM.glb. Captions live in specs/terms/TRM_DDR_SDRAM.json.

A server CPU socket with eight DDR5 DIMMs standing in slots on both sides. One DIMM shows its DRAM
chips, the RCD buffer and the PMIC; on the bench a clock wave carries data beads on both edges and a
cut-open DRAM bank shows the cells inside each chip. Last beat: bars for DDR3 to DDR5 rates.

This file also holds the small server-memory kit (mobo, cpu, dimm, bus, clock) that trm_mrdimm.py
and trm_socamm.py import.

Beats:
  0 server   CPU socket, eight DIMMs, data beads on the channels
  1 dimm     one DIMM: DRAM chips both sides, RCD, PMIC, gold fingers
  2 ddr      the clock wave: one transfer on the rising edge, one on the falling edge
  3 cells    inside a chip: banks of 1T1C cells, a row opens and streams out
  4 gens     DDR3 -> DDR4 -> DDR5 transfer-rate bars
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
from term_common import F  # noqa: E402
from sand_overview import empty  # noqa: E402
from power_vrm_detail import bx, frame, polyline, present, run, rise, blink  # noqa: E402

SLUG = "TRM_DDR_SDRAM"
BEATS = [
    ("Servers keep most of their RAM in DDR5 DIMMs",
     "A server CPU has eight to twelve memory channels, and each channel ends in one or two DIMM slots beside the "
     "socket. Those DIMMs are DDR SDRAM: cheap, dense memory that holds the operating system, the data a job is "
     "working on, and the model weights a CPU or GPU loads next. A two-socket server often carries 1 to 4 TB of it."),
    ("A DIMM is a strip of DRAM chips behind one buffer",
     "A DDR5 RDIMM carries 16 to 40 DRAM chips on both faces. The RCD chip in the middle re-drives the address and "
     "command lines so the CPU sees one load instead of dozens, and a PMIC on the module turns 12 V into the chips' "
     "1.1 V. Data runs straight from the chips to the gold fingers on 2 x 32-bit subchannels."),
    ("Double data rate: data moves on both clock edges",
     "Plain SDRAM sent one word per clock cycle. DDR sends one on the rising edge and one on the falling edge, so "
     "a 3.2 GHz clock gives 6400 million transfers per second (MT/s). At 6400 MT/s a 64-bit channel moves about "
     "51 GB/s."),
    ("Inside each chip: banks of one-transistor, one-capacitor cells",
     "Every bit is a charge on a tiny capacitor, switched by one transistor. A row is opened into the sense amps, "
     "then columns stream out to the pins. The charge leaks, so every row is refreshed every 32 ms or so, and that "
     "is why it is called dynamic RAM."),
    ("Each generation raises the rate and drops the voltage",
     "DDR3 topped out near 2133 MT/s at 1.5 V, DDR4 at 3200 MT/s at 1.2 V, and DDR5 starts at 4800 and is shipping "
     "6400-8000 MT/s at 1.1 V. CPUs and modules must match generation, so each change drives a server refresh cycle. "
     "AI GPUs use stacked HBM instead for bandwidth, while servers fill capacity with DDR5. Related: Micron (MU), "
     "Samsung (005930.KS), SK hynix (000660.KS), AMD (AMD)."),
]

CPU = (-50.0, 0.0, -50.0)
LEFT = [-118.0, -110.0, -102.0, -94.0]
RIGHT = [-6.0, 2.0, 10.0, 18.0]
DZ0, DZ1 = -100.0, 0.0


# ---- server memory kit ---------------------------------------------------------------------
def mobo(m, root, x0=-150.0, x1=50.0, z0=-120.0, z1=20.0):
    C.pcb(m, root, "mobo", x0, x1, z0, z1)
    for k, z in enumerate((-110.0, 10.0)):  # standoffs
        for j, x in enumerate((x0 + 6, x1 - 6)):
            bx(f"mobo_so{k}{j}", (x - 2, 0.0, z - 2), (x + 2, 0.4, z + 2), m["gold"], root)


def cpu(m, root, c=CPU, s=44.0, hot=None):
    """Socket, substrate and heat spreader. Returns the top centre."""
    x, y, z = c
    g = empty("cpu", root)
    bx("cpu_sock", (x - s / 2 - 4, 0.0, z - s / 2 - 4), (x + s / 2 + 4, 2.0, z + s / 2 + 4), m["plastic"], g)
    bx("cpu_sub", (x - s / 2, 2.0, z - s / 2), (x + s / 2, 3.4, z + s / 2), m["substrate"], g)
    bx("cpu_ihs", (x - s / 2 + 3, 3.4, z - s / 2 + 3), (x + s / 2 - 3, 6.4, z + s / 2 - 3), m["alu"], g)
    for k in range(6):  # memory-controller pads along both sides
        zz = z - s / 2 + 5 + k * (s - 10) / 5
        for side in (-1, 1):
            bx(f"cpu_mc{side}{k}", (x + side * (s / 2 - 1.5) - 1, 3.4, zz - 1.5), (x + side * (s / 2 - 1.5) + 1, 3.6, zz + 1.5), m["gold"], g)
    if hot is not None:
        rise(root, "cpu_heat", (x, 7.0, z), 8, 0.9, m["h_amber"], hot, h=26.0, spread=(14.0, 14.0))
    return (x, 6.4, z)


def dimm(m, parent, name, x, z0=DZ0, z1=DZ1, chips=10, h=31.0, buf="rcd", rows=1, chip_mt="mold"):
    """A DIMM standing in its slot in the y-z plane at x. Chips on both faces (rows of them), a
    buffer in the middle, a PMIC at one end. Returns dict of points."""
    g = empty(name, parent)
    bx(f"{name}_slot", (x - 3, 0.0, z0 - 3), (x + 3, 6.0, z1 + 3), m["dark"], g)
    for zz in (z0 - 3, z1 + 1):  # latches
        bx(f"{name}_latch{zz:.0f}", (x - 3.4, 0.0, zz), (x + 3.4, 9.0, zz + 2), m["white"], g)
    bx(f"{name}_pcb", (x - 0.6, 5.0, z0), (x + 0.6, 5.0 + h, z1), m["mask"], g)
    bx(f"{name}_gold", (x - 0.65, 5.0, z0 + 1), (x + 0.65, 7.0, z1 - 1), m["gold"], g)
    mid = (z0 + z1) / 2
    cw = (z1 - z0 - 14.0) / chips
    pts = {"top": (x, 5.0 + h, mid), "chips": [], "buf": None, "pmic": None, "gold": (x, 6.0, mid)}
    for r in range(rows):
        y0 = 9.0 + r * (h - 6.0) / rows
        y1 = y0 + (h - 6.0) / rows - 2.0
        for i in range(chips):
            za = z0 + 3 + i * cw + (cw if i >= chips // 2 else 0) + (8.0 - cw if i >= chips // 2 else 0)
            for side in (-1, 1):
                bx(f"{name}_c{r}{i}{side}", (x + side * 0.6, y0, za + 0.6), (x + side * 1.8, y1, za + cw - 0.6), m[chip_mt], g)
            pts["chips"].append((x + 1.8, (y0 + y1) / 2, za + cw / 2))
    if buf:
        bx(f"{name}_buf", (x + 0.6, 12.0, mid - 3.5), (x + 2.2, 22.0, mid + 3.5), m["driver"], g)
        pts["buf"] = (x + 2.2, 17.0, mid)
    bx(f"{name}_pmic", (x + 0.6, h - 1.0, z0 + 1), (x + 1.8, h + 3.0, z0 + 3.5), m["fet"], g)
    pts["pmic"] = (x + 1.8, h + 1.0, z0 + 2)
    return g, pts


def bus(m, root, name, xs, c=CPU, s=44.0, lanes=(-30.0, -10.0)):
    """Board traces from each DIMM slot to the CPU edge. Returns the bead paths (DIMM -> CPU)."""
    paths = []
    for i, x in enumerate(xs):
        for j, dz in enumerate(lanes):
            z = c[2] + dz + 2.0 * i
            ex = c[0] + (s / 2 + 4) * (1 if x > c[0] else -1)
            p = [(x, 0.3, z + 25.0), (x, 0.3, z), (ex, 0.3, z)]
            C.trace(m, root, f"{name}{i}{j}", [(a, 0.0, b) for a, _, b in p], w=0.8)
            paths.append([(x, 6.0, z + 25.0)] + p)
    return paths


def clock(m, parent, name, x0, x1, y, z, cycles=4, amp=5.0):
    """A square clock wave on a dark plate. Returns (rising, falling) edge points."""
    bx(f"{name}_plate", (x0 - 4, y - amp - 3, z - 1.0), (x1 + 4, y + amp + 3, z - 0.4), m["dark"], parent)
    step = (x1 - x0) / cycles
    pts, rise_p, fall_p = [], [], []
    for k in range(cycles):
        a = x0 + k * step
        pts += [(a, y - amp, z), (a, y + amp, z), (a + step / 2, y + amp, z), (a + step / 2, y - amp, z)]
        rise_p.append((a, y, z + 0.6))
        fall_p.append((a + step / 2, y, z + 0.6))
    pts.append((x1, y - amp, z))
    polyline(f"{name}_wave", pts, 0.35, m["sig"], parent)
    return pts, rise_p, fall_p


def bar(m, parent, name, x, z, w, hgt, mt, beat, until=None):
    """A bar that grows up from the bench in beat `beat` (rendered as stacked blocks)."""
    g = empty(name, parent)
    n = 8
    for k in range(n):
        blk = empty(f"{name}_b{k}", g)
        bx(f"{name}_k{k}", (x - w / 2, k * hgt / n, z - w / 2), (x + w / 2, (k + 0.9) * hgt / n, z + w / 2), m[mt], blk)
        present(blk, [(F(beat, 0.1 + 0.5 * k / n), F(until or beat + 1, 0))])
    return (x, hgt, z)


# ---- the DDR SDRAM scene -------------------------------------------------------------------
def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    mobo(m, root, x1=180.0)
    cpu(m, root, hot=[0, 2])
    dp = {}
    for i, x in enumerate(LEFT + RIGHT):
        _, dp[i] = dimm(m, root, f"d{i}", x, chips=8)
    paths = bus(m, root, "busL", LEFT) + bus(m, root, "busR", RIGHT)
    for k, p in enumerate(paths):
        run(root, f"rd{k}", p, 3, 0.8, m["dram_bead"], [0, 2], 0.0, 0.8, 40)
    d = dp[7]
    # beat 1: the front DIMM's chips light one after another
    for k, c in enumerate(d["chips"][:8]):
        gl = empty(f"chipglow{k}", root)
        bx(f"chipglow{k}_b", (c[0], c[1] - 3, c[2] - 3), (c[0] + 0.3, c[1] + 3, c[2] + 3), m["bit"], gl)
        blink(gl, 1, [k], n=8, on=1.0, u0=0.1, u1=0.9)
    run(root, "cmd", [d["gold"], d["buf"], d["chips"][1]], 4, 0.6, m["e_blue"], 1, 0.1, 0.6, 30)
    run(root, "cmd2", [d["gold"], d["buf"], d["chips"][6]], 4, 0.6, m["e_blue"], 1, 0.15, 0.65, 30)

    # bench: clock wave with transfers on both edges
    bench = empty("bench", root)
    cw, rp, fp = clock(m, bench, "clk", 70.0, 160.0, 22.0, -20.0)
    present(bench, [(F(2, 0), F(3, 0))])
    edges = empty("edges", root)
    for k, p in enumerate(rp + fp):
        bx(f"edge{k}", (p[0] - 1.5, p[1] + 7, p[2] - 0.2), (p[0] + 1.5, p[1] + 10, p[2] + 0.2), m["dram_bead"] if k < 4 else m["h_amber"], edges)
    present(edges, [(F(2, 0.2), F(3, 0))])
    run(root, "clkbead", cw, 2, 1.0, m["bit"], 2, 0.05, 0.4, 70)
    C.trace(m, root, "clkline", [(70.0, 0.0, -20.0), (30.0, 0.0, -20.0)], w=1.0, mt="gold")

    # bench: a cut-open bank (inside one chip)
    BX0, BX1, BZ0, BZ1 = 76.0, 160.0, -100.0, -40.0
    bk = K.bank(m, root, "bank", BX0, BX1, BZ0, BZ1, rows=8, cols=12)
    bp = bk["pts"]
    present(bk["g"], [(F(3, 0), F(4, 0))])
    K.row_open(bk, 4, [(F(3, 0.1), F(4, 0))])
    K.charge_share(m, bk, 4, 3, 0.1, 0.4)
    K.bl_show(bk, "hi", [(F(3, 0.4), F(4, 0))])
    K.io_flow(m, bk, [2, 4, 6, 8, 10], 3, 0.5, 0.9)
    mg = empty("mag_g", root)
    C.magnify(m, mg, d["chips"][5], bp["top"])
    present(mg, [(F(3, 0), F(4, 0))])

    # beat 4: generation bars
    gens = [("DDR3", 2133, "steel"), ("DDR4", 3200, "pcb_blue"), ("DDR5", 6400, "copper"), ("DDR5 OC", 8000, "gold")]
    tops = []
    for k, (nm, rate, mt) in enumerate(gens):
        tops.append(bar(m, root, f"gen{k}", 85.0 + k * 22.0, -60.0, 12.0, rate / 160.0, mt, 4))

    C.tags(root, {
        0: [("CPU socket, 8 memory channels", (CPU[0], 6.4, CPU[2])), ("DDR5 DIMMs in slots", dp[0]["top"]),
            ("data to the memory controller", paths[9][2])],
        1: [("DRAM chips on both faces", d["chips"][2]), ("RCD: buffers address/command", d["buf"]),
            ("PMIC: 12 V to 1.1 V", d["pmic"]), ("gold fingers: 2 x 32-bit", d["gold"])],
        2: [("rising edge: transfer 1", (rp[1][0], 33.0, rp[1][2])), ("falling edge: transfer 2", (fp[2][0], 33.0, fp[2][2])),
            ("3.2 GHz clock = 6400 MT/s", (115.0, 12.0, -20.0))],
        3: [("a bank: grid of 1T1C cells", bp["top"]), ("row opens into sense amps", bp["sa"](6)),
            ("columns stream to the pins", bp["io"]), ("refresh every ~32 ms", bp["cell"](1, 2))],
        4: [("DDR3 2133 MT/s, 1.5 V", tops[0]), ("DDR4 3200 MT/s, 1.2 V", tops[1]),
            ("DDR5 6400 MT/s, 1.1 V", tops[2]), ("8000 MT/s shipping", tops[3])],
    })
    C.done(SLUG, BEATS, [
        frame((-50.0, 8.0, -50.0), 200.0, 0.30, 0.65),
        frame((18.0, 18.0, -50.0), 110.0, 0.55, 0.25),
        frame((100.0, 18.0, -30.0), 120.0, 0.10, 0.20),
        frame((118.0, 4.0, -70.0), 100.0, 0.25, 0.55),
        frame((118.0, 25.0, -60.0), 110.0, 0.20, 0.30),
    ], root)


if __name__ == "__main__":
    build()
