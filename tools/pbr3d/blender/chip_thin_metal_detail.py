"""Detailed parts for the THIN METAL sections (chip_thin_metal.py sec1-sec10), and the small
camera and tag helpers chip_contacts_detail.py shares.

The sections no longer replay the schematic whole chip: each one builds a cut-away of the real
structure at about 10 scene mm per nanometre, so a 28 nm pitch is 280 mm in the scene.

  stack()      M1-M4 in cut-away: copper lines in a TaN barrier and Co liner, low-k between them,
               SiCN caps, vias between levels, tungsten contacts and silicon below. Alternate levels
               run at right angles, and each level is set back from the one below like a staircase,
               so the tops of the lower levels show too.
  damascene()  one damascene loop on a small block: trench, barrier, copper fill, polish and cap.
  subtractive() the other route: a ruthenium blanket etched into lines, then gap-filled with air gaps.
  xsec()       one line in cross-section, for the width and metal comparisons.
  cell()       a standard cell from above: rails, gates, M1 pins and the M2 tracks over them.

Camera: frame() fits a box in the left pane; glide() eases from beat to beat. Units: Y up, the
cut plane at z = 0 and the camera on +z. Fill materials (low-k, silicon) stop at z = -1 and the
parts in them come forward to z = +1..+3, so the cut faces never z-fight.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, box, empty, key, label, mat, rel, show  # noqa: E402
from sand_zooms import scale_keys, stream_of  # noqa: E402

# ---- camera and tags (shared with chip_contacts_detail) -----------------------------------

HALF_H = 0.266  # tan of half the vertical field of view (0.52 rad)
HALF_W = 0.29  # the left pane is a little wider than tall


def frame(lo, hi, yaw=0.45, pitch=0.30, fill=0.84, dx=0.0):
    """The (target, distance, yaw, pitch) pose that fits the box lo..hi in the left pane. `dx`
    shifts the target right (in scene x), to leave room for tags that run right of their pins."""
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    e = (cp * sy, sp, cp * cy)
    r = (cy, 0.0, -sy)
    u = (-sp * sy, cp, -sp * cy)
    d = 0.0
    for X in (lo[0], hi[0]):
        for Y in (lo[1], hi[1]):
            for Z in (lo[2], hi[2]):
                v = (X - c[0], Y - c[1], Z - c[2])
                de = sum(v[i] * e[i] for i in range(3))
                a = abs(sum(v[i] * r[i] for i in range(3)))
                b = abs(sum(v[i] * u[i] for i in range(3)))
                d = max(d, de + a / (HALF_W * fill), de + b / (HALF_H * fill))
    c[0] += dx
    return (tuple(c), d, yaw, pitch)


def glide(root, poses, glide_u=0.25):
    """One pose per beat. Beat 0 holds from the start; later beats ease in from the previous pose
    over the first `glide_u` of the beat, then hold with a slow push-in."""
    target = empty("CamTarget", root)
    eye = empty("CamEye", root)
    for i, (t, dist, yaw, pitch) in enumerate(poses):
        cp, sp = math.cos(pitch), math.sin(pitch)
        a = F(i, 0) if i == 0 else F(i, glide_u)
        b = F(i + 1, 0) - 1
        for f, d in ((a, dist * 1.03), (b, dist * 0.97)):
            e = (t[0] + d * cp * math.sin(yaw), t[1] + d * sp, t[2] + d * cp * math.cos(yaw))
            key(target, f, "location", P(*t))
            key(eye, f, "location", P(*e))


def span(a, b):
    return [(F(a, 0), F(b, 0))]


def sub(b, u0, u1):
    return [(F(b, u0), F(b, u1))]


def group(name, parent, intervals=None):
    g = empty(name, parent)
    if intervals is not None:
        show(g, intervals)
    return g


def tags(root, items):
    """(intervals, text, point) per tag."""
    for iv, text, at in items:
        label(text, at, root, iv)


def lined(name, lo, hi, b, mb, mc, parent, liner=0.0, ml=None, axis="z"):
    """A metal part in its barrier: the barrier box lo..hi, an optional liner `liner` thick inside
    it, and the core inside that. The top stays open (the core comes up to the top), as after
    CMP. The front faces step forward (+1, +1.5, +2) so the cut face shows the rings. `axis` is
    the run direction; a part running in z keeps its back face, the others are lined behind."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    box(name + "_bar", (x0, y0, z0), (x1, y1, z1 + 1.0), mb, parent)
    t = b
    if liner and ml is not None:
        zb = z0 if axis == "z" else z0 + b
        box(name + "_lin", (x0 + b, y0 + b, zb), (x1 - b, y1 + 0.5, z1 + 1.5), ml, parent)
        t = b + liner
    zb = z0 if axis == "z" else z0 + t
    return box(name + "_core", (x0 + t, y0 + t, zb), (x1 - t, y1 + 1.0, z1 + 2.0), mc, parent)


