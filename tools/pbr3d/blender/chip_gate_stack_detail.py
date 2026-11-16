"""Detailed close-up rigs for the GATE STACK sections (chip_gate_stack.py sec1-sec10).

Each rig is a cut-away block on its own (no whole chip), drawn big enough to fill the left pane:

  rmg()     one replacement-metal-gate transistor in section: silicon, raised n+ source and
            drain, nitride spacers, ILD0 oxide, and the gate trench lined by U-shaped films
            (IL on the floor only, then HfO2, TiN cap, work-function metal, TiN barrier) round a
            tungsten fill. Also the dummy-poly and gate-first variants.
  eot_pair() two gate stacks side by side: SiO2 alone (left) and IL + HfO2 (right), at 40 mm/nm,
            for the tunnelling and EOT comparison.
  gaa()     a nanosheet stack cut across the sheets: each sheet wrapped by IL, HfO2 and the
            work-function metal, the tungsten fill round them.

Units are schematic millimetres, Y up, the cut face at z = 0 with the camera on +z. The films are
drawn far thicker than life next to the gate width (the text says so).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from sand_overview import F, P, box, empty, label, mat, show, tube  # noqa: E402
from sand_zooms import stream_of  # noqa: E402

DZ = 520.0  # how far every rig runs back from the cut face


def mats(m):
    m["d_il"] = mat("gsd_il", (0.78, 0.82, 0.88), rough=0.5)
    m["d_hfo2"] = mat("gsd_hfo2", (0.98, 0.84, 0.25), rough=0.35)
    m["d_sio2"] = mat("gsd_sio2", (0.88, 0.92, 1.0), rough=0.35)
    m["d_tin"] = mat("gsd_tin", (0.86, 0.64, 0.28), metal=0.9, rough=0.3)
    m["d_tialc"] = mat("gsd_tialc", (0.20, 0.36, 0.66), metal=0.7, rough=0.35)
    m["d_w"] = mat("gsd_w", (0.62, 0.64, 0.70), metal=0.9, rough=0.28)
    m["d_poly"] = mat("gsd_poly", (0.55, 0.36, 0.22), rough=0.65)
    m["d_spacer"] = mat("gsd_spacer", (0.36, 0.62, 0.58), rough=0.5)
    m["d_ild"] = mat("gsd_ild", (0.70, 0.76, 0.88), rough=0.5, alpha=0.55)
    m["d_si"] = mat("gsd_si", (0.66, 0.56, 0.40), rough=0.75)
    m["d_nplus"] = mat("gsd_nplus", (0.38, 0.55, 0.92), rough=0.55)
    m["d_dip_la"] = mat("gsd_dip_la", (0.80, 0.45, 1.0), emit=(0.75, 0.40, 1.0), strength=1.0)
    m["d_dip_al"] = mat("gsd_dip_al", (0.35, 1.0, 0.70), emit=(0.30, 1.0, 0.65), strength=1.0)
    m["d_heat"] = mat("gsd_heat", (1.0, 0.45, 0.15), emit=(1.0, 0.40, 0.10), strength=2.5, alpha=0.45)
    m["d_hot"] = mat("gsd_hot", (1.0, 0.25, 0.20), emit=(1.0, 0.20, 0.15), strength=3.5)
    m["d_void"] = mat("gsd_void", (0.02, 0.02, 0.03), rough=0.9)
    m["d_hl"] = mat("gsd_hl", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.2, alpha=0.30)
    m["d_elec"] = mat("gsd_elec", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=4.0)
    m["d_leak"] = mat("gsd_leak", (1.0, 0.40, 0.35), emit=(1.0, 0.35, 0.30), strength=4.0)
    m["d_phys"] = mat("gsd_phys", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.5)
    m["d_eot"] = mat("gsd_eot", (1.0, 0.55, 0.85), emit=(1.0, 0.50, 0.80), strength=2.5)
    m["d_slurry"] = mat("gsd_slurry", (0.85, 0.88, 0.95), emit=(0.80, 0.85, 1.0), strength=1.0, alpha=0.5)
    m["d_ald"] = mat("gsd_ald_b", (1.0, 0.92, 0.55), rough=0.35)
    m["d_chan"] = mat("gsd_chan", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.5)
    m["d_pplus"] = mat("gsd_pplus", (0.92, 0.50, 0.55), rough=0.55)
    m["d_field"] = mat("gsd_field", (1.0, 0.72, 0.35), emit=(1.0, 0.65, 0.25), strength=2.5)
    m["d_trk_e"] = mat("gsd_trk_e", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=0.8, alpha=0.30)
    m["d_trk_l"] = mat("gsd_trk_l", (1.0, 0.40, 0.35), emit=(1.0, 0.35, 0.30), strength=0.8, alpha=0.30)


def ivs_all(beats):
    return [(F(0, 0), F(beats, 0))]


def span(a, b):
    """From (beat, u) or beat a to (beat, u) or beat b."""
    a = a if isinstance(a, tuple) else (a, 0.0)
    b = b if isinstance(b, tuple) else (b, 0.0)
    return [(F(*a), F(*b))]


def part(name, lo, hi, m_, parent, ivs=None):
    """A box, in its own switched group when `ivs` is given."""
    if ivs is None:
        return box(name, lo, hi, m_, parent)
    g = empty(name + "_g", parent)
    box(name, lo, hi, m_, g)
    show(g, ivs)
    return g


def group(name, parent, ivs=None):
    g = empty(name, parent)
    if ivs is not None:
        show(g, ivs)
    return g


def arrow(name, a, b, r, m_, parent, head=2.6):
    """A shaft from `a` to `b` with a cone head at `b`."""
    A, B = P(*a), P(*b)
    d = B - A
    hl = min(d.length * 0.45, r * head * 2.2)
    shaft_end = B - d.normalized() * hl
    g = empty(name, parent)
    if (shaft_end - A).length > 1e-3:
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=r, depth=(shaft_end - A).length,
                                            location=(A + shaft_end) / 2)
        s = bpy.context.object
        s.name = name + "_shaft"
        s.rotation_mode = "QUATERNION"
        s.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
        s.data.materials.append(m_)
        s.parent = g
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=r * head, radius2=0.0, depth=hl,
                                    location=shaft_end + d.normalized() * hl / 2)
    c = bpy.context.object
    c.name = name + "_head"
    c.rotation_mode = "QUATERNION"
    c.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    c.data.materials.append(m_)
    c.parent = g
    return g


# ---- the replacement-metal-gate transistor ----------------------------------------------------

# (key, drawn thickness, material key, kind): "floor" lines the trench floor only, "u" lines the
# floor and both walls, "fill" takes what is left
FILMS = [
    ("il", 12.0, "d_il", "floor"),
    ("hk", 26.0, "d_hfo2", "u"),
    ("cap", 12.0, "d_tin", "u"),
    ("wfm", 24.0, "d_tialc", "u"),
    ("bar", 12.0, "d_tin", "u"),
    ("fill", None, "d_w", "fill"),
]
H = 400.0  # gate height (top of spacers, ILD0 and the polished fill)
SD_TOP = 34.0  # raised source/drain top


def films(dipole=False, wfm="d_tialc"):
    out = []
    for k, t, mk, kind in FILMS:
        if k == "wfm":
            mk = wfm
        out.append((k, t, mk, kind))
        if k == "hk" and dipole:
            out.append(("dip", 7.0, "d_dip_la", "u"))
    return out


def frame(parent, m, cx=0.0, wt=220.0, hw=600.0, ivs=None, ild=True, sd=None, sd_mat="d_nplus"):
    """The transistor round the gate: silicon, the n+ source and drain (raised epi plus a shallow
    extension), nitride spacers on the trench walls and ILD0 oxide outside them. `ild` and `sd`
    are True/False or intervals that switch the oxide and the source/drain."""
    g = group("frame", parent, ivs)
    box("si", (cx - hw, -330.0, -DZ), (cx + hw, 0.0, 0.0), m["d_si"], g)
    gs = g if sd in (None, True) else group("sd", g, sd)
    gi = g if ild is True else group("ild", g, ild) if ild else None
    for s in (-1, 1):
        a, b = cx + s * (wt + 44.0), cx + s * (hw - 70.0)
        box(f"sd{s}", (min(a, b), -190.0, -DZ), (max(a, b), SD_TOP, 2.0), m[sd_mat], gs)
        a2 = cx + s * (wt - 30.0)
        box(f"ext{s}", (min(a2, a), -55.0, -DZ), (max(a2, a), 0.6, 2.0), m[sd_mat], gs)
        sp0, sp1 = cx + s * wt, cx + s * (wt + 44.0)
        box(f"spacer{s}", (min(sp0, sp1), 0.0, -DZ), (max(sp0, sp1), H, 0.0), m["d_spacer"], g)
        if gi is not None:
            i0, i1 = cx + s * (wt + 44.0), cx + s * hw
            box(f"ild{s}", (min(i0, i1), SD_TOP, -DZ), (max(i0, i1), H, -1.0), m["d_ild"], gi)
    return g


def ushape(name, x0, x1, y0, top, t, m_, parent, zf):
    """A U of thickness t inside the span x0..x1 from floor y0 up to `top`."""
    box(name + "_floor", (x0, y0, -DZ), (x1, y0 + t, zf), m_, parent)
    box(name + "_l", (x0, y0 + t, -DZ), (x0 + t, top, zf), m_, parent)
    box(name + "_r", (x1 - t, y0 + t, -DZ), (x1, top, zf), m_, parent)


def trench(parent, m, cx=0.0, wt=220.0, on=None, stack=None, stair=0.0, top=H, pre="g"):
    """The gate films in the trench x = cx +- wt, floor at y = 0. `on[key]` switches a film (default
    always on); `stair` recesses each film's front face that much further than the one before, so
    a three-quarter view shows them as steps. Returns {key: (x0, x1, y0)} of each film's inner
    corner, for tags."""
    on = on or {}
    stack = stack or films()
    x0, x1, y0 = cx - wt, cx + wt, 0.0
    where = {}
    for i, (k, t, mk, kind) in enumerate(stack):
        g = group(f"{pre}_{k}", parent, on.get(k))
        zf = -stair * i
        where[k] = (x0, x1, y0)
        if kind == "floor":
            box(f"{pre}_{k}_b", (x0, y0, -DZ), (x1, y0 + t, zf), m[mk], g)
            y0 += t
        elif kind == "u":
            ushape(f"{pre}_{k}", x0, x1, y0, top, t, m[mk], g, zf)
            x0, x1, y0 = x0 + t, x1 - t, y0 + t
        else:
            box(f"{pre}_{k}_b", (x0, y0, -DZ), (x1, top, zf), m[mk], g)
    return where


def flat_stack(parent, m, cx=0.0, wt=220.0, on=None, cap_mat="d_poly", pre="f"):
    """Gate-first: the same films laid flat across the gate, then a polysilicon cap to the top."""
    on = on or {}
    y = 0.0
    for k, t, mk, kind in FILMS[:-1]:
        g = group(f"{pre}_{k}", parent, on.get(k))
        box(f"{pre}_{k}_b", (cx - wt, y, -DZ), (cx + wt, y + t, 0.0), m[mk], g)
        y += t
    g = group(f"{pre}_cap", parent, on.get("polycap"))
    box(f"{pre}_cap_b", (cx - wt, y, -DZ), (cx + wt, H, 0.0), m[cap_mat], g)
    return y


def dummy(parent, m, cx=0.0, wt=220.0, ivs=None, pre="d"):
    """The sacrificial gate: a thin SiO2 film and the polysilicon placeholder on it."""
    g = group(f"{pre}_dummy", parent, ivs)
    box(f"{pre}_dox", (cx - wt, 0.0, -DZ), (cx + wt, 10.0, 0.0), m["d_sio2"], g)
    box(f"{pre}_poly", (cx - wt, 10.0, -DZ), (cx + wt, H, 0.0), m["d_poly"], g)
    return g


def anneal(parent, m, cx=0.0, wt=220.0, hw=600.0, ivs=None, pre="an"):
    """The anneal glow on the source and drain only."""
    g = group(pre, parent, ivs)
    for s in (-1, 1):
        a, b = cx + s * (wt + 40.0), cx + s * (hw - 64.0)
        box(f"{pre}{s}", (min(a, b), -196.0, -DZ), (max(a, b), SD_TOP + 8.0, 8.0), m["d_heat"], g)
    return g


def arc(p0, p1, sag, n=10):
    """Points on a smooth arch from p0 to p1 that bows `sag` in y at its middle (negative: down)."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(tuple(p0[k] + (p1[k] - p0[k]) * t for k in range(3)))
        out[-1] = (out[-1][0], out[-1][1] + sag * math.sin(math.pi * t), out[-1][2])
    return out


