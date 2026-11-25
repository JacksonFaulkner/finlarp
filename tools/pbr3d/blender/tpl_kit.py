"""Diagram templates for ticker dossiers: reusable panels, chained into one 3-beat scene.

A company page like SK hynix (mem_sk_hynix.py) is hand-built, one scene per tab. That does not
scale to every ticker, so this kit turns a *spec* (plain JSON, built from the cached dossier by
py/derive/dossier_diagrams.py) into a GLB with no per-ticker Blender code:

    {"name": "MRVL_financials",
     "beats": [{"panel": "bars",  "title": "Quarterly revenue", "unit": "$M",
                "points": [["Q3'25", 1516.1], ...]},
               {"panel": "bars",  "title": "Operating margin", "unit": "%", "points": [...]},
               {"panel": "donut", "title": "Product / service", "unit": "$M",
                "items": [["Data Center", 6100.3], ...]}]}

Each beat is one panel; panel i shows during beat i only (all are built at the origin), and a
spec with fewer than 3 beats holds the last panel. Every value drawn comes from the spec, and every
spec value comes from a sourced dossier block (no source, no value), so the dossier's source bar
stays the citation for the picture.

Panels (PANELS below; add one = write build_<panel>(g, m, beat, spec) and register it):

    bars    one bar per point; negatives hang below the floor in red, the latest bar is gold.
            Tags: title, first, latest with change vs first, and the peak or trough.
    donut   a ring of sectors in item order (largest first), drawn in turn. Tags: title and the
            top three items with their share.
    towers  one stacked bar per point of several series (e.g. a segment mix over years).

Run (repo root): blender -b --factory-startup --python tools/pbr3d/blender/tpl_run.py -- SPEC.json...
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import OFF, F, P, _constant_until, box, empty, key, label, mat, pivot, rel, show  # noqa: E402
from sand_zooms import camera, start  # noqa: E402

BEATS = 3  # a spec with fewer beats holds its last panel to fill 3
MAX_BEATS = 6  # the TUI loops a scene over its own length (memory_scene::glb_loop_secs)
END = F(BEATS, 0)
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets", "tpl"))

# A panel fills a PW x PH box (scene mm) centred on its own x; panels sit DX apart.
PW, PH, DX = 3000.0, 1100.0, 5200.0
# The camera on a panel: (distance, yaw, pitch). A 3:1 slot shows ~1.4x the distance across.
CAM = (2850.0, 0.10, 0.10)

# Series palette for donut sectors and stacked parts, in order.
PALETTE = [
    ("p0", (0.25, 0.55, 0.95)),
    ("p1", (0.30, 0.78, 0.45)),
    ("p2", (1.00, 0.66, 0.15)),
    ("p3", (0.62, 0.42, 0.92)),
    ("p4", (0.20, 0.72, 0.78)),
    ("p5", (0.92, 0.38, 0.55)),
    ("p6", (0.55, 0.55, 0.60)),
    ("p7", (0.86, 0.84, 0.36)),
    ("p8", (0.96, 0.52, 0.36)),
    ("p9", (0.40, 0.60, 0.30)),
]


def mats():
    m = {
        "bar": mat("tpl_bar", (0.25, 0.55, 0.95), metal=0.2, rough=0.4),
        "bar_dim": mat("tpl_bar_dim", (0.30, 0.38, 0.52), metal=0.2, rough=0.6),
        "neg": mat("tpl_neg", (0.95, 0.18, 0.15), emit=(0.95, 0.15, 0.10), strength=0.5, rough=0.5),
        "last": mat("tpl_last", (1.0, 0.68, 0.12), emit=(1.0, 0.62, 0.10), strength=0.45, metal=0.3, rough=0.35),
        "floor": mat("tpl_floor", (0.13, 0.14, 0.17), rough=0.9),
        "line": mat("tpl_line", (1.0, 0.85, 0.40), emit=(1.0, 0.82, 0.35), strength=0.9),
        "ring_bg": mat("tpl_ring_bg", (0.22, 0.24, 0.30), rough=0.8),
    }
    for name, rgb in PALETTE:
        m[name] = mat(f"tpl_{name}", rgb, metal=0.2, rough=0.45)
    return m


# ---- number formatting ----------------------------------------------------------------------


def fmt(v, unit):
    """A value in the dossier's unit as a short tag: $M -> $1.52B / $820M, % -> 12.9%."""
    if unit == "%":
        return f"{v:.1f}%"
    if unit.endswith("M"):  # millions of a currency: "$M", "NT$M", "EUR M", plain "M"
        cur = unit[:-1].strip()
        cur = cur if not cur or cur.endswith("$") else cur + " "
        a = abs(v)
        s = "-" if v < 0 else ""
        if a >= 1e6:
            return f"{s}{cur}{a / 1e6:.2f}T"
        if a >= 1e3:
            return f"{s}{cur}{a / 1e3:.2f}B"
        if a >= 10:
            return f"{s}{cur}{a:,.0f}M"
        if a >= 1:
            return f"{s}{cur}{a:.1f}M"
        return f"{s}{cur}{a * 1e3:,.0f}K"
    return f"{v:,.2f}{(' ' + unit) if unit else ''}"


