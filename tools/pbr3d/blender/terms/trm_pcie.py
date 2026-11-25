"""TRM_PCIE: the Terms-tab overview for PCI Express, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_pcie.py

Writes assets/term_TRM_PCIE.glb and specs/terms/TRM_PCIE.json.

The GPU board with a PCIe switch chip and two x16 slots near its right edge: trace bundles run from
the GPU package to the switch and on to the slots. On the bench a slot is blown up with its card
standing in it, one transmit and one receive pair per lane. Speed bars show Gen5/6/7.

Beats:
  0 board   PCIe x16 links from the GPU package through a switch to two slots
  1 lanes   one lane = a TX pair and an RX pair; x16 bundles sixteen of them
  2 packets data moves as packets (TLPs) both ways at once
  3 speed   Gen5 32, Gen6 64, Gen7 128 GT/s per lane
  4 fanout  the switch fans the CPU's lanes out to GPUs, NICs and SSDs
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from sand_overview import F, show, empty  # noqa: E402
from power_vrm_detail import run, frame, bx, polyline, blink  # noqa: E402

import term_common as C  # noqa: E402
import kit_link as K  # noqa: E402

SLUG = "TRM_PCIE"
BEATS = [
    ("PCIe is the bus that wires a server's CPU to its GPUs, NICs and SSDs",
     "PCI Express is a point-to-point serial link, not a shared bus. Every GPU, network card and SSD in an AI "
     "server hangs off the host through a PCIe link, usually sixteen lanes wide (x16). On this board the GPU's "
     "links run out to a PCIe switch and on to two x16 slots."),
    ("One lane is two differential pairs: one to send, one to receive",
     "Each lane has its own transmit pair and receive pair, so both directions run at full speed at the same "
     "time. A link bundles 1, 4, 8 or 16 lanes, and bandwidth scales with the count. The gold fingers on a "
     "card edge are just those pairs plus power and ground."),
    ("Data moves as small packets, both ways at once",
     "The protocol wraps reads, writes and completions into transaction-layer packets (TLPs) with a header, "
     "payload and CRC. A bad packet is simply resent by the link layer. A GPU pulling weights from host "
     "memory and a NIC pushing data into GPU memory both look like streams of these packets."),
    ("Each generation doubles the lane rate: 32, 64, 128 GT/s",
     "Gen5 runs 32 GT/s per lane, about 64 GB/s each way on x16. Gen6 doubles that to 64 GT/s using PAM4 "
     "signalling and FLIT framing, and Gen7 targets 128 GT/s. Faster lanes reach a shorter distance over "
     "board copper, which is why each step adds retimers."),
    ("Switches fan the host's lanes out to many devices",
     "A CPU has a limited number of lanes, so AI servers use PCIe switches to fan them out to eight GPUs, "
     "their NICs and NVMe drives, and to let GPUs and NICs talk directly. Speed upgrades drive sales of "
     "switches and retimers. Related: Astera Labs (ALAB), Broadcom (AVGO), Marvell (MRVL), Intel (INTC), AMD (AMD)."),
]

SW = (200.0, 0.0, -105.0)  # PCIe switch on the board
SLOT_X = (160.0, 240.0)
SLOT_Z = (-150.0, -185.0)
BENCH_X = (156.0, 244.0)
BENCH_Z = -40.0  # bench slot centre line (z)


def bundle(m, parent, name, pts, n=4, gap=2.4, mt="copper"):
    """n parallel flat traces following the polyline pts (offset sideways in z/x by gap)."""
    g = empty(name, parent)
    for i in range(n):
        off = (i - (n - 1) / 2) * gap
        p = [(x + off * 0.5, y, z + off) for (x, y, z) in pts]
        polyline(f"{name}{i}", p, 0.35, m[mt], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    b = C.base(m, root)
    pk = b["pk"]

    # board: switch chip, two slots with cards, trace bundles
    sw = K.retimer(m, root, "sw", SW, w=26.0, d=26.0, h=3.2)
    slots = []
    for k, z in enumerate(SLOT_Z):
        s = K.pcie_slot(m, root, f"slot{k}", SLOT_X[0], SLOT_X[1], z)
        K.pcie_card(m, root, f"card{k}", SLOT_X[0] + 4.0, SLOT_X[1] - 4.0, z, h=26.0)
        slots.append(s)
    up = [(60.0, 0.4, -40.0), (150.0, 0.4, -70.0), (186.0, 0.4, -100.0)]
    bundle(m, root, "bup", up)
    for k, z in enumerate(SLOT_Z):
        bundle(m, root, f"bdn{k}", [(SW[0], 0.4, SW[2] - 14.0), (SW[0] - 10.0 * k, 0.4, z + 6.0)], n=4)

    # bench: big slot with its card, TX and RX pairs per lane
    bench = empty("bench", root)
    sl = K.pcie_slot(m, bench, "bslot", BENCH_X[0], BENCH_X[1], BENCH_Z, lanes=16)
    K.pcie_card(m, bench, "bcard", BENCH_X[0] + 2.0, BENCH_X[1] - 2.0, BENCH_Z, h=40.0)
    chipc = ((BENCH_X[0] + BENCH_X[1]) / 2, 34.0, BENCH_Z + 2.8)
    bx("bchip", (chipc[0] - 12, 26.0, BENCH_Z + 0.8), (chipc[0] + 12, 42.0, BENCH_Z + 2.6), m["lnk_pkg"], bench)
    tx, rx = [], []
    for i, (lx, ly, lz) in enumerate(sl["lanes"]):
        for s, lst in ((-0.7, tx), (0.7, rx)):
            p = [(lx + s, 6.6, lz + 1.2), (lx + s, 16.0, lz + 1.2), (chipc[0] + (lx - chipc[0]) * 0.4 + s, 26.0, lz + 1.2)]
            polyline(f"bl{i}{s}", p, 0.18, m["copper"], bench)
            lst.append(p)
    show(bench, [(F(1, 0.0), F(3, 0))])

    # gen bars
    bars = K.speed_bars(m, root, "bars", (-160.0, 0.0, -30.0), rates=(32, 64, 128), x_gap=24.0, scale=0.4)
    show(bars["group"], [(F(3, 0.0), F(4, 0))])

    # beat 0: traffic on the board
    run(root, "b0a", up + [(SW[0], 1.0, SW[2])], 8, 0.9, m["bit"], [0, 4], 0.05, 0.85, 50)
    for k, z in enumerate(SLOT_Z):
        run(root, f"b0s{k}", [(SW[0], 1.0, SW[2] - 14.0), (SW[0] - 10.0 * k, 1.0, z + 6.0), (SW[0] - 10.0 * k, 14.0, z)],
            6, 0.9, m["sig"], [0, 4], 0.1 + 0.1 * k, 0.9, 40)
    # beat 1: every lane carries a TX and an RX stream
    for i in range(0, 16, 3):
        run(root, f"tx{i}", tx[i][::-1], 2, 0.45, m["sig"], [1, 2], 0.05, 0.6, 30)
        run(root, f"rx{i}", rx[i], 2, 0.45, m["e_blue"], [1, 2], 0.3, 0.9, 30)
    # beat 2: packets: header + payload + crc bricks sliding along a lane
    lane_a = [(BENCH_X[0] - 40.0, 52.0, BENCH_Z), (BENCH_X[1] + 6.0, 52.0, BENCH_Z)]
    lane_b = [(BENCH_X[1] + 6.0, 58.0, BENCH_Z), (BENCH_X[0] - 40.0, 58.0, BENCH_Z)]
    lg = empty("lanes_ab", root)
    polyline("lnA", lane_a, 0.2, m["dim_glow"], lg)
    polyline("lnB", lane_b, 0.2, m["dim_glow"], lg)
    show(lg, [(F(2, 0.0), F(3, 0))])
    for k, (mt, n, d) in enumerate((("h_amber", 3, 0.0), ("bit", 3, 0.03), ("bit", 3, 0.06), ("warn", 3, 0.09))):
        run(root, f"tA{k}", lane_a, n, 1.1, m[mt], 2, 0.05 + d, 0.65 + d, 70)
        run(root, f"tB{k}", lane_b, n, 1.1, m[mt], 2, 0.15 + d, 0.75 + d, 70)
    # beat 3: the bars' tops blink
    for i, t in enumerate(bars["tops"]):
        g = empty(f"bt{i}", root)
        bx(f"bt{i}_b", (t[0] - 3.0, t[1], t[2] - 3.0), (t[0] + 3.0, t[1] + 1.0, t[2] + 3.0), m["sig"], g)
        blink(g, 3, [i], n=3, on=0.9)

    C.tags(root, {
        0: [("GPU package", pk["top"]), ("PCIe switch", sw["top"]), ("x16 slots", (200.0, 30.0, -168.0)),
            ("x16 trace bundle", (150.0, 2.0, -70.0))],
        1: [("gold fingers: one pair each", (BENCH_X[0] + 10.0, 6.6, BENCH_Z)), ("TX pair (send)", tx[1][1]),
            ("RX pair (receive)", rx[13][1]), ("x16 = 16 lanes", (chipc[0], 44.0, BENCH_Z))],
        2: [("TLP: header, payload, CRC", (BENCH_X[0] + 10.0, 62.0, BENCH_Z)), ("bad CRC = resend", (BENCH_X[1] - 10.0, 62.0, BENCH_Z)),
            ("both directions at once", (chipc[0], 20.0, BENCH_Z))],
        3: [("Gen5 32 GT/s", bars["tops"][0]), ("Gen6 64 GT/s", bars["tops"][1]), ("Gen7 128 GT/s", bars["tops"][2])],
        4: [("switch fans out lanes", sw["top"]), ("GPU / NIC / SSD slots", (200.0, 30.0, -168.0)),
            ("host lanes in", (110.0, 2.0, -55.0))],
    })
    C.done(SLUG, BEATS, [
        frame((110.0, 0.0, -100.0), 320.0, 0.35, 0.70, pad=1.0),
        frame((200.0, 20.0, BENCH_Z), 110.0, 0.25, 0.25),
        frame((190.0, 40.0, BENCH_Z), 130.0, 0.15, 0.20),
        frame((-130.0, 25.0, -30.0), 100.0, 0.30, 0.25),
        frame((150.0, 5.0, -120.0), 220.0, 0.40, 0.70),
    ], root)


if __name__ == "__main__":
    build()
