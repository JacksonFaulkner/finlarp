"""The OPTICAL FIBER node's overview: the glass run from the laser to the photodiode, in the SAND
template (docs/diagram-pages.md), built from the detailed parts of the numbered sections.

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_fibre_overview.py

Writes blender/fiber_fibre_overview.blend and assets/fiber_fibre_overview.glb. One beat is 8 s.
Units mm, Y up, camera on +z, parts cut in half at z = 0 so the glass shows inside.

The link on its board, left to right: a laser TO-can, a lens, an LC ferrule assembly (zirconia
ferrule, holder, spring) with the fibre's end in its tip, the coated fibre run (drawn short), the
far ferrule, a lens, the photodiode can, and an arched wire to its amplifier chip. Hardware and
glass are drawn 1 mm for 25 um, with the core widened so it shows. A magnifier ring on the run calls
out a cut segment of glass above it, drawn wider still, where the rays and the loss can be seen.

Beats (match the seven beats in diagrams_nodes/fiber/fibre/overview.rs):
  0 the link      the whole link on its board; the fibre's core glows end to end
  1 ferrule       light from the laser window, through the lens, enters the core at the glass end
  2 core          in the magnified segment rays zig-zag down the core: total internal reflection
  3 loss          in the segment each light packet dims and a little light scatters out
  4 reach         light runs the whole length; the run is drawn short (real runs are kilometres)
  5 far end       the far ferrule holds the glass end; light leaves toward the photodiode
  6 next          PHOTODIODE: light lands, current rides the wire to the amplifier
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, beat, box, empty, label, show, tube  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import fiber_kit as K  # noqa: E402
import fiber_fibre_detail as D  # noqa: E402
from fiber_fibre_detail import glide, grow_ray, pulses, rbox, shell  # noqa: E402
import fiber_fibre_sections as S  # noqa: E402

PAGE = "fiber_fibre"
NAME = "overview"
BEATS = 7
END = F(BEATS, 0)

camera = glide  # zooms replace this to hold their own poses

LASER_X, LENS_A, TIP_A = -225.0, -205.0, -185.0  # laser window face, lens, left ferrule tip
TIP_B, LENS_B, PD_X = 235.0, 255.0, 275.0  # right ferrule tip, lens, photodiode window face
RUN_X0, RUN_X1 = -35.0, 85.0  # the coated run between the two ferrule assemblies
BOARD_Y = -40.0
MAG_X, SEG_Y, SEG_X0, SEG_X1 = 25.0, 110.0, -45.0, 95.0  # magnifier ring and the callout segment

POSES = [
    ((35, 10, 0), 870.0, 0.30, 0.28),     # 0 the whole link
    ((-203, 0, 0), 120.0, 0.45, 0.22),    # 1 the laser end
    ((25, 112, 0), 205.0, 0.25, 0.20),    # 2 the magnified segment: rays
    ((30, 104, 0), 190.0, 0.35, 0.25),    # 3 the segment: loss
    ((25, 0, 0), 620.0, 0.20, 0.55),      # 4 the whole run from above
    ((248, 0, 0), 120.0, 0.45, 0.22),     # 5 the far end
    ((298, -5, 0), 150.0, 0.40, 0.25),     # 6 photodiode and its wire
]


def ferrule_at(m, root, name, tip_x, s):
    """An LC ferrule assembly with its tip at x = tip_x, its body toward -s*x, on two posts."""
    g = empty(name, root)
    S.lc_ferrule(m, g, s, funnel=True)
    g.location = P(tip_x, 0, 0)
    for dx in (-74.0, -30.0):
        x = tip_x + s * dx
        r = 31.0 if dx == -74.0 else 25.0
        tube(f"{name}_post{int(dx)}", (x, -r, -4), (x, BOARD_Y, -4), 2.5, m["dark_steel"], root, 10)
    return g


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = D.materials(K.materials())

    # board, laser, lenses, ferrules, run, photodiode, amplifier chip
    rbox("board", (-260, BOARD_Y - 6, -70), (345, BOARD_Y, 40), m["board"], root, 0.0)
    g = empty("laser", root)
    S.can(m, g, LASER_X, 0.0, 1, "laser")
    S.lens(m, empty("lens_a", root), LENS_A, 0.0, 9.0)
    ferrule_at(m, root, "ferrule_a", TIP_A, -1.0)
    run = empty("run", root)
    S.x_shell("run_core", RUN_X0, RUN_X1, 0, 0.5, m["lit"], run)
    S.x_shell("run_clad", RUN_X0, RUN_X1, 0.5, 2.5, m["clad"], run)
    S.x_shell("run_coat", RUN_X0, RUN_X1, 2.5, 5.0, m["secondary"], run)
    for x in (-10.0, 60.0):
        rbox(f"clamp_{x}", (x - 3, BOARD_Y, -10), (x + 3, -5.0, 0), m["steel"], root, 0.4)
    ferrule_at(m, root, "ferrule_b", TIP_B, 1.0)
    S.lens(m, empty("lens_b", root), LENS_B, 0.0, 9.0)
    g = empty("pd", root)
    S.can(m, g, PD_X, 0.0, -1, "pd")
    rbox("tia", (312, BOARD_Y, -12), (334, BOARD_Y + 6, 6), m["die"], root, 0.4)

    # light cones: laser to lens to core, core to lens to photodiode
    beams = empty("beams", root)
    for name, a, b, ra, rb in (("ba", LASER_X + 1.2, LENS_A - 3, 1.5, 7.0), ("bb", LENS_A + 3, TIP_A - 0.2, 7.0, 0.5),
                               ("bc", TIP_B + 0.2, LENS_B - 3, 0.5, 7.0), ("bd", LENS_B + 3, PD_X - 1.2, 7.0, 1.5)):
        shell(name, (a, 0, 0), (b, 0, 0), 0, (ra, rb), m["glow"], beams, half=False, n=24)

    # the magnifier: a ring on the run, two guide lines, and a cut segment of glass above it
    shell("mag_ring", (MAG_X - 3, 0, 0), (MAG_X + 3, 0, 0), 6.5, 8.5, m["dark_steel"], root, half=False, n=32)
    for x0, x1 in ((MAG_X - 3, SEG_X0), (MAG_X + 3, SEG_X1)):
        tube(f"mag_line_{x1}", (x0, 8.5, 0), (x1, SEG_Y - 25.0, 0), 0.6, m["normal"], root, 6)
    seg = empty("segment", root)
    S.x_shell("seg_core", SEG_X0, SEG_X1, 0, 10.0, m["core"], seg, y=SEG_Y)
    S.x_shell("seg_clad", SEG_X0, SEG_X1, 10.0, 25.0, m["clad"], seg, y=SEG_Y)
    # the coating, stripped back in steps so every layer shows: soft primary, hard secondary
    S.x_shell("seg_pri", SEG_X0, SEG_X0 + 85, 25.0, 31.0, m["primary"], seg, y=SEG_Y)
    S.x_shell("seg_sec", SEG_X0, SEG_X0 + 55, 31.0, 36.0, m["secondary"], seg, y=SEG_Y)
    # frozen-in density ripples in the glass (what scatters the light, beat 3)
    rg = random.Random(7)
    for k in range(70):
        ball(f"seg_grain{k}", (rg.uniform(SEG_X0 + 2, SEG_X1 - 2), SEG_Y + rg.uniform(-9, 9), rg.uniform(-3, 0.3)),
             0.35, m["normal"], seg, 6)
    ray = S.zigzag(SEG_X0, SEG_X1, SEG_Y, 10.0, 0.3)
    grow_ray("seg_ray", ray, 0.6, m["ray"], root, F(2, 0.05), F(2, 0.7), END)
    for i, sl in enumerate((0.5, 0.17)):
        rz = S.zigzag(SEG_X0, SEG_X1, SEG_Y, 10.0, sl, z=0.4 + 0.1 * i, up=bool(i))
        grow_ray(f"seg_ray_m{i}", rz, 0.45, m["ray"], root, F(2, 0.2 + 0.1 * i), F(2, 0.8), END)
        for b in (2, 3):
            pulses(root, f"seg_ph{b}_{i}", 3, rz[0], S.rel_path(rz), 1.3, m["spark"], b, 0.1, 0.7, 60, steps=len(rz) * 2)
    pulses(root, "seg_pk2", 3, ray[0], S.rel_path(ray), 1.6, m["lit"], 2, 0.3, 0.75, 60, steps=24)
    pulses(root, "seg_pk3", 4, (SEG_X0, SEG_Y, 0.8), [(0, 0, 0), (SEG_X1 - SEG_X0, 0, 0)], 2.6, m["lit"], 3,
           0.0, 0.6, 90, scale_to=(0.4, 0.4, 0.4))
    rnd = random.Random(4)
    for k in range(30):
        x = rnd.uniform(SEG_X0 + 10, SEG_X1 - 10)
        e = empty(f"sp_{k}", root)
        ball(f"sp_{k}_s", (x, SEG_Y, 1.2), 1.4, m["spark"], e, 8)
        f0 = F(3, rnd.uniform(0.05, 0.8))
        D.fly(e, [(0, 0, 0), (rnd.uniform(-4, 4), (1 if k % 2 else -1) * 44, rnd.uniform(0, 18))], f0, f0 + 30, steps=2)
        show(e, [(f0, f0 + 30)])

    # light down the whole link, every beat (through the lenses, along the core)
    path = [(LASER_X + 1.2, 0, 0.6), (TIP_A, 0, 0.6), (TIP_B, 0, 0.6), (PD_X - 1.2, 0, 0.6)]
    for b in range(BEATS):
        n = 6 if b == 4 else 3
        pulses(root, f"link{b}", n, path[0], S.rel_path(path), 1.6, m["lit"], b, 0.0, 0.6, 90, steps=12)

    # current: beads ride an arched wire from the photodiode to the amplifier chip (beat 6)
    wire = [(PD_X + 14, -4, 0), (292, 12, 0), (304, 20, 0), (316, 16, 0), (322, 6, 0), (323, BOARD_Y + 6, 0)]
    for k in range(len(wire) - 1):
        tube(f"wire_{k}", wire[k], wire[k + 1], 0.9, m["copper"], root, 8)
        if k:
            ball(f"wire_j{k}", wire[k], 0.9, m["copper"], root, 8)
    pulses(root, "amps", 4, wire[0], S.rel_path(wire), 1.5, m["elec"], 6, 0.3, 0.8, 40, steps=12)

    labels = {
        0: [("LASER", (LASER_X - 6, 9, 0)),
            ("FERRULE", (TIP_A + 40, 25, -1)),
            ("OPTICAL FIBER", (25, 5, -1)),
            ("FERRULE", (TIP_B - 40, 25, -1)),
            ("PHOTODIODE", (PD_X + 6, 9, 0))],
        1: [("LASER window", (LASER_X + 1.2, 0, 0)),
            ("LENS focuses on the core", (LENS_A, 9, 0)),
            ("FERRULE tip: the glass end", (TIP_A, 12, 0))],
        2: [("MAGNIFIED: core drawn wide", (SEG_X0 + 15, SEG_Y + 25, -1)),
            ("CORE: rays turn back at the wall", (ray[2][0], ray[2][1], 0.6)),
            ("CLADDING: lower index", (SEG_X1 - 15, SEG_Y - 18, 0.2)),
            ("COATING: soft primary, hard secondary", (SEG_X0 + 30, SEG_Y - 33, 0.2))],
        3: [("packets dim as they run", (SEG_X1 - 20, SEG_Y, 0.8)),
            ("a little scatters out", (SEG_X0 + 30, SEG_Y + 16, 0.2)),
            ("density ripples in the glass scatter it", (SEG_X0 + 70, SEG_Y - 6, 0.3))],
        4: [("drawn short: real runs are km", (25, 5, -1)),
            ("light end to end", (TIP_B - 60, 0, 0.6))],
        5: [("FERRULE: holds the glass end", (TIP_B - 20, 25, -1)),
            ("light leaves the core", (TIP_B + 2, 0, 0.6)),
            ("LENS onto the photodiode", (LENS_B, 9, 0))],
        6: [("PHOTODIODE: light to current", (PD_X + 6, 9, 0)),
            ("current to the amplifier", (304, 20, 0)),
            ("TIA chip", (323, BOARD_Y + 6, 0))],
    }
    for i, items in labels.items():
        for text, at in items:
            label(text, at, root, beat(i))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
