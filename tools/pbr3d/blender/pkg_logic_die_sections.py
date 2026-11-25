"""The LOGIC DIE page's nine numbered sections (PACKAGING tab). Section N illustrates heading N of
tui/src/screens/diagrams_pages/PKG_LOGIC_DIE.txt (the tenth, Sources, is text only). Three beats
each, one beat is 8 s.

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_logic_die_sections.py -- <n>

Writes assets/pkg_logic_die_section_<n>.glb. Parts come from pkg_logic_die_detail.py: the cut-open
package, the die cross-section block (die_block), the wafer and the bridge close-up.

  1 what happens    the die in its package; the reticle field round it; two dies and their HBM
  2 the parts       the die cut open: bulk, transistors, the metal stack, pads and bumps
  3 in order        wafer of fields; wafer test marks the good dies; a known-good die drops onto the interposer
  4 reticle limit   one field; the die filling 95% of it; the High-NA half field
  5 yield           defects land; big dies lost; chiplets lose less
  6 die-to-die      the bridge block: coarse vs fine bumps; the wires; traffic
  7 shoreline+heat  the outer edges lit; data to the HBM; heat out the top
  8 who makes it    each part lit with its makers
  9 chokepoints     reticle cap; a defect killing a die; the extra link to test
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_logic_die_detail as D  # noqa: E402
from pkg_logic_die_detail import frame, camera_path, run, rise, bx, empty, present  # noqa: E402
import pkg_logic_die_overview as OV  # noqa: E402
import pkg_logic_die_zooms as Z  # noqa: E402

PAGE = "pkg_logic_die"
BEATS = 3
WC = D.WAFER_C
span = Z.span
tags = Z.tags


def glow_box(m, root, name, lo, hi, mt, intervals):
    g = empty(name, root)
    bx(f"{name}_b", lo, hi, m[mt], g)
    show(g, intervals)
    return g


V_ALL = OV.V_ALL
V_TOP = OV.V_TOP


def sec1(m, root):
    s = D.package(m, root, lid_on=False, floorplan=True)
    OV.reticle(m, root, span(1, 0.0, 3, 0.0))
    OV.data(m, root, [2])
    OV.d2d(m, root, [2], n=4)
    tags(root, [
        [("the logic die: the GPU itself", (14.0, D.DIE[1], -10.0)), ("on its interposer", (-40.0, D.IP[1], 0.0)),
         ("HBM beside it", (-32.5, D.HBM_Y[1], -16.0))],
        [("RETICLE LIMIT: 26 x 33 mm", (26.6, D.DIE[1] + 0.4, -16.0)), ("DIE SIZE: right up against it", (14.0, D.DIE[1] + 0.4, -33.0))],
        [("CHIPLETS: two dies", (-13.0, D.DIE[1], -20.0)), ("DIE-TO-DIE link", (0.0, D.UB[1], 0.0)), ("HBM on the edges", (-30.0, D.IP[1], 0.0))],
    ])
    camera_path(root, [V_ALL, V_TOP, frame((0.0, 4.0, -6.0), 80.0, 0.25, 0.30)])


def sec2(m, root):
    g, p = D.die_block(m, root)
    ox, oy, _ = D.BLOCK_O
    for k, x in enumerate((-20.0, -2.0, 16.0)):
        run(root, f"s2_sig{k}", D.block_signal(p, ox + x), 4, 0.6, m["data"], [1, 2], 0.05 + 0.1 * k, 0.85, 60)
    run(root, "s2_pw", D.block_signal(p, ox + 25.0), 4, 0.8, m["power"], 2, 0.0, 0.8, 60)
    x0, x1 = p["x"]
    tags(root, [
        [("bulk silicon (backside, to the TIM)", p["bulk"]), ("transistor layer", p["dev"]), ("metal stack: ~15 levels", p["global"]),
         ("microbumps", p["bump"])],
        [("FinFET fins", (x0 + 4.0, p["dev_y"] + 0.8, 0.0)), ("gates", (x0 + 10.0, p["dev_y"] - 0.4, -1.0)),
         ("M1: tens of nm pitch", p["local"])],
        [("thick global levels carry power", p["global"]), ("fine local levels wire gates", p["local"]),
         ("pads + bumps to the interposer", p["pad"])],
    ])
    camera_path(root, [
        frame((ox, oy + 18.0, -4.0), 80.0, 0.30, 0.22),
        frame((x0 + 10.0, p["dev_y"], 0.0), 26.0, 0.25, 0.15, min_d=20.0),
        frame((ox + 10.0, oy + 10.0, 0.0), 50.0, 0.15, 0.10),
    ])


def sec3(m, root):
    w, rects = D.wafer(m, root)
    dg, pts = D.defects(m, root, "def", n=18)
    bad = D.hit(rects, pts)
    good = set(range(len(rects))) - bad
    show(dg, span(1, 0.0, 2, 0.0))
    show(D.marks(m, root, "good", rects, "field_good", WC[1] + 0.55, good), span(1, 0.3, 2, 0.0))
    show(D.marks(m, root, "bad", rects, "field_bad", WC[1] + 0.55, bad), span(1, 0.3, 2, 0.0))
    s = D.package(m, root, lid_on=False, floorplan=True)
    d0 = s["dies"][1]
    key(d0, F(2, 0.0), "location", P(0.0, 40.0, 0.0), linear=True)
    key(d0, F(2, 0.15), "location", P(0.0, 40.0, 0.0), linear=True)
    key(d0, F(2, 0.6), "location", P(0.0, 0.0, 0.0), linear=True)
    fx, fz = WC[0], WC[2]
    tags(root, [
        [("1 design fills one field", (fx + 26.0, WC[1] + 0.8, fz + 16.0)), ("2 exposed field by field", (WC[0] - 110.0, WC[1], WC[2] + 40.0))],
        [("3 wafer test: good", (rects[min(good)][0], WC[1] + 0.8, rects[min(good)][1])), ("bad: one defect", (pts[2][0], WC[1] + 1.0, pts[2][1]))],
        [("4 KNOWN GOOD DIE only", (14.0, D.DIE[1] + 2.0, -10.0)), ("5 bonded beside its HBM", (32.5, D.HBM_Y[1], -16.0))],
    ])
    camera_path(root, [Z.V_WAFER, frame((WC[0], WC[1], WC[2]), 260.0, 0.15, 0.95, pad=1.0), frame((10.0, 8.0, -12.0), 90.0, 0.35, 0.45)])


def sec4(m, root):
    D.wafer(m, root)
    fx, fz = WC[0], WC[2]
    Z.frame_bars(m, root, "s4_field", fx, fz, 26.0, 33.0, WC[1] + 0.5, "reticle", span(0, 0.0, 3, 0.0))
    glow_box(m, root, "s4_die", (fx + 0.6, WC[1] + 0.6, fz + 0.6), (fx + 25.4, WC[1] + 1.3, fz + 32.4), "test", span(1, 0.0, 2, 0.0))
    Z.frame_bars(m, root, "s4_half", fx, fz, 26.0, 16.5, WC[1] + 1.4, "power", beat(2), t=0.6)
    glow_box(m, root, "s4_overflow", (fx + 0.6, WC[1] + 0.6, fz + 17.0), (fx + 25.4, WC[1] + 1.3, fz + 32.4), "field_bad", beat(2))
    tags(root, [
        [("26 mm", (fx + 13.0, WC[1] + 1.0, fz)), ("33 mm", (fx + 26.8, WC[1] + 1.0, fz + 16.5)), ("858 mm2", (fx + 13.0, WC[1] + 1.0, fz + 16.5))],
        [("H100: ~814 mm2", (fx + 13.0, WC[1] + 1.4, fz + 16.0)), ("~95% of the field", (fx + 26.0, WC[1] + 1.0, fz + 30.0))],
        [("High-NA EUV: 26 x 16.5 mm", (fx + 26.6, WC[1] + 1.8, fz + 8.0)), ("this half no longer prints", (fx + 13.0, WC[1] + 1.4, fz + 25.0))],
    ])
    camera_path(root, [Z.V_FIELD, frame((fx + 13.0, WC[1], fz + 16.5), 56.0, 0.15, 0.95), frame((fx + 13.0, WC[1], fz + 16.5), 60.0, 0.05, 1.05)])


def sec5(m, root):
    Z.zoom_b(m, root)


def sec6(m, root):
    Z.zoom_c(m, root)


def sec7(m, root):
    s = D.package(m, root, floorplan=True)
    present(s["lid"], beat(2))
    Z.shoreline(m, root, beat(0))
    OV.data(m, root, [1])
    for g in s["hot"]:
        show(g, beat(2))
    OV.heat(m, root, [2], n=7)
    tags(root, [
        [("HBM SHORELINE: the die's edge", (-26.0, D.DIE[1] + 0.5, -24.0)), ("two stacks per edge here", (-32.5, D.HBM_Y[1], -16.0))],
        [("data through the RDL", (-28.0, D.IP[1] - 0.3, 0.0)), ("~8 TB/s memory (B200)", (30.0, D.HBM_Y[1], -6.0))],
        [("HEAT: the logic die makes most of it", (-13.0, D.LID[1], -6.0)), ("cooled from the top", (0.0, D.LID[1], -20.0))],
    ])
    camera_path(root, [OV.V_TOP, OV.V_HBM, OV.V_HEAT])


def sec8(m, root):
    s = D.package(m, root, lid_on=False, floorplan=True)
    glow_box(m, root, "s8_die", (D.DIES[0][0], D.DIE[1], D.DIE_Z), (D.DIES[1][1], D.DIE[1] + 0.3, 0.0), "test", beat(0))
    glow_box(m, root, "s8_ip", (-D.IP_HALF, D.IP[1], D.BACK), (D.IP_HALF, D.IP[1] + 0.15, 0.0), "slit", beat(1))
    tags(root, [
        [("NVIDIA, AMD: design the dies", (-13.0, D.DIE[1] + 0.4, -14.0)), ("TSMC: builds them (N4/N3)", (13.0, D.DIE[1] + 0.4, -14.0)),
         ("Intel, Samsung: own fabs", (13.0, D.DIE[1], -28.0))],
        [("TSMC CoWoS: interposer + bonding", (-40.0, D.IP[1], -10.0)), ("HBM: SK hynix, Samsung, Micron", (-32.5, D.HBM_Y[1], -16.0))],
        [("ABF film: Ajinomoto", (-50.0, D.SUB[1] - 1.0, 0.0)), ("substrates: Ibiden, Unimicron", (-30.0, -2.7, 0.0))],
    ])
    camera_path(root, [OV.V_TOP, frame((-20.0, 4.0, -10.0), 70.0, 0.35, 0.40), frame((-30.0, -2.0, 0.0), 50.0, 0.20, 0.10)])


def sec9(m, root):
    s = D.package(m, root, lid_on=False, floorplan=True)
    OV.reticle(m, root, beat(0))
    dg = empty("s9_def", root)
    from sand_overview import ball
    ball("s9_defect", (14.0, D.DIE[1] + 0.6, -12.0), 1.4, m["defect"], dg, 12)
    show(dg, beat(1))
    glow_box(m, root, "s9_bad", (D.DIES[1][0], D.DIE[1] + 0.1, D.DIE_Z), (D.DIES[1][1], D.DIE[1] + 0.35, 0.0), "field_bad", span(1, 0.3, 2, 0.0))
    OV.d2d(m, root, [2], n=8)
    tags(root, [
        [("reticle caps one die", (26.6, D.DIE[1] + 0.4, -16.0)), ("growth = more dies", (-13.0, D.DIE[1], -16.0))],
        [("one defect", (14.0, D.DIE[1] + 1.2, -12.0)), ("the whole die is scrap", (14.0, D.DIE[1] + 0.4, -26.0))],
        [("every link: design + test", (0.0, D.UB[1], 0.0)), ("bridge yield adds risk", (0.0, D.IP_SI[0] + 0.6, 0.0))],
    ])
    camera_path(root, [V_TOP, frame((14.0, 8.0, -16.0), 44.0, 0.20, 0.95, min_d=30.0), OV.V_BRIDGE])


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
        raise SystemExit("usage: blender -b --python pkg_logic_die_sections.py -- <1..9>")
    run_section(argv[0])
