"""Detailed transistor builders for the NMOS and PMOS sections (chip_nmos.py, chip_pmos.py).

The two pages are mirror images, so one module draws both: `kind` "n" is an NMOS (n+ source and
drain in a p-well, electrons), "p" a PMOS (SiGe:B source and drain in an n-well, holes).

  planar()   one transistor in cut-away (the cut plane is z = 0, the camera on +z): p-substrate,
             the well, STI walls at both ends, the deep source and drain, the shallow extensions
             and halo pockets, raised epitaxy with a silicide cap, nitride spacers, and the
             replacement-metal gate (interfacial SiO2, a U of high-k, a U of work-function metal,
             the fill metal, a nitride cap), with tungsten contacts on the silicide. Parts are
             named in `Dev.parts` so sections can light them; the carriers, channel, depletion
             and field are separate pieces switched on per beat.
  finfet()   fins cut across the gate (the cut plane is x = 0, seen three-quarter from -x): the
             gate wraps each fin's top and both sides.
  gaa()      stacked nanosheets cut across the gate, the gate all round each sheet.
  layout()   a standard cell seen from above (drawn in the xy plane, so the front camera sees it).
  array()    rows of gates over active strips: many transistors, top-down.

Units are schematic millimetres as on the rest of the Chip tab (the device is about 900 wide),
Y up. Carriers ride at z = +CZ, just in front of the cut face.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, ball, box, empty, label, mat, show, tube  # noqa: E402
from sand_zooms import stream_of  # noqa: E402

CZ = 14.0  # carriers ride this far in front of the cut face


def beats(a, b=None):
    """Beats a up to b (a alone: that one beat) as one interval list."""
    return [(F(a, 0), F(a + 1 if b is None else b, 0))]


def mats(m):
    """The detail materials, all named mos_*; added to m under the same keys."""
    new = {
        "mos_sub": mat("mos_sub", (0.46, 0.37, 0.24), rough=0.85),
        "mos_pwell": mat("mos_pwell", (0.68, 0.55, 0.34), rough=0.8),
        "mos_nwell": mat("mos_nwell", (0.36, 0.44, 0.62), rough=0.8),
        "mos_n_sd": mat("mos_n_sd", (0.20, 0.42, 0.95), rough=0.6),
        "mos_n_epi": mat("mos_n_epi", (0.42, 0.68, 1.0), rough=0.55),
        "mos_p_sd": mat("mos_p_sd", (0.90, 0.36, 0.46), rough=0.6),
        "mos_p_epi": mat("mos_p_epi", (1.0, 0.60, 0.36), rough=0.55),
        "mos_n_halo": mat("mos_n_halo", (0.55, 0.62, 0.95), rough=0.7),
        "mos_p_halo": mat("mos_p_halo", (0.86, 0.50, 0.32), rough=0.7),
        "mos_sti": mat("mos_sti", (0.84, 0.88, 0.94), rough=0.35),
        "mos_il": mat("mos_il", (0.98, 0.98, 1.0), rough=0.3),
        "mos_hik": mat("mos_hik", (0.20, 0.85, 0.72), rough=0.35),
        "mos_n_wfm": mat("mos_n_wfm", (0.78, 0.70, 0.42), metal=0.8, rough=0.3),
        "mos_p_wfm": mat("mos_p_wfm", (0.92, 0.62, 0.28), metal=0.8, rough=0.3),
        "mos_fill": mat("mos_fill", (0.58, 0.60, 0.68), metal=0.85, rough=0.28),
        "mos_sin": mat("mos_sin", (0.50, 0.70, 0.55), rough=0.6),
        "mos_silicide": mat("mos_silicide", (0.22, 0.22, 0.27), metal=0.7, rough=0.35),
        "mos_w": mat("mos_w", (0.74, 0.75, 0.80), metal=0.9, rough=0.25),
        "mos_cu": mat("mos_cu", (0.88, 0.52, 0.30), metal=0.85, rough=0.3),
        "mos_si": mat("mos_si", (0.66, 0.68, 0.74), metal=0.2, rough=0.45),
        "mos_sige": mat("mos_sige", (0.95, 0.55, 0.40), rough=0.5),
        "mos_ge": mat("mos_ge", (0.25, 0.85, 0.75), emit=(0.25, 0.85, 0.75), strength=0.8),
        # glows and overlays
        "mos_gate_on": mat("mos_gate_on", (1.0, 0.70, 0.30), emit=(1.0, 0.62, 0.22), strength=2.2, alpha=0.55),
        "mos_gate_half": mat("mos_gate_half", (1.0, 0.70, 0.30), emit=(1.0, 0.62, 0.22), strength=0.9, alpha=0.35),
        "mos_n_chan": mat("mos_n_chan", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=3.0, alpha=0.9),
        "mos_n_chan_weak": mat("mos_n_chan_weak", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.2, alpha=0.4),
        "mos_p_chan": mat("mos_p_chan", (1.0, 0.62, 0.20), emit=(1.0, 0.58, 0.18), strength=3.0, alpha=0.9),
        "mos_p_chan_weak": mat("mos_p_chan_weak", (1.0, 0.62, 0.20), emit=(1.0, 0.58, 0.18), strength=1.2, alpha=0.4),
        "mos_dep": mat("mos_dep", (0.72, 0.45, 1.0), emit=(0.65, 0.40, 1.0), strength=0.9, alpha=0.38),
        "mos_line": mat("mos_line", (1.0, 0.92, 0.45), emit=(1.0, 0.88, 0.35), strength=4.0),
        "mos_hl": mat("mos_hl", (1.0, 0.95, 0.55), emit=(1.0, 0.92, 0.45), strength=1.2, alpha=0.30),
        "mos_warn": mat("mos_warn", (1.0, 0.30, 0.28), emit=(1.0, 0.25, 0.22), strength=1.6, alpha=0.38),
        "mos_elec": mat("mos_elec", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=4.0),
        "mos_hole": mat("mos_hole", (1.0, 0.62, 0.20), emit=(1.0, 0.58, 0.18), strength=4.0),
        "mos_leak": mat("mos_leak", (0.70, 0.35, 1.0), emit=(0.65, 0.30, 1.0), strength=2.5),
        "mos_field": mat("mos_field", (1.0, 0.45, 0.80), emit=(1.0, 0.40, 0.78), strength=3.0),
        "mos_strain": mat("mos_strain", (1.0, 0.88, 0.35), emit=(1.0, 0.85, 0.30), strength=3.0),
        "mos_atom_n": mat("mos_atom_n", (1.0, 0.95, 0.55), emit=(1.0, 0.92, 0.45), strength=3.0),
        "mos_atom_b": mat("mos_atom_b", (0.95, 0.95, 1.0), emit=(0.9, 0.9, 1.0), strength=3.0),
        "mos_grid": mat("mos_grid", (0.60, 0.80, 1.0), emit=(0.55, 0.78, 1.0), strength=2.0),
        "mos_hot": mat("mos_hot", (1.0, 0.35, 0.25), emit=(1.0, 0.30, 0.20), strength=4.0),
        "mos_vdd": mat("mos_vdd", (1.0, 0.35, 0.30), emit=(1.0, 0.30, 0.25), strength=1.5),
        "mos_gnd": mat("mos_gnd", (0.35, 0.55, 1.0), emit=(0.30, 0.50, 1.0), strength=1.5),
        "mos_poly": mat("mos_poly", (0.55, 0.58, 0.66), metal=0.6, rough=0.35),
        "mos_cell": mat("mos_cell", (1.0, 0.95, 0.55), emit=(1.0, 0.92, 0.45), strength=2.5),
        "mos_tap": mat("mos_tap", (0.55, 1.0, 0.60), emit=(0.50, 1.0, 0.55), strength=1.5),
    }
    m.update(new)
    return m


def carrier(kind):
    """The carrier material key: electrons for an NMOS, holes for a PMOS."""
    return "mos_elec" if kind == "n" else "mos_hole"


def majority(kind):
    """The body's majority carrier: holes in an NMOS's p-well, electrons in a PMOS's n-well."""
    return "mos_hole" if kind == "n" else "mos_elec"


