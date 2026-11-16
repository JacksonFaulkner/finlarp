"""The nine numbered sections of the OPTICAL FIBER node: one close-up picture per idea about the glass.

Run from the repo root, one section at a time (the number comes after `--`):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_fibre_sections.py -- 3

Writes blender/fiber_fibre_section_<n>.blend and assets/fiber_fibre_section_<n>.glb. Each section is
three beats of 8 s (F(beat, u) gives the frame). Units mm, Y up, camera on +z, parts cut away at
z = 0. Part builders live in fiber_fibre_detail.py. Fibre glass is drawn 1 mm for 5 um (a 125 um
cladding is 25 mm across) except where a tag says otherwise; the ferrule is 1 mm for 25 um, the MPO
1 mm for 50 um; lasers, meters, the spool and the draw tower are not to scale.

Each section illustrates the heading of the same number in the OPTICAL FIBER write-up
(tui/src/screens/diagrams_pages/FIB_FIBER.txt), whose headings are the menu titles:

  1 What happens      single-mode and multimode fibre cut away: core, cladding mirror, coating;
                      one beam vs bouncing paths
  2 The parts         a fibre stripped in steps: 8.2 um core, 9.2 um mode field, 125 um cladding,
                      242 um acrylate coating
  3 Light, in order   a bench: laser, lens, acceptance cone, the core, scattering, far end,
                      receiver lens, photodiode
  4 Why it stays in   a shallow ray reflects (TIR), a steep one leaks; single-mode guided mode
  5 SM vs MM          VCSEL into a 50 um core (paths smear) vs InP laser and lens into a single-mode core
  6 Attenuation       scattering out of the core; power meters: 1 km costs 0.32 dB; connectors cost more
  7 Latency           a spool, 5 us per km; hollow-core vs solid-glass fibre side by side
  8 Who makes it      a draw tower: preform, furnace, gauge, coating die, UV lamps, capstan
  9 Chokepoints       dense MPO fibre counts; a tight bend leaking light; dust on a ferrule end face
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, beat, box, empty, key, label, pivot, rel, show, tube  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
import fiber_kit as K  # noqa: E402
import fiber_fibre_detail as D  # noqa: E402
from fiber_fibre_detail import glide, grow_ray, helix, pulses, rbox, segs, shell  # noqa: E402
from pbr_kit import mat, spin  # noqa: E402

PAGE = "fiber_fibre"
BEATS = 3
END = F(BEATS, 0)


def materials():
    return D.materials(K.materials())


def x_shell(name, x0, x1, r_in, r_out, m, parent, y=0.0, half=True, n=40):
    """A shell along x at height y (the usual fibre layer)."""
    return shell(name, (x0, y, 0.0), (x1, y, 0.0), r_in, r_out, m, parent, half=half, n=n)


def y_shell(name, y0, y1, r_in, r_out, m, parent, x=0.0, n=40):
    """A shell standing on the y axis (the draw tower)."""
    return shell(name, (x, y0, 0.0), (x, y1, 0.0), r_in, r_out, m, parent, n=n)


def ribbon_mat(i):
    return mat(f"ff_rib_{i}", D.RIBBON[i], rough=0.45)


# ---- parts reused by several sections ---------------------------------------------------------


def lc_ferrule(m, g, s=1.0, funnel=True):
    """An LC-style ferrule assembly with its tip at x = 0 and its body toward -s*x, 1 mm = 25 um
    (the core drawn wider). Zirconia ferrule with a 125 um bore and a glued glass end, a steel
    holder, a spring round the coated fibre. Returns the x of the far end of the coated fibre."""
    X = lambda x: s * x  # noqa: E731
    sh = lambda n, x0, x1, ri, ro, mt: shell(n, (X(x0), 0, 0), (X(x1), 0, 0), ri, ro, mt, g)  # noqa: E731
    # ferrule: back funnel, bore, chamfered tip
    if funnel:
        sh("fer_back", -70, -58, (9.0, 2.5), 25.0, m["zirconia"])
        sh("fer_body", -58, -4, 2.5, 25.0, m["zirconia"])
        sh("epoxy_a", -70, -64, 5.0, (9.0, 5.75), m["epoxy"])
        sh("epoxy_b", -64, -58, 2.5, (5.75, 2.55), m["epoxy"])
    else:
        sh("fer_body", -60, -4, 2.5, 25.0, m["zirconia"])
    sh("fer_tip", -4, 0, 2.5, (25.0, 18.0), m["zirconia"])
    # glass: lit core and cladding, flush with the tip
    sh("core", -150, 0, 0, 0.5, m["lit"])
    sh("clad", -150, 0, 0.5, 2.5, m["clad"])
    sh("coat", -150, -64 if funnel else -66, 2.5, 5.0, m["secondary"])
    # holder: a sleeve gripping the ferrule's back, a back wall, a flange collar
    sh("holder_sleeve", -70, -56, 25.0, 31.0, m["steel"])
    sh("holder_wall", -78, -70, 5.0, 31.0, m["steel"])
    sh("holder_flange", -78, -72, 31.0, 37.0, m["steel"])
    sh("spring_stop", -126, -120, 5.0, 17.0, m["dark_steel"])
    a, b = sorted((X(-120), X(-78)))
    helix("spring", (0, 0, 0), a, b, 12.0, 1.5, 7, m["steel"], g, per_turn=24)
    return X(-150)



def mpo(m, parent, y0, b=2):
    """Two MT ferrules (an MPO joint) turned so the row of 12 fibres lies in the cut plane, at height
    y0, 1 mm = 50 um. The left ferrule carries the guide pins; the right slides on in beat 2."""
    g = empty("mpo", parent)
    left, right = empty("mt_left", g), empty("mt_right", g)
    pitch = 5.0
    for side, grp in ((-1, left), (1, right)):
        box(f"mt_block_{side}", (min(0, 70 * side), y0 - 64, -25), (max(0, 70 * side), y0 + 64, -0.3), m["mt"], grp)
        for i in range(12):
            y = y0 + (i - 5.5) * pitch
            xa, xb = (0, side * 120)
            shell(f"mt_core_{side}_{i}", (xa, y, 0), (xb, y, 0), 0, 0.4, m["core"], grp, n=12)
            shell(f"mt_clad_{side}_{i}", (xa, y, 0), (xb, y, 0), 0.4, 1.25, m["clad"], grp, n=12)
            shell(f"mt_coat_{side}_{i}", (side * 74, y, 0), (side * 120, y, 0), 1.25, 2.5, ribbon_mat(i), grp, n=12)
        boot = (side * 72, y0 - 32, -6), (side * 76, y0 + 32, -2.6)
        box(f"mt_boot_{side}", tuple(map(min, *boot)), tuple(map(max, *boot)), m["dark_steel"], grp)
    for yp in (y0 - 46, y0 + 46):
        shell(f"pin_{yp}", (-60, yp, 0), (26, yp, 0), 0, 7.0, m["steel"], left, n=20)
    key(right, F(b, 0), "location", P(45, 0, 0))
    key(right, F(b, 0.38), "location", P(0, 0, 0))
    for i in range(12):
        y = y0 + (i - 5.5) * pitch
        pulses(g, f"mpo_pk{i}", 2, (-120, y, 0), [(0, 0, 0), (240, 0, 0)], 1.4, m["lit"], b, 0.42, 0.62, 80, steps=4)
    show(g, beat(b))
    return g



def meter(m, parent, x, name):
    """A handheld optical power meter standing on its foot: body, screen, and a bar in the screen."""
    g = empty(name, parent)
    rbox(f"{name}_body", (x - 20, -40, -16), (x + 20, 42, 6), m["dark_steel"], g, 2.0)
    box(f"{name}_screen", (x - 14, 2, 5.5), (x + 14, 36, 6.6), m["screen"], g)
    for k in range(3):
        rbox(f"{name}_key{k}", (x - 12 + 9 * k, -28, 5), (x - 6 + 9 * k, -22, 7.5), m["steel"], g, 0.6)
    box(f"{name}_foot", (x - 24, -44, -20), (x + 24, -40, 8), m["dark_steel"], g)
    return g


def bar(m, parent, name, x, h, mt):
    g = empty(name, parent)
    box(f"{name}_b", (x - 4, 5, 6.6), (x + 4, 5 + h, 7.4), mt, g)
    return g



# ---- 8 Who makes it ----------------------------------------------------------------------------


def section_8(root, m):
    """Who makes it: a draw tower, cut in half (not to scale): preform, furnace, gauge, coating, UV, capstan."""
    t = empty("tower", root)
    box("column", (-56, -112, -22), (-50, 128, -2), m["dark_steel"], t)
    box("beam", (-56, 122, -22), (12, 128, -2), m["dark_steel"], t)
    y_shell("chuck", 110, 122, 4.0, 10.0, m["steel"], t)
    y_shell("seed_rod", 100, 110, 0, 4.0, m["dark_steel"], t)

    pf = empty("preform", root)
    y_shell("pf_core", 22, 100, 0, 1.6, m["core"], pf)
    y_shell("pf_clad", 22, 100, 1.6, 20.0, m["clad"], pf)
    y_shell("neck_core_a", 10, 22, 0, (0.75, 1.6), m["core"], pf)
    y_shell("neck_clad_a", 10, 22, (0.75, 1.6), (9.0, 20.0), m["clad"], pf)
    y_shell("neck_core_b", -4, 10, 0, (0.2, 0.75), m["core"], pf)
    y_shell("neck_clad_b", -4, 10, (0.2, 0.75), (1.2, 9.0), m["clad"], pf)
    y_shell("fibre_glass", -100, -4, 0, 1.2, m["clad"], pf, n=16)
    y_shell("fibre_coat", -100, -38, 1.2, 2.5, m["secondary"], pf, n=16)

    y_shell("furnace", -6, 36, 27.0, 40.0, m["dark_steel"], t)
    y_shell("heater", 0, 30, 24.0, 27.0, m["heater"], t)
    box("furnace_arm", (-50, 10, -18), (-40, 18, -2), m["dark_steel"], t)
    # diameter gauge: two heads and a laser line across the fibre
    box("gauge_l", (-14, -17, -6), (-6, -11, -0.5), m["steel"], t)
    box("gauge_r", (6, -17, -6), (14, -11, -0.5), m["steel"], t)
    box("gauge_arm", (-50, -15, -6), (-14, -13, -2), m["dark_steel"], t)
    box("gauge_bridge", (-14, -17, -9), (14, -11, -6), m["steel"], t)
    tube("gauge_beam", (-6, -14, 0.3), (6, -14, 0.3), 0.3, m["ray"], t, 6)
    # coating die with liquid resin
    y_shell("die", -40, -30, 2.6, 9.0, m["steel"], t)
    y_shell("resin", -38, -31, 1.2, 2.6, m["primary"], t, n=16)
    box("die_arm", (-50, -37, -8), (-9, -33, -2), m["dark_steel"], t)
    # UV curing lamps
    for sx in (-1, 1):
        a, b = sorted((sx * 8, sx * 20))
        rbox(f"uv_house_{sx}", (a, -72, -14), (b, -48, -0.5), m["steel"], t, 0.8)
        c, d = sorted((sx * 7.5, sx * 8.5))
        box(f"uv_lamp_{sx}", (c, -70, -12), (d, -50, -0.8), m["uv"], t)
        e0, e1 = sorted((sx * 4, sx * 20))
        box(f"uv_top_{sx}", (e0, -48, -14), (e1, -46, -0.5), m["steel"], t)
    box("uv_arm", (-50, -62, -8), (-20, -58, -2), m["dark_steel"], t)
    # capstan wheel, its axle on an arm from the column
    wc = (-14.0, -100.0, -3.0)
    w = pivot("capstan", wc, root)
    tube("wheel", rel(wc, (-14, -100, -7)), rel(wc, (-14, -100, -1)), 14.0, m["steel"], w, 40)
    for k in range(4):
        a = k * math.pi / 4
        dx, dy = 13 * math.cos(a), 13 * math.sin(a)
        tube(f"spoke{k}", rel(wc, (-14 - dx, -100 - dy, -0.6)), rel(wc, (-14 + dx, -100 + dy, -0.6)), 0.8,
             m["dark_steel"], w, 6)
    spin(w, F(0, 0), END, turns=-3.0, axis=1)
    box("capstan_arm", (-50, -102, -10), (-14, -98, -7), m["dark_steel"], t)
    arc = [(-14 + 14 * math.cos(-a), -100 + 14 * math.sin(-a), 0) for a in [k * math.pi / 8 for k in range(9)]]
    segs("wrap", arc, 2.5, m["secondary"], t, 12)

    # bright marks riding down with the drawn fibre, all three beats
    for b in range(3):
        pulses(root, f"draw{b}", 6, (0, -4, 0.9), [(0, 0, 0), (0, -96, 0)], 1.0, m["spark"], b, 0.0, 0.85, 40,
               steps=2)

    label("PREFORM: glass rod, core inside", (14, 80, 0.2), root, beat(0))
    label("CORNING (GLW): the largest maker", (-14, 62, 0.2), root, beat(0))
    label("SEED ROD: lowered slowly", (4, 105, 0.2), root, beat(0))
    label("FURNACE: the tower draws it", (-33, 26, 0.2), root, beat(1))
    label("NECK-DOWN: rod thins to fibre", (4, 6, 0.2), root, beat(1))
    label("GAUGE holds 125 µm", (10, -14, 0.2), root, beat(1))
    label("COATED on the fly", (6, -35, 0.2), root, beat(2))
    label("UV LAMPS cure the coating", (14, -60, 0.2), root, beat(2))
    label("CAPSTAN: on to km-long spools", (-14, -100, 0.2), root, beat(2))
    glide(root, [((0, 62, 0), 195, 0.35, 0.15), ((-6, 12, 0), 125, 0.35, 0.12), ((-8, -74, 0), 165, 0.35, 0.12)])



# ---- shared pieces -------------------------------------------------------------------------------


def sm_fibre(m, g, x0, x1, y=0.0, coat=None, lit=True):
    """Single-mode fibre along x at height y, cut in half, to scale (1 mm = 5 um): an 8.2 um core,
    125 um cladding, and a two-layer acrylate coating 242 um across over `coat` = (x0, x1)."""
    x_shell(f"{g.name}_core", x0, x1, 0, 0.82, m["lit"] if lit else m["core"], g, y=y)
    x_shell(f"{g.name}_clad", x0, x1, 0.82, 12.5, m["clad"], g, y=y)
    if coat:
        x_shell(f"{g.name}_pri", coat[0], coat[1], 12.5, 19.0, m["primary"], g, y=y)
        x_shell(f"{g.name}_sec", coat[0], coat[1], 19.0, 24.2, m["secondary"], g, y=y)


def mm_fibre(m, g, x0, x1, y=0.0, coat=None):
    """Multimode fibre along x at height y, cut in half, to scale: a 50 um core in 125 um cladding."""
    x_shell(f"{g.name}_core", x0, x1, 0, 5.0, m["core"], g, y=y)
    x_shell(f"{g.name}_clad", x0, x1, 5.0, 12.5, m["clad"], g, y=y)
    if coat:
        x_shell(f"{g.name}_pri", coat[0], coat[1], 12.5, 19.0, m["primary"], g, y=y)
        x_shell(f"{g.name}_sec", coat[0], coat[1], 19.0, 24.2, m["aqua"], g, y=y)


def zigzag(x0, x1, y, r, slope, z=0.25, up=True):
    """A ray bouncing between the walls of a core of radius r, from (x0, y) on the axis."""
    pts, x, yy, s = [(x0, y, z)], x0, 0.0, (1 if up else -1)
    while True:
        target = r * s
        dx = abs(target - yy) / slope
        if x + dx >= x1:
            pts.append((x1, y + yy + s * slope * (x1 - x), z))
            return pts
        x += dx
        yy = target
        pts.append((x, y + yy, z))
        s = -s


def rel_path(pts):
    return [tuple(p[j] - pts[0][j] for j in range(3)) for p in pts]


def mode_field(m, g, x0, x1, y=0.0):
    """The guided mode drawn on the cut face: a faint glowing band 9.2 um wide (1 mm = 5 um) round
    the 8.2 um core, showing the light that runs partly in the cladding."""
    box(f"{g.name}_mode", (x0, y - 4.6, 0.05), (x1, y + 4.6, 0.35), m["mode"], g)


def lens(m, g, x, y, r):
    """A small glass lens (a squashed ball) on a post down to the bench at y = -40."""
    o = ball(f"{g.name}_lens", (x, y, 0), r, m["lens"], g, 24)
    o.scale = (0.35, 1.0, 1.0)
    tube(f"{g.name}_post", (x, y - r, -2), (x, -40, -2), 1.2, m["steel"], g, 10)


def can(m, g, x, y, facing, name):
    """A TO-can (a laser or a photodiode) on a block, its window toward `facing` (+1 or -1)."""
    tube(f"{name}_can", (x - facing * 12, y, 0), (x, y, 0), 9.0, m["steel"], g, 32)
    tube(f"{name}_win", (x, y, 0), (x + facing * 1.2, y, 0), 5.0, m["lens"], g, 24)
    tube(f"{name}_cap", (x - facing * 12, y, 0), (x - facing * 14, y, 0), 11.0, m["dark_steel"], g, 32)
    a, b = sorted((x - facing * 14, x))
    rbox(f"{name}_block", (a, -40, -10), (b, y - 9, 6), m["dark_steel"], g, 0.6)


# ---- 1 What happens: light stays trapped in a glass core for kilometres --------------------------


def section_1(root, m):
    """Single-mode (top) and multimode (bottom) fibre, cut in half and to scale: the core, the
    cladding that acts as a mirror, the coating; one beam vs many bouncing paths."""
    sm = empty("sm", root)
    sm_fibre(m, sm, -60, 60, y=30, coat=(-60, 35))
    mm = empty("mm", root)
    mm_fibre(m, mm, -60, 60, y=-30, coat=(-60, 35))
    for b in range(3):
        pulses(root, f"sm_pk{b}", 3, (-60, 30, 0), [(0, 0, 0), (120, 0, 0)], 1.4, m["lit"], b, 0.0, 0.6, 90)
    ray = zigzag(-60, 60, -30, 5.0, 0.3)
    grow_ray("mm_ray", ray, 0.32, m["ray"], root, F(1, 0.05), F(1, 0.75), END)
    ray2 = zigzag(-60, 60, -30, 5.0, 0.18, up=False)
    grow_ray("mm_ray2", ray2, 0.32, m["ray"], root, F(2, 0.05), F(2, 0.6), END)

    label("CORE: ~8 µm, the light rides here", (40, 30, 0.2), root, beat(0))
    label("CLADDING: 125 µm, acts as a mirror", (48, 38, 0.2), root, beat(0))
    label("COATING: plastic, 242 µm", (10, 52, -2), root, beat(0))
    label("MULTIMODE: 50 µm core", (45, -30, 0.2), root, beat(1))
    label("TOTAL INTERNAL REFLECTION", (ray[2][0], ray[2][1], 0.25), root, beat(1))
    label("SINGLE-MODE: one beam", (-20, 30, 0.2), root, beat(2))
    label("MULTIMODE: many paths bounce", (-20, -30, 0.2), root, beat(2))
    glide(root, [((5, 32, 0), 175, 0.40, 0.25), ((5, -28, 0), 175, 0.40, 0.25), ((5, 0, 0), 250, 0.40, 0.25)])


# ---- 2 The parts ---------------------------------------------------------------------------------


def section_2(root, m):
    """The parts, stripped back in steps and cut in half, to scale (1 mm = 5 um)."""
    g = empty("fibre", root)
    x_shell("core", -50, 40, 0, 0.82, m["lit"], g)
    x_shell("clad", -50, 40, 0.82, 12.5, m["clad"], g)
    x_shell("primary", -50, 10, 12.5, 19.0, m["primary"], g)
    x_shell("secondary", -50, 3, 19.0, 24.2, m["secondary"], g)
    ring = empty("mode_ring", root)
    shell("mode_end", (40, 0, 0), (40.3, 0, 0), 0.82, 4.6, m["glow"], ring, half=False, n=32)
    for b in range(3):
        pulses(root, f"pk{b}", 3, (-50, 0, 0), [(0, 0, 0), (90, 0, 0)], 1.2, m["lit"], b, 0.0, 0.6, 90)

    label("CORE: 8.2 µm glass, higher index", (40, 0, 0), root, beat(0))
    label("CLADDING: 125 µm glass, lower index", (24, 12.5, -1), root, beat(0))
    label("COATING: acrylate, 242 µm", (-14, 24.2, -1), root, beat(0))
    label("CORE: 8.2 µm across", (36, 0.0, 0.4), root, beat(1))
    label("MODE FIELD: 9.2 µm, partly in cladding", (40.3, -4.0, 0), root, beat(1))
    label("CLADDING edge: 125 µm across", (40, -12.0, 0), root, beat(1))
    label("PRIMARY: soft, cushions the glass", (7, 16.0, 0.2), root, beat(2))
    label("SECONDARY: hard, takes scratches", (-8, 22.0, 0.2), root, beat(2))
    label("242 µm (or 200 µm) outside", (-30, -24.2, 0.2), root, beat(2))
    glide(root, [((-8, 0, 0), 190, 0.45, 0.30), ((35, 0, 0), 80, 0.75, 0.20), ((0, 6, 0), 130, 0.35, 0.28)])


# ---- 3 Light down the fiber, in order -------------------------------------------------------------


def section_3(root, m):
    """A bench: laser, lens, the fibre (cut, to scale), lens, photodiode. Light runs the whole way."""
    g = empty("bench", root)
    rbox("bench_plate", (-125, -44, -24), (125, -40, 10), m["dark_steel"], g, 0.8)
    can(m, g, -100, 0, 1, "laser")
    lens(m, g, -78, 0, 9.0)
    lens(m, g, 78, 0, 9.0)
    can(m, g, 100, 0, -1, "pd")
    f = empty("fibre", root)
    sm_fibre(m, f, -58, 58, coat=(-46, 46))
    for sx in (-1, 1):
        a, b = sorted((sx * 46, sx * 52))
        rbox(f"clamp_{sx}", (a, -40, -14), (b, -24.2, 6), m["steel"], g, 0.5)
    beams = empty("beams", root)
    shell("beam_a", (-98.8, 0, 0), (-80, 0, 0), 0, (1.5, 7.0), m["glow"], beams, half=False, n=24)
    shell("beam_b", (-76, 0, 0), (-58.2, 0, 0), 0, (7.0, 0.82), m["glow"], beams, half=False, n=24)
    shell("beam_c", (58.2, 0, 0), (76, 0, 0), 0, (0.82, 7.0), m["glow"], beams, half=False, n=24)
    shell("beam_d", (80, 0, 0), (98.8, 0, 0), 0, (7.0, 1.5), m["glow"], beams, half=False, n=24)
    # pulses the whole way, every beat
    for b in range(3):
        pulses(root, f"pk{b}", 3, (-98, 0, 0.6), [(0, 0, 0), (196, 0, 0)], 1.3, m["lit"], b, 0.0, 0.6, 100,
               steps=8)
    # step 4: a little scattered out along the glass
    import random
    rnd = random.Random(3)
    for k in range(10):
        x = rnd.uniform(-40, 40)
        e = empty(f"sp_{k}", root)
        ball(f"sp_{k}_s", (x, 0, 1.0), 0.9, m["spark"], e, 8)
        f0 = F(1, rnd.uniform(0.05, 0.8))
        D.fly(e, [(0, 0, 0), (rnd.uniform(-3, 3), (1 if k % 2 else -1) * 22, 0)], f0, f0 + 30, steps=2)
        show(e, [(f0, f0 + 30)])

    label("1 LASER", (-106, 9, 0), root, beat(0))
    label("1 LENS focuses onto the core", (-78, 9, 0), root, beat(0))
    label("2 inside the acceptance cone: kept", (-64, 2.5, 0.5), root, beat(0))
    label("3 CORE guides it along", (-10, 0, 0.4), root, beat(1))
    label("4 a little scatters out", (15, 13, 0.4), root, beat(1))
    label("5 leaves the far end", (64, 2.5, 0.5), root, beat(2))
    label("RECEIVER LENS", (78, 9, 0), root, beat(2))
    label("PHOTODIODE", (106, 9, 0), root, beat(2))
    glide(root, [((-76, -8, 0), 120, 0.45, 0.25), ((0, -6, 0), 130, 0.35, 0.25), ((76, -8, 0), 120, 0.30, 0.25)])


# ---- 4 Why the light stays in ---------------------------------------------------------------------


def section_4(root, m):
    """A shallow ray reflects at the core wall; a steep one leaks (core widened so rays show, angles
    drawn steep). Then single-mode fibre to scale: one guided mode, partly in the cladding."""
    g = empty("fibre", root)
    x_shell("core", -45, 45, 0, 5.0, m["core"], g)
    x_shell("clad", -45, 45, 5.0, 12.5, m["clad"], g)
    z = 0.25
    ray_a = [(-60, 6.75, z), (-45, 0, z), (-28.33, 5, z), (5, -5, z), (38.33, 5, z), (45, 3, z)]
    grow_ray("ray_a", ray_a, 0.32, m["ray"], root, F(0, 0.08), F(0, 0.85), END)
    ray_b = [(-58, -10, z), (-45, 0, z), (-39.44, 5, z), (-34.1, 12.5, z), (-31.6, 17.5, z)]
    grow_ray("ray_b", ray_b, 0.32, m["leak"], root, F(1, 0.2), F(1, 0.6), END)
    nrm = empty("normal", root)
    for k in range(4):
        y0 = 1.5 + 2.2 * k
        tube(f"normal_{k}", (-28.33, y0, z), (-28.33, y0 + 1.2, z), 0.15, m["normal"], nrm, 6)
    show(nrm, [(F(1, 0), END)])
    pulses(root, "pk_a", 3, ray_a[1], rel_path(ray_a[1:]), 0.9, m["lit"], 1, 0.0, 0.5, 60, steps=16)

    sm = empty("sm", root)
    ys = -60.0
    sm_fibre(m, sm, -45, 45, y=ys)
    mode_field(m, sm, -45, 45, y=ys)
    shell("sm_mode_end", (45, ys, 0), (45.3, ys, 0), 0.82, 4.6, m["glow"], sm, half=False, n=32)
    pulses(root, "pk_sm", 4, (-45, ys, 0.6), [(0, 0, 0), (90, 0, 0)], 1.2, m["lit"], 2, 0.0, 0.6, 80)

    label("SHALLOW: grazing the wall", (-55, 4.5, z), root, beat(0))
    label("CORE: index a little higher", (-36, -2.5, 0.2), root, beat(0))
    label("CLADDING: index a little lower", (-36, -9.0, 0.2), root, beat(0))
    label("reflects completely: TIR", (-28.3, 5, z), root, beat(1))
    label("STEEP: crosses and leaks out", (-42.2, 2.5, z), root, beat(1))
    label("NORMAL to the wall", (-28.3, 9.5, z), root, beat(1))
    label("SINGLE-MODE: one guided mode", (15, ys - 3, 0.4), root, beat(2))
    label("MODE FIELD 9.2 µm: partly in cladding", (45.3, ys + 4.0, 0), root, beat(2))
    label("CORE: only ~1/3 % higher index", (-30, ys, 0.4), root, beat(2))
    glide(root, [((-46, 2, 0), 95, -0.50, 0.22), ((-40, 4, 0), 88, -0.45, 0.20), ((22, ys, 0), 110, 0.65, 0.22)])


# ---- 5 Single-mode vs multimode -------------------------------------------------------------------


def section_5(root, m):
    """Top: a VCSEL lights a multimode core directly. Bottom: an InP laser and a lens focus into a
    single-mode core. Fibres cut in half, to scale; the light sources not to scale."""
    ym, ys = 34.0, -34.0
    mm = empty("mm", root)
    mm_fibre(m, mm, -40, 60, y=ym, coat=(-20, 60))
    sm = empty("sm", root)
    sm_fibre(m, sm, -40, 60, y=ys, coat=(-20, 60), lit=False)
    src = empty("sources", root)
    rbox("bench", (-95, -64, -16), (65, -60, 8), m["dark_steel"], src, 0.6)
    # VCSEL: a small die on a submount on a post, emitting from a round aperture on its face
    rbox("vcsel_sub", (-56, ym - 9, -6), (-50, ym + 9, 2), m["substrate"], src, 0.3)
    rbox("vcsel_die", (-50, ym - 5, -4), (-46, ym + 5, 1.5), m["die"], src, 0.3)
    tube("vcsel_post", (-53, ym - 9, -3), (-53, -60, -3), 1.6, m["steel"], src, 10)
    shell("vcsel_ap", (-46, ym, 0), (-45.6, ym, 0), 0, 3.0, m["lit"], src, half=False, n=24)
    shell("vcsel_beam", (-45.6, ym, 0), (-40.2, ym, 0), 0, (3.0, 5.0), m["glow"], src, half=False, n=24)
    # InP DFB laser: a small chip on a submount, a stripe on its facet, then a ball lens
    rbox("inp_mount", (-86, ys - 9, -8), (-72, ys - 4, 3), m["substrate"], src, 0.4)
    rbox("inp_chip", (-84, ys - 4, -5), (-72, ys - 1, 2), m["oe"], src, 0.2)
    tube("inp_post", (-79, ys - 9, -3), (-79, -60, -3), 1.6, m["steel"], src, 10)
    tube("inp_stripe", (-72, ys - 2.5, 0), (-71.6, ys - 2.5, 0), 0.6, m["lit"], src, 12)
    shell("inp_beam", (-71.6, ys - 2.5, 0), (-60, ys - 0.5, 0), 0, (0.6, 4.0), m["glow"], src, half=False, n=20)
    ball("inp_lens", (-56, ys, 0), 4.0, m["lens"], src, 24)
    tube("inp_lens_post", (-56, ys - 4, -2), (-56, -60, -2), 0.8, m["steel"], src, 8)
    shell("inp_focus", (-52, ys, 0), (-40.2, ys, 0), 0, (3.5, 0.82), m["glow"], src, half=False, n=20)
    for x in (-10, 50):
        rbox(f"clamp_sm_{x}", (x - 3, -60, -14), (x + 3, ys - 24.2, 0), m["steel"], src, 0.4)
        rbox(f"clamp_mm_{x}", (x - 3, -60, -40), (x + 3, ym, -28), m["steel"], src, 0.4)
        rbox(f"clamp_mm_arm_{x}", (x - 3, ym - 3, -28), (x + 3, ym + 3, -24), m["steel"], src, 0.4)

    z = 0.25
    paths = [
        [(-40, ym, z), (60, ym, z)],
        zigzag(-40, 60, ym, 4.6, 0.18),
        zigzag(-40, 60, ym, 4.6, 0.36, up=False),
    ]
    for i, p in enumerate(paths):
        segs(f"mm_ray{i}", p, 0.22, m["ray"], root)
        for b in (0, 1):
            pulses(root, f"mm_pk{i}_{b}", 2, p[0], rel_path(p), 1.3, m["lit"], b, 0.05, 0.5, 80 + 25 * i,
                   steps=24)
    sm_line = empty("sm_line", root)
    tube("sm_line_t", (-40, ys, 0.1), (60, ys, 0.1), 0.35, m["ray"], sm_line, 8)
    show(sm_line, beat(2))
    pulses(root, "sm_pk", 3, (-40, ys, 0.3), [(0, 0, 0), (100, 0, 0)], 1.3, m["lit"], 2, 0.05, 0.6, 90)

    label("VCSEL: cheap 850 nm light", (-49, ym + 8, 0), root, beat(0))
    label("50 µm CORE: easy to hit", (-30, ym, 0.3), root, beat(0))
    label("many paths, different lengths", (10, ym + 4.6, z), root, beat(1))
    label("pulses smear after ~100 m", (45, ym, z), root, beat(1))
    label("InP LASER: precise light", (-78, ys - 1, 2), root, beat(2))
    label("LENS: aims at an 8 µm core", (-56, ys + 4, 0), root, beat(2))
    label("one path: sharp over km", (-15, ys, 0.3), root, beat(2))
    glide(root, [((-34, 30, 0), 115, 0.40, 0.22), ((10, 34, 0), 140, 0.30, 0.22), ((-30, -30, 0), 150, 0.40, 0.22)])


# ---- 6 Attenuation: how little light is lost ------------------------------------------------------


def section_6(root, m):
    """Single-mode fibre between two power meters (glass to scale, 1 mm = 5 um; meters not)."""
    g = empty("fibre", root)
    sm_fibre(m, g, -55, 55, coat=(-55, 55))
    for sx in (-1, 1):
        shell(f"boot_{sx}", (sx * 55, 0, 0), (sx * 60, 0, 0), 0, 27.0, m["black"], g, half=False)
    meter(m, root, -80, "m_in")
    meter(m, root, 80, "m_out")
    bar(m, root, "bar_in", -80, 28.0, m["bar"])
    bar(m, root, "bar_out", 80, 26.1, m["bar"])

    import random
    rnd = random.Random(6)
    for b in (0, 2):
        for k in range(20):
            x = rnd.uniform(-45, 45)
            up = 1 if k % 2 else -1
            e = empty(f"sp{b}_{k}", root)
            ball(f"sp{b}_{k}_s", (x, 0, 1.0), 1.1, m["spark"], e, 8)
            f0 = F(b, rnd.uniform(0.05, 0.8))
            D.fly(e, [(0, 0, 0), (rnd.uniform(-4, 4), up * 26, 0)], f0, f0 + 30, steps=2)
            show(e, [(f0, f0 + 30)])
    for b in range(3):
        pulses(root, f"pk{b}", 3, (-55, 0, 0), [(0, 0, 0), (110, 0, 0)], 1.6, m["spark"], b, 0.0, 0.55, 80,
               scale_to=(0.93, 0.93, 0.93))

    label("SCATTERING in the glass itself", (-20, 0, 0.3), root, beat(0))
    label("light thrown out of the core", (14, 12, 0.3), root, beat(0))
    label("IN: full power", (-80, 34, 7), root, beat(1))
    label("OUT after 1 km: −0.32 dB, ~7% lost", (80, 32, 7), root, beat(1))
    label("FIBRE: 1 km at 1310 nm", (0, 24.2, -1), root, beat(1))
    label("2 km in glass: under 1 dB", (30, 24.2, -1), root, beat(2))
    label("CONNECTOR: loses more than the glass", (57, 27, 0), root, beat(2))
    glide(root, [((0, 0, 0), 145, 0.30, 0.25), ((0, 0, 0), 380, 0.25, 0.18), ((50, 4, 0), 200, 0.30, 0.18)])


# ---- 7 Latency: the speed of light in glass -------------------------------------------------------


def section_7(root, m):
    """A spool of fibre on a stand (not to scale); then hollow-core vs solid-glass fibre, cut."""
    sp = empty("spool", root)
    shell("hub", (-32, 0, 0), (32, 0, 0), 10.0, 18.0, m["spool"], sp, half=False, n=48)
    for sx in (-1, 1):
        shell(f"flange_{sx}", (sx * 32, 0, 0), (sx * 36, 0, 0), 10.0, 46.0, m["spool"], sp, half=False, n=64)
    shell("wound", (-32, 0, 0), (32, 0, 0), 18.0, 35.0, m["secondary"], sp, half=False, n=64)
    _, hp = helix("outer_turns", (0, 0, 0), -31.0, 31.0, 36.2, 1.2, 26, m["secondary"], sp, per_turn=36)
    tube("axle", (-50, 0, 0), (50, 0, 0), 9.5, m["steel"], root, 24)
    for sx in (-1, 1):
        for sz in (-1, 1):
            tube(f"leg_{sx}_{sz}", (sx * 46, 0, 0), (sx * 46, -62, sz * 30), 2.2, m["dark_steel"], root, 10)
    box("floor", (-62, -66, -40), (175, -62, 40), m["budget"], root)
    trail = empty("trail", root)
    for k in range(26):
        e = empty(f"trail_{k}", trail)
        helix(f"trail_{k}_h", (0, 0, 0), -31.0 + 62.0 * k / 26, -31.0 + 62.0 * (k + 1) / 26, 36.3, 1.3, 1,
              m["trail"], e, per_turn=36)
        show(e, [(F(1, 0.05 + 0.8 * k / 26), END)])
    rp = [tuple(p[j] - hp[0][j] for j in range(3)) for p in hp[::4]]
    for b in (0, 1):
        pulses(root, f"run{b}", 2, hp[0], rp, 2.0, m["lit"], b, 0.0, 0.5, 100, steps=len(rp) - 1)

    # Beat 2: two cut samples on stands. Hollow core: glass tubes round an air core. Solid: glass.
    hx0, hx1, yh, yg = 95.0, 165.0, 25.0, -32.0
    hc = empty("hollow", root)
    x_shell("hc_jacket", hx0, hx1, 24.0, 28.0, m["secondary"], hc, y=yh)
    x_shell("hc_tube", hx0, hx1, 18.0, 24.0, m["clad"], hc, y=yh)
    for k, a in enumerate((0, 180, 240, 300)):
        c = (yh + 12.5 * math.cos(math.radians(a)), 12.5 * math.sin(math.radians(a)))
        half = abs(c[1]) < 1e-6
        shell(f"hc_cap{k}", (hx0, c[0], c[1]), (hx1, c[0], c[1]), 4.6, 5.5, m["clad"], hc, half=half, n=24)
    sg = empty("solid", root)
    sm_fibre(m, sg, hx0, hx1, y=yg, coat=(hx0, hx1), lit=False)
    for x in (hx0 + 8, hx1 - 8):
        tube(f"stand_h_{x}", (x, yh - 28, -8), (x, yg + 24.2, -8), 1.5, m["steel"], root, 8)
        tube(f"stand_g_{x}", (x, yg - 24.2, -8), (x, -62, -8), 1.5, m["steel"], root, 8)
    for b in (2,):
        pulses(root, "hc_pk", 3, (hx0, yh, 0.5), [(0, 0, 0), (hx1 - hx0, 0, 0)], 2.2, m["lit"], b, 0.05, 0.6, 60)
        pulses(root, "sg_pk", 3, (hx0, yg, 0.5), [(0, 0, 0), (hx1 - hx0, 0, 0)], 2.2, m["lit"], b, 0.05, 0.6, 90)

    label("SPOOL: kilometres of fibre", (0, 37, -2), root, beat(0))
    label("1 km ≈ 5 µs for the light", (-20, 37.4, -2), root, beat(0))
    label("light at ~2/3 its vacuum speed", (10, 37.4, -2), root, beat(1))
    label("campus or DC-to-DC: it adds up", (-34, 30, 10), root, beat(1))
    label("HOLLOW CORE: light in air", (130, yh, 0.5), root, beat(2))
    label("GLASS TUBES guide it", (150, yh + 12.5, 0.2), root, beat(2))
    label("SOLID GLASS: ~1/3 slower", (130, yg, 0.5), root, beat(2))
    glide(root, [((0, -10, 0), 230, 0.45, 0.25), ((0, 12, 0), 200, 0.30, 0.35), ((130, -2, 0), 245, 0.35, 0.22)])


# ---- 9 Chokepoints and risks ----------------------------------------------------------------------


def section_9(root, m):
    """Three risks: dense fibre counts (an MPO joint), a tight bend leaking light, a dirty end face."""
    mpo(m, root, 0.0, b=0)

    # Beat 1: a coated fibre (not to scale) with a tight loop; light leaks out at the loop.
    yb = -260.0
    bend = empty("bend", root)
    r = 14.0
    loop = [(r * math.sin(t), yb + r - r * math.cos(t), 0) for t in [k * 2 * math.pi / 24 for k in range(25)]]
    path = [(-90, yb, 0)] + loop + [(90, yb, 0)]
    segs("bend_coat", path, 3.0, m["jacket"], bend, 16)
    segs("bend_core", [(p[0], p[1], p[2] + 3.05) for p in path], 0.6, m["lit"], bend, 8)
    tube("bend_peg", (0, yb + r, -12), (0, yb + r, -3), r - 3.2, m["dark_steel"], bend, 32)
    show(bend, beat(1))
    pulses(root, "bend_pk", 4, (path[0][0], path[0][1], 3.2), rel_path(path), 1.8, m["lit"], 1, 0.0, 0.6, 80, steps=40)
    import random
    rnd = random.Random(9)
    for k in range(16):
        t = rnd.uniform(0.3, 2 * math.pi - 0.3)
        p = (r * math.sin(t), yb + r - r * math.cos(t), 3.5)
        out = (math.sin(t) * 26, -math.cos(t) * 26, 0)
        e = empty(f"leak_{k}", root)
        ball(f"leak_{k}_s", p, 1.4, m["spark"], e, 8)
        f0 = F(1, rnd.uniform(0.15, 0.85))
        D.fly(e, [(0, 0, 0), out], f0, f0 + 30, steps=2)
        show(e, [(f0, f0 + 30)])

    # Beat 2: an LC ferrule tip with dust on its end face; light scatters at the dirt.
    yd = -520.0
    dirty = empty("dirty", root)
    lc_ferrule(m, dirty, 1.0, funnel=False)
    for i, (yy, zz, rr) in enumerate(((2.0, -1.0, 1.4), (-6.0, -3.0, 2.2), (9.0, -6.0, 1.8), (-12.0, -9.0, 1.5),
                                       (0.5, -12.0, 1.2))):
        ball(f"dust_{i}", (0.6, yy, zz), rr, m["dust"], dirty, 10)
    dirty.location = P(0, yd, 0)
    for k in range(10):
        a = rnd.uniform(-math.pi, math.pi)
        e = empty(f"scat_{k}", root)
        ball(f"scat_{k}_s", (1.0, yd, 1.0), 1.2, m["spark"], e, 8)
        f0 = F(2, rnd.uniform(0.1, 0.85))
        D.fly(e, [(0, 0, 0), (14, 18 * math.sin(a), 12 * abs(math.cos(a)))], f0, f0 + 24, steps=2)
        show(e, [(f0, f0 + 24)])
    pulses(root, "dirty_pk", 3, (-150, yd, 0.4), [(0, 0, 0), (150, 0, 0)], 1.4, m["lit"], 2, 0.0, 0.6, 70)

    label("AI racks: many times more fibre", (-95, -25, 0.2), root, beat(0))
    label("MPO: 12 fibres per plug", (-30, 27.5, 0.2), root, beat(0))
    label("CONNECTORS: capacity is tight", (40, 64, -1), root, beat(0))
    label("TIGHT BEND: light leaks out", (r, yb + r, 3.5), root, beat(1))
    label("needs bend-insensitive fibre", (-60, yb, 3.5), root, beat(1))
    label("DUST on the end face", (0.6, yd - 6, -3), root, beat(2))
    label("light scatters: link fails", (8, yd + 6, 4), root, beat(2))
    label("FERRULE tip: clean before plugging", (-30, yd + 25, -1), root, beat(2))
    glide(root, [((-8, -22, 0), 330, 0.30, 0.28), ((0, yb + 10, 0), 170, 0.25, 0.25), ((-8, yd + 2, 0), 110, 0.55, 0.20)])

SCENES = {
    1: section_1,
    2: section_2,
    3: section_3,
    4: section_4,
    5: section_5,
    6: section_6,
    7: section_7,
    8: section_8,
    9: section_9,
}


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--") + 1])
    name = f"section_{n}"
    _, root = start(name, beats=BEATS, page=PAGE)
    SCENES[n](root, materials())
    finish(name, page=PAGE)
