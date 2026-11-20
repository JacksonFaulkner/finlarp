"""Blender stills for the AI-universe heatmap tiles.

The heatmap's cursor can only land on a finite set of tiles. Those group tiles (primary, sub,
region, fund) get their own emblem, rendered here once. Every other tile (ticker, holding) shares
one plain plate. The return numbers and labels are never baked: the TUI draws them live beside
the picture.

    cd tools/pbr3d/blender && blender -b --factory-startup --python universe_tiles.py

Reads  universe_keys.json  (the group keys: primary/sub/region from ai_universe_category and
ai_taxonomy, fund tickers from ai_universe kind = etf; re-export when the taxonomy changes).
Writes one PNG per key plus plate.png into
tools/pbr3d/assets/universe/, and tui/src/screens/universe_art.rs, the include table the TUI
compiles in. Output is RGBA with a transparent background, square, UNIVERSE_TILE_PX per side.
"""

import json
import math
import os
import random
import re
import sys
import zlib

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "tools", "pbr3d", "assets", "universe")
RS = os.path.join(REPO, "tui", "src", "screens", "universe_art.rs")
SIZE = int(os.environ.get("UNIVERSE_TILE_PX", "256"))
KEYS = json.load(open(os.path.join(HERE, "universe_keys.json")))

# One accent per primary sector, in the taxonomy's own order (alphabetical here, stable).
FAMILY = [
    (1.00, 0.52, 0.18),  # orange
    (0.25, 0.68, 1.00),  # blue
    (0.46, 0.92, 0.42),  # green
    (0.90, 0.38, 0.92),  # magenta
    (1.00, 0.84, 0.30),  # gold
    (0.30, 0.94, 0.82),  # teal
]
NEUTRAL = (0.70, 0.74, 0.82)   # regions
FUND = (0.98, 0.90, 0.60)      # funds
PLATE_RIM = (0.55, 0.60, 0.68)
BASE = (0.10, 0.11, 0.14)      # the dark plinth every tile stands on

PRIMARY_INDEX = {
    k["name"]: i for i, k in enumerate(sorted((k for k in KEYS if k["level"] == "primary"), key=lambda k: k["name"]))
}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def file_of(level, name):
    return f"{level}_{slug(name)}.png"


def accent_of(key):
    if key["level"] == "primary":
        return FAMILY[PRIMARY_INDEX[key["name"]]]
    if key["level"] == "sub":
        return FAMILY[PRIMARY_INDEX.get(key["parent"], 0)]
    if key["level"] == "fund":
        return FUND
    return NEUTRAL


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.film_transparent = True
    s.render.resolution_x = SIZE
    s.render.resolution_y = SIZE
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGBA"
    s.eevee.taa_render_samples = 24
    world = bpy.data.worlds.new("universe")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.58, 0.66, 1.0)
    bg.inputs["Strength"].default_value = 0.35
    s.world = world
    return s


def material(name, rgb, metal=0.0, rough=0.35, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1.0)
        b.inputs["Emission Strength"].default_value = emit
    return m


def put(obj, mat, loc, scale=(1, 1, 1), rot=(0, 0, 0)):
    obj.data.materials.append(mat)
    obj.location = loc
    obj.scale = scale
    obj.rotation_euler = rot
    return obj


def plinth(base_mat, rim_mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.70, depth=0.10)
    put(bpy.context.object, base_mat, (0, 0, -0.05))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.70, minor_radius=0.025)
    put(bpy.context.object, rim_mat, (0, 0, 0.0))


