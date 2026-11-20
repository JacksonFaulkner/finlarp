"""The Capex & fabs map: countries from GeoJSON, SK hynix sites pinned on it, one empty per site.

Used by mem_sk_hynix.py (tab `fabs`). Coordinates are poly points: x = lon * K, z = -lat * K, y up
(so north is -z, away from the default camera, and reads as "up the screen"). The GLB carries:

  site:<id>      an empty at each site; the TUI flies the camera to it
  countries      the land, one mesh per country, extruded LAND_H deep
  sea            a flat plate under everything

The TUI reads the site text and distances from tools/pbr3d/assets/mem/sk_hynix_fabs.sites.json,
which fab_sites_sidecar() writes next to the GLB. The overview camera is static (no keys).
"""

import json
import math
import os

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

from sand_overview import P, ball, disc, empty, mat, tube

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = os.path.join(HERE, "geo", "countries.geojson")
SITES = os.path.join(HERE, "geo", "sk_hynix_sites.json")

K = 40.0          # poly units per degree
LAND_H = 3.0      # land thickness
PIN_H = 16.0      # pin height above the land
OVERVIEW = {"target": (0.0, 0.0, 0.0), "dist": 15000.0, "yaw": 0.0, "pitch": 1.0}


LAND_TINTS = [(0.20, 0.24, 0.29), (0.23, 0.27, 0.32), (0.18, 0.22, 0.27), (0.25, 0.29, 0.35)]


def xz(lon, lat):
    return (lon * K, 0.0, -lat * K)


def load_sites():
    return json.load(open(SITES))["sites"]


def materials():
    return {
        # four near-identical greys, cycled by country, so neighbouring borders read
        "land": [mat(f"map_land_{i}", c, rough=0.8) for i, c in enumerate(LAND_TINTS)],
        "land_kr": mat("map_land_kr", (0.30, 0.36, 0.44), rough=0.7),
        "sea": mat("map_sea", (0.07, 0.10, 0.15), rough=0.95),
        "pin": mat("map_pin", (0.90, 0.22, 0.12), metal=0.2, rough=0.4),
        "pin_glow": mat("map_pin_glow", (1.0, 0.72, 0.25), emit=(1.0, 0.68, 0.2), strength=1.2, rough=0.4),
        "ring": mat("map_ring", (1.0, 0.85, 0.40), emit=(1.0, 0.82, 0.35), strength=0.5, rough=0.5),
    }


def _rings_2d(poly):
    """A polygon's rings as 2D vectors (x, -z) = (lon * K, lat * K), the closing repeat dropped.
    Not mirrored into z: tessellate_polygon drops half of some countries (the USA) when the
    winding is flipped, so the triangulation runs on the unmirrored plane and the verts take the
    z back in _extrude."""
    out = []
    for ring in poly:
        pts = [Vector((lon * K, lat * K)) for lon, lat in ring]
        if len(pts) > 1 and (pts[0] - pts[-1]).length < 1e-9:
            pts = pts[:-1]
        out.append(pts)
    return out


def _extrude(name, poly, m, parent):
    """One polygon (outer ring then holes) as a flat slab: triangulated top, straight walls."""
    rings = _rings_2d(poly)
    if not rings or len(rings[0]) < 3:
        return None
    flat = [p for ring in rings for p in ring]
    try:
        tris = tessellate_polygon(rings)
    except Exception as e:
        print("map: tessellate failed for", name, e)
        return None
    if not tris:
        print("map: no triangles for", name)
        return None
    bm = bmesh.new()
    top = [bm.verts.new(P(p.x, LAND_H, -p.y)) for p in flat]
    bot = [bm.verts.new(P(p.x, 0.0, -p.y)) for p in flat]
    tops = []
    for t in tris:
        try:
            tops.append(bm.faces.new((top[t[0]], top[t[1]], top[t[2]])))
        except ValueError:
            pass
    base = 0
    for ring in rings:
        n = len(ring)
        for i in range(n):
            a, b = base + i, base + (i + 1) % n
            try:
                bm.faces.new((top[a], top[b], bot[b], bot[a]))
            except ValueError:
                pass
        base += n
    # The slab is open underneath, so recalculating normals can point some tops down, and the
    # renderer culls those faces (holes in the land). Force every top up.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in tops:
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


def build_countries(root, m):
    d = json.load(open(COUNTRIES))
    g = empty("countries", root)
    n = 0
    for k, f in enumerate(d["features"]):
        iso = f["properties"].get("iso3") or "XXX"
        mm = m["land_kr"] if iso in ("KOR", "PRK") else m["land"][k % len(LAND_TINTS)]
        for j, poly in enumerate(f["geometry"]["coordinates"]):
            if _extrude(f"c_{iso}_{j}", poly, mm, g) is not None:
                n += 1
    print(f"map: {n} country slabs")
    return g


def build_sea(root, m):
    lo, hi = -180.0 * K, 180.0 * K
    zlo, zhi = -84.0 * K, 78.0 * K
    bm = bmesh.new()
    vs = [bm.verts.new(P(x, -2.0, z)) for x, z in ((lo, zlo), (hi, zlo), (hi, zhi), (lo, zhi))]
    bm.faces.new(vs)
    me = bpy.data.meshes.new("sea")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("sea", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m["sea"])
    o.parent = root
    return o


def build_sites(root, m, sites):
    for s in sites:
        x, _, z = xz(s["lon"], s["lat"])
        # the site empty sits on the land; its pin parts are built relative to it (children are
        # placed in the parent's frame, so absolute coordinates would be offset twice)
        g = empty(f"site:{s['id']}", root, P(x, LAND_H, z))
        tube(f"pin_{s['id']}", (0.0, 0.0, 0.0), (0.0, PIN_H - LAND_H, 0.0), 1.6, m["pin"], g)
        ball(f"glow_{s['id']}", (0.0, PIN_H - LAND_H + 2.5, 0.0), 2.8, m["pin_glow"], g, segs=16)
        disc(f"ring_{s['id']}", (0.0, 0.4, 0.0), 8.0, 0.8, m["ring"], g, verts=40)


def build_camera(root):
    o = OVERVIEW
    cp, sp = math.cos(o["pitch"]), math.sin(o["pitch"])
    t = o["target"]
    e = (t[0] + o["dist"] * cp * math.sin(o["yaw"]), t[1] + o["dist"] * sp, t[2] + o["dist"] * cp * math.cos(o["yaw"]))
    empty("CamTarget", root, P(*t))
    empty("CamEye", root, P(*e))


def build(root, m):
    """Adds the whole map under `root`; `m` gets the map's materials added to it."""
    mm = materials()
    m.update(mm)
    sites = load_sites()
    build_sea(root, mm)
    build_countries(root, mm)
    build_sites(root, mm, sites)
    build_camera(root)
    return sites


def sidecar(path):
    """The site text and flight distances the TUI reads, as JSON next to the GLB."""
    out = [
        {k: s[k] for k in ("id", "name", "text", "src", "url", "dist")}
        for s in load_sites()
    ]
    with open(path, "w") as fh:
        json.dump({"sites": out}, fh, indent=1, ensure_ascii=False)
    print("wrote", path, len(out), "sites")
