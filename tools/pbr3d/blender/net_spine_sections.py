"""The SPINE page's nine numbered sections, in the picture-and-panel template (docs/diagram-pages.md).
Section N illustrates heading N of tui/src/screens/diagrams_pages/NET_SPINE.txt (the tenth, Sources,
is text only). Three beats each, one beat is 8 s.

Run one section per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/net_spine_sections.py -- <n>

Writes blender/net_spine_section_<n>.blend and assets/net_spine_section_<n>.glb. The switch and fabric
come from net_spine_detail.py; close-ups (the ASIC package, an OSFP module, a PAM4 eye) are built at BY.

  1 what happens   a packet leaves a leaf, crosses the spine's ASIC, lands on another leaf
  2 the parts      lid off: ports and optics, ASIC and heatsink, fans and PSUs
  3 in order       inside the ASIC: SerDes, ingress pipe, shared buffer, egress pipe, SerDes
  4 51.2 Tb/s      512 lanes x 100G; 8 lanes per port; 64 x 800G across the front
  5 SerDes, PAM4   a lane's trace; the PAM4 eye's four levels; 2 bits a symbol
  6 the optic      OSFP shell opens: DSP, drivers, lasers, fibres to the MPO
  7 ECMP           every leaf to every spine; flows hashed; a spine drops out
  8 who makes it   chip, box and optics makers tagged on the parts
  9 chokepoints    power and heat; optics' share; 102.4T and co-packaged optics next
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_spine_detail as D  # noqa: E402
from net_spine_detail import frame, camera_path, run, rise, empty, BY  # noqa: E402
import net_spine_overview as OV  # noqa: E402

PAGE = "net_spine"
BEATS = 3


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def switch(m, root, lid_beats=(), fab=True):
    s = D.scene(m, root, BEATS, fab=fab)
    D.present(s["lid"], [iv for b in lid_beats for iv in beat(b)])
    D.leds_on(s, range(BEATS))
    return s


V_FAB = frame((-450.0, -150.0, 50.0), 3300.0, 0.0, 0.30, pad=1.0)
V_OPEN = frame((0.0, 30.0, -260.0), 620.0, 0.35, 0.75, pad=1.0)
V_FRONT = frame((0.0, 44.0, 0.0), 450.0, 0.0, 0.12, pad=1.0)
V_TRACES = frame((0.0, 10.0, -150.0), 440.0, 0.0, 1.0, pad=1.0)
V_AC = frame((0.0, BY + 20.0, 0.0), 300.0, 0.25, 0.75, pad=1.0)
V_OC = frame((0.0, BY + 20.0, 0.0), 470.0, 0.55, 0.65, pad=1.0)
V_EYE = frame((0.0, BY + 55.0, 0.0), 330.0, 0.0, 0.02, pad=1.0)


def sec1(m, root):
    switch(m, root, lid_beats=(0,))
    run(root, "s1_a", D.flow(1, D.DETAIL, 6), 4, 7.0, m["pkt"], 0, 0.0, 0.6, 160)
    for k in range(3):
        run(root, f"s1_b{k}", D.flow(1, D.DETAIL, 6), 2, 2.4, m["pkt"], 1, 0.05 + 0.1 * k, 0.6, 160)
    OV.ecmp(m, root, [2], 1, 6, n=3)
    tags(root, [
        [("leaf 2 sends a packet", D.leaf_port(1, 2)), ("up to a spine", (0.0, D.CH, -200.0)), ("down to leaf 7", D.leaf_port(6, 2))],
        [("in an 800G port", D.port(2, 3)), ("across the ASIC", (0.0, 18.0, D.ASIC[1])), ("out the port to leaf 7", D.port(12, 3))],
        [("every spine is one hop", (D.SPINES[1], D.CH, -100.0)), ("4 equal paths", (D.SPINES[3], D.CH, -100.0))],
    ])
    camera_path(root, [V_FAB, frame((0.0, 20.0, -140.0), 520.0, 0.10, 0.85, pad=1.0), V_FAB])


def sec2(m, root):
    s = switch(m, root, lid_beats=())
    D.airflow(root, m, [2], n=8)
    tags(root, [
        [("64 OSFP cages", D.port(2, 3)), ("800G optics plugged in", D.port(13, 2)), ("2RU box", (D.CX1, D.CH, -40.0))],
        [("switch ASIC + heatsink", s["asic"]["top"]), ("copper traces", (D.COLS[3], D.TY, -120.0)), ("CPU board: runs the NOS", s["fans"]["cpu"])],
        [("fan wall", (D.FANS[1], D.FAN_Y + 31, D.FAN_Z[1])), ("2 PSUs", s["fans"]["psu"]), ("air front to back", (-150.0, 44.0, 40.0))],
    ])
    camera_path(root, [V_FRONT, V_OPEN, frame((0.0, 40.0, -420.0), 480.0, 0.40, 0.70, pad=1.0)])


def sec3(m, root):
    g = empty("s3", root)
    ac = D.asic_close(m, g)
    for i, z in enumerate((-48.0, -16.0, 16.0, 48.0)):
        run(root, f"s3_a{i}", D.asic_path(ac, z, -z)[:3], 3, 2.6, m["pkt"], 0, 0.05 * i, 0.85, 50)
        run(root, f"s3_b{i}", D.asic_path(ac, z, -z)[2:6], 3, 2.6, m["pkt"], 1, 0.05 * i, 0.85, 60)
        run(root, f"s3_c{i}", D.asic_path(ac, z, -z)[4:], 3, 2.6, m["pkt2"], 2, 0.05 * i, 0.85, 60)
    show(ac["lit"], beat(1))
    tags(root, [
        [("SerDes ring: bits in", ac["serdes"]), ("ingress pipes: read headers", ac["in"]), ("BGA to the board", ac["balls"])],
        [("shared packet buffer", ac["buf"]), ("queues wait here", (0.0, ac["top"] + 7, 54.0))],
        [("egress pipes: rewrite, schedule", ac["out"]), ("SerDes: bits out", (ac["D"] - 9, ac["top"] + 2.5, 30.0))],
    ])
    camera_path(root, [V_AC, frame((0.0, BY + 20.0, 0.0), 190.0, 0.2, 0.9), V_AC])


def sec4(m, root):
    s = switch(m, root, lid_beats=(2,))
    D.present(s["asic"]["hs"], [])
    show(s["asic"]["glow"], beat(0))
    OV.serdes(m, root, [0], n=2)
    OV.serdes(m, root, [1], cols=range(16), n=2)
    for c in range(0, 16, 3):
        run(root, f"s4_l{c}", [(D.COLS[c], D.ROWS[3] + 7, 160.0), D.port(c, 3)], 3, 1.8, m["light"], 2, 0.0, 0.7, 40)
    tags(root, [
        [("512 SerDes lanes", s["asic"]["die"]), ("100G each", (D.COLS[4], D.TY, -110.0))],
        [("8 lanes = one 800G port", D.port(6, 1)), ("512 / 8 = 64 ports", D.port(13, 3))],
        [("64 x 800G = 51.2 Tb/s", D.port(4, 3)), ("or 128 x 400G", D.port(12, 1))],
    ])
    camera_path(root, [V_TRACES, frame((0.0, 30.0, -80.0), 300.0, 0.25, 0.55, pad=1.0), V_FRONT])


def sec5(m, root):
    g = empty("s5", root)
    eg = empty("s5_eye", g)
    D.eye(m, eg)
    seq = [0, 3, 1, 2, 3, 0, 2, 1, 0, 3]
    pts = []
    for i, lv in enumerate(seq):
        x = -130 + 26 * i
        pts += [(x, BY + D.LEVELS[lv], 1.0), (x + 18, BY + D.LEVELS[lv], 1.0)]
    run(root, "s5_sym", pts, 4, 4.0, m["pkt2"], [0, 1, 2], 0.0, 0.8, 110)
    for i, lv in enumerate(D.LEVELS):
        label(["00", "01", "10", "11"][i], (150.0, BY + lv, 0.0), root, beat(1))
    tags(root, [
        [("PAM4: 4 voltage levels", (-150.0, BY + 100, 0.0)), ("one symbol at a time", (0.0, BY + 55, 0.0))],
        [],
        [("~53 GBd x 2 bits = 106G", (-150.0, BY + 10, 0.0)), ("the eye: decide here", (0.0, BY + 25, 0.0))],
    ])
    camera_path(root, [V_EYE, frame((60.0, BY + 55.0, 0.0), 260.0, 0.0, 0.02, pad=1.0), V_EYE])


def sec6(m, root):
    g = empty("s6", root)
    oc = D.optic_close(m, g)
    D.present(oc["top"], beat(0))
    for i in range(8):
        el, li = D.optic_lanes(oc, i)
        run(root, f"s6_e{i}", el, 2, 2.4, m["pkt"], [1, 2], 0.05 * i / 2, 0.6, 60)
        run(root, f"s6_l{i}", li, 2, 2.6, m["light"], [2], 0.2 + 0.03 * i, 0.9, 50)
    tags(root, [
        [("OSFP: 8 lanes, 800G", oc["fins"]), ("built-in fins", (40.0, BY + 72, 60.0))],
        [("edge fingers: 8 x 100G in", oc["fingers"]), ("DSP retimes the lanes", oc["dsp"]), ("drivers", oc["drv"])],
        [("8 lasers", oc["las"]), ("fibre to the MPO", oc["mpo"]), ("~15 W a module", (-45.0, BY + 52, -150.0))],
    ])
    camera_path(root, [V_OC, frame((0.0, BY + 20.0, -100.0), 280.0, 0.45, 0.7), frame((0.0, BY + 20.0, 80.0), 300.0, 0.5, 0.65)])


def sec7(m, root):
    s = switch(m, root, lid_beats=(0, 1, 2))
    show(s["fabric"]["leds"], span(0, 0.0, 3, 0.0))
    OV.ecmp(m, root, [0], 0, 7, n=2)
    OV.ecmp(m, root, [1], 2, 5, n=4)
    OV.ecmp(m, root, [2], 2, 5, n=4, spines=(0, 2, 3))
    dead = empty("s7_dead", root)
    D.bx("s7_x", (D.SPINES[1] - 225, -3.0, -5.0), (D.SPINES[1] + 225, D.CH + 3, 6.0), m["fail"], dead)
    D.present(dead, span(2, 0.0, 3, 0.0))
    tags(root, [
        [("each leaf wired to all 4 spines", D.leaf_port(0, 1)), ("2-tier Clos", (D.SPINES[3], D.CH, -100.0))],
        [("hash of the flow's headers", D.leaf_port(2, 2)), ("picks 1 of 4 equal paths", (D.SPINES[2], D.CH, -100.0))],
        [("spine 2 fails", (D.SPINES[1], D.CH, 0.0)), ("flows rehash onto 3: 75% left", (D.SPINES[3], D.CH, -100.0))],
    ])
    camera_path(root, [V_FAB, frame((-450.0, -150.0, 50.0), 3200.0, -0.1, 0.2, pad=1.0), V_FAB])


def sec8(m, root):
    s = switch(m, root, lid_beats=(2,))
    D.present(s["asic"]["hs"], beat(2))
    OV.ecmp(m, root, [2], 1, 6, n=2)
    tags(root, [
        [("ASIC: Broadcom (AVGO) Tomahawk", s["asic"]["die"]), ("Marvell Teralynx, Cisco Silicon One", (D.SUBH, 8.0, D.ASIC[1] + D.SUBH)),
         ("NVIDIA Spectrum-X", (-D.SUBH, 8.0, D.ASIC[1] - D.SUBH))],
        [("optics: Coherent, Lumentum", D.port(3, 3)), ("Fabrinet builds; AAOI, InnoLight", D.port(12, 2)), ("Credo: AECs, DSPs", D.port(8, 0))],
        [("box: Arista (ANET), Cisco (CSCO)", (D.SPINES[2], D.CH, -280.0)), ("white box: Celestica (CLS)", (D.SPINES[0], D.CH, -280.0))],
    ])
    camera_path(root, [frame((0.0, 12.0, -250.0), 160.0, 0.25, 0.70), V_FRONT, V_FAB])


def sec9(m, root):
    s = switch(m, root, lid_beats=())
    show(s["asic"]["glow"], beat(0))
    D.present(s["asic"]["hs"], span(1, 0.0, 3, 0.0))
    D.airflow(root, m, [0, 1], n=10)
    rise(root, "s9_h", (0.0, D.HS_Y[1], D.ASIC[1]), 8, 2.0, m["heat"], [1], 0.05, 0.85, 50.0, 70, (40.0, 40.0))
    for c in range(0, 16, 2):
        rise(root, f"s9_o{c}", (D.COLS[c], D.CH, -20.0), 1, 1.6, m["heat"], [1], 0.05 + 0.04 * c, 0.85, 40.0, 60)
    g = empty("s9_ac", root)
    ac = D.asic_close(m, g)
    D.present(g, beat(2))
    oc_tag = (ac["D"] + 30, ac["top"], 0.0)
    tags(root, [
        [("ASIC alone: ~500 W class", s["asic"]["die"]), ("air cooling near its limit", (D.FANS[1], D.FAN_Y + 31, D.FAN_Z[1]))],
        [("64 optics x ~15 W: ~1 kW", D.port(8, 3)), ("LPO drops the DSP: ~half", D.port(13, 1))],
        [("next: 102.4T (Tomahawk 6)", ac["buf"]), ("co-packaged optics: lasers by the die", oc_tag)],
    ])
    camera_path(root, [frame((0.0, 40.0, -280.0), 600.0, 0.45, 0.85, pad=1.0), V_FRONT, V_AC])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    m.update(D.materials())
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))
