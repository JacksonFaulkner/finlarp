"""TRM_INFINIBAND: the Terms-tab overview for InfiniBand, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_infiniband.py

Two GPU servers with their lids off (four GPUs with HBM, a CPU with its DIMMs, an InfiniBand HCA at
the front edge) cabled to an open-topped InfiniBand switch above them. In front of the switch a
"link lens" blows up one cable: the sender's buffer, the wire and the receiver's buffer, with credits
flowing back. This file also holds the small cluster kit (`cluster`, `nic_port`, `cable_pts`,
`gpu_out`...) that trm_rdma.py and trm_ultra_ethernet.py import.

Beats:
  0 fabric    two GPU servers, an HCA in each, cabled to one InfiniBand switch
  1 credits   the link lens: data only leaves when the receiver has granted a credit; nothing drops
  2 rdma      GPU memory to GPU memory through the HCAs and switch, the CPUs stay dark
  3 sharp     both servers send partial sums; the switch ASIC adds them and sends one result back
  4 market    link speeds 100 -> 800G per port; Nvidia owns it via Mellanox
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, blink, rise, polyline, arc  # noqa: E402

SLUG = "TRM_INFINIBAND"
BEATS = [
    ("InfiniBand is a separate network built just for clusters",
     "Each GPU server gets InfiniBand host channel adapters (HCAs), one per GPU in big systems, cabled to InfiniBand "
     "switches. It is its own protocol stack, not Ethernet: links, switches, routing and transport were all designed "
     "together for supercomputers, so latency is low and behaviour is predictable."),
    ("Credit flow control: a packet only leaves when there is room for it",
     "The receiving port tells the sender how many buffer slots it has free, as credits. The sender spends one credit "
     "per packet and stops when it runs out, so a switch never has to drop a packet for lack of space. Lossless links "
     "are what let RDMA work without slow retransmissions."),
    ("RDMA is built in: GPU memory to GPU memory, no CPU in the path",
     "The HCA reads data straight out of one GPU's memory, the switch forwards it in well under a microsecond, and the "
     "far HCA writes it straight into the other GPU's memory. Neither CPU nor operating system touches the data, which "
     "keeps GPUs fed during training when they swap gradients thousands of times a second."),
    ("The switch can do the maths itself (SHARP)",
     "In an all-reduce every GPU needs the sum of everyone's gradients. With SHARP the switch ASIC adds the incoming "
     "numbers as they pass and sends a single result back, instead of the data bouncing between servers. That roughly "
     "halves the traffic for the most common collective in training."),
    ("Nvidia owns it, and Ethernet is fighting back",
     "Speeds have doubled every few years: EDR 100G, HDR 200G, NDR 400G, now XDR 800G per port. Nvidia bought Mellanox, "
     "the main supplier, in 2020, and InfiniBand was the default for early large training clusters. Ethernet with RoCE "
     "and Ultra Ethernet now competes for the same job. Related: Nvidia (NVDA), Arista (ANET), Broadcom (AVGO)."),
]

# ---- cluster kit (shared with trm_rdma / trm_ultra_ethernet) -------------------------------

SX = (-170.0, 170.0)  # server centres; server s's NIC faces the middle
TRAY = (100.0, -230.0)  # half width, back z (front edge at z = 0)
SW = (0.0, 70.0, -70.0)  # single switch centre (x, floor y, centre z)
SW_W, SW_H, SW_D = 160.0, 26.0, 120.0
TOP = 2.4  # board top


def kit_mats(m):
    if "cl_tray" in m:
        return
    m["cl_tray"] = mat("cl_tray", (0.30, 0.32, 0.36), metal=0.8, rough=0.45)
    m["cl_pcb"] = mat("cl_pcb", (0.06, 0.28, 0.15), rough=0.55)
    m["cl_nic"] = mat("cl_nic", (0.08, 0.20, 0.30), rough=0.55)
    m["cl_sw"] = mat("cl_sw", (0.16, 0.17, 0.20), metal=0.6, rough=0.45)
    m["cl_sw2"] = mat("cl_sw2", (0.22, 0.20, 0.30), metal=0.6, rough=0.45)
    m["cl_sw3"] = mat("cl_sw3", (0.30, 0.20, 0.16), metal=0.6, rough=0.45)
    m["cl_port"] = mat("cl_port", (0.05, 0.05, 0.06), rough=0.5)
    m["cl_fiber"] = mat("cl_fiber", (0.15, 0.55, 0.65), rough=0.4)
    m["cl_cu"] = mat("cl_cu", (0.80, 0.48, 0.28), metal=0.9, rough=0.32)
    m["cl_dimm"] = mat("cl_dimm", (0.10, 0.22, 0.14), rough=0.55)
    m["cl_led"] = mat("cl_led", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)
    m["cl_gpu_g"] = mat("cl_gpu_g", (0.40, 0.75, 1.0), emit=(0.30, 0.70, 1.0), strength=1.4)
    m["cl_mem_g"] = mat("cl_mem_g", (1.0, 0.80, 0.30), emit=(1.0, 0.75, 0.25), strength=1.4)
    m["cl_asic_g"] = mat("cl_asic_g", (0.85, 0.45, 1.0), emit=(0.80, 0.40, 1.0), strength=1.5)
    m["cl_slot"] = mat("cl_slot", (0.25, 0.28, 0.34), metal=0.3, rough=0.4)
    m["cl_full"] = mat("cl_full", (1.0, 0.70, 0.25), emit=(1.0, 0.65, 0.20), strength=2.0)
    m["cl_credit"] = mat("cl_credit", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=4.0)
    m["cl_bar"] = mat("cl_bar", (0.15, 0.35, 0.70), emit=(0.20, 0.45, 0.90), strength=0.5)
    m["cl_bar2"] = mat("cl_bar2", (0.70, 0.35, 0.12), emit=(0.90, 0.45, 0.15), strength=0.5)


def side(s):
    return 1.0 if s == 0 else -1.0


def gpu(m, g, name, c, glow_parent):
    """GPU package: substrate, two dies, four HBM stacks, a glow slab on the dies (in glow_parent)."""
    x, z = c
    bx(f"{name}_sub", (x - 26, TOP, z - 24), (x + 26, TOP + 2.5, z + 24), m["substrate"], g)
    bx(f"{name}_int", (x - 22, TOP + 2.5, z - 20), (x + 22, TOP + 3.5, z + 20), m["silicon"], g)
    for k, dx in enumerate((-6.5, 6.5)):
        bx(f"{name}_die{k}", (x + dx - 6, TOP + 3.5, z - 12), (x + dx + 6, TOP + 6.5, z + 12), m["die"], g)
    for k, (dx, dz) in enumerate(((-17, -8), (-17, 8), (17, -8), (17, 8))):
        bx(f"{name}_hbm{k}", (x + dx - 3.5, TOP + 3.5, z + dz - 6), (x + dx + 3.5, TOP + 9.0, z + dz + 6), m["hbm"], g)
        for j in range(4):
            y = TOP + 4.5 + 1.1 * j
            bx(f"{name}_hbl{k}{j}", (x + dx - 3.6, y, z + dz - 6.1), (x + dx + 3.6, y + 0.25, z + dz + 6.1), m["hbm_dram"], g)
    gl = empty(f"{name}_glow", glow_parent)
    bx(f"{name}_gl", (x - 12, TOP + 6.5, z - 11), (x + 12, TOP + 7.0, z + 11), m["cl_gpu_g"], gl)
    return (x, TOP + 7.0, z)


def server(m, root, s):
    """One GPU server tray with the lid off. Returns its points dict."""
    sx, sd = SX[s], side(s)
    hw, bz = TRAY
    g = empty(f"srv{s}", root)
    D.join([bx(f"s{s}_floor", (sx - hw, -4.0, bz), (sx + hw, 0.0, 0.0), m["cl_tray"], g),
            bx(f"s{s}_wl", (sx - hw - 3, -4.0, bz), (sx - hw, 24.0, 0.0), m["cl_tray"], g),
            bx(f"s{s}_wr", (sx + hw, -4.0, bz), (sx + hw + 3, 24.0, 0.0), m["cl_tray"], g),
            bx(f"s{s}_wb", (sx - hw, -4.0, bz - 3), (sx + hw, 24.0, bz), m["cl_tray"], g)], f"s{s}_chassis")
    bx(f"s{s}_pcb", (sx - hw + 4, 0.0, bz + 4), (sx + hw - 4, TOP, -4.0), m["cl_pcb"], g)
    p = {"gpu": [], "glow": empty(f"s{s}_gpuglow", root), "mglow": empty(f"s{s}_memglow", root)}
    # four GPUs in the back half, 2 x 2
    for k, (dx, z) in enumerate(((-48, -190), (48, -190), (-48, -130), (48, -130))):
        p["gpu"].append(gpu(m, g, f"s{s}g{k}", (sx + dx, z), p["glow"]))
    # fans across the very back
    for k in range(5):
        fx = sx - 80 + 40 * k
        bx(f"s{s}_fan{k}", (fx - 17, 0.0, bz + 4), (fx + 17, 22.0, bz + 12), m["dark"], g)
    # CPU and its DIMMs (on the side away from the middle)
    cx = sx - sd * 45.0
    cz = -62.0
    bx(f"s{s}_cpus", (cx - 16, TOP, cz - 16), (cx + 16, TOP + 2.0, cz + 16), m["substrate"], g)
    bx(f"s{s}_cpul", (cx - 12, TOP + 2.0, cz - 12), (cx + 12, TOP + 5.0, cz + 12), m["alu"], g)
    p["cpu"] = (cx, TOP + 5.0, cz)
    dimms = []
    for k in range(8):
        dx = cx + (-34 + 4.5 * (k % 4)) * (1 if k < 4 else -1)
        dimms.append(bx(f"s{s}_dimm{k}", (dx - 1.2, TOP, cz - 26), (dx + 1.2, TOP + 16, cz + 26), m["cl_dimm"], g))
        gl = empty(f"s{s}_dg{k}", p["mglow"])
        bx(f"s{s}_dgm{k}", (dx - 1.3, TOP + 15, cz - 26), (dx + 1.3, TOP + 16.4, cz + 26), m["cl_mem_g"], gl)
    D.join(dimms, f"s{s}_dimms")
    show(p["mglow"], [])
    show(p["glow"], [])
    p["mem"] = (cx - 30, TOP + 16, cz)
    # the NIC / HCA card at the front edge, facing the middle
    nx = sx + sd * 50.0
    bx(f"s{s}_nicpcb", (nx - 24, TOP, -92), (nx + 24, TOP + 1.6, -2), m["cl_nic"], g)
    bx(f"s{s}_nics", (nx - 10, TOP + 1.6, -60), (nx + 10, TOP + 3.0, -40), m["substrate"], g)
    bx(f"s{s}_nicd", (nx - 6, TOP + 3.0, -56), (nx + 6, TOP + 5.0, -44), m["die"], g)
    for k in range(3):
        bx(f"s{s}_nicfin{k}", (nx - 9 + 7 * k, TOP + 5.0, -59), (nx - 7 + 7 * k, TOP + 10.0, -41), m["alu"], g)
    bx(f"s{s}_cage", (nx - 12, TOP + 1.6, -18), (nx + 12, TOP + 12, 4), m["alu"], g)
    bx(f"s{s}_xcvr", (nx - 9, TOP + 3.5, 4), (nx + 9, TOP + 10, 14), m["cold"], g)
    led = empty(f"s{s}_led", root)
    bx(f"s{s}_ledm", (nx + 6, TOP + 12, -4), (nx + 10, TOP + 13, 0), m["cl_led"], led)
    p["led"] = led
    p["nic"] = (nx, TOP + 5.0, -50)
    p["port"] = (nx, TOP + 7.0, 14)
    # PCIe switch between GPUs, NIC and CPU
    px = sx + sd * 10.0
    bx(f"s{s}_psw", (px - 8, TOP, -98), (px + 8, TOP + 2.5, -82), m["fet"], g)
    p["psw"] = (px, TOP + 2.5, -90)
    for k, gp in enumerate(p["gpu"]):
        polyline(f"s{s}_tg{k}", [(gp[0], TOP + 0.2, gp[2] + 22), (gp[0], TOP + 0.2, -90), (px, TOP + 0.2, -90)], 0.8, m["cl_cu"], g)
    polyline(f"s{s}_tn", [(px, TOP + 0.2, -90), (nx, TOP + 0.2, -90), (nx, TOP + 1.8, -60)], 1.0, m["cl_cu"], g)
    polyline(f"s{s}_tc", [(px, TOP + 0.2, -90), (px, TOP + 0.2, cz), (cx + sd * 16, TOP + 0.2, cz)], 1.0, m["cl_cu"], g)
    p["g"] = g
    return p


def gpu_out(p, k):
    """Path from GPU k's HBM out through the PCIe switch to the NIC die."""
    gp = p["gpu"][k]
    y = TOP + 1.5
    return [(gp[0], gp[1] + 1.0, gp[2]), (gp[0], y, gp[2] + 24), (gp[0], y, -90), (p["psw"][0], y, -90),
            (p["nic"][0], y, -90), (p["nic"][0], p["nic"][1] + 1.0, p["nic"][2])]