def track(parent, name, pts, r, m_, ivs=None):
    """A faint segmented tube along `pts`, the path a stream of beads rides (a ball at each joint
    so it reads as one wire)."""
    g = group(name, parent, ivs)
    for k in range(len(pts) - 1):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, m_, g, 8)
        if k:
            from sand_overview import ball
            ball(f"{name}_j{k}", pts[k], r, m_, g, 8)
    return g


def path_run(parent, m, name, pts, n, b, u0, u1, life, bead="d_elec", trk="d_trk_e", size=9.0, r=None,
             ivs=None):
    """Beads riding a visible track: the track shows for `ivs` (default beat b), the beads launch
    between fractions u0 and u1 of beat b."""
    track(parent, name + "_trk", pts, r or size * 0.35, m[trk], ivs or span(b, b + 1))
    return electrons(parent, m, name, pts, n, b, u0, u1, life, bead, size)


def electrons(parent, m, name, pts, n, b, u0, u1, life, mat_key="d_elec", size=9.0):
    s = pts[0]
    path = [(p[0] - s[0], p[1] - s[1], p[2] - s[2]) for p in pts]
    return stream_of(parent, name, n, s, path, size, m[mat_key], b, u0, u1, life)


# ---- SiO2 versus HfO2 at the same capacitance ----------------------------------------------------

