"""Zoom-ins (a-e) for the CDU page: the overview's CDU and rack (net_cdu_detail.scene) with their
own camera, beads and tags, three beats each (diagrams_nodes/netcool/cdu/zooms.rs):

  a plate heat exchanger   the plate stack, counterflow through alternate gaps, the approach
  b pumps                  pump A's impeller spinning, B on standby, B taking over
  c filter and reservoir   the strainer cut open, the expansion tank, the pressure drop gauge
  d sensors and controls   T, P and flow points reporting; the valve trimming; leak detection
  e in-rack vs in-row      a 4U CDU in the bottom of one rack; one row CDU feeding four racks

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/net_cdu_zooms.py -- a

Writes assets/net_cdu_zoom_<letter>.glb (and blender/net_cdu_zoom_<letter>.blend).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_cdu_detail as D  # noqa: E402
from net_cdu_detail import frame, camera_path, run  # noqa: E402

PAGE = "net_cdu"
BEATS = 3


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


V_PHE = frame((-46.0, 143.0, -60.0), 80.0, -0.25, 0.20)


def zoom_a(m, root, s):
    run(root, "a_sec", D.p_sec_phe(), 8, 1.8, m["b_sup"], [0, 2], 0.0, 0.85, 60)
    run(root, "a_fac", D.p_fac_phe(), 8, 1.8, m["b_fac"], [1, 2], 0.0, 0.85, 60)
    run(root, "a_si", D.p_sec_filter()[-3:], 4, 2.0, m["b_ret"], [0, 2], 0.0, 0.6, 40)
    run(root, "a_fi", D.p_fac_in()[1:], 4, 2.2, m["b_fac"], [1, 2], 0.0, 0.6, 30)
    run(root, "a_fo", D.p_fac_out()[:2], 4, 2.2, m["b_facw"], [1, 2], 0.3, 0.9, 20)
    D.phe_transfer(root, m, [2], n=14)
    x0, x1, y0, y1, z0, z1 = D.PHE
    tags(root, [
        [("stainless plates, pressed", (-46.0, y1, z1)), ("secondary: warm in, bottom", (x1, 126.0, -52.0)),
         ("leaves cool, top", (x1, 160.0, -78.0))],
        [("facility: cold in, top", (x0, 160.0, -78.0)), ("alternate gaps", (-46.0, 143.0, z1)),
         ("out warmer, bottom", (x0, 126.0, -52.0))],
        [("heat crosses ~0.5 mm of steel", (-46.0, 150.0, z1)), ("counterflow: ~2-4 C approach", (x1, 143.0, -60.0)),
         ("tie bolts hold the stack", (x1 + 3.0, y1 + 1.0, z1 + 1.0))],
    ])
    camera_path(root, [V_PHE, frame((-50.0, 143.0, -60.0), 80.0, -0.55, 0.15), frame((-46.0, 143.0, -55.0), 70.0, -0.10, 0.10)])


def zoom_b(m, root, s):
    pa, pb = s["pumps"]["A"], s["pumps"]["B"]
    D.spin(pa["imp"], 0, 2)
    D.spin(pb["imp"], 2, 3, rps=0.6)
    run(root, "b_a", D.p_sec_pump("A"), 6, 2.0, m["b_ret"], [0, 1], 0.0, 0.85, 80)
    run(root, "b_b", D.p_sec_pump("B"), 6, 2.0, m["b_ret"], [2], 0.15, 0.85, 80)
    show(pa["led"], span(0, 0.0, 2, 0.1))
    D.blink(pb["led"], 1, range(8), 8, 0.5)
    tags(root, [
        [("pump A: running", pa["top"]), ("impeller, cut open", pa["volute"]), ("motor + VFD", (D.PUMPS["A"], D.PUMP_Y + 8.0, D.PUMP_Z - 30.0))],
        [("pump B: standby (N+1)", pb["top"]), ("common suction header", (-30.0, D.PUMP_Y, D.HDR_Z))],
        [("A trips: B takes over", pb["top"]), ("flow held, seconds", (-20.0, 56.0, D.PUMP_Z))],
    ])
    camera_path(root, [frame((-44.0, 34.0, -60.0), 70.0, -0.35, 0.25), frame((-38.0, 38.0, -70.0), 90.0, -0.10, 0.35),
                       frame((-38.0, 38.0, -65.0), 90.0, 0.10, 0.30)])


def zoom_c(m, root, s):
    fl, rs = s["filter"], s["res"]
    run(root, "c_f", D.p_sec_filter(), 7, 1.8, m["b_ret"], [0, 2], 0.0, 0.85, 70)
    run(root, "c_r", D.p_sec_ret()[-2:], 5, 2.0, m["b_ret"], [1, 2], 0.0, 0.85, 40)
    run(root, "c_r2", D.p_sec_pump("A")[:3], 5, 2.0, m["b_ret"], [1, 2], 0.2, 0.85, 50)
    D.blink(fl["gauge"], 0, range(8), 8, 0.6)
    tags(root, [
        [("canister strainer, cut open", fl["mid"]), ("pleated element: ~25-50 micron", (D.FILT[0], 80.0, D.FILT[3])),
         ("differential pressure gauge", (D.FILT[0] + 9.0, D.FILT[2] - 4.0, D.FILT[3]))],
        [("reservoir / expansion tank", rs["top"]), ("sight glass: level", (D.RES[0] + 7.0, 160.0, D.RES[3])),
         ("takes up thermal swell", (D.RES[0], 150.0, D.RES[3]))],
        [("clean coolant protects", (D.FILT[0], D.FILT[2], D.FILT[3])), ("cold plate micro-channels", (32.0, D.TRAY_Y[3] + 6.0, -30.0))],
    ])
    camera_path(root, [frame((-20.0, 82.0, -26.0), 60.0, -0.20, 0.15), frame((-16.0, 163.0, -30.0), 70.0, -0.20, 0.10),
                       frame((0.0, 100.0, -40.0), 150.0, -0.30, 0.20)])


def zoom_d(m, root, s):
    D.leds_on(s, [0, 1, 2])
    D.pulses(root, m, s, [0, 1])
    D.blink(s["ctrl"]["screen"], 0, range(8), 8, 0.85)
    vf = s["valve"]["pos"]
    for i, (u, a) in enumerate(((0.0, 0.0), (0.3, 0.0), (0.6, 0.9), (0.95, 0.9))):
        key(vf, F(1, u), "rotation_euler", (0.0, a, 0.0), linear=True)
    D.facility(root, m, [1], n=6)
    D.run(root, "d_leak", [(30.0, D.TRAY_Y[2] + 5.0, -60.0), (30.0, 9.0, -60.0)], 3, 1.2, m["leak"], 2, 0.1, 0.6, 30)
    tags(root, [
        [("supply temp, pressure, flow", s["sens"]["pts"]["T_sup"]), ("return temp", s["sens"]["pts"]["T_ret"]),
         ("controller (PLC)", s["ctrl"]["at"])],
        [("valve trims facility flow", s["valve"]["act"]), ("holds supply temp", s["sens"]["pts"]["T_sup"])],
        [("leak: drips detected", (30.0, 12.0, -60.0)), ("leak rope + alarm", (-40.0, 9.0, -19.0)), ("isolate and alarm", s["ctrl"]["at"])],
    ])
    camera_path(root, [frame((-40.0, 170.0, -40.0), 110.0, -0.30, 0.15), frame((-60.0, 110.0, -60.0), 110.0, -0.55, 0.10),
                       frame((0.0, 60.0, -30.0), 160.0, -0.20, 0.25)])


def zoom_e(m, root, s):
    ir = s["inrack"]
    D.present(ir["g"], beat(0) + beat(1))
    D.present(s["row"]["g"], beat(2))
    run(root, "e_irf", D.p_inrack_fac(), 6, 1.8, m["b_fac"], [0, 1], 0.0, 0.85, 60)
    run(root, "e_irs", D.p_inrack_sec(), 6, 1.6, m["b_sup"], [0, 1], 0.05, 0.85, 60)
    D.trays(root, m, [1, 2], 0.1, 0.8, ks=(0, 2, 4, 6))
    D.secondary(root, m, [2], n=4)
    for i in range(3):
        run(root, f"e_rs{i}", D.p_row_sup(i), 4, 2.0, m["b_sup"], 2, 0.1 + 0.05 * i, 0.85, 80)
        run(root, f"e_rr{i}", D.p_row_ret(i), 4, 2.0, m["b_ret"], 2, 0.2 + 0.05 * i, 0.85, 80)
    show(ir["led"], beat(0) + beat(1))
    tags(root, [
        [("in-rack CDU: 4U", ir["at"]), ("brazed plate HX + 2 pumps", (24.0, 22.0, -55.0))],
        [("one rack, ~100-250 kW", (40.0, 214.0, -10.0)), ("no floor space", (40.0, 4.0, -4.0))],
        [("in-row CDU: whole row", (-40.0, 200.0, -10.0)), ("header to every rack", (150.0, 222.0, D.MAN_Z)),
         ("~1-2 MW+ per unit", (-40.0, 150.0, -10.0))],
    ])
    camera_path(root, [frame((40.0, 20.0, -50.0), 80.0, -0.25, 0.40), frame((40.0, 100.0, -50.0), 200.0, -0.30, 0.20),
                       frame((90.0, 110.0, -55.0), 380.0, -0.25, 0.25, pad=1.0)])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root, row_racks=(letter == "e"), in_rack=(letter == "e"))
    ZOOMS[letter](m, root, s)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python net_cdu_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
