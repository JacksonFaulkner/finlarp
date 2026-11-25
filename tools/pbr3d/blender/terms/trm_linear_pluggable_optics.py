"""TRM_LINEAR_PLUGGABLE_OPTICS: the Terms-tab overview for linear pluggable optics (LPO).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_linear_pluggable_optics.py

Writes assets/term_TRM_LINEAR_PLUGGABLE_OPTICS.glb. Captions live in specs/terms/TRM_LINEAR_PLUGGABLE_OPTICS.json.

Beats:
  0 pair     a switch ASIC on its board with two cut-open modules: a DSP module and an LPO module
  1 dsp      in the DSP module the bits stop at a hot DSP chip that re-times them
  2 linear   in the LPO module the host SerDes signal goes straight to a linear driver and the laser
  3 power    module power bars ~15 W vs ~8 W; less heat, lower latency
  4 limits   short reach, tight interop; LRO middle ground; tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, mat, show  # noqa: E402
from power_vrm_detail import bx, frame, polyline, rise, run  # noqa: E402

import term_common as C  # noqa: E402
import kit_photonics as K  # noqa: E402

SLUG = "TRM_LINEAR_PLUGGABLE_OPTICS"
BEATS = [
    ("LPO is an optical module with the DSP chip taken out",
     "A standard 800G pluggable transceiver carries a digital signal processor (DSP) that cleans up and re-times the "
     "signal before it reaches the laser. Linear pluggable optics remove that chip and drive the laser and receiver "
     "with purely analog, linear electronics. Here a conventional module (top) and an LPO module (bottom) sit in "
     "front of the same switch chip."),
    ("A DSP module re-times every bit, and that costs power",
     "In the conventional module, the electrical lanes from the switch land on the DSP, which equalises, recovers the "
     "clock and re-sends clean bits to the laser driver. That chip is about half of the module's power and adds "
     "latency on every hop."),
    ("In LPO the host's SerDes does the cleanup",
     "With LPO the switch or GPU SerDes drives the signal across the board, and the module only amplifies it "
     "linearly: driver to laser on the way out, photodiode to linear TIA on the way in. All the equalisation lives in "
     "the big chip's SerDes, which is already there and already powered."),
    ("Dropping the DSP saves roughly 30-50% of module power",
     "An 800G DSP module draws around 14-16 W, an LPO module around 7-9 W. Across tens of thousands of links in an AI "
     "cluster that is megawatts, plus less heat in the faceplate, lower cost and tens of nanoseconds less latency per "
     "link."),
    ("The catch: shorter reach and tighter matching",
     "Without a DSP to fix things, the whole channel (host SerDes, board traces, module, fibre) must be good enough "
     "end to end, so LPO targets short in-rack and in-row links and needs tested host-module pairings. Linear receive "
     "optics (LRO) keep a DSP on transmit only as a middle ground. Broadcom (AVGO), Marvell (MRVL), Arista (ANET), "
     "Coherent (COHR) and Lumentum (LITE) are involved."),
]

ASIC_X = -70.0
MX0, MX1 = 0.0, 80.0
ZD, ZL = -22.0, 22.0  # module centre lines: DSP top, LPO bottom
Y = 2.0


def module(m, parent, name, zc, dsp):
    g = empty(name, parent)
    bx(f"{name}_b", (MX0, Y, zc - 13.0), (MX1, Y + 1.0, zc + 13.0), m["steel"], g)
    for k, (za, zb) in enumerate(((zc - 13.0, zc - 12.0), (zc + 12.0, zc + 13.0))):
        bx(f"{name}_s{k}", (MX0, Y, za), (MX1, Y + 10.0, zb), m["steel"], g)
    bx(f"{name}_e", (MX1 - 1.0, Y, zc - 13.0), (MX1, Y + 10.0, zc + 13.0), m["steel"], g)
    bx(f"{name}_pcb", (MX0 - 4.0, Y + 1.0, zc - 10.0), (MX1 - 18.0, Y + 2.4, zc + 10.0), m["ph_pcb"], g)
    for k in range(8):
        z = zc - 8.0 + 2.2 * k
        bx(f"{name}_f{k}", (MX0 - 4.0, Y + 2.4, z - 0.6), (MX0 + 4.0, Y + 2.6, z + 0.6), m["ph_gold"], g)
    out = {"g": g}
    yt = Y + 2.4
    if dsp:
        bx(f"{name}_dsp", (14.0, yt, zc - 8.0), (30.0, yt + 2.0, zc + 8.0), m["ph_dsp"], g)
        bx(f"{name}_dsph", (15.0, yt + 2.0, zc - 7.0), (29.0, yt + 2.4, zc + 7.0), m["steel"], g)
        out["dsp"] = (22.0, yt + 2.4, zc)
    C.chip(m, g, f"{name}_drv", (40.0, yt, zc - 4.5), 6.0, 5.0, h=1.2, pins=4)
    C.chip(m, g, f"{name}_tia", (40.0, yt, zc + 4.5), 6.0, 5.0, h=1.2, pins=4)
    bx(f"{name}_opt", (48.0, yt, zc - 8.0), (58.0, yt + 2.0, zc + 8.0), m["ceramic"], g)
    for k in range(4):
        z = zc - 7.0 + 1.4 * k
        K.laser(m, g, f"{name}_las{k}", (55.0, yt + 2.0, z), "ph_red", size=0.6)
    for k in range(4):
        z = zc + 2.0 + 1.4 * k
        bx(f"{name}_pd{k}", (54.5, yt + 2.0, z - 0.5), (56.0, yt + 2.8, z + 0.5), m["ph_dsp"], g)
    for k in range(8):
        z = zc - 7.0 + 1.4 * (k % 4) + (9.0 if k >= 4 else 0.0)
        K.fiber(m, g, f"{name}_fb{k}", [(56.5, yt + 2.5, z), (70.0, yt + 3.0, zc + (z - zc) * 0.3), (MX1 + 20.0, yt + 3.0, zc)], r=0.3)
    out["yt"] = yt
    return out


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    m["warm"] = mat("lpo_warm", (1.0, 0.45, 0.15), emit=(1.0, 0.35, 0.1), strength=0.5)
    m["bar_r"] = mat("lpo_barr", (1.0, 0.3, 0.2), emit=(1.0, 0.25, 0.15), strength=1.0)
    m["bar_g"] = mat("lpo_barg", (0.3, 1.0, 0.5), emit=(0.3, 1.0, 0.5), strength=1.0)

    scene = empty("scene", root)
    bx("board", (-120.0, -1.6, -50.0), (0.0, Y, 50.0), m["ph_pcb"], scene)
    C.chip(m, scene, "asic", (ASIC_X, Y, 0.0), 40.0, 40.0, h=3.0, pins=0)
    bx("asic_lid", (ASIC_X - 14.0, Y + 3.0, -14.0), (ASIC_X + 14.0, Y + 4.5, 14.0), m["steel"], scene)
    bx("cage", (-4.0, Y - 1.0, -40.0), (MX0 + 2.0, Y + 14.0, 40.0), m["ph_front"], scene)
    dm = module(m, scene, "dspm", ZD, True)
    lm = module(m, scene, "lpom", ZL, False)
    yt = dm["yt"]
    host = {}
    for name, zc in (("d", ZD), ("l", ZL)):
        paths = []
        for k in range(4):
            z = zc - 8.0 + 2.2 * k
            p = [(ASIC_X + 20.0, Y + 0.05, zc * 0.4 + (k - 1.5) * 2.0), (-20.0, Y + 0.05, z), (MX0 - 4.0, Y + 0.05, z)]
            C.trace(m, scene, f"ht{name}{k}", p, w=0.5)
            paths.append(p)
        host[name] = paths
    show(scene, [(F(0, 0), F(5, 0))])

    # DSP module glow (warm die) and heat, beats 1 and 3
    warm = empty("warm", root)
    bx("dspw", (15.0, yt + 2.4, ZD - 7.0), (29.0, yt + 2.7, ZD + 7.0), m["warm"], warm)
    show(warm, [(F(1, 0.2), F(2, 0)), (F(3, 0), F(4, 0))])
    rise(root, "dsph", dm["dsp"], 10, 0.5, m["h_amber"], [1, 3], 0.1, 0.85, h=22.0, life=45, spread=(6.0, 6.0))
    rise(root, "lpoh", (40.0, yt + 1.5, ZL), 3, 0.4, m["h_amber"], [3], 0.1, 0.85, h=10.0, life=45, spread=(2.0, 2.0))

    # beat 1: bits into the DSP, out to driver, laser, fibre
    for k in range(4):
        z = ZD - 7.0 + 1.4 * k
        path = host["d"][k] + [(MX0 + 4.0, yt + 0.2, host["d"][k][-1][2]), (14.0, yt + 0.2, ZD - 3.0 + k * 2.0)]
        run(root, f"din{k}", path, 3, 0.6, m["h_amber"], [1], 0.0 + 0.03 * k, 0.4, 35)
        run(root, f"dout{k}", [(30.0, yt + 0.2, ZD - 4.5), (40.0, yt + 1.4, ZD - 4.5), (55.0, yt + 2.5, z),
                               (70.0, yt + 3.0, ZD + (z - ZD) * 0.3), (MX1 + 20.0, yt + 3.0, ZD)], 3, 0.6, m["ph_red"], [1], 0.35 + 0.03 * k, 0.75, 35)
    # beat 2: LPO straight through
    for k in range(4):
        z = ZL - 7.0 + 1.4 * k
        path = host["l"][k] + [(MX0 + 4.0, yt + 0.2, host["l"][k][-1][2]), (40.0, yt + 1.4, ZL - 4.5), (55.0, yt + 2.5, z),
                               (70.0, yt + 3.0, ZL + (z - ZL) * 0.3), (MX1 + 20.0, yt + 3.0, ZL)]
        run(root, f"lin{k}", path, 4, 0.6, m["sig"], [2, 4], 0.0 + 0.03 * k, 0.7, 55)
        zr = ZL + 2.0 + 1.4 * k
        back = [(MX1 + 20.0, yt + 3.0, ZL), (70.0, yt + 3.0, ZL + (zr - ZL) * 0.3), (56.0, yt + 2.5, zr), (40.0, yt + 1.4, ZL + 4.5),
                (MX0 + 4.0, yt + 0.2, ZL + 4.0), (-20.0, Y + 0.05, ZL + 4.0), (ASIC_X + 20.0, Y + 0.05, ZL * 0.4 + 2.0)]
        run(root, f"lback{k}", back, 3, 0.6, m["ph_cyan"], [2], 0.1 + 0.03 * k, 0.7, 55)
    # SerDes glow on the ASIC edge during beat 2
    sd = empty("serdes", root)
    bx("sdg", (ASIC_X + 18.0, Y + 3.0, -2.0), (ASIC_X + 20.0, Y + 3.4, 18.0), m["sig"], sd)
    show(sd, [(F(2, 0), F(3, 0))])

    # beat 3: power bars floating above each module
    bars = empty("bars", root)
    for name, zc, wv, mt in (("d", ZD, 15.0, "bar_r"), ("l", ZL, 8.0, "bar_g")):
        bx(f"pb{name}_bg", (90.0, Y, zc - 3.0), (93.0, Y + 30.0, zc + 3.0), m["ph_front"], bars)
        bx(f"pb{name}", (93.0, Y, zc - 2.5), (95.0, Y + 1.9 * wv, zc + 2.5), m[mt], bars)
    show(bars, [(F(3, 0.1), F(4, 0))])

    tags = {
        0: [("switch ASIC + SerDes", (ASIC_X, Y + 6.0, 0.0)), ("DSP module", (40.0, Y + 12.0, ZD)),
            ("LPO module: no DSP", (40.0, Y + 12.0, ZL))],
        1: [("DSP re-times every bit", (22.0, yt + 4.0, ZD)), ("~half the module power", (22.0, yt + 14.0, ZD - 6.0)),
            ("driver -> lasers", (48.0, yt + 3.0, ZD - 5.0))],
        2: [("host SerDes equalises", (-25.0, Y + 0.5, ZL - 6.0)), ("linear driver only", (40.0, yt + 2.5, ZL - 4.5)),
            ("linear TIA on receive", (40.0, yt + 2.5, ZL + 4.5))],
        3: [("DSP module ~15 W", (94.0, Y + 30.0, ZD)), ("LPO ~8 W", (94.0, Y + 16.0, ZL)),
            ("less heat, less latency", (40.0, yt + 10.0, ZL))],
        4: [("short reach: in-rack/row", (MX1 + 15.0, yt + 4.0, ZL)), ("whole channel must match", (-30.0, Y + 1.0, 10.0)),
            ("LRO: DSP on transmit only", (22.0, yt + 4.0, ZD))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-10.0, Y, 0.0), 200.0, 0.25, 0.60),
        frame((30.0, yt, ZD), 90.0, 0.30, 0.70),
        frame((0.0, yt, ZL - 4.0), 130.0, -0.10, 0.70),
        frame((50.0, Y + 10.0, 0.0), 130.0, 0.6, 0.35),
        frame((0.0, Y, 0.0), 220.0, -0.20, 0.55),
    ], root)


if __name__ == "__main__":
    build()
