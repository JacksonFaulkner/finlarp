"""Detailed parts for the TOP METAL page's numbered sections (chip_top_metal.py, sec1-sec10).

Built on the wiring kit in chip_mid_metal_detail.py (copper in barrier and liner, vias, caps,
low-k, all cut away at z = 0 with the camera on +z). Here:

  top_block    M10-M14 in cut-away: M10-M11 fine, M12 wider, M13 a thick rail along the page,
               M14 the thickest stripes into the page, alternating VDD and VSS, a via stack at x = 0
  top_cap      the finish on top: vias up to an Al bond pad, SiN and polyimide with an opening,
               the UBM, a C4 solder bump (cut in half); optionally an RDL trace that moves the
               bump off the pad, the underfill and the package substrate above
  full_tower   one narrow column from transistors and tungsten contacts through M1-M14 to the bump
  c4 / pillars / hybrid   the three die-to-package joints at one scale (1 unit = 0.1 um)
  bspdn_column a front-side or backside power-delivery column, for section 6

Scales are schematic: the bump is drawn far smaller than life next to the wiring.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chip_mid_metal_detail as D  # noqa: E402
from chip_mid_metal_detail import EPS, box, empty, group, slab, span, tower, via, zline  # noqa: E402
from sand_overview import P, ball, cut, key, F  # noqa: E402

X0, X1, Z0 = -1000.0, 1000.0, -460.0

TOP_SPECS = [
    dict(name="M10", h=60.0, w=36.0, pitch=80.0, dir="z", bt=5.0, lt=3.0),
    dict(name="M11", h=60.0, w=36.0, pitch=80.0, dir="x", gap=50.0, bt=5.0, lt=3.0, via_at=[12]),
    dict(name="M12", h=110.0, w=70.0, pitch=180.0, dir="z", gap=80.0, bt=6.0, lt=4.0, via_at=[5]),
    dict(name="M13", h=200.0, w=150.0, pitch=330.0, dir="x", gap=120.0, bt=8.0, lt=5.0, full=True, via_at=[1, 5, 9]),
    dict(name="M14", h=260.0, w=260.0, pitch=400.0, dir="z", gap=140.0, bt=9.0, lt=6.0, via_at=[0, 2, 4], via_w=110.0),
]
VDD_I = (0, 2, 4)  # M14 stripes tied to the VDD rail below; 1 and 3 are VSS


def mats(m):
    D.mats(m)


def top_block(root, m, x0=X0, x1=X1, z0=Z0, name="top", specs=TOP_SPECS):
    g = empty(name, root)
    slab(f"{name}_base", x0, x1, -80.0, 0.0, z0, m["d_lowk"], g)
    lv = tower(g, m, specs, x0, x1, z0)
    lv["g"] = g
    return lv


def top_cap(root, m, lv, pad_x=0.0, bump_x=None, rdl=False, intervals=None, bump_iv=None, sub_iv=None, name="cap"):
    """The pad, passivation, UBM and bump on top of top_block. Returns the key heights.
    `intervals` shows pad and passivation, `bump_iv` the UBM and bump, `sub_iv` the underfill and
    substrate (all on for the whole scene when None)."""
    bump_x = pad_x if bump_x is None else bump_x
    y0 = lv["_top"]
    m14 = lv["M14"]
    out = {}
    gp = group(f"{name}_pad", root, intervals) if intervals is not None else empty(f"{name}_pad", root)
    # two thick vias from the M14 stripe up through the top oxide to the pad
    for k, dx in enumerate((-70.0, 70.0)):
        via(f"{name}_pv{k}", gp, m, pad_x + dx, -45.5, m14.y1, y0 + 60.0, 60.0, 6.0, 4.0, front=0.0)
    slab(f"{name}_ox", X0, X1, y0, y0 + 60.0, Z0, m["d_sio2"], gp)
    box(f"{name}_al", (pad_x - 240.0, y0 + 60.0, Z0 + 4), (pad_x + 240.0, y0 + 120.0, EPS), m["d_al"], gp)
    # SiN round the pad, open over its middle; polyimide on top, opened a little wider
    D_holes(f"{name}_sin", gp, m["d_sin"], X0, X1, [(pad_x - 240.0, pad_x + 240.0)], y0 + 60.0, y0 + 120.0, Z0)
    D_holes(f"{name}_sin2", gp, m["d_sin"], X0, X1, [(pad_x - 170.0, pad_x + 170.0)], y0 + 120.0, y0 + 160.0, Z0)
    D_holes(f"{name}_pi", gp, m["d_pi_o"], X0, X1, [(pad_x - 200.0, pad_x + 200.0)], y0 + 160.0, y0 + 280.0, Z0)
    out.update(pad_top=y0 + 120.0, sin_top=y0 + 160.0, pi_top=y0 + 280.0, y0=y0)
    gb = group(f"{name}_bump", root, bump_iv) if bump_iv is not None else empty(f"{name}_bump", root)
    if rdl:
        # the RDL: copper from the pad opening along the polyimide to a new bump site
        box(f"{name}_rdl_v", (pad_x - 170.0, y0 + 120.0, Z0 + 6), (pad_x + 170.0, y0 + 300.0, EPS), m["d_cu"], gp)
        box(f"{name}_rdl", (pad_x - 170.0, y0 + 280.0, Z0 + 6), (bump_x + 200.0, y0 + 320.0, EPS), m["d_cu"], gp)
        box(f"{name}_pi2", (X0, y0 + 280.0, Z0), (X1, y0 + 300.0, -0.5), m["d_pi_o"], gp)
        D_holes(f"{name}_pi3", gp, m["d_pi_o"], X0, X1, [(bump_x - 170.0, bump_x + 170.0)], y0 + 320.0, y0 + 400.0, Z0)
        ubm_y = y0 + 320.0
        top = y0 + 400.0
    else:
        ubm_y = y0 + 120.0
        top = y0 + 280.0
    box(f"{name}_ubm", (bump_x - 180.0, ubm_y, Z0 + 8), (bump_x + 180.0, top + 18.0, EPS * 2), m["d_ubm"], gb)
    box(f"{name}_ubm_ni", (bump_x - 215.0, top, Z0 + 8), (bump_x + 215.0, top + 26.0, EPS * 3), m["d_liner"], gb)
    r = 330.0
    by = top + 26.0 + r * 0.82
    b = ball(f"{name}_ball", (bump_x, by, -r * 0.4), r, m["d_solder"], gb, 32)
    b.scale = (1.0, 1.0, 0.85)
    cut(b, EPS * 4)
    out.update(bump_y=by, bump_top=by + r * 0.85, bump_r=r, ubm_top=top + 26.0, bump_x=bump_x)
    gs = group(f"{name}_sub", root, sub_iv) if sub_iv is not None else empty(f"{name}_sub", root)
    sy = by + r * 0.85 - 20.0
    box(f"{name}_subpad", (bump_x - 230.0, sy, Z0 + 8), (bump_x + 230.0, sy + 40.0, EPS * 2), m["d_cu"], gs)
    box(f"{name}_sub", (X0, sy + 40.0, Z0), (X1, sy + 360.0, -0.5), m["d_subst"], gs)
    for k in range(3):
        box(f"{name}_subcu{k}", (X0 + 4, sy + 110.0 + 90.0 * k, Z0 + 4), (X1 - 4, sy + 140.0 + 90.0 * k, 0.4), m["d_cu_dim"], gs)
    out.update(sub_y=sy + 40.0, sub_top=sy + 360.0)
    return out


def underfill(root, m, cp, intervals, name="uf"):
    """Opaque epoxy between the polyimide and the substrate, behind the cut bump."""
    g = group(name, root, intervals)
    box(f"{name}_l", (X0, cp["ubm_top"] - 26.0, Z0), (cp["bump_x"] - cp["bump_r"] - 4, cp["sub_y"] - 40.0, -0.6), m["d_underfill_o"], g)
    box(f"{name}_r", (cp["bump_x"] + cp["bump_r"] + 4, cp["ubm_top"] - 26.0, Z0), (X1, cp["sub_y"] - 40.0, -0.6), m["d_underfill_o"], g)
    box(f"{name}_b", (cp["bump_x"] - cp["bump_r"] - 4, cp["ubm_top"] - 26.0, Z0), (cp["bump_x"] + cp["bump_r"] + 4, cp["sub_y"] - 40.0, -cp["bump_r"] * 1.3), m["d_underfill_o"], g)
    return g


def D_holes(name, g, mt, x0, x1, holes, y0, y1, z0, z1=-0.5):
    edges = [x0]
    for a, b in sorted(holes):
        edges += [a, b]
    edges.append(x1)
    for i in range(0, len(edges), 2):
        if edges[i + 1] - edges[i] > 0.5:
            box(f"{name}{i}", (edges[i], y0, z0), (edges[i + 1], y1, z1), mt, g)


def extra_mats(m):
    from sand_overview import mat
    m["d_pi_o"] = mat("d_pi_o", (0.78, 0.50, 0.16), rough=0.55)
    m["d_underfill_o"] = mat("d_underfill_o", (0.36, 0.38, 0.30), rough=0.65)
    m["d_die"] = mat("d_die", (0.26, 0.29, 0.38), metal=0.3, rough=0.45)
    m["d_beol"] = mat("d_beol", (0.40, 0.34, 0.48), metal=0.3, rough=0.5)
    m["d_interposer"] = mat("d_interposer", (0.40, 0.44, 0.54), metal=0.2, rough=0.5)
    m["d_oxide_b"] = mat("d_oxide_b", (0.70, 0.76, 0.92), rough=0.4)


# ---- one narrow column, transistors to bump --------------------------------------------------

FULL_SPECS = (
    [dict(name=f"M{i}", h=14.0, w=8.0, pitch=16.0, dir="z" if i % 2 else "x", gap=12.0) for i in range(1, 5)]
    + [dict(name=f"M{i}", h=30.0, w=16.0, pitch=32.0, dir="z" if i % 2 else "x", gap=24.0) for i in range(5, 10)]
    + [dict(name=f"M{i}", h=60.0, w=36.0, pitch=80.0, dir="z" if i % 2 else "x", gap=48.0) for i in range(10, 13)]
    + [dict(name="M13", h=120.0, w=90.0, pitch=200.0, dir="z", gap=90.0, bt=6.0, lt=4.0),
       dict(name="M14", h=160.0, w=140.0, pitch=320.0, dir="x", gap=110.0, bt=7.0, lt=5.0, full=True)]
)


def full_tower(root, m, x0=-160.0, x1=160.0, z0=-200.0):
    g = empty("full", root)
    xs = D.transistors(g, m, x0, x1, z0, 0.0, pitch=40.0, gate_w=12.0, h_si=90.0)
    slab("pmd", x0, x1, 0.0, 48.0, z0, m["d_sio2"], g)
    lv = tower(g, m, FULL_SPECS, x0, x1, z0, y=48.0)
    m1 = lv["M1"]
    # tungsten contacts from the source/drain tops up to the M1 lines above them
    for k, x in enumerate(xs[:-1]):
        cx = x + 20.0
        near = min(m1.xs, key=lambda v: abs(v - cx))
        box(f"wct{k}", (near - 3.0, 1.0, -12.0), (near + 3.0, m1.y0, EPS), m["d_w"], g)
    lv["xs"] = xs
    return lv


# ---- the three joints, 1 unit = 0.1 um --------------------------------------------------------


def die(g, m, name, x0, x1, y0, thick=500.0, beol=60.0, z0=-1200.0, flip=False):
    """A silicon die with its thin wiring layer on the face (facing down unless flip)."""
    if flip:
        slab(f"{name}_si", x0, x1, y0 + beol, y0 + beol + thick, z0, m["d_die"], g)
        slab(f"{name}_beol", x0, x1, y0, y0 + beol, z0, m["d_beol"], g)
    else:
        slab(f"{name}_beol", x0, x1, y0, y0 + beol, z0, m["d_beol"], g)
        slab(f"{name}_si", x0, x1, y0 + beol, y0 + beol + thick, z0, m["d_die"], g)


def c4_window(g, m, cx, w=3000.0, pitch=1500.0, r=500.0, name="c4"):
    """C4 solder balls between a die (above) and an organic substrate (below)."""
    x0, x1 = cx - w / 2, cx + w / 2
    sub_top = 0.0
    slab(f"{name}_sub", x0, x1, -600.0, sub_top, -1200.0, m["d_subst"], g)
    for k in range(3):
        slab(f"{name}_subcu{k}", x0 + 4, x1 - 4, -540.0 + 160 * k, -510.0 + 160 * k, -1196.0, m["d_cu_dim"], g, front=0.4)
    gap = 2 * r * 0.8
    n = int(w // pitch)
    xs = [x0 + pitch / 2 + k * pitch for k in range(n)]
    for k, x in enumerate(xs):
        box(f"{name}_lp{k}", (x - r * 0.75, sub_top, -1100.0), (x + r * 0.75, sub_top + 30, EPS), m["d_cu"], g)
        box(f"{name}_up{k}", (x - r * 0.65, gap - 30, -1100.0), (x + r * 0.65, gap, EPS), m["d_ubm"], g)
        b = ball(f"{name}_b{k}", (x, gap / 2, -r * 0.5), r, m["d_solder"], g, 32)
        b.scale = (1.0, 1.0, 0.8)
        cut(b, EPS * 2)
    die(g, m, f"{name}_die", x0, x1, gap, thick=700.0, beol=80.0)
    return xs, gap


def pillar_window(g, m, cx, w=3000.0, pitch=400.0, r=125.0, h=300.0, cap=110.0, name="ub", bridge=None):
    """Copper pillars with solder caps between a chiplet (above) and a silicon interposer."""
    x0, x1 = cx - w / 2, cx + w / 2
    slab(f"{name}_int", x0, x1, -500.0, 0.0, -1200.0, m["d_interposer"], g)
    slab(f"{name}_intm", x0, x1, -60.0, 0.0, -1200.0, m["d_beol"], g, front=0.2)
    n = int(w // pitch)
    start = cx - (n - 1) * pitch / 2
    xs = [start + k * pitch for k in range(n)]
    top = 30.0 + cap + h
    for k, x in enumerate(xs):
        box(f"{name}_lp{k}", (x - r * 1.1, 0.0, -r * 2.2), (x + r * 1.1, 30.0, EPS), m["d_cu"], g)
        box(f"{name}_sn{k}", (x - r, 30.0, -r * 2.0), (x + r, 30.0 + cap, EPS * 2), m["d_solder"], g)
        box(f"{name}_cu{k}", (x - r, 30.0 + cap, -r * 2.0), (x + r, top, EPS * 2), m["d_cu"], g)
    die(g, m, f"{name}_die", x0, x1, top, thick=600.0, beol=60.0)
    return xs, top


def hybrid_window(g, m, cx, w=3000.0, pitch=100.0, pad=50.0, ph=40.0, name="hb"):
    """Two dies face to face: copper pads flush in oxide, bonded with no solder."""
    x0, x1 = cx - w / 2, cx + w / 2
    slab(f"{name}_lo_si", x0, x1, -560.0, -100.0, -1200.0, m["d_die"], g)
    slab(f"{name}_lo_beol", x0, x1, -100.0, -ph, -1200.0, m["d_beol"], g)
    slab(f"{name}_lo_ox", x0, x1, -ph, 0.0, -1200.0, m["d_oxide_b"], g)
    slab(f"{name}_hi_ox", x0, x1, 0.0, ph, -1200.0, m["d_oxide_b"], g)
    slab(f"{name}_hi_beol", x0, x1, ph, 100.0, -1200.0, m["d_beol"], g)
    slab(f"{name}_hi_si", x0, x1, 100.0, 560.0, -1200.0, m["d_die"], g)
    n = int(w // pitch)
    start = cx - (n - 1) * pitch / 2
    xs = [start + k * pitch for k in range(n)]
    for k, x in enumerate(xs):
        box(f"{name}_p{k}", (x - pad / 2, -ph, -1190.0), (x + pad / 2, ph, EPS), m["d_cu"], g)
    return xs


# ---- section 6: two power-delivery columns ----------------------------------------------------

FRONT_SPECS = (
    [dict(name=f"F{i}", h=14.0, w=8.0, pitch=16.0, dir="z" if i % 2 else "x", gap=12.0) for i in range(1, 5)]
    + [dict(name=f"F{i}", h=30.0, w=16.0, pitch=32.0, dir="z" if i % 2 else "x", gap=24.0) for i in range(5, 7)]
)
BACK_SPECS = [  # bottom first: the thickest backside metal is furthest from the devices
    dict(name="BM2", h=90.0, w=70.0, pitch=150.0, dir="x", full=True, bt=5.0, lt=3.0),
    dict(name="BM1", h=50.0, w=36.0, pitch=80.0, dir="z", gap=40.0, bt=4.0, lt=3.0),
    dict(name="BM0", h=24.0, w=16.0, pitch=40.0, dir="x", gap=20.0, full=True, bt=3.0, lt=2.0),
]


def m14_by_hand(root, m, lv, etched, shell, copper, cap):
    """M14 built step by step on a top_block made up to M13 (for the damascene loop): the etched
    film, the barrier and seed shells, the plated copper and the cap, each a group switched on for
    its own intervals. Adds lv["M14"] and lv["_top"] so top_cap can go on afterwards."""
    s = TOP_SPECS[4]
    w, h, bt, lt, vw = s["w"], s["h"], s["bt"], s["lt"], s["via_w"]
    ya = lv["_top"]
    yl, yt = ya + s["gap"], ya + s["gap"] + h
    m13 = lv["M13"]
    xs = [-800.0, -400.0, 0.0, 400.0, 800.0]
    vx = [-800.0, 0.0, 800.0]
    hw, hv = w / 2 + lt + bt, vw / 2 + lt + bt
    zv = -(vw + 2 * (lt + bt)) - 1.0
    ge = group("m14_etched", root, etched)
    D_holes("m14_tr", ge, m["d_lowk"], X0, X1, [(x - hw, x + hw) for x in xs], yl, yt, Z0)
    D_holes("m14_vf", ge, m["d_lowk"], X0, X1, [(x - hv, x + hv) for x in vx], ya, yl, zv)
    slab("m14_vb", X0, X1, ya, yl, Z0, m["d_lowk"], ge, front=zv)
    gs = group("m14_shell", root, shell)
    gc = group("m14_cu", root, copper)
    for k, x in enumerate(xs):
        zline(f"m14s{k}", gs, m, x, yl, w, h, Z0 + 2, bt, lt, cu=False)
        zline(f"m14c{k}", gc, m, x, yl, w, h, Z0 + 2, bt, lt)
    for k, x in enumerate(vx):
        via(f"m14sv{k}", gs, m, x, -vw / 2 - 0.5, m13.y1, yl, vw, bt, lt, front=0.0, cu=False)
        via(f"m14cv{k}", gc, m, x, -vw / 2 - 0.5, m13.y1, yl, vw, bt, lt, front=0.0)
    gk = group("m14_cap", root, cap)
    capt = yt + 31.0
    slab("m14_cap_s", X0, X1, yt + 0.4, capt, Z0, m["d_cap"], gk, front=-0.3)
    lev = D.Level("M14", yl, h, w, s["pitch"], "z", xs, [])
    lev.bt, lev.lt, lev.cap_top, lev.vias_at, lev.via_w = bt, lt, capt, vx, vw
    lv["M14"] = lev
    lv["_top"] = capt
    return dict(ya=ya, yl=yl, yt=yt, xs=xs, vx=vx, hw=hw, zv=zv)
