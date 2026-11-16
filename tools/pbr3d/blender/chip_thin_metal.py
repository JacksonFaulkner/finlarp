"""CHIP pictures for THIN METAL: the overview, five zoom-ins (a-e) and ten numbered sections.

Run from the repo root (all scenes, or only the named ones after --):

    blender -b --factory-startup --python tools/pbr3d/blender/chip_thin_metal.py
    blender -b --factory-startup --python tools/pbr3d/blender/chip_thin_metal.py -- thin_metal_zoom_a

Each scene is the same whole chip (chip_kit.py) with the camera gliding into the part it is about.
Writes blender/chip_thin_metal*.blend and assets/chip_thin_metal*.glb. One beat is 8 s.

Overview (6 beats):
  0 whole     the whole chip, the thin band (M1-M4) lit above the transistors
  1 dense     glide in: the thin levels run close together, one pitch apart
  2 hop       a signal climbs the NMOS drain, crosses M3 in one local hop and drops to the PMOS
  3 narrow    close on one thin wire: the barrier skin takes a share of a narrow core, high R
  4 EUV       an EUV exposure slit scans across the band: the tight pitch is printed in one pass
  5 whole     back out to the whole chip, the thin band still lit (loops to beat 0)

Zoom-ins (keys and labels as the old CHIP tab; 3 beats each):
  a  one damascene loop on M3: litho and trench, barrier and fill, cap and via
  b  copper, low-k and the barrier on one M3 run
  c  damascene vs subtractive on M2, then ruthenium and molybdenum
  d  self-aligned vias: a via placed by overlay, a shifted one, the self-aligned one
  e  pin access: M1 pins in a standard cell, and routing on M2

Sections (one scene per `# ` heading of CHIP_THIN_METAL.txt), detailed cut-aways built from
chip_thin_metal_detail.py rather than the schematic chip:
  1 what happens (3 beats)     2 two levels in section (4)   3 damascene vs subtractive (3)
  4 metals for the thinnest (4) 5 self-aligned vias (3)      6 pin access (3)
  7 patterning limits (3)      8 who makes it (3)            9 chokepoints and risks (3)
  10 sources (3)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_zooms import finish, start  # noqa: E402
import chip_kit as C  # noqa: E402
from chip_kit import F, ball, box, empty, glide_camera, label, mat, overlay, route, show, stream_of, tube  # noqa: E402
from sand_overview import fly  # noqa: E402
import chip_thin_metal_detail as D  # noqa: E402

BEATS = 6
LIFE_HOP = 90
LIFE_NARROW = 130
LIFE_FLOW = 90

# the node's band is lit on the whole-chip beats 0 and 5 (they match, so the loop is clean); the close
# beats 1-4 leave it off, so its cyan wash does not hide the wire, skin and slit they are about
THIN_LIT = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
# the one thin wire the close-up follows: M3 (level index 2), the long run from NMOS drain to PMOS drain
WIRE_Y = C.level_y("thin", 2)
WIRE_H = C.TIERS["thin"][2]
WIRE_D = C.TIERS["thin"][3]
X_DRAIN_N, X_DRAIN_P = -510.0, 510.0
TAG_Y = 440.0  # the gap between M1 and M2: a tag there sits between the levels, off the copper
# a beat that adds only tags above the band: the text runs right of its pin, so shift the target
# right by about half a label and drop it onto the band, which the tags name
TAG_POSE = ((130.0, 560.0, 0.0), 2600.0, 0.0, 0.10)

WHOLE = C.WHOLE
POSES = [
    WHOLE,
    ((-100.0, 500.0, 0.0), 1600.0, 0.0, 0.10),  # dense: the band, levels stacked close
    ((0.0, 330.0, 0.0), 2100.0, 0.0, 0.10),  # hop: NMOS drain up, across M3, down to PMOS
    ((0.0, 540.0, 0.0), 1300.0, 0.0, 0.10),  # narrow: one wire close
    ((0.0, 560.0, 0.0), 2000.0, 0.0, 0.10),  # EUV: the band with the slit scanning
    WHOLE,
]


# ---- shared pieces --------------------------------------------------------------------


def mats(m):
    C.mats(m)
    m["tm_barrier"] = mat("chip_thin_metal_barrier", (0.62, 0.74, 0.90), emit=(0.60, 0.75, 1.0), strength=1.5, alpha=0.45)
    m["tm_euv"] = mat("chip_thin_metal_euv", (0.45, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.0, alpha=0.30)
    m["tm_mask"] = mat("chip_thin_metal_mask", (1.0, 0.85, 0.40), emit=(1.0, 0.80, 0.35), strength=2.5, alpha=0.40)
    m["tm_cap"] = mat("chip_thin_metal_cap", (0.95, 0.90, 0.78), emit=(1.0, 0.90, 0.70), strength=1.2, alpha=0.85)
    m["tm_lowk"] = mat("chip_thin_metal_lowk", (0.55, 0.85, 0.95), emit=(0.50, 0.85, 1.0), strength=1.2, alpha=0.30)
    m["tm_metal2"] = mat("chip_thin_metal_metal2", (0.80, 0.75, 0.95), emit=(0.75, 0.65, 1.0), strength=1.8, alpha=0.40)
    m["tm_bad"] = mat("chip_thin_metal_bad", (1.0, 0.35, 0.30), emit=(1.0, 0.30, 0.25), strength=2.5, alpha=0.50)
    m["tm_core"] = mat("chip_thin_metal_core", (1.0, 0.62, 0.35), emit=(1.0, 0.55, 0.25), strength=2.5, alpha=0.75)
    # a faint band for the zoom-ins and sections: it marks M1-M4 without washing out the highlights
    m["tm_band"] = mat("chip_thin_metal_band", (0.45, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=0.4, alpha=0.06)


def base(name, beats):
    """A fresh scene: the whole chip with the thin band lit for every beat."""
    m, root = start(name, beats, page="chip")
    mats(m)
    lit = m["c_lit_thin"]
    m["c_lit_thin"] = m["tm_band"]
    C.chip(root, m, thin=[(F(0, 0), F(beats, 0))])
    m["c_lit_thin"] = lit
    return m, root


def band(level, x0, x1, pad=8):
    """The box round one thin wire run (level index, x span), `pad` mm out on every side."""
    y = C.level_y("thin", level)
    lo = (x0 - pad, y - WIRE_H / 2 - pad, -60 - WIRE_D / 2 - pad)
    hi = (x1 + pad, y + WIRE_H / 2 + pad, -60 + WIRE_D / 2 + pad)
    return lo, hi


def hl(root, name, bounds, mat_, intervals):
    """A translucent highlight over a box `bounds` = (lo, hi), on for `intervals`. Its front face is
    pulled out past the lit band's (z = 6), so the band never sits in front of it."""
    lo, hi = bounds
    return overlay(root, name, lo, (hi[0], hi[1], max(hi[2], 12.0)), mat_, intervals)