# ---- the planar transistor in cut-away -----------------------------------------------------

class Dev:
    """Where a planar() transistor's parts are, for the pieces and highlights placed on it."""

    def __init__(self, kind, cx, half, sd_out, gh, depth, name):
        self.kind, self.cx, self.half, self.sd_out, self.gh, self.depth, self.name = kind, cx, half, sd_out, gh, depth, name
        self.sp = gh + 38  # spacer outer edge
        self.sd_in = gh + 45  # deep source/drain inner edge
        self.ext_in = gh - 10  # extensions reach just under the gate edge
        self.ytop = 190.0  # top of the gate cap
        self.epi_top = 42.0
        self.sil_top = 54.0
        self.ct_top = 340.0
        self.ct_x = (sd_out + self.sp) / 2  # contact centre, from cx
        self.parts = {}  # name -> (lo, hi)

    def x(self, dx):
        return self.cx + dx

    def src(self, sign):
        """x of the source (sign -1, left) or drain (+1) contact."""
        return self.cx + sign * self.ct_x


def planar(m, root, kind="n", cx=0.0, name=None, half=440.0, sd_out=360.0, gh=55.0, depth=360.0,
           iv=None, tap=False, contacts=True, ct_top=None):
    """One planar transistor in cut-away, centred at x = cx; shown for `iv` (always if None)."""
    name = name or f"{kind}mos"
    d = Dev(kind, cx, half, sd_out, gh, depth, name)
    if ct_top is not None:
        d.ct_top = ct_top
    g = empty(name, root)
    Z = -depth
    n = kind == "n"
    well = m["mos_pwell"] if n else m["mos_nwell"]
    sd = m["mos_n_sd"] if n else m["mos_p_sd"]
    epi = m["mos_n_epi"] if n else m["mos_p_epi"]
    halo = m["mos_p_halo"] if n else m["mos_n_halo"]
    wfm = m["mos_n_wfm"] if n else m["mos_p_wfm"]
    xr = half + (130.0 if tap else 0.0)

    def part(key_, lo, hi, mt):
        box(f"{name}_{key_}", lo, hi, mt, g)
        d.parts.setdefault(key_, (lo, hi))

    # silicon: substrate below, the well above it (z fronts stepped back so the cut faces don't fight)
    part("sub", (cx - half, -320, Z), (cx + xr, -230, -3.5), m["mos_sub"])
    part("well", (cx - half, -230, Z), (cx + xr, 0, -3.0), well)
    for s in (-1, 1):
        xo = cx + s * half
        lo, hi = (min(xo, xo - s * 70), -210, Z), (max(xo, xo - s * 70), 2.0, -1.0)
        part(f"sti{s}", lo, hi, m["mos_sti"])
    if tap:  # a well tap past the right-hand STI: n+ in an n-well (PMOS), p+ in a p-well (NMOS)
        part("tap", (cx + half + 20, -100, Z), (cx + half + 110, 1.5, 0.0), m["mos_n_sd"] if not n else m["mos_p_sd"])
        part("tap_sil", (cx + half + 25, 1.5, Z), (cx + half + 105, 14, 0.0), m["mos_silicide"])
        part("tap_ct", (cx + half + 40, 14, -200), (cx + half + 90, d.ct_top, 0.0), m["mos_w"])
    for s in (-1, 1):
        a, b = cx + s * d.sd_in, cx + s * sd_out
        part(f"sd{s}", (min(a, b), -115, Z), (max(a, b), 1.5, 0.0), sd)
        a, b = cx + s * d.ext_in, cx + s * d.sd_in
        part(f"ext{s}", (min(a, b), -34, Z), (max(a, b), 1.0, 0.0), sd)
        a, b = cx + s * (d.ext_in - 8), cx + s * (d.sd_in + 15)
        part(f"halo{s}", (min(a, b), -72, Z), (max(a, b), -34, -1.5), halo)
        a, b = cx + s * (d.sp + 4), cx + s * (sd_out - 10)
        part(f"epi{s}", (min(a, b), 1.5, Z), (max(a, b), d.epi_top, 0.0), epi)
        a, b = cx + s * (d.sp + 12), cx + s * (sd_out - 18)
        part(f"sil{s}", (min(a, b), d.epi_top, Z), (max(a, b), d.sil_top, 0.0), m["mos_silicide"])
        a, b = cx + s * gh, cx + s * d.sp
        part(f"spacer{s}", (min(a, b), 0, Z), (max(a, b), d.ytop, 0.0), m["mos_sin"])
        if contacts:
            xc = cx + s * d.ct_x
            part(f"ct{s}", (xc - 30, d.sil_top, -0.6 * depth), (xc + 30, d.ct_top, 0.0), m["mos_w"])
    # the replacement-metal gate: SiO2, a U of high-k, a U of work-function metal, the fill, a cap
    part("il", (cx - gh, 0, Z), (cx + gh, 6, 0.0), m["mos_il"])
    part("hik_b", (cx - gh, 6, Z), (cx + gh, 17, 0.0), m["mos_hik"])
    part("hik_l", (cx - gh, 17, Z), (cx - gh + 9, 165, 0.0), m["mos_hik"])
    part("hik_r", (cx + gh - 9, 17, Z), (cx + gh, 165, 0.0), m["mos_hik"])
    part("wfm_b", (cx - gh + 9, 17, Z), (cx + gh - 9, 31, 0.0), wfm)
    part("wfm_l", (cx - gh + 9, 31, Z), (cx - gh + 21, 165, 0.0), wfm)
    part("wfm_r", (cx + gh - 21, 31, Z), (cx + gh - 9, 165, 0.0), wfm)
    part("fill", (cx - gh + 21, 31, Z), (cx + gh - 21, 165, 0.0), m["mos_fill"])
    part("cap", (cx - gh, 165, Z), (cx + gh, d.ytop, 0.0), m["mos_sin"])
    d.parts["gate"] = ((cx - gh, 0, Z), (cx + gh, d.ytop, 0.0))
    d.parts["stack"] = ((cx - gh, 0, Z), (cx + gh, 165, 0.0))
    left = ((cx - sd_out, -115, Z), (cx - d.ext_in, d.sil_top, 0.0))
    right = ((cx + d.ext_in, -115, Z), (cx + sd_out, d.sil_top, 0.0))
    # an NMOS's source is on the left (ground side), a PMOS's on the right (VDD side)
    d.parts["source"], d.parts["drain"] = (left, right) if n else (right, left)
    d.parts["body"] = ((cx - half, -320, Z), (cx + xr, 0, 0.0))
    d.parts["chan"] = ((cx - d.ext_in, -14, Z), (cx + d.ext_in, 0, 0.0))
    if iv is not None:
        show(g, iv)
    d.group = g
    return d


