"""TRM_COHERENT_OPTICS: the Terms-tab overview for coherent optics.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_coherent_optics.py

Writes assets/term_TRM_COHERENT_OPTICS.glb. Captions live in specs/terms/TRM_COHERENT_OPTICS.json.

Beats:
  0 dci       two data-centre halls 80 km apart, one fibre pair with an amplifier hut
  1 symbols   on/off light vs a 16QAM constellation: phase + amplitude carry 4 bits a symbol
  2 tx        the cut-open 800ZR module: laser, nested IQ modulators per polarisation, combiner
  3 rx        local-oscillator laser, 90-degree hybrid, photodiodes, DSP straightens smeared pulses
  4 market    ZR pluggables in switch ports; who sells it
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import blink, bx, frame, polyline, rise, run  # noqa: E402

import term_common as C  # noqa: E402
import kit_photonics as K  # noqa: E402

SLUG = "TRM_COHERENT_OPTICS"
BEATS = [
    ("Coherent optics link data centres tens to hundreds of km apart",
     "An AI campus often spans several buildings or sites, and they must trade data as if they were one cluster. "
     "Coherent optics send 400G to 1.6T per wavelength over a single fibre pair for 80 to 1,000+ km, with optical "
     "amplifiers every 80 km or so. Ordinary short-reach optics run out of reach after a few kilometres."),
    ("Bits ride on phase and amplitude, not just on/off",
     "A plain optic turns the light on and off: one bit per symbol. A coherent optic sets the light's phase and "
     "amplitude, so each symbol lands on one point of a grid called a constellation. 16QAM has 16 points, so 4 bits "
     "per symbol, and two polarisations double it to 8. At ~120 Gbaud that is about 1 Tb/s of raw capacity on one colour."),
    ("The transmitter: a laser and nested IQ modulators",
     "Inside the module a tunable laser feeds two nested Mach-Zehnder modulators per polarisation: one sets the in-phase "
     "part (I), the other the quadrature part (Q), 90 degrees apart. A polarisation rotator and combiner merge the X and Y "
     "streams into one fibre. The DSP's DACs drive the modulator electrodes."),
    ("The receiver: a local laser and a DSP that undoes the fibre",
     "At the far end a second laser, the local oscillator, mixes with the incoming light in a 90-degree hybrid, and "
     "balanced photodiodes read out I and Q for each polarisation. A DSP with fast ADCs then reverses chromatic "
     "dispersion and polarisation drift and applies error correction, so smeared pulses become clean symbols. That DSP "
     "is the hardest and most power-hungry chip in the module."),
    ("400ZR and 800ZR put coherent into a switch port",
     "Coherent used to need large line-card systems. 400ZR and 800ZR pluggables shrink it to a QSFP-DD or OSFP module "
     "that plugs straight into a switch, at about 15-30 W each. Ciena (CIEN) leads line systems, Marvell (MRVL) and "
     "Cisco (CSCO, via Acacia) make coherent DSPs and modules, and Coherent (COHR) and Lumentum (LITE) supply lasers "
     "and modulators."),
]

# layout: the long-haul context sits at the back (z = -120); the cut-open module on the bench at z = 0
BZ = -120.0
FY = 6.0


def hall(m, parent, name, x0, x1):
    g = empty(name, parent)
    bx(f"{name}_slab", (x0 - 4, -1.0, BZ - 26), (x1 + 4, 0.0, BZ + 18), m["ph_front"], g)
    bx(f"{name}_wall", (x0, 0.0, BZ - 22), (x1, 22.0, BZ - 20), m["ph_case"], g)
    for k in range(4):  # rack rows with blinking status lights
        z = BZ - 14 + 7 * k
        bx(f"{name}_r{k}", (x0 + 3, 0.0, z - 2.2), (x1 - 3, 16.0, z + 2.2), m["ph_dsp"], g)
        for j in range(6):
            x = x0 + 6 + (x1 - x0 - 12) * j / 5
            led = bx(f"{name}_l{k}_{j}", (x - 0.6, 12.0, z + 2.2), (x + 0.6, 13.0, z + 2.6), m["ph_green"], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)

    # ---- beat 0 (and 4): the long-haul link ----
    ctx = empty("ctx", root)
    hall(m, ctx, "hA", -200.0, -150.0)
    hall(m, ctx, "hB", 150.0, 200.0)
    swa = K.switch_panel(m, ctx, "swA", -146.0, -126.0, 2.0, 14.0, BZ + 4, cols=4, rows=2)
    swb = K.switch_panel(m, ctx, "swB", 126.0, 146.0, 2.0, 14.0, BZ + 4, cols=4, rows=2)
    # buried fibre with a coil every so often, amplifier hut in the middle
    span = [(-130.0, FY, BZ + 6), (-80.0, FY, BZ + 6), (-20.0, FY, BZ + 6)]
    span2 = [(20.0, FY, BZ + 6), (80.0, FY, BZ + 6), (130.0, FY, BZ + 6)]
    K.fiber(m, ctx, "spanA", span, r=0.8)
    K.fiber(m, ctx, "spanB", span2, r=0.8)
    for k, cx in enumerate((-80.0, 80.0)):  # coiled spools = kilometres of glass
        for j in range(5):
            a = [(cx - 6 + 6 * math.cos(2 * math.pi * i / 16), FY + 6 * math.sin(2 * math.pi * i / 16) + 6.0, BZ + 6 + j * 0.9)
                 for i in range(17)]
            K.fiber(m, ctx, f"coil{k}_{j}", a, r=0.35)
    bx("hut", (-20.0, 0.0, BZ - 4), (20.0, 16.0, BZ + 14), m["ph_case"], ctx)
    bx("hut_roof", (-22.0, 16.0, BZ - 6), (22.0, 18.0, BZ + 16), m["steel"], ctx)
    edfa = bx("edfa", (-12.0, 4.0, BZ + 14), (12.0, 10.0, BZ + 15), m["ph_amber"], ctx)
    bx("ground", (-210.0, -2.0, BZ - 30), (210.0, -1.0, BZ + 24), m["ph_pcb"], ctx)
    show(ctx, [(F(0, 0), F(1, 0)), (F(4, 0), F(5, 0))])
    full = span + [(0.0, FY, BZ + 16), (0.0, FY, BZ + 16)] + span2
    run(root, "haul", full, 10, 1.6, m["ph_c4"], [0, 4], 0.0, 0.75, 70)
    run(root, "haul2", list(reversed(full)), 6, 1.6, m["ph_c6"], [0], 0.1, 0.75, 70)

    # ---- beat 1: intensity vs constellation ----
    sym = empty("sym", root)
    # left: an on/off lane, a beam that blinks
    bx("ook_base", (-70.0, -1.0, BZ + 30), (-20.0, 0.0, BZ + 50), m["ph_front"], sym)
    K.laser(m, sym, "ook_las", (-64.0, 0.0, BZ + 40), "ph_red", size=3.0)
    K.fiber(m, sym, "ook_f", [(-60.0, 2.0, BZ + 40), (-22.0, 2.0, BZ + 40)], r=0.5)
    for k in range(8):
        on = empty(f"ook_on{k}", sym)
        bx(f"ook_b{k}", (-56.0 + 4.4 * k, 1.0, BZ + 38.5), (-53.0 + 4.4 * k, 3.0, BZ + 41.5), m["ph_red"], on)
        if k in (0, 2, 3, 6):
            blink(on, 1, [k, (k + 3) % 8], n=8, on=0.9)
        else:
            show(on, [])
    # right: a 16QAM constellation plate standing up, I/Q axes
    qc = (45.0, 22.0, BZ + 40)
    bx("iq_plate", (qc[0] - 22, qc[1] - 22, qc[2] - 1.0), (qc[0] + 22, qc[1] + 22, qc[2]), m["ph_dsp"], sym)
    polyline("iq_i", [(qc[0] - 20, qc[1], qc[2] + 0.3), (qc[0] + 20, qc[1], qc[2] + 0.3)], 0.25, m["steel"], sym)
    polyline("iq_q", [(qc[0], qc[1] - 20, qc[2] + 0.3), (qc[0], qc[1] + 20, qc[2] + 0.3)], 0.25, m["steel"], sym)
    pts = []
    for i, a in enumerate((-15, -5, 5, 15)):
        for j, b in enumerate((-15, -5, 5, 15)):
            pts.append((qc[0] + a, qc[1] + b))
            bx(f"iq_d{i}{j}", (qc[0] + a - 1.0, qc[1] + b - 1.0, qc[2]), (qc[0] + a + 1.0, qc[1] + b + 1.0, qc[2] + 0.6),
               m["dim_glow"], sym)
    for k, (px, py) in enumerate(pts):
        hot = empty(f"iq_hot{k}", sym)
        bx(f"iq_h{k}", (px - 1.6, py - 1.6, qc[2] + 0.6), (px + 1.6, py + 1.6, qc[2] + 1.4), m["ph_c4"], hot)
        blink(hot, 1, [(k * 7) % 16], n=16, on=0.95)
    # a phasor arm sweeping from the origin
    arm = empty("iq_arm", sym)
    polyline("iq_armw", [(qc[0], qc[1], qc[2] + 1.0), (qc[0] + 15, qc[1] + 5, qc[2] + 1.0)], 0.4, m["ph_amber"], arm)
    show(sym, [(F(1, 0), F(2, 0))])

    # ---- beats 2-3: the cut-open module on the bench ----
    mod = empty("mod", root)
    K.pcb(m, mod, "mpcb", -95.0, 95.0, -30.0, 30.0, y=-1.6)
    K.module(m, mod, "case", (0.0, 0.0, 0.0), 196.0, 10.0, 64.0, cut=True)
    # the DSP at the electrical end with its heat
    dsp = K.dsp(m, mod, "dsp", (-62.0, 0.0, 0.0), 34.0, 34.0, h=4.0)
    bx("dsp_lid", (-76.0, 4.0, -14.0), (-48.0, 5.0, 14.0), m["ph_gold"], mod)
    for k in range(10):  # edge fingers
        bx(f"finger{k}", (-98.0, -1.0, -22 + 4.6 * k), (-92.0, 0.0, -20 + 4.6 * k), m["ph_gold"], mod)
    # TX photonic die (front, z > 0) and RX die (back, z < 0)
    K.pic(m, mod, "txpic", -30.0, 80.0, 2.0, 28.0, y=0.0)
    K.pic(m, mod, "rxpic", -30.0, 80.0, -28.0, -2.0, y=0.0)
    Y = 4.0
    las = K.laser(m, mod, "txlas", (-24.0, Y, 15.0), "ph_red", size=3.0)
    # split to X and Y polarisations, each with nested I/Q MZMs
    iq = {}
    for pol, zc in (("X", 22.0), ("Y", 8.0)):
        for part, dz in (("I", 2.6), ("Q", -2.6)):
            iq[pol + part] = K.mzm(m, mod, f"mz{pol}{part}", 22.0, zc + dz, 34.0, 1.6, Y)
    K.wg(m, mod, "tx_split", [(-20.0, Y + 1, 15.0), (-6.0, Y + 1, 15.0), (-6.0, Y + 1, 22.0), (-1.0, Y + 1, 22.0)])
    K.wg(m, mod, "tx_split2", [(-6.0, Y + 1, 15.0), (-6.0, Y + 1, 8.0), (-1.0, Y + 1, 8.0)])
    rot = bx("polrot", (48.0, Y, 5.0), (54.0, Y + 2.5, 11.0), m["ph_ln"], mod)
    pbc = bx("pbc", (60.0, Y, 10.0), (68.0, Y + 3.0, 20.0), m["ph_wg"], mod)
    K.wg(m, mod, "tx_comb", [(45.0, Y + 1, 22.0), (60.0, Y + 1, 18.0)])
    K.wg(m, mod, "tx_combY", [(45.0, Y + 1, 8.0), (60.0, Y + 1, 12.0)])
    K.fiber(m, mod, "txfib", [(68.0, Y + 1, 15.0), (100.0, Y + 1, 15.0), (130.0, Y + 1, 15.0)], r=0.6)
    # DAC drive traces from the DSP to the electrodes
    for k, (key_, zz) in enumerate((("XI", 24.6), ("XQ", 19.4), ("YI", 10.6), ("YQ", 5.4))):
        polyline(f"drv{k}", [(-45.0, 4.5, 6.0 + 4 * k), (0.0, Y + 1.5, zz), (8.0, Y + 1.5, zz)], 0.3, m["ph_gold"], mod)
    # RX: incoming fibre, local oscillator, hybrid, photodiodes
    K.fiber(m, mod, "rxfib", [(130.0, Y + 1, -15.0), (100.0, Y + 1, -15.0), (60.0, Y + 1, -15.0)], r=0.6)
    lo = K.laser(m, mod, "lolas", (62.0, Y, -24.0), "ph_violet", size=2.4)
    hyb = bx("hybrid", (20.0, Y, -24.0), (48.0, Y + 2.0, -6.0), m["ph_wg"], mod)
    for k in range(6):  # interferometer stripes in the hybrid
        polyline(f"hyb_s{k}", [(22.0, Y + 2.2, -22.0 + 3 * k), (46.0, Y + 2.2, -8.0 - 2 * k)], 0.25, m["ph_oxide"], mod)
    K.wg(m, mod, "rx_in", [(60.0, Y + 1, -15.0), (48.0, Y + 1, -15.0)])
    K.wg(m, mod, "lo_in", [(58.0, Y + 1, -24.0), (52.0, Y + 1, -24.0), (48.0, Y + 1, -20.0)])
    pds = []
    for k in range(8):
        zk = -25.0 + 2.8 * k
        bx(f"pd{k}", (6.0, Y, zk - 1.0), (12.0, Y + 2.0, zk + 1.0), m["ph_gold"], mod)
        K.wg(m, mod, f"pdw{k}", [(20.0, Y + 1, -15.0 + (k - 3.5) * 1.6), (12.0, Y + 1, zk)], 0.35)
        pds.append((9.0, Y + 2.0, zk))
        polyline(f"tia{k}", [(6.0, Y + 1, zk), (-45.0, 4.5, -6.0 - 1.2 * k)], 0.25, m["ph_gold"], mod)
    show(mod, [(F(2, 0), F(4, 0))])

    # TX light: laser -> split -> four MZMs -> combiner -> fibre
    for pol, zc, col in (("X", 22.0, "ph_c0"), ("Y", 8.0, "ph_c5")):
        for part in ("I", "Q"):
            arm_ = iq[pol + part]["arms"][1 if part == "I" else -1]
            path = [(-20.0, Y + 1.6, 15.0), (-6.0, Y + 1.6, 15.0), (-6.0, Y + 1.6, zc)] + \
                [(x, Y + 1.6, z) for (x, _, z) in arm_[::4]] + [(45.0, Y + 1.6, zc), (60.0, Y + 1.6, 15.0), (100.0, Y + 1.6, 15.0)]
            run(root, f"tx{pol}{part}", path, 4, 1.0, m[col], [2], 0.0, 0.7, 55)
    run(root, "drive", [(-45.0, 5.5, 12.0), (0.0, Y + 2.0, 15.0)], 6, 0.7, m["h_amber"], [2], 0.0, 0.8, 25)
    # RX: smeared signal in, LO mixes, eight photodiode lanes back to the DSP
    run(root, "rxin", [(130.0, Y + 1.6, -15.0), (48.0, Y + 1.6, -15.0), (34.0, Y + 1.6, -15.0)], 6, 1.4, m["ph_c4"], [3], 0.0, 0.5, 40)
    run(root, "loin", [(58.0, Y + 1.6, -24.0), (48.0, Y + 1.6, -20.0), (34.0, Y + 1.6, -15.0)], 5, 1.0, m["ph_violet"], [3], 0.0, 0.5, 30)
    for k, p in enumerate(pds):
        run(root, f"pdo{k}", [(20.0, Y + 1.6, -15.0 + (k - 3.5) * 1.6), p, (-45.0, 5.5, -6.0 - 1.2 * k)], 2, 0.6, m["sig"], [3], 0.3, 0.8, 30)
    rise(root, "dspheat", (-62.0, 5.5, 0.0), 10, 0.8, m["h_amber"], [3], spread=(10.0, 10.0), h=24.0)
    # smeared vs clean pulses above the DSP: a before/after strip
    pul = empty("pulses", root)
    for k in range(6):
        x = 20.0 + 9 * k
        bx(f"smear{k}", (x - 3.5, 16.0, -40.0), (x + 3.5, 18.0 + (k % 3), -39.0), m["dim_glow"], pul)
        bx(f"clean{k}", (-100.0 + 9 * k - 1.0, 16.0, -40.0), (-100.0 + 9 * k + 1.0, 24.0, -39.0), m["ph_c4"], pul)
    polyline("p_arrow", [(14.0, 20.0, -39.5), (-44.0, 20.0, -39.5)], 0.35, m["steel"], pul)
    show(pul, [(F(3, 0.2), F(4, 0))])

    # ---- beat 4: pluggables in a switch ----
    sw = empty("sw", root)
    bx("sw_box", (-60.0, 30.0, BZ + 30), (60.0, 46.0, BZ + 60), m["ph_case"], sw)
    for k in range(8):
        x = -52.0 + 14.8 * k
        bx(f"zr{k}", (x - 5.0, 33.0, BZ + 60), (x + 5.0, 39.0, BZ + 74), m["steel"] if k % 2 else m["ph_front"], sw)
        bx(f"zrl{k}", (x - 1.0, 40.0, BZ + 60.2), (x + 1.0, 41.4, BZ + 60.8), m["ph_green"], sw)
    show(sw, [(F(4, 0), F(5, 0))])

    C.tags(root, {
        0: [("data hall A", (-175.0, 26.0, BZ - 10)), ("data hall B", (175.0, 26.0, BZ - 10)),
            ("80+ km of fibre", (-80.0, 20.0, BZ + 6)), ("amplifier hut (EDFA)", (0.0, 22.0, BZ + 6))],
        1: [("on/off: 1 bit/symbol", (-45.0, 8.0, BZ + 40)), ("16QAM: 4 bits/symbol", (45.0, 46.0, BZ + 40)),
            ("I axis", (qc[0] + 20, qc[1] + 2, qc[2])), ("Q axis", (qc[0] + 2, qc[1] + 20, qc[2]))],
        2: [("tunable laser", (-24.0, 10.0, 15.0)), ("nested I/Q modulators", (22.0, 10.0, 22.0)),
            ("pol. rotator + combiner", (60.0, 10.0, 12.0)), ("DSP drives via DACs", (-62.0, 10.0, 8.0))],
        3: [("local oscillator laser", (62.0, 10.0, -24.0)), ("90-degree hybrid", (34.0, 10.0, -15.0)),
            ("balanced photodiodes", (9.0, 10.0, -20.0)), ("DSP undoes dispersion", (-62.0, 12.0, -8.0)),
            ("smeared -> clean", (-15.0, 28.0, -40.0))],
        4: [("800ZR pluggables", (0.0, 44.0, BZ + 70)), ("~15-30 W per module", (40.0, 50.0, BZ + 45)),
            ("straight onto the long fibre", (60.0, 16.0, BZ + 6))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 8.0, BZ), 340.0, 0.15, 0.45, pad=1.0),
        frame((0.0, 18.0, BZ + 40), 140.0, 0.10, 0.20),
        [(0.0, frame((20.0, 4.0, 10.0), 200.0, 0.20, 0.60)), (0.5, frame((20.0, 4.0, 14.0), 110.0, 0.30, 0.70))],
        [(0.0, frame((10.0, 4.0, -15.0), 130.0, -0.25, 0.75)), (0.55, frame((-20.0, 10.0, -20.0), 180.0, -0.15, 0.55))],
        frame((0.0, 25.0, BZ + 40), 300.0, 0.25, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