def tag(root, text, at, intervals):
    return label(text, at, root, intervals)


def shown_tube(root, name, a, b, r, mat_, intervals, verts=12):
    g = empty(name, root)
    tube(name + "_t", a, b, r, mat_, g, verts=verts)
    show(g, intervals)
    return g


def flow(root, m, name, pts, beat, u0, u1, n=9, life=LIFE_FLOW, size=30.0):
    """A train of signal dots along the polyline `pts`, launched through fractions u0..u1 of `beat`."""
    s, p = route(pts)
    return stream_of(root, name, n, s, p, size, m["c_dot_sig"], beat, u0, u1, life)


def cam(*poses):
    return list(poses)


# the close-up poses shared by several scenes (target, distance, yaw, pitch)
M3_CLOSE = ((0.0, WIRE_Y, 0.0), 1300.0, 0.0, 0.08)
M3_ZOOM = ((-200.0, WIRE_Y, 0.0), 1500.0, 0.0, 0.10)
M2_WIDE = ((0.0, 480.0, 0.0), 1700.0, 0.0, 0.10)
M2_ZOOM = ((0.0, 480.0, 0.0), 1400.0, 0.0, 0.10)
VIA_ZOOM = ((560.0, 500.0, 0.0), 900.0, 0.15, 0.08)
VIA_WIDE = ((560.0, 500.0, 0.0), 1300.0, 0.15, 0.08)
PIN_ZOOM = ((-700.0, 470.0, 0.0), 1100.0, 0.0, 0.10)
PIN_WIDE = ((-700.0, 470.0, 0.0), 1500.0, 0.0, 0.10)
BAND_WIDE = ((0.0, 500.0, 0.0), 2200.0, 0.0, 0.08)


# ---- the overview ---------------------------------------------------------------------
# Beat 0 is the whole chip with the thin band lit. Beats 1-4 swap the chip for the detailed M1-M4
# cut-away (chip_thin_metal_detail.stack), scaled so it sits in the band, and the camera glides in
# on it. Beat 5 swaps back to the whole chip, matching beat 0 so the loop is clean.

INSET_O = (0.0, C.THIN[0], 0.0)  # the stack's M1 floor on the band's floor
INSET_S = 0.12  # 2,000 stack mm (M1-M4) in the 240 mm band


def ipose(pose):
    return D.world(pose, INSET_O, INSET_S)


def build():
    m, root = start("thin_metal", BEATS, page="chip")
    mats(m)
    D.materials(m)
    whole = [(0, F(1, 0)), (F(5, 0), F(6, 0) + 1000)]
    chip_g = D.group("chip_whole", root, whole)
    C.chip(chip_g, m, thin=THIN_LIT)
    label("thin metal M1-M4", (1000.0, C.THIN[1] - 60, 0), root, whole)
    s = D.inset(root, INSET_O, INSET_S, D.span(1, 5))
    D.stack(m, s)
    l1, l2 = D.LAY[0], D.LAY[1]
    xa, xb = l1["pos"][4], l1["pos"][6]
    yt, ym, zf = l1["y1"] + 10.0, (l2["y0"] + l2["y1"]) / 2, l2["fz"] + 10.0
    hop = [(xa, -180.0, 10.0), (xa, 160.0, 10.0), (xa, yt, 10.0), (xa, yt, zf), (xa, ym, zf), (xb, ym, zf),
           (xb, yt, zf), (xb, yt, 10.0), (xb, 160.0, 10.0), (xb, -180.0, 10.0)]
    D.dots(s, m["sig"], "hop", hop, 2, 0.0, 0.55, n=7, life=150, size=24.0)
    x3, w = l1["pos"][3], l1["w"]
    D.ring_glow("skin", (x3 - w / 2, l1["y0"]), (x3 + w / 2, l1["y1"]), 20.0, m["hl_soft"], s, D.span(3, 4))
    zig = [(x3 - 40 + (80 if k % 2 else 0), 300.0 - 40.0 * k, 12.0) for k in range(8)]
    D.dots(s, m["sig"], "scatter", zig, 3, 0.05, 0.7, n=5, life=110, size=14.0)
    slit = D.group("euv", s, [(F(4, 0.05), F(4, 0.95))])
    sm = D.empty("euv_m", slit)
    top = D.LAY[3]["y1"]
    D.box("euv_light", (-1300.0 - 90, top + 20.0, -2200.0), (-1300.0 + 90, top + 1100.0, 0.0), m["euv"], sm)
    fly(sm, [(0.0, 0.0, 0.0), (2600.0, 0.0, 0.0)], F(4, 0.08), F(4, 0.92), steps=8)
    D.tags(s, [
        (D.span(1, 2), "M1-M4: ~20-40 nm pitch", D.front(D.LAY[2], 4)),
        (D.span(1, 2), "copper lines in low-k", D.front(l1, 2)),
        (D.span(1, 2), "W contacts to transistors", (l1["pos"][4], -100.0, 3.0)),
        (D.span(2, 3), "up a via, along M2", (xa, ym, zf)),
        (D.span(2, 3), "down to the next cell", (xb, yt, 10.0)),
        (D.span(3, 4), "Cu core ~12 nm", (x3, l1["y0"] + 0.5 * l1["h"], 3.0)),
        (D.span(3, 4), "TaN + liner ~2 nm a side", (x3 - w / 2 + 6, l1["y0"] + 0.3 * l1["h"], 3.0)),
        (D.span(4, 5), "EUV exposure scans the wafer", (0.0, top + 600.0, -1100.0)),
        (D.span(4, 5), "~26 nm pitch per exposure", D.front(D.LAY[3], 2)),
    ])
    sp = dict(yaw=0.50, pitch=0.34, fill=0.95)
    D.glide(root, [
        C.WHOLE,
        ipose(D.frame(D.STACK_LO, D.STACK_HI, dx=150.0, **sp)),
        ipose(D.frame((xa - 400, -300.0, -500.0), (xb + 400, l2["y1"] + 80, 0.0), yaw=0.55, pitch=0.30, fill=0.92, dx=120.0)),
        ipose(D.frame((x3 - 200, -40.0, -120.0), (x3 + 200, 360.0, 0.0), yaw=0.12, pitch=0.08, dx=60.0)),
        ipose(D.frame(D.STACK_LO, (D.X1, top + 1100.0, 0.0), yaw=0.45, pitch=0.30, fill=0.95, dx=150.0)),
        C.WHOLE,
    ])