def nic_port(p):
    return [(p["nic"][0], p["nic"][1] + 1.0, p["nic"][2]), (p["nic"][0], TOP + 7.0, 0.0), p["port"]]


def cable_pts(port, dst):
    """A cable from a NIC port arcing up into a switch port at dst (x, y, z)."""
    x, y, z = port
    return [(x, y, z + 2), (x, y + 8, z + 26), (x + (dst[0] - x) * 0.5, (y + dst[1]) * 0.55, z + 40),
            (dst[0], dst[1] - 6, dst[2] + 26), (dst[0], dst[1], dst[2] + 2)]


def switch(m, root, name, c, w, h, d, mt="cl_sw", nports=16):
    """An open-topped switch: floor, walls, front face of ports with LEDs, a big ASIC with a glow
    slab, SerDes traces from the ASIC to the ports. Returns points dict."""
    x, y, z = c
    g = empty(name, root)
    z0, z1 = z - d / 2, z + d / 2
    D.join([bx(f"{name}_fl", (x - w / 2, y, z0), (x + w / 2, y + 2, z1), m[mt], g),
            bx(f"{name}_wl", (x - w / 2 - 2, y, z0), (x - w / 2, y + h, z1), m[mt], g),
            bx(f"{name}_wr", (x + w / 2, y, z0), (x + w / 2 + 2, y + h, z1), m[mt], g),
            bx(f"{name}_wb", (x - w / 2, y, z0 - 2), (x + w / 2, y + h, z0), m[mt], g),
            bx(f"{name}_wf", (x - w / 2, y, z1), (x + w / 2, y + h, z1 + 2), m[mt], g)], f"{name}_box")
    bx(f"{name}_pcb", (x - w / 2 + 3, y + 2, z0 + 3), (x + w / 2 - 3, y + 3.5, z1 - 3), m["cl_pcb"], g)
    aw = min(40.0, w * 0.32)
    bx(f"{name}_as", (x - aw / 2, y + 3.5, z - aw / 2 - 6), (x + aw / 2, y + 6, z + aw / 2 - 6), m["substrate"], g)
    bx(f"{name}_ad", (x - aw / 3, y + 6, z - aw / 3 - 6), (x + aw / 3, y + 9, z + aw / 3 - 6), m["die"], g)
    glow = empty(f"{name}_ag", root)
    bx(f"{name}_agm", (x - aw / 3 + 1, y + 9, z - aw / 3 - 5), (x + aw / 3 - 1, y + 9.5, z + aw / 3 - 7), m["cl_asic_g"], glow)
    show(glow, [])
    ports, leds = [], empty(f"{name}_leds", root)
    pp = []
    for i in range(nports):
        px = x - w / 2 + 10 + (w - 20) * i / max(1, nports - 1)
        pp.append(bx(f"{name}_p{i}", (px - 3.5, y + 6, z1 + 2), (px + 3.5, y + 14, z1 + 3), m["cl_port"], g))
        bx(f"{name}_l{i}", (px - 1.5, y + 16, z1 + 2), (px + 1.5, y + 18, z1 + 3), m["cl_led"], leds)
        ports.append((px, y + 10, z1 + 3))
        polyline(f"{name}_t{i}", [(x + (px - x) * 0.25, y + 3.7, z + aw / 2 - 6), (px, y + 3.7, z1 - 4)], 0.5, m["cl_cu"], g)
    D.join(pp, f"{name}_ports")
    for k in range(4):
        fx = x - w / 2 + w * (k + 0.5) / 4
        bx(f"{name}_fan{k}", (fx - w / 10, y + 2, z0 + 3), (fx + w / 10, y + h - 2, z0 + 9), m["dark"], g)
    return {"g": g, "glow": glow, "leds": leds, "ports": ports, "asic": (x, y + 9.5, z - 6),
            "top": (x, y + h, z)}


