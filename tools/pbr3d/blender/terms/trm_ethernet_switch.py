"""TRM_ETHERNET_SWITCH: the Terms-tab overview for an Ethernet switch, at the POWER pages' detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_ethernet_switch.py

Writes assets/term_TRM_ETHERNET_SWITCH.glb and specs/terms/TRM_ETHERNET_SWITCH.json.

A GPU rack with its top-of-rack switch on the left; on the bench a 64-port 800G switch three
times life size with its lid cut away (switch ASIC under a finned heatsink, SerDes traces fanning
to the OSFP cages, fans and PSUs at the back) and one OSFP optic pulled out and cut open.

Beats:
  0 rack     the switch at the top of a GPU rack, a cable to every server port
  1 inside   lid off: ASIC, heatsink, SerDes traces, cages, fans, PSUs
  2 forward  a packet enters a port, crosses to the ASIC, leaves by another port
  3 ports    64 ports x 800G = 51.2 Tb/s; an OSFP optic cut open
  4 roadmap  switch-chip bandwidth doubles about every two years
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_link as K  # noqa: E402
import net_leaf_detail as NL  # noqa: E402
from sand_overview import F, show, empty  # noqa: E402
from power_vrm_detail import bx, wire, run, rise, blink, frame, join  # noqa: E402

SLUG = "TRM_ETHERNET_SWITCH"
BEATS = [
    ("An Ethernet switch ties every server in a rack to the network",
     "A switch is a box of ports with one job: take each packet that arrives and send it out the right port. In an "
     "AI cluster the top-of-rack switch takes a cable from every GPU server's network card, and its uplinks reach "
     "the next tier. The back-end network that links thousands of GPUs is built from boxes like this one."),
    ("Inside: one big switch ASIC, ringed by ports",
     "Lift the lid and most of the box is a single switch chip under a heatsink. Copper traces fan out from the chip's "
     "SerDes lanes to the cages on the front panel, where optics or copper cables plug in. Fans and two power supplies "
     "at the back keep the 500 W-class ASIC cool. The chip (Broadcom Tomahawk, Nvidia Spectrum, Cisco Silicon One) is the product."),
    ("A packet in one port, out another, in under a microsecond",
     "The ASIC reads each packet's header, looks the destination up in its tables and queues the packet for the right "
     "output port. It does this for billions of packets a second, all in hardware. AI traffic is bursty, so deep buffers, "
     "congestion signals and load balancing (as in Spectrum-X or Ultra Ethernet) decide how fast a training job runs."),
    ("64 ports x 800G = 51.2 terabits a second",
     "Bandwidth is port count times port speed. A 51.2T chip drives 512 SerDes lanes at 100G, grouped into 64 ports of "
     "800G. Each port takes a pluggable optic: inside, a DSP retimes the signal and eight lasers send it down fibre. "
     "Optics often cost more than the switch itself."),
    ("Switch chips double about every two years: 25.6T, 51.2T, 102.4T",
     "Each generation doubles the bandwidth of one chip, so fewer boxes and hops are needed for the same cluster. 102.4T "
     "chips with 200G lanes are shipping now. AI back-end Ethernet is one of the fastest-growing parts of networking. "
     "Related: Arista (ANET), Broadcom (AVGO), Nvidia (NVDA), Cisco (CSCO), Celestica (CLS), Marvell (MRVL)."),
]

RX = -230.0  # the rack on the left
SO = (110.0, 0.0, 60.0)  # the big switch's front-face origin
SS = 3.0


def rack(m, root):
    g = empty("rack", root)
    NL.frame_rack(m, g, RX, 0.0, "rk")
    ports = []
    for t, y in enumerate(NL.TRAY_Y):
        ports += NL.server(m, g, RX, y, 0.0, 1, f"srv{t}")
    sw = NL.switch(m, g, (RX, NL.LEAF_Y, 0.5), 1.0, detail=False, name="tor")
    cg = empty("cables", g)
    for i, p in enumerate(ports):
        q = sw["down"][4 + 3 * i]
        zc = 2.0 + 0.4 * i
        x = RX + 24.0 - 0.6 * i
        wire(f"dac{i}", [p, (p[0], p[1], zc), (x, p[1], zc), (x, q[1] - 3.0, zc), (q[0], q[1] - 3.0, zc), q], 0.35,
             m["dac"], cg, 6)
    for gi, lg in enumerate(sw["leds"]):
        blink(lg, 0, [gi, gi + 4], n=8, on=0.6)
    return sw, ports


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m.update(NL.materials())
    K.materials(m)
    floor = empty("floor", root)
    bx("fl", (-300.0, -2.0, -200.0), (240.0, 0.0, 160.0), m["tile"], floor)
    tor, ports = rack(m, root)

    big = NL.switch(m, root, SO, SS, detail=True, name="big")
    for gi, lg in enumerate(big["leds"]):
        blink(lg, 1, [gi, gi + 4], n=8, on=0.6)
    show(big["die_glow"], [(F(1, 0.0), F(5, 0))])
    rise(root, "heat", big["parts"]["heatsink"], 10, 0.9, m["heat"], [1, 2], 0.0, 0.8, h=40.0, life=50, spread=(16.0, 14.0))
    for k, f in enumerate(big["fans"][:6:2]):
        run(root, f"air{k}", [f, (f[0], f[1], f[2] - 40.0)], 4, 0.6, m["cool"], 1, 0.1, 0.8, 30)

    # beat 0: packets from servers to the ToR
    for i in (0, 3, 6):
        p, q = ports[i], tor["down"][4 + 3 * i]
        run(root, f"up{i}", [p, (p[0], p[1], 3.0), (RX + 22.0, p[1], 3.0), (RX + 22.0, q[1] - 3.0, 3.0), q], 4, 0.9,
            m["pkt"], 0, 0.05 + 0.1 * i, 0.9, 50)
    # beat 2: a packet in port 5 (front -> ASIC), out port 24 (ASIC -> front -> away)
    pin = list(reversed(big["tr_down"][5]))
    pin = [(pin[0][0], pin[0][1], pin[0][2] + 50.0)] + pin + [big["asic"]]
    run(root, "pin", pin, 6, 1.4, m["pkt"], 2, 0.0, 0.4, 70)
    po = [big["asic"]] + big["tr_up"][24]
    po = po + [(po[-1][0], po[-1][1], po[-1][2] + 50.0)]
    run(root, "pout", po, 6, 1.4, m["up"], 2, 0.4, 0.85, 60)
    # header lookup flash on the die
    flash = empty("flash", root)
    a = big["asic"]
    bx("fl0", (a[0] - 10.0, a[1] + 6.4, a[2] - 10.0), (a[0] + 10.0, a[1] + 7.0, a[2] + 10.0), m["ecn"], flash)
    blink(flash, 2, [3, 4], n=8, on=0.8)

    # beat 3: an OSFP pulled out, cut open; all lanes busy
    ox_o = (SO[0] + NL.port_x(8) * SS, 14.0, SO[2] + 80.0)
    ox, op = NL.osfp(m, root, ox_o, 6.0, name="osfp")
    show(ox, [(F(3, 0.0), F(5, 0))])
    blink(op["las_g"], 3, [0, 2, 4, 6], n=8, on=0.7)
    run(root, "dsp", [op["edge"], op["dsp"], op["las"]], 5, 0.7, m["pkt"], 3, 0.05, 0.6, 30)
    for k in (0, 3, 7):
        run(root, f"ln{k}", op["lanes"][k], 4, 0.5, m["laser"], 3, 0.1 + 0.05 * k, 0.8, 30)
    for i in range(0, 32, 4):
        run(root, f"tr{i}", big["tr_down"][i], 2, 0.8, m["pkt"], 3, 0.02 * (i % 8), 0.7, 40)
        run(root, f"tu{i}", big["tr_up"][i + 2], 2, 0.8, m["up"], 3, 0.05 + 0.02 * (i % 8), 0.75, 40)

    # beat 4: roadmap bars
    bars = K.speed_bars(m, root, "bars", (-120.0, 0.0, 40.0), rates=(128, 256, 512, 1024), x_gap=22.0, scale=0.09)
    show(bars["group"], [(F(4, 0.0), F(5, 0))])

    t = bars["tops"]
    C.tags(root, {
        0: [("top-of-rack switch", (RX, NL.LEAF_Y + 14.0, 0.0)), ("a cable per server port", (RX + 24.0, 150.0, 2.0)),
            ("8-GPU servers", (RX, 60.0, 0.0))],
        1: [("switch ASIC under heatsink", big["parts"]["heatsink"]), ("SerDes traces to cages", big["tr_down"][10][1]),
            ("OSFP cages: 64 ports", big["up"][4]), ("fans + PSUs", big["parts"]["psu"])],
        2: [("packet in", pin[1]), ("header lookup", big["asic"]), ("out the right port", po[-2])],
        3: [("800G OSFP optic", op["dsp"]), ("8 lasers x 100G", op["las"]), ("64 x 800G = 51.2T", big["up"][2])],
        4: [("12.8T", t[0]), ("25.6T", t[1]), ("51.2T", t[2]), ("102.4T", t[3])],
    })
    sc = (SO[0], 18.0, SO[2] - 90.0)
    C.done(SLUG, BEATS, [
        [(0.0, frame((RX + 20.0, 120.0, 0.0), 240.0, 0.35, 0.15)), (0.6, frame((RX, 170.0, 0.0), 100.0, 0.25, 0.20))],
        frame(sc, 180.0, 0.35, 0.65),
        frame((SO[0] - 10.0, 10.0, SO[2] - 50.0), 110.0, 0.10, 0.50),
        frame((ox_o[0], 16.0, ox_o[2] - 40.0), 80.0, 0.50, 0.45),
        frame((-70.0, 40.0, 30.0), 200.0, 0.15, 0.25, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
