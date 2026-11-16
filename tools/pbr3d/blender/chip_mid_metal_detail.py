"""Detailed interconnect parts for the CHIP tab's metal sections (MID METAL and TOP METAL).

The sections no longer replay the schematic whole-chip scene (chip_kit.py); each builds a cut-away
block of the actual wiring instead: copper lines in their tantalum-nitride barrier and Co/Ru liner,
vias down to the level below, the SiCN cap on every level and the low-k dielectric between the
lines. Lines on alternate levels run at right angles, so the cut face (z = 0, camera on +z) shows
one level as a row of copper cross-sections and the next as a long copper bar, the way a TEM
cross-section of a real stack looks.

Units are schematic (the mid pages read about 1 unit = 1 nm; the top page compresses more). The
barrier and liner are drawn a little thicker than life so they read at TUI size.

  mats(m)                 the materials, keys prefixed "d_"
  zline / xline / via     one copper line (into the page / along x) or via, with barrier + liner
  slab                    a dielectric, cap or any plain layer filling a band of the block
  tower(...)              a whole stack of levels from a list of specs; returns where it put things
  frame(...)              a camera pose that fills the left pane with a box
  cam(root, poses)        the section camera: chip_kit.focus_camera with one pose per beat
  heat_strip              a rail coloured by voltage drop, segment by segment
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, OFF, ball, box, empty, key, label, mat, show, tube  # noqa: E402
from sand_zooms import scale_keys, stream_of  # noqa: E402
import chip_kit as C  # noqa: E402

EPS = 0.8  # how far a part's front face stands proud of the one behind it (no z-fighting)


def mats(m):
    m["d_cu"] = mat("d_cu", (0.96, 0.56, 0.30), metal=0.6, rough=0.3)
    m["d_cu_dim"] = mat("d_cu_dim", (0.70, 0.42, 0.26), metal=0.7, rough=0.4)
    m["d_tan"] = mat("d_tan", (0.18, 0.20, 0.34), metal=0.6, rough=0.4)  # TaN/Ta barrier
    m["d_liner"] = mat("d_liner", (0.90, 0.92, 0.96), metal=0.7, rough=0.2)  # Co or Ru liner
    m["d_cap"] = mat("d_cap", (0.55, 0.80, 0.62), rough=0.45)  # SiCN / SiN cap
    m["d_lowk"] = mat("d_lowk", (0.46, 0.50, 0.68), rough=0.65)  # low-k / ULK (opaque: glass would refract the copper)
    m["d_sio2"] = mat("d_sio2", (0.80, 0.84, 0.95), rough=0.4)
    m["d_w"] = mat("d_w", (0.58, 0.60, 0.66), metal=0.9, rough=0.3)
    m["d_si"] = mat("d_si", (0.30, 0.33, 0.42), metal=0.3, rough=0.5)
    m["d_nplus"] = mat("d_nplus", (0.40, 0.55, 0.92), rough=0.55)
    m["d_pplus"] = mat("d_pplus", (0.92, 0.50, 0.50), rough=0.55)
    m["d_gate"] = mat("d_gate", (0.60, 0.62, 0.70), metal=0.8, rough=0.3)
    m["d_sin"] = mat("d_sin", (0.74, 0.70, 0.88), rough=0.45)  # SiN passivation
    m["d_pi"] = mat("d_pi", (0.85, 0.55, 0.15), rough=0.5, alpha=0.75)  # polyimide
    m["d_al"] = mat("d_al", (0.85, 0.87, 0.90), metal=0.9, rough=0.35)  # aluminium pad
    m["d_ubm"] = mat("d_ubm", (0.55, 0.58, 0.62), metal=0.8, rough=0.3)
    m["d_solder"] = mat("d_solder", (0.80, 0.82, 0.86), metal=0.75, rough=0.25)
    m["d_underfill"] = mat("d_underfill", (0.40, 0.42, 0.32), rough=0.6, alpha=0.55)
    m["d_subst"] = mat("d_subst", (0.18, 0.40, 0.26), rough=0.7)  # organic substrate
    m["d_void"] = mat("d_void", (0.02, 0.02, 0.03), rough=0.9)
    m["d_ru"] = mat("d_ru", (0.62, 0.74, 0.92), metal=0.9, rough=0.25)
    m["d_air"] = mat("d_air", (0.05, 0.06, 0.10), rough=0.9)
    m["d_pore"] = mat("d_pore", (0.10, 0.11, 0.18), rough=0.9)
    m["d_mask"] = mat("d_mask", (0.30, 0.30, 0.34), metal=0.5, rough=0.4)  # TiN hard mask
    m["d_damage"] = mat("d_damage", (0.38, 0.30, 0.42), rough=0.7)
    m["d_cocap"] = mat("d_cocap", (0.75, 0.85, 1.0), metal=0.6, rough=0.15, emit=(0.55, 0.70, 1.0), strength=1.2)
    # glows
    m["d_elec"] = mat("d_elec", (0.40, 0.80, 1.0), emit=(0.35, 0.75, 1.0), strength=3.5)
    m["d_atom"] = mat("d_atom", (1.0, 0.55, 0.20), emit=(1.0, 0.50, 0.15), strength=3.0)
    m["d_vdd"] = mat("d_vdd", (1.0, 0.62, 0.22), emit=(1.0, 0.58, 0.18), strength=3.5)
    m["d_vss"] = mat("d_vss", (0.42, 0.68, 1.0), emit=(0.40, 0.65, 1.0), strength=3.5)
    m["d_sig"] = mat("d_sig", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=3.5)
    m["d_clk"] = mat("d_clk", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=3.0)
    m["d_vdd_rail"] = mat("d_vdd_rail", (1.0, 0.45, 0.25), emit=(1.0, 0.40, 0.20), strength=1.0, alpha=0.40)
    m["d_vss_rail"] = mat("d_vss_rail", (0.35, 0.60, 1.0), emit=(0.30, 0.55, 1.0), strength=1.0, alpha=0.40)
    m["d_clk_lit"] = mat("d_clk_lit", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=1.2, alpha=0.45)
    m["d_hot"] = mat("d_hot", (1.0, 0.30, 0.10), emit=(1.0, 0.28, 0.08), strength=2.5, alpha=0.55)
    m["d_field"] = mat("d_field", (1.0, 0.92, 0.40), emit=(1.0, 0.90, 0.35), strength=2.5, alpha=0.6)
    m["d_bad"] = mat("d_bad", (1.0, 0.22, 0.22), emit=(1.0, 0.20, 0.20), strength=2.5, alpha=0.5)
    m["d_ok"] = mat("d_ok", (0.40, 1.0, 0.55), emit=(0.35, 1.0, 0.50), strength=2.0, alpha=0.45)
    m["d_plasma"] = mat("d_plasma", (0.80, 0.45, 1.0), emit=(0.75, 0.40, 1.0), strength=3.0, alpha=0.5)
    m["d_crack"] = mat("d_crack", (1.0, 0.25, 0.20), emit=(1.0, 0.20, 0.15), strength=3.0)
    for i, c in enumerate(((1.0, 0.92, 0.35), (1.0, 0.72, 0.25), (1.0, 0.50, 0.18), (1.0, 0.32, 0.12), (0.90, 0.12, 0.10))):
        m[f"d_heat{i}"] = mat(f"d_heat{i}", c, emit=c, strength=2.0, alpha=0.65)


# ---- parts ----------------------------------------------------------------------------------


def slab(name, x0, x1, y0, y1, z0, mt, g, front=-0.5):
    """A plain layer filling x0..x1, y0..y1, from z0 back to the cut plane (front just behind it)."""
    return box(name, (x0, y0, z0), (x1, y1, front), mt, g)


def zline(name, g, m, xc, y0, w, h, z0, bt=4.0, lt=2.5, metal="d_cu", z1=0.0, cu=True):
    """A damascene line running into the page: copper w x h with the liner and the barrier
    round its bottom and sides (the cap covers the top). Its cut face is at z1."""
    o = []
    if bt > 0:
        o.append(box(name + "_bar", (xc - w / 2 - lt - bt, y0 - lt - bt, z0), (xc + w / 2 + lt + bt, y0 + h, z1), m["d_tan"], g))
    if lt > 0:
        o.append(box(name + "_lin", (xc - w / 2 - lt, y0 - lt, z0 + 0.5), (xc + w / 2 + lt, y0 + h + 0.2, z1 + EPS / 2), m["d_liner"], g))
    if cu:
        o.append(box(name, (xc - w / 2, y0, z0 + 1.0), (xc + w / 2, y0 + h + 0.4, z1 + EPS), m[metal], g))
    return o


def xline(name, g, m, x0, x1, y0, h, zc, w, bt=4.0, lt=2.5, metal="d_cu", cut=True):
    """A line running along x at depth zc, w wide in z. With `cut` it is sliced by the cut plane
    (its front face at z = 0 shows copper, the barrier a strip along the bottom)."""
    zf = 0.0 if cut else zc + w / 2 + lt + bt
    o = []
    if bt > 0:
        o.append(box(name + "_bar", (x0 - lt - bt, y0 - lt - bt, zc - w / 2 - lt - bt), (x1 + lt + bt, y0 + h, zf), m["d_tan"], g))
    if lt > 0:
        o.append(box(name + "_lin", (x0 - lt, y0 - lt, zc - w / 2 - lt), (x1 + lt, y0 + h + 0.2, zf + EPS / 2), m["d_liner"], g))
    zf_cu = zf + EPS if cut else zc + w / 2
    o.append(box(name, (x0, y0, zc - w / 2), (x1, y0 + h + 0.4, zf_cu), m[metal], g))
    return o


def via(name, g, m, xc, zc, y0, y1, s, bt=4.0, lt=2.5, metal="d_cu", front=None, cu=True):
    """A square via, s wide, from y0 (the top of the line below) up to y1 (the bottom of the line
    above). The barrier and liner coat its sides only: at its foot copper meets copper."""
    zb = zc + s / 2 + lt + bt if front is None else front
    o = []
    if bt > 0:
        o.append(box(name + "_bar", (xc - s / 2 - lt - bt, y0 + 0.3, zc - s / 2 - lt - bt), (xc + s / 2 + lt + bt, y1, zb), m["d_tan"], g))
    if lt > 0:
        o.append(box(name + "_lin", (xc - s / 2 - lt, y0 + 0.3, zc - s / 2 - lt), (xc + s / 2 + lt, y1 + 0.2, zb + EPS / 2), m["d_liner"], g))
    if cu:
        o.append(box(name, (xc - s / 2, y0 - 0.5, zc - s / 2), (xc + s / 2, y1 + 0.5, zb + EPS), m[metal], g))
    return o


class Level:
    """One wiring level as tower() built it."""

    def __init__(self, name, y0, h, w, pitch, dir_, xs, zcs):
        self.name, self.y0, self.h, self.w, self.pitch, self.dir = name, y0, h, w, pitch, dir_
        self.y1 = y0 + h
        self.yc = y0 + h / 2
        self.xs = xs  # z-running lines: their x centres
        self.zcs = zcs  # x-running lines: their z centres, front first


def tower(g, m, specs, x0, x1, z0, y=0.0, cap=None, ild="d_lowk", vias=True, bt=None, lt=None, gap=None):
    """A stack of wiring levels, bottom first, between x0..x1 and z0..0. Each spec is a dict:
    name, h (line height), w (line width), pitch, dir ("z" into the page or "x" along it),
    and optionally gap (dielectric height under the level, where its vias are), metal, ild,
    via_at (indices of the lines, of whichever level runs into the page, that get a via down),
    bt and lt (barrier and liner thickness, default scaled with w), cap (cap thickness).
    Returns {name: Level}."""
    out = {}
    prev = None
    for li, s in enumerate(specs):
        name, h, w, pitch, d = s["name"], s["h"], s["w"], s["pitch"], s["dir"]
        sbt = s.get("bt", bt if bt is not None else max(2.0, 0.09 * w))
        slt = s.get("lt", lt if lt is not None else max(1.5, 0.06 * w))
        sgap = s.get("gap", gap if gap is not None else 0.8 * h)
        scap = s.get("cap", cap if cap is not None else max(4.0, 0.12 * h))
        metal = s.get("metal", "d_cu")
        sild = s.get("ild", ild)
        lg = empty(f"{name}_g", g)
        yl = y + (sgap if prev is not None else sbt + slt)
        # the dielectric of this level: from the cap below up to the top of the lines
        slab(f"{name}_ild", x0, x1, y, yl + h, z0, m[sild], lg)
        xs, zcs = [], []
        if d == "z":
            n = int((x1 - x0) // pitch)
            start = x0 + ((x1 - x0) - (n - 1) * pitch) / 2
            xs = [start + k * pitch for k in range(n)]
            for k, xc in enumerate(xs):
                zline(f"{name}_{k}", lg, m, xc, yl, w, h, z0 + 2, sbt, slt, metal)
        else:
            # the front line, on the cut face, is broken into wires; the ones behind run through
            if "segs" in s:
                segs = s["segs"]
            elif s.get("full"):
                segs = [(x0 + 2, x1 - 2)]
            else:
                f = (0.42, 0.64, 0.30, 0.55)[li % 4]
                cut_x = x0 + f * (x1 - x0)
                half = 0.6 * w + sbt + slt
                segs = [(x0 + 2, cut_x - half), (cut_x + half, x1 - 2)]
            zc = -w * 0.35
            k = 0
            while zc - w / 2 - sbt - slt > z0 + 2:
                zcs.append(zc)
                if k == 0:
                    for j, (a, b) in enumerate(segs):
                        xline(f"{name}_{k}_{j}", lg, m, a, b, yl, h, zc, w, sbt, slt, metal, cut=True)
                else:
                    xline(f"{name}_{k}", lg, m, x0 + 2, x1 - 2, yl, h, zc, w, sbt, slt, metal, cut=False)
                zc -= pitch
                k += 1
        lev = Level(name, yl, h, w, pitch, d, xs, zcs)
        lev.segs = segs if d == "x" else []
        lev.bt, lev.lt, lev.g, lev.metal = sbt, slt, lg, metal
        # vias down to the level below, where a line into the page crosses a front wire
        lev.vias_at = []
        if prev is not None and vias:
            zl = prev if prev.dir == "z" else lev  # the level that runs into the page
            xl = lev if zl is prev else prev  # the one along x
            if zl.dir == "z" and xl.dir == "x":
                sv = s.get("via_w", 0.62 * min(prev.w, w))
                if "via_at" in s:
                    at = [zl.xs[k] for k in s["via_at"] if k < len(zl.xs)]
                else:
                    cand = [x for x in zl.xs if any(a + sv < x < b - sv for a, b in xl.segs)]
                    n = len(cand)
                    at = sorted({cand[(li * 2) % n], cand[(li * 2 + n // 2) % n]}) if n else []
                for j, xv in enumerate(at):
                    via(f"{name}_v{j}", lg, m, xv, -sv / 2 - 0.5, prev.y1, yl, sv, sbt, slt, metal, front=0.0)
                lev.vias_at = at
                lev.via_w = sv
        # the cap on top
        slab(f"{name}_cap", x0, x1, yl + h + 0.4, yl + h + scap, z0, m[s.get("capm", "d_cap")], lg, front=-0.3)
        lev.cap_top = yl + h + scap
        y = yl + h + scap
        out[name] = lev
        prev = lev
    out["_top"] = y
    return out


def transistors(g, m, x0, x1, z0, y_top=0.0, pitch=60.0, gate_w=18.0, h_si=120.0):
    """Silicon with a row of gates and source/drain contacts in tungsten, as a base for a tower."""
    slab("si", x0, x1, y_top - h_si, y_top, z0, m["d_si"], g)
    n = int((x1 - x0) // pitch)
    start = x0 + ((x1 - x0) - (n - 1) * pitch) / 2
    for k in range(n):
        xc = start + k * pitch
        box(f"sd{k}", (xc - pitch / 2 + gate_w / 2 + 3, y_top - 14, z0 + 2), (xc + pitch / 2 - gate_w / 2 - 3, y_top + 2, 0.4),
            m["d_nplus" if k % 4 < 2 else "d_pplus"], g)
        box(f"gate{k}", (xc - gate_w / 2, y_top, z0 + 2), (xc + gate_w / 2, y_top + 30, 0.6), m["d_gate"], g)
    return [start + k * pitch for k in range(n)]


def heat_strip(g, m, name, x0, x1, y0, y1, z0, z1, n=5, reverse=False):
    """An overlay band split into n segments coloured from yellow (full voltage) to red."""
    for i in range(n):
        a = x0 + (x1 - x0) * i / n
        b = x0 + (x1 - x0) * (i + 1) / n
        k = (n - 1 - i) if reverse else i
        box(f"{name}{i}", (a, y0, z0), (b, y1, z1), m[f"d_heat{min(4, round(k * 4 / max(1, n - 1)))}"], g)


def grow(name, parent, at, build, keys, until=None):
    """A pivot at `at` whose children (built by build(pivot) in pivot-relative coordinates) scale
    by `keys` [(frame, s)], s uniform or (x, y, z) in Blender axes."""
    from sand_overview import pivot
    p = pivot(name, at, parent)
    build(p)
    scale_keys(p, keys, until=until)
    return p


def dots(root, name, pts, n, size, mt, b, u0, u1, life):
    s = pts[0]
    path = [(p[0] - s[0], p[1] - s[1], p[2] - s[2]) for p in pts]
    return stream_of(root, name, n, s, path, size, mt, b, u0, u1, life)


def run(parent, name, pts, n, size, mt, b, u0, u1, life):
    """`n` beads that each ride the absolute polyline `pts` over `life` frames, launched one after
    another between fractions u0 and u1 of beat `b` (as fiber_photodiode_detail.run): enough
    keys per corner that they follow the wire round every bend."""
    from sand_overview import fly
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, mt, e, 12)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, len(pts) * 3))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


def span(b0, b1=None):
    b1 = b0 if b1 is None else b1
    return [(F(b0, 0), F(b1 + 1, 0))]


def group(name, parent, intervals):
    """An empty switched on for `intervals`; build the parts under it."""
    e = empty(name, parent)
    show(e, intervals)
    return e


# ---- camera ---------------------------------------------------------------------------------

PANE_H = 0.48  # visible height / distance (measured off page_sheet frames)
PANE_W = 0.55  # visible width / distance in the left pane


def frame(x0, y0, x1, y1, yaw=0.30, pitch=0.20, pad=1.08, zc=-30.0):
    """The pose that fills the left pane with the box x0..x1, y0..y1 (on the cut face)."""
    w, h = abs(x1 - x0), abs(y1 - y0)
    dist = max(h / PANE_H, w / PANE_W) * pad
    return (((x0 + x1) / 2, (y0 + y1) / 2, zc), dist, yaw, pitch)


def cam(root, poses):
    """The section camera: chip_kit.focus_camera with every beat's pose given (the parts here are
    not the whole chip, so the auto framing has nothing to measure against). Beat 0 opens a
    little wider and glides in."""
    C.BASE.clear()
    t, d, yaw, pitch = poses[0]
    C.focus_camera(root, beats=len(poses), lead=(t, d * 1.35, yaw + 0.12, pitch + 0.05), over=dict(enumerate(poses)))


__all__ = ["mats", "slab", "zline", "xline", "via", "tower", "transistors", "heat_strip", "grow", "dots", "span",
           "group", "frame", "cam", "label", "box", "ball", "tube", "empty", "show", "key", "F", "OFF", "scale_keys", "math"]
