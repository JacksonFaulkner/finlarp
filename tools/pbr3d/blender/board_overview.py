"""The BOARD overview (PACKAGING tab), in the SAND template (docs/diagram-pages.md).

Run from the repo root (on the worker, or locally):

    blender -b --factory-startup --python tools/pbr3d/blender/board_overview.py

Writes blender/board_overview.blend and assets/board_overview.glb. One beat is 8 s.

Beats (match BOARD in diagrams_pkg_nodes.rs, B_B):
  0 the package on its board          the finished package solders to a green board
  1 BGA balls underneath              low view of the ball grid (1 mm pitch)
  2 power: hundreds of amps           regulators on the board; yellow power climbs through the
                                      see-through substrate and interposer into the die
  3 all of it becomes heat            the die glows; heat rises off the top
  4 lid and cold plate                a steel lid and a finned copper plate
  5 liquid cooling                    coolant runs through the plate's base (see-through)
  6 modules linked by NVLink          three modules, each on its own board, linked by NVLink
"""

import os
import sys

import bmesh
import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, beat, box, label, mat, show, tube  # noqa: E402
from sand_zooms import start, camera, finish, stream_of  # noqa: E402
from pbr_kit import empty  # noqa: E402
import pkg_kit as K  # noqa: E402

PAGE = "board"
NAME = "overview"
BEATS = 7

POSES = [
    ((0.0, -4.0, 0.0), 230.0, 0.50, 0.35),
    ((0.0, -9.0, 0.0), 80.0, 0.50, 0.10),
    ((0.0, -3.0, 0.0), 190.0, 0.50, 0.30),
    ((0.0, 4.0, 0.0), 80.0, 0.40, 0.35),
    ((0.0, 8.0, 0.0), 120.0, 0.50, 0.35),
    ((0.0, 9.0, 0.0), 120.0, 0.70, 0.16),
    ((0.0, 0.0, 0.0), 340.0, 0.50, 0.30),
]

BGA_HALF = 30.0  # the ball field covers the substrate
BGA_PITCH = 1.0  # mm, as the text says (~1 mm ball pitch)
BGA_R = 0.4
VRM_CORNERS = ((-48.0, -48.0), (48.0, -48.0), (-48.0, 48.0), (48.0, 48.0))
PWR_TARGETS = 10.0  # the power streams end under the die's corners, at the microbump level


def between(a, b):
    return [(F(a, 0), F(b, 0))]


def bga_fine(m, parent):
    """BGA balls at BGA_PITCH over the substrate's footprint, sitting between board and substrate.
    One bmesh object: a ball per operator call is far too slow at this count."""
    bm = bmesh.new()
    n = int(BGA_HALF // BGA_PITCH)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            c = P(BGA_PITCH * i, K.BOARD_TOP + 1.0, BGA_PITCH * j)
            bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=BGA_R, matrix=Matrix.Translation(c))
    me = bpy.data.meshes.new("bga_mesh")
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(m["solder"])
    o = bpy.data.objects.new("bga", me)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    return o


