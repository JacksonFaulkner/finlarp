"""CHIP page for PLANAR: the overview (the whole chip, then the camera glides in on the planar NMOS),
five zoom-ins a-e, and ten numbered sections. The gate lies flat on the channel and controls it from
one side only; as the channel shortens the drain's field reaches the source and current leaks past
the gate, in the off state.

Run from the repo root (all scenes, or name some after `--`):
    blender -b --factory-startup --python tools/pbr3d/blender/chip_planar.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_planar.py -- zoom_a sec4

Writes assets/chip_planar.glb (overview), assets/chip_planar_zoom_<key>.glb and
assets/chip_planar_sec<N>.glb, plus a .blend next to each. One beat is 8 s.

Overview beats:
  0 whole    the whole chip, the planar NMOS lit
  1 close    glide in: gate, oxide, source, drain, channel, body
  2 on       gate high: the channel forms under the gate and carries current
  3 shrink   the channel is short: drain and source depletion fields reach toward each other
  4 leak     gate low (off), yet dots slip under the gate through the body
  5 whole    back out, all of it again

Zoom-ins (3 beats each): a the four leakage paths, b short channels and DIBL, c high-k metal gate,
d FD-SOI and body bias, e Dennard scaling and its end.

Sections (3 beats each, 4 for the sources): 1 the planar era, 2 the cross-section, 3 short channels
(as zoom b), 4 strain and high-k metal gate, 5 mature nodes, 6 Dennard arithmetic (as zoom e),
7 FD-SOI (as zoom d), 8 who makes it, 9 chokepoints, 10 sources.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, box, glide_camera, label, mat, overlay, pivot, route, scale_keys, show, stream_of  # noqa: E402
from chip_kit import transistor  # noqa: E402

BEATS = 6
CX = C.NMOS_X
GATE_ON = [(F(2, 0.10), F(3, 0.0))]
ZD = 24.0  # the dot streams run just in front of the cut face, so they read over the silicon
THIN = 0.001  # a scale this small reads as hidden (not zero: the exporter divides by parent scale)

NEAR = ((CX, -10.0, 0.0), 1400.0, 0.0, 0.10)
POSES = [C.WHOLE, NEAR, ((CX, -10.0, 0.0), 1350.0, 0.0, 0.10), ((CX, -30.0, 0.0), 1400.0, 0.0, 0.10),
         ((CX, -40.0, 0.0), 1400.0, 0.0, 0.10), C.WHOLE]


def span(a, b):
    """The interval from the start of beat a to the start of beat b; a and b are beats or (beat, u)."""
    a = a if isinstance(a, tuple) else (a, 0)
    b = b if isinstance(b, tuple) else (b, 0)
    return [(F(a[0], a[1]), F(b[0], b[1]))]


def base(name, beats, gate=()):
    """A fresh scene with the whole chip (chip_kit) and this node's extra materials."""
    m, root = start(name, beats, page="chip")
    C.mats(m)
    m["dep"] = mat("chip_planar_dep", (1.0, 0.45, 0.35), emit=(1.0, 0.40, 0.30), strength=1.2, alpha=0.30)
    m["leak"] = mat("chip_planar_leak", (1.0, 0.35, 0.30), emit=(1.0, 0.30, 0.25), strength=4.0)
    m["tunnel"] = mat("chip_planar_tunnel", (1.0, 0.50, 0.75), emit=(1.0, 0.45, 0.70), strength=4.0)
    m["poly"] = mat("chip_planar_poly", (0.48, 0.30, 0.18), rough=0.7)
    m["hik_thick"] = mat("chip_planar_hik_thick", (0.70, 0.92, 1.0), emit=(0.55, 0.88, 1.0), strength=1.0, alpha=0.40)
    m["box"] = mat("chip_planar_box", (0.85, 0.92, 1.0), emit=(0.80, 0.90, 1.0), strength=1.0, alpha=0.45)
    m["bias"] = mat("chip_planar_bias", (0.75, 0.60, 1.0), emit=(0.70, 0.50, 1.0), strength=1.2, alpha=0.40)
    m["sige"] = mat("chip_planar_sige", (0.95, 0.70, 0.35), emit=(1.0, 0.65, 0.30), strength=1.5, alpha=0.45)
    m["nitride"] = mat("chip_planar_nitride", (0.45, 0.85, 0.70), emit=(0.40, 0.85, 0.65), strength=1.5, alpha=0.40)
    parts = C.chip(root, m, gate=gate)
    return m, root, parts


