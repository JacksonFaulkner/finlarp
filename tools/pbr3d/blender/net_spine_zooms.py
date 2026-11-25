"""Zoom-ins (a-e) for the SPINE page: the overview's scene (net_spine_detail.scene) with its own camera,
beads and tags, three beats each (diagrams_nodes/netcool/spine/zooms.rs):

  a front panel     64 OSFP cages in 4 rows of 16, an 800G module in each, link LEDs
  b the ASIC        heatsink on, heatsink lifting, the chip's lid glowing hot
  c SerDes lanes    copper traces from the ASIC's edge to every cage, packets in and out
  d fans and power  fan wall, front-to-back air, PSUs at the rear
  e ECMP            every leaf to every spine; flows hashed across four paths; one link fails

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/net_spine_zooms.py -- a

Writes assets/net_spine_zoom_<letter>.glb (and blender/net_spine_zoom_<letter>.blend).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_spine_detail as D  # noqa: E402
from net_spine_detail import frame, camera_path, run, rise  # noqa: E402
import net_spine_overview as OV  # noqa: E402

PAGE = "net_spine"
BEATS = 3


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def zoom_a(m, root, s):
    D.present(s["lid"], beat(0) + beat(1))
    for c in (2, 7, 12):
        run(root, f"a_in{c}", [(D.COLS[c], D.ROWS[2] + 7, 140.0), D.port(c, 2), (D.COLS[c], D.ROWS[2] + 7, -60.0)],
            4, 1.6, m["light"], [1, 2], 0.0, 0.8, 50)
    tags(root, [
        [("64 ports, 4 rows of 16", D.port(1, 3)), ("2RU: 88 mm tall", (D.CX1, D.CH, 0.0)), ("OSFP cages", D.port(14, 0))],
        [("800G OSFP module", D.port(7, 2)), ("pull tab", (D.COLS[12], D.ROWS[2] + 7, D.MOD_OUT)), ("light in from the fibre", (D.COLS[2], D.ROWS[2] + 7, 140.0))],
        [("module seats in its cage", (D.COLS[7], D.ROWS[2] + 14, -40.0)), ("electrical edge to the board", (D.COLS[12], D.ROWS[2], -62.0))],
    ])
    camera_path(root, [
        frame((0.0, 44.0, 0.0), 450.0, 0.0, 0.10, pad=1.0),
        frame((D.COLS[7], 50.0, 10.0), 130.0, 0.35, 0.25),
        frame((D.COLS[9], 50.0, -40.0), 170.0, 0.30, 0.85),
    ])


def zoom_b(m, root, s):
    OV.lift_hs(s, 1, 0.1, 0.5, 150.0)
    show(s["asic"]["glow"], span(2, 0.2, 3, 0.0))
    rise(root, "b_heat", (0.0, D.HS_Y[1], D.ASIC[1]), 6, 2.0, m["heat"], 0, 0.05, 0.85, 50.0, 70, (40.0, 40.0))
    rise(root, "b_heat2", (0.0, 18.0, D.ASIC[1]), 6, 1.4, m["heat"], 2, 0.3, 0.85, 40.0, 60, (24.0, 24.0))
    tags(root, [
        [("finned heatsink", (D.HS[1], D.HS_Y[1], D.HS[3])), ("heat pipes", (30.0, 60.0, D.HS[3] - 4)), ("heat rises off it", (0.0, D.HS_Y[1] + 40, D.ASIC[1]))],
        [("heatsink lifts", (0.0, D.HS_Y[1] + 150, D.HS[3])), ("ASIC under it", s["asic"]["die"])],
        [("one chip: 51.2 Tb/s", s["asic"]["die"]), ("Tomahawk 5: 5 nm", (D.SUBH, 8.0, D.ASIC[1] + D.SUBH)), ("decoupling caps", (-36.0, 11.0, D.ASIC[1] + 36))],
    ])
    camera_path(root, [
        frame((0.0, 50.0, -260.0), 260.0, 0.35, 0.40),
        frame((0.0, 90.0, -260.0), 340.0, 0.35, 0.40),
        frame((0.0, 12.0, -250.0), 140.0, 0.25, 0.70),
    ])


def zoom_c(m, root, s):
    D.present(s["asic"]["hs"], [])
    OV.serdes(m, root, [0, 1, 2], cols=range(0, 16, 2))
    OV.serdes(m, root, [1, 2], cols=range(1, 16, 2), n=2)
    tags(root, [
        [("copper SerDes traces", (D.COLS[3], D.TY, -120.0)), ("from the ASIC's edge", (0.0, 12.0, D.ASIC[1] + D.SUBH))],
        [("8 lanes per 800G port", D.port(4, 1)), ("100G each, PAM4", (D.COLS[11], D.TY, -110.0))],
        [("in on one port", D.port(0, 1)), ("out on another", D.port(15, 3)), ("512 lanes in all", s["asic"]["die"])],
    ])
    camera_path(root, [
        frame((0.0, 10.0, -180.0), 200.0, 0.15, 0.85),
        frame((-60.0, 10.0, -80.0), 220.0, 0.30, 0.55),
        frame((0.0, 10.0, -150.0), 440.0, 0.0, 1.0, pad=1.0),
    ])


def zoom_d(m, root, s):
    D.airflow(root, m, [0, 1, 2], n=10)
    show(s["asic"]["glow"], beat(1))
    rise(root, "d_heat", (0.0, D.HS_Y[1], D.ASIC[1]), 6, 2.0, m["heat"], 1, 0.05, 0.85, 50.0, 70, (40.0, 40.0))
    tags(root, [
        [("4 fans", (D.FANS[1], D.FAN_Y + 31, D.FAN_Z[1])), ("air: front to back", (-150.0, 44.0, 40.0))],
        [("heatsink takes the ASIC's heat", s["asic"]["top"]), ("optics add ~15 W each", D.port(14, 3))],
        [("2 PSUs, redundant", s["fans"]["psu"]), ("hot air out the rear", (D.FANS[3], D.FAN_Y, D.CZ0))],
    ])
    camera_path(root, [
        frame((0.0, 44.0, -430.0), 260.0, 0.45, 0.35),
        frame((0.0, 40.0, -280.0), 600.0, 0.45, 0.85, pad=1.0),
        frame((0.0, 30.0, -480.0), 460.0, 2.6, 0.45, pad=1.0),
    ])


def zoom_e(m, root, s):
    D.present(s["lid"], span(0, 0.0, 3, 0.0))
    show(s["fabric"]["leds"], span(0, 0.0, 3, 0.0))
    OV.ecmp(m, root, [0], 0, 4, n=2)
    OV.ecmp(m, root, [1], 1, 6, n=3)
    OV.ecmp(m, root, [1], 3, 0, n=2, u0=0.2)
    OV.ecmp(m, root, [2], 1, 6, n=4, spines=(0, 2, 3))
    fail = D.empty("e_fail", root)
    D.polyline("e_fail_l", D.fiber(1, 1), 4.0, m["fail"], fail)
    show(fail, span(2, 0.0, 3, 0.0))
    tags(root, [
        [("each leaf: a link to every spine", D.leaf_port(0, 2)), ("4 spines", (D.SPINES[3], D.CH, -280.0))],
        [("flows hashed over 4 equal paths", (D.SPINES[1], D.CH, -100.0)), ("any leaf, 2 hops to any other", D.leaf_port(6, 3))],
        [("a link fails", D.fiber(1, 1)[3]), ("traffic rehashes onto 3", (D.SPINES[2], D.CH, -100.0))],
    ])
    camera_path(root, [
        frame((-450.0, -150.0, 50.0), 3300.0, 0.0, 0.30, pad=1.0),
        frame((-450.0, -150.0, 50.0), 3200.0, -0.12, 0.20, pad=1.0),
        frame((-900.0, -200.0, 150.0), 2300.0, 0.0, 0.25, pad=1.0),
    ])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root, BEATS)
    D.leds_on(s, range(BEATS))
    if letter in "bcd":
        D.present(s["lid"], [])
    ZOOMS[letter](m, root, s)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python net_spine_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
