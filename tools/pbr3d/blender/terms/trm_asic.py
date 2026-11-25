"""TRM_ASIC: the Terms-tab overview for an ASIC (custom AI accelerator / XPU).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_asic.py

The shared GPU board carries the package; on the BENCH strip a custom accelerator die is drawn
huge, lid off, front edge cut: a big systolic MAC array in the middle, SRAM banks down both
sides, HBM PHYs and two HBM stacks along the back, SerDes lanes along the front, metal stack in
the cut face.

Beats:
  0 board     the GPU board; the custom chip is a drop-in for the merchant GPU
  1 floorplan the giant die: fixed blocks, no general cores
  2 dataflow  weights flow down, activations flow across, a wave of MACs fires
  3 watts     same job, less heat: GPU die vs ASIC die
  4 who       NRE, volume, partners and tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_ASIC"
BEATS = [
    ("An ASIC is a chip built for one job, here a custom AI accelerator",
     "An application-specific integrated circuit has its logic fixed at design time for one task. In AI the big cloud "
     "companies co-design their own accelerators (Google TPU, Amazon Trainium, Meta MTIA), often called XPUs, and put "
     "them on boards just like this one in place of a merchant GPU."),
    ("Open the die: a giant multiply array, SRAM and memory links, no general cores",
     "Most of the silicon is one big grid of multiply-accumulate units sized for the matrix maths of neural networks. "
     "Banks of on-chip SRAM hold weights and activations next to it, PHYs along the edge talk to stacked HBM, and SerDes "
     "lanes link chip to chip. Anything the target models do not need is simply left out."),
    ("Weights stream down, activations stream across, every cell multiplies and passes on",
     "In a systolic array each cell multiplies the weight it holds by the value arriving from its neighbour, adds it to a "
     "running sum and hands both on, so data flows through the grid like a wave without trips back to memory. A "
     "128x128 array does 16,384 multiply-adds every clock cycle."),
    ("Same model, fewer watts: no silicon spent on what the job never uses",
     "Because the chip skips general-purpose scheduling, graphics leftovers and wide number formats it does not need, a "
     "well-targeted ASIC can deliver more inferences per watt and per dollar than a GPU on its home workload. The catch "
     "is flexibility: if models change shape, a fixed design can age fast."),
    ("Huge up-front cost, paid back only at hyperscaler volume",
     "A leading-edge design costs hundreds of millions of dollars and 2-3 years before the first chip, so ASICs make sense "
     "only when one buyer will deploy hundreds of thousands. Design partners Broadcom (AVGO), Marvell (MRVL) and Alchip "
     "build them for Alphabet (GOOGL), Amazon (AMZN) and others, and TSMC (TSM) makes them."),
]

X0, X1 = 158.0, 242.0  # die x
Z0, Z1 = -84.0, 0.0  # die z (front cut at 0)
SY0, SY1 = 0.4, 3.4  # package substrate
DY0, DY1 = 3.4, 7.0  # die
AX0, AX1, AZ0, AZ1 = 176.0, 224.0, -66.0, -16.0  # MAC array
N = 10  # cells a side


def mats(m):
    m["mac"] = mat("asic_mac", (0.30, 0.34, 0.50), metal=0.5, rough=0.3)
    m["sram"] = mat("asic_sram", (0.20, 0.40, 0.36), metal=0.5, rough=0.3)
    m["phy"] = mat("asic_phy", (0.55, 0.42, 0.20), metal=0.6, rough=0.3)
    m["serdes"] = mat("asic_serdes", (0.45, 0.22, 0.40), metal=0.5, rough=0.3)
    m["ctl"] = mat("asic_ctl", (0.28, 0.28, 0.32), metal=0.5, rough=0.35)
    m["cell_on"] = mat("asic_cell_on", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=3.0)
    m["wt"] = mat("asic_wt", (1.0, 0.62, 0.18), emit=(1.0, 0.58, 0.15), strength=4.0)
    m["act"] = mat("asic_act", (0.30, 0.65, 1.0), emit=(0.28, 0.62, 1.0), strength=4.0)
    m["sram_on"] = mat("asic_sram_on", (0.40, 0.90, 0.80), emit=(0.35, 0.85, 0.75), strength=2.0)
    m["asic_hot"] = mat("asic_hot", (0.55, 0.30, 0.20), emit=(1.0, 0.45, 0.15), strength=0.6)


def die(m, root):
    g = empty("asic", root)
    # substrate with BGA row under the front edge and decaps on the land side
    bx("a_sub", (X0 - 8.0, SY0, Z0 - 8.0), (X1 + 8.0, SY1, 0.0), m["substrate"], g)
    for k, y in enumerate((1.2, 2.2)):
        bx(f"a_subcu{k}", (X0 - 8.0, y, Z0 - 8.0), (X1 + 8.0, y + 0.3, 0.2), m["copper"], g)
    for i in range(22):
        x = X0 - 6.0 + 4.6 * i
        D.tube(f"a_bga{i}", (x, 0.0, -1.2), (x, SY0, -1.2), 1.1, m["solder"], g, 10)
    for i in range(10):
        D.mlcc(m, g, f"a_dc{i}", (X0 - 4.0 + 10.0 * i, SY1, Z0 - 5.0), 3.0, 1.6, 1.4)
    # die body; front face shows the metal stack (silicon, then copper layers, thicker upward)
    bx("a_si", (X0, DY0, Z0), (X1, DY0 + 2.0, 0.0), m["silicon"], g)
    for k in range(6):
        y = DY0 + 2.0 + k * 0.28
        bx(f"a_m{k}", (X0, y, Z0), (X1, y + 0.12 + 0.02 * k, 0.15), m["copper"], g)
        bx(f"a_d{k}", (X0, y + 0.12 + 0.02 * k, Z0), (X1, y + 0.28, 0.05), m["oxide"], g)
    bx("a_top", (X0, DY1 - 0.4, Z0), (X1, DY1 - 0.2, 0.0), m["die"], g)
    top = DY1 - 0.2
    # MAC array tiles
    p = (AX1 - AX0) / N
    cells = []
    for i in range(N):
        for j in range(N):
            x, z = AX0 + p * i, AZ0 + p * j
            cells.append(bx(f"a_c{i}_{j}", (x + 0.35, top, z + 0.35), (x + p - 0.35, top + 0.7, z + p - 0.35), m["mac"], g))
    D.join(cells, "a_cells")
    # wave glow: cells grouped by i + j (diagonals) so a front sweeps across the grid
    waves = [empty(f"a_wave{k}", root) for k in range(2 * N - 1)]
    for i in range(N):
        for j in range(N):
            x, z = AX0 + p * i, AZ0 + p * j
            bx(f"a_cg{i}_{j}", (x + 0.6, top + 0.7, z + 0.6), (x + p - 0.6, top + 0.9, z + p - 0.6), m["cell_on"], waves[i + (N - 1 - j)])
    for w in waves:
        show(w, [])
    # SRAM banks both sides, striped
    sram_on = empty("a_sram_on", root)
    for side, (xa, xb) in (("l", (X0 + 3.0, AX0 - 3.0)), ("r", (AX1 + 3.0, X1 - 3.0))):
        for k in range(8):
            z = AZ0 + k * 6.4
            bx(f"a_sr{side}{k}", (xa, top, z), (xb, top + 0.9, z + 5.4), m["sram"], g)
            for s in range(4):
                bx(f"a_srs{side}{k}_{s}", (xa + 0.4, top + 0.9, z + 0.6 + s * 1.2), (xb - 0.4, top + 1.0, z + 1.2 + s * 1.2), m["ctl"], g)
            bx(f"a_srg{side}{k}", (xa + 0.4, top + 1.0, z + 0.4), (xb - 0.4, top + 1.15, z + 5.0), m["sram_on"], sram_on)
    show(sram_on, [])
    # HBM PHYs on the back edge and two HBM stacks behind the die
    for k, (xa, xb) in enumerate(((X0 + 4.0, 196.0), (204.0, X1 - 4.0))):
        bx(f"a_phy{k}", (xa, top, Z0 + 2.0), (xb, top + 0.8, Z0 + 10.0), m["phy"], g)
        for n in range(12):
            y = SY1 + n * 0.75
            bx(f"a_hbm{k}_{n}", (xa + 2.0, y, Z0 - 7.6), (xb - 2.0, y + 0.65, Z0 - 0.8), m["hbm_dram" if n else "hbm"], g)
    # control / scheduler strip and SerDes along the front edge
    bx("a_ctl", (AX0, top, AZ1 + 2.0), (AX1, top + 0.8, AZ1 + 6.0), m["ctl"], g)
    for k in range(10):
        x = X0 + 4.0 + k * 7.8
        bx(f"a_sd{k}", (x, top, -9.0), (x + 6.0, top + 0.8, -2.5), m["serdes"], g)
    hot = empty("a_hot", root)
    bx("a_hotp", (AX0, top + 0.95, AZ0), (AX1, top + 1.05, AZ1), m["asic_hot"], hot)
    show(hot, [])
    pts = {"die": ((X0 + X1) / 2, top, -40.0), "arr": ((AX0 + AX1) / 2, top + 1.0, (AZ0 + AZ1) / 2),
           "sram": (X0 + 8.0, top + 1.0, -40.0), "phy": (185.0, top + 1.0, Z0 + 6.0), "hbm": (225.0, SY1 + 9.0, Z0 - 4.0),
           "sd": (200.0, top + 1.0, -5.0), "cut": (X0 + 10.0, DY0 + 2.8, 0.0), "top": top}
    return pts, waves, sram_on, hot


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk, ph, die_glow = b["pk"], b["ph"], b["die_glow"]
    ap, waves, sram_on, hot = die(m, root)
    C.magnify(m, root, (0.0, D.DIE_Y[1], -17.0), (X0 - 6.0, 10.0, -40.0), r=6.0)
    top = ap["top"]
    p = (AX1 - AX0) / N

    # beat 0: board current into package as context
    for side in (-1, 1):
        run(root, f"pwr{side}", D.front_path(side), 5, 1.0, m["amp"], [0], 0.1, 0.8, 70)

    # beat 1: the blocks light once in turn
    show(sram_on, [(F(1, 0.35), F(1, 0.7)), (F(2, 0.0), F(3, 0.0))])

    # beat 2: systolic wave; weights down columns (z+), activations across rows (x+)
    nw = len(waves)
    for k, w in enumerate(waves):
        iv = []
        for b_ in (2, 3):
            for rep in range(3):
                a = 0.05 + rep * 0.3 + 0.012 * k
                iv.append((F(b_, a), F(b_, a + 0.08)))
        show(w, iv)
    for i in range(0, N, 2):
        x = AX0 + p * (i + 0.5)
        run(root, f"wt{i}", [(x, top + 1.6, Z0 + 10.0), (x, top + 1.6, AZ0), (x, top + 1.6, AZ1)], 4, 0.6, m["wt"], [2], 0.0, 0.8, 50)
    for j in range(0, N, 2):
        z = AZ0 + p * (j + 0.5)
        run(root, f"ac{j}", [(X0 + 6.0, top + 1.6, z), (AX0, top + 1.6, z), (AX1, top + 1.6, z), (X1 - 6.0, top + 1.6, z)],
            4, 0.6, m["act"], [2], 0.05, 0.85, 50)
    run(root, "hbmin", [(185.0, SY1 + 9.0, Z0 - 4.0), (185.0, top + 1.5, Z0 + 6.0), (X0 + 8.0, top + 1.5, -50.0)], 5, 0.8, m["wt"], [1, 2], 0.3, 0.9, 40)
    run(root, "sdout", [(200.0, top + 1.5, -5.0), (200.0, top + 1.5, 4.0), (200.0, 0.6, 12.0)], 5, 0.7, m["act"], [2], 0.2, 0.9, 30)

    # beat 3: heat comparison
    show(die_glow, [(F(3, 0.1), F(4, 0))])
    show(hot, [(F(3, 0.1), F(4, 0))])
    rise(root, "gpu_heat", (0.0, D.DIE_Y[1] + 1.0, -16.0), 10, 1.1, m["heat"], 3, 0.1, 0.9, 40.0, 60, (22.0, 12.0))
    rise(root, "asic_heat", (200.0, top + 1.0, -40.0), 4, 1.0, m["heat"], 3, 0.1, 0.9, 25.0, 60, (18.0, 18.0))

    # beat 4: everything lit together
    for w in waves[::3]:
        blink(w, 4, [0, 2, 4, 6], n=8, on=0.5)

    C.tags(root, {
        0: [("merchant GPU package", pk["top"]), ("custom XPU drops in here", (X0, 12.0, -40.0)),
            ("VRM phases feed it", ph["ind"][(-1, 3)]["top"])],
        1: [("multiply-accumulate array", ap["arr"]), ("on-chip SRAM banks", ap["sram"]),
            ("HBM PHY + stacks", ap["hbm"]), ("chip-to-chip SerDes", ap["sd"]), ("metal stack, cut", ap["cut"])],
        2: [("weights stream down", (AX0 + 4.0, top + 2.0, AZ0 - 4.0)), ("activations stream across", (X0 + 6.0, top + 2.0, -30.0)),
            ("each cell: multiply, add, pass", ap["arr"])],
        3: [("GPU: more watts, same job", pk["top"]), ("ASIC: less heat per answer", ap["arr"]),
            ("no unused silicon", ap["sram"])],
        4: [("$100Ms + 2-3 yrs per design", ap["die"]), ("Broadcom, Marvell, Alchip", ap["sd"]),
            ("TPU, Trainium, MTIA", ap["hbm"]), ("built at TSMC", ap["cut"])],
    })
    cx = (X0 + X1) / 2
    C.done(SLUG, BEATS, [
        frame((50.0, 0.0, -80.0), 400.0, 0.30, 0.65, pad=1.0),
        frame((cx, top, -42.0), 105.0, 0.15, 0.80),
        frame((cx, top, -40.0), 70.0, 0.10, 0.95),
        frame((100.0, 5.0, -40.0), 270.0, 0.15, 0.55, pad=1.0),
        frame((cx, top, -40.0), 110.0, 0.35, 0.45),
    ], root)


if __name__ == "__main__":
    build()
