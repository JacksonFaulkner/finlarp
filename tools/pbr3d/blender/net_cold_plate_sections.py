"""The COLD PLATE page's nine numbered sections, in the picture-and-panel template
(docs/diagram-pages.md). Section N illustrates heading N of
tui/src/screens/diagrams_pages/NET_COLD_PLATE.txt (the tenth, Sources, is text only). Three beats
each, one beat is 8 s.

Run one section per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/net_cold_plate_sections.py -- <n>

Writes blender/net_cold_plate_section_<n>.blend and assets/net_cold_plate_section_<n>.glb. The tray,
plate, hoses, QDs and manifolds come from net_cold_plate_detail.py; close-ups (a fin slice 5x, the
TIM gap 20x, one quick disconnect cut open 4x) are built above the tray at D.BY.

  1 what happens   cool in; heat into the fins; warm out
  2 the parts      package and TIM; base, fins, cover; hoses, QDs, manifolds
  3 in order       manifold > QD > hose; plate; hose > QD > return
  4 why liquid     a 1,000+ W GPU; water holds ~3,500x the heat of air per litre; 120+ kW racks
  5 microchannels  the fin slice: fins, channels, coolant warming as it passes
  6 TIM            rough surfaces with air gaps; TIM fills them; heat crosses
  7 QDs            one QD mated and flowing; parted, poppets shut; blind-mate on the manifold
  8 who makes it   makers tagged on the plate, QDs, manifold and CDU
  9 chokepoints    a leak at a QD; warm water reuse; supply of plates and QDs
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_cold_plate_detail as D  # noqa: E402
from net_cold_plate_detail import frame, camera_path, run, rise  # noqa: E402

PAGE = "net_cold_plate"
BEATS = 3
BY = D.BY


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def sec1(m, root):
    s = D.scene(m, root)
    D.flow_in(m, root, [0])
    show(s["chan_cool"], beat(0))
    D.flow_plate(m, root, [0, 1, 2], 0.1)
    show(s["die_glow"], span(1, 0.0, 3, 0.0))
    D.heat_up(m, root, [1])
    show(s["chan_warm"], span(1, 0.3, 3, 0.0))
    D.flow_out(m, root, [2])
    pp = s["plate"]
    tags(root, [
        [("cool water in", (D.IN_X, D.QY + 6.0, -110.0)), ("onto the plate", pp["inlet"])],
        [("GPU heat", s["pkg"]["die_face"]), ("into the fins", pp["fins"])],
        [("warm out: ~45-60 C", (D.OUT_X, D.QY + 6.0, -110.0)), ("to the rack manifold", (D.OUT_X, 120.0, D.MAN_Z))],
    ])
    camera_path(root, [frame((-10.0, 50.0, -120.0), 280.0, 0.70, 0.35, pad=1.0), frame((0.0, 20.0, 0.0), 120.0, 0.15, 0.15),
                       frame((10.0, 50.0, -140.0), 300.0, -0.75, 0.35, pad=1.0)])


def sec2(m, root):
    s = D.scene(m, root)
    D.flow_plate(m, root, [1], 0.1)
    show(s["chan_cool"], beat(1))
    pp, pk = s["plate"], s["pkg"]
    tags(root, [
        [("GPU dies + HBM", pk["die_face"]), ("TIM", pp["tim"]), ("substrate", pk["sub"])],
        [("copper base", pp["base"]), ("microchannel fins", pp["fins"]), ("cover + inlet", pp["slot"])],
        [("hoses", (D.IN_X, D.QY + 6.0, -110.0)), ("quick disconnects", s["qd"]), ("manifolds", s["man"])],
    ])
    camera_path(root, [frame((0.0, 8.0, 0.0), 90.0, 0.10, 0.10, min_d=44.0), frame((0.0, 26.0, -10.0), 130.0, 0.35, 0.30),
                       frame((0.0, 50.0, -150.0), 320.0, 0.80, 0.35, pad=1.0)])


def sec3(m, root):
    s = D.scene(m, root)
    D.flow_in(m, root, [0], n=8)
    D.flow_plate(m, root, [1], 0.0, n=4)
    show(s["chan_cool"], span(1, 0.0, 1, 0.5))
    show(s["chan_warm"], span(1, 0.5, 2, 0.0))
    D.flow_out(m, root, [2], n=8)
    pp = s["plate"]
    tags(root, [
        [("1 supply manifold", (D.IN_X, 30.0, D.MAN_Z)), ("2 quick disconnect", s["qd"]), ("3 hose", (D.IN_X, D.QY + 6.0, -110.0))],
        [("4 inlet over the dies", pp["slot"]), ("5 microchannels", pp["fins"]), ("6 outlet plenum", pp["plenum"])],
        [("7 hose out", (D.OUT_X, D.QY + 6.0, -110.0)), ("8 QD", s["qd"]), ("9 return manifold", (D.OUT_X, 150.0, D.MAN_Z))],
    ])
    camera_path(root, [frame((0.0, D.QY, -200.0), 200.0, 0.95, 0.30), frame((0.0, 28.0, -30.0), 140.0, 0.40, 0.40),
                       frame((10.0, 60.0, -180.0), 260.0, -0.95, 0.30, pad=1.0)])


def sec4(m, root):
    s = D.scene(m, root)
    show(s["die_glow"], span(0, 0.1, 3, 0.0))
    D.heat_up(m, root, [0], n=12, name="h0")
    rise(root, "h_air", (0.0, D.COV_Y[1] + 4.0, -30.0), 10, 1.4, m["heat"], 0, 0.05, 0.85, 50.0, 60, (40.0, 20.0))
    D.flow_plate(m, root, [1, 2], 0.0)
    show(s["chan_warm"], span(1, 0.0, 3, 0.0))
    D.present(s["others"], beat(2))
    D.rack_flows(m, root, [2])
    tags(root, [
        [("one GPU: ~1,000-1,400 W", s["pkg"]["die_face"]), ("too much for fins + fans", (0.0, D.COV_Y[1] + 30.0, -30.0))],
        [("water: ~3,500x air's heat per litre", s["plate"]["fins"]), ("a litre a minute per kW or so", s["plate"]["inlet"])],
        [("NVL72 rack: ~120-130 kW", (0.0, D.TRAY_DY + 40.0, 0.0)), ("air tops out near 40-50 kW", s["cdu"])],
    ])
    camera_path(root, [frame((0.0, 30.0, -20.0), 150.0, 0.30, 0.25), frame((0.0, 24.0, 0.0), 110.0, 0.15, 0.15),
                       frame((0.0, 40.0, -120.0), 520.0, 0.65, 0.25, pad=1.0)])


def sec5(m, root):
    g, chans, pt = D.fin_bench(m, root)
    y = pt["y0"] + 22.0
    for i, x in enumerate(chans):
        run(root, f"c0{i}", [(x, y, -60.0), (x, y, 1.0)], 3, 2.2, m["cool"], 0, 0.0 + 0.02 * i, 0.85, 60)
        run(root, f"c{i}", [(x, y, -60.0), (x, y, -30.0)], 3, 2.2, m["cool"], [1, 2], 0.0 + 0.02 * i, 0.8, 40)
        run(root, f"w{i}", [(x, y, -30.0), (x, y, 1.0)], 3, 2.2, m["warm"], [1, 2], 0.1 + 0.02 * i, 0.85, 40)
    for i, x in enumerate((-27.0, -9.0, 9.0, 27.0)):
        rise(root, f"hf{i}", (x, BY - 4.0, 1.0), 3, 1.6, m["heat"], [1, 2], 0.05 + 0.04 * i, 0.8, 60.0, 50, (4.0, 0.0))
    # beat 2: a jet in from the top over the middle, splitting both ways
    for i, x in enumerate(chans[4:8]):
        run(root, f"j{i}", [(x, pt["y0"] + 70.0, -20.0), (x, pt["y0"] + 52.0, -20.0), (x, pt["y0"] + 10.0, -20.0)], 3, 2.0, m["cool"], 2, 0.0, 0.7, 30)
    from net_cold_plate_detail import bx, empty
    jet = empty("jet_pipe", root)
    bx("jet_pipe_b", (-24.0, pt["y0"] + 52.0, -30.0), (24.0, pt["y0"] + 80.0, -10.0), m["nickel"], jet)
    D.present(jet, beat(2))
    tags(root, [
        [("copper fins", pt["fin"]), ("channels between", pt["chan"]), ("base", pt["base"])],
        [("heat climbs the fins", (-27.0, pt["y0"] + 10.0, 0.0)), ("water warms as it passes", (30.0, y, 0.0))],
        [("jet onto the hot spot", (0.0, pt["y0"] + 80.0, -20.0)), ("fins ~0.1 mm, skived from the block", pt["fin"])],
    ])
    camera_path(root, [frame((0.0, BY + 30.0, -10.0), 140.0, 0.30, 0.30), frame((0.0, BY + 25.0, 0.0), 120.0, 0.10, 0.10),
                       frame((0.0, BY + 40.0, -25.0), 150.0, 0.45, 0.45)])


def sec6(m, root):
    g, air, tim = D.tim_bench(m, root)
    show(air, span(0, 0.0, 1, 0.5))
    D.present(tim, span(1, 0.5, 3, 0.0))
    from net_cold_plate_detail import bx, empty
    glow = empty("tb_glow", root)
    bx("tb_glow_b", (-68.0, BY - 8.0, -38.0), (68.0, BY - 2.0, 0.3), m["die_hot"], glow)
    show(glow, span(0, 0.2, 3, 0.0))
    for i in range(5):
        x = -55.0 + 27.0 * i
        rise(root, f"hb{i}", (x, BY - 4.0, 1.0), 2, 1.4, m["heat"], 0, 0.05 + 0.05 * i, 0.8, 9.0, 60, (2.0, 0.0))
        rise(root, f"hc{i}", (x, BY - 4.0, 1.0), 3, 1.4, m["heat"], 2, 0.05 + 0.04 * i, 0.8, 40.0, 50, (2.0, 0.0))
    tags(root, [
        [("die top: rough at the micron scale", (-50.0, BY, 0.0)), ("air in the gaps: an insulator", (0.0, BY + 6.0, 0.0))],
        [("TIM fills every gap", (20.0, BY + 6.0, 0.0)), ("paste, liquid metal or indium", (-40.0, BY + 12.0, 0.0))],
        [("heat crosses into the copper", (0.0, BY + 30.0, 0.0)), ("thinner layer, lower resistance", (40.0, BY + 6.0, 0.0))],
    ])
    camera_path(root, [frame((0.0, BY + 5.0, 0.0), 120.0, 0.10, 0.10), frame((0.0, BY + 6.0, 0.0), 110.0, 0.15, 0.12),
                       frame((0.0, BY + 6.0, -10.0), 140.0, 0.30, 0.25)])


def sec7(m, root):
    q = D.qd_bench(m, root)
    # beat 0: mated, poppets pushed back, water flows through; beat 1: halves part, poppets shut
    key(q["a"], 0, "location", P(0.0, 0.0, 0.0), linear=True)
    key(q["a"], F(1, 0.1), "location", P(0.0, 0.0, 0.0), linear=True)
    key(q["a"], F(1, 0.5), "location", P(-40.0, 0.0, 0.0), linear=True)
    key(q["a"], F(2, 0.1), "location", P(-40.0, 0.0, 0.0), linear=True)
    key(q["a"], F(2, 0.5), "location", P(0.0, 0.0, 0.0), linear=True)
    for grp, sx in ((q["pa"], -1), (q["pb"], 1)):
        key(grp, 0, "location", P(sx * 10.0, 0.0, 0.0), linear=True)
        key(grp, F(1, 0.1), "location", P(sx * 10.0, 0.0, 0.0), linear=True)
        key(grp, F(1, 0.3), "location", P(-sx * 1.0, 0.0, 0.0), linear=True)
        key(grp, F(2, 0.3), "location", P(-sx * 1.0, 0.0, 0.0), linear=True)
        key(grp, F(2, 0.5), "location", P(sx * 10.0, 0.0, 0.0), linear=True)
    for i, yy in enumerate((BY - 16.0, BY + 16.0)):
        run(root, f"q{i}", [(-90.0, yy, 1.0), (90.0, yy, 1.0)], 6, 2.2, m["cool"], 0, 0.0 + 0.05 * i, 0.85, 70)
        run(root, f"q2{i}", [(-90.0, yy, 1.0), (90.0, yy, 1.0)], 4, 2.2, m["cool"], 2, 0.55 + 0.05 * i, 0.9, 50)
    tags(root, [
        [("tray half", (-60.0, BY + 28.0, 0.0)), ("rack half", (60.0, BY + 28.0, 0.0)), ("poppets pushed open", q["pop"])],
        [("halves part", (-30.0, BY + 28.0, 0.0)), ("springs shut both valves", q["spring"]), ("flat faces: no drip", (0.0, BY, 0.0))],
        [("blind-mate: push to connect", (-40.0, BY + 28.0, 0.0)), ("O-ring seals", q["oring"])],
    ])
    camera_path(root, [frame((0.0, BY, -5.0), 190.0, 0.15, 0.15), frame((-20.0, BY, -5.0), 230.0, 0.20, 0.20),
                       frame((0.0, BY, -5.0), 190.0, 0.30, 0.25)])


def sec8(m, root):
    s = D.scene(m, root)
    D.present(s["others"], beat(2))
    D.flow_plate(m, root, [0], 0.05)
    show(s["chan_cool"], beat(0))
    D.flow_in(m, root, [1])
    D.rack_flows(m, root, [2])
    pp = s["plate"]
    tags(root, [
        [("plates: CoolIT, Boyd, AVC, Auras", pp["cover"]), ("Cooler Master, Delta", pp["fins"]), ("JetCool (Flex)", pp["slot"])],
        [("QDs: Staubli, CPC, Parker", s["qd"]), ("hoses + fittings", (D.IN_X, D.QY + 6.0, -110.0))],
        [("manifolds + CDUs: Vertiv, nVent", s["man"]), ("Supermicro, Schneider, Delta", s["cdu"])],
    ])
    camera_path(root, [frame((0.0, 26.0, -20.0), 150.0, 0.35, 0.35), frame((0.0, D.QY, -180.0), 200.0, 0.95, 0.30),
                       frame((0.0, 40.0, -150.0), 520.0, 0.75, 0.22, pad=1.0)])


def sec9(m, root):
    s = D.scene(m, root)
    from net_cold_plate_detail import bx, empty
    D.flow_in(m, root, [0])
    # beat 0: a weeping QD: drips fall to the tray floor, alarm blinks
    drip = []
    for k in range(4):
        e = empty(f"drip{k}", root)
        D.bead(f"drip{k}_s", (D.IN_X, D.QY - 6.0, D.QD_Z[1]), 1.6, m["drop"], e)
        drip.append(e)
    for k, e in enumerate(drip):
        f0 = F(0, 0.15 + 0.17 * k)
        D.fly(e, [(0, 0, 0), (0, -(D.QY + 4.0), 0)], f0, f0 + 30, steps=4)
        show(e, [(f0, f0 + 30)])
    al = empty("alarm", root)
    bx("alarm_b", (D.IN_X - 10.0, D.QY + 12.0, D.QD_Z[1] - 3.0), (D.IN_X + 10.0, D.QY + 15.0, D.QD_Z[1] + 3.0), m["fail"], al)
    D.blink(al, 0, range(8), 8, 0.5)
    # beat 1: warm water out, reused
    D.flow_out(m, root, [1], n=8)
    D.present(s["others"], beat(2))
    D.rack_flows(m, root, [2])
    tags(root, [
        [("a weeping QD", (D.IN_X, D.QY + 15.0, D.QD_Z[1])), ("leak sensors cut the flow", (D.IN_X, -6.0, D.QD_Z[1]))],
        [("45-60 C water: no chiller needed", (D.OUT_X, 120.0, D.MAN_Z)), ("heat for reuse", (D.OUT_X, 200.0, D.MAN_Z))],
        [("every new GPU: more watts", (0.0, D.TRAY_DY + 40.0, 0.0)), ("QDs + plates in short supply", s["qd"])],
    ])
    camera_path(root, [frame((0.0, D.QY - 20.0, D.QD_Z[1]), 130.0, 0.80, 0.25), frame((15.0, 60.0, -180.0), 300.0, -0.90, 0.30, pad=1.0),
                       frame((0.0, 40.0, -120.0), 520.0, 0.65, 0.25, pad=1.0)])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    m.update(D.materials())
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
