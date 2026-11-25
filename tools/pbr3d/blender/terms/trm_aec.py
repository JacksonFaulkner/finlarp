"""TRM_AEC: the Terms-tab overview for an active electrical cable, at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_aec.py

Writes assets/term_TRM_AEC.glb and specs/terms/TRM_AEC.json.

An AI rack seen from the front: GPU servers below, a top-of-rack switch at the top, thick copper
cables looping from each server's NIC ports up to the switch. One cable's plug is blown up on the
right and cut open: shell, paddle card, the retimer/DSP chip, twinax pairs soldered on. A reach
ruler beside the rack compares passive copper, AEC and optics.

Beats:
  0 rack     servers cabled to the top-of-rack switch
  1 cable    plain copper twinax with a chip in each plug
  2 plug     inside the plug: the DSP cleans and resends every lane
  3 reach    passive 1-2 m, AEC 3-7 m
  4 tradeoff cheaper and lower power than optics
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from sand_overview import F, show, empty  # noqa: E402
from power_vrm_detail import run, frame, bx, polyline, blink, mat, present, arc, rise  # noqa: E402

import term_common as C  # noqa: E402
import kit_link as K  # noqa: E402

SLUG = "TRM_AEC"
BEATS = [
    ("Inside an AI rack, thick copper cables tie every server to the switch",
     "Each GPU server has several 400G or 800G network ports, and they all run up to a top-of-rack switch a "
     "metre or two away. These short hops are the most numerous links in a cluster. For years they were "
     "passive copper (DAC) cables, but at 100G+ per lane passive copper stops reaching."),
    ("An AEC is copper cable with a small chip in each plug",
     "An active electrical cable keeps the cheap twinax copper in the middle and adds a retimer or DSP chip "
     "inside each connector shell. The plug looks and fits like any other QSFP or OSFP module, so the switch "
     "and NIC need no changes."),
    ("The chip in the plug cleans up and resends every lane",
     "Signals arriving over the copper are blurred and weak. The chip equalizes them, recovers the clock and "
     "retransmits a fresh signal, in both directions, for every lane. It draws a few watts per end, much less "
     "than the lasers and DSP in an optical module."),
    ("Passive copper reaches 1-2 m at 100G+; an AEC reaches 3-7 m",
     "Loss in copper grows with length and frequency, so passive cables shrink with each speed step: about "
     "2 m at 100G per lane and roughly 1 m at 200G. The retimer resets the loss budget, stretching copper to "
     "around 7 m, enough to span a rack or reach the neighbour."),
    ("Cheaper and lower power than optics for short links",
     "Optics would work over any distance but cost more, use more power and fail more often. For in-rack and "
     "rack-to-rack links AECs win, and hyperscalers now buy them by the million. Related: Credo (CRDO), "
     "Marvell (MRVL), Astera Labs (ALAB), Amphenol (APH)."),
]

RX0, RX1 = -40.0, 40.0  # rack inner width (x)
SW_Y = (190.0, 200.0)  # top-of-rack switch
SRV = [(18.0 + 34.0 * k, 18.0 + 34.0 * k + 28.0) for k in range(5)]  # server y ranges
PLUG = (130.0, 100.0, 0.0)  # bench plug position (x of shell start)


def rack(m, root):
    g = empty("rack", root)
    for x in (RX0 - 4.0, RX1):
        for z in (-60.0, 0.0):
            bx(f"post{x}{z}", (x, 0.0, z - 4.0), (x + 4.0, 210.0, z), m["steel"], g)
    bx("rtop", (RX0 - 4.0, 210.0, -64.0), (RX1 + 4.0, 213.0, 0.0), m["steel"], g)
    bx("rbase", (RX0 - 6.0, -2.0, -66.0), (RX1 + 6.0, 0.0, 2.0), m["dark"], g)
    # switch
    bx("sw", (RX0, SW_Y[0], -56.0), (RX1, SW_Y[1], -1.0), m["lnk_pkg"], g)
    ports = []
    for i in range(16):
        x = RX0 + 3.0 + i * 4.7
        bx(f"swp{i}", (x, SW_Y[0] + 2.0, -1.0), (x + 3.6, SW_Y[1] - 2.0, -0.6), m["steel"], g)
        ports.append((x + 1.8, SW_Y[0] + 5.0, -0.4))
    leds = []
    for k, (y0, y1) in enumerate(SRV):
        bx(f"srv{k}", (RX0, y0, -56.0), (RX1, y1, -1.0), m["alu"], g)
        bx(f"bez{k}", (RX0 + 2.0, y0 + 2.0, -1.0), (RX0 + 40.0, y1 - 2.0, -0.4), m["grid"], g)
        for j in range(2):
            x = RX1 - 32.0 + j * 14.0
            bx(f"nic{k}{j}", (x, y0 + 8.0, -1.0), (x + 10.0, y0 + 16.0, -0.4), m["steel"], g)
        lg = empty(f"led{k}", g)
        bx(f"led{k}b", (RX0 + 3.0, y1 - 5.0, -0.4), (RX0 + 5.0, y1 - 3.0, 0.0), m["sig"], lg)
        leds.append(lg)
    return g, ports, leds


def cable(m, parent, name, a, b, k):
    """A thick cable looping out in front of the rack from server port a to switch port b, with
    plug shells on both ends. Returns its centre-line path."""
    mid = ((a[0] + b[0]) / 2 + 52.0 - 4.0 * k, (a[1] + b[1]) / 2, 22.0 + 3.0 * k)
    pts = [a, (a[0], a[1], 8.0), mid, (b[0], b[1], 8.0), b]
    polyline(f"{name}_c", pts, 1.1, m["rubber"], parent)
    for i, p in enumerate((a, b)):
        bx(f"{name}_p{i}", (p[0] - 2.4, p[1] - 2.0, p[2]), (p[0] + 2.4, p[1] + 2.0, 8.0), m["steel"], parent)
    return pts


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    m["pass_bar"] = mat("t_pass_bar", (0.9, 0.5, 0.2), emit=(0.9, 0.5, 0.2), strength=1.5)
    _, ports, leds = rack(m, root)
    bx("floor", (-200.0, -4.0, -200.0), (260.0, -2.0, 120.0), m["dark"], root)

    paths = []
    for k, (y0, _) in enumerate(SRV):
        for j in range(2):
            a = (RX1 - 27.0 + j * 14.0, y0 + 12.0, 0.0)
            b = ports[k * 3 + j]
            paths.append(cable(m, root, f"cb{k}{j}", a, b, k * 2 + j))
    for i, lg in enumerate(leds):
        blink(lg, 0, [i % 3], n=3, on=0.7)
    # beat 0 + 4: bits flowing up every cable and back
    for i, p in enumerate(paths):
        run(root, f"up{i}", p, 3, 0.9, m["sig"], [0, 4], 0.02 * i, 0.6 + 0.02 * i, 50)
        run(root, f"dn{i}", p[::-1], 2, 0.9, m["e_blue"], [0, 4], 0.3 + 0.02 * i, 0.95, 50)

    # bench: big cut-open plug + a length of cable
    pl = empty("plug", root)
    x0, y0, z0 = PLUG
    L = 70.0
    bx("shell_b", (x0, y0 - 9.0, z0 - 12.0), (x0 + L, y0 - 7.5, z0 + 12.0), m["steel"], pl)  # floor of the shell
    bx("shell_s", (x0, y0 - 9.0, z0 - 12.0), (x0 + L, y0 + 9.0, z0 - 10.5), m["steel"], pl)  # back wall
    bx("pcb", (x0 + 4.0, y0 - 3.0, z0 - 9.0), (x0 + L - 8.0, y0 - 1.6, z0 + 9.0), m["fr4"], pl)
    fing = []
    for i in range(8):
        z = z0 - 8.0 + i * 2.2
        bx(f"fg{i}", (x0 + 4.0, y0 - 1.6, z - 0.7), (x0 + 10.0, y0 - 1.3, z + 0.7), m["gold"], pl)
        fing.append((x0 + 7.0, y0 - 1.0, z))
    chip = (x0 + 30.0, y0, z0)
    bx("dsp", (chip[0] - 9.0, y0 - 1.6, z0 - 7.0), (chip[0] + 9.0, y0 + 1.4, z0 + 7.0), m["lnk_pkg"], pl)
    bx("dsp_die", (chip[0] - 5.0, y0 + 1.4, z0 - 4.0), (chip[0] + 5.0, y0 + 1.8, z0 + 4.0), m["lnk_si"], pl)
    for i in range(4):
        z = z0 - 6.0 + i * 4.0
        bx(f"cap{i}", (x0 + 46.0, y0 - 1.6, z - 0.8), (x0 + 48.0, y0 - 0.2, z + 0.8), m["mlcc"], pl)
    pairs = []
    for i in range(4):
        z = z0 - 6.0 + i * 4.0
        for s in (-0.7, 0.7):
            polyline(f"tw{i}{s}", [(x0 + L - 10.0, y0 - 1.0, z + s), (x0 + L + 8.0, y0 - 1.0, z + s * 0.6),
                                    (x0 + L + 50.0, y0 - 1.0, z0 + (z - z0) * 0.3 + s * 0.5)], 0.45, m["copper"], pl)
        pairs.append(z)
    polyline("jacket", [(x0 + L + 20.0, y0 - 1.0, z0), (x0 + L + 60.0, y0 - 1.0, z0)], 4.5, m["rubber"], pl)
    present(pl, [(F(1, 0.0), F(3, 0))])
    for i, z in enumerate(pairs):
        run(root, f"cin{i}", [(x0 + L + 50.0, y0 + 0.5, z0 + (z - z0) * 0.3), (x0 + L - 10.0, y0 + 0.5, z), (chip[0] + 9.0, y0 + 2.0, z0)],
            4, 0.7, m["dim_glow"], 2, 0.0 + 0.05 * i, 0.5, 45)
        run(root, f"cout{i}", [(chip[0] - 9.0, y0 + 2.0, z0), fing[i * 2]], 4, 0.7, m["sig"], 2, 0.3 + 0.05 * i, 0.9, 30)
    hot = rise(root, "heat", (chip[0], y0 + 2.0, z0), 6, 0.6, m["h_amber"], 2, 0.1, 0.8, h=14.0, life=50)

    # beat 3: reach ruler on the floor in front of the rack
    rg = empty("ruler", root)
    zr = 70.0
    for i, (xa, xb, mt) in enumerate(((-40.0, 0.0, "pass_bar"), (-40.0, 100.0, "lnk_bar"))):
        bx(f"rb{i}", (xa, 0.0, zr + 14.0 * i), (xb, 3.0, zr + 14.0 * i + 6.0), m[mt], rg)
    for i in range(8):  # metre ticks, 20 units = 1 m
        x = -40.0 + 20.0 * i
        bx(f"tk{i}", (x - 0.4, 0.0, zr - 6.0), (x + 0.4, 1.0, zr - 2.0), m["white"], rg)
    present(rg, [(F(3, 0.0), F(4, 0))])

    # beat 4: an optical module next to the cable for comparison (warmer, more parts)
    og = empty("optic", root)
    bx("opt_b", (130.0, 60.0, -10.0), (200.0, 74.0, 10.0), m["alu"], og)
    bx("opt_fin", (140.0, 74.0, -8.0), (190.0, 78.0, 8.0), m["steel"], og)
    present(og, [(F(4, 0.0), F(5, 0))])
    rise(root, "oheat", (165.0, 78.0, 0.0), 10, 0.8, m["h_amber"], 4, 0.0, 0.85, h=24.0, life=60, spread=(18.0, 6.0))

    C.tags(root, {
        0: [("top-of-rack switch", (0.0, SW_Y[1] + 4.0, 0.0)), ("GPU servers", (-20.0, 100.0, 0.0)),
            ("copper cables to each NIC", paths[4][2])],
        1: [("DSP chip in each plug", chip), ("plain twinax copper", (x0 + L + 40.0, y0 + 4.0, z0)),
            ("fits a normal OSFP port", fing[0])],
        2: [("weak, blurred lanes in", (x0 + L, y0 + 2.0, z0)), ("equalize + retime", (chip[0], y0 + 4.0, z0)),
            ("clean signal out", fing[3]), ("a few watts per end", (chip[0], y0 + 14.0, z0))],
        3: [("passive DAC: ~2 m", (-20.0, 4.0, zr + 3.0)), ("AEC: up to ~7 m", (60.0, 4.0, zr + 17.0)),
            ("1 m ticks", (-40.0, 1.0, zr - 4.0))],
        4: [("optical module: more watts, $", (165.0, 80.0, 0.0)), ("AEC: cheap copper + chip", paths[4][2])],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 105.0, 0.0), 240.0, 0.35, 0.15, pad=1.0),
        frame((150.0, 100.0, 0.0), 150.0, 0.30, 0.35),
        frame((x0 + 40.0, y0, z0), 80.0, 0.25, 0.55),
        frame((30.0, 20.0, 50.0), 200.0, 0.20, 0.50),
        frame((80.0, 100.0, 0.0), 260.0, 0.30, 0.15, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