# ---- zoom-ins a-e ---------------------------------------------------------------------
# Detailed cut-aways, as the sections: a the damascene loop, b one line's copper, low-k and
# barrier, c damascene vs subtractive then Ru and Mo, d self-aligned vias, e pin access.


def zoom_start(name):
    m, root = start(name, 3, page="chip")
    D.materials(m)
    return m, root


def zoom_a():
    """One damascene loop on a block: litho and trench, barrier and copper fill, CMP, cap and via."""
    m, root = zoom_start("thin_metal_zoom_a")
    pins, lo, hi, blo, bhi = D.loop_rig(m, root)
    D.tags(root, [
        (D.sub(0, 0.05, 0.5), "EUV light through the reticle", pins["light"]),
        (D.sub(0, 0.05, 0.5), "resist on a hard mask", pins["resist"]),
        (D.sub(0, 0.5, 1.0), "trench etched in low-k", pins["trench"]),
        (D.sub(0, 0.5, 1.0), "hard mask", pins["hm"]),
        (D.sub(1, 0.08, 1.0), "TaN + Co liner ~2 nm", pins["lin"]),
        (D.sub(1, 0.2, 0.75), "copper plates bottom-up", pins["core"]),
        (D.sub(1, 0.75, 1.0), "overburden", pins["over"]),
        (D.sub(2, 0.0, 0.42), "CMP pad polishes flat", pins["pad"]),
        (D.sub(2, 0.45, 1.0), "SiCN cap", pins["cap"]),
        (D.sub(2, 0.62, 1.0), "via to the next level", pins["via"]),
    ])
    D.glide(root, [
        D.frame(blo, bhi, yaw=0.30, pitch=0.24, fill=0.92, dx=140.0),
        D.frame(lo, (hi[0], hi[1] + 300.0, 0.0), yaw=0.28, pitch=0.24, fill=0.92, dx=140.0),
        D.frame(lo, hi, yaw=0.28, pitch=0.26, fill=0.92, dx=140.0),
    ])


def zoom_b():
    """Copper, low-k and the barrier on the M1 and M2 cut faces of the stack."""
    m, root = zoom_start("thin_metal_zoom_b")
    D.stack(m, root)
    l1, l2 = D.LAY[0], D.LAY[1]
    ym, zf = (l2["y0"] + l2["y1"]) / 2, l2["fz"] + 10.0
    D.dots(root, m["sig"], "flow", [(l1["pos"][1], ym, zf), (l1["pos"][6], ym, zf)], 0, 0.0, 0.7, n=8, life=90, size=20.0)
    for k in (2, 3):
        x0, x1 = l1["pos"][k] + l1["w"] / 2, l1["pos"][k + 1] - l1["w"] / 2
        D.front_glow(f"lk{k}", (x0, l1["y0"]), (x1, l1["y1"]), m["hl_soft"], root, D.span(1, 2))
    x3, w = l1["pos"][3], l1["w"]
    D.ring_glow("skin", (x3 - w / 2, l1["y0"]), (x3 + w / 2, l1["y1"]), 20.0, m["hl_soft"], root, D.span(2, 3))
    zig = [(x3 - 40 + (80 if k % 2 else 0), 300.0 - 40.0 * k, 12.0) for k in range(8)]
    D.dots(root, m["sig"], "scatter", zig, 2, 0.05, 0.7, n=5, life=110, size=14.0)
    D.tags(root, [
        (D.span(0, 1), "Cu core carries the current", (l1["pos"][3], ym, zf)),
        (D.span(0, 1), "M1 line ~16 nm wide", (l1["pos"][4], l1["y0"] + 0.5 * l1["h"], 3.0)),
        (D.span(1, 2), "low-k SiOCH, k ~2.5-3", ((l1["pos"][2] + l1["pos"][3]) / 2, 160.0, 5.0)),
        (D.span(1, 2), "less coupling to neighbours", ((l1["pos"][3] + l1["pos"][4]) / 2, 260.0, 5.0)),
        (D.span(2, 3), "TaN barrier + Co liner", (x3 - w / 2 + 5, l1["y0"] + 0.3 * l1["h"], 5.0)),
        (D.span(2, 3), "Cu core ~12 nm", (x3, l1["y0"] + 0.55 * l1["h"], 5.0)),
    ])
    near = D.frame((l1["pos"][1] - 180, -60.0, -320.0), (l1["pos"][6] + 180, l2["y1"] + 40, 0.0), yaw=0.35, pitch=0.18, fill=0.95, dx=80.0)
    gaps = D.frame((l1["pos"][1] - 180, -60.0, -320.0), (l1["pos"][5] + 180, 360.0, 0.0), yaw=0.25, pitch=0.14, dx=60.0)
    one = D.frame((x3 - 200, -40.0, -120.0), (x3 + 200, 360.0, 0.0), yaw=0.12, pitch=0.08, dx=60.0)
    D.glide(root, [near, gaps, one])


def zoom_c():
    """Damascene then subtractive, animated; then 14 nm lines of Cu, Ru and Mo side by side."""
    m, root = zoom_start("thin_metal_zoom_c")
    dp, dlo, dhi = D.damascene(m, root, 0.0, 0)
    sp, slo, shi = D.subtractive(m, root, 1250.0, 1, metal="ru")
    g = D.group("trio", root, D.span(2, 3))
    ox = 3200.0
    cu = D.xsec(m, g, "tcu", ox, 140.0)
    ru = D.xsec(m, g, "tru", ox + 340.0, 140.0, metal="ru", barrier=0, liner=0)
    mo = D.xsec(m, g, "tmo", ox + 680.0, 140.0, metal="mo", barrier=0, liner=0)
    D.tags(root, [
        (D.sub(0, 0.03, 0.25), "trench etched in low-k", dp["trench"]),
        (D.sub(0, 0.25, 0.5), "TaN + Co lining", dp["bar"]),
        (D.sub(0, 0.5, 0.75), "copper overfills", dp["top"]),
        (D.sub(0, 0.75, 1.0), "CMP: excess polished off", dp["top"]),
        (D.sub(1, 0.03, 0.33), "Ru blanket", sp["blanket"]),
        (D.sub(1, 0.33, 0.66), "Ru etched into lines", sp["line"]),
        (D.sub(1, 0.66, 1.0), "gap fill leaves air gaps", sp["air"]),
        (D.span(2, 3), "Cu: skin takes ~1/3", cu[1]),
        (D.span(2, 3), "Ru: no barrier", ru[0]),
        (D.span(2, 3), "Mo: no barrier", mo[0]),
    ])
    D.glide(root, [
        D.frame(dlo, dhi, yaw=0.30, pitch=0.28, dx=120.0),
        D.frame(slo, shi, yaw=0.30, pitch=0.28, dx=120.0),
        D.frame((ox - 200.0, 0.0, -300.0), (ox + 880.0, 420.0, 0.0), yaw=0.22, pitch=0.18, fill=0.95, dx=150.0),
    ])