def channel_leak(root, m, name, n, b, u0, u1, life=90):
    """Carriers from drain to source across the channel, at the surface (below threshold)."""
    s, p = route([(CX + C.SD, -10.0, ZD), (CX - C.SD, -10.0, ZD)])
    stream_of(root, name, n, s, p, 30, m["leak"], b, u0, u1, life)


def under_leak(root, m, name, n, b, u0, u1, life=90):
    """Carriers from drain to source, dipping under the gate through the body."""
    s, p = route([(CX + C.SD, -40.0, ZD), (CX, -200.0, ZD), (CX - C.SD, -40.0, ZD)])
    stream_of(root, name, n, s, p, 30, m["leak"], b, u0, u1, life)


def depletion(root, m, grow, prefix="dep"):
    """Two depletion bands, one from each n+ junction toward the other, scaled in x by `grow`."""
    for name, sgn in ((prefix + "_d", 1), (prefix + "_s", -1)):
        pv = pivot(name, (CX + sgn * 120.0, 0.0, 0.0), root)
        x_far = -sgn * 300.0
        lo = (min(0.0, x_far), -150.0, -232.0)  # local to the pivot, so the box grows along x
        hi = (max(0.0, x_far), -4.0, 8.0)
        box(name + "_b", lo, hi, m["dep"], pv)
        scale_keys(pv, grow)


# ---- overview -------------------------------------------------------------------------------


def build():
    m, root, _ = base("planar", BEATS, gate=GATE_ON)

    # beats 0 and 5: the planar NMOS lit
    C.overlay(root, "pick", (CX - 330, -120, -250), (CX + 330, 150, 12), m["c_lit_thin"],
              [(F(0, 0), F(1, 0)), (F(5, 0.3), F(6, 0))])

    # depletion fields: each grows from its junction toward the other, in beat 3, until they meet
    # under the channel; they stay through beat 4 and fade out as the camera backs out in beat 5
    for name, sgn in (("dep_d", 1), ("dep_s", -1)):
        pv = pivot(name, (CX + sgn * 120.0, 0.0, 0.0), root)
        x_far = -sgn * 300.0
        lo = (min(0.0, x_far), -150.0, -232.0)  # local to the pivot, so the box grows along x
        hi = (max(0.0, x_far), -4.0, 8.0)
        box(name + "_b", lo, hi, m["dep"], pv)
        scale_keys(pv, [(F(0, 0), (THIN, 1, 1)), (F(3, 0.0), (THIN, 1, 1)), (F(3, 0.45), (0.35, 1, 1)),
                        (F(3, 0.90), (1, 1, 1)), (F(5, 0.0), (1, 1, 1)), (F(5, 0.25), (THIN, 1, 1))])

    # on: electrons source -> drain along the surface of the channel
    s, p = route([(CX - C.SD, -10.0, ZD), (CX + C.SD, -10.0, ZD)])
    stream_of(root, "on", 10, s, p, 34, m["c_dot_sig"], 2, 0.15, 0.65, 80)
    # off: leakage from drain to source, dipping under the gate into the body
    s, p = route([(CX + 190, -40.0, ZD), (CX + 60, -95.0, ZD), (CX - 60, -95.0, ZD), (CX - 190, -40.0, ZD)])
    stream_of(root, "leak", 12, s, p, 34, m["leak"], 4, 0.05, 0.85, 90)

    label("planar NMOS", (CX, -170.0, 0), root, [(F(0, 0), F(2, 0)), (F(5, 0.3), F(6, 0))])
    label("silicon substrate", (0.0, -230.0, 0), root, [(F(0, 0), F(1, 0)), (F(5, 0.3), F(6, 0))])
    label("PMOS", (C.PMOS_X, -150.0, 0), root, [(F(0, 0), F(1, 0)), (F(5, 0.3), F(6, 0))])
    label("gate", (CX, 140.0, 0), root, span(1, 5))
    label("gate oxide", (CX - 100.0, 20.0, 0), root, span(1, 2))
    label("source n+", (CX - 190.0, -130.0, 0), root, span(1, 5))
    label("drain n+", (CX + 190.0, -130.0, 0), root, span(1, 5))
    label("flat channel", (CX, -10.0, 0), root, span(1, 3))
    label("p-type body", (CX + 290.0, -230.0, 0), root, span(1, 5))
    label("gate high: one side only", (CX, 215.0, 0), root, span((2, 0.10), 3))
    label("current", (CX, 60.0, 0), root, span((2, 0.25), 3))
    label("depletion fields meet", (CX, -200.0, 0), root, span((3, 0.35), 4))
    label("gate low: off", (CX, 215.0, 0), root, span((4, 0.0), (5, 0.3)))
    label("leakage under the gate", (CX, -250.0, 0), root, span((4, 0.1), (5, 0.3)))

    glide_camera(root, POSES)
    finish("planar", page="chip")


