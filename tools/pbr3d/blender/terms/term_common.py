"""Shared setup for hand-built term scenes (blender/terms/trm_*.py).

Each script defines SLUG and BEATS = [(caption, explanation), ...], builds its scene with the
POWER-page kit (power_vrm_detail) plus the extra parts here, then calls `done(SLUG, BEATS)`, which
exports assets/term_<SLUG>.glb and writes specs/terms/<SLUG>.json (captions + per-beat text, read
by py/tools/terms_gen.py; the "script" key makes term_kit.py leave the GLB alone).
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.dirname(HERE)
sys.path.insert(0, BL)
import sand_overview as O  # noqa: E402
from sand_overview import F, P, beat, empty, key, label, show, tube  # noqa: E402
from sand_zooms import finish, start  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, mat  # noqa: E402

SPECS = os.path.normpath(os.path.join(BL, "..", "specs", "terms"))


def setup(slug, n):
    m, root = start(slug, beats=n, page="term")
    m.update(D.materials())
    extra = {
        "ceramic": ((0.80, 0.70, 0.52), 0.0, 0.75),
        "nickel": ((0.62, 0.64, 0.66), 0.95, 0.28),
        "tin": ((0.86, 0.87, 0.89), 0.9, 0.2),
        "si": ((0.36, 0.38, 0.46), 0.5, 0.35),
        "sic": ((0.22, 0.42, 0.36), 0.3, 0.35),
        "gan": ((0.55, 0.50, 0.30), 0.3, 0.35),
        "algan": ((0.70, 0.62, 0.40), 0.3, 0.35),
        "nplus": ((0.30, 0.45, 0.80), 0.3, 0.4),
        "pbody": ((0.75, 0.40, 0.45), 0.3, 0.4),
        "ndrift": ((0.45, 0.58, 0.85), 0.3, 0.45),
        "pplus": ((0.85, 0.30, 0.35), 0.3, 0.4),
        "oxide": ((0.85, 0.90, 0.95), 0.0, 0.2),
        "poly": ((0.55, 0.25, 0.25), 0.3, 0.4),
        "alum": ((0.80, 0.82, 0.86), 0.9, 0.25),
        "quartz_c": ((0.85, 0.90, 0.95), 0.0, 0.08),
        "pcb_blue": ((0.10, 0.18, 0.40), 0.0, 0.55),
        "white": ((0.92, 0.92, 0.90), 0.0, 0.6),
        "rubber": ((0.10, 0.10, 0.11), 0.0, 0.85),
        "steel": ((0.60, 0.62, 0.66), 0.9, 0.35),
        "aln": ((0.78, 0.76, 0.70), 0.1, 0.4),
        "moly": ((0.55, 0.56, 0.60), 0.9, 0.3),
        "car": ((0.20, 0.26, 0.34), 0.7, 0.3),
    }
    for k, (c, metal, rough) in extra.items():
        m[k] = mat(f"t_{k}", c, metal=metal, rough=rough)
    glows = {
        "e_blue": ((0.30, 0.65, 1.0), 6.0),
        "h_amber": ((1.0, 0.62, 0.18), 6.0),
        "sig": ((0.35, 1.0, 0.55), 6.0),
        "bit": ((0.95, 0.95, 1.0), 6.0),
        "rf": ((0.85, 0.45, 1.0), 5.0),
        "dim_glow": ((0.30, 0.40, 0.55), 1.2),
        "chan": ((0.40, 0.85, 1.0), 3.0),
        "warn": ((1.0, 0.25, 0.15), 4.0),
    }
    for k, (c, s) in glows.items():
        m[k] = mat(f"t_{k}", c, emit=c, strength=s)
    m["die_hot"] = mat("t_die_hot", (0.55, 0.28, 0.20), emit=(1.0, 0.40, 0.12), strength=0.45)
    return m, root


def tags(root, per_beat):
    for i, items in per_beat.items():
        for text, pos in items:
            label(text, pos, root, beat(i))


def chip(m, parent, name, c, w, d, h=1.6, pins=8, pitch=None, body="mold", lead="tin"):
    """A leaded package (SOIC/QFP style) centred on c on the board top: pins on all four sides
    when pins > 0. Returns the top centre."""
    x, y, z = c
    g = empty(name, parent)
    bx(f"{name}_b", (x - w / 2, y + 0.3, z - d / 2), (x + w / 2, y + h, z + d / 2), m[body], g)
    if pins:
        p = pitch or (w / (pins + 1))
        for side in (-1, 1):
            for i in range(pins):
                px = x - w / 2 + p * (i + 1)
                bx(f"{name}_pz{side}{i}", (px - p * 0.22, y, z + side * d / 2), (px + p * 0.22, y + 0.5, z + side * (d / 2 + 1.4)), m[lead], g)
            nz = max(1, int(d / p) - 1)
            for i in range(nz):
                pz = z - d / 2 + d * (i + 1) / (nz + 1)
                bx(f"{name}_px{side}{i}", (x + side * w / 2, y, pz - p * 0.22), (x + side * (w / 2 + 1.4), y + 0.5, pz + p * 0.22), m[lead], g)
    D.tube(f"{name}_dot", (x - w / 2 + 1.2, y + h, z - d / 2 + 1.2), (x - w / 2 + 1.2, y + h + 0.05, z - d / 2 + 1.2), 0.4, m["ink"], g, 10)
    return (x, y + h, z)


def pcb(m, parent, name, x0, x1, z0, z1=0.0, t=1.6, mask="mask"):
    """A plain board: mask on top of FR4 with a copper layer, front edge at z1."""
    g = empty(name, parent)
    bx(f"{name}_fr4", (x0, -t, z0), (x1, -0.4, z1), m["fr4"], g)
    bx(f"{name}_cu", (x0, -0.4, z0), (x1, -0.2, z1), m["copper"], g)
    bx(f"{name}_mask", (x0, -0.2, z0), (x1, 0.0, z1), m[mask], g)
    return g


def trace(m, parent, name, pts, w=0.5, mt="copper"):
    """A flat copper trace through pts on the board top (y of the points)."""
    parts = []
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        lo = (min(a[0], b[0]) - w / 2, a[1], min(a[2], b[2]) - w / 2)
        hi = (max(a[0], b[0]) + w / 2, a[1] + 0.15, max(a[2], b[2]) + w / 2)
        parts.append(bx(f"{name}_{k}", lo, hi, m[mt], parent))
    return D.join(parts, name)


def wiggle(obj, beats, amp=(0.0, 0.4, 0.0), period=6):
    """Shake `obj` (a group) back and forth during each beat: a vibrating resonator or plate."""
    bl = [beats] if isinstance(beats, int) else beats
    for b in bl:
        f0, f1 = F(b, 0), F(b + 1, 0)
        f = f0
        s = 1
        while f < f1:
            key(obj, f, "location", P(*(a * s for a in amp)), linear=True)
            f += period // 2
            s = -s
        key(obj, f1, "location", P(0, 0, 0), linear=True)


def spin(obj, beats, turns=1.0, axis=1):
    """Turn `obj` about the scene's y (axis=1) during the given beats."""
    bl = [beats] if isinstance(beats, int) else beats
    O._interp("LINEAR")
    for b in bl:
        for j in range(9):
            f = F(b, j / 8)
            a = 2 * math.pi * turns * j / 8
            # axis 1: scene y (Blender z); 2: scene z (Blender y); else scene x
            obj.rotation_euler = (0.0, 0.0, a) if axis == 1 else (0.0, a, 0.0) if axis == 2 else (a, 0.0, 0.0)
            obj.keyframe_insert("rotation_euler", frame=f)