def zoom_d():
    """Self-aligned vias with the signal riding through: down a placed via into its line, into
    the neighbour when shifted, and into its own line again when the via is self-aligned."""
    m, root = zoom_start("thin_metal_zoom_d")
    h, yv0, yv1 = via_rig(m, root)
    a = D.group("via_ok", root, D.span(0, 1))
    via_box(m, a, "vok", -65.0, 65.0, h - 2.0, yv1 + 2.0)
    b = D.group("via_bad", root, D.span(1, 2))
    via_box(m, b, "vbad", 125.0, 255.0, h - 2.0, yv1 + 2.0)
    sp = D.group("short", root, D.span(1, 2))
    D.ball("spark", (225.0, h + 10.0, 8.0), 34.0, m["bad"], sp, 12)
    c = D.group("via_sav", root, D.span(2, 3))
    for k, (x0, x1) in enumerate(((-370.0, -90.0), (90.0, 370.0))):
        D.box(f"sav_blk{k}", (x0, h + 30.0, -900.0), (x1, h + 100.0, 2.5), m["cap"], c)
    via_box(m, c, "vsav_top", 35.0, 165.0, h + 100.0, yv1 + 2.0)
    D.box("vsav_bot", (35.0, h - 2.0, -110.0), (89.0, h + 102.0, 2.0), m["cu"], c)
    yu = yv1 + 120.0
    D.dots(root, m["sig"], "ok", [(-520.0, yu, 8.0), (0.0, yu, 8.0), (0.0, h * 0.4, 8.0)], 0, 0.0, 0.6, n=6, life=90, size=20.0)
    D.dots(root, m["bad"], "leak", [(-520.0, yu, 8.0), (190.0, yu, 8.0), (190.0, h + 20.0, 8.0), (280.0, h * 0.4, 8.0)], 1, 0.0, 0.6, n=6, life=90, size=20.0)
    D.dots(root, m["sig"], "sav", [(-520.0, yu, 8.0), (100.0, yu, 8.0), (60.0, h + 60.0, 8.0), (0.0, h * 0.4, 8.0)], 2, 0.0, 0.6, n=6, life=90, size=20.0)
    D.tags(root, [
        (D.span(0, 1), "via placed by overlay", (0.0, (yv0 + yv1) / 2, 3.0)),
        (D.span(0, 1), "signal down to its line", (0.0, h * 0.4, 10.0)),
        (D.span(1, 2), "shifted ~1/2 a space", (190.0, (yv0 + yv1) / 2, 3.0)),
        (D.span(1, 2), "short into the neighbour", (225.0, h + 10.0, 10.0)),
        (D.span(2, 3), "dielectric grown on neighbours", (260.0, h + 70.0, 4.0)),
        (D.span(2, 3), "lands only on its own line", (60.0, h + 50.0, 4.0)),
    ])
    pose = D.frame((-560.0, -20.0, -150.0), (560.0, yv1 + 240.0, 0.0), yaw=0.22, pitch=0.14, fill=0.95, dx=110.0)
    D.glide(root, [pose, pose, pose])


def zoom_e():
    """Pin access in a standard cell, from above: the pins, the access points, the routed wires
    with signals riding them."""
    m, root = zoom_start("thin_metal_zoom_e")
    g, pins, zs = D.cell(m, root)
    ap = D.group("access", root, D.span(1, 2))
    for nm in ("A", "B", "Y"):
        x = pins[nm][0]
        for z in zs:
            if -660.0 < z < -180.0:
                D.ball(f"ap{nm}{z:.0f}", (x, D.M2_Y[0] + 20, z), 42.0, m["bad"] if abs(z - zs[2]) < 1 else m["good"], ap, 12)
    blk = D.group("blocker", root, D.span(1, 3))
    D.box("blk", (D.CELL_X0 - 80, D.M2_Y[0], zs[2] - 24), (D.CELL_X1 + 80, D.M2_Y[1], zs[2] + 24), m["rbar"], blk)
    rt = D.group("routes", root, D.span(2, 3))
    D.box("rt1", (pins["A"][0] - 40, D.M2_Y[0], zs[1] - 24), (pins["B"][0] + 40, D.M2_Y[1], zs[1] + 24), m["cu"], rt)
    D.box("rt2", (pins["Y"][0] - 40, D.M2_Y[0], zs[3] - 24), (D.CELL_X1 + 80, D.M2_Y[1], zs[3] + 24), m["cu"], rt)
    for nm, z in (("A", zs[1]), ("B", zs[1]), ("Y", zs[3])):
        D.box(f"rv{nm}", (pins[nm][0] - 36, D.M1_Y[1], z - 36), (pins[nm][0] + 36, D.M2_Y[0], z + 36), m["cu"], rt)
    yb = D.M2_Y[1] + 30.0
    D.dots(root, m["sig"], "ab", [(pins["A"][0], yb, zs[1]), (pins["B"][0], yb, zs[1])], 2, 0.0, 0.7, n=6, life=70, size=26.0)
    D.dots(root, m["sig"], "yout", [(pins["Y"][0], yb, zs[3]), (D.CELL_X1 + 80, yb, zs[3])], 2, 0.0, 0.7, n=6, life=70, size=26.0)
    D.tags(root, [
        (D.span(0, 1), "VDD rail", pins["vdd"]),
        (D.span(0, 1), "VSS rail", pins["vss"]),
        (D.span(0, 1), "M1 pins A, B, Y", pins["B"]),
        (D.span(0, 1), "M2 tracks above", (D.CELL_X1 - 200, D.M2_Y[0], zs[0])),
        (D.span(1, 2), "green: a track reaches the pin", (pins["A"][0], D.M2_Y[0] + 20, zs[1])),
        (D.span(1, 2), "red: track taken by another net", (pins["Y"][0], D.M2_Y[0] + 20, zs[2])),
        (D.span(2, 3), "M2 wire joins A to B", (0.5 * (pins["A"][0] + pins["B"][0]), D.M2_Y[1], zs[1])),
        (D.span(2, 3), "output Y leaves on M2", (pins["Y"][0] + 200, D.M2_Y[1], zs[3])),
    ])
    pose = D.frame(D.CELL_LO, D.CELL_HI, yaw=0.08, pitch=1.15, fill=0.95, dx=150.0)
    D.glide(root, [pose, pose, pose])


