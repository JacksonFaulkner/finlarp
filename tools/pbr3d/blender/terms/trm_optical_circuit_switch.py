"""TRM_OPTICAL_CIRCUIT_SWITCH: the Terms-tab overview for an optical circuit switch (OCS).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_optical_circuit_switch.py

Writes assets/term_TRM_OPTICAL_CIRCUIT_SWITCH.glb and specs/terms/TRM_OPTICAL_CIRCUIT_SWITCH.json.

Two rows of accelerator racks fibred into an OCS chassis in the middle. The chassis lid comes off:
an input collimator array on the left wall, a MEMS mirror array low in the middle, a second mirror
array raised on a mount, an output collimator array on the right wall. Light goes fibre -> mirror
-> mirror -> fibre, never becoming electrical. Tilting one mirror re-points a beam to a new output.

Beats:
  0 pod       racks of accelerators fibred into one OCS chassis
  1 inside    lid off: collimators, two MEMS mirror arrays
  2 light     the beam bounces mirror to mirror; no packets read, no electronics in the path
  3 retarget  one mirror tilts; the beam lands on a different output in milliseconds
  4 power     beside an electrical packet switch: no SerDes, no heat, any speed
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import net_leaf_detail as NL  # noqa: E402
import sand_overview as O  # noqa: E402
from sand_overview import F, show, empty, mat, tube  # noqa: E402
from power_vrm_detail import bx, wire, run, rise, blink, present, frame, join  # noqa: E402

SLUG = "TRM_OPTICAL_CIRCUIT_SWITCH"
BEATS = [
    ("An optical circuit switch patches fibre to fibre with mirrors",
     "An optical circuit switch (OCS) connects any input fibre to any output fibre by steering the light itself. "
     "Google puts OCS between the racks of its TPU pods and in its data-center spine, so the wiring between racks can "
     "be changed by software instead of by people re-plugging cables."),
    ("Inside: collimators and two arrays of tiny tilting mirrors",
     "Each input fibre ends in a collimator lens that launches a narrow beam into free space. The beam hits a MEMS "
     "mirror (a silicon mirror under a millimetre across, tilted by electrostatic force), then a second mirror array, "
     "which aims it into the chosen output collimator. Arrays of over a hundred ports per side are common."),
    ("Light in, light out, never turned into electricity",
     "The switch never reads a packet. Light passes straight through, so it does not care about protocol or line rate: "
     "the same OCS carries 400G today and 1.6T later. There are no SerDes, no DSP and no buffers in the path."),
    ("Tilt a mirror and the beam lands on a different fibre",
     "Re-pointing a mirror makes a new connection in milliseconds. That is far too slow to switch individual packets, so "
     "OCS is used for topologies that change rarely: carving a TPU pod into slices, routing around a failed rack, or "
     "rebalancing spine capacity."),
    ("Far less power than an electrical switch, at any speed",
     "A packet switch converts every bit to electricity, processes it and converts it back, burning watts per port and "
     "needing new silicon each speed generation. An OCS port costs a few hundred milliwatts and survives upgrades. "
     "Related: Alphabet (GOOGL), Lumentum (LITE), Coherent (COHR), Ciena (CIEN)."),
]

XIN, XA, XB, XOUT = -55.0, -12.0, 22.0, 56.0
YIN, YA, YB = 22.0, 6.0, 34.0
ZS = [-21.0 + 6.0 * k for k in range(8)]


def mirror(m, parent, name, c, tilt_axis="z"):
    """A MEMS mirror: a gold plate on a gimbal frame, under its own empty (for tilting)."""
    e = empty(name, parent, loc=c)
    e.location = O.P(*c)
    ps = [bx(f"{name}_fr", (-2.3, -0.4, -2.3), (2.3, -0.1, 2.3), m["si"], e),
          bx(f"{name}_pl", (-1.8, -0.1, -1.8), (1.8, 0.2, 1.8), m["gold"], e)]
    join(ps, f"{name}_m")
    return e


def tilt(e, b, u0, u1, a0, a1, axis=1):
    O._interp("LINEAR")
    for u, a in ((0.0, a0), (u0, a0), (u1, a1), (0.999, a1)):
        r = [0.0, 0.0, 0.0]
        r[axis] = a
        e.rotation_euler = tuple(r)
        e.keyframe_insert("rotation_euler", frame=F(b, u))


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m.update(NL.materials())
    m["beam"] = mat("ocs_beam", (1.0, 0.35, 0.30), emit=(1.0, 0.30, 0.25), strength=4.0)
    m["beam2"] = mat("ocs_beam2", (0.4, 0.9, 1.0), emit=(0.35, 0.85, 1.0), strength=4.0)
    bx("floor", (-330.0, -2.0, -200.0), (330.0, 0.0, 160.0), m["tile"], empty("fl", root))

    # chassis
    ch = empty("ocs", root)
    bx("pan", (-66.0, 0.0, -32.0), (66.0, 2.0, 32.0), m["chassis"], ch)
    bx("back", (-66.0, 0.0, -32.0), (66.0, 46.0, -30.0), m["chassis"], ch)
    bx("wl", (-66.0, 0.0, -32.0), (-62.0, 46.0, 32.0), m["chassis"], ch)
    bx("wr", (62.0, 0.0, -32.0), (66.0, 46.0, 32.0), m["chassis"], ch)
    bx("front", (-66.0, 0.0, 30.0), (66.0, 8.0, 32.0), m["bezel"], ch)
    lid = empty("lid", root)
    bx("lidb", (-66.0, 46.0, -32.0), (66.0, 48.0, 32.0), m["chassis"], lid)
    bx("lidf", (-66.0, 8.0, 30.0), (66.0, 46.0, 32.0), m["chassis"], lid)
    present(lid, [(F(0, 0.0), F(0, 0.999))])
    # collimator arrays
    for side, x in (("in", XIN), ("out", XOUT)):
        s = 1 if side == "in" else -1
        bx(f"cblk_{side}", (x - 4.0 * s, YIN - 6.0, -25.0), (x + 1.0 * s, YIN + 6.0, 25.0), m["dsp"], ch)
        for k, z in enumerate(ZS):
            for row in (-3.0, 3.0):
                tube(f"col_{side}{k}{row}", (x, YIN + row, z), (x + 2.5 * s, YIN + row, z), 1.0, m["glass"], ch, 10)
    # mirror mounts
    bx("mntA", (XA - 4.0, 2.0, -26.0), (XA + 4.0, YA - 1.0, 26.0), m["psu"], ch)
    bx("mntB", (XB - 4.0, YB + 1.0, -26.0), (XB + 4.0, YB + 4.0, 26.0), m["psu"], ch)
    bx("mntBp", (XB - 2.0, 2.0, -28.0), (XB + 2.0, YB + 4.0, -24.0), m["psu"], ch)
    mA = [mirror(m, ch, f"mA{k}", (XA, YA, z)) for k, z in enumerate(ZS)]
    mB = [mirror(m, ch, f"mB{k}", (XB, YB, z)) for k, z in enumerate(ZS)]
    for e in mB:
        e.rotation_euler = (0.0, math.pi, 0.0)
    # fibres out the sides to the racks
    fg = empty("fib", root)
    pod_in, pod_out = [], []
    for k, z in enumerate(ZS):
        a = (XIN - 6.0, YIN, z)
        pts = [(-250.0, 180.0 - 20.0 * (k % 4), -40.0 + 20.0 * (k // 4) - 20.0), (-150.0, 90.0, z * 1.5), (-80.0, YIN, z), a]
        wire(f"fi{k}", pts, 0.5, m["smf"], fg, 6)
        pod_in.append(pts)
        b = (XOUT + 6.0, YIN, z)
        pts = [b, (80.0, YIN, z), (150.0, 90.0, z * 1.5), (250.0, 180.0 - 20.0 * (k % 4), -40.0 + 20.0 * (k // 4) - 20.0)]
        wire(f"fo{k}", pts, 0.5, m["smf"], fg, 6)
        pod_out.append(pts)
    # accelerator racks
    for side, x0 in (("L", -300.0), ("R", 220.0)):
        for j in range(2):
            xc = x0 + 40.0 * j + 20.0
            g = empty(f"rk{side}{j}", root)
            bx(f"rk{side}{j}b", (xc - 18.0, 0.0, -60.0 + 0.0 * j), (xc + 18.0, 200.0, 0.0), m["rack"], g)
            for t in range(8):
                y = 14.0 + 22.0 * t
                bx(f"rk{side}{j}t{t}", (xc - 16.0, y, -1.0), (xc + 16.0, y + 18.0, 0.5), m["server"], g)
            lg = empty(f"rk{side}{j}l", root)
            for t in range(8):
                y = 14.0 + 22.0 * t
                bx(f"rk{side}{j}l{t}", (xc + 10.0, y + 12.0, 0.4), (xc + 13.0, y + 14.0, 0.9), m["led"], lg)
            blink(lg, 0, [j, j + 2, j + 4, j + 6], n=8, on=0.6)

    def beam(i, o):
        return [(XIN + 2.5, YIN + 3.0, ZS[i]), (XA, YA + 0.3, ZS[i]), (XB, YB - 0.3, ZS[o]), (XOUT - 2.5, YIN + 3.0, ZS[o])]

    # beat 0: light from racks into the OCS and out
    for k in (0, 3, 5):
        run(root, f"pi{k}", pod_in[k], 3, 1.6, m["beam"], 0, 0.05 + 0.05 * k, 0.6, 50)
        run(root, f"po{k}", pod_out[(k + 3) % 8], 3, 1.6, m["beam"], 0, 0.3 + 0.05 * k, 0.85, 50)
    # beat 1/2: several beams through mirror pairs
    pairs = [(0, 4), (2, 1), (4, 6), (6, 3), (7, 7)]
    for i, o in pairs:
        run(root, f"b1_{i}", beam(i, o), 4, 0.7, m["beam"], 1, 0.05 + 0.03 * i, 0.8, 30)
        run(root, f"b2_{i}", beam(i, o), 8, 0.9, m["beam"], 2, 0.0 + 0.02 * i, 0.85, 30)
    # beam lines (persistent faint rays) during beat 2
    rays = empty("rays", root)
    for i, o in pairs:
        p = beam(i, o)
        for k in range(3):
            tube(f"ray{i}{k}", p[k], p[k + 1], 0.25, m["lit"], rays, 6)
    present(rays, [(F(2, 0.0), F(3, 0))])
    # beat 3: input 3 goes to output 6, mirror A3 tilts, then to output 1
    run(root, "r0", beam(3, 6), 6, 1.0, m["beam"], 3, 0.0, 0.3, 30, until=F(3, 0.42))
    run(root, "r1", beam(3, 1), 6, 1.0, m["beam2"], 3, 0.55, 0.85, 30)
    tilt(mA[3], 3, 0.42, 0.52, 0.0, 0.35, axis=0)
    tilt(mB[1], 3, 0.42, 0.52, 0.0, 0.25, axis=0)
    flag = empty("flag", root)
    bx("fl3", (XA - 3.0, YA + 2.5, ZS[3] - 3.0), (XA + 3.0, YA + 3.0, ZS[3] + 3.0), m["ecn"], flag)
    show(flag, [(F(3, 0.40), F(3, 0.56))])
    # beat 4: an electrical packet switch beside, hot; the OCS cool
    pk = empty("pkt", root)
    sw = NL.switch(m, pk, (0.0, 0.0, 140.0), 1.6, detail=True, name="esw")
    show(sw["die_glow"], [(F(4, 0.0), F(5, 0))])
    rise(pk, "eheat", sw["parts"]["heatsink"], 12, 0.8, m["heat"], 4, 0.0, 0.8, h=40.0, life=50, spread=(10.0, 10.0))
    run(pk, "oeo", [sw["down"][4], sw["tr_down"][4][2], sw["asic"], sw["tr_up"][26][2], sw["up"][26]], 5, 0.8, m["pkt"], 4,
        0.05, 0.8, 40)
    present(pk, [(F(4, 0.0), F(5, 0))])
    for i, o in pairs:
        run(root, f"b4_{i}", beam(i, o), 4, 0.8, m["beam"], 4, 0.0 + 0.02 * i, 0.85, 30)

    C.tags(root, {
        0: [("OCS chassis", (0.0, 50.0, 0.0)), ("accelerator racks", (-280.0, 205.0, -30.0)),
            ("fibre in, fibre out", pod_out[2][2])],
        1: [("input collimators", (XIN, YIN + 7.0, ZS[6])), ("MEMS mirror array", (XA, YA + 2.0, ZS[1])),
            ("second mirror array", (XB, YB + 4.0, ZS[6])), ("output collimators", (XOUT, YIN + 7.0, ZS[1]))],
        2: [("free-space beam", beam(4, 6)[1]), ("no electronics in path", (XB, YB + 4.0, ZS[2])),
            ("any protocol, any speed", (XOUT, YIN + 7.0, ZS[5]))],
        3: [("mirror tilts", (XA, YA + 3.0, ZS[3])), ("new output", (XOUT, YIN + 7.0, ZS[1])),
            ("milliseconds, not per-packet", (XB, YB + 4.0, ZS[6]))],
        4: [("packet switch: hot ASIC", sw["parts"]["heatsink"]), ("light->bits->light", sw["up"][26]),
            ("OCS: mirrors only, cool", (XB, YB + 4.0, ZS[4]))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 80.0, -20.0), 620.0, 0.20, 0.25, pad=1.0),
        frame((0.0, 20.0, 0.0), 135.0, 0.35, 0.55),
        frame((0.0, 20.0, 0.0), 110.0, 0.55, 0.40),
        frame((5.0, 18.0, -5.0), 95.0, 0.20, 0.50),
        frame((0.0, 15.0, 70.0), 220.0, 0.40, 0.45),
    ], root)


if __name__ == "__main__":
    build()
