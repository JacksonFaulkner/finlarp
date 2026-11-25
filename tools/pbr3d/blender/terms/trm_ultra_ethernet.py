"""TRM_ULTRA_ETHERNET: the Terms-tab overview, built on the cluster kit in trm_infiniband.py.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_ultra_ethernet.py

Two GPU servers with their lids off, each cabled to its own leaf switch, and four spine switches
above (from different vendors, in different colours) with a link from every leaf to every spine.

Beats:
  0 fabric   leaf-spine Ethernet built from several vendors' switches
  1 ecmp     today: a whole flow is hashed onto one path; two flows collide on one spine
  2 spray    Ultra Ethernet sprays each flow's packets over every path; the NIC reorders them
  3 loss     a congested spine trims a packet; the receiver asks for just that one again, fast
  4 spec     UEC 1.0 (2025), open spec, many suppliers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run, blink, rise, polyline  # noqa: E402
import trm_infiniband as K  # noqa: E402

SLUG = "TRM_ULTRA_ETHERNET"
BEATS = [
    ("Ultra Ethernet rebuilds Ethernet's transport for AI clusters",
     "Big AI clusters wire every server to leaf switches and every leaf to every spine, so there are many equal paths "
     "between any two GPUs. Ultra Ethernet is an open specification from the Ultra Ethernet Consortium that keeps "
     "ordinary Ethernet switches and cables but replaces the transport the NICs use on top."),
    ("The old problem: one flow, one path",
     "Classic Ethernet load balancing (ECMP) hashes each flow onto a single path so its packets stay in order. AI "
     "traffic is a few huge flows, so two of them can land on the same spine link while the others sit idle. That link "
     "congests and the whole training step waits for the slowest transfer."),
    ("Packet spraying: every path at once",
     "The Ultra Ethernet transport sprays the packets of one flow across all the paths. They arrive out of order, and "
     "the receiving NIC writes each one straight to its place in memory, so order no longer matters. The fabric's links "
     "fill evenly instead of one running hot."),
    ("Faster congestion control and loss recovery",
     "When a switch queue overflows it can trim a packet to its header instead of silently dropping it. The receiver "
     "sees the gap at once and asks for just that packet again, and senders slow down using signals from both ends. "
     "Recovering in microseconds rather than waiting on a timeout is how it aims to match InfiniBand."),
    ("An open spec with many suppliers",
     "Version 1.0 was published in 2025 and switch and NIC makers are shipping compliant parts. The pitch is "
     "InfiniBand-class performance with Ethernet's multi-vendor supply and tools. Related: Broadcom (AVGO), Arista "
     "(ANET), AMD (AMD), Cisco (CSCO), Marvell (MRVL), Nvidia (NVDA)."),
]

LEAF_X = (-150.0, 150.0)
SPINE_X = (-135.0, -45.0, 45.0, 135.0)
SPY = 170.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    cl = K.cluster(m, root, sw=False)
    A, B = cl["srv"]
    leaves = [K.switch(m, root, f"leaf{i}", (x, 70.0, -70.0), 120.0, 22.0, 90.0, nports=10) for i, x in enumerate(LEAF_X)]
    vend = ("cl_sw", "cl_sw2", "cl_sw3", "cl_sw2")
    spines = [K.switch(m, root, f"sp{k}", (x, SPY, -70.0), 70.0, 20.0, 70.0, mt=vend[k], nports=6) for k, x in enumerate(SPINE_X)]
    cab = []
    for s, p in enumerate(cl["srv"]):
        dst = leaves[s]["ports"][5]
        pts = K.cable_pts(p["port"], dst)
        polyline(f"cab{s}", pts, 1.6, m["cl_fiber"], root)
        cab.append(pts)
    up = {}
    for i, L in enumerate(leaves):
        for k, S in enumerate(spines):
            a = (L["top"][0] - 30 + 20 * k, L["top"][1], L["top"][2] + 10)
            b = (S["top"][0] - 15 + 30 * i, SPY, S["top"][2] + 10)
            polyline(f"up{i}{k}", [a, b], 1.0, m["cl_fiber"], root)
            up[(i, k)] = [L["asic"], a, b, S["asic"]]

    def path(k, rev=False, k_src=0, k_dst=1):
        src, dst = (B, A) if rev else (A, B)
        i0, i1 = (1, 0) if rev else (0, 1)
        c0, c1 = cab[i0], cab[i1]
        return (K.gpu_out(src, k_src) + K.nic_port(src)[1:] + c0[1:] + up[(i0, k)] + list(reversed(up[(i1, k)]))[1:]
                + list(reversed(c1))[:-1] + list(reversed(K.nic_port(dst)))[1:] + list(reversed(K.gpu_out(dst, k_dst)))[1:])

    # beat 0: a little traffic on every path, LEDs
    for k in range(4):
        run(root, f"b0_{k}", path(k), 3, 1.3, m["sig"], 0, 0.05 + 0.05 * k, 0.6, 110)
    for L in leaves + spines:
        blink(L["leds"], 0, [0, 2, 4, 6], n=8)
    # beat 1: two flows both hashed to spine 1
    run(root, "b1_a", path(1), 10, 1.5, m["warn"], 1, 0.0, 0.55, 110)
    run(root, "b1_b", path(1, rev=True, k_src=2, k_dst=3), 10, 1.5, m["h_amber"], 1, 0.03, 0.58, 110)
    rise(root, "b1_hot", spines[1]["asic"], 8, 1.0, m["heat"], 1, 0.2, 0.9, 25.0, 40, (8.0, 8.0))
    show(spines[1]["glow"], [(F(1, 0.25), F(2, 0))])
    # beat 2: sprayed over all four
    for k in range(4):
        run(root, f"b2_{k}", path(k), 5, 1.4, m["e_blue"], 2, 0.02 * k, 0.6, 110)
        show(spines[k]["glow"], [(F(2, 0.3), F(2, 0.8))])
    for s in (0, 1):
        show(cl["srv"][s]["glow"], [(F(2, 0.5), F(3, 0))])
    # beat 3: trim on spine 2, quick NACK, one retransmit
    p2 = path(2)
    cut = p2.index(spines[2]["asic"]) + 1
    run(root, "b3_trim", p2[:cut], 1, 2.2, m["warn"], 3, 0.0, 0.0, 60)
    rest = path(2)[cut - 1:]
    run(root, "b3_hdr", rest, 1, 0.7, m["warn"], 3, 0.22, 0.22, 60)
    run(root, "b3_nack", list(reversed(path(0))), 1, 2.0, m["cl_credit"], 3, 0.45, 0.45, 70)
    run(root, "b3_resend", path(3), 1, 1.8, m["e_blue"], 3, 0.72, 0.72, 70)
    for k in (0, 1, 3):
        run(root, f"b3_ok{k}", path(k), 3, 1.3, m["sig"], 3, 0.0, 0.3, 110)
    # the hero: the leaf's switch ASIC cut open on the bench, spraying one flow over four egress ports
    K.hero_mats(m)
    blocks = [("ing", -96, -60, 146, 206, "hr_green", 1.8, "hr_g_green"),
              ("buf", -54, 10, 146, 206, "hr_sram", 1.6, "hr_g_blue"),
              ("trim", -54, 10, 146, 152, "hr_mag", 1.9, "hr_g_red")]
    for k in range(4):
        blocks.append((f"eg{k}", 16, 56, 147 + 15 * k, 159 + 15 * k, "hr_gold", 1.8, "hr_g_amber"))
    for k in range(8):
        blocks.append((f"sd{k}", 62, 92, 147 + 7.4 * k, 152.5 + 7.4 * k, "hr_serdes", 2.4, None))
    hg, hp, hgl = K.hero(m, root, "asx", -100.0, 96.0, 142.0, 210.0, blocks)
    ty = hp["ty"] + 3.0
    from power_vrm_detail import present
    present(hg, [(F(2, 0.45), F(4, 0))])
    mg = K.empty("mg", root)
    C.magnify(m, mg, leaves[0]["asic"], (-90.0, ty, 150.0), r=5.0)
    show(mg, [(F(2, 0.45), F(4, 0))])
    for k in range(4):
        e = hp[f"eg{k}"]
        run(root, f"h2_{k}", [(-120, ty, 176), (-78, ty, 176), (-22, ty, 176), (e[0], ty, e[2]), (110, ty, e[2])],
            5, 1.1, m["e_blue"], 2, 0.5 + 0.02 * k, 0.88, 40)
        show(hgl[f"eg{k}"], [(F(2, 0.55), F(3, 0)), (F(3, 0.5), F(4, 0))])
    show(hgl["ing"], [(F(2, 0.5), F(4, 0))])
    show(hgl["buf"], [(F(2, 0.5), F(3, 0))])
    show(hgl["trim"], [(F(3, 0.55), F(3, 0.85))])
    run(root, "h3_full", [(-120, ty, 149), (-22, ty, 149)], 1, 2.2, m["warn"], 3, 0.55, 0.55, 30)
    run(root, "h3_hdr", [(-22, ty, 149), (36, ty, 149), (110, ty, 149)], 1, 0.7, m["warn"], 3, 0.68, 0.68, 40)
    for k in range(1, 4):
        e = hp[f"eg{k}"]
        run(root, f"h3_{k}", [(-120, ty, 176), (-22, ty, 176), (e[0], ty, e[2]), (110, ty, e[2])], 3, 1.1, m["e_blue"], 3, 0.5, 0.85, 40)
    from sand_overview import label
    for b, items in ((2, (("ASIC cut open: ingress", hp["ing"]), ("shared packet buffer", hp["buf"]),
                          ("4 egress ports, one per spine", hp["eg3"]))),
                     (3, (("queue full: trim to header", hp["trim"]), ("header still delivered", (100.0, ty, 149.0)),
                          ("others keep flowing", hp["eg2"])))):
        for t, pt in items:
            label(t, pt, root, [(F(b, 0.5), F(b + 1, 0))])

    # beat 4: all fabric busy, evenly
    for k in range(4):
        run(root, f"b4_{k}", path(k), 4, 1.3, m["e_blue"], 4, 0.02 * k, 0.6, 110)
    for L in leaves + spines:
        blink(L["leds"], 4, [0, 1, 3, 4, 6, 7], n=8)

    for b, items in ((2, (("one flow sprayed on all paths", spines[1]["top"]), ("NIC places packets in memory", B["nic"]),
                          ("links fill evenly", spines[3]["top"]))),
                     (3, (("congested spine", spines[2]["top"]), ("receiver asks again at once", B["nic"]),
                          ("only that packet resent", A["nic"])))):
        for t, pt in items:
            label(t, pt, root, [(F(b, 0), F(b, 0.45))])
    C.tags(root, {
        0: [("spine switches", spines[2]["top"]), ("leaf switch", leaves[0]["top"]), ("GPU server + NIC", A["nic"]),
            ("every leaf to every spine", up[(1, 3)][2])],
        1: [("two flows hashed to one spine", spines[1]["top"]), ("other paths idle", spines[3]["top"]),
            ("training step waits", B["gpu"][1])],
        4: [("UEC 1.0, published 2025", spines[1]["top"]), ("mixed-vendor switches", spines[2]["top"]),
            ("AVGO ANET AMD CSCO MRVL NVDA", leaves[1]["top"])],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 80.0, -80.0), 480.0, 0.30, 0.40, pad=1.0),
        frame((0.0, 110.0, -70.0), 400.0, 0.15, 0.30, pad=1.0),
        [(0.0, frame((0.0, 110.0, -70.0), 400.0, -0.20, 0.35, pad=1.0)),
         (0.5, frame((0.0, 10.0, 176.0), 220.0, 0.15, 0.80))],
        [(0.0, frame((40.0, 110.0, -70.0), 380.0, 0.25, 0.30, pad=1.0)),
         (0.5, frame((0.0, 10.0, 176.0), 220.0, -0.15, 0.80))],
        frame((0.0, 80.0, -80.0), 500.0, -0.30, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