# ---- sections 1-10 -------------------------------------------------------------------
# The sections build detailed cut-aways (chip_thin_metal_detail.py) at about 10 scene mm per nm,
# not the schematic chip: the M1-M4 stack, one damascene loop, line cross-sections, a self-aligned
# via, a standard cell from above and EUV line arrays. Every beat's camera is framed on its part.


def sec_start(name, beats):
    m, root = start(name, beats, page="chip")
    D.materials(m)
    return m, root


def lv(i):
    return D.LAY[i]


def gap_pin(i, k, dy=0.5):
    """A pin on the low-k between lines k and k+1 of z-running level i."""
    l = D.LAY[i]
    return ((l["pos"][k] + l["pos"][k + 1]) / 2, l["y0"] + dy * l["h"], l["fz"] + 2.0)


STACK_POSE = dict(yaw=0.50, pitch=0.34, fill=0.95)


def stack_pose(**kw):
    a = dict(STACK_POSE)
    a.update(kw)
    return D.frame(D.STACK_LO, D.STACK_HI, **a)


def sec1():
    """What happens: the M1-M4 stack, one damascene loop on a block, the stack with its levels named."""
    m, root = sec_start("thin_metal_sec1", 3)
    D.stack(m, root)
    pins, lo, hi = D.damascene(m, root, 4200.0, 1)
    D.tags(root, [
        (D.span(0, 1), "M1-M4 copper lines", D.front(lv(2), 4)),
        (D.span(0, 1), "low-k between lines", gap_pin(0, 2)),
        (D.span(0, 1), "W contacts down to transistors", (lv(0)["pos"][4], -100.0, 3.0)),
        (D.sub(1, 0.03, 0.25), "1 trench etched in low-k", pins["trench"]),
        (D.sub(1, 0.03, 0.25), "hard mask", pins["hm"]),
        (D.sub(1, 0.25, 0.5), "2 TaN barrier + Co liner", pins["bar"]),
        (D.sub(1, 0.5, 0.75), "3 copper plated, overfills", pins["top"]),
        (D.sub(1, 0.75, 1.0), "4 polished flat, SiCN cap", pins["top"]),
        (D.span(2, 3), "M1", D.front(lv(0), 6)),
        (D.span(2, 3), "M2 runs across M1", D.front(lv(1), 2)),
        (D.span(2, 3), "M3", D.front(lv(2), 7)),
        (D.span(2, 3), "M4", D.front(lv(3), 3)),
    ])
    D.glide(root, [stack_pose(), D.frame(lo, hi, yaw=0.30, pitch=0.30, dx=120.0), stack_pose(yaw=0.62)])


def sec2():
    """Two thin levels in section: the copper core, low-k and air gaps, the barrier and liner, a via."""
    m, root = sec_start("thin_metal_sec2", 4)
    D.stack(m, root)
    l1 = lv(0)
    # air gaps (an option) in two of the M1 spaces, from beat 1 on
    ag = D.group("airgaps", root, D.span(1, 4))
    for k in (4, 5):
        x = (l1["pos"][k] + l1["pos"][k + 1]) / 2
        D.box(f"air{k}", (x - 50, l1["y0"] + 40, -900.0), (x + 50, l1["y1"] - 70, 0.5), m["air"], ag)
    x3 = l1["pos"][3]
    w = l1["w"]
    near = D.frame((l1["pos"][2] - 180, -60.0, -320.0), (l1["pos"][5] + 180, 360.0, 0.0), yaw=0.25, pitch=0.16, dx=60.0)
    one = D.frame((x3 - 200, -40.0, -120.0), (x3 + 200, 360.0, 0.0), yaw=0.12, pitch=0.08, dx=60.0)
    xv = l1["pos"][4]
    l2 = lv(1)
    via = D.frame((xv - 520, 0.0, -560.0), (xv + 520, l2["y1"] + 60, 0.0), yaw=0.55, pitch=0.30, dx=80.0)
    D.tags(root, [
        (D.span(0, 1), "Cu line ~16 nm wide", (x3, l1["y0"] + 0.55 * l1["h"], 3.0)),
        (D.span(0, 1), "next line, ~32 nm pitch", (l1["pos"][4], l1["y0"] + 0.7 * l1["h"], 3.0)),
        (D.span(1, 2), "low-k SiOCH, k ~2.5-3", gap_pin(0, 2)),
        (D.span(1, 2), "air gap (option), k ~1", gap_pin(0, 4, 0.4)),
        (D.span(2, 3), "TaN barrier", (x3 - w / 2 + 5, l1["y0"] + 0.35 * l1["h"], 3.0)),
        (D.span(2, 3), "Co liner", (x3 - w / 2 + 16, l1["y0"] + 0.62 * l1["h"], 3.0)),
        (D.span(2, 3), "Cu core ~12 nm", (x3, l1["y0"] + 0.5 * l1["h"], 3.0)),
        (D.span(3, 4), "via lands on M1", (xv, l2["yv0"] + 80.0, l2["fz"] + 3.0)),
        (D.span(3, 4), "M2 runs across M1", (xv + 260.0, l2["y0"] + 0.5 * l2["h"], l2["fz"] + 3.0)),
        (D.span(3, 4), "SiCN cap", (xv - 300.0, l1["y1"] + 15.0, l2["fz"] + 1.0)),
    ])
    D.ring_glow("skin", (x3 - w / 2, l1["y0"]), (x3 + w / 2, l1["y1"]), 20.0, m["hl_soft"], root, D.sub(2, 0.45, 1.0))
    D.glide(root, [near, near, one, via])


def sec3():
    """Damascene (copper inlaid in low-k) against subtractive (ruthenium etched to lines)."""
    m, root = sec_start("thin_metal_sec3", 3)
    dp, dlo, dhi = D.damascene(m, root, 0.0, 0)
    sp, slo, shi = D.subtractive(m, root, 1250.0, 1, metal="ru")
    D.tags(root, [
        (D.sub(0, 0.03, 0.25), "trench etched in low-k", dp["trench"]),
        (D.sub(0, 0.25, 0.5), "TaN + Co lining", dp["bar"]),
        (D.sub(0, 0.5, 0.75), "copper overfills", dp["top"]),
        (D.sub(0, 0.75, 1.0), "CMP: excess polished off", dp["top"]),
        (D.sub(1, 0.03, 0.33), "Ru blanket", sp["blanket"]),
        (D.sub(1, 0.03, 0.33), "hard mask", sp["hm"]),
        (D.sub(1, 0.33, 0.66), "Ru etched into lines", sp["line"]),
        (D.sub(1, 0.66, 1.0), "gap fill leaves air gaps", sp["air"]),
        (D.span(2, 3), "Cu: barrier on 3 sides", dp["bar"]),
        (D.span(2, 3), "Ru: no liner", sp["line"]),
        (D.span(2, 3), "air gap", sp["air"]),
    ])
    both = D.frame((dlo[0], dlo[1], -300.0), (shi[0], shi[1], 0.0), yaw=0.22, pitch=0.24, fill=0.95, dx=120.0)
    D.glide(root, [D.frame(dlo, dhi, yaw=0.30, pitch=0.28, dx=120.0), D.frame(slo, shi, yaw=0.30, pitch=0.28, dx=120.0), both])