# ---- zoom-ins a-e ------------------------------------------------------------------------------


def zoom_a(name="planar_zoom_a"):
    """a: the four leakage paths (subthreshold, tunnelling, punch-through and junction leakage)."""
    m, root, _ = base(name, 3)
    label("planar NMOS", (CX, -170.0, 0), root, span(0, 3))
    channel_leak(root, m, "sub", 6, 0, 0.10, 0.80)
    label("subthreshold leak", (CX, -60.0, 0), root, span(0, 1))
    overlay(root, "oxide_lit", (CX - C.GATE_HALF - 8, -4, -246), (CX + C.GATE_HALF + 8, 22, 6),
            m["c_lit_mid"], span(1, 2))
    s, p = route([(CX - 40, -6.0, ZD), (CX - 40, 70.0, ZD)])
    stream_of(root, "tun", 6, s, p, 30, m["tunnel"], 1, 0.10, 0.80, 70)
    label("gate tunnelling", (CX - 150.0, 40.0, 0), root, span(1, 2))
    under_leak(root, m, "punch", 10, 2, 0.10, 0.80)
    label("punch-through", (CX, -215.0, 0), root, span(2, 3))
    label("junction leakage (GIDL)", (CX + 260.0, -150.0, 0), root, span(2, 3))
    glide_camera(root, [NEAR, ((CX - 40, 30, 0), 800, 0, 0.10), ((CX, -120, 0), 1100, 0, 0.10)])
    finish(name, page="chip")


def _short_channel(name):
    """b and section 3: the depletion fields reach under the gate, DIBL, then the swing floor."""
    m, root, _ = base(name, 3)
    depletion(root, m, [(F(0, 0.05), (THIN, 1, 1)), (F(0, 0.85), (1, 1, 1))])
    label("short gate", (CX, 215.0, 0), root, span(0, 1))
    under_leak(root, m, "dibl", 12, 1, 0.10, 0.80)
    label("drain up, Vt down", (CX + 260.0, -150.0, 0), root, span(1, 2))
    channel_leak(root, m, "floor", 8, 2, 0.10, 0.80)
    label("60 mV per decade", (CX, -250.0, 0), root, span(2, 3))
    glide_camera(root, [((CX, -10, 0), 1200, 0, 0.10), ((CX, -30, 0), 1000, 0, 0.10),
                        ((CX, -60, 0), 1100, 0, 0.10)])
    finish(name, page="chip")


