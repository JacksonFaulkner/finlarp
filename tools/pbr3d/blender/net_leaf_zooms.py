"""Zoom-ins (a-e) for the LEAF page: the overview's fabric (net_leaf_detail.scene) with its own
camera, beads and tags, three beats each (diagrams_nodes/netcool/leaf/zooms.rs):

  a downlinks      server NICs, copper DAC beside the leaf, AOC from the outer racks
  b the switch     ports, SerDes traces, the ASIC under its heatsink, fans
  c uplinks        the top port row, 800G optics, yellow fibre up to the tray
  d ECMP           one leaf's flows hashed across four spines, landing on another leaf
  e congestion     many-to-one: a queue builds, pause frames, ECN marks

    blender -b --factory-startup --python tools/pbr3d/blender/net_leaf_zooms.py -- a

Writes assets/net_leaf_zoom_<letter>.glb.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_leaf_detail as D  # noqa: E402
from net_leaf_detail import frame, camera_path, run, rise  # noqa: E402
import net_leaf_overview as OV  # noqa: E402

PAGE = "net_leaf"
BEATS = 3


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def zoom_a(m, root, s):
    lf, ports = s["leaf"], s["srv_ports"]
    for i in (8, 10, 12, 14):
        run(root, f"a_n{i}", D.to_leaf(s, i)[:4], 3, 0.6, m["pkt"], 0, 0.0, 0.8, 50)
    for i in range(8, 24):
        run(root, f"a_d{i}", D.to_leaf(s, i), 2, 0.6, m["pkt"], 1, 0.01 * (i - 8), 0.7, 70)
    for i in list(range(0, 8)) + list(range(24, 32)):
        run(root, f"a_o{i}", D.to_leaf(s, i), 2, 0.6, m["pkt"], 2, 0.01 * (i % 8), 0.7, 80)
    OV.blink_leds(lf, range(3))
    tags(root, [
        [("NIC: 800G port per GPU pair", ports[10]), ("8-GPU server", (D.GPU_RACKS[1], D.TRAY_Y[1] + 10.0, 0.0))],
        [("passive copper DAC, ~2 m at 800G", (D.GPU_RACKS[1] + 26.0, 120.0, 3.0)), ("into the bottom port row", lf["down"][12])],
        [("AOC: lasers in the plugs, up to ~30 m", (D.GPU_RACKS[0] + 26.0, 100.0, 3.0)), ("lighter, thinner, costs more", (D.GPU_RACKS[3] - 26.0, 100.0, 3.0))],
    ])
    camera_path(root, [
        frame((-64.0, 110.0, 0.0), 150.0, 0.30, 0.15),
        frame((-30.0, 160.0, 0.0), 150.0, 0.20, 0.15),
        frame((0.0, 140.0, 0.0), 300.0, -0.10, 0.12),
    ])


def zoom_b(m, root, s):
    lf = s["leaf"]
    for i in range(0, D.N_PORT, 2):
        run(root, f"b_in{i}", lf["tr_down"][i][::-1], 2, 0.4, m["pkt"], [0, 1], 0.01 * i, 0.8, 30)
    for i in range(1, D.N_PORT, 2):
        run(root, f"b_out{i}", lf["tr_up"][i], 2, 0.4, m["up"], 1, 0.2 + 0.01 * i, 0.9, 30)
    show(lf["die_glow"], [(F(1, 0.0), F(3, 0.0))])
    for k, fp in enumerate(lf["fans"]):
        run(root, f"b_air{k}", [(fp[0], fp[1], D.ROW_Z[0] + 2.0), (fp[0], fp[1], fp[2] - 20.0)], 3, 0.5, m["cool"], 2, 0.02 * k, 0.8, 40)
    rise(root, "b_heat", lf["top"], 6, 0.5, m["heat"], 2, 0.05, 0.85, 18.0, 60, (6.0, 6.0))
    OV.blink_leds(lf, range(3))
    tags(root, [
        [("64 OSFP cages", lf["down"][4]), ("SerDes: 512 lanes x 100G", lf["tr_down"][10][1])],
        [("one ASIC switches it all", lf["parts"]["heatsink"]), ("51.2 Tb/s, ~500 W chip", lf["asic"])],
        [("fans pull air front to back", lf["fans"][2]), ("PSUs", lf["parts"]["psu"]), ("control CPU", lf["parts"]["cpu"])],
    ])
    camera_path(root, [
        frame((0.0, D.LEAF_Y + 4.0, -6.0), 60.0, 0.30, 0.55),
        frame((0.0, D.LEAF_Y + 4.0, -28.0), 60.0, -0.30, 0.85),
        frame((0.0, D.LEAF_Y + 4.0, -40.0), 70.0, 0.60, 0.70),
    ])


def zoom_c(m, root, s):
    lf = s["leaf"]
    OV.uplinks(m, root, s, [0, 1, 2], name="c_ul")
    OV.blink_leds(lf, range(3))
    tags(root, [
        [("top row: 32 uplinks", lf["up"][20]), ("800G OSFP optics", lf["up"][6])],
        [("8 fibres per DR8 module", (-4.0, D.TRAY_TOP - 18.0, 3.0)), ("single-mode, up to 500 m", (8.0, D.TRAY_TOP - 6.0, 3.0))],
        [("overhead tray to the spines", (200.0, D.TRAY_TOP + 6.0, -35.0)), ("a quarter of the uplinks to each spine", s["spines"][0]["top"])],
    ])
    camera_path(root, [
        frame((0.0, D.LEAF_Y + 8.0, 0.0), 70.0, 0.30, 0.25),
        frame((0.0, 225.0, 0.0), 90.0, 0.40, 0.15),
        frame((260.0, 200.0, -90.0), 560.0, 0.30, 0.40, pad=0.9),
    ])


def zoom_d(m, root, s):
    OV.ecmp(m, root, s, [0], n=2)
    OV.ecmp(m, root, s, [1], n=4, name="d_b")
    OV.ecmp(m, root, s, [2], dst=2, n=4, name="d_c")
    for sp in s["spines"]:
        show(sp["leds"], [(F(0, 0.3), F(3, 0.0))])
    sp = s["spines"]
    tags(root, [
        [("leaf 0", s["leaf"]["top"]), ("hash picks a spine per flow", (D.SPINE_X - 30.0, D.TRAY_TOP + 10.0, -60.0))],
        [("4 equal-cost paths", sp[1]["top"]), ("any spine reaches any leaf", sp[3]["top"])],
        [("two big flows can collide", sp[2]["top"]), ("then one link runs hot", (D.SPINE_X - 30.0, D.TRAY_TOP + 10.0, -500.0))],
    ])
    camera_path(root, [
        frame((250.0, 200.0, -150.0), 650.0, 0.35, 0.45, pad=0.9),
        frame((400.0, 200.0, -390.0), 700.0, 0.70, 0.45, pad=0.9),
        frame((300.0, 200.0, -400.0), 900.0, 0.30, 0.65, pad=0.85),
    ])


def zoom_e(m, root, s):
    lf = s["leaf"]
    up = lf["up"][9]
    qat = (up[0], up[1] + 3.0, up[2] + 2.0)
    for i in range(0, D.N_PORT, 2):
        run(root, f"e_in{i}", D.to_leaf(s, i), 2, 0.6, m["pkt"], [0, 1, 2], 0.0, 0.3, 60)
    run(root, "e_up", D.to_spine(s, 0, 1, 9), 4, 0.7, m["up"], [0, 1, 2], 0.1, 0.8, 90)
    D.queue(m, root, qat, 10, 0, 0.1, 0.9, 1.0, "e_q0")
    D.queue(m, root, qat, 10, 1, 0.0, 0.2, 1.0, "e_q1")
    for i in (0, 6, 12, 19, 25, 31):
        run(root, f"e_pfc{i}", D.from_leaf(s, i), 2, 0.7, m["fail"], 1, 0.3, 0.7, 60)
    run(root, "e_ecn", D.to_spine(s, 0, 1, 9), 3, 0.8, m["ecn"], 2, 0.0, 0.5, 90)
    D.queue(m, root, qat, 4, 2, 0.0, 0.3, 1.0, "e_q2")
    tags(root, [
        [("many senders, one egress port", lf["down"][16]), ("the buffer fills", qat)],
        [("PFC: pause frames upstream", s["srv_ports"][12]), ("lossless, but stalls spread", lf["down"][4])],
        [("ECN marks: senders slow down", (up[0], D.TRAY_TOP - 10.0, 3.0)), ("queue drains", qat)],
    ])
    camera_path(root, [
        frame((0.0, 170.0, 0.0), 220.0, 0.10, 0.15),
        frame((0.0, 150.0, 0.0), 280.0, -0.15, 0.10),
        frame((0.0, 215.0, 0.0), 110.0, 0.25, 0.15),
    ])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    ZOOMS[letter](m, root, s)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python net_leaf_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