def hl(root, m, d, key_, iv, name=None, pad=8.0, mt="mos_line", t=5.0):
    """A glowing outline round one of `d`'s parts on the cut face (its colour stays visible);
    mt="mos_warn" tints the part red instead."""
    (x0, y0, z0), (x1, y1, z1) = d.parts[key_]
    nm = name or f"{d.name}_hl_{key_}"
    if mt != "mos_line":
        return box_on(root, nm, (x0 - pad, y0 - pad, z0), (x1 + pad, y1 + pad, z1 + 3.0), m[mt], iv)
    return outline(root, m, nm, (x0 - pad, y0 - pad), (x1 + pad, y1 + pad), iv, t=t)


def outline(root, m, name, lo, hi, iv, t=5.0, z=4.0, mt="mos_line"):
    """A glowing rectangle (lo..hi in x, y) just in front of the cut face."""
    g = empty(name + "_g", root)
    (x0, y0), (x1, y1) = lo, hi
    for i, (a, b) in enumerate((((x0 - t, y0 - t), (x1 + t, y0)), ((x0 - t, y1), (x1 + t, y1 + t)),
                                ((x0 - t, y0), (x0, y1)), ((x1, y0), (x1 + t, y1)))):
        box(f"{name}_{i}", (a[0], a[1], z - 3), (b[0], b[1], z), m[mt], g)
    show(g, iv)
    return g


def box_on(root, name, lo, hi, mt, iv):
    g = empty(name + "_g", root)
    box(name, lo, hi, mt, g)
    show(g, iv)
    return g


def gate_glow(root, m, d, iv, weak=False, name=None):
    """The gate metal lit amber: the gate is driven high."""
    cx, gh = d.cx, d.gh
    return box_on(root, name or f"{d.name}_gate_on", (cx - gh + 4, 12, -d.depth), (cx + gh - 4, 168, 2.5),
                  m["mos_gate_half" if weak else "mos_gate_on"], iv)


def channel(root, m, d, iv, weak=False, x0=None, x1=None, name=None, thick=16.0):
    """The inversion layer on the silicon surface under the gate, from x0 to x1 (offsets)."""
    k = ("mos_n_chan" if d.kind == "n" else "mos_p_chan") + ("_weak" if weak else "")
    a = d.cx + (-d.ext_in if x0 is None else x0)
    b = d.cx + (d.ext_in if x1 is None else x1)
    return box_on(root, name or f"{d.name}_chan", (a, -thick, -d.depth), (b, -0.5, 2.0), m[k], iv)


def pinch(root, m, d, iv, name=None, thin=False):
    """A saturated channel: full depth at the source, thinning, gone short of the drain.
    `thin`: the step before, the channel reaching the drain but thinning toward it."""
    g = empty(name or f"{d.name}_pinch", root)
    k = "mos_n_chan" if d.kind == "n" else "mos_p_chan"
    sign = -1 if d.kind == "n" else 1  # the source side the carriers come from
    if thin:
        steps = [(-d.ext_in, -0.2 * d.ext_in, 16.0), (-0.2 * d.ext_in, 0.5 * d.ext_in, 11.0),
                 (0.5 * d.ext_in, d.ext_in, 6.0)]
    else:
        steps = [(-d.ext_in, -0.35 * d.ext_in, 16.0), (-0.35 * d.ext_in, 0.15 * d.ext_in, 11.0),
                 (0.15 * d.ext_in, 0.5 * d.ext_in, 6.0)]
    for i, (a, b, t) in enumerate(steps):
        a, b = sorted((d.cx + sign * -a, d.cx + sign * -b))
        box(f"{g.name}_{i}", (a, -t, -d.depth), (b, -0.5, 2.0), m[k], g)
    show(g, iv)
    return g