def emblem(rng, accent):
    """A cluster of 3 to 5 lit objects on the plinth. The shapes and heights come from the key's
    seed, so each identity keeps its own look from run to run."""
    metal = material("metal", (0.55, 0.58, 0.64), metal=1.0, rough=0.25)
    glow = material("glow", accent, rough=0.3, emit=1.2)
    solid = material("solid", accent, rough=0.4)
    plinth(material("base", BASE, rough=0.6), metal)
    n = 3 + rng.randrange(3)
    kinds = ["bar", "orb", "cone", "ring"]
    for i in range(n):
        ang = 2 * math.pi * i / n + rng.uniform(-0.35, 0.35)
        r = 0.22 + rng.uniform(0.0, 0.2)
        x, y = r * math.cos(ang), r * math.sin(ang)
        kind = kinds[rng.randrange(len(kinds))]
        h = 0.35 + rng.uniform(0.0, 0.75)
        mat_ = glow if i % 2 == 0 else solid
        if kind == "bar":
            bpy.ops.mesh.primitive_cube_add(size=1)
            put(bpy.context.object, mat_, (x, y, h / 2), (0.16, 0.16, h))
        elif kind == "orb":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, segments=32, ring_count=16)
            put(bpy.context.object, mat_, (x, y, 0.15 + h * 0.4))
        elif kind == "cone":
            bpy.ops.mesh.primitive_cone_add(radius1=0.18, radius2=0.0, depth=h, vertices=32)
            put(bpy.context.object, mat_, (x, y, h / 2))
        else:
            bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.045)
            put(bpy.context.object, mat_, (x, y, 0.25 + h * 0.5), rot=(rng.uniform(0, 1.2), 0, rng.uniform(0, 3)))


def plate_only():
    plinth(material("base", BASE, rough=0.6), material("rim", PLATE_RIM, metal=1.0, rough=0.25))


def camera(s):
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 46
    cam = bpy.data.objects.new("cam", cam_data)
    s.collection.objects.link(cam)
    cam.location = (1.95, -2.1, 1.85)
    target = (0.0, 0.0, 0.4)
    direction = [t - c for t, c in zip(target, cam.location)]
    cam.rotation_euler = direction_to_euler(direction)
    s.camera = cam
    light(s, "sun", "SUN", (0, 0, 0), (math.radians(50), 0, math.radians(35)), 2.5)
    light(s, "fill", "AREA", (2.5, -2.0, 3.5), (math.radians(55), 0, math.radians(40)), 180.0)


def direction_to_euler(d):
    from mathutils import Vector

    return Vector(d).to_track_quat("-Z", "Y").to_euler()


def light(s, name, kind, loc, rot, energy):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    obj = bpy.data.objects.new(name, data)
    s.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot


def clear(s):
    """Drops last tile's meshes; the camera and lights stay."""
    for o in list(s.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    s = reset()
    camera(s)
    rendered = []
    for key in KEYS:
        clear(s)
        seed = zlib.crc32(f"{key['level']}:{key['name']}".encode())
        rng = random.Random(seed)
        emblem(rng, accent_of(key))
        name = file_of(key["level"], key["name"])
        s.render.filepath = os.path.join(OUT, name)
        bpy.ops.render.render(write_still=True)
        rendered.append((key["level"], key["name"], name))
        print(f"rendered {name}", file=sys.stderr)
    clear(s)
    plate_only()
    s.render.filepath = os.path.join(OUT, "plate.png")
    bpy.ops.render.render(write_still=True)

    lines = [
        "// Generated by tools/pbr3d/blender/universe_tiles.py. Do not edit by hand.",
        "// Cursor-reachable group tiles get an emblem; every other tile shares PLATE.",
        "",
        "/// Emblem per group tile, keyed `level:name` (the heatmap's own group keys).",
        "pub const ART: &[(&str, &[u8])] = &[",
    ]
    for level, name, fname in rendered:
        rel = f"../../../tools/pbr3d/assets/universe/{fname}"
        lines.append(f'    ("{level}:{name}", include_bytes!("{rel}")),')
    lines += [
        "];",
        "",
        "/// The shared plate every non-group tile is drawn on.",
        'pub const PLATE: &[u8] = include_bytes!("../../../tools/pbr3d/assets/universe/plate.png");',
        "",
    ]
    open(RS, "w").write("\n".join(lines))
    print(f"{len(rendered)} emblems + plate -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
