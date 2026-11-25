"""TRM_SCALE_UP: the Terms-tab overview for scale-up vs scale-out networking.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_scale_up.py

Writes assets/term_TRM_SCALE_UP.glb. Captions live in specs/terms/TRM_SCALE_UP.json (same beat count).

A row of three NVL72-style racks. Inside each, compute trays and NVSwitch trays are tied by a copper
cable spine at the back: that is the scale-up domain (green). Over the row, every rack's NICs run
fibre up to a leaf switch, and the leaves to a spine switch: that is the scale-out network (pink).
Bars compare the bandwidth each GPU gets on the two networks.

Beats:
  0 row       three racks, each one scale-up domain, joined by the scale-out network above
  1 up        inside one rack: tray to switch tray over the copper spine, dense and fast
  2 out       rack to rack: NIC, fibre, leaf, spine, leaf, NIC; fewer, slower beads
  3 numbers   per-GPU bandwidth: 1.8 TB/s scale-up vs 100 GB/s (800G) scale-out
  4 markets   both running at once; who sells what
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import bx, empty, show, mat  # noqa: E402
from sand_overview import F  # noqa: E402
from power_vrm_detail import frame, run, blink, polyline, present, join  # noqa: E402
import net_server_detail as S  # noqa: E402

SLUG = "TRM_SCALE_UP"
BEATS = [
    ("Two networks: scale-up inside the rack, scale-out between racks",
     "An AI cluster has two separate fabrics. Scale-up ties a group of accelerators (here 72 GPUs in one rack) together "
     "with very fast, memory-like links so they behave as one machine. Scale-out connects thousands of those groups "
     "across the building with Ethernet or InfiniBand. Each GPU is wired to both."),
    ("Scale-up: copper links, memory-speed, a few metres",
     "Inside the rack every GPU links through NVSwitch trays over a copper cable spine (NVLink, or UALink in open "
     "designs). GPUs load and store directly into each other's memory with sub-microsecond latency. Copper keeps it "
     "cheap and low-power, but it only reaches a couple of metres, which caps the domain at roughly a rack."),
    ("Scale-out: NICs, optics and switch tiers across the hall",
     "To leave the rack, data goes through a NIC (one per GPU), an optical transceiver and fibre to a leaf switch, up to "
     "a spine and back down. It is packet networking with RDMA, so it reaches any of 100,000 GPUs, at the cost of more "
     "hops, more latency and less bandwidth per GPU."),
    ("Each GPU gets about 18x more bandwidth on scale-up",
     "A Blackwell GPU has 1.8 TB/s of NVLink but one 800 Gb/s NIC, about 100 GB/s, for scale-out. So model work is split "
     "to match: tensor and expert parallelism (chatty, every layer) stays inside the scale-up domain, data and pipeline "
     "parallelism (larger, rarer transfers) cross the scale-out network."),
    ("Two markets: a contested new one and a big established one",
     "Scale-up is newer and fought over: Nvidia's proprietary NVLink against open UALink and Ethernet-based scale-up, "
     "with retimers and copper cables in between. Scale-out is the existing Ethernet/InfiniBand switch, NIC and optics "
     "market, and companies report the two separately. Related: NVDA, AVGO, ALAB, ANET, MRVL."),
]

RXS = (-300.0, -75.0, 150.0)  # rack left edges; 150 wide, front z = 0, back z = -170
RW = 150.0
TRAY_H, TRAY_Y0 = 12.0, 30.0
TOP = TRAY_Y0 + 27 * 14.0 + 10.0
LEAF_Y = TOP + 60.0
SPINE_Y = TOP + 150.0
BAR_X, BAR_Z = 420.0, -60.0


def mats(m):
    m["rack"] = mat("su_rack", (0.18, 0.19, 0.22), metal=0.7, rough=0.45)
    m["tray"] = mat("su_tray", (0.34, 0.36, 0.40), metal=0.8, rough=0.4)
    m["swtray"] = mat("su_swtray", (0.14, 0.30, 0.26), metal=0.6, rough=0.4)
    m["dom"] = mat("su_dom", (0.30, 1.0, 0.40), emit=(0.30, 1.0, 0.40), strength=1.2)
    m["bar_n"] = mat("su_bar_n", (0.20, 0.55, 0.28), metal=0.2, rough=0.5)
    m["bar_p"] = mat("su_bar_p", (0.55, 0.20, 0.48), metal=0.2, rough=0.5)
    m["cap_n"] = mat("su_cap_n", (0.40, 1.0, 0.45), emit=(0.30, 1.0, 0.40), strength=2.0)
    m["cap_p"] = mat("su_cap_p", (1.0, 0.35, 0.85), emit=(1.0, 0.30, 0.85), strength=2.0)


def tray_y(i):
    return TRAY_Y0 + i * (TRAY_H + 2.0)


def rack(m, root, x0, r):
    g = empty(f"rk{r}", root)
    x1 = x0 + RW
    parts = [bx(f"rk{r}_p{i}", (x, 0.0, z), (x + 6.0, TOP, z + 6.0), m["rack"], g)
             for i, (x, z) in enumerate([(x0 - 6, -6), (x1, -6), (x0 - 6, -176), (x1, -176)])]
    parts += [bx(f"rk{r}_top", (x0 - 6, TOP, -176), (x1 + 6, TOP + 6, 0), m["rack"], g),
              bx(f"rk{r}_base", (x0 - 6, -4, -176), (x1 + 6, 0, 0), m["rack"], g)]
    join(parts, f"rk{r}_frame")
    kinds = ["c"] * 8 + ["s"] * 9 + ["c"] * 10
    body, fronts = [], []
    for i, k in enumerate(kinds):
        y = tray_y(i)
        body.append(bx(f"rk{r}_t{i}", (x0, y, -165.0), (x1, y + TRAY_H, 0.0), m["tray" if k == "c" else "swtray"], g))
        if k == "c":
            for j in range(4):
                xx = x0 + 10.0 + 28.0 * j
                fronts.append(bx(f"rk{r}_g{i}{j}", (xx, y + 3.0, 0.0), (xx + 20.0, y + TRAY_H - 3.0, 1.0), m["die"], g))
            # NIC cages on the right of the face
            fronts.append(bx(f"rk{r}_n{i}", (x0 + 124.0, y + 3.0, 0.0), (x0 + 144.0, y + TRAY_H - 3.0, 1.5), m["alu"], g))
        else:
            for j in range(2):
                xx = x0 + 22.0 + 60.0 * j
                fronts.append(bx(f"rk{r}_s{i}{j}", (xx, y + 3.0, 0.0), (xx + 40.0, y + TRAY_H - 3.0, 1.0), m["sw_die"], g))
    join(body, f"rk{r}_trays")
    join(fronts, f"rk{r}_fronts")
    spine_x = [x0 + 18.0 + 23.0 * j for j in range(6)]
    cab = [polyline(f"rk{r}_sp{j}", [(sx, tray_y(0), -172.0), (sx, tray_y(26) + TRAY_H, -172.0)], 2.2, m["copper"], g)
           for j, sx in enumerate(spine_x)]
    for i in range(27):
        y = tray_y(i) + TRAY_H / 2
        for j, sx in enumerate(spine_x):
            cab.append(bx(f"rk{r}_st{i}_{j}", (sx - 1.0, y - 0.8, -172.0), (sx + 1.0, y + 0.8, -165.0), m["copper"], g))
    join(cab, f"rk{r}_spine")
    # fibre bundle from the NIC column up to the leaf
    polyline(f"rk{r}_fib", [(x0 + 146.0, tray_y(2), 4.0), (x0 + 146.0, TOP + 10.0, 4.0), (x0 + RW / 2, LEAF_Y - 2.0, -40.0)],
             2.0, m["fiber"], g)
    return g, kinds, spine_x


def switch_box(m, root, name, c, w, h=18.0, d=60.0, ports=16):
    g = empty(name, root)
    x, y, z = c
    parts = [bx(f"{name}_b", (x - w / 2, y, z - d), (x + w / 2, y + h, z), m["switch"], g)]
    for i in range(ports):
        px = x - w / 2 + 6.0 + (w - 12.0) * i / ports
        parts.append(bx(f"{name}_p{i}", (px, y + 5.0, z), (px + (w - 12.0) / ports - 2.0, y + 13.0, z + 0.8), m["port"], g))
    join(parts, f"{name}_body")
    return g, (x, y + h, z - d / 2)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m.update(S.materials())
    mats(m)
    racks = [rack(m, root, x0, r) for r, x0 in enumerate(RXS)]
    floor = empty("floor", root)
    bx("fl", (-420.0, -8.0, -260.0), (560.0, -4.0, 120.0), m["floor"], floor)
    leaves = [switch_box(m, root, f"leaf{r}", (x0 + RW / 2, LEAF_Y, -10.0), 120.0) for r, x0 in enumerate(RXS)]
    spine = switch_box(m, root, "spine", (0.0, SPINE_Y, -10.0), 220.0, ports=24)
    up = empty("uplinks", root)
    for r, (g, lt) in enumerate(leaves):
        for j in (-1, 1):
            polyline(f"ul{r}{j}", [(lt[0] + 30.0 * j, LEAF_Y + 18.0, -30.0), (lt[0] + 30.0 * j, LEAF_Y + 60.0, -30.0),
                                   (40.0 * j + (lt[0]) * 0.3, SPINE_Y - 2.0, -30.0)], 1.4, m["fiber_aqua"], up)
    # the scale-up domain outline: a faint glowing frame round each rack's front
    doms = []
    for r, x0 in enumerate(RXS):
        dg = empty(f"dom{r}", root)
        for a, b in (((x0 - 8, -2, 2), (x0 + RW + 8, 2, 4)), ((x0 - 8, TOP + 4, 2), (x0 + RW + 8, TOP + 8, 4)),
                     ((x0 - 8, -2, 2), (x0 - 4, TOP + 8, 4)), ((x0 + RW + 4, -2, 2), (x0 + RW + 8, TOP + 8, 4))):
            bx(f"dom{r}_{a[0]}_{a[1]}_{b[0]}", a, b, m["dom"], dg)
        doms.append(dg)
        show(dg, [(F(0, 0.3), F(2, 0)), (F(4, 0.0), F(5, 0))])

    # bars
    bar = empty("bars", root)
    sc = 0.12
    bt = {}
    for k, (nm, val, mt, cap) in enumerate((("up", 1800.0, "bar_n", "cap_n"), ("out", 100.0, "bar_p", "cap_p"))):
        x = BAR_X + 60.0 * k
        h = val * sc
        bx(f"b_{nm}", (x, 0.0, BAR_Z - 18.0), (x + 36.0, h, BAR_Z + 18.0), m[mt], bar)
        bx(f"b_{nm}_c", (x - 1.0, h, BAR_Z - 19.0), (x + 37.0, h + 3.0, BAR_Z + 19.0), m[cap], bar)
        bt[nm] = (x + 18.0, h + 3.0, BAR_Z + 18.0)
    present(bar, [(F(3, 0.0), F(5, 0))])

    def up_path(r, src, dst, lane):
        x0 = RXS[r]
        sx = racks[r][2][lane % 6]
        ys, yd = tray_y(src) + TRAY_H / 2, tray_y(dst) + TRAY_H / 2
        return [(x0 + 25.0 + 28.0 * lane, ys, 2.0), (x0 + 25.0 + 28.0 * lane, ys, -150.0), (sx, ys, -176.0), (sx, yd, -176.0),
                (x0 + RW / 2, yd, -150.0), (x0 + RW / 2, yd, 2.0)]

    # scale-up beads: every rack in beats 0 and 4, rack 0 dense in beat 1
    for r in range(3):
        for i, (src, dst) in enumerate(((2, 10), (22, 14), (5, 16), (25, 12))):
            bl = [0, 1, 4] if r == 0 else [0, 4]
            run(root, f"up{r}{i}", up_path(r, src, dst, i), 8, 4.0, m["nvl"], bl, 0.05 + 0.05 * i, 0.8, 40)

    def out_path(ra, rb, ta, tb):
        a, b = RXS[ra], RXS[rb]
        la, lb = leaves[ra][1], leaves[rb][1]
        return [(a + 134.0, tray_y(ta) + 6.0, 3.0), (a + 146.0, tray_y(ta) + 6.0, 5.0), (a + 146.0, TOP + 10.0, 5.0),
                (la[0], LEAF_Y + 4.0, -10.0), (la[0], LEAF_Y + 22.0, -30.0), (0.0, SPINE_Y + 10.0, -30.0),
                (lb[0], LEAF_Y + 22.0, -30.0), (lb[0], LEAF_Y + 4.0, -10.0), (b + 146.0, TOP + 10.0, 5.0),
                (b + 146.0, tray_y(tb) + 6.0, 5.0), (b + 134.0, tray_y(tb) + 6.0, 3.0)]

    run(root, "out02", out_path(0, 2, 3, 22), 5, 3.0, m["pkt"], [2, 4], 0.0, 0.55, 90)
    run(root, "out21", out_path(2, 1, 6, 24), 4, 3.0, m["pkt"], [2, 4], 0.15, 0.6, 90)
    run(root, "out10", out_path(1, 0, 20, 4), 4, 3.0, m["pkt"], [0, 2], 0.3, 0.6, 90)
    # switch port LEDs
    for r, (g, lt) in enumerate(leaves + [spine]):
        lg = empty(f"swled{r}", root)
        bx(f"swledm{r}", (lt[0] - 20.0, lt[1] - 4.0, -9.0), (lt[0] + 20.0, lt[1] - 2.0, -8.0), m["led_amb"], lg)
        blink(lg, 2, [0, 2, 4, 6], n=8, on=0.5)

    x1 = RXS[1]
    C.tags(root, {
        0: [("scale-up domain: one rack", (RXS[0] + RW / 2, TOP + 8.0, 4.0)), ("scale-out: leaf + spine", spine[1]),
            ("72 GPUs act as one", (x1 + RW / 2, tray_y(20), 2.0))],
        1: [("copper spine: NVLink/UALink", (racks[0][2][2], tray_y(20), -176.0)), ("NVSwitch trays", (RXS[0] + RW / 2, tray_y(12), -165.0)),
            ("load/store into GPU memory", (RXS[0] + RW / 2, tray_y(4), -165.0))],
        2: [("NIC per GPU, optics", (RXS[0] + 146.0, tray_y(3), 5.0)), ("leaf switch", leaves[0][1]), ("spine switch", spine[1]),
            ("Ethernet / InfiniBand, RDMA", (RXS[2] + RW / 2, LEAF_Y + 40.0, -30.0))],
        3: [("scale-up: 1.8 TB/s per GPU", bt["up"]), ("scale-out: ~100 GB/s (800G)", bt["out"]),
            ("tensor/expert parallel stays in", (x1 + RW / 2, tray_y(14), 2.0))],
        4: [("scale-up: NVDA vs UALink, ALAB", (RXS[0] + RW / 2, tray_y(8), 2.0)), ("scale-out: AVGO ANET MRVL NVDA", spine[1])],
    })
    C.done(SLUG, BEATS, [
        frame((40.0, 260.0, -80.0), 900.0, 0.30, 0.22),
        frame((RXS[0] + RW / 2, 210.0, -100.0), 520.0, 2.7, 0.22),
        frame((0.0, 380.0, -40.0), 760.0, 0.20, 0.22),
        frame((330.0, 140.0, -60.0), 420.0, 0.35, 0.15),
        frame((40.0, 300.0, -80.0), 920.0, 0.15, 0.20),
    ], root)


if __name__ == "__main__":
    build()
