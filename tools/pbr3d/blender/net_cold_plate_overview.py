"""The COLD PLATE page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/net_cold_plate_overview.py

Writes blender/net_cold_plate_overview.blend and assets/net_cold_plate_overview.glb. One beat is 8 s.

A GPU compute tray cut through the middle of the GPU (net_cold_plate_detail.py): the package and
its dies, the TIM, the copper cold plate with its microchannel fins and cover, the hoses to the
tray's rear quick disconnects, and the rack manifolds behind.

Beats (match the seven beats in diagrams_nodes/netcool/cold_plate/overview.rs):
  0 tray        the tray: GPU under its cold plate, hoses, quick disconnects, manifolds
  1 cool in     blue coolant up the supply manifold, through the QD and hose into the plate
  2 heat        the dies glow; heat climbs through the TIM and copper base into the fins
  3 fins        coolant runs the microchannels, warming from blue to orange
  4 warm out    warm water leaves by the outlet hose, QD and return manifold: 45-60 C
  5 QDs         the tray slides out; the dripless quick disconnects part and seal
  6 rack        every tray on the manifold, all flows at once
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_cold_plate_detail as D  # noqa: E402
from net_cold_plate_detail import frame, camera_path  # noqa: E402

PAGE = "net_cold_plate"
NAME = "overview"
BEATS = 7


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    D.flow_in(m, root, [1, 6])
    D.flow_plate(m, root, [1, 3, 4, 6], 0.1)
    show(s["die_glow"], span(2, 0.0, 5, 0.0) + beat(6))
    D.heat_up(m, root, [2, 3])
    show(s["chan_cool"], span(1, 0.4, 3, 0.5))
    show(s["chan_warm"], span(3, 0.5, 5, 0.0) + beat(6))
    D.flow_out(m, root, [4, 6])
    D.slide(s["tray"], 5)
    D.rack_flows(m, root, [6])
    D.present(s["others"], beat(6))
    for le in s["leds"]:
        D.blink(le, 6, range(8), 8, 0.5)
    pp, pk = s["plate"], s["pkg"]
    tags = {
        0: [("GPU under its cold plate", pp["cover"]), ("hoses", (D.IN_X, D.QY + 6.0, -110.0)), ("quick disconnects", s["qd"]),
            ("rack manifolds", s["man"])],
        1: [("supply manifold", (D.IN_X, 20.0, D.MAN_Z)), ("cool in: ~25-45 C", (D.IN_X, D.QY + 6.0, -110.0)), ("into the plate", pp["inlet"])],
        2: [("GPU: ~1,000-1,400 W", pk["die_face"]), ("TIM", pp["tim"]), ("copper base", pp["base"])],
        3: [("microchannel fins", pp["fins"]), ("inlet over the dies", pp["slot"]), ("warms as it goes", pp["plenum"])],
        4: [("warm out: ~45-60 C", (D.OUT_X, D.QY + 6.0, -110.0)), ("return manifold", (D.OUT_X, 150.0, D.MAN_Z))],
        5: [("tray slides out", (100.0, 20.0, 20.0)), ("dripless QDs seal", s["qd"])],
        6: [("every tray on one loop", (0.0, D.TRAY_DY + 40.0, 0.0)), ("to the CDU", s["cdu"]), ("~120-130 kW per rack", (D.OUT_X, 180.0, D.MAN_Z))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))
    camera_path(root, [
        frame((0.0, 30.0, -110.0), 380.0, 0.55, 0.40, pad=1.0),
        frame((-10.0, 50.0, -150.0), 300.0, 0.85, 0.30, pad=1.0),
        frame((0.0, 16.0, 0.0), 110.0, 0.12, 0.12),
        frame((0.0, 26.0, -20.0), 130.0, 0.25, 0.35),
        frame((15.0, 60.0, -160.0), 300.0, -0.85, 0.30, pad=1.0),
        frame((0.0, 50.0, -170.0), 280.0, 0.95, 0.35, pad=1.0),
        frame((0.0, 40.0, -120.0), 520.0, 0.65, 0.25, pad=1.0),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
