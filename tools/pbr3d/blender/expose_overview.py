"""The EXPOSE node page's overview (FRONT END, EXPOSE), in the picture-and-panel template (docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/expose_overview.py

Writes blender/expose_overview.blend and assets/expose_overview.glb. One beat is 8 s.

One EUV tool, cut open at z = 0, left to right: a CO2 drive laser cabinet, the source vessel (tin
droplet nozzle above, collector mirror around the plasma, cut open), the intermediate focus on the
scanner wall, and the scanner housing (illuminator mirrors, reflective reticle, six projection
mirrors, wafer on its stage). Glowing beads ride the real light path; tin drops fall from the nozzle.

Beats (match the seven beats in diagrams_nodes/expose/overview.rs):
  0 print     the whole run: light from the plasma through the scanner onto the wafer
  1 tin       droplets fall from the nozzle, about 50,000 a second
  2 pulses    pre-pulse swells the droplet, the CO2 main pulse makes the plasma
  3 collector the collector mirror gathers the light to the intermediate focus
  4 scanner   illuminator, reticle, six mirrors, the pattern lands on the wafer
  5 one maker ASML integrates the tool, ZEISS supplies every mirror
  6 High-NA   0.55 NA: 8 nm CD, anamorphic 4x/8x, half-size fields

power_grid_zooms.py is not used here: this page has no zoom-ins (scope cut for the POC).
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, mat, cut, box, ball, disc, tube, wall, show, label, beat, _smooth, _name  # noqa: E402
from sand_zooms import start  # noqa: E402
from power_grid_detail import finish, frame, camera_path, run  # noqa: E402

PAGE = "expose"
NAME = "overview"
BEATS = 7

# ---- layout (poly units, Y up, camera on +z) -----------------------------------------------------

CX = -1250.0  # the source vessel's axis (poly x)
VESSEL_R = 420.0
VESSEL_TOP = 820.0
PLASMA = (CX, 470.0, 0.0)
COLL_R = 380.0  # collector shell around the plasma
IF = (-700.0, 470.0, 0.0)  # intermediate focus, on the scanner's wall
NOZZLE_TOP = 940.0
LASER_X = (-2050.0, -1700.0)  # CO2 drive laser cabinet

HOUSE_X = (-640.0, 1600.0)  # scanner housing
HOUSE_TOP = 1000.0
HOUSE_Z = 480.0

I1 = (-450.0, 470.0, 0.0)  # illuminator mirrors
I2 = (-260.0, 330.0, 0.0)
RET = (40.0, 886.0, 0.0)  # reflective reticle
PROJ = [  # six projection mirrors, light order
    (320.0, 700.0, 0.0),
    (520.0, 860.0, 0.0),
    (760.0, 620.0, 0.0),
    (900.0, 820.0, 0.0),
    (1080.0, 420.0, 0.0),
    (1200.0, 300.0, 0.0),
]
WAFER = (1200.0, 160.0, 0.0)  # top of the wafer, where the light lands
STAGE_Y = 130.0

# the EUV light path: intermediate focus -> illuminator -> reticle -> projection -> wafer
LIGHT = [IF, I1, I2, RET] + PROJ + [WAFER]
COLLECT = [PLASMA, (CX + COLL_R, 470.0, 0.0), IF]  # plasma -> collector edge -> intermediate focus

POSES = [
    frame((-200.0, 500.0, 0.0), 3900.0, 0.32, 0.20),
    frame((CX, 700.0, 0.0), 900.0, 0.30, 0.12),
    frame((-1400.0, 470.0, 0.0), 1300.0, 0.25, 0.10),
    frame((-1000.0, 520.0, 0.0), 1000.0, 0.45, 0.25),
    frame((480.0, 500.0, 0.0), 2300.0, 0.30, 0.20),
    frame((-200.0, 500.0, 0.0), 3300.0, 0.70, 0.30),
    frame((850.0, 480.0, 0.0), 1400.0, -0.15, 0.12),
]


# ---- helpers -------------------------------------------------------------------------------------


def fold(prev, at, nxt):
    """The unit normal of a mirror at `at` that turns the light from `prev` toward `nxt`."""
    a = (Vector(prev) - Vector(at)).normalized()
    b = (Vector(nxt) - Vector(at)).normalized()
    return (a + b).normalized()


def mirror(name, c, prev, nxt, r, m, parent):
    """A round mirror at poly point c, its face turned to fold the light from prev to nxt."""
    o = disc(name, c, r, 14.0, m, parent, verts=64)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(P(*fold(prev, c, nxt)).normalized())
    return o


def shell_sphere(name, c, r, thick, m, parent):
    """A thin spherical shell (the collector), closed; cut open by the caller."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=64, ring_count=32, location=P(*c))
    o = _name(bpy.context.object, name)
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = thick
    mod.offset = -1.0
    mod.use_rim = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(m)
    o.parent = parent
    _smooth(o)
    return o