def bar(name, x, y0, h, w, m, parent, z=-60.0, d=120.0):
    """A bar for a quantity: w wide, h tall, standing on y0."""
    return box(name, (x - w / 2, y0, z - d / 2), (x + w / 2, y0 + h, z + d / 2), m, parent)


def grow(name, at, parent, f0, f1, axis=2):
    """A pivot at `at` whose children (built with rel(at, p)) grow from nothing along Blender
    axis `axis` (2 is scene Y) between frames f0 and f1."""
    p = empty(name, parent, P(*at))
    s0 = [1.0, 1.0, 1.0]
    s0[axis] = 0.001
    scale_keys(p, [(0, tuple(s0)), (f0, tuple(s0)), (f1, (1.0, 1.0, 1.0))])
    return p


def front_glow(name, lo, hi, m, parent, intervals, z=4.0):
    """A thin glowing plate on the cut face over lo..hi (x, y), just in front of it."""
    g = group(name, parent, intervals)
    box(name + "_p", (lo[0], lo[1], z - 1.0), (hi[0], hi[1], z), m, g)
    return g


def ring_glow(name, lo, hi, t, m, parent, intervals, z=4.0, top=False):
    """A glowing U (or full ring with `top`) t thick on the cut face, round lo..hi (x, y)."""
    g = group(name, parent, intervals)
    (x0, y0), (x1, y1) = lo, hi
    box(name + "_l", (x0, y0, z - 1), (x0 + t, y1, z), m, g)
    box(name + "_r", (x1 - t, y0, z - 1), (x1, y1, z), m, g)
    box(name + "_b", (x0, y0, z - 1), (x1, y0 + t, z), m, g)
    if top:
        box(name + "_t", (x0, y1 - t, z - 1), (x1, y1, z), m, g)
    return g


def dots(root, m, name, pts, beat, u0, u1, n=8, life=70, size=16.0):
    """A train of glowing dots along the polyline `pts` through beat `beat`."""
    s = pts[0]
    path = [(p[0] - s[0], p[1] - s[1], p[2] - s[2]) for p in pts]
    return stream_of(root, name, n, s, path, size, m, beat, u0, u1, life)


# ---- materials -----------------------------------------------------------------------------


