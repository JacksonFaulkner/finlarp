"""The SPINE page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/net_spine_overview.py

Writes blender/net_spine_overview.blend and assets/net_spine_overview.glb. One beat is 8 s.

The spine tier of a leaf-spine fabric (net_spine_detail.py): four spine switches in a row, eight leaf
switches below them, a fibre from every leaf to every spine. One spine (51.2 Tb/s, 2RU) is opened.

Beats (match the seven beats in diagrams_nodes/netcool/spine/overview.rs):
  0 fabric     four spines, eight leaves, every leaf wired to every spine
  1 opened     the lid lifts off one spine: ports, ASIC, fans, PSUs
  2 ports      64 OSFP 800G modules across the front, link LEDs blinking
  3 ASIC       the heatsink lifts away: one 51.2 Tb/s switch chip
  4 SerDes     packets ride copper traces from the ports to the ASIC and back out
  5 air        fans pull cool air in the front, over the heatsink, hot out the back
  6 ECMP       flows from one leaf spread over all four spines to another leaf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_spine_detail as D  # noqa: E402
from net_spine_detail import frame, camera_path, run, rise  # noqa: E402

PAGE = "net_spine"
NAME = "overview"
BEATS = 7
FLOW_M = ["pkt", "pkt2", "pkt3", "pkt4"]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def lift_hs(s, b, u0=0.1, u1=0.4, h=140.0, down=None):
    """Raise the heatsink by h during beat b (and lower it again at `down`=(beat, u) if given)."""
    lift = s["asic"]["lift"]
    key(lift, F(b, 0.0), "location", P(0, 0, 0), linear=True)
    key(lift, F(b, u0), "location", P(0, 0, 0), linear=True)
    key(lift, F(b, u1), "location", P(0, h, 0), linear=True)
    if down:
        key(lift, F(*down), "location", P(0, h, 0), linear=True)
        key(lift, F(down[0], down[1] + 0.2), "location", P(0, 0, 0), linear=True)


def serdes(m, root, beats, cols=range(0, 16, 2), u0=0.0, u1=0.85, n=3):
    """Packets in from ports on the left half, through the ASIC, out to ports on the right."""
    for c in cols:
        inn = list(reversed(D.trace_path(c, 1)))
        out = D.trace_path(15 - c, 3)
        run(root, f"sd_in{c}", inn, n, 1.8, m["pkt"], beats, u0, u1 - 0.3, 60)
        run(root, f"sd_out{c}", out, n, 1.8, m["pkt2"], beats, u0 + 0.25, u1, 60)


def ecmp(m, root, beats, src=1, dst=6, n=3, u0=0.0, u1=0.8, spines=range(4), life=150):
    for k in spines:
        run(root, f"ecmp{src}{dst}_{k}", D.flow(src, k, dst), n, 7.0, m[FLOW_M[k]], beats, u0 + 0.05 * k, u1, life)


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root, BEATS)
    D.present(s["lid"], beat(0) + beat(6))
    D.leds_on(s, range(BEATS))
    show(s["fabric"]["leds"], span(0, 0.0, 7, 0.0))
    # beat 0: the fabric, some traffic everywhere
    for i, (a, b) in enumerate(((0, 5), (3, 7), (6, 2))):
        run(root, f"bg{i}", D.flow(a, i % 4, b), 3, 7.0, m[FLOW_M[i % 4]], 0, 0.05 + 0.1 * i, 0.85, 150)
    # beat 3: heatsink off
    lift_hs(s, 3, down=(4, 0.0))
    show(s["asic"]["glow"], span(3, 0.5, 4, 0.0) + beat(5))
    # beat 4: SerDes
    serdes(m, root, [4])
    # beat 5: air and heat
    D.airflow(root, m, [5], n=10)
    rise(root, "o_heat", (0.0, D.HS_Y[1], D.ASIC[1]), 6, 2.0, m["heat"], 5, 0.05, 0.85, 50.0, 70, (40.0, 40.0))
    # beat 6: ECMP
    ecmp(m, root, [6])

    a, f, fab = s["asic"], s["fans"], s["fabric"]
    tags = {
        0: [("spine switches", (D.SPINES[0], D.CH, -280.0)), ("leaf switches", (D.LEAVES[1], D.LY + D.LH, 460.0)),
            ("every leaf to every spine", D.fiber(1, 3)[3])],
        1: [("lid off: one 2RU spine", (D.CX0, D.CH, -300.0)), ("switch ASIC", a["top"]), ("fan wall", (D.FANS[0], D.FAN_Y + 31, D.FAN_Z[1])),
            ("power supplies", f["psu"])],
        2: [("64 x 800G OSFP ports", D.port(3, 3)), ("pluggable optics", D.port(12, 2)), ("link LEDs", (D.COLS[8] + 9, D.ROWS[1] + 12, 1.0))],
        3: [("one ASIC: 51.2 Tb/s", a["die"]), ("heatsink lifted", (0.0, D.HS_Y[1] + 140, D.HS[3])), ("~500 W class chip", (D.SUBH, 8.0, D.ASIC[1] + D.SUBH))],
        4: [("SerDes traces", (D.COLS[2], D.TY, -120.0)), ("512 lanes x 100G", a["die"]), ("in on one port, out another", D.port(13, 3))],
        5: [("cool air in the front", (-150.0, 44.0, 60.0)), ("over the heatsink", a["top"]), ("hot air out the back", (D.FANS[3], D.FAN_Y, D.CZ0))],
        6: [("ECMP: 4 equal paths", (D.SPINES[1], D.CH, -100.0)), ("from leaf 2", D.leaf_port(1, 0)), ("to leaf 7", D.leaf_port(6, 3))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera_path(root, [
        frame((-450.0, -150.0, 50.0), 3300.0, 0.0, 0.30, pad=1.0),
        frame((0.0, 30.0, -260.0), 620.0, 0.35, 0.75, pad=1.0),
        frame((0.0, 40.0, 0.0), 430.0, 0.12, 0.20, pad=1.0),
        frame((0.0, 40.0, -260.0), 220.0, 0.30, 0.65),
        frame((0.0, 10.0, -150.0), 440.0, 0.10, 0.95, pad=1.0),
        frame((0.0, 40.0, -300.0), 600.0, 0.45, 0.85, pad=1.0),
        frame((-450.0, -150.0, 50.0), 3300.0, 0.10, 0.25, pad=1.0),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