def cylinder_wall_at(name, cx, r, y0, y1, thick, m, parent):
    """A hollow upright cylinder (the source vessel) standing at poly x = cx."""
    o = wall(name, r, y0, y1, thick, m, parent)
    o.location.x += cx
    return o


# ---- the scene -------------------------------------------------------------------------------------


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    steel = mat("euv_steel", (0.36, 0.38, 0.42), metal=0.6, rough=0.4)
    dark = mat("euv_dark", (0.16, 0.17, 0.20), metal=0.5, rough=0.5)
    floor = mat("euv_floor", (0.42, 0.43, 0.45), rough=0.8)
    cab = mat("euv_cabinet", (0.80, 0.52, 0.18), metal=0.3, rough=0.5)
    tin = mat("euv_tin", (0.75, 0.77, 0.80), metal=0.9, rough=0.3)
    co2 = mat("euv_co2", (1.0, 0.45, 0.20), emit=(1.0, 0.40, 0.15), strength=4.0)
    plasma = mat("euv_plasma", (0.70, 0.55, 1.0), emit=(0.62, 0.45, 1.0), strength=6.0)
    light = mat("euv_light", (0.55, 0.85, 1.0), emit=(0.45, 0.82, 1.0), strength=5.0)
    mirror_m = mat("euv_mirror", (0.78, 0.80, 0.84), metal=0.95, rough=0.12)
    stage = mat("euv_stage", (0.30, 0.31, 0.34), metal=0.5, rough=0.5)
    wafer_m = mat("euv_wafer", (0.55, 0.58, 0.64), metal=0.9, rough=0.22)
    resist = mat("euv_resist", (0.20, 0.18, 0.30), rough=0.6)
    reticle_m = mat("euv_reticle", (0.12, 0.13, 0.18), metal=0.4, rough=0.25)
    panel = mat("euv_panel", (0.72, 0.74, 0.76), metal=0.3, rough=0.45)
    glass = mat("euv_glass", (0.85, 0.90, 0.95), rough=0.05, alpha=0.25)

    # floor of the bay
    cut(box("euv_bay_floor", (-2300.0, -40.0, -700.0), (1900.0, 0.0, 700.0), floor, root))

    # ---- source: laser cabinet, vessel, nozzle, collector -------------------------------------
    cut(box("laser_cabinet", (LASER_X[0], 0.0, -260.0), (LASER_X[1], 700.0, 260.0), cab, root))
    cut(cylinder_wall_at("source_vessel", CX, VESSEL_R, 0.0, VESSEL_TOP, 45.0, steel, root))
    tube("tin_nozzle", (CX, NOZZLE_TOP, 0.0), (CX, VESSEL_TOP + 60.0, 0.0), 26.0, steel, root)
    cut(shell_sphere("collector", PLASMA, COLL_R, 22.0, mirror_m, root))

    # ---- scanner housing: five panels, front panel removed -------------------------------------
    x0, x1 = HOUSE_X
    for nm, lo, hi in (
        ("house_floor", (x0, 0.0, -HOUSE_Z), (x1, 30.0, HOUSE_Z)),
        ("house_roof", (x0, HOUSE_TOP - 30.0, -HOUSE_Z), (x1, HOUSE_TOP, HOUSE_Z)),
        ("house_back", (x0, 0.0, -HOUSE_Z), (x1, HOUSE_TOP, -HOUSE_Z + 30.0)),
        ("house_left", (x0, 0.0, -HOUSE_Z), (x0 + 30.0, HOUSE_TOP, HOUSE_Z)),
        ("house_right", (x1 - 30.0, 0.0, -HOUSE_Z), (x1, HOUSE_TOP, HOUSE_Z)),
    ):
        cut(box(nm, lo, hi, panel, root))
    # the intermediate focus aperture on the scanner's wall
    disc("intermediate_focus", IF, 60.0, 16.0, dark, root, verts=48)

    # ---- scanner: illuminator, reticle, projection mirrors, wafer stage and wafer -------------
    path = LIGHT
    mirror("illum_1", I1, path[0], path[2], 110.0, mirror_m, root)
    mirror("illum_2", I2, path[1], path[3], 110.0, mirror_m, root)
    box("reticle", (RET[0] - 90.0, RET[1], -90.0), (RET[0] + 90.0, RET[1] + 12.0, 90.0), reticle_m, root)
    for j, c in enumerate(PROJ):
        mirror(f"proj_{j + 1}", c, path[3 + j], path[5 + j], 95.0, mirror_m, root)
    box("wafer_stage", (1020.0, 100.0, -200.0), (1380.0, STAGE_Y, 200.0), stage, root)
    disc("wafer", (WAFER[0], 138.0, 0.0), 150.0, 14.0, wafer_m, root, verts=96)
    disc("resist", (WAFER[0], 147.5, 0.0), 150.0, 3.0, resist, root, verts=96)

    # ---- the light: plasma and beams -----------------------------------------------------------
    plasma_ball = ball("plasma", PLASMA, 70.0, plasma, root, 16)
    tubes = {
        "pre": tube("prepulse_beam", (LASER_X[1], 470.0, 0.0), (CX - 40.0, 470.0, 0.0), 8.0, co2, root),
        "main": tube("main_pulse_beam", (LASER_X[1], 470.0, 0.0), (CX - 40.0, 470.0, 0.0), 16.0, co2, root),
    }
    pancake = disc("pancake", PLASMA, 110.0, 12.0, tin, root, verts=48)
    droplet = ball("droplet", PLASMA, 26.0, tin, root, 12)

    # plasma glows in beats 0, 2 and 3; the pre-pulse, pancake and main pulse take their turns in beat 2
    show(plasma_ball, [beat(0)[0], (F(2, 0.6), F(4, 0.0))])
    show(tubes["pre"], [(F(2, 0.05), F(2, 0.30))])
    show(droplet, [(F(2, 0.0), F(2, 0.30))])
    show(pancake, [(F(2, 0.30), F(2, 0.45))])
    show(tubes["main"], [(F(2, 0.45), F(2, 0.70))])

    # tin drops fall from the nozzle: beat 1 (the whole stream) and beat 2 (a few more)
    run(root, "tin_a", [(CX, NOZZLE_TOP - 30.0, 0.0), (CX, PLASMA[1] + 40.0, 0.0)], 9, 14.0, tin, 1, 0.0, 0.75, 40)
    run(root, "tin_b", [(CX, NOZZLE_TOP - 30.0, 0.0), (CX, PLASMA[1] + 40.0, 0.0)], 4, 14.0, tin, 2, 0.0, 0.25, 40)

    # EUV beads: the collector's light into the intermediate focus, then the scanner's path to the wafer
    run(root, "euv_all", LIGHT, 10, 12.0, light, 0, 0.0, 0.8, 90)
    run(root, "euv_collect", COLLECT, 8, 12.0, light, 3, 0.05, 0.6, 60)
    run(root, "euv_scan", LIGHT, 10, 12.0, light, 4, 0.0, 0.6, 110)
    run(root, "euv_one", LIGHT, 6, 12.0, light, 5, 0.1, 0.7, 110)
    run(root, "euv_high", LIGHT, 8, 12.0, light, 6, 0.0, 0.7, 110)

    # ---- tags, one set per beat ---------------------------------------------------------------
    tags = {
        0: [("CO2 laser", (-1875.0, 740.0, 0.0)), ("13.5 nm light", (-700.0, 600.0, 0.0)), ("wafer", (1200.0, 220.0, 0.0))],
        1: [("tin drops, 50,000 a second", (CX + 40.0, 960.0, 0.0)), ("drop nozzle", (CX + 180.0, 880.0, 0.0))],
        2: [("pre-pulse: 30 to 100 um", (CX + 230.0, 600.0, 0.0)), ("CO2 main pulse", (-1600.0, 560.0, 0.0)),
            ("plasma: 13.5 nm light", (CX + 150.0, 420.0, 0.0))],
        3: [("collector mirror", (CX + 150.0, 770.0, 0.0)), ("intermediate focus", (-700.0, 560.0, 0.0))],
        4: [("illuminator mirrors", (-450.0, 600.0, 0.0)), ("reticle: the pattern", (40.0, 960.0, 0.0)),
            ("six projection mirrors", (760.0, 920.0, 0.0)), ("wafer", (1200.0, 220.0, 0.0))],
        5: [("ASML: the only maker", (-200.0, 1080.0, 0.0)), ("ZEISS: the mirrors", (600.0, 540.0, 0.0)),
            ("~100,000 parts", (CX, 1000.0, 0.0))],
        6: [("NA 0.33 to 0.55", (1100.0, 500.0, 0.0)), ("8 nm CD, was 13 nm", (1150.0, 640.0, 0.0)),
            ("anamorphic 4x / 8x", (400.0, 960.0, 0.0))],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))
    camera_path(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
