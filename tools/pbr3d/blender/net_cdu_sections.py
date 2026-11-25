"""The CDU page's nine numbered sections, in the picture-and-panel template (docs/diagram-pages.md).
Section N illustrates heading N of tui/src/screens/diagrams_pages/NET_CDU.txt (the tenth, Sources,
is text only). Three beats each, one beat is 8 s.

Run one section per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/net_cdu_sections.py -- <n>

Writes blender/net_cdu_section_<n>.blend and assets/net_cdu_section_<n>.glb. Everything comes from
net_cdu_detail.py (the in-row CDU, the rack, the in-rack CDU and the rest of the row).

  1 what happens   GPUs heat the cold plates; the secondary loop carries it; facility water takes it
  2 the parts      PHE; pumps, filter and reservoir; controller, sensors and manifolds
  3 in order       return > reservoir > pump; filter > PHE; supply > cold plates
  4 two loops      facility water stays out; the sealed loop is small and clean; held above dew point
  5 the PHE        the plate stack; counterflow; heat across the plates and the approach
  6 pumps etc.     N+1 pumps; filter; controller with sensors and valve
  7 in-rack/row    in-rack 4U CDU; one rack; in-row CDU feeding a row
  8 who makes it   makers tagged on the CDU, the in-rack unit and the row
  9 chokepoints    leaks; a pump or controller failure; rising rack heat
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_cdu_detail as D  # noqa: E402
from net_cdu_detail import frame, camera_path, run, rise  # noqa: E402

PAGE = "net_cdu"
BEATS = 3


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


V_ALL = frame((0.0, 110.0, -55.0), 260.0, -0.30, 0.22, pad=1.0)
V_RACK = frame((40.0, 120.0, -50.0), 200.0, -0.50, 0.25)
V_CDU = frame((-40.0, 100.0, -55.0), 210.0, -0.40, 0.18, pad=1.0)
V_PHE = frame((-46.0, 143.0, -60.0), 80.0, -0.25, 0.20)
V_PUMPS = frame((-36.0, 50.0, -55.0), 110.0, -0.35, 0.25)
V_TOP = frame((-40.0, 175.0, -40.0), 110.0, -0.30, 0.15)
V_ROW = frame((90.0, 110.0, -55.0), 380.0, -0.25, 0.25, pad=1.0)
V_IR = frame((40.0, 20.0, -50.0), 80.0, -0.25, 0.40)


def sec1(m, root):
    s = D.scene(m, root)
    D.spin(s["pumps"]["A"]["imp"], 0, 3)
    show(s["rack"]["gpu_glow"], beat(0) + beat(1))
    D.gpu_heat(root, m, 0, ks=(1, 3, 5, 7))
    D.trays(root, m, [0, 1], 0.1, 0.85)
    D.secondary(root, m, [1, 2])
    D.facility(root, m, [2])
    D.phe_transfer(root, m, [2])
    tags(root, [
        [("GPUs: ~1 kW each", (32.0, D.TRAY_Y[5] + 6.0, -30.0)), ("cold plates take the heat", (24.0, D.TRAY_Y[3] + 6.0, -60.0))],
        [("secondary loop carries it", (D.MAN_RET_X, 180.0, D.MAN_Z)), ("CDU pumps it round", s["pumps"]["A"]["top"])],
        [("PHE hands it on", (-46.0, 168.0, -42.0)), ("facility water takes it away", (-66.0, 40.0, -52.0))],
    ])
    camera_path(root, [V_RACK, V_ALL, V_CDU])


def sec2(m, root):
    s = D.scene(m, root)
    D.spin(s["pumps"]["A"]["imp"], 0, 3)
    D.phe_transfer(root, m, [0])
    D.leds_on(s, [2])
    D.blink(s["ctrl"]["screen"], 2, range(8), 8, 0.8)
    tags(root, [
        [("plate heat exchanger", (-46.0, 168.0, -42.0)), ("facility ports", (-62.0, 160.0, -78.0)), ("secondary ports", (-30.0, 126.0, -52.0))],
        [("pumps A + B", s["pumps"]["A"]["top"]), ("filter", s["filter"]["top"]), ("reservoir", s["res"]["top"])],
        [("controller", s["ctrl"]["at"]), ("sensors", s["sens"]["pts"]["T_sup"]), ("manifolds + quick disconnects", s["man"]["qd"])],
    ])
    camera_path(root, [V_PHE, V_PUMPS, frame((0.0, 150.0, -50.0), 200.0, -0.30, 0.18)])


def sec3(m, root):
    s = D.scene(m, root)
    D.spin(s["pumps"]["A"]["imp"], 0, 3)
    run(root, "r", D.p_sec_ret(), 6, 2.2, m["b_ret"], 0, 0.0, 0.6, 80)
    run(root, "p", D.p_sec_pump("A"), 6, 2.0, m["b_ret"], 0, 0.3, 0.85, 80)
    run(root, "f", D.p_sec_filter(), 6, 2.0, m["b_ret"], 1, 0.0, 0.6, 60)
    run(root, "h", D.p_sec_phe(), 6, 1.8, m["b_sup"], 1, 0.3, 0.85, 60)
    run(root, "s", D.p_sec_sup(), 6, 2.2, m["b_sup"], 2, 0.0, 0.5, 80)
    D.trays(root, m, [2], 0.3, 0.9)
    tags(root, [
        [("1 warm return", (20.0, 222.0, D.MAN_Z)), ("2 reservoir", s["res"]["top"]), ("3 pump", s["pumps"]["A"]["top"])],
        [("4 filter", s["filter"]["top"]), ("5 PHE: heat out", (-46.0, 168.0, -42.0))],
        [("6 cool supply", (10.0, 214.0, -78.0)), ("7 cold plates", (32.0, D.TRAY_Y[4] + 6.0, -30.0)), ("8 back to 1", (D.MAN_RET_X, 180.0, D.MAN_Z))],
    ])
    camera_path(root, [V_CDU, frame((-36.0, 115.0, -45.0), 130.0, -0.30, 0.15), V_RACK])


def sec4(m, root):
    s = D.scene(m, root)
    D.facility(root, m, [0, 2])
    D.secondary(root, m, [1, 2])
    D.spin(s["pumps"]["A"]["imp"], 0, 3)
    tags(root, [
        [("facility water: big, shared", (-66.0, 40.0, -78.0)), ("stops at the PHE", (-62.0, 150.0, -78.0)),
         ("never enters the servers", (40.0, 214.0, -10.0))],
        [("sealed loop: tens of litres", (20.0, 222.0, D.MAN_Z)), ("clean, treated (e.g. PG25)", s["filter"]["top"])],
        [("supply held above dew point", s["sens"]["pts"]["T_sup"]), ("set flow + pressure", s["sens"]["pts"]["F_sup"])],
    ])
    camera_path(root, [V_CDU, V_ALL, V_TOP])


def sec5(m, root):
    s = D.scene(m, root)
    run(root, "a_sec", D.p_sec_phe(), 8, 1.8, m["b_sup"], [0, 1, 2], 0.0, 0.85, 60)
    run(root, "a_fac", D.p_fac_phe(), 8, 1.8, m["b_fac"], [1, 2], 0.0, 0.85, 60)
    D.phe_transfer(root, m, [2], n=14)
    tags(root, [
        [("~100-300 thin plates (real)", (-46.0, 168.0, -42.0)), ("gasketed, bolted frame", (-30.0, 170.0, -42.0))],
        [("two fluids, alternate gaps", (-46.0, 143.0, -41.0)), ("counterflow", (-30.0, 126.0, -52.0))],
        [("approach: ~2-4 C", (-46.0, 150.0, -41.0)), ("more plates = more kW", (-62.0, 120.0, -42.0))],
    ])
    camera_path(root, [V_PHE, frame((-50.0, 143.0, -60.0), 80.0, -0.55, 0.15), frame((-46.0, 143.0, -55.0), 70.0, -0.10, 0.10)])


def sec6(m, root):
    s = D.scene(m, root)
    D.spin(s["pumps"]["A"]["imp"], 0, 3)
    run(root, "p", D.p_sec_pump("A"), 6, 2.0, m["b_ret"], [0, 1], 0.0, 0.85, 80)
    run(root, "f", D.p_sec_filter(), 6, 2.0, m["b_ret"], 1, 0.0, 0.85, 60)
    D.blink(s["pumps"]["B"]["led"], 0, range(8), 8, 0.5)
    D.leds_on(s, [2])
    D.pulses(root, m, s, [2])
    D.blink(s["ctrl"]["screen"], 2, range(8), 8, 0.8)
    vf = s["valve"]["pos"]
    for u, a in ((0.0, 0.0), (0.4, 0.0), (0.8, 0.9)):
        key(vf, F(2, u), "rotation_euler", (0.0, a, 0.0), linear=True)
    tags(root, [
        [("2 pumps, N+1", s["pumps"]["A"]["top"]), ("variable speed", (D.PUMPS["A"], D.PUMP_Y + 8.0, D.PUMP_Z - 30.0))],
        [("filter on the discharge", s["filter"]["mid"]), ("strains to ~25-50 micron", s["filter"]["top"])],
        [("PLC reads T, P, flow", s["ctrl"]["at"]), ("valve sets the heat removed", s["valve"]["act"])],
    ])
    camera_path(root, [V_PUMPS, frame((-20.0, 82.0, -26.0), 60.0, -0.20, 0.15), frame((-50.0, 140.0, -40.0), 150.0, -0.40, 0.15)])


def sec7(m, root):
    s = D.scene(m, root, row_racks=True, in_rack=True)
    ir = s["inrack"]
    D.present(ir["g"], beat(0) + beat(1))
    D.present(s["row"]["g"], beat(2))
    run(root, "irf", D.p_inrack_fac(), 6, 1.8, m["b_fac"], [0, 1], 0.0, 0.85, 60)
    run(root, "irs", D.p_inrack_sec(), 6, 1.6, m["b_sup"], [0, 1], 0.05, 0.85, 60)
    D.trays(root, m, [1], 0.1, 0.8)
    D.secondary(root, m, [2], n=4)
    for i in range(3):
        run(root, f"rs{i}", D.p_row_sup(i), 4, 2.0, m["b_sup"], 2, 0.1 + 0.05 * i, 0.85, 80)
        run(root, f"rr{i}", D.p_row_ret(i), 4, 2.0, m["b_ret"], 2, 0.2 + 0.05 * i, 0.85, 80)
    tags(root, [
        [("in-rack CDU (4U)", ir["at"]), ("its own small HX + pumps", (24.0, 22.0, -55.0))],
        [("one rack: ~100-250 kW", (40.0, 214.0, -10.0)), ("SMCI: 250 kW in-rack", (40.0, 4.0, -4.0))],
        [("in-row CDU: a whole row", (-40.0, 200.0, -10.0)), ("Vertiv CoolChip: up to ~2 MW+", (-40.0, 150.0, -10.0)),
         ("one header, many racks", (150.0, 222.0, D.MAN_Z))],
    ])
    camera_path(root, [V_IR, V_RACK, V_ROW])


def sec8(m, root):
    s = D.scene(m, root, row_racks=True, in_rack=True)
    D.present(s["inrack"]["g"], beat(1))
    D.present(s["row"]["g"], beat(2))
    D.spin(s["pumps"]["A"]["imp"], 0, 3)
    tags(root, [
        [("Vertiv (VRT): CoolChip CDUs", (-40.0, 200.0, -10.0)), ("Schneider / Motivair", (-40.0, 150.0, -10.0)),
         ("nVent (NVT), Modine (MOD)", (-40.0, 100.0, -10.0))],
        [("Supermicro (SMCI): in-rack", s["inrack"]["at"]), ("CoolIT, Boyd: rack CDUs", (40.0, 214.0, -10.0))],
        [("Delta, Nidec, LiquidStack", (-40.0, 200.0, -10.0)), ("Danfoss, Alfa Laval: PHEs", (150.0, 222.0, D.MAN_Z))],
    ])
    camera_path(root, [V_CDU, V_IR, V_ROW])


def sec9(m, root):
    s = D.scene(m, root)
    D.trays(root, m, [0], 0.0, 0.8)
    run(root, "leak", [(30.0, D.TRAY_Y[2] + 5.0, -60.0), (30.0, 9.0, -60.0)], 4, 1.2, m["leak"], 0, 0.1, 0.8, 30)
    D.blink(s["ctrl"]["leds"][3], 0, range(8), 8, 0.5)
    D.spin(s["pumps"]["B"]["imp"], 1, 2)
    D.blink(s["pumps"]["B"]["led"], 1, range(8), 8, 0.5)
    run(root, "b", D.p_sec_pump("B"), 5, 2.0, m["b_ret"], 1, 0.2, 0.85, 80)
    show(s["rack"]["gpu_glow"], beat(2))
    D.gpu_heat(root, m, 2, ks=(0, 2, 4, 6))
    D.secondary(root, m, [2], n=4)
    tags(root, [
        [("leaks: water near servers", (30.0, 12.0, -60.0)), ("quick disconnects", s["man"]["qd"]), ("alarm", s["ctrl"]["at"])],
        [("pump fails: standby takes over", s["pumps"]["B"]["top"]), ("one CDU, many racks", (-40.0, 200.0, -10.0))],
        [("racks: ~130 kW now, ~600 kW+ next", (40.0, 214.0, -10.0)), ("more flow, bigger CDUs", (-40.0, 150.0, -10.0))],
    ])
    camera_path(root, [frame((10.0, 60.0, -40.0), 150.0, -0.20, 0.25), V_PUMPS, V_ALL])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    m.update(D.materials())
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
