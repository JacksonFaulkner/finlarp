"""The CDU page's overview, in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/net_cdu_overview.py

Writes blender/net_cdu_overview.blend and assets/net_cdu_overview.glb. One beat is 8 s.

An in-row coolant distribution unit beside the liquid-cooled rack it feeds, both cut open
(net_cdu_detail.py).

Beats (match the seven beats in diagrams_nodes/netcool/cdu/overview.rs):
  0 the CDU        the cabinet beside the rack: PHE, pumps, filter, reservoir, controller
  1 two loops      facility water rises from the floor into the PHE; the secondary loop stays sealed
  2 the pumps      pump A spins; coolant goes reservoir > pump > filter > PHE > supply manifold
  3 cold plates    cool supply through every tray's cold plates; warm return rises; GPUs glow
  4 the exchanger  heat hops across the plates; facility water leaves warmer, back to the chiller
  5 controls       sensors blink and report; the valve trims facility flow; pump B on standby
  6 running        both loops at once
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_cdu_detail as D  # noqa: E402
from net_cdu_detail import frame, camera_path  # noqa: E402

PAGE = "net_cdu"
NAME = "overview"
BEATS = 7


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    pa = s["pumps"]["A"]

    D.facility(root, m, [1, 4, 6])
    D.secondary(root, m, [2, 3, 6])
    D.run(root, "s_ret1", D.p_sec_ret(), 5, 1.6, m["b_ret"], [1], 0.1, 0.85, 70)
    D.spin(pa["imp"], 0, BEATS)
    D.trays(root, m, [4], 0.0, 0.8, ks=(0, 2, 4, 6))
    show(s["rack"]["gpu_glow"], span(3, 0.0, 5, 0.0) + span(6, 0.0, 7, 0.0))
    D.gpu_heat(root, m, 3)
    D.phe_transfer(root, m, [4, 6])
    D.leds_on(s, [5, 6])
    D.pulses(root, m, s, [5])
    D.blink(s["ctrl"]["screen"], 5, range(8), 8, 0.8)

    ph, fl, rs, ctl, vl = s["phe"], s["filter"], s["res"], s["ctrl"], s["valve"]
    tags = {
        0: [("in-row CDU", (-40.0, 200.0, -10.0)), ("plate heat exchanger", (-46.0, 170.0, -42.0)),
            ("pumps A + B", pa["top"]), ("liquid-cooled rack", (40.0, 214.0, -10.0))],
        1: [("facility water in", (-66.0, 40.0, -78.0)), ("facility water out", (-66.0, 60.0, -52.0)),
            ("secondary loop: sealed", (20.0, 222.0, D.MAN_Z))],
        2: [("pump A running", pa["top"]), ("filter", fl["top"]), ("reservoir", rs["top"]),
            ("to the rack", (10.0, 214.0, -78.0))],
        3: [("cold plates on every GPU", (32.0, D.TRAY_Y[5] + 6.0, -30.0)), ("supply ~30-40 C", (D.MAN_SUP_X, 120.0, D.MAN_Z)),
            ("return ~10 C warmer", (D.MAN_RET_X, 180.0, D.MAN_Z))],
        4: [("heat crosses the plates", (-46.0, 168.0, -42.0)), ("counterflow", (-30.0, 126.0, -52.0)),
            ("warmer, to the chiller", (-66.0, 40.0, -52.0))],
        5: [("controller (PLC)", ctl["at"]), ("T / P / flow sensors", s["sens"]["pts"]["T_sup"]),
            ("facility valve", vl["act"]), ("pump B: standby", s["pumps"]["B"]["top"])],
        6: [("facility loop", (-66.0, 40.0, -78.0)), ("CDU", (-40.0, 200.0, -10.0)), ("secondary loop", (40.0, 214.0, -10.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera_path(root, [
        frame((0.0, 110.0, -55.0), 260.0, -0.30, 0.22, pad=1.0),
        frame((-45.0, 90.0, -60.0), 230.0, -0.45, 0.15, pad=1.0),
        frame((-36.0, 80.0, -50.0), 150.0, -0.35, 0.25),
        frame((40.0, 120.0, -50.0), 200.0, -0.50, 0.25),
        frame((-46.0, 143.0, -60.0), 90.0, -0.25, 0.20),
        frame((-38.0, 140.0, -45.0), 160.0, -0.30, 0.15),
        frame((0.0, 110.0, -55.0), 270.0, -0.25, 0.25, pad=1.0),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
