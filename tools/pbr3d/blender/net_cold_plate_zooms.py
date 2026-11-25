"""Zoom-ins (a-e) for the COLD PLATE page: the overview's tray (net_cold_plate_detail.scene) with its
own camera, beads and tags, three beats each (diagrams_nodes/netcool/cold_plate/zooms.rs):

  a the plate cut open     base, fins, cover: the stack on the cut face
  b TIM and heat           the dies heat up; heat crosses the TIM into the copper
  c microchannels          coolant enters over the dies and runs the channels, warming
  d quick disconnects      the tray's QDs mate with the rack's; the tray slides out dry
  e rack manifolds         supply up one pipe, return up the other, every tray tapped in

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/net_cold_plate_zooms.py -- a

Writes assets/net_cold_plate_zoom_<letter>.glb (and blender/net_cold_plate_zoom_<letter>.blend).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_cold_plate_detail as D  # noqa: E402
from net_cold_plate_detail import frame, camera_path  # noqa: E402

PAGE = "net_cold_plate"
BEATS = 3


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def zoom_a(m, root, s):
    pp = s["plate"]
    D.flow_plate(m, root, [2], 0.05)
    show(s["chan_cool"], beat(2))
    tags(root, [
        [("copper base", pp["base"]), ("TIM on the dies", pp["tim"]), ("GPU package", s["pkg"]["sub"])],
        [("skived copper fins", pp["fins"]), ("nickel-plated cover", pp["cover"]), ("spring screws", pp["spring"])],
        [("inlet over the dies", pp["slot"]), ("outlet plenum", pp["plenum"])],
    ])
    camera_path(root, [
        frame((0.0, 16.0, 0.0), 120.0, 0.15, 0.10),
        frame((0.0, 28.0, -10.0), 140.0, 0.45, 0.35),
        frame((0.0, 40.0, -40.0), 170.0, 0.60, 0.55),
    ])


def zoom_b(m, root, s):
    show(s["die_glow"], span(0, 0.2, 3, 0.0))
    D.heat_up(m, root, [1, 2], name="bh")
    D.flow_plate(m, root, [2], 0.05)
    show(s["chan_warm"], beat(2))
    pp, pk = s["plate"], s["pkg"]
    tags(root, [
        [("two GPU dies", pk["die_face"]), ("HBM stacks", pk["hbm"]), ("~1,000-1,400 W", (0.0, D.DIE_Y[1], -30.0))],
        [("TIM fills the gaps", pp["tim"]), ("heat into the copper", pp["base"])],
        [("into the fins", pp["fins"]), ("water carries it off", pp["plenum"])],
    ])
    camera_path(root, [
        frame((0.0, 8.0, 0.0), 80.0, 0.10, 0.10, min_d=40.0),
        frame((-20.0, 13.0, 0.0), 60.0, 0.10, 0.05, min_d=34.0),
        frame((0.0, 22.0, 0.0), 100.0, 0.15, 0.15),
    ])


def zoom_c(m, root, s):
    D.flow_plate(m, root, [0, 1, 2], 0.0, n=4)
    show(s["chan_cool"], span(0, 0.0, 1, 0.5))
    show(s["chan_warm"], span(1, 0.5, 3, 0.0))
    D.heat_up(m, root, [1], name="ch")
    pp = s["plate"]
    tags(root, [
        [("cool water in", pp["inlet"]), ("drops onto the hottest spot", pp["slot"])],
        [("channels ~0.1-0.3 mm wide", pp["fins"]), ("huge wetted area", (30.0, D.FIN_Y[1], 0.0))],
        [("warm water to the plenum", pp["plenum"]), ("out to the hose", pp["outlet"])],
    ])
    camera_path(root, [
        frame((0.0, 40.0, -20.0), 110.0, 0.35, 0.45),
        frame((0.0, 25.0, 0.0), 90.0, 0.10, 0.12),
        frame((15.0, 40.0, -50.0), 150.0, -0.55, 0.45),
    ])


def zoom_d(m, root, s):
    D.flow_in(m, root, [0])
    D.flow_out(m, root, [0])
    D.slide(s["tray"], 1, 70.0)
    D.blink(s["leds"][-1], 2, range(8), 8, 0.5)
    tags(root, [
        [("tray half", (D.IN_X, D.QY + 8.0, D.QD_Z[0])), ("rack half", (D.OUT_X, D.QY + 8.0, D.QD_Z[2])), ("supply / return", s["qd"])],
        [("tray slides out", (D.OUT_X, D.QY + 8.0, -120.0)), ("valves snap shut", s["qd"])],
        [("blind-mate back in", s["qd"]), ("no tools, no drips", (D.IN_X, D.QY + 8.0, -160.0))],
    ])
    camera_path(root, [
        frame((0.0, D.QY, D.QD_Z[1]), 90.0, 0.85, 0.30),
        frame((0.0, D.QY, -170.0), 180.0, 1.05, 0.35),
        frame((0.0, D.QY, D.QD_Z[1]), 100.0, 0.80, 0.30),
    ])


def zoom_e(m, root, s):
    D.present(s["others"], span(0, 0.0, 3, 0.0))
    D.rack_flows(m, root, [0, 1, 2])
    D.flow_in(m, root, [1, 2])
    D.flow_out(m, root, [2])
    for le in s["leds"]:
        D.blink(le, 2, range(8), 8, 0.5)
    tags(root, [
        [("supply manifold", (D.IN_X, 40.0, D.MAN_Z)), ("return manifold", (D.OUT_X, 150.0, D.MAN_Z)), ("from the CDU", s["cdu"])],
        [("one QD pair per tray", s["qd"]), ("cool in", (D.IN_X, D.QY + D.TRAY_DY, D.MAN_Z))],
        [("warm out: ~45-60 C", (D.OUT_X, 200.0, D.MAN_Z)), ("back to the CDU", (D.OUT_X, D.MAN_Y[1], D.MAN_Z))],
    ])
    camera_path(root, [
        frame((0.0, 30.0, D.MAN_Z), 420.0, 1.25, 0.15, pad=1.0),
        frame((0.0, D.QY, -220.0), 160.0, 1.10, 0.25),
        frame((0.0, 40.0, -150.0), 500.0, 0.75, 0.20, pad=1.0),
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
        raise SystemExit("usage: blender -b --python net_cold_plate_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
