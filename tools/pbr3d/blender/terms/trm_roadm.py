"""TRM_ROADM: the Terms-tab overview for a reconfigurable optical add-drop multiplexer.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_roadm.py

Writes assets/term_TRM_ROADM.glb. Captions live in specs/terms/TRM_ROADM.json.

Beats:
  0 mesh      three ROADM sites in a DWDM ring, many colours on each fibre
  1 node      inside one node: colours pass through, one is dropped, one is added
  2 wss       the wavelength selective switch cut open: fibre array, lens, grating, LCoS pixels
  3 reroute   software retilts one pixel column; a colour moves to another port, no site visit
  4 market    who sells ROADMs and WSS modules
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import blink, bx, frame, polyline, run  # noqa: E402

import term_common as C  # noqa: E402
import kit_photonics as K  # noqa: E402

SLUG = "TRM_ROADM"
BEATS = [
    ("A ROADM is a node that routes colours of light",
     "Long-haul and metro fibre carries dense WDM: 64 to 96+ colours on one fibre, each a separate 400G-1.6T channel. "
     "At every junction a ROADM (reconfigurable optical add-drop multiplexer) decides, colour by colour, what goes "
     "where. Light that just passes through never gets turned back into electrons, which saves power and cost."),
    ("Each colour passes through, drops out, or is added",
     "Inside the node a colour can carry on to the next site (express), drop to a local transponder that turns it "
     "into data, or be added from a local transponder onto the outgoing fibre. Here the red channel is dropped and a "
     "new green one is added in its slot, while the rest sail straight through."),
    ("The core part is a wavelength selective switch",
     "A wavelength selective switch (WSS) takes light from an input fibre, spreads it into its colours with a "
     "diffraction grating, and lands each colour on its own stripe of a liquid-crystal-on-silicon (LCoS) panel. Each "
     "stripe acts as a tiny tilted mirror that steers its colour back to the chosen output fibre. Older designs use "
     "MEMS micro-mirrors instead."),
    ("Software changes the route without a truck roll",
     "To reroute a channel, the network controller just rewrites the phase pattern on one LCoS stripe; the colour "
     "lands on a different output port within milliseconds. Carriers and cloud operators use this to shift capacity, "
     "restore around a fibre cut, or light a new data-centre link without sending anyone to the site."),
    ("WSS modules are a big line for optical suppliers",
     "A large ROADM node holds several WSS modules, each costing thousands of dollars, so they are a major product for "
     "component makers. Lumentum (LITE) and Coherent (COHR) dominate WSS supply; Ciena (CIEN) and Nokia (NOK) build the "
     "ROADM systems and line cards around them. AI data-centre interconnect is adding new demand."),
]

NZ = -140.0  # network plane depth
CH = K.CHANNEL_GLOWS


def cabinet(m, parent, name, c):
    g = empty(name, parent)
    x, y, z = c
    bx(f"{name}_body", (x - 12, y, z - 9), (x + 12, y + 34, z + 9), m["ph_case"], g)
    for k in range(5):
        bx(f"{name}_card{k}", (x - 10, y + 3 + 6 * k, z + 9), (x + 10, y + 7.5 + 6 * k, z + 9.6), m["ph_front"], g)
        led = empty(f"{name}_led{k}", g)
        bx(f"{name}_ld{k}", (x + 7, y + 4.5 + 6 * k, z + 9.6), (x + 8.5, y + 6 + 6 * k, z + 10.2), m["ph_green"], led)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)

    # ---- beat 0 / 4: a three-site ring ----
    net = empty("net", root)
    bx("ground", (-170.0, -2.0, NZ - 80), (170.0, -1.0, NZ + 60), m["ph_pcb"], net)
    sites = [(-120.0, 0.0, NZ + 30), (120.0, 0.0, NZ + 30), (0.0, 0.0, NZ - 60)]
    for k, c in enumerate(sites):
        cabinet(m, net, f"site{k}", c)
        bx(f"pad{k}", (c[0] - 20, -1.0, c[2] - 16), (c[0] + 20, 0.0, c[2] + 16), m["ph_front"], net)
    rings = []
    for k in range(3):
        a, b = sites[k], sites[(k + 1) % 3]
        pa, pb = (a[0], 4.0, a[2]), (b[0], 4.0, b[2])
        mid = ((a[0] + b[0]) / 2, 4.0, (a[2] + b[2]) / 2)
        K.fiber(m, net, f"span{k}", [pa, mid, pb], r=0.8)
        rings.append([pa, pb])
    show(net, [(F(0, 0), F(1, 0)), (F(4, 0), F(5, 0))])
    for k in range(3):
        for j in range(4):
            run(root, f"ring{k}_{j}", rings[k], 3, 1.6, m[CH[(2 * k + j) % 8]], [0, 4], 0.05 * j, 0.6 + 0.05 * j, 60)

    # ---- beats 1 and 3: one node opened up ----
    node = empty("node", root)
    bx("n_floor", (-110.0, -1.6, -40.0), (30.0, 0.0, 30.0), m["ph_front"], node)
    west = (-105.0, 4.0, 0.0)
    east = (25.0, 4.0, 0.0)
    wss_in = K.awg(m, node, "wssA", (-70.0, 0.0, 0.0), 14.0, 24.0, 8.0, 4)   # drop-side WSS
    wss_out = K.awg(m, node, "wssB", (-10.0, 0.0, 0.0), 14.0, 24.0, 8.0, 4)  # add-side WSS
    K.fiber(m, node, "lineW", [west, (-77.0, 4.0, 0.0)], r=0.7)
    K.fiber(m, node, "express", [(-63.0, 4.0, 0.0), (-17.0, 4.0, 0.0)], r=0.7)
    K.fiber(m, node, "lineE", [(-3.0, 4.0, 0.0), east], r=0.7)
    # transponders: drop (to the left) and add (to the right), in front
    drop_tp = [(-62.0, 3.0, 26.0), (-48.0, 3.0, 26.0)]
    add_tp = (-14.0, 3.0, 26.0)
    for k, p in enumerate(drop_tp + [add_tp]):
        bx(f"tp{k}", (p[0] - 6, 0.0, p[2] - 4), (p[0] + 6, 6.0, p[2] + 4), m["ph_dsp"], node)
        bx(f"tpf{k}", (p[0] - 5, 1.0, p[2] + 4), (p[0] + 5, 5.0, p[2] + 4.4), m["ph_front"], node)
    K.fiber(m, node, "dropf0", [(-66.0, 4.0, 10.0), (-66.0, 4.0, 18.0), (-62.0, 4.0, 22.0)], r=0.5)
    K.fiber(m, node, "dropf1", [(-66.0, 4.0, 10.0), (-50.0, 4.0, 14.0), (-48.0, 4.0, 22.0)], r=0.5)
    K.fiber(m, node, "addf", [(-14.0, 4.0, 22.0), (-14.0, 4.0, 10.0)], r=0.5)
    # controller box and its control line
    bx("ctrl", (-40.0, 0.0, -36.0), (-24.0, 10.0, -26.0), m["ph_case"], node)
    bx("ctrl_scr", (-38.0, 3.0, -26.0), (-26.0, 8.0, -25.6), m["chan"], node)
    polyline("ctrl_l", [(-32.0, 10.0, -31.0), (-32.0, 14.0, -12.0), (-70.0, 9.0, -12.0), (-70.0, 8.0, -6.0)], 0.3, m["ph_gold"], node)
    show(node, [(F(1, 0), F(2, 0)), (F(3, 0), F(4, 0))])

    express = [west, (-77.0, 4.0, 0.0), (-63.0, 4.0, 0.0), (-17.0, 4.0, 0.0), (-3.0, 4.0, 0.0), east]
    for j in range(1, 8):
        if j == 3:
            continue  # channel 3 is the added slot below
        run(root, f"exp{j}", express, 2, 1.3, m[CH[j]], [1, 3], 0.04 * j, 0.55 + 0.04 * j, 70)
    # red (ch0) dropped: beat 1 to transponder 0, beat 3 (rerouted) to transponder 1
    run(root, "drop1", [west, (-77.0, 4.0, 0.0), (-66.0, 4.0, 6.0), (-66.0, 4.0, 18.0), (-62.0, 4.5, 22.0)],
        4, 1.5, m[CH[0]], [1], 0.0, 0.7, 50)
    run(root, "drop3", [west, (-77.0, 4.0, 0.0), (-66.0, 4.0, 6.0), (-50.0, 4.0, 14.0), (-48.0, 4.5, 22.0)],
        4, 1.5, m[CH[0]], [3], 0.3, 0.85, 50)
    run(root, "drop3a", [west, (-77.0, 4.0, 0.0), (-66.0, 4.0, 6.0), (-66.0, 4.0, 18.0), (-62.0, 4.5, 22.0)],
        2, 1.5, m[CH[0]], [3], 0.0, 0.1, 50)
    run(root, "add", [(-14.0, 4.5, 22.0), (-14.0, 4.0, 10.0), (-10.0, 4.0, 4.0), (-3.0, 4.0, 0.0), east],
        4, 1.5, m[CH[3]], [1, 3], 0.1, 0.75, 45)
    run(root, "cmd", [(-32.0, 11.0, -31.0), (-32.0, 15.0, -12.0), (-70.0, 10.0, -12.0), (-70.0, 9.0, -6.0)],
        3, 0.8, m["h_amber"], [3], 0.15, 0.3, 25)

    # ---- beat 2 (and 3 inset): the WSS cut open on the bench, x 60..200 ----
    w = empty("wss", root)
    WY = 6.0
    bx("w_base", (60.0, -1.0, -30.0), (200.0, 2.0, 30.0), m["ph_case"], w)
    for k, (za, zb) in enumerate(((-30.0, -28.5),)):
        bx(f"w_wall{k}", (60.0, 2.0, za), (200.0, 14.0, zb), m["ph_case"], w)
    # fibre array: 1 in, 4 out, in a V-groove block
    bx("w_vg", (62.0, 2.0, -9.0), (72.0, 9.0, 9.0), m["quartz_c"], w)
    port_z = [-6.0, -3.0, 0.0, 3.0, 6.0]  # index 2 = input
    for k, zp in enumerate(port_z):
        K.fiber(m, w, f"w_f{k}", [(30.0, WY, zp * 2.0), (50.0, WY, zp * 1.4), (72.0, WY, zp)], r=0.45)
    # collimating lens
    for k in range(7):
        r = 9.0 * math.sqrt(max(0.0, 1 - ((k - 3) / 3.6) ** 2))
        bx(f"w_lens{k}", (96.0 + abs(k - 3) * 0.4, WY - r * 0.6, -r), (99.0 - abs(k - 3) * 0.4, WY + r * 0.6, r), m["quartz_c"], w)
    bx("w_lensr", (95.0, 2.0, -10.0), (100.0, 3.0, 10.0), m["steel"], w)
    # diffraction grating (ruled block, angled)
    bx("w_grat", (128.0, 2.0, -12.0), (132.0, 14.0, 12.0), m["ph_gold"], w)
    for k in range(10):
        bx(f"w_rule{k}", (127.6, 2.5, -11.0 + 2.4 * k), (128.0, 13.5, -10.4 + 2.4 * k), m["steel"], w)
    # LCoS panel: 8 stripes, one per colour
    bx("w_lcos", (182.0, 2.0, -24.0), (190.0, 16.0, 24.0), m["ph_si"], w)
    stripes = []
    for k in range(8):
        zc = -21.0 + 6.0 * k
        s_ = empty(f"w_st{k}", w)
        bx(f"w_stp{k}", (181.0, 3.0, zc - 2.4), (182.0, 15.0, zc + 2.4), m[CH[k]], s_)
        stripes.append((zc, s_))
    show(w, [(F(2, 0), F(4, 0))])
    # in-fibre -> lens -> grating (white bundle) -> fan out to stripes -> back to ports
    run(root, "w_in", [(30.0, WY, 0.0), (72.0, WY, 0.0), (97.0, WY, 0.0), (128.0, WY, 0.0)], 8, 1.1, m["bit"], [2, 3], 0.0, 0.5, 40)
    outs = [0, 1, 3, 4]
    for k, (zc, _) in enumerate(stripes):
        po = outs[k % 4]
        back = [(128.0, WY + 2.0, zc * 0.3), (97.0, WY + 2.0, port_z[po] * 1.2), (72.0, WY + 1.0, port_z[po]), (50.0, WY + 1.0, port_z[po] * 1.4)]
        run(root, f"w_c{k}", [(128.0, WY, 0.0), (181.0, WY + 3.0, zc)] + back, 2, 1.0, m[CH[k]], [2], 0.25, 0.7, 50)
    # beat 3: the red stripe's route changes: first half to port 0, second half to port 4
    zc0 = stripes[0][0]
    for half, po, u0, u1 in ((0, 0, 0.0, 0.25), (1, 4, 0.5, 0.8)):
        run(root, f"w_rr{half}", [(128.0, WY, 0.0), (181.0, WY + 3.0, zc0), (128.0, WY + 2.0, zc0 * 0.3),
                                  (97.0, WY + 2.0, port_z[po] * 1.2), (72.0, WY + 1.0, port_z[po]), (50.0, WY + 1.0, port_z[po] * 1.4)],
            3, 1.3, m[CH[0]], [3], u0, u1, 45)
    flash = empty("w_flash", root)
    bx("w_fl", (180.0, 16.5, zc0 - 3.0), (183.0, 18.0, zc0 + 3.0), m["h_amber"], flash)
    blink(flash, 3, [3, 4, 5], n=8, on=0.6)

    C.tags(root, {
        0: [("ROADM site", (-120.0, 40.0, NZ + 30)), ("ROADM site", (120.0, 40.0, NZ + 30)),
            ("DWDM: 64-96 colours/fibre", (0.0, 10.0, NZ + 30)), ("ROADM site", (0.0, 40.0, NZ - 60))],
        1: [("line in (west)", (-100.0, 8.0, 0.0)), ("express: stays as light", (-40.0, 8.0, 0.0)),
            ("drop to transponder", (-62.0, 10.0, 26.0)), ("add a new colour", (-14.0, 10.0, 26.0))],
        2: [("fibre array: 1 in, 4 out", (66.0, 12.0, 0.0)), ("collimating lens", (97.0, 14.0, 0.0)),
            ("grating spreads colours", (130.0, 18.0, 0.0)), ("LCoS: 1 stripe per colour", (186.0, 20.0, 0.0))],
        3: [("controller rewrites stripe", (-32.0, 12.0, -36.0)), ("red moves to new port", (-48.0, 6.0, 30.0)),
            ("stripe retilted", (182.0, 20.0, zc0)), ("milliseconds, no truck", (100.0, 4.0, 30.0))],
        4: [("WSS: LITE, COHR", (120.0, 40.0, NZ + 30)), ("systems: CIEN, NOK", (-120.0, 40.0, NZ + 30)),
            ("DCI adds demand", (0.0, 40.0, NZ - 60))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 10.0, NZ - 15), 290.0, 0.10, 0.55, pad=1.0),
        frame((-40.0, 4.0, 0.0), 140.0, 0.15, 0.65),
        [(0.0, frame((130.0, 6.0, 0.0), 160.0, -0.35, 0.70)), (0.55, frame((160.0, 8.0, 0.0), 100.0, -0.60, 0.50))],
        [(0.0, frame((-40.0, 4.0, 0.0), 150.0, 0.10, 0.65)), (0.5, frame((70.0, 6.0, 0.0), 300.0, -0.20, 0.75))],
        frame((0.0, 10.0, NZ - 15), 290.0, -0.15, 0.50, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