def depletion(root, m, d, iv, under_gate=True, junctions=True, deep=80.0, reach=0.0, name=None):
    """The depletion region: under the gate (`deep` down) and round the source and drain
    junctions. `reach` stretches the drain-side region toward the source (DIBL)."""
    g = empty(name or f"{d.name}_dep", root)
    cx, Z = d.cx, -d.depth
    if under_gate:
        box(f"{g.name}_gate", (cx - d.ext_in, -deep, Z), (cx + d.ext_in, -16.5, 1.2), m["mos_dep"], g)
    if junctions:
        for s in (-1, 1):
            xi, xo = cx + s * d.sd_in, cx + s * d.sd_out
            box(f"{g.name}_bot{s}", (min(xi, xo) - 18, -140, Z), (max(xi, xo) + 2, -116, 1.0), m["mos_dep"], g)
            a, b = cx + s * (d.ext_in - 22), cx + s * d.sd_in
            box(f"{g.name}_side{s}", (min(a, b), -116, Z), (max(a, b), -74, 1.0), m["mos_dep"], g)
    if reach:
        box(f"{g.name}_reach", (cx + d.ext_in - reach, -118, Z), (cx + d.ext_in + 10, -18, 1.4), m["mos_dep"], g)
    show(g, iv)
    return g


def flow(root, m, d, b, name=None, n=10, u0=0.04, u1=0.72, life=110, size=10.0, from_sign=None, y=-8.0,
         mt=None, contacts=True):
    """Carriers in beat b: down the source contact, along the channel, up the drain contact.
    An NMOS's electrons come from the left (source, ground); a PMOS's holes from the right
    unless `from_sign` says otherwise."""
    s = from_sign if from_sign is not None else (-1 if d.kind == "n" else 1)
    xa, xb = d.cx + s * d.ct_x, d.cx - s * d.ct_x
    if contacts:
        pts = [(xa, d.ct_top - 30, CZ), (xa, y, CZ), (xb, y, CZ), (xb, d.ct_top - 30, CZ)]
    else:
        pts = [(xa, y, CZ), (xb, y, CZ)]
    st = pts[0]
    path = [(p[0] - st[0], p[1] - st[1], p[2] - st[2]) for p in pts]
    return stream_of(root, name or f"{d.name}_flow{b}", n, st, path, size, m[mt or carrier(d.kind)], b, u0, u1, life)


def leak(root, m, d, b, name=None, n=6, y=-52.0, life=150, u0=0.05, u1=0.75, size=8.0):
    """Off-state leakage: a few faint carriers under the surface, source to drain."""
    s = -1 if d.kind == "n" else 1
    st = (d.cx + s * (d.sd_in + 20), y, CZ)
    path = [(0, 0, 0), (-s * 2 * (d.sd_in + 20), 0, 0)]
    return stream_of(root, name or f"{d.name}_leak{b}", n, st, path, size, m["mos_leak"], b, u0, u1, life)


def majority_dots(root, m, d, iv_far, iv_gate, name=None):
    """The body's majority carriers sitting in the well: `iv_far` for the ones away from the
    gate, `iv_gate` for the ones under it (a gate voltage pushes those away)."""
    nm = name or f"{d.name}_maj"
    far, near = empty(nm + "_far", root), empty(nm + "_gate", root)
    mt = m[majority(d.kind)]
    k = 0
    for yi, y in enumerate((-36.0, -88.0, -150.0, -200.0)):
        for xi in range(-6, 7):
            x = xi * 66.0 + (33.0 if yi % 2 else 0.0)
            if abs(x) > d.half - 85:
                continue
            if y > -125 and d.sd_in - 12 < abs(x) < d.sd_out + 12:
                continue  # inside the source or drain
            if y > -40 and abs(x) > d.ext_in - 5:
                continue  # inside the extensions
            under = abs(x) < d.ext_in + 15 and y > -100
            ball(f"{nm}{k}", (d.cx + x, y, CZ - 4), 7.0, mt, near if under else far, 8)
            k += 1
    show(far, iv_far)
    show(near, iv_gate)
    return far, near


def arrows(root, m, name, segs, iv, mt="mos_field", r=4.0, tip=11.0):
    """Arrows (tail, head) with ball tips."""
    g = empty(name, root)
    for i, (a, b) in enumerate(segs):
        tube(f"{name}{i}", a, b, r, m[mt], g, verts=8)
        ball(f"{name}{i}_tip", b, tip, m[mt], g, 8)
    show(g, iv)
    return g


def field(root, m, d, iv, name=None):
    """The gate's field: arrows down through the dielectric into the channel."""
    segs = [((d.cx + dx, 150, CZ + 6), (d.cx + dx, -30, CZ + 6)) for dx in (-0.6 * d.gh, 0.0, 0.6 * d.gh)]
    return arrows(root, m, name or f"{d.name}_field", segs, iv)


def strain(root, m, d, iv, name=None):
    """Strain arrows along the channel: outward (tensile) for an NMOS, inward (compressive)
    for a PMOS, pressing from the source and drain."""
    segs = []
    for s in (-1, 1):
        for y in (-22.0, -60.0):
            if d.kind == "n":
                segs.append(((d.cx + s * 20, y, CZ + 6), (d.cx + s * (d.sd_in + 60), y, CZ + 6)))
            else:
                segs.append(((d.cx + s * (d.sd_in + 70), y, CZ + 6), (d.cx + s * 30, y, CZ + 6)))
    return arrows(root, m, name or f"{d.name}_strain", segs, iv, mt="mos_strain", r=6.0, tip=14.0)


def dopants(root, m, d, iv, name=None, kind_atom=None):
    """Dopant atoms dotted through the source, drain and their raised epitaxy."""
    g = empty(name or f"{d.name}_atoms", root)
    mt = m[kind_atom or ("mos_atom_n" if d.kind == "n" else "mos_atom_b")]
    k = 0
    for s in (-1, 1):
        for yi, y in enumerate((-95.0, -60.0, -22.0, 22.0)):
            for f in (0.15, 0.4, 0.65, 0.9):
                x = d.sd_in + (d.sd_out - d.sd_in) * f + (12 if yi % 2 else -12)
                ball(f"{g.name}{k}", (d.cx + s * x, y, CZ - 6), 7.0, mt, g, 8)
                k += 1
    show(g, iv)
    return g


def gate_leak(root, m, d, b, name=None):
    """Carriers tunnelling up through the gate dielectric (gate leakage) in beat b."""
    st = (d.cx - 15, -6, CZ)
    return stream_of(root, name or f"{d.name}_gleak{b}", 5, st, [(0, 0, 0), (0, 60, 0)], 7.0, m["mos_leak"], b, 0.1, 0.8, 70)