def cluster(m, root, sw=True):
    """Two servers and (optionally) one switch with a cable from each NIC. Returns points."""
    kit_mats(m)
    out = {"srv": [server(m, root, s) for s in (0, 1)]}
    if sw:
        S = switch(m, root, "sw", SW, SW_W, SW_H, SW_D)
        out["sw"] = S
        out["cab"] = []
        for s, p in enumerate(out["srv"]):
            dst = S["ports"][6 if s == 0 else 9]
            pts = cable_pts(p["port"], dst)
            polyline(f"cab{s}", pts, 1.6, m["cl_fiber"], root)
            out["cab"].append(pts)
    return out


def gpu_to_gpu(cl, k_src=0, k_dst=0, s_src=0):
    """GPU on server s_src out through its NIC, cable, switch ASIC, other cable, into the far GPU."""
    a, b = cl["srv"][s_src], cl["srv"][1 - s_src]
    S = cl["sw"]
    ca, cb = cl["cab"][s_src], cl["cab"][1 - s_src]
    return (gpu_out(a, k_src) + nic_port(a)[1:] + ca[1:] + [S["asic"]] + list(reversed(cb))[:-1]
            + list(reversed(nic_port(b)))[1:] + list(reversed(gpu_out(b, k_dst)))[1:])


# ---- the bench hero: a giant cut-open chip ------------------------------------------------