def materials(m):
    m["cu"] = mat("d_cu", (0.88, 0.50, 0.28), metal=0.85, rough=0.30)
    m["tan"] = mat("d_tan", (0.20, 0.26, 0.55), metal=0.4, rough=0.4, emit=(0.18, 0.28, 0.75), strength=0.6)
    m["co"] = mat("d_co", (0.78, 0.76, 0.86), metal=0.9, rough=0.25)
    m["ru"] = mat("d_ru", (0.45, 0.80, 0.74), metal=0.85, rough=0.25)
    m["mo"] = mat("d_mo", (0.85, 0.72, 0.42), metal=0.85, rough=0.30)
    m["w"] = mat("d_w", (0.80, 0.84, 0.92), metal=0.55, rough=0.30)
    m["tin"] = mat("d_tin", (0.80, 0.68, 0.32), metal=0.7, rough=0.35)
    m["lowk"] = mat("d_lowk", (0.56, 0.54, 0.64), rough=0.85)
    m["lowk2"] = mat("d_lowk2", (0.34, 0.33, 0.42), rough=0.85)
    m["cap"] = mat("d_cap", (0.82, 0.88, 0.94), rough=0.5)
    m["si"] = mat("d_si", (0.24, 0.26, 0.34), metal=0.3, rough=0.4)
    m["air"] = mat("d_air", (0.04, 0.05, 0.09), rough=0.9)
    m["hm"] = mat("d_hm", (0.30, 0.26, 0.24), metal=0.5, rough=0.5)
    m["resist"] = mat("d_resist", (0.80, 0.32, 0.52), rough=0.6)
    m["euv"] = mat("d_euv", (0.65, 0.45, 1.0), emit=(0.60, 0.40, 1.0), strength=2.0, alpha=0.22)
    m["glass"] = mat("d_glass", (0.20, 0.22, 0.28), metal=0.3, rough=0.15)
    m["gate"] = mat("d_gate", (0.45, 0.16, 0.16), rough=0.6)
    m["rail"] = mat("d_rail", (0.95, 0.70, 0.30), metal=0.6, rough=0.35)
    m["hl"] = mat("d_hl", (1.0, 0.75, 0.30), emit=(1.0, 0.68, 0.22), strength=3.0)
    m["hl_soft"] = mat("d_hl_soft", (1.0, 0.75, 0.30), emit=(1.0, 0.68, 0.22), strength=1.5, alpha=0.35)
    m["bad"] = mat("d_bad", (1.0, 0.22, 0.18), emit=(1.0, 0.20, 0.15), strength=1.8)
    m["good"] = mat("d_good", (0.35, 1.0, 0.55), emit=(0.30, 1.0, 0.50), strength=3.0)
    m["sig"] = mat("d_sig", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=3.5)
    m["sig_soft"] = mat("d_sig_soft", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=0.5, alpha=0.20)
    m["rbar"] = mat("d_rbar", (0.95, 0.35, 0.20), emit=(1.0, 0.32, 0.18), strength=0.5)
    m["gbar"] = mat("d_gbar", (0.35, 0.85, 1.0), emit=(0.30, 0.80, 1.0), strength=1.6)
    m["base"] = mat("d_base", (0.30, 0.32, 0.38), rough=0.7)
    return m


# ---- the M1-M4 stack -------------------------------------------------------------------------

B = 12.0  # TaN barrier
L = 8.0  # Co or Ru liner: barrier and liner together are 2 nm
CAP = 30.0  # SiCN etch-stop cap on each level
X0, X1, ZB = -1200.0, 1200.0, -2200.0
# name, run axis, pitch, width, height, via height, front z (each level is set back: a staircase;
# M3's front sits on the centre of an M2 line so the M3 vias on the cut face land on it)
LEVELS = [
    ("M1", "z", 320.0, 160.0, 320.0, 0.0, 0.0),
    ("M2", "x", 280.0, 140.0, 280.0, 200.0, -300.0),
    ("M3", "z", 280.0, 140.0, 280.0, 200.0, -860.0),
    ("M4", "x", 360.0, 180.0, 360.0, 240.0, -1160.0),
]
CONTACT_Y0, SI_Y0 = -200.0, -520.0


def stack_layout():
    """Per level: dict(name, axis, p, w, h, yv0 (via bottom), y0, y1 (line), fz, pos (line
    centres: x for z-running, z for x-running))."""
    out, y = [], 0.0
    for name, axis, p, w, h, hv, fz in LEVELS:
        yv0 = y
        y += hv
        y0, y1 = y, y + h
        if axis == "z":
            pos, k = [], 0
            while X0 + p / 2 + k * p + w / 2 <= X1:
                pos.append(X0 + p / 2 + k * p)
                k += 1
        else:
            pos, k = [], 0
            while fz - k * p - w / 2 >= ZB:
                pos.append(fz - k * p)
                k += 1
        out.append(dict(name=name, axis=axis, p=p, w=w, h=h, yv0=yv0, y0=y0, y1=y1, fz=fz, pos=pos))
        y = y1 + CAP
    return out


LAY = stack_layout()


def line_box(lv, c):
    """The (lo, hi) of the line at centre `c` on level `lv`, its front on the level's cut face."""
    w = lv["w"]
    if lv["axis"] == "z":
        return (c - w / 2, lv["y0"], ZB), (c + w / 2, lv["y1"], lv["fz"])
    return (X0, lv["y0"], c - w / 2), (X1, lv["y1"], min(c + w / 2, lv["fz"]))