# ---- FinFET and GAA, cut across the gate (the cut plane is x = 0) -----------------------------

FIN_W, FIN_H = 44.0, 150.0
GATE_L = 70.0  # gate length (x) beyond the cut


def finfet(m, root, kind="n", nfins=2, z0=0.0, pitch=130.0, name=None, iv=None, length=360.0, lit=None):
    """Fins along x, cut at x = 0 across the gate. The cut face shows each fin wrapped by
    high-k and the gate on its top and two sides; past the gate (x > GATE_L + spacer) the
    raised source/drain epitaxy grows round the fins. `lit`: intervals for the channel glow on
    each fin's three faces. Returns (group, fin centres z, extent)."""
    name = name or f"fin_{kind}"
    g = empty(name, root)
    n = kind == "n"
    zs = [z0 + (i - (nfins - 1) / 2) * pitch for i in range(nfins)]
    zl, zh = zs[0] - pitch / 2 - 30, zs[-1] + pitch / 2 + 30
    L = length
    wfm = m["mos_n_wfm"] if n else m["mos_p_wfm"]
    epi = m["mos_n_epi"] if n else m["mos_p_epi"]
    box(f"{name}_sub", (0, -170, zl), (L, -40, zh), m["mos_sub"], g)
    box(f"{name}_well", (0, -40, zl), (L, -38, zh), m["mos_pwell"] if n else m["mos_nwell"], g)
    # STI between the fins, up to y = 0
    edges = [zl] + [e for zc in zs for e in (zc - FIN_W / 2, zc + FIN_W / 2)] + [zh]
    for i in range(0, len(edges), 2):
        box(f"{name}_sti{i}", (0, -38, edges[i]), (L, 0, edges[i + 1]), m["mos_sti"], g)
    hk, wf = 7.0, 9.0
    top = FIN_H + 60
    for i, zc in enumerate(zs):
        a, b = zc - FIN_W / 2, zc + FIN_W / 2
        box(f"{name}_fin{i}", (0, -38, a), (L, FIN_H, b), m["mos_si"], g)
        # high-k and work-function metal round the fin's top and sides, inside the gate
        box(f"{name}_hk_t{i}", (0, FIN_H, a - hk), (GATE_L, FIN_H + hk, b + hk), m["mos_hik"], g)
        box(f"{name}_hk_l{i}", (0, 0, a - hk), (GATE_L, FIN_H, a), m["mos_hik"], g)
        box(f"{name}_hk_r{i}", (0, 0, b), (GATE_L, FIN_H, b + hk), m["mos_hik"], g)
        box(f"{name}_wf_t{i}", (0, FIN_H + hk, a - hk - wf), (GATE_L, FIN_H + hk + wf, b + hk + wf), wfm, g)
        box(f"{name}_wf_l{i}", (0, 0, a - hk - wf), (GATE_L, FIN_H + hk, a - hk), wfm, g)
        box(f"{name}_wf_r{i}", (0, 0, b + hk), (GATE_L, FIN_H + hk, b + hk + wf), wfm, g)
        box(f"{name}_fill_t{i}", (0, FIN_H + hk + wf, a - hk - wf), (GATE_L, top, b + hk + wf), m["mos_fill"], g)
        # the epitaxy round the fin past the spacer
        box(f"{name}_epi{i}", (GATE_L + 40, -2, a - 30), (L, FIN_H + 30, b + 30), epi, g)
        box(f"{name}_epis{i}", (GATE_L + 50, FIN_H + 30, a - 18), (L - 10, FIN_H + 42, b + 18), m["mos_silicide"], g)
    # gate fill between and beside the fins
    for i in range(0, len(edges), 2):
        lo_z, hi_z = edges[i], edges[i + 1]
        if i > 0:
            lo_z += hk + wf
        if i < len(edges) - 2:
            hi_z -= hk + wf
        box(f"{name}_fill{i}", (0, 0, lo_z), (GATE_L, top, hi_z), m["mos_fill"], g)
    box(f"{name}_cap", (0, top, zl), (GATE_L, top + 26, zh), m["mos_sin"], g)
    box(f"{name}_spacer", (GATE_L, 0, zl), (GATE_L + 40, top + 26, zh), m["mos_sin"], g)
    if lit:
        cg = empty(f"{name}_chan", root)
        k = m["mos_n_chan" if n else "mos_p_chan"]
        for i, zc in enumerate(zs):
            a, b = zc - FIN_W / 2, zc + FIN_W / 2
            box(f"{name}_ct{i}", (-2.5, FIN_H - 10, a - 1), (GATE_L, FIN_H + 1, b + 1), k, cg)
            box(f"{name}_cl{i}", (-2.5, 4, a - 1), (GATE_L, FIN_H, a + 9), k, cg)
            box(f"{name}_cr{i}", (-2.5, 4, b - 9), (GATE_L, FIN_H, b + 1), k, cg)
        show(cg, lit)
    if iv is not None:
        show(g, iv)
    return g, zs, ((0, -170, zl), (L, top + 26, zh))


SHEET_T, SHEET_W, SHEET_Y = 30.0, 150.0, (30.0, 92.0, 154.0)