NM = 40.0  # drawn mm per nm in eot_pair
EOT_HW = 210.0  # each stack's half-width


def column(parent, m, cx, layers, pre, gate_h=170.0, si_h=170.0):
    """Silicon, then `layers` [(key, nm, mat)] and a metal gate on top. Returns the y of each
    layer's bottom and the gate's bottom."""
    g = empty(pre, parent)
    box(f"{pre}_si", (cx - EOT_HW, -si_h, -DZ * 0.6), (cx + EOT_HW, 0.0, 0.0), m["d_si"], g)
    y = 0.0
    ys = {}
    for k, nm, mk in layers:
        ys[k] = y
        box(f"{pre}_{k}", (cx - EOT_HW, y, -DZ * 0.6), (cx + EOT_HW, y + nm * NM, 0.0), m[mk], g)
        y += nm * NM
    ys["gate"] = y
    box(f"{pre}_gate", (cx - EOT_HW, y, -DZ * 0.6), (cx + EOT_HW, y + gate_h, 0.0), m["d_tin"], g)
    return ys


# ---- the nanosheet gate ------------------------------------------------------------------------

SHEET_HW = 190.0
SHEET_T = 56.0
RING = [("il", 9.0, "d_il"), ("hk", 20.0, "d_hfo2"), ("wfm", 24.0, "d_tialc")]
FILL_GAP = 34.0  # tungsten left between two wrapped sheets
PITCH = SHEET_T + 2 * sum(t for _, t, _ in RING) + FILL_GAP