def zoom_b():
    _short_channel("planar_zoom_b")


def _poly_to_metal(name):
    """c and section 4: polysilicon on SiON, then HfO2 under it, then the metal gate sets Vt."""
    m, root, _ = base(name, 3)
    overlay(root, "poly_gate", (CX - C.GATE_HALF - 6, 12, -244), (CX + C.GATE_HALF + 6, 124, 6),
            m["poly"], span(0, 2))
    label("polysilicon gate", (CX, 150.0, 0), root, span(0, 2))
    label("SiON: thin oxide", (CX - 150.0, 0.0, 0), root, span(0, 1))
    overlay(root, "hik_thick", (CX - C.GATE_HALF - 14, -8, -244), (CX + C.GATE_HALF + 14, 34, 6),
            m["hik_thick"], span(1, 3))
    label("HfO2: thicker film", (CX - 150.0, 40.0, 0), root, span(1, 2))
    overlay(root, "metal_lit", (CX - C.GATE_HALF - 6, 14, -246), (CX + C.GATE_HALF + 6, 126, 6),
            m["c_gate_on"], span(2, 3))
    label("metal gate sets Vt", (CX, 150.0, 0), root, span(2, 3))
    glide_camera(root, [((CX, 60, 0), 700, 0, 0.10), ((CX, 30, 0), 600, 0.10, 0.10),
                        ((CX, 60, 0), 700, 0, 0.10)])
    finish(name, page="chip")


def zoom_c():
    _poly_to_metal("planar_zoom_c")


def _fdsoi(name):
    """d and section 7: bulk depletion reaches deep, FD-SOI's buried oxide, body bias under it."""
    m, root, _ = base(name, 3)
    overlay(root, "deep_dep", (CX - 300, -230, -240), (CX + 300, -4, 4), m["dep"], span(0, 1))
    under_leak(root, m, "deep", 10, 0, 0.10, 0.70)
    label("bulk: depletion reaches deep", (CX, -250.0, 0), root, span(0, 1))
    overlay(root, "box_layer", (-C.HALF, -150, -240), (C.HALF, -130, 4), m["box"], span(1, 3))
    label("buried oxide (BOX)", (-500.0, -140.0, 0), root, span(1, 3))
    label("thin silicon film", (0.0, -110.0, 0), root, span(1, 2))
    overlay(root, "bias_lit", (-C.HALF, -300, -240), (C.HALF, -150, 4), m["bias"], span(2, 3))
    label("back bias: tunes Vt", (0.0, -260.0, 0), root, span(2, 3))
    glide_camera(root, [((CX, -120, 0), 1100, 0, 0.10), ((CX, -120, 0), 1000, 0, 0.10),
                        ((CX, -200, 0), 1300, 0, 0.10)])
    finish(name, page="chip")


def zoom_d():
    _fdsoi("planar_zoom_d")


def _dennard(name):
    """e and section 6: one node shrinks the device by 1/k, then the leakage wall."""
    m, root, parts = base(name, 3)
    show(parts["nmos"], [])  # the scaled copy below stands in for the chip's own NMOS
    pv = pivot("nmos_k", (CX, 0.0, 0.0), root)
    transistor(pv, m, 0.0, True)
    scale_keys(pv, [(F(0, 0), 1.0), (F(1, 0.3), 1.0), (F(1, 0.9), 0.7), (F(2, 0), 0.7)])
    s, p = route([(CX - C.SD, -10.0, ZD), (CX + C.SD, -10.0, ZD)])
    stream_of(root, "on", 10, s, p, 30, m["c_dot_sig"], 0, 0.15, 0.65, 80)
    label("one node: x 1/k", (CX, 215.0, 0), root, span(0, 1))
    label("shrink: power per gate x 1/k^2", (CX, 215.0, 0), root, span(1, 2))
    under_leak(root, m, "wall", 12, 2, 0.10, 0.80)
    label("leakage wall: Vdd near 1 V", (CX, -250.0, 0), root, span(2, 3))
    glide_camera(root, [NEAR, NEAR, NEAR])
    finish(name, page="chip")