def gaa(m, root, kind="p", name=None, iv=None, sheet_ivs=None, lit=None, length=360.0, z0=0.0):
    """Three stacked nanosheets along x, cut at x = 0 across the gate: high-k and gate metal all
    round each sheet. `sheet_ivs`: {material key: intervals} to swap the sheet material by beat
    (silicon, SiGe, germanium); default silicon throughout. Returns (group, extent)."""
    name = name or f"gaa_{kind}"
    g = empty(name, root)
    n = kind == "n"
    L = length
    zl, zh = z0 - SHEET_W / 2 - 90, z0 + SHEET_W / 2 + 90
    a, b = z0 - SHEET_W / 2, z0 + SHEET_W / 2
    wfm = m["mos_n_wfm"] if n else m["mos_p_wfm"]
    epi = m["mos_n_epi"] if n else m["mos_p_epi"]
    top = SHEET_Y[-1] + SHEET_T + 60
    box(f"{name}_sub", (0, -170, zl), (L, -40, zh), m["mos_sub"], g)
    box(f"{name}_sti", (0, -40, zl), (L, 0, zh), m["mos_sti"], g)
    hk, wf = 6.0, 8.0
    sheets = sheet_ivs or {"mos_si": None}
    for mk, siv in sheets.items():
        sg = empty(f"{name}_sheets_{mk}", g)
        for j, y0 in enumerate(SHEET_Y):
            box(f"{name}_{mk}_{j}", (0, y0, a), (L, y0 + SHEET_T, b), m[mk], sg)
        if siv is not None:
            show(sg, siv)
    for j, y0 in enumerate(SHEET_Y):
        y1 = y0 + SHEET_T
        box(f"{name}_hk_b{j}", (0, y0 - hk, a - hk), (GATE_L, y0, b + hk), m["mos_hik"], g)
        box(f"{name}_hk_t{j}", (0, y1, a - hk), (GATE_L, y1 + hk, b + hk), m["mos_hik"], g)
        box(f"{name}_hk_l{j}", (0, y0, a - hk), (GATE_L, y1, a), m["mos_hik"], g)
        box(f"{name}_hk_r{j}", (0, y0, b), (GATE_L, y1, b + hk), m["mos_hik"], g)
        box(f"{name}_wf_b{j}", (0, y0 - hk - wf, a - hk - wf), (GATE_L, y0 - hk, b + hk + wf), wfm, g)
        box(f"{name}_wf_t{j}", (0, y1 + hk, a - hk - wf), (GATE_L, y1 + hk + wf, b + hk + wf), wfm, g)
        box(f"{name}_wf_l{j}", (0, y0 - hk, a - hk - wf), (GATE_L, y1 + hk, a - hk), wfm, g)
        box(f"{name}_wf_r{j}", (0, y0 - hk, b + hk), (GATE_L, y1 + hk, b + hk + wf), wfm, g)
    e = hk + wf
    box(f"{name}_fill_l", (0, 0, zl), (GATE_L, top, a - e), m["mos_fill"], g)
    box(f"{name}_fill_r", (0, 0, b + e), (GATE_L, top, zh), m["mos_fill"], g)
    ys = [0.0] + [v for y0 in SHEET_Y for v in (y0 - e, y0 + SHEET_T + e)] + [top]
    for i in range(0, len(ys), 2):
        if ys[i + 1] > ys[i]:
            box(f"{name}_fill_m{i}", (0, ys[i], a - e), (GATE_L, ys[i + 1], b + e), m["mos_fill"], g)
    box(f"{name}_cap", (0, top, zl), (GATE_L, top + 24, zh), m["mos_sin"], g)
    box(f"{name}_spacer", (GATE_L, 0, zl), (GATE_L + 40, top + 24, zh), m["mos_sin"], g)
    box(f"{name}_epi", (GATE_L + 40, 0, a - 40), (L, SHEET_Y[-1] + SHEET_T + 30, b + 40), epi, g)
    box(f"{name}_epis", (GATE_L + 50, SHEET_Y[-1] + SHEET_T + 30, a - 30), (L - 10, SHEET_Y[-1] + SHEET_T + 42, b + 30),
        m["mos_silicide"], g)
    if lit:
        cg = empty(f"{name}_chan", root)
        k = m["mos_n_chan" if n else "mos_p_chan"]
        for j, y0 in enumerate(SHEET_Y):
            y1 = y0 + SHEET_T
            box(f"{name}_cb{j}", (-2.5, y0 - 1, a - 1), (GATE_L, y0 + 7, b + 1), k, cg)
            box(f"{name}_ct{j}", (-2.5, y1 - 7, a - 1), (GATE_L, y1 + 1, b + 1), k, cg)
            box(f"{name}_cl{j}", (-2.5, y0, a - 1), (GATE_L, y1, a + 7), k, cg)
            box(f"{name}_cr{j}", (-2.5, y0, b - 7), (GATE_L, y1, b + 1), k, cg)
        show(cg, lit)
    if iv is not None:
        show(g, iv)
    return g, ((0, -170, zl), (L, top + 24, zh))


# ---- top-down: standard cells and arrays (drawn in the xy plane, seen from the front) -----------

def cell(m, root, x0, name, w=420.0, h=600.0, flip=False, tap=False, iv=None):
    """One standard cell, seen from above, lower-left corner at (x0, 0) (or flipped upside
    down, sharing the rail below): VDD rail on top, n-well and PMOS active (pink) in the top
    half, NMOS active (blue) below, two gates running down through both, contacts and the M1
    output strap. A tap cell instead holds the n+ and p+ taps that tie the wells to the rails."""
    g = empty(name, root)

    def Y(y):
        return (h - y) if flip else y

    def rect(tag, xa, ya, xb, yb, mt, z):
        y0, y1 = sorted((Y(ya), Y(yb)))
        box(f"{name}_{tag}", (x0 + xa, y0, z - 6), (x0 + xb, y1, z), mt, g)

    rect("pw", 0, 0, w, h / 2, m["mos_pwell"], 0)
    rect("nw", 0, h / 2, w, h, m["mos_nwell"], 0)
    rect("vdd", 0, h - 40, w, h + 40, m["mos_vdd"], 30)
    rect("gnd", 0, -40, w, 40, m["mos_gnd"], 30)
    if tap:
        rect("ntap", 120, h - 150, w - 120, h - 70, m["mos_n_sd"], 8)
        rect("ptap", 120, 70, w - 120, 150, m["mos_p_sd"], 8)
        for i, (xa, ya) in enumerate(((w / 2 - 25, h - 135), (w / 2 - 25, 85))):
            rect(f"tct{i}", xa, ya, xa + 50, ya + 50, m["mos_w"], 16)
        rect("tst", w / 2 - 15, h - 110, w / 2 + 15, h - 40, m["mos_w"], 14)
        rect("tsb", w / 2 - 15, 40, w / 2 + 15, 110, m["mos_w"], 14)
    else:
        rect("pact", 50, h / 2 + 50, w - 50, h - 80, m["mos_p_sd"], 8)
        rect("nact", 50, 80, w - 50, h / 2 - 70, m["mos_n_sd"], 8)
        for i, gx in enumerate((w * 0.33, w * 0.67)):
            rect(f"gate{i}", gx - 18, 50, gx + 18, h - 50, m["mos_poly"], 14)
        for i, (cxr, lo, hi) in enumerate(((0.12, h / 2 + 70, h - 100), (0.5, h / 2 + 70, h - 100), (0.88, h / 2 + 70, h - 100),
                                           (0.12, 100, h / 2 - 90), (0.5, 100, h / 2 - 90), (0.88, 100, h / 2 - 90))):
            rect(f"ct{i}", w * cxr - 20, lo, w * cxr + 20, hi, m["mos_w"], 18)
        rect("m1o", w * 0.5 - 14, 120, w * 0.5 + 14, h - 120, m["mos_cu"], 24)
        rect("m1v", w * 0.12 - 14, h - 110, w * 0.12 + 14, h, m["mos_cu"], 24)
        rect("m1g", w * 0.12 - 14, 0, w * 0.12 + 14, 110, m["mos_cu"], 24)
        rect("m1v2", w * 0.88 - 14, h - 110, w * 0.88 + 14, h, m["mos_cu"], 24)
        rect("m1g2", w * 0.88 - 14, 0, w * 0.88 + 14, 110, m["mos_cu"], 24)
    if iv is not None:
        show(g, iv)
    return g


