"""Zoom-ins (a-e) for the PACKAGING overviews, generated from each overview's own scene.

A zoom is the overview's geometry and timeline with the camera held on one subject for the whole
run, and a single tag: the zoom's caption from diagrams_pkg_nodes.rs (LOGIC `L_Z`, MICROBUMP `U_Z`,
INTERPOSER `I_Z`, SUBSTRATE `S_Z`, ASSEMBLY `A_Z`, BOARD `B_Z`).

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/pkg_zooms.py -- logic_die a

Writes assets/<page>_zoom_<letter>.glb (for example assets/logic_die_zoom_a.glb).
The nine numbered sections map onto these zooms: see SECTION_MAP and sections.json.
"""

import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from bpy_extras import anim_utils  # noqa: E402
from sand_overview import BEAT_FRAMES, F, box, disc, label, tube  # noqa: E402
from sand_zooms import camera as zoom_camera, finish  # noqa: E402
from pbr_kit import empty  # noqa: E402

# node -> (overview module, page name); the page name matches the overview's PAGE.
NODES = {
    "logic_die": "logic_die_overview",
    "microbump": "microbump_overview",
    "interposer": "interposer_overview",
    "substrate": "substrate_overview",
    "assembly": "assembly_overview",
    "board": "board_overview",
}

# Overview beat whose state each zoom freezes (the subject is on screen then). A zoom is one
# picture: the frozen state is shown for the zoom's three caption beats.
FREEZE_BEAT = {
    # A list holds one overview state per zoom beat (the state at mid-beat); an int holds one state
    # for all three beats.
    "logic_die": {"a": [1, 1, 4], "b": [2, 4, 2], "c": 4, "d": [3, 4, 5], "e": [5, 6, 6]},
    "microbump": {"a": [1, 2, 6], "b": [2, 0, 5], "c": [0, 0, 6], "d": [0, 0, 5], "e": 4},
    "interposer": {"a": [3, 3, 4], "b": 1, "c": 5, "d": [2, 2, 3], "e": 6},
    "substrate": {"a": 2, "b": [1, 2, 3], "c": [3, 5, 5], "d": [2, 6, 2], "e": 4},
    "assembly": {"a": 2, "b": 4, "c": 2, "d": 6, "e": 5},
    "board": {"a": 1, "b": 2, "c": 5, "d": 6, "e": 5},
}
ZOOM_BEATS = 3  # the zoom's caption beats (diagrams_pkg_nodes.rs: LA_B..LE_B have three each)

