"""Slim the Natural Earth countries file into tools/pbr3d/blender/geo/countries.geojson.

    python3 make_countries.py <ne_50m_admin_0_countries.geojson>

Natural Earth (public domain, naturalearthdata.com) 50m admin-0 countries, as published at
github.com/nvkelso/natural-earth-vector. This keeps only what the map scene needs: ISO-A3 code,
name, and polygon rings simplified with Ramer-Douglas-Peucker (0.05 degrees), with each ring
unwrapped across the antimeridian (Russia's Chukotka) so no ring spans the whole map. Antarctica
is dropped. Output is plain GeoJSON, lon/lat, WGS84.
"""

import json
import os
import sys

TOL = 0.05
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "countries.geojson")


def rdp(pts, tol):
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = (dx * dx + dy * dy) ** 0.5 or 1e-12
    best, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * (x - x0) - dx * (y - y0)) / norm
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [pts[0], pts[-1]]
    left = rdp(pts[: idx + 1], tol)
    return left[:-1] + rdp(pts[idx:], tol)


def unwrap(ring):
    out, shift, prev = [], 0.0, None
    for lon, lat in ring:
        if prev is not None:
            if lon + shift - prev > 180:
                shift -= 360
            elif lon + shift - prev < -180:
                shift += 360
        p = lon + shift
        out.append([p, lat])
        prev = p
    return out


def slim_ring(ring):
    pts = [tuple(p) for p in unwrap(ring)]
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        return None
    # A closed ring has no chord to simplify against, so split it at the point farthest from the
    # first vertex and simplify the two open halves.
    x0, y0 = pts[0]
    k = max(range(1, len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    a = rdp(pts[: k + 1], TOL)
    b = rdp(pts[k:] + [pts[0]], TOL)
    s = a[:-1] + b[:-1]
    if len(s) < 3:
        return None
    return [list(p) for p in s] + [list(s[0])]


def main(src):
    d = json.load(open(src))
    feats = []
    for f in d["features"]:
        p = f["properties"]
        if p.get("NAME") == "Antarctica":
            continue
        g = f["geometry"]
        if g["type"] == "Polygon":
            polys = [g["coordinates"]]
        elif g["type"] == "MultiPolygon":
            polys = g["coordinates"]
        else:
            continue
        out = []
        for poly in polys:
            rings = [slim_ring(r) for r in poly]
            if rings[0] is None:
                continue
            rings = [r for r in rings if r is not None]
            out.append(rings)
        if not out:
            continue
        geom = {"type": "MultiPolygon", "coordinates": out}
        feats.append({
            "type": "Feature",
            "properties": {"iso3": p.get("ADM0_A3") or p.get("ISO_A3"), "name": p.get("NAME")},
            "geometry": geom,
        })
    with open(OUT, "w") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh, separators=(",", ":"))
    n = sum(len(r) for f in feats for poly in f["geometry"]["coordinates"] for r in poly)
    print(f"wrote {OUT}: {len(feats)} countries, {n} rings, {os.path.getsize(OUT)} bytes")


if __name__ == "__main__":
    main(sys.argv[1])