def hero(m, root, name, x0, x1, z0, z1, blocks, y0=0.0):
    """A huge chip cut open along its front edge (z1): BGA balls, a substrate with copper layers,
    the die with metal-stack stripes on the cut face, and functional blocks on top. `blocks` is a
    list of (key, bx0, bx1, bz0, bz1, mat, h, glow_mat or None). Returns (group, pts, glows)."""
    from sand_overview import ball
    g = empty(name, root)
    balls = [ball(f"{name}_b{i}", (x0 + 4 + i * (x1 - x0 - 8) / 13, y0 + 1.0, z1 - 2.0), 1.4, m["solder"], g, 10)
             for i in range(14)]
    D.join(balls, f"{name}_bga")
    bx(f"{name}_sub", (x0, y0 + 2.0, z0), (x1, y0 + 7.0, z1), m["substrate"], g)
    for k in range(3):
        yy = y0 + 3.0 + 1.3 * k
        bx(f"{name}_cu{k}", (x0, yy, z0), (x1, yy + 0.35, z1 + 0.15), m["copper"], g)
    ty = y0 + 12.0
    bx(f"{name}_die", (x0 + 4, y0 + 7.0, z0 + 4), (x1 - 4, ty, z1), m["die"], g)
    for k in range(5):
        yy = y0 + 9.0 + 0.5 * k
        bx(f"{name}_ms{k}", (x0 + 4, yy, z1 - 0.3), (x1 - 4, yy + 0.2, z1 + 0.1), m["copper"], g)
    pts, glows = {"top": ((x0 + x1) / 2, ty, (z0 + z1) / 2)}, {}
    for key, a, b, c, d, mt, h, gm in blocks:
        bx(f"{name}_{key}", (a, ty, c), (b, ty + h, d), m[mt], g)
        pts[key] = ((a + b) / 2, ty + h, (c + d) / 2)
        if gm:
            ge = empty(f"{name}_{key}_g", root)
            bx(f"{name}_{key}_gm", (a + 0.6, ty + h, c + 0.6), (b - 0.6, ty + h + 0.3, d - 0.6), m[gm], ge)
            show(ge, [])
            glows[key] = ge
    pts["ty"] = ty
    return g, pts, glows


