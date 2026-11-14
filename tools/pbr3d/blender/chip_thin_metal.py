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

Sections (one scene per `# ` heading of CHIP_THIN_METAL.txt):
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

BEATS = 6
LIFE_HOP = 90
LIFE_NARROW = 130
LIFE_FLOW = 90

THIN_LIT = [(F(0, 0), F(6, 0))]  # the node's band stays lit: beat 0 and beat 5 match, so the loop is clean
# the one thin wire the close-up follows: M3 (level index 2), the long run from NMOS drain to PMOS drain
WIRE_Y = C.level_y("thin", 2)
WIRE_H = C.TIERS["thin"][2]
WIRE_D = C.TIERS["thin"][3]
X_DRAIN_N, X_DRAIN_P = -510.0, 510.0
TAG_Y = 440.0  # the gap between M1 and M2: a tag there sits between the levels, off the copper

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
    m["tm_barrier"] = mat("chip_thin_metal_barrier", (0.62, 0.74, 0.90), metal=0.5, rough=0.4, alpha=0.35)
    m["tm_euv"] = mat("chip_thin_metal_euv", (0.45, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.0, alpha=0.30)
    m["tm_mask"] = mat("chip_thin_metal_mask", (1.0, 0.85, 0.40), emit=(1.0, 0.80, 0.35), strength=2.5, alpha=0.40)
    m["tm_cap"] = mat("chip_thin_metal_cap", (0.95, 0.90, 0.78), emit=(1.0, 0.90, 0.70), strength=1.2, alpha=0.85)
    m["tm_lowk"] = mat("chip_thin_metal_lowk", (0.55, 0.85, 0.95), emit=(0.50, 0.85, 1.0), strength=1.2, alpha=0.30)
    m["tm_metal2"] = mat("chip_thin_metal_metal2", (0.80, 0.75, 0.95), emit=(0.75, 0.65, 1.0), strength=1.8, alpha=0.40)
    m["tm_bad"] = mat("chip_thin_metal_bad", (1.0, 0.35, 0.30), emit=(1.0, 0.30, 0.25), strength=2.5, alpha=0.50)


def base(name, beats):
    """A fresh scene: the whole chip with the thin band lit for every beat."""
    m, root = start(name, beats, page="chip")
    mats(m)
    C.chip(root, m, thin=[(F(0, 0), F(beats, 0))])
    return m, root


def band(level, x0, x1, pad=8):
    """The box round one thin wire run (level index, x span), `pad` mm out on every side."""
    y = C.level_y("thin", level)
    lo = (x0 - pad, y - WIRE_H / 2 - pad, -60 - WIRE_D / 2 - pad)
    hi = (x1 + pad, y + WIRE_H / 2 + pad, -60 + WIRE_D / 2 + pad)
    return lo, hi


def hl(root, name, bounds, mat_, intervals):
    """A translucent highlight over a box `bounds` = (lo, hi), on for `intervals`."""
    lo, hi = bounds
    return overlay(root, name, lo, hi, mat_, intervals)


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


def build():
    m, root = start("thin_metal", BEATS, page="chip")
    mats(m)
    C.chip(root, m, thin=THIN_LIT)

    # hop: one signal, NMOS drain up the via, across M3, down the PMOS drain column
    s, p = route([(X_DRAIN_N, 6.0, -60.0), (X_DRAIN_N, WIRE_Y, -60.0), (X_DRAIN_P, WIRE_Y, -60.0), (X_DRAIN_P, 6.0, -60.0)])
    stream_of(root, "hop", 9, s, p, 46, m["c_dot_sig"], 2, 0.10, 0.60, LIFE_HOP)

    # narrow: the same M3 run, with its barrier skin, and a train of dots along it
    skin = empty("barrier", root)
    box("barrier_skin", (X_DRAIN_N - 4, WIRE_Y - WIRE_H / 2 - 4, -60 - WIRE_D / 2 - 4),
        (X_DRAIN_P + 4, WIRE_Y + WIRE_H / 2 + 4, -60 + WIRE_D / 2 + 4), m["tm_barrier"], skin)
    show(skin, [(F(3, 0.10), F(4, 0.0))])
    s, p = route([(X_DRAIN_N, WIRE_Y, -60.0), (X_DRAIN_P, WIRE_Y, -60.0)])
    stream_of(root, "narrow", 9, s, p, 46, m["c_dot_sig"], 3, 0.15, 0.60, LIFE_NARROW)

    # EUV: a translucent exposure slit, built on the origin and flown across the band
    slit = empty("euv_slit", root)
    box("euv_slit_b", (-30.0, C.THIN[0] - 30.0, -150.0), (30.0, C.THIN[1] + 30.0, 14.0), m["tm_euv"], slit)
    fly(slit, [(-640.0, 0.0, 0.0), (640.0, 0.0, 0.0)], F(4, 0.10), F(4, 0.90), steps=8)
    show(slit, [(F(4, 0.05), F(4, 0.95))])

    whole = [(F(0, 0), F(1, 0)), (F(5, 0), F(6, 0))]
    label("thin metal M1-M4", (1000.0, C.THIN[1] - 60, 0), root, whole)
    label("M1-M4: 20-30 nm pitch", (-200.0, 650.0, 0), root, [(F(1, 0.3), F(2, 0.0))])
    label("short local hop", (0.0, 600.0, 0), root, [(F(2, 0.2), F(3, 0.0))])
    label("barrier skin 1-2 nm", (0.0, 580.0, 0), root, [(F(3, 0.15), F(4, 0.0))])
    label("narrow wire: high R", (0.0, 625.0, 0), root, [(F(3, 0.15), F(4, 0.0))])
    label("EUV slit prints the pitch", (0.0, 670.0, 0), root, [(F(4, 0.15), F(5, 0.0))])
    label("EUV: 26-30 nm pitch", (0.0, 710.0, 0), root, [(F(4, 0.15), F(5, 0.0))])

    glide_camera(root, POSES)


# ---- zoom-ins a-e ---------------------------------------------------------------------


def zoom_a():
    """One damascene loop on M3: the mask cuts the trench, the barrier and copper fill it, a cap
    and a via close it off."""
    m, root = base("thin_metal_zoom_a", 3)
    hl(root, "mask", band(2, -510, 510, pad=14), m["tm_mask"], [(F(0, 0), F(1, 0))])
    tag(root, "litho pitch and trench etch", (-200.0, 580.0, 0), [(F(0, 0.05), F(1, 0))])
    hl(root, "barrier", band(2, -510, 510), m["tm_barrier"], [(F(1, 0), F(2, 0))])
    flow(root, m, "fill", [(-480.0, WIRE_Y, -60.0), (480.0, WIRE_Y, -60.0)], 1, 0.05, 0.60)
    tag(root, "barrier and copper fill", (-200.0, 580.0, 0), [(F(1, 0.05), F(2, 0))])
    hl(root, "cap", ((-510.0, WIRE_Y + 12, -70.0), (510.0, WIRE_Y + 20, -50.0)), m["tm_cap"], [(F(2, 0), F(3, 0))])
    shown_tube(root, "via", (-300.0, WIRE_Y, -60.0), (-300.0, 590.0, -60.0), 14, m["c_cu_thin"], [(F(2, 0), F(3, 0))])
    tag(root, "cap, then via up", (-300.0, 640.0, 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(M3_ZOOM, M3_ZOOM, ((-200.0, WIRE_Y, 0.0), 1500.0, 0.25, 0.10)))


def zoom_b():
    """Copper, low-k and the barrier on one M3 run."""
    m, root = base("thin_metal_zoom_b", 3)
    tag(root, "Cu core, 12-15 nm", (0.0, 578.0, 0), [(F(0, 0.05), F(1, 0))])
    hl(root, "lowk", ((-300.0, 548.0, -40.0), (300.0, 574.0, -10.0)), m["tm_lowk"], [(F(1, 0), F(2, 0))])
    tag(root, "low-k between lines", (300.0, 561.0, 0), [(F(1, 0.05), F(2, 0))])
    hl(root, "barrier", band(2, -510, 510, pad=6), m["tm_barrier"], [(F(2, 0), F(3, 0))])
    tag(root, "barrier 1-2 nm on every side", (0.0, 500.0, 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(M3_CLOSE, M3_CLOSE, M3_CLOSE))


def metal_scene(name, pose):
    """Damascene vs subtractive on M2, then the flow along a Ru or Mo wire. Used by zoom c and
    section 3."""
    m, root = base(name, 3)
    hl(root, "lowk", band(1, -700, 700, pad=8), m["tm_lowk"], [(F(0, 0), F(1, 0))])
    tag(root, "damascene, copper inlaid in low-k", (0.0, TAG_Y, 0), [(F(0, 0.05), F(1, 0))])
    hl(root, "metal", band(1, -700, 700, pad=8), m["tm_metal2"], [(F(1, 0), F(3, 0))])
    tag(root, "subtractive, metal etched to lines", (0.0, TAG_Y, 0), [(F(1, 0.05), F(2, 0))])
    flow(root, m, "ru", [(-600.0, 470.0, -60.0), (600.0, 470.0, -60.0)], 2, 0.05, 0.70)
    tag(root, "Ru and Mo etch to volatile products", (0.0, TAG_Y, 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(pose, pose, pose))


def zoom_c():
    metal_scene("thin_metal_zoom_c", M2_ZOOM)


def via_scene(name, pose):
    """A via placed by overlay (beat 0), shifted into a short (beat 1), self-aligned (beat 2)."""
    m, root = base(name, 3)
    shown_tube(root, "via_guess", (580.0, 410.0, -60.0), (580.0, 590.0, -60.0), 18, m["tm_mask"], [(F(0, 0), F(1, 0))])
    tag(root, "overlay places the via", (580.0, 630.0, 0), [(F(0, 0.05), F(1, 0))])
    shown_tube(root, "via_shift", (650.0, 410.0, -60.0), (650.0, 590.0, -60.0), 18, m["tm_bad"], [(F(1, 0), F(2, 0))])
    tag(root, "shifted, shorts or hits the wall", (650.0, 630.0, 0), [(F(1, 0.05), F(2, 0))])
    shown_tube(root, "via_self", (510.0, 410.0, -60.0), (510.0, 590.0, -60.0), 26, m["tm_euv"], [(F(2, 0), F(3, 0))])
    tag(root, "bounded by its own line", (510.0, 630.0, 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(pose, pose, pose))


def zoom_d():
    via_scene("thin_metal_zoom_d", VIA_ZOOM)


def pin_scene(name, pose):
    """Pin access on M1 in a standard cell, then the router on M2."""
    m, root = base(name, 3)
    hl(root, "pins", band(0, -890, -510, pad=12), m["tm_euv"], [(F(0, 0), F(1, 0))])
    tag(root, "pins on M1 and M2", (-700.0, 500.0, 0), [(F(0, 0.05), F(1, 0))])
    g = empty("pin_balls", root)
    for k, x in enumerate((-850.0, -780.0, -710.0, -640.0, -570.0)):
        ball(f"pin{k}", (x, 410.0, 10.0), 20.0, m["c_dot_out"], g, 12)
    show(g, [(F(1, 0), F(2, 0))])
    tag(root, "more pins, fewer tracks", (-700.0, 500.0, 0), [(F(1, 0.05), F(2, 0))])
    flow(root, m, "route", [(-680.0, 470.0, -60.0), (680.0, 470.0, -60.0)], 2, 0.05, 0.60)
    tag(root, "routers join the pins", (-700.0, 500.0, 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(pose, pose, pose))


def zoom_e():
    pin_scene("thin_metal_zoom_e", PIN_ZOOM)


# ---- sections 1-10 -------------------------------------------------------------------


def sec1():
    """What happens: the whole chip, then the thin band, then the four levels named."""
    m, root = base("thin_metal_sec1", 3)
    tag(root, "thin metal M1-M4", (1000.0, C.THIN[1] - 60, 0), [(F(0, 0), F(3, 0))])
    hl(root, "mask", band(0, -890, -510, pad=12), m["tm_mask"], [(F(1, 0), F(2, 0))])
    tag(root, "one damascene loop per level", (0.0, 650.0, 0), [(F(1, 0.05), F(2, 0))])
    for k, name in enumerate(("M1", "M2", "M3", "M4")):
        tag(root, name, (1000.0, C.level_y("thin", k), 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(WHOLE, BAND_WIDE, BAND_WIDE))


def sec2():
    """Two thin levels in section: copper core, low-k between, barrier skin, vias stacking them."""
    m, root = base("thin_metal_sec2", 4)
    tag(root, "copper core, 12-15 nm", (0.0, 578.0, 0), [(F(0, 0.05), F(1, 0))])
    hl(root, "lowk", ((-300.0, 548.0, -40.0), (300.0, 574.0, -10.0)), m["tm_lowk"], [(F(1, 0), F(2, 0))])
    tag(root, "low-k between lines", (300.0, 561.0, 0), [(F(1, 0.05), F(2, 0))])
    hl(root, "barrier", band(2, -510, 510, pad=6), m["tm_barrier"], [(F(2, 0), F(3, 0))])
    tag(root, "barrier 1-2 nm on the sides", (0.0, 500.0, 0), [(F(2, 0.05), F(3, 0))])
    shown_tube(root, "via_l", (-510.0, 410.0, -60.0), (-510.0, 590.0, -60.0), 26, m["tm_euv"], [(F(3, 0), F(4, 0))])
    shown_tube(root, "via_r", (510.0, 410.0, -60.0), (510.0, 590.0, -60.0), 26, m["tm_euv"], [(F(3, 0), F(4, 0))])
    tag(root, "vias stack the levels", (510.0, 640.0, 0), [(F(3, 0.05), F(4, 0))])
    glide_camera(root, cam(M3_CLOSE, M3_CLOSE, M3_CLOSE, ((0.0, 520.0, 0.0), 1900.0, 0.0, 0.10)))


def sec3():
    metal_scene("thin_metal_sec3", M2_WIDE)


def sec4():
    """Metals for the thinnest lines: a liner on copper, Ru, Mo and the cobalt cost."""
    m, root = base("thin_metal_sec4", 4)
    hl(root, "liner", band(1, -700, 700, pad=8), m["tm_barrier"], [(F(0, 0), F(1, 0))])
    tag(root, "copper with a RuCo liner", (0.0, TAG_Y, 0), [(F(0, 0.05), F(1, 0))])
    hl(root, "ru", band(2, -510, 510, pad=8), m["tm_metal2"], [(F(1, 0), F(2, 0))])
    tag(root, "Ru steadier with width", (0.0, 500.0, 0), [(F(1, 0.05), F(2, 0))])
    hl(root, "mo", band(0, -890, -510, pad=8), m["tm_metal2"], [(F(2, 0), F(3, 0))])
    tag(root, "Mo low bulk mean free path", (-700.0, TAG_Y, 0), [(F(2, 0.05), F(3, 0))])
    hl(root, "co", band(1, -700, 700, pad=8), m["tm_barrier"], [(F(3, 0), F(4, 0))])
    tag(root, "Co yield and R cost at 3 nm", (0.0, 650.0, 0), [(F(3, 0.05), F(4, 0))])
    glide_camera(root, cam(M2_WIDE, M2_WIDE, M2_WIDE, M2_WIDE))


def sec5():
    via_scene("thin_metal_sec5", VIA_WIDE)


def sec6():
    pin_scene("thin_metal_sec6", PIN_WIDE)


def sec7():
    """Patterning limits: the EUV slit at about 26 nm, a narrower High-NA slit, then the foundry
    pitches as tags."""
    m, root = base("thin_metal_sec7", 3)
    slit = empty("euv_slit", root)
    box("slit26", (-30.0, C.THIN[0] - 30.0, -150.0), (30.0, C.THIN[1] + 30.0, 14.0), m["tm_euv"], slit)
    fly(slit, [(-640.0, 0.0, 0.0), (640.0, 0.0, 0.0)], F(0, 0.10), F(0, 0.90), steps=8)
    show(slit, [(F(0, 0.05), F(0, 0.95))])
    tag(root, "EUV 0.33 NA, about 26 nm pitch", (0.0, 710.0, 0), [(F(0, 0.05), F(1, 0))])
    slit2 = empty("hna_slit", root)
    box("slit16", (-16.0, C.THIN[0] - 30.0, -150.0), (16.0, C.THIN[1] + 30.0, 14.0), m["tm_euv"], slit2)
    fly(slit2, [(-640.0, 0.0, 0.0), (640.0, 0.0, 0.0)], F(1, 0.10), F(1, 0.90), steps=8)
    show(slit2, [(F(1, 0.05), F(1, 0.95))])
    tag(root, "High-NA 0.55, about 16 nm pitch", (0.0, 710.0, 0), [(F(1, 0.05), F(2, 0))])
    tag(root, "TSMC N3E 23 nm, imec Ru 28 nm", (0.0, 710.0, 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(*[((0.0, 560.0, 0.0), 2000.0, 0.0, 0.10)] * 3))


def sec8():
    """Who makes it: three tags on the band, one group per beat."""
    m, root = base("thin_metal_sec8", 3)
    tag(root, "fabs TSMC Intel Samsung", (0.0, 700.0, 0), [(F(0, 0.05), F(1, 0))])
    tag(root, "tools Applied Lam TEL ASML", (0.0, 700.0, 0), [(F(1, 0.05), F(2, 0))])
    tag(root, "designers and routers NVIDIA AMD Synopsys Cadence", (0.0, 700.0, 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(((0.0, 620.0, 0.0), 3200.0, 0.0, 0.10), ((0.0, 620.0, 0.0), 3200.0, 0.25, 0.10), ((0.0, 620.0, 0.0), 3200.0, -0.25, 0.10)))


def sec9():
    """Chokepoints: Ru and Mo maturity, RC of the thin wires, the pitches not yet public."""
    m, root = base("thin_metal_sec9", 3)
    hl(root, "new_metals", band(1, -700, 700, pad=8), m["tm_metal2"], [(F(0, 0), F(1, 0))])
    tag(root, "new metals: maturity", (0.0, TAG_Y, 0), [(F(0, 0.05), F(1, 0))])
    flow(root, m, "rc", [(-500.0, WIRE_Y, -60.0), (500.0, WIRE_Y, -60.0)], 1, 0.05, 0.70, n=9, life=120)
    tag(root, "RC thin wires slow the signal", (0.0, 500.0, 0), [(F(1, 0.05), F(2, 0))])
    tag(root, "N2 and 14A pitches not public", (0.0, 700.0, 0), [(F(2, 0.05), F(3, 0))])
    glide_camera(root, cam(M2_WIDE, M2_WIDE, ((0.0, 620.0, 0.0), 4200.0, 0.0, 0.10)))


def sec10():
    """Sources: the whole chip, a slow pull-back. The sources are the beat text."""
    m, root = base("thin_metal_sec10", 3)
    tag(root, "thin metal M1-M4", (1000.0, C.THIN[1] - 60, 0), [(F(0, 0), F(3, 0))])
    glide_camera(root, cam(WHOLE, ((0.0, 620.0, 0.0), 5000.0, 0.05, 0.10), WHOLE))


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
