"""TRM_MLCC: the Terms-tab overview for MLCC, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_mlcc.py

Writes assets/term_TRM_MLCC.glb. Captions live in specs/terms/TRM_MLCC.json (same beat count).

The VRM page's GPU board (power_vrm_detail: layered PCB, cut-open package, 16 phases) carries the
decoupling capacitors an AI board is covered in: rings round the package on top, a dense field
under it on the back. One MLCC is drawn ~40x life size beside the board, cut open: barium-titanate
ceramic with ~30 interleaved nickel electrodes, odd ones tied to the left termination and even
ones to the right, each termination copper under nickel under tin.

Beats:
  0 board     the board, the package, the phases and the decap rings
  1 inside    the giant cap, cut open: the interleaved electrodes and the terminations
  2 charge    charge flows in at both ends; the plates light, + and - alternating
  3 load step  the GPU's current jumps; nearby caps dump charge into the package first
  4 everywhere every cap on the board flickers, the die stays steady
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from sand_overview import F, beat, empty, label, show  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, camera_path, run, rise, blink, mat  # noqa: E402

import term_common as C  # noqa: E402

SLUG = "TRM_MLCC"
BEATS = [
    ("Thousands of tiny capacitors sit round the GPU and under it",
     "An AI accelerator board is carpeted in multilayer ceramic capacitors (MLCCs): rings of them round the GPU package, "
     "and a dense field on the back of the board right under the die. Each is a few millimetres long or less. "
     "A phone holds about a thousand; one AI server board holds many thousands."),
    ("Inside one: ceramic layers between interleaved nickel electrodes",
     "Cut one open and it is a stack: up to hundreds of nickel electrode layers, each a few microns thick, separated by "
     "barium-titanate ceramic. Every other electrode reaches the left end, the rest reach the right. Each end is capped "
     "with copper, then nickel, then tin so it can be soldered. More, thinner layers mean more capacitance in the same size."),
    ("Charge comes in at both ends and fills every gap",
     "Voltage across the two ends charges every plate: + on the left-tied plates, - on the right-tied ones. Each ceramic "
     "gap holds a little charge in its electric field, and the stack adds them all up, so a part smaller than a grain of "
     "rice can hold tens of microfarads."),
    ("When the GPU's load jumps, nearby caps answer before the VRM",
     "A GPU can swing hundreds of amps in nanoseconds. The voltage regulator's control loop takes microseconds to react, so "
     "for that gap the capacitors closest to the die dump their stored charge in and hold the voltage up. That is why "
     "they crowd round and under the package: every millimetre of copper adds inductance that slows them down."),
    ("Every cap smooths its own patch; the die sees a steady voltage",
     "Together the caps keep the core voltage within a few percent while current swings wildly. More watts per board means "
     "more and better MLCCs, and supply is concentrated: Murata (MRAAY), Samsung Electro-Mechanics, TDK (TTDKY), Yageo and "
     "Vishay (VSH). High-end parts can run tight in AI build-outs."),
]

# the giant capacitor, beside the board's right edge, standing on its own pads
GX0, GX1 = 175.0, 245.0  # length along x (terminations at both ends)
GY0, GY1 = 0.6, 34.0
GZ0 = -34.0  # back face; front face is the cut at z = 0
TERM = 7.0  # termination thickness at each end
N_EL = 28


def mats(m):
    m["ceramic"] = mat("mlcc_ceramic", (0.80, 0.70, 0.52), rough=0.75)
    m["nickel"] = mat("mlcc_ni", (0.62, 0.64, 0.66), metal=0.95, rough=0.28)
    m["tin"] = mat("mlcc_tin", (0.86, 0.87, 0.89), metal=0.9, rough=0.2)
    m["plus"] = mat("mlcc_plus", (1.0, 0.62, 0.18), emit=(1.0, 0.55, 0.12), strength=2.2)
    m["minus"] = mat("mlcc_minus", (0.30, 0.75, 1.0), emit=(0.25, 0.70, 1.0), strength=2.2)
    m["field_e"] = mat("mlcc_field", (0.75, 0.6, 1.0), emit=(0.65, 0.5, 1.0), strength=3.0)


def giant(m, root):
    """The cut-open capacitor. Returns points, glow groups (+ plates, - plates, field) and the two
    termination charge paths."""
    g = empty("gcap", root)
    a0, a1 = GX0 + TERM, GX1 - TERM
    # ceramic body with cover layers top and bottom
    bx("g_body", (a0, GY0 + 1.2, GZ0), (a1, GY1 - 1.2, 0.0), m["ceramic"], g)
    # terminations: copper base, nickel barrier, tin finish (each a shell over the end)
    for side, (x_in, x_out) in (("l", (a0, GX0)), ("r", (a1, GX1))):
        d = 1.0 if x_out > x_in else -1.0
        for k, (t0, t1, mt) in enumerate(((0.0, 3.2, "copper"), (3.2, 5.0, "nickel"), (5.0, TERM, "tin"))):
            xa, xb = x_in + d * t0, x_in + d * t1
            wrap = 3.0 - 0.8 * k  # each shell wraps a little onto top and bottom
            bx(f"g_t{side}{k}", (xa, GY0 + 0.4 * k, GZ0 - 0.4 * k), (xb, GY1 - 0.4 * k, 0.0), m[mt], g)
            bx(f"g_t{side}{k}_top", (x_in - d * wrap, GY1 - 1.2 - 0.4 * k, GZ0), (xa, GY1 - 0.4 * k, 0.0), m[mt], g)
            bx(f"g_t{side}{k}_bot", (x_in - d * wrap, GY0 + 0.4 * k, GZ0), (xa, GY0 + 1.2 + 0.4 * k, 0.0), m[mt], g)
    # solder pads and fillets onto the board
    for side, (xa, xb) in (("l", (GX0 - 5.0, GX0 + 10.0)), ("r", (GX1 - 10.0, GX1 + 5.0))):
        bx(f"g_pad{side}", (xa, 0.0, GZ0 - 4.0), (xb, 0.4, 0.0), m["copper"], g)
        bx(f"g_fil{side}", (xa + 1.0, 0.4, GZ0 - 2.0), (xb - 1.0, 4.0, 0.0), m["solder"], g)
    # electrodes: alternate tie to left / right, each stopping short of the far end
    pitch = (GY1 - GY0 - 6.0) / N_EL
    plus, minus = empty("g_plus", root), empty("g_minus", root)
    layers = []
    for i in range(N_EL):
        y = GY0 + 3.0 + pitch * (i + 0.5)
        left = i % 2 == 0
        xa, xb = (a0, a1 - 6.0) if left else (a0 + 6.0, a1)
        t = 0.32 * pitch
        layers.append(bx(f"g_el{i}", (xa, y - t, GZ0 + 2.0), (xb, y + t, 0.12), m["nickel"], g))
        gl = plus if left else minus
        bx(f"g_elg{i}", (xa + 0.5, y - t, GZ0 + 2.0), (xb - 0.5, y + t, 0.25), m["plus" if left else "minus"], gl)
    D.join(layers, "g_electrodes")
    # field lines between plates in the overlap: short vertical ticks across the gaps
    fg = empty("g_field", root)
    ticks = []
    for i in range(N_EL - 1):
        y0 = GY0 + 3.0 + pitch * (i + 0.5)
        for x in (a0 + 12.0, a0 + 24.0, (a0 + a1) / 2, a1 - 24.0, a1 - 12.0):
            ticks.append(bx(f"g_ft{i}_{x:.0f}", (x - 0.25, y0 + 0.35 * pitch, -0.1), (x + 0.25, y0 + 0.65 * pitch, 0.35), m["field_e"], fg))
    D.join(ticks, "g_field_m")
    for o in (plus, minus, fg):
        show(o, [])
    ym = (GY0 + GY1) / 2
    paths = {
        "l": [(GX0 - 4.0, 0.6, 1.0), (GX0 + 1.0, 6.0, 1.0), (GX0 + 2.0, ym, 1.0), (GX0 + 2.0, GY1 - 3.0, 1.0)],
        "r": [(GX1 + 4.0, 0.6, 1.0), (GX1 - 1.0, 6.0, 1.0), (GX1 - 2.0, ym, 1.0), (GX1 - 2.0, GY1 - 3.0, 1.0)],
    }
    pts = {"cap": ((GX0 + GX1) / 2, GY1, GZ0 / 2), "el": ((GX0 + GX1) / 2, ym, 0.0), "tl": (GX0 + 2.0, GY1, 0.0),
           "tr": (GX1 - 2.0, GY1 - 8.0, 0.0), "cer": ((GX0 + GX1) / 2, GY1 - 0.6, 0.0), "pad": (GX0, 0.4, 0.0)}
    return pts, {"plus": plus, "minus": minus, "field": fg}, paths


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk, ph, die_glow, glow_top, spots = b["pk"], b["ph"], b["die_glow"], b["glow"], b["spots"]
    gp, gg, gpaths = giant(m, root)
    # a magnifier ring on the board marking which cap the giant one is
    bx("mag_mark", (66.0, 0.0, -14.0), (74.0, 0.25, -6.0), m["field"], root)
    for side in (-1, 1):
        D.polyline(f"mag_line{side}", [(70.0, 3.0, -10.0), (GX0 - 2.0, GY1 * (0.5 + 0.5 * side), -10.0)], 0.25, m["field"], root)

    # beat 1-2: the giant cap's plates and field
    show(gg["plus"], [(F(2, 0.25), F(3, 0)), (F(4, 0), F(5, 0))])
    show(gg["minus"], [(F(2, 0.25), F(3, 0)), (F(4, 0), F(5, 0))])
    show(gg["field"], [(F(2, 0.5), F(3, 0))])
    run(root, "q_l", gpaths["l"], 7, 1.0, m["plus"], [2, 4], 0.0, 0.6, 50)
    run(root, "q_r", gpaths["r"], 7, 1.0, m["minus"], [2, 4], 0.0, 0.6, 50)

    # beat 3: load step. caps right at the package dump charge in fast; the VRM phases follow later
    show(die_glow, [(F(3, 0.2), F(5, 0))])
    for k, (x, z, _) in enumerate(spots[:: 3]):
        if True:
            zc = min(z, -2.0)
            tgt = (max(-30.0, min(30.0, x * 0.4)), D.DIE_Y[1], max(-30.0, min(-4.0, zc * 0.4)))
            run(root, f"dump{k}", [(x, 2.4, zc), ((x + tgt[0]) / 2, 9.0, (zc + tgt[2]) / 2), tgt], 2, 0.8, m["v12"], [3, 4], 0.18, 0.4, 18)
    for side in (-1, 1):
        run(root, f"slow{side}", D.front_path(side), 6, 1.2, m["amp"], [3, 4], 0.45, 0.95, 80)
    rise(root, "die_heat", (0.0, D.DIE_Y[1] + 1.0, -16.0), 5, 1.0, m["heat"], 3, 0.25, 0.9, 30.0, 60, (14.0, 10.0))

    # beat 4: every cap flickers in turn
    for k, g_ in enumerate(glow_top):
        blink(g_, 4, [k, k + 4], n=8, on=0.6)
    blink(glow_top[0], 3, [1, 2], n=8, on=0.8)

    tags = {
        0: [("GPU package", pk["top"]), ("decap rings round the GPU", (-70.0, 2.0, -70.0)),
            ("hundreds more on the back", (0.0, D.BOT - 2.0, -10.0)), ("VRM phases", ph["ind"][(-1, 3)]["top"])],
        1: [("one MLCC, ~40x size, cut open", gp["cap"]), ("~30 nickel electrodes", gp["el"]),
            ("barium-titanate ceramic", gp["cer"]), ("Cu / Ni / Sn termination", gp["tl"])],
        2: [("odd plates tie left: +", gp["tl"]), ("even plates tie right: -", gp["tr"]),
            ("charge held in every gap", gp["el"])],
        3: [("GPU load jumps in ns", pk["top"]), ("caps nearby answer first", (-70.0, 3.0, -40.0)),
            ("VRM catches up in us", ph["ind"][(-1, 1)]["top"])],
        4: [("thousands per AI board", (-70.0, 2.0, -70.0)), ("Murata, Samsung EM, TDK, Yageo", gp["cap"]),
            ("voltage held steady", pk["top"])],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame(((GX0 + GX1) / 2, (GY0 + GY1) / 2, -10.0), 90.0, 0.22, 0.20),
        frame(((GX0 + GX1) / 2, (GY0 + GY1) / 2, -4.0), 80.0, 0.05, 0.08),
        frame((-20.0, 4.0, -30.0), 170.0, 0.25, 0.55),
        frame((60.0, 0.0, -70.0), 400.0, 0.20, 0.55, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