def hero_mats(m):
    kit_mats(m)
    if "hr_blue" in m:
        return
    m["hr_blue"] = mat("hr_blue", (0.30, 0.42, 0.62), metal=0.4, rough=0.35)
    m["hr_green"] = mat("hr_green", (0.22, 0.48, 0.40), metal=0.4, rough=0.35)
    m["hr_mag"] = mat("hr_mag", (0.55, 0.32, 0.50), metal=0.4, rough=0.35)
    m["hr_gold"] = mat("hr_gold", (0.58, 0.48, 0.22), metal=0.4, rough=0.35)
    m["hr_serdes"] = mat("hr_serdes", (0.20, 0.22, 0.28), metal=0.6, rough=0.3)
    m["hr_sram"] = mat("hr_sram", (0.32, 0.30, 0.40), metal=0.5, rough=0.3)
    m["hr_g_blue"] = mat("hr_g_blue", (0.35, 0.65, 1.0), emit=(0.30, 0.60, 1.0), strength=0.6)
    m["hr_g_green"] = mat("hr_g_green", (0.35, 1.0, 0.60), emit=(0.30, 1.0, 0.55), strength=0.6)
    m["hr_g_amber"] = mat("hr_g_amber", (1.0, 0.70, 0.25), emit=(1.0, 0.65, 0.20), strength=0.6)
    m["hr_g_red"] = mat("hr_g_red", (1.0, 0.30, 0.20), emit=(1.0, 0.25, 0.15), strength=0.6)


