"""TRM_CXL on the shared GPU board: a CXL memory expander (controller + DDR5 chips) wired to the
package over PCIe lanes, its controller cut open huge on the bench, and a pooled memory box behind.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_cxl.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import blink, frame, rise, run  # noqa: E402

SLUG = "TRM_CXL"
BEATS = [
    ("A processor's memory is capped by the slots wired to it",
     "A CPU or GPU can only use the DRAM wired straight to its memory channels: a fixed number of DIMM slots, or the "
     "HBM stacks inside the GPU package. AI servers often run out of memory before they run out of compute."),
    ("CXL runs a memory protocol over ordinary PCIe lanes",
     "Compute Express Link reuses the PCIe physical wires and slots but adds a load/store protocol (CXL.mem). The "
     "processor reads and writes the far memory with normal instructions, at cache-line size, instead of moving blocks "
     "through a driver like a disk or NIC."),
    ("An expander card: CXL controller in front of plain DDR5",
     "The card's controller chip takes CXL requests off the PCIe PHY, translates them in its CXL.mem engine, and "
     "drives DDR5 chips through its own memory controller. To the server it shows up as extra memory with no CPU of "
     "its own, often terabytes per box."),
    ("It is slower than local DRAM, but far faster than flash",
     "A local DRAM load takes roughly 100 ns. Going out over CXL adds about 100-200 ns more, since the request crosses "
     "the link and a second controller. That is still around a hundred times faster than an SSD, so it suits big KV "
     "caches, embeddings and in-memory databases."),
    ("Pooling: one memory box shared by many servers",
     "With CXL 2.0/3.x switches, a rack-level box of DRAM can be carved up among several hosts and reassigned as jobs "
     "change, so memory that would sit idle in one server can be used by another. This cuts stranded memory, a large "
     "cost in big fleets."),
    ("Makers: Astera Labs (ALAB), Marvell (MRVL), Micron (MU), Samsung (005930.KS)",
     "Astera Labs (ALAB) Leo and Marvell (MRVL) Structera make CXL memory controllers; Micron (MU), Samsung (005930.KS) "
     "and SK Hynix (000660.KS) sell CXL memory modules. CPUs from Intel (INTC) and AMD (AMD) support CXL natively."),
]

CTL = (195.0, 0.0, -155.0)  # expander controller on the board
DDR = [(170.0, 0.0, -135.0), (170.0, 0.0, -175.0), (220.0, 0.0, -135.0), (220.0, 0.0, -175.0)]
# giant controller die on the bench
GX0, GX1, GZ0 = 158.0, 242.0, -62.0
TY = 8.0
BOX = (-100.0, 0.0, -270.0)  # pooled memory box behind the board


def mats(m):
    m["phy"] = mat("cxl_phy", (0.80, 0.62, 0.28), metal=0.6, rough=0.35)
    m["eng"] = mat("cxl_eng", (0.30, 0.42, 0.62), metal=0.4, rough=0.35)
    m["mc"] = mat("cxl_mc", (0.35, 0.55, 0.40), metal=0.4, rough=0.35)
    m["dram"] = mat("cxl_dram", (0.08, 0.08, 0.09), rough=0.35)
    m["req"] = mat("cxl_req", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=4.0)
    m["dat"] = mat("cxl_dat", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=4.0)
    m["eng_g"] = mat("cxl_eng_g", (0.30, 0.50, 0.95), emit=(0.25, 0.45, 1.0), strength=1.0)


def giant(m, root):
    """The controller die cut open: substrate, die with PHY / CXL.mem / DDR controller blocks, and
    DDR5 chips standing either side on a card strip."""
    g = empty("giant", root)
    bx("g_pcb", (GX0 - 8.0, -1.6, GZ0 - 6.0), (GX1 + 8.0, 0.0, 0.0), m["mask"], g)
    for k in range(14):  # gold fingers on the card edge
        x = GX0 - 6.0 + k * 6.6
        bx(f"g_fing{k}", (x, 0.0, -2.5), (x + 4.0, 0.15, 0.0), m["gold"], g)
    bx("g_sub", (184.0, 0.0, -48.0), (216.0, 3.0, -8.0), m["substrate"], g)
    for k in range(10):
        D.bead(f"g_ball{k}", (186.0 + 3.0 * k, -0.2, -2.0), 0.9, m["solder"], g)
    bx("g_die", (188.0, 3.0, -44.0), (212.0, TY, -12.0), m["silicon"], g)
    pts = {}
    blocks = {"phy": (188.5, 195.0, "phy"), "eng": (196.0, 204.0, "eng"), "mc": (205.0, 211.5, "mc")}
    glow = {}
    for k, (x0, x1, mt) in blocks.items():
        bx(f"g_{k}", (x0, TY, -43.0), (x1, TY + 0.6, -13.0), m[mt], g)
        gg = empty(f"g_{k}_on", g)
        bx(f"g_{k}_on_b", (x0 + 0.5, TY + 0.6, -42.0), (x1 - 0.5, TY + 0.9, -14.0), m["eng_g"], gg)
        glow[k] = gg
        pts[k] = ((x0 + x1) / 2, TY + 0.6, -28.0)
    # DDR5 chips left and right of the controller, traces from the DDR controller
    chips = []
    for k, x in enumerate((162.0, 172.0, 228.0, 238.0)):
        for j, z in enumerate((-50.0, -28.0)):
            bx(f"g_dr{k}{j}", (x - 4.0, 0.0, z - 8.0), (x + 4.0, 2.2, z + 8.0), m["dram"], g)
            chips.append((x, 2.2, z))
    for k, c in enumerate(chips):
        C.trace(m, g, f"g_t{k}", [(c[0], 0.05, c[2]), (pts["mc"][0], 0.05, c[2]), (pts["mc"][0], 0.05, -28.0)], 0.4)
    return glow, pts, chips


def pool(m, root):
    """A rack-level memory box: chassis with DRAM sticks and a CXL switch, cables out to hosts."""
    g = empty("pool", root)
    x, _, z = BOX
    bx("pl_case", (x - 70.0, 0.0, z - 25.0), (x + 70.0, 3.0, z + 25.0), m["steel"], g)
    for k in range(16):
        xx = x - 60.0 + k * 8.0
        bx(f"pl_dimm{k}", (xx, 3.0, z - 18.0), (xx + 1.6, 14.0, z + 4.0), m["mask"], g)
        for j in range(3):
            bx(f"pl_c{k}{j}", (xx + 1.6, 5.0, z - 16.0 + 7.0 * j), (xx + 2.2, 11.0, z - 11.0 + 7.0 * j), m["dram"], g)
    bx("pl_sw", (x - 20.0, 3.0, z + 8.0), (x + 20.0, 6.0, z + 22.0), m["substrate"], g)
    bx("pl_swlid", (x - 12.0, 6.0, z + 10.0), (x + 12.0, 8.0, z + 20.0), m["alu"], g)
    hosts = []
    for k, hx in enumerate((-260.0, -170.0, 60.0)):
        bx(f"host{k}", (hx - 30.0, 0.0, -330.0), (hx + 30.0, 12.0, -300.0), m["alu"], g)
        hosts.append((hx, 12.0, -315.0))
    return g, (x, 8.0, z + 15.0), hosts


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    brd = empty("cxl_brd", root)
    ctop = C.chip(m, brd, "ctl", CTL, 20.0, 20.0, 2.0, pins=0, body="substrate")
    bx("ctl_lid", (CTL[0] - 7.0, 2.0, CTL[2] - 7.0), (CTL[0] + 7.0, 3.6, CTL[2] + 7.0), m["alu"], brd)
    ctop = (CTL[0], 3.6, CTL[2])
    ddr_tops = [C.chip(m, brd, f"ddr{k}", c, 14.0, 10.0, 1.4, pins=6) for k, c in enumerate(DDR)]
    for k, c in enumerate(DDR):
        C.trace(m, brd, f"t_ddr{k}", [(c[0], 0.0, c[2]), (CTL[0], 0.0, c[2]), (CTL[0], 0.0, CTL[2])], 0.6)
    lane = [(CTL[0] - 10.0, 0.0, CTL[2]), (145.0, 0.0, CTL[2]), (145.0, 0.0, -60.0), (60.0, 0.0, -60.0)]
    for k, dz in enumerate((-3.0, -1.0, 1.0, 3.0)):
        C.trace(m, brd, f"t_lane{k}", [(p[0], p[1], p[2] + dz) for p in lane], 0.5)
    glow, gp, chips = giant(m, root)
    C.magnify(m, root, ctop, (GX0 + 10.0, 10.0, -10.0), r=5.0)
    pg, sw, hosts = pool(m, root)

    # beat 0: the GPU's own memory works, die lit
    show(b["die_glow"], [(F(0, 0.2), F(1, 0)), (F(3, 0.0), F(4, 0))])
    # beat 1: requests ride the PCIe lanes out to the expander, data back
    up = [(p[0], 1.0, p[2] - 1.0) for p in reversed(lane)]
    run(root, "req1", up, 10, 1.8, m["req"], [1, 2], 0.0, 0.6, 50)
    run(root, "dat1", [(p[0], 1.0, p[2] + 1.0) for p in lane], 10, 1.8, m["dat"], [1, 2], 0.3, 0.9, 50)
    # beat 2: through PHY -> CXL.mem -> DDR controller -> chips on the bench
    y = TY + 2.0
    path = [(GX0 - 6.0, 1.0, -1.0), (gp["phy"][0], y, -8.0), (gp["phy"][0], y, -28.0), (gp["eng"][0], y, -28.0),
            (gp["mc"][0], y, -28.0), (gp["mc"][0], 3.0, -50.0), (chips[6][0], 3.0, -50.0)]
    run(root, "req2", path, 10, 0.8, m["req"], 2, 0.0, 0.7, 55)
    run(root, "dat2", list(reversed([(chips[1][0], 3.0, -28.0), (gp["mc"][0], y, -28.0), (gp["eng"][0], y, -28.0),
                                     (gp["phy"][0], y, -28.0), (gp["phy"][0], y, -8.0), (GX0 - 6.0, 1.0, -1.0)]))[::-1],
        8, 0.8, m["dat"], 2, 0.3, 0.9, 55)
    for k, key in enumerate(("phy", "eng", "mc")):
        show(glow[key], [(F(2, 0.1 + 0.15 * k), F(3, 0)), (F(5, 0), F(6, 0))])
    # beat 3: local HBM loop is quick, the CXL trip is longer
    pkt = pk["top"]
    run(root, "fast", [(pkt[0] - 30.0, pkt[1] + 2.0, pkt[2]), (pkt[0] + 30.0, pkt[1] + 2.0, pkt[2])], 12, 1.8, m["dat"], 3, 0.0, 0.9, 12)
    run(root, "slow", up + [(CTL[0], 4.0, CTL[2])], 6, 1.8, m["req"], 3, 0.0, 0.7, 70)
    rise(root, "ctl_heat", (CTL[0], 4.0, CTL[2]), 4, 0.6, m["h_amber"], [2, 3], 0.1, 0.9, 14.0, 40, (5.0, 5.0))
    # beat 4: pooled box, cables to hosts, blinking slices
    for k, h in enumerate(hosts + [(0.0, 2.0, -215.0)]):
        cab = [sw, (sw[0], 10.0, sw[2] + 20.0), (h[0], 10.0, sw[2] + 20.0), h]
        D.polyline(f"cab{k}", cab, 0.8, m["rubber"], pg)
        run(root, f"pl{k}", cab, 5, 1.8, m["req"] if k % 2 else m["dat"], 4, 0.05 * k, 0.8, 40)

    C.tags(root, {
        0: [("GPU package + its HBM", pk["top"]), ("fixed memory channels", (pk["top"][0] + 40.0, 2.0, pk["top"][2])),
            ("CXL memory expander", ctop)],
        1: [("x16 PCIe wires carry CXL", (145.0, 1.0, -110.0)), ("load/store, cache-line size", (100.0, 1.0, -60.0)),
            ("expander controller", ctop)],
        2: [("PCIe/CXL PHY", gp["phy"]), ("CXL.mem engine", gp["eng"]), ("DDR5 controller", gp["mc"]),
            ("plain DDR5 chips", chips[6])],
        3: [("local: ~100 ns", pk["top"]), ("CXL: +100-200 ns", ctop), ("~100x faster than SSD", ddr_tops[3])],
        4: [("pooled DRAM box", (BOX[0] - 40.0, 14.0, BOX[2])), ("CXL switch", sw), ("hosts share the pool", hosts[0])],
        5: [("ALAB Leo, MRVL Structera", gp["eng"]), ("MU, 005930.KS modules", chips[6]), ("INTC, AMD CPUs", (GX0, 0.0, -2.0))],
    })
    bc = ((GX0 + GX1) / 2, TY, GZ0 / 2)
    C.done(SLUG, BEATS, [
        frame((60.0, 0.0, -110.0), 330.0, 0.35, 0.70, pad=1.0),
        frame((120.0, 0.0, -110.0), 220.0, 0.20, 0.85, pad=1.0),
        [(0.0, frame(bc, 100.0, 0.25, 0.70)), (0.6, frame((200.0, TY, -30.0), 70.0, 0.10, 0.80))],
        frame((100.0, 0.0, -110.0), 260.0, -0.10, 0.80, pad=1.0),
        frame((-80.0, 0.0, -230.0), 380.0, 0.20, 0.75, pad=1.0),
        frame(bc, 100.0, 0.30, 0.55),
    ], root)


if __name__ == "__main__":
    build()