def wave_pts(x0, x1, y, z, amp, cycles, n=80, phase=0.0, fn=None):
    pts = []
    for i in range(n + 1):
        u = i / n
        v = fn(u) if fn else math.sin(2 * math.pi * cycles * u + phase)
        pts.append((x0 + (x1 - x0) * u, y + amp * v, z))
    return pts


# ---- the base layer: MLCC's GPU board ----------------------------------------------------------
# Board x -310..250, z -215..0 (front cut at z = 0), top at y = 0. The GPU package sits at x = 0,
# 8 phases a side out to |x| ~128. The open strip BENCH (x 150..248) on the right is where each
# term stands its own part, large and cut open, with a magnifier line back to where it lives.

BENCH = (150.0, 248.0)


def decaps(m, root):
    """Decoupling caps: rings on top round the package and a field on the back under it.
    Returns (top group, back group, 4 flicker-glow groups, top cap spots)."""
    top = empty("dc_top", root)
    glow_top = [empty(f"dc_glow{k}", root) for k in range(4)]
    spots = []
    for hx, hz0, hz1 in ((70.0, -70.0, 4.0), (78.0, -78.0, 8.0)):
        for i in range(16):
            spots.append((-hx + 2 * hx * (i + 0.5) / 16, hz0, "x"))
        for j in range(8):
            z = hz0 + (hz1 - hz0 - 6.0) * (j + 0.5) / 8
            for x in (-hx, hx):
                spots.append((x, z, "z"))
    spots = [s for s in spots if abs(s[0]) > 66.0 or s[1] < -66.0]
    for k, (x, z, along) in enumerate(spots):
        zc = min(z, -2.0)
        D.mlcc(m, top, f"dc{k}", (x, 0.0, zc), 4.0, 2.0, 2.0, along=along)
        bx(f"dcg{k}", (x - 1.0, 2.0, zc - 1.0), (x + 1.0, 2.6, zc + 1.0), m["v12"], glow_top[k % 4])
    back = empty("dc_back", root)
    for i in range(14):
        for j in range(7):
            D.mlcc(m, back, f"db{i}_{j}", (-52.0 + 8.0 * i, D.BOT - 1.6, -6.0 - 8.0 * j), 4.0, 2.0, 1.6)
    for g_ in glow_top:
        show(g_, [])
    return top, back, glow_top, spots