def sec4():
    """Metals for the thinnest lines: the barrier's share as copper shrinks, Ru and Mo with no
    barrier, then a thinner RuCo liner."""
    m, root = sec_start("thin_metal_sec4", 4)
    c40 = D.xsec(m, root, "cu40", -1000.0, 400.0)
    c24 = D.xsec(m, root, "cu24", -440.0, 240.0)
    c14 = D.xsec(m, root, "cu14", -60.0, 140.0)
    ru = D.group("ru_g", root, D.span(1, 4))
    r14 = D.xsec(m, ru, "ru14", 280.0, 140.0, metal="ru", barrier=0, liner=0)
    mo = D.group("mo_g", root, D.span(2, 4))
    m14 = D.xsec(m, mo, "mo14", 600.0, 140.0, metal="mo", barrier=0, liner=0)
    lg = D.group("liners", root, D.span(3, 4))
    thick = D.xsec(m, lg, "thick", 1200.0, 140.0, barrier=12.0, liner=18.0)
    thin = D.xsec(m, lg, "thin", 1540.0, 140.0, barrier=10.0, liner=10.0, lm="ru")
    D.tags(root, [
        (D.span(0, 1), "40 nm: ~88% copper", c40[0]),
        (D.span(0, 1), "24 nm: ~80%", c24[0]),
        (D.span(0, 1), "14 nm: ~66%, 2 nm skin", c14[0]),
        (D.span(1, 2), "Cu 14 nm: skin takes 1/3", c14[1]),
        (D.span(1, 2), "Ru 14 nm: all metal", r14[0]),
        (D.span(2, 3), "Ru: no barrier", r14[0]),
        (D.span(2, 3), "Mo: short mean free path", m14[0]),
        (D.span(3, 4), "TaN + Co ~3 nm: ~50% Cu", thick[0]),
        (D.span(3, 4), "RuCo ~2 nm: ~66% Cu", thin[0]),
    ])
    y40 = c40[2]
    D.glide(root, [
        D.frame((-1260.0, 0.0, -300.0), (60.0, y40 + 40, 0.0), yaw=0.22, pitch=0.18, dx=220.0),
        D.frame((-200.0, 0.0, -300.0), (420.0, 420.0, 0.0), yaw=0.22, pitch=0.18, dx=140.0),
        D.frame((-200.0, 0.0, -300.0), (740.0, 420.0, 0.0), yaw=0.22, pitch=0.18, dx=140.0),
        D.frame((1060.0, 0.0, -300.0), (1680.0, 420.0, 0.0), yaw=0.22, pitch=0.18, dx=140.0),
    ])


def via_rig(m, root):
    """Three M1-like lines in low-k, a SiCN cap, the via level, and an upper line running across.
    Returns the y levels."""
    g = D.empty("vrig", root)
    p, w, h, zb = 280.0, 140.0, 280.0, -900.0
    xs = (-p, 0.0, p)
    xa, xb = -2 * p, 2 * p
    D.box("v_si", (xa, -200.0, zb), (xb, 0.0, -1.0), m["lowk2"], g)
    for k, x in enumerate(xs):
        D.lined(f"v_l{k}", (x - w / 2, 0.0, zb), (x + w / 2, h, 0.0), D.B, m["tan"], m["cu"], g, liner=D.L, ml=m["co"])
    edges = [xa] + [e for x in xs for e in (x - w / 2, x + w / 2)] + [xb]
    for k in range(0, len(edges), 2):
        D.box(f"v_gap{k}", (edges[k], 0.0, zb), (edges[k + 1], h, -1.0), m["lowk"], g)
    D.box("v_cap", (xa, h, zb), (xb, h + 30.0, -1.0), m["cap"], g)
    yv0, yv1 = h + 30.0, h + 230.0
    D.box("v_ild", (xa, yv0, zb), (xb, yv1, -1.0), m["lowk2"], g)
    D.lined("v_up", (xa, yv1, -140.0), (xb, yv1 + 240.0, 0.0), D.B, m["tan"], m["cu"], g, liner=D.L, ml=m["co"], axis="x")
    D.box("v_upild", (xa, yv1, zb), (xb, yv1 + 240.0, -141.0), m["lowk"], g)
    return h, yv0, yv1


def via_box(m, parent, name, x0, x1, y0, y1):
    D.lined(name, (x0, y0, -110.0), (x1, y1, 0.0), D.B, m["tan"], m["cu"], parent, liner=D.L, ml=m["co"], axis="y")


def sec5():
    """Self-aligned vias: a via placed by overlay, the same via shifted into its neighbour, and a
    self-aligned one hemmed in by dielectric grown on the neighbours."""
    m, root = sec_start("thin_metal_sec5", 3)
    h, yv0, yv1 = via_rig(m, root)
    a = D.group("via_ok", root, D.span(0, 1))
    via_box(m, a, "vok", -65.0, 65.0, h - 2.0, yv1 + 2.0)
    D.front_glow("land_ok", (-65.0, h - 14.0), (65.0, h + 4.0), m["good"], root, D.span(0, 1), z=5.0)
    b = D.group("via_bad", root, D.span(1, 2))
    via_box(m, b, "vbad", 125.0, 255.0, h - 2.0, yv1 + 2.0)
    sp = D.group("short", root, D.span(1, 2))
    D.ball("spark", (225.0, h + 10.0, 8.0), 34.0, m["bad"], sp, 12)
    c = D.group("via_sav", root, D.span(2, 3))
    for k, (x0, x1) in enumerate(((-370.0, -90.0), (90.0, 370.0))):
        D.box(f"sav_blk{k}", (x0, h + 30.0, -900.0), (x1, h + 100.0, 2.5), m["cap"], c)
    via_box(m, c, "vsav_top", 35.0, 165.0, h + 100.0, yv1 + 2.0)
    D.box("vsav_bot", (35.0, h - 2.0, -110.0), (89.0, h + 102.0, 2.0), m["cu"], c)
    D.front_glow("land_sav", (35.0, h - 14.0), (70.0, h + 4.0), m["good"], root, D.span(2, 3), z=5.0)
    D.tags(root, [
        (D.span(0, 1), "via placed by overlay", (0.0, (yv0 + yv1) / 2, 3.0)),
        (D.span(0, 1), "lands on its line", (0.0, h - 4.0, 6.0)),
        (D.span(1, 2), "shifted ~1/2 a space", (190.0, (yv0 + yv1) / 2, 3.0)),
        (D.span(1, 2), "short to the neighbour", (225.0, h + 10.0, 10.0)),
        (D.span(2, 3), "dielectric grown on neighbours", (260.0, h + 70.0, 4.0)),
        (D.span(2, 3), "lands only on its own line", (60.0, h + 50.0, 4.0)),
    ])
    pose = D.frame((-560.0, -20.0, -150.0), (560.0, yv1 + 240.0, 0.0), yaw=0.22, pitch=0.14, fill=0.95, dx=110.0)
    D.glide(root, [pose, pose, pose])


