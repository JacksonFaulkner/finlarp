"""TRM_TPU on the MLCC base board: the board's package stands in for a TPU, a TPU die is drawn big and
open on the bench (two systolic matrix units, vector unit, HBM stacks, ICI link ports), and behind the
board a 4x4 slice of a pod is wired up in a torus.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_tpu.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_TPU"
BEATS = [
    ("A TPU is a custom chip built only for AI math",
     "A Tensor Processing Unit (TPU) is Google's in-house AI accelerator. It sits on a board much like a GPU: a big "
     "package with high-bandwidth memory beside the die and a forest of power phases round it. Other hyperscalers build "
     "the same kind of chip: AWS Trainium and Inferentia, Meta MTIA, Microsoft Maia."),
    ("Most of the die is a few huge systolic matrix units",
     "Open the die and the bulk of it is matrix multiply units (MXUs): systolic arrays of 128x128 or larger "
     "multiply-accumulate cells. A vector unit handles the activation functions and normalization, a scalar core issues "
     "instructions, and HBM stacks beside the die feed it weights and data. There is far less control logic than in a GPU."),
    ("Data streams from HBM through the matrix units",
     "Weights and activations come in from HBM at terabytes per second, flow through the MXUs in lockstep, and results "
     "go to the vector unit. Because the hardware only does what neural nets need, more of the chip's area and power go "
     "to math, which is why hyperscalers can beat GPU cost per token on their own models."),
    ("Thousands of TPUs join into a pod",
     "Each chip has inter-chip interconnect (ICI) links to its neighbours, wired as a 2D or 3D torus so the edges wrap "
     "round. Newer pods add optical circuit switches to rewire the torus. A pod holds thousands of chips that train one "
     "model together, exchanging gradients over these links instead of the general data-center network."),
    ("Custom chips: owned by cloud giants, designed with partners",
     "The hyperscaler designs the architecture and uses the chips for its own models and cloud customers, so they do not "
     "show up as merchant sales. Broadcom (AVGO) co-designs Google's TPUs and others' chips; Marvell (MRVL) works on "
     "Trainium; TSMC builds them. Related: Alphabet (GOOGL), Amazon (AMZN), Meta (META), AVGO, MRVL."),
]

X0, X1, Z0 = 152.0, 246.0, -70.0  # the die on the bench
DY = (0.6, 6.0)
PZ = -300.0  # pod plane (behind the board)


def mxu(m, g, root, name, x0, z0, n=6, p=5.0):
    """A systolic matrix unit flat on the die: n x n cells. Returns (wavefront groups, centre)."""
    y = DY[1]
    bx(f"{name}_bg", (x0 - 1.0, y, z0 - 1.0), (x0 + n * p + 1.0, y + 0.6, z0 + n * p + 1.0), m["dark"], g)
    diag = [empty(f"{name}_d{k}", root) for k in range(2 * n - 1)]
    cells = []
    for i in range(n):
        for j in range(n):
            cx, cz = x0 + p * (j + 0.5), z0 + p * (i + 0.5)
            cells.append(bx(f"{name}_c{i}{j}", (cx - 2.0, y + 0.6, cz - 2.0), (cx + 2.0, y + 2.2, cz + 2.0), m["fet"], g))
            cells.append(bx(f"{name}_r{i}{j}", (cx - 2.0, y + 2.2, cz - 2.0), (cx + 2.0, y + 2.6, cz - 1.0), m["gold"], g))
            bx(f"{name}_g{i}{j}", (cx - 1.6, y + 2.3, cz - 0.8), (cx + 1.6, y + 2.5, cz + 1.6), m["sig"], diag[i + j])
    D.join(cells, f"{name}_cells")
    for d in diag:
        show(d, [])
    return diag, (x0 + n * p / 2, y + 2.6, z0 + n * p / 2)


def die(m, root):
    g = empty("tpu", root)
    # package substrate, interposer, then the die and HBM
    bx("t_sub", (X0, 0.4, Z0), (X1, DY[0] + 3.0, 0.0), m["substrate"], g)
    bx("t_ip", (X0 + 3.0, 3.4, Z0 + 3.0), (X1 - 3.0, 4.6, -3.0), m["si"], g)
    dx0, dx1 = X0 + 22.0, X1 - 22.0
    bx("t_die", (dx0, 4.6, Z0 + 6.0), (dx1, DY[1], -6.0), m["die"], g)
    hbm = []
    for side, (hx0, hx1) in (("l", (X0 + 5.0, dx0 - 2.0)), ("r", (dx1 + 2.0, X1 - 5.0))):
        for k in range(2):
            z1 = -8.0 - k * 30.0
            for n in range(6):
                y = 4.6 + n * 1.6
                hbm.append(bx(f"t_hbm{side}{k}{n}", (hx0, y, z1 - 24.0), (hx1, y + 1.2, z1), m["hbm"], g))
                hbm.append(bx(f"t_hbmd{side}{k}{n}", (hx0 + 0.3, y + 1.2, z1 - 23.7), (hx1 - 0.3, y + 1.6, z1 - 0.3), m["hbm_dram"], g))
    D.join(hbm, "t_hbm")
    d1, c1 = mxu(m, g, root, "mxa", dx0 + 3.0, Z0 + 9.0)
    d2, c2 = mxu(m, g, root, "mxb", dx0 + 3.0, Z0 + 9.0 + 32.0)
    vx0 = dx0 + 37.0
    bx("t_vpu", (vx0, DY[1], Z0 + 9.0), (dx1 - 3.0, DY[1] + 1.8, -22.0), m["driver"], g)
    bx("t_scalar", (vx0, DY[1], -20.0), (dx1 - 3.0, DY[1] + 2.4, -9.0), m["silicon"], g)
    for k in range(4):
        z = Z0 + 12.0 + k * 9.0
        bx(f"t_vl{k}", (vx0 + 1.0, DY[1] + 1.8, z), (dx1 - 4.0, DY[1] + 2.1, z + 5.0), m["grid"], g)
    # ICI ports along the front and back edges
    for k in range(6):
        x = X0 + 10.0 + k * (X1 - X0 - 20.0) / 5
        for z in (Z0 + 0.5, -0.5):
            bx(f"t_ici{k}{z:.0f}", (x - 3.0, DY[0] + 3.0, z - 1.5), (x + 3.0, DY[0] + 5.0, z + 1.5), m["gold"], g)
    vpu = empty("t_vpug", root)
    bx("t_vpug_b", (vx0 + 0.5, DY[1] + 1.9, Z0 + 9.5), (dx1 - 3.5, DY[1] + 2.4, -22.5), m["dim_glow"], vpu)
    show(vpu, [])
    pts = {"die": ((dx0 + dx1) / 2, DY[1], -40.0), "mxu": c1, "mxu2": c2, "vpu": (vx0 + 10.0, DY[1] + 2.0, -45.0),
           "scalar": (vx0 + 10.0, DY[1] + 2.4, -14.0), "hbm": (X0 + 10.0, 14.0, -20.0), "hbm_r": (X1 - 10.0, 14.0, -50.0),
           "ici": (X0 + 10.0, 5.0, 0.0)}
    return pts, d1 + d2, vpu, (dx0, dx1)


def pod(m, root):
    """A 4x4 slice of a pod behind the board: chip trays on a grid with torus links that wrap."""
    g = empty("pod", root)
    xs = [-240.0 + 120.0 * k for k in range(4)]
    ys = [10.0 + 40.0 * k for k in range(4)]
    chips = []
    for x in xs:
        for y in ys:
            chips.append(bx(f"pt{x:.0f}{y:.0f}", (x - 34.0, y - 8.0, PZ - 20.0), (x + 34.0, y + 8.0, PZ + 20.0), m["dark"], g))
            chips.append(bx(f"pc{x:.0f}{y:.0f}", (x - 12.0, y + 8.0, PZ - 10.0), (x + 12.0, y + 11.0, PZ + 10.0), m["die"], g))
            for s in (-1, 1):
                chips.append(bx(f"ph{x:.0f}{y:.0f}{s}", (x + s * 14.0, y + 8.0, PZ - 8.0), (x + s * 20.0, y + 12.0, PZ + 8.0), m["hbm"], g))
    D.join(chips, "pod_chips")
    links = []
    for y in ys:
        D.polyline(f"lx{y:.0f}", [(xs[0], y, PZ + 22.0), (xs[-1], y, PZ + 22.0)], 0.8, m["copper"], g)
        D.polyline(f"wx{y:.0f}", [(xs[-1] + 34.0, y, PZ + 22.0), (xs[-1] + 50.0, y, PZ + 30.0), (xs[0] - 50.0, y, PZ + 30.0), (xs[0] - 34.0, y, PZ + 22.0)], 0.6, m["alum"], g)
        links.append([(xs[0], y + 1.0, PZ + 23.5), (xs[-1], y + 1.0, PZ + 23.5)])
    for x in xs:
        D.polyline(f"ly{x:.0f}", [(x + 30.0, ys[0], PZ + 22.0), (x + 30.0, ys[-1], PZ + 22.0)], 0.8, m["copper"], g)
        links.append([(x + 30.0, ys[0], PZ + 23.5), (x + 30.0, ys[-1], PZ + 23.5)])
    glow = empty("pod_glow", root)
    for x in xs:
        for y in ys:
            bx(f"pg{x:.0f}{y:.0f}", (x - 11.0, y + 11.0, PZ - 9.0), (x + 11.0, y + 11.6, PZ + 9.0), m["die_hot"], glow)
    show(glow, [])
    return links, glow, {"pod": (xs[1], ys[3] + 12.0, PZ), "link": (xs[2], ys[1], PZ + 22.0),
                         "wrap": (xs[0] - 50.0, ys[2], PZ + 30.0), "mid": (-60.0, 70.0, PZ)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root)
    pk, ph = b["pk"], b["ph"]
    pts, diag, vpu, (dx0, dx1) = die(m, root)
    links, pglow, pp = pod(m, root)
    C.magnify(m, root, pk["die_r"], (X0 - 2.0, 10.0, -35.0))
    show(b["die_glow"], [(F(2, 0.1), F(5, 0))])

    # beat 1: the MXUs flicker once to show what they are; beat 2: data streams HBM -> MXU -> VPU
    for k, g_ in enumerate(diag[:11]):
        blink(g_, 1, [k], n=11, on=1.5)
    for k, g_ in enumerate(diag):
        blink(g_, 2, [k % 11, k % 11 + 11], n=22, on=1.5)
    show(vpu, [(F(2, 0.3), F(3, 0))])
    for side, hx in (("l", X0 + 12.0), ("r", X1 - 12.0)):
        for k, z in enumerate((-20.0, -50.0)):
            run(root, f"hb{side}{k}", [(hx, 15.0, z), (dx0 + 15.0, 10.0, z), (dx0 + 30.0, 10.0, z + 2.0), (dx1 - 12.0, 9.0, -40.0)],
                5, 0.8, m["chan"], 2, 0.0 + 0.1 * k, 0.8, 40)
    for side in (-1, 1):
        run(root, f"amp{side}", D.front_path(side), 5, 1.2, m["amp"], 2, 0.1, 0.9, 90)
    rise(root, "th", ((dx0 + dx1) / 2, DY[1] + 3.0, -35.0), 4, 0.8, m["heat"], 2, 0.1, 0.8, 18.0, 60, (18.0, 18.0))

    # beat 3-4: the pod lights up; beads race round the torus links
    show(pglow, [(F(3, 0.15), F(5, 0))])
    for k, pth in enumerate(links):
        run(root, f"ici{k}", pth, 3, 1.6, m["e_blue"], [3, 4], 0.05 * (k % 4), 0.7, 50)
        run(root, f"icr{k}", pth[::-1], 2, 1.6, m["sig"], [3], 0.1 + 0.05 * (k % 4), 0.7, 50)

    C.tags(root, {
        0: [("TPU-class package", pk["top"]), ("HBM beside the die", pk["hbm"]), ("power phases", ph["ind"][(-1, 3)]["top"]),
            ("one TPU die, opened up", pts["die"])],
        1: [("matrix unit (systolic)", pts["mxu"]), ("second MXU", pts["mxu2"]), ("vector unit", pts["vpu"]),
            ("scalar core", pts["scalar"]), ("HBM stacks", pts["hbm"])],
        2: [("HBM: TB/s in", pts["hbm"]), ("MXUs in lockstep", pts["mxu"]), ("results to vector unit", pts["vpu"])],
        3: [("4x4 slice of a pod", pp["pod"]), ("ICI links chip to chip", pp["link"]), ("torus: edges wrap round", pp["wrap"])],
        4: [("thousands of chips, one model", pp["mid"]), ("GOOGL, AMZN, META", pts["die"]), ("design partners: AVGO, MRVL", pts["ici"])],
    })
    C.done(SLUG, BEATS, [
        frame((30.0, 0.0, -80.0), 400.0, 0.32, 0.6, pad=1.0),
        frame(((dx0 + dx1) / 2, DY[1], -36.0), 85.0, 0.20, 0.75),
        frame(((X0 + X1) / 2, DY[1], -36.0), 105.0, 0.28, 0.6),
        frame((-60.0, 70.0, PZ), 400.0, 0.08, 0.30, pad=1.0),
        frame((-30.0, 40.0, -160.0), 520.0, 0.35, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
