"""TRM_MODULAR_DATA_CENTER: a data hall built from factory modules trucked to site and joined.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_modular_data_center.py

Left: a factory floor where white-space pods, power skids and cooling units are built and tested.
Middle: a road with flatbed trucks. Right: a concrete pad where the modules are set side by side
and their power, coolant and fiber seams are joined.

Beats:
  0 idea      factory, road and pad: the hall is built somewhere else
  1 factory   pods wired, piped and load-tested indoors (beads loop inside each pod)
  2 ship      trucks carry the modules to the pad
  3 join      modules set side by side; power, water and fiber cross the seams; racks light
  4 grow      more pods arrive to add capacity; size limit by road width; tickers
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from sand_overview import P, key  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_MODULAR_DATA_CENTER"
BEATS = [
    ("A modular data center is a hall built from factory-made blocks",
     "Instead of pouring and fitting out a whole building on site, the hall is split into modules: white-space pods "
     "that hold racks, power skids with switchgear and UPS, and cooling units. Each is built in a factory, shipped, "
     "and joined to the others on a prepared concrete pad."),
    ("In the factory, wiring, piping and testing are done indoors",
     "Crews on an assembly line pull the cable, fit busways and coolant pipes, and load-test each module with heater "
     "banks before it leaves. Factory work is faster and more repeatable than field work, and it is not held up by "
     "weather or by finding enough skilled electricians near the site."),
    ("Modules ship by road, so their size is capped",
     "Each block has to fit on a truck and under bridges, roughly 3-4 m wide and up to ~15 m long. That limit sets "
     "how much power one module can hold, so big sites use many of them. Meanwhile the pad, grid hookup and permits "
     "are prepared in parallel on site."),
    ("On site the modules are set and their seams joined",
     "A crane sets each block on the pad. Electricians connect the power links between skids and pods, pipefitters "
     "couple the coolant loops, and fiber is spliced across. Because each part was tested already, commissioning "
     "takes weeks instead of months, and capacity comes online sooner."),
    ("Need more capacity? Add another block",
     "Operators can grow a site block by block as demand arrives instead of building the whole hall up front, which "
     "suits fast-moving AI demand. Prefab power and cooling is a growing share of sales for the big electrical and "
     "thermal suppliers. Related: Vertiv (VRT), Eaton (ETN), Schneider Electric (SU.PA), Legrand (LR.PA)."),
]

# modules: (kind, width x, depth z, height)
MW, MD, MH = 16.0, 50.0, 22.0
PAD = (90.0, 230.0)  # pad x span, z -110..-30
FAC = (-230.0, -90.0)  # factory x span
SLOTS = [100.0, 120.0, 140.0, 160.0, 180.0, 200.0]  # module x positions on the pad (left edge)
KINDS = ["power", "pod", "pod", "pod", "cool", "pod"]


def mats(m):
    m["ground"] = mat("md_ground", (0.30, 0.34, 0.24), rough=0.95)
    m["concrete"] = mat("md_conc", (0.58, 0.58, 0.56), rough=0.9)
    m["shell"] = mat("md_shell", (0.88, 0.89, 0.90), metal=0.3, rough=0.45)
    m["shell_p"] = mat("md_shell_p", (0.30, 0.34, 0.40), metal=0.4, rough=0.45)
    m["shell_c"] = mat("md_shell_c", (0.55, 0.70, 0.80), metal=0.4, rough=0.45)
    m["rack"] = mat("md_rack", (0.08, 0.08, 0.10), metal=0.5, rough=0.45)
    m["truck"] = mat("md_truck", (0.15, 0.30, 0.65), metal=0.4, rough=0.4)
    m["fac"] = mat("md_fac", (0.70, 0.70, 0.68), metal=0.3, rough=0.6)
    m["led_g"] = mat("md_led", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)
    m["hv"] = mat("md_hv", (1.0, 0.85, 0.40), emit=(1.0, 0.80, 0.30), strength=4.0)
    m["cold_b"] = mat("md_cold", (0.30, 0.70, 1.0), emit=(0.25, 0.65, 1.0), strength=4.0)
    m["fib_b"] = mat("md_fib", (0.85, 0.45, 1.0), emit=(0.80, 0.40, 1.0), strength=4.0)
    m["seam"] = mat("md_seam", (1.0, 0.85, 0.30), emit=(1.0, 0.80, 0.25), strength=3.0)


def slide(g, moves):
    for f, d in moves:
        key(g, f, "location", P(*d))


def module(m, root, name, kind, x0, z0):
    """A module with its roof cut away. Returns (group, led group, top centre)."""
    g = empty(name, root)
    sh = {"pod": "shell", "power": "shell_p", "cool": "shell_c"}[kind]
    p = [bx(f"{name}_fl", (x0, 0.0, z0 - MD), (x0 + MW, 1.0, z0), m["steel"], g),
         bx(f"{name}_wl", (x0, 1.0, z0 - MD), (x0 + 0.6, MH, z0), m[sh], g),
         bx(f"{name}_wr", (x0 + MW - 0.6, 1.0, z0 - MD), (x0 + MW, MH, z0), m[sh], g),
         bx(f"{name}_wb", (x0, 1.0, z0 - MD), (x0 + MW, MH, z0 - MD + 0.6), m[sh], g),
         bx(f"{name}_rail", (x0, MH, z0 - MD), (x0 + MW, MH + 0.8, z0), m[sh], g)]
    for k in range(5):
        z = z0 - MD + 2 + k * (MD - 4) / 4
        p.append(bx(f"{name}_rib{k}", (x0 - 0.3, 1.0, z - 0.4), (x0 + 0.1, MH, z + 0.4), m["steel"], g))
    leds = empty(f"{name}_leds", root)
    if kind == "pod":
        for side in (0, 1):
            xa = x0 + 1.0 if side == 0 else x0 + MW - 5.0
            for i in range(8):
                z = z0 - MD + 3 + i * 5.6
                p.append(bx(f"{name}_r{side}{i}", (xa, 1.0, z), (xa + 4.0, 18.0, z + 5.0), m["rack"], g))
                for j in range(3):
                    xf = xa + 4.0 if side == 0 else xa - 0.2
                    bx(f"{name}_l{side}{i}{j}", (xf, 4 + j * 5, z + 0.8), (xf + 0.2, 4.8 + j * 5, z + 4.2), m["led_g"], leds)
        p.append(bx(f"{name}_bus", (x0 + 2, 19.5, z0 - MD + 2), (x0 + MW - 2, 20.5, z0 - 2), m["copper"], g))
    elif kind == "power":
        for i in range(6):
            z = z0 - MD + 3 + i * 7.5
            p.append(bx(f"{name}_sg{i}", (x0 + 2, 1.0, z), (x0 + 9, 16.0, z + 6.5), m["dark"], g))
            p.append(bx(f"{name}_bt{i}", (x0 + 10, 1.0, z), (x0 + 14, 12.0, z + 6.5), m["batt"] if "batt" in m else m["dark"], g))
            bx(f"{name}_l{i}", (x0 + 9, 12.0, z + 1), (x0 + 9.3, 13.0, z + 5), m["led_g"], leds)
    else:
        for i in range(3):
            zc = z0 - MD / 2 + (i - 1) * 15
            p.append(bx(f"{name}_hx{i}", (x0 + 2, 1.0, zc - 6), (x0 + 14, 12.0, zc + 6), m["chiller"] if "chiller" in m else m["steel"], g))
            p.append(D.tube(f"{name}_fan{i}", (x0 + 8, MH, zc), (x0 + 8, MH + 1.2, zc), 5.0, m["grid"], g, 18))
            bx(f"{name}_l{i}", (x0 + 2, 9.0, zc + 6), (x0 + 14, 10.0, zc + 6.3), m["led_g"], leds)
    D.join(p, f"{name}_m")
    if leds.children:
        D.join(list(leds.children), f"{name}_ledm")
    return g, leds, (x0 + MW / 2, MH, z0 - MD / 2)


def truck(m, g, name, x, z):
    bx(f"{name}_cab", (x + 4, 0.5, z), (x + 14, 12, z + 10), m["truck"], g)
    bx(f"{name}_bed", (x - 2, 2.0, z - MD - 2), (x + MW + 2, 3.5, z), m["steel"], g)
    for wz in (z - MD + 4, z - 12, z + 6):
        for side in (-1.5, MW + 1.5):
            D.tube(f"{name}_w{wz:.0f}{side}", (x + side - 0.8, 2.2, wz), (x + side + 0.8, 2.2, wz), 2.2, m["rubber"], g, 12)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    site = empty("site", root)
    s = [bx("ground", (-260.0, -3.0, -200.0), (270.0, -1.5, 60.0), m["ground"], site),
         bx("road", (-90.0, -1.5, 10.0), (240.0, -1.0, 40.0), m["concrete"], site),
         bx("pad", (PAD[0], -1.5, -110.0), (PAD[1], 0.0, -30.0), m["concrete"], site),
         # factory: floor, back wall, left wall, roof trusses
         bx("fac_fl", (FAC[0], -1.5, -140.0), (FAC[1], 0.0, 0.0), m["concrete"], site),
         bx("fac_wb", (FAC[0], 0.0, -140.0), (FAC[1], 50.0, -137.0), m["fac"], site),
         bx("fac_wl", (FAC[0], 0.0, -140.0), (FAC[0] + 3, 50.0, 0.0), m["fac"], site)]
    for k in range(8):
        x = FAC[0] + 4 + k * 19
        s.append(bx(f"fac_t{k}", (x - 0.8, 48.0, -140.0), (x + 0.8, 50.0, 0.0), m["steel"], site))
    # factory crane rails
    s.append(bx("fac_rail", (FAC[0], 40.0, -100.0), (FAC[1], 41.5, -98.0), m["steel"], site))
    for k in range(3):  # utility hookups waiting on the pad
        s.append(bx(f"stub{k}", (PAD[0] + 2, 0.0, -112.0 - k * 4), (PAD[1] - 2, 1.5, -110.5 - k * 4), m[("copper", "pipe" if "pipe" in m else "steel", "steel")[k]], site))
    D.join(s, "site_m")

    # factory line: 3 modules being built (always there), with test-load beads looping inside
    fac_mods = []
    for k, kind in enumerate(("pod", "power", "cool")):
        x0 = FAC[0] + 15 + k * 40
        g, leds, top = module(m, root, f"f{k}", kind, x0, -20.0)
        fac_mods.append((g, leds, top, x0))
        show(leds, [(F(1, 0.3), F(2, 0))])
        loop = [(x0 + 3, 20.0, -22.0), (x0 + 3, 20.0, -68.0), (x0 + MW - 3, 20.0, -68.0), (x0 + MW - 3, 20.0, -22.0), (x0 + 3, 20.0, -22.0)]
        run(root, f"test{k}", loop, 8, 1.1, m["hv"], [1], 0.1, 0.6, 70)
        rise(root, f"theat{k}", (x0 + MW / 2, MH, -45.0), 5, 0.9, m["heat"], [1], 0.3, 0.9, 16.0, 40, (4.0, 18.0))
        # workers / test rigs: a small cart by each
        bx(f"cart{k}", (x0 + MW + 3, 0.0, -30.0), (x0 + MW + 9, 8.0, -24.0), m["dark"], site)

    # pad modules: each rides from the factory over the road on a truck, then sets on its pad slot
    pad = []
    for k, (x0, kind) in enumerate(zip(SLOTS, KINDS)):
        g, leds, top = module(m, root, f"p{k}", kind, x0, -35.0)
        tk = empty(f"tk{k}", g)
        truck(m, tk, f"tk{k}", x0, -35.0)
        late = k >= 4 and kind == "pod" or k == 5
        if not late:
            ship0, ship1 = F(2, 0.05 + 0.12 * k), F(2, 0.45 + 0.12 * k)
            set_f = F(3, 0.05 + 0.08 * k)
        else:
            ship0, ship1 = F(4, 0.05), F(4, 0.45)
            set_f = F(4, 0.6)
        start = (FAC[0] + 20 - x0, 0.0, 0.0)
        road = (FAC[1] + 10 - x0, 0.0, 70.0)
        near = (0.0, 0.0, 70.0)
        slide(g, [(0, (0, -400, 0)), (ship0 - 1, (0, -400, 0)), (ship0, start), ((ship0 + ship1) // 2, road), (ship1, near),
                  (set_f, near), (set_f + 25, (0, 0, 0))])
        C.show(tk, [(0, set_f + 25)]) if hasattr(C, "show") else show(tk, [(0, set_f + 25)])
        on = set_f + 40
        show(leds, [(on, F(5, 0))])
        pad.append((g, top, x0, kind))

    # seams: glowing joins between neighbours once set (beat 3 on)
    seams = empty("seams", root)
    for k in range(len(SLOTS) - 1):
        x = SLOTS[k] + MW
        bx(f"seam{k}", (x - 0.3, 1.0, -84.0), (x + 4.3, 2.0, -36.0), m["seam"], seams)
        bx(f"seamt{k}", (x - 0.3, MH - 1.0, -84.0), (x + 4.3, MH, -36.0), m["seam"], seams)
    show(seams, [(F(3, 0.45), F(4, 0.0)), (F(4, 0.75), F(4, 0.95))])
    # power from the skid across the pods, coolant from the cooler, fiber across the top
    y = MH - 0.5
    run(root, "pwr", [(SLOTS[0] + 8, 16.0, -50.0), (SLOTS[0] + 8, y, -50.0), (SLOTS[3] + 8, y, -50.0)], 8, 1.1, m["hv"], [3], 0.55, 0.95, 40)
    run(root, "cool", [(SLOTS[4] + 8, 12.0, -70.0), (SLOTS[4] + 8, y, -70.0), (SLOTS[1] + 8, y, -70.0)], 8, 1.1, m["cold_b"], [3], 0.6, 0.95, 40)
    run(root, "fib", [(PAD[1] + 10, 1.0, -112.0), (SLOTS[3] + 8, y, -60.0), (SLOTS[1] + 8, y, -60.0)], 6, 1.0, m["fib_b"], [3], 0.6, 0.95, 40)
    run(root, "pwr4", [(SLOTS[0] + 8, 16.0, -50.0), (SLOTS[0] + 8, y, -50.0), (SLOTS[5] + 8, y, -50.0)], 8, 1.1, m["hv"], [4], 0.7, 0.98, 40)
    # width limit marker on the road in beat 2
    lim = empty("limit", root)
    for xx in (-20.0, -20.0 + MW + 4):
        bx(f"lim{xx:.0f}", (xx - 0.4, 0.0, 30.0), (xx + 0.4, 28.0, 31.0), m["warn"], lim)
    bx("lim_t", (-20.4, 27.0, 30.0), (-20.0 + MW + 4.4, 28.0, 31.0), m["warn"], lim)
    show(lim, [(F(2, 0.1), F(3, 0))])

    tags = {
        0: [("factory: modules built", (FAC[0] + 70, 52.0, -60.0)), ("road", (60.0, 0.0, 25.0)),
            ("site pad", (160.0, 1.0, -105.0))],
        1: [("white-space pod: racks", (FAC[0] + 23, MH + 2, -45.0)), ("power skid", (FAC[0] + 63, MH + 2, -45.0)),
            ("cooling unit", (FAC[0] + 103, MH + 2, -45.0)), ("load-tested before it ships", (FAC[0] + 60, 30.0, -100.0))],
        2: [("fits a truck: ~3-4 m wide", (-10.0, 30.0, 30.0)), ("pad + grid prepared in parallel", (160.0, 1.0, -112.0))],
        3: [("set side by side", (150.0, MH + 2, -40.0)), ("power across the seams", (SLOTS[2] + 8, MH, -50.0)),
            ("coolant coupled", (SLOTS[3] + 8, MH, -70.0)), ("weeks, not months", (SLOTS[1] + 8, MH + 6, -90.0))],
        4: [("add a block for more MW", (SLOTS[5] + 8, MH + 2, -60.0)), ("VRT ETN SU.PA LR.PA", (130.0, MH + 8, -60.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((0.0, 10.0, -50.0), 470.0, 0.25, 0.55, pad=1.0),
        frame((FAC[0] + 70, 12.0, -50.0), 160.0, 0.30, 0.65),
        [(0.0, frame((-60.0, 8.0, 0.0), 260.0, 0.20, 0.45)), (0.55, frame((60.0, 8.0, -20.0), 300.0, 0.25, 0.45))],
        frame((160.0, 10.0, -65.0), 160.0, 0.35, 0.60),
        frame((150.0, 10.0, -50.0), 220.0, -0.30, 0.50),
    ], root)


if __name__ == "__main__":
    build()