def change(a, b, unit):
    """b vs a: percentage points for a % series, else % change (None when a is ~0 or signs flip)."""
    if unit == "%":
        return f"{b - a:+.1f} pts"
    if a > 0 and b > 0:
        return f"{(b / a - 1) * 100:+.0f}%"
    return None


# ---- primitives -------------------------------------------------------------------------------


def beat_iv(i, u0=0.0, u1=1.0):
    return [(F(i, u0), F(i, u1) if u1 < 1.0 else F(i + 1, 0))]


def grow(obj, f0, f1):
    """Hidden until f0, then grows in height (poly y = 3rd scale slot) to full by f1."""
    f0 = max(1, f0)
    key(obj, 0, "scale", (OFF, OFF, OFF))
    key(obj, f0, "scale", (1.0, 1.0, OFF))
    key(obj, f1, "scale", (1.0, 1.0, 1.0))
    _constant_until(obj, f0)


def bar(name, parent, x, w, y1, m, d=None):
    """A bar from the floor (y=0) to y1 (may be negative), in a pivot at its base."""
    d = d or w
    at = (x, 0.0, 0.0)
    pv = pivot(name, at, parent)
    lo, hi = (0.0, y1) if y1 >= 0 else (y1, 0.0)
    box(f"{name}_m", rel(at, (x - w / 2, lo, -d)), rel(at, (x + w / 2, hi, 0.0)), m, pv)
    return pv


def stacked(name, parent, x, w, parts, d=None):
    """A bar of stacked segments [(height, mat), ...] in one pivot at its base."""
    at = (x, 0.0, 0.0)
    pv = pivot(name, at, parent)
    y, d = 0.0, d or w
    for i, (h, m) in enumerate(parts):
        if h > 0:
            box(f"{name}_s{i}", rel(at, (x - w / 2, y, -d)), rel(at, (x + w / 2, y + h - 4, 0.0)), m, pv)
            y += h
    return pv


def floor(g, m, y=0.0):
    box("floor", (-PW / 2 - 250, y - 30, -700.0), (PW / 2 + 250, y - 10, 250.0), m["floor"], g)


