"""The nine MELT + PULL write-up sections, each a 3D picture authored in Blender and exported for
pbr3d in the SAND template (docs/diagram-pages.md). Puller pieces come from melt_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/melt_sections.py [-- 3 5]

For each section it writes blender/melt_sec<N>.blend and assets/melt_sec<N>.glb.

  1 what happens   load, melt, seed + neck, shoulder + body, tail + lift (five beats)
  2 inside         chamber and argon; seed down and the crystal forms while both turn; the
                   crucible rises with the falling melt; heater, shield, argon, SiO
  3 physics        atoms joining the lattice; mass flow slice by slice; oxygen off the quartz;
                   dopant segregation from head to tail
  4 numbers        the rod's temperature gradient; the model's settings; a 2 m body beside a
                   450 mm outline; the 400-minute timeline and the 1.6 mm/min study
  5 pull rates     four bars to scale (6.0, 1.6, 2.4, <= 0.5 mm/min), then fast and slow tracks
  6 shares         five 300 mm share bars; the top two; other sources on a 0-100% axis; five
                   makers each with its own puller
  7 risks          a crucible wearing out and its quartz supply cut; a dislocation and a remelt;
                   uniformity across a wafer; SEMI's 2023 falls
  8 names          four listed wafer makers; SK Siltron inside SK Inc; the puller makers;
                   the general-knowledge stamp
  9 sources        eight source cards lighting up in groups

One beat is SEC (8) seconds at 24 fps.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, beat, box, cut, disc, empty, key, label, mat, pivot, rel, rock, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
from poly_overview import keyed_path, run, shell  # noqa: E402
import melt_kit as K  # noqa: E402
from melt_kit import BODY, BODY_TOP, CRU_R, CRU_Y0, END, MELT_Y, NECK, SHOULDER, TAIL, XTAL_R  # noqa: E402

_M = {}


def begin(n, beats=4):
    m, root = start(f"sec{n}", beats, page="melt")
    K.mats(m)
    m["gold"] = mat("gold", (0.94, 0.74, 0.38), metal=0.3, rough=0.4)
    m["gold_glow"] = mat("gold_glow", (0.94, 0.74, 0.38), emit=(1.0, 0.75, 0.3), strength=2.5)
    m["blue"] = mat("blue", (0.36, 0.56, 0.82), metal=0.2, rough=0.45)
    m["grey"] = mat("grey", (0.42, 0.45, 0.52), metal=0.2, rough=0.6)
    m["red"] = mat("red", (0.90, 0.22, 0.18), emit=(0.9, 0.15, 0.1), strength=2.5)
    m["plinth"] = mat("plinth", (0.18, 0.19, 0.23), rough=0.8)
    m["paper"] = mat("paper", (0.90, 0.88, 0.82), rough=0.85)
    m["si_atom"] = mat("atom_si", (0.62, 0.64, 0.70), metal=0.5, rough=0.3)
    m["ghost"] = mat("ghost", (0.6, 0.75, 0.95), rough=0.2, alpha=0.18)
    _M.clear()
    _M.update(m)
    return m, root


def grow_bar(g, name, x, z, w, h, m, f0, f1, y0=0.0, depth=None):
    """A bar standing at (x, y0, z) that grows from nothing to height h over [f0, f1]."""
    d = depth or w
    b = pivot(name, (x, y0, z), g)
    box(f"{name}_box", (-w / 2, 0, -d / 2), (w / 2, h, d / 2), m, b)
    scale_keys(b, [(0, (OFF,) * 3), (f0, (1, 1, OFF)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    return b


def grow_hbar(g, name, x, y, z, length, thick, m, f0, f1):
    """A horizontal bar from (x, y, z) to the right that grows to `length` over [f0, f1]."""
    b = pivot(name, (x, y, z), g)
    box(f"{name}_box", (0, -thick / 2, -thick / 2), (length, thick / 2, thick / 2), m, b)
    scale_keys(b, [(0, (OFF,) * 3), (f0, (OFF, 1, 1)), (f1, (1, 1, 1)), (END, (1, 1, 1))], until=f0)
    return b


def plinth(g, x0, x1, z0=-600, z1=600, y=0.0):
    box("plinth", (x0, y - 80, z0), (x1, y, z1), _M["plinth"], g)


def placed(root, name, x):
    """A group built at the origin and then moved to x (so cut() and pivots build at the origin)."""
    g = empty(name, root)
    return g, lambda: setattr(g, "location", P(x, 0, 0))


def body_only(g, m, p, contact=0, p_keys=None, tags=None, spin=None, wire=False):
    return K.crystal(g, m, p_keys or K.static_p(p), contact, tags=tags or {}, spin=spin, wire=wire)


# ---- 1. what happens ---------------------------------------------------------------------


def sec1():
    m, root = begin(1, 5)
    p_keys = [
        (0, 700.0), (F(2, 0.05), 700.0), (F(2, 0.3), 0.0), (F(2, 0.4), 0.0), (F(2, 0.95), NECK),
        (F(3, 0.05), NECK), (F(3, 0.35), NECK + SHOULDER), (F(3, 0.95), NECK + SHOULDER + BODY),
        (F(4, 0.05), NECK + SHOULDER + BODY), (F(4, 0.5), NECK + SHOULDER + BODY + TAIL),
        (F(4, 0.6), NECK + SHOULDER + BODY + TAIL), (F(4, 0.92), NECK + SHOULDER + BODY + TAIL + 350.0),
    ]
    K.furnace(root, m, heat_on=F(1, 0.08), tags={"heater": beat(1)})
    K.crucible(root, m, load=0, melt=1, rise=(F(3, 0.35), F(3, 0.95)), tags={
        "chunks": ("LOAD: poly chunks", [(F(0, 0.35), F(1, 0))]),
        "dopant": ("plus dopant", [(F(0, 0.6), F(1, 0))]),
        "melt": ("MELT: about 1414 C, argon", [(F(1, 0.55), F(2, 0))]),
    })
    K.crystal(root, m, p_keys, F(2, 0.3), tags={
        "seed": ("SEED: lowered to the melt", [(F(2, 0.0), F(2, 0.5))]),
        "neck": ("NECK: 2-4 mm", [(F(2, 0.55), F(3, 0))]),
        "shoulder": ("SHOULDER: widen", [(F(3, 0.15), F(3, 0.45))]),
        "body": ("BODY: 300 mm, slow", [(F(3, 0.5), F(4, 0))]),
        "tail": ("TAIL: taper", [(F(4, 0.3), F(5, 0))]),
        "lifted": ("lifted clear to cool", [(F(4, 0.7), F(5, 0))]),
    })
    K.argon(root, m, 1)
    camera(root, [
        ((0.0, 1150.0, 0.0), 4900.0, 0.30, 0.16),
        ((0.0, 850.0, 0.0), 3900.0, 0.24, 0.14),
        ((0.0, 870.0, 0.0), 1300.0, 0.30, 0.10),
        ((0.0, 1750.0, 0.0), 6000.0, 0.28, 0.10),
        ((0.0, 2350.0, 0.0), 7200.0, 0.28, 0.10),
    ])
    finish("sec1", page="melt")


# ---- 2. inside a puller ------------------------------------------------------------------


def sec2():
    m, root = begin(2)
    p_keys = [
        (0, 700.0), (F(1, 0.05), 700.0), (F(1, 0.2), 0.0), (F(1, 0.25), 0.0), (F(1, 0.45), NECK),
        (F(1, 0.65), NECK + SHOULDER), (F(1, 0.95), NECK + SHOULDER + 300.0),
        (F(2, 0.05), NECK + SHOULDER + 300.0), (F(2, 0.95), NECK + SHOULDER + 1200.0),
    ]
    K.furnace(root, m, tags={
        "chamber": ("water-cooled steel chamber", beat(0)),
        "pull chamber": beat(0),
        "heater": beat(3),
        "shield": beat(3),
    })
    K.crucible(root, m, rise=(F(2, 0.05), F(2, 0.95)), spin=(F(1, 0.25), F(4, 0), 6), tags={
        "rise": beat(2),
        "melt": ("interface held at 1414 C", beat(2)),
    })
    K.crystal(root, m, p_keys, F(1, 0.2), spin=(F(1, 0.25), F(4, 0), 6), tags={
        "seed": ("seed parked above the melt", beat(0)),
        "shoulder": ("neck, shoulder, body in turn", [(F(1, 0.5), F(2, 0))]),
    })
    label("crystal 5 rpm, crucible -5 rpm", (K.SUS_R, K.CRU_TOP + 30, 15), root, [(F(1, 0.3), F(2, 0))])
    K.argon(root, m, 0, tags={"argon": ("argon at about 2500 Pa", beat(0))})
    K.argon(root, m, 3, tags={"argon": beat(3)})
    for s in (-1, 1):
        run(root, f"sio{s:+d}_", 5, [(s * (XTAL_R + 60), MELT_Y + 10, 26), (s * (CRU_R - 40), MELT_Y + 60, 26), (s * (K.SUS_R + 50), K.CRU_TOP + 40, 26), (s * (K.HEAT_R + 70), 300, 26)], 22, m["sio_b"], 3, 0.15, 0.8, 60)
    camera(root, [
        ((0.0, 1900.0, 0.0), 6600.0, 0.28, 0.12),
        ((0.0, 1000.0, 0.0), 2500.0, 0.30, 0.14),
        ((0.0, 1500.0, 0.0), 5200.0, 0.28, 0.12),
        ((0.0, 1100.0, 0.0), 3900.0, 0.26, 0.12),
    ])
    finish("sec2", page="melt")


# ---- 3. the physics and chemistry --------------------------------------------------------


def sec3():
    m, root = begin(3)
    rnd = random.Random(3)

    # beat 0: atoms joining the lattice at the freezing front (x = 0)
    g0 = empty("atoms", root)
    box("liquid", (-420, -300, -150), (420, 160, -120), m["melt_si"], g0)
    lat = empty("lattice", g0)
    sp, cols = 60.0, 7
    for r in range(3):
        for c in range(cols):
            ball(f"lat{r}_{c}", ((c - 3) * sp, 400 - r * sp, 0), 20, m["si_atom"], lat, 12)
    rows = 4
    for r in range(rows):
        f_row = F(0, 0.15 + 0.2 * r)
        for c in range(cols):
            e = empty(f"new{r}_{c}", lat)
            slot = ((c - 3) * sp, 400 - (3 + r) * sp, 0)
            ball(f"new{r}_{c}_m", slot, 20, m["si_atom"], e, 12)
            start_off = (rnd.uniform(-200, 200), -rnd.uniform(120, 260) - r * sp, rnd.uniform(-40, 40))
            key(e, f_row - 16, "location", P(*start_off))
            key(e, f_row, "location", P(0, 0, 0))
            show(e, [(f_row - 16, END)])
        key(lat, f_row, "location", P(0, r * sp, 0))
        key(lat, f_row + 10, "location", P(0, (r + 1) * sp, 0))
    for k in range(18):
        e = empty(f"liq{k}", g0)
        c = (rnd.uniform(-380, 380), rnd.uniform(-220, 100), 20)
        ball(f"liq{k}_m", c, 18, m["flow_hot"], e, 10)
        for j in range(0, 13):
            key(e, F(0, j / 12), "location", P(rnd.uniform(-25, 25), rnd.uniform(-25, 25), 0))
    label("atoms join in the seed's orientation", ((cols // 2) * sp, 400, 20), lat, beat(0))
    label("freezing point about 1414 C", (380, 140, 20), g0, beat(0))

    # beat 1: mass flow, slice by slice (x = 3000)
    g1, place1 = placed(root, "massflow", 3000)
    box("mf_melt", (-500, -200, -400), (500, 0, 0), m["melt_si"], g1)
    stack = empty("mf_stack", g1)
    n = 14
    th = 60.0
    for k in range(n):
        u0 = 0.05 + 0.05 * k if k < 7 else 0.4 + 0.032 * (k - 7) * 1.6 / 1.0
        f0 = F(1, min(0.95, u0))
        e = empty(f"slice{k}", stack)
        disc(f"slice{k}_m", (0, -th / 2 - k * th, -60), XTAL_R, th - 3, m["xtal"], e, 48)
        hl = empty(f"slice{k}_hl", e)
        disc(f"slice{k}_hl_m", (0, -th / 2 - k * th, -60), XTAL_R + 3, th - 8, m["gold_glow"], hl, 48)
        show(e, [(f0, END)])
        show(hl, [(f0, f0 + 14)])
        key(stack, f0, "location", P(0, k * th, 0), linear=True)
        key(stack, f0 + 6, "location", P(0, (k + 1) * th, 0), linear=True)
    label("1.0 mm/min: about 9.9 kg/h", (XTAL_R, 200, -60), g1, [(F(1, 0.1), F(1, 0.4))])
    label("1.6 mm/min: about 15.8 kg/h", (XTAL_R, 500, -60), g1, [(F(1, 0.45), F(2, 0))])
    place1()

    # beat 2: oxygen off the quartz (x = 6000)
    g2, place2 = placed(root, "oxygen", 6000)
    K.crucible(g2, m, tags={})
    xt = empty("ox_xtal", g2)
    disc("ox_body", (0, MELT_Y + 400, 0), XTAL_R, 800, m["xtal"], xt, 64)
    for s in (-1, 1):
        for k in range(3):
            run(g2, f"ox_sio{s:+d}{k}_", 3, [(s * (CRU_R - 30), CRU_Y0 + 80 + 90 * k, 24), (s * (CRU_R - 120), MELT_Y, 24), (s * (CRU_R - 140), MELT_Y + 300, 24)], 14, m["sio_b"], 2, 0.05 + 0.1 * k, 0.7, 70)
    sp_ = empty("ox_specks", g2)
    for k in range(14):
        a = -0.9 + 1.8 * ((k * 5) % 14) / 13
        ball(f"ox{k}", (XTAL_R * math.sin(a), MELT_Y + 30 + 40 * (k % 7), XTAL_R * math.cos(a)), 7, m["oxygen"], sp_, 8)
    show(sp_, [(F(2, 0.45), END)])
    label("quartz wall dissolves into SiO", (-CRU_R + 30, CRU_Y0 + 200, 24), g2, beat(2))
    label("about 1e18 oxygen per cm3 freezes in", (XTAL_R, MELT_Y + 200, 60), g2, [(F(2, 0.5), F(3, 0))])
    place2()

    # beat 3: segregation, head to tail (x = 9000)
    g3, place3 = placed(root, "segregation", 9000)
    box("seg_melt", (-500, -260, -400), (500, 0, 0), m["melt_si"], g3)
    seg = empty("seg_stack", g3)
    nb, bh = 8, 140.0
    for k in range(nb):
        u = k / (nb - 1)
        mm = mat(f"dope{k}", (0.70 - 0.45 * u, 0.74 - 0.38 * u, 0.80 - 0.05 * u), metal=0.6, rough=0.3)
        f0 = F(3, 0.05 + 0.11 * k)
        e = empty(f"band{k}", seg)
        disc(f"band{k}_m", (0, -bh / 2 - k * bh, -60), XTAL_R, bh - 4, mm, e, 48)
        show(e, [(f0, END)])
        key(seg, f0, "location", P(0, k * bh, 0), linear=True)
        key(seg, f0 + 10, "location", P(0, (k + 1) * bh, 0), linear=True)
    for k in range(24):
        e = empty(f"dop{k}", g3)
        ball(f"dop{k}_m", (rnd.uniform(-450, 450), -rnd.uniform(40, 220), 10), 14, m["dopant"], e, 8)
        show(e, [(F(3, 0.04 * k), END)])
    label("head: lightly doped", (XTAL_R, nb * bh - 60, -60), g3, [(F(3, 0.8), F(4, 0))])
    label("tail: most doped", (XTAL_R, 80, -60), g3, [(F(3, 0.85), F(4, 0))])
    label("dopant builds up in the melt", (450, -60, 10), g3, [(F(3, 0.3), F(4, 0))])
    place3()

    camera(root, [
        ((0.0, 170.0, 0.0), 1700.0, 0.15, 0.10),
        ((3000.0, 450.0, 0.0), 2300.0, 0.25, 0.12),
        ((6000.0, 800.0, 0.0), 2300.0, 0.22, 0.10),
        ((9000.0, 650.0, 0.0), 3300.0, 0.25, 0.12),
    ])
    finish("sec3", page="melt")


# ---- 4. by the numbers -------------------------------------------------------------------


def sec4():
    m, root = begin(4)
    # beat 0: the rod's gradient, hot at the melt
    g0 = empty("gradient", root)
    box("g_melt", (-500, -200, -400), (500, 0, 0), m["melt_si"], g0)
    n, seg = 6, 300.0
    for k in range(n):
        u = k / (n - 1)
        mm = mat(f"band{k}", (1.0 - 0.55 * u, 0.45 - 0.1 * u, 0.15 + 0.45 * u), rough=0.4, emit=(1.0, 0.35, 0.08), strength=2.2 * (1 - u) ** 2)
        e = empty(f"band{k}", g0)
        disc(f"band{k}_m", (0, seg * k + seg / 2, -60), XTAL_R, seg - 4, mm, e, 48)
        show(e, [(F(0, 0.05 + 0.08 * k), END)])
    label("melt about 1414 C (COMSOL)", (500, -20, 0), g0, [(F(0, 0.1), F(1, 0))])
    label("contact 1403-1407.5 C (model)", (XTAL_R, 40, -60), g0, [(F(0, 0.35), F(1, 0))])
    label("500 to 100 C per metre up the rod", (XTAL_R, 1300, -60), g0, [(F(0, 0.6), F(1, 0))])

    # beat 1: the model's settings as four plates rising in turn (not a scale)
    g1, place1 = placed(root, "settings", 3000)
    plinth(g1, -1300, 1300, -400, 400)
    rows = [("argon 100 L/min", m["argon"]), ("furnace 2500 Pa", m["grey"]), ("heater 310 kW", m["heater_hot"]), ("crystal 5, crucible -5 rpm", m["gold"])]
    for k, (text, mm) in enumerate(rows):
        x = -975 + 650 * k
        grow_bar(g1, f"set{k}", x, 0, 420, 600, mm, F(1, 0.08 + 0.18 * k), F(1, 0.2 + 0.18 * k))
        label(text, (x, 600, 210), g1, [(F(1, 0.18 + 0.18 * k), F(2, 0))])
    place1()

    # beat 2: a 2 m body beside a 450 mm outline
    g2, place2 = placed(root, "size", 6000)
    plinth(g2, -700, 700, -400, 400)
    grow_bar(g2, "body2m", -200, -60, 2 * XTAL_R, 2000, m["xtal"], F(2, 0.05), F(2, 0.6))
    ghost = empty("ghost450", g2)
    disc("ghost_m", (300, 1000, -60), 225, 2000, m["ghost"], ghost, 48)
    show(ghost, [(F(2, 0.4), END)])
    label("300 mm body, up to 2 m long", (-200 + XTAL_R, 2000, -60), g2, [(F(2, 0.5), F(3, 0))])
    label("450 mm: planned 2018, stopped 2016", (300 + 225, 1400, -60), g2, [(F(2, 0.45), F(3, 0))])
    label("several hundred kg (Wikipedia)", (-200 + XTAL_R, 900, -60), g2, [(F(2, 0.7), F(3, 0))])
    place2()

    # beat 3: the 400-minute timeline and the 1.6 mm/min study
    g3, place3 = placed(root, "timeline", 9000)
    plinth(g3, -2200, 2200, -300, 300)
    box("axis", (-2000, 0, -40), (2000, 40, 40), m["steel"], g3)
    for k in range(5):
        box(f"tick{k}", (-2000 + 1000 * k - 8, 0, -60), (-2000 + 1000 * k + 8, 120, 60), m["steel"], g3)
    grow_hbar(g3, "elapsed", -2000, 90, 0, 4000, 70, m["gold"], F(3, 0.05), F(3, 0.6))
    mk = empty("marker", g3)
    ball("marker_m", (-2000, 200, 0), 50, m["gold_glow"], mk, 16)
    key(mk, F(3, 0.05), "location", P(0, 0, 0), linear=True)
    key(mk, F(3, 0.6), "location", P(4000, 0, 0), linear=True)
    label("steady after about 400 min (model)", (2000, 250, 0), g3, [(F(3, 0.55), F(4, 0))])
    label("1.6 mm/min: interface moves 33 mm", (-2000, 300, 0), g3, [(F(3, 0.2), F(4, 0))])
    label("growth time -46.4%, power -4.97%", (0, 300, 0), g3, [(F(3, 0.4), F(4, 0))])
    place3()

    camera(root, [
        ((0.0, 800.0, 0.0), 4200.0, 0.25, 0.10),
        ((3000.0, 400.0, 0.0), 4600.0, 0.15, 0.20),
        ((6000.0, 1000.0, 0.0), 4900.0, 0.20, 0.10),
        ((9000.0, 300.0, 0.0), 8600.0, 0.08, 0.35),
    ])
    finish("sec4", page="melt")


# ---- 5. pull rates ------------------------------------------------------------------------


MM_PER_RATE = 600.0  # bar length per mm/min


def sec5():
    m, root = begin(5)
    g = empty("rates", root)
    plinth(g, -300, 4100, -400, 300, y=-60)
    rows = [
        ("dash neck max 6.0 (US 6866713)", 6.0, 1500, m["gold"], 0, 0.1, 0.6),
        ("300 mm body 1.6 (2023 sim)", 1.6, 1050, m["blue"], 1, 0.1, 0.5),
        ("neck example 2.4 (US 5578284)", 2.4, 600, m["gold"], 2, 0.1, 0.45),
        ("dash-free neck <= 0.5", 0.5, 150, m["grey"], 2, 0.45, 0.65),
    ]
    box("zero_line", (-30, -60, -40), (0, 1700, 40), m["steel"], g)
    for k, (text, rate, y, mm, b, u0, u1) in enumerate(rows):
        grow_hbar(g, f"rate{k}", 0, y, 0, rate * MM_PER_RATE, 220, mm, F(b, u0), F(b, u1))
        label(text, (rate * MM_PER_RATE, y + 110, 110), g, [(F(b, u1 - 0.05), END)])
    run(g, "fast", 12, [(0, 1500, 130), (6.0 * MM_PER_RATE, 1500, 130)], 40, m["flow_hot"], 3, 0.0, 0.85, 24)
    run(g, "slow", 4, [(0, 1050, 130), (1.6 * MM_PER_RATE, 1050, 130)], 40, m["argon"], 3, 0.0, 0.6, 96)
    label("neck: fast, purges dislocations", (1800, 1700, 0), g, beat(3))
    label("body: slow, keeps the interface flat", (900, 850, 130), g, beat(3))
    camera(root, [
        ((2000.0, 850.0, 0.0), 8600.0, 0.06, 0.10),
        ((2000.0, 850.0, 0.0), 8600.0, 0.06, 0.10),
        ((2000.0, 850.0, 0.0), 8600.0, 0.06, 0.10),
        ((2000.0, 1000.0, 0.0), 8200.0, 0.08, 0.12),
    ])
    finish("sec5", page="melt")


# ---- 6. who owns the crystal ------------------------------------------------------------


def sec6():
    m, root = begin(6)
    g = empty("shares", root)
    plinth(g, -500, 3700, -400, 400)
    data = [("Shin-Etsu 26.7%", 26.7), ("SUMCO 25.0%", 25.0), ("GlobalWafers 15.0%", 15.0), ("Siltronic 11.7%", 11.7), ("SK Siltron 9.2%", 9.2)]
    for k, (text, v) in enumerate(data):
        x = 800 * k
        grow_bar(g, f"share{k}", x, 0, 520, v * 100, m["blue"], F(0, 0.08 + 0.1 * k), F(0, 0.4 + 0.1 * k))
        label(text, (x, v * 100, 260), g, [(F(0, 0.3 + 0.1 * k), END)])
        if k < 2:
            hl = empty(f"top{k}", g)
            box(f"top{k}_m", (x - 270, 0, -270), (x + 270, v * 100 + 20, 270), m["gold"], hl)
            show(hl, [(F(1, 0.1), END)])
    label("Report Prime estimate, low reliability", (1600, 2900, 0), g, beat(0))
    label("top two about 51.7%", (400, 2800, 270), g, [(F(1, 0.2), F(2, 0))])
    label("listed five add to 87.6%, page says 77%", (2400, 1700, 270), g, [(F(1, 0.45), F(2, 0))])

    # beat 2: other sources on a 0-100% axis
    g2, place2 = placed(root, "others", 7000)
    plinth(g2, -300, 5300, -300, 300)
    box("pct_axis", (0, 0, -30), (5000, 30, 30), m["steel"], g2)
    for k in range(11):
        box(f"pct{k}", (500 * k - 8, 0, -50), (500 * k + 8, 90, 50), m["steel"], g2)
    rows = [("Omdia 2020: top five 94%", 94, 94, 1500), ("Shin-Etsu + SUMCO 53-55%", 53, 55, 1000), ("2023 blurbs: top five 82-85%", 82, 85, 500)]
    for k, (text, a, b, y) in enumerate(rows):
        e = empty(f"src{k}", g2)
        if a == b:
            ball(f"src{k}_m", (a * 50, y, 0), 70, m["gold_glow"], e, 16)
        else:
            box(f"src{k}_m", (a * 50, y - 50, -50), (b * 50, y + 50, 50), m["gold_glow"], e)
        tube(f"src{k}_stem", (a * 50, 30, -10), (a * 50, y, -10), 8, m["steel"], e, verts=6)
        show(e, [(F(2, 0.1 + 0.25 * k), END)])
        label(text, (b * 50 + 60, y, 0), g2, [(F(2, 0.15 + 0.25 * k), F(3, 0))])
    label("0 to 100%", (5000, 60, 0), g2, beat(2))
    place2()

    # beat 3: each maker grows its own crystal
    g3, place3 = placed(root, "pullers", 14500)
    plinth(g3, -400, 4400, -400, 400)
    for k, (text, _) in enumerate(data):
        x = 1000 * k
        box(f"cab{k}_back", (x - 300, 0, -320), (x + 300, 1400, -280), m["dark_steel"], g3)
        box(f"cab{k}_base", (x - 300, 0, -300), (x + 300, 200, 300), m["dark_steel"], g3)
        box(f"cab{k}_melt", (x - 200, 200, -250), (x + 200, 260, 200), m["melt_si"], g3)
        grow_bar(g3, f"xt{k}", x, -20, 160, 1000, m["xtal"], F(3, 0.1 + 0.08 * k), F(3, 0.7 + 0.05 * k), y0=260)
        label(text.split(" ")[0], (x + 300, 1400, -280), g3, beat(3))
    label("each maker grows its own crystals", (2000, 1700, 0), g3, beat(3))
    place3()

    camera(root, [
        ((1600.0, 1300.0, 0.0), 6800.0, 0.12, 0.12),
        ((1600.0, 1300.0, 0.0), 6800.0, 0.05, 0.12),
        ((9700.0, 900.0, 0.0), 10500.0, 0.06, 0.12),
        ((16500.0, 850.0, 0.0), 9000.0, 0.08, 0.14),
    ])
    finish("sec6", page="melt")


# ---- 7. chokepoints and risks ------------------------------------------------------------


def sec7():
    m, root = begin(7)
    # beat 0: the crucible wears, and its quartz supply is cut
    g0 = empty("crucible_wear", root)
    K.crucible(g0, m, tags={"quartz": ("crucible consumed every pull", beat(0))})
    wear = pivot("wear", (0, CRU_Y0, 0), g0)
    cut(shell("wear_m", 0, 0, CRU_R - 24, 0, K.CRU_TOP - CRU_Y0, 30, m["quartz"], wear), 16.0)
    scale_keys(wear, [(0, 1.0), (F(0, 0.05), 1.0), (F(0, 0.9), (1, 1, 0.35)), (END, (1, 1, 0.35))])
    box("spruce", (-2900, 0, -500), (-2100, 700, 100), m["quartz"], g0)
    label("Spruce Pine, NC: high-purity quartz", (-2900, 700, 100), g0, beat(0))
    supply = [(-2100, 350, -200), (-900, 350, -200), (-CRU_R - 60, 700, -200)]
    tube("supply0", supply[0], supply[1], 50, m["pipe_glass"], g0, verts=16)
    tube("supply1", supply[1], supply[2], 50, m["pipe_glass"], g0, verts=16)
    run(g0, "quartz_flow", 8, supply, 40, m["quartz"], 0, 0.0, 0.45, 40)
    x = empty("cut_x", g0)
    for s in (-1, 1):
        o = box(f"x{s:+d}", (-1500 - 14, 200, -150), (-1500 + 14, 500, -130), m["red"], x)
        o.rotation_euler = (0, s * 0.6, 0)
    show(x, [(F(0, 0.55), F(1, 0))])
    label("an outage idles the pullers", (-1500, 520, -140), g0, [(F(0, 0.6), F(1, 0))])

    # beat 1: a dislocation in the body, then a remelt
    g1, place1 = placed(root, "remelt", 3500)
    K.crucible(g1, m, tags={})
    p0 = NECK + SHOULDER + 600.0
    xt = body_only(g1, m, p0, p_keys=[(0, p0), (F(1, 0.45), p0), (F(1, 0.95), NECK + 40.0)])
    line = pivot("disloc", (0, MELT_Y + BODY_TOP, 0), xt)
    tube("disloc_m", (30, 0, XTAL_R + 3), (60, -560, XTAL_R + 3), 4, m["disloc"], line, verts=6)
    scale_keys(line, [(0, (OFF,) * 3), (F(1, 0.05), (1, 1, OFF)), (F(1, 0.35), 1.0), (F(1, 0.5), 1.0), (F(1, 0.51), (OFF,) * 3)], until=F(1, 0.05))
    label("one dislocation in the body", (XTAL_R, MELT_Y + 400, 60), g1, [(F(1, 0.15), F(1, 0.5))])
    label("remelt: the pull starts again", (CRU_R, MELT_Y + 60, 20), g1, [(F(1, 0.55), F(2, 0))])
    place1()

    # beat 2: uniformity across a 300 mm wafer
    g2, place2 = placed(root, "uniformity", 7000)
    disc("wafer", (0, 0, 0), 620, 20, m["grey"], g2, 96)
    levels = [m["argon"], m["gold"], m["red"]]
    rnd = random.Random(7)
    scatter, even = empty("scatter", g2), empty("even", g2)
    for i in range(-5, 6):
        for j in range(-5, 6):
            cx, cz = 110 * i, 110 * j
            if cx * cx + cz * cz > 560 * 560:
                continue
            box(f"c{i}_{j}", (cx - 45, 10, cz - 45), (cx + 45, 40 + 50 * rnd.random(), cz + 45), levels[rnd.randrange(3)], scatter)
            box(f"e{i}_{j}", (cx - 45, 10, cz - 45), (cx + 45, 55, cz + 45), levels[1], even)
    show(scatter, [(0, F(2, 0.55))])
    show(even, [(F(2, 0.55), END)])
    label("oxygen and dopant vary across it", (620, 60, 0), g2, [(F(2, 0.05), F(2, 0.55))])
    label("rotation control evens it out", (620, 60, 0), g2, [(F(2, 0.6), F(3, 0))])
    place2()

    # beat 3: SEMI's 2023 falls, hanging down from the axis
    g3, place3 = placed(root, "semi", 10500)
    box("semi_axis", (-300, 1500, -40), (3300, 1540, 40), m["steel"], g3)
    falls = [("revenue -10.9% to $12.3B", 10.9), ("polished 300 mm -13%", 13.0), ("epi 300 mm -5%", 5.0), ("area -14.3%", 14.3)]
    for k, (text, v) in enumerate(falls):
        xk = 800 * k
        b = pivot(f"fall{k}", (xk, 1500, 0), g3)
        box(f"fall{k}_m", (-250, -v * 90, -250), (250, 0, 250), m["red"] if k == 3 else m["blue"], b)
        scale_keys(b, [(0, (OFF,) * 3), (F(3, 0.08 + 0.15 * k), (1, 1, OFF)), (F(3, 0.3 + 0.15 * k), 1.0), (END, 1.0)], until=F(3, 0.08 + 0.15 * k))
        label(text, (xk + 250, 1500 - v * 90, 250), g3, [(F(3, 0.25 + 0.15 * k), END)])
    label("SEMI, 2023 vs 2022", (1200, 1600, 0), g3, beat(3))
    place3()

    camera(root, [
        ((-1250.0, 550.0, 0.0), 6800.0, 0.14, 0.14),
        ((3500.0, 1000.0, 0.0), 3000.0, 0.25, 0.12),
        ((7000.0, 0.0, 0.0), 2600.0, 0.05, 0.75),
        ((11700.0, 900.0, 0.0), 7200.0, 0.08, 0.10),
    ])
    finish("sec7", page="melt")


# ---- 8. listed names ---------------------------------------------------------------------


def tile(g, name, x, y, w, h, text, f0, m, iv=None):
    e = empty(name, g)
    box(f"{name}_b", (x - w / 2, y - h / 2, -80), (x + w / 2, y + h / 2, 0), m["paper"], e)
    box(f"{name}_rule", (x - w / 2 + 40, y + h / 2 - 70, 0), (x + w / 2 - 40, y + h / 2 - 50, 6), m["gold"], e)
    key(e, f0, "location", P(0, 900, 300))
    key(e, f0 + 14, "location", P(0, 0, 0))
    show(e, [(f0, END)])
    label(text, (x - w / 2 + 40, y, 10), e, iv or [(f0 + 10, END)])
    return e


def sec8():
    m, root = begin(8)
    g = empty("names", root)
    names = ["Shin-Etsu Chemical 4063.T", "SUMCO 3436.T", "GlobalWafers 6488.TWO", "Siltronic SSG.DE, WAF.DE"]
    for k, text in enumerate(names):
        tile(g, f"t{k}", -900 + 1800 * (k % 2), 1400 - 800 * (k // 2), 1600, 600, text, F(0, 0.08 + 0.15 * k), m)

    # beat 1: SK Siltron slides inside SK Inc
    tile(g, "sk", 0, -400, 2600, 800, "SK Inc 034730.KS", F(1, 0.05), m)
    sub = empty("siltron", g)
    box("siltron_b", (-500, -620, -60), (500, -340, 20), m["blue"], sub)
    key(sub, F(1, 0.3), "location", P(2600, 0, 0))
    key(sub, F(1, 0.6), "location", P(0, 0, 0))
    show(sub, [(F(1, 0.3), END)])
    label("SK Siltron: held by SK Inc", (500, -480, 20), sub, [(F(1, 0.55), END)])

    # beat 2: the puller makers, beside a crystal rising
    g2, place2 = placed(root, "puller", 4200)
    K.crucible(g2, m, tags={})
    p_keys = [(0, NECK + SHOULDER), (F(2, 0.05), NECK + SHOULDER), (F(2, 0.95), NECK + SHOULDER + 900.0)]
    K.crystal(g2, m, p_keys, 0, tags={})
    label("puller maker: PVA TePla TPL.DE", (XTAL_R, MELT_Y + 900, 10), g2, [(F(2, 0.2), END)])
    label("puller maker: Ferrotec 6890.T", (XTAL_R, MELT_Y + 400, 10), g2, [(F(2, 0.4), END)])
    place2()

    # beat 3: the sourcing stamp
    stamp = empty("stamp", g)
    box("stamp_b", (-1500, -1300, 20), (1500, -950, 60), m["red"], stamp)
    stamp.rotation_euler = (0, 0, 0.0)
    show(stamp, [(F(3, 0.2), F(3, 0.3)), (F(3, 0.36), F(3, 0.46)), (F(3, 0.52), END)])
    label("general knowledge, not fetched", (-1400, -1120, 60), stamp, [(F(3, 0.52), END)])

    camera(root, [
        ((0.0, 1050.0, 0.0), 7600.0, 0.04, 0.12),
        ((0.0, 500.0, 0.0), 8600.0, 0.04, 0.12),
        ((4200.0, 1400.0, 0.0), 3600.0, 0.22, 0.10),
        ((0.0, 200.0, 0.0), 10500.0, 0.04, 0.12),
    ])
    finish("sec8", page="melt")


# ---- 9. sources -------------------------------------------------------------------------


def sec9():
    m, root = begin(9)
    g = empty("sources", root)
    plinth(g, -3300, 3300, -1700, 1700)
    cards = {
        1: ("[1] COMSOL Cz furnace model", 0),
        4: ("[4] Synthetic Crystals 52(4), 2023", 0),
        3: ("[3] US 6866713, 5578284, 7179330", 1),
        2: ("[2] Wikipedia: Czochralski method", 2),
        8: ("[8] Wikipedia: Wafer (electronics)", 2),
        5: ("[5] Report Prime wafer shares", 3),
        6: ("[6] SEMI 2023, via substack", 3),
        7: ("[7] Omdia 2020, via KED Global", 3),
    }
    order = {b: [n for n, (_, bb) in cards.items() if bb == b] for b in range(4)}
    for n in range(1, 9):
        text, b = cards[n]
        x = -2400 + 1600 * ((n - 1) % 4)
        z = -800 if n <= 4 else 800
        box(f"card{n}", (x - 700, 0, z - 500), (x + 700, 30, z + 500), m["paper"], g)
        box(f"card{n}_rule", (x - 600, 30, z - 380), (x + 300, 34, z - 340), m["grey"], g)
        lit = empty(f"lit{n}", g)
        box(f"lit{n}_m", (x - 600, 34, z - 380), (x + 300, 40, z - 340), m["gold_glow"], lit)
        u = 0.15 + 0.3 * order[b].index(n)
        show(lit, [(F(b, u), END)])
        label(text, (x - 700, 40, z + 500), g, [(F(b, u), END)])
    camera(root, [
        ((0.0, 0.0, 0.0), 13500.0, 0.06, 0.85),
        ((0.0, 0.0, 0.0), 13200.0, 0.03, 0.85),
        ((0.0, 0.0, 0.0), 13200.0, 0.0, 0.85),
        ((0.0, 0.0, 0.0), 13500.0, -0.03, 0.85),
    ])
    finish("sec9", page="melt")


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [str(n) for n in range(1, 10)]
    for n in which:
        globals()[f"sec{n}"]()