def via_xs():
    """(level index, x) of the vias drawn on each cut face, at the x of a line they join."""
    out = []
    m1, m3 = LAY[0]["pos"], LAY[2]["pos"]
    out += [(1, m1[1]), (1, m1[4]), (1, m1[6])]  # M2 vias land on M1 lines
    out += [(2, m3[2]), (2, m3[6])]  # M3 lines drop vias onto the M2 line under the M3 cut face
    out += [(3, m3[4]), (3, m3[7])]  # M4 vias land on M3 lines
    return out


def stack(m, parent, metal="cu", vias=True, contacts=True):
    """M1-M4 in cut-away. Returns a dict of handy pin points."""
    g = empty("stack", parent)
    pins = {}
    # silicon and the contact level
    box("si", (X0, SI_Y0, ZB), (X1, CONTACT_Y0, -1.0), m["si"], g)
    box("ild0", (X0, CONTACT_Y0, ZB), (X1, 0.0, -1.0), m["lowk2"], g)
    if contacts:
        for k in (1, 4, 6):
            x = LAY[0]["pos"][k]
            box(f"ca{k}", (x - 50, CONTACT_Y0, -120.0), (x + 50, 1.0, 2.0), m["w"], g)
        pins["contact"] = (LAY[0]["pos"][4], -100.0, 3.0)
    pins["si"] = (LAY[0]["pos"][2], -380.0, 3.0)
    for i, lv in enumerate(LAY):
        lg = empty(f"lvl_{lv['name']}", g)
        fz, w, p = lv["fz"], lv["w"], lv["p"]
        nxt = LAY[i + 1]["fz"] if i + 1 < len(LAY) else None
        if lv["yv0"] < lv["y0"]:  # the via level: low-k, the vias come forward on the cut face
            box(f"ildv{i}", (X0, lv["yv0"], ZB), (X1, lv["y0"], fz - 1.0), m["lowk2"], lg)
        for k, c in enumerate(lv["pos"]):
            lo, hi = line_box(lv, c)
            lined(f"{lv['name']}_{k}", lo, hi, B, m["tan"], m[metal], lg, liner=L, ml=m["co"], axis=lv["axis"])
        # low-k between the lines
        if lv["axis"] == "z":
            edges = [X0] + [e for c in lv["pos"] for e in (c - w / 2, c + w / 2)] + [X1]
            for k in range(0, len(edges), 2):
                if edges[k + 1] - edges[k] > 1:
                    box(f"gap{i}_{k}", (edges[k], lv["y0"], ZB), (edges[k + 1], lv["y1"], fz - 1.0), m["lowk"], lg)
        else:
            # from the back face of line k to the front face of line k+1 (the last: to the back)
            for k in range(len(lv["pos"])):
                za = lv["pos"][k] - w / 2
                zb = lv["pos"][k + 1] + w / 2 if k + 1 < len(lv["pos"]) else ZB
                if za - zb > 1:
                    box(f"gap{i}_{k}", (X0, lv["y0"], zb), (X1, lv["y1"], za), m["lowk"], lg)
        if nxt is not None:
            box(f"cap{i}", (X0, lv["y1"], ZB), (X1, lv["y1"] + CAP, nxt - 1.0), m["cap"], lg)
        pins[lv["name"]] = lv
    if vias:
        for i, x in via_xs():
            lv = LAY[i]
            vw = min(lv["w"], 130.0)
            lined(f"via{i}_{x:.0f}", (x - vw / 2, lv["yv0"] - CAP, lv["fz"] - 70.0), (x + vw / 2, lv["y0"] + 2.0, lv["fz"]),
                  B, m["tan"], m[metal], g, liner=L, ml=m["co"], axis="y")
    return g, pins


def front(lv, k=0, dy=0.5):
    """A pin point on the cut face of line k of level lv, `dy` of the way up it."""
    if lv["axis"] == "z":
        return (lv["pos"][k], lv["y0"] + dy * lv["h"], lv["fz"] + 3.0)
    return (X0 + 300.0 + 200.0 * k, lv["y0"] + dy * lv["h"], lv["fz"] + 3.0)


STACK_LO = (X0, SI_Y0, ZB)
STACK_HI = (X1, LAY[-1]["y1"], 0.0)


