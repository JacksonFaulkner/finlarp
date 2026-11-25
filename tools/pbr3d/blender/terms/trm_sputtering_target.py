"""TRM_SPUTTERING_TARGET: the Terms-tab overview for sputtering targets (PVD).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_sputtering_target.py

Writes assets/term_TRM_SPUTTERING_TARGET.glb. Captions live in specs/terms/TRM_SPUTTERING_TARGET.json.

A PVD chamber cut open: a metal target bonded to a copper backing plate with a magnet pack behind it,
argon plasma glowing under it, ions striking up and metal atoms flying down to the wafer, where a film
grows. The bench holds a spent target cut open (grains, racetrack groove); a cluster tool sits behind.

Beats:
  0 target   pure metal disc bonded to a copper backing plate, in a vacuum chamber
  1 plasma   argon ions hit the target, magnets trap electrons in a ring
  2 film     knocked-off atoms fly to the wafer and a film grows
  3 wear     racetrack groove, grains and purity; a consumable
  4 fab      many PVD chambers per tool wire up chips; tickers
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
from sand_overview import mat, tube, disc  # noqa: E402
from term_common import F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_SPUTTERING_TARGET"
BEATS = [
    ("A sputtering target is a slab of ultra-pure metal facing the wafer",
     "The target is a disc or plate of copper, tantalum, titanium, aluminum or tungsten, often 99.999% pure or "
     "better, bonded to a copper backing plate that carries away heat. It is clamped in the lid of a vacuum "
     "chamber, face down, with the wafer below it."),
    ("Argon plasma ions slam into the target and knock atoms loose",
     "Argon gas is let in and a high voltage turns it into a glowing plasma. Positive argon ions accelerate into "
     "the negatively biased target and chip off metal atoms one by one. Magnets behind the target trap electrons "
     "in a ring near its face, which makes the plasma denser and the process faster."),
    ("The freed atoms land on the wafer as a thin, even metal film",
     "The knocked-off atoms fly across the chamber and stick to the wafer, building a film a few nanometers to a "
     "micron thick. This is physical vapor deposition (PVD). Chips use it for barrier and seed layers, contacts "
     "and the wiring that joins transistors and memory cells."),
    ("The target wears a groove and must meet tight purity and grain specs",
     "Under the magnet ring the target erodes fastest, cutting a racetrack groove, and it is swapped out before "
     "the groove breaks through. Impurities or uneven grain size make the film uneven or add defects, so targets "
     "are refined, forged and rolled to strict specs. That makes them a steady consumable tied to wafer starts."),
    ("Every metal layer in a fab runs through PVD chambers using targets",
     "A cluster tool holds several PVD chambers round a robot, and a modern chip passes through them for many "
     "layers. More wafers, more metal layers and more advanced packaging all burn more targets. Related: "
     "Materion (MTRN), Entegris (ENTG), Applied Materials (AMAT)."),
]

CC = (0.0, 0.0, 0.0)      # chamber centre x/z
TY = 70.0                  # target face height
WY = 22.0                  # wafer top
BENCH = (170.0, 0.0, 0.0)


def mats(m):
    m["st_metal"] = mat("st_metal", (0.70, 0.72, 0.78), metal=1.0, rough=0.25)
    m["st_cu"] = mat("st_cu", (0.90, 0.50, 0.28), metal=1.0, rough=0.25)
    m["st_wafer"] = mat("st_wafer", (0.30, 0.32, 0.42), metal=0.6, rough=0.15)
    m["st_film"] = mat("st_film", (0.85, 0.86, 0.90), metal=1.0, rough=0.1)
    m["st_plasma"] = mat("st_plasma", (0.75, 0.40, 1.0), emit=(0.70, 0.35, 1.0), strength=1.5, alpha=0.35)
    m["st_ion"] = mat("st_ion", (0.85, 0.45, 1.0), emit=(0.85, 0.45, 1.0), strength=4.0)
    m["st_atom"] = mat("st_atom", (0.75, 0.85, 1.0), emit=(0.6, 0.8, 1.0), strength=3.0)
    m["st_grain_a"] = mat("st_grain_a", (0.62, 0.64, 0.70), metal=1.0, rough=0.35)
    m["st_grain_b"] = mat("st_grain_b", (0.78, 0.80, 0.85), metal=1.0, rough=0.2)


def chamber(m, root):
    """Cut-away chamber: back half walls only so the inside shows."""
    g = empty("ch", root)
    R = 45.0
    for k in range(13):  # back half wall as staves
        a0 = math.pi + math.pi * k / 13
        a1 = math.pi + math.pi * (k + 1) / 13
        x0, z0 = R * math.cos(a0), R * math.sin(a0)
        x1, z1 = R * math.cos(a1), R * math.sin(a1)
        bx(f"ch_wall{k}", (min(x0, x1) - 1, 0.0, min(z0, z1) - 1), (max(x0, x1) + 1, 95.0, max(z0, z1) + 1),
           m["sup_steel"], g)
    disc("ch_floor", (0.0, 1.0, 0.0), R + 1, 2.0, m["sup_steel"], g)
    disc("ch_lid", (0.0, 93.0, 0.0), R + 3, 4.0, m["sup_steel"], g)
    # magnet pack + backing plate + target
    mag = empty("ch_mag", g)
    for k in range(12):
        a = 2 * math.pi * k / 12
        K.magnet(m, mag, f"ch_m{k}", (24.0 * math.cos(a), 86.0, 24.0 * math.sin(a)), (5, 5, 5), "n")
    K.magnet(m, mag, "ch_mc", (0.0, 86.0, 0.0), (7, 5, 7), "s")
    disc("ch_back", (0.0, 80.0, 0.0), 36.0, 5.0, m["st_cu"], g)
    disc("ch_target", (0.0, TY + 2.5, 0.0), 34.0, 5.0, m["st_metal"], g)
    # wafer on chuck
    disc("ch_chuck", (0.0, 10.0, 0.0), 30.0, 18.0, m["sup_steel"], g)
    disc("ch_wafer", (0.0, WY - 1.0, 0.0), 28.0, 1.5, m["st_wafer"], g)
    K.pipe(m, g, "ch_ar", [(-60.0, 60.0, -30.0), (-44.0, 60.0, -30.0)], 2.0)
    K.pipe(m, g, "ch_pump", [(0.0, 0.0, -44.0), (0.0, -2.0, -60.0)], 5.0)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    mats(m)
    bx("floor", (-160.0, -3.0, -110.0), (240.0, 0.0, 70.0), m["sup_steel"], root)
    chamber(m, root)

    plasma = empty("plasma", root)
    disc("pl_glow", (0.0, TY - 6.0, 0.0), 30.0, 8.0, m["st_plasma"], plasma)
    K.ring(m, plasma, "pl_ring", (0.0, TY - 2.0, 0.0), 24.0, 1.2, "st_ion", "y", 32)
    show(plasma, [(F(1, 0), F(3, 0)), (F(4, 0), F(5, 0))])

    # ions up to target, atoms down to wafer
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, z = 24.0 * math.cos(a), 24.0 * math.sin(a)
        run(root, f"ion{k}", [(x * 0.8, TY - 14.0, z * 0.8), (x, TY - 0.5, z)], 3, 1.0, m["st_ion"], [1, 2], 0.05, 0.8, 18)
        tx, tz = 22.0 * math.cos(a + 0.9) * 0.9, 22.0 * math.sin(a + 0.9) * 0.9
        run(root, f"atom{k}", [(x, TY - 1.0, z), (tx, WY + 0.5, tz)], 3, 0.9, m["st_atom"], [2, 4], 0.1, 0.85, 30)

    # film grows in steps
    for s in range(4):
        f = disc(f"film{s}", (0.0, WY + 0.2 + s * 0.4, 0.0), 27.5, 0.4, m["st_film"], root)
        show(f, [(F(2, 0.2 + 0.18 * s), F(5, 0))])

    # bench: spent target cut in half, grains + racetrack groove
    bg = empty("bench", root)
    bx0, bx1 = BENCH[0] - 45, BENCH[0] + 45
    bx("bn_table", (bx0 - 8, 0.0, -25.0), (bx1 + 8, 10.0, 25.0), m["sup_steel"], bg)
    bx("bn_back", (bx0, 10.0, -12.0), (bx1, 16.0, 0.0), m["st_cu"], bg)
    groove = [(BENCH[0] - 24.0), (BENCH[0] + 24.0)]
    nx, ny = 18, 4
    for i in range(nx):
        x = bx0 + i * 5.0
        depth = sum(max(0.0, 1 - abs(x + 2.5 - gx) / 11.0) for gx in groove) * 3
        for j in range(ny):
            y0 = 16.0 + j * 4.0
            if y0 + 4.0 > 32.0 - depth * 3.0 and j >= ny - int(depth + 0.5):
                continue
            mt = "st_grain_a" if (i + j) % 2 else "st_grain_b"
            bx(f"bn_g{i}_{j}", (x + 0.15, y0 + 0.15, -12.0), (x + 4.85, y0 + 3.85, 0.0), m[mt], bg)
    show(bg, [(F(3, 0), F(5, 0))])
    C.magnify(m, root, (24.0, TY, 34.0), (BENCH[0] - 45.0, 25.0, 0.0), name="mag")

    # cluster tool behind: robot hub + PVD chambers
    cl = empty("cluster", root)
    hub = (60.0, 0.0, -80.0)
    disc("cl_hub", (hub[0], 12.0, hub[2]), 16.0, 24.0, m["sup_steel"], cl)
    for k in range(5):
        a = math.pi * (0.1 + 0.2 * k) + math.pi
        cx, cz = hub[0] + 34.0 * math.cos(a), hub[2] - 34.0 * math.sin(a) * -1
        disc(f"cl_ch{k}", (cx, 15.0, cz), 12.0, 30.0, m["sup_steel"], cl)
        disc(f"cl_lid{k}", (cx, 31.0, cz), 9.0, 2.0, m["st_cu"], cl)
        run(root, f"cl_w{k}", [(hub[0], 26.0, hub[2]), (cx, 33.0, cz)], 2, 1.2, m["st_atom"], [4], 0.1 + 0.1 * k, 0.9, 25)

    C.tags(root, {
        0: [("target: 99.999% pure metal", (34.0, TY + 2.5, 0.0)), ("copper backing plate", (-36.0, 80.0, 0.0)),
            ("wafer below, in vacuum", (28.0, WY, 0.0)), ("magnets behind", (0.0, 90.0, -24.0))],
        1: [("argon plasma", (-30.0, TY - 6.0, 0.0)), ("ions hit the target", (24.0, TY - 8.0, 0.0)),
            ("magnet ring traps electrons", (-24.0, TY - 2.0, 10.0))],
        2: [("atoms knocked loose", (0.0, TY - 15.0, 20.0)), ("film grows on the wafer", (27.0, WY + 1.5, 0.0)),
            ("PVD: barrier, seed, wiring", (-45.0, 40.0, 0.0))],
        3: [("racetrack groove", (BENCH[0] - 24.0, 28.0, 0.0)), ("grain size must be even", (BENCH[0] + 5.0, 32.0, 0.0)),
            ("swapped before break-through", (bx1, 16.0, 0.0))],
        4: [("cluster tool: many chambers", (hub[0], 26.0, hub[2])), ("every metal layer", (0.0, WY, 25.0)),
            ("MTRN, ENTG, AMAT", (BENCH[0], 30.0, 0.0))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 50.0, 0.0), 110.0, 0.30, 0.20),
        frame((0.0, TY - 8.0, 0.0), 75.0, 0.25, 0.15),
        [(0.0, frame((0.0, 45.0, 0.0), 80.0, 0.20, 0.10)), (1.0, frame((0.0, 30.0, 0.0), 70.0, 0.15, 0.35))],
        frame((BENCH[0], 22.0, 0.0), 100.0, 0.10, 0.20),
        frame((60.0, 30.0, -30.0), 260.0, 0.30, 0.45),
    ], root)


if __name__ == "__main__":
    build()
