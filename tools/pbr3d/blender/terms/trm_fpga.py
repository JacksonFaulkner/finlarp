"""TRM_FPGA: the Terms-tab overview for an FPGA (field-programmable gate array).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_fpga.py

The shared GPU board, with an FPGA drawn huge on the BENCH strip, lid off and front edge cut:
a fabric of logic tiles (LUT + flip-flops) with a switch box at every crossing, DSP and block-RAM
columns through it, SerDes transceivers along the front, a config flash chip behind it.

Beats:
  0 board     an FPGA on a network card beside the GPU
  1 fabric    the die: logic tiles, switch boxes, DSP and BRAM columns, transceivers
  2 load      a bitstream streams in from flash and sets every tile and switch
  3 rewire    load a different file: the same silicon becomes a different circuit
  4 where     uses, trade-offs and tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, blink, mat  # noqa: E402

SLUG = "TRM_FPGA"
BEATS = [
    ("An FPGA is a chip whose circuit is loaded after it is made",
     "A field-programmable gate array ships blank: its logic and wiring are set by a configuration file loaded at power-up. "
     "In AI data centres FPGAs turn up on network cards and SmartNICs, in storage and in test gear, and engineers use them "
     "to prototype ASICs before committing to silicon."),
    ("Inside: a sea of small logic tiles joined by programmable switches",
     "The die is a grid of logic tiles, each a few look-up tables (tiny truth-table memories that can act as any small "
     "logic gate) plus flip-flops. At every crossing a switch box decides which wires connect. Columns of DSP blocks do fast "
     "multiplies, block RAM holds data, and high-speed transceivers on the edge carry 100G+ links."),
    ("A bitstream sets every look-up table and every switch",
     "At power-up the FPGA reads a bitstream, tens to hundreds of megabits, from a flash chip. Each bit fills a LUT entry or "
     "opens or closes one routing switch. Once loaded, signals ripple through the configured path in parallel, with "
     "fixed, nanosecond-level latency and no instruction fetch."),
    ("Load another file and the same silicon becomes a different circuit",
     "Reprogram it and the tiles and routes change: a packet filter today, a new protocol or a fixed-up bug tomorrow, in the "
     "field. The price of that flexibility is that programmable wiring is big and slow, so the same design runs maybe 5-10x "
     "slower and uses far more power and area than it would as an ASIC."),
    ("Between a CPU and an ASIC: for networks, trading, prototyping, edge inference",
     "FPGAs win where volumes are too small for an ASIC or the logic must change: network and telecom gear, low-latency "
     "trading, radar and signal processing, ASIC emulation, some inference. Related: AMD (AMD, ex-Xilinx), Intel (INTC) and "
     "the now-standalone Altera, Lattice (LSCC), Microchip (MCHP)."),
]

X0, X1 = 160.0, 242.0
Z0, Z1 = -84.0, 0.0
SY0, SY1 = 0.4, 3.4
DY0, DY1 = 3.4, 7.0
FX0, FX1, FZ0, FZ1 = 166.0, 236.0, -76.0, -14.0
NX, NZ = 10, 8
DSP_COL, BRAM_COL = 3, 7  # tile columns replaced by hard blocks


def mats(m):
    m["clb"] = mat("fp_clb", (0.30, 0.34, 0.50), metal=0.5, rough=0.3)
    m["sw"] = mat("fp_sw", (0.62, 0.64, 0.68), metal=0.9, rough=0.3)
    m["dsp"] = mat("fp_dsp", (0.55, 0.42, 0.20), metal=0.6, rough=0.3)
    m["bram"] = mat("fp_bram", (0.20, 0.40, 0.36), metal=0.5, rough=0.3)
    m["xcvr"] = mat("fp_xcvr", (0.45, 0.22, 0.40), metal=0.5, rough=0.3)
    m["route"] = mat("fp_route", (0.40, 0.42, 0.46), metal=0.8, rough=0.35)
    m["onA"] = mat("fp_onA", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=3.0)
    m["onB"] = mat("fp_onB", (0.85, 0.45, 1.0), emit=(0.80, 0.40, 1.0), strength=3.0)
    m["bitb"] = mat("fp_bit", (1.0, 0.62, 0.18), emit=(1.0, 0.58, 0.15), strength=4.0)
    m["sigb"] = mat("fp_sig", (0.30, 0.65, 1.0), emit=(0.28, 0.62, 1.0), strength=4.0)


def die(m, root):
    g = empty("fpga", root)
    bx("f_sub", (X0 - 6.0, SY0, Z0 - 6.0), (X1 + 6.0, SY1, 0.0), m["substrate"], g)
    bx("f_subcu", (X0 - 6.0, 1.8, Z0 - 6.0), (X1 + 6.0, 2.1, 0.2), m["copper"], g)
    for i in range(19):
        D.tube(f"f_bga{i}", (X0 - 4.0 + 4.6 * i, 0.0, -1.2), (X0 - 4.0 + 4.6 * i, SY0, -1.2), 1.1, m["solder"], g, 10)
    bx("f_si", (X0, DY0, Z0), (X1, DY0 + 2.0, 0.0), m["silicon"], g)
    for k in range(6):
        y = DY0 + 2.0 + k * 0.28
        bx(f"f_m{k}", (X0, y, Z0), (X1, y + 0.14, 0.15), m["copper"], g)
        bx(f"f_d{k}", (X0, y + 0.14, Z0), (X1, y + 0.28, 0.05), m["oxide"], g)
    top = DY1 - 0.2
    bx("f_top", (X0, DY1 - 0.4, Z0), (X1, top, 0.0), m["dark"], g)
    pw, pz = (FX1 - FX0) / NX, (FZ1 - FZ0) / NZ
    tiles, sws, routes = [], [], []
    glowA, glowB = empty("f_A", root), empty("f_B", root)
    rows = [empty(f"f_row{j}", root) for j in range(NZ)]  # config fill, row by row
    patA = lambda i, j: (i + 2 * j) % 3 == 0 or (i == j)
    patB = lambda i, j: (2 * i + j) % 4 == 1 or (i + j == NX - 1)
    for i in range(NX):
        x = FX0 + pw * i
        if i in (DSP_COL, BRAM_COL):
            mt = m["dsp"] if i == DSP_COL else m["bram"]
            for j in range(0, NZ, 2):
                z = FZ0 + pz * j
                bx(f"f_hb{i}_{j}", (x + 0.8, top, z + 0.8), (x + pw - 0.8, top + 1.4, z + 2 * pz - 0.8), mt, g)
            continue
        for j in range(NZ):
            z = FZ0 + pz * j
            # tile: four LUT slices
            for s in range(4):
                sx, sz = s % 2, s // 2
                tiles.append(bx(f"f_t{i}_{j}_{s}", (x + 1.6 + sx * 2.3, top, z + 1.6 + sz * 2.3),
                                (x + 3.5 + sx * 2.3, top + 1.0, z + 3.5 + sz * 2.3), m["clb"], g))
            bx(f"f_rg{i}_{j}", (x + 1.8, top + 1.0, z + 1.8), (x + 5.6, top + 1.15, z + 5.6), m["onA"], rows[j])
            if patA(i, j):
                bx(f"f_ga{i}_{j}", (x + 1.4, top + 1.05, z + 1.4), (x + 5.9, top + 1.25, z + 5.9), m["onA"], glowA)
            if patB(i, j):
                bx(f"f_gb{i}_{j}", (x + 1.4, top + 1.05, z + 1.4), (x + 5.9, top + 1.25, z + 5.9), m["onB"], glowB)
    # routing channels and switch boxes at every crossing
    for i in range(NX + 1):
        x = FX0 + pw * i
        routes.append(bx(f"f_rz{i}", (x - 0.35, top, FZ0), (x + 0.35, top + 0.4, FZ1), m["route"], g))
    for j in range(NZ + 1):
        z = FZ0 + pz * j
        routes.append(bx(f"f_rx{j}", (FX0, top, z - 0.35), (FX1, top + 0.4, z + 0.35), m["route"], g))
        for i in range(NX + 1):
            x = FX0 + pw * i
            sws.append(bx(f"f_sw{i}_{j}", (x - 0.8, top, z - 0.8), (x + 0.8, top + 0.8, z + 0.8), m["sw"], g))
    D.join(tiles, "f_tiles")
    D.join(routes, "f_routes")
    D.join(sws, "f_sws")
    for o in [glowA, glowB] + rows:
        show(o, [])
    # transceivers along the front, config flash behind
    for k in range(9):
        x = X0 + 3.0 + k * 8.8
        bx(f"f_x{k}", (x, top, -10.0), (x + 7.0, top + 0.9, -2.5), m["xcvr"], g)
    fl = C.chip(m, root, "f_flash", (200.0, 0.0, -104.0), 20.0, 10.0, h=2.0, pins=6)
    pts = {"die": ((X0 + X1) / 2, top + 1.2, -45.0), "tile": (FX0 + pw * 1.5, top + 1.2, FZ0 + pz * 2.5),
           "sw": (FX0 + pw * 5, top + 0.8, FZ0 + pz * 4), "dsp": (FX0 + pw * (DSP_COL + 0.5), top + 1.4, -40.0),
           "bram": (FX0 + pw * (BRAM_COL + 0.5), top + 1.4, -60.0), "x": (200.0, top + 1.0, -5.0), "flash": fl,
           "cut": (X0 + 6.0, DY0 + 2.8, 0.0), "top": top, "pw": pw, "pz": pz}
    return pts, glowA, glowB, rows


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk, ph = b["pk"], b["ph"]
    fp, gA, gB, rows = die(m, root)
    top, pw, pz = fp["top"], fp["pw"], fp["pz"]
    C.magnify(m, root, (100.0, 0.0, -150.0), (X0 - 6.0, 10.0, -50.0), r=6.0)

    # beat 0: link traffic in and out the transceivers
    run(root, "net", [(200.0, 1.0, 20.0), (200.0, top + 1.5, -5.0)], 6, 0.8, m["sigb"], [0, 4], 0.1, 0.9, 30)
    # beat 2: bitstream from flash; tiles fill row by row, back to front
    for k in range(6):
        x = 170.0 + k * 12.0
        run(root, f"bits{k}", [(200.0, 2.5, -104.0), (200.0, 3.0, -92.0), (x, top + 1.6, Z0 + 2.0), (x, top + 1.6, FZ1)],
            5, 0.55, m["bitb"], [2, 3], 0.0 + 0.02 * k, 0.45, 40)
    for j, r in enumerate(rows):
        show(r, [(F(2, 0.08 + 0.05 * j), F(2, 0.55)), (F(3, 0.05 + 0.04 * j), F(3, 0.45))])
    show(gA, [(F(2, 0.55), F(3, 0.0)), (F(4, 0.0), F(4, 0.5))])
    show(gB, [(F(3, 0.45), F(4, 0.0)), (F(4, 0.5), F(5, 0.0))])
    # signals ripple through the configured path (A in beat 2, B in beat 3)
    pathA = [(FX0, top + 1.6, FZ0 + pz * 0.5)] + [(FX0 + pw * (i + 0.5), top + 1.6, FZ0 + pz * (min(i, NZ - 1) + 0.5)) for i in range(NX)]
    pathB = [(FX0 + pw * (i + 0.5), top + 1.6, FZ0 + pz * (NX - 1 - i + 0.5 if NX - 1 - i < NZ else NZ - 0.5)) for i in range(NX)]
    run(root, "sigA", pathA + [(FX1, top + 1.6, -6.0)], 6, 0.7, m["sigb"], [2], 0.6, 0.95, 30)
    run(root, "sigB", pathB + [(FX1, top + 1.6, -6.0)], 6, 0.7, m["onB"], [3], 0.55, 0.95, 30)
    blink(gB, 4, [5, 7], n=8, on=0.6)

    C.tags(root, {
        0: [("GPU package", pk["top"]), ("FPGA on a network card", fp["die"]), ("VRM phases", ph["ind"][(-1, 3)]["top"])],
        1: [("logic tile: LUTs + flip-flops", fp["tile"]), ("switch box at each crossing", fp["sw"]),
            ("DSP column", fp["dsp"]), ("block RAM column", fp["bram"]), ("100G+ transceivers", fp["x"])],
        2: [("bitstream from flash", fp["flash"]), ("each bit sets a LUT or switch", fp["sw"]),
            ("signal takes the set path", fp["tile"])],
        3: [("new file, new circuit", fp["die"]), ("same silicon, rewired", fp["sw"]), ("~5-10x slower than ASIC", fp["x"])],
        4: [("networks, trading, prototyping", fp["die"]), ("AMD (Xilinx), Altera, INTC", fp["dsp"]),
            ("Lattice LSCC, Microchip MCHP", fp["x"])],
    })
    cx = (X0 + X1) / 2
    C.done(SLUG, BEATS, [
        frame((50.0, 0.0, -80.0), 400.0, 0.30, 0.65, pad=1.0),
        frame((cx, top, -45.0), 100.0, 0.18, 0.80),
        frame((cx, top, -60.0), 120.0, 0.25, 0.70),
        frame((cx, top, -45.0), 95.0, -0.15, 0.85),
        frame((cx, top, -50.0), 125.0, 0.35, 0.45),
    ], root)


if __name__ == "__main__":
    build()
