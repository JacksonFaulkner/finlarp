"""Zoom-ins (a-e) for the LOGIC DIE page, three beats each, own cameras and motion
(diagrams_nodes/packaging/logic_die/zooms.rs):

  a the reticle limit        a wafer of 26 x 33 mm fields; the scanner slit sweeps one; High-NA halves it
  b yield and known-good dies  defects land; big dies lost; the same defects on chiplets lose less
  c chiplets and the bridge  the two dies' edges over the bridge; fine bumps; traffic across
  d HBM shoreline            PHY strip on the die edge; data out to the stacks; the edge as a budget
  e power and heat           current up from the board; through C4, TSV and bump; heat out the top

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_logic_die_zooms.py -- a

Writes assets/pkg_logic_die_zoom_<letter>.glb (and blender/pkg_logic_die_zoom_<letter>.blend).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, label, beat, show, key  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import pkg_logic_die_detail as D  # noqa: E402
from pkg_logic_die_detail import frame, camera_path, run, rise, bx, empty, present  # noqa: E402
import pkg_logic_die_overview as OV  # noqa: E402

PAGE = "pkg_logic_die"
BEATS = 3
WC = D.WAFER_C


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def centre_field():
    """The wafer field nearest the centre: (x0, z0) of a 26 x 33 field on the wafer grid."""
    return WC[0], WC[2]


def frame_bars(m, root, name, x0, z0, w, d, y, mt, intervals, t=0.8):
    g = empty(name, root)
    for n, lo, hi in (("l", (x0 - t, y, z0 - t), (x0, y + 0.6, z0 + d + t)), ("r", (x0 + w, y, z0 - t), (x0 + w + t, y + 0.6, z0 + d + t)),
                      ("b", (x0, y, z0 - t), (x0 + w, y + 0.6, z0)), ("f", (x0, y, z0 + d), (x0 + w, y + 0.6, z0 + d + t))):
        bx(f"{name}_{n}", lo, hi, m[mt], g)
    show(g, intervals)
    return g


def slit(m, root, name, x0, z0, w, d, y, b, u0=0.1, u1=0.8):
    """The scanner's exposure slit: a glowing band the width of the field sweeping its length."""
    g = empty(name, root)
    bx(f"{name}_band", (x0, y, z0), (x0 + w, y + 0.4, z0 + 3.0), m["slit"], g)
    key(g, F(b, 0.0), "location", P(0.0, 0.0, 0.0), linear=True)
    key(g, F(b, u0), "location", P(0.0, 0.0, 0.0), linear=True)
    key(g, F(b, u1), "location", P(0.0, 0.0, d - 3.0), linear=True)
    key(g, F(b + 1, 0) - 1, "location", P(0.0, 0.0, d - 3.0), linear=True)
    show(g, beat(b))
    return g


def shoreline(m, root, intervals):
    g = empty("shore", root)
    for side, (x0, x1) in zip((-1, 1), D.DIES):
        xe = x0 if side < 0 else x1
        bx(f"shore{side}", (xe - 0.5, D.DIE[1] + 0.1, D.DIE_Z), (xe + 0.5, D.DIE[1] + 0.5, 0.0), m["power"], g)
    show(g, intervals)
    return g


V_WAFER = frame((WC[0], WC[1], WC[2]), 300.0, 0.25, 0.95, pad=1.0)
V_FIELD = frame((WC[0] + 13.0, WC[1], WC[2] + 16.5), 70.0, 0.20, 0.85)


def zoom_a(m, root):
    D.wafer(m, root)
    fx, fz = centre_field()
    frame_bars(m, root, "a_field", fx, fz, 26.0, 33.0, WC[1] + 0.5, "reticle", span(0, 0.4, 3, 0.0))
    slit(m, root, "a_slit", fx, fz, 26.0, 33.0, WC[1] + 0.9, 1)
    frame_bars(m, root, "a_half", fx, fz, 26.0, 16.5, WC[1] + 1.2, "power", beat(2), t=0.6)
    tags(root, [
        [("300 mm wafer", (WC[0] - 120.0, WC[1], WC[2])), ("one reticle field", (fx + 26.0, WC[1] + 0.8, fz + 16.0)),
         ("printed field by field", (fx - 52.0, WC[1] + 0.5, fz - 30.0))],
        [("26 mm slit", (fx + 13.0, WC[1] + 1.2, fz + 2.0)), ("scans 33 mm", (fx + 26.8, WC[1] + 0.8, fz + 30.0)),
         ("858 mm2 max die", (fx + 13.0, WC[1] + 0.8, fz + 33.0))],
        [("High-NA field: 26 x 16.5 mm", (fx + 26.6, WC[1] + 1.6, fz + 8.0)), ("half the area", (fx + 13.0, WC[1] + 1.6, fz + 16.5)),
         ("H100 (814 mm2) would not fit", (fx, WC[1] + 0.8, fz + 30.0))],
    ])
    camera_path(root, [V_WAFER, V_FIELD, frame((fx + 13.0, WC[1], fz + 14.0), 64.0, 0.10, 1.0)])