# ---- one damascene loop on a small block -----------------------------------------------------


def damascene(m, parent, ox, b, metal="cu", n=3, p=320.0, w=160.0, h=300.0, cap=True):
    """A low-k block at x offset `ox` going through one loop in beat `b`: trenches cut through a
    hard mask (0-0.25), barrier and liner (0.25-0.5), copper overfill (0.5-0.75), polish and cap
    (0.75-1). Returns pin points and the block's bounds. Built so it holds its last state after `b`."""
    g = empty("dam", parent)
    zb, base = -900.0, 80.0
    xs = [ox + (k - (n - 1) / 2) * p for k in range(n)]
    xa, xb = xs[0] - p / 2, xs[-1] + p / 2
    top = base + h
    box("dam_base", (xa, 0.0, zb), (xb, base, -1.0), m["lowk2"], g)
    edges = [xa] + [e for x in xs for e in (x - w / 2, x + w / 2)] + [xb]
    for k in range(0, len(edges), 2):
        box(f"dam_gap{k}", (edges[k], base, zb), (edges[k + 1], top, -1.0), m["lowk"], g)
    end = F(b + 1, 0) + 100000
    hm = group("dam_hm", g, [(0, F(b, 0.75))])
    for k in range(0, len(edges), 2):
        box(f"dam_hm{k}", (edges[k], top, zb), (edges[k + 1], top + 40.0, 0.0), m["hm"], hm)
    bar_g = group("dam_bar", g, [(F(b, 0.25), end)])
    core_g = group("dam_core", g, [(F(b, 0.5), end)])
    for k, x in enumerate(xs):
        lo, hi = (x - w / 2, base - 0.0, zb), (x + w / 2, top, 0.0)
        box(f"dam_tan{k}", (lo[0], base, zb), (hi[0], top, 1.0), m["tan"], bar_g)
        box(f"dam_lin{k}", (lo[0] + B, base + B, zb), (hi[0] - B, top + 0.5, 1.5), m["co"], bar_g)
        box(f"dam_cu{k}", (lo[0] + B + L, base + B + L, zb), (hi[0] - B - L, top + 1.0, 2.0), m[metal], core_g)
    over = group("dam_over", g, [(F(b, 0.5), F(b, 0.75))])
    box("dam_blanket", (xa, top + 1.0, zb), (xb, top + 120.0, 2.0), m[metal], over)
    if cap:
        capg = group("dam_cap", g, [(F(b, 0.75), end)])
        box("dam_capb", (xa, top + 1.0, zb), (xb, top + 1.0 + CAP, 2.5), m["cap"], capg)
    pins = dict(trench=(xs[1], top - 60.0, 3.0), gap=(edges[2] + 40.0, base + h * 0.5, 3.0),
                core=(xs[1], base + h * 0.5, 3.0), bar=(xs[0] - w / 2 + 6, base + h * 0.4, 3.0),
                top=(xs[2], top + 60.0, 3.0), hm=(edges[4] + 40.0, top + 20.0, 3.0))
    return pins, (xa, 0.0, zb), (xb, top + 140.0, 0.0)


