"""The SUBSTRATE page's nine numbered sections (picture-and-panel template). Section N illustrates
heading N of tui/src/screens/diagrams_pages/PKG_SUBSTRATE.txt (the tenth, Sources, is text only).
Three beats each, one beat is 8 s.

Run one section per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_substrate_sections.py -- <n>

Writes assets/pkg_substrate_section_<n>.glb. The cut-open stack is pkg_substrate_detail.scene;
close-ups (one C4 joint, one BGA joint, a microvia column, two cores, an ABF roll, share bars,
footprints to scale) are built high above it at BY and drawn large.

  1 what happens    the stack; fine bumps on top; signals out to coarse balls
  2 the parts       the laminate's layers; one C4 and one BGA joint cut open; organic vs glass core
  3 in order        core + PTH; build-up layers one by one (via column); resist, pads, bumps
  4 ABF film        the roll; the film in every layer; one supplier's share
  5 layers + size   counting layers; footprints to scale; stacked vs staggered microvias
  6 warpage, glass  bowing in reflow; strained corner joints; a glass core beside an organic one
  7 fan-out         the bump field; signals across layers; power and signals into the balls
  8 who makes it    share bars; the film maker; makers tagged on the stack
  9 chokepoints     one film supplier; layer-count yield; warpage at size
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_substrate_detail as D  # noqa: E402
from pkg_substrate_detail import frame, camera_path, run, rise, present, empty, bead, bx  # noqa: E402
import pkg_substrate_overview as OV  # noqa: E402
import pkg_substrate_zooms as Z  # noqa: E402

PAGE = "pkg_substrate"
BEATS = 3
BY = 400.0


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def after(b, u):
    return [(F(b, u), F(BEATS, 0))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def only(g, beats):
    present(g, [iv for b in beats for iv in beat(b)])
    return g


def warp_strain(g, beats, u=0.45):
    D.show_strain(g, [(F(b, u), F(b + 1, 0)) for b in beats])


V_WARP = frame((0.0, 20.0, -40.0), 330.0, 0.18, 0.08, pad=1.0)


# ---- 1 what happens -------------------------------------------------------------------------


def sec1(m, root, s):
    show(s["sub"]["lit"], beat(2))
    OV.signal_beads(m, root, s, [1], n=2, u0=0.2)
    OV.signal_beads(m, root, s, [2], n=4)
    tags(root, [
        [("PACKAGE SUBSTRATE", D.A_TOPBU), ("interposer + die above", D.A_IP), ("server board below", (-180.0, D.BOARD_TOP, 0.0))],
        [("C4 bumps: ~150 um pitch", D.A_C4), ("signals enter here", (D.ROUTES[1][0], D.C4_Y, 0.0)), ("resist openings", D.A_SR)],
        [("BUILD-UP LAYERS route out", (96.0, D.mid(D.cu_y(1, 4)), 0.0)), ("through the CORE", (120.0, D.CORE0 + 6.0, 0.0)),
         ("BGA: ~1 mm pitch", (120.0, D.BGA_Y, 0.0))],
    ])
    camera_path(root, [D.V_ALL, frame((32.0, 66.0, -10.0), 90.0, 0.20, 0.40), D.V_FACE_R])


# ---- 2 the parts -------------------------------------------------------------------------------


def sec2(m, root, s):
    cj = only(D.c4_joint(m, root, (-80.0, BY, 0.0), 1.0, "s2c"), [1])
    bj = only(D.bga_joint(m, root, (80.0, BY - 10.0, 0.0), 1.0, "s2b"), [1])
    cp, org, gl = D.core_pair(m, root, (0.0, BY, 0.0), 1.0, "s2p")
    only(cp, [2])
    tags(root, [
        [("ABF FILM: the insulator", (-60.0, D.mid(D.abf_y(1, 4)), 0.0)), ("BUILD-UP LAYERS", D.A_TOPBU), ("CORE", D.A_CORE),
         ("solder resist", D.A_SR)],
        [("C4: bump on a copper pad", (-80.0, BY + 42.0, 0.0)), ("microvia under the pad", (-80.0, BY + 19.0, 0.0)),
         ("BGA ball to the board", (80.0, BY + 12.0, 0.0)), ("board pad", (80.0, BY - 12.0, 0.0))],
        [("organic core: glass cloth, drilled", (-60.0, BY + 30.0, -10.0)), ("GLASS CORE: flat, fine vias", (60.0, BY + 30.0, -10.0)),
         ("through-glass vias", (64.0, BY + 15.0, 0.0))],
    ])
    camera_path(root, [D.V_FACE, frame((0.0, BY + 30.0, -10.0), 240.0, 0.15, 0.12, pad=1.0),
                       frame((0.0, BY + 15.0, -10.0), 230.0, 0.20, 0.20, pad=1.0)])


# ---- 3 in order ---------------------------------------------------------------------------------


def sec3(m, root, s):
    Z.build_order(s, 0, 2, 2)  # beat 1 is the close-up; the stack builds up in beat 2
    for n in range(1, 5):
        vc = D.via_column(m, root, (0.0, BY, 0.0), 1.5, False, f"s3v{n}", n)
        present(vc, [(F(1, 0.22 * (n - 1)), F(1, 0.22 * n) if n < 4 else F(2, 0))])
    tags(root, [
        [("1 core with copper foil", D.A_CORE), ("drill + plate through-holes", D.A_PTH), ("plug them with resin", (-24.0, D.CORE1 - 6.0, 0.0))],
        [("2 laminate ABF film", (40.0, BY + 6.0, -10.0)), ("3 laser-drill, plate copper", (0.0, BY + 18.0, 0.0)),
         ("4 repeat, layer on layer", (-40.0, BY + 60.0, -10.0))],
        [("5 solder resist", D.A_SR), ("C4 pads on top", D.A_C4), ("BGA pads below", D.A_BGA)],
    ])
    camera_path(root, [frame((-80.0, 31.0, 0.0), 120.0, 0.18, 0.10),
                       frame((0.0, BY + 40.0, -10.0), 140.0, 0.30, 0.20),
                       frame((-40.0, 30.0, 0.0), 190.0, 0.25, 0.18)])


# ---- 4 ABF film --------------------------------------------------------------------------------


def sec4(m, root, s):
    rg = only(D.abf_roll(m, root, (0.0, BY, 0.0), 1.0, "s4r"), [0, 2])
    bars = empty("s4_bars", root)
    bx("s4_aji", (80.0, BY, -40.0), (104.0, BY + 95.0, -16.0), m["bar_a"], bars)
    bx("s4_rest", (112.0, BY, -40.0), (136.0, BY + 5.0, -16.0), m["bar_b"], bars)
    only(bars, [2])
    tags(root, [
        [("ABF: Ajinomoto Build-up Film", (40.0, BY + 5.0, -20.0)), ("epoxy + silica filler", (-30.0, BY + 4.0, -10.0)),
         ("on a PET carrier", (-50.0, BY + 1.0, 0.0))],
        [("ABF between every copper layer", (48.0, D.mid(D.abf_y(1, 3)), 0.0)), ("12 films here", D.A_TOPBU),
         ("in almost every GPU + CPU", (-80.0, D.mid(D.abf_y(-1, 3)), 0.0))],
        [("Ajinomoto ~95% (est.)", (92.0, BY + 95.0, -28.0)), ("everyone else", (124.0, BY + 5.0, -28.0)),
         ("one supplier: a chokepoint", (0.0, BY + 40.0, -60.0))],
    ])
    camera_path(root, [frame((0.0, BY + 18.0, -30.0), 150.0, 0.35, 0.32), D.V_TOPBU,
                       frame((40.0, BY + 40.0, -30.0), 220.0, 0.20, 0.20, pad=1.0)])


# ---- 5 layers and size -------------------------------------------------------------------------


def sec5(m, root, s):
    sq, at = D.size_squares(m, root, (0.0, BY, 0.0), 2.0, "s5q")
    only(sq, [1])
    st = only(D.via_column(m, root, (-60.0, BY, 0.0), 1.2, False, "s5st"), [2])
    sg = only(D.via_column(m, root, (60.0, BY, 0.0), 1.2, True, "s5sg"), [2])
    tags(root, [
        [("6 build-up layers on top", D.A_TOPBU), ("6 below: 12 here", D.A_BOTBU), ("AI GPUs: 12-20", (60.0, D.TOP, 0.0))],
        [("120 mm: big AI packages (est.)", at[120]), ("100 mm", at[100]), ("77.5 mm", at[77.5]), ("55 mm: a server CPU", at[55])],
        [("stacked microvias", (-60.0, BY + 58.0, 0.0)), ("staggered", (72.0, BY + 58.0, 0.0)), ("stacking saves room", (0.0, BY + 30.0, 0.0))],
    ])
    camera_path(root, [D.V_FACE, frame((0.0, BY + 10.0, -110.0), 280.0, 0.25, 0.70, pad=1.0),
                       frame((0.0, BY + 30.0, -10.0), 200.0, 0.10, 0.15, pad=1.0)])


# ---- 6 warpage and glass cores -----------------------------------------------------------------


def sec6(m, root, s):
    OV.hide_main(s, [])
    g, piv = OV.warp_scene(m, root, [0, 1], [(F(0, 0.0), 0.0), (F(0, 0.15), 0.0), (F(0, 0.6), -0.2),
                                             (F(1, 0.0), -0.2), (F(1, 0.4), 0.16)])
    rise(root, "s6_heat", (0.0, D.TOP, -40.0), 10, 1.3, m["heat"], 0, 0.05, 0.8, 40.0, 60, (120.0, 30.0))
    warp_strain(g, [1])
    cp, org, gl = D.core_pair(m, root, (0.0, BY, 0.0), 1.0, "s6p")
    only(cp, [2])
    tags(root, [
        [("WARPAGE: reflow heat", (0.0, D.TOP + 4.0, 0.0)), ("the big thin laminate bows", (120.0, D.TOP - 16.0, 0.0))],
        [("cooled, it bows back", (0.0, D.TOP + 4.0, 0.0)), ("corner balls strain or open", (150.0, -D.BGA_R, 0.0))],
        [("GLASS CORE: stiffer, flatter", (60.0, BY + 30.0, -10.0)), ("finer through-vias", (64.0, BY + 15.0, 0.0)),
         ("in development", (-60.0, BY + 30.0, -10.0))],
    ])
    camera_path(root, [V_WARP, frame((90.0, 10.0, -10.0), 160.0, -0.25, 0.05),
                       frame((0.0, BY + 15.0, -10.0), 230.0, 0.20, 0.20, pad=1.0)])


# ---- 7 fan-out ---------------------------------------------------------------------------------


def sec7(m, root, s):
    show(s["sub"]["lit"], span(1, 0.0, 3, 0.0))
    show(s["lit_planes"], beat(2))
    OV.signal_beads(m, root, s, [1, 2], n=4)
    OV.power_beads(m, root, [2], n=4)
    tags(root, [
        [("tens of thousands of bumps", (-24.0, D.C4_Y, -40.0)), ("~150 um apart", D.A_C4)],
        [("each signal: a via stack", (D.ROUTES[3][0], D.mid((D.CORE1, D.TOP)), 0.0)), ("a trace on its own layer", (96.0, D.mid(D.cu_y(1, 4)), 0.0)),
         ("a through-hole", (120.0, D.CORE0 + 6.0, 0.0))],
        [("power on the planes", D.A_PLANE), ("signals on traces", (96.0, D.mid(D.cu_y(1, 2)), 0.0)), ("balls ~1 mm apart", (96.0, D.BGA_Y, 0.0))],
    ])
    camera_path(root, [frame((24.0, 66.0, -20.0), 90.0, 0.25, 0.55), D.V_FACE_R, frame((0.0, 30.0, 0.0), 300.0, 0.10, 0.12, pad=1.0)])


# ---- 8 who makes it ----------------------------------------------------------------------------


def sec8(m, root, s):
    bg, who = D.share_bars(m, root, (0.0, BY, 0.0), 1.0, "s8b")
    only(bg, [0])
    only(D.abf_roll(m, root, (0.0, BY, 200.0), 1.0, "s8r"), [1])
    tags(root, [
        [(w, p) for w, p in who.items()] + [("FC-BGA share, % (one estimate)", (0.0, BY + 116.0, -12.0))],
        [("Ajinomoto: the ABF film", (40.0, BY + 5.0, 180.0)), ("~95% of GPU-grade (est.)", (-30.0, BY + 40.0, 140.0))],
        [("Ibiden, Unimicron, Shinko, AT&S, Nan Ya", D.A_TOPBU), ("film: Ajinomoto", (48.0, D.mid(D.abf_y(1, 3)), 0.0)),
         ("Ibiden: ~JPY 500B for new fabs", (-180.0, D.BOARD_TOP, 0.0))],
    ])
    camera_path(root, [frame((0.0, BY + 50.0, -12.0), 190.0, 0.15, 0.18, pad=1.0),
                       frame((0.0, BY + 18.0, 170.0), 150.0, 0.35, 0.32), D.V_ALL])


# ---- 9 chokepoints -----------------------------------------------------------------------------


def sec9(m, root, s):
    only(D.abf_roll(m, root, (0.0, BY, 0.0), 1.0, "s9r"), [0])
    stress = empty("s9_stress", root)
    for k in range(D.NL):
        c = D.cu_y(1, k)
        bx(f"s9_y{k}", (D.SX0, c[0] - 0.05, -1.0), (D.SX0 + 40.0, c[1] + 0.05, 0.06), m["stress"], stress)
    present(stress, beat(1))
    g, piv = OV.warp_scene(m, root, [2], [(F(0, 0.0), 0.0), (F(2, 0.1), 0.0), (F(2, 0.5), 0.18)])
    warp_strain(g, [2], 0.5)
    OV.hide_main(s, span(0, 0.0, 2, 0.0))
    tags(root, [
        [("one film supplier", (40.0, BY + 5.0, -20.0)), ("no second source at scale", (-30.0, BY + 40.0, -60.0))],
        [("every layer is a yield step", (-130.0, D.mid((D.CORE1, D.TOP)), 0.0)), ("few makers yield 14+ layers", D.A_TOPBU)],
        [("bigger packages warp more", (0.0, D.TOP + 4.0, 0.0)), ("corner joints at risk", (150.0, -D.BGA_R, 0.0))],
    ])
    camera_path(root, [frame((0.0, BY + 18.0, -30.0), 150.0, 0.35, 0.32), frame((-110.0, 50.0, 0.0), 90.0, 0.15, 0.10), V_WARP])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def run_section(n):
    name = f"section_{n}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    SECTIONS[n](m, root, s)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or not argv[0].isdigit() or int(argv[0]) not in SECTIONS:
        raise SystemExit("usage: blender -b --python pkg_substrate_sections.py -- <1-9>")
    run_section(int(argv[0]))
