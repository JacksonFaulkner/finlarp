"""TRM_DCI: the Terms-tab overview for data center interconnect, at the POWER pages' detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_dci.py

Writes assets/term_TRM_DCI.glb and specs/terms/TRM_DCI.json.

Two data-center buildings (roofs cut away, rows of GPU racks, a router in each) joined by a
buried fibre duct with an amplifier hut halfway. Colored beads on the one fibre are DWDM
wavelengths; a ZR coherent pluggable is pulled out of the router and cut open.

Beats:
  0 sites    two data centers, kilometres apart, one fibre duct between them
  1 DWDM     many colors (wavelengths) share one fibre pair, each its own channel
  2 ZR       a coherent ZR pluggable in the router puts a wavelength straight on the fibre
  3 amps     signals fade with distance; an amplifier hut boosts all colors at once
  4 AI       training spread over sites keeps the link full both ways
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import net_leaf_detail as NL  # noqa: E402
from sand_overview import F, show, empty, mat  # noqa: E402
from power_vrm_detail import bx, wire, run, blink, present, frame, join  # noqa: E402

SLUG = "TRM_DCI"
BEATS = [
    ("Data center interconnect links separate data centers with fibre",
     "DCI is the network between data centers: from buildings on one campus to sites hundreds of kilometres apart. "
     "It runs over fibre that cloud providers lease or own, buried in ducts along roads and rail lines. Each site's "
     "routers hand traffic to the DCI link, which carries far more capacity per fibre than anything inside the building."),
    ("DWDM: dozens of colors share one fibre",
     "Dense wavelength-division multiplexing puts many lasers of slightly different colors on one fibre, each an "
     "independent channel. Sixty-four channels of 800G on one fibre pair is over 50 Tb/s. Fibre is expensive to lay, "
     "so filling each strand with more colors is how DCI capacity grows."),
    ("A coherent ZR optic turns a router port into a DWDM channel",
     "Coherent optics encode data in the phase and amplitude of the light and use a DSP to undo distortion, which reaches "
     "far further than the simple optics inside a building. ZR pluggables (400ZR, 800ZR) put this into the same port size "
     "as a normal optic, so a router can drive the long link directly instead of through a separate optical shelf."),
    ("Every ~80 km an amplifier boosts all the colors at once",
     "Light fades as it travels through glass. An optical amplifier (an erbium-doped fibre amplifier) boosts every "
     "wavelength together without converting it to electricity, so long routes are chains of amplifier huts. Dedicated "
     "line systems handle these spans; ZR pluggables suit shorter, simpler links."),
    ("AI spreads training over sites, so DCI keeps growing",
     "A single site often lacks the power for the largest clusters, so training and inference fleets are split across "
     "several data centers joined by very high-capacity DCI. Cloud providers are the biggest buyers. Sales show up in "
     "the optical segments of networking firms. Related: Ciena (CIEN), Cisco (CSCO), Arista (ANET), Nokia (NOK), Marvell (MRVL)."),
]

BXS = (-320.0, 320.0)
DY = 0.0  # cable lies in a shallow open trench
COLORS = [(1.0, 0.25, 0.2), (1.0, 0.7, 0.15), (0.4, 1.0, 0.35), (0.25, 0.75, 1.0), (0.7, 0.4, 1.0)]


def building(m, root, xc, name):
    """Floor, three walls, no roof; rows of racks with LEDs; a router by the wall facing the link."""
    g = empty(name, root)
    s = 1 if xc < 0 else -1
    bx(f"{name}_fl", (xc - 110.0, 0.0, -80.0), (xc + 110.0, 2.0, 80.0), m["floor"], g)
    bx(f"{name}_wb", (xc - 110.0, 0.0, -80.0), (xc + 110.0, 70.0, -76.0), m["rackside"], g)
    bx(f"{name}_wo", (xc - s * 110.0, 0.0, -80.0), (xc - s * 106.0, 70.0, 80.0), m["rackside"], g)
    bx(f"{name}_wi", (xc + s * 106.0, 0.0, -80.0), (xc + s * 110.0, 70.0, -10.0), m["rackside"], g)
    bx(f"{name}_wf", (xc - 110.0, 0.0, 76.0), (xc + 110.0, 14.0, 80.0), m["rackside"], g)
    racks = []
    for r in range(3):
        z = -55.0 + 40.0 * r
        for k in range(8):
            x = xc - 90.0 + 18.0 * k
            racks.append(bx(f"{name}_r{r}{k}", (x - 7.0, 2.0, z - 10.0), (x + 7.0, 50.0, z + 10.0), m["rack"], g))
    join(racks, f"{name}_racks")
    lg = empty(f"{name}_leds", root)
    ls = []
    for r in range(3):
        z = -45.0 + 40.0 * r
        for k in range(8):
            x = xc - 90.0 + 18.0 * k
            ls.append(bx(f"{name}_l{r}{k}", (x - 4.0, 40.0, z), (x - 1.0, 42.0, z + 0.4), m["led"], lg))
    join(ls, f"{name}_ledm")
    # router chassis near the link wall
    rx = xc + s * 85.0
    bx(f"{name}_rt", (rx - 10.0, 2.0, 20.0), (rx + 10.0, 46.0, 40.0), m["server"], g)
    for k in range(8):
        y = 8.0 + 4.5 * k
        bx(f"{name}_rc{k}", (rx - 9.0, y, 40.0), (rx + 9.0, y + 3.0, 40.6), m["cage"], g)
    port = (rx, 26.0, 40.8)
    exitp = (xc + s * 112.0, DY + 2.0, 30.0)
    return g, lg, port, exitp


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m.update(NL.materials())
    cm = [mat(f"dci_c{i}", c, emit=c, strength=4.5) for i, c in enumerate(COLORS)]
    bx("ground", (-460.0, -14.0, -120.0), (460.0, 0.0, 120.0), m["tile"], empty("gnd", root))
    gA, lA, pA, eA = building(m, root, BXS[0], "dcA")
    gB, lB, pB, eB = building(m, root, BXS[1], "dcB")
    blink(lA, 0, [0, 2, 4, 6], n=8, on=0.6)
    blink(lB, 4, [1, 3, 5, 7], n=8, on=0.6)
    # duct: an open trench with the cable
    tr = empty("trench", root)
    bx("trench", (eA[0], 0.0, 24.0), (eB[0], 0.3, 36.0), m["bezel"], tr)
    duct = [pA, (pA[0], DY + 2.0, pA[2]), (eA[0], DY + 2.0, 30.0), (0.0, DY + 2.0, 30.0), (eB[0], DY + 2.0, 30.0),
            (pB[0], DY + 2.0, pB[2]), pB]
    wire("duct", duct, 1.6, m["aoc"], tr, 10)
    # amplifier hut at x = 0
    hut = empty("hut", root)
    bx("hut", (-16.0, 0.0, 40.0), (16.0, 24.0, 70.0), m["psu"], hut)
    bx("hutr", (-18.0, 24.0, 38.0), (18.0, 27.0, 72.0), m["rack"], hut)
    bx("edfa", (-10.0, 0.0, 30.0), (10.0, 6.0, 42.0), m["dsp"], hut)
    hl = empty("hutled", root)
    bx("hl", (-6.0, 6.0, 36.0), (6.0, 6.6, 38.0), m["led_a"], hl)
    blink(hl, 3, [0, 2, 4, 6], n=8, on=0.6)

    a_half = duct[:4]
    b_half = duct[3:]
    # beat 0: one stream
    run(root, "s0", duct, 8, 2.0, m["pkt"], 0, 0.0, 0.7, 90)
    # beat 1: five colors on one fibre
    for i, c in enumerate(cm):
        off = [(p[0], p[1] + 0.0, p[2]) for p in duct]
        run(root, f"w{i}", off, 5, 1.6, c, 1, 0.02 * i, 0.75, 80)
    # beat 2: ZR optic cut open, pulled from router A
    zo = (pA[0] + 30.0, 30.0, pA[2] + 30.0)
    zr, zp = NL.osfp(m, root, zo, 5.0, name="zr")
    present(zr, [(F(2, 0.0), F(3, 0))])
    run(root, "zdsp", [zp["edge"], zp["dsp"], zp["las"], zp["mpo"]], 6, 0.7, cm[3], 2, 0.0, 0.7, 30)
    run(root, "zout", duct, 5, 1.8, cm[3], 2, 0.2, 0.8, 90)
    # beat 3: dim beads arrive at the hut, bright ones leave
    for i, c in enumerate(cm):
        run(root, f"dim{i}", a_half, 4, 1.1, m["lit"], 3, 0.02 * i, 0.5, 45)
        run(root, f"amp{i}", b_half, 4, 1.8, c, 3, 0.3 + 0.02 * i, 0.85, 45)
    # beat 4: both ways
    rev = list(reversed(duct))
    for i, c in enumerate(cm[:3]):
        run(root, f"ab{i}", duct, 4, 1.6, c, 4, 0.03 * i, 0.8, 80)
        run(root, f"ba{i}", rev, 4, 1.6, cm[3 + (i % 2)], 4, 0.05 + 0.03 * i, 0.85, 80)

    C.tags(root, {
        0: [("data center A", (BXS[0], 60.0, -40.0)), ("data center B", (BXS[1], 60.0, -40.0)),
            ("fibre duct, km to 100s of km", (-150.0, 2.0, 30.0))],
        1: [("one fibre, many colors", (-150.0, 2.0, 30.0)), ("each color = one channel", (150.0, 2.0, 30.0)),
            ("64 x 800G = 51 Tb/s", (0.0, 28.0, 55.0))],
        2: [("router port", pA), ("ZR coherent optic", zp["dsp"]), ("laser + DSP in the plug", zp["las"])],
        3: [("faded signal in", (-120.0, 2.0, 30.0)), ("amplifier hut (EDFA)", (0.0, 27.0, 55.0)),
            ("all colors boosted", (120.0, 2.0, 30.0))],
        4: [("GPU halls, site A", (BXS[0], 52.0, 0.0)), ("GPU halls, site B", (BXS[1], 52.0, 0.0)),
            ("traffic both ways", (0.0, 2.0, 30.0))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 20.0, 0.0), 820.0, 0.0, 0.35, pad=0.9),
        [(0.0, frame((-140.0, 5.0, 30.0), 260.0, 0.20, 0.30)), (0.6, frame((140.0, 5.0, 30.0), 260.0, -0.20, 0.30))],
        frame((pA[0] + 20.0, 25.0, pA[2] + 10.0), 110.0, 0.55, 0.35),
        frame((0.0, 10.0, 40.0), 280.0, 0.10, 0.40),
        frame((0.0, 30.0, 0.0), 820.0, 0.05, 0.50, pad=0.9),
    ], root)


if __name__ == "__main__":
    build()