def subtractive(m, parent, ox, b, metal="ru", n=3, p=320.0, w=160.0, h=300.0, air=True, done_only=False):
    """The subtractive route at x offset `ox` in beat `b`: a metal blanket under a hard mask
    (0-0.33), etched to lines (0.33-0.66), gap-filled with dielectric and air gaps (0.66-1).
    `done_only` builds just the finished lines."""
    g = empty("sub", parent)
    zb, base = -900.0, 80.0
    xs = [ox + (k - (n - 1) / 2) * p for k in range(n)]
    xa, xb = xs[0] - p / 2, xs[-1] + p / 2
    top = base + h
    end = F(b + 1, 0) + 100000
    box("sub_base", (xa, 0.0, zb), (xb, base, -1.0), m["lowk2"], g)
    if not done_only:
        blanket = group("sub_blanket", g, [(0, F(b, 0.33))])
        box("sub_blank", (xa, base, zb), (xb, top, 1.0), m[metal], blanket)
        hm = group("sub_hm", g, [(0, F(b, 0.66))])
        for k, x in enumerate(xs):
            box(f"sub_hm{k}", (x - w / 2, top, zb), (x + w / 2, top + 40.0, 1.0), m["hm"], hm)
    lines = group("sub_lines", g, [(F(b, 0.33) if not done_only else 0, end)])
    for k, x in enumerate(xs):
        box(f"sub_l{k}", (x - w / 2, base, zb), (x + w / 2, top, 1.0), m[metal], lines)
    fill = group("sub_fill", g, [(F(b, 0.66) if not done_only else 0, end)])
    edges = [xa] + [e for x in xs for e in (x - w / 2, x + w / 2)] + [xb]
    for k in range(0, len(edges), 2):
        box(f"sub_gap{k}", (edges[k], base, zb), (edges[k + 1], top + 30.0, -1.0), m["lowk"], fill)
        if air and 0 < k < len(edges) - 2:
            gw = edges[k + 1] - edges[k]
            box(f"sub_air{k}", (edges[k] + gw * 0.3, base + 30.0, zb), (edges[k + 1] - gw * 0.3, top - 50.0, 0.5), m["air"], fill)
    box("sub_top", (xa, top, zb), (xb, top + 30.0, -1.0), m["lowk"], fill)
    pins = dict(line=(xs[1], base + h * 0.5, 3.0), air=((edges[2] + edges[3]) / 2, base + h * 0.45, 3.0),
                blanket=(xs[1] + p / 2, base + h * 0.5, 3.0), hm=(xs[2], top + 20.0, 3.0))
    return pins, (xa, 0.0, zb), (xb, top + 80.0, 0.0)


def xsec(m, parent, name, x, w, metal="cu", barrier=B, liner=L, lm="co", depth=600.0, aspect=2.0):
    """One line at x, w wide and aspect*w tall, on a low-k pad, its cut face at z = 0. `barrier`
    and `liner` 0 make a barrierless line. Returns (pin on the core, pin on the barrier, top y)."""
    g = empty(name, parent)
    h = aspect * w
    base = 60.0
    box(name + "_pad", (x - w / 2 - 60, 0.0, -depth), (x + w / 2 + 60, base, -1.0), m["lowk2"], g)
    # the low-k the line sits in, flush with its top, so only the cut face and the top show
    box(name + "_l", (x - w / 2 - 60, base, -depth), (x - w / 2, base + h, -1.0), m["lowk"], g)
    box(name + "_r", (x + w / 2, base, -depth), (x + w / 2 + 60, base + h, -1.0), m["lowk"], g)
    if barrier > 0:
        box(name + "_bar", (x - w / 2, base, -depth), (x + w / 2, base + h, 1.0), m["tan"], g)
    t = barrier
    if liner > 0:
        box(name + "_lin", (x - w / 2 + t, base + t, -depth), (x + w / 2 - t, base + h + 0.5, 1.5), m[lm], g)
        t += liner
    box(name + "_core", (x - w / 2 + t, base + t, -depth), (x + w / 2 - t, base + h + 1.0, 2.0), m[metal], g)
    return (x, base + h * 0.55, 3.0), (x - w / 2 + 3, base + h * 0.3, 3.0), base + h


# ---- a standard cell from above -------------------------------------------------------------

CELL_X0, CELL_X1 = -900.0, 900.0
CELL_Z0, CELL_Z1 = -840.0, 0.0  # cell height runs in z: the camera looks down on it
GATES_X = [-600.0, -200.0, 200.0, 600.0]
M2_Y = (150.0, 200.0)
M1_Y = (60.0, 130.0)


