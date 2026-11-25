"""The MICROBUMP page's nine numbered sections. Section N illustrates heading N of
tui/src/screens/diagrams_pages/PKG_MICROBUMP.txt (the tenth, Sources, is text only). Three beats
each, one beat 8 s; every one a real scene with its own cut-aways, beads and cameras.

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_microbump_sections.py -- <n>

Writes assets/pkg_microbump_section_<n>.glb.

  1 what happens    the package cut open: microbumps, then C4 and BGA, then hybrid bonds
  2 the parts       one microbump at 10x: solder and IMC; nickel, pillar, UBM; RDL, TSV, BEOL
  3 in order        plate and cap; place and reflow; underfill
  4 bump pitch      C4 / microbump / hybrid side by side; density; the solder wall
  5 hybrid bonding  polished dished pads; oxide bonds at room temperature; anneal closes copper
  6 underfill       heat; the substrate bows and corner joints strain; underfill shares it
  7 current         electrons through a joint; a void grows; more bumps share
  8 who makes it    TSMC on the interposer and dies; ASE / Amkor on bumps and flip-chip; Besi
  9 chokepoints     solder bridges; a particle under a hybrid bond; a cracked joint
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show, empty  # noqa: E402
from sand_zooms import start  # noqa: E402
import pkg_microbump_detail as K  # noqa: E402
import pkg_microbump_zooms as Z  # noqa: E402
from power_vrm_detail import camera_path, run, rise, bx  # noqa: E402

PAGE = "pkg_microbump"
BEATS = 3
span, tags = Z.span, Z.tags


def sec1(m, root):
    s = K.stack(m, root, hybrid=True)
    K.lower(s["die"], [(F(2, 0.0), 0.0), (F(2, 0.4), -0.96)])
    show(s["ub_joint"], span(0, 0.0, 2, 0.3))
    show(s["ip_pads"], span(0, 0.0, 2, 0.3))
    show(s["hyb"], span(2, 0.3, 3, 0.0))
    show(s["uf_die"], [])
    show(s["uf_c4"], [])
    Z_power(m, root)
    p = s["pts"]
    tags(root, [
        [("MICROBUMP: die to interposer", p["ub"]), ("CU PILLAR + solder cap", (K.UB_XS[10], 8.9, 0.3)), ("~40 um pitch", (K.UB_XS[14], 8.2, 0.3))],
        [("C4 BUMP: interposer to substrate", p["c4"]), ("BGA: substrate to board", p["bga"]), ("TSV links them", p["tsv"])],
        [("HYBRID BOND: copper to copper", (-16.0, 8.1, 0.2)), ("<=10 um, no solder", (-21.0, 8.1, 0.2))],
    ])
    camera_path(root, [
        K.frame((-18.0, 8.4, 0.0), 12.0, 0.20, 0.12),
        K.frame((-20.0, -1.0, 0.0), 34.0, 0.15, 0.08),
        K.frame((-18.0, 8.6, 0.0), 10.0, 0.20, 0.12),
    ])


def Z_power(m, root):
    run(root, "s1_pwr", K.power_path(), 6, 0.3, m["pwr"], [1], 0.0, 0.8, 70)


def sec2(m, root):
    s = 10.0
    g, pt = K.bench_joint(m, root, (0.0, 0.0, 0.0), s, "s2j")
    run(root, "s2_e", [(0.0, 2.0 * s, 0.3), (0.0, -1.2 * s, 0.3)], 6, 0.03 * s, m["pwr"], [0, 1, 2], 0.0, 0.85, 70)
    tags(root, [
        [("interposer Cu pad", pt["pad"]), ("IMC: Cu6Sn5", pt["imc0"]), ("SnAg solder", pt["sol"]), ("IMC: Ni3Sn4", pt["imc1"])],
        [("nickel barrier", pt["ni"]), ("CU PILLAR ~25 um", pt["cu"]), ("UBM seed (Ti/Cu)", pt["ubm"]), ("Al pad", pt["al"])],
        [("polyimide passivation", pt["pi"]), ("die BEOL wiring", pt["beol"]), ("RDL", pt["rdl"]), ("TSV", pt["tsv"])],
    ])
    camera_path(root, [
        K.frame((0.0, 0.25 * s, 0.0), 1.1 * s, 0.25, 0.10),
        K.frame((0.0, 0.8 * s, 0.0), 1.2 * s, 0.25, 0.10),
        K.frame((0.0, 0.3 * s, 0.0), 3.0 * s, 0.30, 0.15),
    ])


def sec3(m, root):
    s = 3.0
    pt = Z.build_assembly(m, root, s)
    tags(root, [
        [("1 copper pillars plated", (pt["cu"][0], pt["cu"][1] + 2.2 * s, 0.0)), ("2 solder caps on top", (pt["xs"][0], 2.55 * s, 0.0))],
        [("3 placed face down", pt["die"]), ("4 reflow melts the joints", pt["sol"])],
        [("5 underfill flows in", pt["uf"]), ("and cures", (pt["xs"][2], 0.6 * s, 0.0))],
    ])
    camera_path(root, [
        K.frame((0.0, 2.6 * s, 0.0), 4.4 * s, 0.30, 0.20),
        K.frame((0.0, 0.6 * s, 0.0), 3.6 * s, 0.15, 0.05),
        K.frame((-0.8 * s, 0.6 * s, -0.3 * s), 3.6 * s, 0.45, 0.25),
    ])


def sec4(m, root):
    s = 4.0
    pt = Z.build_ladder(m, root, s)
    # density: a pad grid at 2x pitch beside one at 1x, same area
    o = (0.0, 0.0, -8.0 * s)
    gg = empty("s4_grid", root)
    for k, (pitch, x0) in enumerate(((1.0, -5.0), (0.5, 1.0))):
        n = int(round(4.0 / pitch))
        for i in range(n):
            for j in range(n):
                x, z = (x0 + pitch * (i + 0.5)) * s, o[2] + pitch * (j + 0.5) * s
                K.cyl(f"s4_g{k}_{i}_{j}", x, 0.0, 0.15 * s, z, 0.18 * pitch * s, m["copper"], gg, 12)
        bx(f"s4_sq{k}", (x0 * s, -0.1 * s, o[2]), ((x0 + 4.0) * s, 0.0, o[2] + 4.0 * s), m["oxide"], gg)
    br, rows = K.bridges(m, root, (12.0 * s, 0.0, 0.0), s, [1.0, 0.62])
    K.glow_bridges(m, root, rows, 1, s, 0.0, "s4_br", span(2, 0.3, 3, 0.0))
    tags(root, [
        [("C4 ~150 um", pt["c4"]), ("microbump ~40 um", pt["ub"]), ("hybrid <=10 um", pt["hb"])],
        [("16 joints", (-3.0 * s, 0.2 * s, o[2] + 4.0 * s)), ("halve the pitch: 64", (3.0 * s, 0.2 * s, o[2] + 4.0 * s)), ("density ~ 1 / pitch^2", (0.0, 0.2 * s, o[2]))],
        [("solder bridges near 10 um", (rows[1][0][3], 0.7 * s, rows[1][1])), ("the solder wall", (rows[0][0][-1], 0.3 * s, 0.0))],
    ])
    camera_path(root, [
        K.frame((-1.0 * s, 0.8 * s, 0.0), 8.0 * s, 0.12, 0.10),
        K.frame((-1.0 * s, 0.0, o[2] + 2.0 * s), 11.0 * s, 0.0, 0.9),
        K.frame((rows[0][0][3], 0.3 * s, -1.5 * s), 7.0 * s, 0.25, 0.40),
    ])


def sec5(m, root):
    s = 6.0
    g, up, hp = K.hybrid(m, root, (0.0, 0.0, 0.0), s, "s5h", gap=0.0, dish=True)
    K.lower(up, [(0, 1.2 * s), (F(1, 0.0), 1.2 * s), (F(1, 0.4), 0.0)])
    flat = empty("s5_flat", root)
    bx("s5_flat_b", (-hp["w"], -0.01 * s, -0.02), (hp["w"], 0.01 * s, 0.06), m["flat"], flat)
    show(flat, span(1, 0.4, 2, 0.3))
    # anneal: copper expands into the dish; the gaps close (a glowing copper seam)
    seam = empty("s5_seam", root)
    for x in hp["pads"]:
        bx(f"s5_seam{x:.1f}", (x - 0.22 * s, -0.02 * s, -0.01), (x + 0.22 * s, 0.02 * s, 0.08), m["melt"], seam)
    show(seam, span(2, 0.3, 3, 0.0))
    rise(root, "s5_heat", (0.0, -1.0 * s, 0.4 * s), 10, 0.05 * s, m["heat"], 2, 0.0, 0.7, 2.4 * s, 50, (hp["w"] * 0.9, 0.0))
    run(root, "s5_cmp", [(-hp["w"], 0.05 * s, 0.3), (hp["w"], 0.05 * s, 0.3)], 8, 0.04 * s, m["sig"], 0, 0.0, 0.8, 50)
    tags(root, [
        [("CMP: oxide polished flat", hp["ox"]), ("copper pads dished a few nm", hp["cu"])],
        [("oxide bonds to oxide", (hp["w"] * 0.8, 0.0, 0.0)), ("room temperature", (-hp["w"] * 0.8, 0.0, 0.0))],
        [("anneal: copper expands", hp["cu"]), ("Cu-Cu bond, no gap, no solder", (hp["pads"][1], 0.0, 0.0))],
    ])
    camera_path(root, [
        K.frame((0.0, 0.6 * s, 0.0), 4.0 * s, 0.25, 0.25),
        K.frame((0.0, 0.0, 0.0), 3.0 * s, 0.15, 0.06),
        K.frame((hp["pads"][3], 0.0, 0.0), 1.6 * s, 0.15, 0.06),
    ])


def sec6(m, root):
    st = Z.build_stress(m, root)
    rise(root, "s6_heat", (0.0, 6.4, -4.0), 10, 0.3, m["heat"], [0, 1], 0.05, 0.85, 6.0, 50, (10.0, 4.0))
    Z.bow(st["sub"], 1, 0.0, 0.5, 2.0, back=(F(2, 0.1), F(2, 0.5)))
    for x in (st["xs"][0], st["xs"][-1]):
        K.glow_box(m, root, f"s6_st{x}", (x - 1.25, -2.4, -0.2), (x + 1.25, 0.0, 0.35), m["stress"], span(1, 0.4, 2, 0.2))
    uf = empty("s6_uf", root)
    bx("s6_uf_b", (-19.0, -2.4, -10.0), (19.0, 0.0, -0.05), m["uf"], uf)
    uf2 = empty("s6_uf2", root)
    bx("s6_uf2_b", (-12.5, 2.4, -10.0), (12.5, 3.6, -0.05), m["uf"], uf2)
    show(uf, span(2, 0.15, 3, 0.0))
    show(uf2, span(2, 0.15, 3, 0.0))
    tags(root, [
        [("die heats", (0.0, 6.2, -4.0)), ("silicon ~3 ppm/C", (16.0, 1.2, 0.0)), ("substrate ~15+ ppm/C", (20.0, -5.0, 0.0))],
        [("substrate grows more: it bows", (-20.0, -6.0, 0.0)), ("outer joints take the shear", (st["xs"][-1], -1.2, 0.4))],
        [("UNDERFILL locks the levels", (0.0, -1.2, 0.0)), ("stress spread over the area", (8.0, 3.0, 0.0)), (">10x C4 cycle life", (st["xs"][0], -1.2, 0.4))],
    ])
    camera_path(root, [
        K.frame((0.0, 1.0, 0.0), 44.0, 0.30, 0.30),
        K.frame((14.0, -2.0, 0.0), 26.0, 0.10, 0.04),
        K.frame((0.0, 0.0, 0.0), 42.0, 0.20, 0.10),
    ])


def sec7(m, root):
    s = 8.0
    pt, xs = Z.build_current(m, root, s)
    tags(root, [
        [("thousands of power bumps", pt["die"]), ("each a few hundred mA", pt["cu"]), ("electron flow", pt["sol"])],
        [("ELECTROMIGRATION", pt["imc1"]), ("atoms pushed by the electron wind", pt["ni"]), ("a void opens at the cathode", pt["sol"])],
        [("split the current", (xs[2], 1.1 * s, 0.0)), ("lower density per bump", (xs[-1], 0.5 * s, 0.0))],
    ])
    camera_path(root, [
        K.frame((0.0, 0.5 * s, 0.0), 2.8 * s, 0.35, 0.20),
        K.frame((0.0, 0.4 * s, 0.0), 0.9 * s, 0.10, 0.06),
        K.frame((3.5 * s, 0.45 * s, 0.0), 3.0 * s, 0.25, 0.15),
    ])


def sec8(m, root):
    s = K.stack(m, root, hybrid=True)
    show(s["hyb"], span(2, 0.0, 3, 0.0))
    show(s["ub_joint"], span(0, 0.0, 2, 0.0))
    show(s["ip_pads"], span(0, 0.0, 2, 0.0))
    K.lower(s["die"], [(F(2, 0.0), -0.96)])
    p = s["pts"]
    tags(root, [
        [("TSMC (TSM): CoWoS interposer", p["ip"]), ("TSMC: microbumps + dies", p["ub"]), ("SK hynix / Micron / Samsung: HBM", p["hbm"])],
        [("ASE (ASX): bumping, flip-chip", p["c4"]), ("Amkor (AMKR): assembly + test", p["bga"]), ("substrates: Ibiden, Unimicron", p["sub"])],
        [("TSMC SoIC: hybrid bonds", (-12.0, 8.1, 0.2)), ("Besi: hybrid bonders (not sourced here)", p["logic"])],
    ])
    camera_path(root, [
        K.frame((-2.0, 7.0, -2.0), 52.0, 0.35, 0.30),
        K.frame((-4.0, -3.0, 0.0), 70.0, 0.25, 0.10),
        K.frame((-16.0, 9.0, -2.0), 24.0, 0.30, 0.30),
    ])


def sec9(m, root):
    s = 3.0
    br, rows = K.bridges(m, root, (0.0, 0.0, 0.0), s, [0.62])
    K.glow_bridges(m, root, rows, 0, s, 0.0, "s9_br", span(0, 0.3, 1, 0.0))
    # a particle trapped between hybrid-bond faces holds them apart: an unbonded void
    hx = 14.0 * s
    g, up, hp = K.hybrid(m, root, (hx, 0.0, 0.0), s, "s9h", gap=0.0, dish=False)
    K.lower(up, [(0, 0.15 * s)])
    K.ball("s9_part", (hx, 0.075 * s, 0.0), 0.075 * s, m["fail"], g, 12)
    vd = empty("s9_void", root)
    bx("s9_void_b", (hx - 1.6 * s, 0.0, -0.01), (hx + 1.6 * s, 0.15 * s, 0.05), m["void"], vd)
    show(vd, span(1, 0.3, 2, 0.0))
    # a cracked joint at the IMC
    jx = 28.0 * s
    jg, jp = K.bench_joint(m, root, (jx, 0.0, 0.0), s, "s9j")
    ck = empty("s9_crack", root)
    bx("s9_crack_b", (jx - 0.27 * s, 0.385 * s, -0.01), (jx + 0.15 * s, 0.405 * s, 0.06), m["fail"], ck)
    show(ck, span(2, 0.3, 3, 0.0))
    tags(root, [
        [("solder bridges below ~10 um", (rows[0][0][3], 0.7 * s, 0.0)), ("a short between neighbours", (rows[0][0][5], 0.3 * s, 0.0))],
        [("one particle: an unbonded void", (hx, 0.1 * s, 0.0)), ("needs near-perfect flatness", hp["ox"])],
        [("thermal cycling cracks the IMC", jp["imc1"]), ("weak underfill: early failure", jp["sol"])],
    ])
    camera_path(root, [
        K.frame((rows[0][0][3], 0.3 * s, 0.0), 4.6 * s, 0.20, 0.30),
        K.frame((hx, 0.1 * s, 0.0), 4.4 * s, 0.15, 0.10),
        K.frame((jx, 0.5 * s, 0.0), 2.0 * s, 0.25, 0.10),
    ])


SECTIONS = {str(i + 1): f for i, f in enumerate((sec1, sec2, sec3, sec4, sec5, sec6, sec7, sec8, sec9))}


def run_section(n):
    name = f"section_{n}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(K.materials())
    SECTIONS[n](m, root)
    K.finish(root, name, PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in SECTIONS:
        raise SystemExit("usage: blender -b --python pkg_microbump_sections.py -- <1-9>")
    run_section(argv[0])