# letter -> (target, distance, yaw, pitch, tag text, tag position); mm, Y up, in each overview's scene.
ZOOMS = {
    "logic_die": {
        "a": ((0.0, 0.6, 0.0), 85.0, 0.50, 0.40, "the reticle limit", (13.3, 1.5, 0.0)),
        "b": ((0.0, 1.2, 0.0), 80.0, 0.40, 0.35, "yield and known-good dies", (5.0, 1.3, 6.0)),
        "c": ((0.0, 0.8, 0.0), 80.0, 0.60, 0.55, "chiplets and the die-to-die link", (0.0, 0.6, 0.0)),
        "d": ((0.0, 2.0, 0.0), 110.0, 0.60, 0.30, "HBM shoreline", (18.5, 6.0, 9.0)),
        "e": ((0.0, 3.0, 0.0), 80.0, 0.50, 0.60, "power and heat", (4.0, 12.0, 4.0)),
    },
    "microbump": {
        "a": ((0.0, 1.5, 0.0), 62.0, 0.60, 0.25, "C4, microbump, hybrid bond", (0.0, 2.2, 0.0)),
        "b": ((0.0, 2.6, 0.0), 62.0, 0.40, 0.12, "making a joint", (4.0, 2.2, 4.0)),
        "c": ((0.0, 2.4, 0.0), 62.0, 0.70, 0.30, "pitch and the solder wall", (-5.6, 2.2, -5.6)),
        "d": ((0.0, 2.5, 0.0), 62.0, 0.90, 0.30, "underfill shares the stress", (-7.6, 2.2, 0.0)),
        "e": ((0.0, 1.5, 0.0), 62.0, 0.50, 0.15, "current through the bumps", (5.6, 2.2, 5.6)),
    },
    "interposer": {
        "a": ((0.0, 0.8, 0.0), 110.0, 0.60, 0.35, "CoWoS-S and -L", (-20.0, 1.8, -20.0)),
        "b": ((-12.0, 2.0, 0.0), 70.0, 0.0, 0.75, "a signal from HBM to GPU", (-13.6, 2.3, 9.0)),
        "c": ((0.0, 0.0, 0.0), 170.0, 0.60, 0.30, "growing past the reticle", (40.0, 1.8, 40.0)),
        "d": ((0.0, 1.0, 0.0), 80.0, 1.45, 0.20, "TSVs and power", (0.0, 0.8, 0.0)),
        "e": ((-105.0, -2.0, 0.0), 240.0, 0.45, 0.45, "interposers per wafer", (-80.0, -2.0, 30.0)),
    },
    "substrate": {
        "a": ((0.0, -4.0, 0.0), 58.0, 0.30, 0.10, "building the layers", (8.0, -1.0, 0.1)),
        "b": ((0.0, -3.0, 0.0), 100.0, 0.50, 0.10, "fan-out: C4 to BGA", (21.0, -7.0, 35.0)),
        "c": ((0.0, -2.0, 0.0), 130.0, 0.60, 0.30, "warpage", (30.0, -2.0, 30.0)),
        "d": ((0.0, -3.0, 0.0), 110.0, 0.50, 0.30, "ABF film and substrate makers", (-24.0, -2.0, -24.0)),
        "e": ((30.0, -4.5, 0.0), 70.0, 0.40, 0.12, "power fans in", (30.0, -3.0, 0.1)),
    },
    "assembly": {
        "a": ((0.0, 0.0, 0.0), 280.0, 0.50, 0.50, "chip on the wafer", (6.0, 4.2, -6.0)),
        "b": ((0.0, -2.0, 0.0), 100.0, 0.60, 0.25, "on substrate", (28.0, -2.0, 22.0)),
        "c": ((0.0, 4.0, 0.0), 90.0, 0.50, 0.35, "yield stackup", (10.0, 8.0, 10.0)),
        "d": ((0.0, 0.0, 0.0), 320.0, 0.30, 0.30, "capacity", (0.0, -2.0, 14.0)),
        "e": ((0.0, 5.0, 0.0), 110.0, 0.60, 0.30, "the lid goes on", (24.0, 9.0, 12.0)),
    },
    "board": {
        "a": ((0.0, -9.0, 0.0), 80.0, 0.50, 0.10, "BGA to the board", (18.0, -7.0, 30.5)),
        "b": ((0.0, -3.0, 0.0), 190.0, 0.50, 0.30, "power climbs the levels", (-22.0, -4.0, 22.0)),
        "c": ((0.0, 10.0, 0.0), 150.0, 0.60, 0.30, "cooling: cold plate and liquid", (-30.0, 13.0, 12.0)),
        "d": ((0.0, 1.0, 0.0), 330.0, 0.50, 0.30, "modules and NVLink", (0.0, 9.0, 40.0)),
        "e": ((0.0, 4.0, 0.0), 210.0, 0.50, 0.25, "size and cooling", (26.0, 14.0, 26.0)),
    },
}

# Which zoom each numbered section shows, from the SECTION tables in diagrams_pkg_nodes.rs
# (the section entries reuse the zoom beat tables, LA/LB/... = zoom a/b/...).
SECTION_MAP = {}


def _drop(obj):
    """Delete an overview object with its children: the zoom builds its own picture of that part."""
    for c in list(obj.children_recursive):
        bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(obj, do_unlink=True)


def _interposer_d(mod, root):
    """Cut open: the silicon slab has a slot along the TSV row, so the copper columns show and the
    power climbs through them (the overview's power stream runs up x = 0, z = 0)."""
    m = mod.K.materials()
    for name in ("si_small_plate", "si_glass_plate"):
        if name in bpy.data.objects:
            _drop(bpy.data.objects[name])
    g = empty("tsv_cut", root)
    box("si_front", (-26.0, 0.0, 4.0), (26.0, 1.6, 26.0), m["silicon"], g)
    box("si_back", (-26.0, 0.0, -26.0), (26.0, 1.6, -4.0), m["silicon"], g)
    for x in range(-15, 16, 3):
        tube(f"tsv_{x}", (float(x), 0.0, 0.0), (float(x), 1.6, 0.0), 0.6, m["copper"], g)