def cell(m, parent, ox=0.0, tracks=5):
    """A standard cell seen from above: VDD and VSS rails, four gates, M1 pins A, B and Y, and
    `tracks` M2 tracks (see-through) over them. Returns pins and the M2 track z positions."""
    g = empty("cell", parent)
    box("cell_base", (CELL_X0 + ox - 80, -60.0, CELL_Z0 - 120), (CELL_X1 + ox + 80, 0.0, CELL_Z1 + 120), m["si"], g)
    for k, x in enumerate(GATES_X):
        box(f"cell_gate{k}", (ox + x - 40, 0.0, CELL_Z0 + 60), (ox + x + 40, 40.0, CELL_Z1 - 60), m["gate"], g)
    for k, z in enumerate((CELL_Z0, CELL_Z1)):
        box(f"cell_rail{k}", (CELL_X0 + ox - 80, M1_Y[0], z - 60), (CELL_X1 + ox + 80, M1_Y[0] + 40, z + 60), m["rail"], g)
    # M1 pins: short vertical (z) runs between gates
    pins_x = {"A": -400.0, "B": 0.0, "Y": 400.0}
    for k, (nm, x) in enumerate(pins_x.items()):
        box(f"cell_pin{nm}", (ox + x - 50, M1_Y[0], -660.0), (ox + x + 50, M1_Y[1] + 10.0, -180.0), m["cu"], g)
    pitch = (CELL_Z1 - CELL_Z0) / (tracks + 1)
    zs = [CELL_Z1 - pitch * (k + 1) for k in range(tracks)]
    tg = empty("cell_tracks", g)
    for k, z in enumerate(zs):
        box(f"cell_trk{k}", (CELL_X0 + ox - 80, M2_Y[0], z - 14), (CELL_X1 + ox + 80, M2_Y[0] + 6, z + 14), m["sig_soft"], tg)
    pins = {nm: (ox + x, M1_Y[1] + 12, -420.0) for nm, x in pins_x.items()}
    pins["vdd"] = (ox + CELL_X0 + 100, M1_Y[1] + 2, CELL_Z1)
    pins["vss"] = (ox + CELL_X0 + 100, M1_Y[1] + 2, CELL_Z0)
    pins["gate"] = (ox + GATES_X[0], 42.0, -300.0)
    return g, pins, zs


CELL_LO = (CELL_X0 - 80, -60.0, CELL_Z0 - 120)
CELL_HI = (CELL_X1 + 80, 220.0, CELL_Z1 + 120)


__all__ = [
    "frame", "glide", "span", "sub", "group", "tags", "lined", "bar", "grow", "front_glow", "ring_glow",
    "dots", "materials", "stack", "front", "LAY", "STACK_LO", "STACK_HI", "damascene", "subtractive",
    "xsec", "cell", "CELL_LO", "CELL_HI", "rel", "ball", "box", "empty", "F", "show",
]


# ---- insets: a detailed rig placed, scaled down, where it sits in the whole chip -------------


def inset(parent, origin, s, intervals):
    """An empty at `origin` (chip coordinates) scaled by `s`, shown for `intervals`. Build a rig
    under it in its own coordinates and it sits in the chip at that scale; pass rig poses
    through world() to frame them."""
    g = group("inset", parent, intervals)
    e = empty("inset_s", g, P(*origin))
    e.scale = (s, s, s)
    return e


def world(pose, origin, s):
    """A pose in an inset's own coordinates, moved into the chip's."""
    t, d, yaw, pitch = pose
    return (tuple(origin[i] + s * t[i] for i in range(3)), d * s, yaw, pitch)


# ---- one damascene loop, animated over three beats ------------------------------------------


