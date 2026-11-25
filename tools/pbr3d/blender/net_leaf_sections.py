"""The LEAF page's nine numbered sections, in the picture-and-panel template (docs/diagram-pages.md).
Section N illustrates heading N of tui/src/screens/diagrams_pages/NET_LEAF.txt (the tenth, Sources,
is text only). Three beats each, one beat is 8 s.

    blender -b --factory-startup --python tools/pbr3d/blender/net_leaf_sections.py -- <n>

Writes assets/net_leaf_section_<n>.glb. The fabric comes from net_leaf_detail.scene; close-ups (the
switch four times larger, an OSFP module cut open, a DAC cable cut across, meter bars) are built
above it at height BY.

  1 what happens   servers to leaf on copper; the ASIC; uplinks to every spine
  2 the parts      the switch four times larger: cages, ASIC + heatsink, fans and PSUs
  3 downlinks      a DAC cut across (twinax pairs); an AOC plug's lasers; the reach of each
  4 uplinks        an 800G DR8 module cut open: DSP, eight lasers, eight fibres; on to the spines
  5 inside         packets in on SerDes, through the ASIC's buffer, out; heat and airflow
  6 ECMP           four equal paths; flows hashed per spine; leaf to spine to leaf
  7 oversubscribe  1:1 meters (32 down, 32 up); 3:1 (48 down, 16 up) and a queue; AI uses 1:1
  8 Eth vs IB      RoCE with PFC/ECN; InfiniBand credits; Ultra Ethernet packet spraying
  9 who + risks    makers tagged on switch, optics, cables; optics supply; power and heat
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show, tube  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_leaf_detail as D  # noqa: E402
from net_leaf_detail import frame, camera_path, run, rise, bx, empty, present  # noqa: E402
import net_leaf_overview as OV  # noqa: E402
import net_leaf_zooms as Z  # noqa: E402

PAGE = "net_leaf"
BEATS = 3
BY = 600.0
BIG = (0.0, BY, 0.0)
S = 4.0


def tags(root, per_beat):
    Z.tags(root, per_beat)


def big_switch(m, root):
    sw = D.switch(m, root, BIG, S, detail=True, name="big")
    return sw


def sec1(m, root):
    s = D.scene(m, root)
    OV.downlinks(m, root, s, [0], step=1)
    show(s["leaf"]["die_glow"], [(F(1, 0.0), F(3, 0.0))])
    for i in range(0, D.N_PORT, 4):
        run(root, f"t{i}", s["leaf"]["tr_down"][i][::-1], 2, 0.45, m["pkt"], 1, 0.02 * (i // 4), 0.7, 30)
    OV.uplinks(m, root, s, [2])
    OV.blink_leds(s["leaf"], range(3))
    tags(root, [
        [("servers' NICs to the leaf", s["srv_ports"][10]), ("one leaf per row", s["leaf"]["top"])],
        [("the switch ASIC forwards", s["leaf"]["parts"]["heatsink"])],
        [("uplinks to every spine", s["spines"][1]["top"]), ("800G over fibre", (200.0, D.TRAY_TOP + 6.0, -35.0))],
    ])
    camera_path(root, [frame((0.0, 150.0, 0.0), 300.0, 0.15, 0.2), frame((0.0, D.LEAF_Y + 4.0, -28.0), 70.0, 0.3, 0.8),
                       frame((240.0, 200.0, -200.0), 700.0, 0.45, 0.45, pad=0.9)])


def sec2(m, root):
    sw = big_switch(m, root)
    OV.blink_leds(sw, range(3))
    show(sw["die_glow"], [(F(1, 0.0), F(3, 0.0))])
    tags(root, [
        [("64 OSFP cages, 800G each", sw["down"][6]), ("downlinks: bottom row", sw["down"][20]), ("uplinks: top row", sw["up"][26])],
        [("switch ASIC under heatsink", sw["parts"]["heatsink"]), ("SerDes traces", sw["tr_down"][8][1])],
        [("fans, front-to-back air", sw["fans"][3]), ("2 PSUs", sw["parts"]["psu"]), ("control CPU", sw["parts"]["cpu"])],
    ])
    camera_path(root, [frame((0.0, BY + 24.0, -4.0), 230.0, 0.25, 0.25), frame((0.0, BY + 20.0, -112.0), 200.0, 0.2, 0.9),
                       frame((0.0, BY + 20.0, -170.0), 240.0, 0.7, 0.7)])


def sec3(m, root):
    s = D.scene(m, root)
    o = (0.0, BY, 0.0)
    # beat 0: a DAC cut across: jacket, shield, eight twinax pairs, copper cores
    dg = empty("dac_x", root)
    tube("dac_j", (0, BY, -40), (0, BY, 0), 12.0, m["dac"], dg, 32)
    tube("dac_sh", (0, BY, -40), (0, BY, 0.5), 10.5, m["cage"], dg, 32)
    for k in range(8):
        import math
        a = k * math.pi / 4
        cx, cy = 6.0 * math.cos(a), 6.0 * math.sin(a)
        for d in (-1, 1):
            px, py = cx + d * 1.4 * math.cos(a + 1.57), cy + d * 1.4 * math.sin(a + 1.57)
            tube(f"tw{k}{d}", (px, BY + py, -40), (px, BY + py, 1.0), 1.3, m["twinax"], dg, 12)
            tube(f"cu{k}{d}", (px, BY + py, -40), (px, BY + py, 1.4), 0.5, m["copper"], dg, 8)
            run(root, f"sig{k}{d}", [(px, BY + py, -40.0), (px, BY + py, 2.0)], 2, 0.45, m["pkt"], 0, 0.05 * k, 0.8, 40)
    present(dg, beat(0))
    # beat 1: an AOC plug: an OSFP with its lasers lit, fibre out
    og = empty("aoc_g", root)
    g, pts = D.osfp(m, og, (100.0, BY, 30.0), 6.0, name="aocp")
    for k, ln in enumerate(pts["lanes"]):
        run(root, f"al{k}", ln, 2, 0.35, m["laser"], 1, 0.03 * k, 0.8, 30)
    present(og, beat(1))
    # beat 2: the row, both cable kinds
    OV.downlinks(m, root, s, [2], step=1)
    del o
    tags(root, [
        [("8 twinax pairs, 100G each", (6.0, BY + 6.0, 1.0)), ("passive: no power, ~0 latency", (0.0, BY - 12.0, 0.0)),
         ("thick: ~2 m at 800G", (-12.0, BY, -20.0))],
        [("AOC: optics built into the plug", pts["las"]), ("lasers on each lane", pts["dsp"]), ("thin fibre, ~30 m+", pts["mpo"])],
        [("DAC: racks beside the leaf", (D.GPU_RACKS[1], D.CM_Y[0], 2.0)), ("AOC: outer racks", (D.GPU_RACKS[3], D.CM_Y[0], 2.0))],
    ])
    camera_path(root, [frame((0.0, BY, 0.0), 40.0, 0.5, 0.25), frame((100.0, BY + 3.0, 0.0), 80.0, 0.5, 0.5),
                       frame((0.0, 140.0, 0.0), 300.0, -0.1, 0.12)])


def sec4(m, root):
    s = D.scene(m, root)
    og = empty("ox_g", root)
    g, pts = D.osfp(m, og, (0.0, BY, 30.0), 10.0, name="dr8")
    present(og, [(F(0, 0.0), F(2, 0.0))])
    for b in (0, 1):
        run(root, f"e{b}", [pts["edge"], pts["dsp"]], 6, 0.5, m["pkt"], b, 0.0, 0.5, 40)
        run(root, f"d{b}", [pts["dsp"], pts["las"]], 6, 0.5, m["up"], b, 0.2, 0.7, 30)
    for k, ln in enumerate(pts["lanes"]):
        run(root, f"ln{k}", ln, 3, 0.4, m["laser"], 1, 0.3 + 0.02 * k, 0.9, 30)
    OV.uplinks(m, root, s, [2])
    tags(root, [
        [("electrical in: 8 x 100G", pts["edge"]), ("DSP retimes the signal", pts["dsp"]), ("finned shell sheds ~15 W", (0.0, BY + 19.0, -40.0))],
        [("8 lasers, one per lane", pts["las"]), ("MPO: 8 single-mode fibres", pts["mpo"]), ("DR8: 500 m reach", (0.0, BY + 6.0, -100.0))],
        [("32 uplinks up to the tray", (0.0, D.TRAY_TOP, 3.0)), ("then to every spine", s["spines"][0]["top"])],
    ])
    camera_path(root, [frame((0.0, BY + 6.0, 0.0), 70.0, 0.5, 0.45), frame((0.0, BY + 6.0, -60.0), 110.0, 0.6, 0.5),
                       frame((240.0, 200.0, -150.0), 650.0, 0.4, 0.45, pad=0.9)])


def sec5(m, root):
    sw = big_switch(m, root)
    for i in range(0, D.N_PORT, 2):
        run(root, f"in{i}", sw["tr_down"][i][::-1], 2, 1.2, m["pkt"], [0, 1], 0.01 * i, 0.8, 30)
    for i in range(1, D.N_PORT, 2):
        run(root, f"out{i}", sw["tr_up"][i], 2, 1.2, m["up"], 1, 0.2 + 0.01 * i, 0.9, 30)
    show(sw["die_glow"], [(F(0, 0.3), F(3, 0.0))])
    D.queue(m, root, (sw["asic"][0] + 34.0, BY + 6.0, sw["asic"][2]), 8, 1, 0.1, 0.6, 3.0, "buf")
    for k, fp in enumerate(sw["fans"]):
        run(root, f"air{k}", [(fp[0], fp[1], 4.0), (fp[0], fp[1], fp[2] - 60.0)], 3, 1.2, m["cool"], 2, 0.02 * k, 0.8, 40)
    rise(root, "heat", sw["top"], 8, 1.4, m["heat"], 2, 0.05, 0.85, 60.0, 60, (24.0, 24.0))
    OV.blink_leds(sw, range(3))
    tags(root, [
        [("packets in on SerDes lanes", sw["tr_down"][10][1]), ("the ASIC reads each header", sw["parts"]["heatsink"])],
        [("on-chip buffer: tens of MB", (sw["asic"][0] + 34.0, BY + 14.0, sw["asic"][2])), ("out to the right port", sw["up"][25])],
        [("~1-2 kW per switch box", sw["parts"]["psu"]), ("air front to back", sw["fans"][2])],
    ])
    camera_path(root, [frame((0.0, BY + 20.0, -60.0), 220.0, 0.2, 0.75), frame((20.0, BY + 20.0, -100.0), 200.0, -0.3, 0.8),
                       frame((0.0, BY + 30.0, -170.0), 260.0, 0.75, 0.55)])


def sec6(m, root):
    s = D.scene(m, root)
    OV.ecmp(m, root, s, [0], n=2)
    OV.ecmp(m, root, s, [1], n=4, name="b")
    for r in (1, 2, 3):
        for j in range(4):
            run(root, f"all{r}{j}", D.to_spine(s, r, j), 2, 0.8, m["up"], 2, 0.05 * j, 0.7, 90)
    OV.ecmp(m, root, s, [2], dst=1, n=3, name="c")
    for sp in s["spines"]:
        show(sp["leds"], [(F(0, 0.2), F(3, 0.0))])
    tags(root, [
        [("any leaf to any leaf: 3 hops", s["leaf"]["top"]), ("via one spine", s["spines"][0]["top"])],
        [("ECMP: hash of the flow's header", (D.SPINE_X - 30.0, D.TRAY_TOP + 10.0, -200.0)), ("4 equal paths", s["spines"][2]["top"])],
        [("add spines to add bandwidth", s["spines"][3]["top"]), ("every leaf meets every spine", (0.0, D.LEAF_Y + 14.0, D.ROW_Z[2]))],
    ])
    camera_path(root, [frame((250.0, 200.0, -300.0), 900.0, 0.4, 0.5, pad=0.85), frame((400.0, 200.0, -390.0), 700.0, 0.7, 0.45, pad=0.9),
                       frame((260.0, 150.0, -380.0), 1050.0, 0.3, 0.65, pad=0.85)])


def sec7(m, root):
    D.scene(m, root, rows=False)
    pg = empty("meters", root)
    D.scope_box(m, pg, (0.0, BY + 20.0, 0.0), 200.0, 80.0, "panel")
    g1, g2 = empty("m11", pg), empty("m31", pg)
    for k in range(32):
        D.bar(m, g1, -90.0 + 2.6 * k, BY - 10.0, 30.0, 0.2, 2.0, m["aoc"], f"d1_{k}")
        D.bar(m, g1, 10.0 + 2.6 * k, BY - 10.0, 30.0, 0.2, 2.0, m["smf"], f"u1_{k}")
    for k in range(48):
        D.bar(m, g2, -90.0 + 1.75 * k, BY - 10.0, 30.0, 0.2, 1.3, m["aoc"], f"d3_{k}")
    for k in range(16):
        D.bar(m, g2, 10.0 + 5.2 * k, BY - 10.0, 30.0, 0.2, 3.0, m["smf"], f"u3_{k}")
    present(g1, beat(0) + beat(2))
    present(g2, beat(1))
    for k in range(6):
        run(root, f"f1_{k}", [(-80.0 + 12 * k, BY + 30.0, 1.0), (20.0 + 12 * k, BY + 30.0, 1.0)], 3, 1.2, m["pkt"], [0, 2], 0.05 * k, 0.8, 50)
        run(root, f"f3_{k}", [(-80.0 + 12 * k, BY + 30.0, 1.0), (40.0, BY + 30.0, 1.0)], 3, 1.2, m["pkt"], 1, 0.03 * k, 0.5, 50)
    D.queue(m, root, (40.0, BY + 33.0, 2.0), 9, 1, 0.1, 0.8, 2.5, "q3", "fail")
    tags(root, [
        [("32 x 800G down", (-50.0, BY + 22.0, 0.5)), ("32 x 800G up", (50.0, BY + 22.0, 0.5)), ("1:1: non-blocking", (0.0, BY + 55.0, 0.5))],
        [("48 down", (-50.0, BY + 22.0, 0.5)), ("16 up: 3:1", (50.0, BY + 22.0, 0.5)), ("bursts queue and drop", (40.0, BY + 50.0, 2.0))],
        [("AI training: 1:1", (0.0, BY + 55.0, 0.5)), ("all-reduce hits every link at once", (0.0, BY - 14.0, 0.5))],
    ])
    camera_path(root, [frame((0.0, BY + 20.0, 0.0), 230.0, 0.0, 0.1)] * 3)


def sec8(m, root):
    s = D.scene(m, root)
    lf = s["leaf"]
    up = lf["up"][9]
    qat = (up[0], up[1] + 3.0, up[2] + 2.0)
    for i in range(0, D.N_PORT, 2):
        run(root, f"in{i}", D.to_leaf(s, i), 2, 0.6, m["pkt"], [0, 1], 0.0, 0.3, 60)
    D.queue(m, root, qat, 8, 0, 0.1, 0.6, 1.0, "q0")
    for i in (0, 12, 19, 31):
        run(root, f"pfc{i}", D.from_leaf(s, i), 2, 0.7, m["fail"], 0, 0.5, 0.8, 60)
    run(root, "ecn", D.to_spine(s, 0, 1, 9), 3, 0.8, m["ecn"], 0, 0.3, 0.8, 90)
    for i in (2, 10, 21, 29):
        run(root, f"cr{i}", D.from_leaf(s, i), 2, 0.6, m["credit"], 1, 0.2, 0.9, 60)
    for j in range(4):
        for p in range(3):
            run(root, f"spr{j}{p}", D.to_spine(s, 0, j, 8 * j + 2 * p) + D.from_spine(s, 3, j), 2, 0.9, m["spine"], 2, 0.02 * p + 0.04 * j, 0.6, 110)
    tags(root, [
        [("RoCE: RDMA over Ethernet", lf["down"][16]), ("PFC pauses the sender", s["srv_ports"][12]), ("ECN marks slow it", qat)],
        [("InfiniBand: credits", lf["down"][8]), ("send only when the buffer has room", s["srv_ports"][20]),
         ("NVIDIA Quantum, 800G", lf["top"])],
        [("Ultra Ethernet: spray packets", s["spines"][1]["top"]), ("over every path, reorder at the NIC", (0.0, D.LEAF_Y + 14.0, D.ROW_Z[3]))],
    ])
    camera_path(root, [frame((0.0, 160.0, 0.0), 280.0, -0.15, 0.12), frame((0.0, 160.0, 0.0), 260.0, 0.15, 0.12),
                       frame((260.0, 150.0, -380.0), 1050.0, 0.4, 0.6, pad=0.85)])


def sec9(m, root):
    s = D.scene(m, root)
    lf = s["leaf"]
    OV.blink_leds(lf, range(3))
    show(lf["die_glow"], beat(2))
    rise(root, "heat", lf["top"], 6, 0.6, m["heat"], 2, 0.05, 0.85, 26.0, 60, (8.0, 8.0))
    tags(root, [
        [("switch: ANET, CSCO, NVDA, CLS", lf["top"]), ("ASIC: AVGO, NVDA, MRVL", lf["parts"]["heatsink"]),
         ("copper: APH, CRDO (AEC)", (D.GPU_RACKS[1], D.CM_Y[0], 2.0))],
        [("optics: COHR, LITE, FN", lf["up"][20]), ("InnoLight, Eoptolink", (0.0, D.TRAY_TOP - 10.0, 3.0)),
         ("fibre: GLW", (200.0, D.TRAY_TOP + 6.0, -35.0))],
        [("800G optics in short supply", lf["up"][6]), ("~1-2 kW a switch, mostly optics", lf["top"]),
         ("copper reach shrinks each speed", (D.GPU_RACKS[1], 120.0, 3.0))],
    ])
    camera_path(root, [frame((0.0, 170.0, 0.0), 240.0, 0.15, 0.2), frame((60.0, 210.0, -30.0), 300.0, 0.4, 0.35),
                       frame((0.0, D.LEAF_Y + 6.0, 0.0), 120.0, 0.3, 0.3)])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    m.update(D.materials())
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