def _interposer_e(mod, root):
    """A wafer of interposer squares beside the package on its board: interposers are cut from it."""
    m = mod.K.materials()
    g = empty("wafer", root)
    cx = -105.0
    disc("wafer", (cx, -3.0, 0.0), 62.0, 1.0, m["lid"], g)
    for i in range(-2, 3):
        for j in range(-2, 3):
            x, z = cx + 22.0 * i, 22.0 * j
            if (x - cx) ** 2 + z**2 <= 50.0**2:
                box(f"ip_{i}_{j}", (x - 10.5, -2.5, z - 10.5), (x + 10.5, -2.0, z + 10.5), m["silicon"], g)


MB_HALF = 12.0  # microbump zooms: the slabs under the die are cut down to this half-width
MB_BALL_K = 0.6  # ...and the solder balls kept are drawn at 60% so they match the smaller package


def _microbump_small(mod, root):
    """Microbump close-ups: shrink the interposer, substrate and board slabs (26-40 mm half-width)
    to MB_HALF and drop the balls beyond it, so the camera can come close to the die and its bumps
    without the slabs' near corners crossing the renderer's 40 mm near plane (a clipped slab
    showed as a grey wall in front of the subject)."""
    for name, half in (("interposer", 26.0), ("substrate", 30.0), ("board", 40.0)):
        f = MB_HALF / half
        for n in (name, f"{name}_glass"):
            o = bpy.data.objects.get(n)
            if o is not None:
                o.scale = (o.scale[0] * f, o.scale[1] * f, o.scale[2])
    for o in list(bpy.data.objects):
        if o.name.startswith(("c4_", "bga_")) and o.type == "MESH":
            x, _, z = o.matrix_world.translation
            if max(abs(x), abs(z)) > MB_HALF - 1.0:
                bpy.data.objects.remove(o, do_unlink=True)
            else:
                o.scale = (MB_BALL_K, MB_BALL_K, MB_BALL_K)


# Per-zoom geometry the overview does not draw: hook(mod, root) runs after the overview is built.
EXTRA = {
    ("interposer", "d"): _interposer_d,
    ("interposer", "e"): _interposer_e,
    **{("microbump", k): _microbump_small for k in "abcde"},
}


def hold(states):
    """Zoom beat k shows the overview's state at `states[k]` (sampled mid-beat), switched at each
    zoom beat boundary. Every animated channel is held constant, so the camera and the tag hold
    with the rest: one picture per caption beat, of the subject that caption names."""
    frames = [k * BEAT_FRAMES for k in range(len(states))]
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in list(cb.fcurves):
            values = [fc.evaluate(F(b, 0.5)) for b in states]
            while len(fc.keyframe_points):
                fc.keyframe_points.remove(fc.keyframe_points[0], fast=True)
            for f, value in zip(frames, values):
                kp = fc.keyframe_points.insert(f, value)
                kp.interpolation = "CONSTANT"
            fc.update()
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = BEAT_FRAMES * len(states)
    bpy.context.scene.frame_set(0)


def run(node, letter):
    if node not in NODES:
        raise SystemExit(f"unknown node {node}; one of {sorted(NODES)}")
    target, dist, yaw, pitch, text, at = ZOOMS[node][letter]
    mod = importlib.import_module(NODES[node])
    base = mod.PAGE
    mod.NAME = f"zoom_{letter}"
    # The overview's tags are replaced by this zoom's one tag, and its camera by a fixed pose.
    mod.label = lambda *a, **k: None
    mod.camera = lambda root, poses: zoom_camera(root, [(target, dist, yaw, pitch)] * mod.BEATS)
    root = mod.build()
    if (node, letter) in EXTRA:
        EXTRA[(node, letter)](mod, root)
    label(text, at, root, [(F(0, 0), F(mod.BEATS, 0))])
    states = FREEZE_BEAT[node][letter]
    hold(states if isinstance(states, list) else [states] * ZOOM_BEATS)
    finish(mod.NAME, page=base)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 2:
        raise SystemExit("usage: blender -b --python pkg_zooms.py -- <node> <letter>")
    run(argv[0], argv[1])
