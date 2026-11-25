"""The INTERPOSER page's nine numbered sections. Section N illustrates heading N of
tui/src/screens/diagrams_pages/PKG_INTERPOSER.txt (the tenth, Sources, is text only). Three beats
each, one beat is 8 s. Parts come from pkg_interposer_detail.py; close-up benches (a TSV, a BEOL
stack, pitch strips, wafers, reticle planes) are built above the package at BY.

  1 what happens   the package cut open; data across the interposer; power up through it
  2 the parts      CoWoS-S, TSV and BEOL; CoWoS-L and its LSI bridge; the BEOL up close
  3 in order       out of the HBM; through the BEOL stack; up into the GPU while power climbs
  4 CoWoS-S        the silicon slab; one TSV cut open; ~3.3 reticles from above
  5 CoWoS-L        the organic slab; an HBM bridge; the die-to-die bridge
  6 past reticle   3.3x from above; 9.5x with 12 stacks; fewer per wafer
  7 why silicon    silicon lines; organic RDL lines; substrate lines, one scale
  8 who makes it   TSMC on the slab; OSATs on the assembly; capacity on the wafer
  9 chokepoints    big slabs, few per wafer; one supplier, HBM beside it; heat and size

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_interposer_sections.py -- <n>
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
TOP = OV.TOP

V_WIDE = frame((0.0, -3.0, -4.0), 115.0, 0.30, 0.28)
V_HBM = frame((15.0, 3.5, 0.0), 30.0, 0.10, 0.20, min_d=40.0)
V_TSV = frame((-6.0, -1.0, 0.0), 40.0, 0.12, 0.10, min_d=40.0)
V_BRIDGE = frame((15.5, 2.0, 0.0), 26.0, 0.12, 0.16, min_d=40.0)


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def pkg(m, root, mode, beats, name):
    g = empty(name, root)
    s = D.scene(m, g, mode)
    present(g, [iv for b in beats for iv in beat(b)])
    return s


# ---- 1 what happens ----------------------------------------------------------------------------------


def sec1(m, root):
    s = D.scene(m, root, "S")
    OV.data(m, root, 1, n=5)
    OV.power(m, root, 2, xs=(-18.0, -12.0, -6.0, 0.0, 6.0, 12.0, 18.0), n=4)
    p = s["pts"]
    tags(root, [
        [("GPU die", p["die"]), ("HBM stacks", p["hbm"]), ("interposer under both", p["beol"]), ("substrate below", p["sub_top"])],
        [("HBM to GPU: thousands of wires", (D.DIE_X + 1.5, D.M_Y[1], D.FZ)), ("all inside the interposer", p["m1"])],
        [("power up through TSVs", p["tsv"]), ("C4 bumps to the substrate", p["c4"]), ("from the board", p["bga"])],
    ])
    camera_path(root, [V_WIDE, V_HBM, V_TSV])


# ---- 2 the parts ------------------------------------------------------------------------------------


def sec2(m, root):
    s = pkg(m, root, "S", [0], "s2_S")
    l_ = pkg(m, root, "L", [1], "s2_L")
    g, bp, path = D.beol_bench(m, root, (0.0, BY, 0.0), 7.0)
    present(g, beat(2))
    run(root, "s2_bb", path, 5, 0.9, m["ip_data"], 2, 0.05, 0.85, 60)
    OV.data(m, root, 1, n=3, bridge=True)
    p = s["pts"]
    tags(root, [
        [("COWOS-S: silicon interposer", p["si"]), ("TSV", p["tsv"]), ("BEOL wiring (M1-M4)", p["m1"]), ("microbumps", p["ub"])],
        [("COWOS-L: organic RDL", (-34.0, 2.0, 0.0)), ("LSI BRIDGE", (15.5, 1.1, 0.0)), ("copper TIVs", (-30.6, 0.0, 0.0))],
        [("M1-M2: finest lines", bp["m1"]), ("M3-M4: wider, for longer runs", bp["m4"]), ("oxide insulator", bp["ild"]), ("microbump pillar", bp["ub"])],
    ])
    camera_path(root, [
        frame((-14.0, 0.5, 0.0), 60.0, 0.22, 0.16, min_d=40.0),
        V_BRIDGE,
        frame((0.0, BY + 14.0, 0.0), 75.0, 0.18, 0.14, min_d=40.0),
    ])


# ---- 3 in order ------------------------------------------------------------------------------------


def sec3(m, root):
    s = pkg(m, root, "S", [0, 2], "s3_S")
    g, bp, path = D.beol_bench(m, root, (0.0, BY, 0.0), 7.0)
    present(g, beat(1))
    for k in range(3):
        p = D.data_path(1, k)
        run(root, f"s3_a{k}", p[:3], 4, 0.4, m["ip_data"], 0, 0.06 * k, 0.8, 40)
    run(root, "s3_bb", path, 6, 0.9, m["ip_data"], 1, 0.0, 0.85, 60)
    OV.data(m, root, 2, n=5)
    OV.power(m, root, 2, xs=(-6.0, 0.0, 6.0), n=3)
    tags(root, [
        [("1 out of the HBM base die", s["pts"]["hbm_base"]), ("through a microbump", (D.HBM_X[0] + 4.0, D.UB[1], 0.0))],
        [("2 down the via stack", bp["m3"]), ("across M2", bp["m2"]), ("from the pad", bp["pad"])],
        [("3 up into the GPU", (D.DIE_X - 2.0, D.DIE[0] + 0.4, D.FZ)), ("4 power climbs the TSVs", s["pts"]["tsv"]),
         ("5 thousands in parallel", s["pts"]["hbm"])],
    ])
    camera_path(root, [
        frame((D.HBM_X[0] + 3.0, 3.5, 0.0), 26.0, 0.14, 0.16, min_d=40.0),
        frame((-8.0, BY + 18.0, 0.0), 75.0, 0.12, 0.12, min_d=40.0),
        frame((4.0, 1.0, 0.0), 55.0, 0.18, 0.16, min_d=40.0),
    ])


# ---- 4 CoWoS-S ------------------------------------------------------------------------------------


def sec4(m, root):
    s = pkg(m, root, "S", [0], "s4_S")
    g, tp = D.tsv_bench(m, root, (0.0, BY, 0.0), 6.0)
    present(g, beat(1))
    run(root, "s4_pw", tp["path"][:6], 5, 1.0, m["ip_power"], 1, 0.05, 0.85, 50)
    gt = empty("s4_top", root)
    D.reticle_plane(m, gt, TOP, 2, 2, "s4_r", frac=3.3 / 4.0)
    D.topdown_package(m, gt, (TOP[0], TOP[1] + 1.2, TOP[2]), 46.0, 60.0, 1, 4, "s4_p")
    present(gt, beat(2))
    p = s["pts"]
    tags(root, [
        [("one silicon slab", p["si"]), ("BEOL on a mature node", p["m1"]), ("~100 um thin", (D.IP_X - 1.0, 0.0, 0.0))],
        [("TSV: copper through silicon", tp["cu"]), ("oxide liner insulates", tp["liner"]), ("barrier stops copper diffusing", tp["bar"])],
        [("limit: ~3.3 reticles", (TOP[0] - 26.0, TOP[1] + 1.0, TOP[2] - 33.0)), ("~2,700 mm2", (TOP[0], TOP[1] + 1.6, TOP[2] + 22.0)),
         ("4 HBM stacks", (TOP[0] + 12.0, TOP[1] + 4.6, TOP[2] - 25.0))],
    ])
    camera_path(root, [
        frame((-24.0, 0.0, 0.0), 50.0, 0.24, 0.16, min_d=40.0),
        frame((0.0, BY + 6.0, 0.0), 48.0, -0.25, 0.12, min_d=40.0),
        frame(TOP, 110.0, 0.0, 1.15, pad=1.0),
    ])


# ---- 5 CoWoS-L ------------------------------------------------------------------------------------


def sec5(m, root):
    s = D.scene(m, root, "L")
    OV.data(m, root, 1, n=5, bridge=True)
    for k in range(8):
        y = 0.98 + 0.12 * (k % 3)
        x0 = -4.0 - 0.6 * k
        run(root, f"s5_d2d{k}", [(x0, D.DIE[0] + 0.4, D.FZ), (x0, D.UB[0], D.FZ), (x0, y, D.FZ), (-x0, y, D.FZ), (-x0, D.UB[1], D.FZ),
                                 (-x0, D.DIE[0] + 0.4, D.FZ)], 4, 0.35, m["ip_data"], 2, 0.03 * k, 0.85, 40)
    tags(root, [
        [("organic interposer: cheaper, bigger", (-34.0, 2.0, 0.0)), ("silicon only at the seams", (15.5, 1.1, 0.0)),
         ("copper TIVs carry power", (-30.6, 0.0, 0.0))],
        [("LSI bridge: die to HBM", (15.5, 1.1, 0.0)), ("fine lines in the bridge", (17.0, 1.25, 0.0))],
        [("bridge under the die seam", (0.0, 1.1, 0.0)), ("Blackwell: ~10 TB/s die to die", (-7.0, D.DIE[1], 0.0))],
    ])
    camera_path(root, [
        frame((-8.0, 0.0, -2.0), 85.0, 0.26, 0.24),
        V_BRIDGE,
        frame((0.0, 2.5, 0.0), 26.0, -0.12, 0.16, min_d=40.0),
    ])


# ---- 6 growing past the reticle --------------------------------------------------------------------


def sec6(m, root):
    g0 = empty("s6_33", root)
    D.reticle_plane(m, g0, TOP, 2, 2, "s6_r33", frac=3.3 / 4.0)
    D.topdown_package(m, g0, (TOP[0], TOP[1] + 1.2, TOP[2]), 46.0, 60.0, 1, 4, "s6_p33")
    present(g0, beat(0))
    g1 = empty("s6_95", root)
    D.reticle_plane(m, g1, TOP, 4, 3, "s6_r95", frac=9.5 / 12.0)
    D.topdown_package(m, g1, (TOP[0], TOP[1] + 1.2, TOP[2]), 92.0, 85.0, 2, 12, "s6_p95", organic=True)
    present(g1, beat(1))
    gw, n95 = D.wafer(m, root, (0.0, BY, 0.0), 88.0, 92.0, "s6_w")
    present(gw, beat(2))
    tags(root, [
        [("CoWoS-S today: ~3.3x", (TOP[0] - 26.0, TOP[1] + 1.0, TOP[2] - 33.0)), ("RETICLE MULTIPLE", (TOP[0] + 26.0, TOP[1] + 1.0, TOP[2] + 33.0))],
        [("2027: ~9.5x", (TOP[0] - 52.0, TOP[1] + 1.0, TOP[2] - 49.0)), ("12 HBM stacks", (TOP[0] + 30.0, TOP[1] + 4.6, TOP[2] + 30.0))],
        [(f"only ~{n95} per 300 mm wafer", (0.0, BY + 1.0, 0.0)), ("2029: 14x+, 24 HBM5E", (110.0, BY + 0.6, 90.0))],
    ])
    camera_path(root, [
        frame(TOP, 110.0, 0.0, 1.15, pad=1.0),
        frame(TOP, 150.0, 0.0, 1.15, pad=1.0),
        frame((0.0, BY, 0.0), 320.0, 0.15, 1.0, pad=1.0),
    ])


# ---- 7 why silicon wiring -------------------------------------------------------------------------


def sec7(m, root):
    g, pp = D.pitch_strips(m, root, (0.0, BY, 0.0))
    for key_, b in (("si", 0), ("rdl", 1), ("sub", 2)):
        cx = pp[key_][0]
        run(root, f"s7_{key_}", [(cx - 19.0, BY + 1.0, -15.0), (cx + 19.0, BY + 1.0, -15.0)], 6, 0.5, m["ip_data"], b, 0.0, 0.85, 50)
    tags(root, [
        [("silicon BEOL: ~0.4 um lines", pp["si"]), (f"{pp['si_n']} wires in 40 um", pp["si_lo"])],
        [("organic RDL: ~2 um lines", pp["rdl"]), (f"{pp['rdl_n']} wires in 40 um", pp["rdl_lo"])],
        [("substrate build-up: ~10 um", pp["sub"]), (f"{pp['sub_n']} wires in 40 um", pp["sub_lo"]), ("1,024 bits need silicon", pp["si"])],
    ])
    camera_path(root, [
        frame((pp["si"][0], BY, -15.0), 44.0, 0.0, 1.0, min_d=40.0),
        frame((pp["rdl"][0], BY, -15.0), 44.0, 0.0, 1.0, min_d=40.0),
        frame((0.0, BY, -15.0), 140.0, 0.0, 1.0, pad=1.0),
    ])


# ---- 8 who makes it -------------------------------------------------------------------------------


def sec8(m, root):
    s = pkg(m, root, "S", [0], "s8_S")
    l_ = pkg(m, root, "L", [1], "s8_L")
    gw, n = D.wafer(m, root, (0.0, BY, 0.0), 46.0, 59.0, "s8_w")
    present(gw, beat(2))
    p = s["pts"]
    tags(root, [
        [("TSMC (TSM): interposer + CoWoS", p["si"]), ("UMC: outsourced interposers", p["m1"]), ("NVIDIA GPU die, TSMC-made", p["die"])],
        [("ASE (ASX): CoWoS-class assembly", (0.0, D.DIE[1], 0.0)), ("Amkor (AMKR): 2.5D packages", (-34.0, 2.0, 0.0)),
         ("HBM: SK hynix, Samsung, Micron", (D.HBM_X[1] - 1.0, D.HBM_Y[1], 0.0))],
        [("TSMC runs most CoWoS wafers", (0.0, BY + 1.0, 0.0)), ("OSATs add overflow", (110.0, BY + 0.6, 90.0))],
    ])
    camera_path(root, [V_WIDE, frame((0.0, 0.0, -2.0), 100.0, -0.25, 0.26), frame((0.0, BY, 0.0), 320.0, 0.0, 1.0, pad=1.0)])


# ---- 9 chokepoints -------------------------------------------------------------------------------


def sec9(m, root):
    gw, n = D.wafer(m, root, (0.0, BY, 0.0), 88.0, 92.0, "s9_w")
    present(gw, beat(0))
    s = pkg(m, root, "L", [1, 2], "s9_L")
    present(s["lid"], beat(2))
    for gl in s["glow"]:
        present(gl, span(2, 0.15, 3, 0))
    rise(root, "s9_heat", (0.0, D.LID[1] + 0.5, -4.0), 10, 0.5, m["ip_heat"], 2, 0.15, 0.9, 20.0, 60, (16.0, 3.0))
    OV.data(m, root, 1, n=3, bridge=True)
    tags(root, [
        [(f"~{n} big slabs per wafer", (0.0, BY + 1.0, 0.0)), ("edge loss grows with size", (110.0, BY + 0.6, 90.0))],
        [("one supplier does most of it", (-34.0, 2.0, 0.0)), ("HBM supply is the other limit", (D.HBM_X[1] - 1.0, D.HBM_Y[1], 0.0))],
        [("1,000 W+ through one slab", (0.0, D.LID[1] + 10.0, -4.0)), ("big slabs warp", (40.0, D.SUB_T[1], 0.0))],
    ])
    camera_path(root, [frame((0.0, BY, 0.0), 320.0, 0.1, 1.0, pad=1.0), frame((4.0, 2.0, -2.0), 80.0, 0.22, 0.24),
                       frame((0.0, -2.0, -6.0), 125.0, 0.36, 0.30)])


SECTIONS = {str(i): f for i, f in enumerate([sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9], 1)}


def run_section(n):
    name = f"section_{n}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    SECTIONS[n](m, root)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in SECTIONS:
        raise SystemExit("usage: blender -b --python pkg_interposer_sections.py -- <1-9>")
    run_section(argv[0])