def wedge(name, c, r0, r1, depth, a0, a1, m, parent, segs=8):
    """A ring sector facing the camera (+z): radii r0..r1, angles a0..a1 clockwise from 12."""
    bm = bmesh.new()
    ring = []
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs
        sx, sy = math.sin(a), math.cos(a)
        layer = []
        for r in (r0, r1):
            for z in (0.0, -depth):
                layer.append(bm.verts.new(P(c[0] + r * sx, c[1] + r * sy, c[2] + z)))
        ring.append(layer)
    for i in range(segs):
        a, b = ring[i], ring[i + 1]
        bm.faces.new((a[0], b[0], b[2], a[2]))
        bm.faces.new((a[1], a[3], b[3], b[1]))
        bm.faces.new((a[2], b[2], b[3], a[3]))
        bm.faces.new((a[0], a[1], b[1], b[0]))
    s, e = ring[0], ring[-1]
    bm.faces.new((s[0], s[2], s[3], s[1]))
    bm.faces.new((e[0], e[1], e[3], e[2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = parent
    return o


# ---- panels -----------------------------------------------------------------------------------
# build_<panel>(g, m, b, spec) draws in panel-local coords (centre x=0, floor y=0) inside group g,
# animates during beat b, and returns the camera target (x, y, z) in panel-local coords.


def build_bars(g, m, b, spec):
    pts = [(str(x), float(y)) for x, y in spec["points"]]
    unit = spec.get("unit", "")
    n = len(pts)
    ys = [y for _, y in pts]
    hi, lo = max(0.0, max(ys)), min(0.0, min(ys))
    S = PH / max(hi - lo, 1e-9)
    base = -lo * S  # lift the floor so the deepest negative bar still sits above y=0 of the frame
    step = PW / max(n, 1)
    w = min(step * 0.7, 420.0)
    floor(g, m, base)
    x0 = -PW / 2 + step / 2
    X = lambda i: x0 + step * i  # noqa: E731
    lift = empty("lift", g, P(0, base, 0))
    for i, (_, y) in enumerate(pts):
        mk = "neg" if y < 0 else ("last" if i == n - 1 else ("bar" if i % 2 == 0 else "bar_dim"))
        pv = bar(f"b{i}", lift, X(i), w, y * S, m[mk], d=min(w, 200.0))
        u0 = 0.04 + 0.5 * i / max(n, 1)
        grow(pv, F(b, u0), F(b, u0 + 0.12))
    top = lambda i: (X(i), base + max(ys[i], 0.0) * S + 12, 0.0)  # noqa: E731
    bot = lambda i: (X(i), base + min(ys[i], 0.0) * S - 40, 0.0)  # noqa: E731
    at = lambda i: top(i) if ys[i] >= 0 else bot(i)  # noqa: E731
    label(f"{spec['title']} ({unit})" if unit else spec["title"], (-PW / 2 + 200, PH + 120, 0.0), g, beat_iv(b, 0.02))
    for tg in spec.get("tags", []):
        label(tg["text"], at(tg["i"] % n), g, beat_iv(b, tg.get("u", 0.6)))
    if not spec.get("auto_tags", True):
        return (0.0, PH * 0.56, 0.0)
    first, last = 0, n - 1
    label(f"{pts[first][0]} {fmt(ys[first], unit)}", at(first), g, beat_iv(b, 0.2))
    ch = change(ys[first], ys[last], unit) if n > 1 else None
    label(f"{pts[last][0]} {fmt(ys[last], unit)}" + (f" ({ch})" if ch else ""), at(last), g, beat_iv(b, 0.65))
    # the most extreme bar other than the ends: the peak if the series ends below it, else the trough
    mid = list(range(1, n - 1))
    if mid:
        pk = max(mid, key=lambda i: ys[i])
        tr = min(mid, key=lambda i: ys[i])
        pick = pk if ys[pk] > ys[last] else (tr if ys[tr] < min(ys[first], ys[last]) else None)
        if pick is not None:
            word = ("peak " if pick == pk else "low ") if ys[pick] >= 0 else ""  # no "peak" on a loss
            label(f"{word}{pts[pick][0]} {fmt(ys[pick], unit)}", at(pick), g, beat_iv(b, 0.45))
    return (0.0, PH * 0.56, 0.0)


def build_donut(g, m, b, spec):
    items = sorted(((str(k), float(v)) for k, v in spec["items"] if v > 0), key=lambda kv: -kv[1])
    unit = spec.get("unit", "")
    total = sum(v for _, v in items) or 1.0
    # fold the tail into "Other" so a sector is never a sliver
    if len(items) > len(PALETTE):
        keep = items[: len(PALETTE) - 1]
        items = keep + [("Other", total - sum(v for _, v in keep))]
    c, r0, r1, depth = (0.0, PH * 0.5, 0.0), PH * 0.30, PH * 0.52, 90.0
    wedge("bg", c, r0 - 6, r1 + 6, depth * 0.5, 0.0, 2 * math.pi - 1e-3, m["ring_bg"], g, segs=64)
    a = 0.0
    tags = []
    for i, (name, v) in enumerate(items):
        span = 2 * math.pi * v / total
        e = empty(f"s{i}", g)
        wedge(f"s{i}_m", (c[0], c[1], c[2] + 10), r0, r1, depth, a + 0.012, a + span - 0.012,
              m[PALETTE[i][0]], e, segs=max(3, int(48 * v / total)))
        u = 0.05 + 0.45 * a / (2 * math.pi)
        show(e, [(F(b, u), END)])
        mid = a + span / 2
        tags.append((name, v, mid, u))
        a += span
    label(f"{spec['title']} ({fmt(total, unit)})", (c[0], c[1] + r1 + 140, 0.0), g, beat_iv(b, 0.02))
    for tg in spec.get("tags", []):
        name, v, mid, u = tags[tg["s"]]
        r = r1 + 60
        label(tg["text"], (c[0] + r * math.sin(mid), c[1] + r * math.cos(mid), 40.0), g, beat_iv(b, tg.get("u", 0.6)))
    for name, v, mid, u in (tags[:3] if spec.get("auto_tags", True) else []):
        r = r1 + 60
        p = (c[0] + r * math.sin(mid), c[1] + r * math.cos(mid), 40.0)
        label(f"{name} {v / total * 100:.0f}%", p, g, beat_iv(b, min(0.9, u + 0.12)))
    return (0.0, c[1], 0.0)


def build_towers(g, m, b, spec):
    """spec: {"title", "unit", "periods": [...], "series": [[name, [v per period]], ...]}
    "pct": true draws each tower as shares of 100%. "tags": [{"i": period, "s": series, "text"}]
    pin callouts at the middle of that part."""
    periods = [str(p) for p in spec["periods"]]
    series = [(str(n), [max(0.0, float(v or 0)) for v in vs]) for n, vs in spec["series"]]
    unit = spec.get("unit", "")
    n = len(periods)
    tot = [sum(vs[i] for _, vs in series) for i in range(n)]
    if spec.get("pct"):
        series = [(nm, [v / max(tot[i], 1e-9) * 100 for i, v in enumerate(vs)]) for nm, vs in series]
        tot, unit = [100.0] * n, "%"
    S = PH / max(max(tot), 1e-9)
    step = PW / max(n, 1)
    w = min(step * 0.62, 520.0)
    floor(g, m)
    x0 = -PW / 2 + step / 2
    colors = spec.get("colors") or list(range(len(series)))  # palette index per series
    for i in range(n):
        parts = [(vs[i] * S, m[PALETTE[colors[k] % len(PALETTE)][0]]) for k, (_, vs) in enumerate(series)]
        pv = stacked(f"t{i}", g, x0 + step * i, w, parts, d=min(w, 300.0))
        u0 = 0.05 + 0.55 * i / max(n, 1)
        grow(pv, F(b, u0), F(b, u0 + 0.15))
    label(f"{spec['title']} ({unit})" if unit else spec["title"], (-PW / 2 + 200, PH + 120, 0.0), g, beat_iv(b, 0.02))
    for i in range(n):  # period names under the towers
        label(periods[i], (x0 + step * i - w / 2, 30.0, 40.0), g, beat_iv(b, 0.05 + 0.55 * i / max(n, 1)))

    def mid_of(i, k):
        return sum(series[j][1][i] for j in range(k)) * S + series[k][1][i] * S / 2

    for tg in spec.get("tags", []):
        i, k = tg["i"] % n, tg["s"]
        label(tg["text"], (x0 + step * i + w / 2 + 20, mid_of(i, k), 60.0), g, beat_iv(b, tg.get("u", 0.6)))
    if not spec.get("auto_tags", True):
        return (0.0, PH * 0.56, 0.0)
    last = n - 1
    label(f"{periods[last]} {fmt(tot[last], unit)}", (x0 + step * last, tot[last] * S + 12, 0.0), g, beat_iv(b, 0.7))
    # the biggest part of the latest tower, tagged at its middle
    k = max(range(len(series)), key=lambda k: series[k][1][last])
    y = sum(series[j][1][last] for j in range(k)) * S + series[k][1][last] * S / 2
    share = series[k][1][last] / max(tot[last], 1e-9) * 100
    label(f"{series[k][0]} {share:.0f}%", (x0 + step * last - w / 2 - 20, y, 60.0), g, beat_iv(b, 0.8))
    return (0.0, PH * 0.56, 0.0)


PANELS = {"bars": build_bars, "donut": build_donut, "towers": build_towers}


# ---- composer ---------------------------------------------------------------------------------


def build(spec):
    """One spec -> one scene of max(3, beats) 8 s beats in the current (fresh) Blender file."""
    beats = spec["beats"][:MAX_BEATS]
    n = max(BEATS, len(beats))
    global END
    END = F(n, 0)
    _, root = start(spec["name"], beats=n, page="tpl")
    m = mats()
    poses = []
    for i, p in enumerate(beats):
        # every panel sits at the origin and shows only in its beat (the camera cuts between
        # beats): pbr3d drew panels spread far along x with uneven spacing
        ox = 0.0
        g = empty(f"panel{i}_{p['panel']}", root)
        last = i == len(beats) - 1
        show(g, [(F(i, 0), F(n, 0) if last else F(i + 1, 0))])
        before = set(bpy.data.objects)
        t = PANELS[p["panel"]](g, m, i, p)
        # panels reuse names ("b0", "floor"); pbr3d resolves nodes by name, so make them unique
        for o in set(bpy.data.objects) - before:
            if not o.name.startswith(("label:", "site:")):
                o.name = f"p{i}_{o.name.split('.')[0]}"
        dist, yaw, pitch = p.get("cam", CAM)
        poses.append(((ox + t[0], t[1], t[2]), dist, yaw, pitch))
    while len(poses) < n:
        poses.append(poses[-1])
    camera(root, poses)


def finish(name):
    os.makedirs(ASSETS, exist_ok=True)
    glb = os.path.join(ASSETS, f"{name}.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb, export_format="GLB", export_yup=True, export_animations=True,
        export_force_sampling=True, export_frame_step=1, export_cameras=False,
        export_lights=False, use_selection=False,
    )
    print("exported", glb)
    return glb