def zoom_e():
    _dennard("planar_zoom_e")


# ---- sections 1-10 ----------------------------------------------------------------------------


def sec1():
    """1: free scaling, the leakage wall, the planar NMOS still made at 22/28 nm and up."""
    m, root, _ = base("planar_sec1", 3)
    label("free scaling: speed up, power flat", (0.0, 1650.0, 0), root, span(0, 1))
    under_leak(root, m, "wall", 12, 1, 0.10, 0.80)
    label("leakage wall, ~2005", (CX, 215.0, 0), root, span(1, 2))
    C.overlay(root, "pick", (CX - 330, -120, -250), (CX + 330, 150, 12), m["c_lit_thin"], span(2, 3))
    label("planar NMOS: still made at 28 nm", (0.0, 1650.0, 0), root, span(2, 3))
    glide_camera(root, [C.WHOLE, NEAR, C.WHOLE])
    finish("planar_sec1", page="chip")


def sec2():
    """2: the cross-section conducting, off, then the four leak paths."""
    m, root, _ = base("planar_sec2", 3, gate=[(F(0, 0), F(1, 0))])
    s, p = route([(CX - C.SD, -10.0, ZD), (CX + C.SD, -10.0, ZD)])
    stream_of(root, "on", 10, s, p, 30, m["c_dot_sig"], 0, 0.15, 0.65, 80)
    label("source n+", (CX - 190.0, -130.0, 0), root, span(0, 3))
    label("drain n+", (CX + 190.0, -130.0, 0), root, span(0, 3))
    label("gate on", (CX, 215.0, 0), root, span(0, 1))
    label("gate low: no channel", (CX, 215.0, 0), root, span(1, 2))
    channel_leak(root, m, "sub", 6, 2, 0.10, 0.80)
    under_leak(root, m, "arc", 10, 2, 0.10, 0.80)
    label("four leak paths", (CX, -250.0, 0), root, span(2, 3))
    glide_camera(root, [NEAR, NEAR, NEAR])
    finish("planar_sec2", page="chip")


def sec3():
    _short_channel("planar_sec3")


def sec4():
    """4: strained silicon, then the HfO2 dielectric, then the metal gate."""
    m, root, _ = base("planar_sec4", 3)
    overlay(root, "sige_p", (C.PMOS_X - C.SD - 80, -96, -246), (C.PMOS_X + C.SD + 80, 12, 6), m["sige"], span(0, 1))
    overlay(root, "nitride_n", (CX - C.SD - 80, -96, -246), (CX + C.SD + 80, 12, 6), m["nitride"], span(0, 1))
    label("SiGe: PMOS squeezed", (C.PMOS_X, -150.0, 0), root, span(0, 1))
    label("nitride cap: NMOS stretched", (CX, -150.0, 0), root, span(0, 1))
    overlay(root, "hik_thick", (CX - C.GATE_HALF - 14, -8, -244), (CX + C.GATE_HALF + 14, 34, 6),
            m["hik_thick"], span(1, 2))
    label("HfO2 replaces SiON", (CX - 150.0, 40.0, 0), root, span(1, 2))
    overlay(root, "metal_lit", (CX - C.GATE_HALF - 6, 14, -246), (CX + C.GATE_HALF + 6, 126, 6),
            m["c_gate_on"], span(2, 3))
    label("metal gate sets Vt", (CX, 150.0, 0), root, span(2, 3))
    glide_camera(root, [((0.0, -90, 0), 3000, 0, 0.10), ((CX, 40, 0), 700, 0, 0.10),
                        ((CX, 60, 0), 700, 0, 0.10)])
    finish("planar_sec4", page="chip")