def ring(name, x0, y0, x1, y1, t, m_, parent, zf=0.0):
    """A rectangular ring of thickness t round the box x0..x1, y0..y1."""
    box(name + "_t", (x0 - t, y1, -DZ), (x1 + t, y1 + t, zf), m_, parent)
    box(name + "_b", (x0 - t, y0 - t, -DZ), (x1 + t, y0, zf), m_, parent)
    box(name + "_l", (x0 - t, y0, -DZ), (x0, y1, zf), m_, parent)
    box(name + "_r", (x1, y0, -DZ), (x1 + t, y1, zf), m_, parent)


def gaa(parent, m, cx=0.0, wfm="d_tialc", on=None, pre="n", thin=None, base_y=0.0):
    """Three sheets over a silicon base, each wrapped by the RING films, inside a tungsten fill.
    `thin`, a sheet index, draws that sheet's work-function ring thinner (a thickness spread).
    Returns the sheets' (y0, y1) and the outer extent."""
    on = on or {}
    g = empty(pre + "_gaa", parent)
    wrap = sum(t for _, t, _ in RING)
    y = base_y + wrap + FILL_GAP * 0.6
    sheets = []
    for i in range(3):
        sheets.append((y, y + SHEET_T))
        y += PITCH
    top = sheets[-1][1] + wrap + FILL_GAP * 0.8
    side = SHEET_HW + wrap + FILL_GAP
    box(f"{pre}_base", (cx - side - 60, base_y - 220.0, -DZ), (cx + side + 60, base_y, 0.0), m["d_si"], g)
    box(f"{pre}_fill", (cx - side, base_y, -DZ), (cx + side, top, -6.0), m["d_w"], g)
    for i, (s0, s1) in enumerate(sheets):
        box(f"{pre}_sheet{i}", (cx - SHEET_HW, s0, -DZ), (cx + SHEET_HW, s1, 0.0), m["d_si"], g)
        x0, x1, y0, y1 = cx - SHEET_HW, cx + SHEET_HW, s0, s1
        for k, t, mk in RING:
            if k == "wfm" and thin == i:
                t = t * 0.3
            mk = wfm if k == "wfm" else mk
            rg = group(f"{pre}_s{i}_{k}", g, on.get(k))
            ring(f"{pre}_s{i}_{k}r", x0, y0, x1, y1, t, m[mk], rg, -1.0 if k == "wfm" else 0.0)
            x0, x1, y0, y1 = x0 - t, x1 + t, y0 - t, y1 + t
    return sheets, (cx - side, base_y - 220.0, cx + side, top)