def loop_rig(m, parent):
    """A low-k block taken through a whole loop. Beat 0: resist under EUV light, then trenches
    etched through the hard mask. Beat 1: barrier and liner, copper grows up from the trench
    floors as ions rain in, then an overburden. Beat 2: a CMP pad sweeps it flat, the SiCN cap goes
    down, and the next via level opens over the middle line. Returns pins and bounds."""
    from sand_overview import fly
    g = empty("loop", parent)
    n, p, w, h, zb, base = 3, 320.0, 160.0, 300.0, -900.0, 80.0
    xs = [(k - 1) * p for k in range(n)]
    xa, xb = -1.5 * p, 1.5 * p
    top = base + h
    end = F(3, 0) + 100000
    box("lp_base", (xa, 0.0, zb), (xb, base, -1.0), m["lowk2"], g)
    whole = group("lp_whole", g, [(0, F(0, 0.5))])
    box("lp_slab", (xa, base, zb), (xb, top, -1.0), m["lowk"], whole)
    box("lp_hm0", (xa, top, zb), (xb, top + 40.0, 0.0), m["hm"], whole)
    res = group("lp_resist", g, [(0, F(0, 0.5))])
    box("lp_res", (xa, top + 40.0, zb), (xb, top + 100.0, 0.5), m["resist"], res)
    beam = group("lp_beam", g, [(F(0, 0.08), F(0, 0.45))])
    box("lp_light", (xa + 40, top + 110.0, -700.0), (xb - 40, top + 900.0, -150.0), m["euv"], beam)
    box("lp_mask", (xa - 60, top + 900.0, -800.0), (xb + 60, top + 950.0, 0.0), m["glass"], beam)
    edges = [xa] + [e for x in xs for e in (x - w / 2, x + w / 2)] + [xb]
    cut = group("lp_cut", g, [(F(0, 0.5), end)])
    for k in range(0, len(edges), 2):
        box(f"lp_gap{k}", (edges[k], base, zb), (edges[k + 1], top, -1.0), m["lowk"], cut)
    hm = group("lp_hm", g, [(F(0, 0.5), F(2, 0.35))])
    for k in range(0, len(edges), 2):
        box(f"lp_hm{k}", (edges[k], top, zb), (edges[k + 1], top + 40.0, 0.0), m["hm"], hm)
    lin = group("lp_lin", g, [(F(1, 0.08), end)])
    for k, x in enumerate(xs):
        box(f"lp_tan{k}", (x - w / 2, base, zb), (x + w / 2, top, 1.0), m["tan"], lin)
        box(f"lp_co{k}", (x - w / 2 + B, base + B, zb), (x + w / 2 - B, top + 0.5, 1.5), m["co"], lin)
        at = (x, base + B + L, 0.0)
        pv = grow(f"lp_grow{k}", at, lin, F(1, 0.25), F(1, 0.75))
        box(f"lp_cu{k}", rel(at, (x - w / 2 + B + L, base + B + L, zb)), rel(at, (x + w / 2 - B - L, top + 1.0, 2.0)), m["cu"], pv)
    over = group("lp_over", g, [(F(1, 0.75), F(2, 0.35))])
    box("lp_blanket", (xa, top + 40.0, zb), (xb, top + 150.0, 2.0), m["cu"], over)
    for k, x in enumerate(xs):
        box(f"lp_ofill{k}", (x - w / 2 + B + L, top, zb), (x + w / 2 - B - L, top + 41.0, 2.0), m["cu"], over)
    pad = group("lp_pad", g, [(F(2, 0.0), F(2, 0.42))])
    padm = empty("lp_padm", pad)
    box("lp_padb", (xa - 500, top + 150.0, -800.0), (xa - 100, top + 260.0, 0.0), m["base"], padm)
    fly(padm, [(0.0, 0.0, 0.0), (1460.0, 0.0, 0.0)], F(2, 0.02), F(2, 0.40), steps=6)
    capg = group("lp_cap", g, [(F(2, 0.45), end)])
    box("lp_capb", (xa, top + 1.0, zb), (xb, top + 31.0, 2.5), m["cap"], capg)
    nxt = group("lp_next", g, [(F(2, 0.62), end)])
    box("lp_ild2", (xa, top + 31.0, zb), (xb, top + 231.0, -1.0), m["lowk2"], nxt)
    lined("lp_via", (xs[1] - 60, top - 2.0, -110.0), (xs[1] + 60, top + 231.0, 0.0), B, m["tan"], m["cu"], nxt,
          liner=L, ml=m["co"], axis="y")
    for k, x in enumerate(xs):
        dots(g, m["sig"], f"lp_ions{k}", [(x, top + 520.0, 30.0), (x, base + 120.0, 30.0)], 1, 0.15 + 0.05 * k, 0.65, n=5, life=50, size=14.0)
    pins = dict(resist=(xs[2], top + 70.0, 3.0), light=(xa + 80, top + 600.0, -150.0), trench=(xs[1], top - 80.0, -200.0),
                hm=(edges[4] + 40.0, top + 20.0, 3.0), lin=(xs[0] - w / 2 + 6, base + 150.0, 3.0), core=(xs[1], base + 140.0, 3.0),
                over=(xs[2], top + 100.0, 3.0), pad=(0.0, top + 200.0, 0.0), cap=(xs[2] + 100, top + 16.0, 3.0),
                via=(xs[1], top + 130.0, 3.0))
    return pins, (xa, 0.0, zb), (xb, top + 260.0, 0.0), (xa, 0.0, zb), (xb, top + 950.0, 0.0)