def build():
    _, root = start(NAME, beats=BEATS, page=PAGE)
    m = K.materials()
    # See-through versions of the layers, shown in beat 2 (power is seen climbing through them)
    # and the cold plate base, shown in beat 5 (coolant is seen running through it).
    ghost_sub = mat("board_ghost_substrate", (0.42, 0.27, 0.15), rough=0.8, alpha=0.22)
    ghost_ip = mat("board_ghost_silicon", (0.30, 0.36, 0.40), metal=0.4, rough=0.5, alpha=0.22)
    ghost_plate = mat("board_ghost_plate", (0.85, 0.55, 0.35), metal=0.9, rough=0.3, alpha=0.3)
    vrm_m = mat("board_vrm", (0.12, 0.12, 0.14), metal=0.3, rough=0.5)

    # One package on its board, beats 0-5 (the rack at beat 6 replaces it). Every group is a direct
    # child of the root with its own switch: nested animated parents render children at the wrong size.
    def in_beats(name, intervals):
        g = empty(name, root)
        show(g, intervals)
        return g

    package = [(F(0, 0), F(6, 0))]
    K.board(m, in_beats("board_grp", package))
    bga_fine(m, in_beats("bga_grp", package))
    K.substrate(m, in_beats("sub_grp", [(F(0, 0), F(2, 0)), (F(3, 0), F(6, 0))]), half=30.0)
    K.c4(m, in_beats("c4_grp", package), half=20.0)
    K.interposer(m, in_beats("ip_grp", [(F(0, 0), F(2, 0)), (F(3, 0), F(6, 0))]), half=26.0)
    gm = dict(m, substrate=ghost_sub, silicon=ghost_ip)
    ghost = in_beats("ghost_grp", beat(2))
    K.substrate(gm, ghost, half=30.0)
    K.interposer(gm, ghost, half=26.0, name="interposer_ghost")
    K.die(m, in_beats("die_grp", [(F(0, 0), F(3, 0)), (F(4, 0), F(6, 0))]))
    K.stacks(m, in_beats("stacks_grp", package), zs=(-9.0, 9.0))
    K.die(m, in_beats("die_hot_grp", [(F(3, 0), F(4, 0))]), mat_name="die_hot")
    K.lid(m, in_beats("lid_grp", between(4, 6)))

    # Cold plate: the fins are opaque; the base is solid in beat 4 and see-through in beat 5.
    plate_g = in_beats("plate_grp", between(4, 6))
    step = 48.0 / 11
    for k in range(11):
        x = -24.0 + step * (k + 0.5)
        box(f"fin_{k}", (x - 0.3, K.PLATE_TOP, -23.0), (x + 0.3, K.PLATE_TOP + 4.0, 23.0), m["plate"], plate_g)
    base_lo, base_hi = (-24.0, K.LID_TOP, -24.0), (24.0, K.PLATE_TOP, 24.0)
    box("plate_base", base_lo, base_hi, m["plate"], in_beats("plate_base_grp", [(F(4, 0), F(5, 0))]))
    box("plate_ghost", base_lo, base_hi, ghost_plate, in_beats("plate_ghost_grp", beat(5)))

    # Beat 2: regulators on the board; power streams from each one up through the layers to the die.
    vrm = empty("vrm_grp", root)
    show(vrm, beat(2))
    for k, (x, z) in enumerate(VRM_CORNERS):
        box(f"vrm_{k}", (x - 4.0, K.BOARD_TOP, z - 4.0), (x + 4.0, K.BOARD_TOP + 3.0, z + 4.0), vrm_m, vrm)
    for k, (x, z) in enumerate(VRM_CORNERS):
        tx = -PWR_TARGETS if x < 0 else PWR_TARGETS
        tz = -PWR_TARGETS if z < 0 else PWR_TARGETS
        stream_of(root, f"power_{k}", 8, (x, K.BOARD_TOP + 3.0, z), [(0, 0, 0), (tx - x, 2.2 - (K.BOARD_TOP + 3.0), tz - z)], 1.8, m["power"], 2, 0.05 + 0.03 * k, 0.75 + 0.03 * k, 70)

    # Beat 3: heat rising off the die's top.
    stream_of(root, "heat", 5, (0.0, K.DIE_TOP, 0.0), [(0, 0, 0), (0, 12, 0)], 1.4, m["heat"], 3, 0.1, 0.7, 40)

    # Beat 5: three coolant channels run through the plate's base, in at the left and out at the right.
    cool = empty("coolant_grp", root)
    show(cool, beat(5))
    y = (K.LID_TOP + K.PLATE_TOP) / 2
    for k, z in enumerate((-10.0, 0.0, 10.0)):
        tube(f"coolant_{k}", (-40.0, y, z), (40.0, y, z), 1.1, m["coolant"], cool, 16)

    # Beat 6: three modules, each on its own board, linked by NVLink (cyan) across the gaps.
    rack = empty("rack_grp", root)
    show(rack, between(6, 7))
    for k, x in enumerate((-70.0, 0.0, 70.0)):
        g = empty(f"module_{k}", rack)
        g.location = P(x, 0.0, 0.0)
        box(f"module_board_{k}", (-26.0, -14.0, -26.0), (26.0, -8.0, 26.0), m["board"], g)
        box(f"module_sub_{k}", (-16.0, -6.0, -16.0), (16.0, -2.0, 16.0), m["substrate"], g)
        box(f"module_ip_{k}", (-12.0, 0.0, -12.0), (12.0, 1.6, 12.0), m["silicon"], g)
        box(f"module_die_{k}", (-6.0, 1.6, -6.0), (6.0, 3.0, 6.0), m["die"], g)
        box(f"module_lid_{k}", (-10.0, 5.0, -10.0), (10.0, 6.0, 10.0), m["lid"], g)
    for k, (xa, xb) in enumerate(((-45.0, -25.0), (25.0, 45.0))):
        tube(f"nvlink_{k}", (xa, -6.5, 0.0), (xb, -6.5, 0.0), 1.6, m["bridge"], rack, 16)

    labels = {
        0: [("the package on its board", (40.0, -9.0, 40.0), root)],
        1: [("BGA balls underneath", (18.0, -7.0, 30.5), root)],
        2: [("power climbs from the board", (-22.0, -4.0, 22.0), root)],
        3: [("all of it becomes heat", (8.0, 10.0, 8.0), root)],
        4: [("lid and cold plate", (26.0, 14.0, 26.0), root)],
        5: [("liquid cooling", (-40.0, 13.0, 14.0), root)],
        6: [("three modules on boards", (0.0, 9.0, 40.0), root),
            ("NVLink between modules", (-35.0, -2.0, 16.0), root)],
    }
    for i, items in labels.items():
        for text, at, parent in items:
            label(text, at, parent, beat(i))

    camera(root, POSES)
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)