def sec6():
    """Pin access: a standard cell from above, its access points, then routed M2 wires."""
    m, root = sec_start("thin_metal_sec6", 3)
    g, pins, zs = D.cell(m, root)
    # access points: where an M2 track crosses a pin; the middle track is taken by another net
    ap = D.group("access", root, D.span(1, 2))
    for nm in ("A", "B", "Y"):
        x = pins[nm][0]
        for z in zs:
            if -660.0 < z < -180.0:
                D.ball(f"ap{nm}{z:.0f}", (x, D.M2_Y[0] + 20, z), 42.0, m["bad"] if abs(z - zs[2]) < 1 else m["good"], ap, 12)
    blk = D.group("blocker", root, D.span(1, 3))
    D.box("blk", (D.CELL_X0 - 80, D.M2_Y[0], zs[2] - 24), (D.CELL_X1 + 80, D.M2_Y[1], zs[2] + 24), m["rbar"], blk)
    rt = D.group("routes", root, D.span(2, 3))
    D.box("rt1", (pins["A"][0] - 40, D.M2_Y[0], zs[1] - 24), (pins["B"][0] + 40, D.M2_Y[1], zs[1] + 24), m["sig"], rt)
    D.box("rt2", (pins["Y"][0] - 40, D.M2_Y[0], zs[3] - 24), (D.CELL_X1 + 80, D.M2_Y[1], zs[3] + 24), m["sig"], rt)
    for nm, z in (("A", zs[1]), ("B", zs[1]), ("Y", zs[3])):
        D.box(f"rv{nm}", (pins[nm][0] - 36, D.M1_Y[1], z - 36), (pins[nm][0] + 36, D.M2_Y[0], z + 36), m["cu"], rt)
    D.tags(root, [
        (D.span(0, 1), "VDD rail", pins["vdd"]),
        (D.span(0, 1), "VSS rail", pins["vss"]),
        (D.span(0, 1), "M1 pins A, B, Y", pins["B"]),
        (D.span(0, 1), "gate", pins["gate"]),
        (D.sub(1, 0.0, 1.0), "green: a track can reach the pin", (pins["A"][0], D.M2_Y[0] + 20, zs[1])),
        (D.sub(1, 0.0, 1.0), "red: track taken by another net", (pins["Y"][0], D.M2_Y[0] + 20, zs[2])),
        (D.span(2, 3), "M2 wire joins A to B", (0.5 * (pins["A"][0] + pins["B"][0]), D.M2_Y[1], zs[1])),
        (D.span(2, 3), "via drops onto pin Y", (pins["Y"][0], D.M2_Y[1], zs[3])),
    ])
    pose = D.frame(D.CELL_LO, D.CELL_HI, yaw=0.08, pitch=1.15, fill=0.95, dx=150.0)
    D.glide(root, [pose, pose, pose])


def line_array(m, parent, name, ox, pitch, n=5, metal="resist", depth=700.0, h=None):
    """n lines at `pitch` on a wafer slab, running in z, centred on ox. Returns (pin, lo, hi)."""
    g = D.empty(name, parent)
    w = pitch / 2
    h = h or 1.6 * w
    xa, xb = ox - n * pitch / 2 - 60, ox + n * pitch / 2 + 60
    D.box(name + "_hm", (xa, -60.0, -depth), (xb, 0.0, -1.0), m["hm"], g)
    D.box(name + "_si", (xa, -260.0, -depth), (xb, -60.0, -1.0), m["si"], g)
    for k in range(n):
        x = ox + (k - (n - 1) / 2) * pitch
        D.box(f"{name}_{k}", (x - w / 2, 0.0, -depth), (x + w / 2, h, 1.0), m[metal], g)
    return (ox + pitch / 2, h * 0.6, 3.0), (xa, -260.0, -depth), (xb, h, 0.0)


def beam(m, parent, name, ox, width, intervals):
    """EUV light coming down onto a line array: a violet column under a dark reticle."""
    g = D.group(name, parent, intervals)
    D.box(name + "_light", (ox - width / 2, 40.0, -600.0), (ox + width / 2, 900.0, -100.0), m["euv"], g)
    D.box(name + "_mask", (ox - width / 2 - 120, 900.0, -700.0), (ox + width / 2 + 120, 950.0, 0.0), m["glass"], g)
    return (ox - width / 2 + 40, 600.0, -100.0), (ox, 925.0, 0.0)


def sec7():
    """Patterning limits: lines printed by one EUV exposure at ~26 nm pitch, then High-NA at ~16 nm,
    then two published pitches side by side."""
    m, root = sec_start("thin_metal_sec7", 3)
    a26, lo26, hi26 = line_array(m, root, "a26", 0.0, 260.0)
    b26 = beam(m, root, "b26", 0.0, 1300.0, D.span(0, 1))
    a16, lo16, hi16 = line_array(m, root, "a16", 2400.0, 160.0)
    b16 = beam(m, root, "b16", 2400.0, 800.0, D.span(1, 2))
    a23, lo23, hi23 = line_array(m, root, "a23", 4800.0, 230.0, metal="cu")
    a28, lo28, hi28 = line_array(m, root, "a28", 6300.0, 280.0, metal="ru")
    D.tags(root, [
        (D.span(0, 1), "EUV 0.33 NA: ~26 nm pitch", a26),
        (D.span(0, 1), "13.5 nm light through the reticle", b26[0]),
        (D.span(1, 2), "High-NA 0.55: ~16 nm (reported)", a16),
        (D.span(1, 2), "same light, wider lens", b16[0]),
        (D.span(2, 3), "TSMC N3E: 23 nm min pitch", (4800.0 - 460.0, 120.0, 3.0)),
        (D.span(2, 3), "imec: 28 nm Ru, one exposure", (6300.0 - 560.0, 130.0, 3.0)),
    ])
    D.glide(root, [
        D.frame(lo26, (hi26[0], 960.0, 0.0), yaw=0.32, pitch=0.24, dx=140.0),
        D.frame(lo16, (hi16[0], 960.0, 0.0), yaw=0.32, pitch=0.24, dx=140.0),
        D.frame(lo23, hi28, yaw=0.20, pitch=0.22, fill=0.97, dx=200.0),
    ])