def array(m, root, name, cols=24, rows=3, pitch=90.0, row_h=520.0, iv=None, wires_iv=None):
    """Many transistors from above: rows of active strips (pink PMOS over blue NMOS), gate lines
    every `pitch` crossing them, and (for `wires_iv`) copper M1/M2 straps over the top."""
    g = empty(name, root)
    W = cols * pitch
    for r in range(rows):
        y = r * row_h
        box(f"{name}_n{r}", (0, y + 40, -10), (W, y + 200, -2), m["mos_n_sd"], g)
        box(f"{name}_p{r}", (0, y + 270, -10), (W, y + 450, -2), m["mos_p_sd"], g)
        box(f"{name}_nw{r}", (0, y + 235, -16), (W, y + row_h - 10, -10), m["mos_nwell"], g)
        box(f"{name}_pw{r}", (0, y - 10, -16), (W, y + 235, -10), m["mos_pwell"], g)
    for c in range(cols):
        x = (c + 0.5) * pitch
        box(f"{name}_g{c}", (x - 14, -10, -2), (x + 14, rows * row_h - 20, 6), m["mos_poly"], g)
    if iv is not None:
        show(g, iv)
    if wires_iv is not None:
        w = empty(name + "_wires", root)
        for r in range(rows * 2):
            y = r * row_h / 2 + 120
            box(f"{name}_m1_{r}", (0, y - 12, 14), (W, y + 12, 26), m["mos_cu"], w)
        for c in range(0, cols, 3):
            x = (c + 1.0) * pitch
            box(f"{name}_m2_{c}", (x - 12, -10, 30), (x + 12, rows * row_h - 20, 42), m["mos_cu"], w)
        show(w, wires_iv)
    return g


# ---- wires and beads ------------------------------------------------------------------------------

def arch(a, b, h, n=10):
    """Points on an arch from a to b, rising `h` above the straight line at its middle."""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(tuple(a[k] + (b[k] - a[k]) * t + (h * math.sin(math.pi * t) if k == 1 else 0.0) for k in range(3)))
    return pts


def wire(name, pts, r, mt, parent, iv=None):
    """A wire through `pts`: a tube per segment, a ball at each joint so it reads as one piece."""
    g = empty(name, parent)
    for k in range(len(pts) - 1):
        tube(f"{name}_{k}", pts[k], pts[k + 1], r, mt, g, 8)
        if k:
            ball(f"{name}_j{k}", pts[k], r, mt, g, 8)
    if iv is not None:
        show(g, iv)
    return g


def beads(parent, name, pts, n, size, mt, b, u0, u1, life):
    """`n` glowing beads that each ride the absolute polyline `pts` over `life` frames, launched
    one after another between fractions u0 and u1 of beat `b`."""
    from sand_overview import fly
    g = empty(name, parent)
    path = [tuple(p[i] - pts[0][i] for i in range(3)) for p in pts]
    for k in range(n):
        e = empty(f"{name}{k}", g)
        ball(f"{name}{k}_s", pts[0], size, mt, e, 10)
        f0 = F(b, u0 + (u1 - u0) * k / max(1, n - 1))
        f1 = f0 + life
        fly(e, path, f0, f1, steps=max(4, len(pts) * 2))
        show(e, [(f0, min(f1, F(b + 1, 0)))])
    return g


def carrier_path(d, from_sign=None, y=-8.0, up=0.0):
    """The carriers' route through a planar device (contact, channel, contact), `up` beyond
    the contact tops."""
    s = from_sign if from_sign is not None else (-1 if d.kind == "n" else 1)
    xa, xb = d.cx + s * d.ct_x, d.cx - s * d.ct_x
    return [(xa, d.ct_top + up, CZ), (xa, y, CZ), (xb, y, CZ), (xb, d.ct_top + up, CZ)]


def meter(root, m, name, x, y0, levels, label_text=None, w=60.0, hmax=300.0):
    """A current gauge beside a device: one glowing bar per beat, `levels` (0..1) high, on a dark
    back plate. A log-scale picture of the drain current."""
    plate = empty(name + "_plate", root)
    box(f"{name}_back", (x - w / 2 - 10, y0 - 10, -30), (x + w / 2 + 10, y0 + hmax + 10, -20), m["mos_silicide"], plate)
    for i in range(1, 6):
        yy = y0 + hmax * i / 6
        box(f"{name}_tick{i}", (x - w / 2 - 10, yy - 1.5, -20), (x - w / 2 + 6, yy + 1.5, -18), m["mos_w"], plate)
    for b, lv in enumerate(levels):
        h = max(6.0, hmax * lv)
        g = empty(f"{name}_bar{b}", root)
        box(f"{name}_b{b}", (x - w / 2, y0, -20), (x + w / 2, y0 + h, -10), m["mos_line"], g)
        show(g, [(F(b, 0), F(b + 1, 0))])
    return plate


# ---- pairs and rows ---------------------------------------------------------------------------

PAIR_X = 380.0  # the NMOS at -PAIR_X, the PMOS at +PAIR_X
PAIR_KW = dict(half=300.0, sd_out=250.0, gh=45.0, depth=300.0)