def hero_cage(m, g, name, x0, y0, z0, z1, n=2):
    """OSFP-style cages standing off the hero's right edge, open toward +x."""
    out = []
    zz = (z1 - z0) / n
    for k in range(n):
        a, b = z0 + k * zz + 2, z0 + (k + 1) * zz - 2
        D.join([bx(f"{name}{k}_f", (x0, y0, a), (x0 + 30, y0 + 0.6, b), m["alu"], g),
                bx(f"{name}{k}_t", (x0, y0 + 11, a), (x0 + 30, y0 + 11.6, b), m["alu"], g),
                bx(f"{name}{k}_s", (x0, y0, a), (x0 + 30, y0 + 11.6, a + 0.6), m["alu"], g)], f"{name}{k}")
        bx(f"{name}{k}_m", (x0 + 4, y0 + 2, a + 2), (x0 + 36, y0 + 9, b - 2), m["cold"], g)
        out.append((x0 + 20, y0 + 12, (a + b) / 2))
    return out


# ---- the link lens (InfiniBand credits) ---------------------------------------------------

LZ = 90.0  # the lens floats in front of the cluster
LY = 40.0


def lens(m, root):
    g = empty("lens", root)
    pts = {"tx": [], "rx": []}
    bx("lens_plate", (-120, LY - 6, LZ - 22), (120, LY - 4, LZ + 22), m["dark"], g)
    slots = {"tx": [], "rx": []}
    for key, x0 in (("tx", -110.0), ("rx", 50.0)):
        bx(f"lens_{key}", (x0, LY - 4, LZ - 18), (x0 + 60, LY - 2, LZ + 18), m["cl_sw"], g)
        for i in range(6):
            sx0 = x0 + 4 + 9 * i
            bx(f"lens_{key}s{i}", (sx0, LY - 2, LZ - 10), (sx0 + 7, LY + 4, LZ + 10), m["cl_slot"], g)
            fe = empty(f"lens_{key}f{i}", root)
            bx(f"lens_{key}fm{i}", (sx0 + 0.5, LY + 4, LZ - 9.5), (sx0 + 6.5, LY + 5, LZ + 9.5), m["cl_full"], fe)
            slots[key].append(fe)
            pts[key].append((sx0 + 3.5, LY + 5, LZ))
    polyline("lens_wire", [(-50, LY + 2, LZ - 4), (50, LY + 2, LZ - 4)], 1.2, m["cl_fiber"], g)
    polyline("lens_back", [(50, LY + 2, LZ + 6), (-50, LY + 2, LZ + 6)], 0.6, m["cl_fiber"], g)
    return g, slots, pts