def sec8():
    """Who makes it: the stack with the fabs, then the tool makers pinned to their steps, then the
    designers and routers on a standard cell."""
    m, root = sec_start("thin_metal_sec8", 3)
    D.stack(m, root)
    ox = 4200.0
    g, pins, zs = D.cell(m, root, ox=ox)
    rt = D.group("routes", root, D.span(2, 3))
    D.box("rt1", (pins["A"][0] - 40, D.M2_Y[0], zs[1] - 24), (pins["B"][0] + 40, D.M2_Y[1], zs[1] + 24), m["sig"], rt)
    l1, l3, l4 = lv(0), lv(2), lv(3)
    D.tags(root, [
        (D.span(0, 1), "TSMC, Intel, Samsung set pitch", D.front(lv(1), 2)),
        (D.span(0, 1), "and pick the metal", D.front(l3, 6)),
        (D.span(1, 2), "Applied: barrier, liner, Ru", (l1["pos"][3] - l1["w"] / 2 + 5, l1["y0"] + 100, 3.0)),
        (D.span(1, 2), "Lam, TEL: etch and plating", D.front(l3, 5)),
        (D.span(1, 2), "ASML: EUV prints the lines", (0.0, l4["y1"] + 2.0, (l4["fz"] + D.LAY[3]["pos"][1]) / 2)),
        (D.span(2, 3), "NVIDIA, AMD, Arm design cells", pins["Y"]),
        (D.span(2, 3), "Synopsys, Cadence route M2", (0.5 * (pins["A"][0] + pins["B"][0]), D.M2_Y[1], zs[1])),
    ])
    lo = (D.CELL_LO[0] + ox, D.CELL_LO[1], D.CELL_LO[2])
    hi = (D.CELL_HI[0] + ox, D.CELL_HI[1], D.CELL_HI[2])
    D.glide(root, [stack_pose(dx=150.0), stack_pose(yaw=0.40, dx=150.0), D.frame(lo, hi, yaw=0.08, pitch=1.15, fill=0.95, dx=180.0)])


def sec9():
    """Chokepoints: ruthenium lines with etch defects, RC on a thin wire against a thick one, and
    the stack with its levels thickening upward."""
    m, root = sec_start("thin_metal_sec9", 3)
    D.stack(m, root)
    ox = 4200.0
    sp, slo, shi = D.subtractive(m, root, ox, 0, metal="ru", done_only=True)
    dg = D.group("defects", root, D.span(0, 1))
    D.ball("def1", (ox - 240.0, 300.0, 4.0), 30.0, m["bad"], dg, 12)
    D.ball("def2", (ox + 80.0, 160.0, 4.0), 30.0, m["bad"], dg, 12)
    # RC: a thin M1-sized wire and a thick upper-level wire, lengthwise, with signals along both
    rx0, rx1 = 7600.0, 9800.0
    D.lined("thin_w", (rx0, 0.0, -160.0), (rx1, 160.0, 0.0), D.B, m["tan"], m["cu"], root, liner=D.L, ml=m["co"], axis="x")
    D.lined("thick_w", (rx0, 420.0, -600.0), (rx1, 1020.0, 0.0), 20.0, m["tan"], m["cu"], root, axis="x")
    D.box("rc_ild", (rx0 - 100, -100.0, -700.0), (rx1 + 100, 1100.0, -601.0), m["lowk2"], root)
    D.dots(root, m["sig"], "slow", [(rx0, 80.0, 30.0), (rx1, 80.0, 30.0)], 1, 0.0, 0.5, n=6, life=190, size=28.0)
    D.dots(root, m["sig"], "fast", [(rx0, 720.0, 30.0), (rx1, 720.0, 30.0)], 1, 0.0, 0.8, n=10, life=50, size=28.0)
    D.tags(root, [
        (D.span(0, 1), "Ru, Mo: etch and CMP maturing", sp["line"]),
        (D.span(0, 1), "defects cost yield", (ox + 80.0, 160.0, 6.0)),
        (D.span(1, 2), "thin wire: high R x C, slow", (rx0 + 300, 160.0, 3.0)),
        (D.span(1, 2), "wide upper wire: fast", (rx0 + 300, 900.0, 3.0)),
        (D.span(2, 3), "upper levels get thicker", D.front(lv(3), 2)),
        (D.span(2, 3), "N2, 14A pitches not public", D.front(lv(1), 2)),
    ])
    D.glide(root, [
        D.frame(slo, shi, yaw=0.25, pitch=0.22, fill=0.92, dx=60.0),
        D.frame((rx0, -100.0, -600.0), (rx1, 1100.0, 0.0), yaw=0.20, pitch=0.12, dx=150.0),
        stack_pose(dx=150.0),
    ])


def sec10():
    """Sources: the M1-M4 stack, turning slowly. The sources are the beat text."""
    m, root = sec_start("thin_metal_sec10", 3)
    D.stack(m, root)
    D.tags(root, [(D.span(0, 3), "M1-M4 in cut-away", D.front(lv(2), 4))])
    D.glide(root, [stack_pose(yaw=0.30), stack_pose(yaw=0.50), stack_pose(yaw=0.70)])


SCENES = {
    "thin_metal": build,
    "thin_metal_zoom_a": zoom_a,
    "thin_metal_zoom_b": zoom_b,
    "thin_metal_zoom_c": zoom_c,
    "thin_metal_zoom_d": zoom_d,
    "thin_metal_zoom_e": zoom_e,
    "thin_metal_sec1": sec1,
    "thin_metal_sec2": sec2,
    "thin_metal_sec3": sec3,
    "thin_metal_sec4": sec4,
    "thin_metal_sec5": sec5,
    "thin_metal_sec6": sec6,
    "thin_metal_sec7": sec7,
    "thin_metal_sec8": sec8,
    "thin_metal_sec9": sec9,
    "thin_metal_sec10": sec10,
}


if __name__ == "__main__":
    names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(SCENES)
    for name in names:
        SCENES[name]()
        finish(name, page="chip")