def inverter(m, root, iv, name="inv", wires=True, depth_n=None, depth_p=None):
    """The CMOS inverter in cut-away: an NMOS (left, source to ground at the far left) and a
    PMOS (right, source to VDD at the far right), gates tied to the input, drains tied to the
    output. Returns (nmos Dev, pmos Dev, extent)."""
    kn = dict(PAIR_KW, depth=depth_n or PAIR_KW["depth"])
    kp = dict(PAIR_KW, depth=depth_p or PAIR_KW["depth"])
    dn = planar(m, root, "n", -PAIR_X, name=f"{name}_n", iv=iv, **kn)
    dp = planar(m, root, "p", PAIR_X, name=f"{name}_p", iv=iv, **kp)
    top = dn.ct_top
    if wires:
        g = empty(f"{name}_wires", root)
        xd_n, xd_p = dn.src(1), dp.src(-1)  # the drains face each other
        box(f"{name}_out", (xd_n - 30, top, -120), (xd_p + 30, top + 34, 0), m["mos_cu"], g)
        for i, d in enumerate((dn, dp)):  # the gate contacts, up to the input bar
            box(f"{name}_gct{i}", (d.cx - 22, d.ytop, -0.6 * d.depth), (d.cx + 22, top + 110, -0.6 * d.depth + 50), m["mos_w"], g)
        box(f"{name}_in", (dn.cx - 40, top + 110, -0.6 * dn.depth), (dp.cx + 40, top + 144, -0.6 * dn.depth + 60), m["mos_cu"], g)
        box(f"{name}_gnd", (dn.src(-1) - 60, top, -120), (dn.src(-1) + 40, top + 34, 0), m["mos_gnd"], g)
        box(f"{name}_vdd", (dp.src(1) - 40, top, -120), (dp.src(1) + 60, top + 34, 0), m["mos_vdd"], g)
        show(g, iv)
    lo = (dn.cx - dn.half, -240.0, -40.0)
    hi = (dp.cx + dp.half, top + (150 if wires else 0), 0.0)
    return dn, dp, (lo, hi)


ROW_Z = (-430.0, 0.0, 430.0)


def makers_row(m, root, kind, iv, name="row"):
    """Three leading-edge transistors side by side, cut across the gate: a FinFET and two
    gate-all-around nanosheet stacks (z ascending is left to right from the row camera)."""
    a, _, ea = finfet(m, root, kind, nfins=2, z0=ROW_Z[0], name=f"{name}_fin", iv=iv, length=300.0)
    b, eb = gaa(m, root, kind, name=f"{name}_gaa1", iv=iv, length=300.0, z0=ROW_Z[1])
    c, ec = gaa(m, root, kind, name=f"{name}_gaa2", iv=iv, length=300.0, z0=ROW_Z[2])
    return (ea[0], ec[1])


ROW_YAW, ROW_PITCH = -1.05, 0.22


def row_pose(e):
    """The camera on makers_row(): three-quarter from -x, so the three cut faces read left to right."""
    return frame((e[0][0], e[0][1], e[0][2]), (60.0, e[1][1], e[1][2]), yaw=ROW_YAW, pitch=ROW_PITCH, pad=1.04)


# ---- in the whole chip ------------------------------------------------------------------------

def in_chip(m, root, **lit):
    """The whole chip (chip_kit) with its two plain transistors and their plugs swapped for the
    detailed NMOS (at NMOS_X) and PMOS (at PMOS_X), whose own contacts reach the first metal.
    Returns (nmos Dev, pmos Dev)."""
    import chip_kit as C
    parts = C.chip(root, m, **lit)
    for k in ("nmos", "pmos", "contacts"):
        show(parts[k], [])
    top = C.level_y("thin", 0)
    dn = planar(m, root, "n", C.NMOS_X, name="chip_n", ct_top=top)
    dp = planar(m, root, "p", C.PMOS_X, name="chip_p", ct_top=top)
    return dn, dp


# ---- camera ---------------------------------------------------------------------------------

def frame(lo, hi, yaw=0.0, pitch=0.12, pad=1.12):
    """A pose that fits the box lo..hi (x, y, z) in the left pane (about 1.14 wide per 1 high,
    vertical field 0.52 rad) from (yaw, pitch): the corners are projected through the real
    perspective, the distance found by bisection, and the target shifted so the box is centred."""
    tv = math.tan(0.26) / pad
    th = tv * 1.137
    cp, sp = math.cos(pitch), math.sin(pitch)
    fwd = (cp * math.sin(yaw), sp, cp * math.cos(yaw))
    right = (math.cos(yaw), 0.0, -math.sin(yaw))
    up = (-sp * math.sin(yaw), cp, -sp * math.cos(yaw))
    corners = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]

    def dot(a, b):
        return sum(a[i] * b[i] for i in range(3))

    def spans(c, dist):
        xs, ys = [], []
        for q in corners:
            v = [q[i] - c[i] for i in range(3)]
            depth = dist - dot(v, fwd)
            xs.append(dot(v, right) / depth)
            ys.append(dot(v, up) / depth)
        return min(xs), max(xs), min(ys), max(ys)

    dist = 1000.0
    for _ in range(3):
        a, b = 10.0, 40000.0
        for _ in range(60):
            mid = (a + b) / 2
            x0, x1, y0, y1 = spans(c, mid)
            if max(-x0, x1) <= th and max(-y0, y1) <= tv:
                b = mid
            else:
                a = mid
        dist = b
        x0, x1, y0, y1 = spans(c, dist)
        sx, sy = (x0 + x1) / 2 * dist, (y0 + y1) / 2 * dist
        c = [c[i] + right[i] * sx + up[i] * sy for i in range(3)]
    return (tuple(c), dist, yaw, pitch)


def frame_dev(d, top=None, bottom=-260.0, pad=1.08, pitch=0.12, yaw=0.0, x0=None, x1=None):
    """The front pose that fills the pane with a planar device (its cut face)."""
    a = d.cx - d.half if x0 is None else x0
    b = d.cx + d.half if x1 is None else x1
    return frame((a, bottom, -40.0), (b, d.ct_top if top is None else top, 0.0), yaw=yaw, pitch=pitch, pad=pad)


__all__ = ["beats", "mats", "planar", "hl", "outline", "box_on", "gate_glow", "channel", "pinch", "depletion", "flow",
           "leak", "majority_dots", "arrows", "field", "strain", "dopants", "gate_leak", "finfet", "gaa",
           "cell", "array", "in_chip", "arch", "wire", "beads", "carrier_path", "meter", "inverter", "makers_row", "ROW_Z", "ROW_YAW", "ROW_PITCH", "row_pose", "PAIR_X", "frame", "frame_dev", "label", "F", "CZ"]