def gaa_side(parent, m, sheets, pre="side", gl=170.0):
    """The same three sheets cut along the channel: each sheet runs from the n+ source epi to the
    drain epi, the gate (HfO2 lining, work-function metal, W) fills the gaps over the middle `gl`
    either side of x = 0, and nitride inner spacers sit between gate and epi."""
    g = empty(pre, parent)
    wrap = sum(t for _, t, _ in RING)
    top = sheets[-1][1] + wrap + 20.0
    box(f"{pre}_base", (-620.0, -220.0, -DZ), (620.0, 0.0, 0.0), m["d_si"], g)
    for s_ in (-1, 1):
        a, b = s_ * (gl + 40.0), s_ * 560.0
        box(f"{pre}_epi{s_}", (min(a, b), 0.0, -DZ), (max(a, b), top, 0.0), m["d_nplus"], g)
    gaps = [(0.0, sheets[0][0])] + [(sheets[i][1], sheets[i + 1][0]) for i in range(2)] + [(sheets[-1][1], top)]
    for k, (y0, y1) in enumerate(gaps):
        box(f"{pre}_hk{k}", (-gl, y0, -DZ), (gl, y1, -1.0), m["d_hfo2"], g)
        box(f"{pre}_wfm{k}", (-gl, y0 + 10.0, -DZ), (gl, y1 - 10.0, 0.0), m["d_tialc"], g)
        for s_ in (-1, 1):
            a, b = s_ * gl, s_ * (gl + 40.0)
            box(f"{pre}_isp{k}{s_}", (min(a, b), y0, -DZ), (max(a, b), y1, 0.0), m["d_spacer"], g)
    for i, (s0, s1) in enumerate(sheets):
        box(f"{pre}_sheet{i}", (-gl - 40.0, s0, -DZ), (gl + 40.0, s1, 1.0), m["d_si"], g)
    return g, top


def dipole_rings(parent, m, cx, sheets, mk, ivs, pre):
    """A thin dipole film at the IL/HfO2 interface round every sheet, just in front of the cut."""
    g = group(pre + "_dip", parent, ivs)
    il = RING[0][1]
    for i, (s0, s1) in enumerate(sheets):
        ring(f"{pre}_dip{i}", cx - SHEET_HW - il, s0 - il, cx + SHEET_HW + il, s1 + il, 6.0, m[mk], g, 3.0)
    return g


__all__ = [
    "mats", "span", "part", "group", "arrow", "frame", "trench", "films", "flat_stack", "dummy",
    "electrons", "arc", "track", "path_run", "column", "gaa", "dipole_rings", "ring", "H", "SD_TOP", "NM", "EOT_HW", "DZ",
    "SHEET_HW", "SHEET_T", "RING", "label", "F", "box", "empty", "show", "tube", "math",
]
