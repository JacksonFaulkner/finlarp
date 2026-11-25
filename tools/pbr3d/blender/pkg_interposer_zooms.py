"""Zoom-ins (a-e) for the INTERPOSER page, three beats each, each its own scene with its own camera
moves and beads (tui/src/screens/diagrams_nodes/packaging/interposer/zooms.rs):

  a CoWoS-S and -L            the silicon slab; its BEOL close up; the organic slab with bridges
  b a signal from HBM to GPU  out of the base die; across the BEOL; up into the GPU, in parallel
  c growing past the reticle  1 reticle and 3.3x; 9.5x with 12 HBM (2027); 14x+ with 24 (2029)
  d TSVs and power            one TSV cut open; power up through it; the TSV array to the C4s
  e interposers per wafer     a wafer of 3.3x squares; of 9.5x squares; the package on its board

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_interposer_zooms.py -- a

Writes assets/pkg_interposer_zoom_<letter>.glb.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_interposer_detail as D  # noqa: E402
from pkg_interposer_detail import frame, camera_path, run, rise, present, empty  # noqa: E402
import pkg_interposer_overview as OV  # noqa: E402

PAGE = "pkg_interposer"
BEATS = 3
BY = D.BY


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def zoom_a(m, root):
    gs, s, gl, l_ = OV.both(m, root)
    present(gs, span(0, 0, 2, 0))
    present(gl, beat(2))
    OV.data(m, root, 1, n=4)
    OV.data(m, root, 2, n=4, bridge=True)
    p = s["pts"]
    tags(root, [
        [("CoWoS-S: one silicon slab", p["si"]), ("slab wider than die + HBM", (D.IP_X - 2.0, D.SI[1], 0.0)), ("on the substrate", p["sub_top"])],
        [("BEOL: M1-M4 in oxide", p["m1"]), ("silicon body", (-20.0, 0.0, 0.0)), ("TSVs", p["tsv"])],
        [("organic RDL interposer", (-34.0, 2.0, 0.0)), ("LSI bridge: silicon only here", (15.5, 1.1, 0.0)), ("two GPU dies", (-7.0, D.DIE[1], 0.0))],
    ])
    camera_path(root, [
        frame((0.0, 0.0, -4.0), 95.0, 0.30, 0.28),
        frame((-24.0, 1.0, 0.0), 30.0, 0.18, 0.18, min_d=40.0),
        frame((10.0, 1.5, 0.0), 40.0, 0.22, 0.20, min_d=30.0),
    ])


def zoom_b(m, root):
    s = D.scene(m, root, "S")
    for k in range(3):
        p = D.data_path(1, k)
        run(root, f"b0_{k}", p[:3], 4, 0.4, m["ip_data"], 0, 0.05 * k, 0.8, 40)
        run(root, f"b1_{k}", p[1:5], 4, 0.4, m["ip_data"], 1, 0.05 * k, 0.8, 60)
    OV.data(m, root, 2, n=6, u1=0.85)
    tags(root, [
        [("HBM base die", s["pts"]["hbm_base"]), ("microbumps", (D.HBM_X[0] + 4.0, D.UB[1], 0.0)), ("down into the BEOL", (D.HBM_X[0] + 2.0, D.M_Y[1], D.FZ))],
        [("across M2/M3", (D.DIE_X + 1.5, D.M_Y[2], D.FZ)), ("a few mm of copper", (D.HBM_X[0] - 1.0, D.M_Y[0], 0.0))],
        [("up into the GPU", (D.DIE_X - 2.0, D.DIE[0] + 0.4, D.FZ)), ("1,024 bits per HBM3 stack", s["pts"]["hbm"]), ("2,048 in HBM4", (-D.HBM_X[1] + 1.0, D.HBM_Y[1], 0.0))],
    ])
    camera_path(root, [
        frame((D.HBM_X[0] + 3.0, 3.5, 0.0), 26.0, 0.14, 0.16, min_d=40.0),
        [(0.0, frame((D.HBM_X[0] + 2.0, 2.5, 0.0), 24.0, 0.10, 0.12, min_d=40.0)), (0.5, frame((D.DIE_X, 2.5, 0.0), 24.0, -0.10, 0.12, min_d=40.0))],
        frame((0.0, 3.5, 0.0), 70.0, 0.15, 0.20, min_d=40.0),
    ])


def zoom_c(m, root):
    cx, cy, cz = OV.TOP
    g0 = empty("c_g0", root)
    D.reticle_plane(m, g0, (cx - 120.0, cy, cz), 1, 1, "c_r1")
    D.topdown_package(m, g0, (cx - 120.0, cy + 1.2, cz), 0.1, 0.1, 1, 0, "c_r1p")
    D.reticle_plane(m, g0, (cx, cy, cz), 2, 2, "c_r33", frac=3.3 / 4.0)
    D.topdown_package(m, g0, (cx, cy + 1.2, cz), 46.0, 60.0, 1, 4, "c_s33")
    present(g0, beat(0))
    g1 = empty("c_g1", root)
    D.reticle_plane(m, g1, (cx, cy, cz), 4, 3, "c_r95", frac=9.5 / 12.0)
    D.topdown_package(m, g1, (cx, cy + 1.2, cz), 92.0, 85.0, 2, 12, "c_l95", organic=True)
    present(g1, beat(1))
    g2 = empty("c_g2", root)
    D.reticle_plane(m, g2, (cx, cy, cz), 4, 4, "c_r14", frac=14.0 / 16.0)
    D.topdown_package(m, g2, (cx, cy + 1.2, cz), 112.0, 118.0, 4, 16, "c_l14", organic=True)
    present(g2, beat(2))
    tags(root, [
        [("one reticle: 26 x 33 mm = 858 mm2", (cx - 120.0, cy + 1.0, cz - 16.5)), ("CoWoS-S: ~3.3x, ~2,700 mm2", (cx, cy + 4.0, cz - 30.0))],
        [("2027 plan: ~9.5 reticles", (cx - 50.0, cy + 1.0, cz - 49.0)), ("12 HBM stacks", (cx + 30.0, cy + 4.6, cz + 30.0)), ("organic slab + bridges", (cx - 40.0, cy + 1.6, cz + 38.0))],
        [("2029 plan: 14+ reticles", (cx - 52.0, cy + 1.0, cz - 66.0)), ("up to 24 HBM5E (16 drawn)", (cx + 40.0, cy + 4.6, cz + 30.0)), ("4 compute dies", (cx, cy + 3.6, cz))],
    ])
    camera_path(root, [
        frame((cx - 60.0, cy, cz), 200.0, 0.0, 1.2, pad=1.0),
        frame((cx, cy, cz), 140.0, 0.0, 1.2, pad=1.0),
        frame((cx, cy, cz), 150.0, 0.0, 1.2, pad=1.0),
    ])


def zoom_d(m, root):
    s = D.scene(m, root, "S")
    g, tp = D.tsv_bench(m, root, (0.0, BY, 0.0), 6.0)
    present(g, span(0, 0, 2, 0))
    run(root, "d_pw", tp["path"][:6], 6, 1.0, m["ip_power"], 1, 0.0, 0.85, 50)
    OV.power(m, root, 2, xs=(-12.0, -6.0, 0.0, 6.0, 12.0, -18.0, 18.0), n=4)
    tags(root, [
        [("copper fill", tp["cu"]), ("oxide liner", tp["liner"]), ("barrier (Ta/TaN)", tp["bar"]), ("silicon, ~100 um", tp["si"])],
        [("backside pad", tp["bpad"]), ("C4 bump below", tp["c4"]), ("lands on M1", tp["m1"])],
        [("TSV array, every amp", s["pts"]["tsv"]), ("C4 row", s["pts"]["c4"]), ("from the substrate", s["pts"]["sub_top"])],
    ])
    camera_path(root, [
        frame((0.0, BY + 9.0, 0.0), 46.0, 0.30, 0.16, min_d=40.0),
        frame((0.0, BY + 3.0, 0.0), 50.0, 0.20, 0.10, min_d=40.0),
        frame((0.0, -3.0, 0.0), 60.0, 0.20, 0.12, min_d=40.0),
    ])


def zoom_e(m, root):
    cx, cy, cz = (0.0, BY, 0.0)
    g0, n33 = D.wafer(m, root, (cx, cy, cz), 46.0, 59.0, "e_w33")
    present(g0, beat(0))
    g1, n95 = D.wafer(m, root, (cx, cy, cz), 88.0, 92.0, "e_w95")
    present(g1, beat(1))
    gp = empty("e_pkg", root)
    s = D.scene(m, gp, "L")
    present(gp, beat(2))
    present(s["lid"], beat(2))
    for gl in s["glow"]:
        present(gl, span(2, 0.2, 3, 0))
    rise(root, "e_heat", (0.0, D.LID[1] + 0.5, -4.0), 8, 0.5, m["ip_heat"], 2, 0.2, 0.9, 20.0, 60, (14.0, 3.0))
    tags(root, [
        [("300 mm wafer", (cx + 110.0, cy + 0.6, cz + 90.0)), (f"~{n33} CoWoS-S slabs (3.3x)", (cx, cy + 1.0, cz))],
        [(f"~{n95} slabs at 9.5x", (cx, cy + 1.0, cz)), ("fewer per wafer as they grow", (cx + 110.0, cy + 0.6, cz + 90.0))],
        [("each one bonded into a package", (0.0, D.LID[1], 0.0)), ("CoWoS capacity caps AI GPU output", (40.0, D.SUB_T[1], 0.0))],
    ])
    camera_path(root, [
        frame((cx, cy, cz), 320.0, 0.0, 1.0, pad=1.0),
        frame((cx, cy, cz), 320.0, 0.25, 1.0, pad=1.0),
        frame((0.0, -2.0, -6.0), 125.0, 0.36, 0.30),
    ])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    ZOOMS[letter](m, root)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python pkg_interposer_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
