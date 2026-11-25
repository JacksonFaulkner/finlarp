"""TRM_SMARTNIC on the MLCC base board: a NIC chip and its network cage beside the GPU, the NIC
die drawn huge on the bench as a line of hardware stages (SerDes, MAC, parser, match-action
pipeline, RDMA engine, PCIe), packets moving stage by stage, RDMA straight from GPU memory, and
congestion control pacing traffic.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_smartnic.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, blink, rise  # noqa: E402
from trm_dpu import cage  # noqa: E402

SLUG = "TRM_SMARTNIC"
BEATS = [
    ("A NIC connects the server to the network; a SmartNIC thinks too",
     "Every server talks to the network through a network interface card: a chip, a cage for the optical cable, and a "
     "PCIe link to the host. A basic NIC just turns bits on the wire into packets in memory. A SmartNIC adds its own "
     "processing (a custom ASIC, an FPGA or small cores) to do packet work itself."),
    ("Inside: a line of hardware stages",
     "Follow a packet across the die. SerDes recover bits from the 112-224 Gb/s lanes, the MAC frames them, a parser "
     "reads the headers, a match-action pipeline looks them up in tables and decides what to do, and the RDMA engine "
     "and PCIe block move the payload into memory. Each stage is fixed logic, so it keeps up at line rate."),
    ("Packets march through the pipeline, one stage per clock",
     "Many packets are in flight at once, each in a different stage, like an assembly line. Virtual switching, "
     "encryption, tunnel encapsulation and load balancing all happen here, instead of on host CPU cores that would "
     "need dozens of cores to keep up with 400 Gb/s."),
    ("RDMA: GPU memory to the wire, no CPU copies",
     "For AI training the key job is RDMA: the NIC reads data straight out of one GPU's memory and writes it into a GPU in "
     "another server, with no CPU and no extra copies. That is how gradients move between thousands of GPUs. Back-end "
     "AI networks use about one 400-800G NIC per GPU, so NIC count grows with accelerator count."),
    ("Congestion control keeps thousands of GPUs from jamming",
     "When many GPUs send to one at the same time, switch buffers fill and packets would drop. The NIC watches for "
     "congestion marks and delay and paces its sending rate in hardware within microseconds. Better congestion control "
     "means GPUs wait less. Makers: NVIDIA ConnectX (NVDA), Broadcom Thor (AVGO), AMD Pollara (AMD), Intel (INTC), Marvell (MRVL)."),
]

NIC = (195.0, 0.0, -155.0)
CAGE_Z = -155.0
GX0, GX1, GZ0 = 156.0, 244.0, -50.0
TY = 8.0
# stages across the die, from the wire (right) to PCIe (left)
STAGES = [("serdes", 228.0, 240.0, "serdes"), ("mac", 216.0, 226.0, "mac"), ("parse", 203.0, 214.0, "parse"),
          ("match", 180.0, 201.0, "match"), ("rdma", 168.0, 178.0, "rdma"), ("pcie", 159.0, 166.0, "pcie")]


def mats(m):
    for k, c in (("serdes", (0.20, 0.22, 0.28)), ("mac", (0.25, 0.40, 0.55)), ("parse", (0.22, 0.48, 0.40)),
                 ("match", (0.40, 0.30, 0.55)), ("rdma", (0.58, 0.42, 0.22)), ("pcie", (0.45, 0.30, 0.22)),
                 ("sram", (0.32, 0.30, 0.40))):
        m[k] = mat(f"nic_{k}", c, metal=0.45, rough=0.35)
    m["stg_g"] = mat("nic_stg_g", (0.35, 1.0, 0.60), emit=(0.30, 1.0, 0.55), strength=1.4)
    m["slow"] = mat("nic_slow", (1.0, 0.70, 0.20), emit=(1.0, 0.62, 0.15), strength=5.0)


def giant(m, root):
    g = empty("gnic", root)
    bx("g_sub", (GX0, 0.6, GZ0), (GX1, 4.0, 0.0), m["substrate"], g)
    for k, y in enumerate((1.4, 2.4, 3.2)):
        bx(f"g_subcu{k}", (GX0, y, GZ0), (GX1, y + 0.3, 0.15), m["copper"], g)
    bx("g_die", (GX0 + 2.0, 4.0, GZ0 + 3.0), (GX1 - 2.0, TY, 0.0), m["die"], g)
    for k in range(5):
        y = 6.2 + 0.35 * k
        bx(f"g_bm{k}", (GX0 + 2.0, y, -0.4), (GX1 - 2.0, y + 0.15, 0.1), m["copper"], g)
    pts, glows = {}, []
    for name, x0, x1, mt in STAGES:
        h = 2.0
        bx(f"g_{name}", (x0, TY, GZ0 + 6.0), (x1, TY + h, -4.0), m[mt], g)
        gl = empty(f"gl_{name}", root)
        bx(f"g_{name}_g", (x0 + 0.5, TY + h, GZ0 + 6.5), (x1 - 0.5, TY + h + 0.3, -4.5), m["stg_g"], gl)
        show(gl, [])
        glows.append(gl)
        pts[name] = ((x0 + x1) / 2, TY + h, GZ0 / 2)
    # detail: SerDes lanes, lookup tables in the match stage
    for k in range(8):
        z0 = GZ0 + 7.0 + 4.6 * k
        bx(f"g_lane{k}", (229.0, TY + 2.0, z0), (239.0, TY + 2.8, z0 + 3.2), m["dark"], g)
    for i in range(4):
        for j in range(3):
            x0, z0 = 182.0 + 4.8 * i, GZ0 + 9.0 + 11.0 * j
            bx(f"g_tcam{i}{j}", (x0, TY + 2.0, z0), (x0 + 4.0, TY + 3.0, z0 + 9.0), m["sram"], g)
    pts["tables"] = (191.0, TY + 3.0, GZ0 + 20.0)
    return glows, pts


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    brd = empty("nic_brd", root)
    C.chip(m, brd, "nic", NIC, 20.0, 20.0, 2.0, pins=0, body="substrate")
    bx("nic_lid", (NIC[0] - 7.0, 2.0, NIC[2] - 7.0), (NIC[0] + 7.0, 3.6, NIC[2] + 7.0), m["alu"], brd)
    ntop = (NIC[0], 3.6, NIC[2])
    cg = cage(m, brd, "cage", CAGE_Z)
    C.trace(m, brd, "t_net", [(222.0, 0.0, CAGE_Z), (NIC[0] + 10.0, 0.0, CAGE_Z)], 1.0)
    gpu_path = [(NIC[0] - 10.0, 0.0, NIC[2]), (145.0, 0.0, NIC[2]), (145.0, 0.0, -60.0), (60.0, 0.0, -60.0)]
    C.trace(m, brd, "t_gpu", gpu_path, 1.0)
    glows, gp = giant(m, root)
    C.magnify(m, root, ntop, (GX0 + 10.0, 10.0, -10.0), r=5.0)

    # beat 1: stages light one after another from the wire side
    for k, gl in enumerate(glows):
        show(gl, [(F(1, 0.1 + 0.12 * k), F(2, 0))])
    # beat 2: a train of packets, every stage busy, stages blinking
    y = TY + 4.0
    line = [(GX1 + 6.0, y, -22.0)] + [(gp[s[0]][0], y, -22.0) for s in STAGES] + [(GX0 + 2.0, y, -22.0), (GX0 + 2.0, y, 4.0)]
    run(root, "pkts", line, 14, 0.9, m["sig"], 2, 0.0, 0.85, 45)
    # beat 3: RDMA from the GPU through the NIC out to the wire
    rd = [(10.0, D.DIE_Y[1] + 1.0, -30.0)] + [(p[0], 1.2, p[2]) for p in reversed(gpu_path)] + [(NIC[0] + 10.0, 1.2, CAGE_Z), (252.0, 1.2, CAGE_Z)]
    run(root, "rdma", rd, 14, 1.0, m["e_blue"], 3, 0.0, 0.85, 70)
    show(b["die_glow"], [(F(3, 0), F(4, 0))])
    rise(root, "nic_heat", (NIC[0], 4.0, NIC[2]), 4, 0.7, m["heat"], [2, 3], 0.1, 0.9, 16.0, 40, (5.0, 5.0))
    # beat 4: congestion: sparse paced packets vs a red burst that backs up
    run(root, "burst", [(GX0 + 2.0, y, 4.0), (GX0 + 2.0, y, -30.0)] + [(gp[s[0]][0], y, -30.0) for s in reversed(STAGES)] + [(GX1 + 20.0, y, -30.0)],
        16, 0.9, m["warn"], 4, 0.0, 0.3, 40)
    run(root, "paced", [(GX0 + 2.0, y, 4.0), (GX0 + 2.0, y, -14.0)] + [(gp[s[0]][0], y, -14.0) for s in reversed(STAGES)] + [(GX1 + 20.0, y, -14.0)],
        5, 0.9, m["slow"], 4, 0.45, 0.95, 40)
    cc = empty("cc", root)
    bx("cc_mark", (GX1 + 8.0, y - 3.0, -34.0), (GX1 + 10.0, y + 6.0, -26.0), m["warn"], cc)
    blink(cc, 4, [0, 1, 2, 3], n=8, on=0.6)

    C.tags(root, {
        0: [("NIC chip", ntop), ("cage: 400-800G optics", cg), ("PCIe to the GPU", (145.0, 1.0, -100.0)), ("GPU package", pk["top"])],
        1: [("SerDes: bits off the wire", gp["serdes"]), ("parser reads headers", gp["parse"]),
            ("match-action tables", gp["tables"]), ("RDMA engine", gp["rdma"]), ("PCIe to memory", gp["pcie"])],
        2: [("one stage per clock", gp["match"]), ("many packets in flight", gp["mac"])],
        3: [("RDMA: read GPU memory", (60.0, 2.0, -60.0)), ("no CPU copies", (145.0, 1.0, -120.0)), ("out to the other server", cg)],
        4: [("burst: buffers fill", (GX1, y + 6.0, -30.0)), ("NIC paces its rate", gp["rdma"]), ("NVDA, AVGO, AMD, INTC, MRVL", gp["match"])],
    })
    bc = ((GX0 + GX1) / 2, TY, GZ0 / 2)
    C.done(SLUG, BEATS, [
        frame((100.0, 0.0, -120.0), 320.0, 0.35, 0.65, pad=1.0),
        frame(bc, 95.0, 0.20, 0.70),
        frame((bc[0], TY + 3.0, bc[2]), 90.0, 0.05, 0.35),
        frame((110.0, 0.0, -120.0), 300.0, 0.10, 0.90, pad=1.0),
        frame((bc[0] + 8.0, TY, bc[2]), 105.0, -0.20, 0.45),
    ], root)


if __name__ == "__main__":
    build()