def build():
    m, root = C.setup(SLUG, len(BEATS))
    cl = cluster(m, root)
    A, B, S = cl["srv"][0], cl["srv"][1], cl["sw"]
    lg, slots, lp = lens(m, root)
    mg1 = empty("mg1", root)
    C.magnify(m, mg1, cl["cab"][0][2], (-60.0, LY + 4, LZ - 20), r=5.0)
    show(mg1, [(F(1, 0), F(2, 0))])
    show(lg, [(F(1, 0), F(2, 0))])
    # the hero: the HCA cut open on the bench in front
    hero_mats(m)
    blocks = [("pcie", -86, -60, 154, 206, "hr_gold", 1.6, None),
              ("xport", -56, -16, 154, 178, "hr_blue", 2.0, "hr_g_blue"),
              ("pkt", -12, 20, 154, 206, "hr_green", 1.8, "hr_g_green")]
    for i in range(6):
        blocks.append((f"cb{i}", -56 + 6.8 * i, -50.5 + 6.8 * i, 182, 206, "hr_sram", 1.4, "hr_g_amber"))
    for i in range(8):
        blocks.append((f"sd{i}", 26, 54, 153 + 6.6 * i, 158.5 + 6.6 * i, "hr_serdes", 2.4, None))
    hg, hp, hgl = hero(m, root, "hca", -90.0, 60.0, 150.0, 210.0, blocks)
    cages = hero_cage(m, hg, "hcage", 60.0, 2.0, 150.0, 210.0)
    from power_vrm_detail import present
    present(hg, [(F(0, 0.45), F(2, 0))])
    mg2 = empty("mg2", root)
    C.magnify(m, mg2, A["nic"], (-80.0, hp["ty"] + 2, 160.0), r=5.0, name="mag_hca")
    show(mg2, [(F(0, 0.45), F(1, 0))])
    ty = hp["ty"] + 3.0
    # beat 0 (second half): data from PCIe through transport, packet engine, SerDes, out the cage
    run(root, "h0", [(-73, ty, 180), hp["xport"][:1] + (ty, 166), (hp["pkt"][0], ty, 180), (40, ty, 180), cages[1]],
        8, 1.2, m["sig"], 0, 0.5, 0.85, 40)
    for k in ("xport", "pkt"):
        show(hgl[k], [(F(0, 0.5), F(1, 0)), (F(2, 0), F(2, 0.5))])
    # beat 1: credit buffers on the HCA fill as the lens slots fill
    for i in range(6):
        show(hgl[f"cb{i}"], [(F(1, 0.16 + 0.13 * i), F(2, 0))])
    bars_g = empty("bars", root)
    kit_mats(m)
    rates = (100, 200, 400, 800)
    btops = []
    for i, r in enumerate(rates):
        x0 = -60.0 + 32.0 * i
        bx(f"bar{i}", (x0, 0.0, LZ - 8), (x0 + 18, r * 0.13, LZ + 8), m["cl_bar"], bars_g)
        btops.append((x0 + 9, r * 0.13 + 2, LZ))
    show(bars_g, [(F(4, 0), F(5, 0))])

    # beat 0: traffic both ways on the cables, LEDs blink
    for s in (0, 1):
        run(root, f"b0_out{s}", nic_port(cl["srv"][s]) + cl["cab"][s][1:], 8, 1.4, m["sig"], 0, 0.05, 0.85, 45)
    blink(S["leds"], 0, [0, 2, 4, 6], n=8)
    # beat 1: credits come back, packets go out one per credit; rx slots fill, drain
    for i in range(6):
        run(root, f"cr{i}", [(50, LY + 3, LZ + 6), (-50, LY + 3, LZ + 6)], 1, 1.2, m["cl_credit"], 1, 0.02 + 0.13 * i, 0.1, 22)
        run(root, f"pk{i}", [lp["tx"][5 - i], (-50, LY + 3, LZ - 4), (50, LY + 3, LZ - 4), lp["rx"][i]], 1, 1.6, m["bit"], 1, 0.08 + 0.13 * i, 0.2, 26)
        show(slots["tx"][5 - i], [(F(1, 0), F(1, 0.08 + 0.13 * i))])
        show(slots["rx"][i], [(F(1, 0.16 + 0.13 * i), F(2, 0))])
    # beat 2: GPU to GPU, CPUs dark, GPU dies glow
    run(root, "b2_g2g", gpu_to_gpu(cl, 0, 1), 14, 1.6, m["e_blue"], 2, 0.05, 0.6, 90)
    run(root, "b2_back", gpu_to_gpu(cl, 3, 2, s_src=1), 8, 1.4, m["e_blue"], 2, 0.15, 0.6, 90)
    for s in (0, 1):
        show(cl["srv"][s]["glow"], [(F(2, 0), F(3, 0)), (F(3, 0.6), F(4, 0))])
    # beat 3: SHARP: partial sums up, one result back
    for s in (0, 1):
        up = nic_port(cl["srv"][s]) + cl["cab"][s][1:] + [S["asic"]]
        run(root, f"sh_up{s}", up, 6, 1.4, m["h_amber"], 3, 0.0, 0.35, 50)
        run(root, f"sh_dn{s}", list(reversed(up)), 4, 2.4, m["sig"], 3, 0.45, 0.7, 50)
    show(S["glow"], [(F(3, 0.25), F(3, 0.75))])
    rise(root, "sh_heat", S["asic"], 5, 0.8, m["heat"], 3, 0.25, 0.65, 18.0, 30, (6.0, 6.0))
    # beat 4: all lit
    blink(S["leds"], 4, [0, 1, 3, 4, 6, 7], n=8)
    for s in (0, 1):
        blink(cl["srv"][s]["led"], 4, [0, 2, 4, 6], n=8)

    from sand_overview import label
    for t, pt in (("InfiniBand switch", S["top"]), ("HCA (InfiniBand NIC)", A["nic"]), ("4 GPUs + HBM", A["gpu"][0]),
                  ("GPU server", B["gpu"][1])):
        label(t, pt, root, [(F(0, 0), F(0, 0.45))])
    for t, pt in (("HCA cut open: PCIe in", hp["pcie"]), ("RDMA transport engine", hp["xport"]),
                  ("packet engine", hp["pkt"]), ("SerDes lanes", hp["sd4"]), ("OSFP cage", cages[1])):
        label(t, pt, root, [(F(0, 0.5), F(1, 0))])
    C.tags(root, {
        1: [("credit buffers on the HCA", hp["cb3"]), ("sender buffer", lp["tx"][2]), ("receiver: free slots = credits", lp["rx"][3]),
            ("credits flow back", (0.0, LY + 4, LZ + 8)), ("no packet is ever dropped", (0.0, LY + 4, LZ - 6))],
        2: [("read from GPU memory", A["gpu"][0]), ("switch: < 1 us", S["asic"]), ("written into far GPU", B["gpu"][1]),
            ("CPU not involved", A["cpu"])],
        3: [("partial sums in", cl["cab"][0][2]), ("switch ASIC adds them", S["asic"]), ("one result back", cl["cab"][1][2])],
        4: [("EDR 100G", btops[0]), ("HDR 200G", btops[1]), ("NDR 400G", btops[2]), ("XDR 800G", btops[3]),
            ("NVDA (Mellanox), ANET, AVGO", S["top"])],
    })
    C.done(SLUG, BEATS, [
        [(0.0, frame((0.0, 30.0, -90.0), 470.0, 0.30, 0.55, pad=1.0)),
         (0.5, frame((-10.0, 12.0, 180.0), 170.0, 0.25, 0.70))],
        frame((0.0, 25.0, 145.0), 260.0, 0.0, 0.70),
        frame((0.0, 30.0, -100.0), 440.0, -0.25, 0.75, pad=1.0),
        frame((0.0, 60.0, -40.0), 300.0, 0.20, 0.40),
        frame((0.0, 40.0, -20.0), 420.0, 0.35, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
