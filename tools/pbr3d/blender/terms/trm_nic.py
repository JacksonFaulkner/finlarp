"""TRM_NIC: the Terms-tab overview for the network interface card (NIC).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_nic.py

Writes assets/term_TRM_NIC.glb. Captions live in specs/terms/TRM_NIC.json (same beat count).

An 8-GPU node with its lid off (net_server_detail): ten cards on the front edge, eight ConnectX-class
NICs (one per GPU) and two DPUs, each with an OSFP cage, transceiver and fibre up to the leaf switch.
A NIC four times life size sits on the bench to the left: PCIe edge connector, the controller chip
under its finned sink, the OSFP cage. Data leaves GPU memory over PCIe, is cut into packets in the
NIC and goes out on the fibre.

Beats:
  0 node      eight NICs and two DPUs along the front edge, fibres to the leaf
  1 inside    the big NIC: PCIe connector, controller under its sink, OSFP cage
  2 rdma      GPU memory to PCIe switch to NIC to leaf, no CPU in the path
  3 packets   bytes come in on PCIe, packets go out of the cage
  4 attach    one NIC per GPU: attach rate scales with GPUs
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import bx, empty, show, mat  # noqa: E402
from sand_overview import F  # noqa: E402
from power_vrm_detail import frame, run, blink, present, rise  # noqa: E402
import net_server_detail as S  # noqa: E402

SLUG = "TRM_NIC"
BEATS = [
    ("Every GPU in an AI server gets its own network card",
     "A network interface card connects a server to the network. An 8-GPU AI server has eight high-speed NICs along its "
     "front edge, one per GPU, for the back-end (GPU-to-GPU) network, plus one or two DPUs for the front-end and "
     "storage network. Each NIC has an optical transceiver and a fibre running to a leaf switch."),
    ("Inside: a PCIe connector, a packet chip and an optical cage",
     "The card plugs into PCIe on one edge. The controller chip in the middle holds the SerDes, a PCIe interface and "
     "hardware engines for RDMA, congestion control and encryption, under a heatsink because it burns 20-30 W. The other "
     "edge is an OSFP cage that holds the transceiver: 400G or 800G per port today, 1.6T next."),
    ("RDMA: data goes from GPU memory straight onto the wire",
     "With GPUDirect RDMA the NIC reads directly from the GPU's memory through the PCIe switch next to it. The CPU and its "
     "memory are never in the path, which cuts latency and frees the CPU. The far NIC writes the data straight into the "
     "remote GPU's memory the same way."),
    ("It turns bytes in memory into packets on the wire",
     "The NIC slices a buffer into packets, adds headers (addresses, sequence numbers), checksums and sends them through "
     "the SerDes and laser. Incoming packets go the other way: checked, reordered and placed in memory. Doing this in "
     "hardware at 800 Gb/s is what separates AI NICs from ordinary ones."),
    ("Attach rate scales with GPUs, so NICs are a real product line",
     "One back-end NIC per GPU means every GPU shipped pulls a NIC with it, plus transceivers and switch ports. SmartNICs "
     "and DPUs add offload for storage and security. Related: Nvidia ConnectX/BlueField (NVDA), Broadcom Thor (AVGO), "
     "AMD Pensando (AMD), Marvell (MRVL), Intel (INTC)."),
]

BIG_X, BIG_S = -470.0, 4.0


def big_nic(m, root):
    """The bench NIC, cut open: PCB (fingers at the back, z -200), substrate + bare controller die
    ringed by SerDes and PCIe blocks, the heatsink lifted and ghosted above it, DDR-less traces to an
    OSFP cage at the front whose side and top are cut away to show the transceiver inside."""
    g = empty("big", root)
    x = BIG_X
    gold = mat("nic_gold", (0.95, 0.75, 0.30), metal=1.0, rough=0.25)
    serd = mat("nic_serdes", (0.20, 0.45, 0.60), metal=0.5, rough=0.3)
    pcie = mat("nic_pcie", (0.60, 0.42, 0.20), metal=0.5, rough=0.3)
    eng = mat("nic_eng", (0.30, 0.25, 0.50), metal=0.4, rough=0.3)
    ghost = mat("nic_ghost", (0.55, 0.58, 0.62), metal=0.6, rough=0.4)
    bx("pcb", (x - 70, 0, -200), (x + 70, 5, 20), m["pcb_nic"], g)
    for i in range(14):  # edge fingers on the back edge
        xx = x - 62 + 9 * i
        bx(f"fing{i}", (xx, 4.9, -200), (xx + 5, 5.6, -178), gold, g)
    bx("brkt", (x - 72, 0, 20), (x + 72, 4, 24), m["alu"], g)  # front bracket, cut down
    # controller: substrate, die, functional blocks
    bx("sub", (x - 36, 5, -126), (x + 36, 9, -54), m["sub"], g)
    bx("die", (x - 24, 9, -114), (x + 24, 12, -66), m["die"], g)
    for i in range(6):
        bx(f"sd_r{i}", (x + 16, 12, -112 + 7.5 * i), (x + 22, 13.5, -106 + 7.5 * i), serd, g)
    bx("pcie_blk", (x - 22, 12, -114), (x + 14, 13.5, -106), pcie, g)
    for i in range(2):
        for j in range(3):
            bx(f"eng{i}{j}", (x - 22 + 12 * j, 12, -102 + 14 * i), (x - 12 + 12 * j, 13.2, -91 + 14 * i), eng, g)
    for i in range(10):  # PCIe traces fingers -> die
        xx = x - 45 + 10 * i
        bx(f"ptr{i}", (xx, 5, -178), (xx + 1.4, 5.3, -126), m["trace"], g)
    for i in range(4):  # SerDes traces die -> cage
        xx = x + 6 + 6 * i
        bx(f"str{i}", (xx, 5, -54), (xx + 1.4, 5.3, -40), m["trace"], g)
    # heatsink lifted above the die, ghosted
    hs = empty("hs", g)
    bx("hs_b", (x - 36, 44, -126), (x + 36, 47, -54), ghost, hs)
    for i in range(9):
        bx(f"hs_f{i}", (x - 34 + 8 * i, 47, -126), (x - 31 + 8 * i, 66, -54), ghost, hs)
    for sx in (-30, 30):
        bx(f"hs_post{sx}", (x + sx - 1, 9, -60), (x + sx + 1, 44, -58), m["alu"], g)
    # OSFP cage: floor, back wall, far side only (near side + top cut away), transceiver inside
    cx0, cx1 = x - 4, x + 50
    bx("cg_floor", (cx0, 5, -40), (cx1, 6, 20), m["alu"], g)
    bx("cg_side", (cx1, 5, -40), (cx1 + 2, 38, 20), m["alu"], g)
    bx("cg_back", (cx0, 5, -42), (cx1, 38, -40), m["alu"], g)
    bx("cg_lip", (cx0, 36, -40), (cx1, 38, -30), m["alu"], g)
    bx("xc_pcb", (cx0 + 6, 9, -34), (cx1 - 6, 11, 18), m["pcb_nic"], g)
    bx("xc_edge", (cx0 + 6, 9, -38), (cx1 - 6, 11.6, -32), gold, g)
    bx("xc_dsp", (cx0 + 14, 11, -24), (cx1 - 14, 15, -12), m["chip"], g)
    leds = []
    lg = empty("big_las", g)
    for k in range(4):
        xx = cx0 + 12 + 8 * k
        bx(f"las{k}", (xx, 11, 2), (xx + 3, 14, 6), m["pkt"], lg)
        bx(f"wg{k}", (xx + 1, 11, 6), (xx + 2, 12, 20), m["fiber_aqua"], g)
    leds.append(lg)
    pt = {"fingers": (x, 6.0, -190.0), "die": (x, 13.5, -90.0), "serdes": (x + 19, 13.5, -95.0),
          "hs": (x, 66.0, -90.0), "dsp": ((cx0 + cx1) / 2, 15.0, -18.0), "las": ((cx0 + cx1) / 2, 14.0, 4.0),
          "port": ((cx0 + cx1) / 2, 13.0, 20.0), "pcie": (x - 4, 13.5, -110.0)}
    return leds, pt


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m.update(S.materials())
    s = S.scene(m, root, cut=False, rails=False, out=True)
    present(s["fe"], [])
    present(s["leaf"], [(F(0, 0.0), F(1, 0)), (F(4, 0.0), F(5, 0))])
    bench = empty("bench", root)
    bx("bench_top", (BIG_X - 110.0, -6.0, -260.0), (BIG_X + 110.0, 0.0, 90.0), m["floor"], bench)
    z1 = S.NIC_Z[1]
    leds, pt = big_nic(m, root)
    conn, chip, port = pt["fingers"], pt["die"], pt["port"]
    for gl in s["glow"]:
        show(gl, [(F(2, 0.0), F(3, 0))])

    # beat 0: a trickle up every fibre
    for i, nx in enumerate(S.NIC_X):
        run(root, f"cab{i}", [(p[0], p[1] + 2.0, p[2]) for p in S.cable_path(nx, S.leaf_x(i))], 2, 3.0, m["pkt"], [0, 4], 0.1 + 0.05 * i, 0.8, 40)
    # beat 1: the big card's parts light in turn
    for i, l in enumerate(leds + s["leds"]):
        blink(l, 1, [i % 8, (i + 4) % 8], n=8, on=0.5)
    rise(root, "big_heat", (BIG_X, 14.0, -90.0), 6, 2.0, m["heat"], [1, 3], 0.1, 0.9, 40.0, 50, (30.0, 30.0))
    # beat 2: GPUDirect RDMA from GPU 1 and GPU 6 out through their NICs to the leaf
    for k in (1, 6):
        nx = S.nic_of(k)
        n = S.NIC_X.index(nx)
        path = [(p[0], p[1] + 4.0, p[2]) for p in S.pcie_path(k)] + [(p[0], p[1] + 2.0, p[2]) for p in S.cable_path(nx, S.leaf_x(n))[1:]]
        run(root, f"rdma{k}", path, 10, 4.0, m["mem"], 2, 0.0, 0.6, 90)
    # beat 3: bytes in at the PCIe edge, packets out of the cage
    D_ = chip
    run(root, "bytes", [(BIG_X - 20.0, 8.0, -230.0), (BIG_X - 20.0, 8.0, -178.0), (BIG_X - 20.0, 8.0, -126.0),
                        (BIG_X - 4.0, 16.0, -110.0), (BIG_X, 16.0, -90.0)], 14, 2.4, m["mem"], 3, 0.0, 0.7, 45)
    run(root, "pkts", [(BIG_X, 16.0, -90.0), (BIG_X + 19.0, 16.0, -95.0), (BIG_X + 15.0, 8.0, -54.0), (BIG_X + 23.0, 17.0, -18.0),
                       (BIG_X + 23.0, 15.0, 4.0), (BIG_X + 23.0, 13.0, 90.0)], 10, 3.0, m["pkt"], 3, 0.2, 0.9, 50)
    run(root, "hdrs", [(BIG_X, 20.0, -90.0), (BIG_X + 19.0, 20.0, -95.0), (BIG_X + 15.0, 12.0, -54.0), (BIG_X + 23.0, 21.0, -18.0),
                       (BIG_X + 23.0, 19.0, 4.0), (BIG_X + 23.0, 17.0, 90.0)], 10, 1.6, m["fe"], 3, 0.21, 0.91, 50)
    run(root, "b1", [(BIG_X - 20.0, 8.0, -200.0), (BIG_X - 20.0, 8.0, -126.0), (BIG_X, 16.0, -90.0), (BIG_X + 19.0, 16.0, -95.0),
                     (BIG_X + 23.0, 15.0, 4.0), (BIG_X + 23.0, 13.0, 60.0)], 6, 2.4, m["pkt"], 1, 0.3, 0.9, 50)
    nic3 = s["nic"][3]
    C.tags(root, {
        0: [("8 NICs: one per GPU", nic3["cage"]), ("2 DPUs: front-end + storage", s["dpu"][0]["cage"]),
            ("fibre to the leaf switch", (S.leaf_x(5), S.LEAF[2] - 20.0, 64.0)), ("8 GPUs", s["gpu"][1]["top"])],
        1: [("PCIe edge fingers", conn), ("controller die", pt["pcie"]), ("SerDes lanes", pt["serdes"]),
            ("heatsink, lifted off", pt["hs"]), ("OSFP cage: DSP + lasers", pt["dsp"])],
        2: [("GPU memory", s["gpu"][1]["top"]), ("PCIe switch", s["psw"][1]["top"]), ("NIC", s["nic"][S.NIC_X.index(S.nic_of(1))]["cage"]),
            ("CPU not in the path", s["cpu"][0]["top"])],
        3: [("bytes in over PCIe", (BIG_X - 20.0, 8.0, -160.0)), ("packets + headers out", (BIG_X + 23.0, 15.0, 50.0)),
            ("RDMA engines on the die", chip)],
        4: [("GPUs shipped = NICs shipped", nic3["cage"]), ("NVDA AVGO AMD MRVL INTC", (S.leaf_x(4), S.LEAF[3], 64.0))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 60.0, -160.0), 680.0, 0.30, 0.95),
        frame((BIG_X, 20.0, -90.0), 300.0, 0.55, 0.75),
        frame((0.0, 40.0, -220.0), 560.0, 0.20, 0.85),
        frame((BIG_X, 15.0, -80.0), 260.0, 0.75, 0.6),
        frame((0.0, 100.0, -60.0), 680.0, -0.25, 0.95),
    ], root)


if __name__ == "__main__":
    build()
