"""TRM_DPU on the MLCC base board: a DPU card's chip, memory and network cages beside the GPU, the
DPU die drawn huge on the bench with its Arm cores, packet, crypto and storage engines, packets
being handled in hardware and landing in GPU memory without touching the host CPU.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_dpu.py

Beats:
  0 board     the DPU, its DDR and two network cages next to the GPU; a trace off to the host CPU
  1 inside    the giant die: Arm core cluster, packet / crypto / storage engines, PCIe, SerDes
  2 packets   packets come off the wire and pass engine by engine, all in hardware
  3 to GPU    payloads go straight to the GPU over PCIe; the host CPU trace stays dark
  4 tenants   two tenants' traffic kept apart; a bad packet is dropped at the firewall
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, blink, rise  # noqa: E402

SLUG = "TRM_DPU"
BEATS = [
    ("A DPU is a whole computer on the network card",
     "A data processing unit sits on a network card beside the GPUs. It has its own fast Ethernet ports, its own DDR "
     "memory and its own processor, and plugs into the server over PCIe. The host CPU sees it as a NIC, but the DPU "
     "runs its own operating system."),
    ("Inside: Arm cores plus hardware engines",
     "Open the chip and most of the die is not general cores. A cluster of Arm cores runs control software, while fixed "
     "engines do the heavy lifting: packet parsing and switching, encryption, compression and NVMe storage. SerDes on "
     "the edge drive 200-800 Gb/s of Ethernet; a PCIe block talks to the host and GPUs."),
    ("Packets are parsed, decrypted and steered in hardware",
     "A packet arrives from the wire, the packet engine reads its headers and matches it against flow tables, the crypto "
     "engine decrypts it at line rate, and it is steered to the right destination. Doing this in silicon takes "
     "nanoseconds per packet, where software on CPU cores would burn dozens of cores at these speeds."),
    ("Data goes straight to GPU memory; the CPU stays free",
     "With GPUDirect-style transfers the DPU writes incoming data straight into GPU memory over PCIe. The host CPU is "
     "not in the path, so its cores stay free for the job, and storage reads (NVMe over fabrics) land in the GPU the same "
     "way."),
    ("It also walls tenants off from each other",
     "Because networking, storage and security policy run on the DPU, a cloud can rent the server's CPU and GPUs to a "
     "customer while keeping its own control plane out of their reach. Firewall rules drop bad traffic before it reaches "
     "the host. Makers: NVIDIA BlueField (NVDA), AMD Pensando (AMD), Intel IPU (INTC), Marvell OCTEON (MRVL), Broadcom (AVGO)."),
]

# board-side parts, behind the phases on the right
DPU = (195.0, 0.0, -155.0)
DDR = [(165.0, 0.0, -130.0), (165.0, 0.0, -180.0)]
CAGE_Z = [-135.0, -175.0]
# the giant die on the bench
GX0, GX1, GZ0 = 158.0, 242.0, -62.0
SY = (0.6, 4.0)  # substrate
DY = (4.0, 8.0)  # die
TY = 8.0  # die top


def mats(m):
    m["arm"] = mat("dpu_arm", (0.30, 0.42, 0.62), metal=0.4, rough=0.35)
    m["eng_pkt"] = mat("dpu_pkt", (0.22, 0.48, 0.40), metal=0.4, rough=0.35)
    m["eng_cry"] = mat("dpu_cry", (0.55, 0.32, 0.50), metal=0.4, rough=0.35)
    m["eng_sto"] = mat("dpu_sto", (0.58, 0.48, 0.22), metal=0.4, rough=0.35)
    m["pcie"] = mat("dpu_pcie", (0.45, 0.30, 0.22), metal=0.5, rough=0.35)
    m["serdes"] = mat("dpu_serdes", (0.20, 0.22, 0.28), metal=0.6, rough=0.3)
    m["sram"] = mat("dpu_sram", (0.32, 0.30, 0.40), metal=0.5, rough=0.3)
    m["arm_g"] = mat("dpu_arm_g", (0.35, 0.65, 1.0), emit=(0.30, 0.60, 1.0), strength=3.0)
    m["pkt_g"] = mat("dpu_pkt_g", (0.35, 1.0, 0.60), emit=(0.30, 1.0, 0.55), strength=1.2)
    m["cry_g"] = mat("dpu_cry_g", (0.95, 0.45, 1.0), emit=(0.90, 0.40, 1.0), strength=1.2)
    m["ten_a"] = mat("dpu_ten_a", (0.30, 0.80, 1.0), emit=(0.25, 0.80, 1.0), strength=5.0)
    m["ten_b"] = mat("dpu_ten_b", (1.0, 0.70, 0.20), emit=(1.0, 0.65, 0.15), strength=5.0)


def block(m, g, name, x0, x1, z0, z1, mt, h=1.2, glow=None, glow_parent=None):
    bx(name, (x0, TY, z0), (x1, TY + h, z1), m[mt], g)
    if glow:
        bx(f"{name}_g", (x0 + 0.5, TY + h, z0 + 0.5), (x1 - 0.5, TY + h + 0.3, z1 - 0.5), m[glow], glow_parent)
    return ((x0 + x1) / 2, TY + h, (z0 + z1) / 2)


def giant(m, root):
    g = empty("gdpu", root)
    # BGA, substrate with copper layers, the die, all cut at z = 0
    balls = []
    for i in range(11):
        x = GX0 + 4.0 + i * (GX1 - GX0 - 8.0) / 10
        balls.append(O_ball(f"g_bga{i}", (x, 0.3, -1.0), 1.0, m["solder"], g))
    D.join(balls, "g_bga")
    bx("g_sub", (GX0, SY[0], GZ0), (GX1, SY[1], 0.0), m["substrate"], g)
    for k, y in enumerate((1.4, 2.4, 3.2)):
        bx(f"g_subcu{k}", (GX0, y, GZ0), (GX1, y + 0.3, 0.15), m["copper"], g)
    bx("g_die", (GX0 + 3.0, DY[0], GZ0 + 3.0), (GX1 - 3.0, DY[1], 0.0), m["die"], g)
    # metal stack stripe on the cut face
    for k in range(5):
        y = DY[0] + 2.2 + 0.35 * k
        bx(f"g_bm{k}", (GX0 + 3.0, y, -0.4), (GX1 - 3.0, y + 0.15, 0.1), m["copper"], g)
    glows = {k: empty(f"gl_{k}", root) for k in ("arm", "pkt", "cry", "sto")}
    pts = {}
    # Arm core cluster: 4 x 4 cores, each with its L2 slice
    cores = []
    for i in range(4):
        for j in range(4):
            x0 = GX0 + 6.0 + 8.0 * i
            z0 = GZ0 + 6.0 + 7.5 * j
            cores.append(bx(f"g_core{i}{j}", (x0, TY, z0), (x0 + 5.0, TY + 1.6, z0 + 5.5), m["arm"], g))
            cores.append(bx(f"g_l2{i}{j}", (x0 + 5.2, TY, z0), (x0 + 7.2, TY + 1.0, z0 + 5.5), m["sram"], g))
            gl = empty(f"gl_core{i}{j}", glows["arm"])
            bx(f"g_coreg{i}{j}", (x0 + 0.4, TY + 1.6, z0 + 0.4), (x0 + 4.6, TY + 1.9, z0 + 5.1), m["arm_g"], gl)
    D.join(cores, "g_cores")
    pts["arm"] = (GX0 + 20.0, TY + 2.0, GZ0 + 20.0)
    # shared cache under the cores
    pts["llc"] = block(m, g, "g_llc", GX0 + 6.0, GX0 + 37.0, GZ0 + 37.0, GZ0 + 44.0, "sram", 1.0)
    # engines
    pts["pkt"] = block(m, g, "g_pkt", GX0 + 42.0, GX1 - 14.0, GZ0 + 6.0, GZ0 + 22.0, "eng_pkt", 1.8, "pkt_g", glows["pkt"])
    pts["cry"] = block(m, g, "g_cry", GX0 + 42.0, GX1 - 14.0, GZ0 + 25.0, GZ0 + 38.0, "eng_cry", 1.8, "cry_g", glows["cry"])
    pts["sto"] = block(m, g, "g_sto", GX0 + 6.0, GX0 + 37.0, GZ0 + 47.0, -4.0, "eng_sto", 1.5, "pkt_g", glows["sto"])
    pts["pcie"] = block(m, g, "g_pcie", GX0 + 42.0, GX1 - 14.0, GZ0 + 42.0, -4.0, "pcie", 1.4)
    # flow-table SRAM banks beside the packet engine
    for k in range(4):
        z0 = GZ0 + 6.0 + 4.0 * k
        bx(f"g_ft{k}", (GX1 - 13.0, TY, z0), (GX1 - 9.0, TY + 1.2, z0 + 3.4), m["sram"], g)
    # SerDes lanes along the right edge
    lanes = []
    for k in range(10):
        z0 = GZ0 + 5.0 + 5.2 * k
        lanes.append(bx(f"g_sd{k}", (GX1 - 8.0, TY, z0), (GX1 - 4.0, TY + 2.2, z0 + 4.0), m["serdes"], g))
    D.join(lanes, "g_serdes")
    pts["serdes"] = (GX1 - 6.0, TY + 2.2, GZ0 + 20.0)
    for o in glows.values():
        show(o, [])
    return glows, pts


def O_ball(name, c, r, mt, parent):
    from sand_overview import ball
    return ball(name, c, r, mt, parent, 10)


def cage(m, parent, name, z):
    """A QSFP cage on the board's right edge, open end facing +x."""
    g = empty(name, parent)
    x0, x1 = 222.0, 250.0
    bx(f"{name}_floor", (x0, 0.0, z - 7.0), (x1, 0.5, z + 7.0), m["alu"], g)
    bx(f"{name}_top", (x0, 9.5, z - 7.0), (x1, 10.0, z + 7.0), m["alu"], g)
    for s in (-1, 1):
        bx(f"{name}_side{s}", (x0, 0.0, z + s * 7.0 - 0.25), (x1, 10.0, z + s * 7.0 + 0.25), m["alu"], g)
    bx(f"{name}_back", (x0, 0.0, z - 7.0), (x0 + 0.5, 10.0, z + 7.0), m["alu"], g)
    for k in range(4):  # heat-sink fins on top
        bx(f"{name}_fin{k}", (x0 + 4.0 + 6.0 * k, 10.0, z - 6.0), (x0 + 6.0 + 6.0 * k, 14.0, z + 6.0), m["alu"], g)
    bx(f"{name}_led", (x1 - 2.0, 10.0, z + 4.0), (x1, 10.6, z + 6.0), m["sig"], g)
    return (x1, 10.0, z)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    brd = empty("dpu_brd", root)
    # the DPU package with a heat spreader, its DDR chips, the cages and traces
    dtop = C.chip(m, brd, "dpu", DPU, 24.0, 24.0, 2.0, pins=0, body="substrate")
    bx("dpu_lid", (DPU[0] - 9.0, 2.0, DPU[2] - 9.0), (DPU[0] + 9.0, 4.0, DPU[2] + 9.0), m["alu"], brd)
    dtop = (DPU[0], 4.0, DPU[2])
    ddr_tops = [C.chip(m, brd, f"ddr{k}", c, 12.0, 10.0, 1.4, pins=6) for k, c in enumerate(DDR)]
    cages = [cage(m, brd, f"cage{k}", z) for k, z in enumerate(CAGE_Z)]
    for k, z in enumerate(CAGE_Z):
        C.trace(m, brd, f"t_net{k}", [(222.0, 0.0, z), (210.0, 0.0, z), (207.0, 0.0, DPU[2] + (8.0 if k == 0 else -8.0))], 0.8)
    for k, c in enumerate(DDR):
        C.trace(m, brd, f"t_ddr{k}", [(c[0] + 7.0, 0.0, c[2]), (DPU[0] - 12.0, 0.0, DPU[2] + (6.0 if k == 0 else -6.0))], 0.6)
    gpu_path = [(DPU[0] - 12.0, 0.0, DPU[2]), (145.0, 0.0, DPU[2]), (145.0, 0.0, -60.0), (60.0, 0.0, -60.0)]
    cpu_path = [(DPU[0], 0.0, DPU[2] - 12.0), (DPU[0], 0.0, -212.0)]
    C.trace(m, brd, "t_gpu", gpu_path, 1.0)
    C.trace(m, brd, "t_cpu", cpu_path, 1.0)
    glows, gp = giant(m, root)
    C.magnify(m, root, dtop, (GX0 + 10.0, 10.0, -10.0), r=5.0)

    # beat 1: cores tick, engines lit
    for k, ch in enumerate(glows["arm"].children):
        blink(ch, 1, [k % 8, (k * 3 + 2) % 8], n=8, on=0.5)
    show(glows["arm"], [(F(1, 0), F(2, 0)), (F(4, 0), F(5, 0))])
    show(glows["pkt"], [(F(1, 0.3), F(3, 0))])
    show(glows["cry"], [(F(1, 0.45), F(3, 0))])
    show(glows["sto"], [(F(1, 0.6), F(2, 0)), (F(3, 0.3), F(4, 0))])

    # beat 2: packets through the engines on the bench, and in at the cages on the board
    y = TY + 3.0
    bench = [(GX1 + 4.0, y, gp["pkt"][2]), gp["serdes"][:1] + (y, gp["pkt"][2]),
             (gp["pkt"][0], y, gp["pkt"][2]), (gp["cry"][0], y, gp["cry"][2]),
             (gp["pcie"][0], y, gp["pcie"][2]), (gp["pcie"][0], y, 3.0)]
    run(root, "pk_bench", bench, 12, 0.9, m["pkt_g"], 2, 0.0, 0.85, 50)
    for k, z in enumerate(CAGE_Z):
        run(root, f"pk_in{k}", [(252.0, 1.0, z), (210.0, 1.0, z), (207.0, 1.0, DPU[2])], 6, 0.9, m["sig"], [2, 3], 0.0, 0.7, 30)

    # beat 3: to the GPU, CPU path dark
    run(root, "to_gpu", [(p[0], 1.2, p[2]) for p in gpu_path] + [(10.0, D.DIE_Y[1] + 1.0, -30.0)], 12, 1.0, m["pkt_g"], 3, 0.1, 0.9, 60)
    run(root, "nvme", [(gp["sto"][0], y, gp["sto"][2]), (gp["pcie"][0] - 10.0, y, gp["pcie"][2]), (gp["pcie"][0], y, 3.0)], 6, 0.8, m["e_blue"], 3, 0.1, 0.8, 30)
    show(b["die_glow"], [(F(3, 0.4), F(4, 0))])
    rise(root, "dpu_heat", (DPU[0], 4.5, DPU[2]), 4, 0.7, m["heat"], [2, 3], 0.1, 0.9, 16.0, 40, (5.0, 5.0))

    # beat 4: two tenants on separate lanes, a bad packet stopped at the crypto/firewall engine
    for k, (mt, dz) in enumerate((("ten_a", -3.0), ("ten_b", 3.0))):
        pp = [(GX1 + 4.0, y, gp["pkt"][2] + dz), (gp["pkt"][0], y, gp["pkt"][2] + dz), (gp["cry"][0], y, gp["cry"][2] + dz),
              (gp["pcie"][0] + dz * 3, y, gp["pcie"][2]), (gp["pcie"][0] + dz * 3, y, 3.0)]
        run(root, f"ten{k}", pp, 8, 0.9, m[mt], 4, 0.0 + 0.05 * k, 0.85, 50)
    run(root, "bad", [(GX1 + 4.0, y + 1.5, gp["pkt"][2]), (gp["pkt"][0], y + 1.5, gp["pkt"][2]), (gp["cry"][0] + 6.0, y + 1.5, gp["cry"][2] - 4.0)],
        3, 1.2, m["warn"], 4, 0.1, 0.7, 35)
    wall = empty("fw", root)
    bx("fw_wall", (gp["cry"][0] - 14.0, TY + 2.0, gp["cry"][2] - 1.0), (gp["cry"][0] + 14.0, TY + 8.0, gp["cry"][2] - 0.5), m["warn"], wall)
    blink(wall, 4, [1, 3, 5, 7], n=8, on=0.6)

    C.tags(root, {
        0: [("DPU", dtop), ("its own DDR memory", ddr_tops[0]), ("200-800G Ethernet cages", cages[0]),
            ("GPU package", pk["top"]), ("PCIe to host CPU", (DPU[0], 1.0, -205.0))],
        1: [("Arm core cluster", gp["arm"]), ("packet engine", gp["pkt"]), ("crypto engine", gp["cry"]),
            ("NVMe storage engine", gp["sto"]), ("SerDes to the wire", gp["serdes"])],
        2: [("parse + match flow tables", gp["pkt"]), ("decrypt at line rate", gp["cry"]), ("steer out over PCIe", gp["pcie"])],
        3: [("straight into GPU memory", (60.0, 2.0, -60.0)), ("host CPU not in the path", (DPU[0], 1.0, -205.0)),
            ("packets in off the wire", cages[1])],
        4: [("tenant A / tenant B kept apart", gp["pcie"]), ("firewall drops bad traffic", (gp["cry"][0], TY + 8.0, gp["cry"][2])),
            ("NVDA, AMD, INTC, MRVL, AVGO", gp["arm"])],
    })
    bc = ((GX0 + GX1) / 2, TY, GZ0 / 2)
    C.done(SLUG, BEATS, [
        frame((100.0, 0.0, -120.0), 320.0, 0.35, 0.65, pad=1.0),
        frame(bc, 95.0, 0.20, 0.75),
        frame((bc[0] + 6.0, TY, bc[2]), 85.0, -0.25, 0.60),
        frame((110.0, 0.0, -120.0), 300.0, 0.10, 0.90, pad=1.0),
        frame(bc, 95.0, 0.30, 0.55),
    ], root)


if __name__ == "__main__":
    build()