def zoom_b(m, root):
    big, rb = D.wafer(m, root, cells=1, name="wbig")
    small, rs = D.wafer(m, root, cells=2, name="wsmall")
    dg, pts = D.defects(m, root, "def")
    show(dg, span(0, 0.3, 3, 0.0))
    hb, hs = D.hit(rb, pts), D.hit(rs, pts)
    show(D.marks(m, root, "bad_big", rb, "field_bad", WC[1] + 0.55, hb), span(1, 0.15, 2, 0.0))
    show(D.marks(m, root, "bad_small", rs, "field_bad", WC[1] + 0.55, hs), span(2, 0.35, 3, 0.0))
    present(big, span(0, 0.0, 2, 0.0))
    present(small, beat(2))
    gb, gs = len(rb) - len(hb), len(rs) - len(hs)
    yb, ys = round(100 * gb / len(rb)), round(100 * gs / len(rs))
    a = (WC[0] - 125.0, WC[1] + 1.0, WC[2] + 20.0)
    c = (WC[0] + 110.0, WC[1] + 1.0, WC[2] - 40.0)
    tags(root, [
        [("random defects", (pts[3][0], WC[1] + 1.0, pts[3][1])), ("same defect density everywhere", c)],
        [(f"big dies: {gb} of {len(rb)} good ({yb}%)", a), ("one defect scraps a whole die", (pts[5][0], WC[1] + 1.0, pts[5][1]))],
        [(f"chiplets: {gs} of {len(rs)} good ({ys}%)", a), ("same defects, less area lost", c),
         ("test each: KNOWN GOOD DIE", (pts[8][0], WC[1] + 1.0, pts[8][1]))],
    ])
    camera_path(root, [V_WAFER, frame((WC[0], WC[1], WC[2]), 260.0, 0.20, 0.9, pad=1.0), V_WAFER])


def zoom_c(m, root):
    g, p = D.bridge_block(m, root)
    for j in range(5):
        run(root, f"c_r{j}", D.bridge_path(j=j, sign=1), 3, 0.35, m["d2d"], [1, 2] if j < 2 else 2, 0.05 + 0.04 * j, 0.85, 45)
        run(root, f"c_l{j}", D.bridge_path(j=j, sign=-1), 3, 0.35, m["d2d"], 2, 0.1 + 0.04 * j, 0.9, 45)
    o = D.BRIDGE_O
    tags(root, [
        [("die 1", p["dieL"]), ("die 2", p["dieR"]), ("silicon bridge in the interposer", p["bridge"])],
        [("fine-pitch bumps over the bridge", p["fine"]), ("coarser bumps elsewhere", p["coarse"]),
         ("bridge wires", (o[0], o[1] + 7.6, o[2]))],
        [("thousands of wires in parallel", (o[0] - 8.0, o[1] + 6.0, o[2])), ("~10 TB/s die to die (B200)", p["dieR"]),
         ("software sees one GPU", p["dieL"])],
    ])
    camera_path(root, [
        frame((o[0], o[1] + 11.0, o[2] - 4.0), 62.0, 0.30, 0.30),
        frame((o[0] - 4.0, o[1] + 8.5, o[2]), 34.0, 0.18, 0.12, min_d=20.0),
        frame((o[0], o[1] + 8.0, o[2]), 40.0, 0.10, 0.18, min_d=24.0),
    ])


def zoom_d(m, root):
    s = D.package(m, root, lid_on=False, floorplan=True)
    shoreline(m, root, beat(2))
    OV.data(m, root, [1, 2], n=6)
    tags(root, [
        [("HBM PHY strip", (-25.5, D.DIE[1] + 0.1, -18.0)), ("HBM stacks", (-32.5, D.HBM_Y[1], -16.0)),
         ("SM tiles", (-12.0, D.DIE[1], -6.0))],
        [("1,024-bit bus per HBM3 stack", (-28.0, D.IP[1], 0.0)), ("RDL: micron-fine wires", (-30.0, D.IP[1] - 0.3, -1.0)),
         ("~8 TB/s total (B200)", (30.0, D.HBM_Y[1], -6.0))],
        [("shoreline: the outer edge", (-26.0, D.DIE[1] + 0.5, -24.0)), ("inner edge faces die 2", (0.0, D.DIE[1], -20.0)),
         ("edge length caps the stacks", (26.0, D.DIE[1] + 0.5, -24.0))],
    ])
    camera_path(root, [
        frame((-24.0, 7.0, -14.0), 40.0, 0.35, 0.75, min_d=30.0),
        frame((-26.0, 4.0, -2.0), 30.0, 0.28, 0.18, min_d=18.0),
        frame((0.0, 8.0, -16.0), 84.0, 0.0, 1.1),
    ])


def zoom_e(m, root):
    s = D.package(m, root)
    OV.power(m, root, [0, 1], n=5)
    for g in s["hot"]:
        show(g, beat(2))
    OV.heat(m, root, [2], n=7)
    tags(root, [
        [("board power planes", (-40.0, -9.6, 0.0)), ("up through the BGA", (-18.0, D.BGA_Y, 0.4)), ("~0.8 V core rail", (19.0, D.DIE[1], -4.0))],
        [("C4 bump", (9.0, D.C4_Y, 0.4)), ("TSV through the interposer", (9.0, 1.8, 0.0)), ("microbump into the metal stack", (19.0, D.UB[1], 0.4))],
        [("most of the package's heat", (-13.0, D.DIE[1], -6.0)), ("TIM: die to lid", (13.0, D.TIM[1], 0.0)),
         ("up into the cold plate (BOARD)", (0.0, D.LID[1], -8.0))],
    ])
    camera_path(root, [
        frame((-8.0, -2.0, 0.0), 70.0, 0.20, 0.12),
        frame((12.0, 1.5, 0.0), 22.0, 0.15, 0.08, min_d=16.0),
        frame((0.0, 8.0, -12.0), 75.0, 0.25, 0.28),
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
        raise SystemExit("usage: blender -b --python pkg_logic_die_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])
