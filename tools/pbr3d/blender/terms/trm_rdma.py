"""TRM_RDMA (RDMA / RoCE): the Terms-tab overview, built on the cluster kit in trm_infiniband.py.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_rdma.py

Two GPU servers with their lids off cabled to an Ethernet switch. Data arriving the old way climbs
through the CPU and gets copied into memory; with RDMA the NIC writes it straight in; with GPUDirect
it goes GPU memory to GPU memory. RoCE brings it to Ethernet with pause frames keeping links lossless.

Beats:
  0 tcp        the normal path: NIC -> CPU (kernel, copies) -> memory; the CPU heats up
  1 rdma       the NIC writes straight into the far server's memory; the CPU stays cool
  2 gpudirect  GPU memory to GPU memory across the network
  3 roce       the same over Ethernet: the switch buffer fills, a pause frame slows the sender
  4 latency    tens of microseconds vs a couple; who sells it
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import bx, empty, show, F  # noqa: E402
from power_vrm_detail import frame, run, blink, rise  # noqa: E402
import trm_infiniband as K  # noqa: E402

SLUG = "TRM_RDMA"
BEATS = [
    ("Normally every byte from the network goes through the CPU",
     "With ordinary TCP the NIC hands each packet to the operating system. The CPU runs the network stack, then copies "
     "the data into the application's memory, often more than once. At 400 Gb/s that burns many CPU cores and adds tens "
     "of microseconds of delay."),
    ("RDMA: the NIC writes straight into the other server's memory",
     "Remote direct memory access lets one server's NIC read or write a registered region of another server's memory "
     "directly. The application posts the request to a queue on the NIC, and the far NIC places the data in memory "
     "itself. No CPU cycles, no kernel, no copies on either side."),
    ("GPUDirect RDMA: GPU memory to GPU memory",
     "With GPUDirect the NIC reads from and writes to GPU memory over PCIe, skipping system memory too. Gradients leave "
     "one GPU's HBM and land in another's, which is what makes training across thousands of GPUs practical."),
    ("RoCE runs RDMA over Ethernet, with pause frames to stay lossless",
     "InfiniBand has RDMA built in. RoCE (RDMA over Converged Ethernet) wraps the same transport in Ethernet and IP "
     "packets. RDMA hates dropped packets, so when a switch buffer fills it sends a pause frame (PFC) or marks packets "
     "(ECN) and the sender slows down. Tuning this is the hard part of running RoCE at scale."),
    ("A few microseconds instead of tens",
     "Cutting out the CPU and the copies takes end-to-end latency from tens of microseconds to about one or two, and "
     "frees those cores. Most Ethernet AI clusters run RoCE today. Related: Nvidia (NVDA), Broadcom (AVGO), "
     "Arista (ANET), AMD (AMD)."),
]


def build():
    m, root = C.setup(SLUG, len(BEATS))
    cl = K.cluster(m, root)
    A, B, S = cl["srv"][0], cl["srv"][1], cl["sw"]
    y = K.TOP + 1.5
    wire_in = K.nic_port(A) + cl["cab"][0][1:] + [S["asic"]] + list(reversed(cl["cab"][1]))[:-1] + list(reversed(K.nic_port(B)))
    to_psw = [(B["nic"][0], y, B["nic"][2]), (B["nic"][0], y, -90), (B["psw"][0], y, -90)]
    via_cpu = to_psw + [(B["psw"][0], y, B["cpu"][2]), B["cpu"], (B["cpu"][0], B["cpu"][1] + 2, B["cpu"][2]), B["mem"]]
    direct = to_psw + [(B["psw"][0], y, B["cpu"][2] - 30), (B["mem"][0], y, B["cpu"][2] - 30), B["mem"]]

    # beat 0: wire -> NIC -> CPU -> memory, copies, CPU hot
    run(root, "b0_wire", wire_in, 8, 1.4, m["sig"], 0, 0.0, 0.5, 50)
    run(root, "b0_cpu", via_cpu, 8, 1.4, m["warn"], 0, 0.25, 0.8, 50)
    run(root, "b0_copy", [B["cpu"], B["mem"], B["cpu"], B["mem"]], 6, 1.2, m["warn"], 0, 0.4, 0.85, 40)
    rise(root, "b0_heat", B["cpu"], 8, 0.9, m["heat"], 0, 0.2, 0.9, 22.0, 40, (8.0, 8.0))
    rise(root, "b0_heatA", A["cpu"], 5, 0.9, m["heat"], 0, 0.1, 0.9, 22.0, 40, (8.0, 8.0))
    # beat 1: direct into memory
    run(root, "b1_wire", [(A["mem"][0], A["mem"][1], A["mem"][2]), (A["psw"][0], y, A["cpu"][2] - 30), (A["psw"][0], y, -90),
                          (A["nic"][0], y, -90)] + K.nic_port(A)[0:1] + wire_in[1:], 8, 1.4, m["e_blue"], 1, 0.0, 0.5, 60)
    run(root, "b1_dir", direct, 8, 1.4, m["e_blue"], 1, 0.3, 0.85, 40)
    for s in (0, 1):
        show(cl["srv"][s]["mglow"], [(F(1, 0.2), F(2, 0))])
    # the hero on the bench: the NIC cut open, its DMA engine writing into a DIMM cut open beside it
    K.hero_mats(m)
    blocks = [("sd", -106, -90, 146, 204, "hr_serdes", 2.4, None),
              ("qp", -86, -56, 146, 172, "hr_sram", 1.6, "hr_g_amber"),
              ("dma", -86, -30, 176, 204, "hr_blue", 2.2, "hr_g_blue"),
              ("pkt", -52, -30, 146, 172, "hr_green", 1.8, "hr_g_green"),
              ("pcie", -26, -6, 146, 204, "hr_gold", 1.6, None)]
    hg, hp, hgl = K.hero(m, root, "nicx", -110.0, -2.0, 142.0, 208.0, blocks)
    ty = hp["ty"] + 3.0
    dg = K.empty("dimmx", root)
    bx("dx_pcb", (40, 0, 146), (140, 3, 204), m["cl_dimm"], dg)
    for i in range(16):
        bx(f"dx_gold{i}", (44 + 6 * i, 0, 202), (47 + 6 * i, 3.1, 205), m["gold"], dg)
    cells = []
    for c in range(4):
        x0 = 46 + 23.5 * c
        bx(f"dx_chip{c}", (x0, 3, 152), (x0 + 19, 6, 198), m["mold"], dg)
        bx(f"dx_die{c}", (x0 + 2, 6, 155), (x0 + 17, 7.2, 195), m["silicon"], dg)
        for r in range(6):
            ce = K.empty(f"dx_c{c}{r}", root)
            bx(f"dx_cm{c}{r}", (x0 + 3, 7.2, 157 + 6.3 * r), (x0 + 16, 7.7, 161.5 + 6.3 * r), m["cl_mem_g"], ce)
            cells.append(ce)
    from power_vrm_detail import present
    for o in (hg, dg):
        present(o, [(F(1, 0.4), F(2, 0))])
    mg = K.empty("mg", root)
    C.magnify(m, mg, B["nic"], (-100.0, ty, 150.0), r=5.0)
    show(mg, [(F(1, 0.4), F(2, 0))])
    run(root, "h_in", [(-130, ty, 175), (-98, ty, 175), hp["pkt"][:1] + (ty, 160), (hp["dma"][0], ty, 190), (-16, ty, 190),
                       (40, ty + 6, 190), (60, 12, 175)], 10, 1.2, m["e_blue"], 1, 0.45, 0.85, 45)
    for k in ("qp", "dma", "pkt"):
        show(hgl[k], [(F(1, 0.45), F(2, 0))])
    for i, ce in enumerate(cells):
        show(ce, [(F(1, 0.55 + 0.016 * i), F(2, 0))])
    from sand_overview import label
    for t, pt in (("NIC cut open", hp["sd"]), ("queue pairs (posted work)", hp["qp"]), ("DMA engine", hp["dma"]),
                  ("PCIe to memory", hp["pcie"]), ("DIMM cut open: cells written", (80.0, 8.0, 175.0))):
        label(t, pt, root, [(F(1, 0.45), F(2, 0))])

    # beat 2: GPUDirect
    run(root, "b2_g2g", K.gpu_to_gpu(cl, 0, 1), 14, 1.6, m["e_blue"], 2, 0.05, 0.6, 90)
    for s in (0, 1):
        show(cl["srv"][s]["glow"], [(F(2, 0), F(3, 0))])
    # beat 3: RoCE: switch fills, pause frame back to the sender
    up = K.nic_port(A) + cl["cab"][0][1:] + [S["asic"]]
    run(root, "b3_up", up, 12, 1.4, m["sig"], 3, 0.0, 0.4, 45)
    run(root, "b3_pause", list(reversed(up)), 3, 2.4, m["warn"], 3, 0.45, 0.6, 45)
    run(root, "b3_slow", up, 4, 1.4, m["sig"], 3, 0.72, 0.95, 45)
    show(S["glow"], [(F(3, 0.3), F(3, 0.55))])
    # beat 4: latency bars
    bg = empty("lat", root)
    bx("lat_tcp", (-50.0, 0.0, 82.0), (-30.0, 90.0, 98.0), m["cl_bar2"], bg)
    bx("lat_rdma", (30.0, 0.0, 82.0), (50.0, 7.0, 98.0), m["cl_bar"], bg)
    show(bg, [(F(4, 0), F(5, 0))])
    blink(S["leds"], 4, [0, 2, 4, 6], n=8)
    run(root, "b4_g2g", K.gpu_to_gpu(cl, 2, 3), 8, 1.4, m["e_blue"], 4, 0.05, 0.7, 80)

    for t, pt in (("NIC writes into memory", B["mem"]), ("CPU idle", B["cpu"]), ("read from memory", A["mem"])):
        label(t, pt, root, [(F(1, 0), F(1, 0.4))])
    C.tags(root, {
        0: [("CPU runs the stack, hot", B["cpu"]), ("copied into memory", B["mem"]), ("NIC", B["nic"]),
            ("Ethernet switch", S["top"])],
        2: [("out of GPU memory", A["gpu"][0]), ("into far GPU memory", B["gpu"][1]), ("system memory skipped", A["mem"])],
        3: [("switch buffer filling", S["asic"]), ("pause frame (PFC)", cl["cab"][0][2]), ("RoCE v2 = RDMA in UDP/IP", S["top"])],
        4: [("TCP: tens of us", (-40.0, 92.0, 90.0)), ("RDMA: ~1-2 us", (40.0, 9.0, 90.0)),
            ("NVDA, AVGO, ANET, AMD", S["top"])],
    })
    C.done(SLUG, BEATS, [
        frame((170.0, 8.0, -95.0), 230.0, -0.15, 0.85),
        [(0.0, frame((60.0, 20.0, -90.0), 380.0, 0.10, 0.70, pad=1.0)),
         (0.45, frame((10.0, 8.0, 175.0), 270.0, 0.15, 0.75))],
        frame((0.0, 30.0, -100.0), 440.0, -0.25, 0.75, pad=1.0),
        frame((-60.0, 50.0, -40.0), 280.0, 0.35, 0.40),
        frame((0.0, 40.0, -20.0), 420.0, 0.30, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