def sec5():
    """5: mature nodes (planar still shipping), the FD-SOI wafers of UMC and GF, SMIC."""
    m, root, _ = base("planar_sec5", 3)
    C.overlay(root, "pick", (CX - 330, -120, -250), (CX + 330, 150, 12), m["c_lit_thin"], span(0, 3))
    label("28 nm and above: 36% of foundry revenue", (0.0, 1650.0, 0), root, span(0, 1))
    overlay(root, "box_layer", (-C.HALF, -150, -240), (C.HALF, -130, 4), m["box"], span(1, 2))
    label("UMC, GF: 22/28 nm, FDX", (-500.0, -140.0, 0), root, span(1, 2))
    label("SMIC: mostly 28 nm and above", (0.0, 1650.0, 0), root, span(2, 3))
    glide_camera(root, [C.WHOLE, ((CX, -120, 0), 1400, 0, 0.10), C.WHOLE])
    finish("planar_sec5", page="chip")


def sec6():
    _dennard("planar_sec6")


def sec7():
    _fdsoi("planar_sec7")


def sec8():
    """8: who makes it: TSMC and Intel, the mature foundries, Soitec's SOI wafers."""
    m, root, _ = base("planar_sec8", 3)
    C.overlay(root, "pick", (CX - 330, -120, -250), (CX + 330, 150, 12), m["c_lit_thin"], span(0, 3))
    label("TSMC, Intel: 28 nm, first FinFET", (0.0, 1650.0, 0), root, span(0, 1))
    label("UMC, GF, SMIC: mature nodes", (0.0, 1650.0, 0), root, span(1, 2))
    overlay(root, "box_layer", (-C.HALF, -150, -240), (C.HALF, -130, 4), m["box"], span(2, 3))
    label("Soitec: SOI wafers", (-500.0, -140.0, 0), root, span(2, 3))
    glide_camera(root, [C.WHOLE, C.WHOLE, ((CX, -120, 0), 1400, 0, 0.10)])
    finish("planar_sec8", page="chip")


def sec9():
    """9: overcapacity, FD-SOI stays niche, node names are not gate lengths."""
    m, root, _ = base("planar_sec9", 3)
    label("overcapacity: price pressure", (0.0, 1650.0, 0), root, span(0, 1))
    overlay(root, "box_layer", (-C.HALF, -150, -240), (C.HALF, -130, 4), m["box"], span(1, 2))
    label("FD-SOI: IoT, RF, auto", (-500.0, -140.0, 0), root, span(1, 2))
    depletion(root, m, [(F(2, 0), (1, 1, 1))])
    label("node names: not gate lengths", (CX, 215.0, 0), root, span(2, 3))
    glide_camera(root, [C.WHOLE, ((CX, -120, 0), 1400, 0, 0.10), ((CX, -10, 0), 1200, 0, 0.10)])
    finish("planar_sec9", page="chip")


def sec10():
    """10: sources, a slow pull-back from the planar NMOS to the whole chip."""
    m, root, _ = base("planar_sec10", 4)
    label("sources: the cards on the page", (0.0, 1650.0, 0), root, span(0, 4))
    glide_camera(root, [((0.0, 620, 0), 3200, 0.10, 0.10), ((0.0, 620, 0), 4200, 0.05, 0.10),
                        ((0.0, 620, 0), 5000, 0.0, 0.10), C.WHOLE])
    finish("planar_sec10", page="chip")


SCENES = {
    "zoom_a": zoom_a, "zoom_b": zoom_b, "zoom_c": zoom_c, "zoom_d": zoom_d, "zoom_e": zoom_e,
    "sec1": sec1, "sec2": sec2, "sec3": sec3, "sec4": sec4, "sec5": sec5,
    "sec6": sec6, "sec7": sec7, "sec8": sec8, "sec9": sec9, "sec10": sec10,
}


if __name__ == "__main__":
    wanted = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in wanted or ["overview"] + list(SCENES):
        if name == "overview":
            build()
        else:
            SCENES[name]()
