"""The three MELT + PULL zoom-ins, authored in Blender and exported for pbr3d in the SAND template
(docs/diagram-pages.md), built from the puller pieces in melt_kit.py.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/melt_zooms.py [-- neck conv hot]

For each zoom it writes blender/melt_<name>.blend and assets/melt_<name>.glb.

  a neck  the seed touches and dislocations appear; the dash neck is pulled and they slide out;
          the neck carries the crystal's weight; a dislocation that gets through forces a remelt
  b conv  the melt convects in two loops; a horizontal magnetic field slows them; the interface
          under the crystal flattens; SiO bubbles off the quartz and oxygen freezes in
  c hot   heater and felt round the crucible; the axial gradient up the crystal; the heat
          shield catching radiant heat; argon carrying SiO and CO out of the base

One beat is SEC (8) seconds at 24 fps; every zoom is four beats.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, ball, beat, box, cut, disc, empty, key, label, mat, pivot, rel, show, tube  # noqa: E402
from sand_zooms import camera, finish, scale_keys, start  # noqa: E402
from poly_overview import keyed_path, run  # noqa: E402
import melt_kit as K  # noqa: E402
from melt_kit import (  # noqa: E402
    BODY_TOP,
    CRU_R,
    CRU_TOP,
    CRU_Y0,
    END,
    HEAT_R,
    MELT_Y,
    NECK,
    NECK_BOT,
    SHELL_R,
    SHIELD_R0,
    SHIELD_R1,
    SHIELD_Y0,
    SHIELD_Y1,
    SHOULDER,
    SUS_R,
    XTAL_R,
)

BEATS = 4


def begin(name):
    m, root = start(name, BEATS, page="melt")
    K.mats(m)
    return m, root


# ---- a: the dash neck -------------------------------------------------------------------


def neck():
    m, root = begin("neck")
    nr = 8.0  # thicker than the overview's neck so the dislocations inside it read
    contact = F(0, 0.45)
    grown_body = 400.0
    p_keys = [
        (0, 320.0),
        (F(0, 0.1), 320.0),
        (contact, 0.0),
        (F(1, 0.05), 0.0),
        (F(1, 0.9), NECK),
        (F(2, 0.05), NECK),
        (F(2, 0.7), NECK + SHOULDER + grown_body),
        (F(3, 0.45), NECK + SHOULDER + grown_body),
        (F(3, 0.92), NECK + 30.0),
        (F(4, 0), NECK + 30.0),
    ]
    K.furnace(root, m, tags={}, pull_chamber=False)
    K.crucible(root, m, tags={})
    g = K.crystal(root, m, p_keys, contact, neck_r=nr, tags={
        "seed": [(F(0, 0.05), F(0, 0.5))],
        "neck": ("dash neck: 2-4 mm, up to 6 mm/min", beat(1)),
    })

    # sparks where the seed meets the melt
    for k in range(10):
        a = 2 * math.pi * k / 10
        run(root, f"spark{k}_", 1, [(0, MELT_Y + 4, 20), (90 * math.cos(a), MELT_Y + 30 + 20 * (k % 3), 20 + 40 * math.sin(a))], 4, m["flow_hot"], 0, 0.46, 0.46, 12)
    label("contact shock: dislocations", (14, MELT_Y + 22, 14), g, [(F(0, 0.5), F(1, 0))])

    # dislocations: red lines thrown into the seed at contact (beat 0), then in the neck as it is
    # pulled; each glides outward and leaves through the surface (beat 1)
    dis = empty("dislocations", g)
    for k in range(5):
        e = empty(f"disloc_seed{k}", dis)
        x = -10 + 5 * k
        tube(f"disloc_seed{k}_m", (x - 4, MELT_Y + 6 + 6 * k, 13), (x + 4, MELT_Y + 18 + 6 * k, 13), 1.4, m["disloc"], e, verts=6)
        show(e, [(contact + 2, F(1, 0.3 + 0.08 * k))])
    for k in range(8):
        e = empty(f"disloc_neck{k}", dis)
        y = MELT_Y - 12 - 13 * k
        s = 1 if k % 2 else -1
        tube(f"disloc_neck{k}_m", (-3 * s, y - 4, nr + 1), (3 * s, y + 4, nr + 1), 1.2, m["disloc"], e, verts=6)
        f0 = F(1, 0.1 + 0.09 * k)
        key(e, f0, "location", P(0, 0, 0))
        key(e, f0 + 30, "location", P(s * (nr + 6), 0, 0), linear=True)
        show(e, [(f0, f0 + 30)])
    label("dislocations glide out the sides", (nr + 2, MELT_Y + 40, 10), g, [(F(1, 0.35), F(2, 0))])

    # beat 2: the weight on the neck
    arrow = empty("weight", root)
    ax = XTAL_R + 160
    tube("weight_shaft", (ax, 1500, 0), (ax, 1050, 0), 18, m["disloc"], arrow, verts=12)
    tip = K.cone("weight_tip", 1050, 960, 0.5, 45, m["disloc"], arrow)
    tip.location.x = ax
    show(arrow, [(F(2, 0.55), F(3, 0))])
    crack = empty("crack", g)
    disc("crack_ring", (0, MELT_Y - 60, 0), nr + 4, 4, m["disloc"], crack, 24)
    show(crack, [(F(2, 0.7), F(2, 0.78)), (F(2, 0.84), F(2, 0.92))])
    label("dash neck holds about 100 kg", (nr + 4, MELT_Y - 60, 10), g, [(F(2, 0.55), F(3, 0))])
    label("300 mm crystal: several hundred kg", (ax, 1300, 0), root, [(F(2, 0.6), F(3, 0))])

    # beat 3: a dislocation that got through runs down the body; the crystal is melted back
    line = pivot("body_disloc", (0, MELT_Y + BODY_TOP, 0), g)
    tube("body_disloc_m", (40, 0, XTAL_R + 3), (70, -grown_body + 20, XTAL_R + 3), 3, m["disloc"], line, verts=6)
    scale_keys(line, [(0, (OFF,) * 3), (F(3, 0.05), (1, 1, OFF)), (F(3, 0.4), 1.0), (F(3, 0.5), 1.0), (F(3, 0.51), (OFF,) * 3)], until=F(3, 0.05))
    label("a dislocation reaches the body", (70, MELT_Y + BODY_TOP - 200, XTAL_R), g, [(F(3, 0.15), F(3, 0.5))])
    label("remelt: back into the pool", (XTAL_R, MELT_Y + 40, 10), root, [(F(3, 0.55), F(4, 0))])

    camera(root, [
        ((0.0, MELT_Y + 150, 0.0), 820.0, 0.30, 0.10),  # the seed is in frame as it comes down
        ((0.0, MELT_Y + 50, 0.0), 700.0, 0.30, 0.10),
        ((0.0, MELT_Y + 380, 0.0), 2300.0, 0.28, 0.10),
        ((0.0, MELT_Y + 300, 0.0), 2100.0, 0.28, 0.10),
    ])
    finish("neck", page="melt")


# ---- b: melt convection and the magnetic field -------------------------------------------


def conv():
    m, root = begin("conv")
    p = NECK + SHOULDER + 500.0
    K.furnace(root, m, tags={}, pull_chamber=False)
    K.crucible(root, m, tags={})
    g = K.crystal(root, m, K.static_p(p), 0, tags={}, wire=False)

    def loop(s, inset=0.0):
        """One convection cell on the cut face: up the hot wall, in along the surface, down near
        the crystal, out along the floor. `s` is the side (+1 right, -1 left)."""
        x_out, x_in = s * (CRU_R - 60 - inset), s * (XTAL_R + 30 + inset)
        y_lo, y_hi = CRU_Y0 + 70, MELT_Y - 40
        c = [(x_out, y_lo, 24), (x_out, y_hi, 24), (x_in, y_hi, 24), (x_in, y_lo, 24)]
        return c + c + [c[0]]

    for s in (-1, 1):
        run(root, f"fast{s:+d}_", 10, loop(s), 16, m["flow_hot"], 0, 0.0, 0.55, 80)
        run(root, f"slow1{s:+d}_", 4, loop(s, 30)[:5], 14, m["flow_hot"], 1, 0.35, 0.7, 150)
        run(root, f"slow2{s:+d}_", 3, loop(s, 30)[:5], 14, m["flow_hot"], 2, 0.0, 0.6, 150)
        run(root, f"slow3{s:+d}_", 3, loop(s, 30)[:5], 14, m["flow_hot"], 3, 0.0, 0.6, 150)
    label("hot wall: melt rises", (CRU_R - 60, MELT_Y - 160, 24), root, beat(0))
    label("cooler melt sinks under the crystal", (-XTAL_R - 30, CRU_Y0 + 140, 24), root, beat(0))
    label("crystal 5 rpm, crucible -5 rpm", (XTAL_R, MELT_Y + 260, 10), root, beat(0))

    # beat 1 on: magnet coils outside the chamber and a horizontal field across the melt
    mag = empty("magnet", root)
    for s in (-1, 1):
        box(f"coil{s:+d}", (s * (SHELL_R + 80) - 120, 300, -500), (s * (SHELL_R + 80) + 120, 1200, 300), m["copper"], mag)
    for k in range(5):
        tube(f"field{k}", (-SHELL_R - 40, CRU_Y0 + 60 + 70 * k, 40 + 6 * k), (SHELL_R + 40, CRU_Y0 + 60 + 70 * k, 40 + 6 * k), 4, m["field"], mag, verts=6)
    show(mag, [(F(1, 0.1), F(3, 0))])
    label("horizontal magnetic field", (SHELL_R + 200, 1200, 300), mag, beat(1))
    label("the flow slows: silicon conducts", (CRU_R - 90, MELT_Y - 120, 24), root, [(F(1, 0.45), F(2, 0))])

    # beat 2: the interface under the crystal relaxes from a bulge to flat
    bulge = pivot("bulge", (0, MELT_Y, 0), root)
    cut(ball("bulge_m", (0, 0, 0), XTAL_R - 2, m["xtal"], bulge, 32), 22.0)
    scale_keys(bulge, [(0, (1, 1, 0.55)), (F(2, 0.1), (1, 1, 0.55)), (F(2, 0.8), (1, 1, 0.04)), (END, (1, 1, 0.04))])
    label("interface: bulge relaxes to flat", (XTAL_R - 20, MELT_Y - 50, 24), root, beat(2))

    # beat 3: SiO from the quartz wall; oxygen specks freeze into the crystal
    for s in (-1, 1):
        for k in range(3):
            y0 = CRU_Y0 + 80 + 90 * k
            run(root, f"sio{s:+d}{k}_", 3, [(s * (CRU_R - 30), y0, 24), (s * (CRU_R - 120), MELT_Y, 24), (s * (CRU_R - 140), MELT_Y + 300, 24)], 12, m["sio_b"], 3, 0.05 + 0.1 * k, 0.7, 70)
    label("quartz dissolves: SiO2 + Si to 2SiO", (-CRU_R + 30, CRU_Y0 + 200, 24), root, beat(3))
    specks = empty("oxygen", g)
    for k in range(14):
        a = -0.9 + 1.8 * ((k * 7) % 14) / 13
        y = MELT_Y - p + 20 + 25 * (k % 7)  # crystal-local: the group sits p above its build height
        ball(f"o{k}", (XTAL_R * math.sin(a), y, XTAL_R * math.cos(a)), 6, m["oxygen"], specks, 8)
    show(specks, [(F(3, 0.45), END)])
    label("about 1e18 oxygen atoms per cm3", (XTAL_R, MELT_Y + 120, 60), root, [(F(3, 0.5), F(4, 0))])

    camera(root, [
        # beat 0: yawed so the crystal stands to one side and the melt surface reads across it
        ((0.0, 650.0, 0.0), 1650.0, 0.95, 0.30),
        ((0.0, 750.0, 0.0), 3900.0, 0.22, 0.12),
        ((0.0, 740.0, 0.0), 1500.0, 0.22, 0.16),
        ((0.0, 720.0, 0.0), 1650.0, 0.22, 0.10),
    ])
    finish("conv", page="melt")


# ---- c: the hot zone and the argon sweep -------------------------------------------------


def hot():
    m, root = begin("hot")
    p = NECK + SHOULDER + 1000.0
    K.furnace(root, m, tags={"heater": beat(0), "felt": beat(0), "shield": beat(2)})
    K.crucible(root, m, tags={"susceptor": beat(0)})
    g = K.crystal(root, m, K.static_p(p), 0, tags={})

    # beat 1: colour bands up the crystal, hot at the melt to cool higher up
    bands = empty("gradient", g)
    n = 6
    seg = 1000.0 / n
    for k in range(n):
        u = k / (n - 1)
        mm = mat(f"band{k}", (1.0 - 0.55 * u, 0.45 - 0.1 * u, 0.15 + 0.45 * u), rough=0.4, emit=(1.0, 0.35, 0.08), strength=2.2 * (1 - u) ** 2)
        top = MELT_Y + BODY_TOP - 1000.0 + seg * (k + 1)  # band 0 (hottest) at the melt
        disc(f"band{k}_m", (0, top - seg / 2, 0), XTAL_R + 3, seg - 4, mm, bands, 48)
    show(bands, [(F(1, 0.05), F(2, 0))])
    label("near 1414 C at the melt", (XTAL_R, MELT_Y + 60, 10), root, beat(1))
    label("gradient 500 to 100 C per metre", (XTAL_R + 3, MELT_Y + 700, 10), root, beat(1))

    # beat 2: radiant heat off the melt, caught by the shield's underside
    for s in (-1, 1):
        for k in range(3):
            x0 = s * (XTAL_R + 70 + 60 * k)
            run(root, f"rad{s:+d}{k}_", 4, [(x0, MELT_Y + 5, 30), (s * (SHIELD_R0 + 40 + 70 * k), SHIELD_Y0 + 70 + 80 * k, 30)], 12, m["radiant"], 2, 0.05 + 0.1 * k, 0.8, 30)
    label("shield blocks radiant heat", (SHIELD_R1 - 60, SHIELD_Y1 - 60, 10), root, [(F(2, 0.3), F(3, 0))])

    # beat 3: argon down past the crystal and out, carrying SiO off the melt and CO off the graphite
    K.argon(root, m, 3, tags={"argon": ("argon 100 L/min at 2500 Pa", beat(3))})
    for s in (-1, 1):
        run(root, f"sio{s:+d}_", 6, [(s * (XTAL_R + 60), MELT_Y + 10, 26), (s * (CRU_R - 40), MELT_Y + 40, 26), (s * (SUS_R + 50), CRU_TOP + 40, 26), (s * (HEAT_R + 70), 300, 26), (s * (SHELL_R - 120), 140, 26)], 22, m["sio_b"], 3, 0.15, 0.8, 70)
        run(root, f"co{s:+d}_", 4, [(s * (HEAT_R + 20), 800, 28), (s * (HEAT_R + 70), 300, 28), (s * (SHELL_R - 120), 140, 28), (s * (SHELL_R + 280), 120, -200)], 26, m["co_b"], 3, 0.25, 0.8, 60)
    label("SiO and CO out the base", (SHELL_R + 200, 120, -200), root, [(F(3, 0.35), F(4, 0))])

    camera(root, [
        # beat 0: higher and pitched down so the heater and felt read round the crucible, not
        # hidden behind the crystal's cone
        ((0.0, 950.0, 0.0), 3900.0, 0.24, 0.34),
        ((0.0, 1300.0, 0.0), 4200.0, 0.24, 0.10),
        # beat 2: yawed off the crystal so the melt and shield both show
        ((0.0, 900.0, 0.0), 2300.0, 0.95, 0.22),
        ((0.0, 1500.0, 0.0), 6200.0, 0.24, 0.10),
    ])
    finish("hot", page="melt")


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["neck", "conv", "hot"]
    for name in which:
        globals()[name]()