def base(m, root, decap=True, ctrl=False):
    """The shared GPU board. Returns a dict: pk (package points), die_glow, ph (phases), and when
    decap: glow (4 groups), spots."""
    D.board(m, root, window=False)
    _, die_glow, pk = D.package(m, root)
    ph = D.phases(m, root, heat=False)
    D.vias(m, root, [-40.0, -24.0, -8.0, 8.0, 24.0, 40.0], D.P08_Y, 0.0, "pkg_vias")
    D.vias(m, root, [-48.0, -16.0, 16.0, 48.0], D.BOT, D.P08_Y, "back_vias", 1.0)
    show(die_glow, [])
    out = {"pk": pk, "die_glow": die_glow, "ph": ph}
    if ctrl:  # the multiphase controller behind the package, PWM traces to every stage
        cp, traces = D.controller(m, root)
        out.update(ctrl=cp["ctrl"], traces=traces)
    if decap:
        _, _, glow, spots = decaps(m, root)
        out.update(glow=glow, spots=spots)
    return out


def magnify(m, root, at, to, r=4.0, name="mag"):
    """Mark the board spot `at` and run two glowing lines from it to the big part at `to`."""
    x, y, z = at
    bx(f"{name}_mark", (x - r, y, z - r), (x + r, y + 0.25, z + r), m["field"], root)
    for k, dy in enumerate((-0.5, 0.5)):
        D.polyline(f"{name}_l{k}", [(x, y + 3.0, z), (to[0], to[1] + dy * 30.0, to[2])], 0.25, m["field"], root)


def xsec(m, parent, name, x0, x1, z0, bands):
    """A device cross-section block cut at z = 0: `bands` = [(y0, y1, mat), ...] bottom up."""
    g = empty(name, parent)
    for k, (y0, y1, mt) in enumerate(bands):
        bx(f"{name}_{k}", (x0, y0, z0), (x1, y1, 0.0), m[mt], g)
    return g


def rings(m, root, name, c, beats, n=4, r0=4.0, r1=60.0, mt="rf", axis="y"):
    """Radio waves: `n` thin glowing rings that grow from r0 to r1 round c, one after another,
    through each beat in `beats`."""
    bl = [beats] if isinstance(beats, int) else beats
    out = []
    for k in range(n):
        outer = empty(f"{name}{k}_o", root)
        g = empty(f"{name}{k}", outer, P(*c))
        ring = []
        for j in range(24):
            a0, a1 = 2 * math.pi * j / 24, 2 * math.pi * (j + 1) / 24
            if axis == "y":  # ring in the x-y plane (facing the camera)
                p0, p1 = (math.cos(a0), math.sin(a0), 0.0), (math.cos(a1), math.sin(a1), 0.0)
            else:  # ring lying flat in x-z
                p0, p1 = (math.cos(a0), 0.0, math.sin(a0)), (math.cos(a1), 0.0, math.sin(a1))
            ring.append(tube(f"{name}{k}_{j}", p0, p1, 0.03, m[mt], g, 6))
        D.join(ring, f"{name}{k}_m")
        O._interp("LINEAR")
        iv = []
        for b in bl:
            fa = F(b, k / n * 0.8)
            fb = fa + 60
            for f, r in ((fa, r0), (fb, r1)):
                g.scale = (r, r, r)
                g.keyframe_insert("scale", frame=f)
            iv.append((fa, min(fb, F(b + 1, 0))))
        D.present(outer, iv)
        out.append(outer)
    return out


def done(slug, beats, camera_plan, root):
    D.camera_path(root, camera_plan)
    finish(slug, page="term")
    spec = {"slug": slug, "script": f"terms/trm_{slug[4:].lower()}.py",
            "beats": [{"caption": c, "text": t} for c, t in beats]}
    with open(os.path.join(SPECS, f"{slug}.json"), "w") as f:
        json.dump(spec, f, indent=1)
